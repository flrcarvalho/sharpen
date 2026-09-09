# PLANO — Barreira de recaptura (não pagar duas vezes pelo mesmo bilhete)

> **Status:** proposto e medido em 2026-09-09 (sessão 334). **Fase 0 (registro em modo
> escuro) aplicada na mesma sessão.** Fases 1 e 2 não iniciadas.
> Origem: pergunta do Feca. *"Se eu extrair as últimas 48h na Bet365, e daqui a 2 horas
> extrair de novo para atualizar meu resultado aberto, como não pagar 2x pelos mesmos
> 100 bilhetes?"*
>
> Todos os números vêm de medição direta: 15.729 blocos reais da `sombra_rotulos`
> (13 dias, 21 casas) e a conta de `uso_tokens`. Câmbio: PTAX de 04/09/2026 = R$ 5,1253.
>
> Companheiros: [`ESTUDO_PRECIFICACAO_2026.md`](ESTUDO_PRECIFICACAO_2026.md) (a conta) ·
> [`PLANO_TRADUTOR_DETERMINISTICO.md`](PLANO_TRADUTOR_DETERMINISTICO.md) (a outra metade).

---

## 1. O problema, medido

Hoje **toda** captura vai inteira para a IA. A dedup acontece **depois**, no `upsert`, por
assinatura. Ou seja: o bilhete que o banco já tem é lido, pago e traduzido de novo, para
no fim colidir com a linha que já existia.

Dos **15.318 blocos com código** que passaram pela IA em 13 dias:

| | Blocos | % |
|---|---|---|
| Primeira leitura daquele bilhete | 8.753 | 57,1 % |
| **Releitura de bloco IDÊNTICO** | **4.975** | **32,5 %** |
| Releitura de bilhete que mudou de estado | 1.590 | 10,4 % |

**Um terço da conta é reler byte a byte o que já está no banco.** Na Bet365 é 39,9 %.

E o alcance é quase total: **99,3 %** dos bilhetes de extração dos últimos 30 dias têm
código (22.492 de 22.658). Print e casa sem marcador são 0,7 %.

---

## 2. A chave: hash do bloco, não (id, resultado)

A proposta original do Feca era conferir **ID e resultado**. Está certa, e foi medida
contra a alternativa (guardar o hash do bloco cru inteiro):

| Situação | Blocos | (id, resultado) | Hash do bloco |
|---|---|---|---|
| Bloco idêntico | 4.988 (75,4 %) | pula | pula |
| Mudou **e** o `Status:` mudou | 1.474 (22,3 %) | reprocessa | reprocessa |
| Mudou e o `Status:` ficou igual | **154 (2,3 %)** | **pula, e perde** | reprocessa |

As duas acertam 97,7 % igual. **O hash ganha por dois motivos, e o segundo é o que
decide:**

1. Pega os 2,3 % que a outra deixaria passar.
2. **Não interpreta nada.** O texto de status do bloco não é fonte confiável de estado:
   `_resultadoB3` (`extensor/content.js`) escreve `Ganho → W` para **qualquer** retorno
   maior que a stake, meia vitória inclusive. Uma chave que leia rótulo herda esse
   defeito; uma que compare bytes não tem o que herdar.
   → o mesmo princípio do `CLAUDE.md`, *"o rótulo não é a prova"*.

E quando um bilhete liquida, **não muda só o status.** Caso real da Novibet:

```
- Status: Em aberto (aguardando resultado)      + Status: Ganhou → W
- Odd: 4,59666667                               + Odd: 2,89666667 (= Retorno ÷ Stake)
- Retorno potencial: R$ 746,91                  + Retorno: R$ 746,91
                                                + Liquidado em: 27/08/2026 10:10:57
```

A odd muda junto. Bytes iguais é a única garantia de que **nada** mudou.

---

## 3. O ganho, simulado lote a lote

Simulação cronológica sobre os 383 lotes de extração reais da janela, com o modelo
`custo = A(chamada) + B×chunks + C×blocos`, calibrado nos agregados de `uso_tokens`.

**Validação do modelo, que é o que autoriza o resto:** ele calcula US$ 203,44 para um
período cuja conta real foi **US$ 194,60**. Erro de **+4,5 %**, e para cima.

| | Resultado |
|---|---|
| Blocos processados | **−32,2 %** |
| **Custo** | **−29,3 %** |

O corte de custo é **menor** que o de blocos, de propósito no modelo e na vida: o pedágio
(o manual relido a cada pedaço) só cai quando cai o **número de pedaços**, e uma extração
que fica com 5 blocos ainda paga os mesmos 4 pedaços de uma que tinha 20.

### Sobre a conta real

| | Hoje | Pós-barreira |
|---|---|---|
| Custo variável de API | US$ 379/mês | **US$ 268/mês** |
| Aquecedor (fixo) | US$ 12,5/mês | US$ 12,5/mês |
| **Total de API** | **US$ 391/mês** | **US$ 281/mês** |
| Em reais | R$ 2.006 | **R$ 1.438** |
| **Custo por bilhete** | R$ 0,092 | **R$ 0,065** |

### Por casa, o corte é desigual

| Casa | Corte |
|---|---|
| **Bet365** | **−38,6 %** |
| Betano | −26,2 % |
| Betfair | −24,5 % |
| Pinnacle | −23,3 % |
| 1xBet | −9,8 % |
| Superbet | −7,7 % |
| Betfast | −5,9 % |
| SportingBet | −0,9 % |

O corte é proporcional a **quanto aquela casa é recapturada**, não ao tamanho dela. A
Bet365 lidera porque é onde está o hábito de conferir resultado.

