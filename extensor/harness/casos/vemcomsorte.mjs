// Vem com Sorte (plataforma PRÓPRIA, `vemcomsorte.com`) — s467.
//
// O que o recon mediu (26/11/2026, Chrome do Feca, conta logada, painel "Minhas Apostas"):
//   • A lista sai de `POST /api/bettor/bet:history`, corpo
//     `{ascending, limit, filter:{dateRange:{from,to}, statuses:[]}, token?}`. A tela pede 90
//     dias, 20 por vez, e SÓ quando o painel abre.
//   • Auth: `Authorization: <localStorage.authToken>` (UUID cru, sem "Bearer"). Só ele basta;
//     sem ele, 401. Por isso o replay arranca A FRIO, sem depender da requisição da página.
//   • Paginação por `token` NO CORPO (o `nextToken` anterior); `nextToken` no corpo é ignorado.
//     Fim: `hasMore:false`. Lista vazia volta `data: null`.
//   • `from` além de ~123 dias → 400 PRECONDITION_FAILED dizendo o piso em epoch ms.
//   • A fixture é a resposta INTEIRA de 120 dias (SHA-256 conferido com o da aba, 39.763 bytes):
//     7 múltiplas de 3 pernas em BRL, R$ 250 cada: 2 abertas (as duas com Combo Boost ativo),
//     1 ganha (com Combo Boost +3% sobre o lucro), 4 perdidas.
//
// PROCEDÊNCIA DOS VALORES ESPERADOS: o CARD do painel "Minhas Apostas", lido nos 7 bilhetes em
// 26/11/2026 — rótulo ("Múltipla: VENCEU/Perdeu/Não resolvida"), "Valor da aposta", "Saque",
// "Ganho possível", "Odds totais" e o resultado de cada perna. O card NÃO mostra data nem hora:
// colocação e início de evento vêm do JSON (`createTime`, `event.startTime`, epoch ms),
// convertidos para Brasília — marcados `json` abaixo.
//
// AS ARMADILHAS QUE ESTE CASO TRAVA
//
// 1. DINHEIRO EM CENTAVOS: `amount` 25000 com `multiplier` 100 = R$ 250,00.
// 2. O CARD TRUNCA A ODD: "Odds totais 6.59" é `odds`; a completa é `initialOdds` (6,595784).
//    O Combo Boost está DENTRO do retorno (`bonus` 4075 = 3% do lucro) e já dentro da
//    `initialOdds`: na GANHA ela fecha o retorno no meio centavo (250 × 6,595784 = 1648,946 →
//    1648,95) e é ela a odd, pela mesma régua da Ficha (`ficha._odd`). Se não fechasse, retorno
//    ÷ stake. Na perdida e na aberta, a `initialOdds` (a do card).
// 3. NA PERDIDA O BOOST SOME do `possiblePayout` (160025 = 250 × 6,401, o produto puro), mas o
//    card segue mostrando a odd com o boost (6.56). A odd do bloco é a do card, nunca o produto.
// 4. RETORNO DA ABERTA É POTENCIAL ("Ganho possível" = `possiblePayout`, já com o boost).
// 5. A FRIO + paginação por `token` + recuo pelo piso do 400 + `data: null`.
//
// MUTAÇÕES (26/11/2026): 17 aplicadas, 15 detectadas, 2 inócuas — (a) parar só pela ausência
// de `nextToken`, sem olhar `hasMore`: a casa só manda o token quando `hasMore:true` (medido) e
// o freio de "página sem bilhete novo" segura o resto; (b) `filter(Boolean)` no parâmetro da
// seleção: a string "0" é verdadeira, então o handicap 0 não some.
//
// O QUE NÃO COBRE (sem amostra; sobe a conferir, provado por clone sintético): simples REAL,
// VOID, CASHOUT, HALF_WIN, HALF_LOSE, SYSTEM/FLEXIBLE/ONE_CUT, ao vivo, freebet.
import { rodarInject, carregarContent, fixture, linha, respostaHttp } from "../sandbox.mjs";

