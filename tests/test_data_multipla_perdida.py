"""Múltipla que perdeu antes da última perna é datada pela perna perdida (s405).

Regra: `MASTER_OUTPUT §4.0.1` (decisão do Feca, 09/10/2026). Código:
`repository.data_da_perna_perdida` e `repository.corrigir_data_tsv`, ligados nos dois
caminhos do `/extrair` (`main._stream_sequential` e `main._stream_parallel`).

Os blocos abaixo são bilhetes reais da `sombra_rotulos`, no formato que a extensão
escreve em cada plataforma (levantamentos de 10 e 11/10/2026, BACKLOG 1.17), cortados
nas pernas que importam. Os sintéticos dizem que são.

O que NÃO cobre:
- o UPSERT gravando a data nova sobre linha que estava aberta (é o `ON CONFLICT` de
  `upsert_bilhetes`, que precisa do Postgres do CI);
- linhas já gravadas resolvidas: essas saem pelo `scripts/reparar_data_multipla_s405.py`,
  cuja escolha (`candidatos`) é testada aqui, mas cuja escrita no banco não;
- Bet365, Superbet, Pinnacle, Megapari, 1xBet, PariPesa e Novibet: o bloco delas não traz
  a perna perdida com início, e a função as deixa intactas (testado por exemplos).

Prova por mutação: s405 (1ª versão) 11 mutações, 9 detectadas, 2 inócuas. Correção da
auditoria (11/10/2026): 16 mutações novas, 14 detectadas, 2 inócuas. As inócuas,
registradas em vez de virar asserção inventada:
- tirar o `[1:]`/separar o cabeçalho (ele passar a contar como perna): nenhum cabeçalho
  de bloco real traz `Início:`, então ele nunca decide data;
- tirar a fronteira `(?:\\]| ·)` do rótulo: nenhum rótulo real começa com `perdeu`,
  `lost` ou `perna perdida` seguido de outro caractere;
- procurar a marca de SISTEMA no bloco inteiro, e o `Status (API):` que escolhe o
  `sel_status` no bloco inteiro: as duas linhas só existem no cabeçalho (linha de perna
  começa com `- `/`  · ` ou é indentada), então o resultado é o mesmo.
As defesas ficam no código para o dia em que uma casa nova mudar isso.

Prova que o teste NÃO dá: a transação única e o snapshot antes do UPDATE do script. Ali
não há banco; o código foi conferido lendo.
"""
import pathlib
import re
import sys

sys.path.insert(0, "app")
sys.path.insert(0, "scripts")
import repository as R  # noqa: E402
import reparar_data_multipla_s405 as S  # noqa: E402

# Altenar (Estrela Bet): perna perdida no meio, pendente mais tarde
ALTENAR = """
Data (evento mais recente): 06/09/2026 10:30:00
Status: Perdeu → L
Status (API): status=2
Tipo: Múltipla (3 seleções)
Seleções:
- Vencedor: Correia, Laura [ganhou]
    Jogo: Luna Dinoto Fernandez vs. Correia, Laura · Início: 05/09/2026 04:00:00
    Odd da seleção: 1,2858
- Mainz 05 total de escanteios: Menos de 4.5 [pendente]
    Jogo: Hamburger SV vs. Mainz 05 · Início: 06/09/2026 10:30:00
    Odd da seleção: 2,6
- Brighton & Hove Albion total de escanteios: Menos de 5.5 [perdeu]
    Jogo: Brighton & Hove Albion vs. Leeds · Início: 05/09/2026 11:00:00
    Odd da seleção: 2,4546
"""

# BetBy (Duel): `[lost]` e `[useless]`; o cabeçalho tem `Status (API): lost`
BETBY = """
Data (evento mais recente): 07/10/2026 02:00:00
Status: Perdeu → L
Status (API): lost
Seleções:
- Winner: Routliffe E / Sutjiadi A [useless]
    Jogo: Routliffe E / Sutjiadi A vs Danilina A / Krawczyk D · Esporte: Tennis · Início: 07/10/2026 02:00:00
    Odd da seleção: 1,96
- Maxima Roma total (incl. overtime): over 81.5 (total=81.5) [lost]
    Jogo: Turk Telekom vs Maxima Roma · Esporte: Basketball · Início: 06/10/2026 13:30:00
    Odd da seleção: 2,36
"""

