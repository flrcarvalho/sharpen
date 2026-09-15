"""O custo que está SÓ NESTE NAVEGADOR (s360).

O caso: o custo de conta, de tipster e o geral nasceram no localStorage; na s165 eles
ganharam coluna no Postgres (`custo_store`), e a trava anti-semeadura-parcial passou a
subir o dado só no SAVE. Quem preencheu antes e nunca mais editou ficou com tudo na
máquina, **com a tela mostrando o número certo o tempo todo** — não havia sintoma.

Medido em 2026-09-15, contra o Postgres de produção: 16 donos, 480 contas cadastradas,
**zero linha de custo em `custo_store`**. O dono Feca era um deles, e o que ele via na
Visão Geral saía do `CUSTO_SEED`, 11 pares cravados no `gestao.js` que só valem para o
username dele. Seed mascarando ausência é a pior forma da ausência: ela some no dia em
que o navegador é limpo, e o dono descobre pela tela zerada.

A saída tem três partes, e as três estão travadas aqui:

1. **A tela passa a dizer.** A faixa `.c2-guardar` (topo da tela de Custos) aparece
   quando há custo local e o servidor não tem, e traz o botão que sobe. A página
   `/dashboard/importar-custos.html` já fazia isso desde a s165, mas é URL avulsa, fora
   do menu de todo mundo — por isso ninguém a usou.
2. **O seed não sobe.** A detecção lê o CACHE e o `_custoHadLegacy` (medido no load,
   antes do fallback em memória), nunca o `custoData`.
3. **A ordem do envio.** `salvar_custo_conta` faz upsert na MESMA linha de
   `custo_store`; guardar o preço de conta primeiro faria `/custos/store` responder
   existe=true com o blob tipster/geral ainda vazio, e a carga seguinte adotaria o
   vazio — o `_ctMirror` gravaria o apagão por cima do cache. O `ctLoad` também passou
   a se defender disso, mas é a ordem que faz a janela não existir.

A prova de COMPORTAMENTO roda em `tests/js/custo_so_no_navegador.mjs`, que executa as
funções RECORTADAS do `gestao.js`, do `app.js` e do `custos2.js` de produção. Nenhuma
regra é reimplementada — a mutação entra pela cópia estragada (`ALVO_*`).

O que NÃO está coberto: o visual da faixa (cor, posição, quebra de linha em 1366), que
só a medição headless pega; e o lado servidor das rotas `/custos/conta` e
`/custos/store`, que não mudaram nesta sessão.
"""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
JS = RAIZ / "app" / "static" / "dash" / "assets" / "js"
ARQS = {
    "gestao": JS / "charts" / "gestao.js",
    "app": JS / "app.js",
    "custos2": JS / "charts" / "custos2.js",
}
MJS = RAIZ / "tests" / "js" / "custo_so_no_navegador.mjs"


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
def test_prova_por_execucao():
    r = subprocess.run(["node", str(MJS)], capture_output=True, text=True,
                       encoding="utf-8", cwd=str(RAIZ))
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")


