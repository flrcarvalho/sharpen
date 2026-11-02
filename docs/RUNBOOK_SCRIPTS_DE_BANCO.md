# Runbook · script que apaga aposta: Postgres de teste antes da produção

> Regra no [`CLAUDE.md`](../CLAUDE.md), seção "Excluir dado". Decisão do Feca, 01/11/2026 (s438):
> a **1ª execução** de qualquer um dos 24 scripts abaixo depois da Fase 7 roda antes contra o
> Postgres de teste local, e só depois em produção.

## Por quê

Na Fase 7 (s438) os 24 scripts trocaram o `DELETE FROM bilhetes` pela
`repository._mover_para_lixeira` (via `scripts/_lixeira.py`). Os gates conferem sintaxe, nomes
indefinidos (`pyflakes`) e que nenhum script apaga fora da lixeira, mas **nenhum deles foi rodado
de ponta a ponta** depois da troca. Na própria s438 a troca deixou o `podar_conta_para_lista.py`
imprimindo uma variável que tinha saído: ele quebraria com `NameError` DEPOIS de já ter apagado.
E script de banco rodando em produção já derrubou o Sharpen (25/10/2026, memória
`semente_com_deploy_derruba_o_sharpen`).

## Os 24

Imports que se refazem: `import_apostas_xlsx`, `import_arrudex_xlsx`, `import_dashboard_xlsx`,
`import_diogo_sharktrack_xlsx`, `import_ewanderson_csv`, `import_fleury_xlsx`,
`import_grego_canal_s325`, `import_grego_csv`, `import_lava`, `import_lavapessoal_xlsx`,
`import_passatips_xlsx`, `import_perereca_csv`, `import_reidocriquete_xlsx`, `import_rogerin_csv`,
`import_sochutes_xlsx`, `import_sohprops_csv`.

Reparos e limpezas: `excluir_historico_fora_do_corte`, `remover_lote_conta_errada`,
`reparar_duplicatas_codigo_fantasma`, `reparar_duplicatas_codigo_ocr`,
`limpar_bet365_sem_confirmation`, `podar_conta_para_lista`, `corrigir_caixa_fantasma_s327`,
`limpar_orfas_bolsa_2026-07-12`.

Quando um deles rodar a 1ª vez (teste e produção), anote aqui, na tabela de baixo: o script sai
da obrigação.

## Como

1. **Suba o Postgres de teste local** (memória `harness_db_ci`): binários em
   `%TEMP%\pgbin\pgsql\bin`, dados em `%TEMP%\pgdata`, porta 55432, banco `sharpen_test`.
   `pg_ctl -D "%TEMP%\pgdata" -o "-p 55432" -w start`. Se o `%TEMP%` foi limpo, a memória diz como
   remontar.
2. **Schema atual:** rode uma vez o harness (`TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:55432/sharpen_test python -m pytest tests/test_repository_db.py -q`), que aplica o `init_db`.
3. **Rode o script apontando para o teste:** todos os 24 leem `DATABASE_URL` do ambiente, e o
   `load_dotenv` não sobrescreve variável já definida.
   ```
   DATABASE_URL=postgresql://postgres@127.0.0.1:55432/sharpen_test python scripts/<script>.py <args>
   ```
   Primeiro o ensaio (quando o script tem), depois o `--aplicar`. Sem dado no banco de teste, o
   reparo não acha nada, mas o caminho inteiro roda (SQL, lixeira, impressão final). Para exercitar
   com dado, copie para o teste só as linhas daquele dono e casa, por `SELECT` (`db_ro.py`), nunca
   o dump inteiro.
4. **Confira no banco de teste:** a `lixeira_bilhetes` recebeu as linhas com o motivo do script, e
   o que tinha de sair saiu.
5. **Só então em produção**, sozinho: nada de push nem deploy enquanto ele roda.

## Registro da 1ª execução

| Script | Teste local (data) | Produção (data) |
|---|---|---|
| (nenhum ainda) | | |
