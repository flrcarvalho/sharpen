// Faz1bet (BetConstruct / sportsbook v4) — 3ª casa do MESMO motor, espelho de Tivo/Betfast (s284).
//
// A Faz1bet (`faz1.bet.br`) roda o mesmo motor no mesmo caminho de API
// (`POST /api/game/p/messagetosport` com `{name:"gethistory"}`), então reusa o
// `tv_inject.js` e o `formatTicketTV` sem uma linha duplicada — como a Betfast já fazia.
//
// ── O motor foi PROVADO antes de escrever qualquer linha, não deduzido da aparência ──
//   • `/api/game/p/messagetosport` responde **401** (existe, exige sessão) contra **404**
//     numa rota falsa do mesmo prefixo — é o contraste que prova que a rota existe;
//   • `/sportsbookv4/sbloader.js` responde **200 · application/javascript**: é o loader
//     do sportsbook v4, o mesmo das outras duas;
//   • no payload real logado, os **118 campos** da resposta são um SUBCONJUNTO exato dos
//     campos de `betfast.gethistory.json` + `tivo.gethistory.json` — **zero campo novo**.
//
// ── Os controles do filtro foram rodados ANTES de acreditar em qualquer vazio ─────────
// (a lição do `to` da s211: "0 resultados" pode ser o parâmetro quebrando a consulta)
//     sem filtro          → 9        `to` no futuro      → 9   (controle positivo)
//     from/to em MS       → 9        `to` ontem          → 7   (subconjunto: o filtro age)
//     from/to em SEGUNDOS → **0, com `Error: null`**     → a mesma armadilha silenciosa
//                                                          do motor, confirmada aqui.
//
// ── O que ESTA amostra prova (9 bilhetes reais, conta `ellennfreitas`, 23/08/2026) ────
//   • A TELA TRUNCA A ODD em 7 dos 9 — e de um jeito que induz erro de verdade: dois
//     bilhetes DIFERENTES aparecem como "10.14" no card (`Koef` 10,143 e 10,1493).
//     Ler a odd do card fundiria dois bilhetes distintos no mesmo número.
//   • A COLUNA "DATA" DO CARD É A COLOCAÇÃO, e em **2 dos 9** ela cai num DIA diferente
//     do evento mais recente (colocados 22/08 à noite, jogo em 23/08). É o evento que
//     vai para a 1ª coluna do TSV (`MASTER_OUTPUT §4`) — sem a distinção, esses dois
//     entrariam na planilha no dia errado.
//   • A COLUNA "QUANTIA" DE BILHETE ABERTO É POTENCIAL, não retorno (97,00 × 10,6029 =
//     1.028,48, o que o card mostra com a aposta ainda em jogo). Tratar isso como
//     retorno é a vitória fantasma da VaideBet (s210) — aqui fica travado.
//   • `Count: 9` está longe do `TETO_ALERTA` de 50: a varredura retroativa **não pode**
//     disparar. Conta pequena não paga o custo de furar teto que não foi tocado.
//
// ── O que esta amostra NÃO cobre (a conta não produziu; não é falta de procura) ───────
//   Ganha (W), `Result:1` de perna (anulada), sistema, cashout, bônus e `ItemType:6`
//   (odd oferecida). Os últimos já estão travados pelo caso da Betfast, que exercita o
//   MESMO código — é essa a economia de casa espelho.
//
// ── Como os valores abaixo foram obtidos ─────────────────────────────────────────────
// Print da tela "Minhas apostas" de 23/08/2026 (colunas `Status · Id · Data · Tipo ·
// Valor Apostado · ODDS · Quantia`), conferido bilhete a bilhete contra o JSON. Onde o
// card não mostra a precisão (segundos da colocação, odd inteira), o valor vem do payload
// — que é justamente o que o card arredonda. `tela` guarda a odd QUE A CASA MOSTRA: ela
// nunca é a que usamos, é a prova do truncamento.
import { rodarInject, carregarContent, fixture, linha } from "../sandbox.mjs";

export const casa = "Faz1bet";

const HREF = "https://faz1.bet.br/br/sportsbook/prematch#/mybets";
const API = "https://faz1.bet.br/api/game/p/messagetosport";

