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
 11/12. (descrição com a linha da casa: substituída pelo dicionário de descrição na s413)
 13. tv sem inverter o sinal do `hisminus`               → test_tv_linha_com_hisminus_inverte_o_sinal
 14. sistema sem a 12ª coluna                            → test_sistema_da_altenar_preenche_a_coluna
  s411, 2ª rodada (a aposta sai da IA na origem; D10 = não reescrever a LIQUIDADA):
 15. a rota reescreve a liquidada no banco               → test_d10_liquidada_no_banco_nao_e_reescrita
 17. a espera ignora o cru em processamento              → test_extrair_espera_o_cru_em_processamento
 18. a espera sem teto (trava em vez de falhar: wait_for) → test_extrair_sem_cru_espera_so_a_folga…
 19. cru igual já gravado é regravado                     → test_cru_igual_ja_gravado_pela_ficha…
 20. recusada no /salvar conta como resolvida pela Ficha  → test_recusada_no_salvar_fica_com_a_ia
 16. texto de múltipla com um `Esporte:` só vota         → test_esportes_do_texto_so_quando_a_perna_e_clara
  s412 (furo N3, D24, R27; 13/10/2026):
  P2. sem a checagem do cru velho (N3)                   → test_extrair_cru_velho_so_vale_com_o_texto_igual
  R.  sem conferir o Master antes de gravar              → test_categoria_fora_do_master_fica_com_a_ia
  T.  `Total` pelo dicionário, não pela regra            → test_total_sem_qualificador_e_a_categoria…
  U.  Tênis sem olhar a linha                            → test_total_sem_qualificador_e_a_categoria…
  V.  termo vago traduz                                  → test_termo_vago_nunca_traduz_nem_vota
  W.  termo vago vota                                    → test_termo_vago_nunca_traduz_nem_vota
  X.  semente aprende valor fora do Master               → test_semente_so_aprende_valor_do_master
  Z.  a semente da casa vence a correção do Feca         → test_correcao_do_feca_vence_a_semente
  AF. `Total` com a descrição geral                      → test_descricao_propria_do_feca
  AG. `Winner. Quarter N` sem a descrição própria        → test_descricao_propria_do_feca
  s413 (dicionário de descrição; o resto em `tests/test_descricao_ficha.py`):
  D1. mercado sem par de descrição grava assim mesmo      → test_descricao_fora_do_dicionario_vai_a_ia…
  D2. maioria de 90% vira contradição (P7)                → test_esporte_geral_pela_maioria_de_cada_casa
  s415 (o vigia; o resto no harness de banco):
  W1. o vigia ignora a stake                              → test_vigia_compara_o_dinheiro_nao_a_forma
  W2. o vigia compara a odd crua também na perdida        → test_vigia_compara_o_dinheiro_nao_a_forma
  s416 (D28 e R32; o resto no harness de banco):
  W9. a reserva da casa sempre livre                      → test_vigia_uma_chamada_por_casa…
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
    pares = [("MYSTAKE", simples("Total de gols"), "Futebol", "Gols"),
             ("MYSTAKE", simples("Total de gols"), "Futebol", "Gols"),
             ("MYSTAKE", simples("Handicap"), "Futebol", "Handicap"),
             ("MYSTAKE", simples("Handicap"), "Futebol", "Handicap"),
             ("MYSTAKE", simples("Handicap", "2"), "Futebol", "Outros"),
             ("MYSTAKE", simples("Total"), "Futebol", "Gols"),          # regra, não termo
             ("DEX", tres, "Múltiplos", "Múltipla")]
    unanimes, contraditos, _ = dicionario.votar(pares)
    assert unanimes[("MYSTAKE", "categoria", "total de gols")] == ("Gols", 2)
    assert unanimes[("MYSTAKE", "esporte", "futebol")] == ("Futebol", 6)
    assert ("MYSTAKE", "categoria", "handicap") not in unanimes
    assert contraditos[("MYSTAKE", "categoria", "handicap")] == Counter(
        {"Handicap": 2, "Outros": 1})
    # o par mercado + seleção desempata o mercado contraditório
    assert unanimes[("MYSTAKE", "categoria", "handicap | 2")] == ("Outros", 1)
    assert ("MYSTAKE", "categoria", "total") not in unanimes
    assert not any(k[0] == "DEX" for k in unanimes)


