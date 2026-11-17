# Plano de confiabilidade (auditoria de 17/11/2026)

Decisão do Feca em 17/11/2026: depois da auditoria independente, **atacar todos os pontos
necessários sem pedir aprovação passo a passo**, chamando o Feca só em caso de necessidade.
Cenário: usuário frequente (Gabriel) reclamando com regularidade; usuário que voltou depois
de meses (Arruda) com 4 ou 5 problemas no mesmo dia (caixa que não bate, extração falhando
em vários sites, números que não batem).

Os seis relatórios, cada um de um agente que não leu os outros nem a documentação do repo:

| Relatório | Lente |
|---|---|
| [`AUDITORIA_NAVEGADOR.md`](AUDITORIA_NAVEGADOR.md) | cache e estado no navegador |
| [`AUDITORIA_SERVIDOR.md`](AUDITORIA_SERVIDOR.md) | caches, tarefas de fundo e marcadores do servidor |
| [`AUDITORIA_EXTENSAO.md`](AUDITORIA_EXTENSAO.md) | SharpenUp e o contrato com o servidor ao longo do tempo |
| [`AUDITORIA_TRAVAS.md`](AUDITORIA_TRAVAS.md) | toda ação legítima que vira "nada" sem erro |
| [`AUDITORIA_GIT.md`](AUDITORIA_GIT.md) | forense do histórico: ritmo, hotspots, famílias |
| [`AUDITORIA_ESCALA.md`](AUDITORIA_ESCALA.md) | concorrência, consistência e escala |

As provas reexecutáveis ficaram no scratchpad da sessão (temporário); os relatórios citam os
nomes dos scripts. Produção **não** foi auditada (acesso negado pelo classificador de
permissões); por isso nenhum número aqui é frequência real.

**Medida na s460** (só leitura, autorização do Feca):
[`MEDICAO_PRODUCAO.md`](MEDICAO_PRODUCAO.md), harness em `tools/medicao_producao/`. Abriu
os itens **2.6**, **5.5** e **6.6** abaixo.

---

## 1. Diagnóstico em uma página

**A taxa de erro por mudança não piorou** (≈36% dos feats levam fix em 30 dias, de junho a
novembro). O que mudou foi a superfície e o tipo de falha:

- comparações `casa === 'literal'` no JS: 4 → 114; linhas que recusam/seguram/pulam aposta: 33 → 211;
  16 das 24 travas nasceram nos últimos 60 dias, 7 delas entre 01 e 14/11;
- a idade mediana do código consertado foi de < 1 dia para 25,5 dias: a falha passou de
  barulhenta a **silenciosa** (aposta aberta, segurada ou pulada sem erro).

Cinco causas-raiz, cada uma achada por mais de um agente:

| # | Causa | Sintoma do usuário |
|---|---|---|
| R1 | Estado que precisa sobreviver vive na memória do único processo, e todo push é deploy | extensão "desconecta sozinha"; captura que some com "enviado ✓" |
| R2 | Várias memórias de "já tratei", cada uma com escopo próprio, decidem o que pular | aposta liquidada na casa, aberta no Sharpen; F5 não resolve |
| R3 | Liquidação reimplementada casa a casa | números e Caixa que não batem |
| R4 | O código não tem identidade de versão (navegador e extensão) | "consertei e voltou"; funciona para um e não para outro |
| R5 | Processo único sem teto nem trava (pool, event loop, IA, escrita sem transação) | lentidão geral; Caixa e custos perdendo atualização |

Achado à parte, o mais grave: **dado de um usuário aparece e é gravado na conta de outro no
mesmo navegador** (IndexedDB `dados_v1` sem dono; `custoTipsterData`/`custoGeralData` globais
semeando o servidor).

---

## 2. Plano de execução

Ordem decidida por gravidade × risco. Cada item é um commit (ou poucos), com teste provado
por mutação e o gate do projeto. **Status:** `[ ]` aberto · `[x]` feito (com o commit).

### Fase 1 — Vazamento entre usuários (gravidade máxima, mudança pequena)

- [x] **1.1** (`ff6af74`) IndexedDB do feed com chave por dono (`dados_v1` → por dono resolvido antes de
  pintar), registro com `{dono, schema}`, descarte se divergir. (NAV C3, M3, B2)
- [x] **1.2** (`ff6af74`) Custo de tipster/geral: nunca ler nem semear a partir das chaves globais
  `custoTipsterData`/`custoGeralData`; o servidor é a fonte. (NAV C4)
