"""A moeda que a CASA informa contra a moeda cadastrada da CONTA (s391, passo 2b).

O achado que originou o passo: os injects sempre leram a moeda da casa (`moeda:` no jb,
x1, kto, rg, stk, tv e bda), mas nenhum formatador do `content.js` a escrevia no bloco.
Ela morria dentro da extensão, e o servidor nunca soube em que moeda a casa falou.

O caminho agora, e o gate de cada trecho:

1. `content.js` escreve `Moeda: X` só quando X não é real → `tests/js/moeda_captura_content.mjs`
   (mutações abaixo, sobre uma cópia do `content.js`).
2. `cambio.moedas_do_texto` lê do TEXTO CRU, e o `/extrair` devolve no `done` dos três
   caminhos → este arquivo (funções puras com mutação automática sobre uma cópia do
   `cambio.py`; os três `done` por presença no fonte).
3. O front transporta ao `/salvar` (`moedas`), igual ao `carimbos` → presença no fonte.
4. O `/salvar` compara com a moeda da conta e AVISA apontando a conta, sem bloquear.
   `$` cabe em USD e em USDT (a Bet Panda manda `$` com carteira em Tether) → este arquivo.
   Mutações da rota, medidas à mão em 03/10/2026, cada uma derrubou ao menos um teste
   daqui: tirar o `if contra and parceiro_txt` (aviso sempre) · trocar por `if False` ·
   o aviso deixar de nomear a conta · o `/salvar` deixar de gravar quando há aviso
   (`rows = []`). 4 de 4 detectadas.

O que NÃO está coberto: o `done` real do `/extrair` com IA (só a presença da chave no
fonte), e a posição da linha `Moeda:` dentro do bloco de cada casa.
"""
import asyncio
import importlib.util
import os
import shutil
import subprocess
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

import main
from main import SalvarRequest

RAIZ = Path(__file__).resolve().parent.parent
CAMBIO = RAIZ / "app" / "cambio.py"
CONTENT = RAIZ / "extensor" / "content.js"
MJS = RAIZ / "tests" / "js" / "moeda_captura_content.mjs"


# ── Funções puras do cambio.py, rodadas contra o módulo dado ─────────────────

def _falhas_cambio(mod) -> list[str]:
    f = []

    def chk(cond, msg):
        if not cond:
            f.append(msg)

    texto = ("[Código: 1]\nStake: 25,00\nMoeda: $\n"
             "[Código: 2]\nStake: 10,00\nMoeda: usdt\n"
             "[Código: 3]\nMoeda: $\n"
             "Descrição: Moeda: XYZ no meio da linha não conta\n")
    chk(mod.moedas_do_texto(texto) == ["$", "usdt"],
        "moedas_do_texto: distintas, na ordem, só no início da linha")
    chk(mod.moedas_do_texto("") == [] and mod.moedas_do_texto(None) == [],
        "moedas_do_texto: texto vazio dá []")
    chk(mod.moedas_do_texto("Stake: 1,00\nStatus: Ganhou") == [],
        "moedas_do_texto: lote em real (sem a linha) dá []")
    chk(mod.moedas_do_texto("Moeda:   USD   \r\n") == ["USD"],
        "moedas_do_texto: apara espaço e CR")

    c = mod.moedas_contraditorias
    chk(c("USDT", ["$"]) == [] and c("USD", ["$"]) == [], "'$' cabe em USD e em USDT")
    chk(c("USDT", ["usdt"]) == [] and c("USDT", ["USDT"]) == [], "comparação sem caixa")
    chk(c("USD", ["US$"]) == [], "'US$' é dólar")
    chk(c("USDT", ["USD"]) == ["USD"], "USD numa conta USDT contradiz")
    chk(c("USD", ["USDT"]) == ["USDT"], "USDT numa conta USD contradiz")
    chk(c("BRL", ["$"]) == ["$"], "'$' numa conta em real contradiz")
    chk(c("BRL", ["USD", "R$"]) == ["USD"], "R$ numa conta em real não contradiz")
    chk(c("USD", ["EUR"]) == ["EUR"], "moeda fora da tabela contradiz")
    chk(c("BRL", None) == [] and c("USDT", []) == [], "sem moeda informada não há aviso")
    return f


