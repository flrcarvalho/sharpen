"""Gate da virada da Ficha (`app/virada.py`, `03_REGUA_NUMEROS §7`) e do dicionário de termos
(`app/dicionario.py`, `04_DICIONARIO`). Virada construída desligada na s409; dicionário, D10,
descrição com a linha e coluna `sistema` na s411 (12/10/2026).

Aqui, sem banco: a chave, a linha da planilha montada da Ficha, a tradução de esporte e
categoria, a semente, e as travas da rota (a recusada nunca vai à planilha; termo fora do
dicionário ficam com a IA; liquidada no banco nunca é reescrita; o `/extrair` espera o cru e
resolve pelo cru guardado; falha ao gravar nunca derruba a rota). O teste dos bilhetes chegando ao banco (aceita pela Ficha, recusada, sem cru, termo
fora do dicionário e D10 pela IA) está no harness de banco, `tests/test_repository_db.py`.

Crus REAIS (`tests/ficha_crus_familias.json`), pelos adaptadores reais.

Mutações provadas (aplicadas, teste ao lado vermelho):
  1. `*` passa a virar todas as casas                    → test_asterisco_nao_vira_casa_nenhuma
  2. a recusada também vai à planilha                    → test_so_a_aceita_vai_a_planilha
  3. sem o `try` em volta da gravação                    → test_falha_ao_gravar_nao_derruba_a_rota
  4. esporte da 1ª perna mesmo com esportes misturados   → test_esporte_segue_o_master_esportes
  5. sem `origem='ficha'` no `/salvar`                    → test_grava_pelo_salvar_com_origem_ficha
  s411:
  6. 3 jogos do mesmo esporte não viram `Múltiplos`      → test_esporte_segue_o_master_esportes
  7. termo que falta não impede a gravação               → test_termo_fora_do_dicionario_fica_com_a_ia
  8. mercado contraditório entra pelo voto da maioria    → test_semente_so_guarda_o_unanime
  9. bilhete `Múltiplos` da IA vota no esporte           → test_semente_so_guarda_o_unanime
 10. `*` exige unanimidade em vez da maioria por casa    → test_esporte_geral_pela_maioria_de_cada_casa
 11. descrição sem a linha                               → test_descricao_traz_a_linha_uma_vez_so
 12. linha repetida quando já está no texto              → test_descricao_traz_a_linha_uma_vez_so
 13. tv sem inverter o sinal do `hisminus`               → test_tv_linha_com_hisminus_inverte_o_sinal
 14. sistema sem a 12ª coluna                            → test_sistema_da_altenar_preenche_a_coluna
  s411, 2ª rodada (a aposta sai da IA na origem; D10 = não reescrever a LIQUIDADA):
 15. a rota reescreve a liquidada no banco               → test_d10_liquidada_no_banco_nao_e_reescrita
 17. a espera ignora o cru em processamento              → test_extrair_espera_o_cru_em_processamento
 18. a espera sem teto (trava em vez de falhar: wait_for) → test_extrair_sem_cru_espera_so_a_folga…
 19. cru igual já gravado é regravado                     → test_cru_igual_ja_gravado_pela_ficha…
 20. recusada no /salvar conta como resolvida pela Ficha  → test_recusada_no_salvar_fica_com_a_ia
 16. texto de múltipla com um `Esporte:` só vota         → test_esportes_do_texto_so_quando_a_perna_e_clara
Inócua (registrada, não é buraco): `virada()` aceitar `*` — o `casas_viradas()` já tira o `*`
da lista antes, então o código segue certo sem a linha.

O QUE NÃO COBRE: a conversão de moeda (é a do `/salvar`, coberta lá), o recorte no `/extrair`
(é o pré-dedup de sempre; o harness de banco prova que ele tira a aceita) e se o dicionário
semeado está CERTO (é a régua: `medir_backtest_virada.py` compara a tradução com o que a IA
gravou, aposta a aposta).
"""
import asyncio
import json
import sys
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, "app")

import dicionario  # noqa: E402
import ficha  # noqa: E402
import virada  # noqa: E402
from adaptadores import tv, vb  # noqa: E402

CRUS = json.loads((Path(__file__).resolve().parent / "ficha_crus_familias.json")
                  .read_text(encoding="utf-8"))
SESS = SimpleNamespace(dono="TDono", casa_key="VAVADA", casa="Vavada", parceiro="conta [Op]")


