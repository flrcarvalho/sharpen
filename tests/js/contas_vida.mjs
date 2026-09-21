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
  ...['_cnMediana', '_cnMedia', '_cnPl', '_cnFraseLongevas', '_cnBaseTxt', '_cnTemPreco', '_cnBase',
      '_cnPorCasa', '_cnHistograma', '_cnGeral', '_cnOrdenarDrill', '_cnUltimas',
      '_cnAgregadoRecente']
      .map(n => recorteFn(CONTAS, n, 'contas.js')),
  // CN_FAIXAS vive fora de funcao: recortada por nome, ATE O `];` — ela nasceu numa
  // linha so e virou multilinha quando os rotulos foram escritos por extenso, e um
  // recorte ancorado em `.*$` pegaria a primeira linha e deixaria o array aberto
  // (`SyntaxError: Unexpected token ';'`, sem dizer de onde). Mesma familia do recorte
  // de funcao de UMA linha que este arquivo ja trata no `recorteFn`.
  (CONTAS.match(/^const CN_FAIXAS=[\s\S]*?^\];$/m) || [''])[0],
  'globalThis.__api={ ordenarDrill:_cnOrdenarDrill, ultimas:_cnUltimas,',
  '  agregadoRecente:_cnAgregadoRecente, set pop(v){_cnPop=v;}, get pop(){return _cnPop;},',
  '  setDados(d,a){DADOS=d;DADOS_ABERTAS=a||[];},',
  '  setCadastro(c){_contasVida=c;_contaVida=null;},',
  '  setCusto(c){custoData=c;},',
  '  setFiltro(f){FS={contas:Object.assign({df:"",dt:"",qd:0,qt:""},f||{})};},',
  '  setCasas(s){MSS["ca_contas"]=new Set(s||[]);},',
  '  base(){return _cnBase();}, porCasa(c){return _cnPorCasa(c);},',
  '  geral(c,l){return _cnGeral(c,l);}, hist(d){return _cnHistograma(d);},',
  '  mediana(x){return _cnMediana(x);}, media(x){return _cnMedia(x);},',
  '  fraseLongevas(n,m){return _cnFraseLongevas(n,m);},',
  '  baseTxt(n){return _cnBaseTxt(n);} };',
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

console.log('— 10. ROI LÍQUIDO sai do denominador ELEGÍVEL, e não do turnover inteiro');
api.pop = 'ambas';
api.setFiltro({ df: '2026-03-01', dt: '2026-03-31' });
const pc = api.porCasa(api.base().contas);
const alfaL = pc.find(c => c.casa === 'Alfa');
// Alfa: 3 contas com preco (500 cada = 1500), turnover 350, P/L 35.
ok(Math.abs(alfaL.roiLiq - ((35 - 1500) / 350 * 100)) < 1e-9,
   'ROI líquido da Alfa = (P/L − custo) ÷ turnover elegível');
const betaL = pc.find(c => c.casa === 'Beta');
// Beta: Propria (300/90, elegivel) + SemPreco (300/60, NAO elegivel). Sem custo lancado,
// o liquido e o P/L da propria e o denominador e SO o turnover dela.
eq(betaL.turnEleg, 300, 'turnover elegível da Beta exclui a conta sem preço');
eq(betaL.plEleg, 90, 'P/L elegível da Beta exclui a conta sem preço');
ok(Math.abs(betaL.roiLiq - 30) < 1e-9, 'ROI líquido da Beta = 90 ÷ 300');
ok(betaL.turnEleg !== betaL.turn, 'o caso precisa ter conta NÃO elegível, senão não exerce a regra');

console.log('— 11. Custo por dia de vida usa a SOMA das durações, não a mediana');
// Alfa: Longeva 157d + Media 31d + Curta 6d = 194 dias, custo 1500.
eq(alfaL.somaDur, 194, 'soma das durações da Alfa');
ok(Math.abs(alfaL.custoDia - (1500 / 194)) < 1e-9, 'custo/dia = custo ÷ SOMA das durações');
ok(Math.abs(alfaL.custoDia - (1500 / alfaL.durMed)) > 1, 'custo/dia NÃO pode usar a mediana');
eq(betaL.custoDia, null, 'casa sem custo lançado não tem custo por dia — nem zero');

