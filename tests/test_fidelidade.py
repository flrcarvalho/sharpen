"""Regressão do gate de FIDELIDADE da descrição (sessão 302).

O bug real (Betfair `O/25146258/0001941`): o bloco do robô dizia
`Norwich x Burnley · Mais/Menos de 3,5 Cartões` e a linha saiu
`Matthew Dennant [Norwich v Burnley]`, esporte Dardos, categoria ML — a seleção do
bilhete VIZINHO no mesmo chunk. Cobertura: 65 de 65, verde. `checar_descricao`: verde,
porque a FORMA é impecável. O defeito só existe na relação entre a linha e o bloco que
a gerou, e nada no sistema olhava para essa relação.

Os blocos deste arquivo são **verbatim da sombra de produção** (`sombra_rotulos`),
inclusive as armadilhas tipográficas que geraram falso positivo na primeira versão do
gate: o acento agudo de `St Patrick´s` (Pinnacle), o hífen com espaços de
`Ararat - Armênia` (1xBet) e o singular de `Tiro de meta` (1xBet). Copiar o trecho para
o teste em vez de trazer o real foi o que deixou a s286 verde sem detectar nada.

O QUE ESTES TESTES **NÃO** COBREM, e está escrito para o verde não virar promessa:
  • a chamada real ao modelo. `_repescar_faltantes` é substituída por uma função de
    roteiro — o que se prova aqui é a DECISÃO de trocar ou não, nunca que o modelo
    responde melhor na segunda vez (isso está medido na sombra, não em teste);
  • troca entre bilhetes que compartilham os mesmos nomes: duas apostas no mesmo jogo
    trocadas entre si PASSAM no gate, e é limitação declarada de `checar_fidelidade`;
  • rótulo traduzido para a categoria errada (`Vence o 3º Set` virando ML): ali nenhum
    token é estranho ao bloco, só falta um. Fica para a regra de período do
    `MASTER_DESCRICAO §12.8`.

MUTAÇÕES INÓCUAS (registradas em vez de inventar asserção para elas — as duas escaparam
na 1ª rodada e a investigação mostrou que o código segue CORRETO sem a linha mutada):
  • tirar o `not texto` de `_garantir_fidelidade`: `_blocos_por_codigo` já devolve {}
    para texto vazio, e o `if not blocos` logo abaixo faz o mesmo no-op. Guarda
    redundante, mantida por ser explícita e por evitar trabalho à toa.
  • tirar o `not codigo` de `_linhas_infieis`: `blocos.get("")` devolve None e a linha
    cai no mesmo `continue`; e `checar_fidelidade` com bloco vazio devolve []. Três
    defesas para a mesma coisa.
A 3ª que escapou era defeito DESTE arquivo, não do código — ver
`test_so_o_decimal_conta_como_linha_da_aposta`.
"""
import asyncio
import os
import sys

os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-nao-usada")

import database  # noqa: E402  (stub do conftest)
if not hasattr(database, "init_db"):
    async def _init_db():  # pragma: no cover - nunca chamado nos testes
        raise RuntimeError("DB indisponível nos testes")
    database.init_db = _init_db

import main  # noqa: E402
import descricao_check  # noqa: E402
from descricao_check import checar_fidelidade  # noqa: E402


# ── Blocos verbatim da sombra ────────────────────────────────────────────────

BLOCO_1941 = """[Código: O/25146258/0001941]
Data:
Apostado em: 29/08/2026
Esporte (casa): English Football · English Championship
Tipo: Simples
Stake: 301,00
Status: em aberto (aguardando resultado — NÃO liquidar; deixe Resultado VAZIO) · Retorno POTENCIAL (ainda não realizado) 617.05
Odd total: 2,05
Seleções:
  • Norwich x Burnley · Mais/Menos de 3,5 Cartões [OVER/UNDER_3.5_CARDS] · Mais de 3,5 cartões @ 2,05"""

BLOCO_1943 = """[Código: O/25146258/0001943]
Data:
Apostado em: 29/08/2026
Esporte (casa): Darts · MODUS Super Series
Tipo: Simples
Stake: 400,00
Status: em aberto (aguardando resultado — NÃO liquidar; deixe Resultado VAZIO)
Odd total: 1,83
Seleções:
  • Matthew Dennant x Steve Beaton · Resultado da partida [MATCH_ODDS] · Matthew Dennant @ 1,83"""

