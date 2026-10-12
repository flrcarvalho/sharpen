# PROMPT: a sombra do Haiku passa a medir números (odd, stake, resultado)

> Cole numa sessão nova do Claude Code aberta em `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`.

---

## 0. Quem pede, o que quer e por quê

O Feca (dono do Sharpen) ligou em 23/09 uma "sombra": o Haiku recebe exatamente os mesmos pedaços
que o Sonnet e lê o mesmo lote em segundo plano. O objetivo é responder **uma pergunta só**:

> "Se eu trocar o Sonnet pelo Haiku, o que vai para o banco continua certo?"

O critério dele, nas palavras dele:

> "A única coisa que não pode errar é número. A odd tem que ser 100% igual, a stake tem que ser 100%
> igual, o resultado tem que ser 100% igual. Se ele entregar uma palavra diferente na descrição, não
> importa. Se ele for mais barato, ele está dentro. O Sharpen é um sistema financeiro das apostas."

**Hoje a sombra não mede isso.** Sua missão é fazer ela medir, sem mudar nada do que o usuário vê ou
grava e sem nenhuma chamada paga a mais.

---

## 1. O que existe hoje (verificado no commit 1beca31, em produção)

- A sombra roda em `app/main.py:497-551` (`_sombra_modelo`). Ela é chamada em três lugares:
  - `app/main.py:2061`: caminho sequencial.
  - `app/main.py:2275`: caminho paralelo, o principal.
  - `app/main.py:2400`: contrato de 4 campos, **desligado em produção** (`CONTRATO_TEXTO_CASAS` não
    existe no Railway).
- Ela monta as linhas do Haiku (`partes`, `app/main.py:535`) e passa tudo a `pontuar_saida`
  (`app/repository.py:5928-5976`). Esse placar confere só código, colunas e descrição. Ele **não compara
  odd, stake nem resultado**.
- A tabela do Haiku é **descartada** depois do placar. `sombra_modelo` guarda só contagens e custo
  (`app/repository.py:5979+`). Em 414 extrações não há como reconstruir o que o Haiku escreveu.
- O Sonnet passa por fiscais determinísticos antes de o resultado voltar à tela (`app/main.py:2215-2267`):
  - `corrigir_codigos_tsv`;
  - `_corrigir_codigos_fantasma`;
  - `_garantir_cobertura` e `_garantir_fidelidade`, que **chamam a IA de novo**;
  - `_apply_betfair_dates`;
  - `corrigir_stake_tsv`, que corrige stake e, pelo retorno do bloco, odd e resultado;
  - `corrigir_data_tsv`;
  - `anexar_sistema_tsv`.
- O `resultado` final do Sonnet (pós-fiscais) existe em `app/main.py:2275`, mas não é passado à sombra.
  O bruto do Sonnet (antes dos fiscais) é o retorno de `_combine_parallel_results` em `app/main.py:2212`.
- A sombra **não** entra em `uso_tokens`, e isso deve continuar assim (`app/main.py:478-479`).

Confirme cada linha acima no código antes de mexer. Se algo mudou desde 1beca31, pare e me diga.

---

## 2. A pergunta, em forma de medida

Para cada aposta (chave = código do bilhete) de cada extração em que a sombra rodou, guarde quatro
versões de **stake, odd e resultado**:

| Versão | O que é |
|---|---|
| `sonnet_bruto` | o que o Sonnet escreveu, antes de qualquer fiscal |
| `sonnet_final` | o que voltou para a tela, depois de todos os fiscais (o que o usuário salva) |
| `haiku_bruto` | o que o Haiku escreveu |
| `haiku_final` | o Haiku depois de passar **pelos mesmos fiscais determinísticos** do Sonnet, na mesma ordem |

**Métrica principal:** `haiku_final == sonnet_final` nos três campos, aposta a aposta. Isso responde à
pergunta do Feca: se trocar, o que iria para o banco seria igual?

**Métricas de apoio:**
- `haiku_bruto == sonnet_bruto`: quanto os dois modelos concordam sozinhos.
- `sonnet_bruto != sonnet_final`: onde o Sonnet errou e um fiscal salvou.
- `haiku_bruto != haiku_final`: o mesmo, para o Haiku.
- Apostas que o Haiku não devolveu e códigos que ele inventou. Faça essa conferência pelo mesmo gabarito
  de códigos que `_garantir_cobertura` usa, **sem** chamar a IA.

