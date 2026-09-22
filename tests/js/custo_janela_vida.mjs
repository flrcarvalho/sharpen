// Prova por EXECUÇÃO das DUAS réguas de custo de conta (s322 + s358).
//
// O arquivo nasceu na s322 provando a JANELA DE VIDA. Na s358 a régua do P/L virou
// CAIXA, e a janela de vida continuou existindo para outra pergunta. As duas convivem,
// e por isso as duas são provadas aqui.
//
//   modo 'pago' (o P/L)  → "quanto saiu do bolso no recorte". Cada conta cobra UMA vez,
//        no dia do pagamento. SOMA: os 12 meses dão o ano.
//   modo 'vivo' (em operação) → "quanto vale o que está rodando". Toda conta viva no recorte
//        cobra cheio. NÃO soma, e por isso nunca entra no P/L.
//
// O caso que virou a régua do P/L (Jonathan, em áudio, 14/09/2026): *"ele só esse mês
// está puxando com o custo contando 12 e foi uma só"*. Medido na base dele: setembro
// cobrava R$ 6.400 de 10 contas tendo ele comprado UMA, de R$ 400; e a soma dos meses
// dava R$ 39.800 contra R$ 28.400 realmente pagos. "Não posso pagar uma conta duas
// vezes: se paguei em agosto, ela pertence a agosto" (Feca).
//
// O caso que criou a janela de vida (Jaao26, em vídeo): filtrar UM dia dava R$ 0 com o
// parque inteiro em uso. Esse número não sumiu — ele deixou de ser custo e virou
// ESTOQUE (modo 'vivo'), que é o que a Fatia 2 põe na tela como "parque".
//
// As funções são RECORTADAS do gestao.js e do filters.js de produção — nunca reescritas
// aqui: teste que reimplementa o código sob teste não detecta a mutação que o quebra
// (CLAUDE.md, "Teste verde não é teste que detecta"). Só `FS`/`MSS` são declarados no
// wrapper, e são recipientes de estado vazios, não lógica.
//
// O que este teste NÃO cobre: nenhum DOM é montado — o texto da legenda do KPI
// ("N contas compradas no período"), a cor do card e a Escada de Tinta ficam para o
// render headless; a carga de `_contasVida` pelo `contasLoad` (fetch) é dublada aqui
// pelo `set({cadastro})`; e o backfill SQL de `adquirida_em`, que só roda contra
// Postgres, é premissa (a medição dele está no CASOS.md, não aqui).
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
const APP = lerJs(path.join(RAIZ, 'app/static/dash/assets/js/app.js'));

let falhas = 0;
const ok = (cond, msg) => { if (!cond) { console.error('FALHOU: ' + msg); falhas++; } };

// Recorta uma função de topo de nível: o `}` de fechamento é o único na coluna 0.
// Função de UMA linha é tentada PRIMEIRO, e o ramo é load-bearing: o recorte multilinha
// vai até o próximo `}` em coluna zero, então numa one-liner (`costKey`, `normForn`) ele
// engole tudo o que houver até a próxima função multilinha — declarações de topo de
// arquivo inclusive, que nascem duplicadas no harness. Isto ficou VISÍVEL quando o
// `CUSTO_SEED` saiu do `gestao.js` (s369): até então o `};` dele servia de parada
// acidental para o recorte do `costKey`, e sem ele o harness passou a engolir o
// `let custoData={}` — `Identifier 'custoData' has already been declared`.
// **O recorte não estava certo antes; estava com sorte.**
const recorteFn = (src, nome, arq) => {
  const uma = src.match(new RegExp('^function ' + nome + '\\([^)]*\\)\\{.*\\}$', 'm'));
  if (uma) return uma[0];
  const m = src.match(new RegExp('^function ' + nome + '\\([^)]*\\)\\{[\\s\\S]*?^\\}', 'm'));
  if (!m) throw new Error('não achei a função ' + nome + ' no ' + arq);
  return m[0];
};

const FONTE = [
  ...['normForn', '_buildContaVida', '_precoVigenteEm', '_degrausPreco', '_dataDoPreco', '_custoDaConta',
      '_dataPagamento', '_renovacoesDoCadastro', '_renovacoesNaJanela', '_custoNaJanela', 'calcCostFiltered', 'calcContasEmOperacao',
      'calcCustoTipsterFiltrado', 'calcCustoGeralFiltrado', 'calcCasaCost']
    .map(n => recorteFn(GESTAO, n, 'gestao.js')),
  // `parseNum` é o parser de número do projeto (app.js) e o custo de tipster depende dele:
  // dublá-lo aqui esconderia justamente a regra de milhar que separa 179,90 de 17.990.
  recorteFn(APP, 'parseNum', 'app.js'),
  // Dependências REAIS do filters.js: `_selRange` é quem traduz o período escolhido na tela
  // (datas digitadas, atalho 7d/30d/90d, "Tudo") em {from,to}. Dublá-lo esconderia
  // justamente a metade da mudança que trocou a janela das LINHAS pela do PERÍODO.
  ...['_ymd', '_today', 'gfs', '_selRange', 'msGet'].map(n => recorteFn(FILTROS, n, 'filters.js')),
].join(LF);

const API = new Function(`
  const FS = {}, MSS = {};                 // recipientes de estado (filters.js), não lógica
  const window = { __dono: 'Feca' };
  let DADOS = [], DADOS_ABERTAS = [], custoData = {}, ctData = {}, cgData = [];
  let _contaVida = null, _contasVida = null, _precosForn = null;
  ${FONTE}
  return {
    set(cfg) {
      DADOS = cfg.dados || []; DADOS_ABERTAS = cfg.abertas || [];
      custoData = cfg.custos || {}; _contasVida = cfg.cadastro || null; ctData = cfg.tipsters || {};
      cgData = cfg.gerais || [];
      _precosForn = cfg.precos || [];
      _contaVida = null;
      for (const k of Object.keys(FS)) delete FS[k];
      for (const k of Object.keys(MSS)) delete MSS[k];
      if (cfg.periodo) FS.overview = Object.assign(gfs('overview'), cfg.periodo);
      if (cfg.ms) for (const k of Object.keys(cfg.ms)) MSS[k] = new Set(cfg.ms[k]);
    },
    vida() { if (!_contaVida) _buildContaVida(); return _contaVida; },
    // As contas em operação chamam a mesma função com modo 'vivo'. O parque(de,ate) daqui
    // exercita a janela em intervalo arbitrario; calcContasEmOperacao e o que a tela usa.
    // Sem crase neste comentário de propósito: ele vive DENTRO da template literal do
    // new Function, e uma crase aqui fecha a string (o caso da s296).
    parque(de, ate) { return _custoNaJanela(de, ate, null, null, '', 'vivo'); },
    calcCostFiltered, calcContasEmOperacao, calcCustoTipsterFiltrado, calcCustoGeralFiltrado,
    calcCasaCost, parseNum, _renovacoesDoCadastro,
  };
`)();