def _ficha(cod, mod=vb, casa="VAVADA"):
    f = dict(mod.adaptar(CRUS[cod], casa), impressao="x")
    assert ficha.validar(f, casa) == []
    return f


def _perna(esporte, evento, mercado="Vencedor", selecao="1", linha=None):
    return {"esporte_casa": esporte, "evento": evento, "mercado_casa": mercado,
            "selecao_casa": selecao, "linha": linha}


def test_chave_vazia_nada_vira(monkeypatch):
    monkeypatch.delenv("FICHA_CASAS_VIRADAS", raising=False)
    assert not virada.virada("VAVADA")
    monkeypatch.setenv("FICHA_CASAS_VIRADAS", " dexsport , MyStake ")
    assert virada.virada("DEXSPORT") and virada.virada("mystake") and not virada.virada("VAVADA")


def test_asterisco_nao_vira_casa_nenhuma(monkeypatch):
    """Cada casa vira por nome: `*` não pode ligar todas de uma vez."""
    monkeypatch.setenv("FICHA_CASAS_VIRADAS", "*")
    assert not virada.virada("VAVADA") and virada.casas_viradas() == frozenset()


# ── dicionário ─────────────────────────────────────────────────────────────────────────

def test_normalizar_troca_numero_so_na_categoria():
    assert dicionario.normalizar("  Total  de Gols 2.5 ") == "total de gols {n}"
    assert dicionario.normalizar("1ª metade - Handicap 1,5") == "{n}ª metade - handicap {n}"
    # a Altenar numera o esporte: o número É o termo
    assert dicionario.normalizar("sportTypeId 4", numeros=False) == "sporttypeid 4"


def test_esporte_segue_o_master_esportes():
    """`MASTER_ESPORTES §2`: esportes diferentes, ou 3+ jogos diferentes, = Múltiplos; 2 jogos
    do mesmo esporte e bet builder (mesmo jogo) = o esporte. A IA de hoje erra os dois lados
    (régua de 12/10: MyStake 307597971 3 jogos = `Futebol`; DEX fab8990b 2 jogos = `Múltiplos`)."""
    termos = {("esporte", "football"): "Futebol", ("esporte", "basketball"): "Basquete"}

    def esp(*pernas):
        return dicionario.traduzir({"tipo": "multipla", "pernas": list(pernas)}, termos)[0]
    assert esp(_perna("football", "A vs B"), _perna("basketball", "C vs D")) == "Múltiplos"
    assert esp(_perna("football", "A vs B"), _perna("football", "C vs D")) == "Futebol"
    assert esp(*(_perna("football", j) for j in ("A vs B", "C vs D", "E vs F"))) == "Múltiplos"
    assert esp(*(_perna("football", "A vs B", m) for m in ("Gols", "Cantos", "Cartões"))) == "Futebol"


def test_categoria_simples_pelo_mercado_e_pelo_par_com_a_selecao():
    termos = {("esporte", "futebol"): "Futebol",
              ("categoria", "total de gols {n}"): "Over/Under",
              ("categoria", "vencedor | empate"): "1X2"}
    f = {"tipo": "simples", "pernas": [_perna("Futebol", "A vs B", "Total de gols 2.5", "Acima")]}
    assert dicionario.traduzir(f, termos) == ("Futebol", "Over/Under", [])
    f = {"tipo": "simples", "pernas": [_perna("Futebol", "A vs B", "Vencedor", "Empate")]}
    assert dicionario.traduzir(f, termos)[:2] == ("Futebol", "1X2")
    f = {"tipo": "multipla", "pernas": [_perna("Futebol", "A vs B"), _perna("Futebol", "C vs D")]}
    assert dicionario.traduzir(f, termos) == ("Futebol", "Múltipla", [])


def test_termo_fora_do_dicionario_fica_com_a_ia():
    termos = {("esporte", "futebol"): "Futebol"}
    f = {"tipo": "simples", "pernas": [_perna("Futebol", "A vs B", "Escanteios asiáticos")]}
    esp, cat, faltam = dicionario.traduzir(f, termos)
    assert cat is None and faltam == [("categoria", "escanteios asiáticos")]
    f = {"tipo": "multipla", "pernas": [_perna("Futebol", "A vs B"), _perna("Andebol", "C vs D")]}
    esp, cat, faltam = dicionario.traduzir(f, termos)
    assert esp is None and faltam == [("esporte", "andebol")]