def test_esporte_geral_pela_maioria_de_cada_casa():
    """`*` vale para todas as casas quando a decisão mais votada é a mesma em todas (a IA
    errou 1 de 11 `tênis` na Betnacional, e isso não pode apagar o termo da MyStake).
    s413 (P7): com 90% ou mais dos votos fica a maioria, também na casa, e o voto isolado vai
    para a revisão; abaixo de 90% o termo continua contraditório."""
    um = {"tipo": "simples", "pernas": [_perna("Tênis", "A vs B")]}
    pares = ([("BETNACIONAL", um, "Tênis", "")] * 10 + [("BETNACIONAL", um, "Futebol", "")]
             + [("MYSTAKE", um, "Tênis", "")] * 3)
    unanimes, contraditos, revisao = dicionario.votar(pares)
    assert unanimes[("*", "esporte", "tênis")] == ("Tênis", 14)
    assert unanimes[("BETNACIONAL", "esporte", "tênis")] == ("Tênis", 10)
    assert ("BETNACIONAL", "esporte", "tênis") not in contraditos
    assert revisao == [{"casa": "BETNACIONAL", "tipo": "esporte", "termo": "tênis",
                        "fica": "Tênis", "votos": {"Tênis": 10, "Futebol": 1}}]
    nove = [("BETNACIONAL", um, "Tênis", "")] * 8 + [("BETNACIONAL", um, "Futebol", "")]
    _, contraditos, _ = dicionario.votar(nove)                     # 8 de 9 = 89%
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

# O dicionário de descrição das duas pernas da 5508528206 (os valores que a IA ensinou).
DESC = {("descricao", "sporttypeid 1 | total cantos"): "{ou} Escanteios",
        ("descricao", "sporttypeid 19 | handicap de sets"): "{ent} {hc} Sets"}
DESC_5508528206 = ("Over 11.5 Escanteios [Vicenza v Pisa] // "
                   "Haro Rioja (F) +1.5 Sets [Haro Rioja (F) v Haris (F)]")


def test_linha_da_planilha_de_uma_ficha_real():
    """Dupla Vavada 5508528206 (futebol + vôlei), ganha: retorno ÷ stake como a régua mede. A
    descrição sai do dicionário de descrição (s413), perna por perna."""
    f = _ficha("5508528206")
    assert virada.descricao(f, DESC) == DESC_5508528206
    col = virada.linha_tsv(f, "Vavada", "conta [Op]", "Múltiplos", "Múltipla",
                           virada.descricao(f, DESC)).split("\t")
    assert col == ["10/10/2026", "Múltiplos", "", "Vavada", "conta [Op]", "Múltipla",
                   DESC_5508528206, "25", "7,6192", "W", "5508528206"]
    # uma perna sem par: a descrição não sai (a aposta vai para a IA)
    assert virada.descricao(f, dict(list(DESC.items())[:1])) is None


