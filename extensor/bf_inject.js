// Mundo MAIN (Betfair): lê as RESPOSTAS da API de bilhetes resolvidos
// (POST /activity/sportsbook — JSON com `bets[]`) que a própria página baixa E **PAGINA
// ATIVAMENTE**: a partir da 1ª resposta, o próprio inject re-emite a requisição avançando
// a página (nextPageIndex), com os cookies da sessão, até `moreAvailable:false`. Assim NÃO
// depende do scroll/botão da página (que se mostrou não confiável — lista curta não rola).
//
// Casamento por FORMA do JSON (não por URL exata — o `open` recebe URL relativa): só aceita
// respostas com `bets[]` e `responseFilters.status === "SETTLED"` (a lista RESOLVIDA; a aba
// "Aberta" também chama o endpoint, com poucas apostas e moreAvailable:false → zerava tudo).
//
// Reporta pro content script na própria janela E na do TOPO (a lista pode rodar em iframe).
// hook:true = injeção OK · respostas>0 = viu a API · bets>0 = leu os bilhetes (autodiagnóstico).
(function () {
  const RX = /sportsbook/i;
  const all = [];
  const seen = new Set();
  let fimReal = false;
  let respostas = 0;
  let reqCtx = null;        // {url, method, headers, body} da requisição SETTLED (p/ replay)
  let loopAtivo = false;    // trava: só um loop de paginação ativa por vez
  let replays = 0;
  let ultimoNext = null;    // nextPageIndex da última resposta vista (p/ retomar a paginação)
  let ultimoStart = 0;      // rangeStart da última resposta vista
  let limite = 0;           // teto de bilhetes pedido pelo robô (0 = sem limite / varrer tudo)
  let pedido = false;       // o robô já pediu a coleta → pode arrancar a paginação ativa
  const LOG = (...a) => { try { console.log("[SharpenUp bf_inject]", ...a); } catch (e) {} };
  LOG("hook instalado em", location.href, "· frame top?", window.top === window);

  const of = window.fetch;  // fetch ORIGINAL — o replay usa este p/ não re-disparar o wrapper.

  function enviar() {
    const msg = { __sharpenupBFData: true, hook: true, bets: all, fim: fimReal, respostas: respostas };
    try { window.postMessage(msg, "*"); } catch (e) {}
    try { if (window.top && window.top !== window) window.top.postMessage(msg, "*"); } catch (e) {}
  }

  function _bodyToStr(b) {
    try {
      if (typeof b === "string") return b;
      if (b instanceof URLSearchParams) return b.toString();
      return JSON.stringify(b);
    } catch (e) { return ""; }
  }
  function _hdrsToObj(h) {
    const o = { "Content-Type": "application/json" };
    try {
      if (!h) return o;
      if (typeof h.forEach === "function") h.forEach((v, k) => { o[k] = v; });   // Headers
      else if (typeof h === "object") for (const k in h) o[k] = h[k];
    } catch (e) {}
    return o;
  }

  // Guarda a 1ª requisição "sportsbook" COM body → base do replay de paginação.
  function capturarReq(url, method, headers, body) {
    if (reqCtx || !RX.test(String(url)) || !body) return;
    reqCtx = { url: String(url), method: (method || "POST"), headers: headers, body: _bodyToStr(body) };
    LOG("requisição capturada p/ replay · body:", (reqCtx.body || "").slice(0, 200));
  }

  // Processa uma resposta de bilhetes (passiva OU do replay). Retorna {more,next,start} ou null.
  function forward(url, text) {
    if (!RX.test(String(url)) || typeof text !== "string") return null;
    let j;
    try { j = JSON.parse(text); } catch (e) { return null; }
    if (!j || !Array.isArray(j.bets)) return null;
    const status = j.responseFilters && j.responseFilters.status;
    if (status && String(status).toUpperCase() !== "SETTLED") return null;   // só a RESOLVIDA
    respostas++;
    const antes = all.length;
    for (const t of j.bets) {
      const c = t && t.betId;
      if (c && !seen.has(c)) { seen.add(c); all.push(t); }
    }
    LOG("bilhetes:", j.bets.length, "· total:", all.length, "· moreAvailable:", j.moreAvailable);
    const start = (typeof j.rangeStart === "number" ? j.rangeStart : 0);
    ultimoNext = j.nextPageIndex; ultimoStart = start;   // p/ retomar quando o robô pedir
    if (j.moreAvailable === false) fimReal = true;
    enviar();
    // Se o robô já pediu (e a resposta chegou depois), arranca a paginação ativa agora.
    if (pedido && !loopAtivo && !fimReal && reqCtx && ultimoNext != null) paginarLoop(ultimoNext, ultimoStart);
    return { more: j.moreAvailable, next: j.nextPageIndex, start: start, antes: antes };
  }

  // Monta o body da próxima página: troca o campo de índice (o que vale rangeStart atual, +
  // nomes comuns) por nextIndex. Se nada casar, o guarda "sem bilhete novo" abaixo evita loop.
  function bodyProxPagina(nextIndex, rangeStart) {
    let obj = null;
    try { obj = JSON.parse(reqCtx.body); } catch (e) {}
    if (!obj || typeof obj !== "object") return reqCtx.body;
    for (const k of Object.keys(obj)) {
      if (typeof obj[k] === "number" && obj[k] === rangeStart) obj[k] = nextIndex;
    }
    for (const k of ["pageIndex", "index", "rangeStart", "startIndex", "startRecord", "from", "offset", "page"]) {
      if (k in obj && typeof obj[k] === "number") obj[k] = nextIndex;
    }
    return JSON.stringify(obj);
  }

  async function paginarLoop(nextIndex, rangeStart) {
    if (loopAtivo) return;
    loopAtivo = true;
    let idx = nextIndex, start = rangeStart;
    try {
      while (!fimReal && reqCtx && idx != null && replays < 400) {
        if (limite && all.length >= limite) break;   // atingiu o teto pedido pelo robô
        replays++;
        const antes = all.length;
        let info;
        try {
          const r = await of.call(window, reqCtx.url, {
            method: reqCtx.method, headers: reqCtx.headers,
            body: bodyProxPagina(idx, start), credentials: "include",
          });
          info = forward(reqCtx.url, await r.text());
        } catch (e) { LOG("erro no replay:", e && e.message); break; }
        if (!info) break;                                  // resposta inesperada → para
        if (all.length === antes) { LOG("replay sem bilhete novo → fim"); break; }  // não avançou
        if (info.more === false || info.next == null || info.next === idx) break;   // fim/estagnou
        start = info.start; idx = info.next;
      }
    } finally {
      loopAtivo = false;
      fimReal = true;   // esgotou a paginação ativa → sinaliza fim p/ o robô parar de esperar
      enviar();
    }
  }

  // O content script pede o estado ao iniciar o robô (com o teto de bilhetes) → responde
  // SEMPRE (reporta hook vivo) e ARRANCA a paginação ativa até o limite. Paginar só sob
  // demanda (não no load da página) respeita o teto e não puxa o histórico inteiro à toa.
  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (!d || !d.__sharpenupBFReq) return;
    if (typeof d.limite === "number") limite = d.limite;
    pedido = true;
    enviar();
    if (!loopAtivo && !fimReal && reqCtx && ultimoNext != null) paginarLoop(ultimoNext, ultimoStart);
  });

  // ── fetch ──
  if (of && !of.__suBFW) {
    const w = function (...a) {
      const url = (a[0] && a[0].url) || a[0];
      const opts = a[1] || (a[0] && typeof a[0] === "object" ? a[0] : null);
      try { if (opts && opts.body) capturarReq(url, opts.method, _hdrsToObj(opts.headers), opts.body); } catch (e) {}
      return of.apply(this, a).then((r) => {
        try { if (RX.test(String(url))) r.clone().text().then((t) => forward(url, t)); } catch (e) {}
        return r;
      });
    };
    w.__suBFW = true;
    window.fetch = w;
  }

  // ── XMLHttpRequest ──
  const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send, osh = XMLHttpRequest.prototype.setRequestHeader;
  if (!os.__suBFW) {
    XMLHttpRequest.prototype.open = function (m, u) { this.__suBFU = u; this.__suBFM = m; this.__suBFH = { "Content-Type": "application/json" }; return oo.apply(this, arguments); };
    XMLHttpRequest.prototype.setRequestHeader = function (k, v) { try { this.__suBFH[k] = v; } catch (e) {} return osh.apply(this, arguments); };
    const s = function (body) {
      try {
        if (RX.test(String(this.__suBFU))) {
          if (body) capturarReq(this.__suBFU, this.__suBFM, this.__suBFH, body);
          this.addEventListener("load", () => { try { forward(this.__suBFU, this.responseText); } catch (e) {} });
        }
      } catch (e) {}
      return os.apply(this, arguments);
    };
    s.__suBFW = true;
    XMLHttpRequest.prototype.send = s;
  }
})();
