// BOOKIES recebe custo e P/L Líquido (s364, Fatia 5) — e a MESMA régua das outras telas.
//
// A lista de Bookies só tinha P/L bruto, ROI, Casas Positivas e Turnover. O drill de uma
// casa já trazia Custo / P/L Líquido / ROI Líquido desde a s358; a LISTA, que é onde se
// decide "a operação nesta casa vale a pena", não trazia nada.
//
// As três regras que este arquivo trava, e nenhuma delas dá erro quando quebra:
//
//   1. O custo sai do `calcCostFiltered('casas')` — a MESMA função do KPI da Visão Geral.
//      Somar `calcCasaCost` casa a casa daria o mesmo número por um caminho novo, e duas
//      derivações para a mesma pergunta é o que a s362 acabou de desfazer.
//   2. `P/L Líquido = P/L bruto − custo`, exato. Um sinal trocado aqui é um número
//      plausível: continua parecendo dinheiro e continua na cor certa.
//   3. **Esporte e Tipster NÃO recortam o custo, e a tela DIZ isso.** Eles descrevem a
//      APOSTA — a conta Bet365 custou os mesmos R$ 900 quer se olhe tênis ou futebol.
//      Com um deles ligado o P/L é do recorte e o custo é das casas inteiras, e sem o
//      rótulo isso lê como defeito: medido na demo, filtrar Tênis leva o líquido de
//      +R$ 237.602,47 para −R$ 38.992,93 sem que nada tenha piorado.
//      Casa e Operador, ao contrário, RECORTAM — eles descrevem a CONTA.
//
// Executa `renderCasa` RECORTADA do `performance.js` de produção, com o
// `calcCostFiltered` REAL do `gestao.js` e os `fmtPL`/`fmtR`/`fmtPct` REAIS do `app.js`.
// O `document` é um dublê que só guarda o `innerHTML` — nada aqui é reimplementado.
//
// O que NÃO está coberto: os cards por casa (decisão do Feca na s364 — eles ficaram
// intactos, porque 45 das 48 casas dele não têm custo e o stat sairia `R$ 0` em todas),
// o layout (nº de colunas do grid, medido no navegador) e o drill, que tem régua própria.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const AQUI = dirname(fileURLToPath(import.meta.url));
const RAIZ = join(AQUI, '..', '..');
const BASE = join(RAIZ, 'app', 'static', 'dash', 'assets', 'js');
// ALVO_* existem para a prova por MUTAÇÃO.
const PERF = readFileSync(process.env.ALVO_PERF || join(BASE, 'charts', 'performance.js'), 'utf8');
const GESTAO = readFileSync(process.env.ALVO_GESTAO || join(BASE, 'charts', 'gestao.js'), 'utf8');
const FILTROS = readFileSync(join(BASE, 'filters.js'), 'utf8');
const APP = readFileSync(join(BASE, 'app.js'), 'utf8');
const LF = '\n';

let falhas = 0;
const ok = (cond, msg) => { if (!cond) { console.error('  ✗ ' + msg); falhas++; } };
const eq = (obtido, esperado, msg) => ok(obtido === esperado, msg + ', veio ' + obtido);

// Função de UMA linha é tentada PRIMEIRO, e o ramo é load-bearing: o recorte multilinha
// vai até o próximo `}` na coluna 0, então numa one-liner (`msGet`, `normForn`) ele
// engole tudo o que houver até a próxima função multilinha — inclusive declarações de
// topo de arquivo, que nascem duplicadas no harness (`_filterCache` já declarado).
// A sessão vizinha bateu no mesmo com o `costKey` engolindo o `CUSTO_SEED`.
const recorteFn = (src, nome, arq) => {
  const uma = src.match(new RegExp('^function ' + nome + '\\([^)]*\\)\\{.*\\}$', 'm'));
  if (uma) return uma[0];
  const m = src.match(new RegExp('^function ' + nome + '\\([^)]*\\)\\{[\\s\\S]*?^\\}', 'm'));
  if (!m) throw new Error('não achei a função ' + nome + ' no ' + arq);
  return m[0];
};