# (título, arquivo, trecho original, trecho estragado)
MUTACOES = [
    # ── O SEED: exemplo cravado no código não é lançamento do dono ────────────
    # A versão INGÊNUA desta função: "servidor não tem, então ofereça o que está na
    # memória". É a que qualquer um escreveria, e é a que sobe o CUSTO_SEED. As duas
    # metades da real (o `_custoHadLegacy` e a leitura do cache) barram o seed cada uma
    # por si — por isso a mutação troca AS DUAS: separadas, cada uma é inócua, e inócua
    # não é buraco de teste. Ver a nota sobre redundância no fim deste arquivo.
    (
        "a deteccao ingenua le a memoria e o CUSTO_SEED vira lancamento do dono",
        "gestao",
        "  if(_custoServerBacked||!_custoHadLegacy)return null;\n"
        "  let cache={};try{cache=JSON.parse(localStorage.getItem(costKey())||'null')||{};}catch(e){return null;}",
        "  if(_custoServerBacked)return null;\n"
        "  const cache=custoData;",
    ),
    (
        "o par zerado passa a contar como lancamento",
        "gestao",
        "  const pares=Object.keys(cache).filter(k=>Number(cache[k])>0);",
        "  const pares=Object.keys(cache).filter(k=>Number(cache[k])>=0);",
    ),
    (
        "a faixa passa a oferecer guardar custo que o servidor JA tem",
        "gestao",
        "  if(_custoServerBacked||!_custoHadLegacy)return null;",
        "  if(!_custoHadLegacy)return null;",
    ),
    # ── O BOTAO NAO PODE MENTIR ──────────────────────────────────────────────
    (
        "o erro HTTP do envio do preco de conta e engolido",
        "gestao",
        "  if(!r.ok)throw new Error('HTTP '+r.status);\n"
        "  _custoServerBacked=true;",
        "  _custoServerBacked=true;",
    ),
    (
        "o erro HTTP do envio de tipster/geral e engolido",
        "app",
        "  if(!r.ok)throw new Error('HTTP '+r.status);\n"
        "  _ctServerBacked=true;",
        "  _ctServerBacked=true;",
    ),
    (
        "o envio de tipster/geral nao marca o dono como servido e a faixa nunca some",
        "app",
        "  _ctServerBacked=true;\n  _ctMirror();\n  return true;",
        "  _ctMirror();\n  return true;",
    ),
    # ── O QUE ESTA NO NAVEGADOR: numero, nao verdade da string ────────────────
    (
        'o "0,00" do tipster passa a contar (zero se disfarcando de conta feita)',
        "app",
        "  const temVal=(o)=>Object.values(o||{}).some(v=>parseNum(v)>0);",
        "  const temVal=(o)=>Object.values(o||{}).some(v=>!!v);",
    ),
    # ── A GUARDA: servidor vazio nao apaga o cache ───────────────────────────
    (
        "o blob vazio do servidor volta a apagar o lancamento local",
        "app",
        "        if(vazioLa&&_ctHadLegacy){_ctServerBacked=false;}",
        "        if(false){_ctServerBacked=false;}",
    ),
    (
        "a guarda passa a valer tambem quando o servidor TEM dado",
        "app",
        "        const vazioLa=!Object.keys(d.custo_tipster||{}).length&&!(d.custo_geral||[]).length;",
        "        const vazioLa=true;",
    ),
    # ── A ORDEM DO ENVIO ─────────────────────────────────────────────────────
    (
        "o preco de conta sobe ANTES do blob e abre a janela do apagao",
        "custos2",
        "    if (typeof ctSubir === 'function') fezCt = await ctSubir();\n"
        "    if (typeof custoContaSubir === 'function') fezCc = await custoContaSubir();",
        "    if (typeof custoContaSubir === 'function') fezCc = await custoContaSubir();\n"
        "    if (typeof ctSubir === 'function') fezCt = await ctSubir();",
    ),
    # ── A FAIXA ──────────────────────────────────────────────────────────────
    (
        "a faixa perde o botao e vira aviso sem acao (foi o que tirou a .c2-previa daqui)",
        "custos2",
        '      <button class="c2-guardar__btn" id="c2GuardarBtn" onclick="c2Guardar()">Guardar na minha conta</button>',
        "      <span>Guardar na minha conta</span>",
    ),
    (
        "a faixa manda conferir as abas mesmo sem tipster/geral em jogo",
        "custos2",
        "  const conferir = t\n",
        "  const conferir = true\n",
    ),
    (
        "o envio parcial passa a se anunciar como falha total",
        "custos2",
        "    const feito = [fezCt ? 'os tipsters e gerais' : '', fezCc ? 'os preços de conta' : ''].filter(Boolean).join(' e ');",
        "    const feito = '';",
    ),
]


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
@pytest.mark.parametrize("titulo,arq,de,para", MUTACOES, ids=[m[0] for m in MUTACOES])
def test_mutacoes_sao_detectadas(tmp_path, titulo, arq, de, para):
    """Quebra o código de propósito e exige que o .mjs fique VERMELHO.

    A cópia estragada entra pelo `ALVO_GESTAO`/`ALVO_APP`/`ALVO_CUSTOS2` — o .mjs
    recorta dela em vez do arquivo de produção, então a mutação é exercida pelo
    código real."""
    alvo = ARQS[arq]
    src = alvo.read_text(encoding="utf-8")
    assert src.count(de) == 1, (
        f"a âncora da mutação «{titulo}» não é única no {alvo.name} "
        f"({src.count(de)} ocorrência(s)) — atualize a lista MUTACOES"
    )
    estragado = tmp_path / alvo.name
    estragado.write_text(src.replace(de, para, 1), encoding="utf-8")

    env = {**os.environ, f"ALVO_{arq.upper()}": str(estragado)}
    r = subprocess.run(["node", str(MJS)], capture_output=True, text=True,
                       encoding="utf-8", cwd=str(RAIZ), env=env)
    assert r.returncode != 0, (
        f"a mutação «{titulo}» passou despercebida — o gate não cobre esta regra.\n"
        + (r.stdout or "")
    )


# ── Mutações INÓCUAS, medidas e registradas (não são buraco de teste) ────────
#
# `ctPendente` lê o localStorage em vez de `ctData`. Trocar por `ctData` NÃO muda
# resultado nenhum: `ctLoad` carrega `ctData` a partir dessas mesmas chaves, `ctSave`
# espelha de volta antes de qualquer decisão, e o caminho em que o servidor manda
# (`_ctServerBacked=true`) já devolve null no primeiro `if`. A leitura fica por
# simetria com o lado do custo por conta, onde ela É load-bearing: lá o `custoData`
# carrega o CUSTO_SEED em memória, e a mutação "detecção ingênua" acima prova isso.
#
# Pelo mesmo motivo, tirar só `!_custoHadLegacy` OU só a leitura do cache (uma de cada
# vez) do `custoContaPendente` é inócuo: as duas metades barram o seed cada uma por si.
# A mutação que vale é a que troca as duas, e é a que está na lista.
