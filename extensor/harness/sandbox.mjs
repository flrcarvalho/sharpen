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
  const resposta = (url, corpo) => ({
    ok: corpo != null, status: corpo == null ? 404 : 200, url: String(url),
    text: () => Promise.resolve(corpo == null ? "" : corpo),
    clone: () => ({ text: () => Promise.resolve(corpo == null ? "" : corpo) }),
  });

  const janela = {
    location: { href: cfg.href, origin: new URL(cfg.href).origin },
    frames: [],
    addEventListener(tipo, cb) { if (tipo === "message") ouvintes.push(cb); },
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
      this.responseText = corpo == null ? "" : corpo;
      this.status = corpo == null ? 404 : 200;
      setTimeout(() => { for (const cb of (this._ouvintes.load || [])) cb.call(this); }, 0);
    },
  };

  const ctx = {
    window: janela, location: janela.location, XMLHttpRequest: XHRFake,
    console: { log: () => {}, warn: () => {}, error: () => {} },   // silencia o LOG do inject
    URL, URLSearchParams, JSON, Math, Date, Array, Number, String, Object, Boolean,
    Promise, Set, Map, isFinite, isNaN, parseFloat, parseInt, Intl, setTimeout, clearTimeout,
  };
  ctx.globalThis = ctx;
  vm.createContext(ctx);
  vm.runInContext(ler(path.join(EXT, cfg.inject)), ctx, { filename: cfg.inject });

  // 1) a página pede a lista (é o que o hook escuta). `corpoInicial` simula o CORPO que a
  // página envia — necessário quando o inject guarda a requisição para repaginar depois.
  await janela.fetch(cfg.urlInicial || cfg.href,
                     cfg.corpoInicial ? { method: "POST", body: cfg.corpoInicial } : undefined);
  await espera(30);
  // 1b) respostas que a PÁGINA busca depois (detalhe por rota, na bet365) — ver `cfg.urlsExtra`.
  for (const u of (cfg.urlsExtra || [])) { await janela.fetch(u); await espera(20); }
  // 2) o content pede o acumulado e arranca o replay
  if (cfg.pedido) { janela.postMessage({ [cfg.pedido]: true }); }
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
