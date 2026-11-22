"""Travas de ENTRADA: o que nem chega à IA nem é gravado (s465, plano do marco zero E1.1).

Funções puras. Quem recorta o texto em blocos e quem grava é o `main` (texto) e a `virada`
(cru); aqui só se decide, bloco a bloco ou Ficha a Ficha, se a aposta entra.

**1. Idade (D51, Feca, 22/11/2026): aposta FINALIZADA com mais de 12 meses NÃO entra no
Sharpen. Aposta ABERTA entra sempre, de qualquer data.** Regra geral, toda casa e todo usuário.
O caso: a Sportsbet.io do Jonathan mandou em 21/11 o histórico inteiro da conta (185 apostas
de abril a setembro de 2023), que foi à IA 4 vezes (US$ 4,61) e foi apagado 4 vezes. O piso de
sanidade dos robôs da extensão (`content.js`, `pisoSanidade = cutoff − 730 dias`) não para em
liquidada mais velha que isso, e o horizonte por conta (7.6) só alarga a janela; a trava tem
de ser do servidor.

  • FINALIZADA = o texto traz o veredito na linha `Status:` (`→ W/L/V/HW/HL`, o mesmo
    `virada._VEREDITO`). Medido em 22/11/2026 com a fotografia do harness (63 casos, 29
    formatadores): todo bloco liquidado o traz. Sem veredito, o bloco FICA (fail-open): a
    Superbet escreve o status cru da casa (`win`/`lost`), e a Bet365 escreve "a conferir
    HW/HL" na meia sem rótulo.
  • A data é a MAIS RECENTE do bloco: colocação (`Data (colocação):`, `Colocada:`,
    `Apostado em:`), evento (`Data:`, `Data (evento):`, `Data (evento mais recente):`) e
    liquidação (`Liquidado em:`, `Liquidada em:`). Aposta colocada há 14 meses e liquidada há
    um mês entra: ela mexeu no dinheiro dentro da janela.
  • Bloco sem data legível FICA (esconder aposta é o erro caro; `CLAUDE.md`, corte histórico).
  • "Mais de 12 meses" = a mais recente ANTES do mesmo dia, um ano atrás (29/02 vira 28/02).

**2. Moeda da Sportsbet.io fora das medidas.** O dinheiro da casa vem em unidades e a escala
(1e8) só foi provada em USDT e USDC (`adaptadores/sbi._MOEDAS_MEDIDAS`, importada daqui, não
copiada). O inject divide QUALQUER moeda por 1e8: conta em real virava `Stake: 0,01` no texto e
a IA gravava 0,02 USDT (risco R45 da consultoria: stake errada gravada sem erro). O bloco sai
antes da IA; a Ficha já recusava.

  • Pelo TEXTO: o `formatTicketSBI` só escreve a linha `Moeda:` quando a moeda NÃO é real
    (`_moedaNaoReal`). Bloco sem `Moeda:` = conta em real (ou moeda vazia, que o adaptador
    também recusa). Medido em 22/11/2026 com o formatador real sobre os 879 crus de 30 dias:
    nenhum bloco USDT/USDC sem a linha; os 185 sem ela são os BRL do Jonathan.

NÃO cobre: texto colado à mão sem `[Código:]` (o bloco não se recorta) e conta em real
noutra casa cripto (cada adaptador tem a sua trava de moeda; esta é só da Sportsbet.io).
"""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone

from adaptadores import sbi as _sbi
from cambio import moedas_do_texto

IDADE = "mais de 12 meses"
MOEDA = "moeda fora da medida"

_DATA = r"\s*(\d{2})/(\d{2})/(\d{4})"
# Toda linha de data que um formatador escreve: `Data:`, `Data (colocação):`, `Data (evento):`,
# `Data (evento mais recente):`, `Colocada:`, `Apostado em:`, `Liquidado em:`, `Liquidada em:`.
_DATAS_RE = re.compile(r"^(?:Data(?: \([^)\n]*\))?|Colocada|Apostado em|Liquidad[oa] em):" + _DATA,
                       re.MULTILINE)
_BRASILIA = timezone(timedelta(hours=-3))
# O resultado que a Ficha deriva e que fecha a aposta (`ficha.derivar`).
_FINALIZADOS = frozenset({"W", "L", "V", "HW", "HL"})


def hoje_brasilia() -> date:
    return datetime.now(_BRASILIA).date()


def limite(hoje: date) -> date:
    """O primeiro dia que ainda entra: o mesmo dia, um ano atrás."""
    try:
        return hoje.replace(year=hoje.year - 1)
    except ValueError:                       # 29/02
        return hoje.replace(year=hoje.year - 1, day=28)


def _datas(regex, bloco: str) -> list[date]:
    out = []
    for m in regex.finditer(bloco or ""):
        try:
            out.append(date(int(m.group(3)), int(m.group(2)), int(m.group(1))))
        except ValueError:
            continue
    return out


def data_do_bloco(bloco: str) -> date | None:
    """A data mais recente do bloco (colocação, evento, liquidação); sem nenhuma, None."""
    datas = _datas(_DATAS_RE, bloco)
    return max(datas) if datas else None


def bloco_finalizado(bloco: str) -> bool:
    """O texto traz o veredito (`Status: … → W/L/V/HW/HL`): a régua é a da virada, um lugar só."""
    from virada import _VEREDITO
    return bool(_VEREDITO.search(bloco or ""))


def bloco_velho(bloco: str, hoje: date) -> bool:
    """Finalizada E com a data mais recente antes do limite. Aberta, ou sem veredito legível, ou
    sem data: entra (fail-open)."""
    if not bloco_finalizado(bloco):
        return False
    d = data_do_bloco(bloco)
    return d is not None and d < limite(hoje)


def bloco_moeda_fora(casa_key: str, bloco: str) -> bool:
    if (casa_key or "").upper() != "SPORTSBETIO":
        return False
    moedas = [m.strip().upper() for m in moedas_do_texto(bloco)]
    return not moedas or any(m not in _sbi._MOEDAS_MEDIDAS for m in moedas)


def motivo_do_bloco(casa_key: str, bloco: str, hoje: date) -> str | None:
    """Por que o bloco não entra (`IDADE` primeiro, depois `MOEDA`), ou None se entra."""
    if bloco_velho(bloco, hoje):
        return IDADE
    if bloco_moeda_fora(casa_key, bloco):
        return MOEDA
    return None


def _dt(v) -> date | None:
    if not v:
        return None
    try:
        d = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    except ValueError:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(_BRASILIA).date()


def ficha_finalizada(f: dict | None) -> bool:
    """A Ficha deriva resultado que fecha a aposta. Se não deriva (cru aberto, ou que não se lê),
    não está finalizada: fail-open."""
    if not f:
        return False
    try:
        import ficha as _ficha
        return _ficha.derivar(f).get("resultado") in _FINALIZADOS
    except Exception:  # noqa: BLE001 — Ficha que não deriva não prova nada: entra
        return False


def ficha_velha(f: dict | None, hoje: date) -> bool:
    """A mesma régua na rota do cru: Ficha FINALIZADA e a mais recente entre `colocada_em`,
    `liquidada_em` e o início das pernas antes do limite; sem nenhuma data, a Ficha entra."""
    if not ficha_finalizada(f):
        return False
    datas = [x for x in [_dt(f.get("colocada_em")), _dt(f.get("liquidada_em"))]
             + [_dt(p.get("inicio")) for p in f.get("pernas") or []] if x]
    return bool(datas) and max(datas) < limite(hoje)