console.log('— 12. Histograma: 5 faixas, e a soma delas é o total');
const h = api.hist([1, 3, 7, 8, 14, 20, 45, 90, 200]);
eq(h.length, 5, 'são 5 faixas');
eq(h.reduce((a, x) => a + x.n, 0), 9, 'a soma das faixas é o total de contas');
eq(h[0].n, 3, 'faixa 0-7 d pega 1, 3 e 7 (limites INCLUSIVOS nas duas pontas)');
eq(h[1].n, 2, 'faixa 8-14 d pega 8 e 14');
eq(h[4].n, 2, 'faixa 60 d + pega 90 e 200');
eq(h[0].larg, 100, 'a maior faixa vale 100% da largura');
// A faixa de ALERTA e marcada por POSICAO, nunca comparando o rotulo: texto e copy e
// muda (os rotulos viraram "0 a 7 dias" na s376), indice e estrutura. Um
// `l.rot === '0-7 d'` sobrevive ao rename em silencio, deixando a faixa sem o ambar.
eq(h[0].primeira, true, 'a 1a faixa e a de alerta');
eq(h.filter(x => x.primeira).length, 1, 'so UMA faixa pode ser a de alerta');
ok(h.slice(1).every(x => !x.primeira), 'nenhuma outra faixa se marca como alerta');
eq(api.hist([]).reduce((a, x) => a + x.n, 0), 0, 'histograma de lista vazia não quebra');

console.log('— 13. O agregado dos painéis sai das MESMAS contas que as fichas');
const B13 = api.base();
const g = api.geral(B13.contas, api.porCasa(B13.contas));
eq(g.n, B13.contas.length, 'a contagem do painel é a mesma da lista');
eq(g.nProprias + g.nComPreco + g.nSemPreco, g.n, 'os três estados de custo particionam a base');
eq(g.plEleg, B13.contas.filter(c => c.propria || c.custo > 0).reduce((a, c) => a + c.pl, 0),
   'P/L elegível exclui a conta sem preço');

console.log('— 14. Concordancia: a frase do rodape fecha no SINGULAR e no PLURAL');
// O erro que originou o caso saiu na tela do Feca: "25 contas PASSOU de 60 dias e puxam
// o numero para cima" — verbo pluralizado ao lado de outro fixo, na MESMA frase.
// Sem `\b` nos padrões de propósito: este arquivo já foi escrito por heredoc uma vez e
// os escapes viraram BACKSPACE (0x08), com o teste falhando enquanto o texto na tela
// estava certo. `includes` diz o mesmo e não tem escape para perder.
const f1 = api.fraseLongevas(1, 30);
const fN = api.fraseLongevas(25, 30);
ok(f1.includes('1 conta passou'), 'singular: "1 conta passou", veio:' + f1);
ok(f1.includes(' puxa ') && !f1.includes('puxam'), 'singular: " puxa ", veio:' + f1);
ok(fN.includes('25 contas passaram'), 'plural: "25 contas passaram", veio:' + fN);
ok(fN.includes('puxam'), 'plural: "puxam", veio:' + fN);
// As TRES palavras concordam entre si: nenhuma pode ficar para tras.
ok(!f1.includes('contas') && !f1.includes('passaram'), 'no singular nada vai para o plural');
ok(!fN.includes('conta passou') && !fN.includes(' puxa '), 'no plural nada fica no singular');
eq(api.fraseLongevas(0, 30), '', 'sem conta longeva, a frase nao aparece');
// O contexto do painel e a BASE DE CALCULO: substantivo E adjetivo concordam. Escrever
// "1 conta inativas" foi o primeiro erro da correcao do erro anterior.
api.pop = 'inativas';
eq(api.baseTxt(1), '1 conta inativa', 'singular: substantivo e adjetivo no singular');
eq(api.baseTxt(184), '184 contas inativas', 'plural: os dois no plural');
api.pop = 'ativas';
eq(api.baseTxt(1), '1 conta ativa', 'singular em ativas');
api.pop = 'ambas';
eq(api.baseTxt(1), '1 conta', 'em ambas, sem adjetivo');
eq(api.baseTxt(184), '184 contas', 'em ambas, plural sem adjetivo');