export const casa = "VEMCOMSORTE";

const HOST = "https://vemcomsorte.com";
const TOKEN = "11111111-2222-4333-8444-555555555555";
const LS = (tok) => ({ localStorage: { getItem: (k) => (k === "authToken" && tok ? tok : null) } });

const W = (r) => new RegExp(`^Ganhou → W \\(retorno R\\$ ${r.replace(",", "\\,")}\\)$`);
const L = /^Perdeu → L$/;
const AB = /^em aberto \(aguardando resultado — NÃO liquidar; sem resultado\)$/;
const CONF = /a conferir — não liquidar automaticamente/;

// card: rótulo, "Valor da aposta", "Odds totais" (truncada → a completa da API), "Saque" /
// "Ganho possível". json: colocação e o evento mais recente, em Brasília.
const ESPERADO = {
  "5898642": { st: AB, odd: "32,55405", tela: "32.55", pot: "R$ 8138,51", col: "26/11/2026 10:30:21", evento: "26/11/2026 15:00:00",
               pernas: ["em aberto", "em aberto", "em aberto"] },
  "3420609": { st: L, odd: "6,56303", tela: "6.56", col: "25/11/2026 20:33:54", evento: "26/11/2026 17:00:00",
               pernas: ["perdida", "em aberto", "perdida"] },
  "1324669": { st: AB, odd: "10,48169075", tela: "10.48", pot: "R$ 2620,42", col: "25/11/2026 20:32:48", evento: "26/11/2026 15:00:00",
               pernas: ["ganha", "em aberto", "em aberto"] },
  "8282618": { st: L, odd: "72,69006", tela: "72.69", col: "25/11/2026 20:30:26", evento: "26/11/2026 11:00:00",
               pernas: ["perdida", "em aberto", "em aberto"] },
  "3602620": { st: W("1648,95"), odd: "6,595784", tela: "6.59", col: "25/11/2026 20:28:53", evento: "26/11/2026 07:00:00",
               pernas: ["ganha", "ganha", "ganha"] },
  "4826593": { st: L, odd: "7,2109", tela: "7.21", col: "25/11/2026 20:27:30", evento: "26/11/2026 04:30:00",
               pernas: ["ganha", "perdida", "perdida"] },
  "5258640": { st: L, odd: "10,621745", tela: "10.62", col: "25/11/2026 20:26:31", evento: "25/11/2026 21:30:00",
               pernas: ["ganha", "perdida", "perdida"] },
};

const RX_LISTA = /\/api\/bettor\/bet:history/;
const ERRO = (det) => JSON.stringify({ code: "PRECONDITION_FAILED", details: [det], message: "Request violation found" });

// A casa dublada com as REGRAS medidas. `todos` em ordem decrescente de colocação.
function casaDublada(todos, pedidos, opts = {}) {
  const pisoDias = opts.pisoDias || 123;
  return (url, o) => {
    if (!RX_LISTA.test(url)) return null;
    let corpo = null;
    try { corpo = JSON.parse((o && o.body) || "null"); } catch (e) {}
    const h = (o && o.headers) || {};
    const auth = Object.keys(h).find((k) => k.toLowerCase() === "authorization");
    if (pedidos) pedidos.push({ corpo, auth: auth ? h[auth] : null, metodo: o && o.method });
    if (!auth || !h[auth]) return respostaHttp(401, JSON.stringify({ code: "UNAUTHENTICATED" }));
    const dr = corpo && corpo.filter && corpo.filter.dateRange;
    if (!dr) return respostaHttp(400, ERRO("Invalid request field 'filter.dateRange'"));
    const piso = Date.now() - pisoDias * 864e5;
    if (dr.from < piso) return respostaHttp(400, ERRO(`Field 'from'=${dr.from} must be greater or equal to ${Math.floor(piso)}.`));
    // Não recorta por data: a fixture é de 26/11/2026 e o `from` do inject é relativo a AGORA.
    // A janela é provada pelo piso (acima) e pelo caso `piso`.
    const dentro = todos;
    const ini = corpo.token ? Number(String(corpo.token).replace("pag-", "")) : 0;
    const lim = corpo.limit || 20;
    const fatia = dentro.slice(ini, ini + lim);
    const mais = ini + lim < dentro.length;
    const r = { data: fatia.length ? fatia : null, hasMore: mais, metadata: { eventsData: {}, eventsStatuses: {} } };
    if (mais) r.nextToken = "pag-" + (ini + lim);
    return JSON.stringify(r);
  };
}

