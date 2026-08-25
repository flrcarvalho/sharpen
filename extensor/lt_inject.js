// Mundo MAIN (Lottu — motor NGBras): lê as RESPOSTAS da API de bilhetes
// (`GET https://alpha-sb.ngbras.com/bet`) e **COMPLETA CADA BILHETE** com o detalhe
// (`GET /bet/{_id}`), porque a lista não traz as seleções.
//
// TRÊS CONSULTAS, e elas têm formas DIFERENTES — não é a mesma URL com outro filtro:
//   1. resolvidas → `/bet?initial_date=…Z&final_date=…Z&status=ALL`  (FAIXA, sem paginar)
//   2. abertas    → `/bet?status=OPEN&page=N`                        (paginado, sem datas)
//   3. detalhe    → `/bet/{_id}`                                     (um por bilhete)
//
// ⚠️ SEM `initial_date`/`final_date` A CASA RESPONDE `[]` COM HTTP 200. Não é erro, é lista
// vazia — o tipo de falha que faz parecer que a conta não tem aposta. Por isso o replay
// SEMPRE manda a faixa, e o `forward` só aceita array.
//
// ⚠️ AUTENTICAÇÃO POR HEADER (`authorization` + `ngx-source`), não cookie. A API é de OUTRA
// origem (`ngbras.com` × `lottu.bet.br`): sem os headers reais a chamada morre no CORS antes
// de chegar ao servidor. Daí aprender a requisição em vez de montá-la.
//
// ⚠️ O DETALHE POR ITEM é o anti-padrão do CLAUDE.md ("API externa por item = latência E
// falha multiplicadas. Peça a FAIXA"). Aqui ele é inevitável — a lista simplesmente não tem
// as seleções, e sem elas não há coluna Data nem descrição. O que dá para fazer é limitar:
// a JANELA DE DIAS corta antes de detalhar, e há teto absoluto. Na 1ª captura de uma conta
// antiga isso custa caro; nas seguintes, quase nada.
//
// NÃO DECIDE NADA: normaliza e sobe o bilhete cru (com `events` anexado). Estado
// desconhecido sobe como está; quem traduz é o `content.js` + `casas/CASA_LOTTU.md`.
(function () {
  const RX_LISTA = /\/bet(\?|$)/i;                 // a lista (com ou sem query)
  const RX_DET = /\/bet\/[a-f0-9]{24}/i;           // o detalhe de um bilhete
  const porCodigo = new Map();                     // code(string) → bilhete cru (+ events)
  const detalhados = new Set();                    // _id já detalhado (não repete a chamada)
  let respostas = 0;
  let reqCtx = null;                               // {origin, headers} de uma requisição REAL
  let pedido = false, loopAtivo = false, fimReal = false;
  let janelaDias = 45;                             // o robô sobrescreve
  const TETO_PAGINAS = 40;                         // anti-loop das abertas
  const TETO_DETALHES = 400;                       // teto absoluto de chamadas por item
  const LOG = (...a) => { try { console.log("[SharpenUp lt_inject]", ...a); } catch (e) {} };
  LOG("hook instalado em", location.href);

  const of = window.fetch;                         // fetch ORIGINAL — o replay usa este

  const ehAberta = (b) => b && b.status === "OPEN";

  // Resolvida vence aberta, e detalhe vence lista: o bilhete da lista NÃO tem `events`, e
  // perder o detalhe já obtido custaria outra chamada por item.
  function guardar(b) {
    if (!b || b.code == null) return false;
    const k = String(b.code);
    const ex = porCodigo.get(k);
    if (ex) {
      if (!ehAberta(ex) && ehAberta(b)) return false;              // não rebaixa
      if (Array.isArray(ex.events) && !Array.isArray(b.events)) {  // não perde o detalhe
        porCodigo.set(k, Object.assign({}, b, { events: ex.events }));
        return false;
      }
    }
    porCodigo.set(k, b);
    return !ex;
  }

  function enviar() {
    try {
      window.postMessage({
        __sharpenupLTData: true, hook: true, respostas: respostas,
        bets: Array.from(porCodigo.values()), fim: fimReal,
      }, "*");
    } catch (e) {}
  }

  // Processa uma resposta (passiva OU do replay). A API devolve ARRAY na lista e OBJETO no
  // detalhe — por isso os dois ramos.
  function forward(url, text) {
    if (typeof text !== "string") return null;
    const u = String(url);
    if (!RX_LISTA.test(u) && !RX_DET.test(u)) return null;
    let j;
    try { j = JSON.parse(text); } catch (e) { return null; }

    if (RX_DET.test(u)) {
      if (!j || !j.code) return null;
      respostas++;
      guardar(j);
      if (j._id) detalhados.add(String(j._id));
      enviar();
      return { n: 1, novos: 0, detalhe: true };
    }

    if (!Array.isArray(j)) return null;
    respostas++;
    let novos = 0;
    for (const b of j) { if (guardar(b)) novos++; }
    LOG("bilhetes na resposta:", j.length, "· novos:", novos, "· total:", porCodigo.size);
    enviar();
    return { n: j.length, novos: novos, detalhe: false };
  }

  // ── replay ativo ──────────────────────────────────────────────────────────────
  function _hdrsToObj(h) {
    const o = {};
    try {
      if (!h) return o;
      if (typeof h.forEach === "function") h.forEach((v, k) => { o[k] = v; });
      else if (typeof h === "object") for (const k in h) o[k] = h[k];
    } catch (e) {}
    return o;
  }

  // Guarda os headers de uma requisição REAL. Sem `authorization` não adianta: guardar uma
  // chamada sem ele deixaria o replay batendo em 401/CORS para sempre.
  function capturarReq(url, headers) {
    if (reqCtx) return;
    const u = String(url);
    if (!RX_LISTA.test(u) && !RX_DET.test(u)) return;
    const h = headers || {};
    const temAuth = Object.keys(h).some((k) => k.toLowerCase() === "authorization");
    if (!temAuth) return;
    let origin = "";
    try { origin = new URL(u).origin; } catch (e) { return; }
    reqCtx = { origin: origin, headers: h };
    LOG("requisição capturada p/ replay · origin:", origin);
    if (pedido) arrancarReplay();
  }

  const _iso = (ts) => new Date(ts).toISOString();

  async function buscar(caminho) {
    const r = await of.call(window, reqCtx.origin + caminho, {
      method: "GET", headers: reqCtx.headers, credentials: "omit",
    });
    return forward(reqCtx.origin + caminho, await r.text());
  }

  // 1) RESOLVIDAS por faixa. Uma chamada resolve o período inteiro — a casa não pagina aqui.
  async function puxarFaixa() {
    const agora = Date.now();
    const dias = Math.max(1, janelaDias);
    const de = _iso(agora - dias * 86400000), ate = _iso(agora + 86400000);
    try {
      const info = await buscar("/bet?initial_date=" + encodeURIComponent(de) +
                                "&final_date=" + encodeURIComponent(ate) + "&status=ALL");
      LOG("faixa", dias, "dia(s):", info ? info.n : "sem resposta", "bilhete(s)");
    } catch (e) { LOG("erro na faixa:", e && e.message); }
  }

  // 2) ABERTAS, que têm forma própria. Nunca cortadas por data: aposta colocada há meses
  // pode ter jogo amanhã.
  async function puxarAbertas() {
    for (let pagina = 0; pagina < TETO_PAGINAS; pagina++) {
      let info = null;
      try { info = await buscar("/bet?status=OPEN&page=" + pagina); }
      catch (e) { LOG("erro nas abertas, pág", pagina, ":", e && e.message); return; }
      if (!info) return;
      if (info.n === 0) { LOG("abertas: fim (lista vazia) na pág", pagina); return; }
      if (info.novos === 0) { LOG("abertas: página sem bilhete novo → para"); return; }
    }
  }

  // 3) DETALHE por item — o caro. Só para bilhete que ainda não tem `events`, um de cada
  // vez (em paralelo a casa devolveria 429 e nós perderíamos o lote inteiro).
  async function puxarDetalhes() {
    const pendentes = Array.from(porCodigo.values())
      .filter((b) => b && b._id && !Array.isArray(b.events) && !detalhados.has(String(b._id)));
    if (!pendentes.length) return;
    LOG("detalhe por item:", pendentes.length, "bilhete(s) — é a parte cara desta casa");
    let n = 0;
    for (const b of pendentes) {
      if (n >= TETO_DETALHES) { LOG("teto de", TETO_DETALHES, "detalhes atingido"); break; }
      n++;
      try { await buscar("/bet/" + b._id); }
      catch (e) { LOG("erro no detalhe de", b.code, ":", e && e.message); }
    }
  }

  async function arrancarReplay() {
    if (loopAtivo || fimReal || !reqCtx) return;
    loopAtivo = true;
    try {
      await puxarFaixa();
      await puxarAbertas();
      await puxarDetalhes();
    } finally {
      loopAtivo = false;
      fimReal = true;
      enviar();
    }
  }

  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (!d || !d.__sharpenupLTReq) return;
    if (typeof d.dias === "number" && d.dias > 0) janelaDias = d.dias;
    pedido = true;
    enviar();
    arrancarReplay();
  });

  // ── fetch ──
  if (of && !of.__suLTW) {
    const w = function (...a) {
      const url = (a[0] && a[0].url) || a[0];
      const opts = a[1] || (a[0] && typeof a[0] === "object" ? a[0] : null);
      try {
        const h = _hdrsToObj((a[0] && a[0].headers) || (opts && opts.headers));
        capturarReq(url, h);
      } catch (e) {}
      return of.apply(this, a).then((r) => {
        try { r.clone().text().then((t) => forward(url, t)); } catch (e) {}
        return r;
      });
    };
    w.__suLTW = true;
    window.fetch = w;
  }

  // ── XMLHttpRequest ──
  const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send, osh = XMLHttpRequest.prototype.setRequestHeader;
  if (!os.__suLTW) {
    XMLHttpRequest.prototype.open = function (m, u) { this.__suLTU = u; this.__suLTH = {}; return oo.apply(this, arguments); };
    XMLHttpRequest.prototype.setRequestHeader = function (k, v) { try { this.__suLTH[k] = v; } catch (e) {} return osh.apply(this, arguments); };
    const s = function () {
      try {
        if (RX_LISTA.test(String(this.__suLTU)) || RX_DET.test(String(this.__suLTU))) {
          capturarReq(this.__suLTU, this.__suLTH);
          this.addEventListener("load", () => { try { forward(this.__suLTU, this.responseText); } catch (e) {} });
        }
      } catch (e) {}
      return os.apply(this, arguments);
    };
    s.__suLTW = true;
    XMLHttpRequest.prototype.send = s;
  }
})();
