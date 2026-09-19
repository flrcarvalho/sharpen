"""O switch R$⇄u da tela Tipsters vale para a TELA inteira (s374).

Sugestão do tester João: *"na tela de tipsters, quando alterar o P/L para U, mudar
para U em cada tipster também"*. Até aqui o "u" alcançava o KPI do topo e a coluna
P/L do Comparativo; os CARDS ficavam em R$, porque eles só sabiam renderizar u pelo
`MODO_PUBLICO`, que não existe no dashboard privado. Um card dizendo "− R$ 1.520,31"
logo abaixo de um KPI dizendo "−28,38u": cada metade certa, a razão entre as duas
impossível de ler.

A regra que os dois lados compartilham é `_tipsterUnidades` (`app.js`), e ela converte
**por linha**, pela unidade vigente na data. A escada muda no tempo, e dividir o total
por uma unidade só misturaria eras.

A prova de COMPORTAMENTO roda em `tests/js/tipster_visao_u.mjs`, que executa as funções
RECORTADAS do `app.js` e do `performance.js` de produção. Este arquivo a invoca e depois
a prova por MUTAÇÃO (ver `test_mutacoes_sao_detectadas`).

O que NÃO está coberto aqui:
  · o render de verdade (o .mjs dubla o `document`): posição, CSS e Escada de Tinta
    seguem fora do alcance de um teste sem navegador;
  · o KPI "Turnover Total" e as duas colunas do Comparativo Geral, que vivem dentro do
    `renderTipsters` (preso ao DOM e ao feed). O que se prova deles aqui é FORMA, em
    `test_a_tela_inteira_pergunta_pelo_switch`, que é um grep: pega remoção, mas não
    prova número nenhum;
  · o drill-down do tipster, que segue em R$ por decisão desta sessão (o Monte Carlo e
    a curva rodam sobre a série em reais);
  · o fetch de `/tipsters/escadas` e a preferência gravada no localStorage.
"""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
APP = RAIZ / "app" / "static" / "dash" / "assets" / "js" / "app.js"
PERF = RAIZ / "app" / "static" / "dash" / "assets" / "js" / "charts" / "performance.js"
MJS = RAIZ / "tests" / "js" / "tipster_visao_u.mjs"


def _node(env_extra=None):
    return subprocess.run(
        ["node", str(MJS)], capture_output=True, text=True, encoding="utf-8",
        cwd=str(RAIZ), env={**os.environ, **(env_extra or {})},
    )


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
def test_prova_por_execucao_da_visao_em_unidades():
    r = _node()
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")


