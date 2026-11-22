"""A linha repescada que sumia no bloco tsv VAZIO (s464, Vavada 5679661219, 22/11/2026).

O caso: lote de 1 bilhete (a Ficha resolveu os outros 52). A IA respondeu SEM cabeçalho e
com o Tipster pulado; o leitor recusou a única linha e o bloco ficou "```tsv\\n```". A
repescagem trouxe a linha certa, o log disse "1 linha(s) repescada(s)", e o recorte
'```tsv\\n(.*?)\\n```' não achava bloco vazio (falta a quebra antes do fechamento):
`_set_tsv_rows` devolvia o texto intacto, a linha sumia e o `/salvar` nem era chamado.
Múltipla perdida de 40: a Caixa ficou 40 acima da casa.

O que estes testes travam:
- o caminho real, com o TSV que a IA devolveu naquele dia, passando pelo leitor de
  verdade (`repository.alinhar_tsv`) e pela `_garantir_cobertura` com a repescagem dublada;
- cada helper que recorta o bloco (`_extract_tsv_rows`, `_reverse_tsv_rows`,
  `_set_tsv_rows`, `_apply_betfair_dates`, `contrato_texto.juntar_resultado`) com bloco vazio;
- o padrão antigo não volta a ser escrito em `app/` (gate por varredura do código);
- a trava de contagem da cobertura acusa em ERROR quando a montagem perde linha.

O que NÃO cobrem: o front (`parseResposta` no `index.html`, que já aceitava bloco vazio) e
a chamada real ao modelo. Provados por mutação na s464 (3 mutações, 3 detectadas):
- padrão antigo em `_TSV_BLOCO_RE` → caem o caso real (pela contagem de blocos), o
  `_set_tsv_rows` em bloco vazio e o gate de varredura. Sem a contagem de blocos o caso
  real ESCAPAVA: as duas defesas se cobrem, e a segunda salva a linha num bloco duplicado;
- sem a criação de bloco em `_set_tsv_rows` → cai a resposta sem bloco nenhum;
- sem a trava de contagem da cobertura → cai o teste do ERROR.
"""
import asyncio
import logging
import os
import pathlib
import re

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-nao-usada")

import database  # noqa: E402  (stub do conftest)
if not hasattr(database, "init_db"):
    async def _init_db():  # pragma: no cover
        raise RuntimeError("DB indisponível nos testes")
    database.init_db = _init_db

import main  # noqa: E402
import contrato_texto  # noqa: E402
from repository import alinhar_tsv, conferir_cobertura  # noqa: E402

COD = "5679661219"
TEXTO = (f"[Código: {COD}]\nData: 21/11/2026\nStake: 40,00\nOdd total: 15,278406\n"
         "Status: Perdeu → L\nSeleções (3):\n  • AS Monaco v Auxerre · Cartões 1x2 · AS Monaco")

# O titular_bruto gravado pela sombra às 11:00:27 UTC de 22/11/2026, verbatim: sem
# cabeçalho, Tipster pulado ("Vavada" caiu no lugar dele) e Parceiro vazio.
BRUTO_REAL = (
    "```tsv\n"
    f"21/11/2026\tMúltiplos\tVavada\t\t\tMúltipla\tAS Monaco [Cartões 1x2] [AS Monaco v Auxerre]"
    f" // Over 18.5 Chutes Roma [Parma Calcio v Roma] // Hawks Helsinki +4.5 [Hawks Helsinki v"
    f" Westend Indians]\t40,00\t15,278406\tL\t{COD}\n"
    "```\n\n## Notas Críticas\n\n1. **Esporte = Múltiplos**: as 3 pernas são de jogos distintos."
)

# A linha que a repescagem devolveria: certa, 11 colunas.
REPESCADA = (f"21/11/2026\tMúltiplos\t\tVavada\t+11982151314 [Eu]\tMúltipla\tAS Monaco - Cartões"
             f" 1x2 [AS Monaco v Auxerre] // Roma Over 18.5 Chutes [Parma Calcio v Roma] //"
             f" Hawks Helsinki +4.5 [Hawks Helsinki v Westend Indians]\t40,00\t15,278406\tL\t{COD}")


def _dublar(monkeypatch, linhas):
    async def _fake(system, texto, faltantes, modelo, instrucao_block, pensamento=None):
        return list(linhas), {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0}
    monkeypatch.setattr(main, "_repescar_faltantes", _fake)


def _cods(texto):
    return [r.split("\t")[10] for r in main._extract_tsv_rows(texto)]


# ── o caso real, ponta a ponta ────────────────────────────────────────────────

