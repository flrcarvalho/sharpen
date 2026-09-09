// Peça compartilhada dos casos das casas do motor **Rogue** — Betão, R7 e 7Games (s335).
//
// Vive FORA de `casos/` de propósito: o `run.mjs` trata todo `casos/*.mjs` como um caso e
// exige `rodar()`. Aqui é biblioteca, não caso.
//
// AS TRÊS SÃO ESPELHO DE VERDADE, e isso foi medido, não deduzido: mesma stack (Next.js),
// mesmo conjunto de hosts, e o mesmo mapa de endpoints extraído dos bundles das três —
// `/api/sportsbook/rogue/v1/…` servido do PRÓPRIO domínio da casa, como a Novibet. Não é
// Altenar, não é BetBy, não é Kambi, não é BetConstruct: motor novo para nós.
//
// Por isso existe UM inject (`rg_inject.js`) e UM formatador (`formatTicketRG`) para as três,
// no padrão das 5 casas Altenar. Cada caso traz a fixture da sua conta e as suas armadilhas;
// o andaime é este arquivo.
//
// ── O CONTRATO, medido ao vivo nas três (recon s335) ────────────────────────────────────
//
//   GET /api/sportsbook/rogue/v1/betsreporting/purchases
//       ?status=all&take=<1..100>&skip=<n>&locale=br-pt&fromDate=<ISO>&toDate=<ISO>
//       header: authorization: Bearer <JWT da sessão>   ← cookie NÃO basta (403 medido)
//   → {"Purchases":[…], "PurchasesCount": <total da janela>}
//
//   • `take` tem TETO DE 100 e a casa diz o limite em vez de truncar calada:
//     `{"ErrorCode":2003,"ErrorMessages":[{"Message":"Value should be in the range [1-100].",
//       "ParameterName":"take","ProvidedValue":200}]}` — medido pedindo 200.
//   • `PurchasesCount` é o total da JANELA → é o fim AUTORITATIVO da paginação por `skip`.
//   • `status=all` traz aberta e liquidada na mesma chamada.
//
// ── POR QUE O REPLAY EXISTE (não é paginação) ───────────────────────────────────────────
//
// O passivo É possível aqui (o `clone().text()` resolve, ao contrário de Novibet/Pitaco/
// SportingBet), mas seria quase inútil sozinho: **a tela abre em "Últ. 24 horas" com
// `take=10`**. É a estreiteza da Novibet outra vez. No dia do recon, o filtro de 30 dias do
// Betão devolvia `{"Purchases":[],"PurchasesCount":0}` numa conta que tem 9 bilhetes. Quem
// alarga a janela é o replay.
//
// ── AS ARMADILHAS DO DADO (medidas em 27 de 27 bilhetes das três contas) ────────────────
//
//   • `Gain` É SEMPRE O RETORNO POTENCIAL — vale `stake × odd` em 100% dos casos, inclusive
//     em PERDIDA e em ABERTA. O retorno REALIZADO é `CurrentBetBalance`. Quem ler o campo
//     óbvio marca toda perda como ganho: é a vitória fantasma do `totalWin` da VaideBet
//     (s210) e do `finalFinancials.payout` da Novibet (s271), com o terceiro nome de campo.
//
//   • O STATUS SE PROVA PELO DINHEIRO, e a prova fechou em 27/27:
//         BetStatusId 0 → CurrentBetBalance 0  e SEM `Result`   → ABERTA
//         BetStatusId 1 → CurrentBetBalance 0                   → L
//         BetStatusId 2 → CurrentBetBalance = stake × odd       → W
//         BetStatusId 4 → CurrentBetBalance = stake exato       → V  (Result: "")
//     `PurchaseStatusId` acompanha `BetStatusId` em 27/27, mas os dois sobem CRUS na linha
//     `Status (API):` — enum novo tem de ser reconhecível, nunca chutado.
//
//   • ODD ZERO NÃO EXISTE AQUI, e é por isso que a odd de L/V/aberta sai de `BetClientOdds`
//     e NUNCA do dinheiro: em L o retorno é 0 e `retorno ÷ stake` daria **odd 0** — o zero
//     que transforma um bilhete em −1u (CLAUDE.md, "Zero não é ausência"). Em V o retorno é
//     a própria stake e a divisão daria 1,00, apagando a odd real do bilhete.
//
//   • Em ABERTA os campos `Result` / `FullTimeResult` / `SettlementResult` **não vêm**
//     (ausentes, não vazios) — separador limpo entre aberta e resolvida. Em V o `Result`
//     vem como string VAZIA e os outros dois somem: são estados distintos e o formatador
//     não pode confundi-los.
//
// ── O QUE ESTA AMOSTRA NÃO COBRE (as três contas somam 27 bilhetes, TODOS simples) ──────
//
// Não há múltipla, sistema, cashout, freebet nem bet builder: `BetTypeId` é 1, `ComboSize`
// 0 e `NumberOfLines` 1 em 27 de 27, e `AdditionalTickets` vem vazio em todos. Os campos
// existem no payload e os endpoints `/v1/cashout/*` existem no bundle, mas **nada disso foi
// exercido**. O formatador trata múltipla pelo número de seleções e deixa o resto subir cru;
// quando aparecer a primeira, a fixture volta para cá.
import { rodarInject, carregarContent, fixture, linha } from "./sandbox.mjs";

