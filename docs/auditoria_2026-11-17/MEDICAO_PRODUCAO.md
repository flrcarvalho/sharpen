# Medição da produção (17/11/2026, sessão 460)

Primeira medição da produção depois da auditoria de 17/11. Autorização do Feca: **só
leitura**. Banco por `DATABASE_PUBLIC_URL` numa conexão com
`default_transaction_read_only=on` e cada consulta numa transação `READ ONLY`; logs por
`railway logs`. Nenhuma escrita, nenhum redeploy, nenhum segredo impresso.

**Harness:** [`tools/medicao_producao/`](../../tools/medicao_producao/README.md). A régua de
"liquidou na casa" é a do próprio servidor: o cru guardado passa por `ficha.montar_ficha` e
`ficha.derivar`, rodados localmente. Nada aqui é palpite por casa.

Instante da medição: 17/11/2026, entre 20:00 e 21:00 UTC. Logs HTTP cobrem de 16/11 ~03h UTC
até 20:37 UTC (os deploys de 15/11 já não aparecem na lista da Railway); logs de aplicação,
de 17/11 09:36 UTC em diante.

---

## Resumo

| # | Pergunta | Resposta |
|---|---|---|
| 1 | Liquidadas na casa, abertas no Sharpen | **9 apostas**, todas do arrudex na Thunderpick (9 perdidas, R$ 1.274,22 de stake). Mais **13 que nem existem** no Sharpen, do arrudex, de hoje |
| 2 | Caixas divergindo | Entre usuários ativos: **2** (as duas Kalshi). As outras 31 divergentes são do `realtrial`, de 14/09. Mas as conferências do mês divergem muito (abaixo) |
| 3 | As correções de hoje funcionam? | Sim, com **um defeito novo** na 2.4: captura enviada para sessão encerrada some com 200 |
| 4 | Versões do SharpenUp | Só 1 dos 7 donos com captura em 30 dias já mandou 0.7.88, e só numa casa. Três donos rodam **várias cópias** ao mesmo tempo |
| 5 | arrudex e Gabriel | arrudex: câmbio bloqueado + a parte da IA esperando um "Processar" que não veio. Gabriel: banco bate com a casa aposta a aposta; a Caixa diverge por dinheiro que entrou sem lançamento |

---

## 1. Estoque "liquidada na casa, aberta no Sharpen"

Método: as 927 apostas com `extraction_state = 'aberta'` (ou resultado vazio) e, para cada
uma, o cru mais recente do mesmo dono e código em `captura_crua`, passado pelo adaptador da
família.

| Situação | Apostas |
|---|---|
| Sem cru (casa de texto/print, ou captura nunca ligada) | 806 |
| Cru diz **aberta** também na casa | 94 |
| Cru recusado pelo adaptador (`bilhete sem iid`, `multiple sem amostra`, `pending`) | 18 |
| **Cru diz liquidada, banco diz aberta** | **9** |

As 9 são do **arrudex, Thunderpick**, códigos `C2299104` a `C2299138`, eventos de 16/11,
todas **L** no cru, stake de 22,71 a 22,72 EUR cada (R$ 1.274,22 no total, P/L real
−R$ 1.274,22 que o Sharpen ainda não conta).

**Causa, provada no código e nos dados:**

1. 15:49 UTC: o cru delas chega liquidado; a Ficha monta, o `/salvar` interno recusa por
   "sem cotação EUR→BRL" (o BCB bloqueando a Railway, s458); `ficha_virada` fica
   `ia / recusada no /salvar`; o cru é marcado `processado_em`.
2. 18:51 UTC: o PTAX já está semeado. O mesmo cru chega **idêntico**; `gravar_cru` não
   devolve id (já existe e já foi processado) e `ficha._processar` pula
   (`app/ficha.py:607`, "cru igual ao já guardado: a Ficha dele já foi montada").
3. A rota da IA, que pegaria essas 9, depende de um `/extrair`, e ele não veio (item 5).

É a família R2 do plano: **"processado" foi tratado como "está na planilha"**.

### 1b. A outra metade: liquidadas na casa e AUSENTES do Sharpen

Códigos com registro em `ficha_virada` e nenhuma linha em `bilhetes` (673), classificados
pelo cru: 280 estão na lixeira (exclusão do dono, fora da conta), 237 têm cru recusado, 10
estão abertos. **163 estão liquidadas no cru e não existem no banco.**

