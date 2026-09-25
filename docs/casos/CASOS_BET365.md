# Casos da captura SharpenUp — bet365

> Partição de [`../CASOS.md`](../CASOS.md) por assunto, aberta quando ele encostou no
> teto de 60 KB do `check_docs.py`. **Teto é sinal de partição, não de excesso: caso não
> se apaga.** Caso novo de captura da bet365 entra AQUI, não lá.

> ⚠️ Daqui de dentro, todo caminho relativo sobe um nível: `../CASOS.md`, `../../casas/`.

---

## O muro que parecia da casa e era do histórico do navegador — bet365, 2026-09-20

A extração da bet365 travava no meio e o operador "reconectava" para seguir. A explicação em
vigor vinha da s184: *"a `confirmation` dá 500 sob rajada no namespace D0"*. Dela saíram a
folga de 900 ms entre bilhetes, o teto de 9 s e os dois retries com bounce no hash.

**Nada disso era verdade, e ninguém nunca tinha medido o status das respostas.**

### O que a medição mostrou

Um gravador no `b3_inject.js` carimbou cada requisição com status HTTP e duração:

| | |
|---|---|
| `confirmation` numa sessão | **473, todas 200** |
| `summary` na mesma sessão | **133, todas 200** |
| mediana do 1º bloco de 50 | 422 ms |
| mediana do ÚLTIMO bloco de 50 | **391 ms** |
| 500, 429 ou 403 | **zero** |

A casa não só nunca recusou: ficou **mais rápida** no fim da rodada. Não há cota nem punição
por rajada. E a cauda do gravador, no instante da travada, mostra o absurdo:

```
nav  FALHOU  9145 ms
conf 200      394 ms   ← a casa respondeu, rápido
nav  FALHOU  9017 ms
conf 200      178 ms   ← e de novo
```

### A causa

Cada detalhe era aberto com `location.hash = rota`, e **toda atribuição ao hash empilha uma
entrada no histórico do navegador**. Passadas ~420 entradas, o roteador da página da bet365
para de reagir à troca de rota: a `confirmation` continua voltando 200, mas sempre do **mesmo**
bilhete, e o `esperarCodigo` estoura o teto em todos os seguintes.

Reproduzido duas vezes no mesmo dia, em sessões independentes: quebrou na **435ª** navegação e
na **417ª**. Depois disso, 100% de falha e zero recuperação.

**"Reconectar" não cura**, e era essa a parte cara: o operador reconectava, o robô recomeçava,
e cada bilhete restante consumia 9 s para produzir nada. Só recarregar a página cura.

O conserto é `location.replace(rota)`, que navega sem empilhar. Nos três lugares que mexiam no
hash: a navegação, o bounce do retry e a volta para a lista.

### E a prova do conserto é do MECANISMO, não do sintoma

O jeito óbvio de validar seria repetir uma varredura grande e ver se passa das 435. Custa caro:
foi exatamente esse tipo de varredura que bloqueou o histórico de duas contas no mesmo dia.

Em vez disso o gravador passou a registrar `history.length` em cada `nav`. Medido na conta de
maior movimentação, **83 navegações seguidas**:

```
H_primeira: 18 · H_ultima: 18 · H_max: 18
navOk: 414 · navFalha: 0 · statusConf: {"200": 414}
```

**O contador não se mexeu.** Com `location.hash =` essas 83 navegações teriam empilhado 83
entradas; com `replace`, zero. O muro se formava por acúmulo de entradas, então provar que o
acúmulo parou prova que ele não pode mais se formar, **sem precisar chegar perto dele**.

> **Método que vale para além deste caso:** quando o sintoma é caro de reproduzir, meça a
> **grandeza intermediária** que o causa. Aqui o sintoma custava uma conta bloqueada por horas
> e a grandeza custava uma linha de instrumentação.

### Os três defeitos que o diagnóstico errado escondia

- **A folga de 900 ms virou 60% do custo por bilhete** (1.523 ms medidos: 617 de navegação
  real, 906 de espera nossa) para proteger de uma rajada que nunca incomodou ninguém.
- **Passada que não termina não grava memória.** O `b3Lembrar` só rodava no fim do laço, e
  recarregar a página no meio — o gesto natural de quem vê a captura travada — matava a rodada
  antes disso: **435 bilhetes detalhados, ~15 minutos de `confirmation` paga, perdidos.**
