// Betpix365 (Altenar / BIA) — 4ª casa do motor, e a PRIMEIRA que não serve o endpoint
// completo por conta própria (s258).
//
// O que sustenta o espelho, MEDIDO no recon ao vivo (09/08/2026):
//   • motor confirmado SEM login: a home carrega `sb2wsdk-cdn-altenar2.biahosted.net`,
//     e o corpo da API traz `integration: "betpix365"`;
//   • MESMO host de gateway das outras três (`sb2bethistory-gateway-altenar2.biahosted.com`);
//   • mesmos arrays `statuses`, mesmo `pageNumber`/`pageSize`, mesmo `isLastPage`;
//   • paginação provada AO VIVO com `pageSize:5`: pág.1 `isLastPage:false` (5 ids),
//     pág.2 `isLastPage:true` (4 ids novos, zero repetido), pág.3 vazia;
//   • mesmo enum contra a faixa do card: 1=`GANHOU / VENCIDO` · 2=`PERDIDO`.
//
// ⚠️ A DIFERENÇA QUE ESTA CASA TROUXE — o inverso da Jogo de Ouro.
// A Jogo de Ouro serve os DOIS widgets e o operador tem de abrir a tela certa. A Betpix365
// serve **só o COMPACTO** (`widgetBetHistory`): a tela "Minhas Apostas" nunca dispara o
// `widgetExpandedBetHistory`, e o detalhe de cada bilhete sai de um `WidgetGetBetDetails`
// **por item** — o anti-padrão do `CLAUDE.md` ("API externa por item = latência E falha
// multiplicadas. Peça a FAIXA.").
//
// Medido: o compacto NÃO traz `selections` em nenhum dos 9 bilhetes (sem pernas, sem
// mercado, sem data de evento) — é estruturalmente insuficiente para o TSV. E o Expanded
// **responde 200 com `selections`** para `integration=betpix365`, reusando os headers da
// própria página. A casa só não o chama.
//
// Daí o desenho, e é isto que este caso trava:
//   • APRENDER a requisição pode vir do compacto (é o único POST que a casa faz);
//   • CONSUMIR resposta continua restrito ao `Expanded` — o corpo do compacto nunca vira
//     bilhete. A regra load-bearing da Jogo de Ouro segue de pé, e o `casos/jogodeouro.mjs`
//     continua provando o outro lado.
//
// ⚠️ SEM AMOSTRA DE ABERTA. A conta tinha 0 apostas em aberto no dia do recon (a aba Aberto
// respondeu `{"isLastPage":true,"bets":[]}` de verdade), então a armadilha do `totalWin`
// potencial NÃO pôde ser verificada nesta casa. Está travada nos casos da VaideBet e da
// Esportiva, sobre o MESMO formatador; aqui o controle negativo prova que o ramo continua
// de pé.
import { rodarInject, carregarContent, fixture, linha } from "../sandbox.mjs";

export const casa = "Betpix365";

