// Mundo MAIN (Cloudbet — plataforma própria, só o sportsbook): aprende os cabeçalhos de
// autenticação que a página manda e BUSCA a conta ela mesma, repassando ao content script.
//
//   GET /sports-betting/v4/bets/positions?limit=999&locale=en&offset=N&status=ACCEPTED
//                                                  (abertas; posições, sem odd e sem ID da tela)
//   GET /sports-betting/v4/bets/positions?…&status=COMPLETED&from=<iso>&to=<iso>
//                                                  (liquidadas, por janela de no máximo 1 ano)
//   → { hasNext, items:[ {positionId, positionStatus, positionTime, type, positions:[…]} ] }
//   GET /sports-betting/v4/bets/positions/{betLegIdentifier}?currency=<moeda>&locale=en&limit=100&offset=N
//   → { bets:[ {uuid, state, result, stake, price, returnAmount, createTime, …} ] }
//   GET /sports-api/v6/sports/events/{eventId}?locale=en&markets=x
//   → { name, sport, competition, cutoffTime, status, … }
//
// PLATAFORMA PRÓPRIA (recon 10/11/2026, s442, conta em USDT). Front Next.js, API no MESMO
// domínio. Nenhuma outra casa do sistema fala `/sports-betting/v4/`.
//
// AUTH: o cookie NÃO basta (HTTP 401). A página manda `authorization` (JWT),
// `x-cloudbet-metadata` e `x-cloudbet-version` em toda chamada de `/sports-api/` e
// `/sports-betting/`, e faz essas chamadas sozinha segundos depois de carregar (medido: 5 em
// `/sports-api/v6` sem o usuário tocar em nada). O inject aprende os três de uma chamada real e
// os guarda SÓ aqui: a mensagem para o content leva `semToken`, nunca o valor.
//
// O QUE FOI MEDIDO na API:
//   • a LISTA não traz odd útil (`aggregate.odds` é 0 em 3 de 4 perdidas e vem RECALCULADA sem
//     a perna anulada na outra), nem o ID que a tela mostra, nem a colocação. Tudo isso está no
//     DETALHE da posição: `bets[].uuid` (o "ID:" do card), `price` (a odd da aposta), `stake`,
//     `returnAmount`, `createTime`, `completeTime`, `result`. Daí uma chamada por posição.
//   • ⚠ o DETALHE só responde na moeda NATIVA da aposta: `currency=USDT` traz a aposta;
//     `BTC`, `BRL` ou sem o parâmetro devolvem `{"bets":[]}`. A moeda nativa são as chaves de
//     `positions[].portfolio`. A lista, ao contrário, CONVERTE o dinheiro para a moeda pedida
//     (em BTC a stake de 30 USDT vira 0,000402): dinheiro da lista nunca entra no bilhete.
//   • ⚠ `returnAmount` é o LUCRO (−30 na perdida de 30). O retorno é stake + returnAmount.
//   • a janela `from`/`to` filtra pela LIQUIDAÇÃO (`positionTime`), e os dois juntos são
//     obrigatórios: só `to` dá HTTP 400, e mais de um ano também. Sem `status`, só liquidadas.
//   • `limit` vai até 1000 (1001 dá 400); o fim é `hasNext:false` (medido com limit 6: 6, 6, 3).
//
// POSIÇÃO COM VÁRIAS APOSTAS (medido ao vivo em 11/11/2026, s445, 4 dias da conta: 43 posições,
// 290 apostas). Conta limitada aposta de novo, pequeno, nas MESMAS seleções, e a casa junta tudo
// num card só ("Aposta (20 aposta(s)) $40.00"):
//   • o item da lista tem `positions[]`, as SUB-POSIÇÕES. Cada uma é um conjunto de seleções, com
//     `betLegIdentifier` e `betCount`. Na múltipla há uma só e o id dela é o `positionId`; na
//     SIMPLES o item é `type: EVENT` (positionId de 8 dígitos, o jogo) e junta as seleções
//     DIFERENTES daquele jogo, uma sub-posição por seleção.
//   • ⚠ o detalhe é pedido pelo `betLegIdentifier`. Pelo `positionId` de um EVENT ele volta
//     `bets:[]`: a simples SUMIA inteira.
//   • ⚠ o detalhe PAGINA em 20 por padrão, sem `hasNext`: a posição de 35 vinha com 20. `limit`
//     vai até 100 (200 dá 400) e o resto vem por `offset`. Página curta = fim.
//   • as apostas de uma sub-posição têm as MESMAS seleções e o mesmo resultado (46 de 46); a odd
//     varia entre elas (6,94 a 7,58 numa de 6), porque cada uma pegou a odd daquele instante.
//   Por isso a sub-posição de N > 1 apostas vira UM bilhete, como no card: código =
//   `betLegIdentifier`, stake e lucro SOMADOS, odd = Σ(stake × odd) ÷ Σ stake (média ponderada,
//   que é o retorno total ÷ stake total quando ganha). A de 1 aposta segue com o `uuid`. O cru
//   leva os uuids das apostas juntadas (`apostas[]`): é por eles que o servidor tira da base as
//   linhas avulsas de captura anterior, sem duplicar.
//   • a seleção não diz o jogo, o esporte nem o início: vêm do evento (`cutoffTime` = início).
//     Uma chamada por evento distinto; `markets=x` tira os mercados (64 → 45 KB no aberto).
//
// NÃO DECIDE NADA: normaliza e sobe o cru. `state`/`result` sobem como vieram; quem traduz é o
// `formatTicketCB` (content.js) + `casas/CASA_CLOUDBET.md`.
(function () {
  // ── CRU para o servidor (Projeto Ficha Sharpen) ──────────────────────────────────────
  // Por aposta: o `bet` do detalhe, o item da lista de onde ela saiu (nomes de mercado e de
  // seleção só existem ali) e os eventos que as pernas citam. Junto, o cru basta para a Ficha.
  const _cruDe = new Map();                    // uuid → cru
  function _crus(lista) {
    const out = [];
    try {
      for (const b of lista || []) {
        const c = _cruDe.get(b.id);
        if (c && b.id) out.push({ codigo: String(b.id), cru: c });
      }
    } catch (e) {}
    return out;
  }

  const P_POS = "/sports-betting/v4/bets/positions";
  const P_EV = "/sports-api/v6/sports/events/";
  const RX_AUTH = /^\/sports-(api|betting)\//i;            // onde os cabeçalhos se aprendem
  const NOMES_AUTH = ["authorization", "x-cloudbet-metadata", "x-cloudbet-version"];
  const LIMITE = 999;                          // o que a página pede (o teto medido é 1000)
  const TETO_PAGINAS = 100;                    // por janela: 100 × 999 bilhetes
  const LIMITE_DET = 100;                      // apostas por página do detalhe (200 dá 400)
  const JANELA_MS = 360 * 86400000;            // < 1 ano (o servidor recusa mais)
  const PISO_MS = Date.UTC(2013, 0, 1);        // a casa não tem aposta anterior a isto
  const FOLGA_MS = 2 * 86400000;               // margem da janela de dias do robô
  const PARALELO = 4;                          // detalhes/eventos simultâneos

  const byId = new Map();                      // uuid → bilhete normalizado
  let respostas = 0;                           // respostas VÁLIDAS (autodiagnóstico)
  const auth = {};                             // os três cabeçalhos (nunca saem daqui)
  let pedido = false;                          // o robô já pediu → pode arrancar o replay
  let desde = 0;                               // janela de dias do robô (ms; 0 = tudo)
  let loopAtivo = false, fimReplay = false, repetir = false;
  let erro = "";
  const LOG = (...a) => { try { console.log("[SharpenUp cb_inject]", ...a); } catch (e) {} };
  LOG("hook instalado em", location.href);

  const of = window.fetch;                     // fetch ORIGINAL — o replay usa este

  // ── normalização ─────────────────────────────────────────────────────────────
  const _n = (v) => {
    if (v == null || v === "") return null;
    const x = Number(v);
    return isFinite(x) ? x : null;
  };
  const _s = (v) => (v == null ? "" : String(v));
  // ISO com 6 casas de fração ("…17:53:03.964243Z"): corta em 3 antes de ler. Unix em SEGUNDOS.
  const _iso = (v) => { const t = Date.parse(_s(v).replace(/(\.\d{3})\d+/, "$1")); return isFinite(t) ? t / 1000 : null; };
  const _caminho = (u) => { try { return new URL(_s(u), location.href).pathname; } catch (e) { return ""; } };
  const _chaveSel = (s) => [s && s.eventId, s && s.marketKey, s && s.outcome, s && s.params].map(_s).join("|");

  function parseEvento(e) {
    if (!e || typeof e !== "object" || e.error) return null;
    return {
      jogo: _s(e.name),
      esporte: _s(e.sport && e.sport.name),
      liga: _s(e.competition && e.competition.name),
      pais: _s(e.competition && e.competition.category && e.competition.category.name),
      inicio: _iso(e.cutoffTime),
      status: _s(e.status),
    };
  }
  // Os campos do evento que o cru leva (o resto é placar, jogadores e mídia).
  function eventoCru(e) {
    if (!e || typeof e !== "object") return null;
    const c = e.competition || {};
    return {
      id: e.id, name: e.name, key: e.key, status: e.status, cutoffTime: e.cutoffTime,
      sport: e.sport ? { key: e.sport.key, name: e.sport.name } : null,
      competition: { key: c.key, name: c.name, category: c.category ? { key: c.category.key, name: c.category.name } : null },
      home: e.home ? { key: e.home.key, name: e.home.name } : null,
      away: e.away ? { key: e.away.key, name: e.away.name } : null,
    };
  }

  function parsePerna(s, nomes, eventos) {
    const nm = nomes.get(_chaveSel(s)) || {};
    const ev = eventos.get(_s(s.eventId)) || {};
    return {
      eventoId: _s(s.eventId),
      jogo: ev.jogo || "",
      liga: ev.liga || "",
      pais: ev.pais || "",
      esporte: ev.esporte || "",
      esporteChave: _s(s.sportKey),
      inicio: ev.inicio == null ? null : ev.inicio,
      mercado: _s(nm.marketName),
      selecao: _s(nm.outcomeName || nm.name),
      mercadoChave: _s(s.marketKey),
      parametros: _s(s.params),
      resultado: _s(s.result),                   // WIN · LOSS · PUSH · PENDING (CRU)
      odd: _n(s.price),
    };
  }

  // Uma aposta do DETALHE + o item da lista de onde ela saiu.
  function parseAposta(bet, item, nomes, eventos) {
    if (!bet || !bet.uuid) return null;
    const estado = _s(bet.state);
    const aberta = estado === "ACCEPTED";
    return {
      id: _s(bet.uuid),
      posicao: _s(item && item.positionId),
      aberta: aberta,
      estado: estado,                            // ACCEPTED · COMPLETED (CRU)
      resultado: _s(bet.result),                 // WIN · LOSS · PUSH · PENDING (CRU)
      tipoApi: _s(bet.type),                     // PARLAY · SAME_GAME_PARLAY · … (CRU)
      lado: _s(bet.side),
      moeda: _s(bet.baseCurrency).toUpperCase(),
      stake: _n(bet.stake),
      odd: _n(bet.price),                        // a odd da aposta (o "@ 6.93" do card)
      oddAjustada: _n(bet.adjustedPrice),
      lucro: aberta ? null : _n(bet.returnAmount),   // LUCRO, não retorno
      retornoPotencial: _n(bet.potentialReturnAmount),
      cashout: bet.isCashoutBet === true,
      colocada: _iso(bet.createTime),
      liquidada: aberta ? null : _iso(bet.completeTime),
      // Da SUB-POSIÇÃO da aposta: no EVENT o `betCount` do item soma seleções diferentes do jogo.
      apostasNaPosicao: _n(((item && item.positions) || []).filter((p) => p && p.betLegIdentifier === bet.betLegsIdentifier)
        .map((p) => p.betCount)[0] ?? (item && item.betCount)),
      pernas: (Array.isArray(bet.selections) ? bet.selections : []).map((s) => parsePerna(s, nomes, eventos)),
    };
  }

  // Assinatura das seleções de uma aposta: duas apostas só se juntam se forem a MESMA aposta.
  const _assinaturaSel = (bet) => (Array.isArray(bet && bet.selections) ? bet.selections : [])
    .map(_chaveSel).sort().join("§");
  const _soma = (xs) => Math.round(xs.reduce((a, x) => a + (typeof x === "number" ? x : 0), 0) * 1e8) / 1e8;

  // N apostas da MESMA sub-posição (mesmas seleções) → UM bilhete, como o card da casa mostra.
  // Cada aposta segue inteira em `apostas[]`: o formatador decide o resultado aposta por aposta
  // e só junta quando todas dizem o mesmo. A odd é a média ponderada pela stake.
  // Seleções de cada aposta ALINHADAS às da 1ª pela chave (a ordem não é garantida entre elas).
  function _alinhar(bets) {
    const ordem = ((bets[0] && bets[0].selections) || []).map(_chaveSel);
    return bets.map((b) => {
      const m = new Map(((b && b.selections) || []).map((s) => [_chaveSel(s), s]));
      return ordem.map((k) => m.get(k) || {});
    });
  }

  function parseGrupo(leg, bets, item, nomes, eventos) {
    const unid = bets.map((bet) => parseAposta(bet, item, nomes, eventos)).filter(Boolean);
    if (unid.length !== bets.length) return null;
    const alinhadas = _alinhar(bets);
    unid.forEach((u, i) => { u.pernas = alinhadas[i].map((s) => ({ odd: _n(s.price), resultado: _s(s.result) })); });
    const base = Object.assign({}, unid[0], { pernas: parseAposta(bets[0], item, nomes, eventos).pernas });
    const stake = _soma(unid.map((u) => u.stake));
    const pond = (f) => {
      let num = 0, den = 0;
      for (const u of unid) { const o = f(u); if (typeof o === "number" && o > 0 && u.stake > 0) { num += u.stake * o; den += u.stake; } }
      return den > 0 ? Math.round((num / den) * 1e9) / 1e9 : null;
    };
    const aberta = unid.some((u) => u.aberta);
    const resultados = Array.from(new Set(unid.map((u) => u.resultado)));
    const colocadas = unid.map((u) => u.colocada).filter((x) => typeof x === "number");
    const liquidadas = unid.map((u) => u.liquidada).filter((x) => typeof x === "number");
    const odds = unid.map((u) => u.odd).filter((x) => typeof x === "number" && x > 0);
    return Object.assign({}, base, {
      id: leg,
      aberta: aberta,
      estado: aberta ? "ACCEPTED" : base.estado,
      resultado: resultados.length === 1 ? resultados[0] : resultados.join("+"),
      stake: stake,
      odd: pond((u) => u.odd),
      oddMin: odds.length ? Math.min.apply(null, odds) : null,
      oddMax: odds.length ? Math.max.apply(null, odds) : null,
      lucro: aberta ? null : (unid.every((u) => typeof u.lucro === "number") ? _soma(unid.map((u) => u.lucro)) : null),
      retornoPotencial: _soma(unid.map((u) => u.retornoPotencial)),
      cashout: unid.some((u) => u.cashout),
      colocada: colocadas.length ? Math.min.apply(null, colocadas) : null,
      liquidada: aberta || !liquidadas.length ? null : Math.max.apply(null, liquidadas),
      apostasNaPosicao: unid.length,
      consolidadas: unid.length,
      // A odd de cada perna também varia entre as apostas (no Bet Builder é a do conjunto).
      pernas: base.pernas.map((p, i) => {
        const o = pond((u) => u.pernas[i] && u.pernas[i].odd);
        return Object.assign({}, p, { odd: o == null ? null : Math.round(o * 1e4) / 1e4 });
      }),
      apostas: unid.map((u) => ({ id: u.id, estado: u.estado, aberta: u.aberta, resultado: u.resultado,
                                  stake: u.stake, odd: u.odd, lucro: u.lucro, cashout: u.cashout,
                                  pernas: u.pernas.map((p) => ({ resultado: p.resultado })) })),
    });
  }

  // O cru da aposta juntada: a 1ª aposta inteira (seleções, tipo, moeda) e, de cada uma, só o que
  // muda entre elas. Cada aposta inteira pesa ~1,9 KB e o servidor recusa cru acima de 64 KB.
  // `precos`/`resultados` seguem a ordem das seleções da 1ª aposta (`aposta.selections`).
  function cruGrupo(leg, bets, item, evs) {
    const alinhadas = _alinhar(bets);
    return {
      grupo: leg, aposta: bets[0], posicao: item, eventos: evs,
      apostas: bets.map((b, i) => ({
        uuid: b.uuid, state: b.state, result: b.result, stake: b.stake, price: b.price,
        returnAmount: b.returnAmount, potentialReturnAmount: b.potentialReturnAmount,
        createTime: b.createTime, completeTime: b.completeTime, isCashoutBet: b.isCashoutBet,
        baseCurrency: b.baseCurrency,
        precos: alinhadas[i].map((s) => (s.price == null ? null : String(s.price))),
        resultados: alinhadas[i].map((s) => _s(s.result)),
      })),
    };
  }

  // O dinheiro do cashout (s453). Medido: BACK 400 @ 8,161 `returnAmount` −400 + LAY 3.129,82 @
  // 1,043 `returnAmount` +134,58 = −265,42, o "L/P −$265,42" do card e o `returnAmount` do
  // `portfolio` da sub-posição; o `cashoutAmount` dele é 134,58 (= stake + lucro). Só vale com a
  // prova da casa: original liquidada como CASHED_OUT, contra-apostas liquidadas e a soma igual ao
  // portfolio. Sem isso o bilhete segue com o lucro só da original e o formatador sobe "a conferir".
  function _cashout(b, bet, contra, it, leg, m) {
    b.cashoutContra = 0;
    if (b.aberta || _s(bet.result) !== "CASHED_OUT" || contra.some((x) => _s(x.state) === "ACCEPTED")) return;
    const lucros = [bet].concat(contra).map((x) => _n(x.returnAmount));
    if (lucros.some((x) => typeof x !== "number")) return;
    const sub = ((it && it.positions) || []).find((p) => p && p.betLegIdentifier === leg);
    const port = sub && sub.portfolio && sub.portfolio[m];
    const lucro = _soma(lucros);
    if (!port || typeof _n(port.returnAmount) !== "number" || Math.abs(lucro - _n(port.returnAmount)) > 0.005) return;
    b.lucro = lucro;
    b.cashoutContra = contra.length;
  }

  // Emite SEMPRE hook:true + respostas (heartbeat), mesmo com 0 bilhetes. NUNCA leva o token.
  function enviar() {
    try {
      const lista = Array.from(byId.values());
      window.postMessage({
        __sharpenupCBData: true, hook: true,
        bilhetes: lista, respostas: respostas, fim: fimReplay,
        cru: _crus(lista), semToken: !auth.authorization, erro: erro,
      }, "*");
    } catch (e) {}
  }

  // ── aprendizado ────────────────────────────────────────────────────────────────
  function aprender(url, headers) {
    if (!RX_AUTH.test(_caminho(url))) return;
    let viu = false;
    for (const k of Object.keys(headers || {})) {
      const l = k.toLowerCase();
      if (NOMES_AUTH.indexOf(l) < 0) continue;
      const v = _s(headers[k]).trim();
      if (!v) continue;
      if (l === "authorization") { if (!auth.authorization) LOG("cabeçalhos aprendidos de", _caminho(url)); viu = true; }
      auth[l] = v;                             // sempre o mais novo: o JWT renova
    }
    if (viu && pedido) arrancarReplay();
  }

  // ── replay ─────────────────────────────────────────────────────────────────────
  async function pedir(caminho) {
    const h = { accept: "application/json" };
    for (const k of NOMES_AUTH) if (auth[k]) h[k] = auth[k];
    const r = await of.call(window, location.origin + caminho, { method: "GET", credentials: "include", headers: h });
    return { ok: !!(r && r.ok), status: r && r.status, text: r ? await r.text() : "" };
  }

  const _falhou = (r) => "replay parou · HTTP " + r.status +
    (r.status === 401 || r.status === 403 ? " (sessão expirada? recarregue a aba logada)" : "");

  // Uma lista (uma janela) inteira, avançando pelo tamanho que VOLTOU, até `hasNext:false`.
  async function lerLista(filtro, itens) {
    let offset = 0;
    for (let p = 0; p < TETO_PAGINAS; p++) {
      const r = await pedir(P_POS + "?limit=" + LIMITE + "&locale=en&offset=" + offset + "&" + filtro);
      if (!r.ok) { erro = _falhou(r); LOG(erro); return false; }
      let j;
      try { j = JSON.parse(r.text); } catch (e) { j = null; }
      if (!j || !Array.isArray(j.items)) { erro = "resposta da lista em formato desconhecido"; LOG(erro); return false; }
      respostas++;
      enviar();                                // batimento: o robô mede atividade por `respostas`
      for (const it of j.items) {
        if (!it || !it.positionId) continue;
        const ex = itens.get(it.positionId);
        // A LIQUIDADA vence a aberta (o bilhete liquidou entre as duas listas).
        if (!ex || ex.positionStatus !== "COMPLETED") itens.set(it.positionId, it);
      }
      offset += j.items.length;
      if (j.hasNext !== true || !j.items.length) return true;      // fim AUTORITATIVO
    }
    LOG("teto de páginas atingido");
    return true;
  }

  const _isoZ = (ms) => new Date(ms).toISOString();

  // Corre `fn` sobre a lista, PARALELO por vez. Devolve false se alguma devolveu false.
  async function emLotes(lista, fn) {
    let ok = true, i = 0;
    const trab = async () => { while (i < lista.length) { const x = lista[i++]; if ((await fn(x)) === false) ok = false; } };
    await Promise.all(Array.from({ length: Math.min(PARALELO, lista.length) }, trab));
    return ok;
  }

  async function varrer() {
    const itens = new Map();
    if (!(await lerLista("status=ACCEPTED", itens))) return false;
    // Liquidadas: janelas de 360 dias, de amanhã para trás, até a janela do robô (ou o piso).
    const piso = Math.max(PISO_MS, desde > 0 ? desde - FOLGA_MS : 0);
    let fim = Date.now() + 86400000;
    while (fim > piso) {
      const ini = Math.max(fim - JANELA_MS, piso);
      const f = "status=COMPLETED&from=" + encodeURIComponent(_isoZ(ini)) + "&to=" + encodeURIComponent(_isoZ(fim));
      if (!(await lerLista(f, itens))) return false;
      fim = ini;
    }
    LOG("posições:", itens.size);

    // Detalhe de cada SUB-POSIÇÃO (`betLegIdentifier`), em cada moeda NATIVA dela (as chaves do
    // `portfolio`), paginado. Pelo `positionId` a simples (EVENT) volta vazia e a página tem 20.
    const pedidos = [];
    for (const it of itens.values()) {
      for (const p of (it.positions || [])) {
        const leg = _s(p && p.betLegIdentifier);
        if (!leg) continue;
        for (const m of Object.keys((p && p.portfolio) || {})) pedidos.push({ it, leg, m });
      }
    }
    const grupos = [];                           // { leg, m, it, bets }
    const okDet = await emLotes(pedidos, async ({ it, leg, m }) => {
      const bets = [];
      for (let offset = 0, pg = 0; pg < TETO_PAGINAS; pg++) {
        const r = await pedir(P_POS + "/" + encodeURIComponent(leg) + "?currency=" + encodeURIComponent(m) +
                              "&locale=en&limit=" + LIMITE_DET + "&offset=" + offset);
        if (!r.ok) { erro = _falhou(r); LOG(erro); return false; }
        let j;
        try { j = JSON.parse(r.text); } catch (e) { j = null; }
        if (!j || !Array.isArray(j.bets)) { erro = "detalhe da posição em formato desconhecido"; LOG(erro); return false; }
        respostas++;
        if (respostas % 20 === 0) enviar();    // batimento a cada 20 detalhes
        for (const bet of j.bets) if (bet && bet.uuid) bets.push(bet);
        offset += j.bets.length;
        if (j.bets.length < LIMITE_DET) break;   // página curta = fim (o detalhe não traz hasNext)
      }
      if (bets.length) grupos.push({ leg, m, it, bets });
    });

    // Um evento por id distinto. Evento que falha não para a captura: a perna vai sem jogo.
    const ids = new Set();
    for (const { bets } of grupos) for (const bet of bets) for (const s of (bet.selections || [])) if (s && s.eventId != null) ids.add(_s(s.eventId));
    const eventos = new Map(), eventosCru = new Map();
    await emLotes(Array.from(ids), async (id) => {
      try {
        const r = await pedir(P_EV + encodeURIComponent(id) + "?locale=en&markets=x");
        if (!r.ok) return;
        const e = JSON.parse(r.text);
        const ev = parseEvento(e);
        if (ev) { eventos.set(id, ev); eventosCru.set(id, eventoCru(e)); }
        respostas++;
        if (respostas % 20 === 0) enviar();
      } catch (e) {}
    });

    // A sub-posição em mais de uma moeda (não medido) não se junta entre moedas: cada moeda é um
    // bilhete, com a moeda no código para não colidir.
    const moedasDoLeg = new Map();
    for (const g of grupos) moedasDoLeg.set(g.leg, (moedasDoLeg.get(g.leg) || 0) + 1);
    const guardar = (b, cru) => {
      _cruDe.set(b.id, cru);
      const ex = byId.get(b.id);
      if (!ex || ex.aberta || !b.aberta) byId.set(b.id, b);
    };
    const evsDe = (b) => {
      const evs = {};
      for (const p of b.pernas) if (eventosCru.has(p.eventoId)) evs[p.eventoId] = eventosCru.get(p.eventoId);
      return evs;
    };
    let juntadas = 0;
    for (const { leg, m, it, bets } of grupos) {
      const nomes = new Map();
      for (const p of (it.positions || [])) for (const s of ((p && p.selections) || [])) nomes.set(_chaveSel(s), s);
      // CASHOUT (s453, o 1º medido, 13/11/2026): a casa registra o cashout como uma aposta
      // CONTRÁRIA na mesma sub-posição (`side: LAY`, `isCashoutBet: true`), e a original passa a
      // `result: CASHED_OUT`. A LAY não é aposta, é o mecanismo do cashout: virava um bilhete de
      // 3.129,82 USDT @ 1,043 e a Caixa contava a stake dela em aberto. Ela nunca vira bilhete; o
      // dinheiro dela vai para a original e sobe no cru (`cashout`), para a Ficha conferir.
      const contra = bets.filter((x) => x && x.isCashoutBet === true);
      if (contra.length) {
        const reais = bets.filter((x) => !(x && x.isCashoutBet === true));
        for (const bet of reais) {
          const b = parseAposta(bet, it, nomes, eventos);
          if (!b) continue;
          if (reais.length === 1) _cashout(b, bet, contra, it, leg, m);
          guardar(b, { aposta: bet, posicao: it, eventos: evsDe(b), cashout: contra });
        }
        continue;
      }
      // Junta só se TODAS têm as mesmas seleções (46 de 46 no recon). Senão, cada uma sozinha.
      const mesma = bets.length > 1 && bets.every((x) => _assinaturaSel(x) === _assinaturaSel(bets[0]));
      if (mesma) {
        const id = moedasDoLeg.get(leg) > 1 ? leg + "-" + m : leg;
        const b = parseGrupo(id, bets, it, nomes, eventos);
        if (b) { guardar(b, cruGrupo(id, bets, it, evsDe(b))); juntadas += bets.length; continue; }
      }
      for (const bet of bets) {
        const b = parseAposta(bet, it, nomes, eventos);
        if (b) guardar(b, { aposta: bet, posicao: it, eventos: evsDe(b) });
      }
    }
    LOG("bilhetes:", byId.size, "· apostas juntadas:", juntadas, "· eventos:", eventos.size, "de", ids.size);
    return okDet;
  }

  async function arrancarReplay() {
    if (loopAtivo || fimReplay || !auth.authorization) return;
    loopAtivo = true;
    erro = "";
    try {
      await varrer();
    } catch (e) {
      erro = "replay falhou: " + (e && e.message); LOG(erro);
    } finally {
      loopAtivo = false;
      fimReplay = true;
      enviar();
      if (repetir) { repetir = false; fimReplay = false; byId.clear(); _cruDe.clear(); arrancarReplay(); }
    }
  }

  // O content pede o acumulado ao iniciar o robô → zera, re-envia e arranca o replay. Zerar é
  // a lição da s393 (DEX Sport): sem isso a 2ª rodada na mesma aba devolvia o mapa velho.
  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (!d || !d.__sharpenupCBReq) return;
    pedido = true;
    if (typeof d.desde === "number" && isFinite(d.desde)) desde = d.desde;
    if (loopAtivo) repetir = true;
    else { fimReplay = false; byId.clear(); _cruDe.clear(); }
    enviar();
    arrancarReplay();
  });

  // ── fetch ── (medido: a página usa fetch, com os cabeçalhos no objeto de opções)
  const _hdrsToObj = (h) => {
    const o = {};
    try {
      if (!h) return o;
      if (typeof h.forEach === "function") h.forEach((v, k) => { o[k] = v; });
      else if (typeof h === "object") for (const k in h) o[k] = h[k];
    } catch (e) {}
    return o;
  };
  if (of && !of.__suCBW) {
    const w = function (...a) {
      const req = (a[0] && typeof a[0] === "object" && a[0].url) ? a[0] : null;
      const url = req ? req.url : a[0];
      const opts = a[1] || {};
      try { aprender(url, _hdrsToObj(opts.headers || (req && req.headers))); } catch (e) {}
      return of.apply(this, a);
    };
    w.__suCBW = true;
    window.fetch = w;
  }

  // ── XMLHttpRequest ── (rede de segurança, caso a casa troque de transporte)
  const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send,
        osh = XMLHttpRequest.prototype.setRequestHeader;
  if (!os.__suCBW) {
    XMLHttpRequest.prototype.open = function (m, u) { this.__suCBU = u; this.__suCBH = {}; return oo.apply(this, arguments); };
    XMLHttpRequest.prototype.setRequestHeader = function (k, v) { try { this.__suCBH[k] = v; } catch (e) {} return osh.apply(this, arguments); };
    const s = function (body) {
      try { aprender(this.__suCBU, this.__suCBH); } catch (e) {}
      return os.apply(this, arguments);
    };
    s.__suCBW = true;
    XMLHttpRequest.prototype.send = s;
  }

  enviar();
})();