| Dono / casa | Liquidadas ausentes | De quando | Leitura |
|---|---|---|---|
| arrudex / Thunderpick | 10 | eventos de 13 a 16/11, cru de hoje | foram à IA (`termo fora do dicionário`), `/extrair` nunca veio |
| arrudex / 20bet | 3 | 14 e 15/11, cru de hoje | idem |
| arrudex / Megapari, MyStake | 6 + 2 | outubro, cru de 13/11 | contas **arquivadas** |
| Jonathan / Stake.com | 34 | **2024** | histórico antigo, `nao_lida` |
| LavaPessoal / MyStake | 46 | outubro | cru de 18 a 21/10, nenhuma linha nas datas |
| Jaao26 / Shuffle | 43 | set-out | cru de 14/10, nenhuma linha nas datas |
| Gabriel, Feca | 1 + 1 | 2024 e 2025 | histórico antigo |

Conferi alias de código cruzando stake, odd, resultado e data com as linhas do mesmo dono e
casa: nenhuma casou. As do arrudex de hoje são **defeito** (mesma causa do item 1). As
antigas são **candidatas**: podem ser escolha do dono (histórico que ele não quis) e pedem
olho humano antes de qualquer correção.

### 1c. O que NÃO é este defeito

- 260 abertas de Bet365 do `realtrial` (eventos de agosto e setembro), 56 do `perereca`, e
  outras de setembro: o dono **não recapturou** depois do evento.
- 90 do Jaao26 na Cloudbet: extração por **print** (códigos `CLO-0292` gerados pelo Sharpen).
- 187 do WilliamOliveira na Lottu: sem data, de agosto.
- Uma do Gabriel na Stake.com (13/11): o cru de hoje diz `active = true`, perna ao vivo.

---

## 2. Caixas divergindo

Estado de cada conta com movimento na Caixa, calculado pela função do servidor
(`repository._caixa_projetar`) sobre os dados de produção.

| Estado | Contas |
|---|---|
| nunca conferida | 235 |
| confere | 188 |
| **divergente** | 33 (31 do `realtrial`, conferidas em 14/09, quase todas arquivadas) |
| reconferir | 3 (todas arquivadas) |

Divergentes de usuário ativo: **Feca / Kalshi, +29,99 USD** (conferida 10/11) e
**Jaao26 / Kalshi, +39,91 USD** (13/11). As duas são a conferência automática da Kalshi.

**O número que importa é o histórico, não a última:** desde 01/10, fora o `realtrial`:

| Dono | Conferências | Divergiram (≥ 1) | Soma absoluta |
|---|---|---|---|
| Jaao26 | 48 | 29 | 6.087,94 |
| Feca | 28 | 18 | 7.443,73 |
| Gabriel | 24 | 12 | 3.931,80 |
| Jonathan | 5 | 5 | 1.718,61 |

Metade das conferências não bate, e o "confere" de hoje é em boa parte **Ajuste que
fechou a diferença** (decisão de 29/09, "ajustou, conciliou"). O estado não mente, mas não
diz se a conta bate *sem* ajuste.

---

## 3. As correções de hoje em produção

| Item | Medido | Veredito |
|---|---|---|
| 2.4 sessão e fila no Postgres | `captura_sessao` com as 2 sessões vivas (arrudex 0.7.86, Gabriel 0.7.88); `captura_fila` vazia, nada sem ack há > 10 min | funciona, **com 1 defeito** (abaixo) |
| 5.1 `bilhetes.lido_em` | 1º preenchimento 18:51:56 UTC; das escritas depois do deploy, **0** sem `lido_em` (extração e Ficha, 4 donos) | funciona |
| 5.3 `captura_crua.processado_em` | 0 crus sem marca (nenhum preso há > 10 min) | funciona |
| Erros HTTP desde 15h BRT | 2.103 requisições: **0 × 5xx**, 13 × 401 (12 `validar` antes de parear, o fluxo normal; 1 `ficha`, abaixo), 2 × 404 de robots/favicon | limpo |
| Erros HTTP desde 16/11 03h UTC | 68 × 401 `validar` (fluxo normal), 59 × 401 `/changelog` (curl manual, um IP, uma hora), 1 × 400 `/salvar` (Gabriel, 17:44, validação de 1,2 KB), 10 × 499 (cliente fechou) | limpo |
| 400 "Part exceeded" (7.1) | nenhum | nenhum caso |
| 426 versão mínima (3.3) | nenhum | ninguém barrado |
| PTAX (s458) | "sem cotação" 101 vezes entre 14 e 17h UTC, **zero** depois das 17h | resolvido |

