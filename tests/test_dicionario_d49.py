"""D49 (Feca, 11/11/2026; revoga a D37, fecha a RC45): o número da Altenar é esporte.

  · `sporttypeid 34` = Tênis de Mesa, `31` = Críquete, `23` = Futsal, `82` = Rugby, para todas as
    casas (`*`), com o peso de uma correção do Feca (`dicionario.ESPORTE_D49`). Fora do `VAGOS`.
  · Sportsbet.io e Thunderpick passam o esporte da casa em vez de vazio (o slug `table-tennis`;
    `gameId <n>`), e o dicionário decide. Os testes do adaptador estão em
    `tests/test_adaptador_sbi.py` e `tests/test_adaptador_thp.py`.

Medição que autorizou: `Auditorias/consultoria_ficha_2026-10/medicoes/2026-11-10_rc45_lista.md`
(14.928 pernas da Altenar, cada `sportTypeId` com um `sportId` só; 116 apostas da Altenar e 40
da Sportsbet.io que travaram a Ficha).

Rodam a `dicionario.carregar` e a `dicionario.semear` REAIS com uma conexão dublada (só o que as
duas pedem ao banco); a `traduzir` é a da virada.

O QUE NÃO COBREM: o banco de verdade (o SQL da `carregar` é o de sempre, coberto pelo harness de
banco) e a regravação das apostas já gravadas pela IA (D10: o passado não muda).
Mutações (s450, detectadas): D1 o 34 volta ao `VAGOS`, D2 o 82 sai da `ESPORTE_D49`, D3 a camada
da D49 sai da `carregar`, D4 a D49 vence a correção do Feca no banco, D5 a semente aprende por
cima da D49, D6 a sbi volta a esvaziar o slug, D7 a thp volta a esvaziar o `gameId`.
"""
import asyncio
import sys

sys.path.insert(0, "app")

import pytest  # noqa: E402

import dicionario  # noqa: E402
import taxonomia  # noqa: E402


class _Conn:
    """O que a `carregar` e a `semear` pedem ao banco. `linhas` = `dicionario_termos`."""

    def __init__(self, linhas=()):
        self.linhas = [dict(zip(("casa", "tipo", "termo_casa", "termo_sharpen", "origem"), x))
                       for x in linhas]
        self.inseridos = []

    async def fetch(self, sql, *a):
        if "FROM dicionario_termos" in sql and "origem = 'feca'" in sql:
            return [r for r in self.linhas if r["origem"] == "feca"]
        if "FROM dicionario_termos" in sql and "origem = 'semente'" in sql:
            return [r for r in self.linhas if r["origem"] == "semente"]
        if "FROM dicionario_termos" in sql:
            return [r for r in self.linhas if r["casa"] in a[0]]
        return []

    async def fetchval(self, sql, *a):
        return len(self.inseridos)

    async def execute(self, sql, *a):
        if "INSERT INTO dicionario_termos" in sql:
            self.inseridos.append(a[:4])

    def transaction(self):
        class _T:
            async def __aenter__(s):
                return s

            async def __aexit__(s, *e):
                return False
        return _T()


def _ficha(esporte_casa, mercado="Vencedor"):
    return {"tipo": "simples", "pernas": [{"esporte_casa": esporte_casa, "mercado_casa": mercado,
                                           "selecao_casa": "1", "evento": "A vs. B"}]}


def _esporte(esporte_casa, linhas=()):
    termos = asyncio.run(dicionario.carregar(_Conn(linhas), "VAVADA", familia=False))
    termos[("categoria", "vencedor")] = "ML"
    esporte, _, faltam = dicionario.traduzir(_ficha(esporte_casa), termos)
    return esporte, faltam


@pytest.mark.parametrize("sid,nome", [("34", "Tênis de Mesa"), ("31", "Críquete"),
                                      ("23", "Futsal"), ("82", "Rugby")])
def test_o_numero_da_altenar_e_esporte(sid, nome):
    assert f"sporttypeid {sid}" not in dicionario.VAGOS
    assert nome in taxonomia.esportes_canonicos()
    assert _esporte(f"sportTypeId {sid}") == (nome, [])


def test_a_gaveta_de_especiais_continua_vaga():
    assert "sporttypeid 300" in dicionario.VAGOS
    esporte, faltam = _esporte("sportTypeId 300", [("*", "esporte", "sporttypeid 300", "E-Sports",
                                                    "semente")])
    assert esporte is None and ("esporte", "sporttypeid 300") in faltam


def test_correcao_do_feca_no_banco_vence_e_semente_nao():
    feca = [("*", "esporte", "sporttypeid 34", "Tênis", "feca")]
    assert _esporte("sportTypeId 34", feca)[0] == "Tênis"
    semente = [("VAVADA", "esporte", "sporttypeid 34", "Hóquei", "semente")]
    assert _esporte("sportTypeId 34", semente)[0] == "Tênis de Mesa"


def test_a_semente_nao_aprende_por_cima_da_d49(monkeypatch):
    unanimes = {("*", "esporte", "sporttypeid 34"): ("Hóquei", 3),
                ("VAVADA", "esporte", "sporttypeid 82"): ("Basquete", 1),
                ("*", "esporte", "darts"): ("Dardos", 2)}

    async def _pares(conn):
        return [], [], {}, set()

    async def _regravar(*a, **kw):
        return []

    async def _recusas(*a, **kw):
        return 0
    monkeypatch.setattr(dicionario, "pares_completo", _pares)
    monkeypatch.setattr(dicionario, "votar", lambda *a: (dict(unanimes), {}, []))
    monkeypatch.setattr(dicionario, "regravar_mes", _regravar)
    monkeypatch.setattr(dicionario, "gravar_recusas", _recusas)
    conn = _Conn()
    asyncio.run(dicionario.semear(conn, "teste"))
    gravados = {(c, t, k) for c, t, k, _ in conn.inseridos}
    assert gravados == {("*", "esporte", "darts")}, gravados
