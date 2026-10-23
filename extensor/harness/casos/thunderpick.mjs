// Thunderpick (thunderpick.io) — captura por API `GET /api/wagers/v2/resolved` + `/pending`.
// Recon 22/10/2026, conta do Feca (EUR), pelo navegador dele.
//
// PLATAFORMA PRÓPRIA (front React Router v7, API `/api/*` no mesmo domínio, atrás da
// Cloudflare; feeds Oddin.gg e DATA.BET). Não é Altenar, BetBy, Kambi, BetConstruct nem
// softlabs: inject e formatador próprios (`thp_inject.js`, `formatTicketTHP`).
//
// AS FIXTURES são a conta INTEIRA no dia do recon, `uuid` zerado e nenhum campo de identidade:
//   • `thunderpick.resolved.json` — `resolved?take=100&skip=0&sortColumn=finishTime`: 29
//     liquidadas (8 ganhas, 21 perdidas), 14 múltiplas e 15 simples, de 2025 e 2026;
//   • `thunderpick.pending.json` — `pending`: 13 abertas, 10 múltiplas com pernas já decididas.
//
// O que este caso trava, cada item cruzado com o card da casa (exibição em EUR):
//   • DINHEIRO em CENTAVOS DE EURO: `amount` 4383 = card 43,83 EUR, `outcome` 7100 = 71,00 EUR.
//     A casa diz na própria tela que aposta e saldo "are always counted and settled in Euro";
//     a exibição em USD usa o câmbio do DIA (medido: o mesmo bilhete de 2025 mudou de 24,98
//     para 24,97 USD entre duas leituras). Por isso o bloco leva `Moeda: EUR` e nunca "R$".
//   • CÓDIGO com prefixo de tipo: `wagerId` tem DUAS séries (múltipla ~2,2M, simples
//     4,9M–10,3M) e nada impede um número de aparecer nas duas. `C2225866` / `S10277912`
//     (`InPlays` também é `S`).
//   • RETORNO arredondado ao centavo sem regra fixa: 2226 × 8,41 = 18720,66 → 18720, mas
//     2196 × 1,8 = 3952,8 → 3953. A odd do bloco é a do card (8,41), nunca retorno ÷ stake.
//   • ESPORTE não vem por nome, só `gameId`: 6 CS2 · 10 futebol · 11 basquete · 14 hóquei ·
//     15 tênis (medido pela liga de cada bilhete). Id fora do mapa sobe cru.
//   • DATAS em ISO UTC: `createTime` = colocação (dia da cotação), `eventStartTime` = evento
//     (na múltipla, o do topo já é o da perna mais tardia), ambos convertidos para São Paulo.
//   • REPLAY: header `thunderpick-token` (aprendido da requisição da página) ou, a frio, de
//     `localStorage["thp.sessionData"].sessionId`. Sem ele a casa responde 403 com
//     `errorCode 2013`. A página pede `take=20`; `take` de 1000 foi aceito. O fim é o
//     `totalWagersCount` da 1ª PÁGINA: `skip` além do fim devolve `{wagers:[], totalWagersCount:0}`.
//
// NÃO COBERTO por amostra real (a conta não tinha): devolvida/cancelada (`cancelReason`),
// cashout (`cashOutOdds`), freebet (`freeBet`) e boost. Os casos de dinheiro estão travados por
// CLONE da perdida (subir "a conferir" quando o número não prova), como na Vave. O teto real do
// `take` também não: com 29 bilhetes, 100, 500 e 1000 devolveram tudo. O caminho XHR do inject
// não é exercitado (a página usa fetch, medido).
import { rodarInject, carregarContent, fixture, linha, respostaHttp } from "../sandbox.mjs";

export const casa = "Thunderpick";

const L = /^Perdeu → L$/;
const W = (r) => new RegExp("^Ganhou → W \\(retorno " + r + " EUR\\)$");
const S1 = /^Simples$/;
const M3 = /^Múltipla \(3 seleções\)$/;

