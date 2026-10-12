# DIÁRIO · Projeto Ficha Sharpen

> Uma entrada por dia ou por etapa, a mais nova no topo. Todo número com prova. A última entrada diz onde o
> projeto está e qual é a próxima ação.

---

## 2026-10-11 · D1 · decisões do Feca, aquecedor, qualidade por casa e regra da odd

**Onde está:** decisões registradas; três propostas esperando o Feca (abaixo). Nada de código novo.

**Decisões do Feca** (`README.md §3`, itens 8 a 12): Ficha antes da Fase 2 da blueprint (`STATUS.md`
atualizado); só esta sessão mexe em `main.py`/`repository.py` (`docs/ESTRUTURA_DO_TIME.md`); virada só com
30 apostas **liquidadas** comparadas (`03_REGUA_NUMEROS.md §4`); odd: aberta pelas pernas, resolvida por
retorno ÷ stake; as 249 apostas antigas ficam como estão (item fechado).

**1. Aquecedor de cache.** A `SUPERBET` **não** está na chave. Confirmado no código: os 6 manuais gerais
são um prefixo de cache comum a todas as casas (`app/prompts.py`, `build_system`, breakpoint no 6º master),
e o aquecedor (`app/main.py`, `_cache_warmer`) só aquece a versão com pensamento. Proposta: com a chave
não vazia, aquecer **as duas** versões (com pensamento para print, PDF e casas fora da lista; sem, para as
listadas). Custo: uma leitura de cache a mais a cada 55 min. Amanhã: `cache esc.` por extração depois
de 21:10 no `medicoes/medir_qualidade_por_casa.py`.

**2. Qualidade por casa.** `medicoes/medir_qualidade_por_casa.py` pronto (uso_tokens, repescagem pela
`sombra_tsv`, fiscal mexeu pela `sombra_numeros`, liquidadas × abertas). Rodado às 21:4x: **nenhuma
extração depois da chave ainda**. O "antes" da sombra é fino (ela grava desde 11/10 19:57: 1 a 3
extrações por casa).
- **Achado, e ele pesa:** em **1xBet (Megapari, PariPesa, SapphireBet, 1xBit) e Altenar (BetMartini,
  Betrebels, Vavada, Kikobet)** o retorno vem numa linha `Retorno:` própria, e o fiscal só lê o retorno
  dentro do `Status:` (`repository._financeiro_do_texto`, `_RETORNO_TXT_RE` sobre o status). Medido com a
  função real em blocos ganhos de outubro: **0 de 40** Megapari, 0/40 BetMartini, 0/40 Betrebels, 0/40
  Vavada, 0/30 SapphireBet, 0/27 PariPesa. Nessas 8 casas o fiscal da odd **nunca roda**, com ou sem
  pensamento, e o erro que a medição da DEX achou passaria direto.

**3. Regra da odd** (`medicoes/medir_regra_odd.py`; 1.547 apostas de outubro das 15 casas, 1.347
comparáveis; sistema e HL fora; odd gravada × odd pela regra, igualdade exata):
- **Mudariam 527 de 1.347.** Por causa: **499 são só precisão** (diferença < 0,5%: `6,169904` ×
  `6,169904352`, `5,5648` × `5,565`), **28 são diferença grande**. P/L: 33 apostas mudariam ≥ R$ 0,01,
  saldo líquido R$ 0,31.
- **As 28 grandes são casos em que o produto das pernas NÃO é a odd que a casa pagou:** ComboBOOST da
  Betpanda (casa `8,918` = produto `8,494` × 1,05), perna anulada (8), mesmo jogo/Bet Builder (2) e
  múltiplas Altenar em que o produto passa do dobro da odd da casa (BetMartini `6,02` × produto `14,25`;
  Betrebels `3,56` × `6,67`; Vavada `6,69` × `15,79`), causa ainda não explicada.
- **(c) cashout pela regra da aberta quebra o P/L:** o P/L de W é `stake × (odd − 1)`; com a odd das
  pernas, um cashout de R$ 50 numa aposta de odd 4 grava lucro de odd 4. Hoje o `MASTER_RESULTADO §5.6`
  manda retorno ÷ stake.

---

## 2026-10-11 · D1 · etapa 2: pensamento atrás de chave (no código, chave desligada)