# DEX Sport
DEX = """
Data (evento mais recente): 10/10/2026 07:00:00
Seleções:
- Kenneth Faried. Rebounds. With overtime: Under 4.5 [perna perdida]
    Jogo: Baskonia Vitoria Gasteiz vs Besiktas · Esporte: basketball · Início: 09/10/2026 15:30:00
- Draw no bet: Kyzylzhar [perna não decidida]
    Jogo: Irtysh vs Kyzylzhar · Esporte: football · Início: 10/10/2026 07:00:00
"""

# Pitaco 80010000039585007 (Gabriel): `sel_status=4` é PERDEU, sem sufixo nenhum
PITACO = """
Data (evento): 27/08/2026
Data (colocação): 26/08/2026 14:35:28
Stake: 150,00
Status: Perdeu → L
Status (API): status=4
Tipo: Múltipla (3 seleções)
Seleções:
- Atlético Grau - Total De Gols: Menos de 1.5 [sel_status=4]
    Jogo: Atlético Grau x Sport Boys · Início: 26/08/2026 17:27:03 · AO VIVO (2T)
    Odd da perna: 1,72
- Vencedor: Justin Schlageter [sel_status=1]
    Jogo: Jakub Filip x Justin Schlageter · Início: 27/08/2026 07:00:00
    Odd da perna: 1,98
- Total De Gols: Menos de 61.5 [sel_status=3]
    Jogo: Herning-Ikast x Odense · Data do evento (casa): 26/08 → 26/08/2026
    Odd da perna: 1,85
"""

# Pitaco 80010000040958134: a perna perdida só traz `Data do evento (casa):`, sem `Início:`
PITACO_SEM_INICIO = """
Data (evento): 10/09/2026
Status: Perdeu → L
Status (API): status=4
Tipo: Múltipla (2 seleções)
Seleções:
- Vencedor: Aryna Sabalenka  [sel_status=3]
    Jogo: Aryna Sabalenka  x Jessica Pegula · Data do evento (casa): 10/09 → 10/09/2026
- Vencedor: Coco Gauff [sel_status=4]
    Jogo: Coco Gauff x Elena Rybakina · Data do evento (casa): 09/09 → 09/09/2026
"""
# (a data da 2ª perna foi trocada de 10/09 para 09/09, para a regra ter o que mover)

# Stake 8823616: aqui `sel_status=3` é PERDIDA e `sel_status=4` é ANULADA
STAKE = """
Data (colocação): 22/09/2026 19:44:49
Stake: 150,00
Status: Perdeu → L
Status (API): bet_status=3 · ticket_status=2
Tipo: Múltipla (3 seleções)
Seleções:
- Vencedor da partida: Jan Trefny [sel_status=4]
    Jogo: Tomas Dousa - Jan Trefny · Esporte: TABLE_TENNIS (Tênis de Mesa) · Início: 21/09/2026 15:30:00
    Odd da perna: 1,74
- Vencedor da partida: Michal Regner [sel_status=3]
    Jogo: Milan Klement - Michal Regner · Esporte: TABLE_TENNIS (Tênis de Mesa) · Início: 22/09/2026 20:30:00
    Odd da perna: 2,05
- Vencedor da partida: Lubos Forman [sel_status=2]
    Jogo: Ludek Madle - Lubos Forman · Esporte: TABLE_TENNIS (Tênis de Mesa) · Início: 23/09/2026 04:30:00
    Odd da perna: 2,12
"""
# (a perna anulada foi posta em 21/09, antes da perdida: é o caso que a regra antiga errava)

# KTO 13127064360: rótulo cru da API em maiúsculas
KTO = """
Data (colocação): 17/09/2026 14:21:22
Status: Perdeu → L
Status (API): LOST
Tipo: Múltipla (2 seleções)
Seleções:
- Gols de campo de 3 pontos: Georgia Amoore - Menos 1.5 (linha 1,5) [LOST]
    Jogo: Chicago Sky (F) - Washington Mystics (F) · Esporte: BASKETBALL (Basquete) · Início: 17/09/2026 21:00:00
- Assistências pelo jogador: Natisha Hiedeman - Mais 4.5 (linha 4,5) [WON]
    Jogo: Seattle Storm (F) - Las Vegas Aces (F) · Esporte: BASKETBALL (Basquete) · Início: 18/09/2026 23:00:00
"""
# (a 2ª perna foi posta em 18/09 para a regra ter o que mover)

