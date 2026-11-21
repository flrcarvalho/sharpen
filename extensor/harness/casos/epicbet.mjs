// EpicBet (plataforma PRÓPRIA, `epicbet.com`, API tRPC) — s462.
//
// O que o recon mediu (21/11/2026, Chrome do Feca, conta logada, painel "My Bets"):
//   • A lista sai de `GET /s/sport-bet/user/ticket.listWithMatchInfo?input=<JSON>`, com
//     `input = {limit, offset, language, filter}`, só com o COOKIE (medido com `fetch` cru).
//     Resposta tRPC: `{result: {data: {tickets: [...], count}}}`, mais recente primeiro.
//   • `filter` é OBRIGATÓRIO e só aceita `pending` ou `settled` (sem ele, ou com `all`, a API
//     devolve 400 `invalid_union`). O inject pede as duas listas.
//   • `limit` MÁXIMO 25 (com 50 a API devolve 400 `too_big`). A tela pede 3 por página e anda
//     por botões 1-2-3-4: ela nunca baixa a lista inteira.
//   • FIM: `count` é o total da lista. Offset além do fim devolve `tickets: []` (não repete a
//     página 1, ao contrário da CopaWin).
//   • A fixture é a resposta inteira das duas listas (SHA-256 conferido com o da aba), com o
//     `walletId` trocado por 1. 13 bilhetes, TODOS múltiplas de 3 pernas, em USDT: 2 abertas
//     (uma com perna `pushed`), 2 ganhas, 9 perdidas (uma com perna `half_won`).
//
// PROCEDÊNCIA DOS VALORES ESPERADOS: o CARD da tela, lido nos 13 bilhetes em 21/11/2026
// (rótulo WON/LOST, "Odds", "Stake", "Payout", o "ID" do card, o dia do agrupamento e o
// horário de cada perna, que o card mostra em Brasília). A hora da colocação não aparece no
// card (só o dia): ela vem do JSON (`createdAt`, UTC), marcado `col: json` com o dia do card.
//
// AS ARMADILHAS QUE ESTE CASO TRAVA
//
// 1. NÃO HÁ CAMPO DE RETORNO. O "Payout" do card é `stake × odds` (40 × 7,14 = 285,6 no
//    ID 11; 0 na perdida). O W sai daí, e só com as provas: status `won`, toda perna `won`,
//    sem cashout e sem boost.
// 2. `bet.odds` JÁ É A ODD EFETIVA. Perna `pushed` (ID 12: 1,97 × 3,32 × 1,85 = 12,10, card
//    "6.14") e perna `half_won` (ID 7: card "5.87" = 1,765 × 1,87 × 1,78) já entram recalculadas.
//    A odd do bloco é a do card, nunca o produto das pernas.
// 3. O "ID" DO CARD É O `sequence` (1, 2, 3… por conta), não o `bet.id`. O CÓDIGO é o
//    `sequence`: é o que a base já tinha por print (10 bilhetes da conta do Gabriel, códigos 1
//    a 10, medido em 21/11/2026). Com o `bet.id` cada um deles viraria duplicata. O `bet.id`
//    (8 dígitos) sobe numa linha própria.
// 4. LIMITE 25 e `filter` obrigatório: o replay nunca pede mais que 25 nem sem filtro.
// 5. MOEDA DA CONTA (USDT): o dinheiro sai rotulado na moeda, com o carimbo da colocação.
//
// O QUE NÃO COBRE (sem amostra; sobe a conferir, provado por clone sintético): aposta simples,
// cashout (`cashouts[]`), boost (`oddsBoost`), bet builder, anulada, `partially_won`,
// `cashed out`, `campaign settled`, ganha com perna `pushed`/`half_won`.
import { rodarInject, carregarContent, fixture, linha } from "../sandbox.mjs";

export const casa = "EPICBET";

const W = (r) => new RegExp(`^Ganhou → W \\(retorno ${r.replace(",", "\\,")} USDT = stake × odd`);
const L = /^Perdeu → L$/;
const AB = /^em aberto \(aguardando resultado — NÃO liquidar; sem resultado\)$/;
const CONF = /a conferir — não liquidar automaticamente/;

