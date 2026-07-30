// ── Web Worker do Monte Carlo ────────────────────────────────────────────────
// Carregado como ARQUIVO de mesma origem (`new Worker('assets/js/mc-worker.js')`),
// nunca como `blob:` — a CSP do app é `default-src 'self'` + `script-src 'self'
// 'unsafe-inline'`, e worker de blob cai no default-src, que não o permite. Foi
// exatamente o que matou o worker anterior em silêncio (ver mc-core.js).
//
// A matemática NÃO vive aqui: vem de mc-core.js, o MESMO arquivo que a página
// carrega. `location.search` repassa o `?v=` do cache-busting — quem bumpa é o
// index.html, num lugar só, e o núcleo nunca fica velho por baixo do worker novo.
importScripts('mc-core.js' + location.search);

self.onmessage = function (e) {
  var d = e.data, n = d.L.length, rows = new Array(n);
  for (var i = 0; i < n; i++) rows[i] = { lucro: d.L[i], stake: d.S[i] };
  try {
    var mc = _calcMCdrawdownRaw(rows, d.sims), pv = _calcPValueMCraw(rows, d.sims);
    self.postMessage({ id: d.id, mc: mc, pv: pv });
  } catch (err) {
    // O chamador (mcComputeAsync) trata `err` recomputando em sync — nunca fica sem número.
    self.postMessage({ id: d.id, err: String(err) });
  }
};
