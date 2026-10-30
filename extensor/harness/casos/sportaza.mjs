// Sportaza (Altenar / BIA) — 11ª casa do motor, ESPELHO da Vavada e das outras Altenar (s434).
//
// Sem inject, formatador ou robô próprios: reusa `vb_inject.js`, `formatTicketVB` e
// `roboVBPassive`. É a 1ª Altenar internacional que entra COM conta e fixture própria.
//
// O que sustenta o espelho, medido no recon (30/10/2026, Chrome do Feca, conta LOGADA, USD):
//   • `sportaza-5178.com` (espelho numerado; o rodapé diz `sportaza.com`) carrega
//     `sb2wsdk-altenar2.biahosted.com` NA PRÓPRIA página (`window.altenarWSDK` no topo) e chama
//     `sb2frontend-altenar2` com `integration=sportaza`, `culture=pt-PT`;
//   • a tela "Minhas apostas" (`/pt/sports?page=betHistory`, abas Aberto · Processado · Ganhou ·
//     Perdido · Cashout) dispara SÓ o COMPACTO (`widgetBetHistory`), como a Betpix365. O
//     expandido existe e responde 200 com o mesmo Bearer, e é dele que saem as pernas;
//   • as ABERTAS com janela de 730 dias voltam `200 · {"isLastPage":true,"bets":[]}` e com 365
//     trazem as 9 — o mesmo gateway da Betrebels. O recuo do `vb_inject` cobre (seção 4);
//   • a tela pede as processadas com `statuses:[1,8,21,2,4,18]`; o inject usa
//     `[1,8,2,4,18,7]`. Medido: zero aposta no 21 e no 7 nesta conta (365 dias), as duas listas
//     trazem as mesmas 18. O significado do 21 NÃO foi medido.
//
// PROCEDÊNCIA: `sportaza.open.json` e `sportaza.settled.json` são o expandido REAL desta conta,
// recortado em 6 bilhetes (2 abertas; simples ganha, simples perdida, múltipla ganha com bônus
// de acumulada, múltipla perdida), verbatim (SHA-256 conferido contra a página). Os valores
// esperados abaixo vêm dos CARDS da tela, não do formatador: o card mostra a odd com 2 casas
// e a hora da colocação em SP sem segundos, então a asserção compara o que o card mostra.
//
// O QUE ESTE CASO **NÃO** COBRE: cashout, anulada, bet builder e sistema (sem amostra na
// conta); a MOEDA — o `formatTicketVB` rotula todo dinheiro como R$ e não escreve `Moeda:`,
// quem converte é o servidor pela moeda do CADASTRO (a conta é USD); e o status 21.
import { rodarInject, carregarContent, fixture } from "../sandbox.mjs";

export const casa = "Sportaza";

// Corpo REAL que a tela mandou (só as datas e `statuses` variam entre abas).
const CORPO = (statuses) => JSON.stringify({
  culture: "pt-PT", timezoneOffset: 180, integration: "sportaza", deviceType: 1, numFormat: "en-GB",
  countryCode: "BR", dateFrom: "2026-10-20T03:00:00.000Z", dateTo: "2026-10-31T02:59:59.999Z",
  liveOnly: false, pageNumber: 1, pageSize: 10, statuses,
});
const CORPO_PROCESSADO = CORPO([1, 8, 21, 2, 4, 18]);
const CORPO_ABERTO = CORPO([0, 10, 3, 20, 17]);

const URL_COMPACTO = "https://sb2bethistory-gateway-altenar2.biahosted.com/api/WidgetReports/widgetBetHistory";
const HREF = "https://sportaza-5178.com/pt/sports?page=betHistory";
const HEADERS_PAGINA = { Authorization: "Bearer harness-token-sportaza", "Content-Type": "application/json" };

// O que o COMPACTO real devolveu para a 1ª aberta (sem `selections`). Serve de molde para o
// inject aprender url+headers; nunca pode virar bilhete.
const COMPACTO = '{"isLastPage":true,"bets":[{"id":5590916289,"type":1,"status":0,"isCancelAllowed":false,"totalStake":30,"totalWin":338.12,"createdDate":"2026-10-30T10:01:23.33Z","currency":"USD","remainingTotalWin":338.12,"openStake":30,"bonusPart":0,"initBonusPart":0,"taxType":0,"taxValue":0,"selectionsCount":null,"eventName":null,"isArchive":false,"totalOdds":10.97184}]}';