- [x] **1.3** (`ff6af74`; o /login apaga o IndexedDB) Logout e "ver como" limpam o estado do navegador que é dado de usuário. (NAV C3)
- [x] **1.4** (`03b30d4`) Tirar `DEFAULT 'Feca'` de `bilhetes.dono`, `parceiros.dono` e da 3ª tabela,
  depois de conferir que todo INSERT passa `dono`. (ESC A12)
- [x] **1.5** (`ff6af74`) `no-store` das rotas HTML deixa de ser apagado pelo middleware; `pageshow`
  persistido revalida sessão. (NAV M2)

### Fase 2 — Parar de derrubar todo mundo

- [x] **2.1** (`32ca46b`) `watchPatterns` no `railway.toml`: commit só de docs/STATUS/BACKLOG/tests/tools
  não faz deploy. (TRAV A6)
- [x] **2.2** (`dd51d08`; o invólucro do pool entrou no commit do 1.4, mesmo arquivo) Pool com `timeout` de aquisição, `command_timeout`, `statement_timeout` e
  `lock_timeout` por sessão. (ESC A3)
- [x] **2.3** (`dd51d08`) Login com bcrypt fora do event loop (`to_thread`). (ESC A5)
- [x] **2.4** (`ee29d2e`; falta: dashboard recarregado perde o id da sessão, a fila daquela sessão expira em 6 h) Sessão de pareamento e fila de captura no Postgres, com confirmação de entrega
  (a captura só sai da fila depois do ack do dashboard); o deploy deixa de derrubar o
  pareamento. (SRV P3, EXT A1, ESC A6, TRAV A6)
- [x] **2.5** (`a04747b`) Tarefas de fundo com referência guardada e log de morte. (SRV P12)
- [ ] **2.6** (s460, medido) `enviar` para sessão encerrada no mesmo instante bate na FK de
  `captura_fila` e responde 200 "em memória": a captura some com "enviado ✓". Responder
  como sessão inexistente. (MEDICAO §3)

### Fase 3 — Identidade de versão

- [x] **3.1** (`b2a4d8b`) `BUILD_ID` em header e no `/eventos`; a casca recarrega quando muda, em momento
  seguro. (NAV C1, M5)
- [x] **3.2** (`b2a4d8b`) Assets com versão pelo hash do conteúdo, calculada pelo servidor; fim do `?v=`
  manual; gate que barra `?v=` literal; `Cache-Control` explícito; APIs com `private, no-store`.
  (NAV C2, M1, M4; SRV P8)
- [x] **3.3** (`74def2e`; mínima por casa onde a antiga comprovadamente captura errado; aviso com gravidade segue aberto) Versão mínima da extensão, global e por casa, cobrada em conectar/validar/enviar
  com mensagem acionável; aviso de versão com gravidade. (EXT A3)
- [x] **3.4** (`42bafee`; detecção pela hora da atualização × hora da aba, sem mudar os 31 injects; o FAB do content ainda não passa por ela) Inject carimba a versão; reinjeção idempotente; versão divergente pede F5 em vez
  de rodar o código velho. (EXT A2, A9)

### Fase 4 — Escrita consistente

- [ ] **4.1** `upsert_bilhetes` numa transação por lote + advisory lock por conta. (ESC A2, A7)
- [x] **4.2** (`19d24e4`) `abertas_corte` atualizado de forma atômica em todos os escritores. (ESC A8)
- [x] **4.3** (`19d24e4`) Custos com controle de versão (409 em conflito) ou escrita por item. (NAV A1, ESC A11)
- [x] **4.4** (`a04747b`) Invalidação de cache pelo banco (matcher, categorias); LISTEN que reconecta avisa
  todos; ping com timeout. (SRV P6, P7)
- [x] **4.5** (`1a66739`) Identidade: o refresher não grava snapshot mais velho que o atual. (SRV P1)
- [x] **4.6** (`1a66739`) Nunca cachear ramo de erro (categorias) nem dia ainda não fechado (PTAX); planilha
  viva com idade máxima e `builtAt` verdadeiro. (SRV P4, P5, P9) — **PTAX coordenar com a
  sessão s458**, que está mexendo em `cambio.py`/`polymarket.py`.

### Fase 5 — Uma régua de "leitura gravada" (R2)

