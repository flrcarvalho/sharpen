# Depoimentos de usuários — matéria-prima de marketing

> **O que este arquivo é:** a voz dos usuários reais do Sharpen, transcrita e cruzada
> com o que a base deles mede. É **matéria-prima**, não peça publicada: daqui saem o
> texto da landing, o roteiro dos vídeos, a ordem das seções e os posts do X.
>
> **O que ele não é:** um arquivo de citações bonitas. Toda afirmação de usuário que
> virar peça pública precisa ter, ao lado, o número medido na base dele. Fala sem
> número é opinião; fala com número é prova.

## Regras

1. **Áudio original fica em `audios/`** (gitignored, é pesado). Transcrição integral
   com timestamp em `transcricoes/`. Aqui fica só a ficha.
2. **Transcrição é local** (ffmpeg via `imageio_ffmpeg` + `faster-whisper`, modelo
   `small`, `language="pt"`). Voz de cliente não sai da máquina.
3. **Citação publicada é verbatim.** Quando o reconhecedor erra uma palavra óbvia, a
   correção vai entre colchetes e o erro fica registrado na ficha.
4. **Áudio que o Feca encaminha já vem autorizado.** Regra dele, 23/09/2026:
   *"TODOS QUE EU TE MANDAR JÁ ESTÃO AUTORIZADOS."* Ele fala com a pessoa antes;
   o encaminhamento é a autorização, e a ficha registra a data em que chegou.
   Não há mais status `pendente` travando peça.
   > O que isso **não** cobre, e continua valendo: dado de terceiro que aparece
   > no áudio sem ser do depoente — nome de tipster, de fornecedor, de grupo,
   > e-mail, valor de custo de outra pessoa. Isso não é dele para autorizar, e
   > fica fora da peça como sempre esteve.
5. **O número do cartão sai do Postgres**, medido na data da ficha, nunca estimado.

## Índice

| Quem | Tipo | Data | Duração | Uso | Transcrição |
|---|---|---|---|---|---|
| Jonathan | usuário (operação) | 19/09/2026 | 5min06 | ✅ liberado | [jonathan-2026-09-19.txt](transcricoes/jonathan-2026-09-19.txt) |
| Germano | usuário (adoção recente) | 20/09/2026 | 7min09 | ✅ liberado | [germano-2026-09-20.txt](transcricoes/germano-2026-09-20.txt) |
| Ewanderson | usuário (6 dias de uso, alto volume) | 21/09/2026 | 3min23 | ✅ liberado | [ewanderson-2026-09-21.txt](transcricoes/ewanderson-2026-09-21.txt) |
| Diogo | usuário (rotina — 86 dias de captura em 90) | 23/09/2026 | 2min19 | ✅ liberado | [diogo-2026-09-23.txt](transcricoes/diogo-2026-09-23.txt) |

> **Arquivo irmão:** [VOZ_DO_FUNDADOR.md](VOZ_DO_FUNDADOR.md) guarda o pitch do Feca
> gravado sem roteiro. Voz de cliente é **prova**; voz de fundador é **copy**. Os dois
> se cruzam: o cliente faz a pergunta ("onde está esse dinheiro?") e o fundador dá o
> nome da resposta ("um mapa de onde está o dinheiro").

---

## Jonathan — 19/09/2026

**Perfil:** 2º maior usuário da base. Opera carteira com contas compradas, vários
fornecedores e muitos tipsters. É o caso de "operação", não de apostador individual.

### Cartão de prova (medido em 19/09/2026)

| Medida | Valor |
|---|---|
| Apostas planilhadas | 13.715 |
| Nos últimos 30 dias | 4.612 (≈ **154 por dia**) |
| Dias com captura, em 90 | 58 |
| Casas | 29 |
| Contas cadastradas | 90 (20 já arquivadas) |
| Tipsters cadastrados | 22 (60 nomes distintos nos bilhetes) |
| Turnover | R$ 1.994.749 |
| Usa desde | 04/07/2026 |

**Prova cruzada que vale mais que o cartão:** ele é hoje o **único dono com custo de
tipster, custo geral e custo por conta preenchidos** no `custo_store`, com tipo de
cobrança declarado por tipster e lançamentos recorrentes (Blogabet e outros). Ele não
está dizendo que a ferramenta de custo é boa, ele é o usuário que mais a usa. A fala
sobre custo é comportamento medido, não elogio.

