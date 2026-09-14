// Prova por EXECUÇÃO do menu de mercados da coluna Aposta (s286).
//
// Recorta o código REAL do index.html — `carregarMercados`, `acSource`/`isAC`/`isMkt` e
// o render do item — e roda contra listas sintéticas. Nada aqui é reescrito à mão: uma
// cópia do código no teste passaria verde enquanto a tela quebrava.
//
// Provado por MUTAÇÃO (9/10 detectadas): corte dos favoritos, inversão fav↔todos,
// contagem em mercado nunca usado, união perdendo a base, ordem não-alfabética, item
// de tipster herdando a classe de mercado, abreviação de milhar, rodapé virando
// `.ac-item` (selecionável) e rodapé voltando a cortar calado.
//
// A 10ª ESCAPOU e fica registrada em vez de virar asserção inventada: baixar o
// `AC_TETO` de 200 para 50 não quebra nada aqui, porque o teto vive no `renderMenu` e
// este harness recorta o `acSource` e o render do ITEM, não o `renderMenu`. Ela é
// coberta do lado do pytest, por leitura do fonte
// (`test_teto_do_menu_nao_morde_lista_de_NOMES`), que é onde a prova é honesta: aqui
// seria preciso dublar o menu inteiro para provar um número.
//
// O que este teste NÃO cobre, e é preciso dizer: o gesto real no DOM (o duplo-clique
// abrir o menu, o Enter aplicar, o blur salvar). Aqui só se prova que `isAC` reconhece
// o editor inline — o resto é o motor de eventos da IIFE, que roda no navegador.
// Rodado pelo pytest em tests/test_menu_mercados.py.
import fs from 'fs';
const CR = String.fromCharCode(13), LF = String.fromCharCode(10);
import path from 'path';
import { fileURLToPath } from 'url';
// Caminho ancorado no PRÓPRIO arquivo, não no cwd: o pytest invoca daqui de qualquer
// diretório, e o ALVO existe só para a prova por mutação (aponta para uma cópia suja).
const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const h = fs.readFileSync(process.env.ALVO || path.join(RAIZ, 'app', 'static', 'index.html'), 'utf8').split(CR + LF).join(LF);

const corte = (ini, fim) => {
  const a = h.indexOf(ini); if (a < 0) throw new Error('não achei: ' + ini);
  const b = h.indexOf(fim, a); if (b < 0) throw new Error('não achei fim de: ' + ini);
  return h.slice(a, b + fim.length);
};
const src_carregar = corte('async function carregarMercados() {', LF + '}' + LF);
const src_source = corte('  const _tem = (el, c)', '  };' + LF);
// Vai ate o fim da EXPRESSAO, incluindo o rodape "+N nomes" que a s358 pendurou no
// `.join('')`. Parar no join deixaria o recorte com meia expressao e, pior, sem prova
// nenhuma do rodape.
const src_render = corte('    const mkt = isMkt(inp);', ": '');");

// ── stubs ─────────────────────────────────────────────────────────────────
const esportesList = ['Futebol', 'Tênis'], tipstersList = ['Peixe', 'LBB'];
const esc = s => String(s);
const RESP = {
  '/taxonomia': { categorias: ['Múltipla', 'Escanteios', 'Cartões', 'Gols', 'Handicap', 'Ambas Marcam', 'Dupla Chance', 'Impedimentos', 'Chutes no Gol', 'Desarmes', 'Faltas', 'DNB', 'H2H', 'Jardas', 'Corridas'] },
  // base do dono: frequência decrescente + grafia herdada de import que o MASTER não tem
  '/mercados': {
    mercados: [
      { nome: 'Múltipla', n: 412 }, { nome: 'Escanteios', n: 188 }, { nome: 'Cartões', n: 96 },
      { nome: 'Gols', n: 74 }, { nome: 'Handicap', n: 51 }, { nome: 'DNB', n: 44 },
      { nome: 'H2H', n: 39 }, { nome: 'Ambas Marcam', n: 31 }, { nome: 'Faltas', n: 22 },
      { nome: 'Desarmes', n: 19 }, { nome: 'Jardas', n: 12 }, { nome: 'Corridas', n: 9 },
      { nome: 'Dupla Chance', n: 7 }, { nome: 'Tênis de Mesa — Sets', n: 3 }]
  },
};
const fetch = async u => ({ json: async () => RESP[u] });

const F = new Function('fetch', 'esc', 'esportesList', 'tipstersList', `
  let mercadosFav = [], mercadosTodos = [], mercadosCont = {}, _taxoCategorias = null;
  ${src_carregar}
  ${src_source}
  return { carregarMercados, acSource, isAC, isMkt, estado: () => ({ mercadosFav, mercadosTodos, mercadosCont }), MKT_FAV };
`)(fetch, esc, esportesList, tipstersList);

// Render do item: o trecho recortado escreve em menu.innerHTML e lê mercadosCont/isMkt/inp.
const render = (classes, opts, cont, cortou = 0) => new Function('esc', 'inp', 'opts', 'mercadosCont', 'cortou', `
  const menu = {};
  const _tem = (el, c) => el.classList.contains(c);
  const isMkt = el => _tem(el, 'js-ac-mercado') || _tem(el, 'js-ac-mercado-todos');
  ${src_render}
  return menu.innerHTML;
`)(esc, { classList: { contains: c => classes.includes(c) } }, opts, cont, cortou);