const ESPERADO = {
  // As duas ABERTAS. `potencial` é a coluna "Quantia" do card — que aqui é o que a aposta
  // PAGARIA, não o que pagou. DIA DIFERENTE nas duas: colocadas 22/08, jogo em 23/08.
  "301574750": { data: "22/08/2026 21:03:19", evento: "23/08/2026 16:30:00", odd: "10,6029", tela: "10.60", stake: "97,00",  pernas: 3, aberta: true, potencial: "1028,48" },
  "301574640": { data: "22/08/2026 21:01:59", evento: "23/08/2026 15:00:00", odd: "13,8928", tela: "13.89", stake: "97,00",  pernas: 3, aberta: true, potencial: "1347,60" },
  // As sete PERDIDAS (`Status 10 · Result 3`, "Quantia 0.00" no card).
  "301527216": { data: "22/08/2026 14:35:14", evento: "22/08/2026 21:30:00", odd: "10,143",  tela: "10.14", stake: "100,00", pernas: 3, status: /^Perdeu → L/ },
  "301526559": { data: "22/08/2026 14:30:54", evento: "22/08/2026 23:30:00", odd: "11,7157", tela: "11.71", stake: "100,00", pernas: 3, status: /^Perdeu → L/ },
  // Único em que o `Koef` já tem 2 casas: card e payload coincidem legitimamente.
  "301526505": { data: "22/08/2026 14:30:32", evento: "22/08/2026 22:00:00", odd: "13,25",   tela: "13.25", stake: "100,00", pernas: 3, status: /^Perdeu → L/ },
  // O par que a tela funde: este mostra "10.14" igual ao 301527216, com Koef diferente.
  "301479429": { data: "22/08/2026 09:49:37", evento: "22/08/2026 22:00:00", odd: "10,1493", tela: "10.14", stake: "147,00", pernas: 3, status: /^Perdeu → L/ },
  "301468414": { data: "22/08/2026 08:30:26", evento: "22/08/2026 15:45:00", odd: "10,971",  tela: "10.97", stake: "150,00", pernas: 3, status: /^Perdeu → L/ },
  "301468140": { data: "22/08/2026 08:28:45", evento: "22/08/2026 15:30:00", odd: "5,5",     tela: "5.50",  stake: "150,00", pernas: 2, status: /^Perdeu → L/ },
  "301468063": { data: "22/08/2026 08:28:22", evento: "22/08/2026 18:00:00", odd: "12,5235", tela: "12.52", stake: "150,00", pernas: 3, status: /^Perdeu → L/ },
};

