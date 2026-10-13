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
tira o código da fila da IA se o cru usado é DESTA captura (chegou na janela `JANELA_CRU` antes
do extrair) ou se o bloco de texto não mudou desde a última leitura (a barreira de hoje). Texto
mudado sem cru novo (a extensão recarregada sem F5 na aba da casa manda o texto e não o cru) vai
para a IA, e o `virada_log` o conta à parte (`sem_cru_novo`).

**Esporte e categoria passam pelo Master antes de gravar** (`app/taxonomia.py`; R27): valor fora
dele vai para a IA (`fora do Master`). O dicionário vale para todos os usuários da casa.

**A descrição sai do dicionário de descrição** (s413, `app/descricao_ficha.py`; regra do Feca:
chamada extra à IA só para a descrição, nunca): o mercado aprendido monta a descrição como a IA
monta. Mercado sem par vai para a IA (`descrição fora do dicionário`), e a semente o aprende logo
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
JANELA_CRU = 30.0       # cru guardado até isto antes do extrair (+ a espera) = desta captura (N3)
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
    """Nome de exibição → chave (`DEX Sport` → `DEXSPORT`), a mesma régua da sessão."""
    return re.sub(r"\s+", "", casa or "").upper()


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
    """A descrição da Ficha pelo dicionário de descrição (`descricao_ficha.montar`): perna por
    perna, unidas por ` // `, com a forma fixada pelo Feca (`dicionario.descricao_perna`) na
    frente. None = algum mercado sem par: a aposta vai para a IA."""
    return _desc.montar(f, termos, _dic.descricao_perna)[0]


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
}


def no_master(esporte: str | None, categoria: str | None) -> bool:
    """Esporte e categoria são valores do Master (`app/taxonomia.py`, que LÊ os MASTERs)."""
    import taxonomia
    return esporte in taxonomia.esportes_canonicos() and \
        categoria in taxonomia.categorias_canonicas()


async def _liquidados(conn, dono: str, codigos: list[str]) -> set[str]:
    """Códigos já LIQUIDADOS no banco, de qualquer origem: a Ficha não os reescreve (D10)."""
    rows = await conn.fetch(
        "SELECT DISTINCT codigo_bilhete FROM bilhetes WHERE dono = $1 "
        "AND codigo_bilhete = ANY($2::text[]) AND extraction_state = 'resolvida'",
        dono, codigos)
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
    liquidados = await _liquidados(conn, dono, cods)
    termos = await _dic.carregar(conn, casa_key)
    estado = {r["codigo"]: (r["impressao"], r["estado"]) for r in await conn.fetch(
        "SELECT codigo, impressao, estado FROM ficha_virada WHERE dono = $1 AND casa = $2 "
        "AND codigo = ANY($3::text[])", dono, casa_key, cods)}
    resolvidos, fica, novo_estado, gravar = set(), {}, {}, []

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
        desc = descricao(f, termos)
        if not desc:
            ia(cod, "descrição fora do dicionário")
            continue
        imp = f.get("impressao") or ""
        if estado.get(cod) == (imp, "ficha"):
            resolvidos.add(cod)            # cru igual, já gravado pela Ficha: só sai do lote
            continue
        gravar.append((f, esporte, categoria, desc))
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


async def resolver_no_extrair(dono: str, casa_key: str, casa: str, parceiro: str,
                              codigos: list[str], inalterados=frozenset()
                              ) -> tuple[set[str], float, dict]:
    """`/extrair` da casa virada: espera o cru, monta a Ficha do cru GUARDADO mais recente de
    cada código e devolve (os que a Ficha resolveu, que saem do lote da IA; segundos de
    espera; {código: motivo} dos que ficam com a IA). Nunca levanta.

    `inalterados` = códigos cujo bloco de texto é igual ao da última leitura. Para os OUTROS,
    só o cru desta captura vale (N3): cru anterior com texto mudado é a liquidação que o cru
    velho esconderia, e o código vai para a IA."""
    if not virada(casa_key) or not codigos:
        return set(), 0.0, {}
    espera = 0.0
    try:
        espera = await esperar_cru(dono, casa_key)
        pool = await _pool_conn()
        async with pool.acquire() as conn:
            crus = await conn.fetch(
                "SELECT DISTINCT ON (codigo) codigo, familia, cru::text AS cru, "
                "(recebido_em >= NOW() - make_interval(secs => $4)) AS fresco FROM captura_crua "
                "WHERE dono = $1 AND casa = $2 AND codigo = ANY($3::text[]) "
                "ORDER BY codigo, id DESC", dono, casa_key.upper(), list(codigos),
                float(JANELA_CRU + espera))
            candidatas, fica, velhos = {}, {}, {}
            for c in crus:
                if not c["fresco"] and c["codigo"] not in inalterados:
                    fica[c["codigo"]] = "texto mudou sem cru novo"
                    velhos[c["codigo"]] = ("", "ia", "texto mudou sem cru novo")
                    continue
                candidatas[c["codigo"]] = _ficha.montar_ficha(c["familia"], json.loads(c["cru"]),
                                                              casa_key.upper())
            for cod in codigos:
                if cod not in candidatas and cod not in fica:
                    fica[cod] = "cru não chegou"
            await _gravar_estados(conn, dono, casa_key.upper(), velhos)
            resolvidos, fica_ficha = await aplicar(conn, dono, casa_key, casa, parceiro,
                                                   candidatas)
        fica.update(fica_ficha)
        return resolvidos, espera, fica
    except Exception:  # noqa: BLE001 — na dúvida, a IA lê tudo, como antes da virada
        logger.exception("virada: falha no /extrair de %s/%s; o lote vai inteiro à IA",
                         dono, casa_key)
        return set(), espera, {}


async def registrar(dono: str, casa_key: str, capturadas: int, ja_no_banco: int,
                    pela_ficha: int, inalterados: int, para_ia: int, espera: float = 0.0,
                    motivos: dict | None = None) -> None:
    """Uma linha por `/extrair` da casa virada: a métrica antes × depois
    (`medicoes/medir_virada_custo.py`), com o motivo de cada código que foi para a IA
    (`motivos` = {motivo: n}, as chaves de `MOTIVOS`). Falha aqui não importa para a captura."""
    m = [(motivos or {}).get(mot, 0) for mot in MOTIVOS]
    try:
        pool = await _pool_conn()
        async with pool.acquire() as conn:
            await conn.execute(
                f"""INSERT INTO virada_log (dono, casa, capturadas, ja_no_banco, pela_ficha,
                                            inalterados, para_ia, espera_s,
                                            {", ".join(MOTIVOS.values())})
                    VALUES ({", ".join(f"${i}" for i in range(1, 9 + len(MOTIVOS)))})""",
                dono, (casa_key or "").upper(), capturadas, ja_no_banco, pela_ficha,
                inalterados, para_ia, round(espera, 2), *m)
    except Exception:  # noqa: BLE001
        logger.exception("virada: não registrou a métrica de %s/%s", dono, casa_key)


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
