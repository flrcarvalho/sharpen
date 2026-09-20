/**
 * Reconhecimento do /realtrial para as pecas de marketing. SO LEITURA: abre a
 * demonstracao publica, navega pelas telas e fotografa. Nao clica em nada que escreva.
 *
 *   node scripts/demo/recon_realtrial.mjs <pasta-de-saida>
 *
 * POR QUE O COOKIE E' SALVO: a rota tem teto de 3 sessoes por IP por dia
 * (`auth.TRIAL_SESSOES_POR_IP`) e a sessao dura 7 dias (`TRIAL_DIAS`). Rodar de novo
 * reusa o cookie e NAO queima outra sessao. Apagar o json e' que custa uma.
 *
 * AS TRES ARMADILHAS DO HEADLESS, todas ja pagas aqui:
 *  · a casca e' feita de iframes, entao ler `page` direto nao acha a tela;
 *  · o dash so redesenha grafico no RESIZE — dai o "bounce" de 1px de largura;
 *  · esperar o relogio nao basta, mas sem o bounce a tela sai VAZIA de verdade.
 *
 * ⚠️ NAO abra `#dash/custos_v2` por link direto esperando ver a tela: ela so pinta
 * quando se chega clicando no menu (BACKLOG §4.6). Nao e' defeito deste script.
 *
 * Este script NAO asserta nada: ele fotografa. Tela errada vira print bonito da tela
 * errada, e quem confere e' o olho.
 */
import fs from "node:fs";
import path from "node:path";
import puppeteer from "puppeteer-core";

const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const BASE = "https://www.sharpen.bet";
const DEST = process.argv[2];
const COOKIES = path.join(DEST, "realtrial-cookies.json");

const LARGURA = 1920, ALTURA = 1200, DPR = 1;
const espera = (ms) => new Promise((r) => setTimeout(r, ms));

const TELAS = [
  ["contas", "plan/contas"],
  ["custos", "dash/custos_v2"],
  ["tipsters", "dash/tipsters"],
  ["overview", "dash/overview"],
  ["extracao", "plan"],
];

const browser = await puppeteer.launch({
  executablePath: CHROME,
  headless: "new",
  defaultViewport: { width: LARGURA, height: ALTURA, deviceScaleFactor: DPR },
  args: ["--no-sandbox", "--hide-scrollbars", "--force-color-profile=srgb",
         "--font-render-hinting=none"],
});
const page = await browser.newPage();

let temSessao = false;
if (fs.existsSync(COOKIES)) {
  await browser.setCookie(...JSON.parse(fs.readFileSync(COOKIES, "utf8")));
  await page.goto(`${BASE}/app`, { waitUntil: "networkidle2", timeout: 60000 });
  temSessao = !page.url().includes("/login");
  console.log(temSessao ? "sessao reusada do cookie" : "cookie vencido");
}
if (!temSessao) {
  console.log("abrindo /realtrial (consome 1 das 3 do dia)…");
  await page.goto(`${BASE}/realtrial`, { waitUntil: "networkidle2", timeout: 90000 });
  console.log("  -> " + page.url());
  fs.writeFileSync(COOKIES, JSON.stringify(await browser.cookies(), null, 1));
}

for (const [nome, hash] of TELAS) {
  await page.goto(`${BASE}/app#${hash}`, { waitUntil: "networkidle2", timeout: 90000 });
  // A casca e' de iframes e o dash so pinta grafico no resize (as tres
  // armadilhas do headless). Sem o "bounce" a tela sai vazia.
  await espera(3500);
  await page.setViewport({ width: LARGURA - 1, height: ALTURA, deviceScaleFactor: DPR });
  await espera(600);
  await page.setViewport({ width: LARGURA, height: ALTURA, deviceScaleFactor: DPR });
  await espera(4500);
  const arq = path.join(DEST, `realtrial-${nome}.png`);
  await page.screenshot({ path: arq });
  console.log(`  ${nome.padEnd(10)} -> ${Math.round(fs.statSync(arq).size / 1024)} KB`);
}

await browser.close();
console.log("fim");
