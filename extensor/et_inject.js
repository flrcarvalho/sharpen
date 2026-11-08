// Mundo MAIN (3et — plataforma própria, só o SPORTSBOOK): escuta as listas de apostas que a
// página pede e BUSCA a conta inteira ela mesma, repassando ao content script.
//
//   GET /betting/v3/eurasian/statement/reports/betsByDate?page=N&size=200&after=0&before=<s>
//                                                          (liquidadas, paginadas)
//   GET /betting/v3/eurasian/reports/bets/current/normal?filter=&page=N&size=200
//                                                          (abertas, paginadas)
//   → página Spring: { content:[…], number, size, totalElements, totalPages, last, … }
//
// PLATAFORMA PRÓPRIA (recon 07-08/11/2026, s441, conta do Feca em USD). Front React, API no
// MESMO domínio. Nenhuma outra casa do sistema fala `/eurasian/`. A EXCHANGE da casa
// (`isExchange`, `/statement/reports/exchange…`) fica FORA: decisão do Feca, 2º momento.
//
// AUTH é só o COOKIE da sessão (medido: `fetch` com `credentials:"include"` e nenhum header
// extra devolve 200). Não há token: o replay arranca a frio, com ou sem a página ter pedido.
//
// O QUE FOI MEDIDO na API:
//   • a tela de extrato pede um DIA por clique (`betsByDate?after=<dia>&before=<dia>`); `after=0`
//     devolve a conta inteira. A janela é pela COLOCAÇÃO.
//   • `size` acima de 200 volta 200. O fim é `last:true` (medido com size 5 e 2: páginas exatas,
//     sem repetir bilhete). A página é por ÍNDICE, então o avanço é `page+1`, e quem decide o
//     tamanho de cada página é o servidor (o `size` que voltou).
//   • a liquidada vem PLANA (`{betId, status:{result}, …}`); a aberta vem EMBRULHADA
//     (`{bet:{betId, status:"Open", …}, betType, translatedBetType}`).
//   • ⚠ `payout`/`profit` são o LUCRO, não o retorno (22 × 6,814 = 149,908; `profit` 127,908).
//   • o bilhete não diz a moeda; ela vem de `/accounts/v3/loggedIn` → `currencyCode`. Essa
//     resposta tem nome, e-mail e endereço: SÓ a moeda sai daqui.
//
// NÃO DECIDE NADA: normaliza o bilhete e sobe o cru. `status.result` sobe como veio; quem traduz
// é o `formatTicketET` (content.js) + `casas/CASA_3ET.md`.
(function () {
  // ── CRU para o servidor (Projeto Ficha Sharpen) ──────────────────────────────────────
  // O item da lista como a casa devolveu (aberta embrulhada, liquidada plana), num campo NOVO
  // (`cru`) da mesma mensagem, mais `moeda_conta`: o bilhete não traz a moeda, e sem ela a
  // Ficha não saberia em que moeda a casa falou (mesma ideia do `dicionario` da Vave).
  const _cruDe = new WeakMap();
  function _crus(lista) {
    const out = [];
    try {
      for (const b of lista || []) {
        const c = _cruDe.get(b);
        if (!c || !b.id) continue;
        out.push({ codigo: String(b.id), cru: moeda ? Object.assign({}, c, { moeda_conta: moeda }) : c });
      }
    } catch (e) {}
    return out;
  }

  const P_LIQ = "/betting/v3/eurasian/statement/reports/betsByDate";
  const P_ABERTAS = "/betting/v3/eurasian/reports/bets/current/normal";
  const P_CONTA = "/accounts/v3/loggedIn";
  const RX_LISTA = /^\/betting\/v\d+\/eurasian\/(statement\/reports\/betsByDate|reports\/bets\/current\/normal)$/i;
  const SIZE = 200;                            // teto medido do servidor
  const TETO_PAGINAS = 200;                    // 200 × 200 = 40 mil bilhetes por lista

  const byId = new Map();                      // id(string) → bilhete normalizado
  let respostas = 0;                           // respostas VÁLIDAS de lista (autodiagnóstico)
  let moeda = "";                              // `currencyCode` da conta (nunca outro campo dela)
  let loopAtivo = false;                       // trava: um replay por vez
  let fimReplay = false;                       // a varredura terminou
  let repetir = false;                         // pedido chegou durante a varredura → roda de novo
  let erro = "";                               // último erro do replay (vai no autodiagnóstico)
  const LOG = (...a) => { try { console.log("[SharpenUp et_inject]", ...a); } catch (e) {} };
  LOG("hook instalado em", location.href);

  const of = window.fetch;                     // fetch ORIGINAL — o replay usa este

  // ── normalização ─────────────────────────────────────────────────────────────
  const _n = (v) => {
    if (v == null || v === "") return null;
    const x = Number(v);
    return isFinite(x) ? x : null;
  };
  const _s = (v) => (v == null ? "" : String(v));
  const _iso = (v) => { const t = Date.parse(_s(v)); return isFinite(t) ? t / 1000 : null; };   // unix em SEGUNDOS
  const _caminho = (u) => { try { return new URL(_s(u), location.href).pathname; } catch (e) { return ""; } };

  function parsePerna(p, aberta) {
    if (!p) return null;
    const st = p.status;
    return {
      // Liquidada: `status.result` (Win · Lose). Aberta: texto do andamento (`finished`,
      // `graded`), que NÃO diz ganha nem perdida. Os dois sobem crus, separados.
      resultado: !aberta && st && typeof st === "object" ? _s(st.result) : "",
      andamento: typeof st === "string" ? st : "",
      placar: st && typeof st === "object" ? _s(st.finalScore) : "",
      odd: _n(p.odds),
      jogo: _s(p.eventName),                    // "A vs B" ou "A at B" (verbatim)
      liga: _s(p.competition),
      esporte: _s(p.sportName),                 // em inglês, como a casa escreve
      mercado: _s(p.marketName),
      selecao: _s(p.runnerName),
      periodo: _s(p.periodName),
    };
  }

  function parseBet(raw) {
    const aberta = !!(raw && raw.bet && typeof raw.bet === "object");
    const x = aberta ? raw.bet : raw;
    if (!x || x.betId == null) return null;
    const bt = aberta ? (raw.betType || x.submittedType) : (x.betType && x.betType.betType);
    return {
      id: _s(x.betId),
      aberta: aberta || _s(x.status) === "Open",
      estado: aberta ? _s(x.status) : _s(x.status && x.status.result),   // Open · Win · Lose (CRU)
      estadoPagamento: _s(x.betStatus),         // "paid" nas liquidadas
      tipoApi: _s(bt),                          // MULTIPLIER · Multiplier (CRU)
      multiplicador: _s(x.multiplierName),      // "Double" (CRU)
      moeda: moeda,
      stake: _n(x.stake),
      stakeReal: _n(x.trueStake),
      freebet: _n(x.freeBetStake),
      odd: _n(x.odds),
      lucro: aberta ? null : _n(x.profit),      // LUCRO (não retorno); null nas abertas
      lucroPotencial: _n(x.potentialProfit),
      colocada: _iso(x.datePlaced),
      liquidada: _iso(x.dateSettled),
      exchange: x.isExchange === true,
      pernas: (Array.isArray(x.legs) ? x.legs : []).map((p) => parsePerna(p, aberta)).filter(Boolean),
    };
  }

  // Emite SEMPRE hook:true + respostas (heartbeat), mesmo com 0 bilhetes.
  function enviar() {
    try {
      const lista = Array.from(byId.values());
      window.postMessage({
        __sharpenupETData: true, hook: true,
        bilhetes: lista, respostas: respostas, fim: fimReplay,
        cru: _crus(lista), erro: erro,
      }, "*");
    } catch (e) {}
  }

  // A versão LIQUIDADA vence a ABERTA, em qualquer ordem de chegada.
  function guardar(b) {
    const ex = byId.get(b.id);
    if (!ex || ex.aberta || !b.aberta) byId.set(b.id, b);
  }

  // Lê uma página de lista. Devolve `{n, last}` ou null (formato desconhecido).
  function consumir(text) {
    if (typeof text !== "string") return null;
    let j;
    try { j = JSON.parse(text); } catch (e) { return null; }
    if (!j || !Array.isArray(j.content)) return null;
    respostas++;
    for (const raw of j.content) {
      const b = parseBet(raw);
      if (!b) continue;
      try { _cruDe.set(b, raw); } catch (e) {}
      guardar(b);
    }
    LOG("bilhetes na resposta:", j.content.length, "· total:", byId.size, "· last:", j.last);
    enviar();
    return { n: j.content.length, last: j.last === true, paginas: _n(j.totalPages), numero: _n(j.number) };
  }

  // ── replay ─────────────────────────────────────────────────────────────────────
  async function pedir(caminho) {
    const r = await of.call(window, location.origin + caminho, {
      method: "GET", credentials: "include",
      headers: { accept: "application/json, text/plain, */*" },
    });
    return { ok: !!(r && r.ok), status: r && r.status, text: r ? await r.text() : "" };
  }

  // Só `currencyCode`. Falhar aqui não para a captura: sem moeda o bloco não inventa uma, e a
  // do cadastro da conta vale (decisão do Feca, D0).
  async function lerMoeda() {
    if (moeda) return;
    try {
      const r = await pedir(P_CONTA);
      if (!r.ok) return;
      const c = JSON.parse(r.text);
      const m = c && typeof c.currencyCode === "string" ? c.currencyCode.trim().toUpperCase() : "";
      if (/^[A-Z]{3,5}$/.test(m)) moeda = m;
    } catch (e) {}
  }

  // Uma lista inteira, página a página até `last:true`. true = chegou ao fim autoritativo.
  async function lerLista(montar) {
    for (let pagina = 0; pagina < TETO_PAGINAS; pagina++) {
      let r;
      try { r = await pedir(montar(pagina)); }
      catch (e) { erro = "replay falhou: " + (e && e.message); LOG(erro); return false; }
      if (!r.ok) { erro = "replay parou · HTTP " + r.status + (r.status === 401 || r.status === 403 ? " (sessão expirada? faça login)" : ""); LOG(erro); return false; }
      const res = consumir(r.text);
      if (!res) { erro = "resposta da lista em formato desconhecido"; LOG(erro); return false; }
      if (res.last || res.n <= 0) return true;                       // fim AUTORITATIVO
      if (res.paginas != null && pagina + 1 >= res.paginas) return true;
    }
    LOG("teto de páginas atingido");
    return true;
  }

  async function varrer() {
    await lerMoeda();
    // `before` com folga de um dia: aposta feita agora entra mesmo com relógio adiantado da casa.
    const ate = Math.floor(Date.now() / 1000) + 86400;
    const ok = await lerLista((p) => P_LIQ + "?page=" + p + "&size=" + SIZE + "&after=0&before=" + ate);
    if (!ok) return false;
    return lerLista((p) => P_ABERTAS + "?filter=&page=" + p + "&size=" + SIZE);
  }

  async function arrancarReplay() {
    if (loopAtivo || fimReplay) return;
    loopAtivo = true;
    erro = "";
    try {
      await varrer();
    } finally {
      loopAtivo = false;
      // Os bilhetes que chegaram antes da moeda ficam com ela também.
      if (moeda) for (const b of byId.values()) if (!b.moeda) b.moeda = moeda;
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
    if (!d || !d.__sharpenupETReq) return;
    if (loopAtivo) repetir = true;
    else { fimReplay = false; byId.clear(); }
    enviar();
    arrancarReplay();
  });

  // ── fetch ── (a página usa axios; o fetch fica de rede de segurança e para o replay)
  if (of && !of.__suETW) {
    const w = function (...a) {
      const req = (a[0] && typeof a[0] === "object" && a[0].url) ? a[0] : null;
      const url = req ? req.url : a[0];
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
    w.__suETW = true;
    window.fetch = w;
  }

  // ── XMLHttpRequest ── (o axios da página sai por aqui)
  const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send;
  if (!os.__suETW) {
    XMLHttpRequest.prototype.open = function (m, u) { this.__suETU = u; return oo.apply(this, arguments); };
    const s = function (body) {
      try {
        if (RX_LISTA.test(_caminho(this.__suETU))) {
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
    s.__suETW = true;
    XMLHttpRequest.prototype.send = s;
  }

  enviar();
})();
