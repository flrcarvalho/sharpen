// Mundo MAIN — Bolsa de Aposta / SPORTSBOOK. Roda DENTRO do iframe do provedor, nunca na
// casca (s299).
//
//   GET <origem>/api/master/my-bets/history?limit=50&offset=0   → o histórico
//   GET <origem>/api/betslip/my-bets/open                       → as em aberto
//
// ⚠ NÃO TEM PARENTESCO COM O EXCHANGE. A mesma casa serve dois produtos de fornecedores
// diferentes: o Exchange é Next.js/LayBack em `mexchange2.bolsadeaposta.bet.br` e fala
// kebab-case; este é outro software, em `prod<N>-<N>.msjxk.com`, e fala PascalCase com
// status numérico. Dois injects, dois formatadores, um `casa` só na planilha.
//
// O HOST É VERSIONADO E CHUMBADO na casca (`"fbookProdUrl":
// "https://prod20454-176166000.msjxk.com/"`). O dia em que a casa trocar o número, um
// `match` literal para de bater e **a captura morre sem erro nenhum** — por isso o curinga
// `*://*.msjxk.com/*` no manifest, e por isso a origem aqui sai de `location`, nunca de
// constante.
//
// O REPLAY É OBRIGATÓRIO por UM motivo, e ele é traiçoeiro:
//
//   A TELA PERGUNTA ERRADO. O painel manda `lastHours=1M` (o preset de 30 dias) e, na conta
//   do recon, isso devolvia **`totalCount: 0`** — os 17 bilhetes eram mais velhos. Um
//   passivo perfeito capturaria ZERO e pareceria estar funcionando. **Omitir `lastHours`
//   traz o histórico inteiro.** E o campo ainda mente no nome: `8760` (as horas de um ano)
//   devolve 0, enquanto `12M` devolve tudo — é um TOKEN, não um número de horas.
//
// ARMADILHAS confirmadas no dado real (o inject NÃO decide — quem lê é o `formatTicketBDS`):
//   • `GainDecimal` é o retorno POTENCIAL, SEMPRE — inclusive em bilhete PERDIDO. O
//     857454677280481281 traz `"720"` e o card dele diz **PERDIDO, Ganho Potencial 0,00**.
//     Quem ler o campo óbvio marca toda perdida como ganha (o `totalWin` da VaideBet).
//     O realizado é `CurrentBetBalanceDecimal`: 0 (perdido) · 409,94 (ganho) · 100 (cancelado,
//     = a stake devolvida).
//   • `BetStatus` é NUMÉRICO e sobe CRU. De-para conferido contra os badges da tela:
//     1 = PERDIDO · 2 = VENCEU · 4 = CANCELADA. Qualquer outro valor sobe do mesmo jeito e
//     o formatador manda conferir à mão — nunca vira resultado por chute.
//   • V NÃO PODE VIRAR ODD 1,00. O cancelado devolve a stake (100 ÷ 100 = 1,0); ali manda o
//     `ClientOdds` estrutural (4,50). É a regra do MASTER_RESULTADO, e o dado dela está aqui.
//   • DINHEIRO E ODD VÊM COMO STRING COM PONTO DECIMAL (`"409.94"`, `"1.80"`). Passar isso
//     por um parser de padrão brasileiro leria 409,94 como 40994.
//   • OS NOMES BONS ESTÃO EM `Translations`. O nível de cima vem em inglês e com rótulo
//     interno: `EventName: "Colombia vs DR Congo"`, `LineTypeName: "Custom QA"`. O card
//     mostra `Translations.EventName` / `.MarketName` / `.SelectionName`, em pt-BR.
//   • `EventDate` em UTC com `Z` → o content converte. Conferido contra o card ao minuto:
//     `2026-07-22T23:30:00.000Z` ⇄ "22/07 • 20:30".
//
// SEM AMOSTRA (a conta do recon não tinha): aposta em aberto, múltipla (`ComboSize > 0`),
// cashout/Retirada (`IsPartialCashOut`) e freebet. Os campos são lidos e sobem crus.
(function () {
  // TRAVA DE HOST — ver a nota gêmea no `bda_inject.js`. O popup injeta os dois arquivos em
  // todos os frames; sem isto o Sportsbook daria `hook:true` de dentro do Exchange.
  try { if (!/(^|\.)msjxk\.com$/i.test(new URL(location.href).host)) return; } catch (e) { return; }

  const RX = /\/api\/(?:master\/my-bets\/history|betslip\/my-bets\/open)/i;
  const byRef = new Map();
  let respostas = 0;
  let reqCtx = null;
  let pedido = false;
  let loopAtivo = false;
  let fimReplay = false;
  let repetir = false;                         // pedido chegou durante a varredura → roda de novo
  let erro = "";
  const LOG = (...a) => { try { console.log("[SharpenUp bds_inject]", ...a); } catch (e) {} };
  LOG("hook instalado em", location.href);

  const of = window.fetch;

  const PAGINA = 50;           // `limit=100` devolve 400 na rota irmã; 50 é o teto seguro medido
  const TETO_PAGINAS = 200;

  function _origem() {
    try { return new URL(location.href).origin; } catch (e) { return ""; }
  }

  // ── normalização ───────────────────────────────────────────────────────────────
  // ⚠ Dinheiro e odd chegam como STRING com PONTO decimal. `Number` é o parser certo aqui;
  // o parser de padrão brasileiro leria "409.94" como 40994.
  const _num = (v) => {
    if (typeof v === "number") return isFinite(v) ? v : null;
    if (typeof v !== "string" || !v.trim()) return null;
    const n = Number(v);
    return isFinite(n) ? n : null;
  };
  const _s = (v) => (v == null ? "" : String(v));

  // Os nomes que o card mostra vivem em `Translations`; o nível de cima é inglês/interno.
  // Preferir a tradução é normalizar, não decidir — e o cru continua disponível ao lado.
  function parseSelecao(s) {
    const T = (s && s.Translations) || {};
    return {
      evento: _s(T.EventName || s.EventName),
      mercado: _s(T.MarketName || s.BetslipMarketName || s.LineTypeName),
      mercadoTipo: _s(T.MarketTypeName || s.EventTypeName),
      selecao: _s(T.SelectionName || s.YourBet),
      esporte: _s(T.SportName || s.SportName),          // "Futebol" (pt) / "Soccer" (cru)
      esporteCru: _s(s.SportName),
      liga: _s(T.LeagueName || s.LeagueName),
      time1: _s(T.Team1Name || s.Team1Name),
      time2: _s(T.Team2Name || s.Team2Name),
      odd: _num(s.ClientOdds),
      linha: (s.Points == null ? null : _num(s.Points)),
      inicio: _s(s.EventDate),                          // UTC com Z
      aoVivo: !!s.IsLive,
      status: (s.SelectionStatus == null ? "" : String(s.SelectionStatus)),  // CRU
      placar: _s(s.SettlementResult || s.FullTimeResult || s.Result),
    };
  }

  function parseTicket(t, out) {
    if (!t || t.TicketId == null) return;
    out.push({
      ref: _s(t.TicketId),                              // o [Código:] e a chave de dedup
      status: (t.BetStatus == null ? "" : String(t.BetStatus)),   // 1/2/4 — CRU
      odd: _num(t.ClientOdds),                          // odd estrutural do bilhete
      stake: _num(t.StakeDecimal != null ? t.StakeDecimal : t.Stake),
      // ⚠ POTENCIAL, sempre — inclusive em perdida. Sobe com nome que não engana.
      potencial: _num(t.GainDecimal != null ? t.GainDecimal : t.Gain),
      // Retorno REALIZADO. É este que responde W/L/V em dinheiro.
      retorno: _num(t.CurrentBetBalanceDecimal != null ? t.CurrentBetBalanceDecimal : t.CurrentBalance),
      tipo: _s(t.Name || t.BetName),                    // "single bet" (CRU)
      combo: (t.ComboSize == null ? null : Number(t.ComboSize)),
      nApostas: (t.NumberOfBets == null ? null : Number(t.NumberOfBets)),
      aoVivo: !!t.IsLive,
      freebet: t.FreeBet || null,
      cashoutParcial: !!t.IsPartialCashOut,
      criado: _s(t.CreationDate),                       // UTC com Z
      atualizado: _s(t.UpdateDate),
      sels: (t.Selections || []).map(parseSelecao),
    });
  }

  function enviar() {
    const msg = {
      __sharpenupBDSData: true, hook: true,
      bilhetes: Array.from(byRef.values()), respostas: respostas, fim: fimReplay, erro: erro,
    };
    try { window.postMessage(msg, "*"); } catch (e) {}
    // ⚠ SEM ESTA LINHA A CAPTURA NÃO EXISTE — ver a nota gêmea no `bda_inject.js`. O iframe
    // aqui é de OUTRA origem (`msjxk.com`), então nem o `content.js` alcança este mundo:
    // o único caminho de volta é o `postMessage` para o topo.
    try { if (window.top && window.top !== window) window.top.postMessage(msg, "*"); } catch (e) {}
  }

  // Resolvida vence aberta: o mesmo bilhete volta na rota `open` e na `history`.
  // `BetStatus` vazio/0 é o estado aberto; qualquer status preenchido é mais final que ele.
  function guardar(b) {
    const ex = byRef.get(b.ref);
    if (!ex) { byRef.set(b.ref, b); return; }
    const vivo = (s) => (!s || s === "0");
    if (vivo(ex.status) && !vivo(b.status)) byRef.set(b.ref, b);
  }

  function forward(url, text) {
    if (!RX.test(String(url)) || typeof text !== "string") return null;
    let j;
    try { j = JSON.parse(text); } catch (e) { return null; }
    if (!j || !Array.isArray(j.data)) return null;      // corpo de erro / formato mudou
    respostas++;
    const novos = [];
    for (const t of j.data) parseTicket(t, novos);
    for (const b of novos) guardar(b);
    LOG("bilhetes na resposta:", j.data.length, "· total:", byRef.size,
        "· totalCount:", j.totalCount);
    enviar();
    return { total: typeof j.totalCount === "number" ? j.totalCount : 0, veio: j.data.length };
  }

  // ── replay ─────────────────────────────────────────────────────────────────────
  function _hdrsToObj(h) {
    const o = {};
    try {
      if (!h) return o;
      if (typeof h.forEach === "function") h.forEach((v, k) => { o[k] = v; });
      else if (typeof h === "object") for (const k in h) o[k] = h[k];
    } catch (e) {}
    return o;
  }

  function capturarReq(url, headers) {
    if (!RX.test(String(url))) return;
    if (!reqCtx) {
      reqCtx = { headers: headers || {} };
      LOG("requisição capturada p/ replay");
    }
    if (pedido) arrancarReplay();
  }

  async function _get(url) {
    let r;
    try {
      r = await of.call(window, url, {
        method: "GET", headers: (reqCtx && reqCtx.headers) || {}, credentials: "include",
      });
    } catch (e) { erro = "replay falhou: " + (e && e.message); LOG(erro); return null; }
    if (!r || !r.ok) { erro = "replay parou · HTTP " + (r && r.status); LOG(erro); return null; }
    try { return forward(r.url || url, await r.text()); } catch (e) { return null; }
  }

  // Histórico completo. `lastHours` fica de FORA de propósito — ver o cabeçalho: com o
  // valor que a tela usa, a conta do recon devolvia zero bilhete.
  async function varrerHistorico() {
    const base = _origem() + "/api/master/my-bets/history";
    let offset = 0;
    for (let i = 0; i < TETO_PAGINAS; i++) {
      const st = await _get(base + "?limit=" + PAGINA + "&offset=" + offset);
      if (!st) return false;
      offset += st.veio;                     // avança pelo que VOLTOU, não pelo `limit` pedido
      if (st.veio <= 0 || offset >= st.total) return true;
    }
    LOG("teto de páginas atingido");
    return true;
  }

  // Em aberto. Rota separada e sem paginação observada (a conta do recon não tinha nenhuma
  // aposta viva, então isto NÃO foi exercitado contra dado real — falha aqui não derruba a
  // varredura do histórico, que é o que já sabemos que funciona).
  async function varrerAbertas() {
    await _get(_origem() + "/api/betslip/my-bets/open");
  }

  async function arrancarReplay() {
    if (loopAtivo) { repetir = true; return; }
    if (fimReplay) return;
    loopAtivo = true;
    try {
      await varrerHistorico();
      await varrerAbertas();
    } finally {
      loopAtivo = false;
      fimReplay = true;
      enviar();
      if (repetir) { repetir = false; fimReplay = false; arrancarReplay(); }
    }
  }

  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (!d || !d.__sharpenupBDSReq) return;
    pedido = true;
    // ⚠ DESTRAVA A SEGUNDA RODADA — ver a nota gêmea no `bda_inject.js`.
    if (!loopAtivo) fimReplay = false;
    enviar();
    arrancarReplay();
  });

  // ── fetch ──
  if (of && !of.__suBDSW) {
    const w = function (...a) {
      const req = (a[0] && typeof a[0] === "object" && a[0].url) ? a[0] : null;
      const url = req ? req.url : a[0];
      const opts = a[1] || {};
      try {
        if (RX.test(String(url))) capturarReq(url, _hdrsToObj(req ? req.headers : opts.headers));
      } catch (e) {}
      return of.apply(this, a).then((r) => {
        try {
          if (RX.test(String(url))) r.clone().text().then((t) => forward(url, t)).catch(() => {});
        } catch (e) {}
        return r;
      });
    };
    w.__suBDSW = true;
    window.fetch = w;
  }

  function _corpoResposta(xhr) {
    try {
      const tipo = xhr.responseType;
      if (tipo === "" || tipo === "text") return xhr.responseText;
      if (tipo === "json") return JSON.stringify(xhr.response);
    } catch (e) {}
    return "";
  }

  // ── XMLHttpRequest ──
  // Medido no recon: o app pede o histórico por XHR. Este é o caminho principal.
  const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send,
        osh = XMLHttpRequest.prototype.setRequestHeader;
  if (!os.__suBDSW) {
    XMLHttpRequest.prototype.open = function (m, u) { this.__suBDSU = u; this.__suBDSH = {}; return oo.apply(this, arguments); };
    XMLHttpRequest.prototype.setRequestHeader = function (k, v) { try { this.__suBDSH[k] = v; } catch (e) {} return osh.apply(this, arguments); };
    const s = function (body) {
      try {
        if (RX.test(String(this.__suBDSU))) {
          capturarReq(this.__suBDSU, this.__suBDSH);
          this.addEventListener("load", () => {
            try { forward(this.__suBDSU, _corpoResposta(this)); } catch (e) {}
          });
        }
      } catch (e) {}
      return os.apply(this, arguments);
    };
    s.__suBDSW = true;
    XMLHttpRequest.prototype.send = s;
  }
})();
