# Guia — ligar uma casa nova ao SharpenUp

> **Escopo:** a camada de **captura** (extensão → ponte → backend). A camada de **leitura**
> (`casas/CASA_*.md`, masters, TSV) está em [`GUIA_NOVA_CASA.md`](GUIA_NOVA_CASA.md) — as duas
> são independentes: dá para ler uma casa por print sem captura, e a captura só entrega texto
> cru para a mesma leitura de sempre.
>
> **Mapa do sistema:** [`SHARPENUP_ARQUITETURA.md`](SHARPENUP_ARQUITETURA.md).
> **Skill guiada:** `/sharpenup-casa` (e `/sharpenup-recon` para a Fase 0).

**Ordem obrigatória. Uma fase por vez: propor → aguardar confirmação → executar.**
Nenhuma fase começa antes de a anterior estar verde.

---

## Fase 0 — Reconhecimento (o Feca no F12, 10 minutos)

**Nunca comece pelo código.** O que decide o modo é o que a casa entrega, e isso se descobre
olhando. Roteiro, na página "Minhas Apostas" logada:

1. F12 → **Network** → filtro **Fetch/XHR** → recarregue a página.
2. Ache a requisição que traz a **lista de bilhetes** (ordene por *Size*; costuma ser a maior).
3. Anote: **método** (GET/POST), **URL**, e — se POST — o **corpo**.
4. **Copy → Copy response** e salve como `extensor/harness/fixtures/<casa>.<endpoint>.json`.
5. Role a lista até o fim / clique "mostrar mais" e veja **como a próxima página é pedida**:
   parâmetro de offset? cursor? corpo diferente? E **como a casa diz que acabou**
   (`more:false`, `hasNext`, campo ausente, lista vazia).
6. Clique a aba **"Em aberto"** e repita — quase sempre é a mesma URL com outro `status`.
7. Se um bilhete tiver detalhe (pernas, mercado) fora da lista, veja **qual requisição o
   clique dispara** e se ela exige token além do cookie.

Perguntas que precisam de resposta antes de escrever uma linha:

| Pergunta | Por que importa |
|---|---|
| Existe um **ID de bilhete** no payload? | é a chave de dedup e o `[Código:]`; sem ele a casa não dedupa |
| **Stake, retorno e odd** vêm em quais campos? Em milésimos? | KTO vinha em milésimos; ler errado erra 1000× |
| A odd bate com o card **em toda situação**, inclusive perdida? | `betOdds` da KTO é **0** em toda perdida |
| A **data** é de colocação, evento ou liquidação? Em que fuso? | é a 1ª coluna do TSV; errar desloca tudo |
| A casa tem **boost / cashout / freebet**? Como aparecem? | mudam a regra de odd (`retorno ÷ stake`) |
| Quantos bilhetes por página e qual o **fim autoritativo**? | sem isso o robô para cedo ou nunca |

> **Regra de ouro:** a leitura correta é **o que a casa mostra na tela**, não o que o campo
> parece dizer. Toda dúvida se resolve cruzando o JSON com o card renderizado.

---

## Fase 1 — Escolher o modo

```
A página baixa a lista de bilhetes por fetch/XHR num JSON legível?
├── SIM ─ o scroll/botão da página traz todas as páginas sozinho?
│         ├── SIM → API PASSIVA          (espelhe sb_inject / bn_inject)
│         └── NÃO → API + REPLAY         (espelhe kto_inject / bf_inject / pn_inject)
│                   o inject aprende url+headers de uma requisição REAL e repagina
└── NÃO ─ o detalhe exige clique e o token rotaciona?
          ├── SIM → NAVEGAÇÃO POR ROTA   (b3_inject — caro, último recurso)
          └── NÃO ─ o card inteiro está no DOM E há LINHA EM BRANCO entre bilhetes?
                    ├── SIM → TEXTO (roboScroll genérico, sem inject)
                    └── NÃO → PRINT (default; não force texto)
```

**Preferir sempre a API.** O texto por DOM parece mais simples e cobra caro depois: sem ID
não há dedup, sem campo não há odd exata, e a fronteira entre bilhetes é frágil
(s192: a KTO virou 1 bloco de ~140 bilhetes e a IA perdeu ~90 % em silêncio).

**Print não é fracasso.** É o default de toda casa nova e funciona. Captura só se paga em
casa de volume.

---

## Fase 2 — Harness ANTES do código (test-first)

Com a fixture salva, escreva `extensor/harness/casos/<casa>.mjs` espelhando `casos/kto.mjs`,
com o valor esperado de cada bilhete **lido do card da casa**, não do código.

```powershell
node extensor/harness/run.mjs <casa>
```

Vermelho aqui é o estado correto — ainda não há código. Isto vira o critério de pronto e
trava a regressão para sempre. Ver `extensor/harness/README.md`.

---