const FONTE = [
  ...['normForn', '_buildContaVida', '_precoVigenteEm', '_degrausPreco', '_dataDoPreco',
      '_custoDaConta', '_dataPagamento', '_renovacoesNaJanela', '_custoNaJanela', 'calcCostFiltered']
    .map(n => recorteFn(GESTAO, n, 'gestao.js')),
  // Máscaras REAIS: é delas que sai o texto que o teste lê. Dublá-las esconderia a
  // troca de `fmtPL` por `fmtR` num valor de P/L, que muda o sinal e as casas.
  ...['fmt', 'fmtPL', 'fmtR', 'fmtPct', 'calcTurnover', 'wrFrac', 'bumpWR']
    .map(n => recorteFn(APP, n, 'app.js')),
  // `msToggle` junto de proposito: e o caminho REAL do clique, e `msGet` sozinho
  // devolve um Set DESCARTAVEL quando o id ainda nao existe em MSS -- adicionar
  // nele nao seleciona nada, e o teste passaria medindo o estado sem filtro.
  ...['_ymd', '_today', 'gfs', '_selRange', 'msGet', 'msToggle'].map(n => recorteFn(FILTROS, n, 'filters.js')),
  recorteFn(PERF, 'renderCasa', 'performance.js'),
].join(LF);

const API = new Function(`
  const FS = {}, MSS = {};
  const window = { __dono: 'Feca' };
  let DADOS = [], DADOS_ABERTAS = [], custoData = {}, ctData = {}, cgData = [];
  let _contaVida = null, _contasVida = null, _precosForn = null;
  let _casaEnts = null, _casaDays = null, _casaAllDays = null;
  let _filterCache = {};                   // o msToggle REAL o zera; aqui so precisa existir
  // Dublê de DOM: guarda o innerHTML e nada mais. Ele NÃO prova layout nenhum — o
  // grid de 3 colunas foi medido no navegador, e este dublê aceitaria qualquer um.
  const _slots = {};
  const document = { getElementById: (id) => (_slots[id] = _slots[id] || { innerHTML: '' }) };
  function _renderCasaCards(){}            // cards não entram neste gate (ver cabeçalho)
  ${FONTE}
  return {
    set(cfg) {
      DADOS = cfg.dados || []; DADOS_ABERTAS = [];
      custoData = cfg.custos || {}; _contasVida = cfg.cadastro || null; _precosForn = [];
      _contaVida = null;
      for (const k of Object.keys(FS)) delete FS[k];
      for (const k of Object.keys(MSS)) delete MSS[k];
      for (const k of Object.keys(_slots)) delete _slots[k];
      if (cfg.periodo) FS.casas = Object.assign(gfs('casas'), cfg.periodo);
      (cfg.esportes || []).forEach(v => msToggle('sp_casas', v));
      (cfg.tipsters || []).forEach(v => msToggle('ti_casas', v));
      (cfg.casas || []).forEach(v => msToggle('ca_casas', v));
      renderCasa(DADOS.filter(r =>
        (!cfg.esportes || !cfg.esportes.length || cfg.esportes.includes(r.esporte)) &&
        (!cfg.tipsters || !cfg.tipsters.length || cfg.tipsters.includes(r.tipster)) &&
        (!cfg.casas || !cfg.casas.length || cfg.casas.includes(r.casa))));
    },
    html() { return (_slots.casaPortfolioKPIs || {}).innerHTML || ''; },
  };
`)();

// Lê um tile pelo rótulo: devolve {valor cru do .money-val, classe, sub}.
const tile = (html, label) => {
  const re = new RegExp('<span class="kpi-pipe"></span> ' + label +
    '</div><div class="kpi-val ([a-z]*)">(.*?)</div><div class="kpi-sub">(.*?)</div>');
  const m = re.exec(html);
  if (!m) return null;
  const val = /<span class="money-val">(.*?)<\/span>/.exec(m[2]);
  const sign = /<span class="money-sign">(.*?)<\/span>/.exec(m[2]);
  return { cls: m[1], sign: sign ? sign[1] : '', val: val ? val[1] : m[2], sub: m[3] };
};

const TUDO = { df: '', dt: '', qd: 0, qt: '' };
const ap = (casa, esporte, tipster, data, stake, lucro) =>
  ({ casa, esporte, tipster, data, stake, lucro, odd: 2, resultado: lucro >= 0 ? 'W' : 'L',
     conta: 'c1', fornecedor: 'GN', operador: 'Feca' });
const cad = (casa, conta, forn, adq) =>
  ({ casa, conta, fornecedor: forn, adquirida_em: adq, arquivada_em: '', arquivado: false, custo: null });

