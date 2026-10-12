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

Uma casa vira quando, ao mesmo tempo:

1. **zero divergências sem explicação** em stake, odd, resultado, código e moeda;
2. pelo menos **30 apostas LIQUIDADAS comparadas** (decisão do Feca, 11/10/2026). **Aberta não conta**: o
   resultado dela é vazio dos dois lados, e a régua de hoje (`sombra_numeros`) conta vazio contra vazio
   como resultado igual. Em 11/10, eram 4 de 10. Por isso a régua **separa liquidadas e abertas** em todo
   relatório. Casa de volume pequeno (1xBit, Kikobet) espera chegar às 30; a fixture da bancada é
   pré-requisito (item 3), não substituto;
3. o harness da família está verde, e fica vermelho quando se remove uma regra (prova por mutação);
4. o Feca leu a lista de divergências e aprovou.

**Proposta (12/10, AGUARDANDO o Feca):** além das 30 liquidadas, **pelo menos 10 GANHAS comparadas** por
casa (Ficha ou IA em W/HW). É na ganha que a odd e o retorno pesam; na perdida a Ficha só precisa acertar
stake e resultado. A régua já mostra a contagem (`medir_regua_adaptadores.py`). Em 12/10, Feca: DEX 11,
MyStake 14, Vavada 10, Duel 12, BetMartini 20, Shuffle 25, Bet Panda 47; Gabriel 0 em todas.

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

**Construído e no ar, DESLIGADO (12/10, s409).** `app/virada.py` + `FICHA_CASAS_VIRADAS` (vazia; `*` não
vale). Como ficou cada ponto:
- **2:** a aceita grava pelo `/salvar` de hoje (`main.gravar_tsv`, o corpo do `/salvar`), `origem='ficha'`.
  Esporte e categoria com o **termo da casa** (`04_DICIONARIO §4.1`), descrição `mercado · seleção [jogo]`.
  ⚠ **Pré-requisito da 1ª virada:** o termo de cada casa no dicionário, senão a grade mostra `football`
  (DEX) e `sportTypeId 4` (Altenar) onde hoje mostra Futebol e Tênis. A MyStake já manda em português.
- **3:** não precisou de código novo no `/extrair`. O pré-dedup por código (`_dedup_superbet_text`) já tira
  do lote, antes da IA, o código RESOLVIDO no banco naquela conta. **Diferença do desenho, a favor da
  segurança:** a aceita ABERTA continua indo para a IA (como hoje, até liquidar); só a liquidada sai.
- **6:** `tests/test_repository_db.py::test_virada_tres_bilhetes_chegam_ao_banco` (Postgres real) e o caso
  desligado com a sombra ligada (o estado de produção); 9 mutações, 9 detectadas, 1 inócua registrada
  (`tests/test_virada.py`).
