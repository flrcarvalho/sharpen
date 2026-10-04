"""Moeda da conta no cadastro (s391, passo 2 de `docs/PLANO_MOEDA_POR_CONTA.md`).

O passo 1 (s390) criou `parceiros.moeda` e a conversão no `/salvar`, mas nada gravava a
coluna: toda conta era BRL. Aqui o cadastro passa a escolher BRL, USD ou USDT, na criação
e na edição, e a escolha sobe ao servidor no mesmo gesto.

Três camadas, três gates:

1. **Rota** (este arquivo): `POST /parceiros` e `POST /parceiros/{id}/editar` validam a
   moeda na FRONTEIRA. Ausente = None ("não mexe"); minúscula vira maiúscula; fora do
   `cambio.MOEDAS` = 400. Uma moeda que o câmbio não conhece faria toda captura da conta
   ser recusada por "sem cotação", com a conta parecendo normal.
2. **Banco** (`test_repository_db.py::test_moeda_no_cadastro_cria_lista_edita_e_reativa_sem_perder`,
   só no CI): grava, lista, edita só a moeda, e `None` preserva inclusive na reativação.
3. **Front** (`tests/js/moeda_conta_front.mjs`): executa as funções RECORTADAS do
   `index.html`. As mutações abaixo estragam uma cópia e exigem o vermelho.

Trocar a moeda vale DAQUI PARA FRENTE (decisão do Feca, 03/10/2026): nenhum bilhete é
reconvertido, e o modal avisa quantas apostas ficam como estão.

Mutações da ROTA, medidas à mão em 03/10/2026 (cada uma derrubou ao menos um teste
daqui): tirar o `.upper()` · tirar o `if m not in _cambio.MOEDAS` · a criação deixar de
repassar `moeda` · a edição deixar de repassar `moeda`. 4 de 4 detectadas.

O que NÃO está coberto: o visual do seletor e do aviso (medição headless) e o aviso de
captura que contradiz o cadastro, que é o passo 2b.
"""
import asyncio
import os
import shutil
import subprocess
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

import main
from main import ParceiroCriarRequest, ParceiroEditarRequest

RAIZ = Path(__file__).resolve().parent.parent
INDEX = RAIZ / "app" / "static" / "index.html"
MJS = RAIZ / "tests" / "js" / "moeda_conta_front.mjs"


# ── Rota ─────────────────────────────────────────────────────────────────────

def _criar(moeda):
    body = ParceiroCriarRequest(casa="Dex Sport", nome="Feca", moeda=moeda)
    with patch.object(main, "casa_canonica", AsyncMock(side_effect=lambda n: n)), \
         patch.object(main, "criar_parceiro", AsyncMock(return_value={"id": 1})) as cp:
        asyncio.run(main.criar_parceiro_route(body, dono="Feca"))
    return cp.call_args[0]


def _editar(moeda):
    body = ParceiroEditarRequest(nome="Feca", moeda=moeda)
    with patch.object(main, "editar_parceiro", AsyncMock(return_value={"ok": True})) as ed:
        asyncio.run(main.editar_parceiro_route(7, body, dono="Feca"))
    return ed.call_args[0]


def test_criar_repassa_a_moeda_normalizada():
    assert _criar("usdt")[3] == "USDT"
    assert _criar("USD")[3] == "USD"
    # s392: Bet365 da Austrália e da Argentina, e conta em euro.
    assert _criar("aud")[3] == "AUD"
    assert _criar("EUR")[3] == "EUR"
    assert _editar("ars")[5] == "ARS"


def test_criar_sem_moeda_repassa_none():
    # None, e não "BRL": é o que deixa a reativação de conta arquivada manter a moeda.
    assert _criar(None)[3] is None
    assert _criar("  ")[3] is None


def test_editar_repassa_a_moeda_e_ausente_nao_mexe():
    assert _editar("usdt")[5] == "USDT"
    assert _editar(None)[5] is None


@pytest.mark.parametrize("ruim", ["JPY", "GTQ", "R$", "$", "Tether"])
def test_moeda_fora_da_lista_e_400_nas_duas_rotas(ruim):
    for chamada in (_criar, _editar):
        with pytest.raises(HTTPException) as e:
            chamada(ruim)
        assert e.value.status_code == 400


# ── Front ────────────────────────────────────────────────────────────────────

@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
def test_front_por_execucao():
    r = subprocess.run(["node", str(MJS)], capture_output=True, text=True,
                       encoding="utf-8", cwd=str(RAIZ))
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")


