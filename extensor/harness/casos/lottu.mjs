// Lottu (motor NGBras) — captura por API `/bet` + detalhe por item (s290).
//
// Motor NOVO no Sharpen, o segundo em dois dias: não é Altenar, BetBy, BetConstruct, Kambi,
// BlueBrown nem bwin/Entain. Confirmado ANTES do login, pelo método de sempre — a home não
// carrega asset de motor nenhum (só `widgets.sir.sportradar.com`, que é widget de
// estatística, não plataforma de apostas), e a API vive em host próprio.
//
// O que sustenta o modo, MEDIDO ao vivo (24/08/2026), não deduzido:
//   • `GET /bet?initial_date=…Z&final_date=…Z&status=ALL` devolve a FAIXA INTEIRA numa
//     chamada — 152 bilhetes, 84 KB, sem paginação e sem cursor. É o "peça a FAIXA" do
//     CLAUDE.md acontecendo de graça;
//   • as ABERTAS têm forma própria: `GET /bet?status=OPEN&page=N` (paginado, sem datas);
//   • autenticação por header (`authorization` + `ngx-source`), não cookie: uma chamada
//     sem eles morre no CORS. O replay reusa os headers da requisição REAL;
//   • **a lista NÃO traz as seleções** — só `events_qty`. Jogo, mercado e a data do EVENTO
//     (que é a coluna Data do TSV) só existem em `GET /bet/{_id}`, uma chamada POR BILHETE.
//     É o anti-padrão do CLAUDE.md ("API externa por item"), aqui inevitável: o freio de
//     dias + `stopId` é o que impede as 152 chamadas virarem rotina.
//
// ⚠️ A ARMADILHA CENTRAL DESTA CASA, e ela é pior que a da VaideBet.
// `return_value`/`gross_return_value` são o retorno **POTENCIAL**, sempre — inclusive nas
// PERDIDAS. Medido nos 152 bilhetes da conta: **114 de 114 perdidas** têm retorno
// preenchido, e em **114 de 114** ele é exatamente `stake × odd`. Na VaideBet o campo só
// mentia na aberta; aqui ele mente em toda linha que não ganhou. Ler dinheiro como
// realizado transformaria **toda perdida em vitória**.
// Consequência de desenho: nesta casa **só o `status` decide** W/L. O dinheiro não é régua.
import { rodarInject, carregarContent, fixture, linha } from "../sandbox.mjs";

export const casa = "Lottu";

// ⚠️ TIPO: os dois bilhetes são "Simples de X" no card e têm UMA seleção na API — e mesmo
// assim são MÚLTIPLA. `CASA_LOTTU §2.2` (s41, escrita a partir do print) já dizia: a Lottu
// vende Desafios, condições combinadas sobre o mesmo jogo, e o `&` na resposta é a marca.
// Classificar pela estrutura da API mandaria todos para "Simples" — a regra da casa é mais
// velha que a captura e vence.
//
// Valores lidos do CARD da Lottu (aba Todas, filtro 01/06→24/08 de 2026), não do código.
// As duas datas são ISO UTC e viram America/Sao_Paulo.
const ESPERADO = {
  // Ganha. Card: "6512222 · Simples de 3.50 · Aposta R$ 50,00 · Retorno R$ 175,00".
  "6512222": { evento: "29/07/2026 21:29:25", colocacao: "29/07/2026 00:27:30", odd: "3,5",
               stake: "50,00", status: /^Ganho → W/, tipo: /^Múltipla \(Desafio · 2 condições no mesmo jogo\)$/, retorno: "175,00",
               jogo: "Vitória x Palmeiras" },

  // Perdida — e é ELA que prova a armadilha: o card estampa "Retorno R$ 125,00" numa aposta
  // que PERDEU, porque 25 × 5 = 125 é o potencial. O bloco não pode chamar isso de retorno.
  "6585838": { evento: "01/08/2026 17:29:52", colocacao: "01/08/2026 15:45:55", odd: "5",
               stake: "25,00", status: /^Perdeu → L$/, tipo: /^Múltipla \(Desafio · 2 condições no mesmo jogo\)$/, potencialMentiroso: "125,00",
               jogo: "Vasco x Fluminense" },

  // ⚠️ O CRIADOR DE APOSTAS COM BOOST (s371) — o bilhete que custou R$ 1.170,93 de P/L.
  // Card: "8410665 · Simples de 7.38 · ⚡ Bônus +25% · Aposta R$ 100,00 · Bônus R$ 184,50 ·
  // Retorno R$ 922,50". A API manda `return_value: 738` (a odd NUA) e o bônus separado em
  // `promotions.odds_boost.value: 184.5`. O retorno é a SOMA, e a odd que vale na planilha
  // é 9,225 (= 922,50 ÷ 100), não 7,38.
  // O mesmo bilhete prova as outras três: a perna NÃO tem `answer` (vinha vazia), o evento
  // NÃO tem `question` (o jogo sumia) e a odd 7,3779 se repete nas três pernas (é a do
  // CUPOM, e multiplicá-las daria 401).
  "8410665": { evento: "20/09/2026 18:30:00", colocacao: "20/09/2026 12:55:20", odd: "7,38",
               stake: "100,00", status: /^Ganho → W/, tipo: /^Múltipla \(Criador de Apostas · 3 seleções no MESMO jogo\)$/,
               retorno: "922,50", jogo: "Flamengo x RB Bragantino",
               boost: { pct: 25, bonus: "184,50", base: "738,00", oddEfetiva: "9,225" },
               esporteDaCasa: "Soccer",
               pernasCruas: ["BOTH_TEAMS_TO_SCORE_YES", "GOALS_OVER_UNDER", "UNDER", "1.5",
                             "CORNERS_OVER_UNDER", "9.5", "FIRST_TIME"] },
};

