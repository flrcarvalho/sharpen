## Testes

**Veredito da área:** Precisa de atenção (amarelo) — o núcleo matemático é sólido e bem protegido, mas as bordas de maior risco (tenancy, escrita de dinheiro no banco e forja de sessão) estão 100% descobertas.

**Top 3 ações prioritárias:**
- **Criar `tests/test_auth.py` (esforço pequeno, retorno alto).** `auth.py` é todo função pura e sem um único teste, guardando a isolação entre inquilinos. Fecha o buraco de forja de cookie e escalada de privilégio com baixo custo.
- **Introduzir um harness de camada-DB** (fake pool asyncpg ou sqlite de teste) para exercer `upsert_bilhetes` e as queries filtradas por `dono`. Hoje o conftest stuba o banco e deixa ~50 de 60 funções async sem rede — é onde vivem dinheiro, dedup e tenancy.
- **Ancorar as regressões de dinheiro no ponto de ESCRITA.** Sobre o harness de DB, travar o `.upper()` do resultado no upsert e o comportamento de descarte silencioso do `parse_tsv`, além de um golden de cashout. Regras monetárias documentadas hoje não têm guard onde o bug realmente mora.

---

### Achados críticos e altos (detalhados)

**1. [ALTO/confirmado] `auth.py` sem nenhum teste — isolação multi-tenant e forja de sessão descobertas.** `app/auth.py:116-204`
Toda a camada de autenticação/autorização é composta de funções puras (sem banco), perfeitamente testáveis, e não tem cobertura. São o guarda da fronteira entre inquilinos:
- `ler_token` — valida HMAC do cookie e expiração;
- `dono_efetivo` — resolve a base visível; deve cair no próprio usuário se o cookie "ver como" for forjado;
- `pode_ver_como` — matriz de privilégio dono→operador;
- `coproprietarios` — linhagem usada na dedup cruzada.

Um bug aqui significa um dono ver/editar/deletar dados de outro, ou um cookie forjado escalar privilégio. Nenhum arquivo `tests/*.py` importa `auth`.

**Recomendação:** `tests/test_auth.py` (puro, sem DB): (1) `ler_token` rejeita HMAC adulterado, token expirado e usuário fora de `USUARIOS`; round-trip `criar_token→ler_token` OK; (2) `dono_efetivo` com cookie ver-como forjado (assinado com outro segredo) ou de alvo não-autorizado retorna o usuário real, nunca o alvo; (3) `pode_ver_como` matriz completa (dono vê operador; operador não vê ninguém; dono não vê outro dono); (4) `coproprietarios` simétrico e vazio para dono solo. *(esforço: pequeno)*

**2. [ALTO/confirmado] Caminho de escrita de dinheiro (`upsert_bilhetes`) e todas as queries por dono sem teste — conftest stuba o banco inteiro.** `app/repository.py:614-870`
O conftest injeta stubs de `asyncpg` e `database` para importar `repository` sem Postgres, mas com isso NENHUMA das ~50 funções async é exercida. A mais crítica, `upsert_bilhetes`, concentra dinheiro + dedup + tenancy num só lugar:
- contagem insere-vs-atualiza (`xmax=0`);
- guard de dedup cruzada entre donos (linhas 730-741);
- aviso da camada 2 (re-extração que perdeu ID);
- migração A/B de assinatura;
- o `ON CONFLICT` do UPSERT;
- a canonização `resultado.strip().upper()` na escrita.

Toda essa lógica de decisão só existe no SQL/orquestração async e roda em produção sem cobertura. O mesmo vale para `list_bilhetes`, `dashboard_rows`, `deletar_bilhetes`, `atualizar_bilhete` — todas filtram por `dono` e nada prova que o dono X não alcança linhas do dono Y.

**Recomendação:** harness de camada-DB — fake pool asyncpg (conn com `fetch`/`fetchrow`/`execute` em memória) OU sqlite/testcontainers só para os testes de repositório. Cobrir no mínimo: (a) upsert do mesmo bilhete duas vezes → 1 inserido + 1 atualizado (não 2 inseridos); (b) mesmo mercado com stake diferente → 2 linhas distintas; (c) guard de dedup cruzada barra recaptura sob co-proprietário; (d) deletar/atualizar/listar de um dono nunca alcança linha de outro dono. *(esforço: grande)*

