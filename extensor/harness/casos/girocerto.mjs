// GiroCerto (plataforma PRÓPRIA, `girocerto.fun`) — s455.
//
// O que o recon mediu (15/11/2026, Chrome do Feca, conta logada na aba "Minhas apostas"):
//   • A página é Next.js (RSC): os bilhetes chegam DENTRO do HTML (`self.__next_f`, prop
//     `tickets` do componente `MyBets`). Abrir a tela não dispara chamada de lista nenhuma.
//   • A mesma lista sai de `GET /api/esportes/bets`, JSON no MESMO domínio, só com o COOKIE
//     (medido com `fetch` cru, sem header). Resposta: um ARRAY de bilhetes, mais recente
//     primeiro. `POST` na mesma URL é FAZER aposta: o inject nunca manda POST.
//   • NÃO HÁ PAGINAÇÃO. São os 50 mais recentes, e nenhum parâmetro muda isso (medido:
//     `limit`, `offset`, `page`, `cursor`, `before`, `take/skip` devolvem os mesmos 50). A tela
//     também só mostra 50 ("Encerradas 50"). O fim é a 1ª resposta.
//   • A fixture é a resposta inteira, byte a byte (SHA-256 conferido com o da aba): 50
//     simples liquidadas — 27 ganhas (1 meia vitória), 16 perdidas (2 meias derrotas), 7
//     anuladas. NÃO HÁ amostra de aberta, múltipla, cashout nem freebet.
//
// PROCEDÊNCIA DOS VALORES ESPERADOS: o CARD da tela, lido nos 50 bilhetes em 15/11/2026
// (rótulo GANHOU/PERDEU/ANULADA, cotação, "Valor apostado", "Valor recebido", data e hora
// da colocação). O card não mostra o início do evento: esse vem do JSON (`legs[].startsAt`,
// UTC), sem leitura de card — marcado `evento: json`.
//
// AS ARMADILHAS QUE ESTE CASO TRAVA
//
// 1. A CASA REESCREVE `odds` NA LIQUIDAÇÃO. Anulada vira `odds: 1`, meia derrota vira 1, meia
//    vitória vira a efetiva (6M3YQUCREG: 1.413 = 423,75 ÷ 300). O card mostra as duas, a
//    original e a efetiva ("Cotação 1.825 1.413"). A odd da aposta é `originalOdds`.
// 2. `payoutCents` É O POTENCIAL até na perdida (QTPTYJD9Z3: card "Ganho potencial
//    R$ 1.875,00", perdeu). O dinheiro que voltou é `creditedCents`.
// 3. MEIA DERROTA SAI COMO `lost` E O CARD DIZ "PERDEU" (GGGT2EW6RZ, TJLVHW8CG7), mas metade
//    voltou (`creditedCents` = stake ÷ 2). Quem prova é a perna `half_lost` + o dinheiro.
//    Meia vitória sai `won` com a perna `half_won`.
// 4. O PAGAMENTO ARREDONDA PARA BAIXO, no centavo: 336,08 × 3,45 = 1.159,476 e o card diz
//    "R$ 1.159,47" (HMD2Y7X9E9). W tem de aceitar a odd da casa com esse corte.
// 5. CÓDIGO: o `code` de 10 caracteres (o do card e do "Bilhete <code>" no compartilhar),
//    nunca o `id` UUID. Os 107 bilhetes da base (por print) já usam o `code`.
// 6. `rejected` NÃO É APOSTA (a casa recusou; o dinheiro não saiu). Nunca sobe para a IA.
//
// MUTAÇÕES (s455): ver o cabeçalho do commit e o STATUS; a lista está em `MUTACOES` abaixo.
// O QUE NÃO COBRE: aberta REAL, múltipla, cashout (`cashed_out`), freebet e "pagamento
// antecipado" (`earlyPayout`/`paidEarly`): sem amostra, todos sobem a conferir e o teste usa
// clone sintético do bilhete real com o campo trocado.
import { rodarInject, carregarContent, fixture, linha } from "../sandbox.mjs";

export const casa = "GIROCERTO";

const W = (r) => new RegExp(`^Ganhou → W \\(retorno R\\$ ${r.replace(",", "\\,")}\\)$`);
const L = /^Perdeu → L$/;
const V = /^Devolvida\/void \(retorno = stake\) → V$/;
const HW = (r) => new RegExp(`^Meia vitória → HW \\(retorno R\\$ ${r} = stake ÷ 2 × odd \\+ stake ÷ 2; perna half_won\\)$`);
const HL = (r) => new RegExp(`^Meia derrota → HL \\(retorno R\\$ ${r} = stake ÷ 2; perna half_lost\\)$`);
const AB = /^em aberto \(aguardando resultado — NÃO liquidar; sem resultado\)$/;
const CONF = /a conferir — não liquidar automaticamente/;

