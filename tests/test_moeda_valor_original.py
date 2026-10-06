"""Valor na moeda original da conta, na tela (s391, passo 3 de `docs/PLANO_MOEDA_POR_CONTA.md`).

Decisões do Feca (03/10/2026): o formato é "US$ 1.234,50" e "1.234,50 USDT"; o seletor
R$ / moeda da conta fica SÓ na grade da Extração (lá a conta é uma só, e a coluna inteira
troca de moeda sem misturar nada); a Base Completa mostra só a sub-linha; e a stake
editada à mão LIMPAVA a origem. **s398 (passo 6.1):** a verdade passou a ser a moeda da
conta, e a edição RECALCULA a origem pela cotação gravada em vez de apagá-la.

Gates:

1. **Funções puras do `repository.py`** (este arquivo, mutação automática sobre uma cópia
   do módulo): `_pl_na_moeda_original` (o P/L sai do `calcular_pl` aplicado à
   `stake_orig`, nunca de `pl ÷ cotacao`) e `_origem_pos_edicao` (s398: a stake em R$
   editada refaz a `stake_orig` pela cotação da linha, a digitada na moeda refaz o R$, e
   nada muda quando o NÚMERO não muda, porque o modal reenvia todos os campos).
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

    def op(*a):
        # Erro também é falha: mutação que divide por cotação nula levanta, não devolve.
        try:
            return mod._origem_pos_edicao(*a)
        except Exception as e:
            return ("erro", repr(e))
    conv = {"stake": "130,00", "moeda": "USDT", "cotacao": Decimal("5.200000")}
    real = {"stake": "130,00", "moeda": None, "cotacao": None}
    chk(op(conv, {"stake": "156,00"}) == {"stake_orig": 30.0},
        "stake em R$ mudou: a origem é refeita pela cotação da linha (156 ÷ 5,2)")
    chk(op(conv, {"stake": "130"}) == {}, "mesmo número noutra grafia: nada muda")
    chk(op(conv, {"stake": "130,00"}) == {}, "mesma stake reenviada: nada muda")
    chk(op(conv, {"odd": "2,00"}) == {}, "edição sem stake: nada muda")
    chk(op(real, {"stake": "150,00"}) == {}, "linha em real: não inventa origem")
    chk(op(None, {"stake": "130,00"}) == {"limpa": True}, "sem snapshot: limpa")
    chk(op(conv, {}, "30,00") == {"stake": "156,00", "stake_orig": 30.0},
        "stake na moeda: o R$ sai da cotação da linha (30 × 5,2)")
    chk(op(conv, {"stake": "999,00"}, "30,00").get("stake") == "156,00",
        "stake na moeda manda sobre o R$ do mesmo envio")
    chk(op(real, {}, "30,00") == {"recusa": True},
        "stake na moeda em linha sem cotação: recusa, nunca grava USDT como R$")
    chk(op(conv, {}, "0") == {"recusa": True}, "stake na moeda zero: recusa")
    return f


def test_funcoes_puras_do_repositorio():
    import repository
    assert _falhas_repo(repository) == []


MUTACOES_REPO = [
    ("o P/L original vira R$ ÷ cotação",
     # s392: a chamada ganhou a freebet na moeda original (`_freebet_na_origem`).
     '    return calcular_pl(f"{float(orig):.2f}".replace(".", ","), d.get("odd"), d.get("resultado"),\n'
     '                       _freebet_na_origem(d))',
     '    _p = calcular_pl(d.get("stake"), d.get("odd"), d.get("resultado"))\n'
     '    return None if _p is None else round(_p / float(d.get("cotacao") or 1), 2)'),
    ("o P/L original ignora a falta de moeda",
     '    if orig is None or not d.get("moeda"):', '    if orig is None:'),
    ("a edição volta a apagar a origem",
     '    return {"stake_orig": round(novo / cot, 2)}', '    return {"limpa": True}'),
    ("a edição compara a grafia em vez do número",
     '    if novo == _num_or_none(antes.get("stake")) or not tem:',
     '    if safe["stake"] == antes["stake"] or not tem:'),
    ("a edição inventa origem em linha de real",
     '    if novo == _num_or_none(antes.get("stake")) or not tem:',
     '    if novo == _num_or_none(antes.get("stake")):'),
    ("sem snapshot a origem fica",
     '        return {"limpa": True} if ("stake" in safe or stake_orig is not None) else {}',
     '        return {}'),
    ("a stake na moeda é gravada como R$",
     '        return {"stake": f"{v * cot:.2f}".replace(".", ","), "stake_orig": round(v, 2)}',
     '        return {"stake": f"{v:.2f}".replace(".", ","), "stake_orig": round(v, 2)}'),
    ("a stake na moeda passa sem cotação",
     '        if not tem or v is None or v <= 0:', '        if v is None or v <= 0:'),
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
    s = src.replace("\r\n", "\n")
    assert 'origem = _origem_pos_edicao(antes, safe, campos.get("stake_orig"))\n' in s
    assert '    if origem.get("limpa"):\n' in s
    assert '        safe = {**safe, "stake": origem["stake"]}\n' in s
    assert 'd["pl_orig"] = _pl_na_moeda_original(d)' in src
    assert 'linha["stake_orig"] = float(r["stake_orig"])' in src
    assert 'linha["lucro_orig"] = _pl_na_moeda_original(r)' in src


# ── Front ────────────────────────────────────────────────────────────────────

@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
def test_front_por_execucao():
    r = subprocess.run(["node", str(MJS)], capture_output=True, text=True,
                       encoding="utf-8", cwd=str(RAIZ))
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")


MUTACOES_FRONT = [
    ("o dólar perde o US$", "index",
     "const _MOEDA_ORIG = { USD: { pre: 'US$' }, USDT: { pos: 'USDT' },",
     "const _MOEDA_ORIG = { USD: { pre: '$' }, USDT: { pos: 'USDT' },"),
    ("o peso perde o país e vira o $ do dólar cripto", "index",
     "ARS: { pre: 'AR$' } };", "ARS: { pre: '$' } };"),
    ("o euro some da grade", "index", " EUR: { pre: '€' },", ""),
    ("o USDT vira prefixo", "index",
     "  return f.pre ? `${sinal}${f.pre} ${t}` : `${sinal}${t} ${f.pos}`;",
     "  return f.pre ? `${sinal}${f.pre} ${t}` : `${sinal}${f.pos} ${t}`;"),
    ("o milhar some (toFixed, como o fmtUSD)", "index",
     "  return Math.abs(Number(n)).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });",
     "  return Math.abs(Number(n)).toFixed(2).replace('.', ',');"),
    ("a stake na moeda da conta grava em R$ (s398)", "index",
     '    return `<div class="btbl-cell btbl-num ap-edit" data-field="stake_orig" title=',
     '    return `<div class="btbl-cell btbl-num ap-edit" data-field="stake" title='),
    ("a stake na moeda da conta deixa de ser editável", "index",
     '    return `<div class="btbl-cell btbl-num ap-edit" data-field="stake_orig" title=',
     '    return `<div class="btbl-cell btbl-num" title='),
    ("a sub-linha some no modo R$", "index",
     "    const txt = _grVer === 'orig' ? (b.stake ? 'R$ ' + b.stake : '') : fmtMoedaOrig(b.stake_orig, b.moeda);",
     "    const txt = _grVer === 'orig' ? (b.stake ? 'R$ ' + b.stake : '') : '';"),
    ("o P/L não troca de moeda", "index",
     "  if (_grVer === 'orig' && _temOrig(b)) return (b.pl_orig != null ? moneyOrig(b.pl_orig, b.moeda, true) : fmtPL(null)) + _subPL(b);",
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
     "const _MOEDA_ORIG={USD:{pre:'US$'},",
     "const _MOEDA_ORIG={USD:{pre:'USD'},"),
    ("o dashboard escreve o dólar australiano diferente da grade", "app",
     "AUD:{pre:'A$'}", "AUD:{pre:'AU$'}"),
    ("o P/L perde a sub-linha", "index",
     "  return fmtPL(b.pl) + _subPL(b);", "  return fmtPL(b.pl);"),
    ("a sub-linha do P/L perde o sinal de mais", "index",
     "  const t = _num2BR(n), sinal = n < 0 ? '−' : (comSinal && n > 0 ? '+' : '');",
     "  const t = _num2BR(n), sinal = n < 0 ? '−' : '';"),
    ("a sub-linha do P/L aparece na aberta", "index",
     "  if (!_temOrig(b) || b.pl_orig == null || b.pl == null) return '';",
     "  if (!_temOrig(b)) return '';"),
    ("no modo moeda da conta o R$ do P/L não desce", "index",
     "    txt = (n > 0 ? '+' : (n < 0 ? '−' : '')) + 'R$ ' + _num2BR(n);",
     "    txt = '';"),
    ("o dashboard perde o sinal do P/L original", "app",
     "s=n<0?'−':(comSinal&&n>0?'+':'');", "s=n<0?'−':'';"),
    ("a Base Completa perde a sub-linha do P/L", "apostas",
     "fmtPL(r.lucro)+(r.lucro_orig!=null&&fmtMoedaOrig(r.lucro_orig,r.moeda,true)?",
     "fmtPL(r.lucro)+(false&&fmtMoedaOrig(r.lucro_orig,r.moeda,true)?"),
    ("a Base Completa perde a sub-linha", "apostas",
     # s392: a célula exibe o valor APOSTADO (`stakeCheio`), que difere do `stake` na freebet.
     "${fmtR(stakeCheio(r))}${r.stake_orig!=null&&fmtMoedaOrig(r.stake_orig,r.moeda)?",
     "${fmtR(stakeCheio(r))}${false&&fmtMoedaOrig(r.stake_orig,r.moeda)?"),
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