// card = rótulo, Odds, Stake, Payout, ID e o horário da última perna (Brasília).
// `col` = dia do agrupamento do card + a hora do `createdAt` (json).
const ESPERADO = {
  "11": { bet: "39939822", st: W("285,60"), odd: "7,14", stake: "40,00", col: "20/11/2026 18:33", evento: "21/11/2026 09:00:00" },
  "6": { bet: "39895669", st: W("323,60"), odd: "8,09", stake: "40,00", col: "20/11/2026 10:55", evento: "21/11/2026 10:30:00" },
  "10": { bet: "39935760", st: L, odd: "12,41", stake: "40,00", col: "20/11/2026 17:46", evento: "20/11/2026 23:00:00" },
  "9": { bet: "39919867", st: L, odd: "6,45", stake: "40,00", col: "20/11/2026 14:35", evento: "20/11/2026 15:00:00" },
  "8": { bet: "39896280", st: L, odd: "5,99", stake: "40,00", col: "20/11/2026 11:02", evento: "21/11/2026 11:00:00" },
  "7": { bet: "39895999", st: L, odd: "5,87", stake: "40,00", col: "20/11/2026 10:58", evento: "20/11/2026 13:30:00" },
  "5": { bet: "39895488", st: L, odd: "11,88", stake: "40,00", col: "20/11/2026 10:53", evento: "20/11/2026 22:00:00" },
  "4": { bet: "39866393", st: L, odd: "7,38", stake: "40,00", col: "19/11/2026 22:23", evento: "20/11/2026 16:00:00" },
  "3": { bet: "39866346", st: L, odd: "8,3", stake: "40,00", col: "19/11/2026 22:21", evento: "20/11/2026 15:00:00" },
  "2": { bet: "39866303", st: L, odd: "14,94", stake: "40,00", col: "19/11/2026 22:19", evento: "20/11/2026 14:30:00" },
  "1": { bet: "39866288", st: L, odd: "13,09", stake: "40,00", col: "19/11/2026 22:18", evento: "20/11/2026 13:30:00" },
  // abertas: card "Odds 13.28 · Stake 10 · Payout 132.8" e "Odds 6.14 · Stake 40 · Payout 245.6"
  "13": { bet: "40014621", st: AB, odd: "13,28", stake: "10,00", col: "21/11/2026 13:11", pot: "132,80 USDT" },
  "12": { bet: "39939954", st: AB, odd: "6,14", stake: "40,00", col: "20/11/2026 18:35", pot: "245,60 USDT" },
};

const RX_LISTA = /\/s\/sport-bet\/user\/ticket\.listWithMatchInfo\?/;
const ERRO_400 = JSON.stringify({ error: { message: "bad request", code: -32600, data: { code: "BAD_REQUEST", httpStatus: 400 } } });

function entrada(url) {
  try { return JSON.parse(new URL(url, "https://epicbet.com").searchParams.get("input") || "null"); }
  catch (e) { return null; }
}

// A casa dublada com as REGRAS medidas: filtro obrigatório, limite 25, fatia por offset.
function casaDublada(listas, pedidos) {
  return (url) => {
    if (!RX_LISTA.test(url)) return null;
    const inp = entrada(url);
    if (pedidos) pedidos.push(inp);
    if (!inp || !listas[inp.filter] || !(inp.limit >= 1) || inp.limit > 25 || !(inp.offset >= 0)) return ERRO_400;
    const todos = listas[inp.filter];
    return JSON.stringify({ result: { data: { tickets: todos.slice(inp.offset, inp.offset + inp.limit), count: todos.length } } });
  };
}

