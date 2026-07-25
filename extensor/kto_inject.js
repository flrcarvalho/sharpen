// Mundo MAIN (só na KTO): lê as RESPOSTAS que a própria página recebe da API de histórico
// de cupons e repassa ao content script. A KTO roda em KAMBI — endpoint documentado e estável:
//
//   GET cf-al-auth-api.kambicdn.com/player/api/v2019/<operador>/coupon/history.json
//       ?lang=pt_BR&market=BR&client_id=…&channel_id=…&range_size=N&range_start=M&status=…
//
// Antes a KTO caía no robô de TEXTO genérico (roboScroll), que parte o innerText por linha em
// branco — e a lista da KTO NÃO tem linha em branco entre cupons: os ~140 bilhetes viravam UM
// bloco gigante junto com o menu e o rodapé, a IA lia os primeiros e perdia o resto em silêncio.
// Aqui o dado vem estruturado e exato: couponRef, odd, stake, payout, status, pernas, esporte.
//
// REPLAY ATIVO (o "puxa sozinho"): a partir de uma requisição real da página o inject aprende
// url+headers (o Bearer é da própria sessão) e RE-EMITE incrementando `range_start` até a
// resposta dizer `range.more === false`. Espelha o paginarLoop do bf_inject / pn_inject.
// O avanço usa o `range.size` que VOLTOU (não o que pedimos) → se a API limitar o tamanho da
// página, o loop se autocorrige em vez de pular bilhetes.
//
// ABAS (status): a lista de "Minhas Apostas" separa Abertas (status=PENDING) de Resolvidas.
// NÃO dependemos de conhecer o valor exato de cada aba: replayamos toda URL que a página
// disparou E, por cima, as variantes de `status` conhecidas. Variante inválida volta erro e é
// ignorada — a URL aprendida continua valendo.
//
// ARMADILHA CONFIRMADA no dado real: `betOdds` vem **0** em toda aposta PERDIDA (cupom
// 12886338194: betOdds 0, playedOdds 6000, site mostra 6.00). Quem ler betOdds grava odd zero
// em 100% das perdas. A odd útil sai de playedOdds/potentialPayout/payout — ver formatTicketKTO
// no content.js. Aqui o inject NÃO decide nada: só entrega os campos crus.
(function () {
  const RX = /\/coupon\/history\.json/i;      // endpoint da LISTA de cupons
  const byRef = new Map();                     // couponRef(string) → cupom normalizado
  let respostas = 0;                           // respostas do endpoint que o hook viu (autodiagnóstico)
  let reqCtx = null;                           // {url, headers} de uma requisição real (p/ replay)
  let pedido = false;                          // o robô já pediu → pode arrancar o replay
  let loopAtivo = false;                       // trava: um replay por vez
  let fimReplay = false;                       // todas as URLs/variantes já foram repaginadas
  const aprendidas = new Map();                // chave(status) → url base (sem range_*)
  const LOG = (...a) => { try { console.log("[SharpenUp kto_inject]", ...a); } catch (e) {} };
  LOG("hook instalado em", location.href);

  const of = window.fetch;                     // fetch ORIGINAL — o replay usa este (não re-dispara o wrapper)

  // Valores de `status` que a lista usa. Só entram como VARIANTE (tentativa extra); o que
  // manda é sempre a URL que a página realmente disparou.
  const STATUS_VARIANTES = ["PENDING", "SETTLED"];

  // ── normalização (Kambi → objeto limpo) ───────────────────────────────────────
  // Dinheiro e odds vêm em MILÉSIMOS (stake 600000 = R$600,00 · betOdds 2043 = 2,043 ·
  // line 8500 = 8.5). Confirmado cruzando o JSON com o texto renderizado da própria página.
  const _m = (v) => (typeof v === "number" ? v / 1000 : null);

  // Um couponRow pode ser 1 seleção (outcomeId) ou um bet builder (outcomeGroup aninhado).
  function colherIds(g, out) {
    if (!g) return out;
    if (Array.isArray(g.outcomeIds)) for (const id of g.outcomeIds) out.push(id);
    if (Array.isArray(g.groups)) for (const sub of g.groups) colherIds(sub, out);
    return out;
  }

  function parseCoupon(c) {
    if (!c || c.couponRef == null) return null;
    const outById = new Map();
    for (const o of (c.outcomes || [])) outById.set(o.outcomeId, o);
    const evById = new Map();
    for (const e of (c.events || [])) evById.set(e.eventId, e);
    const boById = new Map();
    for (const b of (c.betOffers || [])) boById.set(b.betOfferId, b);

    const rows = (c.couponRows || []).map((r) => {
      const ids = r.outcomeId != null ? [r.outcomeId] : colherIds(r.outcomeGroup, []);
      const sels = ids.map((id) => {
        const o = outById.get(id) || {};
        const ev = evById.get(o.eventId) || {};
        const bo = boById.get(o.betOfferId) || {};
        return {
          label: o.label || "",                          // "Ousmane Dembélé - Mais 0.5"
          status: o.status || "",                        // WON / LOST / OPEN / VOID…
          linha: _m(o.line != null ? o.line : bo.line),  // 8500 → 8.5
          antecipada: !!o.earlySettlement,               // liquidação antecipada (EARLY_SETTLED)
          mercado: bo.criterion || "",                   // "Total de Escanteio por Chicago Fire"
          boTipo: bo.boType || "",                       // Match / Over/Under / Handicap / Winner…
          nota: bo.extraInfo || "",                      // "Apenas tempo normal…"
          jogo: ev.eventName || "",                      // "França - Marrocos"
          casa: ev.homeName || "",
          fora: ev.awayName || "",
          esporte: ev.sport || "",                       // FOOTBALL / TENNIS / DARTS / SPECIAL_BETS…
          grupos: (ev.eventGroups || []).map((g) => g.name).filter(Boolean),   // ["Futebol","MLS"]
          inicio: ev.eventStartDate || "",
        };
      });
      return {
        idx: r.index,
        status: r.status || "",
        tipo: r.selectionType || "",                     // SIMPLE / BET_BUILDER
        odd: _m(r.playedOdds),
        oddBoost: _m(r.oddsBoosted),
        sels: sels,
      };
    });

    // Um cupom pode ter MAIS DE UMA entrada em `bets` (aposta de sistema, ou stake dividida
    // entre parte turbinada e parte normal — o card da KTO mostra "R$176.97R$61.52"). O card
    // é UM cupom, então agregamos stake/retorno e guardamos o detalhe por entrada.
    const bets = (c.bets || []).map((b) => ({
      ref: b.betRef,
      status: b.betStatus || "",                         // OPEN / WON / LOST / …
      stake: _m(b.stake),
      payout: _m(b.payout),
      potencial: _m(b.potentialPayout),
      potencialBoost: _m(b.potentialPayoutBoosted),
      odd: _m(b.playedOdds),
      oddBase: _m(b.betOdds),                            // ⚠ 0 quando PERDIDA — nunca usar sozinho
      oddBoost: _m(b.betOddsBoosted),
      bonus: _m(b.bonusPayout),
      pernas: Array.isArray(b.couponRowIndexes) ? b.couponRowIndexes.length : 0,
      tags: b.tags || [],
    }));

    return {
      ref: String(c.couponRef),
      colocada: c.placedDate || "",
      canal: c.channel || "",
      moeda: c.currency || "",
      bets: bets,
      rows: rows,
      sistema: Array.isArray(c.systemBets) ? c.systemBets.length : 0,   // "Simples (2)", "Duplas (3)"…
      boostTipo: c.rewardType || "",                     // ODDS_BOOST / PROFIT_BOOST (= ODDÃO+)
      boostPct: c.boostPercentage != null ? c.boostPercentage : null,
      bonus: _m(c.bonusPayout),
      tags: c.tags || [],
    };
  }

  // Emite SEMPRE hook:true + respostas (heartbeat), mesmo com 0 cupons — o content distingue
  // "hook não carregou" de "endpoint respondeu, lemos 0" (mesmo autodiagnóstico das outras).
  function enviar() {
    try {
      window.postMessage({
        __sharpenupKTOData: true, hook: true,
        cupons: Array.from(byRef.values()), respostas: respostas, fim: fimReplay,
      }, "*");
    } catch (e) {}
  }

  // Guarda o cupom. Um mesmo ref pode voltar em abas diferentes (aberto x resolvido): a versão
  // RESOLVIDA vence a ABERTA (o dinheiro só é final depois de liquidado).
  function guardar(cup) {
    const ex = byRef.get(cup.ref);
    if (!ex) { byRef.set(cup.ref, cup); return; }
    const aberto = (c) => (c.bets || []).some((b) => !b.status || b.status === "OPEN");
    if (aberto(ex) && !aberto(cup)) byRef.set(cup.ref, cup);
  }

  // Processa uma resposta. Devolve o `range` (p/ o replay saber se continua) ou null.
  function forward(url, text) {
    if (!RX.test(String(url)) || typeof text !== "string") return null;
    let j;
    try { j = JSON.parse(text); } catch (e) { return null; }
    const arr = j && Array.isArray(j.historyCoupons) ? j.historyCoupons : null;
    if (!arr) return null;
    respostas++;
    const antes = byRef.size;
    for (const raw of arr) {
      const c = parseCoupon(raw);
      if (c) guardar(c);
    }
    aprender(url);
    LOG("cupons na resposta:", arr.length, "· total:", byRef.size, "· range:", JSON.stringify(j.range || {}));
    enviar();
    return (j.range && typeof j.range === "object") ? j.range : { more: false, size: arr.length, start: 0 };
  }

  // ── replay ativo: repagina por range_start até `more:false` ────────────────────
  function _hdrsToObj(h) {
    const o = {};
    try {
      if (!h) return o;
      if (typeof h.forEach === "function") h.forEach((v, k) => { o[k] = v; });
      else if (typeof h === "object") for (const k in h) o[k] = h[k];
    } catch (e) {}
    return o;
  }

  // URL base = a URL da página SEM range_start/range_size (que o replay controla).
  // A chave é o `status` — uma entrada por aba, para não repaginar a mesma lista duas vezes.
  function aprender(url) {
    let u;
    try { u = new URL(String(url), location.href); } catch (e) { return; }
    if (!RX.test(u.pathname)) return;
    const chave = u.searchParams.get("status") || "_todas_";
    if (!aprendidas.has(chave)) {
      aprendidas.set(chave, u.href);
      LOG("lista aprendida · status =", chave);
    }
  }

  function capturarReq(url, headers) {
    if (!RX.test(String(url))) return;
    aprender(url);
    if (!reqCtx) {
      // Só os headers que a página definiu (authorization/accept). Nada de cookie: vai no
      // credentials:"include", como nas outras casas passivas.
      reqCtx = { url: String(url), headers: headers || {} };
      LOG("requisição capturada p/ replay");
    }
    if (pedido) arrancarReplay();
  }

  function comRange(base, start, size) {
    try {
      const u = new URL(base, location.href);
      u.searchParams.set("range_start", String(start));
      u.searchParams.set("range_size", String(size));
      return u.href;
    } catch (e) { return base; }
  }
  function comStatus(base, status) {
    try {
      const u = new URL(base, location.href);
      u.searchParams.set("status", status);
      return u.href;
    } catch (e) { return null; }
  }

  const PAGINA = 100;      // pedimos 100; o avanço usa o range.size que VOLTAR
  const TETO_PAGINAS = 200;

  async function paginar(baseUrl) {
    let start = 0;
    for (let i = 0; i < TETO_PAGINAS; i++) {
      let r;
      try {
        r = await of.call(window, comRange(baseUrl, start, PAGINA), {
          method: "GET", headers: (reqCtx && reqCtx.headers) || {}, credentials: "include",
        });
      } catch (e) { LOG("erro no replay:", e && e.message); return; }
      if (!r || !r.ok) { LOG("replay parou · HTTP", r && r.status); return; }
      let range;
      try { range = forward(r.url || baseUrl, await r.text()); } catch (e) { return; }
      if (!range) return;
      const size = Number(range.size) || 0;
      if (!range.more || size <= 0) return;                 // fim autoritativo da lista
      start = (Number(range.start) || start) + size;
    }
    LOG("teto de páginas atingido em", baseUrl);
  }

  async function arrancarReplay() {
    if (loopAtivo || fimReplay || !reqCtx) return;
    loopAtivo = true;
    try {
      // 1) toda lista que a página realmente disparou (autoritativo)
      for (const url of Array.from(aprendidas.values())) await paginar(url);
      // 2) variantes de status ainda não vistas — melhor esforço; inválida volta erro e sai
      for (const st of STATUS_VARIANTES) {
        if (aprendidas.has(st)) continue;
        const alvo = comStatus(reqCtx.url, st);
        if (alvo) await paginar(alvo);
      }
    } finally {
      loopAtivo = false;
      fimReplay = true;
      enviar();                                             // sinaliza fim p/ o robô parar de esperar
    }
  }

  // O content script pede o acumulado ao iniciar o robô → re-envia tudo E arranca o replay.
  // A 1ª página vem no load da página (antes do content estar pronto pra ouvir), por isso
  // re-enviamos sob demanda.
  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (!d || !d.__sharpenupKTOReq) return;
    pedido = true;
    enviar();
    arrancarReplay();
  });

  // ── fetch ──
  if (of && !of.__suKTOW) {
    const w = function (...a) {
      const url = (a[0] && a[0].url) || a[0];
      const opts = a[1] || (a[0] && typeof a[0] === "object" ? a[0] : null);
      try { if (RX.test(String(url))) capturarReq(url, _hdrsToObj(opts && opts.headers)); } catch (e) {}
      return of.apply(this, a).then((r) => {
        try { if (RX.test(String(url))) r.clone().text().then((t) => forward(url, t)); } catch (e) {}
        return r;
      });
    };
    w.__suKTOW = true;
    window.fetch = w;
  }

  // ── XMLHttpRequest (a lista da KTO vem por XHR estilo jQuery) ──
  const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send, osh = XMLHttpRequest.prototype.setRequestHeader;
  if (!os.__suKTOW) {
    XMLHttpRequest.prototype.open = function (m, u) { this.__suKTOU = u; this.__suKTOH = {}; return oo.apply(this, arguments); };
    XMLHttpRequest.prototype.setRequestHeader = function (k, v) { try { this.__suKTOH[k] = v; } catch (e) {} return osh.apply(this, arguments); };
    const s = function () {
      try {
        if (RX.test(String(this.__suKTOU))) {
          capturarReq(this.__suKTOU, this.__suKTOH);
          this.addEventListener("load", () => { try { forward(this.__suKTOU, this.responseText); } catch (e) {} });
        }
      } catch (e) {}
      return os.apply(this, arguments);
    };
    s.__suKTOW = true;
    XMLHttpRequest.prototype.send = s;
  }
})();