BLOCO_1938 = """[Código: O/25146258/0001938]
Data: 29/08/2026
Apostado em: 28/08/2026
Tipo: Múltipla
Stake: 300,00
Status: WON → W · Retorno 1,642.38
Odd total: 5,4746 (= Retorno ÷ Stake)
Seleções:
  • Lawrence Lui x Hector Santiago · Resultado da luta · Hector Santiago
  • Lawrence Lui x Hector Santiago · Vai até o Final? · Não"""

# Pinnacle: acento agudo tipográfico (U+00B4) no bloco, apóstrofo reto na descrição.
BLOCO_PINNACLE = """[Código: 3109545432]
Data: 28/08/2026
Apostado em: 25/08/2026
Stake: 100,00
Odd total: 8,500
Esporte (casa): Soccer · Irlanda - Premier
Seleções:
  • St Patrick´s Athletic (-3) Handicap de 3 vias St Patrick´s Athletic x Waterford"""

# 1xBet: hífen com espaços no bloco; e `Tiro de meta` no singular.
BLOCO_1XBET = """[Código: 16163249]
Data (evento): 29/08/2026 02:15:00
Stake: 180,00
Tipo: Múltipla (3 seleções)
Odd: 8,246
Seleções:
1. Atletico Ottawa - Inter Toronto // Total Acima de 2.5 @ 1,9
2. Tiro de meta Crystal Palace - Tiro de meta Manchester City // Total Abaixo de 14.5 @ 2,1
3. Impedimentos Ararat - Armênia - Impedimentos CS Universitatea Craiova // Total Abaixo de 1.5 @ 2,0"""

# Bet365: linha asiática PARTIDA. `4,25` é a média — número que ninguém escreveu.
BLOCO_BET365 = """[Código: KS5481466811I]
Data: 28/08/2026
Stake: 50,00
Odd total: 1,975
Seleções:
  • Auckland United (F) x Fencibles United (F) · Gols + - · Menos de 4.0,4.5 @ 1,975 · NZ-NRFL-PD-WOM"""


# ── checar_fidelidade: a função pura ─────────────────────────────────────────

def _regras(problemas):
    return {p.regra for p in problemas}


def test_carryover_de_nome_e_pego():
    """O caso que abriu a regra: seleção do bilhete vizinho."""
    probs = checar_fidelidade("Matthew Dennant [Norwich v Burnley]", BLOCO_1941)
    assert "nome-fora-do-bloco" in _regras(probs)
    assert "Matthew" in probs[0].msg


def test_descricao_correta_passa():
    assert checar_fidelidade("Over 3.5 Cartões [Norwich v Burnley]", BLOCO_1941) == []


def test_a_mesma_descricao_passa_no_bloco_a_que_pertence():
    """Prova que o gate mede PROCEDÊNCIA, não a descrição em si: o texto que reprova
    no 1941 é o texto legítimo do 1943."""
    assert checar_fidelidade("Matthew Dennant [Matthew Dennant v Steve Beaton]",
                             BLOCO_1943) == []


def test_numero_inventado_e_pego():
    """`Vai até o Final? · Não` virou `Under 1.5 Rounds` — o 1.5 veio do vizinho."""
    probs = checar_fidelidade(
        "Hector Santiago [Lawrence Lui v Hector Santiago] // "
        "Under 1.5 Rounds [Lawrence Lui v Hector Santiago]", BLOCO_1938)
    assert "linha-fora-do-bloco" in _regras(probs)


def test_media_de_linha_asiatica_partida_e_pega():
    """Bet365: `Menos de 4.0,4.5` virou `Under 4,25` — a IA calculou a média."""
    probs = checar_fidelidade("Under 4,25 Gols [Auckland United (F) v Fencibles United (F)]",
                              BLOCO_BET365)
    assert "linha-fora-do-bloco" in _regras(probs)


def test_inteiro_solto_nao_e_cobrado():
    """`Race 7`, `2º Tempo`: a tradução introduz inteiro legitimamente. Só o DECIMAL
    é a linha da aposta."""
    assert checar_fidelidade("Over 3.5 Cartões 2º Tempo [Norwich v Burnley]",
                             BLOCO_1941) == []


