# RUNBOOK · Perfil de tipster com visão: como escrever

> A regra (a casa é SAÍDA da leitura; nunca nomeie uma no prompt) está no `CLAUDE.md`,
> seção "Perfil de tipster". Aqui fica o procedimento, movido de lá na s449 (teto do arquivo).

**Como escrever:** liste `NOMES_CASAS` (`src/casas.js`), peça `"casa"` no JSON e diga
explicitamente que *casa, layout ou formato diferente NÃO é motivo de erro — "ilegível"
é sobre a IMAGEM*. No código, a precedência é **legenda → print → default**, passando o
que a visão devolveu por `casaPorTexto` (canoniza a grafia; verbatim ali cria conta
paralela) e **avisando no apoio quando é o default que decide** — casa errada não dá
erro, dá conta paralela.

Gate barato: o teste assere que a **1ª linha do prompt** não contém nome de casa nenhum.
Exporte o `SYSTEM` só para isso.
