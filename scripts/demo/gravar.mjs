/**
 * Grava CLIPES do Sharpen rodando contra o `servidor_demo.py` (base ficticia).
 *
 *   1) python scripts/demo/servidor_demo.py 8011
 *   2) node scripts/demo/gravar.mjs [saida] [porta] [nome-do-clipe ...]
 *
 * Saida por clipe: `<nome>.webm` (VP9), `<nome>.mp4` (H.264, yuv420p) e
 * `<nome>.poster.jpg`. Feito para `<video autoplay muted loop playsinline>` numa
 * pagina de vendas: sem audio, curto, e leve o bastante para nao atrasar a pagina.
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * O QUE ESTE HARNESS **NAO** COBRE  (leia antes de confiar num clipe)
 * ─────────────────────────────────────────────────────────────────────────────
 *  · NAO e' teste. Nada aqui asserta que a tela esta CERTA — so que ela pintou.
 *    Um numero errado na tela vira um clipe bonito com o numero errado.
 *  · NAO valida marca/UI. O checklist do `/nova-ui` continua sendo do humano.
 *  · NAO garante que o roteiro aconteceu. Ha dois gates baratos (o clipe precisa
 *    render N quadros e o `#exp-status` da cena 2 precisa dizer quantos foram
 *    sugeridos), mas eles nao provam que a coluna Tipster ficou visivelmente
 *    preenchida — quem confere isso e' o olho, abrindo o .webm.
 *  · NAO captura o CURSOR do sistema: o `Page.startScreencast` do CDP nao o
 *    inclui. O ponteiro que aparece no clipe e' um DIV desenhado por este script
 *    no documento da casca (`#__gravcursor`). Ele nao existe no produto — e' o
 *    mesmo artificio de qualquer gravacao de demo, e esta dito aqui para ninguem
 *    procurar esse elemento no `app.html`.
 *  · NAO cobre a extracao de verdade (mandar print -> IA -> grade). O
 *    `servidor_demo.py` nao tem modelo nem chave de API; o que se ve na cena
 *    `extracao` e' a grade e os KPIs de uma conta que JA tem base.
 *  · NAO grava audio, NAO grava o Dashboard (so a tela de Extracao/Captura) e
 *    NAO testa outro navegador que nao o Chrome do sistema.
 *  · NAO e' deterministico no TEMPO: o clipe sai com a duracao do relogio da
 *    maquina. O peso final varia; por isso o script IMPRIME o peso de cada
 *    arquivo e GRITA quando o .webm passa do teto (`TETO_KB`).
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * Por que CDP e nao `page.screencast()`
 * ─────────────────────────────────────────────────────────────────────────────
 * O `page.screencast()` do puppeteer grava direto em webm, mas exige o ffmpeg no
 * PATH — e aqui ele nao esta (vem do `imageio_ffmpeg`, dentro do site-packages do
 * Python). Com `Page.startScreencast` os quadros chegam como JPEG e nos montamos
 * o video chamando o ffmpeg pelo caminho absoluto.
 *
 * Os quadros do screencast chegam SO QUANDO A TELA MUDA — nao ha taxa fixa. Por
 * isso a montagem usa o demuxer `concat` com `duration` por quadro, calculada do
 * timestamp que o proprio CDP manda. Assumir 30 fps constante aceleraria as
 * partes paradas e deixaria o clipe fora de sincronia com o roteiro.
 *
 * Os tres problemas de DIRIGIR este app estao resolvidos no `capturar.mjs` e
 * valem aqui igual: casca com dois iframes, dash que monta ~24 mil apostas e
 * Chart.js que so redesenha no resize. Este script fica na tela de Extracao
 * (`#plan`, iframe `fr-plan`), que nao usa Chart.js.
 */
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import puppeteer from "puppeteer-core";

const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const SAIDA = process.argv[2] || "clipes";
const PORTA = process.argv[3] || "8011";
const FILTRO = process.argv.slice(4);
const BASE = `http://127.0.0.1:${PORTA}`;

