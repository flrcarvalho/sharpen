"""Virada da Ficha (`03_REGUA_NUMEROS §7`; s409 construída desligada, s411 ligada casa a casa).

Regra do Feca: **recusada nunca pode significar aposta perdida.** E, desde 12/10 à noite: **na casa
virada a aposta sai da IA na origem, enquanto está ABERTA.** A IA só recebe o que a Ficha não
resolveu: Ficha recusada, termo fora do dicionário, ou cru que não chegou a tempo.

Dois caminhos chegam aqui, e os dois chamam o mesmo `aplicar`:

  1. **A rota da Ficha** (`ficha.receber`): o cru novo chega, a Ficha aceita grava na planilha
     pelo MESMO `/salvar` de hoje (`main.gravar_tsv`, `origem = 'ficha'`).
  2. **O `/extrair`** (`main._dedup_superbet_text` → `resolver_no_extrair`): antes de mandar
     qualquer coisa à IA, ESPERA o cru da mesma captura terminar de chegar (o texto é postado
     primeiro e o cru logo depois, menos de 1 s antes do extrair; `esperar_cru`), e então, para
     cada código do texto que não está liquidado no banco, monta a Ficha do cru GUARDADO mais
     recente. É isso que passa para a Ficha a aposta aberta que a IA gravou antes da virada: a
     extensão não reenvia cru igual, então a rota nunca o veria de novo. Todo código resolvido
     pela Ficha (aberto ou liquidado) SAI do lote da IA.

**Cru velho não esconde a liquidação (furo N3, parecer 012; s412).** No `/extrair`, a Ficha só
tira o código da fila da IA se o cru usado é DESTA captura (chegou DEPOIS do último `/extrair`
da mesma casa e dono; R32, s416) ou se o bloco de texto não mudou desde a última leitura (a
barreira de hoje). Texto
mudado sem cru novo (a extensão recarregada sem F5 na aba da casa manda o texto e não o cru):
**desde a D39 (01/11/2026) a falta de cru nunca vai à IA.** Cru guardado já LIQUIDADO grava pela
Ficha (cru final não esconde liquidação; o veredito do texto confere); cru ABERTO, ou que não
chegou, segura a aposta como pendente com o aviso "captura incompleta"; e o código que foi à IA e
não virou linha também vira pendente. Só a Ficha RECUSADA com texto mudado segue para a IA
(`sem_cru_novo` no `virada_log`). Ver o bloco "D39" mais abaixo.

**Esporte e categoria passam pelo Master antes de gravar** (`app/taxonomia.py`; R27): valor fora
dele vai para a IA (`fora do Master`). O dicionário vale para todos os usuários da casa.

**A descrição sai do dicionário de descrição** (s413, `app/descricao_ficha.py`; regra do Feca:
chamada extra à IA só para a descrição, nunca): o mercado aprendido monta a descrição como a IA
monta. Desde a D40 (01/11/2026) o mercado sem par grava com o texto da casa e NÃO vai à IA
(`descricao_para_gravar`); antes ia (`descrição fora do dicionário`), e a semente o aprendia logo
depois, com 1 voto (D24).

Quando a aposta liquida, é a Ficha que grava o resultado: o cru muda, chega pela rota, e o
UPSERT atualiza a linha aberta (resultado, e odd/stake/data, que só congelam quando resolve).

**O passado não é mexido (D10, nas palavras do Feca: "não mexer no passado é não ir futricar as
apostas de mês passado").** Aposta já LIQUIDADA no banco nunca é reescrita pela Ficha, venha de
onde vier: o dinheiro já bateu no backtest e não há ganho nisso. O pré-dedup de sempre já a tira
do lote da IA. Aposta ABERTA, de qualquer origem, passa para a Ficha.

`ficha_virada` guarda, por código, o que a Ficha decidiu da última vez (`ficha` ou `ia`) e a
impressão do cru: cru igual com decisão `ficha` sai do lote sem regravar.

`FICHA_CASAS_VIRADAS` = lista de casas. **Vazia = nada vira.** `*` NÃO vale. Desligar a chave
volta a casa ao caminho de hoje na hora, sem deploy. Falha aqui NUNCA derruba a rota nem o
`/extrair`: na dúvida, o código vai para a IA.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from datetime import datetime, timezone

import cambio as _cambio
import casa_chave as _cc
import descricao_ficha as _desc
import dicionario as _dic
import ficha as _ficha

logger = logging.getLogger("scanner")

ORIGEM = "ficha"
# Sistema uniforme (`MASTER_RESULTADO §7.3`): `k` = tamanho de cada linha.
_NOME_K = {1: "Simples", 2: "Duplas", 3: "Triplas", 4: "Quádruplas", 5: "Quíntuplas",
           6: "Sêxtuplas"}
_SISTEMA_VB = re.compile(r"^(\d+) x (\d+) de (\d+)$")

# Corrida cru × extrair (Feca, 12/10): espera do `/extrair` na casa virada.
ESPERA_MAX = 8.0        # teto, com cru ainda em processamento
FOLGA = 1.5             # sem cru em voo nem recente: espera isto por um POST que está no fio
RECENTE = 3.0           # cru terminado até isto antes do extrair = é o desta captura
# Cru DESTA captura (N3) = chegou depois do último `/extrair` da mesma casa e dono (R32, s416;
# o `virada_log` guarda o instante). A janela fixa de 30 s deixava de fora o cru que chega
# antes (Duel, 14/10: 13 crus 32 s antes do `/extrair`, 8 apostas à IA à toa) e só vale
# quando a casa ainda não tem `/extrair` nenhum no log.
JANELA_CRU = 30.0
# A espera supõe UM processo só: `_em_voo` e `_ultimo_fim` vivem na memória do processo; com
# mais de uma réplica o cru pode entrar noutra e o `/extrair` não o veria em voo.
_em_voo: dict[tuple, int] = {}
_ultimo_fim: dict[tuple, float] = {}


def casas_viradas() -> frozenset:
    brutas = os.environ.get("FICHA_CASAS_VIRADAS", "")
    return frozenset(c.strip().upper() for c in brutas.split(",") if c.strip() and c.strip() != "*")


def virada(casa_key: str) -> bool:
    return (casa_key or "").upper() in casas_viradas()


def chave_da_casa(casa: str) -> str:
    """Nome de exibição → chave (`DEX Sport` → `DEXSPORT`, `Sportsbet.io` → `SPORTSBETIO`), a
    mesma régua da sessão (`casa_chave.chave`; s438 tirou também o ponto e o acento)."""
    return _cc.chave(casa)


# A chave de `bilhetes.casa`/`parceiros.casa` no SQL, pela MESMA regra (s438, D39).
_K = _cc.sql("casa")
_KB = _cc.sql("b.casa")


def _limpo(v) -> str:
    """Texto de campo de TSV: TAB e quebra de linha deslocariam as colunas."""
    return " ".join(str(v or "").split())


# ── corrida: o `/extrair` espera o cru da mesma captura ─────────────────────────────────

def cru_entrou(dono: str, casa_key: str) -> None:
    k = (dono, (casa_key or "").upper())
    _em_voo[k] = _em_voo.get(k, 0) + 1


def cru_saiu(dono: str, casa_key: str) -> None:
    k = (dono, (casa_key or "").upper())
    _em_voo[k] = max(0, _em_voo.get(k, 0) - 1)
    _ultimo_fim[k] = time.monotonic()


async def esperar_cru(dono: str, casa_key: str, maximo: float = ESPERA_MAX,
                      folga: float = FOLGA) -> float:
    """Espera o cru da captura terminar de chegar. Devolve os segundos esperados.

    Sai quando nada está em processamento E (um cru terminou há pouco, ou a folga passou),
    ou no teto. Captura sem cru novo (nada mudou na casa) custa só a folga."""
    k = (dono, (casa_key or "").upper())
    t0 = time.monotonic()
    while True:
        agora = time.monotonic()
        fim = _ultimo_fim.get(k)
        recente = fim is not None and fim >= t0 - RECENTE
        if _em_voo.get(k, 0) == 0 and (recente or agora - t0 >= folga):
            return agora - t0
        if agora - t0 >= maximo:
            logger.warning("virada: %s %s · o cru não terminou em %.0f s; segue sem ele",
                           dono, casa_key, maximo)
            return agora - t0
        await asyncio.sleep(0.05)


# ── a linha da planilha ─────────────────────────────────────────────────────────────────

def descricao(f: dict, termos: dict) -> str | None:
    """A descrição da Ficha SÓ pelo dicionário de descrição (`descricao_ficha.montar`): perna por
    perna, unidas por ` // `, com a forma fixada pelo Feca (`dicionario.descricao_perna`) na
    frente. None = algum mercado sem par. É a forma ESTRITA, de quem pergunta "o dicionário
    cobre?" (a regravação da semente, os scripts); quem GRAVA usa `descricao_para_gravar`."""
    return _desc.montar(f, termos, _dic.descricao_perna)[0]