export const CAMINHO = "/api/sportsbook/rogue/v1/betsreporting/purchases";

// Os headers que a página manda. São dois — `accept` e o `authorization: Bearer`. O Bearer é
// da SESSÃO e não vive em cookie nem em localStorage (medido: o token de 759 chars não estava
// em nenhum dos dois), então o inject tem de APRENDER de uma requisição real. Sem ele, a
// mesma URL com o cookie da sessão responde **403** — medido no Betão.
export const HEADERS = {
  accept: "application/json, text/plain, */*",
  authorization: "Bearer eyJhbGciOiJIUzI1NiJ9.HARNESS.TOKEN-FALSO-SO-PARA-O-REPLAY",
};

/** A query que a TELA envia: 24h/30d e `take=10`. É a estreiteza que obriga o replay. */
export function queryDaTela() {
  return new URLSearchParams({
    status: "all", take: "10", skip: "0", locale: "br-pt",
    fromDate: "2026-08-10T14:52:00.000Z", toDate: "2026-09-09T14:52:00.000Z",
  }).toString();
}

/**
 * Roda o `rg_inject.js` contra uma fixture, fatiando-a em páginas MENORES que o `take` que o
 * inject pede. É assim que se prova que o `skip` avança pelo que VOLTOU, e não pelo pedido —
 * a lição que a Pitaco (s270) cobrou caro, onde paginar PERDIA bilhete.
 *
 * @param {object} cfg
 * @param {string} cfg.host      host da casa (ex.: "betao.bet.br")
 * @param {string} cfg.fixture   nome do arquivo em fixtures/
 * @param {number} [cfg.pagina=4] tamanho da página que o sandbox devolve
 */
export async function rodarRogue(cfg) {
  const dados = JSON.parse(fixture(cfg.fixture));
  const lista = dados.Purchases;
  const PAG = cfg.pagina || 4;
  const base = `https://${cfg.host}${CAMINHO}`;
  const pedidos = [];

  const responder = (url) => {
    const u = String(url);
    if (!u.includes(CAMINHO)) return null;
    const q = new URL(u, `https://${cfg.host}`).searchParams;
    const skip = parseInt(q.get("skip") || "0", 10);
    const take = parseInt(q.get("take") || "10", 10);
    pedidos.push({
      skip, take, status: q.get("status"),
      fromDate: q.get("fromDate"), toDate: q.get("toDate"), locale: q.get("locale"),
    });
    // A casa RECUSA take > 100 — e recusa com corpo de erro, status 200 nenhum. Reproduzir
    // isso aqui é o que impede um inject de "otimizar" pedindo 500 e receber vazio calado.
    if (take > 100 || take < 1) {
      return JSON.stringify({
        ErrorCode: 2003,
        ErrorMessages: [{ Message: "Value should be in the range [1-100].",
                          ParameterName: "take", ProvidedValue: take }],
      });
    }
    return JSON.stringify({
      Purchases: lista.slice(skip, skip + Math.min(take, PAG)),
      PurchasesCount: lista.length,
    });
  };

  const { ultima, urls } = await rodarInject({
    inject: "rg_inject.js",
    href: `https://${cfg.host}/account/sports-history`,
    urlInicial: `${base}?${queryDaTela()}`,
    optsInicial: { method: "GET", headers: HEADERS },
    pedido: "__sharpenupRGReq",
    responder,
    ms: 900,
  });

  return { ultima, urls, pedidos, total: lista.length };
}

/**
 * As checagens que valem para as TRÊS casas: heartbeat, replay que alarga, paginação sem
 * perder nem duplicar, e o bloco de cada bilhete contra o que a casa mostra.
 *
 * @param {object} r          o retorno de `rodarRogue`
 * @param {object} ESPERADO   ref → {stake, odd, st, col, ev}
 */
