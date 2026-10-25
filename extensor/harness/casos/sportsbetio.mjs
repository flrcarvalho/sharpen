// Sportsbet.io (sportsbet.io) — captura por API `POST /graphql` (`myBettingHistory` +
// `myActiveTickets`). Recon s428 (25/10/2026), conta do Feca em USDT, pelo navegador dele.
//
// PLATAFORMA PRÓPRIA (GraphQL do grupo Yolo, Apollo no mesmo domínio). Inject e formatador
// próprios (`sbi_inject.js`, `formatTicketSBI`). Família `sbi`.
//
// As FIXTURES são as respostas da casa ao replay, tiradas no mesmo minuto: `sportsbetio.settled
// .json` (17 liquidadas, a conta inteira) e `sportsbetio.active.json` (14 abertas). Nenhum campo
// de identidade do cliente no bilhete; nada foi apagado.
//
// O que este caso trava, cada item cruzado com o card da casa (Minhas Apostas, 25/10/2026):
//   • CÓDIGO = o ObjectId que o botão "ID" do card copia (`6addf2d1bf9e9d0001d7fda3`), tirado
//     do `id` em base64 (`SportsbetTicketsTicket:<hex>`).
//   • DINHEIRO em 1e8: `stakeAmount` 2500000000 = "Aposta USDT 25,00"; `wonAmount` 10621770000 =
//     "Ganhou USDT + 106,21" (o retorno: 60,01 × 1,77 = 106,2177). O card corta em 2 casas; o
//     bloco leva todas (`11,3418` onde o card diz 11,34).
//   • ODD = `boostedOdds` do bilhete: o TURBINADO perdido mostra 5,83 (`odds` 5,71).
//   • PERNA: `status` 1 verde, 2 vermelha, 0 pendente; `voidFactor` 1 CINZA mesmo com status 2
//     (6add828b: vermelha · cinza · vermelha no card).
//   • BET BUILDER ("INVENTOR" no card): uma perna "Bet Builder" com as seleções juntas por ";".
//   • REPLAY: Bearer = o cookie `token` (a frio) ou o header da página; sem ele a casa devolve a
//     lista `null` com HTTP 200; o cursor anda até `hasNextPage: false`, nas DUAS listas.
//
// NÃO COBERTO pela fixture (a conta não tinha): anulada inteira, cashout, freebet, sistema e
// múltipla ganha com perna anulada — a régua do dinheiro está travada abaixo por CLONE, não por
// amostra real. O caminho XHR do inject também não (a página usa fetch).
import { rodarInject, carregarContent, fixture, linha } from "../sandbox.mjs";

export const casa = "Sportsbet.io";

const L = /^Perdeu → L$/;
const W = (r) => new RegExp("^Ganhou → W \\(retorno " + r.replace(/[.,]/g, "\\$&") + " USDT\\)$");
const ABERTA = /^em aberto \(aguardando resultado — NÃO liquidar; sem resultado\)$/;
const M3 = /^Múltipla \(3 seleções\)$/;

