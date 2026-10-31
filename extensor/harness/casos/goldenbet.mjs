// GoldenBet (goldenbet.com) — 6ª casa BetConstruct, espelho da MyStake (s435).
//
// ── O motor foi PROVADO no tráfego real, logado (30/10/2026) ─────────────────────────────
//   • `POST goldenbet.com/api/game/p/messagetosport` com `{name:"gethistory"}` (o corpo das
//     irmãs), disparado por `scripts/common/helpers.js`; resposta `{Error, Tickets, Count}`;
//   • `Company: 73` (MyStake 28 · Tivo 291 · Betfast 99 · Faz1bet 223);
//   • o sportsbook mora em `/eng/sportsbook/prematch` (o `/br/sportsbook` do link dá 404) e o
//     "My Bets" é um painel do cupom, sem rota própria;
//   • `from`/`to` em ms respondem; em SEGUNDOS dão `Count: 0` com `Error: null` (a armadilha
//     das irmãs, re-medida aqui);
//   • a página da conta (site em ENG) pede com `language: 0`, e o inject repassa o idioma da
//     página: mercado, região e esporte chegam em INGLÊS ("Point handicap", "International").
//     A fixture é a resposta com `language: 0`, a que a captura vai receber de verdade.
//
// ── O que SÓ esta casa trouxe: a conta é em DÓLAR ────────────────────────────────────────
//   `CurrencySTR: "USD"` nos 15 de 15, saldo "104.88 USD" no topo, "30.00 USD" em cada card.
//   As quatro irmãs medidas são em real, e o `formatTicketTV` escrevia `Stake: R$` e
//   `Retorno potencial: R$` FIXOS — rótulo errado na frente da IA — e não emitia o
//   `Carimbo de colocação`, que decide o DIA DA COTAÇÃO no servidor (sem ele, aberta com
//   jogo amanhã fica sem cotação: DEX Sport, 10 de 12). Convenção do `_dinJB` (s391): real
//   sai como sempre ("R$ 30,00"); outra moeda sai com o código depois ("30,00 USD").
//   O §4 trava que as casas em REAL ficam byte a byte iguais (o hash do `bloco_visto`).
//
// ── Como os valores abaixo foram obtidos ─────────────────────────────────────────────────
// Painel "My Bets" de 30/10/2026 (colunas `ID · Date · Amount · Possible Win · Type · Status`)
// e o detalhe aberto do 309877580 (badminton, "Point handicap", `Pick: 1 (11.5)`, odd 1.95).
// A data do card é a colocação em horário de Brasília (16:52:06 = `ActionTime` 19:52:06Z). O
// card não mostra a odd na lista; o detalhe mostra "Total Odds" arredondado, e vale o `Koef`.
//
// ── O que esta amostra NÃO cobre ─────────────────────────────────────────────────────────
//   Ganha (W), freebet (a conta ganhou 6 USD de freebet no mesmo dia, ainda não usada),
//   cashout, sistema, bônus de odd. Esses caminhos são o mesmo código das irmãs e estão
//   travados pelos casos da MyStake, Betfast e Faz1bet — em REAL. W em dólar fica para a
//   2ª captura. Os centavos do "Retorno potencial" de 309982775 (355,815) caem no
//   meio-centavo do float e o `_brl` arredonda para baixo (355,81), enquanto o card mostra
//   355.82: nesse só o rótulo da moeda é conferido (valor informativo, não entra em P/L).
import { rodarInject, carregarContent, fixture, linha } from "../sandbox.mjs";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

export const casa = "GoldenBet";

const HOSTS = {
  goldenbet: { href: "https://goldenbet.com/eng/sportsbook/prematch", api: "https://goldenbet.com/api/game/p/messagetosport" },
  mystake:   { href: "https://mystake.bet/br/sportsbook/mybets",      api: "https://mystake.bet/api/game/p/messagetosport" },
};

async function capturar(corpo, h) {
  return rodarInject({
    inject: "tv_inject.js",
    href: h.href,
    urlInicial: h.api,
    pedido: "__sharpenupTVReq",
    responder: (url) => (url.includes("messagetosport") ? corpo : null),
  });
}

