// Betfair (Sportsbook) — captura por API `POST /activity/sportsbook` (s193/s195/s197).
//
// Trava as leituras que já custaram caro nesta casa, cruzando o JSON com o canon
// (`casas/CASA_BETFAIR.md`, `global/MASTER_RESULTADO_2026.md`) — não com o que o código faz:
//
//   • DATA: a casa trocou "18-jul-26" por "18-jul.-26" (mês abreviado COM PONTO) em
//     25/07/2026 e o `_dbrBF` parou de casar → Data vazia em 100% dos bilhetes. Como Data é
//     a 1ª coluna do TSV, o `parse_tsv` deslocava tudo e o /salvar rejeitava o lote inteiro
//     em silêncio: 5 dias sem entrar (s193). As datas abaixo são a regressão desse fix.
//   • EACH WAY: `status:"PLACED"` NÃO é aposta em aberto — é o desfecho "colocou", e o
//     bilhete está liquidado (`result:"SETTLED"` + `settledDate`). Decide o §5 financeiro:
//     Ganhos(530) > Apostado(200) → W, odd = Retorno÷Stake = 2,65 (s195).
//   • CASH OUT: o `status` é INÚTIL — o mesmo desfecho vem "LOST" no 1821 e "WON" no 1807,
//     ambos com Cash Out == Stake. Quem decide é o dinheiro (§5.1.2): **V**, com a odd
//     EXIBIDA. Antes saía "Odd total: 1" e a IA gravava W/odd 1 (s197).
//   • ABERTA (`status:"OPEN"`, `settledDate:""`): Resultado VAZIO, retorno é POTENCIAL e
//     nunca decide W, odd = a exibida (§1.1). Data fica VAZIA de propósito — a coluna Data
//     É a resolução (§4.A) e ela ainda não existe; o UPSERT preenche quando liquidar.
//   • L usa a odd EXIBIDA (Retorno é 0) · múltipla DBL sem `combinedOdds` usa Retorno÷Stake.
//
// NÃO existe checagem genérica de "Apostado em != Data": a maioria dos bilhetes é colocada
// e liquidada no MESMO dia, então a igualdade é legítima e o teste só dava falso positivo.
// Quem discrimina colocação × resolução é o 1772 (colocado 17/07, liquidado 18/07 → 18/07).
import { rodarInject, carregarContent, fixture, linha } from "../sandbox.mjs";

export const casa = "Betfair";

