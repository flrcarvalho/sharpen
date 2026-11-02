// D39 (s438, Feca 01/11/2026): a aposta que espera cru NÃO vai à IA, e a tela tem de dizer isso.
//
// O servidor guarda a aposta pendente (`ficha_virada.aviso`) e a rota `/ficha/nao_lidas` devolve
// duas contagens: `nao_lidas` (s423) e `incompletas` (D39: cru que não chegou, ou leitura que não
// virou linha). Este arquivo RECORTA a `_avisarNaoLidas` do `index.html` de produção e confere
// que cada contagem vira o seu aviso no card, com o que fazer ("atualize a aba da casa (F5) e
// extraia de novo"). Sem o aviso, a aposta seguraria fora da IA em silêncio: o oposto da D39.
//
// O que NÃO está coberto: a contagem em si (é SQL, no harness de banco) e o estilo do card (é o
// `warn` do `acrescentar`, o mesmo do aviso s423, sem CSS novo).
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const AQUI = dirname(fileURLToPath(import.meta.url));
const HTML = readFileSync(join(AQUI, '..', '..', 'app', 'static', 'index.html'), 'utf8');
const m = HTML.match(/async function _avisarNaoLidas\(card, casa\) \{[\s\S]*?\n\}\n/);
if (!m) { console.error('FAIL: _avisarNaoLidas sumiu do index.html'); process.exit(1); }

let falhas = 0;
const ok = (cond, msg) => { if (!cond) { falhas++; console.error('FAIL: ' + msg); } else console.log('ok: ' + msg); };

async function rodar(resposta) {
  const card = { txt: '', acrescentar(s) { this.txt += s; } };
  let url = null;
  const fetch = async (u) => { url = u; return { ok: true, json: async () => resposta }; };
  const fn = new Function('fetch', 'encodeURIComponent', m[0] + '\nreturn _avisarNaoLidas;')(
    fetch, encodeURIComponent);
  await fn(card, 'Sportsbet.io');
  return { txt: card.txt, url };
}

const a = await rodar({ nao_lidas: 0, incompletas: 3 });
ok(a.url === '/ficha/nao_lidas?casa=Sportsbet.io', 'pergunta à rota com o nome da casa');
ok(a.txt.includes('captura incompleta (3 aposta(s) esperando)'), 'incompletas viram o aviso D39 com a contagem');
ok(a.txt.includes('atualize a aba da casa (F5) e extraia de novo'), 'o aviso diz o que fazer');
ok(!a.txt.includes('não lida'), 'sem não lidas, o aviso s423 não aparece');

const b = await rodar({ nao_lidas: 2, incompletas: 0 });
ok(b.txt.includes('2 aposta(s) não lida(s)') && !b.txt.includes('captura incompleta'), 'só não lidas: só o aviso s423');

const c = await rodar({ nao_lidas: 1, incompletas: 1 });
ok(c.txt.includes('não lida') && c.txt.includes('captura incompleta'), 'as duas contagens: os dois avisos');

const d = await rodar({ nao_lidas: 0, incompletas: 0 });
ok(d.txt === '', 'nada pendente: card intacto');

if (falhas) { console.error(`${falhas} falha(s)`); process.exit(1); }
console.log('aviso_captura_incompleta: tudo verde');
