"""Gate do dicionário de DESCRIÇÃO da Ficha (`app/descricao_ficha.py`; s413, 12/10/2026).

Regra do Feca: chamada extra à IA só para a descrição, nunca. O mercado é aprendido UMA vez,
sem lado e sem linha, e depois nenhuma variação dele vai à IA.

Pares REAIS (`tests/ficha_descricao_pares.json`, gerado do banco só com SELECT: perna do cru ×
o trecho que a IA escreveu para ela, 35 mercados de 7 casas). Em cada par, um bilhete ENSINA
e outro bilhete do mesmo mercado, com outra linha, outro lado ou outro jogo, CONFERE: a Ficha
monta a descrição dele igual à da IA sem nunca ter visto aquela variação.

Mutações provadas (aplicadas, teste ao lado vermelho):
  M1. o lado fica na chave                                → test_chave_sem_lado_e_sem_linha
  M2. a linha fica na chave (sem `{n}`)                   → test_chave_sem_lado_e_sem_linha
  M3. sem o esporte na chave                              → test_mesmo_mercado_em_outro_esporte…
  M4. `1`/`2`/`X` ficam como código                       → test_selecao_1_2_x_vira_o_time_ou_empate
  M5. o jogo sai com `vs`                                 → test_separador_do_jogo_e_sempre_v
  M6. o período fica fixo no valor (sem `{nK}`)           → test_o_periodo_vira_marca
  M6b. número que não veio do cru fica no valor          → test_descricao_que_nao_fecha_com_o_cru_nao_vota
  M7. voto que não fecha com o cru vale                   → test_descricao_que_nao_fecha_com_o_cru_nao_vota
      (escaparam na 1ª rodada: a M6 mirava o ramo do número de fora, e a M7 era barrada
      também pela regra do número; cada uma ganhou um caso que só ela barra)
  M8. número do cru que não chega à descrição passa       → test_a_linha_do_cru_tem_de_chegar_a_descricao
  M9. variantes da IA contam como votos diferentes        → test_variantes_da_ia_sao_um_voto_so
  M10. a seleção do par mantém o número (P6)              → test_par_da_selecao_troca_numero
  M11. o Feca não cobre a chave mais específica (P5)      → test_feca_cobre_as_chaves_mais_especificas
  M13. o período segue a IA, não o Master (§12.10)        → test_o_periodo_vira_marca
  M14. o mercado do LADO aceita voto sem o time          → test_descricao_que_nao_fecha_com_o_cru_nao_vota
  M15. o `semente_log` esconde a contradição de descrição  → test_semente_log_registra…
  M12. pernas fora da ordem do cru                       → test_montagem_igual_a_da_ia_nas_fixtures
  Inócua (registrada): exigir o time também no voto do mercado com o NOME do time; o
  `aprender` já recusa a descrição sem o `{time}` que o cru tem (é a M7).
  Mais 6 no cabeçalho de `test_virada.py` (D1, D2) e do harness de banco (D3 a D6).
  s415 (T1, o jogador fora da chave; 13/10/2026), 15 de 15 detectadas:
  J1. a chave ignora o jogador                           → test_dois_jogadores_no_mesmo_mercado…
  J2. (saiu na s416: o voto na chave do próprio jogador não existe mais, D29)
  J3. a montagem não tenta a chave de qualquer jogador   → test_dois_jogadores…
  J4. a chave do próprio jogador vem primeiro            → test_d27_ressaltos_rebotes…
  J5. palavra de mercado vira jogador                    → test_jogador_nao_e_palavra_de_mercado…
  J6. o time do jogo vira jogador                        → test_jogador_nao_e_palavra_de_mercado…
  J7. sem a abreviação (`Sr.`) no nome                   → test_jogador_nao_e_palavra_de_mercado…
  J8. a seleção com o time fica na chave de categoria    → test_selecao_com_o_time_do_jogo_vira_ent…
  J9. `traduzir` sem a chave de categoria do jogador     → test_dois_jogadores…
  J10. a semente não vota no mercado do jogador          → test_dois_jogadores…
  J11. o handicap do mercado (1xBet) não vira `{hc}`     → test_handicap_da_1xbet…
  J12. o lado do handicap fica na chave                  → test_handicap_da_1xbet…
  J13. sem trocar a letra cirílica (`Handiсap`)          → test_handicap_da_1xbet…
  J14. a linha do handicap não precisa chegar            → test_handicap_da_1xbet…
  J15. `Individual Total 2` não diz o time               → test_handicap_da_1xbet… (15 de 15)
  J16. a lista de contradições mostra o termo do Feca    → test_semente_log_registra…
  (bateria: `scratchpad/mutar5.py` da s415; V1 a V4 e W1 a W7 nos cabeçalhos do harness de
  banco e de `test_virada.py`)
  s416 (D29, D27, 1win; 14/10/2026), 17 de 17 detectadas (e as da s415 de novo, todas pegas):
  D1. sem a regra a (total puro)                         → test_d29_a_ordem_das_regras
  D2. sem a regra b                                      → test_d29_a_ordem_das_regras
  D3. a regra b sem o esqueleto (a forma que omite ganha) → test_d29_a_ordem_das_regras
  D4. sem a regra c                                      → test_d29_a_ordem_das_regras
  D5. a regra c sem exigir palavra de verdade (`VFL`)    → test_d29_a_ordem_das_regras
  D6. o minuto não vira um estilo só                     → test_d29_dois_estilos…
  D7. o `canonico` não usa o estilo                      → test_d29_dois_estilos…
  D8. `Ressaltos`/`Rebounds` não viram `Rebotes`         → test_d27_ressaltos_rebotes…
  D9. `PRA` não é reconhecido                            → test_d29_a_ordem_das_regras
  D10. a descrição volta à maioria de 90%                → test_d29_dois_estilos…
  D11. o empate exato não é marcado                      → test_d29_a_ordem_das_regras
  D12. a regra e não vai para a revisão                  → test_semente_log_descricao_nao_fica…
  J17. o lado do jogo (`Time de Fora`) vira jogador      → test_jogador_nao_e_palavra_de_mercado…
  J18. o jogador só no começo da chave                   → test_jogador_depois_do_subjogo…
  J19. `Vencedor. Quarto` sem a forma do Feca            → test_vencedor_quarto_e_o_gemeo…
  H1. handicap positivo sem sinal (1win)                 → test_handicap_positivo_sem_sinal…
  H2. o total puro com o jogo em ` - ` (1win)            → test_total_puro_da_1win…
  (bateria: `scratchpad/mutar6.py` da s416; W3, W9, R1 e R2 no harness de banco e em
  `test_virada.py`)

O QUE NÃO COBRE: se o nome do mercado que a IA escreveu está CERTO (o dicionário aprende o que
ela escreve; o erro se conserta depois, D24, `corrigir_termo.py descricao`), a ordem dos nomes
(`Leclerc, Charles`: a IA vira em metade das vezes; a Ficha fica com o cru, `MASTER_DESCRICAO
§9`) e a 1xBet além do que as fixtures têm (19 crus, o subjogo no nome do jogo). O jogador
só é achado no COMEÇO do mercado (a DEX); jogador no meio do mercado (`Total de remates de
Luca Cagnoni`) segue uma chave por jogador.
"""
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, "app")

