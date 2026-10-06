// Valor na moeda original da conta, na grade e na Base Completa (s391, passo 3).
//
// O que este arquivo prova, executando o código RECORTADO dos arquivos de produção:
//
// A. `fmtMoedaOrig` escreve "US$ 1.234,50" e "1.234,50 USDT" (decisão do Feca), com
//    milhar pt-BR, e a versão do dashboard (`app.js`) dá o MESMO texto que a da grade;
// B. `moneyOrig` usa o componente `.money`: cor e sinal só com `pl`, zero neutro;
// C. a célula da stake: vendo em R$, o R$ editável e o original embaixo; vendo na moeda
//    da conta, o original editável como `stake_orig` (s398) e o R$ embaixo; linha sem
//    origem segue em R$ e editável; o USD do Polymarket segue como era;
// D. a célula de P/L troca para o `pl_orig` só no modo moeda da conta, e leva a OUTRA
//    moeda embaixo, neutra e com sinal, como a stake (pedido do Feca, 03/10/2026);
// E. o seletor só aparece em conta USD/USDT, volta a R$ em conta BRL e põe a moeda nos
//    cabeçalhos;
// F. a Base Completa (`apostas.js`) desenha a sub-linha com o helper do dashboard.
//
// O que NÃO está coberto: o visual e o clique real (é a medição no navegador), e o
// `renderGrade` inteiro (só as células que ele chama).
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import vm from 'node:vm';

const AQUI = dirname(fileURLToPath(import.meta.url));
const RAIZ = join(AQUI, '..', '..');
const DASH = join(RAIZ, 'app', 'static', 'dash', 'assets', 'js');
// ALVO_* existem para a prova por MUTAÇÃO: o .py estraga uma cópia e aponta para ela.
const ler = (env, p) => readFileSync(process.env[env] || p, 'utf8').replace(/\r\n/g, '\n');
const INDEX = ler('ALVO_INDEX', join(RAIZ, 'app', 'static', 'index.html'));
const APP = ler('ALVO_APP', join(DASH, 'app.js'));
const APOSTAS = ler('ALVO_APOSTAS', join(DASH, 'charts', 'apostas.js'));

let falhas = 0;
const ok = (cond, msg) => { if (!cond) { console.error('  ✗ ' + msg); falhas++; } };
const eq = (obtido, esperado, msg) => ok(obtido === esperado, msg + ', veio ' + JSON.stringify(obtido));

const recorteFn = (src, nome) => {
  const uma = src.match(new RegExp('^function ' + nome + '\\([^)]*\\)\\s*\\{.*\\}$', 'm'));
  if (uma) return uma[0];
  const m = src.match(new RegExp('^(\\s*)function ' + nome + '\\([^)]*\\) \\{[\\s\\S]*?^\\1\\}', 'm'));
  if (!m) throw new Error('não achei a função ' + nome);
  return m[0];
};
const recorteConst = (src, nome) => {
  const m = src.match(new RegExp('^const ' + nome + '\\s*=.*;$', 'm'));
  if (!m) throw new Error('não achei a const ' + nome);
  return m[0];
};

// ── Grade (index.html) ───────────────────────────────────────────────────────
function montarGrade() {
  const el = (extra = {}) => {
    const cls = new Set(extra.cls || []);
    return { textContent: extra.txt || '', hidden: !!extra.hidden, dataset: extra.dataset || {},
      classList: { toggle: (c, f) => (f ? cls.add(c) : cls.delete(c)), contains: c => cls.has(c) } };
  };
  const D = { 'grade-moeda': el({ hidden: true }), 'grade-moeda-orig': el({ txt: 'USDT' }),
              'th-stake': el({ txt: 'Stake' }), 'th-pl': el({ txt: 'P/L' }) };
  const botoes = [el({ dataset: { ver: 'BRL' }, cls: ['on'] }), el({ dataset: { ver: 'orig' } })];
  const ctx = {
    D, botoes, console,
    document: { getElementById: id => D[id] || null,
                querySelectorAll: sel => sel === '#grade-moeda-seg button' ? botoes : [] },
  };
  vm.createContext(ctx);
  const dubles = `
    let parceiroSelecionado = null;
    const esc = s => String(s == null ? '' : s);
    function fmtUSD(v) { return '$ ' + Number(v || 0).toFixed(2).replace('.', ','); }
    function moneyStake(v) { return v ? '[R$ ' + v + ']' : ''; }
    function fmtPL(v) { return v == null ? '[—]' : '[PL ' + v + ']'; }
    function _faltando() { return '[faltando]'; }
  `;
  const codigo = [recorteConst(INDEX, '_MOEDA_ORIG'), 'let _grVer = \'BRL\';',
    ...['_num2BR', 'fmtMoedaOrig', 'moneyOrig', '_temOrig', '_subMoeda', '_grMoedaSync',
        '_celStake', '_subPL', '_celPL'].map(n => recorteFn(INDEX, n))].join('\n');
  vm.runInContext(dubles + codigo + `
    this.api = { fmtMoedaOrig, moneyOrig, _subMoeda, _grMoedaSync, _celStake, _celPL,
      ver: v => { _grVer = v; }, verAtual: () => _grVer, conta: p => { parceiroSelecionado = p; } };`, ctx);
  return ctx;
}

