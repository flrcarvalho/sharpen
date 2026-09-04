// Prova por EXECUÇÃO dos filtros da Base Completa (s317).
//
// O pedido do tester era um filtro de resultado. A decisão que veio junto é a que este
// teste existe para travar: o DESFECHO CORTA A TABELA, NÃO A RÉGUA. Filtrar por W e ver
// Win Rate 100% seria um número certo pela conta e mentiroso pela leitura — então os KPIs
// leem `apostasKpiRows` (o recorte sem o corte por resultado) e a tabela lê
// `apostasFiltered`. Trocar um pelo outro não dá erro nenhum: só passa a mentir.
//
// Tudo aqui é RECORTADO dos arquivos de produção — `parseNum` do app.js, as constantes de
// coluna do shared.js e o bloco de repartição de dentro do próprio `renderApostas`. Teste
// que reimplementa o código sob teste não detecta a mutação que o quebra (s286).
//
// O que este teste NÃO cobre: o DOM (chips, chips de filtro ativo e a nota dos KPIs são
// pintados por innerHTML e aqui nada é renderizado), o multiselect de conta (o `msGet` é
// dublado — o que se exerce é o uso dele, não a store), o debounce dos campos de faixa, e
// o `localeCompare` sob outro ICU que não o do node local.
//
// Mutação inócua registrada: das duas opções do `localeCompare`, só `numeric:true` é
// distinguível aqui — sob o ICU do node, `sensitivity:'base'` não muda a vizinhança de
// "kto"/"KTO", que já saem juntos pela colação padrão. Ela fica no código porque a
// garantia é do padrão de colação, não deste ICU; o teste trava a metade que morde.
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const CR = String.fromCharCode(13), LF = String.fromCharCode(10);
const MENOS = String.fromCharCode(0x2212);
const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const lerJs = p => fs.readFileSync(p, 'utf8').split(CR + LF).join(LF);
const APP = lerJs(process.env.ALVO_APP || path.join(RAIZ, 'app/static/dash/assets/js/app.js'));
const SHARED = lerJs(process.env.ALVO_SHARED || path.join(RAIZ, 'app/static/dash/assets/js/charts/shared.js'));
const APOSTAS = lerJs(process.env.ALVO_APOSTAS || path.join(RAIZ, 'app/static/dash/assets/js/charts/apostas.js'));

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

// ── Sandbox: só código de produção, mais os dois stubs declarados acima ─────
const pedacos = [
  recorte(APP, 'function parseNum(raw){', LF + '}', 'parseNum'),
  linha(SHARED, 'const APOSTAS_COLS=', 'APOSTAS_COLS'),
  linha(SHARED, 'const APOSTAS_NUM=', 'APOSTAS_NUM'),
  linha(APOSTAS, 'let apostasFiltered=[]', 'estado do sort'),
  linha(APOSTAS, 'let apostasColFilters=', 'apostasColFilters'),
  linha(APOSTAS, 'let apostasTabela=[]', 'apostasTabela'),
  linha(APOSTAS, 'let apostasKpiRows=[]', 'apostasKpiRows'),
  linha(APOSTAS, 'const APOSTAS_RES_ORDEM=', 'APOSTAS_RES_ORDEM'),
  linha(APOSTAS, 'let apostasResSel=', 'apostasResSel'),
  linha(APOSTAS, 'let apostasFaixas=', 'apostasFaixas'),
  linha(APOSTAS, 'function _apFaixa(', '_apFaixa'),
  recorte(APOSTAS, 'function _apostasColMatch(r){', LF + '}', '_apostasColMatch'),
  linha(APOSTAS, 'function _apostasParcMatch(', '_apostasParcMatch'),
  recorte(APOSTAS, 'function _apostasFaixaMatch(r,aberta){', LF + '}', '_apostasFaixaMatch'),
  linha(APOSTAS, 'function _apostasResMatch(', '_apostasResMatch'),
  linha(APOSTAS, 'function _apostasRecorte(', '_apostasRecorte'),
  recorte(APOSTAS, 'function _apostasCmp(a,b){', LF + '}', '_apostasCmp'),
];
// A repartição KPI × tabela vive DENTRO do renderApostas: recortada daqui até a linha em
// que a tabela é montada. É este trecho — e não uma cópia dele — que o teste executa.
const REPARTE = recorte(
  APOSTAS,
  "  const baseRows=filtrarPagina('apostas');",
  'apostasTabela=apostasAbertasFiltered.concat(apostasFiltered);',
  'reparticao do renderApostas',
);

const fonte = pedacos.join(LF + LF) + LF
  + 'function reparte(){' + LF + REPARTE + LF + '}' + LF
  + 'return {' + [
    'reparte',
    'cmp:_apostasCmp',
    'estado:()=>({tabela:apostasTabela.length,kpi:apostasKpiRows.length,filtered:apostasFiltered,abertas:apostasAbertasFiltered})',
    'setFaixa:(k,v)=>{apostasFaixas[k]=v;}',
    'setRes:(a)=>{apostasResSel=new Set(a);}',
    'setTexto:(i,v)=>{apostasColFilters[i]=v;}',
    'setSort:(c,asc)=>{apostasSortCol=c;apostasSortAsc=asc;}',
    'zerar:()=>{apostasFaixas={stakeMin:"",stakeMax:"",oddMin:"",oddMax:"",plMin:"",plMax:""};apostasResSel=new Set();apostasColFilters={};apostasSortCol=0;apostasSortAsc=false;}',
  ].join(',') + '};';