export async function rodar() {
  const fx = JSON.parse(fixture("vemcomsorte.bet_history.json"));
  const todos = fx.data;
  const pedidos = [];

  // Carga REAL da tela: o painel pede 90 dias, 20 por vez, por XHR com os headers da página.
  const corpoTela = JSON.stringify({ ascending: false, limit: 20, filter: { dateRange: { from: Date.now() - 90 * 864e5, to: Date.now() }, statuses: [] } });
  const { ultima } = await rodarInject({
    inject: "vcs_inject.js",
    href: HOST + "/sport",
    urlInicial: HOST + "/api/bettor/bet:history",
    optsInicial: { method: "POST", body: corpoTela, headers: { Authorization: TOKEN, "x-session-token": TOKEN, "x-project-id": "331", "Content-Type": "application/json" } },
    pedido: "__sharpenupVCSReq",
    janelaExtra: LS(TOKEN),
    responder: casaDublada(todos, pedidos),
  });

  const falhas = [];
  if (!ultima) return { falhas: ["o inject não emitiu nenhuma mensagem"], testes: 0 };
  if (!ultima.hook) falhas.push("o inject não emitiu `hook:true` (autodiagnóstico cego)");
  if (!ultima.fim) falhas.push("o inject não sinalizou `fim` (o robô ficaria esperando o teto)");
  const bilhetes = ultima.bilhetes || [];
  if (bilhetes.length !== 7) falhas.push(`esperava 7 bilhetes normalizados, vieram ${bilhetes.length}`);
  const replays = pedidos.filter((p) => p.corpo && p.corpo.limit === 100);
  if (!replays.length) falhas.push("o replay não pediu a lista larga (limit 100)");
  if (replays.some((p) => !p.corpo.filter || !Array.isArray(p.corpo.filter.statuses) || p.corpo.filter.statuses.length)) {
    falhas.push("o replay filtrou status (tem de pedir `statuses: []`, abertas e liquidadas juntas)");
  }
  if (replays.some((p) => p.metodo !== "POST")) falhas.push("o replay não foi POST");
  if (!Array.isArray(ultima.cru) || ultima.cru.length !== 7) falhas.push("o inject não mandou o cru de cada bilhete");
  else {
    const c = ultima.cru.find((x) => x.codigo === "3602620");
    if (!c || !c.cru || !c.cru.money || c.cru.money.payout !== 164895 || c.cru.money.multiplier !== 100 ||
        !Array.isArray(c.cru.outcomes) || c.cru.outcomes.length !== 3 || !c.cru.outcomes[0].market ||
        c.cru.outcomes[0].market.name !== "Asian Handicap Games" || c.cru.outcomes[0].sport.name !== "Tennis") {
      falhas.push("o cru do 3602620 não é o bilhete da casa verbatim (money em centavos, outcomes com market/sport)");
    }
  }

  const fmt = carregarContent().pegar("formatTicketVCS");
  let testes = 0;
  for (const b of bilhetes) {
    const txt = fmt(b);
    if (!txt.startsWith(`[Código: ${b.id}]`)) falhas.push(`${b.id}: marcador [Código:] ausente/errado`);
    if (!linha(txt, "Status (API):")) falhas.push(`${b.id}: falta o status cru da API`);
    if (linha(txt, "Moeda:")) falhas.push(`${b.id}: linha "Moeda:" numa conta em real (muda o hash do bloco_visto)`);
    if (linha(txt, "Stake:") !== "250,00") falhas.push(`${b.id} (card): stake "${linha(txt, "Stake:")}", o card diz R$ 250,00 (armadilha 1: centavos)`);
  }

  for (const [cod, e] of Object.entries(ESPERADO)) {
    const b = bilhetes.find((x) => x.id === cod);
    if (!b) { falhas.push(`${cod}: bilhete ausente`); continue; }
    const txt = fmt(b);
    testes++;
    const odd = linha(txt, "Odd:"), st = linha(txt, "Status:");
    if (odd !== e.odd) falhas.push(`${cod} (card): odd esperada ${e.odd}, veio "${odd}"`);
    if (!String(e.odd).replace(",", ".").startsWith(e.tela)) falhas.push(`${cod}: o esperado ${e.odd} não começa pela odd do card ${e.tela} (gabarito errado)`);
    if (!e.st.test(st)) falhas.push(`${cod} (card): status "${st}"`);
    if (linha(txt, "Data (colocação):") !== e.col) falhas.push(`${cod} (json): colocação esperada ${e.col}, veio "${linha(txt, "Data (colocação):")}"`);
    if (linha(txt, "Data (evento mais recente):") !== e.evento) falhas.push(`${cod} (json): evento esperado ${e.evento}, veio "${linha(txt, "Data (evento mais recente):")}"`);
    if (e.pot && linha(txt, "Retorno potencial:") !== e.pot) falhas.push(`${cod} (card): potencial esperado ${e.pot}, veio "${linha(txt, "Retorno potencial:")}"`);
    if (!e.pot && linha(txt, "Retorno potencial:")) falhas.push(`${cod}: "Retorno potencial" num bilhete liquidado`);
    if (linha(txt, "Tipo:") !== "Múltipla (3 seleções)") falhas.push(`${cod}: tipo "${linha(txt, "Tipo:")}"`);
    const pernas = (txt.match(/\[perna ([^\]]+)\]/g) || []).map((x) => x.slice(7, -1));
    if (JSON.stringify(pernas) !== JSON.stringify(e.pernas)) falhas.push(`${cod} (card): pernas ${JSON.stringify(pernas)}, o card diz ${JSON.stringify(e.pernas)}`);
  }

  // Seleções como a API escreve (inglês) + a linha, e o contexto da perna.
  {
    const t = fmt(bilhetes.find((x) => x.id === "3602620") || {});
    if (!t.includes("- Asian Handicap Games: Aryan Lakshmanan +6.5 [perna ganha]")) falhas.push(`3602620: perna de handicap mal escrita:\n${t}`);
    if (!/Jogo: Aryan Lakshmanan vs Dev Javia · Liga: ITF Bhopal \| Men \| Singles \(ITF Men\) · Esporte: Tennis · Início: 26\/11\/2026 02:30:00/.test(t)) falhas.push(`3602620: contexto da perna errado:\n${t}`);
    if (!/Odd da seleção: 1,72/.test(t)) falhas.push("3602620: falta a odd da seleção");
    if (!/^Boost: Combo Boost .* \+3% · bônus no retorno R\$ 40,75$/m.test(t)) falhas.push(`3602620: o Combo Boost não aparece no bloco:\n${t}`);
    const t2 = fmt(bilhetes.find((x) => x.id === "3420609") || {});
    if (!t2.includes("- Under/Over Games: Over 21.5 [perna perdida]")) falhas.push(`3420609: perna de total mal escrita:\n${t2}`);
    // Armadilha 3: a perdida não ganha o produto das pernas (6,401) como odd.
    if (/6,401/.test(linha(t2, "Odd:"))) falhas.push("3420609: a odd virou o produto das pernas (6,401); o card diz 6.56");
    const t3 = fmt(bilhetes.find((x) => x.id === "5898642") || {});
    if (!t3.includes("- Double Chance: X2 [perna em aberto]")) falhas.push(`5898642: perna sem parâmetro mal escrita:\n${t3}`);
    if (!t3.includes("- Asian Handicap: Al Baq'a SC 0 [perna em aberto]")) falhas.push(`5898642: handicap 0 sumiu (parâmetro "0" não é vazio):\n${t3}`);
  }

  testes += sinteticos(falhas, fmt, bilhetes);
  testes += await paginacao(falhas, todos);
  testes += await aFrio(falhas, todos);
  testes += await semSessao(falhas);
  testes += await piso(falhas, todos);
  testes += await vazio(falhas);
  testes += await novaRodada(falhas, todos);
  return { falhas, testes };
}

