// Mundo MAIN (plataforma Altenar/BIA — VaideBet, Esportiva, Jogo de Ouro e Betpix365):
// lê as RESPOSTAS da API de bilhetes
// (`POST https://sb2bethistory-gateway-altenar2.biahosted.com/api/WidgetReports/widgetExpandedBetHistory`)
// e **PAGINA ATIVAMENTE**: a partir de uma requisição real, re-emite o POST avançando
// `pageNumber` até `isLastPage:true`, nas DUAS abas.
//
// AS QUATRO CASAS COMPARTILHAM ESTE ARQUIVO. O que separa as marcas é UM campo do corpo
// (`integration`), que vem junto na requisição aprendida — por isso o `RX` casa por PATH e
// nenhum host aparece aqui. Mas "mesmo motor" não garante "mesma superfície":
//   • Jogo de Ouro — serve os DOIS widgets; só a TELA CHEIA dispara o expandido;
//   • Betpix365   — serve SÓ o compacto; o expandido existe e responde, mas ninguém o chama.
// Daí os dois regexes logo abaixo.
//
// POR QUE REPLAY E NÃO PASSIVO (s209): a lista NÃO carrega sozinha — a tela tem um botão
// "Mostrar mais apostas" e o histórico vem de 10 em 10. Paginar por API dispensa o botão
// (na bet365 esse tipo de botão checa `isTrusted` e não é automatizável).
//
// UMA URL, DUAS ABAS: o discriminador é o array `statuses` do CORPO —
//   Processado (resolvidas): [1, 8, 2, 4, 18]      Aberto: [0, 10, 3, 20, 17]
// O estado real, porém, vem no PRÓPRIO bilhete (`status`), então não dependemos de saber
// qual aba disparou: `guardar()` aplica "resolvida vence aberta" pelo dado.
//
// AUTENTICAÇÃO: o endpoint é de OUTRA origem (biahosted.com) e autentica por header
// `Authorization: Bearer <JWT da sessão>`, não por cookie — por isso o replay reusa os
// headers EXATOS da requisição que a página fez. Sem isso volta 401.
//
// NÃO DECIDE NADA: normaliza a lista e sobe o bilhete cru. Status desconhecido sobe como
// está; quem traduz é o `content.js` + `casas/CASA_VAIDEBET.md`.
(function () {
  // ⚠ DOIS regexes, e a separação é o ponto — não é duplicação.
  //
  // `RX` (CONSUMIR) é LOAD-BEARING: só o "Expanded" traz `selections`, e é dele que saem
  // pernas, mercado e data de evento. O `widgetBetHistory` COMPACTO existe de verdade (Jogo
  // de Ouro s256 no painel lateral, Betpix365 s258 na tela inteira) e foi MEDIDO na
  // Betpix365: **nenhum** dos 9 bilhetes tinha `selections`. Consumi-lo geraria bilhete
  // sem descrição, em silêncio. `casos/jogodeouro.mjs` e `casos/betpix365.mjs` travam os
  // dois lados: o corpo do compacto nunca pode virar bilhete.
  //
  // `RX_APRENDE` (APRENDER url+headers) é mais largo, e precisa ser: a **Betpix365 nunca
  // dispara o Expanded**. A tela "Minhas Apostas" dela chama só o compacto, e o detalhe de
  // cada bilhete sai de um `WidgetGetBetDetails` POR ITEM — o anti-padrão do `CLAUDE.md`
  // ("API externa por item = latência E falha multiplicadas. Peça a FAIXA."). O Expanded
  // responde 200 com `selections` para `integration=betpix365`; a casa só não o usa.
  // Então aprendemos a requisição de QUALQUER um dos dois e reescrevemos o path — o
  // compacto entra como MOLDE de url+headers, jamais como dado.
  const RX = /widgetExpandedBetHistory/i;        // CONSUMIR: só o expandido vira bilhete
  const RX_APRENDE = /widget(?:Expanded)?BetHistory/i;   // APRENDER: compacto serve de molde
  // O replay sempre bate no expandido, venha o molde de onde vier.
  const paraExpandido = (u) => String(u).replace(/widgetBetHistory/i, "widgetExpandedBetHistory");
  const porId = new Map();                       // id(string) → bilhete cru
  let respostas = 0;                             // respostas do endpoint que o hook viu (autodiagnóstico)
  let reqCtx = null;                             // {url, method, headers, body} de um POST real (p/ replay)
  let pedido = false;                            // o robô já pediu → pode arrancar o replay
  let loopAtivo = false;                         // trava: um replay por vez
  let fimReal = false;                           // as duas abas terminaram (fim AUTORITATIVO)
  let janelaDias = 45;                           // janela das RESOLVIDAS; o robô sobrescreve
  const TETO_PAGINAS = 60;                       // anti-loop (60 × 10 = 600 bilhetes por aba)
  const LOG = (...a) => { try { console.log("[SharpenUp vb_inject]", ...a); } catch (e) {} };
  LOG("hook instalado em", location.href);

  const of = window.fetch;                       // fetch ORIGINAL — o replay usa este (não re-dispara o wrapper)

  // Os dois arrays de `statuses` que a própria tela envia (colados do Payload real).
  // 0 = aberta · 1 = ganha · 2 = perdida · 8 = ANULADA (os quatro provados contra o card).
  //
  // O `7` NÃO vem da tela: ele foi encontrado medindo a conta (s285, Esportiva/anapetry03 —
  // 250 bilhetes de 2026, um único caso). A casa **não** o inclui em nenhum dos cinco filtros
  // dela (Aberto `[0,10,3,20,17]` · Processado `[1,8,2,4,18]` · Ganho `[1,8]` · Perdida `[2]`
  // · Cashout `[4,18]`), então o bilhete não aparece nem para o operador nem para a captura:
  // some sem erro. Pedimos o 7 de propósito para ele ao menos CHEGAR — o formatador o marca
  // "a conferir" e ninguém liquida por dedução. O gateway aceita o valor extra sem reclamar
  // (medido: `statuses:[7,8]` devolveu os dois).
  //
  // ⚠️ Enum novo aqui NÃO liquida nada sozinho: quem traduz é `_resultadoVB` no content.js,
  // travado pelo harness. Este array decide só o que a casa nos MOSTRA.
  const ST_ABERTAS = [0, 10, 3, 20, 17];
  const ST_RESOLVIDAS = [1, 8, 2, 4, 18, 7];
  const ehAberta = (b) => b && b.status === 0;

  // Resolvida vence aberta: o mesmo bilhete aparece nas duas abas enquanto liquida, e o
  // dado final é o liquidado. Sem isto, a ordem de chegada decidiria o resultado.
  function guardar(b) {
    if (!b || b.id == null) return false;
    const k = String(b.id);
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
        __sharpenupVBData: true, hook: true, respostas: respostas,
        bets: Array.from(porId.values()), fim: fimReal,
      }, "*");
    } catch (e) {}
  }

  // Processa uma resposta (passiva OU do replay). Devolve {isLastPage, n, novos} ou null.
  function forward(url, text) {
    if (!RX.test(String(url)) || typeof text !== "string") return null;
    let j;
    try { j = JSON.parse(text); } catch (e) { return null; }
    if (!j || !Array.isArray(j.bets)) return null;
    respostas++;
    let novos = 0;
    for (const b of j.bets) { if (guardar(b)) novos++; }
    LOG("bilhetes na resposta:", j.bets.length, "· novos:", novos, "· total:", porId.size,
        "· isLastPage:", j.isLastPage);
    enviar();
    return { isLastPage: j.isLastPage === true, n: j.bets.length, novos: novos };
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

  // Guarda o 1º POST real do endpoint COM body → base do replay (url + headers + corpo).
  // Os headers importam mais que o corpo: é onde vive o `Authorization: Bearer`.
  //
  // A URL é normalizada para o EXPANDIDO na hora de guardar: na Betpix365 o único POST que
  // a página faz é o do compacto, e é dele que herdamos `Authorization`, `integration`,
  // `culture`, `pageSize` etc. Reescrever aqui (e não no laço) garante que existe UM só
  // lugar onde o path é decidido.
  function capturarReq(url, method, headers, body) {
    if (reqCtx || !RX_APRENDE.test(String(url)) || !body) return;
    reqCtx = { url: paraExpandido(url), method: (method || "POST"), headers: headers || {}, body: _bodyToStr(body) };
    LOG("requisição capturada p/ replay · body:", (reqCtx.body || "").slice(0, 220));
    if (pedido) arrancarReplay();
  }

  const _iso = (ts) => new Date(ts).toISOString();

  // Corpo de uma aba/página, derivado do corpo REAL aprendido (preserva culture, integration,
  // timezoneOffset, numFormat, deviceType…). Só sobrescreve statuses/pageNumber/datas.
  //
  // JANELA: as RESOLVIDAS respeitam os dias pedidos pelo robô. As ABERTAS levam janela larga
  // de propósito — uma aposta colocada há meses pode ter jogo amanhã, e cortá-la pelo filtro
  // do servidor a faria sumir do lote (o corte por dias no content preserva aberta pelo mesmo
  // motivo).
  function corpoPara(abertas, pagina) {
    let o = null;
    try { o = JSON.parse(reqCtx.body); } catch (e) { o = null; }
    if (!o || typeof o !== "object") o = {};
    const agora = Date.now();
    const dias = abertas ? 730 : Math.max(1, janelaDias);
    o.statuses = abertas ? ST_ABERTAS.slice() : ST_RESOLVIDAS.slice();
    o.pageNumber = pagina;
    if (typeof o.pageSize !== "number" || o.pageSize < 1) o.pageSize = 10;
    o.dateFrom = _iso(agora - dias * 86400000);
    o.dateTo = _iso(agora + 86400000);          // +1 dia: pega o que foi colocado hoje
    return JSON.stringify(o);
  }

  // Pagina UMA aba até o fim autoritativo (`isLastPage:true`). Nunca desiste no 1º obstáculo:
  // só para por fim declarado, página sem bilhete novo (anti-loop) ou teto.
  async function paginarAba(abertas) {
    const rotulo = abertas ? "ABERTAS" : "RESOLVIDAS";
    let semNovos = 0;
    for (let pagina = 1; pagina <= TETO_PAGINAS; pagina++) {
      let info = null;
      try {
        const r = await of.call(window, reqCtx.url, {
          method: reqCtx.method, headers: reqCtx.headers,
          body: corpoPara(abertas, pagina), credentials: "include",
        });
        info = forward(reqCtx.url, await r.text());
      } catch (e) { LOG("erro no replay", rotulo, "pág", pagina, ":", e && e.message); return; }
      if (!info) { LOG(rotulo, "pág", pagina, ": resposta inesperada → para"); return; }
      if (info.isLastPage) { LOG(rotulo, ": fim autoritativo na pág", pagina); return; }
      if (info.n === 0) { LOG(rotulo, "pág", pagina, ": página vazia → para"); return; }
      // "0 bilhete NOVO" não é fim: a página 1 costuma já ter chegado passivamente (a própria
      // tela a pediu ao abrir), e cortar aqui deixava o lote nos 10 primeiros. Só depois de
      // DUAS páginas seguidas sem novidade a gente assume que a casa está repetindo a mesma
      // página e sai — o fim de verdade é o `isLastPage`, e o teto é a rede de segurança.
      if (info.novos === 0) {
        if (++semNovos >= 2) { LOG(rotulo, "pág", pagina, ": 2 páginas seguidas sem bilhete novo → para"); return; }
      } else semNovos = 0;
    }
    LOG(rotulo, ": teto de", TETO_PAGINAS, "páginas atingido");
  }

  // As DUAS abas a partir de UMA requisição, não importa qual o operador abriu primeiro.
  async function arrancarReplay() {
    if (loopAtivo || fimReal || !reqCtx) return;
    loopAtivo = true;
    try {
      await paginarAba(false);   // Processado (resolvidas)
      await paginarAba(true);    // Aberto
    } finally {
      loopAtivo = false;
      fimReal = true;            // esgotou as duas abas → o robô pode parar de esperar
      enviar();
    }
  }

  // O content pede o acumulado ao iniciar o robô (com a janela de dias) → re-envia tudo E
  // arranca o replay. A 1ª página chega no load, antes de o content estar ouvindo: sem este
  // re-envio ela se perderia.
  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (!d || !d.__sharpenupVBReq) return;
    if (typeof d.dias === "number" && d.dias > 0) janelaDias = d.dias;
    pedido = true;
    enviar();
    arrancarReplay();
  });

  // ── fetch ──
  if (of && !of.__suVBW) {
    const w = function (...a) {
      const url = (a[0] && a[0].url) || a[0];
      const opts = a[1] || (a[0] && typeof a[0] === "object" ? a[0] : null);
      try { if (opts && opts.body) capturarReq(url, opts.method, _hdrsToObj(opts.headers), opts.body); } catch (e) {}
      return of.apply(this, a).then((r) => {
        try { if (RX.test(String(url))) r.clone().text().then((t) => forward(url, t)); } catch (e) {}
        return r;
      });
    };
    w.__suVBW = true;
    window.fetch = w;
  }

  // ── XMLHttpRequest ──
  const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send, osh = XMLHttpRequest.prototype.setRequestHeader;
  if (!os.__suVBW) {
    XMLHttpRequest.prototype.open = function (m, u) { this.__suVBU = u; this.__suVBM = m; this.__suVBH = { "Content-Type": "application/json" }; return oo.apply(this, arguments); };
    XMLHttpRequest.prototype.setRequestHeader = function (k, v) { try { this.__suVBH[k] = v; } catch (e) {} return osh.apply(this, arguments); };
    const s = function (body) {
      try {
        // Gate largo (aprende do compacto também). O `forward` se protege sozinho: ele
        // rejeita pelo `RX` estreito, então o corpo do compacto não vira bilhete nem aqui.
        if (RX_APRENDE.test(String(this.__suVBU))) {
          if (body) capturarReq(this.__suVBU, this.__suVBM, this.__suVBH, body);
          this.addEventListener("load", () => { try { forward(this.__suVBU, this.responseText); } catch (e) {} });
        }
      } catch (e) {}
      return os.apply(this, arguments);
    };
    s.__suVBW = true;
    XMLHttpRequest.prototype.send = s;
  }
})();