def test_descricao_propria_do_feca():
    """s412: `Total` sem qualificador = `Over/Under X.X [A v B]`; `Winner. Quarter N` (DEX) =
    `Time - NQ [A v B]`; volta mais rápida = `<piloto> volta mais rápida [<prova>]`."""
    def d(*pernas):
        return virada.descricao({"pernas": list(pernas)}, {})
    assert d(_perna("football", "Nasarawa United vs Doma United FC", "Total", "Under 3.5")) \
        == "Under 3.5 [Nasarawa United v Doma United FC]"
    assert d(_perna("Soccer", "OGC Nice vs Strasbourg", "Total", "over 3")) == "Over 3 [OGC Nice v Strasbourg]"
    assert d(_perna("Futebol", "A vs. B", "Total", "Mais de 2.5", "2.5")) == "Over 2.5 [A v B]"
    assert d(_perna("basketball", "Galatasaray vs Bursaspor", "Winner. Quarter 1", "Bursaspor")) \
        == "Bursaspor - 1Q [Galatasaray v Bursaspor]"
    assert d(_perna("Fórmula 1", "Bahrain Grand Prix 2026 - Race", "Fastest lap", "Norris, Lando")) \
        == "Norris, Lando volta mais rápida [Bahrain Grand Prix 2026 - Race]"
    assert d(_perna("Fórmula 1", "Singapore GP", "Volta mais rápida", "Leclerc, Charles")) \
        == "Leclerc, Charles volta mais rápida [Singapore GP]"
    # `Total` com seleção que não é Over/Under: o dicionário de descrição (aqui vazio: IA)
    assert d(_perna("Futebol", "A vs B", "Total", "Ímpar")) is None


def test_total_sem_qualificador_e_a_categoria_principal_do_esporte():
    """s412 (Feca): Futebol, Hóquei, Handebol = Gols; Basquete, Futebol Americano = Pontos;
    Tênis até 4,5 = Sets, acima = Games; Vôlei até 4,5 = Sets, acima = Pontos; outro = IA.
    Vale mesmo que a semente tenha aprendido outra coisa para `total`."""
    termos = {("esporte", e.lower()): e for e in
              ("Futebol", "Hóquei", "Handebol", "Basquete", "Futebol Americano", "Tênis",
               "Vôlei", "MMA")}
    termos[("categoria", "total")] = "Escanteios"           # semente errada: a regra manda

    def cat(esporte, sel, linha=None):
        f = {"tipo": "simples", "pernas": [_perna(esporte, "A vs B", "Total", sel, linha)]}
        return dicionario.traduzir(f, termos)[1:]
    for e in ("Futebol", "Hóquei", "Handebol"):
        assert cat(e, "Over 2.5") == ("Gols", [])
    for e in ("Basquete", "Futebol Americano"):
        assert cat(e, "Under 210.5") == ("Pontos", [])
    assert cat("Tênis", "Over 3.5") == ("Sets", []) and cat("Tênis", "Under 4.5") == ("Sets", [])
    assert cat("Tênis", "Over 21.5") == ("Games", [])
    assert cat("Vôlei", "Over 4.5") == ("Sets", []) and cat("Vôlei", "Over 180.5") == ("Pontos", [])
    assert cat("Tênis", "Over", "22.5") == ("Games", [])                  # linha em campo próprio
    assert cat("MMA", "Over 1.5") == (None, [("categoria", "total")])     # fora da lista: IA
    assert cat("Tênis", "Over") == (None, [("categoria", "total")])       # sem linha: IA


def test_termo_vago_nunca_traduz_nem_vota():
    """s412: `especiais` nunca entra no dicionário e sempre vai para a IA."""
    termos = {("esporte", "especiais"): "Futebol", ("esporte", "futebol"): "Futebol",
              ("categoria", "especiais"): "Outros"}
    f = {"tipo": "simples", "pernas": [_perna("Especiais", "A vs B", "Vencedor")]}
    assert dicionario.traduzir(f, termos)[2][0] == ("esporte", "especiais")
    f = {"tipo": "simples", "pernas": [_perna("Futebol", "A vs B", "Especiais")]}
    assert dicionario.traduzir(f, termos)[1:] == (None, [("categoria", "especiais")])
    um = {"tipo": "simples", "pernas": [_perna("Especiais", "A vs B", "Especiais")]}
    unanimes, _, _ = dicionario.votar([("7GAMES", um, "Futebol", "Outros")] * 3,
                                      [("7GAMES", ["Especiais"], "Futebol")])
    assert unanimes == {}


