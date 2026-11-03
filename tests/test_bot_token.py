"""Token de serviço do bot de tipster (s273) — autorização e ESCOPO.

Antes disto o bot fazia login COMO o tipster, então cada tipster novo obrigava a
guardar a SENHA DELE numa env var do Railway. Agora é UM token de serviço mais o
header `X-Sharpen-Dono`, e a autorização por dono é um botão no /admin
(`bot_habilitado`).

Um mecanismo que permite escrever na base de terceiro é exatamente onde um teste
frouxo custa caro, então aqui o que se trava é o NÃO: cada condição do desenho
tem um teste que prova que a ausência dela FECHA a porta, e dois testes provam
que o token não alcança rota fora do escopo.

Tudo sem banco: os gates de identidade rodam antes de qualquer query (o stub de
`database` do conftest explodiria se fossem alcançados). O único teste que
chegaria ao DB é o do caminho feliz, e ele prova o que precisa provar — passou da
autenticação — pelo fato de NÃO receber 401.
"""
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, "app")
import auth  # noqa: E402
import main  # noqa: E402

cliente = TestClient(main.app)

TOKEN = "t" * 48          # o piso do app é 32 caracteres
DONO = "tipsterbot"
TSV = "01/08/2026\tFutebol\t\tBet365\tPadrão\tGols\tOver 2.5\t1,00\t1,90\t\tPT202608-1"


@pytest.fixture
def bot_ligado(monkeypatch):
    """Token configurado + um dono ativo e habilitado no cache de auth."""
    monkeypatch.setattr(auth, "_BOT_TOKEN", TOKEN)
    monkeypatch.setattr(auth, "_usuarios_cache", {
        DONO: {"username": DONO, "status": "ativo", "role": "user", "bot_habilitado": True},
        "suspenso": {"username": "suspenso", "status": "suspenso", "role": "user",
                     "bot_habilitado": True},
        "naohabilitado": {"username": "naohabilitado", "status": "ativo", "role": "user",
                          "bot_habilitado": False},
    })
    return TOKEN


def cab(token=TOKEN, dono=DONO):
    h = {"Authorization": f"Bearer {token}"}
    if dono is not None:
        h["X-Sharpen-Dono"] = dono
    return h


# ── dono_do_bot: a função de identidade, isolada ─────────────────────────────

class _Headers(dict):
    """Headers HTTP são case-INSENSITIVE, e é assim que o Starlette os entrega.
    Um dict comum aqui faria o teste falhar por 'Authorization' != 'authorization'
    e acusar o código de um defeito que é do teste."""
    def get(self, chave, padrao=None):
        for k, v in self.items():
            if k.lower() == chave.lower():
                return v
        return padrao


class _Req:
    """Request mínimo — só o que `dono_do_bot` lê."""
    def __init__(self, headers):
        self.headers = _Headers(headers)


def test_identidade_ok(bot_ligado):
    assert auth.dono_do_bot(_Req(cab())) == DONO


def test_token_errado_nao_autentica(bot_ligado):
    assert auth.dono_do_bot(_Req(cab(token="x" * 48))) is None


def test_token_certo_com_prefixo_errado_nao_autentica(bot_ligado):
    # sem "Bearer " o cabeçalho não é sequer olhado
    assert auth.dono_do_bot(_Req({"Authorization": TOKEN, "X-Sharpen-Dono": DONO})) is None


def test_sem_header_de_dono_nao_autentica(bot_ligado):
    """Token válido sozinho não diz em QUAL base escrever — e não se escolhe uma."""
    assert auth.dono_do_bot(_Req(cab(dono=None))) is None


def test_dono_inexistente_nao_autentica(bot_ligado):
    assert auth.dono_do_bot(_Req(cab(dono="ninguem"))) is None


def test_dono_suspenso_nao_autentica(bot_ligado):
    """Suspender no /admin corta o bot junto — o gate de 'ativo' vale para ele também."""
    assert auth.dono_do_bot(_Req(cab(dono="suspenso"))) is None


def test_dono_sem_botao_ligado_nao_autentica(bot_ligado):
    """Conta ATIVA não ganha escrita de robô de brinde: o flag é a autorização."""
    assert auth.dono_do_bot(_Req(cab(dono="naohabilitado"))) is None


def test_mecanismo_desligado_sem_env(monkeypatch):
    """Sem SHARPEN_BOT_TOKEN, nenhum header autentica nada (não abre porta por omissão)."""
    monkeypatch.setattr(auth, "_BOT_TOKEN", "")
    assert auth.dono_do_bot(_Req(cab())) is None


def test_token_vazio_no_header_nao_casa_com_env_vazia(monkeypatch):
    """Regressão: com o mecanismo desligado, 'Bearer ' vazio não pode virar match."""
    monkeypatch.setattr(auth, "_BOT_TOKEN", "")
    assert auth.dono_do_bot(_Req({"Authorization": "Bearer ", "X-Sharpen-Dono": DONO})) is None


# ── ESCOPO: onde o token entra e, principalmente, onde NÃO entra ─────────────

def test_rota_do_bot_aceita_o_token(bot_ligado):
    """A dependency está REALMENTE ligada em /salvar.

    Alcançar o stub de banco É a prova: sem autenticar, a requisição morreria em
    401 na porta e nunca chegaria a uma query. Este teste falharia tanto se o
    token fosse recusado (viraria 401) quanto se a rota tivesse ficado com a
    dependency antiga."""
    with pytest.raises(RuntimeError, match="DB indisponível"):
        cliente.post("/salvar", json={"tsv": TSV, "casa": "Bet365", "parceiro": "Padrão"},
                     headers=cab())