// `A` = aberta ("Current" no card, botão Cashout) · `L` = "LOST". `pot` só nas abertas,
// lido do "Possible Win" do card; `null` = meio-centavo arredondado para baixo (ver cabeçalho).
const ESPERADO = {
  "309985237": { r: "A", data: "30/10/2026 16:52:06", evento: "31/10/2026 14:45:00", odd: "16,5182", stake: "30,00", pot: "495,55" },
  "309984491": { r: "A", data: "30/10/2026 16:47:47", evento: "31/10/2026 17:00:00", odd: "17,5027", stake: "30,00", pot: "525,08" },
  "309984144": { r: "L", data: "30/10/2026 16:45:55", evento: "31/10/2026 10:45:00", odd: "16,9215", stake: "30,00" },
  "309983784": { r: "A", data: "30/10/2026 16:44:07", evento: "31/10/2026 14:30:00", odd: "14,3325", stake: "30,00", pot: "429,98" },
  "309983329": { r: "A", data: "30/10/2026 16:41:57", evento: "31/10/2026 12:00:00", odd: "29,601",  stake: "30,00", pot: "888,03" },
  "309983084": { r: "A", data: "30/10/2026 16:40:37", evento: "31/10/2026 12:00:00", odd: "29,106",  stake: "30,00", pot: "873,18" },
  "309982775": { r: "A", data: "30/10/2026 16:39:09", evento: "31/10/2026 09:30:00", odd: "11,8605", stake: "30,00", pot: null },
  "309981356": { r: "L", data: "30/10/2026 16:32:38", evento: "30/10/2026 17:05:00", odd: "17,1",    stake: "30,00" },
  "309900975": { r: "L", data: "30/10/2026 07:16:54", evento: "30/10/2026 19:00:00", odd: "29,3554", stake: "30,00" },
  "309900809": { r: "L", data: "30/10/2026 07:14:39", evento: "30/10/2026 16:45:00", odd: "12,6766", stake: "30,00" },
  "309900482": { r: "L", data: "30/10/2026 07:10:51", evento: "30/10/2026 21:15:00", odd: "15,8794", stake: "30,00" },
  "309877580": { r: "L", data: "29/10/2026 23:48:31", evento: "30/10/2026 13:25:00", odd: "1,95",    stake: "75,00", simples: true },
  "309877231": { r: "L", data: "29/10/2026 23:36:38", evento: "31/10/2026 14:30:00", odd: "10,5057", stake: "30,00" },
  "309874706": { r: "A", data: "29/10/2026 22:31:20", evento: "30/10/2026 20:30:00", odd: "11,9011", stake: "30,00", pot: "357,03" },
  "309873189": { r: "L", data: "29/10/2026 21:58:33", evento: "31/10/2026 16:30:00", odd: "12,8142", stake: "30,00" },
};

// "dd/mm/aaaa hh:mm:ss" → "aaaammddhhmmss", o formato que o servidor lê (`carimbos_do_texto`).
const carimbo = (s) => s.replace(/^(\d\d)\/(\d\d)\/(\d{4}) (\d\d):(\d\d):(\d\d)$/, "$3$2$1$4$5$6");

