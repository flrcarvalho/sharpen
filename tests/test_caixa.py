"""Caixa (s314) — a projeção de saldo por conta e o que ela precisa acertar.

A Caixa responde "quanto esta conta DEVERIA ter na casa hoje", e a resposta só vale
confrontada com o que a casa mostra. A conta:

    banca      = saldo inicial + preso no corte + depósitos − saques ± ajustes + P/L
    em aberto  = Σ stake das apostas elegíveis ainda não liquidadas
    disponível = banca − em aberto        ← é este que a casa mostra na tela

O caso que obriga o `abertas_corte` a existir, e que estes testes travam: toda aposta
mexe no saldo DUAS vezes — −stake quando é feita, +retorno quando liquida. Para a
aposta nascida depois do corte as duas pontas caem dentro da janela e o líquido é o
P/L. Para a aposta que já estava ABERTA no dia do corte, só a segunda ponta cai: o
stake saiu ANTES (logo não está no saldo informado) e volta INTEIRO ao liquidar. Sem
reconhecer essas apostas, toda conta configurada num dia com aposta viva nasceria com
uma divergência permanente do tamanho desses retornos — a auditoria acusando a si
mesma para sempre.

O que estes testes NÃO cobrem, de propósito: a gravação (`caixa_lancar`,
`caixa_visao`) toca o Postgres e vive no harness de banco; aqui está só a matemática
pura, que é onde o erro sairia caro e silencioso.
"""
import pytest

from app.repository import _caixa_projetar


def mov(tipo, data, valor, **kw):
    m = {"id": kw.get("id", 1), "tipo": tipo, "data": data, "valor": valor,
         "obs": kw.get("obs", ""), "projetado": kw.get("projetado"),
         "abertas_corte": kw.get("abertas_corte"),
         "criado_em": kw.get("criado_em", "2026-09-01T10:00:00")}
    return m


def ap(id_, data, stake, resultado="", odd=None):
    return {"id": id_, "data": data, "stake": stake, "odd": odd, "resultado": resultado}


# ── Caixa desligada ───────────────────────────────────────────────────────────

def test_sem_saldo_inicial_a_caixa_fica_desligada():
    """Sem `inicial` não se projeta nada — nem a partir do histórico de apostas.
    Número inventado numa tela de conferência vale menos que campo vazio."""
    r = _caixa_projetar(
        [mov("deposito", "2026-08-01", 500.0)],
        [ap(1, "2026-08-02", 100.0, "W", 2.0)],
    )
    assert r["ligada"] is False
    assert r["estado"] == "desligada"
    assert r["disponivel"] == 0.0 and r["banca"] == 0.0 and r["pl"] == 0.0


# ── A conta ───────────────────────────────────────────────────────────────────

def test_soma_completa():
    movs = [
        mov("inicial", "2026-08-01", 3000.0, id=1),
        mov("deposito", "2026-08-05", 1500.0, id=2),
        mov("deposito", "2026-08-20", 1000.0, id=3),
        mov("saque", "2026-08-12", 1800.0, id=4),
        mov("ajuste", "2026-08-19", 50.0, id=5),
    ]
    apostas = [
        ap(10, "2026-08-10", 100.0, "W", 2.5),    # +150
        ap(11, "2026-08-11", 200.0, "L"),         # −200
        ap(12, "2026-08-15", 300.0, "V", 1.8),    # 0 (stake devolvido)
        ap(13, "2026-08-30", 250.0),              # aberta: −250 do disponível
    ]
    r = _caixa_projetar(movs, apostas)
    assert r["ligada"] is True
    assert (r["depositos"], r["n_depositos"]) == (2500.0, 2)
    assert (r["saques"], r["n_saques"]) == (1800.0, 1)
    assert (r["ajustes"], r["n_ajustes"]) == (50.0, 1)
    assert (r["pl"], r["n_liquidadas"]) == (-50.0, 3)
    assert (r["aberto"], r["n_abertas"]) == (250.0, 1)
    # 3000 + 2500 − 1800 + 50 − 50 = 3700
    assert r["banca"] == 3700.0
    assert r["disponivel"] == 3450.0