### Os cinco temas, na ordem em que ele mesmo priorizou

1. **Tempo (abre o áudio com isso).** Antes 1 hora por dia, hoje 15 a 20 minutos.
2. **O acúmulo deixou de punir.** Pular um dia antes custava 3 horas; hoje custa 30 a
   35 minutos. Esse é o ponto que ninguém do nosso lado tinha pensado.
3. **Parou de perder aposta.** Antes passava batido ou ficava "para lançar depois" e
   era esquecida. Hoje planilha direto pela casa.
4. **Sabe de quem é cada aposta.** Usa os **centavos da stake** como legenda de
   tipster, e a extração lê isso sozinha.
5. **Descobriu para onde o dinheiro ia.** Custo de conta, duração da conta, qual casa
   dura mais, turnover por casa, custo por fornecedor, custo de tipster e custo de
   fora (contador, VPN, navegador). Achou gargalo e **reduziu custo**.

### Trechos marcados para clipe

| # | Timestamp | O que é | Fala |
|---|---|---|---|
| **A** | 02:18 → 02:49 | **O melhor gancho do material.** É o problema que o produto resolve, dito por um cliente | *"Antes eu planilhava e ouvia: esse mês eu ganhei tanto, ganhei 10 mil reais. Aí eu olhava no meu banco, olhava no saldo, mas não parece que eu ganhei tanto dinheiro assim. Onde é que está esse dinheiro?"* |
| **B** | 00:26 → 00:35 | Prova de tempo, o número que vira manchete | *"Antes eu dedicava por volta de uma hora por dia para planilhar as apostas. Hoje eu faço isso em cerca de 15 a 20 minutos."* |
| **C** | 00:41 → 00:59 | O acúmulo. Argumento novo, não estava em peça nenhuma | *"Se eu ficasse um dia sem planilhar era praticamente 3 horas planilhando. Hoje, dos 20 minutos que eu levaria, talvez leve 30, 35, no máximo."* |
| **D** | 01:02 → 01:15 | Perda de aposta | *"Não perder as bets, que às vezes uma ou outra acabava passando batido, ou que eu marcava para depois voltar e planilhar, esquecia. Agora isso não acontece mais, porque eu planilho direto pela casa."* |
| **E** | 01:17 → 02:03 | Atribuição por legenda. Explica um recurso difícil melhor do que nós explicamos | *"Na hora de colocar a minha stake eu já informo quem é o tipster. No meu caso eu utilizo os centavos. Na hora de fazer a extração o Sharpen já lê a minha stake, ele sabe de quem é aquela aposta."* |
| **F** | 04:11 → 04:23 | **Responde a objeção da demo.** Guardar para usar ao lado do `/realtrial` | *"No Sharpen, à primeira vista, para quem não conhece, ele pode parecer complexo. Mas ele é muito simples de utilizar. O processo de aprendizado dele é muito fluido, é muito natural."* |
| **G** | 04:52 → 05:06 | Fecho de vídeo | *"Hoje, em menos tempo, eu faço mais coisas. Eu tenho mais dados, tenho mais informação sobre a saúde da minha banca do que eu tive ao longo de toda a minha jornada."* |

> Correções de reconhecimento nestes trechos: "CHP" e "chip" = **Sharpen**;
> "chipster" e "tips" = **tipster**. Conferir no áudio antes de queimar legenda.

### O que isto muda nas nossas decisões

- **Os dois números de tempo não se contradizem, e essa é a promessa.** "30 minutos por
  semana" e "15 a 20 minutos por dia" descrevem a mesma coisa vista de dois usos:
  **o tempo do Sharpen não escala com o volume**. Quem olha todo dia gasta 15 a 20
  minutos e sabe tudo; quem só senta no domingo gasta pouquíssimo e não paga juros
  pelo acúmulo. Eixo completo em [VOZ_DO_FUNDADOR.md](VOZ_DO_FUNDADOR.md).
- **A landing deve abrir pelo trecho A, não pela praticidade.** "Ganhei 10 mil, cadê
  o dinheiro?" é a dor; praticidade é a solução. Hoje a página começa pela solução.
