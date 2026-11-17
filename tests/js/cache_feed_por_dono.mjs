// O cache do feed (IndexedDB) é de UMA identidade (s459, auditoria de 17/11, NAVEGADOR C3/M3).
//
// O caso: a chave era a fixa 'dados_v1'. No mesmo navegador, quem entrava depois (outro
// login, ou o supervisor no "ver como") abria o dashboard com a base inteira do anterior
// até o feed chegar, e para sempre se o feed falhasse. Medido no headless da auditoria:
// o Bob viu as 24.000 apostas da Alice por mais de 9,5 s.
//
// Executa as funções RECORTADAS do `app.js` de produção (`_idbIdentidade`,
// `_idbCacheValido`). Nenhuma regra é reimplementada aqui.
//
// O que NÃO está coberto: o IndexedDB de verdade (o `_idbSetData` que apaga as outras
// identidades roda só no navegador) e a ordem de pintura do `loadData`; ambos pedem a
// medição headless.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const AQUI = dirname(fileURLToPath(import.meta.url));
const RAIZ = join(AQUI, '..', '..');
const APP = readFileSync(process.env.ALVO_APP || join(RAIZ, 'app', 'static', 'dash', 'assets', 'js', 'app.js'), 'utf8');

let falhas = 0;
const ok = (cond, msg) => { if (!cond) { console.error('  ✗ ' + msg); falhas++; } };
const eq = (obtido, esperado, msg) => ok(obtido === esperado, msg + ', veio ' + JSON.stringify(obtido));

const recorteFn = (nome) => {
  const m = APP.match(new RegExp('^(?:async )?function ' + nome + '\\([^)]*\\)\\{[\\s\\S]*?^\\}', 'm'));
  if (!m) throw new Error('não achei a função ' + nome + ' no app.js');
  return m[0];
};
const constante = (nome) => {
  const m = APP.match(new RegExp(nome + '=([^,;]+)'));
  if (!m) throw new Error('não achei a constante ' + nome);
  return 'const ' + nome + '=' + m[1] + ';';
};

const API = new Function(`
  let PUBLICO = null, _IDB_KEY = null, ME = null;
  const fetch = async (url) => {
    if (url !== '/me') throw new Error('url inesperada ' + url);
    if (ME === 'rede') throw new Error('rede');
    if (typeof ME === 'number') return { ok: false, status: ME, json: async () => ({}) };
    return { ok: true, status: 200, json: async () => ME };
  };
  ${constante('_IDB_SCHEMA')}
  ${constante('_IDB_MAX_IDADE_MS')}
  ${recorteFn('_idbIdentidade')}
  ${recorteFn('_idbCacheValido')}
  return {
    async chave(me) { ME = me; return _idbIdentidade(); },
    valido: (c, k, agora) => _idbCacheValido(c, k, agora),
    schema: _IDB_SCHEMA,
  };
`)();

console.log('A. a chave carrega quem vê o quê');
const kAlice = await API.chave({ usuario: 'Alice', dono_efetivo: 'Alice' });
const kBob = await API.chave({ usuario: 'Bob', dono_efetivo: 'Bob' });
const kVerComo = await API.chave({ usuario: 'Alice', dono_efetivo: 'Operador1' });
ok(kAlice && kBob && kAlice !== kBob, 'A1. Alice e Bob têm chaves diferentes');
ok(kVerComo && kVerComo !== kAlice, 'A2. o "ver como" é outra chave que a base própria');
eq(await API.chave(401), null, 'A3. sem sessão não há chave (e portanto não há cache)');
eq(await API.chave('rede'), null, 'A4. /me fora do ar não há chave');
eq(await API.chave({ usuario: '' }), null, 'A5. /me sem usuário não há chave');

console.log('B. só pinta o cache da MESMA identidade, no esquema atual e recente');
const agora = Date.parse('2026-11-17T12:00:00Z');
const base = { chave: kAlice, schema: API.schema, data: [{ id: 1 }], savedAt: agora - 3600e3 };
ok(API.valido(base, kAlice, agora), 'B1. o cache da própria Alice, de 1 h atrás, pinta');
ok(!API.valido(base, kBob, agora), 'B2. o cache da Alice NÃO pinta para o Bob');
ok(!API.valido(base, kVerComo, agora), 'B3. nem para a Alice vendo outra base');
ok(!API.valido({ ...base, schema: 1 }, kAlice, agora), 'B4. esquema antigo não pinta');
ok(!API.valido({ ...base, chave: undefined }, kAlice, agora), 'B5. o registro legado dados_v1 (sem chave) não pinta');
ok(!API.valido({ ...base, savedAt: agora - 90 * 864e5 }, kAlice, agora), 'B6. cache de 3 meses atrás não pinta');
ok(!API.valido({ ...base, data: [] }, kAlice, agora), 'B7. cache vazio não pinta');
ok(!API.valido(base, null, agora), 'B8. sem chave, nada pinta');

console.log('C. a chave fixa não volta');
ok(!/_IDB_KEY\s*=\s*PUBLICO\s*\?[^:]*:\s*'dados_v1'/.test(APP), 'C1. a chave fixa dados_v1 não pode voltar');

if (falhas) { console.error(`\n${falhas} falha(s)`); process.exit(1); }
console.log('\n✓ cache_feed_por_dono: tudo verde');
