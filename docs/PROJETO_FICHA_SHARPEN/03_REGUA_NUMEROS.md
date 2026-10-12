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
- **Altenar:** antes da virada da família, explicar o caso em que o produto das pernas passa do dobro da odd
  da casa (BetMartini `6,02` × `14,25`, Betrebels `3,56` × `6,67`, Vavada `6,69` × `15,79`).

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
