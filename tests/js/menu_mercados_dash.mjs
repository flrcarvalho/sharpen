// Prova por EXECUÇÃO do menu de mercados no DASHBOARD (Minha Base / Em Aberto) — s286.
//
// Irmão de `menu_mercados.mjs` (que cobre a Extração). Recorta o código REAL de
// `charts/apostas.js` — as fontes de mercado e a memoização da contagem — e roda contra
// um feed sintético. A diferença que este teste existe para travar: aqui a frequência sai
// de `DADOS ∪ DADOS_ABERTAS`, o que a TELA mostra, e não da rota `/mercados`. Para um
// supervisor o feed inclui a base dos operadores, e contar no servidor daria um menu que
// não corresponde à tela.
//
// Provado por mutação — ver o final de tests/test_menu_mercados.py.
// NÃO cobre o gesto no DOM (duplo-clique, Enter, blur): isso é o motor de eventos.
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const CR = String.fromCharCode(13), LF = String.fromCharCode(10);
const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const ALVO = process.env.ALVO_DASH || path.join(RAIZ, 'app', 'static', 'dash', 'assets', 'js', 'charts', 'apostas.js');
const src = fs.readFileSync(ALVO, 'utf8').split(CR + LF).join(LF);

const corte = (ini, fim) => {
  const a = src.indexOf(ini); if (a < 0) throw new Error('não achei: ' + ini);
  const b = src.indexOf(fim, a); if (b < 0) throw new Error('não achei fim de: ' + ini);
  return src.slice(a, b + fim.length);
};
// Um corte só: do MKT_FAV até a última fonte. Ele arrasta junto o `apAviso`, que fala com
// o DOM — inofensivo, porque nada aqui o CHAMA (o corpo dele só roda se invocado). Se um
// dia esse trecho passar a tocar o DOM em tempo de carga, este teste quebra alto, e é o
// comportamento certo: seria um efeito colateral novo no caminho de import.
const bloco = corte('const MKT_FAV=', 'const AC_MKT_TODOS={ops:()=>_apMercadoTodos(),cont:_apMercadoCont};');

// Feed sintético desenhado para EXERCER cada regra — a 1ª versão dele tinha 5 mercados e
// deixou 3 mutações escaparem (o corte nunca era atingido, não havia empate de verdade, e
// o "só da base" também estava na taxonomia). Agora:
//   · 15 mercados > MKT_FAV, para o corte ser exercido;
//   · `Escanteios` e `Faltas` empatados em 6, para o desempate alfabético ter o que decidir;
//   · `Tênis de Mesa — Sets` só na base e FORA do MASTER (grafia herdada de import);
//   · `Handicap` só em aposta ABERTA (a armadilha da s239 — ler só DADOS o faria sumir).
const rep = (n, aposta) => Array(n).fill({ aposta });
const DADOS = [
  ...rep(9, 'Múltipla'), ...rep(6, 'Escanteios'), ...rep(5, 'Cartões'), ...rep(2, 'Gols'),
  // `Desarmes` entra ANTES de `Ambas Marcam` de propósito: os dois empatam em 3, e o sort
  // do V8 é estável — na ordem natural o teste passaria mesmo SEM desempate (foi o buraco
  // que deixou essa mutação escapar). Invertido, só o desempate alfabético salva.
  ...rep(6, 'Faltas'), ...rep(4, 'DNB'), ...rep(4, 'H2H'), ...rep(3, 'Desarmes'),
  ...rep(3, 'Ambas Marcam'), ...rep(2, 'Jardas'), ...rep(2, 'Corridas'), ...rep(1, 'Dupla Chance'),
  ...rep(1, 'Impedimentos'), ...rep(1, 'Tênis de Mesa — Sets'),
  { aposta: '' }, { },                                   // linha sem mercado não conta
];
const DADOS_ABERTAS = [{ aposta: 'Escanteios' }, { aposta: 'Handicap' }];

const mk = (dados, abertas, taxo) => new Function('DADOS', 'DADOS_ABERTAS', 'fetch', `
  ${bloco}
  _mktTaxo = ${JSON.stringify(taxo)};
  return { AC_MKT, AC_MKT_TODOS, _apMercadoCont, _apMercadoFav, _apMercadoTodos, MKT_FAV,
           _bump: () => { DADOS = DADOS.concat([{ aposta: 'Cartões' }, { aposta: 'Cartões' },
                                                { aposta: 'Cartões' }, { aposta: 'Cartões' },
                                                { aposta: 'Cartões' }]); } };
`)(dados, abertas, async () => ({ json: async () => ({}) }));