## Fase 3 — O inject (`extensor/<xx>_inject.js`)

Copie o inject **mais próximo do seu modo** e troque 5 coisas: o `RX` do endpoint, a chave do
bilhete, o nome da mensagem (`__sharpenupXXData/Req`), a normalização e — se houver replay —
como avança a página. Regras do contrato em
[`SHARPENUP_ARQUITETURA.md §3`](SHARPENUP_ARQUITETURA.md#3-contrato-de-mensagens-inject--content):

- emitir `hook:true` + `respostas` **sempre**, mesmo com 0 bilhetes;
- **re-enviar sob demanda** (`__sharpenupXXReq`) — a 1ª página chega antes do content ouvir;
- guardar o `fetch` **original** (`const of = window.fetch`) e usar ele no replay, senão o
  replay re-dispara o próprio wrapper;
- enganchar **fetch E XHR** (várias casas usam XHR);
- `credentials: "include"` + os headers que a página usou (o Bearer é da sessão dela);
- avançar pelo tamanho de página que **voltou**, não pelo que foi pedido;
- **teto de páginas** + parada quando não vem bilhete novo (anti-loop);
- **normalizar, nunca decidir**: status desconhecido sobe cru.

---

## Fase 4 — O content.js

Quatro peças, todas espelhando uma casa existente (a KTO é a mais recente e completa):

1. **Ouvinte** da mensagem, com o mapa por chave e a regra *resolvida vence aberta*.
2. **`formatTicketXX(t)`** → o bloco de texto que a IA lê. Primeira linha **sempre**
   `[Código: <id>]`. Rotule tudo de forma inequívoca:
   - aberta → `"em aberto (aguardando resultado — NÃO liquidar; sem resultado)"`;
   - retorno de bilhete aberto é **potencial**, nunca "retorno";
   - status desconhecido → `"<cru> (a conferir — não liquidar automaticamente)"`;
   - **odd nunca truncada** (regra primordial); decimal com **vírgula**;
   - W → `retorno ÷ stake` (respeita boost); L/V/aberta → odd estrutural.
3. **`roboXXPassive(ctx)`** — pede o acumulado, espera o `fim`, respeita `ctx.stopId` e a
   janela de dias (**a janela corta só resolvidas**; aberta nunca corta), atualiza o contador
   do painel e **nunca para no primeiro obstáculo** (só desiste por teto de inatividade).
4. **Ramo no `iniciarRobo`** + **entrada no mapa de autodiagnóstico** (`hook`/`respostas`/`vistos`).

---

## Fase 5 — Registro (os 12 pontos)

Percorra a tabela de [`SHARPENUP_ARQUITETURA.md §5`](SHARPENUP_ARQUITETURA.md#5-superfície-de-registro--os-12-pontos)
e depois **prove**:

```powershell
python tools/audit_sharpenup.py <CASA>
```

Os dois pontos que mais somem, ambos silenciosos:

- **`CASAS_CONECTAVEIS`** (`index.html`) — sem ele o botão "Conectar" nasce desabilitado e
  **nada** do que você construiu chega a rodar (foi a s191 inteira).
- **regex de código** (`repository.py`) — sem ele a **conferência de cobertura** fica
  desligada nessa casa: um chunk pode sumir sem erro e a tela diz "✓ N novos" (s179).
  Cadastre o código real em `CODIGO_EXEMPLO` no `tools/audit_sharpenup.py`.

---

## Fase 6 — Gates antes do commit

| Gate | Comando | Exige |
|---|---|---|
| Regressão da captura | `node extensor/harness/run.mjs` | verde |
| Registro completo | `python tools/audit_sharpenup.py` | sem FAIL |
| Camada fina | `python tools/audit_casas.py` | sem FAIL |
| Sintaxe JS | `node --check extensor/<arquivos>.js` | verde |
| Manifest | `node -e "JSON.parse(require('fs').readFileSync('extensor/manifest.json'))"` | verde |
| Backend | `python -m py_compile app/*.py` + `pytest tests/` | verde |
| Marca (se tocou UI) | `node scripts/tokens/check-tokens.mjs` | verde |

Backup dos arquivos que serão editados em `Backups/<nome-descritivo>/` **antes** de editar.

---

## Fase 7 — Soltar e validar ao vivo

1. **Bump da `version` no `manifest.json`** — sem isso ninguém é avisado de que há versão nova.
   Qual dígito subir:

   | Dígito | Quando | Exemplo |
   |---|---|---|
   | **MAJOR** | Quebra de compatibilidade com o backend — a build antiga **para de capturar**, não só fica desatualizada. É o sinal de "atualize agora". | ainda não houve |
   | **MINOR** | Mecanismo novo de captura ou de distribuição; contrato novo retrocompatível. | `0.3.0` Betfair por JSON (nasce o `*_inject` passivo) · `0.4.0` link fixo + aviso de versão · `0.5.0` hook `wager-filter` · `0.6.0` bet365 por rota |
   | **PATCH** | Casa nova sobre mecanismo que já existe, fix, ajuste de parser, casa espelho. | `0.6.23` KTO · `0.6.25` Tivo · `0.6.30` VaideBet · `0.6.32` Betfast |

   > **Casa nova quase sempre é PATCH.** O minor é da *técnica*, não da contagem de casas —
   > 4 casas entraram dentro do `0.6.x` sem mexer no meio. Ficar em `0.x` indefinidamente é
   > esperado: a extensão **não vai para a Chrome Web Store** (a loja não aprova extensão de
   > apostas) e a distribuição é manual pelo link fixo, para sempre — então não existe marco
   > externo para forçar um `1.0.0`.

   A comparação é numérica por tupla (`_versao_tupla` em `app/main.py`), então `0.6.30 > 0.6.9`.
   Não há pressa técnica de virar o meio.
2. Commit + push (deploy Railway automático). `STATUS.md` na mesma sessão.
3. Peça ao operador: **recarregar a extensão** e **Ctrl+Shift+R na aba da casa** — recarregar
   a extensão *não* re-injeta em aba já aberta (armadilha recorrente).
4. Conectar → "Copiar bilhetes" → conferir no dashboard: contagem, datas, odds, código.
5. Marque no STATUS o que **não** foi validado ao vivo. Enquanto não rodou na casa, não rodou.

---

## Livro de armadilhas (pago em sessões)

**Dado**
- **Milésimos** — KTO: `stake 600000` = R$ 600,00, `line 8500` = 8.5.
- **Campo zerado em perdida** — KTO: `betOdds` = 0 em 100 % das perdas; a odd sai do dinheiro.
- **Odd truncada pela casa × retorno arredondado ao centavo** — a odd declarada vence **se**
  explicar o retorno até o centavo; senão o dinheiro manda. Nunca truncar.
- **Boost com duas naturezas** — odd sobe (`ODDS_BOOST`) ou lucro sobe X % (`PROFIT_BOOST`);
  `payout ÷ stake` resolve as duas (= regra global do W).
- **Array posicional** — Pinnacle: bilhete é array de ~98 campos; o de-para vive no inject e
  precisa de âncora validada contra a tela.
- **Odd fracionária** — bet365: `"21/20"` → 2,05.
- **Gramáticas diferentes no mesmo payload** — Betano: dinheiro `"R$1.914,56"` (ponto de
  milhar) e odd `"2.02"` (ponto decimal). Nunca use o parser de dinheiro numa odd.

**Data**
- **Fuso** — ISO com `Z` é UTC e precisa virar America/Sao_Paulo; sem `Z` costuma já ser local.
  Converter o que já é local pula um dia.
- **Formato muda sem aviso** — a Betfair passou de `18-jul-26` para `18-jul.-26` (com ponto) e
  **100 % das datas ficaram vazias**; como Data é a 1ª coluna, a linha inteira era rejeitada em
  silêncio. Regex de data sempre permissiva.
- **Data sentinela** — bet365: bet builder vem com `TP=00010101000000`; sem guarda vira
  "01/01/0001". Data falsa é pior que data ausente.

**Fluxo**
- **Aba já aberta não recebe o inject** ao recarregar a extensão → Ctrl+Shift+R.
- **iframe de outra origem** — bet365: a lista vive no iframe de membros; o `content.js`
  (`all_frames:false`) não alcança. Quem age tem de ser o inject.
- **Token rotativo** — bet365: `x-net-sync-term` muda por requisição; replay por API é
  impossível, só a própria página consegue chamar.
- **Cliques sintéticos** — o "Mostrar Mais" da bet365 checa `isTrusted` e não é automatizável.
- **Lista que volta ao topo** ao sair do detalhe torna a varredura O(n²).
- **Fim autoritativo ≠ heurística** — parar por "N rolagens sem novidade" perde bilhete em
  rede lenta. Use o sinal da casa; tempo é só rede de segurança.
- **Envio único** — o texto fica bancado em `envioPendente` até o servidor confirmar; sem isso,
  uma queda de rede joga fora minutos de raspagem.

**Silêncio**
- **Chunk sem bloco ```tsv some sem erro** (s179: 39 de 61 bilhetes). Só a conferência de
  cobertura pega — e ela depende da regex de código.
- **`respostas>0` e 0 bilhetes** = formato mudou. **`hook:false`** = inject não carregou.
  Sem o heartbeat, os dois viram o mesmo "nada coletado".
- **Marcador inexistente** — o chunker da bet365 procurava `[Bilhete Bet365]`, que nunca foi
  emitido: nada dividia e ninguém percebeu por semanas.

---

VERSÃO: 2026
ATUALIZADO: 2026-07-25 (sessão 194)
