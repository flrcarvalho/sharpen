# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`

_Atualizado: 2026-09-06 (sessao 328 - **a Pinnacle chama o PUSH de "DRAW", e o rotulo desconhecido virava pendente eterno.** O bilhete `3117191609` (Aguila 0.0 no 1o tempo contra o Alianza, 1:1 no intervalo, R$ 408) liquidou como REEMBOLSADO na casa e ficou com "?" na grade. A tela mostra "Decidido / REEMBOLSADO" e `Vitoria/derrota 0.00`, mas o rotulo CRU que a API devolve e `DRAW` - que nao estava no de-para do `formatTicketPN`. O bloco saia `Status: DRAW (a conferir - nao liquidar automaticamente)`, **a IA obedeceu a instrucao** (e ainda registrou no RAIO-X que o P/L 0,00 indicava reembolso, sem poder agir) e o backend gravou `aberta`. Nao foi a IA errando: foi a extensao mandando nao liquidar. Duas travas, e a segunda e a que importa: `DRAW`/`TIE` entraram no de-para, e **por baixo dele** ficou a rede do DINHEIRO - resolvido + rotulo desconhecido + P/L exatamente 0 => retorno = stake => V, pelas cinco formulas de `_veredito_do_retorno` lidas ao contrario. Fecha a familia inteira: o proximo nome que a casa inventar para push ja nasce coberto. Com P/L != 0 o rotulo desconhecido continua indo para a IA como "a conferir" - inferir W/L de um nome que ninguem conhece e chute. Provado por mutacao: tirar `DRAW` PEGOU, tirar a rede PEGOU, e as duas juntas reproduzem o bug palavra por palavra. Uma 3a mutacao ESCAPOU e esta anotada no caso como inocua - o `!t.aberta` dentro do `plZero` e defesa dupla, quem decide a aberta e o `if (t.aberta)` de cima. SharpenUp 0.7.7; a linha presa fecha sozinha na proxima captura, sem script no banco.)

_Anterior: 2026-09-06 (sessão 324 — **botão que não leva a lugar nenhum confunde mais que botão ausente.** O `Entrar com Telegram` saiu do `/login`: o fluxo não conclui e o relato de uso era gente apertando sem retorno. Só o BOTÃO saiu — backend, rotas e os 27 testes do login social seguem inteiros, e o teste que trava a remoção diz como desfazê-la. `temSocial` deixou de olhar `m.telegram` para o separador **ou** não acender sozinho. 2 mutações aplicadas e 2 detectadas; 717 passed. Causa raiz do clique morto segue ABERTA (suspeito: `/setdomain` do BotFather) — não medida, o pedido era tirar o botão. Antes, s323 — **filtrar um dia zerava o Custo de Contas com o parque inteiro em uso.** A régua velha lançava o custo de aquisição num ÚNICO dia — o da primeira aposta LIQUIDADA — e só o cobrava quando o intervalo das LINHAS filtradas continha aquele dia; recorte sem aposta zerava, e conta comprada e ainda não usada não existia no mapa (entrava nos R$ 3.100 da aba Custos e nunca no KPI). Agora o custo tem JANELA DE VIDA: `ini = menor(adquirida_em, 1ª aposta)`, `fim = maior(última aposta, arquivada_em)`, e todo período que CRUZA a janela cobra o custo cheio. Colunas novas `parceiros.adquirida_em` / `arquivada_em`, editável no modal. O escopo saiu das linhas e foi para o filtro: Casa e Operador recortam o custo, Esporte e Tipster não. ⚠️ A régua NÃO é aditiva e o preço foi aceito na mesa: o P/L Líquido de um dia carrega o custo cheio das contas vivas. 9 mutações aplicadas e 9 detectadas; 716 passed. Método: o vídeo do tester tinha ÁUDIO e a tela sozinha apontava para o alvo errado. Antes, s322 — mexer no multiselect invalida o recorte cacheado: o `_filterCache` só era zerado pelo `renderPage`, e a barra própria da Base Completa não passava por ele.)_

_Anterior: 2026-09-05 (sessão 321 — **gate que confere UM campo deixa os vizinhos livres: a odd só era reconferida como efeito colateral da stake, e o RETORNO do bloco foi gravado como ODD.** O Feca abriu com o caixa da `denisesampa01` não batendo e dois bilhetes absurdos: um `HL` num Player Props de F1 (meia derrota exige linha asiática partida) e um `Under 4.0 Gols [Loiske v TP-T]` com **odd 195,53**. Medido antes de tocar em código: `195,53 ÷ 99,00 = 1,9751`, a MESMA aposta noutra conta tinha odd `1,975`, e o bloco cru diz `Status: Ganho → W (retorno R$ 195,53)` com `Odd: 1,975` **duas linhas abaixo**. A IA copiou o retorno para a coluna Odd; P/L de **+R$ 19.258,47** onde o real era +R$ 96,53. **A raiz é de desenho:** desde a s311 a stake vem do bloco, mas a odd só era recalculada DENTRO do `if` que roda quando a stake diverge (`_odd_da_stake`) — stake certa + odd errada passava reto — e o `resultado` não tinha conferência nenhuma. **A prova é o RETORNO**, contra as cinco fórmulas do `calcular_pl` lidas ao contrário (`repository._veredito_do_retorno`), agora rodando SEMPRE que o bloco prova o retorno. **O rótulo do Status não serve de fonte:** `_resultadoB3` escreve `Ganho → W` para qualquer retorno maior que a stake, meia vitória inclusive — ler o texto reescreveria como W 14 bilhetes `HW` que estavam certos. **Varredura da sombra (5.316 blocos, 20 casas): 33 linhas com dinheiro errado, Δ −R$ 19.711,29** (Feca −19.796,51 · Gabriel +69,39 · Jonathan +15,83), corrigidas por `scripts/corrigir_resultado_odd_s321.py` (ensaio por padrão, snapshot que APENSA em `Backups/s321-odd-resultado-contra-bloco/`). O P/L da `denisesampa01` caiu de R$ 28.001,63 para **R$ 8.321,45** — ⚠️ a Caixa precisa ser RECONFERIDA, a conferência registrada não se recalcula sozinha. **Três armadilhas medidas, todas load-bearing:** (1) a Betfair mistura BR e EN no mesmo bloco (stake `300,00`, retorno `1,642.38`) e um parser BR lê 1,64 e destrói 5 odds certas → `_num_bloco` decide pelo ÚLTIMO separador, e **um separador só é sempre decimal** (a regra `3 dígitos = milhar` faz `1,775` virar 1775); (2) **correção humana manda** — 3 bilhetes Betano em que alguém inverteu `W→L` e `L→W` no mesmo minuto são PULADOS pelo script (o gate em extração NÃO tem essa trava, e `resultado` nunca foi congelado pelo UPSERT: recaptura desfaz a edição); (3) só se escreve onde o **dinheiro** muda — piso de R$ 1,00, senão a 'correção' troca `1,925` pela dízima `1,925087108`. **GATES:** `tests/test_odd_resultado_determinista.py` (17 testes, **5 mutações aplicadas e todas pegas** — 2 escaparam na 1ª rodada e o defeito era do teste, registrado no cabeçalho junto com a mutação INÓCUA do lookbehind `(?<!potencial )`), suíte inteira verde (**699**), e **replay do gate na sombra real**: reproduz sozinho as 33 correções do script e mexe em **3** dos 5.316 blocos — exatamente as 3 de edição humana, zero falso positivo. **Bug meu, achado pelo replay e registrado:** o script pulava em silêncio odd truncada com reticências (`1,45070184...`), porque só o `_num_or_none` do repo faz `.rstrip('.')` — 1 bilhete ficou de fora da 1ª aplicação e entrou na 2ª.)_

