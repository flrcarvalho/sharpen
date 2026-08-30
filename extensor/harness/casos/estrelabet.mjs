// Estrela Bet (Altenar / BIA) — 5ª casa do motor, ESPELHO da VaideBet (s303).
//
// Sem inject, formatador ou robô próprios: reusa `vb_inject.js`, `formatTicketVB` e
// `roboVBPassive`. Este caso existe porque o compartilhamento é a parte perigosa — ele prova
// que o MESMO código lê a OUTRA casa contra o card DELA, e não que "deve funcionar porque é
// igual". É o mesmo desenho de `esportiva.mjs`, `jogodeouro.mjs` e `betpix365.mjs`.
//
// O que sustenta o espelho, MEDIDO no recon ao vivo (30/08/2026), não deduzido:
//   • a home de ESPORTES carrega `sb2frontend-altenar2.biahosted.com` e
//     `sb2wsdk-cdn-altenar2.biahosted.net` com `integration=estrelabet` na query — motor
//     confirmado SEM login e sem clicar em nada, como no BetBy;
//   • o histórico sai do MESMO endpoint, no MESMO host de gateway:
//     `POST https://sb2bethistory-gateway-altenar2.biahosted.com/api/WidgetReports/widgetExpandedBetHistory`
//     — e o `RX` do inject casa por PATH, sem citar host nenhum;
//   • mesmos arrays `statuses` no corpo (Aberto `[0,10,3,20,17]` · Processado `[1,8,2,4,18]`),
//     mesmo `pageNumber`/`pageSize:10`, mesmo fim autoritativo `isLastPage`;
//   • UNIÃO DE CHAVES do payload real (o método barato da Faz1bet, s284): as **60 chaves**
//     aninhadas dos 12 bilhetes desta conta são subconjunto exato das 77 das quatro irmãs —
//     **zero campo novo**. As 17 que faltam são de bet builder preenchido e de boost, que
//     esta amostra não tem.
//
// A SUPERFÍCIE, porém, é a mais lisa das cinco, e isso também foi medido: "Ver minhas
// apostas" abre a TELA CHEIA, que dispara o `widgetExpandedBetHistory` sozinha, na window de
// TOPO (não em iframe), e o `clone().text()` resolve. Não precisa do molde do compacto
// (Betpix365) nem de ensinar o operador a achar outra tela (Jogo de Ouro).
//
// ⚠ O QUE ELA TEM DE PRÓPRIO NÃO ESTÁ NA TELA, ESTÁ NO CORS. O gateway responde
// `Access-Control-Allow-Origin: *` para este tenant, e o navegador RECUSA a chamada com
// `credentials:"include"` antes de ela sair — `TypeError: Failed to fetch`, medido **3 de 3**,
// com a MESMA requisição voltando **200 · 8 bilhetes · isLastPage:true** sem credencial,
// também 3 de 3 (o XHR com `withCredentials` falha igual). Como o replay INTEIRO passa por
// ali, isso não degradaria a captura: zeraria. O `pedirPagina` do inject tenta `include`
// primeiro (o que as 4 irmãs usam hoje) e cai para a chamada sem credencial em quem for
// recusado — perder a credencial não custa autenticação, porque quem autentica aqui é o
// `Authorization: Bearer` dos headers aprendidos. A seção 5 abaixo trava os dois lados.
//
// ⚠ E O DICIONÁRIO DESTE TENANT TEM **TAB LITERAL** DENTRO DO NOME DO TIME. Medido:
// `"Real Sociedad vs. RCD Espanyol\t\t"` e `"RCD Espanyol\t\t"` no bilhete 5347925916 (o
// próprio menu da casa traz `"E-sports +\t\t"`). TAB é o separador de coluna do TSV: copiado
// verbatim para a Descrição, ele empurra Stake/Odd/Resultado uma casa à direita e o
// `parse_tsv` lê o código do bilhete no lugar do resultado. A seção 6 trava isso.
import { rodarInject, carregarContent, fixture, linha, FALHA_DE_REDE } from "../sandbox.mjs";

