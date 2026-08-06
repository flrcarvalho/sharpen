// Mundo MAIN (só na Jonbet): lê as RESPOSTAS que a própria página recebe da API de histórico
// de apostas e repassa ao content script. A Jonbet roda **BetBy** (`sptpub.com`):
//
//   GET <apiUrl>/api/v1/my_bets/list
//       ?lang=pt-BR&skip=N&limit=M&status=<enum|vazio>&timestamp_from=&timestamp_to=&currency=BRL
//       Authorization: Bearer <token da sessão BetBy>
//   → { count: <total do filtro>, results: [ … ] }
//
// A Jonbet NÃO tem sportsbook próprio: o BetBy é renderizado por `bt-renderer.min.js` na
// PRÓPRIA página (não é iframe), então este inject engancha o fetch de jonbet.bet.br e alcança
// tudo. Quem for procurar no F12: filtre pelo PATH (`my_bets`), nunca pelo domínio da casa —
// o tráfego sai em `api-NN-sp-<hash>.sptpub.com` e fica soterrado sob um long-poll que dispara
// `api/v4/live/...` a cada ~2 s.
//
// REPLAY ATIVO (o "puxa sozinho"): a partir de uma requisição real da página o inject aprende
// url+headers (o Bearer é da própria sessão) e RE-EMITE incrementando `skip` até acabar.
// Espelha o paginarLoop do kto_inject / bf_inject / pn_inject.
//
// ⚠ ARMADILHA DO TOKEN (medida na casa real, s248): a página dispara a lista ANTES de o token
// chegar e toma **401**. O corpo do erro tem uma chave `status` que NÃO é status de bilhete:
//     {"description":"Unauthorized","status":401,"message":"Unauthorized"}
// Aprender essa requisição para o replay significa repaginar sem token e colher 401 em toda
// página — reportando `hook:true` + `respostas>0` + 0 bilhetes, que é exatamente o sintoma de
// "formato mudou". Por isso `capturarReq` SÓ guarda requisição que carregue `Authorization`, e
// `forward` SÓ processa corpo com `results` array.
//
// ⚠ ARMADILHA DA ODD: `total_k` vem "0" em toda PERDIDA, com `k` guardando a odd que o card
// mostra (6 de 6 na base real). Aqui o inject NÃO decide nada: entrega os dois campos crus e
// quem resolve é o `_oddJB` do content.js. É o mesmo desenho do `betOdds` da KTO.
//
// PAGINAÇÃO (provada ao vivo forçando limit=3 sobre 10 bilhetes): `skip` é offset real, `count`
// é constante entre páginas, a última página vem parcial e passar do fim devolve **200 com
// lista vazia** — nunca erro, nunca repetição. Logo a parada é dupla: `skip >= count` OU lista
// vazia. O avanço usa o tamanho que VOLTOU, não o `limit` pedido.
(function () {
  const RX = /\/my_bets\/list/i;               // endpoint da LISTA de bilhetes
  const byId = new Map();                      // id(string) → bilhete normalizado
  let respostas = 0;                           // respostas VÁLIDAS do endpoint (autodiagnóstico)
  let reqCtx = null;                           // {url, headers} de uma requisição AUTENTICADA
  let pedido = false;                          // o robô já pediu → pode arrancar o replay
  let loopAtivo = false;                       // trava: um replay por vez
  let fimReplay = false;                       // todas as URLs/variantes já foram repaginadas
  const aprendidas = new Map();                // chave(status) → url base (sem skip/limit)
  const LOG = (...a) => { try { console.log("[SharpenUp jb_inject]", ...a); } catch (e) {} };
  LOG("hook instalado em", location.href);

  const of = window.fetch;                     // fetch ORIGINAL — o replay usa este

  // `status` vazio devolve TODAS as abas (confirmado no reducer do próprio app: a lista aceita
  // "" como "sem filtro"). É o superconjunto — basta ele para varrer a conta inteira. Entra só
  // como VARIANTE: o que manda é sempre a URL que a página realmente disparou.
  const STATUS_VARIANTES = [""];

  // ── normalização (BetBy → objeto limpo) ──────────────────────────────────────
  // Dinheiro e odds vêm em STRING com PONTO decimal, em reais ("333.16", "1.87"). Não são
  // milésimos e não são pt-BR — `Number()` resolve; o parser de dinheiro BR estragaria.
  const _n = (v) => {
    if (v == null || v === "") return null;
    const x = Number(v);
    return isFinite(x) ? x : null;
  };

  function parseSel(s) {
    if (!s) return null;
    const d = s.desc || {};
    const comp = Array.isArray(d.competitors) ? d.competitors.map((c) => c && c.name).filter(Boolean) : [];
    const ligas = [];
    if (d.category && d.category.name) ligas.push(d.category.name);
    if (d.tournament && d.tournament.name) ligas.push(d.tournament.name);
    return {
      id: s.id != null ? String(s.id) : "",
      status: s.status || "",                  // won / lost / open / … (cru)
      mercado: s.market_name || "",            // "Handicap pontos" · "Total pontos" · "Vencedor"
      label: s.outcome_name || "",             // "Kharb, Anmol (-3.5)"
      linha: s.specifiers || "",               // "hcp=3.5" · "total=71.5"
      odd: _n(s.k),                            // odd da seleção
      oddRes: _n(s.result_k),                  // ⚠ acompanha o total_k: 0 na perdida
      aoVivo: !!s.live,
      esporte: (d.sport && d.sport.name) || "",
      jogo: comp.join(" vs "),
      ligas: ligas,
      inicio: _n(d.scheduled),                 // epoch em SEGUNDOS, como o timestamp do bilhete
      betBuilder: !!s.is_bet_builder,
      boost: !!s.boost,
    };
  }

  function parseBet(b) {
    if (!b || b.id == null) return null;
    const co = b.cashout || {};
    const tx = b.taxes || {};
    return {
      id: String(b.id),
      status: b.status || "",                  // cru; o de-para vive na CASA_JONBET.md
      tipo: b.type || "",                      // "1/1" = simples · "N/N" = múltipla · sistema
      moeda: b.currency || "",
      stake: _n(b.sum),                        // ⚠ é `sum`, não `stake`
      oddTotal: _n(b.total_k),                 // ⚠ "0" em TODA perdida — nunca usar sozinha
      oddBilhete: _n(b.k),                     // é daqui que sai a odd quando total_k zera
      retorno: _n(b.result_sum),               // liquidado (0 na perdida, ausente na aberta)
      potencial: _n(b.potential_win),          // aberta → retorno POTENCIAL, nunca "retorno"
      cashout: _n(b.cashout_amount),
      cashoutLiq: _n(co.amount_net),
      cashoutBruto: _n(co.amount_gross),
      imposto: _n(co.payout_tax),              // hoje 0 na Jonbet; se vier > 0, muda a conta
      payoutFinal: _n(tx.final_payout),        // idem: existe na estrutura, hoje ausente
      ts: _n(b.timestamp),                     // ⚠ SEGUNDOS (float) e JÁ local de São Paulo
      betBuilder: !!b.is_bet_builder,
      freebet: (b.freebet_data && (b.freebet_data.type || true)) || null,
      bonus: b.bonus != null ? b.bonus : null,
      combinacoes: Array.isArray(b.combinations) ? b.combinations.length : 0,
      sels: (Array.isArray(b.selections) ? b.selections : []).map(parseSel).filter(Boolean),
    };
  }

  // Emite SEMPRE hook:true + respostas (heartbeat), mesmo com 0 bilhetes — o content distingue
  // "hook não carregou" de "endpoint respondeu, lemos 0" (mesmo autodiagnóstico das outras).
  function enviar() {
    try {
      window.postMessage({
        __sharpenupJBData: true, hook: true,
        bilhetes: Array.from(byId.values()), respostas: respostas, fim: fimReplay,
      }, "*");
    } catch (e) {}
  }

  // Guarda o bilhete. O mesmo id volta em abas diferentes (aberto × resolvido): a versão
  // RESOLVIDA vence a ABERTA (o dinheiro só é final depois de liquidado).
  function guardar(b) {
    const ex = byId.get(b.id);
    if (!ex) { byId.set(b.id, b); return; }
    const aberto = (x) => !x.status || x.status === "open";
    if (aberto(ex) && !aberto(b)) byId.set(b.id, b);
  }

  // Processa uma resposta. Devolve {count, n} p/ o replay decidir se continua, ou null.
  // A guarda `Array.isArray(j.results)` é o que barra o corpo do 401 — que, repare, TEM uma
  // chave `status` e passaria em qualquer checagem ingênua de "veio JSON".
  function forward(url, text) {
    if (!RX.test(String(url)) || typeof text !== "string") return null;
    let j;
    try { j = JSON.parse(text); } catch (e) { return null; }
    if (!j || !Array.isArray(j.results)) {
      if (j && j.status === 401) LOG("401 ignorado (requisição sem token) —", String(url));
      return null;
    }
    respostas++;
    for (const raw of j.results) {
      const b = parseBet(raw);
      if (b) guardar(b);
    }
    aprender(url);
    LOG("bilhetes na resposta:", j.results.length, "· total:", byId.size, "· count:", j.count);
    enviar();
    return { count: Number(j.count), n: j.results.length };
  }

  // ── replay ativo: repagina por `skip` até acabar ──────────────────────────────
  function _hdrsToObj(h) {
    const o = {};
    try {
      if (!h) return o;
      if (typeof h.forEach === "function") h.forEach((v, k) => { o[k] = v; });
      else if (typeof h === "object") for (const k in h) o[k] = h[k];
    } catch (e) {}
    return o;
  }

  function _temToken(h) {
    for (const k in (h || {})) if (String(k).toLowerCase() === "authorization" && h[k]) return true;
    return false;
  }

  // URL base = a URL da página SEM skip/limit (que o replay controla). A chave é o `status` —
  // uma entrada por aba, para não repaginar a mesma lista duas vezes.
  function aprender(url) {
    let u;
    try { u = new URL(String(url), location.href); } catch (e) { return; }
    if (!RX.test(u.pathname)) return;
    const chave = u.searchParams.get("status") || "_todas_";
    if (!aprendidas.has(chave)) {
      aprendidas.set(chave, u.href);
      LOG("lista aprendida · status =", JSON.stringify(chave));
    }
  }

  function capturarReq(url, headers) {
    if (!RX.test(String(url))) return;
    // ⚠ SEM TOKEN NÃO SE APRENDE NADA. A 1ª chamada da página sai antes de o token existir e
    // volta 401; guardá-la faria o replay inteiro rodar deslogado.
    if (!_temToken(headers)) { LOG("requisição sem Authorization ignorada (é a que toma 401)"); return; }
    aprender(url);
    if (!reqCtx) {
      reqCtx = { url: String(url), headers: headers || {} };
      LOG("requisição autenticada capturada p/ replay");
    }
    if (pedido) arrancarReplay();
  }

  function comPagina(base, skip, limit) {
    try {
      const u = new URL(base, location.href);
      u.searchParams.set("skip", String(skip));
      u.searchParams.set("limit", String(limit));
      return u.href;
    } catch (e) { return base; }
  }
  function comStatus(base, status) {
    try {
      const u = new URL(base, location.href);
      u.searchParams.set("status", status);
      u.searchParams.set("skip", "0");
      return u.href;
    } catch (e) { return null; }
  }

  const PAGINA = 100;      // pedimos 100; o avanço usa o tamanho que VOLTAR
  const TETO_PAGINAS = 200;

  async function paginar(baseUrl) {
    let skip = 0;
    for (let i = 0; i < TETO_PAGINAS; i++) {
      let r;
      try {
        r = await of.call(window, comPagina(baseUrl, skip, PAGINA), {
          method: "GET",
          headers: (reqCtx && reqCtx.headers) || {},
          credentials: "include",
        });
      } catch (e) { LOG("erro no replay:", e && e.message); return; }
      if (!r || !r.ok) { LOG("replay parou · HTTP", r && r.status); return; }
      let res;
      try { res = forward(r.url || baseUrl, await r.text()); } catch (e) { return; }
      if (!res) return;
      // Fim autoritativo, com dupla garantia: a casa devolve 200 + lista vazia depois do fim,
      // e `count` é o total do filtro. Avança pelo que VOLTOU (`res.n`), nunca pelo PAGINA
      // pedido — se a API limitar o tamanho da página, o loop se autocorrige em vez de pular.
      if (!res.n) return;
      skip += res.n;
      if (isFinite(res.count) && skip >= res.count) return;
    }
    LOG("teto de páginas atingido em", baseUrl);
  }

  async function arrancarReplay() {
    if (loopAtivo || fimReplay || !reqCtx) return;
    loopAtivo = true;
    try {
      // 1) toda lista que a página realmente disparou (autoritativo)
      for (const url of Array.from(aprendidas.values())) await paginar(url);
      // 2) `status` vazio = todas as abas — garante o que o operador não clicou. Variante
      //    inválida volta erro e é ignorada; a URL aprendida continua valendo.
      for (const st of STATUS_VARIANTES) {
        if (aprendidas.has(st || "_todas_")) continue;
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
    if (!d || !d.__sharpenupJBReq) return;
    pedido = true;
    enviar();
    arrancarReplay();
  });

  // ── fetch (é por aqui que o BetBy pede a lista) ──
  if (of && !of.__suJBW) {
    const w = function (...a) {
      const url = (a[0] && a[0].url) || a[0];
      const opts = a[1] || (a[0] && typeof a[0] === "object" ? a[0] : null);
      try { if (RX.test(String(url))) capturarReq(url, _hdrsToObj(opts && opts.headers)); } catch (e) {}
      return of.apply(this, a).then((r) => {
        try { if (RX.test(String(url))) r.clone().text().then((t) => forward(url, t)); } catch (e) {}
        return r;
      });
    };
    w.__suJBW = true;
    window.fetch = w;
  }

  // ── XMLHttpRequest (rede de segurança: hoje o BetBy usa fetch, mas o custo é 10 linhas) ──
  const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send, osh = XMLHttpRequest.prototype.setRequestHeader;
  if (!os.__suJBW) {
    XMLHttpRequest.prototype.open = function (m, u) { this.__suJBU = u; this.__suJBH = {}; return oo.apply(this, arguments); };
    XMLHttpRequest.prototype.setRequestHeader = function (k, v) { try { this.__suJBH[k] = v; } catch (e) {} return osh.apply(this, arguments); };
    const s = function () {
      try {
        if (RX.test(String(this.__suJBU))) {
          capturarReq(this.__suJBU, this.__suJBH);
          this.addEventListener("load", () => { try { forward(this.__suJBU, this.responseText); } catch (e) {} });
        }
      } catch (e) {}
      return os.apply(this, arguments);
    };
    s.__suJBW = true;
    XMLHttpRequest.prototype.send = s;
  }
})();
