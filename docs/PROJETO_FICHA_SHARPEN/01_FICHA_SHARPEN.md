# 01 · A Ficha Sharpen (v1, aprovada pelo Feca no D0, 11/10/2026)

> A Ficha é a peça da qual todo o resto depende. Se ela nascer errada, cada casa herda o erro.
> Por isso ela é aprovada **antes** de qualquer código.

## 1. O que é

É o formato único em que **toda casa** entrega uma aposta ao Sharpen. A extensão monta a Ficha a partir
da ficha da própria casa (o JSON que o ouvinte já captura hoje) e manda ao servidor. O servidor grava
sem IA.

Separação de responsabilidades:

| Quem | Faz | Nunca faz |
|---|---|---|
| **Extensão (adaptador por casa)** | copia da casa, **sem interpretar**: valores, datas, status, textos de mercado e seleção como a casa escreve | traduzir vocabulário, decidir data da planilha, calcular resultado |
| **Servidor (regras fixas)** | deriva o que a planilha mostra: data, resultado W/L/V/HW/HL, odd da planilha, descrição por modelo | chamar IA no caminho da aposta |
| **Dicionário + IA em lote** | traduz termo da casa para termo do Sharpen (esporte, categoria), **uma vez por termo** | tocar em número |

## 2. Os campos

Valores numéricos viajam como **texto com ponto decimal** (`"50.00"`), nunca como número de ponto
flutuante, para não perder centavo. Datas em **ISO 8601 com fuso** (`"2026-10-05T21:42:00Z"`).

### 2.1 A aposta

| Campo | Tipo | Obrigatório | Origem e observação |
|---|---|---|---|
| `versao` | `"ficha/1"` | sim | versão do formato |
| `casa` | texto canônico (`DEXSPORT`, `MEGAPARI`...) | sim | a mesma chave de `casas/CASA_<chave>.md` |
| `codigo` | texto | sim | **exatamente como a casa entrega**, com maiúsculas e minúsculas (resolve o furo do porteiro por construção) |
| `colocada_em` | data-hora ISO | sim | quando a aposta foi feita |
| `liquidada_em` | data-hora ISO ou nulo | não | quando a casa liquidou; nulo em aberta |
| `status` | `aberta` · `ganha` · `perdida` · `anulada` · `meio_ganha` · `meio_perdida` · `cashout` | sim | de-para fixo por adaptador; status desconhecido = **erro visível**, nunca chute |
| `status_casa` | texto | sim | o status cru da casa, para auditoria |
| `moeda` | `BRL`, `USD`, `USDT`... | sim | a da conta na casa; ausência é erro, não "real por padrão" |
| `stake` | decimal | sim | valor apostado |
| `stake_freebet` | decimal | não | parte paga com dinheiro da casa |
| `odd` | decimal | sim | odd do bilhete como a casa mostra |
| `odd_calculada` | booleano | sim | `true` quando a casa não dá a odd combinada e o adaptador multiplicou as pernas |
| `retorno` | decimal ou nulo | não | quanto voltou (inclui cashout) |
| `tipo` | `simples` · `multipla` · `sistema` | sim | |
| `sistema` | texto ou nulo | não | estrutura do sistema, ex. `3x Duplas` |
| `pernas` | lista | sim | ver 2.2 (simples tem 1 perna) |
| `impressao` | texto | sim | hash do objeto cru da casa: muda quando a casa muda algo no bilhete |
| `origem` | texto | sim | `extensao:<ouvinte>@<versão da extensão>` |

### 2.2 Cada perna

