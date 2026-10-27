// 1win (1win.io) — captura por API `POST api-gateway.top-parser.com/bets/history/get-many`.
// Recon s413, conta do Feca (USDT), pelo navegador dele.
//
// PLATAFORMA PRÓPRIA (`top-parser`): a página é da 1win, o sportsbook fala com um gateway em
// OUTRO host. Não é DEX, BetBy, Altenar, Kambi nem 1xBet. Inject e formatador próprios
// (`tp_inject.js`, família `tp`).
//
// AS FIXTURES (`1win.settled.json`, `1win.open.json`) são as respostas da casa, byte a byte
// (hash conferido contra a página): a conta INTEIRA no dia do recon, 1 liquidada + 4 abertas,
// todas múltiplas de 2, em USDT. Sem nome, e-mail, id de usuário nem saldo no payload.
//
// O que este caso trava, cada item cruzado com o card da casa (aba Aberto e Liquidadas):
//   • `profitAmount` NÃO É LUCRO: na aberta é o retorno inteiro (25 × 5,73 = 143,25, card
//     "USDT 25,00 » USDT 143,25"); na perdida é 0 (card "» USDT 0,00").
//   • A ODD DO BILHETE É A `cf`, CORTADA EM 2 CASAS, e é ela que paga: 337817372 tem pernas
//     1,79 × 2,75 = 4,9225 e o card diz 4.92, com retorno 25 × 4,92 = 123,00. O produto das
//     pernas grava uma odd que a casa não pagou.
//   • A PERDIDA TEM PERNA PENDENTE: 337819068 perdeu no basquete com a perna do tênis de mesa
//     ainda por jogar (status 0). A casa liquida pela perna que perdeu.
//   • `refundInfo.refundAmount` é a OFERTA de cashout da aberta e muda a cada minuto. Não é
//     dinheiro de ninguém e não entra no bloco (se entrasse, a mesma aberta viraria texto
//     novo a cada captura).
//   • DATA: `createdAt` vem em UTC (21:44Z → card "18:44"); `startAt` em segundos unix.
//   • REPLAY: o token vai no header `token` (não é cookie) e sai em QUALQUER chamada
//     autenticada da tela de Esportes, não só na do histórico (medido). `limit` tem teto 150
//     (151 volta `bad_request_error`); erro volta com HTTP 200 e `errors[]`; o fim é
//     `offset >= meta.total`. `sportType` só aceita `sport`, `all` e `polybet` — o replay
//     pede `all` para nada ficar de fora.
//
// NÃO COBERTO pela fixture (a conta não tinha): ganha cheia, simples, anulada, sistema, bônus
// de múltipla, freebet, polybet e cashout parcial. A ganha com perna ANULADA tem fixture real
// desde a s419 (`1win.perna_anulada.json`, ver `pernaAnulada` abaixo) e o CASHOUT (status 4)
// desde a s431 (`1win.cashout.json`, ver `cashout` abaixo). Os casos de dinheiro estão
// travados abaixo por CLONE da liquidada (subir "a conferir" quando o número não prova), não
// por amostra real. Também não cobre a corrida "liquidada vence aberta" (o sandbox entrega
// as respostas em ordem fixa, como na Shuffle).
import { rodarInject, carregarContent, fixture, linha } from "../sandbox.mjs";

export const casa = "1win";

const L = /^Perdeu → L$/;
const AB = /^em aberto \(aguardando resultado — NÃO liquidar; sem resultado\)$/;
const M2 = /^Múltipla \(2 seleções\)$/;

