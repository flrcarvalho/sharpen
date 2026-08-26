// 1xBet (1xbet.bet.br) — captura por API `POST /service/bethistory/GetBetInfoHistoryWithSummaryByDates`
// (recon s298, pelo `tools/recon_casa.js` — a 1ª casa reconhecida SEM conta nossa).
//
// PLATAFORMA PRÓPRIA. App Vue, API toda no host da casa em `/service/`. Não é Altenar/BIA,
// não é BetBy, não é Kambi, não é BetConstruct, não é BlueBrown. Inject e formatador próprios.
//
// AUTH POR COOKIE — **não há `Authorization`**. Os headers são só de canal (`accept`,
// `content-type`, `x-language`). Mesmo assim o inject aprende de uma requisição REAL em vez de
// montar a sua: `PartnerId`, `PartnerGroupId`, `Whence`, `CfView` e `BonusUserId` viajam no
// CORPO e são da conta/tenant, não nossos de inventar.
//
// UMA CHAMADA TRAZ ABERTAS E FECHADAS. Diferente da Novibet (que exigiu `result:null`, um valor
// que a página nunca usa), aqui o mesmo POST devolve os dois estados misturados. Não há aba.
//
// ── O QUE ESTE CASO TRAVA (cada item medido no payload real, 91 bilhetes) ──────────────────
//
//   • O `Coef` DO BILHETE MENTE NA PERDIDA. Quando há perna anulada, a casa RECALCULA o `Coef`
//     se o bilhete ganhou (7 de 7: `Coef` == produto das pernas, e `stake × Coef` == `WinSum`)
//     e NÃO recalcula se perdeu (9 de 9 ficam com o valor PRÉ-anulação, inflado — o 16101007
//     diz 8,607956 onde a estrutura real é 4,5787, quase o dobro). Ler `Coef` cru poria odd
//     errada em 9 dos 66 perdidos. A perna anulada se reconhece por `Coef == 1`.
//
//     ⚠ O GATILHO DA CORREÇÃO É A PERNA ANULADA, NÃO A DIVERGÊNCIA SOZINHA — e isso é
//     deliberado. Num bilhete PERDIDO, "Coef inflado por anulação" e "Coef turbinado por
//     boost" são INDISTINGUÍVEIS (nos dois o Coef fica acima do produto e não há dinheiro
//     para arbitrar). Corrigir por divergência pura destruiria uma odd de boost legítima.
//     Nesta casa não se observou boost nenhum em 95 bilhetes — se aparecer, o gatilho por
//     perna anulada já evita o falso positivo.
//
//   • A ANULADA NÃO TEM STATUS PRÓPRIO. `BetStatus` só assume 1 (aberta), 2 (perdida) e
//     4 (ganha) — em 95 bilhetes de 12 meses. A aposta ANULADA vem como **status 4**, com
//     `WinSum == BetSum` e `Coef == 1` (o 16001193: stake 10, devolveu 10). Ler o enum cru
//     marcaria anulada como VITÓRIA. É o inverso da lição da Stake (s257): lá o dinheiro não
//     separava V de L e o enum mandava; aqui o ENUM não separa V de W e o DINHEIRO manda.
//
//   • ODD DE W = RETORNO ÷ STAKE, sempre (`MASTER_RESULTADO §2`). O `Coef` declarado explica o
//     retorno ao centavo em 15 de 15, mas diverge na 5ª casa (4,14164 × 4,14166667) — e regra
//     global não se negocia por arquivo de casa. Em L/V/aberta vale a odd estrutural.
//
//   • `CoefView` É TRUNCADA, não arredondada: `14.704694` vira `"14.704"` (arredondar daria
//     14,705). É o número que o card estampa — conferido contra a tela do operador:
//     `Cotação geral 7,722 · Possíveis ganhos R$ 1.390,03` ⇄ `Coef 7.7224`, `BetSum 180`,
//     `PossibleWinSum 1390.03`. A exata é sempre a `Coef` (odd nunca truncada é primordial).
//
//   • `PossibleWinSum` E `WinSum` NUNCA COEXISTEM — 10 abertas têm só o potencial, 15 ganhas
//     têm só o real, 66 perdidas não têm nenhum. A vitória fantasma da VaideBet/Novibet/
//     Betpix365 **não** é risco aqui; medido, não suposto.
//
//   • DATA: `UnixGameStartDate` == o MAIOR `StartDate` das pernas em 91 de 91 — a casa já
//     entrega "evento mais recente" pronto, que é a convenção da coluna Data. Epoch em
//     segundos → America/Sao_Paulo.
//
//   • FIM AUTORITATIVO DE VERDADE: `BetsSummaryInfo.Count` é o total da JANELA e **não muda**
//     com o `Count` pedido — medido ao vivo: `Count:10` devolveu 10 bilhetes e seguiu dizendo
//     `Count: 95`. Distingue "acabou" de "a consulta encheu", que é exatamente o que o `Count`
//     da Tivo NÃO distinguia (s211).
//
//   • NÃO HÁ PAGINAÇÃO. Não existe `skip`/`page`/`offset`: os únicos controles são `Count` e a
//     janela `DateFrom`/`DateTo`. Quando o lote vem menor que o `BetsSummaryInfo.Count`, o
//     único movimento possível é **pedir um `Count` maior** — e é isso que o inject escala.
//
//   • A TELA É ESTREITA: a página pede uma janela FIXA de ~5,2 dias e reconsulta a mesma
//     janela a cada ~5 segundos, para sempre. Um passivo perfeito pegaria 91 bilhetes e nunca
//     saberia dos outros 4. O replay existe para ALARGAR a janela, como na Novibet (s271).
//
//   • O PASSIVO FUNCIONA (ao contrário de Pitaco e Novibet): o `clone().text()` da resposta
//     resolveu limpo nas 34 capturas do recon, zero `erroLeitura`. O hook lê o que a página
//     recebe E o replay busca o resto.
//
// ── NÃO COBERTO por esta fixture (a conta tinha 95 bilhetes, quase todos do mesmo perfil) ──
//   • bilhete de SISTEMA — `BetSystemType` só apareceu como 1 (simples) e 3 (acumulador);
//     não há Trixie/Yankee/Patent, então a 12ª coluna `Sistema` não é exercitada aqui;
//   • CASHOUT (`CalculateSaleInfo:false` na requisição da página, `OnlyBetsForSale:false`);
//   • BOOST de qualquer natureza — nenhum bilhete com `Coef` acima do produto por promoção;
//   • FREEBET, meia-liquidação (HW/HL) e imposto retido;
//   • bilhete com mais de 3 pernas (90 dos 91 têm exatamente 3, 1 tem 1);
//   • profundidade de histórico além de 12 meses — a casa devolveu 95 em 365 dias e não se
//     provou o teto real, nem se existe corte silencioso mais atrás.
import { rodarInject, carregarContent, fixture, linha } from "../sandbox.mjs";

