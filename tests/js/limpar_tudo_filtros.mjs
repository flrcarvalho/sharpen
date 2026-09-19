// O "Limpar tudo" da barra de filtros (s374, sugestão do tester João).
//
// Ele existia só na Base Completa. Quem recortava a Visão Geral por esporte, casa e
// tipster tinha de desfazer os três um a um, e a barra não dizia que havia recorte
// ligado. Agora a peça é da BARRA, e toda tela que monta barra o ganha junto.
//
// Executa as funções RECORTADAS do `filters.js` de produção. Nunca copia o trecho:
// teste que reimplementa o código sob teste é o 1º modo de falso verde do CLAUDE.md.
//
// O que este arquivo NÃO cobre:
//   · a POSIÇÃO do botão na barra e o CSS (`margin-left:auto`, o `[hidden]` explícito
//     que vence o `display:flex` do `.filter-group`): isso só a tela mede, e foi medido
//     em headless nas 10 telas contra o `servidor_demo`;
//   · o repaint de verdade (`renderPage` é dublado aqui), e portanto o efeito do clique
//     na tabela/KPI que vem depois;
//   · a Base Completa, que tem o botão dela na faixa de filtros ativos (gate próprio em
//     `tests/js/filtros_base_completa.mjs`).
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const AQUI = dirname(fileURLToPath(import.meta.url));
const RAIZ = join(AQUI, '..', '..');
// ALVO_FILTERS existe para a prova por MUTAÇÃO: o pytest aponta para uma cópia
// estragada e exige que este arquivo fique VERMELHO.
const SRC = readFileSync(process.env.ALVO_FILTERS
  || join(RAIZ, 'app', 'static', 'dash', 'assets', 'js', 'filters.js'), 'utf8');
const LF = '\n';

let falhas = 0;
const ok = (cond, msg) => { if (!cond) { console.error('  ✗ ' + msg); falhas++; } };

const recorteFn = (nome) => {
  const m = SRC.match(new RegExp('^function ' + nome + '\\([^)]*\\)\\{.*\\}$', 'm'))
    || SRC.match(new RegExp('^function ' + nome + '\\([^)]*\\)\\{[\\s\\S]*?^\\}', 'm'));
  if (!m) throw new Error('não achei a função ' + nome + ' no filters.js');
  return m[0];
};
const recorteConst = (nome) => {
  const m = SRC.match(new RegExp('^const ' + nome + '=.*$', 'm'));
  if (!m) throw new Error('não achei a const ' + nome + ' no filters.js');
  return m[0];
};

const FONTE = [
  recorteConst('_PERIODO_PADRAO'),
  recorteConst('LIMPAR_EXTRA'),
  ...['gfs', 'msGet', 'msInit', 'msToggle', '_eixosDaPagina', '_periodoLigado',
      'temFiltroAtivo', '_syncLimparTudo', 'limparFiltrosPagina', '_grupoLimpar',
      'clearDate', 'setQuickType', 'setQuick', '_ymd', '_today', '_wtdStart',
      '_mtdStart', '_ytdStart'].map(recorteFn),
].join(LF);

// Dublês: o DOM (só o wrapper do botão importa aqui), o repaint e o refresh visual do
// multiselect. `repaints` conta quantas vezes a tela seria repintada, que é a metade da
// regra que ninguém vê: limpar quatro eixos com repaint em cada um mostra o recorte pela
// metade antes de mostrar a tela limpa.
const API = new Function(`
  const wraps = {};
  const document = {
    getElementById: id => wraps[id] || null,
    querySelectorAll: () => [],
  };
  let repaints = 0, rqbs = 0;
  const FS = {};
  const MSS = {};
  function refreshMS(){}
  function rqb(p){ rqbs++; _syncLimparTudo(p); }
  function _renderPageDebounced(){ repaints++; }
  function renderPage(){ repaints++; }
  ${FONTE}
  return {
    MSS, LIMPAR_EXTRA,
    estado(p) { return { ...FS[p] }; },
    criarWrap(p) { wraps['limparWrap_' + p] = { id: 'limparWrap_' + p, hidden: true }; },
    wrap(p) { return wraps['limparWrap_' + p]; },
    reset() { for (const k in MSS) delete MSS[k]; for (const k in FS) delete FS[k];
              for (const k in LIMPAR_EXTRA) delete LIMPAR_EXTRA[k];
              repaints = 0; rqbs = 0; },
    repaints: () => repaints,
    eixos: (p) => _eixosDaPagina(p),
    temFiltroAtivo, limparFiltrosPagina, _grupoLimpar, _syncLimparTudo,
    msToggle, setQuick, setQuickType, clearDate, gfs,
  };
`)();

const liga = (id, val) => { API.MSS[id] = new Set([val]); };