def test_semente_so_guarda_o_unanime():
    """Unânime entra; IA que decidiu de dois jeitos fica de fora (vai para a IA e para o
    Feca). Bilhete que a IA chamou de `Múltiplos` não diz nada do termo e não vota."""
    def simples(merc, sel="1"):
        return {"tipo": "simples", "pernas": [_perna("Futebol", "A vs B", merc, sel)]}
    tres = {"tipo": "multipla", "pernas": [_perna("Futebol", j) for j in ("A", "B", "C")]}
    pares = [("MYSTAKE", simples("Total"), "Futebol", "Over/Under"),
             ("MYSTAKE", simples("Total"), "Futebol", "Over/Under"),
             ("MYSTAKE", simples("Handicap"), "Futebol", "Handicap Asiático"),
             ("MYSTAKE", simples("Handicap"), "Futebol", "Handicap Asiático"),
             ("MYSTAKE", simples("Handicap", "2"), "Futebol", "Handicap Europeu"),
             ("DEX", tres, "Múltiplos", "Múltipla")]
    unanimes, contraditos = dicionario.votar(pares)
    assert unanimes[("MYSTAKE", "categoria", "total")] == ("Over/Under", 2)
    assert unanimes[("MYSTAKE", "esporte", "futebol")] == ("Futebol", 5)
    assert ("MYSTAKE", "categoria", "handicap") not in unanimes
    assert contraditos[("MYSTAKE", "categoria", "handicap")] == Counter(
        {"Handicap Asiático": 2, "Handicap Europeu": 1})
    # o par mercado + seleção desempata o mercado contraditório
    assert unanimes[("MYSTAKE", "categoria", "handicap | 2")] == ("Handicap Europeu", 1)
    assert not any(k[0] == "DEX" for k in unanimes)


def test_esporte_geral_pela_maioria_de_cada_casa():
    """`*` vale para todas as casas quando a decisão mais votada é a mesma em todas (a IA
    errou 1 de 11 `tênis` na Betnacional, e isso não pode apagar o termo da MyStake)."""
    um = {"tipo": "simples", "pernas": [_perna("Tênis", "A vs B")]}
    pares = ([("BETNACIONAL", um, "Tênis", "")] * 10 + [("BETNACIONAL", um, "Futebol", "")]
             + [("MYSTAKE", um, "Tênis", "")] * 3)
    unanimes, contraditos = dicionario.votar(pares)
    assert unanimes[("*", "esporte", "tênis")] == ("Tênis", 14)
    assert ("BETNACIONAL", "esporte", "tênis") in contraditos
    pares += [("SHUFFLE", um, "Tênis de Mesa", "")] * 2
    assert ("*", "esporte", "tênis") not in dicionario.votar(pares)[0]


def test_esportes_do_texto_so_quando_a_perna_e_clara():
    """`sombra_rotulos`: um `Esporte:` por perna (DEX, MyStake) ou simples. O texto da Altenar
    escreve um `Esporte:` só no bilhete, e numa múltipla ele não diz de qual perna é."""
    dex = ("Tipo: Múltipla (2 seleções)\nSeleções:\n- Total: Under 165.5\n"
           "    Jogo: A vs B · Esporte: basketball · Início: x\n- Over 1.5\n"
           "    Jogo: C vs D · Esporte: football · Início: y\n")
    assert dicionario.esportes_do_texto(dex) == ["basketball", "football"]
    simples = "Tipo: Simples\nSeleções:\n- X\n    Jogo: A vs B · Esporte: tabletennis · Início: x\n"
    assert dicionario.esportes_do_texto(simples) == ["tabletennis"]
    vavada = ("Tipo: Múltipla (2 seleções)\nEsporte: sportTypeId 34 (a conferir)\n"
              "Seleções:\n- V\n    Jogo: A vs. B · Início: x\n- T\n    Jogo: C vs. D · Início: y\n")
    assert dicionario.esportes_do_texto(vavada) is None


# ── linha da planilha ─────────────────────────────────────────────────────────────────

