# Matriz de Confiabilidade das Casas — Planilhador (FDC Capital)

> Documento de leitura. Classifica cada casa por **prontidão de extração**, com base
> exclusivamente nas pendências (TODOs / "aguarda amostra" / ⚠) abertas nos próprios
> manuais em `casas/CASA_*.md`. Não altera nenhuma regra — é um espelho do estado atual.

---

## A distinção central: cálculo é global, localização é da casa

A regra de **cálculo** (como cashout, void, HW/HL e boost viram odd e resultado) é
**global** — vive em `global/MASTER_RESULTADO_2026.md §5` e §6, é idêntica para todas as
casas e já está fechada. O arquivo de casa **não recalcula nada**: ele só **traduz o rótulo**
daquele mercado/desfecho na interface daquela casa específica (onde a Superbet escreve
`PRÊMIO`, a Bet365 escreve `Retorno Obtido`, a Betfair escreve `Ganhos`, etc.).

Consequência prática para esta matriz:

- Uma pendência de **localização** (ex.: "ainda não vi como esta casa rotula um cashout")
  **não corrompe o P/L** dos bilhetes já extraídos. O motor de cálculo continua correto.
  O que ela deixa incerto é a **extração daquele caso específico** — quando um bilhete
  daquele tipo (um cashout, uma freebet, uma meia-liquidação) aparecer pela primeira vez,
  pode não ser reconhecido corretamente até termos uma amostra real para fixar o rótulo.
- **Nenhuma** casa nesta matriz tem pendência de **cálculo**. Todas as pendências abaixo são
  de localização/amostra. Ou seja: os números já processados estão certos; o risco é de
  **cobertura futura** de cenários ainda não observados.

### Os três status

| Status | Significado |
|---|---|
| **Pronta** | Sem pendências abertas relevantes. Boost/void/cashout/bônus resolvidos ou declarados inexistentes. |
| **Parcial** | Casa madura, fluxo principal (W/L/V) confirmado por goldens. Restam lacunas de **localização** de rótulos de borda. Cálculo não afetado; só a extração daquele caso específico fica incerta até haver amostra. |
| **Precisa-amostra** | Cenários inteiros (cashout, boost, bônus e/ou V/HW/HL) **nunca observados** — o próprio manual os marca como "aguarda amostra". Baixo volume ou casa recém-cadastrada. As regras globais cobrem o cálculo quando o caso surgir; falta só o localizador. |

---

## Tabela-resumo

| Casa | Status | Nº pendências | Temas |
|---|---|---|---|
| Betfair | **Pronta** | 0 | — |
| Superbet | **Parcial** | 3 | void (HW/HL), cashout, freebet/bônus |
| Bet365 | **Parcial** | 3 | boost, cashout, freebet/bônus |
| Betano | **Parcial** | 3 | void, boost, freebet/bônus |
| Pinnacle | **Parcial** | 2 | void (HW/HL), freebet/bônus |
| KTO | **Precisa-amostra** | 3 | void, cashout, freebet/bônus |
| Betnacional | **Precisa-amostra** | 3 | void, cashout, freebet/bônus |
| Bolsa de Aposta | **Precisa-amostra** | 3 | boost, cashout, freebet/bônus |
| Jogo de Ouro | **Precisa-amostra** | 3 | void/HW/HL, cashout, freebet/bônus |
| KingPanda | **Precisa-amostra** | 4 | void (V/HW/HL), boost (rótulo), cashout, freebet/bônus |
| Lottu | **Precisa-amostra** | 4 | void (V/HW/HL), boost (individual), cashout, freebet/bônus |
| Vitória Bet | **Precisa-amostra** | 4 | void (V/HW/HL), boost, cashout, freebet/bônus |
| Polymarket | **Pronta (à parte)** | 0 | — casa por API, sem extração por IA |

**Contagem:** 1 Pronta · 4 Parcial · 7 Precisa-amostra · 1 à parte (Polymarket).

---

## Detalhe por casa

### Betfair — Pronta
Nenhuma pendência aberta.
- **Boost:** declarado inexistente — a Betfair Sportsbook não tem boost/promoção; a odd exibida é autoritativa (`CASA_BETFAIR.md:87`).
- **Cashout:** localizado e documentado com exemplo (`Total de Cash Out: R$X`; ex. dupla `0001532`) (`CASA_BETFAIR.md:91-95`).
- **Bônus:** política **decidida** — incluídos no fluxo normal, com o extrato separando colunas de bônus para filtro (`CASA_BETFAIR.md:99-106`, `215`).
- Observação: o cabeçalho do manual ainda diz "QUASE COMPLETO", mas não há TODO em aberto no arquivo. A pegadinha da colisão de código (`V` visual da Betfair = W nosso) está **documentada**, não é pendência.

