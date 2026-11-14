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
 19b. (s429) cru igual dado por gravado sem a linha no banco → test_cru_igual_sem_a_linha_no_banco…
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
  s438 (D39; o resto no harness de banco):
  D39a. cru velho liquidado volta a ser segurado          → cru_velho_liquidado_grava_pela_ficha
  D39b. contradiz() sempre falso                          → liquidado_que_o_texto_desmente
  D39c. cru velho aberto volta a ir à IA (regra antiga)   → cru_velho_aberto_com_texto_mudado
  D39d. sem cru vai sempre à IA                           → extrair_resolve_pelo_cru_guardado
  D39e. sem cru segura mesmo sem cru recente da casa      → sem_cru_so_segura_se_a_casa_manda_cru
  D39f. chave da casa sem tirar o ponto / o acento        → chave_da_casa_bate_com_o_registro
  s438 (D40):
  D40a. a gravação volta a usar a descrição estrita         → d40_descricao_fora_do_dicionario
  D40b. a forma estrita passa a usar o texto da casa        → d40_descricao_fora_do_dicionario
  D40c. perna sem mercado nem seleção grava vazia           → d40_so_a_perna_sem_mercado
  s447 (apagou e recapturou; `iguais` sem exigir a linha no banco):
  S1. sem a trava do texto igual com veredito             → s447_texto_igual_com_veredito…
  S2. a trava vale também para o cru fresco               → s447_cru_fresco_nao_passa…
  S3. a trava ignora se o texto tem veredito              → s447_texto_igual_com_veredito…
  s451 (a recusa da Ficha é um dict, não None):
  S4. `texto_desmente` sem a trava do `cru_recusado`      → s451_ficha_recusada_com_texto_igual…
  s453 (a marca "já gravado" vale por CONTA e só para cru aberto; 1win da Ellen):
  E1. sem o `not cru_final(f)` no pulo                    → s453_cru_liquidado_com_a_linha_aberta…
  E2. `_no_banco` sem o filtro de conta                   → s453_linha_so_noutra_conta…
  E3. `aplicar` não passa o `parceiro` ao `_no_banco`     → s453_linha_so_noutra_conta…
  (o `exigir_linha=False` no `/extrair` em `test_barreira_recaptura.py`; a consulta no banco
  em `test_repository_db.py::test_s447_texto_igual_nao_exige_a_linha_no_banco`)
Inócua (registrada, não é buraco): `texto_desmente` sem o `not cru_final(f)`: com cru aberto o
`contradiz` já dá verdadeiro (aberto não tem classe de resultado). O termo fica pela leitura.
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


class _Dic:
    """Banco dublado do `carregar`: `linhas` = (casa, origem, termo, tradução) da
    `dicionario_termos`; `familias` = (família, casa) da `captura_crua`. Devolve as linhas em
    ordem EMBARALHADA (a do banco não é garantida): a precedência tem de vir do código."""
    def __init__(self, linhas, familias=()):
        self.linhas, self.familias, self.consultas = linhas, familias, 0

    async def fetch(self, sql, *a):
        if "captura_crua" in sql:
            self.consultas += 1
            return [{"familia": f, "casa": c} for f, c in self.familias]
        casas = set(a[0])
        return [{"casa": c, "tipo": "categoria", "termo_casa": t, "termo_sharpen": v, "origem": o}
                for c, o, t, v in reversed(self.linhas) if c in casas]


def _carregar(conn, casa, **kw):
    dicionario._familias.update(em=None, mapa={})          # o cache de família é de módulo
    return asyncio.run(dicionario.carregar(conn, casa, **kw))


def test_correcao_do_feca_vence_a_semente():
    """`carregar`: a correção (`feca`) vence a semente, inclusive a semente DA CASA contra a
    correção geral (`*`); termo vago nunca sai do banco para a tradução."""
    c = _Dic([("*", "semente", "x", "A"), ("BETPANDA", "semente", "volta mais rápida", "Outros"),
              ("*", "feca", "volta mais rápida", "Player Props"),
              ("*", "semente", "especiais", "Futebol")])
    termos = _carregar(c, "BETPANDA")
    assert termos[("categoria", "volta mais rápida")] == "Player Props"
    assert ("categoria", "especiais") not in termos
    # dentro da mesma origem, a casa vence o geral
    c = _Dic([("BETPANDA", "semente", "x", "Casa"), ("*", "semente", "x", "Geral")])
    assert _carregar(c, "BETPANDA")[("categoria", "x")] == "Casa"