// ── Base sintética: cada linha existe para fazer UMA regra morder ───────────
const L = (id, resultado, stake, odd, lucro, extra) => Object.assign(
  {
    id, resultado, stake, odd, lucro,
    data: '2026-09-0' + id, esporte: 'Futebol', tipster: 'T',
    casa: 'KTO', parceiro: 'conta1', aposta: 'ML', descricao: 'jogo ' + id,
  }, extra || {});
const ENCERRADAS = [
  L(1, 'W', 100, 2.00, 100),
  L(2, 'HW', 100, 3.00, 50),
  L(3, 'L', 1000.5, 4.00, -1000.5),   // stake EXATAMENTE no limite (prova o >=, não o >)
  L(4, 'HL', 250, 1.50, -125),
  L(5, 'V', 300, 5.00, 0, { parceiro: 'conta2' }),
  L(6, 'L', 100, 9.99, -100, { parceiro: 'conta2' }),  // P/L EXATAMENTE no limite
];
// Abertas com lucro 0: é o valor que o feed traz, e é justamente o que faria uma faixa de
// P/L cruzando o zero engolir todas elas se a regra do `aberta` sumisse.
const ABERTAS = [L(7, 'ABERTA', 500, 2.50, 0), L(8, 'ABERTA', 20, 1.20, 0)];

// A store do multiselect é o único dublê, e é mutável de propósito: com um Set fixo e
// vazio o `_apostasParcMatch` devolveria `true` sempre, e removê-lo do recorte não
// quebraria teste nenhum — verde que não detecta.
let CONTA_SEL = new Set();
const F = new Function('msGet', 'filtrarPagina', 'filtrarAbertas', fonte)(
  () => CONTA_SEL, () => ENCERRADAS.slice(), () => ABERTAS.slice());

// ── 1. Repartição: o desfecho corta a TABELA, nunca a régua dos KPIs ────────
F.zerar(); F.reparte();
ok(F.estado().kpi === 6, 'sem filtro os KPIs veem as 6 encerradas (veio ' + F.estado().kpi + ')');
ok(F.estado().tabela === 8, 'sem filtro a tabela tem 6 encerradas + 2 abertas (veio ' + F.estado().tabela + ')');

F.setRes(['L']); F.reparte();
ok(F.estado().kpi === 6, 'O FILTRO DE RESULTADO NAO PODE MEXER NOS KPIs — vieram ' + F.estado().kpi + ' de 6');
ok(F.estado().tabela === 2, 'filtrando L a tabela mostra so as 2 perdidas (veio ' + F.estado().tabela + ')');

F.setRes(['ABERTA']); F.reparte();
ok(F.estado().kpi === 6, 'filtrar Aberta tambem nao mexe nos KPIs (veio ' + F.estado().kpi + ')');
ok(F.estado().tabela === 2 && F.estado().abertas.length === 2, 'filtrando Aberta sobram so as 2 abertas');

F.setRes(['W', 'HW']); F.reparte();
ok(F.estado().tabela === 2, 'multi-selecao SOMA os desfechos (W + HW = 2, veio ' + F.estado().tabela + ')');

// ── 2. Faixas: recorte de verdade — e este SIM entra nos KPIs ───────────────
F.zerar(); F.setFaixa('stakeMin', '1.000,50'); F.reparte();
ok(F.estado().kpi === 1, 'stake >= "1.000,50" em pt-BR (ponto de milhar, virgula decimal) pega so a linha 3 — veio ' + F.estado().kpi);
ok(F.estado().abertas.length === 0, 'as duas abertas (R$ 500 e R$ 20) saem da faixa de stake');

F.zerar(); F.setFaixa('stakeMax', '99'); F.reparte();
ok(F.estado().kpi === 0, 'stake <= 99 nao pega nenhuma encerrada (a menor e 100)');
ok(F.estado().abertas.length === 1, 'mas pega a aberta de R$ 20 — faixa de stake VALE para aberta');

F.zerar(); F.setFaixa('stakeMin', '1000.5'); F.reparte();
ok(F.estado().kpi === 1, 'limite no valor EXATO entra: e >=, nao >');

F.zerar(); F.setFaixa('plMax', MENOS + '100'); F.reparte();
ok(F.estado().kpi === 3, 'P/L <= -100 com minus U+2212 pega as linhas 3, 4 e 6 — veio ' + F.estado().kpi);
ok(F.estado().abertas.length === 0, 'APOSTA ABERTA NAO TEM P/L: nenhuma pode entrar numa faixa de P/L');