export const casa = "Estrela Bet";

// Cada valor abaixo foi lido do CARD da Estrela Bet (abas Processado/Aberto de 30/08/2026,
// com "Expandir tudo" ligado), não do código.
//
// `evento` é a data que VAI PARA A COLUNA DATA do TSV (`MASTER_OUTPUT §4`). `data` é a
// colocação, do rodapé cinza do card ("29/08 • 12:53"). `odd` é a "Cotações totais" — mas
// **sem o truncamento da tela**: o card estampa 9.66 onde o payload tem 9.660625.
//
// ⚠ Duas conversões que o card NÃO faz por você, e que já me fizeram escrever expectativa
// errada ao copiar da tela:
//   • o card imprime a data do evento em **Brasília** e o payload em **UTC** — o
//     5353319605 tem `eventDate` mais recente em `2026-08-31T00:00:00Z`, que é
//     **30/08 21:00** no TSV. Copiar o dia do JSON põe a linha no dia seguinte;
//   • o dinheiro do bloco sai por `_brl` (`toFixed(2)`, vírgula decimal, **sem separador de
//     milhar**), enquanto o card usa en-GB: `R$1,727.40` na tela é `R$ 1727,40` no bloco.
//     É comportamento antigo e compartilhado por todas as casas — e no bloco é o certo,
//     porque um `.` de milhar seria decimal ambíguo para a IA.
const ESPERADO = {
  // ── resolvidas (aba Processado) ────────────────────────────────────────────────
  // Todas são múltiplas de 3 pernas — é o padrão desta conta.
  "5348932181": { evento: "29/08/2026 20:30:00", data: "29/08/2026 12:53:40", odd: "9,660625",  stake: "150,00", status: /^Perdeu → L$/, tela: "9.66" },
  "5348918704": { evento: "29/08/2026 23:00:00", data: "29/08/2026 12:51:11", odd: "11,912784", stake: "150,00", status: /^Perdeu → L$/, tela: "11.91" },
  // O bilhete do TAB (ver o cabeçalho). Stake quebrada: o card diz "R$113.63".
  "5347925916": { evento: "29/08/2026 23:00:00", data: "29/08/2026 10:04:37", odd: "8,01822",   stake: "113,63", status: /^Perdeu → L$/, tela: "8.01" },
  "5346418629": { evento: "29/08/2026 17:30:00", data: "28/08/2026 23:49:34", odd: "13,050109", stake: "150,00", status: /^Perdeu → L$/, tela: "13.05" },
  "5346406244": { evento: "29/08/2026 18:25:00", data: "28/08/2026 23:45:10", odd: "8,778",     stake: "150,00", status: /^Perdeu → L$/, tela: "8.77" },
  "5346397094": { evento: "29/08/2026 18:30:00", data: "28/08/2026 23:42:10", odd: "7,20027",   stake: "150,00", status: /^Perdeu → L$/, tela: "7.20" },
  // ⚠ O W, e o bilhete mais importante do caso. O card mostra TRÊS linhas de dinheiro:
  //     Cotações totais  11.01 · Valor total da aposta R$150.00
  //     SuperMúltipla 🎁 R$75.11 · Ganho total R$1,727.40
  // 150 × 11,015269 = 1.652,29 **+ 75,11 = 1.727,40**, exato. Ou seja: a odd declarada NÃO
  // explica o retorno, porque o bônus é pago POR FORA da odd — a régua global do W
  // (`Retorno ÷ Stake` = 11,516) é a que vale. É a 2ª casa Altenar com esse comportamento,
  // depois da Betpix365 ("Ganhos extra"); o nome do selo é da MARCA, o campo (`bonus`) é do
  // motor, como GOLDEN BOOST × TURBINADA × ODDS DE OURO.
  "5346391363": { evento: "29/08/2026 18:30:00", data: "28/08/2026 23:40:07", odd: "11,516",    stake: "150,00", status: /^Ganho → W/, retorno: "1727,40", declarada: "11,015269", bonus: "75,11" },
  // Múltipla de 3 esportes... não: 2 (Baseball + Basquete). Prova o `sportTypeId 12`.
  "5346370202": { evento: "29/08/2026 22:00:00", data: "28/08/2026 23:33:35", odd: "6,824427",  stake: "50,00",  status: /^Perdeu → L$/, tela: "6.82", esporte: /^Baseball\b/ },

  // ── abertas (aba Aberto) ──────────────────────────────────────────────────────
  // O card das quatro estampa "Ganho total R$897.36 / R$1,115.39 / R$1,596.18 / R$1,797.15"
  // com os jogos ainda rolando (6', 34', 36'). É retorno POTENCIAL — a armadilha central
  // desta plataforma, o incidente que a VaideBet levou a produção na s210.
  "5353319605": { evento: "30/08/2026 21:00:00", data: "30/08/2026 10:00:44", odd: "5,745149",  stake: "150,00", status: /em aberto/, aberta: true, potencial: "897,36" },
  "5353292428": { evento: "30/08/2026 18:30:00", data: "30/08/2026 09:56:26", odd: "7,129518",  stake: "150,00", status: /em aberto/, aberta: true, potencial: "1115,39" },
  "5353279994": { evento: "30/08/2026 18:30:00", data: "30/08/2026 09:54:23", odd: "10,182102", stake: "150,00", status: /em aberto/, aberta: true, potencial: "1596,18" },
  "5351868810": { evento: "30/08/2026 19:30:00", data: "29/08/2026 23:20:11", odd: "11,458133", stake: "150,00", status: /em aberto/, aberta: true, potencial: "1797,15", esporte: /^Basquete\b/ },
};

