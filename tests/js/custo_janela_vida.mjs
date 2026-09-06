// Prova por EXECUÇÃO da janela de vida da conta (s322).
//
// O sintoma que abriu o caso (tester Jaao26, vídeo): com o período em "Tudo" o KPI dizia
// `Custo de Contas −R$ 3.100,00`; filtrando UM dia (05/09 → 05/09) ele virava `R$ 0`, com
// o parque inteiro de contas em uso. *"Ele mostra que o meu custo de conta é zero, mas ele
// não necessariamente é zero porque eu ainda estou usando essas contas."*
//
// A causa: `calcCostFiltered` lançava o custo de aquisição num ÚNICO dia — o da primeira
// aposta LIQUIDADA da conta — e cobrava esse custo só quando a janela [menor, maior] data
// das LINHAS filtradas continha aquele dia. Qualquer outro recorte dava zero.
//
// A régua nova (decisão do Feca): o custo é único, pago na compra, e EXISTE enquanto a
// conta existe. Todo período que cruzar [ini, fim] cobra o custo cheio. `ini` = a menor
// entre `adquirida_em` e a 1ª aposta; `fim` = a maior entre a última aposta e
// `arquivada_em`; conta cadastrada, ativa e ainda sem aposta vale até hoje.
//
// As funções são RECORTADAS do gestao.js e do filters.js de produção — nunca reescritas
// aqui: teste que reimplementa o código sob teste não detecta a mutação que o quebra
// (CLAUDE.md, "Teste verde não é teste que detecta"). Só `FS`/`MSS` são declarados no
// wrapper, e são recipientes de estado vazios, não lógica.
//
// O que este teste NÃO cobre: nenhum DOM é montado — o texto da legenda do KPI ("N contas
// no período"), a cor do card e a Escada de Tinta ficam para o render headless; e a carga
// de `_contasVida` pelo `contasLoad` (fetch) é dublada aqui pelo `set({cadastro})`.
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const CR = String.fromCharCode(13), LF = String.fromCharCode(10);
const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const lerJs = p => fs.readFileSync(p, 'utf8').split(CR + LF).join(LF);
// ALVO_GESTAO existe para a prova por MUTAÇÃO: o pytest aponta para uma cópia estragada
// do gestao.js e confere que este arquivo fica vermelho.
const GESTAO = lerJs(process.env.ALVO_GESTAO || path.join(RAIZ, 'app/static/dash/assets/js/charts/gestao.js'));
const FILTROS = lerJs(path.join(RAIZ, 'app/static/dash/assets/js/filters.js'));

let falhas = 0;
const ok = (cond, msg) => { if (!cond) { console.error('FALHOU: ' + msg); falhas++; } };

// Recorta uma função de topo de nível: o `}` de fechamento é o único na coluna 0.
const recorteFn = (src, nome, arq) => {
  const m = src.match(new RegExp('^function ' + nome + '\\([^)]*\\)\\{[\\s\\S]*?^\\}', 'm'));
  if (!m) throw new Error('não achei a função ' + nome + ' no ' + arq);
  return m[0];
};

const FONTE = [
  ...['normForn', '_buildContaVida', '_custoNaJanela', 'calcCostFiltered', 'calcCasaCost']
    .map(n => recorteFn(GESTAO, n, 'gestao.js')),
  // Dependências REAIS do filters.js: `_selRange` é quem traduz o período escolhido na tela
  // (datas digitadas, atalho 7d/30d/90d, "Tudo") em {from,to}. Dublá-lo esconderia
  // justamente a metade da mudança que trocou a janela das LINHAS pela do PERÍODO.
  ...['_ymd', '_today', 'gfs', '_selRange', 'msGet'].map(n => recorteFn(FILTROS, n, 'filters.js')),
].join(LF);

const API = new Function(`
  const FS = {}, MSS = {};                 // recipientes de estado (filters.js), não lógica
  const window = { __dono: 'Feca' };
  let DADOS = [], DADOS_ABERTAS = [], custoData = {};
  let _contaVida = null, _contasVida = null;
  ${FONTE}
  return {
    set(cfg) {
      DADOS = cfg.dados || []; DADOS_ABERTAS = cfg.abertas || [];
      custoData = cfg.custos || {}; _contasVida = cfg.cadastro || null;
      _contaVida = null;
      for (const k of Object.keys(FS)) delete FS[k];
      for (const k of Object.keys(MSS)) delete MSS[k];
      if (cfg.periodo) FS.overview = Object.assign(gfs('overview'), cfg.periodo);
      if (cfg.ms) for (const k of Object.keys(cfg.ms)) MSS[k] = new Set(cfg.ms[k]);
    },
    vida() { if (!_contaVida) _buildContaVida(); return _contaVida; },
    calcCostFiltered, calcCasaCost,
  };
`)();

