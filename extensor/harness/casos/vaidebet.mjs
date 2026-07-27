// VaideBet (Altenar / BIA) — captura por API `POST /api/WidgetReports/widgetExpandedBetHistory`
// no gateway `sb2bethistory-gateway-altenar2.biahosted.com` (s209).
//
// Trava o que o reconhecimento provou, cruzando o JSON com o que o card da casa renderiza:
//
//   • ABERTA (`status:0`): `totalWin` JÁ VEM PREENCHIDO com o valor POTENCIAL — o bilhete
//     5236294996 é stake 30 com `totalWin:90` e o card mostra "Ganho total R$90,00" como
//     promessa, não como pagamento. Ler isso como retorno realizado transformaria TODA
//     aposta em aberto numa vitória fantasma (foi o incidente da Betano). Só `status:1`
//     autoriza `retorno ÷ stake`. `openStake`/`remainingTotalWin` só existem na aberta.
//   • ENUM de status: 0=aberta · 1=ganha · 2=perdida (provados contra "ABERTO" /
//     "GANHOU / VENCIDO" / "PERDIDO" no card). Os outros valores que as abas pedem
//     (3, 4, 8, 10, 17, 18, 20) NUNCA apareceram num bilhete → sobem CRUS, nunca viram W/L.
//   • ODD: `totalOdds` já é a odd BOOSTADA (o card mostra "2.33 » 3.00": o riscado é
//     `boostedSelection.preBoostedPrice`, 2.3334, TRUNCADO pela tela). Nos 3 W a odd
//     exibida explica o retorno ao centavo (40÷10=4 · 75÷30=2,5 · 120÷30=4), então as duas
//     fontes concordam; a regra global (dinheiro manda no W) fica valendo por segurança.
//   • DATA: `createdDate` (colocação) e `eventDate` (evento) são ISO com `Z` = UTC → BRT.
//     Quem vai para a 1ª coluna do TSV é o EVENTO (`MASTER_OUTPUT §4`: perna mais recente).
//     As duas ABERTAS provam que os dois campos divergem de DIA: colocadas 26/07 21:1x para
//     eventos em 27/07 — usar a colocação gravaria as duas no dia errado.
//   • PAGINAÇÃO: `pageNumber` no corpo do POST, fim autoritativo `isLastPage:true`. As duas
//     abas são o MESMO endpoint mudando o array `statuses` — resolvidas [1,8,2,4,18],
//     abertas [0,10,3,20,17]. O botão "Mostrar mais apostas" da tela não é usado.
import { rodarInject, carregarContent, fixture, linha } from "../sandbox.mjs";

export const casa = "VaideBet";

