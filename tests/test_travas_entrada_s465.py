"""Travas de entrada (s465, E1.1 do plano do marco zero, 22/11/2026): `app/travas_entrada.py`.

1. **D51 (Feca, 22/11/2026): aposta colocada há mais de 12 meses não entra no Sharpen**, nos
   dois caminhos: o texto do `/extrair` (o bloco sai antes do pré-dedup, da Ficha e da IA) e a
   rota do cru (`virada.aplicar`: a Ficha não grava).
2. **Sportsbet.io em moeda sem escala medida** (BRL): o bloco sai antes da IA. O inject divide
   toda moeda por 1e8, e a conta em real virava `Stake: 0,01` (risco R45).

Os blocos SBI abaixo são o texto REAL que a extensão manda: gerados pelo `sbi_inject.js` e pelo
`formatTicketSBI` de verdade (sandbox do harness) sobre os crus de produção de 22/11/2026 (o BRL
de 2023 e o USDC do Jonathan, um USDT do Feca), sem nenhuma edição. O replay de 30 dias que
autorizou as duas travas (9.256 crus, só leitura) está no parecer da s465: a de moeda barra
só os 185 BRL do Jonathan; a de idade, esses 185 e 52 da Stake.com (Jonathan e Gabriel, de
nov-dez/2024).

O que estes testes travam:
- a régua de data (colocação primeiro; sem ela a mais recente das outras; sem nenhuma, FICA) e
  o limite (mesmo dia, um ano atrás);
- a de moeda (sem `Moeda:` = real; a lista é a do adaptador, não uma cópia);
- o recorte no `main` (só bloco com `[Código:]`, texto intacto sem barrado);
- os códigos barrados entram no `no_texto` da virada (sem isso viram aviso falso de "não lida")
  e as contagens chegam ao `virada_log` (`fora_idade`, `fora_moeda`), à tela e aos Logs;
- a régua na rota do cru: Ficha aceita e velha fica `barrada`, não grava e sai do lote;
- `marcar_barradas` tira o aviso e grava um estado que não é `ia`.

O que NÃO cobrem: o SQL de verdade (o banco é dublado; o `virada_log` só tem a forma do INSERT
conferida, colunas × parâmetros), a tela (só as frases no `index.html`) e a Ficha RECUSADA velha
que o texto não trouxe (sem data no cru recusado, a rota do cru não a julga; o caso só existe
quando a janela do robô corta, BACKLOG).

Mutações: listadas no parecer da s465 (`mut_travas.json` no scratchpad da sessão).
"""
import asyncio
import json
import os
import pathlib
import re
import sys
from datetime import date

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-nao-usada")
sys.path.insert(0, "app")

import database  # noqa: E402  (stub do conftest)
if not hasattr(database, "init_db"):
    async def _init_db():  # pragma: no cover
        raise RuntimeError("DB indisponível nos testes")
    database.init_db = _init_db

import pytest  # noqa: E402

import main  # noqa: E402
import travas_entrada as T  # noqa: E402
import virada  # noqa: E402
import ficha  # noqa: E402
from adaptadores import sbi  # noqa: E402

HOJE = date(2026, 11, 22)
RAIZ = pathlib.Path(__file__).resolve().parent.parent

BRL_2023 = (
    "[Código: 643ee33d1e4b050001838d82]\nData (evento mais recente): 18/04/2023 16:00:00\n"
    "Data (colocação): 18/04/2023 15:36:45\nStake: 0,01\nStatus: Perdeu → L\n"
    "Status (API): status=ARCHIVED · betType=0\nTipo: Simples\nOdd: 5\nSeleções:\n"
    "- Real Madrid e Napoli classificarem (máx. R$10): Sim [perna perdida]\n"
    "    Jogo: Super Especial - UEFA Champions League · Esporte: sportsbet-specials · "
    "Início: 18/04/2023 16:00:00")
USDC_NOV = (
    "[Código: 6b00a129044677000143a295]\nData (evento mais recente): 20/11/2026 17:00:00\n"
    "Data (colocação): 20/11/2026 16:36:08\nCarimbo de colocação: 20261120163608\n"
    "Stake: 45,4616\nMoeda: USDC\nStatus: Ganhou → W (retorno 95,46936 USDC)\n"
    "Status (API): status=ARCHIVED · betType=0\nTipo: Simples\nOdd: 2,1\nSeleções:\n"
    "- Vencedor (inc. prorrogação): UP Mexico [perna ganha]\n"
    "    Jogo: UP Mexico - Universidad Montrer · Esporte: basketball · Início: 20/11/2026 17:00:00")
