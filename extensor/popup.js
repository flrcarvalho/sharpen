// Popup SharpenUp: parear (trocar código por token), mostrar estado, disparar captura.
const $ = (id) => document.getElementById(id);

const telaConectar = $("tela-conectar");
const telaConectado = $("tela-conectado");
const msg = $("msg");

// Versão desta instalação (do manifest) — reportada ao backend nos handshakes p/ ele
// detectar instalações antigas. O backend responde se está desatualizada.
const VERSAO = chrome.runtime.getManifest().version;
let _versaoInfo = { desatualizada: false, versao_atual: "" };

// Domínio da casa p/ o favicon (grayscale, cosmético — some se não carregar).
const DOMINIOS = {
  "Superbet": "superbet.com", "Betano": "betano.com", "Bet365": "bet365.com",
  "Betfair": "betfair.com", "KTO": "kto.com", "Pinnacle": "pinnacle.com",
  "Betnacional": "betnacional.com", "Lottu": "lottu.com", "Vitória Bet": "vitoriabet.com",
  "BETesporte": "betesporte.bet.br",
};

// Amarração casa↔site (Fix cliente): domínios operacionais (BR) das casas de robô. Ao
// capturar, o popup exige que a aba ativa seja da casa CONECTADA — impede (ex.) capturar
// na Superbet com um código de Betfair. Casa fora deste mapa (print, domínio desconhecido)
// → não checa (não bloqueia captura legítima que não temos como verificar). Espelha o
// _HOSTS_POR_CASA do backend (captura.py), que é o backstop que não dá pra burlar.
const CASA_HOSTS = {
  "Superbet":   ["superbet.bet.br", "superbet.com"],
  "Betano":     ["betano.bet.br"],
  "Bet365":     ["bet365.com", "bet365.bet.br"],
  "BETesporte": ["betesporte.bet.br"],
  "Betfair":    ["betfair.bet.br"],
  "Pinnacle":   ["pinnacle.bet.br"],
};
function hostBate(host, casa) {
  const hosts = CASA_HOSTS[casa];
  if (!hosts) return true;                 // casa sem domínio conhecido → não checa
  const h = (host || "").toLowerCase();
  return hosts.some((x) => h === x || h.endsWith("." + x));
}

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
// Betfair: quantidade (freio principal, padrão 100) + dias opcional + varrer tudo.
$("bf-qtd").addEventListener("change", (e) => {
  const n = Math.max(1, Math.min(5000, Number(e.target.value) || 100));
  e.target.value = n;
  chrome.storage.local.set({ bfQtd: n });
});
$("bf-dias").addEventListener("change", (e) => {
  const v = (e.target.value || "").trim();
  const n = v ? Math.max(1, Math.min(365, Number(v) || 0)) : 0;   // 0 = sem limite de dias
  e.target.value = n || "";
  chrome.storage.local.set({ bfDias: n });
});
$("bf-full").addEventListener("change", (e) => {
  chrome.storage.local.set({ bfFull: !!e.target.checked });
  _bfToggleFull(e.target.checked);
});
// Varrer tudo desativa (visualmente) quantidade + dias — os limites são ignorados.
function _bfToggleFull(on) {
  $("bf-qtd").disabled = on;
  $("bf-dias").disabled = on;
  $("bf-qtd-wrap").style.opacity = on ? ".45" : "";
  $("bf-dias-wrap").style.opacity = on ? ".45" : "";
}

$("btn-conectar").addEventListener("click", conectar);
$("btn-desconectar").addEventListener("click", desconectar);
$("btn-capturar").addEventListener("click", capturar);
$("btn-reenviar").addEventListener("click", reenviar);

// "Atualizar" → abre a página de instalação/atualização com a versão instalada na URL
// (a página mostra atualizado ✓ / desatualizado ⚠ e o link do .zip novo).
$("btn-atualizar").addEventListener("click", async () => {
  const base = await getApiBase();
  chrome.tabs.create({ url: `${base}/extensao?v=${encodeURIComponent(VERSAO)}` });
});

