/**
 * Mede a aba Contas v4 (s372) renderizada DE VERDADE, contra o servidor_demo.
 *
 *   1) python scripts/demo/servidor_demo.py 8646
 *   2) node scripts/demo/medir_aba_contas.mjs [porta] [pasta de saida]
 *
 * Existe porque `node --check` e' falso verde para tudo que vive dentro de template
 * literal: uma crase perdida no markup derruba a pagina inteira e passa no check (o caso
 * da s296). Medir a tela e' o unico gate que pega.
 *
 * O que ele confere, alem do print:
 *   · zero erro de JS e transbordo horizontal zero em cinco larguras;
 *   · os TRES paineis pintaram, com histograma de 5 faixas e barra de cobertura;
 *   · o segmentado de Populacao TROCA os numeros (default = Ambas, desde 21/09);
 *   · a ficha abre o drill, o drill lista TODAS as contas da casa, e ordenar a
 *     sub-tabela NAO fecha o painel;
 *   · a barra de duracao respeita a regua fixa de 30 dias (mediana <= media <= 100%);
 *   · o "Limpar tudo" volta a Populacao ao default (era o que a s371 registrou no
 *     LIMPAR_EXTRA e que a reescrita da v4 quase levou junto);
 *   · o bloco Geral recolhe, a REGUA DE ESCOPO continua visivel recolhida, e a
 *     preferencia sobrevive ao recarregar (s373);
 *   · o 4o painel ("Ultimas contas") pinta so DENTRO da casa, com os quatro na mesma
 *     linha de figura e sem orfao numa segunda fileira (s373).
 */
import fs from "node:fs";
import puppeteer from "puppeteer-core";
const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const PORTA = process.argv[2] || "8646";
const SAIDA = process.argv[3] || "capturas-contas";
const BASE = `http://127.0.0.1:${PORTA}`;
const espera = ms => new Promise(r => setTimeout(r, ms));

fs.mkdirSync(SAIDA, { recursive: true });
const erros = [];
const browser = await puppeteer.launch({ executablePath: CHROME, headless: "new",
  defaultViewport: { width: 1680, height: 1400, deviceScaleFactor: 1 } });
const page = await browser.newPage();
page.on("pageerror", e => { erros.push("pageerror: " + e.message); });
page.on("console", m => { if (m.type() === "error") erros.push("console: " + m.text()); });

await page.goto(`${BASE}/app#dash/contas`, { waitUntil: "networkidle2" });
await espera(5000);

const fr = page.frames().find(f => f.url().includes("/dashboard"));
if (!fr) { console.log("FALHOU: iframe do dashboard nao encontrado"); await browser.close(); process.exit(1); }

const leia = () => fr.evaluate(() => {
  const q = s => document.querySelector(s);
  const txt = s => (q(s) ? q(s).innerText.replace(/\s+/g, " ").trim() : null);
  // Os paineis passaram a viver dentro do bloco Geral (s373); o seletor antigo
  // (`#contasContent > .cn-q3`) devolvia ZERO calado, que e um verde falso disfarcado
  // de "nao ha painel".
  const paineis = [...document.querySelectorAll("#cnGeralCorpo > .cn-q3 > .cn-qp")].map(p => ({
    eyebrow: p.querySelector(".t") ? p.querySelector(".t").innerText.trim() : "",
    figura: [...p.querySelectorAll(".cn-fig")].map(f => f.querySelector(".lb").innerText.trim() + " " + f.querySelector(".v").innerText.trim()).join("  |  "),
  }));
  return {
    regua: !!q("#cnRegua"),
    escopo: txt(".cn-regua__esc"),
    paineis,
    nFaixas: document.querySelectorAll(".cn-drow").length,
    temCobertura: !!q(".cn-covbar"),
    nCobertura: document.querySelectorAll(".cn-covbar i").length,
    nRanking: document.querySelectorAll(".cn-mrow").length,
    nFichas: document.querySelectorAll(".cn-ficha").length,
    nDefs: document.querySelectorAll(".cn-def").length,
    segAtivo: q("#cnSeg button.active") ? q("#cnSeg button.active").innerText.trim() : null,
    temLimpar: !!q("#contasFiltros [onclick*='limparFiltrosPagina']"),
    primeiraFicha: q(".cn-ficha") ? q(".cn-ficha").innerText.replace(/\s+/g, " ").trim().slice(0, 120) : null,
    // Estado VAZIO: recorte sem linha tem de EXPLICAR e oferecer a saída, nunca ficar em
    // branco. Com o default em `ambas` ele nao aparece mais no boot do demo, entao o
    // caminho para exercita-lo e trocar para `inativas` (o bloco POPULACAO abaixo faz).
    vazio: q(".cn-empty") ? q(".cn-empty").innerText.replace(/\s+/g, " ").trim().slice(0, 150) : null,
    vazioAcoes: document.querySelectorAll(".cn-empty__btn").length,
    overflowX: document.documentElement.scrollWidth - document.documentElement.clientWidth,
  };
});

