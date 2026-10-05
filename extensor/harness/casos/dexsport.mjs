// Dex Sport (plataforma PRÓPRIA) — 1ª casa do motor (s391).
//
// SIGILO (decisão do Feca, 02/10/2026): casa normal no seletor, mas fora de aviso aos
// testers, changelog e home.
//
// O que o recon mediu (03/10/2026, conta do Feca, Chrome):
//   • O site tem DUAS listas de apostas. A do PERFIL (`POST dexsport.io/api/v3/txs_list`)
//     carrega, no meio do bilhete, um `token` de 57 caracteres, o `ip` e o `userId` — e lê o
//     retorno de `reserve`, que na PERDIDA guarda o potencial. A captura usa a OUTRA: a do SDK
//     de esportes, `GET prod.dexsport.work//api/sportsbook/history/tickets?status=…&page=N`,
//     com `payout` explícito, epoch nas datas e nomes em pt-BR. (A barra dupla no caminho é da
//     casa, medida.)
//   • O SDK roda em shadow DOM NA PRÓPRIA página e pede a lista por XHR, com `Accept` +
//     `Authorization`. 25 por página; o fim é `meta.totalPages`. `status` = `placed` (abertas)
//     ou `finished` (concluídas). A fixture é a conta inteira: 12 + 25 + 4 = 41.
//
// ⚠ PROCEDÊNCIA DOS VALORES ESPERADOS. Os marcados `card` foram lidos na tela da casa em
// 03/10/2026 (painel "Minhas apostas" do SDK e o histórico do perfil). Os marcados `json`
// vêm do corpo da resposta, que nos lidos bateu com o card. As datas são de São Paulo; o
// card mostra as mesmas horas sem os segundos ("1 de out. · 15:16").
//
// AS ARMADILHAS QUE ESTE CASO TRAVA
//
// 1. PERNA ANULADA (`b4836669`): duas pernas de "Empate anula aposta", uma devolvida (perna
//    `status: 6`, `payoutCoefficient: 1`). O bilhete traz `coefficient` 12,56 (a odd da
//    COLOCAÇÃO, produto das pernas) e `payoutCoefficient` 3,75 / `payout` 93,75. O card
//    estampa 3.75 e +93.75. Quem gravar o `coefficient` (ou o produto das pernas) inventa um
//    ganho de 314. A odd do W é `retorno ÷ stake`.
// 2. PERDIDA: `payout` 0 e `payoutCoefficient` 0; a odd do card está em `coefficient`
//    (4,25 no `2a544c06`). Ler o `payoutCoefficient` grava odd zero.
// 3. ABERTA também vem com `payout` 0 (não nulo). Retorno zero só é derrota com `result: 2`;
//    a aberta é `status: 2` / `result: 0` e o retorno dela é POTENCIAL (`possiblePayout`).
// 4. Perna `status: 0` (não decidida) dentro de bilhete JÁ PERDIDO (`603158df`): a casa
//    encerra a múltipla na 1ª perna perdida. Não é bilhete aberto.
// 5. `eventDate` em ISO **UTC** (`…T14:00:00.000Z`): a coluna Data vira o dia de São Paulo.
// 6. MOEDA: `currency: "usdt"` (minúsculo). O bloco leva `Moeda: usdt` e o dinheiro rotulado
//    nela, nunca "R$". Quem converte é o `/salvar`, pela moeda da CONTA.
// 7. O token nunca entra no bloco: a lista do SDK não o traz, e o inject não repassa header.
import { rodarInject, carregarContent, fixture, linha } from "../sandbox.mjs";

export const casa = "DEXSPORT";

const W = /^Ganhou → W \(retorno [\d.]+,\d{2} usdt\)$/;
const L = /^Perdeu → L$/;
const AB = /^em aberto \(aguardando resultado — NÃO liquidar; sem resultado\)$/;

