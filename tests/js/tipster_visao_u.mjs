// O switch R$⇄u da tela Tipsters vale para a TELA inteira (s374, sugestão do tester João).
//
// Até aqui o "u" alcançava o KPI do topo e a coluna P/L do Comparativo. Os CARDS ficavam
// em R$, porque eles só sabiam renderizar u pelo `MODO_PUBLICO`, que não existe no dashboard
// privado. O resultado era um card dizendo "− R$ 1.520,31" com o KPI logo acima dizendo
// "−28,38u": cada metade certa, a razão entre as duas impossível de ler.
//
// Executa as funções RECORTADAS do `app.js` e do `performance.js` de produção. Nunca copia
// o trecho: teste que reimplementa o código sob teste é o 1º modo de falso verde do
// CLAUDE.md, e aqui ele seria fácil de cair (a conversão é uma divisão).
//
// O que este arquivo NÃO cobre:
//   · o render de verdade: o `document` aqui é dublado, então nada é medido na tela; a
//     posição dos cards, o CSS e a Escada de Tinta seguem fora do alcance de um teste sem
//     navegador;
//   · o KPI "Turnover Total" e as colunas do Comparativo, que vivem dentro do
//     `renderTipsters` (função de ~90 linhas presa ao DOM e ao feed); o que se prova aqui é
//     a RÉGUA que os alimenta (`_tipsterUnidades`) e o card, que é o que o tester viu;
//   · o drill-down do tipster, que segue em R$ por decisão desta sessão;
//   · o fetch de `/tipsters/escadas` e a preferência gravada no localStorage.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const AQUI = dirname(fileURLToPath(import.meta.url));
const RAIZ = join(AQUI, '..', '..');
// ALVO_APP / ALVO_PERF existem para a prova por MUTAÇÃO: o pytest aponta para uma cópia
// estragada e exige que este arquivo fique VERMELHO.
const APP = readFileSync(process.env.ALVO_APP
  || join(RAIZ, 'app', 'static', 'dash', 'assets', 'js', 'app.js'), 'utf8');
const PERF = readFileSync(process.env.ALVO_PERF
  || join(RAIZ, 'app', 'static', 'dash', 'assets', 'js', 'charts', 'performance.js'), 'utf8');
const LF = '\n';

let falhas = 0;
const ok = (cond, msg) => { if (!cond) { console.error('  ✗ ' + msg); falhas++; } };
const perto = (a, b, tol = 1e-9) => Math.abs(a - b) <= tol;

// Recorta uma função de topo de nível. A ordem das duas tentativas é load-bearing: o
// padrão de UMA LINHA vem primeiro porque o multilinha (`[\s\S]*?^\}`) casaria até o
// fechamento da PRÓXIMA função, arrastando as vizinhas para dentro do recorte.
const recorteFn = (src, nome, arquivo) => {
  const m = src.match(new RegExp('^function ' + nome + '\\([^)]*\\)\\{.*\\}$', 'm'))
    || src.match(new RegExp('^function ' + nome + '\\([^)]*\\)\\{[\\s\\S]*?^\\}', 'm'));
  if (!m) throw new Error('não achei a função ' + nome + ' no ' + arquivo);
  return m[0];
};

const FONTE = [
  ...['fmt', 'fmtU', 'fmtRU', '_uVigente', '_tipsterUnidades', 'wrFrac']
    .map(n => recorteFn(APP, n, 'app.js')),
  ...['_tipSparkSVG', '_mkTipCard', '_renderTipCards']
    .map(n => recorteFn(PERF, n, 'performance.js')),
].join(LF);

// Dublês do que o card usa de fora e que não é objeto deste gate: escape de HTML, o
// tooltip da odd, o vazio da grade e o `document`. O `#tipsterKpiCards` guarda o HTML
// escrito para que as asserções o leiam.
const API = new Function(`
  const alvo = { innerHTML: '', onclick: null };
  const document = {
    getElementById: id => (id === 'tipsterKpiCards' ? alvo : null),
    querySelectorAll: () => [],
  };
  const window = {};
  const esc = s => String(s == null ? '' : s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;');
  const fmtPct = (v,d=2,signed=true) => (signed && v>=0 ? '+' : '') + Number(v).toFixed(d) + '%';
  const fmtOdd = v => Number(v||0).toFixed(2);
  const _mkOddTip = () => '';
  const mkEmpty = msg => '<div class="empty">' + msg + '</div>';
  let _tipsterEnts = null, _tipsterDays = {}, _tipsterAllDays = [];
  let _tipsterSort = { k: 'pl', dir: 1 };
  let _tipsterEmU = false, _tipsterU = null;
  ${FONTE}
  return {
    _tipsterUnidades, _mkTipCard, fmtRU, fmtU,
    cards(cfg) {
      _tipsterEnts = cfg.ents;
      _tipsterDays = cfg.dias || {};
      _tipsterAllDays = cfg.allDays || [];
      _tipsterSort = cfg.sort || { k: 'pl', dir: 1 };
      _tipsterEmU = !!cfg.emU;
      _tipsterU = cfg.u || null;
      alvo.innerHTML = '';
      _renderTipCards();
      return alvo.innerHTML;
    },
  };
`)();