### Somada ao tradutor

As duas atacam metades diferentes: a barreira mata a **releitura** (32,5 %), o tradutor
mata a **primeira leitura** (até 70,7 % dela, na Bet365). Encadeadas na Bet365:
US$ 122 → US$ 75 (barreira) → cerca de **US$ 22** (tradutor). Composição de dois
modelos, não medição: trate como ordem de grandeza.

---

## 4. Velocidade: quase não muda, e é bom saber antes

Modelo de tempo (ondas de 8 pedaços simultâneos × 26,5 s por pedaço, medido na s301):

| | Antes | Depois | Ganho |
|---|---|---|---|
| **Mediana** | 30,5 s | **30,5 s** | **0 %** |
| p90 | 57,0 s | 57,0 s | 0 % |
| p99 | 242,5 s | 136,5 s | −43,7 % |
| Pior caso | 401,5 s | 216,0 s | −46,2 % |
| Média | 44,3 s | 36,9 s | −16,6 % |

**No dia a dia o usuário não ganha tempo.** Os pedaços já correm em paralelo, então o
relógio é o tempo de **um** pedaço vezes o número de ondas — e uma extração de 20
bilhetes vira 4 pedaços tanto antes quanto depois. O ganho só aparece quando a extração
cruza uma fronteira de onda.

Onde o usuário ganha de verdade é quando a extração fica **vazia**: nada mudou, nenhuma
chamada acontece, 30 s viram menos de 1. Na janela medida isso foi **2,3 %** das
extrações, **e esse número está subestimado de propósito**: ele reflete o hábito atual, em
que recapturar é caro. Barateando, o hábito muda.

> ⚠️ O número de custo é simulação validada contra a conta real (erro +4,5 %). **O de
> tempo é modelo puro**, sem A/B, e ignora rede e banco. Não prometa os 43 % de p99 a
> ninguém antes de medir na produção.

---

## 5. As fases

| Fase | O que entrega | Como se prova pronta |
|---|---|---|
| **0 · Registro escuro** ✅ | tabela `bloco_visto` + gravação do hash a cada extração; **nada é filtrado** | linhas aparecendo em produção; o log diz quantos blocos SERIAM pulados |
| **1 · Filtro** | o filtro liga, com as três costuras do §6 | replay do harness verde + cobertura intacta |
| **2 · Medição** | comparar `uso_tokens` antes/depois em 30 dias | custo por bilhete cai ~29 % sem bilhete perdido |

A Fase 0 existe para que o número do §3 seja **conferido em produção antes** de qualquer
byte deixar de ser processado. Ela não muda comportamento nenhum.

---

## 6. As quatro costuras — onde uma implementação apressada quebra

Nenhuma delas dá erro. Todas dão **dado faltando em silêncio**, que é o modo de falha que
este repo mais paga caro.

1. **A conferência de cobertura precisa saber do filtro.** `conferir_cobertura` cobra
   quantidade por código: mandou N, tem de voltar N. Filtrando blocos antes do chunker sem
   avisá-la, ela acusa perda que não houve. O esperado passa a ser o **filtrado**.

2. **A reconciliação de órfãs precisa ver TODOS os blocos, não só os filtrados.**
   `_reconciliar_orfas` adota linha antiga sem código casando com o bloco que chegou
   (`checar_fidelidade`). Escondendo dela os blocos já conhecidos, uma órfã perde a chance
   de ser adotada e **vira fantasma** — exatamente o caso do Falkirk (s327). O filtro é
   sobre o que vai para a IA, **nunca** sobre o que a reconciliação enxerga.

3. **Bilhete sem código não passa pela barreira.** Print, texto colado e casa sem marcador
   não têm chave. Continuam indo inteiros para a IA, como hoje. São 0,7 % do volume.

4. **Lote que fica VAZIO não pode virar erro.** Extração em que nada mudou é sucesso, não
   falha: a resposta é "nada novo", com o `done` normal. Tratar como erro treinaria o
   usuário a desconfiar do caso mais comum depois da barreira.

---

## 7. A chave e a tabela

```
bloco_visto (dono, casa, codigo)  →  hash do bloco cru
```

- **Tabela própria, não `sombra_rotulos`.** A sombra tem retenção de 120 dias, grava uma
  linha por **extração** (o mesmo bilhete N vezes, de propósito) e é da Fase 0 do
  tradutor — some quando ele virar. A barreira precisa de **uma linha por bilhete**,
  permanente.
- **Não é coluna em `bilhetes`.** Ficar fora do `upsert` mantém o hot path de dedup
  intocado e a barreira sem acoplamento nenhum. Mesmo princípio da lixeira: tabela
  separada tem acoplamento zero por construção.
- **A chave não inclui `parceiro`**, ao contrário da assinatura de dedup. Código de
  bilhete é único dentro da casa; o mesmo dono ter duas contas na mesma casa com o mesmo
  código não é cenário real. **Limitação declarada**, não esquecimento.

---

## 8. O que este plano NÃO resolve

- **Não reduz o tempo de espera no caso comum** (§4). Quem quiser velocidade tem de mexer
  no piso de 26,5 s por pedaço e no teto de 8 simultâneos, que é outra conversa e esbarra
  em limite de taxa da API.
- **Não ajuda print nem casa sem marcador.** 0,7 % do volume segue como hoje.
- **Não substitui o tradutor.** Ela corta releitura; ele corta primeira leitura. O teto de
  R$ 149 do estudo de preço continua dependendo dos dois.

---

VERSÃO: 2026
ATUALIZADO: 2026-09-09 (sessão 334 — plano criado e Fase 0 aplicada)
