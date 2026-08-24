// Mundo MAIN (SportingBet — motor bwin/Entain): lê as RESPOSTAS da API de bilhetes
// (`POST https://www.sportingbet.bet.br/pt-br/sports/api/mybets/betslips`) e **PAGINA
// ATIVAMENTE**: a partir de uma requisição real, re-emite o POST avançando `index` até a
// casa devolver lista vazia, nas DUAS abas (`Settled` e `Open`).
//
// POR QUE REPLAY E NÃO PASSIVO (s289): a tela pede `maxItems: 6` por vez e só busca mais
// quando o operador rola. Paginar por API dispensa a rolagem — e aqui isso pesa mais que
// nas outras casas, porque o histórico inteiro sai numa chamada só com `maxItems` alto
// (`CLAUDE.md`: "API externa por item = latência E falha multiplicadas. Peça a FAIXA.").
//
// UMA URL, DUAS ABAS: o discriminador é o `typeFilter` do CORPO (`Settled` · `Open`). O
// estado real vem no PRÓPRIO bilhete (`state`), então não dependemos de saber qual aba
// disparou: `guardar()` aplica "resolvida vence aberta" pelo dado.
//
// ⚠️ AUTENTICAÇÃO NÃO É SÓ COOKIE. O endpoint exige headers próprios do motor
// (`x-xsrf-token`, `x-bwin-sports-api`, `sports-api-version`, `x-from-product`,
// `x-device-type`, `x-bwin-browser-url`). Medido na conta: **um GET no mesmo path devolve
// o HTML da SPA, com HTTP 200** — ou seja, a falha não grita, ela devolve lixo que não
// parseia. Por isso o replay reusa os headers EXATOS da requisição que a página fez, e o
// `forward` exige `betslips` como array antes de aceitar qualquer resposta.
//
// ⚠️ FIM AUTORITATIVO = LISTA VAZIA. Esta casa não manda `isLastPage`, `more` nem
// `hasNext`. Medido: `index:2, maxItems:50` devolveu `betslips: []`. E `index` é a
// **página**, não offset — `index:1,max:5` e `index:2,max:5` trazem 10 ids distintos.
//
// NÃO DECIDE NADA: normaliza a lista e sobe o bilhete cru. Estado desconhecido sobe como
// está; quem traduz é o `content.js` + `casas/CASA_SPORTINGBET.md`.
(function () {
  const RX = /\/mybets\/betslips/i;
  const porId = new Map();                       // betSlipNumber(string) → bilhete cru
  let respostas = 0;                             // respostas do endpoint que o hook viu (autodiagnóstico)
  let reqCtx = null;                             // {url, method, headers, body} de um POST real (p/ replay)
  let pedido = false;                            // o robô já pediu → pode arrancar o replay
  let loopAtivo = false;                         // trava: um replay por vez
  let fimReal = false;                           // as duas abas terminaram (fim AUTORITATIVO)
  const TETO_PAGINAS = 60;                       // anti-loop (60 × 50 = 3000 bilhetes por aba)
  const POR_PAGINA = 50;                         // a tela pede 6; a API aceita 50 e evita 8 chamadas
  const LOG = (...a) => { try { console.log("[SharpenUp spb_inject]", ...a); } catch (e) {} };
  LOG("hook instalado em", location.href);

  const of = window.fetch;                       // fetch ORIGINAL — o replay usa este (não re-dispara o wrapper)

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
  // "não injetei" de "endpoint mudou" de "conta vazia" no autodiagnóstico.
  function enviar() {
    try {
      window.postMessage({
        __sharpenupSPBData: true, hook: true, respostas: respostas,
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
  // devolveria HTML no replay (ver o aviso de autenticação no topo).
  function capturarReq(url, method, headers, body) {
    if (reqCtx || !RX.test(String(url)) || !body) return;
    if (String(method || "").toUpperCase() !== "POST") return;
    reqCtx = { url: String(url), method: "POST", headers: headers || {}, body: _bodyToStr(body) };
    LOG("requisição capturada p/ replay · body:", (reqCtx.body || "").slice(0, 220));
    if (pedido) arrancarReplay();
  }

  // Corpo de uma aba/página, derivado do corpo REAL aprendido (preserva os campos que a
  // casa manda e que não conhecemos). Só sobrescreve aba, página e tamanho.
  function corpoPara(aba, pagina) {
    let o = null;
    try { o = JSON.parse(reqCtx.body); } catch (e) { o = null; }
    if (!o || typeof o !== "object") o = {};
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
        const r = await of.call(window, reqCtx.url, {
          method: "POST", headers: reqCtx.headers,
          body: corpoPara(aba, pagina), credentials: "include",
        });
        info = forward(reqCtx.url, await r.text());
      } catch (e) { LOG("erro no replay", aba, "pág", pagina, ":", e && e.message); return; }
      if (!info) { LOG(aba, "pág", pagina, ": resposta inesperada → para"); return; }
      // ESTE é o fim que a casa declara. Nada de heurística por rolagem.
      if (info.n === 0) { LOG(aba, ": fim (lista vazia) na pág", pagina); return; }
      // "0 bilhete NOVO" não é fim: a página 1 costuma já ter chegado passivamente (a
      // própria tela a pediu ao abrir). Só depois de DUAS páginas seguidas sem novidade a
      // gente assume que a casa está repetindo — o fim de verdade é a lista vazia.
      if (info.novos === 0) {
        if (++semNovos >= 2) { LOG(aba, "pág", pagina, ": 2 páginas seguidas sem bilhete novo → para"); return; }
      } else semNovos = 0;
    }
    LOG(aba, ": teto de", TETO_PAGINAS, "páginas atingido");
  }

  // As DUAS abas a partir de UMA requisição, não importa qual o operador abriu primeiro.
  async function arrancarReplay() {
    if (loopAtivo || fimReal || !reqCtx) return;
    loopAtivo = true;
    try {
      for (const aba of ABAS) await paginarAba(aba);
    } finally {
      loopAtivo = false;
      fimReal = true;            // esgotou as duas abas → o robô pode parar de esperar
      enviar();
    }
  }

  // O content pede o acumulado ao iniciar o robô → re-envia tudo E arranca o replay. A 1ª
  // página chega no load, antes de o content estar ouvindo: sem este re-envio ela se perderia.
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
  if (of && !of.__suSPBW) {
    const w = function (...a) {
      const url = (a[0] && a[0].url) || a[0];
      const opts = a[1] || (a[0] && typeof a[0] === "object" ? a[0] : null);
      try { if (opts && opts.body) capturarReq(url, opts.method, _hdrsToObj(opts.headers), opts.body); } catch (e) {}
      return of.apply(this, a).then((r) => {
        try { if (RX.test(String(url))) r.clone().text().then((t) => forward(url, t)); } catch (e) {}
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