// Os 3 abertos que a tela oferece cashout (botão "Cashout R$51.23 / R$150.00 / R$119.40"),
// mas cujo payload traz `cashOutValue: 0`. O valor mora em `GetOpenBetsCashoutValues`, outro
// endpoint — e essa ausência é PROTEÇÃO: oferta de venda não pode virar cashout executado.
const ABERTO_COM_OFERTA_DE_CASHOUT = ["5353292428", "5353279994", "5351868810"];

// Corpos REAIS que a página da Estrela Bet emitiu ao abrir cada aba (colados do Payload do
// F12 desta conta — repare no `"integration":"estrelabet"`, a única diferença para as irmãs).
const CORPO_RESOLVIDAS = '{"culture":"pt-BR","timezoneOffset":180,"integration":"estrelabet","deviceType":1,"numFormat":"en-GB","countryCode":"BR","dateFrom":"2026-08-20T03:00:00.000Z","dateTo":"2026-08-31T02:59:59.999Z","liveOnly":false,"pageNumber":1,"pageSize":10,"statuses":[1,8,2,4,18]}';
const CORPO_ABERTAS   = '{"culture":"pt-BR","timezoneOffset":180,"integration":"estrelabet","deviceType":1,"numFormat":"en-GB","countryCode":"BR","dateFrom":"2026-08-20T03:00:00.000Z","dateTo":"2026-08-31T02:59:59.999Z","liveOnly":false,"pageNumber":1,"pageSize":10,"statuses":[0,10,3,20,17]}';

const URL_API = "https://sb2bethistory-gateway-altenar2.biahosted.com/api/WidgetReports/widgetExpandedBetHistory";
const HREF = "https://www.estrelabet.bet.br/aposta-esportiva";
const HEADERS_PAGINA = { Authorization: "Bearer harness-token-estrelabet", "Content-Type": "application/json" };

