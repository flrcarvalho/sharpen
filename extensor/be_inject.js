// Mundo MAIN (só na BETesporte): escuta as RESPOSTAS que a própria página recebe da
// API de bilhetes (POST /api/bet/RequestUserTickets — JSON perfeito) e repassa ao
// content script. NÃO faz requisição nova, NÃO altera nada — só lê o que a página já
// baixa. Assim a extensão pega o dado exato do site, sem clicar em "Ver Cupom" e sem
// adivinhar auth/headers (o Bearer/JWT fica com a página). O robô só ROLA/pagina a
// lista p/ a página buscar mais (comportamento humano). Espelho do sb_inject.js.
//
// Acumula tudo que captura e RE-ENVIA sob demanda (o content script pede ao iniciar)
// — assim não perde a 1ª página, que a página busca no load antes do content estar
// pronto pra ouvir.
(function () {
  const RX = /\/api\/bet\/RequestUserTickets/i;   // endpoint da LISTA de bilhetes
  const all = [];
  const seen = new Set();
  let respostas = 0;   // respostas do endpoint de tickets que o hook viu (autodiagnóstico)

  // Emite SEMPRE hook:true + respostas (heartbeat), mesmo com 0 itens — assim o content
  // distingue "hook não carregou" de "endpoint respondeu mas lemos 0" (achado #13). Espelha o
  // bf_inject. Postar `items:[]` é inofensivo (o content dedupa e só lê hook/respostas).
  function postAll() {
    try { window.postMessage({ __sharpenupBEData: true, items: all, hook: true, respostas: respostas }, "*"); } catch (e) {}
  }

  function forward(url, text) {
    if (!RX.test(String(url)) || typeof text !== "string") return;
    try {
      const j = JSON.parse(text);
      respostas++;   // o endpoint de tickets respondeu (prova de hook vivo + site respondendo)
      // Forma: { data: { items: [...] } }. Tolerante a variações (items no topo).
      const arr = (j && j.data && Array.isArray(j.data.items)) ? j.data.items
                : (Array.isArray(j) ? j : (j.items || []));
      for (const t of arr) {
        const c = t && t.id;
        if (c != null && !seen.has(c)) { seen.add(c); all.push(t); }
      }
    } catch (e) {}
    postAll();   // sempre reporta o heartbeat (como o bf_inject), inclusive quando lê 0
  }

  // O content script pede o acumulado ao iniciar o robô → re-envia tudo.
  window.addEventListener("message", (ev) => { if (ev.data && ev.data.__sharpenupBEReq) postAll(); });

  // fetch
  const of = window.fetch;
  if (of && !of.__suBEW) {
    const w = function (...a) {
      const url = (a[0] && a[0].url) || a[0];
      return of.apply(this, a).then((r) => {
        try { if (RX.test(String(url))) r.clone().text().then((t) => forward(url, t)); } catch (e) {}
        return r;
      });
    };
    w.__suBEW = true;
    window.fetch = w;
  }

  // XMLHttpRequest
  const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send;
  if (!os.__suBEW) {
    XMLHttpRequest.prototype.open = function (m, u) { this.__suBEU = u; return oo.apply(this, arguments); };
    const s = function () {
      try {
        if (RX.test(String(this.__suBEU))) {
          this.addEventListener("load", () => { try { forward(this.__suBEU, this.responseText); } catch (e) {} });
        }
      } catch (e) {}
      return os.apply(this, arguments);
    };
    s.__suBEW = true;
    XMLHttpRequest.prototype.send = s;
  }
})();
