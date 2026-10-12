"""Gate do cru (`app/cru.py`) e dos adaptadores (`app/adaptadores/`), s409.

Três coisas:
  1. **O filtro é por nome EXATO numa lista fechada** (decisão do Feca, 11/10). Os campos que a
     busca por pedaço de nome apagaria, e que são da aposta, sobrevivem; o código UUID da DEX
     e o nanoid da Shuffle sobrevivem (nada de "valor com cara de token").
  2. **Teste OBRIGATÓRIO do Feca:** em toda fixture da bancada com adaptador, a Ficha montada
     do cru FILTRADO é idêntica à do cru sem filtro. Adaptador novo sem fixture registrada
     aqui quebra o teste: a garantia não pode ficar para trás.
  3. **O adaptador da DEX bate com o gabarito lido NA TELA da casa** (recon de 03/10/2026, o
     mesmo do `extensor/harness/casos/dexsport.mjs`): odd, resultado, stake e data, passando
     pelo `ficha.derivar`, incluindo as armadilhas (perna anulada, perdida com perna ainda
     aberta, data em UTC).

Mutações provadas (aplicadas, teste ao lado vermelho):
  1. filtro por PEDAÇO do nome ("balance" in k)          → test_campos_da_aposta_sobrevivem
  2. filtro apaga valor com cara de token (UUID)          → test_codigo_uuid_e_nanoid_sobrevivem
  3. nome comparado com caixa (sem casefold)              → test_nome_exato_sem_caixa
  4. dx: odd da colocação também na ganha                 → test_dex_odd_da_casa_na_ganha… (escapou
     do teste de ponta a ponta na 1ª rodada: o `derivar` chega a 3,75 pelo dinheiro)
  5. dx: retorno zero vira perdida sem `result` 2         → test_dex_recusa_o_que_hoje_sobe_a_conferir
  6. dx: `amount` float sem cortar o ruído                → test_numero_corta_o_ruido_do_float
  7. adaptador registrado sem fixture no teste obrigatório → test_todo_adaptador_tem_fixture
  8. lista do servidor sem `Player`/`nickname`             → test_player_da_mystake_e_nickname…
  9. lista do servidor sem um nome da extensão            → test_filtro_do_servidor_contem…
"""
import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, "app")

import pytest  # noqa: E402

import cru  # noqa: E402
import ficha  # noqa: E402
from adaptadores import ADAPTADORES, Recusa, dx, numero  # noqa: E402

FIX = Path(__file__).resolve().parent.parent / "extensor" / "harness" / "fixtures"
# Família → fixtures da bancada. Adaptador novo entra aqui junto (test_todo_adaptador_tem_fixture).
FIXTURES_POR_FAMILIA = {
    "dx": ["dexsport.tickets.json"],
    "jb": ["betpanda.my_bets.json", "jonbet.my_bets_all.json", "jonbet.my_bets_open.json"],
    "shf": ["shuffle.sportsbets.json"],
    "tv": ["mystake.gethistory.json", "tivo.gethistory.json", "betfast.gethistory.json"],
    "vb": ["esportiva.settled.json", "esportiva.anuladas.json", "esportiva.cashout.json",
           "estrelabet.settled.json", "vaidebet.settled.json"],
    "x1": ["1xbet.bethistory.json", "1xbit.bethistory.json", "megapari.bethistory.json",
           "paripesa.bethistory.json", "sapphirebet.bethistory.json"],
}


def _respostas(fx):
    """Toda `resposta` dentro de uma fixture da bancada, em qualquer formato de gravação."""
    out = []

    def walk(o):
        if isinstance(o, dict):
            if "resposta" in o:
                out.append(o["resposta"])
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for x in o:
                walk(x)
    walk(fx)
    # Fixture gravada sem o envelope `resposta` (a maioria da bancada): ela É a resposta.
    return out or [fx]


def _bilhetes(familia):
    mod = ADAPTADORES[familia]
    for nome in FIXTURES_POR_FAMILIA[familia]:
        fx = json.loads((FIX / nome).read_text(encoding="utf-8"))
        for r in _respostas(fx):
            yield nome, from_list(mod.bilhetes_da_resposta(r))


def from_list(x):
    return list(x)


# ── 1. o filtro ───────────────────────────────────────────────────────────────────────

def test_campos_da_aposta_sobrevivem():
    """A lista que a busca por pedaço de nome apagaria, conferida nas fixtures (consultoria)."""
    da_aposta = {k: 1 for k in ("CurrentBetBalance", "CurrentBetBalanceDecimal", "betSlipNumber",
                                "betslips", "total_multiplier", "multiplier", "receiptBetId",
                                "championship", "description", "disciplineId")}
    filtrado, removidos = cru.filtrar(da_aposta)
    assert filtrado == da_aposta and removidos == []