// Clones dos bilhetes reais com um campo trocado: o que a amostra não tem sobe a conferir,
// nunca liquidado por chute.
function sinteticos(falhas, fmt, bilhetes) {
  const ganha = bilhetes.find((x) => x.id === "3602620");
  const perdida = bilhetes.find((x) => x.id === "4826593");
  const aberta = bilhetes.find((x) => x.id === "1324669");
  if (!ganha || !perdida || !aberta) { falhas.push("sintéticos: bilhete-base ausente"); return 0; }
  let n = 0;
  const st = (b) => linha(fmt(b), "Status:");
  const ok = (cond, msg) => { n++; if (!cond) falhas.push(msg); };
  const perna = (b, i, s) => ({ ...b, sels: b.sels.map((x, j) => (j === i ? { ...x, status: s } : x)) });

  for (const s of ["VOID", "CASHOUT", "HALF_WIN", "HALF_LOSE", "SUSPENSA"]) {
    ok(CONF.test(st({ ...ganha, status: s })), `status "${s}" virou "${st({ ...ganha, status: s })}"`);
  }
  // Rede do dinheiro: liquidada com retorno = stake é V, qualquer que seja o rótulo.
  ok(/→ V$/.test(st({ ...perdida, status: "VOID", retorno: 250 })), `VOID com retorno = stake virou "${st({ ...perdida, status: "VOID", retorno: 250 })}"`);
  ok(CONF.test(st(perna(ganha, 0, "VOID"))), "WIN com perna VOID virou W (sem amostra)");
  ok(CONF.test(st(perna(ganha, 1, "LOSE"))), "WIN com perna LOSE virou W");
  ok(CONF.test(st({ ...ganha, retorno: 1500 })), "WIN com retorno que não fecha stake × odd virou W");
  // Fecha no centavo mas não no meio centavo: W, com a odd do dinheiro (régua da Ficha).
  ok(linha(fmt({ ...ganha, retorno: 1648.954 }), "Odd:") === "6,595816", `W fora do meio centavo com odd "${linha(fmt({ ...ganha, retorno: 1648.954 }), "Odd:")}" (esperava retorno ÷ stake)`);
  ok(CONF.test(st({ ...perdida, sels: perdida.sels.map((x) => ({ ...x, status: "WIN" })) })), "LOSE sem perna perdida virou L");
  ok(CONF.test(st({ ...perdida, retorno: 100 })), "LOSE com retorno virou L");
  ok(CONF.test(st({ ...ganha, odd: null })), "WIN sem odd virou liquidado");
  ok(CONF.test(st({ ...ganha, stake: null })), "WIN sem stake (sem multiplier) virou liquidado");
  ok(linha(fmt({ ...perdida, odd: null }), "Odd:") === "", "odd ausente virou número (zero não é ausência)");
  ok(AB.test(st(aberta)) && !/W/.test(st(aberta)), "aberta liquidou");
  // O potencial é o `possiblePayout` da CASA, nunca stake × odd (na amostra os dois coincidem
  // ao centavo; aqui não, e só o número da casa pode aparecer).
  ok(linha(fmt({ ...aberta, potencial: 999 }), "Retorno potencial:") === "R$ 999,00", "o potencial da aberta não é o `possiblePayout` da casa");
  ok(CONF.test(st({ ...ganha, tipo: "SYSTEM" })), "SYSTEM ganha virou W (a odd é outra regra)");
  ok(/^tipo SYSTEM/.test(linha(fmt({ ...ganha, tipo: "SYSTEM" }), "Tipo:")), "SYSTEM sem o tipo cru");
  const simples = { ...ganha, tipo: "SINGLE", sels: [ganha.sels[0]], odd: 1.72, retorno: 430 };
  ok(linha(fmt(simples), "Tipo:") === "Simples", `simples com tipo "${linha(fmt(simples), "Tipo:")}"`);
  ok(W("430,00").test(st(simples)), `simples ganha virou "${st(simples)}"`);
  ok(!/Odd da seleção/.test(fmt(simples)), "simples repetindo a odd da seleção");
  ok(/ao vivo/.test(fmt(perna({ ...ganha, sels: ganha.sels.map((x) => ({ ...x, aoVivo: true })) }, 0, "WIN"))), "perna ao vivo sem a marca");
  return n;
}