def test_so_o_decimal_conta_como_linha_da_aposta():
    """Contrato do `_RE_DECIMAL`, e ele é load-bearing por um motivo que o teste de
    comportamento acima NÃO consegue exercer.

    A conferência de número é por SUBSTRING (`'2' in '2.05'` é verdadeiro). Então
    inteiro curto quase sempre "existe" no bloco por acidente — o `2` de `2º Tempo`
    é achado dentro de `Odd total: 2,05`, e a checagem passaria mesmo cobrando
    inteiros. Cobrar inteiro não deixa o teste vermelho; deixa o gate ERRADO em
    produção, no bilhete cujo bloco por acaso não tem aquele dígito. Por isso a
    fronteira é travada aqui, direto: decimal sim, inteiro nunca.
    """
    achados = descricao_check._RE_DECIMAL.findall(
        "Over 3.5 Cartões 2º Tempo · Race 7 · Under 1,5 Gols")
    assert achados == ["3.5", "1,5"]


# ── Os três falsos positivos que a 1ª versão do gate produzia ────────────────

def test_acento_agudo_tipografico_nao_e_falso_positivo():
    """`St Patrick´s` (U+00B4) no bloco × `St Patrick's` (U+0027) na descrição."""
    assert checar_fidelidade("St Patrick's Athletic -3 [St Patrick's Athletic v Waterford]",
                             BLOCO_PINNACLE) == []


def test_hifen_com_espacos_nao_e_falso_positivo():
    """A 1xBet escreve `Ararat - Armênia`; a IA devolve `Ararat-Armênia`."""
    assert checar_fidelidade("Under 1.5 Impedimentos [Ararat-Armênia v CS Universitatea Craiova]",
                             BLOCO_1XBET) == []


def test_plural_nao_e_falso_positivo():
    """A 1xBet escreve `Tiro de meta`; a IA devolve `Tiros de Meta`."""
    assert checar_fidelidade("Under 14.5 Tiros de Meta [Crystal Palace v Manchester City]",
                             BLOCO_1XBET) == []


def test_sem_bloco_cala():
    """Sem bloco não há o que comparar — o gate nunca inventa suspeita."""
    assert checar_fidelidade("Qualquer Coisa [A v B]", "") == []
    assert checar_fidelidade("", BLOCO_1941) == []


# ── _blocos_por_codigo / _linhas_infieis: o recorte ──────────────────────────

TEXTO = "\n\n".join([BLOCO_1943, BLOCO_1941])


def _linha(codigo, descricao, esporte="Futebol", aposta="Cartões"):
    return "\t".join(["29/08/2026", esporte, "", "Betfair", "Duka [Eu]", aposta,
                      descricao, "301,00", "2,05", "", codigo])


def _tsv(*linhas):
    return "```tsv\n" + "\n".join((main._TSV_HEADER,) + linhas) + "\n```"


def test_blocos_por_codigo_indexa_pelo_marcador():
    blocos = main._blocos_por_codigo(TEXTO)
    assert set(blocos) == {"O/25146258/0001941", "O/25146258/0001943"}
    assert "Norwich x Burnley" in blocos["O/25146258/0001941"]
    assert "Norwich" not in blocos["O/25146258/0001943"]


def test_casa_sem_marcador_vira_noop():
    assert main._blocos_por_codigo("bilhete sem marcador nenhum\nStake: 10") == {}


def test_linhas_infieis_aponta_so_a_errada():
    tsv = _tsv(
        _linha("O/25146258/0001943", "Matthew Dennant [Matthew Dennant v Steve Beaton]",
               "Dardos", "ML"),
        _linha("O/25146258/0001941", "Matthew Dennant [Norwich v Burnley]", "Dardos", "ML"),
    )
    suspeitos = main._linhas_infieis(tsv, main._blocos_por_codigo(TEXTO))
    assert list(suspeitos) == ["O/25146258/0001941"]


