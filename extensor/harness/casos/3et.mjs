// 3et (3et.com) — captura por API, só o SPORTSBOOK (a exchange fica para um 2º momento, Feca
// 08/11/2026). Recon 07-08/11/2026 (s441), conta do Feca em USD, pelo navegador dele.
//
// PLATAFORMA PRÓPRIA, sem casa irmã no sistema: front React (Vite), API no MESMO domínio
// (`/betting/v3/eurasian/...`, `/accounts/v3/...`). Nenhum inject existente fala `eurasian`.
// Inject e formatador próprios: `et_inject.js`, `formatTicketET`.
//
//   GET /betting/v3/eurasian/reports/bets/current/normal?filter=&page=N&size=200   (abertas)
//   GET /betting/v3/eurasian/statement/reports/betsByDate?page=N&size=200&after=0&before=<s>
//                                                                                (liquidadas)
//   → { content:[…], number, size, totalElements, totalPages, last, first, … }   (Spring Page)
//
// AS FIXTURES são a conta INTEIRA no dia do recon, sem campo de identidade (o bilhete não tem):
//   • `3et.settled.json` — 13 liquidadas (12 perdidas, 1 ganha), todas duplas ("Multiplier"
//     · "Double"), de 06 e 07/11/2026;
//   • `3et.open.json` — 4 abertas, duplas, no formato EMBRULHADO `{bet:{…}, betType, …}`.
//
// O que este caso trava, cada item cruzado com o card da casa (tela em USD):
//   • AUTENTICAÇÃO é só o COOKIE da sessão (medido: `fetch` com `credentials:"include"` e
//     nenhum header extra devolve 200). Não há token a aprender, e o replay arranca A FRIO,
//     sem a página ter pedido nada (a tela de extrato só pede um dia por clique).
//   • JANELA das liquidadas: a tela pede o mês; o replay pede `after=0` (medido: devolve as 13,
//     o mesmo que 3 e 10 anos). O filtro é pela COLOCAÇÃO (51831830, colocada 07/11 e liquidada
//     08/11, entra numa janela que termina em 08/11 00:00 UTC).
//   • PAGINAÇÃO por índice de página: `size` acima de 200 volta 200 (medido com 1000). O fim é
//     `last:true` (medido com size 5 e 2: páginas exatas, sem repetir bilhete).
//   • DINHEIRO em dólar, com 3 casas quando a conta pede (`profit` 127.908). ⚠ `payout` da
//     liquidada e "Est. Return" da tela são o LUCRO, não o retorno: 22 × 6,814 = 149,908 é o
//     retorno, e o card mostra 127,908. O retorno sai de `stake + profit`.
//   • MOEDA: o bilhete não diz; vem de `/accounts/v3/loggedIn` → `currencyCode` ("USD"). Essa
//     resposta tem nome, e-mail e endereço, e NADA dela pode sair do inject além da moeda.
//   • ODD do card é `odds` (9,175; 6,814). Na ganha ela fecha o retorno ao centavo; o produto
//     das pernas (6,815) NÃO fecha (a casa trunca a odd do conjunto).
//   • DATA: a API não publica início de evento, só `datePlaced` e `dateSettled` (ISO UTC). O
//     bloco leva a colocação em São Paulo (como a Novibet) — 00:06 UTC de 07/11 = 21:06 de 06/11.
//
// SIMPLES e PUSH (s443): a conta do Gabriel trouxe as primeiras, e o bloco ia com "Seleções:"
// vazio (a simples não tem `legs`). `3et.simples.settled.json` = 4 simples liquidadas (2 ganhas,
// 2 perdidas) + a dupla 52019175 com uma perna Push; `3et.simples.open.json` = 2 simples abertas
// (52028388 e o 51851882 ANTES de liquidar, o mesmo bilhete das duas listas). Crus da casa como
// chegaram ao `captura_crua`, sem o `moeda_conta` que o inject anexa. Travado em `simplesReais`.
//
// NÃO COBERTO por amostra real (a conta não tinha): simples anulada, meia vitória ou meia
// derrota (há mercados AH e HDP, então pode existir), cashout, freebet (`freeBetStake`), boost,
// `trueStake` ≠ `stake`, e qualquer `status.result` além de Win/Lose. Os casos de dinheiro estão
// travados por CLONE da perdida: só o número prova; o resto sobe "a conferir". O caminho XHR do
// inject não é exercitado (a página usa axios, que no navegador sai por XHR; o replay usa fetch).
import { rodarInject, carregarContent, fixture, linha, respostaHttp } from "../sandbox.mjs";

