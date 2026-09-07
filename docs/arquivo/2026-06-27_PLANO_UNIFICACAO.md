# PLANO — Unificação Planilhador + Dashboard (migração da planilha)

> Documento de plano. Rascunho vivo — refina quando o CSV limpo chegar.
> Autor: sessão de 2026-06-27. Status: **aguardando** CSV limpo + decisões do Feca (§10).

---

## 0. Veredito (resumo executivo)

Hoje existem **3 fontes de verdade**: (1) Postgres do Planilhador, (2) a planilha do
Google (`2026 Contas Pessoais`, 25.726 apostas), (3) o Dashboard (GitHub Pages + Apps
Script lendo a planilha). A planilha+Apps Script é o **hub de integração** — e é a
causa das 3 dores: copiar à mão, preencher tipster fora do app, dashboard lento/instável.

**Alvo:** Postgres vira a fonte única. O Planilhador passa a servir **a grade E o
dashboard**, na mesma origem (mesmo login). A planilha é aposentada como hub e vira só
um **destino de export CSV** (backup). O dashboard deixa de depender de Apps Script.

**Descoberta que encolhe o projeto:** o dashboard já faz **toda a matemática no cliente**
(ROI, drawdown real, Monte Carlo 10k, p-value, correlações) a partir de um array JSON
montado pelo `Code.gs`. Portanto **não há analytics para reescrever**. O Planilhador só
precisa de **um endpoint** que devolva esse mesmo array (§6). O trabalho real é: (a)
import limpo da planilha, (b) esse endpoint, (c) hospedar o dashboard na mesma origem.

**Ganho de velocidade:** real. Hoje o caminho é Sheets→Apps Script→cache no Drive (7,8 MB;
leitura ao vivo chegou a 137 s; gatilho `rebuildCache` falha por timeout quando a planilha
está suja). Servindo 25k linhas do Postgres: query + transferência em **sub-segundo a
~1 s**, sem gatilho, sem recálculo de fórmula, sem etapa de cópia. A matemática client-side
(já otimizada com Web Worker + IndexedDB + memoização) fica intacta.

---

## 1. Estado atual (mapa real)

```
[Prints] --IA--> Planilhador (Postgres)  --copia manual--> Planilha Google --AppsScript--> Cache Drive --doGet--> Dashboard (GitHub Pages)
[Polymarket] --API--> Planilhador                              (25.726 linhas, fórmulas Valor/PL/Mês/Semana)
```

- **Planilhador:** FastAPI + asyncpg + Postgres (Railway). Tabela `bilhetes`
  (dono, casa, parceiro, assinatura, codigo_bilhete, data, esporte, tipster, aposta,
  descricao, stake, odd, resultado, …). Multiusuário por `dono`. Stake/odd como **texto
  com vírgula**. Saída W·L·V·HW·HL.
- **Planilha:** 25.726 apostas reais (72k linhas no total, resto é template). 41 casas,
  64 tipsters, 99 parceiros, 23 rótulos de esporte, 92 de categoria. Colunas derivadas
  (Valor, P/L, Mês, Semana) calculadas por fórmula.
- **Dashboard (`FDC Capital/Betting Dashboard`):** produto maduro. Views: Visão Geral,
  Esportes, Casas, Tipsters, Resultados (matriz temporal), Métricas, Gestão, Apostas.
  Frontend em `assets/js/{app,overview,performance,gestao,temporal,shared,filters}.js`.
  Backend `Code.gs` (Apps Script) lê a planilha via Sheets API, monta JSON, cacheia no
  Drive, serve por `doGet`. Gatilho `rebuildCache` a cada 30 min.

---

## 2. Arquitetura-alvo

```
[Prints] --IA-----> Planilhador (Postgres = FONTE ÚNICA) --/bilhetes--> Grade (mesma app)
[Polymarket] --API-> Planilhador                          --/dashboard/data--> Dashboard (servido pela própria app, mesmo login)
                                                           --/export.csv-------> backup (abre no Excel/Sheets)
```

