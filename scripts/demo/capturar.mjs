/**
 * Captura as telas do Sharpen contra o `servidor_demo.py` (base ficticia).
 *
 *   1) python scripts/demo/servidor_demo.py 8010
 *   2) node scripts/demo/capturar.mjs [saida] [porta]
 *
 * Usa puppeteer-core com o Chrome do sistema (nao baixa Chromium).
 *
 * Por que nao basta `chrome --headless --screenshot`: o app e' uma casca com
 * dois iframes e graficos em canvas. Sem dirigir a pagina, tres coisas quebram
 * -- e as tres ja estao resolvidas aqui:
 *
 *   a) A Visao Geral e' a pagina inicial do dash. Chegar nela pelo hash NAO
 *      dispara `showPage`, e os graficos saem VAZIOS. Corrige com "bounce":
 *      vai para outra aba e volta, o que forca um render limpo.
 *   b) O dash monta ~24 mil apostas. Esperar tempo fixo e' loteria; esperamos
 *      `_dataBuiltMs > 0` dentro do iframe, que e' o sinal de dado aplicado.
 *   c) Chart.js so redesenha no `resize`. Depois de ajustar o viewport,
 *      disparamos o evento dentro do iframe.
 */
import fs from "node:fs";
import path from "node:path";
import puppeteer from "puppeteer-core";

const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const SAIDA = process.argv[2] || "capturas";
const PORTA = process.argv[3] || "8010";
const BASE = `http://127.0.0.1:${PORTA}`;

// Cada tela: hash da casca, qual iframe carrega o conteudo e a altura util.
//
// A ordem e a numeracao seguem a NARRATIVA da landing, nao a da sidebar: começa
// no panorama, desce para a prova estatistica e termina na camada de operacao
// (contas, fornecedores, custos), que e' o que nenhum tracker concorrente tem.
//
// As 5 telas marcadas `novo` entraram na s294. Sem elas a pagina de vendas nao
// conseguia mostrar quatro dos cinco diferenciais que ela promete -- o pipeline
// capturava a analise e deixava a operacao inteira de fora.
// `acao` roda DENTRO do iframe antes do print, para fotografar estado que so
// existe depois de um clique (aba trocada, box aberto). Vai como funcao de
// verdade, nao string: a CSP do dash e' `default-src 'self'` e `eval` dentro do
// iframe seria bloqueado -- `frame.evaluate` do puppeteer nao passa por eval.
const TELAS = [
  { nome: "01-inicio",           hash: "inicio",              frame: "fr-inicio", h: 1500 },
  { nome: "02-visao-geral",      hash: "dash/overview",       frame: "fr-dash",   h: 2400, bounce: true },
  { nome: "03-metricas",         hash: "dash/metrics",        frame: "fr-dash",   h: 2100 },
  { nome: "04-apostas",          hash: "dash/apostas",        frame: "fr-dash",   h: 1700 },
  { nome: "05-em-aberto",        hash: "dash/abertas",        frame: "fr-dash",   h: 1400 },  // novo
  { nome: "06-tipsters",         hash: "dash/tipsters",       frame: "fr-dash",   h: 1900 },
  // As duas telas da atribuicao automatica. A lista fechada de tipsters nao
  // mostra o recurso -- ele vive no box ABERTO e na aba Casas.
  { nome: "07-tipster-perfil",   hash: "dash/tipster_metodo", frame: "fr-dash",   h: 1700,   // novo
    acao: () => window.tmToggle("Método Ártico") },
  { nome: "08-casas-atribuicao", hash: "dash/tipster_metodo", frame: "fr-dash",   h: 1700,   // novo
    acao: () => window.tmTab("casas") },
  { nome: "09-bookies",          hash: "dash/casas",          frame: "fr-dash",   h: 1800 },
  { nome: "10-esportes",         hash: "dash/sports",         frame: "fr-dash",   h: 1800 },
  { nome: "11-fornecedores",     hash: "dash/parceiros",      frame: "fr-dash",   h: 2000 },  // novo
  { nome: "12-custos-contas",    hash: "dash/custos",         frame: "fr-dash",   h: 1520 },  // novo
  { nome: "13-custos-tipsters",  hash: "dash/custos_tipster", frame: "fr-dash",   h: 1500 },  // novo
  { nome: "14-extracao",         hash: "plan",                frame: "fr-plan",   h: 1400 },
];

