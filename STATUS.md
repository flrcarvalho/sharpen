# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`


_Atualizado: 2026-09-09 (sessao 339: **o mes do Ctrl Alt Green fechava negativo porque a captura datava 8 vitorias em AMANHA.** Relato do Feca as 22:50 de 09/09, com duas perguntas que eram o MESMO defeito: "o resultado nao parece atualizado" e "por que voce finalizou apostas com 10/09?". As 8 linhas estavam no banco, todas `W`, somando **+R$ 928,00** — mas datadas de **10/09**, um dia que ainda nao tinha chegado. O MTD recorta `[1o do mes, hoje]` (`filters.js`, `st.dt = today`), entao bilhete datado de amanha cai fora da conta do mes: com elas dentro o mes vai de **-R$ 892,87 para +R$ 35,13**, ou seja **o filtro trocava o SINAL do resultado**. **A causa:** `_dataFimB3` somava ao kickoff uma "folga de encerramento" por esporte (`_OFF_B3`: 2,5 h em basquete, 3 h em tenis) para estimar a liquidacao. eBasket chega da bet365 como `CL=18` — Basquete, porque a casa nao separa os dois; quem separa e o `_e_ebasket` do `app/tradutor.py`, pelo handle do gamer nos dois lados — e levava **2,5 h de folga num jogo que dura ~4 minutos**. **A assinatura, medida:** as 8 foram capturadas entre 22:30 e 22:40 e as 8 ganharam data +1; nenhum dos outros 397 eBasket da base, fora dessa faixa de horario, foi deslocado. **A escala:** todo esporte tinha folga, entao havia uma janela diaria de ~21h a meia-noite. Piso medido (data = dia da captura + 1, capturado depois das 21h): **188 linhas** da Bet365 (73 Multiplos, 54 Futebol, 37 Badminton, 8 Basquete, 8 eBasket, 5 Tenis, 2 Dardos, 1 E-Sports) — e e PISO, porque quem foi capturado no lote da manha seguinte carrega o mesmo deslocamento e o banco nao guarda o kickoff para conferir. **Por que sobreviveu tanto tempo:** o efeito no KPI se desfaz sozinho (amanha 10/09 entra no MTD), so o DIA errado fica — defeito que se apaga da tela toda madrugada nao vira reclamacao, vira desconfianca difusa. **Decisao do Feca: `Data = kickoff`, para todos os esportes** — e o que a tela da bet365 mostra, o que as outras casas gravam e a unica data que o payload tem. A conversao UK->Brasilia NAO e a folga e continua obrigatoria (hora de parede de Londres). O rotulo do bloco virou `Data (evento):`, que ja era o das outras casas de API. **Gate novo** (bloco 9 do `extensor/harness/casos/bet365.mjs`), **provado por 5 mutacoes** — e a 3a ESCAPOU na primeira rodada: fixar `ukToBr = 4` deixava tudo verde porque nos casos escolhidos a diferenca entre UK-3 e UK-4 caia dentro do MESMO dia. O horario de verao britanico so troca o dia na faixa **03:00-04:00 UK**, entao foram precisos um caso em janeiro e outro em julho, ambos as 03:30, para prender o erro nos dois sentidos. **Reparo aplicado:** `scripts/corrigir_data_folga_s339.py` (ensaio por padrao) corrigiu as 8 linhas do Ctrl Alt Green e registrou cada uma em `correcoes`; a prova de que a data certa e o dia da captura e que a linha entrou no banco **ja resolvida**, e bilhete so resolve depois de o evento acabar. Harness 27 casos / 436 bilhetes verde. **Fica aberto:** o `CLAUDE.md` bateu no teto de 65 KB (65,5) e a regra nova nao cabe sem faxina — decisao do Feca, esta no BACKLOG. Outra sessao rodou em PARALELO nesta noite.)

