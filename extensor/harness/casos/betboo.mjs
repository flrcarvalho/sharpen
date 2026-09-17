// Betboo (bwin / Entain) — ESPELHO da SportingBet (s372).
//
// A Betboo não tem inject, formatador nem robô próprios: ela reusa `spb_inject.js`,
// `formatTicketSPB` e `roboSPBPassive`, como a Betfast reusa os da Tivo e a Betboom os da
// Jonbet. Este caso existe porque o compartilhamento é justamente a parte perigosa — ele
// prova que o MESMO código lê a OUTRA casa contra o card DELA, e não que "deve funcionar
// porque é igual".
//
// O que sustenta o espelho, MEDIDO no recon (17/09/2026) e não deduzido:
//   • `POST /pt-br/sports/api/mybets/betslips` no host da própria casa, mesmo corpo
//     (`typeFilter`/`index`/`maxItems`/`pinnedBetslipIds`/`eventIds`/`useGroupedView`) e
//     mesmo topo de resposta (`summary`/`betslips`/`typeFilter`/`errorLoadingBets`);
//   • **sem os cabeçalhos do motor a casa devolve 200 com o HTML da SPA** (medido: 109 KB),
//     igual à SportingBet. Com eles e sem sessão vem **401**; uma rota inexistente devolve
//     o mesmo HTML 200 — é o controle que prova que o 401 é da rota real;
//   • **`index` é PÁGINA**: `index:2` voltou `betslips: []` nas duas abas;
//   • **fim autoritativo = lista VAZIA** (não há `isLastPage`/`more`/`hasNext`);
//   • o inject casa por PATH (`/mybets/betslips`) e monta a URL de `location.origin`, então
//     ele serve a Betboo sem uma linha de mudança.
//
// TEXTO está descartado com medição, e aqui a medida é mais dura que na SportingBet:
// **nenhum dos 5 ids aparece no `innerText`** da lista (o card colapsado não mostra o
// código), não há linha em branco entre bilhetes, e as seleções saem COLADAS sem separador
// (`"Indonésia -5.5Mais de 0.5Mais de 0.5"`). Sem id não há dedup, e o `roboScroll` juntaria
// tudo num bloco só (a lição da KTO, s192).
//
// ⚠️ O QUE ESTE CASO TRAVA DE NOVO, que a SportingBet não tinha amostra para travar:
//
//   1. **`promoTokens` / `AccaBoost`** — o "+5% Múltipla+" que o card estampa como
//      *Promoção usada*. Está em 3 dos 8 bilhetes. No aberto a conta fecha exata:
//      `maxPayout 2595,92 + WinningsBoost 119,75 = BoostedWinnings 2715,67`. É boost de
//      MÚLTIPLA, no nível do bilhete — não é o `priceBoostData` (boost de odd por seleção)
//      que o formatador já trata.
//   2. **`sport.id` 7 e 56** (Basquete, Tênis de mesa) — fora do `_ESPORTE_SPB`, que só tem
//      `{4, 23}`. São **4 dos 8** bilhetes caindo em "id não mapeado".
//   3. **Duas fontes de catálogo no mesmo bilhete** — pernas com `compoundId: "1:"` vêm
//      SEM `optionBetDetails` (logo sem `isBetBuilder`/`priceBoostData`) e às vezes sem
//      `outcome`. São 5 das 24 pernas da amostra.
//
// ⚠️ O QUE ESTE CASO **NÃO** COBRE, e não dá para fingir que cobre:
//   • **nenhuma SIMPLES.** Os 8 bilhetes da conta são `slipType: "Combo"`;
//   • **nenhum `Canceled`**, nenhum freebet, nenhum cashout, nenhum bet builder (a casa tem
//     "Criar Aposta+" no menu, mas a conta não tem amostra);
//   • **nenhum GANHO com AccaBoost.** Então não se sabe se o `payout` de um ganho turbinado
//     já vem somado ou se o bônus é creditado à parte. O controle negativo (b) exercita a
//     regra do projeto para as duas hipóteses, mas a fonte do número segue por medir.
//
// Os 8 bilhetes abaixo foram lidos do CARD (abas Liquidadas, Em Aberto e Ao Vivo de
// 17/09/2026), nenhum do que o código produz.
import { rodarInject, carregarContent, fixture, linha, cloneAbortado } from "../sandbox.mjs";

