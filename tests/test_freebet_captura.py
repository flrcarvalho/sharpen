"""Gate da FREEBET capturada (s392, passo 2a) — o valor sai do bloco e chega à coluna.

`MASTER_RESULTADO §5.8` (decisão do Feca, 03/10/2026): freebet é dinheiro da casa, e o P/L
de uma aposta com freebet é `retorno − (stake − freebet)`. Este passo só GRAVA: nenhum número
do produto muda ainda (o `calcular_pl` é o passo 2b).

O caminho, e o gate de cada trecho:

1. `content.js` escreve o rótulo no bloco (já existia: Superbet, Betfair, BetConstruct,
   SportingBet) → o harness da extensão; aqui, só que os DOIS rótulos que o servidor lê
   continuam escritos no `content.js` (rótulo renomeado de um lado só = leitura vazia, sem
   erro nenhum).
2. `freebets_do_texto` lê do TEXTO CRU, pareado pelo `[Código: …]` → funções puras abaixo.
   Medido em 04/10/2026 contra os blocos reais da `sombra_rotulos` (com o marcador de código
   recolocado, que a sombra não guarda): 20 de 20 lidos, 0 falso positivo em 3.000 blocos
   sem freebet.
3. O `/extrair` devolve `freebets` nos três `done`; o front transporta ao `/salvar`; o
   `/salvar` passa ao `upsert_bilhetes` → presença no fonte.
4. `_freebet_da_linha` converte pela cotação da stake e recusa freebet maior que a stake →
   funções puras abaixo.
5. O UPSERT só PREENCHE a coluna (COALESCE), nos dois caminhos → leitura do SQL aqui; o
   Postgres de verdade em `tests/test_repository_db.py` (só no CI).

Mutações provadas, cada uma APLICADA ao código e com o teste ao lado vermelho (04/10/2026):
  1. procurar a freebet no texto inteiro, não no bloco do código
     → test_bloco_sem_freebet_nao_herda_a_do_vizinho
  2. aceitar dois valores diferentes no mesmo bloco → test_dois_valores_no_bloco_e_ambiguo
  3. tirar o teto `freebet ≤ stake` do leitor → test_freebet_maior_que_o_stake_e_recusada
  4. ler a Betbra (`aposta grátis (freebet)` sem a frase do saldo) como inteira
     → test_rotulo_sem_valor_e_sem_prova_de_inteira_nao_e_lido
  5. `_freebet_da_linha` sem multiplicar pela cotação → test_freebet_anda_pela_cotacao_da_stake
  6. `stake_freebet = EXCLUDED.stake_freebet` no ON CONFLICT → test_o_upsert_so_preenche

O QUE NÃO ESTÁ COBERTO: o `done` real do `/extrair` com IA (só a presença da chave no
fonte), e as casas que marcam freebet SEM valor (Betbra, BetBy) — ficam de fora de
propósito, no BACKLOG.
"""
import re
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

from repository import _freebet_da_linha, freebets_do_texto  # noqa: E402

REPO = (ROOT / "app" / "repository.py").read_text(encoding="utf-8")
MAIN = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
INDEX = (ROOT / "app" / "static" / "index.html").read_text(encoding="utf-8")
CONTENT = (ROOT / "extensor" / "content.js").read_text(encoding="utf-8")
DB = (ROOT / "app" / "database.py").read_text(encoding="utf-8")


def _bloco(codigo, stake, *extras):
    """Recorte do bloco REAL: `[Código:]`, `Stake:` e as linhas de marcação."""
    return "\n".join([f"[Código: {codigo}]", f"Stake: {stake}", "Status: Perdeu → L",
                      *extras, "Seleções:", "- Handicap: 1 (linha -0,75) [perdeu]"])


VALOR = "Freebet incluído: {} (dinheiro real = stake − freebet)"
SPB = "Marcação da casa: aposta grátis (freebet) — o stake não saiu do saldo"


# ── 2. o leitor ───────────────────────────────────────────────────────────────

def test_le_os_dois_rotulos_e_o_valor_de_cada_bilhete():
    texto = "\n\n".join([
        _bloco("306558902", "R$ 45,00", VALOR.format("45,00")),       # MyStake, inteira
        _bloco("890Y-QHQ8VF", "200,00", VALOR.format("10,00")),       # Superbet, parcial
        _bloco("20NWTMBZYW", "R$ 17,00", SPB),                         # SportingBet
    ])
    assert freebets_do_texto(texto) == {"306558902": "45,00", "890Y-QHQ8VF": "10,00",
                                        "20NWTMBZYW": "17,00"}


