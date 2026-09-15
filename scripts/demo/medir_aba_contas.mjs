/**
 * Mede a aba Contas (s365) renderizada DE VERDADE, contra o servidor_demo.
 *
 * Existe porque `node --check` e' falso verde para tudo que vive dentro de template
 * literal: uma crase perdida no markup que entrou no `buildHTML` derruba a pagina
 * inteira e passa no check (o caso da s296). Medir a tela e' o unico gate que pega.
 *
 * Confere, alem do print: zero erro de JS, a tabela pintou, o segmentado de Populacao
 * TROCA os numeros (se nao trocar, o filtro nao funciona), o tooltip da mediana existe
 * e o `stopPropagation` dele nao reordena a tabela, e transbordo horizontal zero.
 */
import fs from "node:fs";
import puppeteer from "puppeteer-core";
const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const PORTA = process.argv[2] || "8642";
const SAIDA = process.argv[3] || "capturas-contas";
const BASE = `http://127.0.0.1:${PORTA}`;
const espera = ms => new Promise(r => setTimeout(r, ms));

fs.mkdirSync(SAIDA, { recursive: true });
const erros = [];
const browser = await puppeteer.launch({ executablePath: CHROME, headless: "new",
  defaultViewport: { width: 1600, height: 1400, deviceScaleFactor: 1 } });
const page = await browser.newPage();
page.on("pageerror", e => { erros.push("pageerror: " + e.message); });
page.on("console", m => { if (m.type() === "error") erros.push("console: " + m.text()); });

await page.goto(`${BASE}/app#dash/contas`, { waitUntil: "networkidle2" });
await espera(4000);

const fr = page.frames().find(f => f.url().includes("/dashboard"));
if (!fr) { console.log("FALHOU: iframe do dashboard nao encontrado"); await browser.close(); process.exit(1); }

const leia = () => fr.evaluate(() => {
  const q = s => document.querySelector(s);
  const linhas = [...document.querySelectorAll("#tblContas tbody tr.cn-row")].map(tr =>
    [...tr.querySelectorAll("td")].map(td => td.innerText.trim().replace(/\s+/g, " ")));
  return {
    pagina: !!q("#page-contas.active"),
    titulo: q("#contasContent .card-title") ? q("#contasContent .card-title").innerText : null,
    kpis: [...document.querySelectorAll("#contasContent .kpi")].map(k =>
      (k.querySelector(".kpi-label")?.innerText || "") + " = " +
      (k.querySelector(".kpi-val")?.innerText || "") + " (" +
      (k.querySelector(".kpi-sub")?.innerText || "") + ")"),
    nLinhas: linhas.length,
    linhas: linhas.slice(0, 4),
    escopo: q(".cn-escopo") ? q(".cn-escopo").innerText : null,
    temRegua: !!q("#cnRegua"),
    temTip: !!q("#tblContas .metric-info"),
    temCusto: !!q("#tblContasCusto"),
    mult: [...document.querySelectorAll(".cn-mult")].map(m => m.innerText),
    segAtivo: q("#cnSeg button.active") ? q("#cnSeg button.active").innerText : null,
    overflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth,
  };
});

const pop = async k => { await fr.evaluate(kk => window.cnPop(kk), k); await espera(600); };

console.log("=".repeat(76));
const ambas = await leia();
console.log("POPULACAO: Ambas (padrao)");
console.log("  pagina ativa:", ambas.pagina, "| card:", ambas.titulo, "| regua:", ambas.temRegua,
            "| tooltip:", ambas.temTip, "| card custo:", ambas.temCusto);
console.log("  escopo:", ambas.escopo);
ambas.kpis.forEach(k => console.log("   ", k));
console.log("  linhas:", ambas.nLinhas);
ambas.linhas.forEach(l => console.log("   ", l.join(" | ")));
console.log("  multiplos:", ambas.mult.join("  "));
console.log("  overflow-x:", ambas.overflowX);
await page.screenshot({ path: `${SAIDA}/contas-ambas.png`, fullPage: true });

await pop("inativas");
const ina = await leia();
console.log("-".repeat(76));
console.log("POPULACAO: Inativas  (segmentado =", ina.segAtivo + ")");
console.log("  escopo:", ina.escopo);
ina.kpis.forEach(k => console.log("   ", k));
ina.linhas.forEach(l => console.log("   ", l.join(" | ")));
await page.screenshot({ path: `${SAIDA}/contas-inativas.png`, fullPage: true });

await pop("ativas");
const ati = await leia();
console.log("-".repeat(76));
console.log("POPULACAO: Ativas  (segmentado =", ati.segAtivo + ")");
console.log("  escopo:", ati.escopo);
ati.kpis.forEach(k => console.log("   ", k));
ati.linhas.forEach(l => console.log("   ", l.join(" | ")));
await page.screenshot({ path: `${SAIDA}/contas-ativas.png`, fullPage: true });

