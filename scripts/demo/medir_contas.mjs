/**
 * Mede o Painel de Contas em VARIAS larguras, contra o `servidor_demo.py`.
 *
 *   1) python scripts/demo/servidor_demo.py 8641
 *   2) node scripts/demo/medir_contas.mjs [porta] [pasta de saida]
 *
 * Por que existe (s333, Fase 7): a tela distribui as colunas por DEGRAU de largura,
 * e o modo de falha e' invisivel na leitura -- encostando num corte antes de a conta
 * do conteudo fechar, a tabela transborda para dentro do `overflow:hidden` do painel
 * e some do `scrollWidth`. Nenhum lint acusa; so medir acusa.
 *
 * A largura que MANDA e' a da AREA DO APP, nao a da janela: esta pagina vive dentro
 * do `#fr-plan` da casca e a sidebar (~300px) fica fora do iframe. Por isso o script
 * imprime as duas, e por isso os breakpoints sao `@container`, nunca `@media`.
 *
 * O que ele confere em cada largura, alem do print: a grade das quatro superficies
 * (cabecalho, linha da casa, linha da conta e rodape de total) e' a MESMA; as duas
 * colunas opcionais abrem/colapsam juntas com o inline do fornecedor; nenhuma tag na
 * linha da casa; nenhuma abreviacao; e transbordo horizontal zero.
 */
import fs from "node:fs";
import puppeteer from "puppeteer-core";
const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const PORTA = process.argv[2] || "8641";
const SAIDA = process.argv[3] || "capturas-s333";
const BASE = `http://127.0.0.1:${PORTA}`;
const espera = ms => new Promise(r => setTimeout(r, ms));
// Larguras de JANELA. A sidebar da casca (~300px) fica FORA do iframe, entao a
// area do app -- que e' o que o `@container pc` mede -- e' ~300px menor.
const LARGURAS = [1366, 1440, 1600, 1920, 2560];

fs.mkdirSync(SAIDA, { recursive: true });
const browser = await puppeteer.launch({ executablePath: CHROME, headless: "new",
  defaultViewport: { width: 1600, height: 1200, deviceScaleFactor: 1 } });
const page = await browser.newPage();
page.on("pageerror", e => console.log("  ERRO JS:", e.message));
await page.goto(`${BASE}/app#plan/contas`, { waitUntil: "networkidle2" });
await espera(3500);

for (const w of LARGURAS) {
  await page.setViewport({ width: w, height: 1400, deviceScaleFactor: 1 });
  await page.evaluate(() => window.dispatchEvent(new Event("resize")));
  await espera(1800);
  const fr = await (await page.$("#fr-plan")).contentFrame();
  const r = await fr.evaluate(() => {
    const $ = s => document.querySelector(s);
    const $$ = s => [...document.querySelectorAll(s)];
    const painel = $("#painelContas");
    const cs = el => el ? getComputedStyle(el) : null;
    const linha = $(".conta-row");
    const cabec = $(".acct-head");
    const casa  = $(".contas-casa-head");
    const foot  = $(".acct-foot");
    const tags  = $$(".tag-status");
    const cnt = {};
    tags.forEach(t => { const c = [...t.classList].find(x => x !== "tag-status"); cnt[c] = (cnt[c]||0)+1; });
    // transbordo horizontal: a pagina nao pode rolar de lado
    const doc = document.documentElement;
    return {
      appW: painel ? Math.round(painel.getBoundingClientRect().width) : 0,
      grid: linha ? cs(linha).gridTemplateColumns : null,
      gridHead: cabec ? cs(cabec).gridTemplateColumns : null,
      gridCasa: casa ? cs(casa).gridTemplateColumns : null,
      gridFoot: foot ? cs(foot).gridTemplateColumns : null,
      triCols: cs($(".pc-tri")) ? cs($(".pc-tri")).gridTemplateColumns : null,
      topCols: cs($(".pc-top")) ? cs($(".pc-top")).gridTemplateColumns : null,
      kpis: $$(".painel-kpi").length,
      kpiCols: cs($(".pc-kpis")) ? cs($(".pc-kpis")).gridTemplateColumns : null,
      supRows: $$(".sup-row").length,
      supFoot: ($(".sup-foot .v")||{}).textContent || "",
      segForn: $$("#painelSegForn button").length,
      chipsTotal: $$(".acct-total").length,
      tagsNaCasa: $$(".contas-casa-head .tag-status").length,
      arvore: $$(".conta-tree, .acct-tree, .conta-guia").length,
      tags: cnt,
      fornInlineVis: $$(".acct-supplier-inline").filter(e => cs(e).display !== "none").length,
      fornColVis: $$(".conta-row .acct-col-fornecedor").filter(e => cs(e).width !== "0px").length,
      ultimaVis: $$(".conta-row .acct-col-ultima").filter(e => cs(e).width !== "0px").length,
      acoesOp: linha ? cs($(".conta-row .conta-acoes")).opacity : null,
      footTxt: foot ? foot.textContent.trim() : null,
      kpiTerc: ($(".painel-kpi.terc .painel-kpi-val")||{}).textContent || "",
      overflow: doc.scrollWidth - doc.clientWidth,
      abrev: /\b(pend|conc|calc|div)\.|\+99/.test(document.body.innerText),
    };
  });
  console.log(`\n── janela ${w} · área do app ${r.appW}px ─────────────────`);
  console.log(JSON.stringify(r, null, 1));
  await page.screenshot({ path: `${SAIDA}/contas-${w}.png`, fullPage: false });
}
await browser.close();
