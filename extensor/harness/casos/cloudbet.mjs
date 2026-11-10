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
// NÃO COBERTO por amostra real (a conta não tinha): ganha, simples, cashout, freebet, boost,
// posição com mais de uma aposta, aposta em outra moeda. Os casos de dinheiro estão travados por
// CLONE da perdida: só o número prova; o resto sobe "a conferir".
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
      const det = fx.detalhes[id];
      if (!det) return respostaHttp(404, "{}");
      // Só na moeda nativa: em outra, a casa devolve vazio (medido).
      return JSON.stringify(q.currency === "USDT" ? det : { bets: [] });
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
  return { falhas, testes };
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