// Drill: abre a 1a casa e confere que a sub-tabela aparece
await pop("ambas");
const casa1 = await fr.evaluate(() => {
  const tr = document.querySelector("#tblContas tbody tr.cn-row");
  const nome = tr ? tr.querySelector("td").innerText.trim() : "";
  if (tr) tr.click();
  return nome;
});
await espera(600);
const drill = await fr.evaluate(() => {
  const d = document.querySelector(".cn-drill-box");
  return { aberto: !!d, nContas: d ? d.querySelectorAll(":scope > table > tbody > tr").length : 0,
           cabecalho: d ? [...d.querySelectorAll("th")].map(t => t.innerText.trim()).join(" | ") : "" };
});
console.log("-".repeat(76));
console.log("DRILL na 1a casa:", casa1, "| aberto:", drill.aberto, "| contas:", drill.nContas);
console.log("  colunas:", drill.cabecalho);
await page.screenshot({ path: `${SAIDA}/contas-drill.png`, fullPage: true });

// O "i" da mediana nao pode reordenar a tabela (stopPropagation)
const antes = await fr.evaluate(() => document.querySelector("#tblContas tbody tr.cn-row td").innerText.trim());
await fr.evaluate(() => { const b = document.querySelector("#tblContas .metric-info"); if (b) b.click(); });
await espera(400);
const depois = await fr.evaluate(() => document.querySelector("#tblContas tbody tr.cn-row td").innerText.trim());
console.log("-".repeat(76));
console.log("Clique no 'i' da mediana: 1a linha antes =", antes, "| depois =", depois,
            "|", antes === depois ? "OK (nao reordenou)" : "FALHOU (reordenou)");


// Drill: confere que lista TODAS as contas da casa (a contagem do cabecalho) e que
// ordenar a sub-tabela nao fecha o painel.
const drillFull = await fr.evaluate(() => {
  const tr = [...document.querySelectorAll("#tblContas tbody tr.cn-row")][1];
  const cab = tr ? [...tr.querySelectorAll("td")].map(td => td.innerText.trim()) : [];
  if (tr) tr.click();
  return { casa: cab[0] || "", contasNoCabecalho: cab[1] || "", ativasNoCabecalho: cab[2] || "" };
});
await espera(700);
const drill2 = await fr.evaluate(() => {
  const d = document.querySelector(".cn-drill-box");
  if (!d) return { aberto: false };
  const linhas = [...d.querySelectorAll(":scope > table > tbody > tr")];
  return {
    aberto: true,
    nLinhas: linhas.length,
    ativas: linhas.filter(tr => tr.innerText.includes("ativa") && !tr.innerText.includes("encerrada")).length,
    colunas: [...d.querySelectorAll("th")].map(t => t.innerText.trim()).join(" | "),
    rodape: d.querySelector(".cn-drill-foot") ? d.querySelector(".cn-drill-foot").innerText.replace(/\s+/g, " ") : "",
  };
});
console.log("-".repeat(76));
console.log("DRILL completo em", drillFull.casa, "| cabecalho diz", drillFull.contasNoCabecalho,
            "contas /", drillFull.ativasNoCabecalho, "ativas");
console.log("  linhas na sub-tabela:", drill2.nLinhas, "| com estado ATIVA:", drill2.ativas);
console.log("  colunas:", drill2.colunas);
console.log("  rodape:", drill2.rodape);
// ordenar a sub-tabela NAO pode fechar o drill
await fr.evaluate(() => { const th = [...document.querySelectorAll(".cn-drill-box th")].find(t => t.innerText.includes("Custo")); if (th) th.click(); });
await espera(600);
const aposSort = await fr.evaluate(() => !!document.querySelector(".cn-drill-box"));
console.log("  apos ordenar por Custo, o drill continua aberto:", aposSort);


// ── Transbordo por largura ──────────────────────────────────────────────────
// A sub-tabela do drill tem 13 colunas e vive dentro de um `<td>`: sem `max-width:0`
// na celula ela ALARGA a tabela externa e a PAGINA inteira transborda (medido: +332px
// em 1366). O modo de falha e invisivel no codigo e obvio na regua.
console.log("-".repeat(76));
console.log("TRANSBORDO por largura (pagina tem de ser +0 em todas)");
for (const w of [1366, 1440, 1600, 1920, 2560]) {
  const pg = await browser.newPage();
  await pg.setViewport({ width: w, height: 1100 });
  await pg.goto(`${BASE}/app#dash/contas`, { waitUntil: "networkidle2" });
  await espera(4000);
  const f2 = pg.frames().find(f => f.url().includes("/dashboard"));
  const a = await f2.evaluate(() => document.getElementById("tblContas")
    ? document.documentElement.scrollWidth - document.documentElement.clientWidth : -1);
  await f2.evaluate(() => { const tr = document.querySelector("#tblContas tbody tr.cn-row"); if (tr) tr.click(); });
  await espera(600);
  const b = await f2.evaluate(() => {
    const de = document.documentElement, box = document.querySelector(".cn-drill-box");
    return { pagina: de.scrollWidth - de.clientWidth, rola: box ? box.scrollWidth - box.clientWidth : -1 };
  });
  console.log(`  ${String(w).padStart(4)}px  fechado +${a}  |  drill aberto +${b.pagina} (a sub-tabela rola ${b.rola})  ${a === 0 && b.pagina === 0 ? "OK" : "TRANSBORDA"}`);
  await pg.close();
}

console.log("=".repeat(76));
if (erros.length) { console.log("ERROS DE JS:"); erros.forEach(e => console.log("  " + e)); }
else console.log("ZERO erro de JS.");
console.log("prints em", SAIDA);
await browser.close();