**Defeito novo (2.4):** 17:55:41 UTC, o dashboard do arrudex encerrou a sessão no mesmo
instante em que a extensão enviou uma captura para ela. O `INSERT` em `captura_fila` bateu
na FK (`sessao_id` já não existia), o servidor registrou
`captura: persistência indisponível (enfileirar captura); seguindo só em memória` e
**respondeu 200**. A captura ficou na memória de uma sessão morta: a extensão mostra
"enviado ✓" e ninguém a lê. O `/captura/ficha` seguinte tomou 401. É a família R1 numa
corrida estreita; o conserto é responder como sessão inexistente (404) e a extensão
reconectar.

---

## 4. Versões do SharpenUp

A extensão atual é a **0.7.88**. Não há `EXT_VERSAO_MINIMA` configurada; só Thunderpick
(0.7.86) e GiroCerto (0.7.84) cobram mínima.

Última versão vista por dono (`captura_crua.versao_ext`, 30 dias):

| Dono | Última | Última captura | Abaixo da 0.7.88 |
|---|---|---|---|
| Gabriel | 0.7.88 (só CopaWin, 19h); 0.7.74, 0.7.78 e 0.7.79 até 09h de hoje | 17/11 | parcialmente |
| arrudex | 0.7.86 | 17/11 | sim |
| Feca | 0.7.83 **e 0.7.71** na mesma hora | 17/11 | sim |
| Jonathan | 0.7.84 | 17/11 | sim |
| Jaao26 | 0.7.76 | 11/11 | sim |
| WilliamOliveira | 0.7.59 | 03/11 | sim |
| LavaPessoal | 0.7.55 | 01/11 | sim |

**Seis de sete abaixo da 0.7.88.** E três donos rodam **várias cópias** ao mesmo tempo
(versões diferentes na mesma hora, por casa): Feca (0.7.71 em 1win, DEX e Sportsbet.io;
0.7.83 no resto), Gabriel (0.7.74 na Sportsbet.io, 0.7.79 na MyStake, 0.7.78 no resto).
Provável um perfil do Chrome por conta. A memória
[`varias_copias_da_extensao_misturam_inject`] descreve o efeito.

Limite: só casa com cru (Ficha) grava `versao_ext`. Quem só captura casa de texto não
aparece aqui.

---

## 5. Os casos

### arrudex (Arruda), 15/11 a 17/11

- Capturou todo dia (15/11: 20bet, Jack, Sportsbet.io, Thunderpick, Vavada; 16 e 17/11
  idem, mais Betfury). Tudo o que entrou foi **pela Ficha** (origem `ficha`), salvo 2
  apostas da Betfury.
- **Nenhuma linha no `virada_log` em 15 e 16/11**: o `/extrair` não rodou nesses dias. Hoje
  rodou 3 vezes (Jack 14:24, Betfury 15:47, Thunderpick 15:50 UTC). Pelos logs HTTP, o IP
  dele fez **21 envios de captura e 3 `/extrair`** hoje.
- O que a Ficha resolve entra sozinho; o que fica para a IA (termo fora do dicionário,
  Ficha recusada, recusa do `/salvar`) só entra quando ele clica em Processar. Às 18:51 e
  18:53 UTC a captura chegou, a Ficha gravou, o dashboard rodou o `/tipsters/sugerir`
  (a grade atualizou) e ele trocou de casa sem processar o resto. **Para quem vê a grade
  mudar, a captura parece terminada.**
- Thunderpick: rota das liquidadas mudou na casa (s457, 0.7.86) e o câmbio EUR ficou
  bloqueado até ~17h UTC (s458). Daí as 9 abertas e as 10 ausentes de hoje.
- A conta Thunderpick dele está cadastrada em **USD**; a casa e as 204 apostas são **EUR**.
  Cada captura loga `moeda do cru diverge da conta (USD)`. Não estraga aposta (a aposta
  leva a moeda do cru), mas a Caixa dessa conta, se ligada, rodaria na moeda errada.
