# -*- coding: utf-8 -*-
"""Gate do export anonimizado do /realtrial (`scripts/realtrial/exportar.py`).

O QUE ESTE ARQUIVO **NAO** COBRE, para o verde nao virar promessa falsa:
  · nao toca o banco -- `ler_tudo` nao e' exercitada em lugar nenhum. Schema
    que mude de forma passa por aqui sem um arranhao.
  · nao prova que a IMPORTACAO funciona (Fatia 2, ainda nao escrita).
  · nao prova nada sobre re-identificacao por quem JA TEM as bases originais:
    data, casa e descricao viajam verbatim de proposito, e isso e' decisao de
    produto, nao defeito a detectar.

O que ele cobre, e cada caso nasceu de defeito MEDIDO na s352:
  · loop infinito quando ha codigo de bilhete (o `_counter` nao entra no hash)
  · codigo ficticio que nao era deterministico nem unico
  · nome ficticio colidindo com nome real ("Duplo Alto", "Marlon Alves")
  · varredura por substring acusando 21 inocentes ("Beta" dentro de "Betano")
  · conversao BR de stake, onde a regra de milhar errada multiplica por mil
"""
import pathlib
import sys
from decimal import Decimal

import pytest

RAIZ = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "app"))
sys.path.insert(0, str(RAIZ / "scripts" / "realtrial"))

import exportar as ex  # noqa: E402

MEIO = Decimal("0.5")


# ── dinheiro ─────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("txt,esperado", [
    ("250,00", "250.00"),          # forma dominante: 48.770 de 48.885
    ("1.234,56", "1234.56"),       # milhar BR: 111 linhas
    ("250", "250"),                # inteiro: 3 linhas
    ("250.50", "250.50"),          # ponto com 2 casas = decimal EN: 1 linha
])
def test_num_br_le_as_quatro_formas_medidas(txt, esperado):
    assert ex.num_br(txt) == Decimal(esperado)


def test_ponto_com_tres_digitos_e_milhar_nao_decimal():
    """A regra "3 digitos = milhar" vale para dinheiro. Ler "1.234" como
    decimal dividiria a stake por mil -- e a linha passaria sem erro nenhum."""
    assert ex.num_br("1.234") is None, "ambiguo demais para adivinhar: recusa"
    assert ex.num_br("1.234,00") == Decimal("1234.00")


def test_escalar_preserva_valor_ilegivel_em_vez_de_zerar():
    """Zero se disfarca de conta feita: valor ilegivel fica verbatim."""
    assert ex.escalar("nao e numero", MEIO) == "nao e numero"
    assert ex.escalar("", MEIO) == ""


def test_escalar_mantem_stake_redonda_redonda():
    """O fator 0,5 foi escolhido para isso: stake redonda e' sinal que o
    matcher de tipster usa, e fator quebrado apagaria a assinatura."""
    for bruto, esperado in (("100,00", "50,00"), ("250,00", "125,00"),
                            ("500,00", "250,00")):
        assert ex.escalar(bruto, MEIO) == esperado


# ── codigo de bilhete ────────────────────────────────────────────────────────
def test_codigo_e_deterministico_para_o_mesmo_codigo_real():
    """Sem isso o mesmo bilhete visto duas vezes deixa de ser o mesmo bilhete
    e a dedup por ID para de funcionar."""
    c = ex.CodigoFake(1)
    assert c.traduzir("ABC123") == c.traduzir("ABC123")


def test_codigo_preserva_forma():
    c = ex.CodigoFake(1)
    saida = c.traduzir("SP8399910931W")
    assert len(saida) == len("SP8399910931W")
    assert [ch.isdigit() for ch in saida] == [ch.isdigit() for ch in "SP8399910931W"]