import descricao_ficha as D  # noqa: E402
import dicionario  # noqa: E402

PARES = json.loads((Path(__file__).resolve().parent / "ficha_descricao_pares.json")
                   .read_text(encoding="utf-8"))


def _p(esporte, evento, mercado, selecao=None, linha=None):
    return {"esporte_casa": esporte, "evento": evento, "mercado_casa": mercado,
            "selecao_casa": selecao, "linha": linha}


def _aprende(p, ia):
    return D.votos({"pernas": [p]}, ia)


def test_chave_sem_lado_e_sem_linha():
    """`1-st half corner over 4.5`, `over 3.5` e `under 5.5` são o MESMO mercado (Feca)."""
    ks = {D.chave(_p("Football", "A vs B", "Corners. Total. 1-st half", s))
          for s in ("Over 4.5", "Over 3.5", "Under 5.5")}
    assert ks == {"football | corners. total. {n}-st half"}
    # a 1xBet escreve o lado e a linha dentro do mercado
    ks = {D.chave(_p("Futebol", "A - B", m)) for m in
          ("Total acima de (2.5)", "Total abaixo de (3.5)", "Total < (1.5)")}
    assert ks == {"futebol | total ({n})"}
    # mas QUAL time não é linha: Equipa 1 e Equipa 2 são mercados diferentes
    assert D.chave(_p("Futebol", "A - B", "Equipa 1 Total acima de 0.5 no minuto 10")) \
        != D.chave(_p("Futebol", "A - B", "Equipa 2 Total acima de 0.5 no minuto 10"))
    # o time do jogo escrito no mercado vira `{time}`
    assert D.chave(_p("football", "Kashima Antlers vs Gamba Osaka", "Corners Gamba Osaka total",
                      "Over 4.5")) == "football | corners {time} total"


def test_mesmo_mercado_em_outro_esporte_e_outra_chave():
    """`1st half - total` é `Gols 1º Tempo` no futebol e `Pontos 1ª Metade` no basquete."""
    a = D.chave(_p("Soccer", "A vs B", "1st half - total", "over 1.5"))
    b = D.chave(_p("Basketball", "A vs B", "1st half - total", "over 81.5"))
    assert a != b and a.startswith("soccer | ") and b.startswith("basketball | ")


def test_montagem_igual_a_da_ia_nas_fixtures():
    """Para cada mercado real: o bilhete que ensina gera o valor; o OUTRO bilhete (outra linha,
    outro lado, outro jogo) sai igual ao que a IA escreveu para ele."""
    assert len(PARES) >= 30 and len({x["casa"] for x in PARES}) >= 7
    for x in PARES:
        votos = _aprende(x["ensina"], x["ensina"]["ia"])
        assert votos == [(x["chave"], x["valor"])], x
        termos = {("descricao", x["chave"]): x["valor"]}
        assert D.chave(x["confere"]) == x["chave"], x
        desc, faltam = D.montar({"pernas": [x["confere"]]}, termos)
        assert (desc, faltam) == (x["confere"]["ia"], []), x
    # múltipla: perna a perna, unidas por ` // `, na ordem do cru
    a, b = PARES[0]["confere"], PARES[1]["confere"]
    termos = {("descricao", PARES[0]["chave"]): PARES[0]["valor"],
              ("descricao", PARES[1]["chave"]): PARES[1]["valor"]}
    assert D.montar({"pernas": [a, b]}, termos)[0] == f"{a['ia']} // {b['ia']}"
    assert D.montar({"pernas": [b, a]}, termos)[0] == f"{b['ia']} // {a['ia']}"


