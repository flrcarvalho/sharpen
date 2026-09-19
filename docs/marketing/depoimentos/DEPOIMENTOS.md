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
4. **Sem autorização escrita, não vira peça.** Nome, voz e número são dados dele.
   A ficha registra o status, e `pendente` barra publicação.
5. **O número do cartão sai do Postgres**, medido na data da ficha, nunca estimado.

## Índice

| Quem | Tipo | Data | Duração | Autorização | Transcrição |
|---|---|---|---|---|---|
| Jonathan | usuário (operação) | 19/09/2026 | 5min06 | ✅ autorizado (19/09/2026, pelo Feca) | [jonathan-2026-09-19.txt](transcricoes/jonathan-2026-09-19.txt) |

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
