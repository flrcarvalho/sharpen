// SharpenUp 0.7.89 (s460): fila de envios pendentes (7.2), janela pelo servidor (7.6) e
// rodada parcial declarada (6.5). Executa os trechos REAIS do `content.js` e do `popup.js`,
// recortados do arquivo (ALVO_CONTENT / ALVO_POPUP apontam para uma cópia mutada no pytest).
//
// NÃO cobre: o fluxo da página (o robô, o toast, o envio de verdade) nem o HTML do popup; DOM
// dublado sempre "clica". Cobre as decisões: o que entra e sai da fila, para qual conta o
// Reenviar manda, quantos dias o robô varre e quando a rodada é parcial.
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const RAIZ = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const CONTENT = readFileSync(process.env.ALVO_CONTENT || join(RAIZ, 'extensor', 'content.js'), 'utf8');
const POPUP = readFileSync(process.env.ALVO_POPUP || join(RAIZ, 'extensor', 'popup.js'), 'utf8');

const falhas = [];
const ok = (cond, msg) => { if (!cond) falhas.push(msg); };
function recorte(src, re, nome) {
  const m = src.match(re);
  if (!m) { console.log('recorte não achado: ' + nome); process.exit(2); }
  return m[0];
}

function storage(inicial = {}, quebra = false) {
  const d = JSON.parse(JSON.stringify(inicial));
  return {
    d,
    local: {
      get: async (ks) => (Array.isArray(ks) ? ks : [ks]).reduce((o, k) => { if (k in d) o[k] = JSON.parse(JSON.stringify(d[k])); return o; }, {}),
      set: async (o) => { if (quebra) throw new Error('QUOTA_BYTES'); Object.assign(d, JSON.parse(JSON.stringify(o))); },
      remove: async (ks) => { for (const k of (Array.isArray(ks) ? ks : [ks])) delete d[k]; },
    },
  };
}

// ── content.js: a fila ─────────────────────────────────────────────────────────────────────
const filaSrc = recorte(CONTENT, /  const PEND_TETO = \d+;[\s\S]*?\n  async function _pendRemover\(id\) \{[\s\S]*?\n  \}\n/, 'fila do content');
const fabricaFila = new Function('chrome', filaSrc + '\nreturn { _pendGuardar, _pendRemover };');
const item = (id, extra = {}) => Object.assign({ id, texto: 'T' + id, n: 1, casa: 'Betano', parceiro: 'A', dono: 'd', ts: Date.now() }, extra);

{
  const s = storage();
  const { _pendGuardar, _pendRemover } = fabricaFila({ storage: s });
  ok(await _pendGuardar(item('r1')) === true, 'gravar devolve true');
  await _pendGuardar(item('r2'));
  ok(s.d.enviosPendentes.length === 2, 'a 2ª rodada não apaga a 1ª (era slot único)');
  await _pendRemover('r1');
  ok(s.d.enviosPendentes.map((p) => p.id).join() === 'r2', 'remover tira só aquele envio');
}
{
  const s = storage({ envioPendente: { texto: 'velho', n: 3, casa: 'Betano', ts: 1 } });
  const { _pendGuardar } = fabricaFila({ storage: s });
  await _pendGuardar(item('r3'));
  ok(!('envioPendente' in s.d), 'o slot antigo sai do storage');
  ok(s.d.enviosPendentes.length === 2 && s.d.enviosPendentes[0].texto === 'velho', 'o slot antigo entra na fila');
}
{
  const s = storage();
  const { _pendGuardar } = fabricaFila({ storage: s });
  for (let i = 0; i < 12; i++) await _pendGuardar(item('x' + i));
  ok(s.d.enviosPendentes.length === 10, 'teto de 10 envios');
  ok(s.d.pendDescartados === 2, 'o que passou do teto é CONTADO (o popup avisa), não some calado');
  ok(s.d.enviosPendentes[0].id === 'x2', 'sai o mais antigo');
}
{
  const { _pendGuardar } = fabricaFila({ storage: storage({}, true) });
  ok(await _pendGuardar(item('q')) === false, 'gravação que falha devolve false (o aviso não promete "nada foi perdido")');
}