- **O retry com bounce nunca teve chance.** Existia para renovar um token vencido que nunca
  estava vencido.

> **Sintoma para reconhecer isto noutro campo:** o remoto responde **200 e rápido**, e mesmo
> assim o seu laço conta falha. Quando o erro que você registra é um **timeout SEU**, e não um
> status do outro lado, a culpa quase nunca é do outro lado. Registre o status da resposta
> antes de escrever a teoria — aqui foram anos de teoria construída sobre um 500 que nunca
> aconteceu.

## A memória indexada pela VISÃO, não pela aposta — bet365, 2026-09-20

Varrendo um período de 1049 bilhetes já planilhados em ~95%, o driver registrou
`alvos 1038 · pulados 0`: a memória `b3Detalhes` não reconheceu **um** bilhete.

A causa está documentada no próprio arquivo desde sempre, sem ninguém ter ligado as pontas: o
`ID` do `summary` é **da visão**, não da aposta. As últimas 24h vêm no namespace `D1`, as 48h e
o Intervalo de Datas vêm no `D0`. A memória é indexada por esse `ID`.

Medido com as duas visões carregadas com cinco minutos de diferença, em 269 entradas:

```
TP 20260921002749000
  D0  id=49911954609          code=YR5088082431I  stake=160,00
  D1  id=3152534307690061594  code=YR5088082431I  stake=160,00
```

**O mesmo código de comprovante.** São 189 apostas reais aparecendo como 269 entradas, com
**77 duplicatas entre visões**: bilhetes que acabaram de pagar `confirmation` e pagaram de novo.

Dentro do mesmo namespace a memória funciona bem (numa passada seguinte: `alvos 282 ·
pulados 425`). **O desperdício mora só na fronteira entre visões.**

O campo estável é o **`TP`** (carimbo de tempo do bilhete), idêntico nas duas visões em 6 de 6
pares conferidos por código. Ele **não é único sozinho**: nas mesmas 269 entradas, 3 `TP` se
repetiram dentro da mesma visão, que é aposta feita no mesmo segundo. Precisa do desempatador
que o projeto já usa para dedup sem id — stake e odd, ambos no `summary`, de graça.

> **Sintoma para reconhecer isto noutro campo:** uma memória que nunca acerta, num universo
> onde você sabe que quase tudo já foi visto. Antes de suspeitar da memória, pergunte se a
> **chave** dela pertence ao dado ou à consulta que o trouxe. Id de listagem é da listagem.

## A stake editada à mão que quase virou R$ 307,50 de P/L — reparo da meia vitória, s382

O `corrigir_meia_vitoria_s356.py` pula bilhete com correção humana, e a lista de campos
era `('resultado', 'odd')` — **os campos que ele ESCREVE**. O ensaio do reparo dos 65
bilhetes da bet365 mostrou por que isso não basta.

O bilhete **#262170** (`Coreia do Sul -10.5`, conta `Bet365 [Vinicius]`, dono `Jaao26`):

```
bloco da casa:  Stake: 100,00 · Odd: 2,05 · Ganho → W (retorno R$ 205,00)   ← 100 × 2,05 = 205
banco:          stake 250 · odd 2,05 · W                                     ← stake EDITADA à mão
```

A régua é uma conta entre a **stake do banco** e o **retorno do bloco**. Com a stake
editada e o bloco intacto, os dois números deixaram de descrever a mesma aposta: 250
contra 205 fecha como "cashout com prejuízo", e o veredito devolvia `W @ 0,82`, trocando
um P/L de +262,50 por −45,00. **R$ 307,50 escritos por cima de uma linha que o dono já
tinha ajustado.**

Não é erro de margem, é erro de categoria: o número certo de uma fonte comparado ao
número certo de outra.

**A trava passou a cobrir `stake` também.** É a mesma família do *"gate que confere UM
campo deixa os vizinhos livres"* do `CLAUDE.md`, com o detalhe que faltava: a lista de
campos travados tem de conter os que o script **LÊ**, não só os que ele escreve.

> **Sintoma para reconhecer isto noutro reparo:** o script combina um valor do BANCO com
> um valor de uma FONTE congelada (bloco, extrato, planilha). Todo campo do banco que
> entra nessa conta é campo que uma edição humana pode ter mexido, e a fonte não
> acompanha. Pergunte quais campos a conta LÊ antes de escrever a lista de travas.

