# PLANO — Casca unificada Planilhador ↔ Dashboard

> Objetivo do Feca (sessão 86): que o Planilhador e o Dashboard **pareçam um app só** —
> hoje, ao clicar entre eles na sidebar, "parece que muda de página por completo e que os
> sidebars são diferentes". Integração completa, feita **em fatias** (cada uma testável,
> reversível e no ar sozinha), não num merge big-bang.
>
> Fonte de verdade da casca: [`SHELL_SPEC.md`](SHELL_SPEC.md). Etapa A da governança de UI.

---

## Estado atual (o que já existe)

- **Dois front-ends, arquiteturas diferentes:**
  - Planilhador = `app/static/index.html` (HTML monolítico ~230KB, CSS+JS inline). Rota `GET /`.
  - Dashboard = `app/static/dash/` (SPA montada em JS por `assets/js/app.js` em `#root`). Montado como `StaticFiles("/dashboard", html=True)`.
- **Navegação entre eles = recarga de página inteira** (`<a href="/dashboard/#...">` e `<a href="/">`).
- **Já compartilhado:** `app/static/shell.css` (itens de nav: `.nav-group`/`.nav-item`/`.nav-icon`).
- **✅ Fatia 1 (feita, sessão 86 — commit `aeea5e7`):** a *geometria* do sidebar do Planilhador
  foi alinhada à do Dashboard (padding do contêiner, moldura da logo, insets da nav, rodapé,
  `.last-update`). Os dois sidebars agora são visualmente idênticos → o "pulo" na recarga
  praticamente sumiu. **Mas ainda há recarga** (o `<main>` inteiro repinta).

---

## O que falta para "um app só" de verdade

O que ainda entrega a sensação de "trocou de app" é a **recarga da página inteira**: mesmo com
o sidebar idêntico, há um flash branco/repintura e o estado se perde (ex.: uma extração em
andamento no Planilhador some ao ir no Dashboard e voltar). Matar isso = Fatias 2 e 3.

---

## Fatia 2 — Shell hospedeiro (a sidebar deixa de recarregar)

**Meta:** um contêiner único dono da sidebar; só a área de conteúdo troca. Sem flash, sem
"pulo", sidebar sempre viva.

### Estratégia recomendada: **host com `<iframe>`** (baixo risco, isola os dois apps)

Uma página-casca nova (ex.: rota `GET /app`) que contém **só a sidebar compartilhada** + uma
área de conteúdo com **dois iframes**: um carrega `/` (Planilhador), outro `/dashboard/`. Clicar
na sidebar **mostra/esconde** o iframe certo (e ajusta o hash do Dashboard), sem recarregar a
casca.

**Por que iframe e não merge direto:**
- **Isola JS e CSS** dos dois apps → zero colisão de nomes globais (`showPage`/`mostrarView`,
  auto-init, `fetch` no load) e zero vazamento de CSS (`.card`, `.sidebar` etc. têm valores
  diferentes nos dois). Essas colisões são exatamente o que torna o merge direto arriscado.
- **Preserva estado de graça:** mantendo os dois iframes montados e só alternando visibilidade,
  a extração em andamento do Planilhador **sobrevive** a ir no Dashboard e voltar. (Resolve o
  objetivo "preservar estado" da Fatia 3 quase sem custo extra.)
- **Reversível:** se não gostarmos, apaga-se a rota `/app` e volta tudo ao que é hoje.

**Passos:**
1. Criar `app/static/app.html` (a casca): sidebar compartilhada (extraída do markup já idêntico)
   + `<main>` com `<iframe id="fr-plan" src="/">` e `<iframe id="fr-dash" src="/dashboard/">`.
2. A sidebar da casca controla a troca: clicar em "Planilhador"/grupos → mostra o iframe certo,
   marca o `.nav-item.active`, e no caso do Dashboard seta `fr-dash.contentWindow.location.hash`.
3. **Esconder as sidebars internas** dos dois apps quando rodando dentro do host (detecção via
   `window.top !== window.self` → classe `body.embedded` que dá `display:none` no `.sidebar`
   interno e remove a margem/again do conteúdo). Assim não há sidebar dupla.
4. Rota `GET /app` no `main.py` servindo `app.html` (atrás do login, igual `/`). Definir se `/app`
   vira a home (redirecionar `/` autenticado → `/app`) ou se convive.
5. Sincronizar URL ↔ estado (deep-link): `/app#dash/tipsters` abre o Dashboard em Tipsters;
   `/app#plan` abre o Planilhador. Back/forward do navegador funcionam via `hashchange`.

**Riscos e mitigação:**
- *Duas barras de rolagem / altura do iframe* → iframe `width/height:100%`, `border:0`, o scroll
  vive dentro de cada app (já é assim). Testar em tela cheia e reduzida.
- *Login/redirect dentro do iframe* → os dois apps já exigem auth pelo mesmo cookie; um 302 para
  `/login` dentro do iframe precisa ser tratado (detectar e subir para o topo). Testar sessão
  expirada.
- *Downloads (`/exportar.csv`)* e Ctrl+V de print → confirmar que funcionam dentro do iframe
  (o paste é capturado no documento do iframe, deve seguir OK; validar).
- *Performance* → dois iframes carregam duas páginas; o Dashboard puxa base pesada. Mitigar com
  **lazy**: só criar o `src` do `fr-dash` no primeiro clique em Análise (não no load do host).

### Alternativa (não recomendada agora): merge direto num SPA só
Fundir os dois num único documento com roteador client-side. UX teoricamente melhor (sem
iframe), mas exige **modularizar o monolito de 230KB**, resolver colisões de JS/CSS e refazer o
boot dos dois. Multi-sessão, alto risco de regressão num produto no ar. Fica como Fatia 4
opcional **se** o host com iframe não bastar.

**Entregável da Fatia 2:** navegar entre Planilhador e Dashboard sem flash e sem perder estado,
com a sidebar única sempre viva. Já resolve ~100% da queixa do Feca.

---

## Fatia 3 — Polimento da casca única

Depois que o host existe, refinos que só fazem sentido com ele no ar:
1. **Topbar/pagehead compartilhada** no host (hoje cada app tem a sua) — opcional, se quisermos
   o título fora do iframe.
2. **Deep-link completo + histórico** afinado (back/forward, refresh mantém a página certa).
3. **Estado preservado explícito** — garantir que trocar de app nunca dispara re-fetch
   desnecessário (o iframe já ajuda; medir e travar).
4. **Transições** suaves entre conteúdos (fade curto) para reforçar "é o mesmo app".
5. Aposentar os `<a href>` cross-app antigos (viram navegação do host) e podar CSS morto de
   sidebar duplicada.

---

## Validação (toda fatia)
- `node scripts/tokens/check-tokens.mjs` verde (drift · cor · shell · monetário).
- `python -m py_compile` se tocar `main.py`; app importa e rotas registram.
- **Render headless (Chrome)** dos fluxos: abrir `/app`, alternar Plan↔Dash, deep-link, sessão
  expirada, download CSV, Ctrl+V. Backup do arquivo tocado em `Backups/<descritivo>_<data>/`.
- Commit + push (deploy Railway). Uma fatia por commit; validar no deploy antes da próxima.

## Ordem sugerida
**Fatia 2 primeiro** (entrega o essencial). Reavaliar com o Feca **depois de validar no deploy**
se a Fatia 3 (polimento) e/ou o merge purista (Fatia 4) valem o custo — ou se o host com iframe
já deixou "um app só" como ele quer.

---
CRIADO: 2026-07-02 (sessão 86)