**Onde está:** **chave LIGADA** para as 15 casas de outubro em 11/10, 21:10 (o Feca rodou o
`railway variables --set`; o modo auto do Claude Code barra a escrita). Deploy `97387a25` SUCCESS, app no
ar (`www.sharpen.bet` responde, startup limpo no log). Próxima ação: depois de um dia de extrações,
conferir no `uso_tokens` a saída por pedaço nessas casas e os números na régua.

- **Chave:** `EXTRACAO_SEM_PENSAMENTO` = lista de casas ou `*`. Vazia = como sempre. Só lote de **texto**
  (print e PDF seguem pensando: não foram medidos sem). Lida a cada chamada.
- **Onde age** (`app/main.py`, `_pensamento_kw`): todas as chamadas do titular, ou seja, paralelo,
  sequencial e as repescagens de cobertura e de fidelidade. Também no aquecedor de cache, que aquece a
  Superbet: o pensamento entra na chave do cache (medido hoje: a chamada sem pensamento não leu o cache
  escrito com ele), então ele acompanha quando a chave cobre a Superbet. Contrato de 4 campos e sombra:
  intocados.
- Conferido na API real: `max_tokens=0` com `thinking` desligado é aceito (aquecedor).
- **Gate:** `tests/test_extracao_sem_pensamento.py`, 9 testes, **5 mutações, 5 detectadas**. Os dublês
  de `_repescar_faltantes` em `test_cobertura.py` e `test_fidelidade.py` passaram a aceitar o argumento
  novo. `pytest tests`: **1.732 passed**.
- Valor das 15 casas de outubro, conferido contra `casas/CASA_*.md`:
  `DEXSPORT,MEGAPARI,MYSTAKE,SHUFFLE,BETREBELS,DUEL,BETPANDA,BETMARTINI,BETFURY,VAVADA,BETCOIN,PARIPESA,SAPPHIREBET,1XBIT,KIKOBET`

---

## 2026-10-11 · D1 · etapa 1 publicada + quanto do banco caiu no furo

- **Commit `ec50274`, pushado** (fix + teste + STATUS s409, com a s407 indo para o HISTORICO). O commit
  desta pasta foi **barrado pelo filtro de permissão** do Claude Code; fica para o Feca rodar.
- **Medição no banco (só leitura)**, harness `medicoes/medir_furo_folga_odd.py`: para cada aposta W/HW
  com bloco cru na `sombra_rotulos`, a função de antes (backup) × a de agora, com a stake do bloco.
  - 9.436 apostas W/HW com bloco; **249 caíram no furo** (a odd gravada não fecha o retorno e a da casa
    fecha). Todas de agosto (41) e setembro (208); **nenhuma de outubro**.
  - Dinheiro: **R$ 27,94 somando em módulo**, saldo líquido de R$ 0,34; **maior diferença numa aposta:
    R$ 0,80**. Quase tudo é odd com dízima (`1,9505…` onde a casa diz `1,95`), Bet365 à frente
    (Jonathan 81, Feca 65, Gabriel 33).
  - **Ficaram de fora 298** em que a stake do bloco difere da gravada: casa em USDT/USD (o banco guarda em
    real) ou stake editada. As casas cripto do projeto (DEX, Betpanda, Duel, Shuffle) **não foram
    medidas** por isso.
  - Não conferi `correcoes` (edição humana manda). Qualquer reparo precisa pular essas linhas.
  - Primeira rodada saiu inflada (447, R$ 130 mil) por erro meu: usei a stake do banco contra o retorno do
    bloco em USDT. Corrigido antes de reportar.

---

## 2026-10-11 · D1 · etapa 1: furo de 0,005 do fiscal fechado (não commitado)

**Onde está:** código e teste prontos no working tree, **sem commit** (aguarda o Feca). Próxima ação:
commit + push com o "pode" do Feca; depois, a etapa 2 (pensamento desligado atrás de chave).

- **Mudança:** `app/repository.py`, `_veredito_do_retorno`, logo depois da linha 696. Dentro da folga de
  0,005 da odd, em W e HW, a odd da casa substitui a da linha quando **ela fecha o retorno no centavo e a
  da linha não**. Casa que arredonda a odd na tela: a da linha fecha e fica. Nenhuma fecha: nada muda.
  Fora da folga, o comportamento é o de antes.
