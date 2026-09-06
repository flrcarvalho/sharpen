// Prova por EXECUÇÃO de que mexer no multiselect invalida o recorte cacheado (s322).
//
// O sintoma que este teste existe para impedir: o Feca selecionou `Tipster: Fatuch` na
// Base Completa, o chip "TIPSTER Fatuch" apareceu em Filtros ativos, o contador seguiu
// dizendo "336 de 336" e a tabela continuou mostrando MarcoF1, LBB e F1DP. Nenhum erro,
// nenhum aviso — o filtro simplesmente não filtrava.
//
// A causa é de forma, não de regra: o `_filterCache` é indexado por página, mas as
// entradas dele (o `gfs` do período e os Sets do `MSS`) mudam por fora. Até a s317 o
// único caminho de volta era o `renderPage`, que zera o cache na primeira linha; a Base
// Completa passou a repintar só a si mesma (o `cb` dos multiselects) e `applyMS →
// renderApostas` passou a ler o recorte anterior à seleção.
//
// Tudo aqui é RECORTADO do `filters.js` de produção — o cache, o `filtrarPagina`, a
// store do multiselect e o `msToggle`. Teste que reimplementa o código sob teste não
// detecta a mutação que o quebra (s286).
//
// O que este teste NÃO cobre: o DOM (nada é renderizado — `toggleMS`, `applyMS` e o
// `refreshMS` pintam checkmarks e não entram aqui), o debounce do `_renderPageDebounced`
// e a decisão de QUEM repinta (o `cb`), que é do arquivo da tela.
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const CR = String.fromCharCode(13), LF = String.fromCharCode(10);
const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const lerJs = p => fs.readFileSync(p, 'utf8').split(CR + LF).join(LF);
const FILTERS = lerJs(process.env.ALVO_FILTERS
  || path.join(RAIZ, 'app/static/dash/assets/js/filters.js'));

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

// ── Sandbox: só código de produção. `DADOS` entra por parâmetro (é global no app). ──
const fonte = [
  linha(FILTERS, 'const FS={};', 'FS'),
  linha(FILTERS, 'function gfs(p){', 'gfs'),
  linha(FILTERS, 'let _filterCache={};', '_filterCache'),
  linha(FILTERS, 'function _ymd(d){', '_ymd'),
  recorte(FILTERS, 'function filtrarPagina(p){', LF + '}', 'filtrarPagina'),
  linha(FILTERS, 'const MSS={};', 'MSS'),
  linha(FILTERS, 'function msGet(', 'msGet'),
  linha(FILTERS, 'function msInit(', 'msInit'),
  linha(FILTERS, 'function msToggle(', 'msToggle'),
].join(LF + LF) + LF
  + 'return {filtrarPagina,msInit,msToggle,msGet,cache:()=>_filterCache};';

// ── Base sintética: dois tipsters, para a seleção ter o que DEIXAR de fora ─────
// Com um tipster só, filtrar não mudaria a contagem e a mutação passaria verde.
const L = (id, tipster, extra) => Object.assign({
  id, tipster, data: '2026-09-06', esporte: 'Futebol', casa: 'Bet365', operador: 'Fernando',
}, extra || {});
const DADOS = [
  L(1, 'Fatuch'), L(2, 'Fatuch'),
  L(3, 'LBB'), L(4, 'MarcoF1'), L(5, 'F1DP'),
];

const F = new Function('DADOS', fonte)(DADOS);

// ── 1. O cache existe e é reusado enquanto nada muda ──────────────────────
F.msInit('ti_apostas'); F.msInit('sp_apostas'); F.msInit('ca_apostas'); F.msInit('op_apostas');
const primeiro = F.filtrarPagina('apostas');
ok(primeiro.length === 5, 'sem seleção a página vê as 5 linhas (veio ' + primeiro.length + ')');
ok(F.filtrarPagina('apostas') === primeiro,
  'o cache parou de guardar o recorte — cada render volta a varrer DADOS inteiro');

// ── 2. Selecionar um tipster RECORTA de verdade, sem passar pelo renderPage ─
// Este é o caminho da Base Completa: `applyMS` chama o `cb` da tela (renderApostas),
// que chama `filtrarPagina` direto. Ninguém zera o cache no meio.
F.msToggle('ti_apostas', 'Fatuch');
const so = F.filtrarPagina('apostas');
ok(so.length === 2,
  'SELECIONAR TIPSTER NAO FILTROU: vieram ' + so.length + ' de 5 linhas. O recorte '
  + 'cacheado sobreviveu à seleção — é o bug da s322, e ele não dá erro nenhum');
ok(so.every(r => r.tipster === 'Fatuch'),
  'sobrou linha de outro tipster no recorte: ' + so.map(r => r.tipster).join(','));

// ── 3. Somar um segundo tipster também invalida ────────────────────────────
F.msToggle('ti_apostas', 'LBB');
ok(F.filtrarPagina('apostas').length === 3,
  'a segunda seleção não chegou à tabela (multi-seleção SOMA: Fatuch + LBB = 3)');

// ── 4. "Todos" volta atrás — o ramo do `__all__` sai por um `return` mais cedo ──
// Invalidar depois desse `return` deixaria justamente o Limpar sem efeito.
F.msToggle('ti_apostas', '__all__');
ok(F.msGet('ti_apostas').size === 0, 'o "__all__" deveria esvaziar a seleção');
ok(F.filtrarPagina('apostas').length === 5,
  'limpar a seleção não devolveu as 5 linhas — a invalidação ficou depois do return do __all__');

// ── 5. Vale para os outros eixos, não só para tipster ──────────────────────
F.msToggle('ca_apostas', 'Bet365');
ok(F.filtrarPagina('apostas').length === 5, 'casa Bet365 pega as 5 (todas são Bet365)');
F.msToggle('ca_apostas', 'Bet365'); F.msToggle('sp_apostas', 'Tênis');
ok(F.filtrarPagina('apostas').length === 0,
  'esporte inexistente na base tinha de zerar o recorte — o eixo de esporte não invalidou');

if (falhas) { console.error(LF + falhas + ' falha(s).'); process.exit(1); }
console.log('filtro_multiselect_cache: OK');
