# Régua Ficha × IA nos crus guardados (s409, 12/10/2026)

**Harness:** `medir_regua_adaptadores.py` (nesta pasta). Banco só leitura, sem IA, sem custo.
**Amostra:** os crus de `captura_crua` em 12/10 (teste do Feca, contas Feca e Ellen), 6 casas,
5 famílias. Adaptadores `jb`, `shf`, `tv`, `vb` novos; `dx` sem mudança. Comparados com o
bilhete da IA de mesmo código na mesma conta: stake, odd, resultado, retorno e freebet. É uma
rodada, de um dia, de duas contas: placar, não taxa.

## Tabela por casa (2ª rodada, 12/10, depois das correções do Feca)

559 crus: os 545 da 1ª rodada mais 14 da Shuffle que chegaram depois. Com o `derivar` corrigido
no sistema ganho e o `shf` aceitando o aceite parcial:

| Casa | Família | Crus | Batem nos 5 campos | Só a odd difere, P/L igual (< 0,01) | Divergem com dinheiro | Recusadas |
|---|---|---:|---:|---:|---:|---:|
| Bet Panda | jb | 167 | 118 | 49 | 0 | 0 |
| Duel | jb | 65 | 44 | 21 | 0 | 0 |
| DEX Sport | dx | 55 | 55 | 0 | 0 | 0 |
| MyStake | tv | 137 | 137 | 0 | 0 | 0 |
| Shuffle | shf | 86 | 86 | 0 | 0 | 0 |
| Vavada | vb | 49 | 41 | 8 | 0 | 0 |
| **Total** | | **559** | **481** | **78** | **0** | **0** |

Stake (no centavo), resultado, retorno e freebet batem em **todos** os 559. Nenhum cru ficou
sem bilhete. As 28 freebets da MyStake batem dos dois lados.

**1ª rodada (545 crus), para registro:** 463 batiam, 76 só na odd, **4 divergiam com dinheiro**
e **2 eram recusadas**. As 4 eram defeito do `derivar`; as 2, leitura errada minha no `shf`.
As duas seções abaixo dizem o que era e como ficou.

## Liquidadas comparadas, por casa e por dono (D12)

A virada exige **30 liquidadas comparadas por casa** (decisão do Feca, 11/10). Conta a aposta
(código distinto, não o cru) em que a Ficha **e** a IA estão liquidadas (W, L, V, HW, HL);
aberta de qualquer lado não conta. Feca e Gabriel separados. Mesmo harness, seção
"Liquidadas comparadas"; conferido por SELECT independente (mesmos números nas 6 casas).
Medição de 12/10, ~14h UTC.

| Casa | Feca | Gabriel | Casa | Das do Feca: batem / só odd / divergem | Ganhas na Ficha | Piso de 30 |
|---|---:|---:|---:|---|---:|---|
| Bet Panda | 163 | 0 | 163 | 115 / 48 / 0 | 46 | atinge |
| Duel | 60 | 0 | 60 | 39 / 21 / 0 | 7 + 5 cashout | atinge |
| DEX Sport | 52 | 0 | 52 | 52 / 0 / 0 | 10 | atinge |
| MyStake | 135 | 0 | 135 | 135 / 0 / 0 | 13 | atinge |
| Shuffle | 63 | 0 | 63 | 63 / 0 / 0 | 25 | atinge |
| Vavada | 45 | 0 | 45 | 37 / 8 / 0 | 9 | atinge |

O Gabriel ainda não mandou cru (a 0.7.51 não estava instalada na máquina dele). Todas as
liquidadas do Feca vêm da varredura de histórico de 12/10, não de aposta nova. Atingir o piso
não vira a casa: a virada de cada uma só acontece com o "pode" do Feca. Onde a odd e o retorno
pesam é na ganha, e há poucas em algumas casas (DEX 10, Duel 7, Vavada 9).

## As 4 divergências com dinheiro: a IA estava certa, e o `derivar` foi corrigido

As quatro são **sistema ganho**. O adaptador dá a odd estrutural (média das linhas,
`MASTER_RESULTADO §7.3`), e o `ficha.derivar` aplicava a regra "sistema: odd da casa" também
no W. O `§7.1` manda `W com retorno visível → Retorno ÷ Stake`, que é o que a IA gravou.

| Casa | Código | Stake | Retorno (cru) | Ficha antes | Ficha agora | IA | P/L a mais na Ficha antes |
|---|---|---:|---:|---:|---:|---:|---:|
| Bet Panda | 2719953703015690358 | 60 | `result_sum` 88,94 | 4,1691 | 1,4823333333 | 1,48233333 | 161,21 USDT |
| Vavada | 5504514128 | 43,5 | `totalWin` 69 | 5,1184 | 1,5862068966 | 1,586206896551724 | 153,65 USDT |
| Vavada | 5504503270 | 60 | `totalWin` 84 | 3,9551 | 1,4 | 1,4 | 153,31 USDT |
| Vavada | 5504412582 | 60 | `totalWin` 86,1 | 4,4783 | 1,435 | 1,435 | 182,60 USDT |

Prova: no sistema só parte das linhas paga (Bet Panda: 1 de 3 duplas, `combinations[1]`
`status won`, 20 × 4,447 = 88,94). Com a odd média, o P/L seria `stake × (odd − 1)` sobre a
stake inteira, como se todas as linhas tivessem ganho: 650,77 USDT a mais nos quatro.

