// Mundo MAIN (só na 1xBet): escuta a requisição de histórico que a página faz, aprende
// url + headers + corpo, e REFAZ a chamada alargando a janela.
//
//   POST 1xbet.bet.br/service/bethistory/GetBetInfoHistoryWithSummaryByDates → a lista
//
// PLATAFORMA PRÓPRIA. App Vue, API toda em `/service/` no host da casa. Não é Altenar/BIA,
// não é BetBy, não é Kambi, não é BetConstruct, não é BlueBrown (Novibet). Inject próprio.
//
// O PASSIVO FUNCIONA AQUI — e isso não era garantido. Pitaco (s270) e Novibet (s271) abortam
// o próprio request e o `clone().text()` rejeita; nesta casa ele resolveu limpo nas 34
// capturas do recon, com zero erro de leitura. Então o hook lê o que a página recebe E o
// replay busca o resto. Consequência para o autodiagnóstico: `respostas` conta as DUAS
// origens, ao contrário da Novibet, onde só o replay respondia.
//
// O REPLAY EXISTE PARA ALARGAR A JANELA, não para paginar:
//
//   • A TELA PEDE ~5,2 DIAS, PARA SEMPRE. O corpo da página traz `DateFrom`/`DateTo` com
//     ~450.000 s de intervalo, e a página reconsulta a MESMA janela a cada ~5 segundos (34
//     requisições em 3 minutos no recon, todas idênticas menos o `DateTo`, que anda com o
//     relógio). Um passivo perfeito pegaria 91 bilhetes de 95 e pareceria completo.
//
//   • NÃO EXISTE PAGINAÇÃO. Não há `skip`, `page`, `offset` nem cursor. Os únicos controles
//     são `Count` e a janela. Quando o lote volta menor que o total, o único movimento
//     possível é PEDIR UM `Count` MAIOR — é o que `arrancarReplay` escala.
//
// FIM AUTORITATIVO DE VERDADE: `BetsSummaryInfo.Count` é o total da JANELA e **não muda** com
// o `Count` pedido. Medido ao vivo na conta real: `Count:10` devolveu 10 bilhetes e seguiu
// dizendo `Count: 95`; `Count:1000` e `Count:5000` devolveram os 95. Isso distingue "acabou"
// de "a consulta encheu" — exatamente o que o `Count` da Tivo NÃO distinguia (s211), e por
// isso aqui não é preciso o segundo eixo de varrer a janela para trás.
//
// AUTH É POR COOKIE — **não há `Authorization`**. Os headers são só de canal (`accept`,
// `content-type`, `x-language`). Mesmo assim o inject NUNCA monta a requisição do zero: o
// corpo carrega `PartnerId`, `PartnerGroupId`, `Whence`, `CfView` e `BonusUserId`, que são da
// conta e do tenant. Aprender de uma requisição real é o que faz a captura acompanhar sozinha
// qualquer mudança de canal.
//
// ⚠ A casa manda `x-location-latitude` / `x-location-longitude` em toda requisição. Eles
// viajam de volta intactos no replay (são headers da página, aprendidos), mas o coletor de
// recon os REDIGE antes de salvar — é a geolocalização de quem coletou. Ver `tools/recon_casa.js`.
//
// ARMADILHAS confirmadas no dado real. O inject NÃO decide nada: entrega campos crus e quem
// lê é o `formatTicket1X` no content.js, com a `CASA_1XBET.md`.
//   • `Coef` DO BILHETE MENTE NA PERDIDA. Com perna anulada, a casa recalcula o `Coef` se o
//     bilhete GANHOU (7 de 7) e não recalcula se PERDEU (9 de 9 ficam pré-anulação, o 16101007
//     dizendo 8,607956 onde a estrutura é 4,5787). Por isso o inject sobe TAMBÉM o produto das
//     pernas (`oddProduto`) e a marca `temAnulada` — quem escolhe é o formatador.
//   • PERNA ANULADA se reconhece por `Coef == 1` (18 pernas); só 6 trazem
//     `ReturnedBetEventReasonName`, então o texto NÃO serve de detector.
//   • A ANULADA NÃO TEM STATUS PRÓPRIO: `BetStatus` só assume 1/2/4 em 95 bilhetes. A aposta
//     anulada vem como **4 (ganha)** com `WinSum == BetSum` e `Coef == 1`. O enum não separa
//     V de W — o dinheiro separa.
//   • `PossibleWinSum` só existe em ABERTA e `WinSum` só em resolvida — nunca coexistem. Não
//     há vitória fantasma nesta casa (medido: 10 / 15 / 66, sem interseção).
//   • `CoefView` é TRUNCADA (`14.704694` → `"14.704"`), é o número do card. A exata é `Coef`.
//   • `UnixGameStartDate` == maior `StartDate` das pernas em 91 de 91 — a casa já entrega o
//     "evento mais recente". Epoch em SEGUNDOS.

