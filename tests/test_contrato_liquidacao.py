"""Contrato de LIQUIDAÇÃO, igual para todas as casas (plano de confiabilidade 8.1, s460).

A família L da auditoria de 17/11: a liquidação era consertada casa a casa, ~24 vezes, cada
vez com um teste da PRÓPRIA casa, e reaparecia na casa seguinte. Nada obrigava a casa nova
a passar pelas mesmas perguntas.

Aqui as perguntas são as mesmas para todas, e quem responde é o SERVIDOR: as funções reais
(`_financeiro_do_texto`, `_retorno_do_bloco`, `_veredito_do_retorno`, `tradutor._resultado`)
rodam sobre os blocos que os formatadores reais do `content.js` imprimem no harness
(`tests/fixtures/contrato_liquidacao/blocos.json.gz`, mantido por
`tools/contrato_liquidacao.py`; o CI confere que ele está em dia com o harness).

O contrato:
  1. todo bloco com UMA linha `Stake:` é lido pelo servidor (sem isso nenhum gate roda);
  2. resultado declarado (`→ X`) com retorno provado bate com o DINHEIRO (as cinco
     fórmulas do `calcular_pl` ao contrário). Única folga: `W` declarado onde o dinheiro
     prova `HW` (o `Ganho → W` da Bet365, que o servidor corrige, s356);
  3. Status "a conferir" nunca vira resultado no tradutor, mesmo com seta dentro;
  4. cobertura de cenários por casa (W, L, V, HW, HL, cashout, aberta, a conferir) NÃO
     REGRIDE, casa nova declara a sua, e toda casa tem W e L (dívida nomeada abaixo).

Os quatro defeitos que o contrato achou na 1ª rodada, cada um com teste próprio abaixo:
  a. `_veredito_do_retorno` com piso de R$ 0,10 em moeda de valor alto: BTC ganho virava V;
  b. a Ficha com meio centavo fixo: cashout em BTC virava V;
  c. `Stake: 30,00 USDT` (família TV) recusado pela regex: o gate não rodava nela;
  d. Status "a conferir" com os vereditos das sub-apostas (Cloudbet) virava L.

Mutações provadas (aplicadas ao código, o teste ao lado ficou vermelho, revertidas):
  1. piso volta a 0,10 fixo                      → test_veredito_em_btc_nao_vira_void
                                                   + test_todo_resultado_declarado_bate…
  2. `_tol` da Ficha volta a 0,005 fixo           → test_ficha_cashout_em_btc_nao_vira_void
  3. regex da stake sem o sufixo de moeda        → test_stake_com_moeda_depois_e_lida
                                                   + test_todo_bloco_com_stake_e_lido…
  4. `_resultado` sem a guarda do "a conferir"   → test_a_conferir_nunca_vira_resultado
  5. cobertura de uma casa perde um cenário      → test_cobertura_por_casa_nao_regride
  6. some a exigência de W                       → test_toda_casa_tem_w_e_l…

NÃO cobre: se o valor do bloco é VERDADE (o contrato confia no robô); casa sem bloco de
texto (print); a linha aberta com resultado declarado (8.2, em
`test_resultado_declarado_linha_aberta.py`); "perna anulada" como cenário próprio (o texto
não tem marcador estável entre casas; entra como W pelo dinheiro).
"""
import gzip
import json
import pathlib
import re
from decimal import Decimal

import pytest

import ficha
import repository as R
import tradutor as T

PASTA = pathlib.Path(__file__).parent / "fixtures" / "contrato_liquidacao"
BLOCOS = json.loads(gzip.decompress((PASTA / "blocos.json.gz").read_bytes()).decode("utf-8"))
COBERTURA = json.loads((PASTA / "cobertura.json").read_text(encoding="utf-8"))

_CASHOUT = re.compile(r"cash ?out|cashed|encerrad", re.I)
_STAKE_LINHA = re.compile(r"^Stake:", re.M)