**Correção (aprovada pelo Feca, 12/10):** sistema W → retorno ÷ stake, em 10 casas (a régua
do `repository._veredito_do_retorno`; a mesma passou a valer no cashout e no "nenhuma odd
fecha", que davam 28 casas). Sistema perdido, anulado e aberto seguem com a média (§7.3);
meia vitória em sistema, sem amostra, fica com a odd da casa (§7.1). Gate:
`test_sistema_ganho_e_retorno_sobre_stake`, com os 4 crus reais.

## As 2 "recusas" da Shuffle: aceite parcial, e a IA estava certa

Shuffle `CfqYSukd8DqCGMcrVfm4x` (`originalAmount` 90, `amount` 59,56171948, ganha a 1,82) e
`CfqYLyfrUE83UiEDGEHR8` (60 → 58,1435833, perdida). Na 1ª rodada eu li como venda parcial.
**Estava errado.** Conferido pelo Feca na tela da casa: ele pediu 90 e 60, e a casa ACEITOU
59,56 e 58,14, que é o valor de "Sua Aposta" na tela. O ganho de 108,40 é 59,56171948 × 1,82
= 108,40232945, o `payout` exato. Não houve resgate antecipado, e o 1 USDT de ajuste visto na
conta é a taxa do saque. **Não falta P/L nenhum em `bilhetes`: a IA gravou certo.**

**Correção:** a stake é sempre o `amount` (o aceito). O `originalAmount` (o pedido) nunca vira
stake: vai à Ficha só como informação, no campo `stake_pedida`. Nos 2 casos a Ficha agora
bate com a IA (stake 59,56171948 e 58,1435833 contra 59,56 e 58,14: o cru tem 8 casas e a IA
gravou o centavo da tela; P/L igual a menos de 0,004 USDT). Gate:
`test_shf_aceite_parcial_a_stake_e_o_amount_aceito`, com os 2 crus reais.

## De onde cada família tira a stake: sempre o valor aceito pela casa

| Família | Campo da stake | O que mais o cru traz, e por que não é a stake |
|---|---|---|
| `dx` (DEX Sport) | `amount` | nenhum outro valor de aposta no bilhete |
| `jb` (BetBy: Bet Panda, Duel) | `sum` | `combinations[].stake` é a stake de cada linha do sistema; a soma delas = `sum` nos 3 sistemas |
| `tv` (Tivo: MyStake) | `Amount` | `Items[].CalculatedBetAmount` não soma a stake (0 de 137): é conta interna por perna |
| `vb` (Altenar: Vavada) | `totalStake` | `finalStake` = `totalStake` nos 49 (se diferir, o adaptador recusa); `unitStake` é por linha; `openStake` é a parte ainda aberta (= stake só nas 4 abertas) |
| `shf` (Shuffle) | `amount` | `originalAmount` é o PEDIDO (nulo em 84 de 86; 90 e 60 nos 2 aceites parciais) e fica em `stake_pedida` |

Prova de que é o aceito: a stake bate com a IA no centavo nos 559, e nos ganhos o retorno da
casa fecha sobre ela.

## As 78 em que só a odd difere

Nenhuma move dinheiro (diferença de P/L < 0,01 na moeda da conta). São as 76 da 1ª rodada,
mais 2 sistemas ganhos que agora só diferem nas casas da dízima (Bet Panda
2719953703015690358 e Vavada 5504514128: retorno ÷ stake dos dois lados, a Ficha em 10 casas).
Quem está certo:

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
- **Sistema ganho (Bet Panda 2, Vavada 1).** Retorno ÷ stake dos dois lados; a Ficha grava 10
  casas (1,4823333333; 4,2027777778; 1,5862068966) e a IA, outro número de casas. Só dízima.

## Achados fora da régua

1. **O cru da MyStake guardava o login da conta** (`Player.Name`, `Player.ExternalID`), e o da
   DEX, o apelido da conta (`nickname`, no topo dos 55). A varredura dos nomes de campo das 5
   famílias não achou outro. **Corrigido (Feca, 12/10):** os dois entraram na lista do
   `app/cru.py`, só no servidor; a extensão segue com a lista antiga, e o teste passou a exigir
   que a do servidor CONTENHA a dela. Os 192 crus já gravados (137 MyStake, 55 DEX) foram
   limpos e tiveram o hash recalculado, com cópia das linhas antes.
2. **Não medidos, recusados pelo adaptador até haver amostra:** bet builder da Altenar
   (14 bilhetes nas fixtures da Esportiva e da VaideBet), odd oferecida da Tivo (4 na
   Betfast), sistema da Tivo, freebet e cashout parcial da BetBy e da Altenar. Família nova:
   varrer os nomes de campo dos crus dela antes de ligar o adaptador.
3. **A Altenar TRUNCA o pagamento** (dupla de 7,619486 sobre 25 pagou 190,48, não 190,49). O
   `derivar` cai em retorno ÷ stake, igual à IA. Está preso em teste.

## Gate

`tests/test_adaptadores_familias.py` (crus reais reduzidos em `tests/ficha_crus_familias.json`,
sem dado de pessoa): 12 mutações, 12 detectadas. `tests/test_cru.py` exige as fixtures das
quatro famílias (Ficha do cru filtrado = sem filtro) e a lista do servidor contendo a da
extensão: 9 mutações, 9 detectadas.