def descricao_para_gravar(f: dict, termos: dict) -> str | None:
    """D40 (Feca, 01/11/2026): descrição desconhecida nunca manda a aposta à IA. A perna sem par
    grava com o texto da casa (`<mercado da casa> - <seleção da casa> [A v B]`,
    `descricao_ficha.texto_da_casa`), sem marca para corrigir; as outras saem do dicionário. None
    só se uma perna não tem nem mercado nem seleção (aí a IA lê).

    A regravação da semente (`dicionario.regravar_mes`) continua ESTRITA de propósito: quando o
    dicionário aprende o mercado, ela troca o texto da casa pela forma do dicionário; e se uma
    chave sumir do dicionário (o defeito E1 da D42), ela não troca uma descrição boa pelo texto
    da casa."""
    return _desc.montar(f, termos, _dic.descricao_perna, texto_da_casa_se_faltar=True)[0]


def _sistema(f: dict) -> str:
    """12ª coluna (`N x Rótulo`, a do `anexar_sistema_tsv`), quando a Ficha diz a estrutura.
    Hoje a Altenar (`vb`: `3 x 2 de 3`). Formato que não se lê = vazio, nunca um palpite."""
    if f.get("tipo") != "sistema":
        return ""
    m = _SISTEMA_VB.match(_limpo(f.get("sistema")))
    if not m:
        return ""
    linhas, k = int(m.group(1)), int(m.group(2))
    return f"{linhas}x {_NOME_K[k]}" if k in _NOME_K else ""


def _carimbo(f: dict) -> str | None:
    """`colocada_em` no formato do `carimbos_do_texto` (14 dígitos), no fuso de Brasília: é a
    data em que o dinheiro saiu, e a cotação da conta em outra moeda sai dela."""
    d = _ficha._instante(f.get("colocada_em"))
    return d.astimezone(_ficha._BRT).strftime("%Y%m%d%H%M%S") if d else None


def linha_tsv(f: dict, casa: str, parceiro: str, esporte: str, categoria: str,
              descricao_: str) -> str:
    """A linha da planilha (`MASTER_OUTPUT §2`, 10 colunas + código + sistema) de uma Ficha
    ACEITA, com esporte, categoria e descrição JÁ traduzidos (`dicionario.traduzir`,
    `descricao`)."""
    d = _ficha.derivar(f)
    col = [
        d["data"], _limpo(esporte), "", _limpo(casa), _limpo(parceiro), _limpo(categoria),
        _limpo(descricao_), d["stake"], d["odd"] or "", d["resultado"], _limpo(f.get("codigo")),
    ]
    if (s := _sistema(f)):
        col.append(s)
    return "\t".join(col)


async def gravar_na_planilha(dono: str, casa: str, parceiro: str, itens: list[tuple]) -> dict:
    """Grava Fichas ACEITAS em `bilhetes` pelo `/salvar`. `itens` = [(Ficha, esporte, categoria,
    descrição)]. Devolve a resposta dele."""
    if not itens:
        return {"salvos": 0, "rejeitados": [], "alertas": []}
    import main as _main          # tardio: o `main` inclui o router da Ficha
    linhas, carimbos, freebets, moedas = [], {}, {}, set()
    for f, esporte, categoria, desc in itens:
        linhas.append(linha_tsv(f, casa, parceiro, esporte, categoria, desc))
        cod = _limpo(f.get("codigo"))
        if (c := _carimbo(f)):
            carimbos[cod] = c
        fb = _ficha._dec(f.get("stake_freebet"))
        if fb is not None and fb > 0:
            freebets[cod] = _ficha._odd_br(fb)
        if f.get("moeda"):
            moedas.add(str(f["moeda"]).upper())
    corpo = _main.SalvarRequest(tsv="\n".join(linhas), casa=casa, parceiro=parceiro,
                                carimbos=carimbos, freebets=freebets, moedas=sorted(moedas))
    r = await _main.gravar_tsv(corpo, dono, dono, origem=ORIGEM)
    if r.get("rejeitados"):
        logger.warning("virada: %s %s · %d linha(s) da Ficha recusada(s) no /salvar: %s",
                       dono, casa, len(r["rejeitados"]), r["rejeitados"][:2])
    return r


# ── a decisão por código ────────────────────────────────────────────────────────────────

# O motivo de cada código que fica com a IA → a coluna do `virada_log` (s412).
MOTIVOS = {
    "Ficha recusada": "ficha_recusada",
    "termo fora do dicionário": "termo_fora",
    "descrição fora do dicionário": "descricao_fora",
    "fora do Master": "fora_do_master",
    "recusada no /salvar": "recusada_salvar",
    "cru não chegou": "cru_nao_chegou",
    "texto mudou sem cru novo": "sem_cru_novo",
    "captura incompleta esgotada": "captura_esgotada",      # D39: a saída do segurado
}
ESGOTADA = "captura incompleta esgotada"


