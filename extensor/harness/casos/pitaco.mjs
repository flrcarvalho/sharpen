// Pitaco (ex-"Rei do Pitaco") — captura por gRPC-Web/protobuf binário (s270).
//
// Primeira casa do harness cujo payload NÃO é JSON: as fixtures guardam a resposta real em
// base64 (`{b64: …}`), porque o `fixture()` do sandbox lê texto e ler binário por `text()`
// passaria pelo decode UTF-8, que estraga todo byte 0x80-0xFF. O `resposta()` do sandbox
// ganhou `arrayBuffer()` por causa disto.
//
// Trava as seis leituras que decidiram a implementação, todas cruzadas com o card renderizado:
//
//   • **a odd exibida é ARREDONDADA e não explica o retorno** — o bilhete 80010000038606210
//     estampa 3.67x, mas pagou R$ 371,62 sobre R$ 101,00 (= 3,6795, o produto das pernas).
//     Emitir a exibida erraria R$ 0,95 num bilhete só;
//   • **a data é a do EVENTO, e a casa não dá o ano dela** — em bilhete finalizado 112 de 112
//     pernas trazem só `"15/08"`; o ano vem da colocação. Não dá para usar a colocação no
//     lugar: elas divergem em 46 das 112 (o 80010000038606210 foi colocado em 14/08 e o
//     evento mais recente é 15/08);
//   • **retorno de bilhete ABERTO vem igual ao potencial** → tem de sair como "Retorno
//     potencial", nunca como ganho (a vitória fantasma da VaideBet);
//   • **anulada devolve o stake** (R$ 101,00 sobre R$ 101,00): ler o dinheiro marcaria ganho
//     de odd 1,00. Quem manda é o enum — `status=8` → V;
//   • **odd riscada** (`4.18x → 2.18x`) quando uma perna é anulada e o resto do bilhete segue;
//   • **a paginação por página PERDE bilhete**, então o inject pede a lista inteira e sobe o
//     `pageSize` enquanto a casa disser que há mais. O último teste prova a escalada.
import { rodarInject, carregarContent, fixture, linha } from "../sandbox.mjs";

export const casa = "Pitaco";

const BASE = "https://pitaco.bet.br/api/ui_betting_my_bets_components.UiMyBetsService/";
const URL_PAGE = BASE + "GetUiMyBetsPage";          // o que a página dispara no load
const URL_ALVO = BASE + "GetUiMyBetsTabContent";    // o que o replay tem de chamar