export async function rodar() {
  const pend = JSON.parse(fixture("epicbet.pending.json")).result.data.tickets;
  const sett = JSON.parse(fixture("epicbet.settled.json")).result.data.tickets;
  const pedidos = [];

  // Carga REAL da tela: a página pede 3 pendentes; o content pede o resto.
  const { ultima } = await rodarInject({
    inject: "eb_inject.js",
    href: "https://epicbet.com/en/sports",
    urlInicial: "https://epicbet.com/s/sport-bet/user/ticket.listWithMatchInfo?input=" +
      encodeURIComponent(JSON.stringify({ limit: 3, offset: 0, language: "en", filter: "pending" })),
    pedido: "__sharpenupEBReq",
    responder: casaDublada({ pending: pend, settled: sett }, pedidos),
  });

  const falhas = [];
  if (!ultima) return { falhas: ["o inject não emitiu nenhuma mensagem"], testes: 0 };
  if (!ultima.hook) falhas.push("o inject não emitiu `hook:true` (autodiagnóstico cego)");
  if (!ultima.fim) falhas.push("o inject não sinalizou `fim` (o robô ficaria esperando o teto)");
  const bilhetes = ultima.bilhetes || [];
  if (bilhetes.length !== 13) falhas.push(`esperava 13 bilhetes normalizados, vieram ${bilhetes.length}`);
  if (pedidos.some((p) => !p || p.limit > 25)) falhas.push("o inject pediu mais de 25 por página (a casa devolve 400)");
  if (pedidos.some((p) => !p || (p.filter !== "pending" && p.filter !== "settled"))) falhas.push("o inject pediu sem `filter` válido (a casa devolve 400)");
  if (!pedidos.some((p) => p && p.filter === "settled")) falhas.push("o inject nunca pediu as liquidadas");
  if (bilhetes.some((b) => !/^\d{1,6}$/.test(b.id))) falhas.push("o código do bilhete não é o `sequence` (o ID do card): armadilha 3");
  if (!Array.isArray(ultima.cru) || ultima.cru.length !== 13) falhas.push("o inject não mandou o cru de cada bilhete");
  else {
    const c = ultima.cru.find((x) => x.codigo === "7");
    if (!c || !c.cru || !c.cru.bet || c.cru.bet.id !== 39895999 || c.cru.sequence !== 7 ||
        !Array.isArray(c.cru.bet.selections) || c.cru.bet.selections.length !== 3 ||
        !c.cru.bet.selections[0].selectionInfo || !/^2026-11-20T13:5\d/.test(String(c.cru.createdAt))) {
      falhas.push("o cru do ID 7 não é o ticket da casa verbatim (com `sequence`, `createdAt`, `bet.selections[].selectionInfo`)");
    }
  }

  const fmt = carregarContent().pegar("formatTicketEB");
  let testes = 0;
  for (const b of bilhetes) {
    const txt = fmt(b);
    if (!txt.startsWith(`[Código: ${b.id}]`)) falhas.push(`${b.id}: marcador [Código:] ausente/errado`);
    if (!linha(txt, "Status (API):")) falhas.push(`${b.id}: falta o status cru da API`);
    if (linha(txt, "Moeda:") !== "USDT") falhas.push(`${b.id}: moeda "${linha(txt, "Moeda:")}" (a conta é USDT: armadilha 5)`);
    if (!/^\d{14}$/.test(linha(txt, "Carimbo de colocação:"))) falhas.push(`${b.id}: sem carimbo de colocação`);
    if (/R\$/.test(txt)) falhas.push(`${b.id}: "R$" numa conta em USDT`);
  }

  for (const [cod, e] of Object.entries(ESPERADO)) {
    const b = bilhetes.find((x) => x.id === cod);
    if (!b) { falhas.push(`${cod}: bilhete ausente`); continue; }
    const txt = fmt(b);
    testes++;
    const odd = linha(txt, "Odd:"), st = linha(txt, "Status:"), stake = linha(txt, "Stake:");
    if (odd !== e.odd) falhas.push(`${cod} (card): odd esperada ${e.odd}, veio "${odd}"`);
    if (!e.st.test(st)) falhas.push(`${cod} (card): status "${st}"`);
    if (stake !== e.stake) falhas.push(`${cod} (card): stake esperada ${e.stake}, veio "${stake}"`);
    if (linha(txt, "ID interno (bet.id):") !== e.bet) falhas.push(`${cod}: bet.id esperado ${e.bet}, veio "${linha(txt, "ID interno (bet.id):")}" (armadilha 3)`);
    if (!linha(txt, "Data (colocação):").startsWith(e.col)) falhas.push(`${cod} (card+json): colocação esperada ${e.col}, veio "${linha(txt, "Data (colocação):")}"`);
    if (e.evento && linha(txt, "Data (evento mais recente):") !== e.evento) falhas.push(`${cod} (card): evento esperado ${e.evento}, veio "${linha(txt, "Data (evento mais recente):")}"`);
    if (e.pot && linha(txt, "Retorno potencial:") !== e.pot) falhas.push(`${cod} (card): potencial esperado ${e.pot}, veio "${linha(txt, "Retorno potencial:")}"`);
    if (!e.pot && linha(txt, "Retorno potencial:")) falhas.push(`${cod}: "Retorno potencial" num bilhete liquidado`);
    if (linha(txt, "Tipo:") !== "Múltipla (3 seleções)") falhas.push(`${cod}: tipo "${linha(txt, "Tipo:")}"`);
  }

  // Seleções como o card: "<seleção> <linha>" / "<mercado> <linha>" / jogo / liga, e a perna dita.
  {
    const t7 = fmt(bilhetes.find((x) => x.id === "7") || {});
    if (!t7.includes("- Goals Handicap 0 - 0.25: FC Voluntari +0.25 [perna meia vitória]")) falhas.push(`ID 7: perna half_won mal escrita:\n${t7}`);
    if (!t7.includes("- Match Total Points: Under 164.5 [perna perdida]")) falhas.push(`ID 7: perna de total mal escrita:\n${t7}`);
    if (!/Jogo: Botosani - FC Voluntari · Liga: Romania Liga 1 · Esporte: Football · Início: 20\/11\/2026 12:30:00/.test(t7)) falhas.push(`ID 7: contexto da perna errado:\n${t7}`);
    if (!/Odd da seleção: 2,53/.test(t7)) falhas.push("ID 7: falta a odd da seleção");
    const t12 = fmt(bilhetes.find((x) => x.id === "12") || {});
    if (!/\[perna anulada \(pushed\)\]/.test(t12)) falhas.push(`ID 12: a perna pushed não está dita:\n${t12}`);
  }
  // Armadilha 2: a perdida com perna half_won não ganha o produto das pernas como odd.
  {
    const t7 = fmt(bilhetes.find((x) => x.id === "7") || {});
    if (/8,42/.test(linha(t7, "Odd:"))) falhas.push("ID 7: a odd virou o produto das pernas (8,42), o card diz 5,87");
  }

  testes += sinteticos(falhas, fmt, bilhetes);
  testes += await paginacao(falhas, sett);
  testes += await passivo(falhas, pend);
  testes += await deslogado(falhas);
  testes += await novaRodada(falhas, pend, sett);
  return { falhas, testes };
}

