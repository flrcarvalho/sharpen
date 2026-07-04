// SharpenUp — content script (todas as casas). Gerencia o botão flutuante (FAB) e
// a MOLDURA FIXA de captura:
//   FAB (aparece com pareamento em modo print) → clica → desenha a região 1x →
//   a moldura fica fixa com um botão SNAP na borda; interior clicável/rolável.
//   Cada Snap tira o print daquela região e envia. Rola / troca de página / troca
//   a bet → Snap de novo, sem re-desenhar nem reconectar. ✕ fecha o modo.
// A moldura persiste (posição+tamanho) em chrome.storage → sobrevive à navegação.
// Estilos via setProperty('...','important') pra não apanhar do CSS da casa.
(() => {
  if (window.__sharpenupCS) return;
  window.__sharpenupCS = true;

  const AZUL = "#2E8BFF", VERDE = "#2BC07E", Z = "2147483646";
  let fab = null, frame = null, box = null, toolbar = null, handle = null,
      drawRoot = null, capturando = false, safety = null, rectAtual = null;

  const S = (el, m) => { for (const k in m) el.style.setProperty(k, m[k], "important"); };
  const get = () => chrome.storage.local.get(["token", "modo", "frameAtivo", "frameRect", "frameCount"]);

  function bladeSVG(w, h) {
    return '<svg viewBox="40 10 40 100" width="' + w + '" height="' + h + '" style="pointer-events:none">' +
      '<defs><linearGradient id="sharpenupBladeGrad" x1="60" y1="16" x2="60" y2="104" gradientUnits="userSpaceOnUse">' +
      '<stop offset="0" stop-color="#5BA9FF"></stop><stop offset="1" stop-color="#1E7CF0"></stop></linearGradient></defs>' +
      '<path d="M60 16 L60 90 L42 104 Z" fill="url(#sharpenupBladeGrad)"></path>' +
      '<path d="M60 16 L78 104 L60 90 Z" fill="#333B45"></path></svg>';
  }

  // ── FAB ─────────────────────────────────────────────────────────────────────
  function ensureFab() {
    if (fab) return;
    fab = document.createElement("div");
    fab.setAttribute("aria-label", "SharpenUp — capturar");
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
      if (!mv) chrome.storage.local.set({ frameAtivo: true, frameCount: 0 });
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

  // ── Desenho da região (1ª vez) ──────────────────────────────────────────────
  function ensureDraw() {
    if (drawRoot) return;
    let dsx = 0, dsy = 0, drawing = false, ok = false;
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
      ok = true;
      chrome.storage.local.set({ frameRect: { left: r.left, top: r.top, width: r.width, height: r.height } });
    });
    const onKey = (e) => { if (e.key === "Escape") { chrome.storage.local.set({ frameAtivo: false }); } };
    document.addEventListener("keydown", onKey, true);
    drawRoot._cleanup = () => document.removeEventListener("keydown", onKey, true);
    document.documentElement.appendChild(drawRoot);
  }
  function removeDraw() { if (drawRoot) { if (drawRoot._cleanup) drawRoot._cleanup(); drawRoot.remove(); drawRoot = null; } }

  // ── Moldura fixa (persistente) ──────────────────────────────────────────────
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

    // Barra de controle (arrastável) — a única parte que captura o mouse.
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

    // Alça de redimensionar (canto inferior direito).
    handle = document.createElement("div");
    S(handle, { position: "fixed", width: "16px", height: "16px", background: AZUL,
      border: "2px solid #0B0E13", "border-radius": "4px", "pointer-events": "auto",
      cursor: "nwse-resize", "z-index": Z });
    frame.appendChild(handle);

    snap.addEventListener("click", dispararSnap);
    redraw.addEventListener("click", () => chrome.storage.local.remove("frameRect"));
    fechar.addEventListener("click", () => chrome.storage.local.set({ frameAtivo: false }));
    [snap, redraw, fechar].forEach((b) => b.addEventListener("pointerdown", (e) => e.stopPropagation()));

    arrastarBarra();
    redimensionar();

    document.documentElement.appendChild(frame);
    atualizarContador(count);
    reposicionar();
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
      S(toolbar, { cursor: "grabbing" }); try { toolbar.setPointerCapture(e.pointerId); } catch (_) {}
      e.preventDefault();
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
    S(frame, { visibility: "hidden" });   // some do print
    requestAnimationFrame(() => requestAnimationFrame(() => {
      chrome.runtime.sendMessage({ type: "CAPTURAR_REGIAO",
        rect: { x: rectAtual.left, y: rectAtual.top, width: rectAtual.width, height: rectAtual.height },
        vw: innerWidth, vh: innerHeight });
    }));
    clearTimeout(safety);
    safety = setTimeout(() => fimCaptura(false), 6000);   // trava de segurança
  }

  function fimCaptura(ok) {
    clearTimeout(safety); capturando = false;
    if (frame) S(frame, { visibility: "visible" });
    if (ok) {
      chrome.storage.local.get("frameCount").then(({ frameCount }) => {
        chrome.storage.local.set({ frameCount: (frameCount || 0) + 1 });
      });
      if (box) { S(box, { "border-color": VERDE }); setTimeout(() => box && S(box, { "border-color": AZUL }), 350); }
    }
  }

  function removeFrame() {
    if (frame) { frame.remove(); frame = box = toolbar = handle = null; }
    capturando = false; clearTimeout(safety);
  }

  // ── Orquestração ────────────────────────────────────────────────────────────
  async function sync() {
    let st; try { st = await get(); } catch (_) { return; }
    const ok = !!st.token && st.modo === "print";
    if (!ok) { removeFab(); removeFrame(); removeDraw(); return; }
    if (st.frameAtivo) {
      removeFab();
      if (st.frameRect) { removeDraw(); ensureFrame(st.frameRect, st.frameCount || 0); }
      else { removeFrame(); ensureDraw(); }
    } else {
      removeFrame(); removeDraw(); ensureFab();
    }
  }

  chrome.storage.onChanged.addListener((ch, area) => {
    if (area !== "local") return;
    if ("frameCount" in ch && frame && !("frameAtivo" in ch) && !("frameRect" in ch)) {
      atualizarContador(ch.frameCount.newValue); return;
    }
    if ("token" in ch || "modo" in ch || "frameAtivo" in ch || "frameRect" in ch) sync();
  });
  chrome.runtime.onMessage.addListener((msg) => {
    if (msg && msg.type === "CAPTURA_FIM") fimCaptura(!!msg.ok);
  });

  sync();
})();