def test_semente_so_aprende_valor_do_master():
    """R27: a IA às vezes escreve categoria ou esporte que o Master não tem; não vota."""
    um = {"tipo": "simples", "pernas": [_perna("Futebol", "A vs B", "Vencedor")]}
    unanimes, _, _ = dicionario.votar([("MYSTAKE", um, "Futebal", "Vencedor da partida")] * 2)
    assert unanimes == {}
    unanimes, _, _ = dicionario.votar([("MYSTAKE", um, "Futebol", "ML")] * 2)
    assert unanimes[("MYSTAKE", "categoria", "vencedor")] == ("ML", 2)


def test_correcao_do_feca_vence_a_semente():
    """`carregar`: a correção (`feca`) vence a semente, inclusive a semente DA CASA contra a
    correção geral (`*`); termo vago nunca sai do banco para a tradução."""
    class _C:
        async def fetch(self, sql, *a):
            assert "ORDER BY (origem = 'feca'), (casa <> '*')" in sql
            linhas = [("*", "semente", "x", "A"), ("BETPANDA", "semente", "volta mais rápida", "Outros"),
                      ("*", "feca", "volta mais rápida", "Player Props"),
                      ("*", "semente", "especiais", "Futebol")]
            ordem = sorted(linhas, key=lambda r: (r[1] == "feca", r[0] != "*"))
            return [{"casa": c, "tipo": "categoria", "termo_casa": t, "termo_sharpen": v}
                    for c, _, t, v in ordem]
    termos = asyncio.run(dicionario.carregar(_C(), "BETPANDA"))
    assert termos[("categoria", "volta mais rápida")] == "Player Props"
    assert ("categoria", "especiais") not in termos


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
    col = virada.linha_tsv(f, "BetMartini", "c", "Múltiplos", "Múltipla", "d").split("\t")
    assert len(col) == 12 and col[11] == "3x Duplas"
    assert virada._sistema(dict(f, sistema="ilegível")) == ""
    assert len(virada.linha_tsv(_ficha("5508528206"), "V", "c", "x", "y", "d").split("\t")) == 11


# ── rota ───────────────────────────────────────────────────────────────────────────────

def test_simples_aberta_sai_sem_resultado():
    cru = dict(CRUS["5508528206"], status=0, selections=CRUS["5508528206"]["selections"][:1])
    f = dict(vb.adaptar(cru, "VAVADA"), impressao="x")
    col = virada.linha_tsv(f, "Vavada", "c", "Futebol", "Over/Under",
                           virada.descricao(f, DESC)).split("\t")
    assert (col[1], col[5], col[9]) == ("Futebol", "Over/Under", "")
    assert col[6] == "Over 11.5 Escanteios [Vicenza v Pisa]"
    assert "\t" not in col[6] and virada._carimbo(f) == "20261010074000"


def _registros():
    boa = ficha._registro(_ficha("5508528206"), [])
    ruim = ficha._registro({"codigo": "5504514128", "cru_recusado": True}, ["status 7"])
    return [boa, ruim]


class _Conn:
    """Banco dublado: dicionário, códigos liquidados, `ficha_virada` e `captura_crua`."""

    def __init__(self, termos=None, liquidados=(), estado=None, crus=()):
        self.termos = termos if termos is not None else {
            **{k: "Futebol" for k in dicionario.chaves(_ficha("5508528206"))}, **DESC}
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

    async def fetchval(self, sql, *a):
        assert "virada_log" in sql                # R32: o último `/extrair` (o `fresco` do cru
        return None                               # dublado já vem decidido)

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
        vistos.extend((f["codigo"], e, c) for f, e, c, _ in itens)
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