def no_master(esporte: str | None, categoria: str | None) -> bool:
    """Esporte e categoria são valores do Master (`app/taxonomia.py`, que LÊ os MASTERs)."""
    import taxonomia
    return esporte in taxonomia.esportes_canonicos() and \
        categoria in taxonomia.categorias_canonicas()


async def _liquidados(conn, dono: str, casa_key: str, codigos: list[str]) -> set[str]:
    """Códigos já LIQUIDADOS no banco NESTA casa, de qualquer origem: a Ficha não os reescreve
    (D10). O mesmo código noutra casa do dono é outra aposta (s423, BACKLOG §4.18): sem a casa,
    a Ficha nem a decidia, e ela não gravava, não ficava `ia` nem virava pendente."""
    rows = await conn.fetch(
        "SELECT DISTINCT codigo_bilhete FROM bilhetes WHERE dono = $1 "
        "AND codigo_bilhete = ANY($2::text[]) AND extraction_state = 'resolvida' "
        f"AND {_K} = $3",
        dono, codigos, casa_key)
    return {r["codigo_bilhete"] for r in rows}


async def _no_banco(conn, dono: str, casa_key: str, codigos: list[str]) -> set[str]:
    """Códigos com linha no banco NESTA casa, em qualquer estado. "Cru igual, já gravado pela
    Ficha" só vale com a linha lá: o usuário que EXCLUI a aposta e recaptura manda o mesmo cru,
    e sem esta conferência a Ficha a dava por gravada e ela não voltava, nem pela IA (s429)."""
    if not codigos:
        return set()
    rows = await conn.fetch(
        "SELECT DISTINCT codigo_bilhete FROM bilhetes WHERE dono = $1 "
        f"AND codigo_bilhete = ANY($2::text[]) AND {_K} = $3",
        dono, codigos, casa_key)
    return {r["codigo_bilhete"] for r in rows}


async def aplicar(conn, dono: str, casa_key: str, casa: str, parceiro: str,
                  candidatas: dict) -> tuple[set, dict]:
    """`candidatas` = {código: (Ficha ou None, motivos de recusa)}. Grava o que a Ficha resolve
    e devolve (códigos que a Ficha resolveu, {código: motivo} dos que ficam com a IA).
    Código liquidado no banco não entra em nenhum dos dois: o pré-dedup de sempre o tira."""
    casa_key = (casa_key or "").upper()
    cods = [c for c in candidatas if c]
    if not cods:
        return set(), {}
    liquidados = await _liquidados(conn, dono, casa_key, cods)
    termos = await _dic.carregar(conn, casa_key)
    estado = {r["codigo"]: (r["impressao"], r["estado"]) for r in await conn.fetch(
        "SELECT codigo, impressao, estado FROM ficha_virada WHERE dono = $1 AND casa = $2 "
        "AND codigo = ANY($3::text[])", dono, casa_key, cods)}
    gravados = await _no_banco(conn, dono, casa_key,
                               [c for c in cods if (estado.get(c) or ("", ""))[1] == "ficha"])
    resolvidos, fica, novo_estado, gravar = set(), {}, {}, []
    sem_par: list = []            # D42: as pernas que vão com o texto da casa (`virada.py:145`)

    def ia(cod, motivo):
        fica[cod] = motivo
        novo_estado[cod] = ("", "ia", motivo)

    for cod in cods:
        if cod in liquidados:
            continue
        f, motivos = candidatas[cod]
        if f is None or motivos:
            ia(cod, "Ficha recusada")
            continue
        esporte, categoria, faltam = _dic.traduzir(f, termos)
        if faltam:
            ia(cod, "termo fora do dicionário")
            continue
        if not no_master(esporte, categoria):
            ia(cod, "fora do Master")
            continue
        desc = descricao_para_gravar(f, termos)        # D40: perna sem par, texto da casa
        if not desc:
            ia(cod, "descrição fora do dicionário")
            continue
        imp = f.get("impressao") or ""
        if estado.get(cod) == (imp, "ficha") and cod in gravados:
            resolvidos.add(cod)            # cru igual, já gravado pela Ficha: só sai do lote
            continue
        gravar.append((f, esporte, categoria, desc))
        sem_par += [(casa_key, "descricao", k, "sem par no dicionário (gravada com o texto da "
                     "casa)", None, desc) for k in _desc.montar(f, termos, _dic.descricao_perna,
                                                                True)[1]]
    if gravar:
        try:
            r = await gravar_na_planilha(dono, casa, parceiro, gravar)
            recusadas = {int(x.get("linha") or 0) for x in r.get("rejeitados") or []}
        except Exception:  # noqa: BLE001 — o texto cobre: vai para a IA
            logger.exception("virada: falha ao gravar %d Ficha(s) de %s/%s; vão pela IA",
                             len(gravar), dono, casa_key)
            recusadas = set(range(1, len(gravar) + 1))
        for i, (f, *_) in enumerate(gravar, 1):
            cod = _limpo(f.get("codigo"))
            if i in recusadas:
                ia(cod, "recusada no /salvar")
            else:
                resolvidos.add(cod)
                novo_estado[cod] = (f.get("impressao") or "", "ficha", "")
    await _gravar_estados(conn, dono, casa_key, novo_estado)
    if sem_par:
        try:
            await _dic.gravar_recusas(conn, sem_par, origem="gravacao")
        except Exception:  # noqa: BLE001 — o registro nunca derruba a gravação
            logger.exception("virada: semente_recusa (sem par) não gravada")
    if fica:
        logger.info("virada: %s %s · ficam com a IA: %s", dono, casa_key,
                    {m: list(fica.values()).count(m) for m in set(fica.values())})
    return resolvidos, fica


async def _gravar_estados(conn, dono: str, casa_key: str, novo_estado: dict) -> None:
    for cod, (imp, est, motivo) in novo_estado.items():
        await conn.execute(
            """INSERT INTO ficha_virada (dono, casa, codigo, impressao, estado, motivo)
               VALUES ($1, $2, $3, $4, $5, $6)
               ON CONFLICT (dono, casa, codigo) DO UPDATE SET impressao = EXCLUDED.impressao,
                 estado = EXCLUDED.estado, motivo = EXCLUDED.motivo, atualizado_em = NOW()""",
            dono, casa_key, cod, imp, est, motivo)


async def _pool_conn():
    from database import get_pool
    return await get_pool()


