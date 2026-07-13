"""Betfair — join determinístico bilhete↔extrato feito no CÓDIGO (não pela IA).

O bilhete tem o ID `O/…` mas não a data; o extrato CSV tem a data de liquidação por ID.
O código monta o mapa ID→data e preenche depois — some a chamada única gigante que
causava o `network error` em conta grande (Duka ~1044).

conftest.py stuba asyncpg/database; aqui completamos com init_db + ANTHROPIC_API_KEY.
"""
import os
import sys

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-nao-usada")
import database  # noqa: E402  (stub do conftest)
if not hasattr(database, "init_db"):
    async def _init_db():  # pragma: no cover
        raise RuntimeError("DB indisponível nos testes")
    database.init_db = _init_db
import main  # noqa: E402


CSV = (
    "Data,Descrição,Entrada de Dinheiro (R$),Entrada de bônus (R$),Saída de Dinheiro (R$),Saída de bônus (R$),Saldos em Dinheiro (R$)\n"
    '10-jul-26 17:26:50,Sportsbook: Bet Settled (Bet Ref: O/25146258/0001745) Ref: 17837152092087,202.36,--,--,--,"5,897.05"\n'
    '10-jul-26 13:19:33,Sportsbook: Bet Placed (Transaction ID: S/25146258/02706039810) Ref: 17837003732086,--,--,-400.00,--,"5,694.69"\n'
    '09-jul-26 12:24:26,Sportsbook: Voided Bet Refund (Bet Ref: O/25146258/0001600) Ref: 17836106662060,303.00,--,--,--,"7,202.56"\n'
    '08-jul-26 07:15:43,Sportsbook: Bet Settled (Bet Ref: O/25146258/0001716) Ref: 17835057432048,900.00,--,--,--,"7,534.58"\n'
)


# ── _betfair_data ─────────────────────────────────────────────────────────────

def test_betfair_data_converte_mes_pt():
    assert main._betfair_data("10-jul-26 17:26:50") == "10/07/2026"
    assert main._betfair_data("07-jun-26 20:47:03") == "07/06/2026"
    assert main._betfair_data("1-jan-26 00:00:00") == "01/01/2026"


def test_betfair_data_invalida_vazia():
    assert main._betfair_data("lixo") == ""
    assert main._betfair_data("") == ""


# ── _parse_betfair_csv ────────────────────────────────────────────────────────

def test_parse_csv_pega_settled_e_voided_ignora_placed():
    m = main._parse_betfair_csv(CSV)
    assert m["O/25146258/0001745"] == "10/07/2026"   # Bet Settled
    assert m["O/25146258/0001600"] == "09/07/2026"   # Voided Bet Refund
    assert m["O/25146258/0001716"] == "08/07/2026"
    # colocação (S/…) NÃO entra no mapa
    assert not any(k.startswith("S/") for k in m)
    assert len(m) == 3


# ── _split_betfair_bilhetes ───────────────────────────────────────────────────

def test_split_por_id_da_aposta():
    txt = (
        "Simples\nP\nA x B - Resultado\nB\n1.66\nValor Apostado:\nR$303.00\n"
        "Ganhos:\nR$0.00\nID da aposta: O/25146258/0001747\n\n"
        "Você ganhou R$505.00\nSimples\nV\nC x D - Resultado\nC\n1.66\n"
        "Valor Apostado:\nR$303.00\nGanhos:\nR$505.00\nID da aposta: O/25146258/0001746"
    )
    blocos = main._split_betfair_bilhetes(txt)
    assert len(blocos) == 2
    assert "O/25146258/0001747" in blocos[0]
    assert "O/25146258/0001746" in blocos[1]


# ── _apply_betfair_dates (win do mapa + perda por interpolação) ────────────────

def _tsv(rows):
    linhas = [main._TSV_HEADER]
    for cod, res in rows:
        # Data vazia (col0), Código = ID na col 11
        linhas.append(f"\tFutebol\t\tBetfair\t\tML\tsel\t100,00\t1,90\t{res}\t{cod}")
    return "```tsv\n" + "\n".join(linhas) + "\n```\n\n## Notas Críticas\nNenhuma"