// Clones dos bilhetes reais com um campo trocado: o que a amostra não tem sobe a conferir,
// nunca liquidado por chute.
function sinteticos(falhas, fmt, bilhetes) {
  const ganha = bilhetes.find((x) => x.id === "11");
  const perdida = bilhetes.find((x) => x.id === "10");
  const aberta = bilhetes.find((x) => x.id === "13");
  if (!ganha || !perdida || !aberta) { falhas.push("sintéticos: bilhete-base ausente"); return 0; }
  let n = 0;
  const st = (b) => linha(fmt(b), "Status:");
  const ok = (cond, msg) => { n++; if (!cond) falhas.push(msg); };
  const perna = (b, i, s) => ({ ...b, sels: b.sels.map((x, j) => (j === i ? { ...x, status: s } : x)) });

  for (const s of ["void", "cancelled", "cashed out", "partially_won", "campaign settled", "suspensa"]) {
    ok(CONF.test(st({ ...ganha, status: s })), `status "${s}" virou "${st({ ...ganha, status: s })}"`);
  }
  ok(CONF.test(st({ ...ganha, cashouts: [{ amount: 100 }] })), "won com cashout virou liquidado");
  ok(CONF.test(st({ ...perdida, cashouts: [{ amount: 10 }] })), "lost com cashout virou liquidado");
  ok(CONF.test(st({ ...ganha, boost: 1.1 })), "won com boost virou liquidado");
  ok(/^Boost:/m.test(fmt({ ...ganha, boost: 1.1 })), "boost não aparece no bloco");
  ok(CONF.test(st(perna(ganha, 0, "pushed"))), "won com perna pushed virou liquidado (sem amostra liquidada)");
  ok(CONF.test(st(perna(ganha, 1, "half_won"))), "won com perna half_won virou liquidado");
  ok(CONF.test(st(perna(ganha, 2, "lost"))), "won com perna lost virou W");
  ok(CONF.test(st({ ...perdida, sels: perdida.sels.map((x) => ({ ...x, status: "won" })) })), "lost sem perna perdida virou L");
  ok(CONF.test(st({ ...ganha, odd: null })), "won sem odd virou liquidado");
  ok(linha(fmt({ ...ganha, odd: null }), "Odd:") === "", "odd ausente virou número (zero não é ausência)");
  ok(CONF.test(st({ ...ganha, stake: 0 })), "won sem stake virou liquidado");
  // Aberta: o retorno é POTENCIAL; nada de W.
  ok(AB.test(st(aberta)) && !/W/.test(st(aberta)), "aberta liquidou");
  // Simples: 1 perna.
  const simples = { ...ganha, tipo: "single", sels: [ganha.sels[0]], odd: 2.1 };
  ok(linha(fmt(simples), "Tipo:") === "Simples", `simples com tipo "${linha(fmt(simples), "Tipo:")}"`);
  ok(W("84,00").test(st(simples)), `simples ganha virou "${st(simples)}"`);
  ok(!/Odd da seleção/.test(fmt(simples)), "simples repetindo a odd da seleção");
  // Bet builder: a seleção diz, e o tipo também.
  const bb = { ...ganha, sels: ganha.sels.map((x) => ({ ...x, betBuilder: true })) };
  ok(/^Bet Builder/.test(linha(fmt(bb), "Tipo:")), `bet builder com tipo "${linha(fmt(bb), "Tipo:")}"`);
  return n;
}

