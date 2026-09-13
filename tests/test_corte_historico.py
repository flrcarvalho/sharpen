"""Gate do corte de histórico por casa (`main._corte_historico_text`, s344).

Nasceu da Betbra: a 1ª captura da casa gravou 411 bilhetes de uma vez, 298 deles de
2025, e a Betbra é a única casa daquele dono com bilhete daquele ano. Apagar as linhas
do banco não bastava — o `bda_inject` varre 3 anos por desenho (`DIAS_HISTORICO = 1095`)
e a captura seguinte regravaria todas, sem erro nenhum.

**Os blocos abaixo são REAIS**, colhidos da `sombra_rotulos` de produção (dono Feca,
casa Betbra) com o marcador `[Código: …]` remontado na frente, que é como o texto chega
ao `/extrair` (`formatTicketBDA` emite o marcador como 1ª linha). O único bloco derivado
é o `BLOCO_VIRADA`, e ele está marcado: é um real com as duas datas trocadas para cair
em lados OPOSTOS do corte, porque sem isso a escolha entre evento e colocação não é
exercida por nenhum dado que exista hoje na base.

O QUE ESTE ARQUIVO **NÃO** COBRE:

  • **Não toca o banco nem a rota de verdade.** `test_a_rota_chama_o_corte_antes_do_dedup`
    lê o FONTE da rota, não a executa: ele prova que a chamada está lá e na ordem certa,
    não que ela funciona ponta a ponta. Isso se confere ao vivo.
  • **Não cobre print nem imagem.** O corte roda no ramo de `texto`; lote de imagem passa
    inteiro por desenho (não há bloco com data para ler antes da IA).
  • **Não mede economia.** Quanto se deixa de pagar é medição em produção.
"""
import re
import sys

sys.path.insert(0, "app")

import main  # noqa: E402

# ── Blocos reais (sombra_rotulos de produção, dono Feca / casa Betbra) ─────────

BLOCO_2025_A = """[Código: 4112921]
Data (evento): 01/06/2025 19:30:00
Data (colocação): 01/06/2025 11:35:21
Stake: 70,00
Status: Perdeu → L
Status (API): lose
Odd: 4,5
Lado: A favor (Back)
L/P: -70,00
Retorno: 0,00
Evento: Cruzeiro vs Palmeiras
Mercado: Palmeiras vence sem levar gols
Seleção: Sim (resposta ao mercado — CONFIRMA o mercado acima)
Esporte: soccer
Obs. da casa: mercado do Criador de Eventos (custom)."""

BLOCO_2025_B = """[Código: 4113146]
Data (evento): 01/06/2025 19:30:00
Data (colocação): 01/06/2025 11:38:00
Stake: 100,00
Status: Perdeu → L
Status (API): lose
Odd: 5
Lado: A favor (Back)
L/P: -100,00
Retorno: 0,00
Evento: Cruzeiro vs Palmeiras
Mercado: Ambos marcam gols e Menos de 5.5 Cartões
Seleção: Sim (resposta ao mercado — CONFIRMA o mercado acima)
Esporte: soccer
Obs. da casa: mercado do Criador de Eventos (custom)."""

BLOCO_2026_A = """[Código: 8231368]
Data (evento): 01/02/2026 12:30:00
Data (colocação): 01/02/2026 09:16:23
Stake: 38,00
Status: Perdeu → L
Status (API): lose
Odd: 5,7
Lado: A favor (Back)
L/P: -38,00
Retorno: 0,00
Evento: Gil Vicente vs Famalicão
Mercado: Famalicão vence e Mais de 2.5 gols
Seleção: Sim (resposta ao mercado — CONFIRMA o mercado acima)
Esporte: soccer
Obs. da casa: mercado do Criador de Eventos (custom)."""

BLOCO_2026_B = """[Código: 8712590]
Data (evento): 02/03/2026 19:15:00
Data (colocação): 02/03/2026 12:45:54
Stake: 17,00
Status: Perdeu → L
Status (API): lose
Odd: 10
Lado: A favor (Back)
L/P: -17,00
Retorno: 0,00
Evento: Deportivo Riestra vs Platense
Mercado: Platense e River Plate vencem
Seleção: Sim (resposta ao mercado — CONFIRMA o mercado acima)
Esporte: soccer
Obs. da casa: mercado do Criador de Eventos (custom)."""

