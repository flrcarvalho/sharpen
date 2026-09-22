/**
 * Captura os dois recortes do folder da tela Contas.
 *
 * A tela, o markup e o CSS sao os REAIS (servidor_demo): so os VALORES sao trocados no
 * DOM, para bater com a operacao do Feca (decisao dele), e os NOMES de conta e de
 * fornecedor entram ficticios. Assim o folder mostra a tela como ela e, sem publicar
 * conta de ninguem.
 *
 *   node v-folder.mjs <pasta de saida> [porta]
 */
import puppeteer from "puppeteer-core";
const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const SAIDA = process.argv[2];
const PORTA = process.argv[3] || "8655";
const espera = ms => new Promise(r => setTimeout(r, ms));

const browser = await puppeteer.launch({ executablePath: CHROME, headless: "new" });
const page = await browser.newPage();
await page.setViewport({ width: 1760, height: 1500, deviceScaleFactor: 2 });
await page.goto(`http://127.0.0.1:${PORTA}/app#dash/contas`, { waitUntil: "networkidle2" });
await espera(7500);
const fr = page.frames().find(f => f.url().includes("/dashboard"));
await fr.evaluate(() => window.cnPop("ambas"));
await espera(900);

const GERAL = {
  regua: "111 COM PREÇO · 68 PRÓPRIAS · 5 SEM PREÇO",
  cab: "184 contas inativas",
  p1: {
    ctx: "184 contas inativas", v: ["10 dias", "24 dias"],
    faixas: [["79 · 43%", 43], ["30 · 16%", 16], ["25 · 14%", 14],
             ["25 · 14%", 14], ["25 · 14%", 14]],
    foot: "<b>Metade das suas contas durou menos de 10 dias</b>, e 43% não passou da "
        + "primeira semana. A média fica em 24 porque 25 contas passaram de 60 dias e "
        + "puxam o número para cima.",
  },
  p2: {
    ctx: "histórico", v: ["+6,06%", "+7,71%"],
    rank: [["Superbet", "53", "+9,63%"], ["Betano", "41", "+8,25%"],
           ["Bet365", "17", "+4,58%"], ["Betfair", "9", "+13,69%"],
           ["Pinnacle", "6", "−8,84%"]],
    foot: "Cada conta movimentou R$ 25.294 em 13 dias ativos, em média. <b>O líquido é o "
        + "que sobra depois do custo da conta</b>; a diferença para o bruto é o quanto a "
        + "aquisição come da margem.",
  },
  p3: {
    ctx: "179 de 184 contas", v: ["4,65×"],
    linhas: ["R$ 74.284", "+R$ 345.783,50", "+R$ 271.499,50"],
    cov: [111 / 184 * 100, 68 / 184 * 100, 5 / 184 * 100],
    legs: ["111 com preço", "68 próprias", "5 sem preço"],
    foot: '<b>Cada R$ 1 gasto em conta voltou 4,65 reais.</b> Abaixo de 1,00× a conta não '
        + 'devolveu o que custou. As 68 próprias entram com custo zero real. As '
        + '<span class="cn-warnc">5 sem preço</span> ficam fora do cálculo, porque '
        + 'tratá-las como zero inflaria o retorno.',
  },
};

await fr.evaluate((G) => {
  const q = s => document.querySelector(s);
  const ps = [...document.querySelectorAll("#cnGeralCorpo > .cn-q3 > .cn-qp")];
  q(".cn-regua__esc").textContent = G.regua;
  q(".cn-geral__top .m").textContent = G.cab;

  const poe = (p, d) => {
    if (d.ctx) p.querySelector(".s").textContent = d.ctx;
    [...p.querySelectorAll(".cn-fig .v")].forEach((v, i) => { if (d.v[i]) v.textContent = d.v[i]; });
    if (d.foot) p.querySelector(".cn-foot").innerHTML = d.foot;
  };
  poe(ps[0], G.p1); poe(ps[1], G.p2); poe(ps[2], G.p3);

  [...ps[0].querySelectorAll(".cn-drow")].forEach((r, i) => {
    r.querySelector(".rv").textContent = G.p1.faixas[i][0];
    const b = r.querySelector(".cn-dbar i");
    b.style.width = G.p1.faixas[i][1] + "%";
    b.className = i === 0 ? "hot" : "";
  });

  // O chip vem do favicon da casa: trocar so o TEXTO deixaria a Superbet com o icone da
  // Bet365. Regenera o chip pela funcao real do app.
  [...ps[1].querySelectorAll(".cn-mrow")].forEach((r, i) => {
    const [casa, n, roi] = G.p2.rank[i];
    r.querySelector(".nm").innerHTML = mkHouseChip(casa) + casa;
    r.querySelector(".vv .q").textContent = n;
    r.querySelector(".vv .u").textContent = n === "1" ? "conta" : "contas";
    const p = r.querySelector(".vv .p");
    p.textContent = roi;
    p.className = roi.indexOf("−") === 0 ? "p cn-roi-neg" : "p cn-roi-pos";
  });

  [...ps[2].querySelectorAll(".cn-crow .cn")].forEach((c, i) => {
    const t = G.p3.linhas[i];
    const m = c.querySelector(".money-val");
    if (m) m.textContent = t.replace(/^[+\u2212-]?R\$\s*/, "");
    else c.textContent = t;
  });
  [...ps[2].querySelectorAll(".cn-covbar i")].forEach((b, i) => b.style.width = G.p3.cov[i] + "%");
  [...ps[2].querySelectorAll(".cn-covwrap span span, .cn-covleg span")]
    .forEach((s, i) => { if (G.p3.legs[i]) s.textContent = G.p3.legs[i]; });
}, GERAL);
await espera(600);

