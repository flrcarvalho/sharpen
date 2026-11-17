# Auditoria independente: estado e cache do LADO SERVIDOR (Sharpen)

Data: 17/11/2026 · Escopo: `app/` (FastAPI + asyncpg), Dockerfile, railway.toml, e os pontos
onde o servidor conversa com o cache do cliente/extensão. Somente leitura: nada no repo foi
editado, nenhum banco foi tocado (os scripts forçam `DATABASE_URL` para um endereço inexistente).

Provas reexecutáveis em `...\scratchpad\aud_servidor\provas\` (rodar `python pN_*.py` de dentro
da pasta). Cada uma importa o **código real** de `app/` e dubla só o banco/rede.

Legenda: **COMPROVADO** = reproduzido com o código real (diz como) · **HIPÓTESE** = leitura
estática, sem reprodução.

---

## 0. Resumo executivo: a causa sistêmica

O servidor tem **um processo só** (Dockerfile: `uvicorn main:app` sem `--workers`; railway.toml
sem réplicas declaradas) e é **reimplantado várias vezes por dia** (113 commits entre 17/10 e
17/11, todos com push = deploy automático; 12 só em 11/11). Três padrões se repetem e explicam
por que os "problemas de cache" voltam depois de corrigidos:

1. **Estado de sessão e de fila mora na memória do processo** (`captura._SESSOES`, a fila de
   capturas, os contadores de rate-limit, `_termo_novo`, `aviso_diario._falhas`). Cada deploy
   apaga tudo isso **sem aviso**. Para o usuário frequente, a extensão "desconecta sozinha"
   3-4 vezes por dia e ele tem de parear de novo. Capturas que estavam na fila somem.
2. **Cache sem versão, com "o último a escrever vence"**: os caches leem um snapshot e
   **substituem** o estado inteiro, sem comparar idade. Uma leitura antiga pode gravar por
   cima de uma recarga nova (P1, comprovado). Falhas também ficam em cache, como se fossem
   sucesso (P5, P9).
3. **A invalidação é manual, rota por rota**: cada escrita precisa "lembrar" de derrubar o
   cache certo (`matcher.invalidar`, `atualizar_cache_usuarios`, `?v=` no HTML, `bloco_visto`
   com `atualizado_em`). Quem esquece não dá erro, só deixa o dado velho: 3 rotas de rótulo
   não invalidam o matcher (P6), e 20+ commits mudaram `data.js` sem trocar o `?v=` (P8).
   Os marcadores persistentes de "já processado" (`bloco_visto`, pular resolvidos, o
   `cruEnviado` da extensão, o congelamento do UPSERT) provam a persistência por um carimbo
   genérico (`atualizado_em`) que **qualquer outra escrita renova**.

A correção estrutural é a mesma para as três famílias: **estado que precisa sobreviver vai
para o Postgres**, cache em memória vira **otimização opcional com versão** (`xmin`, contador
de geração, `updated_at` monotônico) e a **invalidação sai das rotas** para um ponto só, de
preferência o próprio banco (trigger + `NOTIFY` com o nome do cache, como já existe para
`bilhetes`).

---

## 1. Topologia de execução (o que vale para todos os achados)

| Item | Medido | Fonte |
|---|---|---|
| Processos | 1 (uvicorn sem `--workers`) | `Dockerfile:25` |
| Réplicas | nenhuma declarada em `railway.toml`; o painel da Railway não foi conferido | `railway.toml` |
| Deploy | sobreposição curta: o container antigo serve até o `/healthz` do novo responder (até 300 s) | `railway.toml` |
| Frequência de deploy | 113 commits/31 dias (mediana de 3-6 por dia útil) | `git log --since=2026-10-17` |
| Pool | asyncpg, `max_size=5`, `max_inactive_connection_lifetime=60` | `database.py:1185-1194` |

Consequência: hoje não existe incoerência **entre** workers. Existe incoerência **no tempo**:
todo estado de memória morre a cada deploy, e por alguns segundos dois processos com memórias
diferentes servem ao mesmo tempo. Qualquer passo para "SaaS escalável" (2 workers ou 2
réplicas) quebra **na hora** pelo menos: identidade (até 60 s de logout ao trocar senha),
pareamento da extensão (a sessão existe em um processo só), `virada._em_voo` (espera do cru) e
a reserva do vigia (`virada._vigia_reservas`).

---

## 2. TABELA-INVENTÁRIO

Chave "dono?" = a chave inclui o usuário. "Invalida" = quem derruba antes do TTL.

### 2.1 Variáveis de módulo mutáveis

| # | Onde | Guarda | Chave (dono?) | TTL | Invalida | Toda escrita invalida? | Restart/deploy | >1 processo |
|---|---|---|---|---|---|---|---|---|
| 1 | `auth._usuarios_cache` (`auth.py:197`) | usuários: hash, status, papel, operador, e-mail, bot | username (sim) | 60 s (refresher) | rotas de senha/e-mail/admin/signup chamam `atualizar_cache_usuarios` | sim, mas **corrida**: refresher com snapshot velho sobrescreve (P1) | recarrega do banco no boot | diverge até 60 s |
| 2 | `captura._SESSOES` (`captura.py:388`) | pareamento extensão↔dashboard, token, **fila de capturas** (até 60, imagens em base64) | sessao_id/token; `dono` dentro | 6 h de inatividade | `encerrar`, prune | n/a | **apaga tudo** (P3) | sessão só existe num processo |
| 3 | `virada._em_voo`, `_ultimo_fim` (`virada.py:89-90`) | cru em processamento por (dono, casa) | sim | não | `cru_saiu` (try/finally) | sim | zera | quebra a espera |
| 4 | `virada._vigia_reservas` (`virada.py:871`) | reserva do vigia por (casa, semana) | não (casa) | nunca expira | `vigia_soltar` só em falha | n/a | zera: vigia pode rodar 2× na semana | 2 reservas |
| 5 | `virada._termo_novo` (`virada.py:1034`) | "rodar semente logo depois" | sim | não | `tomar_termo_novo` | n/a | perde o pedido (fica para as 04h) | – |
| 6 | `dicionario._familias` (`dicionario.py:274`) | mapa família→casas | global | 600 s | ninguém | não | recarrega | – |
| 7 | `dicionario._semeando/_de_novo` | trava da semente | global | – | – | – | zera | 2 sementes simultâneas na sobreposição de deploy |
| 8 | `repository._CATEGORIAS_DONO` (`repository.py:468`) | categorias válidas do dono no leitor | sim | 600 s | **ninguém** | não; e **guarda a falha** (P5) | recarrega | – |
| 9 | `matcher._CACHE` (`matcher.py:140`) | modelo de sugestão de tipster | sim | 300 s | 4 rotas chamam `invalidar` | **não**: `/bilhetes/tipster`, `DELETE /bilhetes`, `/bilhetes/restaurar`, `/salvar` não invalidam (P6) | recarrega | – |
| 10 | `planilha_viva._cache` (`planilha_viva.py:26`) | feed da planilha Google do dono | sim | 120 s | `refresh=1` | – | recarrega | – |
| 11 | `main._publico_data_cache` (`main.py:6733`) | feed público do tipster (json+gzip) | slug | 300 s | nenhuma (refresh ignorado de propósito) | não | recarrega | – |
| 12 | `metricas_publicas._cache` | contadores da landing | global | 30 s | – | – | – | – |
| 13 | `main._changelog_cache` (`main.py:3219`) | changelog.json | global | mtime | mtime | sim | – | – |
| 14 | `prompts._file_cache` | MASTERs/casas em disco | caminho | mtime | mtime | sim | – | – |
| 15 | `taxonomia.esportes_canonicos/categorias_canonicas` (`lru_cache`) | listas do MASTER | global | vida do processo | só deploy | arquivo só muda com deploy: ok | – | – |
| 16 | `descricao_ficha._VOCAB_MASTER` | vocabulário do MASTER | global | vida do processo | – | ok (idem) | – | – |
| 17 | `polymarket._PTAX_MAPA/_PTAX_DE/_PTAX_ATE` (`polymarket.py:228`) | PTAX USD por dia | global | **nunca** | – | **marca "hoje" como coberto antes de o BCB publicar** (P4) | zera (número muda conforme a hora do deploy) | cada processo com um número |
| 18 | `cambio._PTAX_MOEDA_MAPA/_FAIXA` (`cambio.py:65-66`) | PTAX EUR/AUD/... | moeda | nunca | – | mesmo defeito do #17 (`cambio.py:127`) | idem | idem |
| 19 | `cambio._HOJE_USD` | PTAX "de hoje" para fallback | global | até a próxima carga | – | – | – | – |
| 20 | `cambio._USDT_MAPA/_USDTARS_MAPA` | candle de abertura Binance | data | nunca | – | ok (abertura não muda) | – | – |
| 21 | `kalshi._CACHE_MERCADO/_EVENTO/_SERIE` (`kalshi.py:174-176`) | metadados de mercado | ticker | nunca, sem teto | – | metadados fixos; guarda `{}` se a API vier sem a chave (HIPÓTESE) | zera | – |
| 22 | `main._login_fails`, `_trial_por_ip`, `_signup_hits`, `_senha_hits` | rate-limit por IP | IP | janela, mas a chave nunca é podada | sucesso | – | **zera** (deploy reseta o limite) | limites por processo |
| 23 | `aviso_diario._falhas` (`aviso_diario.py:36`) | falhas da semente para o aviso diário | global | até o aviso | envio | – | **perde** as falhas (o aviso diz que está tudo bem) | – |
| 24 | `eventos._assinantes` (`eventos.py:28`) | filas SSE abertas | escopo de donos (sim) | vida da conexão | `cancelar` | – | conexões caem, cliente reconecta e recarrega | evento só chega ao processo do LISTEN |
| 25 | `database._pool` | pool asyncpg | – | – | – | – | – | `get_pool` sem trava: 2 chamadas concorrentes no boot podem criar 2 pools (HIPÓTESE) |
| 26 | `main._bg_tasks`, `_tarefas_aviso` | referências a tarefas fire-and-forget | – | – | – | – | tarefa em voo morre no deploy (uso de tokens, sombra, `bloco_visto`) | – |

### 2.2 Tarefas de fundo (lifespan, `main.py:911-933`)

| Tarefa | Faz | Pode servir velho? | Trava? | Morre em silêncio? |
|---|---|---|---|---|
| `_cache_warmer` | aquece o cache de prompt da Anthropic a cada `_WARMER_INTERVALO` | não serve dado | não | `try/except: pass` engole tudo; a referência à tarefa não é guardada (`create_task` solto) |
| `_usuarios_refresher` | recarrega identidade a cada 60 s | **sim: grava snapshot antigo por cima do novo** (P1) | não | não (try/except) |
| `eventos.escutar_banco` | LISTEN `base_mudou` → SSE | ao reconectar **não avisa ninguém** (P7) | **sim**: `conn.execute("SELECT 1")` sem `timeout` (`eventos.py:68`); em conexão meio aberta pode ficar surdo pelo keepalive TCP do SO (HIPÓTESE) | o log registra, mas a tela não sabe |
| `dicionario.diario` | semente às 07h UTC + aviso diário | – | – | deploy perto das 07h pula o dia (o sleep recomeça do zero) |
| `aviso_diario.teste_uma_vez` | 1 mensagem | – | – | – |
| `_fire(...)` (uso de tokens, sombra, `registrar_blocos_vistos`) | escrita depois da resposta | – | – | um deploy no meio perde a escrita; para `bloco_visto` isso é o lado seguro |

### 2.3 Tabelas que funcionam como cache ou marcador

| Tabela/campo | Quem grava | Quem lê | Quando diverge da fonte | Caminho de invalidação |
|---|---|---|---|---|
| `bloco_visto` (hash do bloco lido pela IA) | `registrar_blocos_vistos` (fire-and-forget, depois da IA) | barreira do `/extrair` (`blocos_conhecidos`, `repository.py:6630+`) | a prova de "leitura gravada" é `bilhetes.atualizado_em >= bloco_visto.atualizado_em`, e **qualquer** UPDATE renova esse carimbo (P10) | nenhuma automática; JOIN cobre exclusão |
| pular resolvidos (`get_codigos_resolvidos`, `repository.py:6375`) | – | pré-dedup do texto | a casa muda stake/odd/retorno de aposta resolvida **sem trocar a classe** W/L/V: pulada para sempre | só `reliquidou()` por classe |
| congelamento do UPSERT (`odd`, `data`, `stake`, `esporte`, `aposta`, `descricao` em `resolvida`) | `upsert_bilhetes` | todas as telas | primeira leitura errada da IA fica para sempre; recaptura não corrige | edição manual ou script |
| `caixa_mov.abertas_corte` / `liquidadas_corte` / `projetado` | ativação/conferência da Caixa | `_caixa_projetar` | é um retrato; o retrato pode ser tirado enquanto o `/salvar` ainda está escrevendo | `_caixa_adotar_abertas_tardias` (só cresce) |
| `cruEnviado` (extensão, `extensor/cru.js:26`) | extensão depois de 200 | extensão | chave = hash do cru, **sem dono/conta**; 60 dias; o servidor apaga/perde e a extensão não reenvia | nenhuma vinda do servidor |
| `captura_crua`, `ficha_virada`, `virada_log` | Ficha | virada, semente | – (fora do tempo desta auditoria) | – |
| `semente` regrava `bilhetes.descricao` + `atualizado_em` (`dicionario.py:851`) | tarefa diária e depois de `/extrair` | – | **renova o carimbo que a barreira usa como prova** (alimenta P10) | – |
| `correcoes` | edição humana e Ficha | script de reparo, reabertura | correção humana trava a reliquidação daquele campo | – |

### 2.4 Respostas HTTP

| Rota | Cache-Control | Comentário |
|---|---|---|
| HTML (qualquer) | `no-cache, must-revalidate` (middleware `main.py:996`) | ok |
| `/dashboard/data` | **nenhum** | dado autenticado por cookie sem `private, no-store`; sem `Last-Modified` o Chrome não reaproveita, mas nada impede um proxy/CDN de guardar (COMPROVADO, P8) |
| `/static/*`, `/dashboard/assets/*` (JS/CSS) | **nenhum**, só `ETag` + `Last-Modified` | frescor **heurístico** (10% da idade do arquivo); a renovação depende de alguém trocar o `?v=` no HTML (P8) |
| `/static/tokens.css`, `/static/fonts.css`, `vendor/*` | nenhum e **sem `?v=`** | sem mecanismo de renovação |
| `/metricas` | `public, max-age=30` | ok, público |
| logos | `private, max-age=60` + ETag | ok |
| `/eventos` (SSE) | `no-cache` | ok |
| APIs JSON em geral | nenhum | idem `/dashboard/data` |

---

## 3. Achados

### P1. O refresher de identidade grava um snapshot VELHO por cima da recarga nova (COMPROVADO)

- **Sintoma**: logo depois de trocar a senha, o usuário cai para o login e a senha **nova** dá
  "inválida" (a velha funciona) por até 60 s. Variante: o visitante do `/realtrial` toma 401
  logo depois de entrar. Também afeta aprovar conta, ligar o bot e trocar e-mail.
- **Mecanismo**: `_usuarios_refresher` (`main.py:898-907`) faz
  `atualizar_cache_usuarios(await carregar_usuarios())`. O SELECT fotografa o banco no
  instante em que roda; se a rota (`main.py:3976`, `/conta/senha`) fizer UPDATE + recarga
  imediata **enquanto** esse SELECT está em voo, o refresher termina depois e
  `atualizar_cache_usuarios` (`auth.py:200`) troca o dict inteiro pelo estado anterior.
  `registrar_usuario_no_cache` (`auth.py:361`) é um ler-modificar-escrever que o refresher
  desfaz do mesmo jeito. `ler_token` (`auth.py:532`) compara a impressão do hash contra o
  cache, então o cookie recém-emitido morre.
- **Evidência**: `provas/p1_auth_snapshot_velho.py`, com o `main._usuarios_refresher` real e o
  intervalo encurtado. Saída: `ler_token(cookie novo) = fulano` → depois do snapshot velho
  `= None`, `login senha nova = invalido`, `login senha VELHA = ok`; volta no ciclo
  seguinte. Trial: `ativo = True` → `False`.
- **Frequência real**: a janela é a latência do SELECT (milissegundos a cada 60 s), então é
  rara por evento. Mas é aleatória e impossível de reproduzir a pedido, que é o perfil do
  "bug que volta".
- **Severidade**: média (raro, mas derruba a sessão e engana na senha). Com 2 workers vira
  **certeza** por até 60 s.
- **Família sistêmica**: cache substituído inteiro, sem versão.
- **Correção estrutural**: não cachear identidade em memória sem versão. Opções: (a) carregar
  com `max(atualizado_em)` e só aceitar snapshot com versão ≥ a atual; (b) `LISTEN
  usuarios_mudou` com trigger na tabela (o mesmo padrão de `bilhetes`), trocando o polling;
  (c) a revogação passa a ser uma coluna `sessao_versao` lida do banco (1 query por request
  com índice PK; o custo é desprezível e funciona com N réplicas).

### P2. Família "estado de sessão na memória" e deploys frequentes

#### P3. Pareamento da extensão e fila de capturas morrem a cada deploy (COMPROVADO)

- **Sintoma**: "a extensão desconectou sozinha", "Sessão expirou — reconecte no popup"
  (`extensor/background.js:71/80`), o dashboard perde a sessão de captura (404), e prints ou
  textos enviados e ainda não drenados **somem sem aviso**. O usuário frequente bate nisso a
  cada deploy (3-6 por dia útil). O usuário que volta depois de dias acha o token velho
  guardado na extensão.
- **Mecanismo**: `captura._SESSOES` (`captura.py:388`) é um dict de módulo; o token da
  extensão e a fila (`Sessao.capturas`) só existem ali. `drenar_capturas` (`captura.py:512`)
  é entrega única **sem confirmação**: se a resposta do poll (`main.py:4147`) não chega ao
  navegador (aba fechada, 502 no deploy, rede), as capturas já saíram da fila.
- **Evidência**: `provas/p3_sessao_captura_memoria.py`: antes do reload, sessão viva e 2
  capturas na fila; depois, `sessao_por_token = None`, `sessao_por_id = None`. Drenagem:
  `poll 1 levou 1 | poll 2 recebe 0`.
- **Severidade**: **alta** (perda silenciosa de captura + atrito diário). É a candidata mais
  forte a "problema recorrente" do usuário frequente.
- **Família**: estado que precisa sobreviver vivendo em memória.
- **Correção estrutural**: tabela `captura_sessao` (token com hash, dono, casa, conta,
  expiração) e `captura_fila` (com `entregue_em` + ack explícito do dashboard; apaga só
  depois do ack). Opcional: token de extensão de longa duração ligado ao usuário, e não à
  sessão do dashboard.

#### Outros estados que o deploy apaga (COMPROVADO por leitura; mecanismo trivial)

- Rate-limit de login/signup/senha/trial (`main.py:3291-3296, 3489, 3941`): cada deploy zera.
  Severidade baixa.
- `aviso_diario._falhas`: falha da semente antes de um deploy some do aviso do dia seguinte.
  O aviso diz "tudo certo" com falha real. Severidade média (monitoramento cego).
- `virada._termo_novo`: o termo novo espera a rodada das 04h. Baixa.
- `virada._vigia_reservas`: o vigia pode gastar 2 chamadas pagas na mesma semana. Baixa.
- `dicionario.diario`: deploy perto das 07:00 UTC pula a semente do dia. Baixa.

### P4. Câmbio de HOJE congelado no valor de ONTEM até o próximo deploy (COMPROVADO)

- **Sintoma**: aposta em moeda estrangeira (USD, EUR...) feita hoje é gravada em R$ com a
  cotação de ontem, ou com a de hoje, **dependendo da hora do último deploy**. Na Polymarket
  (`origem='sync'` refresca a stake), o valor em R$ da mesma aposta **muda sozinho** no dia
  seguinte. Na Caixa isso aparece como divergência de centavos/reais que "some".
- **Mecanismo**: `_garantir_cobertura` (`polymarket.py:288`) e `_carregar_ptax_moeda`
  (`cambio.py:127`) gravam a faixa carregada como `[de, hoje]`. Se a 1ª carga do dia ocorre
  antes de o BCB publicar o fechamento (~13h), o mapa não tem hoje, mas a faixa diz que tem;
  todas as chamadas seguintes do dia caem no recuo (ontem). Um processo que nasce depois das
  13h tem o valor certo. Usado em `/salvar` (`main.py:4857`), aposta manual (`main.py:5913`),
  Caixa (`repository.py:3894, 4325`), Kalshi (`kalshi.py:444`) e Polymarket.
- **Evidência**: `provas/p4_ptax_hoje_congelado.py`: processo A às 10h → 5,40; às 15h, depois
  da publicação → **5,40**; processo B (deploy às 14h) às 15h → 5,55.
- **Severidade**: média (dinheiro gravado errado em centavos a reais por aposta, e não
  determinístico).
- **Família**: cache "imutável" que guarda um dado ainda **não fechado**.
- **Correção**: a faixa coberta termina no último dia **publicado** (`max(iso do mapa)`), nunca
  em "hoje"; ou não cachear o dia corrente.

### P5. O leitor guarda por 10 min o resultado de uma FALHA de banco (COMPROVADO no cache; efeito HIPÓTESE)

- **Sintoma**: por até 10 min depois de um soluço do banco, a extração recusa linhas de
  categoria que o dono usa e não estão no Master (Especiais, Aumentadas, Dupla...). Elas vão
  para a repescagem (custo extra de IA) e, na passada final, **saem do lote**. O usuário vê
  "capturei e não entrou", e 10 min depois "entrou".
- **Mecanismo**: `categorias_do_dono` (`repository.py:471-492`) captura a exceção, monta só o
  Master e **grava esse conjunto no cache** com o mesmo TTL de 600 s de um sucesso. Ninguém
  invalida ao usar categoria nova.
- **Evidência**: `provas/p5_categorias_cacheia_falha.py`: com o banco falhando,
  `Especiais = False`; segundos depois, com o banco OK, ainda `False`. Categoria nova
  (`Defesas`) também não aparece até o TTL vencer.
- **Severidade**: média.
- **Família**: falha cacheada como sucesso (mesma de P9).
- **Correção**: nunca cachear o ramo de erro (ou com TTL de segundos); invalidar ao gravar
  categoria nova; ou trocar por uma consulta indexada sem cache (`DISTINCT aposta` por dono é
  barato com índice).

### P6. Rotular tipster à mão não derruba o modelo do matcher (COMPROVADO)

- **Sintoma**: o usuário corrige o tipster de várias apostas e "Sugerir tipsters" continua
  sugerindo o errado por até 5 min. Exclusão e desfazer também não renovam.
- **Mecanismo**: `matcher.invalidar` existe "para quando o dono rotula à mão"
  (`matcher.py:303`), mas só é chamado em `/bilhetes/excluir-lote`, `/bilhetes/lote`,
  `PATCH /bilhetes/{id}` e renomear tipster. Não chamam: `POST /bilhetes/tipster`
  (`main.py:5936`, que é **exatamente** o rótulo em lote), `DELETE /bilhetes`,
  `DELETE /bilhetes/{id}`, `/bilhetes/restaurar`, `/salvar`, `/bilhetes/manual`.
- **Evidência**: `provas/p6_matcher_nao_invalida.py` (rotas reais via TestClient):
  `/bilhetes/tipster`, `DELETE /bilhetes` e `/bilhetes/restaurar` → "modelo antigo ainda em
  cache: True"; controle `/bilhetes/lote` → `False`.
- **Severidade**: baixa-média (sugestão errada, não dado gravado).
- **Família**: invalidação manual rota por rota (a mesma raiz do `?v=`).
- **Correção**: invalidar pelo banco. O trigger `base_mudou` já existe; o processo que escuta
  o `NOTIFY` derruba `matcher._CACHE[dono]` e `_CATEGORIAS_DONO[dono]`. Uma regra, todo
  escritor coberto (inclusive bot e scripts).

### P7. Tempo real: a queda do LISTEN não avisa ninguém, e o ping pode travar (COMPROVADO o primeiro; HIPÓTESE o segundo)

- **Sintoma**: a tela aberta para de se atualizar sozinha depois de uma instabilidade do
  Postgres ou da rede interna. A captura entra, mas o dashboard só mostra depois de F5.
- **Mecanismo**: `escutar_banco` (`eventos.py:56-78`) reconecta, mas os NOTIFY do vão se
  perdem e **nenhum** assinante recebe "recarregue". O cliente só recarrega quando a conexão
  SSE **dele** cai (`app.html:503-507`), e ela não cai nesse caso. A queda só é detectada no
  ping de 30 s, e o ping (`conn.execute("SELECT 1")`, linha 68) não tem `timeout`: numa
  conexão TCP meio aberta ele pode esperar o keepalive do SO (horas). O trigger só existe em
  `bilhetes` (`database.py:540-543`): mudanças em custo, Caixa, contas e tipsters vindas de
  outro aparelho/aba/operador não geram evento.
- **Evidência**: `provas/p7_listen_buraco.py`: aviso entregue antes da queda; depois da
  reconexão (2 conexões abertas), **0** avisos.
- **Severidade**: média.
- **Correção**: ao (re)conectar o LISTEN, publicar "base_mudou" para **todos** os assinantes
  (recarga única); `timeout=5` no ping; triggers equivalentes nas tabelas de cadastro, ou um
  canal genérico `dado_mudou(dono, tabela)`.

### P8. Assets JS/CSS sem `Cache-Control`; renovação depende de trocar o `?v=` à mão (COMPROVADO)

- **Sintoma**: depois de um deploy, parte dos usuários roda o JS velho com o HTML novo (casa
  nova sem ícone ou mapeamento, tela que não monta). Some "sozinho" horas depois. Clássico
  "limpa o cache que resolve".
- **Mecanismo**: StaticFiles devolve `ETag` + `Last-Modified` e nenhum `Cache-Control`
  (medido com TestClient). O navegador aplica frescor heurístico (10% da idade do arquivo) e
  **não revalida** nesse período. O único gatilho de renovação é o `?v=N` no HTML, editado à
  mão. `tokens.css`, `fonts.css` e `vendor/*` nem têm `?v=`.
- **Evidência**: `provas/p8_headers_http.py` (headers reais). Varredura do git desde 01/09:
  **224 pares (commit, asset versionado alterado), 33 sem trocar o `?v=` daquele asset**.
  Ex.: `data.js` mudou em ~20 commits desde 31/10 (2d88a34, 60e9da4, 0b7b0ee...) e continua
  `data.js?v=32` (último bump em 321a60b, 31/10). `app.js` (76f8f44, 7a0ba79),
  `components.css` (bce5fde) e `gestao.js` (7ae5dce) também. O teste existente
  (`tests/test_cache_headers.py`) trava o **contrário**: proíbe `no-cache` no JS.
- **Bônus**: `/dashboard/data` e as APIs JSON vão **sem** `Cache-Control: private, no-store`.
  Hoje nenhum navegador reaproveita (não há `Last-Modified`), mas se um CDN/proxy entrar na
  frente do domínio, nada impede guardar o feed de um usuário.
- **Severidade**: média-alta (é a família que "volta" a cada esquecimento).
- **Correção**: nome de arquivo com hash do conteúdo, gerado no build (ou `?v=<sha do
  arquivo>` calculado pelo servidor ao servir o HTML) + `Cache-Control: public,
  max-age=31536000, immutable` nos assets; `private, no-store` em toda rota de API. Isso
  elimina o passo manual inteiro.

### P9. Planilha ao vivo: fonte fora serve o último feed para sempre, sem dizer (COMPROVADO)

- **Sintoma**: o cliente de planilha viva (`LavaFatuch`) vê números parados por dias; o
  "Atualizar dados" não muda nada; o rótulo "último sync" mostra **agora**.
- **Mecanismo**: `dashboard_rows_ao_vivo` (`planilha_viva.py:84-86`) devolve `em_cache[1]` em
  qualquer exceção, sem limite de idade, inclusive com `refresh=True`; `/dashboard/data`
  carimba `builtAt = now()` (`main.py:5185`).
- **Evidência**: `provas/p9_planilha_viva_stale.py`: 3 dias depois, fonte fora, `refresh=1` →
  1 linha (a fonte tem 2), sem erro.
- **Severidade**: média (1 cliente hoje).
- **Correção**: limite de idade do stale (ex.: 1 h) e `builtAt` = instante do dado, mais um
  campo `stale: true` que a tela mostra.

### P10. A barreira de recaptura prova "leitura gravada" com um carimbo que qualquer escrita renova (HIPÓTESE forte, estática)

- **Sintoma**: aposta liquidada na casa fica **aberta para sempre** no Sharpen; recapturar não
  conserta. A família já foi corrigida em s407, s424, s447 e s448, e voltou.
- **Mecanismo**: `blocos_conhecidos(gravados=True)` (`repository.py:6681-6689`) pula o bloco
  quando `bilhetes.atualizado_em >= bloco_visto.atualizado_em`. O `bloco_visto` é gravado
  fire-and-forget **depois** da IA (`main.py:2562` e `1605`, via `_barreira_lembrar`), sem relação transacional com o `/salvar`.
  Se aquela leitura não chegou ao banco e **qualquer outra escrita** tocar a linha depois,
  o carimbo passa: `set_tipster_bulk` (`repository.py:6054`), tipster sugerido
  (`repository.py:4560`), edição (`repository.py:5700`) e a **semente diária**, que regrava a
  descrição das apostas da Ficha do mês e renova `atualizado_em` (`dicionario.py:851`). O
  próprio docstring admite parte do buraco ("Não cobre: edição à mão...").
- **Severidade**: alta (dinheiro: aposta ganha não liquida).
- **Família**: marcador persistente de "já processado" que não guarda **o que** foi
  persistido.
- **Correção**: gravar o `bloco_hash` **na linha do bilhete, no mesmo UPSERT** do `/salvar`
  (coluna `bloco_hash_gravado`), e pular só quando `hash_atual == bilhetes.bloco_hash_gravado`.
  Assim a prova é atômica com o dado e nenhuma outra escrita a falsifica. O mesmo vale para o
  `cruEnviado` da extensão: o servidor devolve a lista de hashes que **tem**, em vez de a
  extensão lembrar do que **mandou**.
- **Não reproduzido** por falta de tempo para subir o Postgres local (há binários em
  `C:\Program Files\PostgreSQL\17` e o harness `tests/test_repository_db.py`). Roteiro de
  prova: UPSERT aberta → `registrar_blocos_vistos` com o bloco liquidado (sem salvar) →
  `set_tipster_bulk` na linha → `blocos_conhecidos(gravados=True)` devolve o código e
  `_dedup_superbet_text` o pula.

### P11. Vazamento entre usuários (cruza a minha lente com a do cliente)

- **Servidor: nenhum cache sem dono que sirva dado de usuário.** Todos os caches de dado
  (`matcher`, `_CATEGORIAS_DONO`, `planilha_viva`, `_SESSOES`) são chaveados por dono; o
  público é por slug e só tem dado público. Feed principal: **sem cache no servidor**
  (`dashboard_rows` lê do banco a cada chamada). COMPROVADO por inventário (grep de todo
  estado de módulo em `app/`).
- **Cliente, alimentado pelo servidor (HIPÓTESE forte, estática)**: o cache IndexedDB do feed
  usa a chave fixa `'dados_v1'` (`app/static/dash/assets/js/app.js:1538`), sem o dono, e
  nada o limpa no logout (`app.html` só faz `POST /logout`). No mesmo navegador, quem entra
  depois (outro usuário, ou o supervisor alternando "ver como") vê no boot o feed do anterior
  até a revalidação terminar, e **continua vendo** se o fetch falhar. O servidor já manda
  `dono` no payload; basta o cliente namespaciar a chave e limpar no logout. Também explica o
  "usuário que volta depois de muito tempo": o boot mostra o feed de semanas atrás com a
  pílula "Sincronizando".
- `cruEnviado` (extensão) também não tem dono/conta na chave.

### P12. Achados menores

- `kalshi._CACHE_*`: sem teto e guardam `{}` se a resposta vier sem a chave esperada; uma
  aposta pode ficar sem título até o restart (HIPÓTESE).
- `database.get_pool` sem trava: duas corrotinas no boot podem criar dois pools (HIPÓTESE,
  baixo impacto).
- `_cache_warmer` e as outras tarefas do lifespan são criadas sem guardar referência e sem
  `add_done_callback` de log; exceção fora do `try` mata a tarefa em silêncio (HIPÓTESE,
  baixo).
- SSE: o escopo é calculado na assinatura; quem alterna "ver como" continua ouvindo o escopo
  antigo até reconectar (HIPÓTESE, baixo).
- Rate-limit por IP sem poda da chave (crescimento de memória lento).

---

## 4. Ordem de ataque sugerida (estrutural, não remendo)

1. **Assets com hash de conteúdo + `immutable`; APIs com `private, no-store`** (P8). Tira o
   passo manual que mais falha. Baixo risco.
2. **Sessão de captura e fila no Postgres, com ack** (P3). Acaba com o "desconectou" diário e
   com a perda silenciosa.
3. **Invalidação pelo banco**: `NOTIFY` genérico `(tabela, dono)` por trigger nas tabelas de
   dado; um despachante único derruba os caches em memória (matcher, categorias,
   identidade) e repassa ao SSE; ao reconectar o LISTEN, "recarregue tudo" (P1, P6, P7).
   É também o que permite subir para N workers/réplicas.
4. **Prova de persistência atômica** para as barreiras (`bloco_hash` na linha do bilhete)
   (P10).
5. **Regra única de cache em memória**: nunca guardar o ramo de erro; nunca marcar como fechado
   um dia ainda aberto; todo cache com versão/idade exposta (P4, P5, P9).
6. Cliente: chave do IndexedDB por dono + limpar no logout (P11; lente do cliente).

---

## 5. O que não consegui verificar

- **Réplicas na Railway**: só o `railway.toml` foi lido; o número de réplicas e se há CDN/proxy
  na frente de `sharpen.bet` dependem do painel e não foram consultados (não toquei produção).
- **P10 no Postgres real**: não reproduzido (roteiro acima). Também não medi quantas apostas
  abertas em produção estão nessa condição.
- **Efeito final de P5** (linha recusada na passada final = aposta fora do lote): inferido de
  `main.py:695-712`; não rodei uma extração.
- **Frequência real de P1**: depende da latência do SELECT de `usuarios` em produção; não
  medida.
- **Comportamento do navegador**: o frescor heurístico do P8 vem da especificação HTTP e da
  ausência de `Cache-Control`; não abri um navegador. O `Last-Modified` em produção depende
  do mtime que o build da Railway preserva no `COPY`, que não conferi.
- **Travamento do ping do LISTEN (P7, 2ª parte)**: depende do keepalive TCP do container; não
  simulado.
- **Tabelas `captura_crua`, `ficha_virada`, `virada_log`, `sombra_*`, `vigia_ficha`** como
  marcadores: lidas só por cima; podem ter caminhos de "já processado" não auditados.
- `app/casa_chave.py` está modificado por outra sessão; foi importado indiretamente nas
  provas (via `virada`), mas não analisado.
- Não rodei a suíte de testes existente; as provas não dependem dela.
