// Prova por EXECUÇÃO das DUAS réguas de custo de conta (s322 + s358).
//
// O arquivo nasceu na s322 provando a JANELA DE VIDA. Na s358 a régua do P/L virou
// CAIXA, e a janela de vida continuou existindo para outra pergunta. As duas convivem,
// e por isso as duas são provadas aqui.
//
//   modo 'pago' (o P/L)  → "quanto saiu do bolso no recorte". Cada conta cobra UMA vez,
//        no dia do pagamento. SOMA: os 12 meses dão o ano.
//   modo 'vivo' (parque) → "quanto vale o que está rodando". Toda conta viva no recorte
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

let falhas = 0;
const ok = (cond, msg) => { if (!cond) { console.error('FALHOU: ' + msg); falhas++; } };

// Recorta uma função de topo de nível: o `}` de fechamento é o único na coluna 0.
const recorteFn = (src, nome, arq) => {
  const m = src.match(new RegExp('^function ' + nome + '\\([^)]*\\)\\{[\\s\\S]*?^\\}', 'm'));
  if (!m) throw new Error('não achei a função ' + nome + ' no ' + arq);
  return m[0];
};

const FONTE = [
  ...['normForn', '_buildContaVida', '_precoVigenteEm', '_degrausPreco', '_custoDaConta',
      '_dataPagamento', '_custoNaJanela', 'calcCostFiltered', 'calcCasaCost']
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
  let _contaVida = null, _contasVida = null, _precosForn = null;
  ${FONTE}
  return {
    set(cfg) {
      DADOS = cfg.dados || []; DADOS_ABERTAS = cfg.abertas || [];
      custoData = cfg.custos || {}; _contasVida = cfg.cadastro || null;
      _precosForn = cfg.precos || [];
      _contaVida = null;
      for (const k of Object.keys(FS)) delete FS[k];
      for (const k of Object.keys(MSS)) delete MSS[k];
      if (cfg.periodo) FS.overview = Object.assign(gfs('overview'), cfg.periodo);
      if (cfg.ms) for (const k of Object.keys(cfg.ms)) MSS[k] = new Set(cfg.ms[k]);
    },
    vida() { if (!_contaVida) _buildContaVida(); return _contaVida; },
    // O parque (Fatia 2) chama a mesma função com modo 'vivo'.
    parque(de, ate) { return _custoNaJanela(de, ate, null, null, '', 'vivo'); },
    calcCostFiltered, calcCasaCost,
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
// É a pergunta do Jaao26, que não sumiu: ela saiu do P/L e virou estoque. Mesmos dados
// do caso B, onde o custo PAGO é zero.
{
  const cfg = {
    custos: { 'GN||Betano': 1700 },
    dados: [bilhete('Betano1', 'Betano', 'GN', '2026-09-01'), bilhete('Betano1', 'Betano', 'GN', '2026-09-22')],
    cadastro: [cad('Betano1', 'Betano', 'GN', '2026-09-01')],
    periodo: periodo('2026-09-05', '2026-09-05'),
  };
  API.set(cfg);
  ok(API.calcCostFiltered('overview').costConta === 0, 'pré-condição: no dia 05 nada foi PAGO');
  const p = API.parque('2026-09-05', '2026-09-05');
  ok(p.total === 1700 && p.nContas === 1, 'o parque do dia 05 tem a conta viva (1700), veio ' + p.total);
  ok(API.parque('2026-09-28', '2026-09-28').total === 0, 'depois da última aposta a conta sai do parque');
  ok(API.parque('2026-08-20', '2026-08-25').total === 0, 'antes da compra a conta ainda não está no parque');
}

// ── M2. Conta ativa e sem aposta nenhuma fica viva até HOJE ──────────────
{
  API.set({
    custos: { 'GN||Betano': 1700 },
    dados: [], cadastro: [cad('Nova', 'Betano', 'GN', '2026-01-01')],
  });
  const v = API.vida()['GN||Betano']['Nova'];
  ok(v.fim === hoje, 'conta ativa sem aposta deveria valer até hoje (' + hoje + '), veio ' + v.fim);
  ok(API.parque('2026-01-01', hoje).total === 1700, 'e ela está no parque');
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

if (falhas) { console.error(LF + falhas + ' verificação(ões) falharam.'); process.exit(1); }
console.log('custo_janela_vida.mjs: OK');
