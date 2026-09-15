// Dado que o usuário DIGITA sobe SEMPRE para o servidor (s366).
//
// A regra do `CLAUDE.md`: nada que o usuário digita repousa no navegador. O que a
// violava era a trava anti-semeadura-parcial, que existia em TRÊS telas com a mesma
// forma — `if (serverBacked) push; else if (!hadLegacy) push;`. O terceiro caso,
// **servidor vazio + legado no navegador**, não subia NADA: a pessoa digitava um custo
// e ele ficava só na máquina, sem erro e sem aviso.
//
// Este arquivo exercita as três funções de save RECORTADAS dos arquivos de produção e
// exige um POST em TODOS os estados. O estado que importa é o terceiro; os outros dois
// estão aqui para que uma mutação que quebre o caminho comum também apareça.
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
  const m = src.match(new RegExp('^(\\s*)function ' + nome + '\\([^)]*\\) \\{[\\s\\S]*?^\\1\\}', 'm'));
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

const API_EXTRACAO = new Function(`
  ${AMBIENTE}
  const DASH_COST_BASE = 'dash_custos_v2';
  let _custoContaServerBacked = false, _custoContaHadLegacy = false;
  ${recorteFnHtml(EXTRACAO, '_custoKey', 'index.html')}
  ${recorteFnHtml(EXTRACAO, '_salvarCusto', 'index.html')}
  return {
    estado(cfg) {
      LS = {}; POSTS = [];
      _custoContaServerBacked = cfg.serverBacked; _custoContaHadLegacy = cfg.hadLegacy;
      if (cfg.hadLegacy) LS[_custoKey()] = JSON.stringify({ 'JC||Betano': 600 });
    },
    salva: () => { _salvarCusto('Move', 'Bet365', '950'); return POSTS.slice(); },
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

console.log('C. a tela de Extracao tambem sobe em TODO estado (index.html)');
for (const [nome, cfg] of ESTADOS) {
  API_EXTRACAO.estado(cfg);
  const posts = API_EXTRACAO.salva();
  eq(posts.length, 1, 'C. ' + nome + ': tem de sair exatamente 1 POST');
  if (posts.length) {
    eq(posts[0].url, '/custos/conta', 'C. ' + nome + ': vai para a rota do custo por conta');
    eq(posts[0].body.custo_conta['Move||Bet365'], 950, 'C. ' + nome + ': o valor digitado viaja');
    eq(posts[0].body.semear, !cfg.serverBacked, 'C. ' + nome + ': semear = era a 1a vez?');
    // Esta tela guarda o dict INTEIRO, e não só a chave editada: o legado que já
    // estava no navegador precisa viajar junto, senão o save vira uma poda.
    if (cfg.hadLegacy)
      eq(posts[0].body.custo_conta['JC||Betano'], 600, 'C. ' + nome + ': o legado viaja junto');
  }
}

console.log('D. a tela nao promete mais que o dado mora no navegador');
ok(!/permanentemente no navegador/.test(APP),
   'D. a frase "valores salvos permanentemente no navegador" nao pode voltar');
ok(!/localStorage\.getItem\(\s*['"]poly-wallet['"]/.test(EXTRACAO),
   'D. a carteira do Polymarket nao volta a ser lida do navegador');

if (falhas) { console.error(`\n${falhas} falha(s)`); process.exit(1); }
console.log('\n✓ dado_digitado_sobe_sempre: tudo verde');