def test_linha_sem_codigo_nao_entra():
    """Coluna 11 vazia = nada com que parear. Não pode virar suspeita."""
    sem_cod = "\t".join(["29/08/2026", "Dardos", "", "Betfair", "Duka [Eu]", "ML",
                         "Matthew Dennant [Norwich v Burnley]", "301,00", "2,05", "", ""])
    assert main._linhas_infieis(_tsv(sem_cod), main._blocos_por_codigo(TEXTO)) == {}


# ── _garantir_fidelidade: a decisão de trocar ────────────────────────────────

CERTA_1941 = _linha("O/25146258/0001941", "Over 3.5 Cartões [Norwich v Burnley]")
ERRADA_1941 = _linha("O/25146258/0001941", "Matthew Dennant [Norwich v Burnley]",
                     "Dardos", "ML")
BOA_1943 = _linha("O/25146258/0001943",
                  "Matthew Dennant [Matthew Dennant v Steve Beaton]", "Dardos", "ML")


def _rodar(tsv, resposta_da_repescagem, monkeypatch):
    """Roda o gate com a chamada ao modelo substituída por um roteiro fixo."""
    async def _fake(system, texto, faltantes, modelo, instrucao_block):
        _fake.pedidos = list(faltantes)
        return list(resposta_da_repescagem), {"input": 0, "output": 0,
                                              "cache_read": 0, "cache_write": 0}
    _fake.pedidos = []
    monkeypatch.setattr(main, "_repescar_faltantes", _fake)
    out = asyncio.run(main._garantir_fidelidade([], tsv, TEXTO, "m", {"type": "text", "text": "i"}))
    return out + (_fake,)


def test_repescagem_troca_a_linha_infiel(monkeypatch):
    tsv = _tsv(BOA_1943, ERRADA_1941)
    resultado, fid, _tok, fake = _rodar(tsv, [CERTA_1941], monkeypatch)
    assert fake.pedidos == ["O/25146258/0001941"], "só o suspeito volta ao modelo"
    assert fid["corrigidas"] == 1 and fid["restantes"] == 0
    assert "Over 3.5 Cartões [Norwich v Burnley]" in resultado
    assert "Matthew Dennant [Norwich v Burnley]" not in resultado
    assert BOA_1943 in resultado, "a linha que passava não pode ser tocada"


def test_repescagem_que_volta_errada_nao_substitui(monkeypatch):
    """Conservadora: se a segunda leitura também reprova, a linha antiga fica e o
    operador é avisado. Nunca troca errado por errado."""
    outra_errada = _linha("O/25146258/0001941", "Steve Beaton [Norwich v Burnley]",
                          "Dardos", "ML")
    tsv = _tsv(ERRADA_1941)
    resultado, fid, _tok, _fake = _rodar(tsv, [outra_errada], monkeypatch)
    assert fid["corrigidas"] == 0 and fid["restantes"] == 1
    assert "Matthew Dennant [Norwich v Burnley]" in resultado
    assert fid["exemplos"][0]["codigo"] == "O/25146258/0001941"


def test_lote_limpo_nao_chama_o_modelo(monkeypatch):
    """Custo: sem suspeita não há repescagem. O gate é de graça no caso normal."""
    chamou = []

    async def _nunca(*a, **k):  # pragma: no cover - o teste falha se rodar
        chamou.append(1)
        return [], {}
    monkeypatch.setattr(main, "_repescar_faltantes", _nunca)
    tsv = _tsv(BOA_1943, CERTA_1941)
    resultado, fid, _tok = asyncio.run(
        main._garantir_fidelidade([], tsv, TEXTO, "m", {"type": "text", "text": "i"}))
    assert not chamou
    assert fid == {"suspeitas": 0, "corrigidas": 0, "restantes": 0, "exemplos": []}
    assert resultado == tsv


def test_sem_texto_fonte_vira_noop(monkeypatch):
    """Print e casa sem marcador: nada a fazer, e nada pago."""
    async def _nunca(*a, **k):  # pragma: no cover
        raise AssertionError("não pode repescar sem texto-fonte")
    monkeypatch.setattr(main, "_repescar_faltantes", _nunca)
    tsv = _tsv(ERRADA_1941)
    resultado, fid, _tok = asyncio.run(
        main._garantir_fidelidade([], tsv, None, "m", {"type": "text", "text": "i"}))
    assert resultado == tsv and fid["suspeitas"] == 0
