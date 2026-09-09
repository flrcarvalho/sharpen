// Mundo MAIN — motor **Rogue**, compartilhado por TRÊS casas espelho (s335):
//
//   betao.bet.br · r7.bet.br · 7games.bet.br
//
//   GET <host>/api/sportsbook/rogue/v1/betsreporting/purchases
//       ?status=all&take=<1..100>&skip=<n>&locale=br-pt&fromDate=<ISO>&toDate=<ISO>
//   → {"Purchases":[…], "PurchasesCount": <total da janela>}
//
// ESPELHO MEDIDO, não deduzido: os bundles das três publicam o MESMO mapa de endpoints
// (`getPurchases: "/v1/betting/get-purchases"`, `betsReportingPurchases:
// "/v1/betsreporting/purchases"`, `cashoutGetInfo`, …), a mesma stack Next.js e o mesmo
// conjunto de hosts. A API mora no PRÓPRIO domínio da casa, como na Novibet — não é
// Altenar/BIA, não é BetBy, não é Kambi, não é BetConstruct. Um inject serve às três; o que
// muda é só o host, e ele vem da própria requisição aprendida.
//
// ── POR QUE O REPLAY EXISTE ─────────────────────────────────────────────────────────────
//
// Aqui o PASSIVO FUNCIONA — o `clone().text()` resolve normalmente, ao contrário de Novibet
// (Angular), Pitaco (gRPC) e SportingBet, onde ele morre com AbortError. Mesmo assim ele não
// basta, e por um motivo que já custou uma sessão inteira noutra casa: **a tela é ESTREITA**.
// O histórico abre em "Últ. 24 horas" com `take=10`; no dia do recon, o filtro de 30 dias do
// Betão devolvia `PurchasesCount: 0` numa conta com 9 bilhetes. Um inject passivo puro
// pareceria funcionar (hook ativo, respostas > 0) e entregaria quase nada.
//
// Então a divisão é: o passivo aproveita de graça o que a página já baixou, e o REPLAY é
// quem garante a cobertura — alargando a janela e pedindo `status=all`.
//
// ── AUTENTICAÇÃO: o Bearer é obrigatório e NÃO está em lugar nenhum ─────────────────────
//
// A mesma URL com o cookie da sessão responde **403** (medido no Betão). O header
// `authorization: Bearer <JWT>` é obrigatório, o token tem ~759 caracteres e **não vive em
// cookie, localStorage nem sessionStorage** — a varredura das três chaves não o encontrou.
// Ele nasce de `/api/sportsbook/auth`, que exige um corpo que só o app sabe montar (tentar
// `{type:"login"}` à mão devolve 401). Conclusão prática: o inject NUNCA inventa a
// requisição; ele aprende url + headers de uma real, como Betfair/Pinnacle/KTO/Jonbet.
//
// Consequência para o autodiagnóstico: sem a tela de histórico aberta uma vez, não há
// requisição para aprender — `hook: true` com `respostas: 0` e `semReq: true` quer dizer
// "abra Minhas Apostas", nunca "a casa não respondeu".
//
// ── PAGINAÇÃO ──────────────────────────────────────────────────────────────────────────
//
// `skip`/`take`, com `take` limitado a **100** — e a casa DIZ o limite em vez de truncar
// calada (`ErrorCode 2003`, `"Value should be in the range [1-100]"`, medido pedindo 200).
// O fim é autoritativo: `PurchasesCount` é o total da JANELA. O `skip` avança pelo que a
// casa REALMENTE devolveu, nunca pelo `take` pedido — a lição da Pitaco (s270), onde
// paginar perdia bilhete.
//
// ── O QUE ESTE ARQUIVO NÃO DECIDE ──────────────────────────────────────────────────────
//
// Nada. Ele normaliza e entrega campos crus; quem lê é o `formatTicketRG` no content.js, e
// quem traduz são as `casas/CASA_*.md`. Em especial, os enums `BetStatusId`/`PurchaseStatusId`
// sobem como números, sem virar W/L/V aqui — status novo (cashout, meia-liquidação) tem de
// ser reconhecível, não chutado.
(function () {
  const RX = /\/api\/sportsbook\/rogue\/v1\/betsreporting\/purchases/i;
  const byRef = new Map();          // PurchaseTicketId → bilhete normalizado
  let respostas = 0;                // respostas do endpoint que o hook viu (autodiagnóstico)
  let reqCtx = null;                // {url, headers, base} de uma requisição REAL (p/ replay)
  let pedido = false;               // o robô já pediu → pode arrancar o replay
  let loopAtivo = false;            // trava: um replay por vez
  let fimReplay = false;
  let erro = "";
  const LOG = (...a) => { try { console.log("[SharpenUp rg_inject]", ...a); } catch (e) {} };
  LOG("hook instalado em", location.href);

  const of = window.fetch;          // fetch ORIGINAL — o replay usa este (não re-dispara o wrapper)

  const PAGINA = 100;               // teto medido: 101 devolve ErrorCode 2003
  const TETO_PAGINAS = 200;
  const MESES = 36;                 // medido: a casa serve uma janela de 4 anos sem reclamar

  // ── normalização ───────────────────────────────────────────────────────────────
  // Dinheiro e odds vêm em REAIS (200 = R$ 200,00) — não há milésimos como na KTO. Mas os
  // campos chegam em DUAS formas no mesmo objeto: `Stake`/`Gain`/`BetClientOdds` como STRING
  // e `TotalStake`/`AmountToWin`/`BetTrueOdds` como número. Preferimos o numérico onde ele
  // existe e guardamos a string ao lado: é ela que preserva a precisão exata que a casa
  // escreveu (`"2.50"` diz duas casas; o número 2.5 já perdeu essa informação).
  const _n = (v) => {
    if (typeof v === "number") return isFinite(v) ? v : null;
    if (typeof v === "string" && v.trim() !== "") {
      const x = Number(v);
      return isFinite(x) ? x : null;
    }
    return null;
  };
  const _s = (v) => (v == null ? "" : String(v));

  function parseCompra(p, out) {
    if (!p || p.PurchaseTicketId == null) return;
    out.push({
      ref: _s(p.PurchaseTicketId),          // o [Código:] e a chave de dedup (é o "ID:" do card)
      betRef: _s(p.BetTicketId),            // sempre ref+1 nos 27 medidos; sobe por garantia
      colocada: _s(p.CreationDate),         // ISO com Z → o content converte p/ America/Sao_Paulo
      atualizada: _s(p.UpdateDate),         // vira "liquidado em" quando o bilhete resolveu
      statusBilhete: _n(p.BetStatusId),     // CRU: 0 aberta · 1 L · 2 W · 4 V (provado no dinheiro)
      statusCompra: _n(p.PurchaseStatusId), // CRU: acompanha o de cima em 27/27, mas sobe junto
      tipo: _s(p.BetName),                  // "Single" / (múltipla ainda não medida)
      tipoId: _n(p.BetTypeId),
      combo: _n(p.ComboSize),               // 0 em todos os 27 medidos
      apostas: _n(p.NumberOfBets),
      linhas: _n(p.NumberOfLines),          // > 1 indicaria sistema — nunca visto ainda
      stake: _n(p.TotalStake),              // o "Total aposta" do card
      stakeTexto: _s(p.Stake),
      stakeLinha: _n(p.UnitStake),          // = stake enquanto não houver sistema
      odd: _n(p.BetTrueOdds),
      oddTexto: _s(p.BetClientOdds),        // a precisão que a casa escreveu ("2.50")
      oddOriginal: _n(p.BetOriginalTrueOdds),  // difere da atual se a casa revisou a odd
      // ⚠ POTENCIAL, SEMPRE. Vale stake × odd em 27/27, inclusive em perdida e em aberta.
      potencial: _n(p.Gain),
      lucroPotencial: _n(p.AmountToWin),
      // ⚠ O RETORNO REALIZADO. É este que bate com o "Retorno:" do card.
      retorno: _n(p.CurrentBetBalance),
      moeda: _s(p.CustomerCurrencyCode),
      extras: Array.isArray(p.AdditionalTickets) ? p.AdditionalTickets : [],
      sels: (p.Selections || []).map((s) => ({
        selecao: _s(s.SelectionName),       // já traz a linha do handicap ("Joo Eun Kim -1.5")
        mercado: _s(s.MarketName),          // "Vencedor" / "Handicap" / "Resultado Final"
        mercadoEn: _s(s.EnMarketName),      // "FT Winner" / "FT Spread" — o canônico do motor
        jogo: _s(s.EventName),
        time1: _s(s.Team1name),
        time2: _s(s.Team2name),
        liga: _s(s.LeagueName),
        esporte: _s(s.SportName),           // já em pt-BR ("Vôlei", "Dardos", "Automobilismo")
        esporteEn: _s(s.EnSportName),       // "Volleyball" / "Darts" / "Motor Racing"
        esporteId: _n(s.SportId),
        tipoEvento: _n(s.EventTypeId),      // 0 = confronto · 8 = outright (F1, medido)
        odd: _n(s.SelectionTrueOdds),
        oddTexto: _s(s.SelectionClientOdds),
        // Handicap/total: só existe nesses mercados. Sobe cru (pode ser 0, que é linha
        // legítima — por isso o teste é `!= null`, nunca truthy).
        pontos: (s.Points == null ? null : _n(s.Points)),
        // ⚠ AUSENTE em aberta · string VAZIA em anulada · placar ("0 : 2") em resolvida ·
        // FRASE em outright ("Winner Kimi Antonelli, …"). Nunca assumir formato.
        resultado: (s.Result == null ? null : _s(s.Result)),
        resultadoFinal: (s.FullTimeResult == null ? null : _s(s.FullTimeResult)),
        resultadoLiq: (s.SettlementResult == null ? null : _s(s.SettlementResult)),
        statusSel: _n(s.SelectionStatus),   // mesmo enum do bilhete, por perna
        aoVivo: !!s.IsSelectionLive,
        // Placar NO MOMENTO da aposta (1/0 no vôlei ao vivo medido). NÃO é o resultado.
        placar1: _n(s.Score1),
        placar2: _n(s.Score2),
        inicio: _s(s.StartEventDate),       // ISO com Z — a data do EVENTO
        promos: Array.isArray(s.PromotionIds) ? s.PromotionIds : [],
      })),
    });
  }

  // Heartbeat: SEMPRE hook:true + respostas, mesmo com 0 bilhetes. É o que separa "o inject
  // não carregou" de "o endpoint respondeu e lemos 0" — sem isso os dois viram o mesmo nada.
  function enviar() {
    try {
      window.postMessage({
        __sharpenupRGData: true, hook: true,
        bilhetes: Array.from(byRef.values()), respostas: respostas, fim: fimReplay,
        semReq: !reqCtx, erro: erro,
      }, "*");
    } catch (e) {}
  }

  // Guarda o bilhete. O mesmo ref volta em passadas diferentes (a página pede 24h, o replay
  // pede tudo): a versão RESOLVIDA vence a ABERTA. `statusBilhete === 0` é o "ainda aberta".
  function guardar(b) {
    const ex = byRef.get(b.ref);
    if (!ex) { byRef.set(b.ref, b); return; }
    if (ex.statusBilhete === 0 && b.statusBilhete !== 0) byRef.set(b.ref, b);
  }

  // Processa uma resposta. Devolve {count, veio} ou null (corpo de erro / formato mudou).
  function forward(url, text) {
    if (!RX.test(String(url)) || typeof text !== "string") return null;
    let j;
    try { j = JSON.parse(text); } catch (e) { return null; }
    if (!j) return null;
    // Corpo de ERRO da casa (take fora do range, sessão caída): tem `ErrorCode` e nenhuma
    // lista. Registrar a mensagem em vez de engolir — é ela que diz o limite real.
    if (!Array.isArray(j.Purchases)) {
      if (j.ErrorCode != null) {
        const m = (j.ErrorMessages || [])[0] || {};
        erro = "casa recusou · ErrorCode " + j.ErrorCode + (m.Message ? " · " + m.Message : "");
        LOG(erro);
      }
      return null;
    }
    respostas++;
    const novos = [];
    for (const p of j.Purchases) parseCompra(p, novos);
    for (const b of novos) guardar(b);
    const count = typeof j.PurchasesCount === "number" ? j.PurchasesCount : 0;
    LOG("bilhetes na resposta:", j.Purchases.length, "· total:", byRef.size, "· count:", count);
    enviar();
    return { count: count, veio: j.Purchases.length };
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

  // Guarda a query real SEM os parâmetros que o replay controla. Tudo o que a casa exigir e
  // a gente não conhecer (parâmetro novo de canal, filtro) viaja junto sem ser mapeado — é
  // por isso que `locale` continua chegando sem estar escrito em lugar nenhum aqui.
  const _CONTROLADOS = { status: 1, take: 1, skip: 1, fromDate: 1, toDate: 1 };

  // ⚠ SEMPRE SOBRESCREVE o contexto aprendido, nunca só na primeira vez — **o Bearer desta
  // casa EXPIRA**. Medido ao vivo (s335): um token capturado e reusado ~1h depois responde
  // **401**, não 403. Guardar só a primeira requisição fazia o replay envelhecer junto com a
  // aba: numa aba aberta desde a manhã, o robô sairia com um token vencido e a captura
  // voltaria vazia — com o agravante de que 401 e "endpoint mudou" parecem a mesma coisa
  // para quem lê o painel. Como toda navegação da tela de histórico dispara uma requisição
  // nova, sobrescrever mantém o contexto sempre tão fresco quanto a última coisa que o
  // operador fez na página.
  function capturarReq(url, headers) {
    if (!RX.test(String(url))) return;
    let u;
    try { u = new URL(String(url), location.href); } catch (e) { return; }
    const base = [];
    try {
      u.searchParams.forEach((v, k) => { if (!_CONTROLADOS[k]) base.push([k, v]); });
    } catch (e) {}
    // Sem o `authorization` da página a requisição responde 403 — aprender uma requisição
    // que não o traga seria aprender a falhar, e SUBSTITUIR um contexto bom por um cego é
    // pior ainda. Melhor seguir com o que já se tem e esperar a próxima.
    const h = headers || {};
    const temAuth = Object.keys(h).some((k) => k.toLowerCase() === "authorization");
    if (!temAuth) { LOG("requisição sem authorization — ignorada, mantendo a anterior"); return; }
    const novo = !reqCtx;
    reqCtx = { url: u.origin + u.pathname, headers: h, base: base };
    LOG(novo ? "requisição capturada p/ replay" : "contexto do replay renovado (token fresco)");
    if (pedido) arrancarReplay();
  }

  // Janela larga. A casa aceitou 4 anos sem reclamar no recon; pedimos 36 meses para trás e
  // +1h para a frente (a folga cobre diferença de relógio entre navegador e servidor, e sem
  // ela uma aposta feita "agora" pode ficar de fora da própria janela que a pediu).
  function _janela() {
    const agora = new Date();
    const de = new Date(agora.getTime());
    de.setMonth(de.getMonth() - MESES);
    return { fromDate: de.toISOString(), toDate: new Date(agora.getTime() + 3600 * 1000).toISOString() };
  }

  function _url(skip) {
    const jan = _janela();
    const q = new URLSearchParams();
    for (const [k, v] of reqCtx.base) q.set(k, v);
    q.set("status", "all");          // aberta + liquidada numa chamada só
    q.set("take", String(PAGINA));
    q.set("skip", String(skip));
    q.set("fromDate", jan.fromDate);
    q.set("toDate", jan.toDate);
    return reqCtx.url + "?" + q.toString();
  }

  async function varrer() {
    let skip = 0;
    for (let i = 0; i < TETO_PAGINAS; i++) {
      let r;
      try {
        r = await of.call(window, _url(skip), {
          method: "GET", headers: reqCtx.headers, credentials: "include", cache: "no-store",
        });
      } catch (e) { erro = "replay falhou: " + (e && e.message); LOG(erro); return false; }
      if (!r || !r.ok) { erro = "replay parou · HTTP " + (r && r.status); LOG(erro); return false; }
      let st;
      try { st = forward(r.url || reqCtx.url, await r.text()); } catch (e) { return false; }
      if (!st) return false;                       // corpo de erro: `erro` já foi preenchido
      // Avança pelo que a casa REALMENTE devolveu, nunca pelo `take` pedido: se ela limitar
      // a página, o loop se autocorrige em vez de pular bilhete.
      skip += st.veio;
      if (st.veio <= 0 || skip >= st.count) return true;
    }
    LOG("teto de páginas atingido");
    return true;
  }

  async function arrancarReplay() {
    if (loopAtivo || fimReplay || !reqCtx) return;
    loopAtivo = true;
    try { await varrer(); } finally {
      loopAtivo = false;
      fimReplay = true;
      enviar();                                   // sinaliza fim p/ o robô parar de esperar
    }
  }

  // O content pede o acumulado ao iniciar o robô → re-envia tudo E arranca o replay. A 1ª
  // resposta pode chegar antes de o content estar ouvindo, por isso o re-envio existe.
  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (!d || !d.__sharpenupRGReq) return;
    pedido = true;
    enviar();
    arrancarReplay();
  });

  // ── fetch (é o transporte que a página usa — medido) ──
  if (of && !of.__suRGW) {
    const w = function (...a) {
      const req = (a[0] && typeof a[0] === "object" && a[0].url) ? a[0] : null;
      const url = req ? req.url : a[0];
      const opts = a[1] || {};
      try {
        if (RX.test(String(url))) {
          const hdrs = req ? _hdrsToObj(req.headers) : _hdrsToObj(opts.headers);
          capturarReq(url, hdrs);
        }
      } catch (e) {}
      return of.apply(this, a).then((r) => {
        // Leitura PASSIVA: aqui ela funciona de verdade (o clone resolve), então aproveita de
        // graça o que a página baixou. O 2º argumento do `.then` é obrigatório — sem ele uma
        // rejeição do clone morreria como unhandled rejection e "o passivo quebrou" ficaria
        // indistinguível de "o endpoint mudou" (o defeito mudo da SportingBet, s305).
        try {
          if (RX.test(String(url))) {
            r.clone().text().then(
              (t) => { try { forward(url, t); } catch (e) {} },
              (e) => { LOG("clone da resposta rejeitou:", e && e.name); }
            );
          }
        } catch (e) {}
        return r;
      });
    };
    w.__suRGW = true;
    window.fetch = w;
  }

  // ── XMLHttpRequest (rede de segurança) ──
  // Medido: a página usa fetch. Este bloco fica para o caso de a casa trocar de transporte.
  function _corpoResposta(xhr) {
    try {
      const tipo = xhr.responseType;
      if (tipo === "" || tipo === "text") return xhr.responseText;
      if (tipo === "json") return JSON.stringify(xhr.response);
    } catch (e) {}
    return "";
  }

  const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send,
        osh = XMLHttpRequest.prototype.setRequestHeader;
  if (!os.__suRGW) {
    XMLHttpRequest.prototype.open = function (m, u) { this.__suRGU = u; this.__suRGH = {}; return oo.apply(this, arguments); };
    XMLHttpRequest.prototype.setRequestHeader = function (k, v) { try { this.__suRGH[k] = v; } catch (e) {} return osh.apply(this, arguments); };
    const s = function () {
      try {
        if (RX.test(String(this.__suRGU))) {
          capturarReq(this.__suRGU, this.__suRGH);
          this.addEventListener("load", () => {
            try { forward(this.__suRGU, _corpoResposta(this)); } catch (e) {}
          });
        }
      } catch (e) {}
      return os.apply(this, arguments);
    };
    s.__suRGW = true;
    XMLHttpRequest.prototype.send = s;
  }
})();