### Superbet — Parcial
Fluxo principal e boost confirmados por goldens; restam rótulos de borda.
- **Void / HW/HL:** `<!-- TODO -->` como a casa sinaliza HW/HL (meia ganha/perdida); não apareceu em nenhum golden (`CASA_SUPERBET.md:81`).
- **Cashout parcial:** `<!-- TODO -->` onde exibe cashout de encerramento antecipado e com qual rótulo; não apareceu nos 8 bilhetes enviados (`CASA_SUPERBET.md:99`).
- **Freebet/bônus:** `<!-- TODO -->` confirmar se opera com bônus/freebets e a política; sem amostra (`CASA_SUPERBET.md:105`).
- Boost **resolvido**: `PRÊMIO ÷ Stake` já embute o boost (`CASA_SUPERBET.md:87-91`).

### Bet365 — Parcial
`Retorno Obtido` é campo financeiro único e resolve todos os desfechos; faltam só rótulos visuais.
- **Boost:** `<!-- TODO -->` confirmar o rótulo visual do boost ("Bet Boost"/"Aumento"); o cálculo já funciona via `Retorno Obtido ÷ Aposta` (`CASA_BET365.md:103`).
- **Cashout:** `<!-- TODO -->` confirmar o rótulo num bilhete encerrado real; regra e cálculo já definidos (`CASA_BET365.md:116`).
- **Freebet/bônus:** `<!-- TODO -->` confirmar se opera e a política; sem amostra (`CASA_BET365.md:122`).

### Betano — Parcial
`Ganhos ÷ Aposta` resolve W e cashout; faltam rótulos.
- **Void/anulada:** `<!-- TODO -->` rótulo de void/anulada liquidado (só apareceu "Anulado se..." como condição, não como resultado) (`CASA_BETANO.md:72`).
- **Boost:** `<!-- TODO -->` a Betano tem boost? como sinaliza? sem amostra (`CASA_BETANO.md:78`).
- **Freebet/bônus:** `<!-- TODO -->` confirmar se opera e a política; sem amostra (`CASA_BETANO.md:92`).

### Pinnacle — Parcial
Boost e cashout **resolvidos por ausência** (a casa não tem nenhum dos dois); restam duas lacunas.
- **HW/HL:** `<!-- TODO -->` confirmar o rótulo exato do export numa linha quarter liquidada (só apareceram Ganho/Perdeu cheios) (`CASA_PINNACLE.md:111`).
- **Freebet/bônus:** `<!-- TODO -->` confirmar se opera e a política; sem amostra (`CASA_PINNACLE.md:129`).
- Boost inexistente (`:117`), cashout inexistente (`:123`) — não são pendências.

### KTO — Precisa-amostra
Boost (`ODDÃO+`) confirmado; três cenários aguardam bilhete real.
- **Void:** rótulo de void/anulada **não confirmado** (`CASA_KTO.md:92`).
- **Cashout:** `<!-- TODO -->` não confirmado, aguarda amostra (`CASA_KTO.md:118`).
- **Freebet/bônus:** `<!-- TODO -->` não confirmado, aguarda amostra (`CASA_KTO.md:127`).

### Betnacional — Precisa-amostra
Boost ("Super Odds") confirmado; void detectado por assinatura financeira (sem rótulo explícito).
- **Void:** sem rótulo explícito confirmado no Histórico — hoje detectado por `Retorno = Aposta` (`CASA_BETNACIONAL.md:246`).
- **Cashout:** `<!-- TODO -->` aguarda amostra (`CASA_BETNACIONAL.md:154`).
- **Freebet/bônus:** `<!-- TODO -->` aguarda amostra (`CASA_BETNACIONAL.md:163`).

### Bolsa de Aposta — Precisa-amostra
Exchange; odd exibida bate com o retorno real nas amostras.
- **Boost:** `<!-- TODO -->` confirmar se algum mercado exibe odd decorativa ≠ retorno real; até agora sem discrepância (`CASA_BOLSADEAPOSTA.md:115`).
- **Cashout:** `<!-- TODO -->` aguarda amostra do localizador (`CASA_BOLSADEAPOSTA.md:124`).
- **Freebet/bônus:** `<!-- TODO -->` aguarda amostra (`CASA_BOLSADEAPOSTA.md:133`).
- Nota extra (não contada): confirmar se a exchange cobra comissão sobre L/P positivo (`CASA_BOLSADEAPOSTA.md:333`).

