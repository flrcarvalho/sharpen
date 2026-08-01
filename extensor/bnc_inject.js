// Mundo MAIN (só na BetNacional): lê as RESPOSTAS que a própria página recebe da API de
// histórico de apostas e repassa ao content script. Endpoint (BFF próprio da casa):
//
//   GET prod-betnacional-bets.bet6.com.br/api/v2/all-bets
//       ?status=all&paginationDirection=next&limit=N&date_start=YYYY-MM-DD&date_end=YYYY-MM-DD
//       (+ startDate/endDate duplicados — a página manda os dois pares)
//
// A resposta traz `bets[]` como lista de PERNAS, não de bilhetes: uma múltipla de 4 vem
// como 4 objetos com o MESMO `ticket_id` (o "ID da aposta" do card, `NXBNAC…`) e campos
// `header_*` repetidos (stake/retorno/resultado do bilhete). Aqui o inject AGRUPA as
// pernas por ticket_id e sobe 1 objeto por bilhete — normaliza, nunca decide.
//
// REPLAY ATIVO (o "puxa sozinho"): a lista da página cobre só a janela de datas exibida
// (~8 dias). A partir de uma requisição real o inject aprende url+headers (o Bearer
// Keycloak é da própria sessão; `nsx-token-version` vai junto) e RE-EMITE a consulta
// varrendo JANELAS DE DATAS PARA TRÁS — mesma lição do `varrerParaTras` da Tivo/Betfast:
// o fim é "janelas seguidas sem bilhete novo", porque a casa não expôs um `more:false`
// (o cursor `paginationDirection=next` nunca disparou na conta real; ver CASA_BETNACIONAL).
//
// ARMADILHAS CONFIRMADAS no recon (s227), travadas em harness/casos/betnacional.mjs:
//   • `header_return` de bilhete PENDENTE é retorno POTENCIAL (o card mostra "Retorno
//     R$ 135,00" com o jogo por começar) — quem ler como ganho cria vitória fantasma.
//   • `total_odd` vem arredondada em 3 casas (18.795; card 18.80) — no W a odd sai do
//     dinheiro quando a declarada não explica o retorno até o centavo (formatTicketBNC).
//   • dinheiro em STRING com ponto decimal em reais ("150.00") — não é milésimo.
//   • `created_at` já vem em horário LOCAL (sem Z) — não converter de UTC.
(function () {
  const RX = /\/api\/v2\/all-bets/i;           // endpoint da LISTA de apostas
  const byId = new Map();                      // ticket_id → bilhete agrupado
  let respostas = 0;                           // respostas do endpoint que o hook viu (autodiagnóstico)
  let reqCtx = null;                           // {url, headers} de uma requisição real (p/ replay)
  let pedido = false;                          // o robô já pediu → pode arrancar o replay
  let loopAtivo = false;                       // trava: um replay por vez
  let fimReplay = false;                       // varredura de janelas concluída
  const LOG = (...a) => { try { console.log("[SharpenUp bnc_inject]", ...a); } catch (e) {} };
  LOG("hook instalado em", location.href);

  const of = window.fetch;                     // fetch ORIGINAL — o replay usa este (não re-dispara o wrapper)

  // ── normalização (pernas → bilhete agrupado) ──────────────────────────────────
  // Dinheiro vem em string com PONTO decimal, em reais ("150.00" = R$ 150,00).
  const _n = (v) => {
    if (typeof v === "number") return v;
    if (typeof v === "string" && v.trim() !== "") { const x = parseFloat(v); return isFinite(x) ? x : null; }
    return null;
  };
  // Sufixo numérico do id da perna ("1070628814_3" → 3) — ordena as pernas do bilhete.
  const _idx = (leg) => { const m = /_(\d+)$/.exec(String(leg && leg.id || "")); return m ? Number(m[1]) : 0; };

  function agrupar(bets) {
    const porTicket = new Map();
    for (const b of (bets || [])) {
      if (!b || !b.ticket_id) continue;
      let t = porTicket.get(b.ticket_id);
      if (!t) {
        t = {
          codigo: String(b.ticket_id),
          headerId: b.header_id != null ? String(b.header_id) : "",
          statusId: b.bet_status_id,                 // 0 = Pendente · 1 = Finalizado (cru)
          statusNome: b.bet_status_name || "",       // enum CRU — a CASA_BETNACIONAL traduz
          resultado: b.header_result,                // 1 ganhou · 0 perdeu · null pendente (cru)
          stake: _n(b.header_stake),
          retorno: _n(b.header_return),              // ⚠ em PENDENTE é retorno POTENCIAL
          oddTotal: typeof b.total_odd === "number" ? b.total_odd : _n(b.total_odd),
          tipoNome: b.bet_type_name || "",           // "Simples" / "Múltiplas" (cru)
          colocada: b.created_at || "",              // já em horário local (sem Z)
          pagaEm: b.bet_paid_at || "",
          superOdds: false,
          outright: false,
          pernas: [],
        };
        porTicket.set(b.ticket_id, t);
      }
      if (b.is_super_odds) t.superOdds = true;
      if (b.is_outright) t.outright = true;
      t.pernas.push({
        idx: _idx(b),
        mercado: b.market_name || "",
        selecao: b.outcome_name || "",
        specifier: b.specifier || "",
        odd: typeof b.odd === "number" ? b.odd : _n(b.odd),
        resultadoPerna: b.return_type_id,            // 1/0/2/null — sobe CRU (de-para na CASA_*.md)
        casa: b.home || "",
        fora: b.away || "",
        esporte: b.sport_name || "",
        liga: b.tournament_name || "",
        inicio: b.event_date || "",
      });
    }
    for (const t of porTicket.values()) t.pernas.sort((a, b) => a.idx - b.idx);
    return Array.from(porTicket.values());
  }

  // Emite SEMPRE hook:true + respostas (heartbeat), mesmo com 0 bilhetes — o content
  // distingue "hook não carregou" de "endpoint respondeu, lemos 0" (autodiagnóstico).
  function enviar() {
    try {
      window.postMessage({
        __sharpenupBNCData: true, hook: true,
        tickets: Array.from(byId.values()), respostas: respostas, fim: fimReplay,
      }, "*");
    } catch (e) {}
  }

  // Guarda o bilhete. O mesmo ticket pode voltar em janelas/consultas diferentes: a versão
  // RESOLVIDA (statusId !== 0) vence a ABERTA; empatou, vence a que tem mais pernas.
  function guardar(t) {
    const ex = byId.get(t.codigo);
    if (!ex) { byId.set(t.codigo, t); return true; }
    const aberto = (x) => x.statusId === 0;
    if (aberto(ex) && !aberto(t)) { byId.set(t.codigo, t); return false; }
    if ((t.pernas || []).length > (ex.pernas || []).length) { byId.set(t.codigo, t); return false; }
    return false;
  }

  // Processa uma resposta. Devolve o nº de bilhetes NOVOS (p/ o replay saber quando parar)
  // ou null se a resposta não é da lista.
  function forward(url, text) {
    if (!RX.test(String(url)) || typeof text !== "string") return null;
    let j;
    try { j = JSON.parse(text); } catch (e) { return null; }
    const arr = j && Array.isArray(j.bets) ? j.bets : null;
    if (!arr) return null;
    respostas++;
    let novos = 0;
    for (const t of agrupar(arr)) { if (guardar(t)) novos++; }
    LOG("pernas na resposta:", arr.length, "· bilhetes novos:", novos, "· total:", byId.size);
    enviar();
    return novos;
  }

  // ── replay ativo: varre janelas de datas para trás ────────────────────────────
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
      // Só os headers que a página definiu (authorization / nsx-token-version / accept).
      // Nada de cookie: vai no credentials:"include", como nas outras casas passivas.
      reqCtx = { url: String(url), headers: headers || {} };
      LOG("requisição capturada p/ replay");
    } else {
      // Bearer Keycloak expira em ~15 min: mantém sempre os headers MAIS RECENTES vistos.
      reqCtx = { url: String(url), headers: headers || reqCtx.headers };
    }
    if (pedido) arrancarReplay();
  }

  const DIA_MS = 86400000;
  const _ymd = (ms) => {
    const d = new Date(ms);
    const p = (x) => String(x).padStart(2, "0");
    return d.getFullYear() + "-" + p(d.getMonth() + 1) + "-" + p(d.getDate());
  };

  // URL de uma janela [iniMs, fimMs]: preserva a URL aprendida (com o que mais a página
  // mandar) e troca só datas/limite/status. A página manda os DOIS pares de parâmetros de
  // data (date_start/date_end E startDate/endDate) — setamos os dois.
  function comJanela(base, iniMs, fimMs) {
    try {
      const u = new URL(base, location.href);
      u.searchParams.set("status", "all");            // uma consulta cobre Pendente+Finalizado
      u.searchParams.set("limit", "200");             // página pediu 20; pedimos folga
      u.searchParams.set("date_start", _ymd(iniMs));
      u.searchParams.set("date_end", _ymd(fimMs));
      u.searchParams.set("startDate", _ymd(iniMs));
      u.searchParams.set("endDate", _ymd(fimMs));
      return u.href;
    } catch (e) { return base; }
  }

  const JANELA_DIAS = 8;          // a página usa ~8 dias por consulta; espelhamos
  const SEM_NOVIDADE_PARA = 4;    // 4 janelas seguidas sem bilhete novo (~32 dias) = fim
  const TETO_JANELAS = 60;        // rede de segurança (60 × 8 dias ≈ 480 dias)

  async function varrerJanelas() {
    let fimMs = Date.now();
    let semNovidade = 0;
    for (let i = 0; i < TETO_JANELAS; i++) {
      const iniMs = fimMs - (JANELA_DIAS - 1) * DIA_MS;
      let r;
      try {
        r = await of.call(window, comJanela(reqCtx.url, iniMs, fimMs), {
          method: "GET", headers: (reqCtx && reqCtx.headers) || {}, credentials: "include",
        });
      } catch (e) { LOG("erro no replay:", e && e.message); return; }
      if (!r || !r.ok) { LOG("replay parou · HTTP", r && r.status); return; }
      let novos;
      try { novos = forward(r.url || reqCtx.url, await r.text()); } catch (e) { return; }
      if (novos == null) return;                       // formato mudou → não insiste
      semNovidade = novos > 0 ? 0 : semNovidade + 1;
      if (semNovidade >= SEM_NOVIDADE_PARA) return;    // varredura secou → fim
      fimMs = iniMs - DIA_MS;                          // janela anterior
    }
    LOG("teto de janelas atingido");
  }

  async function arrancarReplay() {
    if (loopAtivo || fimReplay || !reqCtx) return;
    loopAtivo = true;
    try {
      await varrerJanelas();
    } finally {
      loopAtivo = false;
      fimReplay = true;
      enviar();                                        // sinaliza fim p/ o robô parar de esperar
    }
  }

  // O content script pede o acumulado ao iniciar o robô → re-envia tudo E arranca o replay.
  // A 1ª página chega no load (antes do content estar ouvindo), por isso re-enviamos sob demanda.
  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (!d || !d.__sharpenupBNCReq) return;
    pedido = true;
    enviar();
    arrancarReplay();
  });

  // ── fetch ──
  if (of && !of.__suBNCW) {
    const w = function (...a) {
      const url = (a[0] && a[0].url) || a[0];
      const opts = a[1] || (a[0] && typeof a[0] === "object" ? a[0] : null);
      try { if (RX.test(String(url))) capturarReq(url, _hdrsToObj(opts && opts.headers)); } catch (e) {}
      return of.apply(this, a).then((r) => {
        try { if (RX.test(String(url))) r.clone().text().then((t) => forward(url, t)); } catch (e) {}
        return r;
      });
    };
    w.__suBNCW = true;
    window.fetch = w;
  }

  // ── XMLHttpRequest (backstop — se a casa trocar fetch por XHR, o hook segue vendo) ──
  const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send, osh = XMLHttpRequest.prototype.setRequestHeader;
  if (!os.__suBNCW) {
    XMLHttpRequest.prototype.open = function (m, u) { this.__suBNCU = u; this.__suBNCH = {}; return oo.apply(this, arguments); };
    XMLHttpRequest.prototype.setRequestHeader = function (k, v) { try { this.__suBNCH[k] = v; } catch (e) {} return osh.apply(this, arguments); };
    const s = function () {
      try {
        if (RX.test(String(this.__suBNCU))) {
          capturarReq(this.__suBNCU, this.__suBNCH);
          this.addEventListener("load", () => { try { forward(this.__suBNCU, this.responseText); } catch (e) {} });
        }
      } catch (e) {}
      return os.apply(this, arguments);
    };
    s.__suBNCW = true;
    XMLHttpRequest.prototype.send = s;
  }
})();