FAMILIA_VB = [("vb", "VAVADA"), ("vb", "BETMARTINI"), ("vb", "SPORTAZA"), ("x1", "MELBET")]


def test_d41_casa_herda_o_que_a_irma_aprendeu():
    """D41: a BetMartini lê o que a semente aprendeu na Vavada (mesma família `vb` no cru), e
    não o que aprendeu a MelBet (`x1`). Casa sem cru nenhum não tem família."""
    c = _Dic([("VAVADA", "semente", "total de cantos", "Escanteios"),
              ("MELBET", "semente", "handicap asiático", "Handicap")], FAMILIA_VB)
    termos = _carregar(c, "BETMARTINI")
    assert termos[("categoria", "total de cantos")] == "Escanteios"
    assert ("categoria", "handicap asiático") not in termos
    assert ("categoria", "total de cantos") not in _carregar(c, "CASANOVA")
    assert ("categoria", "total de cantos") not in _carregar(c, "BETMARTINI", familia=False)


def test_d41_irmas_que_divergem_nao_ensinam():
    """Duas irmãs traduzindo o mesmo termo de jeitos diferentes: a terceira não herda nenhum
    (fica com a IA até aprender o dela). A própria casa continua com o seu."""
    c = _Dic([("VAVADA", "semente", "especial", "Outros"),
              ("SPORTAZA", "semente", "especial", "Player Props")], FAMILIA_VB)
    assert ("categoria", "especial") not in _carregar(c, "BETMARTINI")
    assert _carregar(c, "VAVADA")[("categoria", "especial")] == "Outros"


def test_d41_precedencia_casa_familia_geral():
    """A casa vence a família, a família vence o geral (`*`), e a correção do Feca vence a
    semente em qualquer nível, inclusive a correção feita numa IRMÃ contra a semente da casa."""
    c = _Dic([("*", "semente", "a", "Geral"), ("VAVADA", "semente", "a", "Familia"),
              ("*", "semente", "b", "Geral"), ("VAVADA", "semente", "b", "Familia"),
              ("BETMARTINI", "semente", "b", "Casa"),
              ("BETMARTINI", "semente", "c", "Casa"), ("VAVADA", "feca", "c", "FecaNaIrma"),
              ("*", "feca", "d", "FecaGeral"), ("VAVADA", "feca", "d", "FecaNaIrma")], FAMILIA_VB)
    t = _carregar(c, "BETMARTINI")
    assert t[("categoria", "a")] == "Familia"
    assert t[("categoria", "b")] == "Casa"
    assert t[("categoria", "c")] == "FecaNaIrma"
    assert t[("categoria", "d")] == "FecaNaIrma"