/**
 * Servidor de mentira. Responde pelo `statuses` do corpo, como a casa faz.
 *
 * `corsRecusaCredencial` reproduz o comportamento MEDIDO na casa: toda requisição que leve
 * `credentials:"include"` é recusada pelo navegador (o gateway responde
 * `Access-Control-Allow-Origin: *`). A mesma requisição sem credencial responde 200.
 */
function servidor({ corsRecusaCredencial = false } = {}) {
  const resolvidas = fixture("estrelabet.settled.json");   // 8 bilhetes · isLastPage:true
  const abertas = fixture("estrelabet.open.json");         // 4 bilhetes · isLastPage:true
  const pedidos = [];
  const credenciais = [];
  const resp = (url, opts) => {
    if (!url.includes("widgetExpandedBetHistory")) return null;
    const cred = (opts && opts.credentials) || "";
    credenciais.push(cred);
    if (corsRecusaCredencial && cred === "include") return FALHA_DE_REDE;
    const body = String((opts && opts.body) || "");
    pedidos.push(body);
    let o = null;
    try { o = JSON.parse(body); } catch (e) { return null; }
    const sts = Array.isArray(o.statuses) ? o.statuses : [];
    const pag = Number(o.pageNumber) || 1;
    if (sts.includes(0)) return pag === 1 ? abertas : JSON.stringify({ isLastPage: true, bets: [] });
    if (pag === 1) return resolvidas;
    return JSON.stringify({ isLastPage: true, bets: [] });
  };
  return { resp, pedidos, credenciais };
}

