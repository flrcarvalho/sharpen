// 7Games (7games.bet.br) — motor **Rogue**, a terceira espelho (s335).
// Contrato e armadilhas do motor: `../rogue.mjs`.
//
// A conta tem só TRÊS bilhetes, e o caso existe justamente por isso: ele é a **prova do
// espelho**. Os três passam pelo MESMO `rg_inject.js` e pelo MESMO `formatTicketRG`, com a
// única diferença sendo o host — e é essa passagem que impede alguém de "ajustar" o inject
// para uma casa e quebrar as outras duas sem perceber. Foi o que a família Altenar ensinou:
// espelho sem caso próprio é espelho que ninguém confere.
//
// Cobertura: um de cada estado que a conta tem (`BetStatusId` 2, 0 e 1). Não há anulada nem
// múltipla aqui — esses estão (o que existe deles) no caso da R7.
//
// O bilhete ABERTO desta conta (885232553773772800) é o segundo exemplar da armadilha
// central: `Gain` diz 518,00 e `CurrentBetBalance` diz "0". Emitir o primeiro como retorno
// liquidaria uma aposta que ainda está correndo.
import { rodarRogue, conferir } from "../rogue.mjs";

export const casa = "7Games";

const ESPERADO = {
  "885255718436737024": { stake: "200,00", odd: "1,84", st: 2, col: "08/09/2026 17:10:10", ev: "08/09/2026 23:00:00" },
  "885232553773772800": { stake: "200,00", odd: "2,59", st: 0, col: "08/09/2026 15:38:07", ev: "09/09/2026 04:00:00" },
  "885232207148290048": { stake: "200,00", odd: "1,9",  st: 1, col: "08/09/2026 15:36:44", ev: "09/09/2026 04:00:00" },
};

export async function rodar() {
  // Página de 2 contra `take=100`: mesmo com 3 bilhetes o `skip` precisa avançar duas vezes.
  const r = await rodarRogue({ host: "7games.bet.br", fixture: "7games.purchases.json", pagina: 2 });
  const { falhas, testes, porRef } = conferir(r, ESPERADO);
  if (!porRef) return { falhas, testes };

  // A aberta desta conta: `Gain` 518,00 é POTENCIAL e não pode virar dinheiro recebido.
  const aberta = porRef.get("885232553773772800");
  if (aberta) {
    if (/Retorno: /.test(aberta)) {
      falhas.push("885232553773772800: bilhete ABERTO emitiu \"Retorno:\" — a IA liquidaria a aposta");
    }
    if (!/518,00/.test(aberta)) {
      falhas.push("885232553773772800: o retorno potencial (518,00) não foi informado");
    }
    if (!/POTENCIAL/.test(aberta)) {
      falhas.push("885232553773772800: o valor de 518,00 subiu sem o aviso de que é POTENCIAL");
    }
  }

  return { falhas, testes };
}