// data = settledDate (§4.A) · odd/status conforme §5 e §1.1.
const ESPERADO = {
  // ── fixture 1: página com o Each Way ──────────────────────────────────────
  "O/25146258/0001772": { data: "18/07/2026", status: /→ W/,       odd: "2,65",  nota: "Each Way colocado: §5 financeiro manda W" },
  "O/25146258/0001771": { data: "17/07/2026", status: /^LOST → L/, odd: "1,9" },
  "O/25146258/0001770": { data: "17/07/2026", status: /^LOST → L/, odd: "2,65" },
  "O/25146258/0001769": { data: "17/07/2026", status: /^WON → W/,  odd: "1,725", nota: "DBL sem combinedOdds: Retorno÷Stake" },
  "O/25146258/0001768": { data: "17/07/2026", status: /^WON → W/,  odd: "2,5" },
  "O/25146258/0001767": { data: "17/07/2026", status: /^LOST → L/, odd: "10" },
  "O/25146258/0001766": { data: "15/07/2026", status: /^LOST → L/, odd: "4,5" },
  "O/25146258/0001765": { data: "15/07/2026", status: /Cash Out \(total\) → V/, odd: "2,1", cashout: "301.00",
                          nota: "Cash Out == Stake → V com a odd exibida, nunca odd 1" },
  "O/25146258/0001764": { data: "15/07/2026", status: /^LOST → L/, odd: "2,8" },
  "O/25146258/0001763": { data: "15/07/2026", status: /^LOST → L/, odd: "2,9" },

  // ── fixture 2: página mais recente (cashout com status LOST) ──────────────
  "O/25146258/0001823": { data: "25/07/2026", status: /^LOST → L/, odd: "8" },
  "O/25146258/0001822": { data: "26/07/2026", status: /^LOST → L/, odd: "2,5" },
  "O/25146258/0001821": { data: "25/07/2026", status: /Cash Out \(total\) → V/, odd: "5,5", cashout: "201.00",
                          nota: "status diz LOST, mas Cash Out == Stake → V (o Feca confirmou: desistiu da aposta)" },
  "O/25146258/0001820": { data: "25/07/2026", status: /^WON → W/,  odd: "2" },
  "O/25146258/0001819": { data: "25/07/2026", status: /^LOST → L/, odd: "1,9" },
  "O/25146258/0001818": { data: "25/07/2026", status: /^WON → W/,  odd: "1,83" },
  "O/25146258/0001817": { data: "25/07/2026", status: /^LOST → L/, odd: "5" },
  "O/25146258/0001816": { data: "25/07/2026", status: /^LOST → L/, odd: "3,3" },
  "O/25146258/0001815": { data: "25/07/2026", status: /^LOST → L/, odd: "2,3" },
  "O/25146258/0001813": { data: "25/07/2026", status: /^WON → W/,  odd: "1,65" },

  // ── fixture 3: VOID, o outro cashout (status WON) e a DBL com freebet ─────
  "O/25146258/0001812": { data: "25/07/2026", status: /^LOST → L/, odd: "4,33" },
  "O/25146258/0001811": { data: "25/07/2026", status: /^VOID → V/, odd: "5",
                          nota: "void devolve a stake: odd exibida, nunca Retorno÷Stake" },
  "O/25146258/0001810": { data: "25/07/2026", status: /^WON → W/,  odd: "2,7" },
  // ⚠️ DECISÃO EM ABERTO (ver STATUS s197): a odd sai de Retorno÷Stake, que é a regra
  // global do W, e por isso carrega o ruído do arredondamento ao centavo (4,50002999 em vez
  // dos 4.50 que a casa exibe — 4,50 × 166,75 = 750,375 → 750,38, ou seja a exibida
  // EXPLICA o retorno). Já o 1806 exibe 1,83 e 1,83 × 300 = 549 ≠ 550: ali a exibida NÃO
  // explica e o dinheiro tem de mandar. O `CASA_BETFAIR §6` diz que na Betfair a odd
  // exibida é autoritativa para W (não há boost) — o que apontaria para 4,5 aqui. Enquanto
  // o Feca não decidir, a fixture trava a regra ATUAL (dinheiro sempre), sem prejulgar.
  "O/25146258/0001809": { data: "25/07/2026", status: /^WON → W/,  odd: "4,50002999" },
  "O/25146258/0001808": { data: "24/07/2026", status: /^WON → W/,  odd: "10" },
  "O/25146258/0001807": { data: "24/07/2026", status: /Cash Out \(total\) → V/, odd: "10", cashout: "324.24",
                          nota: "status diz WON e mesmo assim é V — prova que o rótulo não serve em cashout" },
  // Aqui a exibida (1,83) NÃO explica o retorno (1,83 × 300 = 549 ≠ 550) → o dinheiro manda,
  // sem controvérsia: 550 ÷ 300 = 1,83333333.
  "O/25146258/0001806": { data: "24/07/2026", status: /^WON → W/,  odd: "1,83333333" },
  "O/25146258/0001805": { data: "24/07/2026", status: /^WON → W/,  odd: "2,8" },
  "O/25146258/0001804": { data: "24/07/2026", status: /^LOST → L/, odd: "4,5", nota: "DBL perdida: produto das pernas 2,25×2" },
  "O/25146258/0001803": { data: "24/07/2026", status: /^WON → W/,  odd: "2,25" },

  // ── fixture ABERTA ────────────────────────────────────────────────────────
  "O/25146258/0001824": { data: "", status: /em aberto/, odd: "2,65", aberta: true },
  "O/25146258/0001814": { data: "", status: /em aberto/, odd: "5,5",  aberta: true },
};

