"""Valor na moeda original da conta, na tela (s391, passo 3 de `docs/PLANO_MOEDA_POR_CONTA.md`).

Decisões do Feca (03/10/2026): o formato é "US$ 1.234,50" e "1.234,50 USDT"; o seletor
R$ / moeda da conta fica SÓ na grade da Extração (lá a conta é uma só, e a coluna inteira
troca de moeda sem misturar nada); a Base Completa mostra só a sub-linha; e a stake
editada à mão LIMPA a origem.

Gates:

1. **Funções puras do `repository.py`** (este arquivo, mutação automática sobre uma cópia
   do módulo): `_pl_na_moeda_original` (o P/L sai do `calcular_pl` aplicado à
   `stake_orig`, nunca de `pl ÷ cotacao`) e `_limpa_origem` (só quando o NÚMERO da stake
   muda: o modal reenvia todos os campos).
2. **Front** (`tests/js/moeda_grade_front.mjs`, mutação automática sobre cópias do
   `index.html`, `app.js` e `apostas.js`).
3. **Banco** (`test_repository_db.py::test_moeda_original_no_feed_e_a_edicao_que_limpa`,
   só no CI): o feed leva a origem só nas linhas convertidas, e o UPDATE limpa de fato.

O que NÃO está coberto: o visual (medição no navegador) e o `renderGrade` inteiro.
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
MJS = RAIZ / "tests" / "js" / "moeda_grade_front.mjs"
DASH = RAIZ / "app" / "static" / "dash" / "assets" / "js"
ARQS = {
    "index": RAIZ / "app" / "static" / "index.html",
    "app": DASH / "app.js",
    "apostas": DASH / "charts" / "apostas.js",
}


# ── Funções puras do repositório ─────────────────────────────────────────────

def _falhas_repo(mod) -> list[str]:
    f = []

    def chk(cond, msg):
        if not cond:
            f.append(msg)

    pl = mod._pl_na_moeda_original
    usdt = {"moeda": "USDT", "stake_orig": Decimal("25.00"), "odd": "5,03", "resultado": "W"}
    chk(pl(usdt) == 100.75, "W: 25 × (5,03 − 1)")
    chk(pl({**usdt, "resultado": "L"}) == -25.0, "L: −stake original")
    chk(pl({**usdt, "resultado": "V"}) == 0.0, "V: zero")
    chk(pl({**usdt, "resultado": ""}) is None, "aberta: sem P/L")
    chk(pl({**usdt, "moeda": None}) is None, "sem moeda: sem P/L original")
    chk(pl({**usdt, "stake_orig": None}) is None, "sem stake original: sem P/L original")
    # A régua é a da stake ORIGINAL, não a do R$ dividido. 1,00 US$ a 5,0049 grava a stake
    # como R$ 5,00 (arredondada ao centavo). W @ 101: o certo é 100,00 US$; pelo R$
    # dividido sairia 500,00 ÷ 5,0049 = 99,90. O erro do arredondamento cresce com a odd.
    chk(pl({"moeda": "USD", "stake_orig": Decimal("1.00"), "odd": "101,00", "resultado": "W",
            "stake": "5,00", "cotacao": Decimal("5.0049")}) == 100.0,
        "P/L sai da stake original, nunca do R$ ÷ cotação")

    lo = mod._limpa_origem
    chk(lo({"stake": "130,00"}, {"stake": "150,00"}) is True, "stake mudou: limpa")
    chk(lo({"stake": "130,00"}, {"stake": "130"}) is False, "mesmo número noutra grafia: mantém")
    chk(lo({"stake": "130,00"}, {"stake": "130,00"}) is False, "mesma stake reenviada: mantém")
    chk(lo({"stake": "130,00"}, {"odd": "2,00"}) is False, "edição sem stake: mantém")
    chk(lo(None, {"stake": "130,00"}) is True, "sem snapshot: limpa")
    return f


def test_funcoes_puras_do_repositorio():
    import repository
    assert _falhas_repo(repository) == []


MUTACOES_REPO = [
    ("o P/L original vira R$ ÷ cotação",
     '    return calcular_pl(f"{float(orig):.2f}".replace(".", ","), d.get("odd"), d.get("resultado"))',
     '    _p = calcular_pl(d.get("stake"), d.get("odd"), d.get("resultado"))\n'
     '    return None if _p is None else round(_p / float(d.get("cotacao") or 1), 2)'),
    ("o P/L original ignora a falta de moeda",
     '    if orig is None or not d.get("moeda"):', '    if orig is None:'),
    ("a edição limpa a origem mesmo sem mudar o número",
     '    return _num_or_none(antes["stake"]) != _num_or_none(safe["stake"])', '    return True'),
    ("a edição compara a grafia em vez do número",
     '    return _num_or_none(antes["stake"]) != _num_or_none(safe["stake"])',
     '    return (antes["stake"] or "") != (safe["stake"] or "")'),
    ("a edição nunca limpa a origem",
     '    if "stake" not in safe:\n        return False', '    if True:\n        return False'),
    ("sem snapshot a origem fica",
     '    if antes is None:\n        return True', '    if antes is None:\n        return False'),
]


@pytest.mark.parametrize("titulo,de,para", MUTACOES_REPO, ids=[m[0] for m in MUTACOES_REPO])
def test_mutacoes_do_repositorio_sao_detectadas(tmp_path, titulo, de, para):
    src = REPO.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert src.count(de) == 1, f"âncora da mutação «{titulo}» não é única no repository.py"
    alvo = tmp_path / "repository_mutado.py"
    alvo.write_text(src.replace(de, para, 1), encoding="utf-8")
    spec = importlib.util.spec_from_file_location("repository_mutado", alvo)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert _falhas_repo(mod), f"a mutação «{titulo}» passou despercebida"


def test_a_edicao_usa_a_regra_e_o_feed_leva_a_origem():
    """Presença: a regra pura tem de ser a que o UPDATE e o feed chamam."""
    src = REPO.read_text(encoding="utf-8")
    assert 'if _limpa_origem(antes, safe):\n' in src.replace("\r\n", "\n")
    assert 'd["pl_orig"] = _pl_na_moeda_original(d)' in src
    assert 'linha["stake_orig"] = float(r["stake_orig"])' in src


# ── Front ────────────────────────────────────────────────────────────────────

@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
def test_front_por_execucao():
    r = subprocess.run(["node", str(MJS)], capture_output=True, text=True,
                       encoding="utf-8", cwd=str(RAIZ))
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")


MUTACOES_FRONT = [
    ("o dólar perde o US$", "index",
     "const _MOEDA_ORIG = { USD: { pre: 'US$' }, USDT: { pos: 'USDT' } };",
     "const _MOEDA_ORIG = { USD: { pre: '$' }, USDT: { pos: 'USDT' } };"),
    ("o USDT vira prefixo", "index",
     "  return f.pre ? `${sinal}${f.pre} ${t}` : `${sinal}${t} ${f.pos}`;",
     "  return f.pre ? `${sinal}${f.pre} ${t}` : `${sinal}${f.pos} ${t}`;"),
    ("o milhar some (toFixed, como o fmtUSD)", "index",
     "  return Math.abs(Number(n)).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });",
     "  return Math.abs(Number(n)).toFixed(2).replace('.', ',');"),
    ("a stake convertida volta a ser editável no modo moeda da conta", "index",
     '    return `<div class="btbl-cell btbl-num" title="Para editar a stake, volte a ver em R$">',
     '    return `<div class="btbl-cell btbl-num" data-field="stake" title="Para editar a stake, volte a ver em R$">'),
    ("a sub-linha some no modo R$", "index",
     "    const txt = _grVer === 'orig' ? (b.stake ? 'R$ ' + b.stake : '') : fmtMoedaOrig(b.stake_orig, b.moeda);",
     "    const txt = _grVer === 'orig' ? (b.stake ? 'R$ ' + b.stake : '') : '';"),
    ("o P/L não troca de moeda", "index",
     "  if (_grVer === 'orig' && _temOrig(b)) return b.pl_orig != null ? moneyOrig(b.pl_orig, b.moeda, true) : fmtPL(null);",
     "  if (false) return null;"),
    ("o P/L original perde a cor", "index",
     "  const cls = pl ? (n > 0 ? ' pos' : (n < 0 ? ' neg' : '')) : '';",
     "  const cls = '';"),
    ("o zero ganha sinal", "index",
     "  const sinal = pl ? (n > 0 ? '+' : (n < 0 ? '−' : '')) : '';",
     "  const sinal = pl ? (n >= 0 ? '+' : '−') : '';"),
    ("o sinal do USDT descola do número", "index",
     "${sinal ? `<span><span class=\"money-sign\">${sinal}</span>${val}</span>` : val}",
     "${sinal ? `<span class=\"money-sign\">${sinal}</span>` : ''}${val}"),
    ("conta em real não volta a ver em R$", "index",
     "  if (!tem) _grVer = 'BRL';\n", ""),
    ("o seletor aparece em toda conta", "index",
     "  if (box) box.hidden = !tem;", "  if (box) box.hidden = false;"),
    ("o cabeçalho não diz a moeda", "index",
     "  const suf = _grVer === 'orig' ? ' · ' + m : '';", "  const suf = '';"),
    ("o dashboard escreve diferente da grade", "app",
     "const _MOEDA_ORIG={USD:{pre:'US$'},USDT:{pos:'USDT'}};",
     "const _MOEDA_ORIG={USD:{pre:'USD'},USDT:{pos:'USDT'}};"),
    ("a Base Completa perde a sub-linha", "apostas",
     "${fmtR(r.stake)}${r.stake_orig!=null&&fmtMoedaOrig(r.stake_orig,r.moeda)?",
     "${fmtR(r.stake)}${false&&fmtMoedaOrig(r.stake_orig,r.moeda)?"),
]


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
@pytest.mark.parametrize("titulo,arq,de,para", MUTACOES_FRONT, ids=[m[0] for m in MUTACOES_FRONT])
def test_mutacoes_do_front_sao_detectadas(tmp_path, titulo, arq, de, para):
    alvo = ARQS[arq]
    src = alvo.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert src.count(de) == 1, f"âncora da mutação «{titulo}» não é única no {alvo.name} ({src.count(de)})"
    estragado = tmp_path / alvo.name
    estragado.write_text(src.replace(de, para, 1), encoding="utf-8")
    env = {**os.environ, f"ALVO_{arq.upper()}": str(estragado)}
    r = subprocess.run(["node", str(MJS)], capture_output=True, text=True,
                       encoding="utf-8", cwd=str(RAIZ), env=env)
    assert r.returncode != 0, f"a mutação «{titulo}» passou despercebida\n" + (r.stdout or "")