// id → o que o card mostra. `col` = cabeçalho do card; `ev` = início da perna mais tardia.
const ESPERADO = {
  "337819068": { st: L,  odd: "4,87", stake: "25,00", tipo: M2, col: "12/10/2026 18:44:42", ev: "13/10/2026 01:30:00" },
  "338019158": { st: AB, odd: "5,73", stake: "25,00", tipo: M2, col: "12/10/2026 21:55:05", ev: "13/10/2026 15:00:00", pot: "143,25" },
  "337940634": { st: AB, odd: "4,2",  stake: "25,00", tipo: M2, col: "12/10/2026 20:34:59", ev: "13/10/2026 08:15:00", pot: "105,00" },
  "337817372": { st: AB, odd: "4,92", stake: "25,00", tipo: M2, col: "12/10/2026 18:43:29", ev: "14/10/2026 16:00:00", pot: "123,00" },
  "337815546": { st: AB, odd: "9",    stake: "25,00", tipo: M2, col: "12/10/2026 18:42:14", ev: "13/10/2026 15:00:00", pot: "225,00" },
};

const API = "https://api-gateway.top-parser.com";
const TOKEN = "harness.token.falso.1win";
const PAG = 2;   // a casa aceita até 150; páginas de 2 provam o avanço pelo que VOLTOU

const HDRS = {
  accept: "application/json", "Content-Type": "application/json", "x-lang": "pt",
  token: TOKEN, "x-user-location": "BR", "x-external-partner-id": "x",
};

// Simula a casa: ordem por `createdAt` decrescente, `offset`/`limit`, `meta.total`, erros
// com HTTP 200 como os medidos, filtro de `statuses` e `sportType`.
function casaTP(itens, registro) {
  return (url, opts) => {
    if (!String(url).startsWith(API)) return null;
    let corpo = {};
    try { corpo = JSON.parse((opts && opts.body) || "{}"); } catch (e) {}
    const h = (opts && opts.headers) || {};
    const tk = h.token || h.Token;
    const p = new URL(String(url)).pathname;
    registro.push({ p, corpo, tk });
    if (p !== "/bets/history/get-many") return JSON.stringify({ result: { items: [] } });
    if (!tk) return JSON.stringify({ errors: [{ code: "unauthorized" }] });
    if ((corpo.limit || 0) > 150) return JSON.stringify({ errors: [{ code: "bad_request_error" }] });
    if (corpo.sportType != null && !["sport", "all", "polybet"].includes(corpo.sportType)) {
      return JSON.stringify({ errors: [{ code: "validation_error" }] });
    }
    let lista = itens.slice().sort((a, b) => Date.parse(b.bet.createdAt) - Date.parse(a.bet.createdAt));
    if (corpo.sportType === "polybet") lista = [];
    if (Array.isArray(corpo.statuses)) lista = lista.filter((it) => corpo.statuses.includes(it.bet.status));
    const off = corpo.offset || 0, tam = Math.min(corpo.limit || 150, PAG);
    return JSON.stringify({ result: { items: lista.slice(off, off + tam), meta: { total: lista.length } } });
  };
}

function itensDaConta() {
  return JSON.parse(fixture("1win.settled.json")).result.items
    .concat(JSON.parse(fixture("1win.open.json")).result.items);
}

