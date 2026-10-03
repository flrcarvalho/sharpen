// Moeda da conta no modal de conta (s391, passo 2 da moeda por conta).
//
// O que este arquivo prova, executando as funções RECORTADAS do `index.html` de
// produção (nenhuma regra é reimplementada aqui; os dublês são só recipientes):
//
// A. o seletor espelha o valor no hidden `#nc-moeda`, com UM botão aceso;
// B. a leitura do formulário devolve a moeda escolhida;
// C. o POST de criar e o de editar levam a moeda, e a conta ativa adota a nova;
// D. o aviso de troca aparece só na edição, com moeda diferente da salva e conta com
//    aposta (contagem desconhecida mostra sem número; zero esconde);
// E. a guarda de fechamento acidental conta o hidden `data-modal-campo` como campo.
//
// O que NÃO está coberto: o visual (é a medição headless) e o lado servidor das rotas,
// que tem gate próprio em `tests/test_moeda_conta.py` e no `test_repository_db.py`.
// DOM dublado sempre "clica": o clique real nos botões só a tela aberta confere.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import vm from 'node:vm';

const AQUI = dirname(fileURLToPath(import.meta.url));
const RAIZ = join(AQUI, '..', '..');
// ALVO_INDEX existe para a prova por MUTAÇÃO: o .py estraga uma cópia e aponta para ela.
const INDEX = readFileSync(process.env.ALVO_INDEX || join(RAIZ, 'app', 'static', 'index.html'), 'utf8');

let falhas = 0;
const ok = (cond, msg) => { if (!cond) { console.error('  ✗ ' + msg); falhas++; } };
const eq = (obtido, esperado, msg) => ok(obtido === esperado, msg + ', veio ' + JSON.stringify(obtido));

// O `index.html` é HTML: as funções vivem dentro de <script>. Recorta pela indentação
// do próprio `function`, até o fecho na mesma coluna.
const recorte = (nome) => {
  const m = INDEX.replace(/\r\n/g, '\n').match(
    new RegExp('^(\\s*)(?:async )?function ' + nome + '\\([^)]*\\) \\{[\\s\\S]*?^\\1\\}', 'm'));
  if (!m) throw new Error('não achei a função ' + nome + ' no index.html');
  return m[0];
};

// ── DOM dublado ──────────────────────────────────────────────────────────────
function el(id, extra = {}) {
  const classes = new Set(extra.classes || []);
  return {
    id, value: extra.value ?? '', textContent: '', type: extra.type || 'text',
    dataset: extra.dataset || {}, attrs: new Set(extra.attrs || []),
    disabled: false, offsetParent: extra.offsetParent === undefined ? {} : extra.offsetParent,
    parentElement: extra.parentElement || null,
    classList: {
      add: (c) => classes.add(c), remove: (c) => classes.delete(c),
      contains: (c) => classes.has(c),
      toggle: (c, f) => { const on = f === undefined ? !classes.has(c) : !!f; on ? classes.add(c) : classes.delete(c); return on; },
    },
    hasAttribute(a) { return this.attrs.has(a); },
    focus() {}, select() {},
  };
}

function montar() {
  const campoVisivel = { offsetParent: {} };
  const D = {
    'nc-casa': el('nc-casa', { value: 'Dex Sport', type: 'hidden' }),
    'nc-casa-nome': el('nc-casa-nome'), 'nc-casa-url': el('nc-casa-url'),
    'nc-parceiro': el('nc-parceiro', { value: 'Feca' }),
    'nc-forn': el('nc-forn', { value: '' }), 'nc-adq': el('nc-adq', { value: '' }),
    'nc-moeda': el('nc-moeda', { value: 'BRL', type: 'hidden', attrs: ['data-modal-campo'],
                                 offsetParent: null, parentElement: campoVisivel }),
    'nc-moeda-troca': el('nc-moeda-troca', { classes: ['nc-off'] }),
    'nc-moeda-nova': el('nc-moeda-nova'), 'nc-moeda-n': el('nc-moeda-n'),
    'nc-criar': el('nc-criar'),
  };
  const botoes = ['BRL', 'USD', 'USDT'].map(m => el('b' + m, { dataset: { moeda: m } }));
  const POSTS = [];
  const ctx = {
    D, botoes, POSTS, campoVisivel,
    document: {
      getElementById: (id) => D[id] || null,
      querySelectorAll: (sel) => sel === '#nc-moeda-seg button' ? botoes : [],
    },
    alert: () => {},
    fetch: async (url, opt) => {
      POSTS.push({ url, body: JSON.parse(opt.body) });
      return { ok: true, json: async () => ({ id: 7, casa: 'Dex Sport', nome: 'Feca', moeda: JSON.parse(opt.body).moeda }) };
    },
    console,
  };
  vm.createContext(ctx);
  const globais = `
    let _ncModo = 'criar', _ncAlvo = null, _ncOrigem = 'painel';
    let casasCarregadas = ['Dex Sport'], parceiroSelecionado = null, casaSelecionada = null;
    let painelDashRows = null, _painelDashPromise = null;
    const _cxIso = () => '';
    const _actPush = () => {}, carregarParceiros = async () => {}, renderCasaList = () => {};
    const renderPainelContas = () => {}, fecharModalNovaConta = () => {};
    const _ncRegistrarDominio = () => {}, aplicarModoCasa = () => {}, atualizarBotaoConta = () => {};
    const selecionarParceiro = () => {}, abrirAcctPop = () => {}, renderGrade = () => {};
    let acctPopAba = 'ativas';
  `;
  const fns = ['_ncMoedaSet', '_ncAvisoMoeda', '_ncLerForm', 'ncCriarConta', 'ncEditarConta',
               '_modalCampos'].map(recorte).join('\n');
  vm.runInContext(globais + fns + `
    this.api = { _ncMoedaSet, _ncAvisoMoeda, _ncLerForm, ncCriarConta, ncEditarConta, _modalCampos,
      set: (k, v) => { eval(k + ' = v'); }, get: (k) => eval(k) };`, ctx);
  return ctx;
}

