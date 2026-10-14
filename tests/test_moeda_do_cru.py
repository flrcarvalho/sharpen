"""A moeda do CRU vence a da conta (s417, D30; 14/10/2026).

O caso: a conta da LavaPessoal na Megapari estava cadastrada em USDT, e o cru de 52 apostas
dizia `CurrencyCode: BRL` / `CurrencySymbol: R$`. O `/salvar` converteu pela moeda da CONTA:
`BetSum 75` virou 75 USDT × 5,0397 = R$ 377,98. Vale para a IA e para a Ficha, que passam
pelo mesmo `/salvar` (`main.gravar_tsv`).

A regra agora (`cambio.moeda_do_cru`, `ficha.moedas_do_cru_conn`, `main.gravar_tsv`):
  · o cru guardado de cada código (`captura_crua`, pelo adaptador da família) diz a moeda;
  · moeda do cru que não cabe na da conta → a linha vai na moeda do CRU, e o `/salvar` avisa
    apontando a conta e grava `alerta_moeda`;
  · cru sem moeda, `$` solto, ou moeda compatível (USD × USDT, Feca 04/10) → a da conta
    (regra 5A);
  · linha em real numa conta em dólar grava a origem explícita (`BRL`, cotação 1), e a Caixa
    da conta em dólar a deixa fora da soma (`n_sem_origem`), como já fazia com R$ sem origem.

O vigia (D28) compara as duas pontas na moeda da CASA (a `stake_orig` da Ficha × a stake que
a IA leu) e acusa `moeda` quando elas não são a mesma. Antes ele comparava R$ com USDT e dava
falso alarme em toda conta em dólar (Shuffle, MyStake, Duel e DEX em 14/10).

Mutações (s417, `scratchpad/mutar7.py`), cada uma derrubou ao menos um teste daqui:
  M1. o `/salvar` ignora a moeda do cru (`moedas_linha` vazio)      → test_cru_real_da_megapari…
  M2. `moeda_do_cru` devolve a do cru mesmo compatível (USD×USDT)    → test_funcoes_puras
  M3. `$` solto passa a valer como moeda do cru                      → test_funcoes_puras
  M4. linha em real numa conta em dólar sem a origem explícita       → test_converter_por_linha
  M5. a linha em outra moeda converte pela moeda da CONTA            → test_converter_por_linha
  M6. sem o alerta da moeda do cru                                   → test_cru_real_da_megapari…
  M7. sem gravar `alerta_moeda`                                      → test_cru_real_da_megapari…
  M8. o vigia compara a stake em R$ (sem a `stake_orig`)             → test_vigia_na_moeda_da_casa
  M9. o vigia não compara a moeda                                    → test_vigia_na_moeda_da_casa
  M10. o vigia dá à IA a moeda da conta, ignorando o cru             → test_vigia_registrar…
  M11. `moedas_do_cru_conn` lê o cru mais ANTIGO do código           → test_moedas_do_cru_conn…

O que NÃO está coberto: o SELECT real em `captura_crua` (dublado aqui; o harness de banco
não roda o adaptador) e a Caixa com uma linha `BRL` numa conta em dólar (a regra dela já é
`tests/test_caixa_moeda.py`: aposta sem origem NA MOEDA DA CONTA fica fora).
"""
import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import cambio
import ficha
import main
import virada
from main import SalvarRequest

RAIZ = Path(__file__).resolve().parent.parent
CRU = json.loads((RAIZ / "tests" / "ficha_cru_megapari_brl.json").read_text(encoding="utf-8"))
COD = "88778671191"


def _num(s):
    return float(s.replace(".", "").replace(",", ".")) if s else None


# ── funções puras ───────────────────────────────────────────────────────────────────────

def test_funcoes_puras():
    m = cambio.moeda_do_cru
    assert m("USDT", "BRL") == "BRL" and m("USDT", "R$") == "BRL" and m("USD", "brl") == "BRL"
    assert m("BRL", "USDT") == "USDT" and m("BRL", "USD") == "USD" and m("BRL", "US$") == "USD"
    assert m("USDT", "USD") is None and m("USD", "USDT") is None, "USD e USDT: vale a conta"
    assert m("USDT", "$") is None and m("BRL", "$") is None, "`$` solto é moeda ausente"
    assert m("BRL", "BRL") is None and m("BRL", "R$") is None
    assert m("USDT", None) is None and m("USDT", "") is None, "cru sem moeda: regra 5A"
    assert m("USDT", "XYZ") is None, "moeda sem cotação: vale a conta"
    assert m("USDT", "EUR") == "EUR"
    s = cambio.mesma_moeda
    assert s("USD", "USDT") and s("USDT", "$") and s(None, "BRL") and s("R$", "BRL")
    assert not s("USDT", "BRL") and not s(None, "USDT") and not s("EUR", "USD")