export async function rodar() {
  const itens = itensDaConta();
  const registro = [];
  // A requisição REAL da página: aba "Todos", sem filtro de status, `sportType: "sport"`.
  const { ultima, mensagens } = await rodarInject({
    inject: "tp_inject.js",
    href: "https://1win.io/betting/bets-history",
    urlInicial: API + "/bets/history/get-many",
    optsInicial: { method: "POST", headers: HDRS, body: JSON.stringify({ limit: 150, offset: 0, sportType: "sport" }) },
    pedido: "__sharpenupTPReq",
    responder: casaTP(itens, registro),
    ms: 600,
  });

  const falhas = [];
  if (!ultima) return { falhas: ["o inject não emitiu nenhuma mensagem"], testes: 0 };
  if (!ultima.hook) falhas.push("o inject não emitiu `hook:true` (autodiagnóstico cego)");
  if (!(ultima.respostas >= 2)) falhas.push(`\`respostas\` baixo demais (veio ${ultima.respostas})`);
  if (!ultima.fim) falhas.push("o inject não sinalizou `fim` (o robô ficaria esperando o teto)");
  if (JSON.stringify(mensagens).includes(TOKEN)) falhas.push("o token vazou na mensagem para o content");

  const bilhetes = ultima.bilhetes || [];
  if (bilhetes.length !== itens.length) falhas.push(`esperava ${itens.length} bilhetes, vieram ${bilhetes.length}`);

  const replay = registro.filter((r) => r.p === "/bets/history/get-many").slice(1);
  if (!replay.length) falhas.push("o replay não rodou");
  if (replay.some((r) => r.tk !== TOKEN)) falhas.push("o replay não levou o `token` aprendido");
  if (replay.some((r) => r.corpo.limit > 150)) falhas.push("o replay pediu `limit` acima de 150 (a casa recusa)");
  if (replay.some((r) => r.corpo.sportType !== "all")) falhas.push("o replay não pediu `sportType: \"all\"` (polybet ficaria de fora)");
  if (replay.some((r) => Array.isArray(r.corpo.statuses))) falhas.push("o replay pediu com filtro de status — sem ele a casa devolve tudo");
  const paginas = Math.ceil(itens.length / PAG);
  if (replay.length < paginas) falhas.push(`replay pediu ${replay.length} página(s); a lista tem ${paginas} de ${PAG}`);
  // EXATO, não "até uma a mais": quem para pela lista vazia em vez do `meta.total` pede uma
  // página a mais a cada varredura, e só esta régua vê isso.
  if (replay.length > paginas) falhas.push(`replay pediu ${replay.length} páginas para ${paginas} — não parou no meta.total`);

  // O cru tem de ser o item da casa, inteiro, com o código igual ao do texto.
  const cru = ultima.cru || [];
  if (cru.length !== itens.length) falhas.push(`cru: esperava ${itens.length} itens, vieram ${cru.length}`);
  for (const c of cru) {
    if (!c.cru || !c.cru.bet || String(c.cru.bet.id) !== c.codigo) falhas.push(`cru ${c.codigo}: não é o item da casa com o mesmo id`);
  }

  const fmt = carregarContent().pegar("formatTicketTP");
  const porId = new Map(bilhetes.map((b) => [b.id, b]));
  let testes = 0;

  for (const b of bilhetes) {
    const txt = fmt(b);
    if (!txt.startsWith(`[Código: ${b.id}]`)) falhas.push(`${b.id}: marcador [Código:] ausente/errado`);
    if (linha(txt, "Moeda:") !== "USDT") falhas.push(`${b.id}: faltou a linha "Moeda: USDT"`);
    if (!/^\d{14}$/.test(linha(txt, "Carimbo de colocação:"))) falhas.push(`${b.id}: faltou o carimbo de colocação (dia da cotação)`);
    if (/R\$/.test(txt)) falhas.push(`${b.id}: o bloco diz "R$" numa conta em USDT`);
    if (!linha(txt, "Status (API):")) falhas.push(`${b.id}: falta o status cru da API`);
    if (/^0*(,0*)?$/.test(linha(txt, "Odd:"))) falhas.push(`${b.id}: odd zerada ou ausente`);
  }

  for (const [idb, e] of Object.entries(ESPERADO)) {
    const b = porId.get(idb);
    if (!b) { falhas.push(`${idb}: não chegou ao lote`); continue; }
    const txt = fmt(b);
    testes++;
    const odd = linha(txt, "Odd:"), st = linha(txt, "Status:"), stake = linha(txt, "Stake:");
    if (!e.st.test(st)) falhas.push(`${idb}: status "${st}"`);
    if (odd.replace(/\s*\(.*$/, "") !== e.odd) falhas.push(`${idb}: odd esperada ${e.odd}, veio "${odd}"`);
    if (stake !== e.stake) falhas.push(`${idb}: stake esperada ${e.stake}, veio "${stake}"`);
    if (!e.tipo.test(linha(txt, "Tipo:"))) falhas.push(`${idb}: tipo "${linha(txt, "Tipo:")}"`);
    if (linha(txt, "Data (colocação):") !== e.col) falhas.push(`${idb}: colocação esperada ${e.col}, veio "${linha(txt, "Data (colocação):")}"`);
    if (linha(txt, "Data (evento mais recente):") !== e.ev) falhas.push(`${idb}: evento esperado ${e.ev}, veio "${linha(txt, "Data (evento mais recente):")}" (startAt é unix em segundos)`);
    if (/^Retorno:/m.test(txt) && AB.test(st)) falhas.push(`${idb}: aberta com linha "Retorno:" (potencial não é retorno)`);
    if (e.pot && linha(txt, "Retorno potencial (se ganhar):") !== e.pot + " USDT") falhas.push(`${idb}: retorno potencial esperado ${e.pot} USDT, veio "${linha(txt, "Retorno potencial (se ganhar):")}"`);
    if ((txt.match(/^- /gm) || []).length !== 2) falhas.push(`${idb}: esperava 2 seleções no bloco`);
  }

  // A odd que paga é a da casa (4,92), nunca o produto das pernas (4,9225).
  {
    const txt = fmt(porId.get("337817372") || {});
    if (/4,9225/.test(txt)) falhas.push("337817372: o produto das pernas (4,9225) entrou no bloco — a casa paga 4,92");
    if (!/Odd da perna: 1,79/.test(txt) || !/Odd da perna: 2,75/.test(txt)) falhas.push("337817372: faltou a odd de cada perna");
  }
  // A oferta de cashout da aberta não é dinheiro e não entra no bloco.
  {
    const txt = fmt(porId.get("338019158") || {});
    if (/24,46/.test(txt)) falhas.push("338019158: a oferta de cashout (24,46) vazou para o bloco");
  }
  // A perdida com perna pendente: a perna do tênis de mesa sobe como pendente, a do basquete
  // como perdida, e o bilhete é L.
  {
    const txt = fmt(porId.get("337819068") || {});
    if (!/Andrii Troian.*\[perna em aberto\]/.test(txt)) falhas.push("337819068: a perna pendente não está dita como em aberto");
    if (!/Abaixo De 55\.5.*\[perna perdida\]/.test(txt)) falhas.push("337819068: a perna perdida não está dita como perdida");
    if (!/Esporte: Basquete/.test(txt) || !/Liga: Estados Unidos da América · NBA Pré-Época/.test(txt)) falhas.push("337819068: esporte/liga da perna faltando");
  }

  // Dinheiro sem amostra real: clone da liquidada, só o que o número prova vira resultado.
  {
    const base = porId.get("337819068");
    if (base) {
      const c = (o) => linha(fmt(Object.assign({}, base, o)), "Status:");
      const ganha = c({ status: 2, retorno: 121.75 });
      if (!/^Ganhou → W \(retorno 121,75 USDT\)$/.test(ganha)) falhas.push(`status 2 com retorno = stake × odd virou "${ganha}"`);
      const ganhaOdd = linha(fmt(Object.assign({}, base, { status: 2, retorno: 121.75 })), "Odd:");
      if (ganhaOdd.replace(/\s*\(.*$/, "") !== "4,87") falhas.push(`status 2 (121,75 / 25): odd "${ganhaOdd}"`);
      const ganhaLucro = c({ status: 2, retorno: 96.75 });
      if (!/a conferir — não liquidar automaticamente/.test(ganhaLucro)) falhas.push(`status 2 com retorno que não fecha com a odd virou "${ganhaLucro}" (pode ser lucro, não retorno)`);
      const devolvida = c({ status: 3, retorno: 25 });
      if (!/→ V$/.test(devolvida)) falhas.push(`status 3 com retorno = stake virou "${devolvida}"`);
      const ganhoSemLucro = c({ status: 2, retorno: 25 });
      if (!/→ V$/.test(ganhoSemLucro)) falhas.push(`status 2 com retorno = stake virou "${ganhoSemLucro}"`);
      // Status 4 é cashout só com TODA perna em 4; aqui as pernas são 0 e 1 (formato não medido).
      const quatro = c({ status: 4, retorno: 18.4 });
      if (!/a conferir — não liquidar automaticamente/.test(quatro)) falhas.push(`status 4 com pernas fora do 4 virou "${quatro}" (formato sem amostra)`);
      const perdidaComDinheiro = c({ status: 1, retorno: 12 });
      if (/Perdeu → L/.test(perdidaComDinheiro)) falhas.push(`status 1 com retorno 12 virou "${perdidaComDinheiro}" (o dinheiro desmente o rótulo)`);
      const novo = c({ status: 9, retorno: 0 });
      if (!/a conferir — não liquidar automaticamente/.test(novo)) falhas.push(`status desconhecido virou "${novo}"`);
      const semRetorno = c({ status: 2, retorno: null });
      if (!/a conferir/.test(semRetorno)) falhas.push(`status 2 sem retorno virou "${semRetorno}"`);
      const simples = fmt(Object.assign({}, base, { pernas: base.pernas.slice(1) }));
      if (linha(simples, "Tipo:") !== "Simples") falhas.push(`uma perna só virou tipo "${linha(simples, "Tipo:")}"`);
      const sis = linha(fmt(Object.assign({}, base, { tipo: "system" })), "Tipo:");
      if (!/Sistema/.test(sis) || !/NUNCA o produto/.test(sis)) falhas.push(`betType system virou tipo "${sis}"`);
      const bonus = fmt(Object.assign({}, base, { bonus: 4.5, bonusPct: 5 }));
      if (!/^Bônus da casa: 4,50 USDT \(5%\)/m.test(bonus)) falhas.push("bônus de múltipla não está dito no bloco");
      const fb = fmt(Object.assign({}, base, { freebet: 25 }));
      // O rótulo é o que o servidor lê (`freebets_do_texto`); outra grafia some do P/L.
      if (!/^Freebet inclu[íi]do: 25,00 USDT/m.test(fb)) falhas.push("freebet não está dita com o rótulo que o servidor lê");
    }
  }

  testes += await pernaAnulada(falhas);
  testes += await cashout(falhas);
  testes += await partidaAFrio(itens, falhas);
  testes += await semToken(falhas);
  return { falhas, testes };
}

// s419: múltipla GANHA com uma perna ANULADA (crus reais, conta do Feca, `1win.perna_anulada.json`).
// A casa pagou pelo produto das pernas ganhas: 344388133 = 25 × 1,54 = 38,50 (tênis abandonado,
// perna status 3) e 344381942 = 25 × 3,15 = 78,75 (handicap +4 exato). Antes subiam "a conferir"
// e ficavam ABERTAS no Sharpen para sempre, com 117,25 USDT fora da Caixa.
async function pernaAnulada(falhas) {
  const itens = JSON.parse(fixture("1win.perna_anulada.json")).result.items;
  const { ultima } = await rodarInject({
    inject: "tp_inject.js",
    href: "https://1win.com/betting/bets-history",
    urlInicial: API + "/bets/history/get-many",
    optsInicial: { method: "POST", headers: HDRS, body: JSON.stringify({ limit: 150, offset: 0, sportType: "sport" }) },
    pedido: "__sharpenupTPReq",
    responder: casaTP(itens, []),
    ms: 600,
  });
  const fmt = carregarContent().pegar("formatTicketTP");
  const porId = new Map(((ultima && ultima.bilhetes) || []).map((b) => [b.id, b]));
  const ESP = {
    "344388133": { ret: "38,50", odd: "1,54", col: "3,23", anulada: /Vladislav Stukalov \[perna anulada/ },
    "344381942": { ret: "78,75", odd: "3,15", col: "6,02", anulada: /Indiana Hoosiers 4 \[perna anulada/ },
  };
  let n = 0;
  for (const [idb, e] of Object.entries(ESP)) {
    const b = porId.get(idb);
    if (!b) { falhas.push(`perna anulada ${idb}: não chegou ao lote`); continue; }
    n++;
    const txt = fmt(b);
    const st = linha(txt, "Status:"), odd = linha(txt, "Odd:");
    if (!new RegExp(`^Ganhou → W \\(retorno ${e.ret} USDT; perna anulada`).test(st)) falhas.push(`perna anulada ${idb}: status "${st}"`);
    if (!odd.startsWith(e.odd + " (= Retorno ÷ Stake")) falhas.push(`perna anulada ${idb}: odd esperada ${e.odd} (retorno ÷ stake), veio "${odd}"`);
    if (!odd.includes("era " + e.col)) falhas.push(`perna anulada ${idb}: a odd da colocação (${e.col}) não está dita`);
    if (!e.anulada.test(txt)) falhas.push(`perna anulada ${idb}: a perna anulada não está dita como anulada`);
    if (!/\[perna ganha\]/.test(txt)) falhas.push(`perna anulada ${idb}: a perna ganha não está dita como ganha`);
    if (/a conferir/.test(txt)) falhas.push(`perna anulada ${idb}: ainda sobe "a conferir"`);
    // O número tem de PROVAR: retorno que não fecha com as ganhas continua a conferir.
    const torto = linha(fmt(Object.assign({}, b, { retorno: 40 })), "Status:");
    if (!/a conferir — não liquidar automaticamente/.test(torto)) falhas.push(`perna anulada ${idb}: retorno 40 virou "${torto}"`);
    const st4 = linha(fmt(Object.assign({}, b, { status: 4 })), "Status:");
    if (!/a conferir — não liquidar automaticamente/.test(st4)) falhas.push(`perna anulada ${idb}: status 4 virou "${st4}"`);
    // Ganha + anulada continuam ali; só a 3ª perna, num enum sem amostra, tem de barrar.
    const p4 = linha(fmt(Object.assign({}, b, { pernas: b.pernas.concat([Object.assign({}, b.pernas[0], { status: 4 })]) })), "Status:");
    if (!/a conferir — não liquidar automaticamente/.test(p4)) falhas.push(`perna anulada ${idb}: perna status 4 virou "${p4}"`);
  }
  return n;
}

// s431: CASHOUT (crus reais, conta do Feca, 27/10/2026, `1win.cashout.json`). A 1win manda
// `status: 4` no bilhete E em toda perna, até na perna já finalizada (Petrolul 0x6), e
// `profitAmount` é o valor recebido. Antes subiam "a conferir" e ficavam ABERTOS no Sharpen,
// com 253,64 USDT fora da Caixa. Cashout ≠ stake → W, odd = retorno ÷ stake.
async function cashout(falhas) {
  const itens = JSON.parse(fixture("1win.cashout.json")).result.items;
  const { ultima } = await rodarInject({
    inject: "tp_inject.js",
    href: "https://1win.io/betting/bets-history",
    urlInicial: API + "/bets/history/get-many",
    optsInicial: { method: "POST", headers: HDRS, body: JSON.stringify({ limit: 150, offset: 0, sportType: "sport" }) },
    pedido: "__sharpenupTPReq",
    responder: casaTP(itens, []),
    ms: 600,
  });
  const fmt = carregarContent().pegar("formatTicketTP");
  const porId = new Map(((ultima && ultima.bilhetes) || []).map((b) => [b.id, b]));
  const ESP = {
    "361482655": { ret: "31,80", odd: "0,795",   col: "6,15" },
    "362337573": { ret: "86,22", odd: "2,1555",  col: "8,79" },
    "362339071": { ret: "52,50", odd: "1,3125",  col: "4,38" },
    "363617382": { ret: "43,61", odd: "1,09025", col: "8,13" },
    "363619481": { ret: "39,51", odd: "0,98775", col: "5,07" },
  };
  let n = 0;
  for (const [idb, e] of Object.entries(ESP)) {
    const b = porId.get(idb);
    if (!b) { falhas.push(`cashout ${idb}: não chegou ao lote`); continue; }
    n++;
    const txt = fmt(b);
    const st = linha(txt, "Status:"), odd = linha(txt, "Odd:");
    if (!new RegExp(`^Cashout com retorno ${e.ret} USDT ≠ stake → W`).test(st)) falhas.push(`cashout ${idb}: status "${st}"`);
    if (!odd.startsWith(e.odd + " (= Retorno ÷ Stake")) falhas.push(`cashout ${idb}: odd esperada ${e.odd} (retorno ÷ stake), veio "${odd}"`);
    if (!odd.includes("era " + e.col)) falhas.push(`cashout ${idb}: a odd da colocação (${e.col}) não está dita`);
    if ((txt.match(/\[perna encerrada pelo cashout\]/g) || []).length !== 2) falhas.push(`cashout ${idb}: as pernas não estão ditas como encerradas pelo cashout`);
    if (/a conferir/.test(txt)) falhas.push(`cashout ${idb}: ainda sobe "a conferir"`);
    // Cashout = stake é V pela rede do dinheiro, com a odd da casa.
    const igual = fmt(Object.assign({}, b, { retorno: b.stake }));
    if (!/→ V$/.test(linha(igual, "Status:"))) falhas.push(`cashout ${idb}: retorno = stake virou "${linha(igual, "Status:")}"`);
    if (linha(igual, "Odd:").replace(/\s*\(.*$/, "") !== e.col) falhas.push(`cashout ${idb}: cashout = stake com odd "${linha(igual, "Odd:")}"`);
    // Fora do formato medido continua a conferir: perna fora do 4, ou nada recebido.
    const torta = linha(fmt(Object.assign({}, b, { pernas: [Object.assign({}, b.pernas[0], { status: 2 })].concat(b.pernas.slice(1)) })), "Status:");
    if (!/a conferir — não liquidar automaticamente/.test(torta)) falhas.push(`cashout ${idb}: perna 2 num bilhete 4 virou "${torta}"`);
    const zero = linha(fmt(Object.assign({}, b, { retorno: 0 })), "Status:");
    if (!/a conferir — não liquidar automaticamente/.test(zero)) falhas.push(`cashout ${idb}: status 4 sem dinheiro virou "${zero}"`);
  }
  return n;
}

// A página nunca abriu o histórico: o token vem de outra chamada autenticada de Esportes
// (`freebets/get-many`, medido), e o replay arranca sozinho com o corpo de reserva.
async function partidaAFrio(itens, falhas) {
  const registro = [];
  const { ultima } = await rodarInject({
    inject: "tp_inject.js",
    href: "https://1win.io/betting",
    urlInicial: API + "/freebets/get-many",
    optsInicial: { method: "POST", headers: HDRS, body: "{}" },
    pedido: "__sharpenupTPReq",
    responder: casaTP(itens, registro),
    ms: 600,
  });
  const bs = (ultima && ultima.bilhetes) || [];
  if (bs.length !== itens.length) falhas.push(`partida a frio: esperava ${itens.length} bilhetes, vieram ${bs.length} (o token de outra chamada não foi aprendido?)`);
  if (!ultima || !ultima.fim) falhas.push("partida a frio: sem `fim`");
  return bs.length === itens.length ? 1 : 0;
}

// Sem login não há chamada com `token`: o inject não pode replayar, e tem de dizer por quê.
async function semToken(falhas) {
  const registro = [];
  const { ultima } = await rodarInject({
    inject: "tp_inject.js",
    href: "https://1win.io/betting",
    urlInicial: API + "/sports/get",
    optsInicial: { method: "POST", headers: { accept: "application/json", "x-lang": "pt" }, body: "{}" },
    pedido: "__sharpenupTPReq",
    responder: casaTP([], registro),
    ms: 400,
  });
  if (!ultima || !ultima.semToken) { falhas.push("sem token: o inject não avisou `semToken`"); return 0; }
  if (registro.some((r) => r.p === "/bets/history/get-many")) falhas.push("sem token: o inject replayou mesmo assim");
  return 1;
}