export const casa = "1xBet";

// BetId → o que a CASA mostra / o que o payload sustenta.
//   stake  = `BetSum`
//   odd    = W → `WinSum ÷ BetSum` · L/V/aberta → odd ESTRUTURAL (produto das pernas quando o
//            `Coef` está velho por anulação; `Coef` no resto)
//   evento = `UnixGameStartDate` em America/Sao_Paulo
const ESPERADO = {
  // ── GANHA com perna anulada: a casa recalculou o Coef (4,14164 == produto). A odd que vale
  //    é a do dinheiro: 621,25 ÷ 150. Diverge do Coef na 5ª casa, e o global manda.
  "16108953": { stake: "150,00", odd: "4,14166667", evento: "26/08/2026 14:00:00",
                colocada: "25/08/2026 16:24:34", sels: 3, status: /^Ganhou → W$/, retorno: "621,25" },

  // ── PERDIDA com perna anulada: o Coef ficou PRÉ-anulação (8,607956). A estrutura real é
  //    2,11 × 1 × 2,17 = 4,5787. É o bilhete-chave desta casa.
  "16101007": { stake: "150,00", odd: "4,5787", evento: "26/08/2026 07:00:00",
                colocada: "25/08/2026 10:00:17", sels: 3, status: /^Perdeu → L$/, retorno: null },

  // ── PERDIDA com DUAS pernas anuladas: Coef 9,771938 contra produto 2,375 (4×).
  "16061009": { stake: "150,00", odd: "2,375", evento: "23/08/2026 13:00:00",
                colocada: "23/08/2026 09:43:29", sels: 3, status: /^Perdeu → L$/, retorno: null },

  // ── PERDIDA com uma anulada: 23,0652 contra 7,74 (3×).
  "16100981": { stake: "120,00", odd: "7,74", evento: "25/08/2026 15:45:00",
                colocada: "25/08/2026 09:58:40", sels: 3, status: /^Perdeu → L$/, retorno: null },

  // ── A ANULADA disfarçada de ganha: status 4, mas WinSum == BetSum e Coef 1. TEM de sair V.
  //    Se este caso ficar verde marcando W, a casa está inflando lucro em toda anulação.
  "16001193": { stake: "10,00", odd: "1", evento: "23/08/2026 16:00:00",
                colocada: "21/08/2026 14:30:47", sels: 1, status: /^Anulada → V$/, retorno: "10,00" },

  // ── PERDIDA limpa, sem anulação: o Coef vale como está. Guarda contra "corrigir" o que não
  //    está quebrado — o produto em float dá 14,70469392 e a casa diz 14,704694.
  "16119951": { stake: "150,00", odd: "14,704694", evento: "26/08/2026 21:30:00",
                colocada: "26/08/2026 09:54:15", sels: 3, status: /^Perdeu → L$/, retorno: null },

  // ── ABERTA: o retorno é POTENCIAL e o card confirma (Cotação geral 7,722 · R$ 1.390,03).
  "16131833": { stake: "180,00", odd: "7,7224", evento: "27/08/2026 16:00:00",
                colocada: "26/08/2026 19:03:33", sels: 3, status: /^Em aberto/, retorno: null,
                potencial: "1390,03" },
};