def test_o_leitor_esvazia_o_bloco_do_caso_real():
    """Pré-condição: é o LEITOR de verdade que deixa o bloco vazio. Se um dia ele passar a
    aceitar a linha, o teste abaixo deixa de exercer a regra e este avisa."""
    pos, st = alinhar_tsv(BRUTO_REAL, casa="Vavada", exige_codigo=True)
    assert st["recusadas"] == 1
    assert "```tsv\n```" in pos
    assert conferir_cobertura(pos, TEXTO)["faltantes"] == [COD]


def test_a_repescada_entra_no_bloco_que_o_leitor_esvaziou(monkeypatch):
    pos, _ = alinhar_tsv(BRUTO_REAL, casa="Vavada", exige_codigo=True)
    _dublar(monkeypatch, [REPESCADA])
    saida, cob, _ = asyncio.run(main._garantir_cobertura(
        [], pos, TEXTO, "modelo", {"type": "text", "text": "i"}, False))
    assert _cods(saida) == [COD]
    assert cob["faltantes"] == [] and cob["recuperados"] == 1
    assert "## Notas Críticas" in saida
    # UM bloco só. Sem esta linha a mutação "padrão antigo" escapava: a criação de bloco do
    # `_set_tsv_rows` salvava a linha num bloco NOVO e deixava o vazio para trás.
    assert saida.count("```tsv") == 1
    # é o que o front recorta antes de chamar o /salvar
    m = re.search(r"```tsv\n([\s\S]*?)```", saida)
    assert m and COD in m.group(1)


def test_resposta_sem_bloco_nenhum_ainda_guarda_a_repescada(monkeypatch):
    """Mesma família (s179): a IA respondeu só com notas. A repescada não pode sumir."""
    _dublar(monkeypatch, [REPESCADA])
    saida, cob, _ = asyncio.run(main._garantir_cobertura(
        [], "## Notas Críticas\nNenhuma", TEXTO, "modelo", {"type": "text", "text": "i"}, False))
    assert _cods(saida) == [COD] and cob["faltantes"] == []
    assert saida.count("```tsv") == 1


def test_a_cobertura_acusa_em_error_se_a_montagem_perder_linha(monkeypatch, caplog):
    """A trava de contagem: o log de "repescada(s)" não pode mais ser o único rastro."""
    pos, _ = alinhar_tsv(BRUTO_REAL, casa="Vavada", exige_codigo=True)
    _dublar(monkeypatch, [REPESCADA])
    monkeypatch.setattr(main, "_set_tsv_rows", lambda texto, rows: texto)   # a perda antiga
    with caplog.at_level(logging.ERROR, logger=main.logger.name):
        asyncio.run(main._garantir_cobertura(
            [], pos, TEXTO, "modelo", {"type": "text", "text": "i"}, False))
    assert any("linha perdida na montagem" in r.getMessage() for r in caplog.records)


# ── cada helper com bloco vazio ───────────────────────────────────────────────

VAZIO = "```tsv\n```\n\n## Notas Críticas\nNenhuma"
VAZIO_COM_HEADER = f"```tsv\n{main._TSV_HEADER}\n```"


def test_extract_de_bloco_vazio_e_lista_vazia():
    assert main._extract_tsv_rows(VAZIO) == []
    assert main._extract_tsv_rows(VAZIO_COM_HEADER) == []


def test_set_tsv_rows_em_bloco_vazio_poe_as_linhas_e_preserva_notas():
    novo = main._set_tsv_rows(VAZIO, [REPESCADA])
    assert _cods(novo) == [COD]
    assert novo.count("```tsv") == 1 and novo.endswith("## Notas Críticas\nNenhuma")


def test_reverse_tsv_rows_em_bloco_vazio_nao_quebra():
    assert main._extract_tsv_rows(main._reverse_tsv_rows(VAZIO)) == []


def test_apply_betfair_dates_em_bloco_vazio_nao_quebra():
    assert main._extract_tsv_rows(main._apply_betfair_dates(VAZIO, {"O/1/1": "01/01/2026"})) == []


def test_juntar_resultado_substitui_o_bloco_vazio_em_vez_de_somar_outro():
    novo = contrato_texto.juntar_resultado(VAZIO, [REPESCADA], main._TSV_HEADER)
    assert novo.count("```tsv") == 1
    assert _cods(novo) == [COD]


# ── o padrão antigo não volta ─────────────────────────────────────────────────

def test_ninguem_em_app_recorta_o_bloco_pelo_padrao_que_exige_a_quebra():
    """O defeito nasceu de quatro cópias do mesmo recorte. Recorte novo usa `_bloco_tsv`."""
    antigo = re.compile(r"```tsv\\n\(\.\*\?\)\\n```")
    app = pathlib.Path(main.__file__).parent
    achados = [f"{p.name}:{i}" for p in app.rglob("*.py")
               for i, linha in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
               if antigo.search(linha)]
    assert achados == []