def test_funcoes_puras_do_cambio():
    import cambio
    assert _falhas_cambio(cambio) == []


MUTACOES_CAMBIO = [
    ("'$' deixa de caber em USDT",
     '    "USDT": {"USDT", "$"},', '    "USDT": {"USDT"},'),
    ("'$' deixa de caber em USD",
     '    "USD": {"USD", "US$", "$"},', '    "USD": {"USD", "US$"},'),
    ("a comparação passa a ter caixa",
     "if str(v).strip().upper() not in ok]", "if str(v).strip() not in ok]"),
    ("USD e USDT viram a mesma coisa",
     '    "USDT": {"USDT", "$"},', '    "USDT": {"USDT", "USD", "$"},'),
    ("a leitura deixa de exigir o início da linha",
     '_MOEDA_RE = re.compile(r"^Moeda:', '_MOEDA_RE = re.compile(r"Moeda:'),
    ("a leitura repete moedas",
     "        if v and v not in vistas:\n", "        if v:\n"),
    ("a leitura deixa de aparar",
     "        v = m.group(1).strip()\n", "        v = m.group(0)\n"),
    ("toda moeda vira contradição",
     "    return [v for v in (vistas or []) if str(v).strip().upper() not in ok]",
     "    return list(vistas or [])"),
]


@pytest.mark.parametrize("titulo,de,para", MUTACOES_CAMBIO, ids=[m[0] for m in MUTACOES_CAMBIO])
def test_mutacoes_do_cambio_sao_detectadas(tmp_path, titulo, de, para):
    src = CAMBIO.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert src.count(de) == 1, f"âncora da mutação «{titulo}» não é única no cambio.py"
    alvo = tmp_path / "cambio_mutado.py"
    alvo.write_text(src.replace(de, para, 1), encoding="utf-8")
    spec = importlib.util.spec_from_file_location("cambio_mutado", alvo)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert _falhas_cambio(mod), f"a mutação «{titulo}» passou despercebida"


# ── O caminho até o /salvar: presença no fonte ───────────────────────────────

def test_os_tres_done_do_extrair_devolvem_as_moedas():
    src = (RAIZ / "app" / "main.py").read_text(encoding="utf-8")
    assert src.count("'moedas': _cambio.moedas_do_texto(texto)") == 2, "done sequencial e em chunks"
    assert src.count('"moedas": _cambio.moedas_do_texto(texto),') == 1, "done do contrato de 4 campos"


def test_o_front_transporta_as_moedas_ao_salvar():
    src = (RAIZ / "app" / "static" / "index.html").read_text(encoding="utf-8")
    assert "moedas: data.moedas || null" in src


# ── O aviso no /salvar ───────────────────────────────────────────────────────

TSV = "26/07/2026\tFutebol\t\tBet Panda\tX\tML\tFlamengo [Flamengo v Santos]\t25,00\t1,50\tW\t298782220"


def _salvar(moeda_conta, moedas, parceiro_id=351):
    conta = {"id": 351, "casa": "Bet Panda", "nome": "Feca [Eu]", "arquivado": False,
             "moeda": moeda_conta}
    body = SalvarRequest(tsv=TSV, casa="Bet Panda", parceiro="Feca [Eu]",
                         parceiro_id=parceiro_id, moedas=moedas)
    with patch.object(main, "get_parceiro", AsyncMock(return_value=conta)), \
         patch.object(main, "moeda_da_conta", AsyncMock(return_value=moeda_conta)), \
         patch.object(main._cambio, "carregar", AsyncMock(return_value=None)), \
         patch.object(main._cambio, "cotacao", lambda m, iso: 5.0), \
         patch.object(main, "casa_canonica", AsyncMock(side_effect=lambda n: n)), \
         patch.object(main, "upsert_bilhetes", AsyncMock(return_value=(1, 0, [9], [], {}))) as up, \
         patch.object(main, "auto_arquivar", AsyncMock(return_value=0)):
        res = asyncio.run(main.salvar(body, dono="Feca", dono_view="Feca"))
    gravadas = up.call_args[0][0] if up.call_args else []
    return res, gravadas


