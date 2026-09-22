// Dado que o usuário DIGITA sobe SEMPRE para o servidor (s366).
//
// A regra do `CLAUDE.md`: nada que o usuário digita repousa no navegador. O que a
// violava era a trava anti-semeadura-parcial, que existia em TRÊS telas com a mesma
// forma — `if (serverBacked) push; else if (!hadLegacy) push;`. O terceiro caso,
// **servidor vazio + legado no navegador**, não subia NADA: a pessoa digitava um custo
// e ele ficava só na máquina, sem erro e sem aviso.
//
// Este arquivo exercita as funções de save RECORTADAS dos arquivos de produção e
// exige um POST em TODOS os estados. O estado que importa é o terceiro; os outros dois
// estão aqui para que uma mutação que quebre o caminho comum também apareça.
// A Extração saiu da trava na s381: o card dela grava o custo DA CONTA direto no
// cadastro, sem cache local, e a seção C prova isso (e que ela não toca a tabela).
//
// A outra metade da regra: o 1º envio de um navegador para um servidor sem custo vai
// com `semear:true`, e o servidor UNE em vez de substituir. Sem isso, tirar a trava
// abriria outro buraco — a máquina com menos chaves viraria a verdade e a outra adotaria
// o conjunto menor na carga seguinte. A união em si tem gate próprio, em Python
// (`tests/test_uniao_custo_semeadura.py`), porque ela é código de servidor.
//
// O que NÃO está coberto: se o POST chega ao Postgres (é o gate de Python), e o
// `localStorage` continuar sendo escrito — ele segue existindo como CACHE, de propósito,
// e o que a regra proíbe é que ele seja o único lugar.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const AQUI = dirname(fileURLToPath(import.meta.url));
const RAIZ = join(AQUI, '..', '..');
const BASE = join(RAIZ, 'app', 'static', 'dash', 'assets', 'js');
// ALVO_* existem para a prova por MUTAÇÃO: o .py copia o arquivo, estraga a cópia e
// aponta a variável para ela, exigindo que este gate fique VERMELHO.
const GESTAO = readFileSync(process.env.ALVO_GESTAO || join(BASE, 'charts', 'gestao.js'), 'utf8');
const APP = readFileSync(process.env.ALVO_APP || join(BASE, 'app.js'), 'utf8');
const EXTRACAO = readFileSync(process.env.ALVO_EXTRACAO || join(RAIZ, 'app', 'static', 'index.html'), 'utf8');

let falhas = 0;
const ok = (cond, msg) => { if (!cond) { console.error('  ✗ ' + msg); falhas++; } };
const eq = (obtido, esperado, msg) => ok(obtido === esperado, msg + ', veio ' + JSON.stringify(obtido));

const recorteFn = (src, nome, arq) => {
  const uma = src.match(new RegExp('^(?:async )?function ' + nome + '\\([^)]*\\)\\{.*\\}$', 'm'));
  if (uma) return uma[0];
  const m = src.match(new RegExp('^(?:async )?function ' + nome + '\\([^)]*\\)\\{[\\s\\S]*?^\\}', 'm'));
  if (!m) throw new Error('não achei a função ' + nome + ' no ' + arq);
  return m[0];
};
// O `index.html` é HTML: as funções vivem indentadas dentro de <script>, então o
// fecho em coluna zero não existe. Recorta pela indentação do próprio `function`.
const recorteFnHtml = (src, nome, arq) => {
  const m = src.match(new RegExp('^(\\s*)(?:async )?function ' + nome + '\\([^)]*\\) \\{[\\s\\S]*?^\\1\\}', 'm'));
  if (!m) throw new Error('não achei a função ' + nome + ' no ' + arq);
  return m[0];
};

// ── Os três saves, cada um no seu ambiente dublado ───────────────────────────
// Os dublês são RECIPIENTES (localStorage, fetch, render), nunca regra: a decisão de
// subir ou não sai inteira do código recortado.
const AMBIENTE = `
  let LS = {}, POSTS = [];
  const localStorage = {
    getItem: (k) => (k in LS ? LS[k] : null),
    setItem: (k, v) => { LS[k] = String(v); },
  };
  const fetch = (url, opt) => {
    if (opt && opt.method === 'POST') POSTS.push({ url, body: JSON.parse(opt.body) });
    return { ok: true, status: 200, catch: () => {}, then: () => ({ catch: () => {} }) };
  };
  const window = { __dono: 'Feca', __donoEfetivo: 'Feca' };
`;