// ── 1. Tela limpa: o botão existe no markup, mas nasce ESCONDIDO ─────────────
// Botão morto numa tela sem recorte é ruído, e a tela abre sem recorte.
{
  API.reset();
  API.gfs('overview');
  ok(API.temFiltroAtivo('overview') === false, 'tela recém-aberta não tem filtro ativo');
  const html = API._grupoLimpar('overview');
  ok(html.includes('id="limparWrap_overview"'), 'o wrapper precisa do id da página');
  ok(html.includes(' hidden>'), 'sem filtro, o botão nasce hidden');
  ok(html.includes('limparFiltrosPagina(\'overview\')'), 'o clique chama o limpador da própria página');
  ok(html.includes('Limpar tudo'), 'o rótulo é o mesmo da Base Completa');
  ok(html.includes('class="apf-limpar"'), 'reusa o botão da Base Completa, não um estilo novo');
}

// ── 2. Um eixo ligado já acende o botão; o período também ────────────────────
{
  API.reset();
  API.gfs('overview');
  liga('sp_overview', 'Basquete');
  ok(API.temFiltroAtivo('overview') === true, 'eixo selecionado é filtro ativo');
  ok(API._grupoLimpar('overview').includes(' hidden>') === false, 'com filtro, o botão nasce visível');

  API.reset();
  API.setQuick('resultados', 30);
  ok(API.temFiltroAtivo('resultados') === true, 'período de 30d é filtro ativo');
}

// ── 3. O botão acompanha o estado sem ninguém repintar a barra ───────────────
// O markup da barra é montado uma vez por página; quem liga e desliga o botão depois é
// o `_syncLimparTudo`, chamado pelo `rqb` e pelo `refreshMS`.
{
  API.reset();
  API.criarWrap('overview');
  API.gfs('overview');
  API._syncLimparTudo('overview');
  ok(API.wrap('overview').hidden === true, 'tela limpa mantém o botão escondido');
  liga('ca_overview', 'Bet365');
  API._syncLimparTudo('overview');
  ok(API.wrap('overview').hidden === false, 'ligar um eixo acende o botão');
  API.limparFiltrosPagina('overview');
  ok(API.wrap('overview').hidden === true, 'limpar apaga o botão de novo');
}

// ── 4. Limpa os eixos DA PÁGINA e não encosta nos da vizinha ─────────────────
// As telas vivem no mesmo documento e o `MSS` é global: limpar o vizinho seria invisível
// aqui e apareceria na próxima aba que o usuário abrisse, sem erro nenhum.
{
  API.reset();
  API.gfs('overview');
  liga('sp_overview', 'Basquete');
  liga('ca_overview', 'Bet365');
  liga('ti_overview', 'Chasing');
  liga('sp_tipsters', 'Futebol');          // outra página
  liga('ca_custos_tipster', 'Betano');      // nome de página aninhado no da outra
  API.limparFiltrosPagina('overview');
  ok(API.MSS['sp_overview'].size === 0 && API.MSS['ca_overview'].size === 0
    && API.MSS['ti_overview'].size === 0, 'os três eixos da página têm de sair juntos');
  ok(API.MSS['sp_tipsters'].size === 1, 'o eixo de outra página não pode ser tocado');
  ok(API.eixos('tipster').length === 0,
    '`_eixosDaPagina("tipster")` não pode capturar `ca_custos_tipster`, que é de outra tela');
  ok(API.repaints() === 1, 'UM repaint só no fim, veio ' + API.repaints());
}

// ── 5. Custos limpa para o MÊS, não para o vazio ─────────────────────────────
// A tela nasce em MTD de propósito (é de fechamento mensal, e "Tudo" não fecha mês
// nenhum). Limpar para o vazio a levaria a um estado que ela nunca teve ao abrir.
{
  API.reset();
  API.setQuickType('custos_v2', 'mtd');
  ok(API.temFiltroAtivo('custos_v2') === false,
    'o período PADRÃO da tela não conta como filtro ligado');
  API.setQuick('custos_v2', 90);
  ok(API.temFiltroAtivo('custos_v2') === true, '90d na tela de custos é filtro ligado');
  API.limparFiltrosPagina('custos_v2');
  ok(API.estado('custos_v2').qt === 'mtd' && API.estado('custos_v2').qd === 0,
    'limpar a tela de Custos devolve o MÊS, veio qt=' + API.estado('custos_v2').qt);

  API.reset();
  API.setQuick('overview', 90);
  API.limparFiltrosPagina('overview');
  const st = API.estado('overview');
  ok(!st.qt && !st.qd && !st.df && !st.dt, 'nas outras telas limpar devolve "Tudo"');
}

// ── 6. Filtro LOCAL da tela entra na conta ───────────────────────────────────
// O seg de População do Painel de Contas não vive no `MSS`. Sem o registro, o botão
// limparia metade da tela e ainda assim diria "Limpar tudo": rótulo que mente é pior
// que botão que falta.
{
  API.reset();
  let pop = 'inativas';
  API.LIMPAR_EXTRA.contas = { ativo: () => pop !== 'ambas', limpar: () => { pop = 'ambas'; } };
  ok(API.temFiltroAtivo('contas') === true, 'filtro local ligado acende o botão');
  API.limparFiltrosPagina('contas');
  ok(pop === 'ambas', 'o filtro local tem de voltar ao padrão da tela');
  ok(API.temFiltroAtivo('contas') === false, 'depois de limpar, nada fica ligado');
}

if (falhas) { console.error(LF + falhas + ' verificação(ões) falharam.'); process.exit(1); }
console.log('limpar_tudo_filtros.mjs: OK');
