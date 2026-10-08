// BetMartini (Altenar / BIA) — 7ª casa do motor, ESPELHO da VaideBet/Esportiva/Estrela Bet/
// Betrebels (s402).
//
// Sem inject, formatador ou robô próprios: reusa `vb_inject.js`, `formatTicketVB` e
// `roboVBPassive`. Este caso prova que o MESMO inject engancha NA ABA desta casa e que o
// `integration` dela sobrevive ao replay — é a única coisa que a separa das irmãs no gateway.
//
// O que sustenta o espelho, medido no recon (08/10/2026, Chrome, sem login):
//   • `betmartini.com/sports` redireciona para `/en-gb/sports` e carrega
//     `sb2wsdk-altenar2.biahosted.com` NA PRÓPRIA página (`window.altenarWSDK` existe no topo),
//     e chama `sb2frontend-altenar2`/`sb2integration-altenar2` com `integration=betmartini`;
//   • mesmo cluster `altenar2` das irmãs, e o `RX` do inject casa por PATH.
//
// ⚠ PROCEDÊNCIA: a casa entrou SEM conta de teste, então não há fixture DELA. Os bilhetes são
// os da Estrela Bet (`estrelabet.*.json`), e os CORPOS abaixo são os dela com o `integration`
// trocado — dito em voz alta em vez de fingir amostra. `culture`, `countryCode` e
// `timezoneOffset` reais da BetMartini NÃO foram medidos (o site abre em `en-gb`, então o
// `culture` real provavelmente é inglês — e os nomes de mercado também).
//
// O QUE ESTE CASO **NÃO** COBRE: a leitura campo a campo (odd, stake, data, aberta, bônus,
// TAB no nome) está travada em `estrelabet.mjs` e `esportiva.mjs`; o CORS deste tenant não foi
// medido (o fallback sem credencial do `pedirPagina` cobre os dois lados); e a MOEDA: o
// `formatTicketVB` rotula todo dinheiro como R$ e não escreve `Moeda:`, então numa conta em
// outra moeda a conversão vale pela moeda do CADASTRO e o aviso de moeda divergente não dispara.
// Na 1ª captura real, troque a fixture pela da conta e leia os cards na tela.
import { rodarInject, carregarContent, fixture } from "../sandbox.mjs";

export const casa = "BetMartini";

const CORPO = (statuses) => JSON.stringify({
  culture: "pt-BR", timezoneOffset: 180, integration: "betmartini", deviceType: 1, numFormat: "en-GB",
  countryCode: "BR", dateFrom: "2026-08-20T03:00:00.000Z", dateTo: "2026-08-31T02:59:59.999Z",
  liveOnly: false, pageNumber: 1, pageSize: 10, statuses,
});
const CORPO_RESOLVIDAS = CORPO([1, 8, 2, 4, 18]);
const CORPO_ABERTAS = CORPO([0, 10, 3, 20, 17]);

const URL_API = "https://sb2bethistory-gateway-altenar2.biahosted.com/api/WidgetReports/widgetExpandedBetHistory";
const HREF = "https://www.betmartini.com/en-gb/sports";
const HEADERS_PAGINA = { Authorization: "Bearer harness-token-betmartini", "Content-Type": "application/json" };

// ⚠ O GATEWAY DA BETREBELS DEVOLVE VAZIO PARA JANELA LARGA — medido ao vivo (06/10/2026, conta
// do Feca, 7 abertas na tela). NESTA casa não foi medido; a seção 4 prova que o conserto do
// `vb_inject` vale no host dela, e que não recua quando o gateway responde à janela larga: a MESMA requisição de abertas com `dateFrom` a 730 dias voltou
// `200 · {"isLastPage":true,"bets":[]}`, e com 365, 90 e 30 dias voltou as 7. Não é erro, é
// lista vazia "válida": o replay lia "conta sem aberta" e parava, e a 1ª captura real subiu
// as 8 processadas e NENHUMA aberta. `tetoDias` reproduz isso; a seção 4 trava o conserto.
// O limite exato entre 365 e 730 não foi medido.
const TETO_MEDIDO = 365;

function servidor({ tetoDias = null } = {}) {
  const resolvidas = fixture("estrelabet.settled.json");   // 8 bilhetes · isLastPage:true
  const abertas = fixture("estrelabet.open.json");         // 4 bilhetes · isLastPage:true
  const pedidos = [];
  const resp = (url, opts) => {
    if (!url.includes("widgetExpandedBetHistory")) return null;
    const body = String((opts && opts.body) || "");
    pedidos.push(body);
    let o = null;
    try { o = JSON.parse(body); } catch (e) { return null; }
    if (tetoDias != null) {
      const span = (Date.parse(o.dateTo) - Date.parse(o.dateFrom)) / 86400000;
      if (span > tetoDias + 1) return JSON.stringify({ isLastPage: true, bets: [] });
    }
    const sts = Array.isArray(o.statuses) ? o.statuses : [];
    const pag = Number(o.pageNumber) || 1;
    if (sts.includes(0)) return pag === 1 ? abertas : JSON.stringify({ isLastPage: true, bets: [] });
    if (pag === 1) return resolvidas;
    return JSON.stringify({ isLastPage: true, bets: [] });
  };
  return { resp, pedidos };
}

async function umClique(corpoInicial, href = HREF, opcoes = {}) {
  const srv = servidor(opcoes);
  const { ultima } = await rodarInject({
    inject: "vb_inject.js",          // ← o MESMO das outras Altenar
    href,
    urlInicial: URL_API,
    corpoInicial,
    optsInicial: { method: "POST", headers: HEADERS_PAGINA, body: corpoInicial },
    pedido: "__sharpenupVBReq",
    ms: 1200,
    responder: srv.resp,
  });
  return { ultima, pedidos: srv.pedidos };
}

