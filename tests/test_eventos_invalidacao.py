"""Invalidação pelo banco e LISTEN que volta avisando (s459, auditoria SERVIDOR P6 e P7).

P6: cada rota tinha de lembrar de derrubar o cache do matcher, e três que gravam tipster não
lembravam. Agora o `base_mudou` do banco (que todo escritor de `bilhetes` dispara) derruba os
caches do dono. P7: o que mudou enquanto o LISTEN estava caído não gerava aviso; ao reconectar,
toda tela aberta recarrega uma vez.

O que NÃO está coberto: o reconectar de verdade (exige derrubar um Postgres); aqui se exercita
a função que ele chama.
"""
import asyncio

import eventos
import matcher
import repository


def test_aviso_do_banco_derruba_os_caches_do_dono():
    matcher._CACHE["TDonoEv"] = ("modelo velho",)
    repository._CATEGORIAS_DONO["TDonoEv"] = (0, frozenset())
    matcher._CACHE["Outro"] = ("fica",)
    eventos._on_notify(None, 0, "base_mudou", "TDonoEv")
    assert "TDonoEv" not in matcher._CACHE, "o rótulo à mão seguiria com sugestão velha"
    assert "TDonoEv" not in repository._CATEGORIAS_DONO
    assert "Outro" in matcher._CACHE, "aviso de um dono não derruba o cache de outro"
    matcher._CACHE.pop("Outro", None)


def test_reconectar_avisa_toda_tela_aberta():
    async def body():
        a = eventos.assinar(["Ana"])
        b = eventos.assinar(["Bia", "Op1"])
        try:
            eventos._avisar_todos()
            return a[1].qsize(), b[1].qsize()
        finally:
            eventos.cancelar(a)
            eventos.cancelar(b)
    assert asyncio.run(body()) == (1, 1)
