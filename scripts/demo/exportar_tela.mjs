/**
 * Exporta uma tela do Sharpen como UM arquivo .html autocontido, para mandar a
 * terceiros (designer, apresentação) sem servidor e sem acesso ao repo.
 *
 *   1) python scripts/demo/servidor_demo.py 8644
 *   2) node scripts/demo/exportar_tela.mjs dash/contas "saida.html" [porta]
 *
 * O que ele resolve, e nenhuma das quatro coisas é opcional para o arquivo abrir
 * sozinho no Finder/Explorer de outra pessoa:
 *
 *   · ACHATA O IFRAME. A tela vive dentro do `#fr-dash` da casca (`/app`), e um iframe
 *     com `src` relativo aponta para um servidor que o designer não tem. O conteúdo do
 *     iframe entra no lugar dele como uma `<div>`, herdando a mesma caixa.
 *   · INLINE DO CSS. São 5 folhas (`tokens`, `shell`, `layout`, `components`,
 *     `tipster-metodo`), e o `?v=` de cada uma muda a cada sessão.
 *   · IMAGEM VIRA `data:`. Os favicons das casas são `<img src>` relativo — sem isto a
 *     coluna Casa abre com 29 ícones quebrados, que é a primeira coisa que o designer vê.
 *   · FONTE VEM DO GOOGLE. O app self-hospeda Manrope e JetBrains Mono em `/static/fonts`;
 *     embutir os `woff2` em base64 levaria o arquivo a alguns MB. O `<link>` do Google
 *     entrega as MESMAS famílias e mantém o arquivo leve.
 *
 * O JS é REMOVIDO de propósito: o alvo é um retrato para redesenho, e script sem backend
 * só produziria erro de console e tela meio pintada. O que sai é o DOM já renderizado.
 */
import fs from "node:fs";
import path from "node:path";
import puppeteer from "puppeteer-core";

const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const ALVO = process.argv[2] || "dash/contas";
const SAIDA = process.argv[3] || "tela.html";
const PORTA = process.argv[4] || "8644";
const BASE = `http://127.0.0.1:${PORTA}`;
const espera = ms => new Promise(r => setTimeout(r, ms));

const browser = await puppeteer.launch({
  executablePath: CHROME, headless: "new",
  defaultViewport: { width: 1680, height: 1200, deviceScaleFactor: 1 },
});
const page = await browser.newPage();
await page.goto(`${BASE}/app#${ALVO}`, { waitUntil: "networkidle2" });
await espera(5000);

// Abre o drill da 2ª casa: o designer precisa ver o estado expandido, que é onde mora
// metade das decisões de layout desta tela.
const fr = page.frames().find(f => f.url().includes("/dashboard"));
if (fr) {
  await fr.evaluate(() => {
    const linhas = [...document.querySelectorAll("#tblContas tbody tr.cn-row")];
    if (linhas[1]) linhas[1].click();
  }).catch(() => {});
  await espera(900);
}

// ── coleta o CSS de todas as folhas, resolvido pelo próprio navegador ─────────
const coletaCSS = async (alvo) => alvo.evaluate(async () => {
  const links = [...document.querySelectorAll('link[rel="stylesheet"]')]
    .map(l => l.href).filter(h => !h.includes("fonts.googleapis"));
  const partes = [];
  for (const h of links) {
    try { partes.push("/* " + h.split("/").pop() + " */\n" + await (await fetch(h)).text()); }
    catch (e) { partes.push("/* falhou: " + h + " */"); }
  }
  for (const s of document.querySelectorAll("style")) partes.push(s.textContent);
  return partes.join("\n\n");
});

// ── imagens viram data: URI, e o download acontece NO NODE ───────────────────
// ⚠️ Não dá para converter de dentro da página, e a causa não é óbvia: os favicons das
// casas vêm do Google (`google.com/s2/favicons?domain=…`), que responde SEM
// `Access-Control-Allow-Origin`. Um `<img>` os exibe (imagem não passa por CORS), mas
// `fetch` e `canvas` não conseguem LER os bytes — o canvas ainda fica "tainted". Medido:
// 377 de 383 imagens saíam sem `src`, e o arquivo abria com a coluna Casa toda quebrada.
// Do Node não há origem, logo não há CORS.
const coletaSrcs = async (alvo) => alvo.evaluate(() =>
  [...new Set([...document.querySelectorAll("img")]
    .map(i => i.src).filter(s => s && !s.startsWith("data:")))]);

