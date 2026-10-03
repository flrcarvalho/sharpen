// MegaPari — ESPELHO da 1xBet (s391). `megapari.com` redireciona para espelhos que trocam de
// domínio (`2479527mp.pro` no recon); o endpoint é o mesmo `GetBetInfoHistoryWithSummaryByDates`
// em `/bethistory-api/Web/`, conta em USDT. A conferência comum está em `../x1_espelho.mjs`.
//
// Duas acumuladas GANHAS de 3 pernas: a odd é a do dinheiro (249,24 ÷ 12 = 20,77), não o
// `CoefView` truncado (20.77) nem o `Coef` (20,770335) — regra global, W = Retorno ÷ Stake.
// NÃO coberto: anulada, sistema, cashout, boost.
import { conferirEspelho } from "../x1_espelho.mjs";

export const casa = "MegaPari";

const ESPERADO = {
  "88192410319": { stake: "12,00", odd: "20,77", status: /^Ganhou → W$/, retorno: "249,24" },
  "88192397289": { stake: "10,00", odd: "14,837", status: /^Ganhou → W$/, retorno: "148,37" },
  "88193645821": { stake: "19,00", odd: "7,4784", status: /^Perdeu → L$/ },
  "88237330413": { stake: "5,20", odd: "2,08", status: /^Em aberto/, potencial: "10,82" },
};

export async function rodar() {
  return conferirEspelho({
    arquivo: "megapari.bethistory.json",
    href: "https://2479527mp.pro/br/office/history",
    url: "https://2479527mp.pro/bethistory-api/Web/GetBetInfoHistoryWithSummaryByDates",
    moeda: "USDT",
    esperado: ESPERADO,
    // BetDate 1790971858 = 2026-10-02T20:10:58Z → 17:10:58 em São Paulo.
    carimbo: { ref: "88192410319", valor: "20261002171058" },
  });
}