def test_lancamento_anterior_ao_corte_nao_conta():
    """Depósito feito ANTES da data informada já está dentro do saldo informado.
    Somá-lo seria contar o mesmo dinheiro duas vezes."""
    movs = [mov("inicial", "2026-08-01", 1000.0, id=1),
            mov("deposito", "2026-07-20", 900.0, id=2),
            mov("deposito", "2026-08-01", 100.0, id=3)]   # mesmo dia do corte: entra
    r = _caixa_projetar(movs, [])
    assert r["depositos"] == 100.0 and r["n_depositos"] == 1
    assert r["disponivel"] == 1100.0


def test_aposta_anterior_ao_corte_nao_conta():
    """Aposta liquidada antes do corte já está embutida no saldo informado."""
    movs = [mov("inicial", "2026-08-01", 1000.0)]
    r = _caixa_projetar(movs, [ap(1, "2026-07-15", 500.0, "W", 3.0)])
    assert r["pl"] == 0.0 and r["n_liquidadas"] == 0
    assert r["disponivel"] == 1000.0


# ── O caso que o `abertas_corte` existe para resolver ─────────────────────────

def test_aposta_aberta_no_corte_ainda_aberta_nao_muda_o_saldo():
    """O stake dela saiu antes do corte: entra na banca e sai de novo em 'em aberto'.
    Enquanto não liquidar, o disponível tem de ser EXATAMENTE o saldo informado."""
    movs = [mov("inicial", "2026-08-01", 1000.0, abertas_corte=[7])]
    r = _caixa_projetar(movs, [ap(7, "2026-07-28", 400.0)])
    assert r["preso_corte"] == 400.0 and r["n_preso_corte"] == 1
    assert r["aberto"] == 400.0 and r["n_abertas"] == 1
    assert r["banca"] == 1400.0
    assert r["disponivel"] == 1000.0


def test_aposta_aberta_no_corte_ao_liquidar_devolve_stake_mais_pl():
    """Ao liquidar, a casa credita o RETORNO (stake + P/L), não só o lucro."""
    movs = [mov("inicial", "2026-08-01", 1000.0, abertas_corte=[7])]
    r = _caixa_projetar(movs, [ap(7, "2026-07-28", 400.0, "W", 2.0)])   # retorno 800
    assert r["preso_corte"] == 400.0
    assert r["pl"] == 400.0
    assert r["aberto"] == 0.0
    assert r["disponivel"] == 1800.0     # 1000 + 400 (stake) + 400 (lucro)


def test_aposta_aberta_no_corte_perdida_nao_devolve_nada():
    movs = [mov("inicial", "2026-08-01", 1000.0, abertas_corte=[7])]
    r = _caixa_projetar(movs, [ap(7, "2026-07-28", 400.0, "L")])
    assert r["disponivel"] == 1000.0     # 1000 + 400 − 400


def test_sem_a_lista_a_aposta_velha_some_e_o_saldo_fica_baixo():
    """Contraprova: a MESMA aposta, sem estar no `abertas_corte`, some da conta — e é
    exatamente essa a divergência permanente que a lista existe para impedir."""
    movs = [mov("inicial", "2026-08-01", 1000.0)]
    r = _caixa_projetar(movs, [ap(7, "2026-07-28", 400.0, "W", 2.0)])
    assert r["disponivel"] == 1000.0     # deveria ser 1800: o retorno se perdeu


def test_aposta_no_corte_nao_e_contada_duas_vezes():
    """Id na lista E data depois do corte (não deve acontecer, mas se acontecer o
    stake não pode entrar duas vezes na banca)."""
    movs = [mov("inicial", "2026-08-01", 1000.0, abertas_corte=[7])]
    r = _caixa_projetar(movs, [ap(7, "2026-08-10", 400.0, "W", 2.0)])
    assert r["preso_corte"] == 400.0 and r["n_preso_corte"] == 1
    assert r["disponivel"] == 1800.0


# ── Linhas que não entram na conta ────────────────────────────────────────────

def test_stake_zero_e_resultado_lixo_ficam_de_fora():
    movs = [mov("inicial", "2026-08-01", 1000.0)]
    r = _caixa_projetar(movs, [
        ap(1, "2026-08-02", 0.0, "W", 2.0),        # stake 0
        ap(2, "2026-08-03", 100.0, "XPTO"),        # resultado inválido
        ap(3, "2026-08-04", 100.0, "W", None),     # odd ilegível numa vitória
    ])
    assert r["pl"] == 0.0 and r["n_liquidadas"] == 0 and r["aberto"] == 0.0
    assert r["disponivel"] == 1000.0


