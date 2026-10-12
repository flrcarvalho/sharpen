// Espelho da 1xBet em domínio NOVO (s410): a captura se ajusta sozinha.
//
// O caso: a Megapari trocou `2479527mp.pro` por `4569421mp.pro`. Fora do manifest o
// `x1_inject` só entrava pelo popup, depois que a página já tinha buscado o histórico, e a
// captura dava "hook ATIVO · respostas 0" sem erro nenhum.
//
// O que este arquivo prova, executando o código RECORTADO dos arquivos reais da extensão
// (popup.js e background.js) e o `x1_inject.js` inteiro, com o `chrome` dublado:
//
// I. o inject marca `__suX1Cedo` = true só quando entra com a página carregando, e uma
//    injeção tardia por cima de uma cedo não apaga a marca;
// P. o popup, numa casa espelho móvel com hook atrasado: registra o domínio NOVO para
//    `document_start` no mundo MAIN (domínio do manifest não é registrado), deixa a
//    pendência do robô e recarrega a aba. Hook cedo, casa fora da lista ou registro que
//    falha seguem o caminho de sempre, sem recarregar. `*.x` do manifest cobre subdomínio,
//    nunca substring (`fakemegapari.com` não é `megapari.com`);
// B. o background dispara o robô UMA vez, só na mesma aba, no mesmo host, dentro do prazo,
//    só no `complete`, e insiste enquanto o content ainda não ouve.
//
// O que NÃO está coberto: o Chrome de verdade (que `registerContentScripts` aceita
// `world: "MAIN"` e injeta no recarregamento é documentação, não medição deste teste), a
// página da casa repetindo a busca do histórico depois do reload, e o `window.close()`.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import vm from 'node:vm';

const AQUI = dirname(fileURLToPath(import.meta.url));
const RAIZ = join(AQUI, '..', '..');
// ALVO_* existem para a prova por MUTAÇÃO: o .py estraga uma cópia e aponta para ela.
const ler = (env, arq) => readFileSync(process.env[env] || join(RAIZ, 'extensor', arq), 'utf8')
  .replace(/\r\n/g, '\n');
const POPUP = ler('ALVO_POPUP', 'popup.js');
const BG = ler('ALVO_BG', 'background.js');
const INJECT = ler('ALVO_INJECT', 'x1_inject.js');
const MANIFEST = JSON.parse(ler('ALVO_MANIFEST', 'manifest.json'));

let falhas = 0;
const ok = (cond, msg) => { if (!cond) { console.error('  ✗ ' + msg); falhas++; } };

// Recorta `[async ]function nome(...) { ... }` pelo casamento de chaves.
function recortarFuncao(src, nome) {
  const m = src.match(new RegExp('^(async )?function ' + nome + '\\(', 'm'));
  if (!m) throw new Error('função não achada: ' + nome);
  let i = src.indexOf('{', m.index), prof = 0;
  for (let j = i; j < src.length; j++) {
    if (src[j] === '{') prof++;
    else if (src[j] === '}' && --prof === 0) return src.slice(m.index, j + 1);
  }
  throw new Error('chaves desbalanceadas em ' + nome);
}
const recortarConst = (src, nome) => {
  const m = src.match(new RegExp('^const ' + nome + ' = .*;$', 'm'));
  if (!m) throw new Error('const não achada: ' + nome);
  return m[0];
};

