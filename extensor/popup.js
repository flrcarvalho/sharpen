// Popup: parear (trocar código por token), mostrar estado e disparar a captura.
const $ = (id) => document.getElementById(id);

const telaConectar = $("tela-conectar");
const telaConectado = $("tela-conectado");
const msg = $("msg");

function setMsg(texto, tipo) {
  msg.textContent = texto || "";
  msg.className = "msg" + (tipo ? " " + tipo : "");
}

// Formata o código enquanto digita: MAIÚSCULO + hífen automático (ABCD-EFGH).
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
    await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ["overlay.js"] });
    window.close(); // o overlay assume a partir daqui, na própria página
  } catch (e) {
    setMsg("Não foi possível abrir a captura nesta página.", "erro");
  }
}

async function render() {
  const st = await chrome.storage.local.get(["token", "casa", "parceiro", "modo", "lastError"]);
  if (st.token) {
    telaConectar.hidden = true;
    telaConectado.hidden = false;
    $("c-casa").textContent = st.casa || "—";
    $("c-parceiro").textContent = st.parceiro || "—";
    const texto = st.modo === "texto";
    $("nota-texto").hidden = !texto;
    $("btn-capturar").hidden = texto;   // modo texto (Betano) = Fase 3
  } else {
    telaConectar.hidden = false;
    telaConectado.hidden = true;
    if (st.lastError) setMsg(st.lastError, "erro");
  }
}

render();
