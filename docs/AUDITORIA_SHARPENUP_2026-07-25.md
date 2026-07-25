# Auditoria do SharpenUp — 2026-07-25 (sessão 194)

> **Pedido:** *"toda vez que criamos uma casa nova temos dificuldade… o que mais falta é
> padrão."* Esta auditoria varre a captura ponta a ponta, mede a dificuldade, nomeia a causa
> e entrega o padrão que faltava.
>
> **Escopo:** `extensor/` (12 arquivos, ~4.100 linhas de JS), `app/captura.py`, o caminho de
> captura em `app/main.py` / `app/repository.py`, os registros de casa nos fronts, e o
> processo (docs + skills). Leitura integral do código, não amostragem.

---

## 1. Veredito

O sistema **funciona e é bem construído**: 7 casas capturando por API, dado exato sem OCR,
autodiagnóstico, banca de reenvio, backstop casa↔site em duas camadas. A qualidade da
engenharia por casa é alta.

O problema não é qualidade — é que **cada casa é um projeto artesanal do zero**:

| Casa | Commits até estabilizar | Sessões |
|---|---|---|
| Superbet | 8 | 1 longa |
| BETesporte | 4 | 2 |
| Betano | 3 | 2 |
| Betfair | 6 | 1 longa + backfill pendente |
| Pinnacle | 1 | 1 |
| **Bet365** | **11** | **8 (s178→s189)** |
| KTO | 3 | 3 (s190→s192, sendo 2 desperdiçadas) |

As duas sessões desperdiçadas na KTO são o retrato exato da dor:

- **s190** — backend marcou KTO como "texto". Correto, porém **incompleto**.
- **s191** — descoberto que `CASAS_CONECTAVEIS` (front) não listava KTO → **o botão
  "Conectar" nascia desabilitado e nada da s190 chegava a rodar**.
- **s192** — descoberto que o modo escolhido estava errado desde o começo: a lista da KTO
  não tem linha em branco entre cupons, então o robô de texto genérico entregava **1 bloco**
  com ~140 bilhetes e a IA perdia ~90 % em silêncio. Refeito por API (Kambi).

**Causa raiz, em uma frase:** *não existe um lugar onde esteja escrito o que uma casa
precisa para existir, nem um comando que prove que ela está completa.* O conhecimento vive
em prosa no STATUS e na memória de quem fez a casa anterior.

Três consequências mensuráveis:

1. **12 pontos de registro** espalhados por 4 camadas, nenhum verificado (§3.1).
2. **Nenhuma regressão travada**: todo harness era construído no scratchpad e descartado no
   fim da sessão. O parser da bet365 quebrou em três sessões seguidas sem nada acusar (§3.4).
3. **O guia existente cobria 4 dos 12 pontos** e nem menciona a extensão (§3.5).

---

## 2. Achados que valem dinheiro ou dado (agir)

### A1 — Bet365 está fora da conferência de cobertura · **ALTO** · não corrigido

`repository.py::codigos_do_texto` reconhece o código por quatro regexes de formato
(`repository.py:317-330`). Nenhuma casa com o formato da bet365 (`JR8714690761I`):

```
bet365      [Código: JR8714690761I]      -> *** NÃO COBERTO ***
kto         [Código: 12939510404]        -> coberto
superbet    [Código: 891F-YWE4RL]        -> coberto
betesporte  [Código: 189070937]          -> coberto
betfair     [Código: O/25146258/0001775] -> coberto
```

