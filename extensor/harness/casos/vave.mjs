// Vave (34evav91.com, vave.com) — captura por API `GET platform.<host>/api/v2/bet/history`.
// Recon s425, conta do Feca (USDT), pelo navegador dele.
//
// PLATAFORMA PRÓPRIA (`softlabs`, app `vavemain`). O layout lembra a 1xBet, mas o bundle e a API
// não têm nada a ver com ela. Inject e formatador próprios (`vv_inject.js`, `formatTicketVV`).
//
// A FIXTURE `vave.history.json` é a resposta da casa à aba "Todos" (12 meses, limit 100): a conta
// INTEIRA no dia do recon, 11 bilhetes, todos PERDIDOS, 10 múltiplas e 1 simples, em USDT. Só o
// `userId` foi zerado. `vave.dicionarios.json` é o recorte dos dois dicionários públicos da casa
// (`get-all-markets` e `get-all-outcomes`), só com os ids que a fixture usa — o original tem
// 1,4 MB.
//
// O que este caso trava, cada item cruzado com o card da casa (Histórico de apostas):
//   • CÓDIGO = `id` (o "#5435097" do card). DATA DO CARD = `ts` (colocação) em São Paulo
//     (1792502331 → "20.10.2026 10:18").
//   • ODD = `value`, que já é o produto das pernas (5433248: 3,29 × 2,13 × 2,24 = 15,7 no card).
//   • PERNA: `details[].status` 1 = vermelha (perdida), 2 = verde (ganha) — 5433248 é
//     vermelha · verde · vermelha no card.
//   • NOMES NÃO VÊM NO HISTÓRICO: jogo, liga e esporte saem das tabelas irmãs do mesmo lote
//     (`events`, `competitors`, `leagues`…) e mercado/seleção dos dicionários, em template
//     Sportradar (`{$competitor2} ({-hcp})` com `hcp=1` → "Cruzeiro Basquete (-1)").
//   • REPLAY: Bearer no header (por XHR na página) ou, a frio, de `localStorage.customer.token`.
//     Erro volta com HTTP 200 e `code: 401`; `limit` tem teto 100; `total` é o número de
//     PÁGINAS e o fim é `page >= total`.
//
// NÃO COBERTO pela fixture (a conta não tinha): ganha, aberta, devolvida, cashout, freebet, bet
// builder e sistema. Os casos de dinheiro estão travados abaixo por CLONE da perdida (subir "a
// conferir" quando o número não prova), não por amostra real. O caminho XHR do inject também
// não: o sandbox entrega a requisição da página por fetch (o XHR foi provado ao vivo).
import { rodarInject, carregarContent, fixture, linha } from "../sandbox.mjs";

export const casa = "Vave";

const L = /^Perdeu → L$/;
const M2 = /^Múltipla \(2 seleções\)$/;
const M3 = /^Múltipla \(3 seleções\)$/;

// id → o que o card mostra. `col` = data do card (colocação); `ev` = início da perna mais tardia.
const ESPERADO = {
  "5435097": { st: L, odd: "9,19",  stake: "30,00", tipo: M2, col: "20/10/2026 10:18:51", ev: "21/10/2026 15:00:00", pernas: 2 },
  "5433760": { st: L, odd: "4,2",   stake: "30,00", tipo: /^Simples$/, col: "20/10/2026 00:09:30", ev: "21/10/2026 19:00:00", pernas: 1 },
  "5433248": { st: L, odd: "15,7",  stake: "30,00", tipo: M3, col: "19/10/2026 18:27:27", ev: "20/10/2026 16:00:00", pernas: 3 },
  "5432746": { st: L, odd: "10,77", stake: "30,00", tipo: M2, pernas: 2 },
  "5432723": { st: L, odd: "9,75",  stake: "5,00",  tipo: M2, pernas: 2 },
};

const HOST = "https://34evav91.com";
const API = "https://platform.34evav91.com";
const TOKEN = "harness.token.falso.vave";
const HDRS = { accept: "application/json", "content-type": "application/json", "x-requested-with": "XMLHttpRequest",
               authorization: "Bearer " + TOKEN, "client-timezone": "America/Sao_Paulo" };

