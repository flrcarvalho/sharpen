# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`

_Atualizado: 2026-07-31 (sessão 222 — **Base pessoal do Lava importada para `LavaPessoal`: 2.877 apostas (23/02 → 30/07/2026), script próprio `scripts/import_lavapessoal_xlsx.py`.** Pedido do Feca em uma linha, com a regra de conta junto: *"ele não anota o parceiro, então considere Casa - Padrão - sem fornecedor"* — e o aviso que definiu a forma: **"essa importação é única, nada a ver com antigas"**. **O maior achado é uma armadilha herdada:** os dois importadores existentes (`import_lava.py`, `import_dashboard_xlsx.py`) copiaram o `_assinatura` **pré-s133, sem `stake` no hash**. Reusá-los como modelo teria gravado 2.877 assinaturas que não correspondem às que o `repository.py` de hoje gera — a próxima captura não colidiria com nenhuma e **duplicaria o histórico inteiro**. O script novo copia a versão de **hoje** (`casa|parceiro|data|aposta|descricao|stake|_norm_odd(odd)`), com o mesmo laço de `_counter`. **A planilha do Lava contabiliza em UNIDADE, e a unidade não acompanha a coluna de stake:** em **2.553 de 2.860** linhas liquidadas o `P/L (R$)` ≠ `stake × (odd−1)` (stake 800, odd 1,83, W → a planilha marca R$ 830; o derivado é R$ 664). Como o P/L do sistema é **derivado** (`calcular_pl`, nunca persistido), o dashboard mostra **R$ 132.336,58** onde a planilha dele soma **R$ 146.056,20** — ~R$ 13,5 mil (9%) de diferença. **Não há conserto sem falsificar a stake**, então as colunas `U Investida`/`P/L (U)`/`P/L (R$)` foram descartadas e o Feca foi avisado **antes** de rodar. **A descrição não classifica nada nesta base** — é quase sempre só o nome do time ("Fulham", "City"), então o motor de keywords do `import_dashboard_xlsx` **não serve**: o objeto sai do **rótulo + tipster**, que aqui é especializado por mercado (decisão do Feca). `Cantos` (529 linhas) → `Escanteios` em todos os rótulos de escanteio (`Over`/`Under`/`Race`/`HTML`/`MLHT`/`Handicap`/`Last`), que pelo `MASTER_APOSTAS §1` são o mesmo objeto variando só o tipo de mercado. **Uma correção de rumo no meio:** eu havia proposto `Player Props` para o Over/Under de basquete do `MiniSilva`, mas o `§5` é explícito — jogo inteiro **ou time** → `Pontos`; só **jogador** → `Player Props`; as descrições são confrontos e times, então foi `Pontos`. Cuidado gêmeo na Fórmula 1: o rótulo `Pontos` do `Marco` é *"terminar nos pontos"* (posição do piloto) e **não** a categoria `Pontos` (objeto ponto de Basquete/Vôlei) — vai para `Player Props`. Resultado: **0 linhas em `Outros`** e **0 categorias fora do canon**. **Decisões do Feca:** tipsters em CAIXA ALTA → Title Case · `Tivobet` → **Tivo** (casa canônica, `CASA_TIVO.md`) · `Rei` → **Pitaco** ("Rei do Pitaco virou Pitaco só") · casa sem canon prévio entra **verbatim** (nunca title-casear — mutilar nome cria conta paralela). **Um erro meu de medição foi pego pelo próprio gate:** contei "7 linhas sem stake" testando `stake in (None,'')` — **zero é `int 0`, não vazio**, e as linhas reais eram **30** (23 delas COM resultado). Importadas assim mesmo, e a razão importa: `dashboard_rows` corta `stake <= 0`, mas **`list_bilhetes` não** — elas aparecem na grade da Extração, onde dá para preencher a stake e elas voltam ao dashboard. Descartar seria perda irreversível; importar é recuperável. **Gates (contra o dado real, não contra o parser):** roundtrip `stake`/`odd` planilha × gravado → **0 divergências** em 5.754 valores · **2.877 assinaturas únicas de 2.877** · 0 categoria fora do MASTER · 0 data malformada · pós-escrita no Postgres: 0 grupo de assinatura duplicada, **0 linha de import recente em outro dono**, 0 linha fora da ordem cronológica de `criado_em`. Absorvidas 9 odds gravadas como moeda (`"R$ 2,25"`, 21/07 — o valor é a odd, só o formato da célula está errado) e 1 linha com o cabeçalho repetido na célula de esporte. Backup `Backups/s222-import-lavapessoal/`. **Duas contas pré-existentes** apareceram sob `LavaPessoal` (criadas 30/07, arquivadas, **zero** bilhetes): `Bet365 | monster@2025 [Richard]` e `Betano | karlmarxrosa@aurainteligente.com [221193Cy*]` — não foram tocadas; se forem lixo, o botão Excluir da s219 resolve. Elas são a **evidência** de que o `LavaPessoal` já vinha usando o sistema. **Um erro de leitura do próprio STATUS fechou a sessão:** afirmei que o Lava não conseguia entrar por falta de `SENHA_LAVAPESSOAL_HASH`. **Ele entra — o Railway está certo desde antes.** A frase saiu do §5 "Bloqueado por ação humana", escrito na s220 e **nunca revisado** depois que o Feca colou as variáveis. **A lição é sobre o gênero do documento, não sobre o dado:** o §5 lista pendências *do lado humano*, e pendência é **estado declarado no passado**, não fato verificado — o STATUS não é instrumentado, ninguém o atualiza quando a ação acontece fora do repo. Tratar linha de pendência como medição é o mesmo erro de método que a s217 documentou ao contrário (lá, o silêncio do fallback escondeu a quebra por 26 dias). **Regra:** só afirmar estado de configuração externa (Railway, DNS, planilha viva) com **medição do momento** ou palavra do Feca; sem isso, escrever "não confirmado", nunca "faltando". **Anterior: s221 abaixo.**)_

