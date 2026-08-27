// Prova por EXECUÇÃO da ordenação das tabelas do dashboard (s300).
//
// O sintoma que abriu o caso: em Fornecedores & Parceiros nenhuma coluna ordenava certo —
// nem data, nem Turnover, nem Profit, nem ROI. Três causas independentes, todas silenciosas
// (a tabela reordena, só que errado — nenhum erro no console):
//
//   1. O menos do padrão monetário é U+2212 (−), não hífen. `parseFloat` devolvia NaN → 0,
//      e TODO P/L e ROI negativo empilhava num bloco no meio da tabela.
//   2. `fmtR` imprime inteiro sem decimal ("R$ 5.180"); a regra antiga só tirava o ponto de
//      milhar quando vinha vírgula depois. "5.180" virava 5,18 e a conta de R$ 80 subia ao
//      topo do Turnover.
//   3. As colunas de data saem em dd/mm/aa e ordenavam como texto — ou seja, pelo DIA DO MÊS.
//
// `parseNum`, `sortTable` e o construtor de linhas das Contas Individuais são RECORTADOS dos
// arquivos de produção — nunca reescritos aqui: teste que reimplementa o código não detecta
// a mutação que o quebra.
//
// O que este teste NÃO cobre: o clique real (o DOM é dublado, então `makeSortable` e o
// `onclick` do <th> não são exercidos), o resize de coluna, a seta de ordenação no CSS, e
// o `localeCompare` sob outro ICU que não o do node local.
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const CR = String.fromCharCode(13), LF = String.fromCharCode(10);
const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const lerJs = p => fs.readFileSync(p, 'utf8').split(CR + LF).join(LF);
const APP = lerJs(process.env.ALVO_APP || path.join(RAIZ, 'app/static/dash/assets/js/app.js'));
const GESTAO = lerJs(process.env.ALVO_GESTAO || path.join(RAIZ, 'app/static/dash/assets/js/charts/gestao.js'));

let falhas = 0;
const ok = (cond, msg) => { if (!cond) { console.error('FALHOU: ' + msg); falhas++; } };

const recorte = (src, ini, fim, nome) => {
  const a = src.indexOf(ini); if (a < 0) throw new Error('não achei o início de ' + nome);
  const b = src.indexOf(fim, a); if (b < 0) throw new Error('não achei o fim de ' + nome);
  return src.slice(a, b + fim.length);
};

// ── A. parseNum, recortado do app.js ────────────────────────────────────────
const srcParseNum = recorte(APP, 'function parseNum(raw){', LF + '}', 'parseNum');
const parseNum = eval('(' + srcParseNum + ')');

const MENOS = String.fromCharCode(0x2212), TRACO = String.fromCharCode(0x2014);
[
  // [ o que a tela imprime , o número que ele É , por que importa ]
  ['R$5.180',            5180,     'fmtR: milhar sem decimal (bug 2)'],
  ['R$80',               80,       'fmtR: sem milhar — não pode virar maior que 5.180'],
  ['R$52.519',           52519,    'fmtR: milhar grande'],
  ['R$1.234.567',        1234567,  'fmtR: dois grupos de milhar'],
  ['R$ 5.180',           5180,     'com espaço depois do R$'],
  ['1.234u',             1234,     'modo público: sufixo u'],
  ['+R$9.589,60',        9589.60,  'fmtPL positivo'],
  [MENOS + 'R$1.234,56', -1234.56, 'fmtPL NEGATIVO com U+2212 (bug 1)'],
  ['+185,1%',            185.1,    'fmtPct positivo'],
  [MENOS + '12,3%',      -12.3,    'fmtPct NEGATIVO com U+2212 (bug 1)'],
  ['+0,0%',              0,        'zero neutro'],
  ['2,35',               2.35,     'odd: vírgula decimal'],
  ['3d',                 3,        'coluna Período'],
  ['40d',                40,       'coluna Período de dois dígitos'],
  [TRACO,                0,        'célula vazia (em-dash)'],
  ['',                   0,        'célula em branco'],
].forEach(([raw, esp, motivo]) => {
  const got = parseNum(raw);
  ok(Math.abs(got - esp) < 1e-9, 'parseNum(' + JSON.stringify(raw) + ') = ' + got + ', esperado ' + esp + ' — ' + motivo);
});

