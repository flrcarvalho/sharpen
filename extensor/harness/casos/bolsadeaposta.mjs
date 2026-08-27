// Bolsa de Aposta — DUAS plataformas sem parentesco, em iframes de origens diferentes (s299).
//
// A casca `bolsadeaposta.bet.br` é Angular e **não faz uma única requisição de bilhete**:
// grampo em fetch/XHR/WebSocket no frame principal vê zero enquanto a tabela enche. As duas
// telas de aposta são iframes de outra origem — a armadilha da bet365 (`all_frames:false`).
//
//   • EXCHANGE   `mexchange2.bolsadeaposta.bet.br`  → LayBack/FulltBet, JSON kebab-case
//   • SPORTSBOOK `prod20454-176166000.msjxk.com`    → outra casa de software, PascalCase
//
// Trava as cinco leituras que custaram o recon, cada uma cruzada com o card renderizado:
//
//   • `GainDecimal` do Sportsbook é o retorno POTENCIAL, nunca o realizado. O bilhete
//     857454677280481281 traz `"720"` e a tela dele diz **PERDIDO, Ganho Potencial 0,00**.
//     Ler `Gain` como retorno transforma toda perda em vitória (o `totalWin` da VaideBet).
//     O realizado é `CurrentBetBalanceDecimal`: 0 (L) · 409,94 (W) · 100 (V, = stake).
//   • `failed` do Exchange NÃO é bilhete — é oferta que nunca casou, sem `stake-matched`.
//     Dinheiro que nunca esteve em risco. Sai da lista, mas **contado** em `naoCasadas`:
//     descarte silencioso é o que este projeto já pagou caro para não repetir.
//   • Stake do Exchange é `stake-matched`, NUNCA `stake` — a oferta `failed` traz
//     `stake: 100` com risco zero, e ler o campo errado lança R$100 que não existiram.
//   • V nunca vira odd 1,00. O cancelado do Sportsbook devolve a stake (100/100 = 1,0);
//     ali manda o `ClientOdds` estrutural (4,50). Mesma regra do MASTER_RESULTADO.
//   • Data = evento, em UTC com `Z` → America/Sao_Paulo. Sem converter, o bilhete pula de
//     dia. Os três horários abaixo foram conferidos contra o card, um a um.
//
// O QUE ESTE CASO NÃO COBRE (a conta usada no recon não tinha amostra):
// aposta em aberto, `lay` (418 bilhetes, todos `back`), cashout/Retirada, múltipla do
// Sportsbook, e `push_win`/`push_lose` (existem no código da casa, sem bilhete real).
//
// E DUAS REGRAS QUE O CÓDIGO APLICA MAS ESTE TESTE **NÃO DETECTA** — provado por mutação,
// não suposto. Estão aqui escritas porque verde sem esta ressalva é promessa falsa:
//
//   1. `stake-matched` × `stake`. Nos 3 bilhetes que sobram os dois campos valem 100: a
//      única linha onde eles divergem é a `failed`, e ela é descartada antes. Trocar um
//      pelo outro passa verde. Só uma oferta PARCIALMENTE casada exerceria a regra, e não
//      houve nenhuma em 418 bilhetes — inventar uma seria fabricar payload.
//   2. `CurrentBetBalanceDecimal` × `GainDecimal` no bilhete GANHO. No 867908924308574209
//      os dois valem 409,94, então ler o campo errado dá o mesmo número. O que o teste
//      pega (mutação confirmada) é o potencial VAZANDO para bilhete resolvido e a odd de V
//      saindo do dinheiro — que são os dois modos pelos quais essa confusão vira lucro
//      fantasma. Um W com cashout parcial ou boost fecharia o buraco.
import { rodarInject, carregarContent, fixture, linha } from "../sandbox.mjs";

export const casa = "Bolsa de Aposta";