async function umClique(corpoInicial, opcoes = {}) {
  const srv = servidor(opcoes);
  const { ultima, urls } = await rodarInject({
    inject: "vb_inject.js",          // ← o MESMO das outras quatro, sem uma linha de diferença
    href: opcoes.href || HREF,
    urlInicial: URL_API,
    corpoInicial: corpoInicial,
    optsInicial: { method: "POST", headers: HEADERS_PAGINA, body: corpoInicial },
    pedido: "__sharpenupVBReq",
    ms: 1200,
    responder: srv.resp,
  });
  return { ultima, pedidos: srv.pedidos, credenciais: srv.credenciais, urls };
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
    if (!ultima.hook) falhas.push(`${rotulo}: o inject não sinalizou 'hook' rodando em estrelabet.bet.br (autodiagnóstico cego)`);
    if (typeof ultima.respostas !== "number" || ultima.respostas < 1)
      falhas.push(`${rotulo}: 'respostas' não foi reportado — não dá para separar "não injetei" de "endpoint mudou"`);

    const bets = ultima.bets || [];
    if (bets.length !== 12) falhas.push(`${rotulo}: esperava 12 bilhetes (8 resolvidas + 4 abertas), vieram ${bets.length}`);
    if (!ultima.fim) falhas.push(`${rotulo}: não sinalizou 'fim' — o robô ficaria esperando o teto`);

    const temAbertas = pedidos.some((b) => { try { return JSON.parse(b).statuses.includes(0); } catch (e) { return false; } });
    const temResolvidas = pedidos.some((b) => { try { return JSON.parse(b).statuses.includes(1); } catch (e) { return false; } });
    if (!temAbertas) falhas.push(`${rotulo}: nunca pediu a aba ABERTA (statuses com 0) — aposta em aberto sumiria`);
    if (!temResolvidas) falhas.push(`${rotulo}: nunca pediu a aba PROCESSADO (statuses com 1)`);

    // O `integration` desta marca tem de sobreviver ao replay: ele vem do corpo APRENDIDO, e
    // é a única coisa que separa esta casa das outras quatro no mesmo gateway. Um replay que
    // montasse corpo do zero traria os bilhetes de OUTRA marca — ou nenhum.
    const p1 = pedidos[0] || "";
    if (!/"integration"\s*:\s*"estrelabet"/.test(p1))
      falhas.push(`${rotulo}: o replay perdeu o "integration":"estrelabet" do corpo aprendido → ${p1.slice(0, 160)}`);

    if (!colhido && bets.length) colhido = bets;
  }

  if (!colhido) return { falhas: falhas.concat(["nenhum bilhete colhido — o resto do caso não roda"]), testes };

  // ── 2. Leitura bilhete a bilhete, contra o card DA ESTRELA BET ────────────────
  const fmt = carregarContent().pegar("formatTicketVB");   // ← formatador compartilhado
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

    const stake = linha(txt, "Stake:");
    if (stake !== "R$ " + e.stake) falhas.push(`${id}: stake esperada R$ ${e.stake}, veio "${stake}"`);

    const status = linha(txt, "Status:");
    if (!e.status.test(status)) falhas.push(`${id}: status "${status}"`);

    if (!/status=\d+/.test(linha(txt, "Status (API):")))
      falhas.push(`${id}: faltou o enum cru na linha "Status (API):" — um estado novo viraria chute`);

    // Comparação EXATA, nunca `includes`: "9,66" é prefixo de "9,660625", e um `includes`
    // daria verde justamente no valor TRUNCADO, que é o erro que importa.
    const odd = linha(txt, "Odd:").split(" ")[0];
    if (odd !== e.odd) falhas.push(`${id}: odd esperada ${e.odd}, veio "${odd}"`);
    if (e.tela && odd === e.tela.replace(".", ","))
      falhas.push(`${id}: emitiu a odd TRUNCADA do card (${e.tela}) em vez do valor cheio ${e.odd}`);

    // Toda a conta é múltipla de 3 pernas.
    const tipo = linha(txt, "Tipo:");
    if (tipo !== "Múltipla (3 seleções)") falhas.push(`${id}: tipo esperado "Múltipla (3 seleções)", veio "${tipo}"`);

    // O rótulo do esporte é COPIADO pela IA para a coluna Esporte: se não for o valor
    // OFICIAL do MASTER_ESPORTES, o mesmo esporte entra no banco com duas grafias (foi o
    // "Beisebol" × "Baseball" da VaideBet, s210).
    const esp = linha(txt, "Esporte:");
    if (/a conferir/.test(esp)) falhas.push(`${id}: esporte não mapeado → "${esp}"`);
    if (e.esporte && !e.esporte.test(esp)) falhas.push(`${id}: esporte "${esp}" não bate com o card`);

    if (e.retorno) {
      const r = linha(txt, "Retorno:");
      if (r !== "R$ " + e.retorno) falhas.push(`${id}: retorno esperado R$ ${e.retorno}, veio "${r}"`);
      // A odd emitida tem de explicar o retorno do card até o centavo — é a régua global do W.
      const n = Number(e.odd.replace(".", "").replace(",", "."));
      const st = Number(e.stake.replace(".", "").replace(",", "."));
      const ret = Number(e.retorno.replace(".", "").replace(",", "."));
      if (!(Math.abs(n * st - ret) <= 0.01))
        falhas.push(`${id}: odd ${e.odd} × stake ${e.stake} não explica o retorno ${e.retorno} do card`);
    }

    // O BÔNUS POR FORA DA ODD. Duas asserções, e as duas importam: o bloco tem de AVISAR que
    // houve bônus (senão a IA não entende por que a odd difere do card) e NÃO pode emitir a
    // odd declarada, que aqui deixa R$ 75,11 de fora.
    if (e.bonus) {
      const marca = txt.split("\n").find((l) => l.startsWith("Marcação da casa: aposta com bônus")) || "";
      if (!marca) falhas.push(`${id}: bilhete com bônus sem a marcação — a IA não saberia por que a odd difere do card`);
      else if (!marca.includes("R$ " + e.bonus)) falhas.push(`${id}: bônus esperado R$ ${e.bonus} na marcação, veio "${marca}"`);
      if (odd === e.declarada)
        falhas.push(`${id}: emitiu a odd DECLARADA (${e.declarada}), que ignora o bônus de R$ ${e.bonus} — o retorno do card não fecha`);
    }

    if (e.aberta) {
      if (/→ [WLV]\b/.test(status)) falhas.push(`${id}: aberta recebeu código de resultado — proibido`);
      if (/Ganho → W/.test(txt)) falhas.push(`${id}: ABERTA virou vitória — totalWin foi lido como retorno realizado`);
      const pot = linha(txt, "Retorno potencial:");
      if (pot !== "R$ " + e.potencial) falhas.push(`${id}: retorno potencial esperado R$ ${e.potencial}, veio "${pot}"`);
      if (linha(txt, "Retorno:")) falhas.push(`${id}: aberta emitiu linha "Retorno:" — só potencial é permitido`);
      if (ABERTO_COM_OFERTA_DE_CASHOUT.includes(id) && /Cash *Out/i.test(txt))
        falhas.push(`${id}: emitiu "Cash Out" num bilhete ABERTO — o botão da tela é oferta de venda, não liquidação`);
    }
  }

  // ── 3. CONTROLE NEGATIVO ──────────────────────────────────────────────────────
  // Caso espelho passa verde de primeira, e isso NÃO é evidência. Aqui provamos que as
  // asserções centrais têm dente.
  {
    const abertaCrua = JSON.parse(fixture("estrelabet.open.json")).bets.find((b) => String(b.id) === "5353319605");
    testes++;
    // (a) o MESMO bilhete, com status 1, tem de sair como W com "Retorno:". Se sair igual ao
    //     aberto, a asserção da ABERTA era vácuo.
    const comoResolvido = fmt({ ...abertaCrua, status: 1 });
    if (!/Ganho → W/.test(comoResolvido) || !linha(comoResolvido, "Retorno:"))
      falhas.push("controle negativo: o bilhete com status=1 não virou W com 'Retorno:' — a asserção da ABERTA não provava nada");
    testes++;
    // (b) status fora de {0,1,2} sobe CRU e marcado — nunca vira W/L pelo dinheiro.
    const desconhecido = fmt({ ...abertaCrua, status: 17 });
    if (!/a conferir/.test(desconhecido)) falhas.push("status desconhecido (17) não foi marcado 'a conferir' — vira chute");
    if (/Ganho → W|Perdeu → L/.test(desconhecido)) falhas.push("status desconhecido (17) foi convertido em resultado — proibido");
    testes++;
    // (c) o mapa de esporte tem de FALHAR ALTO no id que ele não conhece. Sem isto, a
    //     asserção "esporte não é 'a conferir'" da seção 2 poderia estar passando por um
    //     fallback silencioso em vez de por um mapeamento de verdade.
    const inedito = fmt({ ...abertaCrua, selections: abertaCrua.selections.map((s) => ({ ...s, sportTypeId: 999 })) });
    if (!/a conferir/.test(linha(inedito, "Esporte:")))
      falhas.push("sportTypeId inédito (999) não foi marcado 'a conferir' — a IA receberia um esporte inventado");
  }

  // ── 4. O bloco da Estrela Bet é IDÊNTICO ao da VaideBet — é isso que "espelho" quer dizer ──
  // Roda a MESMA fixture pelos dois hosts e compara byte a byte. Se um dia alguém amarrar o
  // inject ou o formatador ao domínio, isto acusa na hora.
  {
    const { ultima: pelaVB } = await umClique(CORPO_RESOLVIDAS,
      { href: "https://www.vaidebet.bet.br/sports?shareCode=IHLBJGT77FZ#/betHistory" });
    const vb = new Map(((pelaVB && pelaVB.bets) || []).map((b) => [String(b.id), b]));
    const eb = new Map(colhido.map((b) => [String(b.id), b]));
    testes++;
    if (vb.size !== eb.size) {
      falhas.push(`espelho: host vaidebet capturou ${vb.size} e host estrelabet ${eb.size} — a captura não pode depender do domínio`);
    } else {
      const diferentes = [];
      for (const [id, b] of eb) {
        const o = vb.get(id);
        if (!o || fmt(o) !== fmt(b)) diferentes.push(id);
      }
      if (diferentes.length)
        falhas.push(`espelho: ${diferentes.length} bloco(s) diferem entre os dois hosts (${diferentes.slice(0, 3).join(", ")}…)`);
    }
  }

  // ── 5. O CORS QUE RECUSA CREDENCIAL — o único ponto em que esta casa não é espelho ──
  // Dois lados, e os dois são load-bearing:
  //   (a) com o gateway recusando `include`, a captura tem de sair INTEIRA mesmo assim;
  //   (b) num gateway que aceita, o `include` tem de continuar sendo a PRIMEIRA tentativa —
  //       é o comportamento das 4 irmãs, e nenhuma delas foi medida por nós. Trocar a ordem
  //       "porque o Bearer basta" seria mudar 4 casas em produção por dedução.
  {
    testes++;
    const { ultima, credenciais } = await umClique(CORPO_RESOLVIDAS, { corsRecusaCredencial: true });
    const n = ((ultima && ultima.bets) || []).length;
    if (n !== 12)
      falhas.push(`CORS: com o gateway recusando credentials:"include", vieram ${n} de 12 bilhetes — ` +
                  `o replay inteiro passa pelo fetch, então recusa sem fallback ZERA a casa`);
    if (!ultima || !ultima.fim) falhas.push('CORS: não sinalizou "fim" no caminho do fallback');
    // O fallback não pode virar uma tentativa dupla eterna: depois da 1ª recusa a escolha é
    // memorizada, então só UMA requisição sai com `include` na captura toda.
    //
    // ⚠ O índice 0 é a requisição da PRÓPRIA PÁGINA (o `optsInicial`, que o navegador faz e o
    // inject só escuta) — ela nunca leva credencial nossa. Só a partir do índice 1 é replay.
    const doReplay = (lista) => lista.slice(1);
    const comInclude = doReplay(credenciais).filter((c) => c === "include").length;
    if (comInclude !== 1)
      falhas.push(`CORS: ${comInclude} requisições do replay saíram com credentials:"include" — a escolha tem de ser memorizada após a 1ª recusa (esperado 1)`);

    testes++;
    const { credenciais: cred2 } = await umClique(CORPO_RESOLVIDAS);   // gateway que ACEITA
    const replay2 = doReplay(cred2);
    if (!replay2.length) falhas.push("ordem: o replay não fez nenhuma requisição — nada a conferir");
    else if (replay2[0] !== "include")
      falhas.push(`ordem: a 1ª tentativa do replay saiu com credentials="${replay2[0]}" — tem de ser "include", ` +
                  `que é o que VaideBet/Esportiva/Jogo de Ouro/Betpix365 usam hoje e não foi medido por nós`);
    if (replay2.some((c) => c !== "include"))
      falhas.push("ordem: num gateway que aceita credencial, nenhuma requisição do replay pode cair no fallback");
  }

  // ── 6. TAB LITERAL NO NOME DO TIME — o dicionário deste tenant corrompe TSV ────
  // `"Real Sociedad vs. RCD Espanyol\t\t"` é dado REAL desta conta. TAB é o separador de
  // coluna do TSV (`MASTER_OUTPUT`) e a IA copia nome próprio verbatim (é a premissa do gate
  // de fidelidade da s302): um TAB na Descrição empurra Stake/Odd/Resultado uma casa à
  // direita e o `parse_tsv` lê o código do bilhete no lugar do resultado.
  {
    const cru = JSON.parse(fixture("estrelabet.settled.json")).bets.find((b) => String(b.id) === "5347925916");
    testes++;
    // Primeiro: a fixture continua sendo o dado real (se alguém "limpar" o JSON, o teste
    // deixa de testar — é o falso verde do dado sintético que não exerce a regra).
    if (!/\t/.test(cru.selections[0].eventName))
      falhas.push("fixture: o TAB literal sumiu de estrelabet.settled.json — o caso deixou de exercer a regra");

    const txt = fmt(cru);
    testes++;
    if (/\t/.test(txt))
      falhas.push("bloco emitido contém TAB literal — vai partir a coluna do TSV na saída da IA");
    // E o nome tem de continuar LEGÍVEL, não apenas sem TAB: o gate de fidelidade da s302
    // confere nome próprio por substring contra o bloco cru.
    if (!txt.includes("Jogo: Real Sociedad vs. RCD Espanyol"))
      falhas.push('o nome do jogo não saiu higienizado como "Real Sociedad vs. RCD Espanyol"');

    testes++;
    // Espaço DUPLO no meio do nome (`"Mirassol  vs. Palmeiras"`, também real) não pode
    // sobreviver: dois nomes do mesmo jogo contariam como jogos diferentes.
    //
    // ⚠ Medir só o NOME, não a linha: as linhas de contexto do bloco são indentadas com 4
    // espaços, e uma regex sobre a linha inteira acusaria a própria indentação.
    const duplo = JSON.parse(fixture("estrelabet.open.json")).bets.find((b) => String(b.id) === "5353279994");
    const nomes = fmt(duplo).split("\n")
      .map((l) => /Jogo: (.*?)(?: · |$)/.exec(l))
      .filter(Boolean).map((m) => m[1]);
    if (!nomes.length) falhas.push('nenhuma linha "Jogo:" no bloco — nada a conferir');
    if (nomes.some((n) => / {2,}/.test(n)))
      falhas.push(`espaço duplo sobreviveu no nome do jogo (${JSON.stringify(nomes.find((n) => / {2,}/.test(n)))}) — a comparação de mesmo-jogo fica cega`);
    // E o nome tem de ter chegado higienizado ao valor esperado, não só "sem espaço duplo".
    if (!nomes.includes("Mirassol vs. Palmeiras"))
      falhas.push(`esperava "Mirassol vs. Palmeiras" entre os jogos, veio ${JSON.stringify(nomes)}`);
  }

  return { falhas, testes };
}