// Grava em 1920x1200 e ENTREGA em 1440x900 — a mesma proporcao (1,6), entao a
// reducao e' um scale limpo, sem corte e sem barra preta.
//
// MEDIDO (s331), e nenhum dos tres numeros e' folga generosa:
//
//  · Abaixo de ~1600 de LARGURA a tela de Extracao COLAPSA: o rail RAIO-X passa
//    por cima da barra de acoes da grade e o botao "Sugerir tipsters" fica
//    coberto. O clique do puppeteer nao da erro nenhum nesse caso — ele acerta a
//    coordenada certa e o evento vai para o elemento de cima. Gravar em 1440
//    nativo produzia um clipe onde nada acontecia.
//  · Em 1760 a faixa de KPIs ainda sai CORTADA a direita (o tile "Custo" some
//    por baixo da Caixa) e a coluna P/L da grade fica fora da tela. Em 1920 os
//    oito tiles e as dez colunas cabem.
//  · Em 900 px de ALTURA a grade mostra 3 linhas; em 1200, com a captura
//    recolhida, mostra 9 — e o clipe do "Sugerir tipsters" existe justamente
//    para mostrar linha preenchendo.
//
// `DPR` 1,5 captura em 2880x1800 e o ffmpeg reduz para 1440 — supersampling
// barato, e e' o que salva a legibilidade da grade (fonte de 11 px reduzida 1:1
// sai borrada depois da compressao VP9).
const LARGURA = 1920, ALTURA = 1200, DPR = 1.5;
const SAIDA_LARGURA = 1440;  // largura entregue (a altura sai da proporcao)
const FPS = 15;              // captura de tela nao precisa de mais; e pesa menos
const TETO_KB = 800;         // teto do .webm para a landing (pedido do Feca)

const espera = (ms) => new Promise((r) => setTimeout(r, ms));

function ffmpegExe() {
  // O ffmpeg nao esta no PATH neste ambiente — vem junto do `imageio_ffmpeg`.
  const out = execFileSync("python", ["-c", "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())"],
    { encoding: "utf8" }).trim();
  if (!fs.existsSync(out)) throw new Error(`ffmpeg nao encontrado em ${out}`);
  return out;
}
const FFMPEG = ffmpegExe();

// ─────────────────────────────────────────────────────────────────────────────
// Ponteiro sintetico
// ─────────────────────────────────────────────────────────────────────────────
// Desenhado no documento da CASCA (nao no iframe): a casca cobre a tela inteira,
// entao um so elemento serve para apontar qualquer coisa, dentro ou fora dos
// iframes. `pointer-events:none` para ele nunca roubar o clique de verdade —
// quem clica e' o `page.mouse`, que fala com o navegador, nao com o DOM.
async function cursorInit(page) {
  await page.evaluate(() => {
    if (document.getElementById("__gravcursor")) return;
    const c = document.createElement("div");
    c.id = "__gravcursor";
    c.style.cssText = [
      "position:fixed", "left:0", "top:0", "width:22px", "height:22px",
      "margin:-11px 0 0 -11px", "border-radius:50%", "pointer-events:none",
      "z-index:2147483647", "opacity:0",
      "background:radial-gradient(circle at 40% 38%, rgba(255,255,255,.95), rgba(255,255,255,.28) 55%, rgba(255,255,255,0) 70%)",
      "box-shadow:0 0 0 1.5px rgba(255,255,255,.55), 0 2px 10px rgba(0,0,0,.55)",
      "transition:opacity .25s linear",
    ].join(";");
    const r = document.createElement("div");
    r.id = "__gravring";
    r.style.cssText = [
      "position:fixed", "left:0", "top:0", "width:14px", "height:14px",
      "margin:-7px 0 0 -7px", "border-radius:50%", "pointer-events:none",
      "z-index:2147483646", "opacity:0",
      "border:2px solid rgba(255,255,255,.9)",
    ].join(";");
    document.body.appendChild(c);
    document.body.appendChild(r);
    window.__gravPos = (x, y) => {
      c.style.transform = `translate(${x}px,${y}px)`;
      c.style.opacity = "1";
    };
    window.__gravPulso = (x, y) => {
      r.style.transition = "none";
      r.style.transform = `translate(${x}px,${y}px) scale(.4)`;
      r.style.opacity = "1";
      requestAnimationFrame(() => {
        r.style.transition = "transform .38s ease-out, opacity .38s ease-out";
        r.style.transform = `translate(${x}px,${y}px) scale(3)`;
        r.style.opacity = "0";
      });
    };
  });
}

