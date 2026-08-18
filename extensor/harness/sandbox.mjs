// Sandbox do harness do SharpenUp: roda o CÓDIGO REAL da extensão (os `*_inject.js` e o
// `content.js` do repo) fora do navegador, contra payloads salvos em `fixtures/`.
//
// POR QUE ISTO EXISTE: até a s192 todo harness era construído no scratchpad e jogado fora
// no fim da sessão (bet365 s178, KTO s192). Cada casa nova reconstruía o andaime do zero, e
// nenhuma regressão ficava travada — a bet365 quebrou o parser 3 vezes seguidas sem que nada
// acusasse. Aqui o andaime é permanente e a casa nova entra como UM arquivo em `casos/`.
//
// Duas peças:
//   • `rodarInject()`  — mundo MAIN falso (fetch/XHR/postMessage) → devolve o que o inject
//                        emitiu, já normalizado. Exercita inclusive o REPLAY (paginação).
//   • `carregarContent()` — roda o `content.js` inteiro num DOM/chrome dublados e devolve
//                        um acessador para QUALQUER função interna dele (formatTicket*, etc.).
//                        Sem recortar o arquivo por comentário: o slice por marcador quebrava
//                        a cada edição de comentário.
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { fileURLToPath } from "node:url";

export const RAIZ = path.dirname(fileURLToPath(import.meta.url));
export const EXT = path.dirname(RAIZ);

const ler = (p) => fs.readFileSync(p, "utf8");

export function fixture(nome) {
  return ler(path.join(RAIZ, "fixtures", nome));
}

const espera = (ms) => new Promise((r) => setTimeout(r, ms));

/**
 * Roda um `*_inject.js` num mundo MAIN dublado.
 *
 * @param {object} cfg
 * @param {string} cfg.inject     arquivo em extensor/ (ex.: "kto_inject.js")
 * @param {string} cfg.href       location.href da aba (o inject loga e resolve URL relativa)
 * @param {(url:string)=>string|null} cfg.responder  URL → corpo da resposta (null = 404).
 *        Recebe TODA requisição, inclusive as do replay: é aqui que se simula paginação.
 * @param {string} [cfg.pedido]   chave do pedido do content (ex.: "__sharpenupKTOReq") —
 *        postada após a 1ª resposta para arrancar o replay ativo.
 * @param {object} [cfg.pedidoMsg]  pedido COMPLETO a postar (a mensagem inteira do content, com
 *        `acao`/`jaTem`). Use quando a fase testada depender da ação, não só do "acorda".
 * @param {"turbo"} [cfg.relogio]  ver o comentário do `_st` abaixo — encurta as esperas do inject.
 * @param {object} [cfg.optsInicial]  2º argumento do fetch inicial (method/headers/body). Use
 *        quando o replay depender dos HEADERS que a página mandou — ex.: o Bearer da Jonbet.
 * @param {object} [cfg.dom]      `document` dublado, para os injects que DIRIGEM a página além de
 *        escutá-la. Hoje só a bet365: ela expande a lista clicando `.hl-SummaryRenderer_ShowMore`
 *        (s279) e sem um DOM aqui o loop de expansão ficaria sem regressão — justamente o loop
 *        que precisa provar que TERMINA. Precisa expor ao menos `querySelector`. O default é um
 *        documento vazio (querySelector → null), que é o que os outros 16 casos veem: inject que
 *        não toca no DOM segue idêntico.
 * @param {string[]} [cfg.urlsExtra]  URLs buscadas DEPOIS da inicial, em ordem. Existe para as
 *        casas cujo detalhe a PÁGINA busca, não o inject — na bet365 o `confirmation` só sai
 *        quando o app navega por rota (`location.hash`), coisa que não existe fora do navegador.
 *        Sem isto o harness só conseguiria exercitar o `summary`, e o merge summary+confirmation
 *        (de onde vêm código, data e jogo/mercado) ficaria sem regressão.
 * @param {number} [cfg.ms=400]   tempo de forno antes de colher.
 * @returns {Promise<{mensagens:object[], ultima:object|null, urls:string[]}>}
 */