# ── Sistemas: uma perna perdida NÃO encerra o bilhete ──
# Duel 2719643611296838258 (bilhete 378272): sistema 2/3 vivo até 10/10
DUEL_SISTEMA = """
Data (evento mais recente): 10/10/2026 07:00:00
Status: Perdeu → L
Status (API): lost
Tipo: Sistema (3 combinação(ões) · 3 seleções) · combinação da casa: 2/3
Seleções:
- Wonju DB Promy total (incl. overtime): under 87.5 (total=87.5) [lost]
    Jogo: Wonju DB Promy vs LG Sakers · Esporte: Basketball · Início: 08/10/2026 07:00:00
- 1st half - total: under 1 (total=1) [won]
    Jogo: Kyoto Sanga FC vs Machida Zelvia · Esporte: Soccer · Início: 10/10/2026 07:00:00
- 1st half - total: under 1 (total=1) [lost]
    Jogo: FC Orenburg vs FC Dynamo-Makhachkala · Esporte: Soccer · Início: 10/10/2026 07:00:00
"""

# Betfast 302784984 (cabeçalho e pernas reais; a 1ª perna foi posta em 31/08)
BETFAST_SISTEMA = """
Data (evento mais recente): 01/09/2026 15:45:00
Status (API): Status=10 · Result=2
Tipo: Sistema (3 seleções)
Seleções:
- Total de impedimentos: Mais de (linha 2,5) [perdeu]
    Jogo: Lincoln City - Blackburn Rovers FC · Esporte: Futebol · Início: 31/08/2026 15:45:00
- Time de fora Total de faltas: Mais de (linha 10,5) [ganhou]
    Jogo: Sheffield United FC - Bolton Wanderers FC · Esporte: Futebol · Início: 01/09/2026 15:45:00
"""

# Shuffle: o sistema aparece no `Status (API)` e no `Tipo:`. Só o `type=` aqui, para provar
# que ele sozinho basta.
SHUFFLE_SISTEMA = """
Data (evento mais recente): 07/10/2026 06:10:00
Status (API): status=LOST · type=SYSTEM_BET · systemBetType=DOUBLES
Liquidado em: 07/10/2026 09:13:03
Seleções:
- Total sets: Mais de 2.5 [perna perdida]
    Jogo: Fruhvirtova, Linda vs Sasnovich, Aliaksandra · Início: 06/10/2026 01:10:00
- Total sets: Mais de 2.5 [perna ganha]
    Jogo: Fiona Crawley vs Selekhmeteva, Oksana · Início: 07/10/2026 06:10:00
"""

# Shuffle REGULAR: o `status=LOST` do cabeçalho não pode passar por Pitaco
SHUFFLE_REGULAR = """
Status (API): status=LOST · type=REGULAR · systemBetType=null
Seleções:
- Total sets: Mais de 2.5 [sel_status=4]
    Jogo: X vs Y · Início: 06/10/2026 01:10:00
- Total sets: Mais de 2.5 [perna perdida]
    Jogo: Z vs W · Início: 07/10/2026 01:10:00
"""
# (sintético: a Shuffle não escreve `sel_status`; está aqui para provar que só a Pitaco lê o 4)

# Duas pernas perdidas: vale a que começou mais cedo (é ela que encerrou o bilhete)
DUAS = """
Seleções:
- A [perdeu]
    Jogo: X vs Y · Início: 08/10/2026 20:00:00
- B [perdeu]
    Jogo: Z vs W · Início: 07/10/2026 09:00:00
- C [pendente]
    Jogo: Q vs R · Início: 11/10/2026 16:00:00
"""

# Bet365: sem rótulo nem início por perna → intocada
BET365 = """
Data (encerramento): 15/09/2026
Status: Perdeu → L
Seleções:
  • Freseros Irapuato x Soles de Mexicali · Totais do Time · Mais de 41.5 @ 2,2
  • Fauske/Sprint x Strømsgodset 2 · Menos de 5.0 @ 2,075
"""

# Meia derrota NÃO encerra a múltipla
MEIA = """
Seleções:
- A [meia derrota]
    Jogo: X vs Y · Início: 08/10/2026 20:00:00
- B [pendente]
    Jogo: Z vs W · Início: 11/10/2026 16:00:00
"""

# Rótulo de perdida sem `Início:` próprio → intocada
SEM_INICIO = """
Seleções:
- A [perdeu]
    Jogo: X vs Y
- B [pendente]
    Jogo: Z vs W · Início: 11/10/2026 16:00:00
"""


def _crlf(bloco):
    """A sombra guarda o bloco com CRLF, como a extensão manda."""
    return bloco.replace("\n", "\r\n")


