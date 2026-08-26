---
description: Fase 0/1 da casa nova no SharpenUp - reconhecer a casa no F12 e decidir o modo de captura
argument-hint: "<NomeDaCasa> [dominio]  (ex.: Novibet novibet.bet.br)"
allowed-tools: Read, Write, Grep, Glob, Bash(node:*), Bash(python:*)
---

# Reconhecimento da casa: $ARGUMENTS

Objetivo desta sessao: **descobrir o que a casa entrega e decidir o modo de captura**.
NAO escrever codigo de producao. Segue `docs/GUIA_CASA_SHARPENUP.md` Fases 0 e 1.

Antes de comecar, leia `docs/GUIA_CASA_SHARPENUP.md` (Fases 0-1) e
`docs/SHARPENUP_ARQUITETURA.md` (secoes 2 e 3).

## 1. Peca o reconhecimento a quem TEM a conta (voce nao esta no navegador)

**Nao precisa ser o Feca, e nao precisa ser conta nossa.** Casa em que ninguem aqui tem
conta se liga do mesmo jeito: quem tem a conta roda `tools/recon_casa.js` no console e
manda UM arquivo. O roteiro pronto para repassar a um tester esta em
`docs/GUIA_RECON_TESTER.md` — inclui a autorizacao que ele precisa dar antes.

O coletor ja apaga valor de header de credencial e campo de identidade. **Nunca aceite
senha, cookie ou `Copy as cURL` cru** — o inject aprende os headers sozinho, em tempo de
execucao, dentro do navegador do dono (`nv_inject.js::capturarReq`).

Se o Feca mesmo for fazer, o roteiro em 7 passos da Fase 0 do guia serve igual. O que
precisa voltar, por qualquer um dos dois caminhos:

- metodo + URL da requisicao da **lista de bilhetes** (e o corpo, se POST);
- o **response salvo** em `extensor/harness/fixtures/<casa>.<endpoint>.json`;
- como a **proxima pagina** e pedida e como a casa diz que **acabou**;
- a mesma coisa para a aba **Em aberto**;
- se ha detalhe atras de clique, qual requisicao ele dispara.

Peca que a amostra cubra: **1 aberta, 1 perdida, 1 ganha, 1 com boost (se houver), 1
multipla ou bet builder**. Sem essa cobertura o harness nao trava nada.

Se ele mandar print/HAR em vez de JSON, aceite e extraia — mas registre que a fixture
tem de existir antes da Fase 2.

## 2. Leia a fixture e responda a tabela de decisao

Com o JSON na mao, responda por escrito (isso vira o §2.5 do `casas/CASA_<X>.md`):

| Campo | Onde esta | Observacao |
|---|---|---|
| ID do bilhete | | e a chave de dedup e o `[Codigo:]` |
| Stake / retorno / odd | | esta em milesimos? |
| Odd bate com o card **na perdida**? | | KTO: `betOdds` = 0 em toda perda |
| Data (colocacao/evento/liquidacao) + fuso | | 1a coluna do TSV |
| Status (enum bruto) | | de-para so na CASA_*.md, nunca no codigo |
| Boost / cashout / freebet | | mudam a regra da odd |
| Paginacao + fim autoritativo | | `more`, `LastId`, `hasNext`... |

**Cruze cada valor com o que o card da casa mostra na tela.** Divergencia = armadilha
nova; anote, e ela vira linha do harness.

## 3. Decida o modo pela arvore da Fase 1

Aplique a arvore do guia e diga qual e o modo, com a justificativa em 1 linha.
Regras que nao se negociam:

- **Preferir API.** Texto por DOM parece simples e cobra caro depois.
- Se o modo candidato for TEXTO, **prove que ha linha em branco entre bilhetes** no
  `innerText` — sem isso o `roboScroll` junta a lista inteira num bloco so e a IA perde
  o resto em silencio (s192, KTO, ~90% perdidos).
- **Print e um resultado valido.** Casa de baixo volume nao justifica captura.

## 4. Entregue o plano da casa

Feche com um plano curto: modo escolhido, inject espelho (qual arquivo copiar),
chave de dedup, fim autoritativo, freio do popup (dias+ID / quantidade / nenhum), e as
armadilhas ja identificadas.

**Nao avance para a implementacao nesta sessao.** Ao final, diga que o proximo passo e
`/sharpenup-casa <Casa>` e aguarde o Feca confirmar.
