# 03 · A régua de números (o juiz da virada de cada casa)

## 1. Para que serve

Nenhuma casa troca de caminho por opinião. Ela troca quando a régua mostra que a Ficha grava os
**mesmos números** que o caminho de hoje, ou que cada diferença foi explicada e a Ficha estava certa.

Critério do Feca: **odd, stake e resultado 100% exatos.** A descrição não é julgada.

## 2. O que compara

Para cada aposta (chave: dono + casa + conta + código) capturada nos dois caminhos durante o modo sombra:

| Campo | Caminho de hoje | Caminho Ficha | Peso |
|---|---|---|---|
| Stake | `bilhetes.stake` | derivado da Ficha (`01_FICHA_SHARPEN.md §3`) | **bloqueia** |
| Odd | `bilhetes.odd` | idem | **bloqueia** |
| Resultado | `bilhetes.resultado` (W/L/V/HW/HL/vazio) | idem | **bloqueia** |
| Código | `bilhetes.codigo_bilhete` | `codigo` | **bloqueia** |
| Moeda | `bilhetes.moeda` (nulo = real) | `moeda` | **bloqueia** |
| Data | `bilhetes.data` | idem | relata; divergência precisa de explicação |
| Esporte, categoria | `bilhetes.esporte`, `bilhetes.aposta` | dicionário | relata (mede o dicionário) |
| Descrição | — | — | não compara |

Também conta:
- **apostas que um caminho viu e o outro não** (sumiço é erro de número);
- **duplicatas** que o caminho de hoje gerou e a Ficha não (código inventado, código perdido).

## 3. Como compara

- Os dois lados passam pela **mesma normalização** de número: `Decimal`, sem tolerância. `"1,85"` = `"1.85"`;
  `"1,85"` ≠ `"1,86"`. Odd de múltipla `8,9688` = `8,96880`.
- Se já existir a função de comparação da sombra de números (`app/sombra_numeros.py`, que outra frente está
  construindo a partir de `referencias/PROMPT_SOMBRA_NUMEROS.md`), **reaproveite a mesma normalização**.
  Uma régua só no projeto inteiro.
- Toda divergência sai numa lista com: casa, código, campo, valor de hoje, valor da Ficha e o valor **cru da
  casa** (da Ficha guardada). Isso diz quem errou. Quando o caminho de hoje erra (a IA copiou errado e
  nenhum fiscal pegou), a divergência conta **a favor** da Ficha, desde que o valor cru prove.
- **Diferença só de precisão é explicada** (decisão do Feca, 11/10) quando a Ficha traz o valor **cru** da
  casa e o valor de hoje é o mesmo número com menos ou mais casas (`6,169904` × `6,169904352`). Sem isso as
  499 diferenças de precisão medidas em outubro travariam toda virada. Diferença que muda o P/L em R$ 0,01
  ou mais nunca é "só precisão".
- **Altenar:** ~~antes da virada da família, explicar o caso em que o produto das pernas passa do dobro da
  odd da casa~~ **explicado (12/10):** os três são **SISTEMA 2 de 3** (`type` 2, `combLength` 2). O produto
  das três pernas é a odd da TRIPLA, que não está no bilhete; a odd da casa é a média das 3 duplas
  (`MASTER_RESULTADO §7.3`). BetMartini 5501503684: (1,787×2,9 + 1,787×2,75 + 2,9×2,75) ÷ 3 = **6,02385**
  (a casa manda `6,02`); Vavada 5504107339: 6,6896 (`6,69`); Betrebels 5499580342: (3,3334 + 3,3334 + 4) ÷
  3 = 3,5556 (`3,56`). Os três perderam: P/L igual dos dois lados. A Ficha sabe que é sistema; o TEXTO da
  extensão não diz (`_tipoVB` escreve `Múltipla (3 seleções)` para qualquer bilhete de 2+ pernas), então a
  IA grava sistema como múltipla, sem a coluna `sistema` (BACKLOG).

## 4. Quando uma casa vira

**Critério em vigor (decisão do Feca, 12/10/2026, s411). Substitui o piso de 30 liquidadas (D12) e a
proposta das 10 ganhas, que caíram.**

- **Toda casa que pode virar, vira na hora.** Sem pausa entre uma e outra.
- **Backtest com o cru que já chegou.** As capturas do Feca já mandam o histórico que a casa mostra,
  então não precisa de exportação nova. A Ficha é comparada com o banco em TODAS as apostas com cru.
