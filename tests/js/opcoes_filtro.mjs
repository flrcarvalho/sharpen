// Prova por EXECUÇÃO das LISTAS DE OPÇÃO dos filtros (s358).
//
// Três defeitos que este teste existe para impedir, os três medidos na base do Feca e os
// três SILENCIOSOS — nenhum deles gera erro, todos produzem uma lista que parece completa:
//
//   1. ORDEM. `.sort()` puro ordena por código UTF-16 e joga minúscula e acento para
//      depois do Z: `deLucca`, `eSoccer LBB` e `fullpicks` caíam atrás de `Zora`, e
//      `Caçador Basquete` atrás de `Cantos`. Medido: 63 dos 76 tipsters fora do lugar.
//      Ninguém some; quem rola até onde o nome deveria estar é que conclui que sumiu.
//   2. UNIÃO. As opções saem de `DADOS` ∪ `DADOS_ABERTAS`. Tipster que só tem aposta EM
//      ABERTO existe, e lendo só `DADOS` ele fica invisível justamente na tela "Em
//      Aberto", que é onde ele importa (`DADOS` só tem liquidada — ver `aplicarFeed`).
//   3. EXISTÊNCIA NÃO VEM DO BILHETE. O Fornecedor da tela de Custos é cadastro ∪ base:
//      conta comprada custa antes da primeira aposta. Medido: 26 contas ativas
//      cadastradas sem nenhum bilhete e 4 fornecedores só no cadastro.
//
// Tudo aqui é RECORTADO dos arquivos de produção — `cmpNome`/`recalcListasFiltro` do
// filters.js e `_c2Fornecedores`/`normForn` do custos2.js/gestao.js. Teste que
// reimplementa o código sob teste não detecta a mutação que o quebra (s286).
//
// O que este teste NÃO cobre, e é preciso dizer: o DOM. O `msRepintar` e o
// `atualizarOpcoesFiltros` escrevem `innerHTML` e dependem de `msb_<id>`/`ms-opts-<id>`
// existirem na página — nada é renderizado aqui. Que a repintura acontece na chegada do
// feed fresco também não se prova daqui: é uma chamada dentro do `loadData`.
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const CR = String.fromCharCode(13), LF = String.fromCharCode(10);
const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const lerJs = p => fs.readFileSync(p, 'utf8').split(CR + LF).join(LF);
const FILTERS = lerJs(process.env.ALVO_FILTERS
  || path.join(RAIZ, 'app/static/dash/assets/js/filters.js'));
const CUSTOS2 = lerJs(process.env.ALVO_CUSTOS2
  || path.join(RAIZ, 'app/static/dash/assets/js/charts/custos2.js'));
const GESTAO = lerJs(process.env.ALVO_GESTAO
  || path.join(RAIZ, 'app/static/dash/assets/js/charts/gestao.js'));

let falhas = 0;
const ok = (cond, msg) => { if (!cond) { console.error('FALHOU: ' + msg); falhas++; } };

const recorte = (src, ini, fim, nome) => {
  const a = src.indexOf(ini); if (a < 0) throw new Error('nao achei o inicio de ' + nome);
  const b = src.indexOf(fim, a); if (b < 0) throw new Error('nao achei o fim de ' + nome);
  return src.slice(a, b + fim.length);
};
const linha = (src, ini, nome) => {
  const a = src.indexOf(ini); if (a < 0) throw new Error('nao achei a linha de ' + nome);
  const b = src.indexOf(LF, a); if (b < 0) throw new Error('linha sem fim: ' + nome);
  return src.slice(a, b);
};

// ── Sandbox: só código de produção. DADOS/DADOS_ABERTAS/_contasCadastro entram por
// parâmetro porque no app são globais de outro arquivo. ──────────────────────
const fonte = [
  linha(FILTERS, 'function cmpNome(', 'cmpNome'),
  linha(FILTERS, 'function dobra(', 'dobra'),
  linha(FILTERS, 'let _LISTAS=', '_LISTAS'),
  recorte(FILTERS, 'function recalcListasFiltro(){', LF + '}', 'recalcListasFiltro'),
  linha(GESTAO, 'function normForn(', 'normForn'),
  recorte(CUSTOS2, 'function _c2Fornecedores(){', LF + '}', '_c2Fornecedores'),
].join(LF + LF) + LF
  + 'return { cmpNome, dobra, recalcListasFiltro, _c2Fornecedores };';

// Uma linha do feed. `operador` e `parceiro` entram porque são dois dos cinco eixos.
const L = (extra) => Object.assign(
  { data: '2026-09-01', esporte: 'Futebol', tipster: 'T', casa: 'KTO',
    parceiro: 'conta1', operador: 'Feca', fornecedor: 'Norte' }, extra || {});

