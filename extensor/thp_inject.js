// Mundo MAIN (Thunderpick — plataforma própria): lê as apostas que a página pede e BUSCA a
// lista inteira ele mesmo, repassando ao content script.
//
//   GET /api/wagers/v2/resolved?take=&skip=&sortColumn=finishTime   (liquidadas, paginadas)
//   GET /api/wagers/v2/pending                                        (abertas, tudo de uma vez)
//   → { statusCode:200, ok:true, data: { wagers:[…], totalWagersCount } }
//
// PLATAFORMA PRÓPRIA (recon 22/10/2026, conta do Feca, EUR). Front React Router v7, API
// `/api/*` no MESMO domínio, atrás da Cloudflare; os feeds são Oddin.gg e DATA.BET. Não é
// Altenar, BetBy, Kambi, BetConstruct nem softlabs.
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
//   • A página pede `take=20`; `take=100/500/1000` foram aceitos (teto real NÃO medido: a conta
//     tinha 29 liquidadas). Fim AUTORITATIVO = `totalWagersCount` da 1ª PÁGINA: `skip` além do
//     fim devolve `{wagers:[], totalWagersCount:0}`, então o total de uma página tardia mente.
//   • `/pending` não pagina e não tem parâmetro.
//
// NÃO DECIDE NADA: normaliza o bilhete e sobe o cru. `wagerUIState` sobe como veio; quem traduz
// é o `formatTicketTHP` (content.js) + `casas/CASA_THUNDERPICK.md`.
(function () {
  // ── CRU para o servidor (s409, Projeto Ficha Sharpen) ───────────────────────────────
  // O objeto da CASA de onde cada bilhete saiu, num campo NOVO (`cru`) da mesma mensagem. A
  // lista de sempre segue intacta, e é ela que vira o texto. Erro aqui nunca sobe. O wager não
  // tem campo de identidade do cliente (o `uuid` é do BILHETE).
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
  const RX_LISTA = /^\/api\/wagers\/v2\/(resolved|pending)$/i;       // as duas listas
  const TAKE = 100;                            // aceito (medido até 1000); 100 é o passo seguro
  const TETO_PAGINAS = 300;                    // 300 × 100 = 30 mil bilhetes
  const MOEDA = "EUR";                         // a conta é em euro, sempre (ver cabeçalho)

  const byId = new Map();                      // id(string) → bilhete normalizado
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
    return {
      id: (combo ? "C" : "S") + _s(w.wagerId),  // prefixo de tipo: as duas séries de id colidem
      wagerId: _s(w.wagerId),
      tipoApi: _s(w.wagerType),                 // PreMatch · InPlays · Combo (CRU)
      estado: _s(w.wagerUIState),               // open · won · lost (CRU)
      estadoApi: _s(w.state),                   // "resolved" nas liquidadas; ausente nas abertas
      moeda: MOEDA,
      stake: _cent(w.amount),
      odd: _n(w.odds),                          // a odd do card (8,41), já o produto das pernas
      retorno: _cent(w.outcome),                // null nas abertas
      retornoTeorico: _cent(w.theoreticalOutcome),
      cancelamento: _s(w.cancelReason),
      cashoutOdd: _n(w.cashOutOdds),            // ⚠ NÃO MEDIDO (sempre null)
      freebet: fb.valor,                        // ⚠ NÃO MEDIDO (sempre null)
      freebetCru: fb.cru,
      colocada: _iso(w.createTime),             // unix em SEGUNDOS — o dia da cotação
      inicio: _iso(w.eventStartTime),           // na múltipla, a perna mais tardia (medido)
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
  function guardar(b) {
    const ex = byId.get(b.id);
    if (!ex || ex.estado === "open" || b.estado !== "open") byId.set(b.id, b);
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
      const b = parseWager(raw);
      if (!b) continue;
      try { _cruDe.set(b, raw); } catch (e) {}
      guardar(b);
    }
    LOG("bilhetes na resposta:", d.wagers.length, "· total:", byId.size, "· totalWagersCount:", d.totalWagersCount);
    enviar();
    return { n: d.wagers.length, total: _n(d.totalWagersCount) };
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

  // Uma lista inteira. true = chegou ao fim autoritativo.
  async function lerLista(caminho) {
    let r;
    try { r = await pedir(caminho); }
    catch (e) { erro = "replay falhou: " + (e && e.message); LOG(erro); return null; }
    if (!r.ok) { erro = "replay parou · HTTP " + r.status; LOG(erro); return null; }
    const res = consumir(r.text);
    if (!res) { erro = "resposta da lista em formato desconhecido"; LOG(erro); return null; }
    if (res.erro) { erro = "a casa respondeu erro: " + res.erro; LOG(erro); return null; }
    return res;
  }

  async function varrer() {
    // Liquidadas: o total vem da 1ª página e só dela; o avanço é pelo tamanho que VOLTOU.
    let skip = 0, total = null;
    for (let pagina = 0; pagina < TETO_PAGINAS; pagina++) {
      const res = await lerLista("/api/wagers/v2/resolved?take=" + TAKE + "&skip=" + skip + "&sortColumn=finishTime");
      if (!res) return false;
      if (total == null) total = res.total;
      if (res.n <= 0) break;                                       // lista vazia: acabou
      skip += res.n;
      if (total != null && skip >= total) break;                   // fim AUTORITATIVO
      if (pagina === TETO_PAGINAS - 1) LOG("teto de páginas atingido");
    }
    // Abertas: uma chamada só.
    return !!(await lerLista("/api/wagers/v2/pending"));
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
      if (repetir) { repetir = false; fimReplay = false; byId.clear(); arrancarReplay(); }
    }
  }

  // O content pede o acumulado ao iniciar o robô → zera, re-envia e arranca o replay. Zerar é
  // a lição da s393 (DEX Sport): sem isso a 2ª rodada na mesma aba devolvia o mapa velho, e
  // aposta já liquidada subia como "em aberto".
  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (!d || !d.__sharpenupTHPReq) return;
    pedido = true;
    if (loopAtivo) repetir = true;
    else { fimReplay = false; if (_token()) byId.clear(); }
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
          if (RX_LISTA.test(_caminho(url))) {
            // 2º argumento SEMPRE: sem ele um clone abortado vira rejeição muda (s305).
            r.clone().text().then((t) => consumir(t), () => {});
          }
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
        if (RX_LISTA.test(_caminho(this.__suTHPU))) {
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
    s.__suTHPW = true;
    XMLHttpRequest.prototype.send = s;
  }

  // Partida a frio: com o token no `localStorage`, o heartbeat já sai dizendo que há sessão.
  enviar();
})();
