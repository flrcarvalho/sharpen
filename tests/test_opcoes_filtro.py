"""As LISTAS DE OPÇÃO dos filtros (s358) — o filtro que parece completo e não está.

Nasceu de um relato do Feca sobre a aba Tipsters: *"o filtro de Tipster está mto
desatualizado. Falta dezenas de nomes"*. Medindo, eram três defeitos distintos, e
nenhum deles gera erro — todos produzem uma lista que **parece** inteira. Depois, com a
auditoria das outras abas, entrou um quarto, da mesma família:

1. **ORDEM.** `.sort()` puro ordena por código UTF-16, que joga minúscula e acento para
   depois do Z. Medido na base do Feca: **63 dos 76 tipsters fora do lugar** — `deLucca`,
   `eSoccer LBB`, `eSports LG` e `fullpicks` atrás de `Zora`, `Caçador Basquete` atrás de
   `Cantos`, `Várzea` atrás de `VoleyStars`. Ninguém some; quem rola até onde o nome
   deveria estar é que conclui que sumiu.

2. **UNIÃO.** As opções saem de `DADOS` ∪ `DADOS_ABERTAS`, porque `DADOS` só tem aposta
   liquidada (`aplicarFeed`). Tipster, casa ou operador que só tenha aposta EM ABERTO
   ficaria invisível justamente na tela "Em Aberto", que é onde ele importa. O
   `_grupoOperador` era o único dos cinco eixos que ainda lia só `DADOS`.

3. **EXISTÊNCIA NÃO VEM DO BILHETE.** O Fornecedor da tela de Custos é cadastro ∪ base:
   conta comprada custa antes da primeira aposta (regra do `CLAUDE.md`). Medido: **26
   contas ativas cadastradas sem nenhum bilhete** e **4 fornecedores** (`Fernanda`,
   `amigo`, `richard`, `xxxx`) que só existem no cadastro.

4. **EIXO QUE NÃO RECORTA.** O Operador entrou na barra da tela de Custos, porque a
   regra do projeto diz que ele e a Casa descrevem a CONTA e por isso os dois recortam
   custo — a tela aplicava metade. Filtro que aparece e não filtra é **pior** que filtro
   ausente: é o defeito da s322 com outra roupa. O operador de uma conta não é campo do
   cadastro, sai do bilhete, e quem já o resolve é o `_contaVida`.

A prova de COMPORTAMENTO roda em `tests/js/opcoes_filtro.mjs`, que executa `cmpNome`,
`recalcListasFiltro`, `_c2Fornecedores` e `_c2sel`/`_c2passa` RECORTADAS dos arquivos de
produção. Provado por mutação: 9/9 detectadas.

O que NÃO está coberto, e é preciso dizer: o DOM. `msRepintar` e `atualizarOpcoesFiltros`
escrevem `innerHTML` e dependem dos nós `msb_<id>`/`ms-opts-<id>`; que a repintura
acontece na CHEGADA do feed fresco é uma chamada dentro do `loadData` e também não se
prova daqui. Os dois foram medidos na tela, no `servidor_demo`.

Mutação INÓCUA registrada (a mesma já registrada em `tests/js/filtros_base_completa.mjs`,
pelo mesmo motivo): tirar `sensitivity:'base'` do `cmpNome` não é detectável aqui. Sob o
ICU do node a colação pt-BR já separa caixa e acento no nível terciário, então a opção só
muda o DESEMPATE entre variantes da mesma letra (`Bet365` × `BET365`) — e ali ela manda
justamente empatar. Inventar asserção para isso seria afirmar uma ordem que a opção
deliberadamente deixa indefinida.
"""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
FILTERS = RAIZ / "app" / "static" / "dash" / "assets" / "js" / "filters.js"
CUSTOS2 = RAIZ / "app" / "static" / "dash" / "assets" / "js" / "charts" / "custos2.js"
APP_JS = RAIZ / "app" / "static" / "dash" / "assets" / "js" / "app.js"
MJS = RAIZ / "tests" / "js" / "opcoes_filtro.mjs"


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
def test_prova_por_execucao_das_listas():
    r = subprocess.run(["node", str(MJS)], capture_output=True, text=True,
                       encoding="utf-8", cwd=str(RAIZ))
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")


