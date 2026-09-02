"""Gate da rota `POST /tipsters/sugerir` (s289) — a ponte entre a tela e `app/matcher.py`.

`tests/test_matcher.py` trava o modelo; aqui se trava o CONTRATO com a tela, que é onde a
mudança falharia em silêncio (o botão "Sugerir tipsters" simplesmente não faria nada):

1. **`fonte` decide quem manda.** 'evidencia' = o modelo respondeu e a tela NÃO deve cair no
   matcher declarativo — era ele que mandava 155 erros para o Arrudex. 'declarativo' = dono sem
   histórico, e aí a tela usa o matcher local (é ele que acerta 100 % na carteira do Jaao26).
2. **Casa DEDICADA a 1 tipster crava**, acima de qualquer inferência: é curadoria humana
   explícita. E casa dedicada a 2 restringe o pool ao invés de cravar.
3. **A stake chega como STRING BR** ("250,00") — o front manda assim. Se o Pydantic ou o parse
   recusarem, a sugestão perde o sinal mais discriminante sem erro nenhum.
4. **Só tipster ATIVO é sugerido** — arquivado não volta por inferência.

Sem banco: `rotulos_humanos`, `casas_dedicadas` e `list_tipsters_cadastro` são monkeypatchados
(o stub de `database` do conftest explodiria se fosse alcançado).
"""
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, "app")
import main  # noqa: E402
import matcher  # noqa: E402

cliente = TestClient(main.app)
DONO = "DonoTeste"


def _bilhete(casa="Bet365", esporte="Futebol", aposta="Múltipla", stake="100,00",
             descricao="A // B", tipster="Alfa"):
    return {"casa": casa, "esporte": esporte, "aposta": aposta, "stake": stake,
            "descricao": descricao, "tipster": tipster}


@pytest.fixture(autouse=True)
def _sem_cache():
    """O modelo é cache de módulo: sem isto um teste envenena o seguinte."""
    matcher.invalidar(DONO)
    yield
    matcher.invalidar(DONO)


@pytest.fixture
def cenario(monkeypatch):
    """Monta a base do dono e devolve um setter para cada peça."""
    estado = {"rotulos": [], "dedicadas": {}, "ativos": ["Alfa", "Beta"], "dominio": {}}

    async def _rotulos(dono):
        assert dono == DONO
        return estado["rotulos"]

    async def _dedicadas(dono):
        return estado["dedicadas"]

    async def _dominio(dono):
        return estado["dominio"]

    async def _cadastro(dono, incluir_arquivados=False):
        return [{"nome": n} for n in estado["ativos"]]

    monkeypatch.setattr(main, "rotulos_humanos", _rotulos)
    monkeypatch.setattr(main, "casas_dedicadas", _dedicadas)
    monkeypatch.setattr(main, "dominio_esportes", _dominio)
    monkeypatch.setattr(main, "list_tipsters_cadastro", _cadastro)
    main.app.dependency_overrides[main.dono_efetivo] = lambda: DONO
    yield estado
    main.app.dependency_overrides.clear()


def _post(bilhetes):
    r = cliente.post("/tipsters/sugerir", json={"bilhetes": bilhetes})
    assert r.status_code == 200, r.text
    return r.json()


# ── fonte ───────────────────────────────────────────────────────────────────────
def test_sem_historico_a_rota_devolve_o_dono_ao_declarativo(cenario):
    """Abaixo de MIN_TREINO o modelo não se sustenta. A rota precisa DIZER isso — senão a tela
    trata "nenhuma sugestão" como abstenção e o dono novo fica sem matcher nenhum."""
    cenario["rotulos"] = [_bilhete() for _ in range(matcher.MIN_TREINO - 1)]
    d = _post([{"id": "1", "casa": "Bet365", "esporte": "Futebol", "aposta": "Múltipla",
                "stake": "100,00", "descricao": "A // B"}])
    assert d["fonte"] == "declarativo"
    assert d["sugestoes"] == {}


def test_com_historico_a_fonte_e_evidencia_e_ela_responde(cenario):
    cenario["rotulos"] = [_bilhete() for _ in range(matcher.MIN_TREINO)]
    d = _post([{"id": "42", "casa": "Bet365", "esporte": "Futebol", "aposta": "Múltipla",
                "stake": "100,00", "descricao": "A // B"}])
    assert d["fonte"] == "evidencia"
    assert d["sugestoes"] == {"42": "Alfa"}
    assert d["treino"] == matcher.MIN_TREINO