async function colher(arquivo, chave) {
  const corpo = fixture(arquivo);
  const { ultima } = await rodarInject({
    inject: "bf_inject.js",
    href: "https://myactivity.betfair.bet.br/sportsbook",
    urlInicial: "https://myactivity.betfair.bet.br/activity/sportsbook",
    pedido: "__sharpenupBFReq",
    responder: (url) => (url.includes("sportsbook") ? corpo : null),
  });
  return { ultima, lista: (ultima && ultima[chave]) || [] };
}

// Servidor de mentira que responde pelo `status` e pelo ÍNDICE do corpo, como a casa faz.
// É isto que permite provar (a) que a paginação avança de verdade e (b) que uma aba busca a
// outra sozinha — as duas queixas do Feca na s198: "trouxe 22 e eu pedi 100" e "não vem
// abertas + encerradas juntas".
function servidor() {
  const p0 = JSON.parse(fixture("betfair.settled2.json"));   // rangeStart 0  · more:true
  const p1 = JSON.parse(fixture("betfair.settled3.json"));   // rangeStart 10 · more:true
  const ab = fixture("betfair.open.json");
  const pedidos = [];
  const resp = (url, opts) => {
    const body = String((opts && opts.body) || "");
    pedidos.push(body);
    if (!url.includes("sportsbook")) return null;
    if (/"status"\s*:\s*"OPEN"/i.test(body)) return ab;
    const m = /"fromRecord"\s*:\s*(\d+)/i.exec(body);
    const idx = m ? Number(m[1]) : 0;
    if (idx === 0) return JSON.stringify(p0);
    if (idx === 10) return JSON.stringify({ ...p1, moreAvailable: false, nextPageIndex: null });
    return JSON.stringify({ ...p1, bets: [], moreAvailable: false, nextPageIndex: null });
  };
  return { resp, pedidos };
}

// Corpo que a página emite ao abrir CADA aba (formato real, colado do console do Feca).
const CORPO_ABERTA = '{"status":"OPEN","dateFilter":0,"fromRecord":0,"pageSize":10,"oddsType":"decimal"}';
const CORPO_RESOLVIDA = '{"status":"SETTLED","dateFilter":"90","fromRecord":0,"pageSize":10,"oddsType":"decimal"}';

async function umClique(corpoInicial) {
  const srv = servidor();
  const { ultima } = await rodarInject({
    inject: "bf_inject.js",
    href: "https://myactivity.betfair.bet.br/sportsbook",
    urlInicial: "https://myactivity.betfair.bet.br/activity/sportsbook",
    pedido: "__sharpenupBFReq",
    corpoInicial: corpoInicial,
    ms: 900,
    responder: srv.resp,
  });
  return { ultima, pedidos: srv.pedidos };
}