- [x] **5.1** (`1a379cb`) Prova atômica: `bilhetes.lido_em`, que só o UPSERT de uma leitura move (em vez do
  hash na linha, que exigiria levar o hash do `/extrair` ao `/salvar`). (SRV P10)
- [x] **5.2** (`1a379cb`) D39: "já foi à IA" só vale com a leitura provada no banco; o teste que afirma o
  contrário é corrigido. (TRAV A3)
- [x] **5.3** (`ad6b76a`) Ficha: cru marcado como processado só no fim; reenvio reprocessa o que não
  terminou. (ESC A9)
- [x] **5.4** (`4db68bc`, SharpenUp 0.7.88) `cruEnviado` da extensão com escopo de sessão/dono, e marcado só com o que o
  servidor guardou. (TRAV A4)
- [ ] **5.5** (s460, medido: as 9 do arrudex) Cru cuja linha o `/salvar` interno recusou por
  motivo transitório (câmbio) não conta como processado; o cru igual seguinte reprocessa.
  (MEDICAO §1, §6-A)

### Fase 6 — O usuário vê o que aconteceu

- [x] **6.1** (`42bafee`, SharpenUp 0.7.87) A extensão mostra o `detail` de qualquer não-2xx. (TRAV A2)
- [x] **6.2** (`42bafee`) A Extração mostra os alertas e as linhas recusadas pelo `/salvar`. (TRAV A5)
- [x] **6.3** (`718e8cf`, parcial: Início e Dashboard; o wrapper único de fetch para as outras telas segue aberto) Um wrapper de fetch: 401 vai ao login, falha mostra "sem conexão, dados de HH:MM",
  só sucesso mexe no carimbo de sincronização. (NAV A2, A3, B3)
- [x] **6.4** (`74def2e`, parcial: a recusa explica e dá a saída; mover histórico entre contas pela tela segue aberto) Conta errada × conta arquivada deixa de ser beco sem saída. (TRAV A1)
- [ ] **6.5** Captura parcial declarada (completo/parcial:motivo) e mostrada. (EXT A5)
- [ ] **6.6** (s460, medido: arrudex 21 capturas × 3 `/extrair`) A parte que a Ficha deixa
  para a IA espera um "Processar" que não vem, e a grade já mudou. **Decisão do Feca:**
  destacar o número na Extração ou disparar o `/extrair` sozinho. (MEDICAO §5, §6-D)

### Fase 7 — Volume

- [x] **7.1** (`9c72bf6`, lado servidor: campo até 16 MB; fatiar na extensão continua aberto) Envio da extensão fatiado e limite de parte explícito no servidor com 413
  acionável. (EXT A4)
- [ ] **7.2** `envioPendente` vira fila com destino conferido no Reenviar; sem poda muda. (EXT A7)
- [x] **7.3** (`ec23947`, parcial: transformação + JSON/gzip em thread; falta decode do asyncpg, cache por dono e feed incremental) Feed do dashboard montado fora do event loop, com cache por dono invalidado pelo
  `base_mudou`. (ESC A1)
- [ ] **7.4** Trigger `base_mudou` por comando, não por linha. (ESC A2)
- [x] **7.5** (`3d96fae`, parcial: teto global 16; falta cota por dono) Limitador global e por dono de chamadas à IA. (ESC A4)
- [ ] **7.6** Horizonte da captura decidido pelo servidor por conta. (EXT A6)

### Fase 8 — Liquidação com contrato único (R3)

- [ ] **8.1** Teste de contrato igual para todas as casas (cashout, perna anulada, meia
  asiática, devolução) sobre as fixtures do harness. (GIT família L)
- [ ] **8.2** Resultado decidido pelo dinheiro no servidor (`_veredito_do_retorno`) quando o
  rótulo da casa é desconhecido. (GIT família L, TRAV A8)

---

## 3. Regras desta execução

- Cada push ainda é deploy e (até a 2.4) derruba o pareamento de todos: **agrupar** o que for
  da mesma fase e evitar push em horário de pico de captura quando der.
- Outra sessão (s458) está ativa: `git add` por nome e `commit` no mesmo comando; nunca tocar
  `app/cambio.py`, `app/casa_chave.py`, `app/polymarket.py` enquanto estiverem modificados
  no working tree; `STATUS.md` só quando ele não estiver modificado por ela.
- Mudança de schema roda primeiro no Postgres local de teste.
