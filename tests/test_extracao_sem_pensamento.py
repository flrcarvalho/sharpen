"""Gate da chave `EXTRACAO_SEM_PENSAMENTO` (s409, Projeto Ficha Sharpen D1).

O Sonnet 5 pensa por padrão e o pensamento é faturado como saída (medido: 11.407 × 1.545
tokens por pedaço, `docs/PROJETO_FICHA_SHARPEN/DIARIO.md`). A chave desliga o pensamento
por casa, só em lote de TEXTO. Três coisas precisam ser verdade:

  1. **Chave vazia = nada muda.** É a garantia de que o deploy é inerte até alguém ligar.
  2. **Print e PDF nunca saem do padrão**, nem com `*`: não foram medidos sem pensamento.
  3. **TODA chamada do titular recebe a decisão**, inclusive as repescagens de cobertura
     e de fidelidade. Uma chamada esquecida não dá erro: só segue pensando e cobrando, e
     o pedaço que ela devolve vem de um regime diferente do resto do lote.

Mutações provadas (aplicadas ao `main.py`, teste ao lado vermelho):
  1. `_pensamento_kw` ignora a lista e devolve sempre disabled → test_chave_vazia…
  2. some a guarda de imagem/documento                       → test_print_e_pdf…
  3. a repescagem não repassa o `pensamento`                 → test_a_repescagem_da_cobertura…
  4. o paralelo esquece o `**(pensamento or {})` no stream     → test_toda_chamada_do_titular…
  5. o gerador não passa `pensamento=` ao sequencial           → test_o_gerador_passa_a_decisao…

O QUE ESTE GATE NÃO COBRE: não chama a API (custo e qualidade sem pensamento são
medidos pela régua de números, `app/sombra_numeros.py`, e pelo harness do projeto), e não
roda o `_stream_sequential`/`_stream_parallel` de ponta a ponta — ali a prova é por
leitura da árvore do código, não por execução.
"""
import ast
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, "app")

import main  # noqa: E402

_FONTE = (Path(__file__).resolve().parent.parent / "app" / "main.py").read_text(encoding="utf-8")
_ARVORE = ast.parse(_FONTE)
_TEXTO = [{"type": "text", "text": "[Código: AB1]\nStake: 10,00\n"}]


def _funcao(nome):
    for n in ast.walk(_ARVORE):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == nome:
            return n
    raise AssertionError(f"função {nome} sumiu do main.py")


# ── a decisão ─────────────────────────────────────────────────────────────────────────

def test_chave_vazia_nao_muda_nada(monkeypatch):
    monkeypatch.delenv("EXTRACAO_SEM_PENSAMENTO", raising=False)
    assert main._pensamento_kw("DEXSPORT", _TEXTO) == {}
    monkeypatch.setenv("EXTRACAO_SEM_PENSAMENTO", "")
    assert main._pensamento_kw("DEXSPORT", _TEXTO) == {}


def test_lista_de_casas_liga_so_as_casas_da_lista(monkeypatch):
    monkeypatch.setenv("EXTRACAO_SEM_PENSAMENTO", " dexsport , MEGAPARI")
    assert main._pensamento_kw("DEXSPORT", _TEXTO) == {"thinking": {"type": "disabled"}}
    assert main._pensamento_kw("megapari", _TEXTO) == {"thinking": {"type": "disabled"}}
    assert main._pensamento_kw("BET365", _TEXTO) == {}


def test_asterisco_liga_todas(monkeypatch):
    monkeypatch.setenv("EXTRACAO_SEM_PENSAMENTO", "*")
    assert main._pensamento_kw("QUALQUER", _TEXTO) == {"thinking": {"type": "disabled"}}


def test_print_e_pdf_seguem_com_o_padrao_mesmo_com_asterisco(monkeypatch):
    monkeypatch.setenv("EXTRACAO_SEM_PENSAMENTO", "*")
    imagem = [{"type": "image", "source": {}}] + _TEXTO
    pdf = [{"type": "document", "source": {}}] + _TEXTO
    assert main._pensamento_kw("DEXSPORT", imagem) == {}
    assert main._pensamento_kw("DEXSPORT", pdf) == {}


