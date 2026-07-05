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
    const cfg = await chrome.storage.local.get(["lookbackDias", "casa", "stopId"]);
    const N = Math.max(1, Number(cfg.lookbackDias) || 30);
    const cutoff = Date.now() - N * 86400000;
    const pisoSanidade = cutoff - 730 * 86400000;
    const ctx = {
      cutoff, pisoSanidade,
      stopId: (cfg.stopId || "").trim().toUpperCase(),
      parar: () => parar,
      painel,
    };

    let blocos;
    if ((cfg.casa || "").toLowerCase() === "superbet") blocos = await roboSuperbet(ctx);
    else blocos = await roboScroll(ctx);   // Betano + genéricos

    painel.remove();
    roboRodando = false;
    if (!blocos.length) { toastLocal("Nada coletado — rolagem/estrutura não reconhecida.", false); return; }
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

  // Estratégia Superbet: cada card da lista (.bet-list-item__container) tem o
  // CÓDIGO no atributo `id` (exato, sem OCR). Simples já vêm inteiros; múltiplas
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

        let texto = card.innerText || "";
        const datas = parseDatas(texto.toLowerCase());
        const passou = datas.some((ts) => ts < ctx.cutoff && ts > ctx.pisoSanidade);

        if (/mais sele/i.test(texto)) {   // múltipla colapsada → clica p/ o detalhe completo
          try {
            (card.querySelector(".bet-list-item") || card).click();
            const rico = await esperarDetalhe(codigo, texto.length);
            if (rico) texto = rico;
          } catch (_) {}
        }
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

  // Após clicar um bilhete, espera e devolve o texto mais completo do detalhe —
  // procura no card selecionado E no painel da direita (elemento fora da lista que
  // contém o código). Rejeita textos que ainda mostram "mais seleções".
  async function esperarDetalhe(codigo, minLen) {
    const scroller = document.querySelector(".sb-my-bets__items");
    for (let i = 0; i < 9; i++) {
      await sleep(170);
      const cands = [];
      const sel = document.querySelector(".bet-list-item--selected");
      if (sel) cands.push(sel.innerText || "");
      // painel da direita: div fora da lista, contendo o código, com cara de detalhe
      const fora = [...document.querySelectorAll("div")].filter(
        (d) => (!scroller || !scroller.contains(d)) && d.textContent
          && d.textContent.includes(codigo) && /odds totais|status|@/i.test(d.textContent));
      fora.sort((a, b) => (a.innerText || "").length - (b.innerText || "").length);
      if (fora[0]) cands.push(fora[0].innerText || "");
      const bons = cands.map((t) => t.trim())
        .filter((t) => t && !/mais sele/i.test(t) && t.length > minLen * 0.8);
      if (bons.length) { bons.sort((a, b) => b.length - a.length); return bons[0]; }
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
