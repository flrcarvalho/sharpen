// CopaWin (plataforma PRÓPRIA, `wncopa.com`) — s451.
//
// O que o recon mediu (12/11/2026, conta do Jaao26, Chrome, aba "Minhas Apostas"):
//   • A lista é `GET /api/bet/my-bets[?status=<filtro>][&page=N]`, JSON no MESMO domínio, e só
//     o COOKIE da sessão basta (sem token, sem CSRF: medido com `fetch` cru). Resposta:
//     `{ success, bets: [...], pagination: { current_page, total_pages, total } }`.
//   • A 1ª página vem RENDERIZADA NO HTML: abrir `/my-bets` não dispara chamada nenhuma (só o
//     "carregar mais" chama a API). Hook passivo não veria nada — o inject BUSCA a lista.
//   • Filtros da tela: all · active · won · lost · cashout. `all` (sem `status`) traz tudo.
//   • A conta está LIMITADA: 15 bilhetes, todos liquidados (5 ganhas, 8 perdidas, 2 anuladas),
//     todos `type: "single"`. NÃO HÁ amostra de aberta, múltipla (`type: "multiple"`) nem
//     cashout. A fixture é a resposta inteira, byte a byte (SHA-256 conferido com a da aba).
//
// ⚠ PROCEDÊNCIA DOS VALORES ESPERADOS. `card` = lido no card da tela em 12/11/2026 (data de
// colocação, stake, rótulo, mercado, seleção, jogo e o valor de RETORNO quando ganha). `json`
// = do corpo da resposta, sem leitura de card (o Chrome travou antes da segunda passada). A
// odd não aparece no card: ela é a do JSON, conferida pelo dinheiro (W) e pelo "RETORNO" que o
// card estampa (potencial = stake × odd, ver armadilha 2).
//
// AS ARMADILHAS QUE ESTE CASO TRAVA
//
// 1. PÁGINA ALÉM DO FIM DEVOLVE A PÁGINA 1 DE NOVO (medido: `page=2` com `total_pages: 1`
//    respondeu `current_page: 1` e os mesmos 15). Parar por "veio vazio" é laço infinito
//    e duplicação; o fim é `pagination.total_pages`, e página que volta com `current_page`
//    diferente da pedida também encerra. A paginação abaixo é um corte SINTÉTICO dos 15
//    bilhetes reais (10 + 5) — a conta não tem página 2.
// 2. O CARD MOSTRA O RETORNO POTENCIAL ATÉ NA PERDIDA (Náutico, 660703: "RETORNO R$ 2.247,00",
//    perdida). O dinheiro de verdade é `actual_return` (0.00). Quem ler `potential_return`
//    liquida perdida como ganha.
// 3. DATAS EM DOIS FUSOS. `created_at`/`updated_at` em Brasília (o card mostra o `created_at`
//    verbatim); `event_starts_at`/`last_event_at` em UTC (prova: em 6 bilhetes a liquidação
//    vem ~1h ANTES do horário do evento). Náutico x CRB `2026-11-08 00:30:00` é 07/11 às 21:30.
// 4. ODD TURBINADA (652529): a casa vende 4 seleções de 4 jogos como `type: "single"` com UM
//    item (`market_key: "combined"`), seleções juntadas por `||`, SEM odd por seleção
//    (`leg_odds: null`) e o resultado de cada uma em `leg_statuses`. A odd é a do conjunto.
// 5. O TEXTO DA PERNA NÃO É FONTE. `player_note` traz recado interno ("LIQUIDAR MANUALMENTE…",
//    "GANHANDO") em bilhete já liquidado. A verdade é `status` + `actual_return`.
// 6. Meia vitória/derrota não têm status próprio: a casa só escreve "meia-vitória" na nota
//    e devolve `won`/`lost`. Retorno que não fecha com stake × odd sobe a conferir.
//
// MUTAÇÕES (s451): 16 aplicadas, 14 detectadas. As 2 que escapam são INÓCUAS:
//   • "aberta sobrescreve liquidada" no inject: o acumulado zera a cada pedido e uma busca
//     só vê cada bilhete uma vez; a regra protege o "carregar mais" da página, que o
//     harness não reproduz junto com a busca.
//   • tirar o ramo `cashout` do formatador: todo caminho de `cashout` já termina "a conferir"
//     (o ramo só melhora a frase).
// O QUE NÃO COBRE: aberta, múltipla e cashout REAIS (a conta não tem nenhum; os testes acima
// usam clone do 660730 com o status trocado), meia vitória real, boost por `boost_pct`.
import { rodarInject, carregarContent, fixture, linha } from "../sandbox.mjs";

