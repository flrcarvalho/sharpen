# Runbook — formato da saída (TSV)

> **Fonte canônica: [`../global/MASTER_OUTPUT_2026.md`](../global/MASTER_OUTPUT_2026.md)**
> (TAB, 10 colunas, 11ª coluna interna `Código`, decimal vírgula, códigos de resultado).
> O que está aqui é **espelho operacional** — ao mudar o formato, mude no MASTER primeiro.
>
> Saiu do `CLAUDE.md` na s366, quando ele encostou no teto de 65 KB. O critério do
> invariante #10: o que se lê ao **FAZER** vira runbook; o `CLAUDE.md` guarda o que
> **decide**. Este bloco é as duas coisas de uma vez — um resumo de um MASTER —, e
> resumo de fonte canônica é exatamente a duplicação que originou o teto.

---

## As colunas

- Separador: **TAB real** (U+0009) — nunca espaços, ponto-e-vírgula ou pipe
- **10 colunas para a planilha do usuário**: `Data | Esporte | Tipster | Casa | Parceiro | Aposta | Descrição | Stake | Odd | Resultado`
- **11ª coluna interna** (`Código`): ID/código do bilhete visível no print — nunca vai
  para a planilha do usuário, só para o banco de dados. A AI sempre retorna essa coluna;
  se não houver ID visível, a célula fica vazia.
- **12ª coluna interna** (`Sistema`, formato `3x Duplas`): estrutura de bilhete de
  sistema. **A IA NÃO a emite** — o backend a anexa depois de responder
  (`anexar_sistema_tsv`), lendo o `Tipo: SISTEMA …` do texto do robô e casando pelo
  código. Vira `sistema`/`sistema_linhas` no banco; ausente = bilhete de linha única.
  Existe porque a odd de sistema é a **média das linhas** (`MASTER_RESULTADO §7.3`) e
  nada mais no banco distinguia um `3 x Duplas` da tripla das mesmas seleções — a
  descrição dos dois é idêntica.

## Os valores

- Decimal: **vírgula** (`2,35`) — nunca ponto
- Resultado: `W · L · V · HW · HL` — ou **vazio** quando a aposta está aberta (não
  liquidada; ver `MASTER_OUTPUT §13.1` / `MASTER_RESULTADO §1.1`)
- Odd sem limite de casas decimais (planilha usa a precisão completa)

---

> **Por que a 11ª coluna é frágil, e onde isso está escrito:** ela é a última coluna de
> identidade sem extração determinística — quem a escreve é a IA, copiando o `[Código: …]`
> do bloco. A regra de conferência contra o gabarito continua no
> [`../CLAUDE.md`](../CLAUDE.md), porque ela **decide** o que gravar, e não apenas
> descreve o formato.
