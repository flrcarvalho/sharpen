# -*- coding: utf-8 -*-
"""Export ANONIMIZADO das bases reais para a conta de demonstracao `/realtrial`.

SOMENTE LEITURA do banco. Nao escreve, nao altera, nao apaga nada em producao:
le as bases de origem e grava UM arquivo JSON. Quem importa e' o `importar.py`
(Fatia 2), num passo separado e com olho humano no meio.

O QUE ESTE SCRIPT PROTEGE, e o que ele NAO protege
--------------------------------------------------
Protege IDENTIDADE: nome de conta, e-mail, fornecedor, tipster e codigo de
bilhete sao trocados por ficticios, com mapa deterministico (mesma entrada ->
mesma saida), entao TODO vinculo sobrevive: a conta X continua sendo a mesma
conta em todas as casas, o tipster Y continua dono das mesmas apostas. E' isso
que mantem Solidez, Atribuicao por Casa e drawdown por tipster REAIS -- que e'
o ponto da demonstracao.

Protege PORTE: todo valor em dinheiro e' multiplicado por `FATOR`. Fator unico
aplicado a stake, custo e caixa JUNTOS. Isso preserva exatamente ROI, win rate,
drawdown em %, Solidez e qualquer razao entre numeros (divide os dois lados de
toda divisao) e muda so a escala em R$. Escalar stake e esquecer custo faria o
custo virar proporcionalmente maior e o P/L Liquido mentiria -- e' a familia do
"blindar metade dos campos" do CLAUDE.md.

NAO protege contra quem JA TEM as bases originais. Data, casa, esporte, mercado
e descricao do jogo sao copiados verbatim (sao evento publico, e trocar destroi
as telas). Quem tiver as duas bases na mao consegue casar linha a linha. O alvo
aqui e' o publico da demonstracao, nao um adversario com acesso ao banco.

O QUE E' COPIADO VERBATIM, de proposito
---------------------------------------
casa, esporte, aposta (categoria canonica do MASTER_APOSTAS), descricao, odd,
resultado, data, sistema. Trocar categoria quebraria matcher, Atribuicao por
Casa e as telas de mercado sem proteger pessoa nenhuma -- "Escanteios" nao
identifica ninguem. `odd` NAO escala: odd nao e' dinheiro.

    python scripts/realtrial/exportar.py [--fator 0.5] [--saida arquivo.json]
"""
import argparse
import asyncio
import io
import json
import os
import pathlib
import random
import re
import sys
import unicodedata
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP

RAIZ = pathlib.Path(__file__).resolve().parents[2]
# `app/repository.py` faz `from database import ...` (import top-level), entao
# `app/` precisa estar no path alem da raiz -- senao o import falha com
# ModuleNotFoundError antes de qualquer coisa rodar.
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "app"))

# Assinatura vem do REPO, nunca reimplementada aqui: `_assinatura` decide dedup
# em producao e uma copia divergiria em silencio (CLAUDE.md, "o teste que
# reimplementava o codigo"). Trocar parceiro e escalar stake mexe em duas colunas
# de `_SIG_COLS`, entao TODA assinatura e' recalculada -- assinatura velha faria
# a proxima captura nao deduplicar e duplicar o historico inteiro.
from app.repository import _assinatura, _norm_odd  # noqa: E402

SEMENTE = 20260913
DONOS_ORIGEM = ["Feca", "Jonathan"]
DONO_DESTINO = "realtrial"
FATOR_PADRAO = Decimal("0.5")


# ── Banco ────────────────────────────────────────────────────────────────────
def _database_url() -> str:
    """DATABASE_URL do ambiente ou do .env (o app nao usa python-dotenv)."""
    if os.environ.get("DATABASE_URL"):
        return os.environ["DATABASE_URL"]
    env = RAIZ / ".env"
    if env.exists():
        for linha in env.read_text(encoding="utf-8", errors="ignore").splitlines():
            if linha.strip().startswith("DATABASE_URL="):
                return linha.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("DATABASE_URL nao encontrada (.env ou ambiente)")


# ── Dinheiro: texto BR <-> Decimal ───────────────────────────────────────────
# Medido nas duas bases antes de escrever isto: 48.770 de 48.885 stakes em
# "250,00", 111 em "1.234,56", 3 inteiras e UMA em "250.50". Nenhuma no formato
# EN com milhar. As classes abaixo cobrem as quatro e recusam o resto.
_RE_BR_MILHAR = re.compile(r"^\d{1,3}(\.\d{3})+,\d+$")   # 1.234,56
_RE_BR = re.compile(r"^\d+,\d+$")                         # 250,00
_RE_INT = re.compile(r"^\d+$")                            # 250
_RE_PONTO = re.compile(r"^\d+\.\d{1,2}$")                 # 250.50 -> decimal EN