// A ordem de entrada é a ALFABÉTICA ERRADA de propósito: o sort do V8 é estável, então
// uma base já na ordem esperada passaria sem regra nenhuma (s286).
const DADOS = [
  L({ tipster: 'Zora' }),
  L({ tipster: 'deLucca', esporte: 'Tênis', casa: 'Betão', operador: 'Lava' }),
  L({ tipster: 'Cantos', esporte: 'Críquete', parceiro: 'conta2', fornecedor: 'Âncora' }),
  L({ tipster: 'Caçador Basquete', esporte: 'Fórmula 1' }),
  L({ tipster: 'Zora' }),                       // repetida: a lista é de DISTINTOS
  L({ tipster: '', esporte: '', casa: '', parceiro: '', operador: '' }),   // vazios saem
  L({ parceiro: '—' }),                         // travessão é ausência, não uma conta
];
// Só em ABERTO: é o caso que a leitura de `DADOS` sozinha perderia.
const ABERTAS = [L({ tipster: 'Só Abertas', casa: 'Novibet', operador: 'Solo' })];

const F = new Function('DADOS', 'DADOS_ABERTAS', '_contasCadastro', fonte);
const comCadastro = (cad) => F(DADOS, ABERTAS, cad);

console.log('1) ordem pt-BR, insensível a caixa e acento');
{
  const L1 = comCadastro([]).recalcListasFiltro();
  // O `T` é o tipster default do `L()`, que sobra nas linhas que não o sobrescrevem.
  ok(L1.tipsters.join('|') === 'Caçador Basquete|Cantos|deLucca|Só Abertas|T|Zora',
    'ordem dos tipsters veio: ' + L1.tipsters.join('|'));
  // As duas metades que o `.sort()` puro erra, cada uma por um motivo:
  ok(L1.tipsters.indexOf('deLucca') < L1.tipsters.indexOf('Zora'),
    'MINUSCULA nao pode cair depois do Z (deLucca x Zora)');
  ok(L1.tipsters.indexOf('Caçador Basquete') < L1.tipsters.indexOf('Cantos'),
    'ACENTO nao pode cair depois da letra seguinte (Cacador x Cantos)');
  ok(L1.sports.join('|') === 'Críquete|Fórmula 1|Futebol|Tênis',
    'esportes em ordem pt-BR, veio: ' + L1.sports.join('|'));
}

console.log('2) união DADOS + DADOS_ABERTAS, e o que fica de fora');
{
  const L2 = comCadastro([]).recalcListasFiltro();
  ok(L2.tipsters.includes('Só Abertas'), 'tipster que so tem aposta EM ABERTO precisa existir');
  ok(L2.casas.includes('Novibet'), 'casa que so tem aposta EM ABERTO precisa existir');
  ok(L2.operadores.includes('Solo'), 'operador que so tem aposta EM ABERTO precisa existir');
  ok(!L2.tipsters.includes(''), 'nome vazio nao e uma opcao');
  ok(L2.tipsters.filter(t => t === 'Zora').length === 1, 'a lista e de DISTINTOS');
  ok(!L2.parceiros.includes('—'),
    'o travessao e AUSENCIA de conta, nao uma conta chamada travessao');
  ok(L2.parceiros.join('|') === 'conta1|conta2', 'contas vieram: ' + L2.parceiros.join('|'));
}

console.log('3) Fornecedor da tela de Custos: cadastro UNIAO base');
{
  // `richard` só existe no cadastro (conta comprada que ainda não apostou) e `Norte` está
  // nos dois lados — as duas metades importam: a primeira prova a união, a segunda prova
  // que ela não duplica.
  const CAD = [{ casa: 'KTO', conta: 'c9', fornecedor: 'richard' },
               { casa: 'KTO', conta: 'c1', fornecedor: 'Norte' },
               { casa: 'Betão', conta: 'c8', fornecedor: '' }];
  const semCad = comCadastro(null)._c2Fornecedores();
  ok(!semCad.includes('richard'),
    'antes do fetch do cadastro a lista e so a base (e nao pode explodir)');
  ok(semCad.includes('Norte') && semCad.includes('Âncora'), 'a base entra desde o 1o paint');

  const comCad = comCadastro(CAD)._c2Fornecedores();
  ok(comCad.includes('richard'),
    'fornecedor que SO existe no cadastro tem de aparecer numa tela de CUSTO');
  ok(comCad.filter(f => f === 'Norte').length === 1,
    'quem esta nos dois lados nao duplica');
  ok(comCad.includes('Eu'),
    'fornecedor vazio no cadastro vira "Eu" pelo normForn, nao some');
  ok(comCad.join('|') === comCad.slice().sort(
    (a, b) => a.localeCompare(b, 'pt-BR', { sensitivity: 'base', numeric: true })).join('|'),
    'fornecedores em ordem pt-BR, veio: ' + comCad.join('|'));
}

console.log(falhas ? LF + falhas + ' falha(s).' : 'opcoes_filtro: OK');
process.exit(falhas ? 1 : 0);
