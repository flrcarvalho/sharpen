"""Gate da virada da Ficha (`app/virada.py`, `03_REGUA_NUMEROS §7`), construída DESLIGADA (s409).

Aqui, sem banco: a chave, a linha da planilha montada da Ficha e as duas travas da rota (a
recusada nunca vai à planilha; falha ao gravar nunca derruba a rota). O teste dos 3 bilhetes
chegando ao banco (aceita pela Ficha, recusada e sem cru pela IA) está no harness de banco,
`tests/test_repository_db.py::test_virada_tres_bilhetes_chegam_ao_banco`.

Crus REAIS da Vavada (`tests/ficha_crus_familias.json`), pelo adaptador `vb` real.

Mutações provadas (aplicadas, teste ao lado vermelho):
  1. `*` passa a virar todas as casas                    → test_asterisco_nao_vira_casa_nenhuma
  2. a recusada também vai à planilha                    → test_so_a_aceita_vai_a_planilha
  3. sem o `try` em volta da gravação                    → test_falha_ao_gravar_nao_derruba_a_rota
  4. esporte da 1ª perna mesmo com esportes misturados   → test_linha_da_planilha_de_uma_ficha_real
  5. sem `origem='ficha'` no `/salvar`                    → test_grava_pelo_salvar_com_origem_ficha
Inócua (registrada, não é buraco): `virada()` aceitar `*` — o `casas_viradas()` já tira o `*`
da lista antes, então o código segue certo sem a linha.

O QUE NÃO COBRE: a tradução de esporte e categoria (vão com o termo da casa até o dicionário
existir, `04_DICIONARIO §4.1`), a conversão de moeda (é a do `/salvar`, coberta lá) e o recorte
no `/extrair` (é o pré-dedup de sempre; o harness de banco prova que ele tira a aceita).
"""
import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, "app")

import ficha  # noqa: E402
import virada  # noqa: E402
from adaptadores import vb  # noqa: E402

CRUS = json.loads((Path(__file__).resolve().parent / "ficha_crus_familias.json")
                  .read_text(encoding="utf-8"))
SESS = SimpleNamespace(dono="TDono", casa_key="VAVADA", casa="Vavada", parceiro="conta [Op]")


def _ficha(cod):
    f = dict(vb.adaptar(CRUS[cod], "VAVADA"), impressao="x")
    assert ficha.validar(f, "VAVADA") == []
    return f


def test_chave_vazia_nada_vira(monkeypatch):
    monkeypatch.delenv("FICHA_CASAS_VIRADAS", raising=False)
    assert not virada.virada("VAVADA")
    monkeypatch.setenv("FICHA_CASAS_VIRADAS", " dexsport , MyStake ")
    assert virada.virada("DEXSPORT") and virada.virada("mystake") and not virada.virada("VAVADA")


def test_asterisco_nao_vira_casa_nenhuma(monkeypatch):
    """Cada casa vira com o "pode" do Feca: `*` não pode ligar todas de uma vez."""
    monkeypatch.setenv("FICHA_CASAS_VIRADAS", "*")
    assert not virada.virada("VAVADA") and virada.casas_viradas() == frozenset()


def test_linha_da_planilha_de_uma_ficha_real():
    """Dupla Vavada 5508528206 (futebol + vôlei), ganha: retorno ÷ stake como a régua mede."""
    col = virada.linha_tsv(_ficha("5508528206"), "Vavada", "conta [Op]").split("\t")
    assert col == ["10/10/2026", "Múltiplos", "", "Vavada", "conta [Op]", "Múltipla",
                   "Total cantos · Mais de 11.5 [Vicenza vs. Pisa] // Handicap de sets · Haro "
                   "Rioja (F) (+1.5) [Haro Rioja (F) vs. Haris (F)]",
                   "25", "7,6192", "W", "5508528206"]


def test_simples_usa_o_termo_da_casa_e_aberta_sai_sem_resultado():
    cru = dict(CRUS["5508528206"], status=0, selections=CRUS["5508528206"]["selections"][:1])
    f = dict(vb.adaptar(cru, "VAVADA"), impressao="x")
    col = virada.linha_tsv(f, "Vavada", "c").split("\t")
    assert (col[1], col[5], col[9]) == (f["pernas"][0]["esporte_casa"],
                                        f["pernas"][0]["mercado_casa"], "")
    assert "\t" not in col[6] and virada._carimbo(f) == "20261010074000"


def _registros():
    boa = ficha._registro(_ficha("5508528206"), [])
    ruim = ficha._registro({"codigo": "5504514128", "cru_recusado": True}, ["status 7"])
    return [boa, ruim]


def test_so_a_aceita_vai_a_planilha(monkeypatch):
    monkeypatch.setenv("FICHA_CASAS_VIRADAS", "VAVADA")
    vistos = []

    async def falso(dono, casa, parceiro, fichas):
        vistos.extend(f["codigo"] for f in fichas)
        return {"salvos": len(fichas)}
    monkeypatch.setattr(virada, "gravar_na_planilha", falso)
    assert asyncio.run(virada.gravar_aceitas(SESS, _registros())) == 1
    assert vistos == ["5508528206"]


def test_casa_nao_virada_nao_grava(monkeypatch):
    monkeypatch.setenv("FICHA_CASAS_VIRADAS", "DEXSPORT")

    async def falso(*a):
        raise AssertionError("não devia gravar")
    monkeypatch.setattr(virada, "gravar_na_planilha", falso)
    assert asyncio.run(virada.gravar_aceitas(SESS, _registros())) == 0


def test_falha_ao_gravar_nao_derruba_a_rota(monkeypatch):
    """O cru e a Ficha já estão guardados: a aposta vai pela IA, pelo texto."""
    monkeypatch.setenv("FICHA_CASAS_VIRADAS", "VAVADA")

    async def quebra(*a):
        raise RuntimeError("banco fora")
    monkeypatch.setattr(virada, "gravar_na_planilha", quebra)
    assert asyncio.run(virada.gravar_aceitas(SESS, _registros())) == 0


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
    r = asyncio.run(virada.gravar_na_planilha("TDono", "Vavada", "conta [Op]", [f]))
    assert r["salvos"] == 1
    body, dono, dono_view, origem = chamadas[0]
    assert (dono, dono_view, origem) == ("TDono", "TDono", "ficha")
    assert body.tsv == virada.linha_tsv(f, "Vavada", "conta [Op]")
    assert body.carimbos == {"5508528206": "20261010074000"} and body.moedas == ["USD"]