def _texto(**blocos):
    return "\n".join(f"[Código: {c}]\n{b}" for c, b in blocos.items())


def _linha(data, res, cod):
    return "\t".join([data, "Futebol", "", "Casa", "Conta", "Múltipla", "desc",
                      "10,00", "3,5", res, cod])


# ── a função pura ───────────────────────────────────────────────────────────────

def test_cada_plataforma_acha_a_perna_perdida():
    assert R.data_da_perna_perdida(ALTENAR) == "2026-09-05"
    assert R.data_da_perna_perdida(BETBY) == "2026-10-06"
    assert R.data_da_perna_perdida(DEX) == "2026-10-09"
    assert R.data_da_perna_perdida(PITACO) == "2026-08-26"
    assert R.data_da_perna_perdida(STAKE) == "2026-09-22"
    assert R.data_da_perna_perdida(KTO) == "2026-09-17"


def test_o_bloco_com_crlf_da_o_mesmo_resultado():
    for bloco in (ALTENAR, BETBY, DEX, PITACO, STAKE, KTO):
        assert R.data_da_perna_perdida(_crlf(bloco)) == R.data_da_perna_perdida(bloco)


def test_sel_status_le_o_numero_de_cada_casa():
    # Stake: 4 é ANULADA. Sem a perna 3, só sobra a anulada, e ela não move nada.
    assert R.data_da_perna_perdida(STAKE.replace("[sel_status=3]", "[sel_status=2]")) is None
    # Pitaco: 3 é GANHOU. Sem a perna 4, nada move.
    assert R.data_da_perna_perdida(PITACO.replace("[sel_status=4]", "[sel_status=1]")) is None
    # Stake com o sufixo que a extensão põe na liquidação antecipada
    antecipada = STAKE.replace("[sel_status=3]", "[sel_status=3 · liquidação antecipada]")
    assert R.data_da_perna_perdida(antecipada) == "2026-09-22"


def test_sel_status_de_casa_desconhecida_nao_move_data():
    assert R.data_da_perna_perdida(SHUFFLE_REGULAR) == "2026-10-07"     # só a `[perna perdida]`
    sem_cabecalho = PITACO.replace("Status (API): status=4\n", "")
    assert R.data_da_perna_perdida(sem_cabecalho) is None


def test_aposta_de_sistema_nunca_e_redatada():
    assert R.data_da_perna_perdida(DUEL_SISTEMA) is None
    assert R.data_da_perna_perdida(BETFAST_SISTEMA) is None
    assert R.data_da_perna_perdida(SHUFFLE_SISTEMA) is None
    assert R.data_da_perna_perdida(_crlf(DUEL_SISTEMA)) is None
    assert R.data_da_perna_perdida(
        "Status (API): BetStatus=2 · BetTypeName=Sistema · BetSystemType=3\nSeleções:\n"
        "- A [perdeu]\n    Jogo: X · Início: 01/10/2026 10:00:00\n") is None
    # o mesmo bloco SEM a marca de sistema seria redatado: é a marca que decide
    assert R.data_da_perna_perdida(DUEL_SISTEMA.replace("Tipo: Sistema", "Tipo: Múltipla")) \
        == "2026-10-08"


def test_com_duas_perdidas_vale_a_que_comecou_mais_cedo():
    assert R.data_da_perna_perdida(DUAS) == "2026-10-07"


def test_sem_os_dois_sinais_juntos_nao_decide_nada():
    assert R.data_da_perna_perdida(BET365) is None
    assert R.data_da_perna_perdida(MEIA) is None
    assert R.data_da_perna_perdida(SEM_INICIO) is None
    assert R.data_da_perna_perdida(None) is None


def test_data_do_evento_da_casa_nao_e_inicio():
    # a Pitaco imprime `Data do evento (casa):` quando não tem o instante; não serve
    assert R.data_da_perna_perdida(PITACO_SEM_INICIO) is None


def test_o_status_do_cabecalho_nao_conta_como_perna():
    # `Status (API): lost` no cabeçalho, nenhuma perna perdida
    so_cabecalho = BETBY.replace("[lost]", "[won]")
    assert R.data_da_perna_perdida(so_cabecalho) is None


# ── o TSV ──────────────────────────────────────────────────────────────────────