// ── B. sortTable, recortado do app.js, contra um DOM dublado ────────────────
// Só o que o sort usa: cells[], dataset.sort, textContent, appendChild (que MOVE a linha,
// como no DOM real), querySelector('.total-row') e os <th>.
const srcSortTable = recorte(APP, 'function sortTable(tableId,colIdx,numeric){', LF + '}', 'sortTable');

function montarTabela(linhas, nCols) {
  const mkTr = (celulas, total) => ({
    total: !!total,
    cells: celulas.map(c => (typeof c === 'string'
      ? { textContent: c, dataset: {} }
      : { textContent: c.txt, dataset: { sort: c.sort } })),
  });
  const trs = linhas.map(l => mkTr(l.cel, l.total));
  const tbody = {
    filhos: trs,
    querySelectorAll: sel => (sel === 'tr:not(.total-row)' ? tbody.filhos.filter(t => !t.total) : []),
    querySelector: sel => (sel === '.total-row' ? tbody.filhos.find(t => t.total) || null : null),
    appendChild: tr => { tbody.filhos = tbody.filhos.filter(t => t !== tr); tbody.filhos.push(tr); },
  };
  const ths = Array.from({ length: nCols }, () => {
    const th = { classes: new Set(), querySelector: () => ({}), appendChild: () => {} };
    th.classList = { remove: (...cs) => cs.forEach(c => th.classes.delete(c)), add: c => th.classes.add(c) };
    return th;
  });
  return {
    querySelector: sel => (sel === 'tbody' ? tbody : null),
    querySelectorAll: sel => (sel === 'th' ? ths : []),
    _tbody: tbody, _ths: ths,
  };
}

function rodarSort(linhas, nCols, colIdx, numeric, vezes = 1) {
  const tabela = montarTabela(linhas, nCols);
  const doc = { getElementById: () => tabela, createElement: () => ({ classList: {} }) };
  const fn = new Function('sortState', 'parseNum', 'document',
    srcSortTable + LF + 'return sortTable;')({}, parseNum, doc);
  for (let i = 0; i < vezes; i++) fn('t', colIdx, numeric);
  return { ordem: tabela._tbody.filhos.map(tr => tr.cells[colIdx].textContent), ths: tabela._ths };
}

const cel = arr => arr.map(v => ({ cel: [v] }));

// Turnover (numérica) — asc; o R$ 80 tem de ficar embaixo, não no topo
ok(rodarSort(cel(['R$80', 'R$1.242', 'R$5.180', 'R$52.519', 'R$44.940']), 1, 0, true).ordem
  .join('|') === 'R$80|R$1.242|R$5.180|R$44.940|R$52.519', 'Turnover asc');

// Profit (numérica) — desc (2º clique): negativo vai para o FIM, e o mais negativo por último
ok(rodarSort(cel(['+R$9.589,60', MENOS + 'R$2.100,00', '+R$65,60', MENOS + 'R$15.000,00', '+R$226,20']), 1, 0, true, 2).ordem
  .join('|') === ['+R$9.589,60', '+R$226,20', '+R$65,60', MENOS + 'R$2.100,00', MENOS + 'R$15.000,00'].join('|'), 'Profit desc');

// ROI (numérica) — asc: os negativos primeiro, na ordem certa entre si
ok(rodarSort(cel(['+185,1%', MENOS + '12,3%', '+3,1%', MENOS + '99,9%', '+55,3%']), 1, 0, true).ordem
  .join('|') === [MENOS + '99,9%', MENOS + '12,3%', '+3,1%', '+55,3%', '+185,1%'].join('|'), 'ROI asc');

