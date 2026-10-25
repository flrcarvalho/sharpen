// 20bet (20betz0ne1.com) — ESPELHO da Vave: plataforma própria `softlabs`, a mesma API
// `GET platform.<host>/api/v2/bet/history`, o mesmo `vv_inject.js` e o mesmo `formatTicketVV`.
// Recon s428, conta do Gabriel aberta no Chrome do Feca (USD), pelo navegador dele.
//
// PROVA DO MOTOR (s428): a home carrega `platform.20betz0ne1.com/api/v2/…`, o histórico responde
// ao mesmo Bearer de `localStorage.customer.token`, e a UNIÃO DE CHAVES do payload real dá 167
// chaves, ZERO nova contra a fixture da Vave. O que separa as duas é só o domínio — e, como a
// Vave, a 20bet roda em domínio NUMERADO (`20betz0ne1.com`).
//
// A FIXTURE `20bet.history.json` é a resposta da casa ao replay (3 anos, limit 100): a conta
// INTEIRA no dia do recon, 12 bilhetes, em USD. Só o `userId` foi zerado. `20bet.dicionarios.json`
// é o recorte dos dois dicionários públicos da casa em `/pt` (que nesta casa vêm em PORTUGUÊS, a
// Vave os servia em inglês), só com os ids que a fixture usa.
//
// O que este caso trava, cada item cruzado com o card da casa (Betting history, 25/10/2026):
//   • CÓDIGO = `id` (o "#68651106" do card), 8 dígitos — o mesmo número dos 57 bilhetes que a
//     base já tinha por print. DATA DO CARD = `ts` em São Paulo (1792795306 → "23.10.2026, 19:41").
//   • ODD = `value` (7,36 = 1,63 × 2,15 × 2,1, a perna devolvida conta no card pela odd cheia).
//   • PERNA: `details[].status` 1 = Lost, 2 = Won, 3 = Returned, 0 = Pending — 68651106 mostra as
//     três primeiras no card, NESTA ordem.
//   • ABERTA: status 0, "Win amount" do card = `taxesData.potentialWinAmount` (POTENCIAL).
//   • BET BUILDER: "Single bet · Bet builder" no card, UMA perna com mercado "BetBuilder" e as
//     seleções do cupom em `betBetBuilderLegs` (o card lista as duas de 68724463).
//
// NÃO COBERTO pela fixture (a conta não tinha): ganha, devolvida no bilhete inteiro, cashout,
// freebet e sistema — os casos de dinheiro estão travados no `vave.mjs`, que roda o MESMO
// formatador. O caminho XHR do inject também não: o sandbox entrega a requisição da página por
// fetch.
import { rodarInject, carregarContent, fixture, linha } from "../sandbox.mjs";

export const casa = "20bet";

const L = /^Perdeu → L$/;
const ABERTA = /^em aberto \(aguardando resultado — NÃO liquidar; sem resultado\)$/;
const M3 = /^Múltipla \(3 seleções\)$/;
const BB = /^Criar Aposta \/ mesmo jogo \(1 seleções; a odd é a do conjunto\)$/;

// id → o que o card mostra. `col` = data do card (colocação).
const ESPERADO = {
  "68724463": { st: ABERTA, odd: "4,33",  stake: "20,01",  tipo: BB, col: "25/10/2026 13:21:25", pot: "86,64 USD" },
  "68722991": { st: ABERTA, odd: "10,19", stake: "25,00",  tipo: M3, col: "25/10/2026 12:56:35", pot: "254,75 USD" },
  "68718582": { st: L,      odd: "11,25", stake: "25,00",  tipo: M3, col: "25/10/2026 11:17:06" },
  "68651558": { st: L,      odd: "2,5",   stake: "100,00", tipo: BB, col: "23/10/2026 19:57:44" },
  "68651106": { st: L,      odd: "7,36",  stake: "25,00",  tipo: M3, col: "23/10/2026 19:41:46" },
  "68649008": { st: L,      odd: "17",    stake: "20,01",  tipo: BB, col: "23/10/2026 18:26:07" },
};

const HOST = "https://20betz0ne1.com";
const API = "https://platform.20betz0ne1.com";
const TOKEN = "harness.token.falso.20bet";
const HDRS = { accept: "application/json", "content-type": "application/json",
               authorization: "Bearer " + TOKEN, "client-timezone": "America/Sao_Paulo" };