export function conferir(r, ESPERADO) {
  const falhas = [];
  const { ultima, urls, pedidos, total } = r;
  if (!ultima) return { falhas: ["o inject não emitiu nenhuma mensagem"], testes: 0 };

  // ── heartbeat (sem isto, "inject não carregou" e "casa mudou" viram o mesmo silêncio) ──
  if (!ultima.hook) falhas.push("o inject não emitiu `hook:true` (autodiagnóstico cego)");
  if (typeof ultima.respostas !== "number" || ultima.respostas < 1) {
    falhas.push(`\`respostas\` ausente ou zerado (veio ${ultima.respostas})`);
  }
  if (!ultima.fim) falhas.push("o inject não sinalizou `fim` (o robô esperaria o teto de inatividade)");
  if (urls.length < 2) falhas.push(`replay não repaginou (só ${urls.length} requisição(ões))`);

  // ── o replay tem de ALARGAR a janela; é a razão de ele existir ──
  const doReplay = pedidos.filter((p) => p.take > 10);
  if (!doReplay.length) {
    falhas.push("o replay nunca pediu mais que os 10 da tela — a captura pegaria uma fatia mínima");
  } else {
    const p = doReplay[0];
    if (p.take !== 100) falhas.push(`replay pediu take=${p.take}; o teto medido da casa é 100`);
    if (p.status !== "all") {
      falhas.push(`replay pediu status=${p.status}; sem \`all\` as ABERTAS não vêm`);
    }
    const dias = (Date.parse(p.toDate) - Date.parse(p.fromDate)) / 86400000;
    if (!(dias > 300)) {
      falhas.push(`replay pediu janela de ${Math.round(dias)} dia(s) — a tela já pede 30 e a ` +
                  "conta tem bilhete mais velho que isso; sem alargar, a captura nasce curta");
    }
    if (!p.locale) falhas.push("o replay perdeu o `locale` da requisição original");
  }
  // Nenhum pedido pode estourar o teto: a casa devolve corpo de ERRO, não lista.
  const estourou = pedidos.find((p) => p.take > 100);
  if (estourou) falhas.push(`o inject pediu take=${estourou.take}, acima do teto de 100 da casa`);

  // ── paginação: sem perder nem duplicar ──
  const bilhetes = ultima.bilhetes || [];
  if (bilhetes.length !== total) {
    falhas.push(`esperava ${total} bilhetes normalizados, vieram ${bilhetes.length} ` +
                "(a página do sandbox é menor que o `take` — o `skip` tem de avançar pelo que VOLTOU)");
  }
  const refs = bilhetes.map((b) => b.ref);
  if (new Set(refs).size !== refs.length) falhas.push("o inject devolveu códigos repetidos");

  // ── os blocos que a IA vai ler ──
  const fmt = carregarContent().pegar("formatTicketRG");
  let testes = 0;
  const porRef = new Map();
  for (const b of bilhetes) {
    const txt = fmt(b);
    porRef.set(b.ref, txt);
    const e = ESPERADO[b.ref];
    if (!e) continue;
    testes++;
    if (!txt.startsWith(`[Código: ${b.ref}]`)) falhas.push(`${b.ref}: marcador [Código:] ausente/errado`);

    const stake = linha(txt, "Stake:");
    if (stake !== e.stake) falhas.push(`${b.ref}: stake esperado ${e.stake}, veio "${stake}"`);

    const odd = linha(txt, "Odd:");
    if (odd !== e.odd && odd !== `${e.odd} (= Retorno ÷ Stake)`) {
      falhas.push(`${b.ref}: odd esperada ${e.odd}, veio "${odd}"`);
    }
    const col = linha(txt, "Data (colocação):");
    if (col !== e.col) falhas.push(`${b.ref}: data de colocação esperada ${e.col}, veio "${col}"`);
    if (e.ev) {
      const ev = linha(txt, "Data (evento mais recente):");
      if (ev !== e.ev) falhas.push(`${b.ref}: data de evento esperada ${e.ev}, veio "${ev}"`);
    }
    // O enum CRU tem de subir: é ele que a CASA_*.md traduz e o que permite reconhecer um
    // status novo (cashout, meia-liquidação) em vez de chutá-lo.
    const api = linha(txt, "Status (API):");
    if (!api.includes(`BetStatusId=${e.st}`)) {
      falhas.push(`${b.ref}: linha "Status (API):" não trouxe BetStatusId=${e.st} ("${api}")`);
    }

    const status = linha(txt, "Status:");
    const retorno = linha(txt, "Retorno:");
    const potencial = linha(txt, "Retorno potencial:");
    if (e.st === 0) {
      if (!/^Em aberto/.test(status)) falhas.push(`${b.ref}: aberta com status "${status}"`);
      if (retorno) falhas.push(`${b.ref}: ABERTA emitiu "Retorno:" — a IA liquidaria a aposta`);
      if (!/POTENCIAL/.test(potencial)) falhas.push(`${b.ref}: aberta sem o aviso de retorno POTENCIAL`);
    } else if (e.st === 1) {
      if (!/^Perdeu → L$/.test(status)) falhas.push(`${b.ref}: perdida com status "${status}"`);
      if (retorno !== "R$ 0,00") falhas.push(`${b.ref}: retorno de perdida deveria ser R$ 0,00, veio "${retorno}"`);
    } else if (e.st === 2) {
      if (!/^Ganhou → W$/.test(status)) falhas.push(`${b.ref}: ganha com status "${status}"`);
      if (!/^R\$ /.test(retorno)) falhas.push(`${b.ref}: ganha sem linha "Retorno:" ("${retorno}")`);
    } else if (e.st === 4) {
      if (!/^Anulada → V$/.test(status)) falhas.push(`${b.ref}: anulada com status "${status}"`);
    }
  }

  // ── a armadilha central: `Gain` é POTENCIAL, sempre ──
  // Um formatador que o emitisse como retorno marcaria toda perda como ganho. A checagem é
  // pelo NÚMERO, não pelo rótulo: em toda linha resolvida-não-ganha o valor de `stake × odd`
  // não pode aparecer como dinheiro recebido.
  for (const b of (ultima.bilhetes || [])) {
    const txt = porRef.get(b.ref);
    if (!txt) continue;
    const st = b.statusBilhete;
    if (st !== 1 && st !== 4) continue;
    const pot = Number(b.potencial);
    if (!isFinite(pot) || pot <= 0) continue;
    const alvo = pot.toFixed(2).replace(".", ",");
    const linhaRetorno = linha(txt, "Retorno:");
    if (linhaRetorno && linhaRetorno.includes(alvo)) {
      falhas.push(`${b.ref}: o retorno POTENCIAL (${alvo}) vazou para a linha "Retorno:" de um ` +
                  "bilhete que NÃO ganhou — é a vitória fantasma da VaideBet (s210)");
    }
  }

  return { falhas, testes, porRef };
}