> **Histórico completo das sessões 324 → 14** → [`docs/HISTORICO.md`](docs/HISTORICO.md)

---

## Onde parei (fim da sessão 328)

### A Pinnacle chama o push de `DRAW` — e o rótulo desconhecido virava pendente eterno

O relato foi de uma linha só: *"Pinnacle não atualizou o resultado do void na última
extração"*. O bilhete `3117191609` — Aguila `0.0` no 1º tempo contra o Alianza, `1:1` no
intervalo, R$ 408 — estava **liquidado na casa** (`Decidido / REEMBOLSADO`,
`Vitória/derrota 0.00`) e com `?` na grade do Sharpen.

**O rótulo que a tela mostra não é o que a API devolve.** A tela diz `REEMBOLSADO`; o campo
cru do resultado (93 e 6) traz **`DRAW`**, que não estava no de-para do `formatTicketPN`. O
bloco entregue à IA saía:

```
Status: DRAW (a conferir — não liquidar automaticamente) · P/L 0,00
```

**A IA não errou — ela obedeceu.** Ainda registrou no RAIO-X que o `DRAW` ali não era empate
de jogo e que o P/L 0,00 confirmava reembolso; só não tinha autorização para liquidar. O
backend gravou `aberta` e a linha ficou pendente para sempre. Vale como sintoma: quando a
nota da IA explica o caso certo e mesmo assim nada acontece, a instrução veio de quem
formatou o bloco, não do modelo.

`DRAW` é o **push**: handicap ou total que bate exato na linha (`0.0`, `2.0`) devolve a
stake. Não é o empate do jogo — numa Moneyline de 3 vias o empate dá `LOST`. O campo nomeia
o desfecho da **aposta**, não o do jogo.

### A trava que vale é a de baixo: o dinheiro decide, não o rótulo

Duas foram para o código, e a segunda é a que fecha a família:

1. `DRAW`/`TIE` entraram no de-para junto de `PUSHED`/`VOID`/`REFUNDED`/`CANCELLED`.
2. **Rede por baixo dele:** resolvido + rótulo desconhecido + P/L **exatamente 0** ⇒
   retorno = stake ⇒ `V`, que é a 2ª das cinco fórmulas de `_veredito_do_retorno` lidas ao
   contrário. O próximo nome que a casa inventar para push já nasce coberto.

Com **P/L ≠ 0** o rótulo desconhecido continua subindo como "a conferir": inferir `W`/`L`
de um nome que ninguém conhece é chute, e a rede não pode alcançar a **aberta** (o payload
traz P/L 0 nela também — mesmo número, significado oposto).

### As mutações, incluindo a que escapou

| Mutação | Resultado |
|---|---|
| tirar `DRAW` do de-para | **PEGOU** |
| tirar a rede do P/L | **PEGOU** |
| as duas juntas | **PEGOU** — e reproduz o bug palavra por palavra: `DRAW (a conferir — não liquidar automaticamente) · P/L 0,00` |
| tirar o `!t.aberta` de dentro do `plZero` | **ESCAPOU** |

A que escapou está anotada no caso como **inócua**, não como buraco: quem decide a aberta é
o `if (t.aberta)` de cima, então o `!t.aberta` dentro do `plZero` é defesa dupla. O teste
trava o *comportamento* (aberta com P/L 0 não liquida), não aquela linha.

Anotado também que as duas travas **se cobrem de propósito** — tirar `DRAW` sozinho ainda
daria `V`, pela rede; o que a mutação pegou foi o texto do status mudar. É defesa em
profundidade, não independência.

### O que ficou

- `extensor/content.js` (`formatTicketPN`), `casas/CASA_PINNACLE.md §5.1` (o de-para do
  rótulo **cru**, que a tabela antiga não tinha), fixture + caso no harness.
- Fixture `9000000003` é **derivada** do `3099205574` — só o resultado mudou; nenhum campo
  inventado. O JSON cru do `3117191609` não foi capturado, e o cabeçalho do caso pede a
  troca quando aparecer.
- Harness verde (23 casos, 399 bilhetes) · `audit_sharpenup` e `audit_casas` sem FAIL.
- **SharpenUp 0.7.7.** A linha presa **fecha sozinha na próxima captura** — ela está
  `aberta`, e o UPSERT atualiza resultado em linha aberta. Nenhum script no banco.

### Anotado, não resolvido (não é desta sessão)

O mesmo bilhete entrou na grade como **ML**, não como Handicap Asiático `0.0`. A causa é
outra e é de descrição: `_linhaPN` devolve `""` quando a linha é `0`, então o `0.0` some do
bloco e a IA classifica pelo que sobrou. Some a informação que **distingue** DNB de
Moneyline — e é justamente a linha que explica o push. Não mexi: é mudança de descrição,
com o congelamento do UPSERT no caminho (linha já resolvida não reescreve `aposta`/
`descricao`), e merece sessão própria.

---

## Sessão 327 — a Caixa ligada no meio da captura

### `abertas_corte` mede o que o Sharpen SABE, não o que a casa TEM