def test_odd_e_stake_em_texto_br():
    """O banco guarda stake/odd como TEXTO em pt-BR — a projeção tem de ler isso."""
    movs = [mov("inicial", "2026-08-01", 1000.0)]
    r = _caixa_projetar(movs, [ap(1, "2026-08-02", "1.250,50", "W", "2,00")])
    assert r["pl"] == 1250.5
    assert r["disponivel"] == 2250.5


def test_data_em_formato_br_tambem_e_aceita():
    movs = [mov("inicial", "2026-08-01", 1000.0)]
    r = _caixa_projetar(movs, [ap(1, "10/08/2026", 100.0, "L")])
    assert r["n_liquidadas"] == 1 and r["disponivel"] == 900.0


# ── Estado da conferência ─────────────────────────────────────────────────────

def test_nunca_conferida():
    r = _caixa_projetar([mov("inicial", "2026-08-01", 1000.0)], [])
    assert r["estado"] == "nunca" and r["conferencia"] is None and r["divergencia"] is None


def test_conferencia_que_bate():
    movs = [mov("inicial", "2026-08-01", 1000.0, id=1),
            mov("conferencia", "2026-09-02", 1000.0, id=2, projetado=1000.0)]
    r = _caixa_projetar(movs, [])
    assert r["estado"] == "confere"
    assert r["divergencia"] == 0.0


def test_conferencia_divergente_acusa():
    """Faltando dinheiro na conta: é ISTO que denuncia o saque não registrado."""
    movs = [mov("inicial", "2026-08-01", 1000.0, id=1),
            mov("conferencia", "2026-09-02", 150.0, id=2, projetado=1000.0)]
    r = _caixa_projetar(movs, [])
    assert r["estado"] == "divergente"
    assert r["divergencia"] == -850.0


def test_divergencia_medida_no_momento_nao_e_recalculada_hoje():
    """A conferência guarda o que FOI conferido. A projeção de hoje já inclui aposta
    que nem existia na data — recalcular contra ela reescreveria o passado."""
    movs = [mov("inicial", "2026-08-01", 1000.0, id=1),
            mov("conferencia", "2026-08-15", 900.0, id=2, projetado=1000.0,
                criado_em="2026-08-15T10:00:00")]
    r = _caixa_projetar(movs, [ap(9, "2026-08-20", 500.0, "W", 3.0)])
    assert r["disponivel"] == 2000.0          # a projeção de hoje andou
    assert r["divergencia"] == -100.0         # a conferência continua dizendo o que viu


def test_lancamento_posterior_transforma_divergencia_em_reconferir():
    """O operador lançou o que faltava: o número antigo já não descreve a conta, mas
    também não se pode dizer que bate — falta reconferir."""
    movs = [mov("inicial", "2026-08-01", 1000.0, id=1),
            mov("conferencia", "2026-08-15", 900.0, id=2, projetado=1000.0,
                criado_em="2026-08-15T10:00:00"),
            mov("saque", "2026-08-14", 100.0, id=3, criado_em="2026-08-15T11:00:00")]
    r = _caixa_projetar(movs, [])
    assert r["estado"] == "reconferir"


def test_lancamento_anterior_a_conferencia_nao_apaga_o_alerta():
    """Só lançamento feito DEPOIS da conferência a torna obsoleta."""
    movs = [mov("inicial", "2026-08-01", 1000.0, id=1),
            mov("saque", "2026-08-10", 100.0, id=2, criado_em="2026-08-10T09:00:00"),
            mov("conferencia", "2026-08-15", 500.0, id=3, projetado=900.0,
                criado_em="2026-08-15T10:00:00")]
    r = _caixa_projetar(movs, [])
    assert r["estado"] == "divergente" and r["divergencia"] == -400.0


def test_conferencia_que_bate_nao_pede_reconferencia():
    """Divergência zero + lançamento novo é operação normal, não alerta."""
    movs = [mov("inicial", "2026-08-01", 1000.0, id=1),
            mov("conferencia", "2026-08-15", 1000.0, id=2, projetado=1000.0,
                criado_em="2026-08-15T10:00:00"),
            mov("deposito", "2026-08-16", 500.0, id=3, criado_em="2026-08-16T10:00:00")]
    assert _caixa_projetar(movs, [])["estado"] == "confere"


