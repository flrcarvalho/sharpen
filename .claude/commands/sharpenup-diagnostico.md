---
description: Casa parou de capturar ou trouxe dado errado - arvore de diagnostico por sintoma, sem chutar
argument-hint: "<Casa> <sintoma>  (ex.: KTO 0 bilhetes)"
allowed-tools: Read, Grep, Glob, Bash(node:*), Bash(python:*), Bash(git log:*), Bash(git diff:*)
---

# Diagnostico da captura: $ARGUMENTS

**Regra desta sessao: diagnosticar com PROVA, nunca com deducao.** O historico do projeto
mostra que a primeira hipotese costuma estar errada (s179: culpei o robo, era chunk sumido).
Antes de propor conserto, tenha um numero, um log ou uma linha de codigo que feche a conta.

Leia `docs/SHARPENUP_ARQUITETURA.md` (§3 contrato, §5 registro, §7 guardas) antes de opinar.

## 1. Colete a prova ANTES da hipotese

Peca ao Feca (ele tem o navegador):

- a linha de **autodiagnostico** que o robo mostra na tela quando da 0
  (`hook · respostas · bilhetes vistos`);
- o **console** com o filtro `[SharpenUp` (o inject loga endpoint, totais e paginacao);
- na bet365, trocar o contexto do console de `top` para o frame de **membros**.

Se o sintoma for dado errado (odd/data/status), peca **o bilhete na tela + o JSON** da
requisicao. A verdade e o que a casa renderiza.

## 2. Arvore por sintoma

**"0 bilhetes"** — leia o autodiagnostico:

| Sinal | Significa | Onde olhar |
|---|---|---|
| `hook: NAO carregou` | o inject nao entrou na pagina | aba aberta antes de recarregar a extensao (**Ctrl+Shift+R**) · `manifest.json` matches · dispatch no `popup.js` · a lista roda em iframe de outra origem? |
| `hook ATIVO · respostas: 0` | o endpoint mudou de nome/forma | `RX` do inject vs a URL real no Network |
| `respostas > 0 · vistos: 0` | o formato do payload mudou | campo da lista (`bets`/`items`/`historyCoupons`) e a chave do bilhete |
| `vistos > 0` mas nada no dashboard | a ponte ou o envio | sessao expirada (popup diz offline) · `envioPendente` no popup (botao Reenviar) · 409 casa incompativel |

**"Botao Conectar nao acende"** → `CASAS_CONECTAVEIS` no `index.html` **e**
`_MODO_POR_CASA` no `captura.py`. Rode `python tools/audit_sharpenup.py <CASA>` — foi
exatamente esse par que custou a s191.

**"Veio menos bilhete do que a casa mostra"** → conte antes de teorizar:
- a lista parou cedo? (fim autoritativo vs teto de inatividade)
- a janela de dias ou o `stopId` cortaram? (janela corta **so resolvidas**)
- o texto chegou inteiro mas o TSV veio curto? Entao e **perda de chunk**: cruze
  `[Codigo:]` do texto com a 11a coluna do TSV (`repository.conferir_cobertura`) — e
  confirme que a regex de codigo cobre essa casa, senao a conferencia esta **desligada**.

**"Odd/data/status errados"** → nunca conserte no formatador antes de saber a origem:
milesimos? campo zerado na perdida? odd truncada pela casa? fuso? formato de data mudou?
Consulte o "Livro de armadilhas" em `docs/GUIA_CASA_SHARPENUP.md`.

**"Duplicou"** → o codigo veio vazio ou mudou? Dedup e por codigo; sem codigo, a regra de
duplicata exige stake+odd+descricao batendo os tres.

## 3. Isole a mudanca

Se a casa **funcionava antes**: `git log --oneline -- extensor/` e veja o que mudou desde a
ultima captura boa. Ramifique pelo dado (ex.: so o ramo novo) para nao tocar o caminho
provado — o que funciona nao pode quebrar por causa do conserto.

## 4. Trave a regressao

Todo conserto de captura termina com **uma linha nova no caso do harness**
(`extensor/harness/casos/<casa>.mjs`), com a fixture que reproduz o defeito. Sem isso a
armadilha volta — foi o que aconteceu tres vezes com o parser da bet365.

## Ao final

Reporte: sintoma, **prova** coletada, causa (com arquivo:linha), conserto proposto, e o
que ficara travado no harness. Nao aplique o conserto sem aprovacao.