// 230 bilhetes: o inject anda pelo `token` até `hasMore:false`, 100 por página.
async function paginacao(falhas, todos) {
  const muitos = [];
  for (let i = 0; i < 230; i++) {
    const t = JSON.parse(JSON.stringify(todos[i % todos.length]));
    t.id = String(9000000 + i);
    muitos.push(t);
  }
  const pedidos = [];
  const { ultima } = await rodarInject({
    inject: "vcs_inject.js", href: HOST + "/sport",
    semRequisicaoInicial: true, pedido: "__sharpenupVCSReq", janelaExtra: LS(TOKEN),
    responder: casaDublada(muitos, pedidos), ms: 600,
  });
  const n = (ultima && ultima.bilhetes || []).length;
  if (n !== 230) falhas.push(`paginação: esperava 230 bilhetes, vieram ${n}`);
  const toks = pedidos.map((p) => (p.corpo && p.corpo.token) || "");
  if (JSON.stringify(toks) !== JSON.stringify(["", "pag-100", "pag-200"])) falhas.push(`paginação: tokens pedidos ${JSON.stringify(toks)}`);
  if (pedidos.some((p) => p.corpo && "nextToken" in p.corpo)) falhas.push("paginação: mandou `nextToken` no corpo (a casa ignora; é `token`)");
  if (!ultima || !ultima.fim) falhas.push("paginação: sem `fim`");
  return 1;
}