def test_campos_de_pessoa_e_de_sessao_saem():
    obj = {"id": "A1", "CurrentBalance": 900, "user": {"nome": "x"}, "client_ip": "1.2.3.4",
           "detalhe": {"login-id": "abc", "stake": 10}}
    filtrado, removidos = cru.filtrar(obj)
    assert filtrado == {"id": "A1", "detalhe": {"stake": 10}}
    assert sorted(removidos) == ["CurrentBalance", "client_ip", "detalhe.login-id", "user"]


def test_codigo_uuid_e_nanoid_sobrevivem():
    obj = {"id": "1d15646f-c666-4fe6-a4c9-f73545f59ebd", "betId": "V1StGXR8_Z5jdHi6B-myT"}
    assert cru.filtrar(obj)[0] == obj


def test_email_sai_pelo_valor():
    filtrado, removidos = cru.filtrar({"contato": "fulano@exemplo.com.br", "id": "1"})
    assert filtrado == {"id": "1"} and removidos == ["contato (e-mail pelo valor)"]


def test_nome_exato_sem_caixa():
    """`Email`/`EMAIL` caem, `emailVerified` (outro nome) não: igualdade, nunca "contém"."""
    filtrado, _ = cru.filtrar({"Email": 1, "EMAIL": 2, "emailVerified": True})
    assert filtrado == {"emailVerified": True}


def test_filtro_nao_muda_o_original():
    obj = {"user": 1, "id": 2}
    cru.filtrar(obj)
    assert obj == {"user": 1, "id": 2}


def test_hash_estavel_e_independente_da_ordem():
    assert cru.impressao({"a": 1, "b": 2}) == cru.impressao({"b": 2, "a": 1})


# ── 2. o teste OBRIGATÓRIO: filtrado = sem filtro, em toda fixture com adaptador ──────

def test_todo_adaptador_tem_fixture():
    assert set(ADAPTADORES) == set(FIXTURES_POR_FAMILIA), \
        "adaptador sem fixture no teste obrigatório (ou fixture de família sem adaptador)"


@pytest.mark.parametrize("familia", sorted(FIXTURES_POR_FAMILIA))
def test_ficha_do_cru_filtrado_e_identica_a_do_cru_sem_filtro(familia):
    mod = ADAPTADORES[familia]
    vistos = 0
    for nome, bilhetes in _bilhetes(familia):
        for t in bilhetes:
            filtrado, _ = cru.filtrar(t)
            try:
                a = mod.adaptar(t, "CASA")
            except Recusa as e:
                with pytest.raises(Recusa) as e2:
                    mod.adaptar(filtrado, "CASA")
                assert str(e2.value) == str(e)
                continue
            assert mod.adaptar(filtrado, "CASA") == a, f"{nome}: o filtro mudou a Ficha"
            vistos += 1
    assert vistos > 0, f"nenhum bilhete de {familia} foi conferido: o teste não mediu nada"


# ── 3. DEX contra o gabarito da tela ──────────────────────────────────────────────────

# prefixo do id → (odd, resultado, stake, data da planilha). Card lido em 03/10/2026.
_GABARITO_DEX = {
    "3345134c": ("5,03", "W", "25", "02/10/2026"),
    "b4836669": ("3,75", "W", "25", "03/10/2026"),   # perna anulada: 12,56 seria ganho inventado
    "c0140de0": ("3,76", "W", "29,45", "03/10/2026"),
    "b2e1c15c": ("4,3", "W", "25", "03/10/2026"),
    "6836ecd1": ("3,77", "L", "24,5", "02/10/2026"),
    "2cbcf976": ("2,7", "L", "25", "02/10/2026"),
    "c43f1040": ("5,06", "L", "25", "03/10/2026"),
    "2a544c06": ("4,25", "L", "25", "03/10/2026"),   # perdida: payoutCoefficient 0 seria odd zero
    "603158df": ("4,94", "L", "25", "03/10/2026"),   # perdida com perna ainda "não decidida"
    "bf7feb3c": ("6,86", "", "25", "04/10/2026"),    # aberta: payout 0 não é derrota
}


def _dex():
    return [t for _, ts in _bilhetes("dx") for t in ts]


