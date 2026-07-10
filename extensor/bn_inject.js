// Mundo MAIN (só na Betano): escuta as RESPOSTAS que a própria página recebe da API
// de bilhetes resolvidos (GET /myaccount/api/ma/bet/bet-history-v3?settled=true&page=N
// — JSON perfeito) e repassa ao content script. NÃO faz requisição nova, NÃO altera
// nada — só lê o que a página já baixa. O robô só ROLA a lista p/ a página paginar
// (carrega em levas de 10, cursor por lastId). Espelho do be_inject.js / sb_inject.js.
//
// Acumula tudo que captura e RE-ENVIA sob demanda (o content script pede ao iniciar)
// — assim não perde a 1ª página, que a página busca no load antes do content estar
// pronto pra ouvir.
//
// FIM AUTORITATIVO: toda página traz "LastId" (cursor), MENOS a última. Uma resposta
// com Bets mas SEM LastId = fim real da lista → sinaliza `fim:true` p/ o robô parar de
// verdade (nunca no primeiro obstáculo).
(function () {
  const RX = /\/api\/ma\/bet\/bet-history-v3/i;   // endpoint da LISTA de bilhetes resolvidos
  const all = [];
  const seen = new Set();
  let fimReal = false;

  function postAll() {
    if (all.length || fimReal) {
      try { window.postMessage({ __sharpenupBNData: true, bets: all, fim: fimReal }, "*"); } catch (e) {}
    }
  }

  function forward(url, text) {
    const u = String(url);
    // Só a aba "Liquidada" (settled=true). A aba "Em aberto" não é gravada (vai por print).
    if (!RX.test(u) || !/settled=true/i.test(u) || typeof text !== "string") return;
    try {
      const j = JSON.parse(text);
      const res = j && j.Result;
      if (!res) return;
      const arr = Array.isArray(res.Bets) ? res.Bets : [];
      let added = false;
      for (const t of arr) {
        const c = t && t.BetId;
        if (c != null && !seen.has(c)) { seen.add(c); all.push(t); added = true; }
      }
      // Última página vem SEM LastId (ou Bets vazio) → fim autoritativo da lista.
      if (!("LastId" in res) || res.LastId == null) fimReal = true;
      if (added || fimReal) postAll();
    } catch (e) {}
  }

  // O content script pede o acumulado ao iniciar o robô → re-envia tudo.
  window.addEventListener("message", (ev) => { if (ev.data && ev.data.__sharpenupBNReq) postAll(); });

  // fetch
  const of = window.fetch;
  if (of && !of.__suBNW) {
    const w = function (...a) {
      const url = (a[0] && a[0].url) || a[0];
      return of.apply(this, a).then((r) => {
        try { if (RX.test(String(url))) r.clone().text().then((t) => forward(url, t)); } catch (e) {}
        return r;
      });
    };
    w.__suBNW = true;
    window.fetch = w;
  }

  // XMLHttpRequest
  const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send;
  if (!os.__suBNW) {
    XMLHttpRequest.prototype.open = function (m, u) { this.__suBNU = u; return oo.apply(this, arguments); };
    const s = function () {
      try {
        if (RX.test(String(this.__suBNU))) {
          this.addEventListener("load", () => { try { forward(this.__suBNU, this.responseText); } catch (e) {} });
        }
      } catch (e) {}
      return os.apply(this, arguments);
    };
    s.__suBNW = true;
    XMLHttpRequest.prototype.send = s;
  }
})();
