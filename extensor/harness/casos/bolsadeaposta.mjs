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
//   3. O CORTE POR STATUS × o corte por "stake casada = 0". Na fixture as duas regras dão o
//      mesmo resultado, porque as únicas ofertas sem casamento são justamente a `failed` e a
//      `flushed`. Trocar o corte por `!o["stake-matched"]` passa VERDE aqui e quebraria em
//      produção: oferta `unmatched` ainda viva no mercado também tem casado zero e é aposta
//      de verdade, esperando par. Fechar isso exige uma aposta EM ABERTO na amostra, e a
//      conta do recon não tem nenhuma (medido: `status=matched,unmatched` devolve 0).
import { rodarInject, carregarContent, fixture, linha } from "../sandbox.mjs";

export const casa = "Bolsa de Aposta";

// ── EXCHANGE ────────────────────────────────────────────────────────────────────────────
// Conferido contra a aba Liquidadas em 26/08/2026. `event-start-time` é UTC; a coluna
// "Início do Evento" do card mostra o horário local — é ele que está aqui.
// `sel` trava a linha `Seleção:` inteira. Ela existe porque até a s299 `Sim` e `Não`
// recebiam a MESMA anotação ("…\"Não\" NEGA o mercado"), e um bilhete de `Sim` saía dizendo
// que negava o mercado — ruído no campo que decide o sentido da aposta, e ruído que a IA lê.
// Passou despercebido no verde porque o teste não olhava esta linha.
const ESPERADO_EX = {
  // W: L/P +35 sobre stake 100 → odd = retorno ÷ stake = 1,35 (bate com o card). O sufixo
  // faz parte do esperado: ele é o que declara, no bloco que a IA lê, que a odd saiu do
  // DINHEIRO e não do campo exibido — a marca de que a regra global do W foi aplicada.
  "119530135": { odd: "1,35 (= Retorno ÷ Stake)", status: /^Ganho → W$/, bruto: "win",  data: "21/08/2026 16:00:00",
                 sel: "Não (resposta ao mercado — NEGA o mercado acima: a aposta é que ele NÃO acontece)" },
  // L: L/P = −stake. A odd continua a estrutural — nunca 0,00.
  "116060239": { odd: "2",    status: /^Perdeu → L$/, bruto: "lose", data: "12/08/2026 19:00:00",
                 sel: "Sim (resposta ao mercado — CONFIRMA o mercado acima)" },
  // V: `push` vem SEM `profit-and-loss` (ausente, não zero) e com a stake devolvida.
  // Seleção que não é booleana não ganha anotação nenhuma.
  "109761317": { odd: "7",    status: /^Anulada → V$/, bruto: "push", data: "26/07/2026 18:30:00",
                 sel: "Empate" },
};

// ── SPORTSBOOK ──────────────────────────────────────────────────────────────────────────
// Conferido contra Minhas Apostas → Resolvidas, com os badges VENCEU/PERDIDO/CANCELADA.
// `card` é o número que a CASA estampa no bilhete — e ele NÃO é o nosso `[Código:]`: a casa
// mostra o id da COMPRA, que é `TicketId − 1` (conferido em 6 cards e em 17 de 17 pela API).
// A chave de dedup segue sendo o `TicketId`, porque uma compra com duas apostas daria o mesmo
// número às duas e o UPSERT fundiria bilhetes distintos. A linha existe para o operador
// cruzar com a tela; este teste trava que ela não some nem passa a repetir o `[Código:]`.
const ESPERADO_SB = {
  "857454677280481281": { odd: "1,8",  status: /^Perdeu → L$/,  bruto: "1", data: "23/06/2026 23:00:00",
                          card: "857454677280481280" },
  "867908924308574209": { odd: "1,99 (= Retorno ÷ Stake)", status: /^Ganho → W$/, bruto: "2", data: "22/07/2026 20:30:00",
                          card: "867908924308574208" },
  "857407480614727681": { odd: "4,5",  status: /^Anulada → V$/, bruto: "4", data: "23/06/2026 20:00:00",
                          card: "857407480614727680" },
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
    if (e.sel != null) {
      const sel = linha(txt, "Seleção:");
      if (sel !== e.sel) falhas.push(`${rotulo} ${b.ref}: seleção esperada "${e.sel}", veio "${sel}"`);
    }
    if (e.card != null) {
      const card = linha(txt, "ID no card da casa:");
      if (card !== e.card) falhas.push(`${rotulo} ${b.ref}: ID do card esperado ${e.card}, veio "${card}"`);
      if (card === b.ref) falhas.push(`${rotulo} ${b.ref}: o ID do card virou cópia do [Código:] — a diferença de 1 sumiu`);
    }
  }
  return testes;
}

