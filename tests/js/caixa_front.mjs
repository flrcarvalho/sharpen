// Prova por EXECUÇÃO da camada de tela da Caixa (s314).
//
// Duas coisas moram só no front e ninguém mais confere:
//
//   1. A DATA vai e volta. A caixa imprime dd/mm/aa na leitura (cabe na coluna de
//      300px) e dd/mm/aaaa no campo. O primeiro lançamento no navegador falhou aqui:
//      o campo nascia com o ano curto e o parser exigia 4 dígitos, então a tela
//      recusava, com "Data inválida", um valor escrito por ela mesma.
//   2. A MÁSCARA do saldo. É a 3ª variação documentada do `.money` (UI_REFERENCE
//      §5.1): 2 casas, minus U+2212 e — o que mais importa — SEM cor, porque
//      verde/vermelho é semântica de resultado e saque não é prejuízo.
//
// `fmtSaldo`, `_cxDataBR`, `_cxDataBR4` e `_cxIso` são RECORTADOS do `index.html` de
// produção, nunca reescritos aqui: teste que reimplementa o código não detecta a
// mutação que o quebra.
//
// O que este teste NÃO cobre: o render (posição da coluna, contraste e a Escada de
// Tinta ficam para o headless), o SharpenCal (DOM real) e a rede.
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const CR = String.fromCharCode(13), LF = String.fromCharCode(10);
const MENOS = String.fromCharCode(0x2212);
const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const HTML = fs.readFileSync(process.env.ALVO_INDEX || path.join(RAIZ, 'app/static/index.html'),
                             'utf8').split(CR + LF).join(LF);

let falhas = 0;
const ok = (cond, msg) => { if (!cond) { console.error('FALHOU: ' + msg); falhas++; } };
const recorte = (ini, fim, nome) => {
  const a = HTML.indexOf(ini); if (a < 0) throw new Error('não achei o início de ' + nome);
  const b = HTML.indexOf(fim, a); if (b < 0) throw new Error('não achei o fim de ' + nome);
  return HTML.slice(a, b + fim.length);
};

const fmtSaldo   = eval('(' + recorte('function fmtSaldo(n, sinal) {', LF + '}', 'fmtSaldo') + ')');
const _cxDataBR  = eval('(' + recorte('function _cxDataBR(iso) {', LF + '}', '_cxDataBR') + ')');
const _cxDataBR4 = eval('(' + recorte('function _cxDataBR4(iso) {', LF + '}', '_cxDataBR4') + ')');
const _cxIso     = eval('(' + recorte('function _cxIso(txt) {', LF + '}', '_cxIso') + ')');

// ── A. A data volta inteira ─────────────────────────────────────────────────
ok(_cxDataBR4('2026-09-02') === '02/09/2026', 'campo imprime dd/mm/aaaa');
ok(_cxDataBR('2026-09-02') === '02/09/26', 'leitura imprime dd/mm/aa');
ok(_cxIso(_cxDataBR4('2026-09-02')) === '2026-09-02', 'ida e volta pelo campo');
ok(_cxIso(_cxDataBR('2026-09-02')) === '2026-09-02', 'ida e volta pela leitura (ano curto)');
ok(_cxIso('2026-09-02') === '2026-09-02', 'ISO passa direto');
ok(_cxIso('2/9/2026') === '2026-09-02', 'dia e mês sem zero à esquerda');
ok(_cxIso('') === '' && _cxIso('amanhã') === '' && _cxIso('31/2026') === '',
   'lixo não vira data');
ok(_cxDataBR('') === '—' && _cxDataBR(null) === '—', 'sem data, travessão');

// A ida e volta vale para o ANO INTEIRO — o bug original só aparecia em datas reais.
for (let d = 0; d < 366; d++) {
  const iso = new Date(Date.UTC(2026, 0, 1 + d)).toISOString().slice(0, 10);
  if (_cxIso(_cxDataBR4(iso)) !== iso) { ok(false, 'ida e volta quebrou em ' + iso); break; }
  if (_cxIso(_cxDataBR(iso)) !== iso) { ok(false, 'ida e volta curta quebrou em ' + iso); break; }
}

// ── B. A máscara do saldo ───────────────────────────────────────────────────
const val = h => (h.match(/money-val">([^<]*)</) || [])[1];
const sig = h => (h.match(/money-sign">([^<]*)</) || [])[1];

ok(val(fmtSaldo(1234.5)) === '1.234,50', 'pt-BR com 2 casas e milhar');
ok(sig(fmtSaldo(1234.5)) === 'R$', 'sem sinal quando não é movimento');
ok(sig(fmtSaldo(1234.5, true)) === '+R$', 'movimento positivo leva +');
ok(sig(fmtSaldo(-800, true)) === MENOS + 'R$', 'negativo usa o minus U+2212, não hífen');
ok(sig(fmtSaldo(-800)) === MENOS + 'R$', 'saldo negativo mantém o sinal mesmo sem pedir');
ok(val(fmtSaldo(-800)) === '800,00', 'o sinal fica no .money-sign, o número é absoluto');
ok(sig(fmtSaldo(0, true)) === 'R$' && val(fmtSaldo(0, true)) === '0,00',
   'zero é neutro: sem + e sem −');
ok(!/money (pos|neg)/.test(fmtSaldo(-800, true)) && !/money (pos|neg)/.test(fmtSaldo(999, true)),
   'saldo NUNCA é colorido — verde/vermelho é semântica de resultado');
ok(!/\d+(k|K|M|mil)/.test(fmtSaldo(1234567)), 'milhar nunca abreviado');
ok(val(fmtSaldo(1234567.89)) === '1.234.567,89', 'dois grupos de milhar');
ok(val(fmtSaldo('')) === '0,00' && val(fmtSaldo(undefined)) === '0,00', 'vazio não vira NaN');

// A linha "Resultado" é a única colorida da caixa, e ela usa o fmtPL — não o fmtSaldo.
ok(/Resultado[^;]*fmtPL\(d\.pl\)/.test(HTML.replace(/\n/g, ' ')),
   'a linha Resultado tem de usar fmtPL (é P/L de verdade)');

if (falhas) { console.error(falhas + ' falha(s)'); process.exit(1); }
console.log('caixa_front.mjs OK');