async def gravar_aceitas(sess, registros: list[dict]) -> int:
    """Rota da Ficha, cru NOVO. Devolve quantas a Ficha resolveu. Nunca levanta."""
    if not virada(sess.casa_key):
        return 0
    candidatas = {}
    for r in registros:
        f = json.loads(r["ficha"])
        if r.get("codigo"):
            candidatas[r["codigo"]] = (f if r.get("aceita") else None, r.get("motivos") or [])
    try:
        pool = await _pool_conn()
        async with pool.acquire() as conn:
            resolvidos, _ = await aplicar(conn, sess.dono, sess.casa_key, sess.casa,
                                          sess.parceiro, candidatas)
    except Exception:  # noqa: BLE001 — o texto cobre; derrubar a rota perderia o cru seguinte
        logger.exception("virada: falha na rota para %s/%s; vão pela IA", sess.dono, sess.casa_key)
        return 0
    return len(resolvidos)


async def ultimo_extrair(conn, dono: str, casa_key: str):
    """O instante do último `/extrair` desta casa e dono (a linha do `virada_log`, gravada no
    fim de cada um), ou None. O `/extrair` de AGORA ainda não tem linha: ele a grava depois."""
    return await conn.fetchval("SELECT max(criado_em) FROM virada_log WHERE dono = $1 AND "
                               "casa = $2", dono, (casa_key or "").upper())


# ── D39 (Feca, 01/11/2026): falta de cru nunca vai à IA, e aposta nunca some em silêncio ───
# Medido (parecer 022): dos 976 códigos cujo último motivo foi "texto mudou sem cru novo", 963
# tinham o cru guardado JÁ LIQUIDADO, e o resultado dele bate 100% com o que a IA gravou (762 L,
# 209 W, 5 V); só 4, de cru ainda aberto, viraram L (a liquidação que a N3 protege). Então:
#   (a) cru guardado LIQUIDADO: a Ficha grava, sem IA. Cru final não esconde liquidação. A
#       conferência contra uma reliquidação é o veredito que o próprio texto traz
#       (`Status: … → X`, as 13 casas viradas o escrevem): se ele contradiz o cru, a aposta
#       espera um cru novo, como no (b);
#   (b) cru guardado ABERTO com texto mudado, ou cru que não chegou: a aposta NÃO vai à IA e
#       fica pendente com o aviso "captura incompleta" (atualizar a aba da casa e extrair de novo
#       traz o cru). Ficha RECUSADA continua com a IA: ali só o texto lê;
#   (c) código que foi à IA num `/extrair` ANTERIOR e não virou linha (o leitor recusou a linha
#       da IA, o `/salvar` a recusou, ou o lote nem foi salvo): pendente com o mesmo aviso. Duel
#       2728364620980039864, 31/10: duas idas à IA, duas linhas recusadas pelo leitor, 22 h fora
#       do banco, de volta só na 3ª ida. Aqui só AVISA: regravar sozinho recriaria a aposta que
#       o usuário apagou de propósito (a tela de Extração apaga sem lixeira até a Fase 7).
# Sem trava de envio duplo (decisão do Feca, 01/11): ela pularia a aposta recapturada depois de
# apagada. `ficha_virada.aviso` diz POR QUE a aposta está pendente; `pendente_desde`, desde quando.
AVISO_NAO_LIDA = "nao_lida"                  # s423: a Ficha recusou e o texto não trouxe
AVISO_INCOMPLETA = "captura_incompleta"      # (b)
AVISO_SEM_LINHA = "sem_linha"                # (c)
# (c) só olha decisão tomada depois da D39: as de antes incluem apostas que o usuário apagou ou
# refez à mão (os 16 de 14/10 do Jaao26), e avisar delas seria ruído sem saída.
D39_DESDE = datetime(2026, 11, 2, 1, 0, tzinfo=timezone.utc)      # 01/11/2026 22:00 de Brasília
# (c) dá tempo ao `/salvar` da leitura anterior (a IA leva até ~1 min; o `/salvar` vem depois).
SEM_LINHA_FOLGA = 300.0
# (b) A SAÍDA do segurado (Feca, 01/11/2026): a extensão não reenvia cru igual, então a aposta
# aberta cujo texto muda sem o cru mudar (cashout na tela) ou cujo cru nunca vem (histórico
# antigo) ficaria segurada para sempre, e sem linha ela nunca entraria na base. Segurada há
# `SEGURADA_EXTRAIRS` `/extrair` da mesma casa e dono (sem cru novo, ou não estaria segurada) ou
# há mais de `SEGURADA_HORAS`, ela vai à IA UMA vez, com motivo próprio (`ESGOTADA`). "Uma vez"
# é por cru: a ida fica gravada com a impressão do cru, e enquanto o cru for o mesmo a aposta não
# vai de novo nem volta a ser segurada (vale a linha da IA; sem linha, o (c) avisa). Sem isso o
# cashout na tela, que muda o texto a cada captura, iria à IA a cada 3 capturas.
SEGURADA_EXTRAIRS = 2
SEGURADA_HORAS = 24
# (b) "cru que não chegou" só segura a aposta se a casa MANDA cru para este dono: extensão velha
# (sem cru nenhum) segurando tudo deixaria a aposta sem leitor, e F5 não resolveria.
CRU_RECENTE_DIAS = 7

_VEREDITO = re.compile(r"Status:[^\n]*→\s*(HW|HL|W|L|V)\b")
_CLASSE = {"W": "+", "HW": "+", "L": "-", "HL": "-", "V": "0"}


def cru_final(f) -> bool:
    """A Ficha do cru guardado já está liquidada (qualquer status que não seja `aberta`)."""
    return bool(f) and f.get("status") not in (None, "", "aberta")


def contradiz(f, bloco) -> bool:
    """O veredito do texto (`Status: … → X`) contradiz o resultado do cru guardado? Só a CLASSE
    conta (ganhou, perdeu, devolveu): o texto escreve `W` também para meia vitória (`_resultadoB3`)
    e quem decide a meia é o cru. Sem veredito no texto, não contradiz."""
    m = _VEREDITO.search(bloco or "")
    if not m:
        return False
    try:
        res = _ficha.derivar(f)["resultado"]
    except Exception:  # noqa: BLE001 — cru que não se deriva não é prova de nada: espera
        return True
    return _CLASSE.get(res) != _CLASSE[m.group(1)]


_LINHA_NA_CASA = (f"EXISTS (SELECT 1 FROM bilhetes b WHERE b.dono = f.dono "
                  f"AND b.codigo_bilhete = f.codigo AND {_KB} = f.casa)")
# Excluída de propósito: pela lixeira de apostas (toda exclusão da tela, desde a Fase 7) ou junto
# com a conta inteira (`lixeira_contas.bilhetes`, um array das linhas; Fase 7, s438).
_NA_LIXEIRA = ("(EXISTS (SELECT 1 FROM lixeira_bilhetes l WHERE l.dono = f.dono "
               "AND l.bilhete->>'codigo_bilhete' = f.codigo) "
               "OR EXISTS (SELECT 1 FROM lixeira_contas lc WHERE lc.dono = f.dono "
               "AND lc.bilhetes @> jsonb_build_array(jsonb_build_object('codigo_bilhete', "
               "f.codigo))))")


