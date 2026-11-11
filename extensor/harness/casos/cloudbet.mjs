// Cloudbet (cloudbet.com) — captura por API, só o SPORTSBOOK. Recon 10/11/2026 (s442), conta em
// USDT, pelo navegador do Feca.
//
// PLATAFORMA PRÓPRIA, sem casa irmã no sistema: front Next.js, API no MESMO domínio
// (`/sports-betting/v4/`, `/sports-api/v6/`). Inject e formatador próprios: `cb_inject.js`,
// `formatTicketCB`.
//
//   GET /sports-betting/v4/bets/positions?limit=999&locale=en&offset=N&status=ACCEPTED|COMPLETED
//       [&from=<iso>&to=<iso>]                          → { hasNext, items:[posição] }
//   GET /sports-betting/v4/bets/positions/{positionId}?currency=<nativa>&locale=en
//                                                       → { bets:[aposta] }
//   GET /sports-api/v6/sports/events/{eventId}?locale=en&markets=x   → evento
//
// A FIXTURE (`cloudbet.recon.json`) é a conta INTEIRA no dia do recon, as quatro respostas
// juntas: `lista_abertas` (15 posições), `lista_liquidadas` (4), `detalhes` (19, pedidos em USDT)
// e `eventos` (10, só os campos que o inject guarda). Todas múltiplas de 3, NBA e NFL; as 4
// liquidadas são PERDIDAS. Nenhum campo de identidade (o bilhete não tem).
//
// O que este caso trava, cada item cruzado com o card da casa (tela em USDT):
//   • AUTENTICAÇÃO: o cookie não basta (HTTP 401). A página manda `authorization`,
//     `x-cloudbet-metadata` e `x-cloudbet-version` em toda chamada de `/sports-api/` e
//     `/sports-betting/`, e o inject os aprende de uma chamada real. O valor nunca sai dele.
//   • JANELA: o painel pede 72 h; o replay pede as abertas sem janela e as liquidadas em janelas
//     de no máximo 1 ano (o servidor recusa mais), pela LIQUIDAÇÃO, até a janela de dias do robô.
//   • PAGINAÇÃO por `offset`, fim em `hasNext:false` (medido com limit 6: 6, 6, 3).
//   • CÓDIGO é o `uuid` da aposta (o "ID: 225709c2-…" do card expandido), não o `positionId`.
//   • DETALHE só na moeda NATIVA (as chaves de `portfolio`): em outra moeda volta vazio. A lista
//     CONVERTE o dinheiro para a moeda pedida e por isso não entra no bilhete.
//   • ODD é `price` do detalhe (o "@ 6.93" do card, 6,934 sem cortar). A da lista é 0 em 3 das 4
//     perdidas e a tela imprime "@ 0.00" no histórico.
//   • ⚠ `returnAmount` é o LUCRO (−30 na perdida de 30): o retorno é stake + returnAmount.
//   • Bet Builder (`SAME_GAME_PARLAY`): cada perna leva a odd do Criar Aposta do SEU jogo, e a
//     odd do bilhete é o produto dos jogos (225709c2: 3,52 × 1,97 = 6,934; o card mostra os dois
//     jogos, DET×WAS com 2 seleções e TOR×MEM com 1).
//   • DATA do evento é o `cutoffTime` (UTC), a mais recente das pernas, em São Paulo.
//
// s445 (11/11/2026): `cloudbet.posicoes.json`, medida ao vivo, 7 posições, 9 sub-posições, 57
// apostas, com ganha, simples (EVENT), PUSH e PARTIAL. Trava o detalhe por `betLegIdentifier`
// (pelo positionId do EVENT ele volta vazio), paginado (20 sem limit, até 100), e a sub-posição
// de N > 1 apostas virando UM bilhete com o dinheiro do `portfolio` da casa. Mutações (11/11):
// sem limit, pelo positionId, não juntar, sem paginar, média simples, juntada sem a régua por
// aposta, PARTIAL fora: 7 de 7 detectadas.
//
// NÃO COBERTO por amostra real (a conta não tinha): cashout, freebet, boost, aposta em outra
// moeda, juntada ABERTA. Os casos de dinheiro sem amostra estão travados por CLONE da perdida: só
// o número prova; o resto sobe "a conferir".
import { rodarInject, carregarContent, fixture, linha, respostaHttp } from "../sandbox.mjs";

export const casa = "cloudbet";

const HOST = "https://www.cloudbet.com";
const P_POS = "/sports-betting/v4/bets/positions";
const P_EV = "/sports-api/v6/sports/events/";
const TOKEN = "Bearer jwt.harness.segredo";
const H_PAGINA = { authorization: TOKEN, "x-cloudbet-metadata": "meta-harness", "x-cloudbet-version": "v-harness" };

