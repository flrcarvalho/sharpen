"""A cotação de HOJE não fica presa na de ontem até o próximo deploy (s459, auditoria SERVIDOR P4).

O caso: a carga do PTAX marcava a faixa como coberta até HOJE mesmo antes de o BCB publicar o
fechamento do dia (~13h). Todo pedido seguinte achava "coberto" e caía no recuo (ontem). A
mesma aposta em USD virava R$ diferente conforme a hora do deploy. Roteiro do auditor, com o
BCB dublado e o código real do `polymarket.py`.

O que NÃO está coberto: o caminho EUR/AUD (`cambio._carregar_ptax_moeda`) usa as mesmas duas
funções (`_ate_coberto`/`_pode_esperar_hoje`), mas não é exercido aqui.
"""
import asyncio

import polymarket as poly

HOJE, ONTEM = "2026-11-17", "2026-11-16"


class _Resp:
    def __init__(self, v):
        self._v = v

    def json(self):
        return {"value": [{"dataHoraCotacao": d + " 13:00:00", "cotacaoVenda": c}
                          for d, c in sorted(self._v.items())]}


def test_hoje_e_buscado_de_novo_depois_que_o_bcb_publica(monkeypatch):
    publicado = {ONTEM: 5.40}
    chamadas = []

    async def get_fake(client, url, params=None, *a, **k):
        chamadas.append(params)
        return _Resp(dict(publicado))

    async def banco_gravar(*a, **k):
        return None

    relogio = {"t": 1000.0}
    monkeypatch.setattr(poly, "_hoje_iso", lambda: HOJE)
    monkeypatch.setattr(poly, "_get_retry", get_fake)
    monkeypatch.setattr(poly, "_ptax_banco_gravar", banco_gravar)
    monkeypatch.setattr(poly.time, "monotonic", lambda: relogio["t"])
    monkeypatch.setattr(poly, "_PTAX_MAPA", {})
    monkeypatch.setattr(poly, "_PTAX_DE", "")
    monkeypatch.setattr(poly, "_PTAX_ATE", "")
    monkeypatch.setattr(poly, "_PTAX_TENTATIVA", {})

    asyncio.run(poly._garantir_cobertura(None, HOJE))            # 10h
    assert poly._cotacao_do_mapa(HOJE) == 5.40                     # recuo: ontem
    assert poly._PTAX_ATE == ONTEM, "hoje sem fechamento não pode contar como coberto"

    publicado[HOJE] = 5.55                                         # 13h: BCB publica
    relogio["t"] += 60                                             # 1 min depois: espera
    asyncio.run(poly._garantir_cobertura(None, HOJE))
    assert len(chamadas) == 1, "não pode chamar o BCB a cada pedido enquanto hoje não sai"

    relogio["t"] += poly._REFAZ_HOJE_SEG + 1                       # passou o intervalo
    asyncio.run(poly._garantir_cobertura(None, HOJE))
    assert poly._cotacao_do_mapa(HOJE) == 5.55, "a cotação de hoje ficou presa na de ontem"
    assert poly._PTAX_ATE == HOJE
    n = len(chamadas)
    asyncio.run(poly._garantir_cobertura(None, HOJE))
    assert len(chamadas) == n, "com hoje publicado, não chama mais"
