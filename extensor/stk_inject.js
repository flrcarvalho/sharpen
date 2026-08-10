// Mundo MAIN (só na Stake): lê as RESPOSTAS que a própria página recebe da API de histórico
// de bilhetes e repassa ao content script.
//
//   POST web-api.stake.bet.br/restapi/v1/betslip/history   → liquidadas (`status` no corpo)
//   POST web-api.stake.bet.br/restapi/v1/betslip/active    → abertas (sem `status`)
//
// Corpo real da página: {"token":"<uuid de sessão>","range_start":0,"range_size":10,"status":1}
//
// A Stake roda KAMBI, o mesmo motor da KTO — provado pelo vocabulário (`Total de Escanteio
// por <time>`, `Resultado Final`, esportes em caixa alta, paginação `range_start`/`range_size`),
// não pela aparência. Mas ela NÃO expõe a Kambi: embrulha num REST próprio com nomes
// snake_case, dinheiro em REAIS (não milésimos) e status em INTEIRO (não string). Por isso a
// casa é espelho na LEITURA e casa nova na CAPTURA — o `kto_inject.js` é o molde, não o arquivo.
//
// REPLAY ATIVO: a partir de uma requisição real o inject aprende url + headers + o CORPO
// (o `token` é da sessão da página e não há como inventá-lo) e re-emite incrementando
// `range_start` até a resposta dizer `next_page_exists:false` — fim autoritativo de verdade,
// que distingue "acabou" de "a consulta encheu". O avanço usa o número de bilhetes que
// VOLTOU, não o que pedimos: se a API limitar a página, o loop se autocorrige.
//
// A VARIANTE "TUDO" (medida no recon): o campo `status` do corpo é OPCIONAL, e omitindo-o o
// `/history` devolve abertas + liquidadas numa chamada só (medido: status:0 → 1 bilhete,
// status:1 → 16, sem o campo → 17). Ela vai primeiro. Como é um uso que a própria página
// nunca faz, as variantes que a página REALMENTE disparou continuam sendo replayadas por
// cima — se a Stake um dia passar a exigir o campo, a captura degrada em vez de zerar.
//
// ARMADILHAS confirmadas no dado real (o inject NÃO decide nada — só entrega os campos crus;
// quem lê é o formatTicketSTK no content.js):
//   • `bet_total_stake` vem 0 em TODA anulada — o valor real está em `bet_request_stake`.
//   • `bet_payout` é 0 na anulada E na perdida: o dinheiro não distingue as duas. Por isso
//     `bet_status` sobe cru e íntegro.
//   • `bet_total_odds` é arredondada a 2 casas; a odd exata é o produto das `bet_selection_odd`.
//   • o ID que o card estampa é `internal_bet_id` (7 dígitos), não `ticket_id` (11).
(function () {
  const RX = /\/restapi\/v1\/betslip\/(history|active)/i;   // endpoint da LISTA de bilhetes
  const byRef = new Map();                     // internal_bet_id(string) → bilhete normalizado
  let respostas = 0;                           // respostas do endpoint que o hook viu (autodiagnóstico)
  let reqCtx = null;                           // {url, headers, corpo} de uma requisição real (p/ replay)
  let pedido = false;                          // o robô já pediu → pode arrancar o replay
  let loopAtivo = false;                       // trava: um replay por vez
  let fimReplay = false;                       // todas as variantes já foram repaginadas
  const aprendidas = new Map();                // chave(path|status) → {url, corpo}
  const LOG = (...a) => { try { console.log("[SharpenUp stk_inject]", ...a); } catch (e) {} };
  LOG("hook instalado em", location.href);

  const of = window.fetch;                     // fetch ORIGINAL — o replay usa este (não re-dispara o wrapper)

  const PAGINA = 100;          // pedimos 100; o avanço usa quantos bilhetes VOLTARAM
  const TETO_PAGINAS = 200;

  // ── normalização (REST da Stake → objeto limpo) ────────────────────────────────
  // Dinheiro e odds vêm em REAIS, já como número (265.55 = R$265,55). NÃO há milésimos aqui
  // — confirmado cruzando o JSON com o card renderizado.
  const _n = (v) => (typeof v === "number" ? v : null);
  const _s = (v) => (v == null ? "" : String(v));

  // Um ticket pode trazer mais de uma entrada em `ticket_bets`. O ID que o card mostra é o
  // `internal_bet_id`, que é POR ENTRADA — então a unidade do bilhete é a entrada, não o
  // ticket. (Nunca vimos ticket com 2 entradas; o campo é array e o desenho respeita isso.)
  function parseTicket(t, out) {
    if (!t || !Array.isArray(t.ticket_bets)) return;
    for (const b of t.ticket_bets) {
      if (!b) continue;
      const ref = b.internal_bet_id != null ? String(b.internal_bet_id)
                : (b.id != null ? String(b.id) : "");
      if (!ref) continue;
      out.push({
        ref: ref,                                  // internal_bet_id — o [Código:] e a chave de dedup
        ticket: _s(t.ticket_id),                   // ticket_id (agrupador da casa)
        betId: _s(b.id),                           // id longo interno
        externo: _s(t.external_bet_id),
        colocada: t.ticket_placed_date || "",      // UTC com +00:00 → o content converte p/ SP
        moeda: t.ticket_currency || "",
        ticketStatus: t.ticket_status,             // 1 ativo · 2 liquidado (cru)
        status: b.bet_status,                      // 1 aberta · 2 ganha · 3 perdida · 4 anulada (cru)
        tipo: b.bet_type,
        bonusTipo: b.bet_bonus_type,
        odd: _n(b.bet_total_odds),                 // ⚠ arredondada a 2 casas pela casa
        oddBoost: _n(b.bet_total_odds_boosted),
        stake: _n(b.bet_total_stake),              // ⚠ 0 em toda ANULADA — nunca usar sozinho
        stakePedida: _n(b.bet_request_stake),      // o valor que o card mostra na anulada
        potencial: _n(b.bet_potential_payout),
        potencialBoost: _n(b.bet_potential_payout_boosted),
        payout: _n(b.bet_payout),
        cashout: _n(b.bet_cashout_value),          // só existe no endpoint de ABERTAS
        cashoutStatus: b.bet_cashout_status || "",
        sels: (b.bet_selections || []).map((s) => ({
          eventoId: _s(s.event_id),
          inicio: s.event_date || "",
          esporte: s.event_sport || "",            // FOOTBALL / TENNIS / … (vocabulário Kambi)
          jogo: s.event_name || "",                // "Náutico-PE - Atlético-GO"
          mercado: s.bet_selection_criteria || "", // "Total de Escanteio por Náutico-PE"
          resultado: s.bet_selection_outcome_score || "",   // "Mais" / "Menos" / "1" / "N/A"
          label: s.bet_selection_label || "",      // "Mais 4.5"
          status: s.bet_selection_status,          // 1 sem marcação · 2 ganha · 3 perdida (cru)
          odd: _n(s.bet_selection_odd),
          oddBoost: _n(s.bet_selection_odd_boosted),
          antecipada: !!s.early_settlement,
        })),
      });
    }
  }

  // Emite SEMPRE hook:true + respostas (heartbeat), mesmo com 0 bilhetes — o content distingue
  // "hook não carregou" de "endpoint respondeu, lemos 0" (mesmo autodiagnóstico das outras).
  function enviar() {
    try {
      window.postMessage({
        __sharpenupSTKData: true, hook: true,
        bilhetes: Array.from(byRef.values()), respostas: respostas, fim: fimReplay,
      }, "*");
    } catch (e) {}
  }

  // Guarda o bilhete. O mesmo ref pode voltar em variantes diferentes (aberta x liquidada):
  // a versão LIQUIDADA vence a ABERTA (o dinheiro só é final depois de liquidado).
  function guardar(b) {
    const ex = byRef.get(b.ref);
    if (!ex) { byRef.set(b.ref, b); return; }
    const aberto = (x) => x.ticketStatus === 1;
    if (aberto(ex) && !aberto(b)) byRef.set(b.ref, b);
  }

  // Processa uma resposta. Devolve o `Data` (p/ o replay saber se continua) ou null.
  function forward(url, text, corpoEnviado) {
    if (!RX.test(String(url)) || typeof text !== "string") return null;
    let j;
    try { j = JSON.parse(text); } catch (e) { return null; }
    const d = j && j.Data;
    if (!d || !Array.isArray(d.tickets)) return null;    // corpo de erro / formato mudou
    respostas++;
    const novos = [];
    for (const t of d.tickets) parseTicket(t, novos);
    for (const b of novos) guardar(b);
    aprender(url, corpoEnviado);
    LOG("bilhetes na resposta:", novos.length, "· total:", byRef.size,
        "· próxima página:", d.next_page_exists);
    enviar();
    return d;
  }

  // ── replay ativo ───────────────────────────────────────────────────────────────
  function _hdrsToObj(h) {
    const o = {};
    try {
      if (!h) return o;
      if (typeof h.forEach === "function") h.forEach((v, k) => { o[k] = v; });
      else if (typeof h === "object") for (const k in h) o[k] = h[k];
    } catch (e) {}
    return o;
  }

  function _corpoObj(corpo) {
    if (!corpo || typeof corpo !== "string") return null;
    try {
      const o = JSON.parse(corpo);
      return (o && typeof o === "object") ? o : null;
    } catch (e) { return null; }
  }

  function _path(url) {
    try { return new URL(String(url), location.href).pathname; } catch (e) { return String(url); }
  }

  // Uma entrada por VARIANTE de lista (endpoint + status), para não repaginar a mesma coisa
  // duas vezes. `range_start`/`range_size` saem do corpo guardado: quem controla é o replay.
  function aprender(url, corpo) {
    const o = _corpoObj(corpo);
    if (!o) return;
    const p = _path(url);
    if (!RX.test(p)) return;
    const chave = p + "|" + (o.status != null ? o.status : "_sem_");
    if (aprendidas.has(chave)) return;
    const base = {};
    for (const k in o) if (k !== "range_start" && k !== "range_size") base[k] = o[k];
    aprendidas.set(chave, { url: String(url), corpo: base });
    LOG("lista aprendida ·", chave);
  }

  function capturarReq(url, headers, corpo) {
    if (!RX.test(String(url))) return;
    aprender(url, corpo);
    if (!reqCtx && _corpoObj(corpo)) {
      // Só os headers que a página definiu (authorization/content-type). Nada de cookie: vai
      // no credentials:"include", como nas outras casas.
      reqCtx = { url: String(url), headers: headers || {} };
      LOG("requisição capturada p/ replay");
    }
    if (pedido) arrancarReplay();
  }

  async function paginar(url, corpoBase) {
    let start = 0;
    for (let i = 0; i < TETO_PAGINAS; i++) {
      const corpo = JSON.stringify(Object.assign({}, corpoBase, {
        range_start: start, range_size: PAGINA,
      }));
      let r;
      try {
        r = await of.call(window, url, {
          method: "POST", headers: (reqCtx && reqCtx.headers) || {},
          credentials: "include", body: corpo,
        });
      } catch (e) { LOG("erro no replay:", e && e.message); return; }
      if (!r || !r.ok) { LOG("replay parou · HTTP", r && r.status); return; }
      let d;
      try { d = forward(r.url || url, await r.text(), corpo); } catch (e) { return; }
      if (!d) return;
      const n = (d.tickets || []).length;
      if (d.next_page_exists !== true || n <= 0) return;    // fim AUTORITATIVO da lista
      start += n;                                           // avança pelo que VOLTOU
    }
    LOG("teto de páginas atingido em", url);
  }

  async function arrancarReplay() {
    if (loopAtivo || fimReplay || !reqCtx) return;
    loopAtivo = true;
    try {
      const feitas = new Set();
      // 1) variante "tudo": o /history SEM o campo `status` devolve abertas + liquidadas numa
      //    chamada. É a mais completa e vai primeiro.
      const sem = Array.from(aprendidas.values()).find((v) => /\/history/i.test(_path(v.url)));
      if (sem) {
        const corpo = {};
        for (const k in sem.corpo) if (k !== "status") corpo[k] = sem.corpo[k];
        feitas.add(_path(sem.url) + "|_sem_");
        await paginar(sem.url, corpo);
      }
      // 2) por cima, toda variante que a PÁGINA realmente disparou (autoritativo). Melhor
      //    esforço: se a de cima já trouxe tudo, o `byRef` só reconfirma.
      for (const [chave, v] of Array.from(aprendidas.entries())) {
        if (feitas.has(chave)) continue;
        await paginar(v.url, v.corpo);
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
    if (!d || !d.__sharpenupSTKReq) return;
    pedido = true;
    enviar();
    arrancarReplay();
  });

  // ── fetch ──
  // A página chama `fetch(new Request(url, {...}))` — o corpo e os headers só saem de um
  // clone do Request, não de `opts`. Por isso as duas formas são tratadas aqui: sem o corpo
  // não há `token`, e sem `token` o replay volta vazio.
  if (of && !of.__suSTKW) {
    const w = function (...a) {
      const req = (a[0] && typeof a[0] === "object" && a[0].url) ? a[0] : null;
      const url = req ? req.url : a[0];
      const opts = a[1] || {};
      try {
        if (RX.test(String(url))) {
          if (req) {
            const hdrs = _hdrsToObj(req.headers);
            let clone = null;
            try { clone = req.clone(); } catch (e) {}
            if (clone && typeof clone.text === "function") {
              clone.text().then((t) => capturarReq(url, hdrs, t)).catch(() => {});
            } else {
              capturarReq(url, hdrs, typeof opts.body === "string" ? opts.body : null);
            }
          } else {
            capturarReq(url, _hdrsToObj(opts.headers),
                        typeof opts.body === "string" ? opts.body : null);
          }
        }
      } catch (e) {}
      return of.apply(this, a).then((r) => {
        try {
          if (RX.test(String(url))) {
            const corpo = typeof opts.body === "string" ? opts.body : null;
            r.clone().text().then((t) => forward(url, t, corpo));
          }
        } catch (e) {}
        return r;
      });
    };
    w.__suSTKW = true;
    window.fetch = w;
  }

  // ── XMLHttpRequest (rede de segurança: se a Stake trocar de transporte, a captura segue) ──
  const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send,
        osh = XMLHttpRequest.prototype.setRequestHeader;
  if (!os.__suSTKW) {
    XMLHttpRequest.prototype.open = function (m, u) { this.__suSTKU = u; this.__suSTKH = {}; return oo.apply(this, arguments); };
    XMLHttpRequest.prototype.setRequestHeader = function (k, v) { try { this.__suSTKH[k] = v; } catch (e) {} return osh.apply(this, arguments); };
    const s = function (body) {
      try {
        if (RX.test(String(this.__suSTKU))) {
          const corpo = typeof body === "string" ? body : null;
          capturarReq(this.__suSTKU, this.__suSTKH, corpo);
          this.addEventListener("load", () => {
            try { forward(this.__suSTKU, this.responseText, corpo); } catch (e) {}
          });
        }
      } catch (e) {}
      return os.apply(this, arguments);
    };
    s.__suSTKW = true;
    XMLHttpRequest.prototype.send = s;
  }
})();