def test_selecao_1_2_x_vira_o_time_ou_empate():
    """MyStake manda a seleção como `2` e a linha à parte; a IA escreve o time."""
    p = _p("Futebol", "FC Augsburgo vs Bayern de Munique", "Handicap de escanteios", "2", "-3.5")
    assert _aprende(p, "Bayern de Munique -3.5 Escanteios [FC Augsburgo v Bayern de Munique]") \
        == [("futebol | handicap de escanteios", "{ent} {hc} Escanteios")]
    termos = {("descricao", "futebol | handicap de escanteios"): "{ent} {hc} Escanteios"}
    q = _p("Futebol", "Lazio vs Monza", "Handicap de escanteios", "1", "+1.5")
    assert D.montar({"pernas": [q]}, termos)[0] == "Lazio +1.5 Escanteios [Lazio v Monza]"
    # 1xBet: `X` no mercado é o empate, `V2` o time de fora
    x = _p("Futebol", "KDV - Khimik Dzerzhinsk", "X")
    assert _aprende(x, "Empate [KDV v Khimik Dzerzhinsk]") == [("futebol | x", "{ent}")]
    v2 = _p("Futebol", "Agropecuario - Ferrocarril Midland", "V2")
    assert D.montar({"pernas": [v2]}, {("descricao", "futebol | v{n}"): "{ent}"})[0] \
        == "Ferrocarril Midland [Agropecuario v Ferrocarril Midland]"


def test_separador_do_jogo_e_sempre_v():
    termos = {("descricao", "x | vencedor"): "{ent}"}
    for ev in ("A vs. B", "A vs B", "A v B", "A - B"):
        assert D.montar({"pernas": [_p("X", ev, "Vencedor", "B")]}, termos)[0] == "B [A v B]"
    # evento que não é confronto não vira jogo (`MASTER_DESCRICAO §8`)
    assert D.jogo("Grande Prêmio do Bahrein. Corrida. Apostas Especiais") == ""


def test_o_periodo_vira_marca():
    """`Winner. Set 1` e `Winner. Set 2` são o mesmo mercado; o número do período não é a linha
    e não pode ficar fixo no valor."""
    p = _p("tennis", "Shelbayh Abedallah vs Glinka Daniil", "Winner. Set 1", "Shelbayh Abedallah")
    assert _aprende(p, "Shelbayh Abedallah 1º Set [Shelbayh Abedallah v Glinka Daniil]") \
        == [("tennis | winner. set {n}", "{ent} {n1}º Set")]
    q = _p("tennis", "Sinner vs Alcaraz", "Winner. Set 2", "Alcaraz")
    assert D.montar({"pernas": [q]}, {("descricao", "tennis | winner. set {n}"): "{ent} {n1}º Set"}
                    )[0] == "Alcaraz 2º Set [Sinner v Alcaraz]"
    # o recorte de período segue o Master (§12.10) pelo esporte do Sharpen, não a maioria da IA
    termos = {("descricao", "basquete | {n}ª metade - handicap"): "{ent} {hc} {n1}º Tempo",
              ("descricao", "futebol | {n}ª metade - handicap"): "{ent} {hc} {n1}ª Metade",
              ("esporte", "basquete"): "Basquete", ("esporte", "futebol"): "Futebol"}
    b = _p("Basquete", "Joventut vs Bnei", "1ª metade - handicap", "1", "-11")
    f = _p("Futebol", "Holanda vs Sérvia", "1ª metade - handicap", "2", "+0.5")
    assert D.montar({"pernas": [b]}, termos)[0] == "Joventut -11 1ª Metade [Joventut v Bnei]"
    assert D.montar({"pernas": [f]}, termos)[0] == "Sérvia +0.5 1º Tempo [Holanda v Sérvia]"


