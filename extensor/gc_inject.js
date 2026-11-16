// Mundo MAIN (só na GiroCerto, `girocerto.fun`): BUSCA a lista de apostas da própria casa e
// repassa ao content script. Plataforma PRÓPRIA (recon s455, 15/11/2026, Chrome do Feca):
//
//   GET /api/esportes/bets           (mesmo domínio da aba, só o COOKIE)
//   → [ { id, code, kind, status, stakeCents, odds, originalOdds, payoutCents,
//         creditedCents, placedAt, settledAt, cashedCents, freebet, legs: [ … ] }, … ]
//
// O site é Next.js (RSC): "Minhas apostas" chega DENTRO do HTML (`self.__next_f`) e abrir a tela
// não dispara chamada de lista nenhuma. Um hook passivo entregaria zero, então o inject pede a
// lista ele mesmo. O cookie basta (medido com `fetch` cru, sem header): não há token.
//
// ⚠ SEM PAGINAÇÃO: a API devolve os 50 bilhetes mais recentes e nenhum parâmetro muda isso
// (medido: limit, offset, page, cursor, before, take/skip). O fim é a 1ª resposta.
// ⚠ `POST` NESTA MESMA URL FAZ APOSTA. O inject só manda GET, e o hook só aceita resposta que
// seja ARRAY (o POST devolve objeto). O detalhe (`/bets/<uuid>`) e as cotações de cashout
// (`/bets/cashout/quotes`) não casam o `RX`.
//
// O inject NÃO decide nada: normaliza (centavos → reais, ISO → epoch) e sobe o `status` cru.
// Quem traduz é o `formatTicketGC` (pelo dinheiro) e a CASA_GIROCERTO.md.
// ⚠ `odds` é REESCRITA na liquidação (anulada → 1; meia → a efetiva). A odd da aposta é
// `originalOdds`. ⚠ `payoutCents` é o POTENCIAL até na perdida; o dinheiro é `creditedCents`.
(function () {
  // ── CRU para o servidor (s409, Projeto Ficha Sharpen) ───────────────────────────────
  // O bilhete da casa, VERBATIM, ao lado do normalizado (campo `cru` da mensagem). Erro aqui
  // nunca sobe: sem cru, a captura de hoje segue igual. `codigo` = o `[Código: …]` do texto.
  const _cruDe = new WeakMap();
  function _marcarCru(b, cru) { try { _cruDe.set(b, cru); } catch (e) {} }
  function _crus(lista) {
    const out = [];
    try {
      for (const b of lista || []) {
        const c = _cruDe.get(b);
        if (!c || !b.id) continue;
        out.push({ codigo: String(b.id), cru: c });
      }
    } catch (e) {}
    return out;
  }

  // Só a LISTA: `/api/esportes/bets` seguido de fim, `?` ou `#`. O detalhe e o cashout têm
  // mais segmentos e não casam.
  const RX = /\/api\/esportes\/bets(?:[?#]|$)/i;
  const byId = new Map();                      // code → bilhete normalizado
  let respostas = 0;                           // respostas VÁLIDAS do endpoint (autodiagnóstico)
  let loopAtivo = false, fimBusca = false, repetir = false;
  const LOG = (...a) => { try { console.log("[SharpenUp gc_inject]", ...a); } catch (e) {} };
  LOG("hook instalado em", location.href);

  const of = window.fetch;
  const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send;

  // ── normalização ─────────────────────────────────────────────────────────────────────
  const _n = (v) => {
    if (v == null || v === "") return null;
    const x = Number(v);
    return isFinite(x) ? x : null;
  };
  // Centavos inteiros → reais. Divisão por 100 de inteiro não perde centavo.
  const _reais = (v) => { const x = _n(v); return x == null ? null : x / 100; };
  // ISO com fuso (`2026-11-02T00:54:02.590Z`) → epoch em segundos.
  const _epoch = (s) => {
    const t = Date.parse(String(s || ""));
    return isFinite(t) ? t / 1000 : null;
  };

  function parsePerna(l) {
    if (!l) return null;
    return {
      status: String(l.status == null ? "" : l.status),  // open · won · lost · void · half_won · half_lost (cru)
      odd: _n(l.odds),                                    // odd da seleção na colocação
      inicio: _epoch(l.startsAt),                         // início do evento (UTC)
      esporte: String(l.sport || ""),                     // football, basketball, tennis (cru)
      mercado: String(l.market || ""),                    // "1º tempo - handicap 0.0, -0.5"
      label: String(l.pick || ""),                        // "CSD Comunicaciones 0.0, -0.5"
      jogo: String(l.event || ""),                        // "CSD Comunicaciones x Deportivo Mixco"
      aoVivo: !!l.live,
      antecipado: !!l.paidEarly,                          // "Pagamento antecipado" que pagou
    };
  }

  function parseBet(t) {
    if (!t || !t.code) return null;
    return {
      id: String(t.code),                        // "ZHUUMZ423Z" — o código do card
      uuid: String(t.id || ""),
      status: String(t.status == null ? "" : t.status),  // accepted · won · lost · void · cashed_out · rejected … (cru)
      tipo: String(t.kind || ""),                // single (o único medido)
      stake: _reais(t.stakeCents),
      odd: _n(t.originalOdds),                   // odd da COLOCAÇÃO (a `odds` é reescrita ao liquidar)
      oddAtual: _n(t.odds),                      // a efetiva que a casa grava ao liquidar (só diagnóstico)
      potencial: _reais(t.payoutCents),          // ⚠ potencial até na perdida
      retorno: _reais(t.creditedCents),          // o dinheiro que voltou
      cashout: _reais(t.cashedCents),
      freebet: !!t.freebet,
      ts: _epoch(t.placedAt),                    // colocação
      liquidacao: _epoch(t.settledAt),
      sels: (Array.isArray(t.legs) ? t.legs : []).map(parsePerna).filter(Boolean),
    };
  }

  // Heartbeat: SEMPRE hook:true + respostas, mesmo com 0 bilhetes.
  function enviar() {
    try {
      const lista = Array.from(byId.values());
      window.postMessage({
        __sharpenupGCData: true, hook: true,
        bilhetes: lista, respostas: respostas, fim: fimBusca, cru: _crus(lista),
      }, "*");
    } catch (e) {}
  }

  // A versão LIQUIDADA vence a aberta (o dinheiro só é final depois de liquidado).
  const _ABERTA = new Set(["accepted", "pending", "placing", "cashing", "voiding"]);
  const _aberta = (b) => _ABERTA.has(b.status);
  function guardar(b) {
    const ex = byId.get(b.id);
    if (!ex || _aberta(ex) || !_aberta(b)) byId.set(b.id, b);
  }

  // Processa uma resposta da lista; devolve o nº de bilhetes, ou null se não era a lista.
  function forward(url, text) {
    if (!RX.test(String(url)) || typeof text !== "string") return null;
    let j;
    try { j = JSON.parse(text); } catch (e) { return null; }
    if (!Array.isArray(j)) return null;          // POST de aposta / erro / login devolvem objeto
    respostas++;
    for (const raw of j) {
      const b = parseBet(raw);
      if (b) { _marcarCru(b, raw); guardar(b); }
    }
    LOG("bilhetes na resposta:", j.length, "· total:", byId.size);
    enviar();
    return j.length;
  }

  // ── busca ativa ──────────────────────────────────────────────────────────────────────
  // GET pelo `fetch` ORIGINAL (não passa pelo gancho, que processaria duas vezes).
  async function buscar() {
    let url;
    try { url = new URL("/api/esportes/bets", location.href).href; } catch (e) { return; }
    try {
      const r = await of.call(window, url, {
        method: "GET", credentials: "include", headers: { Accept: "application/json" },
      });
      if (!r.ok) { LOG("busca parou · HTTP", r.status); return; }
      forward(url, await r.text());
    } catch (e) { LOG("busca falhou", String(e)); }
  }

  async function arrancar() {
    if (loopAtivo) return;
    loopAtivo = true;
    try { await buscar(); } finally {
      loopAtivo = false;
      fimBusca = true;                           // sem paginação: a 1ª resposta é o fim
      enviar();
      if (repetir) { repetir = false; fimBusca = false; byId.clear(); arrancar(); }
    }
  }

  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (!d || !d.__sharpenupGCReq) return;
    // Pedido novo é rodada NOVA (lição da s393, DEX Sport): o acumulado velho não é reenviado,
    // porque o content formata cada bilhete na 1ª vez que o vê. Pedido com a busca em curso
    // fica marcado e roda ao fim.
    if (loopAtivo) { repetir = true; return; }
    fimBusca = false;
    byId.clear();
    enviar();
    arrancar();
  });

  // ── fetch: a página buscando a lista (hoje ela não busca; é a rede de segurança) ──
  // Só GET: a resposta do POST (fazer aposta) nunca é lida.
  if (of && !of.__suGCW) {
    const w = function (...a) {
      const url = (a[0] && a[0].url) || a[0];
      const metodo = String((a[1] && a[1].method) || (a[0] && a[0].method) || "GET").toUpperCase();
      return of.apply(this, a).then((r) => {
        try {
          if (metodo === "GET" && RX.test(String(url))) r.clone().text().then((t) => forward(url, t));
        } catch (e) {}
        return r;
      });
    };
    w.__suGCW = true;
    window.fetch = w;
  }

  // ── XMLHttpRequest (rede de segurança: hoje a página usa fetch) ──
  if (!os.__suGCW) {
    XMLHttpRequest.prototype.open = function (m, u) { this.__suGCU = u; this.__suGCM = m; return oo.apply(this, arguments); };
    const s = function () {
      try {
        if (String(this.__suGCM || "GET").toUpperCase() === "GET" && RX.test(String(this.__suGCU))) {
          this.addEventListener("load", () => { try { forward(this.__suGCU, this.responseText); } catch (e) {} });
        }
      } catch (e) {}
      return os.apply(this, arguments);
    };
    s.__suGCW = true;
    XMLHttpRequest.prototype.send = s;
  }
})();