def test_converter_por_linha():
    rows = [{"codigo_bilhete": "1", "stake": "75,00", "data": "14/10/2026"},
            {"codigo_bilhete": "2", "stake": "10,00", "data": "14/10/2026"}]
    with patch.object(cambio, "cotacao", lambda moeda, iso: {"USDT": 5.0, "EUR": 6.0}[moeda]):
        ok, rec = cambio.converter_linhas([dict(r) for r in rows], "USDT", None, _num, {"1": "BRL"})
        assert rec == []
        assert ok[0]["stake"] == "75,00" and ok[0]["moeda"] == "BRL"
        assert ok[0]["cotacao"] == 1.0 and ok[0]["stake_orig"] == 75.0
        assert ok[1]["stake"] == "50,00" and ok[1]["moeda"] == "USDT" and ok[1]["cotacao"] == 5.0
        # conta em real, cru em euro: converte a linha pelo euro, a outra fica intocada
        ok, _ = cambio.converter_linhas([dict(r) for r in rows], "BRL", None, _num, {"2": "EUR"})
        assert ok[1]["stake"] == "60,00" and ok[1]["moeda"] == "EUR"
        assert ok[0]["stake"] == "75,00" and "moeda" not in ok[0], "real em conta real: no-op"
        # sem moeda do cru, nada muda
        assert cambio.converter_linhas([dict(r) for r in rows], "BRL", None, _num)[0] == rows


# ── o cru real da Megapari em BRL, conta cadastrada em USDT (item 5) ──────────────────────

class _ConnCru:
    def __init__(self, linhas):
        self.linhas = linhas

    async def fetch(self, sql, *a):
        assert "captura_crua" in sql and "ORDER BY codigo, recebido_em DESC" in sql
        return self.linhas


def test_moedas_do_cru_conn_le_a_moeda_pelo_adaptador():
    assert CRU["CurrencyCode"] == "BRL" and CRU["BetSum"] == 75
    conn = _ConnCru([{"codigo": COD, "familia": "x1", "cru": json.dumps(CRU)}])
    out = asyncio.run(ficha.moedas_do_cru_conn(conn, "LavaPessoal", "megapari", "Lava", [COD, ""]))
    assert out == {COD: "BRL"}
    assert asyncio.run(ficha.moedas_do_cru_conn(conn, "X", "MEGAPARI", "Y", [])) == {}


def _tsv_da_ficha():
    """A linha que a virada manda ao `/salvar` para este cru (a mesma rota da IA)."""
    f, motivos = ficha.montar_ficha("x1", CRU, "MEGAPARI")
    assert not motivos and f["moeda"] == "BRL"
    return virada.linha_tsv(f, "Megapari", "Lava", "Múltiplos", "Múltipla", "x")


def _salvar(moeda_conta, do_cru):
    conta = {"id": 7, "casa": "Megapari", "nome": "Lava", "arquivado": False, "moeda": moeda_conta}
    body = SalvarRequest(tsv=_tsv_da_ficha(), casa="Megapari", parceiro="Lava", parceiro_id=7)
    with patch.object(main, "get_parceiro", AsyncMock(return_value=conta)), \
         patch.object(main, "moedas_do_cru", AsyncMock(return_value=do_cru)) as mc, \
         patch.object(main, "registrar_alerta_moeda", AsyncMock(return_value=None)) as reg, \
         patch.object(main._cambio, "carregar", AsyncMock(return_value=None)), \
         patch.object(main._cambio, "cotacao", lambda m, iso: 5.0397), \
         patch.object(main, "upsert_bilhetes", AsyncMock(return_value=(1, 0, [9], [], {}))) as up, \
         patch.object(main, "auto_arquivar", AsyncMock(return_value=0)):
        res = asyncio.run(main.salvar(body, dono="LavaPessoal", dono_view="LavaPessoal"))
        asyncio.run(asyncio.sleep(0))
    gravadas = up.call_args[0][0] if up.call_args else []
    return res, gravadas, mc, reg


