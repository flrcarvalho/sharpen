// Betão (betao.bet.br) — motor **Rogue**, mesma API da R7 e do 7Games (s335).
// Contrato, teto de `take` e armadilhas do dado: `../rogue.mjs`.
//
// Esta conta é a que tem os esportes FORA do padrão das outras duas, e é por isso que ela
// entra como caso próprio em vez de virar mais uma fixture da R7:
//
//   • OUTRIGHT / FUTURO (867076991768911872, Fórmula 1): `EventTypeId: 8` — o único valor
//     diferente de 0 fora do ao vivo —, `EnMarketName: "Outright"`, e o `Result` NÃO é
//     placar: é a frase `"Winner Kimi Antonelli, Max Verstappen, Lando Norris"`. Quem
//     assumir `Result` no formato `"N : N"` para derivar qualquer coisa quebra aqui. Repare
//     também que `Team1name`/`Team2name` trazem DOIS pilotos que não são "o confronto" — em
//     outright eles não descrevem um duelo, e usá-los para montar descrição inventaria um
//     jogo que não existe.
//
//   • FUTEBOL de verdade (872134288308391936), com `SportId: 1` e `MarketName` "Resultado
//     Final" — as outras duas contas são quase só Badminton. Serve de âncora para o de-para
//     de esporte não ser calibrado num esporte só.
//
//   • A ODD que a divisão confirma ao centavo (872134288308391936): stake 598,00 × odd 1,68
//     = 1.004,64 e `CurrentBetBalance` é exatamente "1004.64". É a prova de que
//     `retorno ÷ stake` reproduz a odd da casa sem sobra nesta casa — e por isso a odd de W
//     pode vir do dinheiro (regra global do W) sem risco de dízima.
//
// A conta não tinha nenhum bilhete aberto nem anulado no dia do recon: `BetStatusId` aqui é
// só 1 e 2. Aberta e anulada estão travadas no caso da R7.
import { rodarRogue, conferir } from "../rogue.mjs";

export const casa = "Betão";

const ESPERADO = {
  "872581186613731328": { stake: "150,00", odd: "3,29", st: 1, col: "04/08/2026 17:46:06", ev: "05/08/2026 03:15:00" },
  "872580874352168960": { stake: "550,00", odd: "2,5",  st: 2, col: "04/08/2026 17:44:52", ev: "04/08/2026 23:40:00" },
  "872580687542071296": { stake: "375,00", odd: "3,27", st: 1, col: "04/08/2026 17:44:07", ev: "05/08/2026 00:40:00" },
  "872580462039359488": { stake: "500,00", odd: "2,44", st: 1, col: "04/08/2026 17:43:13", ev: "04/08/2026 23:40:00" },
  "872580241184239616": { stake: "450,00", odd: "2,79", st: 1, col: "04/08/2026 17:42:21", ev: "04/08/2026 22:40:00" },
  "872235124246147072": { stake: "400,00", odd: "2,92", st: 2, col: "03/08/2026 18:50:58", ev: "04/08/2026 01:30:00" },
  "872234289042673664": { stake: "500,00", odd: "1,67", st: 1, col: "03/08/2026 18:47:39", ev: "04/08/2026 03:50:00" },
  // futebol · a divisão fecha ao centavo: 1004,64 ÷ 598 = 1,68 exato
  "872134288308391936": { stake: "598,00", odd: "1,68", st: 2, col: "03/08/2026 12:10:17", ev: "03/08/2026 15:00:00" },
  // outright de F1 · EventTypeId 8 e `Result` em texto, não placar
  "867076991768911872": { stake: "399,00", odd: "3,5",  st: 2, col: "20/07/2026 13:14:24", ev: "24/07/2026 11:31:00" },
};

export async function rodar() {
  const r = await rodarRogue({ host: "betao.bet.br", fixture: "betao.purchases.json", pagina: 3 });
  const { falhas, testes, porRef } = conferir(r, ESPERADO);
  if (!porRef) return { falhas, testes };

  // (1) OUTRIGHT: o `Result` em texto tem de subir inteiro, sem tentar virar placar.
  const f1 = porRef.get("867076991768911872");
  if (f1) {
    if (!/Winner Kimi Antonelli, Max Verstappen, Lando Norris/.test(f1)) {
      falhas.push("867076991768911872: o `Result` textual do outright foi perdido ou recortado — " +
                  "é ele que diz por que a aposta ganhou");
    }
    if (!/Lando Norris/.test(f1)) falhas.push("867076991768911872: a seleção apostada sumiu do bloco");
    // O evento é uma prova, não um confronto: nada pode ter montado "Kimi Antonelli vs Lewis
    // Hamilton" a partir de Team1name/Team2name.
    if (/Kimi Antonelli\s+(vs|x|-)\s+Lewis Hamilton/i.test(f1)) {
      falhas.push("867076991768911872: o formatador inventou um confronto a partir de " +
                  "Team1name/Team2name num OUTRIGHT — nesse tipo eles não são adversários");
    }
  }

  // (2) FUTEBOL: o esporte tem de chegar como a casa escreve (é o que o MASTER casa).
  const futebol = porRef.get("872134288308391936");
  if (futebol) {
    if (!/Futebol/.test(futebol)) falhas.push("872134288308391936: esporte `Futebol` não chegou ao bloco");
    if (!/Retorno: R\$ 1004,64|Retorno: R\$ 1\.004,64/.test(futebol)) {
      falhas.push("872134288308391936: o retorno real (1.004,64) não apareceu");
    }
  }

  return { falhas, testes };
}