// ── chrome dublado ──────────────────────────────────────────────────────────────────────
function chromeFalso({ cedo = false, execLanca = false, registroLanca = false, registrados = [] } = {}) {
  const st = { local: {}, registrados: registrados.map((r) => ({ ...r })), reloads: [], execs: [],
               registros: [], updates: [], envios: [], gets: 0 };
  const chrome = {
    runtime: { getManifest: () => MANIFEST },
    scripting: {
      executeScript: async (o) => { st.execs.push(o); if (execLanca) throw new Error('sem acesso'); return [{ result: cedo }]; },
      getRegisteredContentScripts: async ({ ids }) => st.registrados.filter((r) => ids.includes(r.id)),
      registerContentScripts: async (l) => {
        if (registroLanca) throw new Error('recusado');
        st.registros.push(...l); st.registrados.push(...l.map((r) => ({ ...r })));
      },
      updateContentScripts: async (l) => {
        st.updates.push(...l);
        for (const u of l) Object.assign(st.registrados.find((r) => r.id === u.id), u);
      },
    },
    storage: { local: {
      get: async (k) => { st.gets++; const ks = Array.isArray(k) ? k : [k]; const o = {}; for (const x of ks) if (x in st.local) o[x] = st.local[x]; return o; },
      set: async (o) => { Object.assign(st.local, o); },
      remove: async (k) => { delete st.local[k]; },
    } },
    tabs: {
      reload: async (id) => { st.reloads.push(id); },
      sendMessage: async (id, msg) => { st.envios.push({ id, msg }); if (st.envios.length <= (st.recusarEnvios || 0)) throw new Error('sem ouvinte'); },
      onUpdated: { addListener: (fn) => { st.ouvinte = fn; } },
    },
  };
  return { chrome, st };
}

// ── P. popup ────────────────────────────────────────────────────────────────────────────
const codigoPopup = [
  recortarConst(POPUP, 'X1_ESPELHOS_MOVEIS'), recortarConst(POPUP, 'X1_DINAMICO_ID'),
  recortarFuncao(POPUP, 'x1NoManifest'), recortarFuncao(POPUP, 'x1Registrar'),
  recortarFuncao(POPUP, 'x1RecarregarSeAtrasado'),
  'globalThis.__api = { x1NoManifest, x1RecarregarSeAtrasado };',
].join('\n');
function popup(opts) {
  const { chrome, st } = chromeFalso(opts);
  const ctx = vm.createContext({ chrome, Date, Set, Array, URL });
  vm.runInContext(codigoPopup, ctx);
  return { api: ctx.__api, st };
}

