// O custo que está SÓ NESTE NAVEGADOR (s360) — detecção, ordem de envio e a guarda
// que impede o servidor vazio de apagar o cache local.
//
// O caso que originou o gate: o custo nasceu no localStorage, virou coluna no Postgres
// na s165, e a trava anti-semeadura só sobe no SAVE. Quem preencheu antes e nunca mais
// editou ficou com tudo na máquina, com a tela mostrando o número certo o tempo todo.
// Medido em 2026-09-15: 16 donos, 480 contas cadastradas, zero linha em `custo_store`.
//
// Três regras que este arquivo trava, e cada uma nasceu de um jeito diferente de perder
// dado:
//   1. memória cheia NÃO é "custo deste navegador" — a detecção lê o cache, e não o
//      `custoData`, que outras fontes enchem (o `CUSTO_SEED` até a s369, o espelho do
//      preço por fornecedor hoje);
//   2. o envio manda tipster/geral ANTES do preço de conta, porque `salvar_custo_conta`
//      CRIA a linha de `custo_store` e a partir dali `/custos/store` responde existe=true;
//   3. `ctLoad` não adota o blob vazio do servidor quando este navegador tem lançamento,
//      senão o `_ctMirror` grava o apagão por cima do cache.
//
// Executa as funções RECORTADAS do `gestao.js`, do `app.js` e do `custos2.js` de
// produção. Nenhuma regra é reimplementada aqui.
//
// O que NÃO está coberto: o visual da faixa (cor, posição, quebra de linha), que só a
// medição headless pega; e o servidor, que tem gate próprio. Aqui é a decisão do front.
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
const CUSTOS2 = readFileSync(process.env.ALVO_CUSTOS2 || join(BASE, 'charts', 'custos2.js'), 'utf8');
const LF = '\n';

let falhas = 0;
const ok = (cond, msg) => { if (!cond) { console.error('  ✗ ' + msg); falhas++; } };
const eq = (obtido, esperado, msg) => ok(obtido === esperado, msg + ', veio ' + JSON.stringify(obtido));

// Função de UMA linha primeiro (o `costKey` é assim). Sem esse ramo o recorte
// multilinha engole tudo até o próximo `}` em coluna zero — que no gestao.js é o fim
// de um bloco de topo de arquivo, e o harness nasce com declaração duplicada.
const recorteFn = (src, nome, arq) => {
  const uma = src.match(new RegExp('^(?:async )?function ' + nome + '\\([^)]*\\)\\{.*\\}$', 'm'));
  if (uma) return uma[0];
  const m = src.match(new RegExp('^(?:async )?function ' + nome + '\\([^)]*\\)\\{[\\s\\S]*?^\\}', 'm'));
  if (!m) throw new Error('não achei a função ' + nome + ' no ' + arq);
  return m[0];
};
// O `c2Guardar` é atribuído ao window, não declarado — recorte próprio.
const recorteWindowFn = (src, nome, arq) => {
  const m = src.match(new RegExp('^window\\.' + nome + ' = async function\\(\\)\\{[\\s\\S]*?^\\};', 'm'));
  if (!m) throw new Error('não achei o window.' + nome + ' no ' + arq);
  return m[0];
};

const FONTE = [
  ...['costKey', 'loadCusto', 'custoContaPendente', 'custoContaSubir']
    .map(n => recorteFn(GESTAO, n, 'gestao.js')),
  ...['parseNum', '_ctHasVal', '_ctMirror', 'ctLoad', 'ctPendente', 'ctSubir']
    .map(n => recorteFn(APP, n, 'app.js')),
  recorteFn(CUSTOS2, '_c2guardarHTML', 'custos2.js'),
  recorteWindowFn(CUSTOS2, 'c2Guardar', 'custos2.js'),
].join(LF);