const off = await page.evaluate(() => {
  const r = document.querySelector("iframe").getBoundingClientRect();
  return { x: r.left, y: r.top };
});
const cA = await fr.evaluate(() => {
  const g = document.getElementById("cnGeral").getBoundingClientRect();
  return { x: g.left, y: g.top, w: g.width, h: g.height };
});
await page.screenshot({ path: `${SAIDA}/recorte-geral.png`,
  clip: { x: off.x + cA.x, y: off.y + cA.y, width: cA.w, height: cA.h } });
console.log("A: bloco Geral " + Math.round(cA.w) + "x" + Math.round(cA.h));
// Posicao dos alvos em % do RECORTE: as chamadas do folder saem daqui, nao de chute.
const posA = await fr.evaluate((c) => {
  const pct = el => { const b = el.getBoundingClientRect();
    return { x: (b.left - c.x) / c.w * 100, y: (b.top - c.y) / c.h * 100 }; };
  return [...document.querySelectorAll("#cnGeralCorpo > .cn-q3 > .cn-qp")].map(pct);
}, cA);

// ── B: a lista Por casa ─────────────────────────────────────────────────────
// Recolhe o Geral: ele ja foi o recorte A, e o folder mostra a lista logo abaixo.
await fr.evaluate(() => window.cnGeralToggle());
await espera(500);

// As fichas do demo entram na ordem dele (por quantidade de contas) e com os numeros
// dele. O chip e regenerado pela funcao real do app: trocar so o nome deixaria a casa
// com o icone da vizinha.
const FICHAS = [
  ["Superbet", "58", "3 ativas", 6, 13, "8", "12.858", "+7,51%", "+12,67%", "51,96", "38.500", 2.45],
  ["Betano",   "41", "5 ativas", 9, 18, "11", "18.402", "+8,25%", "+11,90%", "38,20", "21.400", 3.12],
  ["Bet365",   "17", "2 ativas", 14, 29, "19", "31.775", "+4,58%", "+6,14%", "22,74", "9.800", 4.03],
  ["Betfair",  "9",  "1 ativa",  21, 34, "24", "27.140", "+13,69%", "+15,02%", "12,85", "3.400", 6.88],
  ["Pinnacle", "6",  "0 ativas", 27, 41, "30", "19.630", "−8,84%", "−7,15%", "9,40", "2.300", -1.42],
];
// ⚠️ `cnToggle` REPINTA a tela inteira, entao abrir o drill desfaz esta injecao: ela
// precisa rodar de novo depois do clique. Daí ser funcao, e nao trecho solto.
const injetarFichas = (F) => fr.evaluate((F) => {
  const REGUA = 30, GAUGE = 10;
  [...document.querySelectorAll(".cn-ficha")].forEach((f, i) => {
    const d = F[i];
    if (!d) { f.remove(); return; }
    const [casa, n, sub, med, media, ativos, turn, liq, bruto, dia, custo, mult] = d;
    f.querySelector(".cn-fname").innerHTML = casaCell(casa)
      + '<span class="sub">' + sub + "</span>";
    const cel = f.querySelectorAll(".cn-fcell");
    cel[0].querySelector(".n").textContent = n;
    cel[0].querySelector(".s").textContent = n === "1" ? "conta" : "contas";
    f.querySelector(".cn-track .med").style.width = Math.min(med / REGUA * 100, 100) + "%";
    f.querySelector(".cn-track .avg").style.left = Math.min(media / REGUA * 100, 100) + "%";
    const lab = f.querySelectorAll(".cn-lifelab span");
    lab[0].innerHTML = "mediana <b>" + med + " d</b>";
    lab[1].innerHTML = "média <b>" + media + " d</b>";
    lab[2].innerHTML = "ativos <b>" + ativos + "</b>";
    cel[1].querySelector(".n").innerHTML =
      '<span class="money"><span class="money-sign">R$</span><span class="money-val">'
      + turn + "</span></span>";
    const cls = t => (t.indexOf("−") === 0 ? "cn-roi-neg" : "cn-roi-pos");
    cel[1].querySelector(".s").innerHTML = 'líq. <span class="' + cls(liq) + '">' + liq
      + '</span> · bruto <span class="' + cls(bruto) + '">' + bruto + "</span>";
    cel[2].querySelector(".n").innerHTML =
      '<span class="money"><span class="money-sign">R$</span><span class="money-val">'
      + dia + "</span></span>";
    cel[2].querySelector(".s").textContent = "custo R$ " + custo;
    const mw = f.querySelector(".cn-multwrap");
    mw.querySelector(".n").innerHTML = '<span class="' + (mult < 1 ? "cn-roi-neg" : "cn-roi-pos")
      + '">' + mult.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })
      + '<span class="x">×</span></span>';
    const g = mw.querySelector(".cn-gauge i");
    g.style.width = Math.max(Math.min(Math.abs(mult) / GAUGE * 100, 100), 1.5) + "%";
    g.className = mult < 1 ? "under" : "";
  });
}, F);