USDT_NOV = (
    "[Código: 6b01d283044677000132cb9f]\nData (evento mais recente): 21/11/2026 14:30:00\n"
    "Data (colocação): 21/11/2026 14:18:59\nCarimbo de colocação: 20261121141859\n"
    "Stake: 40,00\nMoeda: USDT\nStatus: Perdeu → L\n"
    "Status (API): status=ARCHIVED · betType=1 · TURBINADO\nTipo: Múltipla (3 seleções)\n"
    "Odd: 11,51\nSeleções:\n- Total (incluindo prorrogação): Menos de 172.5 [perna perdida]")
# A mesma conta em real, aposta RECENTE: a trava de moeda tem de barrar sozinha.
BRL_NOV = BRL_2023.replace("643ee33d1e4b050001838d82", "6b0000000000000000000bb1") \
    .replace("18/04/2023", "21/11/2026")


# ── 1. a régua de data ─────────────────────────────────────────────────────────

LIQ = "Status: Perdeu → L"                                   # o veredito, como os formatadores escrevem
ABERTA = "Status: em aberto (aguardando resultado — NÃO liquidar; sem resultado)"


def test_limite_e_o_mesmo_dia_um_ano_atras():
    assert T.limite(HOJE) == date(2025, 11, 22)
    assert T.limite(date(2028, 2, 29)) == date(2027, 2, 28)
    entra = f"[Código: 1]\nData (colocação): 22/11/2025 00:00:01\nStake: 1\n{LIQ}"
    sai = f"[Código: 1]\nData (colocação): 21/11/2025 23:59:59\nStake: 1\n{LIQ}"
    assert not T.bloco_velho(entra, HOJE)
    assert T.bloco_velho(sai, HOJE)


def test_aberta_colocada_ha_13_meses_entra():
    """D51 refinada (Feca, 22/11/2026): aberta entra sempre, de qualquer data. Aposta de longo
    prazo colocada há 13 meses, ainda sem resultado, é dinheiro que está na mesa."""
    b = f"[Código: 1]\nData (evento): 20/10/2025\nData (colocação): 01/10/2025 10:00:00\n{ABERTA}"
    assert not T.bloco_finalizado(b)
    assert not T.bloco_velho(b, HOJE)


def test_finalizada_colocada_ha_14_meses_e_liquidada_ha_1_mes_entra():
    """A data é a MAIS RECENTE do bloco: ela mexeu no dinheiro dentro da janela."""
    b = (f"[Código: 1]\nData (evento mais recente): 25/09/2025 18:00:00\n"
         f"Data (colocação): 20/09/2025 10:00:00\n{LIQ}\nLiquidado em: 22/10/2026 09:00:00")
    assert T.data_do_bloco(b) == date(2026, 10, 22)
    assert not T.bloco_velho(b, HOJE)
    assert T.bloco_velho(b.replace("Liquidado em: 22/10/2026", "Liquidado em: 26/09/2025"), HOJE)


@pytest.mark.parametrize("linha", ["Colocada: 20/11/2026 10:00:00", "Apostado em: 20/11/2026",
                                   "Liquidada em: 20/11/2026 10:00:00", "Data: 20/11/2026"])
def test_toda_grafia_de_data_conta(linha):
    """1xBet e espelhos escrevem `Colocada:`; a Pinnacle, `Apostado em:`; a Betano, `Data:`; a
    1win e outras, `Liquidado em:`. Qualquer uma recente segura o bloco."""
    b = f"[Código: 1]\nData (evento): 01/01/2024\n{linha}\n{LIQ}"
    assert not T.bloco_velho(b, HOJE)
    assert T.bloco_velho(f"[Código: 1]\nData (evento): 01/01/2024\n{LIQ}", HOJE)