| Campo | Tipo | Obrigatório | Observação |
|---|---|---|---|
| `esporte_casa` | texto | não | como a casa escreve (`Basketball`, `MMA/UFC`) |
| `liga_casa` | texto | não | |
| `evento` | texto | sim | como a casa escreve (`Flamengo - Palmeiras`) |
| `mandante`, `visitante` | texto | não | quando a casa separa |
| `mercado_casa` | texto | sim* | o tipo de aposta **em campo próprio**. *Nas casas em que a casa mistura mercado e seleção num campo só (família 1xBet, `EventTypeName`), vai o texto inteiro aqui e `selecao_casa` fica vazio |
| `selecao_casa` | texto | sim* | a escolha (`Sim`, `Over 2.5`, `Fenerbahce -8.5`) |
| `linha` | decimal ou nulo | não | handicap ou total, quando a casa separa |
| `odd` | decimal | sim | odd da perna |
| `inicio` | data-hora ISO ou nulo | não | início do jogo |
| `status_perna` | mesmo enum do bilhete | não | quando a casa informa por perna |

## 3. O que o servidor deriva (regras fixas, sem IA)

| Coluna da planilha | Regra | Fonte da regra |
|---|---|---|
| **Data** | simples: dia do `inicio` da perna; múltipla: dia do `inicio` da perna mais recente; múltipla perdida com perna marcada perdida e com início: dia do início da perna perdida mais cedo (nunca anda para frente); sem `inicio`: dia da `colocada_em`. Sempre no fuso de Brasília **na exibição** | `MASTER_OUTPUT §4` e `§4.0.1` |
| **Resultado** | `ganha`→W · `perdida`→L · `anulada`→V · `meio_ganha`→HW · `meio_perdida`→HL · `aberta`→vazio · `cashout`→W ou V conforme retorno × stake | `MASTER_RESULTADO §1, §4, §5` |
| **Odd** | tabela de decisão: W com retorno → retorno ÷ stake; W com cashout ≠ stake → cashout ÷ stake; demais → `odd` do bilhete | `MASTER_RESULTADO §2` |
| **Stake** | `stake` | — |
| **Esporte** | dicionário (`casa` + `esporte_casa`); várias pernas de esportes diferentes → `Múltiplos` | `04_DICIONARIO.md` |
| **Aposta (categoria)** | simples: dicionário (`casa` + `mercado_casa`); múltipla → `Múltipla` | `04_DICIONARIO.md` |
| **Descrição** | modelo fixo: `<selecao_casa> <mercado_casa> [<evento>]`, pernas unidas por ` // `. Fica com o termo da casa e **nunca é reescrita** pelo dicionário (casa em inglês = descrição em inglês) | decisão do Feca: descrição pode variar (D0, 11/10) |
| **Código** | `codigo` | — |
| **Casa, Parceiro** | da conta escolhida no pareamento, nunca da Ficha | igual a hoje (`app/main.py:4100-4123`) |

Termo que o dicionário não conhece: a aposta **grava assim mesmo**, com o termo da casa, e o termo vai
para a fila de classificação. Ver `04_DICIONARIO.md`.

## 4. Gravação

- Chave: **dono + casa + conta + `codigo`**. Idempotente: a mesma Ficha duas vezes não duplica.
- Se a `impressao` não mudou, não faz nada. Se mudou, atualiza (é assim que uma aberta vira liquidada).
- Aposta já liquidada no banco não volta para aberta.
- **Fase de transição:** a Ficha é convertida para o formato atual de `bilhetes` (texto com vírgula,
  data `DD/MM/AAAA`), para nenhuma tela quebrar. A Ficha crua é guardada inteira em tabela própria,
  para a migração do banco para número e data de verdade acontecer depois, sem perder nada.

## 5. Entrega

- A extensão manda **só o que é novo ou mudou**, comparando `codigo` + `impressao` com o que ela já mandou
  (memória local). Na recaptura das 11h, das 40 apostas viajam 2.
- Durante o modo sombra, a extensão manda **as duas coisas**: o texto de hoje e as Fichas. O caminho velho
  continua mandando no banco até a virada da casa.
- Entrega autenticada direto ao servidor; a tela é avisada pelo canal de eventos que já existe
  (`app/eventos.py`), sem perguntar a cada 2,5 s.

## 6. O que cada família de outubro já entrega (ponto de partida dos adaptadores)