const el = (...cs) => ({ classList: { contains: c => cs.includes(c) } });
let ok = 0, ko = 0;
const t = (nome, cond, extra = '') => { if (cond) { ok++; console.log('  ✓', nome); } else { ko++; console.log('  ✗', nome, extra); } };

await F.carregarMercados();
const st = F.estado();

console.log(LF + '1) carregarMercados — união e ordem');
t('favoritos vêm em ordem de frequência', st.mercadosFav[0] === 'Múltipla' && st.mercadosFav[1] === 'Escanteios');
t('lista completa é alfabética pt-BR', st.mercadosTodos.slice(0, 3).join('|') === 'Ambas Marcam|Cartões|Chutes no Gol', st.mercadosTodos.slice(0, 3).join('|'));
t('MASTER traz o que ele nunca apostou', st.mercadosTodos.includes('Chutes no Gol') && !st.mercadosFav.includes('Chutes no Gol'));
t('base preserva grafia herdada que o MASTER não tem', st.mercadosTodos.includes('Tênis de Mesa — Sets'));
t('união não duplica o que existe nos dois lados', st.mercadosTodos.filter(x => x === 'Múltipla').length === 1);

console.log(LF + '2) acSource — os dois menus');
const fav = F.acSource(el('ap-inline-inp', 'js-ac-mercado'), false);
t('duplo-clique abre nos favoritos', fav[0] === 'Múltipla');
t('favoritos cortam em 12 (a base tem 14)', fav.length === 12 && !fav.includes('Dupla Chance'), 'len=' + fav.length);
const digitou = F.acSource(el('ap-inline-inp', 'js-ac-mercado'), true);
t('ao digitar, varre a lista COMPLETA', digitou.includes('Chutes no Gol') && digitou.length === st.mercadosTodos.length);
const todos = F.acSource(el('js-ac-mercado-todos'), false);
t('modal abre completo sem digitar nada', todos.length === st.mercadosTodos.length && todos.includes('Chutes no Gol'));

console.log(LF + '3) não quebrei o que já existia');
t('esporte segue na fonte de esporte', F.acSource(el('js-ac-esporte'), false) === esportesList);
t('esporte ignora o flag de filtro', F.acSource(el('js-ac-esporte'), true) === esportesList);
t('tipster segue no default', F.acSource(el('js-ac-tipster'), false) === tipstersList);
t('input sem classe cai no tipster (comportamento antigo)', F.acSource(el('outra'), false) === tipstersList);

console.log(LF + '3b) ponto de contato com o motor de eventos');
// O editor inline nasce com className 'ap-inline-inp js-ac-mercado' (_exInlineStart).
// Se isAC não o reconhecer, o menu nunca abre; se reconhecer DEMAIS, o campo stake
// passa a abrir dropdown de tipster — os dois lados importam.
t('editor inline de mercado é reconhecido pelo motor', F.isAC(el('ap-inline-inp', 'js-ac-mercado')));
t('editor inline de OUTRO campo segue fora do motor', !F.isAC(el('ap-inline-inp')));
t('campo do modal é reconhecido', F.isAC(el('js-ac-mercado-todos')));
t('tipster/esporte seguem reconhecidos', F.isAC(el('js-ac-tipster')) && F.isAC(el('js-ac-esporte')));
t('só os dois de mercado contam como mercado', F.isMkt(el('js-ac-mercado')) && F.isMkt(el('js-ac-mercado-todos')) && !F.isMkt(el('js-ac-tipster')));

console.log(LF + '4) render do item');
const cont = st.mercadosCont;
const hMkt = render(['js-ac-mercado'], ['Múltipla', 'Chutes no Gol'], cont);
t('mercado usado mostra a contagem', hMkt.indexOf('<span class="ac-count">412</span>') >= 0);
t('mercado nunca usado sai SEM número', hMkt.indexOf('Chutes no Gol') >= 0 && hMkt.split('ac-count').length === 2);
t('item de mercado leva a classe própria', hMkt.indexOf('ac-item ac-item--mkt') >= 0);
const hTip = render(['js-ac-tipster'], ['Peixe'], cont);
t('item de tipster continua exatamente o de antes', hTip === '<div class="ac-item" data-i="0">Peixe</div>', hTip);
const hMil = render(['js-ac-mercado'], ['Múltipla'], { 'Múltipla': 12345 });
t('milhar em pt-BR, sem abreviar', hMil.indexOf('12.345') >= 0 && !/12,3k|12k/.test(hMil), hMil);

console.log(LF + '5) lista truncada DIZ que truncou (s358)');
// O teto era 50 e calado: com 76 tipsters, 26 nomes nao existiam para quem rolava. O
// rodape nao pode ser `.ac-item` -- o clique e o teclado casam por essa classe, e um
// rodape selecionavel aplicaria "+26 nomes" como se fosse um nome.
const hCorte = render(['js-ac-tipster'], ['Peixe'], cont, 26);
t('rodape aparece quando cortou', hCorte.indexOf('ac-mais') >= 0, hCorte);
t('rodape diz QUANTOS ficaram de fora', hCorte.indexOf('+26') >= 0, hCorte);
t('rodape NAO e selecionavel (sem a classe ac-item)', hCorte.split('ac-item').length === 2, hCorte);
t('singular quando falta um so', render(['js-ac-tipster'], ['Peixe'], cont, 1).indexOf('+1 nome ') >= 0);
t('sem corte, nenhum rodape', render(['js-ac-tipster'], ['Peixe'], cont, 0).indexOf('ac-mais') < 0);

console.log(LF + ok + ' passaram · ' + ko + ' falharam');
process.exit(ko ? 1 : 0);