const g = montarGrade();
const A = g.api;

// ── A. formato ───────────────────────────────────────────────────────────────
eq(A.fmtMoedaOrig(1234.5, 'USD'), 'US$ 1.234,50', 'A: dólar com US$ na frente e milhar');
eq(A.fmtMoedaOrig(1234.5, 'USDT'), '1.234,50 USDT', 'A: USDT com o código depois');
eq(A.fmtMoedaOrig(-3, 'USDT'), '−3,00 USDT', 'A: negativo com minus U+2212');
eq(A.fmtMoedaOrig('25.5', 'USD'), 'US$ 25,50', 'A: número em string');
eq(A.fmtMoedaOrig(10, 'BRL'), '', 'A: real não é moeda original');
eq(A.fmtMoedaOrig(null, 'USD'), '', 'A: valor ausente fica vazio');
// s392: Bet365 da Austrália e da Argentina, e conta em euro. Símbolo antes, como o US$.
eq(A.fmtMoedaOrig(1234.5, 'EUR'), '€ 1.234,50', 'A: euro com € na frente');
eq(A.fmtMoedaOrig(1234.5, 'AUD'), 'A$ 1.234,50', 'A: dólar australiano com A$');
eq(A.fmtMoedaOrig(-250000, 'ARS', true), '−AR$ 250.000,00', 'A: peso com AR$ (nunca o $ solto do dólar cripto)');

// ── B. componente .money ─────────────────────────────────────────────────────
{
  const pos = A.moneyOrig(100.75, 'USDT', true);
  ok(pos.includes('money pos') && pos.includes('>+<') && pos.includes('>USDT<') && pos.includes('100,75'),
     'B: P/L positivo em USDT com cor só no número e sinal neutro: ' + pos);
  ok(pos.includes('<span><span class="money-sign">+</span><span class="money-val">'),
     'B: o sinal do USDT fica colado ao número (span interno, sem o gap do .money): ' + pos);
  const neg = A.moneyOrig(-25, 'USD', true);
  ok(neg.includes('money neg') && neg.includes('−US$'), 'B: P/L negativo em dólar: ' + neg);
  const zero = A.moneyOrig(0, 'USDT', true);
  ok(!/pos|neg/.test(zero) && !zero.includes('+') && !zero.includes('−'), 'B: zero neutro: ' + zero);
  const stake = A.moneyOrig(25, 'USDT');
  ok(!/pos|neg/.test(stake) && !stake.includes('+'), 'B: stake sem cor e sem sinal: ' + stake);
}

// ── C. célula da stake ───────────────────────────────────────────────────────
const conv = { id: 1, stake: '130,00', stake_orig: 25, moeda: 'USDT', cotacao: 5.2, pl: 524.0, pl_orig: 100.75 };
const real = { id: 2, stake: '50,00', pl: 10 };
const poly = { id: 3, stake: '52,00', stake_usd: 10 };
A.ver('BRL');
{
  const c = A._celStake(conv);
  ok(c.includes('data-field="stake"') && c.includes('[R$ 130,00]'), 'C: vendo em R$, a stake é R$ e editável');
  ok(c.includes('>25,00 USDT<'), 'C: vendo em R$, o original aparece embaixo: ' + c);
  ok(A._celStake(real).includes('data-field="stake"') && !A._celStake(real).includes('btbl-stake-usd'),
     'C: linha em real sem sub-linha');
  ok(A._celStake(poly).includes('$ 10,00'), 'C: o USD do Polymarket segue como era');
}
A.ver('orig');
{
  const c = A._celStake(conv);
  ok(c.includes('data-field="stake_orig"') && !c.includes('data-field="stake"'),
     'C: vendo na moeda da conta, edita-se a stake NA MOEDA (s398)');
  ok(c.includes('25,00') && c.includes('>USDT<'), 'C: vendo na moeda da conta, o original é o principal');
  ok(c.includes('>R$ 130,00<'), 'C: e o R$ desce para a sub-linha: ' + c);
  ok(A._celStake(real).includes('data-field="stake"') && A._celStake(real).includes('[R$ 50,00]'),
     'C: linha sem origem segue em R$ e editável');
}

