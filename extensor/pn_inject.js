// Mundo MAIN (só na Pinnacle): lê as RESPOSTAS que a própria página recebe da API de
// bilhetes (POST /member-service/v2/wager-filter?locale=… — JSON) e repassa ao content
// script. A Pinnacle NÃO devolve objetos com nomes: cada bilhete é um ARRAY POSICIONAL
// (~98 campos). Este inject faz o de-para posição→nome (âncoras validadas contra a tabela
// renderizada + os goldens da CASA_PINNACLE) e envia objetos limpos, para o content script
// tratar igual às outras casas passivas (Betano/Betfair). NÃO faz OCR, NÃO altera a página.
//
// UMA URL, DUAS ABAS: a mesma /wager-filter serve "Decidido" (encerradas) e "Não decidido"
// (abertas) — muda só o CORPO do POST (status + intervalo de datas). O estado de cada
// bilhete vem no próprio dado (campo 18 = "SETTLED" → resolvida; ≠ → aberta), então não
// dependemos de saber qual aba disparou.
//
// REPLAY ATIVO (o "puxa automaticamente"): a partir de um POST real que a página faz, o
// inject aprende url+headers+body e RE-EMITE a requisição para as duas abas numa janela de
// datas larga — com os cookies da sessão (credentials:include), sem tocar na UI. Espelha o
// paginarLoop do bf_inject. Passa a URL/headers exatos que a página usou → mesma origem,
// mesma auth. Se o replay falhar (formato de body inesperado), o modo passivo ainda entrega
// o que a página já baixou.
(function () {
  const RX = /\/wager-filter/i;                 // endpoint da LISTA de bilhetes
  const all = [];
  const seen = new Set();                        // chave: id|A (aberta) ou id|S (settled)
  let respostas = 0;                             // respostas do endpoint que o hook viu (autodiagnóstico)
  let reqCtx = null;                             // {url, method, headers, body} de um POST real (p/ replay)
  let pedido = false;                            // o robô já pediu → pode arrancar o replay ativo
  let loopAtivo = false;                         // trava: um replay por vez
  let fimReplay = false;                         // as duas abas já foram re-emitidas
  let janelaDias = 45;                           // janela de datas do replay (encerradas); o robô sobrescreve
  const LOG = (...a) => { try { console.log("[SharpenUp pn_inject]", ...a); } catch (e) {} };
  LOG("hook instalado em", location.href);

  const of = window.fetch;                       // fetch ORIGINAL — o replay usa este (não re-dispara o wrapper)

  // ── de-para posição→nome de um bilhete (array posicional) ──────────────────────
  // Âncoras (validadas no dump real): 0=P/L · 6=WIN/LOSE · 7=ID · 9=confronto (jogo) ou
  // título do prop · 10=confronto (só em props "Casa-vs-Fora") · 14=colocação · 15=data do
  // evento · 16=odd(str) · 18=SETTLED · 20=lado/seleção ("Mais de"/"Menos de"/mandante) ·
  // 22=seleção escolhida · 24=linha (handicap/total) · 28=liga · 29=stake(Risco) · 31=esporte ·
  // 44=pernas (só múltipla/Mix Parlay) · 45=categoria especial ("Props de Jogadores") ·
  // 46=unidade/período ("Sets"/"Games"/"Escanteios"/"Mortes"/estatística) · 93=WON/LOST/PUSHED.
  function parseBet(a) {
    if (!Array.isArray(a)) return null;
    const id = a[7];
    if (id == null) return null;
    const statusLiq = a[18];
    const aberta = String(statusLiq || "").toUpperCase() !== "SETTLED";
    const pernasRaw = Array.isArray(a[44]) ? a[44] : null;   // múltipla (Mix Parlay)
    const ehProp = a[10] != null && a[10] !== "";            // prop tem o confronto no 10
    return {
      id: id,
      aberta: aberta,
      statusLiq: statusLiq,
      resultRaw: a[6] || "",             // WIN / LOSE (vazio em aberta)
      resultLabel: a[93] || "",          // WON / LOST / PUSHED (vazio em aberta)
      plNet: a[0],                       // Vitória/derrota (P/L líquido)
      esporte: a[31] || "",              // "Tennis", "Soccer", "E Sports"…
      liga: a[28] || "",                 // "ATP Estoril - Qualifiers"
      stake: a[29],                      // Risco
      odd: a[16] || "",                  // "1.636" (ponto)
      dataEvento: a[15] || "",           // "2026-07-19" (data do resultado — a que vale)
      dataColoc: a[14] || "",            // "2026-07-18 18:03:01" (colocação — ignorar)
      confronto: ehProp ? (a[10] || "") : (a[9] || ""),   // "A -vs- B"
      titulo: ehProp ? (a[9] || "") : "",                 // nome do prop (só em props)
      ladoSel: a[20] || "",              // "Mais de"/"Menos de"/mandante
      selecao: a[22] || "",              // seleção escolhida (jogos)
      linha: (typeof a[24] === "number") ? a[24] : null,  // handicap/total
      categoria: a[45] || "",            // "Props de Jogadores" (vazio em jogos)
      unidade: _limpa(a[46]),            // "Sets"/"Games"/"Escanteios"/"Mortes"/estatística
      pernas: pernasRaw ? pernasRaw.map(parseLeg).filter(Boolean) : null,
    };
  }

  // Perna de múltipla (Mix Parlay): array posicional próprio.
  // 0=seleção · 3=data do evento · 4=odd(str) · 7=esporte · 9=liga · 10=mandante · 11=visitante ·
  // 19=linha · 28=confronto ("A -vs- B") · 44=unidade · 48/26=WON/LOST/PUSHED da perna.
  function parseLeg(l) {
    if (!Array.isArray(l)) return null;
    return {
      selecao: l[0] || "",
      dataEvento: l[3] || "",
      odd: l[4] || "",
      esporte: l[7] || "",
      liga: l[9] || "",
      confronto: l[28] || ((l[10] && l[11]) ? (l[10] + " -vs- " + l[11]) : ""),
      linha: (typeof l[19] === "number") ? l[19] : null,
      unidade: _limpa(l[44]),
      resultLabel: l[48] || l[26] || "",
    };
  }

  function _limpa(s) { return String(s == null ? "" : s).replace(/[\r\n]+/g, "").trim(); }

  // Emite SEMPRE hook:true + respostas (heartbeat), mesmo com 0 bilhetes — o content
  // distingue "hook não carregou" de "endpoint respondeu, lemos 0" (autodiagnóstico, achado #13).
  function enviar() {
    try { window.postMessage({ __sharpenupPNData: true, hook: true, bets: all, respostas: respostas, fim: fimReplay }, "*"); } catch (e) {}
  }

  function forward(url, text) {
    if (!RX.test(String(url)) || typeof text !== "string") return false;
    let j;
    try { j = JSON.parse(text); } catch (e) { return false; }
    // Forma: array de arrays (lista de bilhetes). Tolerante: aceita {data:[…]}/{bets:[…]}.
    const arr = Array.isArray(j) ? j
              : (j && Array.isArray(j.data) ? j.data
              : (j && Array.isArray(j.bets) ? j.bets : null));
    if (!arr) return false;
    respostas++;
    const antes = all.length;
    for (const raw of arr) {
      const b = parseBet(raw);
      if (!b) continue;
      const k = b.id + "|" + (b.aberta ? "A" : "S");
      if (seen.has(k)) continue;
      seen.add(k);
      all.push(b);
    }
    LOG("bilhetes na resposta:", arr.length, "· total:", all.length);
    enviar();
    return all.length > antes || arr.length === 0;
  }

  // ── replay ativo: re-emite a busca p/ as duas abas numa janela larga ────────────
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
  // Guarda o 1º POST real de /wager-filter COM body → base do replay.
  function capturarReq(url, method, headers, body) {
    if (reqCtx || !RX.test(String(url)) || !body) return;
    reqCtx = { url: String(url), method: (method || "POST"), headers: headers || {}, body: _bodyToStr(body) };
    LOG("requisição capturada p/ replay · body:", (reqCtx.body || "").slice(0, 240));
    if (pedido) arrancarReplay();
  }

  // Monta o corpo do POST para uma aba (status) e janela de datas. Campos REAIS do
  // /wager-filter (form-urlencoded, confirmados nos dois Payloads da página):
  //   s    = status da aba: "OPEN" (Não decidido) | "SETTLED" (Decidido)
  //   type = "EVENT" (abertas) | "WAGER" (encerradas)   ← muda junto com a aba
  //   sd   = "false" nas DUAS abas (não é o discriminador)
  //   f    = data inicial "YYYY-MM-DD 00:00:00" · t = data final "YYYY-MM-DD 00:00:00"
  //   d    = preset de dias (-1 = intervalo custom, que é o que usamos com f/t explícitos)
  // Reaproveita o body aprendido (preserva product/timezone/timeZoneId/sportId/leagueId) e só
  // sobrescreve s/type/sd/f/t/d. Defensivo: se algum campo não existir no body, apenas adiciona.
  function _ymdHms(ts) {
    const d = new Date(ts);
    const p = (n) => String(n).padStart(2, "0");
    return d.getFullYear() + "-" + p(d.getMonth() + 1) + "-" + p(d.getDate()) + " 00:00:00";
  }
  function bodyParaAba(settled) {
    const base = reqCtx.body || "";
    let ps;
    try { ps = new URLSearchParams(base); } catch (e) { return base; }
    ps.set("sd", "false");
    ps.set("d", "-1");
    if (settled) {
      // Encerradas (Decidido): janela de N dias por data do evento.
      const to = Date.now(), from = to - Math.max(1, janelaDias) * 86400000;
      ps.set("s", "SETTLED");
      ps.set("type", "WAGER");
      ps.set("f", _ymdHms(from));
      ps.set("t", _ymdHms(to));
    } else {
      // Abertas (Não decidido): sem filtro de data (a Pinnacle ignora datas aqui) — mantém
      // f/t como hoje, igual ao que a própria página envia.
      const hoje = _ymdHms(Date.now());
      ps.set("s", "OPEN");
      ps.set("type", "EVENT");
      ps.set("f", hoje);
      ps.set("t", hoje);
    }
    return ps.toString();
  }

  async function _emitir(settled) {
    try {
      const r = await of.call(window, reqCtx.url, {
        method: reqCtx.method, headers: reqCtx.headers,
        body: bodyParaAba(settled), credentials: "include",
      });
      forward(reqCtx.url, await r.text());
    } catch (e) { LOG("erro no replay:", e && e.message); }
  }
  async function arrancarReplay() {
    if (loopAtivo || fimReplay || !reqCtx) return;
    loopAtivo = true;
    try {
      await _emitir(true);    // encerradas (Decidido), janela de N dias
      await _emitir(false);   // abertas (Não decidido), todas
    } finally {
      loopAtivo = false;
      fimReplay = true;
      enviar();               // sinaliza fim p/ o robô parar de esperar
    }
  }

  // O content script pede o acumulado ao iniciar o robô (com a janela de dias) → re-envia
  // tudo E arranca o replay das duas abas. A 1ª página vem no load da página (antes do
  // content estar pronto pra ouvir), por isso re-enviamos sob demanda.
  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (!d || !d.__sharpenupPNReq) return;
    if (typeof d.dias === "number" && d.dias > 0) janelaDias = d.dias;
    pedido = true;
    enviar();
    arrancarReplay();
  });

  // ── fetch ──
  if (of && !of.__suPNW) {
    const w = function (...a) {
      const url = (a[0] && a[0].url) || a[0];
      const opts = a[1] || (a[0] && typeof a[0] === "object" ? a[0] : null);
      try { if (opts && opts.body) capturarReq(url, opts.method, _hdrsToObj(opts.headers), opts.body); } catch (e) {}
      return of.apply(this, a).then((r) => {
        try { if (RX.test(String(url))) r.clone().text().then((t) => forward(url, t)); } catch (e) {}
        return r;
      });
    };
    w.__suPNW = true;
    window.fetch = w;
  }

  // ── XMLHttpRequest ──
  const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send, osh = XMLHttpRequest.prototype.setRequestHeader;
  if (!os.__suPNW) {
    XMLHttpRequest.prototype.open = function (m, u) { this.__suPNU = u; this.__suPNM = m; this.__suPNH = {}; return oo.apply(this, arguments); };
    XMLHttpRequest.prototype.setRequestHeader = function (k, v) { try { this.__suPNH[k] = v; } catch (e) {} return osh.apply(this, arguments); };
    const s = function (body) {
      try {
        if (RX.test(String(this.__suPNU))) {
          if (body) capturarReq(this.__suPNU, this.__suPNM, this.__suPNH, body);
          this.addEventListener("load", () => { try { forward(this.__suPNU, this.responseText); } catch (e) {} });
        }
      } catch (e) {}
      return os.apply(this, arguments);
    };
    s.__suPNW = true;
    XMLHttpRequest.prototype.send = s;
  }
})();
