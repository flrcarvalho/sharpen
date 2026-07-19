// Mundo MAIN (só na Betano): escuta as RESPOSTAS que a própria página recebe da API
// de bilhetes (GET /myaccount/api/ma/bet/bet-history-v3?settled=true|false&page=N —
// JSON perfeito) e repassa ao content script. NÃO faz requisição nova, NÃO altera
// nada — só lê o que a página já baixa. O robô só ROLA a lista p/ a página paginar
// (carrega em levas de 10, cursor por lastId). Espelho do be_inject.js / sb_inject.js.
//
// DUAS abas: "Liquidada" (settled=true → resolvidas) E "Em aberto" (settled=false →
// abertas, aguardando resultado). CADA bilhete é marcado com `__aberta` conforme a
// aba que o trouxe. As abertas sobem como bilhete SEM resultado (o backend grava
// 'aberta' e faz UPSERT por BetId quando o bilhete fecha — atualiza, não duplica).
//
// Acumula tudo que captura e RE-ENVIA sob demanda (o content script pede ao iniciar)
// — assim não perde a 1ª página, que a página busca no load antes do content estar
// pronto pra ouvir. Um MESMO BetId pode existir nas duas listas (aberto e depois
// resolvido) → a chave do `seen` inclui o estado, senão o resolvido seria descartado.
//
// FIM AUTORITATIVO por LISTA: toda página traz "LastId" (cursor), MENOS a última. Uma
// resposta com Bets mas SEM LastId = fim real daquela lista → sinaliza `fimSettled`/
// `fimOpen` p/ o robô parar de verdade a paginação da aba ativa (nunca no 1º obstáculo).
(function () {
  const RX = /\/api\/ma\/bet\/bet-history-v3/i;   // endpoint da LISTA de bilhetes
  const all = [];
  const seen = new Set();                          // chave: BetId|A (aberta) ou BetId|S (liquidada)
  let fimSettled = false, fimOpen = false;
  let respostas = 0;   // respostas do endpoint de histórico que o hook viu (autodiagnóstico)

  // Emite SEMPRE hook:true + respostas (heartbeat), mesmo sem bilhetes/fim — assim o content
  // distingue "hook não carregou" de "endpoint respondeu mas lemos 0" (achado #13). Espelha o
  // bf_inject; mantém `fimSettled`/`fimOpen` p/ o robô saber o fim autoritativo de cada lista.
  function postAll() {
    try { window.postMessage({ __sharpenupBNData: true, bets: all, fimSettled, fimOpen, hook: true, respostas: respostas }, "*"); } catch (e) {}
  }

  function forward(url, text) {
    const u = String(url);
    if (!RX.test(u) || typeof text !== "string") return;
    // settled=true → aba Liquidada (resolvidas). Senão (settled=false ou ausente na aba
    // Em aberto) → abertas. A marca `__aberta` viaja com o bilhete até o content script.
    const aberta = !/settled=true/i.test(u);
    try {
      const j = JSON.parse(text);
      const res = j && j.Result;
      if (res) {
        respostas++;   // o endpoint de histórico respondeu com a forma esperada (hook vivo)
        const arr = Array.isArray(res.Bets) ? res.Bets : [];
        for (const t of arr) {
          const c = t && t.BetId;
          if (c == null) continue;
          const k = c + "|" + (aberta ? "A" : "S");
          if (seen.has(k)) continue;
          seen.add(k);
          t.__aberta = aberta;   // objeto é o nosso clone (JSON.parse) — mutar é seguro
          all.push(t);
        }
        // Última página vem SEM LastId (ou Bets vazio) → fim autoritativo DAQUELA lista.
        if (!("LastId" in res) || res.LastId == null) { if (aberta) fimOpen = true; else fimSettled = true; }
      }
    } catch (e) {}
    postAll();   // sempre reporta o heartbeat (como o bf_inject), inclusive quando lê 0
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