# (arquivo, título, de, para). O arquivo diz qual cópia estragar; a âncora é conferida
# como ÚNICA antes de mutar, porque os três cards (esporte, casa, tipster) nasceram
# copiados um do outro, e uma âncora ambígua mutaria a tela errada. A mutação passaria
# verde com razão, e o verde seria falso.
MUTACOES = [
    (
        "app.js",
        "a unidade deixa de ser a vigente na DATA da linha",
        "      let uu=_uVigente(escada,ln.data);",
        "      let uu=_uVigente(escada,'9999-12-31');",
    ),
    (
        "app.js",
        "o turnover em u passa a incluir o Void",
        "      if(ln.res!=='V'){o.s+=(ln.stake||0)/uu;o.t++;}",
        "      o.s+=(ln.stake||0)/uu;o.t++;",
    ),
    (
        "app.js",
        "linha sem unidade resolvivel vira 1u em vez de ficar fora",
        "      if(!(uu>0))return;",
        "      if(!(uu>0))uu=1;",
    ),
    (
        "app.js",
        "a sparkline continua em R$ enquanto o resto vai para u",
        "      if(ln.data)o.dias[ln.data]=(o.dias[ln.data]||0)+plU;",
        "      if(ln.data)o.dias[ln.data]=(o.dias[ln.data]||0)+ln.pl;",
    ),
    (
        "app.js",
        "fmtRU deixa de ser adaptativo (stake em u viraria 0u)",
        'function fmtRU(v){const n=Number(v)||0;return`<span class="money"><span class="money-val">${fmt(n,Math.abs(n)>=100?0:2)}',
        'function fmtRU(v){const n=Number(v)||0;return`<span class="money"><span class="money-val">${fmt(n,0)}',
    ),
    (
        "performance.js",
        "o card volta a so' obedecer ao MODO PUBLICO",
        "  const U=!!(emU||window.MODO_PUBLICO);",
        "  const U=!!window.MODO_PUBLICO;",
    ),
    (
        "performance.js",
        "so' o P/L troca de moeda: o Turnover do card fica em R$",
        '<div class="tcard__stat-lbl">Turnover</div><div class="tcard__stat-val">${U?`${stakeInt}<span class="tcard__cur--sm">u</span>`:`<span class="tcard__cur--sm">R$</span>${stakeInt}`}',
        '<div class="tcard__stat-lbl">Turnover</div><div class="tcard__stat-val"><span class="tcard__cur--sm">R$</span>${stakeInt}',
    ),
    (
        "performance.js",
        "a Stake Media do card fica em R$",
        '<div class="tcard__stat-lbl">Stake Média</div><div class="tcard__stat-val">${U?`${avgStakeStr}<span class="tcard__cur--sm">u</span>`:`<span class="tcard__cur--sm">R$</span>${avgStakeStr}`}',
        '<div class="tcard__stat-lbl">Stake Média</div><div class="tcard__stat-val"><span class="tcard__cur--sm">R$</span>${avgStakeStr}',
    ),
    (
        "performance.js",
        "o card recebe os valores em u mas nao a MOEDA (meio atualizado)",
        "    return _mkTipCard(t,pl,roi,stake,wr,d.n,_tipSparkSVG(dias,_tipsterAllDays),avgStake,avgOdd,emU);",
        "    return _mkTipCard(t,pl,roi,stake,wr,d.n,_tipSparkSVG(dias,_tipsterAllDays),avgStake,avgOdd,false);",
    ),
    (
        "performance.js",
        "o card troca a moeda mas segue com o valor em R$",
        "    const pl=u?u.pl:d.l;",
        "    const pl=d.l;",
    ),
    (
        "performance.js",
        "a ordenacao por P/L ignora as unidades",
        "    pl:([t,d])=>uv(t,'pl',d.l),",
        "    pl:([,d])=>d.l,",
    ),
    (
        "performance.js",
        "a ordenacao por Turnover ignora as unidades",
        "    to:([t,d])=>uv(t,'s',d.s),",
        "    to:([,d])=>d.s,",
    ),
    (
        "performance.js",
        "a stake media do card usa o denominador do lado em R$",
        "    const avgStake=u?(u.t>0?u.s/u.t:0):(d.t>0?d.s/d.t:0);",
        "    const avgStake=d.t>0?d.s/d.t:0;",
    ),
]


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
@pytest.mark.parametrize("arquivo,titulo,de,para", MUTACOES, ids=[m[1] for m in MUTACOES])
def test_mutacoes_sao_detectadas(tmp_path, arquivo, titulo, de, para):
    """Quebra o código de propósito e exige que o .mjs fique VERMELHO.

    Verde sem esta prova não prova nada (CLAUDE.md, "Teste verde não é teste que
    detecta")."""
    origem = APP if arquivo == "app.js" else PERF
    src = origem.read_text(encoding="utf-8")
    assert src.count(de) == 1, (
        f"a âncora da mutação «{titulo}» não é única no {arquivo} "
        f"({src.count(de)} ocorrência(s)). Mutação que não acerta o alvo passa verde "
        f"com razão; atualize a lista MUTACOES"
    )
    estragado = tmp_path / arquivo
    estragado.write_text(src.replace(de, para, 1), encoding="utf-8")
    chave = "ALVO_APP" if arquivo == "app.js" else "ALVO_PERF"

    r = _node({chave: str(estragado)})
    assert r.returncode != 0, (
        f"a mutação «{titulo}» passou despercebida: o gate não cobre esta regra.\n"
        + (r.stdout or "")
    )


def test_a_tela_inteira_pergunta_pelo_switch():
    """FORMA, não número: o KPI de Turnover e as duas colunas do Comparativo Geral.

    Eles vivem dentro do `renderTipsters`, que é função de ~90 linhas presa ao DOM e ao
    feed, fora do alcance do .mjs. Este teste só garante que ninguém os devolva ao R$
    fixo em silêncio, que é exatamente o defeito que o João reportou nos cards. Um grep
    pega a REMOÇÃO; não prova valor nenhum.
    """
    src = PERF.read_text(encoding="utf-8")
    assert "${emU?fmtRU(portUturn):fmtR(portStake)}" in src, (
        "o KPI 'Turnover Total' voltou a ser sempre em R$"
    )
    assert "const turnCel=u?fmtRU(u.s):fmtR(d.s);" in src, (
        "a coluna Turnover do Comparativo Geral voltou a ser sempre em R$"
    )
    assert "const avgCel=u?fmtRU(u.t>0?u.s/u.t:0):fmtR(avgStake);" in src, (
        "a coluna Stake média do Comparativo Geral voltou a ser sempre em R$"
    )
    assert "_tipsterEmU=emU;_tipsterU=uMap;" in src, (
        "o retrato do switch sumiu: reordenar os cards devolveria a tela a R$"
    )


def test_a_mascara_de_agregado_em_u_e_uma_so():
    """O modo público e o switch da página Tipsters usam a MESMA máscara.

    Duas cópias divergiriam no primeiro ajuste, e a do modo público é a que já estava
    cravada (adaptativa: inteiro acima de 100, 2 casas abaixo).
    """
    src = APP.read_text(encoding="utf-8")
    assert "fmtR=v=>fmtRU(v);" in src, "o modo público voltou a carregar cópia própria da máscara em u"
    assert src.count("<span class=\"money-u\">u</span>") == 2, (
        "o sufixo 'u' tem de existir em exatamente dois lugares (fmtU e fmtRU); "
        "uma terceira cópia é um formatador caseiro nascendo"
    )