// Valores conferidos contra o card da casa (contagem por filtro: Ganhas 10 · Reembolsadas 1 ·
// Encerradas 0 — e a API devolve 10 · 1 · 0).
const ESPERADO = {
  // perdida — a odd sai do potencial (R$ 355,02 ÷ 101 = 3,515), não da exibida (3.51x)
  "80010000038632231": { odd: "3,515", status: /^Perdeu → L$/, tipo: /Múltipla \(2 seleções\)/, evento: "15/08/2026", colocacao: "15/08/2026 09:35:32" },
  // ganha simétrica: produto das pernas explica o pagamento até o centavo
  "80010000038631931": { odd: "5,45", status: /^Ganho → W \(retorno R\$ 550,45\)$/, tipo: /Múltipla \(2 seleções\)/, evento: "15/08/2026", colocacao: "15/08/2026 09:29:43" },
  // ganha COM perna anulada: odd riscada 4.18x → 2.18x, e o bilhete continua valendo
  "80010000038631915": { odd: "2,18", status: /^Ganho → W \(retorno R\$ 220,18\)$/, tipo: /Múltipla \(2 seleções\)/, evento: "15/08/2026", colocacao: "15/08/2026 09:29:29", riscada: /^4,18 → vigente 2,18$/ },
  // ⚠ o bilhete que prova as DUAS regras: odd exibida arredondada e data ≠ colocação
  "80010000038606210": { odd: "3,6795", status: /^Ganho → W \(retorno R\$ 371,62\)$/, tipo: /Múltipla \(2 seleções\)/, evento: "15/08/2026", colocacao: "14/08/2026 20:05:47" },
  // anulada ("A aposta foi recusada após revisão"): stake devolvido → V
  "80010000038596497": { odd: "1", status: /^Anulada pela casa \(stake devolvido; P\/L zero\) → V$/, tipo: /Múltipla \(2 seleções\)/, evento: "15/08/2026", colocacao: "14/08/2026 17:39:57", riscada: /^5,94 → vigente 1$/ },
  // aberta com cashout oferecido (R$ 156,09) — disponível, NÃO executado
  "80010000038724525": { odd: "4,564", status: /em aberto \(aguardando resultado/, tipo: /Múltipla \(2 seleções\)/, evento: "16/08/2026", colocacao: "16/08/2026 09:05:32", cashout: /^R\$ 156,09$/ },
  // aberta com uma perna AO VIVO (a casa manda o período, "1T")
  "80010000038724511": { odd: "7", status: /em aberto \(aguardando resultado/, tipo: /Múltipla \(2 seleções\)/, evento: "16/08/2026", colocacao: "16/08/2026 09:05:21", aoVivo: true },
};

const bytesDaFixture = (nome) => Buffer.from(JSON.parse(fixture(nome)).b64, "base64");

/** A aba pedida sai do CORPO da requisição (as duas usam a mesma URL). */
function abaDoCorpo(opts) {
  const b = opts && opts.body;
  if (!b) return null;
  const s = Buffer.from(b).toString("latin1");
  if (s.includes("finished")) return "finished";
  if (s.includes("open")) return "open";
  return null;
}

/** O `pageSize` pedido (campo 2 do corpo) — para provar a escalada sem depender da ordem. */
function tamDoCorpo(opts) {
  const b = opts && opts.body;
  if (!b) return null;
  const u = Buffer.from(b).subarray(5);          // pula o frame gRPC-Web
  for (let i = 0; i < u.length - 1; i++) {
    if (u[i] === 0x10) {                          // campo 2, wire 0
      let r = 0, s = 1, j = i + 1;
      while (j < u.length) { const x = u[j] & 0x7f; r += x * s; if (!(u[j] & 0x80)) break; s *= 128; j++; }
      return r;
    }
  }
  return null;
}

/** Remonta a resposta com o campo `.5 = 1` ("tem mais") — o sinal que dispara a escalada. */
function comTemMais(u8) {
  const len = (u8[1] * 16777216) + (u8[2] * 65536) + (u8[3] * 256) + u8[4];
  const corpo = u8.subarray(5, 5 + len);
  const novo = Buffer.concat([corpo, Buffer.from([0x28, 0x01])]);
  const out = Buffer.alloc(5 + novo.length);
  out[0] = 0;
  out.writeUInt32BE(novo.length, 1);
  novo.copy(out, 5);
  return out;
}

export async function rodar() {
  const falhas = [];
  const fin = bytesDaFixture("pitaco.finished.json");
  const abe = bytesDaFixture("pitaco.open.json");

  const { ultima, urls } = await rodarInject({
    inject: "pt_inject.js",
    href: "https://pitaco.bet.br/betting/my-bets",
    // A página dispara o `GetUiMyBetsPage`; o inject aprende dele e reescreve o método para o
    // `GetUiMyBetsTabContent` (mesmo desenho do vb_inject na Betpix365).
    urlInicial: URL_PAGE,
    optsInicial: { method: "POST", headers: { authorization: "Bearer forjado-do-harness", "x-grpc-web": "1" }, body: new Uint8Array([0, 0, 0, 0, 0]) },
    pedido: "__sharpenupPTCReq",
    responder: (url, opts) => {
      if (!/GetUiMyBetsTabContent/.test(url)) return null;   // o Page não devolve bilhete
      const aba = abaDoCorpo(opts);
      if (aba === "finished") return fin;
      if (aba === "open") return abe;
      return null;
    },
  });

  if (!ultima) return { falhas: ["o inject não emitiu nenhuma mensagem"], testes: 0 };
  if (!ultima.hook) falhas.push("o inject não sinalizou `hook` (autodiagnóstico cego)");
  if (!ultima.fim) falhas.push("o inject não sinalizou `fim` (o robô ficaria esperando o teto)");
  if (ultima.erro) falhas.push(`o inject reportou erro: ${ultima.erro}`);

  // O replay TEM de ter reescrito o método aprendido — sem isso ele chamaria o endpoint da
  // página (que não devolve bilhete) e o lote voltaria vazio com o hook ativo.
  const doReplay = urls.filter((u) => /GetUiMyBetsTabContent/.test(u));
  if (!doReplay.length) falhas.push("o replay não chamou GetUiMyBetsTabContent (a reescrita do método falhou)");
  if (doReplay.length !== 2) falhas.push(`esperava 2 requisições de replay (uma por aba), vieram ${doReplay.length}`);

  const bilhetes = ultima.bilhetes || [];
  if (bilhetes.length !== 71) falhas.push(`esperava 71 bilhetes (49 finalizados + 22 abertos), vieram ${bilhetes.length}`);

  // A contagem por status é a conferência que foi feita contra o filtro da tela.
  const porStatus = {};
  for (const b of bilhetes) porStatus[b.status] = (porStatus[b.status] || 0) + 1;
  const esperadoStatus = { 1: 6, 2: 16, 3: 10, 4: 38, 8: 1 };
  for (const k of Object.keys(esperadoStatus)) {
    if (porStatus[k] !== esperadoStatus[k]) {
      falhas.push(`status ${k}: esperava ${esperadoStatus[k]} bilhete(s), vieram ${porStatus[k] || 0}`);
    }
  }

  const fmt = carregarContent().pegar("formatTicketPTC");
  let testes = 0;
  const vistos = new Set();
  for (const b of bilhetes) {
    if (vistos.has(b.ref)) falhas.push(`código repetido no lote: ${b.ref}`);
    vistos.add(b.ref);
    const e = ESPERADO[b.ref];
    if (!e) continue;                       // só os 7 escolhidos são conferidos linha a linha
    const txt = fmt(b);
    testes++;
    if (!txt.startsWith(`[Código: ${b.ref}]`)) falhas.push(`${b.ref}: marcador [Código:] ausente/errado`);
    const odd = linha(txt, "Odd:");
    const status = linha(txt, "Status:");
    const tipo = linha(txt, "Tipo:");
    const evento = linha(txt, "Data (evento):");
    const colocacao = linha(txt, "Data (colocação):");
    const stake = linha(txt, "Stake:");
    if (odd !== e.odd) falhas.push(`${b.ref}: odd esperada ${e.odd}, veio "${odd}"`);
    if (!e.status.test(status)) falhas.push(`${b.ref}: status "${status}"`);
    if (!e.tipo.test(tipo)) falhas.push(`${b.ref}: tipo "${tipo}"`);
    if (evento !== e.evento) falhas.push(`${b.ref}: data do evento esperada ${e.evento}, veio "${evento}"`);
    if (colocacao !== e.colocacao) falhas.push(`${b.ref}: colocação esperada ${e.colocacao}, veio "${colocacao}"`);
    if (stake !== "101,00") falhas.push(`${b.ref}: stake esperado 101,00, veio "${stake}"`);
    if (!/Status \(API\): status=/.test(txt)) falhas.push(`${b.ref}: falta o status CRU da API`);
    if (e.riscada && !e.riscada.test(linha(txt, "Odd original (riscada pela casa):"))) {
      falhas.push(`${b.ref}: odd riscada "${linha(txt, "Odd original (riscada pela casa):")}"`);
    }
    if (e.cashout && !e.cashout.test(linha(txt, "Cashout disponível (não executado):"))) {
      falhas.push(`${b.ref}: cashout "${linha(txt, "Cashout disponível (não executado):")}"`);
    }
    if (e.aoVivo && !/AO VIVO \(1T\)/.test(txt)) falhas.push(`${b.ref}: perna ao vivo não foi rotulada`);
    // Aberta nunca pode dizer "retorno": o campo realizado vem igual ao potencial enquanto corre.
    if (/em aberto/.test(status)) {
      if (!/Retorno potencial: R\$ /.test(txt)) falhas.push(`${b.ref}: aberta sem "Retorno potencial"`);
      if (/Status: Ganho/.test(txt)) falhas.push(`${b.ref}: aberta marcada como ganho`);
    }
  }
  for (const ref of Object.keys(ESPERADO)) {
    if (!vistos.has(ref)) falhas.push(`bilhete esperado ausente do lote: ${ref}`);
  }

  // ── escalada de pageSize ────────────────────────────────────────────────────
  // Com `.5` presente (a casa dizendo "tem mais"), o inject tem de pedir DE NOVO com uma
  // página maior — e nunca avançar o número da página, que é o que perde bilhete nesta casa.
  const tamanhos = [];
  const r2 = await rodarInject({
    inject: "pt_inject.js",
    href: "https://pitaco.bet.br/betting/my-bets",
    urlInicial: URL_PAGE,
    optsInicial: { method: "POST", headers: { authorization: "Bearer forjado-do-harness" }, body: new Uint8Array([0, 0, 0, 0, 0]) },
    pedido: "__sharpenupPTCReq",
    ms: 900,
    responder: (url, opts) => {
      if (!/GetUiMyBetsTabContent/.test(url)) return null;
      const aba = abaDoCorpo(opts);
      if (aba !== "finished") return aba === "open" ? abe : null;
      const tam = tamDoCorpo(opts);
      tamanhos.push(tam);
      return tamanhos.length === 1 ? comTemMais(fin) : fin;   // 1ª diz "tem mais", 2ª encerra
    },
  });
  testes++;
  if (tamanhos.length < 2) {
    falhas.push(`escalada: com "tem mais" ligado o inject só pediu ${tamanhos.length} vez(es) a aba finished`);
  } else if (!(tamanhos[1] > tamanhos[0])) {
    falhas.push(`escalada: o 2º pedido não aumentou a página (${tamanhos[0]} → ${tamanhos[1]})`);
  }
  if (r2.ultima && !r2.ultima.fim) falhas.push("escalada: o inject não sinalizou `fim` depois de escalar");
  // Escalar não pode duplicar: o mesmo código voltando duas vezes tem de colidir no mapa.
  if (r2.ultima && (r2.ultima.bilhetes || []).length !== 71) {
    falhas.push(`escalada: esperava 71 bilhetes após reler a aba, vieram ${(r2.ultima.bilhetes || []).length}`);
  }

  return { falhas, testes };
}
