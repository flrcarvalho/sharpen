"""Modo sombra — Fase 0 do tradutor determinístico (sessão 297).

`parear_sombra` monta o corpo de treino do tradutor: para cada bilhete, o BLOCO BRUTO
que o robô da casa emitiu ao lado da DECISÃO que a IA tomou (esporte, categoria,
descrição), pareados pelo CÓDIGO do bilhete.

O modo de falha que estes testes existem para pegar é **cruzamento silencioso**: se o
bloco do bilhete A for gravado ao lado da decisão do bilhete B, nada quebra, nada
avisa, e o corpo de treino nasce envenenado — o tradutor aprenderia a associar o
mercado errado ao rótulo errado. Não há tela que mostre isso; só teste.

⚠️ O QUE ESTES TESTES **NÃO** COBREM (honesto):
  • A gravação em si (`registrar_sombra`) — ela é uma casca de I/O sobre a função pura
    testada aqui. Não há banco nestes testes, então o INSERT, o `executemany` e a purga
    por retenção **não são exercidos**. Quebra de SQL passaria verde aqui.
  • Os outros 15 formatadores de casa. As fixtures abaixo são da Pinnacle, geradas pelo
    inject e pelo formatador REAIS (via harness). Um formato de outra casa que quebre o
    marcador `[Código: …]` não seria visto.
  • Se a decisão da IA está CERTA. Isso é a fase 2 (diff contra a IA); aqui só se prova
    que a decisão dela ficou colada no bloco certo.

As fixtures de texto são saída literal de `formatTicketPN` sobre `pinnacle.settled.json`
e `pinnacle.open.json` — não foram escritas à mão.
"""
import os
import sys

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-nao-usada")

import database  # noqa: E402  (stub do conftest)
if not hasattr(database, "init_db"):
    async def _init_db():  # pragma: no cover - nunca chamado nos testes
        raise RuntimeError("DB indisponível nos testes")
    database.init_db = _init_db

from repository import parear_sombra, _SOMBRA_BRUTO_MAX  # noqa: E402


# ── Fixtures: saída REAL do formatador da Pinnacle ────────────────────────────
# Repare no 3099722204: sendo múltipla, ele **não tem** a linha `Esporte (casa):` —
# o esporte só existe dentro das seleções. É por isso que a sombra grava o bloco
# INTEIRO em vez de um campo isolado: o campo nem sempre existe.
TEXTO = """[Código: 9000000001]
Data: 09/08/2026
Apostado em: 07/08/2026
Stake: 300,00
Status: em aberto (aguardando resultado — NÃO liquidar; sem resultado)
Odd total: 1,877
Esporte (casa): Soccer · Austrália - Copa
Seleções:
  • South Melbourne -2 · South Melbourne v Fremantle City (Regular)

[Código: 9000000002]
Data: 08/08/2026
Apostado em: 07/08/2026
Stake: 300,00
Status: em aberto (aguardando resultado — NÃO liquidar; sem resultado)
Odd total: 1,900
Esporte (casa): Soccer · Austrália - NPL Victoria Feminino
Seleções:
  • Box Hill United 0,25 · Bulleen Lions v Box Hill United (Regular)

[Código: 3099722204]
Data: 09/08/2026
Apostado em: 09/08/2026
Stake: 509,00
Status: Ganho (WON) → W · P/L 336,66
Odd total: 1,661
Tipo: Múltipla (2 seleções)
Seleções:
  • Volleyball · Pan American Cup · EUA -2,5 · EUA v Costa Rica (Games) @ 1,238 · 09/08/2026
  • Volleyball · Pan American Cup · Canadá -2,5 · Canadá v Trinidad e Tobago (Games) @ 1,341 · 09/08/2026

[Código: 3099205574]
Data: 08/08/2026
Apostado em: 08/08/2026
Stake: 208,00
Status: Ganho (WON) → W · P/L 137,70
Odd total: 1,662
Esporte (casa): Soccer · Honduras - Liga Nacional
Seleções:
  • Real Espana -0,75 · Real Espana v Genesis (Regular)
"""


def _linha(data, esporte, aposta, descricao, stake, odd, resultado, codigo):
    """Uma linha de TSV canônico: 10 colunas + a 11ª interna (código)."""
    return "\t".join([data, esporte, "", "Pinnacle", "conta1", aposta, descricao,
                      stake, odd, resultado, codigo])


# A decisão da IA para os quatro bilhetes acima, na ordem em que o TSV sai.
TSV = "\n".join([
    _linha("09/08/2026", "Futebol", "Handicap Asiático",
           "South Melbourne -2 [South Melbourne v Fremantle City]",
           "300,00", "1,877", "", "9000000001"),
    _linha("08/08/2026", "Futebol", "Handicap Asiático",
           "Box Hill United +0,25 [Bulleen Lions v Box Hill United]",
           "300,00", "1,900", "", "9000000002"),
    _linha("09/08/2026", "Múltiplos", "Handicap",
           "EUA -2,5 // Canadá -2,5", "509,00", "1,661", "W", "3099722204"),
    _linha("08/08/2026", "Futebol", "Handicap Asiático",
           "Real Espana -0,75 [Real Espana v Genesis]",
           "208,00", "1,662", "W", "3099205574"),
])