// Rodapé mostra a versão real do manifest (nunca um número hardcoded que dessincroniza).
const _verEl = document.querySelector(".foot .ver");
if (_verEl) _verEl.textContent = "v" + VERSAO;

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
      body: JSON.stringify({ codigo, versao: VERSAO }),
    });
    if (r.status === 404) { setMsg("Código inválido ou expirado. Gere outro no dashboard.", "erro"); return; }
    if (!r.ok) { setMsg("Erro ao conectar (" + r.status + ").", "erro"); return; }
    const d = await r.json();
    _versaoInfo = { desatualizada: !!d.desatualizada, versao_atual: d.versao_atual || "" };
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
    // Amarração casa↔site: não deixa capturar numa casa diferente da conectada (ex.:
    // código de Betfair rodando na Superbet). O backend tem o mesmo check como backstop.
    let host = "";
    try { host = new URL(tab.url).hostname; } catch (_) {}
    if (!hostBate(host, casa)) {
      setMsg("Conectado como " + casa + ", mas esta aba é " + (host || "outro site") +
             ". Abra o site da " + casa + " ou gere um código para a casa certa.", "erro");
      return;
    }
    if (modo === "texto") {
      // Interceptor de API no mundo MAIN (be/sb_inject): o content_script declarativo só
      // roda em page LOAD. Se a aba já estava aberta antes de recarregar a extensão, injeta
      // agora (idempotente — guarda interna). Sem isso o robô roda mas capta zero.
      const inj = casa === "BETesporte" ? "be_inject.js"
                : casa === "Superbet" ? "sb_inject.js"
                : casa === "Betano" ? "bn_inject.js"
                : casa === "Betfair" ? "bf_inject.js"
                : casa === "Pinnacle" ? "pn_inject.js" : null;
      // Frame de topo (onde vivem os bilhetes na Betfair — confirmado). O manifest cobre os
      // sub-frames betfair.bet.br no carregamento (all_frames); aqui é o backup p/ aba já aberta.
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

// Reenvia o texto bancado (`envioPendente`) que ficou de um envio que caiu — SEM re-raspar
// nada. Vai pelo mesmo caminho ENVIAR_TEXTO do background (sem aba → sem checagem casa↔site,
// que aqui é só backstop). Só limpa o banco quando o servidor confirma {ok}; falhou de novo →
// mantém guardado. Se a sessão morreu de novo (401), o background limpa o token → reconectar.
async function reenviar() {
  const st = await chrome.storage.local.get(["token", "envioPendente"]);
  const pend = st.envioPendente;
  if (!pend || !pend.texto) { $("pendente").hidden = true; return; }
  if (!st.token) { setMsg("Reconecte primeiro (cole um novo código) e reenvie.", "erro"); return; }
  setMsg("Reenviando…", "info");
  $("btn-reenviar").disabled = true;
  let resp = null;
  try { resp = await chrome.runtime.sendMessage({ type: "ENVIAR_TEXTO", texto: pend.texto }); } catch (e) {}
  $("btn-reenviar").disabled = false;
  if (resp && resp.ok) {
    await chrome.storage.local.remove("envioPendente");
    $("pendente").hidden = true;
    setMsg((pend.n || "") + " bilhete(s) reenviados ✓ — abra o dashboard para processar.", "ok");
  } else {
    setMsg("Reenvio falhou — os bilhetes seguem guardados. Confira a conexão e tente de novo.", "erro");
  }
}

// Re-renderiza quando o estado de conexão muda no storage (ex.: o background
// remove o token ao expirar a sessão → o popup sai de "Conectado" na hora, sem
// ficar mostrando estado velho). Não re-renderiza em writes de lookback/stopId.
chrome.storage.onChanged.addListener((ch, area) => {
  if (area === "local" && ("token" in ch || "casa" in ch || "modo" in ch || "lastError" in ch)) render();
});

// Valida o token contra a sessão viva no servidor. "ok" = conectado; "expired" (401) =
// sessão morta (limpar token órfão); "offline" = servidor inacessível (não afirmar online).
async function validarToken(token) {
  try {
    const base = await getApiBase();
    const r = await fetch(`${base}/captura/validar`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token, versao: VERSAO }),
    });
    if (r.ok) {
      try { const d = await r.json(); _versaoInfo = { desatualizada: !!d.desatualizada, versao_atual: d.versao_atual || "" }; } catch (_) {}
      return "ok";
    }
    if (r.status === 401) return "expired";
    return "offline";
  } catch (e) {
    return "offline";
  }
}

// Faixa de aviso: some quando atualizado, aparece com a versão-alvo quando atrás.
function renderAvisoVersao() {
  const el = $("aviso-versao");
  if (!el) return;
  if (_versaoInfo.desatualizada) {
    $("aviso-versao-txt").textContent = _versaoInfo.versao_atual
      ? `Versão ${VERSAO} desatualizada — atualize para ${_versaoInfo.versao_atual}.`
      : "Versão desatualizada — atualize.";
    el.hidden = false;
  } else {
    el.hidden = true;
  }
}