def test_descricao_fora_do_dicionario_vai_a_ia_uma_vez_e_depois_nao(monkeypatch):
    """s413 (Feca: chamada extra à IA só para a descrição, nunca): mercado sem par de descrição
    vai para a IA com o motivo próprio; a IA escreve a descrição, a semente aprende com 1 voto
    (D24), e a captura seguinte do MESMO mercado, com outra linha, fica com a Ficha."""
    monkeypatch.setenv("FICHA_CASAS_VIRADAS", "VAVADA")
    sem = {k: v for k, v in _Conn().termos.items() if k != ("descricao", "sporttypeid 1 | total cantos")}
    conn = _banco(monkeypatch, termos=sem)
    vistos = _gravador(monkeypatch)
    assert asyncio.run(virada.gravar_aceitas(SESS, _registros())) == 0 and vistos == []
    assert conn.motivos["5508528206"] == "descrição fora do dicionário"
    # a IA descreveu a aposta; a semente aprende o mercado a partir dela
    f = _ficha("5508528206")
    unanimes, _, _ = dicionario.votar([("VAVADA", f, "Múltiplos", "Múltipla", DESC_5508528206)])
    conn.termos.update({(t, k): v for (c, t, k), (v, _) in unanimes.items() if t == "descricao"})
    assert conn.termos[("descricao", "sporttypeid 1 | total cantos")] == "{ou} Escanteios"
    # outra aposta do mesmo mercado, com outra linha e outro lado: Ficha, sem IA
    cru = json.loads(json.dumps(CRUS["5508528206"]))
    cru["selections"][0]["name"] = "Menos de 9.5"
    g = dict(vb.adaptar(cru, "VAVADA"), impressao="y")
    assert virada.descricao(g, conn.termos).startswith("Under 9.5 Escanteios [Vicenza v Pisa] // ")
    assert asyncio.run(virada.gravar_aceitas(SESS, [ficha._registro(g, [])])) == 1
    assert conn.estado["5508528206"][1] == "ficha"


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
        == (set(), 0.0, {})


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
    _banco(monkeypatch, crus=[{"codigo": "5508528206", "familia": "vb", "fresco": True,
                               "cru": json.dumps(CRUS["5508528206"])}])
    vistos = _gravador(monkeypatch)
    feitos, _, fica = asyncio.run(virada.resolver_no_extrair(
        "TDono", "VAVADA", "Vavada", "c", ["5508528206", "5500000003"]))
    assert feitos == {"5508528206"} and [v[0] for v in vistos] == ["5508528206"]
    assert fica == {"5500000003": "cru não chegou"}


def test_extrair_cru_velho_so_vale_com_o_texto_igual(monkeypatch):
    """N3 (parecer 012): cru de captura ANTERIOR só resolve se o bloco de texto não mudou desde
    a última leitura. Texto mudado + cru velho = a liquidação que o cru esconderia: vai à IA."""
    monkeypatch.setenv("FICHA_CASAS_VIRADAS", "VAVADA")
    monkeypatch.setattr(virada, "FOLGA", 0.0)
    cru = {"codigo": "5508528206", "familia": "vb", "fresco": False,
           "cru": json.dumps(CRUS["5508528206"])}
    conn = _banco(monkeypatch, crus=[cru])
    vistos = _gravador(monkeypatch)
    feitos, _, fica = asyncio.run(virada.resolver_no_extrair(
        "TDono", "VAVADA", "Vavada", "c", ["5508528206"]))
    assert feitos == set() and vistos == []
    assert fica == {"5508528206": "texto mudou sem cru novo"}
    assert conn.motivos["5508528206"] == "texto mudou sem cru novo"
    feitos, _, fica = asyncio.run(virada.resolver_no_extrair(
        "TDono", "VAVADA", "Vavada", "c", ["5508528206"], {"5508528206"}))
    assert feitos == {"5508528206"} and fica == {}