export const casa = "3et";

const L = /^Perdeu → L$/;
const W = (r) => new RegExp("^Ganhou → W \\(retorno " + r + " USD\\)$");
const D2 = /^Múltipla \(2 seleções\)$/;
const ABERTA = /^em aberto \(aguardando resultado — NÃO liquidar; sem resultado\)$/;
const CONFERIR = /a conferir — não liquidar automaticamente/;

// código → o que o card mostra (tela em USD). `col` = colocação em São Paulo.
const ESPERADO = {
  "51835571": { st: L,           odd: "9,175",  stake: "25,00", col: "07/11/2026 14:28:13" },
  "51776597": { st: W("149,908"), odd: "6,814", stake: "22,00", col: "07/11/2026 08:45:33" },
  "51831830": { st: L,           odd: "5,642",  stake: "30,00", col: "07/11/2026 14:07:01" },
  // Colocada 00:06 UTC de 07/11: em São Paulo é 06/11, e o dia é o de São Paulo.
  "51758258": { st: L,           odd: "11,062", stake: "20,00", col: "06/11/2026 21:06:16" },
};

const HOST = "https://www.3et.com";
const P_ABERTAS = "/betting/v3/eurasian/reports/bets/current/normal";
const P_LIQ = "/betting/v3/eurasian/statement/reports/betsByDate";
const P_CONTA = "/accounts/v3/loggedIn";
const PII = "fulano.harness@exemplo.com";

const LIQ = () => JSON.parse(fixture("3et.settled.json")).content;
const ABE = () => JSON.parse(fixture("3et.open.json")).content;
const ID = (x) => String((x && x.bet ? x.bet : x).betId);

// Página no formato Spring da casa. `tetoSize` é o teto do servidor (medido: 200).
function pagina(lista, q, tetoSize) {
  const size = Math.min(Number(q.size || 50), tetoSize);
  const n = Number(q.page || 0);
  const fatia = lista.slice(n * size, n * size + size);
  const total = lista.length, pags = Math.ceil(total / size);
  return JSON.stringify({ content: fatia, number: n, size, totalElements: total, totalPages: pags,
    numberOfElements: fatia.length, first: n === 0, last: n >= pags - 1, empty: !fatia.length });
}

// Simula a casa: cookie = sessão (`logado`); sem ela, 401 em tudo.
function casaET(liquidadas, abertas, registro, { tetoSize = 200, logado = true, moeda = "USD" } = {}) {
  return (url, opts) => {
    if (!String(url).startsWith(HOST + "/")) return null;
    const u = new URL(String(url));
    registro.push({ p: u.pathname, q: Object.fromEntries(u.searchParams), cred: opts && opts.credentials });
    if (!logado) return respostaHttp(401, JSON.stringify({ status: 401, message: "Unauthorized" }));
    if (u.pathname === P_CONTA) {
      return JSON.stringify({ userId: 1, username: "fulano", email: PII, firstName: "Fulano",
                              currencyId: 1, currencyCode: moeda, balance: 181.82 });
    }
    if (u.pathname === P_LIQ) return pagina(liquidadas, Object.fromEntries(u.searchParams), tetoSize);
    if (u.pathname === P_ABERTAS) return pagina(abertas, Object.fromEntries(u.searchParams), tetoSize);
    return JSON.stringify({});
  };
}