export const casa = "BETBOO";

// `evento` é a data que VAI PARA A COLUNA DATA do TSV (`MASTER_OUTPUT §4`): sai de
// `bets[].fixture.date`, a MAIS RECENTE quando há várias pernas, convertida para Brasília.
// `colocacao` sai de `conclusionDateUtc` — e o nome desse campo MENTE aqui também: o card
// do 20RT3JEUU6 estampa "16/09/2026 • 21:54" e o campo traz `2026-09-17T00:54:07Z`, que é
// 16/09 21:54 em Brasília, enquanto o evento mais recente é 17/09. Uma "conclusão" não pode
// ser anterior ao evento.
// `odd` é a "Cota" do card. ⚠ A Betboo mistura convenção no MESMO card: a Cota vem com
// PONTO (`7.58`) e o dinheiro com VÍRGULA (`R$ 201,00`).
const ESPERADO = {
  // ── liquidadas (5 de 5, lidas do CARD) ────────────────────────────────────────
  // Card: "Múltipla · 3 escolhas · R$ 201,00 · Cota 8.02 · Ganhos - · Derrota".
  // Mistura BASQUETE (id 7) com BEISEBOL (id 23) — a 1ª perna é a que vai para a linha
  // "Esporte:", e é ela que hoje cai fora do mapa.
  "20RT3JEUU6": { evento: "17/09/2026 01:00:00", colocacao: "16/09/2026 21:54:07", odd: "8,02",
                  stake: "201,00", status: /^Perdeu → L$/, tipo: /^Múltipla \(3 seleções\)$/,
                  esporte: /^Basquete\b/ },

  // Card: "Cota 7.41 · Ganhos - · Derrota" + faixa "Promoção usada ⚡ +5% Múltipla+".
  // 1ª perna é TÊNIS DE MESA (id 56) — a casa escreve "Tênis de mesa", com `m` minúsculo.
  "20RSN4R2C5": { evento: "16/09/2026 16:00:00", colocacao: "16/09/2026 14:44:52", odd: "7,41",
                  stake: "201,00", status: /^Perdeu → L$/, tipo: /^Múltipla \(3 seleções\)$/,
                  esporte: /^Tênis de Mesa\b/, accaBoost: "5" },

  // Card: "Cota 6.59 · Ganhos - · Derrota". Três pernas de MLB, jogos diferentes.
  "20RSN0GYG6": { evento: "16/09/2026 21:05:00", colocacao: "16/09/2026 14:40:20", odd: "6,59",
                  stake: "201,00", status: /^Perdeu → L$/, tipo: /^Múltipla \(3 seleções\)$/,
                  esporte: /^Baseball\b/ },

  // O ÚNICO W da conta. Card: "Múltipla · 2 escolhas · R$ 201,00 · Cota 7.58 ·
  // Ganhos R$ 1.524,59" (verde).
  //
  // ⚠️ A Cota do card NÃO explica o retorno: 201 × 7,58 = 1.523,58, um real a menos que os
  // 1.524,59 que a casa pagou. A odd exibida é arredondada a 2 casas e o retorno é exato,
  // então a régua global do W manda (`retorno ÷ stake`) e o bloco emite a odd COMPLETA.
  // Travar "7,58" aqui seria travar o arredondamento da casa no lugar do dinheiro.
  "20RSMW9KJA": { evento: "16/09/2026 19:45:00", colocacao: "16/09/2026 14:36:02",
                  odd: "7,58502488", oddCard: "7.58",
                  stake: "201,00", status: /^Ganho → W/, tipo: /^Múltipla \(2 seleções\)$/,
                  esporte: /^Baseball\b/, retorno: "1524,59" },

  // Card: "Cota 12.59 · Ganhos - · Derrota" + "Promoção usada ⚡ +5% Múltipla+".
  "20RSMT6YYF": { evento: "16/09/2026 19:00:00", colocacao: "16/09/2026 14:34:02", odd: "12,59",
                  stake: "201,00", status: /^Perdeu → L$/, tipo: /^Múltipla \(3 seleções\)$/,
                  esporte: /^Futebol\b/, accaBoost: "5" },

  // ── abertas (3 de 3, lidas do CARD) ───────────────────────────────────────────
  // `payout: 0` e o potencial em campo PRÓPRIO (`maxPayout` = `grossPossibleWinnings`).
  // Ler `maxPayout` como realizado transformaria aposta viva em vitória fantasma — foi o
  // que a VaideBet levou a produção na s210, lá com um campo só para as duas coisas.
  //
  // Card: "Múltipla · 2 escolhas · R$ 201,00 · Cota 6.75 · Possíveis ganhos R$ 1.356,75".
  "20RTWGUF65": { evento: "18/09/2026 15:30:00", colocacao: "17/09/2026 11:12:50", odd: "6,75",
                  stake: "201,00", status: /em aberto/, tipo: /^Múltipla \(2 seleções\)$/,
                  esporte: /^Baseball\b/, aberta: true, potencial: "1356,75" },

  // Card: "Cota 6.30 · Possíveis ganhos R$ 1.266,30".
  // ⚠ A Cota do card vem com 2 casas FIXAS ("6.30") e o payload traz `6.3`. O bloco emite a
  // odd sem truncar e sem preencher, então o esperado é "6,3" — preencher com zero aqui
  // seria formatar odd, que o projeto proíbe.
  "20RTWFSR4N": { evento: "19/09/2026 08:30:00", colocacao: "17/09/2026 11:11:30", odd: "6,3",
                  stake: "201,00", status: /em aberto/, tipo: /^Múltipla \(3 seleções\)$/,
                  esporte: /^Basquete\b/, aberta: true, potencial: "1266,30" },

  // O bilhete que mais ensina da amostra: ABERTO **com AccaBoost de valor**, e o card resolve
  // sozinho qual dos dois números é o potencial.
  //
  // ⚠️ O rótulo MUDA de "Possíveis ganhos" para **"Ganhos melhorados"**, e a casa mostra
  // **`R$ 2.595,92` RISCADO** ao lado de **`R$ 2.715,67`**. Ou seja: o potencial que vale é
  // o COM boost, e o `maxPayout` do payload é o riscado. É o mesmo padrão do
  // `priceBoostData` que o formatador já trata, só que no DINHEIRO em vez da odd — e por
  // isso o esperado aqui é 2.715,67, com o 2.595,92 descendo como marcação.
  //
  // Duas das três pernas vêm do catálogo `1:`, SEM `optionBetDetails`.
  "20RTRWRSKY": { evento: "19/09/2026 08:30:00", colocacao: "17/09/2026 09:16:49", odd: "12,91",
                  stake: "201,00", status: /em aberto/, tipo: /^Múltipla \(3 seleções\)$/,
                  esporte: /^Basquete\b/, aberta: true, potencial: "2715,67",
                  accaBoost: "5", potencialRiscado: "2595,92" },
};

