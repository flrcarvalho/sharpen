// Betano — captura por API (`GET /myaccount/api/ma/bet/bet-history-v3?settled=true|false`), s209.
//
// Duas metades:
//   A) ROTEAMENTO POR ABA — a armadilha que abriu a sessão.
//   B) VALORES — cada campo conferido contra o que a PRÓPRIA CASA renderiza (print do
//      "Histórico → Apostas" + o texto que o robô exportou ao vivo em 26/07/2026).
//
// ── A armadilha do roteamento ────────────────────────────────────────────────────────
// `bnById` é acumulador da SESSÃO DA PÁGINA. A Betano é SPA: trocar "Liquidada" ↔ "Em aberto"
// NÃO recarrega, então o hook guarda as duas listas ao mesmo tempo. Até a s209 o `processar()`
// varria o mapa inteiro, e rodar na aba "Em aberto" depois de ter passado pela "Liquidada"
// exportava as duas juntas (caso real: 25 bilhetes = as 5 abertas corretas + 20 liquidadas que
// sobraram em memória). Dois estragos:
//   • token à toa — o pré-dedup do `/extrair` só descarta o que já está RESOLVIDO no banco;
//   • perda SILENCIOSA das abertas — o mapa é percorrido em ordem de inserção; com o campo
//     "parar no ID" preenchido com um bilhete LIQUIDADO, o `travado` disparava antes de chegar
//     nas abertas e elas não saíam, sem erro na tela. Com a guarda desligada, o teste 3 abaixo
//     acusa "0 de 3 abertas" — a perda reproduzida, não teorizada.
//
// ── Fim autoritativo da paginação, provado nos dois sentidos ─────────────────────────
//   • `betano.open.json` NÃO tem `LastId` → é a última página daquela lista → `fimOpen` = true.
//   • `betano.settled.json` TEM `LastId: 20707886166` → ainda há página → `fimSettled` = false.
// Um sinal nunca vaza para a outra lista: é por isso que o robô escolhe o fim da aba ATIVA.
//
// ── Livro de armadilhas confirmado nesta fixture ─────────────────────────────────────
//   • `Accumulator: "{number}-fold"` é PLACEHOLDER CRU da API (bilhete 20713079396, `Type`
//     "Accumulator5"). Cair nele imprimiria "{number}-fold" como tipo — o código detecta a
//     chave `{` e usa a contagem de pernas ("5-seleções", que é o que a tela mostra).
//   • ABERTA NÃO TEM `Return` — só `PossibleWinnings`. O `formatTicketBN` tenta rotular
//     "Retorno potencial", mas o campo não existe, então a linha simplesmente não sai. É o
//     comportamento SEGURO (nenhum número de retorno chega à IA num bilhete sem resultado) e
//     é o que o robô exportou ao vivo. Travado aqui para não "consertarem" isso sem pensar.
//   • BOOST em dois sabores: `OddsBeforeEnhancement` na seleção (20707888096, 3.50 → 4.20) JÁ
//     está dentro do `Return` (445,20 ÷ 106 = 4,20 exato) → nada a fazer. Já o `BonusOffer`
//     (20712642016, "Criar Aposta Turbinada +25%", `Winnings: 149.175`) fica FORA do `Return`
//     (902,70 = 306 × 2,95) e é **dinheiro real**: medido na conta do Diogo em 11/09/2026, o
//     bilhete 21048480456 fechou com R$165 a MAIS do que o Sharpen tinha planilhado, exatamente
//     o `Winnings`. Desde então o retorno do bloco é `Return + Winnings` e a odd de W sai de lá
//     (§6) — era a decisão que faltava, e a fixture já tinha o caso esperando.
//   • Em L a odd é a EXIBIDA, nunca derivada do `Return` (que é 0): 20707886166 é L com boost
//     e vale 2,75, não 0.
//   • `VoidNotStartingPlayersSelected` + `PlayerSubstitutions` (20708999896) é CONDIÇÃO, não
//     resultado — o bilhete perdeu normalmente (`CASA_BETANO §12`).
//
// ── O que esta fixture NÃO cobre (honesto) ───────────────────────────────────────────
//   • Fuso virando o dia: nenhum `PlacedAt` do lote cai entre 00:00 e 02:59 UTC, então o
//     recuo de 3h nunca troca a data aqui. Cashout (`Status 6`) e anulado (`Status 0`) também
//     não têm amostra. Quando aparecerem, salve o payload e some uma linha ao ESPERADO.
//   • O W onde `Retorno ÷ Stake` DIVERGE da odd exibida é o 20712642016, e só desde que o
//     turbo entrou na conta: 3,4375 contra os 2,95 do card. Os outros três W (4,20 · 2,95 ·
//     2,10) batem nos dois cálculos, e foi por isso que o caso confere o RÓTULO
//     "(= Retorno ÷ Stake)" em separado — quebrando o `oddW` de propósito o valor continuava
//     certo e só o rótulo sumia. Hoje a mesma mutação também erra o NÚMERO, no turbinado.
//   • ABERTA com `BonusOffer` continua sem amostra: o `Winnings` de um bilhete vivo é
//     potencial, e o formatador imprime o `+N%` sem valor nenhum (`semRetorno` cobre isso
//     de um lado; do outro, nada prova que a API preenche o campo antes de liquidar).
//   • CASHOUT com `BonusOffer` também não tem amostra. O código soma o turbo em qualquer
//     liquidado com `Winnings > 0` — se a casa algum dia pagar turbo num saque, o dinheiro
//     entra; se não pagar, o campo não vem e nada muda.
import { rodarInject, carregarContent, fixture, linha } from "../sandbox.mjs";

