// Novibet (novibet.bet.br) — captura por API `POST /spt/api/historytickets/search` (recon s271).
//
// PLATAFORMA PRÓPRIA: gateway `BlueBrown.OnlineSportsbook.Gateway` (aparece no `$type` de todo
// objeto do payload), endpoints em `/spt/` e `/ngapi/` no MESMO host da casa. Não é Altenar,
// não é BetBy, não é Kambi, não é BetConstruct — inject e formatador próprios.
//
// REPLAY PURO: o passivo é impossível (medido ao vivo). A página é Angular e aborta o próprio
// request; o `clone().text()` da resposta rejeita com "The user aborted a request." — a mesma
// coisa que a Pitaco (s270) mostrou primeiro. Quem busca o dado é sempre o replay.
//
// Este caso trava as leituras que o recon custou, cada uma cruzada com o CARD renderizado
// (o `textContent` do painel "Apostas" foi salvo junto da fixture; stake, data e retorno dos
// 18 bilhetes que estavam na tela conferem com o payload, 0 divergências):
//
//   • A ODD DO SISTEMA NÃO É A DO CARD. Em `ticketType: "Fold2"`, `placedPrice` é a SOMA dos
//     produtos das C(n,2) linhas — medido em 19 de 19 bilhetes —, não a odd do bilhete. O card
//     estampa `@ 10.33` num bilhete cuja odd estrutural é 3,44446667 (a média das 3 duplas,
//     MASTER_RESULTADO §7.3) e cuja odd real, por ter ganhado, é 1,09706667 (retorno÷stake).
//     Copiar o número do card erraria por 9×. É a armadilha da bet365 (s265) noutra casa.
//
//   • `finalFinancials.payout` É SEMPRE POTENCIAL, inclusive em bilhete PERDIDO — o 474311813
//     perdeu e o campo segue dizendo 529,4268. O retorno real só existe em `settlement.payout`
//     (0 nesse bilhete). Quem ler o campo óbvio marca toda perdida como ganha; é a vitória
//     fantasma da VaideBet (s210) com outro nome de campo.
//
//   • `settlement` é **null** em toda aberta — separador limpo entre aberta e resolvida, sem
//     precisar interpretar enum.
//
//   • `placedPrice` tem `value` (exata) e `text` (a do card, truncada a 2 casas): 11.844 vs
//     "11.84". A `value` é a que vale — odd nunca truncada é regra primordial.
//
//   • STAKE DE SISTEMA: `cost` é o TOTAL (o que o card mostra em "Valor") e `amount` é o valor
//     POR LINHA. `cost / amount == multiplier` em 19 de 19. Emitir o `amount` como stake
//     dividiria por 3 o turnover de todo bilhete de sistema.
//
//   • DATA: não existe data de evento no payload (varredura de todo campo temporal encontrou
//     só `placedAt` e `settledAt`). A coluna Data é a colocação em America/Sao_Paulo,
//     conferida ao segundo: `2026-08-16T15:01:27Z` ⇄ o card diz `16/8/2026, 12:01:27`.
//
// PAGINAÇÃO: o `responder` abaixo fatia a fixture em páginas de 20 embora o inject peça 50 —
// é assim que se prova que o `skip` avança pelo que VOLTOU, não pelo que foi pedido, e que o
// fim vem de `statistics.count` (que é o total da janela e não muda com skip/take).
//
// NÃO COBERTO pela fixture (a conta tem 42 bilhetes em 12 meses): bilhete SIMPLES (nenhum — 3
// têm 2 seleções e 39 têm 3), cashout executado, imposto (`withholdingTax` 0 em 35 de 35),
// `costDiscount`, `overriddenResult`, `isBanker`, `settlementTag`, e qualquer `result` fora de
// {Won, Lost, Pending} — não há anulada/void nem meia-liquidação de BILHETE. No nível de PERNA
// há `HalfLostHalfVoid` (2 pernas), e ela está travada aqui pela odd riscada que produz.
import { rodarInject, carregarContent, fixture, linha } from "../sandbox.mjs";

export const casa = "Novibet";

