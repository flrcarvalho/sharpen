"""Gate da escolha de modelo e do preço que a mede (s377).

Nasceu de um defeito medido: `DEFAULT_MODEL` ficou em `claude-sonnet-4-6` depois que o
Sonnet 5 saiu, e ninguém voltou na lista. Rodamos meses na geração anterior pagando 1,5x
o preço da atual da mesma linha — **R$ 1.496 medidos** em `uso_tokens` de julho a
setembro, a R$ 761/mês no ritmo do fim. Não houve erro de código: houve uma decisão certa
na data, congelada, e nenhuma régua cobrando revisão.

São dois gates, e eles cobrem coisas diferentes:

  1. **Todo modelo permitido tem preço.** Sem a linha em `_PRECOS`, o `custo_usd` cai no
     `_PRECO_PADRAO` (Sonnet 4.6) e o `uso_tokens` registra o preço do modelo ERRADO.
     O modo de falha é o pior possível para uma troca feita para economizar: a conta
     continuaria idêntica no log e a leitura seria "a troca não adiantou".
  2. **A escolha tem prazo de validade.** Quebra o CI 90 dias depois da última revisão.
     É o único jeito que este repo conhece de cobrar uma revisão que não tem dono:
     "regra sem gate não é cumprida neste repo, está medido" (`CLAUDE.md`).

O QUE ESTES TESTES **NÃO** COBREM:

  • **Não conferem o preço contra a tabela oficial da Anthropic.** Não há rede no CI, e
    não deve haver: um gate que depende de rede quebra por motivo errado. A conferência
    do VALOR é humana, e é justamente o que o prazo de validade agenda.
  • **Não dizem que o modelo escolhido é o melhor.** Isso é medição sobre blocos reais
    (o método está no `STATUS` da s377), não teste unitário.
"""
import sys
from datetime import date

sys.path.insert(0, "app")

import config  # noqa: E402
import repository  # noqa: E402


def test_todo_modelo_permitido_tem_preco():
    """Sem linha em `_PRECOS` o custo é calculado ao preço de outro modelo, em silêncio."""
    modelos = {config.DEFAULT_MODEL, *config.ALLOWED_MODELS}
    faltando = sorted(m for m in modelos if m not in repository._PRECOS)
    assert not faltando, (
        "modelo(s) sem preço em repository._PRECOS: %s.\n"
        "O custo_usd cairia no _PRECO_PADRAO e o uso_tokens passaria a registrar o preço "
        "do modelo errado — a economia de uma troca não apareceria." % faltando)


def test_o_modelo_padrao_esta_entre_os_permitidos():
    """`/extrair` recusa modelo fora de ALLOWED_MODELS. Se o default estiver fora, toda
    extração que não passe modelo explícito quebraria com 400."""
    assert config.DEFAULT_MODEL in config.ALLOWED_MODELS


def test_todo_preco_tem_as_quatro_pontas():
    """Faltar uma chave faz o `custo_usd` levantar KeyError dentro do `registrar_uso`,
    que engole a exceção: a chamada sumiria do log em vez de sair com preço errado."""
    for modelo, p in repository._PRECOS.items():
        assert set(p) == {"input", "output", "cache_read", "cache_write"}, modelo
        assert all(isinstance(v, (int, float)) and v > 0 for v in p.values()), modelo


def test_a_escolha_de_modelo_tem_validade():
    """Prazo de validade da revisão humana. Ao estourar: conferir os IDs e os preços
    contra a tabela oficial, corrigir o que mudou e mover `MODELO_REVISADO_EM`.
    **Mover a data sem conferir é pior que não ter o gate.**"""
    revisado = date.fromisoformat(config.MODELO_REVISADO_EM)
    dias = (date.today() - revisado).days
    assert dias <= config.MODELO_VALIDADE_DIAS, (
        "a escolha de modelo foi revisada há %d dias (teto: %d).\n"
        "Confira ALLOWED_MODELS e repository._PRECOS contra a tabela oficial de preços "
        "e então mova config.MODELO_REVISADO_EM." % (dias, config.MODELO_VALIDADE_DIAS))


def test_modelo_fora_da_tabela_ainda_calcula_algo():
    """O fallback é deliberado: levantar aqui faria o `registrar_uso` engolir a exceção e
    a chamada sumir do log — invisível é pior que aproximado. Ele grita no log."""
    v = repository.custo_usd("modelo-que-nao-existe", {"input": 1_000_000})
    assert v == repository._PRECO_PADRAO["input"]
