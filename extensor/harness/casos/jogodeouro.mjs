// Jogo de Ouro (Altenar / BIA) — ESPELHO da VaideBet/Esportiva (s256).
//
// Terceira casa do motor Altenar. Reusa `vb_inject.js`, `formatTicketVB` e `roboVBPassive`,
// sem uma linha de código novo de captura. Este caso existe porque o compartilhamento é a
// parte perigosa — ele prova que o MESMO código lê a OUTRA casa contra o card DELA.
//
// O que sustenta o espelho, MEDIDO no recon ao vivo (09/08/2026):
//   • motor confirmado SEM login e sem tocar no gate de idade: a home carrega
//     `sb2wsdk-cdn-altenar2.biahosted.net` e `sb2commongateway-altenar2.biahosted.com`;
//   • histórico no MESMO host de gateway e MESMO endpoint das outras duas
//     (`POST …/api/WidgetReports/widgetExpandedBetHistory`), com `integration: "jogodeouro"`;
//   • mesmos arrays `statuses`, mesmo `pageNumber`/`pageSize:10`, mesmo `isLastPage`;
//   • paginação provada AO VIVO: `pageNumber:2` devolveu 10 ids novos, nenhum repetido;
//   • mesmo enum contra a faixa do card: 1=`GANHOU / VENCIDO` · 2=`PERDIDO`.
//
// ⚠️ A DIFERENÇA OPERACIONAL QUE ESTA CASA TROUXE — e que nenhuma das outras duas tinha.
// A Jogo de Ouro serve DOIS widgets de histórico:
//   • o painel lateral "MINHAS APOSTAS" chama `widgetBetHistory` (COMPACTO);
//   • a tela cheia (`?page=betHistory`, atrás de "Mostrar mais apostas") chama
//     `widgetExpandedBetHistory` — o mesmo das outras casas.
// O `RX` do inject é `/widgetExpandedBetHistory/i` e **não casa** com o compacto. Isso é
// deliberado e este caso trava os dois lados: o compacto tem de ser IGNORADO (não sabemos
// que campos ele traz — a única amostra veio com `bets: []`, então usá-lo para replay seria
// chute), e o expandido tem de ser aprendido. A consequência para o operador está no
// `CASA_JOGODEOURO §2.1`: **capturar com a tela cheia aberta.**
//
// ⚠️ SEM AMOSTRA DE ABERTA. A conta tinha 0 apostas em aberto no dia do recon, então a
// armadilha do `totalWin` potencial NÃO pôde ser verificada nesta casa. Ela está travada
// nos casos da VaideBet e da Esportiva, sobre o MESMO formatador — o que este caso pode
// fazer (e faz, no controle negativo) é provar que o ramo continua de pé.
import { rodarInject, carregarContent, fixture, linha } from "../sandbox.mjs";

export const casa = "Jogo de Ouro";

