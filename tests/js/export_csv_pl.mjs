// O CSV exportado leva o P/L; o TSV, NUNCA (s303).
//
// Pedido do grupo de testers: *"quando a gente exporta em CSV puxa a coluna de stake, de odd
// mas não puxa a coluna de profit — como às vezes dá meio green/red não tem como calcular na
// mão"*. Meio green/red é HW/HL: o lucro é de meia aposta ((stake/2)×odd + stake/2 − stake),
// e ninguém refaz isso na planilha a partir de stake e odd.
//
// As duas metades desta prova quebram em SILÊNCIO se alguém as desfizer:
//
//   1. o CSV precisa da 11ª coluna, com decimal VÍRGULA e hífen comum. O minus do padrão de
//      tela é U+2212 (−) e o Excel o lê como TEXTO — a coluna apareceria e mesmo assim não
//      somaria, que é exatamente a queixa original;
//   2. o TSV precisa continuar com 10 colunas. Ele é colado direto na planilha do usuário:
//      uma coluna a mais não dá erro, cai em cima do que ele já tem ao lado do Resultado.
//
// O código sob teste é RECORTADO do `index.html` — nunca reescrito aqui (a regra "teste verde
// não é teste que detecta" do CLAUDE.md).
//
// O que este teste NÃO cobre: o download em si (Blob/anchor), a paginação de
// `carregarTodosBilhetes`, e se o `pl` que o backend manda está certo — isso é
// `repository.calcular_pl`, coberto em `tests/test_formulas.py`.
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const CR = String.fromCharCode(13), LF = String.fromCharCode(10);
const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const ALVO = process.env.ALVO_INDEX || path.join(RAIZ, 'app', 'static', 'index.html');
const html = fs.readFileSync(ALVO, 'utf8').split(CR + LF).join(LF);

const corte = (ini) => {
  const a = html.indexOf(ini);
  if (a < 0) throw new Error('não achei: ' + ini);
  const b = html.indexOf(LF + '}' + LF, a);
  if (b < 0) throw new Error('não achei o fim de: ' + ini);
  return html.slice(a, b + 3);
};

const fonte = [
  corte('function _limparOdd'),
  corte('function _linhaExport'),
  corte('function montarTSV'),
  corte('function _plExport'),
  corte('function montarCSV'),
].join(LF);

const { _linhaExport, montarTSV, montarCSV } = new Function(
  fonte + LF + 'return { _linhaExport, montarTSV, montarCSV };'
)();

let falhas = 0;
const ok = (cond, msg) => { if (!cond) { falhas++; console.error('FALHOU: ' + msg); } };

const bilhete = (o) => Object.assign({
  data: '31/08/2026', esporte: 'Futebol', tipster: 'LBB', casa: 'Bet365',
  parceiro: 'Conta 1', aposta: 'Handicap Asiático', descricao: 'Norwich x Burnley',
  stake: '100,00', odd: '2,50', resultado: 'W', pl: 150,
}, o);

// stake 100 @ 2,50 — os cinco resultados oficiais, com o P/L que o backend manda.
const linhas = [
  bilhete({ resultado: 'W', pl: 150 }),
  bilhete({ resultado: 'HW', pl: 75 }),     // meio green: (50×2,5)+50−100
  bilhete({ resultado: 'HL', pl: -50 }),    // meio red: 50−100
  bilhete({ resultado: 'L', pl: -100 }),
  bilhete({ resultado: 'V', pl: 0 }),
  bilhete({ resultado: '', pl: null }),     // aberta
  bilhete({ resultado: 'W', odd: '', pl: null }), // vitória sem odd → não calculável
];

const csv = montarCSV(linhas).split(CR + LF);
const col = (i) => csv[i].split(';');

// 1. a coluna existe e é a 11ª
ok(csv.every(l => l.split(';').length === 11), 'CSV não tem 11 colunas em todas as linhas');

// 2. meio green e meio red — o caso que motivou o pedido
ok(col(1)[10] === '75,00', 'HW: esperado 75,00 na 11ª coluna, veio ' + col(1)[10]);
ok(col(2)[10] === '-50,00', 'HL: esperado -50,00 na 11ª coluna, veio ' + col(2)[10]);

// 3. formato de planilha: decimal vírgula e hífen COMUM (o U+2212 vira texto no Excel)
ok(!montarCSV(linhas).includes('−'), 'o CSV levou o minus U+2212 — Excel lê como texto');
ok(/^-?\d+,\d{2}$/.test(col(3)[10]), 'L: P/L fora do formato decimal-vírgula: ' + col(3)[10]);
ok(col(4)[10] === '0,00', 'V: zero tem de sair 0,00 (e não vazio), veio "' + col(4)[10] + '"');

// 4. sem P/L calculável → célula VAZIA, nunca 0 (zero seria "empatou", mentira diferente)
ok(col(5)[10] === '', 'aposta aberta: 11ª coluna deveria ser vazia, veio "' + col(5)[10] + '"');
ok(col(6)[10] === '', 'vitória sem odd: 11ª coluna deveria ser vazia, veio "' + col(6)[10] + '"');

// 5. o escape do ';' continua valendo com a coluna nova
const comPontoEVirgula = montarCSV([bilhete({ descricao: 'Mais/Menos; 2,5', pl: 1234.5 })]);
ok(comPontoEVirgula.includes('"Mais/Menos; 2,5"'), 'descrição com ";" não foi escapada');
ok(comPontoEVirgula.endsWith(';1234,50'), 'P/L não fechou a linha: ' + comPontoEVirgula);

// 6. o TSV NÃO mudou — 10 colunas, sempre
const tsv = montarTSV(linhas).split(LF);
ok(tsv.every(l => l.split('\t').length === 10),
   'o TSV saiu com ' + [...new Set(tsv.map(l => l.split('\t').length))] + ' colunas — ele é colado na planilha e tem de ficar em 10');
ok(_linhaExport(linhas[1]).length === 10, '_linhaExport deixou de ser as 10 colunas do MASTER_OUTPUT');

if (falhas) { console.error(falhas + ' falha(s)'); process.exit(1); }
console.log('export CSV com P/L: OK (11 colunas no CSV, 10 no TSV)');