- **Uma app, um login, uma fonte.** Grade e dashboard convivem sob a auth da sessão 44.
- Planilha sai do caminho crítico. Apps Script + cache no Drive + gatilho: **aposentados**
  (mantidos vivos como backup até a validação — ver §8 e §9).

---

## 3. Decisões de design

| # | Decisão | Racional | Precisa do Feca? |
|---|---|---|---|
| D1 | **NÃO apagar o banco.** Import **aditivo**, tag `origem='import'`: trazer da planilha **só a era anterior à cobertura do DB** (por casa: linhas com `data` < `MIN(data)` daquela casa no DB; casas que o DB nunca viu → tudo). Polymarket fora do import. | O **Código** (chave de dedup das casas com ID) nunca foi pra planilha — só vivia no DB. Linha importada seria **codeless** → assinatura por conteúdo; re-extração futura gera Código → assinatura por **ID** → **não casa → duplicata**. Importar só a era pré-DB (congelada, nunca re-extraída) preserva 100% a dedup e mantém os Códigos recentes que a planilha descartou. | **SIM** (confirmar a era-split) |
| D2 | Adicionar `stake_num`/`odd_num`/`valor_num`/`pl_num` NUMERIC **armazenados** (não gerados). Preenchimento **por origem**: import (era antiga) e backfill (era recente) → carregam o **P/L da planilha** direto; extração/sync novos → calculam da **odd cheia**. | **Achado da auditoria (harness v0):** recalcular o P/L pela odd da planilha diverge **R$ 319,58 em 1.678 linhas** — a planilha arredonda a odd a 2 casas mas o P/L usa a odd cheia (sessão 50). Logo a coluna P/L da planilha é a verdade para o histórico; coluna gerada recalcularia errado. | não (eu decido) |
| D3 | Dashboard **servido pela própria app** (mesma origem) + **um endpoint** que replica o contrato do `Code.gs`. **Zero reescrita de analytics.** | Mesma origem = o cookie de login funciona (GitHub Pages é cross-origin e o cookie não iria). A matemática é toda client-side; só falta a fonte de dados. | não |
| D4 | Backup = **botão "Exportar base (CSV)"** + backups automáticos do Postgres no Railway. **NÃO** escrever de volta no Sheets. | Escrever no Google exige OAuth, é caminho de escrita frágil e reintroduz a planilha como dependência. CSV é pull, não corrompe. | não |
| D5 | Casas offline: registrar **só o nome** (display/armazenamento), sem manual de extração. Parceiros: import em massa; arquivar os inativos. | Manual só é preciso pra extrair print; dado importado já vem estruturado. | **SIM** (regra de "inativo") |
| D6 | `Múltiplos` vira **esporte canônico** no `MASTER_ESPORTES` + regra "múltipla multi-esporte → Esporte = Múltiplos". | A planilha já usa isso em 2.753 linhas; precisa existir na taxonomia. | não (mas confirmo a regra) |
| D7 | Limpeza via **tabelas de-para no script**, não editando 25k linhas à mão. | Auditável, re-rodável, não mexe na planilha viva. Humano só decide ~40 mapeamentos + revê exceções. | parcial (aprovar de-para) |

---

## 4. Modelo de dados (mudanças no `bilhetes`)

Migração **idempotente** (`ADD COLUMN IF NOT EXISTS` + bloco `DO`):

- `origem TEXT NOT NULL DEFAULT 'extracao'` — valores `extracao | sync | import`.
- `stake_num NUMERIC` , `odd_num NUMERIC` — preenchidos em **todo** caminho de escrita
  (import, extração, sync), parseando a vírgula. As colunas de texto seguem para display.
- `valor_num NUMERIC` , `pl_num NUMERIC` — **armazenados** (não gerados). Import/backfill
  carregam o **P/L da planilha**; extração/sync calculam da **odd cheia**. (Ver achado da
  auditoria: a odd da planilha é arredondada → recalcular daria R$ 319 de erro.)

**Função de resultado (espelha a planilha, validada contra K/L):**

```
Valor = SWITCH(resultado):
  W  -> stake * odd
  L  -> 0
  V  -> stake
  HW -> (stake/2)*odd + stake/2
  HL -> stake/2
  (aberta / "-") -> NULL
P/L = Valor - stake   (quando Valor não é NULL)
```

