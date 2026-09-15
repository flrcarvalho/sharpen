// Prova por EXECUÇÃO do bloco de tipster da sidebar (s362).
//
// O `/static/sb-tipster.js` REAL é carregado num DOM dublado — nunca reescrito aqui:
// teste que reimplementa o código sob teste não detecta a mutação que o quebra.
//
// O que se prova:
//   1. Monograma derivado do nome (duas palavras, uma palavra, vazio).
//   2. "Zero não é ausência": janela sem aposta resolvida vira TRAVESSÃO, não 0,00.
//      É a regra que separa conta nova de conta com desempenho neutro medido.
//   3. Máscara de dinheiro: `.money` com sinal em U+2212, cor só no número, unidade
//      `u` na vitrine e `R$` no host — e NUNCA milhar abreviado.
//   4. Vitrine é read-only: sem botão no avatar, sem menu, sem <input type=file>.
//   5. "Vendo base de X" ocupa o lugar do plano — o aviso de que se está escrevendo
//      na base de outro não pode se perder na mudança de layout.
//
// O que este teste NÃO cobre: CSS (tamanho, cor efetiva, se o bloco cabe na sidebar —
// isso se mede renderizando), o upload de verdade (precisa de rede e de servidor), e
// o arrastar-e-soltar (o DOM dublado sempre "solta" e nunca arrasta).
import fs from 'fs';
import path from 'path';
import assert from 'assert';
import { fileURLToPath } from 'url';

const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const ALVO = process.env.ALVO_SB || path.join(RAIZ, 'app', 'static', 'sb-tipster.js');

// ── DOM dublado: só o que o módulo toca ──────────────────────────────────────
function criarNo(tag) {
  const no = {
    tagName: String(tag).toUpperCase(),
    filhos: [], atributos: {}, classes: new Set(),
    _html: '', _texto: '', hidden: false, style: {}, title: '', alt: '', type: '',
    get className() { return [...this.classes].join(' '); },
    set className(v) { this.classes = new Set(String(v).split(/\s+/).filter(Boolean)); },
    get classList() {
      const c = this.classes;
      return {
        add: (...n) => n.forEach((x) => c.add(x)),
        remove: (...n) => n.forEach((x) => c.delete(x)),
        toggle: (n, f) => (f === undefined ? (c.has(n) ? c.delete(n) : c.add(n)) : (f ? c.add(n) : c.delete(n))),
        contains: (n) => c.has(n),
      };
    },
    get children() { return this.filhos; },
    get innerHTML() { return this._html; },
    set innerHTML(v) { this._html = String(v); this.filhos = analisar(String(v)); },
    get textContent() { return this._texto || this.filhos.map((f) => f.textContent).join(''); },
    set textContent(v) { this._texto = String(v); this.filhos = []; },
    get scrollWidth() { return 100; },
    get clientWidth() { return 100; },
    setAttribute(k, v) { this.atributos[k] = String(v); },
    getAttribute(k) { return k in this.atributos ? this.atributos[k] : null; },
    removeAttribute(k) { delete this.atributos[k]; },
    appendChild(f) { this.filhos.push(f); return f; },
    addEventListener() {},
    contains() { return false; },
    click() {},
    focus() {},
    querySelector(sel) { return this.querySelectorAll(sel)[0] || null; },
    querySelectorAll(sel) {
      const alvo = sel.trim();
      const casa = (n) => {
        if (alvo.startsWith('.')) return n.classes.has(alvo.slice(1));
        if (alvo.startsWith('input[')) return n.tagName === 'INPUT';
        if (alvo.startsWith('button.')) return n.tagName === 'BUTTON' && n.classes.has(alvo.split('.')[1]);
        return n.tagName === alvo.toUpperCase();
      };
      const fora = [];
      const anda = (n) => n.filhos.forEach((f) => { if (casa(f)) fora.push(f); anda(f); });
      anda(this);
      return fora;
    },
  };
  return no;
}