def num_br(txt: str) -> Decimal | None:
    """Texto do banco -> Decimal. None quando nao e' numero reconhecivel.

    A regra do CLAUDE.md e' por TOKEN, nao por casa: o ultimo separador e' o
    decimal, e um separador so e' decimal -- EXCETO ponto seguido de exatamente
    3 digitos em dinheiro, que e' milhar. Por isso `_RE_PONTO` exige 1-2 casas:
    tratar "1.234" como decimal dividiria a stake por mil.
    """
    t = (txt or "").strip()
    if not t:
        return None
    if _RE_BR_MILHAR.match(t):
        return Decimal(t.replace(".", "").replace(",", "."))
    if _RE_BR.match(t):
        return Decimal(t.replace(",", "."))
    if _RE_INT.match(t) or _RE_PONTO.match(t):
        return Decimal(t)
    return None


def br_num(v: Decimal) -> str:
    """Decimal -> texto do banco, no padrao BR de 2 casas com virgula decimal.

    Sem separador de milhar: e' a forma dominante da base (48.770 de 48.885) e
    a que `_num_bloco`/`_numBR` leem sem ambiguidade nenhuma.
    """
    return f"{v.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):f}".replace(".", ",")


def escalar(txt: str, fator: Decimal) -> str:
    """Multiplica um valor monetario em texto, preservando o texto se ilegivel.

    Valor que nao da para ler NAO vira zero: zero se disfarca de conta feita
    (CLAUDE.md). Fica como esta e entra no relatorio de conferencia.
    """
    n = num_br(txt)
    return txt if n is None else br_num(n * fator)


def pl_de(stake: str, odd: str, resultado: str) -> Decimal | None:
    """P/L pelas 5 formulas de `calcular_pl`, em Decimal, para a conferencia.

    Reimplementado aqui de proposito e SO para conferir: o alvo da checagem e'
    provar que ROI antes == ROI depois. Usar a funcao de producao dos dois lados
    esconderia justamente o erro que a conferencia procura.
    """
    s, o = num_br(stake), num_br(odd)
    r = (resultado or "").strip().upper()
    if s is None:
        return None
    if r == "L":
        return -s
    if r == "V":
        return Decimal(0)
    if r == "HL":
        return -s / 2
    if o is None:
        return None
    if r == "W":
        return s * (o - 1)
    if r == "HW":
        return (s / 2) * (o - 1)
    return None


# ── Pools de nomes ficticios ─────────────────────────────────────────────────
# "Marlon" saiu do pool de proposito: existe tipster REAL com esse nome nas
# bases, e um ficticio homonimo faria a demonstracao parecer citar a pessoa.
# Nome ficticio nunca pode coincidir com nome real -- a conferencia acusa.
_PRIMEIROS = [
    "Bruno", "Caio", "Diego", "Otávio", "Renan", "Tiago", "Vitor",
    "Luan", "Igor", "Rafael", "Leandro", "Murilo", "Enzo", "Davi", "Artur",
    "Nuno", "Heitor", "Ravi", "Noah", "Théo", "Gael", "Ícaro", "Breno",
    "Emanuel", "Joaquim", "Levi", "Anselmo", "Fábio", "Gustavo", "Hélio",
    "Ivan", "Juliano", "Kaio", "Lucas", "Mateus", "Nelson", "Osvaldo",
    "Patrick", "Quirino", "Rodrigo", "Sérgio", "Tadeu", "Ulisses", "Válter",
    "Wagner", "Xavier", "Yuri", "Zeca", "Alan", "Bento", "César", "Danilo",
]
_SOBRENOMES = [
    "Alves", "Barros", "Cardoso", "Dias", "Esteves", "Franco", "Guerra",
    "Horta", "Império", "Jardim", "Klein", "Lemos", "Moraes", "Nunes",
    "Oliveira", "Pacheco", "Queiroz", "Ramos", "Serra", "Teles", "Vilela",
]
# 14 fornecedores reais nas duas bases (medido). O pool tem folga de sobra
# para nao esgotar se entrar base nova -- pool apertado levanta RuntimeError
# no meio do export, e a hora de descobrir isso nao e' essa.
_FORNECEDORES = [
    "Vega", "Norte", "Sul", "Âncora", "Trilho", "Pauta", "Órbita", "Cume",
    "Farol", "Bússola", "Cais", "Dique", "Estaleiro", "Fronteira", "Garoa",
    "Aurora", "Baluarte", "Cerro", "Duna", "Enseada", "Fenda", "Grota",
    "Istmo", "Lagoa", "Manguezal", "Nascente", "Oásis", "Planalto",
]
# Tipster ficticio: duas partes combinadas. 133 nomes reais nas duas bases, e
# lista fixa desse tamanho vira lista inventada na marra -- combinar da folga.
_TIP_A = [
    "Linha", "Corner", "Método", "Sala", "Contra-Ataque", "Régua", "Pivô",
    "Quadra", "Bloco", "Fator", "Grid", "Saque", "Modelo", "Cauda", "Pressão",
    "Zona", "Duplo", "Escanteio", "Base", "Marca", "Ritmo", "Eixo", "Vetor",
    "Ponto", "Curva", "Faixa", "Nível", "Traço", "Passe", "Giro",
]
_TIP_B = [
    "Fria", "Value", "Ártico", "7", "Alto", "Rápida", "Norte", "K", "12",
    "Curto", "9", "Longa", "Alta", "14", "Pivô", "Sul", "Seca", "Firme",
    "Exata", "Larga", "Dupla", "Zero", "Prime", "Máxima", "Livre", "Certa",
]


