"""Espelho da 1xBet em domínio NOVO: a captura se ajusta sozinha (s410).

O caso: a Megapari trocou `2479527mp.pro` por `4569421mp.pro`. Fora do manifest o
`x1_inject` só entrava pelo popup, DEPOIS que a página tinha buscado o histórico, e o
replay não tinha requisição para copiar: "hook ATIVO · respostas 0", sem erro.

O conserto, em três peças, e o gate de cada uma (`tests/js/x1_dominio_novo.mjs`, que
executa o código RECORTADO dos arquivos reais):

1. `x1_inject.js` marca `__suX1Cedo` (entrou com a página carregando?).
2. `popup.js` (`x1RecarregarSeAtrasado`): espelho móvel com hook atrasado → registra o
   domínio para `document_start` no MAIN (só se não estiver no manifest), deixa
   `roboPendente` e recarrega a aba.
3. `background.js` (`retomarRobo`): no `complete` da mesma aba e do mesmo host, dentro do
   prazo, manda `START_ROBOT` uma vez.

Mutações abaixo, cada uma sobre uma CÓPIA do arquivo; todas têm de derrubar o .mjs.
O que NÃO está coberto: o Chrome real (registro dinâmico e reload), ver o cabeçalho do .mjs.
"""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
EXT = RAIZ / "extensor"
MJS = RAIZ / "tests" / "js" / "x1_dominio_novo.mjs"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")


def _rodar(env_extra=None):
    env = dict(os.environ, **(env_extra or {}))
    return subprocess.run(["node", str(MJS)], capture_output=True, text=True,
                          encoding="utf-8", env=env, cwd=RAIZ)


def test_dominio_novo_verde():
    r = _rodar()
    assert r.returncode == 0, r.stdout + r.stderr


# (arquivo, variável de ambiente, descrição, trecho original, trecho mutado)
MUTACOES = [
    ("x1_inject.js", "ALVO_INJECT", "marca cedo sempre",
     'window.__suX1Cedo = document.readyState === "loading";', "window.__suX1Cedo = true;"),
    ("x1_inject.js", "ALVO_INJECT", "injeção tardia apaga a marca cedo",
     'if (window.__suX1Cedo == null) window.__suX1Cedo', "window.__suX1Cedo"),
    ("popup.js", "ALVO_POPUP", "registro em document_idle",
     'runAt: "document_start", world: "MAIN"', 'runAt: "document_idle", world: "MAIN"'),
    ("popup.js", "ALVO_POPUP", "registro fora do mundo MAIN",
     'world: "MAIN", persistAcrossSessions', "persistAcrossSessions"),
    ("popup.js", "ALVO_POPUP", "hook cedo também recarrega",
     "  if (cedo) return false;\n", ""),
    ("popup.js", "ALVO_POPUP", "substring vira subdomínio",
     'h.endsWith("." + base)', "h.endsWith(base)"),
    ("popup.js", "ALVO_POPUP", "domínio do manifest também é registrado",
     "  if (!x1NoManifest(host)) {\n", "  if (true) {\n"),
    ("popup.js", "ALVO_POPUP", "registro recusado recarrega mesmo assim",
     "catch (_) { return false; }   // sem registro", "catch (_) {}   // sem registro"),
    ("popup.js", "ALVO_POPUP", "regrava o registro com o mesmo domínio",
     "if (matches.length !== (atual.matches || []).length) {", "if (true) {"),
    ("popup.js", "ALVO_POPUP", "registro novo substitui o antigo",
     "[...(atual.matches || []), ...novos]", "[...novos]"),
    ("popup.js", "ALVO_POPUP", "1xBit sai da lista",
     '"Megapari", "SapphireBet", "1xBit"', '"Megapari", "SapphireBet"'),
    ("popup.js", "ALVO_POPUP", "MelBet sai da lista",
     '"1xBit", "MelBet"]', '"1xBit"]'),
    ("popup.js", "ALVO_POPUP", "capturar() deixa de chamar o desvio",
     "      if (await x1RecarregarSeAtrasado(tab, host, casa)) { window.close(); return; }\n", ""),
    ("popup.js", "ALVO_POPUP", "sem pendência para o background",
     "  await chrome.storage.local.set({ roboPendente:", "  if (0) await chrome.storage.local.set({ roboPendente:"),
    ("background.js", "ALVO_BG", "qualquer aba dispara",
     "if (!p || p.tabId !== tabId) return false;", "if (!p) return false;"),
    ("background.js", "ALVO_BG", "prazo ignorado",
     "  if (Date.now() > p.ate) return false;\n", ""),
    ("background.js", "ALVO_BG", "host ignorado",
     "  if (host !== p.host) return false;\n", ""),
    ("background.js", "ALVO_BG", "pendência não é consumida",
     '  await chrome.storage.local.remove("roboPendente");\n', ""),
    ("background.js", "ALVO_BG", "qualquer status dispara",
     '  if (info.status !== "complete") return;\n', ""),
    ("background.js", "ALVO_BG", "uma tentativa só",
     "for (let i = 0; i < 10; i++)", "for (let i = 0; i < 1; i++)"),
]


@pytest.mark.parametrize("arq,env,desc,orig,mut", MUTACOES, ids=[m[2] for m in MUTACOES])
def test_mutacao_detectada(tmp_path, arq, env, desc, orig, mut):
    src = (EXT / arq).read_text(encoding="utf-8").replace("\r\n", "\n")
    assert src.count(orig) == 1, f"mutação '{desc}' não achou o alvo em {arq}"
    copia = tmp_path / arq
    copia.write_text(src.replace(orig, mut), encoding="utf-8")
    r = _rodar({env: str(copia)})
    assert r.returncode != 0, f"mutação '{desc}' passou verde:\n{r.stdout}{r.stderr}"