export const casa = "Betano";

const URL_ABERTAS = "https://www.betano.bet.br/myaccount/api/ma/bet/bet-history-v3?settled=false&page=1";
const URL_LIQUID  = "https://www.betano.bet.br/myaccount/api/ma/bet/bet-history-v3?settled=true&page=1";
const URL_LIQUID2 = "https://www.betano.bet.br/myaccount/api/ma/bet/bet-history-v3?settled=true&page=2&lastId=20707886166";

// Valores conferidos contra a tela da casa (print) e o texto exportado ao vivo em 26/07/2026.
// `odd` é a 1ª palavra da linha "Odd total:" · `status` casa o início da linha "Status:".
const ESPERADO = {
  // ABERTAS — sem resultado e SEM linha de retorno (a API não manda `Return` na aba aberta).
  "20716925556": { data: "26/07/2026", tipo: "Simples", stake: "800,00", odd: "1,8",
                   status: /^em aberto \(aguardando resultado/, semRetorno: true },
  "20711454676": { data: "26/07/2026", tipo: "Simples", stake: "400,00", odd: "1,62",
                   status: /^em aberto \(aguardando resultado/, semRetorno: true },
  // Dupla com uma perna "Criar Aposta" (ComboLegType 1, 2 sub-seleções) — odd combinada 1,6568.
  "20708244036": { data: "25/07/2026", tipo: "Dupla (Criar Aposta)", stake: "800,00", odd: "1,6568",
                   status: /^em aberto \(aguardando resultado/, semRetorno: true,
                   contem: ["[Criar Aposta @ 1,52] Digvijay Pratap Singh - Sergey Betov:",
                            "Francesco Forti @ 1,09"] },

  // LIQUIDADAS
  // `Accumulator` vem "{number}-fold" (placeholder) → tipo pela contagem de pernas.
  "20713079396": { data: "26/07/2026", tipo: "5-seleções", stake: "300,00", odd: "14,4677",
                   status: /^Perdido → L · Retorno R\$0,00$/,
                   contem: ["Futebol Americano · Montreal Alouettes - Hamilton Tiger-Cats"] },
  // W TURBINADO — o único bilhete em que a odd derivada diverge da exibida. O `Return`
  // (902,70 = 306 × 2,95) é PRÉ-boost e o `BonusOffer.Winnings` (149,175 = 25% do lucro de
  // 596,70) é pago por fora: retorno 1.051,88 → odd 3,4375, que é 1 + 1,95 × 1,25 exato.
  // Ler o `Return` sozinho aqui subestima o bilhete em R$149,18 de P/L.
  "20712642016": { data: "26/07/2026", tipo: "Simples (Criar Aposta)", stake: "306,00",
                   odd: "3,4375", oddDerivada: true, boost: true,
                   status: /^Ganho → W · Retorno R\$1051,88 \(pago R\$902,70 \+ turbo R\$149,18\)$/,
                   contem: ["[Criar Aposta @ 2,95] Bahia - Corinthians:", "Mais de 4.5 · Total de Cartões",
                            "Boost: Criar Aposta Turbinada +25% · pago pela casa R$902,70 + turbo R$149,18 = retorno R$1051,88"] },
  // L com jogador substituível: condição, não resultado. Odd = a exibida.
  "20708999896": { data: "25/07/2026", tipo: "Simples", stake: "100,00", odd: "5,1",
                   status: /^Perdido → L · Retorno R\$0,00$/ },
  // W com odd turbinada NA SELEÇÃO: 445,20 ÷ 106 = 4,20 == a odd boostada. Marca "(sem boost 3,50)".
  "20707888096": { data: "25/07/2026", tipo: "Simples", stake: "106,00", odd: "4,2", oddDerivada: true,
                   status: /^Ganho → W · Retorno R\$445,20$/, contem: ["(sem boost 3,50)"] },
  // L com boost: vale a odd EXIBIDA (2,75), jamais Retorno÷Stake (= 0).
  "20707886166": { data: "25/07/2026", tipo: "Simples", stake: "156,00", odd: "2,75",
                   status: /^Perdido → L · Retorno R\$0,00$/, contem: ["(sem boost 2,50)"] },
  // Outright de F1: `Game` é o GP inteiro, sem confronto A - B.
  "20706361776": { data: "25/07/2026", tipo: "Simples", stake: "201,00", odd: "2,1", oddDerivada: true,
                   status: /^Ganho → W · Retorno R\$422,10$/,
                   contem: ["Fórmula 1 · Grande Prêmio da Hungria · Vencedor do grupo 3"] },
};

const ABERTAS = ["20716925556", "20711454676", "20708244036"];
const LIQUIDADAS = ["20713079396", "20712642016", "20708999896", "20707888096", "20707886166"];

const codigos = (blocos) => blocos.map((b) => (b.match(/^\[Código:\s*([^\]]+)\]/) || [])[1] || "");

export async function rodar() {
  const falhas = [];
  let testes = 0;

  // ── 1. O inject: marca `__aberta` pela URL e sinaliza o fim POR LISTA ────────────────
  const abertas = await rodarInject({
    inject: "bn_inject.js", href: "https://www.betano.bet.br/myaccount/bethistory/open",
    urlInicial: URL_ABERTAS, pedido: "__sharpenupBNReq",
    responder: (url) => (url.includes("settled=false") ? fixture("betano.open.json") : null),
  });
  const liquidadas = await rodarInject({
    inject: "bn_inject.js", href: "https://www.betano.bet.br/myaccount/bethistory/settled",
    urlInicial: URL_LIQUID, pedido: "__sharpenupBNReq",
    responder: (url) => (url.includes("settled=true") ? fixture("betano.settled.json") : null),
  });
  const pag2 = await rodarInject({
    inject: "bn_inject.js", href: "https://www.betano.bet.br/myaccount/bethistory/settled",
    urlInicial: URL_LIQUID2, pedido: "__sharpenupBNReq",
    responder: () => fixture("betano.settled2.json"),
  });

  if (!abertas.ultima || !liquidadas.ultima) return { falhas: ["o inject não emitiu mensagem"], testes: 0 };
  if (!abertas.ultima.hook) falhas.push("abertas: o inject não sinalizou `hook`");
  if (abertas.ultima.respostas !== 1) falhas.push(`abertas: esperava 1 resposta contada, veio ${abertas.ultima.respostas}`);
  // Sem `LastId` = última página daquela lista → fim autoritativo das ABERTAS, e só delas.
  if (!abertas.ultima.fimOpen) falhas.push("abertas: sem `LastId` na resposta, `fimOpen` tinha de ser true (o robô ficaria rolando até o teto)");
  if (abertas.ultima.fimSettled) falhas.push("abertas: `fimSettled` vazou — o fim de uma lista não pode encerrar a outra");
  // COM `LastId` = ainda há página → NÃO é fim (parar aqui perderia o resto do histórico).
  if (liquidadas.ultima.fimSettled) falhas.push("liquidadas: veio `LastId`, então `fimSettled` tinha de ser false");
  if (pag2.ultima.fimSettled) falhas.push("liquidadas pág.2: veio `LastId`, então `fimSettled` tinha de ser false");
  testes += 2;

  const tAbertas = abertas.ultima.bets || [];
  const tLiquid = (liquidadas.ultima.bets || []).concat(pag2.ultima.bets || []);
  if (tAbertas.length !== 3) falhas.push(`esperava 3 abertas na fixture, vieram ${tAbertas.length}`);
  if (tLiquid.length !== 6) falhas.push(`esperava 6 liquidadas na fixture, vieram ${tLiquid.length}`);
  if (tAbertas.some((t) => t.__aberta !== true)) falhas.push("aberta sem a marca `__aberta:true` (settled=false)");
  if (tLiquid.some((t) => t.__aberta !== false)) falhas.push("liquidada marcada como aberta (o teste de `settled=true` na URL falhou)");

  // ── 2. O robô: cada aba exporta só a SUA lista ───────────────────────────────────────
  const { pegar } = carregarContent();
  const robo = pegar("roboBetanoPassive");
  const bnById = pegar("bnById");
  const loc = pegar("location");
  pegar("bnFimOpen = true");      // as duas listas já chegaram ao fim: o robô não tem o que rolar
  pegar("bnFimSettled = true");

  // Ordem de inserção IGUAL à do caso real: a Liquidada foi visitada ANTES da Em aberto.
  const semear = () => {
    bnById.clear();
    for (const t of tLiquid) bnById.set(String(t.BetId), t);
    for (const t of tAbertas) bnById.set(String(t.BetId), t);
  };
  const ctxFake = (stopId = "") => ({
    stopId, cutoff: Date.parse("2026-06-26T00:00:00Z"), pisoSanidade: Date.parse("2024-06-26T00:00:00Z"),
    parar: () => false, painel: { contador: { textContent: "" } },
  });

  semear(); loc.pathname = "/myaccount/bethistory/open";
  let saiu = codigos(await robo(ctxFake()));
  testes++;
  const vazouL = saiu.filter((id) => LIQUIDADAS.includes(id));
  if (vazouL.length) falhas.push(`aba Em aberto vazou ${vazouL.length} LIQUIDADA(s): ${vazouL.join(", ")}`);
  if (saiu.length !== ABERTAS.length || ABERTAS.some((id) => !saiu.includes(id)))
    falhas.push(`aba Em aberto: esperava as ${ABERTAS.length} abertas, saíram ${saiu.length} (${saiu.join(", ")})`);

  semear(); loc.pathname = "/myaccount/bethistory/settled";
  saiu = codigos(await robo(ctxFake()));
  testes++;
  const vazouA = saiu.filter((id) => ABERTAS.includes(id));
  if (vazouA.length) falhas.push(`aba Liquidada vazou ${vazouA.length} ABERTA(s): ${vazouA.join(", ")}`);
  if (saiu.length !== LIQUIDADAS.length + 1) falhas.push(`aba Liquidada: esperava ${LIQUIDADAS.length + 1} liquidadas, saíram ${saiu.length}`);

  // A perda silenciosa: "parar no ID" apontando para um LIQUIDADO não pode decepar as abertas.
  semear(); loc.pathname = "/myaccount/bethistory/open";
  saiu = codigos(await robo(ctxFake(LIQUIDADAS[0])));
  testes++;
  if (saiu.length !== ABERTAS.length)
    falhas.push(`stopId de bilhete liquidado decepou a aba Em aberto: saíram ${saiu.length} de ${ABERTAS.length}`);

  // ...mas o stopId continua valendo DENTRO da própria aba (copiar do último extraído pra cima).
  semear(); loc.pathname = "/myaccount/bethistory/open";
  saiu = codigos(await robo(ctxFake(ABERTAS[2])));
  testes++;
  if (saiu.length !== 2 || saiu[0] !== ABERTAS[0] || saiu[1] !== ABERTAS[1])
    falhas.push(`stopId na própria aba deveria parar nos 2 primeiros, saíram ${saiu.length} (${saiu.join(", ")})`);

  // ── 3. Os valores de cada bilhete, contra a tela da casa ─────────────────────────────
  const fmt = pegar("formatTicketBN");
  for (const t of tAbertas.concat(tLiquid)) {
    const id = String(t.BetId);
    const e = ESPERADO[id];
    if (!e) { falhas.push(`${id}: bilhete na fixture sem linha no ESPERADO`); continue; }
    const txt = fmt(t);
    testes++;

    if (!txt.startsWith(`[Código: ${id}]`)) falhas.push(`${id}: marcador [Código:] ausente/errado`);

    const data = linha(txt, "Data:");
    if (data !== e.data) falhas.push(`${id}: data esperada ${e.data}, veio "${data}"`);

    const tipo = linha(txt, "Tipo:");
    if (tipo !== e.tipo) falhas.push(`${id}: tipo esperado "${e.tipo}", veio "${tipo}"`);

    const stake = linha(txt, "Stake:");
    if (stake !== e.stake) falhas.push(`${id}: stake esperada ${e.stake}, veio "${stake}"`);

    const status = linha(txt, "Status:");
    if (!e.status.test(status)) falhas.push(`${id}: status "${status}"`);

    const odd = linha(txt, "Odd total:").split(" ")[0];
    if (odd !== e.odd) falhas.push(`${id}: odd esperada ${e.odd}, veio "${odd}"`);
    // Em W a odd TEM de vir marcada como derivada; em L/aberta, jamais.
    const marcada = /\(= Retorno ÷ Stake\)/.test(linha(txt, "Odd total:"));
    if (!!e.oddDerivada !== marcada)
      falhas.push(`${id}: "(= Retorno ÷ Stake)" ${marcada ? "apareceu" : "faltou"} — em W a odd sai do retorno, em L/aberta é a exibida`);

    // Aberta não tem `Return` na API: nenhuma linha de retorno pode aparecer.
    if (e.semRetorno && /Retorno/.test(txt))
      falhas.push(`${id}: bilhete ABERTO não pode exibir retorno (a API não manda \`Return\`; só \`PossibleWinnings\`)`);

    // O turbo pago por fora (`BonusOffer`) tem linha PRÓPRIA, e só onde a API manda dinheiro.
    // Os dois sabores de boost desta casa não podem se confundir: o `OddsBeforeEnhancement`
    // da seleção (20707888096) JÁ está dentro do `Return` e não ganha linha nenhuma.
    const temBoost = /^Boost:/m.test(txt);
    if (!!e.boost !== temBoost)
      falhas.push(`${id}: linha "Boost:" ${temBoost ? "apareceu onde não há turbo pago por fora" : "faltou"}`);
    // A odd do turbinado NÃO é a exibida no card. Trava explícita: 2,95 aqui é o valor que
    // a leitura antiga gravava, e é o erro que custou R$149,18 de P/L neste bilhete.
    if (e.boost && linha(txt, "Odd total:").startsWith("2,95"))
      falhas.push(`${id}: odd saiu a PRÉ-boost (2,95) — o turbo do \`BonusOffer\` não entrou no retorno`);

    for (const trecho of (e.contem || [])) {
      if (!txt.includes(trecho)) falhas.push(`${id}: faltou no bloco → "${trecho}"`);
    }
  }

  return { falhas, testes };
}
