// SapphireBet (sbethub2365.com) — ESPELHO da 1xBet (s391). Mesmo `GetBetInfoHistoryWithSummaryByDates`,
// caminho `/bethistory-api/Web/`, conta em USD. A conferência comum está em `../x1_espelho.mjs`.
//
// Esperados: os simples, as acumuladas 88105920437/88122020225/88152128427 e a 88105891221 foram
// conferidos no CARD da casa (03/10/2026); os dois sistemas e a 88105712275, pelo JSON.
//
// O QUE ESTA FIXTURE TRAZ QUE A DA 1xBet NÃO TINHA:
//   • SISTEMA (`BetTypeId` 2, `BetSystemType` 20203, "2 de 3"). O ganho tem `Coef` e a odd é a do
//     dinheiro (156,96 ÷ 60 = 2,616); o PERDIDO vem SEM `Coef` (`CoefView: ""`), e a odd fica
//     ausente — o produto das pernas não é a odd de um sistema.
//   • acumuladas perdidas com perna anulada (`Coef` 1) e `Coef` pré-anulação — a mesma armadilha
//     da 1xBet, e a 88105712275 ainda traz o homóglifo cirílico "Handiсap".
// NÃO coberto: anulada inteira (está na PariPesa), cashout, boost.
import { conferirEspelho } from "../x1_espelho.mjs";

export const casa = "SapphireBet";

const ESPERADO = {
  "88153060447": { stake: "30,00", odd: "1,909", status: /^Ganhou → W$/, retorno: "57,27", evento: "02/10/2026 13:05:00" },
  "88149777189": { stake: "21,00", odd: "2,17", status: /^Ganhou → W$/, retorno: "45,57", evento: "02/10/2026 01:30:00" },
  "88188771753": { stake: "12,00", odd: "2,15", status: /^Perdeu → L$/, evento: "03/10/2026 01:30:00" },
  "88152128427": { stake: "7,30", odd: "22,409866", status: /^Perdeu → L$/, evento: "02/10/2026 20:45:00" },
  "88122020225": { stake: "7,10", odd: "16,85072", status: /^Perdeu → L$/, evento: "02/10/2026 07:00:00" },
  "88105920437": { stake: "21,00", odd: "7,15666667", status: /^Ganhou → W$/, retorno: "150,29" },
  "88105563743": { stake: "60,00", odd: "2,616", status: /^Ganhou → W$/, retorno: "156,96", tipo: /^Sistema \(3 seleções/ },
  "88092600919": { stake: "12,00", odd: null, status: /^Perdeu → L$/, tipo: /^Sistema \(3 seleções/ },
  "88105891221": { stake: "31,00", odd: "6,2997", status: /^Perdeu → L$/ },
  "88105712275": { stake: "13,00", odd: "8,2401", status: /^Perdeu → L$/ },
  "88179616669": { stake: "21,00", odd: "5,65", status: /^Em aberto/, potencial: "118,65" },
  "88149861391": { stake: "31,00", odd: "2,25", status: /^Em aberto/, potencial: "69,75" },
};

export async function rodar() {
  return conferirEspelho({
    arquivo: "sapphirebet.bethistory.json",
    href: "https://sbethub2365.com/br/office/history",
    url: "https://sbethub2365.com/bethistory-api/Web/GetBetInfoHistoryWithSummaryByDates",
    moeda: "USD",
    esperado: ESPERADO,
    // BetDate 2026-10-02T01:55:15Z → 01/10 22:55:15 em São Paulo.
    carimbo: { ref: "88153060447", valor: "20261001225515" },
  });
}
