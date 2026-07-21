# STATUS — Masters & Casas (FDC Capital / Planilhador)

Documento de rehydration de sessão. Quem abrir o Claude Code neste repo lê isto primeiro.

> ⚠️ **STATUS ≠ fonte de regras.** Este arquivo é um **changelog/rehydration** (o que mudou e por quê). As regras vinculantes vivem nos **`global/MASTER_*`** (domínio de apostas), em **`pack/tokens/tokens.css`** + **`pack/CLAUDE.md`** (marca/design) e nos **`CLAUDE.md`** (operacional). Não decida uma regra consultando o STATUS — siga o ponteiro para o canônico.

Repo local: `C:\Users\Fernando\Downloads\FDC Capital\Planilhador`

_Atualizado: 2026-07-21 (sessão 172 — **Pinnacle entrou no SharpenUp (modo texto) + faixa "Novidades" na home.** **1. Pinnacle vira casa de robô** (commits `8355423` back+extensão, `344b4e8` gate do front). Antes só dava print; agora o SharpenUp puxa o dado exato por hook JSON, como Betano/Betfair. **Como:** `extensor/pn_inject.js` (novo, mundo MAIN) faz hook do `POST /member-service/v2/wager-filter` — cada bilhete é um **array posicional** (~98 campos, SEM nomes), convertido em objeto nomeado por de-para ancorado (0=P/L, 6=WIN/LOSE, 7=ID, 9/10=confronto, 14=colocação, 15=data-evento, 16=odd, 18=SETTLED, 20/22=seleção, 24=linha, 28=liga, 29=stake, 31=esporte, 44=pernas-múltipla, 45=categoria, 46=unidade, 93=WON/LOST/PUSHED). **Replay ativo** (espelho do `bf_inject`): re-emite a busca das DUAS abas numa rodada — `s=SETTLED&type=WAGER` (encerradas, janela de dias) + `s=OPEN&type=EVENT` (abertas, todas); campos `s/type/sd/f/t/d` confirmados nos dois Payloads reais (`sd=false` nas duas, `type` é o discriminador junto do `s`). `content.js`: `formatTicketPN`, `roboPinnaclePassive`, `pnById` (SETTLED vence aberta), autodiagnóstico. `captura.py`: PINNACLE=texto + host. `popup.js`: injetor MAIN + guard. `manifest` 0.4.0→**0.5.0**. Parser+formato **validados contra o dump real** (ML/OU/prop-WNBA/Mix-Parlay) e os goldens da CASA_PINNACLE. Feca testou ao vivo: **funcionou.** Fiel à §4 (data=evento), §1 (ponto→vírgula), §6/§7 (sem boost/cashout), §13 (`-vs-`→`v`, esporte≠liga). **Pendente:** confirmar o formato do bilhete ABERTO real (trato `≠SETTLED`→aberta; se índice deslocar em aberta é ajuste de 1 linha). **2. Faixa "Novidades" na home** (`inicio.html`): changelog dev-controlado (array `NOVIDADES`, mesmo p/ todos os donos), faixa larga abaixo dos KPIs; some sozinha após `NOV_DIAS=45`; badge "novo" some depois que o dono vê (localStorage `sharpen_novidades_seen::<dono>`). 1ª entrada = a própria Pinnacle. Reusa a casca `.panel/.ph`, cor 100% token, data em fuso local (nunca UTC), sem dinheiro/formatador. Gate `/nova-ui` cumprido: JS `vm.Script` OK, `check-tokens` verde, render headless conferido. Backups `Backups/sessao170-pinnacle-sharpenup/` e `Backups/sessao172-novidades-inicio/`. **Segurança:** Feca colou cookies de sessão vivos da Pinnacle no chat (JWT `sb`/`BIAB_CUSTOMER`, `cf_clearance`) → recomendei trocar a senha. **Não meu (intocado):** untracked `docs/PESQUISA_BADMINTON_2026.md` e `docs/DESAMBIGUACAO_RAQUETE_2026.md`. Ver [[pinnacle_sharpenup]] · [[extensor_captura]] · [[feedback_nova_ui_gate_total]].)_