// card = rótulo, cotação, valor apostado/recebido e hora da colocação lidos na tela.
const ESPERADO = {
  // ganhas ("Valor recebido" do card = retorno)
  "ZHUUMZ423Z": { st: W("1515,00"), odd: "2,02", stake: "750,00", data: "01/11/2026 21:54", evento: "01/11/2026 22:30:00" },
  "6JAQ86CSU2": { st: W("740,62"), odd: "1,975", stake: "375,00", data: "01/11/2026 21:49", evento: "01/11/2026 22:00:00" },
  "HMD2Y7X9E9": { st: W("1159,47"), odd: "3,45", stake: "336,08", data: "01/11/2026 13:45", evento: "01/11/2026 19:00:00" },
  "LYM9JZ6ZUE": { st: W("1002,22"), odd: "1,909", stake: "525,00", data: "01/11/2026 16:00", evento: "01/11/2026 18:00:00" },
  "TUDRP84GRY": { st: W("1068,75"), odd: "2,375", stake: "450,00", data: "01/11/2026 16:00", evento: "02/11/2026 13:00:00" },
  "3S2ARQNPWL": { st: W("787,50"), odd: "1,75", stake: "450,00", data: "01/11/2026 18:00", evento: "01/11/2026 18:30:00" },
  "CTQ3BMT5FW": { st: W("549,00"), odd: "1,83", stake: "300,00", data: "01/11/2026 13:30", evento: "01/11/2026 14:00:00" },
  // perdidas (o card estampa o "Ganho potencial", nunca dinheiro recebido)
  "QTPTYJD9Z3": { st: L, odd: "2,5", stake: "750,00", data: "01/11/2026 21:24", evento: "02/11/2026 12:00:00" },
  "D3CNWBALFZ": { st: L, odd: "2,675", stake: "300,00", data: "01/11/2026 17:59", evento: "01/11/2026 18:30:00" },
  "3MMFVBMADU": { st: L, odd: "2,2", stake: "525,00", data: "01/11/2026 13:28", evento: "02/11/2026 02:00:00" },
  // anuladas (card "Cotação 1.76 1.00": a odd é a original)
  "P4YT7HM9MW": { st: V, odd: "1,76", stake: "1500,00", data: "01/11/2026 20:54", evento: "01/11/2026 21:00:00" },
  "DNCKNB9UGT": { st: V, odd: "1,72", stake: "375,00", data: "01/11/2026 18:00", evento: "01/11/2026 18:30:00" },
  // meia vitória (card GANHOU, "meio ganha (metade devolvida)", recebido R$ 423,75)
  "6M3YQUCREG": { st: HW("423,75"), odd: "1,825", stake: "300,00", data: "01/11/2026 13:38", evento: "01/11/2026 14:00:00" },
  // meias derrotas (card PERDEU, "meio perdida (metade devolvida)"; a metade só no JSON)
  "GGGT2EW6RZ": { st: HL("262,50"), odd: "2,025", stake: "525,00", data: "01/11/2026 16:25", evento: "01/11/2026 23:00:00" },
  "TJLVHW8CG7": { st: HL("187,50"), odd: "2,15", stake: "375,00", data: "01/11/2026 11:48", evento: "01/11/2026 12:00:00" },
};