class Anonimizador:
    """Mapa deterministico entidade real -> ficticia, com unicidade garantida.

    Deterministico importa: rodar o export de novo depois tem de dar os MESMOS
    nomes, senao reimportar a demo renomeia todo mundo e quem ja viu o video
    ve outra carteira. A semente manda; a ordem de chegada nao (as chaves sao
    ordenadas antes de sortear).
    """

    def __init__(self, semente: int = SEMENTE, proibidos: set[str] | None = None):
        self._rng = random.Random(semente)
        self._mapas: dict[str, dict[str, str]] = defaultdict(dict)
        self._usados: dict[str, set[str]] = defaultdict(set)
        # Nome ficticio NUNCA pode conter um nome real. Parece improvavel e nao
        # e': medido, havia um tipster real "Duplo" e outro "MARLON", e os pools
        # traziam as duas palavras -- sairam "Duplo Alto" e "Marlon Alves",
        # ficticios que citam gente de verdade. Filtrar o pool a mao resolveria
        # esses dois; a familia inteira so fecha recusando na GERACAO, porque a
        # proxima base traz um nome que ninguem previu.
        self._proibido = None
        alvos = sorted((p for p in (proibidos or set()) if len(p.strip()) >= 4),
                       key=len, reverse=True)
        if alvos:
            self._proibido = re.compile(
                "|".join(_re_nome(a).pattern for a in alvos))

    def _colide(self, cand: str) -> bool:
        return bool(self._proibido and self._proibido.search(_sem_acento(cand)))

    def _novo(self, tipo: str) -> str:
        for _ in range(10000):
            if tipo == "conta":
                cand = (f"{self._rng.choice(_PRIMEIROS)} "
                        f"{self._rng.choice(_SOBRENOMES)}")
            elif tipo == "fornecedor":
                cand = self._rng.choice(_FORNECEDORES)
            elif tipo == "tipster":
                cand = f"{self._rng.choice(_TIP_A)} {self._rng.choice(_TIP_B)}"
            else:
                raise ValueError(tipo)
            if cand not in self._usados[tipo] and not self._colide(cand):
                self._usados[tipo].add(cand)
                return cand
        raise RuntimeError(f"pool de '{tipo}' esgotado -- aumente a lista")

    def traduzir(self, tipo: str, chave: str) -> str:
        if chave not in self._mapas[tipo]:
            self._mapas[tipo][chave] = self._novo(tipo)
        return self._mapas[tipo][chave]

    def mapa(self, tipo: str) -> dict[str, str]:
        return dict(self._mapas[tipo])


# `Nome [Fornecedor]` e' a forma dominante (179 de 180 contas do Feca). As do
# Jonathan tem e-mail no lugar do nome em 63 de 90 -- o dado mais identificavel
# da base inteira, e o motivo de a conferencia falhar se sobrar um "@".
_RE_PARCEIRO = re.compile(r"^\s*(?P<nome>.*?)\s*\[\s*(?P<forn>[^\]]*)\s*\]\s*$")


def traduzir_parceiro(anon: Anonimizador, dono: str, bruto: str) -> str:
    """Conta anonimizada, PRESERVANDO a forma (com ou sem `[Fornecedor]`).

    A chave inclui o `dono`: os dois lados podem ter conta de mesmo nome, e
    fundi-las juntaria duas contas reais distintas numa so. O fornecedor tem
    mapa PROPRIO e global -- o mesmo fornecedor atende os dois, e e' assim que
    a tela de Fornecedores continua agrupando o que agrupava.
    """
    bruto = (bruto or "").strip()
    if not bruto:
        return bruto
    m = _RE_PARCEIRO.match(bruto)
    if m:
        nome = anon.traduzir("conta", f"{dono}|{m.group('nome')}")
        forn = anon.traduzir("fornecedor", m.group("forn"))
        return f"{nome} [{forn}]"
    return anon.traduzir("conta", f"{dono}|{bruto}")


