# Casos de teste que passa sem detectar

> Partição de [`../CASOS.md`](../CASOS.md) por assunto, aberta quando ele encostou no
> teto de 60 KB do `check_docs.py`. **Teto é sinal de partição, não de excesso: caso não
> se apaga.** Caso novo de falso verde entra AQUI, não lá.

> ⚠️ Daqui de dentro, todo caminho relativo sobe um nível: `../CASOS.md`, `../../tests/`.

> A **regra** vive no [`../../CLAUDE.md`](../../CLAUDE.md) § *"Teste verde não é teste que
> detecta"*: gate novo só vale depois de provado por mutação.

---


## O teste que reimplementava o código — s286

O harness **reescrevia** a ligação do listener em vez de recortá-la do arquivo. A mutação
que removia o guard passou **verde**: o teste estava exercitando a própria cópia, não o
código.

## O limite que o teste declarou e ninguém foi fechar — barreira de recaptura, s334 → s376

O cabeçalho de `tests/test_barreira_recaptura.py` diz, por escrito: *"Não tocam o banco. O
`JOIN` de `blocos_conhecidos` com `bilhetes` é SQL e não é exercido aqui. Ele tem de ser
conferido contra o Postgres real antes de a barreira valer em produção."*

Ninguém foi conferir. A Fase 1 subiu em **09/09** com 12 testes verdes e o harness verde, e
**não pulou um bloco sequer até 20/09**. O `_filtro_conta` acrescentava ` AND casa = $3` sem
qualificar a tabela; as duas do `JOIN` (`bilhetes` e `bloco_visto`) têm essa coluna, então
vinha `AmbiguousColumnError`, que caía no `except` e devolvia `{}` — "segue sem pular nada",
que é o lado seguro e por isso é invisível.

Medido em produção antes do conserto: **399 de 400** blocos relidos já tinham o hash exato
gravado em `bloco_visto`. A memória existia; quem não conseguia lê-la era a query.

**Três coisas que este caso ensina, e a terceira é a que dói:**

1. **Limite declarado é dívida, não documentação.** Declarar o que o teste não cobre
   (regra do `CLAUDE.md`) é metade; a outra metade é alguém fechar, e a declaração tem de
   vir com dono e data, senão vira álibi.
2. **`except` largo em caminho de economia transforma defeito em silêncio.** O modo de
   falha aqui não é erro, é conta que não baixa. Ninguém abre chamado por isso. Onde o
   `except` protege o caminho quente, o log precisa ser conferido em produção uma vez,
   nem que seja à mão.
3. **Verde não é efeito.** Entre 09/09 e 20/09 o item constava como entregue no plano e no
   `BACKLOG`, e a economia era zero. Item de custo só fecha com número medido em produção,
   antes e depois.

O conserto fechou a **classe**, não a instância: `_filtro_conta` passou a receber `tabela`,
e quem usa uma tabela só não passa nada. O gate novo vive em `tests/test_repository_db.py`
(CI, Postgres de teste), que é onde SQL se prova.

## A bancada que condenou o modelo errado — s377 → s378

Uma bancada nova mediu três modelos sobre blocos reais e reprovou o Haiku 4.5: *"perdeu
8,7 % dos bilhetes e inventou 19 códigos"*. O item foi fechado no `BACKLOG` no mesmo dia.

**Os dois números eram da bancada, não do modelo.** Remedido: ele perde **zero** e inventa
**zero** (300 blocos → 300 linhas). Dois defeitos meus, os dois no arranjo da entrada:

1. **Lotes sorteados.** Eu montava o lote com 6 bilhetes tirados de dias diferentes.
   Bilhete parecido lado a lado é o que faz um modelo fundir dois num só, e a instrução tem
   uma seção inteira sobre isso. Produção nunca monta lote assim: são blocos consecutivos
   de uma extração.
2. **`parceiro = "(nao informado)"`.** O modelo emitia a coluna 5 vazia; com duas colunas
   vazias seguidas ele perde a conta e come a terceira, que é o `resultado` vazio da aposta
   aberta. Produção sempre manda o nome da conta.

**A pista existia e eu usei metade dela.** No mesmo dia eu comparei a bancada com o banco,
vi 3,6 % de coluna comida contra 0,2 % de órfãs em produção, e concluí corretamente *"o
defeito é do meu harness"*. **Usei essa conclusão só para absolver o Sonnet 5.** Não voltei
para reexaminar a condenação do Haiku, que tinha saído da mesma bancada, no mesmo dia, com
o mesmo defeito.

**A regra que faltava:** uma bancada nova é código não testado, e código não testado não
condena ninguém. **Valide a régua contra um caso de resposta conhecida antes de usá-la para
decidir** — aqui havia um de graça, o banco de produção. E quando a régua for desmentida
uma vez, **todo veredito que ela emitiu volta para a fila**, não só o que incomoda.

> Sintoma para reconhecer isto noutra medição: o resultado contradiz uma fonte que você já
> tem. Não escolha qual acreditar por conveniência do argumento — a contradição é sobre a
> RÉGUA, e vale para tudo que ela mediu.

## O dado sintético que não exercia a regra — s287

Um feed com 5 itens nunca atinge um corte de 12. Sem empate, o desempate não decide nada. E
o sort do V8 é **estável**: um empate pode "acertar" sem regra nenhuma, se a ordem natural
já for a esperada.

## O DOM dublado que sempre clica — s279

O DOM de teste sempre "clica" e nunca rola de verdade. O verde não diz nada sobre rolagem.