Sem gabarito, `conferir_cobertura` devolve `esperados: 0` e vira **no-op**. Ou seja: a
proteção criada na s179 — depois de **39 de 61 bilhetes sumirem sem erro** — está
**desligada justamente na casa de maior lote**. Um lote típico da bet365 (~110 bilhetes,
s188) vira 4 chunks de ~28 (`_MAX_CHUNKS = 4`); se um chunk responder sem o bloco
` ```tsv `, **28 bilhetes evaporam e a tela mostra "✓ N novo(s)"**.

A exclusão foi **deliberada na s178** ("robô em obra") e está congelada num teste
(`tests/test_cobertura.py:76`) — mas as s182→s189 estabilizaram o `[Código: BR…]`, e ninguém
voltou para religar o guarda. É dívida de decisão vencida, não bug de digitação.

**Correção proposta** (2 linhas + 1 teste): uma regex genérica de marcador para o caso
alfanumérico, ou `_ID_BET365_RE` explícita, adicionada **só** em `codigos_do_texto` (que
compara exato). Não tocar `corrigir_codigos_tsv`, que usa outra lista e faria *snap* por
edit-distance — comportamento diferente, assunto separado. Inverter o teste que hoje trava a
exclusão.

### A2 — Pinnacle está fora do pré-dedup · **ALTO** · não corrigido

`main.py:1741` lista `("SUPERBET", "BETESPORTE", "BETANO", "BET365", "KTO")`. **Pinnacle não
está** — apesar de o `formatTicketPN` emitir `[Código: …]` (`content.js:1103`) e de
`_dedup_superbet_text` funcionar com qualquer conteúdo no marcador (`_SUPERBET_ID_RE`,
`main.py:413`).

Efeito: **toda recaptura da Pinnacle paga IA de novo por todos os bilhetes já resolvidos no
banco** (~$0,011/bilhete). Não corrompe dado (o UPSERT por código atualiza), mas é custo e
latência puros, recorrentes. É a mesma falha que a s189 corrigiu na bet365 — sobreviveu na
Pinnacle porque ninguém tinha a lista completa dos pontos de registro.

O mesmo vale, com menos gravidade, para o chunker (`main.py:636`): sem a casa na tupla, o
texto fatia pelo fallback `\n\n` em vez do marcador `[Código:]`. Hoje funciona por
coincidência (os robôs juntam blocos com linha em branco) — mas é frágil: um bloco que
contenha linha em branco vira dois bilhetes.

**Correção proposta:** somar `"PINNACLE"` às duas tuplas. Uma linha cada.

### A3 — Comentários canônicos mentindo sobre a KTO · **BAIXO** · não corrigido

`captura.py:45-48` e `index.html:3162-3164` afirmam que a KTO é *"texto SEM injetor — o
`roboScroll` genérico cobre"*. Isso foi verdade por ~4 horas: a s192 substituiu tudo por
`kto_inject.js` + `roboKTOPassive` **exatamente porque o `roboScroll` não cobria**. Quem ler
esses comentários para criar a próxima casa vai repetir o erro que a s192 pagou para descobrir.

### A4 — `CASA_BET365.md` ensina a IA duas coisas que não existem mais · **BAIXO** · não corrigido

O arquivo vai **inteiro para o prompt** em toda extração da bet365:

- **§2, linha 32** — manda emitir na ordem dos bilhetes *"marcados por `[Bilhete Bet365]`"*.
  Esse marcador **nunca foi emitido** pelo `formatTicketB3` e foi removido do backend na s189.
- **§2** — descreve um *"fallback: DOM, raspando os cards `.myb-SettledBetItem`"*. O robô de
  DOM foi **removido na s182**.

Instrução morta no prompt não quebra nada sozinha, mas gasta contexto e induz o modelo a
procurar âncora inexistente.

### A5 — A suíte de testes está VERMELHA no `main` desde 24/07 · **ALTO** · ✅ CORRIGIDO (`61d5c8d`)

```
2 failed, 191 passed, 4 skipped
FAILED tests/test_captura.py::test_casa_de_host_desconhecido_ou_vazio_retorna_none
FAILED tests/test_ordem_bet365.py::test_build_chunks_bet365_split_por_marcador
```

Nos dois casos **o código está certo e o teste é que envelheceu**:

- `test_captura.py:22` usa `kto.bet.br` como exemplo de domínio *desconhecido* e exige
  `None`. A s190 registrou a KTO em `_HOSTS_POR_CASA` — agora devolve `'KTO'`, corretamente.
- `test_ordem_bet365.py:87` exige que o chunker fatie por `[Bilhete Bet365]`. A s189 removeu
  esse marcador **de propósito** (ele nunca foi emitido); hoje a bet365 fatia por `[Código:]`.

Gravidade não está nos dois testes — está no que isso revela: **o `ci.yml` roda `pytest` em
todo push para `main` e ninguém olhou o resultado em pelo menos duas sessões.** Enquanto o
sinal fica vermelho por ruído conhecido, ele **para de avisar quando quebrar de verdade** — e
o deploy do Railway sai no push, independente do CI. O `pre-commit` local só checa tokens de
marca, não roda teste.

**Aplicado (só `tests/`, nenhum arquivo de produção):** `kto.bet.br` e `pinnacle.bet.br` viraram
asserções **positivas** (antes estavam soltas), o exemplo de host desconhecido virou
`kingpanda.bet.br` (casa de print — com comentário fixando a regra: usar sempre casa de print
aqui, senão o teste quebra sozinho quando o robô cobrir a casa) e o teste do chunker passou a
ancorar em `[Código: BR…]`. **193 passed, 4 skipped.**

> **Pendência de DX que apareceu no caminho:** rodar `pytest` da raiz **sem** `tests/` quebra
> localmente — o pytest coleta os `test_*.py` dentro de `Backups/` e o `main.py` de um snapshot
> antigo **sombreia** o `app/main.py`, derrubando 9 coletas. No CI não acontece (`Backups/` é
> gitignored). Conserto de 3 linhas: um `pytest.ini` com `testpaths = tests` e
> `norecursedirs = Backups`. Não apliquei — muda como a suíte roda para todo mundo.

---

## 3. Achados estruturais (o "falta padrão")

### 3.1 — A superfície de registro é de 12 pontos e ninguém a verificava · **CORRIGIDO HOJE**

Uma casa de captura precisa existir em: `casas/CASA_*.md` · `_CASA_DISPLAY` · tupla do
chunker · tupla do pré-dedup · regex de código · `_MODO_POR_CASA` · `_HOSTS_POR_CASA` ·
`CASAS_CONECTAVEIS` · `NOMES`+`DOMINIOS` · 3 mapas de favicon · `popup.js` (hosts +
dispatch) · `manifest.json` (+ bump). Mais 5 lugares dentro do `content.js`.

São **listas paralelas que precisam concordar** e nada as cruzava. Foi assim que a s191
inteira se perdeu.

→ **Entregue:** `tools/audit_sharpenup.py`. Roda em <1 s e já achou A1 e A2 sozinho.

### 3.2 — `content.js` cresce ~150 linhas por casa e roda em TODA página · **não corrigido**

O `manifest.json` injeta `content.js` em `http://*/*` e `https://*/*` — **todo site que o
operador abrir** carrega e parseia 119 KB. Cada casa nova soma um ouvinte, um
`formatTicketXX` e um `roboXXPassive`: em ~20 casas, ~300 KB em toda navegação.