const L = /^Perdeu → L$/;
const ABERTA = /^em aberto \(aguardando resultado — NÃO liquidar; sem resultado\)$/;
const CONFERIR = /a conferir — não liquidar automaticamente/;

const FX = () => JSON.parse(fixture("cloudbet.recon.json"));

// uuid → o que o card mostra. `col` = colocação em São Paulo (o card imprime 09/11/2026 15:11:40).
const ESPERADO = {
  "225709c2-3e94-467c-9812-37379a7082cf": { st: L, odd: "6,934", col: "09/11/2026 15:11:40", ev: "09/11/2026 21:30:00",
    tipo: "Múltipla (3 seleções em 2 jogos; 1 deles em Criar Aposta, com a odd do conjunto do jogo)" },
  "d4789569-da3e-4732-a7e1-995257a42fd1": { st: L, odd: "9,67", col: "09/11/2026 17:19:46", ev: "09/11/2026 21:00:00",
    tipo: "Criar Aposta / mesmo jogo (3 seleções; a odd é a do conjunto)" },
  "0b08efd7-5995-425a-8f7c-cd8c42403bc6": { st: L, odd: "7,68", col: "09/11/2026 14:53:03", ev: "09/11/2026 22:30:00",
    tipo: "Múltipla (3 seleções em 3 jogos)" },
  "c763f002-585d-406a-920e-369d564ee5de": { st: L, odd: "6,48", col: "09/11/2026 18:41:53", ev: "10/11/2026 00:00:00",
    tipo: "Múltipla (3 seleções em 2 jogos; 1 deles em Criar Aposta, com a odd do conjunto do jogo)" },
};

// Simula a casa. Sem os três cabeçalhos: 401 em tudo, como o cookie sozinho.
function casaCB(fx, registro, { logado = true, tetoLimite = 1000 } = {}) {
  return (url, opts) => {
    if (!String(url).startsWith(HOST + "/")) return null;
    const u = new URL(String(url));
    const q = Object.fromEntries(u.searchParams);
    const h = (opts && opts.headers) || {};
    registro.push({ p: u.pathname, q, h, cred: opts && opts.credentials });
    const autenticado = logado && h.authorization === TOKEN && h["x-cloudbet-metadata"] === "meta-harness" &&
                        h["x-cloudbet-version"] === "v-harness";
    if (!autenticado) return respostaHttp(401, JSON.stringify({ error: "unauthorized" }));
    if (u.pathname === P_POS) {
      const limite = Number(q.limit || 20), offset = Number(q.offset || 0);
      if (limite > tetoLimite) return respostaHttp(400, JSON.stringify({ error: "number must be at most " + tetoLimite }));
      let itens;
      if ((q.status || "COMPLETED") === "ACCEPTED") itens = fx.lista_abertas.items;
      else {
        if (!q.from || !q.to) return respostaHttp(400, JSON.stringify({ error: "invalid date range" }));
        const de = Date.parse(q.from), ate = Date.parse(q.to);
        if (!(ate > de) || ate - de > 366 * 86400000) return respostaHttp(400, JSON.stringify({ error: "must not exceed 1 year" }));
        itens = fx.lista_liquidadas.items.filter((i) => { const t = Date.parse(i.positionTime); return t >= de && t < ate; });
      }
      const fatia = itens.slice(offset, offset + limite);
      return JSON.stringify({ hasNext: offset + fatia.length < itens.length, items: fatia });
    }
    if (u.pathname.startsWith(P_POS + "/")) {
      const id = decodeURIComponent(u.pathname.slice(P_POS.length + 1));
      // Medido em 11/11/2026 (s445): o detalhe é por `betLegIdentifier`; o `positionId` de um
      // EVENT (simples) devolve 200 com `bets:[]`. Página de 20 sem `limit`, até 100 com ele
      // (200 dá 400), resto por `offset`, sem `hasNext`.
      const limite = q.limit == null ? 20 : Number(q.limit), offset = Number(q.offset || 0);
      if (limite > 100) return respostaHttp(400, JSON.stringify({ error: "limit must be at most 100" }));
      const det = fx.detalhes[id];
      // Só na moeda nativa: em outra, a casa devolve vazio (medido).
      if (!det || q.currency !== "USDT") return JSON.stringify({ bets: [] });
      return JSON.stringify({ bets: det.bets.slice(offset, offset + limite) });
    }
    if (u.pathname.startsWith(P_EV)) {
      const e = fx.eventos[decodeURIComponent(u.pathname.slice(P_EV.length))];
      return e ? JSON.stringify(Object.assign({ markets: {}, players: { x: { name: "Fulano" } } }, e)) : respostaHttp(404, "{}");
    }
    return JSON.stringify({});
  };
}