// código (ticketId, o mesmo que o card estampa com `#`) → o que o CARD da Novibet mostra.
// stake = "Valor"/"Total" do card · data = rodapé do card · odd = ver acima (a do card é
// truncada, e em sistema nem é odd).
const ESPERADO = {
  "474419052": { stake: "24,69",  odd: "5,15375",    data: "16/08/2026 18:36:48", status: /^Em aberto/,  sistema: false },
  "474419051": { stake: "146,67", odd: "2,99416667", data: "16/08/2026 18:36:48", status: /^Em aberto/,  sistema: true  },
  "474418534": { stake: "39,70",  odd: "17,661",     data: "16/08/2026 18:34:24", status: /^Em aberto/,  sistema: false },
  "474418533": { stake: "235,89", odd: "6,86333333", data: "16/08/2026 18:34:24", status: /^Em aberto/,  sistema: true  },
  "474311813": { stake: "44,70",  odd: "11,844",     data: "16/08/2026 12:01:27", status: /^Perdeu → L$/, sistema: false },
  "474311812": { stake: "265,59", odd: "5,28333333", data: "16/08/2026 12:01:27", status: /^Em aberto/,  sistema: true  },
  "474311262": { stake: "34,81",  odd: "6,9",        data: "16/08/2026 11:57:03", status: /^Em aberto/,  sistema: false },
  "474311261": { stake: "206,85", odd: "3,68333333", data: "16/08/2026 11:57:03", status: /^Em aberto/,  sistema: true  },
  "474269611": { stake: "51,00",  odd: "6,384928",   data: "16/08/2026 08:56:19", status: /^Perdeu → L$/, sistema: false },
  // O bilhete-chave: sistema GANHO. O card diz `@ 10.33` e `Retornos R$332,41` sobre
  // `Valor R$303,00` → a odd é 332,4112 ÷ 303 = 1,09706667. Ganhou 2 das 3 duplas
  // (1,76 × 1,87 = 3,2912 × R$101,00 por linha = R$332,4112, ao centavo).
  "474269610": { stake: "303,00", odd: "1,09706667", data: "16/08/2026 08:56:19", status: /^Ganhou → W$/, sistema: true },
  "474265206": { stake: "36,21",  odd: "9,5445",     data: "16/08/2026 08:25:15", status: /^Perdeu → L$/, sistema: false },
  "474265205": { stake: "215,13", odd: "4,504",      data: "16/08/2026 08:25:15", status: /^Perdeu → L$/, sistema: true  },
  "474267325": { stake: "50,29",  odd: "7,128",      data: "16/08/2026 08:23:16", status: /^Perdeu → L$/, sistema: false },
  "474267324": { stake: "298,80", odd: "3,72",       data: "16/08/2026 08:23:16", status: /^Perdeu → L$/, sistema: true  },
  "474267283": { stake: "51,00",  odd: "6,443385",   data: "16/08/2026 08:21:14", status: /^Perdeu → L$/, sistema: false },
  "474267282": { stake: "303,00", odd: "3,46743333", data: "16/08/2026 08:21:14", status: /^Perdeu → L$/, sistema: true  },
  "474265556": { stake: "51,00",  odd: "7,278825",   data: "16/08/2026 08:19:19", status: /^Perdeu → L$/, sistema: false },
  "474265555": { stake: "303,00", odd: "3,76583333", data: "16/08/2026 08:19:19", status: /^Perdeu → L$/, sistema: true  },
};

const URL_LISTA = "https://www.novibet.bet.br/spt/api/historytickets/search";
// Os 11 headers de canal que a página envia. Sem eles a MESMA requisição responde 500
// (medido) — por isso o inject aprende de uma requisição real em vez de montar a sua.
const HEADERS = {
  "accept": "application/json, text/plain, */*",
  "content-type": "application/json",
  "x-gw-application-name": "NoviBR",
  "x-gw-channel": "WebPC",
  "x-gw-client-layout": "Desktop",
  "x-gw-client-timezone": "America/Sao_Paulo",
  "x-gw-cms-key": "_BR",
  "x-gw-country-sysname": "BR",
  "x-gw-currency-sysname": "BRL",
  "x-gw-domain-key": "_BR",
  "x-gw-language-sysname": "pt-BR",
  "x-gw-odds-representation": "Decimal",
  "x-gw-state-sysname": "",
};

