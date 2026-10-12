"""Ficha Sharpen, em MODO SOMBRA (Projeto Ficha Sharpen, D1; s409).

A extensão monta a Ficha (o formato único de `docs/PROJETO_FICHA_SHARPEN/01_FICHA_SHARPEN.md`)
a partir do JSON da casa e manda aqui, SEPARADA do `/captura/enviar` e sem esperar resposta. O
caminho de hoje continua mandando no banco: esta rota grava na `ficha_sombra`, uma tabela que
nada mais lê, e NUNCA toca em `bilhetes`. A régua compara as duas depois.

Três decisões do Feca (11/10) que moram aqui:

  • **Ficha recusada é gravada com o motivo, nunca descartada.** Descartada, ela viraria
    "faltou" na régua, sem causa.
  • **Casa e conta saem da SESSÃO de captura**, nunca do corpo da Ficha. O token aponta para
    o pareamento feito no dashboard (dono logado + casa + conta escolhidas ali). Ficha que
    diz outra casa é recusada, e o motivo fica gravado.
  • **Chave por casa (`FICHA_SOMBRA_CASAS`), vazia = desligada.** Desligada, a rota responde
    `ligada: false` e não grava nada: é o estado de antes, não uma recusa.

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
MAX_FICHAS = 500


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


def _odd(f: dict, resultado: str, stake: Decimal, retorno: Decimal | None) -> tuple[Decimal | None, str]:
    """A odd pela regra aprovada (Feca, 11/10). Devolve (odd, de onde veio)."""
    casa = _dec(f.get("odd"))
    if f.get("status") == "cashout":
        if resultado == "V":
            return casa, "cashout = stake: odd da casa"
        return retorno / stake, "cashout: retorno ÷ stake"
    if resultado in ("", "L", "V", "HL"):
        return casa, "odd da casa" + (" (calculada pelo adaptador)" if f.get("odd_calculada") else "")
    if f.get("tipo") == "sistema":
        return casa, "sistema: odd da casa (régua própria, MASTER_RESULTADO §7.3)"
    calc = None if f.get("odd_calculada") else _produto(f.get("pernas") or [])

    def fecha(o):
        return o is not None and abs(_paga(resultado, stake, o) - retorno) <= _CENTAVO

    if fecha(casa):
        return casa, "fecha o retorno: odd da casa"
    if fecha(calc):
        return calc, "fecha o retorno: produto das pernas"
    if resultado == "W":
        return retorno / stake, "nenhuma fecha: retorno ÷ stake"
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

def _registro(f, motivos: list[str]) -> dict:
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
    }


async def gravar(dono: str, casa_key: str, parceiro: str, versao_ext: str, origem: str,
                 registros: list[dict]) -> int:
    """Grava e devolve quantas linhas entraram (o resto já existia)."""
    from database import get_pool
    pool = await get_pool()
    novas = 0
    async with pool.acquire() as conn:
        for r in registros:
            st = await conn.execute(
                """INSERT INTO ficha_sombra
                     (dono, casa, parceiro, codigo, impressao, aceita, motivos, ficha,
                      hash_bruto, versao_ext, origem)
                   VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                   ON CONFLICT DO NOTHING""",
                dono, casa_key, parceiro or "", r["codigo"], r["impressao"], r["aceita"],
                r["motivos"], r["ficha"], r["hash_bruto"], versao_ext or "", origem or "")
            novas += st.endswith(" 1")
    return novas


@router.post("/captura/ficha")
async def receber(payload: dict = Body(...)):
    """A extensão manda um lote de Fichas. Responde contagens; a extensão não espera."""
    sess = _captura.sessao_por_token(payload.get("token") or "")
    if not sess:
        raise HTTPException(401, "Token de captura inválido ou expirado.")
    versao = str(payload.get("versao") or "")
    _captura.registrar_versao(sess, versao)
    if not ligada(sess.casa_key):
        return {"ligada": False}
    fichas = payload.get("fichas")
    if not isinstance(fichas, list) or len(fichas) > MAX_FICHAS:
        raise HTTPException(400, f"`fichas` deve ser uma lista de até {MAX_FICHAS}.")
    origem = str(payload.get("origem") or "")
    # Amarração casa↔site, a mesma do `/captura/enviar`. Aqui não se rejeita o lote: cada
    # ficha é gravada RECUSADA com o motivo (decisão do Feca: recusada nunca some).
    casa_origem = _captura.casa_de_host(origem) if origem else None
    fora_do_site = bool(casa_origem and casa_origem != (sess.casa_key or "").upper())
    registros = []
    for f in fichas:
        motivos = validar(f, sess.casa_key)
        if fora_do_site:
            motivos.append(f"veio do site de {casa_origem}, a sessão é {sess.casa_key}")
        # Conta vazia (pareamento sem conta) NÃO recusa: grava com `parceiro = ''` e a régua
        # aponta, porque compara por dono + casa + código.
        registros.append(_registro(f, motivos))
    novas = await gravar(sess.dono, sess.casa_key, sess.parceiro, versao, origem, registros)
    aceitas = sum(1 for r in registros if r["aceita"])
    if len(registros) - aceitas:
        logger.warning("ficha: %s %s — %d de %d recusada(s): %s", sess.dono, sess.casa_key,
                       len(registros) - aceitas, len(registros),
                       next(r["motivos"] for r in registros if not r["aceita"])[:3])
    return {"ligada": True, "recebidas": len(registros), "aceitas": aceitas,
            "recusadas": len(registros) - aceitas, "novas": novas}
