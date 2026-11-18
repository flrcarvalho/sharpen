// s460 (plano 6.6, pedido do Feca em 18/11/2026): a captura que chega pela extensão é
// processada sozinha, sem o clique em "Processar Bilhetes".
//
// Este arquivo RECORTA do `index.html` de produção o trecho que vai do `let extAck` até o fim
// da `pollExtensao` (a fila de confirmação, o Processar automático e o poll) e o roda num
// contexto `vm` com dublês de DOM, fetch e relógio. Confere:
//   1. captura de texto na conta da conexão, formulário vazio antes → dispara o Processar;
//   2. formulário com texto colado à mão antes da captura → NÃO dispara;
//   3. usuário mexeu no texto depois da captura → NÃO dispara, e a tela pede o clique;
//   4. conta na tela diferente da conta da conexão → NÃO dispara;
//   5. processamento desta conta ainda rodando → espera e dispara depois que ele acaba;
//   6. duas capturas seguidas → UM disparo só, depois da última.
//
// O que NÃO está coberto: o `runExtractionCard` em si (o clique é dublado), o tempo real de
// 5 s (o relógio é dublado) e a aparência do `#ext-status` (texto num elemento que já existe).
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import vm from 'node:vm';

const AQUI = dirname(fileURLToPath(import.meta.url));
const ALVO = process.env.ALVO_INDEX || join(AQUI, '..', '..', 'app', 'static', 'index.html');
const HTML = readFileSync(ALVO, 'utf8').split('\r\n').join('\n');
const ini = HTML.indexOf('let extAck = [];');
const fim = HTML.indexOf('function desconectarExtensao(');
if (ini < 0 || fim < 0 || fim < ini) { console.error('FAIL: trecho do poll sumiu do index.html'); process.exit(1); }
const TRECHO = HTML.slice(ini, fim);

let falhas = 0;
const ok = (cond, msg) => { if (!cond) { falhas++; console.error('FAIL: ' + msg); } else console.log('ok: ' + msg); };

function montar({ textoAntes = '', selecionado = 7, sessaoConta = 7 } = {}) {
  const timers = [];
  const els = {
    texto: { value: textoAntes, dispatchEvent() {} },
    'btn-extrair': { cliques: 0, click() { this.cliques++; } },
  };
  let resposta = { conectado: true, capturas: [] };
  const ctx = {
    console,
    document: { getElementById: (id) => els[id] },
    Event: class { constructor(t) { this.type = t; } },
    encodeURIComponent,
    fetch: async () => ({ status: 200, ok: true, json: async () => resposta }),
    setTimeout: (fn) => { timers.push(fn); return timers.length; },
    clearTimeout: (h) => { if (h) timers[h - 1] = null; },
    clearInterval() {},
    extStatus: (msg, tipo) => { ctx._status = msg; ctx._tipo = tipo; },
    setStatus() {},
    b64ParaFile: () => ({}),
    adicionarArquivos: (fs) => { ctx.arquivos.push(...fs); },
    desconectarExtensao() {},
    IMG_MAX: 15,
    arquivos: [], csvFiles: [], xlsFiles: [], pdfFiles: [],
    parceiroSelecionado: selecionado == null ? null : { id: selecionado, casa: 'Thunderpick' },
    extSessao: { sessao_id: 's1', codigo: 'X', parceiro_id: sessaoConta },
    extCapturaParceiro: null,
    extConectadoAviso: true,
    _procPorConta: new Map(),
  };
  vm.createContext(ctx);
  vm.runInContext(TRECHO + '\n;globalThis.__poll = pollExtensao;', ctx);
  return {
    ctx, els, timers,
    async chega(...textos) {
      resposta = { conectado: true, capturas: textos.map((t, i) => ({ id: 'c' + Math.random() + i, tipo: 'texto', data: t })) };
      await ctx.__poll();
    },
    rodarRelogio() { const fs = timers.splice(0); fs.forEach(f => f && f()); },
  };
}

{ // 1
  const t = montar();
  await t.chega('[Código: 1] Stake: 10');
  ok(/Processando em alguns segundos/.test(t.ctx._status), '1: a tela diz que vai processar sozinha');
  t.rodarRelogio();
  ok(t.els['btn-extrair'].cliques === 1, '1: captura limpa na conta da conexão dispara o Processar');
}
{ // 2
  const t = montar({ textoAntes: 'texto colado à mão' });
  await t.chega('[Código: 1] Stake: 10');
  t.rodarRelogio();
  ok(t.els['btn-extrair'].cliques === 0, '2: formulário com texto de outra origem não dispara');
  ok(/Clique em Processar/.test(t.ctx._status), '2: a tela pede o clique');
}
{ // 3
  const t = montar();
  await t.chega('[Código: 1] Stake: 10');
  t.els.texto.value += '\nmais coisa digitada';
  t.rodarRelogio();
  ok(t.els['btn-extrair'].cliques === 0, '3: mexeu no texto depois da captura: não dispara');
  ok(/Clique em Processar/.test(t.ctx._status), '3: a tela pede o clique');
}
{ // 4
  const t = montar({ selecionado: 8, sessaoConta: 7 });
  await t.chega('[Código: 1] Stake: 10');
  t.rodarRelogio();
  ok(t.els['btn-extrair'].cliques === 0, '4: conta na tela diferente da conexão: não dispara');
}
{ // 4b: trocou de conta depois de a captura chegar
  const t = montar();
  await t.chega('[Código: 1] Stake: 10');
  t.ctx.parceiroSelecionado = { id: 9, casa: 'Thunderpick' };
  t.rodarRelogio();
  ok(t.els['btn-extrair'].cliques === 0, '4b: trocou de conta antes do disparo: não dispara');
}
{ // 5
  const t = montar();
  t.ctx._procPorConta.set(7, { fim: null });
  await t.chega('[Código: 1] Stake: 10');
  t.rodarRelogio();
  ok(t.els['btn-extrair'].cliques === 0, '5: com a conta processando, espera');
  ok(t.timers.length === 1, '5: e reagenda');
  t.ctx._procPorConta.get(7).fim = { msg: 'ok' };
  t.rodarRelogio();
  ok(t.els['btn-extrair'].cliques === 1, '5: dispara quando o processamento anterior acaba');
}
{ // 6
  const t = montar();
  await t.chega('[Código: 1] Stake: 10');
  const antigo = t.timers.length - 1;
  await t.chega('[Código: 2] Stake: 20');
  // O relógio da 1ª captura vence antes do da 2ª: ele tem de ter sido cancelado, senão o
  // Processar sai no meio da rajada.
  const f = t.timers[antigo]; t.timers[antigo] = null; if (f) f();
  ok(t.els['btn-extrair'].cliques === 0, '6: o relógio da 1ª captura foi cancelado pela 2ª');
  t.rodarRelogio();
  ok(t.els['btn-extrair'].cliques === 1, '6: duas capturas seguidas: um disparo só');
  ok(t.els.texto.value.includes('[Código: 1]') && t.els.texto.value.includes('[Código: 2]'), '6: com as duas no lote');
}

if (falhas) { console.error(`${falhas} falha(s)`); process.exit(1); }