// Parser mínimo de tags: o módulo monta o bloco por innerHTML e depois busca os nós
// por querySelector, então precisamos das tags, das classes e do texto — nada mais.
function analisar(html) {
  const pilha = [{ filhos: [] }];
  const re = /<(\/)?([a-zA-Z][\w-]*)((?:"[^"]*"|'[^']*'|[^>"'])*?)(\/)?>|([^<]+)/g;
  let m;
  while ((m = re.exec(html))) {
    const [, fecha, tag, attrs, auto, texto] = m;
    if (texto !== undefined) {
      const t = texto.trim();
      if (t) { const n = criarNo('#text'); n.textContent = t; pilha[pilha.length - 1].filhos.push(n); }
      continue;
    }
    if (fecha) { if (pilha.length > 1) pilha.pop(); continue; }
    const n = criarNo(tag);
    (attrs || '').replace(/([\w:-]+)\s*=\s*"([^"]*)"/g, (_, k, v) => {
      if (k === 'class') n.className = v; else n.atributos[k] = v;
      if (k === 'hidden') n.hidden = true;
      return '';
    });
    if (/\shidden(\s|$)/.test(attrs || '')) n.hidden = true;
    pilha[pilha.length - 1].filhos.push(n);
    if (!auto && !['img', 'input', 'br', 'path'].includes(tag.toLowerCase())) pilha.push(n);
  }
  return pilha[0].filhos;
}

const janela = {
  document: {
    createElement: criarNo,
    addEventListener() {},
    body: criarNo('body'),
  },
  FormData: class { append() {} },
  URL: { createObjectURL: () => 'blob:x', revokeObjectURL() {} },
  fetch: () => Promise.reject(new Error('rede desligada no teste')),
};
janela.window = janela;

// Carrega o arquivo de PRODUÇÃO dentro desse escopo.
const fonte = fs.readFileSync(ALVO, 'utf8');
new Function('window', 'document', 'FormData', 'URL', 'fetch', fonte + '\n;return window.SbTipster;');
const SbTipster = new Function(
  'window', 'document', 'FormData', 'URL', 'fetch',
  fonte + '\n;return window.SbTipster;'
)(janela, janela.document, janela.FormData, janela.URL, janela.fetch);

// ── 1. Monograma ─────────────────────────────────────────────────────────────
assert.strictEqual(SbTipster.iniciais('Soh Props'), 'SP', 'duas palavras → uma inicial de cada');
assert.strictEqual(SbTipster.iniciais('Sharpen'), 'SH', 'uma palavra → as duas primeiras letras');
assert.strictEqual(SbTipster.iniciais('  Grego   Tips  VIP '), 'GT', 'espaço extra não conta como palavra');
assert.strictEqual(SbTipster.iniciais(''), '?', 'sem nome, nunca uma caixa vazia');

// ── helpers de leitura do bloco ──────────────────────────────────────────────
const celulas = (bloco) => bloco.el.querySelector('.sb-tipster__stats').children.map((n) => n.textContent);
const plano = (bloco) => bloco.el.querySelector('.sb-tipster__plan').textContent;

// ── 2. Zero não é ausência ───────────────────────────────────────────────────
const novo = SbTipster.montar({ editavel: true, unidade: 'reais' });
novo.aplicar({ nome: 'Conta Nova', mes: { apostas: 0, pl: 0, roi: 0 }, historico: { apostas: 0, pl: 0, roi: 0 } });
const cel = celulas(novo);
// Índices 0-2 são o cabeçalho, 3 e 6 são os rótulos de linha (ROI, P/L). Os VALORES
// são 4, 5 (mês/histórico do ROI) e 7, 8 (do P/L).
const VALORES = [4, 5, 7, 8];
assert.ok(VALORES.every((i) => cel[i] === '—'),
  'janela sem aposta resolvida tem de virar travessão, e veio: ' + JSON.stringify(cel));
assert.ok(!cel.join('').includes('0,00'), 'conta nova nunca mostra 0,00 — leria como neutro MEDIDO');

// ── 3. Máscara de dinheiro ───────────────────────────────────────────────────
const host = SbTipster.montar({ editavel: true, unidade: 'reais' });
host.aplicar({
  nome: 'Ricardo', plano: 'VIP',
  mes: { apostas: 10, pl: 13632.4, roi: 4.82 },
  historico: { apostas: 900, pl: -267002.47, roi: -4.55 },
});
const linhas = host.el.querySelector('.sb-tipster__stats').innerHTML;
assert.ok(linhas.includes('13.632,40'), 'milhar com ponto e decimal com vírgula (pt-BR)');
assert.ok(linhas.includes('R$'), 'host mostra R$');
// Cada máscara com sinal próprio é conferida POR SI. Procurar só "tem um U+2212 em
// algum lugar" deixa passar a troca por hífen numa delas, porque a outra ainda põe o
// dela — foi o que a mutação mostrou.
assert.ok(linhas.includes('−R$'), 'P/L negativo: minus U+2212 colado no R$ (fmtPL)');
assert.ok(linhas.includes('−4,55%'), 'ROI negativo: minus U+2212 (fmtPct)');
assert.ok(!/>-/.test(linhas), 'nenhum hífen ASCII iniciando número — parseFloat devolve NaN nele');
assert.ok(!/\d\s*[kKmM]\b/.test(linhas), 'milhar NUNCA abreviado (check-tokens §d)');
assert.ok(linhas.includes('money-sign'), 'o R$ vive no .money-sign, que é menor e neutro');
assert.ok(/money (neg|pos)/.test(linhas), 'a cor vai na classe do .money, nunca inline');