def test_sem_veredito_fica():
    """Superbet (status cru `lost`) e Bet365 na meia sem rótulo: sem `→ X`, fail-open."""
    assert not T.bloco_velho("[Código: 1]\nData: 01/01/2024\nStatus: lost · retorno R$ 0,00", HOJE)
    assert not T.bloco_velho("[Código: 1]\nData (evento): 01/01/2024\nStatus: Ganho/perda parcial "
                             "(retorno R$ 90,00 · a conferir HW/HL)", HOJE)


def test_bloco_sem_data_legivel_fica():
    assert T.data_do_bloco(f"[Código: 1]\nStake: 10,00\nOdd: 2\n{LIQ}") is None
    assert not T.bloco_velho(f"[Código: 1]\nStake: 10,00\n{LIQ}", HOJE)
    assert not T.bloco_velho(f"[Código: 1]\nData (colocação): 31/02/2020\n{LIQ}", HOJE)


# ── 2. a régua de moeda ────────────────────────────────────────────────────────

def test_moeda_sbi_com_os_blocos_reais():
    assert T.bloco_moeda_fora("SPORTSBETIO", BRL_NOV)          # sem `Moeda:` = real
    assert not T.bloco_moeda_fora("SPORTSBETIO", USDT_NOV)
    assert not T.bloco_moeda_fora("SPORTSBETIO", USDC_NOV)
    assert T.bloco_moeda_fora("SPORTSBETIO", USDT_NOV.replace("Moeda: USDT", "Moeda: EUR"))


def test_moeda_so_vale_na_sportsbetio():
    """Casa em real não escreve `Moeda:`; barrar a falta da linha fora da Sportsbet.io
    tiraria todo bilhete do Brasil."""
    assert not T.bloco_moeda_fora("STAKECOM", BRL_NOV)
    assert not T.bloco_moeda_fora("BET365", "[Código: BR1]\nStake: 10,00")


def test_a_lista_de_moedas_e_a_do_adaptador(monkeypatch):
    monkeypatch.setattr(sbi, "_MOEDAS_MEDIDAS", {"USDT"})
    assert T.bloco_moeda_fora("SPORTSBETIO", USDC_NOV)


def test_idade_vem_antes_da_moeda():
    assert T.motivo_do_bloco("SPORTSBETIO", BRL_2023, HOJE) == T.IDADE
    # o BRL de 2023 ainda em aberto: a idade não o pega, a moeda sim
    assert T.motivo_do_bloco("SPORTSBETIO", BRL_2023.replace("Status: Perdeu → L", ABERTA),
                             HOJE) == T.MOEDA
    assert T.motivo_do_bloco("SPORTSBETIO", BRL_NOV, HOJE) == T.MOEDA
    assert T.motivo_do_bloco("SPORTSBETIO", USDT_NOV, HOJE) is None


# ── 3. o recorte do `/extrair` ─────────────────────────────────────────────────

def test_recorte_tira_os_barrados_e_conta():
    texto = "\n\n".join([USDT_NOV, BRL_2023, USDC_NOV, BRL_NOV])
    saida, barrados, n = main._travas_de_entrada(texto, "SPORTSBETIO", hoje=HOJE)
    assert barrados == {"643ee33d1e4b050001838d82": T.IDADE, "6b0000000000000000000bb1": T.MOEDA}
    assert n == {T.IDADE: 1, T.MOEDA: 1}
    assert "6b01d283044677000132cb9f" in saida and "6b00a129044677000143a295" in saida
    assert "643ee33d" not in saida and "6b0000000000000000000bb1" not in saida


def test_recorte_sem_barrado_devolve_o_texto_intacto():
    texto = USDT_NOV + "\n\n\n" + USDC_NOV
    assert main._travas_de_entrada(texto, "SPORTSBETIO", hoje=HOJE) == (texto, {}, {})


def test_texto_sem_codigo_nunca_e_cortado():
    """Texto colado à mão vira um bloco só; uma linha `Data:` velha nele não pode cortar a
    colagem inteira."""
    colado = ("Minhas apostas\nData: 01/01/2020\nStake: 10\nOdd: 2\nStatus: Perdeu → L\n\n"
              "Data: 02/01/2020\nStake: 5")
    assert T.bloco_velho(colado, HOJE), "o dado tem de ser velho, senão o teste não exerce a regra"
    assert main._travas_de_entrada(colado, "BET365", hoje=HOJE) == (colado, {}, {})


# ── 4. a virada: `no_texto` e `virada_log` ─────────────────────────────────────

