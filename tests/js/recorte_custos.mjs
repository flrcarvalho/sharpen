// O RECORTE da tela de Custos (s348) — "Tudo" tem de significar tudo.
//
// Nasceu de um defeito medido comparando a tela antiga com a nova: com «Tudo»
// ativo a aba Contas somava R$ 0 e a tela antiga somava R$ 29.400, com o MESMO
// dado. A causa não era o dado, era o recorte — `_c2range` caía no mês corrente
// quando `_selRange` devolve null, e null é justamente o que "Tudo" devolve.
//
// O rótulo prometia a série inteira e o número entregava um mês. É a mesma família
// dos outros defeitos desta frente: rótulo e número discordando sem dar erro.
//
// Executa as funções RECORTADAS do `custos2.js` de produção, mais o `_selRange`
// REAL do `filters.js` — dublá-lo esconderia a metade que traduz o botão escolhido
// em {from,to}, que é onde o defeito morava.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const AQUI = dirname(fileURLToPath(import.meta.url));
const RAIZ = join(AQUI, '..', '..');
const BASE = join(RAIZ, 'app', 'static', 'dash', 'assets', 'js');
// ALVO_CUSTOS2 existe para a prova por MUTAÇÃO.
const CUSTOS2 = readFileSync(process.env.ALVO_CUSTOS2 || join(BASE, 'charts', 'custos2.js'), 'utf8');
const FILTROS = readFileSync(join(BASE, 'filters.js'), 'utf8');
const APP = readFileSync(join(BASE, 'app.js'), 'utf8');
const GESTAO = readFileSync(join(BASE, 'charts', 'gestao.js'), 'utf8');
const LF = '\n';

let falhas = 0;
const ok = (cond, msg) => { if (!cond) { console.error('  ✗ ' + msg); falhas++; } };

const recorteFn = (src, nome, arq) => {
  const m = src.match(new RegExp('^function ' + nome + '\\([^)]*\\)\\{[\\s\\S]*?^\\}', 'm'));
  if (!m) throw new Error('não achei a função ' + nome + ' no ' + arq);
  return m[0];
};

const FONTE = [
  ...['_c2meses', '_c2primeiraData', '_c2range', '_c2num'].map(n => recorteFn(CUSTOS2, n, 'custos2.js')),
  ...['_ymd', '_today', 'gfs', '_selRange'].map(n => recorteFn(FILTROS, n, 'filters.js')),
  // REAIS do gestao.js (s362): o comeco de «Tudo» passou a sair do `_dataPagamento`
  // sobre o `_contaVida`, que sao os do KPI. Dubla-los aqui esconderia justamente a
  // camada que faz a 1a APOSTA abrir o periodo quando o cadastro chegou depois dela.
  ...['normForn', '_buildContaVida', '_dataPagamento', '_renovacoesNaJanela'].map(n => recorteFn(GESTAO, n, 'gestao.js')),
  // `parseNum` REAL do app.js: é ele que o `_c2num` passou a chamar (s358, etapa 5b).
  // Dublar aqui esconderia justamente a régua de milhar que o caso 4 abaixo prova.
  recorteFn(APP, 'parseNum', 'app.js'),
].join(LF);

const API = new Function(`
  const FS = {};
  const window = { __dono: 'Feca' };
  let _contasVida = null, _contaVida = null, ctData = {}, cgData = [];
  let DADOS = [], DADOS_ABERTAS = [];
  ${FONTE}
  return {
    set(cfg) {
      _contasVida = cfg.cadastro || null; ctData = cfg.custos || {}; cgData = cfg.gerais || [];
      DADOS = cfg.dados || []; DADOS_ABERTAS = cfg.abertas || [];
      _contaVida = null;                  // refeito pelo _buildContaVida REAL
      for (const k of Object.keys(FS)) delete FS[k];
      if (cfg.periodo) FS.custos_v2 = Object.assign(gfs('custos_v2'), cfg.periodo);
    },
    _c2range, _c2primeiraData, _c2num,
  };
`)();