const API_DASH = new Function(`
  ${AMBIENTE}
  let custoData = {}, _custoServerBacked = false, _custoHadLegacy = false;
  let ctData = {}, cgData = [];
  let _ctServerBacked = false, _ctHadLegacy = false;
  let _costState = { allForns: [], allCasas: [], contaCount: {} };
  // Efeitos de tela do saveCusto: existem para ele rodar, e não medem nada.
  function recalcCustos(){} function renderCostPies(){} function renderCustoCards(){}
  ${recorteFn(GESTAO, 'costKey', 'gestao.js')}
  ${recorteFn(GESTAO, '_custoMirror', 'gestao.js')}
  ${recorteFn(GESTAO, '_custoPush', 'gestao.js')}
  ${recorteFn(GESTAO, 'saveCusto', 'gestao.js')}
  ${recorteFn(APP, '_ctMirror', 'app.js')}
  ${recorteFn(APP, '_ctPush', 'app.js')}
  ${recorteFn(APP, 'ctSave', 'app.js')}
  return {
    estado(cfg) {
      LS = {}; POSTS = [];
      custoData = {}; ctData = {}; cgData = [];
      _custoServerBacked = cfg.serverBacked; _custoHadLegacy = cfg.hadLegacy;
      _ctServerBacked = cfg.serverBacked; _ctHadLegacy = cfg.hadLegacy;
    },
    salvaConta: () => { saveCusto('Move', 'Bet365', '950'); return POSTS.slice(); },
    salvaTipster: () => { ctData['Só Chutes'] = { '2026-09': '500' }; ctSave(); return POSTS.slice(); },
    backedConta: () => _custoServerBacked,
  };
`)();

// A Extração grava o custo DA CONTA, nunca a tabela (s381). O card escrevia em
// `custo_conta[fornecedor||casa]`, e corrigir UMA conta do Richard para R$ 916 virou a
// tabela das 25 contas dele na Superbet. Aqui não há trava de semeadura a provar: o
// valor vai direto para a linha da conta no cadastro, sem cache no navegador.
// Dublê próprio: este save ESPERA a resposta (o erro aparece no card), e o `fetch` do
// AMBIENTE devolve um thenable que nunca resolve, feito para quem dispara e esquece.
const API_EXTRACAO = new Function(`
  let POSTS = [];
  const fetch = async (url, opt) => {
    if (opt && opt.method === 'POST') POSTS.push({ url, body: JSON.parse(opt.body) });
    return { ok: true, status: 200, json: async () => ({}) };
  };
  ${recorteFnHtml(EXTRACAO, '_custoDigitado', 'index.html')}
  ${recorteFnHtml(EXTRACAO, '_salvarCustoDaConta', 'index.html')}
  return {
    async salva(id, bruto) { POSTS = []; const res = await _salvarCustoDaConta(id, bruto); return { res, posts: POSTS.slice() }; },
    num: (v) => _custoDigitado(v),
  };
`)();

// Os três estados possíveis na hora do save. O do meio é o que a trava deixava cair.
const ESTADOS = [
  ['servidor ja tem registro', { serverBacked: true, hadLegacy: true }],
  ['SERVIDOR VAZIO + legado no navegador (o buraco da trava)', { serverBacked: false, hadLegacy: true }],
  ['usuario novo: servidor vazio e navegador limpo', { serverBacked: false, hadLegacy: false }],
];

console.log('A. o custo por conta sobe em TODO estado (gestao.js)');
for (const [nome, cfg] of ESTADOS) {
  API_DASH.estado(cfg);
  const posts = API_DASH.salvaConta();
  eq(posts.length, 1, 'A. ' + nome + ': tem de sair exatamente 1 POST');
  if (posts.length) {
    eq(posts[0].url, '/custos/conta', 'A. ' + nome + ': vai para a rota do custo por conta');
    eq(posts[0].body.custo_conta['Move||Bet365'], 950, 'A. ' + nome + ': o valor digitado viaja');
    // `semear` decide se o servidor UNE. Só o 1º envio deste navegador pede união:
    // depois disso, substituir é obrigatório, senão apagar um custo nunca funciona.
    eq(posts[0].body.semear, !cfg.serverBacked, 'A. ' + nome + ': semear = era a 1a vez?');
  }
}
ok(API_DASH.backedConta(), 'A. depois de subir, o dono conta como servido');

