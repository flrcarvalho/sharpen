// Condição (b) do Feca para a atualização do cru (s409): QUEBRAR o cru não muda o texto.
//
//   node extensor/harness/cru_mutacao.mjs
//
// Roda o harness inteiro duas vezes, fotografando toda mensagem dos injects (sem o campo
// `cru`) e toda saída dos formatadores: uma normal e uma com `SHARPENUP_CRU_QUEBRADO=1`, em
// que cada ponto que MONTA ou MANDA o cru lança erro (ver `sandbox.mjs`, "MODO QUEBRADO").
// Exit 1 se as fotografias diferirem, se o modo quebrado não achou algum dos seus alvos
// (quebra que não casou não testa nada), ou se o harness normal não ficou verde.
//
// Única diferença tolerada entre duas rodadas: o cronômetro `"ms":N` das mensagens do
// resolvedor da Bet365, que varia entre duas rodadas do MESMO código.
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const RAIZ = path.dirname(fileURLToPath(import.meta.url));
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "cru-mutacao-"));
const run = path.join(RAIZ, "run.mjs");

function rodar(nome, extra) {
  const foto = path.join(tmp, nome + ".json");
  const r = spawnSync(process.execPath, [run], {
    env: Object.assign({}, process.env, { SHARPENUP_FOTO: foto }, extra), encoding: "utf8",
  });
  return { foto, status: r.status, saida: (r.stdout || "") + (r.stderr || "") };
}

const norm = (p) => JSON.parse(fs.readFileSync(p, "utf8"))
  .map((x) => Object.assign({}, x, { v: x.v.replace(/"ms":\d+/g, '"ms":_') }));

const normal = rodar("normal", {});
const quebrado = rodar("quebrado", { SHARPENUP_CRU_QUEBRADO: "1" });
const falhas = [];
if (normal.status !== 0) falhas.push("o harness NORMAL não ficou verde:\n" + normal.saida.slice(-1500));
// Harness quebrado que CAI (sem gravar a fotografia) = o erro do cru escapou para o código da
// captura. É a falha mais grave que este teste existe para pegar.
if (!fs.existsSync(quebrado.foto) || !fs.existsSync(quebrado.foto + ".quebras.json")) {
  console.log("FALHA → com o cru quebrado o harness CAIU: o erro do cru escapou para a captura.\n" +
              quebrado.saida.split("\n").filter((l) => !/^\s+at /.test(l)).slice(-8).join("\n"));
  process.exit(1);
}
const quebras = JSON.parse(fs.readFileSync(quebrado.foto + ".quebras.json", "utf8"));
for (const [alvo, n] of Object.entries(quebras)) {
  if (!n) falhas.push(`a quebra de "${alvo}" não achou alvo em arquivo nenhum`);
}
const a = norm(normal.foto), b = norm(quebrado.foto);
let iguais = a.length === b.length;
let primeira = null;
for (let i = 0; iguais && i < a.length; i++) {
  if (a[i].caso !== b[i].caso || a[i].tipo !== b[i].tipo || a[i].v !== b[i].v) { iguais = false; primeira = i; }
}
if (!iguais) {
  const i = primeira == null ? Math.min(a.length, b.length) : primeira;
  falhas.push(`o TEXTO mudou com o cru quebrado (registros ${a.length} × ${b.length}; 1º diferente: ` +
              `${(a[i] || {}).caso} ${(a[i] || {}).tipo})`);
}
console.log(`fotografias: normal ${a.length} · quebrado ${b.length} registro(s) · quebras: ` +
            Object.entries(quebras).map(([k, n]) => `${k.slice(0, 28)}=${n}`).join(" · "));
if (falhas.length) {
  for (const f of falhas) console.log("FALHA → " + f);
  process.exit(1);
}
console.log("RESULTADO: cru quebrado, texto IDÊNTICO.");
