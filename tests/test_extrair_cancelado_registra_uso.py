"""D50 (s465): extração que sai SEM o `done` registra o uso assim mesmo.

O caso (24/11/2026, Jaao26, Cloudbet): o `/extrair` mandou 5 pedaços à IA, os 5 voltaram, e o
cliente fechou a conexão antes do `done`. O Starlette cancelou o gerador num `yield` do laço;
`CancelledError` não é `Exception`, então nada pegou: zero linha no `uso_tokens`, zero no
`extracao_log`, zero log de erro. A conta da Anthropic cobrou as 5 chamadas.

Três coisas precisam ser verdade:
  1. Gerador fechado (`aclose`, o cliente que some) ou cancelado no meio do laço registra o uso.
  2. No paralelo, o registro ESPERA os pedaços que ainda estavam em voo: eles são tarefas
     próprias e seguem gastando depois do cancelamento.
  3. No caminho normal o uso é registrado UMA vez só (o `finally` não dobra a conta).

Mutações provadas (aplicadas ao `main.py`, teste ao lado vermelho):
  1. sem o `finally` do paralelo                          → test_par_cliente_fecha…, test_par_cancelado…
  2. o registro não espera as tarefas (sem `gather`)       → test_par_cliente_fecha…, test_par_cancelado…
  3. o registro não esvazia a fila                         → test_par_cliente_fecha…, test_par_cancelado…
  0. (o código de antes da s465 reprova os três testes de cancelamento)
  4. sem `registrado = True` no paralelo                   → test_par_caminho_normal…
  5. sem o `finally` do sequencial                         → test_seq_cliente_fecha…
  6. sem `registrado = True` no sequencial                 → test_seq_caminho_normal…

O QUE ESTE GATE NÃO COBRE: a chamada cortada no meio (o sequencial cancela a sua; a repescagem
em curso morre com o gerador) não entra na conta, porque a API não devolve o uso de um stream
interrompido e estimar seria inventar custo. Não roda o Starlette de verdade: o `aclose` e o
`cancel` simulam o que ele faz quando o cliente some. O `_stream_contrato` (desligado por
padrão) não foi tocado.
"""
import asyncio
import sys

sys.path.insert(0, "app")

import main  # noqa: E402

# Cada pedaço tem um número próprio por coluna, para a soma dizer QUEM entrou nela.
_USO = {"P0": 1, "P1": 10, "P2": 100}


class _Uso:
    def __init__(self, n):
        self.input_tokens = n
        self.output_tokens = 2 * n
        self.cache_read_input_tokens = 3 * n
        self.cache_creation_input_tokens = 0


class _Stream:
    def __init__(self, n, espera, parada):
        self.n, self.espera, self.parada = n, espera, parada

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    @property
    def text_stream(self):
        async def _g():
            await asyncio.sleep(self.espera)
            yield "```tsv\n```"
        return _g()

    async def get_final_message(self):
        class _M:
            pass
        m = _M()
        m.usage, m.stop_reason = _Uso(self.n), self.parada
        return m


class _Cliente:
    """Pedaço identificado pelo texto (`P0`…); o sequencial, pela ordem da chamada."""

    def __init__(self, esperas, paradas=None):
        self.esperas, self.paradas, self.n = esperas, paradas or {}, 0

        cli = self

        class _Msgs:
            def stream(_s, **kw):
                cli.n += 1
                txt = kw["messages"][0]["content"][0]["text"]
                return _Stream(_USO[txt] if txt in _USO else cli.n, cli.esperas.get(txt, 0),
                               cli.paradas.get(cli.n, "end_turn"))
        self.messages = _Msgs()


def _preparar(monkeypatch, cliente):
    registros = []

    async def _registrar(dono, casa, modelo, chunks, n_itens, tokens, caminho=None):
        registros.append(dict(tokens))

    async def _nada(*a, **k):
        return None

    monkeypatch.setattr(main, "_client", cliente)
    monkeypatch.setattr(main, "registrar_uso", _registrar)
    monkeypatch.setattr(main, "_sombra_e_semente", _nada)
    monkeypatch.setattr(main, "_barreira_lembrar", _nada)
    monkeypatch.setattr(main, "_sombra_vale_agora", lambda: False)
    return registros


async def _esperar_fundo():
    for _ in range(400):
        if not main._bg_tasks:
            return
        await asyncio.sleep(0.01)
    raise AssertionError("tarefa de fundo não terminou")


def _par():
    chunks = [[{"type": "text", "text": f"P{i}"}] for i in range(3)]
    return main._stream_parallel([{"type": "text", "text": "s"}], chunks, "m", 0,
                                 dono="d", casa="c", n_itens=3)


def _soma(*ns):
    t = sum(ns)
    return {"input": t, "output": 2 * t, "cache_read": 3 * t, "cache_write": 0}


def test_par_cliente_fecha_no_primeiro_progresso_registra_os_tres(monkeypatch):
    """O caso do Jaao26: o cliente some depois do 1º pedaço. Os outros dois ainda estão em
    voo e terminam DEPOIS do fechamento; os três entram na conta."""
    reg = _preparar(monkeypatch, _Cliente({"P0": 0, "P1": 0.15, "P2": 0.3}))

    async def run():
        g = _par()
        async for ev in g:
            if "chunk_progress" in ev:
                break
        await g.aclose()
        await _esperar_fundo()
    asyncio.run(run())
    assert reg == [_soma(1, 10, 100)], reg


def test_par_cancelado_no_meio_do_laco_registra(monkeypatch):
    """`CancelledError` enquanto o laço espera a fila (o Starlette cancelando a tarefa)."""
    reg = _preparar(monkeypatch, _Cliente({"P0": 0.1, "P1": 0.1, "P2": 0.1}))

    async def run():
        async def consumir():
            async for _ in _par():
                pass
        t = asyncio.create_task(consumir())
        await asyncio.sleep(0.02)
        t.cancel()
        try:
            await t
        except asyncio.CancelledError:
            pass
        await _esperar_fundo()
    asyncio.run(run())
    assert reg == [_soma(1, 10, 100)], reg


def test_par_caminho_normal_registra_uma_vez(monkeypatch):
    reg = _preparar(monkeypatch, _Cliente({}))

    async def run():
        evs = [ev async for ev in _par()]
        assert any('"done"' in e for e in evs)
        await _esperar_fundo()
    asyncio.run(run())
    assert reg == [_soma(1, 10, 100)], reg


def _seq():
    return main._stream_sequential([{"type": "text", "text": "s"}],
                                   [{"type": "text", "text": "X"}], "m", 0,
                                   dono="d", casa="c", n_itens=1)


def test_seq_cliente_fecha_na_continuacao_registra_a_parte_que_voltou(monkeypatch):
    """A 1ª parte volta com `max_tokens`; o cliente some no aviso de continuação. A parte 1
    entra; a 2ª nem começou."""
    reg = _preparar(monkeypatch, _Cliente({}, paradas={1: "max_tokens"}))

    async def run():
        g = _seq()
        async for ev in g:
            if "continuation" in ev:
                break
        await g.aclose()
        await _esperar_fundo()
    asyncio.run(run())
    assert reg == [_soma(1)], reg


def test_seq_caminho_normal_registra_uma_vez(monkeypatch):
    reg = _preparar(monkeypatch, _Cliente({}))

    async def run():
        evs = [ev async for ev in _seq()]
        assert any('"done"' in e for e in evs)
        await _esperar_fundo()
    asyncio.run(run())
    assert reg == [_soma(1)], reg
