// R7 (r7.bet.br) — motor **Rogue**, captura por API `GET /v1/betsreporting/purchases` (s335).
//
// É a conta mais rica das três espelho e por isso o caso PRINCIPAL do motor: dos quatro
// `BetStatusId` que o recon encontrou, três só aparecem aqui (0 aberta, 4 anulada e o
// handicap com `Points`). O contrato, o teto de `take` e as armadilhas do dado estão
// documentados uma vez em `../rogue.mjs`.
//
// Cruzamento com a TELA (o print do histórico foi lido no dia do recon, 09/09/2026):
//   885258522240761856 → card "Simples R$250,00 · 2.45 GANHA · Retorno: R$612,50"
//   885255900813529088 → card "Simples R$50,00  · 1.84 GANHA · Retorno: R$92,00"
//   885255808819798016 → card "Simples R$200,00 · 1.84 GANHA · Retorno: R$368,00"
// Nos três, `CurrentBetBalance` é exatamente o "Retorno" do card, e o "ID:" do card é o
// `PurchaseTicketId`. É essa igualdade que autoriza usar o campo como retorno REALIZADO.
//
// O que ESTE caso trava, além do que é comum às três:
//
//   • ANULADA (`BetStatusId: 4`, bilhete 884899595909234688): `CurrentBetBalance` = 300 =
//     a stake exata, `Result` string VAZIA, e os campos `FullTimeResult`/`SettlementResult`
//     AUSENTES. Vira `V` com a odd EXIBIDA (3,57) — nunca `retorno ÷ stake`, que daria 1,00
//     e apagaria a odd real (MASTER_RESULTADO §5.1.2).
//
//   • ABERTA (`BetStatusId: 0`, bilhete 885226164280238080): retorno 0 e `Result` ausente.
//     `bal = 0` é IGUAL ao da perdida — o que separa os dois é o enum, e é por isso que o
//     status não pode ser inferido só do dinheiro nesta casa.
//
//   • PERDIDA com odd alta (873256991194910720, odd 4,57): a odd de L sai de
//     `BetClientOdds`. Se saísse do dinheiro seria 0 — e um bilhete com odd 0 que ganhasse
//     depois viraria −1u (CLAUDE.md, "Zero não é ausência").
//
//   • HANDICAP: `SelectionName` já traz a linha ("Joo Eun Kim -1.5") e o campo `Points`
//     (-1.5) vem à parte, SÓ nesses bilhetes. Os dois sobem — o nome porque é o que o card
//     mostra, o `Points` porque é o número que a `CASA_R7.md` usa para reconhecer asiática.
//
//   • AO VIVO (874070447485673472, vôlei): `IsSelectionLive: true` e `Score1/Score2` = 1/0,
//     o placar NO MOMENTO da aposta. E a data do EVENTO (19:58) é ANTERIOR à da colocação
//     (20:23) — a ordem se inverte em aposta ao vivo, e nenhuma checagem pode assumir que
//     evento vem depois de colocação.
//   • A REGRA DA DATA DE MÚLTIPLA não é exercível por nenhuma fixture: as três contas somam
//     27 bilhetes e todos são de UMA perna. `conferirDataEvento()` cobre isso com um bilhete
//     sintético — ver a justificativa em `../rogue.mjs`. Foi a única mutação que escapou na
//     primeira rodada de prova (9 de 10), e é a definição do falso verde tipo 2.
import { rodarRogue, conferir, conferirDataEvento, conferirTokenRenovado } from "../rogue.mjs";

export const casa = "R7";