_Anterior: 2026-07-21 (sessão 171 — **Onboarding do Gabriel + Extração passou a aceitar PDF.** Três frentes numa sessão. **1. Login do Gabriel no ar.** O perfil já existia no código (dono solo, commit `0df72cc`), mas faltava a senha: no Sharpen a senha não fica no código, vem da env `SENHA_<USER>_HASH` no Railway (fail-closed). Gerei o hash bcrypt de "Coxa", o Feca setou `SENHA_GABRIEL_HASH` no Railway. Testado em prod: `Gabriel`/`Coxa` retorna `{ok:true}`; senha errada dá 401. **2. 5 apostas Bet365 do Gabriel importadas (dia 03/07).** Vieram num PDF do extrato "Apostas Resolvidas". Rodei pela Extração real, sem furar o pipeline: renderizei as páginas do PDF em PNG (PyMuPDF), mandei no `/extrair` (IA + MASTERs Bet365), revisei o TSV e salvei via `/salvar`. Ids 63349-63353, P/L do dia +331,88, turnover R$800. Resultados W/L/HL conferidos à mão contra o retorno de cada bilhete. Boost tratado: bilhete Auger Aliassime com "Ganhos Aumentados 25%" gravou odd 2,7188 (Retorno÷Stake), não a 2,37 exibida. 2 bilhetes sem confronto porque o extrato da Bet365 nesta view não mostra o adversário. **3. Sharpen passou a aceitar PDF na Extração (`692e2bb`, no ar e verificado).** O `/extrair` ganhou o campo `pdfs`: cada página vira PNG no servidor via PyMuPDF e entra no MESMO caminho das imagens coladas (chunking, ordem newest-first e detecção de sobreposição reaproveitados). Front: PDF entra pelo seletor e drag-drop, vira card 📕, sobe no campo `pdfs`; `pdfFiles` incluído em estado/retry/limpar/snapshot. Limites: 25MB por PDF, 15 páginas, dentro do teto combinado de 15 imagens. `pymupdf>=1.24` no requirements. Vale pra qualquer casa, não só Bet365. Verificação em prod: o mesmo PDF do Gabriel pelo `/extrair` deu as 5 apostas idênticas à via imagem (só extração, sem `/salvar` → não duplicou as já salvas). `check-tokens` verde no pré-commit. **Nota UX:** PDF de impressão da página inteira da Bet365 traz páginas de cabeçalho/rodapé sem aposta (a IA ignora); imprimir só a área das apostas fica mais enxuto, mas do jeito que veio já rodou. **Pendente:** nada aberto desta frente. Auditoria turbo Onda 1 segue pendente (não toquei). **Não meu (intocado):** untracked `docs/PESQUISA_BADMINTON_2026.md` e `docs/DESAMBIGUACAO_RAQUETE_2026.md`, de outro contexto. Ver [[extracao_worldwide_fase012]] · [[bet365_dedup_e_vazamento_imagens]] · [[fatuch_cadastro]].)_

_Anterior: 2026-07-20 (sessão 169 — **Re-auditoria turbo profunda + Onda 0 de segurança (2 XSS).** Rodou em paralelo às sessões 165-168; git intercalou limpo, commitei só os meus paths. **Auditoria (read-only, 2 passadas):** rasa (27 agentes) e **profunda (219 agentes, arquivos inteiros, adversarial em cada achado, crítico de completude).** Chão medido: 178 testes verdes, check-tokens verde, audit_casas sem FAILs. Resultado: 95 achados confirmados, 17 altos, 0 crítico. Entregável `docs/AUDITORIA_TURBO_2026-07-20.md` + painel privado. **Altos em 3 temas:** event loop único frágil (bcrypt no login, gzip da base inteira, upload antes da auth, teto de captura); dinheiro silencioso em escala (chunker de modo cego corrompe stake/odd em casa nova; XLS múltiplo processa só o 1º arquivo; goldens de VitoriaBet/Betnacional ensinam separador `+`); segurança nova (XSS armazenado por nome de casa; offboarding não revoga sessão). **Corrigido e no ar (Onda 0):** C1 XSS armazenado via nome de casa (`eb8d0ac`: `encodeURIComponent` no `faviconUrl` + `esc()` nos `data-casa`/`alt` do `index.html`); C2 XSS refletido `/extensao?v=` (`8f342c1`: `esc()` no `innerHTML` do `extensao.html`). check-tokens verde; backups `Backups/xss-c1-casa-2026-07-20/` e `Backups/xss-c2-extensao-2026-07-20/`. **Decisões do Feca:** Fatuch `doGet` público é risco contido no Fatuch (Apps Script na conta dele, sem ligação com o Sharpen), adiado e fecha na expansão. C3 (offboarding não revoga sessão de 30 dias) não patchar o auth atual; virou requisito da Fase 1 do projeto SaaS (o token checa o status do usuário). **Pendente (próximo passo, ver o relatório):** Onda 1 tirar bloqueio do event loop (bcrypt para thread, limite de upload, teto de captura); Onda 2 dinheiro silencioso (chunker de modo cego, XLS múltiplo, goldens `+` para `//`); Onda 3 Monte Carlo assíncrono. Ver [[reaudit_turbo_2026-07-20]] · `docs/AUDITORIA_TURBO_2026-07-20.md`.)_

