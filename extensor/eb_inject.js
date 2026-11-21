// Mundo MAIN (só na EpicBet, `epicbet.com`): BUSCA a lista de apostas da própria casa e
// repassa ao content script. Plataforma PRÓPRIA, API tRPC (recon s462, 21/11/2026, Chrome do
// Feca, painel "My Bets"):
//
//   GET /s/sport-bet/user/ticket.listWithMatchInfo?input=<JSON>      (só o COOKIE)
//       input = { limit, offset, language, filter: "pending" | "settled" }
//   → { result: { data: { tickets: [ { bet, cashout, sequence, type, createdAt, … } ], count } } }
//
// O painel pede 3 por página e anda por botões: ele nunca baixa a lista inteira. O inject pede
// ele mesmo as duas listas, de 25 em 25, até o `count`.
//
// ⚠ `limit` MÁXIMO 25 (com 50 a API devolve 400 `too_big`).
// ⚠ `filter` OBRIGATÓRIO, só `pending` ou `settled` (sem ele, ou com `all`, 400 `invalid_union`).
// ⚠ Offset além do fim devolve `tickets: []` (não repete a página 1). O fim é o `count`.
// ⚠ NÃO HÁ CAMPO DE RETORNO: o "Payout" do card é `stake × odds`. Quem decide é o
//   `formatTicketEB`, nunca este arquivo.
// ⚠ `bet.odds` já é a odd EFETIVA (perna pushed/half_won recalculada pela casa).
// ⚠ O CÓDIGO do bilhete é o `sequence`: o "ID" do card (1, 2, 3… por conta), o mesmo que a base
//   já tinha por print (s462: 10 bilhetes da conta do Gabriel, códigos 1 a 10). O `bet.id`
//   (8 dígitos, único na casa) sobe junto como `betId`, só para conferir.
//
// O inject NÃO decide nada: normaliza (ISO → epoch) e sobe o `status` cru.
(function () {
  // ── CRU para o servidor (s409, Projeto Ficha Sharpen) ───────────────────────────────
  // O ticket da casa, VERBATIM, ao lado do normalizado (campo `cru` da mensagem). Erro aqui
  // nunca sobe: sem cru, a captura de hoje segue igual. `codigo` = o `[Código: …]` do texto.
  const _cruDe = new WeakMap();
  function _marcarCru(b, cru) { try { _cruDe.set(b, cru); } catch (e) {} }
  function _crus(lista) {
    const out = [];
    try {
      for (const b of lista || []) {
        const c = _cruDe.get(b);
        if (!c || !b.id) continue;
        out.push({ codigo: String(b.id), cru: c });
      }
    } catch (e) {}
    return out;
  }

  // Só a LISTA. `ticket.getStats`, `ticket.getAvailableFilters` e o cashout não casam.
  const RX = /\/s\/sport-bet\/user\/ticket\.listWithMatchInfo(?:[?#]|$)/i;
  const CAMINHO = "/s/sport-bet/user/ticket.listWithMatchInfo";
  const LIMITE = 25;                           // máximo aceito pela API (medido)
  const TETO_PAGINAS = 200;                    // por lista: 5.000 bilhetes
  const byId = new Map();                      // sequence → bilhete normalizado
  let respostas = 0;                           // respostas VÁLIDAS do endpoint (autodiagnóstico)
  let loopAtivo = false, fimBusca = false, repetir = false;
  const LOG = (...a) => { try { console.log("[SharpenUp eb_inject]", ...a); } catch (e) {} };
  LOG("hook instalado em", location.href);

  const of = window.fetch;
  const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send;

  // ── normalização ─────────────────────────────────────────────────────────────────────
  const _n = (v) => {
    if (v == null || v === "") return null;
    const x = Number(v);
    return isFinite(x) ? x : null;
  };
  const _epoch = (s) => {
    const t = Date.parse(String(s || ""));
    return isFinite(t) ? t / 1000 : null;
  };

  function parsePerna(s) {
    if (!s) return null;
    const i = s.selectionInfo || {}, m = s.matchScoreInfo || {};
    return {
      status: String(s.status == null ? "" : s.status),   // pending · won · lost · pushed · half_won … (cru)
      odd: _n(s.odds),
      inicio: _epoch(i.matchStart),                       // início do evento (UTC)
      esporte: String(m.sportEntityName || ""),           // "Football", "eSports" (cru)
      mercado: String(i.marketName || ""),                // "Goals Handicap"
      linhaMercado: i.marketLine == null ? "" : String(i.marketLine),   // "0 - 0.25"
      selecao: String(i.outcomeName || ""),               // "FC Voluntari"
      linhaSelecao: i.outcomeLine == null ? "" : String(i.outcomeLine), // "+0.25"
      jogo: String(i.matchName || ""),                    // "Botosani - FC Voluntari"
      liga: String(i.leagueName || ""),
      aoVivo: String(s.product || "") === "live",
      betBuilder: !!(i.betBuilderSelectionInfo || (s.selectionExtra && s.selectionExtra.betbuilderInfo)),
    };
  }

  function parseTicket(t) {
    const b = t && t.bet;
    if (!b || t.sequence == null || !isFinite(Number(t.sequence))) return null;
    return {
      id: String(Number(t.sequence)),            // "11": o "ID" do card, o código do bilhete
      betId: b.id == null ? "" : String(b.id),   // 39939822: o id interno da casa
      status: String(b.status == null ? "" : b.status),      // pending · won · lost … (cru)
      tipo: String(t.type || ""),                // combo (o único medido)
      stake: _n(b.stake),
      odd: _n(b.odds),                           // a EFETIVA, a do card
      moeda: String(b.currency || ""),
      boost: b.oddsBoost == null ? null : b.oddsBoost,
      cashouts: Array.isArray(b.cashouts) ? b.cashouts : [],
      ts: _epoch(t.createdAt),                   // colocação
      sels: (Array.isArray(b.selections) ? b.selections : []).map(parsePerna).filter(Boolean),
    };
  }

  // Heartbeat: SEMPRE hook:true + respostas, mesmo com 0 bilhetes.
  function enviar() {
    try {
      const lista = Array.from(byId.values());
      window.postMessage({
        __sharpenupEBData: true, hook: true,
        bilhetes: lista, respostas: respostas, fim: fimBusca, cru: _crus(lista),
      }, "*");
    } catch (e) {}
  }

  // A versão LIQUIDADA vence a aberta.
  const _aberta = (b) => b.status === "pending";
  function guardar(b) {
    const ex = byId.get(b.id);
    if (!ex || _aberta(ex) || !_aberta(b)) byId.set(b.id, b);
  }

  // Processa uma resposta da lista; devolve {n, count}, ou null se não era a lista.
  function forward(url, text) {
    if (!RX.test(String(url)) || typeof text !== "string") return null;
    let j;
    try { j = JSON.parse(text); } catch (e) { return null; }
    const d = j && j.result && j.result.data;
    if (!d || !Array.isArray(d.tickets)) return null;   // erro tRPC (sessão caída, 400)
    respostas++;
    for (const raw of d.tickets) {
      const b = parseTicket(raw);
      if (b) { _marcarCru(b, raw); guardar(b); }
    }
    LOG("bilhetes na resposta:", d.tickets.length, "· total:", byId.size, "· count", d.count);
    enviar();
    return { n: d.tickets.length, count: _n(d.count) };
  }

  // ── busca ativa ──────────────────────────────────────────────────────────────────────
  // GET pelo `fetch` ORIGINAL (não passa pelo gancho, que processaria duas vezes).
  function urlDe(filtro, offset) {
    const input = { limit: LIMITE, offset: offset, language: "en", filter: filtro };
    return new URL(CAMINHO + "?input=" + encodeURIComponent(JSON.stringify(input)), location.href).href;
  }

  async function buscarLista(filtro) {
    let offset = 0;
    for (let pg = 0; pg < TETO_PAGINAS; pg++) {
      const url = urlDe(filtro, offset);
      let res = null;
      try {
        const r = await of.call(window, url, {
          method: "GET", credentials: "include", headers: { Accept: "application/json" },
        });
        res = forward(url, await r.text());
      } catch (e) { LOG("busca falhou", filtro, String(e)); return; }
      if (!res) { LOG("busca parou", filtro, "· resposta não é lista"); return; }
      if (!res.n) return;                        // além do fim: lista vazia
      offset += res.n;                           // anda pelo que VOLTOU, não pelo pedido
      if (res.count != null && offset >= res.count) return;
    }
    LOG("teto de páginas", filtro);
  }

  async function arrancar() {
    if (loopAtivo) return;
    loopAtivo = true;
    try {
      await buscarLista("pending");
      await buscarLista("settled");
    } finally {
      loopAtivo = false;
      fimBusca = true;
      enviar();
      if (repetir) { repetir = false; fimBusca = false; byId.clear(); arrancar(); }
    }
  }

  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (!d || !d.__sharpenupEBReq) return;
    // Pedido novo é rodada NOVA (lição da s393, DEX Sport): o acumulado velho não é reenviado.
    if (loopAtivo) { repetir = true; return; }
    fimBusca = false;
    byId.clear();
    enviar();
    arrancar();
  });

  // ── fetch: a página buscando a lista (o painel pede 3 por vez) ──
  if (of && !of.__suEBW) {
    const w = function (...a) {
      const url = (a[0] && a[0].url) || a[0];
      const metodo = String((a[1] && a[1].method) || (a[0] && a[0].method) || "GET").toUpperCase();
      return of.apply(this, a).then((r) => {
        try {
          if (metodo === "GET" && RX.test(String(url))) r.clone().text().then((t) => forward(url, t)).catch(() => {});
        } catch (e) {}
        return r;
      });
    };
    w.__suEBW = true;
    window.fetch = w;
  }

  // ── XMLHttpRequest (rede de segurança: hoje a página usa fetch) ──
  if (!os.__suEBW) {
    XMLHttpRequest.prototype.open = function (m, u) { this.__suEBU = u; this.__suEBM = m; return oo.apply(this, arguments); };
    const s = function () {
      try {
        if (String(this.__suEBM || "GET").toUpperCase() === "GET" && RX.test(String(this.__suEBU))) {
          this.addEventListener("load", () => { try { forward(this.__suEBU, this.responseText); } catch (e) {} });
        }
      } catch (e) {}
      return os.apply(this, arguments);
    };
    s.__suEBW = true;
    XMLHttpRequest.prototype.send = s;
  }
})();
