// Service worker: recebe a região selecionada pelo overlay, tira o print da aba
// visível, recorta e envia para a ponte (/captura/enviar) autenticado pelo token.
importScripts("config.js");

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg && msg.type === "CAPTURAR_REGIAO") {
    capturarRegiao(msg.rect, msg.dpr, sender.tab)
      .then(() => sendResponse({ ok: true }))
      .catch((e) => sendResponse({ ok: false, erro: String(e && e.message || e) }));
    return true; // resposta assíncrona
  }
});

async function capturarRegiao(rect, dpr, tab) {
  // Print da viewport visível (já sem o overlay, que se escondeu antes de mandar).
  const dataUrl = await chrome.tabs.captureVisibleTab(tab.windowId, { format: "png" });
  const bmp = await createImageBitmap(await (await fetch(dataUrl)).blob());

  // captureVisibleTab devolve em pixels físicos (viewport × dpr); a região vem em
  // px CSS → multiplica por dpr. Clampa nos limites da imagem por segurança.
  const sx = Math.max(0, Math.round(rect.x * dpr));
  const sy = Math.max(0, Math.round(rect.y * dpr));
  const sw = Math.min(bmp.width - sx, Math.round(rect.width * dpr));
  const sh = Math.min(bmp.height - sy, Math.round(rect.height * dpr));
  if (sw < 4 || sh < 4) throw new Error("Região muito pequena.");

  const canvas = new OffscreenCanvas(sw, sh);
  const ctx = canvas.getContext("2d");
  ctx.drawImage(bmp, sx, sy, sw, sh, 0, 0, sw, sh);
  const blob = await canvas.convertToBlob({ type: "image/png" });

  await enviarCaptura(blob, tab);
}

async function enviarCaptura(blob, tab) {
  const { token } = await chrome.storage.local.get("token");
  if (!token) {
    await sinalizar(tab, false, "Não conectado. Cole o código no popup da extensão.");
    return;
  }
  const base = await getApiBase();
  const fd = new FormData();
  fd.append("token", token);
  fd.append("tipo", "imagem");
  fd.append("imagem", blob, "captura.png");

  let r;
  try {
    r = await fetch(`${base}/captura/enviar`, { method: "POST", body: fd });
  } catch (e) {
    await sinalizar(tab, false, "Falha de rede ao enviar. Tente de novo.");
    return;
  }

  if (r.status === 401) {
    // Sessão/token caiu — limpa e pede reconexão.
    await chrome.storage.local.remove(["token", "casa", "parceiro", "modo", "dono", "codigo"]);
    await chrome.storage.local.set({ lastError: "Sessão expirou. Gere um novo código no dashboard e reconecte." });
    await sinalizar(tab, false, "Sessão expirou — reconecte no popup.");
    return;
  }
  if (r.status === 429) {
    await sinalizar(tab, false, "Fila cheia — processe no dashboard antes de enviar mais.");
    return;
  }
  if (!r.ok) {
    await sinalizar(tab, false, "Erro ao enviar (" + r.status + ").");
    return;
  }
  await sinalizar(tab, true, "Enviado ✓");
}

// Feedback na própria página (badge + toast), já que o popup costuma estar fechado.
async function sinalizar(tab, ok, texto) {
  try {
    chrome.action.setBadgeBackgroundColor({ color: ok ? "#2BC07E" : "#E5484D" });
    chrome.action.setBadgeText({ text: ok ? "✓" : "!", tabId: tab.id });
    setTimeout(() => chrome.action.setBadgeText({ text: "", tabId: tab.id }), 4000);
  } catch (_) {}
  try {
    await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: mostrarToast,
      args: [texto, ok],
    });
  } catch (_) {}
}

// Injetada na página: um toast discreto no rodapé.
function mostrarToast(texto, ok) {
  const t = document.createElement("div");
  t.textContent = texto;
  const s = t.style;
  s.setProperty("position", "fixed");
  s.setProperty("bottom", "22px");
  s.setProperty("left", "50%");
  s.setProperty("transform", "translateX(-50%)");
  s.setProperty("z-index", "2147483647");
  s.setProperty("font", "13px/1.4 system-ui, -apple-system, sans-serif");
  s.setProperty("color", "#fff");
  s.setProperty("background", ok ? "#1B7F4E" : "#B3363B");
  s.setProperty("padding", "10px 16px");
  s.setProperty("border-radius", "10px");
  s.setProperty("box-shadow", "0 8px 24px rgba(0,0,0,.35)");
  s.setProperty("opacity", "0");
  s.setProperty("transition", "opacity .18s ease");
  document.body.appendChild(t);
  requestAnimationFrame(() => (t.style.opacity = "1"));
  setTimeout(() => {
    t.style.opacity = "0";
    setTimeout(() => t.remove(), 250);
  }, 2200);
}