const hoje = (() => { const d = new Date(); return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); })();
const bilhete = (conta, casa, forn, data, op) => ({ conta, casa, fornecedor: forn, data, operador: op || 'Feca', resultado: 'W', lucro: 0, stake: 10 });
const cad = (conta, casa, forn, adq, arqEm) => ({ conta, casa, fornecedor: forn, adquirida_em: adq || '', arquivada_em: arqEm || '', arquivado: !!arqEm });
const periodo = (df, dt) => ({ df, dt, qd: 0 });

// ── A. O dia da COMPRA cobra o custo cheio ──────────────────────────────────
// Conta comprada em 01/09, usada de 01 a 22/09, custo 1.700.
{
  const cfg = {
    custos: { 'GN||Betano': 1700 },
    dados: [bilhete('Betano1', 'Betano', 'GN', '2026-09-01'), bilhete('Betano1', 'Betano', 'GN', '2026-09-22')],
    cadastro: [cad('Betano1', 'Betano', 'GN', '2026-09-01')],
  };
  API.set({ ...cfg, periodo: periodo('2026-09-01', '2026-09-01') });
  const r = API.calcCostFiltered('overview');
  ok(r.costConta === 1700, 'o dia da compra deveria cobrar 1700, veio ' + r.costConta);
  ok(r.nContas === 1, 'deveria contar 1 conta, veio ' + r.nContas);
}

// ── B. Um dia QUALQUER depois da compra não cobra nada ──────────────────────
// É o caso do Jonathan: a conta segue em uso, e não volta a custar. "Não posso pagar
// uma conta duas vezes."
{
  const cfg = {
    custos: { 'GN||Betano': 1700 },
    dados: [bilhete('Betano1', 'Betano', 'GN', '2026-09-01'), bilhete('Betano1', 'Betano', 'GN', '2026-09-22')],
    cadastro: [cad('Betano1', 'Betano', 'GN', '2026-09-01')],
  };
  API.set({ ...cfg, periodo: periodo('2026-09-05', '2026-09-05') });
  ok(API.calcCostFiltered('overview').costConta === 0, 'dia no meio do uso não pode recobrar a conta');
  API.set({ ...cfg, periodo: periodo('2026-09-22', '2026-09-22') });
  ok(API.calcCostFiltered('overview').costConta === 0, 'dia com aposta, mas sem compra, não cobra');
  API.set({ ...cfg, periodo: periodo('2026-10-01', '2026-10-31') });
  ok(API.calcCostFiltered('overview').costConta === 0, 'o mês SEGUINTE à compra não cobra de novo');
  API.set({ ...cfg, periodo: periodo('2026-08-20', '2026-08-25') });
  ok(API.calcCostFiltered('overview').costConta === 0, 'período anterior à compra não pode cobrar custo');
}

// ── C. A régua SOMA: os meses somados dão o total pago ─────────────────────
// É a prova aritmética que a régua velha não passava (R$ 39.800 somando os meses contra
// R$ 28.400 pagos, na base do Jonathan).
{
  const cfg = {
    custos: { 'GN||Betano': 600, 'GN||Bet365': 900, 'GN||Superbet': 400 },
    dados: [
      bilhete('B1', 'Betano', 'GN', '2026-07-10'),
      bilhete('B1', 'Betano', 'GN', '2026-09-28'),     // segue em uso em setembro
      bilhete('B2', 'Bet365', 'GN', '2026-08-05'),
      bilhete('B2', 'Bet365', 'GN', '2026-09-27'),
      bilhete('B3', 'Superbet', 'GN', '2026-09-02'),
    ],
    cadastro: [cad('B1', 'Betano', 'GN', '2026-07-10'), cad('B2', 'Bet365', 'GN', '2026-08-05'),
               cad('B3', 'Superbet', 'GN', '2026-09-02')],
  };
  const mes = (de, ate) => { API.set({ ...cfg, periodo: periodo(de, ate) }); return API.calcCostFiltered('overview').costConta; };
  const jul = mes('2026-07-01', '2026-07-31'), ago = mes('2026-08-01', '2026-08-31'), set = mes('2026-09-01', '2026-09-30');
  ok(jul === 600 && ago === 900 && set === 400, 'cada mês cobra só a compra dele, veio ' + jul + '/' + ago + '/' + set);
  API.set({ ...cfg });   // "Tudo"
  const tudo = API.calcCostFiltered('overview').costConta;
  ok(jul + ago + set === tudo, 'a soma dos meses (' + (jul + ago + set) + ') tem de bater com o total pago (' + tudo + ')');
  ok(tudo === 1900, '"Tudo" deveria somar as três contas uma vez cada, veio ' + tudo);
}

// ── D. Duas compras no mesmo mês somam; o mês inteiro cobra uma vez cada ────
{
  API.set({
    custos: { 'GN||Betano': 1700, 'GN||Bet365': 900 },
    dados: [bilhete('Betano1', 'Betano', 'GN', '2026-09-01'), bilhete('B365a', 'Bet365', 'GN', '2026-09-14')],
    cadastro: [cad('Betano1', 'Betano', 'GN', '2026-09-01'), cad('B365a', 'Bet365', 'GN', '2026-09-14')],
    periodo: periodo('2026-09-01', '2026-09-30'),
  });
  ok(API.calcCostFiltered('overview').costConta === 2600, 'o mês inteiro soma as duas compras UMA vez cada');
}

