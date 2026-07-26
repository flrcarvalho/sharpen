// Mundo MAIN (Betfair): lê as RESPOSTAS da API de bilhetes resolvidos
// (POST /activity/sportsbook — JSON com `bets[]`) que a própria página baixa E **PAGINA
// ATIVAMENTE**: a partir da 1ª resposta, o próprio inject re-emite a requisição avançando
// a página (nextPageIndex), com os cookies da sessão, até `moreAvailable:false`. Assim NÃO
// depende do scroll/botão da página (que se mostrou não confiável — lista curta não rola).
//
// Casamento por FORMA do JSON (não por URL exata — o `open` recebe URL relativa): só aceita
// respostas com `bets[]` e `responseFilters.status === "SETTLED"` (a lista RESOLVIDA; a aba
// "Aberta" também chama o endpoint, com poucas apostas e moreAvailable:false → zerava tudo).
//
// Reporta pro content script na própria janela E na do TOPO (a lista pode rodar em iframe).
// hook:true = injeção OK · respostas>0 = viu a API · bets>0 = leu os bilhetes (autodiagnóstico).
(function () {
  const RX = /sportsbook/i;
  const all = [];
  const seen = new Set();
  const abertas = [];              // lista ABERTA (status=OPEN) — balde SEPARADO, ver `forward`
  const seenAb = new Set();
  let reqOpen = null;              // requisição da aba ABERTA   (status:OPEN)
  let reqSettled = null;           // requisição da aba RESOLVIDA (status:SETTLED)
  let buscandoAbertas = false;
  // Campos de ÍNDICE de página. `pageSize`/`limit` ficam de fora de propósito: o replay
  // trocava qualquer número igual ao `rangeStart`, e na 2ª página `pageSize:10` == `rangeStart:10`
  // → o tamanho da página era sobrescrito pelo índice seguinte.
  const _IDX_RE = /^(fromrecord|rangestart|startindex|startrecord|pageindex|index|offset|from|page)$/i;
  let fimReal = false;
  let respostas = 0;
  // (o antigo `reqCtx` — "1ª requisição com body" — saiu: era ele que prendia o replay na
  //  aba Aberta. Agora cada aba tem o seu contexto, ver `capturarReq`/`reqDe`.)
  let loopAtivo = false;    // trava: só um loop de paginação ativa por vez
  let replays = 0;
  let ultimoNext = null;    // nextPageIndex da última resposta vista (p/ retomar a paginação)
  let ultimoStart = 0;      // rangeStart da última resposta vista
  let limite = 0;           // teto de bilhetes pedido pelo robô (0 = sem limite / varrer tudo)
  let pedido = false;       // o robô já pediu a coleta → pode arrancar a paginação ativa
  const LOG = (...a) => { try { console.log("[SharpenUp bf_inject]", ...a); } catch (e) {} };
  LOG("hook instalado em", location.href, "· frame top?", window.top === window);

  const of = window.fetch;  // fetch ORIGINAL — o replay usa este p/ não re-disparar o wrapper.

  function enviar() {
    const msg = { __sharpenupBFData: true, hook: true, bets: all, abertas: abertas,
                  fim: fimReal, paginando: loopAtivo, respostas: respostas };
    try { window.postMessage(msg, "*"); } catch (e) {}
    try { if (window.top && window.top !== window) window.top.postMessage(msg, "*"); } catch (e) {}
  }

  function _bodyToStr(b) {
    try {
      if (typeof b === "string") return b;
      if (b instanceof URLSearchParams) return b.toString();
      return JSON.stringify(b);
    } catch (e) { return ""; }
  }
  function _hdrsToObj(h) {
    const o = { "Content-Type": "application/json" };
    try {
      if (!h) return o;
      if (typeof h.forEach === "function") h.forEach((v, k) => { o[k] = v; });   // Headers
      else if (typeof h === "object") for (const k in h) o[k] = h[k];
    } catch (e) {}
    return o;
  }

  // Guarda a requisição de CADA ABA separadamente, pelo `"status"` do próprio corpo.
  //
  // POR QUE ISTO É ASSIM (s199): antes guardava-se só a PRIMEIRA requisição com body, e a
  // página abre na aba "Aberta" → o contexto do replay ficava preso em `"status":"OPEN"`. O
  // `paginarLoop` então repaginava a lista ERRADA, o `forward` recusava a resposta (não é
  // SETTLED), o laço morria na 1ª volta — e o `finally` marcava `fimReal = true`. No
  // `content.js` o laço de rolagem é `while (… && !bfFimReal)`, ou seja **o robô nunca
  // chegava a rolar**: trazia só o que já estava carregado na tela (o Feca pediu 100 e
  // recebeu 22). A paginação ativa da Betfair nunca funcionou de fato.
  function capturarReq(url, method, headers, body) {
    if (!RX.test(String(url)) || !body) return;
    const s = _bodyToStr(body);
    const ctx = { url: String(url), method: (method || "POST"), headers: headers, body: s };
    if (/"status"\s*:\s*"OPEN"/i.test(s)) {
      if (!reqOpen) { reqOpen = ctx; LOG("requisição da aba ABERTA capturada"); }
    } else if (/"status"\s*:\s*"SETTLED"/i.test(s)) {
      if (!reqSettled) { reqSettled = ctx; LOG("requisição da aba RESOLVIDA capturada"); }
    }
  }

  // Corpo da requisição de uma aba, DERIVADO da outra quando a página não a disparou.
  // O operador costuma capturar de uma aba só; sem isto, a outra lista simplesmente não vem
  // (foi o que aconteceu: na aba Aberta vieram 2 bilhetes e nenhuma encerrada; na Resolvida,
  // 22 encerradas e nenhuma aberta). Troca o `status`, zera o índice e ajusta o `dateFilter`
  // para o valor que a própria casa usa em cada aba (0 na Aberta, 90 na Resolvida).
  function _corpoPara(base, status) {
    let o = null;
    try { o = JSON.parse(base); } catch (e) { return null; }
    if (!o || typeof o !== "object") return null;
    for (const k of Object.keys(o)) {
      if (/^status$/i.test(k)) o[k] = status;
      else if (/^datefilter$/i.test(k)) o[k] = (status === "OPEN") ? 0 : "90";
      else if (_IDX_RE.test(k) && typeof o[k] === "number") o[k] = 0;
    }
    return JSON.stringify(o);
  }

  // Contexto da aba pedida: o REAL capturado tem preferência; derivar é só rede de segurança.
  function reqDe(status) {
    const proprio = (status === "OPEN") ? reqOpen : reqSettled;
    if (proprio) return proprio;
    const outro = (status === "OPEN") ? reqSettled : reqOpen;
    if (!outro) return null;
    const corpo = _corpoPara(outro.body, status);
    if (!corpo) return null;
    LOG("contexto de", status, "derivado da outra aba");
    return { url: outro.url, method: outro.method, headers: outro.headers, body: corpo };
  }

  // Processa uma resposta de bilhetes (passiva OU do replay). Retorna {more,next,start} ou null.
  function forward(url, text) {
    if (!RX.test(String(url)) || typeof text !== "string") return null;
    let j;
    try { j = JSON.parse(text); } catch (e) { return null; }
    if (!j || !Array.isArray(j.bets)) return null;
    const status = String((j.responseFilters && j.responseFilters.status) || "").toUpperCase();
    // Lista ABERTA: a página já dispara esta requisição sozinha ao carregar e, até a s197, a
    // resposta era simplesmente DESCARTADA (por isso nunca capturamos aposta em aberto).
    // Agora ela vai para um balde SEPARADO e a função devolve `null` exatamente como antes:
    // `respostas`, `all`, `fimReal`, `ultimoNext` e o `paginarLoop` só são alimentados pela
    // lista SETTLED, então a captura das ENCERRADAS fica byte a byte igual. Aditivo puro.
    if (status === "OPEN") {
      let novos = 0;
      for (const t of j.bets) {
        const c = t && t.betId;
        if (c && !seenAb.has(c)) { seenAb.add(c); abertas.push(t); novos++; }
      }
      LOG("abertas:", j.bets.length, "· total:", abertas.length);
      if (novos) enviar();
      return null;
    }
    if (status && status !== "SETTLED") return null;   // qualquer outra aba: ignora
    respostas++;
    const antes = all.length;
    for (const t of j.bets) {
      const c = t && t.betId;
      if (c && !seen.has(c)) { seen.add(c); all.push(t); }
    }
    LOG("bilhetes:", j.bets.length, "· total:", all.length, "· moreAvailable:", j.moreAvailable);
    const start = (typeof j.rangeStart === "number" ? j.rangeStart : 0);
    ultimoNext = j.nextPageIndex; ultimoStart = start;   // p/ retomar quando o robô pedir
    if (j.moreAvailable === false) fimReal = true;
    enviar();
    // Se o robô já pediu (e a resposta chegou depois), arranca a paginação ativa agora.
    if (pedido && !loopAtivo && !fimReal && ultimoNext != null) paginarLoop(ultimoNext, ultimoStart);
    return { more: j.moreAvailable, next: j.nextPageIndex, start: start, antes: antes };
  }

  // Monta o body da próxima página: troca o campo de ÍNDICE por nextIndex. Só mexe em chave
  // com NOME de índice (`_IDX_RE`) ou cujo valor bate com o `rangeStart` atual E não é um
  // campo de tamanho — na 2ª página `pageSize:10` == `rangeStart:10` e o tamanho da página
  // era sobrescrito pelo índice seguinte.
  function bodyProxPagina(base, nextIndex, rangeStart) {
    let obj = null;
    try { obj = JSON.parse(base); } catch (e) {}
    if (!obj || typeof obj !== "object") return base;
    for (const k of Object.keys(obj)) {
      if (typeof obj[k] !== "number") continue;
      if (_IDX_RE.test(k)) obj[k] = nextIndex;
      else if (obj[k] === rangeStart && !/size|limit|count|length/i.test(k)) obj[k] = nextIndex;
    }
    return JSON.stringify(obj);
  }

  async function paginarLoop(nextIndex, rangeStart) {
    if (loopAtivo) return;
    const ctxS = reqDe("SETTLED");
    if (!ctxS) { LOG("sem contexto da aba RESOLVIDA → não pagina (robô cai na rolagem)"); return; }
    loopAtivo = true;
    let idx = nextIndex, start = rangeStart;
    try {
      while (!fimReal && idx != null && replays < 400) {
        if (limite && all.length >= limite) break;   // atingiu o teto pedido pelo robô
        replays++;
        const antes = all.length;
        let info;
        try {
          const r = await of.call(window, ctxS.url, {
            method: ctxS.method, headers: ctxS.headers,
            body: bodyProxPagina(ctxS.body, idx, start), credentials: "include",
          });
          info = forward(ctxS.url, await r.text());
        } catch (e) { LOG("erro no replay:", e && e.message); break; }
        if (!info) break;                                  // resposta inesperada → para
        if (all.length === antes) { LOG("replay sem bilhete novo → fim"); break; }  // não avançou
        if (info.more === false || info.next == null || info.next === idx) break;   // fim/estagnou
        start = info.start; idx = info.next;
      }
    } finally {
      loopAtivo = false;
      fimReal = true;   // esgotou a paginação ativa → sinaliza fim p/ o robô parar de esperar
      enviar();
    }
  }

  // O content script pede o estado ao iniciar o robô (com o teto de bilhetes) → responde
  // SEMPRE (reporta hook vivo) e ARRANCA a paginação ativa até o limite. Paginar só sob
  // demanda (não no load da página) respeita o teto e não puxa o histórico inteiro à toa.
  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (!d || !d.__sharpenupBFReq) return;
    if (typeof d.limite === "number") limite = d.limite;
    pedido = true;
    enviar();
    if (!loopAtivo && !fimReal && ultimoNext != null) paginarLoop(ultimoNext, ultimoStart);
    buscarAbertas();
    buscarEncerradas();
  });

  // Se o operador capturou a partir da aba ABERTA, a página nunca pediu a lista resolvida e
  // `ultimoNext` é null → sem isto o `paginarLoop` não arranca e o lote sai só com as
  // abertas (foi o que aconteceu: 2 bilhetes e nenhuma encerrada). Busca a 1ª página das
  // encerradas; o próprio `forward` encadeia a paginação a partir dela.
  async function buscarEncerradas() {
    if (all.length || loopAtivo) return;
    const ctxS = reqDe("SETTLED");
    if (!ctxS) return;
    try {
      const r = await of.call(window, ctxS.url, {
        method: ctxS.method, headers: ctxS.headers,
        body: bodyProxPagina(ctxS.body, 0, 0), credentials: "include",
      });
      forward(ctxS.url, await r.text());
      LOG("1ª página das ENCERRADAS buscada ativamente:", all.length, "bilhete(s)");
    } catch (e) { LOG("busca ativa das encerradas falhou:", e && e.message); }
  }

  // Rede de segurança das ABERTAS: normalmente a página já disparou a lista Aberta ao
  // carregar e o balde acima já está cheio. Se NÃO estiver (ex.: a aba Resolvida foi aberta
  // direto), refaz a MESMA requisição que a própria página faz, com os cookies da sessão.
  // Uma única vez, sem paginar: a lista de abertas é curta (`moreAvailable` costuma vir
  // false) e o custo de errar aqui não pode encostar nas encerradas.
  async function buscarAbertas() {
    if (buscandoAbertas || abertas.length) return;
    const ctxA = reqDe("OPEN");
    if (!ctxA) return;
    buscandoAbertas = true;
    try {
      const r = await of.call(window, ctxA.url, {
        method: ctxA.method, headers: ctxA.headers,
        body: ctxA.body, credentials: "include",
      });
      forward(ctxA.url, await r.text());   // cai no ramo OPEN → balde + enviar()
      LOG("busca ativa da lista ABERTA:", abertas.length, "bilhete(s)");
    } catch (e) { LOG("busca ativa das abertas falhou:", e && e.message); }
    enviar();
  }

  // ── fetch ──
  if (of && !of.__suBFW) {
    const w = function (...a) {
      const url = (a[0] && a[0].url) || a[0];
      const opts = a[1] || (a[0] && typeof a[0] === "object" ? a[0] : null);
      try { if (opts && opts.body) capturarReq(url, opts.method, _hdrsToObj(opts.headers), opts.body); } catch (e) {}
      return of.apply(this, a).then((r) => {
        try { if (RX.test(String(url))) r.clone().text().then((t) => forward(url, t)); } catch (e) {}
        return r;
      });
    };
    w.__suBFW = true;
    window.fetch = w;
  }

  // ── XMLHttpRequest ──
  const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send, osh = XMLHttpRequest.prototype.setRequestHeader;
  if (!os.__suBFW) {
    XMLHttpRequest.prototype.open = function (m, u) { this.__suBFU = u; this.__suBFM = m; this.__suBFH = { "Content-Type": "application/json" }; return oo.apply(this, arguments); };
    XMLHttpRequest.prototype.setRequestHeader = function (k, v) { try { this.__suBFH[k] = v; } catch (e) {} return osh.apply(this, arguments); };
    const s = function (body) {
      try {
        if (RX.test(String(this.__suBFU))) {
          if (body) capturarReq(this.__suBFU, this.__suBFM, this.__suBFH, body);
          this.addEventListener("load", () => { try { forward(this.__suBFU, this.responseText); } catch (e) {} });
        }
      } catch (e) {}
      return os.apply(this, arguments);
    };
    s.__suBFW = true;
    XMLHttpRequest.prototype.send = s;
  }
})();
