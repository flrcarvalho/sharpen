"""Gate da rota da Ficha Sharpen em modo sombra (`app/ficha.py`, s409).

O que tem de ser verdade:
  1. **Ficha recusada é GRAVADA com o motivo** (decisão do Feca, 11/10). Descartada, ela vira
     "faltou" sem causa na régua.
  2. **Casa e conta vêm da SESSÃO**, nunca do corpo. Ficha que diz outra casa é recusada.
  3. **Chave vazia = nada acontece**: a rota responde `ligada: false` e não grava.
  4. **`derivar` segue a regra da odd aprovada** (Ficha §3): aberta/L/V pela odd da casa;
     W/HW pela odd que fecha o retorno no centavo, a da casa primeiro; nenhuma fecha → retorno
     ÷ stake; cashout pelo dinheiro. E a data pelo MASTER_OUTPUT §4 e §4.0.1, em Brasília.

Os números das Fichas abaixo são de bilhetes REAIS da DEX Sport (o `1d15646f…` é o da medição
do pensamento, D1), não inventados.

Mutações provadas (aplicadas ao `ficha.py`, teste ao lado vermelho):
  1. recusada não é gravada (só aceitas vão ao `gravar`)    → test_ficha_recusada_e_gravada…
  2. a casa vem da Ficha e não da sessão                    → test_a_casa_e_a_da_sessao…
  3. chave ignorada (grava sempre)                          → test_chave_desligada_nao_grava
  4. desempate da ganha prefere o produto à odd da casa     → test_quando_as_duas_fecham…
  5. W que nenhuma odd fecha fica com a odd da casa         → test_ganha_que_nenhuma_odd_fecha…
  6. HW medido com a fórmula de W                           → test_meia_vitoria_usa_a_formula…
  7. perdida pelo produto das pernas                        → test_perdida_usa_a_odd_da_casa…
  8. data em UTC, sem passar para Brasília                  → test_data_e_em_brasilia
 10. número float aceito                                    → test_numero_como_float_e_recusado
 11. moeda ausente recusada                                 → test_moeda_ausente_nao_recusa
 12. `derivar` sem a trava de status desconhecido           → test_derivar_recusa_status…

MUTAÇÃO INÓCUA, registrada e sem asserção inventada: tirar o `< d` da perna perdida
(`_data`). A data geral é a da perna MAIS RECENTE e a perdida é uma das pernas, então ela
nunca é posterior: o "nunca anda para frente" do MASTER_OUTPUT §4.0.1 já vale pela
aritmética. A trava fica porque descreve a regra; o teste da data que fica é comportamento.
A mutação 6 escapou na 1ª rodada, e o defeito era do teste: as duas fórmulas davam a mesma
resposta no caso montado.

O QUE NÃO COBRE: o INSERT (SQL; o `gravar` é dublado) e a extensão, que ainda não manda Ficha.
"""
import asyncio
import copy
import sys

sys.path.insert(0, "app")

import pytest  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import ficha  # noqa: E402

_DEX = {
    "versao": "ficha/1", "casa": "DEXSPORT", "codigo": "1d15646f-c666-4fe6-a4c9-f73545f59ebd",
    "colocada_em": "2026-10-06T13:23:30Z", "liquidada_em": "2026-10-06T16:00:00Z",
    "status": "ganha", "status_casa": "result 1 · status 3 · settlementStatus 1",
    "moeda": "USDT", "stake": "40", "odd": "3.97", "odd_calculada": False,
    "retorno": "158.80", "tipo": "multipla", "sistema": None,
    "pernas": [
        {"evento": "Azerbaiyán Sub-21 vs Gibraltar Sub-21", "mercado_casa": "Total. 2da mitad",
         "selecao_casa": "Debajo 1.5", "odd": "2.28", "inicio": "2026-10-06T13:45:00Z",
         "status_perna": "ganha"},
        {"evento": "India vs Uruguay", "mercado_casa": "Total de Uruguay. 2da mitad",
         "selecao_casa": "Encima 1.5", "odd": "1.74", "inicio": "2026-10-06T14:00:00Z",
         "status_perna": "ganha"},
    ],
    "impressao": "a1b2c3", "origem": "extensao:dx_inject@0.7.51",
}


def _f(**troca):
    f = copy.deepcopy(_DEX)
    f.update(troca)
    return f


# ── validação ─────────────────────────────────────────────────────────────────────────

def test_ficha_real_da_dex_e_aceita():
    assert ficha.validar(_DEX, "DEXSPORT") == []


def test_numero_como_float_e_recusado():
    """Ficha §2: número viaja como TEXTO. Float perde centavo antes de chegar aqui."""
    assert any("stake" in m for m in ficha.validar(_f(stake=40.0), "DEXSPORT"))