await injetarFichas(FICHAS);
await espera(600);

const cL = await fr.evaluate(() => {
  const s = document.querySelector(".cn-secao").getBoundingClientRect();
  const fs = [...document.querySelectorAll(".cn-ficha")];
  const u = fs[fs.length - 1].getBoundingClientRect();
  return { x: s.left, y: s.top, w: s.width, h: u.bottom - s.top + 4 };
});
await page.screenshot({ path: `${SAIDA}/recorte-lista.png`,
  clip: { x: off.x + cL.x, y: off.y + cL.y, width: cL.w, height: cL.h } });
console.log("B: lista Por casa " + Math.round(cL.w) + "x" + Math.round(cL.h));
const posB = await fr.evaluate((c) => {
  const f = document.querySelector(".cn-ficha").getBoundingClientRect();
  const t = document.querySelector(".cn-fhead").getBoundingClientRect();
  return { ficha: { x: (f.left - c.x) / c.w * 100, y: (f.top - c.y) / c.h * 100 },
           head: { x: (t.left - c.x) / c.w * 100, y: (t.top - c.y) / c.h * 100 } };
}, cL);

// ── C: uma casa aberta ──────────────────────────────────────────────────────
await fr.evaluate(() => { document.querySelector(".cn-ficha").click(); });
await espera(1200);
await injetarFichas(FICHAS);   // o repaint do toggle desfez a injecao acima
await espera(400);

const CASA = {
  fichaSub: "3 ativas", med: "6 d", media: "13 d", ativos: "8",
  p1: {
    ctx: "58 contas", v: ["6 dias", "13 dias"],
    faixas: [["30 · 52%", 52], ["11 · 19%", 19], ["9 · 16%", 16], ["7 · 12%", 12], ["1 · 2%", 2]],
    foot: "<b>Metade das contas da Superbet durou menos de 6 dias</b>, e 52% não passou da "
        + "primeira semana. A média fica em 13 porque 1 conta passou de 60 dias e puxa o "
        + "número para cima.",
  },
  p2: {
    ctx: "histórico", v: ["+7,51%", "+12,67%"],
    foot: "Cada conta movimentou R$ 12.858 em 8 dias ativos, em média. <b>O líquido é o que "
        + "sobra depois do custo da conta</b>; a diferença para o bruto é o quanto a "
        + "aquisição come da margem.",
  },
  p3: {
    ctx: "58 de 58 contas", v: ["2,45×"],
    linhas: ["R$ 38.500", "+R$ 94.517,37", "+R$ 56.017,37"],
    cov: [56 / 58 * 100, 2 / 58 * 100, 0],
    legs: ["56 com preço", "2 próprias", "0 sem preço"],
    foot: "<b>Cada R$ 1 gasto em conta voltou 2,45 reais.</b> Abaixo de 1,00× a conta não "
        + "devolveu o que custou. As 2 próprias entram com custo zero real. Toda conta do "
        + "recorte tem preço lançado.",
  },
  p4: {
    ctx: "desde 12/08", v: ["4 dias", "6 dias"],
    comp: [["ROI líquido", "+5,12%", "+7,51%"], ["Múltiplo", "1,86×", "2,45×"]],
    foot: "As 10 contas mais recentes duraram 2 dias a menos que a mediana da casa. "
        + "2 seguem ativas e ficam fora da conta de duração.",
  },
};