// ── EXCHANGE ────────────────────────────────────────────────────────────────────────────
// Conferido contra a aba Liquidadas em 26/08/2026. `event-start-time` é UTC; a coluna
// "Início do Evento" do card mostra o horário local — é ele que está aqui.
const ESPERADO_EX = {
  // W: L/P +35 sobre stake 100 → odd = retorno ÷ stake = 1,35 (bate com o card). O sufixo
  // faz parte do esperado: ele é o que declara, no bloco que a IA lê, que a odd saiu do
  // DINHEIRO e não do campo exibido — a marca de que a regra global do W foi aplicada.
  "119530135": { odd: "1,35 (= Retorno ÷ Stake)", status: /^Ganho → W$/, bruto: "win",  data: "21/08/2026 16:00:00" },
  // L: L/P = −stake. A odd continua a estrutural — nunca 0,00.
  "116060239": { odd: "2",    status: /^Perdeu → L$/, bruto: "lose", data: "12/08/2026 19:00:00" },
  // V: `push` vem SEM `profit-and-loss` (ausente, não zero) e com a stake devolvida.
  "109761317": { odd: "7",    status: /^Anulada → V$/, bruto: "push", data: "26/07/2026 18:30:00" },
};

// ── SPORTSBOOK ──────────────────────────────────────────────────────────────────────────
// Conferido contra Minhas Apostas → Resolvidas, com os badges VENCEU/PERDIDO/CANCELADA.
const ESPERADO_SB = {
  "857454677280481281": { odd: "1,8",  status: /^Perdeu → L$/,  bruto: "1", data: "23/06/2026 23:00:00" },
  "867908924308574209": { odd: "1,99 (= Retorno ÷ Stake)", status: /^Ganho → W$/, bruto: "2", data: "22/07/2026 20:30:00" },
  "857407480614727681": { odd: "4,5",  status: /^Anulada → V$/, bruto: "4", data: "23/06/2026 20:00:00" },
};

function conferir(falhas, fmt, bilhetes, esperado, rotulo) {
  let testes = 0;
  for (const b of bilhetes) {
    const e = esperado[b.ref];
    if (!e) { falhas.push(`${rotulo}: bilhete inesperado na fixture: ${b.ref}`); continue; }
    const txt = fmt(b);
    testes++;
    if (!txt.startsWith(`[Código: ${b.ref}]`)) falhas.push(`${rotulo} ${b.ref}: marcador [Código:] ausente/errado`);
    const odd = linha(txt, "Odd:");
    const status = linha(txt, "Status:");
    const api = linha(txt, "Status (API):");
    const data = linha(txt, "Data (evento):");
    if (odd !== e.odd) falhas.push(`${rotulo} ${b.ref}: odd esperada ${e.odd}, veio "${odd}"`);
    if (!e.status.test(status)) falhas.push(`${rotulo} ${b.ref}: status "${status}"`);
    if (api !== e.bruto) falhas.push(`${rotulo} ${b.ref}: status cru esperado ${e.bruto}, veio "${api}"`);
    if (data !== e.data) falhas.push(`${rotulo} ${b.ref}: data esperada ${e.data}, veio "${data}"`);
  }
  return testes;
}