### Jogo de Ouro — Precisa-amostra
Boost ("ODDS DE OURO", formato `>>`) confirmado; a aba `Cashout` existe mas o rótulo do card não foi visto.
- **Cashout / V/HW/HL:** `<!-- TODO -->` confirmar rótulo do card na aba Cashout e de V/HW/HL com amostras reais (`CASA_JOGODEOURO.md:124`).
- **Cashout (card encerrado):** `<!-- TODO -->` confirmar rótulo visual do card e onde aparece o valor recebido (`CASA_JOGODEOURO.md:146`).
- **Freebet/bônus:** `<!-- TODO -->` aguarda amostra (`CASA_JOGODEOURO.md:155`).

### KingPanda — Precisa-amostra
Boost (formato `>>`) confirmado no cálculo; falta o rótulo visual explícito e três cenários.
- **Void / V/HW/HL:** `<!-- TODO -->` confirmar rótulo de void/reembolso e de HW/HL com amostras (`CASA_KINGPANDA.md:156`).
- **Boost (rótulo):** `<!-- TODO -->` verificar se há rótulo visual explícito de "boost" além do `>>` (o cálculo já captura) (`CASA_KINGPANDA.md:168`).
- **Cashout:** `<!-- TODO -->` **não confirmado**, aguarda amostra (`CASA_KINGPANDA.md:176`).
- **Freebet/bônus:** **não confirmado** — aba "Meus Bônus" existe; política pendente (`CASA_KINGPANDA.md:185`).

### Lottu — Precisa-amostra
Campanhas de marketing ("Odds Turbinadas", "MEGA ODDS") já identificadas como ruído (≠ boost por bilhete); cenários de borda sem amostra.
- **Boost individual:** `<!-- TODO -->` confirmar se existe boost por bilhete (odd exibida ≠ `Retorno ÷ Stake`); nas amostras bate exato (`CASA_LOTTU.md:106`).
- **Cashout:** `<!-- TODO -->` aguarda amostra do localizador (`CASA_LOTTU.md:116`).
- **Freebet/bônus:** `<!-- TODO -->` aguarda amostra (`CASA_LOTTU.md:125`).
- V/HW/HL sem amostra na tabela de status (`CASA_LOTTU.md:86-88`).

### Vitória Bet — Precisa-amostra
Casa **low-volume**, v1 com 6 goldens reais (03/07/2026); só W e L observados.
- **Boost:** `<!-- TODO -->` não confirmado, aguarda amostra (`CASA_VITORIABET.md:104`).
- **Cashout:** `<!-- TODO -->` não confirmado, aguarda amostra (`CASA_VITORIABET.md:113`).
- **Freebet/bônus:** `<!-- TODO -->` não confirmado, aguarda amostra (`CASA_VITORIABET.md:122`).
- V/HW/HL e W-simples também sem amostra — o manual registra que **não bloqueiam** (regras globais cobrem) (`CASA_VITORIABET.md:213`, `303`).

### Polymarket — à parte (Pronta por natureza)
Não entra na mesma régua: é casa **por API**, não por extração de IA. O retorno é o resgate
on-chain real (USDC) — não há boost, não há bônus, e o cashout é venda de posição no book,
tudo determinístico (`CASA_POLYMARKET.md:66-82`). Sem pendências de localização.

---

## Nota final — o que NÃO prometer como "100% coberto" ao cliente

Podem ser apresentadas como cobertura madura e confiável (fluxo principal validado, sem
lacuna relevante): **Betfair**, **Pinnacle**, **Superbet**, **Bet365**, **Betano** — e
**Polymarket** (determinística por API).

**Não** devem ser prometidas como "100% cobertas" até fechar as pendências as sete casas em
**Precisa-amostra**: **KTO, Betnacional, Bolsa de Aposta, Jogo de Ouro, KingPanda, Lottu e
Vitória Bet**. O que já foi processado nelas está correto (o cálculo é global), mas há
cenários — sobretudo **cashout** e **freebet/bônus**, e em algumas o rótulo de **void/HW/HL**
— que ainda **nunca foram vistos em bilhete real**. O primeiro bilhete desses tipos pode não
ser extraído corretamente até fixarmos o rótulo com uma amostra. Vitória Bet, KingPanda e
Lottu são as mais expostas (4 temas em aberto cada).

Reforço da distinção: essa incerteza é de **cobertura de extração**, não de **exatidão de
cálculo**. Nenhuma casa tem pendência que corrompa o P/L do que já está no banco.

---

_Data: 2026-07-03. Fonte das pendências: os próprios manuais em `casas/CASA_*.md`_
_(comentários `<!-- TODO -->`, marcações "aguarda amostra"/"não confirmado" e ⚠).
CASA_MODELO.md é template e foi excluído; CASA_POLYMARKET.md é casa por API, tratada à parte._