def _dedup(monkeypatch, texto, barrados, fora, velhas_ficha=()):
    visto, pendentes = {}, []

    async def _resolver(dono, casa_key, casa, parceiro, codigos, iguais, **kw):
        visto["no_texto"] = list(kw.get("no_texto") or [])
        if velhas_ficha and kw.get("info") is not None:
            kw["info"]["velhas_ficha"] = set(velhas_ficha)
        return set(), 0.0, {}, set()

    async def _registrar(*a, **kw):
        visto["registrar"] = (a, kw)

    async def _vazio(*a, **k):
        return set()

    async def _nenhum(*a, **k):
        return {}

    monkeypatch.setattr(virada, "virada", lambda k: True)
    monkeypatch.setattr(virada, "resolver_no_extrair", _resolver)
    monkeypatch.setattr(virada, "registrar", _registrar)
    monkeypatch.setattr(virada, "vigia_por_dia", lambda: 0)
    monkeypatch.setattr(main, "get_codigos_resolvidos", _vazio)
    monkeypatch.setattr(main, "codigos_excluidos_de_vez", _vazio)
    monkeypatch.setattr(main, "blocos_conhecidos", _nenhum)
    monkeypatch.setattr(main, "_fire", pendentes.append)
    info = {}
    saida, _ = asyncio.run(main._dedup_superbet_text(
        texto, "Jonathan", "Sportsbet.io", "Pessoal [Pessoal]", casa_key="SPORTSBETIO",
        info=info, barrados=barrados, fora_travas=fora))
    for coro in pendentes:
        asyncio.run(coro)
    return saida, visto, info


def test_barrado_entra_no_no_texto_e_no_virada_log(monkeypatch):
    texto, barrados, n = main._travas_de_entrada(
        "\n\n".join([USDT_NOV, BRL_2023, BRL_NOV]), "SPORTSBETIO", hoje=HOJE)
    _, visto, _ = _dedup(monkeypatch, texto, barrados, n)
    assert set(visto["no_texto"]) == {"6b01d283044677000132cb9f", "643ee33d1e4b050001838d82",
                                     "6b0000000000000000000bb1"}
    assert visto["registrar"][1]["fora_travas"] == {T.IDADE: 1, T.MOEDA: 1}


def test_ficha_velha_da_rota_sai_do_lote_e_conta(monkeypatch):
    """Texto sem data legível, cru com ela: a `aplicar` barra e o `/extrair` não a manda à IA."""
    cod = "6b01d283044677000132cb9f"
    saida, visto, info = _dedup(monkeypatch, USDT_NOV, {}, {}, velhas_ficha=[cod])
    assert cod not in saida
    assert visto["registrar"][1]["fora_travas"] == {T.IDADE: 1}
    assert info["velhas_ficha_n"] == 1


# ── 5. a rota do cru: `aplicar` não grava a Ficha velha ────────────────────────

CRUS_USDC = json.loads((RAIZ / "tests" / "fixtures" / "sbi_usdc_s465.json").read_text(encoding="utf-8"))


def _cru_sbi(cod, colocada="1681832205", inicio="1681833600", aberta=False):
    """Um cru real da fixture (o W de 45,4616), com as datas trocadas. Padrão: 18/04/2023, a
    data do BRL de 2023. `aberta` = o mesmo bilhete ainda sem resultado (`ACTIVE`)."""
    c = json.loads(json.dumps(CRUS_USDC[2]))
    c["id"] = cod
    c["placedAt"] = colocada
    for s in c["bets"][0]["selections"]:
        s["eventStartTime"] = inicio
        if aberta:
            s["status"] = "0"
    if aberta:
        c["status"], c["wonAmount"] = "ACTIVE", None
    f, m = ficha.montar_ficha("sbi", c, "SPORTSBETIO")
    assert m == [], m
    return f


