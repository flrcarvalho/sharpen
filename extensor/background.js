// Service worker: recebe a região da moldura (content.js), tira o print da aba
// visível, recorta e envia para a ponte (/captura/enviar) autenticado pelo token.
// Ao fim avisa o content.js (CAPTURA_FIM {ok}) pra a moldura reaparecer e o
// contador subir só em envio real.
importScripts("config.js");

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg && msg.type === "CAPTURAR_REGIAO") {
    capturarRegiao(msg, sender.tab)
      .then((ok) => { sendResponse({ ok }); avisarFim(sender.tab.id, ok); })
      .catch((e) => { sendResponse({ ok: false, erro: String(e && e.message || e) }); avisarFim(sender.tab.id, false); });
    return true; // resposta assíncrona
  }
  if (msg && msg.type === "ENVIAR_TEXTO") {
    enviarTexto(msg.texto, sender.tab).then((ok) => sendResponse({ ok })).catch(() => sendResponse({ ok: false }));
    return true;
  }
});

function avisarFim(tabId, ok) {
  try { chrome.tabs.sendMessage(tabId, { type: "CAPTURA_FIM", ok: !!ok }); } catch (_) {}
}

// Domínio da aba de onde veio a captura → o backend amarra casa↔site (recusa gravar a
// captura de um site no slot de outra casa). Vazio se a URL não parsear.
function hostDaAba(tab) {
  try { return new URL(tab.url).hostname; } catch (e) { return ""; }
}

async function capturarRegiao(msg, tab) {
  const { rect, dpr, vw, vh } = msg;
  // Print da viewport visível (já sem a moldura, que se escondeu antes de mandar).
  const dataUrl = await chrome.tabs.captureVisibleTab(tab.windowId, { format: "png" });
  const bmp = await createImageBitmap(await (await fetch(dataUrl)).blob());

  // Escala REAL da foto: largura/altura da imagem ÷ viewport (innerWidth/Height).
  // A região vem em px CSS → multiplica pela escala real. Isso é exato mesmo se o
  // dpr do navegador ≠ escala do print (zoom / escala do Windows) — o que antes
  // cortava a direita/baixo. Fallback no dpr se a viewport não veio.
  const scaleX = vw ? bmp.width / vw : (dpr || 1);
  const scaleY = vh ? bmp.height / vh : (dpr || 1);
  const sx = Math.max(0, Math.round(rect.x * scaleX));
  const sy = Math.max(0, Math.round(rect.y * scaleY));
  const sw = Math.min(bmp.width - sx, Math.round(rect.width * scaleX));
  const sh = Math.min(bmp.height - sy, Math.round(rect.height * scaleY));
  if (sw < 4 || sh < 4) throw new Error("Região muito pequena.");

  const canvas = new OffscreenCanvas(sw, sh);
  const ctx = canvas.getContext("2d");
  ctx.drawImage(bmp, sx, sy, sw, sh, 0, 0, sw, sh);
  const blob = await canvas.convertToBlob({ type: "image/png" });

  return await enviarCaptura(blob, tab);   // true só se enviou de fato
}

async function enviarCaptura(blob, tab) {
  const { token } = await chrome.storage.local.get("token");
  if (!token) {
    await sinalizar(tab, false, "Não conectado. Cole o código no popup da extensão.");
    return false;
  }
  const base = await getApiBase();
  const fd = new FormData();
  fd.append("token", token);
  fd.append("tipo", "imagem");
  fd.append("versao", chrome.runtime.getManifest().version);
  fd.append("imagem", blob, "captura.png");
  const origem = hostDaAba(tab);
  if (origem) fd.append("origem", origem);

  let r;
  try {
    r = await fetch(`${base}/captura/enviar`, { method: "POST", body: fd });
  } catch (e) {
    await sinalizar(tab, false, "Falha de rede ao enviar. Tente de novo.");
    return false;
  }

  if (r.status === 401) {
    // Sessão/token caiu — limpa e pede reconexão.
    await chrome.storage.local.remove(["token", "casa", "parceiro", "modo", "dono", "codigo"]);
    await chrome.storage.local.set({ lastError: "Sessão expirou. Gere um novo código no dashboard e reconecte." });
    await sinalizar(tab, false, "Sessão expirou — reconecte no popup.");
    return false;
  }
  if (r.status === 429) {
    await sinalizar(tab, false, "Fila cheia — processe no dashboard antes de enviar mais.");
    return false;
  }
  if (r.status === 409) {
    // Amarração casa↔site: o site não corresponde à casa conectada.
    await sinalizar(tab, false, "Casa incompatível — o site não corresponde à conexão. Gere um código para a casa certa.");
    return false;
  }
  if (!r.ok) {
    await sinalizar(tab, false, "Erro ao enviar (" + r.status + ").");
    return false;
  }
  await sinalizar(tab, true, "Enviado ✓");
  return true;
}

// Envia o texto colhido pelo robô (modo Betano) → /captura/enviar tipo=texto.
async function enviarTexto(texto, tab) {
  const { token } = await chrome.storage.local.get("token");
  if (!token) { await sinalizar(tab, false, "Não conectado. Cole o código no popup."); return false; }
  if (!texto || !texto.trim()) { await sinalizar(tab, false, "Nada para enviar."); return false; }
  const base = await getApiBase();
  const fd = new FormData();
  fd.append("token", token);
  fd.append("tipo", "texto");
  fd.append("versao", chrome.runtime.getManifest().version);
  fd.append("texto", texto);
  const origem = hostDaAba(tab);
  if (origem) fd.append("origem", origem);
  let r;
  try {
    r = await fetch(`${base}/captura/enviar`, { method: "POST", body: fd });
  } catch (e) {
    await sinalizar(tab, false, "Falha de rede ao enviar. Tente de novo.");
    return false;
  }
  if (r.status === 401) {
    await chrome.storage.local.remove(["token", "casa", "parceiro", "modo", "dono", "codigo"]);
    await chrome.storage.local.set({ lastError: "Sessão expirou. Gere um novo código no dashboard e reconecte." });
    await sinalizar(tab, false, "Sessão expirou — reconecte no popup.");
    return false;
  }
  if (r.status === 409) {
    await sinalizar(tab, false, "Casa incompatível — o site não corresponde à conexão. Gere um código para a casa certa.");
    return false;
  }
  if (!r.ok) { await sinalizar(tab, false, "Erro ao enviar (" + r.status + ")."); return false; }
  await sinalizar(tab, true, "Bilhetes enviados ✓");
  return true;
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
