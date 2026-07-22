// Mundo MAIN (só na Bet365): lê as RESPOSTAS de /sportshistoryapi/summary e
// /sportshistoryapi/confirmation (formato texto proprietário `F|00;chave=valor;…|01;…|`) que
// a própria página baixa, e RE-EMITE ativamente (replay) as buscas — com os cookies+headers da
// sessão — para varrer as duas listas (settled=1 resolvidas · settled=0 abertas) e buscar o
// DETALHE de cada bilhete (jogo/mercado/liga + o código estável `BR`). Depois repassa objetos
// limpos ao content script, para tratar igual às outras casas passivas (Betfair/Pinnacle).
//
// POR QUE PRECISA DO DETALHE: o `summary` NÃO traz jogo/mercado/liga nem o código `BR` — só a
// seleção crua, odd, stake, retorno e o esporte (`CL`). O `confirmation?bsid=` completa.
//
// DEDUP: a chave estável é o `BR` (código do comprovante — do confirmation). O `ID` numérico do
// summary MUDA quando a aposta resolve (namespace D1→D0), então serve só de `bsid` para buscar o
// detalhe na mesma visão. Ver docs/PLANO_BET365_CAPTURA_API.md.
//
// PAGINAÇÃO: a lista é por cursor no parâmetro `to` — a resposta traz no registro `00` um campo
// `PT=<ISO>` que vira o `to` da próxima página. `from` fica fixo.
//
// TOKEN: o header `x-net-sync-term` rotaciona por requisição; o replay reaproveita os headers
// EXATOS da requisição que a página fez (melhor chance de o servidor aceitar). Se o replay for
// recusado, o content cai no robô de DOM atual (roboBet365DOM) — sem regressão.
(function () {
  const RX_SUM = /\/sportshistoryapi\/summary/i;
  const RX_CONF = /\/sportshistoryapi\/confirmation/i;
  const byBsid = new Map();       // bsid(string) → bilhete mesclado (summary + confirmation)
  const confPedido = new Set();   // bsids cujo confirmation já foi disparado (não repetir)
  let respostas = 0;              // respostas de summary/confirmation que o hook viu (autodiagnóstico)
  let reqSum = null;              // {url, method, headers} de um summary real (base do replay)
  let pedido = false;             // o robô já pediu → pode arrancar o replay
  let loopAtivo = false;          // trava: um replay por vez
  let fimReplay = false;          // as duas listas + os detalhes já foram varridos
  let janelaDias = 45;            // janela das RESOLVIDAS (o robô sobrescreve). Abertas = tudo.
  const MAX_PAGINAS = 60;         // teto de páginas por lista (segurança anti-loop)
  const MAX_CONF = 400;           // teto de detalhes buscados (segurança de custo/tempo)
  const CONC = 5;                 // detalhes buscados em paralelo
  const LOG = (...a) => { try { console.log("[SharpenUp b3_inject]", ...a); } catch (e) {} };
  LOG("hook instalado em", location.href);

  const of = window.fetch;        // fetch ORIGINAL — o replay usa este (não re-dispara o wrapper)

  // ── parser do formato F|… ──────────────────────────────────────────────────────
  function parseRecords(blob) {
    const recs = [];
    for (const chunk of String(blob || "").split("|")) {
      const c = chunk.trim();
      if (!c || c === "F") continue;
      const parts = c.split(";");
      const kv = {};
      for (let i = 1; i < parts.length; i++) {
        const p = parts[i];
        const eq = p.indexOf("=");
        if (eq > -1) kv[p.slice(0, eq)] = p.slice(eq + 1);
      }
      recs.push([parts[0], kv]);
    }
    return recs;
  }

  // summary → { cursor:PT, bets:[{bsid,bs,stake,oddFrac,rt,tipo,sel,cl}] }
  function parseSummary(blob) {
    const recs = parseRecords(blob);
    let cursor = null;
    const bets = [];
    let cur = null;
    for (const [code, kv] of recs) {
      if (code === "00") { if (kv.PT) cursor = kv.PT; continue; }
      if (code === "01") {
        if (cur) bets.push(cur);
        cur = { bsid: kv.ID || "", bs: kv.BS, tp: kv.TP || "", sels: [],
                stake: null, ts: null, oddFrac: "", rt: null, tipo: "" };
      } else if (code === "03" && cur) {
        cur.sels.push({ na: kv.NA || kv.FN || "", od: kv.OD || "", cl: kv.CL || "" });
        if (!cur.oddFrac) cur.oddFrac = kv.OD || "";
      } else if (code === "02" && cur) {
        if (kv.TY === "SD") { if ("ST" in kv) cur.stake = kv.ST; if ("TS" in kv) cur.ts = kv.TS; cur.tipo = kv.NA || ""; }
        else if (kv.TY === "ST") {
          if ("RT" in kv) cur.rt = kv.RT;                 // ausente = aberta
          if (cur.stake == null && "ST" in kv) cur.stake = kv.ST;
        }
      }
    }
    if (cur) bets.push(cur);
    return { cursor, bets };
  }

  // confirmation → { br, da, bs, tipo, rt, ts, legs:[{sel,oddFrac,kickoff,cl,liga,jogo,mercado}] }
  function parseConfirmation(blob) {
    const recs = parseRecords(blob);
    if (!recs.length) return null;
    const head = recs[0][1];
    const out = { br: head.BR || "", da: head.DA || "", bs: head.BS, tipo: head.NA || "",
                  rt: null, ts: null, legs: [] };
    for (const [code, kv] of recs) {
      if (code === "02" && "FN" in kv) {
        out.legs.push({ sel: kv.NA || "", oddFrac: kv.OD || "", kickoff: kv.TP || "",
                        cl: kv.CL || "", liga: kv.L3 || "", jogo: kv.FN || "", mercado: kv.MN || "" });
      }
      if (kv.TY === "CS") { if ("RT" in kv) out.rt = kv.RT; if ("TS" in kv) out.ts = kv.TS; }
    }
    return out;
  }

  // ── emissão ao content ─────────────────────────────────────────────────────────
  function enviar() {
    try {
      window.postMessage({ __sharpenupB3Data: true, hook: true,
        bets: Array.from(byBsid.values()), respostas: respostas, fim: fimReplay }, "*");
    } catch (e) {}
  }

  // ── captura passiva das respostas (summary/confirmation que a página já faz) ─────
  function forward(url, text) {
    const u = String(url);
    if (RX_SUM.test(u)) {
      const r = parseSummary(text);
      if (!r) return false;
      respostas++;
      const settled = /settled=1/i.test(u);
      for (const b of r.bets) if (b.bsid) mergeSummary(b, settled);
      enviar();
      return true;
    }
    if (RX_CONF.test(u)) {
      const bsid = _param(u, "bsid");
      const c = parseConfirmation(text);
      if (!c) return false;
      respostas++;
      if (bsid) mergeConf(bsid, c);
      enviar();
      return true;
    }
    return false;
  }

  function mergeSummary(b, settled) {
    const ex = byBsid.get(b.bsid) || { bsid: b.bsid };
    ex.aberta = b.bs === "0";
    ex.tp = b.tp; ex.stake = b.stake; ex.ts = b.ts; ex.oddFrac = b.oddFrac; ex.rt = b.rt; ex.tipo = b.tipo;
    ex.sels = b.sels;
    byBsid.set(b.bsid, ex);
  }
  function mergeConf(bsid, c) {
    const ex = byBsid.get(bsid) || { bsid: bsid };
    ex.code = c.br; ex.da = c.da; ex.legs = c.legs;
    if (c.ts != null) ex.ts = c.ts;
    if (c.rt != null && ex.rt == null) ex.rt = c.rt;   // não sobrescreve o RT do summary (realizado)
    if (!ex.tipo) ex.tipo = c.tipo;
    if (c.bs != null) ex.aberta = c.bs === "0";
    byBsid.set(bsid, ex);
  }

  // ── replay ativo ────────────────────────────────────────────────────────────────
  function _param(u, k) { try { return new URL(u, location.origin).searchParams.get(k) || ""; } catch (e) { return ""; } }
  function _hdrsToObj(h) {
    const o = {};
    try {
      if (!h) return o;
      if (typeof h.forEach === "function") h.forEach((v, k) => { o[k] = v; });
      else if (typeof h === "object") for (const k in h) o[k] = h[k];
    } catch (e) {}
    return o;
  }
  function capturarReq(url, method, headers) {
    if (reqSum || !RX_SUM.test(String(url))) return;
    reqSum = { url: String(url), method: (method || "GET"), headers: headers || {} };
    LOG("summary capturado p/ replay ·", reqSum.url.slice(0, 120));
    if (pedido) arrancar();
  }

  function _iso(ms) { try { return new Date(ms).toISOString(); } catch (e) { return ""; } }

  // Monta a URL de uma página de summary (settled + janela [from,to]).
  function urlSummary(settled, fromISO, toISO) {
    const u = new URL(reqSum.url, location.origin);
    u.searchParams.set("settled", settled ? "1" : "0");
    u.searchParams.set("from", fromISO);
    u.searchParams.set("to", toISO);
    return u.toString();
  }
  // URL do detalhe de um bilhete (a partir do lid/cid do summary).
  function urlConfirmation(settled, bsid) {
    const s = new URL(reqSum.url, location.origin);
    const u = new URL(s.origin + "/sportshistoryapi/confirmation");
    u.searchParams.set("settled", settled ? "1" : "0");
    u.searchParams.set("lid", s.searchParams.get("lid") || "");
    u.searchParams.set("cid", s.searchParams.get("cid") || "");
    u.searchParams.set("bsid", bsid);
    u.searchParams.set("cr", "0");
    return u.toString();
  }

  async function getText(url) {
    const r = await of.call(window, url, { method: "GET", headers: reqSum.headers, credentials: "include" });
    return await r.text();
  }

  // Varre UMA lista (settled 0/1) paginando pelo cursor PT até esgotar/janela/teto.
  async function varrerLista(settled) {
    const to = Date.now();
    const from = settled ? (to - Math.max(1, janelaDias) * 86400000) : (to - 400 * 86400000);
    const fromISO = _iso(from);
    let toISO = _iso(to), pag = 0, ultimoPT = null;
    while (pag < MAX_PAGINAS) {
      pag++;
      let txt;
      try { txt = await getText(urlSummary(settled, fromISO, toISO)); }
      catch (e) { LOG("erro replay summary:", e && e.message); break; }
      const r = parseSummary(txt);
      if (!r) break;
      respostas++;
      const antes = byBsid.size;
      for (const b of r.bets) if (b.bsid) mergeSummary(b, settled);
      enviar();
      if (byBsid.size === antes && !r.bets.length) break;   // página vazia → fim
      if (!r.cursor || r.cursor === ultimoPT) break;        // cursor não avançou → fim
      ultimoPT = r.cursor; toISO = r.cursor;
    }
  }

  // Busca o detalhe (confirmation) de cada bilhete sem `code`, com concorrência limitada.
  async function buscarDetalhes() {
    const alvos = [];
    for (const b of byBsid.values()) {
      if (b.code || confPedido.has(b.bsid)) continue;
      alvos.push(b);
      if (alvos.length >= MAX_CONF) break;
    }
    let i = 0;
    async function worker() {
      while (i < alvos.length) {
        const b = alvos[i++];
        confPedido.add(b.bsid);
        try {
          const txt = await getText(urlConfirmation(!b.aberta, b.bsid));
          respostas++;
          const c = parseConfirmation(txt);
          if (c) mergeConf(b.bsid, c);
        } catch (e) { LOG("erro replay confirmation:", e && e.message); }
        enviar();
      }
    }
    const workers = [];
    for (let w = 0; w < CONC; w++) workers.push(worker());
    await Promise.all(workers);
  }

  async function arrancar() {
    if (loopAtivo || fimReplay || !reqSum) return;
    loopAtivo = true;
    try {
      await varrerLista(true);    // resolvidas (janela de dias)
      await varrerLista(false);   // abertas (todas)
      await buscarDetalhes();     // jogo/mercado/código BR de cada bilhete
    } finally {
      loopAtivo = false;
      fimReplay = true;
      enviar();
    }
  }

  // O content script pede o acumulado ao iniciar o robô (com a janela de dias) → re-envia tudo
  // E arranca o replay. A 1ª resposta pode ter vindo no load (antes do content ouvir).
  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (!d || !d.__sharpenupB3Req) return;
    if (typeof d.dias === "number" && d.dias > 0) janelaDias = d.dias;
    pedido = true;
    enviar();
    arrancar();
  });

  // ── fetch ──
  if (of && !of.__suB3W) {
    const w = function (...a) {
      const url = (a[0] && a[0].url) || a[0];
      const opts = a[1] || (a[0] && typeof a[0] === "object" ? a[0] : null);
      try { if (RX_SUM.test(String(url))) capturarReq(url, opts && opts.method, _hdrsToObj(opts && opts.headers)); } catch (e) {}
      return of.apply(this, a).then((r) => {
        try { if (RX_SUM.test(String(url)) || RX_CONF.test(String(url))) r.clone().text().then((t) => forward(url, t)); } catch (e) {}
        return r;
      });
    };
    w.__suB3W = true;
    window.fetch = w;
  }

  // ── XMLHttpRequest ──
  const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send, osh = XMLHttpRequest.prototype.setRequestHeader;
  if (!os.__suB3W) {
    XMLHttpRequest.prototype.open = function (m, u) { this.__suB3U = u; this.__suB3M = m; this.__suB3H = {}; return oo.apply(this, arguments); };
    XMLHttpRequest.prototype.setRequestHeader = function (k, v) { try { this.__suB3H[k] = v; } catch (e) {} return osh.apply(this, arguments); };
    const s = function (body) {
      try {
        const u = this.__suB3U;
        if (RX_SUM.test(String(u))) capturarReq(u, this.__suB3M, this.__suB3H);
        if (RX_SUM.test(String(u)) || RX_CONF.test(String(u))) {
          this.addEventListener("load", () => { try { forward(u, this.responseText); } catch (e) {} });
        }
      } catch (e) {}
      return os.apply(this, arguments);
    };
    s.__suB3W = true;
    XMLHttpRequest.prototype.send = s;
  }
})();
