# PLANO — "Resolver apostas abertas" (Bet365)

> Estado (s382): **aprovado pelo Feca, e o primeiro passo está NO REPO.** O carimbo de
> colocação (`bilhetes.aposta_em`) já viaja da casa até o banco — falta a extensão chegar
> aos testers para o dado começar a entrar. O resto do desenho segue por implementar.
>
> **Escopo encolhido por decisão do Feca (22/09):** *"não tem problema não resolver as
> abertas, e passar a resolver as próximas extrações"*. As 480 abertas que já existem
> ficam de fora, e com elas sai o fallback de janela chutada (§6.3) — que era a parte mais
> cara e mais imprecisa do plano.
>
> Depende do conserto da truncagem da expansão (fila, item 1). Sem ele, este plano lê uma
> lista incompleta e conclui errado em silêncio.

---

## 1. A dor

Aposta que fica aberta vários dias vira caça manual. A bet365 filtra o histórico pela **data
em que a aposta foi COLOCADA**, e o Sharpen guarda a **data do EVENTO**. Como a lista de
resolvidas reordena por colocação, um bilhete que resolveu ontem mas foi apostado há cinco
dias está enterrado lá atrás, e o operador varre janelas de 2 em 2 dias tentando esbarrar
nele.

Medido em 2026-09-20, numa conta real: **3 bilhetes abertos de 12, 16 e 19/09** que a casa já
tinha parado de listar como pendentes, e que nenhuma das quatro janelas extraídas naquele dia
trouxe de volta.

---

## 2. O que já está medido, e é o que torna isto possível

**A lista já traz o resultado.** Cada resposta de `/sportshistoryapi/summary` carrega, por
bilhete, o registro `01` (identidade e estrutura) e o `02` (dinheiro):

- **`BS`** = status (`0` = aberto)
- **`RT`** = retorno em dinheiro (ausente enquanto aberto)
- **`TP`** = carimbo de tempo do bilhete, com precisão de segundo
- `ST` / `TS` = stake unitária e total · `OD` = odd

O parser (`parseSummary`, `b3_inject.js`) já lê os quatro. Hoje o `RT` só é usado para saber
se o bilhete está aberto; o valor em si é descartado para efeito de resultado.

**O `TP` é estável entre visões e o `ID` não é.** Provado com as duas visões carregadas com 5
minutos de diferença, 6 de 6 pares, conferidos pelo código de comprovante:

```
TP 20260921002749000
  D0  id=49911954609          code=YR5088082431I  stake=160,00
  D1  id=3152534307690061594  code=YR5088082431I  stake=160,00
```

**O `TP` não é único sozinho.** Nas mesmas 269 entradas, **3 `TP` se repetiram dentro da mesma
visão** (aposta feita no mesmo segundo). Precisa de desempatador.

**A régua de retorno para resultado já existe e é determinística**:
`repository._veredito_do_retorno`, as cinco fórmulas de `calcular_pl` lidas ao contrário.

**Custo comparado, medido:** expandir 522 bilhetes custa **35 cliques e 35 segundos**. Abrir
229 detalhes custa **360 segundos**. A lista é ~10% do custo.

---

## 3. A ideia, em uma frase

Para bilhete **que já está no banco como aberto**, o resultado pode vir da LISTA, sem abrir o
detalhe de ninguém: casa-se pelo `TP` + stake + odd e deriva-se o resultado do `RT`.

---

## 3.1 MEDIDO NA TELA (s382): a API aceita a JANELA, e isso encolhe o plano

Medições feitas na conta do Feca, no caminho certo (**bonequinho → Histórico → Apostas
Resolvidas / Pendentes**, `#/ME/X8020`, iframe de `members.bet365.bet.br`):

**1. A casa aceita um intervalo de até SEIS MESES.** Está escrito na própria tela: *"Por
favor note: o intervalo máximo é de seis meses."* Vale para Resolvidas e para Pendentes, que
têm o mesmo seletor (`Últimas 24 horas` · `Últimas 48 horas` · `Intervalo de Datas`).