// ── E. Conta comprada e NUNCA usada cobra no mês da compra ─────────────────
// O tester elogiou isso na aba de Custos ("uma conta que eu nem usei, então
// contabilizou"). Sem aposta nenhuma, a única data que existe é a do cadastro.
{
  const base = { custos: { 'GN||Betano': 1700 }, dados: [], abertas: [] };
  API.set({ ...base, cadastro: [cad('Nova', 'Betano', 'GN', '2026-09-01')], periodo: periodo('2026-09-01', '2026-09-30') });
  ok(API.calcCostFiltered('overview').costConta === 1700, 'conta comprada e ainda sem aposta cobra no mês da compra');
  API.set({ ...base, cadastro: [cad('Nova', 'Betano', 'GN', '2026-09-01')], periodo: periodo('2026-10-01', '2026-10-31') });
  ok(API.calcCostFiltered('overview').costConta === 0, 'e não cobra de novo no mês seguinte');
}

// ── E2. Conta SEM data nenhuma não cobra em período nenhum ────────────────
// Cadastro sem `adquirida_em` (o fetch caiu, ou a linha nasceu sem data) e sem aposta:
// não há como datar o pagamento. Sem esta trava a conta cobraria em TODO recorte, que é
// exatamente o defeito que a régua de caixa existe para matar.
{
  const base = { custos: { 'GN||Betano': 1700 }, dados: [], abertas: [], cadastro: [cad('Sem', 'Betano', 'GN', '')] };
  API.set({ ...base, periodo: periodo('2026-09-01', '2026-09-30') });
  ok(API.calcCostFiltered('overview').costConta === 0, 'conta sem data de pagamento não pode cobrar em setembro');
  API.set({ ...base, periodo: periodo('2026-01-01', '2026-01-31') });
  ok(API.calcCostFiltered('overview').costConta === 0, 'nem em janeiro');
  API.set({ ...base });
  ok(API.calcCostFiltered('overview').costConta === 0, 'nem em "Tudo"');
}

// ── F. Aposta ABERTA também data o pagamento ───────────────────────────────
// `DADOS` só tem liquidadas. Conta cujo único bilhete está em aberto ficaria sem data de
// pagamento nenhuma — o mesmo ponto cego da s239, que deixou a aba de custos em branco
// para quem só tinha aposta em aberto.
{
  API.set({
    custos: { 'GN||Betano': 1700 },
    dados: [],
    abertas: [bilhete('Betano1', 'Betano', 'GN', '2026-09-20')],
    cadastro: [],
    periodo: periodo('2026-09-01', '2026-09-30'),
  });
  ok(API.calcCostFiltered('overview').costConta === 1700, 'aposta ABERTA tem de datar o pagamento da conta');
}

// ── G. Conta só em BILHETE (sem cadastro) paga na 1ª aposta ────────────────
// Na base do Feca são 130 contas que só existem em bilhete; medido na s358, 13 no total
// das bases. Sem cadastro não há data de compra, e a 1ª aposta é o piso medido.
{
  const cfg = {
    custos: { 'GN||Betano': 1700 },
    dados: [bilhete('Antiga', 'Betano', 'GN', '2026-05-10'), bilhete('Antiga', 'Betano', 'GN', '2026-06-10')],
    cadastro: [],
  };
  API.set({ ...cfg, periodo: periodo('2026-05-01', '2026-05-31') });
  ok(API.calcCostFiltered('overview').costConta === 1700, 'conta só em bilhete paga no mês da 1ª aposta');
  API.set({ ...cfg, periodo: periodo('2026-06-01', '2026-06-30') });
  ok(API.calcCostFiltered('overview').costConta === 0, 'e não repete no mês da 2ª aposta');
}

// ── H. A data DIGITADA manda quando é anterior à 1ª aposta ────────────────
// Decisão do Feca (s358): "conta antiga entra o custo na primeira aposta, desde que o
// usuário não tenha lançado o custo numa data anterior". Comprou em 01/09 e só apostou
// em 20/09: o dinheiro saiu em 01/09.
{
  const cfg = {
    custos: { 'GN||Betano': 1700 },
    dados: [bilhete('Betano1', 'Betano', 'GN', '2026-09-20')],
    cadastro: [cad('Betano1', 'Betano', 'GN', '2026-09-01')],
  };
  API.set({ ...cfg, periodo: periodo('2026-09-01', '2026-09-05') });
  ok(API.calcCostFiltered('overview').costConta === 1700, 'a compra declarada antes da 1ª aposta é que paga');
  API.set({ ...cfg, periodo: periodo('2026-09-20', '2026-09-20') });
  ok(API.calcCostFiltered('overview').costConta === 0, 'e a 1ª aposta não cobra de novo');
}

// ── H2. …e NÃO manda quando é POSTERIOR à 1ª aposta ───────────────────────
// É o caso das contas migradas: o `adquirida_em` delas foi DEDUZIDO pelo backfill e não
// declara nada. Se ele cair depois da 1ª aposta, quem paga é a 1ª aposta, que é o piso
// medido. Sem esta metade, base importada dataria o custo no dia do import.
{
  const cfg = {
    custos: { 'GN||Betano': 1700 },
    dados: [bilhete('Antiga', 'Betano', 'GN', '2026-03-10')],
    cadastro: [cad('Antiga', 'Betano', 'GN', '2026-08-01')],   // "cadastrada" no import
  };
  API.set({ ...cfg, periodo: periodo('2026-03-01', '2026-03-31') });
  ok(API.calcCostFiltered('overview').costConta === 1700, 'com adquirida_em posterior, paga a 1ª aposta (março)');
  API.set({ ...cfg, periodo: periodo('2026-08-01', '2026-08-31') });
  ok(API.calcCostFiltered('overview').costConta === 0, 'o mês do import não pode virar o mês do pagamento');
}