def test_descricao_que_nao_fecha_com_o_cru_nao_vota():
    p = _p("Soccer", "Boston vs Southend", "Total corners", "over 9.5")
    assert _aprende(p, "Over 9.5 Escanteios [Boston v Southend]") == \
        [("soccer | total corners", "{ou} Escanteios")]
    assert _aprende(p, "Under 9.5 Escanteios [Boston v Southend]") == []      # outro lado
    assert _aprende(p, "Over 8.5 Escanteios [Boston v Southend]") == []       # outra linha
    assert _aprende(p, "Over 9.5 Escanteios [Leeds v Southend]") == []        # outro jogo
    assert _aprende(p, "Boston v Southend - Over 9.5 Escanteios [Boston v Southend]") == []
    # nome do jogo que sobra no valor depois das marcas
    ml = _p("Soccer", "Boston vs Southend", "Winner", "Boston")
    assert _aprende(ml, "Boston [Boston v Southend]") == [("soccer | winner", "{ent}")]
    assert _aprende(ml, "Boston Vencedor Boston [Boston v Southend]") == []
    # a seleção do cru não está na descrição: a IA descreveu o OUTRO time
    assert _aprende(ml, "Southend [Boston v Southend]") == []
    # número que não veio do cru (nem linha, nem número do mercado): não vota
    assert _aprende(p, "Over 9.5 Escanteios 1º Tempo [Boston v Southend]") == []
    # mercado do time sem o time: a IA escreveu o total do jogo
    t = _p("football", "Kashima Antlers vs Gamba Osaka", "Corners Gamba Osaka total", "Over 4.5")
    assert _aprende(t, "Over 4.5 Escanteios [Kashima Antlers v Gamba Osaka]") == []
    assert _aprende(t, "Gamba Osaka Over 4.5 Escanteios [Kashima Antlers v Gamba Osaka]") == \
        [("football | corners {time} total", "{time} {ou} Escanteios")]
    # o mesmo quando o mercado diz o LADO (MyStake: `Time de casa total de cartões`)
    c = _p("Futebol", "Lazio vs Monza", "Time de casa total de cartões", "Acima", "2.5")
    assert _aprende(c, "Over 2.5 Cartões [Lazio v Monza]") == []
    assert _aprende(c, "Lazio Over 2.5 Cartões [Lazio v Monza]") == \
        [("futebol | time de casa total de cartões", "{t1} {ou} Cartões")]


def test_a_linha_do_cru_tem_de_chegar_a_descricao():
    """Valor que não pede a linha, numa perna que tem linha, não monta: a aposta vai à IA."""
    p = _p("Soccer", "A vs B", "Handicap", "A (-1.5)")
    assert D.montar_perna(p, "{ent}") is None
    assert D.montar_perna(p, "{ent} {hc}") == "A -1.5 [A v B]"
    assert D.montar_perna(_p("Soccer", "A vs B", "Total", "Ímpar"), "{ou} Gols") is None


def test_variantes_da_ia_sao_um_voto_so():
    """`Time - Over` e `Time Over`, `1ª Metade` e `1º Tempo`: o mesmo mercado escrito de dois
    jeitos pela IA. O valor guardado é a variante mais votada."""
    assert D.canonico("{t2} - {ou} Escanteios") == D.canonico("{t2} {ou} Escanteios")
    assert D.canonico("{ou} Pontos {n1}ª Metade") == D.canonico("{ou} Pontos {n1}º Tempo")
    f = {"tipo": "simples", "pernas": [_p("Futebol", "A vs B", "Time de fora total de escanteios",
                                          "Acima", "4.5")]}
    pares = ([("MYSTAKE", f, "Futebol", "Escanteios", "B Over 4.5 Escanteios [A v B]")] * 7
             + [("MYSTAKE", f, "Futebol", "Escanteios", "B - Over 4.5 Escanteios [A v B]")] * 3)
    unanimes, contraditos, _ = dicionario.votar(pares)
    k = ("MYSTAKE", "descricao", "futebol | time de fora total de escanteios")
    assert unanimes[k] == ("{t2} {ou} Escanteios", 10) and k not in contraditos


def test_par_da_selecao_troca_numero():
    """P6 (parecer 013): `total pontos | menos de 71.5` até `80.5` eram 10 termos."""
    def par(sel):
        f = {"tipo": "simples", "pernas": [_p("Badminton", "A vs B", "Total pontos", sel)]}
        return dicionario.chaves(f)[-1]
    assert par("Menos de 71.5") == par("Menos de 80.5") == ("categoria", "total pontos | menos de {n}")
    assert par("1") != par("2")                                   # código não é linha


def test_feca_cobre_as_chaves_mais_especificas():
    """P5 (parecer 013): a correção do Feca vence também `mercado | seleção`."""
    feca = [("DEXSPORT", "categoria", "winner. quarter {n}")]
    assert dicionario.coberto_pelo_feca(feca, "DEXSPORT", "categoria", "winner. quarter {n}")
    assert dicionario.coberto_pelo_feca(feca, "DEXSPORT", "categoria",
                                        "winner. quarter {n} | bursaspor")
    assert not dicionario.coberto_pelo_feca(feca, "MYSTAKE", "categoria", "winner. quarter {n}")
    assert not dicionario.coberto_pelo_feca(feca, "DEXSPORT", "categoria", "winner. quarter")
    assert dicionario.coberto_pelo_feca([("*", "categoria", "fastest lap")], "BETPANDA",
                                        "categoria", "fastest lap | norris, lando")


