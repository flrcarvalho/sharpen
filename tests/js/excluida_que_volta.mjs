// s460 (Feca, 18/11/2026): a aposta excluída que volta pela captura. Este arquivo RECORTA do
// `index.html` de produção o trecho das ações (de `function _voltouCorpo(` até o
// `addEventListener` do "Manter todas") e o roda num `vm` com dublês de fetch e DOM. Confere:
//   1. "Manter" de uma linha manda os ids, e só os ids;
//   2. "Manter todas" manda a conta ativa (casa e parceiro), sem ids;
//   3. "Excluir de vez" pergunta antes, e com "Cancelar" não chama o servidor;
//   4. com "OK" chama a rota de excluir de vez e recarrega a grade;
//   5. erro do servidor aparece no status, com o motivo.
// NÃO cobre: o desenho do selo e da barra (conferido em headless) e o modal de liberar.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import vm from 'node:vm';

const AQUI = dirname(fileURLToPath(import.meta.url));
const ALVO = process.env.ALVO_INDEX || join(AQUI, '..', '..', 'app', 'static', 'index.html');
const HTML = readFileSync(ALVO, 'utf8').split('\r\n').join('\n');
const ini = HTML.indexOf('function _voltouCorpo(');
const fim = HTML.indexOf("document.getElementById('voltou-manter-todas')");
if (ini < 0 || fim < 0 || fim < ini) { console.error('FAIL: trecho das ações sumiu do index.html'); process.exit(1); }
const TRECHO = HTML.slice(ini, fim);

let falhas = 0;
const ok = (c, m) => { if (!c) { falhas++; console.error('FAIL: ' + m); } else console.log('ok: ' + m); };

function montar({ confirma = true, status = 200, resposta = { mantidas: 1, excluidas: 1 } } = {}) {
  const ctx = {
    console, JSON,
    chamadas: [], recargas: 0, statusMsg: null, statusTipo: null, perguntas: 0,
    parceiroSelecionado: { id: 7, casa: 'Stake.com', nome: 'Gabriel' },
  };
  ctx.fetch = async (url, op) => {
    ctx.chamadas.push({ url, corpo: JSON.parse(op.body) });
    return { ok: status < 400, status, json: async () => (status < 400 ? resposta : { detail: 'motivo do servidor' }) };
  };
  ctx.confirm = () => { ctx.perguntas++; return confirma; };
  ctx.setExpStatus = (m, t) => { ctx.statusMsg = m; ctx.statusTipo = t; };
  ctx.carregarGrade = async () => { ctx.recargas++; };
  ctx.atualizarIncompletos = () => {};
  vm.createContext(ctx);
  vm.runInContext(TRECHO + '\n;globalThis.__m = voltouManter; globalThis.__x = voltouExcluirDeVez;', ctx);
  return ctx;
}

{ const c = montar(); await c.__m([11, 12]);
  ok(c.chamadas.length === 1 && c.chamadas[0].url === '/bilhetes/voltaram/manter', '1: manter chama a rota de manter');
  ok(JSON.stringify(c.chamadas[0].corpo) === '{"ids":[11,12]}', '1: só com os ids');
  ok(c.recargas === 1, '1: recarrega a grade'); }
{ const c = montar(); await c.__m(null, true);
  ok(JSON.stringify(c.chamadas[0].corpo) === '{"casa":"Stake.com","parceiro":"Gabriel"}', '2: manter todas manda a conta ativa'); }
{ const c = montar({ confirma: false }); await c.__x([11]);
  ok(c.perguntas === 1 && c.chamadas.length === 0, '3: excluir de vez pergunta e, cancelado, não chama o servidor'); }
{ const c = montar(); await c.__x([11]);
  ok(c.chamadas.length === 1 && c.chamadas[0].url === '/bilhetes/voltaram/excluir-de-vez', '4: OK chama excluir de vez');
  ok(c.recargas === 1, '4: e recarrega a grade'); }
{ const c = montar({ status: 500 }); await c.__m([11]);
  ok(c.statusTipo === 'err' && /motivo do servidor/.test(c.statusMsg), '5: erro aparece no status com o motivo'); }

if (falhas) { console.error(`${falhas} falha(s)`); process.exit(1); }
