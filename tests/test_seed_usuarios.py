"""Seed da tabela `usuarios` (Fase 1 / Deploy A do PLANO_MULTIUSUARIO_2026).

`auth.linhas_seed_usuarios()` é a montagem PURA das linhas que
`database.seed_usuarios()` insere com ON CONFLICT DO NOTHING. Um erro aqui
não quebra nada no Deploy A (a tabela ainda não é lida), mas envenena o
Deploy B: parent_owner errado = "ver como" quebrado; status != 'ativo' =
lockout dos usuários atuais; hash '' em vez de NULL = conta social marcada
como se tivesse senha local. Estes testes travam o contrato linha a linha.

Ordem das colunas (contrato com o INSERT em database.seed_usuarios):
    (username, senha_hash, status, role, parent_owner, planilha_url)
"""
import auth  # conftest põe app/ no sys.path


def _por_username() -> dict[str, tuple]:
    return {linha[0]: linha for linha in auth.linhas_seed_usuarios()}


def test_cobre_todos_os_usuarios_sem_extras():
    linhas = auth.linhas_seed_usuarios()
    assert len(linhas) == len(auth.USUARIOS)
    assert {l[0] for l in linhas} == set(auth.USUARIOS)


def test_todas_as_linhas_tem_6_colunas_e_status_ativo():
    for linha in auth.linhas_seed_usuarios():
        assert len(linha) == 6
        assert linha[2] == "ativo"          # usuários atuais nunca nascem pendentes


def test_feca_e_o_unico_admin():
    papeis = {u: linha[3] for u, linha in _por_username().items()}
    assert papeis["Feca"] == "admin"
    assert all(role == "user" for u, role in papeis.items() if u != "Feca")


def test_parent_owner_espelha_operadores():
    linhas = _por_username()
    assert linhas["Lava"][4] == "Feca"
    assert linhas["Primo"][4] == "Diogo"
    assert linhas["LavaFatuch"][4] == "Fatuch"
    # donos e solos: NULL (inclusive LavaPessoal, que NÃO é operador do Feca)
    for solo in ("Feca", "Diogo", "Fatuch", "Jonathan", "LavaPessoal", "SoChutes"):
        assert linhas[solo][4] is None


def test_hash_vazio_vira_null_nunca_string_vazia():
    # Nos testes as envs SENHA_*_HASH não existem → todo hash é '' → NULL.
    # '' e NULL divergem no Deploy B: NULL = "sem senha local" (conta só-social).
    for linha in auth.linhas_seed_usuarios():
        assert linha[1] is None or linha[1] != ""


def test_planilha_url_vazia_vira_null():
    # Env PLANILHA_LAVAFATUCH_URL ausente nos testes → NULL (fail-safe: Postgres).
    for linha in auth.linhas_seed_usuarios():
        assert linha[5] is None or linha[5] != ""
