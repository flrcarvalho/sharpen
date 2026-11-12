// s450: casa com Ficha recusa print e PDF, mas a PLANILHA (.csv/.xls) continua pela caixa
// (pedido do Feca, 12/11/2026: "a planilha NÃO entra no bloqueio"). O servidor já aceita.
//
// O código sob teste é RECORTADO do `index.html`, nunca reescrito aqui: `aplicarBloqueioPrint`,
// `ehPlanilha`, `separarPelaFicha` e `receberArquivos`. O ambiente (DOM mínimo, `setStatus`,
// `adicionarArquivos`) é dublado e não é o código sob teste.
//
// O que NÃO cobre: o arrasto e o seletor de arquivo de verdade (medidos em headless), o
// desenho, e os ouvintes de evento (a presença deles é conferida no pytest irmão,
// `tests/test_planilha_na_ficha.py`).
import { readFileSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import vm from 'vm';

const RAIZ = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const INDEX = readFileSync(process.env.ALVO_INDEX || join(RAIZ, 'app', 'static', 'index.html'), 'utf8')
  .replace(/\r\n/g, '\n');

const corte = (ini, fim) => {
  const a = INDEX.indexOf(ini); if (a < 0) throw new Error('não achei: ' + ini);
  const b = INDEX.indexOf(fim, a); if (b < 0) throw new Error('não achei o fim de: ' + ini);
  return INDEX.slice(a, b + fim.length);
};

const src = [
  corte("const ACCEPT_PLANILHA = ", ';\n'),
  corte('function aplicarBloqueioPrint(casa) {', '\n}\n'),
  corte('function ehPlanilha(f) {', '}\n'),
  corte('function separarPelaFicha(files) {', '\n}\n'),
  corte('function receberArquivos(files) {', '\n}\n'),
].join('\n');

const ACCEPT_ORIG = 'image/*,application/pdf,.csv,text/csv,.xls,.xlsx';
const el = (txt) => ({ dataset: {}, textContent: txt, innerHTML: txt });
const ctx = {
  CASAS_FICHA: new Set(['Thunderpick']), status: [], adicionados: [],
  MSG_PRINT_BLOQUEADO: 'Esta casa é extraída pela extensão SharpenUp. Abra a aba da casa e capture por ela.',
  parceiroSelecionado: null,
};
const h = el('arraste, cole (Ctrl+V) ou clique · prints, .csv e .xls');
const hint = el('Solte aqui · <b>Escolher arquivo</b>');
const classes = new Set();
const dz = { classList: { toggle: (c, on) => (on ? classes.add(c) : classes.delete(c)) },
  querySelector: (s) => (s === '.capbox__hint' ? hint : h) };
const fi = { dataset: {}, accept: ACCEPT_ORIG };
ctx.document = { getElementById: (id) => (id === 'drop-zone' ? dz : id === 'file-input' ? fi : null) };
ctx.esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;');
ctx.temFicha = (c) => ctx.CASAS_FICHA.has(c);
ctx.printBloqueado = () => !!(ctx.parceiroSelecionado && ctx.temFicha(ctx.parceiroSelecionado.casa));
ctx.setStatus = (m, t) => ctx.status.push([m, t]);
ctx.adicionarArquivos = (fs) => ctx.adicionados.push(fs.map((f) => f.name));
vm.createContext(ctx);
vm.runInContext(src + '\nthis.aplicarBloqueioPrint = aplicarBloqueioPrint; this.receberArquivos = receberArquivos;'
  + ' this.ACCEPT_PLANILHA = ACCEPT_PLANILHA;', ctx);

let falhas = 0;
const ok = (cond, msg) => { if (!cond) { falhas++; console.log('FALHOU: ' + msg); } else console.log('ok: ' + msg); };
const arq = (name, type) => ({ name, type });
const LOTE = [arq('a.png', 'image/png'), arq('extrato.pdf', 'application/pdf'), arq('base.csv', 'text/csv'),
  arq('base.xls', 'application/vnd.ms-excel'), arq('base.XLSX', ''), arq('dados.csv', '')];

// 1. Casa com Ficha: a caixa trava o print e oferece só planilha no seletor.
ctx.parceiroSelecionado = { casa: 'Thunderpick' };
ctx.aplicarBloqueioPrint('Thunderpick');
ok(classes.has('is-bloqueada'), 'a caixa fica marcada como travada');
ok(fi.accept === ctx.ACCEPT_PLANILHA && /\.csv/.test(fi.accept) && /\.xls/.test(fi.accept)
  && !/image|pdf/.test(fi.accept), 'o seletor só oferece .csv e .xls');
ok(hint.innerHTML.includes(ctx.MSG_PRINT_BLOQUEADO) && /Planilha \.csv ou \.xls/.test(hint.innerHTML),
  'a caixa diz a frase e que a planilha continua');

// 2. Casa com Ficha: a planilha entra, print e PDF são recusados com a frase.
ctx.receberArquivos(LOTE);
ok(JSON.stringify(ctx.adicionados) === JSON.stringify([['base.csv', 'base.xls', 'base.XLSX', 'dados.csv']]),
  'só a planilha (csv, xls, xlsx) entra: ' + JSON.stringify(ctx.adicionados));
ok(ctx.status.length === 1 && ctx.status[0][0] === ctx.MSG_PRINT_BLOQUEADO && ctx.status[0][1] === 'warn',
  'print e PDF recusados com a frase do servidor');

// 3. Casa com Ficha, só planilha: entra sem aviso nenhum.
ctx.status.length = 0; ctx.adicionados.length = 0;
ctx.receberArquivos([arq('base.csv', 'text/csv')]);
ok(ctx.adicionados.length === 1 && ctx.status.length === 0, 'planilha sozinha entra sem aviso');

// 4. Casa com Ficha, só print: nada entra, a frase aparece.
ctx.status.length = 0; ctx.adicionados.length = 0;
ctx.receberArquivos([arq('a.png', 'image/png')]);
ok(ctx.adicionados.length === 0 && ctx.status.length === 1, 'print sozinho não entra');

// 5. Casa sem Ficha: tudo entra e a caixa volta ao original.
ctx.parceiroSelecionado = { casa: 'Bet365' };
ctx.aplicarBloqueioPrint('Bet365');
ok(!classes.has('is-bloqueada') && fi.accept === ACCEPT_ORIG, 'casa sem Ficha: caixa e seletor originais');
ok(h.textContent === h.dataset.orig && hint.innerHTML === hint.dataset.orig, 'casa sem Ficha: texto original');
ctx.status.length = 0; ctx.adicionados.length = 0;
ctx.receberArquivos(LOTE);
ok(ctx.adicionados.length === 1 && ctx.adicionados[0].length === LOTE.length && ctx.status.length === 0,
  'casa sem Ficha: o lote inteiro entra');

if (falhas) { console.log(falhas + ' falha(s)'); process.exit(1); }
console.log('tudo verde');