// RECORTES: foto de UM elemento, para a landing usar como destaque de recurso.
//
// A tela inteira tem 2.000+ px de altura; encolhida num card de pagina de vendas
// o texto some e o print deixa de provar o que promete. Recorte por SELETOR, nao
// por regiao em pixel: regiao chutada quebra em silencio quando a tela muda de
// altura, e o corte errado so aparece quando alguem olha a landing publicada.
// `maxH` (px logicos) e' OBRIGATORIO e nao e' enfeite: o elemento so pinta o que
// cabe no viewport. `#card-parc_table` tem 102 linhas e ~7.500 px -- a foto dele
// saiu PRETA, e o script imprimiu "ok" do mesmo jeito (s294). Limitar a altura
// antes do clique garante regiao pintada, e de quebra e' o que a landing quer:
// cabecalho + uma duzia de linhas provam as colunas; 102 linhas nao provam mais.
const RECORTES = [
  { nome: "r1-pl-liquido",       hash: "dash/overview",       frame: "fr-dash", sel: "#kpiGrid",                maxH: 320, bounce: true },
  { nome: "r2-risco",            hash: "dash/overview",       frame: "fr-dash", sel: "#card-ov_risco",          maxH: 260 },
  { nome: "r3-cenario",          hash: "dash/overview",       frame: "fr-dash", sel: "#card-ov_streaks",        maxH: 260 },
  { nome: "r4-contas-periodo",   hash: "dash/parceiros",      frame: "fr-dash", sel: "#card-parc_table",        maxH: 620 },
  { nome: "r5-casa-fornecedor",  hash: "dash/parceiros",      frame: "fr-dash", sel: "#card-cross_table",       maxH: 620 },
  { nome: "r6-custo-fornecedor", hash: "dash/parceiros",      frame: "fr-dash", sel: "#card-forn_custo_cards",  maxH: 700 },
  { nome: "r7-atribuicao-casa",  hash: "dash/tipster_metodo", frame: "fr-dash", sel: "#paneCasas",              maxH: 760,
    acao: () => window.tmTab("casas") },
];

const LARGURA = 1600;
const espera = (ms) => new Promise((r) => setTimeout(r, ms));

/**
 * Espera o Monte Carlo terminar. Retorna `false` se estourar o prazo.
 *
 * Por que o relogio nao serve: `Diagnostico de Risco` e `Nivel de Solidez` sao
 * bootstrap de 10.000 simulacoes sobre 24 mil apostas, num Web Worker. O tempo
 * varia com a maquina, entao `espera(2200)` fotografava o selo "calculando…" --
 * e era justamente o painel que sustenta o argumento estatistico da pagina.
 *
 * O sinal e' o DOM: `mcSpinner()` (app.js) escreve "calculando…" enquanto o
 * numero nao chegou. Sumiu o texto, o valor esta na tela. Esperamos a AUSENCIA
 * do sinal de espera, que e' o unico estado que garante o numero pintado.
 */
async function esperarMonteCarlo(page, frameId, timeout = 180000) {
  const t0 = Date.now();
  let viuSpinner = false;
  while (Date.now() - t0 < timeout) {
    const calculando = await page.evaluate((id) => {
      const fr = document.getElementById(id);
      try {
        const doc = fr && fr.contentDocument;
        if (!doc || !doc.body) return true;      // iframe ainda nao pronto
        return doc.body.innerText.includes("calculando…");
      } catch { return true; }
    }, frameId);
    if (calculando) viuSpinner = true;
    // `esperou` so e' verdadeiro se o selo REALMENTE apareceu. Sem isso nao da
    // para distinguir "o calculo terminou" de "esta funcao nunca viu nada" --
    // e uma espera que nunca ve nada e' um no-op passando por gate (s294: a
    // primeira versao disto era exatamente isso, e passou verde nas 13 telas).
    if (!calculando) return { ok: true, esperou: viuSpinner, ms: Date.now() - t0 };
    await espera(250);
  }
  return { ok: false, esperou: viuSpinner, ms: Date.now() - t0 };
}

/** Leva a casca ate a tela e aplica o clique, se houver. */
async function navegar(page, tela) {
  if (tela.bounce) {
    // (a) forca render limpo da pagina inicial do dash
    await page.evaluate(() => { location.hash = "dash/apostas"; });
    await espera(900);
  }
  await page.evaluate((h) => { location.hash = h; }, tela.hash);
  await espera(1600);

  if (tela.acao) {
    // O render da aba Tipster / Metodo e' async (busca cadastro + taxonomia),
    // entao a acao pode chegar antes de a funcao global existir. Tenta ate ela
    // pegar, e ESTOURA se nunca pegar -- print de estado que nao abriu seria
    // indistinguivel de print da tela normal.
    let aplicou = false;
    for (let t = 0; t < 20 && !aplicou; t++) {
      const alvo = await page.$(`#${tela.frame}`);
      const frame = await alvo.contentFrame();
      try { await frame.evaluate(tela.acao); aplicou = true; }
      catch { await espera(500); }
    }
    if (!aplicou) throw new Error(`acao de ${tela.nome} nunca aplicou`);
    await espera(1400);
  }
}