def test_d41_familia_fica_em_cache():
    """A lista de famílias sai da `captura_crua` uma vez a cada `FAMILIAS_TTL`, não a cada
    captura (o `carregar` roda em todo `/extrair` de casa virada)."""
    c = _Dic([], FAMILIA_VB)
    dicionario._familias.update(em=None, mapa={})
    for _ in range(3):
        asyncio.run(dicionario.carregar(c, "BETMARTINI"))
    assert c.consultas == 1


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

    def __init__(self, termos=None, liquidados=(), estado=None, crus=(), no_banco=(),
                 manda_cru=True):
        self.termos = termos if termos is not None else {
            **{k: "Futebol" for k in dicionario.chaves(_ficha("5508528206"))}, **DESC}
        self.liquidados, self.crus = list(liquidados), list(crus)
        self.no_banco = list(no_banco)            # códigos com linha em `bilhetes` (s429)
        self.estado = dict(estado or {})          # código → (impressão, estado)
        self.motivos = {}
        self.manda_cru = manda_cru                # D39: a casa manda cru para este dono
        self.segurados = set()                    # D39 (b): `_segurar`

    async def fetch(self, sql, *a):
        if "dicionario_termos" in sql:            # termos da própria casa (a[0] = ["*", casa, …])
            return [{"casa": a[0][1], "tipo": t, "termo_casa": k, "termo_sharpen": v,
                     "origem": "semente"} for (t, k), v in self.termos.items()]
        if "DISTINCT familia" in sql:             # D41: a casa sem irmã no banco dublado
            return []
        if "extraction_state" in sql:
            return [{"codigo_bilhete": c} for c in self.liquidados]
        if "FROM bilhetes" in sql:
            # `no_banco`: código, ou (código, conta) para a linha que é de UMA conta (s453)
            linhas = [x if isinstance(x, tuple) else (x, None) for x in self.no_banco]
            conta = a[3] if "parceiro =" in sql else None
            return [{"codigo_bilhete": c} for c, p in linhas
                    if c in a[1] and (conta is None or p in (None, conta))]
        if "FROM ficha_virada" in sql:
            return [{"codigo": c, "impressao": i, "estado": e}
                    for c, (i, e) in self.estado.items()]
        if "captura_crua" in sql:
            return self.crus
        raise AssertionError(sql)

    async def fetchval(self, sql, *a):
        if "captura_crua" in sql:                 # D39: houve cru desta casa e dono há pouco?
            return self.manda_cru
        assert "virada_log" in sql                # R32: o último `/extrair` (o `fresco` do cru
        return None                               # dublado já vem decidido)

    async def execute(self, sql, *a):
        assert "ficha_virada" in sql
        if sql.lstrip().startswith("UPDATE"):     # avisos (D39/s423): regra no harness de banco
            return
        if "aviso" in sql:                        # D39 (b): `_segurar`
            self.segurados.add(a[2])
            return
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


def test_d40_descricao_fora_do_dicionario_grava_com_o_texto_da_casa(monkeypatch):
    """D40 (Feca, 01/11/2026): descrição desconhecida nunca manda a aposta à IA. A perna sem par
    ("Total cantos") grava como a casa escreve, `<mercado> - <seleção> [A v B]`; a outra perna
    sai do dicionário. Antes da D40 a aposta ia à IA (`descrição fora do dicionário`). Depois que
    o dicionário aprende o mercado, a aposta seguinte sai inteira pelo dicionário."""
    monkeypatch.setenv("FICHA_CASAS_VIRADAS", "VAVADA")
    sem = {k: v for k, v in _Conn().termos.items() if k != ("descricao", "sporttypeid 1 | total cantos")}
    conn = _banco(monkeypatch, termos=sem)
    descs = []

    async def falso(dono, casa, parceiro, itens):
        descs.extend((f["codigo"], d) for f, _, _, d in itens)
        return {"salvos": len(itens), "rejeitados": []}
    monkeypatch.setattr(virada, "gravar_na_planilha", falso)
    assert asyncio.run(virada.gravar_aceitas(SESS, _registros())) == 1
    assert descs == [("5508528206", "Total cantos - Mais de 11.5 [Vicenza v Pisa] // "
                                    "Haro Rioja (F) +1.5 Sets [Haro Rioja (F) v Haris (F)]")]
    # D42 commit 5: a aposta com perna no texto da casa fica marcada (o vigia a escolhe primeiro)
    assert conn.estado["5508528206"][1] == "ficha" and         conn.motivos["5508528206"] == virada.TEXTO_DA_CASA
    # a forma ESTRITA (regravação da semente, scripts) continua dizendo "o dicionário não cobre"
    f = _ficha("5508528206")
    assert virada.descricao(f, sem) is None
    # a IA de outra aposta ensina o mercado; a seguinte, com outra linha, sai do dicionário
    unanimes, _, _ = dicionario.votar([("VAVADA", f, "Múltiplos", "Múltipla", DESC_5508528206)])
    conn.termos.update({(t, k): v for (c, t, k), (v, _) in unanimes.items() if t == "descricao"})
    cru = json.loads(json.dumps(CRUS["5508528206"]))
    cru["selections"][0]["name"] = "Menos de 9.5"
    g = dict(vb.adaptar(cru, "VAVADA"), impressao="y")
    assert virada.descricao_para_gravar(g, conn.termos).startswith(
        "Under 9.5 Escanteios [Vicenza v Pisa] // ")


