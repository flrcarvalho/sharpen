// Pinnacle — captura por API (`POST /member-service/v2/wager-filter`), s262.
//
// A casa estava sem caso desde que entrou (backlog da s201). O que abriu a sessão foi o
// Gabriel: a Pinnacle mostrava 8 apostas em aberto e o Sharpen trazia 3, sem erro nenhum
// na tela. Duas causas independentes, as duas travadas aqui.
//
// ── 1. A ordem do mapa decepava as abertas ───────────────────────────────────────────
// `pnById` é percorrido em ORDEM DE INSERÇÃO e o replay emite SETTLED antes de OPEN
// (`pn_inject`: `_emitir(true)` → `_emitir(false)`), então as ABERTAS ficam no FIM. O
// `processar()` varria o mapa numa passada só e qualquer freio das liquidadas — janela de
// dias ou stopId — dava `return`, abortando o laço antes de chegar nelas.
//
// E o freio dispara por CONSTRUÇÃO, não por azar. Medido ao vivo na conta do Feca em
// 12/08/2026, lookback de 30 dias:
//   • o replay pede as liquidadas a partir de `2026-07-12 00:00:00` — o dia INTEIRO;
//   • o robô corta em `ctx.cutoff`, que é `agora − 30d` = `2026-07-12 23:59:48`;
//   • `dataEvento` é data-só ("2026-07-12") e `Date.parse` lê como UTC → no fuso BR vira
//     `2026-07-11 21:00`, três horas mais para trás ainda.
// Resultado: a casa devolveu 4 liquidadas do dia da borda nos índices 88-91 de 92, e as
// abertas morriam ali. O dia mais antigo da janela cai fora SEMPRE — se houver bilhete
// liquidado nele, a captura perde todas as abertas. Se não houver, passa inteira: é daí que
// vinha a intermitência ("às vezes vem tudo").
// Mesmo estrago da Betano na s209 — a Pinnacle nunca herdou a guarda.
//
// ── 2. Aposta ANULADA subia como "em aberto" ─────────────────────────────────────────
// `parseBet` fazia `aberta = a[18] !== "SETTLED"`. A Pinnacle usa `CANCELLED` na anulada, e
// ali os dois campos de resultado (6 e 93) são NULOS — o motivo mora no campo 43
// ("REFUNDED"), com o 4 confirmando ("1:Cancelled,0:Cancelled"). A anulada virava um
// pendente que nunca fecha. Caso real na fixture: 3088982702, R$800 em tênis, P/L 0.
//
// ── De-para posicional, reconferido contra o JSON real desta fixture ─────────────────
// Bilhete: 0=P/L · 6=WIN/LOSE · 7=id · 9=confronto · 14=colocação · 15=data do evento ·
// 16=odd(str) · 18=SETTLED/CANCELLED · 22=seleção · 24=linha · 28=liga · 29=stake ·
// 31=esporte · 43=motivo da anulação · 44=pernas · 45=categoria · 46=unidade · 93=WON/LOST.
// Perna: 0=seleção · 3=data · 4=odd · 7=esporte · 9=liga · 19=linha · 28=confronto ·
// 44=unidade · 48=WON/LOST. Todos batem com as linhas salvas aqui.
//
// ── O que esta fixture NÃO cobre (honesto) ───────────────────────────────────────────
//   • As ABERTAS são DERIVADAS de linhas reais (campo 18 → null, 6/93 → null, 0 → 0), que é
//     a forma que a casa usa na não-decidida. A conta usada para levantar a fixture não tinha
//     nenhuma aposta em aberto no dia (a própria Pinnacle respondeu lista vazia nas três
//     variantes de corpo testadas). Quando aparecer uma de verdade, troque as duas linhas.
//   • `PUSHED`/`VOID`/`REFUND` continuam sem amostra — só `CANCELLED`/`REFUNDED` são reais.
//   • HW/HL (handicap de quarto) segue sem amostra, como o STATUS já registrava.
//   • O campo 45 (categoria, "Props de Jogadores") é null em todas as 8 linhas — o de-para
//     dele segue sem prova nesta fixture.
//   • Os IPs do campo 3 foram trocados por "0.0.0.0": é dado do apostador, não entra no git.
import { rodarInject, carregarContent, fixture, linha } from "../sandbox.mjs";