async function rodarPadrao(liquidadas, abertas, registro, extra = {}, opcCasa = {}) {
  return rodarInject(Object.assign({
    inject: "et_inject.js",
    href: HOST + "/reports/openbets/",
    urlInicial: HOST + P_ABERTAS + "?filter=&page=0&size=50",
    optsInicial: { method: "GET", credentials: "include" },
    pedido: "__sharpenupETReq",
    responder: casaET(liquidadas, abertas, registro, opcCasa),
    ms: 600,
  }, extra));
}

const _liq = (r) => r.filter((x) => x.p === P_LIQ);
const _abe = (r) => r.filter((x) => x.p === P_ABERTAS);

export async function rodar() {
  const liquidadas = LIQ(), abertas = ABE();
  const total = liquidadas.length + abertas.length;
  const registro = [];
  const { ultima, mensagens } = await rodarPadrao(liquidadas, abertas, registro);

  const falhas = [];
  if (!ultima) return { falhas: ["o inject não emitiu nenhuma mensagem"], testes: 0 };
  if (!ultima.hook) falhas.push("o inject não emitiu `hook:true` (autodiagnóstico cego)");
  if (!(ultima.respostas >= 3)) falhas.push(`\`respostas\` baixo demais (veio ${ultima.respostas}; a página + liquidadas + abertas)`);
  if (!ultima.fim) falhas.push("o inject não sinalizou `fim` (o robô ficaria esperando o teto)");
  if (ultima.erro) falhas.push(`erro com a sessão viva: "${ultima.erro}"`);
  const tudo = JSON.stringify(mensagens);
  if (tudo.includes(PII) || tudo.includes("Fulano")) falhas.push("dado pessoal de /accounts/v3/loggedIn vazou na mensagem para o content");

  const bilhetes = ultima.bilhetes || [];
  if (bilhetes.length !== total) falhas.push(`esperava ${total} bilhetes (13 liquidadas + 4 abertas), vieram ${bilhetes.length}`);

  // Replay: janela inteira, 200 por página, cookie da sessão, e uma página de cada lista.
  const liq = _liq(registro);
  if (liq.length !== 1) falhas.push(`replay pediu ${liq.length} página(s) de liquidadas para 13 bilhetes — esperava 1 (last:true)`);
  if (liq.some((r) => r.q.after !== "0")) falhas.push(`o replay não pediu a janela inteira (after=${liq.map((r) => r.q.after).join(",")}; esperava 0)`);
  if (liq.some((r) => !(Number(r.q.before) > Date.now() / 1000))) falhas.push("o replay pediu `before` no passado (as apostas de hoje ficariam de fora)");
  if (liq.concat(_abe(registro).slice(1)).some((r) => r.q.size !== "200")) falhas.push("o replay não pediu 200 por página");
  if (_abe(registro).length !== 2) falhas.push(`abertas pedidas ${_abe(registro).length} vez(es) — esperava 2 (a da página + 1 do replay)`);
  if (registro.some((r) => r.cred !== "include")) falhas.push("requisição sem `credentials:\"include\"` (a sessão é o cookie)");

  // O cru tem de ser o bilhete da casa, com o mesmo código do texto, e levar a moeda da conta.
  const cru = ultima.cru || [];
  if (cru.length !== total) falhas.push(`cru: esperava ${total} itens, vieram ${cru.length}`);
  for (const c of cru) {
    if (!c.cru || ID(c.cru) !== c.codigo) falhas.push(`cru ${c.codigo}: não é o bilhete da casa com o mesmo código`);
    else if (c.cru.moeda_conta !== "USD") falhas.push(`cru ${c.codigo}: sem \`moeda_conta\` USD (o bilhete não diz a moeda)`);
  }

  const fmt = carregarContent().pegar("formatTicketET");
  const porId = new Map(bilhetes.map((b) => [b.id, b]));
  let testes = 0;

  for (const x of liquidadas.concat(abertas)) if (!porId.has(ID(x))) falhas.push(`${ID(x)}: não chegou ao lote`);
  for (const b of bilhetes) {
    const txt = fmt(b);
    if (!txt.startsWith(`[Código: ${b.id}]`)) falhas.push(`${b.id}: marcador [Código:] ausente/errado`);
    if (!/^\d{8}$/.test(b.id)) falhas.push(`${b.id}: código fora do formato (betId do bilhete, 8 dígitos)`);
    if (linha(txt, "Moeda:") !== "USD") falhas.push(`${b.id}: faltou a linha "Moeda: USD"`);
    if (!/^\d{14}$/.test(linha(txt, "Carimbo de colocação:"))) falhas.push(`${b.id}: faltou o carimbo de colocação (dia da cotação)`);
    if (/R\$/.test(txt)) falhas.push(`${b.id}: o bloco diz "R$" numa conta em USD`);
    if (!linha(txt, "Status (API):")) falhas.push(`${b.id}: falta o status cru da API`);
    if (/^0*(,0*)?$/.test(linha(txt, "Odd:"))) falhas.push(`${b.id}: odd zerada ou ausente`);
    if (!/^Data \(colocação\): \d\d\/\d\d\/\d{4} \d\d:\d\d:\d\d$/m.test(txt)) falhas.push(`${b.id}: sem data de colocação`);
    if (/undefined|null|NaN/.test(txt)) falhas.push(`${b.id}: "undefined"/"null"/"NaN" no bloco`);
    if ((txt.match(/^- /gm) || []).length !== 2) falhas.push(`${b.id}: esperava 2 seleções (todas as da fixture são duplas)`);
    if (!/· Esporte: /.test(txt)) falhas.push(`${b.id}: sem esporte`);
    if (!D2.test(linha(txt, "Tipo:"))) falhas.push(`${b.id}: tipo "${linha(txt, "Tipo:")}"`);
  }

  for (const [idb, e] of Object.entries(ESPERADO)) {
    const b = porId.get(idb);
    if (!b) { falhas.push(`${idb}: não chegou ao lote`); continue; }
    const txt = fmt(b);
    testes++;
    const odd = linha(txt, "Odd:"), st = linha(txt, "Status:"), stake = linha(txt, "Stake:");
    if (!e.st.test(st)) falhas.push(`${idb}: status "${st}"`);
    if (odd !== e.odd) falhas.push(`${idb}: odd esperada ${e.odd}, veio "${odd}" (a do card)`);
    if (stake !== e.stake) falhas.push(`${idb}: stake esperada ${e.stake}, veio "${stake}"`);
    if (linha(txt, "Data (colocação):") !== e.col) falhas.push(`${idb}: colocação esperada ${e.col}, veio "${linha(txt, "Data (colocação):")}" (datePlaced UTC → São Paulo)`);
    if (/^Retorno potencial/m.test(txt)) falhas.push(`${idb}: liquidada com "Retorno potencial"`);
  }

  // O carimbo é a colocação em São Paulo, e cruza a meia-noite.
  {
    const c = linha(fmt(porId.get("51758258") || {}), "Carimbo de colocação:");
    if (c !== "20261106210616") falhas.push(`51758258: carimbo esperado 20261106210616, veio "${c}" (dia da cotação em São Paulo)`);
  }

  // A ganha: o `profit` é o lucro, e o retorno é stake + profit. O produto das pernas não fecha.
  {
    const txt = fmt(porId.get("51776597") || {});
    if (/127,908 USD\)$/m.test(linha(txt, "Status:"))) falhas.push("51776597: o lucro (`profit`/`payout`) virou retorno");
    if (!/^- AH: Tauras Erra Taurage -1\.5 \[perna ganha\]$/m.test(txt)) falhas.push("51776597: a perna de handicap não saiu como no card (mercado: seleção [perna ganha])");
    if (!/Jogo: FK Taurage Tauras vs Transinvest II · Liga: Lithuania 1 Lyga · Esporte: Soccer · Período: Full Time · Placar: FT: 3 - 1/.test(txt)) falhas.push("51776597: jogo/liga/esporte/período/placar da perna faltando");
    if (!/Odd da perna: 2,049/.test(txt) || !/Odd da perna: 3,326/.test(txt)) falhas.push("51776597: faltou a odd de cada perna");
  }
  // Perdida com uma perna ganha e a outra perdida: cada perna diz a sua.
  {
    const txt = fmt(porId.get("51831830") || {});
    if (!/^- Corner Total: UNDER 9\.5 \[perna ganha\]$/m.test(txt)) falhas.push("51831830: perna ganha não marcada");
    if (!/^- Team Points South Alabama Jaguars: UNDER 22\.5 \[perna perdida\]$/m.test(txt)) falhas.push("51831830: perna perdida não marcada");
    if (!/Jogo: South Alabama Jaguars at Louisiana-Lafayette · Liga: NCAA Division I FBS · Esporte: American Football/.test(txt)) falhas.push("51831830: o jogo 'X at Y' não saiu verbatim");
  }
  // Período que não é o jogo inteiro sobe junto da perna.
  {
    const txt = fmt(porId.get("51758408") || {});
    if (!/^- Moneyline First Half: TCU Horned Frogs \[perna ganha\]$/m.test(txt) || !/Período: First Half/.test(txt)) falhas.push("51758408: perna de 1º tempo sem o período");
  }

  // Abertas: retorno POTENCIAL (stake × odd), não o "Est. Return" da tela, que é o lucro.
  {
    const txt = fmt(porId.get("51867098") || {});
    testes++;
    if (!ABERTA.test(linha(txt, "Status:"))) falhas.push(`51867098: aberta virou "${linha(txt, "Status:")}"`);
    if (linha(txt, "Retorno potencial (se ganhar):") !== "195,30 USD") falhas.push(`51867098: retorno potencial esperado 195,30 USD (20 × 9,765), veio "${linha(txt, "Retorno potencial (se ganhar):")}"`);
    if (/^Retorno:/m.test(txt)) falhas.push("51867098: aberta com linha \"Retorno:\" (potencial não é retorno)");
    if (/\[perna /.test(txt)) falhas.push("51867098: perna de aberta marcada como decidida (`finished`/`graded` não dizem ganha ou perdida)");
    if (!/Estado da perna \(casa\): finished/.test(txt)) falhas.push("51867098: o estado cru da perna aberta não subiu");
    if (linha(txt, "Odd:") !== "9,765") falhas.push(`51867098: odd da aberta "${linha(txt, "Odd:")}"`);
    if (linha(txt, "Data (colocação):") !== "07/11/2026 18:35:40") falhas.push(`51867098: colocação "${linha(txt, "Data (colocação):")}"`);
  }

  // Dinheiro sem amostra real: clone da perdida, só o que o número prova vira resultado.
  {
    const base = porId.get("51835571");   // 25 USD @ 9,175, perdida
    if (!base) falhas.push("51835571: a perdida-base dos clones não chegou");
    else {
      const c = (o) => linha(fmt(Object.assign({}, base, o)), "Status:");
      const ganha = c({ estado: "Win", lucro: 204.375 });
      if (!W("229,375").test(ganha)) falhas.push(`Win que fecha (25 × 9,175 = 229,375) virou "${ganha}"`);
      const naoFecha = c({ estado: "Win", lucro: 150 });
      if (!CONFERIR.test(naoFecha)) falhas.push(`Win com dinheiro que não fecha com a odd virou "${naoFecha}"`);
      const anulada = c({ estado: "Push", lucro: 0 });
      if (!/→ V$/.test(anulada)) falhas.push(`lucro 0 (retorno = stake) virou "${anulada}"`);
      const meia = c({ estado: "Half Win", lucro: 102.19 });
      if (!CONFERIR.test(meia)) falhas.push(`estado desconhecido com dinheiro virou "${meia}"`);
      const desconhecidoComW = c({ estado: "Half Win", lucro: 204.375 });
      if (!CONFERIR.test(desconhecidoComW)) falhas.push(`estado desconhecido com o dinheiro de W virou "${desconhecidoComW}" (sem amostra, o rótulo manda parar)`);
      const perdidaComDinheiro = c({ estado: "Lose", lucro: -12.5 });
      if (L.test(perdidaComDinheiro)) falhas.push(`Lose com retorno 12,50 virou "${perdidaComDinheiro}" (o dinheiro desmente o rótulo)`);
      const semLucro = c({ estado: "Lose", lucro: null });
      if (!CONFERIR.test(semLucro)) falhas.push(`liquidada sem \`profit\` virou "${semLucro}"`);
      const fb = c({ freebet: 25 });
      if (!CONFERIR.test(fb)) falhas.push(`freebet sem amostra virou "${fb}"`);
      if (!/^Freebet \(cru da casa\): freeBetStake 25/m.test(fmt(Object.assign({}, base, { freebet: 25 })))) falhas.push("freebet: o valor cru não subiu");
      const trueSt = c({ stakeReal: 20 });
      if (!CONFERIR.test(trueSt)) falhas.push(`trueStake ≠ stake virou "${trueSt}"`);
      const semOdd = linha(fmt(Object.assign({}, base, { odd: 0 })), "Odd:");
      if (!/deixe a odd VAZIA/.test(semOdd)) falhas.push(`odd 0 virou "${semOdd}" (zero não é ausência)`);
      // Simples (sem amostra): tipo e a perna com o estado do bilhete.
      const simples = fmt(Object.assign({}, base, { pernas: [base.pernas[0]], odd: 2.98, lucro: -25 }));
      if (linha(simples, "Tipo:") !== "Simples") falhas.push(`simples virou tipo "${linha(simples, "Tipo:")}"`);
      if (/Odd da perna/.test(simples)) falhas.push("simples com linha de odd da perna (repete a do bilhete)");
      // Moeda ausente (a conta não respondeu): sem linha de moeda, nunca "USD" por chute.
      if (/^Moeda:/m.test(fmt(Object.assign({}, base, { moeda: "" })))) falhas.push("moeda ausente virou linha de moeda");
    }
  }

  testes += await liquidadaVenceAberta(falhas);
  testes += await paginacao(falhas, 450, 200, "0,1,2");
  testes += await paginacao(falhas, 400, 200, "0,1");
  // Teto do servidor menor que o pedido: a casa diz quantas páginas há, e o avanço é por elas.
  testes += await paginacao(falhas, 230, 50, "0,1,2,3,4");
  testes += await partidaAFrio(falhas);
  testes += await semSessao(falhas);
  testes += await semMoeda(falhas);
  testes += await simplesReais(falhas);
  return { falhas, testes };
}