# DERIVADO de um bloco real: as duas datas caem em lados OPOSTOS do corte. Aposta
# colocada em 28/12/2025 para um jogo de 02/01/2026 — o bilhete é do dia do JOGO
# (`CASA_BOLSADEAPOSTA §4`), então ele FICA. Nenhum bloco da base exercita isso hoje,
# e sem ele a escolha entre as duas datas passaria despercebida.
BLOCO_VIRADA = """[Código: 8000001]
Data (evento): 02/01/2026 19:15:00
Data (colocação): 28/12/2025 12:45:54
Stake: 17,00
Status: Perdeu → L
Status (API): lose
Odd: 10
Lado: A favor (Back)
L/P: -17,00
Retorno: 0,00
Evento: Deportivo Riestra vs Platense
Mercado: Platense e River Plate vencem
Seleção: Sim (resposta ao mercado — CONFIRMA o mercado acima)
Esporte: soccer"""

# Real, com a linha de evento removida: é o que sobra quando a casa não manda a data do
# jogo. FAIL-OPEN manda mantê-lo, e a colocação decide quando existe.
BLOCO_SEM_EVENTO_2025 = "\n".join(
    l for l in BLOCO_2025_A.splitlines() if not l.startswith("Data (evento):"))

BLOCO_SEM_DATA = """[Código: 9999999]
Stake: 25,00
Status: Perdeu → L
Status (API): lose
Odd: 3,2
Evento: Time A vs Time B"""


def _lote(*blocos):
    return "\n\n".join(blocos)


def _codigos(texto):
    return re.findall(r'^\[Código:\s*([^\]]+)\]', texto, re.MULTILINE)


# ── O caso que originou o gate ────────────────────────────────────────────────

def test_corta_o_que_e_anterior_e_mantem_o_resto():
    texto, n = main._corte_historico_text(
        _lote(BLOCO_2025_A, BLOCO_2026_A, BLOCO_2025_B, BLOCO_2026_B), "Feca", "Betbra")
    assert n == 2
    assert _codigos(texto) == ["8231368", "8712590"]
    assert "4112921" not in texto and "4113146" not in texto


def test_lote_inteiro_anterior_ao_corte_sai_vazio():
    texto, n = main._corte_historico_text(_lote(BLOCO_2025_A, BLOCO_2025_B), "Feca", "Betbra")
    assert n == 2
    assert texto == ""


def test_lote_inteiro_posterior_passa_intacto():
    texto, n = main._corte_historico_text(_lote(BLOCO_2026_A, BLOCO_2026_B), "Feca", "Betbra")
    assert n == 0
    assert _codigos(texto) == ["8231368", "8712590"]


# ── A régua é por PAR EXATO: casa nova não entra sem decisão escrita ──────────

def test_outro_dono_na_mesma_casa_nao_tem_corte():
    lote = _lote(BLOCO_2025_A, BLOCO_2026_A)
    texto, n = main._corte_historico_text(lote, "Jonathan", "Betbra")
    assert n == 0 and texto == lote


def test_outra_casa_do_mesmo_dono_nao_tem_corte():
    """O Pitaco emite o MESMO marcador e a MESMA linha `Data (evento)` (`formatTicketPTC`).
    Se o corte pegasse por formato em vez de por par declarado, ele perderia histórico sem
    ninguém pedir. (Até a s346 este teste usava a Bolsa de Aposta; ela passou a ter corte
    declarado, e casa com decisão escrita não serve mais de controle.)"""
    lote = _lote(BLOCO_2025_A, BLOCO_2026_A)
    texto, n = main._corte_historico_text(lote, "Feca", "Pitaco")
    assert n == 0 and texto == lote


def test_dono_e_casa_batem_sem_olhar_caixa():
    _, n = main._corte_historico_text(_lote(BLOCO_2025_A), "FECA", "BETBRA")
    assert n == 1


# ── Fronteira, fail-open e qual data manda ───────────────────────────────────

