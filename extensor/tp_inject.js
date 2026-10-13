// Mundo MAIN (1win — plataforma `top-parser`): lê o histórico de apostas que a página pede
// e BUSCA a lista inteira ele mesmo, repassando ao content script.
//
//   POST api-gateway.top-parser.com/bets/history/get-many
//        { limit: 150, offset: 0, statuses?: [..], sportType: "sport" }
//   → { result: { items: [ { bet: {...}, selections: [...] } ], meta: { total } } }
//
// PLATAFORMA PRÓPRIA (recon s413, conta do Feca). A página é da 1win (`1win.io` e espelhos),
// mas o sportsbook fala com um gateway em OUTRO host, `api-gateway.top-parser.com`. Não há
// iframe de BetBy/Altenar/Kambi/BetConstruct, e o JSON não se parece com nenhuma casa nossa.
// Inject próprio, formatador próprio (`formatTicketTP`).
//
// AUTH É POR HEADER `token`, não cookie. A página manda `credentials` padrão (sem cookie para
// o outro host), e o `token` vai em TODA chamada autenticada da tela de Esportes
// (`freebets/get-many`, `bonuses/get-many`, `b/get-many`…, medido), não só na do histórico.
// Por isso o inject aprende os headers de QUALQUER chamada do gateway que traga `token`, e o
// replay arranca sem o operador abrir "Histórico de apostas". O valor nunca sai deste
// arquivo: a mensagem para o content leva só `semToken`.
//
// O QUE FOI MEDIDO no gateway, com o token da sessão:
//   • `limit` tem teto 150: 151 volta `{"errors":[{"code":"bad_request_error"}]}`.
//   • ERRO VOLTA COM HTTP 200 e `errors[]`. Quem confia no `r.ok` conta erro como resposta.
//   • Paginação por `offset`, com `meta.total`. Fim AUTORITATIVO = `offset >= total`
//     (com `limit: 2` sobre 5 bilhetes: 2 + 2 + 1, e o offset 6 volta lista vazia).
//   • Sem `statuses` a lista traz abertas e liquidadas juntas (é a aba "Todos" da tela).
//     `statuses` aceita só 0 a 4 (5 volta `validation_error`).
//   • `sportType` só aceita `sport`, `all` e `polybet` (`esport`, `cyber`, `racing` →
//     `validation_error`). eSports não tem filtro próprio no histórico. O replay pede `all`
//     para nada ficar de fora em silêncio; se a casa recusar, cai para o que a página usou.
//
// NÃO DECIDE NADA: normaliza o item e sobe o cru. `status` e `betType` sobem como vieram;
// quem traduz é o `formatTicketTP` (content.js) + `casas/CASA_1WIN.md`.
(function () {
  // ── CRU para o servidor (s409, Projeto Ficha Sharpen) ───────────────────────────────
  // O objeto da CASA de onde cada bilhete saiu, para o SERVIDOR montar a Ficha (o adaptador
  // mora lá, `app/adaptadores/`). Vai num campo NOVO (`cru`) da mesma mensagem: a lista de
  // sempre segue intacta, e é ela que vira o texto. Erro aqui nunca sobe: sem cru, a
  // captura de hoje segue igual. `codigo` = o mesmo campo que o formatador imprime em
  // `[Código: …]`.
  const _cruDe = new WeakMap();
  function _marcarCru(b, cru) { try { _cruDe.set(b, cru); } catch (e) {} }
  function _crus(lista, campo, proprio) {
    const out = [];
    try {
      for (const b of lista || []) {
        const c = proprio ? b : _cruDe.get(b);
        const cod = b && b[campo];
        if (!c || cod == null || cod === "") continue;
        out.push({ codigo: String(cod), cru: proprio ? _semMarcas(c) : c });
      }
    } catch (e) {}
    return out;
  }
  // Tira só as marcas que o próprio inject põe no objeto da casa (`__aberta`).
  function _semMarcas(o) {
    const r = {};
    for (const k of Object.keys(o || {})) if (k.slice(0, 2) !== "__") r[k] = o[k];
    return r;
  }
  const RX_GW = /^https:\/\/api-gateway\.top-parser\.com\//i;       // onde o token se aprende
  const RX_LISTA = /\/bets\/history\/get-many(\?|$)/i;               // a lista de bilhetes
  const URL_LISTA = "https://api-gateway.top-parser.com/bets/history/get-many";
  const LIMITE = 150;                          // teto medido (151 → bad_request_error)
  const TETO_PAGINAS = 200;                    // 200 × 150 = 30 mil bilhetes

  const byId = new Map();                      // bet.id(string) → bilhete normalizado
  let respostas = 0;                           // respostas VÁLIDAS da lista (autodiagnóstico)
  let hdrs = null;                             // headers da última chamada com `token` (nunca sai daqui)
  let sportTypePagina = null;                  // o `sportType` que a página usou, quando visto
  let pedido = false;                          // o robô já pediu → pode arrancar o replay
  let loopAtivo = false;                       // trava: um replay por vez
  let fimReplay = false;                       // a varredura terminou
  let repetir = false;                         // pedido chegou durante a varredura → roda de novo
  let erro = "";                               // último erro do replay (vai no autodiagnóstico)
  const LOG = (...a) => { try { console.log("[SharpenUp tp_inject]", ...a); } catch (e) {} };
  LOG("hook instalado em", location.href);

  const of = window.fetch;                     // fetch ORIGINAL — o replay usa este

  // ── normalização (item do top-parser → objeto limpo) ───────────────────────────
  const _n = (v) => {
    if (v == null || v === "") return null;
    const x = Number(v);
    return isFinite(x) ? x : null;
  };
  const _s = (v) => (v == null ? "" : String(v));

  function parsePerna(s) {
    if (!s) return null;
    const m = s.match || {}, o = s.odd || {}, sp = s.sport || {}, cat = s.category || {}, t = s.tournament || {};
    const casa = _s(m.homeTeam && m.homeTeam.name), fora = _s(m.awayTeam && m.awayTeam.name);
    return {
      status: _n(s.status),                     // 0 pendente · 1 perdida · resto CRU
      meia: !!s.isHalfReturn,                   // meia vitória/derrota (asiática)
      jogo: casa && fora ? casa + " - " + fora : (casa || fora),
      inicio: _n(m.startAt),                    // unix em SEGUNDOS
      mercado: _s(o.groupName || (s.oddGroup && s.oddGroup.name)).trim(),
      selecao: _s(o.name),
      odd: _n(o.cf),                            // odd APOSTADA da perna
      esporte: _s(sp.name),                     // "Futebol", "Basquete" (pt da casa)
      pais: _s(cat.name),
      liga: _s(t.name).trim(),
      esports: !!t.isEsport,
    };
  }

  function parseItem(it) {
    const b = it && it.bet;
    if (!b || b.id == null) return null;
    return {
      id: String(b.id),                         // 9 dígitos — o [Código:] e a chave de dedup
      moeda: _s(b.currencyCode),                // "USDT" — a moeda da CONTA
      tipo: _s(b.betType),                      // "express" (CRU)
      status: _n(b.status),                     // 0 aberta · 1 perdida · 2/3/4 CRU
      stake: _n(b.amount),
      odd: _n(b.cf),                            // ⚠ cortada em 2 casas — é a que paga
      retorno: _n(b.profitAmount),              // ⚠ RETORNO, não lucro (aberta: o potencial)
      potencial: _n(b.possibleProfitAmount),
      bonus: _n(b.bonusAmount),
      bonusPct: _n(b.bonusPercent),
      freebet: _n(b.freebetAmount),
      carteira: _s(b.wallet),                   // "real"
      colocada: _s(b.createdAt),                // ISO UTC
      liquidada: _s(b.closeAt),                 // ISO UTC (só na liquidada)
      // `refundInfo` (oferta de cashout da aberta) fica de fora: muda a cada minuto.
      pernas: (Array.isArray(it.selections) ? it.selections : []).map(parsePerna).filter(Boolean),
    };
  }

  // Emite SEMPRE hook:true + respostas (heartbeat), mesmo com 0 bilhetes. NUNCA leva o token.
  function enviar() {
    try {
      window.postMessage({
        __sharpenupTPData: true, hook: true,
        bilhetes: Array.from(byId.values()), respostas: respostas, fim: fimReplay,
        cru: _crus(Array.from(byId.values()), "id"),
        semToken: !hdrs, erro: erro,
      }, "*");
    } catch (e) {}
  }

  // A versão LIQUIDADA vence a ABERTA (status 0).
  function guardar(b) {
    const ex = byId.get(b.id);
    if (!ex || ex.status === 0 || b.status !== 0) byId.set(b.id, b);
  }

  // Lê uma resposta da lista. Devolve `{n, total}`, `{erro}` ou null.
  function consumir(text) {
    if (typeof text !== "string") return null;
    let j;
    try { j = JSON.parse(text); } catch (e) { return null; }
    const r = j && j.result;
    if (!r || !Array.isArray(r.items)) {
      const e = j && Array.isArray(j.errors) && j.errors[0];
      return e ? { erro: String(e.code || e.message || "erro") } : null;
    }
    respostas++;
    for (const raw of r.items) {
      const b = parseItem(raw);
      if (b) { _marcarCru(b, raw); guardar(b); }
    }
    const total = r.meta && r.meta.total != null ? Number(r.meta.total) : null;
    LOG("bilhetes na resposta:", r.items.length, "· total:", byId.size, "· meta.total:", total);
    enviar();
    return { n: r.items.length, total: total };
  }

  // ── aprendizado ────────────────────────────────────────────────────────────────
  function _hdrsToObj(h) {
    const o = {};
    try {
      if (!h) return o;
      if (typeof h.forEach === "function") h.forEach((v, k) => { o[k] = v; });
      else if (typeof h === "object") for (const k in h) o[k] = h[k];
    } catch (e) {}
    return o;
  }
  const _temToken = (h) => Object.keys(h || {}).some((k) => k.toLowerCase() === "token" && h[k]);

  // Aprende de TODA chamada do gateway. Os headers são os da chamada com `token` mais recente
  // (a sessão pode renovar); o `sportType` vem só da chamada da lista.
  function aprender(url, headers, corpoTxt) {
    if (!RX_GW.test(String(url))) return;
    if (_temToken(headers)) {
      const primeiro = !hdrs;
      hdrs = headers;
      if (primeiro) LOG("token aprendido de", String(url).replace(RX_GW, "/"));
    }
    if (RX_LISTA.test(String(url)) && typeof corpoTxt === "string") {
      try { const c = JSON.parse(corpoTxt); if (c && typeof c.sportType === "string") sportTypePagina = c.sportType; } catch (e) {}
    }
    if (hdrs && pedido) arrancarReplay();
  }

  // ── replay ─────────────────────────────────────────────────────────────────────
  async function pedirPagina(sportType, offset) {
    // Sem `credentials`: a página não manda cookie para o gateway, e `include` exigiria um
    // CORS com credenciais que a casa não prometeu (lição do `credentials:include`).
    const r = await of.call(window, URL_LISTA, {
      method: "POST", headers: hdrs,
      body: JSON.stringify({ limit: LIMITE, offset: offset, sportType: sportType }),
    });
    return { ok: !!(r && r.ok), status: r && r.status, text: r ? await r.text() : "" };
  }

  // Varre a lista inteira de um `sportType`. true = chegou ao fim autoritativo.
  async function varrer(sportType) {
    let offset = 0;
    for (let i = 0; i < TETO_PAGINAS; i++) {
      let r;
      try { r = await pedirPagina(sportType, offset); }
      catch (e) { erro = "replay falhou: " + (e && e.message); LOG(erro); return false; }
      if (!r.ok) { erro = "replay parou · HTTP " + r.status; LOG(erro); return false; }
      const res = consumir(r.text);
      if (!res) { erro = "resposta da lista em formato desconhecido"; LOG(erro); return false; }
      if (res.erro) { erro = "a casa respondeu erro: " + res.erro + " (sportType " + sportType + ")"; LOG(erro); return false; }
      offset += res.n;                                         // avança pelo que VOLTOU
      if (res.n <= 0) return true;                             // lista vazia: acabou
      if (res.total != null && offset >= res.total) return true;   // fim AUTORITATIVO
    }
    LOG("teto de páginas atingido");
    return true;
  }

  async function arrancarReplay() {
    if (loopAtivo || fimReplay || !hdrs) return;
    loopAtivo = true;
    erro = "";
    try {
      // `all` cobre esportes e polybet. Se a casa passar a recusar, cai para o que a própria
      // página pediu (ou `sport`, o padrão dela), em vez de voltar vazio.
      const ok = await varrer("all");
      if (!ok && !/HTTP/.test(erro)) {
        const antes = erro;
        if (await varrer(sportTypePagina && sportTypePagina !== "all" ? sportTypePagina : "sport")) erro = "";
        else if (!erro) erro = antes;
      }
    } finally {
      loopAtivo = false;
      fimReplay = true;
      enviar();
      if (repetir) { repetir = false; fimReplay = false; byId.clear(); arrancarReplay(); }
    }
  }

  // O content pede o acumulado ao iniciar o robô → zera, re-envia e arranca o replay. Zerar é
  // a lição da s393 (DEX Sport): sem isso a 2ª rodada na mesma aba devolvia o mapa velho, e
  // aposta já liquidada subia como "em aberto".
  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (!d || !d.__sharpenupTPReq) return;
    pedido = true;
    if (loopAtivo) repetir = true;
    else { fimReplay = false; if (hdrs) byId.clear(); }
    enviar();
    arrancarReplay();
  });

  // ── fetch ── (medido: a página usa fetch)
  if (of && !of.__suTPW) {
    const w = function (...a) {
      const req = (a[0] && typeof a[0] === "object" && a[0].url) ? a[0] : null;
      const url = req ? req.url : a[0];
      const opts = a[1] || {};
      const corpoTxt = typeof opts.body === "string" ? opts.body : null;
      try {
        if (RX_GW.test(String(url))) aprender(url, _hdrsToObj(opts.headers || (req && req.headers)), corpoTxt);
      } catch (e) {}
      return of.apply(this, a).then((r) => {
        try {
          if (RX_GW.test(String(url)) && RX_LISTA.test(String(url))) {
            // 2º argumento SEMPRE: sem ele um clone abortado vira rejeição muda (s305).
            r.clone().text().then((t) => consumir(t), () => {});
          }
        } catch (e) {}
        return r;
      });
    };
    w.__suTPW = true;
    window.fetch = w;
  }

  // ── XMLHttpRequest (rede de segurança, caso a casa troque de transporte) ──
  const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send,
        osh = XMLHttpRequest.prototype.setRequestHeader;
  if (!os.__suTPW) {
    XMLHttpRequest.prototype.open = function (m, u) { this.__suTPU = u; this.__suTPH = {}; return oo.apply(this, arguments); };
    XMLHttpRequest.prototype.setRequestHeader = function (k, v) { try { this.__suTPH[k] = v; } catch (e) {} return osh.apply(this, arguments); };
    const s = function (body) {
      try {
        if (RX_GW.test(String(this.__suTPU))) {
          aprender(this.__suTPU, this.__suTPH, typeof body === "string" ? body : null);
          if (RX_LISTA.test(String(this.__suTPU))) {
            this.addEventListener("load", () => {
              try {
                const t = (this.responseType === "" || this.responseType === "text")
                  ? this.responseText : JSON.stringify(this.response);
                consumir(t);
              } catch (e) {}
            });
          }
        }
      } catch (e) {}
      return os.apply(this, arguments);
    };
    s.__suTPW = true;
    XMLHttpRequest.prototype.send = s;
  }
})();