// A frio: a página não fez requisição nenhuma. O token sai do localStorage.
async function aFrio(falhas, todos) {
  const pedidos = [];
  const { ultima } = await rodarInject({
    inject: "vcs_inject.js", href: HOST + "/sport",
    semRequisicaoInicial: true, pedido: "__sharpenupVCSReq", janelaExtra: LS(TOKEN),
    responder: casaDublada(todos, pedidos),
  });
  const n = (ultima && ultima.bilhetes || []).length;
  if (n !== 7) falhas.push(`a frio: esperava 7 bilhetes pelo token do localStorage, vieram ${n}`);
  if (pedidos.some((p) => p.auth !== TOKEN)) falhas.push("a frio: requisição sem o Authorization do localStorage");
  if (ultima && ultima.semToken) falhas.push("a frio: `semToken` com o token no localStorage");
  // O token entre aspas (como o app pode gravar) também serve.
  const p2 = [];
  const r2 = await rodarInject({
    inject: "vcs_inject.js", href: HOST + "/sport",
    semRequisicaoInicial: true, pedido: "__sharpenupVCSReq", janelaExtra: LS(JSON.stringify(TOKEN)),
    responder: casaDublada(todos, p2),
  });
  if ((r2.ultima && r2.ultima.bilhetes || []).length !== 7 || p2.some((p) => p.auth !== TOKEN)) falhas.push("a frio: token com aspas no localStorage não foi limpo");
  return 2;
}

