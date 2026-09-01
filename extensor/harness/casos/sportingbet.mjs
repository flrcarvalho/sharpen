// SportingBet (bwin / Entain) — captura por API `/pt-br/sports/api/mybets/betslips` (s289).
//
// Motor NOVO no Sharpen: não é Altenar, BetBy, BetConstruct, Kambi nem BlueBrown. Não há
// espelho para reusar — o que se herda é só o desenho de "API + replay" (aprende a
// requisição real e repagina), como KTO e VaideBet fazem.
//
// O que sustenta o modo, MEDIDO ao vivo na conta (24/08/2026), não deduzido:
//   • `POST /pt-br/sports/api/mybets/betslips`, corpo
//     `{"index":1,"maxItems":6,"typeFilter":"Open","pinnedBetslipIds":"","eventIds":[],"useGroupedView":false}`;
//   • **GET no mesmo path devolve o HTML da SPA** — sem os headers próprios
//     (`x-xsrf-token`, `x-bwin-sports-api`, `sports-api-version`, `x-from-product`,
//     `x-device-type`, `x-bwin-browser-url`) não existe resposta JSON. Daí o replay ter de
//     reusar os headers da requisição REAL, como na VaideBet (Bearer de outra origem);
//   • **`index` é a PÁGINA, não offset** — provado: `index:1,max:5` e `index:2,max:5`
//     devolveram 10 ids distintos, sem repetição;
//   • **fim autoritativo = lista VAZIA.** Não há `isLastPage`/`more`/`hasNext`:
//     `index:2,max:50` voltou `betslips: []`. É o único sinal que a casa dá;
//   • abas = `typeFilter`: `Settled` · `Open` (a terceira, ao vivo, é recorte das abertas).
//
// TEXTO está descartado com medição, não por gosto: o `innerText` da lista tem **6 bilhetes
// e 0 linhas em branco** — o `roboScroll` juntaria tudo num bloco só e a IA perderia o resto
// em silêncio (a lição da KTO, s192). E o card colapsado não mostra o ID nem as pernas.
import { rodarInject, carregarContent, fixture, linha, cloneAbortado } from "../sandbox.mjs";

export const casa = "SportingBet";

// Cada valor abaixo foi lido do CARD da SportingBet (aba Liquidadas/Em Aberto de
// 24/08/2026), não do código.
//
// `evento` é a data que VAI PARA A COLUNA DATA do TSV (`MASTER_OUTPUT §4`) — sai de
// `bets[].fixture.date`, a mais recente quando há várias pernas. `colocacao` sai de
// `conclusionDateUtc`, e o nome desse campo MENTE (ver o bloco de armadilhas abaixo).
// `odd` é a "Cota" do card — a BOOSTADA, quando há boost. `pre` é a riscada.
const ESPERADO = {
  // ── liquidadas ────────────────────────────────────────────────────────────────
  // O W da casa: card "R$50,00 · 1.98 » ⚡2.50 · Ganhos R$125,00". A régua global do W
  // (retorno ÷ stake) dá 125 ÷ 50 = 2,5 e bate com a odd declarada ao centavo.
  "20PGTUNX29": { evento: "20/08/2026 19:00:00", colocacao: "18/08/2026 13:31:45", odd: "2,5",
                  stake: "50,00", status: /^Ganho → W/, tipo: /^Simples$/, esporte: /^Futebol\b/,
                  retorno: "125,00", pre: "1,98" },

  // Múltipla de verdade (`slipType: "Combo"`), 6 pernas, uma delas ANULADA (`Canceled` /
  // `cancellationReason`). O bilhete inteiro é L porque outras perderam — mas a perna nula
  // tem de aparecer, senão ninguém entende a odd.
  "20NK1SSKST": { evento: "28/07/2026 19:40:00", colocacao: "28/07/2026 09:13:21", odd: "133,03",
                  stake: "25,00", status: /^Perdeu → L$/, tipo: /^Múltipla \(6 seleções\)$/,
                  esporte: /^Futebol\b/, pernaNula: true },

  // Perdida com boost: card "R$127,00 · 3.00 » ⚡3.40 · Ganhos -".
  "20PL2W0FBK": { evento: "20/08/2026 21:30:00", colocacao: "20/08/2026 21:00:00", odd: "3,4",
                  stake: "127,00", status: /^Perdeu → L$/, tipo: /^Simples$/, esporte: /^Futebol\b/,
                  pre: "3" },

  // "Múltiplas Aumentadas": a casa empacota TRÊS jogos numa aposta que o payload chama de
  // `Single`. O `fixture.name` é "Quinta-feira" — não é confronto — e os times só existem
  // dentro de `option.name`. Ver armadilha 3.
  "20PGHDRPX3": { evento: "20/08/2026 13:00:00", colocacao: "18/08/2026 08:29:01", odd: "3,2",
                  stake: "28,00", status: /^Perdeu → L$/, tipo: /^Simples$/, esporte: /^Futebol\b/,
                  promo: "Múltiplas Aumentadas" },

  // Freebet (`isFreeBet: true`) — a única da amostra.
  "20P828C463": { evento: "13/08/2026 14:00:00", colocacao: "12/08/2026 07:52:06", odd: "10,5",
                  stake: "20,00", status: /^Perdeu → L$/, tipo: /^Simples$/, esporte: /^Futebol\b/,
                  freebet: true, promo: "Múltiplas Aumentadas" },

  // ── aberta ────────────────────────────────────────────────────────────────────
  // O CORAÇÃO desta casa. `payout: 0` e o potencial mora em campo PRÓPRIO
  // (`maxPayout` = `grossPossibleWinnings` = 1,29 = 0,43 × 3). Ler `maxPayout` como
  // realizado transformaria toda aposta em aberto em vitória fantasma — foi o que a
  // VaideBet levou a produção na s210, lá com um campo só para as duas coisas.
  "20PSJ4C9B6": { evento: "24/08/2026 20:00:00", colocacao: "24/08/2026 18:28:42", odd: "3",
                  stake: "0,43", status: /em aberto/, tipo: /^Simples$/, esporte: /^Futebol\b/,
                  aberta: true, potencial: "1,29", pre: "2,5" },
};