export async function rodarInject(cfg) {
  const mensagens = [];
  const urls = [];
  const ouvintes = [];

  // `opts` (method/headers/body) chega ao `responder` como 2º argumento: sem ele não dá para
  // distinguir duas requisições que compartilham a MESMA URL — caso da Betfair, onde a aba
  // Aberta e a Resolvida só diferem pelo `"status"` do corpo, e a paginação só se prova
  // olhando o índice enviado. Casos antigos ignoram o 2º argumento e seguem iguais.
  const responder = (url, opts) => {
    urls.push(String(url));
    return cfg.responder(String(url), opts || null);
  };
  // O `responder` pode devolver TEXTO (o caso das 15 casas até aqui) ou BYTES (Buffer /
  // Uint8Array). Bytes existem para a Pitaco, que responde protobuf binário em gRPC-Web: ler
  // esse corpo por `text()` passaria pelo decode UTF-8 e **corromperia os bytes** — todo
  // 0x80-0xFF inválido vira U+FFFD e o payload nunca mais volta. Por isso a resposta dublada
  // ganhou `arrayBuffer()`. Para corpo de texto nada muda (`text()` continua sendo a fonte).
  const resposta = (url, corpo) => {
    const bin = corpo != null && typeof corpo !== "string";
    const buf = () => (corpo == null ? Buffer.alloc(0) : (bin ? Buffer.from(corpo) : Buffer.from(corpo, "utf8")));
    const text = () => Promise.resolve(corpo == null ? "" : (bin ? buf().toString("utf8") : corpo));
    const arrayBuffer = () => { const b = buf(); return Promise.resolve(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength)); };
    return {
      ok: corpo != null, status: corpo == null ? 404 : 200, url: String(url),
      text, arrayBuffer,
      clone: () => ({ text, arrayBuffer }),
    };
  };

  const janela = {
    location: { href: cfg.href, origin: new URL(cfg.href).origin },
    frames: [],
    addEventListener(tipo, cb) { if (tipo === "message") ouvintes.push(cb); },
    // `removeEventListener` não é enfeite: o inject registra um ouvinte por rodada enquanto
    // espera a expansão e o solta no fim. Sem ele aqui, o harness quebrava com TypeError e
    // qualquer vazamento de ouvinte passaria despercebido.
    removeEventListener(tipo, cb) {
      if (tipo !== "message") return;
      const i = ouvintes.indexOf(cb);
      if (i > -1) ouvintes.splice(i, 1);
    },
    postMessage(msg) {
      mensagens.push(msg);
      // Entrega também aos ouvintes do próprio inject (é assim que o content dispara o replay).
      for (const cb of ouvintes) { try { cb({ data: msg, source: janela }); } catch (e) {} }
    },
    fetch(url, opts) { return Promise.resolve(resposta(url, responder(url, opts))); },
  };
  janela.top = janela;
  janela.window = janela;

  // XHR dublado: alguns sites (KTO/Kambi) pedem a lista por XHR, não por fetch.
  function XHRFake() { this._ouvintes = {}; }
  XHRFake.prototype = {
    open(m, u) { this._m = m; this._u = u; },
    setRequestHeader() {},
    addEventListener(t, cb) { (this._ouvintes[t] ||= []).push(cb); },
    send(body) {
      const corpo = responder(this._u, { method: this._m, body: body });
      const bin = corpo != null && typeof corpo !== "string";
      this.responseText = corpo == null ? "" : (bin ? Buffer.from(corpo).toString("utf8") : corpo);
      if (bin) { const b = Buffer.from(corpo); this.response = b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength); }
      this.status = corpo == null ? 404 : 200;
      setTimeout(() => { for (const cb of (this._ouvintes.load || [])) cb.call(this); }, 0);
    },
  };

  // Documento dublado (ver `cfg.dom`): vazio por padrão — o inject que só escuta nunca o toca.
  // Em forma de FUNÇÃO recebe a `janela`, para o clique dublado poder disparar a requisição que
  // a PÁGINA faria (é assim que "Mostrar Mais" carrega o lote seguinte na bet365).
  const documento = (typeof cfg.dom === "function" ? cfg.dom(janela) : cfg.dom) ||
                    { querySelector: () => null, querySelectorAll: () => [] };
  janela.document = documento;

  // Relógio turbo (`cfg.relogio === "turbo"`): o `setTimeout` do inject dispara na hora. Existe
  // para o loop de expansão da bet365, que espera 900ms entre cliques — em tempo real um caso de
  // 3 cliques + 8 ciclos de estagnação levaria ~10s e o harness inteiro roda em menos de 1s. NÃO
  // mexe em `Date.now()`: quem tem teto por relógio (`esperarCodigo`) continua medindo tempo real.
  const _st = cfg.relogio === "turbo" ? ((cb) => setTimeout(cb, 0)) : setTimeout;

  const ctx = {
    window: janela, location: janela.location, XMLHttpRequest: XHRFake, document: documento,
    console: { log: () => {}, warn: () => {}, error: () => {} },   // silencia o LOG do inject
    URL, URLSearchParams, JSON, Math, Date, Array, Number, String, Object, Boolean,
    Promise, Set, Map, isFinite, isNaN, parseFloat, parseInt, Intl, setTimeout: _st, clearTimeout,
    // Binário: a Pitaco responde protobuf em gRPC-Web, então o inject dela monta e lê bytes.
    // No navegador esses globais sempre existiram; aqui o `vm` só enxerga o que a gente passa.
    Uint8Array, Int8Array, Uint32Array, DataView, ArrayBuffer, TextDecoder, TextEncoder,
  };
  ctx.globalThis = ctx;
  vm.createContext(ctx);
  vm.runInContext(ler(path.join(EXT, cfg.inject)), ctx, { filename: cfg.inject });

  // 1) a página pede a lista (é o que o hook escuta). `corpoInicial` simula o CORPO que a
  // página envia — necessário quando o inject guarda a requisição para repaginar depois.
  // `optsInicial` dá controle total do 2º argumento do fetch: existe para as casas cujo replay
  // depende dos HEADERS da requisição real (Jonbet/BetBy — o `Authorization: Bearer` é a única
  // coisa que separa a chamada útil daquela que a página dispara antes de autenticar e toma
  // 401). Sem ele o harness não conseguiria exercitar a guarda do token.
  await janela.fetch(cfg.urlInicial || cfg.href,
                     cfg.optsInicial ||
                     (cfg.corpoInicial ? { method: "POST", body: cfg.corpoInicial } : undefined));
  await espera(30);
  // 1b) respostas que a PÁGINA busca depois (detalhe por rota, na bet365) — ver `cfg.urlsExtra`.
  // Cada item é uma URL ou `{url, opts}` — a forma com `opts` existe para reproduzir a
  // sequência real da Jonbet: a 1ª chamada sai sem `Authorization` e toma 401, a 2ª já vai
  // autenticada. É só nessa 2ª que o inject pode aprender a requisição para o replay.
  for (const x of (cfg.urlsExtra || [])) {
    const u = (x && typeof x === "object") ? x.url : x;
    const o = (x && typeof x === "object") ? x.opts : undefined;
    await janela.fetch(u, o);
    await espera(20);
  }
  // 2) o content pede o acumulado e arranca o replay
  if (cfg.pedido) { janela.postMessage({ [cfg.pedido]: true }); }
  // Pedido COMPLETO (objeto): o content manda mais que a chave — na bet365 manda `acao` e
  // `jaTem`, e é a `acao:"detalhar"` que arranca a expansão da lista. Postado depois do simples
  // porque alguns injects usam o 1º como "acorda" e o 2º como comando.
  if (cfg.pedidoMsg) { janela.postMessage(cfg.pedidoMsg); }
  await espera(cfg.ms || 400);

  const meus = mensagens.filter((m) => m && Object.keys(m).some((k) => k.endsWith("Data")));
  return { mensagens: meus, ultima: meus[meus.length - 1] || null, urls };
}

