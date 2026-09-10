// Betbra — a MESMA plataforma da Bolsa de Aposta, com outra marca (s343).
//
// Medido no navegador em 10/09/2026, lendo o `src` real dos dois iframes na conta do Feca:
//
//   • EXCHANGE   `mexchange.betbra.bet.br/exchange`      → LayBack/FulltBet, kebab-case
//   • SPORTSBOOK `prod20454-176166310.msjxk.com/br-pt/spbk` → outro software, PascalCase
//
// As ROTAS DA CASCA são idênticas às da Bolsa (`/b/exchange` · `/fbook`), e os dois injects
// já derivam o endereço de `location` — por isso a Betbra entra como casa ESPELHO, sem
// inject nem formatador próprios. O que ela acrescenta são três leituras que a conta do
// recon da Bolsa não tinha como exercer:
//
//   1. `MappedSelections` — E ESTA QUEBRAVA O CÓDIGO. `Selections` traz 4 entradas para UMA
//      aposta: os índices 0..2 são as PERNAS do bet builder (odds de mercado, nunca
//      apostadas soltas) e o último é a entrada AGREGADA do cupom (`MarketTypeId: "QA0"`),
//      que concatena as pernas com " | " nos campos de texto e carrega a odd do conjunto.
//      Iterar todas monta uma múltipla falsa de 26,72 (1,13 × 2,30 × 2,23 × 4,61) no lugar
//      de uma aposta de 4,61. Medido em 10 de 10 bilhetes desta conta: a odd do bilhete bate
//      com o produto das MAPPED em 10/10 e com o produto de TODAS em 0/10.
//      ⚠ O caso da Bolsa **continua verde** com ou sem a correção: lá `MappedSelections` é
//      sempre `[0]` com uma seleção só, então aquela fixture não exerce a regra. É o falso
//      verde do tipo 2 do CLAUDE.md, e é por isso que a correção entra junto com ESTE caso.
//
//   2. APOSTA EM ABERTO nos DOIS ambientes. A Bolsa não tinha nenhuma (`status=matched,
//      unmatched` devolvia 0 e o Sportsbook não tinha `open`). Aqui há `matched` no Exchange
//      e `BetStatus: 0` no Sportsbook — o que fecha, entre outras coisas, o buraco #3 do
//      caso da Bolsa: uma oferta `unmatched`/`matched` VIVA também tem casamento parcial ou
//      total, e trocar o corte de `failed`/`flushed` por "stake casada = 0" descartaria
//      aposta de verdade.
//
//   3. BOOST REAL, e ele fica onde ninguém procura. `ClientOdds` da agregada é a odd COM
//      boost (4,61) e `DbTrueOdds` é a SEM boost (3,49); a tela risca a segunda e estampa a
//      primeira. Na Bolsa o boost estava "não confirmado". A odd que vale é a `ClientOdds`
//      do bilhete — 50 × 4,61 = 230,50 = `GainDecimal`.
//
// As armadilhas herdadas da Bolsa foram TODAS reconfirmadas na tela da Betbra, uma a uma:
// `GainDecimal` potencial inclusive em perdida (R$ 230,50 num `BetStatus: 1`), o card
// estampando `PurchaseTicketID` = `TicketId − 1`, `failed` sem `stake-matched`, `push` sem
// `profit-and-loss`, e data de evento em UTC com `Z`.
//
// O QUE ESTE CASO NÃO COBRE (não há amostra na conta — medido, não suposto):
//   • `lay` — 403 ofertas do Exchange, TODAS `back`;
//   • cashout / Retirada, e `IsPartialCashOut: true`;
//   • `push_win` / `push_lose` (HW/HL) — existem no código da casa, sem bilhete real;
//   • `MappedSelections` com 2+ índices, que é a múltipla de eventos DIFERENTES. Todos os 10
//     bilhetes do Sportsbook desta conta são bet builder de mesmo jogo, com um índice só.
//     Enquanto não houver amostra, o pareamento de N mapped não está provado aqui;
//   • casamento PARCIAL no Exchange (`stake-matched` < `stake` numa oferta viva), que é a
//     única linha capaz de separar `stake-matched` de `stake` — o mesmo buraco #1 da Bolsa;
//   • `market-type` diferente de `custom`: as 403 ofertas são todas do Criador de Eventos.
import { rodarInject, carregarContent, fixture, linha } from "../sandbox.mjs";

