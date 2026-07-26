// Betfair (Sportsbook) — captura por API `POST /activity/sportsbook` (s193/s195).
//
// Trava as leituras que já custaram caro nesta casa, cruzando o JSON com o canon
// (`casas/CASA_BETFAIR.md`) — não com o que o código faz hoje:
//   • DATA: a casa mudou de "18-jul-26" para "18-jul.-26" (mês abreviado COM PONTO) em
//     25/07/2026 e o `_dbrBF` parou de casar → Data vazia em 100% dos bilhetes. Como Data
//     é a 1ª coluna do TSV, o `parse_tsv` deslocava tudo e o /salvar rejeitava o lote
//     inteiro em silêncio: 5 dias de bilhetes não entraram (s193). As 10 datas abaixo são
//     a regressão desse fix.
//   • EACH WAY: `status:"PLACED"` NÃO é aposta em aberto — é o desfecho "colocou" de um
//     Each Way, e o bilhete está liquidado (`result:"SETTLED"` + `settledDate`). Quem
//     decide é a conferência financeira do §5: Ganhos(530) > Apostado(200) → **W**, e W
//     manda odd = Retorno ÷ Stake = 2,65. Ler o `status` cru dava "a conferir", o bilhete
//     virava `aberta` e um lucro de R$330 sumia do P/L.
//   • CASH OUT: `fullCashout` com Retorno == Stake. O bloco tem de entregar o valor do
//     Cash Out para a IA aplicar o §7 (CLAUDE.md: cashout == stake → V).
//   • L usa a odd EXIBIDA (`originalOdds.decimal`), nunca Retorno÷Stake (Retorno é 0).
//   • Múltipla (DBL) sem `combinedOdds`: a odd vem de Retorno÷Stake (1380÷800 = 1,725).
//
// NÃO existe checagem genérica de "Apostado em != Data": a maioria dos bilhetes é colocada
// e liquidada no MESMO dia, então a igualdade é legítima e o teste só dava falso positivo.
// Quem discrimina colocação × resolução é o 1772 (colocado 17/07, liquidado 18/07 → 18/07).
import { rodarInject, carregarContent, fixture, linha } from "../sandbox.mjs";

export const casa = "Betfair";

// data = settledDate (§4.A: resolução, nunca `placedDate`) · odd/status conforme §5.
const ESPERADO = {
  "O/25146258/0001772": { data: "18/07/2026", status: /→ W/,        odd: "2,65",  nota: "Each Way colocado: §5 financeiro manda W" },
  "O/25146258/0001771": { data: "17/07/2026", status: /^LOST → L/,  odd: "1,9" },
  "O/25146258/0001770": { data: "17/07/2026", status: /^LOST → L/,  odd: "2,65" },
  "O/25146258/0001769": { data: "17/07/2026", status: /^WON → W/,   odd: "1,725", nota: "DBL sem combinedOdds: Retorno÷Stake" },
  "O/25146258/0001768": { data: "17/07/2026", status: /^WON → W/,   odd: "2,5" },
  "O/25146258/0001767": { data: "17/07/2026", status: /^LOST → L/,  odd: "10" },
  "O/25146258/0001766": { data: "15/07/2026", status: /^LOST → L/,  odd: "4,5" },
  "O/25146258/0001765": { data: "15/07/2026", status: /^Cash Out \(total\)/, cashout: "301.00" },
  "O/25146258/0001764": { data: "15/07/2026", status: /^LOST → L/,  odd: "2,8" },
  "O/25146258/0001763": { data: "15/07/2026", status: /^LOST → L/,  odd: "2,9" },
};

export async function rodar() {
  const corpo = fixture("betfair.settled.json");

  const { ultima } = await rodarInject({
    inject: "bf_inject.js",
    href: "https://myactivity.betfair.bet.br/sportsbook",
    urlInicial: "https://myactivity.betfair.bet.br/activity/sportsbook",
    pedido: "__sharpenupBFReq",
    responder: (url) => (url.includes("sportsbook") ? corpo : null),
  });

  const falhas = [];
  if (!ultima) return { falhas: ["o inject não emitiu nenhuma mensagem"], testes: 0 };
  if (!ultima.hook) falhas.push("o inject não sinalizou `hook` (injeção não reportada)");

  const bets = ultima.bets || [];
  if (bets.length !== 10) falhas.push(`esperava 10 bilhetes na fixture, vieram ${bets.length}`);

  const fmt = carregarContent().pegar("formatTicketBF");
  let testes = 0;
  for (const b of bets) {
    const e = ESPERADO[b.betId];
    if (!e) { falhas.push(`bilhete inesperado na fixture: ${b.betId}`); continue; }
    const txt = fmt(b);
    testes++;
    const id = b.betId.slice(-4);   // sufixo curto, só p/ a mensagem de falha ficar legível

    if (!txt.startsWith(`[Código: ${b.betId}]`)) falhas.push(`${id}: marcador [Código:] ausente/errado`);

    const data = linha(txt, "Data:");
    if (data !== e.data) falhas.push(`${id}: data esperada ${e.data}, veio "${data}"`);

    const status = linha(txt, "Status:");
    if (!e.status.test(status)) {
      falhas.push(`${id}: status "${status}"` + (e.nota ? ` — ${e.nota}` : ""));
    }

    if (e.odd != null) {
      // A odd pode vir seguida de " (= Retorno ÷ Stake)"; compara só o número.
      const odd = linha(txt, "Odd total:").split(" ")[0];
      if (odd !== e.odd) falhas.push(`${id}: odd esperada ${e.odd}, veio "${odd}"` + (e.nota ? ` — ${e.nota}` : ""));
    }

    if (e.cashout != null) {
      const co = linha(txt, "Cash Out:");
      if (co !== e.cashout) falhas.push(`${id}: linha "Cash Out:" esperada ${e.cashout}, veio "${co}"`);
    }
  }
  return { falhas, testes };
}