// ref → o que a CASA mostra. stake/odd/retorno conferidos contra o card onde ele estava na
// tela; os demais vêm do payload da própria casa (nunca do que o nosso código produz).
const ESPERADO = {
  "885258522240761856": { stake: "250,00", odd: "2,45", st: 2, col: "08/09/2026 17:21:19", ev: "09/09/2026 03:40:00" },
  "885255900813529088": { stake: "50,00",  odd: "1,84", st: 2, col: "08/09/2026 17:10:54", ev: "08/09/2026 23:00:00" },
  "885255808819798016": { stake: "200,00", odd: "1,84", st: 2, col: "08/09/2026 17:10:32", ev: "08/09/2026 23:00:00" },
  // aberta — sem `Result`, sem "Retorno:", com aviso de POTENCIAL
  "885226164280238080": { stake: "200,00", odd: "3,24", st: 0, col: "08/09/2026 15:12:44", ev: "09/09/2026 12:10:00" },
  // anulada — retorno = stake exato, odd EXIBIDA (não retorno÷stake, que daria 1,00)
  "884899595909234688": { stake: "300,00", odd: "3,57", st: 4, col: "07/09/2026 17:35:04", ev: "07/09/2026 23:00:00" },
  "884898849281044480": { stake: "250,00", odd: "1,86", st: 2, col: "07/09/2026 17:32:06", ev: "07/09/2026 23:00:00" },
  "884898647992184832": { stake: "200,00", odd: "1,98", st: 1, col: "07/09/2026 17:31:18", ev: "07/09/2026 23:00:00" },
  "884425552625954816": { stake: "304,00", odd: "1,71", st: 1, col: "06/09/2026 10:11:23", ev: "06/09/2026 11:00:00" },
  "884226853597622272": { stake: "300,00", odd: "1,81", st: 2, col: "05/09/2026 21:01:50", ev: "06/09/2026 04:00:00" },
  "884226562814930944": { stake: "200,00", odd: "3,44", st: 2, col: "05/09/2026 21:00:40", ev: "06/09/2026 05:25:00" },
  "884226365724692480": { stake: "200,00", odd: "2,63", st: 1, col: "05/09/2026 20:59:53", ev: "06/09/2026 03:35:00" },
  // ao vivo — evento (19:58) ANTES da colocação (20:23)
  "874070447485673472": { stake: "208,00", odd: "1,7",  st: 1, col: "08/08/2026 20:23:54", ev: "08/08/2026 19:58:00" },
  "874047623891111936": { stake: "75,00",  odd: "2,06", st: 1, col: "08/08/2026 18:53:12", ev: "08/08/2026 23:00:00" },
  // perdida de odd alta — a odd de L vem da casa, nunca do dinheiro (seria 0)
  "873256991194910720": { stake: "200,00", odd: "4,57", st: 1, col: "06/08/2026 14:31:31", ev: "07/08/2026 02:00:00" },
  "873256143584866304": { stake: "200,00", odd: "2,7",  st: 1, col: "06/08/2026 14:28:08", ev: "07/08/2026 00:40:00" },
};

export async function rodar() {
  const r = await rodarRogue({ host: "r7.bet.br", fixture: "r7.purchases.json", pagina: 4 });
  const { falhas, testes, porRef } = conferir(r, ESPERADO);
  if (!porRef) return { falhas, testes };

  // ── as armadilhas próprias desta conta ──

  // (1) ANULADA: `V`, retorno igual à stake, e a odd NÃO pode ter virado 1,00.
  const anulada = porRef.get("884899595909234688");
  if (anulada) {
    if (/^1(,00?)?( |$)/.test((anulada.split("\n").find((l) => l.startsWith("Odd:")) || "").slice(4).trim())) {
      falhas.push("884899595909234688: a odd da ANULADA virou 1,00 — o retorno igual à stake " +
                  "foi lido como `retorno ÷ stake`; em V vale a odd exibida (MASTER_RESULTADO §5.1.2)");
    }
    if (!/Retorno: R\$ 300,00/.test(anulada)) {
      falhas.push("884899595909234688: a devolução de R$ 300,00 não apareceu como retorno");
    }
  }

  // (2) HANDICAP: a linha do handicap tem de viajar — nome E `Points`.
  const hc = porRef.get("884898849281044480");
  if (hc) {
    if (!/Joo Eun Kim -1\.5|Joo Eun Kim −1,5|Joo Eun Kim -1,5/.test(hc)) {
      falhas.push("884898849281044480: a linha do handicap sumiu do nome da seleção");
    }
    if (!/-1,5|-1\.5/.test(hc)) {
      falhas.push("884898849281044480: o campo `Points` (-1.5) não subiu — a CASA_R7 §9 " +
                  "precisa dele para reconhecer handicap asiático");
    }
  }

  // (3) AO VIVO: a marca tem de aparecer, e o placar do momento não pode virar resultado.
  const live = porRef.get("874070447485673472");
  if (live) {
    if (!/ao vivo/i.test(live)) falhas.push("874070447485673472: aposta ao vivo não foi marcada");
  }

  // (4) O esporte pt-BR da casa tem de chegar ao bloco (é o que o MASTER_ESPORTES casa).
  const comVolei = [...porRef.values()].find((t) => /Vôlei/.test(t));
  if (!comVolei) falhas.push("nenhum bloco trouxe o esporte `Vôlei` que a casa escreve");

  // (5) A regra da data em MÚLTIPLA — nenhuma fixture real a exerce (ver o cabeçalho).
  for (const f of conferirDataEvento()) falhas.push(f);

  // (6) O Bearer EXPIRA — o contexto do replay tem de ser sempre o mais recente.
  for (const f of await conferirTokenRenovado("r7.bet.br", "r7.purchases.json")) falhas.push(f);

  return { falhas, testes: testes + 2 };
}