_Anterior: 2026-09-09 (sessao 338: **a Blaze duplicando bilhete, e a causa nao era a Blaze: era a PROCEDENCIA do codigo.** Relato do Jonathan: "a blaze ta puxando bet duplicada, tinha feito isso ontem com prints e agora com a extensao". Medido no banco ANTES de tocar em codigo: o bilhete do Susanto (31/08) estava **5 vezes** na base dele, com **5 codigos diferentes**, um deles gravado literalmente como `270625314492244...` e outros dois com espaco no meio do numero. **Nao e defeito da captura: a Blaze so entrou na captura nesta mesma noite** (commit `d3f2233`, 19:24), entao 100% do que estava no banco veio de PRINT. O discriminador foi o `uso_tokens.n_itens`, que conta imagens + blocos de texto: toda extracao de Blaze anterior tem `n_itens` de imagem, e so a de 20:43 e texto. **O id do BetBy tem 19 digitos e a IA lendo o card erra quase sempre:** 53 dos 55 codigos de Blaze no banco tem comprimento errado (17, 18, 20, 21). Para comparar, Betboom (77 de 77) e Jonbet (18 de 18), que so entram por captura, acertam os 19 digitos em 100%. **Como o codigo entra na assinatura, cada leitura vira um bilhete novo** e o pre-dedup por codigo nunca casa: ao ligar a extensao, o historico inteiro da casa duplicaria. Nao e so o Jonathan (germano tem 20 linhas assim, Jaao26 uma). **Tres frentes.** (1) A coluna `codigo_ocr` carrega a PROCEDENCIA do codigo, decidida no servidor (o `/extrair` e quem sabe se o lote tinha imagem) e transportada pelo front ate o `/salvar`. A formula do ON CONFLICT e um **AND das duas pontas**, entao a confianca so DESCE: basta uma leitura confiavel para o codigo deixar de ser suspeito, e nenhum print o rebaixa de volta. O backfill da Blaze e **deterministico, nao heuristico**: toda linha criada antes do deploy da captura veio de print porque nao existia outro caminho. (2) A **Migracao B'** do UPSERT adota essa linha quando o mesmo bilhete volta pela captura com o codigo verdadeiro, em vez de inserir a sexta. Duas travas que a Migracao B nao tem, porque aqui o candidato CARREGA um codigo e adotar o errado nao duplica, **sequestra** a identidade de outro bilhete: candidato UNICO, e o indice so e montado quando o lote que chega e confiavel (print nao adota print). (3) `scripts/reparar_duplicatas_codigo_ocr.py` une o que ja esta duplicado: ensaio por padrao, escolha pelo valor **MODAL** de stake e odd (com N leituras do mesmo card, a moda e a melhor estimativa que o banco tem, e isso importa porque o UPSERT congela stake/odd em linha resolvida), e snapshot em `lixeira_bilhetes` pelo `DELETE ... RETURNING to_jsonb`, uma operacao so. **Gates:** 789 passed / 36 skipped, **7 de 7 mutacoes detectadas** (`scripts/mutar_codigo_ocr.py`), 6 testes de ponta a ponta no harness de DB, `check-tokens` e `audit_sharpenup` verdes.)

_Anterior: 2026-09-09 (sessao 337: **Blaze na captura automatica — 3a casa BetBy, sem uma linha de inject nova, e um defeito de odd que ela expos nas OUTRAS duas.** O espelho foi provado ANTES de escrever codigo e **sem login**: `/pt/sports` carrega `blaze.sptpub.com/bt-renderer` e o trafego sai em `api-31-sp-c7818b61-584` — **mesmo cluster e mesmo hash de operador da Jonbet**. Reusa `jb_inject.js`, `formatTicketJB` e `roboJBPassive`; mudou o ramo do `iniciarRobo`, o autodiagnostico e os 12 registros. **A varredura ao vivo deu 165 bilhetes** (`status` vazio, 5 cards lidos verbatim) e trouxe quatro achados que o espelho nao dispensava. (1) **A casa IGNORA o `limit` pedido**: pedi 100 e vieram 21 por pagina, oito paginas — quem avanca o `skip` pelo que PEDIU pula 79 por pagina, e o loop so nao quebra porque avanca pelo que VOLTOU. (2) **`total_k` zerou em 86 de 86 perdidas**, a armadilha conhecida da familia. (3) **A NOVA: em 4 dessas 86 o `k` TAMBEM vem zero** e a odd so existe dentro da selecao — **e o card deixa a linha "Total de odds" VAZIA**, ou seja a casa tambem nao tem o numero e nao escreve zero nenhum. Parar no `k` gravaria `0` numa coluna Odd, que e a familia do "zero nao e ausencia": passa em toda checagem de forma porque tem cara de conta feita, e num bilhete GANHO faria `stake x (0-1)` virar -1u. **O `_oddDeclJB` ganhou um terceiro degrau** (`total_k` -> `k` -> produto das selecoes -> `null`, nunca 0) e **conserta as tres casas de uma vez**. (4) `refund`/`canceled` achatam a odd para **1** — e ali o `1` e a VERDADE da tela, entao o degrau novo so pode disparar com os dois campos zerados; o caso trava os DOIS lados. **Gates:** harness 27 casos / 436 bilhetes verde, `audit_sharpenup` sem FAIL, `audit_casas` limpo (**e ele pegou uma categoria que eu inventei** — `Placar Exato` nao existe no MASTER; virou `Outros` mais um item de feedback, sem criar categoria por conta propria), e **mutacao provada nos dois sentidos**: o gate nasceu VERMELHO no bilhete certo e, com o produto vencendo sempre, acende 7 falhas, 2 delas nos `V`. A mesma mutacao passa **inocua** na Jonbet e na Betboom — espelho compartilha o conserto, nao compartilha a prova. **NAO coberto, medido e declarado no cabecalho do caso:** a conta nao tinha aposta ABERTA, cashout, boost, freebet nem sistema (`combinations` vazio em 165 de 165), e 3 dos 8 esperados vieram do corpo da resposta porque os cards de marco estavam ~100 posicoes abaixo e o filtro "Personalizado" da casa travou. **Descoberta de lado:** o BetBy da Blaze renderiza dentro de um **shadow root** — `document.body.innerText` traz 2,9 KB de casca e zero bilhete; casa assim nunca pode ter fallback de texto, porque o robo generico nao falha, ele manda a casca para a IA. **Os dois registros de `app/main.py` foram levados pelo commit da s336**, que estava com o arquivo — o caso 8 de novo, registrado e nao reescrito. Falta a validacao ao vivo, que so o operador faz. A s336 rodou em PARALELO, noutra sessao.)



> **Histórico completo das sessões 332 → 14** → [`docs/HISTORICO.md`](docs/HISTORICO.md)

---

## Onde parei (fim da sessão 339)

### O mês que fechava negativo porque a captura datava 8 vitórias em "amanhã"

**22:50 de 09/09/2026.** O relatório do tipster `Ctrl Alt Green` mostrava **MTD −R$ 892,87**
e a grade trazia oito apostas de eBasket datadas de **10/09** — um dia que ainda não tinha
chegado. Duas perguntas na mesma mensagem, *"o resultado não parece atualizado"* e *"por que
você finalizou apostas com 10/09?"*, e **era o mesmo defeito nas duas**.

As 8 estavam no banco, todas `W`, somando **+R$ 928,00**. O MTD recorta `[1º do mês, hoje]`
(`filters.js`, `st.dt = today`), então bilhete datado de amanhã cai fora. Com elas dentro o
mês vai para **+R$ 35,13**: o filtro trocava o **sinal** do resultado.

### A causa: uma folga que estimava um instante que a casa não informa

`_dataFimB3` somava ao kickoff uma folga de encerramento por esporte (`_OFF_B3`), para
estimar a liquidação. eBasket chega da bet365 como `CL=18` — **Basquete**, porque a casa não
separa os dois; quem separa é o `_e_ebasket` do `app/tradutor.py`, pelo handle do gamer nos
dois lados — e levava **2,5 h de folga num jogo que dura ~4 minutos**.

A assinatura bate: as 8 foram capturadas entre **22:30 e 22:40** e as 8 ganharam data +1.
Nenhum dos outros 397 eBasket da base, fora dessa faixa de horário, foi deslocado.

| Esporte (Bet365) | linhas com data = dia da captura + 1, capturadas após 21h |
|---|---|
| Múltiplos | 73 |
| Futebol | 54 |
| Badminton | 37 |
| Basquete | 8 |
| eBasket | 8 |
| Tênis · Dardos · E-Sports | 8 |
| **total** | **188** |

É **piso**, não total: quem foi capturado no lote da manhã seguinte carrega o mesmo
deslocamento e não entra nessa conta, porque o banco não guarda o kickoff para conferir.

> **Por que sobreviveu tanto tempo:** o efeito no KPI se desfaz sozinho — amanhã 10/09 entra
> no MTD e o número "conserta". O que não se desfaz é o **dia errado**. Um defeito que se
> apaga da tela toda madrugada não vira reclamação, vira desconfiança difusa.

### A decisão: `Data = kickoff`, para todos os esportes

Do Feca. É o que a tela da própria bet365 mostra, o que as outras casas gravam e a única data
que o payload realmente tem. Um jogo que começa 22:00 do dia 09 e termina 00:30 do dia 10 é
do dia 09. A **conversão UK→Brasília não é a folga** e continua obrigatória (o payload traz
hora de parede de Londres). O rótulo do bloco virou `Data (evento):`, que já era o das outras
casas de API — o tradutor casa a chave por prefixo, então nada mais precisou mudar.

Regra em `CASA_BET365 §4` e no `CLAUDE.md`; o caso em [`docs/CASOS.md`](docs/CASOS.md).

### O gate, e a mutação que passou verde

Bloco 9 do `extensor/harness/casos/bet365.mjs`, **provado por 5 mutações**. A terceira
**escapou na primeira rodada**: fixar `ukToBr = 4` (ignorar o GMT do inverno britânico)
deixava tudo verde, porque nos casos escolhidos a diferença entre UK−3 e UK−4 caía **dentro
do mesmo dia**. O horário de verão britânico só troca o **dia** na faixa **03:00–04:00 UK**,
então foram precisos um caso em janeiro e outro em julho, ambos às 03:30, para prender o erro
**nos dois sentidos** — com um só, metade do defeito passa.

É o segundo modo de falso verde do `CLAUDE.md` ("o dado sintético não exerce a regra")
aparecendo num teste escrito **na mesma sessão** que a regra.

### O reparo

`scripts/corrigir_data_folga_s339.py`, ensaio por padrão. Corrigiu as **8 linhas** do
Ctrl Alt Green e registrou cada uma em `correcoes`. A prova de que a data certa é o dia da
captura, e não um palpite: a linha entrou no banco **já resolvida**, e bilhete só resolve
depois de o evento acabar — logo o evento é anterior à captura.

Quatro travas, todas fail-closed: só linha **com código** (sem código a `data` entra na
assinatura), só onde a data é posterior ao dia da captura, pula bilhete com correção humana
em `data`, e escopo explícito obrigatório (`--dono` + `--tipster`).

O UPSERT congela `data` em linha resolvida, então **recapturar não conserta** o que já está
gravado. Foi por isso que precisou de script.

> **Fica aberto:** o `CLAUDE.md` bateu no teto de 65 KB (está em 65,5) e a regra nova não cabe
> sem faxina. Não há duplicação a mover — medido: zero frases longas repetidas entre ele e o
> `CASOS.md`. Qual regra sai é decisão do Feca. **Não foi para o `BACKLOG.md` de propósito:**
> outra sessão estava com esse arquivo modificado na mesma noite, e levá-lo no commit seria o
> caso 8 (invariante #8). Registrado aqui até o arquivo liberar.

---

## Sessão 338 — a Blaze e a procedência do código

### A Blaze duplicando bilhete, e a causa não era a Blaze

O relato do Jonathan: *"a blaze ta puxando bet duplicada, tinha feito isso ontem com
prints e agora com a extensao"*. A causa não é a captura nova: é **quem leu o número do
código**.

O `codigo_bilhete` entra na assinatura (`ID|casa|parceiro|codigo`), então um dígito trocado
é um bilhete NOVO. Só que ele nem sempre vem da mesma fonte:

| Fonte | De onde sai o código | Acerto medido |
|---|---|---|
| captura (texto do robô) | `[Código: …]`, exato da API | Betboom 77/77, Jonbet 18/18 |
| print (imagem) | a IA lê o número no card | Blaze **2 de 55** |

Na base do Jonathan o mesmo bilhete estava **5 vezes**, com 5 códigos diferentes:

```
Susanto, Yulia Yosephine · 31/08 · stake 200 · odd 1,85 · W
  #212907 [20] 27063531449244906924   01/09   print
  #216590 [19] 2706253144924498034    02/09   print
  #218223 [18] 270625314492244...     03/09   print   ← a IA escreveu as reticências
  #257345 [20] 27062531440244968824   09/09   print
  #258494 [19] 2706253144924496624    09/09   print
```

**Nada disso veio da extensão.** A Blaze entrou na captura nesta mesma noite (`d3f2233`,
19:24), e o discriminador é o `uso_tokens.n_itens`, que conta imagens + blocos de texto:
toda extração de Blaze anterior é de imagem, e só a de 20:43 é texto. Foi ela que o
Jonathan viu duplicar na tela, e ele parou antes de salvar (nenhuma linha nova entrou).

### O que mudou

**1. A procedência do código passa a existir** (`bilhetes.codigo_ocr`). Quem decide é o
servidor, no `/extrair`, que é quem sabe se o lote tinha imagem; o front só transporta o
flag até o `/salvar`. A fórmula do `ON CONFLICT` é um **AND das duas pontas**, então a
confiança só desce: uma leitura confiável limpa o código para sempre, e nenhum print o
rebaixa de volta. O backfill da Blaze é **determinístico**, não heurístico: linha criada
antes do deploy da captura veio de print porque não existia outro caminho.

**2. A Migração B' adota em vez de duplicar.** Quando o bilhete volta pela captura com o
código verdadeiro, a linha antiga é adotada (código novo + assinatura nova + `codigo_ocr`
limpo). Duas travas que a Migração B não precisa ter: **candidato único** e **índice só com
lote confiável**. O motivo é que o candidato daqui CARREGA um código próprio, então adotar
o errado não duplica, sequestra a identidade de outro bilhete.

**3. O que já está duplicado sai pelo script**, com olho humano:
`scripts/reparar_duplicatas_codigo_ocr.py` (ensaio é o padrão). Ele agrupa por descrição
normalizada, mostra o P/L de cada linha e escolhe pelo valor **modal** de stake e odd, que
importa porque o UPSERT congela stake/odd em linha resolvida: o valor da linha que fica é o
que permanece. Saída para `lixeira_bilhetes`, pelo `DELETE … RETURNING to_jsonb` numa
operação só.

### Aplicado em produção

A migração marcou as **55** linhas de Blaze e o reparo moveu **4** para `lixeira_bilhetes`:
o grupo do Susanto, na conta do Jonathan, que eram **R$ 679,62 de lucro que nunca existiu**.
Quatro leituras concordavam em 200,00 / 1,85 e uma divergia, então a moda decidiu sozinha.
O ensaio agora devolve `0 grupo(s) duplicado(s)`, e sobrou **candidato único** para a
Migração B' adotar quando a captura passar.

germano (20 linhas com código torto) e Jaao26 (1) **não** tinham duplicata: leram cada
bilhete uma vez só. Código errado não é duplicata, é dívida esperando a captura.

### Gates

| Gate | Resultado |
|---|---|
| `pytest tests/` | 789 passed / 36 skipped |
| `python scripts/mutar_codigo_ocr.py` | **7 de 7** mutações detectadas |
| `tests/test_repository_db.py` | 6 casos novos de ponta a ponta (só no CI) |
| `check-tokens` · `audit_sharpenup` | verdes |

O que os testes de forma **não** cobrem está escrito no cabeçalho deles: adotar, recusar o
ambíguo e não rebaixar o confirmado exigem Postgres e vivem no harness de DB.

---

## Sessão 337 — a Blaze na captura

### Blaze: a terceira casa BetBy, e o degrau de odd que ela expôs nas outras duas

Detalhes em [`casas/CASA_BLAZE.md`](casas/CASA_BLAZE.md). O espelho foi **provado antes de
escrever código e sem login**: `/pt/sports` carrega `blaze.sptpub.com/bt-renderer`, e o
tráfego sai em `api-31-sp-c7818b61-584` — **mesmo cluster e mesmo hash de operador da
Jonbet**. Zero arquivo de captura novo: reusa `jb_inject.js`, `formatTicketJB` e
`roboJBPassive`.

Varredura ao vivo de **165 bilhetes** (`status` vazio), com 5 cards lidos verbatim na tela.

### O achado que muda código: a odd que a casa NÃO tem

`total_k` veio `"0"` em **86 de 86 perdidas** — a armadilha conhecida da família. A nova é
que **em 4 dessas 86 o `k` também vem zero**, e a odd só existe dentro da seleção.

E o card concorda com a API: a linha **"Total de odds" aparece VAZIA**. A casa também não
tem o número, e não escreve zero nenhum.

Parar no `k` gravaria `0` numa coluna Odd. É a família do *"zero não é ausência"*: o `0`
passa em toda checagem de forma porque tem cara de conta feita — e num bilhete **ganho**
faria `stake × (0 − 1)` virar `−1u`. O `_oddDeclJB` ganhou um terceiro degrau:

```
total_k, se ≠ 0  →  k, se ≠ 0  →  produto das seleções, se todas > 0  →  null (nunca 0)
```

**Conserta as três casas de uma vez.** E o degrau só pode disparar com os dois campos
zerados: em `refund`/`canceled` a casa achata a odd para **1** e ali o `1` é a verdade da
tela — o produto das pernas (2,5 · 1,5) seria invenção nossa por cima do card. O caso do
harness trava os **dois** lados.

### O que a paginação ensinou

Pedi `limit=100` e a Blaze devolveu **21 por página**, oito páginas, `count` constante em
165. A casa **ignora o `limit` pedido**. Quem avança o `skip` pelo que pediu pula 79
bilhetes por página; o loop do `jb_inject` só não quebra porque avança pelo tamanho que
**voltou**.

### Gates, e as duas coisas que eles pegaram

| Gate | Resultado |
|---|---|
| `node extensor/harness/run.mjs` | verde — 27 casos, **436 bilhetes** |
| `python tools/audit_sharpenup.py` | sem FAIL |
| `python tools/audit_casas.py` | limpo |
| `pytest tests/` | 773 passed (as falhas restantes são da s336, em curso noutra sessão) |

O `audit_casas` **pegou uma categoria que eu inventei**: `Placar Exato` não existe no
`MASTER_APOSTAS §3`. Virou `Outros ⚠️` mais um item de feedback no rodapé do arquivo da
casa — criar categoria é decisão do Feca e arrasta a propagação inteira.

E a **mutação foi provada nos dois sentidos**: o gate nasceu **vermelho** no bilhete certo
e, com o produto vencendo sempre, acende 7 falhas — 2 delas exatamente nos `V`. A mesma
mutação passa **inócua** na Jonbet e na Betboom: espelho compartilha o conserto, não
compartilha a prova.

### O que NÃO está coberto (medido, e escrito no cabeçalho do caso)

A conta não tinha **aposta aberta**, **cashout**, **boost**, **freebet** nem **sistema**
(`combinations` vazio em 165 de 165). E 3 dos 8 valores esperados vieram do corpo da
resposta, não do card: os bilhetes de março estão ~100 posições abaixo na lista e o filtro
"Personalizado" da casa travou carregando nas duas tentativas.

**Descoberta de lado:** o BetBy da Blaze renderiza dentro de um **shadow root** —
`document.body.innerText` traz 2,9 KB de casca e nenhum bilhete. Casa assim nunca pode ter
fallback de texto: o robô genérico não falharia, ele mandaria a casca para a IA.

**Pendente:** a validação ao vivo (recarregar a extensão, Ctrl+Shift+R na aba da Blaze e
capturar), que só o operador faz.

### Duas sessões, um index: os registros de `app/main.py` foram levados pela s336

Aconteceu de novo o [caso 8](docs/CASOS.md#8--duas-sessões-commitando-ao-mesmo-tempo-24082026),
e desta vez a favor: os dois registros da Blaze em `app/main.py` (`_CASA_DISPLAY` e
`_CASAS_MARCADOR_CODIGO`) entraram no commit `2143c06` da s336, que estava com o arquivo
para a Fase 1 da barreira. **Histórico já enviado não se reescreve** — fica registrado aqui
e segue. O resto dos 12 pontos veio no commit desta sessão.

Vale a lição inversa da regra: quando o arquivo é o MESMO, `git add` por nome não separa
nada. Antes de editar `main.py` com outra sessão aberta, o barato é combinar quem leva.

---

## Sessão 336 — a barreira de recaptura, Fase 0

### A barreira de recaptura: Fase 0 no ar, medindo sem filtrar

O plano inteiro está em
[`docs/PLANO_BARREIRA_RECAPTURA.md`](docs/PLANO_BARREIRA_RECAPTURA.md). Ele nasceu de uma
pergunta do Feca que virou medição.

**O problema, medido:** toda captura vai inteira para a IA, e a dedup só acontece depois,
no `upsert`. Dos 15.318 blocos com código que passaram pela IA em 13 dias, **4.975
(32,5%) eram releitura de bloco byte a byte idêntico**. Na Bet365, 39,9%.

| | Blocos | % |
|---|---|---|
| Primeira leitura | 8.753 | 57,1% |
| **Releitura IDÊNTICA** | **4.975** | **32,5%** |
| Releitura de bilhete que mudou | 1.590 | 10,4% |

### Por que hash do bloco, e não (código, resultado)

A proposta original era conferir ID e resultado. Medida contra o hash do bloco inteiro,
as duas decidem igual em **97,7%** dos casos. Nos 2,3% restantes o bloco mudou com o
`Status:` igual, e a chave por rótulo pularia.

Mas o argumento que decide é outro: **o texto de status não é fonte confiável de estado.**
`_resultadoB3` escreve `Ganho → W` para qualquer retorno maior que a stake, meia vitória
inclusive. Chave que lê rótulo herda esse defeito; chave que compara bytes não tem o que
herdar. É o mesmo princípio do "o rótulo não é a prova, o número é".

E liquidar não mexe só no status. Caso real da Novibet: a odd vai de `4,59` (potencial)
para `2,89` (`Retorno ÷ Stake`) na mesma leitura.

### O ganho, e o que ele NÃO é

Simulação lote a lote, com modelo calibrado nos agregados de `uso_tokens` e **validado
contra a conta real: erro de +4,5%**.

| | Hoje | Pós-barreira |
|---|---|---|
| Conta de API | US$ 391/mês | **US$ 281/mês** |
| Custo por bilhete | R$ 0,092 | **R$ 0,065** |

**Velocidade quase não muda, e isso está escrito no plano de propósito.** A mediana fica
em 30,5s: os pedaços já correm em paralelo, então o relógio é o tempo de UM pedaço vezes o
número de ondas, e uma extração de 20 bilhetes vira 4 pedaços antes e depois. Só o p99 cai
43,7%. O ganho real é a extração que fica **vazia** (30s viram menos de 1), que hoje seria
2,3% delas — número subestimado, porque reflete o hábito de quem paga caro para
recapturar.

### A Fase 0 não filtra nada, e é para isso que ela existe

Tabela `bloco_visto`, gravação do hash no `done` da extração, e um log dizendo quantos
blocos **seriam** pulados. Serve para conferir em produção o número da simulação **antes**
de qualquer byte deixar de ser processado.

### As quatro costuras da Fase 1, todas silenciosas se erradas

Estão no `§6` do plano. Nenhuma dá erro; todas dão dado faltando em silêncio.
`conferir_cobertura` precisa saber do filtro (senão acusa perda que não houve);
`_reconciliar_orfas` precisa ver **todos** os blocos, não só os filtrados (senão uma órfã
perde a adoção e vira fantasma, o caso do Falkirk); bilhete sem código não passa pela
barreira; e lote vazio é sucesso, não erro.

### O custo remedido por usuário e por casa: existe um driver único

O custo por bilhete é quase inteiramente função de **bilhetes por chamada**, porque o
manual de 48k tokens é relido a cada pedaço.

| | R$/bilhete | Bilhetes por chamada |
|---|---|---|
| perereca | 0,037 | 55,9 |
| Feca | 0,102 | 12,2 |
| Marques19981 | **0,414** | 2,4 |

**E a Bet365 não é cara, ela é grande:** R$ 0,080 por bilhete, **abaixo** da média de
R$ 0,092 e a mais barata entre as casas de volume. É 42% da conta por volume, não por
ineficiência. A cara é a KTO, R$ 0,429 com 1,7 bilhete por chamada.

> Isso corrige a leitura do `ESTUDO_PRECIFICACAO §1.3`, que listava a Bet365 como o topo
> do custo sem separar volume de eficiência.

---

## 1. O que estamos construindo

A base de conhecimento (masters) do scanner de bets. Camada **global** (regra única, muda devagar) + camada **por casa** (traduz cada casa para a língua global). A saída final é **TSV**.

---

## 2. Invariantes (não se quebram)

1. O app **lê** os masters, **nunca escreve** neles. Mudança de regra = diff revisado por humano + commit. Git é a porta de aprovação.
2. O arquivo de casa **traduz** a casa para a língua global; **não redefine** regra global.
3. **Cálculo é global, localização é da casa.** Ex.: "W → Retorno÷Stake" é global; "o retorno está no campo PRÊMIO" é da Superbet.
4. Nenhuma regra nova é aplicada sozinha. Propor como diff, esperar aprovação.

---

## 3. Estrutura-alvo do repo

```
/global/                 (autoridade única — 6 masters)
    MASTER_PIPELINE_2026.md
    MASTER_ESPORTES_2026.md
    MASTER_APOSTAS_2026.md
    MASTER_DESCRICAO_2026.md
    MASTER_RESULTADO_2026.md
    MASTER_OUTPUT_2026.md
/casas/                  (1 arquivo por casa — traduz, nunca redefine)
    CASA_MODELO.md         (gabarito — 15 seções)
    CASA_BET365.md
    CASA_BETANO.md
    CASA_BETESPORTE.md
    CASA_BETFAIR.md
    CASA_BETNACIONAL.md
    CASA_BOLSADEAPOSTA.md
    CASA_KINGPANDA.md
    CASA_KTO.md
    CASA_LOTTU.md
    CASA_NOVIBET.md        (plataforma própria BlueBrown — replay que ALARGA o filtro)
    CASA_PINNACLE.md
    CASA_PITACO.md         (ex-"Rei do Pitaco" — gRPC-Web/protobuf; 2 grafias, 1 manual)
    CASA_POLYMARKET.md     (por API, não IA)
    CASA_SUPERBET.md
    CASA_TIVO.md
    CASA_BETFAST.md        (espelho técnico da Tivo — mesmo motor BetConstruct)
    CASA_JONBET.md
    CASA_BETBOOM.md        (espelho técnico da Jonbet — mesmo motor BetBy/sptpub)
    CASA_VAIDEBET.md
    CASA_ESPORTIVA.md      (espelho técnico da VaideBet — mesmo motor Altenar/BIA)
    CASA_JOGODEOURO.md     (3ª casa Altenar — captura na TELA CHEIA do histórico)
    CASA_BETPIX365.md      (4ª casa Altenar — a casa NÃO chama o endpoint que ela precisa)
    CASA_ESTRELABET.md     (5ª casa Altenar — a mais lisa na tela; o gateway recusa credencial)
    CASA_STAKE.md          (mesma Kambi da KTO, mas REST próprio — captura NÃO é espelho)
    CASA_VITORIABET.md
/golden_set/
    bilhetes/              (print + TSV esperado)
/docs/                   (guias, referências, ADRs, planos VIVOS — índice em docs/README.md)
    CASOS.md               (os casos que originaram as regras do CLAUDE.md; não auto-carregado)
    HISTORICO.md           (índice) → historico/  (6 partições por faixa de sessão)
    arquivo/               (o que virou registro; índice em arquivo/README.md)
CLAUDE.md                  (regras vinculantes)
STATUS.md                  (este arquivo — estado atual + as 3 últimas sessões)
BACKLOG.md                 (tudo que está aberto)
```

**Um arquivo, uma pergunta** (invariante #10), com gate em `python tools/check_docs.py`.

Os 6 MASTER_*.md vivem em `/global/`; as **28** casas em `/casas/` (Polymarket por API, as demais por IA/texto), mais o gabarito `CASA_MODELO.md`.

---

## 4. Estado atual

- **Produto no ar** em `sharpen.bet` (dashboard + extração); deploy automático via Railway.
- **Multi-tenant:** vários donos (Feca, Fatuch, Diogo, Jonathan, Lava, LavaPessoal…) + operadores; dados isolados por `dono` no Postgres (regras de tenancy/dedup no `CLAUDE.md`). Identidade na tabela `usuarios` do Postgres via cache em memória (s233 — Fase 1 do `docs/PLANO_MULTIUSUARIO_2026.md`); os dicts de `app/auth.py` são a SEMENTE. Conta nova = 1 linha em `USUARIOS` (`app/auth.py`) + `SENHA_<USER>_HASH` no Railway (o seed leva ao banco no boot); base nasce vazia sem migration. Suspender no banco (`status`) revoga login E sessão em ≤60s.
- **Base do Feca:** migração planilha → Postgres **completa e reconciliada**.
- **Base do `LavaPessoal` (s222):** 2.877 apostas importadas do `.xlsx` pessoal do Lava (23/02 → 30/07/2026), `origem='import'`, conta `Padrão` em cada uma das 19 casas (ele não anota fornecedor). Script próprio e idempotente: `scripts/import_lavapessoal_xlsx.py` (re-rodar limpa só `origem='import'` daquele dono; captura da extensão sobrevive). **Não confundir com o dono `Lava`** — são bases distintas que só compartilham o apelido. **O P/L do dashboard não bate com a planilha de origem por desenho** (ela contabiliza em unidade; ver s222 no topo).
- **Base do `SoChutes` (s224):** 23.199 apostas all-time do tipster Só Chutes (17/09/2024 → 27/07/2026) importadas do `.xlsx`, `origem='import'`, conta `Padrão` (Bet365/Superbet/Betano; casa não informada entrou como Bet365 — decisão do Feca). **Stake em UNIDADES** (1u = 1; o P/L do dashboard é o P/L em unidades: +1.381,29u). Script idempotente: `scripts/import_sochutes_xlsx.py`. O planilhamento novo é do **bot Sharpen** (repo próprio `BOTS/sharpen-bot`, ver s223), que desde a **s251** roda 24/7 no Railway — serviço `sharpen-bot`, no mesmo projeto do app, com o estado em volume próprio. Ele escreve nesta base por `/salvar` + `/bilhetes/tipster`: **mudança no contrato dessas rotas quebra o bot em silêncio.**
- **Base do `Flurray` / tipster Fleury (s260):** 473 apostas (11/06 → 09/08/2026) importadas do `.xlsx`, `origem='import'`, conta `Padrão` em cada uma das 4 casas (Bet365, Betano, Superbet, BetMGM). Base de **nicho**: 100 % mercados de finalização no futebol. **Stake em UNIDADES** (1u = 1; P/L +122,30u sobre 447,80u de turnover). Script idempotente: `scripts/import_fleury_xlsx.py`. **⚠️ A marca é `Fleury` e o username é `Flurray`** — o `dono` é sempre o username; a ponte entre os dois é o `TIPSTERS_PUBLICOS`. Conta criada pelo próprio usuário no site e aprovada pelo Feca (Fase 2): **sem env var, sem linha em `app/auth.py`**. Página pública: **`/tipsters/fleury`** (3ª do sistema).
- **Base do `passapano` / tipster PassaTips VIP (s273):** 911 apostas (02/06 → 17/08/2026) importadas do `.xlsx`, `origem='import'`, conta `Padrão` em cada uma das 7 casas (Bet365, Betano, Betnacional, Betvip, Estrela Bet, Novibet, Suprema Bet). Base **multiesporte**: 20 esportes, de futebol e tênis a polo aquático e críquete. **Stake em UNIDADES** (1u = 1; P/L +90,20u sobre 1.102,61u de turnover liquidado). Script idempotente: `scripts/import_passatips_xlsx.py`. **⚠️ A marca é `PassaTips VIP` e o username é `passapano`** — mesmo caso do Fleury. Conta criada pelo próprio usuário no site e aprovada pelo Feca (Fase 2): **sem env var, sem linha em `app/auth.py`**. Página pública: **`/tipsters/passatipsvip`** (5ª do sistema). O planilhamento novo é do **bot Sharpen** (4º tenant, `passatips`) — **1º perfil sem visão**, porque a legenda dele já traz tudo.
- **Casas:** 28 arquivos em `casas/` (extração por IA/texto) + **Polymarket** por API.
- **Fatuch:** dashboard lê a planilha viva do LavaFatuch via Apps Script (leitura por **cabeçalho**, não por posição); coluna `Espelho` = fornecedor. Sem base no Postgres (tudo vem da planilha).
- **Captura:** extensão **SharpenUp** (moldura+Snap e robô de rolagem) no ar, pareando por código. **25 casas por API** (injetor no mundo MAIN, dado exato): Superbet, BETesporte, Betano, Betfair, Pinnacle, Bet365, KTO (Kambi, s192), Tivo (s196), VaideBet (Altenar, s210), **Betfast** (s211 — **espelho da Tivo**: mesmo motor BetConstruct, mesmo `tv_inject.js`), BetNacional, Jonbet (BetBy/sptpub, s248), **Betboom** (s250 — **espelho da Jonbet**: mesmo motor BetBy, mesmo `jb_inject.js`) **Pitaco** (s270 — plataforma própria, **gRPC-Web/protobuf binário**, replay puro) **Novibet** (s271 — plataforma própria BlueBrown, replay puro que **alarga o filtro** da tela: ela pede 24 h e só as fechadas) e **Estrela Bet** (s303 — **5ª casa Altenar**, mesmo `vb_inject.js`; a mais lisa na TELA e a única cujo gateway **recusa `credentials:"include"`**). **Dois pares de espelho, zero código duplicado** — o inject casa por caminho de API, nunca por host, e é isso que faz a casa seguinte da mesma plataforma custar registro em vez de implementação.
- **Apostas em aberto (s215):** o feed (`dashboard_rows`) carrega a aposta não liquidada marcada `resultado='ABERTA'`, `lucro=0`. Ela aparece no topo da **Minha Base** (ex-"Apostas") e tem tela própria em **Minhas Apostas › Em Aberto** (`charts/abertas.js`): KPIs de exposição, horizonte por faixa de dia, calendário por data do evento, barras por casa e por tipster, lista completa. **Nenhuma métrica a soma** — `aplicarFeed` separa `DADOS` (encerradas) de `DADOS_ABERTAS`, e Início/Extração cortam por `resultado==='ABERTA'`.
- **Modelo de extração:** Sonnet 4.6 (`config.py`).

---

## 5. Pendências

> **As pendências mudaram de casa.** Elas moram em **[`BACKLOG.md`](BACKLOG.md)**, na raiz —
> organizadas por natureza (bloqueado por humano · por amostra · decisão do Feca · dívida
> técnica medida · planos com fase aberta · não medido), com as marcas
> **VIVA / NÃO-MEDIDA / HUMANA** da varredura da s261 preservadas.
>
> Motivo: o §5 tinha **51 KB** e ficava atrás de 124 KB de changelog. Quatro arquivos
> disputavam o papel de "onde o projeto está" e três descreviam o projeto de julho. Ver
> [`docs/FAXINA_PROPOSTA.md`](docs/FAXINA_PROPOSTA.md).
>
> **Pendência nova vai para o `BACKLOG.md`, nunca para cá** (invariante #10 do `CLAUDE.md`).
> Gate: `python tools/check_docs.py`.

As três mais quentes de hoje, com o resto no `BACKLOG.md`:

1. **`apps_script/Code_LavaFatuch.gs` expõe a base do Fatuch sem autenticação nenhuma.**
   `doGet(e)` na linha 95, zero token ou segredo no arquivo — e é a fronteira que alimenta o
   `app/planilha_viva.py`, a base financeira **ao vivo** de um cliente. Qualquer um com a URL
   lê. Medido em 06/09. → `BACKLOG §4.3`, e é sessão própria.

2. **PassaTips: 3 passos humanos para fechar o buraco do #259, e a ORDEM importa.**
   Enquanto o painel do #259 estiver armado, um clique ✅ vira o `L` do dia 17 em `W`
   (`resultado` não é congelado). O `/anular #259` **apaga** a linha `Under 1.5 cartões
   Elche`, então o tipster tem de repostar **antes**. → `BACKLOG §1`.

3. **Polymarket ainda mistura `entry_odd` e `realized_odd`** (`AUDITORIA_2026 #32`).
   `_calc_odd` (`app/polymarket.py:894`) devolve um número só, e o próprio comentário da
   `:987` admite "odd de entrada, **ou** a efetiva na liquidação". É o maior risco quant
   aberto e mexe em P/L. → `BACKLOG §4.1`.

---

## 6. Rodar / produção

**App em produção:** `https://sharpen.bet/` (www.sharpen.bet → Railway)

Para rodar localmente:
```
cd app
pip install -r requirements.txt
# .env na raiz do Planilhador com ANTHROPIC_API_KEY e DATABASE_URL
uvicorn main:app --reload
# Abrir http://localhost:8000
```

---

## 7. Workflow

- **Backup antes de editar** — sempre em `Planilhador/Backups/<nome-descritivo>/`. Nunca usar `FDC Capital/Backups/` (é compartilhada por outros projetos da empresa).
- Arquivos completos, nunca diffs parciais.
- Uma mudança por etapa aprovada.
- Atualizar este STATUS.md ao fim de cada etapa.
- Projeto tem git + GitHub (`flrcarvalho/sharpen`, renomeado de `extrator` na sessão 129). Deploy automático via Railway conectado ao GitHub — push dispara deploy.