// O mesmo bilhete nas duas listas (liquidou entre as duas chamadas): a liquidada vence, em
// qualquer ordem de chegada.
async function liquidadaVenceAberta(falhas) {
  const liquidadas = LIQ();
  const ganha = liquidadas.find((x) => x.betId === 51776597);
  const comoAberta = { bet: Object.assign({}, ganha, { status: "Open", legs: ganha.legs.map((l) => Object.assign({}, l, { status: "finished" })) }),
                       betType: "MULTIPLIER", translatedBetType: "Multiplier" };
  const { ultima } = await rodarPadrao(liquidadas, [comoAberta].concat(ABE()), []);
  const b = ((ultima && ultima.bilhetes) || []).filter((x) => x.id === "51776597");
  if (b.length !== 1) falhas.push(`liquidada × aberta: 51776597 veio ${b.length} vez(es)`);
  else if (!W("149,908").test(linha(carregarContent().pegar("formatTicketET")(b[0]), "Status:"))) falhas.push("liquidada × aberta: a versão aberta venceu a liquidada");
  return 1;
}

// N liquidadas: as páginas EXATAS até `last:true`, nenhuma a mais.
async function paginacao(falhas, n, tetoSize, esperado) {
  const modelo = LIQ();
  const liquidadas = [];
  for (let i = 0; i < n; i++) liquidadas.push(Object.assign({}, modelo[i % modelo.length], { betId: 90000000 + i }));
  const registro = [];
  const { ultima } = await rodarPadrao(liquidadas, ABE(), registro, {}, { tetoSize });
  const liq = ((ultima && ultima.bilhetes) || []).filter((b) => /^9\d{7}$/.test(b.id)).length;
  const rot = `${n} com teto ${tetoSize}`;
  if (liq !== n) falhas.push(`paginação ${rot}: esperava ${n} liquidadas, vieram ${liq}`);
  const pags = _liq(registro).map((r) => r.q.page);
  if (pags.join(",") !== esperado) falhas.push(`paginação ${rot}: páginas pedidas ${pags.join(",") || "(nenhuma)"}, esperava ${esperado} (fim = last:true)`);
  if (!(ultima && ultima.fim)) falhas.push(`paginação ${rot}: sem fim`);
  return 1;
}

