"""Caixa Inteligente na moeda da conta (s391, item 5 de `docs/PLANO_MOEDA_POR_CONTA.md`).

O caso: o Feca lançou os depósitos da Betpanda em USDT e a Caixa os leu como R$, somando-os a
apostas convertidas para R$. A conta nunca fechava. Decisão dele (03/10/2026): em conta USD/
USDT a caixa roda INTEIRA na moeda da conta — o saldo que se confere é o que a casa mostra.

Gates:
1. `_caixa_projetar` (pura), com mutação automática sobre uma cópia do `repository.py`:
   stake ORIGINAL nas apostas, aposta sem origem FORA (contada), lançamento de outra moeda
   FORA (contado), lançamento sem moeda = moeda da conta, conta BRL inalterada.
2. Tela: `tests/js/caixa_moeda_front.mjs` (mutação sobre cópia do `index.html`).
3. Forma: o INSERT grava a moeda (`test_caixa_lancar.py`) e as duas queries trazem
   `stake_orig`/`moeda` (`test_caixa.py`).

O que NÃO está coberto: a conversão pela cotação de hoje na `caixa_visao` (async, rede e
banco) e a montagem das telas — conferidas no navegador.
"""
import importlib.util
import os
import shutil
import subprocess
from decimal import Decimal
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
REPO = RAIZ / "app" / "repository.py"
INDEX = RAIZ / "app" / "static" / "index.html"
MJS = RAIZ / "tests" / "js" / "caixa_moeda_front.mjs"

MOVS = [
    {"id": 1, "tipo": "inicial", "data": "2026-10-01", "valor": 100.0, "abertas_corte": [], "criado_em": "1"},
    {"id": 2, "tipo": "deposito", "data": "2026-10-02", "valor": 50.0, "criado_em": "2"},
    # lançado quando a conta era de outra moeda: fora da caixa USDT
    {"id": 3, "tipo": "deposito", "data": "2026-10-02", "valor": 999.0, "moeda": "BRL", "criado_em": "3"},
]
APOSTAS = [
    # W: 25 USDT @2 → +25 USDT. Em R$ seria 130 de stake.
    {"id": 10, "stake": "130,00", "stake_orig": Decimal("25.00"), "moeda": "USDT", "odd": "2,00", "resultado": "W", "data": "02/10/2026"},
    # aberta: 10 USDT presos
    {"id": 11, "stake": "52,00", "stake_orig": Decimal("10.00"), "moeda": "USDT", "odd": "3,00", "resultado": "", "data": "03/10/2026"},
    # editada à mão: perdeu a origem, só tem R$
    {"id": 12, "stake": "40,00", "stake_orig": None, "moeda": None, "odd": "2,00", "resultado": "L", "data": "02/10/2026"},
]


def _falhas(mod) -> list[str]:
    f = []

    def chk(c, m):
        if not c:
            f.append(m)

    r = mod._caixa_projetar([dict(m) for m in MOVS], [dict(a) for a in APOSTAS], "USDT")
    chk(r["moeda"] == "USDT", "a projeção diz a moeda")
    chk(r["depositos"] == 50.0, f"só o depósito na moeda da conta entra (veio {r['depositos']})")
    chk(r["n_mov_outra_moeda"] == 1, "o lançamento de outra moeda é contado")
    chk(r["pl"] == 25.0, f"P/L pela stake ORIGINAL: 25 USDT @2 = +25 (veio {r['pl']})")
    chk(r["aberto"] == 10.0, f"em aberto pela stake ORIGINAL (veio {r['aberto']})")
    chk(r["n_sem_origem"] == 1, "a aposta sem origem é contada")
    chk(r["banca"] == 175.0 and r["disponivel"] == 165.0,
        f"banca 100+50+25 = 175, disponível 165 (veio {r['banca']} / {r['disponivel']})")

    b = mod._caixa_projetar([dict(m) for m in MOVS[:2]], [dict(a) for a in APOSTAS], "BRL")
    chk(b["pl"] == 130.0 - 40.0 and b["aberto"] == 52.0,
        f"conta BRL segue em R$: P/L 130 − 40 = 90, aberto 52 (veio {b['pl']} / {b['aberto']})")
    chk(b["n_sem_origem"] == 0, "conta BRL não descarta aposta nenhuma")
    s = mod._caixa_projetar([dict(m) for m in MOVS[:2]], [dict(a) for a in APOSTAS])
    chk(s["moeda"] == "BRL" and s["pl"] == 90.0, "sem moeda informada é BRL, como sempre")
    return f


