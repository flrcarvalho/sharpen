"""Gate do matcher por evidência (`app/matcher.py`, s289).

Trava os dois cortes de confiança que fazem o matcher se ABSTER — foram eles que levaram a
precisão de 75 % para ≥90 % na medição holdout, e os dois falham em silêncio se alguém os
afrouxar: o matcher continua respondendo, só que errado.

  · MARGEM       — confiança RELATIVA. Sem folga sobre o 2º colocado, fica vazio.
  · MAX_INEDITAS — confiança ABSOLUTA. Bilhete que não se parece com nada que o vencedor já
                   fez não é dele. É o corte que protege contra TIPSTER NOVO: quem não tem
                   histórico não concorre, e sem este corte todo bilhete dele é atribuído,
                   com margem alta, ao tipster conhecido mais parecido (na base do Gabriel
                   isso deu 138 erros num nome só).

O dado sintético aqui EXERCE as regras (a regra "teste verde não é teste que detecta" do
CLAUDE.md): os cenários têm empate real, tipster fora do treino e volume acima dos cortes.
Cada asserção foi provada por mutação: `python scripts/mutar_matcher.py` quebra o matcher de
propósito, uma mutação por vez, e exige que este arquivo passe a falhar (19/19 detectadas
na s289). Rode-o depois de mexer aqui — teste que não detecta a mutação não está testando nada.

O que este arquivo NÃO cobre: a rota HTTP (`POST /tipsters/sugerir`), a leitura do Postgres e
a qualidade estatística real — essa se mede com `scripts/backtest_matcher.py` contra a base.
"""
import math

import pytest

import matcher


def bilhete(casa="Bet365", esporte="Futebol", aposta="Múltipla", stake="100,00",
            descricao="A // B", tipster="X"):
    return {"casa": casa, "esporte": esporte, "aposta": aposta, "stake": stake,
            "descricao": descricao, "tipster": tipster}


def treino(**kw):
    """Um lote homogêneo, grande o bastante para o modelo ter o que dizer."""
    n = kw.pop("n", 200)
    return [bilhete(**kw) for _ in range(n)]


# ── features ────────────────────────────────────────────────────────────────────
def test_stake_string_br_e_numero_dao_a_mesma_feature():
    """O front manda "250,00" (string BR) e o Postgres devolve Decimal. float("250,00")
    estoura — se o parse quebrar, a assinatura de stake nunca casa e ninguém percebe."""
    a = matcher.features("Bet365", "Futebol", "ML", "1.234,50", "")
    b = matcher.features("Bet365", "Futebol", "ML", 1234.50, "")
    assert a == b
    assert "fim=q50" in a, "stake quebrada guarda os CENTAVOS (código de identidade)"


def test_final_da_stake_inteira_vira_feature():
    assert "fim=7" in matcher.features("X", "Y", "Z", "97,00", "")
    assert "fim=0" in matcher.features("X", "Y", "Z", "100,00", "")


def test_pernas_conta_o_separador_canonico():
    """` // ` é o único separador de seleção (MASTER_DESCRICAO §19). É o sinal que separa a
    múltipla de 3 pernas do SóChutes da dupla do Arrudex — nenhum perfil declara isso."""
    assert "pernas=3" in matcher.features("C", "E", "M", "", "A // B // C")
    assert "pernas=1" in matcher.features("C", "E", "M", "", "só uma")
    assert "pernas=0" in matcher.features("C", "E", "M", "", "")


def test_stake_ausente_nao_inventa_feature():
    f = matcher.features("C", "E", "M", "", "A")
    assert not [x for x in f if x.startswith(("fim=", "val=", "faixa="))]


# ── abstenção: confiança ABSOLUTA (MAX_INEDITAS) ────────────────────────────────
def test_bilhete_de_tipster_novo_nao_e_atribuido_a_quem_ja_existe():
    """O caso Fatuchex: um tipster entra na carteira e ainda não tem rótulo nenhum. Ele não
    concorre — e o bilhete dele NÃO pode cair no conhecido mais parecido."""
    m = matcher.treinar(treino(tipster="Antigo"))
    novo = matcher.sugerir(m, ["Antigo", "Novato"], "CasaNova", "Críquete", "Corridas",
                           "33,00", "algo // outro")
    assert novo is None


def test_bilhete_conhecido_do_unico_tipster_e_atribuido():
    """Contraprova do teste acima: sem ele, "não sugere nada" passaria como sucesso."""
    m = matcher.treinar(treino(tipster="Antigo"))
    assert matcher.sugerir(m, ["Antigo"], "Bet365", "Futebol", "Múltipla", "100,00", "A // B") == "Antigo"


