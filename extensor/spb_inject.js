// Mundo MAIN (SportingBet — motor bwin/Entain): PAGINA ATIVAMENTE a API de bilhetes
// (`POST https://www.sportingbet.bet.br/pt-br/sports/api/mybets/betslips`), avançando
// `index` até a casa devolver lista vazia, nas DUAS abas (`Settled` e `Open`).
//
// ⚠️ ARRANQUE A FRIO (s305) — ESTE INJECT NÃO ESPERA VER REQUISIÇÃO NENHUMA.
// Até a 0.7.4 o replay só arrancava depois de aprender uma requisição real da página
// (`reqCtx`). Medido ao vivo na conta do Feca em 31/08, com dois testers travados em
// "0 bilhetes":
//
//   • ABRIR A PÁGINA DE MINHAS APOSTAS NÃO FAZ REQUISIÇÃO. Carga direta (ou F5) de
//     `/pt-br/sports/minhas-apostas/liquidada` renderiza a lista inteira pelo SERVIDOR:
//     **zero** chamadas a `betslips`. O POST só sai na PRIMEIRA vez que cada aba é aberta
//     dentro daquela carga — reabrir a mesma aba não dispara nada, a SPA já tem o dado.
//     Ou seja: quem dá F5 e roda o robô nunca gerou requisição, e o replay antigo voltava
//     na primeira linha (`if (!reqCtx) return`) — hook ATIVO, respostas 0, vistos 0.
//   • E A LEITURA PASSIVA É IMPOSSÍVEL AQUI. A SPA dispara o `fetch` com `AbortSignal` e
//     ABORTA assim que termina de consumir a resposta, o que mata o stream do clone:
//     `r.clone().text()` **rejeita** com `AbortError: The user aborted a request` (medido
//     2 de 2, status 200 nas duas). Sem handler de rejeição isso morria em silêncio.
//
// Por isso o replay hoje monta a requisição SOZINHO, com os cabeçalhos do motor como
// constantes + os cookies da sessão. Provado na conta: `Settled` p1 = 33 bilhetes, p2 = 0;
// `Open` p1 = 4, p2 = 0 — sem aprender nada da página.
//
// ⚠️ AUTENTICAÇÃO NÃO É SÓ COOKIE, e a falha NÃO GRITA. Sem os cabeçalhos do motor o
// servidor devolve **200 com o HTML da SPA** (medido: 135 KB de HTML). Por isso o
// `forward` exige `betslips` como array antes de aceitar qualquer resposta, e por isso
// `HEADERS_MOTOR` não é enfeite. Medido um a um: sem eles → HTML; com eles → JSON. O
// `X-XSRF-TOKEN` é o único dispensável (mandei vazio e passou; nem existe cookie de XSRF
// na sessão), então ele não entra nas constantes.
//
// A requisição real, quando aparece, continua sendo APRENDIDA — ela traz campos que a
// gente não conhece (`openEventIds`, `liveEventIds`, `summaryBetNumbers`) e que preferimos
// preservar. Mas ela virou melhoria, não pré-requisito.
//
// UMA URL, DUAS ABAS: o discriminador é o `typeFilter` do CORPO (`Settled` · `Open`). O
// estado real vem no PRÓPRIO bilhete (`state`), então não dependemos de saber qual aba
// disparou: `guardar()` aplica "resolvida vence aberta" pelo dado.
//
// ⚠️ FIM AUTORITATIVO = LISTA VAZIA. Esta casa não manda `isLastPage`, `more` nem
// `hasNext`. Medido: `index:2, maxItems:50` devolveu `betslips: []`. E `index` é a
// **página**, não offset — `index:1,max:5` e `index:2,max:5` trazem 10 ids distintos.
//
// NÃO DECIDE NADA: normaliza a lista e sobe o bilhete cru. Estado desconhecido sobe como
// está; quem traduz é o `content.js` + `casas/CASA_SPORTINGBET.md`.
(function () {
  const RX = /\/mybets\/betslips/i;
  const PATH_API = "/pt-br/sports/api/mybets/betslips";
  const porId = new Map();                       // betSlipNumber(string) → bilhete cru
  let respostas = 0;                             // respostas do endpoint que o hook viu (autodiagnóstico)
  let abortos = 0;                               // leituras passivas mortas pelo AbortSignal da SPA
  let reqCtx = null;                             // {url, method, headers, body} de um POST real (p/ replay)
  let pedido = false;                            // o robô já pediu → pode arrancar o replay
  let loopAtivo = false;                         // trava: um replay por vez
  let fimReal = false;                           // as duas abas terminaram (fim AUTORITATIVO)
  const TETO_PAGINAS = 60;                       // anti-loop (60 × 50 = 3000 bilhetes por aba)
  const POR_PAGINA = 50;                         // a tela pede 6; a API aceita 50 e evita 8 chamadas
  const LOG = (...a) => { try { console.log("[SharpenUp spb_inject]", ...a); } catch (e) {} };
  LOG("hook instalado em", location.href);

  const of = window.fetch;                       // fetch ORIGINAL — o replay usa este (não re-dispara o wrapper)

  // Cabeçalhos do motor bwin/Entain, medidos na requisição real da casa (31/08). São o que
  // separa JSON de "200 com o HTML da SPA" — ver o aviso de autenticação no topo.
  const HEADERS_MOTOR = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/plain, */*",
    "cache-control": "no-cache",
    "x-bwin-sports-api": "prod",
    "Sports-Api-Version": "SportsAPIv2",
    "X-Device-Type": "desktop",
    "X-From-Product": "host-app",
  };

  // As duas abas, como a própria tela as nomeia no corpo.
  const ABAS = ["Settled", "Open"];
  const ehAberta = (b) => b && b.state === "Open";

  // Resolvida vence aberta: o mesmo bilhete aparece nas duas abas enquanto liquida, e o
  // dado final é o liquidado. Sem isto, a ordem de chegada decidiria o resultado.
  function guardar(b) {
    if (!b || b.betSlipNumber == null) return false;
    const k = String(b.betSlipNumber);
    const ex = porId.get(k);
    if (ex && !ehAberta(ex) && ehAberta(b)) return false;   // não rebaixa resolvida → aberta
    porId.set(k, b);
    return !ex;
  }

  // Emite SEMPRE hook:true + respostas (heartbeat), mesmo com 0 bilhetes — é o que separa
  // "não injetei" de "endpoint mudou" de "conta vazia" no autodiagnóstico. `abortos` conta
  // as leituras passivas que o AbortSignal da casa matou: elas são NORMAIS aqui e não
  // significam falha (o replay é a fonte), mas sem o número ninguém saberia disso.
  function enviar() {
    try {
      window.postMessage({
        __sharpenupSPBData: true, hook: true, respostas: respostas, abortos: abortos,
        bets: Array.from(porId.values()), fim: fimReal,
      }, "*");
    } catch (e) {}
  }

  // Processa uma resposta (passiva OU do replay). Devolve {n, novos} ou null.
  //
  // O guarda de `Array.isArray(j.betslips)` é load-bearing nesta casa: sem os headers do
  // motor o servidor responde **200 com o HTML da SPA**, e sem esta checagem o `respostas`
  // subiria contando lixo — o autodiagnóstico diria "endpoint respondendo" com zero bilhete.
  function forward(url, text) {
    if (!RX.test(String(url)) || typeof text !== "string") return null;
    let j;
    try { j = JSON.parse(text); } catch (e) { return null; }
    if (!j || !Array.isArray(j.betslips)) return null;
    respostas++;
    let novos = 0;
    for (const b of j.betslips) { if (guardar(b)) novos++; }
    LOG("bilhetes na resposta:", j.betslips.length, "· novos:", novos, "· total:", porId.size,
        "· aba:", j.typeFilter);
    enviar();
    return { n: j.betslips.length, novos: novos };
  }

  // ── replay ativo ──────────────────────────────────────────────────────────────
  function _bodyToStr(b) {
    try {
      if (typeof b === "string") return b;
      if (b instanceof URLSearchParams) return b.toString();
      return String(b);
    } catch (e) { return ""; }
  }
  function _hdrsToObj(h) {
    const o = {};
    try {
      if (!h) return o;
      if (typeof h.forEach === "function") h.forEach((v, k) => { o[k] = v; });
      else if (typeof h === "object") for (const k in h) o[k] = h[k];
    } catch (e) {}
    return o;
  }

  // Guarda a 1ª requisição REAL com corpo. Só POST serve de molde — um GET aprendido
  // devolveria HTML no replay (ver o aviso de autenticação no topo). Isto é MELHORIA, não
  // pré-requisito: sem ela o replay usa as constantes (ver `headersDoReplay`/`baseDoCorpo`).
  function capturarReq(url, method, headers, body) {
    if (reqCtx || !RX.test(String(url)) || !body) return;
    if (String(method || "").toUpperCase() !== "POST") return;
    reqCtx = { url: String(url), method: "POST", headers: headers || {}, body: _bodyToStr(body) };
    LOG("requisição capturada p/ replay · body:", (reqCtx.body || "").slice(0, 220));
    if (pedido) arrancarReplay();
  }

  function urlDoReplay() {
    return (reqCtx && reqCtx.url) || (location.origin + PATH_API);
  }

  // Só aceita os cabeçalhos aprendidos se eles trouxerem o do motor. Um molde aprendido
  // incompleto (ex.: a página chamando `fetch(new Request(...))`, onde headers/corpo não
  // vêm no 2º argumento) levaria o replay direto para o HTML da SPA — e o sintoma seria
  // "respostas 0" de novo, agora sem causa visível.
  function headersDoReplay() {
    if (reqCtx && reqCtx.headers) {
      for (const k in reqCtx.headers) {
        if (String(k).toLowerCase() === "x-bwin-sports-api") return reqCtx.headers;
      }
    }
    const h = {};
    for (const k in HEADERS_MOTOR) h[k] = HEADERS_MOTOR[k];
    h["x-bwin-browser-url"] = location.href;
    return h;
  }

  // Corpo REAL aprendido, quando houver (preserva campos que não conhecemos:
  // `openEventIds`, `liveEventIds`, `summaryBetNumbers`). Sem ele, objeto vazio — os
  // campos que importam são escritos por `corpoPara`.
  function baseDoCorpo() {
    if (reqCtx) {
      try { const o = JSON.parse(reqCtx.body); if (o && typeof o === "object") return o; } catch (e) {}
    }
    return {};
  }

  // Corpo de uma aba/página. Só sobrescreve aba, página e tamanho.
  function corpoPara(aba, pagina) {
    const o = baseDoCorpo();
    o.typeFilter = aba;
    o.index = pagina;
    o.maxItems = POR_PAGINA;
    // Estes três a tela manda variar conforme o que está na tela; no replay queremos o
    // histórico inteiro, sem recorte por evento.
    if (!Array.isArray(o.eventIds)) o.eventIds = [];
    o.useGroupedView = false;
    return JSON.stringify(o);
  }

  // Pagina UMA aba até o fim autoritativo (lista vazia). Nunca desiste no 1º obstáculo:
  // só para por lista vazia, duas páginas sem novidade (anti-loop) ou teto.
  async function paginarAba(aba) {
    let semNovos = 0;
    for (let pagina = 1; pagina <= TETO_PAGINAS; pagina++) {
      let info = null;
      try {
        const r = await of.call(window, urlDoReplay(), {
          method: "POST", headers: headersDoReplay(),
          body: corpoPara(aba, pagina), credentials: "include",
        });
        info = forward(urlDoReplay(), await r.text());
      } catch (e) { LOG("erro no replay", aba, "pág", pagina, ":", e && e.message); return; }
      if (!info) { LOG(aba, "pág", pagina, ": resposta inesperada → para"); return; }
      // ESTE é o fim que a casa declara. Nada de heurística por rolagem.
      if (info.n === 0) { LOG(aba, ": fim (lista vazia) na pág", pagina); return; }
      // "0 bilhete NOVO" não é fim: a página 1 pode já ter chegado por outra aba. Só depois
      // de DUAS páginas seguidas sem novidade a gente assume que a casa está repetindo — o
      // fim de verdade é a lista vazia.
      if (info.novos === 0) {
        if (++semNovos >= 2) { LOG(aba, "pág", pagina, ": 2 páginas seguidas sem bilhete novo → para"); return; }
      } else semNovos = 0;
    }
    LOG(aba, ": teto de", TETO_PAGINAS, "páginas atingido");
  }

  // As DUAS abas a partir de UMA chamada, tenha a página feito requisição ou não.
  async function arrancarReplay() {
    if (loopAtivo || fimReal) return;
    loopAtivo = true;
    LOG("replay arrancando ·", reqCtx ? "com requisição aprendida" : "A FRIO (sem requisição da página)");
    try {
      for (const aba of ABAS) await paginarAba(aba);
    } finally {
      loopAtivo = false;
      fimReal = true;            // esgotou as duas abas → o robô pode parar de esperar
      enviar();
    }
  }

  // O content pede o acumulado ao iniciar o robô → re-envia tudo E arranca o replay.
  //
  // Não há janela de dias aqui: o corpo desta casa **não tem filtro de data** (a tela filtra
  // por outro caminho). O corte por dias é do content, como já acontece com as abertas das
  // outras casas.
  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (!d || !d.__sharpenupSPBReq) return;
    pedido = true;
    enviar();
    arrancarReplay();
  });

  // ── fetch ──
  //
  // A leitura passiva daqui quase sempre REJEITA (o `AbortSignal` da SPA mata o clone) —
  // ver o bloco do topo. O handler de rejeição existe para isso virar contador, não silêncio:
  // sem ele a promise morria como unhandled rejection e ninguém sabia por que `respostas`
  // ficava em 0. Quando ela funciona, é bônus: a fonte desta casa é o replay.
  if (of && !of.__suSPBW) {
    const w = function (...a) {
      const url = (a[0] && a[0].url) || a[0];
      const opts = a[1] || (a[0] && typeof a[0] === "object" ? a[0] : null);
      try { if (opts && opts.body) capturarReq(url, opts.method, _hdrsToObj(opts.headers), opts.body); } catch (e) {}
      return of.apply(this, a).then((r) => {
        try {
          if (RX.test(String(url))) {
            r.clone().text().then(
              (t) => forward(url, t),
              (e) => { abortos++; LOG("leitura passiva abortada pela casa (normal aqui):", e && e.message); }
            );
          }
        } catch (e) {}
        return r;
      });
    };
    w.__suSPBW = true;
    window.fetch = w;
  }

  // ── XMLHttpRequest ──
  const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send, osh = XMLHttpRequest.prototype.setRequestHeader;
  if (!os.__suSPBW) {
    XMLHttpRequest.prototype.open = function (m, u) { this.__suSPBU = u; this.__suSPBM = m; this.__suSPBH = { "Content-Type": "application/json" }; return oo.apply(this, arguments); };
    XMLHttpRequest.prototype.setRequestHeader = function (k, v) { try { this.__suSPBH[k] = v; } catch (e) {} return osh.apply(this, arguments); };
    const s = function (body) {
      try {
        if (RX.test(String(this.__suSPBU))) {
          if (body) capturarReq(this.__suSPBU, this.__suSPBM, this.__suSPBH, body);
          this.addEventListener("load", () => { try { forward(this.__suSPBU, this.responseText); } catch (e) {} });
        }
      } catch (e) {}
      return os.apply(this, arguments);
    };
    s.__suSPBW = true;
    XMLHttpRequest.prototype.send = s;
  }
})();