def test_codigo_unico_mesmo_com_espaco_minusculo():
    """MEDIDO: 31 bilhetes tem codigo de 1-2 caracteres, onde cabem 10 e 100
    valores. Com codigo na mao a assinatura NAO tem desempate, entao codigo
    repetido nao e' colisao boba: e' bilhete que some no UNIQUE do import.

    MUTACAO QUE ESCAPA, de proposito: tirar a extensao de molde do
    `CodigoFake` nao quebra teste nenhum, e nao ha teste honesto que a pegue.
    Para um molde de k letras e m digitos existem 26^k x 10^m saidas possiveis
    e, no MAXIMO, esse mesmo tanto de codigos reais com aquela forma -- o
    espaco nunca esgota de verdade. A extensao so entra num sorteio azarado
    alem de 300 tentativas (probabilidade da ordem de 1e-14). E' defesa
    redundante, nao buraco de cobertura; inventar assercao para ela seria
    fabricar verde."""
    c = ex.CodigoFake(7)
    saidas = {c.traduzir(str(i)) for i in range(60)}
    assert len(saidas) == 60, "codigo ficticio repetiu"


def test_codigo_vazio_continua_vazio():
    """Coluna 11 vazia e' legitima (print, texto colado): inventar codigo ali
    criaria identidade onde a casa nao da nenhuma."""
    assert ex.CodigoFake(1).traduzir("") == ""


# ── nomes ────────────────────────────────────────────────────────────────────
def test_limite_de_palavra_nao_casa_dentro_de_palavra():
    """A 1a varredura usava substring solta e acusou 21 inocentes: um tipster
    "Beta" casando em "Betano" 8.372 vezes, "Feca" dentro do hash da
    assinatura, "Samu" em "Samuel Silvera"."""
    assert not ex._re_nome("Beta").search(ex._sem_acento("Betano"))
    assert not ex._re_nome("Samu").search(ex._sem_acento("Samuel Silvera"))
    assert not ex._re_nome("Feca").search("ba9b58844feca9774b5b")
    assert ex._re_nome("Beta").search(ex._sem_acento("aposta do Beta hoje"))


def test_acento_nao_esconde_o_nome():
    assert ex._re_nome("Só Chutes").search(ex._sem_acento("Multipla So Chutes"))


def test_anonimizador_recusa_ficticio_que_contenha_nome_real():
    """MEDIDO: havia tipster real "Duplo" e o pool trazia a palavra, gerando
    "Duplo Alto" -- ficticio que cita gente de verdade. Filtrar dois nomes a
    mao nao fecha a familia; recusar na GERACAO fecha."""
    proibidos = {"Duplo", "MARLON", "Beta"}
    anon = ex.Anonimizador(99, proibidos=proibidos)
    gerados = [anon.traduzir("tipster", f"real-{i}") for i in range(80)]
    gerados += [anon.traduzir("conta", f"conta-{i}") for i in range(80)]
    for g in gerados:
        for p in proibidos:
            assert not ex._re_nome(p).search(ex._sem_acento(g)), f"{g} cita {p}"


def test_mapa_e_deterministico_e_injetivo():
    a1 = ex.Anonimizador(5)
    a2 = ex.Anonimizador(5)
    assert a1.traduzir("tipster", "X") == a2.traduzir("tipster", "X")
    nomes = [a1.traduzir("tipster", f"t{i}") for i in range(50)]
    assert len(set(nomes)) == 50, "dois tipsters reais viraram o mesmo ficticio"


def test_conta_do_mesmo_nome_em_donos_diferentes_nao_funde():
    """Sao duas contas reais distintas; fundi-las juntaria as duas operacoes."""
    anon = ex.Anonimizador(3)
    a = ex.traduzir_parceiro(anon, "Feca", "Fulano [Norte]")
    b = ex.traduzir_parceiro(anon, "Jonathan", "Fulano [Norte]")
    assert a != b


def test_fornecedor_e_o_mesmo_entre_donos():
    """O fornecedor atende os dois, e e' assim que a tela de Fornecedores
    continua agrupando o que agrupava."""
    anon = ex.Anonimizador(3)
    a = ex.traduzir_parceiro(anon, "Feca", "Um [Norte]")
    b = ex.traduzir_parceiro(anon, "Jonathan", "Outro [Norte]")
    assert a.split("[")[1] == b.split("[")[1]


def test_parceiro_sem_colchete_preserva_a_forma():
    anon = ex.Anonimizador(3)
    assert "[" not in ex.traduzir_parceiro(anon, "Feca", "conta-sem-fornecedor")