// ── I. Escopo: Casa e Operador recortam; Esporte e Tipster NÃO ────────────
// "A conta Bet365 custou R$ 900 quer você olhe tênis ou futebol." Casa e Operador
// descrevem a CONTA; esporte e tipster descrevem a APOSTA.
{
  const cfg = {
    custos: { 'GN||Betano': 1700, 'GN||Bet365': 900 },
    dados: [bilhete('Betano1', 'Betano', 'GN', '2026-09-05'), bilhete('B365a', 'Bet365', 'GN', '2026-09-05')],
    cadastro: [],
    periodo: periodo('2026-09-01', '2026-09-30'),
  };
  API.set({ ...cfg, ms: { ca_overview: ['Bet365'] } });
  ok(API.calcCostFiltered('overview').costConta === 900, 'filtro de CASA tem de recortar o custo');
  API.set({ ...cfg, ms: { sp_overview: ['Tênis'], ti_overview: ['LBB'] } });
  ok(API.calcCostFiltered('overview').costConta === 2600, 'filtro de esporte/tipster NÃO pode mexer no custo de contas');
  API.set({ ...cfg, ms: { op_overview: ['Lava'] } });
  ok(API.calcCostFiltered('overview').costConta === 0, 'filtro de OPERADOR tem de recortar o custo');
}

// ── J. Conta sem custo cadastrado não aparece na contagem ─────────────────
// A legenda diz "N contas compradas no período"; contar conta grátis faria o divisor
// mental do leitor não bater com o valor ao lado.
{
  API.set({
    custos: { 'GN||Betano': 1700, 'GN||Bet365': 0 },
    dados: [bilhete('Betano1', 'Betano', 'GN', '2026-09-05'), bilhete('B365a', 'Bet365', 'GN', '2026-09-05')],
    cadastro: [],
    periodo: periodo('2026-09-01', '2026-09-30'),
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
    periodo: periodo('2026-09-01', '2026-09-30'),
  });
  const r = API.calcCostFiltered('overview');
  ok(r.costConta === 1800 && r.nContas === 3, 'três contas do mesmo par custam 3×600, veio ' + r.costConta);
}

// ── L. `calcCasaCost` (drill-down de Bookies) usa a MESMA régua ─────────
// Duas contas de custo na mesma tela não podem medir coisas diferentes. A conta segue
// APOSTANDO em outubro de propósito: é o que separa a régua de caixa da de vida, e sem
// isso o drill podia ficar com a régua velha sem nenhum teste acusar.
{
  API.set({
    custos: { 'GN||Betano': 1700, 'GN||Bet365': 900 },
    dados: [bilhete('Betano1', 'Betano', 'GN', '2026-09-01'), bilhete('B365a', 'Bet365', 'GN', '2026-09-01'),
            bilhete('B365a', 'Bet365', 'GN', '2026-10-20')],
    cadastro: [],
  });
  const so = API.calcCasaCost('Bet365', '2026-09-01', '2026-09-30');
  ok(so.total === 900 && so.nContas === 1, 'calcCasaCost tem de isolar a casa, veio ' + so.total);
  ok(API.calcCasaCost('Bet365', '2026-10-01', '2026-10-31').total === 0,
     'no mês seguinte, com a conta ainda em uso, o drill não pode recobrar a compra');
}

// ── M. A JANELA DE VIDA continua de pé, no modo 'vivo' (o parque) ────────
// É a pergunta do Jaao26, que não sumiu: ela saiu do P/L e virou estoque. Mesmos dados do
// caso B, onde o custo PAGO é zero. Conta SEM cadastro de propósito: dela só se sabe o que
// os bilhetes dizem, então a janela é [1ª aposta, última aposta].
{
  const cfg = {
    custos: { 'GN||Betano': 1700 },
    dados: [bilhete('Betano1', 'Betano', 'GN', '2026-09-01'), bilhete('Betano1', 'Betano', 'GN', '2026-09-22')],
    cadastro: [],
    periodo: periodo('2026-09-05', '2026-09-05'),
  };
  API.set(cfg);
  ok(API.calcCostFiltered('overview').costConta === 0, 'pré-condição: no dia 05 nada foi PAGO');
  const p = API.parque('2026-09-05', '2026-09-05');
  ok(p.total === 1700 && p.nContas === 1, 'o parque do dia 05 tem a conta viva (1700), veio ' + p.total);
  ok(API.parque('2026-09-28', '2026-09-28').total === 0, 'conta só em bilhete sai do parque depois da última aposta');
  ok(API.parque('2026-08-20', '2026-08-25').total === 0, 'antes da compra a conta ainda não está no parque');
}

// ── M1b. Conta CADASTRADA e ativa fica no parque sem apostar hoje ────────
// "fim = última aposta" é o que se sabe de quem não tem cadastro. Quem tem cadastro e não
// foi arquivado continua COMPRADO: medido na base do germano, a régua antiga mostrava 1
// conta de 6 no parque de hoje, só porque as outras 5 não apostaram naquele dia.
{
  API.set({
    custos: { 'GN||Betano': 1700 },
    dados: [bilhete('Betano1', 'Betano', 'GN', '2026-01-10')],   // última aposta em janeiro
    cadastro: [cad('Betano1', 'Betano', 'GN', '2026-01-05')],
  });
  const v = API.vida()['GN||Betano']['Betano1'];
  ok(v.fim === hoje, 'conta cadastrada e ativa deveria viver até hoje (' + hoje + '), veio ' + v.fim);
  ok(API.parque(hoje, hoje).total === 1700, 'e ela tem de estar no parque de hoje');
  ok(API.calcContasEmOperacao('overview').total === 1700, 'calcParqueFiltered pergunta por HOJE sozinho');
}

// ── M1c. Arquivada SEM carimbo não está no parque de hoje ────────────────
// `arquivado: true` com `arquivada_em` vazio é o estado de quem foi arquivado antes de a
// coluna existir. Como `bilhetes.data` é a data do EVENTO, uma aposta em jogo futuro
// deixava a conta "viva" para sempre: quatro contas do Jonathan e do realtrial apareciam
// no parque de hoje com aposta datada de dezembro (s358).
{
  const futura = (() => { const d = new Date(Date.now() + 90 * 864e5); return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); })();
  API.set({
    custos: { 'GN||Betano': 1700 },
    dados: [bilhete('Velha', 'Betano', 'GN', futura)],
    cadastro: [{ casa: 'Betano', conta: 'Velha', fornecedor: 'GN', adquirida_em: '2026-01-05', arquivada_em: '', arquivado: true }],
  });
  ok(API.parque(hoje, hoje).total === 0, 'conta arquivada sem carimbo não pode estar no parque de hoje');
}