def _datas(tsv):
    import re
    corpo = re.search(r"```tsv\n(.*?)\n```", tsv, re.DOTALL).group(1).split("\n")[1:]
    return [ln.split("\t")[0] for ln in corpo if ln.strip()]


def test_apply_dates_win_do_mapa_perda_interpola():
    m = main._parse_betfair_csv(CSV)
    saida = _tsv([
        ("O/25146258/0001747", "L"),   # perda: sem linha no extrato → interpola
        ("O/25146258/0001745", "W"),   # 10/07 do mapa
        ("O/25146258/0001744", "L"),   # perda → interpola pelo vizinho (0001745=10/07)
        ("O/25146258/0001716", "W"),   # 08/07 do mapa
    ])
    datas = _datas(main._apply_betfair_dates(saida, m))
    assert datas[1] == "10/07/2026"   # win direto
    assert datas[3] == "08/07/2026"   # win direto
    assert datas[0] == "10/07/2026"   # perda 0001747 → vizinho 0001745
    assert datas[2] == "10/07/2026"   # perda 0001744 → vizinho 0001745
    assert "" not in datas            # nenhuma linha ficou sem data


def test_apply_dates_mapa_vazio_no_op():
    saida = _tsv([("O/25146258/0001745", "W")])
    assert main._apply_betfair_dates(saida, {}) == saida


def test_apply_dates_sobrescreve_data_errada_do_modelo():
    # Se o modelo desobedecer e preencher a Data (aqui uma perda com data errada), o
    # código SEMPRE recalcula: win pelo extrato, perda por interpolação. Nunca confia.
    m = main._parse_betfair_csv(CSV)
    saida = (
        "```tsv\n" + main._TSV_HEADER + "\n"
        "01/01/2099\tFutebol\t\tBetfair\t\tML\tsel\t100,00\t1,90\tW\tO/25146258/0001745\n"  # win com data errada
        "31/12/2099\tFutebol\t\tBetfair\t\tML\tsel\t100,00\t1,90\tL\tO/25146258/0001744\n"  # perda com data errada
        "\n```\n\n## Notas Críticas\nNenhuma"
    )
    datas = _datas(main._apply_betfair_dates(saida, m))
    assert datas[0] == "10/07/2026"   # win: extrato manda, ignora 2099
    assert datas[1] == "10/07/2026"   # perda: interpola 0001745, ignora 2099


# ── Roteamento do split: CAPTURA (bf_inject, [Código: O/…]) vs LEGADO (ID da aposta:) ──
# A captura (bf_inject) emite o marcador [Código: O/…] das casas passivas → fatia pelo
# _SUPERBET_SPLIT_RE. O legado texto+extrato (sem [Código:]) continua fatiando por
# "ID da aposta: O/…". Ambos precisam render 1 chunk por bilhete (2 bilhetes → 2 chunks).
_INSTR = {"type": "text", "text": "INSTRUCAO"}


def test_build_chunks_betfair_captura_split_por_codigo():
    texto = (
        "[Código: O/25146258/0001761]\nData: 12/07/2026\nStake: 100,00\nStatus: LOST → L\n\n"
        "[Código: O/25146258/0001760]\nData: 12/07/2026\nStake: 100,00\nStatus: VOID → V"
    )
    chunks = main._build_chunks([{"type": "text", "text": texto}], _INSTR, "BETFAIR")
    assert len(chunks) == 2   # 2 bilhetes distintos → 2 chunks (roteou pelo split de [Código:])
    joined = "\n".join(b["text"] for ch in chunks for b in ch if b is not _INSTR)
    assert "0001761" in joined and "0001760" in joined


def test_build_chunks_betfair_legado_split_por_id_da_aposta():
    texto = (
        "Simples\nP\nA x B\n1.66\nID da aposta: O/25146258/0001747\n\n"
        "Simples\nV\nC x D\n1.66\nID da aposta: O/25146258/0001746"
    )
    chunks = main._build_chunks([{"type": "text", "text": texto}], _INSTR, "BETFAIR")
    assert len(chunks) == 2   # sem [Código:] → fatiou pelo _split_betfair_bilhetes (legado)
