// Caixa Inteligente na moeda da conta (s391) — o lado da tela.
//
// Prova, executando o código RECORTADO do `index.html`:
// A. `fmtSaldo` sem moeda (ou BRL) sai EXATAMENTE como antes ("R$" na frente);
// B. com USD/USDT sai no formato da grade, com o sinal colado e sem cor;
// C. `_cxTxt` (texto corrido) idem;
// D. `_cxBrl`: conta em R$ soma o próprio valor; em USD/USDT soma o convertido (`*_brl`);
//    sem cotação devolve null (a conta fica FORA da soma, nunca somada como real);
// E. `_cxSigla` dá o rótulo do campo ("Valor (USDT)");
// F. `_cxHintMoeda` diz na ativação em que moeda a conta está (s392).
//
// O que NÃO está coberto: a montagem das telas (renderCaixa, painel) e o visual — medidos
// no navegador.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import vm from 'node:vm';

const AQUI = dirname(fileURLToPath(import.meta.url));
const RAIZ = join(AQUI, '..', '..');
const INDEX = readFileSync(process.env.ALVO_INDEX || join(RAIZ, 'app', 'static', 'index.html'), 'utf8').replace(/\r\n/g, '\n');

let falhas = 0;
const ok = (c, m) => { if (!c) { console.error('  ✗ ' + m); falhas++; } };
const eq = (a, b, m) => ok(a === b, m + ', veio ' + JSON.stringify(a));

const fn = (nome) => {
  const r = INDEX.match(new RegExp('^function ' + nome + '\\([^)]*\\) \\{[\\s\\S]*?^\\}', 'm'));
  if (!r) throw new Error('não achei ' + nome);
  return r[0];
};
const cst = (nome) => {
  const r = INDEX.match(new RegExp('^const ' + nome + '\\s*=.*;$', 'm'));
  if (!r) throw new Error('não achei ' + nome);
  return r[0];
};

const ctx = {};
vm.createContext(ctx);
vm.runInContext([cst('_MOEDA_ORIG'), fn('_num2BR'), fn('fmtMoedaOrig'), fn('fmtSaldo'), fn('_cxSigla'), fn('_cxHintMoeda'), fn('_cxTxt'), fn('_cxBrl')].join('\n')
  + '\nthis.api = { fmtSaldo, _cxTxt, _cxBrl, _cxSigla, _cxHintMoeda };', ctx);
const A = ctx.api;
const txt = (h) => h.replace(/<[^>]+>/g, '');

// A. BRL inalterado
eq(A.fmtSaldo(1234.5), '<span class="money"><span class="money-sign">R$</span><span class="money-val">1.234,50</span></span>', 'A: sem moeda, o HTML de sempre');
eq(A.fmtSaldo(-10, true, 'BRL'), '<span class="money"><span class="money-sign">−R$</span><span class="money-val">10,00</span></span>', 'A: BRL igual ao de sempre');
eq(A.fmtSaldo(10, true), '<span class="money"><span class="money-sign">+R$</span><span class="money-val">10,00</span></span>', 'A: sinal de movimento em R$');

// B. USD/USDT
eq(txt(A.fmtSaldo(1234.5, false, 'USDT')), '1.234,50USDT', 'B: USDT com o código depois');
ok(A.fmtSaldo(-25, true, 'USDT').includes('<span><span class="money-sign">−</span><span class="money-val">25,00</span></span>'), 'B: sinal colado ao número em USDT');
eq(txt(A.fmtSaldo(25, true, 'USD')), '+US$25,00', 'B: dólar com US$ e sinal');
ok(!/pos|neg/.test(A.fmtSaldo(-25, true, 'USDT')), 'B: saldo sem cor');

// C. texto corrido
eq(A._cxTxt(-3), '−R$ 3,00', 'C: R$ como antes');
eq(A._cxTxt(-3, 'USDT'), '−3,00 USDT', 'C: USDT');
eq(A._cxTxt(1200, 'USD'), 'US$ 1.200,00', 'C: dólar com milhar');

// D. soma em reais
eq(A._cxBrl({ disponivel: 50 }, 'disponivel'), 50, 'D: conta sem moeda soma o próprio valor');
eq(A._cxBrl({ moeda: 'BRL', disponivel: 50 }, 'disponivel'), 50, 'D: conta BRL soma o próprio valor');
eq(A._cxBrl({ moeda: 'USDT', disponivel: 100, disponivel_brl: 540 }, 'disponivel'), 540, 'D: USDT soma o convertido');
eq(A._cxBrl({ moeda: 'USDT', disponivel: 100, disponivel_brl: null }, 'disponivel'), null, 'D: sem cotação fica fora da soma');

// E. rótulo
eq(A._cxSigla('USDT'), 'USDT', 'E: USDT'); eq(A._cxSigla('USD'), 'US$', 'E: USD'); eq(A._cxSigla('BRL'), 'R$', 'E: BRL'); eq(A._cxSigla(null), 'R$', 'E: sem moeda');

// F. a ativação diz a moeda da conta (s392): em R$ aponta onde trocar, fora confirma
ok(txt(A._cxHintMoeda('BRL')).includes('Conta em R$') && A._cxHintMoeda('BRL').includes('edição da conta'), 'F: conta em R$ aponta a edição da conta');
ok(txt(A._cxHintMoeda(null)).includes('Conta em R$'), 'F: sem moeda é R$');
ok(txt(A._cxHintMoeda('AUD')).includes('Conta em A$') && !A._cxHintMoeda('AUD').includes('edição da conta'), 'F: conta em AUD confirma A$ e não manda trocar');

if (falhas) { console.error(`\n${falhas} falha(s)`); process.exit(1); }
console.log('ok: caixa na moeda da conta (tela)');
