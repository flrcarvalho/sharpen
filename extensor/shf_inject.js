// Mundo MAIN (só na Shuffle): escuta o histórico de apostas esportivas que a página pede e
// BUSCA a lista inteira ele mesmo, repassando ao content script.
//
//   POST shuffle.com/main-api/graphql/sports-main/graphql-sports-main
//        { operationName: "GetSportsBets", query: "… sportsBetsV3(…) …", variables: {…} }
//
// PLATAFORMA PRÓPRIA (recon s401, conta do Feca). A Shuffle não é espelho de ninguém: não há
// iframe de Betby/Altenar/Kambi/BetConstruct na página, o app é Next.js e o sportsbook fala
// GraphQL no MESMO host da casa (`/main-api/graphql/…`). As odds vêm da Betradar
// (`provider: "BETRADAR"` em fixture e mercado), mas isso é o feed, não o motor de apostas.
// Inject próprio, formatador próprio. Primeira casa GraphQL do SharpenUp.
//
// A QUERY NÃO ESCOLHE CAMPOS: `sportsBetsV3(…)` é um escalar JSON e devolve o bilhete inteiro.
// Por isso a query que a página manda serve ao replay sem tradução; quando nenhuma chegou
// ainda, vale a cópia literal abaixo (`QUERY`), medida na página.
//
// AUTH É POR HEADER — medido 3 de 3: a mesma chamada só com cookie volta 200 com
// `errors[0].message = "UNAUTHENTICATED"` (e `data: null`), com `credentials` include, omit
// ou same-origin. O que autentica é `authorization` (Bearer da sessão). `content-type` é
// obrigatório também (sem ele o servidor responde texto, "GraphQL only supports…"), e o
// `x-correlation-id` não (a chamada só com os dois volta a lista inteira, medido).
//
// O TOKEN NÃO É SÓ DA LISTA. A página manda o MESMO `authorization` (hash igual, medido) em
// outras chamadas autenticadas — `sports/graphql-sports` e `api/graphql` (`ActiveTournaments`)
// —, que saem em qualquer tela de esportes. O inject aprende o header de QUALQUER chamada
// autenticada em `/main-api/graphql/`, então a captura arranca sem o operador abrir "Minhas
// Apostas". A chamada SEM token (`GetAppBootstrapData`, `GetGlobalUnauthData`) é ignorada.
//
// O PASSIVO FUNCIONA (o `clone().text()` resolve, medido), mas a TELA É ESTREITA: ela pede
// `first: 9` com um filtro de status por aba (`["PENDING"]` ou os seis liquidados). Quem
// garante cobertura é o replay, que pede a lista SEM `statuses` — medido: sem o filtro a API
// devolve abertas e liquidadas juntas (31 de 31 na conta, 8 + 23, mesmos ids da soma das abas).
//
// PAGINAÇÃO POR CURSOR DE DATA. `nextCursor` é o `createdAt` do 1º bilhete da PRÓXIMA página
// e a página seguinte começa NELE (inclusivo; medido com `first: 2` e `first: 3`: 23 lidos /
// 23 únicos em 8 páginas, sem repetição nem perda). Fim AUTORITATIVO = `nextCursor: null`.
// `first` tem teto **20** (21 já volta `errors: "first must not be greater than 20"`, medido);
// se a casa baixar o teto, o inject lê o número do texto do erro e recua.
//
// ⚠ OUTRA LISTA DE APOSTAS NA MESMA PÁGINA. O rodapé de esportes mostra "Últimas Apostas" e
// "Grandes apostadores" — apostas de OUTROS usuários. O inject só consome resposta cuja
// REQUISIÇÃO foi `GetSportsBets`, e ainda descarta todo bilhete que venha com `user`
// preenchido (nos da própria conta ele é `null`, 31 de 31). Bilhete alheio na conta do
// operador é o pior defeito possível desta casa: não dá erro, dá P/L de outra pessoa.
//
// ARMADILHAS confirmadas no dado real (o inject NÃO decide nada; quem lê é o formatTicketSHF):
//   • TRÊS odds na mesma seleção. `legs[].oddsDecimal` (2.28) é a odd APOSTADA;
//     `selections[].oddsNumerator/Denominator` (128/100) é a mesma em FRACIONÁRIO (soma 1);
//     `marketSelection.oddsNumerator/Denominator` é a odd ATUAL do mercado (70/100 = 1,70 no
//     mesmo bilhete) — ler essa grava uma odd que ninguém apostou. O inject nem a repassa.
//   • `totalOddsDecimal` é a odd da COLOCAÇÃO e não muda com perna anulada; `actualOddsDecimal`
//     e `settlement.payoutOddsDecimal` são a LIQUIDADA. Múltipla de 3 com uma perna PUSHED:
//     total 11.5182, pago 5.1192 (card: "Total de probabilidades 11,52" e "Você ganhou 51,19"
//     sobre 10). O card estampa a da colocação, e só o dinheiro diz a verdade.
//   • SISTEMA (`type: "SYSTEM_BET"`, `systemBetType: "DOUBLES"`): `amount` é o stake TOTAL (60 =
//     3 linhas × 20, card "3 Apostas US$ 20,00 · Sua aposta US$ 60,00") e `totalOddsDecimal`
//     já é a MÉDIA das linhas (2.28·2.34 + 2.28·2.8 + 2.34·2.8 = 18,2712 ÷ 3 = 6,0904, medido).
//   • STATUS `WON` COM PREJUÍZO: sistema que acerta só uma dupla com uma perna PUSHED paga
//     54.996 sobre 60 e a casa chama de "VITÓRIA". O status não diz se houve lucro.
//   • Dinheiro e odd vêm em STRING decimal com ponto ("54.996", "14.93856"); a moeda é da
//     CONTA (`currency: "USDT"`) e o card escreve "US$" (a casa exibe 1 USDT = US$ 1,00).
(function () {
  const RX_GQL = /\/main-api\/graphql\//i;                                // onde o token se aprende
  const RX_LISTA = /\/main-api\/graphql\/sports-main\/graphql-sports-main/i; // a lista de bilhetes
  const OP = "GetSportsBets";
  // A query que a página manda (recon s401), literal. Só é usada enquanto a página não mandou
  // a dela — ao ver a real, o inject passa a usar a real.
  const QUERY = "query GetSportsBets($language: Language, $currencyIn: [Currency!], $statuses: [SportsBetStatus!], $first: Int, $skip: Int, $after: DateTime, $cursor: DateTime) {\n  sportsBets: sportsBetsV3(\n    language: $language\n    currencyIn: $currencyIn\n    statuses: $statuses\n    first: $first\n    skip: $skip\n    after: $after\n    cursor: $cursor\n  )\n}";
  // As duas abas que a página usa. Só entram se a lista sem filtro falhar.
  const ABAS = [["PENDING"], ["WON", "CANCELLED", "LOST", "CASHED_OUT", "VOIDED", "PARTIAL"]];

  const byId = new Map();                      // id(string) → bilhete normalizado
  let respostas = 0;                           // respostas VÁLIDAS da lista (autodiagnóstico)
  let alheios = 0;                             // bilhetes com `user` preenchido, descartados
  let auth = null;                             // valor do header `authorization` (nunca sai daqui)
  let query = null;                            // query real da página, quando vista
  let idioma = "pt";                           // `variables.language` da página
  let urlLista = null;                         // URL real da lista, quando vista
  let pedido = false;                          // o robô já pediu → pode arrancar o replay
  let loopAtivo = false;                       // trava: um replay por vez
  let fimReplay = false;                       // a varredura terminou
  let repetir = false;                         // pedido chegou durante a varredura → roda de novo
  let erro = "";                               // último erro do replay (vai no autodiagnóstico)
  let pagina = 20;                             // `first` — teto medido
  const LOG = (...a) => { try { console.log("[SharpenUp shf_inject]", ...a); } catch (e) {} };
  LOG("hook instalado em", location.href);

  const of = window.fetch;                     // fetch ORIGINAL — o replay usa este
  const TETO_PAGINAS = 500;                    // 500 × 20 = 10 mil bilhetes

  // ── normalização (GraphQL da Shuffle → objeto limpo) ───────────────────────────
  const _n = (v) => {
    if (v == null || v === "") return null;
    const x = Number(v);
    return isFinite(x) ? x : null;
  };
  const _s = (v) => (v == null ? "" : String(v));

  function parseSel(s) {
    if (!s) return null;
    const fx = s.fixture || {}, mk = s.market || {}, ms = s.marketSelection || {};
    return {
      esporte: _s(s.sports),                   // "TENNIS", "SOCCER"… (enum cru)
      liga: _s(s.competition && s.competition.name),
      jogo: _s(fx.name),                       // "Bai, Zhuoxuan vs Jones, Emerson"
      inicio: _s(fx.startTime),                // ISO UTC → o content converte p/ SP
      mercado: _s(mk.name),                    // "Total sets" (pt-PT da casa)
      linha: _s(mk.lineValue),
      selecao: _s(ms.formattedName),           // "Mais de 2.5"
      status: _s(s.displayStatus || s.status), // WON / LOST / PUSHED / PENDING (cru)
      oddSemBoost: _n(s.unboostedOddsDecimal), // só vem com boost (null na amostra inteira)
      aoVivo: !!s.inPlay,
      // ⚠ `marketSelection.odds*` é a odd ATUAL do mercado, não a apostada: fica de fora.
    };
  }

  function parseTicket(t) {
    if (!t || t.id == null) return null;
    const st = t.settlement || null;
    return {
      id: String(t.id),                        // nanoid de 21 — o [Código:] e a chave de dedup
      moeda: _s(t.currency),                   // "USDT" — a moeda da CONTA
      stake: _n(t.amount),                     // TOTAL (em sistema, soma das linhas)
      stakeOriginal: _n(t.originalAmount),     // null na amostra inteira (sobe cru)
      oddColocacao: _n(t.totalOddsDecimal),    // ⚠ não muda com perna anulada; em sistema é a MÉDIA
      oddReal: _n(t.actualOddsDecimal),        // liquidada (= colocação até liquidar)
      status: _s(t.status),                    // PENDING / WON / LOST / … (CRU)
      tipo: _s(t.type),                        // REGULAR / SYSTEM_BET (CRU)
      sistema: _s(t.systemBetType),            // DOUBLES / … (CRU) — null fora de sistema
      colocada: _s(t.createdAt),               // ISO UTC
      liquidada: st ? _s(st.createdAt) : "",
      oddPaga: st ? _n(st.payoutOddsDecimal) : null,
      pagou: st ? _n(st.payout) : null,        // retorno REAL — null = ainda não liquidou
      pernas: (Array.isArray(t.legs) ? t.legs : []).map((l) => ({
        tipo: _s(l && l.type),                 // REGULAR (CRU)
        odd: _n(l && l.oddsDecimal),           // odd APOSTADA da perna
        status: _s(l && l.displayStatus),
        sels: ((l && l.selections) || []).map(parseSel).filter(Boolean),
      })),
    };
  }

  // Emite SEMPRE hook:true + respostas (heartbeat), mesmo com 0 bilhetes. NUNCA leva o token.
  function enviar() {
    try {
      window.postMessage({
        __sharpenupSHFData: true, hook: true,
        bilhetes: Array.from(byId.values()), respostas: respostas, fim: fimReplay,
        semToken: !auth, alheios: alheios, erro: erro,
      }, "*");
    } catch (e) {}
  }

  // A versão LIQUIDADA vence a ABERTA: `settlement` só existe depois de liquidar.
  function guardar(b) {
    const ex = byId.get(b.id);
    if (!ex || (ex.pagou == null && b.pagou != null)) byId.set(b.id, b);
  }

  // Lê uma resposta da lista. Devolve `{n, cursor}` (p/ o replay), `{erro}` ou null.
  function consumir(text) {
    if (typeof text !== "string") return null;
    let j;
    try { j = JSON.parse(text); } catch (e) { return null; }
    const sb = j && j.data && j.data.sportsBets;
    if (!sb || !Array.isArray(sb.nodes)) {
      const msg = j && Array.isArray(j.errors) && j.errors[0] && j.errors[0].message;
      return msg ? { erro: String(msg) } : null;
    }
    respostas++;
    for (const raw of sb.nodes) {
      if (raw && raw.user != null) { alheios++; continue; }   // bilhete de OUTRO usuário
      const b = parseTicket(raw);
      if (b) guardar(b);
    }
    LOG("bilhetes na resposta:", sb.nodes.length, "· total:", byId.size, "· nextCursor:", sb.nextCursor);
    enviar();
    return { n: sb.nodes.length, cursor: sb.nextCursor == null ? null : String(sb.nextCursor) };
  }

  // ── aprendizado ────────────────────────────────────────────────────────────────
  function _hdrsToObj(h) {
    const o = {};
    try {
      if (!h) return o;
      if (typeof h.forEach === "function") h.forEach((v, k) => { o[k] = v; });
      else if (typeof h === "object") for (const k in h) o[k] = h[k];
    } catch (e) {}
    return o;
  }
  function _token(h) {
    for (const k in (h || {})) if (String(k).toLowerCase() === "authorization" && h[k]) return String(h[k]);
    return null;
  }
  function _corpo(c) {
    if (!c || typeof c !== "string") return null;
    try { const o = JSON.parse(c); return (o && typeof o === "object") ? o : null; } catch (e) { return null; }
  }
  const _ehLista = (url, corpo) => RX_LISTA.test(String(url)) && !!corpo && corpo.operationName === OP;

  // Aprende de TODA chamada GraphQL da casa. O token é o mais recente (a sessão pode renovar);
  // a query, o idioma e a URL vêm só da chamada da lista.
  function aprender(url, headers, corpoTxt) {
    if (!RX_GQL.test(String(url))) return;
    const tk = _token(headers);
    if (tk) {
      const primeiro = !auth;
      auth = tk;
      if (primeiro) LOG("token aprendido de", String(url).split("/main-api/graphql/")[1] || url);
    }
    const c = _corpo(corpoTxt);
    if (_ehLista(url, c)) {
      if (typeof c.query === "string" && /sportsBetsV3/.test(c.query)) query = c.query;
      if (c.variables && typeof c.variables.language === "string") idioma = c.variables.language;
      urlLista = String(url);
    }
    if (auth && pedido) arrancarReplay();
  }

  // ── replay ─────────────────────────────────────────────────────────────────────
  function _url() {
    if (urlLista) return urlLista;
    try { return new URL("/main-api/graphql/sports-main/graphql-sports-main", location.href).href; }
    catch (e) { return "/main-api/graphql/sports-main/graphql-sports-main"; }
  }

  async function pedirPagina(statuses, cursor) {
    const variables = { language: idioma, first: pagina, skip: 0 };
    if (statuses) variables.statuses = statuses;
    if (cursor) variables.cursor = cursor;
    const r = await of.call(window, _url(), {
      method: "POST",
      headers: { "content-type": "application/json", "accept": "application/json", "authorization": auth },
      credentials: "include",
      body: JSON.stringify({ operationName: OP, query: query || QUERY, variables: variables }),
    });
    return { ok: !!(r && r.ok), status: r && r.status, text: r ? await r.text() : "" };
  }

  // Varre uma lista inteira (sem filtro, ou uma aba). true = chegou ao fim autoritativo.
  async function varrer(statuses) {
    let cursor = null;
    const vistos = new Set();
    for (let i = 0; i < TETO_PAGINAS; i++) {
      let r;
      try { r = await pedirPagina(statuses, cursor); }
      catch (e) { erro = "replay falhou: " + (e && e.message); LOG(erro); return false; }
      if (!r.ok) { erro = "replay parou · HTTP " + r.status; LOG(erro); return false; }
      const res = consumir(r.text);
      if (!res) { erro = "resposta da lista em formato desconhecido"; LOG(erro); return false; }
      if (res.erro) {
        // A casa baixou o teto do `first`: o número vem escrito no erro. Recua e repete.
        const m = /first must not be greater than (\d+)/i.exec(res.erro);
        if (m && Number(m[1]) > 0 && Number(m[1]) < pagina) { pagina = Number(m[1]); i--; continue; }
        erro = /UNAUTHENTICATED/i.test(res.erro)
          ? "a casa recusou o token (UNAUTHENTICATED) — recarregue a página e rode de novo"
          : "a casa respondeu erro: " + res.erro;
        LOG(erro);
        return false;
      }
      if (res.cursor == null) return true;                     // fim AUTORITATIVO
      // Anti-loop pelo CURSOR, nunca por "página sem bilhete novo": a página já mandou as
      // abas dela (passivo) antes do replay, e uma página inteira já vista é normal aqui.
      if (vistos.has(res.cursor) || res.cursor === cursor) {
        LOG("cursor não avançou — parando"); return true;
      }
      vistos.add(res.cursor);
      cursor = res.cursor;
    }
    LOG("teto de páginas atingido");
    return true;
  }

  async function arrancarReplay() {
    if (loopAtivo || fimReplay || !auth) return;
    loopAtivo = true;
    erro = "";
    try {
      // Sem `statuses` = abertas + liquidadas numa varredura só. Se a casa passar a exigir o
      // filtro, degrada para as duas abas que a própria página usa, em vez de voltar vazio.
      const ok = await varrer(null);
      if (!ok && !/UNAUTHENTICATED/.test(erro)) {
        const antes = erro;
        let todas = true;
        for (const st of ABAS) todas = (await varrer(st)) && todas;
        if (todas) erro = ""; else if (!erro) erro = antes;
      }
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
    if (!d || !d.__sharpenupSHFReq) return;
    pedido = true;
    if (loopAtivo) repetir = true;
    else { fimReplay = false; if (auth) byId.clear(); }
    enviar();
    arrancarReplay();
  });

  // ── fetch ──
  if (of && !of.__suSHFW) {
    const w = function (...a) {
      const req = (a[0] && typeof a[0] === "object" && a[0].url) ? a[0] : null;
      const url = req ? req.url : a[0];
      const opts = a[1] || {};
      let corpoTxt = typeof opts.body === "string" ? opts.body : null;
      try {
        if (RX_GQL.test(String(url))) {
          const hdrs = _hdrsToObj(opts.headers || (req && req.headers));
          aprender(url, hdrs, corpoTxt);
        }
      } catch (e) {}
      return of.apply(this, a).then((r) => {
        try {
          if (_ehLista(url, _corpo(corpoTxt))) {
            // 2º argumento SEMPRE: sem ele um clone abortado vira rejeição muda (s305).
            r.clone().text().then((t) => consumir(t), () => {});
          }
        } catch (e) {}
        return r;
      });
    };
    w.__suSHFW = true;
    window.fetch = w;
  }

  // ── XMLHttpRequest (rede de segurança) ──
  // Medido: a página usa fetch. Fica para o caso de a casa trocar de transporte.
  const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send,
        osh = XMLHttpRequest.prototype.setRequestHeader;
  if (!os.__suSHFW) {
    XMLHttpRequest.prototype.open = function (m, u) { this.__suSHFU = u; this.__suSHFH = {}; return oo.apply(this, arguments); };
    XMLHttpRequest.prototype.setRequestHeader = function (k, v) { try { this.__suSHFH[k] = v; } catch (e) {} return osh.apply(this, arguments); };
    const s = function (body) {
      try {
        if (RX_GQL.test(String(this.__suSHFU))) {
          const corpoTxt = typeof body === "string" ? body : null;
          aprender(this.__suSHFU, this.__suSHFH, corpoTxt);
          if (_ehLista(this.__suSHFU, _corpo(corpoTxt))) {
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
    s.__suSHFW = true;
    XMLHttpRequest.prototype.send = s;
  }
})();
