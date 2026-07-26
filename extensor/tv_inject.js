// Mundo MAIN (só na Tivo): lê as RESPOSTAS do histórico de apostas e repassa ao content script.
//
// A Tivo roda o sportsbook v4 da BetConstruct dentro de um IFRAME DE MESMA ORIGEM
// (`tivo.bet.br/sportsbookv4/…`), e o histórico não sai de um endpoint próprio: sai de um
// PROXY genérico do site, que encaminha mensagens para o motor da casa —
//
//   POST tivo.bet.br/api/game/p/messagetosport
//   {"name":"gethistory","message":"{\"countOnly\":false,\"language\":33,\"from\":…,\"to\":…}"}
//
// Duas consequências que mandam no desenho deste arquivo:
//
// 1) A MESMA URL serve dezenas de mensagens diferentes (saldo, notificações, tradução…).
//    Filtrar por URL não basta e filtrar pelo corpo do pedido é frágil (nem todo caminho de
//    request expõe o body). Por isso quem decide é a FORMA DA RESPOSTA: só processamos o que
//    vier com `Tickets` em array. Mensagem que não for histórico é ignorada em silêncio.
//
// 2) NÃO HÁ PAGINAÇÃO. Uma única chamada devolve a conta inteira e a própria casa carimba
//    `Count`. Provado ao vivo: `from` de 2020 devolve exatamente os mesmos bilhetes que `from`
//    vazio. Então o "replay" aqui é UMA requisição, não um laço — o fim é autoritativo
//    (`Error:null` + `Tickets.length === Count`), nunca heurística de tempo.
//
// ARMADILHA CONFIRMADA no dado real: `from`/`to` são epoch em MILISSEGUNDOS. Passar em
// SEGUNDOS devolve `Count: 0` com `Error: null` — ou seja, some tudo sem erro nenhum. Toda
// janela de dias tem de ser montada em ms.
//
// O inject NÃO decide nada: entrega os campos crus normalizados. `Result` desconhecido sobe
// como veio; quem traduz é o content.js com o `casas/CASA_TIVO.md`.
(function () {
  const RX = /\/api\/game\/p\/messagetosport/i;   // proxy de mensagens do sportsbook
  const byId = new Map();                          // ID(string) → bilhete normalizado
  let respostas = 0;                               // respostas de HISTÓRICO que o hook viu
  let reqCtx = null;                               // {url, language} de uma requisição real
  let pedido = false;                              // o robô já pediu → pode arrancar o replay
  let loopAtivo = false;                           // trava: um replay por vez
  let fimReplay = false;                           // a casa já entregou a lista completa
  let dias = 0;                                    // janela pedida pelo robô (0 = tudo)
  const LOG = (...a) => { try { console.log("[SharpenUp tv_inject]", ...a); } catch (e) {} };
  LOG("hook instalado em", location.href);

  const of = window.fetch;                         // fetch ORIGINAL — o replay usa este

  const IDIOMA_PADRAO = 33;                        // pt-BR: mantém mercado/esporte já traduzidos
  const TETO_TENTATIVAS = 3;

  // ── normalização (BetConstruct → objeto limpo) ────────────────────────────────
  // Dinheiro e odd vêm em unidade normal (Amount 150.0 = R$ 150,00) — NÃO há milésimos aqui.
  const _n = (v) => (typeof v === "number" && isFinite(v) ? v : null);
  const _s = (o) => (o && o.Name ? String(o.Name) : "");

  function parseItem(it) {
    if (!it) return null;
    const g = it.Game || null;
    const og = it.OutrightGame || null;
    const fp = it.FinalPosition || null;
    return {
      id: it.ID != null ? String(it.ID) : "",
      odd: _n(it.Value),                            // odd DA PERNA, precisão da casa
      tipo: it.ItemType,                            // 0 = normal · 3 = outright
      resultado: it.Result,                         // 0 pendente · 2 ganha · 3 perdida · cru
      esporte: _s(it.Sport),                        // já em pt-BR ("Futebol", "Basquete")
      regiao: _s(it.Region),
      campeonato: _s(it.Champ),
      mercado: _s(it.Market),                       // pode conter placeholder "{p1_r}"
      selecao: _s(it.Position),                     // "Mais de" / "Menos de" / "Casa" / "Sim"
      linha: fp && _n(fp.h) != null ? _n(fp.h) : null,   // 6.5 · -1.5 (handicap)
      hisminus: fp ? !!fp.hisminus : false,
      p1: fp && fp.p1 != null ? fp.p1 : null,       // preenche o "{p1_r}" do mercado (3º quarto)
      jogo: g ? {
        inicio: _n(g.StartTime),                    // epoch ms UTC
        casa: _s(g.Team1),
        fora: _s(g.Team2),
      } : null,
      // Outright (F1, vencedor de torneio): `Game` é null e o mercado é lixo interno
      // ("Free text multiwinner market") — o que vale é o par abaixo.
      outright: og || it.Outright ? {
        selecao: og ? _s(og.Team1) : "",            // "Piastri, Oscar"
        nome: _s(it.Outright),                      // "Grande Prêmio da Hungria Qualificação - Top 3"
        inicio: og ? _n(og.StartTime) : null,
      } : null,
      // ⚠ `Team1Score`/`Team2Score` NÃO são placar: são a estatística do mercado (escanteios,
      // cartões). O placar é `LiveScore`. Entregamos os dois com nomes que não se confundem.
      placar: it.LiveScore || "",
      estat: [_n(it.Team1Score), _n(it.Team2Score)],
      // ⚠ `CalculatedBetAmount` NÃO é stake: é o rateio da stake por perna.
      rateio: _n(it.CalculatedBetAmount),
    };
  }

  function parseTicket(t) {
    if (!t || t.ID == null) return null;
    return {
      id: String(t.ID),
      colocada: _n(t.ActionTime),                   // epoch ms UTC → o content converte p/ BRT
      editada: _n(t.LastEditTime),
      status: t.Status,                             // 5 = em aberto · 10 = liquidado (cru)
      resultado: t.Result,                          // 0 pendente · 2 ganha · 3 perdida (cru)
      stake: _n(t.Amount),
      koef: _n(t.Koef),                             // ODD TOTAL, precisão completa
      winKoef: _n(t.WinKoef),                       // null em aberto — nunca usar como odd
      retorno: _n(t.WinAmount),                     // 0 nas perdidas E nas abertas
      potencial: _n(t.PossibleWin),                 // retorno POTENCIAL (só faz sentido em aberto)
      cashout: !!t.CashOut,
      cashoutPossivel: _n(t.PossibleCashout),
      sistema: !!t.IsSystem,
      bonus: !!t.IsBonus,
      moeda: t.CurrencySTR || "",
      itens: (t.Items || []).map(parseItem).filter(Boolean),
    };
  }

  // Emite SEMPRE hook:true + respostas (heartbeat), mesmo com 0 bilhetes — é o que separa
  // "inject não carregou" de "respondeu e lemos 0" no autodiagnóstico.
  function enviar() {
    const msg = {
      __sharpenupTVData: true, hook: true,
      tickets: Array.from(byId.values()), respostas: respostas, fim: fimReplay,
    };
    try { window.postMessage(msg, "*"); } catch (e) {}
    // O sportsbook v4 roda num IFRAME (mesma origem) e é DE LÁ que o gethistory sai — mas o
    // content.js só roda no frame de topo (`all_frames:false`). Sem repassar ao topo, o robô
    // ficaria esperando para sempre uma mensagem que nunca sobe.
    try { if (window.top && window.top !== window) window.top.postMessage(msg, "*"); } catch (e) {}
  }

  // Bilhete que veio SÓ com o identificador (sem Status, sem Result, sem pernas). Existe:
  // 3 dos 25 bilhetes do lote de 26/07 subiram assim, com "Status=undefined" e a lista de
  // seleções vazia — e os mesmos IDs vêm CHEIOS no payload de referência do recon.
  const vazio = (x) => x.status == null && x.resultado == null && !(x.itens || []).length;

  // O mesmo bilhete pode voltar em consultas diferentes: a versão RESOLVIDA vence a ABERTA.
  // E CONTEÚDO vence esqueleto, sempre — sem esta regra o esqueleto ganhava por chegar
  // primeiro: ele não parece "aberto" (status undefined), então a linha de baixo nunca o
  // substituía e o bilhete cheio que chegava depois era descartado em silêncio (s198).
  function guardar(t) {
    const ex = byId.get(t.id);
    if (!ex) { byId.set(t.id, t); return; }
    if (vazio(t)) return;                            // esqueleto nunca sobrescreve
    if (vazio(ex)) { byId.set(t.id, t); return; }    // conteúdo sempre vence esqueleto
    const aberto = (x) => x.status === 5 || x.resultado === 0;
    if (aberto(ex) && !aberto(t)) byId.set(t.id, t);
  }

  // Processa uma resposta. Devolve `true` se era histórico (e a lista veio completa).
  function forward(url, text) {
    if (!RX.test(String(url)) || typeof text !== "string") return false;
    let j;
    try { j = JSON.parse(text); } catch (e) { return false; }
    // É AQUI que separamos o histórico das outras mensagens do mesmo endpoint.
    if (!j || !Array.isArray(j.Tickets)) return false;
    respostas++;
    for (const raw of j.Tickets) {
      const t = parseTicket(raw);
      if (t) guardar(t);
    }
    const completa = !j.Error && (j.Count == null || j.Tickets.length === j.Count);
    LOG("bilhetes na resposta:", j.Tickets.length, "· Count:", j.Count, "· total:", byId.size);
    enviar();
    return completa;
  }

  // ── replay: uma requisição, sem paginação ─────────────────────────────────────
  function corpoHistorico() {
    // Janela de dias → `from`/`to` em MILISSEGUNDOS (segundos devolvem 0 em silêncio).
    const agora = Date.now();
    const msg = {
      countOnly: false,
      language: (reqCtx && reqCtx.language) || IDIOMA_PADRAO,
      from: dias > 0 ? agora - dias * 86400000 : "",
      to: dias > 0 ? agora : "",
    };
    // Sem `result`: a consulta sem filtro traz abertas E resolvidas de uma vez.
    return JSON.stringify({ name: "gethistory", message: JSON.stringify(msg) });
  }

  function urlHistorico() {
    if (reqCtx && reqCtx.url) return reqCtx.url;
    try { return new URL("/api/game/p/messagetosport", location.href).href; } catch (e) { return null; }
  }

  async function arrancarReplay() {
    if (loopAtivo || fimReplay) return;
    const alvo = urlHistorico();
    if (!alvo) return;
    loopAtivo = true;
    try {
      for (let i = 0; i < TETO_TENTATIVAS; i++) {
        let r;
        try {
          r = await of.call(window, alvo, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: corpoHistorico(),
            credentials: "include",
          });
        } catch (e) { LOG("erro no replay:", e && e.message); break; }
        if (!r || !r.ok) { LOG("replay parou · HTTP", r && r.status); break; }
        let completa = false;
        try { completa = forward(r.url || alvo, await r.text()); } catch (e) { break; }
        if (completa) { fimReplay = true; break; }        // fim AUTORITATIVO (a casa carimbou)
      }
    } finally {
      loopAtivo = false;
      fimReplay = true;                                    // não deixa o robô esperando o teto
      enviar();
    }
  }

  // Guarda url + idioma de uma requisição real (o idioma manda nos nomes de mercado/esporte).
  function capturarReq(url, body) {
    if (!RX.test(String(url))) return;
    if (!reqCtx) {
      let lang = null;
      try {
        const o = JSON.parse(String(body || "{}"));
        const m = typeof o.message === "string" ? JSON.parse(o.message) : o.message;
        if (m && m.language != null) lang = m.language;
      } catch (e) {}
      reqCtx = { url: String(url), language: lang };
      LOG("requisição capturada p/ replay · idioma =", lang == null ? "(padrão)" : lang);
    }
    if (pedido) arrancarReplay();
  }

  // O content pede o acumulado ao iniciar o robô → re-envia tudo E arranca o replay. A 1ª
  // resposta chega antes de o content estar ouvindo, por isso o re-envio sob demanda.
  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (!d || !d.__sharpenupTVReq) return;
    pedido = true;
    if (Number(d.dias) > 0) dias = Number(d.dias);
    enviar();
    arrancarReplay();
  });

  // ── fetch ──
  if (of && !of.__suTVW) {
    const w = function (...a) {
      const url = (a[0] && a[0].url) || a[0];
      const opts = a[1] || (a[0] && typeof a[0] === "object" ? a[0] : null);
      try { if (RX.test(String(url))) capturarReq(url, opts && opts.body); } catch (e) {}
      return of.apply(this, a).then((r) => {
        try { if (RX.test(String(url))) r.clone().text().then((t) => forward(url, t)); } catch (e) {}
        return r;
      });
    };
    w.__suTVW = true;
    window.fetch = w;
  }

  // ── XMLHttpRequest (o sportsbook v4 dispara o gethistory por XHR) ──
  const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send;
  if (!os.__suTVW) {
    XMLHttpRequest.prototype.open = function (m, u) { this.__suTVU = u; return oo.apply(this, arguments); };
    const s = function (body) {
      try {
        if (RX.test(String(this.__suTVU))) {
          capturarReq(this.__suTVU, body);
          this.addEventListener("load", () => { try { forward(this.__suTVU, this.responseText); } catch (e) {} });
        }
      } catch (e) {}
      return os.apply(this, arguments);
    };
    s.__suTVW = true;
    XMLHttpRequest.prototype.send = s;
  }
})();
