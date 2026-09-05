// Prova por EXECUÇÃO do escopo do calendário da Visão Geral (s319).
//
// O cartão soma o MÊS fechado; os KPIs da página somam o PERÍODO selecionado. Com MTD em
// 05/09 os dois divergiam sem explicação: 12.033,68 no KPI × 11.833 no calendário, porque
// `bilhetes.data` é a data do EVENTO e void da casa / liquidação antecipada resolvem
// bilhete com data futura. Duas decisões nasceram daí, e são as que este teste trava:
//
//   1. o calendário passou a receber as linhas JÁ filtradas por esporte/casa/tipster/
//      operador (antes recebia `DADOS` cru e ignorava os quatro filtros);
//   2. quando o período selecionado não cobre o mês inteiro, o cartão DIZ o que ficou de
//      fora — contagem e P/L, no `fmtPL` do padrão monetário.
//
// Tudo aqui é RECORTADO dos arquivos de produção: `mkCalendarHeatmap` do shared.js, os
// helpers de agregação e o `fmtPL`/`fmt` do app.js, o `filtrarSemData` do filters.js.
// Teste que reimplementa o código sob teste não detecta a mutação que o quebra (s286).
//
// O que este teste NÃO cobre: o CSS (a nota é posicionada por `.cal__bar .nota-escopo`, e
// aqui nada é estilizado — o gap do flex que separava "( −R$ 201,00 )" só aparece no
// navegador); o clique de ‹ › (os handlers vão como STRING para o onclick e aqui nunca
// são avaliados); e o modo público, cujo `fmtPL` é reatribuído no boot do app.js.
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const CR = String.fromCharCode(13), LF = String.fromCharCode(10);
const MENOS = String.fromCharCode(0x2212);
const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const lerJs = p => fs.readFileSync(p, 'utf8').split(CR + LF).join(LF);
const APP = lerJs(process.env.ALVO_APP || path.join(RAIZ, 'app/static/dash/assets/js/app.js'));
const SHARED = lerJs(process.env.ALVO_SHARED || path.join(RAIZ, 'app/static/dash/assets/js/charts/shared.js'));
const FILTERS = lerJs(process.env.ALVO_FILTERS || path.join(RAIZ, 'app/static/dash/assets/js/filters.js'));
const OVERVIEW = lerJs(process.env.ALVO_OVERVIEW || path.join(RAIZ, 'app/static/dash/assets/js/charts/overview.js'));

let falhas = 0;
const ok = (cond, msg) => { if (!cond) { console.error('FALHOU: ' + msg); falhas++; } };

const recorte = (src, ini, fim, nome) => {
  const a = src.indexOf(ini); if (a < 0) throw new Error('nao achei o inicio de ' + nome);
  const b = src.indexOf(fim, a); if (b < 0) throw new Error('nao achei o fim de ' + nome);
  return src.slice(a, b + fim.length);
};
const linha = (src, ini, nome) => {
  const a = src.indexOf(ini); if (a < 0) throw new Error('nao achei a linha de ' + nome);
  const b = src.indexOf(LF, a); if (b < 0) throw new Error('linha sem fim: ' + nome);
  return src.slice(a, b);
};

// ── Código REAL sob teste ────────────────────────────────────────────────────
const FONTE = [
  linha(APP, 'function fmt(v,d=2)', 'fmt'),
  linha(APP, 'function fmtPL(v)', 'fmtPL'),
  linha(APP, 'function fmtOdd(v)', 'fmtOdd'),
  linha(APP, 'function calcTurnover(rows)', 'calcTurnover'),
  linha(APP, 'function wrFrac(', 'wrFrac'),
  linha(APP, 'function wrPctRows(rows)', 'wrPctRows'),
  linha(APP, 'function calcWR(rows)', 'calcWR'),
  linha(APP, 'function calcAvgOdd(rows)', 'calcAvgOdd'),
  recorte(SHARED, 'function mkEmpty(msg){', LF + '}', 'mkEmpty'),
  recorte(SHARED, 'function mkCalendarHeatmap(', LF + '}', 'mkCalendarHeatmap'),
  recorte(FILTERS, 'function filtrarSemData(p){', LF + '}', 'filtrarSemData'),
].join(LF);

const MESES_SRC = "const MESES=['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro'];";
const DATA_JS = lerJs(path.join(RAIZ, 'app/static/dash/assets/js/data.js'));
ok(DATA_JS.includes(MESES_SRC), 'a constante MESES mudou de forma no data.js');

// Ambiente mínimo: só o que o código recortado alcança de fora.
const preludio = `
  ${MESES_SRC}
  const window = { MODO_PUBLICO: null };
  let DADOS = [];
  let _MSS = {};
  const msGet = id => _MSS[id] || new Set();
`;
const fabrica = new Function(preludio + FONTE + `
  ;return { mkCalendarHeatmap, filtrarSemData,
            setDados: d => { DADOS = d; },
            setFiltro: (id, vals) => { _MSS[id] = new Set(vals); } };
`);
const M = fabrica();

// ── Base sintética que EXERCE a regra ────────────────────────────────────────
// Espelha o setembro real do Feca em miniatura: dias dentro do período, uma perdida com
// evento DEPOIS do corte e um void mais tarde no mês. Sem a linha fora do período o
// desempate não decide nada e o teste passaria verde sem provar coisa alguma (s287).
const r = (data, resultado, stake, odd, tipster, lucro) =>
  ({ data, resultado, stake, odd, tipster, esporte: 'Futebol', casa: 'Bet365',
     operador: 'Feca', lucro });
