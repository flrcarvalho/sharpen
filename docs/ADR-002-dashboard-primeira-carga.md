# ADR-002 — Primeira carga do Dashboard (#17): compressão agora, agregação no servidor depois

- **Status:** Quick-win **aplicado** (gzip direcionado do `/dashboard/data`, sessão 95). Trabalho **estrutural adiado** — aguarda decisão do Feca.
- **Contexto:** achado #17 (`AUDITORIA_CRITICA_2026-07-02.md`); pendência recorrente no `STATUS.md` ("dashboard lento/branco no 1º load").

---

## Contexto

O Betting Dashboard (`app/static/dash/`) é uma SPA que **baixa a base inteira** de `/dashboard/data` (um array JSON com ~toda a base de bilhetes resolvidos do dono, hoje na casa das dezenas de milhares de linhas) e faz **toda a matemática no cliente** (`app.js` → agregações por página: overview, esportes, casas, tipsters, etc.).

O caminho de carga (`loadData` em `app/static/dash/assets/js/app.js`) já é razoavelmente maduro:
- **1ª visita:** sem cache → mostra um loader calibrado (~90s) enquanto baixa e monta.
- **Visitas seguintes:** boot **instantâneo** a partir de um cache local em **IndexedDB** (`_idbGetData`) + **revalidação em 2º plano** (stale-while-revalidate) que regrava o cache.

Ou seja: o problema é **só a 1ª visita sem cache** (ou após limpar o navegador). O gargalo dominante é a **transferência do JSON grande**; a agregação no cliente é secundária para o volume atual.

## Decisão

### Fase 1 — Quick-win (FEITO, sessão 95): compressão direcionada

Comprimir com **gzip apenas a resposta de `/dashboard/data`** (`app/main.py`), quando o cliente aceitar (`Accept-Encoding: gzip`, que todo navegador manda) e o corpo passar de 1 KB:

- JSON é altamente compressível → **~85-90% menos bytes** transferidos na 1ª carga (medido ~99% em amostra sintética repetitiva; real menor, mas grande).
- O navegador **descomprime transparente**; nenhuma mudança no front (`await res.json()` continua igual).
- **Por que não `GZipMiddleware` global:** o app usa **SSE** (`StreamingResponse` com `yield data:` + keepalive) na extração; um middleware global bufferizaria/atrapalharia esses streams. A compressão pontual numa **resposta única** não tem esse risco.

Custo/risco: ~irrelevante (compressão em memória de um payload já materializado; CPU trivial). Reversível (deletar o bloco → volta ao `Response` cru).

### Fase 2 — Estrutural (ADIADO, precisa de decisão)

O quick-win ataca a transferência, mas **não** muda o modelo "baixa tudo + agrega no cliente", que não escala indefinidamente (o payload cresce linearmente com a base; um dia o parse/aggregate no cliente também pesa). Opções, do menor ao maior esforço:

| Opção | O que é | Ganho | Custo/risco |
|---|---|---|---|
| **A. Enxugar colunas** | Mandar em `/dashboard/data` só os campos que o dashboard consome (hoje manda o dict completo do `dashboard_rows`) | Menos bytes (soma com o gzip) | Baixo — mas exige auditar **cada** campo que o cliente lê antes de cortar |
| **B. Payload colunar** | Trocar `[{data,esporte,…}, …]` por colunas paralelas (`{data:[…], esporte:[…]}`) ou tabela+dicionário | Menos bytes (tira a repetição das chaves) + parse mais rápido | Médio — reescreve o `normalizeDados` do front |
| **C. Agregação no servidor** | Mover a matemática pra SQL/Python; servir **por página** já agregado (overview, esportes, …) em vez do array cru | Grande — 1ª carga deixa de depender do tamanho da base | **Alto** — reescreve o núcleo do dashboard (toda a matemática client-side migra); muda o contrato `/dashboard/data`; perde o modo offline/IndexedDB atual |
| **D. Materialized views** | Pré-agregar no Postgres (views materializadas atualizadas por gatilho/cron) | Grande — consultas de página viram lookups | Alto — infra nova (refresh, invalidação); só compensa depois de C |

## Recomendação

1. **Fase 1 (gzip)** — já aplicada; **validar no deploy** se a 1ª carga sem cache ficou visivelmente mais rápida.
2. **Medir antes de investir na Fase 2:** com o gzip, reavaliar se a 1ª carga ainda incomoda no volume atual. Se o gargalo virar o **parse/aggregate no cliente** (não mais a rede), ir por **B** (colunar) antes de **C**. Se a base crescer a ponto de a transferência pesar mesmo comprimida, aí sim **C** (agregação no servidor) é o caminho.
3. **Não fazer C/D "no escuro"** — é reescrita do núcleo; abrir plano próprio com o Feca (espelhando o rigor do ADR-001), e só depois de a Fase 1 estar validada.

## Gate de execução (Fase 2)

Só começar a Fase 2 **depois** de:
1. Fase 1 (gzip) validada em produção;
2. uma medição real (base atual, rede real) mostrando que a 1ª carga **ainda** incomoda após o gzip;
3. decisão explícita do Feca sobre qual opção (B → C → D), com janela para a reescrita.

## Consequências

- **Agora:** 1ª carga sem cache muito mais leve (rede), sem mexer no modelo nem no front; SSE intocado.
- **Preservado:** cache IndexedDB + stale-while-revalidate (boot instantâneo nas visitas seguintes) seguem iguais.
- **Aberto:** o modelo "baixa tudo + agrega no cliente" continua; escala por ora, mas tem teto — endereçado pela Fase 2 quando/se a medição justificar.
