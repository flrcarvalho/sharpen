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

$("btn-conectar").addEventListener("click", conectar);
$("btn-desconectar").addEventListener("click", desconectar);
$("btn-capturar").addEventListener("click", capturar);
$("toggle-cfg").addEventListener("click", async () => {
  const cfg = $("cfg");
  cfg.hidden = !cfg.hidden;
  if (!cfg.hidden) $("api-base").value = await getApiBase();
});
$("btn-salvar-cfg").addEventListener("click", async () => {
  const v = $("api-base").value.trim().replace(/\/+$/, "");
  await chrome.storage.local.set({ apiBase: v || "" });
  setMsg("Servidor salvo.", "info");
});

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
    const { modo } = await chrome.storage.local.get("modo");
    if (modo === "texto") {
      // Betano: dispara o robô (rola + colhe + envia texto).
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

async function render() {
  const st = await chrome.storage.local.get(["token", "casa", "parceiro", "modo", "lastError"]);
  if (st.token) {
    telaConectar.hidden = true;
    telaConectado.hidden = false;
    setStatusPill(true);
    $("c-casa").textContent = st.casa || "—";
    $("c-parceiro").textContent = st.parceiro || "—";
    const dom = DOMINIOS[st.casa];
    const fav = $("c-favicon");
    if (dom) { fav.style.display = ""; fav.src = `https://icons.duckduckgo.com/ip3/${dom}.ico`; }
    else { fav.style.display = "none"; }
    const texto = st.modo === "texto";
    $("nota-texto").hidden = !texto;
    $("btn-capturar").hidden = false;   // vale nos dois modos
    $("cap-label").textContent = texto ? "Copiar bilhetes" : "Capturar";
  } else {
    telaConectar.hidden = false;
    telaConectado.hidden = true;
    setStatusPill(false);
    if (st.lastError) setMsg(st.lastError, "erro");
  }
}

render();