// Paginação: 60 liquidadas, 25 por página. O inject anda pelo tamanho que VOLTOU e para no
// `count`; nunca pede além de 25.
async function paginacao(falhas, sett) {
  const muitos = [];
  for (let i = 0; i < 60; i++) {
    const t = JSON.parse(JSON.stringify(sett[i % sett.length]));
    t.bet.id = 50000000 + i; t.sequence = 1000 + i;
    muitos.push(t);
  }
  const pedidos = [];
  const { ultima } = await rodarInject({
    inject: "eb_inject.js", href: "https://epicbet.com/en/sports",
    semRequisicaoInicial: true, pedido: "__sharpenupEBReq",
    responder: casaDublada({ pending: [], settled: muitos }, pedidos), ms: 600,
  });
  const n = (ultima && ultima.bilhetes || []).length;
  if (n !== 60) falhas.push(`paginação: esperava 60 bilhetes, vieram ${n}`);
  const sp = pedidos.filter((p) => p && p.filter === "settled").map((p) => p.offset);
  if (JSON.stringify(sp) !== "[0,25,50]") falhas.push(`paginação: offsets pedidos ${JSON.stringify(sp)}, esperava [0,25,50]`);
  if (!ultima || !ultima.fim) falhas.push("paginação: sem `fim`");
  return 1;
}

// A página que busca a lista (a tela pede 3): o hook passivo encaminha a resposta.
async function passivo(falhas, pend) {
  const { mensagens } = await rodarInject({
    inject: "eb_inject.js", href: "https://epicbet.com/en/sports",
    urlInicial: "https://epicbet.com/s/sport-bet/user/ticket.listWithMatchInfo?input=" +
      encodeURIComponent(JSON.stringify({ limit: 3, offset: 0, language: "en", filter: "pending" })),
    responder: casaDublada({ pending: pend, settled: [] }),
  });
  const n = Math.max(0, ...mensagens.map((m) => (m.bilhetes || []).length));
  if (n !== pend.length) falhas.push(`passivo: a resposta que a PÁGINA buscou não chegou (${n} de ${pend.length})`);
  return 1;
}

// Sessão caída: a API devolve erro tRPC (objeto sem `result`). Não conta como resposta, e o
// robô recebe `fim` com `respostas: 0` (é o que acende o aviso "faça login").
async function deslogado(falhas) {
  const { ultima } = await rodarInject({
    inject: "eb_inject.js", href: "https://epicbet.com/en/sports",
    semRequisicaoInicial: true, pedido: "__sharpenupEBReq",
    responder: (url) => (RX_LISTA.test(url) ? JSON.stringify({ error: { message: "UNAUTHORIZED", data: { httpStatus: 401 } } }) : null),
  });
  if (!ultima || !ultima.fim) falhas.push("deslogado: o inject não sinalizou `fim`");
  else if (ultima.respostas !== 0) falhas.push(`deslogado: respostas = ${ultima.respostas} (o erro contou como lista)`);
  return 1;
}

// Rodada nova (lição da s393): o 2º pedido, depois do `fim`, busca de novo e não reenvia o
// acumulado velho como se fosse novo.
async function novaRodada(falhas, pend, sett) {
  const pedidos = [];
  const { mensagens } = await rodarInject({
    inject: "eb_inject.js", href: "https://epicbet.com/en/sports",
    semRequisicaoInicial: true, pedido: "__sharpenupEBReq",
    pedidoTardio: { __sharpenupEBReq: true },
    responder: casaDublada({ pending: pend, settled: sett }, pedidos), ms: 600,
  });
  const settledPedidos = pedidos.filter((p) => p && p.filter === "settled").length;
  if (settledPedidos < 2) falhas.push(`rodada nova: o 2º pedido não buscou de novo (${settledPedidos} pedido(s) de settled)`);
  const ult = mensagens[mensagens.length - 1];
  if (!ult || !ult.fim || (ult.bilhetes || []).length !== 13) falhas.push("rodada nova: a 2ª rodada não terminou com os 13 bilhetes");
  return 1;
}