// ── 1. A cascata fecha: bruto − custo = líquido ──────────────────────────────
// Sinal trocado aqui não dá erro: continua parecendo dinheiro e na cor certa.
{
  API.set({
    dados: [ap('Bet365', 'Futebol', 'Ze', '2026-03-10', 100, 1000)],
    cadastro: [cad('Bet365', 'c1', 'GN', '2026-03-01')],
    custos: { 'GN||Bet365': 900 }, periodo: TUDO,
  });
  const h = API.html();
  const bruto = tile(h, 'P/L Bruto'), custo = tile(h, 'Custo de Contas'), liq = tile(h, 'P/L Líquido');
  ok(bruto && custo && liq, 'os três tiles da cascata têm de existir');
  eq(bruto.val, '1.000,00', 'P/L Bruto');
  eq(custo.val, '900,00', 'Custo de Contas');
  eq(liq.val, '100,00', 'P/L Líquido = 1000 − 900');
  eq(liq.sign, '+R$', 'líquido positivo leva +R$');
}

// ── 2. O custo desce como contribuição NEGATIVA ──────────────────────────────
// Mesma convenção da Visão Geral e do drill: `fmtPL(-x)`, para a coluna se ler como
// conta (bruto, menos custo, líquido). Trocar por `fmtR` apagaria o sinal e a cor.
{
  const h = API.html();
  const custo = tile(h, 'Custo de Contas');
  eq(custo.sign, '−R$', 'o custo aparece NEGATIVO (minus U+2212)');
  eq(custo.cls, 'neg', 'e em --neg');
}

// ── 3. Custo zero é NEUTRO e volta ao fmtR ───────────────────────────────────
// Não há o que subtrair, então não há sinal nem cor. E `R$ 0` aqui quer dizer "nada
// comprado no período", não "de graça" — é o sub que diz isso.
{
  API.set({
    dados: [ap('Pinnacle', 'Futebol', 'Ze', '2026-03-10', 100, 500)],
    cadastro: [], custos: {}, periodo: TUDO,
  });
  const h = API.html();
  const custo = tile(h, 'Custo de Contas'), liq = tile(h, 'P/L Líquido');
  eq(custo.cls, 'neu', 'custo zero é neutro');
  eq(custo.sign, 'R$', 'custo zero não leva sinal');
  eq(custo.sub, 'nenhuma compra no período', 'e o sub diz que não houve compra');
  eq(liq.val, '500,00', 'sem custo, o líquido é o bruto');
}

// ── 4. ESPORTE não recorta o custo, e a tela DIZ ─────────────────────────────
// A regra e o rótulo saem da MESMA condição; derivar o texto de outro lugar faria
// número e frase divergirem no 1º caso de borda.
{
  const cfg = {
    dados: [ap('Bet365', 'Futebol', 'Ze', '2026-03-10', 100, 1000),
            ap('Bet365', 'Tênis', 'Ze', '2026-03-11', 100, 200)],
    cadastro: [cad('Bet365', 'c1', 'GN', '2026-03-01')],
    custos: { 'GN||Bet365': 900 }, periodo: TUDO,
  };
  API.set(Object.assign({}, cfg));
  eq(tile(API.html(), 'P/L Bruto').val, '1.200,00', 'sem filtro, o bruto soma os dois');

  API.set(Object.assign({ esportes: ['Tênis'] }, cfg));
  const h = API.html();
  eq(tile(h, 'P/L Bruto').val, '200,00', 'com Tênis, o P/L recorta');
  eq(tile(h, 'Custo de Contas').val, '900,00', 'mas o custo NÃO recorta por esporte');
  eq(tile(h, 'Custo de Contas').sub, 'das casas inteiras · não recorta por esporte',
     'e a tela diz o corte');
  eq(tile(h, 'P/L Líquido').val, '700,00', 'líquido = 200 − 900, negativo');
  eq(tile(h, 'P/L Líquido').sign, '−R$', 'e ele fica NEGATIVO — é o caso que o rótulo explica');
  eq(tile(h, 'P/L Líquido').sub, 'P/L do recorte − custo das casas', 'o sub do líquido também muda');
}

// ── 5. TIPSTER também não recorta, e os dois juntos aparecem na frase ────────
{
  const cfg = {
    dados: [ap('Bet365', 'Futebol', 'Ze', '2026-03-10', 100, 1000),
            ap('Bet365', 'Tênis', 'Ana', '2026-03-11', 100, 200)],
    cadastro: [cad('Bet365', 'c1', 'GN', '2026-03-01')],
    custos: { 'GN||Bet365': 900 }, periodo: TUDO,
  };
  API.set(Object.assign({ tipsters: ['Ana'] }, cfg));
  eq(tile(API.html(), 'Custo de Contas').sub, 'das casas inteiras · não recorta por tipster',
     'com tipster ligado');
  API.set(Object.assign({ esportes: ['Tênis'], tipsters: ['Ana'] }, cfg));
  eq(tile(API.html(), 'Custo de Contas').sub, 'das casas inteiras · não recorta por esporte e tipster',
     'com os dois ligados');
}

