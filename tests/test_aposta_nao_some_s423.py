"""Nenhuma aposta é descartada em silêncio (s423, Feca, 19/10/2026): o lado do LEITOR.

O furo: o leitor do `/extrair` (s417, parecer 020) exige a odd em captura com gabarito de
códigos. Só que a extensão ESCREVE no bloco "deixe a odd VAZIA" quando a casa não manda a
cotação (sistema da família 1xBet sem `Coef`, `content.js`). A IA obedecia, o leitor recusava,
a repescagem devolvia a mesma linha vazia, e a passada final do leitor a tirava do lote: a
aposta sumia sem erro. Medido: zero casos desde 14/10 (`sombra_tsv`), mas nada o impedia.

A regra (Feca): odd vazia passa quando o bloco daquele código manda deixá-la vazia; na passada
FINAL (depois da repescagem) odd vazia nunca derruba a linha; W/HW sem odd é gravada (fica
`aberta`, `estado_extracao`) com aviso ao Feca; e linha que a passada final ainda recusa
aparece na tela como faltante, nunca some.

O bloco abaixo é o real da SapphireBet de 01/10 (`sombra_rotulos` 50131, código
88092600919, do Feca), sem nada de pessoa.

Mutações (s423), cada uma derrubou ao menos um teste daqui:
  M1. sem a exceção do `odd_vazia` no `conferir_linha`       → test_o_bloco_que_manda…
  M2. `codigos_odd_vazia` devolve vazio                      → test_o_bloco_que_manda…
  M3. a passada final volta a exigir a odd                   → test_a_passada_final…
  M4. sem o aviso de W/HW sem odd                            → test_a_passada_final…
  M5. a cobertura não é refeita depois da passada final      → test_a_recusa_final…

O que NÃO está coberto: a entrega do Telegram (o `disparar_aviso` é dublado) e a repescagem
real (gate próprio, `_garantir_cobertura`).
"""
import asyncio
from pathlib import Path

import repository as R
import taxonomia

RAIZ = Path(__file__).resolve().parent.parent
MASTER = frozenset(taxonomia.categorias_canonicas())

SAPPHIRE = """[Código: 88092600919]
Data (evento): 01/10/2026 21:15:00
Colocada: 30/09/2026 15:39:25
Stake: 12,00
Moeda: USD
Tipo: Sistema (3 seleções · Sistema · BetSystemType 20203)
Odd: (a casa não informa a cotação deste sistema — deixe a odd VAZIA; não use o produto das pernas nem zero)
Status: Perdeu → L
Seleções:
  1. Cleveland Browns - Pittsburgh Steelers 2º quarto // Total Abaixo de (10.5) @ 2,09
  2. Hapoel Tel Aviv - Real Madrid Basket (Incluindo prorrogação) // Handicap 2 (-2) @ 2,05
  3. Argentina - Bolivia 1º tempo // Handicap 1 (-1) @ 1,79

[Código: 88092600920]
Data (evento): 01/10/2026 21:15:00
Stake: 10,00
Odd: 2,10
Status: Ganhou → W
"""

LINHA_SIS = ("01/10/2026\tMúltiplos\t\tSapphireBet\tFeca [Eu]\tMúltipla\t"
             "Under 10.5 Pontos 2º Quarto [Cleveland Browns v Pittsburgh Steelers]\t12,00\t\tL\t"
             "88092600919")
LINHA_W = ("01/10/2026\tFutebol\t\tSapphireBet\tFeca [Eu]\tML\tTime A [Time A v Time B]\t"
           "10,00\t\tW\t88092600920")
KW = {"casa": "SapphireBet", "categorias": MASTER, "exige_codigo": True, "exige_odd": True}


def test_o_bloco_que_manda_deixar_a_odd_vazia_passa_os_outros_nao():
    vazia = R.codigos_odd_vazia(SAPPHIRE)
    assert vazia == {"88092600919"}
    kw = dict(KW, odd_vazia=vazia)
    for res in ("L", "V", "HL", ""):
        p = LINHA_SIS.split("\t")
        p[9] = res
        assert R.conferir_linha(p, **kw) == [], res
    # o bilhete vizinho, cujo bloco TEM odd, continua recusado sem ela (a repescagem a pede)
    assert "odd" in R.conferir_linha(LINHA_W.split("\t"), **kw)
    # e sem o gabarito do bloco, como antes da s423
    assert "odd" in R.conferir_linha(LINHA_SIS.split("\t"), **KW)


def test_odd_vazia_ganha_aponta_so_w_e_hw():
    hw = LINHA_W.replace("\tW\t", "\tHW\t")
    tsv = "\n".join(["Data\tEsporte", LINHA_SIS, LINHA_W, hw])
    assert R.odd_vazia_ganha(tsv) == ["88092600920", "88092600920"]
    com_odd = LINHA_W.replace("10,00\t\tW", "10,00\t2,10\tW")
    assert R.odd_vazia_ganha(com_odd) == []


def _leitor(monkeypatch, tsv, final):
    import main
    avisos = []

    async def cats(dono):
        return MASTER
    monkeypatch.setattr(main, "categorias_do_dono", cats)
    monkeypatch.setattr(main, "disparar_aviso", avisos.append)
    out, st = asyncio.run(main._leitor(tsv, SAPPHIRE, "TDono", "SapphireBet", "teste",
                                       final=final))
    return out, st, avisos


def test_a_passada_final_grava_a_ganha_sem_odd_e_avisa(monkeypatch):
    tsv = LINHA_SIS + "\n" + LINHA_W
    # 1ª passada: o sistema passa (o bloco manda); a ganha sem odd é recusada para a
    # repescagem pedir a odd, sem aviso ainda
    out, st, avisos = _leitor(monkeypatch, tsv, final=False)
    assert R.codigos_do_tsv(out) == {"88092600919"} and st["recusadas"] == 1 and avisos == []
    # passada final: nada some por odd; a ganha sem odd fica, e o Feca é avisado uma vez
    out, st, avisos = _leitor(monkeypatch, tsv, final=True)
    assert R.codigos_do_tsv(out) == {"88092600919", "88092600920"} and st["recusadas"] == 0
    assert len(avisos) == 1 and "88092600920" in avisos[0] and "sem odd" in avisos[0]


def test_a_recusa_final_volta_como_faltante_nos_dois_caminhos():
    src = (RAIZ / "app" / "main.py").read_text(encoding="utf-8")
    seq = src[src.index("async def _stream_sequential"):src.index("async def _stream_parallel")]
    par = src[src.index("async def _stream_parallel"):src.index("def _evento(")]
    for corpo, var, rot in ((seq, "accumulated", "seq"), (par, "resultado", "par")):
        i = corpo.index(f'"{rot} pós-repesca",\n')
        trecho = corpo[i:i + 600]
        assert "final=True" in trecho, rot
        assert f'conferir_cobertura({var}, texto)["faltantes"]' in trecho, rot
    # e o faltante vira o aviso da tela (o "REPROCESSE" de sempre)
    html = (RAIZ / "app" / "static" / "index.html").read_text(encoding="utf-8")
    assert "NÃO foram extraídos — REPROCESSE" in html