export async function rodar() {
  const corpo = fixture("faz1bet.gethistory.json");
  const falhas = [];
  let testes = 0;

  const { ultima } = await rodarInject({
    inject: "tv_inject.js",
    href: HREF,
    urlInicial: API,
    pedido: "__sharpenupTVReq",
    responder: (url) => (url.includes("messagetosport") ? corpo : null),
  });

  if (!ultima) return { falhas: ["o inject não emitiu nenhuma mensagem"], testes: 0 };

  // ── 1. O espelho funciona a partir do host da Faz1bet ─────────────────────────
  testes++;
  if (!ultima.hook) falhas.push("o inject não sinalizou `hook` rodando em faz1.bet.br");
  testes++;
  if (!ultima.fim) falhas.push("o inject não sinalizou `fim` (o robô ficaria esperando o teto)");

  const tickets = ultima.tickets || [];
  testes++;
  if (tickets.length !== 9) falhas.push(`esperava 9 bilhetes na fixture, vieram ${tickets.length}`);

  // ── 2. Conta pequena NÃO acorda a varredura retroativa ────────────────────────
  // `Count: 9` está muito abaixo do `TETO_ALERTA` (50). Se `tetoSuspeito` ligasse aqui,
  // toda captura pagaria uma requisição extra para furar um teto que não foi tocado.
  testes++;
  if (ultima.tetoSuspeito) {
    falhas.push("`tetoSuspeito` ligado com Count:9 — a consulta não encheu; a varredura " +
                "retroativa só existe para quando a lista PARA no teto (50)");
  }

  const fmt = carregarContent().pegar("formatTicketTV");
  const porId = new Map(tickets.map((t) => [String(t.id), t]));

  // ── 3. Os 9 bilhetes conferidos contra o card ─────────────────────────────────
  for (const [id, e] of Object.entries(ESPERADO)) {
    const t = porId.get(id);
    if (!t) { falhas.push(`${id}: não veio na captura`); continue; }
    const txt = fmt(t);
    testes++;

    if (!txt.startsWith(`[Código: ${id}]`)) falhas.push(`${id}: marcador [Código:] ausente/errado`);

    const evento = linha(txt, "Data (evento mais recente):");
    if (evento !== e.evento) falhas.push(`${id}: data do EVENTO esperada ${e.evento}, veio "${evento}" (é ela que vai para a coluna Data do TSV)`);

    const data = linha(txt, "Data (colocação):");
    if (data !== e.data) falhas.push(`${id}: colocação esperada ${e.data}, veio "${data}"`);

    const stake = linha(txt, "Stake:");
    if (stake !== `R$ ${e.stake}`) falhas.push(`${id}: stake esperada R$ ${e.stake}, veio "${stake}"`);

    const odd = linha(txt, "Odd:");
    if (odd !== e.odd) falhas.push(`${id}: odd esperada ${e.odd}, veio "${odd}" (a tela mostra ${e.tela} — trunca; vale o Koef inteiro)`);

    // O erro que ESTA casa induz: emitir a odd do card. Em 7 dos 9 os dois valores diferem,
    // e em dois bilhetes distintos o card mostra o MESMO "10.14".
    if (e.tela.replace(".", ",") !== e.odd && odd === e.tela.replace(".", ",")) {
      falhas.push(`${id}: emitiu a odd TRUNCADA do card (${e.tela}) em vez do Koef ${e.odd}`);
    }

    const tipo = linha(txt, "Tipo:");
    const esperaTipo = e.pernas >= 2 ? `Múltipla (${e.pernas} seleções)` : "Simples";
    if (tipo !== esperaTipo) falhas.push(`${id}: tipo esperado "${esperaTipo}", veio "${tipo}"`);

    const status = linha(txt, "Status:");
    if (e.aberta) {
      // ── 4. Aberta não pode virar resultado, e a "Quantia" dela é POTENCIAL ─────
      testes++;
      if (!/em aberto/.test(status) || !/NÃO liquidar/.test(status)) {
        falhas.push(`${id}: bilhete em aberto saiu como "${status}" — tem de avisar a IA para NÃO liquidar`);
      }
      if (/Ganho → W|Perdeu → L/.test(status)) {
        falhas.push(`${id}: bilhete AINDA EM JOGO saiu liquidado ("${status}") — vitória fantasma`);
      }
      testes++;
      const pot = linha(txt, "Retorno potencial:");
      if (pot !== `R$ ${e.potencial}`) {
        falhas.push(`${id}: retorno potencial esperado R$ ${e.potencial} (a coluna "Quantia" do card, que aqui é o que a aposta PAGARIA), veio "${pot}"`);
      }
      if (/^Retorno: /m.test(txt)) {
        falhas.push(`${id}: o potencial de bilhete aberto saiu rotulado como "Retorno" — é o que a casa PAGARIA, não o que pagou`);
      }
    } else if (!e.status.test(status)) {
      falhas.push(`${id}: status "${status}"`);
    }
  }

  // ── 5. O bloco da Faz1bet é IDÊNTICO ao da Tivo e ao da Betfast ───────────────
  // É isto que "espelho" quer dizer: a MESMA fixture, rodada pelos TRÊS hosts, tem de
  // render bloco byte a byte igual. Se alguém amarrar o inject a um domínio, ou ramificar
  // o formatador por casa, este teste fica vermelho na hora.
  for (const outro of [
    { nome: "tivo",    href: "https://tivo.bet.br/br/sportsbook/prematch#/mybets", api: "https://tivo.bet.br/api/game/p/messagetosport" },
    { nome: "betfast", href: "https://www.betfast.bet.br/br#/mybets",              api: "https://www.betfast.bet.br/api/game/p/messagetosport" },
  ]) {
    const r = await rodarInject({
      inject: "tv_inject.js",
      href: outro.href,
      urlInicial: outro.api,
      pedido: "__sharpenupTVReq",
      responder: (url) => (url.includes("messagetosport") ? corpo : null),
    });
    const m = new Map((((r.ultima || {}).tickets) || []).map((t) => [String(t.id), t]));
    testes++;
    if (m.size !== porId.size) {
      falhas.push(`espelho: host ${outro.nome} capturou ${m.size} e faz1.bet.br ${porId.size} — a captura não pode depender do domínio`);
      continue;
    }
    const diferentes = [];
    for (const [id, t] of porId) {
      const o = m.get(id);
      if (!o || fmt(o) !== fmt(t)) diferentes.push(id);
    }
    if (diferentes.length) {
      falhas.push(`espelho: ${diferentes.length} bloco(s) diferem entre faz1.bet.br e ${outro.nome} (${diferentes.slice(0, 3).join(", ")}…)`);
    }
  }

  return { falhas, testes };
}