// Gabarito lido NOS CARDS (30/10/2026): odd com 2 casas como o card mostra, stake, "Ganho
// total" e a colocação em SP ("30/10 • 00:07").
const CARDS = {
  "5590916289": { aba: "Aberto",  odd: "10.97", stake: "30,00", ganho: "338,12", tipo: /^Múltipla/ },
  "5588982337": { aba: "Aberto",  odd: "6.82",  stake: "30,00", ganho: "210,03", tipo: /^Múltipla/, col: "29/10/2026 15:40" },
  "5590494619": { aba: "Ganhou",  odd: "1.83",  stake: "75,00", ganho: "137,50", res: /→ W$/,     col: "30/10/2026 00:07" },
  "5589842458": { aba: "Ganhou",  odd: "8.69",  stake: "30,00", ganho: "267,84", res: /→ W$/,     col: "29/10/2026 19:43", tipo: /^Múltipla/ },
  "5590902372": { aba: "Perdido", odd: "21.48", stake: "30,00", ganho: null,     res: /→ L$/,     col: "30/10/2026 06:50", tipo: /^Múltipla/ },
  "5590485064": { aba: "Perdido", odd: "1.83",  stake: "90,00", ganho: null,     res: /→ L$/,     col: "30/10/2026 00:01" },
};

const TETO_MEDIDO = 365;       // abertas com janela maior voltam vazias (medido, 30/10/2026)