const vitrine = SbTipster.montar({ editavel: false, unidade: 'u' });
vitrine.aplicar({
  nome: 'Soh Props', plano: 'VIP',
  mes: { apostas: 10, pl: 52.3, roi: 16.17 },
  historico: { apostas: 900, pl: -318.7, roi: -11.04 },   // negativo de propósito: é ele que exerce o minus
});
const linhasU = vitrine.el.querySelector('.sb-tipster__stats').innerHTML;
assert.ok(linhasU.includes('money-u'), 'vitrine mostra a unidade `u`');
assert.ok(!linhasU.includes('R$'), 'vitrine é 100% em unidades — R$ ali é vazamento do modo privado');
assert.ok(linhasU.includes('−'), 'o minus em unidades também é U+2212 (o fmtU tem sinal próprio)');
assert.ok(!linhasU.includes('-318'), 'hífen ASCII quebra o parseNum de quem reler o número da tela');

// ── 4. Vitrine é read-only ───────────────────────────────────────────────────
assert.strictEqual(vitrine.el.querySelector('button.sb-tipster__av'), null,
  'sem sessão não há o que autorizar upload: o avatar não pode ser botão');
assert.strictEqual(vitrine.el.querySelector('.sb-tipster__menu'), null, 'vitrine não tem menu');
assert.strictEqual(vitrine.el.querySelector('input[type=file]'), null, 'vitrine não tem seletor de arquivo');
assert.strictEqual(vitrine.el.querySelector('.sb-tipster__chev'), null,
  'sem menu, o chevron prometeria uma ação que não existe');
assert.ok(host.el.querySelector('button.sb-tipster__av'), 'no host o avatar É o gatilho do upload');
assert.ok(host.el.querySelector('input[type=file]'), 'no host há seletor de arquivo real (alcançável por teclado)');

// ── 5. Plano, ausência de plano e "vendo base de" ────────────────────────────
assert.strictEqual(plano(host), 'Plano VIP');
// O TEXTO sozinho nao prova o badge: com a classe `tester` colada em todo mundo, o
// plano pago continuaria escrito "Plano VIP" e sairia AZUL. Foi o que a mutacao mostrou.
assert.ok(!host.el.querySelector('.sb-tipster__plan').classes.has('tester'),
  'plano pago fica no ambar — o azul e do estado Tester');
const sem = SbTipster.montar({ editavel: true, unidade: 'reais' });
sem.aplicar({ nome: 'Fulano', plano: null, mes: {}, historico: {} });
// Conta sem assinatura e' conta de TESTE, e o selo diz o que ela E', nao o que lhe falta.
// Um selo vazio (ou ausente) leria como defeito no lugar do estado.
assert.strictEqual(plano(sem), 'Tester', 'sem assinatura o selo vira Tester, nunca some calado');
assert.ok(sem.el.querySelector('.sb-tipster__plan').classes.has('tester'),
  'e troca o ambar do plano pelo azul da marca — a cor e o que separa os estados num corpo de 10px');
assert.ok(!sem.el.querySelector('.sb-tipster__plan').classes.has('vendo'),
  'Tester nao pode carregar a classe de aviso junto');

const vendo = SbTipster.montar({ editavel: true, unidade: 'reais' });
vendo.aplicar({ nome: 'Marina', dono: 'Marina', vendo: true, plano: 'VIP', mes: {}, historico: {} });
assert.ok(plano(vendo).startsWith('Vendo'),
  'o aviso de "ver base de" ocupa o lugar do plano — quem escreve achando que é a própria base escreve na do vizinho');
assert.ok(vendo.el.classes.has('vendo'), 'e o bloco inteiro muda de borda');

console.log('OK — sb_tipster.mjs: monograma, ausência, máscara, read-only e "vendo" verificados.');
