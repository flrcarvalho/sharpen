// 1xBit (1xbit1.com) — ESPELHO da 1xBet (s399). Mesmo `GetBetInfoHistoryWithSummaryByDates`,
// caminho `/bethistory-api/Web/`, conta em USDT. A conferência comum está em `../x1_espelho.mjs`.
//
// Recon de 06/10/2026, conta do Feca: 8 bilhetes, todos perdidos. Stake, cotação e status de
// todos conferidos no CARD da casa; a odd da 88346311263 sai do JSON (ver abaixo).
//
// O QUE ESTA FIXTURE TRAZ QUE AS OUTRAS ESPELHO NÃO TINHAM:
//   • TETO DE `Count` (medido ao vivo): `Count:501` volta HTTP 400 "Requested count must be less
//     or equal 500". O `Count:1000` inicial do inject matava o replay e a captura entregava só a
//     janela da tela. O caso roda DUAS vezes: com o teto real (500, a recusa vira o tamanho) e
//     com teto 3, que obriga a partir a janela — os 8 bilhetes caem em menos de 2 h, então só
//     a partição funda os alcança.
//   • acumulada perdida com perna anulada por desistência (`Coef` 1) e `Coef` pré-anulação: o
//     card mostra 33,175; a estrutura é 3,47 × 2,57 = 8,9179 (a armadilha da 1xBet).
//   • o homóglifo cirílico "Handiсap" na 88345477545.
// NÃO coberto: ganha, aberta, anulada inteira, cashout, sistema — a conta não tinha nenhuma.
import { conferirEspelho } from "../x1_espelho.mjs";

export const casa = "1xBit";

const ESPERADO = {
  "88346311263": { stake: "24,50", odd: "8,9179", status: /^Perdeu → L$/ },
  "88345477545": { stake: "50,00", odd: "2,1", status: /^Perdeu → L$/, tipo: /^Simples$/ },
  "88344024423": { stake: "40,00", odd: "2,375", status: /^Perdeu → L$/, tipo: /^Simples$/ },
  "88343782199": { stake: "25,00", odd: "2,75", status: /^Perdeu → L$/, tipo: /^Simples$/ },
  "88342809691": { stake: "20,00", odd: "25,13049", status: /^Perdeu → L$/, tipo: /^Múltipla \(3 seleções\)$/ },
  "88342710499": { stake: "20,00", odd: "17,4105", status: /^Perdeu → L$/ },
  "88342557245": { stake: "20,00", odd: "31,455", status: /^Perdeu → L$/ },
  "88342462855": { stake: "20,00", odd: "11,85597", status: /^Perdeu → L$/ },
};

export async function rodar() {
  const base = {
    arquivo: "1xbit.bethistory.json",
    href: "https://1xbit1.com/br/office/history",
    url: "https://1xbit1.com/bethistory-api/Web/GetBetInfoHistoryWithSummaryByDates",
    moeda: "USDT",
    esperado: ESPERADO,
    // BetDate 1791232665 = 05/10/2026 20:37:45 UTC → 17:37:45 em São Paulo (o card diz 17:37).
    carimbo: { ref: "88342462855", valor: "20261005173745" },
  };
  const falhas = [], porTeto = [500, 3];
  let testes = 0;
  for (const tetoCount of porTeto) {
    const r = await conferirEspelho(Object.assign({}, base, { tetoCount }));
    for (const f of r.falhas) falhas.push(`[teto ${tetoCount}] ${f}`);
    testes += r.testes;
  }
  return { falhas, testes };
}