/**
 * O BEARER EXPIRA — e por isso o inject tem de SOBRESCREVER o contexto aprendido, sempre.
 *
 * Medido ao vivo (s335): um token capturado da página e reusado ~1h depois responde **401**.
 * A primeira versão deste inject guardava só a PRIMEIRA requisição (`if (reqCtx) return`), o
 * que fazia o contexto envelhecer junto com a aba: numa aba aberta desde a manhã, o robô
 * sairia com token vencido e a captura voltaria vazia. Pior, 401 e "endpoint mudou" leem
 * igual no painel.
 *
 * O caso reproduz a sequência real: a página faz uma requisição com token VELHO, depois
 * outra com token NOVO (é o que acontece a cada clique no filtro de período), e só então o
 * robô arranca. O sandbox recusa o token velho. Um inject que não sobrescreva entrega ZERO.
 *
 * Espelha a montagem da Jonbet, onde a 1ª chamada sai sem `Authorization` e toma 401.
 */
export async function conferirTokenRenovado(host, nomeFixture) {
  const dados = JSON.parse(fixture(nomeFixture));
  const lista = dados.Purchases;
  const base = `https://${host}${CAMINHO}`;
  const VELHO = "Bearer TOKEN-VENCIDO";
  const NOVO = "Bearer TOKEN-FRESCO";

  const responder = (url, opts) => {
    const u = String(url);
    if (!u.includes(CAMINHO)) return null;
    const h = (opts && opts.headers) || {};
    const auth = h.authorization || h.Authorization || "";
    // SÓ o token fresco passa. Token vencido e requisição SEM `authorization` são as duas
    // recusadas — e é assim de propósito: `null` vira 404 no sandbox, e o inject trata todo
    // `!r.ok` como parada do replay, que é o que ele vê diante do 401/403 reais.
    if (auth !== NOVO) return null;
    const q = new URL(u, `https://${host}`).searchParams;
    const skip = parseInt(q.get("skip") || "0", 10);
    const take = parseInt(q.get("take") || "10", 10);
    return JSON.stringify({
      Purchases: lista.slice(skip, skip + Math.min(take, 4)),
      PurchasesCount: lista.length,
    });
  };

  const { ultima } = await rodarInject({
    inject: "rg_inject.js",
    href: `https://${host}/account/sports-history`,
    urlInicial: `${base}?${queryDaTela()}`,
    optsInicial: { method: "GET", headers: { accept: "application/json", authorization: VELHO } },
    // A página refaz a busca (clique num filtro) e agora manda o token renovado. Logo
    // depois vem uma requisição SEM `authorization` — a página dispara uma dessas ao
    // montar, e aceitá-la SUBSTITUIRIA o contexto bom por um cego. As duas coisas têm de
    // valer ao mesmo tempo: sobrescrever com token melhor, nunca com token nenhum.
    urlsExtra: [
      {
        url: `${base}?${queryDaTela()}`,
        opts: { method: "GET", headers: { accept: "application/json", authorization: NOVO } },
      },
      {
        url: `${base}?${queryDaTela()}`,
        opts: { method: "GET", headers: { accept: "application/json" } },
      },
    ],
    pedido: "__sharpenupRGReq",
    responder,
    ms: 900,
  });

  const falhas = [];
  const n = (ultima && ultima.bilhetes || []).length;
  if (n !== lista.length) {
    falhas.push(`token renovado: esperava ${lista.length} bilhetes usando o Bearer NOVO, vieram ` +
                `${n} — o inject ficou com o token da PRIMEIRA requisição, que a casa já recusa ` +
                "(o Bearer desta casa expira; medido 401 ao vivo na s335)");
  }
  return falhas;
}