async function rodarPadrao(fx, registro, extra = {}, opcCasa = {}) {
  return rodarInject(Object.assign({
    inject: "cb_inject.js",
    href: HOST + "/en/sports",
    // A página chama `/sports-api/` sozinha ao carregar, com os três cabeçalhos (medido).
    urlInicial: HOST + "/sports-api/v6/sports/events/37178286?locale=en",
    optsInicial: { method: "GET", headers: H_PAGINA },
    pedidoMsg: { __sharpenupCBReq: true, desde: 0 },
    responder: casaCB(fx, registro, opcCasa),
    ms: 700,
  }, extra));
}

const _lista = (r) => r.filter((x) => x.p === P_POS);
const _det = (r) => r.filter((x) => x.p.startsWith(P_POS + "/"));

export async function rodar() {
  const fx = FX();
  const total = Object.values(fx.detalhes).reduce((s, d) => s + d.bets.length, 0);
  const registro = [];
  const { ultima, mensagens } = await rodarPadrao(fx, registro);

  const falhas = [];
  if (!ultima) return { falhas: ["o inject não emitiu nenhuma mensagem"], testes: 0 };
  if (!ultima.hook) falhas.push("o inject não emitiu `hook:true` (autodiagnóstico cego)");
  if (!ultima.fim) falhas.push("o inject não sinalizou `fim` (o robô ficaria esperando o teto)");
  if (ultima.erro) falhas.push(`erro com a sessão viva: "${ultima.erro}"`);
  if (ultima.semToken) falhas.push("`semToken` com os cabeçalhos aprendidos");
  const tudo = JSON.stringify(mensagens);
  if (tudo.includes("jwt.harness.segredo") || tudo.includes("meta-harness")) falhas.push("o cabeçalho de auth vazou na mensagem para o content");
  if (tudo.includes("Fulano")) falhas.push("os jogadores do evento vazaram no bilhete/cru (só os campos do jogo sobem)");

  const bilhetes = ultima.bilhetes || [];
  if (bilhetes.length !== total) falhas.push(`esperava ${total} apostas (15 abertas + 4 liquidadas), vieram ${bilhetes.length}`);

  // Replay: abertas sem janela; liquidadas com from/to ≤ 1 ano; detalhe na moeda nativa.
  const lista = _lista(registro);
  if (!lista.some((r) => r.q.status === "ACCEPTED")) falhas.push("o replay não pediu as abertas");
  const liq = lista.filter((r) => r.q.status === "COMPLETED");
  if (!liq.length) falhas.push("o replay não pediu as liquidadas");
  if (liq.some((r) => !r.q.from || !r.q.to || Date.parse(r.q.to) - Date.parse(r.q.from) > 365 * 86400000)) falhas.push("janela de liquidadas sem from/to ou maior que 1 ano");
  if (liq.length && !(Date.parse(liq[0].q.to) > Date.now())) falhas.push("a 1ª janela termina no passado (a aposta de hoje ficaria de fora)");
  if (!liq.some((r) => Date.parse(r.q.from) <= Date.UTC(2013, 0, 2))) falhas.push("com `desde: 0` o replay não desceu até o piso de 2013");
  if (lista.some((r) => r.q.limit !== "999")) falhas.push("a lista não pediu 999 por página");
  if (_det(registro).some((r) => r.q.currency !== "USDT")) falhas.push("detalhe pedido fora da moeda nativa (portfolio)");
  if (_det(registro).length !== 19) falhas.push(`esperava 19 detalhes (um por posição), vieram ${_det(registro).length}`);
  const evs = registro.filter((r) => r.p.startsWith(P_EV) && r.q.markets === "x");
  if (evs.length !== 10) falhas.push(`esperava 10 eventos distintos com markets=x, vieram ${evs.length}`);
  if (registro.slice(1).some((r) => r.h.authorization !== TOKEN)) falhas.push("requisição do replay sem o authorization aprendido");

  // O cru tem de ser a aposta do detalhe, com o mesmo código, a posição e os eventos das pernas.
  const cru = ultima.cru || [];
  if (cru.length !== total) falhas.push(`cru: esperava ${total} itens, vieram ${cru.length}`);
  for (const c of cru) {
    const k = c.cru || {};
    if (!k.aposta || k.aposta.uuid !== c.codigo) falhas.push(`cru ${c.codigo}: não é a aposta da casa com o mesmo código`);
    else if (!k.posicao || !Array.isArray(k.posicao.positions)) falhas.push(`cru ${c.codigo}: sem a posição (os nomes de mercado só existem nela)`);
    else {
      const ids = new Set(k.aposta.selections.map((s) => String(s.eventId)));
      for (const id of ids) if (!(k.eventos || {})[id] || !k.eventos[id].cutoffTime) falhas.push(`cru ${c.codigo}: sem o evento ${id} (jogo e início)`);
    }
  }

  const fmt = carregarContent().pegar("formatTicketCB");
  const porId = new Map(bilhetes.map((b) => [b.id, b]));
  let testes = 0;

  for (const b of bilhetes) {
    const txt = fmt(b);
    if (!txt.startsWith(`[Código: ${b.id}]`)) falhas.push(`${b.id}: marcador [Código:] ausente/errado`);
    if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(b.id)) falhas.push(`${b.id}: código fora do formato (uuid da aposta)`);
    if (linha(txt, "Moeda:") !== "USDT") falhas.push(`${b.id}: faltou a linha "Moeda: USDT"`);
    if (!/^\d{14}$/.test(linha(txt, "Carimbo de colocação:"))) falhas.push(`${b.id}: faltou o carimbo de colocação`);
    if (/R\$/.test(txt)) falhas.push(`${b.id}: o bloco diz "R$" numa conta em USDT`);
    if (/undefined|null|NaN/.test(txt)) falhas.push(`${b.id}: "undefined"/"null"/"NaN" no bloco`);
    if ((txt.match(/^- /gm) || []).length !== 3) falhas.push(`${b.id}: esperava 3 seleções`);
    if (/\(mercado sem nome\)|\(seleção sem nome\)|Jogo: \(a casa/.test(txt)) falhas.push(`${b.id}: perna sem nome de mercado, seleção ou jogo`);
    if (!/Esporte: (Basketball|American Football)/.test(txt)) falhas.push(`${b.id}: sem esporte`);
    if (/^0*(,0*)?$/.test(linha(txt, "Odd:"))) falhas.push(`${b.id}: odd zerada ou ausente`);
    if (!/^Data \(evento mais recente\): \d\d\/\d\d\/\d{4} \d\d:\d\d:\d\d$/m.test(txt)) falhas.push(`${b.id}: sem data do evento`);
  }

  for (const [idb, e] of Object.entries(ESPERADO)) {
    const b = porId.get(idb);
    if (!b) { falhas.push(`${idb}: não chegou ao lote`); continue; }
    const txt = fmt(b);
    testes++;
    if (!e.st.test(linha(txt, "Status:"))) falhas.push(`${idb}: status "${linha(txt, "Status:")}"`);
    if (linha(txt, "Odd:") !== e.odd) falhas.push(`${idb}: odd esperada ${e.odd}, veio "${linha(txt, "Odd:")}" (price do detalhe, sem cortar)`);
    if (linha(txt, "Stake:") !== "30,00") falhas.push(`${idb}: stake "${linha(txt, "Stake:")}"`);
    if (linha(txt, "Data (colocação):") !== e.col) falhas.push(`${idb}: colocação "${linha(txt, "Data (colocação):")}" (createTime UTC → São Paulo)`);
    if (linha(txt, "Data (evento mais recente):") !== e.ev) falhas.push(`${idb}: evento "${linha(txt, "Data (evento mais recente):")}" (cutoffTime mais tardio → São Paulo)`);
    if (linha(txt, "Tipo:") !== e.tipo) falhas.push(`${idb}: tipo "${linha(txt, "Tipo:")}"`);
    if (/^Retorno potencial/m.test(txt)) falhas.push(`${idb}: liquidada com "Retorno potencial"`);
  }

  // A do card expandido: Won 1 · Lost 1 · Push 1, os nomes como a casa escreve, dois jogos.
  {
    const txt = fmt(porId.get("225709c2-3e94-467c-9812-37379a7082cf") || {});
    if (!/^- Paul Reed Total Assists: Under 2\.5 \[perna ganha\]$/m.test(txt)) falhas.push("225709c2: perna ganha (Paul Reed) fora do formato do card");
    if (!/^- Kyshawn George Total Rebounds: Over 4\.5 \[perna perdida\]$/m.test(txt)) falhas.push("225709c2: perna perdida (Kyshawn George) não marcada");
    if (!/^- Collin Murray-Boyles Total Points \+ Assists: Under 15\.5 \[perna anulada \(push\)\]$/m.test(txt)) falhas.push("225709c2: perna PUSH não marcada como anulada");
    if (!/Jogo: DET Pistons v WAS Wizards · Liga: NBA \(USA\) · Esporte: Basketball · Início: 09\/11\/2026 21:00:00/.test(txt)) falhas.push("225709c2: jogo/liga/esporte/início da perna faltando");
    if (!/Odd do Criar Aposta deste jogo \(não é da perna\): 3,52/.test(txt)) falhas.push("225709c2: a odd 3,52 do Criar Aposta não saiu como do conjunto");
    if (!/Odd da perna: 1,97/.test(txt)) falhas.push("225709c2: a perna avulsa (1,97) sem a odd própria");
    if (/30,00 USDT\)$/m.test(linha(txt, "Status:"))) falhas.push("225709c2: o lucro virou retorno");
  }
  // Criar Aposta puro: nenhuma linha de odd por perna (todas repetem a do bilhete).
  {
    const txt = fmt(porId.get("d4789569-da3e-4732-a7e1-995257a42fd1") || {});
    if (/Odd da perna|Odd do Criar Aposta/.test(txt)) falhas.push("d4789569: Criar Aposta puro com odd por perna (é a do conjunto)");
  }
  // Parlay: cada perna com a odd própria; PENDING de perdida não é resultado.
  {
    const txt = fmt(porId.get("0b08efd7-5995-425a-8f7c-cd8c42403bc6") || {});
    for (const o of ["2,1", "2,19", "1,67"]) if (!new RegExp("Odd da perna: " + o.replace(",", "\\,") + "$", "m").test(txt)) falhas.push(`0b08efd7: faltou a odd da perna ${o}`);
    if (!/\[perna não decidida\]/.test(txt)) falhas.push("0b08efd7: perna PENDING de bilhete perdido não saiu como não decidida");
  }
  // Aberta: retorno POTENCIAL (stake × odd), perna decidida pela casa em linha própria.
  {
    const txt = fmt(porId.get("1e7c2017-c4ba-437d-b7a0-304833f85d24") || {});
    testes++;
    if (!ABERTA.test(linha(txt, "Status:"))) falhas.push(`1e7c2017: aberta virou "${linha(txt, "Status:")}"`);
    if (linha(txt, "Retorno potencial (se ganhar):") !== "208,11 USDT") falhas.push(`1e7c2017: retorno potencial "${linha(txt, "Retorno potencial (se ganhar):")}" (30 × 6,937 = 208,11)`);
    if (/\[perna /.test(txt)) falhas.push("1e7c2017: perna de aberta marcada no colchete (o bilhete não liquidou)");
    if (!/Estado da perna \(casa\): WIN/.test(txt)) falhas.push("1e7c2017: o estado cru da perna decidida não subiu");
    if (linha(txt, "Odd:") !== "6,937") falhas.push(`1e7c2017: odd "${linha(txt, "Odd:")}"`);
    if (/0001/.test(txt)) falhas.push("1e7c2017: a data sentinela 0001-01-01 da aberta vazou no bloco");
    // A aberta traz `completeTime: 0001-01-01T00:00:00Z` (medido): data falsa é pior que ausente.
    const ab = porId.get("1e7c2017-c4ba-437d-b7a0-304833f85d24");
    if (ab && ab.liquidada !== null) falhas.push(`1e7c2017: aberta com liquidação ${ab.liquidada} (a sentinela 0001-01-01 virou data)`);
  }

  // Dinheiro sem amostra real: clone da perdida, só o que o número prova vira resultado.
  {
    const base = porId.get("0b08efd7-5995-425a-8f7c-cd8c42403bc6");   // 30 USDT @ 7,68, parlay
    if (!base) falhas.push("0b08efd7: a perdida-base dos clones não chegou");
    else {
      const c = (o) => linha(fmt(Object.assign({}, base, o)), "Status:");
      const semPush = base.pernas.map((p) => Object.assign({}, p, { resultado: "WIN" }));
      const ganha = c({ resultado: "WIN", lucro: 200.4, pernas: semPush });
      if (ganha !== "Ganhou → W (retorno 230,40 USDT)") falhas.push(`WIN que fecha (30 × 7,68 = 230,40) virou "${ganha}"`);
      const naoFecha = c({ resultado: "WIN", lucro: 150, pernas: semPush });
      if (!CONFERIR.test(naoFecha)) falhas.push(`WIN sem perna anulada e dinheiro que não fecha virou "${naoFecha}"`);
      const comPush = c({ resultado: "WIN", lucro: 75.21, pernas: base.pernas.map((p) => Object.assign({}, p, { resultado: p.resultado === "PUSH" ? "PUSH" : "WIN" })) });
      if (!/^Ganhou com perna anulada → W \(retorno 105,21 USDT; odd = retorno ÷ stake = 3,507\)$/.test(comPush)) falhas.push(`WIN com perna PUSH virou "${comPush}"`);
      const anulada = c({ resultado: "PUSH", lucro: 0 });
      if (!/→ V$/.test(anulada)) falhas.push(`lucro 0 (retorno = stake) virou "${anulada}"`);
      const desconhecido = c({ resultado: "HALF_WIN", lucro: 200.4 });
      if (!CONFERIR.test(desconhecido)) falhas.push(`rótulo desconhecido com o dinheiro de W virou "${desconhecido}"`);
      const perdidaComDinheiro = c({ lucro: -12.5 });
      if (L.test(perdidaComDinheiro)) falhas.push(`LOSS com retorno 17,50 virou "${perdidaComDinheiro}"`);
      const semLucro = c({ lucro: null });
      if (!CONFERIR.test(semLucro)) falhas.push(`liquidada sem returnAmount virou "${semLucro}"`);
      const cashout = c({ cashout: true, resultado: "WIN", lucro: 10 });
      if (!CONFERIR.test(cashout)) falhas.push(`cashout sem amostra virou "${cashout}"`);
      const semOdd = linha(fmt(Object.assign({}, base, { odd: 0 })), "Odd:");
      if (!/deixe a odd VAZIA/.test(semOdd)) falhas.push(`odd 0 virou "${semOdd}" (zero não é ausência)`);
      const simples = fmt(Object.assign({}, base, { pernas: [base.pernas[0]] }));
      if (linha(simples, "Tipo:") !== "Simples" || /Odd da perna/.test(simples)) falhas.push("simples: tipo errado ou odd da perna repetida");
      if (/^Moeda:/m.test(fmt(Object.assign({}, base, { moeda: "" })))) falhas.push("moeda ausente virou linha de moeda");
      if (!/Apostas na posição/.test(fmt(Object.assign({}, base, { apostasNaPosicao: 2 })))) falhas.push("posição com 2 apostas não avisou");
    }
  }

  testes += await janelaDoRobo(falhas);
  testes += await paginacao(falhas);
  testes += await semCabecalho(falhas);
  testes += await semSessao(falhas);
  testes += await liquidadaVenceAberta(falhas);
  testes += await posicoesJuntadas(falhas);
  testes += await detalhePaginado(falhas);
  testes += await oddPonderada(falhas);
  return { falhas, testes };
}