export async function rodar() {
  const corpo = fixture("goldenbet.gethistory.json");
  const falhas = [];
  let testes = 0;

  // ── 0. A fixture é dado real de cliente: sem o login da conta ────────────────────────
  testes++;
  const cru = readFileSync(fileURLToPath(new URL("../fixtures/goldenbet.gethistory.json", import.meta.url)), "utf8");
  if (/"Player":\{[^}]*"Name":"(?!REDACTED")/.test(cru)) {
    falhas.push("a fixture da GoldenBet carrega o login da conta (Player.Name) — apague antes de versionar");
  }

  const { ultima } = await capturar(corpo, HOSTS.goldenbet);
  if (!ultima) return { falhas: ["o inject não emitiu nenhuma mensagem em goldenbet.com"], testes };

  // ── 1. O inject roda a partir do host da GoldenBet ───────────────────────────────────
  testes++;
  if (!ultima.hook) falhas.push("o inject não sinalizou `hook` rodando em goldenbet.com");
  testes++;
  if (!ultima.fim) falhas.push("o inject não sinalizou `fim` (o robô ficaria esperando o teto)");
  const tickets = ultima.tickets || [];
  testes++;
  if (tickets.length !== 15) falhas.push(`esperava 15 bilhetes na fixture, vieram ${tickets.length}`);
  testes++;
  if (ultima.tetoSuspeito) falhas.push("`tetoSuspeito` ligado com Count:15 — a consulta não encheu");

  const fmt = carregarContent().pegar("formatTicketTV");
  const porId = new Map(tickets.map((t) => [String(t.id), t]));

  // ── 2. Os 15 bilhetes conferidos contra o card ───────────────────────────────────────
  for (const [id, e] of Object.entries(ESPERADO)) {
    const t = porId.get(id);
    if (!t) { falhas.push(`${id}: não veio na captura`); continue; }
    const txt = fmt(t);
    testes++;

    if (!txt.startsWith(`[Código: ${id}]`)) falhas.push(`${id}: marcador [Código:] ausente/errado`);

    const evento = linha(txt, "Data (evento mais recente):");
    if (evento !== e.evento) falhas.push(`${id}: data do EVENTO esperada ${e.evento}, veio "${evento}"`);
    const data = linha(txt, "Data (colocação):");
    if (data !== e.data) falhas.push(`${id}: colocação esperada ${e.data} (a do card), veio "${data}"`);

    const odd = linha(txt, "Odd:");
    if (odd !== e.odd) falhas.push(`${id}: odd esperada ${e.odd} (o Koef inteiro), veio "${odd}"`);

    const tipo = linha(txt, "Tipo:");
    const tipoEsp = e.simples ? "Simples" : "Múltipla (3 seleções)";
    if (tipo !== tipoEsp) falhas.push(`${id}: tipo esperado "${tipoEsp}", veio "${tipo}"`);

    const status = linha(txt, "Status:") || "";
    if (e.r === "L" && !/^Perdeu → L/.test(status)) falhas.push(`${id}: card diz LOST, status "${status}"`);
    if (e.r === "A" && !/^em aberto \(aguardando resultado — NÃO liquidar; sem resultado\)/.test(status)) {
      falhas.push(`${id}: card diz Current, status "${status}"`);
    }

    // ── 3. Dinheiro em DÓLAR, rotulado como o card ─────────────────────────────────────
    testes++;
    const stake = linha(txt, "Stake:");
    if (stake !== `${e.stake} USD`) falhas.push(`${id}: stake esperada "${e.stake} USD" (o card diz ${e.stake.replace(",", ".")} USD), veio "${stake}"`);
    if (linha(txt, "Moeda:") !== "USD") falhas.push(`${id}: linha "Moeda: USD" ausente — o servidor não saberia que a conta é em dólar`);
    if (/R\$/.test(txt)) falhas.push(`${id}: "R$" num bilhete em dólar`);

    if (e.r === "A") {
      const pot = linha(txt, "Retorno potencial:") || "";
      if (e.pot ? pot !== `${e.pot} USD` : !/^\d+,\d\d USD$/.test(pot)) {
        falhas.push(`${id}: retorno potencial esperado "${e.pot || "…"} USD", veio "${pot}"`);
      }
    }

    // ── 3b. O carimbo de colocação, que decide o dia da cotação ────────────────────────
    testes++;
    const cb = linha(txt, "Carimbo de colocação:");
    if (cb !== carimbo(e.data)) {
      falhas.push(`${id}: carimbo de colocação esperado ${carimbo(e.data)}, veio "${cb}" ` +
                  `(sem ele o servidor cota pela data do EVENTO, e aberta com jogo amanhã fica sem cotação)`);
    }
  }

  // ── 3c. A perna da simples, conferida no detalhe aberto ──────────────────────────────
  testes++;
  {
    const t = porId.get("309877580");
    const txt = t ? fmt(t) : "";
    if (!/^- .*: 1 \(linha 11,5\) \[perdeu\]$/m.test(txt)) falhas.push(`309877580: perna esperada "Pick: 1 (11.5)" perdida, veio:\n${txt}`);
    if (!/Esporte: Badminton/.test(txt)) falhas.push("309877580: esporte esperado Badminton");
  }

  // ── 4. Casa em REAL fica byte a byte igual: nem `Moeda:` nem carimbo, `R$` na frente ──
  // É o que mantém o hash do `bloco_visto` das irmãs e impede a recaptura da base inteira.
  testes++;
  {
    const ms = await capturar(fixture("mystake.gethistory.json"), HOSTS.mystake);
    const t = (((ms.ultima || {}).tickets) || []).find((x) => String(x.id) === "306558258");
    const txt = t ? fmt(t) : "";
    if (linha(txt, "Stake:") !== "R$ 100,00") falhas.push(`MyStake (real): stake mudou de forma — veio "${linha(txt, "Stake:")}"`);
    if (/^Moeda:|^Carimbo de colocação:/m.test(txt)) falhas.push("MyStake (real): ganhou linha de moeda/carimbo — o bloco das casas em real mudou");
  }

  // ── 5. A moeda vem do BILHETE, não do host ───────────────────────────────────────────
  // A mesma fixture servida em mystake.bet tem de sair byte a byte igual: se alguém amarrar
  // a moeda ao domínio, ou ramificar o formatador por casa, fica vermelho.
  const r = await capturar(corpo, HOSTS.mystake);
  const m = new Map((((r.ultima || {}).tickets) || []).map((t) => [String(t.id), t]));
  testes++;
  const diferentes = [...porId].filter(([id, t]) => !m.get(id) || fmt(m.get(id)) !== fmt(t)).map(([id]) => id);
  if (m.size !== porId.size || diferentes.length) {
    falhas.push(`espelho: ${diferentes.length} bloco(s) diferem entre goldenbet.com e mystake.bet (${diferentes.slice(0, 3).join(", ")})`);
  }

  return { falhas, testes };
}
