// SharpenUp — content script (todas as casas). Dois modos, conforme o pareamento:
//   • modo PRINT (Superbet & cia): FAB → desenha a região 1x → moldura FIXA com
//     botão Snap; cada Snap tira o print da região e envia. Interior clicável.
//   • modo TEXTO (Betano): FAB (ou popup) → ROBÔ rola a página do topo ao fim,
//     colhe o texto dos bilhetes a cada passo e deduplica (a lista é virtualizada,
//     re-renderiza os mesmos ao rolar) → manda tudo como texto pro dashboard.
// Estado do pareamento em chrome.storage; a moldura persiste (sobrevive à navegação).
// Estilos via setProperty('...','important') pra não apanhar do CSS da casa.
(() => {
  if (window.__sharpenupCS) return;
  window.__sharpenupCS = true;

  const AZUL = "#2E8BFF", VERDE = "#2BC07E", Z = "2147483646";
  let fab = null, fabModo = "print", frame = null, box = null, toolbar = null, handle = null,
      drawRoot = null, capturando = false, safety = null, rectAtual = null, roboRodando = false;

  const S = (el, m) => { for (const k in m) el.style.setProperty(k, m[k], "important"); };
  const get = () => chrome.storage.local.get(["token", "modo", "frameAtivo", "frameRect", "frameCount"]);
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  // Tickets da Superbet capturados pelo sb_inject.js (mundo MAIN) — as RESPOSTAS
  // JSON que a própria página recebe da API. O robô só rola a lista p/ a página
  // paginar; a extensão lê o dado exato do site, sem clicar e sem requisição nova.
  // Duas abas: Liquidada (`status=finished`) e Em aberto (`status=active` → `__aberta:true`,
  // sem resultado). `sbById` guarda 1 ticket por ticketId — a versão LIQUIDADA vence a
  // ABERTA (quando o bilhete fecha na mesma sessão, a verdade da liquidação substitui).
  const sbById = new Map();          // ticketId → ticket (liquidada > aberta)
  let sbHookVivo = false, sbRespostas = 0;   // autodiagnóstico (espelha o da Betfair)
  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (d && d.__sharpenupSBData) {
      if (d.hook) sbHookVivo = true;
      if (typeof d.respostas === "number") sbRespostas = d.respostas;
      if (Array.isArray(d.tickets)) {
        for (const t of d.tickets) {
          const c = t && t.ticketId;
          if (!c) continue;
          const ex = sbById.get(c);
          if (!ex || (ex.__aberta && !t.__aberta)) sbById.set(c, t);   // liquidada vence aberta
        }
      }
    }
  });

  // Itens da BETesporte capturados pelo be_inject.js (mundo MAIN) — as RESPOSTAS JSON de
  // POST /api/bet/RequestUserTickets. Mesmo modelo passivo da Superbet: o robô só rola a
  // lista p/ a página buscar mais; a extensão lê o dado exato do site (id, odd, value,
  // status, date), sem clicar em "Ver Cupom".
  const beTickets = [];
  const beTicketSeen = new Set();
  let beHookVivo = false, beRespostas = 0;   // autodiagnóstico (espelha o da Betfair)
  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (d && d.__sharpenupBEData) {
      if (d.hook) beHookVivo = true;
      if (typeof d.respostas === "number") beRespostas = d.respostas;
      if (Array.isArray(d.items)) {
        for (const t of d.items) {
          const c = t && t.id;
          if (c != null && !beTicketSeen.has(c)) { beTicketSeen.add(c); beTickets.push(t); }
        }
      }
    }
  });

  // Bilhetes da Betano capturados pelo bn_inject.js (mundo MAIN) — as RESPOSTAS JSON de
  // GET /api/ma/bet/bet-history-v3?settled=true|false&page=N. Mesmo modelo passivo: o robô
  // só rola a lista p/ a página paginar (levas de 10, cursor lastId); a extensão lê o dado
  // exato (BetId, Stake, DecimalOdds, Status, PlacedAt, Legs/Selections), sem OCR.
  // Duas abas: Liquidada (resolvidas) e Em aberto (`__aberta:true`, sem resultado).
  // `bnById` guarda 1 bilhete por BetId — a versão LIQUIDADA vence a ABERTA (quando o
  // bilhete fecha na mesma sessão, a verdade da liquidação substitui a aberta). Fim
  // autoritativo é POR LISTA (`bnFimOpen`/`bnFimSettled`): a aba ativa decide qual usar.
  const bnById = new Map();          // BetId(string) → ticket (liquidada > aberta)
  let bnFimOpen = false, bnFimSettled = false;
  let bnHookVivo = false, bnRespostas = 0;   // autodiagnóstico (espelha o da Betfair)
  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (d && d.__sharpenupBNData) {
      if (d.hook) bnHookVivo = true;
      if (typeof d.respostas === "number") bnRespostas = d.respostas;
      if (Array.isArray(d.bets)) {
        for (const t of d.bets) {
          const c = t && t.BetId;
          if (c == null) continue;
          const key = String(c);
          const ex = bnById.get(key);
          // Entra se ainda não há nada; ou se o novo é LIQUIDADO e o guardado era ABERTO.
          if (!ex || (ex.__aberta && !t.__aberta)) bnById.set(key, t);
        }
      }
      if (d.fimOpen) bnFimOpen = true;
      if (d.fimSettled) bnFimSettled = true;
    }
  });

  // Bilhetes da BETFAIR capturados pelo bf_inject.js (mundo MAIN) — as RESPOSTAS JSON de
  // POST /activity/sportsbook. Mesmo modelo passivo: o robô só rola a lista p/ a página
  // paginar (levas de 10, cursor nextPageIndex); a extensão lê o dado exato (betId O/…,
  // settledDate, status WON/LOST/VOID, stake, odd, seleções), sem OCR nem extrato CSV.
  // `bfFimReal` = a página trouxe `moreAvailable:false` → fim autoritativo.
  const bfTickets = [];
  const bfTicketSeen = new Set();
  let bfFimReal = false;
  let bfHookVivo = false;   // o bf_inject respondeu → hook ativo na página (autodiagnóstico)
  let bfRespostas = 0;      // respostas de /activity/sportsbook que o hook viu
  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (d && d.__sharpenupBFData) {
      if (d.hook) bfHookVivo = true;
      if (typeof d.respostas === "number") bfRespostas = d.respostas;
      if (Array.isArray(d.bets)) {
        for (const t of d.bets) {
          const c = t && t.betId;
          if (c && !bfTicketSeen.has(c)) { bfTicketSeen.add(c); bfTickets.push(t); }
        }
      }
      if (d.fim) bfFimReal = true;
    }
  });

  // Bilhetes da PINNACLE capturados pelo pn_inject.js (mundo MAIN) — as RESPOSTAS JSON de
  // POST /member-service/v2/wager-filter, já convertidas de array posicional p/ objeto
  // nomeado pelo inject. Mesmo modelo passivo + REPLAY ATIVO: o inject re-emite a busca das
  // duas abas (Decidido/Não decidido) e devolve tudo. `pnById` guarda 1 bilhete por id — a
  // versão SETTLED (resolvida) vence a ABERTA quando o bilhete fecha na mesma sessão.
  // `pnFimReal` = o inject terminou de re-emitir as duas abas → fim autoritativo.
  const pnById = new Map();          // id(string) → bilhete (resolvida > aberta)
  let pnFimReal = false;
  let pnHookVivo = false, pnRespostas = 0;   // autodiagnóstico (espelha o da Betfair)
  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (d && d.__sharpenupPNData) {
      if (d.hook) pnHookVivo = true;
      if (typeof d.respostas === "number") pnRespostas = d.respostas;
      if (Array.isArray(d.bets)) {
        for (const t of d.bets) {
          const c = t && t.id;
          if (c == null) continue;
          const key = String(c);
          const ex = pnById.get(key);
          // Entra se ainda não há nada; ou se o novo é RESOLVIDO e o guardado era ABERTO.
          if (!ex || (ex.aberta && !t.aberta)) pnById.set(key, t);
        }
      }
      if (d.fim) pnFimReal = true;
    }
  });

  // Bilhetes da BET365 capturados pelo b3_inject.js (mundo MAIN) — as RESPOSTAS de
  // /sportshistoryapi/summary + /confirmation (formato F|…), já parseadas pelo inject. Mesmo
  // modelo passivo + REPLAY ATIVO: o inject varre as duas listas (settled=1 resolvidas · settled=0
  // abertas) e busca o DETALHE de cada bilhete (jogo/mercado + código estável BR). `b3ById` guarda
  // 1 bilhete por bsid (chave da visão); o dedup final no backend é pelo código BR no texto.
  // `b3FimReal` = o inject terminou de varrer as listas e os detalhes → fim autoritativo.
  const b3ById = new Map();          // bsid(string) → bilhete mesclado (summary + confirmation)
  let b3FimReal = false;
  let b3HookVivo = false;
  // Um inject POR FRAME responde (a área de membros da Bet365 é outra origem, em iframe).
  // Guardar por `href` em vez de uma variável única: com 2 frames, o último a falar
  // sobrescreveria o contador do outro — o top diria 0 e apagaria as respostas do iframe.
  const b3PorFrame = new Map();      // href → { respostas, history, topo }
  const b3Soma = (campo) => { let n = 0; for (const f of b3PorFrame.values()) n += (f[campo] || 0); return n; };
  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (d && d.__sharpenupB3Data) {
      if (d.hook) b3HookVivo = true;
      b3PorFrame.set(String(d.href || "?"), {
        respostas: typeof d.respostas === "number" ? d.respostas : 0,
        history: typeof d.history === "number" ? d.history : 0,
        topo: !!d.topo,
      });
      if (Array.isArray(d.bets)) {
        for (const t of d.bets) { if (t && t.bsid) b3ById.set(String(t.bsid), t); }
      }
      if (d.fim) b3FimReal = true;
    }
  });
  // Pede o acumulado + arranca o replay. Posta na própria window E em cada frame filho —
  // quem enxerga as chamadas da API é o inject dentro do iframe de `members.bet365.bet.br`,
  // e o postMessage do content só alcança a própria window. Cada inject repassa adiante.
  function b3Pedir(dias) {
    const msg = { __sharpenupB3Req: true, dias: dias, saltos: 0 };
    try { window.postMessage(msg, "*"); } catch (e) {}
    for (let i = 0; i < window.frames.length && i < 24; i++) {
      try { window.frames[i].postMessage(msg, "*"); } catch (e) {}
    }
  }

  function bladeSVG(w, h) {
    return '<svg viewBox="40 10 40 100" width="' + w + '" height="' + h + '" style="pointer-events:none">' +
      '<defs><linearGradient id="sharpenupBladeGrad" x1="60" y1="16" x2="60" y2="104" gradientUnits="userSpaceOnUse">' +
      '<stop offset="0" stop-color="#5BA9FF"></stop><stop offset="1" stop-color="#1E7CF0"></stop></linearGradient></defs>' +
      '<path d="M60 16 L60 90 L42 104 Z" fill="url(#sharpenupBladeGrad)"></path>' +
      '<path d="M60 16 L78 104 L60 90 Z" fill="#333B45"></path></svg>';
  }

  // ── FAB ─────────────────────────────────────────────────────────────────────
  function ensureFab(modo) {
    fabModo = modo;
    if (fab) { fab.title = modo === "texto" ? "SharpenUp — copiar bilhetes (robô)" : "SharpenUp — capturar"; return; }
    fab = document.createElement("div");
    fab.title = modo === "texto" ? "SharpenUp — copiar bilhetes (robô)" : "SharpenUp — capturar";
    S(fab, {
      position: "fixed", right: "22px", bottom: "22px", width: "52px", height: "52px",
      "border-radius": "50%", background: "linear-gradient(160deg,#161C24,#0B0E13)",
      border: "1px solid rgba(255,255,255,0.10)", display: "grid", "place-items": "center",
      cursor: "grab", "box-shadow": "0 8px 22px rgba(0,0,0,.5)", "z-index": Z,
      opacity: "0.62", transition: "opacity .18s, transform .18s, box-shadow .18s, border-color .18s",
      "touch-action": "none", "user-select": "none",
    });
    fab.innerHTML = bladeSVG(13, 29) +
      '<span style="position:absolute;right:-4px;top:-4px;width:16px;height:16px;border-radius:50%;' +
      'background:' + AZUL + ';border:2px solid #0B0E13;box-shadow:0 0 8px rgba(46,139,255,.7);' +
      'display:grid;place-items:center;pointer-events:none">' +
      '<svg viewBox="0 0 24 24" width="9" height="9" fill="none" stroke="#04101F" stroke-width="3.4" ' +
      'stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5M6 11l6-6 6 6"></path></svg></span>';

    let arr = false, mv = false, sx = 0, sy = 0, ox = 0, oy = 0;
    fab.addEventListener("pointerenter", () => { if (!arr) fabHover(true); });
    fab.addEventListener("pointerleave", () => { if (!arr) fabHover(false); });
    fab.addEventListener("pointerdown", (e) => {
      arr = true; mv = false; S(fab, { cursor: "grabbing" });
      const r = fab.getBoundingClientRect(); ox = r.left; oy = r.top; sx = e.clientX; sy = e.clientY;
      try { fab.setPointerCapture(e.pointerId); } catch (_) {}
    });
    fab.addEventListener("pointermove", (e) => {
      if (!arr) return;
      const dx = e.clientX - sx, dy = e.clientY - sy;
      if (Math.abs(dx) > 2 || Math.abs(dy) > 2) mv = true;
      const w = fab.offsetWidth, h = fab.offsetHeight;
      const x = Math.max(6, Math.min(ox + dx, innerWidth - w - 6));
      const y = Math.max(6, Math.min(oy + dy, innerHeight - h - 6));
      S(fab, { left: x + "px", top: y + "px", right: "auto", bottom: "auto" });
    });
    fab.addEventListener("pointerup", () => {
      if (!arr) return; arr = false; S(fab, { cursor: "grab" });
      if (mv) return;
      if (fabModo === "texto") iniciarRobo();
      else chrome.storage.local.set({ frameAtivo: true, frameCount: 0 });
    });
    document.documentElement.appendChild(fab);
  }
  function fabHover(on) {
    if (!fab) return;
    S(fab, {
      opacity: on ? "1" : "0.62", transform: on ? "scale(1.08)" : "none",
      "border-color": on ? "rgba(46,139,255,0.55)" : "rgba(255,255,255,0.10)",
      "box-shadow": on ? "0 10px 30px rgba(0,0,0,.55),0 0 0 4px rgba(46,139,255,.14)" : "0 8px 22px rgba(0,0,0,.5)",
    });
  }
  function removeFab() { if (fab) { fab.remove(); fab = null; } }

  // ── Desenho da região (1ª vez, modo print) ──────────────────────────────────
  function ensureDraw() {
    if (drawRoot) return;
    let dsx = 0, dsy = 0, drawing = false;
    drawRoot = document.createElement("div");
    S(drawRoot, { position: "fixed", inset: "0", "z-index": Z, cursor: "crosshair",
      background: "rgba(10,15,25,0.28)", "user-select": "none" });
    const db = document.createElement("div");
    S(db, { position: "fixed", border: "2px solid " + AZUL, "border-radius": "3px",
      "box-shadow": "0 0 0 9999px rgba(10,15,25,0.45)", display: "none", "pointer-events": "none" });
    drawRoot.appendChild(db);
    const dica = document.createElement("div");
    dica.textContent = "Arraste para enquadrar o bilhete · Esc cancela";
    S(dica, { position: "fixed", top: "16px", left: "50%", transform: "translateX(-50%)",
      background: "#0E1524", color: "#E6ECF5", font: "13px/1.4 system-ui,sans-serif",
      padding: "8px 14px", "border-radius": "8px", border: "1px solid rgba(46,139,255,0.55)",
      "pointer-events": "none", "z-index": Z });
    drawRoot.appendChild(dica);

    const pos = (x, y, w, h) => S(db, { left: x + "px", top: y + "px", width: w + "px", height: h + "px" });
    drawRoot.addEventListener("pointerdown", (e) => {
      if (e.button !== 0) return; drawing = true; dsx = e.clientX; dsy = e.clientY;
      pos(dsx, dsy, 0, 0); S(db, { display: "block" }); e.preventDefault();
    });
    drawRoot.addEventListener("pointermove", (e) => {
      if (!drawing) return;
      pos(Math.min(dsx, e.clientX), Math.min(dsy, e.clientY), Math.abs(e.clientX - dsx), Math.abs(e.clientY - dsy));
    });
    drawRoot.addEventListener("pointerup", () => {
      if (!drawing) return; drawing = false;
      const r = db.getBoundingClientRect();
      if (r.width < 12 || r.height < 12) { S(db, { display: "none" }); return; }
      chrome.storage.local.set({ frameRect: { left: r.left, top: r.top, width: r.width, height: r.height } });
    });
    const onKey = (e) => { if (e.key === "Escape") chrome.storage.local.set({ frameAtivo: false }); };
    document.addEventListener("keydown", onKey, true);
    drawRoot._cleanup = () => document.removeEventListener("keydown", onKey, true);
    document.documentElement.appendChild(drawRoot);
  }
  function removeDraw() { if (drawRoot) { if (drawRoot._cleanup) drawRoot._cleanup(); drawRoot.remove(); drawRoot = null; } }

  // ── Moldura fixa (modo print) ────────────────────────────────────────────────
  function ensureFrame(rect, count) {
    rectAtual = { left: rect.left, top: rect.top, width: rect.width, height: rect.height };
    if (frame) { atualizarContador(count); reposicionar(); return; }

    frame = document.createElement("div");
    S(frame, { position: "fixed", inset: "0", "pointer-events": "none", "z-index": Z });
    box = document.createElement("div");
    S(box, { position: "fixed", border: "2px solid " + AZUL, "border-radius": "3px",
      "box-shadow": "0 0 0 1px rgba(0,0,0,.35)", "pointer-events": "none",
      transition: "border-color .15s", "box-sizing": "border-box" });
    frame.appendChild(box);

    toolbar = document.createElement("div");
    S(toolbar, { position: "fixed", display: "inline-flex", "align-items": "center", gap: "4px",
      background: "#0E1524", border: "1px solid rgba(46,139,255,0.5)", "border-radius": "10px",
      padding: "4px 4px 4px 8px", "box-shadow": "0 8px 22px rgba(0,0,0,.5)", "pointer-events": "auto",
      cursor: "grab", "z-index": Z, font: "12px/1 system-ui,sans-serif", color: "#E6ECF5",
      "user-select": "none", "white-space": "nowrap" });
    const snap = botao(
      '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#04101F" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path><circle cx="12" cy="13" r="4"></circle></svg><b style="margin-left:5px">Snap</b>',
      { background: AZUL, color: "#04101F", padding: "7px 12px", "font-weight": "700" });
    const cnt = document.createElement("span");
    cnt.id = "su-cnt";
    S(cnt, { "font-family": "ui-monospace,monospace", "font-size": "11px", color: "#7FB2FF", padding: "0 6px" });
    const redraw = botao(
      '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 3-6.7L3 8"></path><path d="M3 3v5h5"></path></svg>',
      { background: "transparent", color: "#9AA6B6", padding: "7px 8px" }, "Redesenhar");
    const fechar = botao(
      '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6L6 18M6 6l12 12"></path></svg>',
      { background: "transparent", color: "#9AA6B6", padding: "7px 8px" }, "Fechar");
    toolbar.appendChild(snap); toolbar.appendChild(cnt); toolbar.appendChild(redraw); toolbar.appendChild(fechar);
    frame.appendChild(toolbar);

    handle = document.createElement("div");
    S(handle, { position: "fixed", width: "16px", height: "16px", background: AZUL,
      border: "2px solid #0B0E13", "border-radius": "4px", "pointer-events": "auto",
      cursor: "nwse-resize", "z-index": Z });
    frame.appendChild(handle);

    snap.addEventListener("click", dispararSnap);
    redraw.addEventListener("click", () => chrome.storage.local.remove("frameRect"));
    fechar.addEventListener("click", () => chrome.storage.local.set({ frameAtivo: false }));
    [snap, redraw, fechar].forEach((b) => b.addEventListener("pointerdown", (e) => e.stopPropagation()));

    arrastarBarra(); redimensionar();
    document.documentElement.appendChild(frame);
    atualizarContador(count); reposicionar();
  }

  function botao(html, estilos, titulo) {
    const b = document.createElement("button");
    b.innerHTML = html; if (titulo) b.title = titulo;
    S(b, Object.assign({ border: "none", "border-radius": "7px", cursor: "pointer",
      display: "inline-flex", "align-items": "center", "font-family": "inherit", "font-size": "12px" }, estilos));
    return b;
  }
  function reposicionar() {
    if (!box) return;
    const r = rectAtual;
    S(box, { left: r.left + "px", top: r.top + "px", width: r.width + "px", height: r.height + "px" });
    let ty = r.top - 44; if (ty < 6) ty = r.top + 6;
    S(toolbar, { left: Math.max(6, r.left) + "px", top: ty + "px" });
    S(handle, { left: (r.left + r.width - 8) + "px", top: (r.top + r.height - 8) + "px" });
  }
  function atualizarContador(count) {
    const el = document.getElementById("su-cnt");
    if (el) el.textContent = (count || 0) + " enviado" + ((count || 0) === 1 ? "" : "s");
  }
  function arrastarBarra() {
    let a = false, sx = 0, sy = 0, ol = 0, ot = 0;
    toolbar.addEventListener("pointerdown", (e) => {
      if (e.target.closest("button")) return;
      a = true; sx = e.clientX; sy = e.clientY; ol = rectAtual.left; ot = rectAtual.top;
      S(toolbar, { cursor: "grabbing" }); try { toolbar.setPointerCapture(e.pointerId); } catch (_) {} e.preventDefault();
    });
    toolbar.addEventListener("pointermove", (e) => {
      if (!a) return;
      rectAtual.left = Math.max(0, Math.min(ol + (e.clientX - sx), innerWidth - rectAtual.width));
      rectAtual.top = Math.max(0, Math.min(ot + (e.clientY - sy), innerHeight - rectAtual.height));
      reposicionar();
    });
    toolbar.addEventListener("pointerup", () => { if (!a) return; a = false; S(toolbar, { cursor: "grab" }); salvarRect(); });
  }
  function redimensionar() {
    let a = false;
    handle.addEventListener("pointerdown", (e) => { a = true; try { handle.setPointerCapture(e.pointerId); } catch (_) {} e.preventDefault(); e.stopPropagation(); });
    handle.addEventListener("pointermove", (e) => {
      if (!a) return;
      rectAtual.width = Math.max(40, Math.min(e.clientX - rectAtual.left, innerWidth - rectAtual.left));
      rectAtual.height = Math.max(40, Math.min(e.clientY - rectAtual.top, innerHeight - rectAtual.top));
      reposicionar();
    });
    handle.addEventListener("pointerup", () => { if (!a) return; a = false; salvarRect(); });
  }
  function salvarRect() {
    chrome.storage.local.set({ frameRect: { left: rectAtual.left, top: rectAtual.top, width: rectAtual.width, height: rectAtual.height } });
  }
  function dispararSnap() {
    if (capturando || !rectAtual) return;
    capturando = true;
    S(frame, { visibility: "hidden" });
    requestAnimationFrame(() => requestAnimationFrame(() => {
      chrome.runtime.sendMessage({ type: "CAPTURAR_REGIAO",
        rect: { x: rectAtual.left, y: rectAtual.top, width: rectAtual.width, height: rectAtual.height },
        vw: innerWidth, vh: innerHeight });
    }));
    clearTimeout(safety);
    safety = setTimeout(() => fimCaptura(false), 6000);
  }
  function fimCaptura(ok) {
    clearTimeout(safety); capturando = false;
    if (frame) S(frame, { visibility: "visible" });
    if (ok) {
      chrome.storage.local.get("frameCount").then(({ frameCount }) => chrome.storage.local.set({ frameCount: (frameCount || 0) + 1 }));
      if (box) { S(box, { "border-color": VERDE }); setTimeout(() => box && S(box, { "border-color": AZUL }), 350); }
    }
  }
  function removeFrame() {
    if (frame) { frame.remove(); frame = box = toolbar = handle = null; }
    capturando = false; clearTimeout(safety);
  }

  // ── Robô de texto (modo Betano) ──────────────────────────────────────────────
  const esDoc = (el) => el === document.scrollingElement || el === document.documentElement || el === document.body;
  const sTop = (el) => esDoc(el) ? (window.scrollY || document.documentElement.scrollTop) : el.scrollTop;
  const sMax = (el) => esDoc(el) ? (document.documentElement.scrollHeight - innerHeight) : (el.scrollHeight - el.clientHeight);
  const sClient = (el) => esDoc(el) ? innerHeight : el.clientHeight;
  const sTo = (el, y) => { if (esDoc(el)) scrollTo(0, y); else el.scrollTop = y; };

  function acharScroll() {
    let best = document.scrollingElement || document.documentElement;
    let score = best.scrollHeight - best.clientHeight;
    document.querySelectorAll("*").forEach((el) => {
      const ov = getComputedStyle(el).overflowY;
      if (ov !== "auto" && ov !== "scroll") return;
      const diff = el.scrollHeight - el.clientHeight;
      if (diff > score && el.clientHeight > 200) { best = el; score = diff; }
    });
    return best;
  }
  // Acha o maior grupo de elementos "irmãos parecidos" com texto médio = os cartões.
  function acharCards(root) {
    const scope = esDoc(root) ? document.body : root;
    const grupos = new Map();
    scope.querySelectorAll("*").forEach((el) => {
      const t = (el.innerText || "").trim();
      if (t.length < 40 || t.length > 3000) return;
      const cls = (typeof el.className === "string" ? el.className.trim().split(/\s+/)[0] : "") || "";
      const sig = el.tagName + "." + cls;
      if (!grupos.has(sig)) grupos.set(sig, []);
      grupos.get(sig).push(el);
    });
    let best = null, n = 0;
    grupos.forEach((arr) => { if (arr.length >= 3 && arr.length > n) { best = arr; n = arr.length; } });
    return best;
  }

  // Datas em pt-BR: "28/06/2026", "28/06/26", "28 de jun. de 2026", "28 de junho de 2026".
  const _MESES = { jan: 0, fev: 1, mar: 2, abr: 3, mai: 4, jun: 5, jul: 6, ago: 7, set: 8, out: 9, nov: 10, dez: 11 };
  function parseDatas(txt) {
    const out = [];
    let m;
    const re1 = /(\d{1,2})\/(\d{1,2})\/(\d{2,4})/g;
    while ((m = re1.exec(txt))) {
      let y = +m[3]; if (y < 100) y += 2000;
      const ts = Date.UTC(y, +m[2] - 1, +m[1]);
      if (!isNaN(ts)) out.push(ts);
    }
    const re2 = /(\d{1,2})\s+de\s+([a-zç]{3,})\.?\s+de\s+(\d{4})/g;
    while ((m = re2.exec(txt))) {
      const mes = _MESES[m[2].slice(0, 3)];
      if (mes !== undefined) out.push(Date.UTC(+m[3], mes, +m[1]));
    }
    return out;
  }

  async function iniciarRobo() {
    if (roboRodando) return;
    roboRodando = true;
    const painel = criarPainelRobo();
    let parar = false;
    painel.btnParar.onclick = () => { parar = true; };

    // Parada do robô: janela de N dias (look-back) OU até o ID do último bilhete
    // já extraído (copiar dele pra cima). Defensivo: sem data reconhecida, a janela
    // não corta → rola até o fim. Custo: o backend dedupa por ID antes da IA.
    const cfg = await chrome.storage.local.get(["lookbackDias", "casa", "stopId", "b365Marco", "b365Teto", "bfQtd", "bfDias", "bfFull"]);
    const N = Math.max(1, Number(cfg.lookbackDias) || 30);
    const cutoff = Date.now() - N * 86400000;
    const pisoSanidade = cutoff - 730 * 86400000;
    const casa = (cfg.casa || "").toLowerCase();
    const ctx = {
      cutoff, pisoSanidade,
      stopId: (cfg.stopId || "").trim().toUpperCase(),
      // Bet365 (sem data nem ID): marco = trecho do último bilhete já exportado;
      // teto = trava de custo (sem ID o backend não pré-dedupa).
      marco: (cfg.b365Marco || "").trim(),
      teto: Math.max(0, Number(cfg.b365Teto) || 0),
      parar: () => parar,
      painel,
    };
    // Betfair: histórico ILIMITADO (não corta como a Betano) → freio por QUANTIDADE
    // (padrão 100) + dias opcional + "varrer conta inteira". A lista é por POSTAGEM
    // (a resolução fica fora de ordem), então quantidade é o freio previsível.
    if (casa === "betfair") {
      ctx.varrerTudo = !!cfg.bfFull;
      ctx.qtdMax = ctx.varrerTudo ? 0 : Math.max(1, Number(cfg.bfQtd) || 100);   // 0 = sem limite
      const dias = Number(cfg.bfDias);
      ctx.bfCutoff = (!ctx.varrerTudo && cfg.bfDias && dias > 0) ? (Date.now() - dias * 86400000) : -Infinity;
    }

    let blocos;
    if (casa === "superbet") {
      // Modo passivo (rola + lê o JSON que a página recebe). Se nada foi capturado
      // (sb_inject inativo), cai no modo clique/DOM.
      blocos = await roboSuperbetPassive(ctx);
      if (!blocos.length) { console.log("[SharpenUp] nada capturado da API → modo clique"); blocos = await roboSuperbet(ctx); }
    } else if (casa === "bet365") {
      // Passivo + replay ativo (b3_inject): dado exato via /sportshistoryapi (código BR estável,
      // resultado, data de encerramento, jogo/mercado). Fallback: o robô de DOM atual (raspa
      // .myb-SettledBetItem) se a API não trouxer nada (token do replay recusado, ou a aba do
      // Histórico não foi aberta) — nunca fica pior que hoje.
      blocos = await roboBet365Passive(ctx);
      if (!blocos.length && !b3ById.size) {
        console.log("[SharpenUp] Bet365: API vazia → fallback DOM");
        blocos = await roboBet365DOM(ctx);
      }
    } else if (casa === "betesporte") {
      blocos = await roboBetesportePassive(ctx);
    } else if (casa === "betano") {
      blocos = await roboBetanoPassive(ctx);
      // Rede de segurança: se a API não trouxe NADA (aba aberta antes da extensão →
      // 1ª página perdida), cai no robô de texto atual — nunca fica pior que hoje.
      if (!blocos.length && !bnById.size) {
        console.log("[SharpenUp] Betano: API vazia → fallback texto");
        blocos = await roboScroll(ctx);
      }
    } else if (casa === "betfair") {
      // Passivo puro (bf_inject): dado exato com betId + settledDate. SEM fallback de
      // scrape DOM — a lista HTML da Betfair não tem data nem ID, scrape seria pior que
      // não enviar. API vazia (aba aberta antes da extensão) → o iniciarRobo avisa "nada
      // coletado"; basta recarregar a página da Betfair e rodar de novo.
      blocos = await roboBetfairPassive(ctx);
    } else if (casa === "pinnacle") {
      // Passivo + replay ativo (pn_inject): dado exato com id, das duas abas de uma vez
      // (Decidido na janela de dias + Não decidido inteira). SEM fallback de scrape DOM — a
      // tabela é a mesma resposta JSON que já lemos; scrape só perderia precisão. API vazia
      // (nenhum /wager-filter disparou) → o autodiagnóstico avisa; basta abrir a tela
      // "Minhas Apostas" e rodar de novo.
      blocos = await roboPinnaclePassive(ctx);
    } else {
      blocos = await roboScroll(ctx);   // genéricos
    }

    painel.remove();
    roboRodando = false;
    if (!blocos.length) {
      // Autodiagnóstico diferencial das casas-robô passivas (antes só a Betfair tinha; achado
      // #13). Distingue "hook NÃO carregou" (inject não injetou) de "endpoint mudou" (hook vivo,
      // 0 respostas) de "formato mudou / conta vazia" (respostas>0, 0 vistos). Antes tudo isso
      // caía num "Nada coletado" genérico → falha silenciosa quando a casa troca o DOM/endpoint.
      // Casas sem inject (genéricos) seguem no aviso genérico.
      const diag = {
        betfair:    { nome: "Betfair",    hook: bfHookVivo, resp: bfRespostas, vistos: bfTickets.length },
        superbet:   { nome: "Superbet",   hook: sbHookVivo, resp: sbRespostas, vistos: sbById.size },
        betesporte: { nome: "BETesporte", hook: beHookVivo, resp: beRespostas, vistos: beTickets.length },
        betano:     { nome: "Betano",     hook: bnHookVivo, resp: bnRespostas, vistos: bnById.size },
        pinnacle:   { nome: "Pinnacle",   hook: pnHookVivo, resp: pnRespostas, vistos: pnById.size },
        bet365:     { nome: "Bet365",     hook: b3HookVivo, resp: b3Soma("respostas"), vistos: b3ById.size,
                      // Extras só da Bet365: em quantos frames o inject respondeu (a área de
                      // membros é outra origem, em iframe) e quantas URLs com "history" passaram
                      // sem casar o padrão — separa "não alcancei o frame certo" de "endpoint mudou".
                      extra: " · frames: " + b3PorFrame.size + " · outras URLs de histórico: " + b3Soma("history") },
      }[casa];
      if (diag) {
        const msg = diag.nome + ": 0 bilhetes. Hook: " + (diag.hook ? "ATIVO" : "NÃO carregou") +
                    " · respostas da API: " + diag.resp + " · bilhetes vistos: " + diag.vistos +
                    (diag.extra || "");
        toastLocal(msg, false);
        // Escala ao popup (persistente) SÓ na falha inequívoca: inject não carregou OU o endpoint
        // não respondeu nenhuma vez. "respostas>0 & 0 vistos" fica só no toast — pode ser conta
        // genuinamente vazia, e um alerta persistente viraria falso positivo.
        if (!diag.hook || diag.resp === 0) {
          try { chrome.storage.local.set({ lastError: msg + " — a extensão pode precisar de atualização; avise o suporte." }); } catch (e) {}
        }
      } else {
        toastLocal("Nada coletado — rolagem/estrutura não reconhecida.", false);
      }
      return;
    }
    try { chrome.storage.local.remove("lastError"); } catch (e) {}   // rodada OK → limpa diagnóstico antigo
    chrome.runtime.sendMessage({ type: "ENVIAR_TEXTO", texto: blocos.join("\n\n") });
    toastLocal(blocos.length + " bilhete(s) coletado(s), enviando…", true);
  }

  // Estratégia genérica (Betano & cia): rola e colhe blocos de texto, dedup por
  // conteúdo. Retorna os blocos coletados.
  async function roboScroll(ctx) {
    const cont = acharScroll();
    const vistos = new Set(), blocos = [];
    let passou = false;
    const push = (t) => {
      t = (t || "").trim();
      const k = t.replace(/\s+/g, " ").toLowerCase();
      if (k.length >= 20 && !vistos.has(k)) {
        vistos.add(k); blocos.push(t);
        for (const ts of parseDatas(k)) { if (ts < ctx.cutoff && ts > ctx.pisoSanidade) passou = true; }
      }
    };
    const coletar = () => {
      const raiz = esDoc(cont) ? document.body : cont;
      let partes = (raiz.innerText || "").split(/\n\s*\n+/);
      if (partes.length <= 2) {
        const cards = acharCards(cont);
        if (cards && cards.length) partes = cards.map((el) => el.innerText);
      }
      partes.forEach(push);
      ctx.painel.contador.textContent = blocos.length + " bilhete" + (blocos.length === 1 ? "" : "s");
    };
    sTo(cont, 0); await sleep(450);
    let estavel = 0, voltas = 0;
    while (!ctx.parar() && voltas < 400) {
      voltas++;
      coletar();
      if (passou && voltas >= 2) break;
      const top = sTop(cont), max = sMax(cont);
      if (top >= max - 2) { coletar(); break; }
      sTo(cont, top + sClient(cont) * 0.8);
      await sleep(380);
      if (Math.abs(sTop(cont) - top) < 2) { if (++estavel > 3) break; } else estavel = 0;
    }
    coletar();
    return blocos;
  }

  // ── Superbet modo API (sem clique) ───────────────────────────────────────────
  // Chama a MESMA API que a página usa (GET /tickets?status=finished, header
  // sessionId, paginação por lastId = o cursor de código). Dado estruturado e exato:
  // ticketId, coefficient (odd), payment.stake, status, dateReceived, events[].
  // Data → fuso America/São_Paulo (a API vem em UTC; sem conversão a data pula 1 dia).
  const _dbr = (iso) => {
    if (!iso) return "";
    const d = new Date(iso);
    if (isNaN(d)) return "";
    const p = new Intl.DateTimeFormat("pt-BR", { timeZone: "America/Sao_Paulo", day: "2-digit", month: "2-digit", year: "numeric" }).formatToParts(d);
    const g = (t) => (p.find((x) => x.type === t) || {}).value || "";
    return g("day") + "/" + g("month") + "/" + g("year");
  };
  const _brl = (x) => (typeof x === "number") ? x.toFixed(2).replace(".", ",") : (x != null ? String(x) : "");
  // Odd SEMPRE completa (regra primordial: nunca encurtar). Só tira ruído de float
  // (ex.: 2.2700000000000002 → 2,27), mantendo toda a precisão real.
  const _odd = (x) => (x == null) ? "" : (Math.round(x * 1e8) / 1e8).toString().replace(".", ",");
  // Betano: Stake/Return vêm como string BRL pt-BR ("R$1.914,56" = ponto milhar, vírgula
  // decimal) → número. Odd vem como string com PONTO decimal ("2.02", "33.32") → número.
  // São gramáticas diferentes: nunca usar o parser de dinheiro numa odd (comeria o ponto).
  const _brlNum = (s) => {
    if (typeof s === "number") return s;
    const n = parseFloat(String(s || "").replace(/[^\d,.-]/g, "").replace(/\./g, "").replace(",", "."));
    return isNaN(n) ? null : n;
  };
  const _oddNum = (x) => {
    if (typeof x === "number") return x;
    const n = parseFloat(String(x || "").replace(",", "."));
    return isNaN(n) ? null : n;
  };
  // BETesporte: `date` vem SEM timezone ("2026-07-02T10:55:18") = já local (America/São
  // Paulo). Só recorta AAAA-MM-DD → DD/MM/AAAA. NÃO usar `_dbr` (converte de UTC → pula 1 dia).
  const _dbrBE = (s) => {
    const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(s || ""));
    return m ? (m[3] + "/" + m[2] + "/" + m[1]) : "";
  };
  // Betfair: `settledDate`/`placedDate` vêm como "12-jul-26 17:33:53" — mês PT abreviado,
  // JÁ em horário local (o mesmo do extrato). Só converte DD-mmm-YY → DD/MM/AAAA. NÃO usar
  // `_dbr` (é p/ ISO UTC → pularia 1 dia). Espelha o `_betfair_data` do backend.
  const _MESES_BF = { jan: "01", fev: "02", mar: "03", abr: "04", mai: "05", jun: "06",
                      jul: "07", ago: "08", set: "09", out: "10", nov: "11", dez: "12" };
  const _dbrBF = (s) => {
    const m = /^\s*(\d{1,2})-([a-zç]{3})-(\d{2})/.exec(String(s || "").toLowerCase());
    if (!m) return "";
    const mes = _MESES_BF[m[2]];
    return mes ? (m[1].padStart(2, "0") + "/" + mes + "/20" + m[3]) : "";
  };

  function formatTicket(t) {
    const pay = t.payment || {};
    const win = t.win || {};
    const stake = pay.stake != null ? pay.stake : pay.total;
    const evs = t.events || [];
    // Bilhete da aba "Em aberto" (URL status=active): ainda não liquidou. Sobe SEM
    // resultado (a IA deixa a coluna Resultado vazia → o backend grava 'aberta'); a odd
    // vai a estrutural (coefficient). Quando fechar, a re-extração (mesmo ticketId) faz
    // UPSERT e atualiza resultado/odd. Nunca liquidar um aberto pelo status.
    const aberta = !!t.__aberta;
    const cashout = !aberta && !!win.isCashedOut;
    const L = [];
    L.push("[Código: " + (t.ticketId || "") + "]");
    // Data = a do EVENTO mais recente (quando o bilhete resolve), não a de criação.
    const datasEv = evs.map((e) => (e.date ? Date.parse(e.date) : NaN)).filter((x) => !isNaN(x));
    const dataJogo = datasEv.length ? new Date(Math.max.apply(null, datasEv)).toISOString() : t.dateReceived;
    L.push("Data: " + _dbr(dataJogo));
    L.push("Apostado em: " + _dbr(t.dateReceived));
    L.push("Stake: " + _brl(stake));
    if (pay.bonusAmount) L.push("Freebet incluído: " + _brl(pay.bonusAmount) + " (dinheiro real = stake − freebet)");
    // Odd COMPLETA p/ cálculo: em VITÓRIA com boost (SUPERTURBO) a coefficient é
    // PRÉ-boost → a odd efetiva (que reconstrói o retorno) = retorno ÷ stake. Aberta =
    // coefficient estrutural (sem retorno realizado ainda).
    const efetiva = (!aberta && t.status === "win" && !cashout && win.payoff > 0 && stake > 0)
      ? (win.payoff / stake) : t.coefficient;
    L.push("Odd total: " + _odd(efetiva));
    // Resultado bruto: a IA/CASA_SUPERBET aplica a regra (win→W, lost→L, cashout→V/W).
    let st = aberta ? "em aberto (aguardando resultado — NÃO liquidar; sem resultado)"
                    : (cashout ? "cashout" : (t.status || ""));
    // Em aberto, `win.payoff` é ganho POTENCIAL (não realizado) → rotula como tal.
    L.push("Status: " + st + (win.payoff != null ? ((aberta ? " · ganho potencial " : " · retorno ") + _brl(win.payoff)) : ""));
    L.push("Seleções (" + evs.length + "):");
    for (const e of evs) {
      const nome = Array.isArray(e.name) ? e.name.join(" — ") : (e.name || "");
      const mkt = (e.market && e.market.name) || "";
      let sel = (e.odd && e.odd.name) || "";
      if (sel && sel === mkt) sel = "";   // evita duplicação (mercado == seleção)
      let desc = [mkt, sel].filter(Boolean).join(" — ");
      // Criar Aposta / bet-builder: mercado/odd vazios no topo → as sub-seleções ficam
      // em eventComponents (cada uma: market.name + oddComponent.name).
      const comps = Array.isArray(e.eventComponents) ? e.eventComponents : [];
      if (!desc && comps.length) {
        desc = comps.map((c) => {
          const cm = (c.market && c.market.name) || "";
          const cs = (c.oddComponent && c.oddComponent.name) || "";
          return [cm, cs].filter(Boolean).join(": ");
        }).filter(Boolean).join(" + ");
      }
      const oc = e.odd && e.odd.coefficient;
      const dt = _dbr(e.date);
      L.push("  • " + (dt ? dt + " · " : "") + nome + (desc ? " · " + desc : "") +
             (oc != null ? " @ " + _odd(oc) : ""));
    }
    return L.join("\n");
  }

  // Modo passivo: rola a lista p/ a página paginar (lazy-load) e vai consumindo os
  // tickets que o sb_inject captura das RESPOSTAS da API (JSON exato do site). Sem
  // clique. Para no stopId (copiar dele pra cima) ou na janela de dias.
  // Scroller da lista: `.sb-my-bets__items` se ele mesmo rolar; senão o maior
  // scroller da página (geralmente o document).
  function acharScrollSuperbet() {
    const c = document.querySelector(".sb-my-bets__items");
    if (c && c.scrollHeight > c.clientHeight + 20) return c;
    return acharScroll();
  }

  async function roboSuperbetPassive(ctx) {
    const cont = acharScrollSuperbet();
    const blocos = [], usados = new Set();
    let travado = false;
    // Aba "Em aberto" (/minhas-apostas/abertos): abertas são recentes → a janela de dias
    // NÃO corta (senão uma liquidada velha ainda em memória interromperia antes das abertas).
    const naAbaAberta = /abertos/i.test(location.pathname);

    const processar = () => {
      for (const t of sbById.values()) {
        const cod = (t.ticketId || "").toUpperCase();
        if (!cod || usados.has(cod)) continue;
        if (ctx.stopId && cod === ctx.stopId) { travado = true; return; }   // último já extraído
        usados.add(cod);
        const dt = t.dateReceived ? Date.parse(t.dateReceived) : NaN;
        // Janela de dias corta só LIQUIDADAS e só fora da aba Em aberto.
        const passou = !naAbaAberta && !t.__aberta && !isNaN(dt) && dt < ctx.cutoff && dt > ctx.pisoSanidade;
        blocos.push(formatTicket(t));
        ctx.painel.contador.textContent = blocos.length + " bilhete" + (blocos.length === 1 ? "" : "s");
        if (passou) { travado = true; return; }   // passou da janela → para
      }
    };

    // Pede ao sb_inject o que ele já capturou (a 1ª página vem no load da página,
    // antes deste content script estar pronto pra ouvir).
    try { window.postMessage({ __sharpenupSBReq: true }, "*"); } catch (e) {}
    await sleep(250);
    processar();                 // o que já veio no load da página

    // Rola JANELA + container até o fim, repetidamente, até a página parar de trazer
    // bilhetes novos (dispara o lazy-load independe de qual elemento rola de fato).
    let semNovo = 0, ultTotal = -1, voltas = 0;
    while (!ctx.parar() && !travado && voltas < 500) {
      voltas++;
      try { window.scrollTo(0, document.documentElement.scrollHeight); } catch (e) {}
      try { if (cont && cont !== document.scrollingElement && cont !== document.documentElement) cont.scrollTop = cont.scrollHeight; } catch (e) {}
      await sleep(700);
      processar();
      if (travado) break;
      if (sbById.size > ultTotal) { ultTotal = sbById.size; semNovo = 0; }
      else if (++semNovo >= 5) break;   // 5 rolagens sem nada novo → fim da lista
    }
    processar();
    console.log("[SharpenUp] passivo: " + blocos.length + " bilhete(s) · sbById=" + sbById.size +
                " · aba=" + (naAbaAberta ? "abertas" : "liquidadas"));
    return blocos;
  }

  // ── BETesporte modo API (sem clique) ─────────────────────────────────────────
  // Formata 1 item da /api/bet/RequestUserTickets no bloco de texto que a IA lê
  // (mesmo marcador "[Código: …]" da Superbet → o backend split/dedupa por ele).
  // Status: 1=Perdido(L), 2=Ganho(W) — os únicos observados. Perna ABERTA (openBetsCount>0)
  // → sobe SEM resultado ('aberta'; UPSERT por código atualiza quando fechar). Devolvido/
  // Encerrado/Cancelado ainda sem amostra → "a conferir" (regra da casa: nunca chutar resultado).
  function formatTicketBE(t) {
    const L = [];
    L.push("[Código: " + (t.id != null ? t.id : "") + "]");
    L.push("Data: " + _dbrBE(t.date));
    L.push("Stake: " + _brl(t.value));
    L.push("Odd: " + _odd(t.odd));
    // "possibleReturn" = value × odd = retorno POTENCIAL (não o realizado). Rotulado
    // como tal p/ a IA nunca confundir o potencial de um bilhete PERDIDO com vitória —
    // quem decide W/L é o Status. Em W, potencial = realizado (cross-check: ÷ stake = odd).
    if (t.possibleReturn != null) L.push("Retorno potencial: " + _brl(t.possibleReturn));
    if (t.cashoutValue && t.cashoutValue > 0) L.push("Cashout: " + _brl(t.cashoutValue));
    let st;
    // Aberta (perna ainda não liquidada): sobe SEM resultado → o backend grava 'aberta'
    // e faz UPSERT por código quando o bilhete fechar (atualiza, não duplica). Sinal
    // explícito (igual à Betano) p/ a IA deixar a coluna Resultado vazia, nunca chutar.
    if (t.openBetsCount && t.openBetsCount > 0) st = "em aberto (aguardando resultado — NÃO liquidar; sem resultado)";
    else if (t.status === 1) st = "1 (Perdido → L)";
    else if (t.status === 2) st = "2 (Ganho → W)";
    else st = t.status + " (a conferir — não liquidar automaticamente)";
    L.push("Status: " + st);
    const mercado = (t.betNome || "").trim();
    const titulo = (t.partidaNome || t.homeTeamName || "").trim();
    if (mercado) L.push("Mercado: " + mercado);
    if (titulo && titulo !== mercado) L.push("Título: " + titulo);
    if (t.optionNome) L.push("Seleção: " + t.optionNome);
    return L.join("\n");
  }

  // ── Betano modo API (sem clique) ─────────────────────────────────────────────
  // Formata 1 bilhete da /api/ma/bet/bet-history-v3 no bloco de texto que a IA lê (mesmo
  // marcador "[Código: …]" das outras casas → o backend split/dedupa por ele). Datas em
  // UTC ("…Z") → America/São_Paulo (_dbr). Fiel ao CASA_BETANO §4/§5/§11:
  //   • Data = PlacedAt (colocação; proxy do evento p/ mesmo-dia — a casa não expõe a do jogo).
  //   • Status do bilhete: 2=Ganho→W · 3=Perdido→L · 0=Devolvido/Anulado→V. `Return` cruza
  //     (Ganhos=0→L, =Stake→V, >Stake→W) — quem decide W/L/V é o pipeline, não a extensão.
  //   • Odd: W = Return÷Stake com precisão total (respeita boost, §11) · L/V = odd combinada
  //     estrutural (DecimalOdds; já é o produto das seleções nas múltiplas).
  const _TIPO_BN = { Single: "Simples", Double: "Dupla", Triple: "Tripla" };
  function formatTicketBN(t) {
    const L = [];
    // Bilhete da aba "Em aberto": ainda não liquidou. Sobe SEM resultado (a IA deixa a
    // coluna Resultado vazia → o backend grava 'aberta'). A odd vai a estrutural
    // (DecimalOdds); quando o bilhete fechar, a re-extração (mesmo BetId) faz UPSERT e
    // atualiza resultado/odd. Nunca liquidar um bilhete aberto pelo Status numérico.
    const aberta = !!t.__aberta;
    const stake = _brlNum(t.Stake);
    const ret = _brlNum(t.Return);
    const legs = Array.isArray(t.Legs) ? t.Legs : [];
    const legItems = [];
    for (const lg of legs) for (const li of (lg.LegItems || [])) legItems.push(li);
    const criarAposta = legItems.some((li) => li.ComboLegType === 1);

    L.push("[Código: " + (t.BetId != null ? t.BetId : "") + "]");
    L.push("Data: " + _dbr(t.PlacedAt));
    let tipo = _TIPO_BN[t.Type];
    if (!tipo) {
      const acc = t.Accumulator || "";
      // "3-fold" etc. serve; o placeholder cru "{number}-fold" da API não → usa a contagem de pernas.
      if (acc && acc !== "Single" && acc.indexOf("{") < 0) tipo = acc;
      else if (legItems.length > 1) tipo = legItems.length + "-seleções";
      else tipo = t.Type || "";
    }
    if (criarAposta) tipo = (tipo ? tipo + " " : "") + "(Criar Aposta)";
    if (tipo) L.push("Tipo: " + tipo);
    L.push("Stake: " + _brl(stake));

    // Resultado bruto — a IA/CASA_BETANO aplica a regra final. Status do bilhete:
    //   2=Ganho→W · 3=Perdido→L · 0=Devolvido/Anulado→V · 6=Cash Out (regra financeira §7).
    // Cashout (Status 6, confirmado): sacado = stake → V (odd exibida) · ≠ stake → W
    // (Odd = Cashout÷Stake; cobre o parcial: retorno<stake vira W com odd<1, preserva o recuperado).
    const cashout = !aberta && ((t.Status === 6) || !!t.IsCreditCashout);
    const cashoutEqStake = cashout && ret != null && stake != null && Math.abs(ret - stake) < 0.005;
    let stTxt;
    if (aberta) stTxt = "em aberto (aguardando resultado — NÃO liquidar; sem resultado)";
    else if (cashoutEqStake) stTxt = "Cash Out (sacado = stake) → V";
    else if (cashout) stTxt = "Cash Out (sacado ≠ stake) → W";
    else if (t.Status === 2) stTxt = "Ganho → W";
    else if (t.Status === 3) stTxt = "Perdido → L";
    else if (t.Status === 0) stTxt = "Devolvido/Anulado → V";
    else stTxt = t.Status + " (a conferir — não liquidar automaticamente)";
    // Em aberto: `Return` é potencial (não realizado) → rotula como tal p/ a IA nunca
    // confundir com vitória. Liquidado: `Return` é o retorno real.
    L.push("Status: " + stTxt + (t.Return != null ? ((aberta ? " · Retorno potencial " : " · Retorno ") + t.Return) : ""));
    if (cashout && t.Return != null) L.push("Cash Out: " + t.Return);   // sinal explícito p/ o pipeline

    // Odd total: W (Ganho OU cashout≠stake) = Return÷Stake (respeita boost, §11); L/V/cashout=stake
    // e ABERTA = odd combinada estrutural (DecimalOdds; já é o produto das pernas nas múltiplas).
    const oddW = !aberta && ret != null && stake > 0 && (t.Status === 2 || (cashout && !cashoutEqStake));
    const oddTot = oddW ? (ret / stake)
                 : (typeof t.DecimalOdds === "number" ? t.DecimalOdds : _oddNum(t.Odds));
    L.push("Odd total: " + _odd(oddTot) + (oddW ? " (= Retorno ÷ Stake)" : ""));

    L.push("Seleções:");
    for (const li of legItems) {
      const legOdd = (typeof li.DecimalOdds === "number") ? li.DecimalOdds : _oddNum(li.Odds);
      const sels = Array.isArray(li.Selections) ? li.Selections : [];
      if (li.ComboLegType === 1 && sels.length > 1) {
        // Criar Aposta: sub-seleções combinadas numa perna, odd única (não repetir por sub).
        const game = (sels[0] && sels[0].Game) || "";
        L.push("  • [Criar Aposta @ " + _odd(legOdd) + "]" + (game ? " " + game : "") + ":");
        for (const s of sels) L.push("      - " + (s.Title || "") + (s.Market ? " · " + s.Market : ""));
      } else {
        for (const s of sels) {
          const so = _oddNum(s.Odd);
          const boost = (s.OddsBeforeEnhancement && s.OddsBeforeEnhancement !== s.Odd)
            ? " (sem boost " + String(s.OddsBeforeEnhancement).replace(".", ",") + ")" : "";
          const partes = [s.Sport, s.Game, s.Market, s.Title].filter(Boolean).join(" · ");
          L.push("  • " + partes + " @ " + _odd(so != null ? so : legOdd) + boost);
        }
      }
    }
    return L.join("\n");
  }

  // ── Betfair modo API (sem clique) ─────────────────────────────────────────────
  // Formata 1 bilhete do POST /activity/sportsbook no bloco de texto que a IA lê (mesmo
  // marcador "[Código: O/…]" das outras casas passivas → o backend split/dedupa por ele).
  // Datas: settledDate/placedDate vêm "DD-mmm-YY HH:MM:SS" JÁ em horário local (_dbrBF).
  // Fiel ao CASA_BETFAIR §4/§5/§11:
  //   • Data = settledDate (RESOLUÇÃO — existe até nas perdas, ao contrário do extrato CSV).
  //   • Status: WON→W · LOST→L · VOID→V · cashout (fullCashout/isPartialCashOut) → regra §7.
  //   • Odd: W = rawPotentialReturn÷rawStake (precisão total, respeita boost/ODDSBOOST) ·
  //     L/V = odd exibida (originalOdds.decimal, nunca 0/1) · múltipla = combinedOdds.
  const _TIPO_BF = { SGL: "Simples" };
  function formatTicketBF(t) {
    const L = [];
    const stake = (typeof t.rawStake === "number") ? t.rawStake : _brlNum(t.stake);
    const ret = (typeof t.rawPotentialReturn === "number") ? t.rawPotentialReturn : _brlNum(t.potentialReturn);
    const oddDec = _oddNum((t.originalOdds && t.originalOdds.decimal) || t.combinedOdds);
    const combined = _oddNum(t.combinedOdds);
    const parts = Array.isArray(t.parts) ? t.parts : null;
    const st = String(t.status || t.result || "").toUpperCase();
    const isMult = (t.betType && t.betType !== "SGL") || (parts && parts.length > 1) || combined != null;

    L.push("[Código: " + (t.betId || "") + "]");
    L.push("Data: " + _dbrBF(t.settledDate));   // resolução (col Data); nunca a colocação
    if (t.placedDate) L.push("Apostado em: " + _dbrBF(t.placedDate));
    if (t.sportName) L.push("Esporte (casa): " + t.sportName + (t.competitionName ? " · " + t.competitionName : ""));

    L.push("Tipo: " + (_TIPO_BF[t.betType] || (isMult ? "Múltipla" : "Simples")));
    L.push("Stake: " + _brl(stake));
    // Freebet faz PARTE do stake (dinheiro real = stake − freebet) → não pode ser MAIOR
    // que o stake. Valor absurdo (visto num Each Way de outright: 10000 num stake de 200)
    // = leitura errada do campo → não exibe, senão gera "dinheiro real" negativo.
    if (t.stakeBonus) {
      const fb = _brlNum(t.stakeBonus);
      if (fb != null && fb > 0 && fb <= stake)
        L.push("Freebet incluído: " + _brl(fb) + " (dinheiro real = stake − freebet)");
    }

    // Status/resultado bruto — a IA/CASA_BETFAIR aplica a regra final (nunca copiar o
    // código visual V/P/N da tela; aqui já vem o status textual limpo do JSON).
    const cashout = !!t.fullCashout || !!t.isPartialCashOut;
    let stTxt;
    if (cashout) stTxt = "Cash Out (" + (t.isPartialCashOut ? "parcial" : "total") + ") → regra §7 (Cash Out ÷ Stake)";
    else if (st === "WON") stTxt = "WON → W";
    else if (st === "LOST") stTxt = "LOST → L";
    else if (st === "VOID") stTxt = "VOID → V";
    else stTxt = st + " (a conferir — não liquidar automaticamente)";
    L.push("Status: " + stTxt + (t.potentialReturn != null ? (" · Retorno " + t.potentialReturn) : ""));
    if (cashout && t.potentialReturn != null) L.push("Cash Out: " + t.potentialReturn);

    // Odd total: W (WON ou cashout com retorno) = Retorno÷Stake (precisão total, respeita
    // boost/ODDSBOOST); L/V = odd exibida; múltipla sem win = combinedOdds estrutural.
    const oddW = ret != null && stake > 0 && (st === "WON" || (cashout && ret > 0));
    let oddTot = oddW ? (ret / stake) : (isMult && combined != null ? combined : oddDec);
    // Múltipla perdida às vezes vem SEM combinedOdds nem originalOdds.decimal → reconstrói
    // a odd combinada pelo PRODUTO das pernas (cada `part` traz a sua odd). Só quando TODAS
    // as pernas têm odd válida (senão deixa vazio, honesto — nunca inventa odd parcial).
    if (oddTot == null && isMult && parts && parts.length) {
      let prod = 1, ok = true;
      for (const p of parts) {
        const po = _oddNum((p.originalOdds && p.originalOdds.decimal) || p.odds || p.decimalOdds);
        if (po != null && po > 0) prod *= po; else { ok = false; break; }
      }
      if (ok) oddTot = prod;
    }
    L.push("Odd total: " + _odd(oddTot) + (oddW ? " (= Retorno ÷ Stake)" : ""));

    L.push("Seleções:");
    if (isMult && parts && parts.length) {
      for (const p of parts) {
        const po = _oddNum((p.originalOdds && p.originalOdds.decimal) || p.odds || p.decimalOdds);
        const desc = [p.eventDescription, p.marketName, p.selection].filter(Boolean).join(" · ");
        L.push("  • " + desc + (po != null ? " @ " + _odd(po) : ""));
      }
    } else {
      const mt = t.marketType ? " [" + t.marketType + "]" : "";
      const hcp = (t.handicap != null && t.handicap !== "") ? " (handicap " + t.handicap + ")" : "";
      const desc = [t.eventDescription, (t.marketName || t.eventMarketDescription || "") + mt, t.selection].filter(Boolean).join(" · ");
      L.push("  • " + desc + hcp + (oddDec != null ? " @ " + _odd(oddDec) : ""));
    }
    return L.join("\n");
  }

  // ── Pinnacle modo API (sem clique) ────────────────────────────────────────────
  // Formata 1 bilhete do POST /wager-filter (já convertido de array posicional p/ objeto
  // pelo pn_inject) no bloco de texto que a IA lê (mesmo marcador "[Código: …]" das outras
  // casas passivas → o backend split/dedupa por ele). Fiel à CASA_PINNACLE:
  //   • Data = data do EVENTO (§4: evento ≈ liquidação; a colocação NUNCA é usada).
  //   • Decimal exibido com PONTO → vírgula (§1). Odd preservada na precisão original (§11).
  //   • Sem boost e sem cashout (§6/§7): a odd exibida é autoritativa; P/L é só cross-check.
  //   • Resultado: WON→W · LOST→L · PUSHED/Void→V · quarto de handicap pode dar HW/HL (§5);
  //     a IA decide o código final — a extensão só entrega o rótulo cru + o P/L p/ conferir.
  //   • Aberta (status ≠ SETTLED): sobe SEM resultado → o backend grava 'aberta' e faz UPSERT
  //     por id quando o bilhete fechar (atualiza, não duplica).
  // Datas "YYYY-MM-DD" (evento) já são locais (America/São Paulo) → só recorta DD/MM/AAAA
  // (NÃO usar _dbr, que converte de UTC e pularia 1 dia).
  const _dbrPN = (s) => {
    const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(s || ""));
    return m ? (m[3] + "/" + m[2] + "/" + m[1]) : "";
  };
  // Odd Pinnacle: string com PONTO ("1.636", "18.060") → vírgula, precisão intacta.
  const _oddPN = (s) => {
    const str = String(s == null ? "" : s).trim();
    return str ? str.replace(".", ",") : "";
  };
  // Linha (handicap/total): número → texto pt-BR. NÃO força "+": em Over/Under a linha é um
  // total (ex.: 20,5, sem sinal) e um "+" seria enganoso; em handicap positivo a IA deduz o
  // sinal pelo contexto (seleção = time + linha), como a CASA_PINNACLE ensina. O "-" natural
  // do handicap negativo é preservado.
  const _linhaPN = (n) => (n == null || n === 0) ? "" : String(n).replace(".", ",");

  function formatTicketPN(t) {
    const L = [];
    L.push("[Código: " + (t.id != null ? t.id : "") + "]");
    L.push("Data: " + _dbrPN(t.dataEvento));                 // data do evento (a que vale)
    if (t.dataColoc) L.push("Apostado em: " + _dbrPN(t.dataColoc));
    L.push("Stake: " + _brl(t.stake));

    // Resultado bruto — a IA/CASA_PINNACLE aplica a regra final. Aberta = sem resultado.
    let stTxt;
    if (t.aberta) {
      stTxt = "em aberto (aguardando resultado — NÃO liquidar; sem resultado)";
    } else {
      const rot = String(t.resultLabel || t.resultRaw || "").toUpperCase();
      if (rot === "WON" || rot === "WIN") stTxt = "Ganho (WON) → W";
      else if (rot === "LOST" || rot === "LOSE") stTxt = "Perdeu (LOST) → L";
      else if (rot === "PUSHED" || rot === "PUSH" || rot === "VOID" || rot === "REFUND") stTxt = rot + " → V";
      else stTxt = (rot || "?") + " (a conferir — não liquidar automaticamente)";
    }
    // P/L líquido (Vitória/derrota) — cross-check p/ a IA distinguir HW/HL de W/L cheio.
    // Nunca é cashout (Pinnacle não tem): é o P/L de liquidação normal.
    const plTxt = (t.plNet != null && !t.aberta) ? " · P/L " + _brl(t.plNet) : "";
    L.push("Status: " + stTxt + plTxt);
    L.push("Odd total: " + _oddPN(t.odd));

    // Múltipla (Mix Parlay): sinaliza o tipo p/ a IA classificar (MASTER_ESPORTES: mistura de
    // esportes OU 3+ jogos diferentes → Múltiplos). Simples: esporte genérico (§13: nunca
    // promover p/ a liga). Localização (Tennis→Tênis…) fica com a IA/CASA_PINNACLE.
    if (t.pernas && t.pernas.length) {
      L.push("Tipo: Múltipla (" + t.pernas.length + " seleções)");
    } else if (t.esporte) {
      L.push("Esporte (casa): " + t.esporte + (t.liga ? " · " + t.liga : ""));
    }

    L.push("Seleções:");
    if (t.pernas && t.pernas.length) {
      // Múltipla (Mix Parlay): cada perna com seu confronto, seleção, linha, odd e data.
      for (const p of t.pernas) {
        const lin = _linhaPN(p.linha);
        const sel = (p.selecao + (lin ? " " + lin : "")).trim();
        const partes = [p.esporte, p.liga, sel, _confrontoPN(p.confronto)].filter(Boolean).join(" · ");
        const un = p.unidade ? " (" + p.unidade + ")" : "";
        L.push("  • " + partes + un +
               (p.odd ? " @ " + _oddPN(p.odd) : "") +
               (p.dataEvento ? " · " + _dbrPN(p.dataEvento) : ""));
      }
    } else {
      // Simples: seleção (ou lado "Mais de/Menos de" + prop) + linha, depois o confronto.
      const conf = _confrontoPN(t.confronto);
      const pick = t.selecao || [t.ladoSel, t.titulo].filter(Boolean).join(" ");
      const lin = _linhaPN(t.linha);
      const un = t.unidade ? " (" + t.unidade + ")" : "";
      const cat = t.categoria ? " [" + t.categoria + "]" : "";
      L.push("  • " + [(pick + (lin ? " " + lin : "")).trim(), conf].filter(Boolean).join(" · ") + un + cat);
    }
    return L.join("\n");
  }
  // Confronto: a Pinnacle usa "A -vs- B"; a descrição global usa "A v B". Normaliza aqui
  // (a IA também sabe, mas entregar já limpo evita ruído). Remove placar ao vivo "[0-0]".
  function _confrontoPN(s) {
    return String(s || "").replace(/\s*\[[0-9]+-[0-9]+\]\s*/g, " ")
      .replace(/\s*-vs-\s*/gi, " v ").replace(/\s+/g, " ").trim();
  }

  // Acha o elemento clicável VISÍVEL cujo rótulo contém a frase (menor texto = o mais
  // específico). Botões/links primeiro; se não achar, um elemento com o texto exato e
  // sobe pro ancestral clicável. Usado p/ "CARREGAR MAIS…" e "FILTRAR".
  const _normBtn = (s) => (s || "").replace(/\s+/g, " ").trim().toLowerCase();
  const _acharBotao = (frase) => {
    let best = null, bestLen = Infinity;
    for (const b of document.querySelectorAll("button, a, [role=button], .btn, input[type=button], input[type=submit]")) {
      if (b.offsetParent === null) continue;
      const t = _normBtn(b.textContent || b.value);
      if (t.includes(frase) && t.length < bestLen) { best = b; bestLen = t.length; }
    }
    if (best) return best;
    for (const el of document.querySelectorAll("div, span, p, li")) {
      if (el.offsetParent === null) continue;
      const t = _normBtn(el.textContent);
      if (t === frase || t.replace(/[.\s…]+$/, "") === frase) return el.closest("button, a, [role=button], .btn") || el;
    }
    return null;
  };
  // Clique robusto: Angular não checa isTrusted, mas alguns handlers querem a sequência
  // pointer/mouse completa. Dispara tudo + o .click() nativo.
  function _clicarForte(el) {
    try { el.scrollIntoView({ block: "center" }); } catch (e) {}
    const o = { bubbles: true, cancelable: true, view: window };
    for (const tipo of ["pointerdown", "mousedown", "pointerup", "mouseup"]) {
      try { el.dispatchEvent(new MouseEvent(tipo, o)); } catch (e) {}
    }
    try { el.click(); } catch (e) {}   // click nativo (sem duplicar com um dispatch de "click")
  }

  // Modo passivo (dado vem do be_inject: exato, com id). A BETesporte pagina por BOTÃO
  // "CARREGAR MAIS…" (não scroll infinito) → o robô CLICA o botão até ele sumir, e vai
  // consumindo o que a API entrega a cada página. Se a aba já estava aberta antes da
  // extensão, o be_inject pode ter perdido a 1ª página → o robô força um refetch clicando
  // "FILTRAR". Para no stopId (copiar dele pra cima) ou na janela de dias.
  async function roboBetesportePassive(ctx) {
    const blocos = [], usados = new Set();
    let travado = false;

    const processar = () => {
      for (const t of beTickets) {
        const cod = (t.id != null ? String(t.id) : "").toUpperCase();
        if (!cod || usados.has(cod)) continue;
        if (ctx.stopId && cod === ctx.stopId) { travado = true; return; }   // último já extraído
        usados.add(cod);
        const dt = t.date ? Date.parse(t.date) : NaN;
        const passou = !isNaN(dt) && dt < ctx.cutoff && dt > ctx.pisoSanidade;
        blocos.push(formatTicketBE(t));
        ctx.painel.contador.textContent = blocos.length + " bilhete" + (blocos.length === 1 ? "" : "s");
        if (passou) { travado = true; return; }   // passou da janela → para
      }
    };

    // Pede ao be_inject o que ele já capturou (a 1ª página vem no load da página).
    try { window.postMessage({ __sharpenupBEReq: true }, "*"); } catch (e) {}
    await sleep(350);
    processar();

    // be_inject perdeu a 1ª página (aba aberta antes da extensão)? Força um refetch
    // clicando "FILTRAR" (recarrega a lista com o filtro atual → a API dispara de novo).
    if (!blocos.length && beTickets.length === 0) {
      const filtrar = _acharBotao("filtrar");
      if (filtrar) { try { filtrar.click(); } catch (e) {} await sleep(1500); processar(); }
    }

    // Pagina clicando "CARREGAR MAIS…". ENCERRA sozinho após 5s sem bilhete novo —
    // INDEPENDENTE do botão continuar na tela (a BETesporte o mantém no fim). Usa RELÓGIO
    // (não contagem de voltas) → robusto a variação de tempo de rede. Ao sair do while, o
    // iniciarRobo envia automaticamente (sem precisar clicar Parar).
    let voltas = 0, ultTotal = -1, ultCresceu = Date.now();
    while (!ctx.parar() && !travado && voltas < 400) {
      voltas++;
      processar();
      if (travado) break;
      const mais = _acharBotao("carregar mais");
      if (mais) { _clicarForte(mais); await sleep(1000); }
      else { try { window.scrollTo(0, document.documentElement.scrollHeight); } catch (e) {} await sleep(600); }
      processar();
      if (beTickets.length > ultTotal) { ultTotal = beTickets.length; ultCresceu = Date.now(); }
      else if (Date.now() - ultCresceu > 5000) break;   // 5s sem bilhete novo → encerra e envia
    }
    processar();
    console.log("[SharpenUp] BETesporte: " + blocos.length + " bilhete(s) · beTickets capturados=" + beTickets.length);
    return blocos;
  }

  // Modo passivo (dado vem do bn_inject: exato, com BetId). A Betano pagina por SCROLL
  // infinito (levas de 10, cursor lastId) → o robô ROLA até o fundo repetidamente p/ a
  // página buscar mais, e vai consumindo o JSON. A ROLAGEM é idêntica à que já funciona
  // hoje (gruda no fundo); só a LEITURA muda (JSON exato, não scraping). Serve às DUAS
  // abas: liquidadas (com resultado) e Em aberto (sem resultado → o backend grava 'aberta').
  // Para no stopId (copiar dele pra cima), na janela de dias (só liquidadas), OU — sinal
  // autoritativo — quando a LISTA ATIVA chega à página FINAL sem LastId (fimAtivo). NUNCA
  // para no 1º obstáculo: só desiste por teto após MUITOS segundos parado sem sinal de fim.
  async function roboBetanoPassive(ctx) {
    const cont = acharScroll();
    const blocos = [], usados = new Set();
    let travado = false;
    // Aba "Em aberto" (/bethistory/open): abertas são sempre recentes → a janela de dias
    // NÃO corta (senão uma liquidada velha ainda em memória interromperia antes das abertas).
    const naAbaAberta = /\/open(\b|$|\/)/i.test(location.pathname);

    const processar = () => {
      for (const t of bnById.values()) {
        const cod = (t.BetId != null ? String(t.BetId) : "").toUpperCase();
        if (!cod || usados.has(cod)) continue;
        if (ctx.stopId && cod === ctx.stopId) { travado = true; return; }   // último já extraído
        usados.add(cod);
        const dt = t.PlacedAt ? Date.parse(t.PlacedAt) : NaN;
        // Janela de dias corta só LIQUIDADAS e só fora da aba Em aberto.
        const passou = !naAbaAberta && !t.__aberta && !isNaN(dt) && dt < ctx.cutoff && dt > ctx.pisoSanidade;
        blocos.push(formatTicketBN(t));
        ctx.painel.contador.textContent = blocos.length + " bilhete" + (blocos.length === 1 ? "" : "s");
        if (passou) { travado = true; return; }   // passou da janela de dias → para
      }
    };
    // Fim autoritativo da paginação = o da LISTA que está aberta na tela.
    const fimAtivo = () => (naAbaAberta ? bnFimOpen : bnFimSettled);

    // Pede ao bn_inject o que já capturou (a 1ª página vem no load da página).
    try { window.postMessage({ __sharpenupBNReq: true }, "*"); } catch (e) {}
    await sleep(300);
    processar();

    // Rola do topo p/ garantir que nada da 1ª leva foi pulado, depois gruda no fundo.
    sTo(cont, 0); await sleep(400);
    let voltas = 0, ultTotal = -1, ultCresceu = Date.now();
    while (!ctx.parar() && !travado && !fimAtivo() && voltas < 3000) {
      voltas++;
      // Gruda no fundo p/ disparar o lazy-load da próxima leva (comportamento que já funciona).
      try { window.scrollTo(0, document.documentElement.scrollHeight); } catch (e) {}
      try { if (cont && cont !== document.scrollingElement && cont !== document.documentElement) cont.scrollTop = cont.scrollHeight; } catch (e) {}
      await sleep(700);
      processar();
      if (travado) break;
      if (bnById.size > ultTotal) { ultTotal = bnById.size; ultCresceu = Date.now(); }
      else if (Date.now() - ultCresceu > 12000) break;   // 12s parado, sem fim real → desiste (nunca no 1º obstáculo)
    }
    await sleep(400);
    processar();   // consome a última leva (inclusive a página final sem LastId)
    console.log("[SharpenUp] Betano: " + blocos.length + " bilhete(s) · bnById=" + bnById.size +
                " · aba=" + (naAbaAberta ? "abertas" : "liquidadas") + " · fimOpen=" + bnFimOpen + " · fimSettled=" + bnFimSettled);
    return blocos;
  }

  // Modo passivo (dado vem do bf_inject: exato, com betId O/…). A Betfair pagina por SCROLL
  // (levas de 10, cursor nextPageIndex) → o robô ROLA até o fundo repetidamente p/ a página
  // buscar mais, e vai consumindo o JSON. Para no stopId (copiar dele pra cima), na janela de
  // dias (por settledDate), OU — sinal autoritativo — quando a página traz `moreAvailable:false`
  // (bfFimReal). NUNCA para no primeiro obstáculo: só desiste por teto após MUITOS segundos
  // totalmente parado sem sinal de fim. Espelho do roboBetanoPassive.
  async function roboBetfairPassive(ctx) {
    const cont = acharScroll();
    const blocos = [], usados = new Set();
    let travado = false;

    const processar = () => {
      for (const t of bfTickets) {
        const cod = (t.betId || "").toUpperCase();
        if (!cod || usados.has(cod)) continue;
        if (ctx.stopId && cod === ctx.stopId) { travado = true; return; }   // último já extraído
        usados.add(cod);
        // Freio da Betfair (histórico ilimitado): QUANTIDADE (padrão 100) é o principal;
        // dias é opcional (janela pela settledDate); "varrer tudo" ignora ambos.
        const dbr = _dbrBF(t.settledDate);
        let dt = NaN;
        if (dbr) { const pp = dbr.split("/"); dt = Date.UTC(+pp[2], +pp[1] - 1, +pp[0]); }
        const passouDias = ctx.bfCutoff > -Infinity && !isNaN(dt) && dt < ctx.bfCutoff;
        blocos.push(formatTicketBF(t));
        ctx.painel.contador.textContent = blocos.length + " bilhete" + (blocos.length === 1 ? "" : "s");
        if (passouDias) { travado = true; return; }                                  // passou da janela de dias
        if (ctx.qtdMax && blocos.length >= ctx.qtdMax) { travado = true; return; }   // atingiu a quantidade
      }
    };

    // Pede ao bf_inject o estado + ARRANCA a paginação ativa até o teto (o bf_inject
    // pagina sozinho pela API — não depende do scroll da página). Varrer tudo → limite 0.
    try { window.postMessage({ __sharpenupBFReq: true, limite: (ctx.varrerTudo ? 0 : (ctx.qtdMax || 0)) }, "*"); } catch (e) {}
    await sleep(300);
    processar();

    // Rola do topo p/ garantir que nada da 1ª leva foi pulado, depois gruda no fundo.
    sTo(cont, 0); await sleep(400);
    let voltas = 0, ultTotal = -1, ultCresceu = Date.now();
    while (!ctx.parar() && !travado && !bfFimReal && voltas < 3000) {
      voltas++;
      try { window.scrollTo(0, document.documentElement.scrollHeight); } catch (e) {}
      try { if (cont && cont !== document.scrollingElement && cont !== document.documentElement) cont.scrollTop = cont.scrollHeight; } catch (e) {}
      await sleep(700);
      processar();
      if (travado) break;
      if (bfTickets.length > ultTotal) { ultTotal = bfTickets.length; ultCresceu = Date.now(); }
      else if (Date.now() - ultCresceu > 12000) break;   // 12s parado, sem fim real → desiste
    }
    await sleep(400);
    processar();   // consome a última leva (inclusive a página final com moreAvailable:false)
    console.log("[SharpenUp] Betfair: " + blocos.length + " bilhete(s) · bfTickets=" + bfTickets.length +
                " · hook=" + bfHookVivo + " · respostas=" + bfRespostas + " · fimReal=" + bfFimReal);
    return blocos;
  }

  // Modo passivo + REPLAY ATIVO (dado vem do pn_inject: exato, com id). A Pinnacle NÃO rola
  // uma lista infinita: cada busca /wager-filter devolve o resultado inteiro de UMA aba. Então
  // o robô não precisa rolar — ele pede ao pn_inject que RE-EMITA as duas abas (Decidido, na
  // janela de dias, + Não decidido, todas) e espera o fim (`pnFimReal`). Depois formata tudo.
  // A janela de dias corta só as ENCERRADAS antigas (as abertas não filtram por data e são
  // sempre atuais). Dedup/estado é por id → janela folgada é segura (o backend faz UPSERT).
  async function roboPinnaclePassive(ctx) {
    const blocos = [], usados = new Set();
    let travado = false;
    const N = Math.max(1, Math.round((Date.now() - ctx.cutoff) / 86400000));   // janela de dias do popup

    const processar = () => {
      for (const t of pnById.values()) {
        const cod = (t.id != null ? String(t.id) : "").toUpperCase();
        if (!cod || usados.has(cod)) continue;
        if (ctx.stopId && cod === ctx.stopId) { travado = true; return; }   // último já extraído
        usados.add(cod);
        // Janela de dias corta só ENCERRADAS (pela data do evento). Abertas nunca cortam.
        const dt = t.dataEvento ? Date.parse(t.dataEvento) : NaN;
        const passou = !t.aberta && !isNaN(dt) && dt < ctx.cutoff && dt > ctx.pisoSanidade;
        blocos.push(formatTicketPN(t));
        ctx.painel.contador.textContent = blocos.length + " bilhete" + (blocos.length === 1 ? "" : "s");
        if (passou) { travado = true; return; }   // passou da janela → para
      }
    };

    // Pede ao pn_inject o acumulado + arranca o replay das duas abas (com a janela de dias).
    try { window.postMessage({ __sharpenupPNReq: true, dias: N }, "*"); } catch (e) {}
    await sleep(400);
    processar();

    // Espera o replay terminar as duas abas (pnFimReal), consumindo o que for chegando.
    // NUNCA para no 1º obstáculo: só desiste por teto após muitos segundos parado sem fim.
    let voltas = 0, ultTotal = -1, ultCresceu = Date.now();
    while (!ctx.parar() && !travado && !pnFimReal && voltas < 600) {
      voltas++;
      await sleep(500);
      processar();
      if (travado) break;
      if (pnById.size > ultTotal) { ultTotal = pnById.size; ultCresceu = Date.now(); }
      else if (Date.now() - ultCresceu > 15000) break;   // 15s parado, sem fim real → desiste
    }
    await sleep(400);
    processar();   // consome o que chegou por último
    console.log("[SharpenUp] Pinnacle: " + blocos.length + " bilhete(s) · pnById=" + pnById.size +
                " · hook=" + pnHookVivo + " · respostas=" + pnRespostas + " · fimReal=" + pnFimReal);
    return blocos;
  }

  // ── Bet365 modo API (passivo + replay) ────────────────────────────────────────
  // Formata 1 bilhete lido do /sportshistoryapi (parseado pelo b3_inject) no bloco de texto que a
  // IA lê (marcador "[Código: BR…]" das outras casas passivas → o backend split/dedupa por ele).
  // Fiel à CASA_BET365 + docs/PLANO_BET365_CAPTURA_API.md:
  //   • Código = BR (comprovante; ESTÁVEL aberta→resolvida). Sem detalhe (BR não veio) → vazio.
  //   • Data = ENCERRAMENTO: maior kickoff das pernas + folga do esporte, convertido UK→Brasília.
  //   • Resultado: RT do summary vs stake → W/L/V (cashout ≠ retorno cheio → W). Aberta = sem.
  //   • Odd fracionária ("21/20") → decimal com precisão completa (21/20 = 2,05).
  //   • Múltiplo (3+ jogos diferentes) → sinaliza o tipo p/ a IA classificar (MASTER_ESPORTES).

  // CL → esporte (âncora; a IA/CASA_BET365 finaliza a localização). eSoccer vem com CL=1 → o
  // handle "(gamer)" entre parênteses é o sinal (a IA trata). CL=15/151 ainda desconhecidos.
  const _CL_B3 = { "1": "Futebol", "13": "Tênis", "18": "Basquete", "94": "Badminton" };
  // Folga kickoff→liquidação por esporte (horas) — só p/ acertar o DIA perto da meia-noite.
  const _OFF_B3 = { "1": 2.5, "18": 2.5, "13": 3, "94": 1.5 };

  // Odd Bet365: fracionária "num/den" → decimal (num/den + 1), precisão completa, vírgula.
  const _oddB3 = (frac) => {
    const s = String(frac || ""); const i = s.indexOf("/");
    if (i < 0) return "";
    const a = parseFloat(s.slice(0, i)), b = parseFloat(s.slice(i + 1));
    if (!isFinite(a) || !isFinite(b) || b === 0) return "";
    return String(a / b + 1).replace(".", ",");
  };
  const _numB3 = (s) => parseFloat(String(s == null ? "" : s).replace(",", ".")) || 0;

  // Reino Unido (Europe/London) → Brasília (UTC-3, sem horário de verão). BST (fim mar→fim out) =
  // UTC+1 → BR = UK-4; GMT = UTC+0 → BR = UK-3. Retorna a DATA de Brasília (já com a folga).
  function _ehBST(y, mo, d) {
    if (mo < 3 || mo > 10) return false;
    if (mo > 3 && mo < 10) return true;
    const ultimoDom = (yy, mm) => { const x = new Date(Date.UTC(yy, mm, 0)); return x.getUTCDate() - x.getUTCDay(); };
    return mo === 3 ? d >= ultimoDom(y, 3) : d < ultimoDom(y, 10);
  }
  function _dataFimB3(kickoffTS, offsetH) {
    const m = /^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})/.exec(String(kickoffTS || ""));
    if (!m) return "";
    const y = +m[1], mo = +m[2], d = +m[3], h = +m[4], mi = +m[5];
    const uk = Date.UTC(y, mo - 1, d, h, mi);                       // hora de parede UK como pseudo-UTC
    const ukToBr = _ehBST(y, mo, d) ? 4 : 3;
    const br = new Date(uk - (ukToBr - offsetH) * 3600000);
    const p = (n) => String(n).padStart(2, "0");
    return p(br.getUTCDate()) + "/" + p(br.getUTCMonth() + 1) + "/" + br.getUTCFullYear();
  }

  // Resultado bruto p/ a IA (RT do summary vs stake). Cashout ≠ retorno cheio → W (regra do MASTER).
  function _resultadoB3(t) {
    if (t.aberta || t.rt == null) return "em aberto (aguardando resultado — NÃO liquidar; sem resultado)";
    const st = _numB3(t.ts != null ? t.ts : t.stake), rt = _numB3(t.rt);
    if (rt === 0) return "Perdeu → L";
    if (Math.abs(rt - st) < 0.005) return "Devolvida/void (retorno = stake) → V";
    if (rt > st) return "Ganho → W (retorno R$ " + rt.toFixed(2).replace(".", ",") + ")";
    return "Ganho/perda parcial (retorno R$ " + rt.toFixed(2).replace(".", ",") + " · a conferir HW/HL)";
  }

  function formatTicketB3(t) {
    const L = [];
    L.push("[Código: " + (t.code || "") + "]");
    const legs = (t.legs && t.legs.length) ? t.legs : [];
    const cls = Array.from(new Set(legs.map((l) => l.cl).filter(Boolean)));
    const jogos = new Set(legs.map((l) => l.jogo).filter(Boolean));
    const multiplo = jogos.size >= 3 || cls.length > 1;
    // data de encerramento = maior kickoff+folga entre as pernas
    let dataFim = "", maxMs = -Infinity;
    for (const l of legs) {
      const off = _OFF_B3[l.cl] != null ? _OFF_B3[l.cl] : 2.5;
      const dd = _dataFimB3(l.kickoff, off);
      if (dd) { const p = dd.split("/"); const ms = Date.UTC(+p[2], +p[1] - 1, +p[0]); if (ms > maxMs) { maxMs = ms; dataFim = dd; } }
    }
    if (dataFim) L.push("Data (encerramento): " + dataFim);
    L.push("Stake: " + _brl(_numB3(t.ts != null ? t.ts : t.stake)));
    L.push("Status: " + _resultadoB3(t));
    if (!multiplo && t.oddFrac) L.push("Odd: " + _oddB3(t.oddFrac));
    if (multiplo) L.push("Tipo: Múltipla (" + legs.length + " seleções)");
    else if (cls.length) L.push("Esporte (casa): CL=" + cls[0] + (_CL_B3[cls[0]] ? " (" + _CL_B3[cls[0]] + ")" : ""));

    L.push("Seleções:");
    if (legs.length) {
      for (const l of legs) {
        const partes = [l.jogo, l.mercado, l.sel].filter(Boolean).join(" · ");
        L.push("  • " + partes + (l.oddFrac ? " @ " + _oddB3(l.oddFrac) : "") + (l.liga ? " · " + l.liga : ""));
      }
    } else if (t.sels && t.sels.length) {
      for (const s of t.sels) L.push("  • " + s.na + (s.od ? " @ " + _oddB3(s.od) : ""));   // só summary (detalhe não veio)
    }
    return L.join("\n");
  }

  // Modo passivo + REPLAY ATIVO (dado vem do b3_inject: exato, com código BR). Não rola lista: o
  // inject re-emite as duas listas (resolvidas na janela de dias + abertas todas) e busca o detalhe
  // de cada bilhete. O robô só espera o fim (`b3FimReal`) e formata. Dedup/estado por código → o
  // backend faz UPSERT (aberta→resolvida na mesma linha). Os detalhes chegam DEPOIS do summary, por
  // isso os blocos são reconstruídos do estado final ao terminar.
  async function roboBet365Passive(ctx) {
    let travado = false;
    const N = Math.max(1, Math.round((Date.now() - ctx.cutoff) / 86400000));

    const contar = () => {
      let n = 0;
      for (const t of b3ById.values()) {
        if (ctx.stopId && t.code && String(t.code).toUpperCase() === ctx.stopId) { travado = true; break; }
        n++;
      }
      ctx.painel.contador.textContent = n + " bilhete" + (n === 1 ? "" : "s");
    };

    // Pede ao b3_inject o acumulado + arranca o replay (janela de dias das resolvidas).
    b3Pedir(N);
    await sleep(500);
    contar();

    let voltas = 0, ultTotal = -1, ultCresceu = Date.now();
    while (!ctx.parar() && !travado && !b3FimReal && voltas < 900) {
      voltas++;
      await sleep(500);
      // Re-pede a cada ~5s enquanto nada chegou: o iframe de membros pode montar DEPOIS do
      // clique em "Copiar bilhetes" (ou o usuário navegar para o Histórico com o robô já
      // rodando) — um pedido único perderia esse frame para sempre.
      if (voltas % 10 === 0 && !b3ById.size) b3Pedir(N);
      contar();
      if (travado) break;
      if (b3ById.size > ultTotal) { ultTotal = b3ById.size; ultCresceu = Date.now(); }
      else if (Date.now() - ultCresceu > 20000) break;   // 20s parado, sem fim → desiste
    }
    await sleep(400);

    // Monta os blocos do ESTADO FINAL (os detalhes que chegaram por último já entraram).
    const blocos = [];
    for (const t of b3ById.values()) {
      if (ctx.stopId && t.code && String(t.code).toUpperCase() === ctx.stopId) break;   // até o já-exportado
      blocos.push(formatTicketB3(t));
    }
    console.log("[SharpenUp] Bet365 API: " + blocos.length + " bilhete(s) · b3ById=" + b3ById.size +
                " · hook=" + b3HookVivo + " · frames=" + b3PorFrame.size +
                " · respostas=" + b3Soma("respostas") + " · fimReal=" + b3FimReal);
    for (const [href, f] of b3PorFrame) {
      console.log("[SharpenUp] Bet365 frame " + (f.topo ? "TOPO" : "iframe") +
                  " · respostas=" + f.respostas + " · history=" + f.history + " · " + href.slice(0, 120));
    }
    return blocos;
  }

  // ── Bet365 modo DOM (fallback) ────────────────────────────────────────────────
  // Usado só quando a API /sportshistoryapi não trouxe nada (roboBet365Passive vazio).
  // A Bet365 não expõe ID nem data (nem no DOM, nem em JSON — o protocolo `Blob` é só
  // preço). MAS cada card (.myb-SettledBetItem) traz o texto COMPLETO no DOM mesmo
  // recolhido (só esconde via CSS) → o robô lê tudo sem clicar pra expandir. A lista é
  // virtualizada (~74 na tela), então rola p/ renderizar o resto.
  // DEDUP POR POSIÇÃO (não por texto): o mesmo card re-renderizado ao rolar fica na MESMA
  // posição do conteúdo → dedupado; dois bilhetes idênticos DE VERDADE (ex.: duas apostas
  // iguais no mesmo jogo) ocupam posições DIFERENTES → ambos mantidos (dedup por texto os
  // fundiria e perderia um bilhete real). A posição vira sobre re-render pq some da
  // virtualização? Se sim, o pior caso é re-coletar (contador infla, visível) — nunca
  // sumir bilhete (erro silencioso). Parada: MARCO (trecho do último exportado; para AO
  // reencontrar, sem incluir) OU TETO de N bilhetes (trava de custo).
  function acharScrollBet365() {
    const c = document.querySelector(".myb-MyBetsScroller");
    if (c && c.scrollHeight > c.clientHeight + 20) return c;
    return acharScroll();
  }
  async function roboBet365DOM(ctx) {
    const cont = acharScrollBet365();
    const vistos = new Set(), blocos = [];
    let travado = false;
    const norm = (s) => (s || "").replace(/\s+/g, " ").trim().toLowerCase();
    const marcoN = norm(ctx.marco);

    const coletar = () => {
      const contTop = esDoc(cont) ? 0 : cont.getBoundingClientRect().top;
      const contScroll = esDoc(cont) ? sTop(cont) : cont.scrollTop;
      for (const el of document.querySelectorAll(".myb-SettledBetItem")) {
        const txt = (el.innerText || "").trim();
        if (txt.length < 20) continue;
        // Posição no conteúdo virtual (estável entre re-renders): distingue o mesmo card
        // de dois bilhetes idênticos. Arredonda p/ absorver subpixels.
        const pos = Math.round(el.getBoundingClientRect().top - contTop + contScroll);
        if (vistos.has(pos)) continue;
        if (marcoN && norm(txt).includes(marcoN)) { travado = true; return; }   // último já exportado
        vistos.add(pos);
        blocos.push("[Bilhete Bet365]\n" + txt);
        ctx.painel.contador.textContent = blocos.length + " bilhete" + (blocos.length === 1 ? "" : "s");
        if (ctx.teto && blocos.length >= ctx.teto) { travado = true; return; }   // teto de segurança
      }
    };

    sTo(cont, 0); await sleep(500);
    // Rola do topo ao fim; ao encostar no fundo, gruda p/ a virtualização render mais e
    // espera. Desiste após 4 esperas sem crescer (nem bilhete novo, nem a lista aumentar).
    let voltas = 0, semNovidade = 0, ultTotal = 0, ultMax = -1;
    while (!ctx.parar() && !travado && voltas < 2000) {
      voltas++;
      coletar();
      if (travado) break;
      const top = sTop(cont), max = sMax(cont);
      const cresceu = blocos.length > ultTotal || max > ultMax + 4;
      ultTotal = blocos.length; ultMax = max;
      if (top >= max - 4) {                 // fundo atual → espera render de mais cards
        sTo(cont, max);
        if (cresceu) semNovidade = 0;
        else if (++semNovidade >= 4) { coletar(); break; }
        await sleep(650);
      } else {
        semNovidade = 0;
        sTo(cont, top + sClient(cont) * 0.85);
        await sleep(420);
      }
    }
    coletar();
    console.log("[SharpenUp] Bet365: " + blocos.length + " bilhete(s)");
    return blocos;
  }

  // Estratégia Superbet (fallback): cada card da lista (.bet-list-item__container) tem
  // o CÓDIGO no atributo `id` (exato, sem OCR). Simples já vêm inteiros; múltiplas
  // colapsam as pernas ("+N mais seleções") → o robô CLICA pra carregar o detalhe
  // completo e lê o texto mais rico (card expandido, selecionado ou painel da
  // direita — auto-descoberto). Para no stopId (copiar dele pra cima) ou na janela.
  async function roboSuperbet(ctx) {
    const cont = document.querySelector(".sb-my-bets__items") || acharScroll();
    const vistos = new Set(), blocos = [];
    let travado = false;
    const atualiza = () => ctx.painel.contador.textContent = blocos.length + " bilhete" + (blocos.length === 1 ? "" : "s");

    const proximoCard = () =>
      [...document.querySelectorAll(".bet-list-item__container")]
        .find((c) => c.id && !vistos.has(c.id.trim().toUpperCase()));

    const processarVisiveis = async () => {
      // Re-consulta o DOM a cada card: clicar/rolar troca a lista virtualizada.
      while (!ctx.parar() && !travado) {
        const card = proximoCard();
        if (!card) return;
        const codigo = card.id.trim().toUpperCase();
        if (ctx.stopId && codigo === ctx.stopId) { travado = true; return; }   // chegou no último já extraído
        vistos.add(codigo);

        // Data da janela: do cabeçalho do card (a Superbet ordena por ela).
        const baseText = card.innerText || "";
        const passou = parseDatas(baseText.toLowerCase())
          .some((ts) => ts < ctx.cutoff && ts > ctx.pisoSanidade);

        // SEMPRE clica p/ ler o DETALHE da direita — só ele traz TODAS as pernas, a
        // data por seleção, ODDS TOTAIS, STATUS/SACADO e o freebet. A lista da esquerda
        // é resumo (colapsa múltiplas e não tem data por perna). Fallback = card.
        let texto = baseText;
        try {
          (card.querySelector(".bet-list-item") || card).click();
          const rico = await esperarDetalhe(codigo);
          if (rico && rico.length > texto.length) texto = rico;
        } catch (_) {}

        texto = texto.trim();
        if (texto.length >= 10) { blocos.push("[Código: " + codigo + "]\n" + texto); atualiza(); }
        if (passou) { travado = true; return; }   // passou da janela de dias → para
      }
    };

    sTo(cont, 0); await sleep(500);
    // A Superbet carrega mais bilhetes (lazy-load) ao chegar no fim. NÃO paramos no
    // primeiro "fundo": ao encostar, grudamos no fim p/ disparar o loader e esperamos;
    // só desistimos após várias esperas SEM novidade (nem card novo, nem a página
    // crescer). Isso resolve o "pegou 10, depois 18" — a lista ainda estava crescendo.
    let voltas = 0, semNovidade = 0, ultTotal = 0, ultMax = -1;
    while (!ctx.parar() && !travado && voltas < 2000) {
      voltas++;
      await processarVisiveis();
      if (travado) break;
      const top = sTop(cont), max = sMax(cont);
      const cresceu = blocos.length > ultTotal || max > ultMax + 4;
      ultTotal = blocos.length; ultMax = max;
      if (top >= max - 4) {                 // no fundo atual → espera o lazy-load
        sTo(cont, max);                     // gruda no fim p/ disparar o carregamento
        if (cresceu) semNovidade = 0;
        else if (++semNovidade >= 4) { await processarVisiveis(); break; }
        await sleep(650);
      } else {
        semNovidade = 0;
        sTo(cont, top + sClient(cont) * 0.85);
        await sleep(420);
      }
    }
    return blocos;
  }

  // Após clicar um bilhete, espera o painel de DETALHE carregar e devolve seu texto.
  // O detalhe é a MENOR div que contém, juntos: o código + "ODDS TOTAIS" + um marcador
  // de resultado (STATUS/PRÊMIO/SACADO/Ganhou/Perdido/Reembolso) — isso isola o painel
  // da direita (com todas as pernas E a data por seleção), sem pegar a página toda.
  // Também considera o card selecionado como candidato. Rejeita "+N mais seleções" e
  // devolve o texto mais rico (o que tem as datas por perna costuma ser o maior).
  // Rodapé do painel = código + ODDS TOTAIS + resultado (financeiro).
  const _MARC = /(status|pr[êe]mio|sacado|ganhou|perdido|reembols|devolvid)/i;
  // Pernas/seleções (só no painel de detalhe, não no rodapé): data por seleção (dia
  // da semana) OU nome de mercado. É o sinal p/ saber que subimos até incluir as pernas.
  const _PERNA = /(seg|ter|qua|qui|sex|s[áa]b|dom)[a-z]*\.?\s*\d{1,2}|total de|menos de|mais de|resultado final|handicap|jogador\b|1[ºo]? tempo|2[ºo]? tempo|ambas|escanteios|cart[õo]es|impedimento|finaliza|chutes|gols|faltas|desarme/i;
  function limparPainel(txt) {
    return txt.split("\n").filter((l) => {
      const s = l.trim();
      if (!s) return false;
      if (/interaja com a comunidade|inspire outros jogadores|entrar no supersocial/i.test(s)) return false;
      if (/^mozilla\/5\.0/i.test(s)) return false;
      if (/^[a-f0-9]{8}-[a-f0-9]{4}-/i.test(s)) return false;   // hash tipo uuid
      if (/^[a-f0-9]{24,}$/i.test(s)) return false;             // hash longo
      return true;
    }).join("\n").trim();
  }
  async function esperarDetalhe(codigo) {
    for (let i = 0; i < 14; i++) {
      await sleep(150);
      // Rodapé: MENOR div com código + ODDS TOTAIS + resultado (isola o painel certo).
      const foot = [...document.querySelectorAll("div")].filter((d) => {
        const t = d.textContent || "";
        return t.includes(codigo) && /odds totais/i.test(t) && _MARC.test(t);
      }).sort((a, b) => (a.textContent || "").length - (b.textContent || "").length)[0];
      if (!foot) continue;
      // Sobe do rodapé até o container que TAMBÉM tem as pernas (o painel completo).
      let el = foot, alvo = foot;
      for (let k = 0; k < 10 && el.parentElement; k++) {
        el = el.parentElement;
        if (_PERNA.test(el.textContent || "")) { alvo = el; break; }
      }
      const txt = limparPainel(alvo.innerText || "");
      if (txt && !/mais sele/i.test(txt) && txt.includes(codigo)) return txt;
    }
    return null;
  }

  function criarPainelRobo() {
    const p = document.createElement("div");
    S(p, { position: "fixed", bottom: "24px", left: "50%", transform: "translateX(-50%)",
      "z-index": "2147483647", display: "inline-flex", "align-items": "center", gap: "12px",
      background: "#0E1524", border: "1px solid rgba(46,139,255,0.5)", "border-radius": "12px",
      padding: "10px 12px 10px 14px", color: "#E6ECF5", font: "13px/1 system-ui,sans-serif",
      "box-shadow": "0 12px 40px rgba(0,0,0,.55)", "user-select": "none" });
    p.innerHTML = bladeSVG(9, 20) +
      '<span style="margin-left:2px">Coletando bilhetes… <b id="su-robo-n" style="font-family:ui-monospace,monospace;color:#7FB2FF">0 bilhetes</b></span>';
    const btn = document.createElement("button");
    btn.textContent = "Parar";
    S(btn, { background: "transparent", color: "#9AA6B6", border: "1px solid rgba(255,255,255,.12)",
      "border-radius": "7px", padding: "6px 12px", cursor: "pointer", font: "inherit", "font-weight": "600" });
    p.appendChild(btn);
    document.documentElement.appendChild(p);
    return { remove: () => p.remove(), contador: p.querySelector("#su-robo-n"), btnParar: btn };
  }

  function toastLocal(texto, ok) {
    const t = document.createElement("div");
    t.textContent = texto;
    S(t, { position: "fixed", bottom: "24px", left: "50%", transform: "translateX(-50%)",
      "z-index": "2147483647", font: "13px/1.4 system-ui,sans-serif", color: "#fff",
      background: ok ? "#1B7F4E" : "#B3363B", padding: "10px 16px", "border-radius": "10px",
      "box-shadow": "0 8px 24px rgba(0,0,0,.35)" });
    document.documentElement.appendChild(t);
    setTimeout(() => t.remove(), 2600);
  }

  // ── Orquestração ────────────────────────────────────────────────────────────
  async function sync() {
    let st; try { st = await get(); } catch (_) { return; }
    if (!st.token) { removeFab(); removeFrame(); removeDraw(); return; }
    if (st.modo === "texto") { removeFrame(); removeDraw(); ensureFab("texto"); return; }
    // modo print
    if (st.frameAtivo) {
      removeFab();
      if (st.frameRect) { removeDraw(); ensureFrame(st.frameRect, st.frameCount || 0); }
      else { removeFrame(); ensureDraw(); }
    } else { removeFrame(); removeDraw(); ensureFab("print"); }
  }

  chrome.storage.onChanged.addListener((ch, area) => {
    if (area !== "local") return;
    if ("frameCount" in ch && frame && !("frameAtivo" in ch) && !("frameRect" in ch)) { atualizarContador(ch.frameCount.newValue); return; }
    if ("token" in ch || "modo" in ch || "frameAtivo" in ch || "frameRect" in ch) sync();
  });
  chrome.runtime.onMessage.addListener((msg) => {
    if (!msg) return;
    if (msg.type === "CAPTURA_FIM") fimCaptura(!!msg.ok);
    else if (msg.type === "START_ROBOT") iniciarRobo();
  });

  sync();
})();