def test_linha_da_planilha_de_uma_ficha_real():
    """Dupla Vavada 5508528206 (futebol + vôlei), ganha: retorno ÷ stake como a régua mede."""
    col = virada.linha_tsv(_ficha("5508528206"), "Vavada", "conta [Op]",
                           "Múltiplos", "Múltipla").split("\t")
    assert col == ["10/10/2026", "Múltiplos", "", "Vavada", "conta [Op]", "Múltipla",
                   "Mais de 11.5 Total cantos [Vicenza vs. Pisa] // Haro Rioja (F) (+1.5) "
                   "Handicap de sets [Haro Rioja (F) vs. Haris (F)]",
                   "25", "7,6192", "W", "5508528206"]


def test_descricao_traz_a_linha_uma_vez_so():
    f = {"pernas": [_perna("Futebol", "A vs B", "Time de casa total de escanteios", "Abaixo",
                           "3.5"),
                    _perna("Futebol", "C vs D", "Total", "Mais de 2.5", "2.5")]}
    assert virada._descricao(f) == ("Abaixo 3.5 Time de casa total de escanteios [A vs B] // "
                                    "Mais de 2.5 Total [C vs D]")


def test_tv_linha_com_hisminus_inverte_o_sinal():
    """Mesma regra do `_textoTV` da extensão (s392): `h: -2.5, hisminus: true` é `+2.5`."""
    it = dict(CRUS["307310722"]["Items"][0], FinalPosition={"h": -2.5, "hisminus": True})
    t = dict(CRUS["307310722"], Items=[it] + CRUS["307310722"]["Items"][1:])
    assert tv.adaptar(t, "MYSTAKE")["pernas"][0]["linha"] == "2.5"
    it = dict(it, FinalPosition={"h": -2.5})
    t = dict(t, Items=[it] + CRUS["307310722"]["Items"][1:])
    assert tv.adaptar(t, "MYSTAKE")["pernas"][0]["linha"] == "-2.5"


def test_sistema_da_altenar_preenche_a_coluna():
    """BetMartini 5501503684 (R16): sistema 2 de 3 = `3x Duplas`, a 12ª coluna do texto."""
    f = _ficha("5501503684", casa="BETMARTINI")
    col = virada.linha_tsv(f, "BetMartini", "c", "Múltiplos", "Múltipla").split("\t")
    assert len(col) == 12 and col[11] == "3x Duplas"
    assert virada._sistema(dict(f, sistema="ilegível")) == ""
    assert len(virada.linha_tsv(_ficha("5508528206"), "V", "c", "x", "y").split("\t")) == 11


# ── rota ───────────────────────────────────────────────────────────────────────────────

def test_simples_aberta_sai_sem_resultado():
    cru = dict(CRUS["5508528206"], status=0, selections=CRUS["5508528206"]["selections"][:1])
    f = dict(vb.adaptar(cru, "VAVADA"), impressao="x")
    col = virada.linha_tsv(f, "Vavada", "c", "Futebol", "Over/Under").split("\t")
    assert (col[1], col[5], col[9]) == ("Futebol", "Over/Under", "")
    assert "\t" not in col[6] and virada._carimbo(f) == "20261010074000"


def _registros():
    boa = ficha._registro(_ficha("5508528206"), [])
    ruim = ficha._registro({"codigo": "5504514128", "cru_recusado": True}, ["status 7"])
    return [boa, ruim]


class _Conn:
    """Banco dublado: dicionário, códigos liquidados, `ficha_virada` e `captura_crua`."""

    def __init__(self, termos=None, liquidados=(), estado=None, crus=()):
        self.termos = termos if termos is not None else {
            k: "Futebol" for k in dicionario.chaves(_ficha("5508528206"))}
        self.liquidados, self.crus = list(liquidados), list(crus)
        self.estado = dict(estado or {})          # código → (impressão, estado)
        self.motivos = {}

    async def fetch(self, sql, *a):
        if "dicionario_termos" in sql:
            return [{"tipo": t, "termo_casa": k, "termo_sharpen": v}
                    for (t, k), v in self.termos.items()]
        if "extraction_state" in sql:
            return [{"codigo_bilhete": c} for c in self.liquidados]
        if "FROM ficha_virada" in sql:
            return [{"codigo": c, "impressao": i, "estado": e}
                    for c, (i, e) in self.estado.items()]
        if "captura_crua" in sql:
            return self.crus
        raise AssertionError(sql)

    async def execute(self, sql, *a):
        assert "ficha_virada" in sql
        _, _, cod, imp, est, motivo = a
        self.estado[cod] = (imp, est)
        self.motivos[cod] = motivo