// Sem sessão: nada no localStorage, nenhuma chamada da página. `semToken` + `fim`, nada pedido.
async function semSessao(falhas) {
  const pedidos = [];
  const { ultima } = await rodarInject({
    inject: "vcs_inject.js", href: HOST + "/sport",
    semRequisicaoInicial: true, pedido: "__sharpenupVCSReq", janelaExtra: LS(null),
    responder: casaDublada([], pedidos), ms: 300,
  });
  if (!ultima || !ultima.fim) falhas.push("sem sessão: o inject não sinalizou `fim`");
  else if (!ultima.semToken) falhas.push("sem sessão: não disse `semToken` (o robô não acende o aviso de login)");
  if (pedidos.length) falhas.push(`sem sessão: pediu ${pedidos.length} vez(es) sem token`);
  // Token velho no storage: a casa responde 401 → erro dito, `respostas` 0.
  const r = await rodarInject({
    inject: "vcs_inject.js", href: HOST + "/sport",
    semRequisicaoInicial: true, pedido: "__sharpenupVCSReq", janelaExtra: LS(TOKEN),
    responder: (url) => (RX_LISTA.test(url) ? respostaHttp(401, JSON.stringify({ code: "UNAUTHENTICATED" })) : null), ms: 300,
  });
  if (!r.ultima || !r.ultima.fim || r.ultima.respostas !== 0 || !/401/.test(r.ultima.erro || "")) {
    falhas.push(`sessão caída: esperava fim, respostas 0 e erro com 401; veio ${JSON.stringify(r.ultima && { fim: r.ultima.fim, respostas: r.ultima.respostas, erro: r.ultima.erro })}`);
  }
  return 2;
}

// A casa encolhe a janela: o 400 diz o piso, o inject recua para ele e segue.
async function piso(falhas, todos) {
  const pedidos = [];
  const { ultima } = await rodarInject({
    inject: "vcs_inject.js", href: HOST + "/sport",
    semRequisicaoInicial: true, pedido: "__sharpenupVCSReq", janelaExtra: LS(TOKEN),
    responder: casaDublada(todos, pedidos, { pisoDias: 60 }),
  });
  const n = (ultima && ultima.bilhetes || []).length;
  if (n !== 7) falhas.push(`piso: depois do 400 com o piso, esperava 7 bilhetes, vieram ${n} (erro: ${ultima && ultima.erro})`);
  if (pedidos.length !== 2) falhas.push(`piso: esperava 2 pedidos (o recusado e o recuado), foram ${pedidos.length}`);
  return 1;
}

// Conta sem aposta na janela: `data: null` é resposta válida, vazia.
async function vazio(falhas) {
  const { ultima } = await rodarInject({
    inject: "vcs_inject.js", href: HOST + "/sport",
    semRequisicaoInicial: true, pedido: "__sharpenupVCSReq", janelaExtra: LS(TOKEN),
    responder: casaDublada([], null), ms: 300,
  });
  if (!ultima || !ultima.fim || ultima.respostas !== 1 || (ultima.bilhetes || []).length !== 0 || ultima.erro) {
    falhas.push(`vazio: \`data: null\` não virou lista vazia válida (${JSON.stringify(ultima && { fim: ultima.fim, respostas: ultima.respostas, erro: ultima.erro })})`);
  }
  return 1;
}

// Rodada nova (lição da s393): o 2º pedido, depois do `fim`, busca de novo.
async function novaRodada(falhas, todos) {
  const pedidos = [];
  const { mensagens } = await rodarInject({
    inject: "vcs_inject.js", href: HOST + "/sport",
    semRequisicaoInicial: true, pedido: "__sharpenupVCSReq", janelaExtra: LS(TOKEN),
    pedidoTardio: { __sharpenupVCSReq: true },
    responder: casaDublada(todos, pedidos), ms: 600,
  });
  if (pedidos.length < 2) falhas.push(`rodada nova: o 2º pedido não buscou de novo (${pedidos.length} pedido(s))`);
  const ult = mensagens[mensagens.length - 1];
  if (!ult || !ult.fim || (ult.bilhetes || []).length !== 7) falhas.push("rodada nova: a 2ª rodada não terminou com os 7 bilhetes");
  return 1;
}