async def _saida(conn, dono: str, casa_key: str, quer: dict) -> tuple[set, dict, set]:
    """Para os códigos que a D39 (b) seguraria (`quer` = {código: impressão do cru guardado, ou
    "" sem cru}): (segurar, {código: impressão} que ESGOTARAM e vão à IA uma vez, os que já
    foram à IA uma vez com ESTE cru e só saem do lote)."""
    if not quer:
        return set(), {}, set()
    rows = await conn.fetch(
        "SELECT f.codigo, f.impressao, f.motivo, (f.aviso = $4 AND (f.pendente_desde < "
        "NOW() - make_interval(hours => $5) OR (SELECT count(*) FROM virada_log v "
        "WHERE v.dono = f.dono AND v.casa = f.casa AND v.criado_em > f.pendente_desde) >= $6)) "
        "AS esgotada FROM ficha_virada f WHERE f.dono = $1 AND f.casa = $2 "
        "AND f.codigo = ANY($3::text[])", dono, casa_key, list(quer), AVISO_INCOMPLETA,
        SEGURADA_HORAS, SEGURADA_EXTRAIRS)
    antes = {r["codigo"]: r for r in rows}
    segurar, esgotou, ja_foi = set(), {}, set()
    for cod, imp in quer.items():
        r = antes.get(cod)
        if r is not None and r["motivo"] == ESGOTADA and (r["impressao"] or "") == imp:
            ja_foi.add(cod)
        elif r is not None and r["esgotada"]:
            esgotou[cod] = imp
        else:
            segurar.add(cod)
    if esgotou:
        logger.warning("virada: %s %s · %d aposta(s) com captura incompleta esgotada vão à IA "
                       "uma vez (sem cru novo há %d /extrair ou %d h)", dono, casa_key,
                       len(esgotou), SEGURADA_EXTRAIRS, SEGURADA_HORAS)
    return segurar, esgotou, ja_foi


async def _segurar(conn, dono: str, casa_key: str, codigos) -> None:
    """(b): a aposta fica fora da IA e pendente com o aviso de captura incompleta. Não mexe na
    última decisão (`estado`, `motivo`, `atualizado_em`): é ela que diz, depois, que a aposta
    foi decidida de novo (e o aviso sai)."""
    for cod in codigos:
        await conn.execute(
            """INSERT INTO ficha_virada (dono, casa, codigo, estado, motivo, aviso, pendente_desde)
               VALUES ($1, $2, $3, 'ia', 'captura incompleta', $4, NOW())
               ON CONFLICT (dono, casa, codigo) DO UPDATE SET aviso = EXCLUDED.aviso,
                 pendente_desde = COALESCE(ficha_virada.pendente_desde, NOW())""",
            dono, casa_key, cod, AVISO_INCOMPLETA)


async def _marcar_sem_linha(conn, dono: str, casa_key: str, ultimo) -> None:
    """(c): `ia` decidido num `/extrair` ANTERIOR (até o último, depois da D39 e há mais de
    `SEM_LINHA_FOLGA`) e sem linha na casa. Roda ANTES de decidir os códigos desta captura, que
    reescrevem o `atualizado_em` dos que voltam no texto. A aposta excluída pela lixeira sai na
    soltura do `_pendentes`, na mesma captura (um lugar só; a mesma conferência aqui seria
    redundante, e a mutação dela escapava, s438)."""
    if ultimo is None:
        return
    await conn.execute(
        "UPDATE ficha_virada f SET pendente_desde = NOW(), aviso = $3 WHERE f.dono = $1 "
        "AND f.casa = $2 AND f.estado = 'ia' AND f.pendente_desde IS NULL "
        "AND f.atualizado_em <= $4::timestamptz AND f.atualizado_em >= $5::timestamptz "
        "AND f.atualizado_em <= NOW() - make_interval(secs => $6) "
        f"AND NOT {_LINHA_NA_CASA}",
        dono, casa_key, AVISO_SEM_LINHA, ultimo, D39_DESDE, float(SEM_LINHA_FOLGA))


async def _pendentes(conn, dono: str, casa_key: str, casa: str, no_texto: list[str],
                     ultimo, janela: float) -> tuple[set[str], dict]:
    """A aposta que ninguém lê (s423; Feca: "nenhuma aposta é descartada em silêncio").

    A rota do cru decide TODO código que a casa mandou; o texto da mesma captura pode trazer
    menos (Jaao26, Shuffle, 14/10: 43 crus, 9 códigos no texto). O código que a Ficha recusou
    e que o texto não trouxe não chega à IA, e some sem erro. Aqui, em ordem:

      1. **tenta de novo** os pendentes `nao_lida` que o texto também não trouxe, pelo cru
         guardado mais recente (o dicionário pode ter aprendido o termo desde então). Os da D39
         (`captura_incompleta`, `sem_linha`) NÃO: esperam o cru novo ou só avisam;
      2. **marca** os novos `nao_lida`: `ia` decididos NESTA captura (depois do último
         `/extrair`, a régua do R32; sem nenhum, a `JANELA_CRU`), fora do texto e sem linha no
         banco. Os decididos antes do último `/extrair` NUNCA entram aqui: é o que deixa os 16 de
         14/10 do Jaao26 de fora (ele refez o histórico à mão por print; recuperá-los duplicaria);
      3. **solta** o que deixou de ser pendente, pela regra de cada aviso:
         `nao_lida` (ou sem aviso, de antes da D39): virou Ficha, veio no texto (a IA lê) ou tem
         linha; `captura_incompleta`: foi decidido de novo depois de segurado (cru novo chegou);
         `sem_linha`: tem linha, foi para a lixeira, ou a Ficha o gravou depois.

    "Tem linha no banco" é na MESMA casa (`casa_chave`: sem espaço, ponto e acento, em
    maiúsculas): código igual noutra casa não é esta aposta.

    Devolve (códigos que a Ficha resolveu agora, {"nao_lidas": n, "incompletas": n})."""
    ck = (casa_key or "").upper()
    resolvidos: set[str] = set()
    velhos = await conn.fetch(
        "SELECT DISTINCT ON (c.codigo) c.codigo, c.familia, c.parceiro, c.cru::text AS cru "
        "FROM ficha_virada f JOIN captura_crua c ON c.dono = f.dono AND c.casa = f.casa "
        "AND c.codigo = f.codigo WHERE f.dono = $1 AND f.casa = $2 AND f.estado = 'ia' "
        "AND f.pendente_desde IS NOT NULL AND coalesce(f.aviso, $4) = $4 "
        f"AND NOT (f.codigo = ANY($3::text[])) AND NOT {_LINHA_NA_CASA} "
        "ORDER BY c.codigo, c.id DESC", dono, ck, list(no_texto), AVISO_NAO_LIDA)
    por_conta: dict[str, dict] = {}
    for c in velhos:
        por_conta.setdefault(c["parceiro"] or "", {})[c["codigo"]] = _ficha.montar_ficha(
            c["familia"], json.loads(c["cru"]), ck)
    for conta, cands in por_conta.items():
        feitos, _ = await aplicar(conn, dono, ck, casa, conta, cands)
        resolvidos |= feitos
    await conn.execute(
        "UPDATE ficha_virada f SET pendente_desde = NOW(), aviso = $6 WHERE f.dono = $1 "
        "AND f.casa = $2 AND f.estado = 'ia' AND f.pendente_desde IS NULL "
        "AND NOT (f.codigo = ANY($3::text[])) "
        "AND (CASE WHEN $4::timestamptz IS NULL "
        "          THEN f.atualizado_em >= NOW() - make_interval(secs => $5) "
        "          ELSE f.atualizado_em > $4::timestamptz END) "
        f"AND NOT {_LINHA_NA_CASA}",
        dono, ck, list(no_texto), ultimo, float(janela), AVISO_NAO_LIDA)
    await conn.execute(
        "UPDATE ficha_virada f SET pendente_desde = NULL, aviso = NULL WHERE f.dono = $1 "
        "AND f.casa = $2 AND f.pendente_desde IS NOT NULL AND ("
        f" (coalesce(f.aviso, $4) = $4 AND (f.estado <> 'ia' OR f.codigo = ANY($3::text[]) "
        f"   OR {_LINHA_NA_CASA}))"
        " OR (f.aviso = $5 AND f.atualizado_em > f.pendente_desde)"
        f" OR (f.aviso = $6 AND ({_LINHA_NA_CASA} OR {_NA_LIXEIRA} "
        "   OR (f.estado = 'ficha' AND f.atualizado_em > f.pendente_desde))))",
        dono, ck, list(no_texto), AVISO_NAO_LIDA, AVISO_INCOMPLETA, AVISO_SEM_LINHA)
    n = await _contar_avisos(conn, dono, ck)
    if n["nao_lidas"]:
        logger.warning("virada: %s %s · %d aposta(s) não lida(s): a Ficha recusou e o texto "
                       "da captura não as trouxe", dono, ck, n["nao_lidas"])
    if n["incompletas"]:
        logger.warning("virada: %s %s · %d aposta(s) com captura incompleta (cru que não chegou "
                       "ou leitura que não virou linha)", dono, ck, n["incompletas"])
    return resolvidos, n