def test_o_proprio_dia_do_corte_fica():
    """O corte é 01/01/2026 e a régua é `<`: o dia do corte está DENTRO."""
    bloco = BLOCO_2026_A.replace("Data (evento): 01/02/2026", "Data (evento): 01/01/2026")
    texto, n = main._corte_historico_text(bloco, "Feca", "Betbra")
    assert n == 0 and "8231368" in texto


def test_vespera_do_corte_sai():
    bloco = BLOCO_2026_A.replace("Data (evento): 01/02/2026", "Data (evento): 31/12/2025")
    texto, n = main._corte_historico_text(bloco, "Feca", "Betbra")
    assert n == 1 and texto == ""


def test_bloco_sem_data_legivel_e_mantido():
    """FAIL-OPEN. Esconder bilhete é o modo de falha caro; um a mais para a IA é o que
    a barreira de recaptura já devolve."""
    texto, n = main._corte_historico_text(_lote(BLOCO_SEM_DATA, BLOCO_2025_A), "Feca", "Betbra")
    assert n == 1
    assert _codigos(texto) == ["9999999"]


def test_data_invalida_nao_derruba_nem_corta():
    bloco = BLOCO_2025_A.replace("Data (evento): 01/06/2025", "Data (evento): 31/02/2025")
    texto, n = main._corte_historico_text(bloco, "Feca", "Betbra")
    assert n == 0 and "4112921" in texto


def test_quem_manda_e_o_EVENTO_nao_a_colocacao():
    """Colocada em 28/12/2025, jogo em 02/01/2026: o bilhete é do dia do jogo e FICA.
    Ler a colocação cortaria uma aposta que o dono quer ver."""
    texto, n = main._corte_historico_text(BLOCO_VIRADA, "Feca", "Betbra")
    assert n == 0 and "8000001" in texto


def test_sem_evento_a_colocacao_decide():
    texto, n = main._corte_historico_text(BLOCO_SEM_EVENTO_2025, "Feca", "Betbra")
    assert n == 1 and texto == ""


# ── Entradas degeneradas ─────────────────────────────────────────────────────

def test_texto_vazio_nao_quebra():
    assert main._corte_historico_text("", "Feca", "Betbra") == ("", 0)
    assert main._corte_historico_text(None, "Feca", "Betbra") == (None, 0)


def test_texto_sem_marcador_nenhum_e_mantido():
    """Colagem manual sem `[Código:]` vira um bloco só, e sem data legível ela fica."""
    livre = "Aposta colada à mão, sem marcador e sem data."
    texto, n = main._corte_historico_text(livre, "Feca", "Betbra")
    assert n == 0 and texto == livre


# ── A costura: o corte tem de rodar ANTES da IA e antes do pré-dedup ─────────

def test_a_rota_chama_o_corte_antes_do_dedup():
    """Regra sem gate não é cumprida neste repo. Este teste NÃO executa a rota: ele lê o
    fonte dela e prova que a chamada existe e vem antes do pré-dedup — que é o que faz o
    bloco cortado não pagar IA. Removida a chamada, o corte fica verde e inútil."""
    import inspect
    fonte = inspect.getsource(main.extrair)
    assert "_corte_historico_text(" in fonte, "a rota /extrair não chama mais o corte"
    assert fonte.index("_corte_historico_text(") < fonte.index("_dedup_superbet_text("), \
        "o corte precisa vir ANTES do pré-dedup, senão o bloco cortado ainda paga IA"


def test_o_corte_declarado_da_betbra_e_o_que_foi_decidido():
    """A régua vive num mapa, e mapa se edita sem querer. 01/01/2026, decisão do dono."""
    from datetime import date
    assert main._CORTE_HISTORICO[("feca", "betbra")] == date(2026, 1, 1)


# ── Bolsa de Aposta (s346): mesma plataforma, mesma decisão, outra chave ───────
#
# Blocos REAIS da `sombra_rotulos` (dono Feca, casa Bolsa de Aposta), com o marcador
# `[Código: …]` remontado na frente — é como o texto chega ao `/extrair`, e a sombra
# guarda só o corpo. O de virada aqui NÃO é derivado: existe de verdade na base (evento
# 01/01/2026, colocação 30/12/2025), então a escolha entre evento e colocação é exercida
# por dado real nesta casa.

