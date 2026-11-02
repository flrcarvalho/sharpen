"""Aviso diário ao Feca (D42, s438; Feca, 01/11/2026): "toda falha avisa o Feca, nunca o usuário".

A semente agora guarda a chave errada até alguém corrigir (E1, D24), então o Feca precisa VER os
erros. Uma mensagem por dia, no canal `TELEGRAM_ALERTA_*` (o mesmo do aviso de cadastro,
`main.avisar_admin`), logo depois da semente das 04h (`dicionario.diario`), com:

  • recusas repetidas: chave que a semente recusou `REPETIDA_MIN` vezes ou mais na rodada
    (`semente_recusa`, origem `semente`);
  • mercados sem par gravados com o texto da casa nas últimas 24 h (`semente_recusa`, `gravacao`);
  • a semente: rodou (termos, preservadas) ou falhou (`registrar_falha`, e a falta da rodada);
  • apostas pendentes há mais de 24 h (`ficha_virada.pendente_desde`, D39);
  • captura incompleta esgotada nas últimas 24 h (`virada_log.captura_esgotada`, D39).

Só contagens por CASA e chaves de mercado: nenhum nome de usuário, conta ou valor (dado pessoal
fica fora). Sem nada a dizer, não manda. No máximo UMA por dia: a tabela `aviso_admin` é reservada
antes do envio (`INSERT … ON CONFLICT DO NOTHING`), então duas réplicas ou um reinício não mandam
duas vezes; o envio que falha fica registrado (`ok = false`) e não se repete no mesmo dia.

`teste_uma_vez`: a mensagem de teste que o Feca pediu ("teste do aviso diário da semente"),
mandada UMA vez pelo próprio app em produção, sem ninguém tocar no token.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger("scanner")

REPETIDA_MIN = 3
MAX_LINHAS = 6
CHAVE_TESTE = "teste-s438"
TEXTO_TESTE = "teste do aviso diário da semente"
LIMITE_TELEGRAM = 3800
_falhas: list[str] = []           # falhas da semente desde o último aviso (memória do processo)


def registrar_falha(onde: str, erro: BaseException) -> None:
    """A semente falhou: entra no próximo aviso (tipo do erro e o começo da mensagem)."""
    _falhas.append(f"{onde}: {type(erro).__name__} {str(erro)[:120]}".strip())


def _hoje_brt() -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=3)).strftime("%Y-%m-%d")


async def montar(conn) -> str | None:
    """O texto do aviso de hoje, ou None quando não há nada a dizer."""
    linhas: list[str] = []
    rep = await conn.fetch(
        "SELECT casa, tipo, chave, motivo, n FROM semente_recusa WHERE origem = 'semente' "
        "AND n >= $1 AND ultima_em >= NOW() - interval '26 hours' ORDER BY n DESC, casa, chave",
        REPETIDA_MIN)
    if rep:
        linhas.append(f"• Recusas repetidas (≥{REPETIDA_MIN} na rodada): {len(rep)} chave(s)")
        linhas += [f"   {r['casa']} · {r['tipo']} · {r['chave']} · {r['motivo']} ({r['n']})"
                   for r in rep[:MAX_LINHAS]]
    sem_par = await conn.fetch(
        "SELECT casa, chave, n FROM semente_recusa WHERE origem = 'gravacao' "
        "AND ultima_em >= NOW() - interval '24 hours' ORDER BY n DESC, casa, chave")
    if sem_par:
        linhas.append(f"• Mercados gravados com o texto da casa (24 h): {len(sem_par)}")
        linhas += [f"   {r['casa']} · {r['chave']} ({r['n']})" for r in sem_par[:MAX_LINHAS]]
    rodada = await conn.fetchrow(
        "SELECT termos, fontes FROM semente_log WHERE gatilho = 'diaria' "
        "AND criado_em >= NOW() - interval '6 hours' ORDER BY id DESC LIMIT 1")
    falhas = list(_falhas)
    if falhas:
        linhas.append(f"• A semente FALHOU {len(falhas)} vez(es): " + " | ".join(falhas[:3]))
    elif rodada is None:
        linhas.append("• A semente diária não registrou rodada hoje")
    pend = await conn.fetch(
        "SELECT casa, count(*) AS n FROM ficha_virada WHERE pendente_desde IS NOT NULL "
        "AND pendente_desde < NOW() - interval '24 hours' GROUP BY casa ORDER BY n DESC, casa")
    if pend:
        linhas.append(f"• Pendentes há mais de 24 h: {sum(r['n'] for r in pend)} ("
                      + ", ".join(f"{r['casa']}: {r['n']}" for r in pend[:MAX_LINHAS]) + ")")
    esg = await conn.fetch(
        "SELECT casa, sum(captura_esgotada) AS n FROM virada_log "
        "WHERE criado_em >= NOW() - interval '24 hours' GROUP BY casa "
        "HAVING sum(captura_esgotada) > 0 ORDER BY n DESC, casa")
    if esg:
        linhas.append(f"• Captura incompleta esgotada (24 h): {sum(r['n'] for r in esg)} ("
                      + ", ".join(f"{r['casa']}: {r['n']}" for r in esg[:MAX_LINHAS]) + ")")
    if not linhas:
        return None
    if rodada is not None and not falhas:
        import json
        fontes = rodada["fontes"]
        fontes = json.loads(fontes) if isinstance(fontes, str) else (fontes or {})
        linhas.insert(0, f"• Semente das 04h: {rodada['termos']} termo(s) na rodada, "
                         f"{fontes.get('preservadas', 0)} preservada(s)")
    texto = f"Sharpen · aviso diário da semente ({_hoje_brt()})\n" + "\n".join(linhas)
    return texto[:LIMITE_TELEGRAM]


async def _reservar(conn, chave: str) -> bool:
    return await conn.fetchval("INSERT INTO aviso_admin (chave) VALUES ($1) "
                               "ON CONFLICT DO NOTHING RETURNING true", chave) is not None


async def _enviar(conn, chave: str, texto: str) -> bool:
    if not await _reservar(conn, chave):
        return False                              # já mandado (ou tentado) com esta chave
    import main
    ok = await main.avisar_admin(texto)
    await conn.execute("UPDATE aviso_admin SET ok = $2, texto = $3 WHERE chave = $1",
                       chave, ok, texto)
    return ok


async def enviar_diario(conn) -> bool:
    """O aviso de hoje, uma vez por dia (dia de Brasília). Nunca levanta."""
    try:
        texto = await montar(conn)
        if not texto:
            return False
        ok = await _enviar(conn, f"diario-{_hoje_brt()}", texto)
        if ok:
            _falhas.clear()
        return ok
    except Exception:  # noqa: BLE001 — o aviso nunca derruba a semente
        logger.exception("aviso diário: não enviado")
        return False


async def teste_uma_vez() -> bool:
    """A mensagem de teste do Feca, uma vez só na vida do banco. Nunca levanta."""
    try:
        from database import get_pool
        pool = await get_pool()
        async with pool.acquire() as conn:
            return await _enviar(conn, CHAVE_TESTE, TEXTO_TESTE)
    except Exception:  # noqa: BLE001
        logger.exception("aviso diário: teste não enviado")
        return False