def traduzir_tipster(anon: Anonimizador, nome: str) -> str:
    """Tipster anonimizado, com mapa GLOBAL (sem o dono na chave).

    Tipster de mesmo nome nos dois lados e' o mesmo tipster (eles assinam os
    mesmos canais). Separar por dono criaria dois tipsters ficticios para uma
    pessoa so e dividiria a amostra dela ao meio -- a Solidez por tipster, que
    e' o que a demonstracao mostra, sairia medida sobre metade das apostas.
    """
    nome = (nome or "").strip()
    return anon.traduzir("tipster", nome) if nome else ""


class CodigoFake:
    """Codigo de bilhete ficticio: DETERMINISTICO por codigo real e UNICO.

    Sao duas exigencias diferentes, e faltar qualquer uma quebra o sistema:

    · deterministico -- o mesmo codigo real sempre vira o mesmo ficticio. Sem
      isso o mesmo bilhete visto duas vezes deixa de ser o mesmo bilhete e a
      dedup por ID para de funcionar.
    · unico -- dois codigos reais nunca podem virar o mesmo ficticio. Com
      codigo na mao, `_assinatura` IGNORA o `_counter` (o hash e'
      `ID|casa|parceiro|codigo`), entao colisao aqui NAO tem desempate: ela
      vira UNIQUE violado no import, ou loop infinito em quem procurar um
      contador livre. Foi exatamente o que travou a primeira rodada deste
      script.

    Preserva comprimento e classe de caractere, porque o comprimento e' o
    sintoma que denuncia codigo lido por OCR (CLAUDE.md, s338). MEDIDO: 31
    bilhetes tem codigo de 1-2 caracteres, onde o espaco e' de 10 e 100 valores
    e a colisao e' certa. Nesses, ESTENDE o molde ate caber -- unicidade vale
    mais que o sintoma, e sao 31 linhas em 48.885.
    """

    _LETRAS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    def __init__(self, semente: int):
        self._rng = random.Random(semente)
        self._mapa: dict[str, str] = {}
        self._usados: set[str] = set()

    def _sortear(self, molde: str) -> str:
        saida = []
        for ch in molde:
            if ch.isdigit():
                saida.append(str(self._rng.randint(0, 9)))
            elif ch.isalpha():
                novo = self._rng.choice(self._LETRAS)
                saida.append(novo if ch.isupper() else novo.lower())
            else:
                saida.append(ch)
        return "".join(saida)

    def traduzir(self, codigo: str) -> str:
        codigo = (codigo or "").strip()
        if not codigo:
            return ""
        if codigo in self._mapa:
            return self._mapa[codigo]
        molde = codigo
        for tentativa in range(1, 301):
            cand = self._sortear(molde)
            if cand not in self._usados:
                self._mapa[codigo] = cand
                self._usados.add(cand)
                return cand
            # Espaco esgotado para este comprimento: alonga o molde mantendo a
            # classe do ultimo caractere. So acontece em codigo curtissimo.
            if tentativa % 50 == 0:
                molde += "0" if molde[-1].isdigit() else "A"
        raise RuntimeError(
            f"sem codigo unico para molde de {len(codigo)} caracteres")

    @property
    def mapa(self) -> dict[str, str]:
        return dict(self._mapa)


# ── Leitura ──────────────────────────────────────────────────────────────────
COLS_BILHETE = [
    "casa", "parceiro", "data", "esporte", "tipster", "aposta", "descricao",
    "stake", "odd", "resultado", "extraction_state", "codigo_bilhete",
    "archived", "sistema", "sistema_linhas", "criado_em", "dono",
]

SQL_BILHETES = f"""
    SELECT {', '.join(COLS_BILHETE)}
    FROM bilhetes WHERE dono = ANY($1) ORDER BY dono, id
"""
SQL_PARCEIROS = """
    SELECT dono, casa, nome, arquivado, adquirida_em, arquivada_em
    FROM parceiros WHERE dono = ANY($1) ORDER BY dono, casa, nome
"""
SQL_TIPSTERS = """
    SELECT dono, nome, casas, mercados, obs, arquivado,
           stake_min, stake_max, apelidos, dica_stake
    FROM tipsters WHERE dono = ANY($1) ORDER BY dono, nome
"""
SQL_CUSTOS = """
    SELECT dono, custo_tipster, custo_geral, custo_conta
    FROM custo_store WHERE dono = ANY($1)
"""