- Não tem Caixa ligada em conta nenhuma (0 movimentos). "Caixa que não bate", se veio
  dele, não veio do módulo Caixa.
- Uma captura perdida pelo defeito novo da 2.4 (17:55 UTC).
- IA: US$ 0,45 hoje em 3 leituras.

### Gabriel (gfatuch), 15/11 a 17/11

- Volume alto e contínuo: 7 casas por rodada, 2 a 3 rodadas por dia; 263 apostas novas no
  período (Stake.com, CopaWin, Cloudbet, Sportsbet.io e outras).
- **CopaWin manda quase tudo para a IA:** 105 `Ficha recusada` (`type 'multiple' sem
  amostra`). Funciona, mas a IA paga cada múltipla.
- **16/11 00:01 UTC:** excluiu 90 apostas da CopaWin pela Extração e recapturou 15 s depois
  (as mesmas 90 voltaram, pela IA). É o contorno "apaga e recaptura" de quem não confia no
  número.
- **Caixa:** em 16/11 conferiu Cloudbet (Sharpen −1.082,31, casa 7,69) e Sportsbet.io
  (Sharpen −644,22, casa 0,76) e fechou as duas com Ajuste (+1.090 e +644,98 USDT).
  Comparei as duas contas aposta a aposta com o cru da casa: **Cloudbet 186 de 186 iguais**
  (13 crus recusados), **Sportsbet.io 79 de 79**, P/L idêntico ao centavo. As 19 apostas da
  Cloudbet que estavam abertas na conferência (criadas 13 s antes) foram liquidadas depois
  e a conta com o Ajuste fecha exato no saldo de hoje. Então **a diferença já existia antes
  e não vem de aposta**: é dinheiro que entrou na casa sem lançamento no Sharpen (depósito
  ou bônus) ou aposta anterior ao horizonte do cru. Só o extrato da casa fecha.
- Várias cópias da extensão (item 4).
- IA: US$ 3,08 em 3 dias.

---

## 6. Proposta de conserto do estoque (item 1)

**Não aplicada.** Duas partes, nesta ordem.

**A. Código (estrutural, fecha a família):** o cru só conta como tratado quando a linha
dele **chegou ao banco**. Hoje `marcar_processados` roda depois de `gravar_aceitas`
mesmo quando o `/salvar` interno recusou a linha por motivo **transitório** (câmbio,
cotação). Mudança proposta em `ficha._processar` / `virada.gravar_aceitas`: os ids de cru
cuja linha foi recusada no `/salvar` **não** recebem `processado_em`; e `gravar_cru`, para
o cru igual já marcado, devolve o id de novo quando o código está em `ficha_virada` como
`recusada no /salvar` e não há linha resolvida no banco. Assim a próxima captura igual
reprocessa sozinha. Com teste provado por mutação, no padrão do 5.3.

**B. Dado (as 9 de hoje):** com A no ar, **não precisa de script**: a próxima captura da
Thunderpick do arrudex reprocessa as 9 (o `gravar_cru` passa a devolvê-las) e as 10 + 3
ausentes entram pela IA quando ele clicar Processar. Se o Feca preferir não depender da
próxima captura, o script seria só limpar `processado_em` desses 9 crus (`captura_crua.id`
dos 9 códigos), que roda primeiro no Postgres local e vem para aprovação.

**C. As ausentes antigas (LavaPessoal, Jaao26, Jonathan, contas arquivadas do arrudex):**
não proponho correção sem o dono dizer se queria aquele histórico. Lista pronta para
mostrar.

**D. Fora do estoque, mas da mesma raiz (item 5):** a parte da IA esperando um clique é o
que deixa a captura "pela metade" sem ninguém ver. Proposta para o Feca decidir: quando a
Ficha devolve "ficam com a IA: N", a tela de Extração mostra o número e o botão em
destaque, ou dispara o `/extrair` sozinha. Não mexo nisso sem decisão.

**E. Defeito novo da 2.4:** `enviar` para sessão encerrada responde 404 em vez de 200 "em
memória". Pequeno; entra junto com o pacote da extensão (a 7.2 já mexe no reenvio).
