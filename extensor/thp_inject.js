// Mundo MAIN (Thunderpick — plataforma própria): lê as apostas que a página pede e BUSCA a
// lista inteira ele mesmo, repassando ao content script.
//
//   GET /api/users/wagers/settled?take=&skip=&sortColumn=finishTime  (liquidadas, paginadas; s457)
//   GET /api/wagers/v2/resolved?take=&skip=&sortColumn=finishTime    (rota ANTIGA; 404 desde nov/2026)
//   GET /api/wagers/v2/pending                                        (abertas, tudo de uma vez)
//   → { statusCode:200, ok:true, data: { wagers:[…], totalWagersCount } }
//   GET /api/wagers/events?eventIds=1&eventIds=2…                     (nome/início/liga do jogo; s457)
//   → { statusCode:200, ok:true, data: [ {id, name, startTime, competition, homeCompetitor, awayCompetitor} ] }
//
// PLATAFORMA PRÓPRIA (recon 22/10/2026, conta do Feca, EUR). Front React Router v7, API
// `/api/*` no MESMO domínio, atrás da Cloudflare; os feeds são Oddin.gg e DATA.BET. Não é
// Altenar, BetBy, Kambi, BetConstruct nem softlabs.
//
// A MUDANÇA DE 17/11/2026 (s457, medida na conta do Feca, 132 liquidadas): a casa tirou a rota
// `/api/wagers/v2/resolved` do ar (404) e a tela "Settled" passou a pedir
// `/api/users/wagers/settled`, com o MESMO envelope e a mesma paginação. Só que o bilhete
// chega SEM o jogo: saíram `eventName`, `eventStartTime`, `competition`, `homeCompetitor` e
// `awayCompetitor`, do topo e das pernas. A página os busca à parte em `/api/wagers/events`
// (aceitou os 124 eventos da conta numa chamada). Este inject ENCAIXA esses campos de volta
// no objeto da casa, só onde faltam, e o bilhete volta à forma de antes: nem o
// `formatTicketTHP` nem o adaptador `thp` do servidor precisam saber da mudança.
// Bilhete cujo evento não chegou sobe sem o jogo; nada é inventado.
//
// AUTH é o header `thunderpick-token` (64 caracteres, opaco, não é JWT), mandado pela página
// em toda chamada de `/api/`. Sem ele: HTTP 403 com `errorCode 2013`. O mesmo valor fica em
// `localStorage["thp.sessionData"].sessionId`, então o replay arranca A FRIO. O valor nunca
// sai deste arquivo: a mensagem para o content leva só `semToken`.
//
// O QUE FOI MEDIDO na API, com o token da sessão:
//   • DINHEIRO em CENTAVOS DE EURO: `amount` 4383 = card 43,83 EUR; `outcome` 7100 = 71,00.
//     A conta guarda tudo em euro; a exibição em USD da tela usa o câmbio do DIA. Por isso a
//     moeda daqui é sempre `EUR` (a API não manda campo de moeda).
//   • `wagerId` tem DUAS séries (Combo ~2,2M; PreMatch/InPlays 4,9M–10,3M). O código leva o
//     prefixo do tipo, `C` ou `S`, para as séries nunca colidirem na dedup.
//   • A página pede `take=10` (antes 20); `take=100/500/1000` foram aceitos (com 132
//     liquidadas, `take=500` devolveu as 132). Fim AUTORITATIVO = `totalWagersCount` da 1ª
//     PÁGINA: `skip` além do fim devolve `{wagers:[], totalWagersCount:0}`, então o total de
//     uma página tardia mente. Vale nas duas rotas (medido de novo em 17/11).
//   • `/pending` não pagina e não tem parâmetro.
//
// NÃO DECIDE NADA: normaliza o bilhete e sobe o cru. `wagerUIState` sobe como veio; quem traduz
// é o `formatTicketTHP` (content.js) + `casas/CASA_THUNDERPICK.md`.
(function () {
  // ── CRU para o servidor (s409, Projeto Ficha Sharpen) ───────────────────────────────
  // O objeto da CASA de onde cada bilhete saiu, num campo NOVO (`cru`) da mesma mensagem. A
  // lista de sempre segue intacta, e é ela que vira o texto. Erro aqui nunca sobe. O wager não
  // tem campo de identidade do cliente (o `uuid` é do BILHETE). Desde a s457 o cru leva os
  // campos de evento ENCAIXADOS (ver cabeçalho), na mesma forma da rota antiga.
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

  const RX_API = /^\/api\//i;                                        // onde o token se aprende (caminho)
  // As listas: a rota nova das liquidadas, a antiga (fallback) e as abertas.
  const RX_LISTA = /^\/api\/(wagers\/v2\/(resolved|pending)|users\/wagers\/settled)$/i;
  const RX_EVENTOS = /^\/api\/wagers\/events$/i;                     // o jogo de cada eventId
  // Liquidadas: a nova primeiro; a antiga só se a nova der 404 (conta/região que ainda a use).
  const ROTAS_LIQ = ["/api/users/wagers/settled", "/api/wagers/v2/resolved"];
  const TAKE = 100;                            // aceito (medido até 1000); 100 é o passo seguro
  const TETO_PAGINAS = 300;                    // 300 × 100 = 30 mil bilhetes
  const LOTE_EVENTOS = 100;                    // ids por chamada de eventos (124 medidos numa só)
  const MOEDA = "EUR";                         // a conta é em euro, sempre (ver cabeçalho)

  const byId = new Map();                      // id(string) → bilhete normalizado
  const cruById = new Map();                   // id(string) → objeto da casa (para reencaixar)
  const eventos = new Map();                   // eventId(string) → evento de `/api/wagers/events`
  let respostas = 0;                           // respostas VÁLIDAS da lista (autodiagnóstico)
  let token = "";                              // `thunderpick-token` visto numa chamada real (nunca sai daqui)
  let pedido = false;                          // o robô já pediu → pode arrancar o replay
  let loopAtivo = false;                       // trava: um replay por vez
  let fimReplay = false;                       // a varredura terminou
  let repetir = false;                         // pedido chegou durante a varredura → roda de novo
  let erro = "";                               // último erro do replay (vai no autodiagnóstico)
  const LOG = (...a) => { try { console.log("[SharpenUp thp_inject]", ...a); } catch (e) {} };
  LOG("hook instalado em", location.href);

  const of = window.fetch;                     // fetch ORIGINAL — o replay usa este

  // ── normalização ─────────────────────────────────────────────────────────────
  const _n = (v) => {
    if (v == null || v === "") return null;
    const x = Number(v);
    return isFinite(x) ? x : null;
  };
  const _s = (v) => (v == null ? "" : String(v));
  const _cent = (v) => { const x = _n(v); return x == null ? null : x / 100; };
  // ISO da casa com 6 ou 7 casas de fração ("…00:59:09.0069724+00:00"): corta em 3 antes de
  // ler, para não depender de quanto o `Date.parse` tolera. Devolve unix em SEGUNDOS.
  const _iso = (v) => {
    const t = Date.parse(_s(v).replace(/(\.\d{3})\d+/, "$1"));
    return isFinite(t) ? t / 1000 : null;
  };
  const _caminho = (u) => { try { return new URL(_s(u), location.href).pathname; } catch (e) { return ""; } };

  // `freeBet` nunca veio preenchido (null em todos os 42). Lê número ou `{amount}` em
  // centavos, e o cru sobe junto: se a forma for outra, o formatador manda conferir.
  function _freebet(fb) {
    if (fb == null) return { valor: null, cru: "" };
    let v = null;
    if (typeof fb === "number") v = fb / 100;
    else if (typeof fb === "object" && _n(fb.amount) != null) v = _n(fb.amount) / 100;
    let cru = "";
    try { cru = JSON.stringify(fb); } catch (e) { cru = _s(fb); }
    return { valor: v, cru: cru };
  }

  // ── encaixe do evento (s457) ─────────────────────────────────────────────────
  // Os objetos que levam o jogo: o próprio bilhete na simples, cada perna na múltipla. O topo
  // da múltipla tem `eventId` null e nunca levou jogo.
  function _alvos(w) {
    if (!w) return [];
    if (w.wagerType === "Combo") return Array.isArray(w.subWagers) ? w.subWagers.filter(Boolean) : [];
    return [w];
  }
  const _semJogo = (o) => !_s(o.eventName) && o.eventId != null;

  // Preenche SÓ o que falta, com o evento da casa. true = mexeu em algo.
  function _encaixar(w) {
    let mexeu = false;
    for (const o of _alvos(w)) {
      if (!_semJogo(o)) continue;
      const ev = eventos.get(_s(o.eventId));
      if (!ev) continue;
      if (ev.name) { o.eventName = ev.name; mexeu = true; }
      if (o.eventStartTime == null && ev.startTime) o.eventStartTime = ev.startTime;
      if (o.competition == null && ev.competition) o.competition = ev.competition;
      if (o.homeCompetitor == null && ev.homeCompetitor) o.homeCompetitor = ev.homeCompetitor;
      if (o.awayCompetitor == null && ev.awayCompetitor) o.awayCompetitor = ev.awayCompetitor;
    }
    return mexeu;
  }

  // eventIds que ainda estão sem jogo e cujo evento não chegou.
  function _faltando() {
    const ids = new Set();
    for (const w of cruById.values()) {
      for (const o of _alvos(w)) if (_semJogo(o) && !eventos.has(_s(o.eventId))) ids.add(_s(o.eventId));
    }
    return Array.from(ids);
  }

  function parsePerna(p, estado) {
    if (!p) return null;
    return {
      estado: _s(estado),                       // won · lost · open (CRU; perna sem estado = "")
      odd: _n(p.odds),
      jogo: _s(p.eventName),                    // "Vitality vs Wildcard" (verbatim)
      liga: _s(p.competition && p.competition.name),
      mercado: _s(p.marketName),
      selecao: _s(p.selectionName),
      linha: _s(p.selectionTotal),              // "-5.5", "14.5" — a linha DA SELEÇÃO
      esporteId: _n(p.gameId),                  // 6 CS2 · 10 futebol · 11 basquete · 14 hóquei · 15 tênis
      inicio: _iso(p.eventStartTime),
      vencedora: Array.isArray(p.winningSelectionName) ? p.winningSelectionName.join(" / ") : _s(p.winningSelectionName),
      cancelamento: _s(p.cancelReason),
    };
  }

  function parseWager(w) {
    if (!w || w.wagerId == null) return null;
    const combo = w.wagerType === "Combo";
    const fb = _freebet(w.freeBet);
    const pernas = combo
      ? (Array.isArray(w.subWagers) ? w.subWagers : []).map((p) => parsePerna(p, p && p.subWagerUIState))
      : [parsePerna(w, w.wagerUIState)];
    // Data do evento da múltipla: a rota antiga trazia no topo a da perna mais tardia; a nova
    // não traz no topo, e o formatador já usa a perna mais tardia primeiro.
    return {
      id: (combo ? "C" : "S") + _s(w.wagerId),  // prefixo de tipo: as duas séries de id colidem
      wagerId: _s(w.wagerId),
      tipoApi: _s(w.wagerType),                 // PreMatch · InPlays · Combo (CRU)
      estado: _s(w.wagerUIState),               // open · won · lost · cashed-out (CRU)
      estadoApi: _s(w.state),                   // resolved · canceled nas liquidadas; ausente nas abertas
      moeda: MOEDA,
      stake: _cent(w.amount),
      odd: _n(w.odds),                          // a odd do card (8,41), já o produto das pernas
      retorno: _cent(w.outcome),                // null nas abertas
      retornoTeorico: _cent(w.theoreticalOutcome),
      cancelamento: _s(w.cancelReason),
      cashoutOdd: _n(w.cashOutOdds),            // preenchido no cashout (medido 17/11: 1,97)
      freebet: fb.valor,                        // ⚠ NÃO MEDIDO (sempre null)
      freebetCru: fb.cru,
      colocada: _iso(w.createTime),             // unix em SEGUNDOS — o dia da cotação
      inicio: _iso(w.eventStartTime),           // na múltipla da rota antiga, a perna mais tardia
      liquidada: _iso(w.finishTime),
      pernas: pernas.filter(Boolean),
    };
  }

  // Emite SEMPRE hook:true + respostas (heartbeat), mesmo com 0 bilhetes. NUNCA leva o token.
  function enviar() {
    try {
      window.postMessage({
        __sharpenupTHPData: true, hook: true,
        bilhetes: Array.from(byId.values()), respostas: respostas, fim: fimReplay,
        cru: _crus(Array.from(byId.values())),
        semToken: !_token(), erro: erro,
      }, "*");
    } catch (e) {}
  }

  // A versão LIQUIDADA vence a ABERTA.
  function guardar(b, raw) {
    const ex = byId.get(b.id);
    if (!ex || ex.estado === "open" || b.estado !== "open") {
      byId.set(b.id, b);
      cruById.set(b.id, raw);
    }
  }

  // Lê uma resposta de lista. Devolve `{n, total}`, `{erro}` ou null.
  function consumir(text) {
    if (typeof text !== "string") return null;
    let j;
    try { j = JSON.parse(text); } catch (e) { return null; }
    const d = j && j.data;
    if (!d || !Array.isArray(d.wagers)) {
      if (j && (j.errorCode != null || j.message)) return { erro: "errorCode " + _s(j.errorCode) + (j.message ? " · " + _s(j.message) : "") };
      return null;
    }
    respostas++;
    for (const raw of d.wagers) {
      if (!raw) continue;
      _encaixar(raw);
      const b = parseWager(raw);
      if (!b) continue;
      try { _cruDe.set(b, raw); } catch (e) {}
      guardar(b, raw);
    }
    LOG("bilhetes na resposta:", d.wagers.length, "· total:", byId.size, "· totalWagersCount:", d.totalWagersCount);
    enviar();
    return { n: d.wagers.length, total: _n(d.totalWagersCount) };
  }

  // Lê uma resposta de `/api/wagers/events` e reencaixa quem estava sem jogo. Devolve quantos
  // eventos vieram, ou null se o formato não for o medido.
  function consumirEventos(text) {
    if (typeof text !== "string") return null;
    let j;
    try { j = JSON.parse(text); } catch (e) { return null; }
    const lista = j && j.data;
    if (!Array.isArray(lista)) return null;
    let n = 0;
    for (const ev of lista) {
      if (!ev || ev.id == null) continue;
      eventos.set(_s(ev.id), ev);
      n++;
    }
    let refeitos = 0;
    for (const [id, raw] of cruById) {
      if (!_encaixar(raw)) continue;
      const b = parseWager(raw);
      if (!b) continue;
      try { _cruDe.set(b, raw); } catch (e) {}
      byId.set(id, b);
      refeitos++;
    }
    LOG("eventos na resposta:", n, "· bilhetes reencaixados:", refeitos);
    if (refeitos) enviar();
    return n;
  }

  // ── aprendizado ────────────────────────────────────────────────────────────────
  function aprender(url, headers) {
    if (!RX_API.test(_caminho(url))) return;
    for (const k of Object.keys(headers || {})) {
      if (k.toLowerCase() !== "thunderpick-token") continue;
      const v = _s(headers[k]).trim();
      if (v) {
        if (!token) LOG("token aprendido de", _caminho(url));
        token = v;
      }
    }
    if (_token() && pedido) arrancarReplay();
  }

  // Partida a frio: o token da sessão fica em `localStorage["thp.sessionData"].sessionId`
  // (medido). A chamada real manda, porque a sessão renova.
  function _token() {
    if (token) return token;
    try {
      const ls = window.localStorage;
      const s = ls && JSON.parse(ls.getItem("thp.sessionData") || "null");
      return s && typeof s.sessionId === "string" ? s.sessionId.trim() : "";
    } catch (e) { return ""; }
  }

  // ── replay ─────────────────────────────────────────────────────────────────────
  async function pedir(caminho) {
    // `same-origin`, como a página: a API é do mesmo domínio e a auth é o header.
    const r = await of.call(window, location.origin + caminho, {
      method: "GET", credentials: "same-origin",
      headers: { accept: "application/json, text/plain, */*", "thunderpick-token": _token() },
    });
    return { ok: !!(r && r.ok), status: r && r.status, text: r ? await r.text() : "" };
  }

  const _rota = (caminho) => _s(caminho).split("?")[0];

  // Uma página de lista. `{n,total}` = leu; `{status}` = HTTP não-ok (quem chama decide);
  // null = falhou (o erro já está em `erro`).
  async function lerLista(caminho) {
    let r;
    try { r = await pedir(caminho); }
    catch (e) { erro = "replay falhou em " + _rota(caminho) + ": " + (e && e.message); LOG(erro); return null; }
    if (!r.ok) return { status: r.status };
    const res = consumir(r.text);
    if (!res) { erro = "resposta da lista em formato desconhecido em " + _rota(caminho); LOG(erro); return null; }
    if (res.erro) { erro = "a casa respondeu erro em " + _rota(caminho) + ": " + res.erro; LOG(erro); return null; }
    return res;
  }

  const _parouHttp = (caminho, status) => { erro = "replay parou · HTTP " + status + " em " + _rota(caminho); LOG(erro); };

  // Liquidadas por UMA rota. true = fim; false = falhou; "404" = a rota não existe nesta casa.
  async function varrerLiquidadas(rota) {
    // O total vem da 1ª página e só dela; o avanço é pelo tamanho que VOLTOU.
    let skip = 0, total = null;
    for (let pagina = 0; pagina < TETO_PAGINAS; pagina++) {
      const caminho = rota + "?take=" + TAKE + "&skip=" + skip + "&sortColumn=finishTime";
      const res = await lerLista(caminho);
      if (!res) return false;
      if (res.status != null) {
        if (pagina === 0 && res.status === 404) return "404";
        _parouHttp(caminho, res.status);
        return false;
      }
      if (total == null) total = res.total;
      if (res.n <= 0) break;                                       // lista vazia: acabou
      skip += res.n;
      if (total != null && skip >= total) break;                   // fim AUTORITATIVO
      if (pagina === TETO_PAGINAS - 1) LOG("teto de páginas atingido");
    }
    return true;
  }

  // Busca o jogo dos eventIds que faltam, em lotes. Falha aqui não derruba a captura: o
  // bilhete sobe sem o jogo e o erro vai para o autodiagnóstico.
  async function buscarEventos() {
    const ids = _faltando();
    for (let i = 0; i < ids.length; i += LOTE_EVENTOS) {
      const caminho = "/api/wagers/events?" + ids.slice(i, i + LOTE_EVENTOS).map((x) => "eventIds=" + encodeURIComponent(x)).join("&");
      let r;
      try { r = await pedir(caminho); }
      catch (e) { erro = "jogos não chegaram: " + (e && e.message); LOG(erro); return; }
      if (!r.ok) { erro = "jogos não chegaram · HTTP " + r.status + " em /api/wagers/events"; LOG(erro); return; }
      if (consumirEventos(r.text) == null) { erro = "jogos em formato desconhecido em /api/wagers/events"; LOG(erro); return; }
    }
    const resto = _faltando().length;
    if (resto) LOG("eventos sem resposta da casa:", resto);
  }

  async function varrer() {
    let ok = false;
    for (const rota of ROTAS_LIQ) {
      const r = await varrerLiquidadas(rota);
      if (r === "404") { LOG("rota de liquidadas 404, tentando a seguinte:", rota); continue; }
      ok = r;
      break;
    }
    if (ok === false && !erro) _parouHttp(ROTAS_LIQ[ROTAS_LIQ.length - 1], 404);
    if (!ok) return false;
    // Abertas: uma chamada só.
    const ab = await lerLista("/api/wagers/v2/pending");
    if (!ab) return false;
    if (ab.status != null) { _parouHttp("/api/wagers/v2/pending", ab.status); return false; }
    await buscarEventos();
    return true;
  }

  async function arrancarReplay() {
    if (loopAtivo || fimReplay || !_token()) return;
    loopAtivo = true;
    erro = "";
    try {
      await varrer();
    } finally {
      loopAtivo = false;
      fimReplay = true;
      enviar();
      if (repetir) { repetir = false; fimReplay = false; byId.clear(); cruById.clear(); arrancarReplay(); }
    }
  }

  // O content pede o acumulado ao iniciar o robô → zera, re-envia e arranca o replay. Zerar é
  // a lição da s393 (DEX Sport): sem isso a 2ª rodada na mesma aba devolvia o mapa velho, e
  // aposta já liquidada subia como "em aberto". O mapa de EVENTOS não zera: jogo não muda.
  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (!d || !d.__sharpenupTHPReq) return;
    pedido = true;
    if (loopAtivo) repetir = true;
    else { fimReplay = false; if (_token()) { byId.clear(); cruById.clear(); } }
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
  if (of && !of.__suTHPW) {
    const w = function (...a) {
      const req = (a[0] && typeof a[0] === "object" && a[0].url) ? a[0] : null;
      const url = req ? req.url : a[0];
      const opts = a[1] || {};
      try { aprender(url, _hdrsToObj(opts.headers || (req && req.headers))); } catch (e) {}
      return of.apply(this, a).then((r) => {
        try {
          const cam = _caminho(url);
          // 2º argumento SEMPRE: sem ele um clone abortado vira rejeição muda (s305).
          if (RX_LISTA.test(cam)) r.clone().text().then((t) => consumir(t), () => {});
          else if (RX_EVENTOS.test(cam)) r.clone().text().then((t) => consumirEventos(t), () => {});
        } catch (e) {}
        return r;
      });
    };
    w.__suTHPW = true;
    window.fetch = w;
  }

  // ── XMLHttpRequest ── (rede de segurança, caso a casa troque de transporte)
  const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send,
        osh = XMLHttpRequest.prototype.setRequestHeader;
  if (!os.__suTHPW) {
    XMLHttpRequest.prototype.open = function (m, u) { this.__suTHPU = u; this.__suTHPH = {}; return oo.apply(this, arguments); };
    XMLHttpRequest.prototype.setRequestHeader = function (k, v) { try { this.__suTHPH[k] = v; } catch (e) {} return osh.apply(this, arguments); };
    const s = function (body) {
      try {
        aprender(this.__suTHPU, this.__suTHPH);
        const cam = _caminho(this.__suTHPU);
        const lista = RX_LISTA.test(cam), evs = RX_EVENTOS.test(cam);
        if (lista || evs) {
          this.addEventListener("load", () => {
            try {
              const t = (this.responseType === "" || this.responseType === "text")
                ? this.responseText : JSON.stringify(this.response);
              if (lista) consumir(t); else consumirEventos(t);
            } catch (e) {}
          });
        }
      } catch (e) {}
      return os.apply(this, arguments);
    };
    s.__suTHPW = true;
    XMLHttpRequest.prototype.send = s;
  }

  // Partida a frio: com o token no `localStorage`, o heartbeat já sai dizendo que há sessão.
  enviar();
})();