---

### Achados médios e baixos (resumidos em tabela)

| Sev. | Achado | Local | Ação recomendada | Esforço |
|---|---|---|---|---|
| Médio | Regressão do bug case-sensitive do resultado só cobre a LEITURA, não a ESCRITA. Remover o `.upper()` do upsert (linha 794) mantém a suíte verde, pois `estado_extracao` canoniza por conta própria — a regressão não está travada onde o bug mora. | `repository.py:794` | Sobre o harness de DB: upsert de linha com `resultado='w'` → persistido tem `resultado='W'` e `extraction_state='resolvida'`. | Pequeno |
| Médio | `parse_tsv` — fronteira de entrada do `/salvar` sem teste; linha com <10 colunas é descartada em silêncio (TAB colado como espaço faz um bilhete de dinheiro sumir sem erro). | `repository.py:282-301` | `tests/test_parse_tsv.py`: 10 e 11 colunas parseiam (código correto); 9 colunas descartada (comportamento intencional documentado); cabeçalho ignorado; linhas vazias puladas. | Pequeno |
| Médio | Regra de cashout (dinheiro) sem nenhum guard automatizado. Conversão acontece na extração (prompt/IA), fora do Python; mudança de prompt pode quebrá-la sem alarme. | `MASTER_RESULTADO_2026.md` | Caso golden (bilhete real de cashout + TSV esperado) OU, se isolável, extrair a conversão e testar: cashout 70/stake 100 → W, odd 0,70, P/L −30; cashout 130 → W, odd 1,30, P/L +30; cashout=stake → V, P/L 0. | Médio |
| Baixo | `analisar_extracao` (confiança + notas do rail RAIO-X) coberta só de raspão — o único teste checa sinalização de descrição, não o número de confiança nem os contadores `sem_odd`/`sem_stake`/duplicata. | `repository.py:459-544` | Lote misto (1 sem odd, 1 sem stake, 1 incerto) → confiança e notas com `n` corretos; dict duplicatas com `occ>1` → nota DUPLICATA; lote limpo → única nota `ok`. | Pequeno |
| Baixo | `custo_usd` (billing de tokens, base do `/uso/tokens`) é puro e não testado — erro de fator (1M vs 1k, cache não descontado) distorce a métrica de custo por bilhete. | `repository.py:1930-1940` | `tests/test_custo.py`: casos input/output/cache conhecidos por modelo → dólar esperado, incluindo modelo desconhecido (fallback) e desconto de cache. | Trivial |

---

### Pontos positivos (o que está bem feito)

- **Núcleo monetário com rede de regressão exemplar.** `test_formulas.py` cobre `calcular_pl` nos cinco resultados (W/L/V/HW/HL), os guards de odd ilegível (W/HW não viram −stake), parsers BR (milhar ponto vs decimal vírgula), validadores de fronteira e o agregado (P/L, turnover, ROI, win rate). `test_dedup` e `test_assinatura_edicao` amarram cada caso ao bug real que guardam (stake fora da assinatura; assinatura stale na edição), com docstrings explicando o incidente. Qualquer mudança que altere um centavo ou reabra o gap de dedup quebra aqui antes de produção. **Este é o padrão a replicar** na camada async (auth e DB). *(`tests/test_formulas.py:1-305`)*
- **Backstops anti-corrupção de identidade cobertos.** `test_captura.py` protege dois pontos sensíveis a fraude/corrupção: `casa_de_host` (impede que captura do site de uma casa seja gravada no slot de outra e não confunde domínio que só *contém* o nome — `betfair.bet.br.evil.com → None`) e `corrigir_codigos_tsv` (snap determinístico de ID contra o texto-fonte, com casos exato/garbled/truncado/um-para-um calibrados em dados reais da conta KingPanda). São exatamente os pontos onde um erro silencioso contaminaria a dedup por ID. Nenhuma ação necessária. *(`tests/test_captura.py:1-32`)*

**Síntese para o CEO:** o dinheiro *calculado* está sólido e bem defendido; o dinheiro *gravado, isolado por cliente e protegido por sessão* está sem teste. As duas primeiras ações (auth + harness de DB) fecham o grosso do risco e usam os arquivos de teste já existentes como molde.