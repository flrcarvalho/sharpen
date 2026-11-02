"""Rotas da Kalshi (s439): a chave da conta, o Sincronizar e a Caixa automática.

O coletor (`kalshi.py`) lê a conta e devolve linhas prontas; este módulo guarda a chave,
grava o que o coletor leu e confere a Caixa. Mesmo molde da Polymarket (`/polymarket/sync`
no `main.py`), com duas diferenças que mudam o desenho:

  • **A conta é PRIVADA.** A Polymarket lê uma carteira pública pelo endereço; a Kalshi só
    responde com a chave do usuário. A chave privada fica no servidor, CIFRADA (Fernet, com
    o segredo na env var `KALSHI_CHAVE_CIFRA`, que nunca vai ao banco), e nunca volta para
    a tela. Só entra chave SÓ LEITURA (`kalshi.conferir_chave`, decisão do Feca de 30/10).
  • **A chave é da CONTA, não do dono.** Um dono pode ter duas contas Kalshi; a linha de
    `kalshi_chave` é chaveada por `parceiros.id` e some com a conta (CASCADE).

Único ponto de registro no `main.py`: o `include_router` (o `main.py` é da Ficha, aval do
Feca em 01/11 para esta linha). Nada aqui mexe no `repository.py`: ele é só lido.

Rotas de CRIAÇÃO usam `usuario_atual` (a base de quem está logado), como o `/polymarket/sync`.
"""
from __future__ import annotations

import logging
import os
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import httpx
from cryptography.fernet import Fernet, InvalidToken
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

import kalshi
from auth import usuario_atual
from database import get_pool
from polymarket import CambioIndisponivel
from repository import (
    _caixa_apostas, _caixa_mov_dict, _caixa_projetar, _moeda_conta,
    auto_arquivar, caixa_conta, upsert_bilhetes,
)

logger = logging.getLogger("scanner")
router = APIRouter()

ENV_CIFRA = "KALSHI_CHAVE_CIFRA"
CASA = kalshi.CASA
BRT = timezone(timedelta(hours=-3))


class CifraAusente(Exception):
    """O servidor não tem o segredo da cifra: nenhuma chave entra nem sai."""


# ── Cifra (PURA: o segredo entra como argumento) ─────────────────────────────

def _fernet(segredo: str | None) -> Fernet:
    s = (segredo or "").strip()
    if not s:
        raise CifraAusente()
    try:
        return Fernet(s.encode())
    except (ValueError, TypeError) as exc:
        raise CifraAusente() from exc


def cifrar(pem: str, segredo: str | None) -> str:
    return _fernet(segredo).encrypt(pem.encode()).decode()


def decifrar(token: str, segredo: str | None) -> str:
    """Levanta `CifraAusente` também quando o segredo TROCOU: a chave guardada não abre
    mais, e o caminho é o mesmo da chave ausente (conectar de novo)."""
    try:
        return _fernet(segredo).decrypt(token.encode()).decode()
    except InvalidToken as exc:
        raise CifraAusente() from exc


def _segredo() -> str | None:
    return os.environ.get(ENV_CIFRA)


def prefixo_key_id(key_id: str) -> str:
    """O que a tela pode ver da chave: os 8 primeiros caracteres do ID, para o usuário
    reconhecer qual chave está conectada. A chave privada nunca sai do servidor."""
    return (key_id or "")[:8] + "…"


_MSG_CIFRA = ("A guarda de chaves da Kalshi não está configurada no servidor. "
              "Avise o suporte do Sharpen.")


# ── Conta e chave no banco ──────────────────────────────────────────────────

async def _conta(conn, dono: str, parceiro: str):
    p = await conn.fetchrow(
        "SELECT id, casa, nome, moeda FROM parceiros WHERE dono = $1 AND casa = $2 AND nome = $3",
        dono, CASA, (parceiro or "").strip())
    if not p:
        raise HTTPException(404, f"A conta {parceiro} da Kalshi não está cadastrada.")
    return p


