// Prova por EXECUÇÃO das regras novas do Painel de Contas (s333, Fases 7 e 8).
//
// O que vive só no front e ninguém mais confere:
//
//   1. A PRECEDÊNCIA do estado da conta, agora com um degrau novo:
//      Divergência › Aguardando resultado › Aguardando tipster › Parada há N dias ›
//      Sem caixa › Conciliada.
//      `Parada` entra DEPOIS das três esperas de propósito: conta parada que ainda
//      tem item pendente tem o que resolver, e o abandono só é a leitura principal
//      quando não sobrou nada na frente. Sem a tag, essa conta se disfarçava de
//      `Conciliada` — limpa porque ninguém a usa.
//   2. A ANATOMIA da pílula: lista fechada, número dentro de <b>, zero abreviação.
//   3. A AGREGAÇÃO por fornecedor, que é o que a zona nova e o 4º KPI leem.
//
// Tudo é RECORTADO do `index.html` de produção, nunca reescrito aqui: teste que
// reimplementa o código não detecta a mutação que o quebra (s286).
//
// O que este teste NÃO cobre: a grade em px, os degraus de container e o contraste
// — isso é render, e render se mede no headless, não aqui. Também não cobre o
// clique (filtro por casa/fornecedor), que é DOM.
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const CR = String.fromCharCode(13), LF = String.fromCharCode(10);
const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const HTML = fs.readFileSync(process.env.ALVO_INDEX || path.join(RAIZ, 'app/static/index.html'),
                             'utf8').split(CR + LF).join(LF);

let falhas = 0;
const ok = (cond, msg) => { if (!cond) { console.error('FALHOU: ' + msg); falhas++; } };
const recorte = (ini, fim, nome) => {
  const a = HTML.indexOf(ini); if (a < 0) throw new Error('não achei o início de ' + nome);
  const b = HTML.indexOf(fim, a); if (b < 0) throw new Error('não achei o fim de ' + nome);
  return HTML.slice(a, b + fim.length);
};

// ── Ambiente mínimo: só o que os recortes tocam ─────────────────────────────
// Os recortes vão para dentro de UM escopo só (`new Function`), com as variáveis de
// que dependem declaradas antes e um `set` para mexer nelas de fora. Chamar `eval`
// linha a linha não serve: em módulo ESM o eval é estrito e a declaração morre no
// escopo dele — o recorte "roda" e some, que é um verde sem código exercido.
const CODIGO = [
  "let contasTab = 'ativas';",
  'let caixaVisaoCache = null;',
  'let casasCarregadas = [];',
  'const parceirosCache = {}, abertasPorParceiro = {};',
  "const window = { __donoEfetivo: 'Feca' };",
  'function abertasDe(casa, nome) { return (abertasPorParceiro[casa] || {})[nome] || 0; }',
  recorte('function esc(s) {', LF + '}', 'esc'),
  recorte('const _TAG_STATUS = {', LF + '};', '_TAG_STATUS'),
  recorte('const _TAG_TITULO = {', LF + '};', '_TAG_TITULO'),
  recorte('function _diasDesde(iso) {', LF + '}', '_diasDesde'),
  recorte('const _PARADA_DIAS =', ';', '_PARADA_DIAS'),
  recorte('function tagStatus(estado, n) {', LF + '}', 'tagStatus'),
  recorte('function _statusDaConta(cx, abertas, semTipster) {', LF + '}', '_statusDaConta'),
  recorte('function _painelParseForn(nome) {', LF + '}', '_painelParseForn'),
  recorte("const _FORN_EU = '__eu__';", LF, '_FORN_EU'),
  recorte('function _painelFornDe(nome) {', LF, '_painelFornDe'),
  recorte('function _painelRotuloEu() {', LF + '}', '_painelRotuloEu'),
  recorte('function _iniciais(nome) {', LF + '}', '_iniciais'),
  recorte('function _caixaPorConta() {', LF + '}', '_caixaPorConta'),
  recorte('function _painelAggForn(v) {', LF + '}', '_painelAggForn'),
  `return {
     tagStatus, _statusDaConta, _diasDesde, _PARADA_DIAS, _TAG_STATUS, _TAG_TITULO,
     _painelParseForn, _painelFornDe, _FORN_EU, _painelRotuloEu, _iniciais, _painelAggForn,
     set(o) {
       if ('tab' in o) contasTab = o.tab;
       if ('cache' in o) caixaVisaoCache = o.cache;
       if ('casas' in o) casasCarregadas = o.casas;
       if ('parceiros' in o) Object.assign(parceirosCache, o.parceiros);
       if ('abertas' in o) Object.assign(abertasPorParceiro, o.abertas);
     },
   };`,
].join(LF + LF);