- **O argumento do acúmulo (C) é inédito** e ataca a objeção real de quem já tentou
  planilhar e desistiu: não é o tempo por dia, é a dívida que se forma ao pular um dia.
- **O trecho F é a resposta à objeção do `/realtrial`.** O maior usuário diz que
  parece complexo e que o aprendizado é fluido. Isso vai ao lado da demo, não escondido.
- **Custo é seção de primeira dobra, não de rodapé.** Foi nele que ele mais falou, e é
  onde ele mais usa o produto.

---

## Germano — 20/09/2026

**Perfil:** o oposto do Jonathan, e é por isso que vale tanto. Usa há **três semanas**,
e o depoimento dele responde a objeção que o do Jonathan não alcança: *"vou conseguir
tirar valor disso rápido?"*. Também é o único que **compara com os concorrentes**,
porque tentou vários antes.

### Cartão de prova (medido em 20/09/2026)

| Medida | Valor |
|---|---|
| Apostas planilhadas | 1.670, **todas nos últimos 30 dias** |
| Casas | 13 |
| Contas cadastradas | 18 (5 já arquivadas) |
| Tipsters | 21 |
| Turnover | R$ 347.203 |
| Dias com captura | 9 |
| Usa desde | 07/09/2026 |

**O que o número prova sozinho:** em 13 dias ele cadastrou 21 tipsters, 18 contas, já
arquivou 5 e lançou custo de tipster, de conta e geral. Não é alguém experimentando,
é alguém que **montou a operação inteira dentro do produto na primeira semana**.

### Trechos marcados para clipe

| # | Áudio · tempo | Por quê | Fala |
|---|---|---|---|
| **G1** | 1 · 00:08 → 00:28 | **O comparativo, dito por cliente, sem nomear ninguém.** É a objeção número um de quem já tentou planilhar | *"Eu nunca tive saco. Já comprei alguns planilhadores para tentar, e nunca passou de três dias. Você tinha que ficar mandando foto de bet por bet, o planilhador dava bug, o jogo vinha por modalidade inexistente, stake errada. E isso falando dos maiores do mercado que tem hoje."* |
| **G2** | 3 · 00:14 → 00:27 | **Repete a história do Jonathan, com outro número.** Dois usuários independentes, a mesma descoberta | *"No final do mês você acha que lucrou: rapaz, fiz 8 mil reais em apostas esse mês. Mas quando você vai ver quanto de conta queimou, quanto de tipster pagou, essa conta nem fecha direito."* |
| **G3** | 3 · 01:07 → 01:14 | **O fecho mais duro de todo o material.** É a consequência dita em voz alta | *"Aquele mês em que eu não estava planilhando, que eu achava que tinha saído positivo, eu não saí positivo."* |
| **G4** | 3 · 00:52 → 00:59 | Explica o **mecanismo** de por que o custo some. Nenhum texto nosso explica tão bem | *"Como a conta é comprada, quando você é limitado você está basicamente pegando do seu saldo. Você não tinha esse controle. E agora eu tenho."* |
| **G5** | 1 · 00:46 → 01:04 | Precisão, no caso mais difícil (print, casa sem captura) | *"As casas que não têm extrator automático, você bate o print de seis apostas ao mesmo tempo. Eu nunca tive problema de pegar uma aposta errada, uma stake errada, de não entender qual é o evento. Sempre ele consegue entender."* |
| **G6** | 2 · 00:23 → 01:03 | **Número honesto de quem tem 3 semanas**, e a projeção que ele mesmo faz | *"Hoje, com 13 casas, eu demoro basicamente 50 minutos para planilhar. Se eu usasse stake quebrada, o tempo cai de 50 minutos para 25, no máximo."* |
| **G7** | 6 · 00:00 → 00:16 | Fecho | *"É o único planilhador que eu consegui usar a ponto de ter paciência. De não ser uma coisa exaustiva, de ficar batendo print sem parar, de ficar tendo que corrigir coisa toda hora porque está errada."* |

> Correções de reconhecimento: "steak" = **stake**; "best"/"baita" = **bet**;
> "casos" (áudio 2) = **casas**; "tips"/"tímpit" = **tipster**. O nome de grupo citado
> no áudio 5 **não vai para peça nenhuma**.

---

## Ewanderson — 21/09/2026