**2. E a lista sai por API, com a janela nos parâmetros:**

```
GET /sportshistoryapi/summary?settled=1&lid=33&cid=28&csid=0
      &from=2026-09-22T19:06:57.370Z&to=2026-09-23T19:06:57.370Z
```

**É o mesmo endpoint que a captura já escuta e o `parseSummary` já lê.** O que não se sabia é
que ele aceita `from`/`to`.

### O que isso muda

O §4 abaixo continua verdadeiro: **não existe rota por código de comprovante.** Só que a
pergunta deixa de ser essa. Com o carimbo de colocação, o que se tem é uma **data**, e por
data a casa responde direto.

- **A Fase B não precisa navegar pela tela nem clicar em "Mostrar Mais".** Uma chamada por
  janela, com `from`/`to` no dia da aposta.
- **A truncagem da expansão deixa de ser pré-requisito do botão** (segue valendo para a
  captura normal, que é outra coisa). O que a lista traz não depende mais de a página ter
  carregado tudo na tela.
- **O custo cai mais uma vez:** sem cliques, sem expansão, sem esperar altura de página.

### O que ainda NÃO foi medido

- **Paginação.** A resposta traz a janela inteira ou vem em lotes? Na captura normal a página
  pede mais ao rolar, então provavelmente há corte — falta ver qual parâmetro o controla.
- **`settled=0` para as pendentes.** A tela de Pendentes usa o mesmo seletor; presume-se o
  mesmo endpoint com `settled=0`, e presumir não vale. Medir na próxima aba aberta.
- **Quantas requisições a janela larga custa**, contra o teto de volume por conta que
  bloqueou três contas em 20/09.

---

## 4. Por que não dá para "mergulhar direto" no bilhete

A pergunta natural é: se eu sei qual bilhete quero, por que preciso da lista?

Porque **o endereço do detalhe é o `bsid`**, e a rota só aceita `bsid`:

```
#/HICO/BSSB/C<bsid>/D0/     ·     confirmation?bsid,cid,cr,lid,settled
```

Não existe rota por código de comprovante. O catálogo completo de rotas foi levantado em
2026-09-20 e não há nenhuma.

E o `bsid` que guardamos quando o bilhete estava aberto **não serve mais**: ele é do namespace
da visão (`D1` para pendentes e 24h, `D0` para 48h e Intervalo de Datas) e muda quando a
aposta resolve. Sabemos QUEM procurar (o código) e não sabemos ONDE ele está.

A lista é o único lugar que devolve endereços atuais. A saída não é mergulhar direto: é
**parar de precisar do detalhe**, lendo identidade e resultado da própria lista.

---

## 5. O desenho

### Fase A — descobrir o que resolveu (barato, sem escrita)

1. O painel manda à extensão a lista das **abertas daquela conta**: `{id, tp, stake, odd,
   data, criado_em}` por bilhete.
2. A extensão abre **Apostas Pendentes** e expande. É lista curta.
3. Toda aberta nossa que **não aparece** ali já resolveu na casa. Esse é o alvo.

> Esta fase sozinha já responde "quais das minhas abertas estão plantadas" e o descasamento
> de contagem entre o Sharpen e a casa, que hoje se descobre no olho.

### Fase B — achar o resultado (uma expansão por janela)

4. Para os alvos, calcular as **janelas de colocação** a abrir (ver §6, item 3).
5. Para cada janela: abrir **Apostas Resolvidas → Intervalo de Datas** e expandir até o fim.
6. Casar cada bilhete da lista com os alvos pela chave `TP` + stake + odd.
7. Derivar o resultado do `RT` com `_veredito_do_retorno`.
8. `PATCH /bilhetes/{id}` com `resultado` (e `odd` quando a régua devolver odd nova, no ramo
   de cashout).

**Zero `confirmation`. Zero IA. Zero custo de extração.**

### O que fica de fora, de propósito