// ── M1d. Contas em operação respeitam CASA e OPERADOR, e ignoram o período ──
{
  const cfg = {
    custos: { 'GN||Betano': 1700, 'GN||Bet365': 900 },
    dados: [bilhete('Betano1', 'Betano', 'GN', '2026-01-10'), bilhete('B365a', 'Bet365', 'GN', '2026-01-10')],
    cadastro: [cad('Betano1', 'Betano', 'GN', '2026-01-05'), cad('B365a', 'Bet365', 'GN', '2026-01-05')],
    // Período ANTERIOR à compra das duas contas, de propósito: é o único recorte que
    // separa "parque de hoje" de "parque do período". Um período depois da compra daria
    // o mesmo número nas duas réguas, e a mutação passaria verde (foi o que aconteceu).
    periodo: periodo('2025-01-01', '2025-01-31'),
  };
  API.set(cfg);
  ok(API.calcContasEmOperacao('overview').total === 2600, 'o rodapé ignora o período da tela, veio ' + API.calcContasEmOperacao('overview').total);
  API.set({ ...cfg, ms: { ca_overview: ['Bet365'] } });
  ok(API.calcContasEmOperacao('overview').total === 900, 'filtro de CASA recorta as contas em operação');
  API.set({ ...cfg, ms: { op_overview: ['Lava'] } });
  ok(API.calcContasEmOperacao('overview').total === 0, 'filtro de OPERADOR recorta as contas em operação');
  // Esporte segue sem recortar (uma conta não pertence a um esporte). TIPSTER passou a
  // recortar no desenho da s358 — a prova está no caso O, com a conta compartilhada.
  API.set({ ...cfg, ms: { sp_overview: ['Tenis'] } });
  ok(API.calcContasEmOperacao('overview').total === 2600, 'esporte NÃO recorta as contas em operação');
}

// ── M2. Conta ativa e sem aposta nenhuma fica viva até HOJE ──────────────
{
  API.set({
    custos: { 'GN||Betano': 1700 },
    dados: [], cadastro: [cad('Nova', 'Betano', 'GN', '2026-01-01')],
  });
  const v = API.vida()['GN||Betano']['Nova'];
  ok(v.fim === hoje, 'conta ativa sem aposta deveria valer até hoje (' + hoje + '), veio ' + v.fim);
  ok(API.parque(hoje, hoje).total === 1700, 'e ela está no parque de hoje');
}

// ── M3. Arquivar tira do parque, sem mexer no que já foi pago ───────────
// O carimbo de arquivamento fecha a janela de vida. O pagamento é passado e não se
// desfaz: quem arquiva não recebe o dinheiro de volta.
{
  const base = { custos: { 'GN||Betano': 1700 }, dados: [], abertas: [] };
  API.set({ ...base, cadastro: [cad('Nova', 'Betano', 'GN', '2026-09-01', '2026-09-03')], periodo: periodo('2026-09-01', '2026-09-30') });
  ok(API.parque('2026-09-05', '2026-09-05').total === 0, 'depois do arquivamento a conta sai do parque');
  ok(API.parque('2026-09-02', '2026-09-02').total === 1700, 'antes do arquivamento ela ainda está lá');
  ok(API.calcCostFiltered('overview').costConta === 1700, 'e o mês da compra segue cobrando o que foi pago');
}

// ── T. Custo de TIPSTER: o filtro de tipster recorta (etapa 3) ──────────────
// Pedido do Germano: "quando a gente filtrar so um tipster ficar os custos so dele".
{
  const cfg = {
    custos: {}, dados: [bilhete('C', 'Betano', 'GN', '2026-09-10')], cadastro: [],
    tipsters: {
      'Badminton': { '2026-09': '2000,00' },
      'Latino': { '2026-09': '207,00' },
      'Beta': { '2026-08': '164,00' },
    },
    periodo: periodo('2026-09-01', '2026-09-30'),
  };
  API.set(cfg);
  let r = API.calcCustoTipsterFiltrado('overview');
  ok(r.total === 2207 && r.nTips === 2, 'setembro inteiro soma os dois tipsters do mes, veio ' + r.total);
  API.set({ ...cfg, ms: { ti_overview: ['Badminton'] } });
  r = API.calcCustoTipsterFiltrado('overview');
  ok(r.total === 2000 && r.nTips === 1, 'com o Badminton filtrado, so o custo dele, veio ' + r.total);
  API.set({ ...cfg, ms: { ti_overview: ['Beta'] } });
  ok(API.calcCustoTipsterFiltrado('overview').total === 0, 'tipster sem lancamento no periodo custa 0');
  // Casa, esporte e operador NAO recortam: assinatura nao e de casa nenhuma.
  API.set({ ...cfg, ms: { ca_overview: ['Bet365'], sp_overview: ['Tenis'], op_overview: ['Lava'] } });
  ok(API.calcCustoTipsterFiltrado('overview').total === 2207, 'casa/esporte/operador nao recortam o custo de tipster');
}

// ── T2. A janela vem do PERIODO, nunca das linhas ──────────────────────────
// Era o `_ymMin`/`_ymMax` tirado das apostas que sobraram: mes pago SEM aposta nenhuma
// valia R$ 0, e um filtro de esporte encolhia a janela do custo de todo mundo.
{
  const cfg = {
    custos: {}, dados: [], abertas: [], cadastro: [],
    tipsters: { 'Latino': { '2026-08': '207,00', '2026-09': '207,00' } },
  };
  API.set({ ...cfg, periodo: periodo('2026-09-01', '2026-09-30') });
  ok(API.calcCustoTipsterFiltrado('overview').total === 207, 'mes pago sem aposta nenhuma continua custando');
  API.set({ ...cfg, periodo: periodo('2026-08-01', '2026-09-30') });
  ok(API.calcCustoTipsterFiltrado('overview').total === 414, 'dois meses somam duas mensalidades');
  API.set({ ...cfg });   // "Tudo"
  ok(API.calcCustoTipsterFiltrado('overview').total === 414, '"Tudo" pega todos os meses');
  API.set({ ...cfg, periodo: periodo('2026-07-01', '2026-07-31') });
  ok(API.calcCustoTipsterFiltrado('overview').total === 0, 'mes sem lancamento custa 0');
}