**Perfil:** o mais novo de todos, **seis dias de uso**, e o de maior volume relativo.
Opera muitas casas ao mesmo tempo e segue vários grupos. É o depoente que traz o tema
que nenhum outro tinha trazido: **a liquidação automática**.

### Cartão de prova (medido em 21/09/2026)

| Medida | Valor |
|---|---|
| Apostas planilhadas | 1.623, todas em **6 dias** |
| Casas na base | 26 |
| Contas cadastradas | 39 |
| Tipsters | 5 |
| Turnover | R$ 50.468 |
| Dias com captura | 7 |
| Usa desde | 15/09/2026 |

### Trechos marcados para clipe

| # | Áudio · tempo | Por quê | Fala |
|---|---|---|---|
| **E1** | 01 · 00:00 → 00:37 | **Tema inédito no material: a liquidação automática.** Ninguém mais falou disso, e é recurso que não está em peça nenhuma | *"O que eu mais curto no Sharpen é que não tem que fazer nada manual. Até as apostas pendentes ele lê de novo e resolve sozinho. No outro eu tinha que fazer isso manual, e às vezes tinha que voltar a procurar a aposta lá na casa, no dia, para poder colocar o resultado."* |
| **E2** | 01 · 00:49 → 01:14 | **Terceira confirmação do acúmulo**, e a mais concreta de todas | *"Se eu deixasse sábado e domingo para planilhar na segunda, eu perdia uma manhã toda. Porque sábado e domingo é aposta demais."* |
| **E3** | 01 · 01:40 → 02:10 | O custo real do acúmulo, no concorrente | *"No outro eu perdia uma manhã, às vezes mais de uma manhã, porque eu precisava sair, precisava fazer alguma coisa, e tinha que voltar à tarde para terminar. Isso mudou demais na minha rotina."* |
| **E4** | 02 · 00:29 → 00:49 | Volume, e o público que ele descreve | *"Para planilhar 15 casas, aposta por aposta, meu irmão. Para a gente que trabalha com grupos é uma loucura. Por semana vai mais de mil apostas. Com o Sharpen estou gastando mais ou menos uma hora por dia, até menos. Dia de semana é muito menos."* |
| **E5** | 01 · 01:14 → 01:40 | **Honestidade que vale ouro numa peça.** Ele mesmo diz que ainda está aprendendo | *"Como tudo é 99% automático, eu faço agora em menos de uma hora. Só não estou fazendo mais rápido porque ainda estou pegando alguns macetes, ainda estou revisando bastante, porque comecei a planilhar tem uns cinco dias só."* |

> Correções de reconhecimento: "Sharpie", "Sharpim" e "chip" = **Sharpen**; "bets" =
> apostas. O trecho E4 fala "tirava print de tudo", não "tirava a frente de tudo".

### ⚠️ Uma divergência entre o declarado e o medido, e ela é da regra da casa

Ele diz **"eu uso 15 casas de apostas diferentes"**. A base dele tem **26 casas**.

Não é erro dele nem erro nosso: provavelmente são 15 casas que ele opera com regularidade
contra 26 em que já houve aposta. Mas a peça segue a regra **número dito é número na
tela** (ver o [roteiro](../ROTEIRO_VIDEO_APRESENTACAO.md)), então **os dois números não
podem aparecer juntos**: ou se usa a fala dele com a imagem que a sustenta, ou se usa o
cartão medido sem essa frase. Usar "15 casas" de legenda embaixo de uma tela que mostra 26
é o tipo de detalhe que destrói a credibilidade da peça inteira.

> O que **bate** e pode ir junto: ele diz *"mais de mil apostas por semana"*, e a base
> mede 1.623 em 6 dias. O declarado é conservador diante do medido, que é o melhor caso
> possível para uma peça.

---

## Diogo — 23/09/2026

**Perfil:** o mais constante da base inteira, **captura em 86 dos últimos 90 dias**.
Nenhum outro depoente chega perto. Se o Jonathan é profundidade e o Germano é adoção
rápida, o Diogo é **rotina**, e é dele que vem o ângulo mais novo do arquivo.

### Cartão de prova (medido em 23/09/2026)

