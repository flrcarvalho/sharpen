// Mundo MAIN (Tivo e Betfast): lê as RESPOSTAS do histórico de apostas e repassa ao content.
//
// DUAS CASAS, UM ARQUIVO. A Betfast (`betfast.bet.br`, s211) é espelho da Tivo: mesmo motor,
// mesmo caminho de API, mesmos nomes de campo — muda o domínio e a cor. Provado antes de
// escrever qualquer linha: `POST /api/game/p/messagetosport` responde 401 nas duas (rota
// inexistente responde 400), e os 50 bilhetes reais da Betfast batem campo a campo com o
// card. Por isso NADA aqui pode depender do host: a URL do replay sai de `location.href` e
// o `RX` casa só o caminho. O harness roda esta mesma fixture pelos dois domínios e compara
// os blocos byte a byte (`casos/betfast.mjs`) — se alguém amarrar o domínio, fica vermelho.
//
// A casa roda o sportsbook v4 da BetConstruct dentro de um IFRAME DE MESMA ORIGEM
// (`<casa>.bet.br/sportsbookv4/…`), e o histórico não sai de um endpoint próprio: sai de um
// PROXY genérico do site, que encaminha mensagens para o motor da casa —
//
//   POST <casa>.bet.br/api/game/p/messagetosport
//   {"name":"gethistory","message":"{\"countOnly\":false,\"language\":33,\"from\":…,\"to\":…}"}
//
// Duas consequências que mandam no desenho deste arquivo:
//
// 1) A MESMA URL serve dezenas de mensagens diferentes (saldo, notificações, tradução…).
//    Filtrar por URL não basta e filtrar pelo corpo do pedido é frágil (nem todo caminho de
//    request expõe o body). Por isso quem decide é a FORMA DA RESPOSTA: só processamos o que
//    vier com `Tickets` em array. Mensagem que não for histórico é ignorada em silêncio.
//
// 2) NÃO HÁ PAGINAÇÃO. Uma única chamada devolve a conta inteira e a própria casa carimba
//    `Count`. Provado ao vivo: `from` de 2020 devolve exatamente os mesmos bilhetes que `from`
//    vazio. Então o "replay" aqui é UMA requisição, não um laço — o fim é autoritativo
//    (`Error:null` + `Tickets.length === Count`), nunca heurística de tempo.
//
//    ⚠ MEDIDO E NÃO RESOLVIDO (s211): a conta da Betfast respondeu `Count: 50` com
//    exatamente 50 bilhetes. Na Tivo o `Count` era 24, então o limite NUNCA foi exercitado
//    num número redondo. Se 50 for teto do servidor e não o total da conta, o fim
//    "autoritativo" acima é falso e o resto do histórico some sem erro nenhum — a família
//    de falha que custou 39 de 61 bilhetes na s179. Enquanto a medição não é feita (rolar
//    a lista até o fim e ver se há algo antes do bilhete mais antigo recebido), o mínimo
//    é NÃO ficar calado: `tetoSuspeito` sobe junto com os bilhetes e o content avisa.
//
// ARMADILHA CONFIRMADA no dado real: `from`/`to` são epoch em MILISSEGUNDOS. Passar em
// SEGUNDOS devolve `Count: 0` com `Error: null` — ou seja, some tudo sem erro nenhum. Toda
// janela de dias tem de ser montada em ms.
//
// O inject NÃO decide nada: entrega os campos crus normalizados. `Result` desconhecido sobe
// como veio; quem traduz é o content.js com o `casas/CASA_TIVO.md`.
(function () {
  const RX = /\/api\/game\/p\/messagetosport/i;   // proxy de mensagens do sportsbook
  const byId = new Map();                          // ID(string) → bilhete normalizado
  let respostas = 0;                               // respostas de HISTÓRICO que o hook viu
  let reqCtx = null;                               // {url, language} de uma requisição real
  let pedido = false;                              // o robô já pediu → pode arrancar o replay
  let loopAtivo = false;                           // trava: um replay por vez
  let fimReplay = false;                           // a casa já entregou a lista completa
  let dias = 0;                                    // janela pedida pelo robô (0 = tudo)
  let tetoSuspeito = false;                        // `Count` redondo: pode ser teto, não total
  const LOG = (...a) => { try { console.log("[SharpenUp tv_inject]", ...a); } catch (e) {} };
  LOG("hook instalado em", location.href);

  const of = window.fetch;                         // fetch ORIGINAL — o replay usa este

  const IDIOMA_PADRAO = 33;                        // pt-BR: mantém mercado/esporte já traduzidos
  const TETO_TENTATIVAS = 3;
  // A partir daqui um `Count` que fecha com o nº de bilhetes deixa de ser prova de conta
  // inteira: 50 é valor de página típico. Abaixo disso (a Tivo respondeu 24) o fim é fim.
  const TETO_ALERTA = 50;

  // ── normalização (BetConstruct → objeto limpo) ────────────────────────────────
  // Dinheiro e odd vêm em unidade normal (Amount 150.0 = R$ 150,00) — NÃO há milésimos aqui.
  const _n = (v) => (typeof v === "number" && isFinite(v) ? v : null);
  const _s = (o) => (o && o.Name ? String(o.Name) : "");

  // O motor mistura DUAS gramáticas de data. Os campos normais são epoch ms UTC
  // (`ActionTime`, `Game.StartTime`). Já o `OfferedOddObject` — que vem de outra parte do
  // backend — serializa string ISO **sem `Z`** ("2026-07-02T00:00:00"). Em JS, `new Date()`
  // de uma string sem offset é lida como hora LOCAL DA MÁQUINA: no Chrome do operador em
  // São Paulo isso somaria 3 h por engano. Forçamos `Z` para ler como UTC, coerente com
  // todo o resto do motor.
  //
  // ⚠ HIPÓTESE DECLARADA, NÃO MEDIDA (s211): que essa string seja UTC é dedução por
  // consistência, não leitura de tela. Nos 4 bilhetes da amostra a escolha só muda o DIA em
  // um (`296275825`, USA x Bósnia: 01/07 se UTC, 02/07 se local) — desempate = abrir o
  // bilhete na casa e ler o horário do jogo. Está travado em `casos/betfast.mjs`.
  function _msISO(s) {
    if (typeof s !== "number" && typeof s !== "string") return null;
    if (typeof s === "number") return isFinite(s) ? s : null;
    const t = Date.parse(/[Zz]|[+-]\d{2}:?\d{2}$/.test(s) ? s : s + "Z");
    return isFinite(t) ? t : null;
  }

  // `ItemType: 6` — ODD OFERECIDA (bet builder promocional da casa). A perna vem com
  // `Game`, `Market`, `Position` e `Sport` TODOS null: sem ler o `OfferedOddObject`, o
  // bloco sai MUDO ("- [perdeu]") e a IA teria de inventar esporte e descrição. Foram 4
  // dos 50 bilhetes da Betfast (8%). A Tivo tem o mesmo buraco — só não tinha amostra.
  //
  // Os rótulos aqui vêm EM INGLÊS ("Soccer", "Match result", "shots on target"): o
  // `language: 33` do pedido não alcança este objeto. Entregamos como estão — traduzir é
  // trabalho da IA com o `MASTER_APOSTAS`, não do inject.
  //
  // NÃO traduzimos `SubItems[].PriceResult`: o enum dele é OUTRO (aparecem 3 e 4, onde o
  // `Items[].Result` usa 2 e 3) e nunca foi cruzado com a tela. O resultado que vale é o
  // do bilhete; inventar um por sub-seleção seria chute.
  function parseOferta(oo) {
    if (!oo) return null;
    const it = (oo.Items || [])[0] || null;
    const g = it && it.Game ? it.Game : null;
    return {
      inicio: _msISO(oo.StartTime) || (g ? _msISO(g.StartTime) : null),
      jogo: g ? String(g.Name || "") : "",
      esporte: it ? _s(it.Sport) : "",          // "Soccer" — inglês, a casa não traduz
      regiao: it ? _s(it.Region) : "",
      campeonato: it ? _s(it.Champ) : "",
      selecoes: ((it && it.SubItems) || []).map((s) => ({
        mercado: _s(s.Market),
        selecao: _s(s.Position),
        odd: _n(s.CoefValue),
      })),
    };
  }

  function parseItem(it) {
    if (!it) return null;
    const g = it.Game || null;
    const og = it.OutrightGame || null;
    const fp = it.FinalPosition || null;
    return {
      oferta: it.ItemType === 6 || it.OfferedOddObject ? parseOferta(it.OfferedOddObject) : null,
      id: it.ID != null ? String(it.ID) : "",
      odd: _n(it.Value),                            // odd DA PERNA, precisão da casa
      tipo: it.ItemType,                            // 0 = normal · 3 = outright
      resultado: it.Result,                         // 0 pendente · 2 ganha · 3 perdida · cru
      esporte: _s(it.Sport),                        // já em pt-BR ("Futebol", "Basquete")
      regiao: _s(it.Region),
      campeonato: _s(it.Champ),
      mercado: _s(it.Market),                       // pode conter placeholder "{p1_r}"
      selecao: _s(it.Position),                     // "Mais de" / "Menos de" / "Casa" / "Sim"
      linha: fp && _n(fp.h) != null ? _n(fp.h) : null,   // 6.5 · -1.5 (handicap)
      hisminus: fp ? !!fp.hisminus : false,
      p1: fp && fp.p1 != null ? fp.p1 : null,       // preenche o "{p1_r}" do mercado (3º quarto)
      jogo: g ? {
        inicio: _n(g.StartTime),                    // epoch ms UTC
        casa: _s(g.Team1),
        fora: _s(g.Team2),
      } : null,
      // Outright (F1, vencedor de torneio): `Game` é null e o mercado é lixo interno
      // ("Free text multiwinner market") — o que vale é o par abaixo.
      outright: og || it.Outright ? {
        selecao: og ? _s(og.Team1) : "",            // "Piastri, Oscar"
        nome: _s(it.Outright),                      // "Grande Prêmio da Hungria Qualificação - Top 3"
        inicio: og ? _n(og.StartTime) : null,
      } : null,
      // ⚠ `Team1Score`/`Team2Score` NÃO são placar: são a estatística do mercado (escanteios,
      // cartões). O placar é `LiveScore`. Entregamos os dois com nomes que não se confundem.
      placar: it.LiveScore || "",
      estat: [_n(it.Team1Score), _n(it.Team2Score)],
      // ⚠ `CalculatedBetAmount` NÃO é stake: é o rateio da stake por perna.
      rateio: _n(it.CalculatedBetAmount),
    };
  }

  function parseTicket(t) {
    if (!t || t.ID == null) return null;
    return {
      id: String(t.ID),
      colocada: _n(t.ActionTime),                   // epoch ms UTC → o content converte p/ BRT
      editada: _n(t.LastEditTime),
      status: t.Status,                             // 5 = em aberto · 10 = liquidado (cru)
      resultado: t.Result,                          // 0 pendente · 2 ganha · 3 perdida (cru)
      stake: _n(t.Amount),
      koef: _n(t.Koef),                             // ODD TOTAL, precisão completa
      winKoef: _n(t.WinKoef),                       // null em aberto — nunca usar como odd
      retorno: _n(t.WinAmount),                     // 0 nas perdidas E nas abertas
      potencial: _n(t.PossibleWin),                 // retorno POTENCIAL (só faz sentido em aberto)
      cashout: !!t.CashOut,
      cashoutPossivel: _n(t.PossibleCashout),
      sistema: !!t.IsSystem,
      bonus: !!t.IsBonus,
      moeda: t.CurrencySTR || "",
      itens: (t.Items || []).map(parseItem).filter(Boolean),
    };
  }

  // Emite SEMPRE hook:true + respostas (heartbeat), mesmo com 0 bilhetes — é o que separa
  // "inject não carregou" de "respondeu e lemos 0" no autodiagnóstico.
  function enviar() {
    const msg = {
      __sharpenupTVData: true, hook: true,
      tickets: Array.from(byId.values()), respostas: respostas, fim: fimReplay,
      tetoSuspeito: tetoSuspeito,
    };
    try { window.postMessage(msg, "*"); } catch (e) {}
    // O sportsbook v4 roda num IFRAME (mesma origem) e é DE LÁ que o gethistory sai — mas o
    // content.js só roda no frame de topo (`all_frames:false`). Sem repassar ao topo, o robô
    // ficaria esperando para sempre uma mensagem que nunca sobe.
    try { if (window.top && window.top !== window) window.top.postMessage(msg, "*"); } catch (e) {}
  }

  // Bilhete que veio SÓ com o identificador (sem Status, sem Result, sem pernas). Existe:
  // 3 dos 25 bilhetes do lote de 26/07 subiram assim, com "Status=undefined" e a lista de
  // seleções vazia — e os mesmos IDs vêm CHEIOS no payload de referência do recon.
  const vazio = (x) => x.status == null && x.resultado == null && !(x.itens || []).length;

  // O mesmo bilhete pode voltar em consultas diferentes: a versão RESOLVIDA vence a ABERTA.
  // E CONTEÚDO vence esqueleto, sempre — sem esta regra o esqueleto ganhava por chegar
  // primeiro: ele não parece "aberto" (status undefined), então a linha de baixo nunca o
  // substituía e o bilhete cheio que chegava depois era descartado em silêncio (s198).
  function guardar(t) {
    const ex = byId.get(t.id);
    if (!ex) { byId.set(t.id, t); return; }
    if (vazio(t)) return;                            // esqueleto nunca sobrescreve
    if (vazio(ex)) { byId.set(t.id, t); return; }    // conteúdo sempre vence esqueleto
    const aberto = (x) => x.status === 5 || x.resultado === 0;
    if (aberto(ex) && !aberto(t)) byId.set(t.id, t);
  }

  // Processa uma resposta. Devolve `true` se era histórico (e a lista veio completa).
  function forward(url, text) {
    if (!RX.test(String(url)) || typeof text !== "string") return false;
    let j;
    try { j = JSON.parse(text); } catch (e) { return false; }
    // É AQUI que separamos o histórico das outras mensagens do mesmo endpoint.
    if (!j || !Array.isArray(j.Tickets)) return false;
    respostas++;
    for (const raw of j.Tickets) {
      const t = parseTicket(raw);
      if (t) guardar(t);
    }
    const completa = !j.Error && (j.Count == null || j.Tickets.length === j.Count);
    // "A conta acabou" e "o servidor cortou no teto" chegam com a MESMA cara: `len == Count`.
    // Não dá para distinguir daqui — mas dá para não fingir certeza. A partir de TETO_ALERTA
    // o fim vira suspeito e o content avisa em vez de dizer "pronto" em silêncio.
    if (completa && typeof j.Count === "number" && j.Count >= TETO_ALERTA) {
      if (!tetoSuspeito) LOG("ATENÇÃO: Count =", j.Count, "— pode ser TETO do servidor, não o total da conta.");
      tetoSuspeito = true;
    }
    LOG("bilhetes na resposta:", j.Tickets.length, "· Count:", j.Count, "· total:", byId.size);
    enviar();
    return completa;
  }

  // ── replay: uma requisição, sem paginação ─────────────────────────────────────
  function corpoHistorico() {
    // Janela de dias → `from`/`to` em MILISSEGUNDOS (segundos devolvem 0 em silêncio).
    const agora = Date.now();
    const msg = {
      countOnly: false,
      language: (reqCtx && reqCtx.language) || IDIOMA_PADRAO,
      from: dias > 0 ? agora - dias * 86400000 : "",
      to: dias > 0 ? agora : "",
    };
    // Sem `result`: a consulta sem filtro traz abertas E resolvidas de uma vez.
    return JSON.stringify({ name: "gethistory", message: JSON.stringify(msg) });
  }

  function urlHistorico() {
    if (reqCtx && reqCtx.url) return reqCtx.url;
    try { return new URL("/api/game/p/messagetosport", location.href).href; } catch (e) { return null; }
  }

  async function arrancarReplay() {
    if (loopAtivo || fimReplay) return;
    const alvo = urlHistorico();
    if (!alvo) return;
    loopAtivo = true;
    try {
      for (let i = 0; i < TETO_TENTATIVAS; i++) {
        let r;
        try {
          r = await of.call(window, alvo, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: corpoHistorico(),
            credentials: "include",
          });
        } catch (e) { LOG("erro no replay:", e && e.message); break; }
        if (!r || !r.ok) { LOG("replay parou · HTTP", r && r.status); break; }
        let completa = false;
        try { completa = forward(r.url || alvo, await r.text()); } catch (e) { break; }
        if (completa) { fimReplay = true; break; }        // fim AUTORITATIVO (a casa carimbou)
      }
    } finally {
      loopAtivo = false;
      fimReplay = true;                                    // não deixa o robô esperando o teto
      enviar();
    }
  }

  // Guarda url + idioma de uma requisição real (o idioma manda nos nomes de mercado/esporte).
  function capturarReq(url, body) {
    if (!RX.test(String(url))) return;
    if (!reqCtx) {
      let lang = null;
      try {
        const o = JSON.parse(String(body || "{}"));
        const m = typeof o.message === "string" ? JSON.parse(o.message) : o.message;
        if (m && m.language != null) lang = m.language;
      } catch (e) {}
      reqCtx = { url: String(url), language: lang };
      LOG("requisição capturada p/ replay · idioma =", lang == null ? "(padrão)" : lang);
    }
    if (pedido) arrancarReplay();
  }

  // O content pede o acumulado ao iniciar o robô → re-envia tudo E arranca o replay. A 1ª
  // resposta chega antes de o content estar ouvindo, por isso o re-envio sob demanda.
  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (!d || !d.__sharpenupTVReq) return;
    pedido = true;
    if (Number(d.dias) > 0) dias = Number(d.dias);
    enviar();
    arrancarReplay();
  });

  // ── fetch ──
  if (of && !of.__suTVW) {
    const w = function (...a) {
      const url = (a[0] && a[0].url) || a[0];
      const opts = a[1] || (a[0] && typeof a[0] === "object" ? a[0] : null);
      try { if (RX.test(String(url))) capturarReq(url, opts && opts.body); } catch (e) {}
      return of.apply(this, a).then((r) => {
        try { if (RX.test(String(url))) r.clone().text().then((t) => forward(url, t)); } catch (e) {}
        return r;
      });
    };
    w.__suTVW = true;
    window.fetch = w;
  }

  // ── XMLHttpRequest (o sportsbook v4 dispara o gethistory por XHR) ──
  const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send;
  if (!os.__suTVW) {
    XMLHttpRequest.prototype.open = function (m, u) { this.__suTVU = u; return oo.apply(this, arguments); };
    const s = function (body) {
      try {
        if (RX.test(String(this.__suTVU))) {
          capturarReq(this.__suTVU, body);
          this.addEventListener("load", () => { try { forward(this.__suTVU, this.responseText); } catch (e) {} });
        }
      } catch (e) {}
      return os.apply(this, arguments);
    };
    s.__suTVW = true;
    XMLHttpRequest.prototype.send = s;
  }
})();
