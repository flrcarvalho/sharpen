// Roda todos os casos de `casos/*.mjs` contra o código REAL da extensão.
//   node extensor/harness/run.mjs           → todos
//   node extensor/harness/run.mjs kto        → só a KTO
// Exit 1 se qualquer caso falhar. É o gate de regressão da captura: rode antes de todo
// commit que toque `*_inject.js` ou os formatadores do `content.js`.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const RAIZ = path.dirname(fileURLToPath(import.meta.url));
const filtro = process.argv.slice(2).map((s) => s.toLowerCase());

const arquivos = fs.readdirSync(path.join(RAIZ, "casos"))
  .filter((f) => f.endsWith(".mjs"))
  .filter((f) => !filtro.length || filtro.includes(path.basename(f, ".mjs").toLowerCase()))
  .sort();

if (!arquivos.length) {
  console.error(filtro.length ? `Nenhum caso casa com ${filtro.join(", ")}` : "Nenhum caso em casos/");
  process.exit(1);
}

// FALHAS CONHECIDAS (s409, decisão do Feca, 11/10/2026). Cada entrada absorve só as falhas
// de UM caso cujo texto começa pelo prefixo dado; qualquer outra falha do mesmo caso continua
// derrubando o gate. Elas são IMPRESSAS, nunca escondidas, e o executor avisa quando uma
// conhecida deixa de aparecer (aí ela sai daqui).
//
// Bet365, resolvedor de abertas: falha só em UTC (o CI). Aqui, com o fuso de Brasília, passa;
// com `TZ=UTC node extensor/harness/run.mjs bet365`, as 11 checagens do `resolverAbertas`
// falham. Vermelho desde a s407 e travando os passos seguintes do CI (auditoria do SharpenUp,
// tokens de marca, gate de documentação). Conserto quando a Bet365 migrar para a Ficha:
// BACKLOG §4 "Bet365: resolvedor de abertas depende do fuso".
const CONHECIDAS = [
  { caso: "Bet365", prefixo: "resolver", soEmUTC: true,
    motivo: "depende do fuso (falha em UTC); BACKLOG §4" },
];

let totalFalhas = 0, totalTestes = 0, totalConhecidas = 0;
const conhecidasVistas = new Set(), casosRodados = new Set();
for (const f of arquivos) {
  const mod = await import(pathToFileURL(path.join(RAIZ, "casos", f)).href);
  const nome = mod.casa || path.basename(f, ".mjs");
  casosRodados.add(nome);
  globalThis.__casoHarness = nome;
  let res;
  try {
    res = await mod.rodar();
  } catch (e) {
    res = { falhas: ["exceção: " + (e && e.stack || e)], testes: 0 };
  }
  const regras = CONHECIDAS.filter((k) => k.caso === nome);
  const conhecidas = [], falhas = [];
  for (const x of res.falhas || []) {
    const k = regras.find((r) => String(x).startsWith(r.prefixo));
    if (k) { conhecidas.push([x, k]); conhecidasVistas.add(k); } else falhas.push(x);
  }
  totalFalhas += falhas.length;
  totalConhecidas += conhecidas.length;
  totalTestes += res.testes || 0;
  const rotulo = falhas.length ? "  FALHA" : conhecidas.length ? "  CONH." : "  OK   ";
  console.log(`${rotulo} ${nome}  (${res.testes || 0} bilhete(s) conferido(s))`);
  for (const x of falhas) console.log("         → " + x);
  for (const [x, k] of conhecidas) console.log(`         ~ falha CONHECIDA (${k.motivo}): ${x}`);
}

// TRAVA DO CRU (s409): toda casa que imprimiu `[Código: …]` tem de ter mandado cru pelo
// inject, e todo cru tem de virar JSON (é o que vai no corpo do POST). Não cobra "código do
// texto sem cru": vários casos chamam o formatador direto com objeto montado no teste, sem
// passar pelo inject (Esportiva anuladas/cashout, os sintéticos da Bet365 e da Betnacional).
// No modo quebrado (`SHARPENUP_CRU_QUEBRADO`) o cru some de propósito e a trava não roda.
{
  const { CRU } = await import(pathToFileURL(path.join(RAIZ, "sandbox.mjs")).href);
  if (!process.env.SHARPENUP_CRU_QUEBRADO) {
    for (const [caso, r] of Object.entries(CRU)) {
      const f = [];
      if (r.naoJson) f.push(`${r.naoJson} cru(s) que não viram JSON`);
      if (r.texto.size && !r.itens) f.push(`imprimiu ${r.texto.size} código(s) e o inject não mandou cru nenhum`);
      if (f.length) {
        totalFalhas += f.length;
        console.log(`  FALHA ${caso} (cru)`);
        for (const x of f) console.log("         → " + x);
      }
    }
  }
}
if (process.env.SHARPENUP_FOTO) {
  const { FOTO, QUEBRAS } = await import(pathToFileURL(path.join(RAIZ, "sandbox.mjs")).href);
  if (process.env.SHARPENUP_CRU_QUEBRADO) {
    fs.writeFileSync(process.env.SHARPENUP_FOTO + ".quebras.json", JSON.stringify(QUEBRAS));
  }
  fs.writeFileSync(process.env.SHARPENUP_FOTO, JSON.stringify(FOTO, null, 0));
  console.log(`
fotografia: ${FOTO.length} registro(s) em ${process.env.SHARPENUP_FOTO}`);
}
console.log();
for (const k of CONHECIDAS) {
  const esperada = !k.soEmUTC || new Date().getTimezoneOffset() === 0;
  if (esperada && casosRodados.has(k.caso) && !conhecidasVistas.has(k)) {
    console.log(`AVISO: a falha conhecida de ${k.caso} ("${k.prefixo}…") não apareceu. ` +
                `Se ela foi consertada, tire-a de CONHECIDAS em run.mjs.`);
  }
}
if (totalConhecidas) console.log(`(${totalConhecidas} falha(s) CONHECIDA(S) impressa(s) acima, fora da conta.)`);
if (totalFalhas) {
  console.log(`RESULTADO: ${totalFalhas} falha(s) em ${arquivos.length} caso(s).`);
  process.exit(1);
}
console.log(`RESULTADO: verde — ${arquivos.length} caso(s), ${totalTestes} bilhete(s) conferido(s).`);