async def _contar_avisos(conn, dono: str, casa_key: str) -> dict:
    r = await conn.fetchrow(
        "SELECT count(*) FILTER (WHERE coalesce(aviso, $3) = $3) AS nao_lidas, "
        "count(*) FILTER (WHERE aviso IN ($4, $5)) AS incompletas FROM ficha_virada "
        "WHERE dono = $1 AND casa = $2 AND pendente_desde IS NOT NULL",
        dono, (casa_key or "").upper(), AVISO_NAO_LIDA, AVISO_INCOMPLETA, AVISO_SEM_LINHA)
    return {"nao_lidas": int(r["nao_lidas"] or 0), "incompletas": int(r["incompletas"] or 0)}


async def avisos(dono: str, casa_key: str) -> dict:
    """Quantas apostas desta casa estão pendentes, por aviso, para a tela: `nao_lidas` (s423) e
    `incompletas` (D39: captura incompleta ou leitura que não virou linha)."""
    if not virada(casa_key):
        return {"nao_lidas": 0, "incompletas": 0}
    pool = await _pool_conn()
    async with pool.acquire() as conn:
        return await _contar_avisos(conn, dono, casa_key)


async def resolver_no_extrair(dono: str, casa_key: str, casa: str, parceiro: str,
                              codigos: list[str], inalterados=frozenset(),
                              no_texto: list[str] | None = None, info: dict | None = None,
                              blocos: dict | None = None
                              ) -> tuple[set[str], float, dict, set[str]]:
    """`/extrair` da casa virada: espera o cru, monta a Ficha do cru GUARDADO mais recente de
    cada código e devolve (os que a Ficha resolveu, que saem do lote da IA; segundos de espera;
    {código: motivo} dos que ficam com a IA; os SEGURADOS, que também saem do lote e ficam
    pendentes, D39 b). Nunca levanta.

    `inalterados` = códigos cujo bloco de texto é igual ao da última leitura. Para os OUTROS, o
    cru tem de ser desta captura (N3) ou, desde a D39, estar LIQUIDADO e não contradizer o
    veredito do texto (`blocos` = {código: bloco de texto}). Cru velho ABERTO com texto mudado,
    ou cru que não chegou, segura a aposta. Desta captura = chegou depois do último `/extrair`
    desta casa e dono (`virada_log`; R32), ou, sem nenhum, na `JANELA_CRU`."""
    if not virada(casa_key):
        return set(), 0.0, {}, set()
    espera = 0.0
    resolvidos, fica, segurados = set(), {}, set()
    ck = casa_key.upper()
    try:
        espera = await esperar_cru(dono, casa_key)
        pool = await _pool_conn()
        async with pool.acquire() as conn:
            ultimo = await ultimo_extrair(conn, dono, casa_key)
            try:                                       # (c), antes de decidir esta captura
                await _marcar_sem_linha(conn, dono, ck, ultimo)
            except Exception:  # noqa: BLE001 — só deixa de avisar
                logger.exception("virada: (c) sem linha de %s/%s não conferido", dono, ck)
            if codigos:
                crus = await conn.fetch(
                    "SELECT DISTINCT ON (codigo) codigo, familia, cru::text AS cru, "
                    "(CASE WHEN $5::timestamptz IS NULL "
                    "      THEN recebido_em >= NOW() - make_interval(secs => $4) "
                    "      ELSE recebido_em > $5::timestamptz END) AS fresco FROM captura_crua "
                    "WHERE dono = $1 AND casa = $2 AND codigo = ANY($3::text[]) "
                    "ORDER BY codigo, id DESC", dono, ck, list(codigos),
                    float(JANELA_CRU + espera), ultimo)
                candidatas, velhos, quer = {}, {}, {}
                for c in crus:
                    cod = c["codigo"]
                    fm = _ficha.montar_ficha(c["familia"], json.loads(c["cru"]), ck)
                    if not c["fresco"] and cod not in inalterados:
                        f, mot = fm
                        if f is None or mot:           # Ficha recusa: só o texto lê
                            fica[cod] = "texto mudou sem cru novo"
                            velhos[cod] = ("", "ia", "texto mudou sem cru novo")
                        elif cru_final(f) and not contradiz(f, (blocos or {}).get(cod)):
                            candidatas[cod] = fm       # (a) cru liquidado: Ficha, sem IA
                        else:
                            quer[cod] = f.get("impressao") or ""   # (b) cru aberto, ou desmentido
                        continue
                    candidatas[cod] = fm
                faltam = [cod for cod in codigos if cod not in candidatas and cod not in fica
                          and cod not in quer]
                if faltam:
                    manda_cru = await conn.fetchval(
                        "SELECT EXISTS (SELECT 1 FROM captura_crua WHERE dono = $1 AND casa = $2 "
                        "AND recebido_em >= NOW() - make_interval(days => $3))",
                        dono, ck, CRU_RECENTE_DIAS)
                    for cod in faltam:
                        if manda_cru:
                            quer[cod] = ""             # (b) cru que não chegou
                        else:
                            fica[cod] = "cru não chegou"   # extensão sem cru: a IA lê
                segurar, esgotou, ja_foi = await _saida(conn, dono, ck, quer)
                for cod, imp in esgotou.items():       # a saída: à IA uma vez
                    fica[cod] = ESGOTADA
                    velhos[cod] = (imp, "ia", ESGOTADA)
                segurados = segurar | ja_foi           # os dois saem do lote da IA
                await _gravar_estados(conn, dono, ck, velhos)
                if segurar:
                    await _segurar(conn, dono, ck, segurar)
                resolvidos, fica_ficha = await aplicar(conn, dono, casa_key, casa, parceiro,
                                                       candidatas)
                fica.update(fica_ficha)
            # Depois de decidir os do texto: a aposta que o texto não trouxe (s423) e a soltura
            # dos avisos. Falha aqui não tira nada do lote da IA: só deixa de avisar.
            try:
                _, n = await _pendentes(conn, dono, casa_key, casa,
                                        list(no_texto if no_texto is not None else codigos),
                                        ultimo, JANELA_CRU + espera)
                if info is not None:
                    info.update(n)
            except Exception:  # noqa: BLE001
                logger.exception("virada: pendentes de %s/%s não conferidos", dono, casa_key)
        return resolvidos, espera, fica, segurados
    except Exception:  # noqa: BLE001 — na dúvida, a IA lê tudo, como antes da virada
        logger.exception("virada: falha no /extrair de %s/%s; o lote vai inteiro à IA",
                         dono, casa_key)
        return set(), espera, {}, set()