// ── D. célula de P/L ─────────────────────────────────────────────────────────
A.ver('BRL');
ok(A._celPL(conv).startsWith('[PL 524]'), 'D: vendo em R$, o P/L em R$ por cima');
ok(A._celPL(conv).includes('>+100,75 USDT<'), 'D: vendo em R$, o P/L em USDT embaixo, com sinal: ' + A._celPL(conv));
ok(A._celPL({ ...conv, pl: -130, pl_orig: -25 }).includes('>−25,00 USDT<'), 'D: P/L negativo embaixo com minus');
ok(A._celPL({ ...conv, pl: 0, pl_orig: 0 }).includes('>0,00 USDT<'), 'D: P/L zero embaixo sem sinal');
A.ver('orig');
ok(A._celPL(conv).includes('100,75') && A._celPL(conv).includes('USDT'), 'D: vendo na moeda da conta, o pl_orig');
ok(A._celPL(conv).includes('>+R$ 524,00<'), 'D: vendo na moeda da conta, o R$ desce para baixo: ' + A._celPL(conv));
eq(A._celPL({ ...conv, pl_orig: null }), '[—]', 'D: aposta aberta segue o travessão');
eq(A._celPL(real), '[PL 10]', 'D: linha sem origem segue em R$, sem sub-linha');
A.ver('BRL');
eq(A._celPL({ ...conv, pl: null, pl_orig: null }), '[—]', 'D: aposta aberta sem sub-linha');
eq(A._celPL(real), '[PL 10]', 'D: em R$, linha sem origem sem sub-linha');
A.ver('orig');

// ── E. o seletor ─────────────────────────────────────────────────────────────
{
  A.conta({ id: 9, moeda: 'BRL' });
  A.ver('orig');
  A._grMoedaSync();
  ok(g.D['grade-moeda'].hidden, 'E: conta em real esconde o seletor');
  eq(A.verAtual(), 'BRL', 'E: conta em real volta a ver em R$');
  eq(g.D['th-stake'].textContent, 'Stake', 'E: cabeçalho sem moeda em R$');

  A.conta({ id: 7, moeda: 'USD' });
  A._grMoedaSync();
  ok(!g.D['grade-moeda'].hidden, 'E: conta em dólar mostra o seletor');
  eq(g.D['grade-moeda-orig'].textContent, 'USD', 'E: o botão nomeia a moeda da conta');
  A.ver('orig');
  A._grMoedaSync();
  eq(g.D['th-stake'].textContent, 'Stake · USD', 'E: o cabeçalho da stake diz a moeda');
  eq(g.D['th-pl'].textContent, 'P/L · USD', 'E: o cabeçalho do P/L diz a moeda');
  ok(g.botoes[1].classList.contains('on') && !g.botoes[0].classList.contains('on'), 'E: o botão aceso acompanha');

  A.conta(null);
  A._grMoedaSync();
  ok(g.D['grade-moeda'].hidden, 'E: sem conta, sem seletor');
}

// ── F. dashboard ─────────────────────────────────────────────────────────────
{
  const ctx = {};
  vm.createContext(ctx);
  vm.runInContext([recorteFn(APP, 'fmt'), recorteConst(APP, '_MOEDA_ORIG'), recorteFn(APP, 'fmtMoedaOrig')].join('\n') +
    '\nthis.f = fmtMoedaOrig;', ctx);
  for (const [v, m] of [[1234.5, 'USD'], [1234.5, 'USDT'], [-3, 'USDT'], [0.5, 'USD'], [10, 'BRL'], [null, 'USD'], [0, 'USDT'], [1234.5, 'EUR'], [-9, 'AUD'], [250000, 'ARS']]) {
    eq(ctx.f(v, m), A.fmtMoedaOrig(v, m), `F: dashboard e grade escrevem igual (${v} ${m})`);
    eq(ctx.f(v, m, true), A.fmtMoedaOrig(v, m, true), `F: com sinal, dashboard e grade escrevem igual (${v} ${m})`);
  }
  eq(A.fmtMoedaOrig(100.75, 'USDT', true), '+100,75 USDT', 'F: P/L positivo com +');
  eq(A.fmtMoedaOrig(0, 'USDT', true), '0,00 USDT', 'F: P/L zero sem sinal');
  ok(/\$\{fmtR\(stakeCheio\(r\)\)\}\$\{r\.stake_orig!=null&&fmtMoedaOrig\(r\.stake_orig,r\.moeda\)/.test(APOSTAS),
     'F: a Base Completa põe o original sob a stake');
  ok(/fmtPL\(r\.lucro\)\+\(r\.lucro_orig!=null&&fmtMoedaOrig\(r\.lucro_orig,r\.moeda,true\)/.test(APOSTAS),
     'F: a Base Completa põe o P/L original sob o P/L');
}

if (falhas) { console.error(`\n${falhas} falha(s)`); process.exit(1); }
console.log('ok: moeda original na grade e na Base Completa');