_Anterior: 2026-07-31 (sessão 221 — **"Sugerir tipsters" parou no 199 do LBB: um perfil NOVO envenenou a assinatura de um perfil ANTIGO, em silêncio.** **Sintoma do Feca:** *"rodava perfeito até duas ou três extrações e agora nada, em bets e contas que ele sempre reconhecia"* — 13 bilhetes `Bet365 · Futebol · Gols · 199,00` da conta `gleicecacia01 [Richard]` voltando com "Nenhuma sugestão confiante". **O matcher NÃO tinha parado:** rodando o código exato do `index.html` contra os 32 perfis ativos e os bilhetes reais do banco, Peixe/DartsVader/TC Insider continuavam saindo. Quem parou foi **o LBB**, e a causa é dado, não código: o perfil **`MultiLBB` nasceu em 27/07 12:54 UTC** com a dica de stake `49, 99`. **O parser deriva o *final* de todo valor não-redondo** (`49 → 9`, `99 → 9`), então o MultiLBB virou dono do **final 9 inteiro** — a mesma digital do `199` do LBB. Ranking: **LBB 28 × MultiLBB 27**, folga **1**, e a régua exige **≥ 7** → os dois se anulam e a coluna fica vazia. **O matcher é desenhado para não chutar em empate**, então a regressão não deu erro nenhum: ele só emudeceu. **A prova foi por remoção, não por dedução** — tirando só o `MultiLBB` da lista de perfis, os 8 bilhetes de 199 voltam a sair `LBB` sem tocar em uma linha de código. **A regra que o Feca cravou** (`MultiLBB = 49 e 99`; `199 = LBB, em Futebol Gols e em Basquete Handicap/Pontos`) diz que o discriminante é o **valor exato**, não o final. **Fix, uma linha em `_stakeSignal`:** valor exato **não-redondo** declarado é **DIGITAL** (peso 40) e ganha do **final derivado**, que é só **FAMÍLIA** (25/√nº). **O corte do redondo não é detalhe, é o que segura o resto:** a primeira tentativa deu peso alto a todo valor exato e o **M&M** — que declara `50 100 200 300 400` — passou a roubar os 50/100 do **Peixe**: **252 erros novos** no backtest. Redondo é valor comum, não digital. **O MultiLBB também estava quebrado e ninguém tinha notado:** só era reconhecido em `Múltiplos`; em Futebol/Basquete ele empatava com o LBB e os dois se anulavam. O fix conserta **os dois lados**. **Backtest sobre 4.000 bilhetes do Feca já rotulados:** acertos **2.014 → 2.326**, vazios **1.828 → 1.505**, erros 158 → 169. **Os 11 erros a mais são um handover temporal, não defeito:** o `199` **trocou de dono** (maio: SóTudo 330 × LBB 0; julho: SóTudo 16 × LBB **313**) e o próprio perfil do SóTudo diz *"Já usei 199 mas hoje uso 205"* — são bilhetes de maio/junho já preenchidos. **Não-regressão conferida caso a caso:** Robotenis 250, TC Insider 800, BFM 302, Peixe 306 na Betano — idênticos a antes. **O que este fix NÃO resolve, e não é regressão:** as 5 stakes **quebradas** da mesma tela (109,38 · 112,18 · 184,21 · 121,53 · 128,68) **nunca** foram sugeridas — quebrada na Bet365 não é digital de ninguém (M&M 284, SóChutes 121, SóTudo 31, LBB 30). O que as identificaria é o **trio casa · esporte · categoria** (`Bet365 · Futebol · Gols` = **94 % LBB** em jul/ago), sinal que o matcher **não usa** hoje — ele é 100 % declarativo, nunca lê o histórico. Proposta de "feudo empírico" medida e **não** implementada (ver §5). **Gates:** `pytest tests/` **271 passed, 13 skipped** · `check-tokens` OK · JS inline sem erro de sintaxe · casos da regra do Feca e backtest re-rodados **contra o arquivo já editado**, não contra a cópia de trabalho. Backup `Backups/s221-matcher-valor-exato-digital/`. **Anterior: s220 abaixo.**)_