const P = new Function(CODIGO)();
const { tagStatus, _statusDaConta, _diasDesde, _PARADA_DIAS, _TAG_STATUS, _TAG_TITULO,
        _painelParseForn, _painelFornDe, _FORN_EU, _painelRotuloEu, _iniciais,
        _painelAggForn } = P;

const DIA = 86400000;
const hoje = () => new Date().toISOString();
const atras = d => new Date(Date.now() - d * DIA).toISOString();

// ── A. `_diasDesde` ─────────────────────────────────────────────────────────
ok(_diasDesde(null) === null && _diasDesde('') === null, 'sem data devolve null, não 0');
ok(_diasDesde('nunca') === null, 'lixo devolve null');
ok(_diasDesde(hoje()) === 0, 'hoje = 0 dias');
ok(_diasDesde(atras(62)) === 62, '62 dias atrás = 62');
// Relógio adiantado (data no futuro) não pode virar contagem negativa: "há -3 dias"
// é um número que ninguém sabe ler, e ele reprovaria o corte de 30 por acidente.
ok(_diasDesde(new Date(Date.now() + 3 * DIA).toISOString()) === 0, 'futuro não vira negativo');

// ── B. Precedência do estado ────────────────────────────────────────────────
// A conta usada em todos os casos: ligada, com caixa e PARADA há 62 dias. É ela que
// mostra qual degrau ganha — se `parada` subisse na ordem, os quatro primeiros casos
// quebrariam de uma vez.
const velha = { ligada: true, banca: 100, estado: 'confere', ultima_captura: atras(62) };
const nova = { ligada: true, banca: 100, estado: 'confere', ultima_captura: atras(2) };

ok(_statusDaConta({ ...velha, estado: 'divergente' }, 5, 3)[0] === 'divergencia',
   'divergência ganha de tudo');
ok(_statusDaConta(velha, 5, 3)[0] === 'aguardando', 'aguardando resultado ganha de tipster e de parada');
ok(_statusDaConta(velha, 5, 3)[1] === 5, 'o número da tag é o de apostas em espera');
ok(_statusDaConta(velha, 0, 3)[0] === 'tipster', 'aguardando tipster ganha de parada');
ok(_statusDaConta(velha, 0, 0)[0] === 'parada', 'sem espera nenhuma, a conta velha é PARADA');
ok(_statusDaConta(velha, 0, 0)[1] === 62, 'a tag carrega o número REAL de dias');
ok(_statusDaConta(nova, 0, 0)[0] === 'conciliada', 'conta usada recentemente segue conciliada');
// O corte é EXCLUSIVO: 30 dias ainda não é parada, 31 é. Um corte que pegasse o
// próprio 30 marcaria como abandonada a conta usada uma vez por mês.
ok(_statusDaConta({ ...nova, ultima_captura: atras(_PARADA_DIAS) }, 0, 0)[0] === 'conciliada',
   'exatamente 30 dias ainda não é parada');
ok(_statusDaConta({ ...nova, ultima_captura: atras(_PARADA_DIAS + 1) }, 0, 0)[0] === 'parada',
   '31 dias já é parada');
// Conta que nunca capturou nada não "parou": nunca começou. Sem esta guarda toda
// conta recém-criada nasceria com a tag de abandono.
ok(_statusDaConta({ ligada: false, banca: 0, estado: 'sem_caixa', ultima_captura: null }, 0, 0)[0] === 'semcaixa',
   'conta sem captura nenhuma não é parada');
ok(_statusDaConta({ ...velha, ligada: false, banca: 0 }, 0, 0)[0] === 'parada',
   'parada ganha de sem caixa: abandono é a leitura mais forte');
// `reconferir` = divergência endereçada, ainda não rebatida. Entra como um item em
// espera, e por isso NÃO pode cair em `parada`.
ok(_statusDaConta({ ...velha, estado: 'reconferir' }, 0, 0)[0] === 'aguardando',
   'reconferir conta como item em espera');
