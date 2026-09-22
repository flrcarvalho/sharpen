// A RÉGUA ÚNICA de custo de conta (s362) — a aba Contas e o KPI medem o mesmo.
//
// Desde a s358 as duas respondem LANÇAMENTO ("o que saiu do bolso no recorte"), mas
// cada uma derivava a resposta por um caminho: `_c2contas` varria o CADASTRO
// (`_contasVida`) e datava por `adquirida_em` cru; `calcCostFiltered` varria cadastro
// ∪ BILHETE (`_contaVida`) e datava por `_dataPagamento`. Nas 8 bases medidas os dois
// davam o mesmo número — por sorte do dado, não por construção: toda conta com custo
// tinha cadastro e `adquirida_em` anterior à 1ª aposta, porque foi o backfill que a
// deduziu assim.
//
// Este arquivo exercita justamente os dois casos em que a sorte acaba, e exige que o
// TOTAL da aba seja igual ao do KPI. Executa as funções RECORTADAS do `custos2.js` e
// do `gestao.js` de produção, mais o `_selRange` REAL do `filters.js` e o `parseNum`
// REAL do `app.js` — nenhuma regra é reimplementada aqui.
//
// O que NÃO está coberto: o render da tabela (as colunas, a origem do valor, o
// rodapé) e o recorte por Casa/Fornecedor/Operador, que têm gate próprio no
// `test_recorte_custos.py`. Aqui é só a igualdade dos dois números.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const AQUI = dirname(fileURLToPath(import.meta.url));
const RAIZ = join(AQUI, '..', '..');
const BASE = join(RAIZ, 'app', 'static', 'dash', 'assets', 'js');
// ALVO_* existem para a prova por MUTAÇÃO: o .py copia o arquivo, estraga a cópia e
// aponta a variável para ela, exigindo que este gate fique VERMELHO.
const CUSTOS2 = readFileSync(process.env.ALVO_CUSTOS2 || join(BASE, 'charts', 'custos2.js'), 'utf8');
const GESTAO = readFileSync(process.env.ALVO_GESTAO || join(BASE, 'charts', 'gestao.js'), 'utf8');
const FILTROS = readFileSync(join(BASE, 'filters.js'), 'utf8');
const APP = readFileSync(join(BASE, 'app.js'), 'utf8');
const LF = '\n';

let falhas = 0;
const ok = (cond, msg) => { if (!cond) { console.error('  ✗ ' + msg); falhas++; } };
// `eq` existe porque `ok(f() === x, 'veio ' + f())` chama `f` DUAS vezes: a mensagem
// imprime o valor da segunda, que pode nao ser o que reprovou -- e foi o que
// aconteceu com o `_contaVida` construido preguicosamente pela chamada anterior.
const eq = (obtido, esperado, msg) => ok(obtido === esperado, msg + ', veio ' + obtido);

// Função de UMA linha é tentada PRIMEIRO: o recorte multilinha vai até o próximo `}` na
// coluna 0, então numa one-liner (`normForn`) ele engole tudo o que houver até a próxima
// função multilinha — inclusive declarações de topo de arquivo, que nascem duplicadas no
// harness. Aqui ainda não tinha mordido; no `bookies_custo.mjs` mordeu (s364).
const recorteFn = (src, nome, arq) => {
  const uma = src.match(new RegExp('^function ' + nome + '\\([^)]*\\)\\{.*\\}$', 'm'));
  if (uma) return uma[0];
  const m = src.match(new RegExp('^function ' + nome + '\\([^)]*\\)\\{[\\s\\S]*?^\\}', 'm'));
  if (!m) throw new Error('não achei a função ' + nome + ' no ' + arq);
  return m[0];
};

const FONTE = [
  ...['normForn', '_buildContaVida', '_precoVigenteEm', '_degrausPreco', '_dataDoPreco',
      '_custoDaConta', '_temPrecoConta', '_dataPagamento', '_renovacoesNaJanela', '_custoNaJanela', 'calcCostFiltered']
    .map(n => recorteFn(GESTAO, n, 'gestao.js')),
  ...['_c2num', '_c2meses', '_c2primeiraData', '_c2range', '_c2sel', '_c2opDaConta',
      '_c2passa', '_c2contas'].map(n => recorteFn(CUSTOS2, n, 'custos2.js')),
  ...['_ymd', '_today', 'gfs', '_selRange', 'msGet'].map(n => recorteFn(FILTROS, n, 'filters.js')),
  recorteFn(APP, 'parseNum', 'app.js'),
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
      custoData = cfg.custos || {}; _contasVida = cfg.cadastro || null;
      ctData = {}; cgData = []; _precosForn = cfg.precos || [];
      _contaVida = null;                   // refeito pelo _buildContaVida REAL
      for (const k of Object.keys(FS)) delete FS[k];
      for (const k of Object.keys(MSS)) delete MSS[k];
      if (cfg.periodo) FS.custos_v2 = Object.assign(gfs('custos_v2'), cfg.periodo);
      if (cfg.periodo) FS.overview = Object.assign(gfs('overview'), cfg.periodo);
    },
    // O total da ABA (o que o rodapé e o KPI "Contas" da tela somam).
    totalAba() { return _c2contas().reduce((a, c) => a + c.custo, 0); },
    linhasAba() { return _c2contas(); },
    // O total do KPI da Visão Geral, que desce no P/L Líquido.
    totalKpi() { return calcCostFiltered('overview').costConta; },
  };