_Anterior: 2026-07-30 (sessão 220 — **Conta nova `ViniciusOliveira` (dono solo, base virgem) — o mesmo procedimento de duas metades da s216/s218.** Pedido do Feca em três linhas: "Novo Usuario / ViniciusOliveira / Oliveira". **A terceira linha era ambígua e foi PERGUNTADA, não adivinhada** — sobrenome de exibição (que não existe como campo no sistema) ou senha? Era a **senha**; adivinhar errado gastaria um deploy e deixaria o login falhando com a mesma cara de "senha errada". A segunda pergunta foi a que muda código: **dono solo ou operador**. Ficou **solo** (default do projeto, igual ao `WilliamOliveira` da s218) — ninguém "vê como" ele, ele não vê ninguém, `coproprietarios == []` → **sem dedup cruzada**. **A armadilha desta conta é o sobrenome**, exatamente como a da s216 era o prefixo `Lava`: `WilliamOliveira` e `ViniciusOliveira` **não formam linhagem**, são duas bases isoladas que por acaso compartilham sobrenome. Travado em teste próprio (`test_os_dois_oliveira_sao_donos_solos_independentes`) que checa os dois sentidos de `pode_ver_como` — pendurar um em `OPERADORES` do outro numa sessão futura derruba a suíte. **Mudança total: 3 linhas** — 1 em `USUARIOS` (`app/auth.py`), 1 no `.env.example`, 1 no assert de donos solos. Sem migration, sem seed, sem import: o isolamento é a coluna `dono` no Postgres, a base nasce vazia e o primeiro bilhete capturado cria as linhas. **Hash bcrypt gerado e conferido ponta a ponta antes do commit** (60 caracteres, sem espaço nas pontas, valida a senha certa, rejeita a caixa trocada e a errada, `verificar_credenciais` + roundtrip do token com a env var carregada). **O hash não entra no git** — vai na caixa de Variables do Railway pela mão do Feca, colado literal, porque o `$` do `$2b$12$…` chega mutilado por qualquer shell que interpole variável. **Gates:** `pytest tests/test_auth.py` **29 passed** (1 novo). Backup `Backups/s220-user-viniciusoliveira/`. **Pendente do lado humano:** agora são **três** env vars de senha faltando no Railway (s216, s218 e s220 — ver §5); enquanto faltarem, o login responde "usuário ou senha inválidos" por desenho (fail-closed). **Anterior: s219 abaixo.**)_