O relato veio em três sintomas que pareciam três problemas: "a Betnacional não exporta",
"uma aposta de ontem não resolve" e "preenchi a Caixa e ela não bate". Era **um só**, e
nenhum deles estava na casa — os 11 bilhetes do período estão lá, completos, com odd e
retorno corretos (conferidos card a card no Chrome; a casa diz **"Sem apostas
pendentes"**).

**Defeito 1 — a Caixa foi ligada no meio da captura.** Cronologia medida no banco:

```
03:17:32  Caixa ligada     → abertas_corte = []   (o banco ainda não tinha aberta)
03:17:59  IA termina       (uso_tokens id 2163)
03:18:19  /salvar grava    → 3 apostas nascem ABERTAS: R$ 600,00
03:18:35  Conferência      → projetado −599,00 · saldo real 2.379,87
                           → Ajuste +2.978,87  (R$ 600,00 a mais do que devia)
```

`_caixa_abertas_ids` diz que com `corte = hoje` "toda aposta aberta entra: se ela está
aberta agora, o stake saiu antes de agora, é exato". **É exato só se o Sharpen já souber
da aposta.** O dinheiro sai da conta na casa, não no nosso banco — e entre a captura
começar e o `/salvar` gravar existe uma janela de ~1 minuto em que a Caixa enxerga zero
abertas e grava esse zero para sempre. Pior: o Ajuste da conferência, que existe para
fechar a conta, **cimenta o erro** com cara de número conferido.

**Defeito 2 — a linha órfã sem código.** A captura de 05/09 devolveu a múltipla do
Falkirk sem a 11ª coluna. Sem código a dedup cai na assinatura por conteúdo, e a
"Migração B" do UPSERT (que adota linha sem código) exige `odd` **idêntica**: `14` não é
`14,00`. Quando o bilhete liquidou em 06/09, entrou linha **nova** (246454) e a velha
(243667) ficou `aberta` para sempre — o `AGUARDANDO RESULTADO 1` da grade.

**A prova, contra a casa:**

```
Saldo no corte (05/09)                              2.379,87
+ retorno das 3 abertas no corte                    1.662,26
    243665  R$300 @2,834    L  →        0,00
    243666  R$150 @11,08173 W  →    1.662,26   ← card da casa: "Retorno R$ 1.662,26"
    243667  R$150 @14       L  →        0,00
+ líquido das 8 apostadas depois do corte             515,96
                                                 ──────────
= saldo esperado hoje                               4.558,09   ← bate com a casa
```

A Caixa projetava 3.195,83. A diferença de **1.362,26** é exatamente **+1.662,26** (o
retorno que ela não conta — a `data` 04/09 é anterior ao corte, então ela lê a linha como
"já embutida no saldo informado"; só o **stake** estava, o **retorno** não) **−300,00** (o
Falkirk descontado duas vezes: R$ 150 como fantasma em aberto e R$ 150 como L liquidado).

**Correção aplicada** (`scripts/corrigir_caixa_fantasma_s327.py`, ensaio → `--aplicar`):
apaga o fantasma, grava `abertas_corte = [243665, 243666, 246454]` (o id que carrega
**hoje** cada bilhete — o do Falkirk é o 246454) e baixa o Ajuste em exatamente o
`preso_corte` que faltou, `2.978,87 → 2.378,87`. O script **aborta** se a projeção
corrigida não fechar com o saldo lido na casa. Resultado, relido da API de produção:
`preso_corte 600,00 (3) · pl 1.578,22 (11) · aberto 0,00 (0) · banca 4.558,09 ·
disponível 4.558,09` — divergência **0,00** depois da nova conferência.

O lançamento `conferencia` de 05/09 **não** foi tocado: ele é a medição daquele momento e
não se recalcula. O que ele registrou aconteceu de verdade.

> **Sintoma para reconhecer isto noutro lugar:** um retrato tirado de uma fonte que ainda
> está sendo preenchida. Vale para todo campo que congela estado no instante do clique —
> se a escrita que o alimenta é assíncrona, o clique pode chegar antes dela.

### Os dois defeitos de produto, corrigidos

**1. A órfã não era adotada porque `"14"` não era `"14,00"`.** A Migração B do UPSERT
adota a linha sem código quando o mesmo bilhete volta COM código — e comparava a odd como
**string crua**. `_assinatura` já normaliza a odd (`_norm_odd`) para decidir se duas
linhas são o mesmo bilhete; a Migração B contradizia a própria régua do sistema. Agora as
duas usam `chave_orfa()`, onde o porquê e o caso medido estão escritos. `descricao` fica
de fora **de propósito** — a Migração B nasceu para casar import por imagem com captura da
casa, e é justamente a descrição que diverge entre as duas; há teste para essa ausência
ser decisão registrada, não esquecimento.

De quebra, o índice de órfãs virou **uma consulta por conta** em vez de um
UPDATE-com-subconsulta por linha do lote, e cada órfã só é adotada **uma vez** (`pop`):
sem isso dois bilhetes iguais reivindicariam a mesma linha antiga — e a Migração B, quando
erra, não duplica: ela **sequestra**.

**2. A Caixa ligada no meio da captura gravava `abertas_corte` vazio.** Ao INSERIR uma
aposta que **nasce** aberta e cuja captura (`criado_em`) antecede a ativação, o id agora
entra no `abertas_corte`. Não é heurística: a aposta não pode ter liquidado e
desliquidado, então o stake já tinha saído quando o saldo foi lido. Três travas — só linha
recém-**inserida**; a decisão é do próprio `_caixa_abertas_ids` com `ate` = instante da
ativação (um segundo critério divergiria do original em silêncio); e a lista **só cresce**,
porque tirar um id descontaria o stake duas vezes. `criado_em` nulo ou sem fuso fica de
fora: sem ele não há prova, e comparar um naive estouraria **dentro** do `/salvar`,
derrubando a gravação inteira por causa de uma linha de caixa.

**3. A raiz: a repescagem acrescentava a linha e deixava a órfã.** `conferir_cobertura`
cobra **quantidade por código** — ela não sabe que o bilhete "faltante" pode estar ali
como uma linha que perdeu a 11ª coluna. E a repescagem só ACRESCENTA
(`_extract_tsv_rows(resultado) + novas`); ninguém removia a órfã. Os dois desfechos
deixavam linha sem código: repescagem OK dava **duas** linhas do mesmo bilhete no lote;
repescagem falha (o que aconteceu em 05/09) deixava a órfã — e sem código ela nunca dedupa.

`_reconciliar_orfas` faz duas coisas, ambas conservadoras:

- **Adoção** — a órfã recebe o código do bloco faltante de que ela é **fiel**
  (`checar_fidelidade`, o gate de procedência da s302: todo nome próprio e todo decimal da
  descrição existem naquele bloco). Só quando o par é único **nos dois sentidos** — a órfã
  casa com um único bloco livre, e aquele bloco casa com uma única órfã. Ambíguo não vira
  chute.
- **Descarte** — sobrando órfã depois disso, e não havendo mais bilhete do texto sem linha
  própria, ela é cópia de alguém que já tem a sua. Sai.

**NO-OP integral onde a coluna 11 vazia é legítima:** casa sem marcador (prints, texto
colado) e texto que traga **qualquer** `[Código: ]` vazio — é o que a bet365 manda quando o
detalhe não chegou, e descartar ali apagaria bilhete real.

Roda em **todos** os caminhos de saída, inclusive quando não houve repescagem: era esse o
desfecho que deixava fantasma. O sort por posição no texto-fonte passou a rodar **só quando
este passo mexeu no TSV** — reordenar de graça mudaria calado a ordem que o resto do
sistema lê como hora de envio.

**Gates, provados por mutação** (cada uma pega por exatamente o teste que devia pegá-la):
`_norm_odd` → string crua deixa **6** vermelhos, incluindo o caso medido `14`/`14,00`;
tirar `aposta` da chave, **1**; tirar o `ate`, **1**; sobrescrever `abertas_corte` em vez
de unir, **1**; tirar a guarda de `criado_em`, **2**. Nas órfãs, **1** cada: trava de
par único, guarda do marcador vazio, descarte, adoção e a **ligação** dentro do
`_garantir_cobertura`.

> A **ligação** tem gate próprio no harness de DB (`test_upsert_adota_aberta_que_chegou_
> depois_da_caixa_ligada`). O dublê testa a função, não a chamada: removendo o
> `await _caixa_adotar_abertas_tardias(...)` do `upsert_bilhetes`, o arquivo de dublê fica
> **todo verde** e a Caixa volta a nascer torta. Foi o modo de falso verde nº 1 da
> s286. O mesmo vale para as órfãs: removendo a chamada de dentro do
> `_garantir_cobertura`, os 7 testes de `_reconciliar_orfas` seguem verdes — só o
> teste da ligação pega.

Suíte: **756 passed, 30 skipped**. CI verde em `863f67c`, com os 30 do harness de
Postgres (é lá que o SQL novo do UPSERT é exercido de verdade).

**Backfill: nada a fazer.** `recalcular_abertas_corte_s314.py` em ensaio sobre todas as
caixas ligadas devolve **0 a corrigir**. As 3 contas que uma primeira query apontou
(`Gabriel/Pinnacle`, `Gabriel/1xBet`, `Feca/Bet365 marloncezar01`) são o **piso
deliberado** de corte no passado — o `_caixa_abertas_ids` as exclui de propósito.

**Pendente para a próxima sessão:**

1. **Duas órfãs antigas**, anteriores à correção: `passapica / BETesporte` (04/09,
   R$ 0,75) e `Diogo / Betfair` (12/08, R$ 400,00). São linhas abertas sem código em
   conta que usa código. A Migração B as adota quando o bilhete voltar liquidado, **se**
   data, categoria e stake baterem — não é garantido, e a do Diogo está aberta há quase
   um mês. Duas linhas; resolver à mão é mais barato que esperar.
2. **Aviso aos testers não foi enviado.** Sem bump do SharpenUp, o tester não tem ação a
   tomar. Decisão do Feca; a pergunta ficou em aberto.

---

## Sessão 326 — data ausente não é data antiga

O relato veio da tela: a Caixa da `Betfair · Duka [Eu]` projetava **R$ 5.456,42** e a
casa mostrava **R$ 5.155,42** — divergência de R$ 301,00, exatamente o stake da única
aposta em aberto (`O/25146258/0001998`, Botafogo × Palmeiras). A conta do painel batia
consigo mesma; o que faltava era a linha **"Em aberto"**, que dizia `0 apostas`
enquanto a grade logo abaixo dizia `AGUARDANDO RESULTADO 1`.

- **A causa é a data VAZIA, e ela é vazia de propósito.** Onde a coluna `Data` é a data
  de **resolução** (Betfair, `extensor/content.js`), a aposta aberta sobe sem data — a
  resolução ainda não existe. O `_caixa_projetar` decidia a janela por
  `data_iso >= corte`; com `data_iso = None` a condição caía e a linha era lida como
  **anterior ao corte**.
- **Sumir de uma ponta é erro; sumir das DUAS é o erro silencioso.** Fora da janela e
  fora do `abertas_corte` (nasceu depois da ativação), o stake não entrava na banca
  **nem** em "em aberto". Nada acusava: os totais continuavam coerentes, só altos em
  exatamente um stake — e a auditoria acusava uma divergência que era **dela**.
- **Correção:** sem data, a data efetiva é `criado_em` — o único sinal restante de
  quando o stake saiu da conta. Onde há data, nada muda. Extraí `_caixa_criado_iso`
  para `_caixa_projetar` e `_caixa_abertas_ids` não discordarem sobre como ler o campo.
- **A query do Painel de Contas não trazia `criado_em`.** `caixa_conta` e `caixa_visao`
  chamam o mesmo núcleo mas montam queries próprias: sem o campo, o Painel projetaria
  **diferente** da tela da conta, com a mesma conta e sem erro nenhum.

**Alcance medido em produção:** 193 bilhetes sem data no sistema inteiro (187 Lottu,
5 Betfair, 1 Bet365), e **1 só** em conta com caixa ligada — a do relato. Nenhuma conta
Lottu tem caixa hoje; ligar uma cairia no mesmo buraco.

**Prova contra o dado real** (leitura pura, nada escrito): `preso_corte 421,00 ·
pl 1.250,58 (18 liquidadas) · aberto 301,00 (1) · banca 5.456,42 · **disponível
5.155,42**` — igual ao Principal da Betfair. A conta segue em `reconferir` porque o
ajuste de 05/09 endereçou a divergência antiga; a próxima conferência fecha.

**Gates, provados por mutação:** removendo o fallback, 3 testes ficam vermelhos
(incluindo `test_caso_medido_betfair_duka`, que reproduz os números da tela);
removendo `criado_em` da query do Painel, o gate de forma das duas queries fica
vermelho. O simétrico também está travado — aberta que o Sharpen **já conhecia** antes
do corte e ficou fora do `abertas_corte` continua fora, senão o stake seria descontado
duas vezes. Suíte: **724 passed, 26 skipped**.

---

## Sessão 325 — 8º tipster público: `Grego Tips - VIP`

> **Parte 2 (07/09): o tenant do bot entrou em produção.** O que está escrito
> abaixo é o import; o resto da sessão está resumido aqui e mora no
> `sharpen-bot` (commits `5cd8c6b`, `eb1bca4`, `d283ed8`, `36b29ce`).

### O 8º tenant do bot, no ar

`src/perfis/grego.js` forkado do `sohprops`, bloco `GV_*`, linha no registro
`PERFIS` (a que faltando derruba TODOS em crash-loop, s316). Boot com **7
tenants**, suíte verde, **12 mutações aplicadas e 10 pegas** — as 2 inócuas
estão escritas no teste.

Cinco diferenças do irmão, todas medidas no export do canal: a stake é `%` e
**não abre a linha** (1.043 de 1.305 no meio/fim — ancorar em `^` perderia 80%
das apostas), o que obrigou a reconhecer a linha por CONTER stake e a criar
guardas, porque o `%` tem outros três papéis (`2.02 + 25% = 2,27@`, `só vale com
25% odd final`, `ROI: 15.28%`); `⌛` = aberta; casa por **apelido** (`mgm`,
`365`, `Super`, `Betan` devolvem null no `casas.js`); **34% das legendas cegas**;
e `Quadra`.

### O bloqueio não era código: era o bot ser MEMBRO do grupo

`getMe` diz `can_read_all_group_messages: false` — privacy mode ligado. Bot com
privacy, como membro comum, **recebe só comandos**: as mensagens com print não
chegam, e o tenant nasceria **surdo, sem erro nenhum**. Medido, não deduzido: os
6 apoios que funcionam têm o bot como `administrator`; o do Grego era o único
fora do padrão. Promovido, o log provou a virada
(`[apoio:grego] msg — foto=false texto=false`).

### A coluna `Tipster` passou a sair por AUTOR

O canal tem DOIS admins, e o **Sign messages** está ligado: cada post carrega
quem escreveu (`grego` 958 · `ricklxrd` 110). Isso tornou a atribuição do atraso
**determinística** — 148 `Grego` e 48 `Rick`, sem heurística.

Daqui pra frente quem resolve é o núcleo, por `msg.from.id` → `XX_TIPSTER_NOMES`
(genérico; vazio = comportamento de sempre; **inerte em canal**, onde não existe
`msg.from`). Autor fora do mapa cai na marca **com aviso dizendo o id**. Os dois
ids foram provados contra o grupo por `getChatMember`, e o `first_name` de cada
um é **exatamente a assinatura do canal** — a mesma pessoa chega pelo mesmo nome
pelos dois caminhos, e por isso as duas metades da coluna se somam.

**As 956 do tracker ficam sob a marca**, e é decisão com número atrás: o join
por (título, stake, data) fecha em **704 de 956 (73,6%), zero ambíguas**. Um
quarto sem autor faria um ROI "por admin" **parecer completo sem ser**.

### Dois defeitos que apareceram no uso

- **`/anular` dizia "3 apostas removidas" tendo removido 0.** O aviso repetia
  `ids.length` — o que foi MANDADO — e ignorava `resp.deletados`. Mesma família
  do `rejeitados` do `/salvar`: contagem devolvida pela API é dado, não enfeite.
  Hoje acusa (`removeu 0 de 3`), e resposta sem número vira `?`, nunca `0`.
- **Modo de teste desvia o POST, não o planilhamento.** Os dois bilhetes de
  teste entraram na base de verdade. Só não sobrescreveram o histórico porque o
  bot põe sufixo `-S<n>` quando há N apostas: `GV202609-1-S1` ≠ `GV202609-1`.
  **Teste de UMA aposta só, na mesma casa, teria batido a assinatura** — é a
  colisão que o `/contador` existe para evitar, e ela quase aconteceu.

### O post, como o tipster pediu

`🧠 <Nome>` na última linha, depois do total — o cabeçalho só diz a marca, igual
para os dois. É o **mesmo valor** que vai para a coluna `Tipster`: o núcleo
resolve uma vez e entrega nos dois caminhos, então canal e planilha não podem
divergir sobre de quem é a aposta. Autor desconhecido não imprime linha nenhuma
— repetir a marca ali seria fingir resposta.

E o **P/L saiu de `u` para `%`**, a régua que eles usam. Derivado do `plFmt`
compartilhado, não copiado: o sinal continua sendo **U+2212**, e a mutação que
copia o formatador perde exatamente isso.

### Estado final

    base gregozxrd   1.152 · Grego Tips - VIP 956 · Grego 148 · Rick 48
    série            GV202609-228 · contador 228 → próximo #229
    bot              publicando no canal (GV_MODO_TESTE=0), 2 autores mapeados

### 8º tipster público — `Grego Tips - VIP`

Conta `gregozxrd` (alyssongrego587@gmail.com) aprovada no `/admin` e **956 apostas
importadas** (`scripts/import_grego_csv.py`), 01/08 → 01/09/2026, stake em
unidades, 12 contas `Padrão` — uma por casa.

| | |
|---|---|
| Slug / marca | `/tipsters/gregotipsvip` · `Grego Tips - VIP` (o username diverge pela 5ª vez) |
| Códigos | `GV202608-1` … `GV202609-32` |
| Carteira | prop de jogador de futebol: Chutes 472 · Anytime 229 · Múltipla 120 · Desarmes 30 · Faltas 29 · Assistência 25 |
| Resultado | L 675 · W 267 · **V 14** (`Reembolsada` → void, `Ganho` e `Lucro` zerados) |
| Total | 1.008,48u de turnover · **+132,79u** · ROI **+13,17%** |

### O gate mais forte não veio da planilha — veio do canal

Ele publicou o fechamento de agosto no grupo em 01/09: **924 apostas, P/L
+127,84u, ROI 13,02%**. O import, lendo só o CSV, deriva **924 apostas, +127,73u,
13,00%**. A diferença de 0,11u é o arredondamento a centavo da coluna `Ganho`,
acumulado em 267 vitórias — o derivado usa a odd inteira.

Isso é diferente da reconciliação interna (que também fecha: **0 divergências em
956** entre P/L derivado e a coluna `Lucro`). O número do canal saiu da boca do
dono **antes de existir import**: ele não pode estar errado pelo mesmo motivo que
a planilha estaria.

### As 6 linhas sem casa foram MEDIDAS, não decididas

O Rogerin resolveu isso com uma decisão do Feca (126 linhas → Betano). Aqui a
resposta estava no export do Telegram, nas mensagens do próprio dia:

    Nesta Elphege chutes 3+/4+/5+   01/09  → Bet365   (msg 938)
    Forson +2 Chutes / +3 Chutes    01/09  → Bet365   (msg 940)
    Summerville Ast                 01/09  → Betano   (msg 942)

O mapa é fechado e casado por (data, título): linha sem casa fora dele **aborta o
script**. Casa chutada não dá erro — dá conta paralela.

### Três leituras de categoria que não eram óbvias

- **`<Nome> +2 Gols` é `Anytime`, não `Gols`.** O `MASTER_APOSTAS §3` põe
  "marcar 2 ou mais gols (marcador 2+)" na família Anytime, e o limiar vai na
  descrição. As odds confirmam (11,0 a 81,0 — total de jogo não paga isso), e o
  canal mostra a escada: `Tresoldi Anytime 1.50%` + `Tresoldi +2 Gols 0.50%`,
  mesmo jogador. `Gols` ficou com o que é do JOGO: gol em ambos os tempos,
  próximo gol, linha decimal.
- **`25%` / `50%` no título é odd TURBINADA, não mercado** (24 linhas). Ele
  escreve a conta no canal: `2.02 + 25% = 2,27@`. Mesma família do `aumentada`
  do Rogerin e do `SuperMúltipla` da Estrela Bet.
- **` e ` separa PERNAS** em 12 títulos que combinam sem dizer "dupla"
  (`Priske e Tolaj` @24,96). Com 3 pernas declaradas o esporte vira `Múltiplos`.

### O `%` tem DOIS papéis na mesma fonte — e o segundo é a stake vazando

`Cuevas Christian Chutes +2 0.50%` não é bet builder: o `0.50%` é a **stake**
(u=0,50) escrita dentro do título. Lido como turbinada, ele transformava duas
apostas de `Chutes` em `Múltipla`. O mesmo vale para `- 1.50` no fim de
`Forson +2 Chutes - 1.50`, que viraria **handicap** (nesta fonte é o SINAL que
declara handicap).

A limpeza só corta o sufixo **quando o número é exatamente a stake da linha**, e
é essa condição que mantém `cruzeiro -1` (stake 2,50, handicap de verdade)
intocado. A categoria lê o texto já limpo — senão o mesmo caractere decide duas
coisas contraditórias.

### Prefixo `GV`, conferido contra a coluna INTEIRA

`GR` (233), `GT` (35), `GG` (8), `GX` (35) e `GP` (34) estão todos ocupados por
**código NATIVO da bet365** (`GR3383912251I`) — duas letras mais dígitos, que um
regex ancorado em `XX<aaaamm>-<n>` **não enxerga** (regra da s316). `GV` é o
único par com G livre: 0 linhas.

⚠️ **Ele vai usar o bot** (canal `-1003928624343`, apoio `-5577016989`). No dia em
que o bot entrar, suba o contador (`/contador N`) para além de **`GV202609-32`**
antes da primeira aposta — planilha e bot escrevem na MESMA série.

### Anotado, não resolvido

- **18 linhas `Nome N+` sem mercado** (`Julio Enciso 3+`, `Sebastian 2+`): nem o
  canal diz qual é. Vão para `Player Props` — a gaveta do §3 —, nunca para o
  total do esporte, que inventaria um objeto que ninguém escreveu.
- **`Betsson` é casa nova no banco** e entrou nos 4 mapas de favicon
  (`data.js` tem `CASA_ICONS` **e** `HOUSE_DOMAIN`), com o domínio **medido** no
  link do canal (`betsson.bet.br`), não deduzido do nome.

### `SOA` era `score or assist` — a inferência razoável estava errada

Perguntado, respondido no mesmo dia: **`SOA` = "marcar OU assistir"**, não chute
no gol. As 5 linhas foram para `Player Props`, junto com o `G/A` do mesmo arquivo
— é o mesmo mercado escrito de dois jeitos, o §3 não tem categoria para ele, e
escolher `Anytime` ou `Assistência` sozinhas jogaria metade do mercado fora.
Base reimportada (o script é idempotente por `origem='import'`): 956 linhas, a
reconciliação segue em **0 divergências**.

A inferência era razoável e ainda assim falhou: `SOA` e `SOT` aparecem na MESMA
escada e os dois pareados com `Anytime` (`Kvam SOA 2.00%` + `Kvam Anytime
1.00%`), o que fazia um parecer variação do outro. **Vizinhança tipográfica não é
significado.** Sigla que não aparece por extenso em lugar nenhum da fonte só se
resolve perguntando ao dono — e o que fez a pergunta acontecer foi ela estar
marcada como inferência declarada no relatório, em vez de passar como fato.

### O atraso do canal: 196 apostas que nunca chegaram ao tracker

Ele parou de planilhar na msg **969** (01/09 22:04) — a fronteira veio do Feca e
confere: nenhum bilhete de lá em diante aparece no CSV, que termina no lote de
01/09 23:28–23:35. Do 969 até a última mensagem do export (1110, 06/09 15:51) são
**79 mensagens de aposta e 196 linhas**, agora em `GV202609-33 … GV202609-228`
(`scripts/import_grego_canal_s325.py`). Base do dono: **1.152 bilhetes**, 83 em
aberto — o que não tinha marca entra sem resultado e ele completa à mão.

**A fonte aqui não é planilha nenhuma: são os 79 PRINTS.** A legenda dá stake e
marca; o print dá odd, seleção e confronto. E o print carrega mais do que a
legenda: **67 das 196 linhas (34%) têm legenda CEGA** (`1.50%`, sem nome) — sem a
imagem elas não existiriam.

### O pareamento stake ↔ seleção tem três conferências, e todas foram usadas

É onde esse tipo de trabalho erra em silêncio: legenda fora de ordem põe o valor
certo na aposta errada **sem o total mudar**.

1. **A caixa de valor do print traz o R$ igual ao `%` da legenda.** Na msg 990 o
   print mostra R$ 2,00 / 0,50 / 0,50 / 0,25 e a legenda diz `2.00% / 0.50% /
   0.50% / 0.25%`. Pareamento vira conferência, não suposição.
2. **A escada de odd** — limiar maior, odd maior, stake menor.
3. **O nome, quando a legenda o traz, MANDA sobre a posição.** Na msg 986 a
   legenda está fora de ordem (`+2`, `+4`, `+3`) e o print em ordem: quem pareia
   por posição erra duas das três.

Para a combinada, o produto das pernas confere a odd do cupom — msg 1085 dá
`1.95 × 1.98 × 2.50 = 9.65` exato. No `Criar Aposta` da Betano o produto fica
ACIMA do pago (a casa corta a combinação do mesmo jogo): ali vale o print.

### O gate que não depende de eu ter lido certo

As marcas foram contadas por regex sobre as 79 mensagens, **sem olhar print
nenhum**: `❌ 73 · ✔️ 40 · ⌛ 15 · sem marca 68`. A leitura dos prints produziu
**73 L, 40 W e 83 abertas (15 + 68)** — fecha nos três.

Provado por mutação, **4 de 5**: trocar `W` por `L`, trocar `L` por aberta,
remover uma linha e duplicar uma linha quebram o gate. **A 5ª escapou e está
escrita no código:** trocar a *stake* de uma linha passa reto. O gate conta
MARCAS e LINHAS, não confere valor — a conferência de stake é a do item 1 acima,
feita a olho, e não é automatizável sem reler as 79 imagens.

### Três coisas que só o print contou

- **Bet builder disfarçado de simples.** A legenda diz `Tyreece chutes 2+`; o
  print mostra `Criar Aposta @1.70 = 2+ Chutes + Over 0.5 Gols`. São 26 múltiplas
  no lote, e várias chegam assim — nomeadas pela perna que interessa a ele.
- **Cupom que a legenda NÃO menciona não entra.** Nas msgs 1046 e 1055 o print
  mostra o construtor montado, mas a legenda declara duas SIMPLES com odd própria
  (`1.25% @2,42❌ | 1.25% @1.95✔️`). São duas apostas, não um cupom.
- **A odd do print vence a da legenda quando o dinheiro depende dela.** Msg 1062:
  legenda `@3.5`, print `3.60` — e o print se prova sozinho (`R$4,50 ÷ R$1,25`).
  É `W`, então a odd entra no P/L. Já na msg 1057 (legenda `@1.39` × print
  `2.22`) o bilhete é `L` e a odd não muda nada: fica a da legenda, com a
  divergência anotada.

**Descrição no formato do MASTER** (decisão do Feca): `Entidade - Mercado
[Confronto]`, com `v` no confronto e a conversão `Mais de 2.5 → Over 2.5`. **A
forma da linha segue a CASA** (§10.1 × §10.2): Betano/MGM vendem discreto
(`3+ Chutes`), bet365/Superbet vendem contínuo (`Over 2.5 Chutes`) — reescrever
uma na outra seria inventar apresentação.

⚠️ **`origem='extracao'`, e a idempotência é por FAIXA DE CÓDIGO.** Com
`origem='import'` um reimport do tracker levaria estas 196 junto, em silêncio (o
importador apaga por origem antes de reescrever). O `DELETE ... WHERE
codigo_bilhete = ANY(...)` não depende de origem e não encosta no que o bot vier
a escrever.

### Os dois ids do Telegram, conferidos por `getChat`

    canal oficial  -1003928624343  channel  'Grego Tips - VIP'  bot = administrator ✔
    apoio          -5577016989     group    'sharpenbot'        bot = MEMBER

O apoio **não migrou para supergrupo** (o id `-5…` responde, sem
`migrate_to_chat_id`), então o tenant não nasce surdo — a armadilha da s316 não
se aplica aqui.

**Renomear o apoio para `Apoio - Grego` FALHOU** e não foi insistido:
`setChatTitle` → `Bad Request: not enough rights to change chat title`. O bot é
membro comum ali. Ou ele é promovido a admin com "alterar informações do grupo",
ou o Feca renomeia na mão.

### Pendência que não é desta sessão

**O perfil do bot (8º tenant) NÃO foi feito** — o escopo desta sessão era só o
import. O recon do canal já está medido: 1.074 mensagens, 31/07 → 06/09, 621 com
print, formato irmão do Soh Props (1 linha por aposta, stake em `%`, marca
`✅`/`✔️`/`❌`/`⌛` na própria linha, casa pelo NOME no rodapé, `⏰` com a hora do
evento). Falta medir se ele EDITA a mensagem para marcar depois — é o que decide
`legendaOpcional`/`recompoePorLegenda`.

---

## 1. O que estamos construindo

A base de conhecimento (masters) do scanner de bets. Camada **global** (regra única, muda devagar) + camada **por casa** (traduz cada casa para a língua global). A saída final é **TSV**.

---

## 2. Invariantes (não se quebram)

1. O app **lê** os masters, **nunca escreve** neles. Mudança de regra = diff revisado por humano + commit. Git é a porta de aprovação.
2. O arquivo de casa **traduz** a casa para a língua global; **não redefine** regra global.
3. **Cálculo é global, localização é da casa.** Ex.: "W → Retorno÷Stake" é global; "o retorno está no campo PRÊMIO" é da Superbet.
4. Nenhuma regra nova é aplicada sozinha. Propor como diff, esperar aprovação.

---

## 3. Estrutura-alvo do repo

```
/global/                 (autoridade única — 6 masters)
    MASTER_PIPELINE_2026.md
    MASTER_ESPORTES_2026.md
    MASTER_APOSTAS_2026.md
    MASTER_DESCRICAO_2026.md
    MASTER_RESULTADO_2026.md
    MASTER_OUTPUT_2026.md
/casas/                  (1 arquivo por casa — traduz, nunca redefine)
    CASA_MODELO.md         (gabarito — 15 seções)
    CASA_BET365.md
    CASA_BETANO.md
    CASA_BETESPORTE.md
    CASA_BETFAIR.md
    CASA_BETNACIONAL.md
    CASA_BOLSADEAPOSTA.md
    CASA_KINGPANDA.md
    CASA_KTO.md
    CASA_LOTTU.md
    CASA_NOVIBET.md        (plataforma própria BlueBrown — replay que ALARGA o filtro)
    CASA_PINNACLE.md
    CASA_PITACO.md         (ex-"Rei do Pitaco" — gRPC-Web/protobuf; 2 grafias, 1 manual)
    CASA_POLYMARKET.md     (por API, não IA)
    CASA_SUPERBET.md
    CASA_TIVO.md
    CASA_BETFAST.md        (espelho técnico da Tivo — mesmo motor BetConstruct)
    CASA_JONBET.md
    CASA_BETBOOM.md        (espelho técnico da Jonbet — mesmo motor BetBy/sptpub)
    CASA_VAIDEBET.md
    CASA_ESPORTIVA.md      (espelho técnico da VaideBet — mesmo motor Altenar/BIA)
    CASA_JOGODEOURO.md     (3ª casa Altenar — captura na TELA CHEIA do histórico)
    CASA_BETPIX365.md      (4ª casa Altenar — a casa NÃO chama o endpoint que ela precisa)
    CASA_ESTRELABET.md     (5ª casa Altenar — a mais lisa na tela; o gateway recusa credencial)
    CASA_STAKE.md          (mesma Kambi da KTO, mas REST próprio — captura NÃO é espelho)
    CASA_VITORIABET.md
/golden_set/
    bilhetes/              (print + TSV esperado)
/docs/                   (referências, ADRs, planos, HISTORICO.md)
STATUS.md                  (este arquivo)
```

Os 6 MASTER_*.md vivem em `/global/`; as **28** casas em `/casas/` (Polymarket por API, as demais por IA/texto), mais o gabarito `CASA_MODELO.md`.

---

## 4. Estado atual

- **Produto no ar** em `sharpen.bet` (dashboard + extração); deploy automático via Railway.
- **Multi-tenant:** vários donos (Feca, Fatuch, Diogo, Jonathan, Lava, LavaPessoal…) + operadores; dados isolados por `dono` no Postgres (regras de tenancy/dedup no `CLAUDE.md`). Identidade na tabela `usuarios` do Postgres via cache em memória (s233 — Fase 1 do `docs/PLANO_MULTIUSUARIO_2026.md`); os dicts de `app/auth.py` são a SEMENTE. Conta nova = 1 linha em `USUARIOS` (`app/auth.py`) + `SENHA_<USER>_HASH` no Railway (o seed leva ao banco no boot); base nasce vazia sem migration. Suspender no banco (`status`) revoga login E sessão em ≤60s.
- **Base do Feca:** migração planilha → Postgres **completa e reconciliada**.
- **Base do `LavaPessoal` (s222):** 2.877 apostas importadas do `.xlsx` pessoal do Lava (23/02 → 30/07/2026), `origem='import'`, conta `Padrão` em cada uma das 19 casas (ele não anota fornecedor). Script próprio e idempotente: `scripts/import_lavapessoal_xlsx.py` (re-rodar limpa só `origem='import'` daquele dono; captura da extensão sobrevive). **Não confundir com o dono `Lava`** — são bases distintas que só compartilham o apelido. **O P/L do dashboard não bate com a planilha de origem por desenho** (ela contabiliza em unidade; ver s222 no topo).
- **Base do `SoChutes` (s224):** 23.199 apostas all-time do tipster Só Chutes (17/09/2024 → 27/07/2026) importadas do `.xlsx`, `origem='import'`, conta `Padrão` (Bet365/Superbet/Betano; casa não informada entrou como Bet365 — decisão do Feca). **Stake em UNIDADES** (1u = 1; o P/L do dashboard é o P/L em unidades: +1.381,29u). Script idempotente: `scripts/import_sochutes_xlsx.py`. O planilhamento novo é do **bot Sharpen** (repo próprio `BOTS/sharpen-bot`, ver s223), que desde a **s251** roda 24/7 no Railway — serviço `sharpen-bot`, no mesmo projeto do app, com o estado em volume próprio. Ele escreve nesta base por `/salvar` + `/bilhetes/tipster`: **mudança no contrato dessas rotas quebra o bot em silêncio.**
- **Base do `Flurray` / tipster Fleury (s260):** 473 apostas (11/06 → 09/08/2026) importadas do `.xlsx`, `origem='import'`, conta `Padrão` em cada uma das 4 casas (Bet365, Betano, Superbet, BetMGM). Base de **nicho**: 100 % mercados de finalização no futebol. **Stake em UNIDADES** (1u = 1; P/L +122,30u sobre 447,80u de turnover). Script idempotente: `scripts/import_fleury_xlsx.py`. **⚠️ A marca é `Fleury` e o username é `Flurray`** — o `dono` é sempre o username; a ponte entre os dois é o `TIPSTERS_PUBLICOS`. Conta criada pelo próprio usuário no site e aprovada pelo Feca (Fase 2): **sem env var, sem linha em `app/auth.py`**. Página pública: **`/tipsters/fleury`** (3ª do sistema).
- **Base do `passapano` / tipster PassaTips VIP (s273):** 911 apostas (02/06 → 17/08/2026) importadas do `.xlsx`, `origem='import'`, conta `Padrão` em cada uma das 7 casas (Bet365, Betano, Betnacional, Betvip, Estrela Bet, Novibet, Suprema Bet). Base **multiesporte**: 20 esportes, de futebol e tênis a polo aquático e críquete. **Stake em UNIDADES** (1u = 1; P/L +90,20u sobre 1.102,61u de turnover liquidado). Script idempotente: `scripts/import_passatips_xlsx.py`. **⚠️ A marca é `PassaTips VIP` e o username é `passapano`** — mesmo caso do Fleury. Conta criada pelo próprio usuário no site e aprovada pelo Feca (Fase 2): **sem env var, sem linha em `app/auth.py`**. Página pública: **`/tipsters/passatipsvip`** (5ª do sistema). O planilhamento novo é do **bot Sharpen** (4º tenant, `passatips`) — **1º perfil sem visão**, porque a legenda dele já traz tudo.
- **Casas:** 28 arquivos em `casas/` (extração por IA/texto) + **Polymarket** por API.
- **Fatuch:** dashboard lê a planilha viva do LavaFatuch via Apps Script (leitura por **cabeçalho**, não por posição); coluna `Espelho` = fornecedor. Sem base no Postgres (tudo vem da planilha).
- **Captura:** extensão **SharpenUp** (moldura+Snap e robô de rolagem) no ar, pareando por código. **25 casas por API** (injetor no mundo MAIN, dado exato): Superbet, BETesporte, Betano, Betfair, Pinnacle, Bet365, KTO (Kambi, s192), Tivo (s196), VaideBet (Altenar, s210), **Betfast** (s211 — **espelho da Tivo**: mesmo motor BetConstruct, mesmo `tv_inject.js`), BetNacional, Jonbet (BetBy/sptpub, s248), **Betboom** (s250 — **espelho da Jonbet**: mesmo motor BetBy, mesmo `jb_inject.js`) **Pitaco** (s270 — plataforma própria, **gRPC-Web/protobuf binário**, replay puro) **Novibet** (s271 — plataforma própria BlueBrown, replay puro que **alarga o filtro** da tela: ela pede 24 h e só as fechadas) e **Estrela Bet** (s303 — **5ª casa Altenar**, mesmo `vb_inject.js`; a mais lisa na TELA e a única cujo gateway **recusa `credentials:"include"`**). **Dois pares de espelho, zero código duplicado** — o inject casa por caminho de API, nunca por host, e é isso que faz a casa seguinte da mesma plataforma custar registro em vez de implementação.
- **Apostas em aberto (s215):** o feed (`dashboard_rows`) carrega a aposta não liquidada marcada `resultado='ABERTA'`, `lucro=0`. Ela aparece no topo da **Minha Base** (ex-"Apostas") e tem tela própria em **Minhas Apostas › Em Aberto** (`charts/abertas.js`): KPIs de exposição, horizonte por faixa de dia, calendário por data do evento, barras por casa e por tipster, lista completa. **Nenhuma métrica a soma** — `aplicarFeed` separa `DADOS` (encerradas) de `DADOS_ABERTAS`, e Início/Extração cortam por `resultado==='ABERTA'`.
- **Modelo de extração:** Sonnet 4.6 (`config.py`).

---

## 5. Pendências

> **As pendências mudaram de casa.** Elas moram em **[`BACKLOG.md`](BACKLOG.md)**, na raiz —
> organizadas por natureza (bloqueado por humano · por amostra · decisão do Feca · dívida
> técnica medida · planos com fase aberta · não medido), com as marcas
> **VIVA / NÃO-MEDIDA / HUMANA** da varredura da s261 preservadas.
>
> Motivo: o §5 tinha **51 KB** e ficava atrás de 124 KB de changelog. Quatro arquivos
> disputavam o papel de "onde o projeto está" e três descreviam o projeto de julho. Ver
> [`docs/FAXINA_PROPOSTA.md`](docs/FAXINA_PROPOSTA.md).
>
> **Pendência nova vai para o `BACKLOG.md`, nunca para cá** (invariante #10 do `CLAUDE.md`).
> Gate: `python tools/check_docs.py`.

As três mais quentes de hoje, com o resto no `BACKLOG.md`:

1. **`apps_script/Code_LavaFatuch.gs` expõe a base do Fatuch sem autenticação nenhuma.**
   `doGet(e)` na linha 95, zero token ou segredo no arquivo — e é a fronteira que alimenta o
   `app/planilha_viva.py`, a base financeira **ao vivo** de um cliente. Qualquer um com a URL
   lê. Medido em 06/09. → `BACKLOG §4.3`, e é sessão própria.

2. **PassaTips: 3 passos humanos para fechar o buraco do #259, e a ORDEM importa.**
   Enquanto o painel do #259 estiver armado, um clique ✅ vira o `L` do dia 17 em `W`
   (`resultado` não é congelado). O `/anular #259` **apaga** a linha `Under 1.5 cartões
   Elche`, então o tipster tem de repostar **antes**. → `BACKLOG §1`.

3. **Polymarket ainda mistura `entry_odd` e `realized_odd`** (`AUDITORIA_2026 #32`).
   `_calc_odd` (`app/polymarket.py:894`) devolve um número só, e o próprio comentário da
   `:987` admite "odd de entrada, **ou** a efetiva na liquidação". É o maior risco quant
   aberto e mexe em P/L. → `BACKLOG §4.1`.

---

## 6. Rodar / produção

**App em produção:** `https://sharpen.bet/` (www.sharpen.bet → Railway)

Para rodar localmente:
```
cd app
pip install -r requirements.txt
# .env na raiz do Planilhador com ANTHROPIC_API_KEY e DATABASE_URL
uvicorn main:app --reload
# Abrir http://localhost:8000
```

---

## 7. Workflow

- **Backup antes de editar** — sempre em `Planilhador/Backups/<nome-descritivo>/`. Nunca usar `FDC Capital/Backups/` (é compartilhada por outros projetos da empresa).
- Arquivos completos, nunca diffs parciais.
- Uma mudança por etapa aprovada.
- Atualizar este STATUS.md ao fim de cada etapa.
- Projeto tem git + GitHub (`flrcarvalho/sharpen`, renomeado de `extrator` na sessão 129). Deploy automático via Railway conectado ao GitHub — push dispara deploy.
