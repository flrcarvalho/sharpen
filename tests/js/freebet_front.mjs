// FREEBET no dashboard (s392, passo 2c, MASTER_RESULTADO 5.8).
//
// O que este arquivo prova, executando o código RECORTADO dos arquivos de produção:
//
// A. `_aplicarFreebet` (app.js): linha com `stake_freebet` passa a ter `stake` = dinheiro
//    real e `stake_cheio` = o apostado; linha SEM freebet não muda em nada (nem ganha chave);
//    freebet maior que a stake é ignorada;
// B. turnover e ROI (`calcTurnover`/`calcROI`, sem mudança de código) passam a medir o
//    dinheiro real — o caso da MyStake: freebet de R$ 45 perdida + aposta de R$ 70 perdida;
// C. `stakeCheio` devolve o apostado com e sem freebet;
// D. o modal e a edição inline (`_apEditVal`, apostas.js) mostram e comparam o APOSTADO —
//    mandar o `stake` real de volta gravaria R$ 0 numa freebet inteira;
// E. exibição e ordenação (apostas.js, abertas.js) e a assinatura de stakes do tipster
//    (gestao.js) leem `stakeCheio` — por presença no fonte.
//
// O que NÃO está coberto: o visual (a stake exibida é a mesma de antes, sem marca nova),
// e o `aplicarFeed` inteiro com o `normalizeDados` (só a transformação que ele chama).
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import vm from 'node:vm';

const AQUI = dirname(fileURLToPath(import.meta.url));
const RAIZ = join(AQUI, '..', '..');
const DASH = join(RAIZ, 'app', 'static', 'dash', 'assets', 'js');
const ler = (env, p) => readFileSync(process.env[env] || p, 'utf8').replace(/\r\n/g, '\n');
const APP = ler('ALVO_APP', join(DASH, 'app.js'));
const APOSTAS = ler('ALVO_APOSTAS', join(DASH, 'charts', 'apostas.js'));
const ABERTAS = ler('ALVO_ABERTAS', join(DASH, 'charts', 'abertas.js'));
const GESTAO = ler('ALVO_GESTAO', join(DASH, 'charts', 'gestao.js'));

let falhas = 0;
const ok = (cond, msg) => { if (!cond) { console.error('  ✗ ' + msg); falhas++; } };
const eq = (obtido, esperado, msg) => ok(obtido === esperado, msg + ', veio ' + JSON.stringify(obtido));

// Recorta `function nome(...){ ... }` de uma linha só, ou de várias até a `}` na coluna 0.
const recorte = (src, nome) => {
  const uma = src.match(new RegExp('^function ' + nome + '\\([^)]*\\)\\s*\\{.*\\}$', 'm'));
  if (uma) return uma[0];
  const m = src.match(new RegExp('^function ' + nome + '\\([^)]*\\)\\s*\\{[\\s\\S]*?^\\}', 'm'));
  if (!m) throw new Error('não achei a função ' + nome);
  return m[0];
};

const ctx = {};
vm.createContext(ctx);
vm.runInContext([
  recorte(APP, '_aplicarFreebet'), recorte(APP, 'stakeCheio'),
  recorte(APP, 'calcTurnover'), recorte(APP, 'calcROI'), recorte(APOSTAS, '_apIsoToBR'),
  recorte(APOSTAS, '_apEditVal'),
].join('\n'), ctx);
const { _aplicarFreebet, stakeCheio, calcTurnover, calcROI, _apEditVal } = ctx;

// ── A ──
const fb = _aplicarFreebet({ stake: 45, stake_freebet: 45, lucro: 0, resultado: 'L' });
eq(fb.stake, 0, 'A: freebet inteira vira dinheiro real 0');
eq(fb.stake_cheio, 45, 'A: o apostado fica em stake_cheio');
const parcial = _aplicarFreebet({ stake: 200, stake_freebet: 10, lucro: -190, resultado: 'L' });
eq(parcial.stake, 190, 'A: freebet parcial desconta só a parte da casa');
const normal = _aplicarFreebet({ stake: 70, lucro: -70, resultado: 'L' });
eq(normal.stake, 70, 'A: linha sem freebet não muda');
ok(!('stake_cheio' in normal), 'A: linha sem freebet não ganha stake_cheio');
const invalida = _aplicarFreebet({ stake: 10, stake_freebet: 45, lucro: -10, resultado: 'L' });
eq(invalida.stake, 10, 'A: freebet maior que a stake é ignorada');

// ── B ──
const rows = [fb, normal];
eq(calcTurnover(rows), 70, 'B: turnover = dinheiro real (a freebet não é volume)');
eq(Math.round(calcROI(rows) * 100) / 100, -100, 'B: ROI = −70 / 70');

// ── C ──
eq(stakeCheio(fb), 45, 'C: stakeCheio da freebet é o apostado');
eq(stakeCheio(normal), 70, 'C: stakeCheio sem freebet é a stake');

// ── D ──
eq(_apEditVal(fb, 'stake'), '45', 'D: o input da edição mostra o apostado, não o real');
eq(_apEditVal(normal, 'stake'), '70', 'D: sem freebet, a stake de sempre');

// ── E ──
const presente = (src, trecho, msg) => ok(src.includes(trecho), msg);
presente(APOSTAS, "${df('stake')}>${fmtR(stakeCheio(r))}", 'E: a Base Completa exibe o apostado');
presente(APOSTAS, "col==='stake'?stakeCheio(r).toString()", 'E: ordenar/exportar pela stake usa o apostado');
presente(APOSTAS, 'if(sMin!==null&&!(stakeCheio(r)>=sMin))return false;', 'E: o filtro de faixa usa o apostado');
presente(ABERTAS, "${df('stake')}>${fmtR(stakeCheio(r))}</div>", 'E: Em Aberto exibe o apostado');
presente(GESTAO, 'a.stakes[stakeCheio(r)]', 'E: a assinatura de stakes do tipster usa o apostado');
presente(APP, 'const norm=normalizeDados(dados).map(_aplicarFreebet);', 'E: o aplicarFeed aplica a freebet');

if (falhas) { console.error(`\n${falhas} falha(s)`); process.exit(1); }
console.log('freebet_front: ok');