const pop = async k => { await fr.evaluate(kk => window.cnPop(kk), k); await espera(700); };

console.log("=".repeat(78));
const ini = await leia();
console.log("ESTRUTURA v4");
console.log("  regua:", ini.regua, "| escopo:", ini.escopo);
console.log("  paineis:", ini.paineis.length, ini.paineis.length === 3 ? "" : "<- ESPERADO 3");
ini.paineis.forEach(p => console.log(`     ${p.eyebrow.padEnd(24)} -> ${p.figura}`));
console.log("  histograma:", ini.nFaixas, "faixas | cobertura:", ini.temCobertura,
            "(" + ini.nCobertura + " segmentos) | ranking:", ini.nRanking, "casas");
console.log("  fichas:", ini.nFichas, "| definicoes:", ini.nDefs, "| Limpar tudo:", ini.temLimpar);
console.log("  segmentado no boot:", ini.segAtivo, "(esperado: Ambas)");
console.log("  1a ficha:", ini.primeiraFicha);
console.log("  estado vazio:", ini.vazio, "| atalhos:", ini.vazioAcoes);
await page.screenshot({ path: `${SAIDA}/v4-boot.png`, fullPage: true });

for (const k of ["ativas", "inativas"]) {
  await pop(k);
  const r = await leia();
  console.log("-".repeat(78));
  console.log(`POPULACAO ${k} (seg = ${r.segAtivo})`);
  console.log("  escopo:", r.escopo);
  r.paineis.forEach(p => console.log(`     ${p.eyebrow.padEnd(24)} -> ${p.figura}`));
  await page.screenshot({ path: `${SAIDA}/v4-${k}.png`, fullPage: true });
}

// A barra e o drill precisam de uma populacao COM contas. No dado do demo todas as
// contas sao ativas, entao `inativas` (a ultima do laco acima) fica vazia.
await pop("ambas");
const barras = await fr.evaluate(() => [...document.querySelectorAll(".cn-ficha")].slice(0, 8).map(f => {
  const med = f.querySelector(".cn-track .med"), avg = f.querySelector(".cn-track .avg");
  const nome = f.querySelector(".cn-fname") ? f.querySelector(".cn-fname").innerText.split("\n")[0].trim() : "";
  return { nome, med: med ? parseFloat(med.style.width) : -1, avg: avg ? parseFloat(avg.style.left) : -1 };
}));
console.log("-".repeat(78));
console.log("BARRA DE DURACAO (regua fixa 0-30 d; mediana <= media, teto 100%)");
let ruimBarra = 0;
barras.forEach(b => {
  const ok = b.med <= 100 && b.avg <= 100 && b.med <= b.avg + 0.05;
  if (!ok) ruimBarra++;
  console.log(`   ${b.nome.padEnd(22)} med ${String(b.med).padStart(6)}%  avg ${String(b.avg).padStart(6)}%  ${ok ? "ok" : "FORA DA REGUA"}`);
});