def test_d40_so_a_perna_sem_mercado_nem_selecao_vai_a_ia():
    """A única descrição que a D40 não monta é a da perna sem mercado E sem seleção: não há
    texto da casa para gravar, e aí a IA lê (motivo `descrição fora do dicionário`)."""
    vazia = {"pernas": [{"esporte_casa": "x", "evento": "A vs B", "mercado_casa": "",
                         "selecao_casa": None}]}
    assert virada.descricao_para_gravar(vazia, {}) is None

def test_d10_liquidada_no_banco_nao_e_reescrita(monkeypatch):
    """D10 (Feca, 12/10): "não mexer no passado é não ir futricar as apostas de mês passado".
    Liquidada no banco, de qualquer origem, fica como está: nem grava, nem decide."""
    monkeypatch.setenv("FICHA_CASAS_VIRADAS", "VAVADA")
    conn = _banco(monkeypatch, liquidados=["5508528206"])
    vistos = _gravador(monkeypatch)
    assert asyncio.run(virada.gravar_aceitas(SESS, _registros())) == 0 and vistos == []
    assert "5508528206" not in conn.estado


def _registros_aberta():
    """Os `_registros()` com a aposta boa ainda ABERTA na casa (o cru antes de liquidar)."""
    f = dict(_ficha("5508528206"), status="aberta")
    return [ficha._registro(f, []), _registros()[1]]


def test_cru_igual_ja_gravado_pela_ficha_sai_sem_regravar(monkeypatch):
    monkeypatch.setenv("FICHA_CASAS_VIRADAS", "VAVADA")
    _banco(monkeypatch, estado={"5508528206": ("x", "ficha")},      # impressão do _ficha
           no_banco=[("5508528206", SESS.parceiro)])
    vistos = _gravador(monkeypatch)
    assert asyncio.run(virada.gravar_aceitas(SESS, _registros_aberta())) == 1 and vistos == []


def test_s453_cru_liquidado_com_a_linha_aberta_nesta_conta_e_regravado(monkeypatch):
    """s453 (1win da Ellen, 13/11/2026): a captura na conta errada deixou a marca "ficha" com o
    cru LIQUIDADO. Na conta certa a linha está aberta (se estivesse liquidada, o `_liquidados`
    a tiraria antes). Cru liquidado nunca é "já gravado": a Ficha liquida a linha."""
    monkeypatch.setenv("FICHA_CASAS_VIRADAS", "VAVADA")
    _banco(monkeypatch, estado={"5508528206": ("x", "ficha")},
           no_banco=[("5508528206", SESS.parceiro)])
    vistos = _gravador(monkeypatch)
    assert asyncio.run(virada.gravar_aceitas(SESS, _registros())) == 1
    assert [v[0] for v in vistos] == ["5508528206"]


def test_s453_linha_so_noutra_conta_nao_conta_como_gravada_nesta(monkeypatch):
    """s453: a marca é por dono e casa. A linha que a Ficha gravou noutra conta (a arquivada, por
    engano, ou a conta compartilhada) não prova nada sobre esta: a aposta aberta é gravada aqui."""
    monkeypatch.setenv("FICHA_CASAS_VIRADAS", "VAVADA")
    _banco(monkeypatch, estado={"5508528206": ("x", "ficha")},
           no_banco=[("5508528206", "Feca [Eu]")])
    vistos = _gravador(monkeypatch)
    assert asyncio.run(virada.gravar_aceitas(SESS, _registros_aberta())) == 1
    assert [v[0] for v in vistos] == ["5508528206"]