async def registrar(dono: str, casa_key: str, capturadas: int, ja_no_banco: int,
                    pela_ficha: int, inalterados: int, para_ia: int, espera: float = 0.0,
                    motivos: dict | None = None, segurados: int = 0) -> None:
    """Uma linha por `/extrair` da casa virada: a métrica antes × depois
    (`medicoes/medir_virada_custo.py`), com o motivo de cada código que foi para a IA
    (`motivos` = {motivo: n}, as chaves de `MOTIVOS`) e, desde a D39, quantos ficaram fora da IA
    esperando cru (`captura_incompleta`). Falha aqui não importa para a captura."""
    m = [(motivos or {}).get(mot, 0) for mot in MOTIVOS]
    try:
        pool = await _pool_conn()
        async with pool.acquire() as conn:
            await conn.execute(
                f"""INSERT INTO virada_log (dono, casa, capturadas, ja_no_banco, pela_ficha,
                                            inalterados, para_ia, espera_s,
                                            {", ".join(MOTIVOS.values())}, captura_incompleta)
                    VALUES ({", ".join(f"${i}" for i in range(1, 10 + len(MOTIVOS)))})""",
                dono, (casa_key or "").upper(), capturadas, ja_no_banco, pela_ficha,
                inalterados, para_ia, round(espera, 2), *m, segurados)
    except Exception:  # noqa: BLE001
        logger.exception("virada: não registrou a métrica de %s/%s", dono, casa_key)


# ── vigia da virada (s415, RC34/R29) ─────────────────────────────────────────────────────
# Uma amostra das apostas que a Ficha gravou também é lida pela IA, numa chamada À PARTE e em
# segundo plano, só para comparar o dinheiro: stake, resultado e odd (P/L, na liquidada). A
# IA não grava nada: a resposta dela vai só para `vigia_ficha`. Desligado com
# `VIGIA_POR_DIA` vazio ou 0; ligado, é o máximo de apostas numa chamada. D28 (Feca,
# 14/10/2026): UMA chamada por casa virada por dia (dia de Brasília), de qualquer dono, na
# primeira captura do dia com aposta da Ficha ainda não conferida naquele resultado (a aberta
# conferida volta a valer quando liquida). Ligado em 14/10/2026 com 3, por 2 semanas: rever
# em 27/10 (BACKLOG). A chamada à parte e não no lote da
# IA porque o lote volta para a extensão, que o grava pelo `/salvar`: a IA escreveria por
# cima da Ficha.

def vigia_por_dia() -> int:
    try:
        return max(0, int(os.environ.get("VIGIA_POR_DIA", "") or 0))
    except ValueError:
        return 0


async def vigia_vagas(conn, casa_key: str) -> int:
    """Quantas apostas a chamada de hoje pode levar: `VIGIA_POR_DIA`, ou 0 se esta casa já
    teve a sua chamada hoje (dia de Brasília), de QUALQUER dono (D28)."""
    ja = await conn.fetchval(
        "SELECT EXISTS (SELECT 1 FROM vigia_ficha WHERE casa = $1 AND "
        "(criado_em AT TIME ZONE 'America/Sao_Paulo')::date = "
        "(NOW() AT TIME ZONE 'America/Sao_Paulo')::date)", (casa_key or "").upper())
    return 0 if ja else vigia_por_dia()


_vigia_reservas: set = set()


def vigia_reservar(casa_key: str, hoje: str) -> bool:
    """Reserva a chamada do dia desta casa NESTE processo: duas capturas ao mesmo tempo (Feca e
    Gabriel) passariam as duas pelo `vigia_vagas` antes de a primeira gravar. Supõe um
    processo só, como a espera pelo cru."""
    k = ((casa_key or "").upper(), hoje)
    if k in _vigia_reservas:
        return False
    _vigia_reservas.add(k)
    return True


def vigia_soltar(casa_key: str, hoje: str) -> None:
    """Devolve a reserva quando a chamada não aconteceu (nada a conferir, ou falhou)."""
    _vigia_reservas.discard(((casa_key or "").upper(), hoje))


async def vigia_candidatos(conn, dono: str, casa_key: str, codigos: list[str],
                           vagas: int) -> list[str]:
    """Até `vagas` apostas desta captura que a FICHA gravou (`origem = 'ficha'`) e que o vigia
    ainda não conferiu NESTE resultado (a aberta conferida volta a ser candidata quando
    liquida), a mais recente primeiro. A liquidada pela rota do cru já chega ao `/extrair`
    como resolvida: por isso a escolha é pelo banco, não pelo que a Ficha resolveu agora."""
    if vagas <= 0 or not codigos:
        return []
    rows = await conn.fetch(
        "SELECT b.codigo_bilhete FROM bilhetes b WHERE b.dono = $1 AND b.origem = 'ficha' "
        f"AND {_KB} = $2 AND b.codigo_bilhete = ANY($3::text[]) "
        "AND NOT EXISTS (SELECT 1 FROM vigia_ficha v WHERE v.dono = b.dono AND v.casa = $2 "
        "  AND v.codigo = b.codigo_bilhete "
        "  AND coalesce(v.ficha->>'resultado', '') = coalesce(b.resultado, '')) "
        "ORDER BY b.atualizado_em DESC NULLS LAST, b.id DESC LIMIT $4",
        dono, (casa_key or "").upper(), list(codigos), vagas)
    return [r["codigo_bilhete"] for r in rows]