// Os ids da Dex são UUIDs; o card estampa o UUID inteiro ("ID da aposta: 3345134c-ef5a-…").
// O caso localiza pelo PREFIXO de 8 (o que o recon anotou) e confere que é único.
const POR_PREFIXO = {
  // ganhas
  "3345134c": { odd: "5,03", status: W, stake: "25,00", ret: 125.75, data: "01/10/2026 15:16:01", evento: "02/10/2026 11:00:00", tipo: /^Múltipla \(2 seleções\)$/, p: "card" },
  "b4836669": { odd: "3,75", status: W, stake: "25,00", ret: 93.75,  data: "03/10/2026 01:02:18", evento: "03/10/2026 11:00:00", tipo: /^Múltipla \(2 seleções\)$/, p: "card (perfil)" },
  "c0140de0": { odd: "3,76", status: W, stake: "29,45", ret: 110.73, data: "02/10/2026 22:45:01", evento: "03/10/2026 02:05:00", tipo: /^Múltipla/, p: "json" },
  "b2e1c15c": { odd: "4,3",  status: W, stake: "25,00", ret: 107.5,  data: "02/10/2026 21:30:36", evento: "03/10/2026 08:30:00", tipo: /^Simples$/, p: "json" },
  // perdidas
  "6836ecd1": { odd: "3,77", status: L, stake: "24,50", data: "01/10/2026 15:19:50", evento: "02/10/2026 14:30:00", tipo: /^Múltipla/, p: "card" },
  "2cbcf976": { odd: "2,7",  status: L, stake: "25,00", data: "02/10/2026 01:13:15", evento: "02/10/2026 19:00:00", tipo: /^Múltipla/, p: "card" },
  "c43f1040": { odd: "5,06", status: L, stake: "25,00", data: "02/10/2026 13:01:54", evento: "03/10/2026 15:45:00", tipo: /^Múltipla \(3 seleções\)$/, p: "card" },
  "2a544c06": { odd: "4,25", status: L, stake: "25,00", data: "03/10/2026 01:18:09", evento: "03/10/2026 03:05:00", tipo: /^Múltipla/, p: "json (card do perfil: 4.25)" },
  "603158df": { odd: "4,94", status: L, stake: "25,00", data: "02/10/2026 17:19:01", evento: "03/10/2026 15:45:00", tipo: /^Múltipla/, p: "json" },
  // aberta
  "bf7feb3c": { odd: "6,86", status: AB, stake: "25,00", data: "03/10/2026 14:57:21", evento: "04/10/2026 11:30:00", potencial: "171,50 usdt", tipo: /^Múltipla/, p: "card (perfil)" },
};

const ANULADA = "b4836669";
const PERDIDA_COM_PERNA_ABERTA = "603158df";