def test_aplicar_barra_a_ficha_velha(monkeypatch):
    f_rec = ficha.montar_ficha("sbi", CRUS_USDC[2], "SPORTSBETIO")[0]
    f_vel = _cru_sbi("velho")
    f_vab = _cru_sbi("velho_aberto", aberta=True)
    gravados, estados = [], {}

    async def _set(*a, **k):
        return set()

    async def _termos(*a, **k):
        return {}

    async def _estados(conn, dono, ck, novo):
        estados.update(novo)

    async def _gravar(dono, casa, parceiro, itens):
        gravados.extend(f["codigo"] for f, *_ in itens)
        return {}

    class _Conn:
        async def fetch(self, *a, **k):
            return []

    monkeypatch.setattr(T, "hoje_brasilia", lambda: HOJE)
    monkeypatch.setattr(virada, "_liquidados", _set)
    monkeypatch.setattr(virada, "_no_banco", _set)
    monkeypatch.setattr(virada._dic, "carregar", _termos)
    monkeypatch.setattr(virada._dic, "traduzir", lambda f, t: ("Basquete", "Simples", []))
    monkeypatch.setattr(virada, "no_master", lambda e, c: True)
    monkeypatch.setattr(virada, "descricao_para_gravar", lambda f, t: "desc")
    monkeypatch.setattr(virada._desc, "montar", lambda *a, **k: ("desc", []))
    monkeypatch.setattr(virada, "_gravar_estados", _estados)
    monkeypatch.setattr(virada, "gravar_na_planilha", _gravar)
    velhas: set = set()
    resolvidos, fica = asyncio.run(virada.aplicar(
        _Conn(), "Jonathan", "SPORTSBETIO", "Sportsbet.io", "c",
        {f["codigo"]: (f, []) for f in (f_rec, f_vel, f_vab)}, velhas))
    assert sorted(gravados) == sorted([f_rec["codigo"], f_vab["codigo"]]), \
        "a recente grava, e a ABERTA de 2023 também (D51: aberta entra sempre)"
    assert velhas == {f_vel["codigo"]} and f_vel["codigo"] not in fica
    assert estados[f_vel["codigo"]][1:] == (virada.BARRADA, T.IDADE)


def test_ficha_velha_regua():
    assert T.ficha_finalizada(_cru_sbi("v"))
    assert T.ficha_velha(_cru_sbi("v"), HOJE)
    assert not T.ficha_velha(_cru_sbi("a", aberta=True), HOJE), "aberta entra sempre"
    # colocada há 14 meses, perna que começou há 1 mês: a mais recente segura a aposta
    assert not T.ficha_velha(_cru_sbi("p", colocada="1758362400", inicio="1792764000"), HOJE)
    assert not T.ficha_velha({"colocada_em": "2023-01-01T00:00:00Z", "status": "ganha"}, HOJE), \
        "Ficha que não deriva não prova nada: entra"
    assert not T.ficha_velha(None, HOJE)


# ── 6. o banco (dublado): `marcar_barradas` e a forma do INSERT do `virada_log` ────

class _Pool:
    def __init__(self):
        self.sql = []

    def acquire(self):
        pool = self

        class _Ctx:
            async def __aenter__(self):
                class _C:
                    async def execute(self, sql, *args):
                        pool.sql.append((sql, args))
                return _C()

            async def __aexit__(self, *a):
                return False
        return _Ctx()


def test_marcar_barradas_tira_o_aviso_e_nao_e_ia(monkeypatch):
    pool = _Pool()

    async def _p():
        return pool
    monkeypatch.setattr(virada, "_pool_conn", _p)
    monkeypatch.setattr(virada, "virada", lambda k: True)
    asyncio.run(virada.marcar_barradas("Jonathan", "sportsbetio", {"643ee": T.IDADE}))
    (sql, args), = pool.sql
    assert args[2:] == ("643ee", virada.BARRADA, T.IDADE) and args[1] == "SPORTSBETIO"
    assert virada.BARRADA != "ia"
    assert "aviso = NULL" in sql and "pendente_desde = NULL" in sql


def test_insert_do_virada_log_fecha_colunas_e_parametros(monkeypatch):
    pool = _Pool()

    async def _p():
        return pool
    monkeypatch.setattr(virada, "_pool_conn", _p)
    asyncio.run(virada.registrar("Jonathan", "SPORTSBETIO", 5, 0, 0, 0, 5,
                                 fora_travas={T.IDADE: 185, T.MOEDA: 2}))
    (sql, args), = pool.sql
    colunas = re.search(r"\((.*?)\)\s*VALUES", sql, re.S).group(1).split(",")
    marcas = re.findall(r"\$\d+", sql)
    assert len(colunas) == len(marcas) == len(args)
    assert [c.strip() for c in colunas[-2:]] == ["fora_idade", "fora_moeda"]
    assert args[-2:] == (185, 2)


