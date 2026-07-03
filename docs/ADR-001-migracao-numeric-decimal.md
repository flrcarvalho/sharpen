# ADR-001 — Migração de dinheiro/odd/data para tipos numéricos (NUMERIC/DATE + Decimal)

- **Status:** Proposto (aprovado em princípio na leva pós-auditoria Codex, 2026-07-03). **Execução adiada** — sem backfill imediato.
- **Contexto:** achados #13 e #25 da `AUDITORIA_CRITICA_2026-07-02.md`; §4 do `RELATORIO_CORRECOES_2026-07-03.md`; verdito do Codex ("não migrar no escuro; abrir plano formal com colunas canônicas e backfill auditado, migrar depois que o `/salvar` estiver validando melhor").

---

## Contexto

Hoje `bilhetes.stake`, `bilhetes.odd`, `bilhetes.data` e `bilhetes.resultado` são `TEXT` (`app/database.py`). A conversão para número/data acontece em Python (`_num`/`_num_or_none`/`_data_iso` em `app/repository.py`). Isso foi uma **decisão deliberada**: a odd guarda precisão livre (até 12 casas), e o histórico mistura convenções (BR `1.234,50` e ponto-decimal `75.2606`; datas `DD/MM/YYYY` e ISO).

**Verificação (sessão 2026-07-03):** as fórmulas de P/L estão matematicamente corretas e o uso de `float` é **inofensivo** na prática (arredonda por bilhete; erro << 1 centavo). Ou seja: **não há corrupção de dinheiro hoje** por causa do TEXT/float — o risco é de *higiene, performance e robustez futura*, não de exatidão atual. Por isso a migração é **melhoria estrutural, não correção urgente**.

Custos reais do TEXT hoje:
- nenhuma agregação/ordenação numérica ou por data no SQL — tudo reprocessado linha a linha em Python;
- parsing manual repetido; risco de `0.0` silencioso (mitigado pelo guard T1.1 e pela validação de fronteira T1.2/T4);
- ordenação por data é lexicográfica (só correta quando ISO).

## Decisão

Adotar **colunas canônicas aditivas**, preservando o TEXT original como valor exibido/auditável:

| Nova coluna | Tipo | Origem |
|---|---|---|
| `stake_num` | `NUMERIC(18,6)` | parse de `stake` |
| `odd_num` | `NUMERIC(18,6)` | parse de `odd` |
| `data_date` | `DATE` | parse de `data` |

- O `TEXT` original **permanece** (`stake`/`odd`/`data`) como "valor como veio do bilhete" — nada é destruído.
- O backend passa a calcular com **`Decimal`** (não `float`) a partir das colunas canônicas, com **política de arredondamento explícita** (a definir: `ROUND_HALF_UP`, 2 casas no P/L).
- `resultado` já é validado (T1.2/T4) e tem domínio pequeno — vira `CHECK`/enum numa fase posterior, opcional.

**Gate de execução:** a migração só começa **depois** que:
1. o `/salvar` estiver rejeitando entrada malformada (✅ feito — item 4 desta leva);
2. os golden tests cobrirem o caminho Decimal (a adicionar na fase 2);
3. houver janela para rodar o backfill auditado com o Feca acompanhando.

## Plano em fases (quando executar)

**Fase 0 — Migrações versionadas.** Decidir o mecanismo: adotar **Alembic** ou manter um bloco SQL idempotente versionado (hoje o schema roda inline no boot, `SCHEMA_SQL`). Recomendação: migração **one-shot** fora do boot para os `ALTER`/backfill (o boot idempotente serve para `CREATE IF NOT EXISTS`, não para backfill pesado).

**Fase 1 — Adicionar colunas (nullable).** `ALTER TABLE bilhetes ADD COLUMN stake_num NUMERIC(18,6)`, idem `odd_num`, `data_date DATE`. Zero impacto: colunas vazias, ninguém lê ainda.

**Fase 2 — Backfill auditado.** Script que lê o TEXT, converte com `_num_or_none`/`_data_iso`, grava o canônico e **emite relatório**: total, convertidos, falhados (com id/valor). Idempotente e re-executável; **read-verify** (recomputar P/L pelos dois caminhos e comparar). Nada é sobrescrito no TEXT. Adicionar golden tests do caminho Decimal aqui.

**Fase 3 — Dual-write.** `upsert_bilhetes`/`atualizar_bilhete` passam a gravar TEXT **e** canônico (parse na escrita, já barrado por validação).

**Fase 4 — Trocar as leituras.** `calcular_pl`/`_resumir_apostas`/`dashboard_rows` leem o canônico quando presente, com fallback ao parse do TEXT enquanto houver linha sem backfill. Índices em `data_date` e agregações no SQL entram aqui.

**Fase 5 — Tornar canônico autoritativo.** Backfill 100% limpo → canônico manda; TEXT vira só "valor original exibido". Opcional: `NOT NULL` + `CHECK`.

## Consequências

- **Ganho:** agregação/ordenação no SQL (destrava #17 — dashboard agregar no banco), `Decimal` fim-a-fim, dados robustos, menos parsing em Python.
- **Custo/risco:** backfill sobre dezenas de milhares de linhas; qualquer parse divergente aparece no relatório da fase 2 antes de virar autoritativo. Rollback trivial nas fases 1–4 (basta parar de ler o canônico; TEXT intacto).
- **Não faz parte deste ADR:** trocar o mecanismo de auth, modularizar, tenancy.

## Decisões em aberto (para o Codex/Feca)

1. **Alembic vs SQL versionado** — adotar Alembic agora (paga dívida #14) ou migração one-shot manual?
2. **Política de arredondamento** do `Decimal` (proposta: `ROUND_HALF_UP`, 2 casas no P/L; odd sem arredondar).
3. **`BASE_BANK` (banca base 100k hardcoded)** — parametrizar por dono/conta na mesma leva? (achado do drawdown %).

---

VERSÃO: 2026 · 2026-07-03 · complementa `RISK_REDUCTION_PLAN.md` e `RELATORIO_CORRECOES_2026-07-03.md`