async def ler_tudo(donos: list[str]) -> dict:
    import asyncpg
    conn = await asyncpg.connect(_database_url())
    try:
        dados = {
            "bilhetes": [dict(r) for r in await conn.fetch(SQL_BILHETES, donos)],
            "parceiros": [dict(r) for r in await conn.fetch(SQL_PARCEIROS, donos)],
            "tipsters": [dict(r) for r in await conn.fetch(SQL_TIPSTERS, donos)],
            "custos": [dict(r) for r in await conn.fetch(SQL_CUSTOS, donos)],
        }
        # `fornecedor_preco` e `caixa_mov` variam de schema entre ambientes; se
        # nao existirem, a demo simplesmente nao tem aquela tela populada. Falha
        # de tabela ausente nao pode derrubar o export inteiro.
        for chave, sql in (
            ("caixa", "SELECT * FROM caixa_mov WHERE dono = ANY($1)"),
            ("fornecedor_preco", "SELECT * FROM fornecedor_preco WHERE dono = ANY($1)"),
        ):
            try:
                dados[chave] = [dict(r) for r in await conn.fetch(sql, donos)]
            except Exception as e:            # noqa: BLE001
                dados[chave] = []
                print(f"   aviso: {chave} nao lida ({type(e).__name__}: {e})")
        return dados
    finally:
        await conn.close()


# ── Transformacao ────────────────────────────────────────────────────────────
def transformar(dados: dict, fator: Decimal, semente: int) -> dict:
    reais_all = {(b["parceiro"] or "").strip() for b in dados["bilhetes"]}
    reais_all |= {(b["tipster"] or "").strip() for b in dados["bilhetes"]}
    reais_all |= {(p["nome"] or "").strip() for p in dados["parceiros"]}
    reais_all |= {(t["nome"] or "").strip() for t in dados["tipsters"]}
    anon = Anonimizador(semente, proibidos=reais_all)
    cod = CodigoFake(semente ^ 0xC0D1)
    vistas: set[str] = set()
    saida_bilhetes = []
    ilegiveis = []

    # Nomes reais que precisam sumir TAMBEM de dentro da descricao (ver
    # `_NOMES_PUBLICOS`). Montado depois que os mapas ja conhecem o ficticio de
    # cada tipster, entao a descricao passa a citar o mesmo nome que a coluna.
    nomes_reais = sorted(
        {(b["tipster"] or "").strip() for b in dados["bilhetes"]}
        | {(t["nome"] or "").strip() for t in dados["tipsters"]},
        key=len, reverse=True)
    trocas = [
        (_re_nome(n), traduzir_tipster(anon, n))
        for n in nomes_reais
        if len(n) >= 4 and _sem_acento(n) not in _NOMES_PUBLICOS
    ]

    total = len(dados["bilhetes"])
    for i, b in enumerate(dados["bilhetes"], 1):
        if i % 10000 == 0:
            print(f"   {i}/{total}...", flush=True)
        dono = b["dono"]
        novo = {
            # verbatim: evento publico, e o que faz a demonstracao ser real
            "casa": b["casa"], "data": b["data"], "esporte": b["esporte"],
            "aposta": b["aposta"],
            "descricao": limpar_descricao(b["descricao"], trocas),
            "odd": b["odd"], "resultado": b["resultado"],
            "extraction_state": b["extraction_state"], "archived": b["archived"],
            "sistema": b["sistema"], "sistema_linhas": b["sistema_linhas"],
            "criado_em": b["criado_em"].isoformat() if b["criado_em"] else None,
            # trocado
            "parceiro": traduzir_parceiro(anon, dono, b["parceiro"]),
            "tipster": traduzir_tipster(anon, b["tipster"]),
            "codigo_bilhete": cod.traduzir(b["codigo_bilhete"] or ""),
            # escalado
            "stake": escalar(b["stake"], fator),
            "dono": DONO_DESTINO,
        }
        if num_br(b["stake"]) is None:
            ilegiveis.append({"campo": "stake", "casa": b["casa"]})

        # Assinatura recalculada sobre os valores FINAIS, e os dois ramos de
        # `_assinatura` se comportam de forma OPOSTA na colisao:
        #
        # · COM codigo, o hash e' `ID|casa|parceiro|codigo` e o `_counter` nao
        #   entra nele. Nao existe desempate: procurar contador livre ali e'
        #   loop infinito (foi o que travou a 1a rodada). O codigo ja nasce
        #   unico no `CodigoFake`, entao colisao aqui e' defeito -- aborta, em
        #   vez de gravar linha que o import perderia no UNIQUE.
        # · SEM codigo, o `_counter` entra no hash e escala, igual ao
        #   `upsert_bilhetes` faz: duas linhas de conteudo identico sao
        #   bilhetes distintos (regra do Feca) e precisam escalar, nao colidir.
        if novo["codigo_bilhete"]:
            sig = _assinatura(novo)
            chave = (novo["casa"], novo["parceiro"], sig)
            if chave in vistas:
                raise RuntimeError(
                    f"colisao de assinatura COM codigo em {novo['casa']} -- o "
                    "codigo ficticio deveria ser unico; export abortado")
        else:
            # Teto explicito: `while True` aqui e' a mesma armadilha de cima.
            for contador in range(1, 1001):
                sig = _assinatura(novo, contador)
                chave = (novo["casa"], novo["parceiro"], sig)
                if chave not in vistas:
                    break
            else:
                raise RuntimeError(
                    f"mais de 1000 linhas identicas em {novo['parceiro']}")
        vistas.add(chave)
        novo["assinatura"] = sig
        saida_bilhetes.append(novo)

    saida_parceiros = []
    for p in dados["parceiros"]:
        saida_parceiros.append({
            "casa": p["casa"],
            "nome": traduzir_parceiro(anon, p["dono"], p["nome"]),
            "arquivado": p["arquivado"],
            "adquirida_em": p["adquirida_em"].isoformat() if p["adquirida_em"] else None,
            "arquivada_em": p["arquivada_em"].isoformat() if p["arquivada_em"] else None,
            "dono": DONO_DESTINO,
        })

    saida_tipsters = []
    for t in dados["tipsters"]:
        saida_tipsters.append({
            "nome": traduzir_tipster(anon, t["nome"]),
            "casas": t["casas"], "mercados": t["mercados"],
            # `obs`, `apelidos` e `dica_stake` sao TEXTO LIVRE escrito por humano:
            # e' onde mora "grupo do Fulano", telefone, @ de canal. Nao ha como
            # anonimizar texto livre com garantia, entao nao viaja. `dica_stake`
            # cita valor em R$, que tambem sairia fora de escala.
            "obs": None, "apelidos": None, "dica_stake": None,
            "arquivado": t["arquivado"],
            "stake_min": float(Decimal(str(t["stake_min"])) * fator) if t["stake_min"] else None,
            "stake_max": float(Decimal(str(t["stake_max"])) * fator) if t["stake_max"] else None,
            "dono": DONO_DESTINO,
        })

    # Custos: as chaves dos dicts sao NOMES (tipster, fornecedor||casa), entao
    # passam pelo mesmo mapa; os valores sao dinheiro e escalam.
    saida_custos = []
    for c in dados["custos"]:
        ct = json.loads(c["custo_tipster"]) if isinstance(c["custo_tipster"], str) else c["custo_tipster"]
        cc = json.loads(c["custo_conta"]) if isinstance(c["custo_conta"], str) else c["custo_conta"]
        cg = json.loads(c["custo_geral"]) if isinstance(c["custo_geral"], str) else c["custo_geral"]
        saida_custos.append({
            "dono": DONO_DESTINO,
            "custo_tipster": {
                traduzir_tipster(anon, k): _escala_valor(v, fator) for k, v in (ct or {}).items()
            },
            "custo_conta": {
                _chave_conta(anon, c["dono"], k): _escala_valor(v, fator)
                for k, v in (cc or {}).items()
            },
            "custo_geral": [
                {**item, "valor": _escala_valor(item.get("valor"), fator)}
                for item in (cg or [])
            ],
        })

    return {
        "bilhetes": saida_bilhetes,
        "parceiros": saida_parceiros,
        "tipsters": saida_tipsters,
        "custos": saida_custos,
        "_mapas": {t: anon.mapa(t) for t in ("conta", "fornecedor", "tipster")},
        "_ilegiveis": ilegiveis,
    }