def test_status_desconhecido_e_recusado_e_nunca_chutado():
    assert any("status desconhecido" in m for m in ficha.validar(_f(status="won"), "DEXSPORT"))


def test_data_sem_fuso_e_recusada():
    assert any("colocada_em" in m for m in
               ficha.validar(_f(colocada_em="2026-10-06T13:23:30"), "DEXSPORT"))


def test_ganha_sem_retorno_e_recusada():
    assert any("sem retorno" in m for m in ficha.validar(_f(retorno=None), "DEXSPORT"))


def test_moeda_ausente_nao_recusa():
    """Decisão do Feca (D0, pergunta 5): vale a moeda da conta."""
    assert ficha.validar(_f(moeda=None), "DEXSPORT") == []


def test_perna_sem_odd_e_recusada():
    f = _f()
    f["pernas"][1]["odd"] = ""
    assert any("perna 2" in m for m in ficha.validar(f, "DEXSPORT"))


# ── derivação: a odd (regra aprovada pelo Feca, 11/10) ────────────────────────────────

def test_ganha_fica_com_a_odd_que_fecha_o_retorno():
    d = ficha.derivar(_DEX)
    assert (d["resultado"], d["odd"], d["stake"]) == ("W", "3,97", "40")


def test_casa_que_arredonda_a_odd_cede_para_o_produto_que_fecha():
    """A casa mostra 3,97 e pagou pela odd cheia: 40 × 3,9672 = 158,69."""
    assert ficha.derivar(_f(retorno="158.69"))["odd"] == "3,9672"


def test_quando_as_duas_fecham_vale_a_da_casa():
    """Retorno 195,53 com stake 99: `1,975` (casa) e o produto `1,97505` (pernas inventadas
    para fechar também) pagam o mesmo centavo. Vale a da casa."""
    f = _f(stake="99", odd="1.975", retorno="195.53")
    f["pernas"] = [dict(_DEX["pernas"][0], odd="1.97505")]
    assert ficha.derivar(f)["odd"] == "1,975"


def test_ganha_que_nenhuma_odd_fecha_vira_retorno_sobre_stake():
    assert ficha.derivar(_f(retorno="158.75"))["odd"] == "3,96875"


def test_meia_vitoria_usa_a_formula_de_hw():
    """`(100/2) × 1,95 + 50 = 147,50` fecha; a da casa (1,96) não. Só a fórmula de HW
    separa as duas: pela de W, nenhuma fecharia e ficaria a da casa."""
    f = _f(status="meio_ganha", stake="100", odd="1.96", retorno="147.50")
    f["pernas"] = [dict(_DEX["pernas"][0], odd="1.95")]
    d = ficha.derivar(f)
    assert (d["resultado"], d["odd"]) == ("HW", "1,95")


def test_perdida_usa_a_odd_da_casa_e_nao_o_produto():
    """ComboBOOST da Betpanda: a casa paga 8,918; o produto das pernas dá 8,494."""
    f = _f(status="perdida", retorno=None, odd="8.918")
    f["pernas"] = [dict(_DEX["pernas"][0], odd=o) for o in ("2.04", "1.91", "2.18")]
    d = ficha.derivar(f)
    assert (d["resultado"], d["odd"]) == ("L", "8,918")


def test_derivar_recusa_status_desconhecido_em_vez_de_chutar():
    """Sem esta trava, `meia_ganha` (grafia errada) virava cashout calado: W @ retorno ÷
    stake. Foi um erro de digitação neste próprio teste que mostrou o buraco."""
    with pytest.raises(ValueError):
        ficha.derivar(_f(status="meia_ganha"))


def test_cashout_decide_pelo_dinheiro():
    d = ficha.derivar(_f(status="cashout", retorno="50.00"))
    assert (d["resultado"], d["odd"]) == ("W", "1,25")
    d = ficha.derivar(_f(status="cashout", retorno="40.00"))
    assert (d["resultado"], d["odd"]) == ("V", "3,97")


# ── derivação: a data ─────────────────────────────────────────────────────────────────

def test_data_e_em_brasilia():
    """02:00 UTC do dia 10 são 23:00 do dia 09 em Brasília."""
    f = _f(status="aberta", retorno=None)
    f["pernas"] = [dict(_DEX["pernas"][0], inicio="2026-10-10T02:00:00Z")]
    assert ficha.derivar(f)["data"] == "09/10/2026"


def test_multipla_e_a_perna_mais_recente():
    assert ficha.derivar(_f(status="aberta", retorno=None))["data"] == "06/10/2026"
    f = _f(status="aberta", retorno=None)
    f["pernas"][1]["inicio"] = "2026-10-08T14:00:00Z"
    assert ficha.derivar(f)["data"] == "08/10/2026"