// Cada valor lido do CARD da Jogo de Ouro (aba Processado de 09/08/2026, "Expandir tudo"
// ligado). `evento` é o que vai para a coluna Data do TSV; `data` é a colocação do rodapé;
// `odd` é a "Cotações totais"; `pre` é o riscado do boost, que a tela TRUNCA.
const ESPERADO = {
  "5277792927": { evento: "09/08/2026 18:30:00", data: "09/08/2026 10:58:35", odd: "3,05", stake: "30,00", status: /^Perdeu → L$/, tipo: /^Bet Builder \(mesmo jogo · 2 seleções\)$/, pre: "2,7143", tela: "2.71" },
  "5277766810": { evento: "09/08/2026 16:00:00", data: "09/08/2026 10:51:36", odd: "2,9",  stake: "30,00", status: /^Perdeu → L$/, tipo: /^Bet Builder \(mesmo jogo · 3 seleções\)$/, pre: "2,625",  tela: "2.62" },
  "5274355446": { evento: "08/08/2026 20:30:00", data: "08/08/2026 13:15:19", odd: "3",    stake: "30,00", status: /^Perdeu → L$/, tipo: /^Bet Builder \(mesmo jogo · 2 seleções\)$/, pre: "2,6667", tela: "2.66" },
  "5273475058": { evento: "08/08/2026 19:15:00", data: "08/08/2026 08:36:48", odd: "3,3",  stake: "30,00", status: /^Ganho → W/,   tipo: /^Bet Builder \(mesmo jogo · 2 seleções\)$/, pre: "2,9", retorno: "99,00" },
  "5270277400": { evento: "07/08/2026 19:30:00", data: "07/08/2026 10:06:35", odd: "2,8",  stake: "30,00", status: /^Perdeu → L$/, tipo: /^Bet Builder \(mesmo jogo · 3 seleções\)$/, pre: "2,5" },
  "5270276694": { evento: "07/08/2026 19:30:00", data: "07/08/2026 10:06:12", odd: "2,65", stake: "30,00", status: /^Ganho → W/,   tipo: /^Bet Builder \(mesmo jogo · 2 seleções\)$/, pre: "2,3334", tela: "2.33", retorno: "79,50" },
  // ⭐ APOSTA ESPECIAL — o que só esta casa trouxe. Ver o bloco dedicado no fim do caso.
  "5268433627": { evento: "06/08/2026 20:00:00", data: "06/08/2026 17:33:37", odd: "4",    stake: "30,00", status: /^Ganho → W/,   tipo: /^Simples$/, pre: "3", retorno: "120,00" },
  "5268033210": { evento: "06/08/2026 20:00:00", data: "06/08/2026 15:26:54", odd: "2,25", stake: "30,00", status: /^Ganho → W/,   tipo: /^Bet Builder \(mesmo jogo · 2 seleções\)$/, pre: "2", retorno: "67,50" },
  "5267175515": { evento: "06/08/2026 20:00:00", data: "06/08/2026 10:45:35", odd: "2,8",  stake: "30,00", status: /^Perdeu → L$/, tipo: /^Bet Builder \(mesmo jogo · 2 seleções\)$/, pre: "2,5" },
  "5263880148": { evento: "05/08/2026 19:00:00", data: "05/08/2026 09:37:40", odd: "3",    stake: "30,00", status: /^Ganho → W/,   tipo: /^Bet Builder \(mesmo jogo · 2 seleções\)$/, pre: "2,6667", tela: "2.66", retorno: "90,00" },
};

// Corpos reais do F12 desta conta — repare no `"integration":"jogodeouro"`.
const CORPO_RESOLVIDAS = '{"culture":"pt-BR","timezoneOffset":180,"integration":"jogodeouro","deviceType":1,"countryCode":"BR","dateFrom":"2026-07-30T03:00:00.000Z","dateTo":"2026-08-10T02:59:59.999Z","liveOnly":false,"numFormat":"en-GB","pageNumber":1,"pageSize":10,"statuses":[1,8,2,4,18]}';
const CORPO_ABERTAS   = '{"culture":"pt-BR","timezoneOffset":180,"integration":"jogodeouro","deviceType":1,"countryCode":"BR","dateFrom":"2026-07-30T03:00:00.000Z","dateTo":"2026-08-10T02:59:59.999Z","liveOnly":false,"numFormat":"en-GB","pageNumber":1,"pageSize":10,"statuses":[0,10,3,20,17]}';

const URL_API = "https://sb2bethistory-gateway-altenar2.biahosted.com/api/WidgetReports/widgetExpandedBetHistory";
// O widget COMPACTO do painel lateral. Mesmo host, mesmo corpo, PATH diferente.
const URL_COMPACTO = "https://sb2bethistory-gateway-altenar2.biahosted.com/api/WidgetReports/widgetBetHistory";
const HREF = "https://jogodeouro.bet.br/pt/sports?page=betHistory";

function servidor() {
  const resolvidas = fixture("jogodeouro.settled.json");   // 10 bilhetes · isLastPage:false
  const pedidos = [];
  let compactoServido = 0;
  const resp = (url, opts) => {
    const body = String((opts && opts.body) || "");
    // O compacto responde com ALGO que o inject nunca deve consumir: se ele passar a casar
    // este path, o bilhete fantasma abaixo apareceria no lote e o teste acusa.
    if (url.includes("widgetBetHistory") && !url.includes("Expanded")) {
      compactoServido++;
      return JSON.stringify({ isLastPage: true, bets: [{ id: 999999, status: 1, totalStake: 1, totalWin: 2, totalOdds: 2, selections: [] }] });
    }
    if (!url.includes("widgetExpandedBetHistory")) return null;
    pedidos.push(body);
    let o = null;
    try { o = JSON.parse(body); } catch (e) { return null; }
    const sts = Array.isArray(o.statuses) ? o.statuses : [];
    const pag = Number(o.pageNumber) || 1;
    // A conta NÃO tinha aposta em aberto no dia do recon: a aba Aberto respondeu
    // `{"isLastPage":true,"bets":[]}` de verdade. É isso que se reproduz aqui.
    if (sts.includes(0)) return JSON.stringify({ isLastPage: true, bets: [] });
    if (pag === 1) return resolvidas;
    return JSON.stringify({ isLastPage: true, bets: [] });
  };
  return { resp, pedidos, compacto: () => compactoServido };
}

