// Mundo MAIN (só na Bet365): lê as RESPOSTAS de /sportshistoryapi/summary e
// /sportshistoryapi/confirmation (formato texto proprietário `F|00;chave=valor;…|01;…|`) que
// a própria página baixa, e repassa objetos limpos ao content script — para tratar igual às
// outras casas passivas (Betfair/Pinnacle).
//
// A CAPTURA É PASSIVA — POR QUE NÃO HÁ REPLAY NELA: até a v0.6.2 este arquivo re-emitia as
// buscas por conta própria, reaproveitando os headers da requisição que a página tinha feito.
// Não funciona: o header `x-net-sync-term` rotaciona A CADA requisição e o servidor o exige.
// Provado ao vivo na sessão 178, do frame `members.bet365.bet.br` e com a sessão logada:
//   • mesma URL, com os headers da página  → 200 com o payload `F|…`
//   • mesma URL, só com cookie (sem token) → 200 com corpo VAZIO (`len: 0`)
//   • mesma URL, com um token VENCIDO      → HTML da página de 404
// Reconfirmado na s382: a URL colada na barra de endereços da conta logada volta EM BRANCO.
// Quem consegue chamar a API é a PRÓPRIA página → o content script pede ao inject que NAVEGUE
// por rota (location.replace("#/HICO/BSSB/C<bsid>/D1/"), NUNCA `location.hash =` — ver
// `navegarUm`) até a confirmation de cada bilhete, e este arquivo só escuta as respostas.
// Ver docs/PLANO_BET365_CAPTURA_API.md.
//
// ⚠️ **UMA EXCEÇÃO, E SÓ UMA: o "Resolver apostas abertas" (s382).** Lá embaixo há chamada
// ATIVA, e ela funciona porque o token é PEDIDO À PRÓPRIA PÁGINA (`_pedirTermo`) em vez de
// reaproveitado. É o mecanismo anti-automação da casa, e usá-lo foi decisão explícita do dono
// da conta, tomada com os dois caminhos na mesa. A captura normal segue passiva, e a linha
// entre as duas coisas é para ser mantida: o que a extração faz continua sendo escutar.
//
// DUAS COISAS ELE DIRIGE (o resto é escuta pura): expande a lista clicando "Mostrar Mais" até o
// fim (`expandirLista`, s279 — era o último gesto manual da casa) e navega por rota (sempre com
// `location.replace`) até a confirmação de cada bilhete (`detalharPorRota`, s180). Nenhuma das duas chama a API por
// conta própria — quem chama é sempre a página, com o token dela.
//
// POR QUE PRECISA DO DETALHE: o `summary` NÃO traz jogo/mercado/liga nem o código `BR` — só a
// seleção crua, odd, stake, retorno, o esporte (`CL`) e as pernas de bet builder. O
// `confirmation?bsid=` completa.
//
// DEDUP: a chave estável é o `BR` (código do comprovante — do confirmation). O `ID` numérico do
// summary MUDA quando a aposta resolve (namespace D1→D0), então serve só de `bsid` para buscar o
// detalhe na mesma visão.
(function () {
  const RX_SUM = /\/sportshistoryapi\/summary/i;
  const RX_CONF = /\/sportshistoryapi\/confirmation/i;
  const byBsid = new Map();       // bsid(string) → bilhete mesclado (summary + confirmation)
  let respostas = 0;              // respostas de summary/confirmation que o hook viu (autodiagnóstico)
  let outrasHistory = 0;          // requisições com "history" no path que NÃO casaram os regex —
                                  // se isto for >0 com `respostas`=0, o endpoint mudou de nome.
  const LOG = (...a) => { try { console.log("[SharpenUp b3_inject]", ...a); } catch (e) {} };
  LOG("hook instalado em", location.href);

  // ── GRAVADOR DA EXTRAÇÃO (diagnóstico) ────────────────────────────────────────
  // Carimba cada evento da captura com hora e STATUS HTTP, e SOBREVIVE ao "reconectar"
  // (persiste no localStorage desta origem). Existe para responder onde o tempo vai numa
  // extração grande: quanto é expansão, quanto é detalhe, e em que instante exato a casa
  // começa a recusar — 500, corpo vazio ou timeout são três causas diferentes e hoje o robô
  // não distingue nenhuma. Medido antes dele existir: 26 bilhetes limpos a 2,0s e depois
  // UMA resposta em 230s, sem ninguém saber o porquê.
  //
  // NUNCA decide nada: só observa, sempre dentro de try/catch. Zera com `acao:"limpar"`.
  const REC_KEY = "__sharpenupB3Rec";
  const REC_MAX = 4000;           // ~320 KB de JSON; o teto do localStorage é 5 MB
  let rec = [];
  try { const b = localStorage.getItem(REC_KEY); if (b) rec = JSON.parse(b) || []; } catch (e) { rec = []; }
  let recSujo = false;
  function gravar(tipo, d) {
    try {
      const ev = { t: Date.now(), tipo: tipo };
      if (d) for (const k in d) if (d[k] !== undefined) ev[k] = d[k];
      rec.push(ev);
      if (rec.length > REC_MAX) rec.splice(0, rec.length - REC_MAX);
      recSujo = true;
    } catch (e) {}
  }
  // Salva em LOTE (1 escrita a cada 2s). Por evento seria uma serialização do buffer inteiro
  // a cada requisição, e aí o gravador viraria parte do gargalo que ele veio medir.
  //
  // ⚠️ `setInterval` NÃO existe no sandbox do harness (só `setTimeout`), e chamá-lo solto
  // derrubava o arquivo inteiro na carga — o caso Bet365 foi de 471 bilhetes para exceção.
  // Persistência é conveniência do gravador; a captura não pode cair por causa dela.
  try {
    if (typeof setInterval === "function") {
      setInterval(() => {
        if (!recSujo) return;
        recSujo = false;
        try { localStorage.setItem(REC_KEY, JSON.stringify(rec)); } catch (e) {}
      }, 2000);
    }
  } catch (e) {}

  const of = window.fetch;        // fetch ORIGINAL (o wrapper embrulha este)

  // ── parser do formato F|… ──────────────────────────────────────────────────────
  function parseRecords(blob) {
    const recs = [];
    for (const chunk of String(blob || "").split("|")) {
      const c = chunk.trim();
      if (!c || c === "F") continue;
      const parts = c.split(";");
      const kv = {};
      for (let i = 1; i < parts.length; i++) {
        const p = parts[i];
        const eq = p.indexOf("=");
        if (eq > -1) kv[p.slice(0, eq)] = p.slice(eq + 1);
      }
      recs.push([parts[0], kv]);
    }
    return recs;
  }

  // summary → { cursor:PT, bets:[{bsid,bs,stake,oddFrac,rt,tipo,bc,bt,sels}] }
  // Registros: 00 header (PT=cursor) · 01 bilhete · 03 seleção · 04 perna de BET BUILDER
  // (mesmo jogo: NA=seleção, N2=mercado) · 02 TY=SD/ST (stake/retorno).
  //
  // ⚠️ BC e BT são a ESTRUTURA do bilhete e sem eles um sistema é indistinguível de uma múltipla:
  //   BC = nº de APOSTAS (linhas) · BT = seleções por aposta · NA = o rótulo ("Duplas"/"Triplas")
  //   ST (no TY=SD) = stake UNITÁRIO (por linha) · TS = stake TOTAL (= ST × BC)
  // `3 x Duplas` (BC=3, BT=2) e a tripla das MESMAS 3 seleções (BC=1, BT=3) chegam com as mesmas
  // odds e o mesmo NA-ish; só BC/BT separam. Ver `_linhasSistemaB3` no content.js (s265).
  function parseSummary(blob) {
    const recs = parseRecords(blob);
    let cursor = null;
    const bets = [];
    let cur = null;
    for (const [code, kv] of recs) {
      if (code === "00") { if (kv.PT) cursor = kv.PT; continue; }
      if (code === "01") {
        if (cur) bets.push(cur);
        cur = { bsid: kv.ID || "", bs: kv.BS, tp: kv.TP || "", pd: kv.PD || "", sels: [],
                stake: null, ts: null, oddFrac: "", rt: null, tipo: "",
                bc: kv.BC || "", bt: kv.BT || "" };
      } else if (code === "03" && cur) {
        // `na` é a seleção; quando vierem pernas 04 depois, esse mesmo `na` é o JOGO
        // (bet builder). Quem decide é o formatador, olhando se `subs` tem item.
        cur.sels.push({ na: kv.NA || kv.FN || "", od: kv.OD || "", cl: kv.CL || "", subs: [] });
        if (!cur.oddFrac) cur.oddFrac = kv.OD || "";
      } else if (code === "04" && cur && cur.sels.length && "NA" in kv) {
        // Bet builder: cada 04 é uma perna do MESMO jogo da seleção 03 anterior. Sem isto o
        // bilhete sai "reduzido" — só o nome do jogo, sem os mercados (bug visto na s178).
        cur.sels[cur.sels.length - 1].subs.push({ na: kv.NA || "", mercado: kv.N2 || "" });
      } else if (code === "02" && cur) {
        // TY=SD é o registro mais confiável da estrutura (BC/BT vêm aqui E no `01`; o `01` de
        // alguns bilhetes vem sem BC). `cur.stake` = ST do SD = stake UNITÁRIO, não o total.
        if (kv.TY === "SD") {
          if ("ST" in kv) cur.stake = kv.ST;
          if ("TS" in kv) cur.ts = kv.TS;
          cur.tipo = kv.NA || "";
          if (kv.BC) cur.bc = kv.BC;
          if (kv.BT) cur.bt = kv.BT;
        }
        else if (kv.TY === "ST") {
          if ("RT" in kv) cur.rt = kv.RT;                 // ausente = aberta
          if (cur.stake == null && "ST" in kv) cur.stake = kv.ST;
        }
      }
    }
    if (cur) bets.push(cur);
    return { cursor, bets };
  }

  // confirmation → { br, da, bs, tipo, rt, ts, legs:[{sel,oddFrac,kickoff,cl,liga,jogo,mercado,subs}] }
  // Estrutura REAL (payload capturado na s178, não a suposta):
  //   00           cabeçalho — BR (código), DA (colocação), BS, NA (tipo)
  //   02 (com NA)  EVENTO/perna — NA=seleção (ou o jogo, em bet builder), FN=jogo, L3=liga,
  //                MN=mercado, TP=kickoff, CL=esporte, OD=odd
  //   03 (com NA)  perna do BET BUILDER dentro do 02 anterior — NA=seleção, N2=mercado
  //   01 TY=CS     linha final — RT (retorno) e TS (stake total)
  //   01 TY=DI     início do bloco KYC (nome, endereço, CPF) → IGNORAR daqui pra frente
  function parseConfirmation(blob) {
    const recs = parseRecords(blob);
    if (!recs.length) return null;
    const head = recs[0][1];
    // Guarda: sem `BR` no cabeçalho não é um confirmation (é HTML de erro/404, por exemplo).
    // Sem esta checagem o parser devolvia um objeto com código VAZIO e o bilhete subia sem
    // chave de dedup, silenciosamente — foi assim que o replay quebrado passou despercebido.
    if (!head || !("BR" in head)) return null;
    // BC/BT também no cabeçalho `00` (redundância boa: se um bilhete vier sem eles no summary,
    // o confirmation completa). NUNCA ler BC do `01;TY=CS` — lá ele vem VAZIO (`BC=;`).
    const out = { br: head.BR || "", da: head.DA || "", bs: head.BS, tipo: head.NA || "",
                  bc: head.BC || "", bt: head.BT || "", rt: null, ts: null, legs: [] };
    let sensivel = false;   // depois de 01;TY=DI vêm dados pessoais — nunca viram perna
    let atual = null;
    for (const [code, kv] of recs) {
      if (kv.TY === "CS") { if ("RT" in kv) out.rt = kv.RT; if ("TS" in kv) out.ts = kv.TS; }
      if (code === "01" && kv.TY === "DI") { sensivel = true; atual = null; continue; }
      if (sensivel) continue;
      if (code === "02" && "NA" in kv && !("VA" in kv)) {
        atual = { sel: kv.NA || "", oddFrac: kv.OD || "", kickoff: kv.TP || "",
                  cl: kv.CL || "", liga: kv.L3 || "", jogo: kv.FN || "",
                  mercado: kv.MN || "", subs: [] };
        out.legs.push(atual);
      } else if (code === "03" && atual && "NA" in kv) {
        atual.subs.push({ na: kv.NA || "", mercado: kv.N2 || "" });
      }
    }
    return out;
  }

  // ── emissão ao content ─────────────────────────────────────────────────────────
  // A área de membros da Bet365 roda em OUTRA origem (`members.bet365.bet.br`) — na prática,
  // num iframe dentro da página que o usuário vê. O `b3_inject` roda em todos os frames
  // (`all_frames`), mas o `content.js` só existe no TOP → postar só na própria window deixaria
  // o inject do iframe gritando para dentro do iframe, sem ninguém ouvindo (sintoma: "Hook
  // ATIVO · respostas 0"). Por isso emitimos na própria window E no topo (postMessage
  // cross-origin é permitido). `href`/`topo` identificam o frame no autodiagnóstico.
  // `fim` = o driver deste frame terminou de abrir os detalhes (fim autoritativo, evita o
  // robô ficar esperando o timeout de inatividade). `driver` = contadores p/ o log do content.
  function enviar(fim, driver) {
    const msg = { __sharpenupB3Data: true, hook: true, href: location.href,
                  topo: window.top === window, bets: Array.from(byBsid.values()),
                  respostas: respostas, history: outrasHistory,
                  fim: !!fim, driver: driver || null };
    try { window.postMessage(msg, "*"); } catch (e) {}
    try { if (window.top && window.top !== window) window.top.postMessage(msg, "*"); } catch (e) {}
  }

  // ── captura passiva das respostas (summary/confirmation que a página faz) ───────
  function forward(url, text) {
    const u = String(url);
    if (RX_SUM.test(u)) {
      // Referência para as chamadas ATIVAS do "Resolver apostas abertas": é daqui que saem
      // `lid`/`cid`/`csid` (variam por país) e o ORIGIN certo — a lista mora no `members`,
      // e este inject roda em todos os frames.
      ultimaUrlSummary = u;
      try { const rs = parseRecords(text); catalogarCampos("summary", rs); amostrar01(u, rs); } catch (e) {}   // diagnóstico, não decide nada
      const r = parseSummary(text);
      if (!r || !r.bets.length) return false;
      respostas++;
      const settled = /settled=1/i.test(u);
      for (const b of r.bets) if (b.bsid) mergeSummary(b, settled);
      enviar();
      return true;
    }
    if (RX_CONF.test(u)) {
      const bsid = _param(u, "bsid");
      try { catalogarCampos("confirmation", parseRecords(text)); } catch (e) {}   // diagnóstico
      const c = parseConfirmation(text);
      if (!c) { LOG("confirmation sem BR (resposta inválida) · bsid", bsid); return false; }
      respostas++;
      if (bsid) mergeConf(bsid, c);
      // DIAGNÓSTICO (s180): descobrir se dá pra abrir a confirmação por ROTA/ID, pulando a lista
      // e o "Mostrar Mais" quebrado. Loga a rota do frame + a URL da API no momento em que a
      // confirmação abre. Se a rota carregar o bsid, o robô navega direto em cada bilhete.
      LOG("CONFIRM abriu · bsid=" + bsid + " · code=" + (c.br || "") + " · rota=" + location.href + " · api=" + String(u).slice(0, 220));
      enviar();
      return true;
    }
    return false;
  }

  function mergeSummary(b, settled) {
    const ex = byBsid.get(b.bsid) || { bsid: b.bsid };
    ex.aberta = b.bs === "0";
    ex.tp = b.tp; ex.stake = b.stake; ex.ts = b.ts; ex.oddFrac = b.oddFrac; ex.rt = b.rt; ex.tipo = b.tipo;
    ex.sels = b.sels;
    if (b.bc) ex.bc = b.bc;
    if (b.bt) ex.bt = b.bt;
    if (b.pd) ex.pd = b.pd;   // rota da confirmation — o namespace (D0/D1) vem daqui, não de chute
    byBsid.set(b.bsid, ex);
  }
  function mergeConf(bsid, c) {
    const ex = byBsid.get(bsid) || { bsid: bsid };
    ex.code = c.br; ex.da = c.da; ex.legs = c.legs;
    if (c.ts != null) ex.ts = c.ts;
    if (c.rt != null && ex.rt == null) ex.rt = c.rt;   // não sobrescreve o RT do summary (realizado)
    if (!ex.tipo) ex.tipo = c.tipo;
    if (!ex.bc && c.bc) ex.bc = c.bc;
    if (!ex.bt && c.bt) ex.bt = c.bt;
    if (c.bs != null) ex.aberta = c.bs === "0";
    byBsid.set(bsid, ex);
  }

  function _param(u, k) { try { return new URL(u, location.origin).searchParams.get(k) || ""; } catch (e) { return ""; } }

  // Diagnóstico: requisição com "history" no path que NÃO é o summary/confirmation esperado.
  // Se virem `respostas=0` mas `history>0`, o endpoint foi renomeado — o log guarda a URL real
  // e o conserto vira ajuste de regex, sem mais uma rodada às cegas.
  function contarHistory(url) {
    const u = String(url || "");
    if (!/history/i.test(u) || RX_CONF.test(u)) return;
    outrasHistory++;
    if (outrasHistory <= 5) LOG("URL com 'history' fora do padrão:", u.slice(0, 200));
  }

  // ── CATÁLOGO DE ROTAS (diagnóstico sob demanda) ───────────────────────────────
  // A pergunta que ele existe para responder: a casa tem alguma rota que devolva o DETALHE de
  // vários bilhetes de uma vez? Hoje é UMA `confirmation` por bilhete, e a casa corta o acesso
  // depois de ~26 seguidas (medido: 26 limpas a 2,0s, depois 1 resposta em 230s). Com corte por
  // COTA, apertar o ritmo e paralelizar não ganham nada — o único ganho possível é fazer MENOS
  // requisições. E só este arquivo pode responder: a origem `members` se recusa a rodar fora do
  // iframe (redireciona para o wrapper) e nenhuma ferramenta de fora enxerga a rede dela.
  //
  // Guarda a FORMA (path + NOMES dos parâmetros), nunca os valores: valor carrega bsid, conta e
  // sessão, e o que se procura é o desenho da rota. Só responde quando perguntado (`acao:"rotas"`),
  // então o caminho quente da captura fica intocado.
  const rotas = new Map();          // "path?a,b,c" → { n, metodo }
  const CAT_MAX = 200;              // teto de formas distintas
  function catalogar(url, metodo) {
    try {
      const u = new URL(String(url || ""), location.origin);
      if (u.hostname !== location.hostname) return;      // só a própria casa
      const ps = Array.from(u.searchParams.keys()).sort().join(",");
      const chave = u.pathname + (ps ? "?" + ps : "");
      const ex = rotas.get(chave);
      if (ex) { ex.n++; return; }
      if (rotas.size >= CAT_MAX) return;
      rotas.set(chave, { n: 1, metodo: metodo || "GET" });
    } catch (e) {}
  }
  // ── INVENTÁRIO DE CAMPOS (mesmo diagnóstico) ──────────────────────────────────
  // O parser lê SEIS campos do registro `01` do summary (ID, BS, TP, PD, BC, BT) e descarta o
  // resto sem nunca ter olhado o que era. A pergunta que isto responde: o summary já traz algo
  // que dispense a `confirmation` de bilhete que já está no banco? Ele já dá status e retorno;
  // se trouxer também identidade estável, a varredura de resolvidas (que reordena por data de
  // COLOCAÇÃO, e por isso obriga a revarrer a janela inteira) fica quase de graça.
  //
  // Guarda só os NOMES dos campos, nunca os valores.
  const campos = new Map();         // "summary·01" → Set de nomes
  const CAMPOS_MAX = 40;            // pares endpoint·registro distintos
  function catalogarCampos(tag, recs) {
    for (const [code, kv] of recs) {
      const chave = tag + "·" + code;
      let s = campos.get(chave);
      if (!s) { if (campos.size >= CAMPOS_MAX) continue; s = new Set(); campos.set(chave, s); }
      for (const k in kv) if (s.size < 60) s.add(k);
    }
  }

  // ── AMOSTRA DO REGISTRO DE BILHETE (`01` do summary) ──────────────────────────
  // Responde UMA pergunta: existe campo ESTÁVEL entre visões? A memória `b3Detalhes` é indexada
  // pelo `ID`, e o `ID` é da VISÃO, não da aposta (24h vem `D1`, 48h/Período vem `D0`). Então a
  // MESMA aposta vista em dois filtros é duas apostas para a memória, e paga `confirmation` duas
  // vezes. Medido na conta do Feca: `alvos 1038 · pulados 0` num período onde ~95% já estava no
  // banco. Se `RA`, `UP` ou `UW` (três campos que o parser nunca leu) forem iguais nas duas
  // visões, a memória troca de chave e o desperdício acaba.
  //
  // ⚠️ SÓ o registro `01` do summary, que é nível de BILHETE: id e estrutura, sem nome de
  // seleção. Os registros 02/03/04 trazem seleção e a `confirmation` tem um bloco KYC
  // (`01;TY=DI`) com nome, endereço e CPF. Nada disso entra aqui, em hipótese nenhuma.
  const amostra01 = [];
  const AM_MAX = 60;
  function amostrar01(url, recs) {
    try {
      if (amostra01.length >= AM_MAX) return;
      const u = String(url);
      const marca = { _settled: _param(u, "settled"), _from: _param(u, "from") || "" };
      let n = 0;
      for (const [code, kv] of recs) {
        if (code !== "01") continue;
        if (n++ >= 6) break;                        // 6 bilhetes por resposta bastam
        if (amostra01.length >= AM_MAX) break;
        amostra01.push(Object.assign({}, marca, kv));
      }
    } catch (e) {}
  }

  // ── "Resolver apostas abertas": buscar na LISTA, por carimbo ──────────────────
  //
  // ⚠️ **CHAMADA ATIVA — a única do arquivo.** Funciona porque o token é pedido à própria
  // página (`_pedirTermo`); requisição sem ele devolve 200 com corpo vazio. É o mecanismo
  // anti-automação da casa, e a decisão de usá-lo foi do dono da conta, com o caminho
  // alternativo (dirigir a tela) medido e na mesa: 4× mais lento e com MAIS requisições.
  //
  // Nada aqui participa da captura: usa o fetch original, não toca no `byBsid` e não
  // dispara `enviar()`. E nada aqui ESCREVE — quem decide gravar é o servidor, depois das
  // travas do §7 do plano.
  //
  // Desenho em `docs/PLANO_RESOLVER_ABERTAS.md`. Medido no F12 em 23/09, conta real:
  //
  //   GET /sportshistoryapi/summary?settled=1&from=<ISO>&to=<ISO>&lid=33&cid=28
  //
  // • a lista vem ORDENADA por `TP` decrescente e a página é de **10 bilhetes**;
  // • o `to` é INCLUSIVO e é o CURSOR: a página seguinte repete a chamada com `to` = o
  //   carimbo do último bilhete recebido. Cada "Mostrar Mais" da tela é uma requisição.
  //
  // A consequência é que o cursor é um ENDEREÇO: pedir `to` perto do carimbo da aposta
  // procurada a traz na primeira página, com as anteriores de graça. Não é varredura.
  let ultimaUrlSummary = "";     // preenchida pelo hook — ver `forward`

  const FOLGA_CEGA_H = 3;        // só quando o fuso NÃO pôde ser lido — ver `_offsetUK`
  const JANELA_ABAIXO_H = 27;    // 24h + a folga cega: onde parar quando o casamento falha
  const PAGINA = 10;             // medido; serve só para saber que "cheia" não é "fim"
  const MAX_PAGINAS = 40;        // teto duro de segurança, NUNCA o critério de parada

  function _msDoCarimbo(c) {
    const m = /^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})/.exec(String(c || ""));
    if (!m) return NaN;
    return Date.UTC(+m[1], +m[2] - 1, +m[3], +m[4], +m[5], +m[6]);
  }

  // ── O FUSO, LIDO DA CASA EM VEZ DE ADIVINHADO ─────────────────────────────────
  // O carimbo (`TP`/`DA`) é hora LOCAL DO REINO UNIDO e o `from`/`to` da API é UTC. Este
  // projeto vinha supondo o horário de verão britânico (`_ehBST`, no content) e marcava a
  // suposição como "assumida, não medida" desde a s373 — e errar por uma hora faz a aposta
  // não aparecer, sem erro nenhum.
  //
  // A página publica o ajuste: `Locator.user.timeZoneAdjustment` é UK → hora local do
  // usuário, em MINUTOS (medido: −240 em BST com o usuário em GMT-3). Somando o offset
  // local → UTC do próprio navegador, sai UK → UTC sem supor nada:
  //
  //     UK + tza                      = local
  //     local + getTimezoneOffset()   = UTC
  //     ⇒ UK → UTC = tza + getTimezoneOffset()
  //     (−240 + 180 = −60 min = −1h, que é BST. No inverno: −180 + 180 = 0, que é GMT.)
  //
  // `getTimezoneOffset` é chamado NA DATA DO CARIMBO, não em hoje: onde o fuso local tem
  // horário de verão, o de hoje descreveria outro dia.
  function _offsetUK(msCarimbo) {
    try {
      // `window.Locator`, nunca o global solto: fora do navegador (harness) o global não
      // existe e o `try` engoliria a ausência como "sem fuso", deixando o teste medir a
      // janela cega em vez do caminho real.
      const L = window.Locator;
      const tza = L && L.user && L.user.timeZoneAdjustment;
      if (typeof tza === "number" && isFinite(tza)) {
        return { min: tza + new Date(msCarimbo).getTimezoneOffset(), medido: true };
      }
    } catch (e) {}
    return { min: 0, medido: false };
  }

  // A janela que se pede à casa para UM carimbo. Com o fuso lido, ela é de 1 SEGUNDO e a
  // resposta traz exatamente aquela aposta (`from` inclusivo, `to` EXCLUSIVO — medido por
  // tentativa com milissegundos). Sem o fuso, abre a folga cega e o laço pagina até achar;
  // em nenhum dos dois casos o casamento afrouxa, porque quem decide é `TP === carimbo`.
  function _janelaDoCarimbo(ms) {
    const off = _offsetUK(ms);
    const base = ms + off.min * 60e3;
    if (off.medido) return { de: base, ate: base + 1000, cega: false };
    return { de: base - JANELA_ABAIXO_H * 3600e3, ate: base + FOLGA_CEGA_H * 3600e3, cega: true };
  }

  // ── O TOKEN QUE A CASA EXIGE, pedido à PRÓPRIA PÁGINA ─────────────────────────
  // Requisição sem `X-Net-Sync-Term` devolve **200 com corpo VAZIO** — medido na s178 e
  // reconfirmado na s382 (a URL colada na barra de endereços da conta logada volta em
  // branco). O termo é de uso único e assinado SOBRE A URL: reaproveitar um capturado
  // também devolve vazio.
  //
  // O mecanismo que o gera está exposto no `window` do frame de membros: escreve-se a URL
  // alvo em `ns_gen5_net.url`, dispara-se `xcftr` com um id, e o termo volta no evento
  // `xcft<id>`. Por isso este caminho **só funciona no frame `members`, no mundo MAIN**.
  //
  // ⚠️ É o mecanismo ANTI-AUTOMAÇÃO da casa, e usá-lo foi decisão explícita do dono da
  // conta. Se ela renomear qualquer uma dessas peças, a resposta passa a vir **vazia, sem
  // erro** — que é o MESMO sintoma de "não há aposta nesse segundo". É essa confusão que o
  // gate de controle (`_conferirMecanismo`) existe para impedir.
  const TERMO_TIMEOUT = 4000;

  function _pedirTermo(urlRelativa) {
    return new Promise((resolve) => {
      let g;
      try { g = window.ns_gen5_net; } catch (e) { g = null; }
      if (!g) return resolve(null);
      const id = 100000 + Math.floor(Math.random() * 1e6);
      let pronto = false;
      const fim = (v) => { if (!pronto) { pronto = true; try { g.url = ""; } catch (e) {} resolve(v); } };
      const t = setTimeout(() => fim(null), TERMO_TIMEOUT);
      try {
        window.addEventListener("xcft" + id, (ev) => { clearTimeout(t); fim(ev && ev.detail); },
                                { once: true });
        g.url = urlRelativa;
        g.body = "";
        window.dispatchEvent(new CustomEvent("xcftr", { detail: id }));
      } catch (e) { clearTimeout(t); fim(null); }
    });
  }

  function _urlSummary(settled, msDe, msAte) {
    // A base sai da ÚLTIMA chamada que a PRÓPRIA página fez: é de lá que vêm `lid`/`cid`/
    // `csid` (variam por país) e, sobretudo, o ORIGIN certo — este inject roda em todos os
    // frames, e a lista mora no `members`, não no `www`. Sem essa referência a gente não
    // chuta: devolve erro pedindo para abrir o histórico uma vez.
    if (!ultimaUrlSummary) return null;
    let u;
    try { u = new URL(ultimaUrlSummary, location.origin); } catch (e) { return null; }
    const p = new URLSearchParams();
    p.set("settled", settled ? "1" : "0");
    p.set("from", new Date(msDe).toISOString());
    p.set("to", new Date(msAte).toISOString());
    for (const k of ["lid", "cid", "csid"]) {
      const v = u.searchParams.get(k);
      if (v != null && v !== "") p.set(k, v);
    }
    return u.origin + u.pathname + "?" + p.toString();
  }

  async function _paginaSummary(settled, msDe, msAte) {
    const url = _urlSummary(settled, msDe, msAte);
    // `chamou:false` não é detalhe de contagem: RECUSAR É NÃO CHAMAR. Uma URL chutada
    // devolveria 404 e o erro pareceria o mesmo, e aí ninguém distingue "não sei o
    // endereço" de "a casa não tem esse bilhete".
    if (!url) return { erro: "sem referência de URL — abra o Histórico uma vez antes", chamou: false };
    // ⚠️ `of` é o fetch ORIGINAL, guardado ANTES do hook — e não é detalhe de estilo. O
    // `window.fetch` daqui está embrulhado pelo `forward`, que joga tudo o que passa dentro
    // do `byBsid` da captura e chama `enviar()`. Buscar por carimbo com ele contaminaria a
    // extração em curso com bilhetes que ninguém pediu, e o operador veria a contagem subir
    // sozinha. A busca observa a casa; ela não participa da captura.
    // O termo é assinado sobre a URL **relativa**, que é o que a página escreve em
    // `ns_gen5_net.url`. Mandar a absoluta aqui devolve termo válido e resposta vazia.
    let rel = url;
    try { const u = new URL(url, location.origin); rel = u.pathname + u.search; } catch (e) {}
    const termo = await _pedirTermo(rel);
    if (!termo) {
      return { erro: "o mecanismo de token não respondeu (frame errado, ou a casa mudou)",
               chamou: false, semTermo: true };
    }
    const cab = { "X-Net-Sync-Term": termo };
    try { const L = window.Locator; if (L && L.Guid) cab["X-Request-Id"] = L.Guid; } catch (e) {}
    const r = await of.call(window, url, { credentials: "include", headers: cab });
    if (!r.ok) return { erro: "HTTP " + r.status };
    const txt = await r.text();
    // ⚠️ CORPO VAZIO NÃO É "NÃO EXISTE". É o que a casa devolve quando o termo não serve —
    // e também o que ela devolve quando realmente não há aposta naquela janela. Os dois
    // casos têm exatamente o mesmo sintoma, então quem chama NÃO pode concluir daqui:
    // é o `_conferirMecanismo` que desempata, com uma aposta que sabemos existir.
    const parsed = parseSummary(txt);
    return { bets: (parsed && parsed.bets) || [], vazio: !String(txt || "").trim(),
             // DIAGNÓSTICO (s382): `status` e `len` são o que separa as DUAS causas de uma
             // resposta vazia, que de fora são idênticas — token recusado (a casa devolve
             // 200 com corpo 0) e janela no lugar errado (200 com só o cabeçalho, ~60
             // bytes). Sem isso, consertar vira adivinhação, e já foram cinco defeitos.
             status: r.status, len: String(txt || "").length, url: url };
  }

  /** Acha, na lista da casa, os bilhetes dos `carimbos` pedidos. Não escreve nada. */
  async function buscarPorCarimbos(carimbos, settled) {
    const alvos = Array.from(new Set((carimbos || []).map(String)))
      .filter((c) => !isNaN(_msDoCarimbo(c)))
      .sort().reverse();                       // do mais recente para o mais antigo
    const achados = new Map();                 // carimbo(14) → bilhete da casa
    const vistos = new Map();                  // bsid → bilhete (tudo o que passou)
    let paginas = 0, chamadas = 0, erro = "", cegas = 0, vazias = 0, semTermo = false;
    let amostra = null;   // a 1ª resposta da casa, inteira — ver o log

    for (const alvo of alvos) {
      if (achados.has(alvo)) continue;         // veio de graça numa página anterior
      const msAlvo = _msDoCarimbo(alvo);
      // Com o fuso lido da casa esta janela tem 1 SEGUNDO e a 1ª página já traz a aposta;
      // sem ele, abre a folga cega e o laço abaixo pagina. O casamento não muda nos dois.
      const jan = _janelaDoCarimbo(msAlvo);
      let cursor = jan.ate;
      const piso = jan.de;
      if (jan.cega) cegas++;
      while (paginas < MAX_PAGINAS) {
        const r = await _paginaSummary(settled, piso, cursor);
        if (r.chamou !== false) chamadas++;
        // Guarda a PRIMEIRA resposta inteira para o log. Uma basta: se a 1ª voltou vazia,
        // as 19 seguintes voltaram pelo mesmo motivo.
        if (!amostra && r.chamou !== false) {
          amostra = { status: r.status, len: r.len, bets: (r.bets || []).length, url: r.url };
        }
        if (r.semTermo) semTermo = true;
        if (r.erro) { erro = r.erro; break; }
        paginas++;
        if (r.vazio) vazias++;
        const bets = r.bets;
        let menorMs = Infinity;
        for (const b of bets) {
          if (b.bsid) vistos.set(String(b.bsid), b);
          const c14 = String(b.tp || "").slice(0, 14);
          if (c14) achados.set(c14, b);
          const ms = _msDoCarimbo(c14);
          if (!isNaN(ms) && ms < menorMs) menorMs = ms;
        }
        if (achados.has(alvo)) break;          // achou o que procurava
        // ── AS TRÊS ARMADILHAS DA PAGINAÇÃO POR TEMPO ────────────────────────────
        // 1. Página CHEIA não é fim, e página curta é: só `bets.length < PAGINA` encerra.
        if (bets.length < PAGINA) break;
        // 2. O cursor pode TRAVAR: se o menor carimbo da página não é menor que o cursor
        //    (dois bilhetes no mesmo segundo — 2,03% dos bilhetes compartilham carimbo),
        //    repetir a chamada devolveria a mesma página para sempre. Empurra 1 segundo.
        const proximo = (menorMs < cursor) ? menorMs : (cursor - 1000);
        // 3. E abaixo do piso não há mais o que procurar: a aposta não está nesta janela.
        if (proximo < piso) break;
        cursor = proximo;
      }
      if (erro) break;
    }
    // A fronteira REPETE um item por página (o do carimbo igual ao `to`), então contar
    // "quantos vieram" conta a mais. Quem responde é o mapa por bsid, não a soma.
    return { achados: achados, vistos: vistos, paginas: paginas, chamadas: chamadas,
             erro: erro, cegas: cegas, vazias: vazias, semTermo: semTermo,
             amostra: amostra };
  }

  // ── O GATE DA FALHA SILENCIOSA ────────────────────────────────────────────────
  // Corpo vazio significa DUAS coisas que não se distinguem pela resposta: "não há aposta
  // nessa janela" e "o token não serve mais". A segunda acontece sozinha, no dia em que a
  // casa renomear qualquer peça do mecanismo — e aí o botão passaria a dizer "todas ainda
  // abertas" para sempre, sem erro em lugar nenhum.
  //
  // O desempate é uma aposta que o SERVIDOR sabe que existe e já está resolvida: se nem
  // ela aparece, não é a casa que está vazia, é o mecanismo que quebrou.
  //
  // ⚠️ Só se consulta o controle quando ALGUMA busca voltou vazia — senão seria uma
  // requisição a mais por rodada, contra o teto de volume, para confirmar o que já se sabe.
  async function _conferirMecanismo(controle) {
    const ms = _msDoCarimbo(controle && controle.carimbo);
    if (isNaN(ms)) return { ok: null, motivo: "sem aposta de controle", chamadas: 0 };
    const jan = _janelaDoCarimbo(ms);
    const r = await _paginaSummary(true, jan.de, jan.ate);
    // A conferência é uma ida à casa como qualquer outra, e conta contra o mesmo teto de
    // volume. Deixá-la fora do total faz o relatório mentir sobre o custo da rodada.
    const gasto = r.chamou === false ? 0 : 1;
    if (r.erro) return { ok: false, motivo: r.erro, chamadas: gasto };
    const achou = (r.bets || []).some(
      (b) => String(b.tp || "").slice(0, 14) === String(controle.carimbo).slice(0, 14));
    return { ok: achou, chamadas: gasto,
             motivo: achou ? "" : "a aposta de controle não voltou — o mecanismo " +
             "de token parou de funcionar, e 'vazio' NÃO quer dizer que a aposta segue aberta" };
  }

  // ⚠️ RESPOSTA VAI PARA O PRÓPRIO FRAME **E PARA O TOPO**, como o `enviar()` faz — e não
  // é redundância: o `content.js` roda com `all_frames: false`, ou seja, **só no topo**.
  // Mensagem postada apenas no frame do `members` não chega a ninguém.
  //
  // Medido na casa (s382): sem isto, a única resposta que o content via era a do frame de
  // cima — justamente o que NÃO tem a lista. O botão dizia "abra o Histórico uma vez antes"
  // com o Histórico aberto, e a marca `apto` não salvava, porque a apta nunca chegava.
  function responder(msg) {
    try { window.postMessage(msg, "*"); } catch (e) {}
    try { if (window.top && window.top !== window) window.top.postMessage(msg, "*"); } catch (e) {}
  }

  async function resolverAbertas(pedido) {
    // Aceita o formato antigo (array de carimbos) e o novo ({alvos, controle}).
    const carimbos = Array.isArray(pedido) ? pedido : ((pedido && pedido.alvos) || []);
    const controle = (pedido && !Array.isArray(pedido)) ? pedido.controle : null;
    const t0 = Date.now();
    const r = await buscarPorCarimbos(carimbos, true);
    const encontrados = [];
    for (const c of (carimbos || [])) {
      const b = r.achados.get(String(c).slice(0, 14));
      if (!b) continue;
      encontrados.push({
        carimbo: String(b.tp || "").slice(0, 14),
        stake: b.ts != null ? b.ts : b.stake,
        // A odd da casa, em DECIMAL: o `oddFrac` é fracionário (`9/10`) e quem casa do
        // outro lado é o `_norm_odd` do servidor, que fala decimal.
        odd: _oddDecimal(b.oddFrac),
        // ⚠️ `rt` AUSENTE viaja como ausência. Zero é uma conta feita: com ele, o bilhete
        // GANHO vira `L` do outro lado e ninguém vê erro nenhum.
        retorno: (b.rt == null || b.rt === "") ? null : b.rt,
        bsid: b.bsid, bs: b.bs,
      });
    }
    // ── O GATE, e ele decide o SENTIDO do que não foi achado ────────────────────
    // Só roda quando faltou alguém: com tudo achado, o mecanismo provou-se sozinho e uma
    // consulta a mais seria requisição gasta contra o teto de volume da conta.
    let mecanismo = { ok: true, motivo: "" };
    const faltaram = (carimbos || []).length - encontrados.length;
    if (faltaram > 0) {
      if (r.semTermo) {
        mecanismo = { ok: false, motivo: "o mecanismo de token não respondeu" };
      } else if (controle) {
        mecanismo = await _conferirMecanismo(controle);
      } else {
        mecanismo = { ok: null, motivo: "sem aposta de controle — não dá para afirmar que " +
                      "as que faltaram continuam abertas" };
      }
    }
    responder({
      __sharpenupB3Resolver: true,
      // ⚠️ APTO diz se ESTE frame é o que pode responder. O inject roda em TODOS os frames
      // (`all_frames: true`) e a lista mora só no do `members` — o frame de cima nunca viu
      // um `summary`, falha na hora e responde PRIMEIRO. Sem esta marca, quem pediu pega a
      // resposta do frame errado e conclui que não dá para buscar, com a lista na tela.
      apto: !!ultimaUrlSummary,
      encontrados: encontrados,
      pedidos: (carimbos || []).length,
      // `confiavel` é o que o servidor tem de olhar ANTES de concluir qualquer coisa sobre
      // quem não apareceu. `false` ou `null` significa: não sabemos, não escreva nada e
      // não diga ao operador que a aposta segue aberta.
      confiavel: mecanismo.ok === true,
      mecanismo: mecanismo.motivo || "",
      janelaCega: r.cegas > 0,     // o fuso não pôde ser lido — janela larga, mais chamadas
      paginas: r.paginas, chamadas: r.chamadas + (mecanismo.chamadas || 0), erro: r.erro,
      ms: Date.now() - t0,
    });
    if (r.amostra) {
      // A janela pedida vai junto: se o `from`/`to` estiver uma hora fora, o alvo não cai
      // dentro e a resposta vem "vazia" sem nada de errado com o token.
      LOG("resolver · 1ª resposta da casa: HTTP " + r.amostra.status + " · corpo " +
          r.amostra.len + " byte(s) · " + r.amostra.bets + " bilhete(s) · " +
          String(r.amostra.url || "").replace(/^https?:\/\/[^/]+/, ""));
    }
    LOG("resolver: " + encontrados.length + "/" + (carimbos || []).length + " achado(s) · " +
        r.chamadas + " chamada(s) · " + (Date.now() - t0) + "ms" +
        (mecanismo.ok === true ? "" : " · ⚠ " + (mecanismo.motivo || "mecanismo incerto")) +
        (r.erro ? " · " + r.erro : ""));
  }

  // Fracionária ("9/10") → decimal com precisão completa. Mesma conta do `_oddNumB3` do
  // content; aqui em string, porque é assim que viaja para o servidor.
  function _oddDecimal(frac) {
    const s = String(frac || ""); const i = s.indexOf("/");
    if (i < 0) return "";
    const a = parseFloat(s.slice(0, i)), b = parseFloat(s.slice(i + 1));
    if (!isFinite(a) || !isFinite(b) || b === 0) return "";
    return String(a / b + 1);
  }

  function enviarRotas() {
    const lista = Array.from(rotas, ([rota, v]) => ({ rota: rota, n: v.n, metodo: v.metodo }));
    const campoLista = Array.from(campos, ([reg, s]) => ({ reg: reg, campos: Array.from(s).sort() }));
    // `build` existe para uma coisa só: provar, em um segundo, QUAL código está carregado antes
    // de alguém gastar uma hora de extração medindo a versão errada. A extensão é distribuída à
    // mão e o Feca roda um perfil por casa no Octo, então "recarreguei" não garante nada.
    // Muda junto com qualquer mudança de comportamento da captura.
    const msg = { __sharpenupB3Rotas: true, topo: window.top === window, build: "s378-folga300",
                  host: location.hostname, rotas: lista, campos: campoLista, rec: rec,
                  amostra01: amostra01 };
    LOG("catálogo: " + lista.length + " forma(s) de rota · " + campoLista.length +
        " registro(s) inventariado(s) · " + rec.length + " evento(s) gravado(s) em " + location.hostname);
    try { window.postMessage(msg, "*"); } catch (e) {}
    try { if (window.top && window.top !== window) window.top.postMessage(msg, "*"); } catch (e) {}
  }

  // ── Helpers do detalhamento por ROTA (ver `detalharPorRota` abaixo) ────────────
  // O detalhamento por CLIQUE na lista (driver de UI, até a v0.6.13) foi REMOVIDO na s180: ao
  // voltar de um detalhe a lista reinicia no topo e perde as páginas já carregadas. O método por
  // rota (`location.hash`, abaixo) dispensa lista e "Voltar" — navega direto na confirmação de
  // cada bilhete. Histórico dessa saga no git (v0.6.5→0.6.13) e no STATUS (s180a).
  //
  // ⚠️ O QUE AQUELE COMENTÁRIO AFIRMAVA E ERA FALSO (corrigido na s279): "o 'Mostrar Mais' é
  // bugado, não aciona nem com ~1000 cliques sintéticos — barreira isTrusted". Isso era DEDUÇÃO
  // a partir de um driver que clicava numa lista que ele mesmo desmontava a cada bilhete. Prova
  // em contrário: uma extensão de terceiro (o "auto-show-more" do arrudex) clica no MESMO
  // seletor com `el.click()` puro e expande a lista inteira, sem truque nenhum. Não há barreira
  // de trusted event — havia lista instável. Ver `expandirLista`, logo abaixo.
  const jaTentados = new Set();   // bsids já tentados neste ciclo → não repete (término garantido) e
                                  // deixa passadas novas pegarem o que chegou depois (período em lotes)
  const espera = (ms) => new Promise((r) => setTimeout(r, ms));

  // Folga entre bilhetes. Era 900 ms no D0 (48h/Período) contra 300 ms no D1 (24h), assimetria
  // criada na s184 para "não irritar a casa com rajada". **A razão da assimetria morreu**: o
  // que travava a captura era o muro de histórico (ver `navegarUm`), não a casa, e isso está
  // medido e provado. Os dois valem 300 agora.
  //
  // As duas constantes continuam separadas de propósito, para uma volta atrás parcial custar
  // um número e não um refactor.
  //
  // **O QUE ESTÁ MEDIDO:** 473 `confirmation` seguidas voltam 200 sem degradação (mediana
  // 422 ms no primeiro bloco de 50, 391 ms no último), e outras 414 numa sessão posterior, todas
  // 200. Não há punição por volume acumulado. Os 900 ms eram **59% do custo por bilhete**
  // (1.540 ms medidos: 634 de trabalho real, 906 de espera nossa).
  //
  // ⚠️ **O QUE NÃO ESTÁ MEDIDO, e por isso este número é o que se mexe primeiro numa regressão:**
  // toda aquela medição foi feita COM os 900 ms, ou seja a ~40 requisições por minuto. A 300 ms
  // vai-se a ~66/min, taxa que ninguém nunca exerceu contra esta casa. O valor 300 não é chute
  // (o ramo D1 sempre usou ele, sem um problema em produção), mas nunca foi exercido em
  // varredura longa.
  //
  // **O risco que NÃO se manifesta no HTTP:** o histórico da conta ficou bloqueado por horas
  // duas vezes em 2026-09-20, as duas depois de varredura GRANDE (1049 e 970 bilhetes), nunca
  // depois de janela pequena, e **sem um único status ≠ 200 antes**. Então vigiar o gravador
  // pega recusa da casa e **não** pega esse bloqueio. Se ele voltar, este é o primeiro número a
  // devolver para 900, e o segundo suspeito é o TAMANHO da janela, não o ritmo.
  const FOLGA_D0_MS = 300;
  const FOLGA_D1_MS = 300;

  // Espera surgir um código NOVO (a confirmation navegada chegou), com teto. Retorna assim que
  // chega — a confirmation por rota sai em ~1s, não nos 8s.
  async function esperarCodigo(antes, limiteMs) {
    const t0 = Date.now();
    while (Date.now() - t0 < limiteMs) {
      let n = 0; for (const b of byBsid.values()) if (b.code) n++;
      if (n > antes) return true;
      await espera(150);
    }
    return false;
  }

  // Navega para UMA confirmation e espera o código chegar (ou o teto estourar). Isolado p/ o
  // ramo D0 poder repetir a MESMA navegação; o D1 (24h) usa igual, sem retry.
  // ⚠️ `location.replace`, NUNCA `location.hash =`. Atribuir ao hash EMPILHA uma entrada no
  // histórico do navegador a cada bilhete, e por volta de 420 entradas o roteador da bet365
  // para de reagir à troca de rota: a `confirmation` continua voltando 200 em ~350 ms, mas
  // sempre do MESMO bilhete, e o `esperarCodigo` estoura o teto de 9 s em cada um dali em
  // diante. Medido duas vezes no mesmo dia, em sessões independentes: quebrou na **435ª**
  // navegação de manhã e na **417ª** à tarde, com 100% de falha depois e zero recuperação —
  // "reconectar" não cura, só recarregar a página. `replace` navega sem empilhar.
  //
  // O sintoma é traiçoeiro porque a casa parece culpada e não é: 606 requisições na sessão da
  // manhã, TODAS 200, sem degradação nenhuma (o último bloco de 50 foi mais rápido que o
  // primeiro). Foi esse mesmo engano que, na s184, virou "a confirmation dá 500 sob rajada".
  async function navegarUm(rota, teto) {
    let antes = 0; for (const b of byBsid.values()) if (b.code) antes++;
    const t0 = Date.now();
    try { location.replace(rota); } catch (e) { try { location.hash = rota; } catch (e2) {} }
    const ok = await esperarCodigo(antes, teto);
    // `h` = `history.length` DEPOIS de navegar. É a prova direta de que o `replace` está
    // fazendo o trabalho: com `location.hash =` esse número subia um por bilhete e o muro se
    // formava perto de 420. Com `replace` ele fica parado. Medir isto dispensa repetir a
    // varredura grande que bloqueou duas contas em 2026-09-20 só para ver se o muro voltou.
    let h = 0; try { h = history.length; } catch (e) {}
    gravar("nav", { ok: ok ? 1 : 0, ms: Date.now() - t0, h: h });
    return ok;
  }

  // ── EXPANSÃO DA LISTA — "Mostrar Mais" automático (s279) ──────────────────────
  // O ÚNICO gesto humano que sobrava na bet365: sem clicar "Mostrar Mais" até o fim, a página só
  // baixa o 1º lote de `/summary` e o robô capturava só esses ~10 bilhetes — silenciosamente, sem
  // erro nenhum. O detalhamento já é automático desde a s180 (por rota); a paginação, não.
  //
  // QUEM CLICA É O `b3_expand.js`, no mundo ISOLATED — não este arquivo. A 1ª tentativa clicava
  // aqui mesmo (MAIN) e deu 8 cliques com ZERO requisição, enquanto o mesmo `.click()` no mesmo
  // elemento funcionava pelo console. O porquê disso continua sem nome; o cabeçalho do
  // `b3_expand.js` lista tudo o que foi descartado por medição. Este arquivo só PEDE e ESPERA.
  //
  // A ORDEM IMPORTA: expandir tem de terminar antes de `detalharPorRota`, que navega por hash e
  // tira a lista da tela. O que não carregou até ali não existe para o robô.
  //
  // Consequência boa de a captura ser passiva: depois de expandida, a lista pode resetar à
  // vontade — cada clique já fez a página baixar um `/summary` que o hook guardou em `byBsid`.
  const ESPERA_ACK  = 1500;     // ms; sem ACK = `b3_expand` ausente → segue sem expandir
  const TETO_EXPAND = 420000;   // ms; teto do lado de cá (o de lá é 400 cliques × 900ms)

  let expansaoFeita = false;    // 1 expansão por rodada do robô (reset no `onmessage`)
  let expandindo = false;

  async function expandirLista() {
    if (expandindo || expansaoFeita) return;
    if (!byBsid.size) return;   // frame sem summaries não é o da lista de membros
    expandindo = true;
    expansaoFeita = true;
    gravar("exp0", { bilhetes: byBsid.size });
    let ack = false, pronto = null;
    const ouvir = (ev) => {
      const d = ev.data;
      if (!d) return;
      if (d.__sharpenupB3ExpandAck) ack = true;
      if (d.__sharpenupB3Expandido) { ack = true; pronto = d; }
    };
    window.addEventListener("message", ouvir);
    const t0 = Date.now();
    try {
      // Avisa o content ANTES de qualquer espera: o laço dele roda a cada 500ms e a condição de
      // fim precisa saber que há expansão em curso já na 1ª volta. Sem este ping o robô podia
      // encerrar durante o ACK (s279 — o log mostrava `[b3_expand] #N` saindo DEPOIS do
      // `Bet365 API: N bilhete(s)`).
      enviar(false, { expandindo: true });
      window.postMessage({ __sharpenupB3Expandir: true }, "*");
      while (!ack && Date.now() - t0 < ESPERA_ACK) await espera(100);
      if (!ack) {
        LOG("expansão: b3_expand não respondeu — seguindo sem expandir (extensão desatualizada?)");
        return;
      }
      while (!pronto && Date.now() - t0 < TETO_EXPAND) {
        await espera(300);
        // Ping ao content: durante a expansão a contagem fica parada e o robô tem timeout de
        // 45 s de inatividade — sem este sinal ele desistiria no meio.
        enviar(false, { expandindo: true });
      }
      if (pronto) {
        LOG("expansão: " + pronto.cliques + " clique(s) · " + pronto.cards + " card(s) · " +
            pronto.motivo + " · " + Math.round((Date.now() - t0) / 1000) + "s · bilhetes " + byBsid.size);
      } else {
        LOG("expansão: teto de " + Math.round(TETO_EXPAND / 1000) + "s estourado — seguindo com o que veio");
      }
    } catch (e) {
      LOG("expansão erro:", e && e.message);
    } finally {
      window.removeEventListener("message", ouvir);
      gravar("exp1", { bilhetes: byBsid.size, ms: Date.now() - t0,
                       cliques: pronto ? pronto.cliques : undefined });
      expandindo = false;
      // `expandindo:false` é o que LIBERA o fim do robô — inclusive nos caminhos de erro e de
      // ACK ausente. Por isso vive no `finally`, não no caminho feliz.
      enviar(false, { expandindo: false });
    }
  }

  // Expandir SEMPRE antes de detalhar. Guarda única para as duas fases — o content re-pede
  // "detalhar" a cada ~6 s e sem isto a 2ª chamada entraria no meio da expansão.
  let cicloRodando = false;
  async function expandirEDetalhar(jaTem) {
    if (cicloRodando) return;
    cicloRodando = true;
    try {
      await expandirLista();
      await detalharPorRota(jaTem);
    } finally { cicloRodando = false; }
  }

  // ── DETALHAMENTO POR ROTA (s180 — o método bom) ───────────────────────────────
  // Em vez de clicar "Detalhes" → Voltar → "Mostrar Mais", navega DIRETO para a rota da
  // confirmação de cada bilhete: `#/HICO/BSSB/C<bsid>/D<ns>/`. Provado ao vivo: essa rota carrega
  // a confirmation (a própria página faz a chamada, com o token dela) e o hook captura o código BR
  // + jogo/mercado/liga. NÃO mexe na lista → sem Voltar, sem reset, sem o "Mostrar Mais" bugado.
  // A rota vem do campo `PD=#HICO#BSSB#C<id>#D<ns>#` do summary — e o NAMESPACE importa: 24h
  // recentes vêm `D1`, 48h/Período vêm `D0`. Chutar `/D1/` fixo fazia a confirmation voltar VAZIA
  // (sem BR) fora do 24h (s183) → agora deriva do PD; sem PD, cai no padrão `/D1/`.
  // Só o frame de membros (que capturou os summaries → `byBsid` populado) tem a hash do app.
  let rotaRodando = false;
  const _volta = { hash: "" };
  async function detalharPorRota(jaTem) {
    if (rotaRodando) return;                        // 1 passada por vez (concorrência) — SEM lock permanente
    if (!byBsid.size) return;                       // frame sem summaries não é o de membros
    const conhecidos = new Set(jaTem || []);
    // Alvos = uncoded, não-conhecidos (memória) e ainda NÃO tentados neste ciclo. Uma passada pega
    // só o que está na mão AGORA; em lista grande (período) os bilhetes chegam em LOTES → o content
    // re-pede "detalhar" e cada passada nova detalha o lote que chegou depois, até esgotar.
    let pulados = 0;
    const alvos = [];
    for (const [bsid, t] of byBsid) {
      if (t.code) continue;                         // já tem detalhe (rodada anterior/re-hidratado)
      if (conhecidos.has(String(bsid))) { pulados++; continue; }
      if (jaTentados.has(String(bsid))) continue;   // já tentei neste ciclo → não repete
      alvos.push(bsid);
    }
    if (!alvos.length) { enviar(true, { feitos: 0, pulados: pulados, falhas: 0 }); return; }  // nada novo → fim
    rotaRodando = true;
    _volta.hash = location.hash || "";              // p/ voltar à lista no fim
    let feitos = 0, falhas = 0;
    const tPasso = Date.now();
    // `pulados` é o que a MEMÓRIA poupou. É o número que mede o desperdício da varredura de
    // resolvidas: a lista reordena por data de COLOCAÇÃO, então revarrer a janela para achar
    // um bilhete que resolveu ontem traz junto tudo que já está planilhado.
    gravar("passo0", { alvos: alvos.length, pulados: pulados, vistos: byBsid.size });
    try {
      LOG("rota: detalhando " + alvos.length + " bilhete(s) por hash");
      for (const bsid of alvos) {
        jaTentados.add(String(bsid));               // marca ANTES de tentar → nunca repete, mesmo se falhar
        const t = byBsid.get(bsid);
        // Rota derivada do PD do bilhete (`#HICO#BSSB#C<id>#D0/D1#` → `#/HICO/BSSB/C<id>/D0-D1/`).
        // O namespace muda por janela (24h=D1, 48h/Período=D0); sem PD, cai no /D1/ legado.
        const rota = (t && t.pd) ? "#" + t.pd.replace(/#/g, "/") : "#/HICO/BSSB/C" + bsid + "/D1/";
        const isD0 = !!(t && t.pd && /#D0#/i.test(t.pd));
        // D1 (24h): uma navegação, teto 8s, folga 300ms. D0 (48h/Período): teto 9s, folga 900ms
        // e 2 retries com bounce.
        //
        // ⚠️ **A JUSTIFICATIVA ORIGINAL DESTE RAMO ESTAVA ERRADA.** A s184 concluiu que "a
        // confirmation dá 500 sob rajada no D0" e daí saíram a folga maior, o teto maior e o
        // retry. Medição de 2026-09-20, com o gravador registrando o STATUS de cada resposta:
        // **473 `confirmation` e 133 `summary` numa sessão, TODAS 200**, e mais 55 em outra, todas
        // 200 — inclusive as que o driver contou como falha. Nunca houve 500 nenhum.
        //
        // O que existia era o muro de histórico (ver `navegarUm`): passadas ~420 navegações, a
        // resposta continua 200 em ~350 ms mas traz sempre o MESMO bilhete, e o `esperarCodigo`
        // estoura o teto. O retry com bounce nunca teve chance de funcionar, porque não havia
        // token vencido para renovar. Ele fica aqui por ora **como rede**, até o `replace` provar
        // que o muro sumiu; quando provar, este ramo inteiro pode ser simplificado.
        let ok = await navegarUm(rota, isD0 ? 9000 : 8000);
        if (isD0) {
          for (let tent = 0; !ok && tent < 2; tent++) {
            LOG("D0: retry " + (tent + 1) + " · bsid " + bsid);
            // bounce: volta à lista e retorna, forçando o roteador a tratar como rota nova.
            // Também por `replace`, senão o próprio retry empilharia histórico (ver `navegarUm`).
            try { location.replace(_volta.hash || "#/HISU/"); } catch (e) {}
            await espera(800);
            ok = await navegarUm(rota, 9000);
          }
        }
        if (ok) feitos++; else falhas++;
        enviar();
        await espera(isD0 ? FOLGA_D0_MS : FOLGA_D1_MS);
      }
    } catch (e) {
      LOG("rota erro:", e && e.message);
    } finally {
      try { location.replace(_volta.hash || "#/HISU/"); } catch (e) {}  // volta p/ a lista
      rotaRodando = false;
      gravar("passo1", { feitos: feitos, falhas: falhas, ms: Date.now() - tPasso });
      LOG("driver(rota): " + feitos + " detalhe(s) · " + falhas + " falha(s) · tentados " + jaTentados.size);
      enviar(true, { feitos: feitos, pulados: pulados, falhas: falhas });
    }
  }

  // O content script pede o acumulado ao iniciar o robô → re-envia tudo (a 1ª resposta pode ter
  // vindo no load, antes de o content estar ouvindo). Repassa aos frames FILHOS: o content só
  // alcança a própria window, e quem vê as chamadas é o inject dentro do iframe de membros.
  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (!d || !d.__sharpenupB3Req) return;
    const saltos = (typeof d.saltos === "number" ? d.saltos : 0) + 1;
    if (saltos <= 4) {
      for (let i = 0; i < window.frames.length && i < 24; i++) {
        // ⚠️ O repasse copia CAMPO A CAMPO, então todo campo novo do pedido precisa ser
        // acrescentado aqui — senão ele chega vazio no frame de dentro, que é justamente
        // quem faz o trabalho. Medido na casa (s382): o frame de cima recebeu os 22 alvos
        // e não tinha como buscar; o do `members` tinha como buscar e recebeu ZERO alvos.
        // O log dizia `0/22` num e `0/0` no outro, e nada disso era erro em lugar nenhum.
        try { window.frames[i].postMessage({ __sharpenupB3Req: true, acao: d.acao,
                                             jaTem: d.jaTem, pedido: d.pedido,
                                             carimbos: d.carimbos, saltos: saltos }, "*"); } catch (e) {}
      }
    }
    // Diagnóstico sob demanda: devolve o CATÁLOGO de rotas e sai. Nunca mexe no estado da
    // captura (não reseta `expansaoFeita`, não chama `enviar`, não dispara driver nenhum).
    if (d.acao === "rotas") { enviarRotas(); return; }
    // "Resolver apostas abertas": busca na LISTA e devolve. Não escreve, não navega, não
    // mexe no estado da captura — sai antes de qualquer reset, como o catálogo de rotas.
    if (d.acao === "resolver") { resolverAbertas(d.pedido || d.carimbos || []); return; }
    if (d.acao === "limpar") {
      rec = []; recSujo = true;
      try { localStorage.removeItem(REC_KEY); } catch (e) {}
      LOG("gravador zerado");
      return;
    }
    // Pedido SEM ação = o content está abrindo uma rodada nova do robô (`b3Pedir(N)` é a 1ª
    // coisa que `roboBet365Passive` faz). É o único sinal de "começou de novo" que o inject
    // recebe — a página não recarrega entre rodadas. Sem este reset, rodar o robô 2× sem F5
    // deixaria a 2ª rodada sem expandir a lista.
    if (!d.acao) expansaoFeita = false;
    enviar();
    // Expande a lista ("Mostrar Mais") e só então detalha por hash. A ordem importa: detalhar
    // navega para fora da lista, e o que não foi carregado até ali não existe para o robô.
    if (d.acao === "detalhar") expandirEDetalhar(d.jaTem);
  });

  // ── fetch ──
  if (of && !of.__suB3W) {
    const w = function (...a) {
      const url = (a[0] && a[0].url) || a[0];
      try { catalogar(url, (a[1] && a[1].method) || (a[0] && a[0].method) || "GET"); } catch (e) {}
      try { if (!RX_SUM.test(String(url))) contarHistory(url); } catch (e) {}
      const t0 = Date.now();
      return of.apply(this, a).then((r) => {
        try {
          const s = String(url);
          const ehSum = RX_SUM.test(s), ehConf = RX_CONF.test(s);
          if (ehSum || ehConf) {
            gravar(ehSum ? "sum" : "conf", { st: r.status, ms: Date.now() - t0,
                                             bsid: _param(s, "bsid") || undefined });
            r.clone().text().then((t) => forward(url, t));
          }
        } catch (e) {}
        return r;
      });
    };
    w.__suB3W = true;
    window.fetch = w;
  }

  // ── XMLHttpRequest ──
  const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send;
  if (!os.__suB3W) {
    XMLHttpRequest.prototype.open = function (m, u) { this.__suB3U = u; this.__suB3M = m; return oo.apply(this, arguments); };
    const s = function (body) {
      try {
        const u = this.__suB3U;
        catalogar(u, this.__suB3M || "GET");
        if (!RX_SUM.test(String(u))) contarHistory(u);
        const ehSum = RX_SUM.test(String(u)), ehConf = RX_CONF.test(String(u));
        if (ehSum || ehConf) {
          const t0 = Date.now();
          const marcar = (st) => { try { gravar(ehSum ? "sum" : "conf",
            { st: st, ms: Date.now() - t0, bsid: _param(String(u), "bsid") || undefined }); } catch (e) {} };
          this.addEventListener("load", () => {
            marcar(this.status);
            try { forward(u, this.responseText); } catch (e) {}
          });
          // Falha de REDE não tem status. Sem este ramo ela some do gravador e a análise
          // confunde "a casa recusou" com "a requisição nem chegou".
          this.addEventListener("error", () => marcar(0));
        }
      } catch (e) {}
      return os.apply(this, arguments);
    };
    s.__suB3W = true;
    XMLHttpRequest.prototype.send = s;
  }
})();