// ── 15. Ordem de entrada do drill: ativas em cima, inativas da ultima limitada ──────
// Pedido do Feca (21/09): *"como default: ordenar primeiro as ativas depois inativas, e
// ordenar da ultima inativada (ultima q foi limitada pra primeira)"*.
//
// O dado EXERCE a regra, que e o segundo modo de falso verde que o CLAUDE.md lista:
//  · o array de entrada chega na ordem ERRADA de proposito (inativa velha primeiro,
//    ativa por ultimo), senao o sort estavel do V8 "acertaria" sem criterio nenhum;
//  · as tres inativas empatam no valor de estado (todas valem 0), que e o unico jeito
//    de o desempate por recencia decidir alguma coisa;
//  · duas ativas com o MESMO `fim` (hoje) forcam o segundo desempate, o `ini`.
console.log('— 15. Ordem de entrada do drill: ativa em cima, depois a ultima limitada');
{
  const c = (conta, ativa, ini, fim) => ({ conta, ativa, ini, fim, forn: 'F', dur: 1,
    dias: 1, bets: 1, turn: 100, pl: 0, custo: 100, propria: false, casa: 'X' });
  const entrada = [
    c('inativa_velha',  false, '2026-01-01', '2026-02-01'),
    c('inativa_media',  false, '2026-03-01', '2026-05-10'),
    c('ativa_antiga',   true,  '2026-04-01', '2026-09-21'),
    c('inativa_recente',false, '2026-06-01', '2026-08-20'),
    c('ativa_nova',     true,  '2026-07-15', '2026-09-21'),
  ];
  const nomes = api.ordenarDrill(entrada, 'estado', -1).map(x => x.conta);
  eq(nomes.slice(0, 2).every(n => n.startsWith('ativa_')), true,
     'as duas ativas tem de vir primeiro: ' + nomes.join(' > '));
  eq(nomes[0], 'ativa_nova',
     'entre ativas (mesmo fim) desempata pelo `ini`, a ultima comprada em cima');
  eq(nomes.slice(2).join(','), 'inativa_recente,inativa_media,inativa_velha',
     'as inativas saem da ULTIMA limitada para a primeira');
  // A ordenacao manual por outra coluna nao pode herdar o desempate de recencia. Os dois
  // itens tem o MESMO turnover de proposito: com valores diferentes o desempate nunca
  // seria chamado e o caso passaria verde com o vazamento no lugar (medido -- esta era
  // a versao que deixava a mutacao "o desempate vaza para TODA coluna" escapar).
  // Entrada na ordem antiga->recente: sem vazamento o sort estavel a preserva; com
  // vazamento a recente sobe.
  const empate = [c('antiga', false, '2026-01-01', '2026-02-01'),
                  c('recente', false, '2026-06-01', '2026-08-20')];
  const porTurn = api.ordenarDrill(empate, 'turn', -1).map(x => x.conta);
  eq(porTurn.join(','), 'antiga,recente',
     'empate em Turnover NAO pode cair no desempate de recencia, que e so do Estado');
  const porTurnDif = api.ordenarDrill(
    [{ ...c('a', false, '2026-01-01', '2026-02-01'), turn: 900 },
     { ...c('b', true, '2026-01-01', '2026-09-21'), turn: 100 }], 'turn', -1).map(x => x.conta);
  eq(porTurnDif.join(','), 'a,b', 'clicar em Turnover volta a ordenar por turnover');
}

