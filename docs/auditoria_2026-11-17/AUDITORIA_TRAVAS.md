# Auditoria independente — lente TRAVAS (Sharpen, 17/11/2026)

Escopo: todo ponto do caminho extensão/print/PDF/texto → `/captura/*` → `/extrair` → IA/Ficha →
`/salvar` → banco em que uma ação legítima resulta em NADA (ou em menos) sem erro claro.
Fonte de verdade: o código e os diffs (`git log -S`, `git blame`), e execução real. Nenhum arquivo
do repo foi editado. Postgres de teste próprio no scratchpad (porta 55491, PG17 de Program Files).

Provas executáveis (todas no scratchpad `aud_travas\`):

| Arquivo | O que roda | Saída |
|---|---|---|
| `p_rotas.py` | app FastAPI real (TestClient) + Postgres de teste: print/PDF bloqueado, conta arquivada, conta errada, deploy, fila | `p_rotas.out` |
| `test_aud_d39.py` | harness real do repo (`tests/test_repository_db.py`), 7 capturas seguidas na casa virada | `p_d39.out` |
| `p_ext_409.mjs` | `extensor/background.js` + `cru.js` reais em sandbox Node, `chrome`/`fetch` dublados | `p_ext_409.out` |
| linha de comando | `repository.validar_linhas` com odd 0 | no corpo, T15 |

Regressão do repo usada como controle: `pytest tests/test_repository_db.py -k "d39 or segur or arquiv or barreira or incomplet"` → 11 passed.

---

## 1. Tabela das travas

Coluna "Data" = 1º commit em que o código da trava aparece (`git log -S`). **Negrito = últimos 60 dias** (desde 18/09/2026).
"Saída?" = existe mensagem acionável na tela de quem agiu E um caminho que destrava.

| # | Onde (arquivo:linha) | Data | Disparo | O que o usuário vê | Saída? |
|---|---|---|---|---|---|
| T1 | `captura.py:20-27,499` (sessões em memória) + `railway.toml` sem `watchPatterns` | 04/07 | todo deploy (todo push, inclusive só-docs) apaga `_SESSOES`; o token da extensão vira 401 | extensão: "Sessão expirou — reconecte no popup"; dashboard: "Sessão expirou. Conecte de novo." (só no próximo poll/envio) | Parcial: claro, mas obriga a repetir o pareamento manual a cada deploy (até 12 commits/dia em 01, 02 e 11/11) |
| T2 | `main.py:4294` + `ficha.py:519-522` | 13/07 | `origem` é host de OUTRA casa conhecida | extensão: "Casa incompatível…" | Sim |
| T3 | `extensor/popup.js` `hostBate` (até 0.7.84) | 13/07 → corrigido **17/11** | aba em domínio da própria casa fora da lista (espelho novo) | popup: "esta aba é <host>… gere um código para a casa certa" (falso) | Não, até instalar 0.7.85 (distribuição manual) |
| T4 | `captura.py:499` | 04/07 | 61ª captura não drenada | extensão: "Erro ao enviar (429)" no envio de TEXTO (o 429 só tem texto próprio no print) | Parcial |
| T5 | `main.py:4304` `_checar_conta_errada` | **28/09** | maioria dos códigos do lote já gravada em OUTRA conta do mesmo dono e casa | servidor manda "Conta incompatível: N de M já são da conta X…"; a extensão **descarta o detail e mostra "Casa incompatível — o site não corresponde à conexão"** | Não (mensagem errada); ver Achado A2 |
| T6 | `ficha.py:551-560` (cru) | **14/11** | mesma regra de T5 sobre o cru | nada: 200 com `conta_errada`, a extensão marca o cru como enviado e não sinaliza | Não precisa (o cru fica guardado), mas é invisível |
| T7 | `main.py:4112/4140/4478` `_trava_conta_arquivada` | **13/11** | parear ou extrair numa conta arquivada sem `confirmar_arquivada` | modal "Processar nesta conta?"; 409 com texto claro se o cadastro da tela estava velho | Sim isolada; **combinada com T5 vira beco** (Achado A1) |
| T8 | `main.py:4481` + `captura.py` `CASAS_COM_FICHA` | **11/11** | print ou PDF em 30 casas (`1WIN`…`VAVE`; só `GIROCERTO` liberada em 16/11) | 400 "Esta casa é extraída pela extensão SharpenUp…"; a tela já barra antes | Só se a extensão funcionar naquela casa/domínio (T3, T1) |
| T9 | `main.py:4547` `_corte_historico_text` | **10/09** | (dono, casa) no mapa `_CORTE_HISTORICO` e data do evento < corte | "N anterior(es) ao corte da casa" | Sim (só afeta `feca`) |
| T10 | `main.py:4570` → `_dedup_superbet_text:1563` `ja_resolvidos` | 22/06 (escopo de conta 2026-09) | código já `resolvida` NESTA conta (exceto reliquidação de classe, s448) | "N já salva(s)" | Por desenho; corrigir resultado errado só à mão |
| T11 | `main.py:1576` barreira (`bloco_visto`) | **09/09**; `gravados=True` **20/10** | bloco idêntico ao da última leitura E a linha atualizada depois do hash | conta como "já salva" | Sim desde s424 |
| T12 | `virada.py:377` D10 `_liquidados` | **12/10** | código liquidado no banco nesta casa: a Ficha nunca reescreve | nada | Por desenho |
| T13 | `virada.py:757-790` + `main.py:1571` D39 (b) "segurar" | **01/11** | casa virada; cru guardado ABERTO com texto mudado, ou cru que não chegou (e a casa mandou cru deste dono nos últimos 7 dias) | card: "captura incompleta (N esperando): atualize a aba da casa (F5) e extraia de novo" | Automática após 2 `/extrair` ou 24 h; o F5 sugerido **não reenvia cru de hash igual** (`cru.js`, chave `cruEnviado`) |
| T14 | `virada.py:583` `ja_foi` (D39, "uma vez") | **01/11** | segurada que esgotou já foi à IA uma vez com ESTE cru | nada | **Não** — Achado A3 (comprovado) |
| T15 | `main.py:4806` `validar_linhas` + `4860` câmbio | 03/07, 29/06 | stake/odd/data ilegível ou ≤0; sem cotação | `200`; card "⚠️ N alerta(s)", **o texto do alerta e `rejeitados` nunca aparecem na Extração** (só na página Logs, desde 29/10) | Parcial |
| T16 | `main.py` `_reconciliar_orfas` | **06/09** | linha sem código fiel a bloco que já tem linha | só contagem em log | Por desenho |
| T17 | `main.py` `_corrigir_codigos_fantasma` (esvazia) | **13/09** | código da IA fora do texto e sem par único | linha gravada sem código (vira órfã) | Parcial |
| T18 | `main.py:695-714` leitor `conferir_linha` | **14/10** | linha da IA fora do tipo | vira "faltante" → "N NÃO foram extraídos — REPROCESSE" | Sim |
| T19 | `ficha.py:536-540` cru > 64 KB | **11/10** | cru filtrado acima de `MAX_BYTES` | nada; a extensão recebe 200 e **marca como enviado** | Não para o cru; o código cai em T13 (segurado 2 capturas) e depois T14 |
| T20 | `ficha.py:488` `CRU_CAPTURA_DESLIGADA` | **11/10** | env ligada | nada (503, extensão reenvia depois) | Sim |
| T21 | `extensor/cru.js` `cruEnviado` (chave `host\|família\|código`, 60 dias) | **12/10** | cru de hash igual já mandado uma vez, para QUALQUER sessão/dono/conta | nada | Não — Achado A4 |
| T22 | `main.py:4470` teto do trial | **13/09** | 10 extrações no `trial_` | 429 claro | Sim |
| T23 | `virada.py` (c) `sem_linha` / `nao_lida` (s423) | **19/10**, **01/11** | código foi à IA e não virou linha; Ficha recusou e texto não trouxe | aviso de contagem no card | Parcial (só avisa, não regrava) |
| T24 | `virada.py:805-808`, `ficha.py`, `repository.py` — 78 `except Exception`; **45 tocados nos últimos 60 dias** (virada 9/9, ficha 9/9, dicionario 4/4, repository 13/21, main 10/35) | — | falha de banco/rede no meio da decisão | nada (fail-open: vai à IA ou não trava) | Aceitável no geral; não esconde perda, mas esconde motivo |

Contagem: das 24 travas, **16 nasceram ou mudaram de comportamento nos últimos 60 dias**, e **7 só entre 01/11 e 14/11** (T6, T7, T8, T13, T14, T23(c), `texto_desmente` s447). Churn no mesmo período: `main.py` 88 commits (+2.115), `repository.py` 50 (+2.572), `virada.py` 23 (+1.382 de 1.049 linhas atuais: reescrito mais de uma vez), `extensor/content.js` 59 (+3.084). 381 commits em 47 dias com commit (mediana 5/dia, máx. 38); cada push é deploy.

---

## 2. Achados

### A1 — O usuário que volta e tem a conta antiga arquivada fica entre duas travas que mandam em sentidos opostos (COMPROVADO)

- **Sintoma:** ele arquivou a conta "velha" (ou ela foi arquivada por ele/alguém meses atrás), cria/usa uma "nova" para o mesmo login da casa, pareia, captura: a extensão diz "Casa incompatível — o site não corresponde à conexão". Ele está no site certo.
- **Mecanismo:** T5 vê que 10 de 10 códigos já moram na "velha" e recusa (409). A mensagem do servidor manda "gere o código da conta certa", que é a arquivada; lá T7 exige confirmação para "processar novas apostas" numa conta arquivada. A única saída é gravar de novo na conta que ele arquivou de propósito. E a mensagem que chega à tela da extensão nem é essa (A2).
- **Evidência:** `p_rotas.out`, itens 2/2b/3: `409 "A conta velha está arquivada desde 01/06/2026…"` nos dois pontos de entrada e `409 "Conta incompatível: 10 de 10 bilhetes desta captura já são da conta velha, não da nova…"` no envio pela conta nova.
- **Severidade:** alta para quem volta (é exatamente o estado que meses de uso deixam: histórico numa conta, contas reorganizadas). **Família:** travas de "proteção de conta" criadas cada uma para um incidente (s388, s453), sem teste da composição.
- **Correção estrutural:** a trava de conta errada precisa saber que a "outra conta" está ARQUIVADA (ou ser de mesma credencial de casa) e oferecer "mover o histórico para esta conta" em vez de recusar; e toda recusa tem de carregar o `detail` do servidor até a tela que agiu.

### A2 — A extensão joga fora a mensagem do servidor em 409/429 (COMPROVADO)

- **Sintoma:** qualquer 409 no envio de texto aparece como "Casa incompatível — o site não corresponde à conexão"; 429 aparece como "Erro ao enviar (429)".
- **Mecanismo:** `extensor/background.js:158,197` têm texto fixo; o `r.json().detail` nunca é lido. O comentário do servidor (`main.py`, junto de `_checar_conta_errada`) diz que isso valia "até a 0.7.33" — **falso na 0.7.86 atual**.
- **Evidência:** `p_ext_409.out`: servidor devolve "Conta incompatível: 9 de 10…", toast exibido = "Casa incompatível — o site não corresponde à conexão…". Para o cru recusado por conta errada (T6): 0 toasts.
- **Severidade:** alta (transforma travas COM saída em travas sem saída). **Família:** canal de retorno genérico (mesma de A5).
- **Correção:** um único formatador de erro na extensão que mostra o `detail` de qualquer não-2xx; teste que percorre todo `HTTPException` das rotas `/captura/*` e confere que o texto chega ao toast.

### A3 — Aposta segurada pela D39 que "esgota" vai à IA uma vez e, se essa leitura não chegar ao banco, sai do lote para sempre, sem aviso (COMPROVADO)

- **Sintoma:** aposta liquidada na casa continua ABERTA no Sharpen; recapturar não muda nada; nenhum aviso.
- **Mecanismo:** `virada._saida` marca `ja_foi` quando `motivo = ESGOTADA` e a impressão do cru é a mesma (`virada.py:583`); `ja_foi` entra em `segurados`, que `_dedup_superbet_text` tira do lote (`main.py:1571`). Nada confere se a ida à IA virou linha. O aviso (c) `sem_linha` só olha código SEM linha; aqui a linha aberta existe, então nem aviso há. O teste do próprio repo (`test_d39_segurada_esgota…`, `lidos5 == []`) **afirma** esse comportamento como correto.
- **Evidência:** `p_d39.out` — lote da IA por captura `[[], ['5500000003'], ['5508528206'], [], [], [], []]`: a aposta foi à IA uma vez (captura 3), a leitura não foi salva, e nas capturas 4–7 nunca mais; linha `{'extraction_state': 'aberta', 'resultado': None}`; avisos `{}`. A outra (sem cru) também foi uma vez e não tem linha.
- **Quando dispara de verdade:** texto muda sem o cru mudar (cashout na tela, cru maior que 64 KB descartado — T19, cru vindo de endpoint de lista desatualizado) **e** a única ida à IA falha em gravar (aba fechada antes do `/salvar`, linha recusada pelo leitor/`validar_linhas`, chunk falho, deploy no meio — T1). HIPÓTESE quanto à frequência real; o mecanismo é comprovado.
- **Severidade:** alta (perda silenciosa de liquidação = P/L e Caixa errados). **Família:** "marca de já-tratado gravada antes de o dado chegar ao banco" — a mesma de s424 (barreira), s429, s447, s451, s453, todas consertadas uma a uma.
- **Correção estrutural:** "já foi" só pode valer depois de provado que a leitura gravou (mesma régua `gravados=True` da barreira: `bilhetes.atualizado_em >= ficha_virada.atualizado_em`). Uma régua só de "lido" para barreira, Ficha e D39.

### A4 — A memória "cru já enviado" da extensão não tem dono, conta nem sessão (COMPROVADO)

- **Sintoma:** depois de parear em outra conta/dono, ou de o servidor descartar o cru (T19) ou gravá-lo sem montar Ficha, F5 não reenvia nada; o card manda "atualize a aba (F5)".
- **Mecanismo:** `extensor/cru.js` chave `origem|familia|codigo` (+hash), válida 60 dias; o servidor guarda e procura o cru por `dono + casa`. Cru mandado sob o dono A nunca chega ao dono B no mesmo navegador (operador, "ver como", contas de família). E 200 com `descartados` é marcado como enviado.
- **Evidência:** `p_ext_409.out`: `chave_do_registro: ["www.mystake.com|x1|C1"]`; segundo envio do mesmo cru → `iguais: 1, enviados: 0, http: []`.
- **Severidade:** média (há saída automática via T13→esgota→IA, mas cai em A3). **Família:** escopos de memória divergentes (ver seção 3).
- **Correção:** chave do registro inclui o token/sessão (ou o servidor devolve por item "guardado/descartado" e só o guardado é marcado); o aviso "F5" só aparece quando F5 de fato resolve.

### A5 — O que o `/salvar` recusa nunca aparece na tela de Extração (COMPROVADO)

- **Sintoma:** "✓ 3 novos · ⚠️ 1 alerta(s)"; a aposta recusada não está na lista; não diz qual nem por quê.
- **Mecanismo:** `/salvar` responde `200` com `rejeitados` e o texto em `alertas`; `app/static/index.html` não lê `rejeitados` em lugar nenhum (`grep` = 0 ocorrências em `app/static`) e mostra só `ds.alertas.length` (linhas 7858, 7887, desde 20/06 e 29/10). O texto vai à página Logs (`fechar_extracao`, s433) — outra tela, admin-orientada.
- **Evidência:** `validar_linhas` com odd `0` → `aceitas ['C2']`, `rejeitadas [{linha 1, campo odd, valor '0', erro 'odd inválido…'}]`; o card mostraria "1 alerta(s)".
- **Severidade:** média. **Família:** canal de retorno = contagem (mesma de A2, T13 "N esperando", T23).
- **Correção:** o card lista os alertas (no mínimo o 1º com "ver todos"), e a linha recusada aparece na grade como "não salva" com o motivo.

### A6 — Cada deploy derruba o pareamento; deploy acontece a cada commit (COMPROVADO o mecanismo; contagem de deploys = HIPÓTESE)

- **Mecanismo:** `captura._SESSOES` é dict em memória (docstring admite); `railway.toml` sem `watchPatterns` ⇒ todo push redeploya, inclusive commit só de `STATUS.md`/docs; a regra do repo é commit+push sempre. Processo novo ⇒ token 401; a extensão apaga o token (`background.js:147-151`), o cru vai a 401 em silêncio.
- **Evidência:** `p_rotas.out` item 4 — depois de recarregar o módulo (processo novo), `/captura/enviar` → `401 "Token de captura inválido ou expirado."`. Commits/dia: 10 (01/11), 12 (02/11), 12 (11/11), 6 (12/11), 5 (13/11), 6 (14/11).
- **Severidade:** alta na percepção ("não funciona mais"): o usuário que volta e passa o dia capturando é desconectado várias vezes, e cada desconexão aparece só no próximo envio. **Família:** infraestrutura efêmera + cadência de deploy.
- **Correção:** sessão de pareamento persistida (tabela, com o mesmo TTL) e `watchPatterns` excluindo `docs/`, `STATUS.md`, `BACKLOG.md`, `tests/`.

### A7 — Bloqueio de print/PDF em 30 casas depende de a extensão funcionar naquela casa (COMPROVADO o bloqueio; dependência = HIPÓTESE parcial)

- **Mecanismo:** desde 11/11 (`cc27bd3`) `/extrair` recusa imagem/PDF nas 30 casas de `CASAS_COM_FICHA` antes de qualquer coisa. Quem voltava a usar print nessas casas agora só tem a extensão, que tem suas próprias travas de domínio (T3 até 17/11 na versão nova; continua em quem não atualizou; o `matches` do manifest não injeta em domínio novo) e de sessão (T1). Exceção já precisou ser aberta 5 dias depois (`PRINT_LIBERADO = {GIROCERTO}`, 16/11).
- **Evidência:** `p_rotas.out` itens 1/1b/1c (lista das 30).
- **Severidade:** alta para esse perfil. **Família:** trava nova que remove a rota de fuga das outras.
- **Correção:** print bloqueado só quando a extensão daquela conta mandou cru recentemente; senão aceitar com aviso.

### A8 — Família "liquidada na casa, aberta no Sharpen", consertada por casa (COMPROVADO pela série de diffs; não reexecutado)

13 commits `fix` em 60 dias com "ficava/deixa de ficar aberta / a conferir / presa" (CopaWin ×3, Stake.com ×2, 1win ×2, Betrebels, barreira s424, Ficha s447/s451/s453…). Duas raízes distintas: (a) o formatador da extensão tem `else` "a conferir" para rótulo desconhecido (por casa); (b) memórias de "já visto" do servidor fora de sincronia (A3/A4/seção 3). Os adaptadores da Ficha, ao contrário, RECUSAM status desconhecido (vai à IA) — é o padrão correto e não está no texto.

---

## 3. Causa sistêmica

1. **Camadas de "pular" empilhadas, cada uma com memória própria e escopo próprio.** Antes da IA o lote passa por: corte → `ja_resolvidos` (dono+casa+**conta**) → barreira `bloco_visto` (dono+casa, com JOIN em `bilhetes`) → Ficha/`ficha_virada` (dono+casa, sem conta até 14/11) → D39 segurar/`ja_foi` (dono+casa+impressão) → RC44. Na extensão, `cruEnviado` (host+família, **sem dono**). Toda ação legítima que muda escopo — apagar e recapturar, arquivar, mover conta, trocar de dono no mesmo navegador, leitura que não salvou — deixa uma camada dizendo "já tratei" enquanto outra não tem o dado. Os consertos s424, s429, s447, s451, s453 e RC44 são **o mesmo defeito em pontos diferentes**; cada um corrigiu UMA camada.
2. **Travas novas nascem fail-closed (segurar/recusar) com saída desenhada para o incidente que as criou**, não para o estado que o usuário antigo carrega. 7 travas em 14 dias (01–14/11). Composição nunca testada: A1 é T5×T7; A3 é T13×T1/T15.
3. **O canal de volta é contagem ou texto fixo.** "N alerta(s)", "N esperando", "Casa incompatível" (errado), "Erro (429)". A trava tem mensagem boa no servidor e ela morre no caminho (A2, A5).
4. **A cadência de deploy (até 12/dia, todo push) apaga estado em memória** (pareamento, `_em_voo` da espera do cru) e faz o sistema "esquecer" o usuário várias vezes por dia (A6).

Para quem volta depois de meses, as quatro somam no mesmo dia: extensão velha que barra o domínio (T3) → atualiza → print bloqueado (T8) → pareia na conta nova e toma "Casa incompatível" (A1/A2) → descobre a arquivada (T7) → deploy derruba o pareamento (A6) → aposta liquidada que fica aberta sem aviso (A3). É o "4-5 problemas no mesmo dia".

**Correção estrutural proposta (uma, não 24):** um registro único de "leitura confirmada" por (dono, casa, conta, código, impressão), gravado SÓ pelo `/salvar` (ou pela Ficha quando ela grava), que todas as camadas de pular consultam; toda trava devolve `{codigo, motivo, saida}` por item até a tela que agiu; e um teste de composição que roda o cenário "usuário que volta" (conta arquivada + conta nova + extensão sem cru + deploy no meio) ponta a ponta.

---

## 4. O que não consegui verificar

- **Produção:** quantas apostas estão hoje em `ficha_virada` com `motivo='captura incompleta esgotada'` e linha aberta (o tamanho real de A3); quantos 409 de conta errada por dia; valor real de `FICHA_CASAS_VIRADAS`, `FICHA_SOMBRA_CASAS`, `CONTRATO_TEXTO_CASAS`, `VIGIA_POR_DIA` (as travas da virada só valem nas casas listadas lá).
- **Deploys reais:** contei commits; não tenho o histórico da Railway (pushes podem agrupar commits).
- **Extensão em navegador real:** o `matches` do manifest em domínio espelho novo (inject que não entra = robô que não coleta nada) e o fluxo do popup foram lidos, não executados; só `background.js`/`cru.js` rodaram em sandbox.
- **Front no navegador:** a leitura de `index.html` (contagem de alertas, aviso F5) foi estática; não renderizei a tela.
- **sharpen-bot / socantos-bot** (outro repo): não auditados; escrevem pelo `/salvar` e herdam A5.
- **Frequência dos gatilhos de A3** (texto muda sem cru mudar): mecanismo provado; frequência é HIPÓTESE.
- Não li `content.js` inteiro (21 mil linhas de extensão); o `else` "a conferir" por casa (A8a) foi inferido dos diffs dos consertos, não auditado casa a casa.
