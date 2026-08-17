// Mundo MAIN (só na Novibet): aprende a requisição de histórico que a página faz e BUSCA a
// lista ele mesmo, repassando ao content script.
//
//   POST www.novibet.bet.br/spt/api/historytickets/search   → a lista (abertas E fechadas)
//
// ⚠ O MODO PASSIVO É IMPOSSÍVEL AQUI — medido, não suposto. A página é Angular e o
// `HttpClient` aborta o próprio request ao desinscrever: o `clone().text()` da resposta morre
// com **"The user aborted a request."**, exatamente como na Pitaco (s270). Por isso este
// inject NUNCA lê a resposta que a página recebeu; ele só aprende url + headers + corpo e
// refaz a chamada. Consequência para o autodiagnóstico: **`respostas` conta as do REPLAY**,
// não as da página — hook ATIVO com `respostas: 0` significa que o replay não rodou (o painel
// de apostas nunca foi aberto, ou a sessão caiu), nunca "a casa não respondeu".
//
// Corpo real da página (recon s271, capturado no F12):
//   {"dateFrom":"…Z","dateTo":"…Z","skip":0,"take":20,"result":2,
//    "sortOrder":"Descending","sorting":2,"type":null}
//
// PLATAFORMA PRÓPRIA. A Novibet não é espelho de ninguém: não é Altenar/BIA, não é BetBy,
// não é Kambi, não é BetConstruct. O gateway é `BlueBrown.OnlineSportsbook.Gateway` (aparece
// no `$type` de todo objeto) e os endpoints vivem no mesmo host da casa, em `/spt/` e
// `/ngapi/`. Inject próprio, formatador próprio.
//
// O REPLAY É OBRIGATÓRIO, e por TRÊS motivos independentes — nenhum deles é paginação:
//
//   (0) O PASSIVO NÃO EXISTE (ver acima): o corpo da resposta da página é inalcançável.
//
//   (1) A TELA PEDE UM DIA SÓ. O corpo que a página envia tem `dateFrom`/`dateTo` com
//       ~24h de intervalo (é o filtro do próprio painel). Um inject puramente passivo
//       capturaria o dia corrente e mais nada — a conta tinha 42 bilhetes em 12 meses e
//       11 no dia da medição. Quem alarga a janela é o replay.
//   (2) A TELA PEDE SÓ AS FECHADAS. O campo `result` filtra: 1=Pending · 2=fechadas ·
//       3=ganhas · **null = TUDO**. O `null` é um uso que a página nunca faz, e traz
//       abertas + fechadas numa chamada (medido: 1→7, 2→35, null→42 = 7+35). Mesma
//       família do truque do `status` omitido no `stk_inject`.
//
// AUTH É POR COOKIE, mas os HEADERS `x-gw-*` são obrigatórios: sem eles a mesma requisição
// responde **500** (medido), e com eles + corpo idêntico responde 200 byte a byte. São 11
// headers de canal (`x-gw-application-name: NoviBR`, `x-gw-client-timezone`, …), sem token
// nem segredo — mas o inject NUNCA os inventa: aprende de uma requisição real, como
// Betfair/Pinnacle/KTO. Se a casa mudar um valor de canal, a captura acompanha sozinha.
//
// PAGINAÇÃO — `skip`/`take`, com `take` limitado a **50** (51 já devolve 400; medido por
// busca binária). O fim é AUTORITATIVO de verdade: `statistics.count` é o total da JANELA e
// **não muda com skip/take** (medido: skip=5 devolve 6 itens e segue dizendo count=11).
// Provado por códigos ÚNICOS em três estratégias — take 50, 20 e 7 → 42 lidos / 42 únicos
// nas três, sem repetição nem perda (a lição da Pitaco, onde paginar PERDIA bilhete).
//
// TETO DE HISTÓRICO: a casa devolve `statistics.maxDurationInMonths: 12` e liga
// `maxDurationExceeded` quando a janela pedida passa disso. O inject pede 12 meses e
// repassa a flag — histórico mais antigo que isso a casa simplesmente não serve.
//
// ARMADILHAS confirmadas no dado real (o inject NÃO decide nada — só entrega campos crus;
// quem lê é o formatTicketNV no content.js):
//   • `finalFinancials.payout` é SEMPRE o retorno POTENCIAL, inclusive em bilhete PERDIDO
//     (474311813: perdeu e o campo diz 529,4268). O retorno REAL só existe em
//     `settlement.payout`. Quem ler o campo óbvio marca toda perdida como ganha.
//   • `settlement` é **null** em toda aberta — é o separador limpo entre aberta e resolvida.
//   • `placedPrice` tem `value` (exata) e `text` (o que o card estampa, arredondado a 2
//     casas): 11.844 vs "11.84". A odd exata é a `value`, sempre (regra primordial).
//   • Em bilhete de SISTEMA (`ticketType: "Fold2"`), `placedPrice` **não é a odd**: é a
//     SOMA dos produtos das C(n,k) linhas (medido: 19 de 19). E `cost` é o stake TOTAL
//     enquanto `amount` é o stake POR LINHA (cost/amount == multiplier em 19 de 19).
//   • A odd da perna e a do bilhete já vêm PÓS-BOOST — o card mostra a riscada
//     (`13.00@ 17.66`), o payload traz só a efetiva (17.661 = produto das pernas).
//   • `placedFinancials.boost` é OUTRO mecanismo: bônus multiplicativo pago por fora
//     (`payout = cost × odd × factor`, factor 1.05 medido). Sobe cru.
//   • `offerCaption` vem com o emoji 🚀 COLADO quando a odd foi turbinada — normalizamos
//     separando o marcador do rótulo, senão o mapa de mercados nunca casaria.
//   • NÃO EXISTE data de evento no payload (varredura de todo campo temporal: só `placedAt`
//     e `settledAt`). A data do card é `placedAt` em America/Sao_Paulo — conferido ao
//     segundo: `2026-08-16T15:01:27Z` ⇄ o card diz `16/8/2026, 12:01:27`.
(function () {
  const RX = /\/spt\/api\/historytickets\/search/i;   // endpoint da LISTA de bilhetes
  const byRef = new Map();                     // ticketId(string) → bilhete normalizado
  let respostas = 0;                           // respostas do endpoint que o hook viu (autodiagnóstico)
  let reqCtx = null;                           // {url, headers} de uma requisição real (p/ replay)
  let corpoBase = null;                        // corpo real da página, sem os campos que o replay controla
  let pedido = false;                          // o robô já pediu → pode arrancar o replay
  let loopAtivo = false;                       // trava: um replay por vez
  let fimReplay = false;                       // a varredura terminou
  let truncado = false;                        // a casa disse que a janela estourou os 12 meses
  let erro = "";                               // último erro do replay (vai no autodiagnóstico)
  const LOG = (...a) => { try { console.log("[SharpenUp nv_inject]", ...a); } catch (e) {} };
  LOG("hook instalado em", location.href);

  const of = window.fetch;                     // fetch ORIGINAL — o replay usa este (não re-dispara o wrapper)

  const PAGINA = 50;           // teto medido: 51 devolve 400
  const TETO_PAGINAS = 200;
  const MESES = 12;            // `statistics.maxDurationInMonths` da própria casa

  // ── normalização (gateway BlueBrown → objeto limpo) ────────────────────────────
  // Dinheiro e odds vêm em REAIS, já como número (44.7 = R$44,70). Não há milésimos.
  const _n = (v) => (typeof v === "number" ? v : null);
  const _s = (v) => (v == null ? "" : String(v));
  const _preco = (p) => (p && typeof p === "object")
    ? { valor: _n(p.value), texto: _s(p.text) } : { valor: null, texto: "" };

  // O 🚀 marca odd turbinada e vem COLADO no rótulo do mercado. Separar aqui é normalizar
  // (o rótulo limpo é o que a CASA_NOVIBET §9 mapeia), e o sinal não se perde: vira `turbinada`.
  function _rotulo(txt) {
    const s = _s(txt);
    const turbinada = /🚀/.test(s);
    return { texto: s.replace(/🚀/g, " ").replace(/\s+/g, " ").trim(), turbinada };
  }

  function parseTicket(t, out) {
    if (!t || t.ticketId == null) return;
    const pf = t.placedFinancials || {};
    const ff = t.finalFinancials || {};
    const st = t.settlement || null;
    out.push({
      ref: _s(t.ticketId),                     // o [Código:] e a chave de dedup
      colocada: _s(t.placedAt),                // UTC com Z → o content converte p/ SP
      liquidada: st ? _s(st.settledAt) : "",
      resultado: _s(t.result),                 // Won / Lost / Pending (CRU)
      tipo: _s(t.ticketType),                  // Accumulator / Fold2 (CRU)
      linhas: _n(t.multiplier),                // nº de apostas do sistema (1 = linha única)
      stake: _n(pf.cost),                      // TOTAL — é o que o card estampa em "Valor"
      stakeLinha: _n(pf.amount),               // por linha (só difere em sistema)
      desconto: _n(pf.costDiscount),
      odd: _preco(t.placedPrice),              // ⚠ em SISTEMA é a SOMA das linhas, não a odd
      oddFinal: _preco(t.finalPrice),          // riscada quando uma perna é anulada
      potencial: _n(ff.payout),                // ⚠ SEMPRE potencial, mesmo em perdida
      pagou: st ? _n(st.payout) : null,        // retorno REAL — null = ainda não liquidou
      imposto: st ? _n(st.withholdingTax) : null,
      impostoBonus: st ? _n(st.taxBonus) : null,
      boost: pf.boost || null,                 // {amount, factor, isMax} — bônus por fora
      bonus: pf.bonus || null,
      cashout: t.cashout || null,
      cashoutPreco: _preco(t.cashoutPrice).valor != null ? _preco(t.cashoutPrice) : null,
      sels: (t.selections || []).map((s) => {
        const bi = s.betInstance || {};
        const bc = s.betContext || {};
        const r = _rotulo(bi.offerCaption);
        return {
          mercado: r.texto,                    // "Total de Gols" (sem o 🚀)
          turbinada: r.turbinada,              // a casa turbinou a odd desta perna
          selecao: _s(bi.offerBetCaption),     // "Mais de 2,5" / "Chicago Fire FC"
          jogo: _s(bc.betContextCaption),      // "Chicago Fire FC - Portland Timbers"
          esporte: _s(bc.competitionContextCaption),      // "Futebol" (pt-PT: "Ténis")
          esporteSys: _s(bc.competitionContextSysname),   // SOCCER / TENNIS_SINGLES / …
          mercadoSys: _s(bi.marketSysname),    // SOCCER_POINT_CARDS_RESULT
          odd: _preco(bi.placedPrice),
          resultado: _s(bi.finalResult || bi.result),     // Won/Lost/HalfLostHalfVoid/""
          sobrescrito: _s(bi.overriddenResult),
          tag: _s(bi.settlementTag),
          aoVivo: !!bc.placedIsLive,
          banker: !!s.isBanker,                // sistema com perna fixa
          blindada: !!s.securedOdds,
        };
      }),
    });
  }

  // Emite SEMPRE hook:true + respostas (heartbeat), mesmo com 0 bilhetes — o content distingue
  // "hook não carregou" de "endpoint respondeu, lemos 0" (mesmo autodiagnóstico das outras).
  function enviar() {
    try {
      window.postMessage({
        __sharpenupNVData: true, hook: true,
        bilhetes: Array.from(byRef.values()), respostas: respostas, fim: fimReplay,
        truncado: truncado, erro: erro,
      }, "*");
    } catch (e) {}
  }

  // Guarda o bilhete. O mesmo ref pode voltar em variantes diferentes (a página pede as
  // fechadas, o replay pede tudo): a versão LIQUIDADA vence a ABERTA — `settlement` só
  // existe depois de liquidar, e é ele que traz o dinheiro final.
  function guardar(b) {
    const ex = byRef.get(b.ref);
    if (!ex) { byRef.set(b.ref, b); return; }
    if (ex.pagou == null && b.pagou != null) byRef.set(b.ref, b);
  }

  // Processa uma resposta. Devolve `{count, veio}` (p/ o replay saber se continua) ou null.
  // `veio` é quantos bilhetes a CASA devolveu nesta página — é por ele que o `skip` avança,
  // nunca pelo `take` que pedimos: se a casa limitar a página, o loop se autocorrige.
  function forward(url, text) {
    if (!RX.test(String(url)) || typeof text !== "string") return null;
    let j;
    try { j = JSON.parse(text); } catch (e) { return null; }
    if (!j || !Array.isArray(j.historyTickets)) return null;   // corpo de erro / formato mudou
    respostas++;
    const novos = [];
    for (const t of j.historyTickets) parseTicket(t, novos);
    for (const b of novos) guardar(b);
    const st = j.statistics || {};
    if (st.maxDurationExceeded) truncado = true;
    LOG("bilhetes na resposta:", j.historyTickets.length, "· total:", byRef.size,
        "· count:", st.count);
    enviar();
    return { count: typeof st.count === "number" ? st.count : 0, veio: j.historyTickets.length };
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

  function _corpoObj(corpo) {
    if (!corpo || typeof corpo !== "string") return null;
    try {
      const o = JSON.parse(corpo);
      return (o && typeof o === "object") ? o : null;
    } catch (e) { return null; }
  }

  // Guarda o corpo real SEM os campos que o replay controla. Tudo o que a casa exigir e a
  // gente não conhecer (campos novos de canal, filtros) viaja junto sem precisar ser mapeado.
  function aprender(corpo) {
    const o = _corpoObj(corpo);
    if (!o || corpoBase) return;
    const base = {};
    for (const k in o) {
      if (k === "skip" || k === "take" || k === "result" ||
          k === "dateFrom" || k === "dateTo") continue;
      base[k] = o[k];
    }
    corpoBase = base;
    LOG("corpo da lista aprendido");
  }

  function capturarReq(url, headers, corpo) {
    if (!RX.test(String(url))) return;
    aprender(corpo);
    if (!reqCtx) {
      // Só os headers que a página definiu (os `x-gw-*` + content-type). Nada de cookie:
      // vai no credentials:"include", como nas outras casas.
      reqCtx = { url: String(url), headers: headers || {} };
      LOG("requisição capturada p/ replay");
    }
    if (pedido) arrancarReplay();
  }

  // Janela máxima que a casa serve, com DUAS folgas deliberadas:
  //
  //   • no início, +2 dias: pedir os 12 meses cheios liga `maxDurationExceeded` (medido ao
  //     vivo — a casa considera a borda como estouro). A flag existe para avisar que o
  //     histórico foi cortado; se ela acendesse em toda captura viraria ruído, e o operador
  //     aprenderia a ignorar justamente o aviso que importa.
  //   • no fim, +1 hora: cobre diferença de relógio entre navegador e servidor, sem empurrar
  //     a janela total para além do teto.
  function _janela() {
    const agora = new Date();
    const de = new Date(agora.getTime());
    de.setMonth(de.getMonth() - MESES);
    de.setDate(de.getDate() + 2);
    const ate = new Date(agora.getTime() + 3600 * 1000);
    return { dateFrom: de.toISOString(), dateTo: ate.toISOString() };
  }

  // Varre uma variante de `result` inteira. `null` = tudo (abertas + fechadas).
  async function varrer(result) {
    const jan = _janela();
    let skip = 0;
    for (let i = 0; i < TETO_PAGINAS; i++) {
      const corpo = JSON.stringify(Object.assign({}, corpoBase, jan, {
        skip: skip, take: PAGINA, result: result,
      }));
      let r;
      try {
        r = await of.call(window, reqCtx.url, {
          method: "POST", headers: (reqCtx && reqCtx.headers) || {},
          credentials: "include", body: corpo,
        });
      } catch (e) { erro = "replay falhou: " + (e && e.message); LOG(erro); return false; }
      if (!r || !r.ok) {
        erro = "replay parou · HTTP " + (r && r.status);
        LOG(erro);
        return false;
      }
      let st;
      try { st = forward(r.url || reqCtx.url, await r.text()); } catch (e) { return false; }
      if (!st) return false;
      // Avança pelo que a casa REALMENTE devolveu nesta página, nunca pelo que pedimos.
      skip += st.veio;
      // Fim AUTORITATIVO: `count` é o total da JANELA e não muda com skip/take (medido —
      // skip=5 devolveu 6 itens e seguiu dizendo count=11). Distingue "acabou" de "a
      // consulta encheu", que é o que o `Count` da Tivo não distinguia.
      if (st.veio <= 0 || skip >= st.count) return true;
    }
    LOG("teto de páginas atingido");
    return true;
  }

  async function arrancarReplay() {
    if (loopAtivo || fimReplay || !reqCtx || !corpoBase) return;
    loopAtivo = true;
    try {
      // `result: null` traz abertas + fechadas de uma vez — é a varredura completa.
      const ok = await varrer(null);
      // Se a variante "tudo" falhar (a casa pode passar a exigir o campo), degrada para as
      // duas que a página realmente usa, em vez de voltar vazio.
      if (!ok) { await varrer(2); await varrer(1); }
    } finally {
      loopAtivo = false;
      fimReplay = true;
      enviar();                                             // sinaliza fim p/ o robô parar de esperar
    }
  }

  // O content script pede o acumulado ao iniciar o robô → re-envia tudo E arranca o replay.
  // A 1ª página pode chegar antes de o content estar pronto pra ouvir, por isso re-enviamos.
  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (!d || !d.__sharpenupNVReq) return;
    pedido = true;
    enviar();
    arrancarReplay();
  });

  // ── fetch ──
  if (of && !of.__suNVW) {
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
        // A leitura passiva fica aqui de propósito, embora HOJE ela SEMPRE falhe: o Angular
        // aborta o stream e o clone rejeita com "The user aborted a request.". Custa nada,
        // não polui (a rejeição é engolida) e é o caminho que volta a funcionar sozinho se a
        // casa parar de abortar. Quem entrega o dado é o replay — ver o cabeçalho.
        try {
          if (RX.test(String(url))) r.clone().text().then((t) => forward(url, t)).catch(() => {});
        } catch (e) {}
        return r;
      });
    };
    w.__suNVW = true;
    window.fetch = w;
  }

  // Corpo de uma resposta XHR, respeitando o `responseType`.
  //
  // ⚠ ISTO NÃO É DETALHE. O `HttpClient` do Angular pede `responseType: "json"`, e nesse modo
  // **ler `responseText` LANÇA `InvalidStateError`** — o corpo só existe em `response`, já
  // desserializado. Com o acesso ingênuo dentro de um `try` mudo, o modo passivo morria em
  // silêncio: o inject aprendia a requisição (o `send` roda antes) e o replay entregava tudo,
  // então o lote vinha completo e nada denunciava o defeito. Medido ao vivo: zero heartbeat
  // antes do pedido do robô, com `respostas` contando só as do replay.
  function _corpoResposta(xhr) {
    try {
      const tipo = xhr.responseType;
      if (tipo === "" || tipo === "text") return xhr.responseText;
      if (tipo === "json") return JSON.stringify(xhr.response);
    } catch (e) {}
    return "";
  }

  // ── XMLHttpRequest (rede de segurança) ──
  // Medido: a página usa **fetch**, não XHR — é o wrapper acima que aprende a requisição.
  // Este bloco fica para o caso de a casa trocar de transporte, e porque o `HttpClient` do
  // Angular pode cair em XHR conforme a configuração. O `_corpoResposta` existe por causa
  // dele: em `responseType: "json"` ler `responseText` LANÇA, e o passivo morreria calado.
  const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send,
        osh = XMLHttpRequest.prototype.setRequestHeader;
  if (!os.__suNVW) {
    XMLHttpRequest.prototype.open = function (m, u) { this.__suNVU = u; this.__suNVH = {}; return oo.apply(this, arguments); };
    XMLHttpRequest.prototype.setRequestHeader = function (k, v) { try { this.__suNVH[k] = v; } catch (e) {} return osh.apply(this, arguments); };
    const s = function (body) {
      try {
        if (RX.test(String(this.__suNVU))) {
          const corpo = typeof body === "string" ? body : null;
          capturarReq(this.__suNVU, this.__suNVH, corpo);
          this.addEventListener("load", () => {
            try { forward(this.__suNVU, _corpoResposta(this)); } catch (e) {}
          });
        }
      } catch (e) {}
      return os.apply(this, arguments);
    };
    s.__suNVW = true;
    XMLHttpRequest.prototype.send = s;
  }
})();
