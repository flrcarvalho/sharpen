// Mundo MAIN (Vave — plataforma própria `softlabs`): lê o histórico de apostas que a página
// pede e BUSCA a lista inteira ele mesmo, repassando ao content script.
//
//   GET platform.<host da casa>/api/v2/bet/history?page=&from=AAAA-MM-DD&till=AAAA-MM-DD&limit=&lang=
//   → { status:"ok", code:200, data: { bets: { bets:[…], events:[…], competitors:[…],
//       leagues:[…], sportCategories:[…], sports:[…], results:[…], players:[…], … },
//       page, limit, total } }
//
// PLATAFORMA PRÓPRIA (recon s425, conta do Feca, USDT). O app é `vavemain` (bundle em
// cloudfront, Sentry em `sentry.softlabs.com`) e a API mora num subdomínio da própria casa,
// `platform.<host>`. Não é 1xBet (apesar do layout parecido), BetBy, Altenar, Kambi nem
// BetConstruct. A casa roda em DOMÍNIO NUMERADO (`34evav91.com` no recon; `vave.com` serve o
// mesmo app), então nada aqui fixa o host: a API sai do host da aba.
//
// O PAYLOAD É NORMALIZADO: o bilhete traz `details[]` com `event_id`, `league_id`,
// `marketId`, `outcomeId` e `specifiers`, e os nomes vivem em tabelas irmãs (`events`,
// `competitors`, `leagues`…). Mercado e seleção NÃO vêm no histórico: saem de dois
// dicionários públicos da casa (`/api/market-descriptions/get-all-markets/<lang>` e
// `…/get-all-outcomes/<lang>`, 1,4 MB e 100 KB, sem auth), em TEMPLATE Sportradar e em
// inglês mesmo na rota `/pt` (`{$competitor2} clean sheet`, `over {total}`,
// `{$competitor2} ({-hcp})`). O inject resolve o template; o cru (`specifiers`) sobe junto.
//
// AUTH É `authorization: Bearer` + `client-timezone`, por XHR (medido). O token também fica
// em `localStorage.customer.token`, então o replay arranca A FRIO, sem esperar requisição
// nenhuma da página — e é isso que cobre o domínio novo que não está no manifest (o popup
// injeta tarde e a página já fez as chamadas dela). O valor nunca sai deste arquivo: a
// mensagem para o content leva só `semToken`.
//
// O QUE FOI MEDIDO na API, com o token da sessão:
//   • sem o header a resposta é HTTP 200 com `code: 401` no corpo. ERRO VOLTA COM 200: quem
//     confia no `r.ok` conta erro como resposta. A forma decide, nunca o status.
//   • `limit` tem teto 100 (1000 → `code: 400`, "less than or equal to 100").
//   • `total` é o número de PÁGINAS, não de bilhetes (limit 5 sobre 11 → total 3, a página
//     3 traz 1). Fim AUTORITATIVO = `page >= total`.
//   • sem `status` vem tudo (é a aba "Todos"). O filtro da tela usa 0 pendente · 1 perdida ·
//     2 ganhou · 3 devolvida · 8 "Pagamento" (cashout). A conta do recon só tinha perdidas.
//   • `from` de 2020 é aceito (a janela não tem teto medido).
//
// NÃO DECIDE NADA: normaliza o bilhete e sobe o cru. `status` sobe como veio; quem traduz é o
// `formatTicketVV` (content.js) + `casas/CASA_VAVE.md`.
(function () {
  // ── CRU para o servidor (s409, Projeto Ficha Sharpen) ───────────────────────────────
  // O objeto da CASA de onde cada bilhete saiu, para o SERVIDOR montar a Ficha (o adaptador
  // mora lá, `app/adaptadores/vv.py`, s427). Vai num
  // campo NOVO (`cru`) da mesma mensagem: a lista de sempre segue intacta, e é ela que vira o
  // texto. Erro aqui nunca sobe. Como o payload é normalizado, o cru de um bilhete leva as
  // linhas das tabelas irmãs que ele usa — sozinho, o `details[]` é só um punhado de ids.
  // `userId` sai aqui: identifica o cliente e não está na lista fechada do filtro.
  //
  // DICIONÁRIO (s427): o nome do mercado e da seleção NÃO vem no histórico, só o id; ele mora
  // nos dois dicionários públicos da casa (§2.5 da CASA_VAVE). O cru leva as linhas que o
  // bilhete usa, verbatim (o template, sem resolver), para o adaptador `vv` do servidor montar o
  // nome sozinho. Sai na hora do ENVIO, não da leitura: a página pode responder a lista antes de
  // o dicionário carregar, e o `fim` do replay sempre chega com ele. Sem dicionário, sem a chave
  // (o servidor recusa e o texto leva o bilhete à IA).
  const _cruDe = new WeakMap();
  function _dicDe(bet) {
    if (!dic) return null;
    const mercados = {}, selecoes = {};
    for (const d of (Array.isArray(bet.details) ? bet.details : [])) {
      const m = dic.mercados.get(_s(d && d.marketId)), s = dic.selecoes.get(_s(d && d.outcomeId));
      if (m != null) mercados[_s(d.marketId)] = m;
      if (s != null) selecoes[_s(d.outcomeId)] = s;
    }
    return { mercados: mercados, selecoes: selecoes };
  }
  function _crus(lista) {
    const out = [];
    try {
      for (const b of lista || []) {
        const c = _cruDe.get(b);
        if (!c || !b.id) continue;
        const dc = _dicDe(c.bet);
        out.push({ codigo: String(b.id), cru: dc ? Object.assign({}, c, { dicionario: dc }) : c });
      }
    } catch (e) {}
    return out;
  }
  function _montarCru(raw, bt, ix) {
    try {
      const bet = {};
      for (const k of Object.keys(raw)) if (k !== "userId") bet[k] = raw[k];
      const det = Array.isArray(raw.details) ? raw.details : [];
      const evs = det.map((d) => ix.eventos.get(String(d.event_id))).filter(Boolean);
      const ids = (arr) => new Set(arr.filter((x) => x != null).map(String));
      const times = ids([].concat(...evs.map((e) => [e.competitor1Id, e.competitor2Id])));
      const ligas = ids(det.map((d) => d.league_id).concat(evs.map((e) => e.league_id)));
      const ligasObj = Array.from(ligas).map((l) => ix.ligas.get(l)).filter(Boolean);
      const paises = ids(ligasObj.map((l) => l.sportCategoryId));
      const esportes = ids(evs.map((e) => e.sport_id));
      const evIds = ids(evs.map((e) => e.id));
      const de = (arr, set, chave) => (Array.isArray(arr) ? arr : []).filter((x) => x && set.has(String(x[chave || "id"])));
      return {
        bet: bet, events: evs, competitors: de(bt.competitors, times), leagues: ligasObj,
        sportCategories: de(bt.sportCategories, paises), sports: de(bt.sports, esportes),
        results: de(bt.results, evIds, "eventId"),
      };
    } catch (e) { return null; }
  }

  const RX_API = /^https:\/\/platform\.[^/]+\/api\//i;            // onde o token se aprende
  const RX_LISTA = /\/api\/v2\/bet\/history(\?|$)/i;                 // a lista de bilhetes
  const LIMITE = 100;                          // teto medido (1000 → code 400)
  const TETO_PAGINAS = 300;                    // 300 × 100 = 30 mil bilhetes
  const DIAS_HISTORICO = 1095;                 // 3 anos, como as outras casas de replay

  const byId = new Map();                      // id(string) → bilhete normalizado
  let respostas = 0;                           // respostas VÁLIDAS da lista (autodiagnóstico)
  let hdrs = null;                             // headers da última chamada com Bearer (nunca sai daqui)
  let base = null;                             // `https://platform.<host>` visto numa chamada real
  let dic = null;                              // { mercados: Map, selecoes: Map } — null = não carregou
  let pedido = false;                          // o robô já pediu → pode arrancar o replay
  let loopAtivo = false;                       // trava: um replay por vez
  let fimReplay = false;                       // a varredura terminou
  let repetir = false;                         // pedido chegou durante a varredura → roda de novo
  let erro = "";                               // último erro do replay (vai no autodiagnóstico)
  const LOG = (...a) => { try { console.log("[SharpenUp vv_inject]", ...a); } catch (e) {} };
  LOG("hook instalado em", location.href);

  const of = window.fetch;                     // fetch ORIGINAL — o replay usa este

  // ── normalização ─────────────────────────────────────────────────────────────
  const _n = (v) => {
    if (v == null || v === "") return null;
    const x = Number(v);
    return isFinite(x) ? x : null;
  };
  const _s = (v) => (v == null ? "" : String(v));

  // `specifiers` = "quarternr=1|total=42.5" → { quarternr: "1", total: "42.5" }
  function _spec(txt) {
    const o = {};
    for (const par of _s(txt).split("|")) {
      const i = par.indexOf("=");
      if (i > 0) o[par.slice(0, i).trim()] = par.slice(i + 1).trim();
    }
    return o;
  }
  const _ordinal = (v) => {
    const n = parseInt(v, 10);
    if (!isFinite(n)) return v;
    const r = n % 100;
    return n + ((r >= 11 && r <= 13) ? "th" : ({ 1: "st", 2: "nd", 3: "rd" })[n % 10] || "th");
  };
  // Sinal do template Sportradar: `{+hcp}` mostra o valor com sinal; `{-hcp}`, o oposto.
  // Trabalha sobre o TEXTO do número, para não mudar a grafia que a casa mandou (1.50 fica 1.50).
  function _sinal(v, inverte) {
    const t = _s(v).trim();
    if (!t || !isFinite(Number(t))) return t;
    if (Number(t) === 0) return "0";
    const neg = t[0] === "-";
    const abs = t.replace(/^[+-]/, "");
    return (neg !== !!inverte) ? "-" + abs : "+" + abs;
  }
  // Resolve `{$competitor1}`, `{!quarternr}`, `{+hcp}`, `{-hcp}`, `{total}`. Placeholder sem
  // valor FICA como veio: inventar texto seria pior que o template cru, e o `specifiers` vai no
  // bloco para a IA conferir.
  function _template(t, spec, c1, c2) {
    return _s(t).replace(/\{([!+\-$%]?)([^}]+)\}/g, (m, op, k) => {
      if (op === "$") {
        if (k === "competitor1") return c1 || m;
        if (k === "competitor2") return c2 || m;
        if (k === "event") return (c1 && c2) ? c1 + " - " + c2 : m;
        return m;
      }
      const v = spec[k];
      if (v == null || v === "") return m;
      if (op === "!") return _ordinal(v);
      if (op === "+") return _sinal(v, false);
      if (op === "-") return _sinal(v, true);
      return v;                                   // `{x}` e `{%player}` (id cru, sem tabela)
    });
  }

  // Data "AAAA-MM-DD hh:mm:ss" da API é UTC (medido: `events[].time` 17:00:00 = `ts` 17:00Z).
  const _utc = (txt) => {
    const t = Date.parse(_s(txt).replace(" ", "T") + "Z");
    return isFinite(t) ? Math.floor(t / 1000) : null;
  };

  // Uma resposta = um lote com as tabelas irmãs. Os índices são por lote, nunca globais.
  function _indices(bt) {
    const por = (arr) => { const m = new Map(); for (const x of (Array.isArray(arr) ? arr : [])) if (x && x.id != null) m.set(String(x.id), x); return m; };
    return {
      eventos: por(bt.events), times: por(bt.competitors), ligas: por(bt.leagues),
      paises: por(bt.sportCategories), esportes: por(bt.sports),
    };
  }

  function parsePerna(d, ix) {
    if (!d) return null;
    const ev = ix.eventos.get(_s(d.event_id)) || {};
    const c1 = _s((ix.times.get(_s(ev.competitor1Id)) || {}).name) || _s(ev.team1);
    const c2 = _s((ix.times.get(_s(ev.competitor2Id)) || {}).name) || _s(ev.team2);
    const liga = ix.ligas.get(_s(d.league_id || ev.league_id)) || {};
    const pais = ix.paises.get(_s(liga.sportCategoryId)) || {};
    const esp = ix.esportes.get(_s(ev.sport_id || liga.sport_id)) || {};
    const spec = _spec(d.specifiers);
    const mTpl = dic ? dic.mercados.get(_s(d.marketId)) : null;
    const sTpl = dic ? dic.selecoes.get(_s(d.outcomeId)) : null;
    return {
      status: _n(d.status),                     // 0 aberta · 1 perdida · 2 ganha · 3 devolvida (20bet, s428) · resto CRU
      odd: _n(d.value != null ? d.value : d.odds),
      jogo: c1 && c2 ? c1 + " - " + c2 : (_s(ev.name) || c1 || c2),
      inicio: _n(ev.ts) != null ? _n(ev.ts) : _utc(d.event_time),   // unix em SEGUNDOS
      mercado: mTpl != null ? _template(mTpl, spec, c1, c2).trim() : "",
      selecao: sTpl != null ? _template(sTpl, spec, c1, c2).trim() : "",
      mercadoId: _n(d.marketId), selecaoId: _n(d.outcomeId),
      especificadores: _s(d.specifiers),
      esporte: _s(esp.name),                    // "Football", "Basketball" (inglês da casa)
      pais: _s(pais.name),
      liga: _s(liga.name).trim(),
    };
  }

  function parseBet(b, ix) {
    if (!b || b.id == null) return null;
    const tx = b.taxesData || {};
    return {
      id: String(b.id),                         // 7 dígitos — o "#" do card, o [Código:] e a chave
      status: _n(b.status),                     // 0 pendente · 1 perdida · 2/3/8 CRU (filtro da tela)
      tipo: _s(b.typeName).replace(/^.*_\._/, ""),   // "accumulator" · "single bet" (CRU)
      sistema: _n(b.system),
      moeda: _s(b.currency),                    // "USDT" — a moeda da CONTA
      stake: _n(b.amount),
      stakeTotal: _n(b.fullAmount),
      bonus: _n(b.bonusAmount),
      freebet: _n(b.freebetAmount),
      odd: _n(b.value),                         // a odd do card (9.19), já o produto das pernas
      ganho: _n(b.win),                         // ⚠ NÃO MEDIDO em ganha (a conta só tinha perdas)
      ganhoTotal: _n(b.winFull),                // ⚠ idem
      cashout: _n(b.betCashoutAmount),          // ⚠ idem
      potencial: _n(tx.potentialWinAmount),     // stake × odd (30 × 9,19 = 275,70, medido)
      colocada: _n(b.ts),                       // unix em SEGUNDOS (card = ts em São Paulo)
      liquidada: _utc(b.finishedAt),            // ⚠ fuso NÃO provado; o formatador não usa
      betBuilder: b.betBetBuilderId != null,
      // Bet Builder (medido na 20bet, s428): a perna única só diz "BetBuilder"; as seleções do
      // cupom vêm prontas aqui, no idioma da conta. Espaço/TAB colapsados: TAB é coluna do TSV.
      legsBB: (Array.isArray(b.betBetBuilderLegs) ? b.betBetBuilderLegs : [])
        .map((x) => _s(x).replace(/\s+/g, " ").trim()).filter(Boolean),
      pernas: (Array.isArray(b.details) ? b.details : []).map((d) => parsePerna(d, ix)).filter(Boolean),
    };
  }

  // Emite SEMPRE hook:true + respostas (heartbeat), mesmo com 0 bilhetes. NUNCA leva o token.
  function enviar() {
    try {
      window.postMessage({
        __sharpenupVVData: true, hook: true,
        bilhetes: Array.from(byId.values()), respostas: respostas, fim: fimReplay,
        cru: _crus(Array.from(byId.values())),
        semToken: !_headers(), semDicionario: !dic, erro: erro,
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
    const d = j && j.data;
    const bt = d && d.bets;
    if (!bt || !Array.isArray(bt.bets)) {
      if (j && (j.code != null || j.status)) {
        const msg = (j.data && Array.isArray(j.data.messages) && j.data.messages[0]) || j.message || j.status;
        return { erro: "code " + _s(j.code) + (msg ? " · " + _s(msg) : "") };
      }
      return null;
    }
    respostas++;
    const ix = _indices(bt);
    for (const raw of bt.bets) {
      const b = parseBet(raw, ix);
      if (!b) continue;
      const c = _montarCru(raw, bt, ix);
      if (c) { try { _cruDe.set(b, c); } catch (e) {} }
      guardar(b);
    }
    LOG("bilhetes na resposta:", bt.bets.length, "· total:", byId.size, "· páginas:", d.total);
    enviar();
    return { n: bt.bets.length, total: _n(d.total), pagina: _n(d.page) };
  }

  // ── aprendizado ────────────────────────────────────────────────────────────────
  const _temBearer = (h) => Object.keys(h || {}).some((k) => k.toLowerCase() === "authorization" && /^Bearer\s+\S/i.test(_s(h[k])));

  function aprender(url, headers) {
    const u = _s(url);
    if (!RX_API.test(u)) return;
    try { base = new URL(u).origin; } catch (e) {}
    if (_temBearer(headers)) {
      const primeiro = !hdrs;
      const h = {};
      for (const k of Object.keys(headers)) h[k] = headers[k];
      hdrs = h;
      if (primeiro) LOG("token aprendido de", u.replace(/^https:\/\/[^/]+/, "").split("?")[0]);
    }
    if (_headers() && pedido) arrancarReplay();
  }

  // Partida a frio: o Bearer da sessão fica em `localStorage.customer.token` (medido). Só
  // vale quando nenhuma chamada real foi vista; a chamada real manda, porque a sessão renova.
  function _headers() {
    if (hdrs) return hdrs;
    try {
      const ls = window.localStorage;
      const c = ls && JSON.parse(ls.getItem("customer") || "null");
      const tk = c && typeof c.token === "string" ? c.token.trim() : "";
      if (!tk) return null;
      let tz = "America/Sao_Paulo";
      try { tz = Intl.DateTimeFormat().resolvedOptions().timeZone || tz; } catch (e) {}
      return { accept: "application/json, text/plain, */*", "content-type": "application/json",
               authorization: "Bearer " + tk, "client-timezone": tz };
    } catch (e) { return null; }
  }

  const _aqui = () => { try { return new URL(location.href); } catch (e) { return null; } };
  function _base() {
    if (base) return base;
    const u = _aqui();
    return "https://platform." + (u ? u.hostname : "").replace(/^www\./i, "");
  }

  // ── replay ─────────────────────────────────────────────────────────────────────
  const _dia = (t) => {
    const d = new Date(t);
    const p = (x) => String(x).padStart(2, "0");
    return d.getFullYear() + "-" + p(d.getMonth() + 1) + "-" + p(d.getDate());
  };

  // Os dois dicionários são públicos e quase imutáveis: carrega uma vez por página. Falhar
  // aqui NÃO para a captura: o bloco sai com o id do mercado e o template cru fica de fora.
  async function carregarDicionario() {
    if (dic) return;
    const lang = (_s((_aqui() || {}).pathname).match(/^\/([a-z]{2})(\/|$)/i) || [])[1] || "pt";
    try {
      const pega = async (tipo) => {
        const r = await of.call(window, _base() + "/api/market-descriptions/get-all-" + tipo + "/" + lang);
        const j = JSON.parse(r ? await r.text() : "null");
        const it = j && j.data && Array.isArray(j.data.items) ? j.data.items : null;
        if (!it) throw new Error(tipo + " em formato desconhecido");
        const m = new Map();
        for (const x of it) if (x && x.id != null) m.set(String(x.id), _s(x.name));
        return m;
      };
      const mercados = await pega("markets");
      const selecoes = await pega("outcomes");
      dic = { mercados, selecoes };
    } catch (e) { LOG("dicionário indisponível:", e && e.message); }
  }

  async function pedirPagina(pagina, de, ate) {
    const q = new URLSearchParams({ page: String(pagina), from: de, till: ate, limit: String(LIMITE), lang: "pt" });
    // Sem `credentials`: a auth é o Bearer, e `include` exigiria um CORS com credenciais que a
    // casa não prometeu (lição do `credentials:include`).
    const r = await of.call(window, _base() + "/api/v2/bet/history?" + q.toString(), { method: "GET", headers: _headers() });
    return { ok: !!(r && r.ok), status: r && r.status, text: r ? await r.text() : "" };
  }

  // Varre a lista inteira. true = chegou ao fim autoritativo.
  async function varrer() {
    const agora = Date.now();
    const de = _dia(agora - DIAS_HISTORICO * 86400000), ate = _dia(agora + 86400000);
    for (let pagina = 1; pagina <= TETO_PAGINAS; pagina++) {
      let r;
      try { r = await pedirPagina(pagina, de, ate); }
      catch (e) { erro = "replay falhou: " + (e && e.message); LOG(erro); return false; }
      if (!r.ok) { erro = "replay parou · HTTP " + r.status; LOG(erro); return false; }
      const res = consumir(r.text);
      if (!res) { erro = "resposta da lista em formato desconhecido"; LOG(erro); return false; }
      if (res.erro) { erro = "a casa respondeu erro: " + res.erro; LOG(erro); return false; }
      if (res.n <= 0) return true;                                 // lista vazia: acabou
      if (res.total != null && pagina >= res.total) return true;   // fim AUTORITATIVO (páginas)
    }
    LOG("teto de páginas atingido");
    return true;
  }

  async function arrancarReplay() {
    if (loopAtivo || fimReplay || !_headers()) return;
    loopAtivo = true;
    erro = "";
    try {
      await carregarDicionario();
      await varrer();
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
    if (!d || !d.__sharpenupVVReq) return;
    pedido = true;
    if (loopAtivo) repetir = true;
    else { fimReplay = false; if (_headers()) byId.clear(); }
    enviar();
    arrancarReplay();
  });

  // ── XMLHttpRequest ── (medido: a página usa XHR, com os headers por `setRequestHeader`)
  const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send,
        osh = XMLHttpRequest.prototype.setRequestHeader;
  if (!os.__suVVW) {
    XMLHttpRequest.prototype.open = function (m, u) { this.__suVVU = u; this.__suVVH = {}; return oo.apply(this, arguments); };
    XMLHttpRequest.prototype.setRequestHeader = function (k, v) { try { this.__suVVH[k] = v; } catch (e) {} return osh.apply(this, arguments); };
    const s = function (body) {
      try {
        if (RX_API.test(_s(this.__suVVU))) {
          aprender(this.__suVVU, this.__suVVH);
          if (RX_LISTA.test(_s(this.__suVVU))) {
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
    s.__suVVW = true;
    XMLHttpRequest.prototype.send = s;
  }

  // ── fetch ── (rede de segurança, caso a casa troque de transporte)
  if (of && !of.__suVVW) {
    const _hdrsToObj = (h) => {
      const o = {};
      try {
        if (!h) return o;
        if (typeof h.forEach === "function") h.forEach((v, k) => { o[k] = v; });
        else if (typeof h === "object") for (const k in h) o[k] = h[k];
      } catch (e) {}
      return o;
    };
    const w = function (...a) {
      const req = (a[0] && typeof a[0] === "object" && a[0].url) ? a[0] : null;
      const url = req ? req.url : a[0];
      const opts = a[1] || {};
      try { if (RX_API.test(_s(url))) aprender(url, _hdrsToObj(opts.headers || (req && req.headers))); } catch (e) {}
      return of.apply(this, a).then((r) => {
        try {
          if (RX_API.test(_s(url)) && RX_LISTA.test(_s(url))) {
            // 2º argumento SEMPRE: sem ele um clone abortado vira rejeição muda (s305).
            r.clone().text().then((t) => consumir(t), () => {});
          }
        } catch (e) {}
        return r;
      });
    };
    w.__suVVW = true;
    window.fetch = w;
  }

  // Partida a frio: com o token no `localStorage`, o heartbeat já sai dizendo que há sessão.
  enviar();
})();