// A frio: a página não fez requisição nenhuma (a tela de extrato só pede um dia por clique, e o
// inject pode chegar tarde). O cookie basta: o pedido do robô busca tudo sozinho.
async function partidaAFrio(falhas) {
  const registro = [];
  const { ultima } = await rodarPadrao(LIQ(), ABE(), registro, { href: HOST + "/", semRequisicaoInicial: true });
  const n = ((ultima && ultima.bilhetes) || []).length;
  if (n !== 17) falhas.push(`a frio: esperava 17 bilhetes só pelo cookie, vieram ${n}`);
  if (!(ultima && ultima.fim)) falhas.push("a frio: sem fim");
  return 1;
}

// Sem sessão: a casa responde 401. O inject diz o erro, sinaliza fim e não fica em laço.
async function semSessao(falhas) {
  const registro = [];
  const { ultima } = await rodarPadrao(LIQ(), ABE(), registro, { href: HOST + "/", semRequisicaoInicial: true, ms: 400 }, { logado: false });
  if (!ultima || !ultima.fim) falhas.push("sem sessão: o inject não sinalizou fim (o robô esperaria o teto)");
  if (!ultima || !/401/.test(String(ultima.erro || ""))) falhas.push(`sem sessão: erro não diz o HTTP 401 (veio "${ultima && ultima.erro}")`);
  if (registro.length > 4) falhas.push(`sem sessão: ${registro.length} requisições (laço?)`);
  return 1;
}