def test_tipster_sem_historico_nao_rouba_a_folga_de_quem_tem():
    """Quem não tem histórico não entra no ranking — nem no fim dele.

    O guard `if not n: continue` parece só uma otimização, e não é: deixar o novato entrar
    com contagem 1 o coloca em 2º lugar e a folga do 1º passa a ser medida contra ELE. Com
    treino pequeno essa folga encolhe abaixo da margem e o matcher se ABSTÉM num bilhete que
    ele conhece. Medido: 11 divergências em 6.480 cenários, todas perdendo cobertura.

    O cenário abaixo é um deles — treino curto de propósito: com 200 bilhetes a folga é grande
    demais e a regra não seria exercida (dado sintético que não exerce a regra dá falso verde).
    """
    m = matcher.treinar(treino(tipster="Antigo", n=3))
    assert matcher.sugerir(m, ["Antigo", "Novato", "Outro"], "Bet365", "Futebol",
                           "Múltipla", "100,00", "A // B") == "Antigo"


def test_uma_feature_estavel_inedita_ja_basta_para_abster():
    """MAX_INEDITAS=0: o corte é NENHUMA inédita, não "poucas". Aqui só o mercado muda."""
    m = matcher.treinar(treino(tipster="Antigo"))
    assert matcher.sugerir(m, ["Antigo"], "Bet365", "Futebol", "MercadoQueEleNuncaFez",
                           "100,00", "A // B") is None


def test_casa_nova_NAO_abstem():
    """Tipster abrir conta numa casa nova é rotina — não é outro dono.

    Este é o caso do Bad Milton (s289): único de Badminton na carteira, vencia com folga 5,4 e
    era barrado porque nunca tinha apostado na Betboom. O corte disparava em NOVIDADE.
    """
    m = matcher.treinar(treino(tipster="Antigo"))
    assert matcher.sugerir(m, ["Antigo"], "CasaQueEleNuncaUsou", "Futebol", "Múltipla",
                           "100,00", "A // B") == "Antigo"


def test_valor_de_stake_novo_NAO_abstem():
    """Caso do Fatuch (s289): vencia com folga 8,5 num bilhete de final 7 e era barrado porque
    `val=147` era inédito. Valor exato é quase único por bilhete — contá-lo no corte fazia quase
    toda stake nova emudecer o matcher. O FINAL da stake continua contando (é a assinatura)."""
    m = matcher.treinar(treino(tipster="Antigo", stake="107,00"))
    assert matcher.sugerir(m, ["Antigo"], "Bet365", "Futebol", "Múltipla",
                           "147,00", "A // B") == "Antigo", "mesmo final 7, valor novo"


def test_final_de_stake_inedito_ainda_abstem():
    """Contraprova: `fim` NÃO está na lista de ignorados. Ele é a assinatura do tipster, e um
    final que ele nunca usou continua sendo motivo para não cravar."""
    m = matcher.treinar(treino(tipster="Antigo", stake="100,00"))
    assert matcher.sugerir(m, ["Antigo"], "Bet365", "Futebol", "Múltipla",
                           "97,00", "A // B") is None


# ── abstenção: confiança RELATIVA (MARGEM) ──────────────────────────────────────
def test_empate_entre_dois_donos_fica_vazio():
    """Dois tipsters com histórico IDÊNTICO: nada distingue, e chutar seria pior que a coluna
    vazia. O empate é real — os dois têm as mesmas features, então nenhum tem folga."""
    m = matcher.treinar(treino(tipster="A") + treino(tipster="B"))
    assert matcher.sugerir(m, ["A", "B"], "Bet365", "Futebol", "Múltipla", "100,00", "A // B") is None


def test_folga_clara_sugere():
    """Mesmo cenário do empate, mas o bilhete carrega a assinatura de um dos dois (o final 7
    da stake, que só o B usa). Aí há folga e o matcher decide."""
    m = matcher.treinar(treino(tipster="A") + treino(tipster="B", stake="97,00"))
    assert matcher.sugerir(m, ["A", "B"], "Bet365", "Futebol", "Múltipla", "97,00", "A // B") == "B"


def test_tipster_arquivado_nao_e_sugerido():
    """`ativos` é o pool. Tipster fora dele não volta por inferência, mesmo dominando o treino."""
    m = matcher.treinar(treino(tipster="Arquivado"))
    assert matcher.sugerir(m, [], "Bet365", "Futebol", "Múltipla", "100,00", "A // B") is None


def test_modelo_vazio_nao_sugere():
    assert matcher.sugerir(matcher.treinar([]), ["A"], "C", "E", "M", "10,00", "x") is None