export async function rodar() {
  const settled = JSON.parse(fixture("novibet.settled.json"));
  const todos = JSON.parse(fixture("novibet.todos.json"));

  // O corpo REAL da página: janela de ~24h e `result:2` (só fechadas). É a estreiteza dessa
  // requisição que obriga o replay a existir.
  const corpoInicial = JSON.stringify({
    dateFrom: "2026-08-16T02:36:26.900Z", dateTo: "2026-08-17T02:36:26.900Z",
    skip: 0, take: 20, result: 2, sortOrder: "Descending", sorting: 2, type: null,
  });

  // Páginas de 20 embora o inject peça 50: prova que o avanço usa o que VOLTOU.
  const PAG = 20;
  const pedidos = [];
  const responder = (url, opts) => {
    if (!String(url).includes("/spt/api/historytickets/search")) return null;
    let corpo = null;
    try { corpo = JSON.parse((opts && opts.body) || "{}"); } catch (e) { corpo = {}; }
    pedidos.push(corpo);
    // A requisição da própria página (result:2, janela de 1 dia) devolve a fixture das
    // fechadas, como no site.
    if (corpo.result === 2 && corpo.take === 20 && corpo.skip === 0) return fixture("novibet.settled.json");
    // O replay (`result: null`) recebe a lista inteira, fatiada.
    const lista = corpo.result == null ? todos.historyTickets : settled.historyTickets;
    const skip = corpo.skip || 0;
    return JSON.stringify({
      $type: todos.$type,
      historyTickets: lista.slice(skip, skip + PAG),
      statistics: Object.assign({}, todos.statistics, { count: lista.length }),
    });
  };

  const { ultima, urls } = await rodarInject({
    inject: "nv_inject.js",
    href: "https://www.novibet.bet.br/apostas-esportivas",
    urlInicial: URL_LISTA,
    optsInicial: { method: "POST", headers: HEADERS, body: corpoInicial },
    pedido: "__sharpenupNVReq",
    responder,
    ms: 900,
  });

  const falhas = [];
  if (!ultima) return { falhas: ["o inject não emitiu nenhuma mensagem"], testes: 0 };
  if (!ultima.hook) falhas.push("o inject não emitiu `hook:true` (autodiagnóstico cego)");
  if (typeof ultima.respostas !== "number" || ultima.respostas < 1) {
    falhas.push(`\`respostas\` ausente ou zerado (veio ${ultima.respostas})`);
  }
  if (!ultima.fim) falhas.push("o inject não sinalizou `fim` (o robô ficaria esperando o teto)");
  if (urls.length < 3) falhas.push(`replay não repaginou (só ${urls.length} requisição(ões))`);

  // ── o replay tem de ALARGAR a janela e pedir `result:null` ──
  // É a razão de este inject existir: a página pede 24h e só as fechadas.
  const doReplay = pedidos.filter((p) => p.result == null);
  if (!doReplay.length) {
    falhas.push("o replay nunca pediu `result:null` → as ABERTAS não seriam capturadas");
  } else {
    const p = doReplay[0];
    if (p.take !== 50) falhas.push(`replay pediu take=${p.take}; o teto medido da casa é 50`);
    const dias = (Date.parse(p.dateTo) - Date.parse(p.dateFrom)) / 86400000;
    if (!(dias > 300)) {
      falhas.push(`replay pediu janela de ${Math.round(dias)} dia(s) — a casa serve 12 meses ` +
                  "e a tela só pede 1 dia; sem alargar, a captura pega uma fatia mínima");
    }
    // Os campos que o replay NÃO controla têm de viajar intactos, senão a casa dá 400.
    if (p.sortOrder !== "Descending" || p.sorting !== 2) {
      falhas.push("o replay não preservou os campos do corpo original (sortOrder/sorting)");
    }
  }

  // ── paginação: sem perder nem duplicar ──
  const bilhetes = ultima.bilhetes || [];
  if (bilhetes.length !== 42) falhas.push(`esperava 42 bilhetes normalizados, vieram ${bilhetes.length}`);
  const refs = bilhetes.map((b) => b.ref);
  if (new Set(refs).size !== refs.length) falhas.push("o inject devolveu códigos repetidos");

  // ── os blocos que a IA vai ler ──
  const fmt = carregarContent().pegar("formatTicketNV");
  let testes = 0;
  const porRef = new Map();
  for (const b of bilhetes) {
    const txt = fmt(b);
    porRef.set(b.ref, txt);
    const e = ESPERADO[b.ref];
    if (!e) continue;                       // bilhete fora da tela no momento do recon
    testes++;
    if (!txt.startsWith(`[Código: ${b.ref}]`)) falhas.push(`${b.ref}: marcador [Código:] ausente/errado`);
    const stake = linha(txt, "Stake:");
    const odd = linha(txt, "Odd:");
    const status = linha(txt, "Status:");
    const data = linha(txt, "Data (colocação):");
    if (stake !== e.stake) falhas.push(`${b.ref}: stake esperado ${e.stake}, veio "${stake}"`);
    if (odd !== e.odd && odd !== `${e.odd} (= Retorno ÷ Stake)`) {
      falhas.push(`${b.ref}: odd esperada ${e.odd}, veio "${odd}"`);
    }
    if (!e.status.test(status)) falhas.push(`${b.ref}: status "${status}"`);
    if (data !== e.data) falhas.push(`${b.ref}: data esperada ${e.data}, veio "${data}"`);
    // O resultado CRU da API tem de subir junto: é ele que a CASA_NOVIBET.md traduz e é o
    // que permite reconhecer um valor novo (anulada, cashout) em vez de chutá-lo.
    if (!linha(txt, "Status (API):")) falhas.push(`${b.ref}: linha "Status (API):" ausente`);
    // Sistema: a linha que o backend lê para montar a 12ª coluna (`3x Duplas`).
    const tipo = linha(txt, "Tipo:");
    if (e.sistema) {
      if (!/^SISTEMA Duplas — 3 apostas de 2 seleção\(ões\)/.test(tipo)) {
        falhas.push(`${b.ref}: sistema não declarado no formato que o backend lê — "${tipo}"`);
      }
    } else if (!/^Múltipla \(\d seleções\)$/.test(tipo)) {
      falhas.push(`${b.ref}: tipo "${tipo}"`);
    }
  }

  // ── as armadilhas, uma a uma ──
  // (1) PERDIDA não pode mostrar o potencial como retorno.
  const perdida = porRef.get("474311813");
  if (perdida) {
    if (/529/.test(perdida.replace(/Retorno potencial.*/g, ""))) {
      falhas.push("474311813: o retorno POTENCIAL (529,4268) vazou para um bilhete perdido");
    }
    if (linha(perdida, "Retorno:") !== "R$ 0,00") {
      falhas.push(`474311813: retorno real deveria ser R$ 0,00, veio "${linha(perdida, "Retorno:")}"`);
    }
  }
  // (2) ABERTA nunca diz "Retorno:", só "Retorno potencial:".
  for (const ref of ["474419052", "474418534"]) {
    const txt = porRef.get(ref);
    if (!txt) continue;
    if (linha(txt, "Retorno:")) falhas.push(`${ref}: aberta emitiu "Retorno:" (a IA liquidaria a aposta)`);
    if (!/POTENCIAL/.test(linha(txt, "Retorno potencial:"))) {
      falhas.push(`${ref}: aberta sem o aviso de retorno POTENCIAL`);
    }
  }
  // (3) O sistema tem de avisar que o número do card não é a odd.
  const sisGanho = porRef.get("474269610");
  if (sisGanho) {
    if (!/SOMA dos multiplicadores/.test(sisGanho)) {
      falhas.push("474269610: falta o aviso de que o @ do card é a SOMA das linhas, não a odd");
    }
    // 10,3334 (a soma das 3 duplas) ÷ 3 = 3,44446667 — a média do §7.3, sem truncar.
    if (linha(sisGanho, "Odd (estrutural do sistema):").indexOf("3,44446667") !== 0) {
      falhas.push(`474269610: odd estrutural esperada 3,44446667, veio ` +
                  `"${linha(sisGanho, "Odd (estrutural do sistema):")}"`);
    }
  }
  // (4) Odd riscada por perna meio-anulada (`HalfLostHalfVoid`).
  const riscada = porRef.get("473922217");
  if (riscada) {
    const l = linha(riscada, "Odd revisada pela casa:");
    if (!/7,62734 → 2,107/.test(l)) falhas.push(`473922217: odd revisada não emitida ("${l}")`);
    if (!/HalfLostHalfVoid/.test(riscada)) falhas.push("473922217: o resultado cru da perna sumiu");
  }
  // (5) Esporte em pt-PT tem de vir com a dica canônica (`Ténis` → Tênis).
  const comTenis = [...porRef.values()].find((t) => /Esporte: Ténis/.test(t));
  if (!comTenis) falhas.push("nenhum bloco trouxe o esporte `Ténis` (pt-PT) da casa");
  else if (!/Esporte: Ténis \(Tênis\)/.test(comTenis)) {
    falhas.push("o esporte pt-PT `Ténis` não recebeu a dica canônica `(Tênis)`");
  }

  return { falhas, testes };
}