// evento/colocação lidos do card (o rodapé cinza mostra a colocação; o bloco branco, o evento).
// odd = a "Cotações totais" do card · tipo pelo nº de seleções do bet builder.
const ESPERADO = {
  // ── resolvidas ────────────────────────────────────────────────────────────────
  "5234878919": { evento: "26/07/2026 16:00:00", data: "26/07/2026 14:34:39", odd: "3",   status: /^Perdeu → L$/, tipo: /^Bet Builder \(mesmo jogo · 2 seleções\)$/ },
  "5233893347": { evento: "26/07/2026 16:00:00", data: "26/07/2026 09:40:48", odd: "4",   status: /^Perdeu → L$/, tipo: /^Bet Builder \(mesmo jogo · 3 seleções\)$/ },
  "5232943733": { evento: "26/07/2026 18:30:00", data: "25/07/2026 22:55:50", odd: "2,5", status: /^Perdeu → L$/, tipo: /^Simples$/ },
  "5232941657": { evento: "26/07/2026 17:00:00", data: "25/07/2026 22:55:08", odd: "4",   status: /^Ganho → W/,   tipo: /^Bet Builder \(mesmo jogo · 2 seleções\)$/, retorno: "40,00" },
  "5232940855": { evento: "26/07/2026 15:00:00", data: "25/07/2026 22:54:54", odd: "2,5", status: /^Ganho → W/,   tipo: /^Simples$/, retorno: "75,00" },
  "5232940065": { evento: "26/07/2026 15:00:00", data: "25/07/2026 22:54:39", odd: "4,3", status: /^Perdeu → L$/, tipo: /^Bet Builder \(mesmo jogo · 3 seleções\)$/ },
  // ODDS TURBINADAS (boostProperty 1, o outro tipo de boost) — a odd continua sendo totalOdds.
  "5230926410": { evento: "25/07/2026 21:30:00", data: "25/07/2026 14:04:32", odd: "2",   status: /^Perdeu → L$/, tipo: /^Simples$/ },
  "5229246530": { evento: "26/07/2026 00:00:00", data: "25/07/2026 00:12:25", odd: "4",   status: /^Ganho → W/,   tipo: /^Bet Builder \(mesmo jogo · 3 seleções\)$/, retorno: "120,00" },
  // beisebol (sportTypeId 13) — o payload não traz o NOME do esporte, só o id. O rótulo tem
  // de ser o valor OFICIAL do MASTER_ESPORTES (`Baseball`); no 1º lote real ele saiu como
  // "Beisebol" (sinônimo) e o banco ficou com duas grafias do mesmo esporte.
  "5227473386": { evento: "24/07/2026 20:10:00", data: "24/07/2026 14:24:05", odd: "3,3", status: /^Perdeu → L$/, tipo: /^Simples$/, esporte: /^Baseball\b/ },
  "5226364090": { evento: "24/07/2026 19:45:00", data: "24/07/2026 02:09:54", odd: "4",   status: /^Perdeu → L$/, tipo: /^Simples$/, esporte: /^Baseball\b/ },

  // ── abertas (DIA DIFERENTE: colocadas 26/07, eventos em 27/07) ────────────────
  "5236294996": { evento: "27/07/2026 19:00:00", data: "26/07/2026 21:14:14", odd: "3", status: /em aberto/, tipo: /^Bet Builder \(mesmo jogo · 2 seleções\)$/, aberta: true, potencial: "90,00" },
  "5236292971": { evento: "27/07/2026 19:30:00", data: "26/07/2026 21:13:40", odd: "5", status: /em aberto/, tipo: /^Bet Builder \(mesmo jogo · 3 seleções\)$/, aberta: true, potencial: "150,00" },
};

// Corpos que a página emite ao abrir cada aba (colados do Payload real do F12).
const CORPO_RESOLVIDAS = '{"culture":"pt-BR","timezoneOffset":180,"integration":"vaidebet","deviceType":1,"countryCode":"BR","dateFrom":"2026-07-01T03:00:00.000Z","dateTo":"2026-07-27T02:59:59.999Z","liveOnly":false,"numFormat":"en-GB","pageNumber":1,"pageSize":10,"statuses":[1,8,2,4,18]}';
const CORPO_ABERTAS   = '{"culture":"pt-BR","timezoneOffset":180,"integration":"vaidebet","deviceType":1,"countryCode":"BR","dateFrom":"2026-07-01T03:00:00.000Z","dateTo":"2026-07-27T02:59:59.999Z","liveOnly":false,"numFormat":"en-GB","pageNumber":1,"pageSize":10,"statuses":[0,10,3,20,17]}';

const URL_API = "https://sb2bethistory-gateway-altenar2.biahosted.com/api/WidgetReports/widgetExpandedBetHistory";

// Servidor de mentira: responde pelo `statuses` e pelo `pageNumber` do corpo, como a casa faz.
// É o que prova (a) que a paginação avança de verdade — a página 1 das resolvidas volta
// `isLastPage:false` e o inject TEM de pedir a 2 — e (b) que um clique em qualquer aba traz
// as duas listas.
function servidor() {
  const resolvidas = fixture("vaidebet.settled.json");   // 10 bilhetes · isLastPage:false
  const abertas = fixture("vaidebet.open.json");         //  2 bilhetes · isLastPage:true
  const pedidos = [];
  const resp = (url, opts) => {
    const body = String((opts && opts.body) || "");
    if (!url.includes("widgetExpandedBetHistory")) return null;
    pedidos.push(body);
    let o = null;
    try { o = JSON.parse(body); } catch (e) { return null; }
    const sts = Array.isArray(o.statuses) ? o.statuses : [];
    const pag = Number(o.pageNumber) || 1;
    if (sts.includes(0)) return pag === 1 ? abertas : JSON.stringify({ isLastPage: true, bets: [] });
    if (pag === 1) return resolvidas;
    return JSON.stringify({ isLastPage: true, bets: [] });
  };
  return { resp, pedidos };
}