---

## 5. O ETL (script de import — "Extract, Transform, Load")

Um script Python, rodado **uma vez**, re-rodável:

1. **Extract** — lê o CSV/xlsx limpo (aba `DB Apostas`).
2. **Transform:**
   - de-para de **esporte** (~7 decisões), **casa** (~2 merges), **categoria**
     (~25 óbvias + ~12 merges + 3 a decidir, §10).
   - resultado: limpar `w`→`W`, descartar `None`/inválidos.
   - parceiro `"nome [fornecedor]"` → `conta` + `fornecedor` (mesmo regex do `Code.gs`).
   - data → ISO; stake/odd → NUMERIC (vírgula/ponto).
   - **recalcular `valor`/`pl` e dar diff contra as colunas K/L** → prova de correção;
     linhas divergentes entram num relatório pra revisão (pega lixo na fonte).
3. **Load (era-split, roda contra prod — gatilho do Feca):** por casa, `MIN(data)` no DB
   define o corte; inserir em lote só as linhas da planilha com `data < corte` (casas
   ausentes do DB → todas), `origem='import'`, codeless. **Nunca tocar** em
   `origem IN ('extracao','sync')` — os bilhetes recentes COM Código ficam intactos
   (dedup preservada). Idempotente: re-run apaga só `origem='import'` e reinsere.
   - **`criado_em` do bloco import (lição da sessão 62):** a lista ordena por `criado_em DESC`.
     Se o import deixar o default `NOW()`, todo o bloco sobe ao TOPO, na frente das extrações
     reais. Carimbar `criado_em` abaixo do corte `T_min` (= `MIN(criado_em)` das linhas
     `origem IN ('extracao','sync')` do mesmo dono), ordenado pela data real desc:
     `criado_em = (T_min − 1min) − (data_max_import − data_da_linha)`. Assim o bloco vai pro
     fim, ordenado cronologicamente por dentro, sem se intrometer nas extrações.
4. **Saída:** relatório (linhas importadas, rejeitadas, diffs de P/L, valores não-mapeados).

---

## 6. Integração do dashboard (o contrato, exato)

O `Code.gs.getData()` devolve um array onde **cada linha** é:

```json
{ "data":"YYYY-MM-DD", "esporte":"", "tipster":"", "casa":"", "parceiro":"",
  "conta":"", "fornecedor":"", "aposta":"", "descricao":"", "stake":0.0,
  "odd":0.0, "resultado":"W", "lucro":0.0 }
```

e o `doGet` embrulha em `{ ok:true, data:[...], builtAt:ISO, count:N }`.

**Plano:**
- Nova rota **`GET /dashboard/data`** no Planilhador → devolve **exatamente** esse
  envelope, montado do Postgres, **filtrado por `dono`** (login). `lucro` = `pl_num`;
  `stake`/`odd` numéricos; `conta`/`fornecedor` derivados do parceiro.
- **Hospedar** os estáticos do dashboard dentro da app (rota autenticada). No `loadData`
  do front, trocar a URL do Apps Script pela rota same-origin. **Nada mais muda** —
  IndexedDB, Web Worker, memoização e todas as views seguem iguais.
- Aposentar Apps Script + cache no Drive + gatilho (mantидos como backup até validar).

> Filtro de resultado do dashboard hoje: só `W/L/V/HW/HL` com `stake>0` e `lucro` numérico.
> O endpoint deve respeitar o mesmo (apostas abertas, `pl_num` NULL, ficam de fora — como já é).

---

## 7. Expectativa de velocidade (honesta)

- **Hoje:** cache no Drive ~4 s no caminho feliz; leitura ao vivo já mediu 137 s; o
  gatilho falhava ~7% das vezes por timeout (planilha suja). Mais a etapa manual de cópia
  e a defasagem de até 30 min.
- **Depois:** servir 25k linhas do Postgres é uma query simples + ~3–5 MB de JSON →
  ordem de **sub-segundo a ~1 s**. Sem gatilho, sem recálculo, sem cópia, **ao vivo**.