export const casa = "Betbra";

// ── EXCHANGE ────────────────────────────────────────────────────────────────────────────
// Cruzado com Minha conta → Minhas Apostas → Passada, em 10/09/2026. A coluna "Início do
// Evento" da tabela mostra o horário local — é ele que está aqui. `event-start-time` é UTC.
const ESPERADO_EX = {
  // W: `profit-and-loss` é LUCRO (+480 sobre stake 100) → retorno 580 → odd 5,8. Bate com a
  // coluna Odd Back (5.80) e com a coluna Retorno (R$580,00) da tela.
  "12515190":  { odd: "5,8 (= Retorno ÷ Stake)", status: /^Ganho → W$/,  bruto: "win",   data: "07/09/2026 16:30:00",
                 sel: "Sim (resposta ao mercado — CONFIRMA o mercado acima)" },
  // L: odd estrutural. A tela diz Odd Back 13.00 e **Retorno R$520,00 num bilhete PERDIDO** —
  // a coluna Retorno da casa é potencial, como o `GainDecimal` do Sportsbook.
  "12536715":  { odd: "13",   status: /^Perdeu → L$/,  bruto: "lose",  data: "08/09/2026 21:30:00",
                 sel: "Sim (resposta ao mercado — CONFIRMA o mercado acima)" },
  // V: `push` vem SEM `profit-and-loss` (ausente, não zero) e com a stake devolvida.
  "7447879":   { odd: "3,6",  status: /^Anulada → V$/, bruto: "push",  data: "15/12/2025 14:30:00",
                 sel: "Sim (resposta ao mercado — CONFIRMA o mercado acima)" },
  // ABERTA — o que a Bolsa nunca teve. `matched` = casada e viva; odd é a estrutural.
  "12567916":  { odd: "6,6",  status: /^em aberto \(aguardando resultado — NÃO liquidar; sem resultado\)$/,
                 bruto: "matched", data: "09/09/2026 21:30:00",
                 sel: "Sim (resposta ao mercado — CONFIRMA o mercado acima)" },
};

// ── SPORTSBOOK ──────────────────────────────────────────────────────────────────────────
// `card` é o número que a CASA estampa no bilhete, e ele NÃO é o nosso `[Código:]`: a casa
// mostra o id da COMPRA (`TicketId − 1`). Conferido na tela da Betbra no bilhete aberto
// 885271132847751169, cujo card exibe 885271132847751168.
const ESPERADO_SB = {
  "817057028597719041": { odd: "4,61", status: /^Perdeu → L$/, bruto: "1", data: "04/03/2026 21:30:00",
                          card: "817057028597719040" },
  "885271132847751169": { odd: "3,36",
                          status: /^em aberto \(aguardando resultado — NÃO liquidar; sem resultado\)$/,
                          bruto: "0", data: "12/09/2026 16:00:00",
                          card: "885271132847751168" },
};