const URL_API = "https://www.betboo.bet.br/pt-br/sports/api/mybets/betslips";
const HREF = "https://www.betboo.bet.br/pt-br/sports/minhas-apostas/liquidada";

// Corpo que a página emite ao abrir cada aba (mesmo formato medido na SportingBet; o recon
// da Betboo confirmou que a API aceita e responde a ele campo por campo).
const CORPO_LIQUIDADAS = '{"index":1,"maxItems":6,"typeFilter":"Settled","pinnedBetslipIds":"","eventIds":[],"useGroupedView":false}';
const CORPO_ABERTAS    = '{"index":1,"maxItems":6,"typeFilter":"Open","pinnedBetslipIds":"","eventIds":[],"useGroupedView":false}';

// Cabeçalhos do motor, os mesmos que o recon usou para arrancar 200 na Betboo.
const HEADERS_PAGINA = {
  "x-bwin-sports-api": "prod",
  "cache-control": "no-cache",
  "x-bwin-browser-url": HREF,
  "X-Device-Type": "desktop",
  "X-From-Product": "host-app",
  "Sports-Api-Version": "SportsAPIv2",
  "Accept": "application/json, text/plain, */*",
  "Content-Type": "application/json",
};

// O que a Betboo devolve — com status 200! — para quem chama sem os cabeçalhos do motor.
// Medido: 109.472 bytes de HTML da SPA. A falha não grita.
const HTML_DA_SPA = '<!DOCTYPE html><html class="vn-26" lang="pt-BR"><head><title>betboo</title></head><body>SPA</body></html>';

