// Mundo MAIN — Vem com Sorte (`vemcomsorte.com`), plataforma PRÓPRIA (s467).
//
//   POST /api/bettor/bet:history          (no MESMO domínio da aba, Vue + XHR)
//     corpo  {ascending:false, limit:N, filter:{dateRange:{from,to}, statuses:[]}, token?}
//     header Authorization: <authToken>  (UUID cru, SEM "Bearer"; o app manda também
//            x-session-token com o mesmo valor, x-project-id, x-language e x-currency)
//   → {data:[…] | null, hasMore, nextToken?, metadata:{eventsData, eventsStatuses}}
//
// O que o recon mediu (26/11/2026, Chrome do Feca, conta logada):
//   • A TELA É ESTREITA: o painel "Minhas Apostas" pede 90 dias, 20 por vez, e só quando o
//     usuário abre o painel. Quem garante a cobertura é o replay.
//   • A FRIO FUNCIONA: o token mora em `localStorage.authToken` e só o `Authorization` basta
//     (medido: Authorization sozinho → 200; x-session-token sozinho → 401; nada → 401). O inject
//     não depende de o usuário abrir o painel (lição da SportingBet, s305). Se a página fizer a
//     chamada, os headers dela são aprendidos e têm precedência.
//   • PAGINAÇÃO por `token` NO CORPO (o `nextToken` da resposta anterior). `nextToken` no corpo
//     é IGNORADO pela casa (devolve a 1ª página de novo — medido 6 vezes). Fim AUTORITATIVO:
//     `hasMore:false` (e aí não vem `nextToken`).
//   • JANELA MÁXIMA ~123 dias: com `from` mais antigo a casa devolve 400 PRECONDITION_FAILED e
//     DIZ o piso ("Field 'from'=… must be greater or equal to <epoch ms>"). O inject pede 120
//     dias e, se a casa recusar, recua para o piso que ela mesma informou. `filter.dateRange`
//     é obrigatório (sem ele: 400).
//   • LISTA VAZIA VOLTA `data: null`, não `[]`. É resposta válida, não erro.
//   • `limit` 1000 foi aceito sem erro (a conta tinha 7). O inject pede 100 e anda pelo token.
//
// DINHEIRO EM CENTAVOS: `money.amount` 25000 com `money.multiplier` 100 = R$ 250,00. O inject
// divide pelo `multiplier` que a CASA informa; sem ele, o valor sobe nulo (nunca chuta 100).
//
// O inject NÃO decide nada: `status` (UNSETTLED/WIN/LOSE/VOID/CASHOUT/HALF_WIN/HALF_LOSE, enum
// do bundle) e `type` (SINGLE/MULTIPLE/SYSTEM/FLEXIBLE/ONE_CUT) sobem crus; quem lê é o
// `formatTicketVCS` (content.js) e quem traduz é a `casas/CASA_VEMCOMSORTE.md`.
//
// ⚠ O TOKEN NÃO SAI DAQUI. Ele vive só em memória para o replay; a mensagem ao content leva o
// bilhete normalizado e o cru da casa (que não tem nada da sessão).
(function () {
  // ── CRU para o servidor (s409, Projeto Ficha Sharpen) ───────────────────────────────
  // O objeto da CASA de onde cada bilhete saiu, VERBATIM, para o servidor montar a Ficha
  // (`app/adaptadores/vcs.py`). O bilhete da casa já traz tudo o que a Ficha usa (nomes de
  // esporte, liga, evento, mercado e seleção dentro de cada `outcome`): não há tabela irmã.
  const _cruDe = new WeakMap();
  function _marcarCru(b, cru) { try { _cruDe.set(b, cru); } catch (e) {} }
  function _crus(lista) {
    const out = [];
    try {
      for (const b of lista || []) {
        const c = _cruDe.get(b);
        if (!c || b.id == null || b.id === "") continue;
        out.push({ codigo: String(b.id), cru: c });
      }
    } catch (e) {}
    return out;
  }

  const RX = /\/api\/bettor\/bet:history/i;
  const URL_LISTA = "/api/bettor/bet:history";
  const JANELA_DIAS = 120;                     // a casa aceita ~123; 120 deixa folga ao relógio
  const LIMITE = 100;
  const TETO_PAGINAS = 200;

  const byId = new Map();                      // id(string) → bilhete normalizado
  let respostas = 0;                           // respostas VÁLIDAS do endpoint (autodiagnóstico)
  let reqHeaders = null;                       // headers de uma requisição REAL da página
  let loopAtivo = false, fimReplay = false, repetir = false;
  let semToken = false, erro = "";
  const LOG = (...a) => { try { console.log("[SharpenUp vcs_inject]", ...a); } catch (e) {} };
  LOG("hook instalado em", location.href);

  const of = window.fetch;
  const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send,
        osh = XMLHttpRequest.prototype.setRequestHeader;

  // ── normalização (casa → objeto limpo) ───────────────────────────────────────
  const _n = (v) => {
    if (v == null || v === "" || typeof v === "boolean") return null;
    const x = Number(v);
    return isFinite(x) ? x : null;
  };
  // Centavos → unidade, pelo multiplicador que a CASA declara. Sem ele: nulo.
  const _din = (v, mult) => {
    const x = _n(v);
    return (x == null || !(mult > 0)) ? null : Math.round((x / mult) * 1e8) / 1e8;
  };
  const _seg = (ms) => { const x = _n(ms); return x == null ? null : x / 1000; };

  function parsePerna(o) {
    if (!o) return null;
    const ev = o.event || {}, mk = o.market || {}, sp = o.sport || {}, tr = o.tournament || {}, rg = o.region || {};
    return {
      id: o.id != null ? String(o.id) : "",
      status: o.status != null ? String(o.status) : "",   // cru: UNSETTLED/WIN/LOSE/…
      odd: _n(o.odds),
      esporte: String(sp.name || ""),                      // "Tennis", "Ice Hockey" (inglês, como a API manda)
      liga: String(tr.name || ""),
      regiao: String(rg.name || ""),
      jogo: String(ev.name || ""),                         // "Frolunda HC vs IF Bjorkloven"
      inicio: _seg(ev.startTime),                          // epoch ms → s (o content converte p/ SP)
      mercado: String(mk.name || ""),                      // "Asian Handicap Games"
      selecao: String(o.name || ""),                       // "Aryan Lakshmanan"
      parametro: o.parameters != null ? String(o.parameters) : "",   // "+6.5", "21.5", ""
      aoVivo: o.sportService === "LIVE",
    };
  }

  function parseTicket(t) {
    if (!t || t.id == null || t.id === "") return null;
    const m = t.money || {};
    const mult = _n(m.multiplier);
    const boosts = [];
    for (const x of (Array.isArray(t.bonuses) ? t.bonuses : [])) {
      const at = (Array.isArray(x && x.options) ? x.options : []).find((o) => o && o.active);
      boosts.push({ nome: String((x && x.name) || ""), pct: at ? _n(at.bonusPercentage) : null });
    }
    return {
      id: String(t.id),                        // o "ID" da aposta (7 dígitos)
      tipo: t.type != null ? String(t.type) : "",
      status: t.status != null ? String(t.status) : "",
      moeda: String(m.currency || ""),
      stake: _din(m.amount, mult),
      retorno: _din(m.payout, mult),           // o "Saque" do card (0 na perdida e na aberta)
      potencial: _din(m.possiblePayout, mult), // o "Ganho possível" da aberta (já com o boost)
      bonus: _din(m.bonus, mult),              // parte do retorno que é o Combo Boost
      odd: _n(t.initialOdds) != null ? _n(t.initialOdds) : _n(t.odds),   // completa (card trunca em 2)
      oddTela: _n(t.odds),                     // a que o card mostra ("Odds totais")
      ts: _seg(t.createTime),                  // colocação, epoch s
      atualizada: _seg(t.updateTime),
      cashoutElegivel: !!t.cashoutEligible,
      corte: _n(t.cutPercentage),
      boosts: boosts,
      sels: (Array.isArray(t.outcomes) ? t.outcomes : []).map(parsePerna).filter(Boolean),
    };
  }

  // Heartbeat: SEMPRE hook:true + respostas, mesmo com 0 bilhetes.
  function enviar() {
    try {
      const lista = Array.from(byId.values());
      window.postMessage({
        __sharpenupVCSData: true, hook: true,
        bilhetes: lista, respostas: respostas, fim: fimReplay,
        semToken: semToken, erro: erro,
        cru: _crus(lista),
      }, "*");
    } catch (e) {}
  }

  // A versão LIQUIDADA vence a aberta (o dinheiro só é final depois de liquidado).
  function guardar(b) {
    const ex = byId.get(b.id);
    if (!ex || ex.status === "UNSETTLED" || b.status !== "UNSETTLED") byId.set(b.id, b);
  }

  // Processa uma resposta; devolve {n, novos, hasMore, nextToken} p/ o replay, ou null.
  function forward(url, text) {
    if (!RX.test(String(url)) || typeof text !== "string") return null;
    let j;
    try { j = JSON.parse(text); } catch (e) { return null; }
    // `data: null` é lista VAZIA (medido). Corpo de erro (`code`/`message`) não conta.
    if (!j || typeof j !== "object" || !("data" in j) || !(j.data === null || Array.isArray(j.data))) return null;
    respostas++;
    const lista = j.data || [];
    let novos = 0;
    for (const raw of lista) {
      const b = parseTicket(raw);
      if (!b) continue;
      if (!byId.has(b.id)) novos++;
      _marcarCru(b, raw);
      guardar(b);
    }
    LOG("bilhetes na resposta:", lista.length, "· novos:", novos, "· total:", byId.size, "· hasMore:", j.hasMore);
    enviar();
    return { n: lista.length, novos: novos, hasMore: j.hasMore === true, nextToken: j.nextToken || "" };
  }

  // ── replay ───────────────────────────────────────────────────────────────────
  function _tokenLocal() {
    try {
      const ls = window.localStorage;
      let v = ls && ls.getItem("authToken");
      if (!v) return "";
      v = String(v).trim();
      if (v.charAt(0) === "\"") { try { v = String(JSON.parse(v)); } catch (e) {} }
      return v;
    } catch (e) { return ""; }
  }
  function _temAuth(h) {
    for (const k in (h || {})) if (String(k).toLowerCase() === "authorization" && h[k]) return true;
    return false;
  }
  function headersReplay() {
    const h = {};
    if (reqHeaders) for (const k in reqHeaders) h[k] = reqHeaders[k];
    if (!_temAuth(h)) {
      const tok = _tokenLocal();
      if (!tok) return null;
      h["Authorization"] = tok;
      h["x-session-token"] = tok;
    }
    let temCT = false;
    for (const k in h) if (String(k).toLowerCase() === "content-type") temCT = true;
    if (!temCT) h["Content-Type"] = "application/json";
    return h;
  }

  async function pedir(corpo, headers) {
    try {
      const r = await of.call(window, URL_LISTA, {
        method: "POST", credentials: "include", headers: headers, body: JSON.stringify(corpo),
      });
      const text = await r.text();
      return { ok: r.ok, status: r.status, text: text };
    } catch (e) { return { ok: false, status: 0, text: "" }; }
  }

  // O piso que a casa informa no 400 ("must be greater or equal to 1785073857365").
  const _piso = (text) => {
    const m = /greater or equal to (\d{12,})/.exec(String(text || ""));
    return m ? Number(m[1]) : null;
  };

  async function varrer() {
    const headers = headersReplay();
    if (!headers) { semToken = true; LOG("sem authToken: sessão deslogada"); return; }
    const to = Date.now();
    let from = to - JANELA_DIAS * 864e5;
    let token = "", recuou = false;
    for (let pg = 0; pg < TETO_PAGINAS; pg++) {
      const corpo = { ascending: false, limit: LIMITE, filter: { dateRange: { from: from, to: to }, statuses: [] } };
      if (token) corpo.token = token;
      const r = await pedir(corpo, headers);
      if (!r.ok) {
        const piso = r.status === 400 ? _piso(r.text) : null;
        if (piso && !recuou && !token) { recuou = true; from = piso + 60000; pg--; continue; }
        erro = (r.status === 401 || r.status === 403) ? "HTTP " + r.status + ": sessão caída, faça login e rode de novo"
                                                       : "HTTP " + r.status + " no histórico";
        LOG("replay parou ·", erro);
        return;
      }
      const res = forward(URL_LISTA, r.text);
      if (!res) { erro = "resposta fora do formato"; return; }
      // Fim AUTORITATIVO: a casa diz que não há mais. Página sem bilhete novo com `hasMore`
      // ainda ligado é laço (token que não avança): para em vez de girar até o teto.
      if (!res.hasMore || !res.nextToken) return;
      if (!res.novos) { LOG("token não avançou: parando"); return; }
      token = res.nextToken;
    }
    LOG("teto de páginas atingido");
  }

  async function arrancarReplay() {
    if (loopAtivo) return;
    loopAtivo = true;
    try { await varrer(); }
    finally {
      loopAtivo = false;
      fimReplay = true;
      enviar();
      if (repetir) { repetir = false; fimReplay = false; byId.clear(); semToken = false; erro = ""; arrancarReplay(); }
    }
  }

  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (!d || !d.__sharpenupVCSReq) return;
    // Pedido novo é rodada NOVA, a partir do zero (lição da s393, DEX Sport): o acumulado velho
    // não é reenviado como se fosse novo. Pedido durante a varredura fica marcado e roda ao fim.
    if (loopAtivo) { repetir = true; return; }
    fimReplay = false; semToken = false; erro = "";
    byId.clear();
    enviar();
    arrancarReplay();
  });

  // ── XMLHttpRequest (é por aqui que o app pede a lista) ──
  if (!os.__suVCSW) {
    XMLHttpRequest.prototype.open = function (m, u) { this.__suVCSU = u; this.__suVCSH = {}; return oo.apply(this, arguments); };
    XMLHttpRequest.prototype.setRequestHeader = function (k, v) { try { this.__suVCSH[k] = v; } catch (e) {} return osh.apply(this, arguments); };
    const s = function () {
      try {
        if (RX.test(String(this.__suVCSU))) {
          if (_temAuth(this.__suVCSH)) reqHeaders = Object.assign({}, this.__suVCSH);
          this.addEventListener("load", () => { try { forward(this.__suVCSU, this.responseText); } catch (e) {} });
        }
      } catch (e) {}
      return os.apply(this, arguments);
    };
    s.__suVCSW = true;
    XMLHttpRequest.prototype.send = s;
  }

  // ── fetch (rede de segurança: hoje o app usa XHR) ──
  if (of && !of.__suVCSW) {
    const w = function (...a) {
      const url = (a[0] && a[0].url) || a[0];
      const opts = a[1] || null;
      try {
        if (RX.test(String(url)) && opts && opts.headers) {
          const h = {};
          const src = opts.headers;
          if (typeof src.forEach === "function") src.forEach((v, k) => { h[k] = v; });
          else for (const k in src) h[k] = src[k];
          if (_temAuth(h)) reqHeaders = h;
        }
      } catch (e) {}
      return of.apply(this, a).then((r) => {
        try {
          if (RX.test(String(url))) {
            r.clone().text().then((t) => forward(url, t), (e) => LOG("clone falhou:", e && e.name));
          }
        } catch (e) {}
        return r;
      });
    };
    w.__suVCSW = true;
    window.fetch = w;
  }
})();
