---
description: Checklist obrigatorio de marca ANTES de criar/alterar qualquer UI (numeros, dinheiro, cor, tipografia, componente)
argument-hint: "<o que vou construir> (ex: cards de KPI por conta)"
allowed-tools: Read, Grep, Edit, Bash(node scripts/tokens/check-tokens.mjs), Bash(git:*), Bash(grep:*)
---

# Nova UI: $ARGUMENTS

Executa a **REGRA DE UI / MARCA OBRIGATORIA** do `CLAUDE.md`. Existe porque regra
escrita sem habito de conferir e' pulada (sessao 83: cards de KPI com formatador
caseiro que abreviava e coloria errado). NAO comecar a construir antes de passar
por 1-3. Uma etapa por vez; parar e perguntar ao Feca em qualquer duvida de convencao.

## 1. LER as regras aplicaveis (antes de escrever qualquer linha)
- `docs/UI_REFERENCE.md` — **§5 = padrao monetario** (R$, P/L, cor, casas decimais).
- `docs/SHELL_SPEC.md` — se tocar na casca (pagehead / nav / sidebar / cards do shell).
- Biblia de marca: `../pack/CLAUDE.md`. Tokens: `../pack/tokens/tokens.css` (fonte de verdade de cor/tamanho).
- Escrever aqui, em 1 linha, **quais regras se aplicam** ao que vou construir.

## 2. REUSAR helper — nunca criar formatador
- `grep -nE "fmtPL|moneyStake|function fmt|\.money" app/static/index.html` (e no dashboard, os charts/*.js).
- Todo R$ usa o componente `.money`; muda so as casas por contexto (`UI_REFERENCE §5.1`):
  - **P/L** (tabela e KPI) -> `fmtPL` (2 casas, `R$` menor `--ink-soft`, cor SO no numero `.money-val`, sinal colado, minus U+2212, zero neutro).
  - **Agregado / KPI / turnover / custo** -> `fmtR` (**inteiro**).
  - **Stake / unitario** -> `moneyStake` / `.money` (2 casas).
- **Nunca** abreviar milhar (`k`/`M`) — barrado pelo `check-tokens §d`. **`.toFixed`/`.replace`** so nas excecoes (odd/USD, §5.3), nunca em R$.
- **Cor** sempre `var(--…)`, nunca literal. **%** com `fmtPct`; **odd** com `fmtOdd`.
- Regra de decisao: e' P/L -> `fmtPL`; e' agregado/total -> `fmtR`. Contexto novo que nao se encaixe: **perguntar ao Feca**, nao inventar uma terceira mascara.

## 3. CONSTRUIR
- Backup em `Backups/<nome-descritivo>/` antes de editar (invariante 4).
- Arquivo completo, uma mudanca por vez (invariantes 5-6).

## 4. AUTO-AUDITAR antes do commit (obrigatorio)
- Conferir item a item contra `UI_REFERENCE §5`: 2 casas? `R$` menor/neutro? cor so no numero? minus U+2212? zero neutro? sem abreviar? sem `.toFixed`/`.replace`? label PT-BR?
- **Escada de Tinta** (`CLAUDE.md`): nenhum `--ink-mute` abaixo de 10px; nenhum nome
  proprio (casa/tipster/operador/e-mail) em `--ink-mute`; contraste medido sobre o
  **fundo efetivo** (somando overlays `rgba(255,255,255,…)`), nao sobre o token de
  superficie. **Varredura em TRES criterios** — o grep de px literal sozinho da falso verde:
  - `... | grep -E "font-size: ?(8|8\.5|9|9\.5)px"` — tamanho literal abaixo do piso
  - `... | grep "text-nano"` — tamanho vindo de TOKEN (`--text-nano` = 9px)
  - `grep -rn "ink-mute\|ink-soft" ... | grep -E "opacity: ?\.[0-9]"` — opacidade sobre tom apagado
  Excecoes ja documentadas (nao contam): caret/seta/`.metric-info` (icone) e
  `.act-btn.off`/`*.is-loading` (opacidade como ESTADO).
- `node scripts/tokens/check-tokens.mjs` -> tem que sair **verde** (drift + paleta + shell + monetario).
- Validar o JS: extrair o script inline e `new vm.Script(...)` (0 erro).
- Se possivel, **render headless** (Chrome `--headless=new --screenshot`) e conferir visualmente.

## 5. STATUS + commit + push (invariantes 7-8)
- Atualizar `STATUS.md`. `git add` -> `git commit` -> `git push` (deploy Railway).

> Se qualquer passo revelar que a regra da marca esta ambigua ou o proprio codigo canonico a viola (ex: `.toFixed` em `fmtUSD`), **registrar e avisar o Feca** — nao replicar a violacao "porque ja existe".
