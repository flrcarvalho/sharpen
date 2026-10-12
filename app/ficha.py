"""Ficha Sharpen, em MODO SOMBRA (Projeto Ficha Sharpen, D1; s409).

A extensão manda aqui o JSON CRU de cada bilhete, como a casa devolveu, SEPARADO do
`/captura/enviar` e sem esperar resposta. O servidor filtra o cru (`app/cru.py`), guarda em
`captura_crua` para TODAS as casas e, onde a chave liga a casa, monta a Ficha com o adaptador
da família (`app/adaptadores/`) e grava em `ficha_sombra`. O caminho de hoje continua mandando
no banco: nada aqui toca em `bilhetes`, EXCETO na casa VIRADA (`FICHA_CASAS_VIRADAS`, vazia
até o "pode" do Feca), onde a Ficha aceita vai à planilha pelo `/salvar` (`app/virada.py`).
A régua compara depois.

Decisões do Feca (11/10) que moram aqui:

  • **O adaptador mora no servidor**, não na extensão: casa nova migra sem atualizar o
    SharpenUp, e adaptador corrigido roda de novo sobre o cru já guardado.
  • **Ficha recusada é gravada com o motivo, nunca descartada.** Descartada, ela viraria
    "faltou" na régua, sem causa. Vale para recusa do adaptador e da validação.
  • **Casa e conta saem da SESSÃO de captura**, nunca do corpo. O token aponta para o
    pareamento feito no dashboard (dono logado + casa + conta escolhidas ali).
  • **Cru vindo do site de OUTRA casa é 409, resposta final:** não grava, conta no log, e a
    extensão marca como tratado e não reenvia.
  • **`FICHA_SOMBRA_CASAS` liga o ADAPTADOR casa por casa** (vazia = só guarda o cru).
    `CRU_CAPTURA_DESLIGADA=1` desliga a rota inteira, sem deploy de código, e ela responde
    **503**: a extensão só marca o cru como enviado depois do 200, então com 503 ela guarda e
    reenvia quando a rota voltar. Com 200 o cru desligado se perderia em silêncio.
  • **Erro QUALQUER do adaptador vira Ficha recusada** (`erro do adaptador: …`), nunca 500.
    O cru já foi gravado antes da Ficha: um 500 ali faz o reenvio cair em "cru igual" e a
    Ficha daquele cru nunca é montada.

Token inválido NÃO grava: sem sessão não há dono, e gravar requisição anônima abriria o banco
para lixo. A rota responde 401 e a extensão reenvia depois do novo pareamento.

`derivar(ficha)` monta stake, odd, resultado e data pelas regras da Ficha §3, SEM IA. Roda na
hora do relatório, não na gravação: mudar uma regra não obriga a regravar nada.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation, localcontext
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Body, HTTPException

import captura as _captura
import cru as _cru
from tradutor import _PRECISAO_ODD, _PRECISAO_PRODUTO, _odd_br

logger = logging.getLogger("scanner")
router = APIRouter()

VERSAO = "ficha/1"
# status da Ficha → código da planilha. `cashout` decide pelo dinheiro (W ou V).
_RESULTADO = {"aberta": "", "ganha": "W", "perdida": "L", "anulada": "V",
              "meio_ganha": "HW", "meio_perdida": "HL", "cashout": None}
_TIPOS = {"simples", "multipla", "sistema"}
_NUMERO = re.compile(r"^\d+(?:\.\d+)?$")       # Ficha §2: texto com PONTO decimal, sem sinal
_BRT = ZoneInfo("America/Sao_Paulo")
_CENTAVO = Decimal("0.005")                     # "fecha no centavo": arredonda para o mesmo


def casas_ligadas() -> frozenset:
    brutas = os.environ.get("FICHA_SOMBRA_CASAS", "")
    return frozenset(c.strip().upper() for c in brutas.split(",") if c.strip())


def ligada(casa_key: str) -> bool:
    casas = casas_ligadas()
    return "*" in casas or (casa_key or "").upper() in casas


# ── leitura dos campos ────────────────────────────────────────────────────────────────

def _dec(v) -> Decimal | None:
    """Número da Ficha. Só TEXTO com ponto decimal: float perde centavo, e vírgula seria o
    formato da tela, não o da Ficha. Qualquer outra coisa = None (o validador acusa)."""
    if not isinstance(v, str) or not _NUMERO.match(v.strip()):
        return None
    try:
        return Decimal(v.strip())
    except InvalidOperation:
        return None


def _instante(v) -> datetime | None:
    """ISO 8601 COM fuso. Sem fuso não é instante: é um palpite de fuso."""
    if not isinstance(v, str) or not v.strip():
        return None
    try:
        d = datetime.fromisoformat(v.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return d if d.tzinfo is not None else None


def validar(f, casa_key: str) -> list[str]:
    """Motivos de recusa. Lista vazia = a Ficha é aceita."""
    if not isinstance(f, dict):
        return ["a ficha não é um objeto"]
    m: list[str] = []
    if f.get("versao") != VERSAO:
        m.append(f"versao deve ser {VERSAO!r}")
    if (f.get("casa") or "").strip().upper() != (casa_key or "").upper():
        m.append(f"casa {f.get('casa')!r} não é a da sessão ({casa_key})")
    if not (isinstance(f.get("codigo"), str) and f["codigo"].strip()):
        m.append("codigo ausente")
    if _instante(f.get("colocada_em")) is None:
        m.append("colocada_em ausente ou sem fuso")
    if f.get("liquidada_em") not in (None, "") and _instante(f.get("liquidada_em")) is None:
        m.append("liquidada_em sem fuso")
    status = f.get("status")
    if status not in _RESULTADO:
        m.append(f"status desconhecido: {status!r}")
    if not isinstance(f.get("status_casa"), str):
        m.append("status_casa ausente")
    # Moeda ausente NÃO recusa: decisão do Feca (D0, pergunta 5), vale a da conta.
    stake = _dec(f.get("stake"))
    if stake is None or stake <= 0:
        m.append("stake ausente, zero ou fora do formato (texto com ponto)")
    odd = _dec(f.get("odd"))
    if odd is None or odd <= 0:
        m.append("odd ausente, zero ou fora do formato (texto com ponto)")
    if not isinstance(f.get("odd_calculada"), bool):
        m.append("odd_calculada deve ser booleano")
    if f.get("retorno") not in (None, "") and _dec(f.get("retorno")) is None:
        m.append("retorno fora do formato (texto com ponto)")
    if status in ("ganha", "meio_ganha", "cashout") and _dec(f.get("retorno")) is None:
        m.append(f"{status} sem retorno")
    if f.get("tipo") not in _TIPOS:
        m.append(f"tipo desconhecido: {f.get('tipo')!r}")
    pernas = f.get("pernas")
    if not isinstance(pernas, list) or not pernas:
        m.append("pernas ausentes")
    else:
        for i, p in enumerate(pernas, 1):
            if not isinstance(p, dict):
                m.append(f"perna {i} não é um objeto")
                continue
            if not (isinstance(p.get("evento"), str) and p["evento"].strip()):
                m.append(f"perna {i}: evento ausente")
            if not any(isinstance(p.get(k), str) and p[k].strip()
                       for k in ("mercado_casa", "selecao_casa")):
                m.append(f"perna {i}: sem mercado nem seleção")
            if _dec(p.get("odd")) is None:
                m.append(f"perna {i}: odd ausente ou fora do formato")
            if p.get("inicio") not in (None, "") and _instante(p.get("inicio")) is None:
                m.append(f"perna {i}: inicio sem fuso")
            if p.get("status_perna") not in (None, "") and p.get("status_perna") not in _RESULTADO:
                m.append(f"perna {i}: status_perna desconhecido")
    if not (isinstance(f.get("impressao"), str) and f["impressao"].strip()):
        m.append("impressao ausente")
    if not (isinstance(f.get("origem"), str) and f["origem"].strip()):
        m.append("origem ausente")
    return m


# ── derivação (Ficha §3), sem IA ─────────────────────────────────────────────────────

def _produto(pernas: list) -> Decimal | None:
    odds = [_dec(p.get("odd")) for p in pernas]
    if not odds or any(o is None or o <= 1 for o in odds):
        return None
    with localcontext() as ctx:
        ctx.prec = _PRECISAO_PRODUTO
        prod = Decimal(1)
        for o in odds:
            prod *= o
    with localcontext() as ctx:
        ctx.prec = _PRECISAO_ODD
        return +prod


def _paga(resultado: str, stake: Decimal, odd: Decimal) -> Decimal:
    return stake * odd if resultado == "W" else (stake / 2) * odd + stake / 2


def _razao(retorno: Decimal, stake: Decimal) -> Decimal:
    """Retorno ÷ Stake em 10 casas, a régua do `repository._veredito_do_retorno`: a dízima
    do retorno arredondado ao centavo não ganha 28 casas na planilha."""
    return (retorno / stake).quantize(Decimal("1e-10"))


def _odd(f: dict, resultado: str, stake: Decimal, retorno: Decimal | None) -> tuple[Decimal | None, str]:
    """A odd pela regra aprovada (Feca, 11/10). Devolve (odd, de onde veio)."""
    casa = _dec(f.get("odd"))
    if f.get("status") == "cashout":
        if resultado == "V":
            return casa, "cashout = stake: odd da casa"
        return _razao(retorno, stake), "cashout: retorno ÷ stake"
    if resultado in ("", "L", "V", "HL"):
        return casa, "odd da casa" + (" (calculada pelo adaptador)" if f.get("odd_calculada") else "")
    if f.get("tipo") == "sistema":
        # Sistema ganho paga só as linhas que ganharam: a odd média sobre a stake inteira
        # lançaria como se todas tivessem ganho (s409: +650 USDT em 4 bilhetes). W com
        # retorno é Retorno ÷ Stake (MASTER_RESULTADO §7.1); HW fica com a odd da casa.
        if resultado == "W":
            return _razao(retorno, stake), "sistema ganho: retorno ÷ stake (MASTER_RESULTADO §7.1)"
        return casa, "sistema: odd da casa (régua própria, MASTER_RESULTADO §7.3)"
    calc = None if f.get("odd_calculada") else _produto(f.get("pernas") or [])

    def fecha(o):
        return o is not None and abs(_paga(resultado, stake, o) - retorno) <= _CENTAVO

    if fecha(casa):
        return casa, "fecha o retorno: odd da casa"
    if fecha(calc):
        return calc, "fecha o retorno: produto das pernas"
    if resultado == "W":
        return _razao(retorno, stake), "nenhuma fecha: retorno ÷ stake"
    return casa, "meia vitória que nenhuma odd fecha: odd da casa (conferir)"


def _data(f: dict, resultado: str) -> tuple[str, str]:
    """Data da planilha (Ficha §3 = MASTER_OUTPUT §4 e §4.0.1), no fuso de Brasília."""
    pernas = [p for p in (f.get("pernas") or []) if isinstance(p, dict)]
    inicios = [_instante(p.get("inicio")) for p in pernas]
    inicios = [i for i in inicios if i is not None]
    if not inicios:
        d, fonte = _instante(f.get("colocada_em")), "sem início: colocação"
    else:
        d, fonte = max(inicios), ("início da perna" if len(pernas) == 1 else "perna mais recente")
        if resultado == "L" and f.get("tipo") != "sistema":
            perdidas = [_instante(p.get("inicio")) for p in pernas
                        if p.get("status_perna") == "perdida" and _instante(p.get("inicio"))]
            if perdidas and min(perdidas) < d:
                d, fonte = min(perdidas), "perna perdida mais cedo"
    return d.astimezone(_BRT).strftime("%d/%m/%Y"), fonte


def derivar(f: dict) -> dict:
    """Stake, odd, resultado e data da planilha, a partir de uma Ficha ACEITA."""
    if f.get("status") not in _RESULTADO:
        # Só Ficha ACEITA chega aqui; status desconhecido viraria cashout em silêncio.
        raise ValueError(f"status desconhecido: {f.get('status')!r}")
    stake = _dec(f.get("stake"))
    retorno = _dec(f.get("retorno"))
    resultado = _RESULTADO[f["status"]]
    if resultado is None:                      # cashout: o dinheiro decide
        resultado = "V" if retorno is not None and abs(retorno - stake) <= _CENTAVO else "W"
    odd, fonte_odd = _odd(f, resultado, stake, retorno)
    data, fonte_data = _data(f, resultado)
    return {"stake": _odd_br(stake), "odd": _odd_br(odd) if odd is not None else None,
            "resultado": resultado, "data": data,
            "fonte_odd": fonte_odd, "fonte_data": fonte_data}


# ── gravação ─────────────────────────────────────────────────────────────────────────

MAX_ITENS = 200


def _registro(f, motivos: list[str], cru_id: int | None = None) -> dict:
    bruto = json.dumps(f, ensure_ascii=False, sort_keys=True, default=str)
    ok = not motivos
    return {
        "aceita": ok,
        "codigo": (f.get("codigo") or "").strip() if isinstance(f, dict) else "",
        "impressao": (f.get("impressao") or "").strip() if isinstance(f, dict) else "",
        "motivos": motivos,
        "ficha": bruto,
        # recusada dedupa pelo conteúdo: a mesma ficha ruim a cada captura não enche a tabela
        "hash_bruto": hashlib.sha256(bruto.encode("utf-8")).hexdigest(),
        "cru_id": cru_id,
    }


async def gravar(dono: str, casa_key: str, parceiro: str, versao_ext: str, origem: str,
                 registros: list[dict]) -> int:
    """Grava Fichas (aceitas e recusadas) e devolve quantas linhas entraram."""
    from database import get_pool
    pool = await get_pool()
    novas = 0
    async with pool.acquire() as conn:
        for r in registros:
            st = await conn.execute(
                """INSERT INTO ficha_sombra
                     (dono, casa, parceiro, codigo, impressao, aceita, motivos, ficha,
                      hash_bruto, versao_ext, origem, cru_id)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                   ON CONFLICT DO NOTHING""",
                dono, casa_key, parceiro or "", r["codigo"], r["impressao"], r["aceita"],
                r["motivos"], r["ficha"], r["hash_bruto"], versao_ext or "", origem or "",
                r.get("cru_id"))
            novas += st.endswith(" 1")
    return novas


async def gravar_cru(dono: str, casa_key: str, parceiro: str, familia: str, versao_ext: str,
                     origem: str, itens: list[dict]) -> list[int | None]:
    """Grava o cru e devolve, por item, o id da linha NOVA (None = já existia igual)."""
    from database import get_pool
    pool = await get_pool()
    ids: list[int | None] = []
    async with pool.acquire() as conn:
        for it in itens:
            ids.append(await conn.fetchval(
                """INSERT INTO captura_crua
                     (dono, casa, parceiro, familia, codigo, hash, cru, removidos,
                      versao_ext, origem)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                   ON CONFLICT DO NOTHING RETURNING id""",
                dono, casa_key, parceiro or "", familia, it["codigo"], it["hash"],
                _cru.canonico(it["cru"]), it["removidos"], versao_ext or "", origem or ""))
    return ids


def montar_ficha(familia: str, cru: dict, casa_key: str) -> tuple[dict | None, list[str]]:
    """(Ficha, motivos de recusa) pelo adaptador da família. Sem adaptador = (None, [])."""
    from adaptadores import Recusa, adaptador
    mod = adaptador(familia)
    if mod is None:
        return None, []
    try:
        f = mod.adaptar(cru, casa_key)
    except Recusa as e:
        return {"codigo": str((cru or {}).get("id") or ""), "cru_recusado": True}, [str(e)]
    except Exception as e:  # noqa: BLE001 — defeito do adaptador é recusa gravada, nunca 500
        logger.exception("ficha: adaptador %s quebrou em %s", familia, casa_key)
        return ({"codigo": str((cru or {}).get("id") or ""), "cru_recusado": True},
                [f"erro do adaptador: {type(e).__name__}: {e}"[:300]])
    # A impressão é do SERVIDOR, sobre o cru que ficou guardado (já filtrado): o adaptador
    # só copia o que é da aposta.
    f = dict(f, impressao=_cru.impressao(cru))
    return f, validar(f, casa_key)


def _desligada() -> bool:
    return os.environ.get("CRU_CAPTURA_DESLIGADA", "").strip() in ("1", "true", "sim")


@router.post("/captura/ficha")
async def receber(payload: dict = Body(...)):
    """A extensão manda o cru de um lote de bilhetes. Responde contagens; ela não espera."""
    sess = _captura.sessao_por_token(payload.get("token") or "")
    if not sess:
        raise HTTPException(401, "Token de captura inválido ou expirado.")
    versao = str(payload.get("versao") or "")
    _captura.registrar_versao(sess, versao)
    if _desligada():
        # 503, nunca 200: com 200 a extensão marcaria o cru como enviado e não reenviaria.
        raise HTTPException(503, "Captura do cru desligada no servidor; reenvie depois.")
    import virada as _virada      # tardio: a virada importa este módulo
    # Corrida cru × extrair (Feca, 12/10): o `/extrair` da casa virada espera este cru
    # terminar (`virada.esperar_cru`) antes de mandar qualquer coisa à IA.
    _virada.cru_entrou(sess.dono, sess.casa_key)
    try:
        return await _processar(sess, payload, versao)
    finally:
        _virada.cru_saiu(sess.dono, sess.casa_key)


async def _processar(sess, payload: dict, versao: str) -> dict:
    origem = str(payload.get("origem") or "")
    casa_origem = _captura.casa_de_host(origem) if origem else None
    if casa_origem and casa_origem != (sess.casa_key or "").upper():
        # Resposta FINAL (decisão do Feca): não grava, conta no log, a extensão não reenvia.
        logger.warning("ficha: cru de %s numa sessão de %s (dono %s) — 409, não gravado",
                       casa_origem, sess.casa_key, sess.dono)
        raise HTTPException(409, f"Cru do site de {casa_origem}; a conexão é {sess.casa}.")
    familia = str(payload.get("familia") or "").strip().lower()
    itens = payload.get("itens")
    if not familia or not isinstance(itens, list) or len(itens) > MAX_ITENS:
        raise HTTPException(400, f"`familia` e `itens` (lista de até {MAX_ITENS}) são obrigatórios.")

    aceitos, descartados = [], 0
    for it in itens:
        cod = it.get("codigo") if isinstance(it, dict) else None
        if not (isinstance(cod, str) and cod.strip()) or not isinstance(it.get("cru"), dict):
            descartados += 1
            continue
        # O filtro roda DE NOVO aqui (a extensão já filtrou): segunda trava, e o hash é o
        # do cru que de fato fica guardado.
        filtrado, removidos = _cru.filtrar(it["cru"])
        if len(_cru.canonico(filtrado).encode("utf-8")) > _cru.MAX_BYTES:
            descartados += 1
            logger.warning("ficha: cru de %s %s acima de %d bytes — descartado",
                           sess.casa_key, cod, _cru.MAX_BYTES)
            continue
        aceitos.append({"codigo": cod.strip(), "cru": filtrado,
                        "hash": _cru.impressao(filtrado), "removidos": removidos})
    ids = await gravar_cru(sess.dono, sess.casa_key, sess.parceiro, familia, versao, origem,
                           aceitos)

    import virada as _virada      # tardio: a virada importa este módulo
    fichas_aceitas = fichas_recusadas = na_planilha = 0
    if ligada(sess.casa_key) or _virada.virada(sess.casa_key):
        registros = []
        for it, cru_id in zip(aceitos, ids):
            if cru_id is None:
                continue          # cru igual ao já guardado: a Ficha dele já foi montada
            f, motivos = montar_ficha(familia, it["cru"], sess.casa_key)
            if f is None:
                continue          # família sem adaptador ainda: fica só o cru
            registros.append(_registro(f, motivos, cru_id))
        if registros:
            await gravar(sess.dono, sess.casa_key, sess.parceiro, versao, origem, registros)
            # Casa VIRADA (§7): a aceita vai à planilha, aberta ou liquidada; a recusada e o
            # termo fora do dicionário ficam para a IA, pelo texto.
            na_planilha = await _virada.gravar_aceitas(sess, registros)
        fichas_aceitas = sum(1 for r in registros if r["aceita"])
        fichas_recusadas = len(registros) - fichas_aceitas
        if fichas_recusadas:
            logger.warning("ficha: %s %s — %d Ficha(s) recusada(s): %s", sess.dono,
                           sess.casa_key, fichas_recusadas,
                           next(r["motivos"] for r in registros if not r["aceita"])[:3])
    return {"guardado": True, "recebidos": len(itens), "descartados": descartados,
            "novos": sum(1 for i in ids if i is not None),
            "fichas": {"aceitas": fichas_aceitas, "recusadas": fichas_recusadas},
            "na_planilha": na_planilha}