const HIST = () => JSON.parse(fixture("vave.history.json"));
const DIC = () => JSON.parse(fixture("vave.dicionarios.json"));

// Simula a casa: `page`/`limit`, `total` em PÁGINAS, erro com HTTP 200 como os medidos.
function casaVV(bets, registro, op = {}) {
  const tabelas = HIST().data.bets;
  const dic = DIC();
  return (url, opts) => {
    if (!String(url).startsWith(API)) return null;
    const u = new URL(String(url));
    const h = (opts && opts.headers) || {};
    const auth = h.authorization || h.Authorization || "";
    registro.push({ p: u.pathname, q: Object.fromEntries(u.searchParams), auth });
    if (/get-all-markets/.test(u.pathname)) return op.semDicionario ? null : JSON.stringify(dic.markets);
    if (/get-all-outcomes/.test(u.pathname)) return op.semDicionario ? null : JSON.stringify(dic.outcomes);
    if (u.pathname !== "/api/v2/bet/history") return JSON.stringify({ status: "ok", code: 200, data: {} });
    if (auth !== "Bearer " + TOKEN) {
      return JSON.stringify({ status: "error", data: { messages: ["Iniciar sessão para participar na ação"], status: "error", auth: false, apiErrorCode: 32 },
                              messages: ["Iniciar sessão para participar na ação"], code: 401 });
    }
    const limit = Number(u.searchParams.get("limit") || 10);
    if (limit > 100) return JSON.stringify({ status: "fail", code: 400, message: "validation", data: { limit: "This value should be less than or equal to 100." } });
    const page = Number(u.searchParams.get("page") || 1);
    const fatia = bets.slice((page - 1) * limit, page * limit);
    return JSON.stringify({ status: "ok", code: 200, data: {
      bets: Object.assign({}, tabelas, { bets: fatia }), columns: [], limit, page: String(page),
      total: Math.ceil(bets.length / limit) } });
  };
}

const LS = (tok) => ({ localStorage: { getItem: (k) => (k === "customer" && tok ? JSON.stringify({ id: 1, token: tok }) : null) } });