// Sem `Handicap` e sem `Tênis de Mesa — Sets` de propósito: os dois existem SÓ na base,
// e são eles que provam que a união não é só o MASTER.
const TAXO = ['Múltipla', 'Escanteios', 'Cartões', 'Gols', 'Faltas', 'DNB', 'H2H',
  'Ambas Marcam', 'Desarmes', 'Jardas', 'Corridas', 'Dupla Chance', 'Impedimentos',
  'Chutes no Gol', 'Escanteios Asiáticos'];
const F = mk(DADOS, DADOS_ABERTAS, TAXO);

let ok = 0, ko = 0;
const t = (nome, cond, extra = '') => { if (cond) { ok++; console.log('  ✓', nome); } else { ko++; console.log('  ✗', nome, extra); } };

console.log(LF + '1) contagem sai da TELA (DADOS ∪ DADOS_ABERTAS)');
const c = F._apMercadoCont();
t('conta as liquidadas', c['Múltipla'] === 9);
t('soma aberta na mesma chave', c['Escanteios'] === 7, JSON.stringify(c['Escanteios']));
t('mercado que só existe em ABERTA aparece', c['Handicap'] === 1);
t('linha sem mercado não vira chave', !('' in c) && !('undefined' in c));

console.log(LF + '2) favoritos — ordem e corte');
const fav = F._apMercadoFav();
t('ordena por frequência', fav[0] === 'Múltipla' && fav[1] === 'Escanteios');
// `Ambas Marcam` e `Desarmes` estão os dois em 3: sem o desempate, a ordem entre eles
// vira sorte do motor e o item muda de lugar entre uma abertura e outra do menu.
t('empate desempata por ordem alfabética', fav.indexOf('Ambas Marcam') < fav.indexOf('Desarmes'),
  fav.join(','));
t('corta em MKT_FAV (a base tem 15)', fav.length === F.MKT_FAV, 'len=' + fav.length);
// Quatro mercados empatados em 1 uso disputam a 12ª vaga; o desempate alfabético dá
// para `Dupla Chance` e deixa os outros três de fora. É a regra funcionando, não sobra.
t('o corte derruba os menos usados', !fav.includes('Impedimentos') && !fav.includes('Handicap'),
  fav.join(','));
t('só mercado da base — nada do MASTER entra nos favoritos', !fav.includes('Chutes no Gol'));

console.log(LF + '3) lista completa — união com o MASTER');
const todos = F._apMercadoTodos();
t('traz o canônico que ele nunca apostou', todos.includes('Chutes no Gol') && todos.includes('Impedimentos'));
t('preserva o que só existe na base', todos.includes('Handicap'));
t('preserva a grafia herdada de import que o MASTER não tem', todos.includes('Tênis de Mesa — Sets'));
t('alfabética', todos.join('|') === todos.slice().sort((a, b) => a.localeCompare(b, 'pt-BR')).join('|'));
t('não duplica o que está nos dois lados', todos.filter(x => x === 'Múltipla').length === 1);

console.log(LF + '4) as duas fontes que os dois gestos usam');
t('duplo-clique (sem digitar) → favoritos', F.AC_MKT.ops(false).length === fav.length && F.AC_MKT.ops(false)[0] === 'Múltipla');
t('digitou → lista completa', F.AC_MKT.ops(true).includes('Chutes no Gol'));
t('modal abre completo sem digitar', F.AC_MKT_TODOS.ops(false).includes('Chutes no Gol'));
t('as duas fontes expõem a contagem', typeof F.AC_MKT.cont === 'function' && typeof F.AC_MKT_TODOS.cont === 'function');

console.log(LF + '5) memo da contagem — invalida quando o feed muda');
const antes = F._apMercadoCont();
t('memo devolve o MESMO objeto enquanto o feed não muda', F._apMercadoCont() === antes);
F._bump();
const depois = F._apMercadoCont();
t('feed novo derruba o memo', depois !== antes && depois['Cartões'] === 10, JSON.stringify(depois['Cartões']));
t('e o novo total reordena os favoritos', F._apMercadoFav()[0] === 'Cartões', F._apMercadoFav().slice(0, 2).join(','));

console.log(LF + '6) sem base nenhuma (dono novo) não quebra');
const V = mk([], [], TAXO);
t('favoritos vazios, sem erro', V._apMercadoFav().length === 0);
t('lista completa ainda oferece o MASTER inteiro', V._apMercadoTodos().length === TAXO.length);

console.log(LF + ok + ' passaram · ' + ko + ' falharam');
process.exit(ko ? 1 : 0);