def test_multipla_perdida_e_a_perna_perdida_mais_cedo():
    f = _f(status="perdida", retorno=None)
    f["pernas"][0].update(inicio="2026-10-04T14:00:00Z", status_perna="perdida")
    f["pernas"][1]["inicio"] = "2026-10-08T14:00:00Z"
    assert ficha.derivar(f)["data"] == "04/10/2026"


def test_perna_perdida_nunca_anda_a_data_para_frente():
    f = _f(status="perdida", retorno=None)
    f["pernas"][0].update(inicio="2026-10-04T14:00:00Z", status_perna="ganha")
    f["pernas"][1].update(inicio="2026-10-06T14:00:00Z", status_perna="perdida")
    f["pernas"].append(dict(_DEX["pernas"][0], inicio="2026-10-02T14:00:00Z",
                            status_perna="ganha"))
    # a mais recente é 06/10 e a perdida é 06/10: fica 06/10
    assert ficha.derivar(f)["data"] == "06/10/2026"


def test_sem_inicio_e_a_colocacao():
    f = _f(status="aberta", retorno=None)
    for p in f["pernas"]:
        p["inicio"] = None
    assert ficha.derivar(f)["data"] == "06/10/2026"


# ── a rota ────────────────────────────────────────────────────────────────────────────

class _Sessao:
    dono, casa_key, parceiro = "Feca", "DEXSPORT", "Feca [Eu]"


@pytest.fixture
def cliente(monkeypatch):
    gravados = []

    async def _gravar(dono, casa_key, parceiro, versao, origem, registros):
        gravados.append({"dono": dono, "casa": casa_key, "parceiro": parceiro,
                         "registros": registros})
        return len(registros)

    monkeypatch.setattr(ficha, "gravar", _gravar)
    monkeypatch.setattr(ficha._captura, "sessao_por_token",
                        lambda t: _Sessao() if t == "ok" else None)
    monkeypatch.setattr(ficha._captura, "registrar_versao", lambda s, v: None)
    monkeypatch.setenv("FICHA_SOMBRA_CASAS", "DEXSPORT")
    app = FastAPI()
    app.include_router(ficha.router)
    return TestClient(app), gravados


def test_token_invalido_e_401_e_nao_grava(cliente):
    c, gravados = cliente
    r = c.post("/captura/ficha", json={"token": "x", "fichas": [_DEX]})
    assert r.status_code == 401 and gravados == []


def test_chave_desligada_nao_grava(cliente, monkeypatch):
    c, gravados = cliente
    monkeypatch.setenv("FICHA_SOMBRA_CASAS", "")
    r = c.post("/captura/ficha", json={"token": "ok", "fichas": [_DEX]})
    assert r.json() == {"ligada": False} and gravados == []


def test_ficha_aceita_e_gravada(cliente):
    c, gravados = cliente
    r = c.post("/captura/ficha", json={"token": "ok", "fichas": [_DEX]}).json()
    assert r["aceitas"] == 1 and r["recusadas"] == 0
    assert gravados[0]["registros"][0]["aceita"] is True


def test_ficha_recusada_e_gravada_com_o_motivo(cliente):
    c, gravados = cliente
    r = c.post("/captura/ficha", json={"token": "ok", "fichas": [_f(status="won")]}).json()
    assert r["recusadas"] == 1
    reg = gravados[0]["registros"][0]
    assert reg["aceita"] is False and any("status" in m for m in reg["motivos"])


def test_a_casa_e_a_da_sessao_nunca_a_da_ficha(cliente):
    c, gravados = cliente
    r = c.post("/captura/ficha", json={"token": "ok", "fichas": [_f(casa="MEGAPARI")]}).json()
    assert r["recusadas"] == 1
    assert gravados[0]["casa"] == "DEXSPORT" and gravados[0]["parceiro"] == "Feca [Eu]"


def test_ficha_vinda_do_site_de_outra_casa_e_recusada(cliente):
    c, gravados = cliente
    r = c.post("/captura/ficha", json={"token": "ok", "origem": "megapari.com",
                                       "fichas": [_DEX]}).json()
    assert r["recusadas"] == 1
    assert any("site" in m for m in gravados[0]["registros"][0]["motivos"])


def test_lote_que_nao_e_lista_e_400(cliente):
    c, _ = cliente
    assert c.post("/captura/ficha", json={"token": "ok", "fichas": {}}).status_code == 400


# ── o registro no main.py ─────────────────────────────────────────────────────────────

def test_main_registra_a_rota_e_a_isencao_de_csrf():
    import main
    assert "/captura/ficha" in main._CAPTURA_ISENTAS
    assert any(getattr(r, "path", "") == "/captura/ficha" for r in main.app.routes)