> **Histórico completo das sessões 219 → 14** → [`docs/HISTORICO.md`](docs/HISTORICO.md)

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
    CASA_JOGODEOURO.md
    CASA_KINGPANDA.md
    CASA_KTO.md
    CASA_LOTTU.md
    CASA_PINNACLE.md
    CASA_POLYMARKET.md     (por API, não IA)
    CASA_SUPERBET.md
    CASA_TIVO.md
    CASA_BETFAST.md        (espelho técnico da Tivo — mesmo motor BetConstruct)
    CASA_VAIDEBET.md
    CASA_VITORIABET.md
/golden_set/
    bilhetes/              (print + TSV esperado)
/docs/                   (referências, ADRs, planos, HISTORICO.md)
STATUS.md                  (este arquivo)
```

Os 6 MASTER_*.md vivem em `/global/`; as 17 casas em `/casas/` (Polymarket por API, as demais por IA/texto).

---

## 4. Estado atual

- **Produto no ar** em `sharpen.bet` (dashboard + extração); deploy automático via Railway.
- **Multi-tenant:** vários donos (Feca, Fatuch, Diogo, Jonathan, Lava, LavaPessoal…) + operadores; dados isolados por `dono` no Postgres (regras de tenancy/dedup no `CLAUDE.md`). Conta nova = 1 linha em `USUARIOS` (`app/auth.py`) + `SENHA_<USER>_HASH` no Railway; base nasce vazia sem migration.
- **Base do Feca:** migração planilha → Postgres **completa e reconciliada**.
- **Base do `LavaPessoal` (s222):** 2.877 apostas importadas do `.xlsx` pessoal do Lava (23/02 → 30/07/2026), `origem='import'`, conta `Padrão` em cada uma das 19 casas (ele não anota fornecedor). Script próprio e idempotente: `scripts/import_lavapessoal_xlsx.py` (re-rodar limpa só `origem='import'` daquele dono; captura da extensão sobrevive). **Não confundir com o dono `Lava`** — são bases distintas que só compartilham o apelido. **O P/L do dashboard não bate com a planilha de origem por desenho** (ela contabiliza em unidade; ver s222 no topo).
- **Casas:** 17 arquivos em `casas/` (extração por IA/texto) + **Polymarket** por API.
- **Fatuch:** dashboard lê a planilha viva do LavaFatuch via Apps Script (leitura por **cabeçalho**, não por posição); coluna `Espelho` = fornecedor. Sem base no Postgres (tudo vem da planilha).
- **Captura:** extensão **SharpenUp** (moldura+Snap e robô de rolagem) no ar, pareando por código. **10 casas por API** (injetor no mundo MAIN, dado exato): Superbet, BETesporte, Betano, Betfair, Pinnacle, Bet365, KTO (Kambi, s192), Tivo (s196), VaideBet (Altenar, s210) e **Betfast** (s211 — **espelho da Tivo**: mesmo motor BetConstruct, mesmo `tv_inject.js`, sem código duplicado).
- **Apostas em aberto (s215):** o feed (`dashboard_rows`) carrega a aposta não liquidada marcada `resultado='ABERTA'`, `lucro=0`. Ela aparece no topo da **Minha Base** (ex-"Apostas") e tem tela própria em **Minhas Apostas › Em Aberto** (`charts/abertas.js`): KPIs de exposição, horizonte por faixa de dia, calendário por data do evento, barras por casa e por tipster, lista completa. **Nenhuma métrica a soma** — `aplicarFeed` separa `DADOS` (encerradas) de `DADOS_ABERTAS`, e Início/Extração cortam por `resultado==='ABERTA'`.
- **Modelo de extração:** Sonnet 4.6 (`config.py`).

---

## 5. Pendências (aguardam bilhete real)

- **Bet365:** §6 rótulo visual do boost · §7 rótulo visual do cashout encerrado
- **Betfair:** cashout **parcial** (`isPartialCashOut`) sem amostra — o total já está travado no harness (2 casos) · HW/HL sem amostra · Each Way com `0 < Retorno < Stake` (o §5 não cobre essa faixa; hoje sai "a conferir", sem chute)
- **Betano:** §5 rótulo de void/anulada · §6 boost (existe?)
- **Pinnacle:** §5 rótulo exato de HW/HL no export (precisa de Asian Handicap de quarto liquidado)
- **Bolsa de Aposta:** §5 V/HW/HL · §6 boost · §7 cashout · §8 bônus · apostas Lay
- **Betnacional:** §5 HW/HL · §5 V (rótulo visual de void) · §7 cashout · §8 bônus
- **Jogo de Ouro:** §5 V/HW/HL · §5 rótulo do card na aba Cashout · §7 cashout · §8 bônus
- **KTO:** de-para do `betStatus` da API para VOID/Nula, Recusado, cashout encerrado e meia-liquidação. Também sem amostra: `systemBets` (`Simples (N)`, `Duplas (X), Triplas (Y)`), aposta grátis e stake dividida (duas entradas em `bets[]`). Confirmados hoje: `WON`, `LOST`, `OPEN`.

- **Betfast / Tivo (s211):** cashout · bônus · aposta de sistema · outright · **aposta ABERTA** (as 50 da amostra são liquidadas) · `§9` de duas categorias (`Total de defesas do goleiro` · `Handicap de mapas`/`Map Advantage`)

**Achados de performance da s217 — medidos, não corrigidos (decisão do Feca, um por vez):**
- **`sims=10000` fixo mesmo com a base cheia.** As chamadas passam `10000` explícito, o que **atropela** a escala adaptativa que o `_calcPValueMCraw` tem por dentro (`n>10000 → 3000`). Com 30.851 linhas são ~308 milhões de iterações por cálculo, duas vezes. Fora da thread principal a tela não trava mais, mas o valor ainda leva **~1 minuto** para chegar (conferido no demo com 24.000: os cards ficaram girando bem depois do render). Cair para ~2.000 sims em base grande resolveria — **muda número exibido** (p95/p99 e p-value), então exige antes/depois medido na mesa e aval do Feca.
- **`/uso/tokens` responde 500** em produção (visto ao cronometrar as rotas do feed). Não investigado.
- **A casca `/app` carrega 3 iframes e os 3 puxam `/dashboard/data`** — `/inicio`, `/` (Extração) e `/dashboard/`, cada um montando o feed inteiro no servidor (3 × 11,6 MB por abertura). Um cache compartilhado entre os frames (ou o feed servido uma vez pela casca) cortaria 2/3 do trabalho.
- **Deep-link a frio monta a tela vazia.** Abrir `/app#dash/metrics` sem cache local: a casca chama `showPage('metrics')` antes de o `buildHTML` existir, `_lastPage` já fica marcado, e o `loadData` termina **sem chamar `renderPage`** (`app.js:1183`) — o `showPage` seguinte volta cedo pelo `if(id===_lastPage&&sig===_lastPageSig)return`. A tela fica com os `—` do markup. **Pré-existente**, não veio da s217.

