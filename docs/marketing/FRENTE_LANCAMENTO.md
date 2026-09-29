# Frente de marketing do lançamento — o que existe, e o que falta

Registro da Equipe 2, aberta em 19/09/2026. Estrutura das duas frentes em
[`ESTRUTURA_DO_TIME.md`](../ESTRUTURA_DO_TIME.md).

## As decisões que não se reabrem sem motivo novo

| Decisão | Onde nasceu |
|---|---|
| **Eixo da promessa:** o tempo do Sharpen **não escala com o volume**. 10, 200 ou 2.000 bilhetes levam praticamente o mesmo tempo | Correção do Feca em 20/09, desfazendo a leitura de que "30 min/semana" e "15-20 min/dia" se contradiziam |
| **Conceito:** *"Onde está o meu dinheiro?"*. A pergunta é do cliente, a resposta é do fundador (*"um mapa de onde está o dinheiro"*) | Jonathan + o pitch do Feca |
| **Formato do vídeo:** história em três atos (*a investigação*), nunca pergunta e resposta | Escolha do Feca em 20/09 |
| **Voz:** narração **sintética**, sem a voz do Feca. Mas **depoimento nunca é sintetizado** | 21/09 |
| **Comunicação é software de GESTÃO**, nunca picks ou tips | É a fronteira que decide se um gateway aceita a operação na Fase 4 |
| **Peça de marketing não é auditoria:** número que muda toda semana pede ordem de grandeza | 21/09 |
| **Áudio que o Feca encaminha já vem autorizado** | 23/09 |

## O que está pronto

**Prova social** — [`depoimentos/`](depoimentos/DEPOIMENTOS.md)

Cinco depoimentos transcritos localmente (ffmpeg + faster-whisper, nada sai da máquina) e
cruzados com a base de cada um. Os perfis são variados de propósito, e isso responde à
ressalva que o próprio Gabriel levantou sobre viés de amostra.

| Quem | Uso | Volume 30d | O que ele prova |
|---|---|---|---|
| Jonathan | 3 meses | 4.612 | profundidade, e a dor de abertura |
| Gabriel | 2 meses | 6.284 | maior volume, e a palavra "auto-auditoria" |
| Diogo | 3 meses | 3.097 | rotina (86 de 90 dias), o acúmulo virando método |
| Germano | 3 semanas | 1.935 | adoção rápida, e o comparativo com o mercado |
| Ewanderson | 6 dias | 1.743 | volume alto de cara, e a liquidação automática |

Oito convergências medidas, que são o que decide a ordem das seções. A mais forte: **a
dívida do acúmulo**, em quatro vozes.

**Peças** — todas em 4K, com o ponteiro da marca

- 4 clipes de passo a passo ([`scripts/demo/gravar.mjs --4k`](../../scripts/demo/gravar.mjs)):
  trocar de conta, um clique preenche o tipster, a caixa que bate, a caixa que não bate.
- 5 cartões de prova em Remotion ([`video/`](video/README.md)), com o número lido do
  Postgres no momento do render, nunca digitado.
- Roteiro do vídeo de apresentação: [`ROTEIRO_VIDEO_APRESENTACAO.md`](ROTEIRO_VIDEO_APRESENTACAO.md).

**No produto**

- **Contador ao vivo** na landing, lendo `/publico/metricas` (agregado, sem sessão, sem a
  base de demonstração). Regra em [`app/metricas_publicas.py`](../../app/metricas_publicas.py).
- O clipe da Caixa entrou na landing, no lugar de uma imagem parada.
- **Defeito corrigido de passagem:** `autoplay muted loop` só toca o vídeo que já está na
  viewport no carregamento; os demais o navegador pausa e eles nunca retomam. O clipe do
  "Sugerir tipsters" estava parado desde que entrou na página. Resolvido com
  `IntersectionObserver`.
- **Etapa 3.5 no `/nova-ui`:** a tela tem de dizer o que ela é e o que fazer ali. O
  checklist cuidava de como a tela parece e não do que ela diz.

## O que ficou aberto

1. **Reescrita da landing** com a ordem de seções que saiu das convergências. É o próximo
   passo natural: a ordem já está decidida pelos depoimentos, falta escrever.
2. **Material do X**: perfil, bio e a fila de posts de largada.
3. **Peças que o Feca viu na 1ª revisão e não aprovou** — ele disse que falaríamos depois,
   e não disse quais.
4. **Clipes da Caixa em 3840 nativo?** Hoje saem em 2692 porque são recorte de uma região
   da tela. Ampliar seria upscale sem ganho; o caminho honesto é gravar sem recorte.
5. **Legenda escrita dentro dos clipes** ("passo 1, escolha a conta"), se o Feca quiser
   além da etapa 3.5 que entrou no checklist.
6. **A narração** ainda não foi gravada. Ao escolher a voz sintética, ouvir o ato 1
   inteiro, nunca uma frase solta: o defeito de prosódia aparece na terceira frase.

## Achados que foram para a Equipe 1

- **`BACKLOG 4.6`** — a tela de Custos abre vazia por link direto ou F5; só pinta quando se
  chega pelo menu. Medido em produção, com a hipótese apontada.
- **`BACKLOG 3.13`** — os dois pedidos de produto do Germano (medir liquidez do grupo e
  juntar a mesma aposta feita em contas diferentes), com a viabilidade medida dos dois.