// ── s445: posição com várias apostas ────────────────────────────────────────────────────────
// Fixture `cloudbet.posicoes.json`, medida ao vivo em 11/11/2026 (USDT): 7 posições, 9
// sub-posições, 57 apostas. O card mostra UMA aposta por sub-posição; a referência do dinheiro é o
// `portfolio` dela, a soma que a própria casa faz.
const FXP = () => JSON.parse(fixture("cloudbet.posicoes.json"));
const L6 = "0dbcfd56af57199afd64a7846b1d8eb2fb038db3";      // Bet Builder, 6 apostas, 6,94 e 7,58, L
const P35 = "c4e03fcd4631e41a2400eb8343fa738dbb9bcd90";     // parlay, 35 apostas
const W5 = "078f360f78e8a70f0a09353d3846f908480d51cd";      // Bet Builder, 5 apostas, ganha
const PUSH2 = "a10af6d67a378d08b9627f9352f0ba6243f0b4ac";   // simples (EVENT), 2 apostas anuladas

async function posicoesJuntadas(falhas) {
  const fx = FXP();
  const registro = [];
  const { ultima } = await rodarPadrao(fx, registro, { ms: 1500 });
  const bs = (ultima && ultima.bilhetes) || [];
  const porId = new Map(bs.map((b) => [b.id, b]));
  const fmt = carregarContent().pegar("formatTicketCB");
  if (bs.length !== 9) falhas.push(`posições: esperava 9 bilhetes (um por sub-posição), vieram ${bs.length}`);
  const somaApostas = bs.reduce((s, b) => s + (b.consolidadas || 1), 0);
  if (somaApostas !== 57) falhas.push(`posições: os bilhetes cobrem ${somaApostas} apostas, a casa tem 57`);
  const det = _det(registro);
  if (det.some((r) => /^\d{8}$/.test(r.p.slice(P_POS.length + 1)))) falhas.push("posições: detalhe pedido pelo positionId do EVENT (volta vazio: a simples some)");
  if (det.some((r) => r.q.limit !== "100")) falhas.push("posições: detalhe sem limit=100 (a casa pagina em 20)");

  // Dinheiro de cada juntada = o portfolio da sub-posição.
  const subs = new Map();
  for (const it of fx.lista_liquidadas.items) for (const p of it.positions) subs.set(p.betLegIdentifier, p);
  for (const b of bs) {
    if (!(b.consolidadas > 1)) continue;
    const port = subs.get(b.id) && subs.get(b.id).portfolio.USDT;
    if (!port) { falhas.push(`${b.id}: juntada com código que não é sub-posição`); continue; }
    if (Math.abs(b.stake - Number(port.stakeAmount)) > 1e-9) falhas.push(`${b.id}: stake ${b.stake} ≠ ${port.stakeAmount} da casa`);
    if (Math.abs(b.lucro - Number(port.returnAmount)) > 1e-9) falhas.push(`${b.id}: lucro ${b.lucro} ≠ ${port.returnAmount} da casa`);
    if (b.consolidadas !== subs.get(b.id).betCount) falhas.push(`${b.id}: ${b.consolidadas} apostas juntadas, a casa diz ${subs.get(b.id).betCount}`);
  }
  const p35 = porId.get(P35);
  if (!p35 || p35.consolidadas !== 35) falhas.push(`35 apostas: vieram ${p35 && p35.consolidadas} (a 1ª página do detalhe tem 20)`);

  const l6 = fmt(porId.get(L6) || {});
  if (linha(l6, "Status:") !== "Perdeu → L") falhas.push(`L6: status "${linha(l6, "Status:")}"`);
  if (linha(l6, "Odd:") !== "7,1533") falhas.push(`L6: odd "${linha(l6, "Odd:")}" (média ponderada medida na aba: 7,1533)`);
  if (linha(l6, "Stake:") !== "30,00") falhas.push(`L6: stake "${linha(l6, "Stake:")}"`);
  if (!/^Odd de cada aposta \(casa\): de 6,94 a 7,58/m.test(l6)) falhas.push("L6: faltou a faixa de odd das apostas");
  if (!/^Apostas juntadas: 6 /m.test(l6)) falhas.push("L6: faltou a linha das apostas juntadas");
  if (/a conferir/.test(l6)) falhas.push("L6: a juntada ficou \"a conferir\"");
  if (/undefined|null|NaN/.test(l6)) falhas.push("L6: undefined/null/NaN no bloco");
  const w5 = linha(fmt(porId.get(W5) || {}), "Status:");
  if (!/^Ganhou → W \(retorno 292,95 USDT, soma das 5 apostas; odd = retorno ÷ stake = 8,37\)$/.test(w5)) falhas.push(`W5: status "${w5}"`);
  const v2 = linha(fmt(porId.get(PUSH2) || {}), "Status:");
  if (!/→ V$/.test(v2)) falhas.push(`PUSH2: status "${v2}"`);
  const partial = bs.find((b) => b.resultado === "PARTIAL");
  const tp = partial ? linha(fmt(partial), "Status:") : "";
  if (tp !== "Ganhou com perna anulada → W (retorno 159,87 USDT; odd = retorno ÷ stake = 5,329)") falhas.push(`PARTIAL: status "${tp}"`);
  // Uma aposta perdida no meio de uma juntada de ganhas não fecha: a conferir.
  const w = porId.get(W5);
  if (w) {
    const misto = Object.assign({}, w, { apostas: w.apostas.map((a, i) => i ? a : Object.assign({}, a, { resultado: "LOSS", lucro: -a.stake })) });
    if (!CONFERIR.test(linha(fmt(misto), "Status:"))) falhas.push("juntada com resultados diferentes não ficou a conferir");
  }

  // O cru da juntada: o código, os uuids de todas, abaixo do teto de 64 KB do servidor.
  const crus = new Map(((ultima && ultima.cru) || []).map((c) => [c.codigo, c.cru]));
  for (const b of bs) {
    const c = crus.get(b.id);
    if (!c) { falhas.push(`${b.id}: sem cru`); continue; }
    if (!(b.consolidadas > 1)) continue;
    if (c.grupo !== b.id || !Array.isArray(c.apostas) || c.apostas.length !== b.consolidadas) falhas.push(`${b.id}: cru sem o grupo ou sem as ${b.consolidadas} apostas`);
    else if (c.apostas.some((a) => !a.uuid || a.precos.length !== c.aposta.selections.length)) falhas.push(`${b.id}: aposta do cru sem uuid ou sem os preços alinhados`);
    if (JSON.stringify(c).length > 64 * 1024) falhas.push(`${b.id}: cru acima de 64 KB (o servidor descarta)`);
  }
  return 1;
}