let _cx = LARGURA / 2, _cy = ALTURA - 60;

/** Move o ponteiro (e o mouse real) em arco suave — passo a passo, para o
 *  screencast ter quadros do trajeto e nao um teleporte. */
async function mover(page, x, y, ms = 520) {
  const passos = Math.max(6, Math.round((ms / 1000) * FPS * 1.6));
  const x0 = _cx, y0 = _cy;
  for (let i = 1; i <= passos; i++) {
    const t = i / passos;
    const e = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;   // easeInOutQuad
    const px = x0 + (x - x0) * e, py = y0 + (y - y0) * e;
    await page.mouse.move(px, py);
    await page.evaluate((a, b) => window.__gravPos(a, b), px, py);
    await espera(ms / passos);
  }
  _cx = x; _cy = y;
}

async function clicar(page, x, y) {
  await page.evaluate((a, b) => window.__gravPulso(a, b), x, y);
  await page.mouse.click(x, y);
}

// ─────────────────────────────────────────────────────────────────────────────
// Geometria: elemento DENTRO do iframe -> coordenada da pagina
// ─────────────────────────────────────────────────────────────────────────────
// O `page.mouse` fala em pixels da pagina DE CIMA, e o alvo vive num iframe.
//
// ⚠️ `elementHandle.boundingBox()` de um elemento dentro do iframe JA VEM na
// coordenada da pagina de cima — ele passa pelo `DOM.getBoxModel` do CDP, que
// devolve a caixa no espaco do frame PRINCIPAL, nao no do iframe. Somar o
// retangulo do <iframe> parece obvio e DOBRA o deslocamento (medido: botao em
// x=1000 dentro do iframe, iframe em x=264, boundingBox ja devolvendo 1264).
// O modo de falha e' mudo: o clique cai fora, nada acontece, nenhum erro, e o
// clipe sai com a tela parada. Por isso este comentario e por isso o gate.
async function rect(page, frameId, sel) {
  const fr = await page.$(`#${frameId}`);
  if (!fr) throw new Error(`iframe #${frameId} nao existe`);
  const frame = await fr.contentFrame();
  const el = await frame.$(sel);
  if (!el) throw new Error(`seletor ${sel} nao existe em #${frameId}`);
  const b = await el.boundingBox();
  if (!b || b.width < 1 || b.height < 1) throw new Error(`${sel} sem caixa visivel`);
  return { x: b.x, y: b.y, w: b.width, h: b.height };
}

const centro = (r) => ({ x: Math.round(r.x + r.w / 2), y: Math.round(r.y + r.h / 2) });

/** Move ate o elemento e clica. Um lugar so: e' o gesto que todo roteiro faz. */
async function clicarEm(page, frameId, sel, ms) {
  const c = centro(await rect(page, frameId, sel));
  await mover(page, c.x, c.y, ms);
  await espera(140);
  await clicar(page, c.x, c.y);
}

/** Digita no campo focado, tecla a tecla — para o clipe MOSTRAR a digitacao. */
async function digitar(page, texto, msPorTecla = 85) {
  for (const ch of texto) {
    await page.keyboard.type(ch);
    await espera(msPorTecla);
  }
}

/** Le o texto de um elemento do iframe (usado pelos gates das cenas). */
async function texto(page, frameId, sel) {
  const fr = await page.$(`#${frameId}`);
  const frame = await fr.contentFrame();
  return frame.evaluate((s) => (document.querySelector(s) || {}).textContent || "", sel);
}

/** Espera o `#exp-status` dizer alguma coisa e devolve o texto.
 *
 *  Existe porque `setExpStatus` LIMPA a mensagem sozinho depois de 3,5 s: um gate
 *  que lesse o status depois da gravacao encontraria string vazia e acusaria
 *  falha numa cena que deu certo. Como bonus, a espera acompanha o tempo REAL do
 *  preenchimento (uma requisicao por linha) em vez de um `espera()` chutado. */
async function esperarStatus(page, limite = 20000) {
  const t0 = Date.now();
  while (Date.now() - t0 < limite) {
    const t = (await texto(page, FRAME, "#exp-status")).trim();
    if (t && !/^Sugerindo/.test(t)) return t;
    await espera(200);
  }
  return "";
}