const hoje = (() => { const d = new Date(); return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); })();
const bilhete = (conta, casa, forn, data, op) => ({ conta, casa, fornecedor: forn, data, operador: op || 'Feca', resultado: 'W', lucro: 0, stake: 10 });
const cad = (conta, casa, forn, adq, arqEm) => ({ conta, casa, fornecedor: forn, adquirida_em: adq || '', arquivada_em: arqEm || '', arquivado: !!arqEm });
const periodo = (df, dt) => ({ df, dt, qd: 0 });

// ── A. O caso do vídeo: um dia dentro da vida da conta cobra o custo cheio ───
// Conta comprada em 01/09 e usada de 01 a 22/09. O custo é 1.700.
{
  API.set({
    custos: { 'GN||Betano': 1700 },
    dados: [bilhete('Betano1', 'Betano', 'GN', '2026-09-01'), bilhete('Betano1', 'Betano', 'GN', '2026-09-22')],
    cadastro: [cad('Betano1', 'Betano', 'GN', '2026-09-01')],
    periodo: periodo('2026-09-05', '2026-09-05'),
  });
  const r = API.calcCostFiltered('overview');
  ok(r.costConta === 1700, 'um dia DENTRO da vida da conta deveria cobrar 1700, veio ' + r.costConta);
  ok(r.nContas === 1, 'deveria contar 1 conta, veio ' + r.nContas);
}

// ── B. …e um dia DEPOIS da última aposta não cobra nada ──────────────────────
// "Se eu filtrar do dia 6 pra frente, ele já não vai puxar mais o custo daquela conta."
{
  API.set({
    custos: { 'GN||Betano': 1700 },
    dados: [bilhete('Betano1', 'Betano', 'GN', '2026-09-01'), bilhete('Betano1', 'Betano', 'GN', '2026-09-22')],
    cadastro: [cad('Betano1', 'Betano', 'GN', '2026-09-01')],
    periodo: periodo('2026-09-28', '2026-09-28'),
  });
  ok(API.calcCostFiltered('overview').costConta === 0, 'período depois da última aposta não pode cobrar custo');
  // E um dia ANTES da compra também não: a conta ainda não existia.
  API.set({
    custos: { 'GN||Betano': 1700 },
    dados: [bilhete('Betano1', 'Betano', 'GN', '2026-09-01')],
    cadastro: [cad('Betano1', 'Betano', 'GN', '2026-09-01')],
    periodo: periodo('2026-08-20', '2026-08-25'),
  });
  ok(API.calcCostFiltered('overview').costConta === 0, 'período anterior à compra não pode cobrar custo');
}

// ── C. Período SEM aposta nenhuma, no meio da vida, cobra igual ──────────────
// É a diferença de natureza entre a régua velha e a nova: o custo deixou de derivar das
// LINHAS do recorte. Apostou dia 01 e 22; o recorte 10→12 não tem bilhete e mesmo assim a
// conta estava viva. A régua velha devolvia 0 aqui por construção.
{
  API.set({
    custos: { 'GN||Betano': 1700 },
    dados: [bilhete('Betano1', 'Betano', 'GN', '2026-09-01'), bilhete('Betano1', 'Betano', 'GN', '2026-09-22')],
    cadastro: [cad('Betano1', 'Betano', 'GN', '2026-09-01')],
    periodo: periodo('2026-09-10', '2026-09-12'),
  });
  const r = API.calcCostFiltered('overview');
  ok(r.costConta === 1700, 'recorte sem aposta DENTRO da vida ainda cobra o custo, veio ' + r.costConta);
}