// As 3 pernas do cupom, na ORDEM DO TEXTO AGREGADO — que é a ordem da tela, e NÃO a ordem
// do array de `Selections`. O array traz [América MG, Mais de 3.5, Mais de 1.5]; o
// `SelectionId` da agregada é `0VS0|2|1`, os índices na ordem em que a casa os imprime.
// Conferido no card do bilhete aberto, cujas três linhas aparecem na ordem do agregado.
const PERNAS_SB = {
  "817057028597719041": [
    "- Resultado Final 1x2: América MG",
    "- Primeiro Tempo Total de Gols Acima/Abaixo: Mais de 1.5",
    "- Total de Gols Acima/Abaixo: Mais de 3.5",
  ],
  "885271132847751169": [
    "- Fluminense: Não sofrer gol no 1º Tempo: Não",
    "- Vencer Algum Tempo: Atlético MG",
    "- Resultado do 1º Tempo: Atlético MG",
  ],
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

  // ── EXCHANGE ──────────────────────────────────────────────────────────────────────────
  // O host é `mexchange.` SEM NÚMERO (a Bolsa é `mexchange2.`). O guard do inject é
  // `/^mexchange\d*\./i` e `\d*` aceita zero dígitos — passa, mas por sorte medida, não por
  // desenho. Este `href` é o que trava isso: trocar o guard por `\d+` derruba o caso aqui.
  const corpoEx = fixture("betbra.reportsv2.json");
  const baseEx = "https://mexchange-api.betbra.bet.br/api/offers/reportsv2";

  const ex = await rodarInject({
    inject: "bda_inject.js",
    href: "https://mexchange.betbra.bet.br/account/mybets",
    urlInicial: `${baseEx}?offset=0&per-page=20&after-day=2026-09-01&before-day=2026-09-10&timezone-offset=180&status=liquidated`,
    pedido: "__sharpenupBDAReq",
    responder: (url) => (url.includes("/offers/reportsv2") ? corpoEx : null),
    ms: 4000,
  });

  if (!ex.ultima) {
    falhas.push("EXCHANGE: o inject não emitiu nenhuma mensagem");
  } else {
    if (!ex.ultima.fim) falhas.push("EXCHANGE: o inject não sinalizou `fim` (o robô esperaria o teto)");
    // A API tem de sair do domínio da CASA, derivado do host do iframe. Se o inject caísse
    // no domínio da Bolsa (chumbado em vez de derivado), a Betbra capturaria zero — e com
    // cookie de outra casa, sem erro nenhum.
    const foraDeCasa = ex.urls.filter((u) => u.includes("/offers/reportsv2") && !u.includes("mexchange-api.betbra.bet.br"));
    if (foraDeCasa.length) {
      falhas.push(`EXCHANGE: ${foraDeCasa.length} requisição(ões) para fora de mexchange-api.betbra.bet.br — o domínio tem de vir do host do iframe`);
    }

    const replayEx = ex.urls.slice(1);   // urls[0] é a requisição da PÁGINA (o `urlInicial`)
    const janelas = [];
    for (const u of replayEx) {
      const j = _janela(u);
      if (!j) { falhas.push(`EXCHANGE: requisição sem janela de datas: ${u}`); continue; }
      janelas.push(j);
      if (j.dias > 95) falhas.push(`EXCHANGE: janela de ${j.dias} dias — a casa devolve 400 acima de 95`);
    }
    if (!janelas.length) {
      falhas.push("EXCHANGE: o replay não fez nenhuma requisição com janela");
    } else {
      // O histórico da Betbra vai de MAIO/2025 a hoje (403 ofertas, medidas). Um horizonte
      // curto traria só a ponta e ninguém veria falta — o mesmo defeito que na Bolsa
      // exportou 21 de 418.
      const maisAntiga = janelas.map((j) => j.de).sort()[0];
      const cobertos = (Date.now() - Date.parse(maisAntiga)) / 86400000;
      if (cobertos < 1000) {
        falhas.push(`EXCHANGE: replay cobriu só ${Math.round(cobertos)} dias (mais antiga: ${maisAntiga}) — o horizonte é de ~3 anos`);
      }
      // Sem `status` a casa devolve SÓ as liquidadas: a variante das abertas é obrigatória,
      // e é ela que traz as 9 ofertas `matched` vivas desta conta.
      if (!replayEx.some((u) => /status=matched%2Cunmatched|status=matched,unmatched/.test(u))) {
        falhas.push("EXCHANGE: o replay nunca pediu `status=matched,unmatched` — sem isso a casa devolve só as liquidadas e toda aposta em aberto some");
      }
    }

    // 5 ofertas na fixture, 1 sem casamento (`failed`) → 4 bilhetes, um deles ABERTO.
    const bilhetes = ex.ultima.bilhetes || [];
    if (bilhetes.length !== 4) falhas.push(`EXCHANGE: esperava 4 bilhetes (\`failed\` não é bilhete), vieram ${bilhetes.length}`);
    if (ex.ultima.naoCasadas !== 1) falhas.push(`EXCHANGE: esperava naoCasadas=1 (failed), veio ${ex.ultima.naoCasadas}`);

    const fmtEx = content.pegar("formatTicketBDA");
    testes += conferir(falhas, fmtEx, bilhetes, ESPERADO_EX, "EXCHANGE");

    // A ABERTA não pode carregar número de dinheiro resolvido. `push` também não tem `pl`,
    // mas ganha "Retorno: <stake devolvida>" de propósito; aqui não há retorno nenhum.
    const aberta = bilhetes.find((b) => b.ref === "12567916");
    if (aberta) {
      const txt = fmtEx(aberta);
      testes++;
      if (/^L\/P:/m.test(txt)) falhas.push("EXCHANGE 12567916: bilhete ABERTO saiu com linha L/P — a casa não informou lucro nenhum");
      if (/^Retorno:/m.test(txt)) falhas.push("EXCHANGE 12567916: bilhete ABERTO saiu com linha Retorno — retorno de aposta viva é potencial, nunca realizado");
    }
  }

  // ── SPORTSBOOK ────────────────────────────────────────────────────────────────────────
  // Duas rotas, e as duas importam: `history` traz as liquidadas e `open` as vivas. O
  // `responder` separa por caminho — devolver a mesma fixture nas duas esconderia um inject
  // que só chama uma delas.
  const corpoHist = fixture("betbra.sportsbook.json");
  const corpoOpen = fixture("betbra.sportsbook_open.json");
  const origemSb = "https://prod20454-176166310.msjxk.com";

  const sb = await rodarInject({
    inject: "bds_inject.js",
    href: `${origemSb}/br-pt/spbkv4/my-bets/sports`,
    urlInicial: `${origemSb}/api/master/my-bets/history?limit=10&offset=0&lastHours=1M`,
    pedido: "__sharpenupBDSReq",
    responder: (url) => {
      if (url.includes("/my-bets/history")) return corpoHist;
      if (url.includes("/my-bets/open")) return corpoOpen;
      return null;
    },
  });

  if (!sb.ultima) {
    falhas.push("SPORTSBOOK: o inject não emitiu nenhuma mensagem");
  } else {
    if (!sb.ultima.fim) falhas.push("SPORTSBOOK: o inject não sinalizou `fim`");
    const replaySb = sb.urls.slice(1);
    if (!replaySb.length) falhas.push("SPORTSBOOK: o replay não fez nenhuma requisição");
    // `lastHours` é a pergunta estreita da tela: com `1M` a conta do recon da Bolsa devolvia
    // ZERO. Omitir o parâmetro traz o histórico inteiro. O nome mente — `8760` devolve 0.
    if (replaySb.some((u) => /lastHours=/.test(u))) {
      falhas.push("SPORTSBOOK: o replay manteve `lastHours` — a janela da tela esconde o histórico");
    }
    if (!replaySb.some((u) => u.includes("/api/betslip/my-bets/open"))) {
      falhas.push("SPORTSBOOK: o replay nunca chamou `/api/betslip/my-bets/open` — as apostas vivas não estão no `history`");
    }

    const bilhetes = sb.ultima.bilhetes || [];
    if (bilhetes.length !== 2) falhas.push(`SPORTSBOOK: esperava 2 bilhetes (1 liquidado + 1 aberto), vieram ${bilhetes.length}`);

    const fmtSb = content.pegar("formatTicketBDS");
    testes += conferir(falhas, fmtSb, bilhetes, ESPERADO_SB, "SPORTSBOOK");

    // ── O CUPOM DE MESMO JOGO ───────────────────────────────────────────────────────────
    // O coração deste caso. Cada bilhete é UMA aposta de 3 pernas, não uma múltipla de 4.
    for (const b of bilhetes) {
      const esperadas = PERNAS_SB[b.ref];
      if (!esperadas) continue;
      const txt = fmtSb(b);
      testes++;

      const linhasSel = txt.split("\n").filter((l) => l.startsWith("- "));
      if (linhasSel.length !== 3) {
        falhas.push(`SPORTSBOOK ${b.ref}: esperava 3 seleções (as pernas do cupom), vieram ${linhasSel.length}` +
                    (linhasSel.length === 4 ? " — a entrada AGREGADA entrou como se fosse uma 4ª perna" : ""));
      }
      for (let i = 0; i < esperadas.length; i++) {
        if (linhasSel[i] !== esperadas[i]) {
          falhas.push(`SPORTSBOOK ${b.ref}: perna ${i + 1} esperada "${esperadas[i]}", veio "${linhasSel[i] || "(nenhuma)"}"`);
        }
      }
      // O separador " | " da casa não pode vazar para o bloco: ele é a marca de que a
      // entrada agregada subiu inteira, sem ser quebrada em pernas.
      if (linhasSel.some((l) => l.includes(" | "))) {
        falhas.push(`SPORTSBOOK ${b.ref}: uma linha de seleção ainda tem o separador " | " da casa — o cupom não foi quebrado em pernas`);
      }
      // O tipo tem de dizer o que é. "Múltipla (4 seleções)" seria mentira em três frentes:
      // o número, a natureza (mesmo jogo) e o fato de a odd ser única.
      const tipo = linha(txt, "Tipo:");
      if (!/Criador de Apostas/.test(tipo) || !/MESMO jogo/.test(tipo)) {
        falhas.push(`SPORTSBOOK ${b.ref}: tipo deveria declarar o cupom de mesmo jogo, veio "${tipo}"`);
      }
      // As odds das pernas são de MERCADO e não compõem o cupom (o produto delas dá 26,72 e
      // 5,79; o cupom sem boost é 3,49 e 2,89). Publicá-las é oferecer à IA um número que
      // parece conta feita e não é — a família do "zero se disfarça de conta feita".
      if (/Odd da perna/.test(txt)) {
        falhas.push(`SPORTSBOOK ${b.ref}: "Odd da perna" no bloco — as pernas de um bet builder não têm odd própria no cupom`);
      }
      for (const fantasma of ["26,7", "5,79", "26.7"]) {
        if (txt.includes(fantasma)) {
          falhas.push(`SPORTSBOOK ${b.ref}: o produto FALSO das pernas (${fantasma}) vazou para o bloco`);
        }
      }
    }

    // O campo que engana, reconfirmado na Betbra: o potencial não pode aparecer como retorno
    // em bilhete resolvido, e TEM de aparecer rotulado como potencial no aberto.
    const perdido = bilhetes.find((b) => b.ref === "817057028597719041");
    if (perdido) {
      const txt = fmtSb(perdido);
      testes++;
      if (/230,50|230,5/.test(txt)) falhas.push("SPORTSBOOK 817057028597719041: o retorno POTENCIAL (230,50) vazou para o bloco de um bilhete PERDIDO");
      if (linha(txt, "Retorno:") !== "0,00") falhas.push(`SPORTSBOOK 817057028597719041: retorno realizado deveria ser 0,00, veio "${linha(txt, "Retorno:")}"`);
    }
    const viva = bilhetes.find((b) => b.ref === "885271132847751169");
    if (viva) {
      const txt = fmtSb(viva);
      testes++;
      const pot = linha(txt, "Retorno potencial (ainda não liquidado):");
      if (pot !== "672,00") falhas.push(`SPORTSBOOK 885271132847751169: potencial esperado 672,00, veio "${pot}"`);
      if (/^Retorno:/m.test(txt)) falhas.push("SPORTSBOOK 885271132847751169: bilhete ABERTO saiu com linha Retorno — só existe potencial enquanto a aposta vive");
      if (/^L\/P:/m.test(txt)) falhas.push("SPORTSBOOK 885271132847751169: bilhete ABERTO saiu com L/P");
    }
  }

  return { falhas, testes };
}