function servidor({ tetoDias = null } = {}) {
  const resolvidas = fixture("sportaza.settled.json");   // 4 bilhetes · isLastPage:true
  const abertas = fixture("sportaza.open.json");         // 2 bilhetes · isLastPage:true
  const pedidos = [];
  let compactoServido = 0, semAuth = 0;
  const resp = (url, opts) => {
    const body = String((opts && opts.body) || "");
    const hdr = (opts && opts.headers) || {};
    if (url.includes("widgetBetHistory") && !url.includes("Expanded")) { compactoServido++; return COMPACTO; }
    if (!url.includes("widgetExpandedBetHistory")) return null;
    if (!hdr.Authorization) { semAuth++; return null; }
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
  return { resp, pedidos, compacto: () => compactoServido, semAuth: () => semAuth };
}

// A sequência REAL da casa: a página dispara só o compacto.
async function umClique(corpoInicial, opcoes = {}) {
  const srv = servidor(opcoes);
  const { ultima } = await rodarInject({
    inject: "vb_inject.js",          // ← o MESMO das outras Altenar
    href: HREF,
    urlInicial: URL_COMPACTO,
    optsInicial: { method: "POST", headers: HEADERS_PAGINA, body: corpoInicial },
    pedido: "__sharpenupVBReq",
    ms: 1200,
    responder: srv.resp,
  });
  return { ultima, pedidos: srv.pedidos, compacto: srv.compacto(), semAuth: srv.semAuth() };
}

const linha = (bloco, rotulo) => (bloco.split("\n").find((l) => l.startsWith(rotulo)) || "").slice(rotulo.length);

export async function rodar() {
  const falhas = [];
  let testes = 0;
  let colhido = null;

  // ── 1. Um clique, partindo do COMPACTO de qualquer aba = as duas listas expandidas ──
  for (const [rotulo, corpo] of [["aba Processado", CORPO_PROCESSADO], ["aba Aberto", CORPO_ABERTO]]) {
    const { ultima, pedidos, compacto, semAuth } = await umClique(corpo);
    testes++;
    if (!ultima) { falhas.push(`${rotulo}: o inject não emitiu nenhuma mensagem`); continue; }
    if (!ultima.hook) falhas.push(`${rotulo}: o inject não sinalizou 'hook' rodando em sportaza-5178.com`);
    if (!ultima.fim) falhas.push(`${rotulo}: não sinalizou 'fim' — o robô ficaria esperando o teto`);
    if (!compacto) falhas.push(`${rotulo}: o compacto nunca foi servido — a sequência real não foi exercitada`);
    if (semAuth) falhas.push(`${rotulo}: ${semAuth} replay(s) sem o Bearer aprendido do compacto`);
    const bets = ultima.bets || [];
    if (bets.length !== 6) falhas.push(`${rotulo}: esperava 6 bilhetes (4 processadas + 2 abertas), vieram ${bets.length}`);
    if (bets.some((b) => !Array.isArray(b.selections) || !b.selections.length))
      falhas.push(`${rotulo}: bilhete sem pernas no lote — o corpo do COMPACTO virou bilhete`);
    const pediu = (n) => pedidos.some((b) => { try { return JSON.parse(b).statuses.includes(n); } catch (e) { return false; } });
    if (!pediu(0)) falhas.push(`${rotulo}: nunca pediu a aba ABERTA — aposta em aberto sumiria`);
    if (!pediu(1)) falhas.push(`${rotulo}: nunca pediu as PROCESSADAS`);
    if (!pedidos.length || pedidos.some((b) => !/"integration"\s*:\s*"sportaza"/.test(b)))
      falhas.push(`${rotulo}: o replay perdeu o "integration":"sportaza" do corpo aprendido`);
    if (pedidos.some((b) => !/"culture"\s*:\s*"pt-PT"/.test(b)))
      falhas.push(`${rotulo}: o replay perdeu o "culture":"pt-PT" — os mercados viriam noutro idioma`);
    if (!colhido && bets.length) colhido = bets;
  }
  if (!colhido) return { falhas: falhas.concat(["nenhum bilhete colhido — o resto do caso não roda"]), testes };

  // ── 2. Cada bloco contra o CARD da casa ──
  const fmt = carregarContent().pegar("formatTicketVB");
  const porId = new Map(colhido.map((b) => [String(b.id), b]));
  for (const [id, c] of Object.entries(CARDS)) {
    testes++;
    const b = porId.get(id);
    if (!b) { falhas.push(`${id}: bilhete da aba ${c.aba} ausente do lote`); continue; }
    const t = fmt(b);
    if (!t.startsWith(`[Código: ${id}]`)) falhas.push(`${id}: marcador [Código:] ausente/errado`);
    if (!/^\d{10}$/.test(id)) falhas.push(`${id}: id fora do formato de 10 dígitos do motor`);
    // A odd do bloco é a EXATA; o card a mostra com 2 casas, truncada. Na GANHA a régua global
    // é retorno ÷ stake (MASTER_RESULTADO), e é contra os dois números do card que se confere.
    const odd = parseFloat(linha(t, "Odd: ").replace(",", "."));
    const num = (s) => parseFloat(s.replace(/\./g, "").replace(",", "."));
    if (c.aba === "Ganhou") {
      if (!(Math.abs(odd - num(c.ganho) / num(c.stake)) < 0.001))
        falhas.push(`${id}: odd ${linha(t, "Odd: ")} ≠ ganho ÷ stake do card (${c.ganho} ÷ ${c.stake})`);
    } else if ((Math.floor(odd * 100) / 100).toFixed(2) !== c.odd) {
      falhas.push(`${id}: odd ${linha(t, "Odd: ")} não bate com a do card (${c.odd})`);
    }
    if (linha(t, "Stake: ") !== `R$ ${c.stake}`) falhas.push(`${id}: stake "${linha(t, "Stake: ")}" ≠ card $${c.stake}`);
    if (c.aba === "Aberto") {
      if (!/em aberto/i.test(linha(t, "Status: "))) falhas.push(`${id}: aberta sem o texto de "em aberto" → ${linha(t, "Status: ")}`);
      if (linha(t, "Retorno potencial: ") !== `R$ ${c.ganho}`) falhas.push(`${id}: retorno potencial ≠ card $${c.ganho}`);
      if (/^Retorno: /m.test(t)) falhas.push(`${id}: aberta com "Retorno:" — potencial lido como liquidado`);
    } else {
      if (!c.res.test(linha(t, "Status: "))) falhas.push(`${id}: status "${linha(t, "Status: ")}" ≠ card ${c.aba} (${c.res})`);
      const ret = linha(t, "Retorno: ");
      if (c.ganho ? ret !== `R$ ${c.ganho}` : ret !== "") falhas.push(`${id}: retorno "${ret}" ≠ card ${c.ganho || "vazio"}`);
    }
    if (c.col && !linha(t, "Data (colocação): ").startsWith(c.col))
      falhas.push(`${id}: colocação "${linha(t, "Data (colocação): ")}" ≠ card ${c.col}`);
    if (c.tipo && !c.tipo.test(linha(t, "Tipo: "))) falhas.push(`${id}: tipo "${linha(t, "Tipo: ")}" ≠ card Múltipla`);
  }

  // ── 3. O bônus de acumulada é pago por FORA da odd: o bloco precisa dizer ──
  // 30 × 8,697344 = 260,92, e o card paga 267,84 (bônus 6,92). Sem a marcação, retorno ÷ stake
  // parece odd adulterada.
  {
    testes++;
    const t = fmt(porId.get("5589842458"));
    if (!/aposta com bônus \(R\$ 6,92\)/.test(t)) falhas.push("5589842458: bônus de acumulada (6,92) sumiu do bloco");
  }

  // ── 4. Janela larga que volta VAZIA não pode virar "conta sem aberta" (medido nesta conta) ──
  {
    testes++;
    const { ultima } = await umClique(CORPO_PROCESSADO, { tetoDias: TETO_MEDIDO });
    const bets = (ultima && ultima.bets) || [];
    const abertas = bets.filter((b) => b.status === 0).length;
    if (abertas !== 2)
      falhas.push(`janela: com as abertas vazias acima de ${TETO_MEDIDO} dias, vieram ${abertas} de 2 — ` +
                  `a lista vazia da janela larga foi lida como "conta sem aberta"`);
    if (bets.length !== 6) falhas.push(`janela: esperava 6 bilhetes no total, vieram ${bets.length}`);
    if (!ultima || !ultima.fim) falhas.push('janela: não sinalizou "fim" no caminho do recuo');
  }

  return { falhas, testes };
}