async def _credencial(conn, dono: str, pid: int) -> kalshi.Credencial:
    r = await conn.fetchrow(
        "SELECT key_id, pem_cifrado FROM kalshi_chave WHERE parceiro_id = $1 AND dono = $2",
        pid, dono)
    if not r:
        raise HTTPException(409, "Conecte a chave da Kalshi desta conta antes de sincronizar.")
    try:
        pem = decifrar(r["pem_cifrado"], _segredo())
    except CifraAusente:
        raise HTTPException(503, _MSG_CIFRA)
    try:
        return kalshi.Credencial(r["key_id"], pem)
    except kalshi.KalshiChaveInvalida as exc:
        raise HTTPException(400, str(exc))


class ChaveRequest(BaseModel):
    parceiro: str
    key_id: str = Field(max_length=100)
    pem: str = Field(max_length=10_000)


@router.get("/kalshi/chave")
async def kalshi_chave_estado(parceiro: str, dono: str = Depends(usuario_atual)):
    """Se a conta tem chave conectada. NUNCA devolve a chave: só o começo do ID."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        p = await _conta(conn, dono, parceiro)
        r = await conn.fetchrow(
            "SELECT key_id, conferida_em, ultimo_sync FROM kalshi_chave "
            "WHERE parceiro_id = $1 AND dono = $2", p["id"], dono)
    if not r:
        return {"tem": False}
    return {"tem": True, "key_id": prefixo_key_id(r["key_id"]),
            "conferida_em": r["conferida_em"].isoformat(),
            "ultimo_sync": r["ultimo_sync"].isoformat() if r["ultimo_sync"] else None}


@router.post("/kalshi/chave")
async def kalshi_chave_salvar(body: ChaveRequest, dono: str = Depends(usuario_atual)):
    """Confere a chave NA KALSHI (autentica e é só leitura) e só então guarda, cifrada.
    Chave que não passa não é gravada: guardar e descobrir depois deixaria a conta com
    uma chave que nunca funcionou."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        p = await _conta(conn, dono, body.parceiro)
    try:
        cred = kalshi.Credencial(body.key_id, body.pem)
        async with httpx.AsyncClient(timeout=30.0) as client:
            await kalshi.conferir_chave(client, cred)
    except kalshi.KalshiChaveInvalida as exc:
        raise HTTPException(400, str(exc))
    except kalshi.KalshiErro as exc:
        raise HTTPException(502, str(exc))
    try:
        cifrado = cifrar(body.pem, _segredo())
    except CifraAusente:
        raise HTTPException(503, _MSG_CIFRA)
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO kalshi_chave (parceiro_id, dono, key_id, pem_cifrado) "
            "VALUES ($1, $2, $3, $4) "
            "ON CONFLICT (parceiro_id) DO UPDATE SET key_id = EXCLUDED.key_id, "
            "pem_cifrado = EXCLUDED.pem_cifrado, conferida_em = NOW(), ultimo_sync = NULL",
            p["id"], dono, cred.key_id, cifrado)
    logger.info("kalshi: chave conectada dono=%s conta=%s key=%s", dono, p["id"],
                prefixo_key_id(cred.key_id))
    return {"tem": True, "key_id": prefixo_key_id(cred.key_id)}


