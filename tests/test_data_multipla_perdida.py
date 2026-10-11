"""Múltipla que perdeu antes da última perna é datada pela perna perdida (s405).

Regra: `MASTER_OUTPUT §4.0.1` (decisão do Feca, 09/10/2026). Código:
`repository.data_da_perna_perdida` e `repository.corrigir_data_tsv`, ligados nos dois
caminhos do `/extrair` (`main._stream_sequential` e `main._stream_parallel`).

Os blocos abaixo seguem o formato que a extensão escreve em cada plataforma, copiados
de bilhetes reais da `sombra_rotulos` (levantamento de 10/10/2026, BACKLOG 1.17).

O que NÃO cobre:
- o UPSERT gravando a data nova sobre linha que estava aberta (é o `ON CONFLICT` de
  `upsert_bilhetes`, que precisa do Postgres do CI);
- linhas já gravadas resolvidas: essas saem pelo `scripts/reparar_data_multipla_s405.py`;
- Bet365, Superbet, Pinnacle, Megapari, 1xBet e PariPesa: o bloco delas não traz a
  perna perdida com início, e a função as deixa intactas (testado só por um exemplo).

Prova por mutação (s405): 11 mutações, 9 detectadas. As 2 que escapam são INÓCUAS com
o vocabulário real da extensão, e ficam registradas em vez de virar asserção inventada:
- tirar o `[1:]` (o cabeçalho passar a contar como perna): nenhum cabeçalho de bloco das
  casas do grupo A traz `Início:`, então ele nunca decide data;
- tirar a fronteira `(?:\\]| ·)` do rótulo: nenhum rótulo real começa com `perdeu`,
  `lost`, `perna perdida` ou `sel_status=4` seguido de outro caractere.
As duas defesas ficam no código para o dia em que uma casa nova mudar isso.
"""
import pathlib
import re
import sys

sys.path.insert(0, "app")
import repository as R  # noqa: E402

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

# Pitaco: código numérico, com o sufixo de liquidação antecipada
PITACO = """
Data (evento): 27/08/2026
Seleções:
- Atlético Grau - Total De Gols: Menos de 1.5 [sel_status=4 · liquidação antecipada]
    Jogo: Atlético Grau x Sport Boys · Início: 26/08/2026 17:27:03 · AO VIVO (2T)
- Vencedor: Justin Schlageter [sel_status=1]
    Jogo: Jakub Filip x Justin Schlageter · Início: 27/08/2026 07:00:00
"""

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


def _texto(**blocos):
    return "\n".join(f"[Código: {c}]\n{b}" for c, b in blocos.items())


def _linha(data, res, cod):
    return "\t".join([data, "Futebol", "", "Casa", "Conta", "Múltipla", "desc",
                      "10,00", "3,5", res, cod])


# ── a função pura ───────────────────────────────────────────────────────────────

def test_cada_plataforma_do_grupo_a_acha_a_perna_perdida():
    assert R.data_da_perna_perdida(ALTENAR) == "2026-09-05"
    assert R.data_da_perna_perdida(BETBY) == "2026-10-06"
    assert R.data_da_perna_perdida(DEX) == "2026-10-09"
    assert R.data_da_perna_perdida(PITACO) == "2026-08-26"


def test_com_duas_perdidas_vale_a_que_comecou_mais_cedo():
    assert R.data_da_perna_perdida(DUAS) == "2026-10-07"


def test_sem_os_dois_sinais_juntos_nao_decide_nada():
    assert R.data_da_perna_perdida(BET365) is None
    assert R.data_da_perna_perdida(MEIA) is None
    assert R.data_da_perna_perdida(SEM_INICIO) is None
    assert R.data_da_perna_perdida(None) is None


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