def test_dex_bate_com_o_gabarito_da_tela():
    achados = {}
    for t in _dex():
        g = _GABARITO_DEX.get(t["id"][:8])
        if not g:
            continue
        f = dict(dx.adaptar(t, "DEXSPORT"), impressao="x")
        assert ficha.validar(f, "DEXSPORT") == [], t["id"]
        d = ficha.derivar(f)
        achados[t["id"][:8]] = (d["odd"], d["resultado"], d["stake"], d["data"])
    assert achados == _GABARITO_DEX


def test_dex_monta_todos_os_41_da_fixture_sem_recusa():
    ts = _dex()
    assert len(ts) == 41
    for t in ts:
        f = dict(dx.adaptar(t, "DEXSPORT"), impressao="x")
        assert ficha.validar(f, "DEXSPORT") == [], t["id"]


def test_dex_recusa_o_que_hoje_sobe_a_conferir():
    base = next(t for t in _dex() if t["id"].startswith("2a544c06"))   # perdida
    t = copy.deepcopy(base)
    t["result"] = 0                         # retorno zero sem result 2
    with pytest.raises(Recusa):
        dx.adaptar(t, "DEXSPORT")
    t = copy.deepcopy(base)
    t["payout"] = 12.5                      # meio retorno: HW/HL ou cashout
    with pytest.raises(Recusa):
        dx.adaptar(t, "DEXSPORT")
    t = copy.deepcopy(base)
    t["status"] = 7                         # combinação nunca vista
    with pytest.raises(Recusa):
        dx.adaptar(t, "DEXSPORT")


def test_dex_moeda_em_maiusculo_e_codigo_verbatim():
    t = next(t for t in _dex() if t["id"].startswith("b4836669"))
    f = dx.adaptar(t, "DEXSPORT")
    assert f["moeda"] == "USDT" and f["codigo"] == t["id"]


def test_dex_odd_da_casa_na_ganha_e_a_liquidada():
    """Complemento (a) do Feca: "a odd da casa" é um campo definido POR FAMÍLIA. Na DEX ganha,
    é o `payoutCoefficient` (3,75), nunca o `coefficient` da colocação (12,56, com a perna
    anulada dentro). O `derivar` chegaria a 3,75 pelo dinheiro de qualquer jeito, e por isso o
    teste de ponta a ponta não via este campo: a mutação 4 escapou dele na 1ª rodada."""
    t = next(t for t in _dex() if t["id"].startswith("b4836669"))
    assert dx.adaptar(t, "DEXSPORT")["odd"] == "3.75"
    perdida = next(t for t in _dex() if t["id"].startswith("2a544c06"))
    assert dx.adaptar(perdida, "DEXSPORT")["odd"] == "4.25"


def test_numero_corta_o_ruido_do_float():
    assert numero(123.50000000000001) == "123.5"
    assert numero(25) == "25" and numero(29.45) == "29.45" and numero(None) is None


# ── a lista do servidor CONTÉM a da extensão ─────────────────────────────────────────

def test_filtro_do_servidor_contem_o_da_extensao():
    """`extensor/cru.js` filtra antes de o cru sair do navegador; `app/cru.py` filtra de novo
    antes de gravar. A do servidor pode ser MAIOR (campo novo entra sem atualizar a extensão,
    Feca 12/10), nunca menor: o que a extensão jogaria fora, o servidor também joga."""
    import re as _re
    fonte = (Path(__file__).resolve().parent.parent / "extensor" / "cru.js").read_text(encoding="utf-8")
    bloco = fonte.split("const CRU_NOMES_FILTRADOS = new Set([", 1)[1].split("]", 1)[0]
    js = {n.casefold() for n in _re.findall(r'"([^"]+)"', bloco)}
    assert js and js <= set(cru.NOMES_FILTRADOS)


def test_player_da_mystake_e_nickname_da_dex_saem():
    """Os dois campos de pessoa que a varredura dos 545 crus achou (s409): o login e o id
    externo da conta na MyStake, e o apelido da conta no topo do bilhete da DEX."""
    tv = {"ID": 307310722, "Amount": 100, "Player": {"ID": 1, "Name": "fulano.de.tal",
                                                     "Company": 2, "ExternalID": "123"}}
    dx = {"id": "0826db2e", "amount": 25, "nickname": "ApelidoQualquer"}
    f_tv, rem_tv = cru.filtrar(tv)
    f_dx, rem_dx = cru.filtrar(dx)
    assert f_tv == {"ID": 307310722, "Amount": 100} and rem_tv == ["Player"]
    assert f_dx == {"id": "0826db2e", "amount": 25} and rem_dx == ["nickname"]