`)();

const TUDO = { df: '', dt: '', qd: 0, qt: '' };
const bilhete = (casa, conta, forn, data) => ({ casa, conta, fornecedor: forn, data, operador: 'Feca' });
const cad = (casa, conta, forn, adq, extra) => Object.assign(
  { casa, conta, fornecedor: forn, adquirida_em: adq, arquivada_em: '', arquivado: false, custo: null }, extra || {});

// ── 1. O caso normal: cadastro antes da 1ª aposta ────────────────────────────
// A linha de base. Se os dois já discordassem aqui, nada abaixo teria sentido.
{
  API.set({
    cadastro: [cad('Bet365', 'c1', 'GN', '2026-03-01')],
    dados: [bilhete('Bet365', 'c1', 'GN', '2026-04-10')],
    custos: { 'GN||Bet365': 900 }, periodo: TUDO,
  });
  eq(API.totalAba(), 900, 'a aba deveria somar 900');
  eq(API.totalKpi(), 900, 'o KPI deveria somar 900');
}

// ── 2. `adquirida_em` DEPOIS da 1ª aposta ────────────────────────────────────
// O dono cadastrou tarde uma conta que já apostava. `_dataPagamento` manda a 1ª
// aposta (piso medido: a conta existia ali); ler `adquirida_em` cru datava a conta
// num mês em que ela não foi paga. Num recorte de mês, isso é R$ 900 cobrados no
// mês errado nos DOIS sentidos — some de um e aparece no outro.
{
  const cfg = {
    cadastro: [cad('Bet365', 'c1', 'GN', '2026-08-20')],
    dados: [bilhete('Bet365', 'c1', 'GN', '2026-02-09')],
    custos: { 'GN||Bet365': 900 },
  };
  API.set(Object.assign({ periodo: { df: '2026-02-01', dt: '2026-02-28', qd: 0, qt: '' } }, cfg));
  eq(API.totalAba(), 900, 'fev/26 é o mês do pagamento; a aba');
  { const a = API.totalAba(), k = API.totalKpi();
    ok(a === k, 'aba e KPI têm de bater em fev/26: ' + a + ' × ' + k); }

  API.set(Object.assign({ periodo: { df: '2026-08-01', dt: '2026-08-31', qd: 0, qt: '' } }, cfg));
  eq(API.totalAba(), 0, 'ago/26 não pagou nada; a aba');
  { const a = API.totalAba(), k = API.totalKpi();
    ok(a === k, 'aba e KPI têm de bater em ago/26: ' + a + ' × ' + k); }
}

// ── 3. Conta que SÓ existe em bilhete ────────────────────────────────────────
// São 130 na base do Feca. Varrendo só o cadastro, a tela de LANÇAMENTO escondia
// uma conta que o KPI cobrava: o total dizia 1.500 e a tabela logo abaixo, 600.
// É o sintoma que o CLAUDE.md descreve — "o KPI não bate com a soma da tabela".
{
  API.set({
    cadastro: [cad('Bet365', 'c1', 'GN', '2026-03-01')],
    dados: [bilhete('Bet365', 'c1', 'GN', '2026-03-05'),
            bilhete('Superbet', 'orfa', 'JC', '2026-03-07')],
    custos: { 'GN||Bet365': 600, 'JC||Superbet': 900 }, periodo: TUDO,
  });
  eq(API.totalKpi(), 1500, 'o KPI cobra as duas');
  eq(API.totalAba(), 1500, 'a aba tem de mostrar as duas');
  const orfa = API.linhasAba().find(c => c.conta === 'orfa');
  ok(!!orfa, 'a conta só-de-bilhete tem de ter linha na tela onde se lança');
  ok(orfa && orfa.id === null, 'conta sem cadastro chega com id null (a tela a marca como não-editável)');
}

// ── 4. O degrau do fornecedor segue a data da COMPRA, não a do pagamento ─────
// São perguntas diferentes, e é por isso que `_dataDoPreco` existe separado. A conta
// foi comprada em 2026-03 (cadastro), quando o preço era 600; o reajuste de 900 veio
// depois e não é retroativo. O rótulo da origem tem de citar o MESMO degrau que entrou
// no número — a lição da Fatia 1.
{
  API.set({
    cadastro: [cad('Bet365', 'c1', 'GN', '2026-03-01')],
    dados: [bilhete('Bet365', 'c1', 'GN', '2026-03-05')],
    precos: [{ fornecedor: 'GN', casa: 'Bet365', valor: 600, vigente_desde: '2026-01-01' },
             { fornecedor: 'GN', casa: 'Bet365', valor: 900, vigente_desde: '2026-07-01' }],
    custos: { 'GN||Bet365': 900 }, periodo: TUDO,
  });
  const l = API.linhasAba()[0];
  ok(l && l.custo === 600, 'preço novo não é retroativo; veio ' + (l && l.custo));
  ok(l && l.degrau && l.degrau.valor === 600,
     'a origem exibida tem de ser o degrau que gerou o número, veio ' + (l && l.degrau && l.degrau.valor));
  ok(API.totalAba() === API.totalKpi(), 'aba e KPI seguem batendo com degrau, ' + API.totalAba() + ' × ' + API.totalKpi());
}

// ── 4b. O degrau exibido é o que GEROU o número, e as duas datas divergem aqui ─
// Cadastro tardio (ago) de uma conta que aposta desde fev, com reajuste em julho no
// meio. A data da COMPRA (`_dataDoPreco` = ago) pega o degrau de 900; a do PAGAMENTO
// (`_dataPagamento` = fev) pegaria o de 600. O custo sai da primeira, entao a origem
// exibida tem de sair da primeira tambem -- senao a celula diz "600 desde jan" ao lado
// de um valor de 900, que e a divergencia rotulo x numero da Fatia 1.
{
  API.set({
    cadastro: [cad('Bet365', 'c1', 'GN', '2026-08-20')],
    dados: [bilhete('Bet365', 'c1', 'GN', '2026-02-09')],
    precos: [{ fornecedor: 'GN', casa: 'Bet365', valor: 600, vigente_desde: '2026-01-01' },
             { fornecedor: 'GN', casa: 'Bet365', valor: 900, vigente_desde: '2026-07-01' }],
    custos: { 'GN||Bet365': 111 }, periodo: TUDO,
  });
  const l = API.linhasAba()[0];
  eq(l && l.custo, 900, 'o custo sai do degrau da data de COMPRA');
  ok(l && l.degrau && l.degrau.valor === l.custo,
     'a origem exibida tem de ser o degrau que gerou o número: degrau '
     + (l && l.degrau && l.degrau.valor) + ' × custo ' + (l && l.custo));
}

// ── 4c. `adquirida_em` DECLARADO antes da 1ª aposta manda, e manda no MÊS ──
// A 1a camada do `_dataPagamento`: o dono declarando a compra sabe mais que a base.
// A checagem aqui e ABSOLUTA de proposito -- comparar aba com KPI nao pega uma
// mutacao no `_dataPagamento`, porque ela move os DOIS numeros para o mesmo mes errado.
{
  const cfg = {
    cadastro: [cad('Bet365', 'c1', 'GN', '2026-02-10')],
    dados: [bilhete('Bet365', 'c1', 'GN', '2026-04-02')],
    custos: { 'GN||Bet365': 900 },
  };
  API.set(Object.assign({ periodo: { df: '2026-02-01', dt: '2026-02-28', qd: 0, qt: '' } }, cfg));
  eq(API.totalAba(), 900, 'fev/26 e o mes DECLARADO da compra; a aba');
  eq(API.totalKpi(), 900, 'fev/26 e o mes DECLARADO da compra; o KPI');

  API.set(Object.assign({ periodo: { df: '2026-04-01', dt: '2026-04-30', qd: 0, qt: '' } }, cfg));
  eq(API.totalAba(), 0, 'abr/26 e so a 1a aposta, nao a compra; a aba');
  eq(API.totalKpi(), 0, 'abr/26 e so a 1a aposta, nao a compra; o KPI');
}

// ── 4d. Sem cadastro, a 1ª aposta é o piso e data a conta ──────────────
// 3a camada. Tambem absoluta: e a que segura a conta migrada, que nao tem cadastro.
{
  const cfg = {
    dados: [bilhete('Bet365', 'so-bilhete', 'GN', '2026-05-14')],
    custos: { 'GN||Bet365': 900 },
  };
  API.set(Object.assign({ periodo: { df: '2026-05-01', dt: '2026-05-31', qd: 0, qt: '' } }, cfg));
  eq(API.totalAba(), 900, 'mai/26 e a 1a aposta da conta sem cadastro; a aba');
  eq(API.totalKpi(), 900, 'mai/26 e a 1a aposta da conta sem cadastro; o KPI');

  API.set(Object.assign({ periodo: { df: '2026-06-01', dt: '2026-06-30', qd: 0, qt: '' } }, cfg));
  eq(API.totalAba(), 0, 'jun/26 nao pagou nada; a aba');
}

// ── 5. Custo PRÓPRIO da conta ganha do fornecedor, nos dois lados ────────────
{
  API.set({
    cadastro: [cad('Bet365', 'c1', 'GN', '2026-03-01', { custo: 1200 })],
    dados: [bilhete('Bet365', 'c1', 'GN', '2026-03-05')],
    custos: { 'GN||Bet365': 900 }, periodo: TUDO,
  });
  eq(API.totalAba(), 1200, 'o custo próprio manda na aba');
  eq(API.totalKpi(), 1200, 'o custo próprio manda no KPI');
}

// ── 6. Conta sem data nenhuma não cobra, e não aparece — nos dois lados ──────
// Cadastro sem `adquirida_em` e sem aposta: não há mês a que ela pertença. Inventar
// um seria datar por estimativa, que é dado inventado (CLAUDE.md).
{
  API.set({
    cadastro: [cad('Bet365', 'c1', 'GN', ''), cad('Betano', 'c2', 'JC', '2026-03-01')],
    dados: [bilhete('Betano', 'c2', 'JC', '2026-03-05')],
    custos: { 'GN||Bet365': 900, 'JC||Betano': 600 }, periodo: TUDO,
  });
  eq(API.totalAba(), 600, 'conta sem data não cobra na aba');
  eq(API.totalKpi(), 600, 'conta sem data não cobra no KPI');
  ok(!API.linhasAba().some(c => c.conta === 'c1'), 'conta sem data não vira linha datada');
}

// ── 7. A igualdade vale MÊS A MÊS, não só no total ───────────────────────────
// Totais iguais com meses trocados é o defeito que o MTD esconde: some de um mês e
// aparece noutro, e a soma do ano continua batendo.
{
  const cfg = {
    cadastro: [cad('Bet365', 'a', 'GN', '2026-02-10'), cad('Betano', 'b', 'JC', '2026-09-01')],
    dados: [bilhete('Bet365', 'a', 'GN', '2026-02-11'), bilhete('Betano', 'b', 'JC', '2026-04-02')],
    custos: { 'GN||Bet365': 900, 'JC||Betano': 600 },
  };
  for (const [de, ate, rotulo] of [['2026-02-01', '2026-02-28', 'fev'],
                                   ['2026-04-01', '2026-04-30', 'abr'],
                                   ['2026-09-01', '2026-09-30', 'set']]){
    API.set(Object.assign({ periodo: { df: de, dt: ate, qd: 0, qt: '' } }, cfg));
    const a = API.totalAba(), k = API.totalKpi();
    ok(a === k, rotulo + '/26: aba ' + a + ' × KPI ' + k);
  }
}

// ── R. RENOVAÇÃO (s381): a tabela ganha uma LINHA por pagamento ─────────────
// Conta comprada em março e renovada em setembro. Em setembro o KPI cobra só a
// renovação, e a tabela tem de mostrar exatamente essa linha — sem ela, o KPI desconta
// um valor que a tela de lançamento não mostra (o sintoma do CLAUDE.md).
{
  const cfg = {
    cadastro: [cad('Bet365', 'c1', 'GN', '2026-03-01',
      { ren: [{ id: 'a', valor: 350, data: '2026-09-10' }, { id: 'b', valor: 90, data: '2026-06-02' }] })],
    dados: [bilhete('Bet365', 'c1', 'GN', '2026-03-05')],
    custos: { 'GN||Bet365': 900 },
  };
  API.set(Object.assign({ periodo: { df: '2026-09-01', dt: '2026-09-30', qd: 0, qt: '' } }, cfg));
  eq(API.totalKpi(), 350, 'set/26: o KPI cobra so a renovacao');
  eq(API.totalAba(), 350, 'set/26: a aba soma o mesmo');
  const ls = API.linhasAba();
  eq(ls.length, 1, 'set/26: uma linha, a da renovacao');
  ok(ls[0] && ls[0].renovacao === true && ls[0].data === '2026-09-10',
     'set/26: a linha e a renovacao, datada no dia dela');
  API.set(Object.assign({ periodo: TUDO }, cfg));
  { const a = API.totalAba(), k = API.totalKpi();
    ok(a === 1340 && a === k, 'Tudo: compra + duas renovacoes, aba ' + a + ' x KPI ' + k); }
  eq(API.linhasAba().length, 3, 'Tudo: tres linhas (compra e duas renovacoes)');
}

if (falhas) { console.error(LF + falhas + ' verificação(ões) falharam.'); process.exit(1); }
console.log('custos_regua_unica.mjs: OK');
