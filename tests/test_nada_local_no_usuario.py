"""Nada que o usuário DIGITA repousa no navegador (s366).

Regra do Feca, dita em termos absolutos: *"JAMAIS, JAMAIS JAMAIS DEVEMOS ARMAZENAR
CUSTO OU QUALQUER INFORMAÇÃO LOCALMENTE NOS USUARIOS"*. `localStorage` é cache
descartável; o lugar onde o dado repousa é o Postgres, escopado por dono.

**O que violava a regra, e estava vivo:** a trava anti-semeadura-parcial, em TRÊS
telas com a mesma forma — `if (serverBacked) push; else if (!hadLegacy) push;`. O
terceiro caso (**servidor vazio + legado no navegador**) não subia NADA: a pessoa
digitava um custo e ele ficava só na máquina, sem erro e sem aviso. Medido em
15/09/2026: 16 donos e 480 contas cadastradas estavam nesse estado.

A trava tinha um motivo real, e ele não desapareceu: o custo viveu anos só no
`localStorage`, então o mesmo dono pode ter conjuntos DIFERENTES em máquinas
diferentes, nenhum no servidor. Se a máquina com menos chaves escrever primeiro,
ela vira a verdade e a outra adota o conjunto menor na carga seguinte.

**A saída foi mover a defesa de lugar:** o front sobe sempre, e o 1º envio de um
navegador para um servidor sem custo vai com `semear=True`, que UNE em vez de
substituir. Assim o servidor só cresce na semeadura. A edição normal continua
substituindo, e tem de continuar: apagar um custo é tirar a chave do dict, e união
nenhuma apaga chave.

Dois gates, um por camada:
  · o front (as três funções de save) em `tests/js/dado_digitado_sobe_sempre.mjs`;
  · a união, aqui, exercitando as funções REAIS do `repository`.

O que NÃO está coberto: o SQL do `semear` do `salvar_custo_conta` (é `||` de jsonb,
e roda no Postgres — o harness de camada-DB o alcança, os testes de fórmula não), e
a carteira do Polymarket, que é leitura/escrita direta sem regra de merge.
"""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from repository import _unir_custo_geral, _unir_custo_tipster

RAIZ = Path(__file__).resolve().parent.parent
JS = RAIZ / "app" / "static" / "dash" / "assets" / "js"
ARQS = {
    "gestao": JS / "charts" / "gestao.js",
    "app": JS / "app.js",
    "extracao": RAIZ / "app" / "static" / "index.html",
}
MJS = RAIZ / "tests" / "js" / "dado_digitado_sobe_sempre.mjs"


# ── A união não pode ENCOLHER o que já está no servidor ──────────────────────

def test_a_uniao_de_tipster_preserva_mes_que_so_existe_de_um_lado():
    """O caso que a união existe para resolver: duas máquinas, meses diferentes.

    Unir só no primeiro nível (por tipster) trocaria o mapa inteiro e apagaria
    agosto — que é justamente o dado que a semeadura veio salvar."""
    velho = {"Só Chutes": {"2026-08": "500"}}
    novo = {"Só Chutes": {"2026-09": "600"}}
    assert _unir_custo_tipster(velho, novo) == {
        "Só Chutes": {"2026-08": "500", "2026-09": "600"}
    }


def test_na_uniao_de_tipster_o_novo_vence_no_mes_que_os_dois_tem():
    assert _unir_custo_tipster(
        {"Só Chutes": {"2026-09": "500"}},
        {"Só Chutes": {"2026-09": "700"}},
    ) == {"Só Chutes": {"2026-09": "700"}}


def test_a_uniao_de_tipster_nao_perde_quem_so_existe_de_um_lado():
    fora = _unir_custo_tipster({"A": {"2026-09": "1"}}, {"B": {"2026-09": "2"}})
    assert set(fora) == {"A", "B"}


def test_a_uniao_de_geral_casa_por_id_em_vez_de_concatenar():
    """`custo_geral` é uma LISTA de {id, tipo, values}: concatenar duplicaria a
    linha 'VPS' em vez de uni-la, e o total do dono dobraria."""
    fora = _unir_custo_geral(
        [{"id": 1, "tipo": "VPS", "values": {"2026-08": "120"}}],
        [{"id": 1, "tipo": "VPS", "values": {"2026-09": "130"}}],
    )
    assert len(fora) == 1
    assert fora[0]["values"] == {"2026-08": "120", "2026-09": "130"}


def test_a_uniao_de_geral_mantem_linha_que_so_existe_de_um_lado():
    fora = _unir_custo_geral(
        [{"id": 1, "tipo": "VPS", "values": {"2026-09": "120"}}],
        [{"id": 2, "tipo": "VPN", "values": {"2026-09": "30"}}],
    )
    assert sorted(l["id"] for l in fora) == [1, 2]