export async function rodar() {
  const bets = HIST().data.bets.bets;
  const registro = [];
  // A requisição REAL da página: aba "Todos", 30 dias, limit 10, com o Bearer.
  const { ultima, mensagens } = await rodarInject({
    inject: "vv_inject.js",
    href: HOST + "/pt/cabinet/betting-history",
    urlInicial: API + "/api/v2/bet/history?page=1&from=2026-09-21&till=2026-10-21&limit=10&lang=pt&_trlang=pt",
    optsInicial: { method: "GET", headers: HDRS },
    pedido: "__sharpenupVVReq",
    responder: casaVV(bets, registro),
    ms: 600,
  });

  const falhas = [];
  if (!ultima) return { falhas: ["o inject não emitiu nenhuma mensagem"], testes: 0 };
  if (!ultima.hook) falhas.push("o inject não emitiu `hook:true` (autodiagnóstico cego)");
  if (!(ultima.respostas >= 2)) falhas.push(`\`respostas\` baixo demais (veio ${ultima.respostas})`);
  if (!ultima.fim) falhas.push("o inject não sinalizou `fim` (o robô ficaria esperando o teto)");
  if (ultima.semDicionario) falhas.push("o dicionário de mercados não carregou");
  if (JSON.stringify(mensagens).includes(TOKEN)) falhas.push("o token vazou na mensagem para o content");

  const bilhetes = ultima.bilhetes || [];
  if (bilhetes.length !== bets.length) falhas.push(`esperava ${bets.length} bilhetes, vieram ${bilhetes.length}`);

  const replay = registro.filter((r) => r.p === "/api/v2/bet/history").slice(1);
  if (!replay.length) falhas.push("o replay não rodou");
  if (replay.some((r) => r.auth !== "Bearer " + TOKEN)) falhas.push("o replay não levou o Bearer aprendido");
  if (replay.some((r) => Number(r.q.limit) > 100)) falhas.push("o replay pediu `limit` acima de 100 (a casa recusa)");
  if (replay.some((r) => r.q.status != null)) falhas.push("o replay pediu com filtro de status — sem ele a casa devolve tudo");
  if (replay.some((r) => !(r.q.from <= "2024-01-01"))) falhas.push("o replay não alargou a janela da tela (30 dias) para o histórico");
  if (replay.length !== 1) falhas.push(`replay pediu ${replay.length} página(s) para 11 bilhetes em páginas de 100 — não parou no total`);

  // O cru tem de ser o bilhete da casa, com o código igual ao do texto e as tabelas irmãs que
  // ele usa (sem elas o `details[]` é só id) — e SEM o `userId`, que identifica o cliente.
  const cru = ultima.cru || [];
  if (cru.length !== bets.length) falhas.push(`cru: esperava ${bets.length} itens, vieram ${cru.length}`);
  for (const c of cru) {
    if (!c.cru || !c.cru.bet || String(c.cru.bet.id) !== c.codigo) falhas.push(`cru ${c.codigo}: não é o bilhete da casa com o mesmo id`);
    else if ("userId" in c.cru.bet) falhas.push(`cru ${c.codigo}: levou o \`userId\` da conta`);
    else if (c.cru.events.length !== c.cru.bet.details.length || !c.cru.competitors.length) falhas.push(`cru ${c.codigo}: faltam os eventos/times das pernas`);
  }

  const fmt = carregarContent().pegar("formatTicketVV");
  const porId = new Map(bilhetes.map((b) => [b.id, b]));
  let testes = 0;

  for (const b of bilhetes) {
    const txt = fmt(b);
    if (!txt.startsWith(`[Código: ${b.id}]`)) falhas.push(`${b.id}: marcador [Código:] ausente/errado`);
    if (!/^\d{7}$/.test(b.id)) falhas.push(`${b.id}: código fora da série de 7 dígitos do card`);
    if (linha(txt, "Moeda:") !== "USDT") falhas.push(`${b.id}: faltou a linha "Moeda: USDT"`);
    if (!/^\d{14}$/.test(linha(txt, "Carimbo de colocação:"))) falhas.push(`${b.id}: faltou o carimbo de colocação (dia da cotação)`);
    if (/R\$/.test(txt)) falhas.push(`${b.id}: o bloco diz "R$" numa conta em USDT`);
    if (!linha(txt, "Status (API):")) falhas.push(`${b.id}: falta o status cru da API`);
    if (/^0*(,0*)?$/.test(linha(txt, "Odd:"))) falhas.push(`${b.id}: odd zerada ou ausente`);
    if (/\{[^}]*\}/.test(txt)) falhas.push(`${b.id}: template da casa sem resolver no bloco`);
    if (/sem nome/.test(txt)) falhas.push(`${b.id}: perna sem nome de mercado`);
    if (!/^Data \(evento mais recente\): \d\d\/\d\d\/\d{4} /m.test(txt)) falhas.push(`${b.id}: sem data de evento`);
  }

  for (const [idb, e] of Object.entries(ESPERADO)) {
    const b = porId.get(idb);
    if (!b) { falhas.push(`${idb}: não chegou ao lote`); continue; }
    const txt = fmt(b);
    testes++;
    const odd = linha(txt, "Odd:"), st = linha(txt, "Status:"), stake = linha(txt, "Stake:");
    if (!e.st.test(st)) falhas.push(`${idb}: status "${st}"`);
    if (odd !== e.odd) falhas.push(`${idb}: odd esperada ${e.odd}, veio "${odd}"`);
    if (stake !== e.stake) falhas.push(`${idb}: stake esperada ${e.stake}, veio "${stake}"`);
    if (!e.tipo.test(linha(txt, "Tipo:"))) falhas.push(`${idb}: tipo "${linha(txt, "Tipo:")}"`);
    if (e.col && linha(txt, "Data (colocação):") !== e.col) falhas.push(`${idb}: colocação esperada ${e.col}, veio "${linha(txt, "Data (colocação):")}" (ts é unix em segundos, card em São Paulo)`);
    if (e.ev && linha(txt, "Data (evento mais recente):") !== e.ev) falhas.push(`${idb}: evento esperado ${e.ev}, veio "${linha(txt, "Data (evento mais recente):")}"`);
    if ((txt.match(/^- /gm) || []).length !== e.pernas) falhas.push(`${idb}: esperava ${e.pernas} seleção(ões) no bloco`);
  }

  // A múltipla de 3 do card (vermelha · verde · vermelha), com os dois handicaps de sinais
  // opostos: `{-hcp}` com hcp=1 é "-1", `{+hcp}` com hcp=-2.5 é "-2.5".
  {
    const txt = fmt(porId.get("5433248") || {});
    if (!/^- Oxford United clean sheet: yes \[perna perdida\]$/m.test(txt)) falhas.push("5433248: a 1ª perna (clean sheet do mandante) não saiu como no card");
    if (!/^- 1st half - handicap: Cruzeiro Basquete \(-1\) \[perna ganha\]$/m.test(txt)) falhas.push("5433248: `{-hcp}` com hcp=1 não virou \"(-1)\", ou a perna verde não está dita como ganha");
    if (!/^- 1st half - corner handicap: Roma \(-2\.5\) \[perna perdida\]$/m.test(txt)) falhas.push("5433248: `{+hcp}` com hcp=-2.5 não virou \"(-2.5)\"");
    if (!/Jogo: EC Uniao Corinthians - Cruzeiro Basquete · Liga: Brazil · NBB · Esporte: Basketball/.test(txt)) falhas.push("5433248: jogo/liga/esporte da perna do basquete faltando");
    if (!/Especificadores \(cru da casa\): hcp=1$/m.test(txt)) falhas.push("5433248: o cru do especificador não subiu");
    if (!/Odd da perna: 3,29/.test(txt) || !/Odd da perna: 2,13/.test(txt) || !/Odd da perna: 2,24/.test(txt)) falhas.push("5433248: faltou a odd de cada perna");
  }
  // `{!quarternr}` = ordinal; o `{$competitor2}` do mercado da simples é o visitante do card.
  {
    const t1 = fmt(porId.get("5432739") || {});
    if (!/^- 1st quarter - total: over 42\.5 /m.test(t1)) falhas.push("5432739: `{!quarternr} quarter - total` com quarternr=1 não virou \"1st quarter - total: over 42.5\"");
    const t2 = fmt(porId.get("5433760") || {});
    if (!/^- Clube Atletico Mineiro clean sheet: yes \[perna perdida\]$/m.test(t2)) falhas.push("5433760: `{$competitor2}` não virou o visitante (Clube Atletico Mineiro)");
    if (/Odd da perna/.test(t2)) falhas.push("5433760: simples com linha de odd da perna (repete a do bilhete)");
  }

  // Dinheiro sem amostra real: clone da perdida, só o que o número prova vira resultado.
  {
    const base = porId.get("5432746");   // 30 × 10,77
    if (base) {
      const c = (o) => linha(fmt(Object.assign({}, base, o)), "Status:");
      const ganhaRet = c({ status: 2, ganhoTotal: 323.1, ganho: 0 });
      if (!/^Ganhou → W \(retorno 323,10 USDT\)$/.test(ganhaRet)) falhas.push(`status 2 com winFull = stake × odd virou "${ganhaRet}"`);
      const ganhaLucro = c({ status: 2, ganhoTotal: 0, ganho: 293.1 });
      if (!/^Ganhou → W \(retorno 323,10 USDT\)$/.test(ganhaLucro)) falhas.push(`status 2 com win = stake × (odd − 1) virou "${ganhaLucro}"`);
      const naoFecha = c({ status: 2, ganhoTotal: 300, ganho: 270 });
      if (!/a conferir — não liquidar automaticamente/.test(naoFecha)) falhas.push(`status 2 com dinheiro que não fecha com a odd virou "${naoFecha}"`);
      const devolvida = c({ status: 3, ganhoTotal: 30, ganho: 0 });
      if (!/→ V$/.test(devolvida)) falhas.push(`status 3 com winFull = stake virou "${devolvida}"`);
      // O dinheiro de W com rótulo que não é "ganhou" não vira W: sem amostra, o rótulo manda parar.
      const devolvidaComW = c({ status: 3, ganhoTotal: 323.1, ganho: 293.1 });
      if (!/a conferir — não liquidar automaticamente/.test(devolvidaComW)) falhas.push(`status 3 com winFull = stake × odd virou "${devolvidaComW}"`);
      const cashStake = c({ status: 8, cashout: 30, ganhoTotal: null, ganho: null });
      if (!/→ V$/.test(cashStake)) falhas.push(`cashout = stake virou "${cashStake}"`);
      const cash = c({ status: 8, cashout: 41.2, ganhoTotal: 41.2, ganho: 11.2 });
      if (!/a conferir — não liquidar automaticamente/.test(cash) || !/cashout 41,20/.test(cash)) falhas.push(`cashout sem amostra virou "${cash}" (o valor tem de subir, a decisão não)`);
      const perdidaComDinheiro = c({ status: 1, ganhoTotal: 12, ganho: 0 });
      if (/Perdeu → L/.test(perdidaComDinheiro)) falhas.push(`status 1 com winFull 12 virou "${perdidaComDinheiro}" (o dinheiro desmente o rótulo)`);
      const novo = c({ status: 9, ganhoTotal: 0, ganho: 0 });
      if (!/a conferir — não liquidar automaticamente/.test(novo)) falhas.push(`status desconhecido virou "${novo}"`);
      const aberta = fmt(Object.assign({}, base, { status: 0, potencial: 323.1 }));
      if (!/^em aberto \(aguardando resultado — NÃO liquidar; sem resultado\)$/.test(linha(aberta, "Status:"))) falhas.push(`status 0 virou "${linha(aberta, "Status:")}"`);
      if (linha(aberta, "Retorno potencial (se ganhar):") !== "323,10 USDT") falhas.push("aberta sem o retorno potencial");
      if (/^Retorno:/m.test(aberta)) falhas.push("aberta com linha \"Retorno:\" (potencial não é retorno)");
      const sis = linha(fmt(Object.assign({}, base, { sistema: 2 })), "Tipo:");
      if (!/Sistema/.test(sis) || !/NUNCA o produto/.test(sis)) falhas.push(`system 2 virou tipo "${sis}"`);
      const fb = fmt(Object.assign({}, base, { freebet: 30 }));
      // O rótulo é o que o servidor lê (`freebets_do_texto`); outra grafia some do P/L.
      if (!/^Freebet inclu[íi]do: 30,00 USDT/m.test(fb)) falhas.push("freebet não está dita com o rótulo que o servidor lê");
      const semOdd = linha(fmt(Object.assign({}, base, { odd: 0 })), "Odd:");
      if (!/deixe a odd VAZIA/.test(semOdd)) falhas.push(`odd 0 virou "${semOdd}" (zero não é ausência)`);
    }
  }

  testes += await paginacao(falhas);
  testes += await partidaAFrio(falhas);
  testes += await semToken(falhas);
  testes += await semDicionario(falhas);
  return { falhas, testes };
}

