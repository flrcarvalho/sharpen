// PariPesa (paripesa.com) — ESPELHO da 1xBet (s391). Mesmo `GetBetInfoHistoryWithSummaryByDates`,
// caminho `/bethistory-api/Web/`, conta em USDT. A conferência comum está em `../x1_espelho.mjs`.
//
// O bilhete-chave é a ANULADA: `BetStatus` 4 (o enum de "ganha"), `Coef` 1 e `WinSum` igual à
// stake (7 USDT), com a perna dizendo "Formato do jogo alterado". Tem de sair V — é a mesma regra
// da 1xBet, provada aqui em USDT. Acumulador nesta casa vem com `BetSystemType` 2 (na 1xBet, 3):
// o formatador decide por `BetTypeId`, e este caso trava isso.
// NÃO coberto: sistema (está na SapphireBet), cashout, boost.
import { conferirEspelho } from "../x1_espelho.mjs";

export const casa = "PariPesa";

const ESPERADO = {
  "88194620599": { stake: "7,00", odd: "1", status: /^Anulada → V$/, retorno: "7,00" },
  "88194577145": { stake: "8,40", odd: "2", status: /^Perdeu → L$/ },
  "88195014537": { stake: "10,00", odd: "12,9536", status: /^Perdeu → L$/, tipo: /^Múltipla \(2 seleções\)$/ },
  "88237452875": { stake: "5,20", odd: "2,08", status: /^Em aberto/, potencial: "10,82" },
};

export async function rodar() {
  return conferirEspelho({
    arquivo: "paripesa.bethistory.json",
    href: "https://paripesa.com/br/office/history",
    url: "https://paripesa.com/bethistory-api/Web/GetBetInfoHistoryWithSummaryByDates",
    moeda: "USDT",
    esperado: ESPERADO,
    // A anulada: tem linha de dinheiro, então o controle em BRL prova o "R$" de volta.
    // BetDate 1790974851 = 2026-10-02T21:00:51Z → 18:00:51 em São Paulo.
    carimbo: { ref: "88194620599", valor: "20261002180051" },
  });
}