// código → o que o card mostra (exibição em EUR). `col` = colocação, `ev` = evento, em São Paulo.
const ESPERADO = {
  "S4965610":  { st: W("71,00"),  odd: "1,62",  stake: "43,83", tipo: S1, col: "25/04/2025 19:19:35", ev: "30/04/2025 12:10:00", pernas: 1 },
  "S4956054":  { st: W("39,53"),  odd: "1,8",   stake: "21,96", tipo: S1, pernas: 1 },
  "S4988241":  { st: L,           odd: "2,8",   stake: "22,03", tipo: S1, pernas: 1 },
  "S10277912": { st: W("117,49"), odd: "1,76",  stake: "66,76", tipo: S1, col: "21/10/2026 20:52:51", ev: "21/10/2026 21:00:00", pernas: 1 },
  "S10286618": { st: W("49,88"),  odd: "2,24",  stake: "22,27", tipo: S1, pernas: 1 },
  // Múltipla ganha: o retorno da casa (187,20) é truncado, o teórico seria 187,21.
  "C2225866":  { st: W("187,20"), odd: "8,41",  stake: "22,26", tipo: M3, col: "21/10/2026 21:56:00", ev: "21/10/2026 23:30:00", pernas: 3 },
  "C2225863":  { st: L,           odd: "13,38", stake: "22,26", tipo: M3, pernas: 3 },
};

const HOST = "https://thunderpick.io";
const TOKEN = "harness-token-falso-thunderpick-0000000000000000000000000000000";
const HDRS = { accept: "application/json", "thunderpick-token": TOKEN };

const RES = () => JSON.parse(fixture("thunderpick.resolved.json")).data.wagers;
const PEN = () => JSON.parse(fixture("thunderpick.pending.json")).data.wagers;
const COD = (w) => (w.wagerType === "Combo" ? "C" : "S") + w.wagerId;

// Simula a casa: `take`/`skip` nas liquidadas, abertas de uma vez só, 403 sem o token, e a
// armadilha medida — `skip` além do fim devolve lista vazia com total ZERO.
function casaTHP(resolvidas, abertas, registro, tetoTake = Infinity) {
  return (url, opts) => {
    if (!String(url).startsWith(HOST + "/api/")) return null;
    const u = new URL(String(url));
    const h = (opts && opts.headers) || {};
    const tok = h["thunderpick-token"] || h["Thunderpick-Token"] || "";
    registro.push({ p: u.pathname, q: Object.fromEntries(u.searchParams), tok, cred: opts && opts.credentials });
    if (!/^\/api\/wagers\/v2\/(resolved|pending)$/.test(u.pathname)) return JSON.stringify({ statusCode: 200, ok: true, data: {} });
    if (tok !== TOKEN) return respostaHttp(403, JSON.stringify({ errorCode: 2013, message: "Forbidden" }));
    if (u.pathname.endsWith("/pending")) {
      return JSON.stringify({ statusCode: 200, ok: true, data: { wagers: abertas, totalWagersCount: abertas.length } });
    }
    const take = Math.min(Number(u.searchParams.get("take") || 20), tetoTake);
    const skip = Number(u.searchParams.get("skip") || 0);
    const fatia = resolvidas.slice(skip, skip + take);
    return JSON.stringify({ statusCode: 200, ok: true,
      data: { wagers: fatia, totalWagersCount: fatia.length ? resolvidas.length : 0 } });
  };
}

const LS = (tok) => ({ localStorage: { getItem: (k) => (k === "thp.sessionData" && tok ? JSON.stringify({ sessionId: tok, userId: 0 }) : null) } });
const _resolvidas = (r) => r.filter((x) => x.p === "/api/wagers/v2/resolved");