// Servidor de mentira: responde pelo `typeFilter` e pelo `index` do CORPO, como a casa faz.
// Página 1 das liquidadas = 5 bilhetes, das abertas = 3; página 2 = VAZIO, que é o único
// jeito desta casa dizer "acabou". Se o inject não parar aí, ele pagina para sempre.
//
// Duas fidelidades medidas na Betboo que este servidor precisa ter:
//   • quem chama SEM `x-bwin-sports-api` recebe **HTML com status 200**, não erro;
//   • a PRIMEIRA resposta chega com o CLONE MORTO — a SPA aborta o `fetch` logo após
//     consumir o corpo. Sem isso, um inject que dependesse da leitura passiva passaria
//     verde, que é exatamente o defeito que travou dois testers na SportingBet (s305).
function servidor() {
  const liquidadas = fixture("betboo.settled.json");
  const abertas = fixture("betboo.open.json");
  const vazio = JSON.stringify({ summary: {}, betslips: [], typeFilter: "Settled", errorLoadingBets: false });
  const pedidos = [];
  const cabecalhos = [];
  let primeira = true;
  const resp = (url, opts) => {
    if (!String(url).includes("/mybets/betslips")) return null;
    const body = String((opts && opts.body) || "");
    const hdrs = (opts && opts.headers) || {};
    pedidos.push(body);
    cabecalhos.push(hdrs);
    let o = null;
    try { o = JSON.parse(body); } catch (e) { return null; }
    if ((opts && opts.method) !== "POST") return null;          // GET devolveria o HTML da SPA
    const temMotor = Object.keys(hdrs).some((k) => String(k).toLowerCase() === "x-bwin-sports-api");
    if (!temMotor) return HTML_DA_SPA;                          // 200 com HTML, como a casa faz
    const pag = Number(o.index) || 1;
    const corpo = pag > 1 ? vazio : (o.typeFilter === "Open" ? abertas : liquidadas);
    if (primeira) { primeira = false; return cloneAbortado(corpo); }
    return corpo;
  };
  return { resp, pedidos, cabecalhos };
}

async function umClique(corpoInicial) {
  const srv = servidor();
  const { ultima, urls } = await rodarInject({
    inject: "spb_inject.js",
    href: HREF,
    urlInicial: URL_API,
    optsInicial: { method: "POST", headers: HEADERS_PAGINA, body: corpoInicial },
    pedido: "__sharpenupSPBReq",
    ms: 1200,
    responder: srv.resp,
  });
  return { ultima, pedidos: srv.pedidos, cabecalhos: srv.cabecalhos, urls };
}

// O cenário que derrubou a SportingBet em produção e vale igual aqui: a página NÃO faz
// requisição nenhuma (carga direta de Minhas Apostas vem renderizada pelo servidor) e o
// operador roda o robô.
async function semRequisicaoDaPagina() {
  const srv = servidor();
  const { ultima } = await rodarInject({
    inject: "spb_inject.js",
    href: HREF,
    semRequisicaoInicial: true,
    pedido: "__sharpenupSPBReq",
    ms: 1200,
    responder: srv.resp,
  });
  return { ultima, pedidos: srv.pedidos, cabecalhos: srv.cabecalhos };
}

