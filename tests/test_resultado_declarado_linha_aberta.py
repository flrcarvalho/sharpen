"""8.2 (s460): a linha que a IA deixou ABERTA, num bloco em que o formatador DECLAROU o
resultado e o retorno é provado, sai com o resultado que o dinheiro confirma
(`repository._bloco_declarou` + `_veredito_do_retorno`, dentro do `corrigir_stake_tsv`).

E o "a conferir" CONTINUA aberto. O plano pedia decidi-lo pelo dinheiro; a medição da s460
recusou (o porquê está no comentário de `_bloco_declarou`): nenhuma aposta do estoque de
produção estava presa por rótulo, os "a conferir" do harness são ambíguos de propósito, e o
CLAUDE.md proíbe inferir W/L de rótulo desconhecido. Este arquivo trava as duas metades.

Roda sobre os blocos REAIS que os formatadores imprimem no harness (o snapshot do contrato,
`tests/fixtures/contrato_liquidacao/blocos.json.gz`), pelo caminho inteiro: a linha do TSV
entra aberta e sai do `corrigir_stake_tsv`.

A propriedade que vale para TODA linha fechada aqui: o P/L gravado é retorno − stake.

Mutações provadas (aplicadas, teste vermelho, revertidas):
  1. sem o ramo da linha aberta                → test_todo_resultado_declarado_que_a_ia_perdeu…
  2. `_bloco_declarou` aceita "a conferir"      → test_a_conferir_do_harness_continua_aberto
  3. grava sem conferir com o dinheiro          → test_declaracao_que_o_dinheiro_desmente…
  4. sem a conferência de P/L = retorno − stake → test_nunca_grava_sem_odd…

NÃO cobre: o print (sem bloco não há prova); se a casa liquidou de fato (o gate confia no
texto do robô, como os outros gates financeiros).
"""
import gzip
import json
import pathlib

import repository as R

PASTA = pathlib.Path(__file__).parent / "fixtures" / "contrato_liquidacao"
BLOCOS = json.loads(gzip.decompress((PASTA / "blocos.json.gz").read_bytes()).decode("utf-8"))


def _codigo(b):
    return R._ID_MARCADOR_RE.search(b).group(1).strip()


def _decidir(b, odd=""):
    """A linha que a IA escreve com o resultado em branco, passada pelo gate."""
    info = R._financeiro_do_texto(b)[_codigo(b)]
    linha = "\t".join(["17/11/2026", "Casa", "Conta", "", "Futebol", "Resultado Final",
                       "Time A v Time B", info["stake"], odd, "", _codigo(b)])
    tsv, rel = R.corrigir_stake_tsv(linha, b)
    return tsv.split("\t"), rel


def _todos():
    for caso, lista in BLOCOS.items():
        for b in lista:
            info = R._financeiro_do_texto(b).get(_codigo(b))
            if info:
                yield caso, b, info


def test_todo_resultado_declarado_que_a_ia_perdeu_volta_e_fecha_o_dinheiro():
    fechados = 0
    for caso, b, info in _todos():
        stt = info.get("status") or ""
        if "a conferir" in stt.lower() or not R._RESULTADO_SETA_RE.search(stt):
            continue
        stake = R._num_or_none(info["stake"])
        ret = R._retorno_do_bloco(info, stake)
        if ret is None:
            continue
        p, rel = _decidir(b)
        if not p[9]:
            continue                       # sem odd que feche (ver o teste de odd abaixo)
        fechados += 1
        assert abs(R.calcular_pl(p[7], p[8], p[9]) - (ret - stake)) < 0.01, (caso, p, ret)
        declarado = R._RESULTADO_SETA_RE.search(stt).group(1)
        assert p[9] == declarado or (declarado, p[9]) == ("W", "HW"), (caso, declarado, p[9])
    assert fechados > 600, fechados        # o teste precisa EXERCER o ramo novo


def test_a_conferir_do_harness_continua_aberto():
    vistos = 0
    for caso, b, info in _todos():
        if "a conferir" in (info.get("status") or "").lower():
            vistos += 1
            assert _decidir(b, odd="2,00")[0][9] == "", (caso, info["status"][:80])
    assert vistos >= 90, vistos
    # No harness, a 1ª seta de todo "a conferir" contraria o dinheiro, e a conferência pelo
    # dinheiro já a barraria. Este é o caso em que ela NÃO barra: a Cloudbet de apostas
    # juntadas com a 1ª sub-aposta ganha, citando o retorno DELA (não o do bilhete).
    b = ("[Código: X7]\nStake: 20,00\nOdd: 1,95\nStatus: result WIN · as 2 apostas não fecham "
         "o mesmo resultado (Ganhou → W (retorno 39,00) | Perdeu → L) "
         "(a conferir — não liquidar automaticamente)\n")
    assert _decidir(b)[0][9] == ""


def test_aposta_aberta_de_verdade_nao_e_tocada():
    b = "[Código: X5]\nStake: 20,00\nOdd: 1,95\nStatus: Em aberto · Retorno potencial: 39,00\n"
    assert _decidir(b)[0][9] == ""
    for caso, blk, info in _todos():
        if "em aberto" in (info.get("status") or "").lower():
            assert _decidir(blk)[0][9] == "", caso


def test_declaracao_que_o_dinheiro_desmente_nao_e_gravada():
    # "Perdeu → L" com retorno pago: o bloco se contradiz, e nada se escreve
    b = "[Código: X6]\nStake: 20,00\nOdd: 1,95\nStatus: Perdeu → L (retorno 39,00)\n"
    assert _decidir(b)[0][9] == ""


def test_nunca_grava_sem_odd_que_feche_o_dinheiro():
    # V sem odd em lugar nenhum: o `/salvar` recusaria a linha; fica aberta
    b = "[Código: X3]\nStake: 10,00\nStatus: Anulada → V (retorno 10,00)\n"
    assert _decidir(b)[0][9] == ""
    p, _ = _decidir(b, odd="1,90")
    assert (p[9], p[8]) == ("V", "1,90")


def test_resultado_declarado_que_a_ia_perdeu_volta_pelo_dinheiro():
    b = "[Código: X4]\nStake: 20,00\nOdd: 1,95\nStatus: Ganhou → W (retorno 39,00)\n"
    p, rel = _decidir(b)
    assert (p[9], p[8]) == ("W", "1,95")
    assert rel["financeiro"] == 1 and rel["exemplos_fin"][0]["res_ia"] == ""