- Não está atrás de chave por casa: é conserto do fiscal de hoje, vale para todas as casas e todos os
  modelos (decisão desta etapa, aprovada como "fechar o furo").
- **Gate:** 4 testes novos em `tests/test_odd_resultado_determinista.py` (bloco real da DEX); **7
  mutações, 7 detectadas** (lista no cabeçalho do arquivo, itens 13 a 19). `pytest tests`: **1.723
  passed**, 51 skipped.
- **Prova na medição de hoje**, sem chamada nova à API (respostas gravadas da medição, refeitas pelo
  fiscal novo): números A × B **30 de 30 iguais** em stake, odd e resultado (era 29 de 30). O fiscal
  corrigiu 1 linha do B e nenhuma do A.
- Backup: `Backups/s409_fiscal_odd_fecha_no_centavo/`.
- **Não medido:** quantas linhas já gravadas no banco caíram nesse furo. Dá para medir só leitura.

---

## 2026-10-11 · D1 (início) · medição do pensamento do Sonnet 5

**Onde está:** medido; **nada mudou em produção**. Próxima ação: o Feca escolhe o que fazer com o
pensamento (ver "Pendente").

**Pergunta do Feca:** voltar para o Sonnet 4.6 não resolve mais fácil? **Não**, e não foi feito:
- na bancada limpa da s380 (21/09, 300 blocos), o 4.6 **perdeu 6 bilhetes** e o Sonnet 5 nenhum
  (`docs/historico/HISTORICO_s300-s327.md:25`); foi o motivo da troca da s377 (`docs/HISTORICO.md:49`);
- o 4.6 custa mais por token (3/15 contra 2/10 por MTok) e saiu do `ALLOWED_MODELS` (`app/config.py`).

**Medição** (harness: `medicoes/medir_pensamento.py`; 5 lotes × 6 blocos reais da DEX Sport de outubro,
`sombra_rotulos`; caminho de produção; banco só leitura; juiz = `app/sombra_numeros.comparar`):

| | A: como hoje | B: pensamento desligado |
|---|---|---|
| Respostas com bloco de pensamento | 5 de 5 | 0 de 5 |
| Saída por pedaço (média) | **11.407 tok** | **1.545 tok** |
| Custo por pedaço, cache quente | US$ 0,142 (medido) | ~US$ 0,039 (calculado com o cache lido; na medição o cache não foi reaproveitado, ver abaixo) |

- **Confirmado: o excesso é pensamento.** Saída cai 86% sem ele.
- **Números, A × B, 30 apostas:** stake 30/30 iguais, resultado 30/30, **odd 29/30**. A diferente é um
  **erro do B**: bilhete `1d15646f…` (DEX, múltipla ganha, stake 40, retorno 158,80 USDT, odd da casa
  3,97). 158,80 ÷ 40 = **3,97** (A acertou). O B gravou **3,9672**, que é o produto das pernas
  (2,28 × 1,74), e escreveu na nota que era "retorno ÷ stake". Os fiscais (`corrigir_stake_tsv`)
  **não pegaram**: o final saiu igual ao bruto. No P/L seria R$ 118,69 no lugar de R$ 118,80.
- Amostra pequena (30 apostas, 1 casa, 1 rodada): é sinal, não taxa.
- **Custo da medição: ~US$ 2,24**, acima do "menos de US$ 1" que eu prometi. Mudar o pensamento
  invalida o cache do manual, e cada chamada B escreveu o cache de novo (70 mil tokens).

**Por que o fiscal não pegou** (reproduzido com as funções reais, sem IA): `_financeiro_do_texto` leu
certo o bloco (`odd_total 3,97`, `retorno 158,80`), e `_veredito_do_retorno(40, 3,9672, 158,80, …)`
devolveu `('W', None)`: confirmou o W e **não trocou a odd**, porque `app/repository.py:696` só troca
quando a diferença passa de **0,005** (`abs(n_bloco - odd) > 0,005`), pensado para barrar ruído de estilo
(`1,95` × `1,950`). 3,97 − 3,9672 = 0,0028. É um furo do fiscal que vale para **qualquer** modelo e casa,
não só sem pensamento.

**Pendente com o Feca:** desligar o pensamento hoje **troca dinheiro por erro de número** (1 em 30
aqui). Opções na resposta da sessão: manter como está até a Ficha virar a casa, ou medir um meio-termo
(esforço médio) antes.