def test_cru_igual_sem_a_linha_no_banco_e_regravado(monkeypatch):
    """s429 (20bet do Gabriel): o usuário EXCLUIU a aposta e recapturou. O cru é o mesmo e o
    `ficha_virada` ainda diz "ficha"; sem a linha no banco, a Ficha a grava de novo."""
    monkeypatch.setenv("FICHA_CASAS_VIRADAS", "VAVADA")
    _banco(monkeypatch, estado={"5508528206": ("x", "ficha")})
    vistos = _gravador(monkeypatch)
    assert asyncio.run(virada.gravar_aceitas(SESS, _registros())) == 1
    assert [v[0] for v in vistos] == ["5508528206"]


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
        == (set(), 0.0, {}, set())


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
    da virada passa para a Ficha pelo cru GUARDADO. D39 (s438): o código SEM cru não vai mais à
    IA; fica segurado ("captura incompleta") enquanto a casa manda cru para este dono."""
    monkeypatch.setenv("FICHA_CASAS_VIRADAS", "VAVADA")
    monkeypatch.setattr(virada, "FOLGA", 0.0)
    conn = _banco(monkeypatch, crus=[{"codigo": "5508528206", "familia": "vb", "fresco": True,
                                      "cru": json.dumps(CRUS["5508528206"])}])
    vistos = _gravador(monkeypatch)
    feitos, _, fica, seg = asyncio.run(virada.resolver_no_extrair(
        "TDono", "VAVADA", "Vavada", "c", ["5508528206", "5500000003"]))
    assert feitos == {"5508528206"} and [v[0] for v in vistos] == ["5508528206"]
    assert fica == {} and seg == {"5500000003"} and conn.segurados == {"5500000003"}


def test_d39_sem_cru_so_segura_se_a_casa_manda_cru(monkeypatch):
    """D39: extensão velha (nenhum cru desta casa e dono há 7 dias) segurando tudo deixaria a
    aposta sem leitor, e F5 não resolveria: aí o código sem cru segue para a IA, como antes."""
    monkeypatch.setenv("FICHA_CASAS_VIRADAS", "VAVADA")
    monkeypatch.setattr(virada, "FOLGA", 0.0)
    conn = _banco(monkeypatch, manda_cru=False)
    _gravador(monkeypatch)
    feitos, _, fica, seg = asyncio.run(virada.resolver_no_extrair(
        "TDono", "VAVADA", "Vavada", "c", ["5500000003"]))
    assert fica == {"5500000003": "cru não chegou"} and seg == set() and conn.segurados == set()


def _cru_velho(status=None):
    cru = CRUS["5508528206"] if status is None else dict(CRUS["5508528206"], status=status)
    return {"codigo": "5508528206", "familia": "vb", "fresco": False, "cru": json.dumps(cru)}


def test_extrair_cru_velho_aberto_com_texto_mudado_e_segurado(monkeypatch):
    """N3 (parecer 012) + D39: cru de captura ANTERIOR ainda ABERTO, com o bloco de texto
    mudado, é a liquidação que o cru esconderia. Antes da D39 ia à IA; agora fica fora dela,
    segurado ("captura incompleta"), até o cru novo chegar. Texto igual: a Ficha resolve."""
    monkeypatch.setenv("FICHA_CASAS_VIRADAS", "VAVADA")
    monkeypatch.setattr(virada, "FOLGA", 0.0)
    conn = _banco(monkeypatch, crus=[_cru_velho(status=0)])
    vistos = _gravador(monkeypatch)
    feitos, _, fica, seg = asyncio.run(virada.resolver_no_extrair(
        "TDono", "VAVADA", "Vavada", "c", ["5508528206"]))
    assert feitos == set() and vistos == [] and fica == {}
    assert seg == {"5508528206"} and conn.segurados == {"5508528206"}
    feitos, _, fica, seg = asyncio.run(virada.resolver_no_extrair(
        "TDono", "VAVADA", "Vavada", "c", ["5508528206"], {"5508528206"}))
    assert feitos == {"5508528206"} and fica == {} and seg == set()


def test_d39_cru_velho_liquidado_grava_pela_ficha_sem_ia(monkeypatch):
    """D39 (a): cru guardado JÁ LIQUIDADO não esconde liquidação nenhuma. Medido (parecer 022):
    963 de 976 "texto mudou sem cru novo" tinham cru final, 100% iguais ao que a IA gravou.
    Shuffle do Gabriel, 31/10: 108 apostas à IA duas vezes, US$ 1,51, por esta regra."""
    monkeypatch.setenv("FICHA_CASAS_VIRADAS", "VAVADA")
    monkeypatch.setattr(virada, "FOLGA", 0.0)
    _banco(monkeypatch, crus=[_cru_velho()])
    vistos = _gravador(monkeypatch)
    bloco = {"5508528206": "[Código: 5508528206]\nStatus: Ganhou → W\n"}
    feitos, _, fica, seg = asyncio.run(virada.resolver_no_extrair(
        "TDono", "VAVADA", "Vavada", "c", ["5508528206"], blocos=bloco))
    assert feitos == {"5508528206"} and [v[0] for v in vistos] == ["5508528206"]
    assert fica == {} and seg == set()


def test_d39_cru_velho_liquidado_que_o_texto_desmente_e_segurado(monkeypatch):
    """D39 (a), a trava: se o veredito do texto contradiz o cru guardado (a casa reliquidou), a
    Ficha não grava o resultado velho: a aposta espera o cru novo."""
    monkeypatch.setenv("FICHA_CASAS_VIRADAS", "VAVADA")
    monkeypatch.setattr(virada, "FOLGA", 0.0)
    _banco(monkeypatch, crus=[_cru_velho()])
    vistos = _gravador(monkeypatch)
    bloco = {"5508528206": "[Código: 5508528206]\nStatus: Perdeu → L\n"}
    feitos, _, fica, seg = asyncio.run(virada.resolver_no_extrair(
        "TDono", "VAVADA", "Vavada", "c", ["5508528206"], blocos=bloco))
    assert feitos == set() and vistos == [] and seg == {"5508528206"}


def test_s447_texto_igual_com_veredito_que_o_cru_velho_nao_confirma_e_segurado(monkeypatch):
    """s447: desde que o `iguais` deixou de exigir a linha no banco (a apagada e recapturada
    conta como texto igual), "texto igual" pode ser o de uma leitura da IA mais nova que o cru.
    Se o texto já diz o resultado e o cru guardado está aberto, ou diz outra classe, a Ficha
    NÃO grava o cru velho: espera o cru novo. Sem veredito no texto, ou veredito que o cru
    confirma, a Ficha resolve como sempre."""
    monkeypatch.setenv("FICHA_CASAS_VIRADAS", "VAVADA")
    monkeypatch.setattr(virada, "FOLGA", 0.0)
    cod = "5508528206"
    ganhou = {cod: f"[Código: {cod}]\nStatus: Ganhou → W\n"}
    perdeu = {cod: f"[Código: {cod}]\nStatus: Perdeu → L\n"}
    aberto = {cod: f"[Código: {cod}]\nStatus: Em aberto\n"}
    # cru velho ABERTO, texto igual com veredito: segura
    _banco(monkeypatch, crus=[_cru_velho(status=0)])
    vistos = _gravador(monkeypatch)
    feitos, _, fica, seg = asyncio.run(virada.resolver_no_extrair(
        "TDono", "VAVADA", "Vavada", "c", [cod], {cod}, blocos=ganhou))
    assert feitos == set() and vistos == [] and seg == {cod}
    # cru velho ABERTO, texto igual sem veredito: a Ficha grava (o caso da Cloudbet)
    _banco(monkeypatch, crus=[_cru_velho(status=0)])
    vistos = _gravador(monkeypatch)
    feitos, _, fica, seg = asyncio.run(virada.resolver_no_extrair(
        "TDono", "VAVADA", "Vavada", "c", [cod], {cod}, blocos=aberto))
    assert feitos == {cod} and seg == set()
    # cru velho LIQUIDADO (W), texto igual dizendo L: segura; dizendo W: grava
    _banco(monkeypatch, crus=[_cru_velho()])
    vistos = _gravador(monkeypatch)
    feitos, _, fica, seg = asyncio.run(virada.resolver_no_extrair(
        "TDono", "VAVADA", "Vavada", "c", [cod], {cod}, blocos=perdeu))
    assert feitos == set() and seg == {cod}
    _banco(monkeypatch, crus=[_cru_velho()])
    vistos = _gravador(monkeypatch)
    feitos, _, fica, seg = asyncio.run(virada.resolver_no_extrair(
        "TDono", "VAVADA", "Vavada", "c", [cod], {cod}, blocos=ganhou))
    assert feitos == {cod} and seg == set()


def test_s447_cru_fresco_nao_passa_pela_trava_do_texto(monkeypatch):
    """A trava é só do cru VELHO: cru desta captura é a verdade da casa, e manda."""
    monkeypatch.setenv("FICHA_CASAS_VIRADAS", "VAVADA")
    monkeypatch.setattr(virada, "FOLGA", 0.0)
    cod = "5508528206"
    _banco(monkeypatch, crus=[{"codigo": cod, "familia": "vb", "fresco": True,
                               "cru": json.dumps(dict(CRUS[cod], status=0))}])
    _gravador(monkeypatch)
    feitos, _, fica, seg = asyncio.run(virada.resolver_no_extrair(
        "TDono", "VAVADA", "Vavada", "c", [cod], blocos={cod: "Status: Ganhou → W"}))
    assert feitos == {cod} and seg == set()


def test_d39_contradiz_so_pela_classe_do_resultado():
    """O texto escreve `W` também para meia vitória: só a CLASSE conta. Sem veredito, não
    contradiz; cru que não se deriva é tratado como contradito (espera)."""
    f = _ficha("5508528206")
    assert ficha.derivar(f)["resultado"] == "W"
    assert not virada.contradiz(f, "Status: Ganhou → W")
    assert not virada.contradiz(f, "Status: Meio ganho → HW")
    assert virada.contradiz(f, "Status: Perdeu → L") and virada.contradiz(f, "Status: x → V")
    assert not virada.contradiz(f, "Status: Ganhou") and not virada.contradiz(f, None)
    assert virada.contradiz({"status": "inexistente"}, "Status: a → W")


def test_d39_ficha_recusada_com_texto_mudado_segue_para_a_ia(monkeypatch):
    """Ficha RECUSADA não tem como gravar: com o texto mudado, só a IA lê o bloco atual."""
    monkeypatch.setenv("FICHA_CASAS_VIRADAS", "VAVADA")
    monkeypatch.setattr(virada, "FOLGA", 0.0)
    conn = _banco(monkeypatch, crus=[_cru_velho(status=7)])     # status 7: recusa
    _gravador(monkeypatch)
    feitos, _, fica, seg = asyncio.run(virada.resolver_no_extrair(
        "TDono", "VAVADA", "Vavada", "c", ["5508528206"]))
    assert fica == {"5508528206": "texto mudou sem cru novo"} and seg == set()
    assert conn.motivos["5508528206"] == "texto mudou sem cru novo"


def test_s451_ficha_recusada_com_texto_igual_e_veredito_vai_a_ia(monkeypatch):
    """s451 (Stake.com do Gabriel, 12/11/2026): XMulti liquidada, apagada e recapturada. O cru
    é VELHO (a extensão não reenvia cru igual), o texto é IGUAL ao da última leitura e traz o
    veredito. A Ficha recusa a XMulti, então só a IA lê: a aposta vai à IA, nunca é segurada.
    Antes, o dict de recusa do `montar_ficha` (sem `status`) passava por "cru aberto" no
    `texto_desmente` e 20 de 69 ficavam fora da base, sem erro.

    O cru é o REAL da fixture e a Ficha passa pelo `montar_ficha` de verdade: o teste antigo
    da s447 nunca exerceu a recusa, porque a supunha None."""
    from adaptadores import stc
    fix = (Path(__file__).resolve().parents[1] / "extensor" / "harness" / "fixtures"
           / "stakecom.xmulti.json")
    xm = json.loads(fix.read_text(encoding="utf-8"))
    cod = "689158437"                       # XMulti de 3, Derrota, 40 USDT, payout 0
    cru = next({"iid": x["iid"], "bet": x["bet"]} for x in xm["settled"]
               if stc.codigo(x) == cod)
    f, mot = ficha.montar_ficha("stc", cru, "STAKECOM")
    assert f.get("cru_recusado") and mot                       # a premissa: a Ficha recusa
    assert not virada.texto_desmente(f, "Status: Perdeu → L")

    monkeypatch.setenv("FICHA_CASAS_VIRADAS", "STAKECOM")
    monkeypatch.setattr(virada, "FOLGA", 0.0)
    conn = _banco(monkeypatch, crus=[{"codigo": cod, "familia": "stc", "fresco": False,
                                      "cru": json.dumps(cru)}])
    vistos = _gravador(monkeypatch)
    feitos, _, fica, seg = asyncio.run(virada.resolver_no_extrair(
        "Gabriel", "STAKECOM", "Stake.com", "gfatuch [Fatuch]", [cod], {cod},
        blocos={cod: f"[Código: {cod}]\nStatus: Perdeu → L\n"}))
    assert seg == set() and conn.segurados == set()
    assert feitos == set() and vistos == [] and cod in fica


def test_chave_da_casa_bate_com_o_registro_inteiro():
    """D39 (d): a chave sem espaço, PONTO e acento. Só sem espaço, `Sportsbet.io`, `Stake.com`,
    `Betão` e `Vitória Bet` não batiam com a chave do registro, e a virada não via a linha que
    já estava no banco. Confere as casas do `_CASA_DISPLAY` (62 em 01/11/2026)."""
    import ast
    import re
    src = (Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(encoding="utf-8")
    reg = ast.literal_eval(re.search(r"^_CASA_DISPLAY[^=]*=\s*(\{.*?^\})", src,
                                     re.M | re.S).group(1))
    assert len(reg) >= 60
    assert {k: v for k, v in reg.items() if virada.chave_da_casa(v) != k} == {}
    assert virada.chave_da_casa("Sportsbet.io") == "SPORTSBETIO"
    assert virada.chave_da_casa(" Vitória  Bet ") == "VITORIABET"


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
    """D28 (s416): a reserva é por casa (de qualquer dono) e só volta quando a chamada não
    aconteceu. Duas capturas juntas (Feca e Gabriel) passariam as duas pelo banco antes de a
    primeira gravar. Desde a RC46 (s449) a chave é a SEMANA (`semana_brasilia`).
    Mutação W9 (reserva sempre livre): detectada."""
    virada._vigia_reservas.clear()
    assert virada.vigia_reservar("dexsport", "2026-11-09") is True
    assert virada.vigia_reservar("DEXSPORT", "2026-11-09") is False      # a 2ª captura
    assert virada.vigia_reservar("DEXSPORT", "2026-11-16") is True       # outra semana
    assert virada.vigia_reservar("DUEL", "2026-11-09") is True           # outra casa
    virada.vigia_soltar("DEXSPORT", "2026-11-09")                        # não chamou
    assert virada.vigia_reservar("DEXSPORT", "2026-11-09") is True
    virada._vigia_reservas.clear()


def test_vigia_semana_de_segunda_a_domingo_no_horario_de_brasilia():
    """RC46 (s449): a semana do vigia vai de segunda a domingo em Brasília. A terça e o domingo
    23:59 (já segunda 02:59 em UTC) são da semana de 09/11; segunda 00:00 em Brasília abre a
    seguinte. Mutações (detectadas): V1 a chave volta a ser o dia, V2 a semana em UTC."""
    from datetime import datetime, timezone
    S = virada.semana_brasilia
    utc = timezone.utc
    assert S(datetime(2026, 11, 9, 3, 0, tzinfo=utc)) == "2026-11-09"      # seg 00:00 BRT
    assert S(datetime(2026, 11, 10, 15, 0, tzinfo=utc)) == "2026-11-09"    # terça
    assert S(datetime(2026, 11, 16, 2, 59, tzinfo=utc)) == "2026-11-09"    # dom 23:59 BRT
    assert S(datetime(2026, 11, 16, 3, 0, tzinfo=utc)) == "2026-11-16"     # seg 00:00 BRT
    assert S(datetime(2026, 11, 9, 2, 59, tzinfo=utc)) == "2026-11-02"     # dom 23:59 BRT


def test_vigia_desligado_sem_a_variavel(monkeypatch):
    monkeypatch.delenv("VIGIA_POR_DIA", raising=False)
    assert virada.vigia_por_dia() == 0
    monkeypatch.setenv("VIGIA_POR_DIA", "3")
    assert virada.vigia_por_dia() == 3
    monkeypatch.setenv("VIGIA_POR_DIA", "x")
    assert virada.vigia_por_dia() == 0