# Casas SEM bloco de W no harness em 17/11/2026. É dívida, não isenção: a lista só encolhe
# (o teste reprova quando uma delas ganha W e continua aqui, e quando uma casa fora dela
# fica sem W). Fixture de W ganho vem da conta real, nunca inventada.
SEM_W_NO_HARNESS = {"1xBit", "20bet", "Faz1bet", "GoldenBet", "Jack", "Locasbet", "MelBet",
                    "PariPesa"}


def _codigo(bloco: str) -> str:
    return R._ID_MARCADOR_RE.search(bloco).group(1).strip()


def _status(bloco: str, info: dict | None) -> str:
    if info and info.get("status"):
        return info["status"]
    m = R._STATUS_TXT_RE.search(bloco)
    return m.group(1) if m else ""


def cobertura(blocos: dict) -> dict[str, list[str]]:
    """{caso: cenários}. O cenário é o que o SERVIDOR lê do bloco, não o que a casa diz."""
    out = {}
    for caso, lista in blocos.items():
        tags = set()
        for b in lista:
            stt = _status(b, R._financeiro_do_texto(b).get(_codigo(b)))
            d = T._resultado(stt)
            if d:
                tags.add(d)
                if _CASHOUT.search(stt):
                    tags.add("cashout")
            elif "a conferir" in stt.lower():
                tags.add("a_conferir")
            elif stt:
                tags.add("aberta")
        out[caso] = sorted(tags)
    return out


# ── 1. todo bloco é lido ─────────────────────────────────────────────────────────────

def test_todo_bloco_com_stake_e_lido_pelo_servidor():
    nao_lidos = []
    for caso, lista in BLOCOS.items():
        for b in lista:
            stakes = _STAKE_LINHA.findall(b)
            if len(stakes) != 1:
                continue
            if R._financeiro_do_texto(b).get(_codigo(b)) is None:
                linha = next(l for l in b.split("\n") if l.startswith("Stake:"))
                nao_lidos.append(f"{caso}: {linha!r}")
    assert not nao_lidos, (f"{len(nao_lidos)} bloco(s) com `Stake:` que o servidor não lê "
                           f"(o gate de stake/odd/resultado não roda neles): {nao_lidos[:5]}")


# ── 2. resultado declarado × dinheiro ────────────────────────────────────────────────

def test_todo_resultado_declarado_bate_com_o_dinheiro():
    falhas, conferidos = [], 0
    for caso, lista in BLOCOS.items():
        for b in lista:
            info = R._financeiro_do_texto(b).get(_codigo(b))
            if not info:
                continue
            decl = T._resultado(info.get("status") or "")
            stake = T._num_bloco(info["stake"])
            if not decl or not stake:
                continue
            ret = R._retorno_do_bloco(info, stake)
            if ret is None:
                continue
            odd = T._num_bloco(info.get("odd_total")) or 0.0
            v, _ = R._veredito_do_retorno(stake, odd, ret, b, info.get("odd_total"),
                                          odd_bloco_manda=not info.get("sistema"))
            conferidos += 1
            if v != decl and not (decl == "W" and v == "HW"):
                falhas.append(f"{caso} {_codigo(b)}: declara {decl}, o dinheiro prova {v} "
                              f"(stake {stake}, retorno {ret}, odd {info.get('odd_total')})")
    assert conferidos > 700, conferidos     # o contrato precisa EXERCER, não só passar
    assert not falhas, "\n".join(falhas[:10])


# ── 3. "a conferir" nunca vira resultado ─────────────────────────────────────────────

def test_a_conferir_nunca_vira_resultado():
    vistos, errados = 0, []
    for caso, lista in BLOCOS.items():
        for b in lista:
            stt = _status(b, R._financeiro_do_texto(b).get(_codigo(b)))
            if "a conferir" not in stt.lower():
                continue
            vistos += 1
            if T._resultado(stt):
                errados.append(f"{caso}: {stt[:90]}")
    assert vistos >= 20
    assert not errados, errados
    # o caso real que abriu o item: as setas das sub-apostas estão DENTRO da mensagem
    assert T._resultado("result WIN · as 5 apostas não fecham o mesmo resultado "
                        "(Perdeu → L | Ganhou → W (retorno 58,59)) "
                        "(a conferir — não liquidar automaticamente)") == ""
    assert T._resultado("Ganhou → W (retorno 58,59)") == "W"


