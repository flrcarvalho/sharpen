"""Caixa Inteligente da Polymarket (s397) — a conta, a leitura da carteira e a tela.

A Caixa da Polymarket é AUTOMÁTICA: depósitos, saques e ajustes vêm do extrato da
própria Polymarket (`/v2/activity` com depósito e saque incluídos, s398), e o saldo
observado é o da blockchain (+ o que já ganhou e não foi resgatado). Na carteira do Feca, em 06/10/2026, ela achou no 1º uso
US$ 260,42 de mercado anulado gravado como vitória (conserto em `test_polymarket.py`) e,
corrigido isso, fecha em US$ 0,13 — arredondamento de centavos.

Cobre, sem rede e sem banco:
1. `_caixa_movimentos`: DEPOSIT = depósito, WITHDRAWAL = saque, rebate = ajuste; aposta,
   resgate e conversão não viram nada;
2. `_caixa_trava`: o extrato inteiro, cada linha com o seu sinal, tem de dar o saldo
   on-chain, senão a Caixa não confere (um depósito faltando não fecha);
3. `_a_resgatar`, `coletar_sync` (falha da Caixa NÃO derruba o sync das apostas);
4. `_caixa_tol`/`_caixa_projetar`: a margem de arredondamento vale SÓ na Polymarket;
5. a tela, por execução (`tests/js/caixa_polymarket_front.mjs`), e mutações dos dois lados.

NÃO cobre: a gravação (`caixa_polymarket_sync`) toca o Postgres — foi ensaiada contra a
base real dentro de uma transação desfeita (ROLLBACK) em 06/10/2026: 9 lançamentos, o
2º sync sem duplicar nada, estado `confere`. E a API de verdade (rede): a s398 rodou a
coleta contra a carteira do Feca, 872 linhas, trava com diferença US$ 0,0000.
"""
import asyncio
import importlib.util
import os
import shutil
import subprocess
from pathlib import Path

import pytest

import polymarket

RAIZ = Path(__file__).resolve().parent.parent
POLY = RAIZ / "app" / "polymarket.py"
REPO = RAIZ / "app" / "repository.py"
INDEX = RAIZ / "app" / "static" / "index.html"
MJS = RAIZ / "tests" / "js" / "caixa_polymarket_front.mjs"

W = "0x2b3cf54201a00def81ec5d840da7d58fc37e9f22"
FORA = "0x1111111111111111111111111111111111111111"
ZERO = "0x0000000000000000000000000000000000000000"


def _ex(h, tipo, valor, lado="", ts=1778000000):
    """Uma linha do `/v2/activity`, com os campos em snake_case como a API devolve."""
    return {"transaction_hash": h, "type": tipo, "usdc_size": valor, "side": lado,
            "timestamp": ts, "proxy_wallet": W}


EXTRATO = [
    _ex("0xDEP", "DEPOSIT", 281.82),                        # depósito
    _ex("0xbuy", "TRADE", 25.0, "BUY"),                     # compra: aposta
    _ex("0xred", "REDEEM", 50.0),                           # resgate: aposta
    _ex("0xreb", "TAKER_REBATE", 2.88, ts=1783000000),     # rebate: ajuste
    _ex("0xsell", "TRADE", 10.0, "SELL"),                   # venda: aposta
    _ex("0xconv", "CONVERSION", 499.99),                    # USDC.e → pUSD: não muda o saldo
    _ex("0xsplit", "SPLIT", 5.0),                           # split: sai dinheiro
    _ex("0xmerge", "MERGE", 5.0),                           # merge: volta
    _ex("0xsaq", "WITHDRAWAL", 100.0, ts=1791200000),       # saque
]
SALDO = 281.82 - 25.0 + 50.0 + 2.88 + 10.0 - 5.0 + 5.0 - 100.0
MOVS_ESPERADOS = {
    "0xdep": ("deposito", 281.82),
    "0xreb": ("ajuste", 2.88),
    "0xsaq": ("saque", 100.0),
}


def test_movimentos_so_deposito_saque_e_ajuste():
    movs = polymarket._caixa_movimentos(EXTRATO)
    por = {m["ref"]: (m["tipo"], m["valor"]) for m in movs}
    assert por == MOVS_ESPERADOS
    rebate = next(m for m in movs if m["ref"] == "0xreb")
    assert "Taker Rebate" in rebate["obs"]
    dep = next(m for m in movs if m["ref"] == "0xdep")
    assert dep["data"] == polymarket._iso_brt(1778000000)
    assert [m["ref"] for m in movs] == ["0xdep", "0xreb", "0xsaq"]   # em ordem de data