def test_semente_log_descricao_nao_fica_contradita_e_o_empate_vai_para_a_revisao(monkeypatch):
    """D29 (s416): a descrição nunca entra na lista de contraditos; o empate que a regra não
    decide (`e`, a mais votada) vai para a REVISÃO. A categoria segue com os 90% e com a lista
    de contraditos, e o termo que o Feca já corrigiu sai das duas listas (s415)."""
    f = {"tipo": "simples", "pernas": [_p("Baseball", "A vs B", "Total hits", "over 9.5")]}

    async def pares(conn):
        return ([("DUEL", f, "Baseball", "Pontos", "Over 9.5 Hits [A v B]"),
                 ("DUEL", f, "Baseball", "Corridas", "Over 9.5 Rebatidas [A v B]")], [], {})

    async def nada(*a, **k):
        return []

    async def grava(conn, u):
        return len(u)
    monkeypatch.setattr(dicionario, "pares", pares)
    monkeypatch.setattr(dicionario, "regravar_mes", nada)
    monkeypatch.setattr(dicionario, "gravar_semente", grava)

    class _C:
        async def fetch(self, sql, *a):
            return []

        async def execute(self, sql, *a):
            self.args = a
    c = _C()
    asyncio.run(dicionario.semear(c, "teste"))
    contra, revisao = json.loads(c.args[3]), json.loads(c.args[6])
    assert [x["tipo"] for x in contra] == ["categoria"]            # `total hits`: Pontos × Corridas
    assert [(x["tipo"], x["termo"]) for x in revisao] == [("descricao", "baseball | total hits")]

    # s415: o termo que o Feca já corrigiu sai das listas (não é mais para revisar)
    class _CF(_C):
        async def fetch(self, sql, *a):
            if "origem = 'feca'" in sql:
                return [{"casa": "DUEL", "tipo": "descricao", "termo_casa": "baseball | total hits"},
                        {"casa": "DUEL", "tipo": "categoria", "termo_casa": "total hits"}]
            return []
    c = _CF()
    asyncio.run(dicionario.semear(c, "teste"))
    assert json.loads(c.args[3]) == [] and json.loads(c.args[6]) == []


def _mega(evento, mercado, codigo):
    return {"tipo": "simples", "codigo": codigo, "pernas": [_p("Football", evento, mercado)]}


def test_d29_dois_estilos_do_mesmo_mercado_saem_pela_ficha():
    """D29 (d): estilo não é voto diferente. Megapari, `Team 1 Total Over 1.5 In 75 Minute`: a IA
    escreveu `até 75'` num bilhete e `75º Minuto` no outro (reais, 13/10). Até a s415 eram dois
    votos 1 × 1, a chave ficava contradita e toda aposta desse mercado ia para a IA. Agora é um
    voto só, na forma `{n}min` (o Master não tem forma para o minuto), e o terceiro bilhete,
    que a semente nunca viu, sai pela Ficha."""
    a = _mega("Scotland (Women) - Czech Republic (Women)", "Team 1 Total Over 1.5 In 75 Minute", "m1")
    b = _mega("Vissel Kobe - Jeonbuk Hyundai Motors", "Team 1 Total Under 2.5 In 75 Minute", "m2")
    termos, contra = _semente([
        ("MEGAPARI", a, "Futebol", "Gols",
         "Scotland (Women) Over 1.5 Gols até 75' [Scotland (Women) v Czech Republic (Women)]"),
        ("MEGAPARI", b, "Futebol", "Gols",
         "Vissel Kobe Under 2.5 Gols 75º Minuto [Vissel Kobe v Jeonbuk Hyundai Motors]")],
        casa="MEGAPARI")
    k = "football | team 1 total {n} in {n} minute"
    assert contra == {} and termos[("descricao", k)] == "{time} {ou} Gols {n3}min"
    novo = _mega("Austria (Women) - Kosovo (Women)", "Team 1 Total Over 2.5 In 75 Minute", "m3")
    assert dicionario.traduzir(novo, termos) == ("Futebol", "Gols", [])
    assert D.montar(novo, termos, dicionario.descricao_perna) == (
        "Austria (Women) Over 2.5 Gols 75min [Austria (Women) v Kosovo (Women)]", [])
    # os estilos de minuto que a IA escreveu na Megapari (semente_log 17) são uma forma só
    for v in ("{time} {ou} Gols {n3}min", "{time} - {ou} Gols {n3}º Minuto",
              "{time} {ou} Gols {n3} Min", "{time} - {ou} Gols ({n3} min)",
              "{time} {ou} Gols até {n3}'", "{time} {ou} Gols (até Min {n3})",
              "{time} {ou} Gols até o {n3}º Minuto", "{time} {ou} Gols In {n3} Minute",
              "{time} {ou} Gols no {n3}º Minuto", "{time} - {ou} Gols {n3} Minutos",
              "{time} {ou} Gols Primeiros {n3} Minutos"):
        assert D.canonico(v) == "{time} {ou} Gols {n3}min", v