// Cada valor lido do CARD da Betpix365 (aba Processado de 09/08/2026, cards expandidos).
//   `evento` → coluna Data do TSV (evento mais recente, UTC→Brasília)
//   `data`   → colocação, do rodapé do card ("08/08 · 09:44")
//   `odd`    → "Cotações totais"
//   `pre`    → o riscado do GOLDEN BOOST; `tela` = como a casa o TRUNCA
const ESPERADO = {
  // 3 pernas · GOLDEN BOOST · riscado "4.50 » 5.80" · rodapé "08/08 · 09:44"
  "5273628588": { evento: "08/08/2026 18:30:00", data: "08/08/2026 09:44:44", odd: "5,8",  stake: "30,00", status: /^Perdeu → L$/, tipo: /^Bet Builder \(mesmo jogo · 3 seleções\)$/, pre: "4,5" },
  "5270230300": { evento: "07/08/2026 19:30:00", data: "07/08/2026 09:39:17", odd: "4,3",  stake: "20,00", status: /^Perdeu → L$/, tipo: /^Bet Builder \(mesmo jogo · 3 seleções\)$/, pre: "3,4" },
  "5263929700": { evento: "05/08/2026 19:00:00", data: "05/08/2026 10:05:00", odd: "4,5",  stake: "30,00", status: /^Perdeu → L$/, tipo: /^Bet Builder \(mesmo jogo · 3 seleções\)$/, pre: "3,5" },
  // Colocada 04/08 05:32Z, jogo 05/08 02:00Z — em Brasília os DOIS caem em 04/08. É a prova
  // de que converter o fuso não é detalhe: sem converter, evento e colocação cairiam em dias
  // diferentes e a coluna Data sairia um dia à frente.
  "5260272324": { evento: "04/08/2026 23:00:00", data: "04/08/2026 02:32:02", odd: "5",    stake: "20,00", status: /^Perdeu → L$/, tipo: /^Bet Builder \(mesmo jogo · 2 seleções\)$/, pre: "4" },
  "5260267237": { evento: "04/08/2026 21:30:00", data: "04/08/2026 02:25:47", odd: "5",    stake: "20,00", status: /^Perdeu → L$/, tipo: /^Bet Builder \(mesmo jogo · 3 seleções\)$/, pre: "4" },
  "5260262220": { evento: "04/08/2026 13:00:00", data: "04/08/2026 02:19:37", odd: "4",    stake: "20,00", status: /^Ganho → W/,  tipo: /^Bet Builder \(mesmo jogo · 3 seleções\)$/, pre: "3,1", retorno: "80,00" },
  // ⭐ O riscado que a TELA TRUNCA: card mostra "3.33 » 4.30", a API traz 3.3334.
  "5260259052": { evento: "04/08/2026 15:00:00", data: "04/08/2026 02:15:55", odd: "4,3",  stake: "20,00", status: /^Perdeu → L$/, tipo: /^Bet Builder \(mesmo jogo · 2 seleções\)$/, pre: "3,3334", tela: "3.33" },
  "5260257589": { evento: "04/08/2026 15:00:00", data: "04/08/2026 02:14:20", odd: "4",    stake: "20,00", status: /^Ganho → W/,  tipo: /^Bet Builder \(mesmo jogo · 2 seleções\)$/, pre: "3", retorno: "80,00" },
  // ⭐ A MÚLTIPLA COM BÔNUS — ver o bloco dedicado no fim do caso. Sem boost (`semBoost`).
  "5255274526": { evento: "02/08/2026 19:30:00", data: "02/08/2026 10:34:05", odd: "4,23", stake: "1,00",  status: /^Ganho → W/,  tipo: /^Múltipla \(3 seleções\)$/, semBoost: true, retorno: "4,23" },
};

// Corpos reais do F12 desta conta — repare no `"integration":"betpix365"`.
const CORPO_RESOLVIDAS = '{"culture":"pt-BR","timezoneOffset":180,"integration":"betpix365","deviceType":1,"numFormat":"en-GB","countryCode":"BR","dateFrom":"2026-07-30T03:00:00.000Z","dateTo":"2026-08-10T02:59:59.999Z","liveOnly":false,"pageNumber":1,"pageSize":10,"statuses":[1,8,2,4,18]}';
const CORPO_ABERTAS   = '{"culture":"pt-BR","timezoneOffset":180,"integration":"betpix365","deviceType":1,"numFormat":"en-GB","countryCode":"BR","dateFrom":"2026-07-30T03:00:00.000Z","dateTo":"2026-08-10T02:59:59.999Z","liveOnly":false,"pageNumber":1,"pageSize":10,"statuses":[0,10,3,20,17]}';

const URL_EXPANDED = "https://sb2bethistory-gateway-altenar2.biahosted.com/api/WidgetReports/widgetExpandedBetHistory";
// O ÚNICO endpoint que a Betpix365 dispara. Mesmo host, mesmo corpo, PATH diferente.
const URL_COMPACTO = "https://sb2bethistory-gateway-altenar2.biahosted.com/api/WidgetReports/widgetBetHistory";
const HREF = "https://www.betpix365.bet.br/user-dashboard/my-bets?option=MY-BETS_MAIN";