def test_projecao_na_moeda_da_conta():
    import repository
    assert _falhas(repository) == []


MUTACOES_REPO = [
    ("a aposta usa a stake em R$", 'b["stake"] = f"{float(orig):.2f}".replace(".", ",")', 'b["stake"] = a.get("stake")'),
    ("a aposta sem origem entra como se fosse USDT", "            elif _num(a.get(\"stake\")) > 0:\n                n_sem_origem += 1",
     "            else:\n                convertidas.append(dict(a))"),
    ("o lançamento de outra moeda entra",
     "        movs = [m for m in movs if not (m.get(\"moeda\") and m.get(\"moeda\") != moeda)]", "        pass"),
    ("lançamento sem moeda fica de fora",
     'n_mov_outra = sum(1 for m in movs if m.get("moeda") and m.get("moeda") != moeda)',
     'n_mov_outra = sum(1 for m in movs if m.get("moeda") != moeda)'),
    ("a conta BRL também troca de stake", '    if moeda != "BRL":\n        convertidas = []', '    if True:\n        convertidas = []'),
]


@pytest.mark.parametrize("titulo,de,para", MUTACOES_REPO, ids=[m[0] for m in MUTACOES_REPO])
def test_mutacoes_da_projecao(tmp_path, titulo, de, para):
    src = REPO.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert src.count(de) == 1, f"âncora «{titulo}» não é única ({src.count(de)})"
    alvo = tmp_path / "repository_mutado.py"
    alvo.write_text(src.replace(de, para, 1), encoding="utf-8")
    spec = importlib.util.spec_from_file_location("repository_mutado", alvo)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert _falhas(mod), f"a mutação «{titulo}» passou despercebida"


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
def test_tela_por_execucao():
    r = subprocess.run(["node", str(MJS)], capture_output=True, text=True, encoding="utf-8", cwd=str(RAIZ))
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")


MUTACOES_TELA = [
    ("o saldo em USDT vira R$", "  if (f && f.pos) {", "  if (false) {"),
    ("o sinal descola do número", "    const num = s ? `<span><span class=\"money-sign\">${s}</span><span class=\"money-val\">${abs}</span></span>` : `<span class=\"money-val\">${abs}</span>`;",
     "    const num = `<span class=\"money-sign\">${s}</span><span class=\"money-val\">${abs}</span>`;"),
    ("o R$ muda de formato", "  const sg = s + (f ? f.pre : 'R$');", "  const sg = s + (f ? f.pre : 'BRL');"),
    ("a conta USDT soma o valor cru", "  const v = cx[k + '_brl'];", "  const v = cx[k];"),
    ("sem cotação vira zero na soma", "  return (v == null) ? null : v;", "  return (v == null) ? 0 : v;"),
    ("o texto ignora a moeda", "  if (moeda && _MOEDA_ORIG[moeda]) return fmtMoedaOrig(n, moeda);\n", ""),
    # s392: a ativação diz a moeda da conta e, em R$, onde trocá-la.
    ("a ativação manda trocar a moeda de toda conta", "  return sg === 'R$'\n", "  return true\n"),
    ("a ativação de conta em R$ não aponta onde trocar",
     "troque a moeda na edição da conta antes de ativar.", "confira o saldo."),
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