// Nomes ficticios, no mesmo formato dos reais. Nada aqui e conta de ninguem.
const LINHAS = [
  ["marianalopes203040", "MV", 1, "17 d", "16", "354", "61.233", "+6.853,93", "500", "+6.353,93", "+10,38%"],
  ["KaR1515", "TopPro", 0, "33 d", "20", "199", "52.519", "+29.053,50", "600", "+28.453,50", "+54,18%"],
  ["rafaelsouzainvest", "Leandro", 0, "23 d", "22", "281", "44.940", "+11.679,90", "916", "+10.763,90", "+23,95%"],
  ["Brunog20contas", "TopPro", 0, "51 d", "33", "226", "40.849", "\u22125.601,83", "600", "\u22126.201,83", "\u221215,18%"],
  ["contaprincipal01", "Eu", 0, "82 d", "29", "275", "39.731", "+5.980,04", "própria", "+5.980,04", "+15,05%"],
  ["tiagomelo03", "Leandro", 0, "15 d", "14", "204", "38.545", "+9.160,86", "916", "+8.244,86", "+21,39%"],
  ["andrecosta03", "Leandro", 0, "20 d", "19", "190", "37.592", "+20.631,84", "916", "+19.715,84", "+52,45%"],
  ["carolinaduartebets", "MV", 0, "34 d", "27", "177", "35.072", "+1.607,83", "500", "+1.107,83", "+3,16%"],
  ["julianapires01", "Leandro", 0, "8 d", "8", "164", "26.770", "+2.490,43", "916", "+1.574,43", "+5,88%"],
];

