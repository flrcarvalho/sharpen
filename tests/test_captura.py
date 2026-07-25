"""Ponte de captura — amarração casa↔site (segurança da informação).

`casa_de_host` é o núcleo do backstop do servidor: uma captura vinda do site de uma casa
CONHECIDA não pode ser gravada no slot de OUTRA casa (ex.: código de Betfair + site da
Superbet). Domínio desconhecido (casa de print) → None → passa (não bloqueia legítimo).
"""
import captura  # conftest põe app/ no sys.path


def test_casa_de_host_reconhece_dominio_exato_e_subdominio():
    assert captura.casa_de_host("betfair.bet.br") == "BETFAIR"
    assert captura.casa_de_host("myactivity.betfair.bet.br") == "BETFAIR"   # subdomínio
    assert captura.casa_de_host("www.superbet.bet.br") == "SUPERBET"
    assert captura.casa_de_host("superbet.com") == "SUPERBET"
    assert captura.casa_de_host("betano.bet.br") == "BETANO"
    assert captura.casa_de_host("bet365.com") == "BET365"
    assert captura.casa_de_host("betesporte.bet.br") == "BETESPORTE"
    # Casas de captura que entraram depois (s170 Pinnacle, s190 KTO): o backstop tem de
    # protegê-las igual. Antes só a KTO era citada, e como EXEMPLO DE DESCONHECIDA no teste
    # abaixo — o registro da s190 passou a devolver "KTO" e o teste ficou vermelho por
    # envelhecimento, não por regressão. Agora a expectativa está do lado certo.
    assert captura.casa_de_host("pinnacle.bet.br") == "PINNACLE"
    assert captura.casa_de_host("kto.bet.br") == "KTO"
    assert captura.casa_de_host("www.kto.bet.br") == "KTO"                 # subdomínio


def test_casa_de_host_desconhecido_ou_vazio_retorna_none():
    # Casa de PRINT (não está em _HOSTS_POR_CASA) → None → NÃO bloqueia (não dá p/ verificar).
    # Use sempre uma casa de print como exemplo aqui: casa de captura vira "conhecida" no dia
    # em que o robô cobrir ela, e o teste quebraria sozinho de novo.
    assert captura.casa_de_host("kingpanda.bet.br") is None
    assert captura.casa_de_host("exemplo.com") is None
    assert captura.casa_de_host("") is None
    assert captura.casa_de_host(None) is None


def test_casa_de_host_nao_confunde_dominio_parecido():
    # Não pode casar um domínio que apenas CONTÉM o nome (evita falso-positivo de bloqueio).
    assert captura.casa_de_host("betfair.bet.br.evil.com") is None
    assert captura.casa_de_host("naosuperbet.com") is None