// Dias entre `after-day=` / `before-day=` de uma URL do replay. `null` se a URL não tem janela.
function _janela(u) {
  const m = /after-day=(\d{4}-\d{2}-\d{2})[^]*?before-day=(\d{4}-\d{2}-\d{2})/.exec(u);
  return m ? { de: m[1], ate: m[2], dias: (Date.parse(m[2]) - Date.parse(m[1])) / 86400000 } : null;
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
    // DOIS pedidos extras, e cada um prova uma metade do defeito da s299 (`fimReplay` que
    // latchava em `true` e matava toda rodada seguinte):
    //   • `pedidoMsg` chega COM a varredura em curso → prova a fila de re-pedido;
    //   • `pedidoTardio` chega DEPOIS do `fim` → prova o destravamento, que é o caso real
    //     (o operador roda o robô outra vez).
    // Três varreduras no total, então a fatia mais recente tem de ser pedida 6× (2 por
    // varredura: liquidadas + abertas).
    pedidoMsg: { __sharpenupBDAReq: true },
    pedidoTardio: { __sharpenupBDAReq: true },
    // A fixture traz `total: 4` e devolve 4 na primeira página → cada fatia encerra sozinha.
    responder: (url) => (url.includes("/offers/reportsv2") ? corpoEx : null),
    ms: 4000,
  });

  if (!ex.ultima) {
    falhas.push("EXCHANGE: o inject não emitiu nenhuma mensagem");
  } else {
    if (!ex.ultima.fim) falhas.push("EXCHANGE: o inject não sinalizou `fim` (o robô esperaria o teto)");
    // `urls[0]` é a requisição da PÁGINA que o sandbox dispara (o `urlInicial`); o replay é
    // tudo a partir da segunda. Confundir as duas faria o teste cobrar do inject o que é da tela.
    const replayEx = ex.urls.slice(1);
    const janelas = [];
    for (const u of replayEx) {
      const j = _janela(u);
      if (!j) { falhas.push(`EXCHANGE: requisição sem janela de datas: ${u}`); continue; }
      janelas.push(j);
      // Teto DURO do servidor: acima de 95 dias ele responde 400 `Max allowed interval`.
      if (j.dias > 95) falhas.push(`EXCHANGE: janela de ${j.dias} dias — a casa devolve 400 acima de 95`);
    }
    if (!janelas.length) {
      falhas.push("EXCHANGE: o replay não fez nenhuma requisição com janela");
    } else {
      // COBERTURA DO HISTÓRICO. Aqui mora a regressão que quebrou a 1ª captura ao vivo: o
      // replay saía com os 30 dias do painel e parava na borda, trazendo 21 de 418 bilhetes.
      // O horizonte é fixo (3 anos) e NÃO sai do `lookbackDias` — este teste é o que trava isso.
      const maisAntiga = janelas.map((j) => j.de).sort()[0];
      const cobertos = (Date.now() - Date.parse(maisAntiga)) / 86400000;
      if (cobertos < 1000) {
        falhas.push(`EXCHANGE: replay cobriu só ${Math.round(cobertos)} dias (mais antiga: ${maisAntiga}) — o horizonte é de ~3 anos`);
      }
      // REPLAY REPETÍVEL. Cada fatia é pedida 2× por varredura (liquidadas + abertas), e o
      // caso manda TRÊS pedidos (o inicial, um durante e um depois do `fim`) → a fatia mais
      // recente tem de aparecer 6×. Menos que isso significa que algum pedido morreu: 4× = o
      // tardio caiu no `fimReplay` travado; 4× também = o pedido de meio da varredura se
      // perdeu. Os dois modos derrubam este teste, e os dois foram provados por mutação.
      const maisNova = janelas.map((j) => j.de).sort().reverse()[0];
      const vezes = janelas.filter((j) => j.de === maisNova).length;
      if (vezes < 6) {
        falhas.push(`EXCHANGE: 3 pedidos deveriam render 3 varreduras — a fatia ${maisNova} foi pedida ${vezes}× (esperado 6)`);
      }
    }

    // 5 ofertas na fixture, 2 sem casamento (`failed` e `flushed`) → 3 bilhetes.
    // O `flushed` é o que vazou na 1ª captura ao vivo e virou linha com stake 0.
    const bilhetes = ex.ultima.bilhetes || [];
    if (bilhetes.length !== 3) falhas.push(`EXCHANGE: esperava 3 bilhetes (\`failed\` e \`flushed\` não são bilhete), vieram ${bilhetes.length}`);
    if (ex.ultima.naoCasadas !== 2) falhas.push(`EXCHANGE: esperava naoCasadas=2 (failed + flushed), veio ${ex.ultima.naoCasadas}`);

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

  // ── A janela de dias NÃO pode cortar nesta casa ───────────────────────────────────────
  // Esta é a regressão que quebrou a 1ª captura ao vivo (s299) e a única das correções que
  // não passa pelo inject: o corte vivia no laço do robô. Sem este bloco, restaurar o corte
  // passava verde — o caso testava o `formatTicket*` e o replay, nunca o laço.
  //
  // Chama `_roboBolsa` direto, com um mapa sintético de 3 bilhetes RESOLVIDOS e TODOS mais
  // velhos que o cutoff de 30 dias. Com o corte de volta, o laço emite um e para; sem ele,
  // emite os três. `fim: () => true` encerra a espera na hora.
  const roboBolsa = content.pegar("_roboBolsa");
  const mapaJanela = new Map();
  for (const [ref, iso] of [["A", "2026-01-10T12:00:00Z"],
                            ["B", "2026-02-10T12:00:00Z"],
                            ["C", "2026-03-10T12:00:00Z"]]) {
    mapaJanela.set(ref, { ref, colocada: iso });
  }
  const ctxJanela = {
    cutoff: Date.now() - 30 * 86400000,
    pisoSanidade: Date.now() - 760 * 86400000,
    stopId: "",
    parar: () => false,
    painel: { contador: { textContent: "" } },
  };
  const blocosJanela = await roboBolsa(ctxJanela, {
    mapa: mapaJanela, fmt: (b) => "[Código: " + b.ref + "]", aberta: () => false,
    quando: (b) => b.colocada, pedido: "__sharpenupBDAReq", fim: () => true,
  });
  testes++;
  if (blocosJanela.length !== 3) {
    falhas.push(`JANELA: os 3 bilhetes são mais velhos que o lookback de 30 dias e TODOS têm de sair — saíram ${blocosJanela.length}`);
  }
  // E o `stopId` continua sendo o freio: ele é o mecanismo incremental que substitui a janela.
  const blocosStop = await roboBolsa(
    { ...ctxJanela, stopId: "B" },
    { mapa: mapaJanela, fmt: (b) => "[Código: " + b.ref + "]", aberta: () => false,
      quando: (b) => b.colocada, pedido: "__sharpenupBDAReq", fim: () => true });
  testes++;
  if (blocosStop.length !== 1) {
    falhas.push(`JANELA: com stopId=B o laço deveria parar depois de C (1 bloco) — saíram ${blocosStop.length}`);
  }

  return { falhas, testes };
}
