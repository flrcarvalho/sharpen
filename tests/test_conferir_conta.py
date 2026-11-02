"""D44 (Feca, 01/11/2026): "Conferir conta com a casa" — o núcleo puro (`app/conferir_conta.py`).

O caminho com banco (rota, `correcoes`, edição de sempre) está em `tests/test_repository_db.py`
(`test_d44_*`). Aqui: o lado da casa sai do cru real da fixture do harness (Sportsbet.io
`6add3525`, 30,01 @ 4,75, perdida), e as regras que decidem o que é oferecido.

Mutações provadas (aplicadas, teste ao lado vermelho; C6 no harness de banco):
  C1. o lado da casa perde o resultado               → o_lado_da_casa_sai_do_cru
  C2. correção humana deixa de bloquear              → correcao_humana_manda
  C3. moeda diferente passa a ser oferecida          → moeda_diferente_nao_se_oferece
  C4. stake de conta estrangeira gravada como R$     → stake_estrangeira_vai_pela_origem
  C5. o resultado corrigido sem a odd da casa        → resultado_leva_a_odd_junto
  C6. o aplicar ignora o "não oferecida"             → test_d44_correcao_humana_nao_e_desfeita
  C7. a correção do botão grava sem origem (humana)  → test_d44_correcao_do_botao_nao_trava
  C8. `campos_corrigidos` volta a contar o 'conferir' → test_d44_correcao_do_botao_nao_trava
  C10. sem o piso, centavo de P/L vira divergência  → piso_de_um_real_na_odd
  C11. cru aberto desmente linha liquidada          → cru_aberto_nao_desmente_liquidada
  C12. bônus volta a ser oferecido como odd        → bonus_nao_e_odd
  C13. cashout abaixo da odd passa por bônus        → bonus_nao_e_odd
  C13b (sem a trava de status) é INÓCUA: cashout nunca paga acima de stake × odd, e a trava
       do retorno já o barra. Fica como defesa; registrado, sem asserção inventada.
  C9. o cru recusado conta como conferido            → ficha_com_motivo_nao_e_conferida

O QUE NÃO COBRE: a leitura do banco e a escrita (harness de banco); a tela (ainda não existe).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "app")

import conferir_conta as cc  # noqa: E402
import ficha  # noqa: E402
from adaptadores import sbi  # noqa: E402

_FIX = Path(__file__).resolve().parent.parent / "extensor" / "harness" / "fixtures"
CRUS = {sbi.codigo(c): c for c in sbi.bilhetes_da_resposta(
    json.loads((_FIX / "sportsbetio.settled.json").read_text(encoding="utf-8")))}
COD = "6add3525bf9e9d0001ae48c4"


def _casa():
    f, motivos = ficha.montar_ficha("sbi", CRUS[COD], "SPORTSBETIO")
    assert motivos == []
    return cc.lado_da_casa(f, "BRL")


def _b(**kw):
    base = {"id": 7, "codigo_bilhete": COD, "stake": "30,01", "odd": "4,75", "resultado": "L",
            "descricao": "x", "moeda": None, "stake_orig": None, "data": "25/10/2026"}
    base.update(kw)
    return base


def test_o_lado_da_casa_sai_do_cru():
    assert _casa() == {"stake": "30,01", "odd": "4,75", "resultado": "L", "moeda": "BRL"}


def test_linha_igual_a_casa_nao_diverge():
    assert cc.comparar_linha(_b(), _casa(), set()) is None
    assert cc.comparar_linha(_b(stake="30,010"), _casa(), set()) is None


def test_resultado_divergente_e_oferecido():
    d = cc.comparar_linha(_b(resultado="W"), _casa(), set())
    assert d["campos"] == ["resultado"] and d["oferecida"] and d["motivo"] is None
    assert d["banco"]["resultado"] == "W" and d["casa"]["resultado"] == "L"


def test_odd_so_conta_onde_muda_o_dinheiro():
    """Perdida: a odd não muda o P/L (−stake), então odd diferente não é divergência."""
    assert cc.comparar_linha(_b(odd="9,99"), _casa(), set()) is None
    w = {"stake": "10,00", "odd": "2,00", "resultado": "W", "moeda": "BRL"}
    assert cc.comparar_linha(_b(stake="10,00", odd="2", resultado="W"), w, set()) is None
    assert cc.comparar_linha(_b(stake="10,00", odd="1,90", resultado="W"), w, set())["campos"] == ["odd"]


def test_correcao_humana_manda():
    d = cc.comparar_linha(_b(resultado="W"), _casa(), {"resultado"})
    assert not d["oferecida"] and d["motivo"] == "corrigida à mão"
    # correção num campo que NÃO diverge não bloqueia o que diverge
    assert cc.comparar_linha(_b(resultado="W"), _casa(), {"stake"})["oferecida"]


def test_moeda_diferente_nao_se_oferece():
    d = cc.comparar_linha(_b(moeda="USDT", stake_orig=30.01, stake="150,05"), _casa(), set())
    assert "moeda" in d["campos"] and not d["oferecida"] and d["motivo"] == "moeda diferente"


def test_stake_estrangeira_vai_pela_origem():
    casa = {"stake": "12,00", "odd": "2,00", "resultado": "L", "moeda": "USDT"}
    p = cc.patch_da_correcao(_b(moeda="USDT", stake_orig=10.0), casa, ["stake"])
    assert p == {"stake_orig": "12,00"}
    assert cc.patch_da_correcao(_b(), casa, ["stake"]) == {"stake": "12,00"}


def test_conferir_conta_cada_caso():
    """O miolo sem banco (o mesmo que a medição de produção roda): sem cru, cru recusado,
    conferida e divergente, cada um na sua contagem."""
    cru_ruim = dict(CRUS[COD], stakeAmount=None)      # a Ficha recusa: sem stake
    usdt = {"moeda": "USDT", "stake_orig": 30.01, "stake": "150,05"}   # o cru é USDT
    linhas = [_b(id=1, **usdt), _b(id=2, codigo_bilhete="SEMCRU"),
              _b(id=3, codigo_bilhete="RUIM"), _b(id=4, resultado="W", **usdt)]
    crus = {COD: ("sbi", CRUS[COD]), "RUIM": ("sbi", cru_ruim)}
    out = cc.conferir(linhas, crus, {4: {"stake"}}, "USDT", "SPORTSBETIO")
    assert (out["conferidas"], out["sem_cru"], out["cru_recusado"]) == (2, 1, 1)
    assert [(d["id"], d["campos"], d["oferecida"]) for d in out["divergentes"]] == [
        (4, ["resultado"], True)]


def test_ficha_com_motivo_nao_e_conferida(monkeypatch):
    """Ficha montada mas com motivo de recusa não serve de prova, mesmo que o dinheiro se
    derive: entra em `cru_recusado`, nunca em `conferidas`."""
    f, _ = ficha.montar_ficha("sbi", CRUS[COD], "SPORTSBETIO")
    monkeypatch.setattr(cc._ficha, "montar_ficha", lambda *a: (f, ["perna sem jogo"]))
    out = cc.conferir([_b(resultado="W")], {COD: ("sbi", CRUS[COD])}, {}, "USDT", "SPORTSBETIO")
    assert (out["conferidas"], out["cru_recusado"], out["divergentes"]) == (0, 1, [])


def test_piso_de_um_real_na_odd():
    """Só a odd diverge e o P/L muda menos de 1,00: não é divergência (stake 18,8662713 da casa
    × 18,87 da linha). A partir de 1,00 é (o bônus de 1,29 da Vavada)."""
    casa = {"stake": "18,8662713", "odd": "3,875", "resultado": "W", "moeda": "BRL"}
    assert cc.comparar_linha(_b(stake="18,87", odd="3,875", resultado="W"), casa, set()) is None
    bonus = {"stake": "10", "odd": "7,6", "resultado": "W", "moeda": "BRL"}
    d = cc.comparar_linha(_b(stake="10,00", odd="7,471205", resultado="W"), bonus, set())
    assert d["campos"] == ["odd"] and d["oferecida"]


def test_cru_aberto_nao_desmente_liquidada():
    """O último cru guardado ainda está aberto e a linha já liquidou: o cru é de antes da
    liquidação e não prova nada. A linha aberta contra cru aberto confere normalmente."""
    aberto = dict(CRUS[COD], status="ACTIVE")
    f, motivos = ficha.montar_ficha("sbi", aberto, "SPORTSBETIO")
    assert motivos == [] and cc.lado_da_casa(f, "USDT")["resultado"] == ""
    usdt = {"moeda": "USDT", "stake_orig": 30.01, "stake": "150,05"}
    out = cc.conferir([_b(id=1, **usdt), _b(id=2, resultado="", **usdt)],
                      {COD: ("sbi", aberto)}, {}, "USDT", "SPORTSBETIO")
    assert (out["cru_aberto"], out["conferidas"], out["divergentes"]) == (1, 1, [])


def test_bonus_nao_e_odd(monkeypatch):
    """Feca, 02/11: a Vavada 5520005256 pagou 76 sobre 10 @ 7,471205 (bônus de 1,29). O banco tem
    a odd da casa: não é correção de odd, vai para `bonus`. Retorno ABAIXO de stake × odd
    (cashout) continua oferecido: ali o dinheiro gravado está errado de verdade."""
    f, _ = ficha.montar_ficha("sbi", CRUS[COD], "SPORTSBETIO")
    usdt = {"moeda": "USDT", "stake_orig": 10.0, "stake": "50,00"}
    linha = _b(odd="7,471205", resultado="W", **usdt)

    def com(status, retorno):
        g = dict(f, status=status, stake="10", odd="7.471205", retorno=retorno)
        monkeypatch.setattr(cc._ficha, "montar_ficha", lambda *a: (g, []))
        return cc.conferir([linha], {COD: ("sbi", CRUS[COD])}, {}, "USDT", "SPORTSBETIO")

    bonus = com("ganha", "76")
    assert (bonus["bonus"], bonus["conferidas"], bonus["divergentes"]) == (1, 0, [])
    cashout = com("cashout", "60")
    assert cashout["bonus"] == 0 and cashout["divergentes"][0]["oferecida"]
    a_menos = com("ganha", "60")                 # ganhou e pagou MENOS que stake × odd
    assert a_menos["bonus"] == 0 and a_menos["divergentes"][0]["oferecida"]


def test_resultado_leva_a_odd_junto():
    casa = {"stake": "10,00", "odd": "2,50", "resultado": "W", "moeda": "BRL"}
    assert cc.patch_da_correcao(_b(), casa, ["resultado"]) == {"resultado": "W", "odd": "2,50"}
    assert cc.patch_da_correcao(_b(), dict(casa, odd=None), ["resultado"]) == {"resultado": "W"}