// ── T3. Mensal: o mes entra INTEIRO se um dia dele estiver no recorte ──────
// Meia mensalidade nao existe, e ratear inventaria um numero que ninguem pagou.
{
  const cfg = {
    custos: {}, dados: [], abertas: [], cadastro: [],
    tipsters: { 'Latino': { '2026-09': '207,00' } },
  };
  API.set({ ...cfg, periodo: periodo('2026-09-14', '2026-09-14') });
  ok(API.calcCustoTipsterFiltrado('overview').total === 207, 'um dia do mes cobra a mensalidade inteira');
  API.set({ ...cfg, periodo: periodo('2026-09-28', '2026-09-30') });
  ok(API.calcCustoTipsterFiltrado('overview').total === 207, 'o fim do mes cobra a mesma mensalidade');
}

// ── T4. O valor vem do parseNum, e a regra de milhar e por FORMA ───────────
// Ha valor gravado como "179.90" na base real (2 linhas). Um separador so, com menos de
// tres digitos depois, e DECIMAL — um parser que apaga o ponto le 17.990 (CLAUDE.md,
// "as duas armadilhas de reparsear o que a tela imprimiu").
{
  ok(API.parseNum('179.90') === 179.9, 'um separador com 2 digitos depois e decimal, veio ' + API.parseNum('179.90'));
  ok(API.parseNum('1.234') === 1234, 'grupo de 3 digitos e milhar, veio ' + API.parseNum('1.234'));
  ok(API.parseNum('1.234,56') === 1234.56, 'ponto de milhar com virgula decimal, veio ' + API.parseNum('1.234,56'));
  ok(API.parseNum('250,00') === 250, 'virgula decimal, veio ' + API.parseNum('250,00'));
  const cfg = {
    custos: {}, dados: [], abertas: [], cadastro: [],
    tipsters: { 'SoChutes': { '2026-07': '179.90' }, 'Outro': { '2026-07': '1.200' } },
    periodo: periodo('2026-07-01', '2026-07-31'),
  };
  API.set(cfg);
  const t = API.calcCustoTipsterFiltrado('overview').total;
  ok(Math.abs(t - 1379.9) < 0.001, '179.90 + 1.200 deveria dar 1379,90; veio ' + t);
}

// ── G. Custos GERAIS: mesma regua do tipster, e filtro nenhum recorta ──────
// VPN, ferramentas e taxas sao da OPERACAO inteira. O Jonathan tem R$ 987/mai,
// R$ 1.468/jun e R$ 1.321/jul lancados que nunca desceram no P/L Liquido dele.
{
  const cfg = {
    custos: {}, dados: [bilhete('C', 'Betano', 'GN', '2026-09-10')], cadastro: [],
    gerais: [
      { id: 1, tipo: 'VPN', values: { '2026-08': '120,00', '2026-09': '120,00' } },
      { id: 2, tipo: 'Ferramentas', values: { '2026-09': '1.480,00' } },
      { id: 3, tipo: 'Taxas', values: {} },
    ],
  };
  API.set({ ...cfg, periodo: periodo('2026-09-01', '2026-09-30') });
  let r = API.calcCustoGeralFiltrado('overview');
  ok(r.total === 1600 && r.nLinhas === 2, 'setembro soma VPN + Ferramentas (1600), veio ' + r.total + '/' + r.nLinhas);
  API.set({ ...cfg, periodo: periodo('2026-08-01', '2026-09-30') });
  ok(API.calcCustoGeralFiltrado('overview').total === 1720, 'dois meses somam as duas mensalidades da VPN');
  API.set({ ...cfg, periodo: periodo('2026-07-01', '2026-07-31') });
  ok(API.calcCustoGeralFiltrado('overview').total === 0, 'mes sem lancamento custa 0');
  API.set({ ...cfg });
  ok(API.calcCustoGeralFiltrado('overview').total === 1720, '"Tudo" pega todos os meses');
  // Linha sem valor nenhum nao conta como categoria.
  API.set({ ...cfg, periodo: periodo('2026-09-01', '2026-09-30') });
  ok(API.calcCustoGeralFiltrado('overview').nLinhas === 2, 'linha vazia nao entra na contagem');
  // Filtro NENHUM recorta: a VPN nao e de casa, de esporte nem de tipster.
  API.set({ ...cfg, periodo: periodo('2026-09-01', '2026-09-30'),
            ms: { ca_overview: ['Bet365'], sp_overview: ['Tenis'], ti_overview: ['LBB'], op_overview: ['Lava'] } });
  ok(API.calcCustoGeralFiltrado('overview').total === 1600, 'filtro nenhum recorta custo geral');
  // E o valor passa pelo parseNum: "1.480,00" e mil quatrocentos e oitenta.
  ok(API.parseNum('1.480,00') === 1480, 'o geral le pela regua do projeto');
}

