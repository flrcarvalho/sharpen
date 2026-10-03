// A moeda que a casa informa sai no bloco da extensão (s391, passo 2b da moeda por conta).
//
// O que este arquivo prova, executando o código RECORTADO do `extensor/content.js`:
//
// A. `_linhaMoeda` NÃO escreve nada para real (`BRL`, `R$`, `brl`, vazio, null), e é isso
//    que mantém o texto das casas em real byte a byte igual (hash do `bloco_visto`);
// B. moeda que não é real sai como `Moeda: <o que a casa disse>`, sem traduzir: `$` segue
//    `$`, `usdt` segue `usdt`. Quem decide a compatibilidade é o servidor;
// C. os 7 formatadores cujo inject lê a moeda chamam `_linhaMoeda` com o bilhete deles.
//
// O que NÃO está coberto: a posição da linha dentro do bloco (logo após o `Stake:`) e o
// bloco inteiro de cada casa com moeda estrangeira. Os fixtures do harness são todos em
// real; o harness (`extensor/harness/run.mjs`) prova que o texto deles não mudou.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import vm from 'node:vm';

const AQUI = dirname(fileURLToPath(import.meta.url));
const RAIZ = join(AQUI, '..', '..');
// ALVO_CONTENT existe para a prova por MUTAÇÃO: o .py estraga uma cópia e aponta para ela.
const SRC = readFileSync(process.env.ALVO_CONTENT || join(RAIZ, 'extensor', 'content.js'), 'utf8')
  .replace(/\r\n/g, '\n');

let falhas = 0;
const ok = (cond, msg) => { if (!cond) { console.error('  ✗ ' + msg); falhas++; } };
const eq = (obtido, esperado, msg) => ok(obtido === esperado, msg + ', veio ' + JSON.stringify(obtido));

const recorteConst = (nome) => {
  const m = SRC.match(new RegExp('^  const ' + nome + ' = \\([^)]*\\) => \\{[\\s\\S]*?\\};$', 'm'));
  if (!m) throw new Error('não achei ' + nome + ' no content.js');
  return m[0];
};

const ctx = {};
vm.createContext(ctx);
vm.runInContext(recorteConst('_moedaNaoReal') + '\n' + recorteConst('_linhaMoeda') +
  '\nthis.linha = (m) => { const L = []; _linhaMoeda(L, m); return L; };', ctx);

// ── A. real não escreve nada ─────────────────────────────────────────────────
for (const m of ['BRL', 'brl', ' BRL ', 'R$', 'r$', '', null, undefined]) {
  eq(ctx.linha(m).length, 0, `A: ${JSON.stringify(m)} não gera linha`);
}

// ── B. o resto sai como a casa disse ─────────────────────────────────────────
eq(ctx.linha('$').join('|'), 'Moeda: $', 'B: "$" sai verbatim');
eq(ctx.linha('usdt').join('|'), 'Moeda: usdt', 'B: "usdt" sai verbatim');
eq(ctx.linha(' USD ').join('|'), 'Moeda: USD', 'B: espaço em volta sai aparado');
eq(ctx.linha('BRLX').join('|'), 'Moeda: BRLX', 'B: só o real EXATO se cala');

// ── C. os 7 formatadores chamam o helper com o próprio bilhete ───────────────
const ALVOS = [['formatTicketKTO', 'c'], ['formatTicketBDA', 'b'], ['formatTicketSTK', 'b'],
               ['formatTicketRG', 'b'], ['formatTicket1X', 'b'], ['formatTicketJB', 'b'],
               ['formatTicketTV', 't']];
for (const [nome, v] of ALVOS) {
  const ini = SRC.indexOf('  function ' + nome + '(' + v + ') {\n');
  ok(ini >= 0, `C: ${nome} existe`);
  if (ini < 0) continue;
  const fim = SRC.indexOf('\n  function ', ini + 10);
  const corpo = SRC.slice(ini, fim < 0 ? undefined : fim);
  ok(corpo.includes(`_linhaMoeda(L, ${v}.moeda);`), `C: ${nome} escreve a moeda do bilhete`);
}

if (falhas) { console.error(`\n${falhas} falha(s)`); process.exit(1); }
console.log('ok: moeda da casa no bloco da extensão');