def _avisos(res):
    return [a for a in res["alertas"] if "A casa informou" in a]


def test_moeda_que_contradiz_a_conta_avisa_apontando_a_conta_e_grava():
    res, gravadas = _salvar("BRL", ["USD"])
    av = _avisos(res)
    assert len(av) == 1, res["alertas"]
    assert "Feca [Eu]" in av[0] and "Bet Panda" in av[0], "o aviso precisa apontar a conta"
    assert "USD" in av[0] and "cadastrada em BRL" in av[0]
    assert len(gravadas) == 1, "o aviso não bloqueia a gravação"
    assert gravadas[0]["stake"] == "25,00", "grava pela moeda da CONTA, sem converter"


def test_dolar_sem_distincao_numa_conta_usdt_nao_avisa():
    res, gravadas = _salvar("USDT", ["$"])
    assert _avisos(res) == []
    assert gravadas[0]["stake"] == "125,00", "a conversão da conta USDT segue normal"


def test_usd_numa_conta_usdt_avisa():
    res, _ = _salvar("USDT", ["USD"])
    assert len(_avisos(res)) == 1


def test_lote_sem_moeda_informada_nao_avisa():
    for moedas in (None, []):
        res, _ = _salvar("BRL", moedas)
        assert _avisos(res) == []


# ── content.js ───────────────────────────────────────────────────────────────

@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
def test_content_por_execucao():
    r = subprocess.run(["node", str(MJS)], capture_output=True, text=True,
                       encoding="utf-8", cwd=str(RAIZ))
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")


MUTACOES_CONTENT = [
    ("o real passa a escrever linha (muda o hash de toda casa em real)",
     '    return (!t || /^(brl|r\\$)$/i.test(t)) ? "" : t;',
     '    return !t ? "" : t;'),
    ("só o BRL maiúsculo se cala",
     '    return (!t || /^(brl|r\\$)$/i.test(t)) ? "" : t;',
     '    return (!t || /^(BRL|R\\$)$/.test(t)) ? "" : t;'),
    ("o real deixa de ser exato",
     '    return (!t || /^(brl|r\\$)$/i.test(t)) ? "" : t;',
     '    return (!t || /(brl|r\\$)/i.test(t)) ? "" : t;'),
    ("a moeda deixa de ser aparada",
     '    const t = String(m == null ? "" : m).trim();',
     '    const t = String(m == null ? "" : m);'),
    ("o helper para de escrever",
     'if (t) L.push("Moeda: " + t); };', 'if (t) {} };'),
    ("a 1xBet deixa de escrever a moeda", "    _linhaMoeda(L, b.moeda);\n\n    const n = (b.sels",
     "\n    const n = (b.sels"),
    ("a Jonbet deixa de escrever a moeda",
     '    _linhaMoeda(L, b.moeda);\n    L.push("Status: " + _resultadoJB(b));',
     '    L.push("Status: " + _resultadoJB(b));'),
    ("a KTO deixa de escrever a moeda", "    _linhaMoeda(L, c.moeda);\n", ""),
    ("a Tivo deixa de escrever a moeda", "    _linhaMoeda(L, t.moeda);\n", ""),
]


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
@pytest.mark.parametrize("titulo,de,para", MUTACOES_CONTENT, ids=[m[0] for m in MUTACOES_CONTENT])
def test_mutacoes_do_content_sao_detectadas(tmp_path, titulo, de, para):
    src = CONTENT.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert src.count(de) == 1, f"âncora da mutação «{titulo}» não é única no content.js ({src.count(de)})"
    alvo = tmp_path / "content.js"
    alvo.write_text(src.replace(de, para, 1), encoding="utf-8")
    env = {**os.environ, "ALVO_CONTENT": str(alvo)}
    r = subprocess.run(["node", str(MJS)], capture_output=True, text=True,
                       encoding="utf-8", cwd=str(RAIZ), env=env)
    assert r.returncode != 0, f"a mutação «{titulo}» passou despercebida\n" + (r.stdout or "")