// Odd PONDERADA pela stake. Na fixture as 6 apostas da L6 têm a mesma stake e as duas médias
// coincidem; com 25 na 1ª (6,94) e 5 nas outras: 353,4 ÷ 50 = 7,068 (a simples seria 7,1533).
async function oddPonderada(falhas) {
  const fx = FXP();
  Object.assign(fx.detalhes[L6].bets[0], { stake: "25", returnAmount: "-25" });
  const { ultima } = await rodarPadrao(fx, [], { ms: 1500 });
  const b = ((ultima && ultima.bilhetes) || []).find((x) => x.id === L6);
  const txt = b ? carregarContent().pegar("formatTicketCB")(b) : "";
  if (linha(txt, "Odd:") !== "7,068") falhas.push(`odd ponderada: "${linha(txt, "Odd:")}", esperava 7,068`);
  if (linha(txt, "Stake:") !== "50,00") falhas.push(`odd ponderada: stake "${linha(txt, "Stake:")}"`);
  return 1;
}

// Sub-posição com mais de 100 apostas: segue pelo `offset` até a página curta.
async function detalhePaginado(falhas) {
  const fx = FXP();
  const base = fx.detalhes[P35].bets;
  const bets = [];
  for (let i = 0; i < 230; i++) bets.push(Object.assign({}, base[i % base.length], { uuid: "u-" + i }));
  fx.detalhes[P35] = { bets };
  const sub = fx.lista_liquidadas.items.find((i) => i.positionId === P35).positions[0];
  sub.betCount = 230;
  const registro = [];
  const { ultima } = await rodarPadrao(fx, registro, { ms: 1500 });
  const b = ((ultima && ultima.bilhetes) || []).find((x) => x.id === P35);
  if (!b || b.consolidadas !== 230) falhas.push(`230 apostas: vieram ${b && b.consolidadas}`);
  const offs = _det(registro).filter((r) => r.p.endsWith(P35)).map((r) => r.q.offset).join(",");
  if (offs !== "0,100,200") falhas.push(`230 apostas: offsets ${offs}, esperava 0,100,200`);
  return 1;
}