const URL_API = "https://www.sportingbet.bet.br/pt-br/sports/api/mybets/betslips";
const HREF = "https://www.sportingbet.bet.br/pt-br/sports/minhas-apostas/liquidada";

// Corpo que a página emite ao abrir cada aba (colado do Payload real do F12 desta conta).
const CORPO_LIQUIDADAS = '{"index":1,"maxItems":6,"typeFilter":"Settled","pinnedBetslipIds":"","eventIds":[],"useGroupedView":false}';
const CORPO_ABERTAS    = '{"index":1,"maxItems":6,"typeFilter":"Open","pinnedBetslipIds":"","eventIds":[],"useGroupedView":false}';

// Cabeçalhos que a PÁGINA manda (colados do F12, 31/08). Sem o `x-bwin-sports-api` a casa
// devolve 200 com o HTML da SPA — por isso o servidor de mentira abaixo faz o mesmo.
const HEADERS_PAGINA = {
  "x-bwin-sports-api": "prod",
  "cache-control": "no-cache",
  "X-XSRF-TOKEN": "0".repeat(32),
  "x-bwin-browser-url": HREF,
  "X-Device-Type": "desktop_Windows 11",
  "X-From-Product": "host-app",
  "Sports-Api-Version": "SportsAPIv2",
  "Accept": "application/json, text/plain, */*",
  "Content-Type": "application/json",
};

// Pedaço do HTML que a casa devolve — com status 200! — para quem chama sem os cabeçalhos
// do motor. A falha não grita: ela vem 200 e não parseia (medido: 135 KB de HTML).
const HTML_DA_SPA = "<!DOCTYPE html><html><head><title>Sportingbet</title></head><body>SPA</body></html>";

