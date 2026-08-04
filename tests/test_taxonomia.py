"""A taxonomia é PARSEADA dos MASTERs — quando o parse quebra, ele quebra em silêncio.

`app/taxonomia.py` lê os valores válidos de `Esporte` e `Aposta` direto do
`MASTER_ESPORTES §7` e do `MASTER_APOSTAS §3`, em vez de manter uma cópia no código. Isso
tira uma linha da regra de propagação do CLAUDE.md, mas cria um modo de falha novo:
renumerar a seção ou trocar a tabela por lista faz a extração devolver **lista vazia**, e
o sintoma no usuário é um menu sem opções — nenhum erro, nenhum log.

Estes testes são o gate que troca esse silêncio por CI vermelho: âncoras que o MASTER não
pode perder e um piso de tamanho. Categoria/esporte NOVO não quebra nada aqui (é só
crescer); o que quebra é o parse deixar de achar o que existe.
"""
import sys

from fastapi.testclient import TestClient

import taxonomia

sys.path.insert(0, "app")
import main  # noqa: E402
from auth import dono_efetivo  # noqa: E402

cliente = TestClient(main.app)


def test_esportes_tem_ancoras_e_piso():
    esp = taxonomia.esportes_canonicos()
    # Piso, não igualdade: esporte novo entra no MASTER sem quebrar o CI (Badminton entrou
    # na s2xx assim). O que este número pega é o parse voltando vazio ou quase.
    assert len(esp) >= 18, f"parse da §7 encolheu: {esp}"
    for ancora in ("Futebol", "Basquete", "Tênis", "Badminton", "eSoccer", "E-Sports"):
        assert ancora in esp, f"'{ancora}' sumiu da §7 do MASTER_ESPORTES"


def test_esportes_inclui_outro():
    # `Outro` é válido (MASTER_ESPORTES §3) mas não tem seção própria na §7 — é acrescentado
    # à mão no módulo. Se alguém tirar essa linha, o valor de fallback some do menu.
    assert "Outro" in taxonomia.esportes_canonicos()


def test_categorias_tem_ancoras_e_piso():
    cat = taxonomia.categorias_canonicas()
    assert len(cat) >= 25, f"parse da §3 encolheu: {cat}"
    for ancora in ("ML", "Handicap", "Escanteios", "Gols", "Player Props", "Outros"):
        assert ancora in cat, f"'{ancora}' sumiu da §3 do MASTER_APOSTAS"


def test_nao_vaza_cabecalho_nem_separador_da_tabela():
    # O parse lê a 1ª coluna de TODA linha de tabela da §3 — o cabeçalho ("Categoria") e o
    # separador ("---") são linhas de tabela também e apareceriam como categorias no menu.
    cat = taxonomia.categorias_canonicas()
    assert "Categoria" not in cat
    assert not [c for c in cat if set(c) <= {"-", ":"}]


def test_valores_limpos_e_sem_duplicata():
    for valores in (taxonomia.esportes_canonicos(), taxonomia.categorias_canonicas()):
        assert len(valores) == len(set(valores)), "valor duplicado na taxonomia"
        for v in valores:
            assert v == v.strip() and v, f"valor com espaço nas pontas ou vazio: {v!r}"
            assert "|" not in v and not v.startswith("#"), f"resto de markdown vazou: {v!r}"


def test_rota_devolve_as_duas_listas():
    """A rota é o que o menu consome — se ela mudar de forma, o front cai no `||[]` e o
    menu esvazia calado. Trava o formato: duas chaves, listas não-vazias."""
    main.app.dependency_overrides[dono_efetivo] = lambda: "Teste"
    try:
        r = cliente.get("/taxonomia")
    finally:
        main.app.dependency_overrides.pop(dono_efetivo, None)
    assert r.status_code == 200
    corpo = r.json()
    assert set(corpo) == {"esportes", "categorias"}
    assert "Futebol" in corpo["esportes"] and "ML" in corpo["categorias"]


def test_rota_exige_login():
    """Sem sessão não responde a taxonomia — mesma porta de todas as rotas de dados."""
    r = cliente.get("/taxonomia", follow_redirects=False)
    assert r.status_code != 200, "rota de dados respondendo sem autenticação"


def test_secao_errada_devolve_vazio_sem_explodir():
    # Garante que o recorte por número de seção não pega a seção vizinha por engano
    # (um `_secao(texto, "99")` inexistente tem que ser vazio, não o arquivo inteiro).
    assert taxonomia._secao("# 1. A\ntexto\n# 2. B\noutro\n", "99") == ""
    assert taxonomia._secao("# 1. A\ntexto\n# 2. B\noutro\n", "1").strip() == "texto"