async function render() {
  renderAvisoVersao();
  const st = await chrome.storage.local.get(["token", "casa", "parceiro", "modo", "lastError", "envioPendente"]);
  // Envio bancado que ficou de uma queda no envio único. Poda > 24h (o backend dedupa por
  // código, mas um aviso perpétuo de dado velho confunde) — some silenciosamente.
  let pend = (st.envioPendente && st.envioPendente.texto) ? st.envioPendente : null;
  if (pend && pend.ts && (Date.now() - pend.ts) > 24 * 3600 * 1000) {
    try { await chrome.storage.local.remove("envioPendente"); } catch (e) {}
    pend = null;
  }
  if (!st.token) {
    telaConectar.hidden = false;
    telaConectado.hidden = true;
    setStatusPill(false);
    // Pendência guardada tem prioridade sobre o lastError: reassegura o usuário na hora ("nada
    // foi perdido") e diz o próximo passo (reconectar → o banner de Reenviar aparece).
    if (pend) setMsg(pend.n + " bilhete(s) do último envio ficaram guardados. Reconecte para reenviar — nada foi perdido.", "info");
    else if (st.lastError) setMsg(st.lastError, "erro");
    return;
  }
  // Token salvo ≠ sessão viva: a sessão mora em memória no servidor (some no restart do
  // Railway / TTL de 6h). Valida ANTES de afirmar "Conectado" — pill/tela só dizem
  // conectado se a sessão existir de fato.
  const estado = await validarToken(st.token);
  // validarToken acabou de popular _versaoInfo (a resposta do /validar traz o sinal de
  // versão) — re-renderiza a faixa agora, senão ela só apareceria no próximo render.
  renderAvisoVersao();
  if (estado === "expired") {
    // Sessão morta → limpa o token órfão + volta a parear (onChanged re-renderiza com o aviso).
    await chrome.storage.local.set({ lastError: "Sessão expirada. Gere um novo código no dashboard e reconecte." });
    await chrome.storage.local.remove(["token", "casa", "parceiro", "modo", "dono", "codigo"]);
    return;
  }
  // "ok" (online) OU "offline" (servidor inacessível): mostra o slot pareado, mas o pill só
  // acende no "ok"; no "offline" avisa e NÃO afirma conexão.
  telaConectar.hidden = true;
  telaConectado.hidden = false;
  setStatusPill(estado === "ok");
  setMsg(estado === "offline" ? "Sem conexão com o servidor — reabra o popup para tentar de novo." : "",
         estado === "offline" ? "erro" : "");
  $("c-casa").textContent = st.casa || "—";
  $("c-parceiro").textContent = st.parceiro || "—";
  const dom = DOMINIOS[st.casa];
  const fav = $("c-favicon");
  if (dom) { fav.style.display = ""; fav.src = `https://icons.duckduckgo.com/ip3/${dom}.ico`; }
  else { fav.style.display = "none"; }
  const texto = st.modo === "texto";
  // Bet365: nada extra — o robô detalha por rota e o backend pré-dedupa/pagina (não precisa
  // mais de marco/teto). Betfair: quantidade + dias + varrer tudo. Betano/Superbet/BETesporte:
  // janela de dias + ID.
  const isBet365 = texto && st.casa === "Bet365";
  const isBetfair = texto && st.casa === "Betfair";
  const isBetSup = texto && !isBet365 && !isBetfair;
  $("nota-texto").hidden = !texto;
  $("janela-wrap").hidden = !isBetSup;
  $("stopid-wrap").hidden = !isBetSup;
  $("bf-qtd-wrap").hidden = !isBetfair;
  $("bf-dias-wrap").hidden = !isBetfair;
  $("bf-full-wrap").hidden = !isBetfair;
  $("btn-capturar").hidden = false;   // vale nos dois modos
  $("cap-label").textContent = texto ? "Copiar bilhetes" : "Capturar";
  if (isBetSup) {
    const cfg = await chrome.storage.local.get(["lookbackDias", "stopId"]);
    $("lookback").value = cfg.lookbackDias || 30;
    $("stopid").value = cfg.stopId || "";
  } else if (isBetfair) {
    const cfg = await chrome.storage.local.get(["bfQtd", "bfDias", "bfFull"]);
    $("bf-qtd").value = cfg.bfQtd || 100;
    $("bf-dias").value = cfg.bfDias || "";
    $("bf-full").checked = !!cfg.bfFull;
    _bfToggleFull(!!cfg.bfFull);
  }
  // Banner de reenvio: aparece quando há texto bancado de um envio que caiu. O botão só
  // funciona de fato com sessão viva; se estiver "offline", reenviar falha e mantém guardado.
  const pendEl = $("pendente");
  if (pend) {
    $("pend-txt").textContent = pend.n + " bilhete(s) guardados do último envio (a conexão caiu). Reenvie sem raspar de novo:";
    pendEl.hidden = false;
  } else {
    pendEl.hidden = true;
  }
}

render();
