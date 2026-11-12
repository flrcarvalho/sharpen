// Mundo MAIN (só na CopaWin, `wncopa.com`): BUSCA a lista de apostas da própria casa e repassa
// ao content script. Plataforma PRÓPRIA (recon s451, 12/11/2026, conta do Jaao26):
//
//   GET /api/bet/my-bets[?status=<filtro>][&page=N]       (mesmo domínio da aba, só o COOKIE)
//   → { success, bets: [ … ], pagination: { current_page, total_pages, total } }
//
// Não é Altenar, Kambi, BetBy nem BetConstruct: o site carrega o JS da casa (`/js/app.js`,
// `ticket.js`, `betslip.js`) e fala JSON no mesmo host. O cookie da sessão basta (medido com
// `fetch` cru, sem header nenhum): não há token para aprender.
//
// BUSCA ATIVA, não passiva: a 1ª página de "Minhas Apostas" vem RENDERIZADA NO HTML e abrir a
// tela não dispara chamada nenhuma (medido). Só o "carregar mais" chama a API. Um hook passivo
// entregaria zero, então o inject pede as páginas ele mesmo, sem `status` (= "Todas": abertas
// e liquidadas na mesma lista), até `pagination.total_pages`.
//
// ⚠ PÁGINA ALÉM DO FIM DEVOLVE A PÁGINA 1 (medido: `page=2` com `total_pages: 1` respondeu
// `current_page: 1` e os mesmos bilhetes). Parar por "veio vazio" nunca para. O fim é o
// `total_pages`, e página que volta com `current_page` diferente da pedida também encerra.
//
// O inject NÃO decide nada: normaliza campos crus (texto "750.00" → número, datas → epoch).
// `status` sobe como a casa escreveu; quem traduz é o `formatTicketCW` (pelo dinheiro) e a
// CASA_COPAWIN.md. ⚠ `created_at`/`updated_at` vêm em horário de BRASÍLIA e
// `event_starts_at`/`last_event_at` em UTC (prova no CASA_COPAWIN §2.5).
(function () {
  // ── CRU para o servidor (s409, Projeto Ficha Sharpen) ───────────────────────────────
  // O bilhete da casa, VERBATIM, ao lado do normalizado (campo `cru` da mensagem). Erro aqui
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

  // Sem exigir a barra inicial: a página chama `App.fetch('api/bet/my-bets?page=N')`, relativo.
  const RX = /(?:^|\/)api\/bet\/my-bets(?:[?#]|$)/i;
  const byId = new Map();                      // id(string) → bilhete normalizado
  let respostas = 0;                           // respostas VÁLIDAS do endpoint (autodiagnóstico)
  let loopAtivo = false, fimBusca = false, repetir = false;
  const LOG = (...a) => { try { console.log("[SharpenUp cw_inject]", ...a); } catch (e) {} };
  LOG("hook instalado em", location.href);

  const of = window.fetch;
  const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send;

  // ── normalização ─────────────────────────────────────────────────────────────────────
  // Dinheiro e odd vêm como TEXTO com ponto decimal ("750.00", "1.73").
  const _n = (v) => {
    if (v == null || v === "") return null;
    const x = Number(v);
    return isFinite(x) ? x : null;
  };
  // "AAAA-MM-DD HH:MM:SS" sem fuso → epoch (s), no fuso DECLARADO pelo chamador.
  const _epoch = (s, fuso) => {
    const m = /^(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2}:\d{2})/.exec(String(s || ""));
    if (!m) return null;
    const t = Date.parse(m[1] + "T" + m[2] + fuso);
    return isFinite(t) ? t / 1000 : null;
  };
  const _brt = (s) => _epoch(s, "-03:00");     // created_at / updated_at (o card mostra igual)
  const _utc = (s) => _epoch(s, "Z");          // event_starts_at / last_event_at

  function parsePerna(it) {
    if (!it) return null;
    const lista = (v) => (Array.isArray(v) ? v.map((x) => String(x == null ? "" : x)) : null);
    return {
      id: it.id != null ? String(it.id) : "",
      status: String(it.result == null ? "" : it.result),   // won · lost · void · pending (cru)
      odd: _n(it.odds),                                    // odd da seleção na colocação
      inicio: _utc(it.event_starts_at),
      ultimo: _utc(it.last_event_at),                      // no combo, o último jogo do pacote
      esporte: String(it.sport || ""),                     // "futebol", "basquete" (pt-BR, cru)
      mercado: String(it.market_name || ""),
      mercadoKey: String(it.market_key || ""),             // "combined" = Odd Turbinada
      label: String(it.selection_name || ""),
      jogo: String(it.match_name || ""),
      boost: _n(it.boost_pct),
      // Só no combo da casa: resultado, descrição e jogo de cada seleção, na mesma ordem.
      pernasCombo: lista(it.leg_statuses),
      jogosCombo: lista(it.leg_matches),
    };
  }

  function parseBet(t) {
    if (!t || t.id == null) return null;
    return {
      id: String(t.id),                          // "660753" — o número do card
      status: String(t.status == null ? "" : t.status),  // pending/active · won · lost · void · cashout (cru)
      tipo: String(t.type || ""),                // single · multiple (cru)
      stake: _n(t.stake),
      odd: _n(t.total_odds),                     // odd do bilhete (a da colocação; cheia na perdida)
      potencial: _n(t.potential_return),         // ⚠ o card mostra ESTE até na perdida
      retorno: _n(t.actual_return),              // o dinheiro que voltou (0 na perdida)
      cashout: {
        usado: !!Number(t.cashout_used), valor: _n(t.cashout_value), odd: _n(t.cashout_odd),
      },
      pernaAnulada: !!t.has_void_leg,
      ts: _brt(t.created_at),                    // colocação
      liquidacao: _brt(t.updated_at),
      sels: (Array.isArray(t.items) ? t.items : []).map(parsePerna).filter(Boolean),
    };
  }

  // Heartbeat: SEMPRE hook:true + respostas, mesmo com 0 bilhetes.
  function enviar() {
    try {
      const lista = Array.from(byId.values());
      window.postMessage({
        __sharpenupCWData: true, hook: true,
        bilhetes: lista, respostas: respostas, fim: fimBusca, cru: _crus(lista),
      }, "*");
    } catch (e) {}
  }

  // A versão LIQUIDADA vence a aberta (o dinheiro só é final depois de liquidado).
  const _aberta = (b) => b.status === "pending" || b.status === "active";
  function guardar(b) {
    const ex = byId.get(b.id);
    if (!ex || _aberta(ex) || !_aberta(b)) byId.set(b.id, b);
  }

  // Processa uma resposta; devolve {pagina, total, n} para a busca, ou null.
  function forward(url, text) {
    if (!RX.test(String(url)) || typeof text !== "string") return null;
    let j;
    try { j = JSON.parse(text); } catch (e) { return null; }
    if (!j || j.success === false || !Array.isArray(j.bets)) return null;   // barra login/erro
    respostas++;
    for (const raw of j.bets) {
      const b = parseBet(raw);
      if (b) { _marcarCru(b, raw); guardar(b); }
    }
    const p = j.pagination || {};
    LOG("bilhetes na resposta:", j.bets.length, "· total:", byId.size, "· página", p.current_page, "de", p.total_pages);
    enviar();
    return { pagina: Number(p.current_page), total: Number(p.total_pages), n: j.bets.length };
  }

  // ── busca ativa ──────────────────────────────────────────────────────────────────────
  function urlPagina(pg) {
    try {
      const u = new URL("/api/bet/my-bets", location.href);
      if (pg > 1) u.searchParams.set("page", String(pg));
      return u.href;
    } catch (e) { return null; }
  }

  // GET pelo `fetch` ORIGINAL (não passa pelo gancho, que processaria duas vezes).
  async function pedirPagina(url) {
    try {
      const r = await of.call(window, url, {
        method: "GET", credentials: "include",
        headers: { Accept: "application/json", "X-Requested-With": "XMLHttpRequest" },
      });
      return { ok: !!r.ok, status: r.status, text: await r.text() };
    } catch (e) { return { ok: false, status: 0, text: "" }; }
  }

  const TETO_PAGINAS = 300;

  async function buscar() {
    for (let pg = 1; pg <= TETO_PAGINAS; pg++) {
      const url = urlPagina(pg);
      if (!url) return;
      const r = await pedirPagina(url);
      if (!r.ok) { LOG("busca parou · HTTP", r.status, "· página", pg); return; }
      const res = forward(url, r.text);
      if (!res || !res.n) return;                              // sessão caiu / lista vazia
      if (isFinite(res.pagina) && res.pagina !== pg) return;   // a casa devolveu OUTRA página: acabou
      if (!isFinite(res.total) || pg >= res.total) return;     // fim AUTORITATIVO
    }
    LOG("teto de páginas atingido");
  }

  async function arrancar() {
    if (loopAtivo) return;
    loopAtivo = true;
    try { await buscar(); } finally {
      loopAtivo = false;
      fimBusca = true;
      enviar();
      if (repetir) { repetir = false; fimBusca = false; byId.clear(); arrancar(); }
    }
  }

  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (!d || !d.__sharpenupCWReq) return;
    // Pedido novo é rodada NOVA (lição da s393, DEX Sport): o acumulado velho não é reenviado,
    // porque o content formata cada bilhete na 1ª vez que o vê. Pedido com a busca em curso
    // fica marcado e roda ao fim.
    if (loopAtivo) { repetir = true; return; }
    fimBusca = false;
    byId.clear();
    enviar();
    arrancar();
  });

  // ── fetch: o "carregar mais" da página (`App.fetch('api/bet/my-bets?page=N')`) ──
  if (of && !of.__suCWW) {
    const w = function (...a) {
      const url = (a[0] && a[0].url) || a[0];
      return of.apply(this, a).then((r) => {
        try { if (RX.test(String(url))) r.clone().text().then((t) => forward(url, t)); } catch (e) {}
        return r;
      });
    };
    w.__suCWW = true;
    window.fetch = w;
  }

  // ── XMLHttpRequest (rede de segurança: hoje a página usa fetch) ──
  if (!os.__suCWW) {
    XMLHttpRequest.prototype.open = function (m, u) { this.__suCWU = u; return oo.apply(this, arguments); };
    const s = function () {
      try {
        if (RX.test(String(this.__suCWU))) {
          this.addEventListener("load", () => { try { forward(this.__suCWU, this.responseText); } catch (e) {} });
        }
      } catch (e) {}
      return os.apply(this, arguments);
    };
    s.__suCWW = true;
    XMLHttpRequest.prototype.send = s;
  }
})();
