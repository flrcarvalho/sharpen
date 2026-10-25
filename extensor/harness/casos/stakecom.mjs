// Stake.com (stake.com) — a Stake INTERNACIONAL. Captura por `POST /_api/v1/graphql`
// (`SportSportList` + `ActiveBets_User`). Recon s428 (25/10/2026), conta do Feca em USDT.
//
// ⚠ NÃO é a `Stake` (stake.bet.br, `casos/stake.mjs`): outro motor, outro id, outra moeda.
//
// FIXTURES: as respostas da casa às duas queries da PÁGINA, tiradas no mesmo minuto:
// `stakecom.settled.json` (15 liquidadas, todas props de jogador = `SwishBet`) e
// `stakecom.active.json` (3 abertas, `SportBet` de Fórmula 1). O `user` (id e nome da conta) foi
// trocado por um marcador; nada mais mexido.
//
// O que este caso trava, cada item cruzado com a aba Definido / Ativo de `/pt/my-bets/sports`:
//   • CÓDIGO = o número do `bet.iid` ("sport:676297455" → "ID da Aposta: 676.297.455" no modal).
//   • DINHEIRO: `amount` = "Aposta 75.00000000"; `payout` = "Pagamento" (o RETORNO).
//   • ODD: a do bilhete inteira (2,2716947); o card arredonda ("2,27").
//   • "Retirado" no card = status `cashout`, pagamento = stake (60,01) → V.
//   • COLOCAÇÃO = `createdAt` em São Paulo (15:58:11 GMT → "23/10/2026 às 12:58" no modal).
//   • REPLAY: token = cookie `session` (a frio) ou o header `x-access-token` da página;
//     `limit` acima de 50 devolve VAZIO sem erro (o replay nunca pede mais de 50).
//
// NÃO COBERTO (a conta não tinha): SportBet liquidada, cashout ≠ stake, cancelada, corrida,
// XMulti, boost/promoção. A régua do dinheiro desses vai por CLONE abaixo. XHR também não.
import { rodarInject, carregarContent, fixture, linha } from "../sandbox.mjs";

export const casa = "Stake.com";

const L = /^Perdeu → L$/;
const W = (r) => new RegExp("^Ganhou → W \\(retorno " + r.replace(/[.,]/g, "\\$&") + " USDT\\)$");
const ABERTA = /^em aberto \(aguardando resultado — NÃO liquidar; sem resultado\)$/;

