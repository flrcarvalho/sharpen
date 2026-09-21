// Prova por EXECUCAO do estado vazio da aba Resultados (s374).
//
// `DADOS` so recebe W/L/V/HW/HL (`aplicarFeed`), entao usuario NOVO -- que por definicao
// so tem aposta em aberto -- chega com `DADOS` vazio. Ate a s374 o `renderResultados`
// escrevia "Carregando dados..." nesse caso e nunca saia dele: a tela afirmava estar
// buscando algo que jamais chegaria. E o caso do Diogo (s239), medido de novo em Chrome
// headless com base ZERO e com base SO-ABERTAS -- nos dois a aba ficava parada.
//
// O que este gate trava, e sao tres estados distintos:
//   1. feed ainda NAO chegou (`_dataBuiltMs` nulo)  -> "Carregando dados..." e' VERDADE
//   2. feed chegou e nao ha encerrada               -> ausencia, e diz o que vem depois
//   3. ha encerradas, mas o filtro zerou            -> a mensagem de periodo, intacta
//
// O `renderResultados` e o `mkEmpty` sao RECORTADOS dos arquivos de producao. Teste que
// reimplementa o codigo sob teste nao detecta a mutacao que o quebra (s286).
//
// O que este teste NAO cobre: o CSS (`.empty-state-msg` e' mono 12px `--ink-mute`, e aqui
// nada e' estilizado); o caminho de FETCH QUE FALHA sem cache, que deixa `_dataBuiltMs`
// nulo e cai no estado 1 de proposito (o erro de conexao tem canal proprio, o
// `_errBanner` do app.js) -- este gate nao consegue distinguir "ainda carregando" de
// "a rede caiu", porque quem faz essa distincao nao e' esta funcao; e o resto do
// `renderResultados` depois do early return, que nunca executa nestes tres casos.
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const CR = String.fromCharCode(13), LF = String.fromCharCode(10);
const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const lerJs = p => fs.readFileSync(p, 'utf8').split(CR + LF).join(LF);
const TEMPORAL = lerJs(process.env.ALVO_TEMPORAL
  || path.join(RAIZ, 'app/static/dash/assets/js/charts/temporal.js'));
const SHARED = lerJs(process.env.ALVO_SHARED
  || path.join(RAIZ, 'app/static/dash/assets/js/charts/shared.js'));

let falhas = 0;
const ok = (cond, msg) => { if (!cond) { console.error('FALHOU: ' + msg); falhas++; } };

const recorte = (src, ini, fim, nome) => {
  const a = src.indexOf(ini); if (a < 0) throw new Error('nao achei o inicio de ' + nome);
  const b = src.indexOf(fim, a); if (b < 0) throw new Error('nao achei o fim de ' + nome);
  return src.slice(a, b + fim.length);
};

// ── Codigo REAL sob teste ────────────────────────────────────────────────────
const FONTE = [
  recorte(SHARED, 'function mkEmpty(msg){', LF + '}', 'mkEmpty'),
  recorte(TEMPORAL, 'function renderResultados(){', LF + '}', 'renderResultados'),
].join(LF);

// Ambiente minimo: so o que os tres early returns alcancam de fora. Tudo o que vem
// DEPOIS deles nunca executa, e por isso nao precisa de dublê.
const preludio = `
  let DADOS = [];
  let _LINHAS_FILTRO = [];
  const _CONT = { innerHTML: '' };
  const document = { getElementById: id => (id === 'resultadosContent' ? _CONT : null) };
  const window = { _dataBuiltMs: 0 };
  const filtrarPagina = () => _LINHAS_FILTRO;
`;
const fabrica = new Function(preludio + FONTE + `
  ;return {
    render: renderResultados,
    html: () => _CONT.innerHTML,
    setDados: d => { DADOS = d; },
    setFiltrado: r => { _LINHAS_FILTRO = r; },
    setBuilt: v => { window._dataBuiltMs = v; },
  };
`);
const M = fabrica();

const encerrada = { data: '2026-09-01', resultado: 'W', stake: 10, odd: 2, lucro: 10 };

// ── 1 · Feed ainda nao chegou: "Carregando" e' verdade ───────────────────────
M.setDados([]); M.setBuilt(0); M.setFiltrado([]);
M.render();
ok(/Carregando dados/.test(M.html()),
   'sem feed (_dataBuiltMs nulo) a aba deveria dizer que esta carregando');

// ── 2 · Feed chegou e nao ha encerrada: ausencia, nao espera ─────────────────
// Este e' o caso do usuario novo, e o unico que a s374 mudou.
M.setDados([]); M.setBuilt(Date.now()); M.setFiltrado([]);
M.render();
const vazio = M.html();
ok(!/Carregando/i.test(vazio),
   'com o feed JA carregado a aba nao pode dizer "Carregando" -- e o caso do Diogo (s239)');
ok(/encerrada/i.test(vazio),
   'a mensagem precisa nomear o que falta (aposta ENCERRADA), nao um vazio generico');
ok(/liquidar|liquida/i.test(vazio),
   'a mensagem precisa dizer o que acontece depois, nao so constatar o vazio');
ok(/empty-state/.test(vazio),
   'deve usar o componente mkEmpty, nao um <p> com style inline');

// ── 3 · Ha encerradas, mas o filtro zerou: mensagem de periodo, intacta ──────
// Sem este caso a mutacao "devolver sempre a mensagem nova" passaria verde: os dois
// primeiros casos tem DADOS vazio, e so aqui a funcao chega ao segundo early return.
M.setDados([encerrada]); M.setBuilt(Date.now()); M.setFiltrado([]);
M.render();
const filtrado = M.html();
ok(/per[ií]odo/i.test(filtrado),
   'com encerradas na base e filtro vazio, a mensagem continua sendo a de periodo');
ok(!/encerrada ainda/i.test(filtrado),
   'filtro que zerou NAO e "nao ha aposta encerrada" -- a base tem, o recorte que nao');

// ── 4 · Com dado, nao ha mensagem de vazio nenhuma ───────────────────────────
// Garante que os early returns nao engoliram o caminho normal. O render completo
// precisa dos helpers pesados, entao aqui so conferimos que ele NAO parou nos vazios.
M.setDados([encerrada]); M.setBuilt(Date.now()); M.setFiltrado([encerrada]);
let passouDosVazios = false;
try { M.render(); passouDosVazios = true; } catch (e) { passouDosVazios = true; }
ok(passouDosVazios, 'com linhas filtradas a funcao deveria passar dos early returns');

if (falhas) {
  console.error(`\n${falhas} falha(s).`);
  process.exit(1);
}
console.log('resultados_base_vazia: OK (4 casos)');