// A janela de dias do robô: nenhuma janela de liquidadas antes dela (menos a folga de 2 dias).
async function janelaDoRobo(falhas) {
  const registro = [];
  const desde = Date.now() - 30 * 86400000;
  await rodarPadrao(FX(), registro, { pedidoMsg: { __sharpenupCBReq: true, desde } });
  const liq = _lista(registro).filter((r) => r.q.status === "COMPLETED");
  if (liq.length !== 1) falhas.push(`janela de 30 dias: ${liq.length} janela(s) de liquidadas pedidas — esperava 1`);
  if (liq.some((r) => Date.parse(r.q.from) < desde - 3 * 86400000)) falhas.push("janela de 30 dias: pediu liquidadas antes da janela do robô");
  return 1;
}

// N abertas: avança pelo que VOLTOU até `hasNext:false`, nenhuma página a mais.
async function paginacao(falhas) {
  const fx = FX();
  const modelo = fx.lista_abertas.items;
  const itens = [];
  for (let i = 0; i < 2100; i++) itens.push(Object.assign({}, modelo[i % modelo.length], { positionId: "p" + i }));
  fx.lista_abertas = { hasNext: false, items: itens };
  const registro = [];
  // Os detalhes não existem para "pN" (404): basta contar as páginas da lista.
  await rodarPadrao(fx, registro, { ms: 900 });
  const offs = _lista(registro).filter((r) => r.q.status === "ACCEPTED").map((r) => r.q.offset);
  if (offs.join(",") !== "0,999,1998") falhas.push(`paginação de 2100 abertas: offsets ${offs.join(",")}, esperava 0,999,1998 (fim = hasNext:false)`);
  return 1;
}