// Drill
const drill = await fr.evaluate(async () => {
  const f = [...document.querySelectorAll(".cn-ficha")][0];
  if (!f) return { casa: "(sem ficha nesta populacao)", sub: "", aberto: false, nLinhas: 0, colunas: "", rodape: "" };
  const nome = f.querySelector(".cn-fname").innerText.split("\n")[0].trim();
  const sub = f.querySelector(".cn-fname .sub").innerText.trim();
  f.click();
  await new Promise(r => setTimeout(r, 500));
  const d = document.querySelector(".cn-drill");
  return {
    casa: nome, sub,
    aberto: !!d,
    nLinhas: d ? d.querySelectorAll(":scope > table > tbody > tr").length : 0,
    colunas: d ? [...d.querySelectorAll("th")].map(t => t.innerText.trim()).join(" | ") : "",
    rodape: d ? d.querySelector(".cn-drillfoot").innerText.replace(/\s+/g, " ").trim() : "",
  };
});
console.log("-".repeat(78));
console.log("DRILL em", drill.casa, "|", drill.sub);
console.log("  aberto:", drill.aberto, "| linhas:", drill.nLinhas);
console.log("  colunas:", drill.colunas);
console.log("  rodape:", drill.rodape);

// O 4o painel (Ultimas contas) so existe DENTRO da casa. Duas coisas que so a tela diz:
// que os QUATRO ficam na mesma linha de figura (o titulo do 3o quebra em duas linhas
// quando a coluna aperta, e so ele) e que o 4o nao deixa orfao numa segunda fileira.
const p4 = await fr.evaluate(() => {
  const ps = [...document.querySelectorAll(".cn-drill .cn-q3 > .cn-qp")];
  if (ps.length < 4) return { n: ps.length };
  const linhas = [...new Set(ps.map(p => Math.round(p.getBoundingClientRect().top)))];
  const yFig = ps.map(p => Math.round(p.querySelector(".cn-fig .v").getBoundingClientRect().top));
  const q = ps[3];
  return {
    n: ps.length,
    titulo: q.querySelector(".t").innerText.trim(),
    ctx: q.querySelector(".s").innerText.trim(),
    nLista: q.querySelectorAll(".cn-urow").length,
    nComp: q.querySelectorAll(".cn-crow--cmp").length,
    grade: linhas.map(y => ps.filter(p => Math.round(p.getBoundingClientRect().top) === y).length).join("+"),
    figAlinhada: [...new Set(yFig)].length === linhas.length,
    foot: q.querySelector(".cn-foot").innerText.replace(/\s+/g, " ").trim().slice(0, 110),
  };
});
console.log("-".repeat(78));
console.log("4o PAINEL (so na casa):", p4.n, "paineis | grade", p4.grade,
            "| figuras alinhadas por linha:", p4.figAlinhada);
if (p4.n >= 4) {
  console.log(`  "${p4.titulo}" · ${p4.ctx} | ${p4.nComp} linhas de comparativo | lista com ${p4.nLista}`);
  console.log("  rodape:", p4.foot);
}
const p4Ok = p4.n === 4 && p4.figAlinhada && p4.nLista > 0 && p4.nComp >= 3;
console.log("  " + (p4Ok ? "ok" : "FALHOU: o 4o painel nao pintou, desalinhou ou veio sem lista"));

const aposSort = await fr.evaluate(async () => {
  const th = [...document.querySelectorAll(".cn-drill th")].find(t => t.innerText.includes("Custo"));
  if (th) th.click();
  await new Promise(r => setTimeout(r, 500));
  return !!document.querySelector(".cn-drill");
});
console.log("  ordenar a sub-tabela mantem o drill aberto:", aposSort);
await page.screenshot({ path: `${SAIDA}/v4-drill.png`, fullPage: true });

// Limpar tudo volta a Populacao ao default
const limpou = await fr.evaluate(async () => {
  window.cnPop("inativas");
  await new Promise(r => setTimeout(r, 300));
  const antes = document.querySelector("#cnSeg button.active").innerText.trim();
  const b = document.querySelector("#contasFiltros [onclick*='limparFiltrosPagina']");
  if (b) b.click();
  await new Promise(r => setTimeout(r, 700));
  return { antes, depois: document.querySelector("#cnSeg button.active").innerText.trim() };
});
console.log("-".repeat(78));
console.log("LIMPAR TUDO: Populacao", limpou.antes, "->", limpou.depois,
            limpou.depois === "Ambas" ? "ok" : "FALHOU (nao voltou ao default)");

// O "Limpar tudo" acima devolveu a Populacao ao default. Garante `ambas` de todo jeito:
// num dono cujo default caia numa populacao vazia nao ha bloco Geral para medir.
await pop("ambas");