// O `Authorization` da página: o gateway é de OUTRA origem e NÃO autentica por cookie.
// O replay tem de reusar este header — sem ele volta 401 (medido: `credentials:"include"`
// sozinho falha).
const HEADERS_PAGINA = { Authorization: "Bearer harness-token-betpix365", "Content-Type": "application/json" };

function servidor() {
  const resolvidas = fixture("betpix365.settled.json");    // 9 bilhetes · isLastPage:true
  const pedidos = [];
  let compactoServido = 0;
  let semAuth = 0;
  const resp = (url, opts) => {
    const body = String((opts && opts.body) || "");
    const hdr = (opts && opts.headers) || {};
    // O compacto responde com ALGO que o inject nunca deve CONSUMIR. Ele pode (e deve) ser
    // usado para APRENDER url+headers, mas se o corpo dele virar bilhete, o fantasma abaixo
    // aparece no lote e o teste acusa.
    if (url.includes("widgetBetHistory") && !url.includes("Expanded")) {
      compactoServido++;
      return JSON.stringify({ isLastPage: true, bets: [{ id: 999999, status: 1, totalStake: 1, totalWin: 2, totalOdds: 2, selections: [] }] });
    }
    if (!url.includes("widgetExpandedBetHistory")) return null;
    // O gateway é de outra origem e exige o Bearer: replay sem header aprendido = 401.
    if (!hdr.Authorization) { semAuth++; return null; }
    pedidos.push(body);
    let o = null;
    try { o = JSON.parse(body); } catch (e) { return null; }
    const sts = Array.isArray(o.statuses) ? o.statuses : [];
    const pag = Number(o.pageNumber) || 1;
    // A conta NÃO tinha aposta em aberto no dia do recon.
    if (sts.includes(0)) return JSON.stringify({ isLastPage: true, bets: [] });
    if (pag === 1) return resolvidas;
    return JSON.stringify({ isLastPage: true, bets: [] });
  };
  return { resp, pedidos, compacto: () => compactoServido, semAuth: () => semAuth };
}

// A sequência REAL da casa: a página dispara SÓ o compacto. O expandido nunca sai dela.
async function umClique(corpoInicial, href) {
  const srv = servidor();
  const { ultima, urls } = await rodarInject({
    inject: "vb_inject.js",          // ← o MESMO da VaideBet/Esportiva/Jogo de Ouro
    href: href || HREF,
    urlInicial: URL_COMPACTO,
    optsInicial: { method: "POST", headers: HEADERS_PAGINA, body: corpoInicial },
    pedido: "__sharpenupVBReq",
    ms: 1200,
    responder: srv.resp,
  });
  return { ultima, pedidos: srv.pedidos, urls, compacto: srv.compacto(), semAuth: srv.semAuth() };
}