def test_trava_fecha_e_nao_fecha():
    t = polymarket._caixa_trava(EXTRATO, SALDO)
    assert t["ok"] and abs(t["diferenca"]) < 1e-9 and t["linhas"] == len(EXTRATO)
    # Um depósito fora do extrato: a soma não fecha e a Caixa não confere.
    sem_deposito = [a for a in EXTRATO if a["type"] != "DEPOSIT"]
    t2 = polymarket._caixa_trava(sem_deposito, SALDO)
    assert not t2["ok"] and abs(t2["diferenca"] - 281.82) < 0.01
    # Tipo que ninguém cadastrou conta zero, e se ele movia dinheiro a trava acusa.
    estranho = EXTRATO + [_ex("0xnovo", "TIPO_NOVO", 7.0)]
    assert not polymarket._caixa_trava(estranho, SALDO + 7.0)["ok"]


def test_a_resgatar_soma_simples_e_combo_ganha():
    pos = [{"redeemable": True, "curPrice": 1.0, "currentValue": 80.0},
           {"redeemable": True, "curPrice": 0.0, "currentValue": 0.0},
           {"redeemable": False, "curPrice": 0.5, "currentValue": 30.0}]          # aberta: não
    combos = [{"status": "RESOLVED_WIN", "shares_balance": "125"},
              {"status": "OPEN", "shares_balance": "999"}]
    assert polymarket._a_resgatar(pos, combos) == 205.0


def test_falha_da_caixa_nao_derruba_o_sync(monkeypatch):
    async def coletar(client, wallet, parceiro):
        return [{"codigo_bilhete": "R"}], [{"codigo_bilhete": "A"}], {"activity": [], "positions": [], "combos": []}

    async def caixa(client, wallet, bruto):
        raise RuntimeError("extrato fora do ar")

    monkeypatch.setattr(polymarket, "_coletar", coletar)
    monkeypatch.setattr(polymarket, "coletar_caixa", caixa)
    res, atv, cx = asyncio.run(polymarket.coletar_sync("0xW", "P"))
    assert res == [{"codigo_bilhete": "R"}] and atv == [{"codigo_bilhete": "A"}]
    assert "extrato fora do ar" in cx["erro"]


# ── a projeção: a margem de arredondamento é SÓ da Polymarket ─────────────────

MOVS = [
    {"id": 1, "tipo": "inicial", "data": "2026-05-06", "valor": 0.0, "abertas_corte": [], "criado_em": "1"},
    {"id": 2, "tipo": "deposito", "data": "2026-05-06", "valor": 100.0, "criado_em": "2"},
]


def _apostas(n):
    # n apostas perdidas de US$ 1 → disponível 100 − n
    return [{"id": 10 + i, "stake": "5,00", "stake_orig": 1.0, "moeda": "USD", "odd": "2,00",
             "resultado": "L", "data": "07/05/2026"} for i in range(n)]


def _proj(mod, casa, observado, n=400):
    movs = [dict(m) for m in MOVS]
    movs.append({"id": 3, "tipo": "conferencia", "data": "2026-10-06", "valor": observado,
                 "projetado": 100.0 - n, "criado_em": "3"})
    return mod._caixa_projetar(movs, _apostas(n), "USD", casa)


def _falhas_proj(mod) -> list[str]:
    f = []
    # 400 apostas → margem 1,25 centavo × 20 = US$ 0,25
    a = _proj(mod, "Polymarket", 100.0 - 400 + 0.13)
    if a["estado"] != "confere" or a["tolerancia"] != 0.25:
        f.append(f"Polymarket com 0,13 de arredondamento devia conferir (veio {a['estado']}, tol {a['tolerancia']})")
    b = _proj(mod, "Polymarket", 100.0 - 400 + 0.40)
    if b["estado"] != "divergente":
        f.append(f"Polymarket com 0,40 (acima da margem) devia divergir (veio {b['estado']})")
    c = _proj(mod, "Betano", 100.0 - 400 + 0.13)
    if c["estado"] != "divergente" or c["tolerancia"] != 0.0:
        f.append(f"Betano não tem margem: 0,13 diverge (veio {c['estado']}, tol {c['tolerancia']})")
    d = _proj(mod, "Polymarket", 100.0 - 400 - 260.42)
    if d["estado"] != "divergente":
        f.append("o anulado de US$ 260,42 tem de divergir")
    return f


def test_tolerancia_so_na_polymarket():
    import repository
    assert _falhas_proj(repository) == []


MUTACOES_REPO = [
    ("a margem vale para toda casa", '    if casa == "Polymarket":\n        return max(', '    if True:\n        return max('),
    ("a margem cresce com n e não com √n", "0.0125 * (max(n_apostas, 0) ** 0.5)", "0.0125 * max(n_apostas, 0)"),
    ("a projeção ignora a margem", "    if div is None or abs(div) < tol:", "    if div is None or abs(div) < CAIXA_TOL:"),
]