def _banco(monkeypatch, **kw):
    conn = _Conn(**kw)

    class _Pool:
        def acquire(self):
            class _Ctx:
                async def __aenter__(self_):
                    return conn

                async def __aexit__(self_, *e):
                    return False
            return _Ctx()

    async def pool():
        return _Pool()
    monkeypatch.setattr(virada, "_pool_conn", pool)
    return conn


def _gravador(monkeypatch, rejeitados=()):
    vistos = []

    async def falso(dono, casa, parceiro, itens):
        vistos.extend((f["codigo"], e, c) for f, e, c in itens)
        return {"salvos": len(itens) - len(rejeitados),
                "rejeitados": [{"linha": n} for n in rejeitados]}
    monkeypatch.setattr(virada, "gravar_na_planilha", falso)
    return vistos


def test_so_a_aceita_vai_a_planilha(monkeypatch):
    monkeypatch.setenv("FICHA_CASAS_VIRADAS", "VAVADA")
    conn = _banco(monkeypatch)
    vistos = _gravador(monkeypatch)
    assert asyncio.run(virada.gravar_aceitas(SESS, _registros())) == 1
    assert vistos == [("5508528206", "Futebol", "Múltipla")]
    assert conn.estado["5508528206"][1] == "ficha" and conn.estado["5504514128"][1] == "ia"
    assert conn.motivos["5504514128"] == "Ficha recusada"


def test_termo_fora_do_dicionario_nao_vai_a_planilha(monkeypatch):
    monkeypatch.setenv("FICHA_CASAS_VIRADAS", "VAVADA")
    conn = _banco(monkeypatch, termos={})
    vistos = _gravador(monkeypatch)
    assert asyncio.run(virada.gravar_aceitas(SESS, _registros())) == 0 and vistos == []
    assert conn.motivos["5508528206"] == "termo fora do dicionário"


def test_d10_liquidada_no_banco_nao_e_reescrita(monkeypatch):
    """D10 (Feca, 12/10): "não mexer no passado é não ir futricar as apostas de mês passado".
    Liquidada no banco, de qualquer origem, fica como está: nem grava, nem decide."""
    monkeypatch.setenv("FICHA_CASAS_VIRADAS", "VAVADA")
    conn = _banco(monkeypatch, liquidados=["5508528206"])
    vistos = _gravador(monkeypatch)
    assert asyncio.run(virada.gravar_aceitas(SESS, _registros())) == 0 and vistos == []
    assert "5508528206" not in conn.estado


def test_cru_igual_ja_gravado_pela_ficha_sai_sem_regravar(monkeypatch):
    monkeypatch.setenv("FICHA_CASAS_VIRADAS", "VAVADA")
    _banco(monkeypatch, estado={"5508528206": ("x", "ficha")})      # impressão do _ficha
    vistos = _gravador(monkeypatch)
    assert asyncio.run(virada.gravar_aceitas(SESS, _registros())) == 1 and vistos == []


def test_recusada_no_salvar_fica_com_a_ia(monkeypatch):
    monkeypatch.setenv("FICHA_CASAS_VIRADAS", "VAVADA")
    conn = _banco(monkeypatch)
    _gravador(monkeypatch, rejeitados=[1])
    assert asyncio.run(virada.gravar_aceitas(SESS, _registros())) == 0
    assert conn.estado["5508528206"][1] == "ia"


def test_casa_nao_virada_nao_grava(monkeypatch):
    monkeypatch.setenv("FICHA_CASAS_VIRADAS", "DEXSPORT")

    async def falso(*a):
        raise AssertionError("não devia gravar")
    monkeypatch.setattr(virada, "gravar_na_planilha", falso)
    monkeypatch.setattr(virada, "_pool_conn", falso)
    assert asyncio.run(virada.gravar_aceitas(SESS, _registros())) == 0
    assert asyncio.run(virada.resolver_no_extrair("TDono", "VAVADA", "Vavada", "c", ["1"])) \
        == (set(), 0.0)


def test_falha_ao_gravar_nao_derruba_a_rota(monkeypatch):
    """O cru e a Ficha já estão guardados: a aposta vai pela IA, pelo texto."""
    monkeypatch.setenv("FICHA_CASAS_VIRADAS", "VAVADA")
    conn = _banco(monkeypatch)

    async def quebra(*a):
        raise RuntimeError("banco fora")
    monkeypatch.setattr(virada, "gravar_na_planilha", quebra)
    assert asyncio.run(virada.gravar_aceitas(SESS, _registros())) == 0
    assert conn.estado["5508528206"][1] == "ia"
    monkeypatch.setattr(virada, "_pool_conn", quebra)
    assert asyncio.run(virada.gravar_aceitas(SESS, _registros())) == 0