# ── treino ──────────────────────────────────────────────────────────────────────
def test_treino_ignora_linha_sem_tipster():
    m = matcher.treinar(treino(n=10) + [bilhete(tipster="")] * 5 + [bilhete(tipster=None)] * 5)
    assert m.treino == 10


def test_cache_por_dono_e_invalidacao():
    m = matcher.treinar(treino())
    matcher.guardar_modelo("dono-teste", m)
    assert matcher.modelo_em_cache("dono-teste") is m
    matcher.invalidar("dono-teste")
    assert matcher.modelo_em_cache("dono-teste") is None


def test_cache_expira():
    m = matcher.treinar(treino())
    matcher.guardar_modelo("dono-ttl", m)
    matcher._CACHE["dono-ttl"] = (matcher._CACHE["dono-ttl"][0] - matcher.TTL_MODELO - 1, m)
    assert matcher.modelo_em_cache("dono-ttl") is None


# ── os cortes existem e valem ───────────────────────────────────────────────────
def test_constantes_de_confianca_nao_foram_afrouxadas():
    """Números medidos, não escolhidos: ver a docstring de `app/matcher.py`. Mexer neles é
    decisão que pede backtest novo (`scripts/backtest_matcher.py`), não ajuste fino no escuro."""
    assert matcher.MARGEM >= 2.5
    assert matcher.MAX_INEDITAS == 0
    assert matcher.MIN_TREINO >= 200


# ── esporte praticamente exclusivo (s289) ───────────────────────────────────────
# Feedback do Feca: "as do Bad Milton são muito fáceis de caracterizar, são as únicas do
# Badminton, não tem por que não categorizar". O modelo não via isso — um tipster que NUNCA
# fez Badminton ficava a 1,67 de log-odds e comia a folga.
DOM = {"badminton": ("Bad Milton", 44, 45)}   # 97,8 %… abaixo do corte de propósito
DOM_EXCLUSIVO = {"badminton": ("Bad Milton", 44, 44)}


def test_esporte_exclusivo_decide_antes_do_modelo():
    """Evidência direta ganha da inferência: o treino inteiro diz "Outro" e o esporte diz
    "Bad Milton"."""
    m = matcher.treinar(treino(tipster="Outro", esporte="Badminton"))
    assert matcher.sugerir(m, ["Outro", "Bad Milton"], "Betboom", "Badminton", "ML",
                           "300,00", "x", dominio=DOM_EXCLUSIVO) == "Bad Milton"


def test_esporte_exclusivo_decide_sem_modelo_nenhum():
    """Não depende de treino — o dono pode não ter histórico nenhum ainda."""
    assert matcher.sugerir(matcher.treinar([]), ["Bad Milton"], "Betboom", "Badminton", "ML",
                           "300,00", "x", dominio=DOM_EXCLUSIVO) == "Bad Milton"


def test_esporte_compartilhado_nao_decide():
    """PUREZA_ESPORTE: 44 de 60 é 73 % — o esporte é dele, mas não SÓ dele. Sem esta contraprova
    a regra viraria "crava o maior de qualquer esporte"."""
    assert matcher.dono_do_esporte({"badminton": ("Bad Milton", 44, 60)},
                                   "Badminton", ["Bad Milton"]) is None


def test_esporte_exclusivo_com_pouco_historico_nao_decide():
    """MIN_ESPORTE: exclusividade com 5 bilhetes é coincidência, não padrão."""
    assert matcher.dono_do_esporte({"badminton": ("Bad Milton", 5, 5)},
                                   "Badminton", ["Bad Milton"]) is None


def test_dono_do_esporte_arquivado_nao_decide():
    assert matcher.dono_do_esporte(DOM_EXCLUSIVO, "Badminton", ["Outro"]) is None


def test_dono_do_esporte_normaliza_o_nome():
    """A chave do domínio vem em minúsculas do SQL; o bilhete traz "Badminton"."""
    assert matcher.dono_do_esporte(DOM_EXCLUSIVO, "  BADMINTON ", ["Bad Milton"]) == "Bad Milton"


def test_sem_dominio_o_matcher_segue_igual():
    """`dominio` é opcional: quem não passa (backtest antigo, chamada solta) não muda de
    comportamento."""
    m = matcher.treinar(treino(tipster="Antigo"))
    assert matcher.sugerir(m, ["Antigo"], "Bet365", "Futebol", "Múltipla", "100,00", "A // B") == "Antigo"
    assert matcher.dono_do_esporte({}, "Badminton", ["Bad Milton"]) is None
    assert matcher.dono_do_esporte(None, "Badminton", ["Bad Milton"]) is None


def test_cortes_do_esporte_nao_foram_afrouxados():
    assert matcher.PUREZA_ESPORTE >= 0.98
    assert matcher.MIN_ESPORTE >= 25