const HOST = "https://alpha-sb.ngbras.com";
const HREF = "https://www.lottu.bet.br/user-dashboard/my-bets?option=MY-BETS_MAIN";

// Servidor de mentira: responde pelo `status` da QUERY e serve o detalhe por `_id`, como a
// casa faz. A aba OPEN volta vazia (a conta não tinha aposta viva no reconhecimento).
function servidor() {
  const lista = JSON.parse(fixture("lottu.bets.json"));
  const detalhes = JSON.parse(fixture("lottu.detalhes.json"));
  const pedidos = [];
  const resp = (url) => {
    const u = String(url);
    if (!u.includes("/bet")) return null;
    pedidos.push(u);
    const det = /\/bet\/([a-f0-9]{24})/i.exec(u);
    if (det) {
      const d = detalhes.find((x) => x._id === det[1]);
      return d ? JSON.stringify(d) : JSON.stringify({});
    }
    const q = new URL(u).searchParams;
    if (q.get("status") === "OPEN") return "[]";          // sem aposta viva na amostra
    return JSON.stringify(lista);
  };
  return { resp, pedidos };
}

async function umClique() {
  const srv = servidor();
  const { ultima } = await rodarInject({
    inject: "lt_inject.js",
    href: HREF,
    urlInicial: HOST + "/bet?status=OPEN&page=0",
    // Os headers são o ponto: o inject SÓ aprende uma requisição que traga `authorization`.
    // Guardar uma sem ele deixaria o replay batendo em CORS/401 para sempre, e a casa
    // devolveria lista vazia com HTTP 200 — falha muda. Sem `optsInicial` o replay nem
    // arranca, e é assim que este caso prova a guarda.
    optsInicial: { method: "GET", headers: { "authorization": "Bearer TOKEN_DE_TESTE",
                                             "ngx-source": "DESKTOP", "accept": "application/json" } },
    pedido: "__sharpenupLTReq",
    ms: 1500,
    responder: srv.resp,
  });
  return { ultima, pedidos: srv.pedidos };
}