def test_bloco_sem_freebet_nao_herda_a_do_vizinho():
    """O par de controle da MyStake: mesmas pernas e mesma odd, só um deles é freebet."""
    texto = "\n\n".join([_bloco("306558885", "R$ 70,00"),
                         _bloco("306558902", "R$ 45,00", VALOR.format("45,00"))])
    assert freebets_do_texto(texto) == {"306558902": "45,00"}
    texto = "\n\n".join([_bloco("306558902", "R$ 45,00", VALOR.format("45,00")),
                         _bloco("306558885", "R$ 70,00")])
    assert freebets_do_texto(texto) == {"306558902": "45,00"}


def test_dois_valores_no_bloco_e_ambiguo():
    texto = _bloco("X1", "R$ 50,00", VALOR.format("10,00"), VALOR.format("20,00"))
    assert freebets_do_texto(texto) == {}


def test_freebet_maior_que_o_stake_e_recusada():
    assert freebets_do_texto(_bloco("X1", "R$ 10,00", VALOR.format("20,00"))) == {}
    assert freebets_do_texto(_bloco("X1", "R$ 20,00", VALOR.format("20,00"))) == {"X1": "20,00"}


def test_rotulo_sem_valor_e_sem_prova_de_inteira_nao_e_lido():
    """Betbra e BetBy marcam freebet sem dizer quanto: deduzir 'inteira' seria chute."""
    assert freebets_do_texto(_bloco("B1", "30,00", "Marcação da casa: aposta grátis (freebet)")) == {}
    assert freebets_do_texto(_bloco("J1", "30,00", "Freebet: sim (conferir regra de stake devolvida)")) == {}


def test_sem_marcador_de_codigo_nao_ha_o_que_parear():
    assert freebets_do_texto("Stake: 45,00\n" + VALOR.format("45,00")) == {}
    assert freebets_do_texto("") == {} and freebets_do_texto(None) == {}


def test_os_rotulos_que_o_servidor_le_continuam_escritos_na_extensao():
    """Rótulo renomeado de um lado só não dá erro: dá leitura vazia. Por isso o gate."""
    assert '"Freebet incluído: "' in CONTENT
    assert '"Marcação da casa: aposta grátis (freebet) — o stake não saiu do saldo"' in CONTENT


# ── 4. a linha que vai para a coluna ──────────────────────────────────────────

def test_freebet_em_reais_vai_como_decimal():
    assert _freebet_da_linha({"stake": "45,00"}, "306558902", {"306558902": "45,00"}) == Decimal("45.00")


def test_freebet_anda_pela_cotacao_da_stake():
    """Conta em USDT: o `/salvar` já gravou stake em R$ (25 × 5,2 = 130). A freebet vai junto."""
    row = {"stake": "130,00", "stake_orig": 25.0, "cotacao": 5.2}
    assert _freebet_da_linha(row, "D1", {"D1": "10,00"}) == Decimal("52.00")


def test_linha_sem_freebet_sem_codigo_ou_freebet_maior_fica_nula():
    assert _freebet_da_linha({"stake": "70,00"}, "306558885", {"306558902": "45,00"}) is None
    assert _freebet_da_linha({"stake": "45,00"}, "", {"": "45,00"}) is None
    assert _freebet_da_linha({"stake": "45,00"}, "X", None) is None
    assert _freebet_da_linha({"stake": "10,00"}, "X", {"X": "45,00"}) is None


# ── 3 e 5. o transporte e a escrita ───────────────────────────────────────────

def test_os_tres_done_do_extrair_devolvem_as_freebets():
    assert MAIN.count("'freebets': freebets_do_texto(texto)") == 2
    assert MAIN.count('"freebets": freebets_do_texto(texto)') == 1


def test_o_salvar_recebe_e_repassa_as_freebets():
    assert re.search(r"^\s+freebets: Optional\[dict\] = None", MAIN, re.MULTILINE)
    assert "freebets=body.freebets" in MAIN


def test_o_front_transporta_as_freebets_ao_salvar():
    assert "freebets: data.freebets || null" in INDEX


def test_a_coluna_existe_em_reais():
    assert "ALTER TABLE bilhetes ADD COLUMN IF NOT EXISTS stake_freebet NUMERIC(14,2);" in DB


def test_o_upsert_so_preenche():
    """A parte da casa não muda depois de feita: só PREENCHE, nos dois caminhos do UPSERT.
    Sobrescrever deixaria uma recaptura sem a marca (extensão velha, print) APAGAR a freebet."""
    assert "stake_freebet    = COALESCE(bilhetes.stake_freebet, EXCLUDED.stake_freebet)," in REPO
    assert "stake_freebet    = COALESCE(stake_freebet, $23)," in REPO
    assert REPO.count("_freebet_da_linha(row, codigo, freebets),") == 2
    assert "moeda, stake_orig, cotacao, stake_freebet)" in REPO