**A segunda trava da mesma rodada: a ambiguidade do `stake/2`.** O `#213760`
(`Under 2,5 Gols`, retorno 40,18 sobre stake 80,36) está gravado como `HL`, e o veredito
queria `W @ 0,50` — porque `HL` exige linha partida na descrição e a casa imprimiu a linha
sem a partição. Os dois pagam o mesmo dinheiro, então trocar ali é ruído por ruído, e a
regra do `CLAUDE.md` já dizia: **só se escreve onde o DINHEIRO muda.** O script agora pula
esse caso e o caminho por `--id` continua aberto para decisão humana.

**O que o reparo entregou (bet365, 23/09):** 63 linhas, 62 `W→HW` e 1 `L→V`. O P/L mexeu
**R$ 178,76 no total**, e R$ 180 disso são de um único bilhete que a casa **devolveu**
(`Status: Devolvida/void`) e estava gravado como perdido. Os 62 somam −R$ 1,24 de
arredondamento. A taxa de `W` conferida contra o retorno subiu de **98,7% para 99,8%**, e
os `HW` da base foram de **124 para 187**.

## Oito defeitos num caminho novo, e seis eram da TUBULAÇÃO — "Resolver apostas abertas", s382

O botão nasceu ao lado de uma captura que funciona há meses. Foi para a mão do tester oito
vezes no mesmo dia. **Nenhum dos defeitos estava na ideia; todos estavam em coisas que o
código antigo, a um palmo de distância, já resolvia.**

| # | o que era | tinha a ver com o caminho escolhido? |
|---|---|---|
| 1 | `sync` lia `st.casa`, e `casa` não estava na lista do `chrome.storage.local.get` | não |
| 2 | o frame de cima respondia primeiro e ganhava a corrida | não |
| 3 | a resposta não era postada para `window.top`, e o content só roda lá | não |
| 4 | o repasse entre frames copiava campo a campo e perdia o `pedido` | não |
| 5 | o POST da extensão levava **403**: a rota não estava em `_CAPTURA_ISENTAS` | não |
| 6 | o clique travava em "Procurando…" quando a extensão era atualizada com a aba aberta | não |
| 7 | a URL saía com `%3A` no lugar dos dois-pontos | sim |
| 8 | (em aberto) o termo gerado não é aceito pela casa | sim |

**Seis de oito aconteceriam igual em QUALQUER forma de buscar.** Isso derruba o reflexo de
"trocar de abordagem quando emperra": a abordagem não era o problema, e trocar teria jogado
fora a tubulação já consertada para recomeçar com outra.

> **A regra, e ela é de método:** código novo colado num mecanismo que já funciona **começa
> copiando o mecanismo**, não reescrevendo o pedaço visível dele. Responder para o topo,
> repassar o pedido inteiro, isentar a rota da ponte, montar a URL como a página monta —
> tudo isso o `enviar()` e o `/captura/enviar` já faziam, e cada um virou um defeito por ter
> sido reescrito do zero a poucas linhas do original.

**O que o harness NÃO cobre, e por isso deixou os seis passarem verdes:** o sandbox tem **um
documento só**. Hierarquia de frames, ciclo de vida da extensão e o `chrome.storage` real
ficam de fora por construção. Os gates novos (§11 a §14 do caso da bet365) são **estruturais
de propósito** — leem o texto do arquivo — porque é a única forma de travar algo que o
andaime não consegue executar.

> **Sintoma para reconhecer isto noutra frente:** a suíte inteira verde, o `node --check`
> limpo, e o operador dizendo "não aparece nada". Quando o verde e a tela discordam, o
> ambiente do teste é o suspeito, não o relato.

### O termo que a casa emite para quem pede por fora não serve, e o dela REUSADO serve (s387)

Dois dias de conserto no "Resolver apostas abertas" foram gastos numa hipótese que ninguém
tinha testado: a de que o `X-Net-Sync-Term` obtido pela máquina da própria página seria
aceito. A casa devolvia **200 com corpo de 0 byte** em 19 de 19 chamadas, e como esse é o
MESMO corpo que ela devolve quando não há aposta na janela, cada tentativa parecia "quase".

**O que cada rodada de medição eliminou**, em duas idas à conta real:

