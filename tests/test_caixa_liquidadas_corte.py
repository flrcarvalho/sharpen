"""Caixa (s453): a aposta JÁ LIQUIDADA na ativação, com evento a partir do corte.

`bilhetes.data` é a data do EVENTO. A aposta de hoje que já liquidou tem o retorno DENTRO do
saldo que o operador acabou de digitar, mas cai na janela da projeção (`data ≥ corte`) e o P/L
dela era somado de novo. Medido: Jonathan CopaWin, Caixa ligada 12/11/2026 16:33 com 2.668,00;
8 apostas de 12/11 já liquidadas somavam −367,25, exatamente a divergência da 1ª conferência
(9 minutos depois). Mais 10 Caixas com o mesmo defeito.

A saída é o espelho do `abertas_corte`: na ativação com corte = HOJE o servidor grava em
`liquidadas_corte` os ids já liquidados com evento ≥ corte, e a projeção os trata como
anteriores ao corte.

Mutações (todas detectadas): (1) tirar o `ja_no_saldo` da condição do `_caixa_projetar`;
(2) `_caixa_liquidadas_ids` devolvendo também com corte no passado; (3) devolvendo aberta.

O que NÃO cobre: a gravação (`caixa_lancar` → UPDATE da coluna) é Postgres e só roda no
harness de banco; e a aposta feita e liquidada antes da ativação mas CAPTURADA depois (a
"tardia já liquidada"), que não tem prova de quando liquidou e continua contando.
"""
from repository import _caixa_liquidadas_ids, _caixa_projetar

HOJE = "2026-11-12"


def _ini(**kw):
    return {"id": 1, "tipo": "inicial", "data": HOJE, "valor": 2668.0, "obs": "", "projetado": None,
            "abertas_corte": kw.get("abertas", []), "liquidadas_corte": kw.get("liquidadas", []),
            "criado_em": "2026-11-12T19:33:46+00:00"}


def _ap(id_, data, stake, resultado="", odd=None):
    return {"id": id_, "data": data, "stake": stake, "odd": odd, "resultado": resultado, "criado_em": None}


APOSTAS = [
    _ap(10, "12/11/2026", "150,00", "L"),            # já perdida na ativação: −150 já no saldo
    _ap(11, "12/11/2026", "100,00", "W", "2,00"),    # já ganha na ativação: +100 já no saldo
    _ap(12, "13/11/2026", "50,00"),                  # aberta (feita depois da ativação)
    _ap(13, "10/11/2026", "80,00", "W", "3,00"),     # evento antes do corte: nunca conta
]


def test_lista_so_liquidadas_com_evento_a_partir_do_corte_hoje():
    assert _caixa_liquidadas_ids(APOSTAS, HOJE, HOJE) == [10, 11]


def test_corte_no_passado_nao_lista_nada():
    """Corte de ontem: a aposta pode ter liquidado depois da leitura do saldo. Sem prova, conta."""
    assert _caixa_liquidadas_ids(APOSTAS, "2026-11-11", HOJE) == []


def test_projecao_nao_soma_de_novo_o_que_ja_estava_no_saldo():
    sem = _caixa_projetar([_ini()], APOSTAS)
    com = _caixa_projetar([_ini(liquidadas=[10, 11])], APOSTAS)
    assert round(sem["pl"], 2) == -50.0                       # o defeito: −150 + 100 de novo
    assert com["pl"] == 0.0 and com["disponivel"] == 2668.0 - 50.0
    assert com["n_anteriores"] == sem["n_anteriores"] + 2     # a tela diz que ficaram de fora


def test_conta_ligada_antes_da_coluna_segue_igual():
    """`liquidadas_corte` vazio (NULL) = Caixa antiga: o Ajuste dela já absorveu, nada muda."""
    antigo = _ini(); antigo.pop("liquidadas_corte")
    assert _caixa_projetar([antigo], APOSTAS) == _caixa_projetar([_ini()], APOSTAS)
