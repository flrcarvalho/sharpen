"""Gate do CARIMBO DE COLOCAÇÃO (`aposta_em`) — a identidade estável da bet365.

POR QUE ESTA COLUNA EXISTE: a bet365 não dá identidade estável. O `ID` do summary é da
VISÃO (últimas 24h vêm no namespace `D1`; 48h e Intervalo de Datas, no `D0`) e muda outra
vez quando a aposta resolve. Uma aposta gravada como ABERTA fica sem endereço: sabe-se
QUEM procurar (o código do comprovante) e não ONDE ele está. O `TP` é o mesmo nas duas
visões e é o campo pelo qual a casa FILTRA o histórico, então é com ele que se reencontra
a aposta na LISTA de resolvidas, sem abrir o detalhe de ninguém.

O que este arquivo cobre: `carimbos_do_texto` (o pareamento código → carimbo lido do TEXTO
CRU) e, por leitura do SQL, a política de escrita da coluna nos dois caminhos do UPSERT.

O QUE ELE NÃO COBRE, de propósito:
  • o lado da extensão (que o carimbo SAI no bloco, verbatim, e não sai quando é falso) —
    isso é do harness, `extensor/harness/casos/bet365.mjs` §6c, contra a fixture real;
  • o banco de verdade. As duas asserções de SQL são ESTRUTURAIS: leem o texto do
    `repository.py`. Exercitar o UPSERT exigiria Postgres, que aqui só existe no CI, e o
    que se quer travar são duas linhas específicas.

Mutações provadas — cada uma foi APLICADA ao código e o teste ao lado ficou vermelho:
  1. buscar o carimbo no texto inteiro em vez de dentro do bloco
     → test_bloco_sem_carimbo_nao_herda_o_do_vizinho
  2. rótulo casado por igualdade exata      → test_rotulo_pode_mudar_de_redacao
  3. aceitar carimbo de qualquer tamanho    → test_carimbo_de_tamanho_errado_e_ignorado
  4. `aposta_em = EXCLUDED.aposta_em` (sem COALESCE) no ON CONFLICT
     → test_o_upsert_so_preenche_o_carimbo_nunca_sobrescreve
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

from repository import carimbos_do_texto  # noqa: E402

ROTULO = "Carimbo (colocação · uso interno — NÃO usar como data):"


def _bloco(codigo: str, carimbo: str | None) -> str:
    """Recorte do bloco REAL que o `formatTicketB3` emite (fixture bet365.summary)."""
    linhas = [f"[Código: {codigo}]", "Data (colocação): 22/07/2026"]
    if carimbo:
        linhas.append(f"{ROTULO} {carimbo}")
    linhas += ["Stake: 96,00", "Status: Perdeu → L", "Odd: 4",
               "Seleções:", "  • São Paulo v Athletico Paranaense"]
    return "\n".join(linhas)


def test_pareia_cada_bilhete_com_o_seu_carimbo():
    texto = "\n\n".join([_bloco("JR8714690761I", "20260722233620"),
                         _bloco("YR5088082431I", "20260722150124")])
    assert carimbos_do_texto(texto) == {"JR8714690761I": "20260722233620",
                                        "YR5088082431I": "20260722150124"}


def test_bloco_sem_carimbo_nao_herda_o_do_vizinho():
    """A fronteira é o próximo `[Código: …]`, não o fim do texto.

    Sem ela, o bilhete do meio pega o carimbo do bilhete de BAIXO e o casamento manda o
    resultado de uma aposta para outra. Casamento errado não perde bilhete: CORROMPE, e
    o P/L fecha certo nas duas pontas porque os dois valores existem.
    """
    texto = "\n\n".join([_bloco("AAA111", "20260722233620"),
                         _bloco("BBB222", None),
                         _bloco("CCC333", "20260721223826")])
    assert carimbos_do_texto(texto) == {"AAA111": "20260722233620",
                                        "CCC333": "20260721223826"}


def test_rotulo_pode_mudar_de_redacao():
    """O rótulo é prosa dirigida à IA e vai mudar; o nome do campo e os 14 dígitos, não."""
    texto = "[Código: AAA111]\nCarimbo: 20260722233620\nStake: 10,00"
    assert carimbos_do_texto(texto) == {"AAA111": "20260722233620"}


def test_carimbo_de_tamanho_errado_e_ignorado():
    """17 dígitos é o `TP` cru do summary; 8 é data solta. A chave é de 14, e só.

    Aceitar outro tamanho faria a mesma aposta ter chave diferente conforme a fonte
    (`TP` do summary × `DA` do confirmation), que é o oposto do que a coluna existe para
    resolver.
    """
    for ruim in ("20260722233620000", "20260722", "2026072223362"):
        assert carimbos_do_texto(f"[Código: AAA111]\n{ROTULO} {ruim}\nStake: 10,00") == {}


def test_texto_sem_marcador_nao_inventa_nada():
    """Print, casa sem marcador, texto colado à mão: ausência viaja como ausência."""
    assert carimbos_do_texto("Stake: 10,00\nStatus: Perdeu → L") == {}
    assert carimbos_do_texto("") == {}
    assert carimbos_do_texto(None) == {}


def test_primeiro_carimbo_do_bloco_manda():
    """Bloco com duas linhas de carimbo (não deve acontecer) usa a primeira, sem estourar."""
    texto = (f"[Código: AAA111]\n{ROTULO} 20260722233620\n"
             f"{ROTULO} 20260101000000\nStake: 10,00")
    assert carimbos_do_texto(texto) == {"AAA111": "20260722233620"}


# ── Política de escrita: ESTRUTURAL (ver o cabeçalho) ─────────────────────────
_SQL = (ROOT / "app" / "repository.py").read_text(encoding="utf-8")


def test_o_upsert_so_preenche_o_carimbo_nunca_sobrescreve():
    """`COALESCE(bilhetes.aposta_em, EXCLUDED.aposta_em)`, nos DOIS caminhos de escrita.

    O instante em que uma aposta foi feita não muda, então recaptura de bilhete antigo
    vira backfill de graça — inclusive em linha já resolvida, sem violar o congelamento
    da extração por IA. E sobrescrever seria a porta para uma leitura ruim substituir uma
    chave boa.

    São DOIS caminhos porque o `upsert_bilhetes` tem o ON CONFLICT e, sob corrida, um
    UPDATE manual de fallback. Gate por LISTA e não por lembrança: foi olhar um caminho
    de cada vez que deixou o segundo argumento do INSERT da Caixa passar duas vezes.
    """
    assert "aposta_em        = COALESCE(bilhetes.aposta_em, EXCLUDED.aposta_em)" in _SQL, \
        "ON CONFLICT: o carimbo deixou de ser só-preenche"
    assert "aposta_em        = COALESCE(aposta_em, $19)" in _SQL, \
        "UPDATE de fallback (corrida entre dois /salvar): o carimbo deixou de ser só-preenche"


def test_o_insert_declara_a_coluna_e_o_placeholder():
    """Coluna na lista, `$22` nos VALUES e um 22º argumento. O asyncpg não converte tipo:
    argumento a mais ou a menos vira erro dentro do driver, antes de qualquer SQL rodar,
    e sai como 500 na rota."""
    insert = _SQL[_SQL.index("INSERT INTO bilhetes\n                        (dono"):]
    insert = insert[:insert.index("ON CONFLICT")]
    assert "aposta_em)" in insert
    assert "$22)" in insert
    assert re.search(r"VALUES \(\$1,.*\$19, \$20, \$21, \$22\)", insert, re.S)