// 230 bilhetes em páginas de 100: 3 páginas EXATAS, nenhuma a mais.
async function paginacao(falhas) {
  const modelo = HIST().data.bets.bets;
  const bets = [];
  for (let i = 0; i < 230; i++) bets.push(Object.assign({}, modelo[i % modelo.length], { id: 9000000 + i }));
  const registro = [];
  const { ultima } = await rodarInject({
    inject: "vv_inject.js", href: HOST + "/pt/cabinet/betting-history",
    urlInicial: API + "/api/v2/bet/history?page=1&from=2026-09-21&till=2026-10-21&limit=10&lang=pt",
    optsInicial: { method: "GET", headers: HDRS },
    pedido: "__sharpenupVVReq", responder: casaVV(bets, registro), ms: 600,
  });
  const n = ((ultima && ultima.bilhetes) || []).length;
  if (n !== 230) falhas.push(`paginação: esperava 230 bilhetes, vieram ${n}`);
  const pags = registro.filter((r) => r.p === "/api/v2/bet/history").slice(1).map((r) => r.q.page);
  // EXATO: quem para pela lista vazia em vez do `total` pede uma página a mais a cada varredura.
  if (pags.join(",") !== "1,2,3") falhas.push(`paginação: páginas pedidas ${pags.join(",") || "(nenhuma)"}, esperava 1,2,3 (total = páginas)`);
  return 1;
}