// Dublês do ambiente do navegador. São RECIPIENTES (localStorage, fetch, DOM), nunca
// regra: toda decisão medida aqui sai do código recortado acima.
const API = new Function(`
  const CT_KEY = 'custoTipsterData', CG_KEY = 'custoGeralData';
  let custoData = {}, _custoServerBacked = false, _custoHadLegacy = false;
  let ctData = {}, cgData = [], ctMeta = {};
  let _ctServerBacked = false, _ctHadLegacy = false, _ctRepintou = true;
  let _c2guardou = false;
  let LS = {}, RESP = {}, CHAMADAS = [], POSTS = [];
  const window = { __dono: 'Feca' };
  const localStorage = {
    getItem: (k) => (k in LS ? LS[k] : null),
    setItem: (k, v) => { LS[k] = String(v); },
  };
  // Só os ids que a faixa usa; innerHTML/classList/textContent são recipientes.
  const NOS = {};
  const novoNo = (id) => ({ id, innerHTML: '', textContent: '', disabled: false,
    classList: { lista: [], add(c){ this.lista.push(c); }, contains(c){ return this.lista.includes(c); } } });
  const document = { getElementById: (id) => NOS[id] || null };
  const fetch = async (url, opt) => {
    CHAMADAS.push(url);
    if (opt && opt.method === 'POST') POSTS.push({ url, body: JSON.parse(opt.body) });
    const r = RESP[url];
    if (typeof r === 'function') return r();
    return { ok: true, status: 200, json: async () => (r || {}) };
  };
  const fmtR = (v) => 'R$ ' + Math.round(v);
  function renderCustos2(){ NOS.c2Guardar = NOS.c2Guardar || novoNo('c2Guardar');
                            NOS.c2Guardar.innerHTML = _c2guardarHTML(); }
  ${FONTE}
  return {
    async reset(cfg) {
      LS = Object.assign({}, cfg.ls || {});
      RESP = cfg.resp || {};
      CHAMADAS = []; POSTS = [];
      custoData = {}; _custoServerBacked = false; _custoHadLegacy = false;
      ctData = {}; cgData = []; _ctServerBacked = false; _ctHadLegacy = false;
      _c2guardou = false;
      for (const k of Object.keys(NOS)) delete NOS[k];
      window.__dono = cfg.dono === undefined ? 'Feca' : cfg.dono;
      if (cfg.carregar !== false) { await loadCusto(); await ctLoad(); }
      // Enche a MEMORIA sem passar pelo navegador, como o _c2precos faz ao espelhar o
      // preco por fornecedor (e como o CUSTO_SEED fazia ate a s369).
      // (Sem crase: este comentario vive DENTRO de um template literal, e uma crase
      // perdida derruba o harness inteiro — o caso da s296.)
      if (cfg.memoria) custoData = { ...cfg.memoria };
    },
    contaPendente: () => custoContaPendente(),
    tipsPendente: () => ctPendente(),
    contaSubir: () => custoContaSubir(),
    tipsSubir: () => ctSubir(),
    faixa: () => _c2guardarHTML(),
    async guardar() {
      NOS.c2GuardarBox = novoNo('c2GuardarBox');
      NOS.c2GuardarBtn = novoNo('c2GuardarBtn');
      NOS.c2GuardarMsg = novoNo('c2GuardarMsg');
      await window.c2Guardar();
      return { box: NOS.c2GuardarBox, btn: NOS.c2GuardarBtn, msg: NOS.c2GuardarMsg };
    },
    estado: () => ({ custoData, _custoServerBacked, _custoHadLegacy,
                     ctData, cgData, _ctServerBacked, _ctHadLegacy, LS }),
    posts: () => POSTS,
    // Permite simular o dono que JÁ tem registro sem passar pelo fetch.
    forcar: (o) => { if ('conta' in o) _custoServerBacked = o.conta;
                     if ('tips' in o) _ctServerBacked = o.tips; },
  };
`)();

const K_CONTA = 'dash_custos_v2::Feca';
const VAZIO = { '/custos/conta': { existe: false }, '/custos/store': { existe: false } };

// ── A. custoContaPendente: quem é dado do dono e quem é seed ──────────────────
console.log('A. o preço de conta que está só no navegador');
{
  await API.reset({ ls: { [K_CONTA]: JSON.stringify({ 'Move||Bet365': 950, 'JC||Betano': 600 }) },
                    resp: VAZIO });
  const p = API.contaPendente();
  eq(p && p.pares, 2, 'A1. dois pares no cache, servidor vazio: a faixa deve acusar 2');
  eq(p && p.total, 1550, 'A1. o total somado é o que a faixa exibe');

  await API.reset({ ls: { [K_CONTA]: JSON.stringify({ 'Move||Bet365': 950 }) },
                    resp: { '/custos/conta': { existe: true, custo_conta: { 'Move||Bet365': 950 } },
                            '/custos/store': { existe: false } } });
  eq(API.contaPendente(), null, 'A2. servidor JÁ tem o custo: nada a guardar, faixa muda');

  // Memória preenchida, navegador VAZIO: nada a oferecer. Enquanto existiu, quem enchia
  // a memória sem passar pelo navegador era o `CUSTO_SEED` (11 pares cravados no código,
  // só para o dono 'Feca'), e foi ele que mascarou a perda por meses — a tela mostrava
  // R$ 59.600 de uma base que não tinha custo nenhum. O seed saiu na s369, mas a regra
  // continua tendo dono: `_c2precos` também escreve em `custoData` a partir do preço por
  // fornecedor, que é dado do SERVIDOR. Oferecer isso como "custo deste navegador"
  // ofereceria o que ninguém digitou ali.
  await API.reset({ ls: {}, resp: VAZIO, memoria: { 'Move||Bet365': 950, 'JC||Betano': 600 } });
  const est = API.estado();
  eq(Object.keys(est.custoData).length, 2, 'A3. pré-condição: a memória está cheia');
  eq(est._custoHadLegacy, false, 'A3. pré-condição: e o navegador está vazio');
  eq(API.contaPendente(), null, 'A3. memória cheia não vira "custo deste navegador"');

  await API.reset({ ls: { [K_CONTA]: JSON.stringify({ 'Move||Bet365': 0, 'JC||Betano': 0 }) },
                    resp: VAZIO });
  eq(API.contaPendente(), null, 'A4. par zerado não é lançamento: nada a guardar');
}