const hoje = (() => { const d = new Date(); return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); })();
const mesCorrente = hoje.slice(0, 7) + '-01';
const cad = (adq) => ({ casa: 'Bet365', conta: 'c' + adq, fornecedor: 'GN', adquirida_em: adq, arquivada_em: '', arquivado: false });
// "Tudo" no filters.js é o estado ZERADO: sem datas e sem atalho.
const TUDO = { df: '', dt: '', qd: 0, qt: '' };

// ── 1. "Tudo" começa na PRIMEIRA compra, não no mês corrente ─────────────────
{
  API.set({ cadastro: [cad('2026-01-18'), cad('2026-05-02')], periodo: TUDO });
  const r = API._c2range();
  ok(r.de === '2026-01-18', '«Tudo» deveria começar em 2026-01-18, veio ' + r.de);
  ok(r.ate === hoje, '«Tudo» vai até hoje, veio ' + r.ate);
  ok(r.meses.length > 1, '«Tudo» tem de cobrir mais de um mês, veio ' + r.meses.length);
}

// ── 2. O mês de custo de tipster também conta como primeiro dado ─────────────
// Quem só lança tipster (sem conta cadastrada) não pode cair no mês corrente.
{
  API.set({ custos: { Ze: { '2026-03': '250,00', '2026-07': '250,00' } }, periodo: TUDO });
  ok(API._c2primeiraData() === '2026-03-01', 'o 1º mês de tipster deveria abrir o período, veio ' + API._c2primeiraData());
  ok(API._c2range().de === '2026-03-01', '«Tudo» deveria começar em 2026-03-01');
}

// ── 3. E o custo geral também ────────────────────────────────────────────────
{
  API.set({ gerais: [{ id: 1, tipo: 'VPN', values: { '2026-02': '39,00' } }], periodo: TUDO });
  ok(API._c2primeiraData() === '2026-02-01', 'o 1º mês de geral deveria abrir o período, veio ' + API._c2primeiraData());
}

// ── 4. A MAIS ANTIGA das três fontes é que manda ─────────────────────────────
{
  API.set({
    cadastro: [cad('2026-06-01')],
    custos: { Ze: { '2026-04': '250,00' } },
    gerais: [{ id: 1, tipo: 'VPN', values: { '2026-02': '39,00' } }],
    periodo: TUDO,
  });
  ok(API._c2primeiraData() === '2026-02-01', 'a mais antiga das três fontes manda, veio ' + API._c2primeiraData());
}

// ── 4b. A 1ª APOSTA abre o período quando o cadastro chegou depois (s362) ──
// O comeco de «Tudo» passou a sair do `_dataPagamento` sobre o `_contaVida`, que sao
// os do KPI. Lendo `adquirida_em` cru, como antes, a conta migrada -- cujo cadastro
// nasceu de backfill DEPOIS da aposta -- fazia «Tudo» comecar tarde e deixava de fora
// justamente os meses mais antigos, que sao os que so existem em bilhete.
{
  API.set({
    cadastro: [{ casa: 'Bet365', conta: 'velha', fornecedor: 'GN',
                 adquirida_em: '2026-06-01', arquivada_em: '', arquivado: false }],
    dados: [{ casa: 'Bet365', conta: 'velha', fornecedor: 'GN', data: '2026-02-09', operador: 'Feca' }],
    periodo: TUDO,
  });
  ok(API._c2primeiraData() === '2026-02-09',
     'a 1ª aposta deveria abrir o período, veio ' + API._c2primeiraData());
}

// ── 4c. Conta que SÓ existe em bilhete também abre o período (s362) ──
// Sao 130 na base do Feca. Varrendo so o cadastro elas nao existiam para o recorte,
// e o KPI as cobrava -- o total dizia uma coisa e a janela que o produz, outra.
{
  API.set({
    abertas: [{ casa: 'Superbet', conta: 'so-bilhete', fornecedor: 'JC', data: '2026-01-05', operador: 'Feca' }],
    periodo: TUDO,
  });
  ok(API._c2primeiraData() === '2026-01-05',
     'conta so-de-bilhete deveria abrir o período, veio ' + API._c2primeiraData());
}