def test_d29_a_ordem_das_regras():
    """D29: a. total puro sem objeto; b. a palavra do Master; c. o mercado escrito vence o time
    sozinho; d. estilo (já no agrupamento); e. a mais votada, para a revisão."""
    dec = D.decidir
    # a. total puro: só `{ou}`, mesmo com o objeto em maioria
    assert dec("basketball | total. com prorrogação", {"{ou} Pontos": 4, "{ou}": 1}) == ("{ou}", "a")
    assert dec("mixed martial arts | total", {"{ou} Rounds": 3, "{ou} Total": 1}) == ("{ou}", "a")
    assert dec("hóquei no gelo | total (incluindo prolongamento e penalties)",
               {"{ou} Gols": 6, "{ou} Total": 1}) == ("{ou}", "a")
    # … e só no total PURO (com objeto no mercado não é a)
    assert dec("football | shots towards the goal total ({n})",
               {"{ou} Chutes no Gol": 6, "{ou} Chutes": 4})[1] != "a"
    # b. a palavra do Master vence a que não é dele (mesmo em minoria)
    assert dec("baseball | total hits ({n})", {"{ou} Hits": 3, "{ou} Corridas": 1})         == ("{ou} Corridas", "b")
    assert dec("baseball | most hits - team 2", {"{time} - Most Hits": 2, "{time} - Mais Hits": 1})         == ("{time} - Mais Hits", "b")
    # … só entre formas do mesmo esqueleto: a que OMITE o minuto (1 voto, todas as palavras do
    # Master) não derruba as 63 que o escrevem (Megapari, 14/10; foi a 1ª versão desta regra)
    k = "football | team 1 total {n} in {n} minute"
    assert dec(k, {"{time} {ou} Gols {n3}º Minuto": 19, "{time} - {ou} Gols {n3}min": 44,
                   "{time} {ou} Gols": 1, "{time} {ou} Gols {n1}º Tempo": 1})[0]         == "{time} - {ou} Gols {n3}min"                 # a variante mais votada, no estilo único
    # c. o mercado escrito vence o time sozinho; `VFL` não é mercado (não decide)
    assert dec("football | ambas as equipes vão marcar", {"{ent}": 3, "Ambas Marcam - {ent}": 1})         == ("Ambas Marcam - {ent}", "c")
    assert dec("baseball | most hits - team 2", {"{time} - Most Hits": 2, "{time}": 1})         == ("{time} - Most Hits", "c")
    assert dec("football | escanteios. vencedor", {"{ent}": 1, "VFL {ent}": 1})[1] == "e-empate"
    # d. o estilo (` - `, minuto, `Ressaltos`/`Rebounds`, `PRA`) é um voto só
    assert dec("basketball | {jogador}. ressaltos. com prorrogação",
               {"{jogador} - {ou} Rebotes": 5, "{jogador} - {ou} Rebounds": 4,
                "{jogador} - {ou} Ressaltos": 14}) == ("{jogador} - {ou} Rebotes", "unico")
    assert D.estilo("{jogador} - {ou} PRA") == D.estilo("{jogador} - {ou} Pontos+Rebotes+Assistências")         == "{jogador} - {ou} Pontos + Assistências + Rebotes"
    # combinação que o Feca não decidiu fica como veio (só a grafia)
    assert D.estilo("{ent} - {ou} Rebotes+Assistências") == "{ent} - {ou} Rebotes + Assistências"
    # e. empate que nenhuma regra decide: a mais votada, para a revisão
    assert dec("baseball | total hits ({n})", {"{ou} Hits": 1, "{ou} Rebatidas": 2})         == ("{ou} Rebatidas", "e")


# ── s415 (T1): o jogador fora da chave ───────────────────────────────────────────────────

_DEX_JOGO = "BC Dubai vs Crvena Zvezda"


def _dex(mercado, selecao, codigo):
    return {"tipo": "simples", "codigo": codigo,
            "pernas": [_p("basketball", _DEX_JOGO, mercado, selecao)]}


def _semente(pares, casa="DEXSPORT"):
    """A semente de verdade (`dicionario.votar`) e os termos da casa, como o `carregar`."""
    unanimes, contraditos, _ = dicionario.votar(pares)
    termos = {(t, k): v for (c, t, k), (v, _) in unanimes.items() if c in ("*", casa)}
    return termos, contraditos


def test_dois_jogadores_no_mesmo_mercado_o_primeiro_ensina_o_segundo_sai_pela_ficha():
    """DEX (13/10): `basketball | alec peters. ressaltos. com prorrogação` era uma chave POR
    jogador, e todo jogador novo ia para a IA. O primeiro ensina; o segundo, que a semente
    nunca viu, sai pela Ficha: esporte, categoria e descrição, sem IA."""
    ensina = _dex("Dwayne Bacon. Ressaltos. Com prorrogação", "Menos 3.5", "a1")
    confere = _dex("Alec Peters. Ressaltos. Com prorrogação", "Mais 5.5", "a2")
    termos, _ = _semente([("DEXSPORT", ensina, "Basquete", "Player Props",
                           "Dwayne Bacon - Under 3.5 Rebotes [BC Dubai v Crvena Zvezda]")])
    assert termos[("descricao", "basketball | {jogador}. ressaltos. com prorrogação")] \
        == "{jogador} - {ou} Rebotes"
    assert ("descricao", D.chave(confere["pernas"][0])) not in termos   # a do 2º não existe
    assert dicionario.traduzir(confere, termos) == ("Basquete", "Player Props", [])
    assert D.montar(confere, termos, dicionario.descricao_perna) == (
        "Alec Peters - Over 5.5 Rebotes [BC Dubai v Crvena Zvezda]", [])