const linha = (o) => Object.assign(
  { tipster: 'Ze', lucro: 0, stake: 100, odd: 2, resultado: 'W', data: '2026-09-10' }, o);

// ── 1. A unidade é a VIGENTE NA DATA da linha, não uma só para o período ─────
// Escada com dois degraus: a mesma aposta de R$ 100 vale 1u antes e 0,5u depois.
// Converter o total por uma unidade só misturaria eras e é o erro que esta prova pega.
{
  const escadas = { Ze: [
    { vigente_desde: '2026-01-01', valor: 100 },
    { vigente_desde: '2026-06-01', valor: 200 },
  ] };
  const u = API._tipsterUnidades([
    linha({ data: '2026-03-10', lucro: 100, stake: 100 }),   // 1u de lucro, 1u de stake
    linha({ data: '2026-09-10', lucro: 100, stake: 100 }),   // 0,5u de lucro, 0,5u de stake
  ], escadas).Ze;
  ok(perto(u.pl, 1.5), 'P/L em u deveria ser 1,5 (1u + 0,5u), veio ' + u.pl);
  ok(perto(u.s, 1.5), 'turnover em u deveria ser 1,5, veio ' + u.s);
  ok(u.t === 2, 'as duas encerradas deveriam contar no denominador, veio ' + u.t);
  ok(perto(u.dias['2026-03-10'], 1) && perto(u.dias['2026-09-10'], 0.5),
    'o P/L por dia (sparkline) tem de sair em u também');
  // Clamp à esquerda: aposta ANTERIOR ao 1º degrau usa o 1º degrau.
  const antes = API._tipsterUnidades([linha({ data: '2025-12-01', lucro: 100 })], escadas).Ze;
  ok(perto(antes.pl, 1), 'antes do 1º degrau a unidade é a do 1º degrau, veio ' + antes.pl);
}

// ── 2. Turnover em u exclui Void, como o calcTurnover ────────────────────────
// Void devolve a stake: ela não é risco, e a régua em u tem de ser a MESMA da régua em R$.
{
  const escadas = { Ze: [{ vigente_desde: '2026-01-01', valor: 50 }] };
  const u = API._tipsterUnidades([
    linha({ lucro: 50, stake: 50, resultado: 'W' }),
    linha({ lucro: 0, stake: 500, resultado: 'V' }),
  ], escadas).Ze;
  ok(perto(u.s, 1), 'o Void não pode entrar no turnover em u, veio ' + u.s);
  ok(u.t === 1, 'o Void não pode entrar no denominador da stake média, veio ' + u.t);
}

// ── 3. Sem escada: fallback = stake média. Sem escada E sem stake: FORA ──────
// "Zero é uma odd que não existe" (CLAUDE.md): linha que não dá para converter sai da
// soma em vez de entrar como 0. Ausência viaja como ausência.
{
  const semEscada = API._tipsterUnidades([
    linha({ lucro: 20, stake: 100 }),
    linha({ lucro: -10, stake: 300 }),
  ], {}).Ze;   // stake média = 200
  ok(perto(semEscada.pl, 20 / 200 + -10 / 200), 'sem escada o fallback é a stake média, veio ' + semEscada.pl);

  const nadaPraConverter = API._tipsterUnidades([
    linha({ lucro: 77, stake: 0 }),
  ], {}).Ze;
  ok(nadaPraConverter.pl === 0 && nadaPraConverter.t === 0,
    'linha sem unidade resolvível fica FORA das somas, não vira zero somado');
}