// ── D. O mês inteiro cobra uma vez só (e "Tudo" bate com o parque) ──────────
// "Se eu puxar o mês inteiro, como essa conta estava nos primeiros dias, ela contabiliza."
{
  API.set({
    custos: { 'GN||Betano': 1700, 'GN||Bet365': 900 },
    dados: [bilhete('Betano1', 'Betano', 'GN', '2026-09-01'), bilhete('B365a', 'Bet365', 'GN', '2026-09-14')],
    cadastro: [cad('Betano1', 'Betano', 'GN', '2026-09-01'), cad('B365a', 'Bet365', 'GN', '2026-09-14')],
    periodo: periodo('2026-09-01', '2026-09-30'),
  });
  ok(API.calcCostFiltered('overview').costConta === 2600, 'o mês inteiro soma as duas contas UMA vez cada');
  // "Tudo" = sem período nenhum (`_selRange` devolve null) → o parque inteiro.
  API.set({
    custos: { 'GN||Betano': 1700, 'GN||Bet365': 900 },
    dados: [bilhete('Betano1', 'Betano', 'GN', '2026-09-01'), bilhete('B365a', 'Bet365', 'GN', '2026-09-14')],
    cadastro: [cad('Betano1', 'Betano', 'GN', '2026-09-01'), cad('B365a', 'Bet365', 'GN', '2026-09-14')],
  });
  ok(API.calcCostFiltered('overview').costConta === 2600, '"Tudo" tem de somar o parque inteiro');
}

// ── E. Conta comprada e NUNCA usada conta — e some ao ser arquivada ─────────
// O tester elogiou isso na aba de Custos ("uma conta que eu nem usei, então contabilizou,
// isso tá cool") — e no KPI ela era invisível, porque a régua velha nascia da 1ª aposta.
{
  const base = { custos: { 'GN||Betano': 1700 }, dados: [], abertas: [] };
  API.set({ ...base, cadastro: [cad('Nova', 'Betano', 'GN', '2026-09-01')], periodo: periodo('2026-09-05', '2026-09-05') });
  ok(API.calcCostFiltered('overview').costConta === 1700, 'conta comprada e ainda sem aposta tem de contar');
  // Arquivada em 03/09: o carimbo fecha a janela e o período de 05/09 fica de fora.
  API.set({ ...base, cadastro: [cad('Nova', 'Betano', 'GN', '2026-09-01', '2026-09-03')], periodo: periodo('2026-09-05', '2026-09-05') });
  ok(API.calcCostFiltered('overview').costConta === 0, 'depois do arquivamento o custo para de aparecer');
  // …mas segue valendo ANTES do arquivamento.
  API.set({ ...base, cadastro: [cad('Nova', 'Betano', 'GN', '2026-09-01', '2026-09-03')], periodo: periodo('2026-09-02', '2026-09-02') });
  ok(API.calcCostFiltered('overview').costConta === 1700, 'antes do arquivamento o custo vale');
}

// ── F. Aposta ABERTA também mantém a conta viva ────────────────────────────
// `DADOS` só tem liquidadas. Conta cujo único bilhete está em aberto leria como morta —
// o mesmo ponto cego da s239, que deixou a aba de custos em branco para quem só tinha
// aposta em aberto.
{
  API.set({
    custos: { 'GN||Betano': 1700 },
    dados: [],
    abertas: [bilhete('Betano1', 'Betano', 'GN', '2026-09-20')],
    cadastro: [],
    periodo: periodo('2026-09-20', '2026-09-20'),
  });
  ok(API.calcCostFiltered('overview').costConta === 1700, 'aposta ABERTA tem de manter a conta viva');
}

// ── G. Conta só em BILHETE (sem cadastro) tem janela mesmo assim ────────────
// Na base do Feca são 130 contas que só existem em bilhete.
{
  API.set({
    custos: { 'GN||Betano': 1700 },
    dados: [bilhete('Antiga', 'Betano', 'GN', '2026-05-10'), bilhete('Antiga', 'Betano', 'GN', '2026-06-10')],
    cadastro: [],
    periodo: periodo('2026-05-20', '2026-05-25'),
  });
  ok(API.calcCostFiltered('overview').costConta === 1700, 'conta que só existe em bilhete tem janela pela 1ª/última aposta');
}

// ── H. `adquirida_em` ANTECIPA o início — não é a 1ª aposta ────────────────
// Comprou em 01/09 e só apostou em 20/09: o custo existe desde a compra.
{
  const cfg = {
    custos: { 'GN||Betano': 1700 },
    dados: [bilhete('Betano1', 'Betano', 'GN', '2026-09-20')],
    cadastro: [cad('Betano1', 'Betano', 'GN', '2026-09-01')],
  };
  API.set({ ...cfg, periodo: periodo('2026-09-05', '2026-09-05') });
  ok(API.calcCostFiltered('overview').costConta === 1700, 'entre a compra e a 1ª aposta o custo já vale');
  const v = API.vida()['GN||Betano']['Betano1'];
  ok(v.ini === '2026-09-01', 'ini deveria ser a data de compra, veio ' + v.ini);
  ok(v.fim === '2026-09-20', 'fim deveria ser a última aposta, veio ' + v.fim);
}