// Data (texto + data-sort ISO) — o dia do mês NÃO pode mandar
const datas = [['24/05/26', '2026-05-24'], ['14/01/26', '2026-01-14'], ['09/08/26', '2026-08-09'],
               ['10/05/26', '2026-05-10'], ['31/12/25', '2025-12-31']];
ok(rodarSort(datas.map(([txt, sort]) => ({ cel: [{ txt, sort }] })), 1, 0, false).ordem
  .join('|') === '31/12/25|14/01/26|10/05/26|24/05/26|09/08/26', 'Data asc pelo data-sort ISO');

// Texto — a caixa não pode partir a lista em dois blocos, e dígito ordena natural
ok(rodarSort(cel(['ZuG1212', 'maysacarol01', 'MichelCleiton', 'conta10', 'conta2', 'Andson1994']), 1, 0, false).ordem
  .join('|') === 'Andson1994|conta2|conta10|maysacarol01|MichelCleiton|ZuG1212', 'Conta asc');

// A linha de Total nunca sai do fim
const comTotal = [{ cel: ['R$5.180'] }, { cel: ['R$80'] }, { cel: ['Total'], total: true }, { cel: ['R$52.519'] }];
ok(rodarSort(comTotal, 1, 0, true).ordem.slice(-1)[0] === 'Total', 'total-row fica no fim');

// A seta vai para a coluna clicada, e só nela
const th = rodarSort([{ cel: ['a', 'R$80', 'x'] }, { cel: ['b', 'R$5.180', 'y'] }], 3, 1, true).ths;
ok(th[1].classes.has('sort-asc') && !th[0].classes.has('sort-asc') && !th[2].classes.has('sort-asc'),
  'a classe sort-asc marca só a coluna clicada');

// ── C. as linhas das Contas Individuais, recortadas do gestao.js ────────────
// As duas datas e a Casa precisam sair com data-sort — sem ele o sort cai no textContent,
// que é dd/mm/aa (dia do mês) na data e leva a letra do chip de inicial na Casa.
const srcAccRows = recorte(GESTAO, 'const accRows=Object.values(map)', ".join('');", 'accRows');
const construir = new Function('map', 'esc', 'casaCell', 'fmtR', 'fmtPL', 'fmtPct',
  srcAccRows + LF + 'return accRows;');
const html = construir(
  { k1: { conta: 'ZuG1212', forn: 'P2Pro', casa: 'Superbet', n: 199, s: 52519, l: 29053.5,
          datas: ['2026-03-21', '2026-04-22', '2026-01-14'] } },
  String, c => '<span class="house-chip">S</span>' + c, v => 'R$' + v, v => 'R$' + v, v => v + '%');
ok(html.includes('data-sort="2026-01-14"'), '1ª Aposta leva o data-sort da data MAIS ANTIGA');
ok(html.includes('data-sort="2026-04-22"'), 'Última leva o data-sort da data MAIS RECENTE');
ok(html.includes('data-sort="Superbet"'), 'Casa leva data-sort com o nome limpo, sem o chip');
ok(html.includes('>14/01/26<') && html.includes('>22/04/26<'), 'a tela segue mostrando dd/mm/aa');

// As colunas numéricas declaradas no makeSortable têm de bater com as colunas de número
const cols = GESTAO.match(/makeSortable\('tblParc',\[([^\]]*)\]\)/);
ok(cols && cols[1] === '3,4,5,6,9',
  'tblParc: numéricas = Bets(3) Turnover(4) Profit(5) ROI(6) Período(9); as datas ordenam por data-sort');

console.log(falhas ? LF + falhas + ' falha(s)' : 'sort_tabelas: tudo ok');
process.exit(falhas ? 1 : 0);