const BASE = [
  r('2026-09-01', 'W', 100, 2.0, 'LBB', 100),
  r('2026-09-03', 'L', 100, 1.9, 'LBB', -100),
  r('2026-09-05', 'W', 100, 3.0, 'Peixe', 200),
  r('2026-09-06', 'L', 201, 4.0, 'F1DP', -201),   // evento FORA do período (a perdida)
  r('2026-09-18', 'V', 500, 1.9, 'DartsVader', 0), // void, também fora — P/L 0, conta 1
  r('2026-08-20', 'W', 100, 2.0, 'LBB', 100),      // outro mês: nunca entra
];
const RANGE_MTD = { from: '2026-09-01', to: '2026-09-05' };

const texto = html => html.replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim();
const nota = html => {
  const i = html.indexOf('nota-escopo');
  return i < 0 ? null : texto(html.slice(i, html.indexOf('</div>', html.indexOf('</span>', i) + 1)));
};

// 1) Período menor que o mês → a nota aparece, com a contagem e o P/L do que ficou fora.
{
  const html = M.mkCalendarHeatmap('2026-09', BASE, { showNav: true, range: RANGE_MTD });
  const n = nota(html);
  ok(n !== null, 'período parcial não gerou a nota de escopo');
  ok(/2 apostas/.test(n || ''), 'a nota não contou as 2 apostas fora do período: ' + n);
  ok((n || '').includes(MENOS + 'R$') && (n || '').includes('201,00'),
     'a nota não trouxe o P/L de fora no fmtPL (menos U+2212, 2 casas): ' + n);
  ok(/fora do período selecionado/.test(n || ''), 'a nota não diz de que recorte fala: ' + n);
  // O hero segue sendo do MÊS: a nota explica a diferença, não a apaga.
  ok(texto(html).includes('5 apostas'), 'o hero deixou de somar o mês inteiro');
}

// 2) Período cobrindo o mês inteiro → nada a avisar.
{
  const html = M.mkCalendarHeatmap('2026-09', BASE, { showNav: true, range: { from: '2026-09-01', to: '2026-09-30' } });
  ok(nota(html) === null, 'nota apareceu com o período cobrindo o mês inteiro');
}

// 3) Sem `range` (o calendário da aba Resultados, que já recebe linhas recortadas por
//    data) → nada a avisar. Sem este caso, a nota vazaria para um cartão onde ela mente.
{
  const html = M.mkCalendarHeatmap('2026-09', BASE, { showNav: true });
  ok(nota(html) === null, 'nota apareceu sem opts.range');
}

// 4) Singular: uma aposta só fora do período não vira "1 apostas".
{
  const html = M.mkCalendarHeatmap('2026-09', BASE, { showNav: true, range: { from: '2026-09-01', to: '2026-09-06' } });
  const n = nota(html) || '';
  ok(/1 aposta[^s]/.test(n + ' '), 'a nota não concorda no singular: ' + n);
}

// 5) Mês selecionado que o filtro esvaziou continua na lista de meses — senão `indexOf`
//    dá −1, as setas ‹ › travam e o cartão fica em branco sem dizer por quê.
{
  const html = M.mkCalendarHeatmap('2026-09', [BASE[5]], { showNav: true, range: RANGE_MTD });
  ok(html.includes('value="2026-09"'), 'o mês selecionado sumiu do seletor quando ficou vazio');
  ok(!/aria-label="Mês anterior" disabled/.test(html),
     'a seta de mês anterior travou num mês vazio');
}

// 6) O `filtrarSemData` REAL respeita tipster e ignora data — é ele que o calendário usa.
{
  M.setDados(BASE);
  M.setFiltro('ti_overview', ['LBB']);
  const rows = M.filtrarSemData('overview');
  ok(rows.length === 3, 'filtrarSemData não recortou por tipster (esperado 3, veio ' + rows.length + ')');
  ok(rows.some(x => x.data === '2026-08-20'), 'filtrarSemData cortou por data — o calendário perderia os outros meses');
}

// 7) Estrutural: a Visão Geral tem de ENTREGAR as linhas filtradas ao calendário. Rodar o
//    `renderOvHeatmap` aqui exigiria o DOM inteiro; o que se trava é a ligação, que é
//    exatamente o que regrediu.
{
  ok(/function _ovCalRows\(\)\{return filtrarSemData\('overview'\);\}/.test(OVERVIEW),
     '_ovCalRows deixou de sair do filtrarSemData');
  ok(/mkCalendarHeatmap\(window\._ovHeatMonth,rows,/.test(OVERVIEW),
     'o calendário da Visão Geral voltou a receber a base crua em vez das linhas filtradas');
  ok(!/mkCalendarHeatmap\(window\._ovHeatMonth,DADOS,/.test(OVERVIEW),
     'o calendário da Visão Geral recebe DADOS de novo');
  ok(/_ovCalMeses\(\)/.test(OVERVIEW) && !/onPrev:"[^"]*DADOS\.map/.test(OVERVIEW),
     'a nav ‹ › voltou a derivar os meses de DADOS, discordando do que o cartão desenha');
}

if (falhas) { console.error(falhas + ' falha(s)'); process.exit(1); }
console.log('calendario_escopo: ok');
