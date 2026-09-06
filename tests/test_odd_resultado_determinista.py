"""Gate financeiro: ODD e RESULTADO conferidos contra o RETORNO do bloco cru (s321).

O que este arquivo cobre: `_veredito_do_retorno`, `_retorno_do_bloco`, `_num_bloco` e o
caminho deles dentro de `corrigir_stake_tsv`. Os blocos abaixo são RECORTES DE BLOCO REAL
(sombra de 26/08–05/09), não texto inventado — o formato de cada casa é o que faz ou quebra
o gate, e um fixture estilizado testaria o parser contra ele mesmo.

O QUE ELE NÃO COBRE, de propósito:
  • extração por PRINT — sem `[Código: …]` no texto não há bloco, e o gate não roda;
  • casa cujo bloco não imprime retorno realizado (BETesporte só tem `Retorno potencial:`);
  • se o valor do bloco é VERDADE. O gate confia no robô; ele conserta a TRADUÇÃO da IA,
    não a captura. Bloco errado na origem entra errado (é o caso conhecido da KTO).

Mutações provadas — cada uma foi APLICADA ao código e o teste ao lado ficou vermelho:
  1. rodar o veredito só quando a stake diverge  → test_odd_errada_com_stake_certa
  2. remover a fórmula de HW                     → test_w_que_era_hw_recebe_o_rotulo_hw…
  3. `_num_bloco` BR-first (como `_num_or_none`) → test_betfair_retorno_em_formato_ingles
  4. tirar a exigência de linha partida no HL    → test_meia_derrota_exige_linha_partida
  5. escrever mesmo sem mudar o P/L              → test_nao_mexe_quando_o_dinheiro_nao_muda

Duas coisas que a rodada de mutação ensinou e que ficam registradas:

  • A mutação 2 ESCAPOU na primeira tentativa, e o defeito era do teste. Eu tinha exercido
    o caso "a IA já acertou HW", onde remover a fórmula não muda nada — porque `HW @ o` e
    `W @ (1+o)/2` pagam o MESMO valor, e o gate só escreve quando o P/L muda. O caso que
    prova a fórmula é o inverso: a IA escreveu W e o bilhete pagou meia vitória.
  • O lookbehind `(?<!potencial )` de `_RETORNO_TXT_RE` é MUTAÇÃO INÓCUA hoje: removê-lo
    não quebra nada, porque nenhum formato de casa escreve `retorno potencial <número>`
    colado. Não inventei asserção para ele — o porquê está em
    test_betfair_em_aberto_com_retorno_potencial_no_proprio_status.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

import repository as R  # noqa: E402

COL = ["05/09/2026", "Futebol", "LBB", "Bet365", "conta [Op]", "Gols",
       "Under 4.0 Gols [Loiske v TP-T]", "99,00", "1,975", "W", "KR4610093301I"]


def _linha(troca=None):
    p = list(COL)
    for i, v in (troca or {}).items():
        p[i] = v
    return "\t".join(p)


def _bloco(codigo="KR4610093301I", stake="99,00", status="Ganho → W (retorno R$ 195,53)",
           odd="1,975"):
    return (f"[Código: {codigo}]\n"
            f"Data (encerramento): 05/09/2026\n"
            f"Stake: {stake}\n"
            f"Status: {status}\n"
            f"Odd: {odd}\n"
            f"Esporte (casa): CL=1 (Futebol)\n"
            f"Seleções:\n"
            f"  • Loiske x TP-T · Gols + - · Menos de 4.0 @ {odd} · Finn Kolmonen\n")


def _saida(tsv, texto):
    out, info = R.corrigir_stake_tsv(tsv, texto)
    return out.split("\t"), info


# ── o caso que abriu a sessão ────────────────────────────────────────────────────────

def test_odd_errada_com_stake_certa():
    """O RETORNO gravado na coluna Odd. A stake está CERTA, e era isso que escondia o erro.

    MUTAÇÃO: mover o veredito para dentro do `if` da stake (o comportamento até a s321)
    faz este teste falhar — que é exatamente o bug que custou R$ 19.161,94 de P/L fantasma.
    """
    parts, info = _saida(_linha({8: "195,53"}), _bloco())
    assert parts[8] == "1,975", "a odd tem de voltar para a que o bloco imprime"
    assert parts[9] == "W"
    assert parts[7] == "99,00", "a stake estava certa e não pode ser tocada"
    assert info["financeiro"] == 1
    assert info["stakes"] == 0, "nenhuma stake divergia: o gate rodou por conta própria"


def test_odd_do_bloco_tem_preferencia_sobre_a_dizima():
    """`195,53 ÷ 99,00 = 1,9750505…`, mas o bloco imprime `1,975`. Vale o bloco.

    Preserva a precisão da casa (`MASTER_OUTPUT`: odd sem limite de casas) em vez de gravar
    a dízima que nasce do retorno arredondado ao centavo.
    """
    parts, _ = _saida(_linha({8: "195,53"}), _bloco())
    assert parts[8] == "1,975"


def test_cashout_grava_o_quociente_quando_a_odd_do_bloco_nao_bate():
    """Liam Lawson: stake 200, retorno 90,91, bloco imprime `Odd: 5`. É cashout → W."""
    tsv = _linha({6: "Liam Lawson - Sim [Grande Prémio da Itália - Top 6]",
                    7: "200,00", 8: "5", 9: "HL"})
    parts, info = _saida(tsv, _bloco(stake="200,00", odd="5",
                                     status="Ganho/perda parcial (retorno R$ 90,91 · a conferir HW/HL)"))
    assert parts[9] == "W", "meia derrota exige linha partida; aqui é cashout"
    assert parts[8] == "0,45455", "odd = retorno ÷ stake"
    assert info["financeiro"] == 1


# ── o que NÃO pode ser tocado ────────────────────────────────────────────────────────

def test_hw_legitimo_nao_vira_w():
    """`Under 3.0,3.5` com retorno de meia vitória.

    MUTAÇÃO: ler o rótulo do Status (`Ganho → W`) em vez da aritmética do retorno reescreve
    este bilhete como W. `_resultadoB3` chama de W qualquer retorno > stake, meia vitória
    inclusive — foram 14 bilhetes certos que quase viraram erro na varredura da s321.
    """
    # stake 99, odd 1,90 → HW paga (49,5 × 1,9) + 49,5 = 143,55; W cheio pagaria 188,10.
    tsv = _linha({6: "Under 3.0,3.5 Gols [A v B]", 8: "1,90", 9: "HW"})
    parts, info = _saida(tsv, _bloco(odd="1,90", status="Ganho → W (retorno R$ 143,55)"))
    assert parts[9] == "HW", "o retorno é de meia vitória, não de W cheio"
    assert info["financeiro"] == 0


def test_w_legitimo_passa_intacto():
    parts, info = _saida(_linha(), _bloco())
    assert parts[8] == "1,975" and parts[9] == "W"
    assert info["financeiro"] == 0


def test_w_que_era_hw_recebe_o_rotulo_hw_e_mantem_a_odd():
    """A IA escreveu W cheio num bilhete que pagou meia vitória. É onde a fórmula de HW
    é load-bearing — e o teste do HW já correto (acima) NÃO prova isso.

    Sem a fórmula de HW o veredito ainda acerta o DINHEIRO, porque `HW @ o` e
    `W @ (1+o)/2` pagam exatamente o mesmo: cairia no cashout e gravaria W com odd
    1,4501. O que se perde é o RÓTULO — e com ele a odd real da aposta, que vira um
    número derivado. Por isso a asserção é sobre as duas colunas, não sobre o P/L.
    """
    # stake 120,36, odd 1,90 → HW paga (60,18 × 1,9) + 60,18 = 174,52.
    tsv = _linha({6: "Under 3.0,3.5 Gols [A v B]", 7: "120,36", 8: "1,9", 9: "W"})
    parts, info = _saida(tsv, _bloco(stake="120,36", odd="1,9",
                                     status="Ganho → W (retorno R$ 174,53)"))
    assert parts[9] == "HW", "o retorno é de meia vitória"
    assert parts[8] == "1,9", "a odd da aposta continua sendo a da casa, não retorno÷stake"
    assert info["financeiro"] == 1


def test_nao_mexe_quando_o_dinheiro_nao_muda():
    """Retorno = stake/2 com linha partida lê como HL; a IA escreveu HL. P/L idêntico.

    MUTAÇÃO: trocar o corte de `abs(Δ P/L) >= 0.01` por "escreve sempre" faz o gate
    reescrever a odd com a dízima do quociente sem que nenhum número mude.
    """
    tsv = _linha({6: "Under 2,5/3,0 Gols [A v B]", 8: "1,875", 9: "HL"})
    parts, info = _saida(tsv, _bloco(odd="1,875", status="Ganho/perda parcial (retorno R$ 49,50)"))
    assert info["financeiro"] == 0
    assert parts[8] == "1,875" and parts[9] == "HL"


def test_aposta_em_aberto_nao_e_liquidada():
    """Liquidar aposta VIVA pelo valor que ela ainda poderia pagar é o pior estrago
    possível deste gate. Duas camadas independentes barram isso, e o teste exerce as duas.
    """
    aberto = _bloco(status="em aberto (aguardando resultado — NÃO liquidar; sem resultado)")
    aberto = aberto.replace("Odd: 1,975", "Odd: 1,975\nRetorno potencial: 195,53")
    parts, info = _saida(_linha({9: ""}), aberto)
    assert parts[9] == "" and info["financeiro"] == 0


def test_betfair_em_aberto_com_retorno_potencial_no_proprio_status():
    """O formato real da Betfair põe o valor potencial DENTRO da linha do Status:
    `em aberto (…) · Retorno POTENCIAL (ainda não realizado) 617.05` (32 blocos na sombra).

    É o único formato em que um número segue a palavra "Retorno" numa aposta viva. Ele não
    é capturado por dois motivos independentes: o `em aberto` barra em `_retorno_do_bloco`,
    e `POTENCIAL (ainda não realizado)` já quebra o padrão da regex antes do número.

    NOTA DE COBERTURA HONESTA: o lookbehind `(?<!potencial )` de `_RETORNO_TXT_RE` é uma
    TERCEIRA camada que nenhum formato de casa exerce hoje — removê-lo não quebra teste
    nenhum, e isso foi verificado por mutação, não suposto. Ele fica como defesa para uma
    casa futura que escreva `retorno potencial 617,05` colado; se um dia isso aparecer, é
    aqui que o caso deve entrar.
    """
    status = ("em aberto (aguardando resultado — NÃO liquidar; deixe Resultado VAZIO) · "
              "Retorno POTENCIAL (ainda não realizado) 617.05")
    parts, info = _saida(_linha({3: "Betfair", 9: ""}), _bloco(status=status))
    assert parts[9] == "" and info["financeiro"] == 0


def test_meia_derrota_exige_linha_partida():
    """Sem linha asiática partida, metade da stake de volta é CASHOUT, não HL.

    MUTAÇÃO: remover a exigência de `_LINHA_PARTIDA_RE` faz o gate aceitar HL em qualquer
    mercado — inclusive no Player Props de F1 que abriu esta sessão.
    """
    tsv = _linha({6: "Liam Lawson - Sim [GP da Itália - Top 6]", 8: "5", 9: "W"})
    parts, _ = _saida(tsv, _bloco(odd="5", status="Ganho/perda parcial (retorno R$ 49,50)"))
    assert parts[9] == "W"


# ── formatos de número por casa ──────────────────────────────────────────────────────

def test_betfair_retorno_em_formato_ingles():
    """A Betfair mistura BR e EN no MESMO bloco: stake `300,00`, retorno `1,642.38`.

    MUTAÇÃO: usar `_num_or_none` (BR-first) aqui lê 1,64238 e "corrige" a odd 5,4746 para
    0,0054 — cinco linhas certas destruídas na varredura da s321.
    """
    assert R._num_bloco("1,642.38") == 1642.38
    assert R._num_bloco("1.642,38") == 1642.38
    tsv = _linha({3: "Betfair", 7: "300,00", 8: "5,4746", 9: "W"})
    parts, info = _saida(tsv, _bloco(stake="300,00", odd="5,4746",
                                     status="WON → W · Retorno 1,642.38"))
    assert parts[8] == "5,4746" and info["financeiro"] == 0


def test_num_bloco_nao_confunde_odd_com_milhar():
    """`1,775` é odd, não mil setecentos e setenta e cinco.

    MUTAÇÃO: a regra "3 dígitos depois do separador = milhar" (correta para dinheiro)
    multiplica toda odd de 3 casas decimais por mil.
    """
    assert R._num_bloco("1,775") == 1.775
    assert R._num_bloco("120,36") == 120.36
    assert R._num_bloco("0.00") == 0.0


def test_perdido_sem_valor_vira_L():
    """Casa que escreve o rótulo sem número: os dois extremos ainda são deriváveis."""
    parts, info = _saida(_linha({9: "W"}), _bloco(status="Perdeu → L"))
    assert parts[9] == "L" and info["financeiro"] == 1


def test_devolvida_vira_V():
    parts, _ = _saida(_linha({9: "W"}), _bloco(status="Devolvida/void (retorno = stake) → V"))
    assert parts[9] == "V"


# ── fail-closed ──────────────────────────────────────────────────────────────────────

def test_bloco_sem_status_passa_intacto():
    sem = _bloco().replace("Status: Ganho → W (retorno R$ 195,53)\n", "")
    parts, info = _saida(_linha({8: "195,53"}), sem)
    assert parts[8] == "195,53" and info["financeiro"] == 0


def test_stake_ambigua_no_bloco_nao_autoriza_nada():
    """Dois `Stake:` no bloco = sem prova. Não corrige stake NEM financeiro."""
    ambiguo = _bloco().replace("Stake: 99,00", "Stake: 99,00\nStake: 777,00")
    parts, info = _saida(_linha({8: "195,53"}), ambiguo)
    assert parts[8] == "195,53"
    assert info["stakes"] == 0 and info["financeiro"] == 0


def test_linha_sem_codigo_passa_intacta():
    sem_codigo = "\t".join(list(COL)[:10])
    out, info = R.corrigir_stake_tsv(sem_codigo, _bloco())
    assert out == sem_codigo and info["financeiro"] == 0
