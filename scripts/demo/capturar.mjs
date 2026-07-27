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
const TELAS = [
  { nome: "01-inicio",     hash: "inicio",             frame: "fr-inicio", h: 1500 },
  { nome: "02-visao-geral", hash: "dash/overview",     frame: "fr-dash",   h: 2400, bounce: true },
  { nome: "03-apostas",    hash: "dash/apostas",       frame: "fr-dash",   h: 1700 },
  { nome: "04-metricas",   hash: "dash/metrics",       frame: "fr-dash",   h: 2100 },
  { nome: "05-tipsters",   hash: "dash/tipsters",      frame: "fr-dash",   h: 1900 },
  { nome: "06-bookies",    hash: "dash/casas",         frame: "fr-dash",   h: 1800 },
  { nome: "07-esportes",   hash: "dash/sports",        frame: "fr-dash",   h: 1800 },
  { nome: "08-extracao",   hash: "plan",               frame: "fr-plan",   h: 1400 },
];

const LARGURA = 1600;
const espera = (ms) => new Promise((r) => setTimeout(r, ms));

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
    if (tela.bounce) {
      // (a) forca render limpo da pagina inicial do dash
      await page.evaluate(() => { location.hash = "dash/apostas"; });
      await espera(900);
    }
    await page.evaluate((h) => { location.hash = h; }, tela.hash);
    await espera(1600);

    await page.setViewport({ width: LARGURA, height: tela.h, deviceScaleFactor: 2 });
    // (c) Chart.js so recalcula no resize
    await page.evaluate((id) => {
      const fr = document.getElementById(id);
      if (fr && fr.contentWindow) fr.contentWindow.dispatchEvent(new Event("resize"));
    }, tela.frame);
    await espera(2200);

    await limpar(page);
    await espera(400);

    const destino = path.join(SAIDA, `${tela.nome}.png`);
    await page.screenshot({ path: destino });
    console.log("ok");
  }

  await browser.close();
  console.log(`\n${TELAS.length} telas em ${path.resolve(SAIDA)}`);
}

capturar().catch((e) => { console.error(e); process.exit(1); });