def _carrega(src_path, nome, de, para, tmp_path):
    src = src_path.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert src.count(de) == 1, f"âncora «{nome}» não é única ({src.count(de)})"
    alvo = tmp_path / (src_path.stem + "_mutado.py")
    alvo.write_text(src.replace(de, para, 1), encoding="utf-8")
    spec = importlib.util.spec_from_file_location(src_path.stem + "_mutado", alvo)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize("titulo,de,para", MUTACOES_REPO, ids=[m[0] for m in MUTACOES_REPO])
def test_mutacoes_da_projecao(tmp_path, titulo, de, para):
    assert _falhas_proj(_carrega(REPO, titulo, de, para, tmp_path)), f"«{titulo}» passou despercebida"


def _falhas_coletor(mod) -> list[str]:
    f = []
    try:
        movs = mod._caixa_movimentos(EXTRATO)
        por = {m["ref"]: (m["tipo"], m["valor"]) for m in movs}
        if por != MOVS_ESPERADOS:
            f.append(f"movimentos errados: {por}")
        if not mod._caixa_trava(EXTRATO, SALDO)["ok"]:
            f.append("trava não fechou com o extrato completo")
        if mod._caixa_trava([a for a in EXTRATO if a["type"] != "DEPOSIT"], SALDO)["ok"]:
            f.append("trava fechou sem o depósito")
    except Exception as exc:  # noqa: BLE001
        f.append(f"quebrou: {exc}")
    return f


MUTACOES_COLETOR = [
    ("rebate vira depósito", "            tipo, obs = \"ajuste\", f\"{tipo_at.replace('_', ' ').title()} (Polymarket)\"",
     '            tipo, obs = "deposito", "x"'),
    ("o saque vira depósito", '            tipo, obs = "saque", "Saída da carteira"', '            tipo, obs = "deposito", "x"'),
    ("aposta vira movimento",
     '        if tipo_at not in ("DEPOSIT", "WITHDRAWAL") and tipo_at not in _AJUSTE_POR_TIPO:\n            continue\n', ""),
    ("o hash perde a caixa", '        h = str(a.get("transaction_hash") or "").lower()', '        h = str(a.get("transaction_hash") or "")'),
    ("a compra entra somando", '        return -u if lado == "BUY" else u', '        return u'),
    ("o saque soma no saldo", '_SINAL_EXTRATO = {"DEPOSIT": 1, "WITHDRAWAL": -1,', '_SINAL_EXTRATO = {"DEPOSIT": 1, "WITHDRAWAL": 1,'),
    ("a conversão conta como entrada", '"CONVERSION": 0,', '"CONVERSION": 1,'),
    ("o split não tira dinheiro", '"SPLIT": -1,', '"SPLIT": 0,'),
    ("a trava aceita qualquer coisa", '    return {"ok": abs(diferenca) <= _TRAVA_TOL,', '    return {"ok": True,'),
]


@pytest.mark.parametrize("titulo,de,para", MUTACOES_COLETOR, ids=[m[0] for m in MUTACOES_COLETOR])
def test_mutacoes_do_coletor(tmp_path, titulo, de, para):
    assert _falhas_coletor(_carrega(POLY, titulo, de, para, tmp_path)), f"«{titulo}» passou despercebida"


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
def test_tela_por_execucao():
    r = subprocess.run(["node", str(MJS)], capture_output=True, text=True, encoding="utf-8", cwd=str(RAIZ))
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")


MUTACOES_TELA = [
    ("a Polymarket volta a ficar de fora", "  const fora = !parceiroSelecionado;", "  const fora = !parceiroSelecionado || casaSelecionada === 'Polymarket';"),
    ("a Polymarket ganha o Ativar", "  if (!d.ligada && poly) {", "  if (false) {"),
    ("o saldo inicial fica editável", "  let corpo = poly\n", "  let corpo = false\n"),
    ("volta o campo de conferência", "  const conf = poly\n", "  const conf = false\n"),
    ("voltam + Depósito e − Saque", "    + (poly ? '' : '<button", "    + (false ? '' : '<button"),
    ("o arredondamento vira zero", "  if (d.estado === 'confere' && d.tolerancia && c.divergencia)", "  if (false)"),
    ("o sync não recarrega a Caixa", "    carregarCaixa();   // s397", "    // s397"),
]


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
@pytest.mark.parametrize("titulo,de,para", MUTACOES_TELA, ids=[m[0] for m in MUTACOES_TELA])
def test_mutacoes_da_tela(tmp_path, titulo, de, para):
    src = INDEX.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert src.count(de) == 1, f"âncora «{titulo}» não é única ({src.count(de)})"
    alvo = tmp_path / "index.html"
    alvo.write_text(src.replace(de, para, 1), encoding="utf-8")
    r = subprocess.run(["node", str(MJS)], capture_output=True, text=True, encoding="utf-8",
                       cwd=str(RAIZ), env={**os.environ, "ALVO_INDEX": str(alvo)})
    assert r.returncode != 0, f"a mutação «{titulo}» passou despercebida"
