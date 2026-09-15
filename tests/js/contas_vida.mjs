// Aba CONTAS (s365) — as réguas que, quando quebram, NÃO dão erro nenhum.
//
// Quatro delas, e todas produzem número plausível quando invertidas:
//
//   1. **O período NÃO corta a duração.** Ele escolhe QUAIS CONTAS ENTRAM (vida
//      intersectando a janela) e nada mais. Truncar a vida ao filtro inventaria número:
//      uma conta que viveu de janeiro a junho não durou "31 dias" porque alguém filtrou
//      março — e 31 é um número perfeitamente plausível numa coluna de dias.
//   2. **Turnover e P/L, ao contrário, SEGUEM o período**, como no resto do app. As duas
//      metades desta regra são load-bearing: travar só uma deixa a vizinha livre.
//   3. **Mediana é a mediana**, não a média. Elas coincidem em dado simétrico, então o
//      caso de teste precisa de CAUDA — senão a asserção passa com a régua errada.
//   4. **Conta própria (custo zero declarado) entra no múltiplo; conta comprada sem
//      preço fica FORA.** São coisas diferentes: a primeira custou zero de verdade, a
//      segunda tem custo que existe e não foi declarado. Somar a segunda como zero
//      inflaria o retorno — a ausência se disfarçando de zero.
//
// Executa `_cnBase`, `_cnPorCasa` e `_cnMediana` RECORTADAS do `contas.js` de produção,
// com o `_buildContaVida` / `_custoDaConta` / `normForn` REAIS do `gestao.js` e o
// `_selRange` / `msGet` / `gfs` / `_ymd` REAIS do `filters.js`. Nada é reimplementado.
//
// O que NÃO está coberto aqui: o HTML (cor, máscara, Escada de Tinta), o layout, o
// tooltip da mediana e a corrida de boot — tudo isso foi medido no Chrome, dentro do
// iframe do dash, por `scripts/demo/medir_aba_contas.mjs`. Um dublê de DOM aceitaria
// qualquer um deles calado.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const AQUI = dirname(fileURLToPath(import.meta.url));
const RAIZ = join(AQUI, '..', '..');
const BASE = join(RAIZ, 'app', 'static', 'dash', 'assets', 'js');
// ALVO_* existem para a prova por MUTAÇÃO.
const CONTAS = readFileSync(process.env.ALVO_CONTAS || join(BASE, 'charts', 'contas.js'), 'utf8');
const GESTAO = readFileSync(process.env.ALVO_GESTAO || join(BASE, 'charts', 'gestao.js'), 'utf8');
const FILTROS = readFileSync(join(BASE, 'filters.js'), 'utf8');
const LF = '\n';

let falhas = 0;
const ok = (cond, msg) => { if (!cond) { console.error('  ✗ ' + msg); falhas++; } };
const eq = (obtido, esperado, msg) => ok(obtido === esperado, msg + ', veio ' + obtido);

// One-liner PRIMEIRO: o recorte multilinha vai até o próximo `}` na coluna 0 e, numa
// função de uma linha, engoliria as declarações de topo do arquivo.
const recorteFn = (src, nome, arq) => {
  const uma = src.match(new RegExp('^function ' + nome + '\\([^)]*\\)\\{.*\\}$', 'm'));
  if (uma) return uma[0];
  const m = src.match(new RegExp('^function ' + nome + '\\([^)]*\\)\\{[\\s\\S]*?^\\}', 'm'));
  if (!m) throw new Error('não achei a função ' + nome + ' no ' + arq);
  return m[0];
};

const FONTE = [
  'let _contaVida=null, _contasVida=null, custoData={}, _precosForn=null;',
  'let DADOS=[], DADOS_ABERTAS=[];',
  'let MSS={};',
  'let FS={};',
  ...['gfs', '_ymd', '_today', '_selRange', 'msGet'].map(n => recorteFn(FILTROS, n, 'filters.js')),
  ...['normForn', '_buildContaVida', '_degrausPreco', '_precoVigenteEm', '_dataDoPreco',
      '_custoDaConta'].map(n => recorteFn(GESTAO, n, 'gestao.js')),
  'let _cnPop="ambas";',
  ...['_cnMediana', '_cnMedia', '_cnBase', '_cnPorCasa'].map(n => recorteFn(CONTAS, n, 'contas.js')),
  'globalThis.__api={ set pop(v){_cnPop=v;}, get pop(){return _cnPop;},',
  '  setDados(d,a){DADOS=d;DADOS_ABERTAS=a||[];},',
  '  setCadastro(c){_contasVida=c;_contaVida=null;},',
  '  setCusto(c){custoData=c;},',
  '  setFiltro(f){FS={contas:Object.assign({df:"",dt:"",qd:0,qt:""},f||{})};},',
  '  setCasas(s){MSS["ca_contas"]=new Set(s||[]);},',
  '  base(){return _cnBase();}, porCasa(c){return _cnPorCasa(c);},',
  '  mediana(x){return _cnMediana(x);}, media(x){return _cnMedia(x);} };',
].join(LF);

