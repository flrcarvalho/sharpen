"""Janela de vida da conta (s322) — o custo existe enquanto a conta existe.

Reclamação do tester Jaao26, em vídeo: com o período em "Tudo" o KPI dizia
`Custo de Contas −R$ 3.100,00` e, filtrando UM dia (05/09 → 05/09), virava `R$ 0` —
com o parque inteiro de contas em uso. *"Ele mostra que o meu custo de conta é zero,
mas ele não necessariamente é zero porque eu ainda estou usando essas contas."*

A causa: `calcCostFiltered` lançava o custo de aquisição num ÚNICO dia — o da primeira
aposta LIQUIDADA — e só o cobrava quando o intervalo das LINHAS filtradas continha
aquele dia. Qualquer outro recorte dava zero. E a conta comprada e ainda não usada não
existia nesse mapa: ela entrava nos R$ 3.100 da aba Custos e nunca no KPI.

A régua nova (decisão do Feca): o custo é único, pago na compra, e todo período que
cruzar `[ini, fim]` cobra o custo CHEIO da conta.

    ini = menor(adquirida_em, 1ª aposta)
    fim = maior(última aposta, arquivada_em) — e HOJE p/ conta ativa ainda sem aposta

Consequência aceita e conhecida: a régua **não é aditiva** (somar os dias do mês dá
muito mais que o custo do mês). É o preço de "o custo está lá enquanto a conta está
viva", e o Feca confirmou o preço antes da implementação.

A prova de COMPORTAMENTO roda em `tests/js/custo_janela_vida.mjs`, que executa o
`calcCostFiltered`, o `calcCasaCost` e o `_buildContaVida` RECORTADOS do arquivo de
produção, mais o `_selRange` real do `filters.js`. Este arquivo o invoca e, em seguida,
o prova por MUTAÇÃO — ver `test_mutacoes_sao_detectadas`.

O que NÃO está coberto: o render (a legenda "N contas no período", a cor do card e a
Escada de Tinta ficam para o render headless), o `contasLoad` (fetch, dublado no .mjs) e
o backfill SQL de `adquirida_em`, que só roda contra Postgres.
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
GESTAO = RAIZ / "app" / "static" / "dash" / "assets" / "js" / "charts" / "gestao.js"
OVERVIEW = RAIZ / "app" / "static" / "dash" / "assets" / "js" / "charts" / "overview.js"
PERFORMANCE = RAIZ / "app" / "static" / "dash" / "assets" / "js" / "charts" / "performance.js"
MJS = RAIZ / "tests" / "js" / "custo_janela_vida.mjs"


def _sem_comentarios(codigo: str) -> str:
    """O gate lê o CÓDIGO, não a prosa sobre o código — o comentário desta mudança cita
    justamente os termos que os asserts procuram."""
    codigo = re.sub(r"/\*.*?\*/", "", codigo, flags=re.DOTALL)
    return re.sub(r"^\s*//.*$", "", codigo, flags=re.MULTILINE)


# ── Gates baratos de leitura: apontam a linha exata se alguém reverter ────────

def test_o_mapa_de_primeira_aposta_nao_voltou():
    """`_firstBetMap` guardava só a 1ª aposta liquidada — é a régua velha inteira.
    Enquanto ele não existir, ninguém reintroduz o lançamento em um dia só por engano."""
    src = _sem_comentarios(GESTAO.read_text(encoding="utf-8"))
    assert "_firstBetMap" not in src, (
        "_firstBetMap voltou ao gestao.js: o custo volta a ser lançado no DIA da 1ª "
        "aposta e filtrar qualquer outro dia devolve R$ 0 (s322)"
    )


def test_a_janela_de_vida_le_liquidadas_e_abertas():
    """Só `DADOS` deixaria de fora a conta que tem aposta viva e nenhuma encerrada: ela
    leria como morta. É o ponto cego da s239 numa roupa nova."""
    src = _sem_comentarios(GESTAO.read_text(encoding="utf-8"))
    m = re.search(r"^function _buildContaVida\(\)\{.*?^\}", src, re.S | re.M)
    assert m, "_buildContaVida sumiu do gestao.js"
    assert "DADOS_ABERTAS" in m.group(0), (
        "_buildContaVida parou de ler DADOS_ABERTAS: conta com aposta só em aberto "
        "passa a ler como morta e perde o custo"
    )


def test_o_custo_nao_deriva_mais_das_linhas_filtradas():
    """As duas telas de custo têm de perguntar o PERÍODO ao `_selRange`. Derivar do
    intervalo das linhas era o que encolhia um mês filtrado até a última aposta dele e
    zerava o custo em recorte sem aposta nenhuma."""
    for arq in (GESTAO, PERFORMANCE):
        src = _sem_comentarios(arq.read_text(encoding="utf-8"))
        assert "_selRange" in src, f"{arq.name} não consulta mais o período selecionado"
    ov = _sem_comentarios(OVERVIEW.read_text(encoding="utf-8"))
    assert "calcCostFiltered(rows)" not in ov, (
        "renderKPI voltou a passar `rows` ao calcCostFiltered — a janela é do PERÍODO, "
        "não do intervalo das linhas (s322)"
    )


def test_escopo_do_custo_ignora_esporte_e_tipster():
    """Casa e Operador descrevem a CONTA e recortam; Esporte e Tipster descrevem a
    APOSTA e não. A conta Bet365 custou R$ 900 quer se olhe tênis ou futebol."""
    src = _sem_comentarios(GESTAO.read_text(encoding="utf-8"))
    m = re.search(r"^function calcCostFiltered\([^)]*\)\{.*?^\}", src, re.S | re.M)
    assert m, "calcCostFiltered sumiu do gestao.js"
    corpo = m.group(0)
    assert "'ca_'" in corpo and "'op_'" in corpo, "o custo parou de respeitar casa/operador"
    assert "'sp_'" not in corpo and "'ti_'" not in corpo, (
        "esporte/tipster voltaram a recortar o custo de contas: filtrar 'Tênis' faz a "
        "conta deixar de custar (s322)"
    )


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
def test_prova_por_execucao_da_janela():
    r = subprocess.run(
        ["node", str(MJS)], capture_output=True, text=True, encoding="utf-8", cwd=str(RAIZ),
    )
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")


# ── Prova por MUTAÇÃO: quebra o código de propósito e exige vermelho ─────────
# Cada par (de, para) é uma reversão plausível da mudança. Verde aqui sem esta lista
# não provaria nada — foi assim que a s286/s287 pegaram dois falsos verdes.
MUTACOES = [
    (
        "janela vira 'só o INÍCIO dentro do período' (a régua velha)",
        "if(v.fim<de||v.ini>ate)return;",
        "if(v.ini<de||v.ini>ate)return;",
    ),
    (
        "para de ler as apostas em aberto",
        "(typeof DADOS_ABERTAS!=='undefined'&&DADOS_ABERTAS)?DADOS_ABERTAS:[]);",
        "[]);",
    ),
    (
        "ignora a data de compra do cadastro",
        "if(p.adquirida_em&&(!v.ini||p.adquirida_em<v.ini))v.ini=p.adquirida_em;",
        "",
    ),
    (
        "ignora o carimbo de arquivamento",
        "if(p.arquivada_em){if(!v.fim||p.arquivada_em>v.fim)v.fim=p.arquivada_em;}",
        "if(false){}",
    ),
    (
        "conta ativa e ainda sem aposta deixa de valer até hoje",
        "else if(!p.arquivado&&!v.fim)v.fim=hoje;",
        "",
    ),
    (
        "o filtro de casa deixa de recortar o custo",
        "if(casasSel&&casasSel.size&&!casasSel.has(casa))return;",
        "",
    ),
    (
        "o filtro de operador deixa de recortar o custo",
        "if(opsSel&&opsSel.size&&v.op&&!opsSel.has(v.op))return;",
        "",
    ),
    (
        "conta sem custo cadastrado passa a entrar na contagem",
        "if(!(custoPorConta>0))return;",
        "",
    ),
    (
        "'Tudo' deixa de significar o parque inteiro (janela nasce vazia)",
        "range?range.from:'0000-01-01', range?range.to:'9999-12-31'",
        "range?range.from:'9999-12-31', range?range.to:'0000-01-01'",
    ),
]


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
@pytest.mark.parametrize("titulo,de,para", MUTACOES, ids=[m[0] for m in MUTACOES])
def test_mutacoes_sao_detectadas(tmp_path, titulo, de, para):
    """Quebra o gestao.js de propósito e exige que o .mjs fique VERMELHO.

    A cópia estragada entra pelo `ALVO_GESTAO` — o .mjs recorta dela em vez do arquivo de
    produção, então a mutação é exercida pelo código real, não por uma reimplementação."""
    src = GESTAO.read_text(encoding="utf-8")
    assert src.count(de) == 1, (
        f"a âncora da mutação «{titulo}» não é única no gestao.js "
        f"({src.count(de)} ocorrência(s)) — atualize a lista MUTACOES"
    )
    alvo = tmp_path / "gestao.js"
    alvo.write_text(src.replace(de, para), encoding="utf-8")
    r = subprocess.run(
        ["node", str(MJS)], capture_output=True, text=True, encoding="utf-8",
        cwd=str(RAIZ), env={**__import__("os").environ, "ALVO_GESTAO": str(alvo)},
    )
    assert r.returncode != 0, (
        f"mutação «{titulo}» passou VERDE — o teste não detecta o que ele promete "
        "detectar. O defeito está no teste, não no código."
    )
