// Mundo MAIN (só na Bet365): lê as RESPOSTAS de /sportshistoryapi/summary e
// /sportshistoryapi/confirmation (formato texto proprietário `F|00;chave=valor;…|01;…|`) que
// a própria página baixa, e repassa objetos limpos ao content script — para tratar igual às
// outras casas passivas (Betfair/Pinnacle).
//
// SÓ PASSIVO — POR QUE NÃO HÁ REPLAY: até a v0.6.2 este arquivo re-emitia as buscas por conta
// própria (replay), reaproveitando os headers da requisição que a página tinha feito. Não
// funciona: o header `x-net-sync-term` rotaciona A CADA requisição e o servidor o exige.
// Provado ao vivo na sessão 178, do frame `members.bet365.bet.br` e com a sessão logada:
//   • mesma URL, com os headers da página  → 200 com o payload `F|…`
//   • mesma URL, só com cookie (sem token) → 200 com corpo VAZIO (`len: 0`)
//   • mesma URL, com um token VENCIDO      → HTML da página de 404
// Não temos como gerar um token válido (vem de código ofuscado da casa). Quem consegue chamar
// a API é a PRÓPRIA página → o content script pede ao inject que NAVEGUE por rota
// (location.hash = #/HICO/BSSB/C<bsid>/D1/) até a confirmation de cada bilhete, e este arquivo
// só escuta as respostas. Ver docs/PLANO_BET365_CAPTURA_API.md.
//
// DUAS COISAS ELE DIRIGE (o resto é escuta pura): expande a lista clicando "Mostrar Mais" até o
// fim (`expandirLista`, s279 — era o último gesto manual da casa) e navega por `location.hash`
// até a confirmação de cada bilhete (`detalharPorRota`, s180). Nenhuma das duas chama a API por
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
  async function navegarUm(rota, teto) {
    let antes = 0; for (const b of byBsid.values()) if (b.code) antes++;
    try { location.hash = rota; } catch (e) {}
    return await esperarCodigo(antes, teto);
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
    try {
      LOG("rota: detalhando " + alvos.length + " bilhete(s) por hash");
      for (const bsid of alvos) {
        jaTentados.add(String(bsid));               // marca ANTES de tentar → nunca repete, mesmo se falhar
        const t = byBsid.get(bsid);
        // Rota derivada do PD do bilhete (`#HICO#BSSB#C<id>#D0/D1#` → `#/HICO/BSSB/C<id>/D0-D1/`).
        // O namespace muda por janela (24h=D1, 48h/Período=D0); sem PD, cai no /D1/ legado.
        const rota = (t && t.pd) ? "#" + t.pd.replace(/#/g, "/") : "#/HICO/BSSB/C" + bsid + "/D1/";
        const isD0 = !!(t && t.pd && /#D0#/i.test(t.pd));
        // D1 (24h) = caminho de sempre, INTOCADO: uma navegação, teto 8s, folga 300ms.
        // D0 (48h/Período) = caminho novo: a confirmation dá 500 sob RAJADA (o 24h não). Espera
        // mais, dá folga maior p/ o token `x-net-sync-term` rotacionar, e RETENTA com "bounce" no
        // hash (volta à lista e retorna → força um hashchange NOVO = re-fetch com token fresco, que
        // é o que faz o clique manual dar 200). Nenhum bilhete D1 entra aqui → 24h não pode quebrar.
        let ok = await navegarUm(rota, isD0 ? 9000 : 8000);
        if (isD0) {
          for (let tent = 0; !ok && tent < 2; tent++) {
            LOG("D0: retry " + (tent + 1) + " · bsid " + bsid);
            try { location.hash = _volta.hash || "#/HISU/"; } catch (e) {}   // bounce → força hashchange novo
            await espera(800);
            ok = await navegarUm(rota, 9000);
          }
        }
        if (ok) feitos++; else falhas++;
        enviar();
        await espera(isD0 ? 900 : 300);
      }
    } catch (e) {
      LOG("rota erro:", e && e.message);
    } finally {
      try { location.hash = _volta.hash || "#/HISU/"; } catch (e) {}  // volta p/ a lista
      rotaRodando = false;
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
        try { window.frames[i].postMessage({ __sharpenupB3Req: true, acao: d.acao,
                                             jaTem: d.jaTem, saltos: saltos }, "*"); } catch (e) {}
      }
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
      try { if (!RX_SUM.test(String(url))) contarHistory(url); } catch (e) {}
      return of.apply(this, a).then((r) => {
        try { if (RX_SUM.test(String(url)) || RX_CONF.test(String(url))) r.clone().text().then((t) => forward(url, t)); } catch (e) {}
        return r;
      });
    };
    w.__suB3W = true;
    window.fetch = w;
  }

  // ── XMLHttpRequest ──
  const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send;
  if (!os.__suB3W) {
    XMLHttpRequest.prototype.open = function (m, u) { this.__suB3U = u; return oo.apply(this, arguments); };
    const s = function (body) {
      try {
        const u = this.__suB3U;
        if (!RX_SUM.test(String(u))) contarHistory(u);
        if (RX_SUM.test(String(u)) || RX_CONF.test(String(u))) {
          this.addEventListener("load", () => { try { forward(u, this.responseText); } catch (e) {} });
        }
      } catch (e) {}
      return os.apply(this, arguments);
    };
    s.__suB3W = true;
    XMLHttpRequest.prototype.send = s;
  }
})();