- **Bilhete novo, nunca visto.** Continua precisando da `confirmation`, porque é de lá que sai
  o código, que é a identidade. Este plano não toca na extração normal.
- **Criar linha.** O botão só ATUALIZA o que já existe. Se a casa tem bilhete que não está no
  banco, isso é trabalho da extração, e o botão apenas reporta o número.

---

## 6. O que muda, arquivo por arquivo

**1. `app/database.py` — uma coluna nova**

```sql
ALTER TABLE bilhetes ADD COLUMN IF NOT EXISTS aposta_em TEXT;
```

O `TP` da casa, verbatim (`20260921002749000`). É o instante em que a aposta foi feita, que é
exatamente o campo pelo qual a casa filtra. Guardá-lo resolve o problema da janela para todo
bilhete capturado dali em diante.

Só a Bet365 preenche por enquanto. Coluna nula não quebra nada.

**2. `extensor/b3_inject.js` e `content.js` — passar o `TP` adiante**

O `tp` já viaja no objeto do bilhete (`parseSummary` o lê). Falta emiti-lo no bloco que a
extração manda ao servidor, e o servidor gravá-lo.

**3. Chave e janela**

- **Chave:** `TP` + stake + odd, normalizados pela régua do projeto (`_norm_odd`, o mesmo
  tratamento de `chave_orfa`).
- **Trava obrigatória, a mesma de órfãs e código fantasma: par ÚNICO NOS DOIS SENTIDOS.** Só
  escreve quando a chave casa **um** alvo com **um** bilhete da lista. Chave ambígua não
  decide nada e o bilhete sai no relatório como "a conferir".
- **Janela:** `aposta_em` quando existir. Sem ela, `[data do evento − 7 dias, min(criado_em,
  hoje)]`, porque `criado_em` é o instante em que a captura viu o bilhete pendente pela
  primeira vez, logo a aposta já existia ali. Janelas que se sobrepõem são unidas antes de
  abrir, para não expandir duas vezes a mesma lista.

**4. `app/main.py` — uma rota nova. FEITA (s382).**

`POST /bet365/resolver-abertas` recebe `encontrados` (o que a extensão leu da lista da casa:
`carimbo`, `stake`, `odd`, `retorno`) e devolve o que faria. **Ensaio é o padrão**; só grava
com `aplicar: true`.

O miolo é puro e mora no `repository.py`, para o gate exercitar a regra e não um dublê dela:

- **`casar_abertas_por_carimbo(abertas, encontrados)`** — par único NOS DOIS SENTIDOS, com a
  chave normalizada (`_norm_odd`, a mesma régua da `chave_orfa`). Devolve os pares e, nomeados,
  os que ficaram de fora: `ambiguos`, `sem_par`, `sem_chave`.
- **`resultado_da_aposta_encontrada(aberta, encontrado)`** — delega ao `_veredito_do_retorno`.
  Nenhuma régua nova; régua duplicada é régua que diverge. Retorno ausente devolve `None` e um
  motivo, nunca `L`.
- **`campos_corrigidos(ids, campos)`** — a trava de correção humana, com **`stake` na lista**
  além de `resultado` e `odd`: a régua LÊ a stake do banco contra o retorno da casa, e stake
  editada à mão com a fonte intacta faz o veredito errar de categoria (o `#262170` da s382).

E a leitura das abertas **não precisou de rota nova**: `/bilhetes?extraction_state=aberta&archived=all`
já serve, e o `SELECT *` já traz o `aposta_em`.

**Gate:** `tests/test_resolver_abertas.py`, **7 mutações, 7 detectadas** (par único em cada um
dos dois sentidos, a odd fora da chave, a odd crua sem `_norm_odd`, retorno ausente virando
zero, a odd da casa mandando em SISTEMA, carimbo de qualquer tamanho). O teste do SISTEMA
precisou ser refeito: a 1ª versão passava a MESMA odd nos dois lados e teria ficado verde com
a exceção apagada.

**5. Painel** — o botão, ao lado de "Reconectar SharpenUp".