const baixar = async (url) => {
  try {
    const r = await fetch(url);
    if (!r.ok) return null;
    const buf = Buffer.from(await r.arrayBuffer());
    if (buf.length > 400000) return null;
    const tipo = r.headers.get("content-type") || "image/png";
    return `data:${tipo.split(";")[0]};base64,${buf.toString("base64")}`;
  } catch (e) { return null; }
};

const aplicaMapa = async (alvo, mapa) => alvo.evaluate((m) => {
  let trocadas = 0, perdidas = 0;
  for (const img of document.querySelectorAll("img")) {
    if (img.src.startsWith("data:")) continue;
    if (m[img.src]) { img.setAttribute("src", m[img.src]); trocadas++; }
    else { img.removeAttribute("src"); perdidas++; }
  }
  return { trocadas, perdidas };
}, mapa);

const cssCasca = await coletaCSS(page.mainFrame());
const cssDash = fr ? await coletaCSS(fr) : "";

const srcs = [...new Set([
  ...await coletaSrcs(page.mainFrame()),
  ...(fr ? await coletaSrcs(fr) : []),
])];
const mapa = {};
// Em lotes: são dezenas de favicons e o Google responde devagar um a um.
for (let i = 0; i < srcs.length; i += 8) {
  const lote = srcs.slice(i, i + 8);
  const rs = await Promise.all(lote.map(baixar));
  lote.forEach((u, k) => { if (rs[k]) mapa[u] = rs[k]; });
}
const a = await aplicaMapa(page.mainFrame(), mapa);
const b = fr ? await aplicaMapa(fr, mapa) : { trocadas: 0, perdidas: 0 };
const nImgs = a.trocadas + b.trocadas;
const nPerdidas = a.perdidas + b.perdidas;

const htmlDash = fr ? await fr.evaluate(() => document.body.innerHTML) : "";

// ── achata: o conteúdo do iframe entra no lugar do próprio iframe ────────────
const htmlFinal = await page.evaluate((corpoDash) => {
  const fr = document.getElementById("fr-dash");
  if (fr) {
    const div = document.createElement("div");
    div.id = "fr-dash";
    div.className = fr.className;
    div.setAttribute("style", (fr.getAttribute("style") || "") + ";border:0;overflow:auto;");
    div.innerHTML = corpoDash;
    fr.replaceWith(div);
  }
  // Os outros iframes (Início, Planilhador) não fazem parte do retrato.
  document.querySelectorAll("iframe").forEach(i => i.remove());
  document.querySelectorAll("script").forEach(s => s.remove());
  document.querySelectorAll('link[rel="stylesheet"]').forEach(l => l.remove());
  return document.documentElement.outerHTML;
}, htmlDash);

const fontes = '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
  + '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
  + '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
  + 'family=Manrope:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap">';

const cabecalho = `<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sharpen — ${ALVO}</title>
${fontes}
<style>
/* ── CSS da casca (/app) ─────────────────────────────────────────────── */
${cssCasca}
/* ── CSS do dashboard ────────────────────────────────────────────────── */
${cssDash}
/* ── ajustes SÓ do export: o iframe virou div e não tem mais viewport próprio ── */
#fr-dash { display: block !important; width: 100%; height: auto; }
#fr-dash .main { min-height: 0; }
html.embedded .sidebar { display: none; }
</style>`;

const out = htmlFinal
  .replace(/<head>/i, "<head>\n" + cabecalho)
  .replace(/<\/head>/i, "</head>");

fs.mkdirSync(path.dirname(path.resolve(SAIDA)), { recursive: true });
fs.writeFileSync(SAIDA, "<!doctype html>\n" + out, "utf8");
const kb = Math.round(fs.statSync(SAIDA).size / 1024);
console.log(`ok: ${SAIDA} (${kb} KB) - ${nImgs} imagens embutidas` + (nPerdidas ? `, ${nPerdidas} NAO baixadas` : ", nenhuma perdida") + `, CSS inline, sem script`);
await browser.close();