// ── O. Contas em operacao: o filtro de TIPSTER recorta pelas contas USADAS ──
// Regra 6.4 do desenho. O vinculo conta->tipster nao existe no cadastro: existe no
// BILHETE. Medido na base real, 96% das contas do Feca sao usadas por mais de um
// tipster, entao a mesma conta entra no recorte de varios e os rodapes NAO somam —
// e e por isso que o rotulo muda junto com o numero.
{
  const cfg = {
    custos: { 'GN||Betano': 600, 'GN||Bet365': 900 },
    dados: [
      { conta: 'B1', casa: 'Betano', fornecedor: 'GN', data: '2026-09-02', operador: 'Feca', tipster: 'Zora', resultado: 'W', lucro: 0, stake: 10 },
      { conta: 'B2', casa: 'Bet365', fornecedor: 'GN', data: '2026-09-03', operador: 'Feca', tipster: 'LBB', resultado: 'W', lucro: 0, stake: 10 },
      // a MESMA conta usada por dois tipsters: ela entra nos dois recortes
      { conta: 'B1', casa: 'Betano', fornecedor: 'GN', data: '2026-09-04', operador: 'Feca', tipster: 'LBB', resultado: 'W', lucro: 0, stake: 10 },
    ],
    cadastro: [cad('B1', 'Betano', 'GN', '2026-09-01'), cad('B2', 'Bet365', 'GN', '2026-09-01')],
  };
  API.set(cfg);
  let r = API.calcContasEmOperacao('overview');
  ok(r.nContas === 2 && r.total === 1500, 'sem filtro, as duas contas; veio ' + r.nContas + '/' + r.total);
  API.set({ ...cfg, ms: { ti_overview: ['Zora'] } });
  r = API.calcContasEmOperacao('overview');
  ok(r.nContas === 1 && r.total === 600, 'o Zora so usou a Betano; veio ' + r.nContas + '/' + r.total);
  API.set({ ...cfg, ms: { ti_overview: ['LBB'] } });
  r = API.calcContasEmOperacao('overview');
  ok(r.nContas === 2 && r.total === 1500, 'o LBB usou as duas; veio ' + r.nContas + '/' + r.total);
  // A soma dos dois recortes (600 + 1500) e MAIOR que o total (1500): conta compartilhada
  // entra nos dois. E medido, e e por isso que o rotulo do cartao muda.
  API.set({ ...cfg, ms: { ti_overview: ['Ninguem'] } });
  ok(API.calcContasEmOperacao('overview').nContas === 0, 'tipster sem conta nenhuma da zero');
  // esporte e operador seguem sem recortar
  API.set({ ...cfg, ms: { sp_overview: ['Tenis'] } });
  ok(API.calcContasEmOperacao('overview').total === 1500, 'esporte nao recorta contas em operacao');
}

// ── N. As TRES camadas do custo de uma conta (s348, Fatia 2) ────────────────
// A ordem e a regra. Errar a ordem nao da erro: da o numero errado, com cara de
// numero certo — e o total do KPI e feito desta soma.

// N1. INVARIANTE DA MIGRACAO: sem custo proprio e sem historico de preco, o custo
// cai no preco do par, que e exatamente o que a tela cobrava ANTES da Fatia 2.
{
  API.set({
    custos: { 'GN||Betano': 1700 },
    dados: [bilhete('Betano1', 'Betano', 'GN', '2026-09-01')],
    cadastro: [cad('Betano1', 'Betano', 'GN', '2026-09-01')],
    precos: [],
    periodo: periodo('2026-09-01', '2026-09-30'),
  });
  const r = API.calcCostFiltered('overview');
  ok(r.costConta === 1700, 'sem custo proprio e sem historico, vale o preco do par; veio ' + r.costConta);
}

// N2. O custo PROPRIO da conta manda em tudo: "voce pode comprar 10 contas a um
// valor x, e duas voce acabou colocando outro preco individual".
{
  API.set({
    custos: { 'GN||Betano': 1700 },
    dados: [bilhete('Betano1', 'Betano', 'GN', '2026-09-01')],
    cadastro: [Object.assign(cad('Betano1', 'Betano', 'GN', '2026-09-01'), { custo: 2500 })],
    precos: [{ id: 1, fornecedor: 'GN', casa: 'Betano', valor: 900, vigente_desde: '2026-01-01' }],
    periodo: periodo('2026-09-01', '2026-09-30'),
  });
  ok(API.calcCostFiltered('overview').costConta === 2500,
     'o custo proprio da conta tem de vencer o preco do fornecedor e o do par');
}

// N3. Sem custo proprio, vale o preco VIGENTE NA DATA DE COMPRA — nao o de hoje.
// Preco novo nao e retroativo: quem comprou em marco pagou o de marco.
{
  API.set({
    custos: { 'GN||Betano': 9999 },   // o "preco de hoje" do par, que NAO pode ser usado
    dados: [bilhete('Antiga', 'Betano', 'GN', '2026-03-10')],
    cadastro: [cad('Antiga', 'Betano', 'GN', '2026-03-10')],
    precos: [
      { id: 1, fornecedor: 'GN', casa: 'Betano', valor: 850, vigente_desde: '2026-01-01' },
      { id: 2, fornecedor: 'GN', casa: 'Betano', valor: 950, vigente_desde: '2026-08-01' },
    ],
    periodo: periodo('2026-03-01', '2026-03-31'),
  });
  ok(API.calcCostFiltered('overview').costConta === 850,
     'conta comprada em marco tem de custar o preco de marco (850), veio ' +
     API.calcCostFiltered('overview').costConta);
}

// N4. Duas contas do MESMO par, compradas em degraus diferentes, custam diferente.
// E a razao inteira de o preco ter data.
{
  API.set({
    custos: {},
    dados: [bilhete('Velha', 'Betano', 'GN', '2026-03-10'), bilhete('Nova', 'Betano', 'GN', '2026-08-10')],
    cadastro: [cad('Velha', 'Betano', 'GN', '2026-03-10'), cad('Nova', 'Betano', 'GN', '2026-08-10')],
    precos: [
      { id: 1, fornecedor: 'GN', casa: 'Betano', valor: 850, vigente_desde: '2026-01-01' },
      { id: 2, fornecedor: 'GN', casa: 'Betano', valor: 950, vigente_desde: '2026-08-01' },
    ],
    periodo: periodo('2026-01-01', '2026-12-31'),
  });
  const r = API.calcCostFiltered('overview');
  ok(r.costConta === 1800, 'as duas contas somam 850+950=1800, veio ' + r.costConta);
  ok(r.nContas === 2, 'deveria contar 2 contas, veio ' + r.nContas);
}

// N5. Conta com custo PROPRIO num par SEM preco nenhum existe e conta. Antes da
// Fatia 2 o laco percorria os pares COM preco, e uma conta assim seria invisivel.
{
  API.set({
    custos: {},
    dados: [bilhete('Solta', 'Pinnacle', 'GN', '2026-09-01')],
    cadastro: [Object.assign(cad('Solta', 'Pinnacle', 'GN', '2026-09-01'), { custo: 400 })],
    precos: [],
    periodo: periodo('2026-09-01', '2026-09-30'),
  });
  const r = API.calcCostFiltered('overview');
  ok(r.costConta === 400, 'conta com custo proprio sem preco de par deveria custar 400, veio ' + r.costConta);
  ok(r.nContas === 1, 'e deveria ser contada, veio ' + r.nContas);
}