// A frio: a página não fez requisição nenhuma (domínio novo, inject tardio). O Bearer sai do
// `localStorage.customer.token`.
async function partidaAFrio(falhas) {
  const registro = [];
  const { ultima } = await rodarInject({
    inject: "vv_inject.js", href: "https://vave.com/pt/cabinet/betting-history",
    semRequisicaoInicial: true, janelaExtra: LS(TOKEN),
    pedido: "__sharpenupVVReq",
    // A API mora em `platform.` do host da ABA: em vave.com, `platform.vave.com`.
    responder: (u, o) => casaVV(HIST().data.bets.bets, registro)(String(u).replace("platform.vave.com", "platform.34evav91.com"), o),
    ms: 600,
  });
  const n = ((ultima && ultima.bilhetes) || []).length;
  if (n !== 11) falhas.push(`a frio: esperava 11 bilhetes pelo token do localStorage, vieram ${n}`);
  if (ultima && ultima.semToken) falhas.push("a frio: `semToken` com o token no localStorage");
  return 1;
}

// Sem sessão: nada no localStorage e nenhuma chamada da página. Diz `semToken` e não pede nada.
async function semToken(falhas) {
  const registro = [];
  const { ultima } = await rodarInject({
    inject: "vv_inject.js", href: HOST + "/pt", semRequisicaoInicial: true, janelaExtra: LS(null),
    pedido: "__sharpenupVVReq", responder: casaVV(HIST().data.bets.bets, registro), ms: 300,
  });
  if (!ultima || !ultima.semToken) falhas.push("sem sessão: o inject não disse `semToken`");
  if (registro.some((r) => r.p === "/api/v2/bet/history")) falhas.push("sem sessão: o inject pediu o histórico sem Bearer");
  return 1;
}