**Próximo passo (backlog vivo, um por vez):**
- **Matcher: "feudo empírico" — medido na s221, NÃO implementado.** O `Sugerir tipsters` é 100 % **declarativo**: lê só os perfis (casas · esportes · mercados · dica de stake) e **nunca** o histórico. Por isso as stakes **quebradas** (109,38 · 112,18 · 184,21…) ficam eternamente vazias — nenhum perfil declara quebrada na Bet365, e por stake elas são de todo mundo (M&M 284 · SóChutes 121 · SóTudo 31 · LBB 30). **O sinal que falta está na própria base:** no trio **casa · esporte · categoria**, um tipster domina. Medido na janela de 2.207 bilhetes que a tela **já carrega** (dá para computar no front, sem endpoint novo): `Bet365·Futebol·Gols → LBB 98 %` (226) · `Bet365·Futebol·Escanteios → SóTudo 82 %` (257) · `Bet365·eBasket·Pontos → Ctrl Alt Green 100 %` (219) · `Bet365·Tênis·ML → Robotenis 99 %` (168) · `Superbet·Múltiplos·Múltipla → Arrudex 92 %` (169) · `BETesporte·Futebol·Múltipla → Peixe 100 %`. Regra proposta: tipster **ativo** com ≥ 90 % e ≥ 15 bilhetes no trio leva; senão cai no matcher declarativo de hoje. **Cuidado que o próprio caso do 199 ensina:** o dono de um trio **muda com o tempo** (SóTudo → LBB entre maio e julho), então a janela precisa ser **recente**, não a base inteira — na base inteira `Bet365·Futebol·Gols` cai para 52 % de LBB e o critério não dispara. Fazer só depois de backtest com **holdout temporal** (treina no passado, mede no futuro), nunca in-sample.
- **Excluir conta: o caminho nunca rodou contra Postgres de verdade** (s219). Os 7 casos de `test_excluir_parceiro.py` usam conn simulado, como o resto da suíte. Três coisas ficaram sem prova real: o `DELETE ... RETURNING to_jsonb(b.*)`, o cast `::jsonb` do snapshot no INSERT da lixeira, e o corpo do `DELETE` via HTTP. **Teste barato, fazer antes de excluir qualquer conta com histórico:** criar conta descartável, capturar 1 ou 2 bilhetes, excluir pelo modal, e rodar `python scripts/restaurar_conta_lixeira.py` para ver se a linha aparece com a contagem certa. Depois `--aplicar` num id e conferir se as apostas voltam. A forma travada seria um caso em `tests/test_repository_db.py` (roda no CI com `TEST_DATABASE_URL`, nunca em prod).
- **Betfast: rodar a captura pela EXTENSÃO** (s211). A API já foi validada ao vivo (varredura do teto: 32 de 32, ver acima), mas o robô em si nunca rodou: recarregar a extensão, **Ctrl+Shift+R** na aba, capturar e conferir contagem/datas/odds/código no dashboard. **O gatilho do teto continua sem exercício ao vivo** — a conta que loga no navegador tem 32 bilhetes e não chega nas 50; para ver o toast *"a captura foi além do teto"* seria preciso rodar na conta `fecanario`.
- **Pinnacle sem fixture no harness** (s201): a instrução foi corrigida (§6/§11 não afirmam mais que a exibida é autoritativa em `W`), mas a leitura da odd **nunca foi travada contra dado real** — só Betfair, KTO e Tivo têm caso. Com o JSON do `POST /member-service/v2/wager-filter` dá para criar `fixtures/pinnacle.*.json` + `casos/pinnacle.mjs` e medir de fato o quanto a exibida diverge de `Retorno ÷ Stake`. O banco não serve para isso: guarda stake e odd, nunca o retorno.
- **bet365 sem caso no harness** (s202): é a única casa de robô sem regressão travada — e o parser dela já quebrou 3 vezes. As fixtures reais (`summary` + `confirmation` do bilhete com bet builder) já estão em `extensor/harness/fixtures/`; falta escrever `casos/bet365.mjs`. A conferência de cobertura dela **já está ligada** (`831f97f`).
- **`renomear_parceiro` não recalcula a assinatura** (s198): `parceiro` entra no hash, então toda conta renomeada duplica o histórico na próxima captura.
- **41 apostas com odd truncada em reticências** (`2.50001664442...`): 22 Bet365, 6 Novibet, 6 Bolsa, 4 Betfair, 3 Esportiva Bet. A instrução proíbe reticências e uma odd assim não converte para número — mexe em P/L, não é cosmético.
- Preencher pendências das casas existentes assim que amostras reais chegarem (ver lista acima).
- **Solto (cosmético):** favicon da KTO aponta para `kto.com`; o domínio real é `kto.bet.br`. Corrigir nos 3 mapas (`extensor/popup.js`, `app/static/index.html`, `app/static/dash/assets/js/data.js` + `inicio.html`).
- **Tela "Em Aberto" fora do material de venda** (s215): `scripts/demo/capturar.mjs` não captura a tela nova — o servidor de demonstração já a serve, falta só decidir se ela entra no showcase (e a numeração dos arquivos existentes muda). **Decisão do Feca: entra, mas só depois de a tela estar finalizada.**
- **Em Aberto: relato do Gabriel SEM confirmação** (s215, aberto): funciona para o Feca (57 abertas, R$ 13.325, conferido na sessão logada em `www.sharpen.bet`), mas o Gabriel disse que não. **Hipótese principal: casca velha ainda gravada no navegador dele** — o `no-cache` só vale a partir da próxima ida ao servidor, não desfaz cache já gravado; `Ctrl+Shift+R` uma vez resolve (F5 normal pode não recarregar o iframe do dashboard). **Antes de mexer na tela, distinguir pelo que ele vê:** cards com título e corpo vazio, sem nenhum KPI = ainda é cache; os 4 KPIs em `R$ 0` / "nada em aberto" = não é bug, a base dele não tem aposta aberta (conferir de quem é a base pelo filtro "Operador"). O jeito de medir é ler quais scripts o navegador dele carregou (`[...frame.contentDocument.scripts].map(s=>s.src)`) — versão antiga ou tag ausente = cache.
- **Frente worldwide (nova, plano aprovado):** construir a Fase 1 do [`docs/PLANO_EXTRACAO_WORLDWIDE.md`](docs/PLANO_EXTRACAO_WORLDWIDE.md) (confidence da IA + guardrail de enum) quando o Feca quiser. Fase 0 já validada (zero-shot 94,5% de acerto de categoria). Meta: extração universal + cache aprendido → "+adicionar conta" em autosserviço.