def test_bilhete_sem_convicao_nao_entra_na_resposta(cenario):
    """Abstenção é a ausência da chave, não uma chave vazia — a tela itera o que veio."""
    cenario["rotulos"] = [_bilhete() for _ in range(matcher.MIN_TREINO)]
    d = _post([{"id": "9", "casa": "CasaInedita", "esporte": "Críquete", "aposta": "Corridas",
                "stake": "33,00", "descricao": "x"}])
    assert d["fonte"] == "evidencia"
    assert "9" not in d["sugestoes"]


# ── casa dedicada (curadoria humana) ────────────────────────────────────────────
def test_casa_dedicada_a_um_tipster_crava(cenario):
    """Crava mesmo contra o histórico: o dono declarou que aquela casa é de um tipster só.
    Aqui todo o treino diz "Alfa" e a curadoria diz "Beta" — quem manda é a curadoria."""
    cenario["rotulos"] = [_bilhete() for _ in range(matcher.MIN_TREINO)]
    cenario["dedicadas"] = {"bet365": ["Beta"]}
    d = _post([{"id": "7", "casa": "Bet365", "esporte": "Futebol", "aposta": "Múltipla",
                "stake": "100,00", "descricao": "A // B"}])
    assert d["sugestoes"] == {"7": "Beta"}


def test_casa_dedicada_crava_mesmo_sem_historico(cenario):
    """A curadoria não depende de modelo: vale inclusive no dono que cai no declarativo."""
    cenario["rotulos"] = []
    cenario["dedicadas"] = {"bet365": ["Beta"]}
    d = _post([{"id": "7", "casa": "Bet365", "esporte": "Futebol", "aposta": "ML",
                "stake": "50,00", "descricao": "x"}])
    assert d["fonte"] == "declarativo"
    assert d["sugestoes"] == {"7": "Beta"}


def test_casa_dedicada_a_dois_restringe_o_pool_sem_cravar(cenario):
    """Com 2 donos a casa não decide sozinha — ela limita quem pode ganhar e o modelo
    desempata. Aqui o treino inteiro é do Alfa, que está fora do par: ninguém é sugerido."""
    cenario["ativos"] = ["Alfa", "Beta", "Gama"]
    cenario["rotulos"] = [_bilhete() for _ in range(matcher.MIN_TREINO)]
    cenario["dedicadas"] = {"bet365": ["Beta", "Gama"]}
    d = _post([{"id": "7", "casa": "Bet365", "esporte": "Futebol", "aposta": "Múltipla",
                "stake": "100,00", "descricao": "A // B"}])
    assert d["sugestoes"] == {}


def test_dono_de_casa_dedicada_que_foi_arquivado_nao_crava(cenario):
    """Curadoria velha apontando para tipster arquivado não pode ressuscitá-lo."""
    cenario["rotulos"] = [_bilhete() for _ in range(matcher.MIN_TREINO)]
    cenario["dedicadas"] = {"bet365": ["Arquivado"]}
    d = _post([{"id": "7", "casa": "Bet365", "esporte": "Futebol", "aposta": "Múltipla",
                "stake": "100,00", "descricao": "A // B"}])
    assert d["sugestoes"] == {"7": "Alfa"}, "cai no modelo, não no arquivado"


def test_casa_casa_por_slug_ignora_caixa_e_espaco(cenario):
    """`Bet 365` e `bet365` são a mesma casa para a curadoria (slug), como no resto do sistema."""
    cenario["rotulos"] = []
    cenario["dedicadas"] = {"betesporte": ["Beta"]}
    d = _post([{"id": "7", "casa": "BET Esporte", "esporte": "Futebol", "aposta": "ML",
                "stake": "50,00", "descricao": "x"}])
    assert d["sugestoes"] == {"7": "Beta"}