const RX_LISTA = /\/api\/esportes\/bets(?:[?#]|$)/;

export async function rodar() {
  const fx = JSON.parse(fixture("girocerto.bets.json"));
  const pedidas = [];
  const responder = (url, opts) => {
    if (!RX_LISTA.test(url)) return null;
    pedidas.push(((opts && opts.method) || "GET").toUpperCase());
    return JSON.stringify(fx);
  };

  // Carga REAL da tela: nenhuma requisição de lista (os bilhetes vêm no HTML).
  const { ultima } = await rodarInject({
    inject: "gc_inject.js",
    href: "https://girocerto.fun/esportes?aba=apostas",
    semRequisicaoInicial: true,
    pedido: "__sharpenupGCReq",
    responder,
  });

  const falhas = [];
  if (!ultima) return { falhas: ["o inject não emitiu nenhuma mensagem"], testes: 0 };
  if (!ultima.hook) falhas.push("o inject não emitiu `hook:true` (autodiagnóstico cego)");
  if (!ultima.fim) falhas.push("o inject não sinalizou `fim` (o robô ficaria esperando o teto)");
  const bilhetes = ultima.bilhetes || [];
  if (bilhetes.length !== fx.length) falhas.push(`esperava ${fx.length} bilhetes normalizados, vieram ${bilhetes.length}`);
  if (pedidas.length !== 1) falhas.push(`o inject pediu a lista ${pedidas.length} vez(es) (a casa não pagina: 1 pedido basta)`);
  if (pedidas.some((m) => m !== "GET")) falhas.push(`o inject mandou ${JSON.stringify(pedidas)} — POST nesta URL FAZ APOSTA`);
  if (ultima.respostas !== 1) falhas.push(`respostas = ${ultima.respostas}, esperava 1`);
  if (bilhetes.some((b) => !/^[A-Z0-9]{10}$/.test(b.id))) falhas.push("o id do bilhete não é o `code` de 10 caracteres do card");
  if (!Array.isArray(ultima.cru) || ultima.cru.length !== fx.length) falhas.push("o inject não mandou o cru de cada bilhete");
  else {
    const c = ultima.cru.find((x) => x.codigo === "6M3YQUCREG");
    if (!c || !c.cru || c.cru.code !== "6M3YQUCREG" || !Array.isArray(c.cru.legs) || c.cru.originalOdds !== 1.825) {
      falhas.push("o cru da meia vitória não é o bilhete da casa verbatim (com `code`, `legs` e `originalOdds`)");
    }
  }

  const fmt = carregarContent().pegar("formatTicketGC");
  let testes = 0;
  for (const b of bilhetes) {
    const txt = fmt(b);
    if (!txt.startsWith(`[Código: ${b.id}]`)) falhas.push(`${b.id}: marcador [Código:] ausente/errado`);
    if (!linha(txt, "Status (API):")) falhas.push(`${b.id}: falta o status cru da API`);
    const odd = linha(txt, "Odd:");
    if (!odd || /^1(,0*)?$/.test(odd) || /^0*(,0*)?$/.test(odd)) falhas.push(`${b.id}: odd "${odd}" (a reescrita da liquidação vazou: armadilha 1)`);
    if (linha(txt, "Retorno potencial:")) falhas.push(`${b.id}: "Retorno potencial" num bilhete liquidado`);
    if (CONF.test(linha(txt, "Status:"))) falhas.push(`${b.id}: liquidada da amostra ficou a conferir ("${linha(txt, "Status:")}")`);
  }

  for (const [cod, e] of Object.entries(ESPERADO)) {
    const b = bilhetes.find((x) => x.id === cod);
    if (!b) { falhas.push(`${cod}: bilhete ausente`); continue; }
    const txt = fmt(b);
    testes++;
    const odd = linha(txt, "Odd:"), st = linha(txt, "Status:"), stake = linha(txt, "Stake:");
    if (odd !== e.odd) falhas.push(`${cod} (card): odd esperada ${e.odd}, veio "${odd}"`);
    if (!e.st.test(st)) falhas.push(`${cod} (card): status "${st}"`);
    if (stake !== e.stake) falhas.push(`${cod} (card): stake esperada ${e.stake}, veio "${stake}"`);
    if (!linha(txt, "Data (colocação):").startsWith(e.data)) falhas.push(`${cod} (card): colocação esperada ${e.data}, veio "${linha(txt, "Data (colocação):")}"`);
    if (linha(txt, "Data (evento mais recente):") !== e.evento) falhas.push(`${cod} (json): evento esperado ${e.evento}, veio "${linha(txt, "Data (evento mais recente):")}" (o início vem em UTC)`);
  }

  // Armadilha 2: o potencial nunca entra no status da perdida.
  {
    const txt = fmt(bilhetes.find((x) => x.id === "QTPTYJD9Z3") || {});
    if (/1875|1\.875/.test(txt)) falhas.push("QTPTYJD9Z3: o potencial R$ 1.875 entrou no bloco da perdida");
  }
  // Seleção: mercado, pick, jogo e o resultado da perna, como o card.
  {
    const txt = fmt(bilhetes.find((x) => x.id === "GGGT2EW6RZ") || {});
    if (!txt.includes("- 1º tempo - handicap 0.0, -0.5: CSD Comunicaciones 0.0, -0.5 [perna meia derrota]")) falhas.push(`GGGT2EW6RZ: seleção mal escrita:\n${txt}`);
    if (!txt.includes("Jogo: CSD Comunicaciones x Deportivo Mixco")) falhas.push("GGGT2EW6RZ: o jogo sumiu do bloco");
  }

  testes += sinteticos(falhas, fmt, bilhetes);
  testes += await passivo(falhas, fx);
  testes += await semLixo(falhas, fx);
  testes += await novaRodada(falhas, fx);
  testes += await deslogado(falhas);
  return { falhas, testes };
}

// Sessão caída: a API responde OBJETO (erro), não lista. Não é resposta válida, e o robô
// tem de receber o `fim` com `respostas: 0` (é o que acende o aviso "faça login").
async function deslogado(falhas) {
  const { ultima } = await rodarInject({
    inject: "gc_inject.js", href: "https://girocerto.fun/esportes?aba=apostas",
    semRequisicaoInicial: true, pedido: "__sharpenupGCReq",
    responder: (url) => (RX_LISTA.test(url) ? JSON.stringify({ error: "unauthorized" }) : null),
  });
  if (!ultima || !ultima.fim) falhas.push("deslogado: o inject não sinalizou `fim`");
  else if (ultima.respostas !== 0) falhas.push(`deslogado: respostas = ${ultima.respostas} (o erro contou como lista)`);
  return 1;
}

// Clones dos bilhetes reais com um campo trocado: o que a amostra não tem sobe a conferir ou em
// aberto, nunca liquidado por chute.
function sinteticos(falhas, fmt, bilhetes) {
  const ganha = bilhetes.find((x) => x.id === "ZHUUMZ423Z");
  const hl = bilhetes.find((x) => x.id === "GGGT2EW6RZ");
  const perdida = bilhetes.find((x) => x.id === "QTPTYJD9Z3");
  if (!ganha || !hl || !perdida) { falhas.push("sintéticos: bilhete-base ausente"); return 0; }
  let n = 0;
  const st = (b) => linha(fmt(b), "Status:");
  const ok = (cond, msg) => { n++; if (!cond) falhas.push(msg); };

  // Aberta: todo status de "em andamento" do JS da casa.
  for (const s of ["accepted", "pending", "placing", "cashing", "voiding"]) {
    const t = fmt({ ...ganha, status: s, retorno: 0 });
    ok(AB.test(linha(t, "Status:")), `${s}: "${linha(t, "Status:")}" (tinha de ficar em aberto)`);
    ok(linha(t, "Retorno potencial:") === "R$ 1515,00", `${s}: retorno potencial "${linha(t, "Retorno potencial:")}"`);
  }
  ok(CONF.test(st({ ...ganha, status: "suspensa" })), `status desconhecido virou "${st({ ...ganha, status: "suspensa" })}"`);
  ok(CONF.test(st({ ...ganha, status: "rejected" })), "rejected não ficou a conferir");
  ok(/NÃO lançar/.test(st({ ...ganha, status: "rejected" })), "rejected não diz que não é aposta");
  ok(CONF.test(st({ ...ganha, status: "cashed_out", cashout: 900, retorno: 900 })), "cashed_out sem amostra virou liquidado");
  ok(CONF.test(st({ ...ganha, cashout: 500 })), "won com cashedCents > 0 (cashout parcial?) virou liquidado");
  ok(CONF.test(st({ ...ganha, freebet: true })), "freebet sem amostra virou liquidado");
  ok(CONF.test(st({ ...ganha, retorno: 1320 })), "won com retorno que não fecha stake × odd virou liquidado");
  ok(CONF.test(st({ ...ganha, retorno: 750 })), "won com retorno = stake virou liquidado (só void é V)");
  ok(CONF.test(st({ ...perdida, status: "void" })), "retorno zero com void virou liquidado");
  ok(CONF.test(st({ ...perdida, status: "won" })), "retorno zero com won virou liquidado");
  // Meia derrota só com as DUAS provas: perna half_lost E retorno = stake ÷ 2.
  ok(CONF.test(st({ ...hl, retorno: 300 })), "meia derrota fora do centavo virou HL");
  ok(CONF.test(st({ ...hl, sels: hl.sels.map((s) => ({ ...s, status: "lost" })) })), "metade da stake sem perna half_lost virou HL (pode ser cashout de metade)");
  ok(CONF.test(st({ ...hl, status: "won" })), "half_lost com status won virou HL");
  // Múltipla: odd do bilhete × stake fecha → W; não fecha → a conferir; odd por seleção dita.
  const p2 = { ...ganha.sels[0], odd: 1.01, label: "Outra seleção" };
  const mult = { ...ganha, tipo: "multiple", sels: [ganha.sels[0], p2] };
  ok(W("1515,00").test(st(mult)), `múltipla que fecha virou "${st(mult)}"`);
  ok(/^Múltipla \(2 seleções\)$/.test(linha(fmt(mult), "Tipo:")), `múltipla com tipo "${linha(fmt(mult), "Tipo:")}"`);
  ok(/Odd da seleção: 1,01/.test(fmt(mult)), "múltipla sem a odd de cada seleção");
  ok(CONF.test(st({ ...mult, retorno: 1200 })), "múltipla que não fecha virou liquidada");
  // O robô pula `rejected` (armadilha 6): a regra mora num helper testável.
  const rej = carregarContent().pegar("_rejeitadaGC");
  ok(rej({ status: "rejected" }) === true && rej({ status: "won" }) === false, "_rejeitadaGC não separa rejected");
  return n;
}

// A página que CHAMA a lista (o caso futuro, ou um "atualizar"): o hook passivo encaminha a
// resposta sem o content pedir nada.
async function passivo(falhas, fx) {
  const { ultima } = await rodarInject({
    inject: "gc_inject.js", href: "https://girocerto.fun/esportes?aba=apostas",
    urlInicial: "https://girocerto.fun/api/esportes/bets",
    responder: (url) => (RX_LISTA.test(url) ? JSON.stringify(fx) : null),
  });
  const n = (ultima && ultima.bilhetes || []).length;
  if (n !== fx.length) falhas.push(`passivo: a resposta que a PÁGINA buscou não chegou (${n} de ${fx.length})`);
  return 1;
}

// Respostas que NÃO são a lista: o detalhe de um bilhete, as cotações de cashout e o objeto
// que o POST de aposta devolve. Nenhuma vira bilhete nem conta como resposta.
async function semLixo(falhas, fx) {
  const um = fx[0];
  const { ultima, todas } = await rodarInject({
    inject: "gc_inject.js", href: "https://girocerto.fun/esportes?aba=apostas",
    semRequisicaoInicial: true,
    urlsExtra: [
      "https://girocerto.fun/api/esportes/bets/" + um.id,
      { url: "https://girocerto.fun/api/esportes/bets/cashout/quotes", opts: { method: "POST", body: "{}" } },
      { url: "https://girocerto.fun/api/esportes/bets", opts: { method: "POST", body: "{}" } },
    ],
    responder: (url, opts) => {
      if (/\/bets\/cashout\/quotes/.test(url)) return JSON.stringify([{ id: um.id, quoteCents: 1 }]);
      if (/\/bets\/[0-9a-f-]{36}/.test(url)) return JSON.stringify([um]);
      if (RX_LISTA.test(url) && opts && opts.method === "POST") return JSON.stringify({ ok: true, tickets: [um] });
      return null;
    },
  });
  const n = ultima ? (ultima.bilhetes || []).length : 0;
  if (n) falhas.push(`semLixo: ${n} bilhete(s) de resposta que não é a lista`);
  if (ultima && ultima.respostas) falhas.push(`semLixo: respostas = ${ultima.respostas} (detalhe/cotação/POST contaram)`);
  void todas;
  return 1;
}

// Pedido novo é rodada NOVA: o acumulado zera e a lista é pedida de novo (lição da s393).
async function novaRodada(falhas, fx) {
  let pedidos = 0;
  const { ultima } = await rodarInject({
    inject: "gc_inject.js", href: "https://girocerto.fun/esportes?aba=apostas",
    semRequisicaoInicial: true, pedido: "__sharpenupGCReq",
    pedidoTardio: { __sharpenupGCReq: true },
    responder: (url) => {
      if (!RX_LISTA.test(url)) return null;
      pedidos++;
      return JSON.stringify(pedidos === 1 ? fx : fx.slice(0, 3));
    },
  });
  const n = ultima ? (ultima.bilhetes || []).length : 0;
  if (pedidos !== 2) falhas.push(`novaRodada: a 2ª rodada não pediu a lista de novo (${pedidos} pedido(s))`);
  if (n !== 3) falhas.push(`novaRodada: a 2ª rodada carregou o acumulado velho (${n} bilhetes, esperava 3)`);
  return 1;
}