export async function rodar() {
  const falhas = [];
  let testes = 0;
  let colhido = null;

  // ── 1. Um clique = as duas listas, partindo de qualquer aba, com o integration DESTA casa ──
  for (const [rotulo, corpo] of [["aba Processado", CORPO_RESOLVIDAS], ["aba Aberto", CORPO_ABERTAS]]) {
    const { ultima, pedidos } = await umClique(corpo);
    testes++;
    if (!ultima) { falhas.push(`${rotulo}: o inject não emitiu nenhuma mensagem`); continue; }
    if (!ultima.hook) falhas.push(`${rotulo}: o inject não sinalizou 'hook' rodando em betmartini.com`);
    if (!ultima.fim) falhas.push(`${rotulo}: não sinalizou 'fim' — o robô ficaria esperando o teto`);
    const bets = ultima.bets || [];
    if (bets.length !== 12) falhas.push(`${rotulo}: esperava 12 bilhetes (8 resolvidas + 4 abertas), vieram ${bets.length}`);

    const pediu = (n) => pedidos.some((b) => { try { return JSON.parse(b).statuses.includes(n); } catch (e) { return false; } });
    if (!pediu(0)) falhas.push(`${rotulo}: nunca pediu a aba ABERTA — aposta em aberto sumiria`);
    if (!pediu(1)) falhas.push(`${rotulo}: nunca pediu a aba PROCESSADO`);

    // Um replay que montasse corpo do zero traria os bilhetes de OUTRA marca, ou nenhum.
    const doReplay = pedidos.slice(1);
    if (!doReplay.length) falhas.push(`${rotulo}: o replay não fez nenhuma requisição`);
    if (doReplay.some((b) => !/"integration"\s*:\s*"betmartini"/.test(b)))
      falhas.push(`${rotulo}: o replay perdeu o "integration":"betmartini" do corpo aprendido`);

    if (!colhido && bets.length) colhido = bets;
  }
  if (!colhido) return { falhas: falhas.concat(["nenhum bilhete colhido — o resto do caso não roda"]), testes };

  // ── 2. Todo bloco abre com o código, no formato de 10 dígitos do motor ──
  const fmt = carregarContent().pegar("formatTicketVB");
  for (const b of colhido) {
    testes++;
    const id = String(b.id);
    if (!fmt(b).startsWith(`[Código: ${id}]`)) falhas.push(`${id}: marcador [Código:] ausente/errado`);
    if (!/^\d{10}$/.test(id)) falhas.push(`${id}: id fora do formato numérico de 10 dígitos do motor`);
  }

  // ── 3. O bloco é IDÊNTICO ao do host da VaideBet — é isso que "espelho" quer dizer ──
  {
    testes++;
    const { ultima: pelaVB } = await umClique(CORPO_RESOLVIDAS,
      "https://www.vaidebet.bet.br/sports?shareCode=IHLBJGT77FZ#/betHistory");
    const vb = new Map(((pelaVB && pelaVB.bets) || []).map((b) => [String(b.id), b]));
    if (vb.size !== colhido.length) {
      falhas.push(`espelho: host vaidebet capturou ${vb.size} e host betmartini ${colhido.length}`);
    } else {
      const dif = colhido.filter((b) => { const o = vb.get(String(b.id)); return !o || fmt(o) !== fmt(b); });
      if (dif.length) falhas.push(`espelho: ${dif.length} bloco(s) diferem entre os dois hosts`);
    }
  }

  // ── 4. Janela larga que volta VAZIA não pode virar "conta sem aberta" ──
  // Dois lados: (a) com o gateway cortando acima de 365 dias, as 4 abertas TÊM de chegar, e a
  // janela que as trouxe tem de ser ≤ 365; (b) num gateway que responde à janela larga (as 5
  // irmãs, hoje), nenhuma requisição de recuo pode sair — o conserto é aditivo.
  {
    testes++;
    const { ultima } = await umClique(CORPO_RESOLVIDAS, HREF, { tetoDias: TETO_MEDIDO });
    const bets = (ultima && ultima.bets) || [];
    const abertas = bets.filter((b) => b.status === 0).length;
    if (abertas !== 4)
      falhas.push(`janela: com o gateway devolvendo vazio acima de ${TETO_MEDIDO} dias, vieram ${abertas} de 4 abertas — ` +
                  `a lista vazia da janela larga foi lida como "conta sem aberta"`);
    if (bets.length !== 12) falhas.push(`janela: esperava 12 bilhetes no total, vieram ${bets.length}`);
    if (!ultima || !ultima.fim) falhas.push('janela: não sinalizou "fim" no caminho do recuo');

    testes++;
    const { pedidos: p2 } = await umClique(CORPO_RESOLVIDAS);   // gateway sem teto
    const curtas = p2.slice(1).filter((b) => {
      try { const o = JSON.parse(b); return o.statuses.includes(0) && (Date.parse(o.dateTo) - Date.parse(o.dateFrom)) / 86400000 <= TETO_MEDIDO + 1; }
      catch (e) { return false; }
    });
    if (curtas.length)
      falhas.push(`janela: ${curtas.length} pedido(s) de abertas com janela recuada num gateway que respondeu à larga — o recuo tem de ser só para lista vazia`);
  }

  return { falhas, testes };
}