def test_rota_do_bot_sem_token_e_401():
    r = cliente.post("/salvar", json={"tsv": TSV, "casa": "Bet365", "parceiro": "Padrão"})
    assert r.status_code == 401


@pytest.mark.parametrize("metodo,rota,corpo", [
    ("get", "/admin/usuarios", None),
    ("post", "/admin/usuarios/alguem/aprovar", None),
    ("post", "/admin/usuarios/alguem/suspender", None),
    ("post", "/admin/usuarios/alguem/bot", {"habilitado": True}),
])
def test_token_do_bot_nao_alcanca_o_admin(bot_ligado, metodo, rota, corpo):
    """O token escreve bilhete, não administra o sistema. As rotas /admin seguem
    em `usuario_atual` (cookie), então o Bearer não é sequer considerado."""
    r = getattr(cliente, metodo)(rota, headers=cab(), **({"json": corpo} if corpo else {}))
    assert r.status_code == 401


@pytest.mark.parametrize("rota", ["/dashboard/data", "/exportar.csv", "/me"])
def test_token_do_bot_nao_le_a_base(bot_ligado, rota):
    """Escopo de ESCRITA: o token não serve para ler dado de ninguém."""
    assert cliente.get(rota, headers=cab()).status_code == 401


def test_dependencies_do_bot_sao_exatamente_as_esperadas():
    """Trava a superfície: se alguém aplicar `_ou_bot` numa rota nova, este teste
    quebra e obriga a decisão a ser consciente. É o grep virado gate."""
    import re
    fonte = open("app/main.py", encoding="utf-8").read()
    # linha da rota mais próxima acima de cada uso de `_ou_bot`
    usos = []
    linhas = fonte.split("\n")
    for i, l in enumerate(linhas):
        if "_ou_bot" in l and "Depends(" in l:
            for j in range(i, max(0, i - 6), -1):
                m = re.match(r'@app\.(get|post|patch|delete|put)\("([^"]+)"', linhas[j].strip())
                if m:
                    usos.append(f"{m.group(1).upper()} {m.group(2)}")
                    break
    assert sorted(set(usos)) == sorted([
        "POST /salvar",
        "POST /bilhetes/tipster",
        "PATCH /bilhetes/{bilhete_id}",
        "DELETE /bilhetes",
    ]), f"superfície do token mudou: {sorted(set(usos))}"


# ── D44 item 3 (Feca, 03/11/2026): de onde veio a edição ────────────────────
# "Bot dos tipsters: grava origem 'bot', mas conta como correção HUMANA." O PATCH é o mesmo da
# grade; quem decide a origem é a identidade que passou pela porta. Mutações provadas:
#   B1 rastro sempre None (o bot sem origem)          → test_patch_do_bot_grava_origem_bot
#   B2 rastro sempre 'bot' (a grade vira bot)          → test_patch_da_grade_segue_sem_origem
#   B3 'bot' entra em ORIGENS_DE_ROBO                  → test_so_ficha_conferir_e_resolver_sao_robo
#   B4 'resolver' sai de ORIGENS_DE_ROBO               → test_so_ficha_conferir_e_resolver_sao_robo
# Não cobre: a gravação em `correcoes` (é o `atualizar_bilhete`, coberto no harness de banco).

def _patch_capturando(monkeypatch):
    from unittest.mock import AsyncMock
    pego = {}

    async def falso(bid, campos, dono, rastro=None):
        pego.update(bid=bid, dono=dono, rastro=rastro)
        return True
    monkeypatch.setattr(main, "atualizar_bilhete", falso)
    monkeypatch.setattr(main, "flags_pos_edicao", AsyncMock(return_value={}))
    return pego


def test_patch_do_bot_grava_origem_bot(bot_ligado, monkeypatch):
    pego = _patch_capturando(monkeypatch)
    r = cliente.patch("/bilhetes/7", json={"odd": "1,95"}, headers=cab())
    assert r.status_code == 200, r.text
    assert pego == {"bid": 7, "dono": DONO, "rastro": "bot"}


def test_patch_da_grade_segue_sem_origem(bot_ligado, monkeypatch):
    """Sessão de navegador = a mão do dono: NULL, como sempre foi."""
    pego = _patch_capturando(monkeypatch)
    monkeypatch.setattr(auth, "impressao_senha", lambda u: "")
    c = TestClient(main.app, base_url="https://www.sharpen.bet")
    c.cookies.set(auth.COOKIE_NAME, auth.criar_token(DONO))
    r = c.patch("/bilhetes/7", json={"odd": "1,95"},
                headers={"Origin": "https://www.sharpen.bet"})
    assert r.status_code == 200, r.text
    assert pego == {"bid": 7, "dono": DONO, "rastro": None}


def test_so_ficha_conferir_e_resolver_sao_robo():
    """"Robô = só ficha, conferir e resolver. Qualquer outra origem, ou NULL, é humana.\""""
    import repository
    assert sorted(repository.ORIGENS_DE_ROBO) == ["conferir", "ficha", "resolver"]
    assert repository.ORIGEM_BOT == "bot" and "bot" not in repository.ORIGENS_DE_ROBO