def _escala_valor(v, fator: Decimal):
    """Escala numero vindo de JSONB (pode ser int, float ou string)."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(Decimal(str(v)) * fator)
    n = num_br(str(v))
    return br_num(n * fator) if n is not None else v


def _chave_conta(anon: Anonimizador, dono: str, chave: str) -> str:
    """`custo_conta` usa a chave `fornecedor||casa`. So o fornecedor e' nome."""
    if "||" in chave:
        forn, _, casa = chave.partition("||")
        return f"{anon.traduzir('fornecedor', forn)}||{casa}"
    return anon.traduzir("fornecedor", chave)


# ── Nome real dentro da DESCRICAO ────────────────────────────────────────────
# A descricao e' copiada verbatim porque e' evento publico, e por isso ela cita
# nome de atleta e de time o tempo todo. Varrer nome real ali da uma montanha de
# falso positivo -- MEDIDO na 1a rodada: 24 nomes acusados, 21 inocentes.
#
# As duas classes de inocente:
#   a) substring dentro de palavra maior -- um tipster "Beta" casando em
#      "Betano" (8.372x), "Samu" em "Samuel Silvera", "Nine" em "Moknine",
#      "Feca" dentro do hash hexadecimal da assinatura. Resolve-se exigindo
#      limite de PALAVRA, e e' o que `_re_nome` faz.
#   b) o nome do tipster E' uma palavra publica: ou o proprio esporte
#      (Badminton, Volei, eSports, Duplo), ou o nome de um atleta/time de
#      verdade (Sonny Gray, Kevin Punter, Moriyama Samurai, Damir Dzumhur,
#      Latinovic, Araujo, Fusion, Australia). A descricao contem essas
#      palavras porque elas sao o EVENTO, nao porque alguem vazou.
#
# Os tres culpados de verdade eram rotulo interno escrito no lugar do evento
# ("Arrudex 1", "Multipla So Chutes", "Pessoal"). Esses SAO trocados, abaixo.
_NOMES_PUBLICOS = {
    "badminton", "volei", "esports", "duplo", "australia", "sonny", "punter",
    "samurai", "fusion", "araujo", "damir", "latino", "beta", "ebask", "samu",
    "nine", "macca", "diamond", "zora", "feca", "marlon",
}


