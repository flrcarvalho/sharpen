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
//   5. DUAS TELAS, A MESMA ENTIDADE. Tipsters & Métodos listava só o CADASTRO, enquanto
//      Custo de Tipsters lista cadastro ∪ base. `garantir_tipster` cria o perfil sozinha
//      quando o tipster é atribuído EDITANDO um bilhete, mas não roda no `/salvar` — por
//      onde entram a IA, o bot e os imports. Um tipster vindo do bot dava para cobrar e
//      não dava para configurar. Zero casos medidos hoje; isto é blindagem.
//   4. EIXO QUE NÃO RECORTA. O Operador entrou na barra da tela de Custos, porque a regra
//      do projeto diz que ele e a Casa descrevem a CONTA e por isso os dois recortam
//      custo — a tela aplicava metade. Filtro que aparece e não filtra é PIOR que filtro
//      ausente: é o defeito da s322 com outra roupa.
//
// Tudo aqui é RECORTADO dos arquivos de produção — `cmpNome`/`recalcListasFiltro` do
// filters.js e `_c2Fornecedores`/`_c2sel`/`_c2passa`/`normForn` do custos2.js/gestao.js.
// Teste que reimplementa o código sob teste não detecta a mutação que o quebra (s286).
//
// A seção 4 mora NESTE arquivo, e não no `recorte_custos.mjs`, que seria o vizinho
// natural: aquele arquivo estava sendo editado por outra frente na mesma sessão. Se as
// duas frentes se encontrarem de novo, o lugar certo dela é lá.
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

// Ordem pt-BR da uniao usada na secao 5 (cadastro {Perfilado, Zora} + os da base).
const _tmEsperado = 'Caçador Basquete|Cantos|deLucca|Perfilado|Só Abertas|T|Zora';
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

console.log('4) o eixo Operador RECORTA de verdade na tela de Custos');
{
  // `_contaVida` (gestao.js) é quem sabe o operador de uma conta: ele sai do bilhete,
  // não do cadastro. Aqui ele entra dublado porque o que se prova é o USO dele.
  const VIDA = {
    'Norte||KTO': { c1: { op: 'Feca' }, c2: { op: 'Lava' } },
    'Âncora||Betão': { c3: { op: '' } },     // conta sem bilhete: operador desconhecido
  };
  const G = new Function('msGet', '_contaVida', [
    recorte(CUSTOS2, 'function _c2sel(){', LF + '}', '_c2sel'),
    recorte(CUSTOS2, 'function _c2opDaConta(', LF + '}', '_c2opDaConta'),
    recorte(CUSTOS2, 'function _c2passa(', LF + '}', '_c2passa'),
  ].join(LF + LF) + LF + 'return { _c2sel, _c2passa };');

  const sel = (ops) => {
    const S = { ca_custos_v2: new Set(), fo_custos_v2: new Set(), op_custos_v2: new Set(ops) };
    return G(id => S[id] || new Set(), VIDA);
  };

  const semOp = sel([]);
  ok(semOp._c2passa(semOp._c2sel(), 'KTO', 'Norte', 'c1'), 'sem selecao, tudo passa');
  ok(semOp._c2passa(semOp._c2sel(), 'KTO', 'Norte', 'c2'), 'sem selecao, tudo passa (2)');

  const soFeca = sel(['Feca']);
  ok(soFeca._c2passa(soFeca._c2sel(), 'KTO', 'Norte', 'c1'),
    'a conta do Feca passa com Feca selecionado');
  ok(!soFeca._c2passa(soFeca._c2sel(), 'KTO', 'Norte', 'c2'),
    'A CONTA DO LAVA TEM DE SAIR com Feca selecionado - senao o filtro nao filtra');
  ok(!soFeca._c2passa(soFeca._c2sel(), 'Betão', 'Âncora', 'c3'),
    'conta sem operador conhecido nao entra num recorte de operador');

  // A omissão do 4º argumento é SIGNIFICATIVA: a tabela de preços é por par
  // fornecedor × casa, e preço não pertence a operador nenhum.
  ok(soFeca._c2passa(soFeca._c2sel(), 'KTO', 'Norte'),
    'sem `conta`, o eixo Operador nao corta (tabela de precos)');
}

console.log('5) Tipsters & Metodos lista cadastro UNIAO base');
{
  const T = new Function('DADOS', 'DADOS_ABERTAS', '_tmCadastro', [
    recorte(GESTAO, 'function _tmSortNomes(nomes){', LF + '}', '_tmSortNomes'),
    recorte(GESTAO, 'function _tmNomes(){', LF + '}', '_tmNomes'),
  ].join(LF + LF) + LF + 'return { _tmNomes };');

  // `Perfilado` só no cadastro (cadastrado e ainda sem aposta), `Zora` nos dois lados,
  // `Só Abertas` só em aposta viva. As tres metades importam.
  const nomes = T(DADOS, ABERTAS, { Perfilado: {}, Zora: {} })._tmNomes();
  ok(nomes.includes('Perfilado'), 'quem esta so no cadastro continua na lista');
  ok(nomes.includes('Zora'), 'quem esta nos dois lados aparece');
  ok(nomes.filter(n => n === 'Zora').length === 1, 'e nao duplica');
  ok(nomes.includes('Caçador Basquete'),
    'TIPSTER QUE SO EXISTE EM BILHETE tem de aparecer - era o buraco do bot');
  ok(nomes.includes('Só Abertas'),
    'inclusive quem so tem aposta EM ABERTO (DADOS sozinho nao o veria)');
  ok(!nomes.includes(''), 'nome vazio nao vira perfil');
  ok(nomes.join('|') === _tmEsperado, 'ordem pt-BR, veio: ' + nomes.join('|'));
}

console.log(falhas ? LF + falhas + ' falha(s).' : 'opcoes_filtro: OK');
process.exit(falhas ? 1 : 0);