def test_categoria_fora_do_master_fica_com_a_ia(monkeypatch):
    """R27: a Ficha confere o Master antes de gravar. Categoria que o Master não tem vai à IA."""
    monkeypatch.setenv("FICHA_CASAS_VIRADAS", "VAVADA")
    conn = _banco(monkeypatch)
    vistos = _gravador(monkeypatch)
    assert virada.no_master("Futebol", "Múltipla") and not virada.no_master("Futebol", "Especiais")
    assert not virada.no_master("Futebal", "Múltipla")
    # a aceita é múltipla (categoria `Múltipla`, do Master): o esporte é que sai do Master
    conn.termos = {k: "Futebal" for k in conn.termos}
    assert asyncio.run(virada.gravar_aceitas(SESS, _registros())) == 0 and vistos == []
    assert conn.motivos["5508528206"] == "fora do Master"


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
                                              [(f, "Múltiplos", "Múltipla", DESC_5508528206)]))
    assert r["salvos"] == 1
    body, dono, dono_view, origem = chamadas[0]
    assert (dono, dono_view, origem) == ("TDono", "TDono", "ficha")
    assert body.tsv == virada.linha_tsv(f, "Vavada", "conta [Op]", "Múltiplos", "Múltipla",
                                        DESC_5508528206)
    assert DESC_5508528206 in body.tsv
    assert body.carimbos == {"5508528206": "20261010074000"} and body.moedas == ["USD"]


# ── s415: o vigia da virada ──────────────────────────────────────────────────────────────

def test_vigia_compara_o_dinheiro_nao_a_forma():
    """O vigia acusa onde o DINHEIRO muda: stake, resultado, e a odd só pelo P/L na liquidada
    (a IA escreve a odd da W como retorno ÷ stake, e as duas pagam o mesmo)."""
    C = virada.vigia_comparar
    ficha = {"stake": "10", "odd": "1,85", "resultado": "W"}
    assert C(ficha, {"stake": "10,00", "odd": "1.85", "resultado": "W"}) == []
    assert C(ficha, {"stake": "10", "odd": "1,8500", "resultado": "W"}) == []
    assert C(ficha, {"stake": "12", "odd": "1,85", "resultado": "W"}) == ["stake", "odd"]
    assert C(ficha, {"stake": "10", "odd": "1,85", "resultado": "L"}) == ["resultado"]
    assert C(ficha, {"stake": "10", "odd": "1,95", "resultado": "W"}) == ["odd"]
    # perdida: a odd não muda o dinheiro
    assert C({"stake": "10", "odd": "1,85", "resultado": "L"},
             {"stake": "10", "odd": "2,10", "resultado": "L"}) == []
    # aberta: a própria odd
    assert C({"stake": "10", "odd": "1,85", "resultado": ""},
             {"stake": "10", "odd": "1,90", "resultado": ""}) == ["odd"]
    assert C(ficha, None) == ["linha"]


def test_vigia_uma_chamada_por_casa_mesmo_com_duas_capturas_ao_mesmo_tempo():
    """D28 (s416): a reserva do dia é por casa (de qualquer dono) e só volta quando a chamada
    não aconteceu. Duas capturas juntas (Feca e Gabriel) passariam as duas pelo banco antes de
    a primeira gravar. Mutação W9 (reserva sempre livre): detectada."""
    virada._vigia_reservas.clear()
    assert virada.vigia_reservar("dexsport", "14/10/2026") is True
    assert virada.vigia_reservar("DEXSPORT", "14/10/2026") is False      # a 2ª captura
    assert virada.vigia_reservar("DEXSPORT", "15/10/2026") is True       # outro dia
    assert virada.vigia_reservar("DUEL", "14/10/2026") is True           # outra casa
    virada.vigia_soltar("DEXSPORT", "14/10/2026")                        # não chamou
    assert virada.vigia_reservar("DEXSPORT", "14/10/2026") is True
    virada._vigia_reservas.clear()


def test_vigia_desligado_sem_a_variavel(monkeypatch):
    monkeypatch.delenv("VIGIA_POR_DIA", raising=False)
    assert virada.vigia_por_dia() == 0
    monkeypatch.setenv("VIGIA_POR_DIA", "3")
    assert virada.vigia_por_dia() == 3
    monkeypatch.setenv("VIGIA_POR_DIA", "x")
    assert virada.vigia_por_dia() == 0