export const casa = "Pinnacle";

const URL = "https://sports2.pinnacle.bet.br/member-service/v2/wager-filter?locale=pt_BR";
// Corpo REAL que a página envia (capturado no `my-bets-full` em 12/08/2026). Repare que a
// própria casa manda `f = t = hoje` com `d = -1` na aba aberta — o inject só o espelha.
const CORPO_PAGINA = "f=2026-08-12 00:00:00&t=2026-08-12 00:00:00&d=-1&s=OPEN&sd=false" +
                     "&type=EVENT&product=SB&timezone=GMT-4&sportId=&leagueId=" +
                     "&timeZoneId=America/Sao_Paulo";

const ABERTAS = ["9000000001", "9000000002"];
const LIQUIDADAS = ["3099722204", "3099205574", "3099033945", "3088982702", "3078338702", "3078337766"];

// Valores conferidos contra a tela da casa (`my-bets-full`) e o JSON da mesma requisição.
const ESPERADO = {
  // Múltipla (Mix Parlay) de 2 pernas de vôlei.
  "3099722204": { data: "09/08/2026", stake: "509,00", odd: "1,661",
                  status: /^Ganho \(WON\) → W · P\/L 336,66$/,
                  contem: ["Tipo: Múltipla (2 seleções)",
                           "• Volleyball · Pan American Cup · EUA -2,5 · EUA v Costa Rica (Games) @ 1,238 · 09/08/2026",
                           "• Volleyball · Pan American Cup · Canadá -2,5 · Canadá v Trinidad e Tobago (Games) @ 1,341 · 09/08/2026"] },
  // Simples W: handicap asiático de -0,75. Odd exibida preservada com 3 casas.
  "3099205574": { data: "08/08/2026", stake: "208,00", odd: "1,662",
                  status: /^Ganho \(WON\) → W · P\/L 137,70$/,
                  contem: ["Esporte (casa): Soccer · Honduras - Liga Nacional",
                           "• Real Espana -0,75 · Real Espana v Genesis (Regular)"] },
  // Simples L: em L o P/L é a stake inteira negativa.
  "3099033945": { data: "08/08/2026", stake: "808,00", odd: "1,724",
                  status: /^Perdeu \(LOST\) → L · P\/L -808,00$/,
                  contem: ["• Club Villa Mitre -0,5 · Club Villa Mitre v Club Cipolletti (Regular)"] },
  // ANULADA: campo 18 CANCELLED, 6 e 93 nulos, motivo no 43. Tem de sair V, nunca "em aberto".
  "3088982702": { data: "22/07/2026", stake: "800,00", odd: "1,571",
                  status: /^REFUNDED → V · P\/L 0,00$/,
                  contem: ["Esporte (casa): Tennis · ATP Estoril - Doubles", "(Sets)"] },
  // As duas do dia da borda: são elas que disparam o freio da janela.
  "3078338702": { data: "03/07/2026", stake: "300,00", odd: "1,704",
                  status: /^Ganho \(WON\) → W · P\/L 211,20$/ },
  "3078337766": { data: "03/07/2026", stake: "200,00", odd: "2,240",
                  status: /^Perdeu \(LOST\) → L · P\/L -200,00$/ },

  // ABERTAS: sem resultado e SEM P/L (o número existe no payload, mas não pode vazar).
  "9000000001": { data: "09/08/2026", stake: "300,00", odd: "1,877",
                  status: /^em aberto \(aguardando resultado/, semPL: true },
  "9000000002": { data: "08/08/2026", stake: "300,00", odd: "1,900",
                  status: /^em aberto \(aguardando resultado/, semPL: true },
};

const codigos = (blocos) => blocos.map((b) => (b.match(/^\[Código:\s*([^\]]+)\]/) || [])[1] || "");

export async function rodar() {
  const falhas = [];
  let testes = 0;

  // ── 1. O inject: de-para posicional + replay das DUAS abas ───────────────────────────
  // A mesma URL serve as duas listas; só o `s` do corpo muda. É por ele que o responder
  // decide o que devolver — e é assim que se prova a ORDEM em que o replay pede.
  const pedidos = [];
  const r = await rodarInject({
    inject: "pn_inject.js",
    href: "https://sports2.pinnacle.bet.br/pt/account/my-bets-full",
    urlInicial: URL, corpoInicial: CORPO_PAGINA, pedido: "__sharpenupPNReq",
    responder: (url, opts) => {
      const s = new URLSearchParams(String((opts && opts.body) || "")).get("s") || "";
      pedidos.push(s);
      return s === "SETTLED" ? fixture("pinnacle.settled.json") : fixture("pinnacle.open.json");
    },
  });

  if (!r.ultima) return { falhas: ["o inject não emitiu mensagem"], testes: 0 };
  if (!r.ultima.hook) falhas.push("o inject não sinalizou `hook`");
  if (!r.ultima.fim) falhas.push("`fim` não veio true — o robô ficaria esperando até o teto");
  if (r.ultima.respostas !== 3) falhas.push(`esperava 3 respostas contadas (página + 2 abas do replay), veio ${r.ultima.respostas}`);
  // A PREMISSA do bug #1: o replay pede SETTLED antes de OPEN. Se um dia inverter, o caso 2
  // abaixo para de exercitar a ordem perigosa — então a ordem é travada aqui, explicitamente.
  if (pedidos[1] !== "SETTLED" || pedidos[2] !== "OPEN")
    falhas.push(`o replay tem de pedir SETTLED e depois OPEN; veio ${pedidos.slice(1).join(" → ")}`);
  testes += 2;

  const bets = r.ultima.bets || [];
  if (bets.length !== 8) falhas.push(`esperava 8 bilhetes (6 liquidados + 2 abertos), vieram ${bets.length}`);

  const porId = new Map(bets.map((b) => [String(b.id), b]));
  for (const id of ABERTAS) {
    if (!porId.get(id)) { falhas.push(`${id}: aberta não chegou do inject`); continue; }
    if (porId.get(id).aberta !== true) falhas.push(`${id}: era para ser ABERTA (campo 18 nulo)`);
  }
  for (const id of LIQUIDADAS) {
    if (!porId.get(id)) { falhas.push(`${id}: liquidada não chegou do inject`); continue; }
    if (porId.get(id).aberta !== false) falhas.push(`${id}: era para ser RESOLVIDA`);
  }
  // O coração do bug #2: CANCELLED é resolvida, e o rótulo do 43 tem de sobreviver.
  const anulada = porId.get("3088982702");
  if (anulada) {
    testes++;
    if (anulada.aberta) falhas.push("3088982702: CANCELLED classificada como ABERTA — vira pendente que nunca fecha");
    if (anulada.resultLabel !== "REFUNDED")
      falhas.push(`3088982702: resultLabel devia ser "REFUNDED" (campo 43), veio "${anulada.resultLabel}"`);
  }

  // ── 2. O robô: liquidada travada NÃO pode decepar as abertas ─────────────────────────
  const { pegar } = carregarContent();
  const robo = pegar("roboPinnaclePassive");
  const pnById = pegar("pnById");
  pegar("pnFimReal = true");   // o replay já terminou: o robô não tem o que esperar

  const tAbertas = ABERTAS.map((id) => porId.get(id)).filter(Boolean);
  const tLiquid = LIQUIDADAS.map((id) => porId.get(id)).filter(Boolean);

  // Ordem de inserção IGUAL à do caso real: o replay entrega as LIQUIDADAS antes das ABERTAS.
  const semear = () => {
    pnById.clear();
    for (const t of tLiquid) pnById.set(String(t.id), t);
    for (const t of tAbertas) pnById.set(String(t.id), t);
  };
  // Janela que deixa as duas de 03/07 FORA e o resto dentro — a borda do caso real.
  const ctxFake = (stopId = "") => ({
    stopId, cutoff: Date.parse("2026-07-10T00:00:00Z"), pisoSanidade: Date.parse("2024-07-10T00:00:00Z"),
    parar: () => false, painel: { contador: { textContent: "" } },
  });

  semear();
  let saiu = codigos(await robo(ctxFake()));
  testes++;
  const faltando = ABERTAS.filter((id) => !saiu.includes(id));
  if (faltando.length)
    falhas.push(`a janela de dias decepou ${faltando.length} de ${ABERTAS.length} ABERTA(s): ${faltando.join(", ")} ` +
                `— liquidada fora da janela não pode abortar a lista das abertas`);
  // ...e a janela continua freando as LIQUIDADAS: a 1ª de 03/07 sai e a 2ª não.
  if (saiu.includes("3078337766"))
    falhas.push("a janela de dias parou de frear as liquidadas: 3078337766 (2ª do dia da borda) não devia sair");
  if (!saiu.includes("3078338702"))
    falhas.push("o bilhete que dispara o freio ainda tem de sair (o corte é DEPOIS de emitir)");

  // stopId apontando para uma LIQUIDADA não pode calar as abertas (era a outra metade da s209).
  semear();
  saiu = codigos(await robo(ctxFake("3099205574")));
  testes++;
  if (ABERTAS.some((id) => !saiu.includes(id)))
    falhas.push(`stopId de bilhete liquidado decepou as abertas: saíram ${saiu.filter((id) => ABERTAS.includes(id)).length} de ${ABERTAS.length}`);

  // ...mas o stopId continua valendo DENTRO da própria lista.
  semear();
  saiu = codigos(await robo(ctxFake("9000000002")));
  testes++;
  if (saiu.includes("9000000002"))
    falhas.push("stopId na lista das abertas devia parar ANTES de emitir o próprio bilhete");
  if (!saiu.includes("9000000001"))
    falhas.push("stopId nas abertas decepou a aberta anterior a ele");

  // ── 3. Os valores de cada bilhete, contra a tela da casa ─────────────────────────────
  const fmt = pegar("formatTicketPN");
  for (const t of tLiquid.concat(tAbertas)) {
    const id = String(t.id);
    const e = ESPERADO[id];
    if (!e) { falhas.push(`${id}: bilhete na fixture sem linha no ESPERADO`); continue; }
    const txt = fmt(t);
    testes++;

    if (!txt.startsWith(`[Código: ${id}]`)) falhas.push(`${id}: marcador [Código:] ausente/errado`);

    const data = linha(txt, "Data:");
    if (data !== e.data) falhas.push(`${id}: data esperada ${e.data}, veio "${data}"`);

    const stake = linha(txt, "Stake:");
    if (stake !== e.stake) falhas.push(`${id}: stake esperada ${e.stake}, veio "${stake}"`);

    // Odd na precisão ORIGINAL da casa: "2.240" continua "2,240", nunca "2,24".
    const odd = linha(txt, "Odd total:");
    if (odd !== e.odd) falhas.push(`${id}: odd esperada ${e.odd}, veio "${odd}"`);

    const status = linha(txt, "Status:");
    if (!e.status.test(status)) falhas.push(`${id}: status "${status}"`);

    // Aberta não pode exibir P/L: o payload traz o número, e vazá-lo viraria resultado.
    if (e.semPL && /P\/L/.test(txt)) falhas.push(`${id}: bilhete ABERTO não pode exibir P/L`);

    for (const trecho of (e.contem || [])) {
      if (!txt.includes(trecho)) falhas.push(`${id}: faltou no bloco → "${trecho}"`);
    }
  }

  return { falhas, testes };
}
