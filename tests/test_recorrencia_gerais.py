"""Custo geral: categoria e recorrência (s348, Fatia 4).

Os custos que não são conta nem tipster — infra, ferramentas, taxas — ganharam duas
coisas: uma **categoria** (três de fábrica mais as que o dono criar) e uma
**recorrência**, que decide se o valor do mês anterior se arrasta.

A recorrência usa o MESMO `_arrasta` do tipster. Escrever a regra duas vezes a faria
divergir no dia em que um terceiro tipo aparecesse, e ninguém descobriria pelo erro:
descobriria pelo número preenchido sozinho.

A lista de categorias é **derivada das linhas**: uma categoria existe porque alguma
linha a usa. Não há lista para manter nem categoria órfã para limpar — e é por isso
que a ordem e a deduplicação precisam de gate.

A prova de COMPORTAMENTO roda em `tests/js/recorrencia_gerais.mjs`, que executa as
funções RECORTADAS do `gestao.js` de produção. Este arquivo a invoca e depois a
prova por MUTAÇÃO.

O que NÃO está coberto: o render da aba e a gravação (`ctSave` → `/custos/store`),
que é o mesmo caminho que o custo de tipster já usava antes desta fatia.
"""
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
GESTAO = RAIZ / "app" / "static" / "dash" / "assets" / "js" / "charts" / "gestao.js"
MJS = RAIZ / "tests" / "js" / "recorrencia_gerais.mjs"


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
def test_prova_por_execucao_dos_gerais():
    r = subprocess.run(["node", str(MJS)], capture_output=True, text=True,
                       encoding="utf-8", cwd=str(RAIZ))
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")


MUTACOES = [
    (
        "mensal deixa de arrastar",
        "  return _arrasta(_cgRecorrencia(i)) ? _cgValor(i,ymAnterior) : 0;",
        "  return 0;",
    ),
    (
        "TODA recorrencia passa a arrastar (variavel volta a repetir)",
        "  return _arrasta(_cgRecorrencia(i)) ? _cgValor(i,ymAnterior) : 0;",
        "  return _cgValor(i,ymAnterior);",
    ),
    (
        "valor no mes deixa de confirmar a linha",
        "  return _cgValor(i,ym)>0 ? 'confirmado' : 'pendente';",
        "  return 'pendente';",
    ),
    (
        "as categorias de fabrica somem da lista",
        "  return CG_CATEGORIAS_BASE.concat(proprias);",
        "  return proprias;",
    ),
    (
        "categoria repetida passa a entrar duas vezes",
        "  const usadas=new Set();",
        "  const usadas=[];",
    ),
    (
        "categoria de fabrica passa a duplicar quando uma linha a usa",
        "  const proprias=[...usadas].filter(c=>!CG_CATEGORIAS_BASE.includes(c))",
        "  const proprias=[...usadas].filter(c=>true)",
    ),
    (
        "categoria vazia passa a virar uma categoria",
        "    if(c)usadas.add(c);",
        "    usadas.add(c);",
    ),
    (
        "a ordem das proprias deixa de ser pt-BR",
        "    .sort((a,b)=>a.localeCompare(b,'pt-BR'));",
        "    ;",
    ),
    (
        "de fabrica para de aparar espaco e a categoria some da marcacao",
        "function _cgEhDeFabrica(c){return CG_CATEGORIAS_BASE.includes((c||'').trim());}",
        "function _cgEhDeFabrica(c){return CG_CATEGORIAS_BASE.includes(c);}",
    ),
    (
        "o valor do custo geral para de ler o decimal em virgula",
        "function _cgValor(i,ym){\n  const r=_cgLinha(i);\n  const v=((r&&r.values)||{})[ym];\n  const n=parseFloat((v==null?'':v).toString().replace(/\\./g,'').replace(',','.'));",
        "function _cgValor(i,ym){\n  const r=_cgLinha(i);\n  const v=((r&&r.values)||{})[ym];\n  const n=parseFloat((v==null?'':v).toString());",
    ),
]

# MUTAÇÃO INÓCUA, medida e registrada (CLAUDE.md, "Teste verde não é teste que
# detecta"): trocar `_cgLinha` por `return cgData[i];` NÃO derruba o gate, e não é
# buraco de teste — é redundância real. `cgData[i]` fora da lista já devolve
# `undefined`, e `(r&&r.values)||{}` lida com isso sozinho. O que a guarda protege
# é `cgData` ser *undefined*, que só aconteceria se o `gestao.js` rodasse antes do
# `app.js` — e ele não roda nada no load. Escrever um teste que apaga a variável
# provaria o harness, não o produto.


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
@pytest.mark.parametrize("titulo,de,para", MUTACOES, ids=[m[0] for m in MUTACOES])
def test_mutacoes_sao_detectadas(tmp_path, titulo, de, para):
    """Quebra o gestao.js de propósito e exige que o .mjs fique VERMELHO."""
    src = GESTAO.read_text(encoding="utf-8")
    assert src.count(de) == 1, (
        f"a âncora da mutação «{titulo}» não é única no gestao.js "
        f"({src.count(de)} ocorrência(s)) — atualize a lista MUTACOES"
    )
    estragado = tmp_path / "gestao.js"
    estragado.write_text(src.replace(de, para, 1), encoding="utf-8")

    import os
    r = subprocess.run(["node", str(MJS)], capture_output=True, text=True,
                       encoding="utf-8", cwd=str(RAIZ),
                       env={**os.environ, "ALVO_GESTAO": str(estragado)})
    assert r.returncode != 0, (
        f"a mutação «{titulo}» passou despercebida — o gate não cobre esta regra.\n"
        + (r.stdout or "")
    )