// N6. Preco AGENDADO para o futuro nao muda o que a conta ja comprada custou.
{
  API.set({
    custos: {},
    dados: [bilhete('Betano1', 'Betano', 'GN', '2026-09-01')],
    cadastro: [cad('Betano1', 'Betano', 'GN', '2026-09-01')],
    precos: [
      { id: 1, fornecedor: 'GN', casa: 'Betano', valor: 500, vigente_desde: '2026-01-01' },
      { id: 2, fornecedor: 'GN', casa: 'Betano', valor: 3000, vigente_desde: '2099-01-01' },
    ],
    periodo: periodo('2026-09-01', '2026-09-30'),
  });
  ok(API.calcCostFiltered('overview').costConta === 500,
     'preco futuro nao pode encarecer conta ja comprada');
}

// ── R. RENOVAÇÕES (s381): cada pagamento cobra no mês DELE ──────────────────
// Conta comprada em julho por 600 e renovada duas vezes em setembro: no DIA 1º (300) e
// no dia 30 (50). As datas nas BORDAS do mês são de propósito: um `>` no lugar do `>=`
// perderia a primeira, e um `<` no lugar do `<=`, a segunda.
const comRen = (c, ren) => Object.assign(c, { ren });
{
  const cfg = {
    custos: { 'GN||Betano': 600 },
    dados: [bilhete('B1', 'Betano', 'GN', '2026-07-10'), bilhete('B1', 'Betano', 'GN', '2026-09-15')],
    cadastro: [comRen(cad('B1', 'Betano', 'GN', '2026-07-10'),
      [{ id: 'a', valor: 300, data: '2026-09-01' }, { id: 'b', valor: 50, data: '2026-09-30' }])],
  };
  const mes = (de, ate) => { API.set({ ...cfg, periodo: periodo(de, ate) }); return API.calcCostFiltered('overview'); };
  const jul = mes('2026-07-01', '2026-07-31'), ago = mes('2026-08-01', '2026-08-31'), set = mes('2026-09-01', '2026-09-30');
  ok(jul.costConta === 600, 'R1. julho cobra so a compra, veio ' + jul.costConta);
  ok(ago.costConta === 0, 'R1. agosto nao tem pagamento nenhum, veio ' + ago.costConta);
  ok(set.costConta === 350, 'R1. setembro cobra as DUAS renovacoes (bordas do mes), veio ' + set.costConta);
  ok(set.nContas === 1, 'R1. a conta renovada conta como 1 conta no mes, veio ' + set.nContas);
  const out = mes('2026-10-01', '2026-10-31');
  ok(out.costConta === 0, 'R1. o mes SEGUINTE as renovacoes nao recobra nada, veio ' + out.costConta);
  API.set({ ...cfg });
  const tudo = API.calcCostFiltered('overview').costConta;
  ok(tudo === 950 && jul.costConta + ago.costConta + set.costConta === tudo,
     'R1. a regua continua SOMANDO: meses ' + (jul.costConta + ago.costConta + set.costConta) + ' x tudo ' + tudo);
}

// R2. Conta sem preco de compra, so com renovacao: o dinheiro da renovacao saiu e cobra.
{
  API.set({
    custos: {},
    dados: [bilhete('B1', 'Betano', 'GN', '2026-07-10')],
    cadastro: [comRen(cad('B1', 'Betano', 'GN', '2026-07-10'), [{ id: 'a', valor: 200, data: '2026-09-05' }])],
    periodo: periodo('2026-09-01', '2026-09-30'),
  });
  ok(API.calcCostFiltered('overview').costConta === 200, 'R2. renovacao cobra mesmo sem preco de compra');
}

// R3. Filtro de CASA recorta a renovacao junto com a conta.
{
  API.set({
    custos: { 'GN||Betano': 600 },
    dados: [bilhete('B1', 'Betano', 'GN', '2026-07-10')],
    cadastro: [comRen(cad('B1', 'Betano', 'GN', '2026-07-10'), [{ id: 'a', valor: 300, data: '2026-09-05' }])],
    periodo: periodo('2026-09-01', '2026-09-30'), ms: { ca_overview: ['Bet365'] },
  });
  ok(API.calcCostFiltered('overview').costConta === 0, 'R3. filtrar outra casa tira a renovacao desta');
}

// R4. ESTOQUE (contas em operacao): a conta viva vale compra + renovacoes JA pagas.
// Renovacao agendada no futuro ainda nao saiu do bolso e nao entra.
{
  API.set({
    custos: { 'GN||Betano': 600 },
    dados: [bilhete('B1', 'Betano', 'GN', '2026-07-10')],
    cadastro: [comRen(cad('B1', 'Betano', 'GN', '2026-07-10'),
      [{ id: 'a', valor: 300, data: '2026-08-05' }, { id: 'f', valor: 999, data: '2099-01-01' }])],
  });
  const op = API.calcContasEmOperacao('overview');
  ok(op.total === 900, 'R4. estoque = compra 600 + renovacao paga 300 (sem a futura), veio ' + op.total);
}

// R5. A carga do cadastro normaliza: valor em string passa pelo parseNum (1.200 e
// milhar, nao 1,2) e item sem data ou sem valor fica de fora (nao ha mes a que pertencer).
{
  const r = API._renovacoesDoCadastro([
    { id: 'a', valor: '1.200', data: '2026-09-10' },
    { id: 'b', valor: 10 },
    { id: 'c', valor: 0, data: '2026-09-10' },
  ]);
  ok(r.length === 1, 'R5. so a renovacao valida entra, vieram ' + r.length);
  ok(r[0] && r[0].valor === 1200, 'R5. "1.200" e milhar, veio ' + (r[0] && r[0].valor));
  ok(API._renovacoesDoCadastro(null).length === 0, 'R5. cadastro sem lista vira lista vazia');
}

if (falhas) { console.error(LF + falhas + ' verificação(ões) falharam.'); process.exit(1); }
console.log('custo_janela_vida.mjs: OK');