@router.delete("/kalshi/chave")
async def kalshi_chave_remover(parceiro: str, dono: str = Depends(usuario_atual)):
    """Desconecta: apaga a chave do servidor. As apostas já gravadas ficam."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        p = await _conta(conn, dono, parceiro)
        await conn.execute("DELETE FROM kalshi_chave WHERE parceiro_id = $1 AND dono = $2",
                           p["id"], dono)
    return {"tem": False}


# ── Sincronizar ─────────────────────────────────────────────────────────────

class SyncRequest(BaseModel):
    parceiro: str
    ensaio: bool = False


def alerta_nao_mapeado(nm: dict) -> str | None:
    """Tag de esporte ou escopo de mercado que o coletor ainda não conhece: a aposta
    entrou como `Outro`/`Outros`, e o aviso diz qual, para virar mapa."""
    partes = []
    if nm.get("tags"):
        partes.append("esporte " + ", ".join(nm["tags"]))
    if nm.get("escopos"):
        partes.append("mercado " + ", ".join(nm["escopos"]))
    if not partes:
        return None
    return ("Sem tradução ainda (entrou como Outro/Outros): " + "; ".join(partes) + ".")


@router.post("/kalshi/sync")
async def kalshi_sync(body: SyncRequest, dono: str = Depends(usuario_atual)):
    """Lê a conta inteira na Kalshi e grava na grade (casa='Kalshi', origem='sync').

    `ensaio=True` lê e devolve as linhas SEM gravar nada (o ensaio que o BACKLOG pede
    antes da 1ª gravação). Mesma resposta do `/polymarket/sync` no caminho real."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        p = await _conta(conn, dono, body.parceiro)
        cred = await _credencial(conn, dono, p["id"])
    parceiro = p["nome"]

    try:
        res = await kalshi.coletar(cred, parceiro)
    except kalshi.KalshiChaveInvalida as exc:
        raise HTTPException(400, str(exc))
    except kalshi.KalshiErro as exc:
        raise HTTPException(502, str(exc))
    except CambioIndisponivel as exc:
        raise HTTPException(503, str(exc))
    except Exception:
        logger.exception("Falha na coleta Kalshi")
        raise HTTPException(502, "Erro ao consultar a Kalshi. Tente novamente.")

    rows = [{k: v for k, v in r.items() if k != "_sort"} for r in res["linhas"]]
    alertas = list(res["alertas"])
    nm = alerta_nao_mapeado(res.get("nao_mapeado") or {})
    if nm:
        alertas.append(nm)
    caixa_dados = res.get("caixa") or {}

    if body.ensaio:
        return {"ensaio": True, "coletados": len(rows), "linhas": rows, "alertas": alertas,
                "caixa": {k: caixa_dados.get(k) for k in ("saldo", "inicio", "erro")}
                         | {"movimentos": len(caixa_dados.get("movimentos") or [])}}

    inseridos = atualizados = arquivados = 0
    ids: list = []
    duplicatas: dict = {}
    if rows:
        inseridos, atualizados, ids, alertas_up, duplicatas = await upsert_bilhetes(
            rows, dono, origem="sync")
        alertas += alertas_up
        arquivados = await auto_arquivar(CASA, parceiro, len(ids), dono)
    else:
        alertas.append("Nenhuma aposta encontrada nesta conta da Kalshi.")

    async with pool.acquire() as conn:
        # A conta é em dólar por fato (o coletor grava a origem em USD de toda aposta),
        # como a Polymarket (s397). Depois do upsert: nunca USD com aposta sem origem.
        st = await conn.execute(
            "UPDATE parceiros SET moeda = 'USD' WHERE id = $1 AND dono = $2 AND moeda <> 'USD'",
            p["id"], dono)
        if int(st.split()[-1]) > 0:
            alertas.append(f"A conta {parceiro} passou a ser em dólar (USD), a moeda da Kalshi: "
                           "a grade mostra o valor original de cada aposta.")
        await conn.execute("UPDATE kalshi_chave SET ultimo_sync = NOW() WHERE parceiro_id = $1",
                           p["id"])

    caixa = await _caixa(dono, p["id"], caixa_dados, alertas)
    return {"salvos": inseridos + atualizados, "inseridos": inseridos, "atualizados": atualizados,
            "ids": ids, "alertas": alertas, "duplicatas": duplicatas, "arquivados": arquivados,
            "coletados": len(rows), "caixa": caixa}


# ── Caixa automática ────────────────────────────────────────────────────────

async def _caixa(dono: str, pid: int, dados: dict, alertas: list) -> dict | None:
    """Caixa depois do sync. Nunca derruba o sync: o que der errado vira ALERTA."""
    if dados.get("erro"):
        logger.warning("caixa kalshi: leitura falhou: %s", dados["erro"])
        alertas.append(f"Caixa da Kalshi não atualizada: {dados['erro']}. As apostas foram "
                       "sincronizadas.")
        return None
    alertas += dados.get("alertas") or []
    try:
        res = await caixa_kalshi_sync(dono, pid, dados)
    except Exception:
        logger.exception("caixa kalshi: gravação falhou")
        alertas.append("Caixa da Kalshi não atualizada: erro ao gravar. As apostas foram "
                       "sincronizadas.")
        return None
    cx = res.get("caixa") or {}
    if cx.get("estado") == "divergente" and cx.get("divergencia") is not None:
        d = cx["divergencia"]
        lado = "a mais na conta" if d > 0 else "a menos na conta"
        valor = f"{abs(d):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        alertas.append(f"Caixa da Kalshi: US$ {valor} {lado} do que o Sharpen calcula. "
                       "Confira no extrato da Caixa.")
    return {"estado": cx.get("estado"), "divergencia": cx.get("divergencia"),
            "novos": res.get("novos", 0)}