### Bloqueado por ação humana (não é bilhete)

- **Env vars de senha no Railway (s216, s218, s220) — estado NÃO instrumentado.** `SENHA_LAVAPESSOAL_HASH` **está no ar e o Lava entra** (confirmado pelo Feca em 31/07, s222). `SENHA_WILLIAMOLIVEIRA_HASH` e `SENHA_VINICIUSOLIVEIRA_HASH`: **não confirmadas** — podem já ter sido coladas; ninguém atualiza esta linha quando a ação acontece fora do repo.
  > ⚠️ **Esta linha é uma pendência declarada, não uma medição.** Não afirme a partir dela que um login está quebrado — foi exatamente o erro cometido na s222. Para saber de verdade: `POST /login` devolvendo **200** = hash certo; **401** = ausente ou diferente (429 é rate-limit, 500 é erro do app). Sem esse teste ou a palavra do Feca, escreva "não confirmado".

  Procedimento, se algum dia faltar mesmo: os hashes **não entram no git** — se perdidos, gerar de novo com bcrypt e colar na caixa de Variables do Railway (literal, 60 caracteres, sem espaço nas pontas; o `$` do `$2b$12$…` chega mutilado por qualquer shell que interpole variável).
- **`LavaPessoal`: 30 apostas com stake 0** (s222) — importadas, mas **invisíveis no dashboard** (`dashboard_rows` corta `stake <= 0`). 23 delas têm resultado. Aparecem na grade da **Extração** (`list_bilhetes` não filtra), então a correção é humana: preencher a stake lá e elas entram no P/L. Todas do tipster `Peixe`, abr–jul.
- **`LavaPessoal`: duas contas pré-existentes vazias** (s222) — `Bet365 | monster@2025 [Richard]` e `Betano | karlmarxrosa@aurainteligente.com [221193Cy*]`, criadas em 30/07, arquivadas, **zero** bilhetes. Não vieram do import e não foram tocadas. Se forem lixo de teste, apagar pelo botão Excluir do Painel de Contas (s219).

Quando chegar um bilhete novo: abrir o arquivo da casa correspondente, preencher a pendência, rodar o checklist do `CLAUDE.md` se envolver categoria nova.

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