Além do peso, os 7 `roboXXPassive` são **o mesmo laço** com nomes trocados: pedir acumulado
→ esperar `fim` → processar com `stopId` + janela de dias → teto de inatividade. Um
`roboPassivoGenerico({chave, mapa, fimReal, formatar})` colapsaria ~450 linhas e faria a
parte de robô de uma casa nova custar ~10 linhas em vez de ~70.

O mesmo para os injects: `sb`, `be` e `bn` são **o mesmo arquivo** com quatro diferenças
(regex do endpoint, chave do bilhete, nome da mensagem, forma da lista). Um
`su_hook.js` compartilhado deixaria cada inject com ~30 linhas de específico.

> Não é refactor cosmético: **é a diferença entre casa nova custar 300 linhas ou 40**, e é
> o que decide se o volume de casas escala.

### 3.3 — Ouvintes de `message` sem checagem de origem · **MÉDIO** · não corrigido

Os 7 listeners do `content.js` (`content.js:29, 52, 77, 107, 131, 158, 191`) aceitam
qualquer mensagem com a chave certa, de qualquer frame ou script da página. Com pareamento
ativo, uma página hostil poderia postar `__sharpenupKTOData` com bilhetes forjados e eles
subiriam como apostas do usuário.

Risco prático baixo (exige pareamento ativo + o operador numa página maliciosa), conserto
barato: `if (ev.source !== window && ev.source !== window.top) return;` no topo de cada
listener — exceto onde a ponte iframe→top é intencional (bet365), que precisa de um teste
mais específico.

### 3.4 — Toda validação era descartada no fim da sessão · **CORRIGIDO HOJE**

Os harnesses de bet365 (s178) e KTO (s192) foram escritos no scratchpad e perdidos. Sem
regressão travada, o parser da bet365 quebrou três vezes seguidas (`02` lido como perna,
`04` ignorado, `TP=00010101000000` virando "01/01/0001") — cada uma descoberta ao vivo.

→ **Entregue:** `extensor/harness/` permanente, que roda o **código real** (não uma cópia)
contra payloads salvos, sem navegador. A fixture da KTO foi resgatada do scratchpad antes de
sumir. Teste de mutação feito: quebrando uma expectativa de propósito, o harness acusa.

