# Medição da produção (só leitura)

Harness da [`MEDICAO_PRODUCAO.md`](../../docs/auditoria_2026-11-17/MEDICAO_PRODUCAO.md)
(s460, 17/11/2026). Precisa do CLI da Railway logado e vinculado ao projeto.

**Só leitura, por construção:** `prodq.py` pega a `DATABASE_PUBLIC_URL` do serviço
Postgres pelo CLI dentro do processo (nunca imprime), conecta com
`default_transaction_read_only=on`, roda cada consulta numa transação `READ ONLY` e recusa
SQL que não comece com `SELECT`/`WITH`/`SHOW`/`EXPLAIN`. Saída em JSON vai para fora do
repo (passe um caminho no scratchpad): tem dado de usuário.

| Script | O que mede |
|---|---|
| `prodq.py arquivo.sql` | executor de consultas (blocos separados por `-- @@ título`) |
| `dump_abertas.py saida.json` | apostas abertas + cru, `bloco_visto` e `ficha_virada` mais recentes |
| `classificar.py entrada.json saida.json` | passa o cru pelos adaptadores do servidor (`ficha.montar_ficha` + `derivar`): liquidada × aberta × recusada |
| `dump_ausentes.py saida.json` | códigos em `ficha_virada` sem linha em `bilhetes` |
| `caixas.py saida.json` | estado de toda Caixa com movimento, por `repository._caixa_projetar` |
| `banco_x_cru.py dono "Casa" "conta"` | aposta a aposta: banco × cru da casa, com a diferença de P/L |
| `agrega_http.py pasta` | erros por rota nos logs HTTP baixados com `railway logs --http --json` |

O CLI da Railway aceita no máximo **5.000** linhas por chamada de log (`-n`); acima disso
devolve `Invalid input` em silêncio. Logs HTTP são por deploy: baixe deploy por deploy.

Não cobre: casa sem cru (texto/print), onde `bloco_visto` só guarda hash e não diz o
resultado.