---

## 7. As travas, porque aqui errar é pior que não fazer

**Casamento errado não perde bilhete: CORROMPE.** Escreve o resultado de uma aposta em outra,
e o P/L fecha certo nas duas pontas porque os dois valores existem. É a mesma família da
descrição e da stake que vieram do vizinho. Por isso:

1. **Par único nos dois sentidos**, sempre. Na dúvida, não escreve.
2. **Só escreve em `extraction_state = 'aberta'`.** Linha resolvida nunca é tocada por este
   caminho, nem que a chave bata.
3. **Nunca escreve por cima de correção humana.** O mesmo critério do script de reparo: se o
   bilhete tem registro em `correcoes` para `resultado`, pula.
4. **Ensaio primeiro.** O botão mostra o que faria (quantos, quais, com que resultado) e só
   grava no segundo clique. Grupo e banco não têm desfazer.
5. **`RT` ausente com `BS` resolvido não vira zero.** Ausência viaja como ausência: o bilhete
   sai como "a conferir", nunca como `L`. Zero é uma conta feita, não um vazio.

---

## 8. O que NÃO está resolvido, e precisa de medição antes

Estes são os furos honestos do desenho. Nenhum é bloqueio, mas nenhum está provado.

1. ~~**O `RT` cobre todos os desfechos?**~~ **MEDIDO em 2026-09-22, e a resposta é sim.**

   A medição era offline o tempo todo e ninguém tinha visto: o `_resultadoB3` (`content.js`)
   **já deriva o Status do bloco a partir do `t.rt`**, que é o RT do summary, e a
   `sombra_rotulos` guarda o bloco cru desde 26/08. Cruzando **13.115 bilhetes de Bet365**
   com `_veredito_do_retorno`:

   | gravado | conferível | o `RT` reproduz | taxa |
   |---|---|---|---|
   | W | 5.155 | 5.086 | 98,7 % |
   | L | 6.269 | 6.262 | 99,9 % |
   | V | 488 | 483 | 99,0 % |
   | HW | 124 | 124 | **100 %** |
   | HL | 190 | 189 | 99,5 % |

   **Nenhum desfecho sai do escopo.** E **zero bilhetes em SISTEMA** entre os conferíveis,
   então a ressalva do item 2 abaixo não morde na base de hoje.

   As 82 divergências apontam para o **banco**, não para o `RT` — 69 são `W` que o dinheiro
   diz `HW`, todas em linha asiática partida. Viraram item próprio: `BACKLOG 4.9`.

   > A medição tem **circularidade parcial**: o resultado gravado foi decidido pela IA lendo
   > o MESMO bloco de onde saiu o retorno. Onde os dois discordam é onde ela quebra, e é por
   > isso que a divergência vale mais que a taxa.

2. **A odd que a régua usa.** `_veredito_do_retorno` testa a **odd do bloco antes da odd da
   linha**, e é isso que separa meia vitória de vitória cheia. Aqui a "odd do bloco" seria o
   `OD` do `summary`, que é a odd da casa. Em tese é a fonte mais limpa que já tivemos. Em
   SISTEMA não vale (a odd do cupom não é a da linha), então **SISTEMA fica fora até medir**.