### 3.5 — O guia de casa nova cobria 4 dos 12 pontos · **CORRIGIDO HOJE**

`docs/GUIA_NOVA_CASA.md` (de 20/06) trata só da camada de leitura e **não menciona a
extensão**. Não havia nenhum documento sobre como ligar uma casa ao SharpenUp: o
conhecimento estava em prosa no STATUS e nos comentários do código.

→ **Entregue:** `SHARPENUP_ARQUITETURA.md` (mapa) + `GUIA_CASA_SHARPENUP.md` (procedimento
em 7 fases, árvore de decisão de modo e o **livro de armadilhas** consolidado de todas as
casas) + 4 skills.

### 3.6 — Documentação da extensão desatualizada · **CORRIGIDO HOJE**

O `extensor/README.md` listava `fab.js` e `overlay.js` (arquivos que não existem), omitia os
**7 injects** e o modo texto da KTO e da Pinnacle. Reescrito.

### 3.7 — Higiene de arquivos · **parcialmente corrigido**

- `extensor/Backups/` — pasta de backup **fora do lugar** (regra #4 manda `Planilhador/Backups/`).
  Estava vazia, duplicando `Backups/kto-inject-api-2026-07-25/`. **Removida.**
- `Backups/` tem **434 pastas**. A regra #4 pede poda além de ~90 dias / últimas sessões.
  **Não podei** — apagar backup é irreversível e é decisão do Feca. Proposta em §4.

---

## 4. Próximos passos, na ordem em que eu faria

| # | O quê | Por quê | Tamanho | Risco |
|---|---|---|---|---|
| ~~1~~ | ~~**Voltar o CI ao verde** (A5)~~ | ✅ feito em `61d5c8d` | — | — |
| 2 | **Religar a cobertura da bet365** (A1) | 28 bilhetes podem sumir em silêncio hoje | 2 linhas + teste | baixo |
| 3 | **Pinnacle no pré-dedup e no chunker** (A2) | custo de IA recorrente à toa | 2 linhas | baixo |
| 4 | **Comentários e `CASA_BET365.md`** (A3, A4) | a doc canônica está ensinando errado | 4 trechos | nenhum |
| 5 | **Checagem de origem nos listeners** (3.3) | integridade do dado | 7 linhas | baixo |
| 6 | **`roboPassivoGenerico` + `su_hook.js`** (3.2) | casa nova: 300 → ~40 linhas | 1 sessão | **médio** — mexe em 7 casas que funcionam; fazer **depois** de haver caso de harness para cada uma |
| 7 | **Caso de harness para as 6 casas restantes** | pré-requisito do #5: sem regressão travada, refatorar 7 casas é apostar | 1 fixture por casa (o Feca captura no F12) | baixo |
| 8 | **Injeção por host** (`registerContentScripts`) | tirar 119 KB de toda navegação | ½ sessão | médio |
| 9 | **Podar `Backups/`** | 434 pastas; o git já guarda o versionado | decisão do Feca | irreversível |

> **#7 antes de #6.** A ordem importa: refatorar as 7 casas sem harness cobrindo cada uma
> repetiria a lição de "isolar a mudança, não quebrar o que funciona".

---

## 5. O que mudou nesta sessão (resumo)

**Novos**
- `docs/SHARPENUP_ARQUITETURA.md` — mapa da captura, contrato de mensagens, tabela das 7
  casas, os 12 pontos de registro, limites conhecidos.
- `docs/GUIA_CASA_SHARPENUP.md` — procedimento em 7 fases, árvore de decisão de modo,
  livro de armadilhas.
- `tools/audit_sharpenup.py` — gate determinístico dos 12 pontos.
- `extensor/harness/` — regressão offline permanente (sandbox + runner + caso da KTO +
  fixture real resgatada).
- Skills `/sharpenup-recon`, `/sharpenup-casa`, `/sharpenup-validar`, `/sharpenup-diagnostico`.

**Editados**
- `extensor/README.md` — reescrito (estava descrevendo arquivos inexistentes).
- `docs/GUIA_NOVA_CASA.md` — escopo explicitado + ponteiro para o guia da captura.

**Organização**
- `extensor/Backups/` removida (duplicata vazia fora do lugar).

**Nada de produção foi alterado.** `app/`, `extensor/*.js` e `manifest.json` estão intactos —
os achados A1–A4 estão propostos, não aplicados.

---

VERSÃO: 2026
ATUALIZADO: 2026-07-25 (sessão 194)