// ─────────────────────────────────────────────────────────────────────────────
// Captura
// ─────────────────────────────────────────────────────────────────────────────
async function gravarCena(page, cdp, roteiro) {
  const quadros = [];
  const onFrame = async (ev) => {
    quadros.push({ t: ev.metadata.timestamp, buf: Buffer.from(ev.data, "base64") });
    try { await cdp.send("Page.screencastFrameAck", { sessionId: ev.sessionId }); }
    catch { /* sessao ja fechada no fim da cena */ }
  };
  cdp.on("Page.screencastFrame", onFrame);
  await cdp.send("Page.startScreencast", {
    format: "jpeg", quality: 82, maxWidth: LARGURA * DPR, maxHeight: ALTURA * DPR,
    everyNthFrame: 1,
  });
  try {
    await roteiro();
  } finally {
    await cdp.send("Page.stopScreencast").catch(() => {});
    cdp.off("Page.screencastFrame", onFrame);
  }
  return quadros;
}

/** Escreve os quadros + a lista do demuxer `concat`, com a duracao REAL de cada
 *  um (o screencast nao tem taxa fixa). O ultimo ganha uma cauda curta. */
function escreverQuadros(quadros, dir) {
  fs.mkdirSync(dir, { recursive: true });
  const linhas = [];
  for (let i = 0; i < quadros.length; i++) {
    const nome = `q${String(i).padStart(5, "0")}.jpg`;
    fs.writeFileSync(path.join(dir, nome), quadros[i].buf);
    const dur = i + 1 < quadros.length
      ? Math.max(1 / 60, Math.min(2.0, quadros[i + 1].t - quadros[i].t))
      : 0.45;
    linhas.push(`file '${nome}'`, `duration ${dur.toFixed(4)}`);
  }
  // O concat ignora a duracao do ultimo arquivo; repeti-lo e' o truque padrao
  // para o quadro final nao sumir do video.
  if (quadros.length) linhas.push(`file 'q${String(quadros.length - 1).padStart(5, "0")}.jpg'`);
  fs.writeFileSync(path.join(dir, "lista.txt"), linhas.join("\n") + "\n");
  return path.join(dir, "lista.txt");
}

function ff(args) {
  execFileSync(FFMPEG, ["-hide_banner", "-loglevel", "error", "-y", ...args], { stdio: "inherit" });
}

const kb = (p) => Math.round(fs.statSync(p).size / 1024);

/** `recorte` (opcional) chega em px LOGICOS e vira crop em px de CAPTURA (x DPR).
 *  Toda dimensao sai PAR: o ffmpeg recusa largura/altura impar em yuv420p. */
function filtro(recorte) {
  const par = (n) => Math.max(2, Math.round(n / 2) * 2);
  // NORMALIZA a entrada antes de qualquer coisa. O screencast NAO garante quadro
  // do mesmo tamanho o tempo todo: num relayout ele manda alguns quadros menores,
  // o ffmpeg reinicializa o grafo de filtros e o `crop` estoura com "Invalid too
  // big or non positive size" — no meio da montagem, com os quadros ja escritos.
  const partes = [`fps=${FPS}`, `scale=${par(LARGURA * DPR)}:${par(ALTURA * DPR)}`];
  if (recorte) {
    partes.push(`crop=${par(recorte.w * DPR)}:${par(recorte.h * DPR)}`
      + `:${par(recorte.x * DPR)}:${par(recorte.y * DPR)}`);
    // Recorte sai no tamanho LOGICO (1:1 em CSS px): ele ja e' pequeno, e ampliar
    // ou reduzir de novo so tiraria nitidez do texto que o clipe existe para ler.
    partes.push(`scale=${par(recorte.w)}:${par(recorte.h)}:flags=lanczos`);
  } else {
    partes.push(`scale=${SAIDA_LARGURA}:${par(SAIDA_LARGURA * ALTURA / LARGURA)}:flags=lanczos`);
  }
  // Sem `setsar=1` o ffmpeg compensa o arredondamento par com pixel nao-quadrado
  // (SAR 511:510), e o player estica o video de volta — texto borrado de graca.
  partes.push("setsar=1");
  return partes.join(",");
}