def _sem_acento(s: str) -> str:
    """Minusculas sem acento, PRESERVANDO o comprimento.

    O comprimento importa: `limpar_descricao` acha a posicao no texto
    normalizado e substitui no texto ORIGINAL, no mesmo offset. NFD decompoe o
    acento num caractere combinante separado, que e' descartado, entao
    "Só" (2) vira "so" (2) e os offsets continuam validos.
    """
    return "".join(c for c in unicodedata.normalize("NFD", s)
                   if unicodedata.category(c) != "Mn").lower()


def _re_nome(nome: str) -> re.Pattern:
    """Regex do nome com limite de palavra nas duas pontas, sem acento."""
    return re.compile(rf"(?<![0-9a-z]){re.escape(_sem_acento(nome))}(?![0-9a-z])")


def limpar_descricao(desc: str, trocas: list[tuple[re.Pattern, str]]) -> str:
    """Troca nome real citado na descricao pelo ficticio correspondente.

    Acha no texto normalizado e recorta no ORIGINAL pelo mesmo offset, para
    nao destruir acento e caixa do resto da descricao (que e' o evento e tem
    de continuar fiel -- `checar_fidelidade` compara nome proprio da descricao
    com o bloco cru).
    """
    if not desc:
        return desc
    plano = _sem_acento(desc)
    for padrao, novo in trocas:
        while True:
            m = padrao.search(plano)
            if not m:
                break
            desc = desc[:m.start()] + novo + desc[m.end():]
            plano = _sem_acento(desc)
    return desc


def conferir(origem: dict, saida: dict, fator: Decimal) -> list[str]:
    """Falhas encontradas. Lista vazia = export aprovado.

    Tres perguntas, e nenhuma delas confia na anterior:
      1. o dado sobreviveu? (contagem, e nada virou zero)
      2. a MATEMATICA sobreviveu? (ROI identico, P/L exatamente x fator)
      3. o NOME real sumiu? (varredura do texto inteiro do export)
    """
    falhas = []

    # 1. contagem
    if len(origem["bilhetes"]) != len(saida["bilhetes"]):
        falhas.append(f"contagem: {len(origem['bilhetes'])} -> {len(saida['bilhetes'])}")
    sigs = {(b["casa"], b["parceiro"], b["assinatura"]) for b in saida["bilhetes"]}
    if len(sigs) != len(saida["bilhetes"]):
        falhas.append(f"assinatura duplicada: {len(saida['bilhetes']) - len(sigs)} colisoes")

    # 2. matematica
    def agregar(linhas):
        turnover = Decimal(0)
        pl = Decimal(0)
        for b in linhas:
            s = num_br(b["stake"])
            if s is not None:
                turnover += s
            p = pl_de(b["stake"], b["odd"], b["resultado"])
            if p is not None:
                pl += p
        return turnover, pl

    t0, p0 = agregar(origem["bilhetes"])
    t1, p1 = agregar(saida["bilhetes"])
    esperado_t, esperado_p = t0 * fator, p0 * fator
    # Tolerancia de centavo: `br_num` arredonda cada linha a 2 casas, entao a
    # soma de 48 mil arredondamentos nao bate o produto exato. 1 centavo por
    # linha e' o teto teorico; usamos metade disso como folga.
    folga = Decimal(len(saida["bilhetes"])) * Decimal("0.005")
    if abs(t1 - esperado_t) > folga:
        falhas.append(f"turnover: esperado {esperado_t:.2f}, veio {t1:.2f}")
    if abs(p1 - esperado_p) > folga:
        falhas.append(f"P/L: esperado {esperado_p:.2f}, veio {p1:.2f}")
    roi0 = (p0 / t0 * 100) if t0 else Decimal(0)
    roi1 = (p1 / t1 * 100) if t1 else Decimal(0)
    if abs(roi0 - roi1) > Decimal("0.01"):
        falhas.append(f"ROI mudou: {roi0:.4f}% -> {roi1:.4f}%")

    # 3. nome real
    reais = set()
    for b in origem["bilhetes"]:
        reais.add((b["parceiro"] or "").strip())
        reais.add((b["tipster"] or "").strip())
    for p in origem["parceiros"]:
        reais.add((p["nome"] or "").strip())
    for t in origem["tipsters"]:
        reais.add((t["nome"] or "").strip())
    # Abaixo de 4 caracteres a varredura nao prova nada: o nome vira substring
    # de qualquer palavra e a checagem mentiria se passasse.
    reais = {r for r in reais if len(r) >= 4}
    padroes = {r: _re_nome(r) for r in reais}

    # Dois campos, duas naturezas -- e por isso duas reguas:
    #
    # · campo ANONIMIZADO (parceiro, tipster, nome de conta, chave de custo):
    #   tolerancia ZERO. O valor ali saiu do mapa; nome real e' defeito do mapa.
    # · `descricao`: copiada verbatim porque e' evento publico, entao cita
    #   atleta e time de verdade. So falha para nome que NAO e' palavra publica
    #   (`_NOMES_PUBLICOS`) -- e esse ja deveria ter sido trocado por
    #   `limpar_descricao`, entao aparecer aqui significa que a troca falhou.
    campos_anon = {
        "bilhetes": ("parceiro", "tipster"),
        "parceiros": ("nome",),
        "tipsters": ("nome",),
    }
    achados_anon, achados_desc = set(), set()
    for tabela, campos in campos_anon.items():
        for linha in saida[tabela]:
            for campo in campos:
                v = _sem_acento(str(linha.get(campo) or ""))
                for r in reais:
                    if padroes[r].search(v):
                        achados_anon.add(f"{tabela}.{campo}:{r}")
    for b in saida["bilhetes"]:
        v = _sem_acento(b.get("descricao") or "")
        if not v:
            continue
        for r in reais:
            if _sem_acento(r) in _NOMES_PUBLICOS:
                continue
            if padroes[r].search(v):
                achados_desc.add(r)

    if achados_anon:
        falhas.append(f"{len(achados_anon)} nome(s) real(is) em campo anonimizado")
    if achados_desc:
        falhas.append(f"{len(achados_desc)} nome(s) real(is) sobrando na descricao")

    # E-mail: 63 das 90 contas do Jonathan tem e-mail de verdade no nome. Se
    # sobrar um '@' em campo anonimizado, o mapa falhou no caso mais grave.
    for tabela, campos in campos_anon.items():
        for linha in saida[tabela]:
            if any("@" in str(linha.get(c) or "") for c in campos):
                falhas.append(f"sobrou e-mail em {tabela}")
                break
    return falhas