/** Esconde o que nao pode aparecer em material de venda. */
async function limpar(page) {
  await page.evaluate(() => {
    const fr = document.getElementById("fr-inicio");
    if (!fr || !fr.contentDocument) return;
    // "Novidades" e "SharpenUp versao a versao" sao changelog INTERNO: expoem
    // numero de versao e nome de casa em desenvolvimento. Nao entram no print.
    const linha = fr.contentDocument.getElementById("novrow");
    if (linha) linha.style.display = "none";
  });
}

const falhas = [];      // Monte Carlo nao terminou
const vazias = [];      // recorte saiu em branco
const esperaram = [];   // prova de que a espera do Monte Carlo exerceu algo

async function capturar() {
  fs.mkdirSync(SAIDA, { recursive: true });
  const browser = await puppeteer.launch({
    executablePath: CHROME,
    headless: "new",
    defaultViewport: { width: LARGURA, height: 1200, deviceScaleFactor: 2 },
    args: ["--no-sandbox", "--hide-scrollbars", "--force-color-profile=srgb"],
  });
  const page = await browser.newPage();

  console.log("abrindo a casca…");
  await page.goto(`${BASE}/app#inicio`, { waitUntil: "networkidle2", timeout: 60000 });

  // Carrega o dash uma vez e espera o feed ser aplicado (24 mil linhas).
  await page.evaluate(() => { location.hash = "dash/overview"; });
  await page.waitForFunction(
    () => {
      const fr = document.getElementById("fr-dash");
      try { return fr && fr.contentWindow && fr.contentWindow._dataBuiltMs > 0; }
      catch { return false; }
    },
    { timeout: 120000, polling: 500 }
  );
  console.log("feed aplicado.");

  for (const tela of TELAS) {
    process.stdout.write(`  ${tela.nome} … `);
    await navegar(page, tela);

    await page.setViewport({ width: LARGURA, height: tela.h, deviceScaleFactor: 2 });
    // (c) Chart.js so recalcula no resize
    await page.evaluate((id) => {
      const fr = document.getElementById(id);
      if (fr && fr.contentWindow) fr.contentWindow.dispatchEvent(new Event("resize"));
    }, tela.frame);
    await espera(2200);

    // Nenhum print sai com "calculando…" na tela. Se estourar, o print SAI mesmo
    // assim -- mas gritando, para ninguem descobrir isso olhando a landing.
    const mc = await esperarMonteCarlo(page, tela.frame);
    if (!mc.ok) {
      falhas.push(tela.nome);
      process.stdout.write("[MONTE CARLO NAO TERMINOU] ");
    } else if (mc.esperou) {
      process.stdout.write(`[MC ${(mc.ms / 1000).toFixed(1)}s] `);
      esperaram.push(tela.nome);
    }

    await limpar(page);
    await espera(400);

    const destino = path.join(SAIDA, `${tela.nome}.png`);
    await page.screenshot({ path: destino });
    console.log("ok");
  }

  // ── Segundo passe: recortes por elemento ──────────────────────────────────
  console.log("\nrecortes:");
  // Viewport ALTO -- e este numero e' load-bearing, nao folga generosa.
  //
  // MEDIDO (s294): o card `Contas Individuais` fica em y=2600 na pagina de
  // Fornecedores. Com viewport 1400 a foto do elemento sai com 11.459 bytes de
  // NADA; com 3000 sai com 219 KB e com 4200 com 338 KB. Elemento fora do
  // viewport de layout nao e' pintado, e o puppeteer fotografa a regiao mesmo
  // assim -- sem erro nenhum. Rolar ate ele NAO resolve (tentado: o
  // `scrollIntoView` do DOM e o do puppeteer, os dois deram a mesma imagem
  // vazia); o que resolve e' o viewport CONTER o elemento.
  const VH_RECORTE = 4200;
  await page.setViewport({ width: LARGURA, height: VH_RECORTE, deviceScaleFactor: 2 });
  for (const rec of RECORTES) {
    process.stdout.write(`  ${rec.nome} … `);
    // `bounce` em TODO recorte: dois recortes seguidos na mesma pagina nao
    // disparam hashchange, entao o segundo fotografaria o DOM que o primeiro
    // deixou (inclusive o `maxHeight` injetado). Ir e voltar forca render limpo.
    await navegar(page, { ...rec, bounce: true });
    const mc = await esperarMonteCarlo(page, rec.frame);
    if (!mc.ok) { falhas.push(rec.nome); process.stdout.write("[MC NAO TERMINOU] "); }
    else if (mc.esperou) { process.stdout.write(`[MC ${(mc.ms / 1000).toFixed(1)}s] `); esperaram.push(rec.nome); }

    const alvo = await page.$(`#${rec.frame}`);
    const frame = await alvo.contentFrame();
    const el = await frame.$(rec.sel);
    // Seletor que nao casa e' erro DURO: sem isto o recorte simplesmente nao
    // sairia e a landing ficaria com um <img> quebrado, descoberto so no ar.
    if (!el) throw new Error(`recorte ${rec.nome}: seletor ${rec.sel} nao existe`);
    await frame.evaluate((sel, h) => {
      const n = document.querySelector(sel);
      n.style.maxHeight = h + "px";
      n.style.overflow = "hidden";
    }, rec.sel, rec.maxH);
    // Rolar pelo DOM, nao pelo `el.scrollIntoView()` do puppeteer: o dash rola
    // num container interno (`.main-content`), e elemento fora de vista NAO E'
    // PINTADO -- a foto sai do tamanho certo e completamente vazia. Era o que
    // acontecia com os dois cards do fim da pagina de Fornecedores; o card do
    // topo (custo por fornecedor) saia bem, e foi esse contraste que entregou
    // a causa. `block:"start"` sobe o elemento para o alto do scroller.
    await frame.evaluate((sel) => {
      document.querySelector(sel).scrollIntoView({ block: "start" });
    }, rec.sel);
    await espera(900);

    // Checa a CAUSA (elemento fora do viewport), nao so o sintoma (arquivo
    // pequeno): caixa nula ou abaixo da dobra = foto vazia garantida.
    const box = await el.boundingBox();
    if (!box || box.height < 40) {
      throw new Error(`recorte ${rec.nome}: elemento sem caixa visivel — nao da para fotografar`);
    }
    if (box.y + box.height > VH_RECORTE) {
      throw new Error(`recorte ${rec.nome}: elemento termina em y=${Math.round(box.y + box.height)},`
        + ` alem do viewport de ${VH_RECORTE}px. Suba VH_RECORTE ou reduza maxH.`);
    }

    const destino = path.join(SAIDA, `${rec.nome}.png`);
    await el.screenshot({ path: destino });
    // Desfaz o corte: o `bounce` re-renderiza quase tudo, mas painel que nao
    // re-monta guardaria o estilo e sairia truncado no recorte seguinte.
    await frame.evaluate((sel) => {
      const n = document.querySelector(sel);
      if (n) { n.style.maxHeight = ""; n.style.overflow = ""; }
    }, rec.sel);

    // Foto preta passa por "ok" (foi o que aconteceu antes do maxH). Mede a
    // variancia dos pixels: imagem chapada nao tem nenhuma.
    const bytes = fs.statSync(destino).size;
    if (bytes < 15000) {
      vazias.push(`${rec.nome} (${bytes} B)`);
      console.log(`ERRO — imagem vazia (${bytes} bytes)`);
    } else {
      console.log("ok");
    }
  }

  await browser.close();
  console.log(`\n${TELAS.length} telas + ${RECORTES.length} recortes em ${path.resolve(SAIDA)}`);
  // Se NENHUMA tela viu o selo, a espera nao esta exercendo nada: ou o sinal
  // mudou de texto, ou o painel nao esta renderizando. Nos dois casos o print
  // pode sair errado e o silencio seria pior que o aviso.
  if (!esperaram.length) {
    console.error("\n!! A espera do Monte Carlo NUNCA viu o selo 'calculando…'.");
    console.error("   Ou o calculo virou instantaneo, ou o sinal mudou — confira");
    console.error("   `mcSpinner` em assets/js/app.js antes de confiar nos prints.");
    process.exitCode = 3;
  } else {
    console.log(`Monte Carlo esperado em: ${esperaram.join(", ")}`);
  }
  if (falhas.length) {
    console.error(`\n!! ${falhas.length} tela(s) fotografadas com o Monte Carlo`
      + ` ainda rodando: ${falhas.join(", ")}`);
    console.error("   NAO usar essas na landing sem recapturar.");
    process.exitCode = 2;
  }
}

capturar().catch((e) => { console.error(e); process.exit(1); });
