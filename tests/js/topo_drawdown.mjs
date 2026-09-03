// Prova por EXECUÇÃO do Topo Histórico e do Drawdown Atual (s313).
//
// O sintoma que abriu o caso (tester Gabriel, print no grupo): carteira R$ 1.605,30 no
// vermelho exibindo "Drawdown Atual R$ 0,00" e "Topo Histórico −R$ 1.605,30" — um topo
// NEGATIVO, que é impossível: a curva começa no zero, antes da primeira aposta, e o topo
// nunca esteve abaixo do início.
//
// A causa: `calcTopoDrawdown` partia de `peak=-Infinity` enquanto `calcDrawdownReal`
// (o Max Drawdown do card ao lado) partia de `peak=0`. As duas funções descrevem a MESMA
// curva. Com -Infinity o primeiro dia virava o topo fosse ele qual fosse, e numa série que
// só sobe depois do mergulho o topo passava a ser o ÚLTIMO ponto — então `dd = peak - acc`
// dava 0 por construção. Não dependia de "começar negativo": bastava o acumulado atual ser
// o máximo da série e ainda estar abaixo de zero.
//
// As funções são RECORTADAS do app.js de produção — nunca reescritas aqui: teste que
// reimplementa o código sob teste não detecta a mutação que o quebra (CLAUDE.md, "Teste
// verde não é teste que detecta").
//
// O que este teste NÃO cobre: o render (nenhum DOM é montado aqui — a cor do KPI, o
// `data-state` e o CSS da Escada de Tinta são conferidos no render headless), a agregação
// por dia vinda do feed real, e o Recovery Factor (que só divide por `calcMDDreais`).
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const CR = String.fromCharCode(13), LF = String.fromCharCode(10);
const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const lerJs = p => fs.readFileSync(p, 'utf8').split(CR + LF).join(LF);
// ALVO_APP existe para a prova por MUTAÇÃO: o pytest aponta para uma cópia estragada do
// app.js e confere que este arquivo fica vermelho.
const APP = lerJs(process.env.ALVO_APP || path.join(RAIZ, 'app/static/dash/assets/js/app.js'));

let falhas = 0;
const ok = (cond, msg) => { if (!cond) { console.error('FALHOU: ' + msg); falhas++; } };
const quase = (a, b, tol) => Math.abs(a - b) < (tol === undefined ? 0.005 : tol);

// Recorta uma função de topo de nível: o `}` de fechamento é o único na coluna 0.
const recorteFn = (src, nome) => {
  const m = src.match(new RegExp('^function ' + nome + '\\([^)]*\\)\\{[\\s\\S]*?^\\}', 'm'));
  if (!m) throw new Error('não achei a função ' + nome + ' no app.js');
  return m[0];
};

const FONTE = ['calcDrawdownReal', 'calcTopoDrawdown', 'topoSub'].map(n => recorteFn(APP, n)).join(LF);
// BASE_BANK vem do data.js em produção (const BASE_BANK=100000) — injetado como parâmetro
// para o recorte rodar isolado, com o MESMO valor.
const BASE_BANK = 100000;
const API = new Function('BASE_BANK',
  FONTE + LF + 'return {calcDrawdownReal:calcDrawdownReal, calcTopoDrawdown:calcTopoDrawdown, topoSub:topoSub};'
)(BASE_BANK);
const { calcDrawdownReal, calcTopoDrawdown, topoSub } = API;

const dia = (d, lucro) => ({ data: '2026-08-' + String(d).padStart(2, '0'), lucro: lucro });

// ── A. O caso do relato: mergulha, recupera em parte, segue no vermelho ──────
// Números do print: MDD −2.514,00 e P/L acumulado −1.605,30.
{
  const rows = [dia(30, -2514), dia(31, 500), { data: '2026-09-01', lucro: 408.70 }];
  const td = calcTopoDrawdown(rows), dr = calcDrawdownReal(rows);

  ok(td.topo === 0, 'topo tem de ser 0 (o início da série), veio ' + td.topo);
  ok(td.topoData === null, 'topoData tem de ser null quando o topo é o início, veio ' + td.topoData);
  ok(quase(td.atual, -1605.30), 'acumulado deveria ser −1605,30, veio ' + td.atual);
  ok(quase(td.ddAtual, 1605.30), 'DD ATUAL deveria ser 1605,30 (o bug do relato dava 0), veio ' + td.ddAtual);
  ok(td.ddAtual > 0, 'DD atual NÃO pode ser 0 com a banca abaixo do topo — é o bug da s313');
  ok(quase(dr.mddReais, 2514), 'Max Drawdown deveria ser 2514, veio ' + dr.mddReais);
  // A % do DD atual passa a ter a MESMA régua do mddPct: queda ÷ banca no topo.
  ok(quase(td.ddAtualPct * 100, 1605.30 / BASE_BANK * 100, 0.001),
    'ddAtualPct tem de ser dd/(BASE_BANK+peak), veio ' + td.ddAtualPct);
}