def test_extrair_resolve_pelo_cru_guardado(monkeypatch):
    """A extensão não reenvia cru igual: no `/extrair`, a aposta aberta que a IA gravou antes
    da virada passa para a Ficha pelo cru GUARDADO. O que não tem cru fica com a IA."""
    monkeypatch.setenv("FICHA_CASAS_VIRADAS", "VAVADA")
    monkeypatch.setattr(virada, "FOLGA", 0.0)
    _banco(monkeypatch, crus=[{"codigo": "5508528206", "familia": "vb",
                               "cru": json.dumps(CRUS["5508528206"])}])
    vistos = _gravador(monkeypatch)
    feitos, _ = asyncio.run(virada.resolver_no_extrair(
        "TDono", "VAVADA", "Vavada", "c", ["5508528206", "5500000003"]))
    assert feitos == {"5508528206"} and [v[0] for v in vistos] == ["5508528206"]


# ── corrida: o `/extrair` espera o cru da mesma captura ─────────────────────────────────

def test_extrair_espera_o_cru_em_processamento():
    async def cenario():
        virada.cru_entrou("TDono", "VAVADA")

        async def termina():
            await asyncio.sleep(0.3)
            virada.cru_saiu("TDono", "VAVADA")
        t = asyncio.create_task(termina())
        esperou = await virada.esperar_cru("TDono", "VAVADA", maximo=3, folga=0)
        await t
        return esperou
    assert 0.25 <= asyncio.run(cenario()) < 1.5


def test_extrair_sem_cru_espera_so_a_folga_e_com_teto():
    virada._em_voo.clear(), virada._ultimo_fim.clear()
    assert 0.15 <= asyncio.run(virada.esperar_cru("TDono", "DUEL", maximo=3, folga=0.2)) < 1
    virada.cru_saiu("TDono", "DUEL")                       # cru desta captura já terminou
    assert asyncio.run(virada.esperar_cru("TDono", "DUEL", maximo=3, folga=2)) < 0.5
    virada.cru_entrou("TDono", "SHUFFLE")                  # nunca termina: o teto manda
    # `wait_for`: sem o teto a espera seria eterna, e o teste tem de FALHAR, não travar
    assert 0.25 <= asyncio.run(asyncio.wait_for(
        virada.esperar_cru("TDono", "SHUFFLE", maximo=0.3), 3)) < 1.5
    virada.cru_saiu("TDono", "SHUFFLE")


def test_dicionario_aprende_uma_vez_por_dia():
    from datetime import datetime, timezone
    antes = datetime(2026, 10, 12, 6, 30, tzinfo=timezone.utc)
    depois = datetime(2026, 10, 12, 7, 30, tzinfo=timezone.utc)
    assert dicionario.segundos_ate(7, antes) == 1800
    assert dicionario.segundos_ate(7, depois) == 23.5 * 3600


def test_grava_pelo_salvar_com_origem_ficha(monkeypatch):
    """O `/salvar` de hoje (`main.gravar_tsv`), com a procedência da Ficha e o carimbo de
    colocação para a cotação da conta em outra moeda."""
    chamadas = []

    async def gravar_tsv(body, dono, dono_view, origem="extracao"):
        chamadas.append((body, dono, dono_view, origem))
        return {"salvos": 1, "rejeitados": []}

    class _SR:
        def __init__(self, **kw):
            self.__dict__.update(kw)
    monkeypatch.setitem(sys.modules, "main", SimpleNamespace(gravar_tsv=gravar_tsv,
                                                             SalvarRequest=_SR))
    f = _ficha("5508528206")
    r = asyncio.run(virada.gravar_na_planilha("TDono", "Vavada", "conta [Op]",
                                              [(f, "Múltiplos", "Múltipla")]))
    assert r["salvos"] == 1
    body, dono, dono_view, origem = chamadas[0]
    assert (dono, dono_view, origem) == ("TDono", "TDono", "ficha")
    assert body.tsv == virada.linha_tsv(f, "Vavada", "conta [Op]", "Múltiplos", "Múltipla")
    assert body.carimbos == {"5508528206": "20261010074000"} and body.moedas == ["USD"]