// Dicionário fora do ar: a captura SEGUE, com o id do mercado no lugar do nome.
async function semDicionario(falhas) {
  const { ultima } = await rodarInject({
    inject: "vv_inject.js", href: HOST + "/pt/cabinet/betting-history",
    urlInicial: API + "/api/v2/bet/history?page=1&from=2026-09-21&till=2026-10-21&limit=10&lang=pt",
    optsInicial: { method: "GET", headers: HDRS },
    pedido: "__sharpenupVVReq", responder: casaVV(HIST().data.bets.bets, [], { semDicionario: true }), ms: 600,
  });
  const bs = (ultima && ultima.bilhetes) || [];
  if (bs.length !== 11) falhas.push(`sem dicionário: esperava 11 bilhetes, vieram ${bs.length} (o dicionário não pode parar a captura)`);
  if (!(ultima && ultima.semDicionario)) falhas.push("sem dicionário: o inject não disse `semDicionario`");
  const txt = carregarContent().pegar("formatTicketVV")(bs.find((b) => b.id === "5433760") || {});
  if (!/^- \(mercado id 844, sem nome\): seleção id 74 \[perna perdida\]$/m.test(txt)) falhas.push("sem dicionário: a perna não saiu com o id do mercado e da seleção");
  return 1;
}