const acesos = (ctx) => ctx.botoes.filter(b => b.classList.contains('on')).map(b => b.dataset.moeda);
const avisoVisivel = (ctx) => !ctx.D['nc-moeda-troca'].classList.contains('nc-off');

// ── A. o seletor espelha o valor ─────────────────────────────────────────────
{
  const ctx = montar();
  ctx.api._ncMoedaSet('USDT');
  eq(ctx.D['nc-moeda'].value, 'USDT', 'A: o hidden guarda a moeda escolhida');
  eq(acesos(ctx).join(','), 'USDT', 'A: só o botão escolhido fica aceso');
  ctx.api._ncMoedaSet('USD');
  eq(acesos(ctx).join(','), 'USD', 'A: trocar apaga o botão anterior');
}

// ── B e C. o formulário e os dois POSTs levam a moeda ────────────────────────
{
  const ctx = montar();
  ctx.api._ncMoedaSet('USDT');
  eq(ctx.api._ncLerForm().moeda, 'USDT', 'B: a leitura do formulário devolve a moeda');
  await ctx.api.ncCriarConta();
  eq(ctx.POSTS.length, 1, 'C: criar faz um POST');
  eq(ctx.POSTS[0].url, '/parceiros', 'C: criar vai ao /parceiros');
  eq(ctx.POSTS[0].body.moeda, 'USDT', 'C: o POST de criar leva a moeda');
}
{
  const ctx = montar();
  ctx.api.set('_ncModo', 'editar');
  ctx.api.set('_ncAlvo', { id: 7, casa: 'Dex Sport', nome: 'Feca', bilhetes: 3, moeda: 'BRL' });
  ctx.api.set('parceiroSelecionado', { id: 7, casa: 'Dex Sport', nome: 'Feca', moeda: 'BRL' });
  ctx.api._ncMoedaSet('USD');
  await ctx.api.ncEditarConta();
  eq(ctx.POSTS.length, 1, 'C: editar faz um POST');
  eq(ctx.POSTS[0].url, '/parceiros/7/editar', 'C: editar vai à rota da conta');
  eq(ctx.POSTS[0].body.moeda, 'USD', 'C: o POST de editar leva a moeda');
  eq(ctx.api.get('parceiroSelecionado').moeda, 'USD', 'C: a conta ativa adota a moeda nova');
}

// ── D. o aviso de troca ──────────────────────────────────────────────────────
{
  const ctx = montar();
  ctx.api.set('_ncModo', 'editar');
  ctx.api.set('_ncAlvo', { id: 7, casa: 'Dex Sport', nome: 'Feca', bilhetes: 1234, moeda: 'BRL' });
  ctx.api._ncMoedaSet('BRL');
  ok(!avisoVisivel(ctx), 'D: moeda igual à salva não avisa');
  ctx.api._ncMoedaSet('USDT');
  ok(avisoVisivel(ctx), 'D: moeda diferente numa conta com aposta avisa');
  eq(ctx.D['nc-moeda-nova'].textContent, 'USDT', 'D: o aviso nomeia a moeda nova');
  eq(ctx.D['nc-moeda-n'].textContent, 'As 1.234 apostas', 'D: o aviso conta as apostas em milhar pt-BR');

  ctx.api.set('_ncAlvo', { id: 7, casa: 'Dex Sport', nome: 'Feca', bilhetes: 1, moeda: 'BRL' });
  ctx.api._ncAvisoMoeda();
  eq(ctx.D['nc-moeda-n'].textContent, 'A aposta', 'D: uma aposta vai no singular');

  ctx.api.set('_ncAlvo', { id: 7, casa: 'Dex Sport', nome: 'Feca', bilhetes: null, moeda: 'BRL' });
  ctx.api._ncAvisoMoeda();
  ok(avisoVisivel(ctx), 'D: contagem desconhecida ainda avisa');
  eq(ctx.D['nc-moeda-n'].textContent, 'As apostas', 'D: contagem desconhecida avisa sem número');

  ctx.api.set('_ncAlvo', { id: 7, casa: 'Dex Sport', nome: 'Feca', bilhetes: 0, moeda: 'BRL' });
  ctx.api._ncAvisoMoeda();
  ok(!avisoVisivel(ctx), 'D: conta sem aposta não tem o que avisar');

  ctx.api.set('_ncModo', 'criar');
  ctx.api.set('_ncAlvo', null);
  ctx.api._ncMoedaSet('USDT');
  ok(!avisoVisivel(ctx), 'D: na criação não há troca a avisar');
}

// ── E. a guarda de fechamento acidental enxerga a moeda ──────────────────────
{
  const ctx = montar();
  const ov = { querySelectorAll: () => Object.values(ctx.D) };
  const campos = ctx.api._modalCampos(ov).map(e => e.id);
  ok(campos.includes('nc-moeda'), 'E: o hidden marcado conta como campo do modal');
  ok(!campos.includes('nc-casa'), 'E: hidden sem marca continua fora');
  ctx.campoVisivel.offsetParent = null;
  ok(!ctx.api._modalCampos(ov).map(e => e.id).includes('nc-moeda'),
     'E: campo escondido não conta');
}

if (falhas) { console.error(`\n${falhas} falha(s)`); process.exit(1); }
console.log('ok: moeda da conta no modal');
