// Botão flutuante SharpenUp (content script em todas as casas). Aparece quando há
// pareamento ativo em modo print; clique abre a moldura de captura. Some durante o
// print pra não entrar na foto. Estilos via .style.setProperty (não bate no CSP da
// casa); anel de hover via inline. Compartilha o mundo isolado com overlay.js.
(() => {
  if (window.__sharpenupFab) return;
  window.__sharpenupFab = true;

  const AZUL = "#2E8BFF";
  let fab = null, ring = null, arrastando = false, moveu = false;
  let sx = 0, sy = 0, ox = 0, oy = 0;

  function estilo(el, m) { for (const k in m) el.style.setProperty(k, m[k]); }

  function construir() {
    if (fab) return;
    fab = document.createElement("div");
    fab.setAttribute("aria-label", "SharpenUp — capturar");
    estilo(fab, {
      position: "fixed", right: "22px", bottom: "22px", width: "52px", height: "52px",
      "border-radius": "50%", background: "linear-gradient(160deg,#161C24,#0B0E13)",
      border: "1px solid rgba(255,255,255,0.10)", display: "grid", "place-items": "center",
      cursor: "grab", "box-shadow": "0 8px 22px rgba(0,0,0,.5)", "z-index": "2147483646",
      opacity: "0.62", transition: "opacity .18s, transform .18s, box-shadow .18s, border-color .18s",
      "touch-action": "none", "user-select": "none",
    });
    fab.innerHTML =
      '<svg viewBox="40 10 40 100" width="13" height="29" style="pointer-events:none">' +
      '<defs><linearGradient id="suBladeGrad" x1="60" y1="16" x2="60" y2="104" gradientUnits="userSpaceOnUse">' +
      '<stop offset="0" stop-color="#5BA9FF"></stop><stop offset="1" stop-color="#1E7CF0"></stop></linearGradient></defs>' +
      '<path d="M60 16 L60 90 L42 104 Z" fill="url(#suBladeGrad)"></path>' +
      '<path d="M60 16 L78 104 L60 90 Z" fill="#333B45"></path></svg>';

    const pin = document.createElement("span");
    estilo(pin, {
      position: "absolute", right: "-4px", top: "-4px", width: "16px", height: "16px",
      "border-radius": "50%", background: AZUL, border: "2px solid #0B0E13",
      "box-shadow": "0 0 8px rgba(46,139,255,.7)", display: "grid", "place-items": "center",
      "pointer-events": "none",
    });
    pin.innerHTML =
      '<svg viewBox="0 0 24 24" width="9" height="9" fill="none" stroke="#04101F" stroke-width="3.4" ' +
      'stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5M6 11l6-6 6 6"></path></svg>';
    fab.appendChild(pin);

    fab.addEventListener("pointerenter", () => { if (!arrastando) hover(true); });
    fab.addEventListener("pointerleave", () => { if (!arrastando) hover(false); });
    fab.addEventListener("pointerdown", onDown);
    fab.addEventListener("pointermove", onMove);
    fab.addEventListener("pointerup", onUp);

    document.documentElement.appendChild(fab);
    restaurarPos();
  }

  function hover(on) {
    if (!fab) return;
    fab.style.setProperty("opacity", on ? "1" : "0.62");
    fab.style.setProperty("transform", on ? "scale(1.08)" : "none");
    fab.style.setProperty("border-color", on ? "rgba(46,139,255,0.55)" : "rgba(255,255,255,0.10)");
    fab.style.setProperty("box-shadow", on
      ? "0 10px 30px rgba(0,0,0,.55),0 0 0 4px rgba(46,139,255,.14)"
      : "0 8px 22px rgba(0,0,0,.5)");
  }

  function onDown(e) {
    arrastando = true; moveu = false; fab.style.setProperty("cursor", "grabbing");
    const r = fab.getBoundingClientRect();
    ox = r.left; oy = r.top; sx = e.clientX; sy = e.clientY;
    try { fab.setPointerCapture(e.pointerId); } catch (_) {}
  }
  function onMove(e) {
    if (!arrastando) return;
    const dx = e.clientX - sx, dy = e.clientY - sy;
    if (Math.abs(dx) > 2 || Math.abs(dy) > 2) moveu = true;
    colocar(ox + dx, oy + dy);
  }
  function onUp() {
    if (!arrastando) return;
    arrastando = false; fab.style.setProperty("cursor", "grab");
    const r = fab.getBoundingClientRect();
    try { chrome.storage.local.set({ fabPos: { left: r.left, top: r.top } }); } catch (_) {}
    if (!moveu) abrirCaptura();
  }

  function colocar(x, y) {
    const w = fab.offsetWidth, h = fab.offsetHeight;
    x = Math.max(6, Math.min(x, window.innerWidth - w - 6));
    y = Math.max(6, Math.min(y, window.innerHeight - h - 6));
    estilo(fab, { left: x + "px", top: y + "px", right: "auto", bottom: "auto" });
  }
  async function restaurarPos() {
    try {
      const { fabPos } = await chrome.storage.local.get("fabPos");
      if (fabPos) colocar(fabPos.left, fabPos.top);
    } catch (_) {}
  }

  function abrirCaptura() {
    esconder();                       // some antes do print
    chrome.runtime.sendMessage({ type: "ABRIR_OVERLAY" });
  }
  function esconder() { if (fab) fab.style.setProperty("display", "none"); }
  function mostrar() { if (fab) fab.style.setProperty("display", "grid"); }
  function remover() { if (fab) { fab.remove(); fab = null; } }

  // Overlay abriu (por FAB ou popup) → some; cancelou → volta.
  window.addEventListener("sharpenup:overlay-open", esconder);
  window.addEventListener("sharpenup:overlay-cancel", mostrar);
  // Background avisa o fim da captura (ok/erro) → volta o FAB.
  chrome.runtime.onMessage.addListener((msg) => {
    if (msg && msg.type === "FAB_ESTADO" && msg.estado === "idle") mostrar();
  });

  // Mostra/esconde conforme o pareamento (token + modo print).
  async function sincronizar() {
    let st = {};
    try { st = await chrome.storage.local.get(["token", "modo"]); } catch (_) { return; }
    const ativo = !!st.token && st.modo === "print";
    if (ativo) { construir(); mostrar(); } else { remover(); }
  }
  chrome.storage.onChanged.addListener((ch, area) => {
    if (area === "local" && ("token" in ch || "modo" in ch)) sincronizar();
  });
  sincronizar();
})();