BDA_2025 = """[Código: 47657550]
Data (evento): 31/12/2025 21:00:00
Data (colocação): 31/12/2025 00:40:29
Stake: 100,00
Status: Ganho → W
Status (API): win
Odd: 1,15 (= Retorno ÷ Stake)
Lado: A favor (Back)
L/P: +15,00
Retorno: 115,00
Evento: New Orleans Pelicans em Chicago Bulls
Mercado: Chicago Bulls vencem por mais de 15,5 pontos ou Anula
Seleção: Chicago Bulls vencem por mais de 15,5 pontos ou Anula
Esporte: basketball
Obs. da casa: mercado do Criador de Eventos (custom).
Marcação da casa: aceita ao vivo (keep in play)"""

BDA_2026 = """[Código: 100386622]
Data (evento): 25/06/2026 23:00:00
Data (colocação): 25/06/2026 10:50:43
Stake: 100,00
Status: Anulada → V
Status (API): push
Odd: 3
Lado: A favor (Back)
L/P: a casa não informou (anulada — stake devolvida)
Retorno: 100,00
Evento: Turquia vs EUA
Mercado: Folarin Balogun para Marcar a Qualquer momento
Seleção: Sim (resposta ao mercado — CONFIRMA o mercado acima)
Esporte: soccer
Obs. da casa: mercado do Criador de Eventos (custom).
Marcação da casa: aceita ao vivo (keep in play)"""

# Virada REAL: o evento cai depois do corte, a colocação antes. Pela régua do evento a
# linha FICA; pela da colocação sairia.
BDA_VIRADA = """[Código: 47589762]
Data (evento): 01/01/2026 17:00:00
Data (colocação): 30/12/2025 17:09:56
Stake: 50,00
Status: Perdeu → L
Status (API): lose
Odd: 2,38
Lado: A favor (Back)
L/P: -50,00
Retorno: 0,00
Evento: Sunderland vs Manchester City
Mercado: Manchester City para vencer por 2 ou mais gols de diferença.
Seleção: Sim (resposta ao mercado — CONFIRMA o mercado acima)
Esporte: soccer
Obs. da casa: mercado do Criador de Eventos (custom).
Marcação da casa: aceita ao vivo (keep in play)"""


def test_a_chave_do_mapa_e_a_QUE_A_ROTA_PASSA():
    """O erro que a data certa não pega: chave canônica (`BOLSADEAPOSTA`) no lugar do nome
    que a rota entrega. O `/extrair` chama `_corte_historico_text(..., _casa_display(key))`,
    então quem tem de estar no mapa é o display em minúsculas. Chave torta = corte mudo."""
    assert (main._casa_display("BOLSADEAPOSTA").strip().lower()
            in {c for _, c in main._CORTE_HISTORICO})


def test_bolsa_de_aposta_corta_2025_e_mantem_2026():
    texto = "\n\n".join([BDA_2025, BDA_2026])
    saida, n = main._corte_historico_text(texto, "Feca", main._casa_display("BOLSADEAPOSTA"))
    assert n == 1
    assert "47657550" not in saida
    assert "100386622" in saida


def test_bolsa_de_aposta_mantem_a_virada_real_pela_data_do_evento():
    """Colocada em 30/12/2025 para um jogo de 01/01/2026: é bilhete de 2026 e fica."""
    saida, n = main._corte_historico_text(BDA_VIRADA, "Feca",
                                          main._casa_display("BOLSADEAPOSTA"))
    assert n == 0 and "47589762" in saida


def test_outro_dono_na_bolsa_de_aposta_nao_e_tocado():
    """A régua é por par exato: Jonathan e sohprops também têm conta nesta casa."""
    texto = "\n\n".join([BDA_2025, BDA_2026])
    saida, n = main._corte_historico_text(texto, "Jonathan",
                                          main._casa_display("BOLSADEAPOSTA"))
    assert n == 0 and saida == texto


def test_o_corte_declarado_da_bolsa_de_aposta_e_o_que_foi_decidido():
    """477 das 905 linhas do Feca aqui eram de 2025. 01/01/2026, decisão do dono, 13/09/2026."""
    from datetime import date
    assert main._CORTE_HISTORICO[("feca", "bolsa de aposta")] == date(2026, 1, 1)