3. ~~**Quantos alvos sobram sem `TP`.**~~ **FORA DO ESCOPO por decisão do Feca (22/09).**
   Toda aberta capturada antes desta mudança não tem `aposta_em`, e ele decidiu que elas não
   precisam ser resolvidas: o botão passa a valer para o que a captura vir daqui em diante.
   O fallback de janela chutada, descrito no §6.3, **não será construído**. O que segue
   abaixo fica como registro do que ele custaria.

   **MEDIDO em 2026-09-21: 505 abertas de Bet365 no total**, concentradas em poucos donos
   (`realtrial` 260, `Jonathan` 68, `perereca` 56, `arrudex` 52, `Gabriel` 33, `Feca` 25).
   Todas sem `aposta_em`, por construção. O fallback não é caso de borda, é o caso comum no
   primeiro ano.

   > ⚠️ **ARMADILHA, e ela sozinha mataria a funcionalidade em silêncio.** A coluna
   > `archived` **não é ação do usuário**: `arquivar_bilhetes_antigos` mantém sem arquivar
   > apenas os ~40 bilhetes mais recentes de cada `(casa, parceiro, dono)`, por `criado_em
   > DESC`, e marca todo o resto. Numa conta movimentada, **aposta aberta antiga está SEMPRE
   > arquivada** — as 25 do Feca são 25 de 25. E são justamente as plantadas que este botão
   > existe para resolver.
   >
   > **O alvo NUNCA filtra por `archived`.** Um `WHERE NOT archived` deixaria o botão cego
   > exatamente para o seu caso de uso, e o sintoma seria "não achou nada", sem erro nenhum.

4. ~~**Unicidade da chave em escala.**~~ **MEDIDO em 23/09, com carimbo REAL: zero colisão.**

   O proxy pessimista (dia + stake + odd) tinha dado **11.792 trios repetidos** e não
   autorizava supor nada. Com `aposta_em` gravado de verdade, nos **639 bilhetes** que a
   captura do Jonathan trouxe no primeiro dia da 0.7.18:

   | chave | chaves distintas | grupos com colisão | bilhetes ambíguos |
   |---|---|---|---|
   | carimbo sozinho | 630 | 4 | **13** (2,03%) |
   | carimbo + stake | 633 | 4 | 10 (1,56%) |
   | **carimbo + stake + odd** (a do plano) | **639** | **0** | **0** (0,00%) |

   As duas primeiras linhas são a razão de a chave ter três partes: o carimbo sozinho erra
   em 2% dos bilhetes, exatamente como o plano previa ao dizer que ele não é único (aposta
   feita no mesmo segundo). **A terceira parte zera.**

   > ⚠️ **É medição datada, de UM dono, num dia.** Ela autoriza o desenho, não dispensa a
   > trava: par único nos dois sentidos continua obrigatório, e chave ambígua sai como "a
   > conferir" em vez de decidir. Refazer quando houver mais donos com carimbo.

5. **A truncagem da expansão.** Se a lista vier cortada, a Fase A conclui que um bilhete
   resolveu quando ele só não foi carregado. **Este plano não pode ser ligado antes do item 1
   da fila.**

---

## 9. Custo e ganho

| | hoje | com o botão |
|---|---|---|
| achar uma aberta plantada | varrer janelas de 2 em 2 dias, no olho | Fase A, uma lista curta |
| resolver N abertas achadas | N `confirmation` + N leituras de IA | **0 `confirmation`, 0 IA** |
| requisições contra a casa | ~1 por bilhete da janela | ~1 por página de 10 |

E há um ganho que não é de tempo: o resultado passa a vir de **número da casa**, não de
transcrição de modelo. Foi por transcrição que nasceram os 39 bilhetes com meia vitória
gravada como vitória cheia (s356).

---

## 10. Ordem sugerida

1. ~~Medir o §8.1~~ **FEITO (s382).** O plano se sustenta nos cinco desfechos.
2. ~~Gravar o `TP` (`aposta_em`)~~ **FEITO (s382), da casa ao banco.** Falta a extensão
   chegar aos testers: enquanto a 0.7.17 não for distribuída, a coluna nasce vazia.
3. **Medir a colisão real de `(aposta_em, stake, odd)`**, assim que houver dado — ver §8.4,
   que é hoje o maior risco do desenho.
4. **Fase A** (descobrir o que resolveu), que já entrega valor sozinha e **não escreve nada**.
5. ~~O aviso de truncagem da expansão~~ **deixou de ser pré-requisito** (ver §3.1): a
   lista passa a vir da API com `from`/`to`, sem depender do que carregou na tela. O conserto
   da truncagem continua valendo para a CAPTURA normal, que é outra frente.
6. **Fase B** (aplicar o resultado), com ensaio antes de gravar.