// ── 6. CASA recorta o custo — ela descreve a CONTA ───────────────────────────
// A outra metade da regra. Um gate que só provasse o "não recorta" passaria com um
// custo que não recorta por NADA.
{
  API.set({
    dados: [ap('Bet365', 'Futebol', 'Ze', '2026-03-10', 100, 1000),
            ap('Betano', 'Futebol', 'Ze', '2026-03-11', 100, 500)],
    cadastro: [cad('Bet365', 'c1', 'GN', '2026-03-01'), cad('Betano', 'c1', 'JC', '2026-03-02')],
    custos: { 'GN||Bet365': 900, 'JC||Betano': 600 }, periodo: TUDO,
    casas: ['Bet365'],
  });
  const h = API.html();
  eq(tile(h, 'Custo de Contas').val, '900,00', 'com a casa filtrada, só o custo dela entra');
  eq(tile(h, 'Custo de Contas').sub, '1 conta comprada no período', 'e o sub conta 1, não 2');
}

// ── 6b. O sub do custo conta CONTAS, não casas ───────────────────────────────
// Duas contas na MESMA casa: `nContas` é 2 e o nº de casas é 1. Nos casos acima os
// dois números coincidem, e uma troca de um pelo outro passaria despercebida — é o
// "dado sintético que não exerce a regra" do CLAUDE.md.
{
  API.set({
    dados: [ap('Bet365', 'Futebol', 'Ze', '2026-03-10', 100, 1000)],
    cadastro: [cad('Bet365', 'c1', 'GN', '2026-03-01'), cad('Bet365', 'c2', 'GN', '2026-03-02')],
    custos: { 'GN||Bet365': 900 }, periodo: TUDO,
  });
  const h = API.html();
  eq(tile(h, 'Custo de Contas').sub, '2 contas compradas no período',
     'duas contas na mesma casa contam 2, não 1');
  eq(tile(h, 'Custo de Contas').val, '1.800,00', 'e o custo soma as duas');
  eq(tile(h, 'Casas Positivas').val, '1 / 1', 'enquanto a casa segue sendo uma só');
}

// ── 7. O PERÍODO recorta o custo, pela régua de lançamento ───────────────────
// Conta paga em março não cobra em maio. É a régua da s358, e aqui ela tem de chegar
// à tela: melhorar o cálculo não basta se ele não chega ao número exibido.
{
  const cfg = {
    dados: [ap('Bet365', 'Futebol', 'Ze', '2026-05-10', 100, 1000)],
    cadastro: [cad('Bet365', 'c1', 'GN', '2026-03-01')],
    custos: { 'GN||Bet365': 900 },
  };
  API.set(Object.assign({ periodo: { df: '2026-03-01', dt: '2026-03-31', qd: 0, qt: '' } }, cfg));
  eq(tile(API.html(), 'Custo de Contas').val, '900,00', 'março é o mês da compra');
  API.set(Object.assign({ periodo: { df: '2026-05-01', dt: '2026-05-31', qd: 0, qt: '' } }, cfg));
  eq(tile(API.html(), 'Custo de Contas').val, '0', 'maio não pagou nada');
}

// ── 8. Os tiles que já existiam continuam lá ─────────────────────────────────
// A fileira foi de 4 para 6; perder um no caminho não dá erro, some da tela.
{
  API.set({
    dados: [ap('Bet365', 'Futebol', 'Ze', '2026-03-10', 100, 1000),
            ap('Betano', 'Futebol', 'Ze', '2026-03-11', 100, -500)],
    cadastro: [], custos: {}, periodo: TUDO,
  });
  const h = API.html();
  ['P/L Bruto', 'Custo de Contas', 'P/L Líquido', 'ROI', 'Casas Positivas', 'Turnover Total']
    .forEach(l => ok(!!tile(h, l), 'o tile «' + l + '» tem de existir'));
  eq(tile(h, 'Casas Positivas').val, '1 / 2', 'Casas Positivas segue contando');
  eq(tile(h, 'Turnover Total').val, '200', 'Turnover segue somando');
}

if (falhas) { console.error(LF + falhas + ' verificação(ões) falharam.'); process.exit(1); }
console.log('bookies_custo.mjs: OK');
