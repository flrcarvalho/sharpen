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

let totalFalhas = 0, totalTestes = 0;
for (const f of arquivos) {
  const mod = await import(pathToFileURL(path.join(RAIZ, "casos", f)).href);
  const nome = mod.casa || path.basename(f, ".mjs");
  let res;
  try {
    res = await mod.rodar();
  } catch (e) {
    res = { falhas: ["exceção: " + (e && e.stack || e)], testes: 0 };
  }
  const falhas = res.falhas || [];
  totalFalhas += falhas.length;
  totalTestes += res.testes || 0;
  console.log(`${falhas.length ? "  FALHA" : "  OK   "} ${nome}  (${res.testes || 0} bilhete(s) conferido(s))`);
  for (const x of falhas) console.log("         → " + x);
}

console.log();
if (totalFalhas) {
  console.log(`RESULTADO: ${totalFalhas} falha(s) em ${arquivos.length} caso(s).`);
  process.exit(1);
}
console.log(`RESULTADO: verde — ${arquivos.length} caso(s), ${totalTestes} bilhete(s) conferido(s).`);