def test_email_some_do_nome_da_conta():
    """63 das 90 contas do Jonathan tem e-mail real no nome -- o dado mais
    identificavel da base inteira."""
    anon = ex.Anonimizador(3)
    assert "@" not in ex.traduzir_parceiro(anon, "Jonathan", "alguem@gmail.com [Norte]")


# ── descricao ────────────────────────────────────────────────────────────────
def test_troca_rotulo_interno_na_descricao():
    """MEDIDO: "Arrudex 1", "Multipla So Chutes" e "Pessoal" estavam escritos
    como descricao -- rotulo interno no lugar do evento."""
    trocas = [(ex._re_nome("Arrudex"), "Linha Fria")]
    assert ex.limpar_descricao("Arrudex 1", trocas) == "Linha Fria 1"


def test_troca_preserva_acento_e_caixa_do_resto():
    """A descricao e' comparada com o bloco cru por `checar_fidelidade`: o que
    nao e' o nome trocado tem de sair identico."""
    trocas = [(ex._re_nome("Zora"), "Base Fria")]
    saida = ex.limpar_descricao("Zora - Over 2,5 Gols [Grêmio v Ceará]", trocas)
    assert saida == "Base Fria - Over 2,5 Gols [Grêmio v Ceará]"


def test_nome_publico_nao_e_trocado_na_descricao():
    """Badminton, Marlon Tolic e Moriyama Samurai sao o EVENTO. Trocar ali
    destruiria a descricao sem proteger ninguem."""
    for pub in ("badminton", "marlon", "samurai"):
        assert pub in ex._NOMES_PUBLICOS


# ── conferencia: ela precisa DETECTAR, nao so passar ─────────────────────────
def _origem():
    return {
        "bilhetes": [
            {"casa": "Bet365", "parceiro": "Fulano [Norte]", "data": "01/02/2026",
             "esporte": "Futebol", "tipster": "Tipster Real", "aposta": "ML",
             "descricao": "A x B", "stake": "100,00", "odd": "2,00",
             "resultado": "W", "extraction_state": "resolvida",
             "codigo_bilhete": "AB123", "archived": False, "sistema": None,
             "sistema_linhas": None, "criado_em": None, "dono": "Feca"},
            {"casa": "Bet365", "parceiro": "Fulano [Norte]", "data": "02/02/2026",
             "esporte": "Futebol", "tipster": "Tipster Real", "aposta": "ML",
             # o codigo deste bilhete aparece TAMBEM dentro da descricao: e'
             # a forma exata dos 63 casos medidos na base real.
             "descricao": "C x D #20493487958", "stake": "200,00", "odd": "3,00",
             "resultado": "L", "extraction_state": "resolvida",
             "codigo_bilhete": "20493487958", "archived": False, "sistema": None,
             "sistema_linhas": None, "criado_em": None, "dono": "Feca"},
        ],
        "parceiros": [{"dono": "Feca", "casa": "Bet365", "nome": "Fulano [Norte]",
                       "arquivado": False, "adquirida_em": None, "arquivada_em": None}],
        "tipsters": [{"dono": "Feca", "nome": "Tipster Real", "casas": None,
                      "mercados": None, "obs": "grupo do zap", "arquivado": False,
                      "stake_min": 50.0, "stake_max": 500.0, "apelidos": "@canal",
                      "dica_stake": "unidade 500"}],
        "custos": [],
        "donos_sistema": ["germano", "Jonathan", "Feca"],
    }


def test_export_limpo_passa():
    origem = _origem()
    saida = ex.transformar(origem, MEIO, 42)
    assert ex.conferir(origem, saida, MEIO) == []


def test_texto_livre_do_tipster_nao_viaja():
    """`obs`, `apelidos` e `dica_stake` sao escritos por humano: e' onde mora
    telefone, @ de canal e nome de grupo. Nao ha como anonimizar texto livre
    com garantia, entao nao viaja."""
    saida = ex.transformar(_origem(), MEIO, 42)
    t = saida["tipsters"][0]
    assert t["obs"] is None and t["apelidos"] is None and t["dica_stake"] is None