# ── contrato com a tela ─────────────────────────────────────────────────────────
def test_stake_string_br_e_aceita_e_discrimina(cenario):
    """O front manda "97,00". Se isso virasse 0 (ou 400), o final da stake — o sinal mais
    discriminante que existe — sumiria da conta sem ninguém perceber."""
    cenario["rotulos"] = ([_bilhete(tipster="Alfa") for _ in range(matcher.MIN_TREINO)]
                          + [_bilhete(tipster="Beta", stake="97,00") for _ in range(matcher.MIN_TREINO)])
    d = _post([{"id": "1", "casa": "Bet365", "esporte": "Futebol", "aposta": "Múltipla",
                "stake": "97,00", "descricao": "A // B"}])
    assert d["sugestoes"] == {"1": "Beta"}


def test_lote_vazio_nao_quebra(cenario):
    d = _post([])
    assert d["sugestoes"] == {} and d["treino"] == 0


def test_ids_voltam_como_string(cenario):
    """A tela procura pelo id que mandou. Chave numérica no JSON viraria string mesmo, mas o
    contrato precisa ser explícito: o front faz `sug[String(b.id)]`."""
    cenario["rotulos"] = [_bilhete() for _ in range(matcher.MIN_TREINO)]
    d = _post([{"id": "1234", "casa": "Bet365", "esporte": "Futebol", "aposta": "Múltipla",
                "stake": "100,00", "descricao": "A // B"}])
    assert list(d["sugestoes"]) == ["1234"]


def test_modelo_e_reaproveitado_do_cache_entre_chamadas(cenario, monkeypatch):
    """Treinar a cada bilhete seria caro (26 mil linhas). O cache é por dono, com TTL."""
    cenario["rotulos"] = [_bilhete() for _ in range(matcher.MIN_TREINO)]
    treinos = {"n": 0}
    real = matcher.treinar

    def _conta(linhas):
        treinos["n"] += 1
        return real(linhas)

    monkeypatch.setattr(matcher, "treinar", _conta)
    corpo = [{"id": "1", "casa": "Bet365", "esporte": "Futebol", "aposta": "Múltipla",
              "stake": "100,00", "descricao": "A // B"}]
    _post(corpo)
    _post(corpo)
    assert treinos["n"] == 1


# ── esporte praticamente exclusivo (s289) ───────────────────────────────────────
def test_esporte_exclusivo_decide_sozinho(cenario):
    """O caso Bad Milton: 44 apostas de Badminton na carteira, praticamente todas dele, e o
    matcher se calava porque um tipster que nunca fez Badminton ficava perto na log-odds.
    Aqui o treino inteiro aponta para Alfa e o domínio do esporte aponta para Beta — o domínio
    ganha, porque é evidência direta e não inferência."""
    cenario["rotulos"] = [_bilhete() for _ in range(matcher.MIN_TREINO)]
    cenario["dominio"] = {"badminton": ("Beta", 44, 44)}
    d = _post([{"id": "1", "casa": "Betboom", "esporte": "Badminton", "aposta": "ML",
                "stake": "300,00", "descricao": "x"}])
    assert d["sugestoes"] == {"1": "Beta"}


def test_esporte_exclusivo_vale_ate_sem_modelo(cenario):
    """Evidência direta não depende de treino: vale no dono que ainda cai no declarativo."""
    cenario["rotulos"] = []
    cenario["dominio"] = {"badminton": ("Beta", 44, 44)}
    d = _post([{"id": "1", "casa": "Betboom", "esporte": "Badminton", "aposta": "ML",
                "stake": "300,00", "descricao": "x"}])
    assert d["fonte"] == "declarativo"
    assert d["sugestoes"] == {"1": "Beta"}


def test_esporte_compartilhado_NAO_decide(cenario):
    """Contraprova — sem ela a regra passaria a cravar o maior de qualquer esporte. 44 de 60 é
    73 %: o esporte é dele, mas não SÓ dele."""
    cenario["rotulos"] = []
    cenario["dominio"] = {"badminton": ("Beta", 44, 60)}
    d = _post([{"id": "1", "casa": "Betboom", "esporte": "Badminton", "aposta": "ML",
                "stake": "300,00", "descricao": "x"}])
    assert d["sugestoes"] == {}


