"""Gate do "Resolver apostas abertas" (bet365) — o CASAMENTO e o veredito.

Desenho em `docs/PLANO_RESOLVER_ABERTAS.md`. O que este arquivo cobre é a única parte que
decide escrita: `casar_abertas_por_carimbo` (quem casa com quem) e
`resultado_da_aposta_encontrada` (que resultado o retorno da casa determina).

POR QUE A BARRA É ALTA AQUI: **casamento errado não perde bilhete, CORROMPE.** Escreve o
resultado de uma aposta em outra, e o P/L fecha certo nas duas pontas porque os dois
valores existem — é a família da descrição e da stake que vieram do vizinho. Um bilhete
perdido aparece; um bilhete trocado, não.

O QUE ELE NÃO COBRE, de propósito:
  • a rota `/bet365/resolver-abertas` de ponta a ponta (precisa de Postgres, que aqui só
    existe no CI) e a trava de correção humana, que é uma consulta ao banco;
  • o lado da extensão: ler a lista da casa e montar `encontrados`. Nada disso existe
    ainda;
  • se o `RT` da casa é VERDADE. O gate confia no número publicado — ele foi conferido
    contra 13.115 bilhetes já resolvidos (98,7% a 100% por desfecho, s382), e isso é
    medição datada, não garantia.

Mutações provadas — cada uma foi APLICADA ao código e o teste ao lado ficou vermelho:
  1. par único só num sentido (uma aberta, N na casa) → test_duas_apostas_da_casa…
  2. par único só no outro sentido (N abertas, uma na casa) → test_duas_abertas…
  3. a odd sai da chave → test_mesmo_carimbo_e_stake_com_odds_diferentes…
  4. a odd entra crua, sem `_norm_odd` → test_a_mesma_odd_escrita_de_dois_jeitos…
  5. retorno ausente vira zero → test_retorno_ausente_nao_vira_perdida
  6. a odd da casa manda em SISTEMA → test_em_sistema_a_odd_da_casa_nao_manda
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

from repository import (  # noqa: E402
    casar_abertas_por_carimbo, resultado_da_aposta_encontrada, _chave_carimbo,
)

# Bilhete REAL, corrigido na s382 (#269465): stake 180, odd 1,9 da casa, retorno 261,00.
# (180/2 × 1,9) + 90 = 261 — a conta da meia vitória fecha exata.
CARIMBO = "20260722233620"


def aberta(**kw):
    base = {"id": 1, "aposta_em": CARIMBO, "stake": "180,00", "odd": "1,9",
            "descricao": "Under 3.0,3.5 Gols [A v B]", "sistema": None}
    base.update(kw)
    return base


def achado(**kw):
    base = {"carimbo": CARIMBO, "stake": "180.00", "odd": "1.9", "retorno": "261.00"}
    base.update(kw)
    return base


# ── O casamento ───────────────────────────────────────────────────────────────

def test_par_unico_casa():
    r = casar_abertas_por_carimbo([aberta()], [achado()])
    assert len(r["pares"]) == 1
    assert r["pares"][0][0]["id"] == 1
    assert not r["ambiguos"] and not r["sem_par"]


def test_duas_abertas_com_a_mesma_chave_nao_decidem_nada():
    """Par único NOS DOIS SENTIDOS. Duas apostas iguais existem de verdade (mesmo segundo,
    mesma stake, mesma odd) e escolher uma delas é sortear em qual gravar."""
    r = casar_abertas_por_carimbo([aberta(id=1), aberta(id=2)], [achado()])
    assert not r["pares"]
    assert sorted(a["id"] for a in r["ambiguos"]) == [1, 2]


def test_duas_apostas_da_casa_com_a_mesma_chave_nao_decidem_nada():
    r = casar_abertas_por_carimbo([aberta()], [achado(), achado(retorno="342.00")])
    assert not r["pares"]
    assert [a["id"] for a in r["ambiguos"]] == [1]


def test_mesmo_carimbo_e_stake_com_odds_diferentes_sao_apostas_diferentes():
    """A odd é a terceira parte da chave, e é ela que zera a colisão.

    MEDIDO (s382, 639 bilhetes reais do 1º dia com carimbo): carimbo sozinho deixa 13
    bilhetes ambíguos (2,03%), carimbo+stake deixa 10, carimbo+stake+odd deixa ZERO.
    """
    r = casar_abertas_por_carimbo(
        [aberta(id=1, odd="1,9"), aberta(id=2, odd="2,5")],
        [achado(odd="1.9"), achado(odd="2.5", retorno="450.00")])
    assert len(r["pares"]) == 2
    assert not r["ambiguos"]


def test_a_mesma_odd_escrita_de_dois_jeitos_casa():
    """`1,9` no banco e `1.90` na casa são a MESMA odd. Em string crua não são, e o
    casamento falharia em silêncio — a régua é o `_norm_odd`, a mesma da `chave_orfa`."""
    r = casar_abertas_por_carimbo([aberta(odd="1,9", stake="180")],
                                  [achado(odd="1.90", stake="180.00")])
    assert len(r["pares"]) == 1


def test_aberta_sem_carimbo_sai_como_sem_chave():
    """As 480 abertas anteriores à 0.7.18 não têm carimbo. Elas não somem: saem
    nomeadas, para a tela poder dizer quantas ficaram de fora e por quê."""
    r = casar_abertas_por_carimbo([aberta(aposta_em=None)], [achado()])
    assert not r["pares"]
    assert [a["id"] for a in r["sem_chave"]] == [1]


def test_carimbo_de_tamanho_errado_nao_vira_chave():
    """17 dígitos é o `TP` cru do summary e 8 é data solta. A chave é de 14, e só."""
    for ruim in ("20260722233620000", "20260722", "", None, "abcdefghijklmn"):
        assert _chave_carimbo(ruim, "180,00", "1,9") is None


def test_aberta_sem_par_na_lista_da_casa_nao_e_erro():
    """Aposta que continua aberta na casa simplesmente não aparece na lista de
    resolvidas. Isso é informação, não falha."""
    r = casar_abertas_por_carimbo([aberta()], [])
    assert not r["pares"] and [a["id"] for a in r["sem_par"]] == [1]


# ── O veredito ────────────────────────────────────────────────────────────────

def test_meia_vitoria_sai_como_HW_com_a_odd_da_casa():
    res, odd_nova, _ = resultado_da_aposta_encontrada(aberta(), achado())
    assert res == "HW"


def test_vitoria_cheia_continua_W():
    res, _, _ = resultado_da_aposta_encontrada(aberta(), achado(retorno="342.00"))
    assert res == "W"


def test_retorno_zero_e_perdida():
    res, _, _ = resultado_da_aposta_encontrada(aberta(), achado(retorno="0"))
    assert res == "L"


def test_retorno_igual_a_stake_e_devolvida():
    res, _, _ = resultado_da_aposta_encontrada(aberta(), achado(retorno="180.00"))
    assert res == "V"


def test_retorno_ausente_nao_vira_perdida():
    """Zero é uma conta feita; ausência é ausência.

    Com o retorno achatado em 0, um bilhete GANHO viraria `L` e o P/L iria a −1u sem
    erro nenhum em lugar nenhum (o caso dos `Só Chutes 12`, s318).
    """
    for vazio in (None, "", "   "):
        res, _, motivo = resultado_da_aposta_encontrada(aberta(), achado(retorno=vazio))
        assert res is None and motivo


def test_em_sistema_a_odd_da_casa_nao_manda():
    """Em SISTEMA a odd do cupom não descreve a linha (a da linha é a MÉDIA das apostas),
    então ela não pode decidir o resultado. Mesma exceção do `corrigir_stake_tsv`.

    O teste só prova alguma coisa com as duas odds DIFERENTES — foi o erro da 1ª versão
    deste arquivo, que passou a mesma odd nos dois lados e teria ficado verde com a
    exceção apagada. É o "dado sintético que não exerce a regra" do `CLAUDE.md`.

    Aqui a odd da linha é 3,0 (a média que o sistema grava) e a da casa é 1,9. Com a odd
    da CASA, a fórmula de HW fecha exata em 261. Com a da LINHA, nenhuma fecha, e o
    veredito cai em cashout. Se o resultado vier `HW`, a odd do cupom decidiu.
    """
    res, _, _ = resultado_da_aposta_encontrada(
        aberta(sistema="3 x Duplas", odd="3,0"), achado(odd="1.9"))
    assert res != "HW", "a odd do cupom decidiu meia vitória num sistema"


def test_fora_de_sistema_a_mesma_configuracao_da_HW():
    """O par do teste acima: sem `sistema`, a odd da casa MANDA e o HW aparece.

    Sem este, apagar a exceção do sistema passaria despercebido de outro jeito — bastaria
    a odd da casa nunca ser usada para o teste de cima ficar verde por acidente.
    """
    res, _, _ = resultado_da_aposta_encontrada(aberta(odd="3,0"), achado(odd="1.9"))
    assert res == "HW"


def test_stake_ilegivel_no_banco_nao_escreve():
    res, _, motivo = resultado_da_aposta_encontrada(aberta(stake=""), achado())
    assert res is None and motivo