P.set({ tab: 'arquivadas' });
ok(_statusDaConta(velha, 0, 0)[0] === 'arquivada', 'na aba Arquivadas o estado é sempre arquivada');
P.set({ tab: 'ativas' });

// ── C. Anatomia da pílula ───────────────────────────────────────────────────
const parada = tagStatus('parada', 62);
ok(parada.includes('tag-status parada'), 'a pílula parada usa o modificador .parada');
ok(parada.includes('<b>62</b>'), 'o número vai dentro de <b> — ele é o dado');
ok(/Parada há <b>62<\/b> dias/.test(parada), 'rótulo exato "Parada há N dias"');
ok(tagStatus('inventado', 3) === '<span></span>', 'estado fora da lista não vira tag');
// Nenhum rótulo abreviado e nenhum teto no número, em nenhum estado da lista.
for (const [estado] of Object.entries(_TAG_STATUS)) {
  const h = tagStatus(estado, 199);
  ok(!/\b(pend|conc|calc|div|apr)\.|\+99/.test(h), 'sem abreviação nem teto em ' + estado);
  ok(!/[A-ZÀ-Ú]{4,}/.test(h.replace(/<[^>]*>/g, '').replace(/class=|tag-status/g, '')),
     'caixa alta é do CSS, nunca do dado, em ' + estado);
}
ok(Object.keys(_TAG_STATUS).every(k => _TAG_TITULO[k]), 'todo estado tem explicação no title');

// ── D. Fornecedor: quem é dono da conta ─────────────────────────────────────
ok(_painelParseForn('Léo [Pauta]') === 'Pauta', 'o fornecedor sai do colchete');
ok(_painelFornDe('Conta minha') === _FORN_EU, 'conta sem colchete é do próprio usuário');
ok(_painelRotuloEu() === 'Eu (Feca)', 'o rótulo do próprio usuário nomeia o dono');
ok(_iniciais('Richard') === 'RI' && _iniciais('Ana Paula') === 'AP' && _iniciais('Eu (Feca)') === 'EU',
   'iniciais vêm do NOME, nunca de índice ou de valor');

// ── E. Agregação por fornecedor ─────────────────────────────────────────────
P.set({
  casas: ['Bet365', 'Betano'],
  parceiros: {
    'Bet365': [{ id: 1, nome: 'A [Richard]' }, { id: 2, nome: 'B [Gustavo]' }, { id: 3, nome: 'C' }],
    'Betano': [{ id: 4, nome: 'D [Richard]' }],
  },
  abertas: { 'Bet365': { 'A [Richard]': 2 } },
  cache: { contas: [
    { parceiro_id: 1, ligada: true, banca: 300 },
    { parceiro_id: 2, ligada: true, banca: 100 },
    { parceiro_id: 3, ligada: true, banca: 600 },
    // `banca` NÃO-zero com `ligada:false`: se o fixture usasse 0 aqui, tirar a
    // checagem de `ligada` do código não mudaria número nenhum e a mutação passaria.
    { parceiro_id: 4, ligada: false, banca: 999 },
  ] },
});
const agg = _painelAggForn({ totais: { banca: 1000 } });
ok(agg.linhas.length === 3, 'uma linha por fornecedor, mais a do próprio usuário');
// Ordenação por CAIXA, decrescente — não por nome nem por número de contas.
ok(agg.linhas.map(l => l.nome).join('|') === 'Eu (Feca)|Richard|Gustavo',
   'ordenado por caixa decrescente: ' + agg.linhas.map(l => l.nome + ':' + l.caixa).join(', '));
ok(agg.linhas[0].eu === true && agg.linhas[1].eu === false, 'a linha do próprio usuário se identifica');
ok(agg.terceiros === 400, 'em contas de terceiros = 300 + 100, sem a própria (600)');
ok(agg.nForn === 2, 'o contador de fornecedores não conta o próprio usuário');
const richard = agg.linhas.find(l => l.nome === 'Richard');
ok(richard.contas === 2, 'as contas do fornecedor somam entre casas');
ok(richard.espera === 2, 'as apostas em espera do fornecedor somam');
ok(richard.caixa === 300, 'conta sem caixa ligada NÃO entra como zero na soma do fornecedor');

if (falhas) { console.error(falhas + ' falha(s)'); process.exit(1); }
console.log('contas_status.mjs OK');
