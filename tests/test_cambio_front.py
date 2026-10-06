"""Câmbio e corretoras no front (s398, passo 6 do `docs/PLANO_MOEDA_POR_CONTA.md`).

Gates:

1. `tests/js/cambio_front.mjs` por execução: o período do câmbio no dashboard
   (`calcCambioFiltrado`) e a transferência no modal da Caixa (`_cxCorrVisivelPara`,
   `_cxCorrLer`), recortados dos arquivos de produção.
2. Mutação automática sobre cópias do `index.html`, do `gestao.js` e do `overview.js`.
3. Presença: o P/L Líquido da Visão Geral soma o câmbio, e o Painel chama o card.

O que NÃO está coberto: o desenho (medido no navegador com o `servidor_demo.py` e
`DEMO_CAMBIO=1`) e o clique real.
"""
import os
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
MJS = RAIZ / "tests" / "js" / "cambio_front.mjs"
JS = RAIZ / "app" / "static" / "dash" / "assets" / "js" / "charts"
ARQS = {
    "index": RAIZ / "app" / "static" / "index.html",
    "gestao": JS / "gestao.js",
}
OVERVIEW = JS / "overview.js"


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
def test_front_por_execucao():
    r = subprocess.run(["node", str(MJS)], capture_output=True, text=True,
                       encoding="utf-8", cwd=str(RAIZ))
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")


MUTACOES = [
    ("o período do câmbio é ignorado", "gestao",
     "(b.realizados||[]).forEach(x=>{if(x.data>=de&&x.data<=ate){",
     "(b.realizados||[]).forEach(x=>{if(true){"),
    ("a taxa soma em vez de descontar", "gestao",
     "return{realizado,taxas,total:realizado-taxas,", "return{realizado,taxas,total:realizado+taxas,"),
    ("as taxas ficam fora do período", "gestao",
     "(b.taxas||[]).forEach(x=>{if(x.data>=de&&x.data<=ate){taxas",
     "(b.taxas||[]).forEach(x=>{if(false){taxas"),
    ("conta em real ganha destino", "index",
     "  return !!d && d.casa !== 'Polymarket' && !!d.moeda && d.moeda !== 'BRL'",
     "  return !!d && d.casa !== 'Polymarket' && !!d.moeda"),
    ("a Polymarket ganha destino", "index",
     "  return !!d && d.casa !== 'Polymarket' && !!d.moeda && d.moeda !== 'BRL'",
     "  return !!d && !!d.moeda && d.moeda !== 'BRL'"),
    ("ajuste ganha destino", "index",
     "    && (tipo === 'saque' || tipo === 'deposito');",
     "    && (tipo !== 'inicial');"),
    ("taxa sem corretora passa", "index",
     "  if (!id && taxa) return { erro:", "  if (false) return { erro:"),
    ("taxa vazia vira zero", "index",
     "  return { corretora_id: id, taxa: taxa || null };", "  return { corretora_id: id, taxa: taxa || 0 };"),
]


@pytest.mark.skipif(shutil.which("node") is None, reason="node ausente")
@pytest.mark.parametrize("titulo,arq,de,para", MUTACOES, ids=[m[0] for m in MUTACOES])
def test_mutacoes_sao_detectadas(tmp_path, titulo, arq, de, para):
    alvo = ARQS[arq]
    src = alvo.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert src.count(de) == 1, f"âncora da mutação «{titulo}» não é única ({src.count(de)})"
    estragado = tmp_path / alvo.name
    estragado.write_text(src.replace(de, para, 1), encoding="utf-8")
    env = {**os.environ, f"ALVO_{arq.upper()}": str(estragado)}
    r = subprocess.run(["node", str(MJS)], capture_output=True, text=True,
                       encoding="utf-8", cwd=str(RAIZ), env=env)
    assert r.returncode != 0, f"a mutação «{titulo}» passou despercebida\n" + (r.stdout or "")


def test_o_pl_liquido_soma_o_cambio_e_o_painel_desenha_o_card():
    ov = OVERVIEW.read_text(encoding="utf-8")
    assert "const lucroLiq=lucro-totalCost+cb.total;" in ov
    assert "if(!window.MODO_PUBLICO&&typeof cbLoad==='function')cbLoad();" in ov
    idx = ARQS["index"].read_text(encoding="utf-8")
    assert "renderPainelCambio(true).catch(function () {});  // câmbio e corretoras — /cambio/visao" in idx
    assert "'<div class=\"painel-card\" id=\"painelCambio\" hidden></div>' +" in idx