def test_devolve_copia_e_nao_o_dict_compartilhado(monkeypatch):
    monkeypatch.setenv("EXTRACAO_SEM_PENSAMENTO", "*")
    kw = main._pensamento_kw("DEXSPORT", _TEXTO)
    kw["thinking"] = {"type": "enabled"}
    assert main._pensamento_kw("DEXSPORT", _TEXTO) == {"thinking": {"type": "disabled"}}


# ── a decisão chega a toda chamada ────────────────────────────────────────────────────

class _Stream:
    def __init__(self, registro, kw):
        registro.append(kw)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    @property
    def text_stream(self):
        async def _g():
            yield "```tsv\n```"
        return _g()

    async def get_final_message(self):
        class _U:
            input_tokens = output_tokens = 0
            cache_read_input_tokens = cache_creation_input_tokens = 0

        class _M:
            usage = _U()
        return _M()


class _Cliente:
    def __init__(self):
        self.chamadas = []

        class _Msgs:
            def stream(_s, **kw):
                return _Stream(self.chamadas, kw)
        self.messages = _Msgs()


def test_a_repescagem_da_cobertura_recebe_a_decisao(monkeypatch):
    """Execução de verdade: um bilhete falta, a cobertura repesca, e a chamada leva o
    `thinking`. É o caminho que um esquecimento deixaria pensando em silêncio."""
    cli = _Cliente()
    monkeypatch.setattr(main, "_client", cli)
    texto = "[Código: AB1]\nStake: 10,00\n\n[Código: AB2]\nStake: 20,00\n"
    resultado = "```tsv\n" + "\t".join(["01/10/2026"] + [""] * 9 + ["AB1"]) + "\n```"
    kw = {"thinking": {"type": "disabled"}}
    asyncio.run(main._garantir_cobertura([], resultado, texto, "m", {"type": "text", "text": "i"},
                                         False, kw))
    assert cli.chamadas, "a cobertura deveria ter repescado o AB2"
    assert all(c.get("thinking") == {"type": "disabled"} for c in cli.chamadas)
    # e sem decisão, nenhum `thinking` entra (o padrão do modelo)
    cli.chamadas.clear()
    asyncio.run(main._garantir_cobertura([], resultado, texto, "m", {"type": "text", "text": "i"},
                                         False))
    assert cli.chamadas and all("thinking" not in c for c in cli.chamadas)


def test_toda_chamada_do_titular_espalha_o_pensamento():
    """Cada `messages.stream` do caminho de hoje leva `**(pensamento or {})`."""
    for nome in ("_repescar_faltantes", "_stream_sequential", "_stream_parallel"):
        chamadas = [n for n in ast.walk(_funcao(nome))
                    if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                    and n.func.attr == "stream"]
        assert chamadas, f"{nome} não chama mais messages.stream?"
        for c in chamadas:
            espalhados = [ast.unparse(k.value) for k in c.keywords if k.arg is None]
            assert "pensamento or {}" in espalhados, f"{nome}: stream sem a decisão"


def test_cobertura_e_fidelidade_recebem_a_decisao_de_quem_chama():
    for nome in ("_stream_sequential", "_stream_parallel", "_garantir_cobertura",
                 "_garantir_fidelidade"):
        alvos = [n for n in ast.walk(_funcao(nome)) if isinstance(n, ast.Call)
                 and isinstance(n.func, ast.Name)
                 and n.func.id in ("_garantir_cobertura", "_garantir_fidelidade",
                                   "_repescar_faltantes")]
        assert alvos, nome
        for c in alvos:
            nomes = [ast.unparse(a) for a in c.args] + [ast.unparse(k.value) for k in c.keywords]
            assert "pensamento" in nomes, f"{nome} chama {c.func.id} sem repassar o pensamento"


def test_o_gerador_passa_a_decisao_aos_dois_caminhos():
    alvos = [n for n in ast.walk(_ARVORE) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Name)
             and n.func.id in ("_stream_sequential", "_stream_parallel")]
    assert len(alvos) >= 2
    for c in alvos:
        kws = {k.arg: ast.unparse(k.value) for k in c.keywords}
        assert kws.get("pensamento") == "_pensamento", f"{c.func.id} chamado sem pensamento="
