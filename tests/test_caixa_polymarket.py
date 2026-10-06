"""Caixa Inteligente da Polymarket (s397) — a conta, a leitura da carteira e a tela.

A Caixa da Polymarket é AUTOMÁTICA: depósitos, saques e ajustes vêm das transferências
de pUSD/USDC.e que NÃO são aposta, e o saldo observado é o da blockchain (+ o que já
ganhou e não foi resgatado). Na carteira do Feca, em 06/10/2026, ela achou no 1º uso
US$ 260,42 de mercado anulado gravado como vitória (conserto em `test_polymarket.py`) e,
corrigido isso, fecha em US$ 0,13 — arredondamento de centavos.

Cobre, sem rede e sem banco:
1. `_caixa_movimentos`: o hash decide aposta × caixa; rebate vira ajuste; a conversão
   USDC.e → pUSD (líquido zero) não vira nada; entrada = depósito, saída = saque;
2. `_caixa_trava`: a lista do Blockscout + as apostas que ela não listou têm de dar o
   saldo on-chain, senão a Caixa não confere;
3. `_a_resgatar`, `coletar_sync` (falha da Caixa NÃO derruba o sync das apostas);
4. `_caixa_tol`/`_caixa_projetar`: a margem de arredondamento vale SÓ na Polymarket;
5. a tela, por execução (`tests/js/caixa_polymarket_front.mjs`), e mutações dos dois lados.

NÃO cobre: a gravação (`caixa_polymarket_sync`) toca o Postgres — foi ensaiada contra a
base real dentro de uma transação desfeita (ROLLBACK) em 06/10/2026: 9 lançamentos, o
2º sync sem duplicar nada, estado `confere`. E o Blockscout de verdade (rede).
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


def _tr(h, de, para, valor, token="PUSD", ts="1778000000"):
    return {"hash": h, "from": de, "to": para, "value": str(int(round(valor * 1e6))),
            "tokenDecimal": "6", "tokenSymbol": token, "timeStamp": ts}


TRANSFERS = [
    _tr("0xdep", ZERO, W, 281.82),                         # depósito (pUSD cunhado na carteira)
    _tr("0xbuy", W, FORA, 25.0),                           # compra: aposta
    _tr("0xred", ZERO, W, 50.0),                           # resgate: aposta
    _tr("0xreb", FORA, W, 2.88),                           # rebate: ajuste
    _tr("0xusdc", FORA, W, 499.99, "USDC.E", "1791200000"),  # depósito em USDC.e
    _tr("0xwrap", W, FORA, 499.99, "USDC.E", "1791200500"),  # … convertido em pUSD:
    _tr("0xwrap", ZERO, W, 499.99, "PUSD", "1791200500"),    #   líquido zero na mesma tx
    _tr("0xcombo", W, FORA, 26.0),                         # compra de combo: aposta
    _tr("0xsaq", W, FORA, 100.0),                          # saque
]
ACTIVITY = [
    {"type": "TRADE", "side": "BUY", "transactionHash": "0xbuy", "usdcSize": 25.0},
    {"type": "REDEEM", "transactionHash": "0xred", "usdcSize": 50.0},
    {"type": "TAKER_REBATE", "transactionHash": "0xreb", "usdcSize": 2.88},
]
COMBO_ATIV = [{"type": "SPLIT", "tx_hash": "0xcombo"}]


def test_movimentos_o_hash_decide_aposta_ou_caixa():
    movs = polymarket._caixa_movimentos(TRANSFERS, ACTIVITY, COMBO_ATIV, W)
    por = {m["ref"]: (m["tipo"], m["valor"]) for m in movs}
    assert por == {
        "0xdep": ("deposito", 281.82),
        "0xreb": ("ajuste", 2.88),
        "0xusdc": ("deposito", 499.99),
        "0xsaq": ("saque", 100.0),
    }
    rebate = next(m for m in movs if m["ref"] == "0xreb")
    assert "Taker Rebate" in rebate["obs"]
    dep = next(m for m in movs if m["ref"] == "0xdep")
    assert dep["data"] == polymarket._iso_brt(1778000000)


def test_trava_fecha_e_nao_fecha():
    # Saldo real = tudo o que se moveu. O Blockscout PERDEU o resgate 0xred (como os 5
    # resgates grandes da carteira do Feca); o /activity sabe que ele valeu 50.
    sem_resgate = [t for t in TRANSFERS if t["hash"] != "0xred"]
    saldo = 281.82 - 25.0 + 50.0 + 2.88 + 499.99 - 499.99 + 499.99 - 26.0 - 100.0
    t = polymarket._caixa_trava(sem_resgate, ACTIVITY, W, saldo)
    assert t["ok"] and abs(t["faltou_listar"] - 50.0) < 1e-9
    # Se o que ele perdeu fosse um DEPÓSITO, a soma não fecha: a Caixa não confere.
    sem_deposito = [t for t in TRANSFERS if t["hash"] != "0xdep"]
    t2 = polymarket._caixa_trava(sem_deposito, ACTIVITY, W, saldo)
    assert not t2["ok"] and abs(t2["diferenca"] - 281.82) < 0.01


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
        raise RuntimeError("Blockscout fora do ar")

    monkeypatch.setattr(polymarket, "_coletar", coletar)
    monkeypatch.setattr(polymarket, "coletar_caixa", caixa)
    res, atv, cx = asyncio.run(polymarket.coletar_sync("0xW", "P"))
    assert res == [{"codigo_bilhete": "R"}] and atv == [{"codigo_bilhete": "A"}]
    assert "Blockscout fora do ar" in cx["erro"]


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
        movs = mod._caixa_movimentos(TRANSFERS, ACTIVITY, COMBO_ATIV, W)
        por = {m["ref"]: (m["tipo"], m["valor"]) for m in movs}
        if por != {"0xdep": ("deposito", 281.82), "0xreb": ("ajuste", 2.88),
                   "0xusdc": ("deposito", 499.99), "0xsaq": ("saque", 100.0)}:
            f.append(f"movimentos errados: {por}")
        sem_dep = [t for t in TRANSFERS if t["hash"] != "0xdep"]
        saldo = 281.82 - 25.0 + 50.0 + 2.88 + 499.99 - 26.0 - 100.0
        if mod._caixa_trava(sem_dep, ACTIVITY, W, saldo)["ok"]:
            f.append("trava fechou sem o depósito")
        if not mod._caixa_trava([t for t in TRANSFERS if t["hash"] != "0xred"], ACTIVITY, W, saldo)["ok"]:
            f.append("trava não fechou com o resgate perdido pelo Blockscout")
    except Exception as exc:  # noqa: BLE001
        f.append(f"quebrou: {exc}")
    return f


MUTACOES_COLETOR = [
    ("compra de combo vira saque", '    aposta |= {str(a.get("tx_hash") or "").lower() for a in combo_atividade}\n', ""),
    ("rebate vira depósito", '            tipo, obs, valor_mov = "ajuste", f"{tipo_at.replace(\'_\', \' \').title()} (Polymarket)", valor',
     '            tipo, obs, valor_mov = "deposito", "x", valor'),
    ("a conversão vira dois movimentos", '        liquido[h] = liquido.get(h, 0.0) + v', '        liquido[h + str(v > 0)] = liquido.get(h + str(v > 0), 0.0) + v'),
    ("o sinal da saída se perde", '        if str(t.get("from") or "").lower() == wallet:\n            v = -v\n        liquido', '        liquido'),
    ("a trava não completa com a activity", '    faltou = sum(v for h, v in _fluxo_da_atividade(activity).items() if h not in hashes)', '    faltou = 0.0'),
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