// ── B. O topo NUNCA fica abaixo do zero de partida ───────────────────────────
{
  const rows = [dia(1, -100), dia(2, -200), dia(3, -50)];   // só perde, nunca sobe
  const td = calcTopoDrawdown(rows);
  ok(td.topo === 0, 'série 100% negativa: topo tem de ser 0, veio ' + td.topo);
  ok(quase(td.ddAtual, 350), 'DD atual da série só-negativa é o acumulado inteiro, veio ' + td.ddAtual);
  ok(topoSub(td) === 'no início da série', 'subtítulo do topo=início errado: ' + topoSub(td));
}

// ── C. Carteira positiva não muda de comportamento (não-regressão) ───────────
{
  const rows = [dia(1, 3000), dia(2, 2000), dia(3, -2000)];  // topo 5000 no dia 2, cai p/ 3000
  const td = calcTopoDrawdown(rows), dr = calcDrawdownReal(rows);
  ok(td.topo === 5000, 'topo deveria ser 5000, veio ' + td.topo);
  ok(td.topoData === '2026-08-02', 'topoData deveria ser o dia 02, veio ' + td.topoData);
  ok(quase(td.ddAtual, 2000), 'DD atual deveria ser 2000, veio ' + td.ddAtual);
  ok(topoSub(td) === 'atingido em 02/08/2026', 'subtítulo com data errado: ' + topoSub(td));
  ok(quase(dr.mddReais, 2000), 'MDD deveria ser 2000, veio ' + dr.mddReais);
}

// ── D. Os dois cards têm de CONCORDAR quando o vale é o último dia ───────────
// É o teste que amarra as duas funções: mesma curva, mesmo episódio pico→vale, então o
// R$ e a % do "Drawdown Atual" batem com os do "Max Drawdown". Era exatamente isso que
// o peak divergente quebrava.
{
  const casos = [
    [dia(1, -800), dia(2, 300), dia(3, -900)],          // nunca positiva
    [dia(1, 1200), dia(2, -400), dia(3, -1500)],        // positiva e depois no vermelho
    [dia(1, 500), dia(2, 700), dia(3, -300)],           // sempre no azul
  ];
  for (let i = 0; i < casos.length; i++) {
    const td = calcTopoDrawdown(casos[i]), dr = calcDrawdownReal(casos[i]);
    ok(quase(td.ddAtual, dr.mddReais),
      'caso ' + i + ': vale no último dia — DD atual (' + td.ddAtual + ') tem de bater com o MDD (' + dr.mddReais + ')');
    ok(quase(td.ddAtualPct * 100, dr.mddPct, 0.001),
      'caso ' + i + ': a % dos dois cards divergiu — ' + (td.ddAtualPct * 100) + ' vs ' + dr.mddPct);
    ok(td.topo >= 0, 'caso ' + i + ': topo negativo é impossível, veio ' + td.topo);
  }
}

// ── E. Invariantes gerais, em curvas aleatórias ──────────────────────────────
// O DD atual é UM episódio; o Max Drawdown é o pior de todos. Um nunca passa o outro.
{
  let seed = 7;
  const rnd = () => { seed = (seed * 1103515245 + 12345) % 2147483648; return seed / 2147483648; };
  for (let t = 0; t < 200; t++) {
    const n = 2 + Math.floor(rnd() * 12), rows = [];
    for (let d = 1; d <= n; d++) rows.push(dia(d, Math.round((rnd() - 0.5) * 4000)));
    const td = calcTopoDrawdown(rows), dr = calcDrawdownReal(rows);
    if (td.topo < 0) { ok(false, 'curva ' + t + ': topo negativo (' + td.topo + ')'); break; }
    if (td.ddAtual < -0.005) { ok(false, 'curva ' + t + ': DD atual negativo (' + td.ddAtual + ')'); break; }
    if (td.ddAtual > dr.mddReais + 0.005) { ok(false, 'curva ' + t + ': DD atual (' + td.ddAtual + ') maior que o MDD (' + dr.mddReais + ')'); break; }
    if (td.atual < 0 && td.ddAtual <= 0) { ok(false, 'curva ' + t + ': acumulado no vermelho com DD atual zerado — o bug da s313'); break; }
  }
}

// ── F. Empate no topo: o marco é a PRIMEIRA vez que ele foi atingido ─────────
// "Topo Histórico · atingido em <data>" é um marco. Se a curva volta ao mesmo valor
// depois, o marco continua sendo o dia em que ele nasceu — daí o `>` estrito no laço.
{
  const td = calcTopoDrawdown([dia(1, 1000), dia(2, -400), dia(3, 400)]); // topo 1000 nos dias 1 e 3
  ok(td.topo === 1000, 'topo do empate deveria ser 1000, veio ' + td.topo);
  ok(td.topoData === '2026-08-01', 'empate no topo tem de manter a PRIMEIRA data, veio ' + td.topoData);
  // Mesmo raciocínio para o zero: curva que volta a zero não "atinge um topo" no dia 2 —
  // o topo continua sendo o início da série, e o subtítulo não pode inventar uma data.
  const tz = calcTopoDrawdown([dia(1, -100), dia(2, 100)]);
  ok(tz.topo === 0 && tz.topoData === null, 'voltar a zero não cria data de topo, veio ' + tz.topoData);
  ok(quase(tz.ddAtual, 0), 'quem volta ao topo tem DD atual 0, veio ' + tz.ddAtual);
}

if (falhas) { console.error(LF + falhas + ' verificação(ões) falharam.'); process.exit(1); }
console.log('topo_drawdown.mjs: OK');