/**
 * Roda o `content.js` inteiro (IIFE) num ambiente dublado e devolve `pegar(nome)`, que
 * enxerga QUALQUER binding interno do arquivo — inclusive os `formatTicket*`.
 *
 * Truque: injeta `globalThis.__SUget = (n) => eval(n)` DENTRO do IIFE, antes do fechamento.
 * `eval` direto herda a cadeia de escopo, então nada precisa ser exportado e nenhum recorte
 * por comentário é necessário (o slice por marcador quebrava a cada edição de comentário).
 */
export function carregarContent() {
  let src = ler(path.join(EXT, "content.js"));
  const fim = src.lastIndexOf("})();");
  if (fim < 0) throw new Error("content.js: não achei o fechamento do IIFE");
  src = src.slice(0, fim) + "\n  globalThis.__SUget = (n) => eval(n);\n" + src.slice(fim);

  const noop = () => {};
  const elemento = () => ({
    style: { setProperty: noop }, classList: { add: noop, remove: noop, toggle: noop },
    appendChild: noop, remove: noop, addEventListener: noop, setAttribute: noop,
    querySelector: () => null, querySelectorAll: () => [], innerText: "", textContent: "",
  });
  const documento = {
    createElement: elemento, documentElement: elemento(), body: elemento(),
    scrollingElement: elemento(), addEventListener: noop,
    querySelector: () => null, querySelectorAll: () => [],
  };
  const janela = {
    addEventListener: noop, postMessage: noop, frames: [], innerHeight: 800, scrollY: 0,
    scrollTo: noop, getComputedStyle: () => ({ overflowY: "visible" }),
    location: { href: "https://exemplo.test/", pathname: "/" },
  };
  janela.top = janela;
  const chrome = {
    storage: { local: { get: () => Promise.resolve({}), set: () => Promise.resolve(),
                        remove: () => Promise.resolve() }, onChanged: { addListener: noop } },
    runtime: { onMessage: { addListener: noop }, sendMessage: () => Promise.resolve({ ok: true }),
               getManifest: () => ({ version: "0.0.0-harness" }) },
  };

  const ctx = {
    window: janela, document: documento, chrome, location: janela.location,
    console: { log: noop, warn: noop, error: noop },
    innerHeight: 800, scrollTo: noop, getComputedStyle: janela.getComputedStyle,
    URL, URLSearchParams, JSON, Math, Date, Array, Number, String, Object, Boolean, RegExp,
    Promise, Set, Map, isFinite, isNaN, parseFloat, parseInt, Intl, setTimeout, clearTimeout,
    requestAnimationFrame: (cb) => setTimeout(cb, 0),
  };
  ctx.globalThis = ctx;
  vm.createContext(ctx);
  vm.runInContext(src, ctx, { filename: "content.js" });
  if (typeof ctx.__SUget !== "function") throw new Error("content.js: __SUget não foi exposto");
  return { pegar: (nome) => ctx.__SUget(nome) };
}

/** Linha `Rótulo: valor` de um bloco de texto do bilhete (o que a IA lê). */
export function linha(bloco, rotulo) {
  const alvo = bloco.split("\n").find((l) => l.startsWith(rotulo));
  return alvo ? alvo.slice(rotulo.length).trim() : "";
}