# (título, trecho original, trecho estragado)
MUTACOES = [
    (
        "o POST de criar deixa de levar a moeda",
        "body: JSON.stringify({ casa: f.casa, nome: f.nome, moeda: f.moeda }) });",
        "body: JSON.stringify({ casa: f.casa, nome: f.nome }) });",
    ),
    (
        "o POST de editar deixa de levar a moeda",
        "adquirida_em: f.adq || undefined, moeda: f.moeda }),",
        "adquirida_em: f.adq || undefined }),",
    ),
    (
        "a leitura do formulário crava BRL",
        "  const moeda = (document.getElementById('nc-moeda') || {}).value || 'BRL';\n"
        "  return { novo,",
        "  const moeda = 'BRL';\n"
        "  return { novo,",
    ),
    (
        "o seletor não grava o hidden",
        "  if (hid) hid.value = m || 'BRL';",
        "  if (hid) {}",
    ),
    (
        "o seletor acende todos os botões",
        "b.classList.toggle('on', b.dataset.moeda === (m || 'BRL'))",
        "b.classList.toggle('on', true)",
    ),
    (
        "a conta ativa não adota a moeda nova",
        "      parceiroSelecionado.moeda = f.moeda;\n",
        "",
    ),
    (
        "o aviso aparece também na criação",
        "  const mostra = _ncModo === 'editar' && !!_ncAlvo && m !== _ncAlvo.moeda && n !== 0;",
        "  const mostra = (_ncModo === 'editar' || !_ncAlvo) && (!_ncAlvo || (m !== _ncAlvo.moeda && n !== 0));",
    ),
    (
        "o aviso aparece com a moeda igual à salva",
        "  const mostra = _ncModo === 'editar' && !!_ncAlvo && m !== _ncAlvo.moeda && n !== 0;",
        "  const mostra = _ncModo === 'editar' && !!_ncAlvo && n !== 0;",
    ),
    (
        "o aviso aparece em conta sem aposta",
        "  const mostra = _ncModo === 'editar' && !!_ncAlvo && m !== _ncAlvo.moeda && n !== 0;",
        "  const mostra = _ncModo === 'editar' && !!_ncAlvo && m !== _ncAlvo.moeda;",
    ),
    (
        "o aviso some quando a contagem não chegou",
        "  const mostra = _ncModo === 'editar' && !!_ncAlvo && m !== _ncAlvo.moeda && n !== 0;",
        "  const mostra = _ncModo === 'editar' && !!_ncAlvo && m !== _ncAlvo.moeda && !!n;",
    ),
    (
        "a contagem do aviso perde o milhar pt-BR",
        "'As ' + n.toLocaleString('pt-BR') + ' apostas'",
        "'As ' + n + ' apostas'",
    ),
    (
        "a guarda de fechamento ignora o hidden marcado",
        "    .filter(el => el.hasAttribute('data-modal-campo')\n"
        "      ? (!!el.parentElement && el.parentElement.offsetParent !== null)\n",
        "    .filter(el => el.hasAttribute('data-modal-campo')\n"
        "      ? false\n",
    ),
    (
        "a guarda conta a moeda mesmo com o campo escondido",
        "      ? (!!el.parentElement && el.parentElement.offsetParent !== null)\n",
        "      ? true\n",
    ),
]


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
@pytest.mark.parametrize("titulo,de,para", MUTACOES, ids=[m[0] for m in MUTACOES])
def test_mutacoes_do_front_sao_detectadas(tmp_path, titulo, de, para):
    """Estraga uma cópia do `index.html` e exige que o .mjs fique VERMELHO."""
    src = INDEX.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert src.count(de) == 1, (
        f"a âncora da mutação «{titulo}» não é única no index.html "
        f"({src.count(de)} ocorrência(s)), atualize a lista MUTACOES"
    )
    estragado = tmp_path / "index.html"
    estragado.write_text(src.replace(de, para, 1), encoding="utf-8")
    env = {**os.environ, "ALVO_INDEX": str(estragado)}
    r = subprocess.run(["node", str(MJS)], capture_output=True, text=True,
                       encoding="utf-8", cwd=str(RAIZ), env=env)
    assert r.returncode != 0, (
        f"a mutação «{titulo}» passou despercebida, o gate não cobre esta regra.\n"
        + (r.stdout or "")
    )


def test_seletor_cambio_e_formato_oferecem_as_mesmas_moedas():
    """s392: as três pontas da moeda andam juntas. Botão sem fonte de câmbio faz toda
    captura da conta ser recusada; moeda sem formato na tela some da sub-linha sem aviso
    (o `fmtMoedaOrig` devolve '' para a moeda que não conhece)."""
    import re
    import cambio
    src = INDEX.read_text(encoding="utf-8")
    seletor = src[src.index('id="nc-moeda-seg"'):]
    seletor = seletor[:seletor.index("</div>")]
    assert tuple(re.findall(r'data-moeda="([A-Z]+)"', seletor)) == cambio.MOEDAS
    linha = re.search(r"const _MOEDA_ORIG = \{(.*?)\};", src).group(1)
    assert set(re.findall(r"([A-Z]{3,4}): \{", linha)) == set(cambio.MOEDAS) - {"BRL"}
    app = (RAIZ / "app" / "static" / "dash" / "assets" / "js" / "app.js").read_text(encoding="utf-8")
    linha_app = re.search(r"const _MOEDA_ORIG=\{(.*?)\};", app).group(1)
    assert set(re.findall(r"([A-Z]{3,4}):\{", linha_app)) == set(cambio.MOEDAS) - {"BRL"}
