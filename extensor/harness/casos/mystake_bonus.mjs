// MyStake — BÔNUS DE ODD (`RiskBonusPercent`, s422).
//
// O card mostra "+5%" vermelho ao lado da Quantia. É bônus de odd da múltipla: a casa paga o
// percentual sobre o LUCRO da ganha, e o `WinAmount` da API vem SEM ele. Lendo só o
// `WinAmount`, a odd ia para a planilha sem o bônus e a Caixa da conta Ellen [Eu] acusava
// R$ 297,75 a menos que a casa.
//
// ── Como foi provado (18/10/2026) ─────────────────────────────────────────────────────────
//   Pelo DINHEIRO, não pela tela: as 4 ganhas da conta com o campo somam R$ 248,04 de bônus,
//   e com a "Bonus Activation" de R$ 49,71 do extrato fecham os R$ 297,75 ao centavo. A tela
//   confirma os três cards abertos pelo dono:
//       308194559  100 @ 12,495 → API 1.249,50 · card 1.306,97 (+5%)
//       308368220  100 @ 24,168 → API 2.416,80 · card 2.532,64 (+5%)
//       307478724  100 @ 14,0811 → API 1.408,11 · card 1.473,51 (+5%)
//   O card TRUNCA o centavo (1.306,97), mas o crédito é arredondado com a metade para cima
//   (57,475 → 57,48): truncando, a soma daria 296,73 e a Caixa não fecharia.
//
// ── Os cinco bilhetes da fixture (crus reais da `captura_crua`, sem dado de pessoa) ────────
//   308194559  ganha, 5%            → retorno 1.306,98 · odd 13,0698
//   308368220  ganha, 5%            → retorno 2.532,64 · odd 25,3264
//   307310722  ganha, 3%, perna anulada: o bônus sai do lucro PAGO (310,40), não do Koef
//              9,0288 (802,88)      → retorno 419,71 · odd 4,1971
//   307486282  ganha SEM o campo (0) → nada muda: Koef 16,3721 (controle)
//   307114626  perdida COM 3%        → nada muda: L, sem linha de bônus (controle)
//
// ── O que NÃO cobre ──────────────────────────────────────────────────────────────────────
//   Cashout e anulada com o campo (sem amostra: o formatador não dá bônus a nenhum dos dois),
//   freebet ganha com o campo, e as casas irmãs (Tivo/Betfast/Faz1bet), que não trouxeram o
//   campo preenchido em nenhum cru medido.
//   Mutação inócua conhecida: tirar a guarda "só na ganha" do `_bonusOddTV` não muda bloco
//   nenhum daqui (na perdida o lucro é negativo e a linha só sai com bônus > 0; o Status de L
//   não lê o retorno). Ela passa a importar no cashout com o campo, que não tem amostra.
//   Mutações provadas (vermelho): inject sem o campo · bônus sobre o retorno · sobre o lucro do
//   Koef · truncado · Status sem o bônus · odd sem o bônus · sem a linha de bônus.
import { rodarInject, fixture, carregarContent, linha } from "../sandbox.mjs";

export const casa = "MyStake";

const HREF = "https://mystake.bet/br/sportsbook/mybets";
const API = "https://mystake.bet/api/game/p/messagetosport";

const ESPERADO = {
  "308194559": { odd: "13,0698", status: "Ganho → W (retorno R$ 1306,98)", bonus: "+5% sobre o lucro = R$ 57,48" },
  "308368220": { odd: "25,3264", status: "Ganho → W (retorno R$ 2532,64)", bonus: "+5% sobre o lucro = R$ 115,84" },
  "307310722": { odd: "4,1971",  status: "Ganho → W (retorno R$ 419,71)",  bonus: "+3% sobre o lucro = R$ 9,31" },
  "307486282": { odd: "16,3721", status: "Ganho → W (retorno R$ 1637,21)", bonus: null },
  "307114626": { odd: "11,9616", status: "Perdeu → L",                     bonus: null },
};

export async function rodar() {
  const corpo = fixture("mystake_bonus.gethistory.json");
  const falhas = [];
  let testes = 0;

  const { ultima } = await rodarInject({
    inject: "tv_inject.js",
    href: HREF,
    urlInicial: API,
    pedido: "__sharpenupTVReq",
    responder: (url) => (url.includes("messagetosport") ? corpo : null),
  });
  if (!ultima) return { falhas: ["o inject não emitiu nenhuma mensagem"], testes };

  const fmt = carregarContent().pegar("formatTicketTV");
  const porId = new Map((ultima.tickets || []).map((t) => [String(t.id), t]));

  for (const [id, e] of Object.entries(ESPERADO)) {
    const t = porId.get(id);
    testes++;
    if (!t) { falhas.push(`${id}: não veio na captura`); continue; }
    const txt = fmt(t);

    const odd = linha(txt, "Odd:");
    if (odd !== e.odd) falhas.push(`${id}: odd esperada ${e.odd}, veio "${odd}"` +
      (e.bonus ? " — sem o bônus de odd a planilha grava a odd da API e a Caixa fica abaixo da casa" : ""));

    const status = linha(txt, "Status:");
    if (status !== e.status) falhas.push(`${id}: Status esperado "${e.status}", veio "${status}" (é dele que o gate s321 lê o retorno)`);

    testes++;
    const bonus = linha(txt, "Bônus de odd da casa:");
    if (e.bonus) {
      if (!(bonus || "").startsWith(e.bonus)) falhas.push(`${id}: linha de bônus esperada "${e.bonus}…", veio "${bonus}"`);
    } else if (bonus) {
      falhas.push(`${id}: bilhete sem bônus pago saiu com linha de bônus ("${bonus}")`);
    }
  }

  return { falhas, testes };
}