def test_o_feed_fresco_repinta_os_seletores():
    """A outra metade do defeito, que o .mjs não alcança: `buildHTML` roda só na primeira
    pintura. Com cache local ele monta as opções com o dado CACHEADO, e quando o feed
    fresco chega o `loadData` repintava a view sem tocar em seletor nenhum — numa aba
    aberta por dias, todo nome novo ficava invisível em TODOS os filtros enquanto os
    cards, que leem `DADOS` ao vivo, seguiam mostrando ele."""
    src = APP_JS.read_text(encoding="utf-8")
    assert "function atualizarOpcoesFiltros(" in src, "a repintura das opções sumiu"
    # A chamada tem de estar no caminho do dado fresco (bloco 3a do loadData), ANTES do
    # renderPage: é ele que fecha o ciclo trocou-o-dado → refez-as-opções.
    bloco = src[src.index("if(servedFromCache||!_rebuild){"):src.index("// ── 3b)")]
    assert "atualizarOpcoesFiltros()" in bloco, (
        "o dado fresco voltou a chegar sem refazer as opções dos filtros"
    )


def test_todo_eixo_da_barra_entra_na_repintura():
    """Gate por LISTA, não por lembrança: o eixo novo que alguém acrescentar à barra
    precisa entrar aqui, senão ele congela no primeiro paint e ninguém percebe — é
    exatamente o modo de falha que esta sessão consertou."""
    src = APP_JS.read_text(encoding="utf-8")
    bloco = src[src.index("function atualizarOpcoesFiltros("):src.index("function buildHTML(")]
    for prefixo in ("sp_", "ca_", "ti_", "op_", "pa_apostas", "fo_custos_v2"):
        assert prefixo in bloco, f"o eixo {prefixo} ficou de fora do atualizarOpcoesFiltros"


MUTACOES = [
    ("cmpNome volta a ser .sort() puro (minuscula e acento depois do Z)",
     FILTERS, ".sort(cmpNome)", ".sort()"),
    ("as listas leem so DADOS e perdem quem so tem aposta em aberto",
     FILTERS, "const t=DADOS.concat(DADOS_ABERTAS);", "const t=DADOS.slice();"),
    ("o travessao volta a ser uma conta chamada travessao",
     FILTERS, "p=>p&&p!=='—'", "p=>!!p"),
    ("nome vazio vira uma opcao do seletor",
     FILTERS,
     "const uniq=(f,extra)=>[...new Set(t.map(f).filter(extra||Boolean))].sort(cmpNome);",
     "const uniq=(f,extra)=>[...new Set(t.map(f).filter(extra||(()=>true)))].sort(cmpNome);"),
    ("o Fornecedor da tela de Custos volta a ler so o bilhete",
     CUSTOS2,
     "  (typeof _contasCadastro !== 'undefined' && _contasCadastro ? _contasCadastro : [])\n"
     "    .forEach(c => { const f = normForn(c.fornecedor); if (f) s.add(f); });",
     "  // cadastro removido pela mutacao"),
    ("o fornecedor vazio do cadastro deixa de virar \"Eu\"",
     CUSTOS2,
     "const f = normForn(c.fornecedor); if (f) s.add(f);",
     "const f = c.fornecedor; if (f) s.add(f);"),
    # Eixo Operador na tela de Custos: filtro que aparece e nao filtra e pior que ausente.
    ("o eixo Operador aparece na barra e NAO recorta",
     CUSTOS2,
     "  if (conta !== undefined && sel.op && sel.op.size && !sel.op.has(_c2opDaConta(forn, casa, conta))) return false;",
     "  // recorte por operador removido pela mutacao"),
    ("o Operador passa a cortar tambem a tabela de precos, que nao tem conta",
     CUSTOS2,
     "  if (conta !== undefined && sel.op && sel.op.size",
     "  if (sel.op && sel.op.size"),
    ("o operador da conta deixa de vir do _contaVida e vira sempre vazio",
     CUSTOS2,
     "  return (v && v.op) || '';",
     "  return '';"),
]


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
@pytest.mark.parametrize("titulo,alvo,de,para", MUTACOES, ids=[m[0] for m in MUTACOES])
def test_mutacoes_sao_detectadas(tmp_path, titulo, alvo, de, para):
    """Quebra o arquivo de produção de propósito e exige que o .mjs fique VERMELHO."""
    src = alvo.read_text(encoding="utf-8")
    assert src.count(de) == 1, (
        f"a âncora da mutação «{titulo}» não é única em {alvo.name} "
        f"({src.count(de)} ocorrência(s)) — atualize a lista MUTACOES"
    )
    estragado = tmp_path / alvo.name
    estragado.write_text(src.replace(de, para, 1), encoding="utf-8")
    env_var = "ALVO_FILTERS" if alvo is FILTERS else "ALVO_CUSTOS2"

    r = subprocess.run(["node", str(MJS)], capture_output=True, text=True,
                       encoding="utf-8", cwd=str(RAIZ),
                       env={**os.environ, env_var: str(estragado)})
    assert r.returncode != 0, (
        f"a mutação «{titulo}» passou despercebida — o gate não cobre esta regra.\n"
        + (r.stdout or "")
    )