const ESPERADO = {
  "676297455": { st: L, odd: "2,2716947", stake: "75,00", tipo: /^Simples \(props de jogador\)$/, col: "23/10/2026 12:58:11",
                 perna: /^- Props de jogador: Matisse Thybulle · rebounds · over 2\.5 \[perna perdida\]$/m },
  "676299526": { st: W("44,943819"), odd: "1,4981273", stake: "30,00", tipo: /^Simples/ },
  "675668548": { st: /^Retorno = stake \(60,01 USDT, status cashout\) → V$/, odd: "1,6747613", stake: "60,01", tipo: /^Simples/ },
  "674734395": { st: W("178,73134626"), odd: "2,2341418", stake: "80,00", tipo: /^Múltipla \(2 seleções em 2 jogos\)$/ },
  "674775479": { st: L, odd: "2,45", stake: "40,01", tipo: /^Criar Aposta \/ mesmo jogo \(2 seleções/ },
  "674778558": { st: L, odd: "6,027", stake: "20,01", tipo: /^Múltipla \(4 seleções em 2 jogos; com Criar Aposta dentro/ },
  "678433549": { st: ABERTA, odd: "21", stake: "30,00", tipo: /^Simples$/, pot: "630,00 USDT",
                 perna: /^- Grande Prémio dos Estados Unidos Corrida - Primeiro Piloto a Efetuar uma Pit Stop: Hamilton, Lewis \[perna aberta\]$/m },
};

const HOST = "https://stake.com";
const TOKEN = "harness-sessao-falsa-stakecom";
const COOKIE = "locale=pt; session=" + TOKEN + "; oddsFormat=decimal";

const HIST = () => JSON.parse(fixture("stakecom.settled.json"));
const ATIV = () => JSON.parse(fixture("stakecom.active.json"));
const LISTAS = ["activeSportBets", "activeSwishBetList", "activeRacingBets", "activeSportsbookXMultiBetList"];

// A casa como medida: `limit` > 50 devolve VAZIO, sem token devolve `user: null` com erro.
function casaSTC(hist, abertas, registro) {
  return (url, opts) => {
    if (!/\/_api\/v1\/graphql$/.test(new URL(String(url)).pathname)) return null;
    const h = (opts && opts.headers) || {};
    const tok = h["x-access-token"] || h["X-Access-Token"] || "";
    let body = {};
    try { body = JSON.parse((opts && opts.body) || "{}"); } catch (e) {}
    const v = body.variables || {};
    const q = String(body.query || "");
    const op = (q.match(/query (\w+)/) || [])[1];
    registro.push({ op, limit: v.limit, offset: v.offset, status: v.status, tok });
    if (tok !== TOKEN) return JSON.stringify({ errors: [{ message: "unauthenticated" }], data: { user: null } });
    const lim = v.limit > 50 ? 0 : v.limit, off = v.offset || 0;
    const u = { __typename: "User", id: "x" };
    if (/sportBetList/.test(q)) u.sportBetList = hist.slice(off, off + lim);
    else for (const k of LISTAS) u[k] = (abertas[k] || []).slice(off, off + lim);
    return JSON.stringify({ data: { user: u } });
  };
}

const DOM = (cookie) => ({ cookie, querySelector: () => null, querySelectorAll: () => [] });

export async function rodar() {
  const hist = HIST().data.user.sportBetList, ativ = ATIV().data.user;
  const registro = [];
  const { ultima, mensagens } = await rodarInject({
    inject: "stc_inject.js", href: HOST + "/pt/sports/home", semRequisicaoInicial: true, dom: DOM(COOKIE),
    pedido: "__sharpenupSTCReq", responder: casaSTC(hist, ativ, registro), ms: 600,
  });

  const falhas = [];
  if (!ultima) return { falhas: ["o inject não emitiu nenhuma mensagem"], testes: 0 };
  if (!ultima.hook) falhas.push("o inject não emitiu `hook:true`");
  if (!ultima.fim) falhas.push("o inject não sinalizou `fim`");
  if (ultima.erro) falhas.push("erro no replay: " + ultima.erro);
  if (JSON.stringify(mensagens).includes(TOKEN)) falhas.push("o token vazou na mensagem para o content");
  if (registro.some((r) => r.tok !== TOKEN)) falhas.push("o replay não levou o token do cookie");
  if (registro.some((r) => !(r.limit <= 50))) falhas.push("o replay pediu mais de 50 (a casa devolve VAZIO, sem erro)");
  const h1 = registro.find((r) => r.op === "SportSportList");
  if (!h1 || !Array.isArray(h1.status) || !h1.status.includes("cashout") || !h1.status.includes("cancelled")) falhas.push("o histórico não pediu os status da página (cashout, cancelled…)");
  if (!registro.some((r) => r.op === "ActiveBets_User")) falhas.push("o replay não pediu as abertas");

  const bilhetes = ultima.bilhetes || [];
  if (bilhetes.length !== 18) falhas.push(`esperava 18 bilhetes (15 + 3), vieram ${bilhetes.length}`);
  const cru = ultima.cru || [];
  if (cru.length !== 18) falhas.push(`cru: esperava 18, vieram ${cru.length}`);
  if (cru.some((c) => !c.cru || !c.cru.bet || "user" in c.cru.bet)) falhas.push("cru com o `user` (nome da conta) ou sem a aposta");
  if (cru.some((c) => c.cru.iid !== "sport:" + c.codigo)) falhas.push("cru sem o `iid` do código (a props não traz `bet.iid`; sem ele a Ficha fica sem código)");

  const fmt = carregarContent().pegar("formatTicketSTC");
  const porId = new Map(bilhetes.map((b) => [b.id, b]));
  let testes = 0;
  for (const b of bilhetes) {
    const txt = fmt(b);
    if (!txt.startsWith(`[Código: ${b.id}]`)) falhas.push(`${b.id}: marcador [Código:] ausente/errado`);
    if (!/^\d{9}$/.test(b.id)) falhas.push(`${b.id}: código fora do número de 9 dígitos do card`);
    if (linha(txt, "Moeda:") !== "USDT") falhas.push(`${b.id}: faltou "Moeda: USDT"`);
    if (/R\$/.test(txt)) falhas.push(`${b.id}: "R$" numa conta em USDT`);
    if (/a conferir/.test(linha(txt, "Status:"))) falhas.push(`${b.id}: a conta inteira tem resultado provado, veio "${linha(txt, "Status:")}"`);
    if (!/^Data \(evento mais recente\): \d\d\/\d\d\/\d{4} /m.test(txt)) falhas.push(`${b.id}: sem data de evento`);
  }
  for (const [idb, e] of Object.entries(ESPERADO)) {
    const b = porId.get(idb);
    if (!b) { falhas.push(`${idb}: não chegou ao lote`); continue; }
    const txt = fmt(b);
    testes++;
    if (!e.st.test(linha(txt, "Status:"))) falhas.push(`${idb}: status "${linha(txt, "Status:")}"`);
    if (linha(txt, "Odd:") !== e.odd) falhas.push(`${idb}: odd esperada ${e.odd}, veio "${linha(txt, "Odd:")}"`);
    if (linha(txt, "Stake:") !== e.stake) falhas.push(`${idb}: stake esperada ${e.stake}, veio "${linha(txt, "Stake:")}"`);
    if (!e.tipo.test(linha(txt, "Tipo:"))) falhas.push(`${idb}: tipo "${linha(txt, "Tipo:")}"`);
    if (e.col && linha(txt, "Data (colocação):") !== e.col) falhas.push(`${idb}: colocação "${linha(txt, "Data (colocação):")}"`);
    if (e.pot && linha(txt, "Retorno potencial (se ganhar):") !== e.pot) falhas.push(`${idb}: potencial "${linha(txt, "Retorno potencial (se ganhar):")}"`);
    if (e.perna && !e.perna.test(txt)) falhas.push(`${idb}: a perna não saiu como no card`);
  }

  // Dinheiro sem amostra: clone, só o que o número prova vira resultado.
  {
    const base = porId.get("676297455");     // 75 @ 2,2716947, perdida
    const c = (o) => linha(fmt(Object.assign({}, base, o)), "Status:");
    if (!/→ W \(odd = retorno ÷ stake/.test(c({ status: "cashout", retorno: 90 }))) falhas.push("cashout ≠ stake não virou W pela regra do MASTER §5.6");
    if (!/→ V$/.test(c({ status: "cancelled", retorno: 75 }))) falhas.push("cancelada não virou V");
    if (!/a conferir/.test(c({ retorno: 100 }))) falhas.push("retorno que não fecha com a odd não subiu a conferir");
    if (!/a conferir/.test(c({ tipo: "RacingBet" }))) falhas.push("corrida sem amostra não subiu a conferir");
    if (!/a conferir/.test(c({ promocao: true }))) falhas.push("promoção/boost sem amostra não subiu a conferir");
    if (!/a conferir/.test(c({ cashoutParcial: true }))) falhas.push("cashout parcial não subiu a conferir");
    if (!/deixe a odd VAZIA/.test(linha(fmt(Object.assign({}, base, { odd: 0 })), "Odd:"))) falhas.push("odd 0 não virou ausência");
  }

  testes += await paginacao(falhas, hist);
  testes += await semSessao(falhas, hist, ativ);
  testes += await aprendido(falhas, hist, ativ);
  testes += await liquidadaVence(falhas, hist);
  return { falhas, testes };
}

// 45 liquidadas em páginas de 20: 3 pedidos exatos (20, 20, 5), o último menor = fim.
async function paginacao(falhas, hist) {
  const lista = [];
  for (let i = 0; i < 45; i++) {
    const x = JSON.parse(JSON.stringify(hist[i % hist.length]));
    x.iid = "sport:" + (700000000 + i);
    x.bet.id = "id-" + i;
    lista.push(x);
  }
  const registro = [];
  const { ultima } = await rodarInject({
    inject: "stc_inject.js", href: HOST + "/pt", semRequisicaoInicial: true, dom: DOM(COOKIE),
    pedido: "__sharpenupSTCReq", responder: casaSTC(lista, {}, registro), ms: 600,
  });
  const n = ((ultima && ultima.bilhetes) || []).length;
  if (n !== 45) falhas.push(`paginação: esperava 45, vieram ${n}`);
  const offs = registro.filter((r) => r.op === "SportSportList").map((r) => r.offset).join(",");
  if (offs !== "0,20,40") falhas.push(`paginação: offsets ${offs}, esperava 0,20,40`);
  return 1;
}

// Sem sessão: nada no cookie, nenhuma chamada. Diz `semToken` e não pede nada.
async function semSessao(falhas, hist, ativ) {
  const registro = [];
  const { ultima } = await rodarInject({
    inject: "stc_inject.js", href: HOST + "/pt", semRequisicaoInicial: true, dom: DOM("locale=pt"),
    pedido: "__sharpenupSTCReq", responder: casaSTC(hist, ativ, registro), ms: 300,
  });
  if (!ultima || !ultima.semToken) falhas.push("sem sessão: o inject não disse `semToken`");
  if (registro.length) falhas.push("sem sessão: o inject pediu a lista");
  // Sessão vencida: a casa responde erro + `user: null` → erro dito, nunca "0 bilhetes" mudo.
  const { ultima: u2 } = await rodarInject({
    inject: "stc_inject.js", href: HOST + "/pt", semRequisicaoInicial: true, dom: DOM("session=vencida"),
    pedido: "__sharpenupSTCReq", responder: casaSTC(hist, ativ, []), ms: 300,
  });
  if (!(u2 && /unauthenticated/.test(u2.erro || ""))) falhas.push(`sessão vencida não virou erro (veio "${u2 && u2.erro}")`);
  return 1;
}

// Sem cookie: o token vem do header que a PÁGINA mandou.
async function aprendido(falhas, hist, ativ) {
  const { ultima } = await rodarInject({
    inject: "stc_inject.js", href: HOST + "/pt/my-bets/sports", dom: DOM("locale=pt"),
    urlInicial: HOST + "/_api/v1/graphql",
    optsInicial: { method: "POST", headers: { "content-type": "application/json", "x-access-token": TOKEN },
                   body: JSON.stringify({ query: "query ActiveBetCount_User { user { id } }", variables: {} }) },
    pedido: "__sharpenupSTCReq", responder: casaSTC(hist, ativ, []), ms: 600,
  });
  const n = ((ultima && ultima.bilhetes) || []).length;
  if (n !== 18) falhas.push(`token aprendido da página: esperava 18, vieram ${n}`);
  return 1;
}

// O mesmo bilhete aberto e liquidado no mesmo lote: a liquidada vence, em qualquer ordem.
async function liquidadaVence(falhas, hist) {
  const liq = hist.find((x) => x.iid === "sport:676299526");          // ganha, 44,943819
  const aberta = JSON.parse(JSON.stringify(liq.bet));
  aberta.active = true; aberta.status = "confirmed"; aberta.payout = 0; aberta.bet = { iid: liq.iid };
  const { ultima } = await rodarInject({
    inject: "stc_inject.js", href: HOST + "/pt", semRequisicaoInicial: true, dom: DOM(COOKIE),
    pedido: "__sharpenupSTCReq", responder: casaSTC([liq], { activeSwishBetList: [aberta] }, []), ms: 600,
  });
  const b = ((ultima && ultima.bilhetes) || []).find((x) => x.id === "676299526");
  if (!b || b.ativa || b.status !== "settled") falhas.push("a aberta (lida depois) apagou a liquidada do mesmo código");
  return 1;
}
