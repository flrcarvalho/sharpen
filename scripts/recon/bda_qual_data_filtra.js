// Qual data o filtro `after-day`/`before-day` do Exchange da Bolsa/Betbra usa?
// Colocacao, evento ou liquidacao? A resposta decide se uma janela curta de recaptura
// perde a aposta antiga que liquidou hoje.
//
// COMO RODAR: F12 na aba da Bolsa de Aposta, com a tela do Exchange aberta.
// No seletor de contexto do Console (o dropdown que costuma dizer "top"), escolha o
// frame `mexchange2.bolsadeaposta.bet.br`. Cole isto e de Enter.
//
// O bilhete usado e real e ja esta na base: colocado em 31/12/2025, evento em 03/01/2026.
(async () => {
  const ALVO = "47658074";                 // colocacao 31/12/2025 · evento 03/01/2026
  const base = "https://mexchange-api." + location.host.replace(/^mexchange\d*\./i, "")
             + "/api/offers/reportsv2";
  const tz = String(new Date().getTimezoneOffset());

  async function janela(de, ate) {
    const q = new URLSearchParams({ offset: "0", "per-page": "500",
      "after-day": de, "before-day": ate, "timezone-offset": tz });
    const r = await fetch(base + "?" + q, { credentials: "include" });
    if (!r.ok) return { erro: "HTTP " + r.status };
    const j = await r.json();
    const ofertas = j.offers || [];
    const achou = ofertas.find(o => String(o.id) === ALVO);
    return {
      total: j.total, veio: ofertas.length, achou: !!achou,
      // Para ler a cara da janela: o intervalo de datas que ela devolveu.
      colocadas: ofertas.length ? [ofertas[ofertas.length-1]["created-at"], ofertas[0]["created-at"]] : null,
    };
  }

  const dez = await janela("2025-12-30", "2026-01-01");   // so a COLOCACAO cai aqui
  const jan = await janela("2026-01-02", "2026-01-04");   // so o EVENTO cai aqui
  console.log("janela da COLOCACAO (30/12→01/01):", dez);
  console.log("janela do EVENTO    (02/01→04/01):", jan);
  console.log(dez.achou && !jan.achou ? ">>> filtra por COLOCACAO"
            : jan.achou && !dez.achou ? ">>> filtra por EVENTO (ou liquidacao)"
            : dez.achou && jan.achou  ? ">>> aparece nas duas — o filtro e por outra data, medir mais"
            : ">>> nao apareceu em nenhuma — confira se o bilhete e desta casa/conta");
})();