/**
 * A regra "Data = a perna MAIS RECENTE" (MASTER_OUTPUT §4), exercida com bilhete SINTÉTICO.
 *
 * Por que sintético, contra a regra normal do harness de só esperar o que a casa mostra: as
 * três contas somam 27 bilhetes e **todos são simples**, de uma perna só. Com uma perna, "a
 * mais recente" e "a primeira" são o mesmo valor — a mutação que troca `t > melhor` por
 * "pega a primeira" passa VERDE em todas as fixtures reais. É o falso verde do tipo 2 do
 * CLAUDE.md, medido: 9 de 10 mutações detectadas, e a que escapou foi exatamente esta.
 *
 * O que se testa aqui NÃO é dado da casa — é uma regra NOSSA, do MASTER. Por isso o bilhete
 * pode ser montado à mão sem inventar comportamento de casa nenhuma: as duas pernas usam
 * datas quaisquer, e o único fato afirmado é qual das duas o formatador tem de escolher.
 *
 * As pernas vêm em ordem DECRESCENTE de data de propósito — assim "pegar a primeira" dá o
 * valor ERRADO, e não o certo por acidente. (Ordem crescente faria a mutação acertar sem
 * regra nenhuma, que é a outra metade da armadilha do dado sintético.)
 *
 * Quando a primeira múltipla real aparecer numa das contas, ela vira fixture e este teste
 * pode ir embora.
 */
export function conferirDataEvento() {
  const falhas = [];
  const fmt = carregarContent().pegar("formatTicketRG");
  const perna = (inicio) => ({
    selecao: "Seleção", mercado: "Vencedor", jogo: "A vs B", liga: "Liga", esporte: "Futebol",
    odd: 1.5, oddTexto: "1.50", inicio: inicio, pontos: null, resultado: null,
    aoVivo: false, tipoEvento: 0, placar1: 0, placar2: 0,
  });
  const b = {
    ref: "SINTETICO-DATA", colocada: "2026-09-01T12:00:00.000Z",
    atualizada: "2026-09-01T12:00:00.000Z",
    statusBilhete: 0, statusCompra: 0, tipo: "Multiple", linhas: 1,
    stake: 10, stakeTexto: "10", stakeLinha: 10, odd: 2.25, oddTexto: "2.25",
    potencial: 22.5, retorno: 0,
    // decrescente: a MAIS RECENTE (dia 20) é a ÚLTIMA da lista
    sels: [perna("2026-09-10T18:00:00.000Z"), perna("2026-09-20T18:00:00.000Z")],
  };
  const txt = fmt(b);
  const ev = linha(txt, "Data (evento mais recente):");
  if (ev !== "20/09/2026 15:00:00") {
    falhas.push("múltipla sintética: a data do evento deveria ser a da perna MAIS RECENTE " +
                `(20/09/2026 15:00:00), veio "${ev}" — MASTER_OUTPUT §4`);
  }
  if (!/Tipo: Múltipla \(2 seleções\)/.test(txt)) {
    falhas.push(`múltipla sintética: tipo não foi reconhecido ("${linha(txt, "Tipo:")}")`);
  }
  return falhas;
}