async function umClique(corpoInicial) {
  const srv = servidor();
  const { ultima, urls } = await rodarInject({
    inject: "vb_inject.js",
    href: "https://www.vaidebet.bet.br/sports?shareCode=IHLBJGT77FZ#/betHistory",
    urlInicial: URL_API,
    corpoInicial: corpoInicial,
    pedido: "__sharpenupVBReq",
    ms: 1200,
    responder: srv.resp,
  });
  return { ultima, pedidos: srv.pedidos, urls };
}

export async function rodar() {
  const falhas = [];
  let testes = 0;

  // ── 1. Um clique = as duas listas, partindo de QUALQUER aba ───────────────────
  let colhido = null;
  for (const [rotulo, corpo] of [["aba Processado", CORPO_RESOLVIDAS], ["aba Aberto", CORPO_ABERTAS]]) {
    const { ultima, pedidos } = await umClique(corpo);
    testes++;
    if (!ultima) { falhas.push(`${rotulo}: o inject não emitiu nenhuma mensagem`); continue; }
    if (!ultima.hook) falhas.push(`${rotulo}: o inject não sinalizou 'hook' (autodiagnóstico cego)`);
    if (typeof ultima.respostas !== "number" || ultima.respostas < 1)
      falhas.push(`${rotulo}: 'respostas' não foi reportado — não dá para separar "não injetei" de "endpoint mudou"`);

    const bets = ultima.bets || [];
    if (bets.length !== 12) falhas.push(`${rotulo}: esperava 12 bilhetes (10 resolvidas + 2 abertas), vieram ${bets.length}`);
    if (!ultima.fim) falhas.push(`${rotulo}: não sinalizou 'fim' — o robô ficaria esperando o teto`);

    // A 2ª página das resolvidas só é pedida se a paginação ativa funcionar (a 1ª volta
    // `isLastPage:false`). Sem isto o robô traria só os 10 primeiros e nunca saberia.
    const p2 = pedidos.find((b) => { try { const o = JSON.parse(b); return o.pageNumber === 2 && !o.statuses.includes(0); } catch (e) { return false; } });
    if (!p2) falhas.push(`${rotulo}: nenhuma requisição pediu a página 2 das resolvidas — paginação ativa não avançou`);
    else if (!/"pageSize"\s*:\s*10/.test(p2)) falhas.push(`${rotulo}: pageSize foi corrompido ao avançar a página → ${p2}`);

    // As duas abas têm de ser buscadas mesmo partindo de uma só.
    const temAbertas = pedidos.some((b) => { try { return JSON.parse(b).statuses.includes(0); } catch (e) { return false; } });
    const temResolvidas = pedidos.some((b) => { try { return JSON.parse(b).statuses.includes(1); } catch (e) { return false; } });
    if (!temAbertas) falhas.push(`${rotulo}: nunca pediu a aba ABERTA (statuses com 0) — aposta em aberto sumiria`);
    if (!temResolvidas) falhas.push(`${rotulo}: nunca pediu a aba PROCESSADO (statuses com 1)`);

    if (!colhido && bets.length) colhido = bets;
  }

  if (!colhido) return { falhas: falhas.concat(["nenhum bilhete colhido — o resto do caso não roda"]), testes };

  // ── 2. Leitura bilhete a bilhete, contra o card ───────────────────────────────
  const fmt = carregarContent().pegar("formatTicketVB");
  for (const b of colhido) {
    const id = String(b.id);
    const e = ESPERADO[id];
    if (!e) { falhas.push(`bilhete inesperado na fixture: ${id}`); continue; }
    const txt = fmt(b);
    testes++;

    if (!txt.startsWith(`[Código: ${id}]`)) falhas.push(`${id}: marcador [Código:] ausente/errado na 1ª linha`);

    const evento = linha(txt, "Data (evento mais recente):");
    if (evento !== e.evento) falhas.push(`${id}: data do EVENTO esperada ${e.evento}, veio "${evento}" (é ela que vai para a coluna Data do TSV)`);

    const data = linha(txt, "Data (colocação):");
    if (data !== e.data) falhas.push(`${id}: colocação esperada ${e.data}, veio "${data}"`);

    const status = linha(txt, "Status:");
    if (!e.status.test(status)) falhas.push(`${id}: status "${status}"`);

    // Enum CRU da casa — é ele que a CASA_VAIDEBET.md traduz.
    if (!/status=\d+/.test(linha(txt, "Status (API):")))
      falhas.push(`${id}: faltou o enum cru na linha "Status (API):" — um estado novo viraria chute`);

    const odd = linha(txt, "Odd:").split(" ")[0];
    if (odd !== e.odd) falhas.push(`${id}: odd esperada ${e.odd}, veio "${odd}"`);

    const tipo = linha(txt, "Tipo:");
    if (!e.tipo.test(tipo)) falhas.push(`${id}: tipo "${tipo}"`);

    // O rótulo do esporte é copiado pela IA para a coluna Esporte: se não for o valor
    // OFICIAL do MASTER_ESPORTES, o mesmo esporte entra no banco com duas grafias.
    if (e.esporte) {
      const esp = linha(txt, "Esporte:");
      if (!e.esporte.test(esp)) falhas.push(`${id}: esporte "${esp}" não é o valor oficial do MASTER_ESPORTES`);
    }

    if (e.retorno) {
      const r = linha(txt, "Retorno:");
      if (r !== "R$ " + e.retorno) falhas.push(`${id}: retorno esperado R$ ${e.retorno}, veio "${r}"`);
    }

    if (e.aberta) {
      // O CORAÇÃO DESTA CASA: `totalWin` de uma aberta é POTENCIAL. O 5236294996 tem stake 30
      // e totalWin 90 — se escorregar para a regra do W, vira lucro fantasma de R$ 60.
      if (/→ [WLV]\b/.test(status)) falhas.push(`${id}: aberta recebeu código de resultado — proibido`);
      if (/Ganho → W/.test(txt)) falhas.push(`${id}: ABERTA virou vitória — totalWin foi lido como retorno realizado`);
      const pot = linha(txt, "Retorno potencial:");
      if (pot !== "R$ " + e.potencial) falhas.push(`${id}: retorno potencial esperado R$ ${e.potencial}, veio "${pot}"`);
      if (linha(txt, "Retorno:")) falhas.push(`${id}: aberta emitiu linha "Retorno:" — só potencial é permitido`);
    }
  }

  // ── 3. Casos SINTÉTICOS (não há amostra real na conta do Feca) ────────────────
  // Construídos a partir do dado real, travam só COMPORTAMENTO estrutural — nenhum valor
  // de tela é inventado aqui.
  const bruto = JSON.parse(fixture("vaidebet.settled.json"));
  const acha = (id) => bruto.bets.find((b) => String(b.id) === id);

  // 3a. Status desconhecido (4, 8, 17, 18, 20 são pedidos pelas abas e nunca vistos num
  //     bilhete): tem de subir CRU e marcado, jamais virar W/L pelo dinheiro.
  testes++;
  const desconhecido = fmt({ ...acha("5232941657"), status: 17 });
  if (!/a conferir/.test(desconhecido)) falhas.push("status desconhecido (17) não foi marcado 'a conferir' — vira chute");
  if (/Ganho → W|Perdeu → L/.test(desconhecido)) falhas.push("status desconhecido (17) foi convertido em resultado — proibido");

  // 3b. Múltipla de jogos diferentes: o Feca só tem simples e bet builder, mas o formato
  //     precisa aguentar N seleções sem chamar de "mesmo jogo".
  testes++;
  const a = acha("5232943733"), b2 = acha("5230926410");
  const multipla = fmt({ ...a, id: 9999999999, selectionsCount: 2, totalOdds: 5,
                         selections: [a.selections[0], b2.selections[0]] });
  if (!/^Múltipla \(2 seleções\)$/m.test(linha(multipla, "Tipo:")))
    falhas.push(`múltipla de 2 jogos diferentes saiu como "${linha(multipla, "Tipo:")}"`);
  if (/Mesmo jogo/.test(multipla)) falhas.push("múltipla de jogos DIFERENTES foi marcada como mesmo jogo");

  // 3c. Cashout: a conta não tem nenhum e `cashOutValue` veio 0 até nas abertas com botão
  //     ativo (o valor oferecido vem de outro endpoint). Se um dia vier preenchido, tem de
  //     aparecer no bloco para a IA aplicar a regra de cashout — nunca ser ignorado.
  testes++;
  const comCashout = fmt({ ...acha("5232940855"), cashOutValue: 45 });
  if (!/[Cc]ash *[Oo]ut/.test(comCashout)) falhas.push("cashOutValue > 0 não apareceu no bloco — a regra de cashout ficaria invisível para a IA");

  return { falhas, testes };
}