// id → o que o card mostra.
const ESPERADO = {
  "6addf2d1bf9e9d0001d7fda3": { st: L, odd: "11,64", stake: "25,00",   tipo: M3, pernas: "ganha,perdida,aberta" },
  "6add804bbf9e9d0001423206": { st: L, odd: "17,29", stake: "11,3418", tipo: M3 },
  "6add828bbf9e9d0001c921a7": { st: L, odd: "5,07",  stake: "25,00",   tipo: M3, pernas: "perdida,anulada,perdida" },
  "6add45c3bf9e9d0001114d46": { st: W("106,2177"), odd: "1,77", stake: "60,01", tipo: /^Simples$/ },
  "6adc8eefbf9e9d00016fa2ac": { st: W("328,75"), odd: "13,15", stake: "25,00", tipo: M3, turbo: "12,71" },
  "6adbc55dbf9e9d0001c75309": { st: L, odd: "5,83",  stake: "25,00",   tipo: M3, turbo: "5,71", pernas: "perdida,ganha,anulada" },
  "6add3525bf9e9d0001ae48c4": { st: L, odd: "4,75",  stake: "30,01",   tipo: /^Criar Aposta \/ mesmo jogo \(2 seleções; a odd é a do conjunto\)$/ },
  "6adbd1f9bf9e9d00010157de": { st: L, odd: "59,5",  stake: "10,01",   tipo: /^Múltipla \(2 seleções; 2 delas são Criar Aposta/ },
  "6add8201bf9e9d000151e59d": { st: ABERTA, odd: "15,66", stake: "25,00", tipo: M3, pot: "391,50 USDT", pernas: "ganha,ganha,aberta" },
  "6ade2cb6bf9e9d000131a183": { st: ABERTA, odd: "5,5", stake: "40,01", tipo: /^Criar Aposta \/ mesmo jogo \(3 seleções/, pot: "220,055 USDT" },
};

const HOST = "https://sportsbet.io";
const JWT = "eyJharness.token.falso.sportsbetio";
const COOKIE = "theme=dark; token=" + JWT + "; _ga=GA1.1";

const SETTLED = () => JSON.parse(fixture("sportsbetio.settled.json")).data.sportsbetTickets.myBettingHistory.edges;
const ACTIVE = () => JSON.parse(fixture("sportsbetio.active.json")).data.sportsbetTickets.myActiveTickets.edges;
const cursor = (i) => Buffer.from("mongodbconnection:" + i).toString("base64");
const doCursor = (c) => Number(Buffer.from(String(c), "base64").toString().split(":")[1]);

// A casa como medida: `first`/`after` por cursor, lista `null` sem o Bearer, HTTP 200 sempre.
function casaSBI(settled, active, registro) {
  return (url, opts) => {
    if (!/\/graphql$/.test(new URL(String(url)).pathname)) return null;
    const h = (opts && opts.headers) || {};
    const auth = h.authorization || h.Authorization || "";
    let body = {};
    try { body = JSON.parse((opts && opts.body) || "{}"); } catch (e) {}
    const v = body.variables || {};
    registro.push({ op: body.operationName, first: v.first, after: v.after, auth });
    const campo = /myActiveTickets/.test(body.query || "") ? "myActiveTickets" : "myBettingHistory";
    const base = { id: "U3BvcnRzYmV0VGlja2V0czpHTE9CQUxMWV9VTklRVUVfU1BPUlRTQkVUVElDS0VUU19JRA==", __typename: "SportsbetTickets" };
    if (auth !== "Bearer " + JWT) return JSON.stringify({ data: { sportsbetTickets: Object.assign(base, { [campo]: null }) } });
    const lista = campo === "myActiveTickets" ? active : settled;
    const ini = v.after ? doCursor(v.after) + 1 : 0;
    const fatia = lista.slice(ini, ini + (v.first || 5));
    const fim = ini + fatia.length;
    return JSON.stringify({ data: { sportsbetTickets: Object.assign(base, { [campo]: {
      edges: fatia, pageInfo: { hasNextPage: fim < lista.length, endCursor: cursor(fim - 1), __typename: "PageInfo" } } }) } });
  };
}

const DOM = (cookie) => ({ cookie, querySelector: () => null, querySelectorAll: () => [] });

export async function rodar() {
  const registro = [];
  // A frio: o popup injeta tarde; o JWT sai do cookie.
  const { ultima, mensagens } = await rodarInject({
    inject: "sbi_inject.js", href: HOST + "/pt/user/my-bets/settled",
    semRequisicaoInicial: true, dom: DOM(COOKIE),
    pedido: "__sharpenupSBIReq", responder: casaSBI(SETTLED(), ACTIVE(), registro), ms: 600,
  });

  const falhas = [];
  if (!ultima) return { falhas: ["o inject não emitiu nenhuma mensagem"], testes: 0 };
  if (!ultima.hook) falhas.push("o inject não emitiu `hook:true` (autodiagnóstico cego)");
  if (!ultima.fim) falhas.push("o inject não sinalizou `fim`");
  if (ultima.erro) falhas.push("erro no replay: " + ultima.erro);
  if (JSON.stringify(mensagens).includes(JWT)) falhas.push("o token vazou na mensagem para o content");
  if (registro.some((r) => r.auth !== "Bearer " + JWT)) falhas.push("o replay não levou o Bearer do cookie");
  if (registro.some((r) => !(r.first <= 100))) falhas.push("o replay pediu mais de 100 por página");
  const ops = [...new Set(registro.map((r) => r.op))].join(",");
  if (ops !== "SettledTicketsQuery,ActiveTicketsQuery") falhas.push(`o replay pediu ${ops}, esperava histórico e abertas`);

  const total = SETTLED().length + ACTIVE().length;
  const bilhetes = ultima.bilhetes || [];
  if (bilhetes.length !== total) falhas.push(`esperava ${total} bilhetes (17 + 14), vieram ${bilhetes.length}`);
  const cru = ultima.cru || [];
  if (cru.length !== total) falhas.push(`cru: esperava ${total} itens, vieram ${cru.length}`);
  for (const c of cru) if (!c.cru || !String(c.cru.id || "").length || !Array.isArray(c.cru.bets)) falhas.push(`cru ${c.codigo}: não é o node da casa`);

  const fmt = carregarContent().pegar("formatTicketSBI");
  const porId = new Map(bilhetes.map((b) => [b.id, b]));
  let testes = 0;

  for (const b of bilhetes) {
    const txt = fmt(b);
    if (!txt.startsWith(`[Código: ${b.id}]`)) falhas.push(`${b.id}: marcador [Código:] ausente/errado`);
    if (!/^[0-9a-f]{24}$/.test(b.id)) falhas.push(`${b.id}: código fora do ObjectId de 24 hex do card`);
    if (linha(txt, "Moeda:") !== "USDT") falhas.push(`${b.id}: faltou a linha "Moeda: USDT"`);
    if (!/^\d{14}$/.test(linha(txt, "Carimbo de colocação:"))) falhas.push(`${b.id}: faltou o carimbo de colocação`);
    if (/R\$/.test(txt)) falhas.push(`${b.id}: o bloco diz "R$" numa conta em USDT`);
    if (/\t/.test(txt)) falhas.push(`${b.id}: TAB no bloco (é a coluna do TSV)`);
    if (/^0*(,0*)?$/.test(linha(txt, "Odd:"))) falhas.push(`${b.id}: odd zerada ou ausente`);
    if (!/^Data \(evento mais recente\): \d\d\/\d\d\/\d{4} /m.test(txt)) falhas.push(`${b.id}: sem data de evento`);
    if (/a conferir/.test(linha(txt, "Status:"))) falhas.push(`${b.id}: a conta inteira tem resultado provado, veio "${linha(txt, "Status:")}"`);
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
    if (e.turbo && !String(linha(txt, "Odd sem o turbo:")).startsWith(e.turbo)) falhas.push(`${idb}: faltou "Odd sem o turbo: ${e.turbo}"`);
    if (e.pot && linha(txt, "Retorno potencial (se ganhar):") !== e.pot) falhas.push(`${idb}: potencial esperado ${e.pot}, veio "${linha(txt, "Retorno potencial (se ganhar):")}"`);
    if (e.pot && /^Retorno:/m.test(txt)) falhas.push(`${idb}: aberta com linha "Retorno:"`);
    if (e.pernas) {
      const est = (txt.match(/\[perna (\w+)\]/g) || []).map((x) => x.slice(7, -1)).join(",");
      if (est !== e.pernas) falhas.push(`${idb}: pernas "${est}", o card mostra ${e.pernas}`);
    }
  }
  // Perna do 1º card, como a tela escreve, e o Bet Builder com as seleções uma por linha.
  {
    const t1 = fmt(porId.get("6addf2d1bf9e9d0001d7fda3") || {});
    if (!/^- 1º tempo - Cadiz CF total de escanteios: Menos de 1\.5 \[perna ganha\]$/m.test(t1)) falhas.push("6addf2d1: a 1ª perna não saiu como no card");
    if (!/Jogo: Cadiz CF - AD Ceuta · Esporte: soccer/.test(t1)) falhas.push("6addf2d1: jogo/esporte da 1ª perna");
    if (!/Odd da perna: 3,05/.test(t1)) falhas.push("6addf2d1: faltou a odd da perna");
    const t2 = fmt(porId.get("6add3525bf9e9d0001ae48c4") || {});
    if (!/^- Criar Aposta: 2 seleções \[perna perdida\]$/m.test(t2)) falhas.push("6add3525: o Bet Builder não saiu como perna única");
    if (!/^ {4}· Rebotes do jogador - P\.J\. Washington 10\+ \(Partida\)$/m.test(t2) || !/^ {4}· Pontos do jogador - P\.J\. Washington 10\+ \(Partida\)$/m.test(t2)) falhas.push("6add3525: as seleções do Bet Builder não estão uma por linha");
    const t3 = fmt(porId.get("6adc8eefbf9e9d00016fa2ac") || {});
    if (!/Odd da perna: 2,2 \(turbinada; sem turbo 2,18\)/.test(t3)) falhas.push("6adc8eef: a odd turbinada da perna não subiu");
  }

  // Dinheiro sem amostra real: clone, só o que o número prova vira resultado.
  {
    const base = porId.get("6add828bbf9e9d0001c921a7");     // 25 @ 5,07, perdida
    if (base) {
      const c = (o) => linha(fmt(Object.assign({}, base, o)), "Status:");
      const anul = c({ retorno: 25 });
      if (!/→ V$/.test(anul)) falhas.push(`retorno = stake virou "${anul}"`);
      const cash = c({ cashouts: [{ valor: "1500000000", pago: "1500000000", tipo: "FULL", odd: 1.2 }], retorno: 15 });
      if (!/a conferir — não liquidar automaticamente/.test(cash) || !/cashout 1500000000/.test(cash)) falhas.push(`cashout sem amostra virou "${cash}"`);
      const fb = c({ freebet: true });
      if (!/a conferir/.test(fb)) falhas.push(`freebet sem amostra virou "${fb}"`);
      const naoFecha = c({ retorno: 40, pernas: base.pernas.map((p) => Object.assign({}, p, { status: 1, anulada: 0 })) });
      if (!/a conferir/.test(naoFecha)) falhas.push(`retorno que não fecha com a odd virou "${naoFecha}"`);
      const semPerdida = c({ retorno: null, pernas: base.pernas.map((p) => Object.assign({}, p, { status: 1, anulada: 0 })) });
      if (/→ L/.test(semPerdida)) falhas.push(`sem retorno e sem perna perdida virou "${semPerdida}"`);
      // Múltipla ganha com perna anulada: 25 × 1,98 × 2,56 (a do meio anulada) = 126,72.
      const comAnul = c({ retorno: 126.72, pernas: base.pernas.map((p, i) => Object.assign({}, p, { status: i === 1 ? 2 : 1, anulada: i === 1 ? 1 : 0 })) });
      if (!/^Ganhou → W \(retorno 126,72 USDT; perna anulada fora da odd\)$/.test(comAnul)) falhas.push(`múltipla ganha com perna anulada virou "${comAnul}"`);
      const sis = linha(fmt(Object.assign({}, base, { apostas: 3 })), "Tipo:");
      if (!/Sistema/.test(sis) || !/NUNCA o produto/.test(sis)) falhas.push(`sistema virou tipo "${sis}"`);
      const semOdd = linha(fmt(Object.assign({}, base, { odd: 0 })), "Odd:");
      if (!/deixe a odd VAZIA/.test(semOdd)) falhas.push(`odd 0 virou "${semOdd}" (zero não é ausência)`);
    }
  }

  testes += await paginacao(falhas);
  testes += await liquidadaVence(falhas);
  testes += await aprendido(falhas);
  testes += await semSessao(falhas);
  return { falhas, testes };
}

// 230 liquidadas em páginas de 100: 3 pedidos EXATOS, nenhum a mais.
async function paginacao(falhas) {
  const m = SETTLED();
  const lista = [];
  for (let i = 0; i < 230; i++) {
    const n = JSON.parse(JSON.stringify(m[i % m.length]));
    n.node.id = Buffer.from("SportsbetTicketsTicket:" + (0x6a000000 + i).toString(16).padEnd(24, "0")).toString("base64");
    lista.push(n);
  }
  const registro = [];
  const { ultima } = await rodarInject({
    inject: "sbi_inject.js", href: HOST + "/pt/user/my-bets/settled", semRequisicaoInicial: true, dom: DOM(COOKIE),
    pedido: "__sharpenupSBIReq", responder: casaSBI(lista, [], registro), ms: 600,
  });
  const n = ((ultima && ultima.bilhetes) || []).length;
  if (n !== 230) falhas.push(`paginação: esperava 230 bilhetes, vieram ${n}`);
  const pags = registro.filter((r) => r.op === "SettledTicketsQuery").map((r) => (r.after ? doCursor(r.after) : -1)).join(",");
  if (pags !== "-1,99,199") falhas.push(`paginação: cursores pedidos ${pags}, esperava -1,99,199 (fim = hasNextPage)`);
  return 1;
}

// O mesmo bilhete aberto e depois liquidado: a liquidada vence, em qualquer ordem.
async function liquidadaVence(falhas) {
  const liq = SETTLED().find((e) => Buffer.from(e.node.id, "base64").toString().endsWith("6add45c3bf9e9d0001114d46"));   // ganha
  const aberta = JSON.parse(JSON.stringify(liq));
  aberta.node.status = "ACTIVE"; aberta.node.wonAmount = null;
  const { ultima } = await rodarInject({
    inject: "sbi_inject.js", href: HOST + "/pt", semRequisicaoInicial: true, dom: DOM(COOKIE),
    pedido: "__sharpenupSBIReq", responder: casaSBI([liq], [aberta], []), ms: 600,
  });
  const b = ((ultima && ultima.bilhetes) || []).find((x) => x.id === "6add45c3bf9e9d0001114d46");
  if (!b || b.status === "ACTIVE") falhas.push("a aberta (lida depois) apagou a liquidada do mesmo código");
  return 1;
}

// Sem cookie: o Bearer vem da chamada que a PÁGINA fez.
async function aprendido(falhas) {
  const registro = [];
  const { ultima } = await rodarInject({
    inject: "sbi_inject.js", href: HOST + "/pt/user/my-bets/active", dom: DOM("theme=dark"),
    urlInicial: HOST + "/graphql",
    optsInicial: { method: "POST", headers: { "Content-Type": "application/json", Authorization: "Bearer " + JWT },
                   body: JSON.stringify({ operationName: "GetUserPendingEventsQuery", variables: {}, query: "query { x }" }) },
    pedido: "__sharpenupSBIReq", responder: casaSBI(SETTLED(), ACTIVE(), registro), ms: 600,
  });
  const n = ((ultima && ultima.bilhetes) || []).length;
  if (n !== SETTLED().length + ACTIVE().length) falhas.push(`token aprendido da página: esperava 31 bilhetes, vieram ${n}`);
  return 1;
}

// Sem sessão: nada no cookie e nenhuma chamada. Diz `semToken` e não pede nada.
async function semSessao(falhas) {
  const registro = [];
  const { ultima } = await rodarInject({
    inject: "sbi_inject.js", href: HOST + "/pt", semRequisicaoInicial: true, dom: DOM("theme=dark"),
    pedido: "__sharpenupSBIReq", responder: casaSBI(SETTLED(), ACTIVE(), registro), ms: 300,
  });
  if (!ultima || !ultima.semToken) falhas.push("sem sessão: o inject não disse `semToken`");
  if (registro.some((r) => /Tickets/.test(r.op || ""))) falhas.push("sem sessão: o inject pediu a lista sem Bearer");
  // Cookie VENCIDO: a casa devolve `null` com 200 → erro dito, nunca "0 bilhetes" mudo.
  const { ultima: u2 } = await rodarInject({
    inject: "sbi_inject.js", href: HOST + "/pt", semRequisicaoInicial: true, dom: DOM("token=eyJvencido"),
    pedido: "__sharpenupSBIReq", responder: casaSBI(SETTLED(), ACTIVE(), []), ms: 300,
  });
  if (!(u2 && /sessão expirada/.test(u2.erro || ""))) falhas.push(`lista null com 200 não virou erro (veio "${u2 && u2.erro}")`);
  return 1;
}