async def caixa_kalshi_sync(dono: str, pid: int, dados: dict) -> dict:
    """Grava na Caixa o que o sync leu da conta. Mesmo desenho da Polymarket
    (`repository.caixa_polymarket_sync`), numa transação:

      1. depósitos e saques com `ref` = `kalshi:<tipo>:<id>`: o índice único
         `caixa_mov_ref` faz o sync regravar a lista inteira sem duplicar;
      2. o `inicial` (US$ 0 no 1º dia da conta), só se ainda não há: a API traz o
         extrato inteiro, então não há saldo a digitar;
      3. a CONFERÊNCIA (`balance_dollars` contra o projetado), só quando um dos dois mudou
         desde a última, para cada sync não empilhar uma conferência igual.

    Não tem a TRAVA da Polymarket (a lista de transferências da blockchain contra o
    saldo): aqui a lista vem da própria conta, e a conferência é a trava.
    A conferência registra, não absorve: grava o projetado daquele momento."""
    hoje = datetime.now(BRT).date()
    pool = await get_pool()
    async with pool.acquire() as conn:
        async with conn.transaction():
            p = await conn.fetchrow(
                "SELECT id, casa, nome, arquivado, moeda FROM parceiros WHERE id = $1 AND dono = $2",
                pid, dono)
            if not p:
                return {"ok": False, "motivo": "conta não encontrada"}
            moeda = _moeda_conta(p)
            novos = 0
            for m in dados.get("movimentos") or []:
                st = await conn.execute(
                    "INSERT INTO caixa_mov (dono, parceiro_id, tipo, data, valor, obs, moeda, ref) "
                    "VALUES ($1,$2,$3,$4,$5,$6,$7,$8) "
                    "ON CONFLICT (parceiro_id, ref) WHERE ref IS NOT NULL DO NOTHING",
                    dono, pid, m["tipo"], date.fromisoformat(m["data"]),
                    Decimal(str(m["valor"])), (m.get("obs") or "")[:280], moeda, m["ref"])
                novos += int(st.split()[-1])
            if not await conn.fetchval(
                    "SELECT 1 FROM caixa_mov WHERE parceiro_id = $1 AND tipo = 'inicial'", pid):
                await conn.execute(
                    "INSERT INTO caixa_mov (dono, parceiro_id, tipo, data, valor, obs, "
                    "abertas_corte, moeda) VALUES ($1,$2,'inicial',$3,$4,$5,$6,$7)",
                    dono, pid, date.fromisoformat(dados["inicio"]), Decimal("0"),
                    "Início da conta (automático)", [], moeda)
            movs = [_caixa_mov_dict(r) for r in await conn.fetch(
                "SELECT * FROM caixa_mov WHERE dono = $1 AND parceiro_id = $2 ORDER BY data, id",
                dono, pid)]
            apostas = await _caixa_apostas(conn, dono, p["casa"], p["nome"])
            projetado = round(_caixa_projetar(movs, apostas, moeda, p["casa"])["disponivel"], 2)
            valor = round(float(dados["saldo"]), 2)
            ult = await conn.fetchrow(
                "SELECT valor, projetado FROM caixa_mov WHERE parceiro_id = $1 "
                "AND tipo = 'conferencia' ORDER BY criado_em DESC, id DESC LIMIT 1", pid)
            if not (ult and ult["projetado"] is not None
                    and float(ult["valor"]) == valor and float(ult["projetado"]) == projetado):
                await conn.execute(
                    "INSERT INTO caixa_mov (dono, parceiro_id, tipo, data, valor, obs, "
                    "projetado, moeda) VALUES ($1,$2,'conferencia',$3,$4,$5,$6,$7)",
                    dono, pid, hoje, Decimal(str(valor)),
                    "Automática: saldo da conta na Kalshi", Decimal(str(projetado)), moeda)
    res = await caixa_conta(dono, pid)
    logger.info("caixa kalshi: dono=%s conta=%s novos=%d estado=%s div=%s",
                dono, pid, novos, res and res.get("estado"), res and res.get("divergencia"))
    return {"ok": True, "novos": novos, "caixa": res}