// ── B. ctPendente: lê o localStorage, e lê NÚMERO ─────────────────────────────
console.log('B. o custo de tipster e o geral que estão só no navegador');
{
  await API.reset({ ls: { custoTipsterData: JSON.stringify({ 'Só Chutes': { '2026-09': '500,00' } }) },
                    resp: VAZIO });
  const p = API.tipsPendente();
  eq(p && p.tipsters, 1, 'B1. valor em string BR ("500,00") conta como lançamento');
  eq(p && p.gerais, 0, 'B1. sem custo geral, o contador fica zerado');

  // "0,00" é truthy em JS. Quem testar por verdade da string conta um lançamento que
  // não existe — mesma família do "zero se disfarça de conta feita".
  await API.reset({ ls: { custoTipsterData: JSON.stringify({ 'Só Chutes': { '2026-09': '0,00' } }) },
                    resp: VAZIO });
  eq(API.tipsPendente(), null, 'B2. tipster com "0,00" não é lançamento');

  await API.reset({ ls: { custoGeralData: JSON.stringify([{ id: 1, tipo: 'VPS', values: { '2026-09': '120' } }]) },
                    resp: VAZIO });
  const g = API.tipsPendente();
  eq(g && g.gerais, 1, 'B3. custo geral com valor conta');

  await API.reset({ ls: { custoTipsterData: JSON.stringify({ 'Só Chutes': { '2026-09': '500' } }) },
                    resp: { '/custos/conta': { existe: false },
                            '/custos/store': { existe: true, custo_tipster: { 'Só Chutes': { '2026-09': '500' } },
                                               custo_geral: [] } } });
  eq(API.tipsPendente(), null, 'B4. servidor já tem o blob: nada a guardar');
}

// ── C. a guarda que impede o servidor vazio de apagar o cache ────────────────
console.log('C. linha existe no servidor, blob vazio, navegador com lançamento');
{
  // Como isso acontece: `salvar_custo_conta` faz upsert na MESMA linha de custo_store.
  // Um dono que só guardou o preço de conta passa a ter linha, e `/custos/store`
  // responde existe=true com o blob tipster/geral ainda no default.
  await API.reset({ ls: { custoTipsterData: JSON.stringify({ 'Só Chutes': { '2026-09': '500' } }) },
                    resp: { '/custos/conta': { existe: false },
                            '/custos/store': { existe: true, custo_tipster: {}, custo_geral: [] } } });
  const e = API.estado();
  eq(Object.keys(e.ctData).length, 1, 'C1. o lançamento local SOBREVIVE ao blob vazio do servidor');
  eq(JSON.parse(e.LS.custoTipsterData || '{}')['Só Chutes']['2026-09'], '500',
     'C1. e o cache no navegador não foi sobrescrito pelo vazio');
  eq(e._ctServerBacked, false, 'C1. com o blob vazio o dono NÃO conta como servido');
  ok(API.tipsPendente() !== null, 'C1. e a faixa passa a oferecer guardar');

  // O caminho normal segue intacto: servidor com dado manda, e o local é corrigido.
  await API.reset({ ls: { custoTipsterData: JSON.stringify({ 'Antigo': { '2026-08': '100' } }) },
                    resp: { '/custos/conta': { existe: false },
                            '/custos/store': { existe: true, custo_tipster: { 'Novo': { '2026-09': '700' } },
                                               custo_geral: [] } } });
  const e2 = API.estado();
  eq(Object.keys(e2.ctData).join(','), 'Novo', 'C2. servidor COM dado continua sendo a fonte de verdade');
  eq(e2._ctServerBacked, true, 'C2. e o dono volta a contar como servido');
}