(function () {
  const RX = /\/service\/bethistory\/GetBetInfoHistoryWithSummaryByDates/i;
  const byRef = new Map();                     // BetId(string) → bilhete normalizado
  let respostas = 0;                           // respostas do endpoint (passivas + replay)
  let reqCtx = null;                           // {url, headers} de uma requisição real
  let corpoBase = null;                        // corpo real da página, sem o que o replay controla
  let pedido = false;                          // o robô já pediu → pode arrancar o replay
  let loopAtivo = false;
  let fimReplay = false;
  let totalCasa = 0;                            // último `BetsSummaryInfo.Count` visto
  let erro = "";
  const LOG = (...a) => { try { console.log("[SharpenUp x1_inject]", ...a); } catch (e) {} };
  LOG("hook instalado em", location.href);

  const of = window.fetch;                     // fetch ORIGINAL — o replay usa este

  const MESES = 12;
  const COUNT_INICIAL = 1000;
  const COUNT_TETO = 25000;
  const TENTATIVAS = 6;

  // ── normalização ────────────────────────────────────────────────────────────────────────
  // Dinheiro e odds vêm em REAIS, como número (150 = R$ 150,00). Não há milésimos.
  const _n = (v) => (typeof v === "number" ? v : null);
  const _s = (v) => (v == null ? "" : String(v));

  function parseBet(t, out) {
    if (!t || t.BetId == null) return;
    const evs = Array.isArray(t.Events) ? t.Events : [];
    // Produto das pernas: a odd ESTRUTURAL. Sobe cru junto com o `Coef` declarado porque em
    // bilhete perdido com anulação os dois divergem e só o formatador sabe qual usar.
    let produto = 1;
    let temAnulada = false;
    for (const e of evs) {
      const c = _n(e.Coef);
      if (c != null) produto *= c;
      if (c === 1) temAnulada = true;
    }
    out.push({
      ref: _s(t.BetId),                        // o [Código:] e a chave de dedup
      status: _n(t.BetStatus),                 // 1=aberta · 2=perdida · 4=ganha (CRU)
      colocada: _n(t.BetDate),                 // epoch s
      evento: _n(t.UnixGameStartDate),         // epoch s — maior StartDate das pernas
      liquidada: _n(t.BetSettlingDate),        // ausente = aberta
      tipoNome: _s(t.BetTypeName),             // "Acumulador" / "Simples"
      tipoId: _n(t.BetTypeId),
      sistema: _n(t.BetSystemType),            // 1=simples · 3=acumulador
      stake: _n(t.BetSum),
      odd: _n(t.Coef),                         // ⚠ pré-anulação em bilhete PERDIDO
      oddTexto: _s(t.CoefView),                // truncada — é a do card
      oddProduto: evs.length ? produto : null, // odd estrutural real
      temAnulada: temAnulada,
      pagou: _n(t.WinSum),                     // só em resolvida
      payout: _n(t.PayoutSum),
      potencial: _n(t.PossibleWinSum),         // só em aberta
      moeda: _s(t.CurrencyCode),
      sels: evs.map((e) => ({
        esporte: _s(e.SportName),              // pt-BR ⚠ "Badminton " com espaço, "Tenis de Mesa" sem acento
        esporteEng: _s(e.SportNameEng),
        camp: _s(e.ChampName),
        jogo: _s(e.GameName),
        opp1: _s(e.Opp1Name),
        opp2: _s(e.Opp2Name),
        mercado: _s(e.EventTypeName),          // "Equipe 1 Total Acima de 1.5 no 75° Minuto"
        param: _n(e.Param),
        odd: _n(e.Coef),                       // == 1 ⇒ perna ANULADA
        oddTexto: _s(e.CoefView),
        inicio: _n(e.StartDate),
        resultado: _n(e.EventResult),
        placar: _s(e.Score),
        periodo: _s(e.PeriodName),
        anulada: _n(e.Coef) === 1,
        razao: _s(e.ReturnedBetEventReasonName),
        razaoStatus: _s(e.ReturnedBetEventStatusName),
        aoVivo: !!e.IsLiveGameInLive,
      })),
    });
  }

  // Emite SEMPRE hook:true + respostas (heartbeat), mesmo com 0 bilhetes.
  function enviar() {
    try {
      window.postMessage({
        __sharpenupX1Data: true, hook: true,
        bilhetes: Array.from(byRef.values()), respostas: respostas, fim: fimReplay,
        total: totalCasa, erro: erro,
      }, "*");
    } catch (e) {}
  }

  // O mesmo BetId pode voltar em janelas diferentes. A versão RESOLVIDA vence a ABERTA —
  // `BetSettlingDate` só existe depois de liquidar.
  function guardar(b) {
    const ex = byRef.get(b.ref);
    if (!ex) { byRef.set(b.ref, b); return; }
    if (ex.liquidada == null && b.liquidada != null) byRef.set(b.ref, b);
  }

  // Processa uma resposta. Devolve `{total, veio}` ou null.
  function forward(url, text) {
    if (!RX.test(String(url)) || typeof text !== "string") return null;
    let j;
    try { j = JSON.parse(text); } catch (e) { return null; }
    if (!j || !Array.isArray(j.BetInfos)) return null;    // corpo de erro / formato mudou
    respostas++;
    const novos = [];
    for (const t of j.BetInfos) parseBet(t, novos);
    for (const b of novos) guardar(b);
    const si = j.BetsSummaryInfo || {};
    if (typeof si.Count === "number") totalCasa = si.Count;
    LOG("bilhetes na resposta:", j.BetInfos.length, "· acumulado:", byRef.size,
        "· total da janela:", si.Count);
    enviar();
    return { total: typeof si.Count === "number" ? si.Count : 0, veio: j.BetInfos.length };
  }

  // ── replay ativo ───────────────────────────────────────────────────────────────────────
  function _hdrsToObj(h) {
    const o = {};
    try {
      if (!h) return o;
      if (typeof h.forEach === "function") h.forEach((v, k) => { o[k] = v; });
      else if (typeof h === "object") for (const k in h) o[k] = h[k];
    } catch (e) {}
    return o;
  }

  function _corpoObj(corpo) {
    if (!corpo || typeof corpo !== "string") return null;
    try {
      const o = JSON.parse(corpo);
      return (o && typeof o === "object") ? o : null;
    } catch (e) { return null; }
  }

  // Guarda o corpo real SEM os campos que o replay controla. Tudo o que a casa exigir e a
  // gente não conhecer (campos novos de canal, o `BonusUserId` da conta) viaja junto sem
  // precisar ser mapeado — é o que mantém a captura viva quando a casa mexe no protocolo.
  function aprender(corpo) {
    const o = _corpoObj(corpo);
    if (!o || corpoBase) return;
    const base = {};
    for (const k in o) {
      if (k === "Count" || k === "DateFrom" || k === "DateTo") continue;
      base[k] = o[k];
    }
    corpoBase = base;
    LOG("corpo da lista aprendido");
  }

  function capturarReq(url, headers, corpo) {
    if (!RX.test(String(url))) return;
    aprender(corpo);
    if (!reqCtx) {
      reqCtx = { url: String(url), headers: headers || {} };
      LOG("requisição capturada p/ replay");
    }
    if (pedido) arrancarReplay();
  }

  // Janela larga: 12 meses para trás, +1 h para a frente (folga de relógio entre navegador e
  // servidor). A casa não anuncia teto de histórico — `UseArchive: true` já vem no corpo da
  // própria página, então o arquivo morto está incluído. Se houver corte, ele aparece como
  // `BetsSummaryInfo.Count` estável e menor, não como erro.
  function _janela() {
    const agora = Math.floor(Date.now() / 1000);
    const de = new Date();
    de.setMonth(de.getMonth() - MESES);
    return { DateFrom: Math.floor(de.getTime() / 1000), DateTo: agora + 3600 };
  }

  // Uma tentativa com um `Count`. Devolve `{total, veio}` ou null.
  async function pedir(count, jan) {
    const corpo = JSON.stringify(Object.assign({}, corpoBase, jan, { Count: count }));
    let r;
    try {
      r = await of.call(window, reqCtx.url, {
        method: "POST", headers: (reqCtx && reqCtx.headers) || {},
        credentials: "include", body: corpo,
      });
    } catch (e) { erro = "replay falhou: " + (e && e.message); LOG(erro); return null; }
    if (!r || !r.ok) { erro = "replay parou · HTTP " + (r && r.status); LOG(erro); return null; }
    try { return forward(r.url || reqCtx.url, await r.text()); } catch (e) { return null; }
  }

  // Não há paginação: o laço ESCALA o `Count` enquanto o lote voltar menor que o total que a
  // própria casa declara. Medido: `Count:1000` já basta para 95 bilhetes — a escalada é a
  // rede de segurança de uma conta grande, e para no `BetsSummaryInfo.Count`, que é fim
  // autoritativo de verdade (não muda com o tamanho pedido).
  async function arrancarReplay() {
    if (loopAtivo || fimReplay || !reqCtx || !corpoBase) return;
    loopAtivo = true;
    try {
      const jan = _janela();
      let count = COUNT_INICIAL;
      for (let i = 0; i < TENTATIVAS; i++) {
        const st = await pedir(count, jan);
        if (!st) break;                                   // erro de rede/HTTP: para e reporta
        if (st.veio >= st.total || st.total === 0) break;  // fim AUTORITATIVO
        if (count >= COUNT_TETO) {
          erro = "lote incompleto: " + st.veio + " de " + st.total + " com Count=" + count;
          LOG(erro);
          break;
        }
        count = Math.min(count * 5, COUNT_TETO);
        LOG("lote curto (" + st.veio + "/" + st.total + ") · escalando Count para", count);
      }
    } finally {
      loopAtivo = false;
      fimReplay = true;
      enviar();
    }
  }

  // O content script pede o acumulado ao iniciar o robô → re-envia tudo E arranca o replay.
  // A 1ª página chega no load, antes de o content estar ouvindo; sem isto ela se perderia.
  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (!d || !d.__sharpenupX1Req) return;
    pedido = true;
    enviar();
    arrancarReplay();
  });

  // ── fetch ──
  if (of && !of.__suX1W) {
    const w = function (...a) {
      const req = (a[0] && typeof a[0] === "object" && a[0].url) ? a[0] : null;
      const url = req ? req.url : a[0];
      const opts = a[1] || {};
      try {
        if (RX.test(String(url))) {
          if (req) {
            const hdrs = _hdrsToObj(req.headers);
            let clone = null;
            try { clone = req.clone(); } catch (e) {}
            if (clone && typeof clone.text === "function") {
              clone.text().then((t) => capturarReq(url, hdrs, t)).catch(() => {});
            } else {
              capturarReq(url, hdrs, typeof opts.body === "string" ? opts.body : null);
            }
          } else {
            capturarReq(url, _hdrsToObj(opts.headers),
                        typeof opts.body === "string" ? opts.body : null);
          }
        }
      } catch (e) {}
      return of.apply(this, a).then((r) => {
        // Leitura PASSIVA — e aqui ela funciona de verdade (medido: 34 de 34 clones
        // resolveram no recon), diferente de Pitaco e Novibet. É ela que entrega os
        // bilhetes da janela da tela antes mesmo de o robô arrancar.
        try {
          if (RX.test(String(url))) r.clone().text().then((t) => forward(url, t)).catch(() => {});
        } catch (e) {}
        return r;
      });
    };
    w.__suX1W = true;
    window.fetch = w;
  }

  // Corpo de uma resposta XHR, respeitando o `responseType`. Em `responseType: "json"` ler
  // `responseText` LANÇA InvalidStateError — o corpo só existe em `.response`.
  function _corpoResposta(xhr) {
    try {
      const tipo = xhr.responseType;
      if (tipo === "" || tipo === "text") return xhr.responseText;
      if (tipo === "json") return JSON.stringify(xhr.response);
    } catch (e) {}
    return "";
  }

  // ── XMLHttpRequest (rede de segurança) ──
  // Medido: a página usa **fetch**. Este bloco fica para o caso de a casa trocar de transporte.
  const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send,
        osh = XMLHttpRequest.prototype.setRequestHeader;
  if (!os.__suX1W) {
    XMLHttpRequest.prototype.open = function (m, u) { this.__suX1U = u; this.__suX1H = {}; return oo.apply(this, arguments); };
    XMLHttpRequest.prototype.setRequestHeader = function (k, v) { try { this.__suX1H[k] = v; } catch (e) {} return osh.apply(this, arguments); };
    const s = function (body) {
      try {
        if (RX.test(String(this.__suX1U))) {
          capturarReq(this.__suX1U, this.__suX1H, typeof body === "string" ? body : null);
          this.addEventListener("load", () => {
            try { forward(this.__suX1U, _corpoResposta(this)); } catch (e) {}
          });
        }
      } catch (e) {}
      return os.apply(this, arguments);
    };
    s.__suX1W = true;
    XMLHttpRequest.prototype.send = s;
  }
})();
