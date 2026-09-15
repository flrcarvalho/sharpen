"""A RÉGUA ÚNICA de custo de conta (s362) — a aba Contas e o KPI medem o mesmo.

Desde a s358 as duas telas respondem LANÇAMENTO ("o que saiu do bolso no recorte"),
mas cada uma derivava a resposta por um caminho próprio: `_c2contas` varria o CADASTRO
(`_contasVida`) e datava por `adquirida_em` cru; `calcCostFiltered` varria cadastro ∪
BILHETE (`_contaVida`) e datava por `_dataPagamento`.

Medido antes de mexer, carregando o JS de produção contra o Postgres real: os dois
davam o MESMO número em 8 bases (Feca R$ 59.600, realtrial R$ 30.000, Jonathan
R$ 28.400, Jaao26 R$ 4.600, germano R$ 3.600, Gabriel R$ 540, Diogo e arrudex R$ 0) —
divergência R$ 0 em todas. Mas por sorte do dado: toda conta com custo hoje tem
cadastro e `adquirida_em` anterior à 1ª aposta, porque foi o backfill que a deduziu
assim. Bastava um `adquirida_em` digitado depois da 1ª aposta, ou um preço numa das
130 contas que só existem em bilhete, para os números discordarem sem erro nenhum.

A prova de COMPORTAMENTO roda em `tests/js/custos_regua_unica.mjs`, que executa
`_c2contas` RECORTADA do `custos2.js` de produção e `calcCostFiltered` RECORTADA do
`gestao.js`, mais o `_selRange` REAL do `filters.js` e o `parseNum` REAL do `app.js`.
Nenhuma regra é reimplementada — a mutação entra pela cópia estragada (`ALVO_*`) e o
código exercido é o real.

O que NÃO está coberto: o render da tabela (colunas, rótulo de origem, rodapé) e o
recorte por Casa/Fornecedor/Operador, que têm gate próprio em `test_recorte_custos.py`.
Aqui é só a igualdade dos dois números, total e mês a mês.
"""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
JS = RAIZ / "app" / "static" / "dash" / "assets" / "js"
CUSTOS2 = JS / "charts" / "custos2.js"
GESTAO = JS / "charts" / "gestao.js"
MJS = RAIZ / "tests" / "js" / "custos_regua_unica.mjs"


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
def test_prova_por_execucao_da_regua_unica():
    r = subprocess.run(["node", str(MJS)], capture_output=True, text=True,
                       encoding="utf-8", cwd=str(RAIZ))
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")


# (título, arquivo, trecho original, trecho estragado)
MUTACOES = [
    # ── A DATA: `_c2contas` volta a datar pelo cadastro cru ──────────────────
    (
        "a aba volta a datar a conta por adquirida_em cru (o defeito da s362)",
        "custos2",
        "      const data = _dataPagamento(v);",
        "      const data = v.adq;",
    ),
    (
        "a aba deixa de recortar por periodo e cobra tudo em todo mes",
        "custos2",
        "      if (!data || data < r.de || data > r.ate) return;",
        "      if (!data) return;",
    ),
    # ── O UNIVERSO: `_c2contas` volta a varrer so o cadastro ─────────────────
    (
        "a aba volta a varrer so o CADASTRO e esconde a conta so-de-bilhete",
        "custos2",
        "  Object.entries(_contaVida || {}).forEach(([k, contas]) => {",
        "  Object.entries({}).forEach(([k, contas]) => {",
    ),
    (
        "o _contaVida deixa de ser construido e a aba nasce vazia",
        "custos2",
        # Ancora com a linha de cima: a MESMA guarda existe no `_c2primeiraData`, e
        # sem ela o trecho nao e unico no arquivo.
        "  if (typeof _contaVida === 'undefined') return out;\n"
        "  if (!_contaVida && typeof _buildContaVida === 'function') _buildContaVida();",
        "  if (typeof _contaVida === 'undefined') return out;\n"
        "  if (false) _buildContaVida();",
    ),
    # ── O DEGRAU: a data do preco e a da COMPRA, nao a do pagamento ──────────
    (
        "o degrau exibido passa a sair da data do PAGAMENTO",
        "custos2",
        "      const degrau = _precoVigenteEm(_degrausPreco(forn, casa), _dataDoPreco(v));",
        "      const degrau = _precoVigenteEm(_degrausPreco(forn, casa), data);",
    ),
    (
        "o preco do fornecedor passa a ser o de HOJE, e nao o da data de compra",
        "gestao",
        "  return (v&&(v.adq||v.ini))||'';",
        "  return '9999-12-31';",
    ),
    # ── O VALOR: as tres camadas do _custoDaConta ───────────────────────────
    (
        "o custo PROPRIO da conta deixa de ganhar do preco do fornecedor",
        "gestao",
        "  if(v&&v.custo>0)return v.custo;",
        "  if(false)return v.custo;",
    ),
    (
        "a aba para de usar o _custoDaConta e le o preco do par cru",
        "custos2",
        "                 custo: _custoDaConta(forn, casa, conta) });",
        "                 custo: herdadoPar });",
    ),
    # ── A DATA DO PAGAMENTO: a ordem das tres camadas ───────────────────────
    (
        "o adquirida_em digitado deixa de ganhar da 1a aposta",
        "gestao",
        "  if(v.adq&&(!v.pa||v.adq<v.pa))return v.adq;",
        "  if(false)return v.adq;",
    ),
    (
        "a 1a aposta deixa de ser piso e a conta migrada perde a data",
        "gestao",
        "  return v.pa||v.adq||'';",
        "  return v.adq||'';",
    ),
]


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
@pytest.mark.parametrize("titulo,arq,de,para", MUTACOES, ids=[m[0] for m in MUTACOES])
def test_mutacoes_sao_detectadas(tmp_path, titulo, arq, de, para):
    """Quebra o código de propósito e exige que o .mjs fique VERMELHO.

    A cópia estragada entra pelo `ALVO_CUSTOS2`/`ALVO_GESTAO` — o .mjs recorta dela em
    vez do arquivo de produção, então a mutação é exercida pelo código real."""
    alvo = CUSTOS2 if arq == "custos2" else GESTAO
    src = alvo.read_text(encoding="utf-8")
    assert src.count(de) == 1, (
        f"a âncora da mutação «{titulo}» não é única no {alvo.name} "
        f"({src.count(de)} ocorrência(s)) — atualize a lista MUTACOES"
    )
    estragado = tmp_path / alvo.name
    estragado.write_text(src.replace(de, para, 1), encoding="utf-8")

    env = {**os.environ, ("ALVO_CUSTOS2" if arq == "custos2" else "ALVO_GESTAO"): str(estragado)}
    r = subprocess.run(["node", str(MJS)], capture_output=True, text=True,
                       encoding="utf-8", cwd=str(RAIZ), env=env)
    assert r.returncode != 0, (
        f"a mutação «{titulo}» passou despercebida — o gate não cobre esta regra.\n"
        + (r.stdout or "")
    )