await fr.evaluate((arg) => {
  const C = arg.C, L = arg.L;
  const neg = t => t.indexOf("\u2212") === 0;
  const money = (txt, cls) => '<span class="money ' + (cls || "") + '">'
    + '<span class="money-sign">R$</span><span class="money-val">'
    + txt.replace(/^[+\u2212-]?R\$\s*/, "") + "</span></span>";

  const ps = [...document.querySelectorAll(".cn-drill .cn-q3 > .cn-qp")];
  // O demo tem 9 contas nesta casa; o folder mostra o recorte de 10 do painel.
  ps[3].querySelector(".t").textContent = "Últimas 10 contas";
  const poe = (p, d) => {
    if (d.ctx) p.querySelector(".s").textContent = d.ctx;
    [...p.querySelectorAll(".cn-fig .v")].forEach((v, i) => { if (d.v && d.v[i]) v.textContent = d.v[i]; });
    if (d.foot) p.querySelector(".cn-foot").innerHTML = d.foot;
  };
  poe(ps[0], C.p1); poe(ps[1], C.p2); poe(ps[2], C.p3); poe(ps[3], C.p4);

  [...ps[0].querySelectorAll(".cn-drow")].forEach((r, i) => {
    r.querySelector(".rv").textContent = C.p1.faixas[i][0];
    const b = r.querySelector(".cn-dbar i");
    b.style.width = C.p1.faixas[i][1] + "%";
    b.className = i === 0 ? "hot" : "";
  });
  [...ps[2].querySelectorAll(".cn-crow .cn")].forEach((c, i) => {
    const t = C.p3.linhas[i];
    const m = c.querySelector(".money-val");
    if (m) m.textContent = t.replace(/^[+\u2212-]?R\$\s*/, "");
    else c.textContent = t;
  });
  [...ps[2].querySelectorAll(".cn-covbar i")].forEach((b, i) => b.style.width = C.p3.cov[i] + "%");
  [...ps[2].querySelectorAll(".cn-covwrap span span, .cn-covleg span")]
    .forEach((s, i) => { if (C.p3.legs[i]) s.textContent = C.p3.legs[i]; });

  const rows = [...ps[3].querySelectorAll(".cn-crow--cmp")]
    .filter(r => r.className.indexOf("cn-crow--head") < 0);
  rows.forEach((r, i) => {
    if (!C.p4.comp[i]) return;
    r.querySelector(".cl").textContent = C.p4.comp[i][0];
    r.querySelector(".cn").innerHTML = '<span class="cn-roi-pos">' + C.p4.comp[i][1] + "</span>";
    r.querySelector(".ch").innerHTML = '<span class="cn-roi-pos">' + C.p4.comp[i][2] + "</span>";
  });
  [...ps[3].querySelectorAll(".cn-urow")].forEach((u, i) => {
    const l = L[i];
    if (!l) { u.remove(); return; }
    u.querySelector(".nm").textContent = l[0];
    u.querySelector(".du").textContent = l[3];
    u.querySelector(".es").innerHTML = l[2]
      ? '<span class="cn-tag cn-tag--on">ativa</span>' : '<span class="cn-tag">inativa</span>';
  });

  [...ps[1].querySelectorAll(".cn-mrow")].forEach((r, i) => {
    const l = L[i];
    if (!l) { r.remove(); return; }
    r.querySelector(".nm").textContent = l[0];
    r.querySelector(".vv").innerHTML = "<b>R$ " + l[6] + "</b> · "
      + '<span class="' + (neg(l[10]) ? "cn-roi-neg" : "cn-roi-pos") + '">' + l[10] + "</span>";
  });

  [...document.querySelectorAll(".cn-drill > table > tbody > tr")].forEach((tr, i) => {
    const l = L[i];
    if (!l) { tr.remove(); return; }
    const td = tr.querySelectorAll("td");
    td[0].textContent = l[0];
    td[1].textContent = l[1];
    td[2].innerHTML = l[2] ? '<span class="cn-tag cn-tag--on">ativa</span>'
                           : '<span class="cn-tag">inativa</span>';
    td[3].textContent = l[3];
    td[4].textContent = l[4];
    td[5].textContent = l[5];
    td[6].innerHTML = money("R$ " + l[6]);
    td[7].innerHTML = money(l[7], neg(l[7]) ? "cn-roi-neg" : "cn-roi-pos");
    td[8].innerHTML = l[8] === "própria" ? '<span class="cn-propria">própria</span>' : money("R$ " + l[8]);
    td[9].innerHTML = money(l[9], neg(l[9]) ? "cn-roi-neg" : "cn-roi-pos");
    td[10].innerHTML = '<span class="' + (neg(l[10]) ? "cn-roi-neg" : "cn-roi-pos") + '">' + l[10] + "</span>";
  });
  const rod = document.querySelector(".cn-drillfoot");
  if (rod) rod.innerHTML = rod.innerHTML.replace(/\d+ contas nesta casa/, "58 contas nesta casa");
}, { C: CASA, L: LINHAS });
await espera(700);

// O recorte C comeca na FICHA, nao na secao: o cabecalho "Por casa" e a legenda da
// barra ja sao o recorte B, e repeti-los aqui alonga o folder sem dizer nada novo.
const cB = await fr.evaluate(() => {
  const f = document.querySelector(".cn-ficha").getBoundingClientRect();
  const s = document.querySelector(".cn-secao").getBoundingClientRect();
  const d = document.querySelector(".cn-drill").getBoundingClientRect();
  return { x: s.left, y: f.top - 10, w: s.width, h: d.bottom - f.top + 10 };
});
await page.screenshot({ path: `${SAIDA}/recorte-casa.png`,
  clip: { x: off.x + cB.x, y: off.y + cB.y, width: cB.w, height: cB.h } });
console.log("C: casa aberta " + Math.round(cB.w) + "x" + Math.round(cB.h));
const posC = await fr.evaluate((c) => {
  const pct = el => { const b = el.getBoundingClientRect();
    return { x: (b.left - c.x) / c.w * 100, y: (b.top - c.y) / c.h * 100 }; };
  const ps = [...document.querySelectorAll(".cn-drill .cn-q3 > .cn-qp")];
  return { p4: pct(ps[3]), tabela: pct(document.querySelector(".cn-drill > table")),
           ficha: pct(document.querySelector(".cn-ficha")) };
}, cB);

const fs = await import("node:fs");
fs.writeFileSync(`${SAIDA}/pos.json`, JSON.stringify(
  { A: { w: cA.w, h: cA.h, paineis: posA },
    B: { w: cL.w, h: cL.h, ...posB },
    C: { w: cB.w, h: cB.h, ...posC } }, null, 1));
console.log("posicoes gravadas em pos.json");
await browser.close();