// ─────────────────────────────────────────────────────────────────────────────
// O QUE ESTE CASO **NÃO** COBRE (o verde aqui não promete estas coisas):
//
//  • **CORS de verdade.** O sandbox reproduz o SINTOMA (a promise rejeita), não a
//    negociação do navegador. Que o gateway recusa `include` e aceita sem credencial está
//    medido AO VIVO (3 de 3 em cada sentido), não aqui — e que as 4 irmãs continuam
//    aceitando `include` NÃO está medido em lugar nenhum: é preservado por desenho, mantendo
//    o `include` como primeira tentativa.
//  • **Anulada (`status 8`) e cashout.** A conta tem 12 bilhetes e nenhum dos dois. O
//    tratamento vem do código compartilhado e está travado em `esportiva.mjs`.
//  • **Bet builder e boost.** `bbOdds` vem `[]` em 36 de 36 seleções e não há
//    `boostedSelection`/`boostedBet` — as 17 chaves que faltam para as irmãs são todas
//    dessas duas famílias. O selo desta marca é a **SuperMúltipla** (`bonus`), que é outra
//    coisa: bônus pago por fora da odd, não boost da odd.
//  • **Paginação com mais de uma página.** As duas abas devolvem `isLastPage:true` na
//    página 1 porque a conta tem 12 bilhetes; o replay de várias páginas está travado em
//    `esportiva.mjs`, que tem uma conta grande.
//  • **eBasket.** O `sportTypeId 12` está provado como `Basquete` por dois eixos (ver o
//    comentário em `_ESPORTE_VB`), mas não há bilhete de basquete VIRTUAL nesta conta para
//    provar que a casa o separa — ela lista `E-Basquete` como sport próprio, o que é
//    indício, não medição.