// ── content.js: a janela ───────────────────────────────────────────────────────────────────
const janelaSrc = recorte(CONTENT, /    const hz = cfg\.horizonteServidor;[\s\S]*?const N = [^;]+;/, 'janela');
const janela = new Function('cfg', janelaSrc + '\nreturn N;');
const agora = Date.now();
const cfgBase = { lookbackDias: 30, casa: 'Betano', parceiro: 'A' };
ok(janela(Object.assign({}, cfgBase, { horizonteServidor: { casa: 'Betano', parceiro: 'A', dias: 95, ts: agora } })) === 95, 'quem volta depois de 3 meses varre 95 dias');
ok(janela(Object.assign({}, cfgBase, { horizonteServidor: { casa: 'Betano', parceiro: 'A', dias: 3, ts: agora } })) === 30, 'janela do usuário maior vale');
ok(janela(Object.assign({}, cfgBase, { horizonteServidor: { casa: 'Betano', parceiro: 'B', dias: 95, ts: agora } })) === 30, 'horizonte de OUTRA conta não vale');
ok(janela(Object.assign({}, cfgBase, { horizonteServidor: { casa: 'Betano', parceiro: 'A', dias: 95, ts: agora - 13 * 3600000 } })) === 30, 'horizonte velho (13 h) não vale');
ok(janela(cfgBase) === 30, 'sem horizonte: a janela do usuário');

// ── content.js: rodada parcial ─────────────────────────────────────────────────────────────
const parcialSrc = recorte(CONTENT, /    const parcial = \(diag[\s\S]*?: "";/, 'parcial');
const parcial = new Function('diag', 'casa', parcialSrc + '\nreturn parcial;');
ok(parcial({ nome: 'Thunderpick', extra: ' · HTTP 404 em /api/wagers' }, 'thunderpick') === 'Thunderpick: HTTP 404 em /api/wagers', 'erro do inject com bilhetes = parcial, com o motivo');
ok(parcial({ nome: 'Cloudbet', extra: ' · faça login, espere a página carregar e rode de novo' }, 'cloudbet') === '', 'dica de login não é erro de rodada');
ok(parcial({ nome: 'Bet365', extra: ' · frames: 2' }, 'bet365') === '', 'Bet365 tem aviso próprio');
ok(parcial({ nome: '3et', extra: '' }, '3et') === '', 'sem erro = completa');
ok(parcial(undefined, 'generica') === '', 'casa sem diagnóstico = completa');

// ── popup.js: a fila vista pelo Reenviar ───────────────────────────────────────────────────
const popSrc = recorte(POPUP, /const PEND_VALIDADE = [\s\S]*?\n(?=function _pendIdade)/, 'fila do popup');
const fabricaPop = new Function('chrome', popSrc + '\nreturn { _pendFila, _pendTirar };');
{
  const s = storage({
    enviosPendentes: [item('a', { parceiro: 'A' }), item('b', { parceiro: 'B' }), item('c', { casa: 'Superbet' }),
                      item('velha', { ts: agora - 31 * 24 * 3600000 })],
    envioPendente: { texto: 'legado', n: 2, casa: 'Betano', ts: agora },
    pendDescartados: 1,
  });
  const { _pendFila, _pendTirar } = fabricaPop({ storage: s });
  const f = await _pendFila({ casa: 'Betano', parceiro: 'A' });
  ok(f.minhas.map((p) => p.id).sort().join() === 'a,legado', 'Reenviar só manda o que é desta casa e conta (e o legado, que não tinha conta)');
  ok(f.outras.map((p) => p.id).sort().join() === 'b,c', 'de outra conta/casa fica guardado para lá');
  ok(f.descartadas === 2, 'vencida (30 dias) e descartada pelo teto são CONTADAS para o aviso');
  ok(!s.d.enviosPendentes.some((p) => p.id === 'velha') && !('pendDescartados' in s.d), 'a vencida sai e o contador zera depois de lido');
  await _pendTirar('a');
  ok(!s.d.enviosPendentes.some((p) => p.id === 'a'), 'enviado sai da fila');
}

if (falhas.length) {
  console.log('FALHAS:\n - ' + falhas.join('\n - '));
  process.exit(1);
}
console.log('fila/janela/parcial da extensão: ok');
