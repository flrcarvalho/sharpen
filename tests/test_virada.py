"""Gate da virada da Ficha (`app/virada.py`, `03_REGUA_NUMEROS §7`) e do dicionário de termos
(`app/dicionario.py`, `04_DICIONARIO`). Virada construída desligada na s409; dicionário, D10,
descrição com a linha e coluna `sistema` na s411 (12/10/2026).

Aqui, sem banco: a chave, a linha da planilha montada da Ficha, a tradução de esporte e
categoria, a semente, e as travas da rota (a recusada nunca vai à planilha; termo fora do
dicionário e código já gravado por outro caminho ficam com a IA; falha ao gravar nunca derruba
a rota). O teste dos bilhetes chegando ao banco (aceita pela Ficha, recusada, sem cru, termo
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
 15. a separação ignora o código já gravado (D10)        → test_d10_codigo_de_outro_caminho_fica_com_a_ia
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


def _sem_banco(monkeypatch, termos=None, outro=()):
    """`separar` real, com o banco dublado: o dicionário e os códigos de outro caminho."""
    termos = termos if termos is not None else {
        k: "Futebol" for k in dicionario.chaves(_ficha("5508528206"))}

    async def separar_no_banco(casa_key, dono, aceitas):
        class Conn:
            async def fetch(self, sql, *a):
                if "dicionario_termos" in sql:
                    return [{"tipo": t, "termo_casa": k, "termo_sharpen": v}
                            for (t, k), v in termos.items()]
                return [{"codigo_bilhete": c} for c in outro]
        return await virada.separar(Conn(), casa_key, dono, aceitas)
    monkeypatch.setattr(virada, "_separar_no_banco", separar_no_banco)


def _gravador(monkeypatch):
    vistos = []

    async def falso(dono, casa, parceiro, itens):
        vistos.extend((f["codigo"], e, c) for f, e, c in itens)
        return {"salvos": len(itens)}
    monkeypatch.setattr(virada, "gravar_na_planilha", falso)
    return vistos


def test_so_a_aceita_vai_a_planilha(monkeypatch):
    monkeypatch.setenv("FICHA_CASAS_VIRADAS", "VAVADA")
    _sem_banco(monkeypatch)
    vistos = _gravador(monkeypatch)
    assert asyncio.run(virada.gravar_aceitas(SESS, _registros())) == 1
    assert vistos == [("5508528206", "Futebol", "Múltipla")]


def test_termo_fora_do_dicionario_nao_vai_a_planilha(monkeypatch):
    monkeypatch.setenv("FICHA_CASAS_VIRADAS", "VAVADA")
    _sem_banco(monkeypatch, termos={})
    vistos = _gravador(monkeypatch)
    assert asyncio.run(virada.gravar_aceitas(SESS, _registros())) == 0 and vistos == []


def test_d10_codigo_de_outro_caminho_fica_com_a_ia(monkeypatch):
    """D10: o histórico não é reescrito pela Ficha. Código que a IA já gravou fica com ela."""
    monkeypatch.setenv("FICHA_CASAS_VIRADAS", "VAVADA")
    _sem_banco(monkeypatch, outro=["5508528206"])
    vistos = _gravador(monkeypatch)
    assert asyncio.run(virada.gravar_aceitas(SESS, _registros())) == 0 and vistos == []


def test_casa_nao_virada_nao_grava(monkeypatch):
    monkeypatch.setenv("FICHA_CASAS_VIRADAS", "DEXSPORT")

    async def falso(*a):
        raise AssertionError("não devia gravar")
    monkeypatch.setattr(virada, "gravar_na_planilha", falso)
    monkeypatch.setattr(virada, "_separar_no_banco", falso)
    assert asyncio.run(virada.gravar_aceitas(SESS, _registros())) == 0


def test_falha_ao_gravar_nao_derruba_a_rota(monkeypatch):
    """O cru e a Ficha já estão guardados: a aposta vai pela IA, pelo texto."""
    monkeypatch.setenv("FICHA_CASAS_VIRADAS", "VAVADA")
    _sem_banco(monkeypatch)

    async def quebra(*a):
        raise RuntimeError("banco fora")
    monkeypatch.setattr(virada, "gravar_na_planilha", quebra)
    assert asyncio.run(virada.gravar_aceitas(SESS, _registros())) == 0
    monkeypatch.setattr(virada, "_separar_no_banco", quebra)
    assert asyncio.run(virada.gravar_aceitas(SESS, _registros())) == 0


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
