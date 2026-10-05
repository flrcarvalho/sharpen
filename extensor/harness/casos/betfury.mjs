// BetFury (BetBy / sptpub) — 5ª casa do motor, ESPELHO da Jonbet/Betboom/Blaze/Betpanda (s393).
//
// Não tem inject, formatador nem robô próprios: reusa `jb_inject.js`, `formatTicketJB` e
// `roboJBPassive`. Este caso prova que o mesmo inject engancha NA ABA desta casa e no host de
// API dela, que é o que muda de uma espelho para outra.
//
// O que sustenta o espelho, medido no recon (04/10/2026, Chrome, sem login):
//   • `betfury.com/sports` carrega `sports.betfury.ai/bt-renderer.min.js` NA PRÓPRIA página (sem iframe), e
//     `window.BTRenderer` existe no mundo da página;
//   • o tráfego sai em `api-g-c7818b61-607.sptpub.com` — MESMO hash de operador (`c7818b61`) das outras
//     BetBy, e o inject casa por PATH (`/my_bets/list`), nunca por host.
//
// ⚠ PROCEDÊNCIA: a casa entrou SEM conta de teste, então não há fixture DELA. Os bilhetes são
// os da Betpanda (`betpanda.my_bets.json`), servidos com o host e a aba desta casa — dito em
// voz alta em vez de fingir amostra. O caso NÃO cobre o dicionário de mercados nem a moeda da
// conta desta casa; a leitura fina de cada campo está provada em `betpanda.mjs`. Na 1ª
// captura real, troque a fixture pela da conta e leia os cards na tela.
import { rodarInject, carregarContent, fixture } from "../sandbox.mjs";

export const casa = "BETFURY";

const PAGINA_FALSA = 7;

export async function rodar() {
  const base = "https://api-g-c7818b61-607.sptpub.com/api/v1/my_bets/list";
  const todos = JSON.parse(fixture("betpanda.my_bets.json")).results;
  const err401 = fixture("jonbet.my_bets_401.json");
  let servidas = 0, negadas = 0;

  const responder = (url, opts) => {
    if (!/my_bets\/list/.test(url)) return null;
    if (!url.startsWith(base)) return null;   // o host DESTA casa, não o da Betpanda
    const h = (opts && opts.headers) || {};
    if (!(h.Authorization || h.authorization)) { negadas++; return err401; }
    servidas++;
    let skip = 0;
    try { skip = Number(new URL(url).searchParams.get("skip")) || 0; } catch (e) {}
    return JSON.stringify({ results: todos.slice(skip, skip + PAGINA_FALSA), count: todos.length });
  };

  const alvo = `${base}?currency=USD&lang=pt&limit=15&skip=0&status=&timestamp_from=&timestamp_to=`;
  const { ultima, urls } = await rodarInject({
    inject: "jb_inject.js",          // ← o MESMO das outras BetBy
    href: "https://betfury.com/sports",
    urlInicial: alvo,
    optsInicial: { method: "GET", headers: { "Content-Type": "application/json" } },
    urlsExtra: [{ url: alvo, opts: { method: "GET", headers: { "Content-Type": "application/json", Authorization: "Bearer harness.token.falso" } } }],
    pedido: "__sharpenupJBReq",
    responder,
  });

  const falhas = [];
  if (!ultima) return { falhas: ["o inject não emitiu nenhuma mensagem"], testes: 0 };
  if (!ultima.hook) falhas.push("o inject não emitiu `hook:true` (autodiagnóstico cego)");
  if (!ultima.fim) falhas.push("o inject não sinalizou `fim` (o robô ficaria esperando o teto)");

  const bilhetes = ultima.bilhetes || [];
  if (bilhetes.length !== todos.length) falhas.push(`esperava ${todos.length} bilhetes normalizados, vieram ${bilhetes.length}`);

  const fmt = carregarContent().pegar("formatTicketJB");
  let testes = 0;
  for (const b of bilhetes) {
    testes++;
    const txt = fmt(b);
    if (!txt.startsWith(`[Código: ${b.id}]`)) falhas.push(`${b.id}: marcador [Código:] ausente/errado`);
    if (!/^\d{19}$/.test(b.id)) falhas.push(`${b.id}: id fora do formato numérico de 19 dígitos do motor`);
  }

  if (servidas < 3) falhas.push(`o replay pediu só ${servidas} página(s) autenticada(s) no host desta casa`);
  if (!negadas) falhas.push("o corpo 401 nunca foi servido — a guarda do token não foi exercitada");
  if (negadas > 1) falhas.push(`${negadas} requisições sem Bearer — o replay está repaginando sem token`);
  if (urls.some((u) => !String(u).startsWith(base))) falhas.push("o replay saiu do host de API desta casa");
  return { falhas, testes };
}
