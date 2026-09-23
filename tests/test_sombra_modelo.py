"""Gate da sombra de modelo (s383).

Decisão do Feca: *"tudo que o Sonnet fizer, o Haiku tem que receber EXATAMENTE a mesma
instrução no background, com custo separado e documentado"*.

Três coisas precisam ser verdade, e cada uma protege de um estrago diferente:

  1. **O juiz é determinístico e acusa o que tem de acusar.** `pontuar_saida` é o que
     decide se o candidato presta. Se ele não enxergar bilhete perdido, código inventado
     ou coluna comida, a sombra vira um número bonito e a decisão sai errada — que é
     exatamente o que aconteceu na s377, quando a bancada reprovou o modelo certo.
  2. **A sombra não pode entrar no `uso_tokens`.** Aquela tabela é a conta da operação e
     é lida por toda medição de preço. Gasto de experimento ali envenena as duas leituras.
  3. **A entrada da sombra é a MESMA do titular.** Se ela mandasse outro `system` ou outro
     recorte, o placar não compararia nada — e o defeito seria invisível, porque o número
     sairia igual.

O QUE ESTE GATE **NÃO** COBRE:

  • Não chama a API. Custo, latência e o comportamento do modelo candidato são medidos em
    produção, na própria `sombra_modelo`, não aqui.
  • Não exercita o INSERT (é SQL; vive no harness de banco quando fizer falta).
"""
import sys

sys.path.insert(0, "app")

import main  # noqa: E402
import repository  # noqa: E402


_TEXTO = (
    "[Código: AB1]\n"
    "Stake: R$ 10,00\n"
    "Status: Ganho (WON) → W\n"
    "Seleções:\n"
    "  • Time A · Total de Gols · Mais de 2.5 @ 1,90\n\n"
    "[Código: AB2]\n"
    "Stake: R$ 20,00\n"
    "Seleções:\n"
    "  • Time B @ 2,00\n"
)
_OK = ("01/07/2026\tFutebol\t\tBet365\tc1\tGols\tOver 2.5 Gols [Time A v Time C]"
       "\t10,00\t1,90\tW\tAB1")


def test_o_juiz_acha_o_bilhete_que_nao_voltou():
    """O pior defeito: bloco entrou, linha não saiu. Ou o bilhete sumiu, ou nasce órfã."""
    p = repository.pontuar_saida(_OK, _TEXTO)
    assert p["blocos"] == 2 and p["linhas"] == 1
    assert p["sem_codigo"] == 1, "AB2 entrou e não voltou; tem de aparecer"


def test_o_juiz_acha_o_codigo_inventado():
    """Código que não existe no texto-fonte = identidade falsa = linha duplicada."""
    p = repository.pontuar_saida(_OK.replace("AB1", "ZZ9"), _TEXTO)
    assert p["cod_inventado"] == 1
    assert p["sem_codigo"] == 2, "com o código trocado, NENHUM dos dois blocos voltou"


def test_o_juiz_acha_a_coluna_comida():
    """Linha com menos de 11 campos: o modelo omitiu o TAB do `resultado` vazio e o
    código escorregou de coluna. É a origem medida das órfãs no banco."""
    curta = _OK.replace("\tW\t", "\t")
    assert repository.pontuar_saida(curta, _TEXTO)["coluna_comida"] == 1
    assert repository.pontuar_saida(_OK, _TEXTO)["coluna_comida"] == 0


def test_o_juiz_pontua_a_descricao_mesmo_na_linha_de_codigo_inventado():
    """Senão um modelo que erra as duas coisas esconde a segunda atrás da primeira."""
    ruim = _OK.replace("AB1", "ZZ9").replace("Over 2.5 Gols", "Mais de 2.5 Gols")
    p = repository.pontuar_saida(ruim, _TEXTO)
    assert p["descricoes"] == 1, "a descrição da linha inventada tem de ser pontuada"
    assert p["fora_master"] == 1, "'Mais de' viola o MASTER e tem de contar"


def test_o_juiz_aprova_o_que_esta_certo():
    """Contraprova: sem ela, um juiz que reprova tudo passaria nos testes acima."""
    p = repository.pontuar_saida(_OK, _TEXTO)
    assert p["cod_inventado"] == 0
    assert p["coluna_comida"] == 0
    assert p["fora_master"] == 0
    assert p["infiel"] == 0


def test_a_sombra_nao_escreve_em_uso_tokens():
    """`uso_tokens` é a conta da OPERAÇÃO. Gasto de experimento ali envenenaria toda
    medição de preço (a mesma armadilha do `realtrial` na medição de formato, s356)."""
    import inspect
    src = inspect.getsource(repository.registrar_sombra_modelo)
    assert "INSERT INTO sombra_modelo" in src
    assert "uso_tokens" not in src.split('"""')[2], (
        "fora do docstring, a função não pode mencionar uso_tokens — ela escreve "
        "só na tabela do experimento")


def test_a_sombra_recebe_a_MESMA_entrada_do_titular():
    """Se ela mandasse outro `system` ou outro recorte, o placar não compararia nada —
    e o defeito seria invisível, porque o número sairia igual."""
    import inspect
    src = inspect.getsource(main)
    seq = "_sombra_modelo(dono, casa, system, [content], texto, modelo)"
    par = "_sombra_modelo(dono, casa, system, chunks, texto, modelo)"
    assert seq in src, "o caminho sequencial tem de replicar o MESMO content"
    assert par in src, "o caminho paralelo tem de replicar os MESMOS chunks"


def test_desligar_a_sombra_e_uma_variavel_de_ambiente():
    """Ela custa dinheiro de verdade. Desligar não pode exigir deploy."""
    assert main._SOMBRA_MODELO_PCT >= 0
    orig_m, orig_p = main._SOMBRA_MODELO, main._SOMBRA_MODELO_PCT
    try:
        main._SOMBRA_MODELO = ""
        assert main._sombra_vale_agora() is False
        main._SOMBRA_MODELO, main._SOMBRA_MODELO_PCT = "claude-haiku-4-5", 0
        assert main._sombra_vale_agora() is False
        main._SOMBRA_MODELO_PCT = 100
        assert main._sombra_vale_agora() is True
    finally:
        main._SOMBRA_MODELO, main._SOMBRA_MODELO_PCT = orig_m, orig_p


def test_o_modelo_da_sombra_tem_preco():
    """Sem linha em `_PRECOS` o custo da sombra sai ao preço de outro modelo, e a
    comparação que ela existe para fazer vira ficção. Irmão do test_modelo_e_preco."""
    if main._SOMBRA_MODELO:
        assert main._SOMBRA_MODELO in repository._PRECOS