| medido | conclusão |
|---|---|
| a URL **verbatim da página**, com termo novo, volta vazia | **não é a URL.** As sete tentativas mexendo em ordem, escape e formato eram no lugar errado |
| `termo recebido · tipo=string · len=1500` | **não é lixo no header.** A hipótese do `"[object Object]"` morre |
| `X-Request-Id` da página **=** `Locator.Guid` | **não é o id de requisição** |
| a mesma chamada por `XMLHttpRequest` volta vazia | **não é `fetch` × XHR** |
| não limpar `ns_gen5_net.url` antes da chamada: vazia | **não é a limpeza do objeto da página** |
| **o termo DA PÁGINA, reusado: `200 · 3.374 bytes · 10 bilhetes`** | **o termo dela FUNCIONA, e não é de uso único** |

E a comparação que explica o resto, com os dois termos assinando **a mesma URL**:

```
da PÁGINA: len=1536 · início "AzQABAA6AAHqtTlN07OHiMwoDE99" · fim "uJWYM6x+W4gw2+jg47c="
NOSSO:     len=1536 · início "AzQABAA6AAHqtTlN07OHiMwoDE99" · fim "f5AxS+CcWM11O3FkpPw="
```

**Mesmo input, mesma estrutura, assinatura diferente.** O gerador tem estado, e o que ele
entrega a quem pede por fora a casa recusa — sem erro, sem status diferente, com o corpo
vazio que se confunde com "não há aposta". É o desenho de um token marcado, e é por isso
que nenhuma quantidade de conserto na requisição ia funcionar.

> **A lição de método, e ela vale para qualquer parede remota:** quando o sintoma de
> "recusado" é idêntico ao de "não existe", **toda tentativa parece quase certa** e a
> depuração vira adivinhação com custo. O que quebrou o impasse não foi mais uma tentativa,
> foi montar um **controle**: repetir a requisição que comprovadamente funciona, mudando
> uma variável por vez. Cinco chamadas responderam o que dezenove não responderam.
>
> **E o controle tem de existir ANTES da primeira tentativa de conserto.** A pergunta
> "qual requisição eu sei que funciona, e o que a minha tem de diferente dela?" estava
> disponível no primeiro minuto do primeiro dia.

### A odd que era a da PRIMEIRA PERNA, e ela valia 30% das abertas (s387)

O "Resolver apostas abertas" casa a aposta por `carimbo | stake | odd`. A odd que a extensão
mandava era `_oddDecimal(b.oddFrac)`, e o `oddFrac` do `parseSummary` é o `OD` da **primeira
seleção** do bilhete.

**A casa não publica odd combinada.** Isso estava escrito, medido e em produção desde sempre,
a poucas linhas dali: o `formatTicketB3` só imprime `Odd:` quando `nSel === 1`, e a s386
mediu que **zero de 3.442 blocos `Tipo: Múltipla` trazem linha de odd**. Em múltipla, quem
calcula o produto é quem lê o bloco, e é o produto que fica no banco.

**Medido na base em 24/09**, abertas de bet365 **com carimbo** (o universo do botão):

| | |
|---|---|
| abertas com carimbo | **113** |
| com 1 perna (a odd do summary descreve o bilhete) | 79 |
| com 2+ pernas | **34** (30%) |
| dessas 34, a odd do banco = odd da 1ª perna | **0** |
| dessas 34, a odd do banco = **produto** das pernas (2 casas) | **34** |
| stake do banco ≠ stake do bloco | **0 de 113** |

Zero em 34 não é margem, é campo errado. E o modo de falha é o pior possível para quem está
depurando: a chave não bate, o bilhete sai como `sem_par`, e **o sintoma é idêntico ao de "a
casa não devolveu nada"** — que é exatamente o defeito que estava sendo caçado ao lado.

**A régua certa é a do `content.js`, copiada e não reinventada**, com as duas exceções que
ela já tinha: **SISTEMA (`BC > 1`) não tem produto** (a odd é a média das linhas,
`MASTER_RESULTADO §7.3`; a mutação que tira esse guard produz `18,7` onde a média é bem
menor) e **perna sem odd legível não tem conta** (produto de parte das pernas é um número
que existe e passa em toda checagem de forma). Nos dois casos a odd sai **vazia**, e vazia
não forma chave: o bilhete vira "a conferir" em vez de casar errado.

**Por que nenhum gate pegava:** o `casaDublada` do harness gerava todo bilhete com **uma
seleção** (`od: "4/5"`). Não havia múltipla, não havia sistema, não havia perna sem odd — o
falso verde nº 2 do `CLAUDE.md`, o dado sintético que não exerce a regra. O dublê ganhou
`pernas` e `bc`; **4 mutações, 4 detectadas.**

