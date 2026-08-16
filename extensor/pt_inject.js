// Mundo MAIN (só na Pitaco): lê o histórico de apostas pela API da casa e repassa ao content
// script. A Pitaco (`pitaco.bet.br`, ex-"Rei do Pitaco") roda plataforma PRÓPRIA — não é
// espelho de Altenar/BetBy/Kambi/BetConstruct — e fala **gRPC-Web com protobuf binário**:
//
//   POST /api/ui_betting_my_bets_components.UiMyBetsService/GetUiMyBetsTabContent
//   corpo    = frame de 5 bytes (flag 0x00 + tamanho BE) + mensagem protobuf
//   resposta = mesmo enquadramento; o 2º frame (flag 0x80) é o trailer gRPC
//
// Por isso este é o primeiro inject que decodifica BYTES em vez de JSON. Não há `.proto`
// publicado: o de-para de campo abaixo foi medido cruzando o payload com o card renderizado
// (recon s270), e é isso que o `casos/pitaco.mjs` trava.
//
// ── DUAS DECISÕES QUE NÃO SÃO ÓBVIAS ─────────────────────────────────────────────────────
//
// 1) **O modo passivo não funciona nesta casa.** A página dispara a requisição com um
//    `AbortController` e cancela o stream assim que termina de ler; o `r.clone().arrayBuffer()`
//    do hook morre com "The user aborted a request" (medido: 5 de 5 respostas). Ler a resposta
//    da página é impossível aqui — o inject **só aprende url+headers** e busca o dado ele
//    mesmo, pelo replay. `respostas` conta as respostas do REPLAY.
//
// 2) **Nunca paginar por `.4` (página). Pedir a lista inteira num `pageSize` grande.**
//    Medido, determinístico, duas varreduras idênticas: com `pageSize=20` as páginas devolvem
//    20 · 10 · 20 · 0 · 1 — a página 3 REPETE o primeiro código da página 1 e o total de
//    códigos únicos dá **31**, contra **49** numa chamada só com `pageSize=200`. O critério
//    "página menor que a pedida = fim" também é falso (a 2ª veio com 10 e a 3ª veio cheia).
//    A própria tela da casa sofre disso: o filtro "Perdidas" trava em 20 cards por mais que
//    se role, enquanto a API tem 38. O fim autoritativo é o campo `.5` da resposta, que só
//    aparece quando a página encheu E há mais — some quando a lista acabou.
(function () {
  const RX = /UiMyBetsService\/GetUiMyBetsTabContent/i;   // endpoint que CONSUMIMOS
  // Aprende de QUALQUER método do serviço: o `GetUiMyBetsPage` sai no load com o mesmo pacote
  // de headers, e aprender só do TabContent perderia o molde se a tela mudasse de chamada.
  // O path é reescrito para o TabContent na hora do replay (mesmo desenho do vb_inject).
  const RX_APRENDE = /UiMyBetsService\/(GetUiMyBets\w+)/i;
  const ALVO = "GetUiMyBetsTabContent";

  const byRef = new Map();                     // código(string) → bilhete normalizado
  let respostas = 0;                           // respostas do REPLAY (autodiagnóstico)
  let reqCtx = null;                           // {url, headers} de uma requisição real
  let pedido = false;                          // o robô já pediu → pode arrancar o replay
  let loopAtivo = false;                       // trava: um replay por vez
  let fimReplay = false;
  let ultimoErro = "";                         // último erro do replay (autodiagnóstico)
  const LOG = (...a) => { try { console.log("[SharpenUp pt_inject]", ...a); } catch (e) {} };
  LOG("hook instalado em", location.href);

  const of = window.fetch;                     // fetch ORIGINAL (o replay usa este)

  // ── protobuf: leitura ────────────────────────────────────────────────────────
  // Varint sem BigInt (multiplicação em vez de shift): os valores desta API cabem em 2^53 —
  // o maior é o timestamp em segundos (~1,79e9). `<<` estouraria em 32 bits.
  function _vi(b, i) {
    let r = 0, s = 1;
    while (i < b.length) { const x = b[i] & 0x7f; r += x * s; const c = b[i] & 0x80; i++; if (!c) break; s *= 128; }
    return [r, i];
  }
  function _campos(b) {
    const out = []; let i = 0;
    while (i < b.length) {
      const [k, ni] = _vi(b, i); i = ni;
      const f = Math.floor(k / 8), w = k % 8;
      if (f === 0) return null;
      if (w === 0) { const [v, n2] = _vi(b, i); i = n2; out.push({ f: f, w: w, v: v }); }
      else if (w === 2) {
        const [l, n2] = _vi(b, i); i = n2;
        if (i + l > b.length) return null;
        out.push({ f: f, w: w, v: b.subarray(i, i + l) }); i += l;
      }
      else if (w === 5) { i += 4; out.push({ f: f, w: w, v: null }); }
      else if (w === 1) { i += 8; out.push({ f: f, w: w, v: null }); }
      else return null;
    }
    return out;
  }
  const _dec = new TextDecoder("utf-8");
  const _um = (cs, n) => { for (let i = 0; i < cs.length; i++) if (cs[i].f === n) return cs[i]; return null; };
  const _todos = (cs, n) => { const o = []; for (let i = 0; i < cs.length; i++) if (cs[i].f === n) o.push(cs[i]); return o; };
  // Caminho por lista de campos: `_txt(cs, [2,1,3])` = campo 2 › 1 › 3, como string.
  function _no(cs, caminho) {
    let atual = cs;
    for (let i = 0; i < caminho.length; i++) {
      const c = _um(atual, caminho[i]);
      if (!c) return null;
      if (i === caminho.length - 1) return c;
      if (c.w !== 2 || !c.v) return null;
      atual = _campos(c.v);
      if (!atual) return null;
    }
    return null;
  }
  const _txt = (cs, caminho) => { const c = _no(cs, caminho); return (c && c.w === 2 && c.v) ? _dec.decode(c.v) : null; };
  const _int = (cs, caminho) => { const c = _no(cs, caminho); return (c && c.w === 0) ? c.v : null; };

  // ── protobuf: escrita (o corpo do replay) ────────────────────────────────────
  function _evi(n) { const o = []; let v = Math.floor(n); do { let b = v % 128; v = Math.floor(v / 128); if (v) b |= 0x80; o.push(b); } while (v); return o; }
  const _chave = (f, w) => _evi(f * 8 + w);
  function _bytesDe(s) { const o = []; for (let i = 0; i < s.length; i++) o.push(s.charCodeAt(i) & 0x7f); return o; }   // ASCII: "finished"/"open"
  // `.1=1 · .2=pageSize · .3={.1:aba, .2:tipo} · .4=página` — medido no corpo real da página.
  function _corpo(aba, tipo, pagina, tam) {
    const a = _bytesDe(aba);
    const sub = [].concat(_chave(1, 2), _evi(a.length), a, _chave(2, 0), _evi(tipo));
    const m = [].concat(
      _chave(1, 0), _evi(1),
      _chave(2, 0), _evi(tam),
      _chave(3, 2), _evi(sub.length), sub,
      _chave(4, 0), _evi(pagina));
    const out = new Uint8Array(5 + m.length);
    out[0] = 0;
    out[1] = (m.length >>> 24) & 0xff; out[2] = (m.length >>> 16) & 0xff;
    out[3] = (m.length >>> 8) & 0xff;  out[4] = m.length & 0xff;
    for (let i = 0; i < m.length; i++) out[5 + i] = m[i];
    return out;
  }
  // Desmonta os frames gRPC-Web. O 1º (flag 0) é a mensagem; o de flag 0x80 é o trailer.
  function _frames(u8) {
    const fr = []; let i = 0;
    while (i + 5 <= u8.length) {
      const flag = u8[i];
      const len = (u8[i + 1] * 16777216) + (u8[i + 2] * 65536) + (u8[i + 3] * 256) + u8[i + 4];
      i += 5;
      if (i + len > u8.length) break;
      fr.push({ flag: flag, corpo: u8.subarray(i, i + len) });
      i += len;
    }
    return fr;
  }

  // ── normalização ─────────────────────────────────────────────────────────────
  // Dinheiro chega FORMATADO ("R$ 1.234,56"), não em centavos — exceto o stake, que também
  // vem inteiro em `.5.6`. Onde houver o inteiro, ele manda: não passa por parser nenhum.
  function _brl(s) {
    if (typeof s !== "string") return null;
    const t = s.replace(/[^\d,.-]/g, "").replace(/\./g, "").replace(",", ".");
    const n = parseFloat(t);
    return isFinite(n) ? n : null;
  }
  const _odd = (s) => { if (typeof s !== "string") return null; const n = parseFloat(s.replace("x", "").trim()); return isFinite(n) ? n : null; };

  // Uma perna. O campo `.3` dela é um ONEOF de três formas, e a forma muda com o estado do
  // evento (medido: em bilhete finalizado são 112 de 112 pernas na forma de texto):
  //   `.3.1` ao vivo  → `.3.1.1` período ("1T ") + `.3.1.2` timestamp
  //   `.3.2.1` texto  → "15/08" — **SEM ANO**; quem deriva o ano é o content, pela colocação
  //   `.3.3.1` futuro → timestamp unix do início
  function _perna(b) {
    const cs = _campos(b);
    if (!cs) return null;
    return {
      label: _txt(cs, [2, 1, 2]) || "",             // "Barnsley" / "Mais de 4.5"
      mercado: _txt(cs, [2, 1, 3]) || "",           // "Time com Mais Escanteios"
      status: _int(cs, [2, 1, 6]),                  // 1 não começou · 2 ao vivo · 3 ganhou · 4 perdeu · 5 anulado
      odd: _odd(_txt(cs, [2, 1, 8])),               // odd VIGENTE da perna (1.00x quando anulada)
      oddOriginal: _odd(_txt(cs, [2, 1, 9])),       // odd de antes (só quando mudou)
      casa: _txt(cs, [1, 1, 1, 1, 1]) || "",        // mandante
      fora: _txt(cs, [1, 1, 2, 1, 1]) || "",        // visitante
      eventoId: _txt(cs, [3, 4]) || _txt(cs, [4, 1]) || "",
      inicio: _int(cs, [3, 3, 1]) || _int(cs, [3, 1, 2]) || null,   // unix (futuro / ao vivo)
      dataTxt: _txt(cs, [3, 2, 1]) || "",           // "15/08" (sem ano)
      periodo: (_txt(cs, [3, 1, 1]) || "").trim(),  // "1T" — só quando ao vivo
    };
  }

  function _bilhete(b) {
    const cs = _campos(b);
    if (!cs) return null;
    const ref = _txt(cs, [4, 1, 1]);
    if (!ref) return null;
    const cent = _int(cs, [5, 6]);
    return {
      ref: String(ref),
      status: _int(cs, [6]),                        // 1/2 aberta · 3 ganha · 4 perdida · 8 anulada
      tipo: _txt(cs, [1, 1]) || "",                 // "Dupla" / "Tripla"
      // Stake pelo INTEIRO em centavos quando existe — a única grandeza desta API que não
      // depende de parsear texto formatado.
      stake: (typeof cent === "number") ? cent / 100 : _brl(_txt(cs, [1, 2])),
      oddExibida: _odd(_txt(cs, [1, 3])),           // ⚠ ARREDONDADA a 2 casas — não explica o retorno
      oddOriginal: _odd(_txt(cs, [1, 4])),          // odd de antes (anulação de perna, mudança)
      retorno: _brl(_txt(cs, [5, 2])),              // realizado SÓ depois de liquidado
      potencial: _brl(_txt(cs, [5, 5])),            // ⚠ em bilhete aberto o `.5.2` vem igual a este
      colocada: _int(cs, [4, 2]),                   // unix (segundos)
      cashout: _brl(_txt(cs, [7, 2])),              // valor de "Encerrar aposta" (só em aberta)
      cashoutDisp: _int(cs, [7, 1]),
      sels: _todos(cs, 3).map((c) => _perna(c.v)).filter(Boolean),
    };
  }

  // Emite SEMPRE hook:true + respostas (heartbeat), mesmo com 0 bilhetes — o content distingue
  // "hook não carregou" de "replay falhou" de "conta vazia".
  function enviar() {
    try {
      window.postMessage({
        __sharpenupPTCData: true, hook: true,
        bilhetes: Array.from(byRef.values()), respostas: respostas, fim: fimReplay,
        erro: ultimoErro,
      }, "*");
    } catch (e) {}
  }

  // Um mesmo código pode voltar nas duas abas; a versão RESOLVIDA vence a ABERTA.
  const _aberto = (b) => b.status === 1 || b.status === 2;
  function guardar(b) {
    const ex = byRef.get(b.ref);
    if (!ex) { byRef.set(b.ref, b); return; }
    if (_aberto(ex) && !_aberto(b)) byRef.set(b.ref, b);
  }

  // Processa uma resposta binária. Devolve {n, temMais} ou null.
  function forward(u8) {
    const fr = _frames(u8);
    if (!fr.length) return null;
    const cs = _campos(fr[0].corpo);
    if (!cs) return null;
    respostas++;
    const itens = _todos(cs, 2);
    for (const c of itens) {
      const b = _bilhete(c.v);
      if (b) guardar(b);
    }
    // `.5` = "tem mais" — presente só quando a página encheu E sobrou. Ausente = fim.
    const mais = _um(cs, 5);
    LOG("bilhetes na resposta:", itens.length, "· total:", byRef.size, "· temMais:", !!mais);
    enviar();
    return { n: itens.length, temMais: !!mais };
  }

  // ── replay ───────────────────────────────────────────────────────────────────
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
    const m = RX_APRENDE.exec(String(url));
    if (!m) return;
    if (!reqCtx) {
      // Reescreve o método para o TabContent: a auth é por HEADER (Firebase), e o pacote de
      // ~20 headers da página é a única coisa que autentica — `credentials:"include"` sozinho
      // dá 401 nesta casa.
      const alvo = String(url).replace(m[1], ALVO);
      reqCtx = { url: alvo, headers: headers || {} };
      LOG("requisição capturada p/ replay ·", m[1], "→", ALVO);
    }
    if (pedido) arrancarReplay();
  }

  // Escalada de tamanho de página. Começa grande de propósito (a conta inteira costuma caber
  // numa resposta) e só cresce se a casa disser que ainda há mais.
  const TAMANHOS = [200, 500, 1000, 2000];
  const ABAS = [{ nome: "finished", tipo: 2 }, { nome: "open", tipo: 1 }];

  async function puxarAba(aba) {
    for (let i = 0; i < TAMANHOS.length; i++) {
      const tam = TAMANHOS[i];
      let r;
      try {
        r = await of.call(window, reqCtx.url, {
          method: "POST", headers: reqCtx.headers, credentials: "include",
          body: _corpo(aba.nome, aba.tipo, 1, tam),
        });
      } catch (e) { ultimoErro = "rede: " + (e && e.message); LOG("erro no replay:", ultimoErro); return; }
      if (!r || !r.ok) { ultimoErro = "HTTP " + (r && r.status); LOG("replay parou ·", ultimoErro); return; }
      let res;
      try { res = forward(new Uint8Array(await r.arrayBuffer())); }
      catch (e) { ultimoErro = "corpo: " + (e && e.message); LOG("erro lendo corpo:", ultimoErro); return; }
      if (!res) { ultimoErro = "resposta ilegível (formato mudou?)"; LOG(ultimoErro); return; }
      if (!res.temMais) return;                     // fim autoritativo da casa
      LOG("aba", aba.nome, "encheu com", tam, "→ subindo o tamanho da página");
    }
    // Chegou ao teto ainda com "tem mais": melhor gritar do que entregar lote incompleto em
    // silêncio (é o modo de falha que a s179 pagou caro).
    ultimoErro = "a aba " + aba.nome + " tem mais de " + TAMANHOS[TAMANHOS.length - 1] + " bilhetes";
    LOG(ultimoErro);
  }

  async function arrancarReplay() {
    if (loopAtivo || fimReplay || !reqCtx) return;
    loopAtivo = true;
    try { for (const aba of ABAS) await puxarAba(aba); }
    finally {
      loopAtivo = false;
      fimReplay = true;
      enviar();                                     // sinaliza fim p/ o robô parar de esperar
    }
  }

  // O content pede o acumulado ao iniciar o robô → re-envia tudo E arranca o replay.
  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (!d || !d.__sharpenupPTCReq) return;
    pedido = true;
    enviar();
    arrancarReplay();
  });

  // ── fetch ──
  // Só APRENDE a requisição: a resposta da página é inalcançável nesta casa (ver o cabeçalho).
  if (of && !of.__suPTCW) {
    const w = function (...a) {
      const url = (a[0] && a[0].url) || a[0];
      const opts = a[1] || (a[0] && typeof a[0] === "object" ? a[0] : null);
      try { if (RX_APRENDE.test(String(url))) capturarReq(url, _hdrsToObj(opts && opts.headers)); } catch (e) {}
      return of.apply(this, a);
    };
    w.__suPTCW = true;
    window.fetch = w;
  }

  // ── XMLHttpRequest ──
  // A tela usa `fetch` (medido), mas o hook fica de pé porque o custo é nulo e uma troca de
  // cliente HTTP pela casa mataria a captura em silêncio.
  const oo = XMLHttpRequest.prototype.open, os = XMLHttpRequest.prototype.send, osh = XMLHttpRequest.prototype.setRequestHeader;
  if (!os.__suPTCW) {
    XMLHttpRequest.prototype.open = function (m, u) { this.__suPTCU = u; this.__suPTCH = {}; return oo.apply(this, arguments); };
    XMLHttpRequest.prototype.setRequestHeader = function (k, v) { try { this.__suPTCH[k] = v; } catch (e) {} return osh.apply(this, arguments); };
    const s = function () {
      try { if (RX_APRENDE.test(String(this.__suPTCU))) capturarReq(this.__suPTCU, this.__suPTCH); } catch (e) {}
      return os.apply(this, arguments);
    };
    s.__suPTCW = true;
    XMLHttpRequest.prototype.send = s;
  }

  // `RX` é usado pelo harness e pela documentação como o endpoint consumido; mantido em uso
  // aqui para não virar constante morta.
  if (reqCtx && !RX.test(reqCtx.url)) LOG("aviso: url aprendida não casa o endpoint alvo");
})();
