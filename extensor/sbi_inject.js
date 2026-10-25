// Mundo MAIN (Sportsbet.io — plataforma própria, GraphQL): lê as apostas que a página pede e
// BUSCA a lista inteira ela mesma, repassando ao content script.
//
//   POST /graphql   { operationName, variables:{ first, after, language }, query }
//     SettledTicketsQuery → data.sportsbetTickets.myBettingHistory { edges[].node, pageInfo }
//     ActiveTicketsQuery  → data.sportsbetTickets.myActiveTickets  { edges[].node, pageInfo }
//
// PLATAFORMA PRÓPRIA (recon s428, 25/10/2026, conta do Feca em USDT). Apollo/GraphQL no MESMO
// domínio (`sportsbet.io/graphql`), o `sportsbetTickets` do grupo Yolo. Não é Altenar, BetBy,
// Kambi, BetConstruct nem softlabs. O WebSocket da página (`/graphql`, protocolo próprio
// `{eventName, eventData, token}`) só leva PING/PONG e assinaturas de bilhete novo: a lista vem
// por fetch.
//
// AUTH é `authorization: Bearer <JWT>`. O JWT é o cookie `token` (não é HttpOnly), então o
// replay arranca A FRIO, sem esperar requisição nenhuma da página. Medido: sem o header a
// resposta é HTTP 200 com `myBettingHistory: null` — ERRO VOLTA COM 200 E SEM `errors`; quem
// decide é a forma, nunca o status. O Bearer só com o JWT cru (sem "Bearer ") também volta
// `null`. O valor nunca sai deste arquivo: a mensagem para o content leva só `semToken`.
//
// O QUE FOI MEDIDO na API, com o token da sessão:
//   • DINHEIRO em 1e8 (unidade de cripto): `stakeAmount` "2500000000" = card 25,00 USDT;
//     `wonAmount` "10621770000" = 106,2177. ⚠ Medido só em USDT; outra moeda pode ter outra
//     escala — o cru sobe junto.
//   • `wonAmount` é o RETORNO (60,01 × 1,77 = 106,2177) e vem `null` na perdida. `maxWin` é o
//     potencial (stake × odd).
//   • A odd do CARD é `boostedOdds` do bilhete (5,83 no turbinado, onde `odds` = 5,71 e
//     `bets[].totalOdds` = 5,91). Sem turbo, `boostedOdds` = `odds`.
//   • A tela pede `first: 5` e depois `first: 20` com `after` (cursor `mongodbconnection:N`
//     em base64). `first` 100, 500 e 1000 aceitos. Fim AUTORITATIVO = `pageInfo.hasNextPage`
//     false. As ABERTAS também paginam (a tela pede `first: 100` sem `pageInfo`; o replay pede
//     com). Provado: `first: 5` + cursor = 16 únicos de 16, igual a `first: 100`.
//   • O `id` do bilhete é base64 de `SportsbetTicketsTicket:<ObjectId>`; o botão "ID" do card
//     copia o ObjectId (24 hex). É ele o `[Código:]`.
//
// NÃO DECIDE NADA: normaliza o bilhete e sobe o cru. `status` sobe como veio; quem traduz é o
// `formatTicketSBI` (content.js) + `casas/CASA_SPORTSBETIO.md`.
(function () {
  // ── CRU para o servidor (Projeto Ficha Sharpen) ─────────────────────────────────────
  // O `node` da casa, inteiro, num campo NOVO (`cru`) da mesma mensagem. O bilhete não tem
  // campo de identidade do cliente. Erro aqui nunca sobe.
  const _cruDe = new WeakMap();
  function _crus(lista) {
    const out = [];
    try {
      for (const b of lista || []) {
        const c = _cruDe.get(b);
        if (c && b.id) out.push({ codigo: String(b.id), cru: c });
      }
    } catch (e) {}
    return out;
  }

  const RX_GQL = /\/graphql(\?|$)/i;           // onde o token se aprende e a lista passa
  const PAGINA = 100;                          // aceito (medido até 1000); 100 é o passo seguro
  const TETO_PAGINAS = 300;                    // 300 × 100 = 30 mil bilhetes por lista
  const ESCALA = 1e8;                          // dinheiro em 1e8 (medido em USDT)

  const byId = new Map();                      // id(string) → bilhete normalizado
  let respostas = 0;                           // respostas VÁLIDAS da lista (autodiagnóstico)
  let auth = "";                               // `authorization` visto numa chamada real (nunca sai daqui)
  let pedido = false;                          // o robô já pediu → pode arrancar o replay
  let loopAtivo = false;                       // trava: um replay por vez
  let fimReplay = false;                       // a varredura terminou
  let repetir = false;                         // pedido chegou durante a varredura → roda de novo
  let erro = "";                               // último erro do replay (vai no autodiagnóstico)
  const LOG = (...a) => { try { console.log("[SharpenUp sbi_inject]", ...a); } catch (e) {} };
  LOG("hook instalado em", location.href);

  const of = window.fetch;                     // fetch ORIGINAL — o replay usa este

  // ── as queries (cópia literal da página, s428; só o `pageInfo` das abertas é acrescentado) ──
  const FRAG = "fragment TicketFragment on SportsbetTicketsTicket {\n  id\n  __typename\n  status\n  wonAmount: won_amount\n  placedAt: placed_at\n  stakeAmount: stake_amount\n  maxWin: max_win\n  odds\n  boostedOdds: boosted_odds\n  boosterTicket: boosted_ticket\n  betType: bet_type\n  multiboost\n  insuranceActive\n  cashBackStake\n  giveaways(language: $language) {\n    totalTokenCount\n    matchedGiveaways {\n      name\n      termsUrl\n      tokenCount\n      __typename\n    }\n    __typename\n  }\n  bets {\n    id\n    __typename\n    amount\n    totalOdds: total_odds\n    freeBet: free_bet\n    cashbackPercent: cashback_percent\n    boostType\n    selections {\n      id\n      __typename\n      status\n      voidFactor: void_factor\n      boostedOdds: boosted_odds\n      odds\n      eventStartTime: event_start_time\n      eventScore: event_score\n      selectionId: selection_id\n      eventId: event_id\n      name(language: $language)\n      eventName: event_name(language: $language)\n      marketName: market_name(language: $language)\n      enName: market_name(language: \"en\")\n      provider_product_id\n      deductions {\n        applied_at\n        deduction_value\n        __typename\n      }\n      market {\n        id\n        selections {\n          id\n          name(language: $language)\n          providerProductId\n          active\n          odds\n          __typename\n        }\n        __typename\n      }\n      sport {\n        id\n        __typename\n        iconCode\n        scoreType\n        slug\n      }\n    }\n  }\n  cashoutOffer {\n    id\n    __typename\n    cashoutAvailable\n    maxCashout\n  }\n  cashout {\n    id\n    __typename\n    instances {\n      __typename\n      performedAt\n      amount\n      type\n      paidAmount\n      oddsAtCashout\n    }\n  }\n  cashoutAllowed\n  currencyCode\n  racingMeta {\n    track\n    countryCode\n    meetingDate\n    raceNumber\n    raceClass\n    prizeMoney\n    prizeCurrency\n    selectionId\n    programNumber\n    barrierNumber\n    __typename\n  }\n}\n";
  const _query = (nome, campo) => "query " + nome + "($language: String, $first: Int, $after: String) {\n  sportsbetTickets {\n    id\n    " + campo + "(first: $first, after: $after) {\n      edges {\n        node {\n          ...TicketFragment\n          __typename\n        }\n        __typename\n      }\n      pageInfo {\n        hasNextPage\n        endCursor\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n\n" + FRAG;
  const LISTAS = [
    { op: "SettledTicketsQuery", campo: "myBettingHistory" },
    { op: "ActiveTicketsQuery", campo: "myActiveTickets" },
  ];

  // ── normalização ─────────────────────────────────────────────────────────────
  const _n = (v) => {
    if (v == null || v === "") return null;
    const x = Number(v);
    return isFinite(x) ? x : null;
  };
  const _s = (v) => (v == null ? "" : String(v));
  // Espaço e TAB colapsados: TAB é a coluna do TSV, e a casa escreve "longa  (inc. …)".
  const _limpo = (v) => _s(v).replace(/\s+/g, " ").trim();
  const _din = (v) => { const x = _n(v); return x == null ? null : x / ESCALA; };
  const _caminho = (u) => { try { return new URL(_s(u), location.href).pathname; } catch (e) { return ""; } };

  // `U3BvcnRz…` → "SportsbetTicketsTicket:6addf2d1bf9e9d0001d7fda3" → o ObjectId do card.
  function _codigo(id) {
    const s = _s(id);
    try {
      const t = atob(s);
      const i = t.lastIndexOf(":");
      if (i >= 0 && /^[0-9a-f]{24}$/i.test(t.slice(i + 1))) return t.slice(i + 1).toLowerCase();
    } catch (e) {}
    return s;
  }

  function parsePerna(s) {
    if (!s) return null;
    return {
      status: _n(s.status),                     // 0 pendente · 1 ganha · 2 perdida (card) — CRU
      anulada: _n(s.voidFactor),                // 1 = anulada (cinza no card), qualquer status
      odd: _n(s.odds),
      oddTurbo: _n(s.boostedOdds),              // a odd da perna com o turbo, ou null
      selecao: _limpo(s.name),                  // no Bet Builder, as seleções juntas por ";"
      mercado: _limpo(s.marketName),            // "Bet Builder" no Criar Aposta
      jogo: _limpo(s.eventName),                // "Cadiz CF - AD Ceuta" / "A vs B" no tênis
      esporte: _s(s.sport && s.sport.slug),     // soccer · basketball · tennis … (slug CRU)
      inicio: _n(s.eventStartTime),             // unix em SEGUNDOS
      placar: _limpo(s.eventScore),
    };
  }

  function parseTicket(n) {
    if (!n || n.id == null) return null;
    const bets = Array.isArray(n.bets) ? n.bets : [];
    const sels = [].concat(...bets.map((b) => (b && Array.isArray(b.selections) ? b.selections : [])));
    const inst = n.cashout && Array.isArray(n.cashout.instances) ? n.cashout.instances : [];
    return {
      id: _codigo(n.id),                        // o ObjectId que o botão "ID" do card copia
      status: _s(n.status),                     // ACTIVE · SETTLED · ARCHIVED (CRU)
      tipoAposta: _s(n.betType),                // "0" simples · "1" múltipla (CRU)
      moeda: _s(n.currencyCode).toUpperCase(),  // "USDT" — a moeda da CONTA
      stake: _din(n.stakeAmount),
      retorno: _din(n.wonAmount),               // null na perdida e na aberta
      potencial: _din(n.maxWin),
      odd: _n(n.boostedOdds) != null ? _n(n.boostedOdds) : _n(n.odds),   // a odd do CARD
      oddSemTurbo: _n(n.odds),
      turbinado: n.boosterTicket === true,
      apostas: bets.length,                     // 1 em toda a amostra; > 1 = sistema (sem amostra)
      freebet: bets.some((b) => b && b.freeBet === true),
      cashouts: inst.map((i) => ({ valor: _s(i && i.amount), pago: _s(i && i.paidAmount),
                                   tipo: _s(i && i.type), odd: _n(i && i.oddsAtCashout) })),
      colocada: _n(n.placedAt),                 // unix em SEGUNDOS
      pernas: sels.map(parsePerna).filter(Boolean),
    };
  }

  // Emite SEMPRE hook:true + respostas (heartbeat), mesmo com 0 bilhetes. NUNCA leva o token.
  function enviar() {
    try {
      window.postMessage({
        __sharpenupSBIData: true, hook: true,
        bilhetes: Array.from(byId.values()), respostas: respostas, fim: fimReplay,
        cru: _crus(Array.from(byId.values())),
        semToken: !_auth(), erro: erro,
      }, "*");
    } catch (e) {}
  }

  // A versão LIQUIDADA vence a ABERTA.
  function guardar(b) {
    const ex = byId.get(b.id);
    if (!ex || ex.status === "ACTIVE" || b.status !== "ACTIVE") byId.set(b.id, b);
  }

  // Lê uma resposta GraphQL. Devolve `{n, proxima, cursor}`, `{erro}` ou null (não é lista).
  function consumir(text) {
    if (typeof text !== "string" || !/myBettingHistory|myActiveTickets/.test(text)) return null;
    let j;
    try { j = JSON.parse(text); } catch (e) { return null; }
    const st = j && j.data && j.data.sportsbetTickets;
    const con = st && (st.myBettingHistory || st.myActiveTickets);
    if (!con || !Array.isArray(con.edges)) {
      if (j && Array.isArray(j.errors) && j.errors.length) return { erro: _s(j.errors[0] && j.errors[0].message) };
      if (st) return { erro: "a casa devolveu a lista vazia (null): sessão expirada ou sem login" };
      return null;
    }
    respostas++;
    for (const e of con.edges) {
      const raw = e && e.node;
      const b = parseTicket(raw);
      if (!b) continue;
      try { _cruDe.set(b, raw); } catch (er) {}
      guardar(b);
    }
    const pi = con.pageInfo || null;
    LOG("bilhetes na resposta:", con.edges.length, "· total:", byId.size);
    enviar();
    return { n: con.edges.length, proxima: !!(pi && pi.hasNextPage), cursor: pi ? _s(pi.endCursor) : "" };
  }

  // ── aprendizado ────────────────────────────────────────────────────────────────
  function aprender(url, headers) {
    if (!RX_GQL.test(_caminho(url))) return;
    for (const k of Object.keys(headers || {})) {
      if (k.toLowerCase() !== "authorization") continue;
      const v = _s(headers[k]).trim();
      if (/^Bearer\s+\S/i.test(v)) {
        if (!auth) LOG("token aprendido de", _caminho(url));
        auth = v;
      }
    }
    if (_auth() && pedido) arrancarReplay();
  }

  // Partida a frio: o JWT da sessão é o cookie `token` (medido). A chamada real manda.
  function _auth() {
    if (auth) return auth;
    try {
      const c = _s(document.cookie).split(/;\s*/).find((x) => x.indexOf("token=") === 0);
      const v = c ? decodeURIComponent(c.slice(6)).trim() : "";
      return /^eyJ/.test(v) ? "Bearer " + v : "";
    } catch (e) { return ""; }
  }

  const _lang = () => (_s(location.pathname || _caminho(location.href)).match(/^\/([a-z]{2})(\/|$)/i) || [])[1] || "pt";

  // ── replay ─────────────────────────────────────────────────────────────────────
  async function pedir(lista, after) {
    const variables = { first: PAGINA, language: _lang() };
    if (after) variables.after = after;
    const r = await of.call(window, location.origin + "/graphql", {
      method: "POST", credentials: "include",
      headers: { accept: "*/*", "content-type": "application/json", authorization: _auth() },
      body: JSON.stringify({ operationName: lista.op, variables: variables, query: _query(lista.op, lista.campo) }),
    });
    return { ok: !!(r && r.ok), status: r && r.status, text: r ? await r.text() : "" };
  }

  // Uma lista inteira, pelo cursor. true = chegou ao fim autoritativo.
  async function varrerLista(lista) {
    let after = "";
    for (let pagina = 0; pagina < TETO_PAGINAS; pagina++) {
      let r;
      try { r = await pedir(lista, after); }
      catch (e) { erro = "replay falhou: " + (e && e.message); LOG(erro); return false; }
      if (!r.ok) { erro = "replay parou · HTTP " + r.status; LOG(erro); return false; }
      const res = consumir(r.text);
      if (!res) { erro = "resposta da lista em formato desconhecido"; LOG(erro); return false; }
      if (res.erro) { erro = "a casa respondeu erro: " + res.erro; LOG(erro); return false; }
      if (!res.proxima) return true;                               // fim AUTORITATIVO
      if (res.n <= 0 || !res.cursor || res.cursor === after) {     // anti-loop
        erro = "a casa disse que há mais, mas o cursor não andou"; LOG(erro); return false;
      }
      after = res.cursor;
    }
    LOG("teto de páginas atingido");
    return true;
  }

  async function arrancarReplay() {
    if (loopAtivo || fimReplay || !_auth()) return;
    loopAtivo = true;
    erro = "";
    try {
      for (const l of LISTAS) await varrerLista(l);
    } finally {
      loopAtivo = false;
      fimReplay = true;
      enviar();
      if (repetir) { repetir = false; fimReplay = false; byId.clear(); arrancarReplay(); }
    }
  }

  // O content pede o acumulado ao iniciar o robô → zera, re-envia e arranca o replay (lição da
  // s393: sem zerar, a 2ª rodada na mesma aba devolvia o mapa velho).
  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (!d || !d.__sharpenupSBIReq) return;
    pedido = true;
    if (loopAtivo) repetir = true;
    else { fimReplay = false; if (_auth()) byId.clear(); }
    enviar();
    arrancarReplay();
  });

  // ── fetch ── (medido: a página usa fetch, com o header no objeto de opções)
  const _hdrsToObj = (h) => {
    const o = {};
    try {
      if (!h) return o;
      if (typeof h.forEach === "function") h.forEach((v, k) => { o[k] = v; });
      else if (typeof h === "object") for (const k in h) o[k] = h[k];
    } catch (e) {}
    return o;
  };
  if (of && !of.__suSBIW) {
    const w = function (...a) {
      const req = (a[0] && typeof a[0] === "object" && a[0].url) ? a[0] : null;
      const url = req ? req.url : a[0];
      const opts = a[1] || {};
      try { aprender(url, _hdrsToObj(opts.headers || (req && req.headers))); } catch (e) {}
      return of.apply(this, a).then((r) => {
        try {
          if (RX_GQL.test(_caminho(url))) {
            // 2º argumento SEMPRE: sem ele um clone abortado vira rejeição muda (s305).
            r.clone().text().then((t) => { const x = consumir(t); if (x && x.erro) LOG("lista da página:", x.erro); }, () => {});
          }
        } catch (e) {}
        return r;
      });
    };
    w.__suSBIW = true;
    window.fetch = w;
  }

  // ── XMLHttpRequest ── (rede de segurança, caso a casa troque de transporte)
  const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send,
        osh = XMLHttpRequest.prototype.setRequestHeader;
  if (!os.__suSBIW) {
    XMLHttpRequest.prototype.open = function (m, u) { this.__suSBIU = u; this.__suSBIH = {}; return oo.apply(this, arguments); };
    XMLHttpRequest.prototype.setRequestHeader = function (k, v) { try { this.__suSBIH[k] = v; } catch (e) {} return osh.apply(this, arguments); };
    const s = function (body) {
      try {
        aprender(this.__suSBIU, this.__suSBIH);
        if (RX_GQL.test(_caminho(this.__suSBIU))) {
          this.addEventListener("load", () => {
            try {
              const t = (this.responseType === "" || this.responseType === "text")
                ? this.responseText : JSON.stringify(this.response);
              consumir(t);
            } catch (e) {}
          });
        }
      } catch (e) {}
      return os.apply(this, arguments);
    };
    s.__suSBIW = true;
    XMLHttpRequest.prototype.send = s;
  }

  // Partida a frio: com o cookie da sessão, o heartbeat já sai dizendo que há sessão.
  enviar();
})();