const URL_LISTA = "https://1xbet.bet.br/service/bethistory/GetBetInfoHistoryWithSummaryByDates";

// Os headers que a página envia. Note a AUSÊNCIA de `Authorization` — a auth é por cookie, e o
// `credentials:"include"` do inject é o que a carrega. Os `x-location-*` que a casa manda
// ficam de fora de propósito: são a geolocalização de quem coletou, e o recon os redige
// (foi essa fixture que expôs essa terceira família de PII — ver `tools/recon_casa.js`).
const HEADERS = {
  "accept": "application/json",
  "content-type": "application/json",
  "x-language": "pt_BR",
};

export async function rodar() {
  const payload = JSON.parse(fixture("1xbet.bethistory.json"));
  const TODOS = payload.BetInfos;
  const TOTAL = TODOS.length;                       // 91

  // O corpo REAL da página (recon s298), com a janela estreita que obriga o replay a existir:
  // DateFrom/DateTo distam 5,22 dias. `BonusUserId` vem redigido na fixture do request.
  const DIA = 86400;
  const AGORA = Math.floor(Date.parse("2026-08-26T22:07:19Z") / 1000);
  const corpoInicial = JSON.stringify({
    BonusUserId: 1644491, CalculateSaleInfo: false, CalculateSummaryInfo: true, CfView: 3,
    Count: 1000, DateFrom: AGORA - Math.round(5.22 * DIA), DateTo: AGORA, IsTerminal: false,
    Language: "pt", OnlyBetsForSale: false, PartnerGroupId: 123, PartnerId: 394,
    UseArchive: true, Whence: 55,
  });

  const pedidos = [];
  // TETO ARTIFICIAL de 40 por resposta, MENOR que qualquer `Count` que o inject peça: é assim
  // que se prova que ele percebe o lote curto (`len < BetsSummaryInfo.Count`) e ESCALA o
  // `Count` em vez de aceitar o que veio. A casa real não faz isso — o teto aqui é o teste.
  const TETO_SIMULADO = 40;
  const responder = (url, opts) => {
    if (!String(url).includes("/service/bethistory/GetBetInfoHistoryWithSummaryByDates")) return null;
    let corpo = {};
    try { corpo = JSON.parse((opts && opts.body) || "{}"); } catch (e) { corpo = {}; }
    pedidos.push(corpo);
    const dias = ((corpo.DateTo || 0) - (corpo.DateFrom || 0)) / DIA;
    // A janela estreita da própria página só enxerga os bilhetes recentes.
    const universo = dias > 30 ? TODOS : TODOS.slice(0, 60);
    // Escalada: o `Count` pedido é respeitado, mas o teto simulado corta antes.
    const quantos = Math.min(corpo.Count || 0, TETO_SIMULADO * Math.ceil((corpo.Count || 1) / 1000), universo.length);
    return JSON.stringify({
      BetsSummaryInfo: Object.assign({}, payload.BetsSummaryInfo, { Count: universo.length }),
      BetInfos: universo.slice(0, quantos),
    });
  };

  const { ultima, urls } = await rodarInject({
    inject: "x1_inject.js",
    href: "https://1xbet.bet.br/pt/office/bets-history",
    urlInicial: URL_LISTA,
    optsInicial: { method: "POST", headers: HEADERS, body: corpoInicial },
    pedido: "__sharpenupX1Req",
    responder,
    ms: 900,
  });

  const falhas = [];
  if (!ultima) return { falhas: ["o inject não emitiu nenhuma mensagem"], testes: 0 };

  // ── heartbeat do autodiagnóstico ──
  if (!ultima.hook) falhas.push("o inject não emitiu `hook:true` (autodiagnóstico cego)");
  if (typeof ultima.respostas !== "number" || ultima.respostas < 1) {
    falhas.push(`\`respostas\` ausente ou zerado (veio ${ultima.respostas})`);
  }
  if (!ultima.fim) falhas.push("o inject não sinalizou `fim` (o robô ficaria esperando o teto)");

  // ── o replay tem de ALARGAR a janela ──
  // É a razão de este inject existir: a tela pede 5,2 dias e reconsulta ela para sempre.
  const largos = pedidos.filter((p) => ((p.DateTo || 0) - (p.DateFrom || 0)) / DIA > 30);
  if (!largos.length) {
    falhas.push("o replay nunca alargou a janela — capturaria só os ~5 dias que a tela pede");
  } else {
    const dias = ((largos[0].DateTo || 0) - (largos[0].DateFrom || 0)) / DIA;
    if (dias < 300) falhas.push(`replay pediu janela de ${Math.round(dias)} dia(s); a casa serve 12 meses`);
    // Campos de canal/tenant que o replay NÃO controla têm de viajar intactos.
    for (const k of ["PartnerId", "PartnerGroupId", "Whence", "CfView", "BonusUserId", "UseArchive"]) {
      if (largos[0][k] === undefined) falhas.push(`o replay perdeu o campo \`${k}\` do corpo original`);
    }
  }

  // ── escalada do Count: o lote veio curto, o inject tem de pedir mais ──
  if (largos.length < 2) {
    falhas.push("o inject aceitou um lote menor que `BetsSummaryInfo.Count` sem escalar o `Count`");
  } else {
    const counts = largos.map((p) => p.Count || 0);
    if (!(counts[counts.length - 1] > counts[0])) {
      falhas.push(`o \`Count\` não escalou entre as tentativas (${counts.join(" → ")})`);
    }
  }

  // ── cobertura: nada perdido, nada repetido ──
  const bilhetes = ultima.bilhetes || [];
  if (bilhetes.length !== TOTAL) falhas.push(`esperava ${TOTAL} bilhetes normalizados, vieram ${bilhetes.length}`);
  const refs = bilhetes.map((b) => b.ref);
  if (new Set(refs).size !== refs.length) falhas.push("o inject devolveu códigos repetidos");

  // ── os blocos que a IA vai ler ──
  const fmt = carregarContent().pegar("formatTicket1X");
  let testes = 0;
  for (const b of bilhetes) {
    const e = ESPERADO[b.ref];
    if (!e) continue;
    testes++;
    const txt = fmt(b);
    if (!txt.startsWith(`[Código: ${b.ref}]`)) falhas.push(`${b.ref}: marcador [Código:] ausente/errado`);

    const stake = linha(txt, "Stake:");
    if (stake !== e.stake) falhas.push(`${b.ref}: stake esperado ${e.stake}, veio "${stake}"`);

    const odd = linha(txt, "Odd:");
    if (odd !== e.odd && odd !== `${e.odd} (= Retorno ÷ Stake)`) {
      falhas.push(`${b.ref}: odd esperada ${e.odd}, veio "${odd}"`);
    }

    const status = linha(txt, "Status:");
    if (!e.status.test(status)) falhas.push(`${b.ref}: status "${status}"`);

    const evento = linha(txt, "Data (evento):");
    if (evento !== e.evento) falhas.push(`${b.ref}: data de evento esperada ${e.evento}, veio "${evento}"`);

    const colocada = linha(txt, "Colocada:");
    if (colocada !== e.colocada) falhas.push(`${b.ref}: colocação esperada ${e.colocada}, veio "${colocada}"`);

    // O status CRU tem de subir junto — é ele que a CASA_1XBET.md traduz, e é o que permite
    // reconhecer um valor novo (cashout, meia-liquidação) em vez de chutá-lo.
    if (!linha(txt, "Status (API):")) falhas.push(`${b.ref}: linha "Status (API):" ausente`);

    // Retorno REAL só em bilhete resolvido; em aberto tem de vir rotulado como POTENCIAL.
    if (e.retorno) {
      const r = linha(txt, "Retorno:");
      if (r !== `R$ ${e.retorno}`) falhas.push(`${b.ref}: retorno esperado R$ ${e.retorno}, veio "${r}"`);
    }
    if (e.potencial) {
      const pot = linha(txt, "Retorno potencial:");
      if (!pot || !pot.includes(e.potencial)) {
        falhas.push(`${b.ref}: retorno potencial esperado ${e.potencial}, veio "${pot}"`);
      }
      if (linha(txt, "Retorno:")) falhas.push(`${b.ref}: bilhete ABERTO emitiu "Retorno:" — vitória fantasma`);
    }

    // As seleções precisam estar todas no bloco, senão a descrição sai truncada.
    const nSel = (txt.match(/^\s+\d+\. /gm) || []).length;
    if (nSel !== e.sels) falhas.push(`${b.ref}: esperava ${e.sels} seleção(ões) no bloco, vieram ${nSel}`);
  }

  // ── varredura global: nenhuma anulada pode ter escapado como W ──
  // Regra medida: status 4 com `WinSum == BetSum` é V, não W. Como só 1 dos 91 bilhetes cai
  // aqui, um defeito nessa regra passaria despercebido numa amostra pequena — por isso a
  // conferência varre TODOS.
  let vs = 0;
  for (const b of bilhetes) {
    const txt = fmt(b);
    if (/^Status: Anulada → V$/m.test(txt)) vs++;
  }
  if (vs !== 1) falhas.push(`esperava exatamente 1 anulada (V) nos ${TOTAL} bilhetes, o formatador marcou ${vs}`);
  testes++;

  // ── nenhum bilhete pode sair sem odd ou sem data (a linha inteira seria rejeitada) ──
  for (const b of bilhetes) {
    const txt = fmt(b);
    if (!linha(txt, "Odd:")) falhas.push(`${b.ref}: bloco sem "Odd:"`);
    if (!linha(txt, "Data (evento):")) falhas.push(`${b.ref}: bloco sem "Data (evento):"`);
  }
  testes++;

  // ── HOMÓGLIFOS CIRÍLICOS: nenhum pode sobreviver até o bloco ──
  // A casa mistura cirílico no próprio dicionário — medido na fixture: `Handiсap … Sets`
  // (`с` = U+0441) em 3 pernas, `Superсopa - Alemanha` num campeonato e o clube francês
  // `АС Lorient` com as DUAS letras cirílicas. São idênticos aos latinos na tela e diferentes
  // como string: `АС Lorient` nunca casaria com `AC Lorient` em dedup nem em descrição, e nada
  // acusaria. Esta varredura é o único lugar onde o defeito é visível.
  let comCirilico = 0, achouHandicap = false, achouLorient = false;
  for (const b of bilhetes) {
    const txt = fmt(b);
    if (/[Ѐ-ӿ]/.test(txt)) comCirilico++;
    if (/Handicap 1 \(-2\.5\) Sets/.test(txt)) achouHandicap = true;
    if (/AC Lorient/.test(txt)) achouLorient = true;
  }
  if (comCirilico) falhas.push(`${comCirilico} bloco(s) ainda com caractere cirílico — o homóglifo passou`);
  if (!achouHandicap) falhas.push('"Handicap 1 (-2.5) Sets" não saiu em latim (o `с` cirílico não foi normalizado)');
  if (!achouLorient) falhas.push('"AC Lorient" não saiu em latim (o `АС` cirílico não foi normalizado)');
  testes += 3;

  if (urls.length < 2) falhas.push(`replay não rodou (só ${urls.length} requisição(ões))`);

  return { falhas, testes };
}