def test_stake_min_max_do_tipster_escala_junto():
    """Escalar a stake e deixar a faixa do tipster em escala real faria todo
    bilhete cair fora da faixa -- a mesma familia de "blindar metade"."""
    saida = ex.transformar(_origem(), MEIO, 42)
    assert saida["tipsters"][0]["stake_min"] == pytest.approx(25.0)
    assert saida["tipsters"][0]["stake_max"] == pytest.approx(250.0)


# As tres mutacoes abaixo QUEBRAM o dado de proposito. Se a conferencia passar
# em qualquer uma delas, o gate e' falso verde.
def test_mutacao_roi_alterado_e_detectado():
    origem = _origem()
    saida = ex.transformar(origem, MEIO, 42)
    saida["bilhetes"][0]["stake"] = "999,00"      # muda o ROI
    assert ex.conferir(origem, saida, MEIO), "ROI adulterado passou"


def test_mutacao_nome_real_vazado_e_detectado():
    origem = _origem()
    saida = ex.transformar(origem, MEIO, 42)
    saida["bilhetes"][0]["tipster"] = "Tipster Real"
    assert ex.conferir(origem, saida, MEIO), "nome real em campo anonimizado passou"


def test_mutacao_email_e_detectado():
    origem = _origem()
    saida = ex.transformar(origem, MEIO, 42)
    saida["parceiros"][0]["nome"] = "alguem@gmail.com [Vega]"
    assert ex.conferir(origem, saida, MEIO), "e-mail vazado passou"


def test_mutacao_assinatura_duplicada_e_detectada():
    origem = _origem()
    saida = ex.transformar(origem, MEIO, 42)
    saida["bilhetes"][1]["casa"] = saida["bilhetes"][0]["casa"]
    saida["bilhetes"][1]["parceiro"] = saida["bilhetes"][0]["parceiro"]
    saida["bilhetes"][1]["assinatura"] = saida["bilhetes"][0]["assinatura"]
    assert ex.conferir(origem, saida, MEIO), "assinatura duplicada passou"


def test_transformar_nao_trava_com_codigo_repetido_na_mesma_conta():
    """O defeito que travou a 1a rodada: com codigo, `_assinatura` ignora o
    `_counter`, entao procurar contador livre e' loop infinito. Hoje isso
    levanta erro; o que nao pode e' PENDURAR."""
    origem = _origem()
    origem["bilhetes"][1]["codigo_bilhete"] = origem["bilhetes"][0]["codigo_bilhete"]
    try:
        ex.transformar(origem, MEIO, 42)
    except RuntimeError:
        pass  # abortar e' aceitavel; travar nao e'

# ── codigo real e rotulo interno DENTRO da descricao ─────────────────────────
def test_codigo_real_citado_na_descricao_e_trocado():
    """MEDIDO: 63 bilhetes trazem o codigo colado no texto (`... #20493487958`).
    Anonimizar so a COLUNA deixava intacto o ultimo elo capaz de casar a linha
    publica com o bilhete real na casa."""
    origem = _origem()
    saida = ex.transformar(origem, MEIO, 42)
    descs = " ".join(b["descricao"] or "" for b in saida["bilhetes"])
    assert "20493487958" not in descs


def test_rotulo_interno_com_nome_de_dono_sai():
    """"Multipla Germano" e' rotulo interno escrito no lugar do evento."""
    origem = _origem()
    origem["bilhetes"][0]["descricao"] = "Multipla Germano"
    saida = ex.transformar(origem, MEIO, 42)
    assert "germano" not in ex._sem_acento(saida["bilhetes"][0]["descricao"])


def test_nome_de_dono_que_e_ATLETA_fica():
    """Dos 324 casos medidos, 322 eram atleta: "Jonathan David [Suica v
    Canada]", "Gabriel Diallo". Trocar ali destruiria a descricao do evento.
    A FORMA e' o discriminador: com confronto, e' evento."""
    origem = _origem()
    origem["bilhetes"][0]["descricao"] = "Jonathan David [Suíça v Canadá]"
    saida = ex.transformar(origem, MEIO, 42)
    assert saida["bilhetes"][0]["descricao"] == "Jonathan David [Suíça v Canadá]"