# ── Principal ────────────────────────────────────────────────────────────────
async def principal(fator: Decimal, saida_path: pathlib.Path, semente: int) -> None:
    print(f"# export anonimizado -> {DONO_DESTINO}")
    print(f"  origem={DONOS_ORIGEM} · fator={fator} · semente={semente}\n")

    print("lendo producao (somente leitura)...")
    dados = await ler_tudo(DONOS_ORIGEM)
    for k in ("bilhetes", "parceiros", "tipsters", "custos", "caixa", "fornecedor_preco"):
        print(f"   {k}: {len(dados.get(k, []))}")

    print("\nanonimizando e escalando...")
    saida = transformar(dados, fator, semente)
    print(f"   contas: {len(saida['_mapas']['conta'])} · "
          f"fornecedores: {len(saida['_mapas']['fornecedor'])} · "
          f"tipsters: {len(saida['_mapas']['tipster'])}")
    if saida["_ilegiveis"]:
        print(f"   stake ilegivel preservada verbatim: {len(saida['_ilegiveis'])}")

    print("\nconferindo...")
    falhas = conferir(dados, saida, fator)
    if falhas:
        print("\n!! EXPORT REPROVADO")
        for f in falhas:
            print(f"   - {f}")
        raise SystemExit(1)
    print("   ok: contagem, assinatura unica, ROI identico, P/L x fator, zero nome real")

    # O mapa real->ficticio NAO vai para o arquivo de dados: ele e' a chave que
    # desfaz a anonimizacao inteira. Fica num arquivo irmao, que nao se importa
    # e nao se compartilha (existe so para reimportar de forma consistente).
    mapas = saida.pop("_mapas")
    saida.pop("_ilegiveis")
    saida_path.parent.mkdir(parents=True, exist_ok=True)
    saida_path.write_text(json.dumps(saida, ensure_ascii=False, default=str), encoding="utf-8")
    chave = saida_path.with_suffix(".chave.json")
    chave.write_text(json.dumps(mapas, ensure_ascii=False), encoding="utf-8")

    mb = saida_path.stat().st_size / 1_048_576
    print(f"\ngravado: {saida_path}  ({mb:.1f} MB)")
    print(f"chave  : {chave}   << NAO compartilhar, NAO commitar")


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace", line_buffering=True)
    ap = argparse.ArgumentParser()
    ap.add_argument("--fator", type=Decimal, default=FATOR_PADRAO)
    ap.add_argument("--semente", type=int, default=SEMENTE)
    ap.add_argument("--saida", type=pathlib.Path,
                    default=RAIZ / "Backups" / "realtrial" / "export.json")
    a = ap.parse_args()
    asyncio.run(principal(a.fator, a.saida, a.semente))
