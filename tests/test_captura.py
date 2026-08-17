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


def test_backstop_casa_de_host_da_pitaco():
    """A Pitaco é a antiga "Rei do Pitaco" — a grafia foi unificada no banco na s270 e a casa
    tem UMA chave só (`PITACO`).

    O backstop compara chaves por igualdade exata, o que só é seguro enquanto cada casa tiver
    uma chave. Enquanto as duas grafias conviveram, `casa_de_host` devolvia sempre a primeira
    e o `!=` rejeitava com 409 quem capturava do site CERTO.
    """
    assert captura.casa_de_host("pitaco.bet.br") == "PITACO"
    assert captura.casa_de_host("www.pitaco.bet.br") == "PITACO"
    # O domínio ANTIGO da marca não está registrado (a operação regulada é a `.bet.br`).
    assert captura.casa_de_host("reidopitaco.com.br") is None
    # E a grafia velha não pode ter voltado ao registro: ela não casa mais linha nenhuma
    # do banco, então uma sessão nela capturaria para uma casa que não existe.
    assert "REIDOPITACO" not in captura._HOSTS_POR_CASA
    assert "REIDOPITACO" not in captura._MODO_POR_CASA


def test_modo_da_casa_pitaco_e_texto():
    # Modo "print" aqui significaria a extensão nem tentar o robô — falha silenciosa.
    assert captura.modo_da_casa("PITACO") == "texto"


def test_backstop_casa_de_host_da_novibet():
    """A Novibet é plataforma PRÓPRIA e serve a API no mesmo host do site.

    Isso torna o backstop casa↔site especialmente simples aqui: não há domínio de gateway
    separado para registrar (como o `biahosted.com` das casas Altenar), então o host da aba
    é o único que importa.
    """
    assert captura.casa_de_host("novibet.bet.br") == "NOVIBET"
    assert captura.casa_de_host("www.novibet.bet.br") == "NOVIBET"
    # `.com` é a operação internacional, não a regulada no BR — fora do registro de propósito.
    assert captura.casa_de_host("novibet.com") is None
    # E o guard do domínio parecido continua valendo.
    assert captura.casa_de_host("novibet.bet.br.evil.com") is None


def test_modo_da_casa_novibet_e_texto():
    # Modo "print" aqui significaria a extensão nem tentar o robô — falha silenciosa.
    assert captura.modo_da_casa("NOVIBET") == "texto"