const { runInNewContext } = await import('node:vm');
const ctx = { console, Date, Math, Set, Object, Array, JSON, Number, String, setTimeout, document: undefined };
runInNewContext(FONTE, ctx);
const api = ctx.__api;

const HOJE = new Date();
const ymd = d => d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
const hoje = ymd(HOJE);

// ── Dado sintético que EXERCE cada regra ────────────────────────────────────
// `Longeva` vive jan→jun e aposta em janeiro E em março: é ela que separa "duração da
// vida" de "duração dentro da janela", e é ela que separa turnover recortado de turnover
// inteiro. Sem aposta DENTRO e FORA da janela na mesma conta, a regra 2 não é exercida.
const bilhete = (casa, conta, forn, data, stake, lucro) => ({
  casa, conta, fornecedor: forn, parceiro: conta + ' [' + forn + ']',
  data, stake, lucro, resultado: 'W', operador: 'Feca',
});

const DADOS = [
  bilhete('Alfa', 'Longeva', 'JC', '2026-01-15', 100, 10),
  bilhete('Alfa', 'Longeva', 'JC', '2026-03-10', 200, 20),
  bilhete('Alfa', 'Longeva', 'JC', '2026-06-10', 400, 40),
  bilhete('Alfa', 'Curta', 'JC', '2026-03-05', 50, 5),
  bilhete('Alfa', 'Media', 'JC', '2026-03-01', 50, 5),
  bilhete('Alfa', 'Media', 'JC', '2026-03-20', 50, 5),
  bilhete('Beta', 'Propria', 'Eu', '2026-03-08', 300, 90),
  bilhete('Beta', 'SemPreco', 'Novo', '2026-03-09', 300, 60),
  bilhete('Gama', 'Velha', 'JC', '2025-02-01', 70, 7),      // vida toda FORA do filtro
];
// Cadastro: quem tem `arquivada_em` está encerrada; quem não tem e não está arquivado
// vive até HOJE (é assim que `_buildContaVida` marca "ativa").
const CADASTRO = [
  { casa: 'Alfa', conta: 'Longeva', fornecedor: 'JC', adquirida_em: '2026-01-10', arquivada_em: '2026-06-15', arquivado: true, custo: 0 },
  { casa: 'Alfa', conta: 'Curta', fornecedor: 'JC', adquirida_em: '2026-03-01', arquivada_em: '2026-03-06', arquivado: true, custo: 0 },
  { casa: 'Alfa', conta: 'Media', fornecedor: 'JC', adquirida_em: '2026-03-01', arquivada_em: '2026-03-31', arquivado: true, custo: 0 },
  { casa: 'Beta', conta: 'Propria', fornecedor: 'Eu', adquirida_em: '2026-03-01', arquivada_em: null, arquivado: false, custo: 0 },
  { casa: 'Beta', conta: 'SemPreco', fornecedor: 'Novo', adquirida_em: '2026-03-01', arquivada_em: null, arquivado: false, custo: 0 },
  { casa: 'Gama', conta: 'Velha', fornecedor: 'JC', adquirida_em: '2025-01-01', arquivada_em: '2025-02-10', arquivado: true, custo: 0 },
];
// Preço por par `fornecedor||casa`. `Eu||Beta` fica de fora de propósito: conta própria
// não tem preço, e é isso que a distingue da comprada sem preço (`Novo||Beta`).
const CUSTO = { 'JC||Alfa': 500 };

api.setDados(DADOS, []);
api.setCadastro(CADASTRO);
api.setCusto(CUSTO);
api.setCasas([]);

console.log('— 1. Mediana é a mediana, e o dado tem CAUDA (senão média e mediana coincidem)');
eq(api.mediana([3, 4, 5, 8, 51]), 5, 'mediana de 5 valores com cauda deve ser 5');
eq(api.media([3, 4, 5, 8, 51]), 14.2, 'média dos mesmos valores deve ser 14,2');
ok(api.mediana([3, 4, 5, 8, 51]) !== api.media([3, 4, 5, 8, 51]),
   'o caso de teste precisa distinguir mediana de média');
eq(api.mediana([2, 4, 6, 8]), 5, 'mediana par é a média dos dois do meio');
eq(api.mediana([]), 0, 'mediana de lista vazia é 0');

console.log('— 2. O período ESCOLHE quem entra, e NÃO corta a duração');
api.pop = 'ambas';
api.setFiltro({ df: '2026-03-01', dt: '2026-03-31' });
const marco = api.base();
const nomes = marco.contas.map(c => c.conta).sort();
eq(nomes.join(','), 'Curta,Longeva,Media,Propria,SemPreco',
   'a conta cuja vida é disjunta do período (Velha, de 2025) tem de SAIR');