function montar(nome, listaTxt, recorte, crf) {
  fs.mkdirSync(SAIDA, { recursive: true });
  const vf = filtro(recorte);
  const webm = path.join(SAIDA, `${nome}.webm`);
  const mp4 = path.join(SAIDA, `${nome}.mp4`);
  const poster = path.join(SAIDA, `${nome}.poster.jpg`);
  const entrada = ["-f", "concat", "-safe", "0", "-i", listaTxt];

  ff([...entrada, "-vf", vf, "-c:v", "libvpx-vp9", "-crf", String(crf), "-b:v", "0",
      "-row-mt", "1", "-deadline", "good", "-cpu-used", "2",
      "-pix_fmt", "yuv420p", "-an", webm]);
  // `-pix_fmt yuv420p` no mp4 nao e' enfeite: sem ele o Safari nao toca o video.
  ff([...entrada, "-vf", vf, "-c:v", "libx264", "-crf", "26", "-preset", "slow",
      "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", mp4]);
  return { webm, mp4, poster };
}

/** Poster: quadro do FIM da cena, nao do comeco. O primeiro quadro de quase todo
 *  roteiro e' a tela antes de acontecer o que o clipe existe para mostrar — poster
 *  assim vende uma tela vazia. */
function poster(mp4, destino, segundosDoFim = 1.2) {
  // `-sseof` = "N segundos antes do fim" — evita ter de descobrir a duracao do
  // arquivo (que o ffmpeg so escreve no stderr, e parsear stderr e' pior).
  ff(["-sseof", `-${segundosDoFim}`, "-i", mp4, "-frames:v", "1", "-q:v", "3", destino]);
}

// ─────────────────────────────────────────────────────────────────────────────
// Cenas
// ─────────────────────────────────────────────────────────────────────────────
// `preparar` roda ANTES da gravacao comecar (deixa a tela no estado inicial);
// `roteiro` roda COM a camera ligada. `gate` roda depois e ESTOURA se a cena nao
// aconteceu — clipe mudo e' o modo de falha caro aqui: sai um arquivo bonito de
// uma tela onde nada foi clicado.
const FRAME = "fr-plan";

/** Seleciona a conta de id `id` por dentro (sem gesto) — usado no `preparar`. */
async function selecionarConta(page, id) {
  const fr = await page.$(`#${FRAME}`);
  const frame = await fr.contentFrame();
  // Identificador NU (`parceirosCache`), nunca `window.parceirosCache`: no
  // index.html ele e' `let` de topo, e `let` de topo de script classico NAO vira
  // propriedade do window. Pelo window a leitura devolve `undefined` — sem erro,
  // so uma espera que nunca termina.
  await frame.evaluate((pid) => {
    const todas = Object.values(parceirosCache || {}).flat();
    const p = todas.find((x) => x.id === pid);
    if (!p) throw new Error("conta " + pid + " nao esta no cache");
    mostrarView("extracao");
    selecionarParceiro(p);
  }, id);
  await espera(2200);
}

/** Nome da conta ativa no extrator ('' se nenhuma). */
async function contaAtiva(page) {
  const fr = await page.$(`#${FRAME}`);
  const frame = await fr.contentFrame();
  return frame.evaluate(() => (parceiroSelecionado || {}).nome || "");
}

/** Aquece o modelo do matcher no servidor com um bilhete de mentira.
 *
 *  O 1o `POST /tipsters/sugerir` depois do boot TREINA o Naive-Bayes sobre 21 mil
 *  rotulos (~1-2 s). Em producao o modelo vive em cache com TTL de 5 min e essa
 *  espera praticamente nunca acontece; grava-la seria filmar um artefato do boot
 *  do servidor de demo, nao o produto. READ-ONLY: a rota nao grava nada. */
async function aquecerMatcher(page) {
  const fr = await page.$(`#${FRAME}`);
  const frame = await fr.contentFrame();
  await frame.evaluate(() => fetch("/tipsters/sugerir", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ bilhetes: [{ id: "0", casa: "Bet365", esporte: "Futebol",
                                        aposta: "ML", stake: "100,00", descricao: "aquecimento" }] }),
  }).then((r) => r.json()));
}

