// Popup SharpenUp: parear (trocar código por token), mostrar estado, disparar captura.
const $ = (id) => document.getElementById(id);

const telaConectar = $("tela-conectar");
const telaConectado = $("tela-conectado");
const msg = $("msg");

// Domínio da casa p/ o favicon (grayscale, cosmético — some se não carregar).
const DOMINIOS = {
  "Superbet": "superbet.com", "Betano": "betano.com", "Bet365": "bet365.com",
  "Betfair": "betfair.com", "KTO": "kto.com", "Pinnacle": "pinnacle.com",
  "Betnacional": "betnacional.com", "Lottu": "lottu.com", "Vitória Bet": "vitoriabet.com",
  "BETesporte": "betesporte.bet.br",
};

function setMsg(texto, tipo) {
  msg.textContent = texto || "";
  msg.className = "msg" + (tipo ? " " + tipo : "");
}

function setStatusPill(online) {
  $("status-pill").className = "status " + (online ? "on" : "off");
  $("status-txt").textContent = online ? "online" : "offline";
}

// Formata o código: MAIÚSCULO + hífen automático (ABCD-EFGH).
$("codigo").addEventListener("input", (e) => {
  let v = e.target.value.toUpperCase().replace(/[^A-Z0-9]/g, "").slice(0, 8);
  if (v.length > 4) v = v.slice(0, 4) + "-" + v.slice(4);
  e.target.value = v;
});
$("codigo").addEventListener("keydown", (e) => { if (e.key === "Enter") conectar(); });

$("lookback").addEventListener("change", (e) => {
  const n = Math.max(1, Math.min(365, Number(e.target.value) || 30));
  e.target.value = n;
  chrome.storage.local.set({ lookbackDias: n });
});
$("stopid").addEventListener("input", (e) => {
  const v = e.target.value.trim().toUpperCase();
  e.target.value = v;
  chrome.storage.local.set({ stopId: v });
});
// Bet365: marco (texto livre — mantém acento/maiúsc.) + teto de bilhetes.
$("b365-marco").addEventListener("input", (e) => {
  chrome.storage.local.set({ b365Marco: e.target.value });
});
$("b365-teto").addEventListener("change", (e) => {
  const n = Math.max(0, Math.min(500, Number(e.target.value) || 0));
  e.target.value = n || "";
  chrome.storage.local.set({ b365Teto: n });
});

$("btn-conectar").addEventListener("click", conectar);
$("btn-desconectar").addEventListener("click", desconectar);
$("btn-capturar").addEventListener("click", capturar);

async function conectar() {
  const codigo = $("codigo").value.trim().toUpperCase();
  if (codigo.replace(/[^A-Z0-9]/g, "").length < 8) {
    setMsg("Digite o código completo (ABCD-EFGH).", "erro");
    return;
  }
  setMsg("Conectando…", "info");
  try {
    const base = await getApiBase();
    const r = await fetch(`${base}/captura/conectar`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ codigo }),
    });
    if (r.status === 404) { setMsg("Código inválido ou expirado. Gere outro no dashboard.", "erro"); return; }
    if (!r.ok) { setMsg("Erro ao conectar (" + r.status + ").", "erro"); return; }
    const d = await r.json();
    await chrome.storage.local.set({
      token: d.token, casa: d.casa, parceiro: d.parceiro,
      modo: d.modo, dono: d.dono, codigo,
    });
    await chrome.storage.local.remove("lastError");
    setMsg("", "");
    render();
  } catch (e) {
    setMsg("Falha de rede. Confira a URL do servidor.", "erro");
  }
}

async function desconectar() {
  await chrome.storage.local.remove(["token", "casa", "parceiro", "modo", "dono", "codigo"]);
  $("codigo").value = "";
  setMsg("", "");
  render();
}

async function capturar() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab || /^(chrome|edge|about|chrome-extension):/.test(tab.url || "")) {
      setMsg("Abra a página da casa antes de capturar.", "erro");
      return;
    }
    // Garante o content script presente (abas abertas antes de instalar não o têm).
    try { await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ["content.js"] }); } catch (_) {}
    const { modo, casa } = await chrome.storage.local.get(["modo", "casa"]);
    if (modo === "texto") {
      // Interceptor de API no mundo MAIN (be/sb_inject): o content_script declarativo só
      // roda em page LOAD. Se a aba já estava aberta antes de recarregar a extensão, injeta
      // agora (idempotente — guarda interna). Sem isso o robô roda mas capta zero.
      const inj = casa === "BETesporte" ? "be_inject.js"
                : casa === "Superbet" ? "sb_inject.js"
                : casa === "Betano" ? "bn_inject.js" : null;
      if (inj) { try { await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: [inj], world: "MAIN" }); } catch (_) {} }
      // Dispara o robô (rola/pagina + colhe + envia texto).
      try { await chrome.tabs.sendMessage(tab.id, { type: "START_ROBOT" }); } catch (_) {}
    } else {
      // Print: liga o modo moldura — desenhar 1x → Snap várias vezes.
      await chrome.storage.local.set({ frameAtivo: true, frameCount: 0 });
    }
    window.close();
  } catch (e) {
    setMsg("Não foi possível abrir a captura nesta página.", "erro");
  }
}

// Re-renderiza quando o estado de conexão muda no storage (ex.: o background
// remove o token ao expirar a sessão → o popup sai de "Conectado" na hora, sem
// ficar mostrando estado velho). Não re-renderiza em writes de lookback/stopId.
chrome.storage.onChanged.addListener((ch, area) => {
  if (area === "local" && ("token" in ch || "casa" in ch || "modo" in ch || "lastError" in ch)) render();
});

async function render() {
  const st = await chrome.storage.local.get(["token", "casa", "parceiro", "modo", "lastError"]);
  if (st.token) {
    telaConectar.hidden = true;
    telaConectado.hidden = false;
    setMsg("", "");                 // conectado é auto-explicativo; sem erro velho
    setStatusPill(true);
    $("c-casa").textContent = st.casa || "—";
    $("c-parceiro").textContent = st.parceiro || "—";
    const dom = DOMINIOS[st.casa];
    const fav = $("c-favicon");
    if (dom) { fav.style.display = ""; fav.src = `https://icons.duckduckgo.com/ip3/${dom}.ico`; }
    else { fav.style.display = "none"; }
    const texto = st.modo === "texto";
    // Bet365 usa marco + teto (sem data/ID); Betano/Superbet usam janela de dias + ID.
    const isBet365 = texto && st.casa === "Bet365";
    const isBetSup = texto && !isBet365;
    $("nota-texto").hidden = !texto;
    $("janela-wrap").hidden = !isBetSup;
    $("stopid-wrap").hidden = !isBetSup;
    $("b365-marco-wrap").hidden = !isBet365;
    $("b365-teto-wrap").hidden = !isBet365;
    $("btn-capturar").hidden = false;   // vale nos dois modos
    $("cap-label").textContent = texto ? "Copiar bilhetes" : "Capturar";
    if (isBetSup) {
      const cfg = await chrome.storage.local.get(["lookbackDias", "stopId"]);
      $("lookback").value = cfg.lookbackDias || 30;
      $("stopid").value = cfg.stopId || "";
    } else if (isBet365) {
      const cfg = await chrome.storage.local.get(["b365Marco", "b365Teto"]);
      $("b365-marco").value = cfg.b365Marco || "";
      $("b365-teto").value = cfg.b365Teto || "";
    }
  } else {
    telaConectar.hidden = false;
    telaConectado.hidden = true;
    setStatusPill(false);
    if (st.lastError) setMsg(st.lastError, "erro");
  }
}

render();