def test_d27_ressaltos_rebotes_e_rebounds_sao_um_mercado_so():
    """D27 (s416): `Ressaltos`, `Rebotes` e `Rebounds` = `Rebotes`. Na s415 a chave de qualquer
    jogador ficava contradita e o jogador novo ia para a IA; agora sai pela Ficha. A chave do
    próprio jogador, com o nome, só vale quando é do Feca (a semente não vota mais nela)."""
    a, b = (_dex(f"{n}. Ressaltos. Com prorrogação", "Menos 3.5", n) for n in ("Joel Parra",
                                                                                 "Moses Wright"))
    termos, contra = _semente([
        ("DEXSPORT", a, "Basquete", "Player Props", "Joel Parra - Under 3.5 Rebotes [BC Dubai v Crvena Zvezda]"),
        ("DEXSPORT", b, "Basquete", "Player Props", "Moses Wright - Under 3.5 Ressaltos [BC Dubai v Crvena Zvezda]")])
    assert contra == {}
    assert ("descricao", "basketball | joel parra. ressaltos. com prorrogação") not in termos
    novo = _dex("Zach LeDay. Ressaltos. Com prorrogação", "Mais 4.5", "y")
    assert D.montar(novo, termos) == ("Zach LeDay - Over 4.5 Rebotes [BC Dubai v Crvena Zvezda]", [])
    # a correção do Feca para UM jogador vence a de qualquer jogador? Não: a de qualquer um vem
    # primeiro (é a regra do mercado); a do jogador só entra sem ela
    so_dele = {("descricao", "basketball | zach leday. ressaltos. com prorrogação"): "{ou} X"}
    assert D.montar(novo, so_dele)[0] == "Over 4.5 X [BC Dubai v Crvena Zvezda]"
    assert D.montar(novo, {**so_dele, **termos})[0] == \
        "Zach LeDay - Over 4.5 Rebotes [BC Dubai v Crvena Zvezda]"


def test_jogador_nao_e_palavra_de_mercado_nem_time():
    """`_jogador`: duas palavras ou mais com maiúscula no começo do mercado, antes de `. ` ou de
    `Total`. Mercado (`Match Winner`, `Double Chance. 1st Half`) e time do jogo não são jogador."""
    J = D._jogador
    assert J("Alec Peters. Ressaltos. Com prorrogação") == "Alec Peters"
    assert J("Jerian Grant Total de pontos. Com prorrogação") == "Jerian Grant"
    assert J("Kyle Pitts Sr. Total receções") == "Kyle Pitts Sr."
    assert J("Luca Cagnoni total de remates à baliza (incl. prolongamento)") == "Luca Cagnoni"
    assert J("Escanteios Anderlecht total") == "" and J("Corners Manchester City total") == ""
    assert J("Sander van Ockenburg. 180s") == "Sander van Ockenburg"
    for m in ("Match Winner", "Double Chance. 1st Half", "Handicap. Com prorrogação",
              "Total. 1ª metade", "Corners. Double chance", "Ambas as equipes vão marcar"):
        assert J(m) == "", m
    # s416: o LADO do jogo não é jogador (MyStake: `Time de Fora total de escanteios` virava
    # `{jogador} total de escanteios`, juntando o mercado da casa e o de fora)
    for m in ("Time de Fora total de escanteios", "Time de Casa total de cartões",
              "Home Team total corners", "Away Team total cards"):
        assert J(m) == "", m
    assert J("Kaspiy Aktau total. 1-st half", ("Kaspiy Aktau", "Oulu")) == ""
    assert J("Kaspiy Aktau. Escanteios", ("Kaspiy Aktau", "Oulu")) == ""        # time do jogo
    # a chave de categoria troca o jogador também
    f = _dex("Alec Peters. Ressaltos. Com prorrogação", "Menos 3.5", "z")
    assert ("categoria", "{jogador}. ressaltos. com prorrogação") in dicionario.chaves(f)


def test_jogador_depois_do_subjogo_da_megapari():
    """s416: na Megapari o jogo é `Players' stats A - Players' stats B` e o prefixo entra no
    mercado efetivo (`players' stats Breanna Stewart total assists`): o jogador vira
    `{jogador}` também no meio da chave, e não só no começo."""
    p = _p("Basketball", "Players' stats New York Liberty (Women) - Players' stats Atlanta Dream "
           "(Women) (Including Overtime)", "Breanna Stewart Total Assists Over 3.5")
    assert D.chave(p, jogador=True) == "basketball | players' stats {jogador} total assists {n}"
    v = D.aprender(p, "Breanna Stewart - Over 3.5 Assistências [New York Liberty (Women) v "
                      "Atlanta Dream (Women) (Including Overtime)]")
    assert v == "{jogador} - {ou} Assistências"


def test_vencedor_quarto_e_o_gemeo_do_winner_quarter():
    """D27 (s416): `Vencedor. Quarto N` (DEX em português) segue o que o Feca decidiu para
    `Winner. Quarter N`: ML, descrição `Time X - NQ [A v B]`."""
    for merc in ("Winner. Quarter 1", "Vencedor. Quarto 1"):
        p = _p("basketball", "BC Dubai vs Crvena Zvezda", merc, "BC Dubai")
        assert dicionario.descricao_perna(p) == "BC Dubai - 1Q [BC Dubai v Crvena Zvezda]", merc