F.zerar(); F.setFaixa('plMin', MENOS + '200'); F.setFaixa('plMax', '200'); F.reparte();
ok(F.estado().abertas.length === 0, 'faixa de P/L que CRUZA o zero segue sem aberta (o zero delas e ausencia, nao valor)');
ok(F.estado().kpi === 5, 'a faixa cruzando o zero pega tudo entre -200 e +200: W, HW, V, HL(-125) e L(-100) — veio ' + F.estado().kpi);

F.zerar(); F.setFaixa('oddMin', '2'); F.setFaixa('oddMax', '4'); F.reparte();
ok(F.estado().kpi === 3, 'odd entre 2 e 4 pega W(2,00), HW(3,00) e L(4,00) — bordas incluidas, veio ' + F.estado().kpi);

// ── 3. Busca textual, faixa e desfecho se ACUMULAM ─────────────────────────
// Sozinha primeiro: no caso combinado a faixa dava o mesmo número, e a busca podia sumir
// sem que nada mudasse — dado sintético que não exerce a regra não prova a regra.
F.zerar(); F.setTexto(6, 'jogo 1'); F.reparte();
ok(F.estado().kpi === 1, 'busca na descricao recorta sozinha (veio ' + F.estado().kpi + ')');
ok(F.estado().abertas.length === 0, 'a busca vale tambem para as abertas');

F.zerar(); F.setTexto(6, 'jogo 3'); F.setFaixa('stakeMin', '500'); F.reparte();
ok(F.estado().kpi === 1, 'texto + faixa recortam juntos (veio ' + F.estado().kpi + ')');
F.setTexto(6, 'jogo 1'); F.reparte();
ok(F.estado().kpi === 0, 'texto e faixa sao E logico: "jogo 1" tem stake 100 e cai fora do >= 500');
F.setTexto(6, 'jogo 3'); F.setRes(['W']); F.reparte();
ok(F.estado().kpi === 1 && F.estado().tabela === 0, 'com o desfecho por cima: tabela vazia, KPI intacto (a linha 3 e L, nao W)');

// ── 3b. Conta (multiselect próprio da tela) ────────────────────────────────
F.zerar(); CONTA_SEL = new Set(['conta2']); F.reparte();
ok(F.estado().kpi === 2, 'conta2 tem 2 encerradas (veio ' + F.estado().kpi + ')');
ok(F.estado().abertas.length === 0, 'as abertas sao da conta1 e saem do recorte');
CONTA_SEL = new Set(['conta1', 'conta2']); F.reparte();
ok(F.estado().kpi === 6, 'multi-selecao de conta soma as duas (veio ' + F.estado().kpi + ')');
CONTA_SEL = new Set();

// ── 4. Ordem do resultado é SEMÂNTICA, nunca alfabética ────────────────────
// A alfabética daria HL, HW, L, L, V, W — sem significado para quem confere a base.
F.zerar(); F.setSort(9, true);
const semantica = ENCERRADAS.slice().sort((a, b) => F.cmp(a, b)).map(r => r.resultado).join(',');
ok(semantica === 'W,HW,V,HL,L,L', 'ordem semantica ganhou->perdeu; veio: ' + semantica);
ok(semantica !== 'HL,HW,L,L,V,W', 'a ordem NAO pode ser a alfabetica');

// Texto: ordem natural de dígito — "conta2" antes de "conta10". É o que as opções do
// localeCompare compram; sem elas a ordem é a de caractere e conta10 sobe na frente.
F.setSort(4, true);
const CONTAS = [
  L(1, 'W', 1, 1, 0, { parceiro: 'conta10' }),
  L(2, 'W', 1, 1, 0, { parceiro: 'conta2' }),
  L(3, 'W', 1, 1, 0, { parceiro: 'Conta1' }),
];
const op = CONTAS.slice().sort((a, b) => F.cmp(a, b)).map(r => r.parceiro).join(',');
ok(op === 'Conta1,conta2,conta10', 'ordem natural de digito e insensivel a caixa (veio ' + op + ')');

// Numérica: stake ordena por número, não por texto ("1000.5" < "250" como string).
F.setSort(7, true);
const on = ENCERRADAS.slice().sort((a, b) => F.cmp(a, b)).map(r => r.stake).join(',');
ok(on === '100,100,100,250,300,1000.5', 'stake ordena numerico, nao como texto (veio ' + on + ')');

// P/L é a coluna que separa o ramo numérico do textual de verdade: com NEGATIVO, o
// localeCompare de dígito natural põe -125 antes de -1000,5 (lê os algarismos depois do
// sinal), e o P/L da tabela sairia trocado sem erro nenhum — o bug da s300 de novo.
F.setSort(10, true);
const opl = ENCERRADAS.slice().sort((a, b) => F.cmp(a, b)).map(r => r.lucro).join(',');
ok(opl === '-1000.5,-125,-100,0,50,100', 'P/L negativo ordena por VALOR, nao por algarismo (veio ' + opl + ')');

if (falhas) { console.error(LF + falhas + ' falha(s).'); process.exit(1); }
console.log('filtros_base_completa: OK');