// Bloco Geral: recolher. O gate de forma (test_a_regua_de_escopo_fica_FORA...) le a
// ORDEM do markup; so a tela diz se a regua fica mesmo VISIVEL com o bloco fechado, se
// o corpo some de verdade e quanto a tabela de baixo sobe, que e o motivo do pedido.
const vis = sel => fr.evaluate(s => {
  const el = document.querySelector(s);
  return !!(el && el.offsetParent !== null && el.getBoundingClientRect().height > 0);
}, sel);
const yPorCasa = () => fr.evaluate(() => {
  const s = document.querySelector(".cn-secao");
  return s ? Math.round(s.getBoundingClientRect().top) : -1;
});
console.log("-".repeat(78));
console.log("BLOCO GERAL (recolher)");
const gAberto = { corpo: await vis("#cnGeralCorpo"), regua: await vis("#cnRegua"), y: await yPorCasa() };
await fr.evaluate(() => window.cnGeralToggle());
await espera(600);
const gFechado = { corpo: await vis("#cnGeralCorpo"), regua: await vis("#cnRegua"), y: await yPorCasa() };
const acao = await fr.evaluate(() => {
  const a = document.querySelector(".cn-geral__acao");
  const t = document.querySelector(".cn-geral__top");
  return { rotulo: a ? getComputedStyle(a, "::after").content : null,
           aria: t ? t.getAttribute("aria-expanded") : null };
});
console.log(`  aberto  -> corpo ${gAberto.corpo} · regua ${gAberto.regua} · "Por casa" em y=${gAberto.y}`);
console.log(`  fechado -> corpo ${gFechado.corpo} · regua ${gFechado.regua} · "Por casa" em y=${gFechado.y}`);
console.log(`  a tabela subiu ${gAberto.y - gFechado.y}px · rotulo ${acao.rotulo} · aria-expanded ${acao.aria}`);
const geralOk = gAberto.corpo && !gFechado.corpo && gAberto.regua && gFechado.regua
  && acao.aria === "false" && (gAberto.y - gFechado.y) > 200;
console.log("  " + (geralOk ? "ok" : "FALHOU: recolher nao escondeu o corpo, escondeu a regua junto, ou nao subiu a tabela"));
await page.screenshot({ path: `${SAIDA}/v4-geral-fechado.png`, fullPage: true });
await fr.evaluate(() => window.cnGeralToggle());
await espera(400);

// Transbordo por largura
console.log("-".repeat(78));
console.log("TRANSBORDO por largura (pagina tem de ser +0 em todas)");
for (const w of [1366, 1440, 1600, 1920, 2560]) {
  const pg = await browser.newPage();
  await pg.setViewport({ width: w, height: 1200 });
  await pg.goto(`${BASE}/app#dash/contas`, { waitUntil: "networkidle2" });
  await espera(4500);
  const f2 = pg.frames().find(f => f.url().includes("/dashboard"));
  await f2.evaluate(() => window.cnPop("ambas"));
  await espera(800);
  const a = await f2.evaluate(() => document.querySelector(".cn-ficha")
    ? document.documentElement.scrollWidth - document.documentElement.clientWidth : -1);
  await f2.evaluate(() => { const f = document.querySelector(".cn-ficha"); if (f) f.click(); });
  await espera(600);
  const b = await f2.evaluate(() => {
    const de = document.documentElement, d = document.querySelector(".cn-drill");
    return { pagina: de.scrollWidth - de.clientWidth, rola: d ? d.scrollWidth - d.clientWidth : -1 };
  });
  console.log(`  ${String(w).padStart(4)}px  fechado +${a}  |  drill +${b.pagina} (rola ${b.rola})  ${a === 0 && b.pagina === 0 ? "OK" : "TRANSBORDA"}`);
  await pg.close();
}

console.log("=".repeat(78));
if (ruimBarra) console.log(`ATENCAO: ${ruimBarra} barra(s) fora da regua.`);
if (!geralOk) console.log("ATENCAO: o recolher do bloco Geral nao passou.");
if (!p4Ok) console.log("ATENCAO: o 4o painel (Ultimas contas) nao passou.");
if (erros.length) { console.log("ERROS DE JS:"); erros.forEach(e => console.log("  " + e)); }
else console.log("ZERO erro de JS.");
console.log("prints em", SAIDA);
await browser.close();