export async function rodar() {
  const falhas = [];
  const fmt = carregarContent().pegar("formatTicketBF");
  let testes = 0;

  const fontes = [
    { arq: "betfair.settled.json",  chave: "bets",    n: 10 },
    { arq: "betfair.settled2.json", chave: "bets",    n: 10 },
    { arq: "betfair.settled3.json", chave: "bets",    n: 10 },
    { arq: "betfair.open.json",     chave: "abertas", n: 2  },
  ];

  for (const f of fontes) {
    const { ultima, lista } = await colher(f.arq, f.chave);
    if (!ultima) { falhas.push(`${f.arq}: o inject não emitiu nenhuma mensagem`); continue; }
    if (!ultima.hook) falhas.push(`${f.arq}: o inject não sinalizou 'hook'`);
    if (lista.length !== f.n) falhas.push(`${f.arq}: esperava ${f.n} em '${f.chave}', vieram ${lista.length}`);

    // A lista ABERTA não pode contaminar o canal das encerradas — é o que garante que
    // ligar as abertas não mexe na paginação/fim das resolvidas.
    if (f.chave === "abertas" && (ultima.bets || []).length)
      falhas.push(`${f.arq}: resposta OPEN vazou para 'bets' (${ultima.bets.length}) — contaminaria as encerradas`);

    for (const b of lista) {
      const e = ESPERADO[b.betId];
      if (!e) { falhas.push(`bilhete inesperado na fixture: ${b.betId}`); continue; }
      const txt = fmt(b);
      testes++;
      const id = b.betId.slice(-4);

      if (!txt.startsWith(`[Código: ${b.betId}]`)) falhas.push(`${id}: marcador [Código:] ausente/errado`);

      const data = linha(txt, "Data:");
      if (data !== e.data) falhas.push(`${id}: data esperada "${e.data}", veio "${data}"`);

      const status = linha(txt, "Status:");
      if (!e.status.test(status)) falhas.push(`${id}: status "${status}"` + (e.nota ? ` — ${e.nota}` : ""));

      if (e.odd != null) {
        const odd = linha(txt, "Odd total:").split(" ")[0];
        if (odd !== e.odd) falhas.push(`${id}: odd esperada ${e.odd}, veio "${odd}"` + (e.nota ? ` — ${e.nota}` : ""));
      }
      if (e.cashout != null) {
        const co = linha(txt, "Cash Out:");
        if (co !== e.cashout) falhas.push(`${id}: linha "Cash Out:" esperada ${e.cashout}, veio "${co}"`);
      }
      if (e.aberta) {
        // §1.1: o retorno de uma aberta é POTENCIAL e não pode ser lido como realizado.
        if (!/POTENCIAL/.test(status)) falhas.push(`${id}: aberta sem rótulo "Retorno POTENCIAL" — a IA pode ler como vitória`);
        if (/→ [WLV]\b/.test(status)) falhas.push(`${id}: aberta recebeu código de resultado — §1.1 proíbe`);
      }
    }
  }

  // ── UM CLIQUE = as duas listas, partindo de QUALQUER aba (s199) ───────────────
  // Antes: o contexto do replay ficava preso na 1ª requisição (a da aba Aberta), o
  // `paginarLoop` repaginava a lista errada, morria na 1ª volta e o `finally` marcava
  // `fimReal` — o que impedia o robô de sequer rolar. Resultado: 22 encerradas quando o
  // operador pediu 100, e nunca as duas listas juntas.
  for (const [rotulo, corpo] of [["aba Resolvida", CORPO_RESOLVIDA], ["aba Aberta", CORPO_ABERTA]]) {
    const { ultima, pedidos } = await umClique(corpo);
    testes++;
    if (!ultima) { falhas.push(`${rotulo}: o inject não emitiu nenhuma mensagem`); continue; }
    const nEnc = (ultima.bets || []).length;
    const nAb = (ultima.abertas || []).length;
    // 2 páginas de 10 = 20 encerradas; a 2ª só chega se a paginação ATIVA funcionar.
    if (nEnc !== 20) falhas.push(`${rotulo}: esperava 20 encerradas (2 páginas), vieram ${nEnc} — paginação ativa não avançou`);
    if (nAb !== 2) falhas.push(`${rotulo}: esperava 2 abertas no mesmo clique, vieram ${nAb}`);
    if (!ultima.fim) falhas.push(`${rotulo}: não sinalizou fim ao esgotar a lista`);
    // A 2ª página tem de ser pedida com fromRecord=10 E pageSize intacto (o replay antigo
    // sobrescrevia o pageSize junto com o índice quando os dois valiam 10).
    const p2 = pedidos.find((b) => /"fromRecord"\s*:\s*10/.test(b));
    if (!p2) falhas.push(`${rotulo}: nenhuma requisição pediu a 2ª página (fromRecord:10)`);
    else if (!/"pageSize"\s*:\s*10/.test(p2)) falhas.push(`${rotulo}: pageSize foi sobrescrito junto com o índice → ${p2}`);
  }

  return { falhas, testes };
}
