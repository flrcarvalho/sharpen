"""Cobrança do tipster (s348, Fatia 3) — o TIPO decide se o valor se arrasta.

Regra na voz do Feca: *"o número do mês anterior se arrasta se não for atualizado.
Lançamento variável não atualiza pro próximo mês."* São quatro tipos:

    mensalidade  → arrasta (é o mesmo valor todo mês)
    staking      → NÃO arrasta (o valor muda; "o usuário apenas imputa o valor")
    temporada    → paga de uma vez, cobre os meses seguintes até `ate`
    sem_cobranca → resolve o mês sem valor

E um quinto estado que não é tipo: **vazio**, "a definir". Ausência de resposta não
pode virar mensalidade, senão a tela preencheria sozinha o mês de um tipster cujo
tipo ninguém declarou.

A prova de COMPORTAMENTO roda em `tests/js/cobranca_tipster.mjs`, que executa as
funções RECORTADAS do `gestao.js` de produção. Este arquivo a invoca e depois a
prova por MUTAÇÃO — ver `test_mutacoes_sao_detectadas`.

O que NÃO está coberto aqui: o render da aba (o `<select>`, o botão "Repetir", o
selo) e a gravação em `/custos/tipster/cobranca`, cujo lado de servidor tem gate
próprio em `test_fornecedor_preco.py`.
"""
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
GESTAO = RAIZ / "app" / "static" / "dash" / "assets" / "js" / "charts" / "gestao.js"
MJS = RAIZ / "tests" / "js" / "cobranca_tipster.mjs"


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
def test_prova_por_execucao_da_cobranca():
    r = subprocess.run(["node", str(MJS)], capture_output=True, text=True,
                       encoding="utf-8", cwd=str(RAIZ))
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")


MUTACOES = [
    (
        "mensalidade deixa de arrastar",
        "  return _arrasta(_ctCobranca(nome)) ? _ctValor(nome,ymAnterior) : 0;",
        "  return 0;",
    ),
    (
        "TODO tipo passa a arrastar (o staking volta a repetir)",
        "  return _arrasta(_ctCobranca(nome)) ? _ctValor(nome,ymAnterior) : 0;",
        "  return _ctValor(nome,ymAnterior);",
    ),
    (
        "a regra compartilhada passa a deixar o staking arrastar",
        "const _ARRASTA={mensalidade:true,mensal:true};",
        "const _ARRASTA={mensalidade:true,mensal:true,staking:true};",
    ),
    (
        "a regra compartilhada para de reconhecer a mensalidade",
        "const _ARRASTA={mensalidade:true,mensal:true};",
        "const _ARRASTA={mensal:true};",
    ),
    (
        "temporada ignora o prazo e cobre para sempre",
        "    if(!ate||ym<=ate){",
        "    if(true){",
    ),
    (
        "temporada cobre mesmo sem pagamento anterior",
        "      if(meses.some(m=>m<ym&&_ctValor(nome,m)>0))return 'coberto';",
        "      return 'coberto';",
    ),
    (
        "sem_cobranca volta a contar como pendencia",
        "  if(tipo==='sem_cobranca')return 'sem_custo';",
        "",
    ),
    (
        "valor no mes deixa de confirmar a linha",
        "  if(_ctValor(nome,ym)>0)return 'confirmado';",
        "",
    ),
    (
        "repetiveis passa a contar quem ja esta resolvido",
        "  return (nomes||[]).filter(n=>_ctSituacao(n,ym)==='pendente'&&_ctSugestao(n,ym,ymAnterior)>0);",
        "  return (nomes||[]).filter(n=>_ctSugestao(n,ym,ymAnterior)>0);",
    ),
    (
        "o valor do tipster para de ler o decimal em virgula",
        "function _ctValor(nome,ym){\n  const v=((typeof ctData!=='undefined'&&ctData[nome])||{})[ym];\n  const n=parseFloat((v==null?'':v).toString().replace(/\\./g,'').replace(',','.'));",
        "function _ctValor(nome,ym){\n  const v=((typeof ctData!=='undefined'&&ctData[nome])||{})[ym];\n  const n=parseFloat((v==null?'':v).toString());",
    ),
]


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
@pytest.mark.parametrize("titulo,de,para", MUTACOES, ids=[m[0] for m in MUTACOES])
def test_mutacoes_sao_detectadas(tmp_path, titulo, de, para):
    """Quebra o gestao.js de propósito e exige que o .mjs fique VERMELHO.

    Verde sem esta prova não prova nada: um gate que não detecta a quebra é uma
    promessa falsa (CLAUDE.md, "Teste verde não é teste que detecta")."""
    src = GESTAO.read_text(encoding="utf-8")
    assert src.count(de) == 1, (
        f"a âncora da mutação «{titulo}» não é única no gestao.js "
        f"({src.count(de)} ocorrência(s)) — atualize a lista MUTACOES"
    )
    estragado = tmp_path / "gestao.js"
    estragado.write_text(src.replace(de, para, 1), encoding="utf-8")

    r = subprocess.run(["node", str(MJS)], capture_output=True, text=True,
                       encoding="utf-8", cwd=str(RAIZ),
                       env={**__import__("os").environ, "ALVO_GESTAO": str(estragado)})
    assert r.returncode != 0, (
        f"a mutação «{titulo}» passou despercebida — o gate não cobre esta regra.\n"
        + (r.stdout or "")
    )