| Medida | Valor |
|---|---|
| Apostas planilhadas | 7.918 |
| Nos últimos 30 dias | 3.097 |
| **Dias com captura, em 90** | **86** |
| Casas | 28 |
| Contas cadastradas | 52 (7 já arquivadas) |
| Tipsters cadastrados | 20 (44 nomes distintos nos bilhetes) |
| Usa desde | 24/06/2026 |

### Trechos marcados para clipe

| # | Tempo | Por quê | Fala |
|---|---|---|---|
| **D1** | 00:43 → 01:02 | **O ângulo mais novo do arquivo inteiro.** Os outros contam que o acúmulo deixou de doer; ele transformou o acúmulo em método | *"A principal mudança na minha rotina, e foi o ponto que eu mais gostei, é que eu posso literalmente esquecer. Só fazer as apostas. Não tiro print de nada, só vou fazendo, fazendo. Depois de 2, de 3, de 4, 5 dias eu vou lá e planilho."* |
| **D2** | 01:16 → 01:31 | O antes, e é o trabalho manual inteiro numa frase | *"Antes era muito chato, porque eu tinha que ficar tirando print, depois ir lá aposta por aposta, ver se bateu, ver se não bateu, ver se foi void, ir em cada casa olhar o resultado. Isso me fazia ficar muito tempo nisso."* |
| **D3** | 00:12 → 00:29 | **Confirma a Caixa por teste próprio**, e é o argumento do dinheiro que some | *"A Caixa Inteligente, que você acompanha ali: dificilmente você vai tomar o calote, porque ele acompanha o saldo até os centavos e é bem certinho. Eu já fiz o teste com todas as casas."* |
| **D4** | 00:30 → 00:42 | **Posicionamento dito por cliente**, e é exatamente o que a marca precisa dizer | *"Ele não é só um planilhador. Ele basicamente te ajuda com toda a sua rotina de compra e venda de conta, pix pra cá, saque pra lá. É bem completo."* |
| **D5** | 01:28 → 01:43 | Benefício que ninguém tinha citado, e é emocional, não funcional | *"Você fica um pouco viciado de acompanhar a aposta, querer ver o resultado. Hoje em dia eu só faço a aposta, depois eu vejo se bateu ou não bateu."* |

> Correções de reconhecimento: "Charpen" = **Sharpen**; "a posta" = **a aposta**;
> "Best 35" = **Bet365**; "tomar os cãs" = **tomar o calote**.

> ⚠️ **O D5 é ótimo e exige cuidado.** Ele descreve passar menos tempo olhando aposta,
> o que é verdade e é bom. Mas uma peça que sugira "aposte sem acompanhar" lê como
> incentivo a apostar no escuro. Se for usado, a legenda precisa ser sobre **tempo de
> tela**, nunca sobre despreocupação com o dinheiro.

### O que ele pediu, e o que isso diz

Perguntado sobre pontos a melhorar: *"não tem muito, tudo que eu dei de orientação já foi
feito"*, e o único aberto é a **velocidade da Bet365**, que ele mesmo diz estar *"300%
melhor"* depois de duas atualizações. Não é item de backlog novo; é prova de ritmo de
resposta, e isso é material de venda por si.

### Divergências entre o que ele diz e o que a base mede

| Ele diz | A base mede |
|---|---|
| *"uso mais ou menos há um mês"* | desde **24/06**, três meses |
| *"10 a 15 casas"* (e ele mesmo ressalva que não conta as contas) | **28 casas** |

Nenhuma das duas é erro dele, e pela régua de 21/09 isso **não é para virar trabalho de
ajuste fino**. Só vale a regra de sempre: os dois números não aparecem juntos na mesma
peça. E há uma leitura simpática no primeiro: o uso virou rotina a ponto de ele perder a
noção de quando começou.

---

## As convergências — o que mais de um usuário disse sozinho

Isto é a parte mais valiosa do arquivo, e só aparece com dois ou mais depoimentos.
Quando pessoas que não se falaram dizem a mesma coisa, aquilo deixa de ser opinião e
vira **padrão**, e padrão decide o que entra na landing.