// ── 16. O 4o painel: quais contas sao "as ultimas", e o que entra na mediana ────────
// Pedido do Feca (21/09): *"o historico nao representa fielmente o momento"*. O painel
// so vale se os dois lados forem comparaveis, e e ai que ele quebra em silencio.
console.log('— 16. Ultimas contas: eixo pela 1a aposta, e a duracao CENSURADA fora da mediana');
{
  const c = (conta, ativa, pa, ini, dur, extra) => ({ conta, ativa, pa, ini, dur,
    forn: 'F', casa: 'X', dias: 1, bets: 1, turn: 1000, pl: 100, custo: 100,
    propria: false, fim: '2026-09-01', ...(extra || {}) });

  // (a) O eixo e `pa` (1a aposta), NAO `ini`. A conta abaixo tem o `ini` mais ANTIGO de
  //     todos (adquirida_em de backfill) e a aposta mais RECENTE: se o codigo ordenar
  //     por `ini` ela cai para o fim e o caso falha.
  const porPa = api.ultimas([
    c('meio',    false, '2026-05-01', '2026-05-01', 10),
    c('antiga',  false, '2026-01-01', '2026-01-01', 10),
    c('nova',    false, '2026-08-01', '2020-01-01', 10),
  ], 10).map(x => x.conta);
  eq(porPa.join(','), 'nova,meio,antiga',
     'ordena pela 1a APOSTA; a conta com `ini` de 2020 e aposta de agosto tem de vir 1a');

  // (b) Sem `pa` cai no `ini`; sem nenhum dos dois fica FORA (posicao que o dado nao tem).
  const semData = api.ultimas([
    c('so_ini', false, '', '2026-07-01', 10),
    c('sem_nada', false, '', '', 10),
    c('com_pa', false, '2026-06-01', '2026-06-01', 10),
  ], 10).map(x => x.conta);
  eq(semData.join(','), 'so_ini,com_pa', 'conta sem data nenhuma NAO entra na lista');

  // (c) Corta em N.
  eq(api.ultimas([1, 2, 3, 4, 5].map((i) =>
      c('c' + i, false, '2026-0' + i + '-01', '2026-0' + i + '-01', 10)), 3).length, 3,
     'corta nas N mais recentes');

  // (d) ⚠️ O caso que mais importa: a duracao de conta ATIVA e censurada (ainda vai
  //     crescer) e nao pode entrar na mediana. Aqui a ativa tem dur=1: se ela entrar, a
  //     mediana desaba de 20 para 1 e o painel diz que a casa piorou quando o que houve
  //     foi a conta ser nova. As duas inativas dao mediana 20.
  const comAtiva = api.agregadoRecente([
    c('viva',  true,  '2026-09-01', '2026-09-01', 1),
    c('morta1', false, '2026-08-01', '2026-08-01', 20),
    c('morta2', false, '2026-07-01', '2026-07-01', 20),
  ], 300);
  eq(comAtiva.durMed, 20, 'a duracao da conta ATIVA fica fora da mediana');
  eq(comAtiva.nAtivas, 1, 'e o painel conta quantas ficaram de fora');
  eq(comAtiva.n, 3, 'mas as ativas CONTAM no total, no ROI e no multiplo');

  // (e) Todas ativas: nao ha mediana. `null`, nunca 0 — zero e uma duracao que existe.
  const sóAtivas = api.agregadoRecente([
    c('a', true, '2026-09-01', '2026-09-01', 5),
    c('b', true, '2026-08-01', '2026-08-01', 7),
  ], 200);
  eq(sóAtivas.durMed, null, 'sem conta encerrada a mediana e null, nunca 0');

  // (f) O custo vem de FORA (a regua unica `_custoNaJanela`), e o multiplo o usa.
  //     pl = 100+100 = 200 elegiveis, custo 50 -> 4x.
  const m = api.agregadoRecente([
    c('a', false, '2026-09-01', '2026-09-01', 5),
    c('b', false, '2026-08-01', '2026-08-01', 7),
  ], 50);
  eq(m.mult, 4, 'o multiplo usa o custo que o chamador passou, nao uma soma propria');
  eq(Math.round(m.roiLiq * 100) / 100, 7.5, 'ROI liquido = (pl - custo) / turnover');
}

console.log(falhas ? `\nFALHAS: ${falhas}` : '\nok: contas_vida');
process.exit(falhas ? 1 : 0);