export async function rodar() {
  const fx = JSON.parse(fixture("dexsport.tickets.json"));
  const paginas = { placed: fx.placed.map((p) => p.resposta), finished: fx.finished.map((p) => p.resposta) };
  const todos = [...paginas.placed, ...paginas.finished].flatMap((r) => r.data);
  let servidas = 0, negadas = 0;
  const pedidas = new Set();

  const responder = (url, opts) => {
    if (!/\/api\/sportsbook\/history\/tickets/.test(url)) return null;
    const h = (opts && opts.headers) || {};
    if (!(h.Authorization || h.authorization)) { negadas++; return JSON.stringify({ message: "Unauthorized", statusCode: 401 }); }
    servidas++;
    let st = "placed", pg = 1;
    try { const u = new URL(url); st = u.searchParams.get("status") || st; pg = Number(u.searchParams.get("page")) || 1; } catch (e) {}
    pedidas.add(st + ":" + pg);
    const lista = paginas[st] || [];
    const totalPages = lista.length;
    // Além do fim: a casa devolve página vazia com o mesmo `meta` (comportamento padrão do SDK).
    const r = lista[pg - 1] || { data: [], meta: { pageNumber: pg, pageSize: 25, totalPages, totalRows: 0 } };
    return JSON.stringify(r);
  };

  // A chamada REAL que o SDK dispara ao abrir "Minhas apostas" (aba Abertas), autenticada.
  const alvo = "https://prod.dexsport.work//api/sportsbook/history/tickets?status=placed&page=1&locale=pt";
  const { ultima, urls } = await rodarInject({
    inject: "dx_inject.js",
    href: "https://dexsport.io/pt/sports/",
    urlInicial: alvo,
    optsInicial: { method: "GET", headers: { Accept: "application/json", Authorization: "Bearer harness.token.falso" } },
    pedido: "__sharpenupDXReq",
    responder,
  });

  const falhas = [];
  if (!ultima) return { falhas: ["o inject não emitiu nenhuma mensagem"], testes: 0 };
  if (!ultima.hook) falhas.push("o inject não emitiu `hook:true` (autodiagnóstico cego)");
  if (!ultima.fim) falhas.push("o inject não sinalizou `fim` (o robô ficaria esperando o teto)");
  const bilhetes = ultima.bilhetes || [];
  if (bilhetes.length !== todos.length) falhas.push(`esperava ${todos.length} bilhetes normalizados, vieram ${bilhetes.length}`);
  for (const k of ["placed:1", "finished:1", "finished:2"]) {
    if (!pedidas.has(k)) falhas.push(`o replay não pediu ${k} — não varreu a lista até o totalPages`);
  }
  if (pedidas.has("finished:3")) falhas.push("o replay pediu finished:3 — passou do `meta.totalPages` (2)");
  if (negadas) falhas.push(`${negadas} requisição(ões) sem Authorization — o replay perdeu o header aprendido`);
  // O token nunca pode viajar para o content: o inject entrega o bilhete, não a requisição.
  if (JSON.stringify(ultima).includes("harness.token.falso")) falhas.push("o token do Authorization vazou na mensagem para o content");

  const fmt = carregarContent().pegar("formatTicketDX");
  let testes = 0;

  for (const b of bilhetes) {
    const txt = fmt(b);
    if (!txt.startsWith(`[Código: ${b.id}]`)) falhas.push(`${b.id}: marcador [Código:] ausente/errado`);
    if (linha(txt, "Moeda:") !== "usdt") falhas.push(`${b.id}: faltou a linha "Moeda: usdt"`);
    if (/R\$/.test(txt)) falhas.push(`${b.id}: o bloco diz "R$" numa conta em USDT`);
    if (!linha(txt, "Status (API):")) falhas.push(`${b.id}: falta o status cru da API`);
    if (/^0*(,0*)?$/.test(linha(txt, "Odd:"))) falhas.push(`${b.id}: odd zerada ou ausente`);
  }

  for (const [pre, e] of Object.entries(POR_PREFIXO)) {
    const achados = bilhetes.filter((b) => String(b.id).startsWith(pre));
    if (achados.length !== 1) { falhas.push(`${pre} (${e.p}): esperava 1 bilhete com esse prefixo, achei ${achados.length}`); continue; }
    const b = achados[0];
    const txt = fmt(b);
    testes++;
    const odd = linha(txt, "Odd:"), status = linha(txt, "Status:"), stake = linha(txt, "Stake:");
    const data = linha(txt, "Data (colocação):"), evento = linha(txt, "Data (evento mais recente):");
    if (odd !== e.odd) falhas.push(`${pre} (${e.p}): odd esperada ${e.odd}, veio "${odd}"`);
    if (!e.status.test(status)) falhas.push(`${pre} (${e.p}): status "${status}"`);
    if (stake !== e.stake) falhas.push(`${pre} (${e.p}): stake esperada ${e.stake}, veio "${stake}"`);
    if (data !== e.data) falhas.push(`${pre}: data de colocação esperada ${e.data}, veio "${data}"`);
    if (evento !== e.evento) falhas.push(`${pre}: data do EVENTO esperada ${e.evento}, veio "${evento}" (o eventDate vem em UTC)`);
    if (!e.tipo.test(linha(txt, "Tipo:"))) falhas.push(`${pre}: tipo "${linha(txt, "Tipo:")}"`);
    if (e.ret != null) {
      const n = Number(String(odd).replace(",", "."));
      const st = Number(e.stake.replace(".", "").replace(",", "."));
      if (!(Math.abs(n * st - e.ret) <= 0.01)) falhas.push(`${pre} (${e.p}): odd ${odd} × stake ${e.stake} não explica o retorno ${e.ret}`);
    }
    if (e.potencial != null && linha(txt, "Retorno potencial:") !== e.potencial) {
      falhas.push(`${pre}: retorno potencial esperado "${e.potencial}", veio "${linha(txt, "Retorno potencial:")}"`);
    }
    if (AB.test(status) && /Ganhou|Perdeu/.test(status)) falhas.push(`${pre}: aberta liquidada por dedução`);
  }

  // Armadilha 1: a perna anulada aparece como anulada, e nenhum número do bloco vira 12,56 de odd.
  {
    const b = bilhetes.find((x) => String(x.id).startsWith(ANULADA));
    const txt = b ? fmt(b) : "";
    if (b && linha(txt, "Odd:") === "12,56") falhas.push(`${ANULADA}: odd 12,56 é a da COLOCAÇÃO — a casa pagou 3,75`);
    if (b && !/anulada/i.test(txt)) falhas.push(`${ANULADA}: a perna anulada (status 6) não está dita no bloco`);
  }
  // Armadilha 4: perna não decidida num bilhete perdido não reabre o bilhete.
  {
    const b = bilhetes.find((x) => String(x.id).startsWith(PERDIDA_COM_PERNA_ABERTA));
    if (b && !L.test(linha(fmt(b), "Status:"))) falhas.push(`${PERDIDA_COM_PERNA_ABERTA}: a perna "status 0" reabriu um bilhete perdido`);
  }
  // Status desconhecido sobe cru, a conferir — nunca vira W/L.
  {
    const b0 = bilhetes.find((x) => String(x.id).startsWith("3345134c"));
    if (b0) {
      const estranho = { ...b0, resultado: 9, status: 9 };
      const st = linha(fmt(estranho), "Status:");
      if (!/a conferir — não liquidar automaticamente/.test(st)) falhas.push(`status desconhecido virou "${st}" (tinha de subir a conferir)`);
    }
    // Retorno ZERO numa concluída só é derrota quando o `result` concorda (2). Um `result`
    // que ninguém mapeou, com dinheiro zero, não pode virar L por dedução. A fixture não tem
    // esse caso (toda concluída com payout 0 tem result 2), por isso o clone.
    const p0 = bilhetes.find((x) => String(x.id).startsWith("2a544c06"));
    if (p0) {
      const st = linha(fmt({ ...p0, resultado: 0 }), "Status:");
      if (/Perdeu → L/.test(st)) falhas.push(`retorno zero com result 0 virou "${st}" (só result 2 é derrota)`);
    }
  }
  if (urls.length < 4) falhas.push(`replay não repaginou o bastante (só ${urls.length} requisição(ões))`);
  void servidas;

  testes += await segundaRodada(fx, falhas, fmt);
  return { falhas, testes };
}