def test_linha_sem_id_entra_como_nova_em_vez_de_sumir():
    """Sem chave não há como decidir que é a mesma linha. Some é o erro caro;
    duplicar é visível e o dono corrige."""
    fora = _unir_custo_geral([{"tipo": "VPS", "values": {}}], [{"tipo": "VPN", "values": {}}])
    assert len(fora) == 2


def test_a_uniao_nao_muda_o_dicionario_que_recebeu():
    """Mutar o argumento faria o chamador gravar o que ele achava que só tinha lido."""
    velho = {"A": {"2026-08": "1"}}
    _unir_custo_tipster(velho, {"A": {"2026-09": "2"}})
    assert velho == {"A": {"2026-08": "1"}}


# ── O front sobe SEMPRE, provado por mutação ─────────────────────────────────

@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
def test_prova_por_execucao():
    r = subprocess.run(["node", str(MJS)], capture_output=True, text=True,
                       encoding="utf-8", cwd=str(RAIZ))
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")


# (título, arquivo, trecho original, trecho estragado)
MUTACOES = [
    # ── A TRAVA DE VOLTA, nas três telas ─────────────────────────────────────
    (
        "a trava volta ao custo por conta do dash",
        "gestao",
        "  const semear=!_custoServerBacked;\n"
        "  _custoServerBacked=true;\n"
        "  _custoPush(semear);",
        "  if(_custoServerBacked)_custoPush();\n"
        "  else if(!_custoHadLegacy){_custoServerBacked=true;_custoPush();}",
    ),
    (
        "a trava volta ao custo de tipster e geral",
        "app",
        "  const semear=!_ctServerBacked;\n"
        "  _ctServerBacked=true;\n"
        "  _ctPush(semear);",
        "  if(_ctServerBacked){_ctPush();return;}\n"
        "  if(!_ctHadLegacy){_ctServerBacked=true;_ctPush();}",
    ),
    (
        "a trava volta a tela de Extracao",
        "extracao",
        "    const semear = !_custoContaServerBacked;\n"
        "    _custoContaServerBacked = true;\n"
        "    fetch('/custos/conta',",
        "    const semear = !_custoContaServerBacked;\n"
        "    if (!_custoContaServerBacked && _custoContaHadLegacy) return;\n"
        "    _custoContaServerBacked = true;\n"
        "    fetch('/custos/conta',",
    ),
    # ── A UNIÃO: sem ela, tirar a trava abre o outro buraco ──────────────────
    (
        "o dash para de pedir uniao no 1o envio e a maquina menor vira a verdade",
        "gestao",
        "  const semear=!_custoServerBacked;",
        "  const semear=false;",
    ),
    (
        "o blob de tipster para de pedir uniao no 1o envio",
        "app",
        "  const semear=!_ctServerBacked;",
        "  const semear=false;",
    ),
    (
        "a Extracao para de pedir uniao no 1o envio",
        "extracao",
        "    const semear = !_custoContaServerBacked;",
        "    const semear = false;",
    ),
    (
        "o semear e pedido SEMPRE, e apagar um custo deixa de funcionar",
        "gestao",
        "function _custoPush(semear){try{fetch('/custos/conta',{method:'POST',"
        "headers:{'Content-Type':'application/json'},"
        "body:JSON.stringify({custo_conta:custoData,semear:!!semear})});}catch(e){}}",
        "function _custoPush(semear){try{fetch('/custos/conta',{method:'POST',"
        "headers:{'Content-Type':'application/json'},"
        "body:JSON.stringify({custo_conta:custoData,semear:true})});}catch(e){}}",
    ),
    # ── O QUE A TELA PROMETE ─────────────────────────────────────────────────
    (
        "a tela volta a dizer que o valor mora no navegador",
        "app",
        "Os valores ficam guardados na sua conta.",
        "Valores salvos permanentemente no navegador.",
    ),
    (
        "a carteira do Polymarket volta a ser lida do navegador",
        "extracao",
        "    if (w && !w.value) w.value = window.__polyWallet || '';",
        "    if (w && !w.value) w.value = localStorage.getItem('poly-wallet') || '';",
    ),
    # ── O DADO EM SI ─────────────────────────────────────────────────────────
    (
        "a Extracao passa a mandar so a chave editada e poda o legado",
        "extracao",
        "body: JSON.stringify({ custo_conta: o, semear })",
        "body: JSON.stringify({ custo_conta: { [forn + '||' + casa]: n }, semear })",
    ),
]


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
@pytest.mark.parametrize("titulo,arq,de,para", MUTACOES, ids=[m[0] for m in MUTACOES])
def test_mutacoes_sao_detectadas(tmp_path, titulo, arq, de, para):
    """Quebra o código de propósito e exige que o .mjs fique VERMELHO.

    A cópia estragada entra pelo `ALVO_GESTAO`/`ALVO_APP`/`ALVO_EXTRACAO` — o .mjs
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