// Servidor de mentira: responde pelo `typeFilter` e pelo `index` do CORPO, como a casa faz.
// A página 1 das liquidadas devolve 5 bilhetes; a 2 devolve VAZIO — que é o único jeito
// desta casa dizer "acabou". Se o inject não parar aí, ele pagina para sempre.
//
// Duas fidelidades que este servidor precisa ter, as duas medidas na casa em 31/08 (s305):
//   • quem chama SEM `x-bwin-sports-api` recebe **HTML com status 200**, não erro;
//   • a PRIMEIRA resposta (a que a página buscou) chega com o CLONE MORTO — a SPA aborta o
//     `fetch` logo após consumir o corpo, e `clone().text()` rejeita com `AbortError`.
//     Sem isto o harness leria o clone de boa vontade e um inject que dependesse da leitura
//     passiva passaria verde, que é exatamente o defeito que travou dois testers.
function servidor() {
  const liquidadas = fixture("sportingbet.settled.json");
  const abertas = fixture("sportingbet.open.json");
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

// O cenário que derrubou a casa em produção: a página NÃO faz requisição nenhuma (carga
// direta de Minhas Apostas vem renderizada pelo servidor) e o operador roda o robô.
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
    const { ultima, pedidos, cabecalhos } = await umClique(corpo);
    testes++;
    if (!ultima) { falhas.push(`${rotulo}: o inject não emitiu nenhuma mensagem`); continue; }
    if (!ultima.hook) falhas.push(`${rotulo}: não sinalizou 'hook' — o autodiagnóstico fica cego`);
    if (typeof ultima.respostas !== "number" || ultima.respostas < 1)
      falhas.push(`${rotulo}: 'respostas' não reportado — não separa "não injetei" de "endpoint mudou"`);
    if (!ultima.fim) falhas.push(`${rotulo}: não sinalizou 'fim' — o robô esperaria o teto`);

    const bets = ultima.bets || [];
    if (bets.length !== 6) falhas.push(`${rotulo}: esperava 6 bilhetes (5 liquidados + 1 aberto), vieram ${bets.length}`);

    // As DUAS abas têm de ser pedidas, não importa qual o operador abriu.
    const pediu = (f) => pedidos.some((b) => { try { return JSON.parse(b).typeFilter === f; } catch (e) { return false; } });
    if (!pediu("Settled")) falhas.push(`${rotulo}: nunca pediu a aba Liquidadas`);
    if (!pediu("Open")) falhas.push(`${rotulo}: nunca pediu a aba Em Aberto — aposta viva sumiria do lote`);

    // Paginação ativa: `index` é PÁGINA. Sem avançar, o lote pararia nos primeiros da aba.
    const p2 = pedidos.find((b) => { try { return Number(JSON.parse(b).index) === 2; } catch (e) { return false; } });
    if (!p2) falhas.push(`${rotulo}: nenhuma requisição pediu index 2 — a paginação não avançou`);

    // Todo pedido tem de ser POST com o corpo no formato aprendido (GET volta HTML).
    for (const b of pedidos) {
      let o = null; try { o = JSON.parse(b); } catch (e) { falhas.push(`${rotulo}: corpo não é JSON: ${b.slice(0, 60)}`); continue; }
      if (typeof o.maxItems !== "number" || o.maxItems < 1) falhas.push(`${rotulo}: maxItems corrompido → ${b}`);
      if (!("useGroupedView" in o)) falhas.push(`${rotulo}: o corpo perdeu campos do formato real → ${b}`);
    }

    // Todo pedido tem de levar o cabeçalho do motor. Sem ele a casa responde 200 com o HTML
    // da SPA — o replay "funciona", o `forward` descarta e o lote volta vazio sem erro nenhum.
    const semMotor = cabecalhos.filter((h) => !Object.keys(h || {}).some((k) => String(k).toLowerCase() === "x-bwin-sports-api"));
    if (semMotor.length) falhas.push(`${rotulo}: ${semMotor.length} requisição(ões) sem 'x-bwin-sports-api' — a casa devolveria HTML com status 200`);

    if (!colhido && bets.length) colhido = bets;
  }

  // ── 1b. ARRANQUE A FRIO: a página não fez requisição nenhuma ──────────────────
  // Este é o cenário real que travou os testers em 31/08 (s305) e que o caso antigo não
  // exercia: carga direta de Minhas Apostas vem do SERVIDOR, sem nenhuma chamada de API.
  // O inject antigo dependia de aprender uma requisição (`if (!reqCtx) return`) e entregava
  // ZERO aqui, com hook ATIVO e respostas 0 — indistinguível de "endpoint mudou".
  {
    const { ultima, pedidos, cabecalhos } = await semRequisicaoDaPagina();
    testes++;
    if (!ultima) falhas.push("a frio: o inject não emitiu nenhuma mensagem");
    else {
      if (!ultima.hook) falhas.push("a frio: não sinalizou 'hook'");
      if (!(ultima.respostas >= 1)) falhas.push("a frio: 'respostas' ficou em 0 — o replay não arrancou sem requisição aprendida");
      if (!ultima.fim) falhas.push("a frio: não sinalizou 'fim' — o robô esperaria o teto de inatividade");
      const n = (ultima.bets || []).length;
      if (n !== 6) falhas.push(`a frio: esperava 6 bilhetes, vieram ${n} — sem requisição da página o lote precisa sair igual`);
    }
    testes++;
    // As duas abas, e com os cabeçalhos do motor montados pelo próprio inject.
    const pediu = (f) => pedidos.some((b) => { try { return JSON.parse(b).typeFilter === f; } catch (e) { return false; } });
    if (!pediu("Settled") || !pediu("Open")) falhas.push("a frio: alguma aba não foi pedida");
    if (!cabecalhos.length || !cabecalhos.every((h) => Object.keys(h || {}).some((k) => String(k).toLowerCase() === "x-bwin-sports-api")))
      falhas.push("a frio: requisição sem 'x-bwin-sports-api' — a casa devolveria HTML com status 200");
  }

  if (!colhido) return { falhas: falhas.concat(["nenhum bilhete colhido — o resto do caso não roda"]), testes };

  // ── 2. Leitura bilhete a bilhete, contra o card DA CASA ───────────────────────
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

    // ⚠️ ARMADILHA 1: `conclusionDateUtc` é a COLOCAÇÃO, apesar do nome. Prova: o bilhete
    // aberto foi colocado 24/08 18:28 e o jogo é 24/08 20:00 — uma "conclusão" não pode
    // ser anterior ao evento. Quem ler pelo nome grava liquidação onde é colocação.
    const colocacao = linha(txt, "Data (colocação):");
    if (colocacao !== e.colocacao) falhas.push(`${id}: colocação esperada ${e.colocacao}, veio "${colocacao}"`);

    const stake = linha(txt, "Stake:");
    if (stake !== "R$ " + e.stake) falhas.push(`${id}: stake esperada R$ ${e.stake}, veio "${stake}"`);

    const status = linha(txt, "Status:");
    if (!e.status.test(status)) falhas.push(`${id}: status "${status}"`);

    // Enum CRU da casa — é ele que a CASA_SPORTINGBET.md traduz. Sem isso um estado novo
    // (a anulada que a Esportiva escondeu por meses) viraria chute a partir do dinheiro.
    if (!/state=\w+/.test(linha(txt, "Status (API):")))
      falhas.push(`${id}: faltou o enum cru na linha "Status (API):"`);

    const odd = linha(txt, "Odd:").split(" ")[0];
    if (odd !== e.odd) falhas.push(`${id}: odd esperada ${e.odd}, veio "${odd}"`);

    const tipo = linha(txt, "Tipo:");
    if (!e.tipo.test(tipo)) falhas.push(`${id}: tipo "${tipo}"`);

    // ⚠️ ARMADILHA 2: `sport.name` vem "Beisebol", que é SINÔNIMO DE ENTRADA. O valor
    // oficial do MASTER_ESPORTES é "Baseball", e a IA copia o rótulo verbatim — foi assim
    // que a VaideBet gravou 3 linhas "Beisebol" + 1 "Baseball" no banco (s210), duas
    // grafias do mesmo esporte contadas como esportes diferentes.
    const esp = linha(txt, "Esporte:");
    if (!e.esporte.test(esp)) falhas.push(`${id}: esporte "${esp}" não é o valor oficial do MASTER_ESPORTES`);

    if (e.pre) {
      const marca = txt.split("\n").find((l) => l.startsWith("Marcação da casa: odd turbinada")) || "";
      if (!marca) falhas.push(`${id}: bilhete turbinado sem a marcação de boost — a IA não saberia que o riscado do card não é a odd`);
      else {
        const m = /antes do boost ([\d,]+)/.exec(marca);
        if ((m ? m[1] : "") !== e.pre) falhas.push(`${id}: odd pré-boost esperada ${e.pre}, veio "${m ? m[1] : ""}"`);
      }
    }

    if (e.retorno) {
      const r = linha(txt, "Retorno:");
      if (r !== "R$ " + e.retorno) falhas.push(`${id}: retorno esperado R$ ${e.retorno}, veio "${r}"`);
      const n = Number(e.odd.replace(",", ".")), st = Number(e.stake.replace(".", "").replace(",", ".")),
            ret = Number(e.retorno.replace(".", "").replace(",", "."));
      if (!(Math.abs(n * st - ret) <= 0.01)) falhas.push(`${id}: odd ${e.odd} × stake ${e.stake} não explica o retorno ${e.retorno} do card`);
    }

    if (e.freebet && !/aposta gr[áa]tis|freebet/i.test(txt))
      falhas.push(`${id}: freebet (isFreeBet) não foi marcada — o stake não saiu do bolso e o P/L muda`);

    // ⚠️ ARMADILHA 3: "BIG ODD" / "Múltiplas Aumentadas" chegam em `market.name`, mas são
    // o nome da PROMOÇÃO, não o mercado. O mercado real vive em `option.name` ("Kevin
    // Viveros tem 2 ou mais chutes no gol"). Copiar `market.name` jogaria todo bilhete
    // turbinado em `Outros` — e turbinada aqui é o padrão, não a exceção.
    if (e.promo) {
      if (!txt.includes(e.promo)) falhas.push(`${id}: o rótulo de promoção "${e.promo}" sumiu do bloco`);
      const mercado = linha(txt, "Mercado:");
      if (mercado === e.promo) falhas.push(`${id}: "Mercado:" recebeu o nome da PROMOÇÃO (${e.promo}) — o mercado real está em option.name`);
    }

    // Perna anulada: existe `state:"Canceled"` + `cancellationReason` no payload (achado
    // da s289, antes de qualquer bilhete inteiro anulado aparecer).
    if (e.pernaNula && !/anulad|nula/i.test(txt))
      falhas.push(`${id}: a perna Canceled não aparece no bloco — a odd do bilhete fica inexplicável`);

    if (e.aberta) {
      if (/→ [WLV]\b/.test(status)) falhas.push(`${id}: aberta recebeu código de resultado — proibido`);
      if (/Ganho → W/.test(txt)) falhas.push(`${id}: ABERTA virou vitória — maxPayout foi lido como retorno realizado`);
      const pot = linha(txt, "Retorno potencial:");
      if (pot !== "R$ " + e.potencial) falhas.push(`${id}: retorno potencial esperado R$ ${e.potencial}, veio "${pot}"`);
      if (linha(txt, "Retorno:")) falhas.push(`${id}: aberta emitiu linha "Retorno:" — só potencial é permitido`);
    }
  }

  // ── 3. CONTROLE NEGATIVO ──────────────────────────────────────────────────────
  // Um caso que passa verde de primeira não é evidência. Aqui provamos que as asserções
  // centrais têm dente.
  {
    const aberta = JSON.parse(fixture("sportingbet.open.json")).betslips[0];
    testes++;
    // (a) o MESMO bilhete, com state Won e payout preenchido, TEM de virar W com "Retorno:".
    //     Se sair igual ao aberto, a asserção da aberta não estava provando nada.
    const comoW = fmt({ ...aberta, state: "Won",
                        payout: { currency: "BRL", value: 1.29 },
                        bets: aberta.bets.map((x) => ({ ...x, state: "Won", outcome: "Ganhas" })) });
    if (!/Ganho → W/.test(comoW) || !linha(comoW, "Retorno:"))
      falhas.push("controle negativo: o bilhete com state=Won não virou W com 'Retorno:' — o teste da ABERTA era vácuo");

    testes++;
    // (b) estado fora de {Open,Won,Lost,Canceled} sobe CRU e marcado — nunca vira W/L pelo
    //     dinheiro. É a lição da Esportiva (s285): enum não traduzido que liquida por
    //     dedução mente, e enum não traduzido que trava em silêncio some.
    const inedito = fmt({ ...aberta, state: "PartiallyCashedOut" });
    if (!/a conferir/.test(inedito)) falhas.push("estado desconhecido não foi marcado 'a conferir' — vira chute");
    if (/Ganho → W|Perdeu → L/.test(inedito)) falhas.push("estado desconhecido foi convertido em resultado — proibido");

    testes++;
    // (c) O ESPORTE tem de sair do MAPA DE ID, nunca de `sport.name`.
    //
    // Sem este caso o teste do esporte é VÁCUO, e isso foi provado por mutação, não
    // suposto: toda a amostra de `ESPERADO` é futebol (id 4), onde o mapa e o `sport.name`
    // dizem a mesma coisa — trocar o formatador para copiar `sport.name` (que é exatamente
    // o defeito que a VaideBet levou a produção na s210) passava VERDE.
    //
    // O único esporte da conta onde os dois divergem está nas pernas do combo: id 23, que
    // a casa chama de "Beisebol" (sinônimo de entrada) e o MASTER_ESPORTES chama de
    // "Baseball" (valor oficial, o que a IA copia para a coluna Esporte).
    const combo = JSON.parse(fixture("sportingbet.settled.json")).betslips.find((b) => b.slipType === "Combo");
    const pernaMLB = (combo.bets || []).find((x) => x.sport && x.sport.id === 23);
    if (!pernaMLB) falhas.push("a fixture perdeu a perna de beisebol — o teste do rótulo oficial ficou sem amostra");
    else {
      const espB = linha(fmt({ ...combo, slipType: "Single", bets: [pernaMLB] }), "Esporte:");
      if (!/^Baseball\b/.test(espB))
        falhas.push(`esporte do sportId 23 saiu "${espB}" — tem de ser o valor OFICIAL "Baseball", nunca o "Beisebol" da casa`);
    }
  }

  return { falhas, testes };
}
