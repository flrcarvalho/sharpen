"""Contrato de TEXTO de 4 campos — Bet365. Integração LOCAL e DESLIGADA (s386).

    bloco do robô ─► NÚMEROS pelo código ─► coberto? ─► IA devolve 4 campos ─► linha final
                                              └─ não ─► caminho atual (IA de 11 colunas)

A IA de hoje recebe ~54 mil tokens de manual e reescreve as 11 colunas do TSV, e depois
quatro corretores refazem o que ela copiou. Neste caminho a IA decide só o que pede
julgamento — esporte, categoria e descrição — e o CÓDIGO lê do bloco código, data, stake,
odd e resultado, pelas funções que o servidor já usa para conferir esses campos.

DESLIGADO de três formas, e as três são necessárias para ele rodar:
  • `main.py` NÃO importa este módulo. Ligar é uma mudança de código, revisada.
  • `CONTRATO_TEXTO_CASAS` vazio (padrão) = nenhuma casa.
  • `CASAS_SUPORTADAS` = só `BET365`. Outra casa na variável é ignorada.

INVARIANTE (a do `tradutor.py`): **nunca inventa**. Campo ausente, ambíguo ou estimado
manda o bilhete INTEIRO para o caminho atual, com o motivo. Resposta da IA sem linha,
com código que não está no texto, com código repetido, fora do formato ou reprovada
pelos gates de descrição também manda o bilhete para o caminho atual — que tem
repescagem, fidelidade e todas as correções de hoje. O pior caso é pagar a chamada de
hoje; o inaceitável é gravar errado.

REAPROVEITA, NÃO COPIA (coordenação com a frente do tradutor): `_cabecalho`,
`_odd_estrutural`, `_num_bloco`, `_dec_bloco`, `_odd_br`, `_resultado` e as precisões vêm
do próprio `tradutor.py`; `_financeiro_do_texto`, `_veredito_do_retorno`, `calcular_pl` e
`anexar_sistema_tsv` do `repository.py`. Mudou a régua lá, muda aqui.

AS CORREÇÕES DE HOJE, uma por uma, e o que acontece com cada uma neste caminho:
  `_corrigir_codigos_fantasma`  vira a associação por código: linha com código fora do
                                texto é descartada e o bilhete vai ao caminho atual.
  `_reconciliar_orfas`          não se aplica: toda linha nasce com o código do bloco.
  cobertura + repescagem        bilhete sem linha vai ao caminho atual (que repesca).
  `_garantir_fidelidade`        descrição reprovada vai ao caminho atual (que re-pergunta).
  `corrigir_stake_tsv`          stake e odd já saem do bloco; rodar por cima é no-op
                                (provado na demonstração da s386).
  `anexar_sistema_tsv`          continua: a 12ª coluna é anexada aqui.
  `correcoes` / UPSERT          intocados: a linha segue pelo mesmo `/salvar`.

O que NÃO está resolvido está em `STATUS`/`BACKLOG` quando este módulo for ligado; a
lista da s386 está no relatório daquela sessão.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from decimal import localcontext

import prompts
import repository as repo
import taxonomia
import tradutor as trad
from config import CASAS_DIR, GLOBAL_DIR
from descricao_check import checar_descricao, checar_fidelidade

CASAS_SUPORTADAS = frozenset({"BET365"})


def casas_ligadas() -> frozenset:
    """As casas em que o contrato está ligado: `CONTRATO_TEXTO_CASAS` ∩ suportadas."""
    brutas = os.environ.get("CONTRATO_TEXTO_CASAS", "")
    return frozenset(c.strip().upper() for c in brutas.split(",") if c.strip()) & CASAS_SUPORTADAS


def ligado(casa_key: str) -> bool:
    return (casa_key or "").upper() in casas_ligadas()


# ── Prompt enxuto: seções INTEIRAS e VERBATIM dos MASTERs ──────────────────────
# Nenhuma regra é reescrita aqui. Entram as três que decidem esporte, categoria e
# descrição; saem PIPELINE, RESULTADO e OUTPUT (o trabalho que o código faz) e, das três,
# as "Validação Final" e as listas de atletas (que servem para adivinhar o esporte quando
# o print não mostrava — o bloco da Bet365 traz o esporte).

def _sem_secoes(md: str, fora) -> str:
    out, pulando = [], None
    for ln in md.splitlines(keepends=True):
        m = re.match(r"^(#{1,6})\s+(.*)", ln)
        if m:
            nivel = len(m.group(1))
            if pulando is not None and nivel <= pulando:
                pulando = None
            if pulando is None and fora(m.group(2)):
                pulando = nivel
        if pulando is None:
            out.append(ln)
    return "".join(out)


def _so_secoes(md: str, dentro) -> str:
    out, pegando = [], False
    for ln in md.splitlines(keepends=True):
        m = re.match(r"^(#{1,6})\s+(.*)", ln)
        if m and len(m.group(1)) <= 2:
            pegando = bool(dentro(m.group(2)))
        if pegando:
            out.append(ln)
    return "".join(out)


def _validacao(t: str) -> bool:
    return "Validação Final" in t


def build_system_enxuto(casa_key: str) -> list[dict]:
    """Mesmo desenho de cache do `prompts.build_system`: breakpoint nos masters e na casa."""
    masters = [
        _sem_secoes(prompts._read(GLOBAL_DIR / "MASTER_ESPORTES_2026.md"),
                    lambda t: _validacao(t) or "Referências auxiliares" in t
                    or "Contextos auxiliares" in t),
        _sem_secoes(prompts._read(GLOBAL_DIR / "MASTER_APOSTAS_2026.md"), _validacao),
        _sem_secoes(prompts._read(GLOBAL_DIR / "MASTER_DESCRICAO_2026.md"), _validacao),
    ]
    blocos = [{"type": "text", "text": t} for t in masters]
    blocos[-1]["cache_control"] = dict(prompts._CACHE_TTL)
    casa = CASAS_DIR / f"CASA_{casa_key.upper()}.md"
    if casa.exists():
        mapa = _so_secoes(prompts._read(casa), lambda t: "Mapa de mercados" in t
                          or re.match(r"\d+\.\s*Esporte", t))
        if mapa:
            blocos.append({"type": "text", "text": mapa,
                           "cache_control": dict(prompts._CACHE_TTL)})
    return blocos


INSTRUCAO = (
    "Casa: {casa}\n\n"
    "O texto acima traz bilhetes de aposta. Cada bilhete começa em uma linha [Código: X].\n"
    "Para CADA bilhete, escreva UMA linha com 4 campos separados por TAB:\n\n"
    "Código<TAB>Esporte<TAB>Aposta<TAB>Descrição\n\n"
    "- Código: copie exatamente o valor de [Código: X].\n"
    "- Esporte: padrão do MASTER_ESPORTES. Se o bloco informa o esporte, normalize-o pela tabela.\n"
    "- Aposta: categoria do MASTER_APOSTAS, usando o mapa de mercados da casa. Cupom com mais de "
    "uma seleção é Múltipla, inclusive Criar Aposta / bet builder.\n"
    "- Descrição: padrão do MASTER_DESCRICAO. Em Múltipla, as seleções unidas por ' // '.\n\n"
    "Data, stake, odd e resultado NÃO são seus: o sistema os lê direto do bloco. Não os escreva.\n"
    "Responda apenas com as linhas, dentro de um bloco ```tsv, sem cabeçalho e sem comentários. "
    "Uma linha por bilhete, na ordem do texto."
)


# ── Números pelo código ────────────────────────────────────────────────────────

_TIPO_SISTEMA = re.compile(r"^SISTEMA\b", re.I)
_PERNA = re.compile(r"^\s*•\s+(.*)$")
_ODD_PERNA = re.compile(r"@\s+([\d.,]+)")
_SUB = re.compile(r"^\s+–\s+")
_CODIGO = re.compile(r"^\[Código:\s*([^\]\r\n]*?)\s*\]")
_SPLIT = re.compile(r"(?m)(?=^\[Código:\s)")        # o MESMO corte do `main._SUPERBET_SPLIT_RE`


def _tok(s):
    """Primeiro token numérico: o bloco cola aviso depois do número
    (`Odd (estrutural do sistema): 3,5466  ← JÁ CALCULADA …`)."""
    if s in (None, ""):
        return None
    m = re.match(r"\s*([-+]?[\d.,]+)", str(s))
    return m.group(1) if m else None


def _num(s):
    t = _tok(s)
    return trad._num_bloco(t) if t else None


@dataclass(frozen=True)
class _PernaOdd:
    """O que o leitor de NÚMEROS precisa de uma perna. O `tradutor._pernas` recusa a perna
    de Criar Aposta (sub-linhas `–`) de propósito, porque a DESCRIÇÃO dela não está
    portada; para a odd basta o `@` da linha `•`."""
    selecao: str
    odd: str


def _pernas_odd(bloco: str) -> list:
    out = []
    for ln in (bloco or "").splitlines():
        m = _PERNA.match(ln)
        if m:
            mo = _ODD_PERNA.search(m.group(1))
            out.append(_PernaOdd(m.group(1), mo.group(1) if mo else ""))
    return out


@dataclass
class Leitura:
    codigo: str
    bruto: str
    rota: str = "caminho_atual"          # "coberto" | "caminho_atual"
    motivos: list = field(default_factory=list)
    campos: dict = field(default_factory=dict)   # nome -> {valor, estado, fonte, texto?}
    forma: str = ""
    n_pernas: int = 0
    retorno: float | None = None
    tipo: str = ""


def ler_numeros(codigo: str, bruto: str, casa_key: str = "BET365") -> Leitura:
    """Código, data, stake, odd, resultado e P/L de UM bloco da Bet365. Nunca presume."""
    lt = Leitura(codigo=codigo or "", bruto=bruto or "")

    def put(nome, valor, estado, fonte, **extra):
        lt.campos[nome] = dict(valor=valor, estado=estado, fonte=fonte, **extra)
        if estado != "ok":
            lt.motivos.append(f"{nome} {estado} ({fonte})")

    if (casa_key or "").upper() not in CASAS_SUPORTADAS:
        lt.motivos.append(f"casa não suportada: {casa_key}")
        return lt

    fin = repo._financeiro_do_texto(f"[Código: {codigo}]\n{bruto}").get(codigo or "")
    if not codigo:
        put("codigo", None, "ausente", "bloco sem [Código] (o detalhe da bet365 não chegou)")
    else:
        put("codigo", codigo, "ok", "[Código: …] do bloco")

    cab = trad._cabecalho(bruto or "")
    pernas = _pernas_odd(bruto or "")

    if cab.get("Data (evento)"):
        put("data", cab["Data (evento)"], "ok", "Data (evento): kickoff da perna mais recente")
    elif cab.get("Data (colocação)"):
        put("data", cab["Data (colocação)"], "ok", "Data (colocação): CASA_BET365 §4, sem kickoff")
    elif cab.get("Data (encerramento)"):
        put("data", cab["Data (encerramento)"], "estimado",
            "Data (encerramento) = kickoff + folga por esporte (extensão anterior à s339)")
    else:
        put("data", None, "ausente", "nenhuma linha de data")

    stake = None
    if fin is None:
        put("stake", None, "ambiguo", "sem Stake único (_financeiro_do_texto recusou)")
    else:
        stake = _num(fin["stake"])
        if stake and stake > 0:
            put("stake", stake, "ok", "Stake: do bloco", texto=fin["stake"].strip())
        else:
            put("stake", None, "ausente", "Stake ilegível ou zero")
            stake = None

    status = (fin or {}).get("status") or cab.get("Status", "")
    retorno = _num((fin or {}).get("retorno"))
    tipo = (cab.get("Tipo") or "").strip()
    sistema = bool((fin or {}).get("sistema")) or bool(_TIPO_SISTEMA.match(tipo))
    n = len(pernas)
    if sistema:
        forma, odd_bloco = "sistema", _tok(cab.get("Odd (estrutural do sistema)"))
    elif n == 1 and cab.get("Odd"):
        sub = any(_SUB.match(l) for l in (bruto or "").splitlines())
        forma, odd_bloco = ("bet builder" if sub else "simples"), _tok(cab.get("Odd"))
    elif n > 1:
        forma, odd_bloco = "multipla", None
    else:
        forma, odd_bloco = "desconhecida", _tok(cab.get("Odd"))
    lt.forma, lt.n_pernas, lt.retorno, lt.tipo = forma, n, retorno, tipo
    rotulo = trad._resultado(status)
    aberta = "em aberto" in status

    resultado = odd = None
    if n == 0:
        put("resultado", None, "ausente", "nenhuma perna reconhecida no bloco")
        put("odd", None, "ausente", "nenhuma perna reconhecida no bloco")
    elif aberta or rotulo in ("L", "V"):
        resultado = "" if aberta else rotulo
        put("resultado", resultado, "ok", "Status aberto" if aberta else f"Status → {rotulo}")
        if forma == "multipla":
            o = trad._odd_estrutural("BET365", cab, pernas)
            fonte = "produto das pernas (MASTER_RESULTADO §7.1/§7.2)"
        else:
            o = odd_bloco
            fonte = "odd impressa pela casa" + (" (média do sistema, §7.3)" if sistema else "")
        if o and _num(o):
            odd = _num(o)
            put("odd", odd, "ok", fonte, texto=o)
        else:
            put("odd", None, "ausente", fonte + " indisponível")
    elif retorno is not None and stake:
        # W, HW, HL ou cashout: o DINHEIRO decide. A odd de partida é a do MASTER_RESULTADO
        # §5.2.1 (Retorno ÷ Stake) e o `_veredito_do_retorno` é chamado como em produção:
        # só troca pela odd do bloco quando ela revela outro resultado (HW) ou quando a de
        # partida se afasta mais de 0,005 dela.
        legs = (bruto or "").split("Seleções:", 1)[-1]       # linha partida pode estar na sub-linha
        o_ref = odd_bloco
        if forma == "multipla":
            with localcontext() as ctx:
                ctx.prec = trad._PRECISAO_PRODUTO
                prod, ok = trad.Decimal(1), True
                for p in pernas:
                    d = trad._dec_bloco(p.odd)
                    if d is None or d <= 1:
                        ok = False
                        break
                    prod *= d
            if ok:
                with localcontext() as ctx:
                    ctx.prec = trad._PRECISAO_ODD
                    o_ref = trad._odd_br(+prod)
            else:
                o_ref = None
        calc = retorno / stake
        odd_rs = f"{calc:.10f}".rstrip("0").rstrip(".").replace(".", ",")
        ver, odd_nova = repo._veredito_do_retorno(
            stake, calc, retorno, legs, o_ref, odd_bloco_manda=not sistema)
        resultado = ver
        odd_txt = (odd_nova or o_ref) if ver in ("L", "V", "HL") else (odd_nova or odd_rs)
        odd = _num(odd_txt) if odd_txt else None
        put("resultado", resultado, "ok", f"retorno R$ {retorno:.2f} → {ver}")
        if odd and odd > 0:
            fonte = ("§5.2.1: Retorno ÷ Stake" if odd_txt == odd_rs
                     else "fórmula de HW com a odd impressa" if ver == "HW"
                     else "odd do bloco (_veredito_do_retorno)")
            put("odd", odd, "ok", fonte, texto=odd_txt)
        else:
            put("odd", None, "ausente", f"nenhuma odd legível para {ver}")
    else:
        put("resultado", None, "ambiguo", f"Status sem seta e sem retorno legível: {status[:60]!r}")
        put("odd", None, "ambiguo", "depende do resultado")

    if all(lt.campos.get(k, {}).get("estado") == "ok" for k in ("stake", "odd", "resultado")):
        pl = repo.calcular_pl(stake, odd, resultado) if resultado else None
        if resultado and retorno is not None and pl is not None:
            if abs(pl - (retorno - stake)) > max(0.10, abs(retorno) * 0.005):
                put("pl", pl, "ambiguo", f"P/L {pl:.2f} não fecha com retorno−stake do texto")
            else:
                put("pl", pl, "ok", "calcular_pl; fecha com retorno−stake do texto")
        else:
            put("pl", pl, "ok", "calcular_pl" if resultado else "aberta: sem P/L")
    lt.rota = "coberto" if not lt.motivos else "caminho_atual"
    return lt


# ── Partição do texto ──────────────────────────────────────────────────────────

@dataclass
class Particao:
    cobertos: dict = field(default_factory=dict)       # codigo -> Leitura (ordem do texto)
    texto_ia: str = ""                                 # só os blocos cobertos, para a IA de 4 campos
    blocos_ia: list = field(default_factory=list)      # os mesmos, um por item, na ordem do texto
    atual: list = field(default_factory=list)          # [(codigo, bloco_completo, motivos)]


def particionar(texto: str, casa_key: str = "BET365") -> Particao:
    """Parte o texto do robô: bloco coberto vai ao contrato de 4 campos; o resto, intacto,
    ao caminho atual. Nada se perde: todo byte do texto sai por um dos dois lados."""
    p = Particao()
    pedacos = _SPLIT.split(texto or "")
    contagem: dict = {}
    for ped in pedacos:
        m = _CODIGO.match(ped)
        if m:
            contagem[m.group(1)] = contagem.get(m.group(1), 0) + 1
    cobertos_blocos = []
    for ped in pedacos:
        if not ped.strip():
            continue
        m = _CODIGO.match(ped)
        if not m:
            p.atual.append(("", ped, ["texto fora de bloco [Código]"]))
            continue
        codigo = m.group(1)
        corpo = ped[m.end():].lstrip("\n")
        if not codigo:
            p.atual.append(("", ped, ["bloco com [Código] vazio"]))
            continue
        if contagem[codigo] > 1:
            p.atual.append((codigo, ped, ["código repetido no mesmo texto"]))
            continue
        lt = ler_numeros(codigo, corpo, casa_key)
        if lt.rota != "coberto":
            p.atual.append((codigo, ped, lt.motivos))
            continue
        p.cobertos[codigo] = lt
        cobertos_blocos.append(ped.rstrip("\n"))
    p.blocos_ia = cobertos_blocos
    p.texto_ia = "\n\n".join(cobertos_blocos)
    return p


# ── Resposta da IA → linha final ───────────────────────────────────────────────

@dataclass
class Montagem:
    tsv: str = ""                                      # linhas finais, 11 colunas (+12ª em sistema)
    linhas: dict = field(default_factory=dict)         # codigo -> linha final
    atual: list = field(default_factory=list)          # [(codigo, bloco_completo, motivos)] antes E depois
    rejeitados: list = field(default_factory=list)     # os de `atual` que saíram DEPOIS da IA
    ajustes: list = field(default_factory=list)        # (codigo, campo, da IA, do código)
    descartadas: list = field(default_factory=list)    # (linha da IA, motivo)


def _linhas_resposta(resposta: str) -> list[str]:
    """Linhas de TODOS os blocos ```tsv (a resposta junta várias chamadas). Sem bloco
    nenhum, as linhas com TAB — prosa sem TAB não é linha de ninguém."""
    blocos = re.findall(r"```tsv\s*\n(.*?)```", resposta or "", re.S)
    if blocos:
        return [l for b in blocos for l in b.splitlines() if l.strip()]
    return [l for l in (resposta or "").splitlines() if "\t" in l]


def montar(particao: Particao, resposta_ia: str, casa_display: str, parceiro: str) -> Montagem:
    """Associa a resposta de 4 campos aos blocos cobertos e monta a linha final.

    Bilhete sem exatamente UMA linha válida para ele vai ao caminho atual, com o motivo."""
    mt = Montagem(atual=list(particao.atual))
    esportes = set(taxonomia.esportes_canonicos())
    categorias = set(taxonomia.categorias_canonicas())
    por_cod: dict = {}
    for ln in _linhas_resposta(resposta_ia):
        cols = [c.strip() for c in ln.split("\t")]
        if len(cols) != 4:
            mt.descartadas.append((ln, f"{len(cols)} campos, esperado 4"))
            continue
        if cols[0] not in particao.cobertos:
            mt.descartadas.append((ln, "código que não está entre os blocos enviados"))
            continue
        por_cod.setdefault(cols[0], []).append(cols)

    def para_atual(cod, motivo):
        item = (cod, f"[Código: {cod}]\n{particao.cobertos[cod].bruto}", [motivo])
        mt.atual.append(item)
        mt.rejeitados.append(item)

    linhas = []
    for cod, lt in particao.cobertos.items():
        achadas = por_cod.get(cod, [])
        if len(achadas) != 1:
            para_atual(cod, "IA sem linha para o bilhete" if not achadas
                       else f"IA devolveu {len(achadas)} linhas para o mesmo código")
            continue
        _, esporte, aposta, descricao = achadas[0]
        # O que a ESTRUTURA do bloco já decide, o código decide (MASTER_ESPORTES §2 e
        # MASTER_APOSTAS "Bet Builder = Múltipla"); a IA é conferida contra isso.
        if trad._TIPO_MULTIPLA.match(lt.tipo) and esporte != "Múltiplos":
            mt.ajustes.append((cod, "esporte", esporte, "Múltiplos"))
            esporte = "Múltiplos"
        if (lt.n_pernas > 1 or lt.forma == "bet builder") and aposta != "Múltipla":
            mt.ajustes.append((cod, "aposta", aposta, "Múltipla"))
            aposta = "Múltipla"
        if esporte not in esportes:
            para_atual(cod, f"esporte fora do MASTER: {esporte!r}")
            continue
        if aposta not in categorias:
            para_atual(cod, f"categoria fora do MASTER: {aposta!r}")
            continue
        erros = [x for x in checar_descricao(aposta, descricao) if x[0] == "erro"]
        erros += [x for x in checar_fidelidade(descricao, lt.bruto) if x[0] == "erro"]
        if erros:
            para_atual(cod, "descrição reprovada: " + "; ".join(e[2][:80] for e in erros))
            continue
        c = lt.campos
        linha = "\t".join([
            c["data"]["valor"], esporte, "", casa_display, parceiro or "",
            aposta, descricao, c["stake"]["texto"], c["odd"]["texto"],
            c["resultado"]["valor"], cod,
        ])
        mt.linhas[cod] = linha
        linhas.append(linha)
    tsv = "\n".join(linhas)
    if tsv:
        tsv, _ = repo.anexar_sistema_tsv(tsv, particao.texto_ia)
        mt.linhas = {l.split("\t")[10]: l for l in tsv.split("\n")}
    mt.tsv = tsv
    return mt


# ── Peças do fluxo (puras, testáveis sem rede) ─────────────────────────────────

def lotes_ia(particao: Particao, por_lote: int) -> list[str]:
    """Os blocos cobertos em lotes de `por_lote`, na ordem do texto: um texto por chamada."""
    b = particao.blocos_ia
    return ["\n\n".join(b[i:i + por_lote]) for i in range(0, len(b), max(1, por_lote))]


def texto_dos_encaminhados(atual: list) -> str:
    """O texto que o caminho de hoje recebe: os blocos encaminhados, INTACTOS, na ordem
    em que apareceram (antes da IA primeiro, pela ordem do texto; depois os rejeitados)."""
    return "\n\n".join(bloco.rstrip("\n") for _cod, bloco, _m in atual if bloco.strip())


def texto_dos_aceitos(particao: Particao, montagem: Montagem) -> str:
    """Só os blocos cujas linhas o contrato entregou — é o que a barreira de recaptura e
    a sombra do tradutor devem lembrar desta metade (os rejeitados, a outra metade lembra)."""
    return "\n\n".join(b for b in particao.blocos_ia
                       if (m := _CODIGO.match(b)) and m.group(1) in montagem.linhas)


def pontuar_4campos(resposta: str, particao: Particao) -> dict:
    """Juiz DETERMINÍSTICO da resposta de 4 campos, com as MESMAS chaves de
    `repository.pontuar_saida` — é o que deixa a sombra de modelo comparar o Haiku no
    contrato novo. `coluna_comida` aqui = linha com número de campos diferente de 4."""
    out = {"blocos": len(particao.cobertos), "linhas": 0, "sem_codigo": 0, "cod_inventado": 0,
           "coluna_comida": 0, "fora_master": 0, "infiel": 0, "descricoes": 0}
    devolvidos = set()
    for ln in _linhas_resposta(resposta):
        out["linhas"] += 1
        cols = [c.strip() for c in ln.split("\t")]
        if len(cols) != 4:
            out["coluna_comida"] += 1
            continue
        cod, _esporte, aposta, desc = cols
        if cod not in particao.cobertos:
            out["cod_inventado"] += 1
        else:
            devolvidos.add(cod)
        if not desc:
            continue
        out["descricoes"] += 1
        if [p for p in checar_descricao(aposta, desc) if p[0] == "erro"]:
            out["fora_master"] += 1
        lt = particao.cobertos.get(cod)
        if lt and [p for p in checar_fidelidade(desc, lt.bruto) if p[0] == "erro"]:
            out["infiel"] += 1
    out["sem_codigo"] = len(set(particao.cobertos) - devolvidos)
    return out


def ordenar_final(texto: str, linhas_antigas: list[str], linhas_contrato: list[str]) -> list[str]:
    """Junta as duas metades na ORDEM DE HOJE: a Bet365 chega do mais novo para o mais
    antigo e a planilha quer o contrário, então a ordem final é a do texto INVERTIDA — a
    mesma inversão por linha que `_combine_parallel_results(reverse_rows=True)` faz.

    Linha do caminho de hoje sem código (não deveria haver na Bet365, mas o bloco de
    `[Código: ]` vazio existe) fica logo depois da linha que a precedia lá: nunca some e
    nunca troca de lugar com um bilhete que tem código."""
    pos: dict = {}
    for m in re.finditer(r"(?m)^\[Código:\s*([^\]\r\n]*?)\s*\]", texto or ""):
        if m.group(1):
            pos.setdefault(m.group(1), len(pos))
    n = len(pos)

    def cod(linha):
        c = linha.split("\t")
        return c[10].strip() if len(c) > 10 else ""

    chaves = []
    ultimo = -1
    for i, l in enumerate(linhas_antigas):
        c = cod(l)
        if c in pos:
            ultimo = n - pos[c]
            chaves.append(((ultimo, 0, i), l))
        else:
            chaves.append(((ultimo, 1, i), l))
    for i, l in enumerate(linhas_contrato):
        c = cod(l)
        chaves.append(((n - pos.get(c, -1), 0, len(linhas_antigas) + i), l))
    chaves.sort(key=lambda kv: kv[0])
    return [l for _k, l in chaves]


def juntar_resultado(resultado_antigo: str, linhas: list[str], cabecalho: str) -> str:
    """O `resultado` do `done`, no formato de hoje: bloco ```tsv com cabeçalho e as linhas,
    mais o resto do texto do caminho antigo (as Notas Críticas) intacto."""
    novo = "```tsv\n" + "\n".join([cabecalho] + linhas) + "\n```"
    m = re.search(r"```tsv\n(.*?)\n```", resultado_antigo or "", re.S)
    if m:
        return resultado_antigo[:m.start()] + novo + resultado_antigo[m.end():]
    resto = (resultado_antigo or "").strip()
    return novo + ("\n\n" + resto if resto else "\n\n## Notas Críticas\nNenhuma")


def resumo(particao: Particao, montagem: Montagem) -> dict:
    """O que vai no `done` e no log: contagens e motivos, para o encaminhamento ser
    auditável sem abrir o banco. Extensão antiga e falso alarme do avaliador aparecem
    aqui pelo nome, sem que o módulo precise resolvê-los."""
    def motivos(itens):
        c: dict = {}
        for _cod, _b, ms in itens:
            for m in ms:
                chave = re.sub(r"'[^']*'", "'…'", m)[:120]
                c[chave] = c.get(chave, 0) + 1
        return dict(sorted(c.items(), key=lambda kv: -kv[1]))
    return {
        "cobertos": len(particao.cobertos),
        "linhas": len(montagem.linhas),
        "encaminhados_antes": len(particao.atual),
        "rejeitados_depois": len(montagem.rejeitados),
        "motivos_antes": motivos(particao.atual),
        "motivos_depois": motivos(montagem.rejeitados),
        "ajustes": [list(a) for a in montagem.ajustes],
        "descartadas": [d[1] for d in montagem.descartadas],
    }