export async function rodar() {
  const falhas = [];
  let testes = 0;

  const { ultima, pedidos } = await umClique();
  testes++;
  if (!ultima) return { falhas: ["o inject não emitiu nenhuma mensagem"], testes };
  if (!ultima.hook) falhas.push("não sinalizou 'hook' — o autodiagnóstico fica cego");
  if (typeof ultima.respostas !== "number" || ultima.respostas < 1)
    falhas.push("'respostas' não reportado — não separa \"não injetei\" de \"endpoint mudou\"");
  if (!ultima.fim) falhas.push("não sinalizou 'fim' — o robô esperaria o teto");

  const bets = ultima.bets || [];
  if (bets.length !== 3) falhas.push(`esperava 3 bilhetes na fixture, vieram ${bets.length}`);

  // A LISTA tem de ser pedida por FAIXA DE DATAS. Sem `initial_date`/`final_date` a casa
  // responde 200 com `[]` — foi o que aconteceu no reconhecimento e me fez achar, por um
  // momento, que a conta estava vazia. Falha silenciosa: HTTP 200, zero bilhete.
  testes++;
  const comFaixa = pedidos.find((u) => /initial_date=/.test(u) && /final_date=/.test(u));
  if (!comFaixa) falhas.push("nenhuma requisição mandou initial_date/final_date — a casa devolveria [] com HTTP 200");

  // As ABERTAS têm forma PRÓPRIA (status=OPEN, paginado). Sem este pedido, aposta viva
  // sumiria do lote — e ela é justamente a que ainda não tem amostra nesta conta.
  testes++;
  if (!pedidos.some((u) => /status=OPEN/.test(u)))
    falhas.push("nunca pediu a aba OPEN — aposta viva sumiria do lote");

  // O DETALHE por item é o que traz jogo, mercado e a data do evento. Um bilhete sem
  // detalhe não tem coluna Data.
  testes++;
  const detalhes = pedidos.filter((u) => /\/bet\/[a-f0-9]{24}/i.test(u));
  if (detalhes.length !== 3)
    falhas.push(`esperava 1 detalhe por bilhete (3), vieram ${detalhes.length}`);

  // ── Leitura bilhete a bilhete, contra o card ──────────────────────────────────
  const fmt = carregarContent().pegar("formatTicketLT");
  for (const b of bets) {
    const id = String(b.code || "");
    const e = ESPERADO[id];
    if (!e) { falhas.push(`bilhete inesperado na fixture: ${id}`); continue; }
    const txt = fmt(b);
    testes++;

    if (!txt.startsWith(`[Código: ${id}]`)) falhas.push(`${id}: marcador [Código:] ausente/errado na 1ª linha`);

    const evento = linha(txt, "Data (evento mais recente):");
    if (evento !== e.evento) falhas.push(`${id}: data do EVENTO esperada ${e.evento}, veio "${evento}"`);

    const colocacao = linha(txt, "Data (colocação):");
    if (colocacao !== e.colocacao) falhas.push(`${id}: colocação esperada ${e.colocacao}, veio "${colocacao}"`);

    const stake = linha(txt, "Stake:");
    if (stake !== "R$ " + e.stake) falhas.push(`${id}: stake esperada R$ ${e.stake}, veio "${stake}"`);

    const status = linha(txt, "Status:");
    if (!e.status.test(status)) falhas.push(`${id}: status "${status}"`);

    if (!/status=\w+/.test(linha(txt, "Status (API):")))
      falhas.push(`${id}: faltou o enum cru na linha "Status (API):"`);

    const odd = linha(txt, "Odd:").split(" ")[0];
    if (odd !== e.odd) falhas.push(`${id}: odd esperada ${e.odd}, veio "${odd}"`);

    const tipo = linha(txt, "Tipo:");
    if (!e.tipo.test(tipo)) falhas.push(`${id}: tipo "${tipo}"`);

    if (!txt.includes(e.jogo)) falhas.push(`${id}: o jogo "${e.jogo}" não aparece no bloco — veio do detalhe?`);

    // ⚠️ A casa NÃO informa esporte em campo nenhum (só `championship` e `country`). O bloco
    // tem de dizer isso explicitamente, senão a IA inventa a coluna Esporte em silêncio.
    // (só no DESAFIO, onde `__t` vale "Challenge" e não há esporte nenhum na resposta. No
    // Criador de Apostas a casa informa, e aí deduzir seria pior — ver `esporteDaCasa`.)
    if (!e.esporteDaCasa) {
      const esp = linha(txt, "Esporte:");
      if (!/não informad/i.test(esp))
        falhas.push(`${id}: "Esporte:" devia declarar que a casa não informa, veio "${esp}"`);
    }

    if (e.retorno) {
      const r = linha(txt, "Retorno:");
      if (!r.startsWith("R$ " + e.retorno)) falhas.push(`${id}: retorno esperado R$ ${e.retorno}, veio "${r}"`);
    }

    // ── BOOST: o dinheiro pago POR FORA da odd ────────────────────────────────
    // O coração do caso da s371. Três asserções distintas, porque um gate que confere só o
    // retorno deixaria a odd passar errada — e é a odd que vai para a coluna da planilha.
    if (e.boost) {
      // (a) o retorno TEM de ser a soma. Se sair 738,00, o P/L nasce R$ 184,50 curto.
      const r = linha(txt, "Retorno:");
      if (!r.startsWith("R$ " + e.retorno))
        falhas.push(`${id}: com boost de ${e.boost.pct}%, o retorno tem de ser R$ ${e.retorno} ` +
                    `(R$ ${e.boost.base} da odd + R$ ${e.boost.bonus} de bônus), veio "${r}"`);
      // (b) a decomposição fica na MESMA linha: o número sozinho não deixa ninguém conferir.
      if (!r.includes(e.boost.bonus) || !r.includes(e.boost.base))
        falhas.push(`${id}: a linha do retorno não mostra a decomposição (R$ ${e.boost.base} + R$ ${e.boost.bonus}) — veio "${r}"`);
      // (c) a ODD EFETIVA, que é a que vai para a planilha. Sem ela a IA escreve 7,38.
      const oe = linha(txt, "Odd efetiva (COM o boost de " + e.boost.pct + "%):");
      if (!oe.startsWith(e.boost.oddEfetiva))
        falhas.push(`${id}: esperava a odd efetiva ${e.boost.oddEfetiva} (= retorno ÷ stake), veio "${oe}"`);
      if (!/Retorno ÷ Stake/.test(oe))
        falhas.push(`${id}: a odd efetiva não diz de onde vem — sem isso a IA não sabe qual das duas usar`);
      // (d) a odd base tem de sair MARCADA, senão as duas odds no bloco viram ambiguidade.
      if (!/SEM o boost/.test(linha(txt, "Odd:")))
        falhas.push(`${id}: a linha "Odd:" não avisa que é a odd BASE — duas odds sem rótulo é pior que uma errada`);
    }

    // ── CRIADOR DE APOSTAS: a perna sem `answer` ──────────────────────────────
    if (e.pernasCruas) {
      for (const campo of e.pernasCruas)
        if (!txt.includes(campo))
          falhas.push(`${id}: o campo cru "${campo}" da perna não chegou ao bloco — a descrição nasce "Mercado Especial - REVISAR"`);
      // A linha da seleção não pode sair VAZIA (era o defeito: `e.answer || ""`).
      for (const ln of txt.split("\n"))
        if (/^- \s*\[/.test(ln)) falhas.push(`${id}: seleção sem descrição nenhuma — "${ln}"`);
      // A odd do CUPOM repetida por perna não pode ser impressa como odd da seleção.
      if (/Odd da seleção/.test(txt))
        falhas.push(`${id}: imprimiu "Odd da seleção" num Criador de Apostas — a odd é do CUPOM, e multiplicar as 3 daria 401`);
      if (!/NÃO têm odd própria/.test(txt))
        falhas.push(`${id}: faltou o aviso de que as pernas não têm odd própria`);
    }

    // ⚠️ `includes` NÃO serve aqui: a mesma frase aparece na linha da PERNA (indentada), e
    // um teste feito com ela deixou passar a mutação que apagava o esporte do CABEÇALHO.
    // `linha()` casa por início de linha, então só enxerga o cabeçalho — que é o que a IA
    // lê para preencher a coluna Esporte.
    if (e.esporteDaCasa) {
      const cab = linha(txt, "Esporte (campo __t da casa):");
      if (!cab.startsWith(e.esporteDaCasa))
        falhas.push(`${id}: o CABEÇALHO devia declarar o esporte que a casa informa ` +
                    `(__t = ${e.esporteDaCasa}), veio "${cab}"`);
      if (/^Esporte: não informad/m.test(txt))
        falhas.push(`${id}: a casa INFORMA o esporte e o bloco mandou deduzir assim mesmo`);
    }

    // O CORAÇÃO DO CASO: na PERDIDA, o campo de dinheiro é potencial e NÃO pode sair como
    // "Retorno:". Se sair, a IA lê lucro onde houve prejuízo — 114 linhas da conta.
    if (e.potencialMentiroso) {
      if (linha(txt, "Retorno:"))
        falhas.push(`${id}: PERDIDA emitiu "Retorno:" — o campo é potencial (${e.potencialMentiroso}), não dinheiro recebido`);
      if (/Ganho → W/.test(txt)) falhas.push(`${id}: PERDIDA virou vitória`);
      // Exige o valor E o aviso na mesma linha: o número sozinho não protege ninguém — é a
      // frase que impede a IA de ler 125 como dinheiro recebido numa aposta perdida.
      const pot = linha(txt, "Retorno potencial:");
      if (!pot.startsWith("R$ " + e.potencialMentiroso))
        falhas.push(`${id}: esperava "Retorno potencial: R$ ${e.potencialMentiroso}…", veio "${pot}"`);
      if (!/POTENCIAL|não é ganho/i.test(pot))
        falhas.push(`${id}: a linha do potencial não avisa que o valor NÃO é ganho — o número sozinho engana`);
    }
  }

  // ── CONTROLE NEGATIVO ─────────────────────────────────────────────────────────
  {
    const perdida = JSON.parse(fixture("lottu.detalhes.json")).find((b) => b.status === "LOST");
    testes++;
    // (a) o MESMO bilhete, com status WON, TEM de virar W com "Retorno:" — se não virar, a
    //     asserção da perdida não estava provando nada.
    const comoW = fmt({ ...perdida, status: "WON" });
    if (!/Ganho → W/.test(comoW) || !linha(comoW, "Retorno:"))
      falhas.push("controle negativo: o bilhete com status=WON não virou W com 'Retorno:' — o teste da PERDIDA era vácuo");

    testes++;
    // (b) estado fora de {WON,LOST,OPEN,...} sobe CRU e marcado. Aqui isso pesa mais que em
    //     qualquer outra casa: como o dinheiro vem preenchido em TODA linha, um estado
    //     desconhecido tratado pelo dinheiro viraria W automático.
    const inedito = fmt({ ...perdida, status: "CASHED_OUT" });
    if (!/a conferir/.test(inedito)) falhas.push("estado desconhecido não foi marcado 'a conferir' — vira chute");
    if (/Ganho → W|Perdeu → L/.test(inedito)) falhas.push("estado desconhecido foi convertido em resultado — proibido");

    // (c) O BÔNUS É POTENCIAL COMO TODO O RESTO NESTA CASA. `odds_boost.value` vem
    //     preenchido na PERDIDA também (medido: 2 de 2 na conta). Somá-lo fora do `WON`
    //     repetiria, com o bônus, exatamente o erro que o `return_value` já ensinou —
    //     e desta vez inflando o P/L em vez de encolhê-lo.
    const comBoost = JSON.parse(fixture("lottu.detalhes.json")).find((b) => b.code === "8410665");
    testes++;
    const perdeuComBoost = fmt({ ...comBoost, status: "LOST" });
    if (linha(perdeuComBoost, "Retorno:"))
      falhas.push("controle negativo: PERDIDA com boost emitiu 'Retorno:' — o bônus não é dinheiro recebido");
    if (/922,50/.test(perdeuComBoost))
      falhas.push("controle negativo: o bônus foi somado numa aposta PERDIDA — R$ 184,50 de lucro fantasma");
    if (!/TAMBÉM é potencial/.test(perdeuComBoost))
      falhas.push("controle negativo: a perdida com boost não avisa que o bônus é potencial");

    testes++;
    // (d) O CAMINHO INVERSO, que prova que a asserção do ganho não é vácuo: sem boost, o
    //     retorno é o `return_value` puro e NÃO pode aparecer odd efetiva nenhuma.
    const semBoost = fmt({ ...comBoost, promotions: { odds_boost: { percentage: 0, value: 0 } } });
    if (linha(semBoost, "Retorno:") !== "R$ 738,00")
      falhas.push(`controle negativo: sem boost o retorno tem de ser R$ 738,00, veio "${linha(semBoost, "Retorno:")}"`);
    if (/Odd efetiva/.test(semBoost))
      falhas.push("controle negativo: bilhete SEM boost ganhou linha de odd efetiva — duas odds onde só há uma");
  }

  return { falhas, testes };
}