_Anterior: 2026-07-20 (sessão 168 — **Painel "Apostas em Aberto" da tela de início lia só o Postgres.** O Fatuch viu a contradição: o card **APOSTAS** da página Apostas mostrava `Abertas:2`, mas o painel "Apostas em Aberto" da tela de início dizia "Nenhuma aposta em aberto — tudo resolvido ✓". **Causa:** duas fontes diferentes. O card lê do feed `/dashboard/data`, que para a carteira do Fatuch é a **planilha AO VIVO** (Apps Script) e traz as abertas com `resultado='ABERTA'`. O painel do início (`inicio.html:308`) só consultava `/bilhetes?extraction_state=aberta` (Postgres) — vazio, porque a base do Fatuch não está no Postgres, é planilha-viva. Detalhe que fecha o raciocínio: `repository.dashboard_rows` (feed do Postgres) **exclui** abertas (`resultado not in {W,L,V,HW,HL}: continue`), enquanto a planilha viva **inclui**; por isso o `Abertas:N` só aparecia pra quem é planilha-viva. **Fix (`ce67012`):** o painel agora **une** as abertas do feed (`rows` com `resultado==='ABERTA'`, stake normalizada via `fmt(num(...),2)`) com as do Postgres. Cada dono é sempre planilha-viva **OU** Postgres (fontes disjuntas), então a união não duplica; donos Postgres (Feca, Jonathan, etc.) ficam **idênticos** ao de antes porque o feed deles não traz linhas ABERTA (`feedAbertas=[]`). Reusou os helpers existentes (`fmt`/`num`/`moneyStake`), sem formatador novo; gate `/nova-ui` ok, `check-tokens` verde. **Ressalva:** as abertas da planilha não carregam `criado_em`, então não entram no alerta "parada há 48h+" (a planilha não carimba horário de envio). Backup `Backups/s168-inicio-painel-abertas/` (STATUS) + `Backups/inicio-painel-abertas-planilha-viva/` (inicio.html). **Residual não meu (deixado intocado por decisão do Feca):** `app/static/extensao.html` (modificado) + untracked `docs/AUDITORIA_TURBO_2026-07-20.md` e `scratch_findings.txt` — pré-existentes, fora do meu commit. Ver [[fatuch_cadastro]] · [[betano_abertas_e_upsert]].)_

> **Histórico completo das sessões 167 → 14** → [`docs/HISTORICO.md`](docs/HISTORICO.md)

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
    CASA_VITORIABET.md
/golden_set/
    bilhetes/              (print + TSV esperado)
/docs/                   (referências, ADRs, planos, HISTORICO.md)
STATUS.md                  (este arquivo)
```

Os 6 MASTER_*.md vivem em `/global/`; as 15 casas em `/casas/` (Polymarket por API, as demais por IA/texto).

---

## 4. Estado atual

- **Produto no ar** em `sharpen.bet` (dashboard + extração); deploy automático via Railway.
- **Multi-tenant:** vários donos (Feca, Fatuch, Diogo, Jonathan, Lava…) + operadores; dados isolados por `dono` no Postgres (regras de tenancy/dedup no `CLAUDE.md`).
- **Base do Feca:** migração planilha → Postgres **completa e reconciliada**.
- **Casas:** 15 arquivos em `casas/` (extração por IA/texto) + **Polymarket** por API.
- **Fatuch:** dashboard lê a planilha viva do LavaFatuch via Apps Script (leitura por **cabeçalho**, não por posição); coluna `Espelho` = fornecedor. Sem base no Postgres (tudo vem da planilha).
- **Captura:** extensão **SharpenUp** (moldura+Snap e robô de rolagem) no ar, pareando por código.
- **Modelo de extração:** Sonnet 4.6 (`config.py`).

---

## 5. Pendências (aguardam bilhete real)

- **Bet365:** §6 rótulo visual do boost · §7 rótulo visual do cashout encerrado
- **Betano:** §5 rótulo de void/anulada · §6 boost (existe?)
- **Pinnacle:** §5 rótulo exato de HW/HL no export (precisa de Asian Handicap de quarto liquidado)
- **Bolsa de Aposta:** §5 V/HW/HL · §6 boost · §7 cashout · §8 bônus · apostas Lay
- **Betnacional:** §5 HW/HL · §5 V (rótulo visual de void) · §7 cashout · §8 bônus
- **Jogo de Ouro:** §5 V/HW/HL · §5 rótulo do card na aba Cashout · §7 cashout · §8 bônus

**Próximo passo:**
- Preencher pendências das casas existentes assim que amostras reais chegarem (ver lista acima).
- **Frente worldwide (nova, plano aprovado):** construir a Fase 1 do [`docs/PLANO_EXTRACAO_WORLDWIDE.md`](docs/PLANO_EXTRACAO_WORLDWIDE.md) (confidence da IA + guardrail de enum) quando o Feca quiser. Fase 0 já validada (zero-shot 94,5% de acerto de categoria). Meta: extração universal + cache aprendido → "+adicionar conta" em autosserviço.

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