{ // cobertura do manifest: subdomínio sim, substring não
  const { api } = popup();
  ok(api.x1NoManifest('megapari.com'), 'megapari.com está no manifest');
  ok(api.x1NoManifest('www.megapari.com'), '*.megapari.com cobre www');
  ok(api.x1NoManifest('2479527mp.pro'), '2479527mp.pro está no manifest');
  ok(!api.x1NoManifest('9999999mp.pro'), 'domínio novo não está no manifest');
  ok(!api.x1NoManifest('fakemegapari.com'), 'substring não é subdomínio');
  ok(!api.x1NoManifest('megapari.com.evil.io'), 'prefixo não é o domínio');
}
const TAB = { id: 7 };
{ // domínio novo, hook atrasado: registra cedo no MAIN, deixa a pendência e recarrega
  const { api, st } = popup({ cedo: false });
  const r = await api.x1RecarregarSeAtrasado(TAB, '9999999mp.pro', 'Megapari');
  ok(r === true, 'domínio novo atrasado devolve true');
  ok(st.execs.length === 1 && st.execs[0].world === 'MAIN', 'a marca é lida no mundo MAIN');
  const reg = st.registros[0] || {};
  ok(st.registros.length === 1, 'registrou um script dinâmico');
  ok(reg.runAt === 'document_start', 'registro em document_start, veio ' + reg.runAt);
  ok(reg.world === 'MAIN', 'registro no mundo MAIN');
  ok(JSON.stringify(reg.js) === '["x1_inject.js"]', 'registro injeta o x1_inject.js');
  ok(JSON.stringify(reg.matches) === '["*://9999999mp.pro/*"]', 'registro casa só o domínio novo');
  const p = st.local.roboPendente || {};
  ok(p.tabId === 7 && p.host === '9999999mp.pro' && p.ate > Date.now(), 'pendência do robô com aba, host e prazo');
  ok(st.reloads.length === 1 && st.reloads[0] === 7, 'recarregou a aba');
}
{ // hook cedo: caminho de sempre
  const { api, st } = popup({ cedo: true });
  ok(await api.x1RecarregarSeAtrasado(TAB, '9999999mp.pro', 'Megapari') === false, 'hook cedo devolve false');
  ok(st.reloads.length === 0 && st.registros.length === 0 && !st.local.roboPendente, 'hook cedo não recarrega nem registra');
}
{ // casa fora da lista dos espelhos móveis: nem consulta a aba
  const { api, st } = popup({ cedo: false });
  ok(await api.x1RecarregarSeAtrasado(TAB, 'qualquer.com', '1xBet') === false, '1xBet não entra no desvio');
  ok(st.execs.length === 0 && st.reloads.length === 0, '1xBet não consulta nem recarrega');
}
for (const casa of ['SapphireBet', '1xBit']) {
  const { api, st } = popup({ cedo: false });
  ok(await api.x1RecarregarSeAtrasado(TAB, 'novo-' + casa.toLowerCase() + '.com', casa) === true, casa + ' entra no desvio');
  ok(st.reloads.length === 1, casa + ' recarrega');
}
{ // domínio do manifest atrasado (aba aberta antes da extensão): recarrega sem registrar
  const { api, st } = popup({ cedo: false });
  ok(await api.x1RecarregarSeAtrasado(TAB, '2479527mp.pro', 'Megapari') === true, 'domínio do manifest atrasado devolve true');
  ok(st.registros.length === 0 && st.updates.length === 0, 'domínio do manifest não é registrado');
  ok(st.reloads.length === 1, 'domínio do manifest atrasado recarrega');
}
{ // registro já existe: acrescenta o domínio; o mesmo domínio de novo não regrava
  const existente = { id: 'x1-espelho-dinamico', matches: ['*://1111111mp.pro/*'], js: ['x1_inject.js'] };
  const { api, st } = popup({ cedo: false, registrados: [existente] });
  await api.x1RecarregarSeAtrasado(TAB, '2222222mp.pro', 'Megapari');
  ok(st.registros.length === 0, 'não registra de novo um id que já existe');
  ok(st.updates.length === 1 && JSON.stringify(st.updates[0].matches) === '["*://1111111mp.pro/*","*://2222222mp.pro/*"]',
     'acrescenta o domínio novo sem perder o antigo');
  await api.x1RecarregarSeAtrasado(TAB, '2222222mp.pro', 'Megapari');
  ok(st.updates.length === 1, 'o mesmo domínio não regrava o registro');
}
{ // registro recusado: recarregar não adiantaria, segue o caminho de sempre
  const { api, st } = popup({ cedo: false, registroLanca: true });
  ok(await api.x1RecarregarSeAtrasado(TAB, '9999999mp.pro', 'Megapari') === false, 'registro recusado devolve false');
  ok(st.reloads.length === 0 && !st.local.roboPendente, 'registro recusado não recarrega nem deixa pendência');
}
{ // a aba não responde à consulta: trata como atrasado
  const { api, st } = popup({ execLanca: true });
  ok(await api.x1RecarregarSeAtrasado(TAB, '9999999mp.pro', 'Megapari') === true, 'consulta que falha conta como atrasado');
  ok(st.reloads.length === 1, 'consulta que falha recarrega');
}
{ // o gancho está no capturar(), ANTES do inject tardio
  const cap = recortarFuncao(POPUP, 'capturar');
  const iG = cap.indexOf('await x1RecarregarSeAtrasado(tab, host, casa)');
  const iInj = cap.indexOf('if (inj) {');
  ok(iG > 0 && iInj > iG, 'capturar() chama x1RecarregarSeAtrasado antes de injetar');
}

// ── B. background ───────────────────────────────────────────────────────────────────────
const mOuv = BG.match(/^chrome\.tabs\.onUpdated\.addListener\([\s\S]*?\n\}\);$/m);
ok(!!mOuv, 'background registra o ouvinte de onUpdated no topo');
const codigoBg = [(mOuv || [''])[0], recortarFuncao(BG, 'retomarRobo'),
  'globalThis.__api = { retomarRobo };'].join('\n');