// A conta não disse a moeda (resposta sem `currencyCode`): os bilhetes vêm, sem moeda inventada.
async function semMoeda(falhas) {
  // `null`, nunca `undefined`: `undefined` cairia no padrão "USD" da desestruturação do `casaET`.
  const { ultima } = await rodarPadrao(LIQ(), ABE(), [], {}, { moeda: null });
  const b = ((ultima && ultima.bilhetes) || [])[0];
  if (!b) { falhas.push("sem moeda: nenhum bilhete"); return 1; }
  if (b.moeda) falhas.push(`sem moeda: o inject inventou "${b.moeda}"`);
  if (((ultima && ultima.cru) || []).some((c) => c.cru && c.cru.moeda_conta)) falhas.push("sem moeda: o cru levou moeda_conta inventada");
  return 1;
}

// SIMPLES reais (s443): sem `legs`, a seleção vem solta no bilhete, em formatos diferentes na
// liquidada e na aberta. O bloco tem de levar mercado, seleção, jogo, liga e esporte, senão a IA
// devolve "Mercado Especial - REVISAR" ou nada (o "Nenhuma linha válida" do Gabriel).
async function simplesReais(falhas) {
  const liq = JSON.parse(fixture("3et.simples.settled.json")).content;
  const abe = JSON.parse(fixture("3et.simples.open.json")).content;
  const { ultima } = await rodarPadrao(liq, abe, []);
  const fmt = carregarContent().pegar("formatTicketET");
  const porId = new Map(((ultima && ultima.bilhetes) || []).map((b) => [b.id, b]));
  const txt = (id) => (porId.has(id) ? fmt(porId.get(id)) : "");
  let n = 0;
  if (porId.size !== 6) falhas.push(`simples: esperava 6 bilhetes (51851882 nas duas listas conta 1), vieram ${porId.size}`);
  const SIMPLES = {
    "51663167": { st: W("81,25"), sel: "- Team Points Jacksonville Jaguars: OVER 29.5 [perna ganha]",
                  ctx: "Jogo: Jacksonville Jaguars at Baltimore Ravens · Liga: US NFL · Esporte: American Football · Período: Full Time · Placar: FT: 33 - 10" },
    "51666575": { st: L, sel: "- Kobi Simmons - Assists: Under (+2.5) [perna perdida]",
                  ctx: "Jogo: Fenerbahce vs Cazoo Baskonia Vitoria Gasteiz · Liga: Euroleague · Esporte: Basketball · Período: Full Time" },
    "51851882": { st: L, sel: "- Total Touchdowns: Over 5.5 [perna perdida]",
                  ctx: "Jogo: Tampa Bay Buccaneers at Chicago Bears · Liga: US NFL · Esporte: American Football" },
    "52022943": { st: W("140,40"), sel: "- Team Points Western Michigan Broncos: OVER 38.5 [perna ganha]",
                  ctx: "Liga: NCAA Division I FBS · Esporte: American Football" },
  };
  for (const [id, e] of Object.entries(SIMPLES)) {
    const t = txt(id); n++;
    if (!t) { falhas.push(`simples ${id}: não chegou ao lote`); continue; }
    if (linha(t, "Tipo:") !== "Simples") falhas.push(`simples ${id}: tipo "${linha(t, "Tipo:")}"`);
    if (!e.st.test(linha(t, "Status:"))) falhas.push(`simples ${id}: status "${linha(t, "Status:")}"`);
    if (!t.split(/\r?\n/).includes(e.sel)) falhas.push(`simples ${id}: seleção não saiu como "${e.sel}"`);
    if (!t.includes(e.ctx)) falhas.push(`simples ${id}: contexto da perna sem "${e.ctx}"`);
    if (/\(mercado sem nome\)|\(seleção sem nome\)|undefined|null|NaN/.test(t)) falhas.push(`simples ${id}: campo vazio ou "undefined" no bloco`);
  }
  // Aberta: plana no `bet`, liga no embrulho, sem resultado e sem estado de perna inventado.
  {
    const t = txt("52028388"); n++;
    if (!ABERTA.test(linha(t, "Status:"))) falhas.push(`simples aberta 52028388: status "${linha(t, "Status:")}"`);
    if (!t.split(/\r?\n/).includes("- HDP: HDP -7.5 (Boston Celtics)")) falhas.push("simples aberta 52028388: a seleção não subiu");
    if (!t.includes("Jogo: Boston Celtics at Toronto Raptors · Liga: US NBA · Esporte: Basketball")) falhas.push("simples aberta 52028388: jogo/liga (do embrulho)/esporte faltando");
    if (/\[perna |Estado da perna/.test(t)) falhas.push("simples aberta 52028388: perna de aberta com estado ou resultado");
    if (linha(t, "Retorno potencial (se ganhar):") !== "3,92 USD") falhas.push(`simples aberta 52028388: retorno potencial "${linha(t, "Retorno potencial (se ganhar):")}" (2 × 1,96)`);
  }
  // A liquidada vence a aberta do MESMO bilhete (51851882 veio nas duas listas).
  if (!L.test(linha(txt("51851882"), "Status:"))) falhas.push("simples 51851882: a versão aberta venceu a liquidada");
  // Push numa perna de múltipla: perna anulada, o bilhete pelo dinheiro (perdida).
  {
    const t = txt("52019175"); n++;
    if (!L.test(linha(t, "Status:"))) falhas.push(`push 52019175: status "${linha(t, "Status:")}"`);
    if (!t.split(/\r?\n/).includes("- Draw no bet: Bristol Rovers [perna anulada (push)]")) falhas.push("push 52019175: a perna Push não saiu como anulada");
    if (!t.split(/\r?\n/).includes("- Team Points Kent State Golden Flashes: UNDER 14.5 [perna perdida]")) falhas.push("push 52019175: a perna perdida não saiu");
  }
  return n;
}
