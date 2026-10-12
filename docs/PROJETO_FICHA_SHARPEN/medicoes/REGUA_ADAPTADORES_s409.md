# Régua Ficha × IA nos 545 crus (s409, 12/10/2026)

**Harness:** `medir_regua_adaptadores.py` (nesta pasta). Banco só leitura, sem IA, sem custo.
**Amostra:** os 545 crus de `captura_crua` em 12/10 (teste do Feca, contas Feca e Ellen),
6 casas, 5 famílias. Adaptadores da branch `ficha-adaptadores`: `jb`, `shf`, `tv`, `vb`
novos; `dx` sem mudança. Comparados com o bilhete da IA de mesmo código na mesma conta:
stake, odd, resultado, retorno e freebet. É uma rodada, de um dia, de duas contas: placar,
não taxa.

## Tabela por casa

| Casa | Família | Crus | Batem nos 5 campos | Só a odd difere, P/L igual (< 0,01) | Divergem com dinheiro | Recusadas |
|---|---|---:|---:|---:|---:|---:|
| Bet Panda | jb | 167 | 118 | 48 | 1 | 0 |
| Duel | jb | 65 | 44 | 21 | 0 | 0 |
| DEX Sport | dx | 55 | 55 | 0 | 0 | 0 |
| MyStake | tv | 137 | 137 | 0 | 0 | 0 |
| Shuffle | shf | 72 | 70 | 0 | 0 | 2 |
| Vavada | vb | 49 | 39 | 7 | 3 | 0 |
| **Total** | | **545** | **463** | **76** | **4** | **2** |

Stake, resultado, retorno e freebet bateram em **todos** os 543 aceitos. Nenhum cru ficou
sem bilhete. As 28 freebets da MyStake batem dos dois lados.

## As 4 divergências com dinheiro: a IA está certa

As quatro são **sistema ganho**. O adaptador dá a odd estrutural (média das linhas,
`MASTER_RESULTADO §7.3`), e o `ficha.derivar` aplica a regra "sistema: odd da casa" também
no W. O `§7.1` manda `W com retorno visível → Retorno ÷ Stake`, que é o que a IA gravou.

| Casa | Código | Stake | Retorno (cru) | Ficha | IA | P/L a mais na Ficha |
|---|---|---:|---:|---:|---:|---:|
| Bet Panda | 2719953703015690358 | 60 | `result_sum` 88,94 | 4,1691 | 1,4823 | 161,21 USDT |
| Vavada | 5504514128 | 43,5 | `totalWin` 69 | 5,1184 | 1,5862 | 153,65 USDT |
| Vavada | 5504503270 | 60 | `totalWin` 84 | 3,9551 | 1,4 | 153,31 USDT |
| Vavada | 5504412582 | 60 | `totalWin` 86,1 | 4,4783 | 1,435 | 182,60 USDT |

Prova: no sistema só parte das linhas paga (Bet Panda: 1 de 3 duplas, `combinations[1]`
`status won`, 20 × 4,447 = 88,94). Com a odd média, o P/L seria `stake × (odd − 1)` sobre
a stake inteira, como se todas as linhas tivessem ganho. **O defeito é do `derivar`, não
dos adaptadores**, e por isso fica fora desta branch: a mudança (sistema W/HW pela fórmula
do retorno, como as outras) é de regra e precisa de aprovação.

## As 76 em que só a odd difere

Nenhuma move dinheiro (diferença de P/L < 0,01 na moeda da conta). Quem está certo:

- **Perdida da BetBy, IA com o `k` da tela (49: 32 Bet Panda, 17 Duel).** O `k` é o produto
  das pernas TRUNCADO em 3 casas (1,94 × 2,16 = 4,1904 → `k` 4,19). **Ficha certa**: é o
  produto exato, e a prova é o dinheiro. Nos 232 crus da família, pelo produto, 51 de 51
  retornos ganhos e 9 de 9 potenciais abertos fecham no centavo; pelo `k`, não.
