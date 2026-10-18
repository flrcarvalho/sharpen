// MelBet (melbet.com) — ESPELHO da 1xBet (s420). A 5ª da família, depois de SapphireBet,
// PariPesa, Megapari e 1xBit. A conferência comum está em `../x1_espelho.mjs`.
//
// ⚠ LIGADA SEM RECON DE CONTA. Ninguém aqui tinha conta na MelBet em 18/10/2026, e o Claude in
// Chrome barra o domínio. O que foi MEDIDO, por fora e sem login:
//   • `melbet.com` responde do Brasil (200, redireciona para `/en`, serve `/br` e `/pt`);
//   • o app é o MESMO `sys-v3-host-app` das quatro espelho medidas (bundle
//     `sys-v3-host-app-static/Desktop/Melbet/entry-*.js`; SapphireBet e PariPesa servem
//     `Desktop/Other`, Megapari `Desktop/Megapari`, 1xBit `Desktop/DefaultBit`);
//   • o único bilhete da casa na base (print, `codigo_ocr`) tem código `88772424445`: 11
//     dígitos, a mesma série de `BetId` da família.
// O que NÃO foi medido: o caminho da API (as quatro do mesmo app usam `/bethistory-api/Web/`, e
// o `RX` do inject casa também o `/service/bethistory/` da 1xBet), o teto de `Count`, a moeda
// que a conta manda, o fuso do `BetDate` e o comportamento do `Coef` na perdida com anulação.
//
// POR ISSO A FIXTURE É EMPRESTADA: é a da PariPesa (recon de 03/10/2026, conferida no card),
// servida no endereço da MelBet. Este caso trava a LIGAÇÃO (o inject casa o caminho no domínio
// da MelBet, o replay varre e o formatador sai igual ao das irmãs), NÃO os dados da casa. Os
// valores esperados são os do card da PariPesa. Roda com teto 500 e teto 3 de `Count`, porque o
// teto da MelBet é desconhecido e a 1xBit mostrou que ele existe.
//
// Quando a 1ª captura real chegar: salvar o payload como `fixtures/melbet.bethistory.json`,
// conferir no card e trocar `arquivo` e `ESPERADO` por bilhetes da própria MelBet.
import { conferirEspelho } from "../x1_espelho.mjs";

export const casa = "MelBet";

const ESPERADO = {
  "88194620599": { stake: "7,00", odd: "1", status: /^Anulada → V$/, retorno: "7,00" },
  "88194577145": { stake: "8,40", odd: "2", status: /^Perdeu → L$/ },
  "88195014537": { stake: "10,00", odd: "12,9536", status: /^Perdeu → L$/, tipo: /^Múltipla \(2 seleções\)$/ },
  "88237452875": { stake: "5,20", odd: "2,08", status: /^Em aberto/, potencial: "10,82" },
};

export async function rodar() {
  const base = {
    arquivo: "paripesa.bethistory.json",
    href: "https://melbet.com/br/office/history",
    url: "https://melbet.com/bethistory-api/Web/GetBetInfoHistoryWithSummaryByDates",
    moeda: "USDT",
    esperado: ESPERADO,
    carimbo: { ref: "88194620599", valor: "20261002180051" },
  };
  const falhas = [];
  let testes = 0;
  for (const tetoCount of [500, 3]) {
    const r = await conferirEspelho(Object.assign({}, base, { tetoCount }));
    for (const f of r.falhas) falhas.push(`[teto ${tetoCount}] ${f}`);
    testes += r.testes;
  }
  return { falhas, testes };
}