Regras dos fiscais na versão `haiku_final`:
- Rode só os fiscais **determinísticos**: `corrigir_codigos_tsv`, `_corrigir_codigos_fantasma`,
  `_apply_betfair_dates` (se houver datas), `corrigir_stake_tsv`, `corrigir_data_tsv` e
  `anexar_sistema_tsv`.
- **Não** rode `_garantir_cobertura` nem `_garantir_fidelidade`, porque chamam a IA e custam dinheiro.
  Em vez disso, registre quantas apostas teriam precisado de repescagem.

Comparação de números:
- Normalize os dois lados com **a mesma função que o caminho do `/salvar` usa** (`parse_tsv` em
  `app/repository.py:377`, mais a normalização de número e de resultado de `validar_linhas` em
  `app/repository.py:1302`).
- Compare com `Decimal`, **sem tolerância**. "1,85" e "1.85" são iguais; "1,85" e "1,86" são diferentes.
- O resultado é comparado como código: W, L, V, HW, HL ou vazio para aposta aberta.
- Não compare descrição, esporte nem categoria para decidir nada. Se quiser, guarde-os sem julgamento.

---

## 3. O que construir

1. **Guardar as saídas.**
   - Crie uma tabela nova, uma linha por aposta por extração, com: `id da extração` (gere um uuid por
     extração e grave o mesmo uuid em `sombra_modelo`), `criado_em`, `dono`, `casa`, `codigo`, as quatro
     versões de stake, odd e resultado, e as marcas de "faltou" e "inventado".
   - Guarde também, por extração, o TSV bruto do Haiku e os TSV bruto e final do Sonnet, para permitir
     reanálise sem nova chamada.
   - A criação da tabela segue o padrão idempotente que o app já usa no boot.
2. **Passar o que falta à sombra.**
   - Nos caminhos sequencial e paralelo, passe o bruto e o final do Sonnet e os tokens/custo do titular
     daquela extração (`total_tokens` e `modelo`, disponíveis em `app/main.py:2268`). Assim o custo dos
     dois fica lado a lado, na mesma extração.
   - No caminho do contrato (`:2400`, desligado), não quebre nada. Diga explicitamente o que fez.
3. **Função pura de comparação**, testada. Casos mínimos:
   - `1,85` × `1.85` iguais; `1,85` × `1,86` diferentes;
   - `HW` × `W` diferentes; aberta (vazio) × `W` diferentes;
   - odd de múltipla `8,9688` × `8,96880` iguais;
   - aposta que o Haiku não devolveu; código inventado pelo Haiku;
   - stake errada no bruto que `corrigir_stake_tsv` conserta nos dois lados.
4. **Relatório só de leitura**, um script em `scripts/` que roda com SELECT e imprime:
   - por casa e no total, desde uma data: apostas comparadas;
   - % com stake idêntica, % com odd idêntica, % com resultado idêntico, % com **os três idênticos**;
   - apostas faltando, códigos inventados, repescagens que seriam necessárias;
   - custo do Haiku × custo do Sonnet nas mesmas extrações;
   - a lista das divergências de número (código, casa, campo, valor do Sonnet, valor do Haiku, se algum
     fiscal mexeu). Usuário só pelo `dono`.

---

## 4. Proibições

- Nada muda no que o usuário vê, recebe ou grava. A sombra continua fire-and-forget, com `except` largo,
  depois do `done`.
- Nenhuma chamada paga nova: reaproveite a chamada do Haiku que já existe. Nada de repescagem para o Haiku.
- Não mexa em `uso_tokens`, no `SOMBRA_MODELO` nem no `SOMBRA_MODELO_PCT` (troca de modelo ou de
  amostragem é decisão do Feca, por variável do Railway).
- Não mexa nos manuais (`global/`, `casas/`): mudar o manual invalida o cache.
- Siga o `CLAUDE.md` do repositório e o fluxo do Feca: **proponha o plano, espere aprovação, depois
  execute**. Backup antes de editar. Nada de commit, push ou deploy sem ele mandar.
- Comunicação em pt-BR, frases diretas.

---

## 5. Pronto quando

- Os testes da função de comparação passam.
- O plano foi aprovado, a mudança foi publicada pelo Feca e o relatório roda contra produção (só leitura).
- Depois de um número de extrações que o Feca definir, o relatório responde, por casa e no total:

> "Em X% das apostas, o Haiku, depois dos mesmos fiscais, gravaria stake, odd e resultado idênticos aos
> do Sonnet. Nas Y% restantes, as diferenças foram estas, e custaria Z% do Sonnet."