def test_multipla_perdida_volta_para_o_dia_da_perna_perdida():
    texto = _texto(EB1=ALTENAR, DU1=BETBY)
    tsv = "\n".join([_linha("06/09/2026", "L", "EB1"), _linha("07/10/2026", "L", "DU1")])
    novo, info = R.corrigir_data_tsv(tsv, texto)
    datas = [l.split("\t")[0] for l in novo.split("\n")]
    assert datas == ["05/09/2026", "06/10/2026"]
    assert info["datas"] == 2
    assert info["exemplos"][0] == {"codigo": "EB1", "ia": "06/09/2026",
                                   "perna_perdida": "05/09/2026"}


def test_sistema_no_tsv_passa_intacto():
    texto = _texto(DU2=DUEL_SISTEMA)
    tsv = _linha("10/10/2026", "L", "DU2")
    novo, info = R.corrigir_data_tsv(tsv, texto)
    assert novo == tsv and info["datas"] == 0


def test_so_mexe_em_L():
    texto = _texto(EB1=ALTENAR)
    for res in ("W", "V", "HL", ""):
        tsv = _linha("06/09/2026", res, "EB1")
        assert R.corrigir_data_tsv(tsv, texto)[0] == tsv


def test_a_data_nunca_anda_para_frente():
    texto = _texto(EB1=ALTENAR)
    for data in ("05/09/2026", "04/09/2026"):        # igual ou anterior à perna perdida
        tsv = _linha(data, "L", "EB1")
        novo, info = R.corrigir_data_tsv(tsv, texto)
        assert novo == tsv and info["datas"] == 0


def test_data_iso_na_linha_tambem_e_lida():
    texto = _texto(EB1=ALTENAR)
    novo, _ = R.corrigir_data_tsv(_linha("2026-09-06", "L", "EB1"), texto)
    assert novo.split("\t")[0] == "05/09/2026"


def test_linha_sem_codigo_ou_de_outro_codigo_passa_intacta():
    texto = _texto(EB1=ALTENAR)
    for cod in ("", "OUTRO"):
        tsv = _linha("06/09/2026", "L", cod)
        assert R.corrigir_data_tsv(tsv, texto)[0] == tsv


def test_casa_sem_perna_perdida_no_bloco_passa_intacta():
    texto = _texto(B3=BET365)
    tsv = _linha("15/09/2026", "L", "B3")
    assert R.corrigir_data_tsv(tsv, texto)[0] == tsv


def test_nota_e_texto_livre_passam_intactos():
    texto = _texto(EB1=ALTENAR)
    tsv = "Nota: 1 bilhete\n" + _linha("06/09/2026", "L", "EB1")
    novo, _ = R.corrigir_data_tsv(tsv, texto)
    assert novo.split("\n")[0] == "Nota: 1 bilhete"


# ── o script de reparo escolhe pela mesma função ───────────────────────────────

def _registro(id_, bruto, data="10/10/2026", resultado="L"):
    return {"id": id_, "dono": "X", "casa": "C", "codigo": f"c{id_}", "data": data,
            "resultado": resultado, "stake": 10, "odd": 3, "stake_freebet": None,
            "bruto": bruto}


def test_script_pula_sistema_correcao_humana_e_quem_nao_e_L():
    linhas = [_registro(1, _crlf(DUEL_SISTEMA)), _registro(2, _crlf(BETBY), "07/10/2026"),
              _registro(3, _crlf(BETBY), "07/10/2026"), _registro(4, BETBY, "07/10/2026", "W")]
    mudar, pulados = S.candidatos(linhas, travados={3})
    assert [m["id"] for m in mudar] == [2]
    assert mudar[0]["data_depois"] == "06/10/2026"
    assert [p["id"] for p in pulados] == [3]


# ── ligação no /extrair ────────────────────────────────────────────────────────

def test_os_dois_caminhos_do_extrair_chamam_a_correcao_depois_da_stake():
    """Recorta o corpo real de cada stream: a correção tem de estar lá, depois da stake
    (o resultado final pode ter mudado nela) e antes do sistema (que fecha o TSV)."""
    src = pathlib.Path("app/main.py").read_text(encoding="utf-8")
    for nome, var in (("_stream_sequential", "accumulated"), ("_stream_parallel", "resultado")):
        ini = src.index(f"async def {nome}(")
        fim = src.index("\nasync def ", ini + 1)
        corpo = src[ini:fim]
        p_stake = corpo.index(f"corrigir_stake_tsv({var}, texto)")
        m = re.search(rf"{var}, data_fix = corrigir_data_tsv\({var}, texto\)", corpo)
        assert m, nome
        p_sis = corpo.index(f"anexar_sistema_tsv({var}, texto)")
        assert p_stake < m.start() < p_sis, nome