# ── Lado do servidor: gravar o tipo ─────────────────────────────────────────

import asyncio
import json
from unittest.mock import patch

import repository


class _MetaConn:
    def __init__(self, meta=None):
        self.meta = meta or {}
        self.gravado = None

    def transaction(self):
        conn = self

        class _T:
            async def __aenter__(self_inner):
                return conn

            async def __aexit__(self_inner, *a):
                return False

        return _T()

    async def fetchval(self, sql, *a):
        return json.dumps(self.meta)

    async def execute(self, sql, *a):
        if "custo_tipster_meta" in sql:
            self.gravado = json.loads(a[1])
        return "OK"


class _MetaPool:
    def __init__(self, conn):
        self.conn = conn

    def acquire(self):
        conn = self.conn

        class _A:
            async def __aenter__(self_inner):
                return conn

            async def __aexit__(self_inner, *a):
                return False

        return _A()


def _salvar(conn, **kw):
    args = dict(dono="Feca", tipster="Só Chutes", cobranca="mensalidade", parametro="", ate="")
    args.update(kw)
    with patch.object(repository, "get_pool",
                      lambda: asyncio.sleep(0, result=_MetaPool(conn))):
        return asyncio.run(repository.salvar_cobranca_tipster(**args))


def test_grava_o_tipo_na_chave_do_tipster():
    conn = _MetaConn()
    _salvar(conn)
    assert conn.gravado["Só Chutes"]["cobranca"] == "mensalidade"


@pytest.mark.parametrize("ruim", ["mensal", "MENSALIDADE", "assinatura", "x"])
def test_cobranca_fora_da_lista_e_recusada(ruim):
    """Tipo livre viraria uma quinta regra que nada implementa — e a tela cairia no
    ramo do `else`, que é justamente o defeito do 'push da Pinnacle' no CLAUDE.md."""
    conn = _MetaConn()
    with pytest.raises(ValueError):
        _salvar(conn, cobranca=ruim)
    assert conn.gravado is None


def test_tipster_vazio_e_recusado():
    conn = _MetaConn()
    with pytest.raises(ValueError):
        _salvar(conn, tipster="   ")
    assert conn.gravado is None


def test_cobranca_vazia_apaga_a_chave_e_volta_a_a_definir():
    """Apagar é voltar a 'a definir', que é diferente de `sem_cobranca`: um é
    ausência de resposta, o outro é a resposta."""
    conn = _MetaConn({"Só Chutes": {"cobranca": "staking"}})
    _salvar(conn, cobranca="")
    assert "Só Chutes" not in conn.gravado


def test_ate_so_e_guardado_na_temporada():
    """`ate` numa mensalidade não significa nada e viraria dado morto que um leitor
    futuro tentaria interpretar."""
    conn = _MetaConn()
    _salvar(conn, cobranca="mensalidade", ate="2026-12")
    assert "ate" not in conn.gravado["Só Chutes"]
    conn2 = _MetaConn()
    _salvar(conn2, cobranca="temporada", ate="2026-12")
    assert conn2.gravado["Só Chutes"]["ate"] == "2026-12"


def test_renomear_tipster_move_o_tipo_junto():
    """Gate ESTRUTURAL, no mesmo espírito do `grep -n "_ou_bot"` do CLAUDE.md: o tipo
    mora na chave-NOME, então `renomear_tipster` tem de movê-lo junto com o custo.
    Deixar o tipo para trás faz o tipster voltar a 'a definir' e parar de arrastar a
    mensalidade, sem erro nenhum. O comportamento contra Postgres é do CI com banco;
    aqui se prova que a função não esqueceu o outro lugar."""
    src = (RAIZ / "app" / "repository.py").read_text(encoding="utf-8")
    i = src.index("async def renomear_tipster")
    corpo = src[i:src.index(chr(10) + "async def ", i + 10)]
    assert "custo_tipster_meta" in corpo, (
        "renomear_tipster não move mais o tipo de cobrança — o tipster renomeado "
        "voltaria a 'a definir' em silêncio"
    )