| Família (ouvinte) | Casas de outubro | Datas que a casa dá | Mercado |
|---|---|---|---|
| `dx_inject` | DEX Sport | evento + colocação | campo próprio |
| `x1_inject` | Megapari, PariPesa, SapphireBet, 1xBit | evento + colocação | **misturado** com a seleção (`EventTypeName`) |
| `tv_inject` (BetConstruct) | MyStake | evento + colocação | campo próprio (`- <mercado>: <seleção>`) |
| `jb_inject` (BetBy) | Betpanda, Duel, Betfury, Betcoin | evento + colocação | campo próprio; moeda quando não é real |
| `vb_inject` (Altenar) | BetMartini, Betrebels, Vavada, Kikobet | evento + colocação | campo próprio (`marketName` / `name`); **não emite moeda hoje**, e a Betrebels tem conta em USDT |
| `shf_inject` | Shuffle | evento + colocação + liquidação | campo próprio |

Prova: frente F6 do mapa (`Auditorias\mapa_2026-10\claude\frentes\F6\F6.md`) e
`extensor/content.js` (formatadores 4625, 3972, 5193, 4473, 5655, 4787).

## 7. Pós

- Números saem da fonte: cumpre "100% exatos" sem fiscal e sem modelo.
- Uma Ficha, todas as casas: casa nova vira um adaptador pequeno, não um manual de 7 a 16 mil tokens.
- Três datas guardadas em vez de uma "Data" com quatro sentidos.
- Moeda obrigatória: acaba o "nulo significa real".
- O termo original da casa fica guardado: pronto para outra língua.

## 8. Contras

- Exige mexer na extensão (um adaptador por família) e publicar versão nova; usuários na versão antiga
  ficam no caminho velho até atualizar.
- A família 1xBet não separa mercado de seleção: o dicionário dela trabalha com o texto inteiro, e o
  número de termos tende a ser maior.
- A descrição por modelo fica menos elegante que a da IA.
- Na transição, convivem a Ficha crua e o formato antigo de `bilhetes`: dois formatos por um tempo.

## 9. Perguntas para o Feca (D0) · respondidas em 11/10/2026

| # | Pergunta | Resposta do Feca |
|---|---|---|
| 1 | Data | **A: a regra do §3 vale**, incluindo "sem início = dia da colocação". Nas 6 famílias de outubro todo ouvinte já entrega o início por perna (`extensor/content.js:4656, 5257, 5303, 4515, 5746, 4865`; `extensor/x1_inject.js:143`), então a última linha é rede de segurança aqui e vale de verdade na fase de prints, PDF, texto e bot. Lido no código; pernas sem início nas fixtures **não foram contadas**. |
| 2 | Termo desconhecido | **A: grava na hora** com o termo da casa; o lote classifica depois e atualiza só Esporte e Aposta. |
| 2b | A descrição muda depois da tradução? | **Não.** Fica com o termo original (casa em inglês = descrição em inglês). "A descrição não tem essa importância toda." |
| 3 | Descrição por modelo | **A: serve.** |
| 4 | Revisão antes de salvar | **A: entra direto**; correção na planilha. |
| 5 | Moeda ausente | **A: moeda cadastrada na conta.** |

Texto original das perguntas:

1. **Data:** a regra do §3 (início do jogo; múltipla = perna mais recente; múltipla perdida = perna
   perdida mais cedo; sem início = colocação) continua sendo a regra do produto?
2. **Termo desconhecido:** a aposta grava na hora com o termo da casa e é classificada minutos depois
   (rápido, sem IA no caminho), **ou** espera a IA classificar antes de aparecer (mais lento, sempre
   "bonita")? Recomendação: gravar na hora.
3. **Descrição:** o modelo `<seleção> <mercado> [<evento>]` serve?
4. **Revisão antes de salvar:** some (a aposta entra direto) ou vira uma caixa de "novas apostas" para
   conferir? Recomendação: entra direto; a planilha já permite editar.
5. **Moeda ausente** (Altenar hoje): bloquear a casa até o adaptador mandar a moeda, ou assumir a moeda
   cadastrada na conta? Recomendação: moeda da conta.