const longeva = marco.contas.find(c => c.conta === 'Longeva');
// jan/10 → jun/15 = 157 dias. Se o período cortasse, daria 31 (o março inteiro).
eq(longeva.dur, 157, 'duração da Longeva é a VIDA INTEIRA (jan/10 a jun/15)');
ok(longeva.dur !== 31, 'duração NÃO pode ser o tamanho da janela do filtro');
eq(longeva.dias, 3, 'dias ativos são os 3 dias com aposta na vida inteira, não só o de março');

console.log('— 3. Turnover e P/L, ao contrário, SEGUEM o período');
eq(longeva.turn, 200, 'turnover da Longeva conta só a aposta de março');
eq(longeva.pl, 20, 'P/L da Longeva conta só a aposta de março');
api.setFiltro({});
const tudo = api.base();
const longevaTudo = tudo.contas.find(c => c.conta === 'Longeva');
eq(longevaTudo.turn, 700, 'sem período, o turnover soma as três apostas');
eq(longevaTudo.dur, 157, 'e a duração NÃO muda quando o período sai — ela nunca dependeu dele');

console.log('— 4. População recorta ativas e inativas');
api.setFiltro({ df: '2026-03-01', dt: '2026-03-31' });
api.pop = 'ativas';
const ativas = api.base().contas.map(c => c.conta).sort().join(',');
eq(ativas, 'Propria,SemPreco', 'ativas = as que não têm carimbo de arquivamento');
api.pop = 'inativas';
const inativas = api.base().contas.map(c => c.conta).sort().join(',');
eq(inativas, 'Curta,Longeva,Media', 'inativas = as arquivadas');
api.pop = 'ambas';
eq(api.base().contas.length, 5, 'ambas = a união das duas');

console.log('— 5. Duração média x mediana por casa, na população que responde "quanto aguenta"');
api.pop = 'inativas';
const alfa = api.porCasa(api.base().contas).find(c => c.casa === 'Alfa');
// Longeva 157d, Media 31d, Curta 6d → média 64,67 · mediana 31
eq(Math.round(alfa.dur), 65, 'duração média da Alfa');
eq(alfa.durMed, 31, 'duração MEDIANA da Alfa (a do meio, não a média)');
ok(Math.round(alfa.dur) !== alfa.durMed, 'média e mediana têm de diferir neste caso');

console.log('— 6. Própria entra no múltiplo com custo zero; comprada SEM preço fica fora');
api.pop = 'ambas';
const porCasa = api.porCasa(api.base().contas);
const beta = porCasa.find(c => c.casa === 'Beta');
eq(beta.proprias, 1, 'Beta tem 1 conta própria (fornecedor Eu)');
eq(beta.semPreco, 1, 'Beta tem 1 conta COMPRADA sem preço lançado');
eq(beta.custo, 0, 'Beta não tem custo lançado em nenhuma conta');
eq(beta.mult, null, 'sem custo lançado não há múltiplo — nem zero, nem infinito');
const alfa2 = porCasa.find(c => c.casa === 'Alfa');
eq(alfa2.semPreco, 0, 'toda conta da Alfa tem preço (JC||Alfa = 500)');
eq(alfa2.custo, 1500, 'custo da Alfa = 3 contas x R$ 500');
ok(Math.abs(alfa2.mult - (alfa2.pl / 1500)) < 1e-9, 'múltiplo da Alfa = P/L / custo');

console.log('— 7. Conta própria NÃO é contada como "sem preço"');
ok(beta.semPreco !== 2, 'própria e sem-preço não podem cair no mesmo balde');

console.log('— 8. Apostas e ROI por casa, e o ROI é sobre TURNOVER (não sobre custo)');
// Alfa no período de março: Longeva 1 aposta (200/20), Curta 1 (50/5), Media 2 (100/10).
eq(alfa2.bets, 4, 'apostas da Alfa contam só as do período');
eq(alfa2.turn, 350, 'turnover da Alfa no período');
eq(alfa2.pl, 35, 'P/L da Alfa no período');
ok(Math.abs(alfa2.roi - 10) < 1e-9, 'ROI da Alfa = P/L / TURNOVER (35/350 = 10%)');
// O ROI não pode ser calculado sobre o custo: ali daria 35/1500 = 2,33%, e é o Múltiplo
// que mede retorno sobre custo. Dois denominadores, dois nomes.
ok(Math.abs(alfa2.roi - (alfa2.pl / alfa2.custo * 100)) > 1, 'ROI não é P/L sobre CUSTO');

console.log('— 9. Casa sem turnover no período não divide por zero');
api.setFiltro({ df: '2026-12-01', dt: '2026-12-31' });
api.pop = 'ambas';
const dez = api.porCasa(api.base().contas);
dez.forEach(c => ok(Number.isFinite(c.roi), 'ROI de ' + c.casa + ' tem de ser finito'));
api.setFiltro({ df: '2026-03-01', dt: '2026-03-31' });

if (falhas) { console.error(falhas + ' falha(s)'); process.exit(1); }
console.log('ok: contas_vida');