export const casa = "COPAWIN";

const W = /^Ganhou → W \(retorno R\$ \d+,\d{2}\)$/;
const L = /^Perdeu → L$/;
const V = /^Devolvida\/void \(retorno = stake\) → V$/;
const AB = /^em aberto \(aguardando resultado — NÃO liquidar; sem resultado\)$/;
const CONF = /a conferir — não liquidar automaticamente/;

const ESPERADO = {
  // anuladas
  "660753": { st: V, odd: "1,73", stake: "750,00", data: "07/11/2026 14:44:34", evento: "07/11/2026 15:00:00", p: "card" },
  "659054": { st: V, odd: "4,62", stake: "3000,00", data: "07/11/2026 13:35:19", evento: "07/11/2026 22:00:00", p: "json" },
  // ganhas (o retorno do card é o dinheiro recebido)
  "660730": { st: W, odd: "2,2", stake: "825,00", ret: 1815, data: "07/11/2026 14:43:20", evento: "07/11/2026 16:00:00", p: "card (RETORNO R$ 1.815,00)" },
  "660701": { st: W, odd: "3,15", stake: "1875,00", ret: 5906.25, data: "07/11/2026 14:41:32", evento: "07/11/2026 17:30:00", p: "json" },
  "659239": { st: W, odd: "2,3", stake: "600,00", ret: 1380, data: "07/11/2026 13:43:23", evento: "08/11/2026 08:00:00", p: "json" },
  "659209": { st: W, odd: "2,6", stake: "900,00", ret: 2340, data: "07/11/2026 13:42:08", evento: "07/11/2026 22:00:00", p: "json" },
  "659194": { st: W, odd: "2,5", stake: "1050,00", ret: 2625, data: "07/11/2026 13:41:36", evento: "07/11/2026 17:30:00", p: "json" },
  // perdidas
  "660725": { st: L, odd: "2,62", stake: "975,00", data: "07/11/2026 14:42:55", evento: "08/11/2026 02:00:00", p: "card" },
  "660703": { st: L, odd: "4,28", stake: "525,00", data: "07/11/2026 14:41:45", evento: "07/11/2026 21:30:00", p: "card (RETORNO potencial R$ 2.247,00)" },
  "659246": { st: L, odd: "1,73", stake: "525,00", data: "07/11/2026 13:43:41", evento: "07/11/2026 14:00:00", p: "json" },
  "659226": { st: L, odd: "2,1", stake: "825,00", data: "07/11/2026 13:43:00", evento: "07/11/2026 16:00:00", p: "json" },
  "659222": { st: L, odd: "2,39", stake: "825,00", data: "07/11/2026 13:42:46", evento: "07/11/2026 16:00:00", p: "json" },
  "659217": { st: L, odd: "2,5", stake: "900,00", data: "07/11/2026 13:42:27", evento: "08/11/2026 04:30:00", p: "json" },
  "659201": { st: L, odd: "2,5", stake: "1050,00", data: "07/11/2026 13:41:52", evento: "07/11/2026 19:00:00", p: "json" },
  // Odd Turbinada (combo da casa): evento mais recente = `last_event_at` 20:05 UTC
  "652529": { st: L, odd: "2,64", stake: "15,00", data: "07/11/2026 08:10:02", evento: "07/11/2026 17:05:00", p: "card" },
};

const NAUTICO = "660703";
const TURBINADA = "652529";
const TAM = 10;   // corte sintético da paginação (a conta real tem 1 página)

function paginas(fx) {
  const todos = fx.bets;
  const total = Math.ceil(todos.length / TAM);
  return { todos, total, pg: (n) => ({
    success: true, bets: todos.slice((n - 1) * TAM, n * TAM),
    pagination: { current_page: n, total_pages: total, total: todos.length },
  }) };
}

