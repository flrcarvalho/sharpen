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
// boost/promoção, XMulti com perna anulada. A régua do dinheiro desses vai por CLONE abaixo. XHR
// também não. XMulti real: `xmulti()` no fim (s445).
//
// MUTAÇÃO INÓCUA registrada (s445): tirar o `byId.delete(outro)` do `guardar` do INJECT não quebra
// nada, porque o pedido do content limpa o lote e o replay sempre traz o histórico ANTES das
// abertas. Fica como defesa; quem precisa dele de verdade é o `_guardarSTC` do content, que
// acumula entre mensagens e está travado abaixo.
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
  testes += await xmulti(falhas, fmt);
  return { falhas, testes };
}

// XMulti (s445, crus reais da conta do Gabriel, `fixtures/stakecom.xmulti.json`). Até a 0.7.74
// toda `SportsbookXMultiBet` subia "a conferir" e a IA a deixava ABERTA para sempre: 15 múltiplas
// liquidadas na casa (14 perdidas, 1 ganha) apareciam como "atrasadas" e somavam ~700 USDT em
// aberto na Caixa. E a aberta de props/XMulti não traz `iid`: o código dela é o UUID (`bet.id`),
// e a liquidada volta com o número — duas linhas para uma aposta. Os números esperados abaixo
// são os da casa (`payout`, `_potentialMultiplier`, `result._status`), conferidos no cru.
async function xmulti(falhas, fmt) {
  const F = JSON.parse(fixture("stakecom.xmulti.json"));
  const { ultima } = await rodarInject({
    inject: "stc_inject.js", href: HOST + "/pt", semRequisicaoInicial: true, dom: DOM(COOKIE),
    pedido: "__sharpenupSTCReq", responder: casaSTC(F.settled, F.active, []), ms: 600,
  });
  const bs = (ultima && ultima.bilhetes) || [];
  const por = new Map(bs.map((b) => [b.id, b]));
  const ESP = {
    "689158437": { st: /^Perdeu → L$/, odd: "8,55631372", n: 3 },
    "689168071": { st: /^Ganhou → W \(retorno 377,89919511 USDT\)$/, odd: "9,44747988", n: 3 },
    "689759345": { st: /^Ganhou → W \(retorno 218,75 USDT\)$/, odd: "4,375", n: 2 },
    "689207229": { st: /^Perdeu → L$/, odd: "10,97827363", n: 3 },
  };
  for (const [cod, e] of Object.entries(ESP)) {
    const b = por.get(cod);
    if (!b) { falhas.push(`xmulti ${cod}: não chegou ao lote`); continue; }
    const txt = fmt(b);
    if (!e.st.test(linha(txt, "Status:"))) falhas.push(`xmulti ${cod}: status "${linha(txt, "Status:")}" (liquidada na casa)`);
    if (linha(txt, "Odd:") !== e.odd) falhas.push(`xmulti ${cod}: odd "${linha(txt, "Odd:")}", esperava ${e.odd}`);
    if (!/^Múltipla \(\d seleções em \d jogos; a odd é a do bilhete\)$/.test(linha(txt, "Tipo:"))) falhas.push(`xmulti ${cod}: tipo "${linha(txt, "Tipo:")}"`);
    const pernas = (txt.match(/^- /gm) || []).length;
    if (pernas !== e.n) falhas.push(`xmulti ${cod}: ${pernas} perna(s), esperava ${e.n}`);
    if (/\(sem seleção\)|\(sem jogador\)/.test(txt)) falhas.push(`xmulti ${cod}: perna sem seleção/jogador (o "Mercado Especial - REVISAR" da IA)`);
  }
  // As duas formas de perna, como a casa manda.
  const t1 = fmt(por.get("689207229") || {});
  if (!/^- 1ª parte - total: mais de 1\.5 \[perna perdida\]$/m.test(t1)) falhas.push("xmulti: perna comum (SportMarketOutcome) sem mercado/seleção/resultado");
  if (!/^- Props de jogador: Aaron Wiggins · rebounds · under 3\.5$/m.test(t1)) falhas.push("xmulti: perna de props (SwishMarketOutcome) fora do formato");
  // A aberta 18295be1-… é a MESMA aposta que a 689207229 (mesmo `bet.id`): a liquidada vence.
  if (por.has("18295be1-18c6-4fee-859d-00c401239fca")) falhas.push("xmulti: a aberta (UUID) foi ao lote junto com a liquidada da mesma aposta (bet.id)");
  if ((ultima.cru || []).some((c) => c.codigo === "18295be1-18c6-4fee-859d-00c401239fca")) falhas.push("xmulti: o cru da aberta gêmea subiu");
  // O content ACUMULA entre mensagens do inject: a aberta (UUID) pode ter chegado numa mensagem
  // anterior. As duas ordens, no `_guardarSTC` real.
  {
    const ct = carregarContent();
    const guardar = ct.pegar("_guardarSTC"), mapa = ct.pegar("stcById");
    const liq = por.get("689207229");
    const ab = { id: "18295be1-18c6-4fee-859d-00c401239fca", uid: liq && liq.uid, ativa: true, status: "confirmed" };
    guardar(ab); guardar(liq);
    if (mapa.has(ab.id) || !mapa.has("689207229")) falhas.push("content: a aberta (mensagem anterior) ficou ao lado da liquidada da mesma aposta");
    const ct2 = carregarContent();
    const g2 = ct2.pegar("_guardarSTC"), m2 = ct2.pegar("stcById");
    g2(liq); g2(ab);
    if (m2.has(ab.id) || !m2.has("689207229")) falhas.push("content: a aberta (mensagem posterior) entrou depois da liquidada da mesma aposta");
  }
  // A ordem inversa no inject: a PÁGINA pede as abertas primeiro (a aba Ativo); o pedido do content
  // limpa o lote e o replay traz histórico antes das abertas.
  {
    const { ultima: u2 } = await rodarInject({
      inject: "stc_inject.js", href: HOST + "/pt/my-bets/sports", dom: DOM(COOKIE),
      urlInicial: HOST + "/_api/v1/graphql",
      optsInicial: { method: "POST", headers: { "content-type": "application/json", "x-access-token": TOKEN },
                     body: JSON.stringify({ query: "query ActiveBets_User { user { activeSportBets { id } } }",
                                            variables: { limit: 50, offset: 0 } }) },
      pedido: "__sharpenupSTCReq", responder: casaSTC(F.settled, F.active, []), ms: 600,
    });
    const ids2 = ((u2 && u2.bilhetes) || []).map((b) => b.id);
    if (!ids2.includes("689207229")) falhas.push("xmulti (abertas antes): a liquidada não chegou");
    if (ids2.includes("18295be1-18c6-4fee-859d-00c401239fca")) falhas.push("xmulti (abertas antes): a aberta lida primeiro ficou no lote junto com a liquidada");
  }
  // A aberta de props sem gêmea fica, com o UUID como código (a casa não manda outro).
  const ab = por.get("fe2027a1-e340-4005-b0d9-85f90086db20");
  if (!ab || !ab.ativa) falhas.push("xmulti: a aberta de props sem gêmea sumiu");
  else if (!/^em aberto/.test(linha(fmt(ab), "Status:"))) falhas.push("xmulti: a aberta de props não saiu em aberto");
  // Cru da liquidada leva o `bet.id`: é por ele que o servidor adota a linha aberta antiga.
  const c = (ultima.cru || []).find((x) => x.codigo === "689207229");
  if (!c || c.cru.bet.id !== "18295be1-18c6-4fee-859d-00c401239fca") falhas.push("xmulti: o cru da liquidada perdeu o bet.id (o servidor não acha a aberta antiga)");
  // Perna anulada: a casa paga stake × payoutMultiplier (< odd cheia). Clone, sem amostra real.
  const w = por.get("689168071");
  if (w) {
    const s = linha(fmt(Object.assign({}, w, { retorno: 200, multPago: 5 })), "Status:");
    if (!/^Ganhou → W .*perna anulada; odd = retorno ÷ stake\)$/.test(s)) falhas.push(`xmulti: perna anulada não virou W pelo payoutMultiplier ("${s}")`);
    const s2 = linha(fmt(Object.assign({}, w, { retorno: 200, multPago: 9 })), "Status:");
    if (!/a conferir/.test(s2)) falhas.push("xmulti: retorno que não fecha nem com a odd nem com o payoutMultiplier não subiu a conferir");
  }
  // s451: a múltipla de PROPS (`SwishBet` de 3 pernas) também paga stake × payoutMultiplier com
  // perna anulada. Números do cru real 690343621 (Gabriel, 11/11): subia "a conferir" e ficava
  // aberta. A casa não marca qual perna caiu (`cancel` false nas três).
  {
    const perna = (j, e, l, o) => ({ status: "", anulada: 0, odd: o, jogador: j, estatistica: e, linha: l, lado: "under", jogo: "A - B" });
    const props = { id: "690343621", uid: "x", tipo: "SwishBet", status: "settled", ativa: false, moeda: "USDT",
                    stake: 70, retorno: 274.46288203255324, multPago: 3.9208983147507603, odd: 6.5742764, colocada: 1762894713,
                    pernas: [perna("Anthony Cirelli", "shots", 1.5, 1.9580967), perna("Logan Cooley", "shots", 2.5, 1.676727),
                             perna("Kel'el Ware", "rebounds", 8.5, 2.0024028)] };
    const s3 = linha(fmt(props), "Status:");
    if (!/^Ganhou → W .*perna anulada; odd = retorno ÷ stake\)$/.test(s3)) falhas.push(`props múltipla (690343621): perna anulada não virou W pelo payoutMultiplier ("${s3}")`);
    // Na SIMPLES de props o multiplicador é a própria odd: retorno fora dela continua a conferir.
    const simples = Object.assign({}, props, { pernas: props.pernas.slice(0, 1) });
    if (!/a conferir/.test(linha(fmt(simples), "Status:"))) falhas.push("props simples com retorno ≠ stake × odd virou W pelo payoutMultiplier");
  }
  return 1;
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