const HIST = () => JSON.parse(fixture("20bet.history.json"));
const DIC = () => JSON.parse(fixture("20bet.dicionarios.json"));

// A casa como medida: `page`/`limit`, `total` em PÁGINAS, erro com HTTP 200.
function casa20(bets, registro) {
  const tabelas = HIST().data.bets;
  const dic = DIC();
  return (url, opts) => {
    if (!String(url).startsWith(API)) return null;
    const u = new URL(String(url));
    const h = (opts && opts.headers) || {};
    const auth = h.authorization || h.Authorization || "";
    registro.push({ p: u.pathname, q: Object.fromEntries(u.searchParams), auth });
    if (/get-all-markets/.test(u.pathname)) return JSON.stringify(dic.markets);
    if (/get-all-outcomes/.test(u.pathname)) return JSON.stringify(dic.outcomes);
    if (u.pathname !== "/api/v2/bet/history") return JSON.stringify({ status: "ok", code: 200, data: {} });
    if (auth !== "Bearer " + TOKEN) return JSON.stringify({ status: "error", data: { messages: ["login"] }, code: 401 });
    const limit = Number(u.searchParams.get("limit") || 10);
    const page = Number(u.searchParams.get("page") || 1);
    return JSON.stringify({ status: "ok", code: 200, data: {
      bets: Object.assign({}, tabelas, { bets: bets.slice((page - 1) * limit, page * limit) }),
      columns: [], limit, page: String(page), total: Math.ceil(bets.length / limit) } });
  };
}

const LS = (tok) => ({ localStorage: { getItem: (k) => (k === "customer" && tok ? JSON.stringify({ id: 1, token: tok }) : null) } });

