// Prova por EXECUÇÃO das duas caixas de changelog da home (s292).
//
// O conteúdo saiu do `inicio.html` e virou `app/changelog.json`, servido por GET /changelog.
// A troca é silenciosa quando quebra: rota fora do ar, JSON com outro formato ou campo
// renomeado não dão erro na tela — as caixas simplesmente somem, que é exatamente o
// sintoma de "changelog desatualizado" que esta sessão veio consertar.
//
// Aqui o `renderNovidades` REAL é recortado do `inicio.html` (nunca reescrito: teste que
// reimplementa o código não detecta a mutação que o quebra) e roda contra o changelog
// REAL do repo, com DOM e `jget` dublados.
//
// O que este teste NÃO cobre: o CSS/layout, a rota de verdade (é dublada aqui e testada
// em `tests/test_changelog.py`), e o localStorage do navegador — o `seen` é um Map em
// memória, então "o badge some na próxima visita" não é exercido no browser real.
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const CR = String.fromCharCode(13), LF = String.fromCharCode(10);
const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const ALVO = process.env.ALVO_INICIO || path.join(RAIZ, 'app', 'static', 'inicio.html');
const html = fs.readFileSync(ALVO, 'utf8').split(CR + LF).join(LF);
const CHANGELOG = JSON.parse(fs.readFileSync(path.join(RAIZ, 'app', 'changelog.json'), 'utf8'));

// Constantes + helpers + a função inteira, do arquivo de produção (fim exclusivo:
// pega tudo até o comentário do boot, que é o próximo bloco do arquivo).
const recorte = (ini, fim) => {
  const a = html.indexOf(ini); if (a < 0) throw new Error('não achei: ' + ini);
  const b = html.indexOf(fim, a); if (b < 0) throw new Error('não achei fim de: ' + ini);
  return html.slice(a, b);
};
const src = recorte('const NOV_DIAS=45;', '/* boot(force)');

let falhas = 0;
const ok = (cond, msg) => { if (!cond) { console.error('FALHOU: ' + msg); falhas++; } };

// ── DOM dublado: só o que o render usa (innerHTML, hidden, style.display) ──
function montar(resposta) {
  const nos = {};
  const el = id => (nos[id] = nos[id] || { id, innerHTML: '', hidden: null, style: {},
                                           classList: { toggle: (c, v) => { nos[id]['cls_' + c] = v; } } });
  ['nv-list', 'nv-new', 'novidades', 'su-list', 'su-new', 'supanel', 'novrow'].forEach(el);
  const store = new Map();
  const localStorage = { getItem: k => (store.has(k) ? store.get(k) : null),
                         setItem: (k, v) => store.set(k, v) };
  const esc = s => String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  const jget = async () => resposta;
  const fn = new Function('el', 'esc', 'jget', 'localStorage', `
    ${src}
    return renderNovidades;
  `)(el, esc, jget, localStorage);
  return { nos, render: fn };
}

const hoje = new Date();
const dias = n => new Date(hoje.getTime() - n * 864e5).toISOString().slice(0, 10);

// ── 1. changelog REAL monta as duas caixas ────────────────────────────────
{
  const { nos, render } = montar(CHANGELOG);
  await render('Feca');
  ok(nos['nv-list'].innerHTML.includes('nvrow'), 'caixa Novidades vazia com o changelog real');
  ok(nos['su-list'].innerHTML.includes('svrow'), 'caixa SharpenUp vazia com o changelog real');
  ok(nos['supanel'].style.display === '', 'painel do SharpenUp continuou escondido');
  ok(nos['novrow'].style.display === '', 'a linha das caixas continuou escondida');

  // A versão publicada tem de estar VISÍVEL, não só existir no arquivo: é o corte SU_MAX
  // que já escondeu itens recuperados antes (s254).
  const manifesto = JSON.parse(fs.readFileSync(path.join(RAIZ, 'extensor', 'manifest.json'), 'utf8')).version;
  ok(nos['su-list'].innerHTML.includes('v' + manifesto),
     `a versão publicada (v${manifesto}) não aparece na caixa — SU_MAX está cortando cedo demais`);
}

