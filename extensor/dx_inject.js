// Mundo MAIN (só na Dexsport): lê as RESPOSTAS que o SDK de esportes da própria página recebe
// do histórico de apostas e repassa ao content script. Plataforma PRÓPRIA (s391):
//
//   GET https://prod.dexsport.work//api/sportsbook/history/tickets?status=<placed|finished>&page=N&locale=pt
//       Accept: application/json · Authorization: <token da sessão do SDK>
//   → { data: [ … ], meta: { pageNumber, pageSize: 25, totalPages, totalRows } }
//
// A barra DUPLA no caminho é da casa (medido). O SDK roda num shadow DOM NA PRÓPRIA página
// (sem iframe) e pede a lista por XHR — este inject engancha o XHR e o fetch do mundo MAIN.
//
// ⚠ A OUTRA LISTA. O perfil do site tem um histórico próprio (`POST dexsport.io/api/v3/
// txs_list`) que carrega, no meio do bilhete, um `token` de 57 caracteres, o `ip` e o `userId`,
// e lê o retorno de `reserve` — que na PERDIDA guarda o potencial. Este inject IGNORA aquela
// lista de propósito: o RX só casa o caminho do SDK.
//
// REPLAY ATIVO: a partir de uma requisição AUTENTICADA da página, o inject aprende a URL e os
// headers e repagina `placed` e `finished` por `page` até `meta.totalPages`. O replay vai por
// XHR, com os protótipos ORIGINAIS, porque é assim que a página chama: não arriscar um CORS
// diferente no fetch (foi o que zerou o replay da Betboom, s340).
//
// ⚠ O TOKEN NÃO SAI DAQUI. Ele vive só em `reqCtx.headers`, para o replay; a mensagem ao
// content leva o bilhete normalizado e nada da requisição.
//
// O inject NÃO decide nada: normaliza campos crus. `result`, `status` e o status de cada perna
// sobem como número; quem traduz é o `formatTicketDX` (leitura pelo dinheiro) e a CASA_DEXSPORT.md.
(function () {
  const RX = /\/api\/sportsbook\/history\/tickets/i;    // lista do SDK (nunca o txs_list do perfil)
  const byId = new Map();                      // id(string) → bilhete normalizado
  let respostas = 0;                           // respostas VÁLIDAS do endpoint (autodiagnóstico)
  let reqCtx = null;                           // {url, headers} de uma requisição AUTENTICADA
  let pedido = false;                          // o robô já pediu → pode arrancar o replay
  let loopAtivo = false;                       // trava: um replay por vez
  let fimReplay = false;                       // as duas listas já foram repaginadas
  const LOG = (...a) => { try { console.log("[SharpenUp dx_inject]", ...a); } catch (e) {} };
  LOG("hook instalado em", location.href);

  const of = window.fetch;
  const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send,
        osh = XMLHttpRequest.prototype.setRequestHeader;

  // As duas abas do painel "Minhas apostas" do SDK: Abertas e Concluídas.
  const STATUS = ["placed", "finished"];

  // ── normalização (SDK Dexsport → objeto limpo) ───────────────────────────────
  // Dinheiro e odd vêm como NÚMERO JSON (25, 93.75, 3.76). Datas: `placedAt`/`finishedAt`
  // em epoch SEGUNDOS; `bets[].eventDate` em ISO **UTC** (`…T14:00:00.000Z`).
  const _n = (v) => {
    if (v == null || v === "") return null;
    const x = Number(v);
    return isFinite(x) ? x : null;
  };
  const _epochIso = (s) => {
    const t = Date.parse(String(s || ""));
    return isFinite(t) ? t / 1000 : null;
  };

  function parsePerna(b) {
    if (!b) return null;
    const ev = b.event || {}, mk = b.eventMarket || {};
    return {
      id: b.id != null ? String(b.id) : "",
      status: _n(b.status),                    // 0 não decidida · 1 ganha · 2 perdida · 6 anulada (cru)
      odd: _n(b.coefficient),                  // odd da perna na colocação
      oddPaga: _n(b.payoutCoefficient),        // 0 na perdida · 1 na anulada · = odd na ganha
      inicio: _epochIso(b.eventDate),          // ⚠ ISO em UTC → epoch; o content converte p/ SP
      esporte: String(b.disciplineId || ""),   // "football", "basketball"… (id cru do SDK)
      mercado: String(mk.name || ""),          // "Escanteios. Handicap 1º tempo"
      label: String(b.outcomeName || ""),      // "Tchéquia +2.5"
      jogo: String(ev.name || ""),             // "Espanha vs Tchéquia"
      betBuilder: Array.isArray(b.betBuilderOutcomes) && b.betBuilderOutcomes.length > 0,
    };
  }

  function parseTicket(t) {
    if (!t || t.id == null) return null;
    return {
      id: String(t.id),                        // UUID — o card estampa inteiro em "ID da aposta"
      numero: _n(t.number),
      resultado: _n(t.result),                 // 0 aberta · 1 ganha · 2 perdida (cru)
      status: _n(t.status),                    // 2 aberta · 3 concluída (cru)
      liquidacao: _n(t.settlementStatus),
      tipo: _n(t.ticketType),                  // 0 simples · 1 múltipla (cru)
      moeda: String(t.currency || ""),         // "usdt"
      stake: _n(t.amount),
      odd: _n(t.coefficient),                  // odd na COLOCAÇÃO (produto das pernas)
      oddPaga: _n(t.payoutCoefficient),        // odd LIQUIDADA (0 na perdida e na aberta)
      retorno: _n(t.payout),                   // ⚠ 0 também na ABERTA — nunca decidir por ele só
      potencial: _n(t.possiblePayout),
      boost: _n(t.boosterCoefficient),
      boostPago: _n(t.payoutBoosterCoefficient),
      bonus: _n(t.bonusType),
      ts: _n(t.placedAt),                      // colocação, epoch s
      fim: _n(t.finishedAt),
      sels: (Array.isArray(t.bets) ? t.bets : []).map(parsePerna).filter(Boolean),
    };
  }

  // Heartbeat: SEMPRE hook:true + respostas, mesmo com 0 bilhetes.
  function enviar() {
    try {
      window.postMessage({
        __sharpenupDXData: true, hook: true,
        bilhetes: Array.from(byId.values()), respostas: respostas, fim: fimReplay,
      }, "*");
    } catch (e) {}
  }

  // A versão CONCLUÍDA vence a aberta (o dinheiro só é final depois de liquidado).
  function guardar(b) {
    const ex = byId.get(b.id);
    if (!ex || (ex.status !== 3 && b.status === 3)) byId.set(b.id, b);
  }

  // Processa uma resposta; devolve {pagina, total, n} p/ o replay, ou null.
  function forward(url, text) {
    if (!RX.test(String(url)) || typeof text !== "string") return null;
    let j;
    try { j = JSON.parse(text); } catch (e) { return null; }
    if (!j || !Array.isArray(j.data)) return null;      // barra o corpo do 401
    respostas++;
    for (const raw of j.data) {
      const b = parseTicket(raw);
      if (b) guardar(b);
    }
    const m = j.meta || {};
    LOG("bilhetes na resposta:", j.data.length, "· total:", byId.size, "· página", m.pageNumber, "de", m.totalPages);
    enviar();
    return { pagina: Number(m.pageNumber), total: Number(m.totalPages), n: j.data.length };
  }

  // ── replay ───────────────────────────────────────────────────────────────────
  function _hdrsToObj(h) {
    const o = {};
    try {
      if (!h) return o;
      if (typeof h.forEach === "function") h.forEach((v, k) => { o[k] = v; });
      else if (typeof h === "object") for (const k in h) o[k] = h[k];
    } catch (e) {}
    return o;
  }
  function _temToken(h) {
    for (const k in (h || {})) if (String(k).toLowerCase() === "authorization" && h[k]) return true;
    return false;
  }

  function capturarReq(url, headers) {
    if (!RX.test(String(url))) return;
    // Sem token não se aprende nada: repaginar sem `Authorization` é colher 401 em toda página.
    if (!_temToken(headers)) { LOG("requisição sem Authorization ignorada"); return; }
    if (!reqCtx) {
      reqCtx = { url: String(url), headers: headers || {} };
      LOG("requisição autenticada capturada p/ replay");
    }
    if (pedido) arrancarReplay();
  }

  function comPagina(status, pagina) {
    try {
      const u = new URL(reqCtx.url, location.href);
      u.searchParams.set("status", status);
      u.searchParams.set("page", String(pagina));
      return u.href;
    } catch (e) { return null; }
  }

  // GET por XHR com os protótipos ORIGINAIS (não passa pelo gancho, que processaria duas vezes).
  function pedirPagina(url) {
    return new Promise((resolve) => {
      try {
        const x = new XMLHttpRequest();
        oo.call(x, "GET", url);
        const h = (reqCtx && reqCtx.headers) || {};
        for (const k in h) { try { osh.call(x, k, h[k]); } catch (e) {} }
        x.addEventListener("load", () => resolve({ ok: x.status >= 200 && x.status < 300, status: x.status, text: x.responseText }));
        x.addEventListener("error", () => resolve({ ok: false, status: 0, text: "" }));
        os.call(x);
      } catch (e) { resolve({ ok: false, status: 0, text: "" }); }
    });
  }

  const TETO_PAGINAS = 200;

  async function paginar(status) {
    for (let pg = 1; pg <= TETO_PAGINAS; pg++) {
      const url = comPagina(status, pg);
      if (!url) return;
      const r = await pedirPagina(url);
      if (!r.ok) { LOG("replay parou · HTTP", r.status, "·", status, pg); return; }
      const res = forward(url, r.text);
      if (!res || !res.n) return;                           // página vazia = acabou
      // Fim AUTORITATIVO: a casa diz quantas páginas existem.
      if (isFinite(res.total) && pg >= res.total) return;
    }
    LOG("teto de páginas atingido ·", status);
  }

  async function arrancarReplay() {
    if (loopAtivo || fimReplay || !reqCtx) return;
    loopAtivo = true;
    try {
      for (const st of STATUS) await paginar(st);
    } finally {
      loopAtivo = false;
      fimReplay = true;
      enviar();
    }
  }

  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (!d || !d.__sharpenupDXReq) return;
    pedido = true;
    enviar();
    arrancarReplay();
  });

  // ── XMLHttpRequest (é por aqui que o SDK pede a lista) ──
  if (!os.__suDXW) {
    XMLHttpRequest.prototype.open = function (m, u) { this.__suDXU = u; this.__suDXH = {}; return oo.apply(this, arguments); };
    XMLHttpRequest.prototype.setRequestHeader = function (k, v) { try { this.__suDXH[k] = v; } catch (e) {} return osh.apply(this, arguments); };
    const s = function () {
      try {
        if (RX.test(String(this.__suDXU))) {
          capturarReq(this.__suDXU, this.__suDXH);
          this.addEventListener("load", () => { try { forward(this.__suDXU, this.responseText); } catch (e) {} });
        }
      } catch (e) {}
      return os.apply(this, arguments);
    };
    s.__suDXW = true;
    XMLHttpRequest.prototype.send = s;
  }

  // ── fetch (rede de segurança: hoje o SDK usa XHR) ──
  if (of && !of.__suDXW) {
    const w = function (...a) {
      const url = (a[0] && a[0].url) || a[0];
      const opts = a[1] || (a[0] && typeof a[0] === "object" ? a[0] : null);
      try { if (RX.test(String(url))) capturarReq(url, _hdrsToObj(opts && opts.headers)); } catch (e) {}
      return of.apply(this, a).then((r) => {
        try { if (RX.test(String(url))) r.clone().text().then((t) => forward(url, t)); } catch (e) {}
        return r;
      });
    };
    w.__suDXW = true;
    window.fetch = w;
  }
})();