def test_check_da_ficha_virada_aceita_barrada():
    """`ficha_virada.estado` nasceu com CHECK de dois estados (`ficha`, `ia`). Sem trocá-lo, o
    INSERT de `barrada` levanta: na `aplicar` ele derrubava a gravação dos estados das Fichas já
    gravadas (a rota devolvia 0 e o `/extrair` mandava tudo à IA) e o `marcar_barradas` falhava
    sempre, em silêncio (revisão da consultoria, s465). O banco NOVO (CREATE) e o que JÁ EXISTE
    (DO, só quando o CHECK não tem `barrada`) precisam dos três. Provado num Postgres real na
    s465: no CHECK antigo o INSERT dá CheckViolation; migrado, entra, e o 2º boot não muda nada."""
    src = (RAIZ / "app" / "database.py").read_text(encoding="utf-8")
    ini = src.index("CREATE TABLE IF NOT EXISTS ficha_virada (")
    assert "CHECK (estado IN ('ficha', 'ia', 'barrada'))" in src[ini:src.index(");", ini)]
    do = src[src.index("-- s465: `barrada`"):]
    do = do[:do.index("END$$;")]
    assert "pg_get_constraintdef(oid) LIKE '%barrada%'" in do
    assert "DROP CONSTRAINT IF EXISTS ficha_virada_estado_check" in do
    assert "ADD CONSTRAINT ficha_virada_estado_check\n            CHECK (estado IN ('ficha', 'ia', 'barrada'))" in do
    assert f"'{virada.BARRADA}'" in do


def test_migracao_idempotente_das_colunas():
    src = (RAIZ / "app" / "database.py").read_text(encoding="utf-8")
    for col in ("fora_idade", "fora_moeda"):
        assert f"ALTER TABLE virada_log ADD COLUMN IF NOT EXISTS {col} INTEGER NOT NULL DEFAULT 0" in src


# ── 7. a contagem chega à tela e aos Logs ──────────────────────────────────────

def test_done_leva_as_contagens_e_o_aviso_de_moeda(monkeypatch):
    capt = {}

    async def _reg(*a, **kw):
        capt.update(kw)
        return 7
    monkeypatch.setattr(main, "registrar_extracao", _reg)

    async def _fluxo():
        yield f"data: {json.dumps({'done': True, 'resultado': '', 'modelo': 'm'})}\n\n"

    async def _rodar():
        contagem = {"fora_travas": {T.IDADE: 185, T.MOEDA: 2},
                    "motivos": {T.IDADE: 185, T.MOEDA: 2}}
        return [ev async for ev in main._com_log(_fluxo(), "J", "Sportsbet.io", "c", contagem, 0.0)]
    ev, = asyncio.run(_rodar())
    d = json.loads(ev[6:])
    assert (d["fora_idade"], d["fora_moeda"], d["log_id"]) == (185, 2, 7)
    assert any("conta de real" in a for a in capt["avisos"])
    assert capt["motivos"] == {T.IDADE: 185, T.MOEDA: 2}


def test_extrair_liga_as_travas_na_ordem():
    """O `/extrair` não se roda aqui (multipart, IA, banco); a ligação é conferida no código:
    travas depois do corte histórico e ANTES do pré-dedup, a marca na virada logo em seguida,
    os barrados indo ao pré-dedup e a contagem ao `done`."""
    import inspect
    src = inspect.getsource(main.extrair)
    i_corte = src.index("_corte_historico_text(texto")
    i_trava = src.index("_travas_de_entrada(texto, casa_key)")
    i_marca = src.index("marcar_barradas(dono, casa_key, barrados)")
    i_dedup = src.index("_dedup_superbet_text(")
    assert i_corte < i_trava < i_marca < i_dedup
    assert "barrados=barrados, fora_travas=fora_travas" in src
    assert 'contagem["fora_travas"] = fora_travas' in src
    assert "or fora_travas:" in src            # lote inteiro barrado ainda responde e registra


def test_frases_da_tela():
    src = (RAIZ / "app" / "static" / "index.html").read_text(encoding="utf-8")
    assert "com mais de 12 meses ignorada(s)" in src
    assert "em conta de real: ainda não suportada nesta casa" in src