> **Sintoma para reconhecer isto noutro casamento:** uma chave cujo campo tem, na fonte, um
> significado mais ESTREITO do que no banco. `OD` é a odd de uma seleção; `odd` é a do
> bilhete. O nome igual nos dois lados é o que faz ninguém conferir.

### O nono defeito, e ele estava ATRÁS de um gate verde — o cursor que andava 1 s por requisição (s387)

O botão tinha oito defeitos conhecidos e um gate de paginação verde com três casos. O nono
apareceu quando se perguntou, pela primeira vez, se aquele gate testava alguma coisa.

**A mutação que revelou:** trocar `proximo = menorMs` por `proximo = cursor` (o cursor que
não anda, exatamente o que o caso 10c existe para pegar) **passou VERDE**. O motivo é de
arranjo, não de asserção: o caso rodava **com o fuso lido da casa**, e aí a janela é de 1
segundo e a 1ª chamada já traz o alvo. **O laço nunca paginava.** A paginação só existe no
caminho CEGO, e nenhum caso a exercia desde que o fuso passou a ser lido (s382).

**O defeito que o gate consertado achou, e ele estava NO AR na 0.7.28:**

```
  cursor (o `to` que se pede)  → UTC
  TP     (o carimbo que volta) → hora do REINO UNIDO
  cursor = menorMs             → compara os dois CRUS
```

Com uma hora de diferença entre os dois, `menorMs` **nunca** fica abaixo do `cursor`
enquanto a distância for menor que o offset. O ramo de desempate (`cursor - 1000`, escrito
para dois bilhetes no mesmo segundo) ganhava **todas** as voltas, e o cursor descia **um
segundo por requisição**. Medido no harness: **40 páginas, o teto, alvo não encontrado,
zero erro em lugar nenhum.** Para atravessar uma hora nesse passo seriam 3.600 chamadas,
contra um teto de volume que já bloqueou três contas.

**E converter o carimbo NÃO resolve**, que foi a primeira tentativa: no caminho cego o
offset é justamente o que não se conhece. A saída dispensa o fuso, porque **a DIFERENÇA
entre dois carimbos é a mesma nos dois fusos**:

```
  cobertura = maior TP da página − menor TP da página
  proximo   = cursor − cobertura − 1000
```

O cursor recua o intervalo que a página cobriu, mais um segundo para não repetir a
fronteira. Vale com o fuso lido e sem ele.

**Gate: 4 mutações, 4 detectadas** (a régua antiga, cobertura fixada em zero, o segundo de
folga removido, e a página curta deixando de encerrar). A quarta só foi detectada depois
que um caso novo nasceu para ela: apagar `bets.length < PAGINA` passava verde porque nos
outros cenários quem encerrava era o piso da janela, e a conta de chamadas continuava
dentro do teto. O caso que separa os dois é o **histórico que acaba dentro da janela**.

> **Sintoma para reconhecer isto noutro laço:** um cursor cujo próximo valor vem de um
> campo da RESPOSTA, enquanto o valor pedido vem de um cálculo NOSSO. São dois espaços
> diferentes, e a conversão entre eles é fácil de esquecer porque o laço não dá erro: ele
> anda devagar, gasta o teto e devolve "não achei".
>
> **E o de método, que é o mais caro:** o caso do harness foi escrito para um cenário
> (janela cega) e continuou passando depois que o código mudou de cenário (janela de 1 s).
> Gate que não falha quando o código quebra não é gate, é decoração — e este tinha três
> casos, nome certo e comentário explicando a armadilha que ele não testava mais.

### E duas armadilhas de FERRAMENTA que custaram duas rodadas

1. **O heredoc do bash come barras invertidas** (já registrado na memória do projeto, e
   repetido três vezes neste dia). Um `` de regex virou o caractere de controle `0x08`, e
   o gate passou verde **sem testar nada** — a mutação é que denunciou. Onde houver escape,
   use o editor de arquivo, não o heredoc.
2. **Gate que encontra a si mesmo.** Um teste procurava `context invalidated` no arquivo
   inteiro para provar que o erro era tratado; a frase continuava no **comentário** logo
   acima do código desligado. Gate de presença de texto procura a **mensagem que o usuário
   vê**, nunca a palavra que o programador escreveu.

