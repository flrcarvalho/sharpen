// Shuffle (shuffle.com) — captura por GraphQL `POST /main-api/graphql/sports-main/
// graphql-sports-main`, operação `GetSportsBets` (`sportsBetsV3`). Recon s401, conta do Feca.
//
// PLATAFORMA PRÓPRIA: app Next.js, sportsbook em GraphQL no host da casa, odds da Betradar.
// Primeira casa GraphQL do SharpenUp. Inject e formatador próprios (`shf_inject.js`).
//
// A FIXTURE (`shuffle.sportsbets.json`) é a conta INTEIRA no dia do recon (31 bilhetes: 8
// abertos, 23 liquidados), lida pelo replay sem filtro de status. É um payload ENXUTO: só os
// campos que o inject lê, e os ids trocados por `SHFfixture…` com o mesmo comprimento (21) —
// a ferramenta do navegador mascarava os ids reais na saída. Valores, datas e textos são os
// da casa, sem edição.
//
// Cada esperado abaixo foi lido do CARD da casa (aba "Apostas encerradas", páginas 1 e 2)
// quando a coluna `p` diz "card"; "json" é bilhete que o card não chegou a mostrar na
// conferência. O card arredonda a odd a 2 casas (6,356 → "6,36"), então a odd esperada é a
// do payload — odd nunca truncada é regra primordial —, e o card confere o resto.
//
// O que este caso trava, cada item cruzado com o card:
//   • MÚLTIPLA COM PERNA ANULADA (push): o card estampa "Total de probabilidades 11,52" e
//     "Você ganhou US$ 51,19" sobre US$ 10. A odd do bilhete é 5,1192 (retorno ÷ stake), não
//     11,5182 (a da colocação, que a casa não revisa no card).
//   • SISTEMA "GANHO" COM PREJUÍZO: Duplos de 3, card "VITÓRIA" e "Você ganhou US$ 55,00"
//     sobre US$ 60. O retorno real é 54,996 (3 casas, USDT) — arredondar para 55,00 faria o
//     gate do retorno (`_veredito_do_retorno`) ler outro número e reescrever a odd.
//   • SISTEMA PERDIDO: `totalOddsDecimal` já é a MÉDIA das 3 duplas (5,6298), e o `amount` é o
//     stake TOTAL (60 = 3 × 20, card "3 Apostas US$ 20,00 · Sua aposta US$ 60,00").
//   • FUSO: evento e colocação em America/Sao_Paulo. O 7 tem a perna mais recente às 02:00Z de
//     08/10 — em São Paulo é 23:00 de 07/10, outro dia.
//   • MOEDA: a conta é em USDT; nenhum "R$" no bloco.
//   • REPLAY: a página pede `first: 9` com filtro de aba; o replay pede SEM filtro e anda pelo
//     cursor até `nextCursor: null`. O responder abaixo serve páginas de 7 para provar que o
//     avanço é pelo cursor que VOLTOU, e devolve erro para `first > 20`, como a casa.
//   • BILHETE ALHEIO: o rodapé da casa lista apostas de outros usuários. Um nó com `user`
//     preenchido nunca entra no lote.
//
// NÃO COBERTO pela regra "liquidada vence aberta" do inject: ela só decide numa CORRIDA entre
// uma resposta da página (passiva) e o replay, e o sandbox entrega as duas em ordem fixa — a
// mutação que a remove passa verde (medido). O mesmo vale para o ouvinte do content.
//
// NÃO COBERTO pela fixture: cashout executado, anulada/cancelada (VOIDED/CANCELLED), PARTIAL,
// boost (`unboostedOddsDecimal` null em tudo), freebet, bet builder (perna com 2+ seleções) e
// outra moeda que não USDT. Os enums novos estão travados abaixo por CLONE (subir "a conferir"),
// não por amostra real.
import { rodarInject, carregarContent, fixture, linha } from "../sandbox.mjs";

export const casa = "Shuffle";