export async function rodar() {
  const fx = JSON.parse(fixture("copawin.my-bets.json"));
  const P = paginas(fx);
  const pedidas = [];

  // A casa como foi MEDIDA: página fora da faixa volta a página 1 (armadilha 1).
  const responder = (url) => {
    if (!/\/api\/bet\/my-bets/.test(url)) return null;
    let pg = 1;
    try { pg = Number(new URL(url).searchParams.get("page")) || 1; } catch (e) {}
    pedidas.push(pg);
    if (pedidas.length > 50) return JSON.stringify({ success: true, bets: [], pagination: { current_page: 1, total_pages: P.total, total: 15 } });
    return JSON.stringify(P.pg(pg >= 1 && pg <= P.total ? pg : 1));
  };

  // Carga REAL da tela: nenhuma requisição de lista (a 1ª página vem no HTML).
  const { ultima, urls } = await rodarInject({
    inject: "cw_inject.js",
    href: "https://wncopa.com/my-bets",
    semRequisicaoInicial: true,
    pedido: "__sharpenupCWReq",
    responder,
  });

  const falhas = [];
  if (!ultima) return { falhas: ["o inject não emitiu nenhuma mensagem"], testes: 0 };
  if (!ultima.hook) falhas.push("o inject não emitiu `hook:true` (autodiagnóstico cego)");
  if (!ultima.fim) falhas.push("o inject não sinalizou `fim` (o robô ficaria esperando o teto)");
  const bilhetes = ultima.bilhetes || [];
  if (bilhetes.length !== P.todos.length) falhas.push(`esperava ${P.todos.length} bilhetes normalizados, vieram ${bilhetes.length}`);
  if (!pedidas.includes(1) || !pedidas.includes(2)) falhas.push(`o inject não varreu as 2 páginas (pediu ${JSON.stringify(pedidas)})`);
  if (pedidas.some((p) => p > P.total)) falhas.push(`o inject pediu além de total_pages (${JSON.stringify(pedidas)}) — a casa devolve a página 1 de novo`);
  if (pedidas.length > 2 * P.total) falhas.push(`o inject pediu ${pedidas.length} páginas para ${P.total} (laço na paginação)`);
  if (ultima.respostas !== P.total) falhas.push(`respostas = ${ultima.respostas}, esperava ${P.total}`);
  if (!Array.isArray(ultima.cru) || ultima.cru.length !== P.todos.length) falhas.push("o inject não mandou o cru de cada bilhete");
  else {
    const c = ultima.cru.find((x) => x.codigo === TURBINADA);
    if (!c || !c.cru || !Array.isArray(c.cru.items) || !c.cru.items[0].leg_statuses) falhas.push("o cru da Turbinada não é o bilhete da casa verbatim");
  }
  void urls;

  const fmt = carregarContent().pegar("formatTicketCW");
  let testes = 0;
  for (const b of bilhetes) {
    const txt = fmt(b);
    if (!txt.startsWith(`[Código: ${b.id}]`)) falhas.push(`${b.id}: marcador [Código:] ausente/errado`);
    if (!linha(txt, "Status (API):")) falhas.push(`${b.id}: falta o status cru da API`);
    if (/^0*(,0*)?$/.test(linha(txt, "Odd:"))) falhas.push(`${b.id}: odd zerada ou ausente`);
    if (/LIQUIDAR MANUALMENTE|GANHANDO|Acompanhando/.test(txt)) falhas.push(`${b.id}: recado interno da casa (player_note/live_description) entrou no bloco`);
  }

  for (const [cod, e] of Object.entries(ESPERADO)) {
    const b = bilhetes.find((x) => x.id === cod);
    if (!b) { falhas.push(`${cod} (${e.p}): bilhete ausente`); continue; }
    const txt = fmt(b);
    testes++;
    const odd = linha(txt, "Odd:"), st = linha(txt, "Status:"), stake = linha(txt, "Stake:");
    if (odd !== e.odd) falhas.push(`${cod} (${e.p}): odd esperada ${e.odd}, veio "${odd}"`);
    if (!e.st.test(st)) falhas.push(`${cod} (${e.p}): status "${st}"`);
    if (stake !== e.stake) falhas.push(`${cod} (${e.p}): stake esperada ${e.stake}, veio "${stake}"`);
    if (linha(txt, "Data (colocação):") !== e.data) falhas.push(`${cod}: data de colocação esperada ${e.data}, veio "${linha(txt, "Data (colocação):")}"`);
    if (linha(txt, "Data (evento mais recente):") !== e.evento) falhas.push(`${cod}: data do EVENTO esperada ${e.evento}, veio "${linha(txt, "Data (evento mais recente):")}" (o evento vem em UTC)`);
    if (e.ret != null) {
      const n = Number(odd.replace(",", ".")), s = Number(e.stake.replace(",", "."));
      if (Math.abs(n * s - e.ret) > 0.01) falhas.push(`${cod}: odd ${odd} × stake ${e.stake} não explica o retorno ${e.ret}`);
    }
  }

  // Armadilha 2: o potencial nunca vira retorno de perdida.
  {
    const b = bilhetes.find((x) => x.id === NAUTICO);
    const txt = b ? fmt(b) : "";
    if (/2247|2\.247/.test(linha(txt, "Status:"))) falhas.push(`${NAUTICO}: o potencial R$ 2.247 entrou no status da perdida`);
    if (linha(txt, "Retorno potencial:")) falhas.push(`${NAUTICO}: "Retorno potencial" num bilhete liquidado`);
  }
  // Armadilha 4: a Turbinada sai como combo de 4 seleções, sem odd por seleção, com o resultado de cada uma.
  {
    const b = bilhetes.find((x) => x.id === TURBINADA);
    const txt = b ? fmt(b) : "";
    if (!/^Odd Turbinada \(combo da casa · 4 seleções/.test(linha(txt, "Tipo:"))) falhas.push(`${TURBINADA}: tipo "${linha(txt, "Tipo:")}"`);
    for (const j of ["Nottingham vs Manchester City", "AS Roma vs Sassuolo", "Valencia vs Real Madrid", "PSG vs Troyes"]) {
      if (!txt.includes(j)) falhas.push(`${TURBINADA}: o jogo "${j}" sumiu do bloco`);
    }
    if (!/Manchester City vence \[perna perdida\]/.test(txt)) falhas.push(`${TURBINADA}: a perna perdida (leg_statuses[0]) não está dita`);
    if (/Odd da seleção/.test(txt)) falhas.push(`${TURBINADA}: odd por seleção inventada (a casa não dá)`);
  }
  // Status desconhecido sobe cru; aberta não liquida; cashout e retorno que não fecha vão a conferir.
  {
    const base = bilhetes.find((x) => x.id === "660730");
    if (base) {
      const est = linha(fmt({ ...base, status: "suspensa" }), "Status:");
      if (!CONF.test(est)) falhas.push(`status desconhecido virou "${est}"`);
      for (const s of ["pending", "active"]) {
        const ab = { ...base, status: s, retorno: 0 };
        const t = fmt(ab);
        if (!AB.test(linha(t, "Status:"))) falhas.push(`${s}: "${linha(t, "Status:")}" (tinha de ficar em aberto)`);
        if (linha(t, "Retorno potencial:") !== "R$ 1815,00") falhas.push(`${s}: retorno potencial "${linha(t, "Retorno potencial:")}"`);
      }
      const co = linha(fmt({ ...base, status: "cashout", retorno: 1000 }), "Status:");
      if (!CONF.test(co)) falhas.push(`cashout sem amostra virou "${co}"`);
      const meia = linha(fmt({ ...base, retorno: 1320 }), "Status:");
      if (!CONF.test(meia)) falhas.push(`won com retorno que não fecha stake × odd virou "${meia}"`);
      // Retorno = stake só é V com `void`: `won` devolvendo a stake é caso a conferir.
      const wv = linha(fmt({ ...base, retorno: 825 }), "Status:");
      if (!CONF.test(wv)) falhas.push(`won com retorno = stake virou "${wv}" (só void é V)`);
    }
    const p0 = bilhetes.find((x) => x.id === "660725");
    if (p0) {
      const st = linha(fmt({ ...p0, status: "void" }), "Status:");
      if (/Perdeu → L|→ V/.test(st)) falhas.push(`retorno zero com status void virou "${st}" (só lost com zero é derrota)`);
    }
  }
  testes += await totalMentido(fx, falhas);
  testes += await segundaRodada(fx, falhas, fmt);
  return { falhas, testes };
}

// Armadilha 1, a outra metade: a casa ANUNCIA mais páginas do que tem (`total_pages: 5` com
// 2 páginas reais) e, além do fim, devolve a página 1. A guarda do `current_page` encerra na
// 1ª página "errada"; sem ela o inject pediria as 5.
async function totalMentido(fx, falhas) {
  const P = paginas(fx);
  const pedidas = [];
  const responder = (url) => {
    if (!/\/api\/bet\/my-bets/.test(url)) return null;
    let pg = 1;
    try { pg = Number(new URL(url).searchParams.get("page")) || 1; } catch (e) {}
    pedidas.push(pg);
    const r = P.pg(pg >= 1 && pg <= P.total ? pg : 1);
    r.pagination.total_pages = 5;
    return JSON.stringify(r);
  };
  const { ultima } = await rodarInject({
    inject: "cw_inject.js", href: "https://wncopa.com/my-bets", semRequisicaoInicial: true,
    pedido: "__sharpenupCWReq", responder,
  });
  if (JSON.stringify(pedidas) !== "[1,2,3]") falhas.push(`total_pages mentido: o inject pediu ${JSON.stringify(pedidas)} (esperava parar na 1ª página que volta trocada: [1,2,3])`);
  if (!ultima || (ultima.bilhetes || []).length !== P.todos.length) falhas.push("total_pages mentido: acumulado errado");
  if (!ultima || !ultima.fim) falhas.push("total_pages mentido: sem `fim`");
  return 1;
}

// 2ª rodada na mesma aba: o inject repergunta à casa (não reenvia o acumulado velho) e o
// content não formata o mapa da 1ª rodada antes da resposta nova (lição da s393, DEX Sport).
async function segundaRodada(fx, falhas, fmt) {
  const clone = JSON.parse(JSON.stringify(fx));
  const alvo = clone.bets.find((b) => b.id === 660725);
  const antes = JSON.parse(JSON.stringify(fx));
  // Na 1ª rodada, 660725 ainda estava ABERTA; depois a casa a liquidou como perdida.
  const ab = antes.bets.find((b) => b.id === 660725);
  ab.status = "pending"; ab.actual_return = "0.00"; ab.items[0].result = "pending";
  let fimVisto = false, depois = false;
  const responder = (url) => {
    if (!/\/api\/bet\/my-bets/.test(url)) return null;
    if (fimVisto) depois = true;
    const src = depois ? clone : antes;
    fimVisto = true;
    return JSON.stringify({ success: true, bets: src.bets, pagination: { current_page: 1, total_pages: 1, total: src.bets.length } });
  };
  const { ultima, mensagens } = await rodarInject({
    inject: "cw_inject.js", href: "https://wncopa.com/my-bets", semRequisicaoInicial: true,
    pedido: "__sharpenupCWReq", pedidoTardio: { __sharpenupCWReq: true }, responder, ms: 500,
  });
  const b = ((ultima && ultima.bilhetes) || []).filter((x) => x.id === "660725");
  if (!depois) falhas.push("2ª rodada (inject): o pedido tardio não tocou a rede");
  if (b.length !== 1 || !L.test(linha(fmt(b[0]), "Status:"))) falhas.push(`2ª rodada (inject): 660725 liquidou na casa e subiu "${b[0] ? linha(fmt(b[0]), "Status:") : "(ausente)"}"`);
  const iFim = mensagens.findIndex((m) => m && m.fim);
  const velha = mensagens.slice(iFim + 1).some((m) => (m.bilhetes || []).some((x) => x.id === "660725" && x.status === "pending"));
  if (iFim >= 0 && velha) falhas.push("2ª rodada (inject): reenviou a aberta velha antes de a casa responder");
  void alvo;

  const { pegar } = carregarContent();
  const mapa = pegar("cwById");
  const velhaB = { id: "660725", status: "pending", stake: 975, odd: 2.62, potencial: 2554.5, retorno: 0, ts: 0, sels: [] };
  mapa.set("660725", velhaB);
  pegar("cwFimReal = true");
  setTimeout(() => { mapa.set("660725", { ...velhaB, status: "lost" }); pegar("cwFimReal = true"); }, 1200);
  const blocos = await pegar("roboCWPassive")({ parar: () => false, stopId: null, cutoff: 0, pisoSanidade: 0, painel: { contador: {} } });
  const meu = blocos.filter((t) => t.startsWith("[Código: 660725]"));
  if (meu.length !== 1 || !L.test(linha(meu[0], "Status:"))) falhas.push(`2ª rodada (content): formatou a versão velha — ${meu.map((t) => linha(t, "Status:")).join(" | ")}`);
  return 2;
}
