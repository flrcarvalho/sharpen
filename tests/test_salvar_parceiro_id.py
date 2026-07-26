"""Regressão da sessão 195 — o lote não pode cair numa conta que não existe.

A conta `Tivo · Feca` foi renomeada ENQUANTO um lote de 22 bilhetes estava em voo.
O card de extração carrega uma cópia RASA do parceiro (nome congelado no clique), então
o `/salvar` gravou com o nome VELHO: 22 bilhetes órfãos — presentes no banco, invisíveis
em todas as telas, e a UI dizendo "✓ 22 novo(s)" enquanto a grade mostrava 0.

Fix: quando vem `parceiro_id`, o nome da conta é lido do banco NO INSTANTE DA GRAVAÇÃO e
manda sobre o texto que o cliente enviou. Mesma família do
`test_roundtrip_casa_cega_preserva_nome_verbatim` (s141, conta paralela por grafia).
"""
import asyncio
from unittest.mock import AsyncMock, patch

import main
from main import SalvarRequest

# 10 colunas + código: data, esporte, tipster, casa, parceiro, aposta, descrição, stake, odd, resultado
TSV = "26/07/2026\tFutebol\t\tTivo\tX\tML\tFlamengo [Flamengo v Santos]\t100,00\t1,50\tW\t298782220"

CONTA = {"id": 351, "casa": "Tivo", "nome": "Feca [Eu]", "arquivado": False}


def _salvar(body, conta, casa_no_banco=None):
    """Chama a rota direto (sem TestClient): as Depends viram argumentos normais.

    `casa_no_banco`: grafia com que a casa já existe (o que `casa_canonica` devolveria).
    None = casa nova, entra como veio.
    """
    canonica = AsyncMock(side_effect=lambda nome: casa_no_banco or nome)
    with patch.object(main, "get_parceiro", AsyncMock(return_value=conta)), \
         patch.object(main, "casa_canonica", canonica), \
         patch.object(main, "upsert_bilhetes", AsyncMock(return_value=(1, 0, [9], [], {}))) as up, \
         patch.object(main, "auto_arquivar", AsyncMock(return_value=0)):
        res = asyncio.run(main.salvar(body, dono="Feca", dono_view="Feca"))
    return res, up.call_args[0][0], canonica


def test_parceiro_id_manda_sobre_o_nome_enviado():
    # O cliente manda o nome VELHO (o que estava congelado no card); o ID aponta para a
    # conta renomeada. Vence o banco.
    body = SalvarRequest(tsv=TSV, casa="Tivo", parceiro="Feca [[Eu]]", parceiro_id=351)
    res, rows, canonica = _salvar(body, CONTA)
    assert rows[0]["parceiro"] == "Feca [Eu]"
    assert res["parceiro"] == "Feca [Eu]"     # eco para o guard do front
    assert res["casa"] == "Tivo"
    # Com conta resolvida, a casa vem DELA — não precisa (nem deve) passar pela trava.
    canonica.assert_not_called()


def test_sem_parceiro_id_usa_o_texto():
    # Extensão, import e /bilhetes/manual não têm id — comportamento antigo intacto.
    body = SalvarRequest(tsv=TSV, casa="Tivo", parceiro="Feca [Eu]")
    res, rows, _ = _salvar(body, None)
    assert rows[0]["parceiro"] == "Feca [Eu]"
    assert res["parceiro"] == "Feca [Eu]"


def test_parceiro_id_inexistente_cai_no_texto():
    # ID de outro dono / conta apagada: nunca derruba o lote, só não corrige o nome.
    body = SalvarRequest(tsv=TSV, casa="Tivo", parceiro="Feca [Eu]", parceiro_id=999999)
    res, rows, _ = _salvar(body, None)
    assert rows[0]["parceiro"] == "Feca [Eu]"
    assert res["parceiro"] == "Feca [Eu]"


def test_sem_parceiro_id_a_casa_passa_pela_trava_de_grafia():
    # Sem conta pela qual resolver, o texto da casa ainda cai na grafia que já existe:
    # é o que impede "Pixbet" de nascer gêmea de "PixBet" (s199).
    body = SalvarRequest(tsv=TSV.replace("\tTivo\t", "\tPixbet\t"), casa="Pixbet",
                         parceiro="Feca [Eu]")
    res, rows, canonica = _salvar(body, None, casa_no_banco="PixBet")
    canonica.assert_awaited_once_with("Pixbet")
    assert rows[0]["casa"] == "PixBet"
    assert res["casa"] == "PixBet"
