// O RECORTE da tela de Custos (s348) — "Tudo" tem de significar tudo.
//
// Nasceu de um defeito medido comparando a tela antiga com a nova: com «Tudo»
// ativo a aba Contas somava R$ 0 e a tela antiga somava R$ 29.400, com o MESMO
// dado. A causa não era o dado, era o recorte — `_c2range` caía no mês corrente
// quando `_selRange` devolve null, e null é justamente o que "Tudo" devolve.
//
// O rótulo prometia a série inteira e o número entregava um mês. É a mesma família
// dos outros defeitos desta frente: rótulo e número discordando sem dar erro.
//
// Executa as funções RECORTADAS do `custos2.js` de produção, mais o `_selRange`
// REAL do `filters.js` — dublá-lo esconderia a metade que traduz o botão escolhido
// em {from,to}, que é onde o defeito morava.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const AQUI = dirname(fileURLToPath(import.meta.url));
const RAIZ = join(AQUI, '..', '..');
const BASE = join(RAIZ, 'app', 'static', 'dash', 'assets', 'js');
// ALVO_CUSTOS2 existe para a prova por MUTAÇÃO.
const CUSTOS2 = readFileSync(process.env.ALVO_CUSTOS2 || join(BASE, 'charts', 'custos2.js'), 'utf8');
const FILTROS = readFileSync(join(BASE, 'filters.js'), 'utf8');
const LF = '\n';

let falhas = 0;
const ok = (cond, msg) => { if (!cond) { console.error('  ✗ ' + msg); falhas++; } };

const recorteFn = (src, nome, arq) => {
  const m = src.match(new RegExp('^function ' + nome + '\\([^)]*\\)\\{[\\s\\S]*?^\\}', 'm'));
  if (!m) throw new Error('não achei a função ' + nome + ' no ' + arq);
  return m[0];
};

const FONTE = [
  ...['_c2meses', '_c2primeiraData', '_c2range'].map(n => recorteFn(CUSTOS2, n, 'custos2.js')),
  ...['_ymd', '_today', 'gfs', '_selRange'].map(n => recorteFn(FILTROS, n, 'filters.js')),
].join(LF);

const API = new Function(`
  const FS = {};
  let _contasVida = null, ctData = {}, cgData = [];
  ${FONTE}
  return {
    set(cfg) {
      _contasVida = cfg.cadastro || null; ctData = cfg.custos || {}; cgData = cfg.gerais || [];
      for (const k of Object.keys(FS)) delete FS[k];
      if (cfg.periodo) FS.custos_v2 = Object.assign(gfs('custos_v2'), cfg.periodo);
    },
    _c2range, _c2primeiraData,
  };
`)();

const hoje = (() => { const d = new Date(); return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); })();
const mesCorrente = hoje.slice(0, 7) + '-01';
const cad = (adq) => ({ casa: 'Bet365', conta: 'c' + adq, fornecedor: 'GN', adquirida_em: adq, arquivada_em: '', arquivado: false });
// "Tudo" no filters.js é o estado ZERADO: sem datas e sem atalho.
const TUDO = { df: '', dt: '', qd: 0, qt: '' };

// ── 1. "Tudo" começa na PRIMEIRA compra, não no mês corrente ─────────────────
{
  API.set({ cadastro: [cad('2026-01-18'), cad('2026-05-02')], periodo: TUDO });
  const r = API._c2range();
  ok(r.de === '2026-01-18', '«Tudo» deveria começar em 2026-01-18, veio ' + r.de);
  ok(r.ate === hoje, '«Tudo» vai até hoje, veio ' + r.ate);
  ok(r.meses.length > 1, '«Tudo» tem de cobrir mais de um mês, veio ' + r.meses.length);
}

// ── 2. O mês de custo de tipster também conta como primeiro dado ─────────────
// Quem só lança tipster (sem conta cadastrada) não pode cair no mês corrente.
{
  API.set({ custos: { Ze: { '2026-03': '250,00', '2026-07': '250,00' } }, periodo: TUDO });
  ok(API._c2primeiraData() === '2026-03-01', 'o 1º mês de tipster deveria abrir o período, veio ' + API._c2primeiraData());
  ok(API._c2range().de === '2026-03-01', '«Tudo» deveria começar em 2026-03-01');
}

// ── 3. E o custo geral também ────────────────────────────────────────────────
{
  API.set({ gerais: [{ id: 1, tipo: 'VPN', values: { '2026-02': '39,00' } }], periodo: TUDO });
  ok(API._c2primeiraData() === '2026-02-01', 'o 1º mês de geral deveria abrir o período, veio ' + API._c2primeiraData());
}

// ── 4. A MAIS ANTIGA das três fontes é que manda ─────────────────────────────
{
  API.set({
    cadastro: [cad('2026-06-01')],
    custos: { Ze: { '2026-04': '250,00' } },
    gerais: [{ id: 1, tipo: 'VPN', values: { '2026-02': '39,00' } }],
    periodo: TUDO,
  });
  ok(API._c2primeiraData() === '2026-02-01', 'a mais antiga das três fontes manda, veio ' + API._c2primeiraData());
}

// ── 5. Sem dado nenhum, "Tudo" é o mês corrente ──────────────────────────────
// É o único caso em que "tudo" e "este mês" são a mesma coisa — e aí o rótulo não
// mente, porque não há nada antes.
{
  API.set({ periodo: TUDO });
  ok(API._c2primeiraData() === '', 'sem dado, não há primeira data');
  ok(API._c2range().de === mesCorrente, 'sem dado, «Tudo» cai no mês corrente, veio ' + API._c2range().de);
}

// ── 6. Período escolhido MANDA sobre tudo isso ───────────────────────────────
// O dado velho não pode puxar o recorte para trás quando o dono escolheu um mês.
{
  API.set({ cadastro: [cad('2026-01-18')], periodo: { df: '2026-09-01', dt: '2026-09-30', qd: 0, qt: 'mtd' } });
  const r = API._c2range();
  ok(r.de === '2026-09-01' && r.ate === '2026-09-30', 'o período escolhido manda, veio ' + r.de + '→' + r.ate);
  ok(r.meses.length === 1, 'um mês escolhido é um mês, veio ' + r.meses.length);
  ok(r.mesRef === '2026-09', 'o mês de referência é o último do recorte, veio ' + r.mesRef);
}

// ── 7. O atalho de dias também manda ─────────────────────────────────────────
{
  API.set({ cadastro: [cad('2020-01-01')], periodo: { df: '', dt: '', qd: 30, qt: '' } });
  const r = API._c2range();
  ok(r.ate === hoje, '30d termina hoje, veio ' + r.ate);
  ok(r.de > '2020-01-01', '30d não pode voltar a 2020 só porque existe conta de lá, veio ' + r.de);
}

// ── 8. `mesRef` é sempre o ÚLTIMO mês do recorte ─────────────────────────────
// É ele que as abas Tipsters e Gerais listam; pegar o primeiro faria a tela pedir
// o lançamento de um mês que já passou.
{
  API.set({ cadastro: [cad('2026-01-18')], periodo: TUDO });
  const r = API._c2range();
  ok(r.mesRef === r.meses[r.meses.length - 1], 'mesRef tem de ser o último mês do recorte');
  ok(r.mesRef === hoje.slice(0, 7), 'com «Tudo» o mês de referência é o corrente, veio ' + r.mesRef);
}

if (falhas) { console.error(LF + falhas + ' verificação(ões) falharam.'); process.exit(1); }
console.log('recorte_custos.mjs: OK');