function bg(pendente, recusarEnvios = 0) {
  const { chrome, st } = chromeFalso();
  if (pendente) st.local.roboPendente = pendente;
  st.recusarEnvios = recusarEnvios;
  const ctx = vm.createContext({ chrome, Date, URL, Promise, setTimeout: (fn) => fn() });
  vm.runInContext(codigoBg, ctx);
  return { api: ctx.__api, st };
}
const ABA = { url: 'https://9999999mp.pro/pt/office/history' };
const PEND = () => ({ tabId: 7, host: '9999999mp.pro', ate: Date.now() + 60000 });
{
  const { api, st } = bg(PEND());
  ok(await api.retomarRobo(7, ABA) === true, 'pendência válida dispara o robô');
  ok(st.envios.length === 1 && st.envios[0].msg.type === 'START_ROBOT' && st.envios[0].id === 7, 'manda START_ROBOT para a aba');
  ok(!st.local.roboPendente, 'a pendência sai depois de usada');
  ok(await api.retomarRobo(7, ABA) === false && st.envios.length === 1, 'segunda carga da aba não dispara de novo');
}
{
  const { api, st } = bg(PEND());
  ok(await api.retomarRobo(8, ABA) === false && st.envios.length === 0, 'outra aba não dispara');
  ok(!!st.local.roboPendente, 'outra aba não consome a pendência');
}
{
  const { api, st } = bg({ ...PEND(), ate: Date.now() - 1 });
  ok(await api.retomarRobo(7, ABA) === false && st.envios.length === 0, 'pendência vencida não dispara');
  ok(!st.local.roboPendente, 'pendência vencida é apagada');
}
{
  const { api, st } = bg(PEND());
  ok(await api.retomarRobo(7, { url: 'https://outro-site.com/' }) === false && st.envios.length === 0, 'outro host não dispara');
}
{
  const { api, st } = bg(PEND(), 2);
  ok(await api.retomarRobo(7, ABA) === true && st.envios.length === 3, 'insiste até o content ouvir');
}
{ // o ouvinte só age no `complete`
  const { st } = bg(PEND());
  st.ouvinte(7, { status: 'loading' }, ABA);
  await new Promise((r) => setImmediate(r));
  ok(st.gets === 0, 'status loading não consulta a pendência');
  st.ouvinte(7, { status: 'complete' }, ABA);
  await new Promise((r) => setImmediate(r));
  await new Promise((r) => setImmediate(r));
  ok(st.envios.length === 1, 'status complete dispara o robô');
}

// ── I. inject ───────────────────────────────────────────────────────────────────────────
function rodarInject(ctx, readyState) {
  ctx.document.readyState = readyState;
  vm.runInContext(INJECT, ctx);
}
function ctxInject() {
  function XHR() {}
  XHR.prototype.open = function () {}; XHR.prototype.send = function () {};
  XHR.prototype.setRequestHeader = function () {};
  const ctx = { console: { log() {} }, location: { href: 'https://9999999mp.pro/pt/office/history' },
    document: {}, XMLHttpRequest: XHR, fetch: async () => ({}), addEventListener() {}, postMessage() {},
    setTimeout, clearTimeout, Map, Set, WeakMap, JSON, Date, Math, Promise, String, Number, Array, Object };
  ctx.window = ctx;
  return vm.createContext(ctx);
}
{
  const c = ctxInject(); rodarInject(c, 'loading');
  ok(c.__suX1Cedo === true, 'inject com a página carregando marca cedo');
}
{
  const c = ctxInject(); rodarInject(c, 'complete');
  ok(c.__suX1Cedo === false, 'inject depois do load marca atrasado');
}
{
  const c = ctxInject(); rodarInject(c, 'loading'); rodarInject(c, 'complete');
  ok(c.__suX1Cedo === true, 'injeção tardia por cima da cedo não apaga a marca');
}

if (falhas) { console.error(`x1_dominio_novo: ${falhas} falha(s)`); process.exit(1); }
console.log('x1_dominio_novo: ok');