// ── 4. O card inteiro troca de moeda, não só o P/L ───────────────────────────
// Card meio em u e meio em R$ é a família do "meio atualizado": os dois números certos,
// a leitura errada.
{
  const emU = API._mkTipCard('Ze', -28.38, -21.54, 15.4, 45.5, 11, '<svg></svg>', 1.4, 2.2, true);
  ok(!emU.includes('R$'), 'com o switch em u nenhum R$ pode sobrar no card');
  ok((emU.match(/>u</g) || []).length === 3,
    'P/L, Turnover e Stake Média têm de sair em u (3 sufixos), vieram ' + (emU.match(/>u</g) || []).length);
  ok(emU.includes('−28,38'), 'o P/L em u mantém o minus U+2212 e as 2 casas');
  ok(emU.includes('1,40'), 'stake média em u abaixo de 100 sai com 2 casas, senão viraria "0u"');

  const emReais = API._mkTipCard('Ze', -1520.31, -47.4, 3209, 14.3, 41, '<svg></svg>', 92, 4.2, false);
  ok(emReais.includes('R$'), 'sem o switch o card segue em R$');
  ok(!/>u</.test(emReais), 'sem o switch nenhum "u" pode aparecer no card');
  ok(emReais.includes('3.209'), 'turnover em R$ segue inteiro com milhar pt-BR');
}

// ── 5. A ordenação segue o que está NA TELA ──────────────────────────────────
// Dois tipsters onde R$ e u discordam: em R$ o Zé ganha, em u o Bia ganha (a unidade dele
// é 10x maior). Ordenar pelo valor em R$ deixaria a lista fora de ordem à vista de quem lê.
{
  const ents = [
    ['Ze',  { l: 1000, s: 5000, n: 10, w: 5, t: 10, hw: 0, hl: 0, wt: 0, stk: 0 }],
    ['Bia', { l: 600,  s: 3000, n: 10, w: 5, t: 10, hw: 0, hl: 0, wt: 0, stk: 0 }],
  ];
  const u = { Ze: { pl: 10, s: 50, t: 10, dias: {} }, Bia: { pl: 60, s: 300, t: 10, dias: {} } };

  const html = API.cards({ ents, emU: true, u, sort: { k: 'pl', dir: 1 } });
  ok(html.indexOf('Bia') < html.indexOf('Ze'),
    'em u, quem tem mais UNIDADES vem primeiro, e a ordem tem de seguir o valor exibido');
  ok(html.includes('+60,00') && html.includes('+10,00'),
    'os cards têm de mostrar o P/L em u, não o de R$');
  ok(!html.includes('1.000'), 'o valor em R$ não pode sobrar no card quando o switch está em u');
  // Stake média em u = turnover em u ÷ encerradas (300/10 e 50/10), o MESMO denominador
  // do lado em R$, senão os dois lados respondem perguntas diferentes.
  ok(html.includes('30,00') && html.includes('5,00'),
    'a stake média do card tem de sair em u, pelo mesmo denominador do R$');
  ok(!html.includes('R$'), 'nenhum R$ pode sobrar na grade de cards em modo u');

  const porTurnover = API.cards({ ents, emU: true, u, sort: { k: 'to', dir: 1 } });
  ok(porTurnover.indexOf('Bia') < porTurnover.indexOf('Ze'),
    'ordenar por turnover em u também segue o valor exibido');

  const reais = API.cards({ ents, emU: false, u: null, sort: { k: 'pl', dir: 1 } });
  ok(reais.indexOf('Ze') < reais.indexOf('Bia'), 'em R$ a ordem é a de sempre');
  ok(reais.includes('R$'), 'em R$ o card segue com R$');
}

// ── 6. fmtRU: agregado em u, adaptativo (a régua que o modo público já usava) ─
{
  ok(API.fmtRU(12182).includes('12.182'), 'agregado grande em u sai inteiro, com milhar pt-BR');
  ok(!/,/.test(API.fmtRU(12182).replace(/<[^>]*>/g, '')), 'acima de 100 não leva decimal');
  ok(API.fmtRU(1.25).includes('1,25'), 'abaixo de 100 leva 2 casas, senão stake em u viraria "0u"');
  ok(API.fmtRU(0).includes('0,00'), 'zero em u é 0,00u, não "0u"');
  ok(!API.fmtRU(1234).includes('k') && !API.fmtRU(1234).includes('mil'),
    'nunca abreviar milhar (UI_REFERENCE §5.2)');
}

if (falhas) { console.error(LF + falhas + ' verificação(ões) falharam.'); process.exit(1); }
console.log('tipster_visao_u.mjs: OK');