// ── D. a ORDEM do envio ──────────────────────────────────────────────────────
console.log('D. tipster/geral sobe ANTES do preço de conta');
{
  await API.reset({ ls: { [K_CONTA]: JSON.stringify({ 'Move||Bet365': 950 }),
                          custoTipsterData: JSON.stringify({ 'Só Chutes': { '2026-09': '500' } }) },
                    resp: VAZIO });
  ok(API.contaPendente() !== null && API.tipsPendente() !== null, 'D. pré-condição: os dois pendentes');
  await API.guardar();
  const urls = API.posts().map(p => p.url);
  eq(urls.join(' > '), '/custos/store > /custos/conta',
     'D1. /custos/conta CRIA a linha; subir o blob depois dela abre a janela do apagão');
  const est = API.estado();
  eq(est._custoServerBacked, true, 'D2. depois de guardar, o preço de conta conta como servido');
  eq(est._ctServerBacked, true, 'D2. e o blob tipster/geral também');
  eq(API.contaPendente(), null, 'D3. a faixa some depois do sucesso');
  eq(API.tipsPendente(), null, 'D3. nos dois blocos');
}

// ── E. o botão não pode mentir ───────────────────────────────────────────────
console.log('E. falha do servidor não vira sucesso na tela');
{
  await API.reset({ ls: { [K_CONTA]: JSON.stringify({ 'Move||Bet365': 950 }) },
                    resp: { '/custos/conta': () => ({ ok: false, status: 500 }),
                            '/custos/store': { existe: false } },
                  });
  let subiu = null;
  try { await API.contaSubir(); subiu = 'ok'; } catch (e) { subiu = 'erro'; }
  eq(subiu, 'erro', 'E1. HTTP 500 tem de chegar ao chamador, não ser engolido');
  eq(API.estado()._custoServerBacked, false, 'E1. e o dono NÃO pode ser marcado como servido');
  ok(API.contaPendente() !== null, 'E1. o custo continua pendente, para tentar de novo');

  const r = await API.guardar();
  ok(r.box.classList.contains('is-erro'), 'E2. a faixa se marca como erro');
  ok(/Não consegui guardar/.test(r.msg.innerHTML), 'E2. e diz que nada se perdeu');
  eq(r.btn.disabled, false, 'E2. o botão volta a poder ser clicado');

  // O mesmo do outro lado: o blob de tipster/geral tem endpoint próprio, e engolir o
  // erro DELE marcaria o dono como servido com o servidor ainda vazio. A partir daí a
  // faixa some e o `ctSave` acha que pode empurrar, sem nunca ter semeado nada.
  await API.reset({ ls: { custoTipsterData: JSON.stringify({ 'Só Chutes': { '2026-09': '500' } }) },
                    resp: { '/custos/conta': { existe: false },
                            '/custos/store': () => ({ ok: false, status: 500 }) } });
  let subiuT = null;
  try { await API.tipsSubir(); subiuT = 'ok'; } catch (e) { subiuT = 'erro'; }
  eq(subiuT, 'erro', 'E1b. HTTP 500 no /custos/store também tem de chegar ao chamador');
  eq(API.estado()._ctServerBacked, false, 'E1b. e o dono NÃO pode ser marcado como servido');
  ok(API.tipsPendente() !== null, 'E1b. o lançamento continua pendente, para tentar de novo');

  // Metade passou: a tela tem de dizer O QUE passou, não "deu tudo certo".
  await API.reset({ ls: { [K_CONTA]: JSON.stringify({ 'Move||Bet365': 950 }),
                          custoTipsterData: JSON.stringify({ 'Só Chutes': { '2026-09': '500' } }) },
                    resp: { '/custos/conta': () => ({ ok: false, status: 500 }),
                            '/custos/store': { existe: false } } });
  const r2 = await API.guardar();
  ok(/tipsters e gerais/.test(r2.msg.innerHTML), 'E3. envio parcial diz qual metade subiu');
}

// ── F. a faixa só aparece quando há o que guardar ────────────────────────────
console.log('F. a faixa');
{
  await API.reset({ ls: {}, resp: { '/custos/conta': { existe: true, custo_conta: { 'Move||Bet365': 950 } },
                                    '/custos/store': { existe: true, custo_tipster: {}, custo_geral: [] } } });
  eq(API.faixa(), '', 'F1. dono com tudo no servidor não vê faixa nenhuma');

  await API.reset({ ls: { [K_CONTA]: JSON.stringify({ 'Move||Bet365': 950 }) }, resp: VAZIO });
  const h = API.faixa();
  ok(/c2GuardarBtn/.test(h), 'F2. com pendência a faixa traz o BOTÃO (aviso sem ação já saiu daqui)');
  ok(!/Confira as abas/.test(h),
     'F3. sem tipster/geral pendente a faixa não manda conferir aba nenhuma');

  await API.reset({ ls: { custoTipsterData: JSON.stringify({ 'Só Chutes': { '2026-09': '500' } }) },
                    resp: VAZIO });
  ok(/Confira as abas/.test(API.faixa()),
     'F4. com tipster/geral a faixa manda conferir: CT_KEY/CG_KEY não têm dono');
}

if (falhas) { console.error(`\n${falhas} falha(s)`); process.exit(1); }
console.log('\n✓ custo_so_no_navegador: tudo verde');