const W = /^Ganhou → W \(retorno [\d.]+,\d{2,} USDT/;
const L = /^Perdeu → L$/;
const AB = /^em aberto \(aguardando resultado — NÃO liquidar; sem resultado\)$/;
const SIS = /^SISTEMA Duplas — 3 apostas de 2 seleção\(ões\), sobre 3 seleções/;

const id = (n) => "SHFfixture" + String(n).padStart(11, "0");

// n → o que a casa mostra. stake = "Sua aposta"; ret = "Você ganhou" (o do payload, exato).
const ESPERADO = {
  1:  { st: L,  odd: "4,9",      stake: "35,00", tipo: /^Simples$/, p: "card",
        col: "07/10/2026 21:13:38", ev: "08/10/2026 14:00:00" },
  2:  { st: W,  odd: "1,88",     stake: "40,00", ret: "75,20", tipo: /^Simples$/, p: "card",
        col: "07/10/2026 21:12:16", ev: "08/10/2026 06:10:00" },
  3:  { st: W,  odd: "1,85",     stake: "20,00", ret: "37,00", tipo: /^Simples$/, p: "card" },
  4:  { st: L,  odd: "5",        stake: "40,00", tipo: /^Simples$/, p: "card" },
  5:  { st: L,  odd: "6,356",    stake: "25,00", tipo: /^Múltipla \(2 seleções\)$/, p: "card (6,36)" },
  6:  { st: L,  odd: "9,075",    stake: "25,00", tipo: /^Múltipla \(2 seleções\)$/, p: "card (9,08)" },
  7:  { st: W,  odd: "8,82",     stake: "25,00", ret: "220,50", tipo: /^Múltipla \(2 seleções\)$/, p: "card",
        ev: "07/10/2026 23:00:00" },
  8:  { st: W,  odd: "6,44",     stake: "25,00", ret: "161,00", tipo: /^Múltipla \(2 seleções\)$/, p: "card" },
  9:  { st: L,  odd: "5,6298",   stake: "60,00", tipo: SIS, p: "card" },
  10: { st: L,  odd: "13,1271",  stake: "10,00", tipo: /^Múltipla \(3 seleções\)$/, p: "card (13,13)" },
  // O sistema "ganho" que perdeu dinheiro: 54,996 sobre 60.
  11: { st: W,  odd: "0,9166",   stake: "60,00", ret: "54,996", tipo: SIS, p: "card (55,00)",
        col: "07/10/2026 13:00:16", ev: "08/10/2026 01:20:00" },
  12: { st: L,  odd: "14,861",   stake: "10,00", tipo: /^Múltipla \(3 seleções\)$/, p: "card (14,86)" },
  13: { st: W,  odd: "3,2164",   stake: "60,00", ret: "192,984", tipo: SIS, p: "card (192,98)" },
  // A múltipla com perna PUSHED: card 11,52, pagou 51,19.
  14: { st: W,  odd: "5,1192",   stake: "10,00", ret: "51,192", tipo: /^Múltipla \(3 seleções\)$/, p: "card (11,52 / 51,19)",
        ev: "08/10/2026 14:00:00" },
  15: { st: W,  odd: "4,2224",   stake: "10,00", ret: "42,224", tipo: /^Múltipla \(3 seleções\)$/, p: "card (42,22)" },
  16: { st: W,  odd: "2,7774",   stake: "60,00", ret: "166,644", tipo: SIS, p: "card (166,64)" },
  17: { st: W,  odd: "4,84",     stake: "20,00", ret: "96,80", tipo: /^Múltipla \(2 seleções\)$/, p: "card" },
  18: { st: L,  odd: "14,93856", stake: "10,00", tipo: /^Múltipla \(3 seleções\)$/, p: "card (14,94)",
        col: "06/10/2026 22:23:20", ev: "07/10/2026 10:00:00" },
  19: { st: L,  odd: "6,0904",   stake: "60,00", tipo: SIS, p: "recon (média das duplas)" },
  20: { st: L,  odd: "7,3845",   stake: "60,00", tipo: SIS, p: "json" },
  21: { st: L,  odd: "19,925775", stake: "10,00", tipo: /^Múltipla \(3 seleções\)$/, p: "json" },
  22: { st: L,  odd: "26,796",   stake: "10,00", tipo: /^Múltipla \(3 seleções\)$/, p: "json" },
  23: { st: W,  odd: "3,08",     stake: "60,00", ret: "184,80", tipo: SIS, p: "json" },
  24: { st: AB, odd: "8,066",    stake: "25,00", tipo: /^Múltipla \(2 seleções\)$/, p: "card (8,07)",
        col: "08/10/2026 16:01:40", ev: "09/10/2026 00:00:00" },
  25: { st: AB, odd: "5,022",    stake: "25,00", tipo: /^Múltipla \(2 seleções\)$/, p: "card (5,02)" },
  28: { st: AB, odd: "7,2231",   stake: "60,00", tipo: SIS, p: "json" },
  29: { st: AB, odd: "19,207375", stake: "10,00", tipo: /^Múltipla \(3 seleções\)$/, p: "json" },
  30: { st: AB, odd: "2,25",     stake: "31,00", tipo: /^Simples$/, p: "json (F1, outright)",
        col: "07/10/2026 12:01:22", ev: "09/10/2026 05:30:00" },
};

const URL_LISTA = "https://shuffle.com/main-api/graphql/sports-main/graphql-sports-main";
const TOKEN = "Bearer harness.token.falso";
const PAG = 7;   // a casa aceita até 20; páginas menores provam o avanço pelo cursor

// Simula a casa: ordem por `createdAt` decrescente, `cursor` inclusivo, `nextCursor` = data do
// 1º bilhete da página seguinte, erro para `first > 20` e para chamada sem token.
function casaGraphQL(nodes, registro, teto = 20) {
  return (url, opts) => {
    if (!/\/main-api\/graphql\/sports-main\/graphql-sports-main/.test(String(url))) return null;
    let corpo = {};
    try { corpo = JSON.parse((opts && opts.body) || "{}"); } catch (e) {}
    const h = (opts && opts.headers) || {};
    const tk = h.authorization || h.Authorization;
    registro.push({ corpo, tk });
    if (corpo.operationName !== "GetSportsBets") return JSON.stringify({ data: { sportsBetsCount: 8 } });
    if (!tk) return JSON.stringify({ errors: [{ message: "UNAUTHENTICATED" }], data: null });
    const v = corpo.variables || {};
    if ((v.first || 0) > teto) return JSON.stringify({ errors: [{ message: "first must not be greater than " + teto }], data: null });
    let lista = nodes;
    if (Array.isArray(v.statuses)) lista = lista.filter((n) => v.statuses.includes(n.status));
    if (v.cursor) lista = lista.filter((n) => Date.parse(n.createdAt) <= Date.parse(v.cursor));
    const tam = Math.min(v.first || 9, PAG);
    const pag = lista.slice(0, tam);
    const prox = lista[tam];
    return JSON.stringify({ data: { sportsBets: { nodes: pag, nextCursor: prox ? prox.createdAt : null } } });
  };
}

export async function rodar() {
  const fx = JSON.parse(fixture("shuffle.sportsbets.json"));
  const nodes = fx.data.sportsBets.nodes;
  // Um bilhete de OUTRO usuário no meio da lista (o rodapé "Grandes apostadores" da casa).
  const alheio = Object.assign(JSON.parse(JSON.stringify(nodes[3])), {
    id: "OUTROusuarioXXXXXXXXX", user: { username: "outro" },
  });
  const comAlheio = nodes.slice(0, 4).concat([alheio], nodes.slice(4));

  const registro = [];
  // A requisição REAL da página: aba "Apostas pendentes", `first: 9`, com token.
  const corpoPagina = JSON.stringify({
    operationName: "GetSportsBets",
    query: "query GetSportsBets($language: Language, $currencyIn: [Currency!], $statuses: [SportsBetStatus!], $first: Int, $skip: Int, $after: DateTime, $cursor: DateTime) {\n  sportsBets: sportsBetsV3(\n    language: $language\n    currencyIn: $currencyIn\n    statuses: $statuses\n    first: $first\n    skip: $skip\n    after: $after\n    cursor: $cursor\n  )\n}",
    variables: { first: 9, language: "pt", skip: 0, statuses: ["PENDING"] },
  });
  const { ultima, mensagens } = await rodarInject({
    inject: "shf_inject.js",
    href: "https://shuffle.com/pt/sports?section=my-bets",
    urlInicial: URL_LISTA,
    optsInicial: { method: "POST", headers: { "content-type": "application/json", authorization: TOKEN, "x-correlation-id": "x" }, body: corpoPagina },
    pedido: "__sharpenupSHFReq",
    responder: casaGraphQL(comAlheio, registro),
    ms: 600,
  });

  const falhas = [];
  if (!ultima) return { falhas: ["o inject não emitiu nenhuma mensagem"], testes: 0 };
  if (!ultima.hook) falhas.push("o inject não emitiu `hook:true` (autodiagnóstico cego)");
  if (!(ultima.respostas >= 2)) falhas.push(`\`respostas\` baixo demais (veio ${ultima.respostas})`);
  if (!ultima.fim) falhas.push("o inject não sinalizou `fim` (o robô ficaria esperando o teto)");
  if (JSON.stringify(mensagens).includes("harness.token.falso")) falhas.push("o token do authorization vazou na mensagem para o content");

  const bilhetes = ultima.bilhetes || [];
  if (bilhetes.length !== nodes.length) falhas.push(`esperava ${nodes.length} bilhetes, vieram ${bilhetes.length}`);
  if (bilhetes.some((b) => b.id === alheio.id)) falhas.push("bilhete de OUTRO usuário (`user` preenchido) entrou no lote");

  const replay = registro.filter((r) => r.corpo.operationName === "GetSportsBets").slice(1);
  if (!replay.length) falhas.push("o replay não rodou");
  if (replay.some((r) => r.tk !== TOKEN)) falhas.push("o replay não levou o authorization aprendido");
  if (replay.some((r) => Array.isArray(r.corpo.variables && r.corpo.variables.statuses))) {
    falhas.push("o replay pediu com filtro de status — sem o filtro a casa devolve abertas e liquidadas juntas");
  }
  const paginasEsperadas = Math.ceil((nodes.length + 1) / PAG);
  if (replay.length < paginasEsperadas) falhas.push(`replay pediu ${replay.length} página(s); a lista tem ${paginasEsperadas} de ${PAG}`);
  if (replay.length > paginasEsperadas + 1) falhas.push(`replay pediu ${replay.length} páginas para ${paginasEsperadas} — não parou no nextCursor null`);

  const fmt = carregarContent().pegar("formatTicketSHF");
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

  for (const [n, e] of Object.entries(ESPERADO)) {
    const b = porId.get(id(n));
    if (!b) { falhas.push(`${id(n)} (${e.p}): não chegou ao lote`); continue; }
    const txt = fmt(b);
    testes++;
    const odd = linha(txt, "Odd:"), st = linha(txt, "Status:"), stake = linha(txt, "Stake:");
    if (!e.st.test(st)) falhas.push(`#${n} (${e.p}): status "${st}"`);
    if (odd.replace(/\s*\(.*$/, "") !== e.odd) falhas.push(`#${n} (${e.p}): odd esperada ${e.odd}, veio "${odd}"`);
    if (stake !== e.stake) falhas.push(`#${n} (${e.p}): stake esperada ${e.stake}, veio "${stake}"`);
    if (!e.tipo.test(linha(txt, "Tipo:"))) falhas.push(`#${n} (${e.p}): tipo "${linha(txt, "Tipo:")}"`);
    if (e.ret != null && !st.includes("retorno " + e.ret + " USDT")) falhas.push(`#${n} (${e.p}): retorno esperado ${e.ret} USDT no Status, veio "${st}"`);
    if (e.col && linha(txt, "Data (colocação):") !== e.col) falhas.push(`#${n}: colocação esperada ${e.col}, veio "${linha(txt, "Data (colocação):")}"`);
    if (e.ev && linha(txt, "Data (evento mais recente):") !== e.ev) falhas.push(`#${n}: evento esperado ${e.ev}, veio "${linha(txt, "Data (evento mais recente):")}" (startTime vem em UTC)`);
    if (AB.test(st) && /Retorno:/.test(txt)) falhas.push(`#${n}: aberta com linha "Retorno:" (potencial não é retorno)`);
    // A odd tem de explicar o dinheiro: em W, odd × stake = retorno, ao centavo.
    if (e.ret != null) {
      const o = Number(e.odd.replace(",", ".")), s = Number(e.stake.replace(",", ".")), r = Number(e.ret.replace(",", "."));
      if (Math.abs(o * s - r) > 0.005) falhas.push(`#${n}: odd ${e.odd} × ${e.stake} não explica o retorno ${e.ret}`);
    }
  }

  // Armadilha: a múltipla com perna PUSHED nunca pode sair com a odd da colocação.
  {
    const txt = fmt(porId.get(id(14)) || {});
    if (/^Odd: 11,5182/m.test(txt)) falhas.push("#14: odd 11,5182 é a da COLOCAÇÃO — a casa pagou 5,1192");
    if (!/push|anulada/i.test(txt)) falhas.push("#14: a perna PUSHED não está dita no bloco");
  }
  // Armadilha: a odd ATUAL do mercado (`marketSelection`) nunca entra no bloco. O #18 tem a
  // perna do Padres apostada a 2,28 e o mercado hoje a 1,40 (40/100 + 1).
  {
    const txt = fmt(porId.get(id(18)) || {});
    if (!/Odd da perna: 2,28/.test(txt)) falhas.push("#18: a odd APOSTADA da perna (2,28) não está no bloco");
    if (/1,4\b/.test(txt)) falhas.push("#18: a odd ATUAL do mercado (1,40) vazou para o bloco");
  }
  // Enum novo / caso sem amostra sobe cru, a conferir — nunca W/L por chute.
  {
    const base = porId.get(id(2));
    if (base) {
      const c = (o) => linha(fmt(Object.assign({}, base, o)), "Status:");
      const parcial = c({ status: "PARTIAL", pagou: 50 });
      if (!/a conferir — não liquidar automaticamente/.test(parcial)) falhas.push(`PARTIAL virou "${parcial}" (tinha de subir a conferir)`);
      const estranho = c({ status: "ALGO_NOVO", pagou: 0 });
      if (!/a conferir — não liquidar automaticamente/.test(estranho)) falhas.push(`status desconhecido virou "${estranho}"`);
      const lostComDinheiro = c({ status: "LOST", pagou: 20 });
      if (/Perdeu → L/.test(lostComDinheiro)) falhas.push(`LOST com retorno 20 virou "${lostComDinheiro}" (o dinheiro desmente o rótulo)`);
      const anulada = c({ status: "VOIDED", pagou: 40 });
      if (!/→ V$/.test(anulada)) falhas.push(`VOIDED com retorno = stake virou "${anulada}"`);
      const cashout = c({ status: "CASHED_OUT", pagou: 52.5 });
      if (!/^Cashout → W \(retorno 52,50 USDT/.test(cashout)) falhas.push(`CASHED_OUT com retorno 52,5 virou "${cashout}"`);
      const ganhoSemLucro = c({ status: "WON", pagou: 40 });
      if (!/→ V$/.test(ganhoSemLucro)) falhas.push(`WON com retorno = stake virou "${ganhoSemLucro}" (P/L zero é V)`);
      const semRetorno = c({ status: "WON", pagou: null });
      if (!/a conferir/.test(semRetorno)) falhas.push(`WON sem settlement virou "${semRetorno}"`);
    }
  }
  // Stake e retorno de moeda com mais casas (BTC) não podem ser arredondados a 2.
  {
    const base = porId.get(id(2));
    if (base) {
      const txt = fmt(Object.assign({}, base, { moeda: "BTC", stake: 0.00123, pagou: 0.0023124 }));
      if (linha(txt, "Stake:") !== "0,00123") falhas.push(`stake em BTC saiu "${linha(txt, "Stake:")}" (precisa das casas todas)`);
      if (!/retorno 0,0023124 BTC/.test(linha(txt, "Status:"))) falhas.push(`retorno em BTC saiu "${linha(txt, "Status:")}"`);
    }
  }

  testes += await partidaAFrio(nodes, falhas);
  testes += await tetoMenor(nodes, falhas);
  return { falhas, testes };
}

// A casa baixa o teto do `first` (hoje 20) e diz o novo no texto do erro. O inject tem de
// ler o número, recuar e varrer a lista inteira com ele, em vez de parar no 1º erro.
async function tetoMenor(nodes, falhas) {
  const registro = [];
  const PAG_BAIXO = 5;
  const { ultima } = await rodarInject({
    inject: "shf_inject.js",
    href: "https://shuffle.com/pt/sports",
    urlInicial: "https://shuffle.com/main-api/graphql/api/graphql",
    optsInicial: { method: "POST", headers: { "content-type": "application/json", authorization: TOKEN }, body: "{}" },
    pedido: "__sharpenupSHFReq",
    responder: (url, opts) => /\/api\/graphql$/.test(String(url)) ? "{}" : casaGraphQL(nodes, registro, PAG_BAIXO)(url, opts),
    ms: 600,
  });
  const bs = (ultima && ultima.bilhetes) || [];
  if (bs.length !== nodes.length) falhas.push(`teto ${PAG_BAIXO}: esperava ${nodes.length} bilhetes, vieram ${bs.length} (o inject não recuou o \`first\`)`);
  if (ultima && ultima.erro) falhas.push(`teto ${PAG_BAIXO}: o recuo deixou erro no autodiagnóstico: "${ultima.erro}"`);
  return bs.length === nodes.length ? 1 : 0;
}

// A página nunca pediu a lista (operador em outra tela de esportes): o token vem de outra
// chamada GraphQL autenticada, e o replay arranca com a query de reserva.
async function partidaAFrio(nodes, falhas) {
  const registro = [];
  const { ultima } = await rodarInject({
    inject: "shf_inject.js",
    href: "https://shuffle.com/pt/sports",
    urlInicial: "https://shuffle.com/main-api/graphql/api/graphql",
    optsInicial: { method: "POST", headers: { "content-type": "application/json", authorization: TOKEN },
                   body: JSON.stringify({ operationName: "ActiveTournaments", query: "query ActiveTournaments { x }", variables: {} }) },
    pedido: "__sharpenupSHFReq",
    responder: (url, opts) => {
      if (/\/api\/graphql$/.test(String(url))) return JSON.stringify({ data: { activeTournaments: [] } });
      return casaGraphQL(nodes, registro)(url, opts);
    },
    ms: 600,
  });
  const bs = (ultima && ultima.bilhetes) || [];
  if (bs.length !== nodes.length) falhas.push(`partida a frio: esperava ${nodes.length} bilhetes, vieram ${bs.length} (o token de outra chamada GraphQL não foi aprendido?)`);
  if (!ultima || !ultima.fim) falhas.push("partida a frio: sem `fim`");
  const q = registro.find((r) => r.corpo.operationName === "GetSportsBets");
  if (q && !/sportsBetsV3/.test(q.corpo.query || "")) falhas.push("partida a frio: a query de reserva não pede sportsBetsV3");
  return bs.length === nodes.length ? 1 : 0;
}
