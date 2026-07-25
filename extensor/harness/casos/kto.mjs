// KTO (Kambi) — captura por API `/coupon/history.json` (s192).
//
// Trava as 6 leituras que custaram a sessão inteira para descobrir, cruzando o JSON com o
// que o próprio card da KTO renderiza:
//   • `betOdds` vem 0 em TODA perdida → a odd nunca pode sair dele (cupom 12886338194: o
//     site mostra 6.00 e o campo diz 0).
//   • stake/odd/line em MILÉSIMOS (stake 600000 = R$600,00).
//   • ODDÃO+ tem 2 naturezas (ODDS_BOOST sobe a odd · PROFIT_BOOST sobe o lucro X%) e
//     `payout ÷ stake` resolve as duas — que é a regra global do W.
//   • odd declarada é truncada em 3 casas pela Kambi e o retorno é arredondado ao centavo:
//     a declarada vence SE explicar o retorno até o centavo, senão o dinheiro manda.
//   • aberta usa `potentialPayout ÷ stake` (2,0435), mais preciso que betOdds (2,043).
//   • data UTC → America/Sao_Paulo (sem isso o cupom pula de dia).
import { rodarInject, carregarContent, fixture, linha } from "../sandbox.mjs";

export const casa = "KTO";

const ESPERADO = {
  "12939510404": { odd: "2,0435", status: /em aberto/,    tipo: /Múltipla \(3 seleções\)/,                data: "25/07/2026 01:12:03" },
  "12886338194": { odd: "6",      status: /^Perdeu → L$/, tipo: /Simples/,                                data: "09/07/2026 17:16:09" },
  "12886595322": { odd: "2,15",   status: /^Ganho → W/,   tipo: /Simples/,                                data: "09/07/2026 18:04:20" },
  "12886593360": { odd: "2,3226", status: /^Ganho → W/,   tipo: /Simples/,                                data: "09/07/2026 18:04:09" },
  "12864726191": { odd: "2",      status: /^Ganho → W/,   tipo: /Simples/,                                data: "05/07/2026 12:17:44" },
  "12885883904": { odd: "2,2",    status: /^Ganho → W/,   tipo: /Bet Builder \(mesmo jogo · 3 seleções\)/, data: "09/07/2026 16:43:08" },
};

export async function rodar() {
  const corpo = fixture("kto.history.json");
  const base = "https://cf-al-auth-api.kambicdn.com/player/api/v2019/ktobr/coupon/history.json";

  const { ultima, urls } = await rodarInject({
    inject: "kto_inject.js",
    href: "https://www.kto.bet.br/app/esportes/historico-de-apostas",
    urlInicial: `${base}?lang=pt_BR&range_size=100&range_start=0&status=SETTLED`,
    pedido: "__sharpenupKTOReq",
    // A fixture responde `range.more:false` → o replay encerra em 1 página por URL.
    responder: (url) => (url.includes("/coupon/history.json") ? corpo : null),
  });

  const falhas = [];
  if (!ultima) return { falhas: ["o inject não emitiu nenhuma mensagem"], testes: 0 };
  if (!ultima.fim) falhas.push("o inject não sinalizou `fim` (o robô ficaria esperando o teto)");
  if (urls.length < 2) falhas.push(`replay não repaginou (só ${urls.length} requisição)`);

  const cupons = ultima.cupons || [];
  if (cupons.length !== 6) falhas.push(`esperava 6 cupons normalizados, vieram ${cupons.length}`);

  const fmt = carregarContent().pegar("formatTicketKTO");
  let testes = 0;
  for (const c of cupons) {
    const e = ESPERADO[c.ref];
    if (!e) { falhas.push(`cupom inesperado na fixture: ${c.ref}`); continue; }
    const txt = fmt(c);
    testes++;
    if (!txt.startsWith(`[Código: ${c.ref}]`)) falhas.push(`${c.ref}: marcador [Código:] ausente/errado`);
    const odd = linha(txt, "Odd:");
    const status = linha(txt, "Status:");
    const tipo = linha(txt, "Tipo:");
    const data = linha(txt, "Data (colocação):");
    if (odd !== e.odd) falhas.push(`${c.ref}: odd esperada ${e.odd}, veio "${odd}"`);
    if (!e.status.test(status)) falhas.push(`${c.ref}: status "${status}"`);
    if (!e.tipo.test(tipo)) falhas.push(`${c.ref}: tipo "${tipo}"`);
    if (data !== e.data) falhas.push(`${c.ref}: data esperada ${e.data}, veio "${data}"`);
  }
  return { falhas, testes };
}