// A página ainda não fez chamada nenhuma: sem cabeçalho, sem replay, e o content é avisado.
async function semCabecalho(falhas) {
  const registro = [];
  const { ultima } = await rodarPadrao(FX(), registro, { semRequisicaoInicial: true, ms: 300 });
  if (!ultima || !ultima.semToken) falhas.push("sem cabeçalho aprendido: o inject não avisou `semToken`");
  if (registro.length) falhas.push(`sem cabeçalho aprendido: ${registro.length} requisição(ões) — o replay não pode sair sem auth`);
  return 1;
}

// Sessão caída: 401. O inject diz o erro, sinaliza fim e não fica em laço.
async function semSessao(falhas) {
  const registro = [];
  const { ultima } = await rodarPadrao(FX(), registro, { ms: 400 }, { logado: false });
  if (!ultima || !ultima.fim) falhas.push("sem sessão: o inject não sinalizou fim");
  if (!ultima || !/401/.test(String(ultima.erro || ""))) falhas.push(`sem sessão: erro não diz o HTTP 401 (veio "${ultima && ultima.erro}")`);
  if (registro.length > 4) falhas.push(`sem sessão: ${registro.length} requisições (laço?)`);
  return 1;
}

// A mesma posição nas duas listas (liquidou entre as duas chamadas): a liquidada vence.
async function liquidadaVenceAberta(falhas) {
  const fx = FX();
  const liq = fx.lista_liquidadas.items[0];
  fx.lista_abertas.items = fx.lista_abertas.items.concat([Object.assign({}, liq, { positionStatus: "ACCEPTED" })]);
  const { ultima } = await rodarPadrao(fx, []);
  const b = ((ultima && ultima.bilhetes) || []).filter((x) => x.posicao === liq.positionId);
  if (b.length !== 1) falhas.push(`liquidada × aberta: a posição veio ${b.length} vez(es)`);
  else if (b[0].aberta) falhas.push("liquidada × aberta: a versão aberta venceu");
  return 1;
}