/** Recolhe ou expande a area de CAPTURA (botao real da tela, `#btn-recolher-cap`).
 *
 *  Recolhida, a grade passa de 3 para 8 linhas visiveis — e' o que faz o clipe do
 *  "Sugerir tipsters" mostrar a coluna preenchendo. Expandida, a Caixa fica com o
 *  extrato inteiro na tela, que e' o que os clipes de caixa precisam. Como a
 *  preferencia mora no localStorage, ela ATRAVESSA as cenas: por isso o estado e'
 *  declarado sempre, nunca "clicado uma vez". */
async function recolherCaptura(page, recolher) {
  const fr = await page.$(`#${FRAME}`);
  const frame = await fr.contentFrame();
  await frame.evaluate((quer) => {
    const sec = document.getElementById("upload-section");
    const btn = document.getElementById("btn-recolher-cap");
    if (!sec || !btn) throw new Error("botao de recolher captura nao existe");
    if (sec.classList.contains("cap-recolhida") !== quer) btn.click();
  }, recolher);
  await espera(700);
}

async function limparConta(page) {
  const fr = await page.$(`#${FRAME}`);
  const frame = await fr.contentFrame();
  await frame.evaluate(() => mostrarView("contas"));
  await espera(1200);
}

const CENAS = [
  {
    // 1. A conta ativa: escolher a conta e ver a grade + a faixa de KPIs
    //    (P/L, turnover, apostas, win rate) trocarem junto.
    nome: "extracao",
    crf: 36,
    // Comeca COM conta ativa, de proposito. Sem conta a tela vira o Painel de
    // Contas — outra pagina, onde o seletor de conta nem existe (largura 0) — e o
    // clipe perderia o unico gesto que ele quer mostrar.
    preparar: async (page) => {
      await selecionarConta(page, 1);
      await recolherCaptura(page, true);
    },
    roteiro: async (page, ctx) => {
      await espera(900);
      await clicarEm(page, FRAME, "#acctSelBtn", 520);       // abre o seletor de conta
      await espera(800);
      await clicarEm(page, FRAME, "#acctTree .acct-acct", 460);   // 1a conta da lista
      await espera(2700);                                    // grade + KPIs pintam
      ctx.contas = [await contaAtiva(page)];
      await clicarEm(page, FRAME, "#acctNext", 520);         // proxima conta
      await espera(2400);
      ctx.contas.push(await contaAtiva(page));
      await clicarEm(page, FRAME, "#acctNext", 280);
      await espera(2000);
      ctx.contas.push(await contaAtiva(page));
    },
    // O gate cobra os TRES cliques, nao so o ultimo estado: clique que erra o alvo
    // nao levanta erro nenhum (ver `rect`), e sem isto a cena sairia com a tela
    // parada e o script dizendo "ok".
    gate: async (page, ctx) => {
      const t = await texto(page, FRAME, "#ctxKpis");
      if (!/Turnover/.test(t)) throw new Error("faixa de KPIs vazia");
      const c = ctx.contas || [];
      if (c.length !== 3 || new Set(c).size !== 3 || c.some((x) => !x)) {
        throw new Error(`as 3 contas deviam ser distintas: ${JSON.stringify(c)}`);
      }
      return c.join(" → ");
    },
  },
  {
    // 2. O clipe que vende: um clique preenche a coluna Tipster.
    //    O badge azul FILTRA a grade para as linhas sem tipster (recurso real da
    //    barra, s262) — sem ele as ~30 vazias ficam diluidas entre 100 linhas e
    //    o preenchimento nao aparece.
    nome: "sugerir-tipsters",
    crf: 36,
    preparar: async (page) => {
      await selecionarConta(page, 1);
      await recolherCaptura(page, true);       // grade alta: 8 linhas na tela
      await aquecerMatcher(page);
    },
    roteiro: async (page, ctx) => {
      await espera(1400);
      await clicarEm(page, FRAME, "#s-info", 620);           // filtra: so sem tipster
      await espera(1800);
      await clicarEm(page, FRAME, "#btn-sugerir-tip", 620);
      ctx.status = await esperarStatus(page);                // preenche linha a linha
      await espera(2800);                                    // o resultado na tela
    },
    gate: async (page, ctx) => {
      const m = /^(\d+) de (\d+) sugerido/.exec(ctx.status || "");
      if (!m) throw new Error(`#exp-status nao confirmou sugestao: "${ctx.status}"`);
      if (Number(m[1]) < 8) throw new Error(`so ${m[1]} sugestoes — clipe fraco`);
      return `${m[1]} de ${m[2]} sugeridos`;
    },
  },
  {
    // 3a. Caixa Inteligente que BATE. Conta 2 nasce "nunca conferida": o clipe
    //     digita o disponivel projetado e o box vira o verde "Bate com a casa".
    nome: "caixa-confere",
    crf: 38,
    recorte: { de: "#ctxKpis", ate: "#caixaBox", margem: 22, baixo: 90 },
    preparar: async (page) => {
      await recolherCaptura(page, false);      // caixa com o extrato inteiro na tela
      await selecionarConta(page, 2);
    },
    roteiro: async (page) => {
      await espera(1500);
      await clicarEm(page, FRAME, "#cx-conf-val", 560);
      await espera(320);
      const v = await valorProjetado(page);
      await digitar(page, v, 95);
      await espera(650);
      await clicarEm(page, FRAME, ".cx__go", 420);
      await espera(3600);
    },
    gate: async (page) => {
      const t = await texto(page, FRAME, ".cx__diver");
      if (!/Bate com a casa/.test(t)) throw new Error(`caixa nao fechou verde: "${t.trim()}"`);
      return "Bate com a casa";
    },
  },
  {
    // 3b. A outra ponta, que e' o motivo de a Caixa existir: o saldo da casa NAO
    //     bate e a tela diz de quanto e' o buraco, com o botao de lancar o ajuste.
    nome: "caixa-divergencia",
    crf: 38,
    recorte: { de: "#ctxKpis", ate: "#caixaBox", margem: 22, baixo: 90 },
    preparar: async (page) => {
      await recolherCaptura(page, false);
      await selecionarConta(page, 4);
    },
    roteiro: async (page) => {
      await espera(1500);
      await clicarEm(page, FRAME, "#cx-conf-val", 560);
      await espera(320);
      // Digita MENOS do que o projetado: e' o caso "faltam X na conta", o que
      // manda conferir saque nao lancado.
      const v = await valorProjetado(page, -638.68);
      await digitar(page, v, 95);
      await espera(650);
      await clicarEm(page, FRAME, ".cx__go", 420);
      await espera(3800);
    },
    gate: async (page) => {
      const t = await texto(page, FRAME, ".cx__diver");
      if (!/Faltam|Sobram/.test(t)) throw new Error(`caixa nao acusou divergencia: "${t.trim()}"`);
      return t.trim().slice(0, 46);
    },
  },
];