export async function rodar() {
  const falhas = [];
  let testes = 0;

  // ── 1. Um clique = as duas listas, partindo de QUALQUER aba ───────────────────
  let colhido = null;
  for (const [rotulo, corpo] of [["aba Liquidadas", CORPO_LIQUIDADAS], ["aba Em Aberto", CORPO_ABERTAS]]) {
    const { ultima, pedidos, cabecalhos, urls } = await umClique(corpo);
    testes++;
    if (!ultima) { falhas.push(`${rotulo}: o inject não emitiu nenhuma mensagem`); continue; }
    if (!ultima.hook) falhas.push(`${rotulo}: não sinalizou 'hook' — o autodiagnóstico fica cego`);
    if (typeof ultima.respostas !== "number" || ultima.respostas < 1)
      falhas.push(`${rotulo}: 'respostas' não reportado — não separa "não injetei" de "endpoint mudou"`);
    if (!ultima.fim) falhas.push(`${rotulo}: não sinalizou 'fim' — o robô esperaria o teto`);

    const bets = ultima.bets || [];
    if (bets.length !== 8) falhas.push(`${rotulo}: esperava 8 bilhetes (5 liquidados + 3 abertos), vieram ${bets.length}`);

    // O inject monta a URL de `location.origin` — é isto que o faz servir a Betboo sem
    // mudança. Se alguém cravar o host da SportingBet, o espelho quebra aqui.
    const foraDoHost = (urls || []).filter((u) => String(u).includes("/mybets/betslips") && !String(u).includes("betboo.bet.br"));
    if (foraDoHost.length)
      falhas.push(`${rotulo}: ${foraDoHost.length} requisição(ões) saíram de outro host (${foraDoHost[0]}) — o inject cravou o domínio da gêmea`);

    // As DUAS abas têm de ser pedidas, não importa qual o operador abriu.
    const pediu = (f) => pedidos.some((b) => { try { return JSON.parse(b).typeFilter === f; } catch (e) { return false; } });
    if (!pediu("Settled")) falhas.push(`${rotulo}: nunca pediu a aba Liquidadas`);
    if (!pediu("Open")) falhas.push(`${rotulo}: nunca pediu a aba Em Aberto — aposta viva sumiria do lote`);

    // Paginação ativa: `index` é PÁGINA (medido na Betboo: index 2 devolve lista vazia).
    const p2 = pedidos.find((b) => { try { return Number(JSON.parse(b).index) === 2; } catch (e) { return false; } });
    if (!p2) falhas.push(`${rotulo}: nenhuma requisição pediu index 2 — a paginação não avançou`);

    for (const b of pedidos) {
      let o = null; try { o = JSON.parse(b); } catch (e) { falhas.push(`${rotulo}: corpo não é JSON: ${b.slice(0, 60)}`); continue; }
      if (typeof o.maxItems !== "number" || o.maxItems < 1) falhas.push(`${rotulo}: maxItems corrompido → ${b}`);
      if (!("useGroupedView" in o)) falhas.push(`${rotulo}: o corpo perdeu campos do formato real → ${b}`);
    }

    // Todo pedido tem de levar o cabeçalho do motor. Sem ele a Betboo responde 200 com o
    // HTML da SPA — o replay "funciona", o `forward` descarta e o lote volta vazio sem erro.
    const semMotor = cabecalhos.filter((h) => !Object.keys(h || {}).some((k) => String(k).toLowerCase() === "x-bwin-sports-api"));
    if (semMotor.length) falhas.push(`${rotulo}: ${semMotor.length} requisição(ões) sem 'x-bwin-sports-api' — a casa devolveria HTML com status 200`);

    if (!colhido && bets.length) colhido = bets;
  }

  // ── 1b. ARRANQUE A FRIO: a página não fez requisição nenhuma ──────────────────
  {
    const { ultima, pedidos, cabecalhos } = await semRequisicaoDaPagina();
    testes++;
    if (!ultima) falhas.push("a frio: o inject não emitiu nenhuma mensagem");
    else {
      if (!ultima.hook) falhas.push("a frio: não sinalizou 'hook'");
      if (!(ultima.respostas >= 1)) falhas.push("a frio: 'respostas' ficou em 0 — o replay não arrancou sem requisição aprendida");
      if (!ultima.fim) falhas.push("a frio: não sinalizou 'fim' — o robô esperaria o teto de inatividade");
      const n = (ultima.bets || []).length;
      if (n !== 8) falhas.push(`a frio: esperava 8 bilhetes, vieram ${n} — sem requisição da página o lote precisa sair igual`);
    }
    testes++;
    const pediu = (f) => pedidos.some((b) => { try { return JSON.parse(b).typeFilter === f; } catch (e) { return false; } });
    if (!pediu("Settled") || !pediu("Open")) falhas.push("a frio: alguma aba não foi pedida");
    if (!cabecalhos.length || !cabecalhos.every((h) => Object.keys(h || {}).some((k) => String(k).toLowerCase() === "x-bwin-sports-api")))
      falhas.push("a frio: requisição sem 'x-bwin-sports-api' — a casa devolveria HTML com status 200");
  }

  if (!colhido) return { falhas: falhas.concat(["nenhum bilhete colhido — o resto do caso não roda"]), testes };

  // ── 2. Leitura bilhete a bilhete, contra o card DA BETBOO ─────────────────────
  const fmt = carregarContent().pegar("formatTicketSPB");
  for (const b of colhido) {
    const id = String(b.betSlipNumber || "");
    const e = ESPERADO[id];
    if (!e) { falhas.push(`bilhete inesperado na fixture: ${id}`); continue; }
    const txt = fmt(b);
    testes++;

    if (!txt.startsWith(`[Código: ${id}]`)) falhas.push(`${id}: marcador [Código:] ausente/errado na 1ª linha`);

    const evento = linha(txt, "Data (evento mais recente):");
    if (evento !== e.evento) falhas.push(`${id}: data do EVENTO esperada ${e.evento}, veio "${evento}" (é ela que vai para a coluna Data)`);

    // ⚠️ `conclusionDateUtc` é a COLOCAÇÃO, apesar do nome. Prova NESTA casa: o card do
    // 20RT3JEUU6 estampa "16/09/2026 • 21:54" e o evento mais recente dele é 17/09 01:00.
    const colocacao = linha(txt, "Data (colocação):");
    if (colocacao !== e.colocacao) falhas.push(`${id}: colocação esperada ${e.colocacao}, veio "${colocacao}"`);

    const stake = linha(txt, "Stake:");
    if (stake !== "R$ " + e.stake) falhas.push(`${id}: stake esperada R$ ${e.stake}, veio "${stake}"`);

    const status = linha(txt, "Status:");
    if (!e.status.test(status)) falhas.push(`${id}: status "${status}"`);

    if (!/state=\w+/.test(linha(txt, "Status (API):")))
      falhas.push(`${id}: faltou o enum cru na linha "Status (API):"`);

    const odd = linha(txt, "Odd:").split(" ")[0];
    if (odd !== e.odd) falhas.push(`${id}: odd esperada ${e.odd}, veio "${odd}"`);

    const tipo = linha(txt, "Tipo:");
    if (!e.tipo.test(tipo)) falhas.push(`${id}: tipo "${tipo}"`);

    // ⚠️ O rótulo do esporte sai do MAPA DE ID, nunca de `sport.name`. A Betboo trouxe DOIS
    // ids que a SportingBet nunca trouxe: 7 ("Basquete") e 56 ("Tênis de mesa", com `m`
    // minúsculo). São 4 dos 8 bilhetes. Sem mapear, a IA copia o rótulo da casa verbatim e
    // grava duas grafias do mesmo esporte (o que a VaideBet fez na s210).
    const esp = linha(txt, "Esporte:");
    if (!e.esporte.test(esp)) falhas.push(`${id}: esporte "${esp}" não é o valor oficial do MASTER_ESPORTES`);

    // ⚠️ AccaBoost ("+5% Múltipla+"): é boost de MÚLTIPLA, no nível do bilhete
    // (`promoTokens`), e não o `priceBoostData` por seleção que o formatador já trata.
    // O card estampa "Promoção usada". Sem a marcação, a IA não tem como saber que a Cota
    // declarada não é a única coisa que decide o retorno.
    if (e.accaBoost) {
      const marca = txt.split("\n").find((l) => /Marcação da casa: .*m[úu]ltipla/i.test(l)) || "";
      if (!marca) falhas.push(`${id}: AccaBoost do card ("+5% Múltipla+") não aparece no bloco`);
      // ⚠️ O percentual se confere ANCORADO no `+`, nunca por substring solta: `includes("5%")`
      // passava com "+0,05%" na marcação, e foi assim que a mutação do fator de conversão do
      // `AccaBoostRatio` (0.0500 → 5) escapou verde na 1ª rodada de mutação deste caso.
      else if (!new RegExp("\\+" + e.accaBoost.replace(",", "[.,]") + "%").test(marca))
        falhas.push(`${id}: o percentual do boost (+${e.accaBoost}%) não saiu na marcação → "${marca}"`);
      // O valor RISCADO do card (o `maxPayout` sem boost) desce como marcação, nunca como
      // o potencial — é o mesmo tratamento que a odd pré-boost já recebe.
      if (e.potencialRiscado && !txt.includes(e.potencialRiscado))
        falhas.push(`${id}: o potencial riscado do card (R$ ${e.potencialRiscado}) não aparece como marcação`);
    } else if (/Marcação da casa: .*m[úu]ltipla\+/i.test(txt)) {
      falhas.push(`${id}: apareceu marcação de AccaBoost em bilhete SEM promoTokens — marcação inventada`);
    }

    if (e.retorno) {
      const r = linha(txt, "Retorno:");
      if (r !== "R$ " + e.retorno) falhas.push(`${id}: retorno esperado R$ ${e.retorno}, veio "${r}"`);
      // ⚠️ E a prova de que a odd do bloco é a do DINHEIRO, não a arredondada do card: a
      // Cota estampada NÃO explica o retorno até o centavo, e é por isso que ela não pode
      // ser a odd gravada.
      const st = Number(e.stake.replace(".", "").replace(",", ".")),
            ret = Number(e.retorno.replace(".", "").replace(",", ".")),
            oCard = Number(String(e.oddCard || e.odd).replace(",", ".")),
            oBloco = Number(e.odd.replace(",", "."));
      if (Math.abs(oCard * st - ret) <= 0.01)
        falhas.push(`${id}: a Cota do card (${e.oddCard}) explica o retorno — o caso perdeu a amostra do arredondamento`);
      if (!(Math.abs(oBloco * st - ret) <= 0.01))
        falhas.push(`${id}: a odd do bloco (${e.odd}) × stake ${e.stake} não dá o retorno ${e.retorno} do card`);
    }

    if (e.aberta) {
      if (/→ [WLV]\b/.test(status)) falhas.push(`${id}: aberta recebeu código de resultado — proibido`);
      if (/Ganho → W/.test(txt)) falhas.push(`${id}: ABERTA virou vitória — maxPayout foi lido como retorno realizado`);
      const pot = linha(txt, "Retorno potencial:");
      if (pot !== "R$ " + e.potencial) falhas.push(`${id}: retorno potencial esperado R$ ${e.potencial}, veio "${pot}"`);
      if (linha(txt, "Retorno:")) falhas.push(`${id}: aberta emitiu linha "Retorno:" — só potencial é permitido`);
    }
  }

  // ── 3. CONTROLES NEGATIVOS ────────────────────────────────────────────────────
  // Um caso que passa verde de primeira não é evidência. Aqui provamos que as asserções
  // centrais têm dente.
  {
    const abertas = JSON.parse(fixture("betboo.open.json")).betslips;
    const comBoost = abertas.find((b) => (b.promoTokens || []).length);

    testes++;
    // (a) o MESMO bilheteberto, com state Won e payout preenchido, TEM de virar W com
    //     "Retorno:". Se sair igual ao aberto, a asserção da aberta não provava nada.
    const comoW = fmt({ ...comBoost, state: "Won",
                        payout: { currency: "BRL", value: 2595.92 },
                        bets: comBoost.bets.map((x) => ({ ...x, state: "Won", outcome: "Ganhas" })) });
    if (!/Ganho → W/.test(comoW) || !linha(comoW, "Retorno:"))
      falhas.push("controle negativo (a): o bilhete com state=Won não virou W com 'Retorno:' — o teste da ABERTA era vácuo");

    testes++;
    // (b) GANHO COM ACCABOOST PAGO. Não há amostra real, então construímos a única situação
    //     que importa: se o boost entrar no `payout` (2.715,67 em vez de 2.595,92), a Cota
    //     declarada (12,91) deixa de explicar o dinheiro e a odd TEM de sair da divisão.
    //     Isto vale para as duas hipóteses da incógnita: se o bônus for creditado à parte, o
    //     `payout` vem sem ele e a odd declarada fecha — e o bloco continua correto.
    const wComBoost = fmt({ ...comBoost, state: "Won",
                            payout: { currency: "BRL", value: 2715.67 },
                            bets: comBoost.bets.map((x) => ({ ...x, state: "Won", outcome: "Ganhas" })) });
    const oddW = linha(wComBoost, "Odd:").split(" ")[0];
    const esperada = String(Math.round((2715.67 / 201) * 1e8) / 1e8).replace(".", ",");
    if (oddW !== esperada)
      falhas.push(`controle negativo (b): ganho com AccaBoost pago saiu com odd "${oddW}" — tem de ser ${esperada} (retorno ÷ stake), nunca a Cota declarada 12,91`);

    testes++;
    // (c) estado fora de {Open,Won,Lost,Canceled} sobe CRU e marcado — nunca vira W/L pelo
    //     dinheiro. Lição da Esportiva (s285).
    const inedito = fmt({ ...abertas[0], state: "PartiallyCashedOut" });
    if (!/a conferir/.test(inedito)) falhas.push("controle negativo (c): estado desconhecido não foi marcado 'a conferir' — vira chute");
    if (/Ganho → W|Perdeu → L/.test(inedito)) falhas.push("controle negativo (c): estado desconhecido foi convertido em resultado — proibido");

    testes++;
    // (d) O ESPORTE sai do MAPA DE ID, nunca de `sport.name`, e a Betboo dá DUAS amostras
    //     onde os dois divergem — coisa que a SportingBet não tinha (lá tudo era futebol,
    //     id 4, onde mapa e `sport.name` dizem o mesmo, e copiar `sport.name` passava VERDE).
    //       • id 23: casa diz "Beisebol", oficial é "Baseball";
    //       • id 56: casa diz "Tênis de mesa", a grafia do projeto é "Tênis de Mesa".
    const todas = JSON.parse(fixture("betboo.settled.json")).betslips.concat(abertas);
    const pernaDe = (sid) => {
      for (const b of todas) for (const s of (b.bets || [])) if (s.sport && s.sport.id === sid) return { b, s };
      return null;
    };
    for (const [sid, oficial] of [[23, "Baseball"], [56, "Tênis de Mesa"], [7, "Basquete"]]) {
      const achado = pernaDe(sid);
      if (!achado) { falhas.push(`controle negativo (d): a fixture perdeu a perna de sportId ${sid} — o teste do rótulo oficial ficou sem amostra`); continue; }
      const esp = linha(fmt({ ...achado.b, slipType: "Single", bets: [achado.s] }), "Esporte:");
      if (!new RegExp("^" + oficial.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "\\b").test(esp))
        falhas.push(`controle negativo (d): sportId ${sid} saiu "${esp}" — tem de ser o valor oficial "${oficial}", nunca o "${achado.s.sport.name}" da casa`);
    }

    testes++;
    // (e) Perna do catálogo `1:` (SEM `optionBetDetails`, e às vezes sem `outcome`) não pode
    //     derrubar nem sumir do bloco. São 5 das 24 pernas da amostra — é a diferença de
    //     forma que a SportingBet não tinha.
    const semDetalhe = (() => {
      for (const b of todas) {
        const s = (b.bets || []).find((x) => !("optionBetDetails" in x));
        if (s) return { b, s };
      }
      return null;
    })();
    if (!semDetalhe) falhas.push("controle negativo (e): a fixture perdeu a perna sem optionBetDetails — a diferença de forma da Betboo ficou sem amostra");
    else {
      const t = fmt(semDetalhe.b);
      const nome = (semDetalhe.s.option && semDetalhe.s.option.name) || "";
      if (nome && !t.includes(nome))
        falhas.push(`controle negativo (e): a seleção "${nome}" (perna sem optionBetDetails) não aparece no bloco`);
      if (/undefined|\[object Object\]/.test(t))
        falhas.push("controle negativo (e): o bloco vazou 'undefined'/'[object Object]' na perna sem optionBetDetails");
    }
  }

  return { falhas, testes };
}