async function umClique(corpoInicial, href) {
  const srv = servidor();
  const { ultima, urls } = await rodarInject({
    inject: "vb_inject.js",          // ← o MESMO da VaideBet/Esportiva
    href: href || HREF,
    // A página dispara PRIMEIRO o widget compacto do painel lateral e só depois o expandido
    // da tela cheia — é a sequência real desta casa, e o inject tem de ignorar o primeiro.
    urlInicial: URL_COMPACTO,
    optsInicial: { method: "POST", body: corpoInicial },
    urlsExtra: [{ url: URL_API, opts: { method: "POST", body: corpoInicial } }],
    pedido: "__sharpenupVBReq",
    ms: 1200,
    responder: srv.resp,
  });
  return { ultima, pedidos: srv.pedidos, urls, compacto: srv.compacto() };
}

export async function rodar() {
  const falhas = [];
  let testes = 0;

  // ── 1. Um clique = a lista inteira, partindo de qualquer aba ──────────────────
  let colhido = null;
  for (const [rotulo, corpo] of [["aba Processado", CORPO_RESOLVIDAS], ["aba Aberto", CORPO_ABERTAS]]) {
    const { ultima, pedidos, compacto } = await umClique(corpo);
    testes++;
    if (!ultima) { falhas.push(`${rotulo}: o inject não emitiu nenhuma mensagem`); continue; }
    if (!ultima.hook) falhas.push(`${rotulo}: o inject não sinalizou 'hook' rodando em jogodeouro.bet.br`);
    if (typeof ultima.respostas !== "number" || ultima.respostas < 1)
      falhas.push(`${rotulo}: 'respostas' não foi reportado`);

    const bets = ultima.bets || [];
    if (bets.length !== 10) falhas.push(`${rotulo}: esperava 10 bilhetes (a conta não tinha nenhuma aberta), vieram ${bets.length}`);
    if (!ultima.fim) falhas.push(`${rotulo}: não sinalizou 'fim' — o robô ficaria esperando o teto`);

    // ⭐ O widget COMPACTO foi servido e NÃO pode ter entrado no lote.
    if (!compacto) falhas.push(`${rotulo}: o widget compacto nunca foi servido — a guarda de path não foi exercitada`);
    if (bets.some((b) => String(b.id) === "999999")) {
      falhas.push(`${rotulo}: o bilhete do widget COMPACTO (widgetBetHistory) entrou no lote — ` +
                  "o inject passou a casar um endpoint cujos campos ninguém mediu");
    }

    const p2 = pedidos.find((b) => { try { const o = JSON.parse(b); return o.pageNumber === 2 && !o.statuses.includes(0); } catch (e) { return false; } });
    if (!p2) falhas.push(`${rotulo}: nenhuma requisição pediu a página 2 das resolvidas — paginação ativa não avançou`);
    else if (!/"pageSize"\s*:\s*10/.test(p2)) falhas.push(`${rotulo}: pageSize corrompido ao avançar → ${p2}`);

    const temAbertas = pedidos.some((b) => { try { return JSON.parse(b).statuses.includes(0); } catch (e) { return false; } });
    const temResolvidas = pedidos.some((b) => { try { return JSON.parse(b).statuses.includes(1); } catch (e) { return false; } });
    if (!temAbertas) falhas.push(`${rotulo}: nunca pediu a aba ABERTA (statuses com 0)`);
    if (!temResolvidas) falhas.push(`${rotulo}: nunca pediu a aba PROCESSADO (statuses com 1)`);

    if (!colhido && bets.length) colhido = bets;
  }

  if (!colhido) return { falhas: falhas.concat(["nenhum bilhete colhido — o resto do caso não roda"]), testes };

  // ── 2. Leitura bilhete a bilhete, contra o card DA JOGO DE OURO ───────────────
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

    // Boost: 10 de 10 bilhetes desta conta são "ODDS DE OURO" (`boostProperty: 3` — o mesmo
    // enum que a VaideBet chama de GOLDEN BOOST e a Esportiva de TURBINADA). A tela trunca
    // o riscado; o bloco tem de emitir o valor cheio.
    const marca = txt.split("\n").find((l) => l.startsWith("Marcação da casa: odd turbinada")) || "";
    if (!marca) falhas.push(`${id}: bilhete com ODDS DE OURO sem a marcação de boost`);
    else {
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
      const n = Number(e.odd.replace(",", ".")), st = Number(e.stake.replace(",", "."));
      const ret = Number(e.retorno.replace(",", "."));
      if (!(Math.abs(n * st - ret) <= 0.01)) falhas.push(`${id}: odd ${e.odd} × stake ${e.stake} não explica o retorno ${e.retorno}`);
    }
  }

  // ── 3. A APOSTA ESPECIAL (o que só esta casa trouxe) ─────────────────────────
  // `QUEM CONSEGUE A REMONTADA?` não é jogo: é um mercado especial da casa. O payload vem
  // com `eventName` = o NOME DO MERCADO (não um confronto), sem `eventScore`,
  // `marketTypeId: 5001`, `selectionTypeId: -1`, `bbOdds: []` e `isBetBuilder: false`.
  // O risco é o bloco sair mudo ou o tipo virar bet builder — a IA precisa do texto da
  // seleção, que aqui é uma FRASE ("Corinthians OU Vitória avançarem às quartas...").
  {
    const b = colhido.find((x) => String(x.id) === "5268433627");
    testes++;
    if (!b) {
      falhas.push("5268433627 (aposta especial) não veio na captura");
    } else {
      const txt = fmt(b);
      if (!txt.includes("Corinthians OU Vitória avançarem")) {
        falhas.push("5268433627: a frase da seleção especial não apareceu no bloco — a IA ficaria sem descrição");
      }
      if (!txt.includes("QUEM CONSEGUE A REMONTADA?")) {
        falhas.push("5268433627: o nome do mercado especial não apareceu no bloco");
      }
      if (/Bet Builder|Mesmo jogo/.test(txt)) {
        falhas.push("5268433627: aposta especial classificada como bet builder");
      }
      // Placar não existe neste bilhete: a linha não pode sair vazia nem inventada.
      if (/^\s+Placar:\s*$/m.test(txt)) falhas.push("5268433627: emitiu 'Placar:' vazio");
    }
  }

  // ── 4. CONTROLE NEGATIVO ─────────────────────────────────────────────────────
  // Caso espelho passa verde de primeira, e isso não é evidência.
  {
    const base = JSON.parse(fixture("jogodeouro.settled.json")).bets.find((x) => String(x.id) === "5273475058");
    testes++;
    // (a) O ramo da ABERTA continua de pé — esta conta não tinha nenhuma, então a única
    //     forma de exercitar aqui é sintética, e está declarada como tal.
    const comoAberta = fmt({ ...base, status: 0, remainingTotalWin: 99.0 });
    if (!/em aberto/.test(linha(comoAberta, "Status:"))) falhas.push("controle negativo: status=0 não virou 'em aberto'");
    if (linha(comoAberta, "Retorno:")) falhas.push("controle negativo: aberta emitiu 'Retorno:' — o ramo do potencial quebrou");
    if (linha(comoAberta, "Retorno potencial:") !== "R$ 99,00") falhas.push("controle negativo: aberta sem 'Retorno potencial:' correto");
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
    const jd = new Map(colhido.map((b) => [String(b.id), b]));
    testes++;
    if (vb.size !== jd.size) {
      falhas.push(`espelho: host vaidebet capturou ${vb.size} e host jogodeouro ${jd.size} — a captura não pode depender do domínio`);
    } else {
      const diferentes = [];
      for (const [id, b] of jd) {
        const o = vb.get(id);
        if (!o || fmt(o) !== fmt(b)) diferentes.push(id);
      }
      if (diferentes.length) falhas.push(`espelho: ${diferentes.length} bloco(s) diferem entre os hosts (${diferentes.slice(0, 3).join(", ")}…)`);
    }
  }

  return { falhas, testes };
}