/** Le o `disponivel` que a propria tela projetou e devolve em texto pt-BR.
 *  LER da tela, nunca cravar um numero no roteiro: o valor muda com a data (a
 *  base ficticia e' gerada relativa a HOJE) e um numero cravado transformaria o
 *  clipe "bate com a casa" num clipe de divergencia sem ninguem perceber. */
async function valorProjetado(page, delta = 0) {
  const fr = await page.$(`#${FRAME}`);
  const frame = await fr.contentFrame();
  const n = await frame.evaluate(() => (caixaAtual || {}).disponivel);
  if (typeof n !== "number") throw new Error("caixa nao esta ligada nesta conta");
  return (n + delta).toFixed(2).replace(".", ",");
}

// ─────────────────────────────────────────────────────────────────────────────
async function principal() {
  const alvo = CENAS.filter((c) => !FILTRO.length || FILTRO.includes(c.nome));
  if (!alvo.length) throw new Error(`nenhuma cena casa ${FILTRO.join(", ")}`);

  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: "new",
    defaultViewport: { width: LARGURA, height: ALTURA, deviceScaleFactor: DPR },
    args: ["--no-sandbox", "--hide-scrollbars", "--force-color-profile=srgb",
           "--font-render-hinting=none"],
  });
  const page = await browser.newPage();
  const cdp = await page.createCDPSession();

  console.log("abrindo a casca…");
  await page.goto(`${BASE}/app#plan`, { waitUntil: "networkidle2", timeout: 60000 });
  // A grade so existe depois de o extrator carregar casas + contas. Esperar o
  // CACHE, nao o relogio: `carregarCasas` faz um fetch por casa (29 aqui).
  // A espera roda DENTRO do iframe porque `parceirosCache` e' `let` de topo — de
  // fora, por `contentWindow`, ele nao existe (ver `selecionarConta`).
  const frPlan = await page.waitForSelector("#fr-plan");
  const framePlan = await frPlan.contentFrame();
  await framePlan.waitForFunction(
    () => Object.values(parceirosCache || {}).flat().length > 50,
    { timeout: 90000, polling: 400 },
  );
  await cursorInit(page);
  console.log("contas carregadas.\n");

  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "sharpen-grav-"));
  const relatorio = [];

  for (const cena of alvo) {
    process.stdout.write(`  ${cena.nome} … `);
    await cena.preparar(page);
    await cursorInit(page);          // o iframe pode ter re-renderizado por cima
    // O recorte e' medido ANTES da gravacao: o elemento pode mudar de altura no
    // meio da cena (a caixa cresce quando a divergencia aparece), e um crop que
    // muda de tamanho no meio nao existe — o ffmpeg quer um retangulo so.
    // O recorte e' a UNIAO de dois elementos (`de` … `ate`), medida agora. Dois e
    // nao um porque o painel sozinho nao diz de QUE conta ele fala — a faixa de
    // KPIs ao lado e' que da o P/L, o turnover e o nome. Ler a geometria da tela
    // em vez de cravar pixel: regiao chutada quebra em silencio quando a tela muda
    // de altura (a licao do `capturar.mjs`).
    let recorte = null;
    if (cena.recorte) {
      const a = await rect(page, FRAME, cena.recorte.de);
      const b = await rect(page, FRAME, cena.recorte.ate);
      const m = cena.recorte.margem || 0;
      const x = Math.max(0, Math.min(a.x, b.x) - m);
      const y = Math.max(0, Math.min(a.y, b.y) - m);
      const dir = Math.max(a.x + a.w, b.x + b.w) + m;
      // Folga embaixo: a caixa CRESCE quando a divergencia aparece, e crop nao
      // acompanha (o ffmpeg quer um retangulo so para o clipe inteiro).
      const bai = Math.max(a.y + a.h, b.y + b.h) + m + (cena.recorte.baixo || 0);
      recorte = { x, y, w: Math.min(LARGURA - x, dir - x), h: Math.min(ALTURA - y, bai - y) };
    }

    // `ctx` e' o que o roteiro observou ENQUANTO gravava. Existe porque parte do
    // que o gate precisa conferir some da tela sozinha (o `#exp-status` se apaga
    // em 3,5 s) — ler depois seria acusar falha numa cena que deu certo.
    const ctx = {};
    const quadros = await gravarCena(page, cdp, () => cena.roteiro(page, ctx));
    const nota = cena.gate ? await cena.gate(page, ctx) : "";
    if (quadros.length < FPS * 3) throw new Error(`${cena.nome}: so ${quadros.length} quadros`);

    const dir = path.join(tmp, cena.nome);
    const lista = escreverQuadros(quadros, dir);
    const { webm, mp4, poster: pj } = montar(cena.nome, lista, recorte, cena.crf);
    poster(mp4, pj);
    fs.rmSync(dir, { recursive: true, force: true });

    const segundos = quadros.length > 1 ? (quadros.at(-1).t - quadros[0].t) : 0;
    relatorio.push({ nome: cena.nome, s: segundos, webm: kb(webm), mp4: kb(mp4), poster: kb(pj), nota });
    console.log(`ok — ${segundos.toFixed(1)}s · ${quadros.length} quadros`
      + ` · webm ${kb(webm)} KB · mp4 ${kb(mp4)} KB${nota ? ` · ${nota}` : ""}`);
  }

  await browser.close();
  fs.rmSync(tmp, { recursive: true, force: true });

  console.log(`\n${relatorio.length} clipe(s) em ${path.resolve(SAIDA)}`);
  const gordos = relatorio.filter((r) => r.webm > TETO_KB);
  if (gordos.length) {
    console.error(`\n!! ${gordos.length} clipe(s) acima do teto de ${TETO_KB} KB no .webm:`);
    gordos.forEach((r) => console.error(`   ${r.nome}: ${r.webm} KB`));
    console.error("   Corte duracao ou suba o `crf` da cena ANTES de baixar a resolucao.");
    process.exitCode = 2;
  }
}

principal().catch((e) => { console.error(e); process.exit(1); });