def _f(v) -> float | None:
    """Número da planilha (`10,50`, `1.85`, `1.234,56`)."""
    s = _limpo(v)
    if not s:
        return None
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _pl(stake, odd, res) -> float | None:
    """O P/L pelas fórmulas do `calcular_pl` (None na aberta)."""
    if stake is None or not res:
        return None
    if res == "L":
        return -stake
    if res == "V":
        return 0.0
    if odd is None:
        return None
    if res == "W":
        return stake * (odd - 1)
    if res == "HW":
        return stake / 2 * (odd - 1)
    if res == "HL":
        return -stake / 2
    return None


def vigia_comparar(ficha: dict, ia: dict | None) -> list[str]:
    """Os campos de DINHEIRO em que a IA diverge da linha que a Ficha gravou. `ficha` e `ia` =
    {stake, odd, resultado, moeda} NA MOEDA DA CASA (s417): a da Ficha é a `stake_orig` com a
    `moeda` gravada; a da IA é o que ela leu, na moeda que o cru disse (ou a da conta). Moeda
    que não é a mesma (`cambio.mesma_moeda`; USD e USDT são) é divergência própria: foi assim
    que a stake em real gravada como USDT apareceu. Sem linha da IA para o código: `["linha"]`.
    A odd só conta onde muda o dinheiro: na liquidada compara o P/L (a IA escreve a odd da W
    como retorno ÷ stake, e as duas pagam o mesmo); na aberta, a própria odd."""
    if not ia:
        return ["linha"]
    out = []
    if not _cambio.mesma_moeda(ficha.get("moeda"), ia.get("moeda")):
        out.append("moeda")
    sf, si = _f(ficha.get("stake")), _f(ia.get("stake"))
    if sf is None or si is None or abs(sf - si) > 0.005:
        out.append("stake")
    rf, ri = _limpo(ficha.get("resultado")).upper(), _limpo(ia.get("resultado")).upper()
    if rf != ri:
        out.append("resultado")
    of, oi = _f(ficha.get("odd")), _f(ia.get("odd"))
    if rf and rf == ri:
        pf, pi = _pl(sf, of, rf), _pl(si, oi, ri)
        if pf is None or pi is None or abs(pf - pi) > 0.01:
            out.append("odd")
    elif not rf and not ri and (of is None or oi is None or abs(of - oi) > 0.005):
        out.append("odd")
    return out


def _linhas_por_codigo(tsv: str) -> dict:
    out = {}
    for linha in (tsv or "").splitlines():
        col = linha.split("\t")
        if len(col) >= 11 and _limpo(col[10]):
            out[_limpo(col[10])] = {"stake": col[7], "odd": col[8], "resultado": col[9],
                                    "descricao": col[6]}
    return out


def _na_moeda_da_casa(b) -> dict:
    """A linha gravada pela Ficha como a casa a mostrou: a stake ORIGINAL e a moeda dela.
    Linha sem origem (conta em real) já está na moeda da casa."""
    f = {k: b[k] for k in ("stake", "odd", "resultado", "descricao")}
    if b["moeda"] and b["stake_orig"] is not None:
        f["stake"] = f"{float(b['stake_orig']):.2f}".replace(".", ",")
        f["moeda"] = str(b["moeda"]).upper()
    else:
        f["moeda"] = _cambio.BRL
    return f


async def vigia_registrar(conn, dono: str, casa_key: str, codigos: list[str], tsv: str,
                          parceiro: str = "") -> int:
    """Compara a resposta da IA (`tsv`, já pelos fiscais determinísticos) com a linha que a
    Ficha gravou e grava uma linha por código em `vigia_ficha`. Devolve as divergentes.

    As duas pontas vão na moeda da CASA (s417): a IA lê a stake do bloco, antes da conversão
    do `/salvar`, e a Ficha gravou em R$; comparar R$ com USDT dava falso alarme em toda
    conta em dólar. A moeda da IA é a que o cru disse para o código, senão a da conta."""
    ia = _linhas_por_codigo(tsv)
    conta = await conn.fetchval(
        f"SELECT moeda FROM parceiros WHERE dono = $1 AND {_K} = $2 "
        "AND nome = $3 LIMIT 1", dono, (casa_key or "").upper(), parceiro or "") or _cambio.BRL
    do_cru = await _ficha.moedas_do_cru_conn(conn, dono, casa_key, parceiro, list(codigos))
    for cod, linha in ia.items():
        linha["moeda"] = _cambio.moeda_do_cru(conta, do_cru.get(cod)) or conta
    div = 0
    for cod in codigos:
        b = await conn.fetchrow(
            "SELECT stake, odd, resultado, descricao, moeda, stake_orig FROM bilhetes "
            f"WHERE dono = $1 AND codigo_bilhete = $2 AND {_K} = $3 "
            "ORDER BY id DESC LIMIT 1", dono, cod, (casa_key or "").upper())
        if not b:
            continue
        f = _na_moeda_da_casa(b)
        campos = vigia_comparar(f, ia.get(cod))
        div += bool(campos)
        await conn.execute(
            "INSERT INTO vigia_ficha (dono, casa, codigo, ficha, ia, divergente, campos) "
            "VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, $6, $7::text[])",
            dono, (casa_key or "").upper(), cod, json.dumps(f, ensure_ascii=False),
            json.dumps(ia.get(cod), ensure_ascii=False) if cod in ia else None,
            bool(campos), campos)
        if campos:
            logger.warning("vigia: %s %s %s · a IA diverge da Ficha em %s: Ficha %s × IA %s",
                           dono, casa_key, cod, campos, f, ia.get(cod))
    return div


# ── termo novo foi para a IA: a semente roda logo depois dela (s412) ─────────────────────
_termo_novo: set = set()


def marcar_termo_novo(dono: str, casa: str) -> None:
    _termo_novo.add((dono, chave_da_casa(casa)))


def tomar_termo_novo(dono: str, casa: str) -> bool:
    """True uma vez só, depois de um `/extrair` da casa virada que mandou termo (ou mercado de
    descrição) fora do dicionário para a IA. Quem chama roda a semente depois de gravar a
    decisão da IA."""
    k = (dono, chave_da_casa(casa))
    if k in _termo_novo:
        _termo_novo.discard(k)
        return True
    return False
