// Câmbio e corretoras no front (s398, passo 6 do docs/PLANO_MOEDA_POR_CONTA.md).
//
// O que este arquivo prova, executando o código RECORTADO dos arquivos de produção:
//
// A. `calcCambioFiltrado` (gestao.js) soma só as vendas e taxas DENTRO do período, e o
//    total que desce no P/L Líquido é realizado − taxas; sem dado, n = 0 (o card some);
// B. `_cxCorrVisivelPara` (index.html): destino/origem só em saque e depósito de conta em
//    outra moeda, nunca em conta em real nem na Polymarket (Caixa automática);
// C. `_cxCorrLer`: taxa sem corretora é erro; com corretora viajam id e taxa; taxa vazia
//    vira ausência (null), nunca zero; campos fora da tela não mandam nada (null).
//
// O que NÃO está coberto: o desenho do card (`renderPainelCambio`) e dos modais, que são
// medidos no navegador (servidor_demo com DEMO_CAMBIO=1), e o clique real.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import vm from 'node:vm';

const AQUI = dirname(fileURLToPath(import.meta.url));
const RAIZ = join(AQUI, '..', '..');
const ler = (env, p) => readFileSync(process.env[env] || p, 'utf8').replace(/\r\n/g, '\n');
const INDEX = ler('ALVO_INDEX', join(RAIZ, 'app', 'static', 'index.html'));
const GESTAO = ler('ALVO_GESTAO', join(RAIZ, 'app', 'static', 'dash', 'assets', 'js', 'charts', 'gestao.js'));

let falhas = 0;
const ok = (cond, msg) => { if (!cond) { console.error('  ✗ ' + msg); falhas++; } };
const eq = (a, b, msg) => ok(JSON.stringify(a) === JSON.stringify(b), msg + ', veio ' + JSON.stringify(a));

const recorteFn = (src, nome) => {
  const m = src.match(new RegExp('^(\\s*)function ' + nome + '\\([^)]*\\)\\s*\\{[\\s\\S]*?^\\1\\}', 'm'));
  if (!m) throw new Error('não achei a função ' + nome);
  return m[0];
};

// ── A. período ───────────────────────────────────────────────────────────────
{
  const ctx = { range: null };
  vm.createContext(ctx);
  vm.runInContext(`
    let cbData = null;
    function _selRange() { return range; }
    ${recorteFn(GESTAO, 'calcCambioFiltrado')}
    this.api = { calc: calcCambioFiltrado, set: d => { cbData = d; } };`, ctx);
  const A = ctx.api;
  A.set({ bolsos: {
    USDT: { realizados: [{ data: '2026-09-30', brl: 100 }, { data: '2026-10-04', brl: -62.3 }],
            taxas: [{ data: '2026-10-03', brl: 15.2 }] },
    USD: { realizados: [{ data: '2026-10-10', brl: 40 }], taxas: [] },
  } });
  ctx.range = { from: '2026-10-01', to: '2026-10-31' };
  const r = A.calc('overview');
  ok(Math.abs(r.realizado - (-62.3 + 40)) < 1e-9, 'A: soma as vendas do mês nas duas moedas, sem a de setembro: ' + r.realizado);
  ok(Math.abs(r.taxas - 15.2) < 1e-9, 'A: soma as taxas do mês');
  ok(Math.abs(r.total - (-22.3 - 15.2)) < 1e-9, 'A: o total que desce no P/L é realizado − taxas: ' + r.total);
  eq([r.nVendas, r.nTaxas, r.n], [2, 1, 3], 'A: contagens');
  ctx.range = null;
  ok(Math.abs(A.calc('overview').realizado - 77.7) < 1e-9, 'A: sem período, a base inteira');
  A.set(null);
  eq(A.calc('overview').n, 0, 'A: sem dado, nada (o card não aparece)');
}

// ── B e C. o modal da Caixa ──────────────────────────────────────────────────
{
  const D = { 'cxm-corr': { value: '' }, 'cxm-taxa': { value: '' } };
  const ctx = { D };
  vm.createContext(ctx);
  vm.runInContext(`
    let caixaAtual = null, _cxModo = 'saque';
    function _numBR(v) { return Number(String(v).replace(/\\./g, '').replace(',', '.')) || 0; }
    const document = { getElementById: id => D[id] };
    ${recorteFn(INDEX, '_cxCorrVisivelPara')}
    ${recorteFn(INDEX, '_cxCorrLer')}
    this.api = { vis: _cxCorrVisivelPara, ler: _cxCorrLer,
      conta: c => { caixaAtual = c; }, modo: m => { _cxModo = m; } };`, ctx);
  const C = ctx.api;
  C.conta({ moeda: 'USDT', casa: 'Betpanda' });
  ok(C.vis('saque') && C.vis('deposito'), 'B: saque e depósito em USDT têm destino/origem');
  ok(!C.vis('ajuste') && !C.vis('inicial'), 'B: ajuste e saldo inicial não têm');
  C.conta({ moeda: 'BRL', casa: 'Betano' });
  ok(!C.vis('saque'), 'B: conta em real não transfere para corretora');
  C.conta({ moeda: 'USD', casa: 'Polymarket' });
  ok(!C.vis('saque'), 'B: a Polymarket tem Caixa automática, sem lançamento à mão');
  C.conta(null);
  ok(!C.vis('saque'), 'B: sem conta, nada');

  C.conta({ moeda: 'USDT', casa: 'Betpanda' }); C.modo('saque');
  D['cxm-corr'].value = ''; D['cxm-taxa'].value = '2,00';
  ok(C.ler() && C.ler().erro, 'C: taxa sem corretora é erro');
  D['cxm-corr'].value = '7'; D['cxm-taxa'].value = '1,50';
  eq(C.ler(), { corretora_id: 7, taxa: 1.5 }, 'C: corretora e taxa viajam');
  D['cxm-taxa'].value = '';
  eq(C.ler(), { corretora_id: 7, taxa: null }, 'C: taxa vazia é ausência, nunca zero');
  D['cxm-corr'].value = ''; D['cxm-taxa'].value = '';
  eq(C.ler(), { corretora_id: null, taxa: null }, 'C: sem destino, o saque sai do Sharpen');
  C.modo('ajuste');
  eq(C.ler(), null, 'C: fora de saque/depósito, o formulário não manda transferência');
}

if (falhas) { console.error(falhas + ' falha(s)'); process.exit(1); }
console.log('cambio_front: ok');