export async function rodar() {
  const bets = HIST().data.bets.bets;
  const registro = [];
  // A frio, como a casa nova chega: o popup injeta tarde, a página já fez as chamadas dela.
  const { ultima } = await rodarInject({
    inject: "vv_inject.js", href: HOST + "/cabinet/betting-history",
    semRequisicaoInicial: true, janelaExtra: LS(TOKEN),
    pedido: "__sharpenupVVReq", responder: casa20(bets, registro), ms: 600,
  });

  const falhas = [];
  if (!ultima) return { falhas: ["o inject não emitiu nenhuma mensagem"], testes: 0 };
  if (!ultima.hook) falhas.push("o inject não emitiu `hook:true`");
  if (!ultima.fim) falhas.push("o inject não sinalizou `fim`");
  if (ultima.semDicionario) falhas.push("o dicionário de mercados não carregou");
  // A API mora em `platform.` do host da ABA — nada fixa o domínio da Vave.
  if (!registro.some((r) => r.p === "/api/v2/bet/history")) falhas.push("o replay não chamou platform.<host da aba>");
  if (registro.some((r) => r.p === "/api/v2/bet/history" && r.auth !== "Bearer " + TOKEN)) falhas.push("o replay não levou o Bearer do localStorage");

  const bilhetes = ultima.bilhetes || [];
  if (bilhetes.length !== bets.length) falhas.push(`esperava ${bets.length} bilhetes, vieram ${bilhetes.length}`);
  const cru = ultima.cru || [];
  if (cru.length !== bets.length) falhas.push(`cru: esperava ${bets.length} itens, vieram ${cru.length}`);
  if (cru.some((c) => !c.cru || !c.cru.dicionario || "userId" in (c.cru.bet || {}))) falhas.push("cru sem dicionário ou com o `userId`");

  const fmt = carregarContent().pegar("formatTicketVV");
  const porId = new Map(bilhetes.map((b) => [b.id, b]));
  let testes = 0;

  for (const b of bilhetes) {
    const txt = fmt(b);
    if (!txt.startsWith(`[Código: ${b.id}]`)) falhas.push(`${b.id}: marcador [Código:] ausente/errado`);
    if (!/^\d{8}$/.test(b.id)) falhas.push(`${b.id}: código fora da série de 8 dígitos do card`);
    if (linha(txt, "Moeda:") !== "USD") falhas.push(`${b.id}: faltou a linha "Moeda: USD"`);
    if (/R\$/.test(txt)) falhas.push(`${b.id}: o bloco diz "R$" numa conta em USD`);
    if (/\{[^}]*\}/.test(txt)) falhas.push(`${b.id}: template da casa sem resolver no bloco`);
    if (/sem nome/.test(txt)) falhas.push(`${b.id}: perna sem nome de mercado`);
    if (/\[perna status /.test(txt)) falhas.push(`${b.id}: perna com status cru (todos os medidos têm nome)`);
  }

  for (const [idb, e] of Object.entries(ESPERADO)) {
    const b = porId.get(idb);
    if (!b) { falhas.push(`${idb}: não chegou ao lote`); continue; }
    const txt = fmt(b);
    testes++;
    const st = linha(txt, "Status:");
    if (!e.st.test(st)) falhas.push(`${idb}: status "${st}"`);
    if (linha(txt, "Odd:") !== e.odd) falhas.push(`${idb}: odd esperada ${e.odd}, veio "${linha(txt, "Odd:")}"`);
    if (linha(txt, "Stake:") !== e.stake) falhas.push(`${idb}: stake esperada ${e.stake}, veio "${linha(txt, "Stake:")}"`);
    if (!e.tipo.test(linha(txt, "Tipo:"))) falhas.push(`${idb}: tipo "${linha(txt, "Tipo:")}"`);
    if (linha(txt, "Data (colocação):") !== e.col) falhas.push(`${idb}: colocação esperada ${e.col}, veio "${linha(txt, "Data (colocação):")}"`);
    if (e.pot && linha(txt, "Retorno potencial (se ganhar):") !== e.pot) falhas.push(`${idb}: potencial esperado ${e.pot}`);
    if (e.pot && /^Retorno:/m.test(txt)) falhas.push(`${idb}: aberta com linha "Retorno:"`);
  }

  // A múltipla de 68651106 do card: Lost · Returned · Won, nesta ordem.
  {
    const txt = fmt(porId.get("68651106") || {});
    const est = (txt.match(/\[perna (\w+)\]/g) || []).join(",");
    if (est !== "[perna perdida],[perna devolvida],[perna ganha]") falhas.push(`68651106: pernas "${est}", o card mostra Lost · Returned · Won`);
    if (!/^- Handicap: Club Atletico Ituzaingo \(\+1\) \[perna perdida\]$/m.test(txt)) falhas.push("68651106: `({+hcp})` com hcp=1 não virou \"(+1)\" como no card");
    if (!/^- 1st quarto - 1x2: Hsinchu Lioneers \[perna devolvida\]$/m.test(txt)) falhas.push("68651106: o 1x2 do 1º quarto não saiu como o dicionário da casa escreve");
  }
  // Bet Builder: as duas seleções do card, com o texto da casa.
  {
    const txt = fmt(porId.get("68724463") || {});
    if (!/^Seleções do Criar Aposta \(texto da casa\):$/m.test(txt)) falhas.push("68724463: faltou a lista de seleções do Bet Builder");
    if (!/^ {4}· Ressaltos do jogador - Josh Hart 10\+ \(Partida\)$/m.test(txt) || !/^ {4}· Pontos do jogador - Josh Hart 10\+ \(Partida\)$/m.test(txt)) falhas.push("68724463: as duas seleções do card não estão no bloco");
    if (!/^- BetBuilder: BetBuilder \[perna aberta\]$/m.test(txt)) falhas.push("68724463: a perna única do Bet Builder não saiu");
  }
  // TAB na seleção do Bet Builder some NA ENTRADA (TAB é coluna do TSV).
  {
    const sujos = HIST().data.bets.bets.map((x) => x.id === 68649008 ? Object.assign({}, x, { betBetBuilderLegs: ["Pontos\t\tdo jogador  - X"] }) : x);
    const { ultima: u2 } = await rodarInject({
      inject: "vv_inject.js", href: HOST + "/cabinet/betting-history",
      semRequisicaoInicial: true, janelaExtra: LS(TOKEN),
      pedido: "__sharpenupVVReq", responder: casa20(sujos, []), ms: 600,
    });
    const b = ((u2 && u2.bilhetes) || []).find((x) => x.id === "68649008");
    if (!b || JSON.stringify(b.legsBB) !== JSON.stringify(["Pontos do jogador - X"])) falhas.push(`TAB na seleção do Bet Builder não foi limpo na entrada (${JSON.stringify(b && b.legsBB)})`);
    testes++;
  }
  return { falhas, testes };
}