---

## 2026-10-11 · D0 · Ficha aprovada

**Onde está:** Ficha Sharpen v1 aprovada, nenhum código escrito. **Próxima ação: D1**, começando por
confirmar que os tokens a mais do Sonnet 5 são pensamento, antes de mexer nele.

**Respostas do Feca às 5 perguntas** (detalhe no §9 de `01_FICHA_SHARPEN.md`): 1A, 2A, 3A, 4A, 5A.
- Data: regra do §3 inteira, incluindo "sem início = colocação".
- Termo desconhecido grava na hora; o lote atualiza só Esporte e Aposta.
- Descrição fica com o termo original da casa e nunca é reescrita (pergunta extra do Feca; resposta:
  "a descrição não tem essa importância toda").
- Sem caixa de revisão. Moeda ausente = moeda da conta.

**Medido para responder a pergunta 1** (leitura de código, não de dado): as 6 famílias de outubro
entregam início por perna: DEX `extensor/content.js:4656`, 1xBet `extensor/x1_inject.js:143`
(`StartDate`), BetConstruct `content.js:5257` e `5303`, BetBy `content.js:4515`, Altenar
`content.js:5746` (`eventDate`), Shuffle `content.js:4865`. Pernas sem início nas fixtures não foram
contadas.

**Feito por outras frentes hoje (não por este projeto), conferido no git:**
- Sombra no `claude-haiku-5-5` por padrão: `app/main.py:490`, commit `e2427d4` (s407). A régua de
  números (`app/sombra_numeros.py`, `scripts/relatorio_sombra_numeros.py`) entrou no mesmo commit.
- Barreira de recaptura (porteiro) da DEX Sport e da Shuffle: commit `9d5a66c` (s407/s408).
- Outra sessão segue mexendo em `app/repository.py` e `global/MASTER_OUTPUT_2026.md` (git status de
  11/10, noite).

**Pendente com o Feca:**
- A ordem das casas do `02_CASAS_OUTUBRO.md §2` não foi perguntada explicitamente; segue a do arquivo.
- D1: reduzir o pensamento do Sonnet 5 (depois de confirmar que é pensamento) e a rota sombra da Ficha.

---

## 2026-10-11 · D-1 · Projeto aberto

**Onde está:** desenho pronto, nenhum código escrito. **Próxima ação: D0, aprovar a Ficha** (as 5 perguntas
do §9 de `01_FICHA_SHARPEN.md`).

**O que aconteceu hoje:**
- Mapa independente do Sharpen concluído (Fase 1), com verificação cega: 53 de 55 fatos confirmados na
  fonte. `Auditorias\mapa_2026-10\claude\MAPA.md`.
- Revisão do processo de extração com o Feca, passo a passo, em duas gravações. Página final:
  `referencias/viagem-de-uma-aposta.html`.
- Decisões do Feca registradas no `README.md §3`.
- Medido para este projeto (banco de produção, só leitura):
  - custo por extração: US$ 0,22 no Sonnet 4.6 → US$ 0,45 no Sonnet 5 (`uso_tokens` por modelo);
  - 69% da conta do Sonnet 5 é a IA escrevendo (`uso_tokens` × preço de tabela, bate com o gravado);
  - 73% do manual geral é padrão de esporte, categoria e descrição (`count_tokens` por arquivo);
  - as 15 casas do projeto custaram cerca de US$ 87,5 de 01/10 a 11/10, só Feca e Gabriel
    (`02_CASAS_OUTUBRO.md`).
- Em paralelo, outra frente está construindo a sombra de números Sonnet × Haiku (`app/sombra_numeros.py`,
  `scripts/relatorio_sombra_numeros.py`, ainda não commitados) a partir de
  `referencias/PROMPT_SOMBRA_NUMEROS.md`. Também em paralelo: as correções do porteiro para DEX Sport e
  Shuffle.

**Pendente com o Feca:**
- As 5 perguntas do §9 da Ficha.
- Reduzir ou desligar o "pensamento" do Sonnet 5 no caminho de hoje (D1). Que os 4,6 mil tokens a mais por
  pedaço são pensamento é dedução: confirmar com o uso detalhado de uma resposta real antes de mexer.
- Trocar a sombra para `claude-haiku-5-5` (variável `SOMBRA_MODELO` no Railway).