export async function rodar() {
  const falhas = [];
  let testes = 0;

  // ── 1. Um clique = a lista inteira, PARTINDO SÓ DO COMPACTO ──────────────────
  let colhido = null;
  for (const [rotulo, corpo] of [["aba Processado", CORPO_RESOLVIDAS], ["aba Aberto", CORPO_ABERTAS]]) {
    const { ultima, pedidos, urls, compacto, semAuth } = await umClique(corpo);
    testes++;
    if (!ultima) { falhas.push(`${rotulo}: o inject não emitiu nenhuma mensagem`); continue; }
    if (!ultima.hook) falhas.push(`${rotulo}: o inject não sinalizou 'hook' rodando em betpix365.bet.br`);
    if (typeof ultima.respostas !== "number" || ultima.respostas < 1)
      falhas.push(`${rotulo}: 'respostas' não foi reportado`);

    const bets = ultima.bets || [];
    if (bets.length !== 9) falhas.push(`${rotulo}: esperava 9 bilhetes (a conta não tinha nenhuma aberta), vieram ${bets.length}`);
    if (!ultima.fim) falhas.push(`${rotulo}: não sinalizou 'fim' — o robô ficaria esperando o teto`);

    // ⭐ O CORAÇÃO DESTA CASA: a página só chamou o COMPACTO, e mesmo assim o inject tem
    // de ter ido buscar o EXPANDED. Sem isso a Betpix365 nasce "hook ATIVO, 0 bilhetes".
    if (!compacto) falhas.push(`${rotulo}: o widget compacto nunca foi servido — a sequência real da casa não foi exercitada`);
    if (!urls.some((u) => u.includes("widgetExpandedBetHistory"))) {
      falhas.push(`${rotulo}: o inject NUNCA pediu o widgetExpandedBetHistory — nesta casa a página ` +
                  "só dispara o compacto, então sem o replay reescrevendo o path não vem bilhete nenhum");
    }
    // …e o corpo do compacto não pode ter virado bilhete.
    if (bets.some((b) => String(b.id) === "999999")) {
      falhas.push(`${rotulo}: o bilhete do widget COMPACTO (widgetBetHistory) entrou no lote — ` +
                  "o inject passou a CONSUMIR um endpoint que não traz `selections`");
    }
    // O Bearer aprendido do compacto tem de viajar no replay.
    if (semAuth) falhas.push(`${rotulo}: ${semAuth} requisição(ões) ao Expanded saíram SEM Authorization — o replay perdeu os headers da página (401 na casa real)`);

    const temAbertas = pedidos.some((b) => { try { return JSON.parse(b).statuses.includes(0); } catch (e) { return false; } });
    const temResolvidas = pedidos.some((b) => { try { return JSON.parse(b).statuses.includes(1); } catch (e) { return false; } });
    if (!temAbertas) falhas.push(`${rotulo}: nunca pediu a aba ABERTA (statuses com 0)`);
    if (!temResolvidas) falhas.push(`${rotulo}: nunca pediu a aba PROCESSADO (statuses com 1)`);
    // O corpo aprendido do COMPACTO tem de ser preservado (culture, integration, numFormat…).
    const p1 = pedidos[0] || "";
    if (!/"integration"\s*:\s*"betpix365"/.test(p1))
      falhas.push(`${rotulo}: o replay perdeu o \`integration\` aprendido do compacto → ${p1.slice(0, 160)}`);
    if (!/"pageSize"\s*:\s*10/.test(p1)) falhas.push(`${rotulo}: pageSize corrompido → ${p1.slice(0, 160)}`);

    if (!colhido && bets.length) colhido = bets;
  }

  if (!colhido) return { falhas: falhas.concat(["nenhum bilhete colhido — o resto do caso não roda"]), testes };

  // ── 2. Leitura bilhete a bilhete, contra o card DA BETPIX365 ──────────────────
  const fmt = carregarContent().pegar("formatTicketVB");
  for (const b of colhido) {
    const id = String(b.id);
    const e = ESPERADO[id];
    if (!e) { falhas.push(`bilhete inesperado na fixture: ${id}`); continue; }
    const txt = fmt(b);
    testes++;

    if (!txt.startsWith(`[Código: ${id}]`)) falhas.push(`${id}: marcador [Código:] ausente/errado`);

    const evento = linha(txt, "Data (evento mais recente):");
    if (evento !== e.evento) falhas.push(`${id}: evento esperado ${e.evento}, veio "${evento}" (é ele que vai para a coluna Data)`);
    const data = linha(txt, "Data (colocação):");
    if (data !== e.data) falhas.push(`${id}: colocação esperada ${e.data}, veio "${data}"`);
    const stake = linha(txt, "Stake:");
    if (stake !== "R$ " + e.stake) falhas.push(`${id}: stake esperada R$ ${e.stake}, veio "${stake}"`);
    const status = linha(txt, "Status:");
    if (!e.status.test(status)) falhas.push(`${id}: status "${status}"`);
    if (!/status=\d+/.test(linha(txt, "Status (API):"))) falhas.push(`${id}: faltou o enum cru`);
    const odd = linha(txt, "Odd:").split(" ")[0];
    if (odd !== e.odd) falhas.push(`${id}: odd esperada ${e.odd}, veio "${odd}"`);
    const tipo = linha(txt, "Tipo:");
    if (!e.tipo.test(tipo)) falhas.push(`${id}: tipo "${tipo}"`);
    const esp = linha(txt, "Esporte:");
    if (!/^Futebol\b/.test(esp)) falhas.push(`${id}: esporte "${esp}" não é o valor oficial do MASTER_ESPORTES`);

    // Boost: 8 de 9 bilhetes desta conta são "GOLDEN BOOST" (`boostProperty: 3` — o mesmo
    // enum que a Esportiva chama de TURBINADA e a Jogo de Ouro de ODDS DE OURO). A tela
    // trunca o riscado; o bloco tem de emitir o valor cheio.
    const marca = txt.split("\n").find((l) => l.startsWith("Marcação da casa: odd turbinada")) || "";
    if (e.semBoost) {
      if (marca) falhas.push(`${id}: bilhete SEM boost ganhou marcação de odd turbinada`);
    } else if (!marca) {
      falhas.push(`${id}: bilhete com GOLDEN BOOST sem a marcação de boost`);
    } else {
      const m = /antes do boost ([\d,]+)/.exec(marca);
      const emitida = m ? m[1] : "";
      if (emitida !== e.pre) falhas.push(`${id}: odd pré-boost esperada ${e.pre}, veio "${emitida}"`);
      if (e.tela && emitida === e.tela.replace(".", ",")) {
        falhas.push(`${id}: emitiu a odd pré-boost TRUNCADA do card (${e.tela}) em vez de ${e.pre}`);
      }
    }

    if (e.retorno) {
      const r = linha(txt, "Retorno:");
      if (r !== "R$ " + e.retorno) falhas.push(`${id}: retorno esperado R$ ${e.retorno}, veio "${r}"`);
      // Regra global do W: a odd que vai ao TSV tem de explicar o retorno até o centavo.
      const n = Number(e.odd.replace(",", ".")), st = Number(e.stake.replace(",", "."));
      const ret = Number(e.retorno.replace(",", "."));
      if (!(Math.abs(n * st - ret) <= 0.01)) falhas.push(`${id}: odd ${e.odd} × stake ${e.stake} não explica o retorno ${e.retorno}`);
    }
  }

  // ── 3. A MÚLTIPLA COM BÔNUS (o que só esta casa trouxe) ──────────────────────
  // O card mostra "Cotações totais 4.08 · Valor total R$1.00 · Ganhos extra 🎁 R$0.15 ·
  // Ganho total R$4.23". O payload traz `totalOdds: 4.08345` e `bonus: 0.15`.
  //
  // `totalWin ÷ stake` = 4,23 ≠ `totalOdds` = 4,08345. É a 1ª casa Altenar em que a odd
  // declarada NÃO explica o retorno — o "Ganhos extra" entra por fora. A regra global do W
  // manda (`Odd = Retorno ÷ Stake`), e a odd declarada só venceria se fechasse ao centavo.
  //
  // Nem `totalOdds` nem o 4.08 do card servem: os dois deixariam a linha com lucro menor
  // que o real. E a tela AINDA trunca (4.08345 → 4.08), então copiar o card erra duas vezes.
  {
    const b = colhido.find((x) => String(x.id) === "5255274526");
    testes++;
    if (!b) {
      falhas.push("5255274526 (múltipla com bônus) não veio na captura");
    } else {
      const txt = fmt(b);
      const odd = linha(txt, "Odd:").split(" ")[0];
      if (odd === "4,08345") falhas.push("5255274526: emitiu `totalOdds` (4,08345) — o bônus 'Ganhos extra' de R$0,15 ficaria fora do P/L");
      if (odd === "4,08") falhas.push("5255274526: emitiu a odd TRUNCADA do card (4,08) — odd nunca se trunca");
      if (odd !== "4,23") falhas.push(`5255274526: odd esperada 4,23 (retorno ÷ stake), veio "${odd}"`);
      // O bônus tem de aparecer no bloco: é ele que explica a diferença para a IA.
      if (!/Marcação da casa: aposta com bônus \(R\$ 0,15\)/.test(txt)) {
        falhas.push("5255274526: o bônus (R$ 0,15) não foi marcado no bloco — a diferença entre odd declarada e retorno ficaria sem explicação");
      }
      // Múltipla de 3 jogos DIFERENTES: não pode virar "mesmo jogo".
      if (/Mesmo jogo/.test(txt)) falhas.push("5255274526: múltipla de 3 jogos distintos marcada como mesmo jogo");
      for (const jogo of ["Internacional vs. Corinthians", "Palmeiras vs. Fortaleza", "Chapecoense vs. Cruzeiro"]) {
        if (!txt.includes(jogo)) falhas.push(`5255274526: o jogo "${jogo}" não apareceu no bloco`);
      }
      // A odd de cada seleção sai cheia — o card mostra 1.55 para o 1.5556 da API.
      if (!txt.includes("Odd da seleção: 1,5556")) {
        falhas.push("5255274526: a odd da 1ª seleção não saiu cheia (1,5556) — o card a trunca em 1.55");
      }
    }
  }

  // ── 4. CONTROLE NEGATIVO ─────────────────────────────────────────────────────
  // Caso espelho passa verde de primeira, e isso não é evidência.
  {
    const base = JSON.parse(fixture("betpix365.settled.json")).bets.find((x) => String(x.id) === "5260262220");
    testes++;
    // (a) O ramo da ABERTA continua de pé — esta conta não tinha nenhuma, então a única
    //     forma de exercitar aqui é sintética, e está declarada como tal.
    const comoAberta = fmt({ ...base, status: 0, remainingTotalWin: 80.0 });
    if (!/em aberto/.test(linha(comoAberta, "Status:"))) falhas.push("controle negativo: status=0 não virou 'em aberto'");
    if (linha(comoAberta, "Retorno:")) falhas.push("controle negativo: aberta emitiu 'Retorno:' — o ramo do potencial quebrou");
    if (linha(comoAberta, "Retorno potencial:") !== "R$ 80,00") falhas.push("controle negativo: aberta sem 'Retorno potencial:' correto");
    testes++;
    // (b) status fora de {0,1,2} sobe CRU.
    const desconhecido = fmt({ ...base, status: 17 });
    if (!/a conferir/.test(desconhecido)) falhas.push("status desconhecido (17) não foi marcado 'a conferir'");
    if (/Ganho → W|Perdeu → L/.test(desconhecido)) falhas.push("status desconhecido (17) virou resultado — proibido");
  }

  // ── 5. Bloco IDÊNTICO ao gerado pelos hosts das casas irmãs ──────────────────
  {
    const { ultima: pelaVB } = await umClique(CORPO_RESOLVIDAS,
      "https://www.vaidebet.bet.br/sports?shareCode=IHLBJGT77FZ#/betHistory");
    const vb = new Map(((pelaVB && pelaVB.bets) || []).map((b) => [String(b.id), b]));
    const bp = new Map(colhido.map((b) => [String(b.id), b]));
    testes++;
    if (vb.size !== bp.size) {
      falhas.push(`espelho: host vaidebet capturou ${vb.size} e host betpix365 ${bp.size} — a captura não pode depender do domínio`);
    } else {
      const diferentes = [];
      for (const [id, b] of bp) {
        const o = vb.get(id);
        if (!o || fmt(o) !== fmt(b)) diferentes.push(id);
      }
      if (diferentes.length) falhas.push(`espelho: ${diferentes.length} bloco(s) diferem entre os hosts (${diferentes.slice(0, 3).join(", ")}…)`);
    }
  }

  return { falhas, testes };
}