def test_selecao_com_o_time_do_jogo_vira_ent_na_chave_de_categoria():
    """`resultado da partida | ng ka long angus` era um termo por jogador (T1)."""
    ev = "Ng Ka Long Angus vs Lee Zii Jia"
    assert dicionario.sel_chave("Ng Ka Long Angus", ev) == "{ent}"
    assert dicionario.sel_chave("Lee Zii Jia", ev) == "{ent}"
    assert dicionario.sel_chave("Roma ou empate", "Roma vs Lazio") == "{ent} ou empate"
    assert dicionario.sel_chave("Peristeri (+6)", "Peristeri vs AEK") == "{ent} (+{n})"
    assert dicionario.sel_chave("1", ev) == "1" and dicionario.sel_chave("X", ev) == "x"
    assert dicionario.sel_chave("Over 2.5", ev) == "over {n}"


def test_handicap_da_1xbet_lado_e_sinal_sao_o_mesmo_mercado():
    """Megapari (T1): `Handicap 1 (-1.5)`, `Handicap 1 (1.5)` e `Handicap 2 (2.5)` são UM
    mercado; o lado vira o `{time}` e o sinal com a linha vira o `{hc}`."""
    jogo = "Lakers - Celtics"
    ps = [_p("Basketball", jogo, m) for m in ("Handicap 1 (-1.5)", "Handicap 1 (1.5)",
                                               "Handicap 2 (2.5)", "Handicap 2 (-3)")]
    assert {D.chave(p) for p in ps} == {"basketball | handicap {hc}"}
    termos = dict(_aprende_termos(ps[0], "Lakers -1.5 [Lakers v Celtics]"))
    assert D.montar({"pernas": [ps[2]]}, termos)[0] == "Celtics +2.5 [Lakers v Celtics]"
    assert D.montar({"pernas": [ps[3]]}, termos)[0] == "Celtics -3 [Lakers v Celtics]"
    # a linha do mercado tem de chegar à descrição
    assert D.montar({"pernas": [ps[2]]}, {("descricao", "basketball | handicap {hc}"): "{time}"}) \
        == (None, ["basketball | handicap {hc}"])
    # `Individual Total 2` diz QUAL time: vira `{time}` (a IA votava `{t1}` contra `{t2}`)
    it = _p("Football", "Lakers - Celtics", "Individual Total 2 Over (0.5)")
    assert D.decompor(it)["time"] == "Celtics"
    assert _aprende(it, "Celtics Over 0.5 Gols [Lakers v Celtics]") == \
        [("football | individual total 2 ({n})", "{time} {ou} Gols")]
    # a Megapari escreve `Handiсap` com o `с` cirílico
    assert D.chave(_p("Esports", "A - B", "Handiсap 2 (1.5) Rounds")) == "esports | handicap {hc} rounds"


def _aprende_termos(p, ia):
    return {("descricao", k): v for k, v in _aprende(p, ia)}


def test_handicap_positivo_sem_sinal_da_1win():
    """s416: a 1win escreve o handicap positivo sem sinal (`FC Slavia Mozyr 1.5`, real, 13/10).
    A Ficha lia o nome com o número junto e descrevia `FC Slavia Mozyr 1.5`; a IA escreveu
    `+1.5`. Só em mercado de handicap: fora dele o número é parte do nome. Mutação H1 (sem o
    ramo): detectada."""
    p = _p("Futebol", "Din Minsk - FC Slavia Mozyr", "Handicap", "FC Slavia Mozyr 1.5")
    d = D.decompor(p)
    assert (d["ent"], d["hc"]) == ("FC Slavia Mozyr", "+1.5")
    assert D.aprender(p, "FC Slavia Mozyr +1.5 [Din Minsk v FC Slavia Mozyr]") == "{ent} {hc}"
    assert D.montar_perna(p, "{ent} {hc}") == "FC Slavia Mozyr +1.5 [Din Minsk v FC Slavia Mozyr]"
    assert D.decompor(_p("Futebol", "A - B", "Handicap", "B 0"))["hc"] == "0"
    assert D.decompor(_p("Futebol", "A - B", "Handicap", "B -1.5"))["hc"] == "-1.5"
    assert D.decompor(_p("Futebol", "A - B", "Vencedor", "Time 2"))["ent"] == "Time 2"


def test_total_puro_da_1win_sai_com_v_no_jogo():
    """s416: a forma própria do total puro (D24) só trocava `vs` por `v`; o jogo da 1win vem
    com ` - ` e a descrição saía `Over 3 [FK Atyrau - Fc Yelimai]` (real, 13/10). Mutação H2
    (volta o `_jogo_v` antigo): detectada."""
    p = _p("Futebol", "FK Atyrau - Fc Yelimai", "Total", "Acima De 3")
    assert dicionario.descricao_perna(p) == "Over 3 [FK Atyrau v Fc Yelimai]"
    p = _p("soccer", "A vs. B", "Total", "Under 2.5")
    assert dicionario.descricao_perna(p) == "Under 2.5 [A v B]"