export async function rodar() {
  const falhas = [];
  let testes = 0;
  const content = carregarContent();

  // ── Exchange ──────────────────────────────────────────────────────────────────────────
  const corpoEx = fixture("bolsadeaposta.reportsv2.json");
  const baseEx = "https://mexchange-api.bolsadeaposta.bet.br/api/offers/reportsv2";

  const ex = await rodarInject({
    inject: "bda_inject.js",
    href: "https://mexchange2.bolsadeaposta.bet.br/account/mybets",
    urlInicial: `${baseEx}?offset=0&per-page=20&after-day=2026-08-01&before-day=2026-08-26&timezone-offset=180&status=liquidated`,
    pedido: "__sharpenupBDAReq",
    // A fixture traz `total: 4` e devolve 4 na primeira página → o replay encerra sozinho.
    responder: (url) => (url.includes("/offers/reportsv2") ? corpoEx : null),
  });

  if (!ex.ultima) {
    falhas.push("EXCHANGE: o inject não emitiu nenhuma mensagem");
  } else {
    if (!ex.ultima.fim) falhas.push("EXCHANGE: o inject não sinalizou `fim` (o robô esperaria o teto)");
    // `urls[0]` é a requisição da PÁGINA que o sandbox dispara (o `urlInicial`); o replay é
    // tudo a partir da segunda. Confundir as duas faria o teste cobrar do inject o que é da tela.
    const replayEx = ex.urls.slice(1);
    // A tela oferece no máximo 30 dias e o servidor corta em `Max allowed interval is 95 days`.
    // O replay tem de ALARGAR o filtro em fatias — e são 2 chamadas por fatia (liquidadas +
    // abertas), então menos de 2 significa que ele não varreu.
    if (replayEx.length < 2) falhas.push(`EXCHANGE: replay não alargou a janela (só ${replayEx.length} requisição)`);
    for (const u of replayEx) {
      const m = /after-day=(\d{4}-\d{2}-\d{2})[^]*?before-day=(\d{4}-\d{2}-\d{2})/.exec(u);
      if (!m) { falhas.push(`EXCHANGE: requisição sem janela de datas: ${u}`); continue; }
      const dias = (Date.parse(m[2]) - Date.parse(m[1])) / 86400000;
      if (dias > 95) falhas.push(`EXCHANGE: janela de ${dias} dias — a casa devolve 400 acima de 95`);
    }

    const bilhetes = ex.ultima.bilhetes || [];
    if (bilhetes.length !== 3) falhas.push(`EXCHANGE: esperava 3 bilhetes (a 4ª é \`failed\`), vieram ${bilhetes.length}`);
    if (ex.ultima.naoCasadas !== 1) falhas.push(`EXCHANGE: esperava naoCasadas=1, veio ${ex.ultima.naoCasadas}`);

    const fmtEx = content.pegar("formatTicketBDA");
    testes += conferir(falhas, fmtEx, bilhetes, ESPERADO_EX, "EXCHANGE");
  }

  // ── Sportsbook ────────────────────────────────────────────────────────────────────────
  const corpoSb = fixture("bolsadeaposta.sportsbook.json");
  const baseSb = "https://prod20454-176166000.msjxk.com/api/master/my-bets/history";

  const sb = await rodarInject({
    inject: "bds_inject.js",
    href: "https://prod20454-176166000.msjxk.com/br-pt/spbkv4/my-bets/sports",
    urlInicial: `${baseSb}?limit=10&offset=0&lastHours=1M`,
    pedido: "__sharpenupBDSReq",
    responder: (url) => (url.includes("/my-bets/history") ? corpoSb : null),
  });

  if (!sb.ultima) {
    falhas.push("SPORTSBOOK: o inject não emitiu nenhuma mensagem");
  } else {
    if (!sb.ultima.fim) falhas.push("SPORTSBOOK: o inject não sinalizou `fim`");
    // `lastHours` é a pergunta estreita da tela: com `1M` a conta do recon devolvia ZERO,
    // porque os bilhetes eram mais velhos. Omitir o parâmetro traz o histórico inteiro.
    // (E ele não aceita número: `8760` devolve 0 e `12M` devolve tudo — o nome mente.)
    const replaySb = sb.urls.slice(1);   // urls[0] é a requisição da PÁGINA, que usa `lastHours`
    if (!replaySb.length) falhas.push("SPORTSBOOK: o replay não fez nenhuma requisição");
    if (replaySb.some((u) => /lastHours=/.test(u))) {
      falhas.push("SPORTSBOOK: o replay manteve `lastHours` — a janela da tela esconde o histórico");
    }

    const bilhetes = sb.ultima.bilhetes || [];
    if (bilhetes.length !== 3) falhas.push(`SPORTSBOOK: esperava 3 bilhetes, vieram ${bilhetes.length}`);

    const fmtSb = content.pegar("formatTicketBDS");
    testes += conferir(falhas, fmtSb, bilhetes, ESPERADO_SB, "SPORTSBOOK");

    // O campo que engana: o potencial não pode aparecer como retorno em bilhete perdido.
    const perdido = bilhetes.find((b) => b.ref === "857454677280481281");
    if (perdido) {
      const txt = fmtSb(perdido);
      if (/720/.test(txt)) falhas.push("SPORTSBOOK 857454677280481281: o retorno POTENCIAL (720) vazou para o bloco de um bilhete PERDIDO");
    }
  }

  return { falhas, testes };
}
