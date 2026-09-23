// Prova por EXECUÇÃO de que o escopo de unidade morre junto com o modal do tipster (s383).
//
// Relato do Ewanderson1 (1u = R$ 50), sobre o calendário da aba Resultados: "Era p ser,
// mas eu n fiz 2.041u no dia 15". O número era R$ 2.041 com um "u" colado. O
// `renderTipsterDrill` liga `_uEscopo` quando o switch da tela Tipsters está em u, e o
// comentário dizia que o `closeTipsterDrill` o desligava. A linha que desligava tinha
// ido parar no `closeCasaDrill`, que nunca liga nada. Fechado o modal, o calendário e o
// Dia da Semana do dashboard inteiro seguiam escrevendo "u" sobre valor em R$.
//
// Duas travas, cada uma provada sozinha:
//   1. o `closeTipsterDrill` desliga o escopo;
//   2. o `renderPage` desliga o escopo quando o modal NÃO está aberto (a rede para
//      qualquer saída do modal que não passe pelo close), e o PRESERVA com o modal
//      aberto, senão um repintar da página por baixo tiraria o modal do modo u.
//
// Tudo aqui é RECORTADO dos arquivos de produção (s286: teste que reimplementa o código
// sob teste não detecta a mutação que o quebra).
//
// O que este teste NÃO cobre: o `renderTipsterDrill` ligando o escopo (função de
// centenas de linhas presa ao DOM; aqui o "aberto em u" é o estado de partida, não uma
// consequência provada), e o render real no navegador.
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const CR = String.fromCharCode(13), LF = String.fromCharCode(10);
const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const lerJs = p => fs.readFileSync(p, 'utf8').split(CR + LF).join(LF);
const APP = lerJs(process.env.ALVO_APP || path.join(RAIZ, 'app/static/dash/assets/js/app.js'));
const PERF = lerJs(process.env.ALVO_PERF || path.join(RAIZ, 'app/static/dash/assets/js/charts/performance.js'));
const SHARED = lerJs(path.join(RAIZ, 'app/static/dash/assets/js/charts/shared.js'));

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

// A rede do renderPage é recortada SOZINHA: o resto da função puxa o dashboard inteiro.
// O recorte vai do `const _tdo=` até o fim da linha seguinte, e por isso uma mutação que
// apague a linha do `_uEscopo=false` ainda deixa o recorte de pé (ele pega a linha de
// baixo) e o teste falha pelo COMPORTAMENTO, não por não achar o trecho.
const REDE_INI = "  const _tdo=document.getElementById('tipsterDrillOverlay');";
const iRede = APP.indexOf(REDE_INI);
if (iRede < 0) throw new Error('nao achei a rede de _uEscopo no renderPage');
const fimL1 = APP.indexOf(LF, iRede), fimL2 = APP.indexOf(LF, fimL1 + 1);
const REDE = APP.slice(iRede, fimL2);

const FONTE = [
  linha(APP, 'let _uEscopo=false;', '_uEscopo'),
  linha(APP, 'function emUnidades()', 'emUnidades'),
  linha(APP, 'function fmt(v,d=2)', 'fmt'),
  linha(APP, 'function fmtPL(v)', 'fmtPL'),
  linha(APP, 'function fmtOdd(v)', 'fmtOdd'),
  linha(APP, 'function calcTurnover(rows)', 'calcTurnover'),
  linha(APP, 'function wrFrac(', 'wrFrac'),
  linha(APP, 'function wrPctRows(rows)', 'wrPctRows'),
  linha(APP, 'function calcWR(rows)', 'calcWR'),
  linha(APP, 'function calcAvgOdd(rows)', 'calcAvgOdd'),
  recorte(SHARED, 'function mkEmpty(msg){', LF + '}', 'mkEmpty'),
  recorte(SHARED, 'function mkCalendarHeatmap(', LF + '}', 'mkCalendarHeatmap'),
  recorte(PERF, 'function closeTipsterDrill(e){', LF + '}', 'closeTipsterDrill'),
  'function _redeDoRenderPage(){' + LF + REDE + LF + '}',
].join(LF);

const preludio = `
  const MESES=['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro'];
  const PUBLICO = null;
  const window = { MODO_PUBLICO: null };
  const _els = {};
  const document = {
    getElementById: id => _els[id] || null,
    body: { style: {} },
    removeEventListener: () => {},
  };
  let _drillEscHandler = null;
`;
const M = new Function(preludio + FONTE + `
  ;return {
    ligar: () => { _uEscopo = true; },
    emUnidades,
    closeTipsterDrill,
    redeDoRenderPage: _redeDoRenderPage,
    mkCalendarHeatmap,
    overlay: display => { if (display === null) delete _els.tipsterDrillOverlay; else _els.tipsterDrillOverlay = { style: { display } }; },
  };
`)();

// O dia 15 do Ewanderson, em R$ (a base dele é em reais; 1u = R$ 50).
const BASE = [
  { data: '2026-09-15', resultado: 'W', stake: 50, odd: 41.82, tipster: 'Padovan', lucro: 2041 },
];
const diz_u = html => /<span class="cur">u<\/span>/.test(html);
const diz_rs = html => html.includes('R$');

// 1) Aberto em u, fechado pelo ✕/Esc: o escopo morre e o calendário volta a R$.
{
  M.overlay('flex'); M.ligar();
  ok(M.emUnidades() === true, 'estado de partida: o modal em u deveria estar em unidades');
  M.overlay('none'); M.closeTipsterDrill();
  ok(M.emUnidades() === false, 'fechar o modal do tipster não desligou o escopo de unidade');
  const html = M.mkCalendarHeatmap('2026-09', BASE, { showNav: true });
  ok(!diz_u(html), 'depois de fechar o modal, o calendário ainda escreve "u" sobre valor em R$');
  ok(diz_rs(html), 'depois de fechar o modal, o calendário não voltou a R$');
}

// 2) A rede: modal fechado por um caminho que NÃO passa pelo close (o escopo ficou
//    ligado); o próximo renderPage o desliga.
{
  M.overlay('none'); M.ligar();
  M.redeDoRenderPage();
  ok(M.emUnidades() === false, 'renderPage com o modal fechado deixou o escopo de unidade ligado');
}

// 3) Página sem o overlay no DOM (modo que não monta o modal): também é R$.
{
  M.overlay(null); M.ligar();
  M.redeDoRenderPage();
  ok(M.emUnidades() === false, 'renderPage sem overlay no DOM deixou o escopo de unidade ligado');
}

// 4) O outro lado da rede: com o modal ABERTO, repintar a página por baixo não pode tirar
//    o modal do modo u (o calendário dele navega e repinta depois do render).
{
  M.overlay('flex'); M.ligar();
  M.redeDoRenderPage();
  ok(M.emUnidades() === true, 'renderPage com o modal aberto desligou o escopo e tirou o modal de u');
}

if (falhas) { console.error(falhas + ' falha(s)'); process.exit(1); }
console.log('uescopo_fecha_com_modal: ok');