async function rodarPadrao(resolvidas, abertas, registro, extra = {}, tetoTake = Infinity) {
  return rodarInject(Object.assign({
    inject: "thp_inject.js",
    href: HOST + "/en/my-bets/settled",
    urlInicial: HOST + "/api/wagers/v2/resolved?take=20&skip=0&sortColumn=finishTime",
    optsInicial: { method: "GET", headers: HDRS, credentials: "same-origin" },
    pedido: "__sharpenupTHPReq",
    responder: casaTHP(resolvidas, abertas, registro, tetoTake),
    ms: 600,
  }, extra));
}

export async function rodar() {
  const resolvidas = RES(), abertas = PEN();
  const total = resolvidas.length + abertas.length;
  const registro = [];
  const { ultima, mensagens } = await rodarPadrao(resolvidas, abertas, registro);

  const falhas = [];
  if (!ultima) return { falhas: ["o inject não emitiu nenhuma mensagem"], testes: 0 };
  if (!ultima.hook) falhas.push("o inject não emitiu `hook:true` (autodiagnóstico cego)");
  if (!(ultima.respostas >= 2)) falhas.push(`\`respostas\` baixo demais (veio ${ultima.respostas})`);
  if (!ultima.fim) falhas.push("o inject não sinalizou `fim` (o robô ficaria esperando o teto)");
  if (ultima.semToken) falhas.push("`semToken` com o token aprendido da página");
  if (JSON.stringify(mensagens).includes(TOKEN)) falhas.push("o token vazou na mensagem para o content");

  const bilhetes = ultima.bilhetes || [];
  if (bilhetes.length !== total) falhas.push(`esperava ${total} bilhetes (29 liquidadas + 13 abertas), vieram ${bilhetes.length}`);

  const replay = _resolvidas(registro).slice(1);
  if (!replay.length) falhas.push("o replay não rodou");
  if (registro.slice(1).some((r) => r.tok !== TOKEN)) falhas.push("o replay não levou o `thunderpick-token` aprendido");
  if (replay.some((r) => Number(r.q.take) !== 100)) falhas.push(`o replay pediu take ${replay.map((r) => r.q.take).join(",")} — esperava 100 (a página pede 20)`);
  if (replay.length !== 1) falhas.push(`replay pediu ${replay.length} página(s) de liquidadas para 29 bilhetes em páginas de 100 — não parou no total`);
  if (registro.filter((r) => r.p === "/api/wagers/v2/pending").length !== 1) falhas.push("o replay não buscou as abertas (`/pending`) exatamente uma vez");

  // O cru tem de ser o bilhete da casa, com o mesmo código do texto.
  const cru = ultima.cru || [];
  if (cru.length !== total) falhas.push(`cru: esperava ${total} itens, vieram ${cru.length}`);
  for (const c of cru) {
    if (!c.cru || c.cru.wagerId == null || COD(c.cru) !== c.codigo) falhas.push(`cru ${c.codigo}: não é o bilhete da casa com o mesmo código`);
  }

  const fmt = carregarContent().pegar("formatTicketTHP");
  const porId = new Map(bilhetes.map((b) => [b.id, b]));
  let testes = 0;

  // Toda a fixture, sem exceção.
  for (const w of resolvidas.concat(abertas)) if (!porId.has(COD(w))) falhas.push(`${COD(w)}: não chegou ao lote (ou o código não tem o prefixo de tipo)`);
  for (const b of bilhetes) {
    const txt = fmt(b);
    if (!txt.startsWith(`[Código: ${b.id}]`)) falhas.push(`${b.id}: marcador [Código:] ausente/errado`);
    if (!/^[CS]\d+$/.test(b.id)) falhas.push(`${b.id}: código sem o prefixo de tipo (C múltipla / S simples)`);
    if (linha(txt, "Moeda:") !== "EUR") falhas.push(`${b.id}: faltou a linha "Moeda: EUR"`);
    if (!/^\d{14}$/.test(linha(txt, "Carimbo de colocação:"))) falhas.push(`${b.id}: faltou o carimbo de colocação (dia da cotação)`);
    if (/R\$/.test(txt)) falhas.push(`${b.id}: o bloco diz "R$" numa conta em EUR`);
    if (!linha(txt, "Status (API):")) falhas.push(`${b.id}: falta o status cru da API`);
    if (/^0*(,0*)?$/.test(linha(txt, "Odd:"))) falhas.push(`${b.id}: odd zerada ou ausente`);
    if (!/^Data \(evento mais recente\): \d\d\/\d\d\/\d{4} /m.test(txt)) falhas.push(`${b.id}: sem data de evento`);
    if (/undefined|null|NaN/.test(txt)) falhas.push(`${b.id}: "undefined"/"null"/"NaN" no bloco`);
    if (!/^Esporte: |· Esporte: /m.test(txt)) falhas.push(`${b.id}: sem esporte`);
  }

  for (const [idb, e] of Object.entries(ESPERADO)) {
    const b = porId.get(idb);
    if (!b) { falhas.push(`${idb}: não chegou ao lote`); continue; }
    const txt = fmt(b);
    testes++;
    const odd = linha(txt, "Odd:"), st = linha(txt, "Status:"), stake = linha(txt, "Stake:");
    if (!e.st.test(st)) falhas.push(`${idb}: status "${st}"`);
    if (odd !== e.odd) falhas.push(`${idb}: odd esperada ${e.odd}, veio "${odd}" (a do card, nunca retorno ÷ stake)`);
    if (stake !== e.stake) falhas.push(`${idb}: stake esperada ${e.stake}, veio "${stake}" (centavos de euro ÷ 100)`);
    if (!e.tipo.test(linha(txt, "Tipo:"))) falhas.push(`${idb}: tipo "${linha(txt, "Tipo:")}"`);
    if (e.col && linha(txt, "Data (colocação):") !== e.col) falhas.push(`${idb}: colocação esperada ${e.col}, veio "${linha(txt, "Data (colocação):")}" (createTime em UTC → São Paulo)`);
    if (e.ev && linha(txt, "Data (evento mais recente):") !== e.ev) falhas.push(`${idb}: evento esperado ${e.ev}, veio "${linha(txt, "Data (evento mais recente):")}"`);
    if ((txt.match(/^- /gm) || []).length !== e.pernas) falhas.push(`${idb}: esperava ${e.pernas} seleção(ões) no bloco`);
    if (/^Retorno potencial/m.test(txt)) falhas.push(`${idb}: liquidada com "Retorno potencial"`);
  }

  // O carimbo é a colocação em São Paulo, e cruza a meia-noite: 22/10 00:56 UTC = 21/10 21:56.
  {
    const c = linha(fmt(porId.get("C2225866") || {}), "Carimbo de colocação:");
    if (c !== "20261021215600") falhas.push(`C2225866: carimbo esperado 20261021215600, veio "${c}" (dia da cotação em São Paulo)`);
  }

  // A múltipla ganha do card: 3 props da NBA, odd de cada perna, mercado + seleção com a linha.
  {
    const txt = fmt(porId.get("C2225866") || {});
    if (!/^- Player Green Jalen - total assists and rebounds \(incl\. overtime\): Under 7\.5 \[perna ganha\]$/m.test(txt)) falhas.push("C2225866: a perna do Jalen Green não saiu como no card (mercado: seleção linha [perna ganha])");
    if (!/Jogo: Portland Trail Blazers vs Phoenix Suns · Liga: NBA · Esporte: Basquete/.test(txt)) falhas.push("C2225866: jogo/liga/esporte da perna faltando (gameId 11 = Basquete)");
    if (!/Odd da perna: 2,28/.test(txt) || !/Odd da perna: 2,17/.test(txt) || !/Odd da perna: 1,7(\D|$)/m.test(txt)) falhas.push("C2225866: faltou a odd de cada perna");
  }
  // Perdida com as 3 pernas vermelhas.
  {
    const txt = fmt(porId.get("C2225863") || {});
    if ((txt.match(/\[perna perdida\]$/gm) || []).length !== 3) falhas.push("C2225863: as 3 pernas perdidas não estão ditas como perdidas");
  }
  // Simples de eSports: handicap com sinal, e o CS2 dito pelo `gameId` 6.
  {
    const txt = fmt(porId.get("S4965610") || {});
    if (!/^- Round Handicap - Map 2: Vitality -5\.5/m.test(txt)) falhas.push("S4965610: mercado/seleção/linha não saíram como no card (Vitality -5.5, Round Handicap - Map 2)");
    if (!/Jogo: Vitality vs Wildcard · Liga: BLAST Rivals Spring 2025/.test(txt)) falhas.push("S4965610: jogo/liga faltando");
    if (!/Esporte: [^\n]*E-Sports/.test(txt) || !/CS2/.test(txt)) falhas.push("S4965610: gameId 6 não virou E-Sports (CS2)");
    if (/Odd da perna/.test(txt)) falhas.push("S4965610: simples com linha de odd da perna (repete a do bilhete)");
  }
  // Abertas: a múltipla com uma perna JÁ ganha continua em aberto, e o retorno é potencial.
  {
    const aberta = fmt(porId.get("C2225869") || {});
    testes++;
    if (!/^em aberto \(aguardando resultado — NÃO liquidar; sem resultado\)$/.test(linha(aberta, "Status:"))) falhas.push(`C2225869: aberta virou "${linha(aberta, "Status:")}" (perna ganha não liquida o bilhete)`);
    if (linha(aberta, "Retorno potencial (se ganhar):") !== "329,00 EUR") falhas.push(`C2225869: retorno potencial esperado 329,00 EUR (22,26 × 14,78), veio "${linha(aberta, "Retorno potencial (se ganhar):")}"`);
    if (/^Retorno:/m.test(aberta)) falhas.push("C2225869: aberta com linha \"Retorno:\" (potencial não é retorno)");
    if (!/^- Player Strazel Matthew - total assists and rebounds \(incl\. overtime\): Over 6\.5 \[perna ganha\]$/m.test(aberta)) falhas.push("C2225869: a perna já ganha não está marcada");
    if ((aberta.match(/^- .*\[perna /gm) || []).length !== 1) falhas.push("C2225869: perna ainda em aberto marcada como decidida");
    const simples = fmt(porId.get("S10286616") || {});
    testes++;
    if (!/^em aberto \(aguardando resultado — NÃO liquidar; sem resultado\)$/.test(linha(simples, "Status:"))) falhas.push(`S10286616: aberta virou "${linha(simples, "Status:")}"`);
    if (linha(simples, "Retorno potencial (se ganhar):") !== "38,97 EUR") falhas.push(`S10286616: retorno potencial esperado 38,97 EUR, veio "${linha(simples, "Retorno potencial (se ganhar):")}"`);
  }

  // Dinheiro sem amostra real: clone da perdida, só o que o número prova vira resultado.
  {
    const base = porId.get("S10286602");   // 22,27 × 2,24, perdida
    if (!base) falhas.push("S10286602: a perdida-base dos clones não chegou");
    else {
      const c = (o) => linha(fmt(Object.assign({}, base, o)), "Status:");
      const trunc = c({ estado: "won", retorno: 49.88 });
      if (!W("49,88").test(trunc)) falhas.push(`won com retorno truncado (49,88 de 49,8848) virou "${trunc}"`);
      const arred = c({ estado: "won", retorno: 49.89 });
      if (!W("49,89").test(arred)) falhas.push(`won com retorno arredondado para cima (49,89) virou "${arred}" (a casa arredonda dos dois jeitos)`);
      const naoFecha = c({ estado: "won", retorno: 45 });
      if (!/a conferir — não liquidar automaticamente/.test(naoFecha)) falhas.push(`won com dinheiro que não fecha com a odd virou "${naoFecha}"`);
      const cancelada = c({ estado: "cancelled", cancelamento: "Event cancelled", retorno: 22.27 });
      if (!/→ V$/.test(cancelada)) falhas.push(`cancelada com retorno = stake virou "${cancelada}"`);
      const desconhecidoStake = c({ estado: "refunded", retorno: 22.27 });
      if (!/→ V$/.test(desconhecidoStake)) falhas.push(`estado desconhecido com retorno = stake virou "${desconhecidoStake}" (P/L 0 prova V)`);
      const desconhecido = c({ estado: "halfwon", retorno: 30 });
      if (!/a conferir — não liquidar automaticamente/.test(desconhecido)) falhas.push(`estado desconhecido com retorno ≠ stake virou "${desconhecido}"`);
      // O dinheiro de W com rótulo que não é "won" não vira W: sem amostra, o rótulo manda parar.
      const desconhecidoComW = c({ estado: "halfwon", retorno: 49.88 });
      if (!/a conferir — não liquidar automaticamente/.test(desconhecidoComW)) falhas.push(`estado desconhecido com retorno = stake × odd virou "${desconhecidoComW}"`);
      const cancComDinheiro = c({ estado: "lost", cancelamento: "Event cancelled", retorno: 0 });
      if (L.test(cancComDinheiro)) falhas.push(`perdida com \`cancelReason\` virou "${cancComDinheiro}" (o motivo desmente o rótulo)`);
      const perdidaComDinheiro = c({ estado: "lost", retorno: 12 });
      if (L.test(perdidaComDinheiro)) falhas.push(`lost com retorno 12 virou "${perdidaComDinheiro}" (o dinheiro desmente o rótulo)`);
      const cash = c({ estado: "won", cashoutOdd: 1.5, retorno: 33.4 });
      if (!/a conferir — não liquidar automaticamente/.test(cash) || !/cashout 33,40/.test(cash)) falhas.push(`cashout sem amostra virou "${cash}" (o valor tem de subir, a decisão não)`);
      const aberta = fmt(Object.assign({}, base, { estado: "open", retorno: null }));
      if (!/^em aberto \(aguardando resultado — NÃO liquidar; sem resultado\)$/.test(linha(aberta, "Status:"))) falhas.push(`open virou "${linha(aberta, "Status:")}"`);
      if (linha(aberta, "Retorno potencial (se ganhar):") !== "49,88 EUR") falhas.push("open sem o retorno potencial (22,27 × 2,24)");
      // Na simples, a perna diz o estado do BILHETE: aberta não pode sair com perna decidida.
      if (/\[perna /.test(aberta)) falhas.push("simples aberta com a perna marcada como decidida");
      const fb = fmt(Object.assign({}, base, { freebet: 22.27 }));
      // O rótulo é o que o servidor lê (`freebets_do_texto`); outra grafia some do P/L.
      if (!/^Freebet inclu[íi]do: 22,27 EUR/m.test(fb)) falhas.push("freebet não está dita com o rótulo que o servidor lê");
      const semOdd = linha(fmt(Object.assign({}, base, { odd: 0 })), "Odd:");
      if (!/deixe a odd VAZIA/.test(semOdd)) falhas.push(`odd 0 virou "${semOdd}" (zero não é ausência)`);
      const esp = fmt(Object.assign({}, base, { pernas: base.pernas.map((p) => Object.assign({}, p, { esporteId: 99 })) }));
      if (!/gameId 99/.test(esp) || /Esporte: Basquete/.test(esp)) falhas.push("gameId fora do mapa não subiu cru (ou foi chutado)");
    }
  }

  testes += await resolvidaVenceAberta(falhas);
  testes += await paginacao(falhas, 230, "0,100,200");
  testes += await paginacao(falhas, 200, "0,100");
  // O teto real do `take` não foi medido: se a casa devolver menos que o pedido, o avanço é
  // pelo tamanho que VOLTOU, senão bilhetes ficam para trás sem erro nenhum.
  testes += await paginacao(falhas, 230, "0,50,100,150,200", 50);
  testes += await partidaAFrio(falhas);
  testes += await semToken(falhas);
  return { falhas, testes };
}

// O mesmo bilhete nas duas listas (liquidou entre as duas chamadas): a liquidada vence.
async function resolvidaVenceAberta(falhas) {
  const resolvidas = RES();
  const ganha = resolvidas.find((w) => w.wagerId === 2225866);
  const comoAberta = Object.assign({}, ganha, { wagerUIState: "open", outcome: undefined, state: undefined, finishTime: undefined });
  const { ultima } = await rodarPadrao(resolvidas, [comoAberta].concat(PEN()), []);
  const b = ((ultima && ultima.bilhetes) || []).filter((x) => x.id === "C2225866");
  if (b.length !== 1) falhas.push(`liquidada × aberta: C2225866 veio ${b.length} vez(es)`);
  else if (!W("187,20").test(linha(carregarContent().pegar("formatTicketTHP")(b[0]), "Status:"))) falhas.push("liquidada × aberta: a versão aberta venceu a liquidada");
  return 1;
}

// N liquidadas em páginas de 100: as páginas EXATAS pelo total da 1ª, nenhuma a mais. Com 200,
// quem para pela lista vazia pede `skip=200` e ainda lê `totalWagersCount: 0` dali.
async function paginacao(falhas, n, esperado, tetoTake = Infinity) {
  const modelo = RES();
  const resolvidas = [];
  for (let i = 0; i < n; i++) resolvidas.push(Object.assign({}, modelo[i % modelo.length], { wagerId: 90000000 + i }));
  const registro = [];
  const { ultima } = await rodarPadrao(resolvidas, PEN(), registro, {}, tetoTake);
  const liq = ((ultima && ultima.bilhetes) || []).filter((b) => /^[CS]9\d{7}$/.test(b.id)).length;
  const rot = n + (isFinite(tetoTake) ? ` com teto ${tetoTake}` : "");
  if (liq !== n) falhas.push(`paginação ${rot}: esperava ${n} liquidadas, vieram ${liq}`);
  const skips = _resolvidas(registro).slice(1).map((r) => r.q.skip);
  if (skips.join(",") !== esperado) falhas.push(`paginação ${rot}: skips pedidos ${skips.join(",") || "(nenhum)"}, esperava ${esperado} (fim = totalWagersCount da 1ª página)`);
  return 1;
}

// A frio: a página não fez requisição nenhuma (inject tardio). O token sai do localStorage.
async function partidaAFrio(falhas) {
  const registro = [];
  const { ultima } = await rodarPadrao(RES(), PEN(), registro, { href: HOST + "/en", semRequisicaoInicial: true, janelaExtra: LS(TOKEN) });
  const n = ((ultima && ultima.bilhetes) || []).length;
  if (n !== 42) falhas.push(`a frio: esperava 42 bilhetes pelo token do localStorage, vieram ${n}`);
  if (ultima && ultima.semToken) falhas.push("a frio: `semToken` com o token no localStorage");
  if (registro.some((r) => r.tok !== TOKEN)) falhas.push("a frio: requisição sem o token do localStorage");
  return 1;
}

// Sem sessão: nada no localStorage e nenhuma chamada da página. Diz `semToken` e não pede nada.
async function semToken(falhas) {
  const registro = [];
  const { ultima } = await rodarPadrao(RES(), PEN(), registro, { href: HOST + "/en", semRequisicaoInicial: true, janelaExtra: LS(null), ms: 300 });
  if (!ultima || !ultima.semToken) falhas.push("sem sessão: o inject não disse `semToken`");
  if (registro.some((r) => /\/api\/wagers\//.test(r.p))) falhas.push("sem sessão: o inject pediu as apostas sem o token");
  return 1;
}