def test_parece_evento_separa_os_dois_casos():
    assert ex.parece_evento("Jonathan David [Suíça v Canadá]")
    assert ex.parece_evento("Over 2,5 // Under 1,5")
    assert not ex.parece_evento("Multipla Germano")
    assert not ex.parece_evento("Arrudex 1")


def test_mutacao_codigo_real_na_descricao_e_detectada():
    origem = _origem()
    saida = ex.transformar(origem, MEIO, 42)
    saida["bilhetes"][0]["descricao"] = "A x B #20493487958"
    assert ex.conferir(origem, saida, MEIO), "codigo real na descricao passou"


def test_mutacao_rotulo_interno_e_detectado():
    origem = _origem()
    saida = ex.transformar(origem, MEIO, 42)
    saida["bilhetes"][0]["descricao"] = "Multipla Germano"
    assert ex.conferir(origem, saida, MEIO), "rotulo interno passou"


def test_identificador_que_nunca_virou_coluna_tambem_sai():
    """A 1a correcao pegou so metade: procurava codigo que EXISTE na coluna
    `codigo_bilhete`. MEDIDO: 495 bilhetes citam identificador que nunca virou
    coluna (`Multipla - #291310574`, `Simples - #291367894`, e alguns em que o
    numero E' a descricao inteira). A regra e por FORMA: so-digitos com 7+."""
    origem = _origem()
    origem["bilhetes"][0]["descricao"] = "Múltipla - #291310574"
    origem["bilhetes"][0]["codigo_bilhete"] = ""
    saida = ex.transformar(origem, MEIO, 42)
    assert "291310574" not in (saida["bilhetes"][0]["descricao"] or "")


def test_numero_curto_do_evento_nao_e_tocado():
    """Odd, linha, placar e minuto tem 1 a 4 digitos: trocar ali destruiria a
    descricao. O piso de 7 existe para isso."""
    origem = _origem()
    origem["bilhetes"][0]["descricao"] = "Over 2.5 Gols 1º Tempo [A v B] 3-0 aos 45"
    saida = ex.transformar(origem, MEIO, 42)
    assert saida["bilhetes"][0]["descricao"] == "Over 2.5 Gols 1º Tempo [A v B] 3-0 aos 45"


def test_alfanumerico_sem_codigo_conhecido_fica():
    """`4ikibabmoni` e' nome de jogador de e-sports. A forma nao discrimina
    alfanumerico, entao ali so se troca o que bate com codigo conhecido."""
    origem = _origem()
    origem["bilhetes"][0]["descricao"] = "Mapa 1 [4ikibabmoni v outro]"
    saida = ex.transformar(origem, MEIO, 42)
    assert "4ikibabmoni" in saida["bilhetes"][0]["descricao"]


def test_mutacao_identificador_solto_e_detectado():
    origem = _origem()
    origem["bilhetes"][0]["descricao"] = "Múltipla - #291310574"
    saida = ex.transformar(origem, MEIO, 42)
    saida["bilhetes"][0]["descricao"] = "Múltipla - #291310574"
    assert ex.conferir(origem, saida, MEIO), "identificador solto passou"


def test_codigo_alfanumerico_de_bilhete_POSTERIOR_tambem_e_trocado():
    """Prova a PASSADA 1 (traduzir todos os codigos antes de limpar descricao).

    O codigo de um bilhete aparece no texto de OUTRO, e nada garante que o dono
    do codigo venha primeiro. Alfanumerico nao e' pego pela regra de forma
    (`_RE_SO_DIGITOS`), entao depende do mapa estar COMPLETO: montar o mapa na
    mesma passada deixaria de fora todo codigo ainda nao visto, em silencio.
    Codigo nativo de casa existe de verdade -- a Superbet grava `SP8399910931W`.
    """
    origem = _origem()
    origem["bilhetes"][0]["descricao"] = "A x B ref SP8399910931W"
    origem["bilhetes"][0]["codigo_bilhete"] = "AB123"
    origem["bilhetes"][1]["codigo_bilhete"] = "SP8399910931W"
    origem["bilhetes"][1]["descricao"] = "C x D"
    saida = ex.transformar(origem, MEIO, 42)
    assert "SP8399910931W" not in (saida["bilhetes"][0]["descricao"] or "")