// ── 5. Sem dado nenhum, "Tudo" é o mês corrente ──────────────────────────────
// É o único caso em que "tudo" e "este mês" são a mesma coisa — e aí o rótulo não
// mente, porque não há nada antes.
{
  API.set({ periodo: TUDO });
  ok(API._c2primeiraData() === '', 'sem dado, não há primeira data');
  ok(API._c2range().de === mesCorrente, 'sem dado, «Tudo» cai no mês corrente, veio ' + API._c2range().de);
}

// ── 6. Período escolhido MANDA sobre tudo isso ───────────────────────────────
// O dado velho não pode puxar o recorte para trás quando o dono escolheu um mês.
{
  API.set({ cadastro: [cad('2026-01-18')], periodo: { df: '2026-09-01', dt: '2026-09-30', qd: 0, qt: 'mtd' } });
  const r = API._c2range();
  ok(r.de === '2026-09-01' && r.ate === '2026-09-30', 'o período escolhido manda, veio ' + r.de + '→' + r.ate);
  ok(r.meses.length === 1, 'um mês escolhido é um mês, veio ' + r.meses.length);
  ok(r.mesRef === '2026-09', 'o mês de referência é o último do recorte, veio ' + r.mesRef);
}

// ── 7. O atalho de dias também manda ─────────────────────────────────────────
{
  API.set({ cadastro: [cad('2020-01-01')], periodo: { df: '', dt: '', qd: 30, qt: '' } });
  const r = API._c2range();
  ok(r.ate === hoje, '30d termina hoje, veio ' + r.ate);
  ok(r.de > '2020-01-01', '30d não pode voltar a 2020 só porque existe conta de lá, veio ' + r.de);
}

// ── 8. `mesRef` é sempre o ÚLTIMO mês do recorte ─────────────────────────────
// É ele que as abas Tipsters e Gerais listam; pegar o primeiro faria a tela pedir
// o lançamento de um mês que já passou.
{
  API.set({ cadastro: [cad('2026-01-18')], periodo: TUDO });
  const r = API._c2range();
  ok(r.mesRef === r.meses[r.meses.length - 1], 'mesRef tem de ser o último mês do recorte');
  ok(r.mesRef === hoje.slice(0, 7), 'com «Tudo» o mês de referência é o corrente, veio ' + r.mesRef);
}

// ── 4. `_c2num` lê pela régua do projeto, não por uma própria (s358, 5b) ────
// A régua antiga apagava TODO ponto antes de converter, então decidia milhar pela
// PRESENÇA do separador em vez da forma do número. Medido na base real: `179.90` em
// 2 linhas (`Só Chutes` jul/26 e `Curva Rápida` jul/26) virava 17.990,00 aqui e valia
// 179,90 na Visão Geral — o total do sistema mudava de R$ 30.884 para R$ 66.504
// conforme a tela que lia.
{
  const casos = [
    ['179.90', 179.9, 'um separador com 2 digitos depois e DECIMAL'],
    ['1.234', 1234, 'grupo de 3 digitos e MILHAR'],
    ['1.234,56', 1234.56, 'ponto de milhar com virgula decimal'],
    ['250,00', 250, 'virgula decimal'],
    ['1.234.567', 1234567, 'dois grupos de 3 seguem sendo milhar'],
    ['600', 600, 'inteiro puro'],
    ['', 0, 'vazio vale 0'],
    [null, 0, 'null vale 0'],
  ];
  for (const [entrada, esperado, porque] of casos) {
    const veio = API._c2num(entrada);
    ok(Math.abs(veio - esperado) < 0.0001,
       '_c2num(' + JSON.stringify(entrada) + ') deveria dar ' + esperado + ' (' + porque + '), veio ' + veio);
  }
}

if (falhas) { console.error(LF + falhas + ' verificação(ões) falharam.'); process.exit(1); }
console.log('recorte_custos.mjs: OK');