// ── 2. **negrito** vira <b>, e HTML do dado é ESCAPADO (XSS) ──────────────
{
  const { nos, render } = montar({
    novidades: [{ id: 'x', data: dias(1), tag: 'Sharpen', titulo: 'T',
                  texto: 'vai **forte** e <script>alert(1)</script>' }],
    sharpenup: [],
  });
  await render('Feca');
  const h = nos['nv-list'].innerHTML;
  ok(h.includes('<b>forte</b>'), 'o **negrito** não virou <b>');
  ok(!h.includes('<script>'), 'HTML do changelog chegou cru na tela (XSS)');
  ok(h.includes('&lt;script&gt;'), 'o <script> não foi escapado');
}

// ── 3a. corte de IDADE: novidade velha some, e some mesmo quando cabe no teto ──
// (a ordem importa: com as velhas no TOPO, tirar o corte de idade as coloca na tela —
//  com elas no fim, o teto de itens as esconderia por acidente e a mutacao escaparia)
{
  const velhas = Array.from({ length: 3 }, (_, i) => ({ id: 'v' + i, data: dias(60 + i), texto: 'velha' }));
  const novas = Array.from({ length: 5 }, (_, i) => ({ id: 'n' + i, data: dias(i), texto: 'nova' }));
  const { nos, render } = montar({ novidades: velhas.concat(novas), sharpenup: [] });
  await render('Feca');
  const linhas = (nos['nv-list'].innerHTML.match(/class="nvrow"/g) || []).length;
  ok(!nos['nv-list'].innerHTML.includes('velha'), 'novidade com mais de 45 dias continuou na tela');
  ok(linhas === 5, `corte de idade errado: ${linhas} linhas (esperado 5)`);
}

// ── 3b. teto de itens das duas caixas (NOV_MAX e SU_MAX) ──────────────────
{
  const novas = Array.from({ length: 12 }, (_, i) => ({ id: 'n' + i, data: dias(i), texto: 'nova' }));
  const versoes = Array.from({ length: 20 }, (_, i) => ({ id: 's' + i, v: 'v0.9.' + (20 - i), data: dias(i), texto: 'v' }));
  const { nos, render } = montar({ novidades: novas, sharpenup: versoes });
  await render('Feca');
  const linhasNov = (nos['nv-list'].innerHTML.match(/class="nvrow"/g) || []).length;
  const linhasSU = (nos['su-list'].innerHTML.match(/class="svrow"/g) || []).length;
  ok(linhasNov === 8, `NOV_MAX não cortou: ${linhasNov} linhas (esperado 8)`);
  ok(linhasSU === 12, `SU_MAX não cortou: ${linhasSU} linhas (esperado 12)`);
}

// ── 4. rota fora do ar / JSON quebrado → a linha inteira some, sem erro ───
for (const resposta of [null, {}, { novidades: 'nada', sharpenup: 7 }]) {
  const { nos, render } = montar(resposta);
  await render('Feca');
  ok(nos['novrow'].style.display !== '', 'resposta ruim deixou a linha das caixas aparecer vazia');
  ok(nos['nv-list'].innerHTML === '' && nos['su-list'].innerHTML === '',
     'resposta ruim renderizou alguma coisa');
}

// ── 5. o badge "novo" só acende para quem ainda não viu ───────────────────
{
  const feed = { novidades: [{ id: 'a', data: dias(1), texto: 'x' }], sharpenup: [{ id: 'b', v: 'v0.9.9', data: dias(1), texto: 'y' }] };
  const { nos, render } = montar(feed);
  await render('Feca');
  ok(nos['nv-new'].hidden === false, 'badge não acendeu na primeira visita');
  await render('Feca');                       // mesma sessão, mesmo store: agora já viu
  ok(nos['nv-new'].hidden === true, 'badge continuou aceso depois de visto');
}

if (falhas) { console.error(`\n${falhas} falha(s)`); process.exit(1); }
console.log('novidades_render.mjs: OK');
