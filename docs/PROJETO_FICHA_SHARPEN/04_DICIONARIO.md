# 04 · O dicionário (a IA vira compiladora de vocabulário, não leitora de aposta)

> **Estado (12/10/2026, s411):** §2 e §3 construídos. `dicionario_termos` no ar, semeada por
> `scripts/semear_dicionario.py --aplicar` (pares cru × `bilhetes`; esporte também do texto da
> `sombra_rotulos`; só o UNÂNIME entra; esporte vale para todas as casas pela maioria de cada uma).
> Quem lê é a virada (`app/virada.py`), por `app/dicionario.traduzir`. **Diferença do §4, por decisão
> do Feca (12/10): termo nunca visto NÃO grava com o termo da casa; a aposta vai para a IA, como hoje.**
> `termos_pendentes` e a classificação em lote (§4.3) não foram construídos (BACKLOG §1). Chave do
> termo: categoria pelo mercado normalizado (`{n}` no número) e, se o mercado tem duas decisões,
> pelo par mercado + seleção (seleção sem trocar número: `1` e `2` são seleções diferentes).
>
> **s412 (12/10, D24 e R27):** o termo entra com 1 voto e o erro se conserta depois, pela correção do
> Feca (`scripts/corrigir_termo.py`, `origem = 'feca'`; vence a semente, inclusive a da casa; regrava as
> apostas da Ficha do mês corrente, nunca as de mês passado). Proteções da semente: só valor do Master,
> nunca aposta editada à mão, nunca termo vago (`VAGOS`: `especiais`). `Total` sem qualificador é REGRA
> (categoria principal do esporte, `categoria_do_total`), não termo. A semente roda às 04h e logo depois
> de um `/extrair` de casa virada que mandou termo novo à IA; cada rodada vai ao `semente_log`.

## 1. O problema que ele resolve

A única coisa que a IA faz hoje e o código ainda não faz é **traduzir vocabulário**: "Basketball" vira
"Basquete", "Ambas as equipes marcam" vira a categoria certa. Para isso, a IA lê um manual de ~76 mil
tokens **a cada pedaço de apostas** (17.843 vezes de 05/07 a 11/10), e 73% do manual geral existe só para
ensinar esse padrão.

Mas os termos se repetem. "Basketball" na Pinnacle é sempre "Basquete". Traduzir **uma vez por termo** e
guardar a resposta custa uma fração do que se paga hoje, e não cresce com o volume.

## 2. As tabelas

**`dicionario_termos`**: uma linha por termo traduzido.

| Coluna | Exemplo |
|---|---|
| `casa` | `MEGAPARI` (ou `*` quando o termo vale para todas) |
| `tipo` | `esporte` · `categoria` |
| `termo_casa` | texto normalizado (minúsculo, sem espaço sobrando, números trocados por `{n}`: `over {n} gols`) |
| `termo_sharpen` | `Futebol` · `Over/Under` |
| `origem` | `semente` · `ia` · `feca` |
| `confirmado` | o Feca conferiu (amostra) |
| `ocorrencias` | quantas apostas já usaram |
| `criado_em`, `atualizado_em` | |

**`termos_pendentes`**: a fila. Casa, tipo, termo, quantas apostas estão esperando, primeira e última vez visto.

## 3. Como ele nasce: semente automática durante o modo sombra

Durante o modo sombra, a mesma aposta chega pelos dois caminhos. Para cada código:
- a Ficha traz `esporte_casa` e `mercado_casa` (como a casa escreve);
- o caminho de hoje traz `esporte` e `aposta` (o que a IA decidiu, já gravado em `bilhetes`).

Esse par vira uma linha do dicionário com `origem = semente`, por **voto da maioria** quando o mesmo termo
aparece várias vezes. **O dicionário se escreve sozinho com o tráfego real, sem nenhuma chamada nova à IA.**
Termos em que a IA de hoje se contradiz (mesmo termo, decisões diferentes) vão para a conferência do Feca.

## 4. Termo nunca visto, depois da virada

1. A aposta **grava na hora**, com o termo da casa nos campos de esporte e categoria. Os números já estão
   certos.
2. O termo entra em `termos_pendentes`.
3. Um trabalho em lote classifica os pendentes:
   - modelo barato (o que passar no teste; candidato `claude-haiku-5-5`), pela API de lote (metade do
     preço);
   - entrada mínima: a lista fechada de esportes e de categorias do Sharpen, mais o termo e 2 ou 3 exemplos
     reais daquela casa, em vez de 76 mil tokens de manual;
   - saída estruturada (`{"termo_sharpen": ...}`), escolhendo **só da lista fechada**; fora da lista = vai
     para o Feca.
4. A resposta entra no dicionário, e as apostas que esperavam são atualizadas.

## 5. Como saber se funciona

| Medida | Sinal bom |
|---|---|
| Termos novos por dia, por casa | caem até perto de zero (o vocabulário de uma casa é finito) |
| % de apostas com esporte e categoria resolvidos na hora | sobe para perto de 100% |
| Custo do lote de classificação | centavos por semana |
| Concordância do dicionário com a IA de hoje (no modo sombra) | relatada pela régua; não bloqueia |

Se os termos novos **não caírem** depois de duas semanas numa casa, a premissa do vocabulário finito está
errada para aquela casa, e isso precisa ser levado ao Feca.

## 6. Prós e contras

**Prós:** custo deixa de acompanhar o volume; resposta instantânea para termo conhecido; o termo original fica
guardado (pronto para outra língua); a semente vem de graça do modo sombra.

**Contras:** a família 1xBet mistura mercado e seleção num campo só, então o termo é mais variado e o
dicionário dela cresce mais; casa que renomeia um mercado gera termo novo, que aparece cru por alguns
minutos; o dicionário precisa de um dono humano para as contradições.
