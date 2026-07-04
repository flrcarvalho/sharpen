// Overlay de seleção de região (injetado na aba ativa pelo popup). Arraste para
// desenhar a moldura sobre o bilhete; Capturar → manda a região para o background.
// Estilos aplicados via .style.setProperty (não via <style>) para não esbarrar no
// CSP da casa. Guarda contra dupla injeção.
(() => {
  if (window.__sharpenOverlayAtivo) return;
  window.__sharpenOverlayAtivo = true;

  const AZUL = "#2E8BFF";
  const dpr = window.devicePixelRatio || 1;
  let sx = 0, sy = 0, desenhando = false, temBox = false;

  const root = document.createElement("div");
  aplicar(root, {
    position: "fixed", inset: "0", "z-index": "2147483647",
    cursor: "crosshair", background: "rgba(10,15,25,0.28)", "user-select": "none",
  });

  const box = document.createElement("div");
  aplicar(box, {
    position: "fixed", border: "2px solid " + AZUL,
    "box-shadow": "0 0 0 9999px rgba(10,15,25,0.45)",
    display: "none", "pointer-events": "none", "border-radius": "2px",
  });
  root.appendChild(box);

  const dica = document.createElement("div");
  dica.textContent = "Arraste para selecionar o bilhete · Esc cancela";
  aplicar(dica, {
    position: "fixed", top: "16px", left: "50%", transform: "translateX(-50%)",
    background: "#0E1524", color: "#E6ECF5",
    font: "13px/1.4 system-ui, -apple-system, sans-serif",
    padding: "8px 14px", "border-radius": "8px",
    border: "1px solid rgba(46,139,255,0.55)", "pointer-events": "none",
  });
  root.appendChild(dica);

  const bar = document.createElement("div");
  aplicar(bar, {
    position: "fixed", display: "none", gap: "8px", "z-index": "2147483647",
  });
  const btnCap = botao("Capturar", true);
  const btnCancel = botao("Cancelar", false);
  bar.appendChild(btnCap);
  bar.appendChild(btnCancel);
  root.appendChild(bar);

  document.documentElement.appendChild(root);

  // ── Desenho da moldura ──────────────────────────────────────────────────────
  root.addEventListener("mousedown", (e) => {
    if (e.button !== 0) return;
    if (e.target === btnCap || e.target === btnCancel) return;
    desenhando = true; temBox = false;
    bar.style.display = "none";
    sx = e.clientX; sy = e.clientY;
    posicionar(sx, sy, 0, 0);
    box.style.display = "block";
    e.preventDefault();
  });

  root.addEventListener("mousemove", (e) => {
    if (!desenhando) return;
    const x = Math.min(sx, e.clientX), y = Math.min(sy, e.clientY);
    posicionar(x, y, Math.abs(e.clientX - sx), Math.abs(e.clientY - sy));
  });

  root.addEventListener("mouseup", (e) => {
    if (!desenhando) return;
    desenhando = false;
    const r = box.getBoundingClientRect();
    if (r.width < 8 || r.height < 8) { box.style.display = "none"; return; }
    temBox = true;
    dica.style.display = "none";
    // Barra logo abaixo da moldura (ou acima, se não couber).
    let top = r.bottom + 10;
    if (top > window.innerHeight - 44) top = Math.max(10, r.top - 44);
    bar.style.left = Math.max(10, r.left) + "px";
    bar.style.top = top + "px";
    bar.style.display = "flex";
  });

  btnCap.addEventListener("mousedown", (e) => e.stopPropagation());
  btnCancel.addEventListener("mousedown", (e) => e.stopPropagation());
  btnCap.addEventListener("click", capturar);
  btnCancel.addEventListener("click", fechar);

  const onKey = (e) => { if (e.key === "Escape") fechar(); };
  document.addEventListener("keydown", onKey, true);

  function capturar() {
    if (!temBox) return;
    const r = box.getBoundingClientRect();
    const rect = { x: r.left, y: r.top, width: r.width, height: r.height };
    // Some com o overlay ANTES de mandar, senão ele entra no print. Dois rAF
    // garantem que o navegador repintou sem a moldura antes do captureVisibleTab.
    limpar();
    requestAnimationFrame(() => requestAnimationFrame(() => {
      chrome.runtime.sendMessage({ type: "CAPTURAR_REGIAO", rect, dpr });
    }));
  }

  function fechar() { limpar(); }

  function limpar() {
    document.removeEventListener("keydown", onKey, true);
    root.remove();
    window.__sharpenOverlayAtivo = false;
  }

  function posicionar(x, y, w, h) {
    box.style.left = x + "px"; box.style.top = y + "px";
    box.style.width = w + "px"; box.style.height = h + "px";
  }

  function botao(texto, primario) {
    const el = document.createElement("button");
    el.textContent = texto;
    aplicar(el, {
      font: "13px/1 system-ui, -apple-system, sans-serif", "font-weight": "600",
      padding: "9px 16px", "border-radius": "8px", cursor: "pointer",
      border: primario ? "none" : "1px solid rgba(230,236,245,0.35)",
      color: primario ? "#08111F" : "#E6ECF5",
      background: primario ? AZUL : "rgba(14,21,36,0.92)",
      "pointer-events": "auto",
      "box-shadow": "0 4px 14px rgba(0,0,0,.3)",
    });
    return el;
  }

  function aplicar(el, estilos) {
    for (const k in estilos) el.style.setProperty(k, estilos[k]);
  }
})();