# ── 4. cobertura ────────────────────────────────────────────────────────────────────

def test_cobertura_por_casa_nao_regride():
    atual = cobertura(BLOCOS)
    novas = sorted(set(atual) - set(COBERTURA))
    assert not novas, (f"casa(s) nova(s) no harness sem cobertura declarada: {novas}. "
                       "Acrescente em tests/fixtures/contrato_liquidacao/cobertura.json o "
                       "que ela cobre (e o que falta vira dívida nomeada aqui).")
    perdas = {c: sorted(set(COBERTURA[c]) - set(atual.get(c, []))) for c in COBERTURA}
    perdas = {c: p for c, p in perdas.items() if p}
    assert not perdas, f"cenário que deixou de ser exercido no harness: {perdas}"


def test_toda_casa_tem_w_e_l_ou_esta_na_divida():
    atual = cobertura(BLOCOS)
    sem_l = sorted(c for c, t in atual.items() if "L" not in t)
    assert not sem_l, f"casa sem bloco de L no harness: {sem_l}"
    sem_w = {c for c, t in atual.items() if "W" not in t}
    fora = sorted(sem_w - SEM_W_NO_HARNESS)
    assert not fora, f"casa sem bloco de W no harness, fora da dívida nomeada: {fora}"
    pagas = sorted(SEM_W_NO_HARNESS - sem_w)
    assert not pagas, f"já têm W, tire de SEM_W_NO_HARNESS: {pagas}"


# ── os quatro consertos, por si ──────────────────────────────────────────────────────

def test_veredito_em_btc_nao_vira_void():
    # Shuffle, fixture do harness: 0,00123 BTC @ 1,88, retorno 0,0023124.
    assert R._veredito_do_retorno(0.00123, 1.88, 0.0023124, "", "1,88")[0] == "W"
    # e na escala do real nada muda: 2 centavos de folga em stake 20 continuam fechando W
    assert R._veredito_do_retorno(20.0, 1.95, 39.02, "", "1,95") == ("W", None)
    # cashout em BTC abaixo da stake é W, não V
    assert R._veredito_do_retorno(0.002, 0.0, 0.0015, "", None)[0] == "W"


def test_ficha_cashout_em_btc_nao_vira_void():
    # A Ficha real da DEX (a de `test_ficha.py`), com os valores em BTC.
    from test_ficha import _f
    d = ficha.derivar(_f(status="cashout", stake="0.002", retorno="0.0015"))
    assert (d["resultado"], d["odd"]) == ("W", "0,75")
    d = ficha.derivar(_f(status="cashout", stake="0.002", retorno="0.002"))
    assert d["resultado"] == "V"
    # na escala do real nada muda: meio centavo de folga, como sempre
    d = ficha.derivar(_f(status="cashout", stake="40", retorno="40.004"))
    assert d["resultado"] == "V"
    assert ficha._tol(Decimal("50")) == Decimal("0.005")


def test_stake_com_moeda_depois_e_lida():
    bloco = ("[Código: 309873189]\nStake: 30,00 USD\nOdd: 1,85\n"
             "Status: Ganhou → W (retorno 55,50 USD)\n")
    info = R._financeiro_do_texto(bloco)["309873189"]
    assert info["stake"] == "30,00"
    assert R._STAKE_TXT_RE.search("Stake: 12,50 USDT").group(1) == "12,50"
    assert R._STAKE_TXT_RE.search("Stake: R$ 12,50").group(1) == "12,50"
    # texto livre depois do número continua recusado (não é moeda)
    assert R._STAKE_TXT_RE.search("Stake: 12,50 por perna") is None


@pytest.mark.parametrize("caso", ["GoldenBet", "Jack", "MyStake"])
def test_familia_tv_entra_no_gate(caso):
    """O sufixo de moeda é o que a família TV imprime em conta fora do real."""
    lidos = [b for b in BLOCOS.get(caso, []) if R._financeiro_do_texto(b).get(_codigo(b))]
    assert lidos, f"{caso}: nenhum bloco lido pelo servidor"
