"""O feed do dashboard monta as linhas fora do event loop (s459, auditoria ESCALA A1).

Medido pelo auditor: 60 mil linhas = ~4,7 s de CPU no event loop por carga, e a tela de outro
usuário foi de 10 ms para 7,5 s enquanto isso. A transformação linha a linha agora roda numa
thread. Aqui o miolo é espiado: ele não pode ver um event loop rodando.

O que NÃO está coberto: o decode do asyncpg (`export_bilhetes`), que segue no loop, nem o
JSON/gzip da rota (também em thread, exercidos pelos testes da rota).
"""
import asyncio

import repository as R


def test_linhas_do_feed_rodam_numa_thread(monkeypatch):
    async def export(_dono):
        return [{"id": 1, "resultado": "W", "stake": "10", "odd": "2", "data": "01/11/2026",
                 "parceiro": "Conta [Forn]", "casa": "Betano"}]

    viu = {}
    original = R._linhas_do_feed

    def espiao(rows, dono):
        try:
            asyncio.get_running_loop()
            viu["no_loop"] = True
        except RuntimeError:
            viu["no_loop"] = False
        return original(rows, dono)

    monkeypatch.setattr(R, "export_bilhetes", export)
    monkeypatch.setattr(R, "_linhas_do_feed", espiao)
    out = asyncio.run(R.dashboard_rows(["TDonoFeed"]))
    assert viu == {"no_loop": False}, "a montagem do feed voltou para dentro do event loop"
    assert out and out[0]["lucro"] == 10.0 and out[0]["conta"] == "Conta"