# Índices da tupla gravada: (dono, casa, codigo, bruto, ia_esporte, ia_aposta, ia_descricao)
DONO, CASA, CODIGO, BRUTO, ESPORTE, APOSTA, DESCRICAO = range(7)


def test_pareia_os_quatro_bilhetes():
    linhas = parear_sombra("Feca", "Pinnacle", TEXTO, TSV)
    assert len(linhas) == 4, f"esperava 4 pares, vieram {len(linhas)}"
    assert [l[CODIGO] for l in linhas] == \
        ["9000000001", "9000000002", "3099722204", "3099205574"]
    assert all(l[DONO] == "Feca" and l[CASA] == "Pinnacle" for l in linhas)


def test_cada_bloco_fica_com_a_decisao_do_PROPRIO_bilhete():
    """O teste que importa: cruzar bloco com decisão alheia não quebra nada sozinho.

    Cada bilhete tem uma marca textual que só existe nele. Se o pareamento deslizar
    uma casa (erro clássico de `split` com grupo de captura), a marca cai no bloco
    errado e esta asserção fica vermelha.
    """
    por_codigo = {l[CODIGO]: l for l in parear_sombra("Feca", "Pinnacle", TEXTO, TSV)}

    marca = {
        "9000000001": "South Melbourne",
        "9000000002": "Box Hill United",
        "3099722204": "Múltipla (2 seleções)",
        "3099205574": "Real Espana",
    }
    for codigo, texto_unico in marca.items():
        bruto = por_codigo[codigo][BRUTO]
        assert texto_unico in bruto, f"{codigo}: o bloco não é o dele ({texto_unico!r} ausente)"
        # ...e nenhuma marca dos OUTROS pode ter vazado para dentro dele.
        for outro, alheio in marca.items():
            if outro != codigo:
                assert alheio not in bruto, f"{codigo}: bloco contaminado com {outro}"

    # E a decisão colada é a daquele bilhete, não a do vizinho.
    assert por_codigo["3099722204"][ESPORTE] == "Múltiplos"
    assert por_codigo["3099722204"][DESCRICAO] == "EUA -2,5 // Canadá -2,5"
    assert por_codigo["9000000001"][ESPORTE] == "Futebol"


def test_bilhete_sem_par_nao_entra():
    """Só vira linha o que casa DOS DOIS lados. Sobra de um lado só é descartada."""
    # (a) bilhete no texto que a IA não devolveu → fora
    tsv_curto = "\n".join(TSV.split("\n")[:2])
    assert len(parear_sombra("Feca", "Pinnacle", TEXTO, tsv_curto)) == 2

    # (b) código no TSV que não existe no texto → fora (não inventa bloco vazio)
    tsv_intruso = TSV + "\n" + _linha(
        "01/08/2026", "Tênis", "ML", "Sinner", "10,00", "1,75", "W", "0000000000")
    linhas = parear_sombra("Feca", "Pinnacle", TEXTO, tsv_intruso)
    assert len(linhas) == 4
    assert "0000000000" not in [l[CODIGO] for l in linhas]

    # (c) linha sem a 11ª coluna (código) → fora: sem código não há como parear
    tsv_sem_codigo = "\t".join([
        "01/08/2026", "Tênis", "", "Pinnacle", "conta1", "ML", "Sinner",
        "10,00", "1,75", "W"])
    assert parear_sombra("Feca", "Pinnacle", TEXTO, tsv_sem_codigo) == []


def test_print_e_texto_vazio_nao_geram_nada():
    """Print não tem marcador de código — e também não tem payload para traduzir.

    Ficar de fora aqui é o comportamento certo, não uma lacuna.
    """
    assert parear_sombra("Feca", "Pinnacle", None, TSV) == []
    assert parear_sombra("Feca", "Pinnacle", "", TSV) == []
    assert parear_sombra("Feca", "Pinnacle", "foto colada, sem marcador nenhum", TSV) == []
    assert parear_sombra("Feca", "Pinnacle", TEXTO, "") == []


def test_bloco_gigante_e_truncado_sem_derrubar_a_linha():
    """Bilhete-monstro corta no teto; a linha continua entrando (dado parcial > nada)."""
    inchado = TEXTO.replace(
        "Seleções:\n  • Real Espana", "Seleções:\n" + ("  • perna · x\n" * 900) + "  • Real Espana")
    linhas = parear_sombra("Feca", "Pinnacle", inchado, TSV)
    assert len(linhas) == 4
    assert all(len(l[BRUTO]) <= _SOMBRA_BRUTO_MAX for l in linhas)
    gigante = [l for l in linhas if l[CODIGO] == "3099205574"][0]
    assert len(gigante[BRUTO]) == _SOMBRA_BRUTO_MAX