- **Perdida com perna devolvida (BetBy, 5: 2 Bet Panda, 3 Duel).** A casa recalcula o `k` sem a perna
  (`[1,69 refund, 2,16 lost]` → `k` 2,16), e a IA gravou 2,16. **Ficha certa** pelo
  `MASTER_RESULTADO §5.5.1`: na derrota, a odd estrutural sem remover a seleção anulada (3,6504).
- **Perdida ComboBOOST (Bet Panda, 3).** A IA gravou o `k` com o boost (8,918), que não foi
  aplicado (`total_multiplier` 1). **Ficha certa**: 8,494152, o produto sem boost.
- **Sistema perdido (Duel 1, Vavada 5).** A IA gravou o `k` da BetBy (13,05, a SOMA das
  linhas) e o `totalOdds` da Altenar (média arredondada em 2 casas, 6,86). **Ficha certa**:
  média exata das linhas, `§7.3`.
- **Anulada simples (Bet Panda, 1).** `refund` com `k` 1. A IA gravou 1,00; a Ficha, a odd da
  seleção (3,71). **Ficha certa** pelo `§5.1.1` (preservar a odd original).
- **Aberta (Bet Panda, 1).** IA 4,19 (`k`), Ficha 4,1904; `potential_win` 104,76 = 25 × 4,1904.
  **Ficha certa.**
- **Ganha, as duas fecham o retorno no centavo (8 Bet Panda, 2 Vavada).** Simples a 1,85 e
  1,9 com retorno arredondado pela casa (73,77 × 1,85 = 136,4745 → 136,47), e múltiplas em que
  a IA gravou retorno ÷ stake. A Ficha fica com a odd da casa, pela regra aprovada (Ficha §3).
  **Empate técnico, Ficha pela regra.** Um caso dá meio centavo contra a Ficha:
  `2720757024458679045`, 25 × 4,5854 = 114,635 e a casa pagou 114,64 (IA 4,5856).
- **Sistema todo ganho (Bet Panda, 1).** Média 4,2028 contra 151,30 ÷ 36 = 4,20278: diferença
  de 0,0008 USDT.

## As 2 recusas: a Ficha está certa ao recusar, e a IA perdeu dinheiro

Shuffle `CfqYSukd8DqCGMcrVfm4x` (`originalAmount` 90, `amount` 59,56171948, ganha 1,82) e
`CfqYLyfrUE83UiEDGEHR8` (60 → 58,1435833, perdida). É **cashout parcial**: parte da stake foi
vendida antes, e o valor recebido nessa venda **não está no cru**. A IA gravou só a parte
que ficou (stake 59,56 e 58,14), então o resultado das partes vendidas (30,44 e 1,86 de
stake) não está em `bilhetes`. A Ficha recusa com o motivo. Para medir o P/L que falta, é
preciso achar onde a Shuffle publica a venda.

## Achados fora da régua

1. **O cru da MyStake guarda o login da conta** (`Player.Name`, `Player.ExternalID`). O
   filtro por nome exato do `app/cru.py` tem `playerId`, mas não `Player`. Não mexi: o filtro é da
   extensão e do servidor juntos (`test_filtro_da_extensao_e_o_mesmo_do_servidor`).
2. **Não medidos, recusados pelo adaptador até haver amostra:** bet builder da Altenar
   (14 bilhetes nas fixtures da Esportiva e da VaideBet), odd oferecida da Tivo (4 na
   Betfast), sistema da Tivo, freebet e cashout parcial da BetBy e da Altenar.
3. **A Altenar TRUNCA o pagamento** (dupla de 7,619486 sobre 25 pagou 190,48, não 190,49). O
   `derivar` cai em retorno ÷ stake, igual à IA. Está preso em teste.

## Gate

`tests/test_adaptadores_familias.py` (crus reais reduzidos em `tests/ficha_crus_familias.json`,
sem dado de pessoa): 9 mutações, 9 detectadas. `test_cru.py` passa a exigir as fixtures das
quatro famílias (Ficha do cru filtrado = sem filtro). `pytest tests`: 1803 verde.