| Convergência | Quem | O que decide |
|---|---|---|
| **A dívida do acúmulo** | Jonathan (pular 1 dia = 3h) · Ewanderson (sábado e domingo = uma manhã, às vezes o dia) · **Diogo (acumula 5 dias de propósito)** · o eixo do Feca | **Quatro vozes, e a do Diogo fecha o argumento.** Os outros contam que a dívida deixou de doer; ele a transformou em método: aposta e esquece, planilha dias depois. Não é mais argumento secundário, é a promessa |
| **A Caixa pega o dinheiro que sumiu** | Diogo (*"dificilmente você vai tomar o calote, testei em todas as casas"*) · o pitch do Feca (o operador que saca de pouquinho) | O fundador levantou a hipótese; um cliente **testou em todas as casas** e confirmou. É o par que sustenta a cena da virada do vídeo |
| **"Achei que tinha lucrado, e não tinha"** | Jonathan (R$ 10 mil) · Germano (R$ 8 mil) | **Valida o arco do vídeo.** Dois usuários independentes contaram a MESMA história, com números diferentes. É a dor de abertura, não uma frase de efeito |
| **Assinatura do tipster pela stake** | Feca (401/402/403) · Jonathan (centavos) · Germano (299 / 300 / 300,50) | **Três** vozes, sendo uma delas a de quem ainda NÃO usa e por isso gasta o dobro do tempo. Seção própria, com demonstração |
| **"O outro planilhador não deu conta"** | Germano (nunca durou 3 dias) · Ewanderson (grupo por grupo, aposta por aposta) | Comparativo dito por cliente, sem nomear ninguém. É o que nós não podemos escrever sem soar arrogantes |
| **Custo invisível de conta e tipster** | Jonathan · Germano | Primeira dobra da landing. Os dois abriram por aí |
| **Precisão da leitura** | Germano (G5) · Jonathan (D) | Confiança é objeção silenciosa: ninguém pergunta, todo mundo pensa |

### O tema que só um trouxe, e que muda uma cena

**A liquidação automática** (Ewanderson, E1). Ele abre o depoimento com isso, e é o que
o fez trocar de ferramenta: no anterior, marcar o resultado exigia **voltar na casa,
procurar a aposta do dia e lançar à mão**. Um voto só, mas é de quem tem seis dias de uso
e portanto a lembrança fresca do que doía antes.

O Jonathan diz o vizinho disso ("parei de perder aposta"), e os dois juntos formam o par:
**a aposta entra sozinha e o resultado fecha sozinho.** Nenhuma peça nossa diz a segunda
metade.

### O que o Germano acrescenta e o Jonathan não tinha

- **A comparação com o mercado.** O Jonathan fala do que ganhou; o Germano fala do que
  os outros não entregaram, e ele tentou "os maiores do mercado". Isso é material que
  nós não podemos escrever sem soar arrogantes, e ele entrega de graça.
- **A prova de adoção.** Três semanas, 13 casas, operação montada. O medo de quem vê a
  tela pela primeira vez é "isso vai me tomar um mês para configurar".
- **Um número honesto que eu prefiro ao número bonito.** Ele leva **50 minutos para 13
  casas, a cada dois dias**, e diz que cairia para 25 com a stake quebrada. A promessa
  da página não deve ser um número fixo: o tempo depende da técnica e da quantidade de
  casas. O que **não** varia é o que o eixo diz: não há dívida por ter deixado acumular.

### Pedido de produto que saiu do áudio 5 (não é marketing)

Dois pedidos concretos, e nenhum deles existe hoje:

1. **Medir a liquidez do grupo.** Declarar a stake-alvo do tipster e comparar com a
   stake média efetivamente aceita ("a stake é 300, a sua aposta média é 280"), para
   saber quanto se deixou de ganhar por não conseguir passar o valor cheio.
2. **Juntar a mesma aposta feita em contas diferentes.** R$ 250 numa conta e R$ 200 em
   outra são **uma** aposta de R$ 450, e hoje contam como duas. Sem isso não dá para
   responder se vale a pena comprar mais uma conta para aquele tipster.

> **Registrados no [`BACKLOG.md §3.13`](../../../BACKLOG.md), com medição** (20/09). O
> que a medição achou: a liquidez esbarra em dado que ninguém coleta (`stake_min`/`max`
> existem no schema e estão vazios em 100% dos donos), e o agrupamento esbarra no
> CRITÉRIO, não na falta de dado — a mesma aposta em contas diferentes cobre 6,2% da base
> do Germano, 10,1% da do Jonathan e 8,9% da do Feca.