console.log('B. o custo de tipster e o geral sobem em TODO estado (app.js)');
for (const [nome, cfg] of ESTADOS) {
  API_DASH.estado(cfg);
  const posts = API_DASH.salvaTipster();
  eq(posts.length, 1, 'B. ' + nome + ': tem de sair exatamente 1 POST');
  if (posts.length) {
    eq(posts[0].url, '/custos/store', 'B. ' + nome + ': vai para a rota do blob');
    ok(posts[0].body.custo_tipster['Só Chutes'], 'B. ' + nome + ': o lançamento viaja');
    eq(posts[0].body.semear, !cfg.serverBacked, 'B. ' + nome + ': semear = era a 1a vez?');
  }
}

console.log('C. a Extracao grava o custo DA CONTA e nunca a tabela (index.html)');
{
  const { res, posts } = await API_EXTRACAO.salva(15, '916,00');
  ok(res.ok, 'C. um custo valido grava');
  eq(posts.length, 1, 'C. tem de sair exatamente 1 POST');
  if (posts.length) {
    eq(posts[0].url, '/parceiros/15/custo', 'C. vai para a rota da CONTA, pelo id');
    eq(posts[0].body.custo, 916, 'C. o valor digitado viaja como numero');
  }
  ok(!posts.some(p => p.url === '/custos/conta'),
     'C. o card NAO pode escrever no preco de tabela (/custos/conta)');
  ok(!/fetch\(\s*['"]\/custos\/conta['"]\s*,\s*\{\s*method:\s*['"]POST/.test(EXTRACAO),
     'C. nenhum POST para /custos/conta pode voltar ao index.html');
}
{
  // Vazio devolve a conta à tabela: null, que é diferente de zero (conta de graça).
  const { res, posts } = await API_EXTRACAO.salva(15, '  ');
  ok(res.ok, 'C. apagar o valor grava');
  eq(posts.length && posts[0].body.custo, null, 'C. vazio viaja como null, nao como 0');
}
{
  // ZERO e preco (s381, decisao do Feca): conta de brinde custou zero, e isso se grava.
  // E ele viaja como 0, nunca como null — null devolveria a conta a tabela.
  const { res, posts } = await API_EXTRACAO.salva(15, '0');
  ok(res.ok, 'C. zero grava');
  eq(posts.length && posts[0].body.custo, 0, 'C. zero viaja como 0, e nao como null');
}
{
  const { res, posts } = await API_EXTRACAO.salva(15, '-5');
  ok(!res.ok && res.erro, 'C. negativo e recusado com mensagem');
  eq(posts.length, 0, 'C. negativo nao chega ao servidor');
}
// A régua do `parseNum`: o ponto sozinho só é milhar em grupos de 3.
eq(API_EXTRACAO.num('1.200'), 1200, 'C. "1.200" e milhar');
eq(API_EXTRACAO.num('179.90'), 179.9, 'C. "179.90" e decimal, nao 17.990');
eq(API_EXTRACAO.num('1.200,50'), 1200.5, 'C. "1.200,50" e BR completo');
eq(API_EXTRACAO.num('R$ 916'), 916, 'C. o R$ some');

console.log('D. a tela nao promete mais que o dado mora no navegador');
ok(!/permanentemente no navegador/.test(APP),
   'D. a frase "valores salvos permanentemente no navegador" nao pode voltar');
ok(!/localStorage\.getItem\(\s*['"]poly-wallet['"]/.test(EXTRACAO),
   'D. a carteira do Polymarket nao volta a ser lida do navegador');

if (falhas) { console.error(`\n${falhas} falha(s)`); process.exit(1); }
console.log('\n✓ dado_digitado_sobe_sempre: tudo verde');