- **A casa vira se nenhum DINHEIRO divergir sem explicação:** stake, resultado e retorno (e a
  freebet, que é stake). Odd diferente com P/L igual não trava (é a regra da odd, §3).
- **O histórico não é reescrito pela Ficha (D10).** Nas palavras do Feca (12/10): "não mexer no passado
  é não ir futricar as apostas de mês passado". Aposta já LIQUIDADA no banco nunca é reescrita (o
  dinheiro já bateu no backtest; não há ganho). Aposta ABERTA, de qualquer origem, passa para a Ficha.
  (Na 1ª versão, de 12/10 à tarde, o D10 travava todo código gravado pela IA; corrigido à noite.)
- **O Gabriel é só usuário:** não trava nada e não é critério de nada. Cru dele entra no backtest
  como qualquer outro.
- **Cobertura parcial não trava:** a régua mostra o número (apostas do dono com cru ÷ apostas da
  casa no banco) e segue.
- **Termo fora do dicionário vai para a IA, como hoje** (`04_DICIONARIO`, `app/dicionario.py`). A
  cobertura do dicionário sai na mesma linha do backtest.

Harness: `medicoes/medir_backtest_virada.py [CASA ...]` (banco só com SELECT; uma linha por casa:
comparadas, dinheiro divergente, "IA ainda aberta", só odd, recusadas, cobertura, dicionário).
**"IA ainda aberta"** é explicada: a casa liquidou e a linha da IA está aberta até a próxima leitura
do texto; é o tempo, não o número.

**Backtest de 12/10 (~19h30 UTC), que virou as 8 casas:**

| Casa | Comparadas | Dinheiro divergente | Cobertura (Feca) | Dicionário (in-sample) |
|---|---:|---:|---:|---:|
| MyStake | 146 | 0 | 146/155 | 144/146 |
| DEX Sport | 60 | 0 (3 "IA ainda aberta") | 62/118 | 52/60 |
| Bet Panda | 168 | 0 | 168/168 | 149/168 |
| Duel | 70 | 0 | 70/70 | 66/70 |
| Shuffle | 80 | 0 | 80/80 | 78/80 |
| Vavada | 57 | 0 | 57/57 | 40/57 |
| BetMartini | 97 | 0 | 97/97 | 79/97 |
| Megapari | 19 | 0 | 19/39 | 18/19 |

Todas com a Ficha aceita (0 recusadas). Onde a tradução discorda da IA (13 apostas), em 12 a IA errou a
regra do `Múltiplos` (`MASTER_ESPORTES §2`) e a Ficha seguiu (BACKLOG §1); 1 Megapari é mercado
combinado (`Equipa 1 para vencer e Total`), que a IA chama de `Múltipla` e o dicionário de `Outros`.

*Histórico do critério:* 11/10 o Feca pôs 30 liquidadas por casa (D12; aberta não conta, porque a
régua antiga contava vazio contra vazio como resultado igual); 12/10 de manhã a proposta das 10
ganhas; 12/10 à tarde as duas caíram pelo backtest acima.

A virada é uma chave por casa. Desligar a chave volta a casa ao caminho de hoje na hora, sem deploy.

## 5. Depois da virada

A régua continua rodando por uma semana em amostra: a IA do caminho de hoje lê uma fração das capturas
daquela casa só para comparação. Depois disso, desliga.

## 6. Relatório

Um script só de leitura imprime, por casa e **separando liquidadas de abertas**: apostas comparadas, % idênticas por campo, % com os cinco
campos de bloqueio idênticos, sumiços, duplicatas e a lista de divergências. Usuário só pelo `dono`.

Decisão do Feca (11/10): o relatório compara também **moeda** e **código** (os dois bloqueiam) e conta, por
casa, quantas **ganhas caem em "nenhuma odd fecha o retorno"** (`ficha.derivar`, `fonte_odd`): é o sinal
de cashout ou de odd da casa mal escolhida pelo adaptador.

## 7. Na casa virada, Ficha recusada volta sozinha ao caminho de hoje (desenho, 12/10)

Regra do Feca: **recusada nunca pode significar aposta perdida.** Desenho, para aprovar antes da 1ª virada:

1. **O texto continua indo sempre**, também na casa virada. O SharpenUp manda o texto e o cru em toda
   varredura (já é assim na atualização única). O texto é a rede de segurança: nada depende de o cru chegar.
2. **Virar uma casa = uma chave** (`FICHA_CASAS_VIRADAS`, por casa, reversível sem deploy). Na casa virada, a
   Ficha **aceita** grava em `bilhetes` pelo mesmo `/salvar` de hoje (mesma dedup, mesmo UPSERT), com
   procedência própria, e o código entra na lista de "já gravado pela Ficha" daquela conta.
3. **No `/extrair` da casa virada, o texto é recortado por código, antes da IA:** bloco cujo código já tem
   Ficha aceita e gravada sai do lote (a IA não paga por ele). **Todo o resto vai para a IA como hoje:** Ficha
   recusada (pelo adaptador ou pela validação), cru que ainda não chegou, cru que nunca chegou, bilhete sem
   código. Não existe um caminho em que o bilhete fica sem nenhum dos dois.
4. **A ordem favorece a segurança:** o cru sai depois do texto e chega em segundos; se o `/extrair` rodar
   antes, o código não está na lista e o bilhete vai para a IA. Custa uma leitura, nunca uma aposta.
5. **A recusa aparece:** contagem de recusadas por casa e por dia no relatório da régua, com o motivo. Recusa
   que se repete vira conserto de adaptador, não fila silenciosa.
6. **Gate antes de ligar:** teste que monta um lote com 3 bilhetes (Ficha aceita, Ficha recusada, sem cru) e
   prova que os 3 terminam em `bilhetes`, 1 pela Ficha e 2 pela IA, com mutação de cada ramo.

**LIGADO em 8 casas (12/10 ~19h40 UTC, s411):** `FICHA_CASAS_VIRADAS=MYSTAKE,DEXSPORT,BETPANDA,DUEL,SHUFFLE,VAVADA,BETMARTINI,MEGAPARI`. Antes, construído e no ar desligado (12/10, s409). `app/virada.py` + `FICHA_CASAS_VIRADAS` (vazia; `*` não
vale). Como ficou cada ponto:
- **2:** a aceita grava pelo `/salvar` de hoje (`main.gravar_tsv`, o corpo do `/salvar`), `origem='ficha'`.
  Esporte e categoria com o **termo da casa** (`04_DICIONARIO §4.1`), descrição `mercado · seleção [jogo]`.
  **s411:** esporte e categoria TRADUZIDOS pelo dicionário (`app/dicionario.py`, tabela
  `dicionario_termos`); termo sem par, e código que o banco já tem por outro caminho (D10), ficam
  com a IA. Descrição `<seleção> <linha> <mercado> [jogo]` (a linha só quando a casa a manda em campo
  próprio e ela não está no texto; `tv` inverte o sinal com `hisminus`). Sistema da Altenar com a
  12ª coluna (`3x Duplas`).
- **3 (refeito em 12/10 à noite, pedido do Feca: a aposta sai da IA na ORIGEM, enquanto aberta):** o
  `/extrair` da casa virada ESPERA o cru da mesma captura (o texto é postado antes e o cru chega menos
  de 1 s antes do extrair; `virada.esperar_cru`: enquanto houver cru em processamento, mais 1,5 s de
  folga se nenhum chegou há pouco, teto 8 s), monta a Ficha do cru GUARDADO de cada código não
  liquidado (a extensão não reenvia cru igual: é assim que a aberta gravada pela IA antes da virada
  passa para a Ficha) e o pré-dedup tira do lote todo código que a Ficha resolveu, aberto ou
  liquidado. Quando a aposta liquida, é a Ficha que grava o resultado. A IA só recebe Ficha recusada,
  termo fora do dicionário ou cru que não chegou. `ficha_virada` guarda a decisão por código;
  `virada_log` uma linha por captura (métrica: `medicoes/medir_virada_custo.py`).
- **6:** `tests/test_repository_db.py::test_virada_tres_bilhetes_chegam_ao_banco` (Postgres real) e o caso
  desligado com a sombra ligada (o estado de produção); 9 mutações, 9 detectadas, 1 inócua registrada
  (`tests/test_virada.py`). s411: termo fora do dicionário e D10 no mesmo harness de banco (mutações E e F,
  detectadas) e 15 mutações unitárias novas, todas detectadas.