def test_cru_real_da_megapari_em_brl_na_conta_usdt_sai_75_em_brl_com_alerta():
    res, gravadas, mc, reg = _salvar("USDT", {COD: "BRL"})
    assert mc.call_args[0][:3] == ("LavaPessoal", "MEGAPARI", "Lava")
    assert COD in mc.call_args[0][3]
    g = gravadas[0]
    assert g["stake"] == "75,00", "a stake é a que a casa mostrou, em real"
    assert g["moeda"] == "BRL" and g["cotacao"] == 1.0 and g["stake_orig"] == 75.0
    av = [a for a in res["alertas"] if "mostrou BRL" in a]
    assert len(av) == 1 and "Lava" in av[0] and "cadastrada em USDT" in av[0], res["alertas"]
    assert reg.call_args is not None, "o alerta é gravado em `alerta_moeda`"
    assert reg.call_args[0] == ("LavaPessoal", "MEGAPARI", "Lava", "USDT", {COD: "BRL"})


def test_sem_moeda_no_cru_vale_a_conta():
    res, gravadas, _, reg = _salvar("USDT", {})
    assert gravadas[0]["stake"] == "377,98" and gravadas[0]["moeda"] == "USDT"
    assert reg.call_args is None and not [a for a in res["alertas"] if "mostrou" in a]


def test_cru_compativel_com_a_conta_nao_muda_nada():
    res, gravadas, _, reg = _salvar("USDT", {COD: "USD"})
    assert gravadas[0]["stake"] == "377,98" and gravadas[0]["moeda"] == "USDT"
    assert reg.call_args is None


# ── o vigia na moeda da casa (item 3) ───────────────────────────────────────────────────

def _bil(stake, odd, res, moeda, orig):
    return {"stake": stake, "odd": odd, "resultado": res, "descricao": "x",
            "moeda": moeda, "stake_orig": orig}


def test_vigia_na_moeda_da_casa():
    """O falso alarme da Shuffle (vigia_ficha id 4): Ficha R$ 329,29 = 66 USDT, IA 66,00."""
    f = virada._na_moeda_da_casa(_bil("329,29", "2,9590368", "L", "USDT", 66))
    assert f["stake"] == "66,00" and f["moeda"] == "USDT"
    ia = {"stake": "66,00", "odd": "2,9590368", "resultado": "L", "moeda": "USDT"}
    assert virada.vigia_comparar(f, ia) == []
    assert virada.vigia_comparar(f, dict(ia, moeda="USD")) == [], "USD e USDT são a mesma"
    # A LavaPessoal: Ficha gravou 75 USDT, a IA leu 75 do cru em real.
    f = virada._na_moeda_da_casa(_bil("377,98", "12,62", "", "USDT", 75))
    assert virada.vigia_comparar(f, {"stake": "75,00", "odd": "12,62", "resultado": "",
                                     "moeda": "BRL"}) == ["moeda"]
    # Conta em real, sem origem: a stake é a da planilha
    f = virada._na_moeda_da_casa(_bil("40", "1,9", "W", None, None))
    assert f == {"stake": "40", "odd": "1,9", "resultado": "W", "descricao": "x", "moeda": "BRL"}


class _ConnVigia:
    def __init__(self, conta, crus, bilhete):
        self.conta, self.crus, self.bilhete = conta, crus, bilhete
        self.gravado = []

    async def fetchval(self, sql, *a):
        assert "FROM parceiros" in sql
        return self.conta

    async def fetch(self, sql, *a):
        assert "captura_crua" in sql
        return self.crus

    async def fetchrow(self, sql, *a):
        assert "stake_orig" in sql
        return self.bilhete

    async def execute(self, sql, *a):
        self.gravado.append(a)


def test_vigia_registrar_da_a_ia_a_moeda_do_cru():
    tsv = "\t".join(["14/10/2026", "Múltiplos", "", "Megapari", "Lava", "Múltipla", "x",
                     "75,00", "12,627892", "", COD])
    cru = [{"codigo": COD, "familia": "x1", "cru": json.dumps(CRU)}]
    # Ficha gravada em USDT (o defeito): a IA, na moeda do cru, diz BRL → `moeda`
    conn = _ConnVigia("USDT", cru, _bil("377,98", "12,627892", None, "USDT", 75))
    assert asyncio.run(virada.vigia_registrar(conn, "LavaPessoal", "MEGAPARI", [COD], tsv, "Lava")) == 1
    assert conn.gravado[0][-1] == ["moeda"]
    assert json.loads(conn.gravado[0][4])["moeda"] == "BRL"
    # Ficha já em real: nada diverge
    conn = _ConnVigia("USDT", cru, _bil("75,00", "12,627892", None, "BRL", 75))
    assert asyncio.run(virada.vigia_registrar(conn, "LavaPessoal", "MEGAPARI", [COD], tsv, "Lava")) == 0