// Armadilha 8 (s393): a SEGUNDA rodada do robô na mesma aba. O `fimReplay` do inject e o
// `dxFimReal` do content latchavam em `true` na 1ª rodada; a 2ª reenviava o acumulado velho
// sem perguntar nada à casa, e a aposta liquidada entre as duas subia como "em aberto"
// (`b779a93a`, conta do Feca, 04/10/2026). Aqui a casa LIQUIDA a aberta `bf7feb3c` entre as
// rodadas, e as duas metades precisam enxergar isso:
//   · inject: o pedido tardio (com o `fim` já dado) repagina, e a última mensagem traz W;
//   · content: com o mapa velho carregado e o `fim` velho ligado, o robô espera a casa e
//     formata a versão NOVA — sem o reset ele formata a aberta em 400 ms e encerra.
const ABERTA_QUE_LIQUIDA = "bf7feb3c";

async function segundaRodada(fx, falhas, fmt) {
  const clone = (x) => JSON.parse(JSON.stringify(x));
  const antes = { placed: fx.placed.map((p) => p.resposta), finished: fx.finished.map((p) => p.resposta) };
  // O estado da casa DEPOIS: a aberta saiu de `placed` e entrou em `finished`, ganha.
  const depois = { placed: clone(antes.placed), finished: clone(antes.finished) };
  let liquidada = null;
  for (const r of depois.placed) {
    const i = r.data.findIndex((t) => String(t.id).startsWith(ABERTA_QUE_LIQUIDA));
    if (i >= 0) { liquidada = r.data.splice(i, 1)[0]; r.meta.totalRows--; }
  }
  if (!liquidada) { falhas.push(`2ª rodada: ${ABERTA_QUE_LIQUIDA} não está em placed na fixture`); return 0; }
  Object.assign(liquidada, { status: 3, result: 1, settlementStatus: 1,
                             payout: 171.5, payoutCoefficient: liquidada.coefficient });
  depois.finished[0].data.unshift(liquidada);

  // A casa vira de estado no 1º pedido que chegar depois que a 1ª varredura terminou.
  let primeira = true, fimVisto = false;
  const responder = (url) => {
    if (!/\/api\/sportsbook\/history\/tickets/.test(url)) return null;
    let st = "placed", pg = 1;
    try { const u = new URL(url); st = u.searchParams.get("status") || st; pg = Number(u.searchParams.get("page")) || 1; } catch (e) {}
    if (fimVisto) primeira = false;
    const lista = (primeira ? antes : depois)[st] || [];
    if (st === "finished" && pg >= lista.length) fimVisto = true;
    return JSON.stringify(lista[pg - 1] || { data: [], meta: { pageNumber: pg, pageSize: 25, totalPages: lista.length, totalRows: 0 } });
  };
  const { ultima, mensagens } = await rodarInject({
    inject: "dx_inject.js",
    href: "https://dexsport.io/pt/sports/",
    urlInicial: "https://prod.dexsport.work//api/sportsbook/history/tickets?status=placed&page=1&locale=pt",
    optsInicial: { method: "GET", headers: { Authorization: "Bearer harness.token.falso" } },
    pedido: "__sharpenupDXReq",
    pedidoTardio: { __sharpenupDXReq: true },
    responder, ms: 600,
  });
  const bs = (ultima && ultima.bilhetes) || [];
  const b = bs.filter((x) => String(x.id).startsWith(ABERTA_QUE_LIQUIDA));
  if (primeira) falhas.push("2ª rodada (inject): o pedido tardio não tocou a rede — devolveu o acumulado velho");
  if (!ultima || !ultima.fim) falhas.push("2ª rodada (inject): a última mensagem não sinalizou `fim`");
  if (b.length !== 1) falhas.push(`2ª rodada (inject): esperava 1 ${ABERTA_QUE_LIQUIDA}, vieram ${b.length}`);
  else if (!W.test(linha(fmt(b[0]), "Status:"))) falhas.push(`2ª rodada (inject): ${ABERTA_QUE_LIQUIDA} liquidou na casa e subiu "${linha(fmt(b[0]), "Status:")}"`);
  // Depois do 1º `fim`, NENHUMA mensagem pode trazer a aberta velha: o content formata cada
  // bilhete na 1ª vez que o vê, então reenviar o acumulado antes de a casa responder é o
  // mesmo defeito por outro caminho (o `fim` destravado, mas o mapa velho na frente).
  const iFim = mensagens.findIndex((m) => m && m.fim);
  const velhaDepois = mensagens.slice(iFim + 1).some((m) => (m.bilhetes || [])
    .some((x) => String(x.id).startsWith(ABERTA_QUE_LIQUIDA) && x.status !== 3));
  if (iFim >= 0 && velhaDepois) falhas.push(`2ª rodada (inject): reenviou a ${ABERTA_QUE_LIQUIDA} ABERTA antes de a casa responder (acumulado velho não foi zerado)`);
  if (bs.length !== antes.placed.concat(antes.finished).flatMap((r) => r.data).length) {
    falhas.push(`2ª rodada (inject): ${bs.length} bilhetes no acumulado (bilhete perdido ou duplicado entre as rodadas)`);
  }

  // Metade do content: roda o `roboDXPassive` real com o estado que a 1ª rodada deixa na aba.
  const { pegar } = carregarContent();
  const parse = (raw) => ({ id: String(raw.id), resultado: raw.result, status: raw.status, liquidacao: raw.settlementStatus,
    tipo: raw.ticketType, moeda: String(raw.currency || ""), stake: raw.amount, odd: raw.coefficient,
    oddPaga: raw.payoutCoefficient, retorno: raw.payout, potencial: raw.possiblePayout, ts: raw.placedAt, fim: raw.finishedAt,
    sels: [] });
  const abertaRaw = antes.placed.flatMap((r) => r.data).find((t) => String(t.id).startsWith(ABERTA_QUE_LIQUIDA));
  const mapa = pegar("dxById");
  mapa.set(String(abertaRaw.id), parse(abertaRaw));     // o que a 1ª rodada deixou
  pegar("dxFimReal = true");
  // A "casa" responde 1,2 s depois do pedido: DEPOIS da 1ª leitura do robô (400 ms), onde o
  // mapa velho era formatado, e depois da saída rápida (~800 ms) de quem não destrava o `fim`.
  // Com 700 ms a mutação "não zera o dxFimReal" passava por sorte de relógio (medido, s393).
  setTimeout(() => { mapa.set(String(liquidada.id), parse(liquidada)); pegar("dxFimReal = true"); }, 1200);
  const blocos = await pegar("roboDXPassive")({
    parar: () => false, stopId: null, cutoff: 0, pisoSanidade: 0, painel: { contador: {} },
  });
  const meu = blocos.filter((t) => t.startsWith(`[Código: ${liquidada.id}]`));
  if (meu.length !== 1) falhas.push(`2ª rodada (content): esperava 1 bloco de ${ABERTA_QUE_LIQUIDA}, vieram ${meu.length}`);
  else if (!W.test(linha(meu[0], "Status:"))) falhas.push(`2ª rodada (content): formatou a versão VELHA — "${linha(meu[0], "Status:")}"`);
  return 2;
}