def test_vale_a_ultima_conferencia():
    movs = [mov("inicial", "2026-08-01", 1000.0, id=1),
            mov("conferencia", "2026-08-15", 500.0, id=2, projetado=1000.0,
                criado_em="2026-08-15T10:00:00"),
            mov("conferencia", "2026-08-20", 1000.0, id=3, projetado=1000.0,
                criado_em="2026-08-20T10:00:00")]
    assert _caixa_projetar(movs, [])["estado"] == "confere"


def test_centavo_de_arredondamento_nao_e_divergencia():
    movs = [mov("inicial", "2026-08-01", 1000.0, id=1),
            mov("conferencia", "2026-09-02", 1000.002, id=2, projetado=1000.0)]
    assert _caixa_projetar(movs, [])["estado"] == "confere"


def test_um_centavo_e_divergencia():
    """O corte é de meio centavo: um centavo de diferença TEM de acender."""
    movs = [mov("inicial", "2026-08-01", 1000.0, id=1),
            mov("conferencia", "2026-09-02", 999.99, id=2, projetado=1000.0)]
    assert _caixa_projetar(movs, [])["estado"] == "divergente"


# ── Sinais ────────────────────────────────────────────────────────────────────

def test_ajuste_negativo_reduz_o_saldo():
    movs = [mov("inicial", "2026-08-01", 1000.0, id=1),
            mov("ajuste", "2026-08-10", -120.0, id=2)]
    r = _caixa_projetar(movs, [])
    assert r["ajustes"] == -120.0
    assert r["disponivel"] == 880.0


def test_saldo_projetado_pode_ficar_negativo():
    """Não é prejuízo — é lançamento faltando. A tela pinta em âmbar (aviso)."""
    movs = [mov("inicial", "2026-08-01", 100.0, id=1),
            mov("saque", "2026-08-10", 500.0, id=2)]
    assert _caixa_projetar(movs, [])["disponivel"] == -400.0


# ── Camada de tela ────────────────────────────────────────────────────────────
# A máscara do saldo e o vaivém da data vivem no `index.html`. `tests/js/caixa_front.mjs`
# RECORTA `fmtSaldo`/`_cxDataBR`/`_cxDataBR4`/`_cxIso` do arquivo de produção e os executa.

import io
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
INDEX = RAIZ / "app" / "static" / "index.html"
MJS = RAIZ / "tests" / "js" / "caixa_front.mjs"


def _node(alvo=None):
    env = None
    if alvo:
        import os
        env = dict(os.environ, ALVO_INDEX=str(alvo))
    return subprocess.run(["node", str(MJS)], capture_output=True, text=True,
                          encoding="utf-8", cwd=str(RAIZ), env=env)


def test_prova_por_execucao_do_front():
    r = _node()
    assert r.returncode == 0, (r.stdout or "") + (r.stderr or "")


def test_o_gate_detecta_a_data_de_ano_curto_no_campo(tmp_path):
    """O bug medido no navegador: o campo nascer com dd/mm/aa e o parser exigir 4
    dígitos. A mutação devolve o parser antigo — o gate TEM de ficar vermelho."""
    src = INDEX.read_text(encoding="utf-8")
    alvo = "m = /^(\d{1,2})\/(\d{1,2})\/(\d{2}|\d{4})$/.exec(s);"
    assert src.count(alvo) == 1, "a regex de data mudou de forma — reveja esta mutação"
    mutante = tmp_path / "index_mutante.html"
    io.open(mutante, "w", encoding="utf-8", newline="").write(
        src.replace(alvo, "m = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/.exec(s);")
    )
    assert _node(mutante).returncode != 0, "o gate passou com o parser quebrado"


def test_o_gate_detecta_saldo_colorido(tmp_path):
    """Pintar o saldo de verde/vermelho quebra a regra de cor da marca (verde e
    vermelho são semântica de RESULTADO). O gate tem de pegar."""
    src = INDEX.read_text(encoding="utf-8")
    alvo = "  const sg = (v < 0 ? '−' : (sinal && v > 0 ? '+' : '')) + 'R$';   // minus U+2212"
    assert src.count(alvo) == 1
    mutante = tmp_path / "index_cor.html"
    io.open(mutante, "w", encoding="utf-8", newline="").write(
        src.replace(alvo, alvo + "\n  if (v < 0) return `<span class=\"money neg\">"
                          "<span class=\"money-sign\">${sg}</span>"
                          "<span class=\"money-val\">${abs}</span></span>`;")
    )
    assert _node(mutante).returncode != 0, "o gate passou com o saldo colorido"