def test_esporte_exclusivo_mas_com_pouco_historico_NAO_decide(cenario):
    """Exclusividade com 5 bilhetes é coincidência, não padrão (MIN_ESPORTE)."""
    cenario["rotulos"] = []
    cenario["dominio"] = {"badminton": ("Beta", 5, 5)}
    d = _post([{"id": "1", "casa": "Betboom", "esporte": "Badminton", "aposta": "ML",
                "stake": "300,00", "descricao": "x"}])
    assert d["sugestoes"] == {}


def test_dono_do_esporte_arquivado_NAO_decide(cenario):
    cenario["rotulos"] = []
    cenario["ativos"] = ["Alfa"]
    cenario["dominio"] = {"badminton": ("Arquivado", 44, 44)}
    d = _post([{"id": "1", "casa": "Betboom", "esporte": "Badminton", "aposta": "ML",
                "stake": "300,00", "descricao": "x"}])
    assert d["sugestoes"] == {}


def test_casa_dedicada_ganha_do_esporte_exclusivo(cenario):
    """Curadoria humana explícita fica acima de qualquer evidência derivada."""
    cenario["rotulos"] = []
    cenario["dedicadas"] = {"betboom": ["Alfa"]}
    cenario["dominio"] = {"badminton": ("Beta", 44, 44)}
    d = _post([{"id": "1", "casa": "Betboom", "esporte": "Badminton", "aposta": "ML",
                "stake": "300,00", "descricao": "x"}])
    assert d["sugestoes"] == {"1": "Alfa"}


# ── s310: a rota abre a 2ª passada do declarado, mas não a executa ──────────────────────────
#
# A rota não decide quem o perfil declarado sugere — isso é do matcher declarativo, que vive no
# `index.html`. O que ela decide, e o que se trava aqui, são os DOIS CORTES: sobre QUEM ele pode
# falar (`novatos`) e com QUANTA folga (`folga_declarada`). Replicar esses números no front
# criaria dois valores para a mesma regra, divergindo em silêncio.

def test_novatos_lista_quem_a_base_mal_conhece(cenario):
    """Perfil com pouco rótulo entra; o que a base já conhece, não."""
    cenario["ativos"] = ["Alfa", "Beta"]
    # 300 no Alfa também mantém o treino acima de MIN_TREINO — senão a rota cai no
    # declarativo e a lista de novatos nem é montada.
    cenario["rotulos"] = ([_bilhete(tipster="Alfa")] * 300
                          + [_bilhete(tipster="Beta")] * 3)
    d = _post([{"id": "1", "casa": "Bet365", "esporte": "Futebol", "aposta": "Múltipla",
                "stake": "100,00", "descricao": "A // B"}])
    assert d["fonte"] == "evidencia"
    assert d["novatos"] == ["Beta"], "só quem a base mal viu abre espaço para o declarado"


def test_tipster_sem_nenhum_rotulo_e_novato(cenario):
    """O caso que mais importa: quem entrou esta semana e o modelo nem coloca na disputa."""
    cenario["ativos"] = ["Alfa", "Fusion"]
    cenario["rotulos"] = [_bilhete(tipster="Alfa")] * 300
    d = _post([{"id": "1", "casa": "Bet365", "esporte": "Futebol", "aposta": "Múltipla",
                "stake": "503,00", "descricao": "A // B"}])
    assert "Fusion" in d["novatos"]


def test_folga_declarada_vai_na_resposta(cenario):
    """A tela não pode ter um segundo número para a mesma regra."""
    cenario["rotulos"] = [_bilhete()] * 300
    d = _post([{"id": "1", "casa": "Bet365", "esporte": "Futebol", "aposta": "Múltipla",
                "stake": "100,00", "descricao": "A // B"}])
    assert d["folga_declarada"] == matcher.FOLGA_DECLARADA
    assert matcher.FOLGA_DECLARADA > 7, "a 2ª passada exige MAIS folga que o caminho principal"


def test_dono_no_declarativo_nao_recebe_novatos(cenario):
    """Base pequena já usa o declarativo como caminho PRINCIPAL — abrir a 2ª passada ali seria
    aplicá-lo duas vezes, uma delas com corte que não é dele."""
    cenario["rotulos"] = [_bilhete()] * 3
    d = _post([{"id": "1", "casa": "Bet365", "esporte": "Futebol", "aposta": "Múltipla",
                "stake": "100,00", "descricao": "A // B"}])
    assert d["fonte"] == "declarativo"
    assert d["novatos"] == []
