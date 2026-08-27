// Mundo MAIN — Bolsa de Aposta / EXCHANGE. Roda DENTRO do iframe `mexchange2.…`, nunca na
// casca (s299).
//
//   GET https://mexchange-api.<dominio>/api/offers/reportsv2   → a lista de ofertas
//
// ⚠ A CASCA NÃO SERVE. `bolsadeaposta.bet.br` é Angular e **não faz uma única requisição de
// bilhete**: grampo em fetch + XHR + WebSocket no frame principal viu ZERO enquanto a tabela
// enchia de aposta. A tela de apostas vive num iframe de OUTRA ORIGEM — a armadilha da
// bet365 (`all_frames:false`). Este arquivo só funciona com `all_frames: true`.
//
// PLATAFORMA, NÃO CASA. O bundle é o mesmo de `matchbook.bet.br`, `verdinhabet`,
// `fulltbet.bet.br`, `betespecial.bet.br` e `bet-bra.bet.br` (LayBack/FulltBet). O `match`
// usa curinga de propósito: o subdomínio é VERSIONADO (`"defaultExchangeVerion":
// "https://mexchange2."`, chumbado no bundle da casca) e o dia em que virar `mexchange3.`
// um match literal para de bater e **a captura morre sem erro nenhum**.
//
// A URL DA API É DERIVADA, os headers NÃO. A própria casa deriva assim
// (`host.replace(/^(mexchange\d*\.)/,"")`) e foi o que medi: a chamada responde 200 com
// **cookie e mais nada** — nenhum header de canal, nenhum Bearer. Testado anônimo, o mesmo
// endereço devolve `401 "Please login to get offers"`, então a rota existe e a sessão é o
// cookie. Derivar a URL é reproduzir a regra pública do app; inventar header seria chute, e
// por isso os headers só entram se vierem de uma requisição REAL (`capturarReq`).
//
// O REPLAY É OBRIGATÓRIO, e não é por paginação:
//
//   (1) A TELA PEDE NO MÁXIMO 30 DIAS (o maior preset do calendário) e avisa que "apostas
//       feitas há mais de 3 meses não são mostradas aqui". A conta do recon tinha 418
//       bilhetes em 9 meses. Um passivo perfeito pegaria o último mês e pareceria funcionar.
//   (2) SEM `status` A CASA NÃO DEVOLVE TUDO — devolve só as liquidadas (medido: omitir o
//       parâmetro e `status=liquidated` dão exatamente o mesmo total). Aposta em aberto
//       exige uma segunda chamada, com `status=matched,unmatched`.
//
// TETO DURO DA JANELA: `Max allowed interval is 95 days` (HTTP 400, mensagem da própria
// casa). O replay fatia em 90 dias — margem deliberada, porque a borda de 95 é do servidor e
// não vale disputar um dia com ela. `status=cancelled` NÃO entra na varredura: os 3 bilhetes
// que ele devolveu já vinham nas liquidadas (todos `failed`), então seria uma chamada a mais
// por fatia para reencontrar o que já temos.
//
// ARMADILHAS confirmadas no dado real (o inject NÃO decide — quem lê é o `formatTicketBDA`):
//   • `failed` NÃO É BILHETE. É oferta que nunca casou: vem sem `stake-matched` e sem
//     `profit-and-loss`. Dinheiro que nunca esteve em risco. Sai da lista — mas **contado**
//     em `naoCasadas`, porque descarte silencioso é o pecado que este projeto já pagou caro.
//     O corte é pelo status `failed`, NUNCA por "stake zerado": oferta `unmatched` em aberto
//     também tem casado zero e é aposta viva de verdade.
//   • STAKE É `stake-matched`, NUNCA `stake`. A oferta `failed` traz `stake: 100` com risco
//     zero — ler o campo óbvio lança R$100 que não existiram.
//   • `push` (= anulada) vem SEM `profit-and-loss` — o campo é AUSENTE, não zero. Quem fizer
//     `pl ?? 0` acerta o número por acidente; quem tratar ausência como perda, erra.
//   • `profit-and-loss` é LUCRO, não retorno. W → `(stake + pl) ÷ stake`.
//   • Datas em UTC com `Z` → o content converte para America/Sao_Paulo. Conferido ao minuto
//     contra o card: `2026-08-21T19:00:00Z` ⇄ "Início do Evento: 21/08/2026, 16:00:00".
//   • `push_win` / `push_lose` existem no código da casa (meia-vitória / meia-derrota) mas
//     não houve amostra. Sobem CRUS — nunca viram HW/HL por chute.
(function () {
  // TRAVA DE HOST. O popup injeta os DOIS arquivos em TODOS os frames (é o único jeito de
  // alcançar aba já aberta, onde o manifest declarativo não roda de novo). Sem esta linha,
  // este inject também carregaria dentro do frame do Sportsbook e mandaria `hook:true` de
  // lá — e o autodiagnóstico passaria a jurar que o Exchange respondeu quando ele nem
  // existe na página. Heartbeat falso é pior que heartbeat ausente.
  try { if (!/^mexchange\d*\./i.test(new URL(location.href).host)) return; } catch (e) { return; }

  const RX = /\/api\/offers\/reportsv2/i;      // endpoint da LISTA de ofertas
  const byRef = new Map();                     // id(string) → bilhete normalizado
  let respostas = 0;                           // respostas do endpoint que o hook viu
  // Ofertas `failed` descartadas — por IDENTIDADE, nunca por ocorrência. A mesma oferta
  // reaparece a cada fatia da varredura (e nas duas variantes de `status`); um contador que
  // incrementa transformaria 1 descarte em 11 e o painel mentiria para o operador.
  const naoCasadas = new Set();
  let reqCtx = null;                           // {url, headers} de uma requisição real
  let pedido = false;                          // o robô já pediu → pode arrancar o replay
  let diasPedidos = 0;                         // janela que o robô pediu (0 = padrão)
  let loopAtivo = false;
  let fimReplay = false;
  let repetir = false;                         // pedido chegou durante a varredura → roda de novo
  let erro = "";
  const LOG = (...a) => { try { console.log("[SharpenUp bda_inject]", ...a); } catch (e) {} };
  LOG("hook instalado em", location.href);

  const of = window.fetch;                     // fetch ORIGINAL (o replay não re-dispara o wrapper)

  const PAGINA = 500;          // aceito e respeitado (500 pedidos → 213 devolvidos, sem corte)
  const FATIA = 90;            // dias por requisição — a casa recusa acima de 95
  const TETO_PAGINAS = 200;
  // HORIZONTE FIXO — 3 anos, ~13 fatias × 2 chamadas ≈ 5 s. Não sai do `lookbackDias` do
  // painel, e isso é deliberado: na 1ª captura ao vivo (s299) a janela padrão de 30 dias
  // fez o robô varrer 27/07→26/08 e parar na borda exata, trazendo 21 de 418 bilhetes. O
  // operador leu como "travou na primeira página", porque a data que ele tinha escolhido NA
  // TELA nunca chegou até aqui — o robô não lê a tela, ele varre a API. Aqui a varredura
  // completa é barata (uma chamada por fatia) e a recaptura não paga IA de novo: a casa está
  // no pré-dedup por código do backend. O `dias` do painel só é respeitado quando pede MAIS.
  const DIAS_HISTORICO = 1095;

  // Base da API. A casa deriva o domínio removendo o prefixo `mexchange<N>.` do próprio host —
  // é a regra dela, lida no bundle, não invenção nossa. `new URL` em vez de `location.host`
  // porque o harness dubla `location` com só `href` e `origin`.
  function _base() {
    let host = "";
    try { host = new URL(location.href).host; } catch (e) { host = ""; }
    const dominio = String(host).replace(/^mexchange\d*\./i, "");
    return "https://mexchange-api." + dominio + "/api/offers/reportsv2";
  }

  // ── normalização ───────────────────────────────────────────────────────────────
  // Dinheiro e odds vêm em REAIS, já como número (1.35 = odd 1,35 · 100 = R$100,00).
  // NÃO há milésimos — conferido campo a campo contra o card.
  const _n = (v) => (typeof v === "number" ? v : null);
  const _s = (v) => (v == null ? "" : String(v));

  function parseOferta(o, out) {
    if (!o || o.id == null) return;
    const status = _s(o.status);
    // Oferta que nunca casou. Não é bilhete: não há dinheiro em risco, não há resultado, e
    // planilhá-la criaria uma linha de aposta que não existiu. Contada, nunca calada.
    if (status === "failed") { naoCasadas.add(_s(o.id)); return; }
    out.push({
      ref: _s(o.id),                                  // o [Código:] e a chave de dedup
      lado: _s(o.side),                               // back / lay (CRU — só há amostra de back)
      status: status,                                 // win / lose / push / matched / … (CRU)
      // A odd efetiva é a MÉDIA do que casou. `odds` é a pedida; nas amostras coincidem, mas
      // em casamento parcial elas divergem por natureza — e quem manda é o que casou.
      odd: _n(o["avg-decimal-odds-matched"]),
      oddPedida: _n(o["decimal-odds"]),
      stake: _n(o["stake-matched"]),                  // ⚠ NUNCA `o.stake`
      stakePedida: _n(o.stake),
      restante: _n(o.remaining),
      // AUSENTE em `push`. Fica `null` de propósito: o formatador precisa distinguir
      // "não houve lucro/prejuízo" de "a casa não informou".
      pl: Object.prototype.hasOwnProperty.call(o, "profit-and-loss") ? _n(o["profit-and-loss"]) : null,
      moeda: _s(o.currency),
      esporte: _s(o.sportName),                       // "soccer" (inglês, CRU)
      evento: _s(o["event-name"]),
      mercado: _s(o["market-name"]),
      tipoMercado: _s(o["market-type"]),              // "custom" = Criador de Eventos
      selecao: _s(o["runner-name"]),                  // ⚠ "Sim"/"Não" INVERTEM o mercado
      inicio: _s(o["event-start-time"]),              // UTC com Z → autoridade da coluna Data
      colocada: _s(o["created-at"]),
      casada: _s(o["matched-time"]),
      liquidada: _s(o["settled-time"]),
      aoVivo: !!o["keep-in-play"],
    });
  }

  // Heartbeat: SEMPRE `hook` + `respostas`, mesmo com 0 bilhetes. É o que separa "não
  // injetei" de "endpoint mudou" de "conta vazia" no autodiagnóstico.
  function enviar() {
    const msg = {
      __sharpenupBDAData: true, hook: true,
      bilhetes: Array.from(byRef.values()), respostas: respostas, fim: fimReplay,
      naoCasadas: naoCasadas.size, erro: erro,
    };
    try { window.postMessage(msg, "*"); } catch (e) {}
    // ⚠ SEM ESTA LINHA A CAPTURA NÃO EXISTE. Este inject roda DENTRO do iframe e o
    // `content.js` roda no topo (`all_frames: false`); `postMessage` na própria janela nunca
    // sobe. Mesmo remédio de bf_inject/b3_inject/tv_inject.
    try { if (window.top && window.top !== window) window.top.postMessage(msg, "*"); } catch (e) {}
  }

  // Resolvida vence aberta: o mesmo id volta na varredura das liquidadas e na das abertas.
  // `settled-time` só existe depois de liquidar.
  function guardar(b) {
    const ex = byRef.get(b.ref);
    if (!ex) { byRef.set(b.ref, b); return; }
    if (!ex.liquidada && b.liquidada) byRef.set(b.ref, b);
  }

  // Processa uma resposta. Devolve `{total, veio}` para o replay decidir se continua.
  function forward(url, text) {
    if (!RX.test(String(url)) || typeof text !== "string") return null;
    let j;
    try { j = JSON.parse(text); } catch (e) { return null; }
    if (!j || !Array.isArray(j.offers)) return null;   // corpo de erro (400/401) ou formato mudou
    respostas++;
    const novos = [];
    for (const o of j.offers) parseOferta(o, novos);
    for (const b of novos) guardar(b);
    LOG("ofertas na resposta:", j.offers.length, "· bilhetes:", byRef.size,
        "· não casadas:", naoCasadas.size, "· total da janela:", j.total);
    enviar();
    return { total: typeof j.total === "number" ? j.total : 0, veio: j.offers.length };
  }

  // ── replay ─────────────────────────────────────────────────────────────────────
  function _hdrsToObj(h) {
    const o = {};
    try {
      if (!h) return o;
      if (typeof h.forEach === "function") h.forEach((v, k) => { o[k] = v; });
      else if (typeof h === "object") for (const k in h) o[k] = h[k];
    } catch (e) {}
    return o;
  }

  function capturarReq(url, headers) {
    if (!RX.test(String(url))) return;
    if (!reqCtx) {
      reqCtx = { url: String(url).split("?")[0], headers: headers || {} };
      LOG("requisição capturada p/ replay");
    }
    if (pedido) arrancarReplay();
  }

  const _dia = (d) => {
    const p = (n) => (n < 10 ? "0" + n : String(n));
    return d.getFullYear() + "-" + p(d.getMonth() + 1) + "-" + p(d.getDate());
  };

  // Fatias de 90 dias cobrindo `dias` para trás, da mais recente para a mais antiga.
  function _fatias(dias) {
    const out = [];
    const fim = new Date();
    fim.setDate(fim.getDate() + 1);            // +1 dia: cobre fuso e bilhete de hoje
    let restam = dias;
    while (restam > 0 && out.length < 60) {
      const ini = new Date(fim.getTime());
      const passo = Math.min(FATIA, restam);
      ini.setDate(ini.getDate() - passo);
      out.push({ de: _dia(ini), ate: _dia(fim) });
      fim.setTime(ini.getTime());
      restam -= passo;
    }
    return out;
  }

  // Uma fatia × uma variante de `status`, paginando por `offset` até o `total` da janela.
  async function varrer(fatia, status) {
    const alvo = (reqCtx && reqCtx.url) || _base();
    let offset = 0;
    for (let i = 0; i < TETO_PAGINAS; i++) {
      const q = new URLSearchParams({
        offset: String(offset), "per-page": String(PAGINA),
        "after-day": fatia.de, "before-day": fatia.ate,
        "timezone-offset": String(new Date().getTimezoneOffset()),
      });
      // Sem `status` a casa devolve SÓ as liquidadas — a variante das abertas é obrigatória.
      if (status) q.set("status", status);
      let r;
      try {
        r = await of.call(window, alvo + "?" + q.toString(), {
          method: "GET", headers: (reqCtx && reqCtx.headers) || {}, credentials: "include",
        });
      } catch (e) { erro = "replay falhou: " + (e && e.message); LOG(erro); return false; }
      if (!r || !r.ok) { erro = "replay parou · HTTP " + (r && r.status); LOG(erro); return false; }
      let st;
      try { st = forward(r.url || alvo, await r.text()); } catch (e) { return false; }
      if (!st) return false;
      // Avança pelo que a casa REALMENTE devolveu, nunca pelo `per-page` que pedimos.
      offset += st.veio;
      if (st.veio <= 0 || offset >= st.total) return true;
    }
    LOG("teto de páginas atingido");
    return true;
  }

  async function arrancarReplay() {
    // Pedido que chega com a varredura em curso não se perde: fica marcado e roda ao fim.
    if (loopAtivo) { repetir = true; return; }
    if (fimReplay) return;
    loopAtivo = true;
    try {
      const fatias = _fatias(Math.max(diasPedidos, DIAS_HISTORICO));
      for (const f of fatias) {
        await varrer(f, "");                      // liquidadas (o padrão da casa)
        await varrer(f, "matched,unmatched");     // em aberto — a tela nunca pede as duas juntas
      }
    } finally {
      loopAtivo = false;
      fimReplay = true;
      enviar();
      if (repetir) { repetir = false; fimReplay = false; arrancarReplay(); }
    }
  }

  // O content pede o acumulado ao iniciar o robô → re-envia tudo E arranca o replay.
  // A 1ª página pode chegar antes de o content estar ouvindo, por isso o re-envio.
  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (!d || !d.__sharpenupBDAReq) return;
    pedido = true;
    if (typeof d.dias === "number" && d.dias > 0) diasPedidos = d.dias;
    // ⚠ DESTRAVA A SEGUNDA RODADA. `fimReplay` latchava em `true` para sempre: rodar o robô
    // outra vez na mesma aba devolvia o mesmo acumulado e não varria nada — indistinguível
    // de "a casa não tem mais bilhete". Pedido novo é rodada nova.
    if (!loopAtivo) fimReplay = false;
    enviar();
    arrancarReplay();
  });

  // ── fetch ──
  if (of && !of.__suBDAW) {
    const w = function (...a) {
      const req = (a[0] && typeof a[0] === "object" && a[0].url) ? a[0] : null;
      const url = req ? req.url : a[0];
      const opts = a[1] || {};
      try {
        if (RX.test(String(url))) {
          capturarReq(url, _hdrsToObj(req ? req.headers : opts.headers));
        }
      } catch (e) {}
      return of.apply(this, a).then((r) => {
        // Leitura passiva: aqui ela FUNCIONA (a app é Next.js/axios e não aborta o stream,
        // ao contrário do Angular da Novibet). Ainda assim ela sozinha não basta — a
        // requisição da tela é estreita demais. Quem completa é o replay.
        try {
          if (RX.test(String(url))) r.clone().text().then((t) => forward(url, t)).catch(() => {});
        } catch (e) {}
        return r;
      });
    };
    w.__suBDAW = true;
    window.fetch = w;
  }

  // Corpo de uma resposta XHR respeitando o `responseType`: em `json` ler `responseText`
  // LANÇA `InvalidStateError`, e o passivo morreria em silêncio (lição do nv_inject).
  function _corpoResposta(xhr) {
    try {
      const tipo = xhr.responseType;
      if (tipo === "" || tipo === "text") return xhr.responseText;
      if (tipo === "json") return JSON.stringify(xhr.response);
    } catch (e) {}
    return "";
  }

  // ── XMLHttpRequest ──
  // O app usa axios, que fala XHR: este bloco é o caminho PRINCIPAL aqui, não rede de segurança.
  const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send,
        osh = XMLHttpRequest.prototype.setRequestHeader;
  if (!os.__suBDAW) {
    XMLHttpRequest.prototype.open = function (m, u) { this.__suBDAU = u; this.__suBDAH = {}; return oo.apply(this, arguments); };
    XMLHttpRequest.prototype.setRequestHeader = function (k, v) { try { this.__suBDAH[k] = v; } catch (e) {} return osh.apply(this, arguments); };
    const s = function (body) {
      try {
        if (RX.test(String(this.__suBDAU))) {
          capturarReq(this.__suBDAU, this.__suBDAH);
          this.addEventListener("load", () => {
            try { forward(this.__suBDAU, _corpoResposta(this)); } catch (e) {}
          });
        }
      } catch (e) {}
      return os.apply(this, arguments);
    };
    s.__suBDAW = true;
    XMLHttpRequest.prototype.send = s;
  }
})();