- A matemática client-side não muda de custo (já era no browser). O ganho percebido vem
  de matar a camada Sheets/Apps Script e a cópia manual.

---

## 8. Fases e sequência

| Fase | Entrega | Depende de |
|---|---|---|
| **A** | Schema (§4) + carregar P/L da planilha + canônicos `Múltiplos`/`Handebol` + **harness de auditoria** (§11) + **botão Export base CSV** (backup, D4). Sem tocar em dado existente. | nada |
| **B** | ETL de import (§5). | CSV limpo + de-para aprovado + "Peixe"/"HPC"/Over-Under resolvidos (§10) |
| **C** | Endpoint `/dashboard/data` + dashboard hospedado same-origin + cutover do `loadData`. | A, B |
| **D** | Botão Export CSV (backup) + aposentar Apps Script (mantém vivo até validar). | C |

> Regra do projeto: uma mudança por vez, propor → confirmar → executar, backup antes de
> editar, commit+push juntos, atualizar STATUS ao fim.

---

## 9. Riscos e rollback

- **Sem apagar dados (D1):** import é **aditivo** (só a era pré-DB). Bilhetes com Código
  (recentes) ficam intactos → **dedup preservada**. Antes de importar, comparar contagem
  planilha vs DB na janela de sobreposição (pega bets digitadas direto na planilha).
- **Cutover do dashboard:** manter Apps Script + planilha **vivos** até o dashboard
  same-origin ser validado lado a lado (mesmos números). Reverter = apontar o `loadData`
  de volta pra URL do Apps Script.
- **Qualidade de dados:** o diff contra K/L na fase B é a rede de segurança — import
  rápido e *errado* é pior que planilha lenta e certa. Não pular essa validação.
- **Polymarket:** fora do import (D1). Continua via API/sync, com o dashboard ao vivo já
  existente na grade.

---

## 11. Harness de auditoria (erro ZERO)

Regressão por agregados, além do diff linha-a-linha. Mesmo código roda sobre **duas
fontes** (planilha = golden · endpoint do Planilhador) e dá diff.

- **Golden (planilha, harness v0 — 25.708 bets válidas):** P/L R$ 288.921,33 · ROI 4,85%
  · turnover R$ 5.956.595 · odd média ponderada 10,80 · W/L/V/HW/HL = 8016/16132/1470/50/40.
  Reproduz o dashboard (sessão 46: R$ 289.223 / 4,86%, com 2 dias a menos). Método validado.
- **Definições espelham o dashboard:** turnover e ROI **excluem Void**; odd média
  ponderada `Σ(odd·stake)/Σ(stake)` com odd>0 & stake>0; win rate sobre não-Void; P/L = coluna L.
- **Dimensões que devem bater CENTAVO a centavo** (invariantes ao de-para de esporte/categoria
  e ao backfill): **total geral · por casa · por tipster · por mês/semana**.
- **Esporte e categoria** mudam de bucket pelo de-para → validados pela soma dos buckets
  remapeados (não por igualdade crua).
- **Gate:** Fase B só fecha quando o diff golden × Planilhador = **0** em todas as
  dimensões invariantes.

---

## 10. Perguntas abertas (Feca)

1. **"Peixe"** (584 linhas: esporte/tipster/aposta = Peixe) — o que é? (você disse que
   trata à parte na fonte).
2. **"HPC"** (categoria, 106 linhas) — o que é?
3. **`Over` (376) + `Under` (187)** — não são categorias nossas. Mapeio grosso para
   `Player Props` ou jogo em `Outras`?
4. **Regra de "parceiro inativo"** para arquivar em massa: por data da última aposta
   (ex.: > 60 dias) ou você me passa a lista de ativos?
5. **`Handebol`/`Handeball`** (2 linhas) — vira esporte canônico `Handebol` ou `Outro`?
6. **Confirmar a era-split** (D1): manter o banco (bilhetes recentes com Código) e importar
   da planilha **só a era anterior à cobertura do DB** — preserva a dedup. (Substitui o
   antigo clean-slate, que quebraria a dedup.)