// ── I. Escopo: Casa recorta; Esporte e Tipster NÃO ─────────────────────────
// "A conta Bet365 custou R$ 900 quer você olhe tênis ou futebol." Casa e Operador
// descrevem a CONTA; esporte e tipster descrevem a APOSTA.
{
  const cfg = {
    custos: { 'GN||Betano': 1700, 'GN||Bet365': 900 },
    dados: [bilhete('Betano1', 'Betano', 'GN', '2026-09-05'), bilhete('B365a', 'Bet365', 'GN', '2026-09-05')],
    cadastro: [],
    periodo: periodo('2026-09-05', '2026-09-05'),
  };
  API.set({ ...cfg, ms: { ca_overview: ['Bet365'] } });
  ok(API.calcCostFiltered('overview').costConta === 900, 'filtro de CASA tem de recortar o custo');
  API.set({ ...cfg, ms: { sp_overview: ['Tênis'], ti_overview: ['LBB'] } });
  ok(API.calcCostFiltered('overview').costConta === 2600, 'filtro de esporte/tipster NÃO pode mexer no custo de contas');
  API.set({ ...cfg, ms: { op_overview: ['Lava'] } });
  ok(API.calcCostFiltered('overview').costConta === 0, 'filtro de OPERADOR tem de recortar o custo');
}

// ── J. Conta sem custo cadastrado não aparece na contagem ─────────────────
// A legenda diz "N contas no período"; contar conta grátis faria o divisor mental do
// leitor não bater com o valor ao lado.
{
  API.set({
    custos: { 'GN||Betano': 1700, 'GN||Bet365': 0 },
    dados: [bilhete('Betano1', 'Betano', 'GN', '2026-09-05'), bilhete('B365a', 'Bet365', 'GN', '2026-09-05')],
    cadastro: [],
    periodo: periodo('2026-09-05', '2026-09-05'),
  });
  const r = API.calcCostFiltered('overview');
  ok(r.costConta === 1700 && r.nContas === 1, 'conta com custo 0 não entra no valor nem na contagem, veio ' + r.costConta + '/' + r.nContas);
}

// ── K. O custo é POR CONTA, não por par fornecedor+casa ──────────────────
// `custoData` guarda o preço de UMA conta daquele par; três contas do mesmo par custam 3×.
{
  API.set({
    custos: { 'GN||Betano': 600 },
    dados: ['A', 'B', 'C'].map(c => bilhete(c, 'Betano', 'GN', '2026-09-05')),
    cadastro: [],
    periodo: periodo('2026-09-05', '2026-09-05'),
  });
  const r = API.calcCostFiltered('overview');
  ok(r.costConta === 1800 && r.nContas === 3, 'três contas do mesmo par custam 3×600, veio ' + r.costConta);
}

// ── L. `calcCasaCost` (drill-down de Bookies) usa a MESMA janela ─────────
// Duas contas de custo na mesma tela não podem medir coisas diferentes.
{
  API.set({
    custos: { 'GN||Betano': 1700, 'GN||Bet365': 900 },
    dados: [bilhete('Betano1', 'Betano', 'GN', '2026-09-01'), bilhete('B365a', 'Bet365', 'GN', '2026-09-01')],
    cadastro: [],
  });
  const so = API.calcCasaCost('Bet365', '2026-09-01', '2026-09-01');
  ok(so.total === 900 && so.nContas === 1, 'calcCasaCost tem de isolar a casa, veio ' + so.total);
  ok(API.calcCasaCost('Bet365', '2026-10-01', '2026-10-31').total === 0, 'fora da janela, calcCasaCost devolve 0');
}

// ── M. Conta ativa e sem aposta nenhuma vale até HOJE ───────────────────
{
  API.set({
    custos: { 'GN||Betano': 1700 },
    dados: [], cadastro: [cad('Nova', 'Betano', 'GN', '2026-01-01')],
  });
  const v = API.vida()['GN||Betano']['Nova'];
  ok(v.fim === hoje, 'conta ativa sem aposta deveria valer até hoje (' + hoje + '), veio ' + v.fim);
}

if (falhas) { console.error(LF + falhas + ' verificação(ões) falharam.'); process.exit(1); }
console.log('custo_janela_vida.mjs: OK');
