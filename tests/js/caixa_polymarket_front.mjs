// Caixa Inteligente da Polymarket (s397) — o lado da tela.
//
// Prova, executando o código RECORTADO do `index.html` (`renderCaixa`, `_cxDiver` e os
// formatadores de que eles dependem) com um DOM mínimo:
// A. a Polymarket ENTRA na Caixa (o `carregarCaixa` não a exclui mais);
// B. desligada, ela diz que liga sozinha no Sincronizar e NÃO oferece o "Ativar"
//    (saldo inicial digitado à mão entraria por cima do automático);
// C. ligada, não tem campo de conferência, nem + Depósito / − Saque, nem saldo
//    inicial editável — viriam em dobro com os da blockchain; o Ajuste fica;
// D. "bate" com diferença de arredondamento mostra a diferença REAL, nunca um zero;
// E. a divergência diz "carteira" e aponta as apostas (depósito/saque são automáticos);
// F. conta de OUTRA casa sai exatamente como antes (campo, botões, lápis);
// G. o Sincronizar recarrega a Caixa.
//
// O que NÃO está coberto: o visual (medido no Chrome headless) e o extrato.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import vm from 'node:vm';

const AQUI = dirname(fileURLToPath(import.meta.url));
const RAIZ = join(AQUI, '..', '..');
const INDEX = readFileSync(process.env.ALVO_INDEX || join(RAIZ, 'app', 'static', 'index.html'), 'utf8').replace(/\r\n/g, '\n');

let falhas = 0;
const ok = (c, m) => { if (!c) { console.error('  ✗ ' + m); falhas++; } };

const fn = (nome, src = INDEX) => {
  const r = src.match(new RegExp('^(async )?function ' + nome + '\\([^)]*\\) \\{[\\s\\S]*?^\\}', 'm'));
  if (!r) throw new Error('não achei ' + nome);
  return r[0];
};
const cst = (nome) => {
  const r = INDEX.match(new RegExp('^const ' + nome + '\\s*=[\\s\\S]*?;$', 'm'));
  if (!r) throw new Error('não achei ' + nome);
  return r[0];
};

const box = { innerHTML: '', classList: { toggle() {} } };
const ctx = { document: { getElementById: (id) => (id === 'caixaBox' ? box : null) } };
vm.createContext(ctx);
vm.runInContext([cst('_MOEDA_ORIG'), cst('_CX_PILL'), fn('_num2BR'), fn('fmtMoedaOrig'), fn('moneyOrig'),
  fn('fmtPL'), fn('fmtSaldo'), fn('_cxSigla'), fn('_cxTxt'), fn('_cxDataBR'), fn('_cxDataBR4'),
  fn('hojeISO'), fn('_cxDiver'), fn('renderCaixa')].join('\n')
  + '\nthis.api = { renderCaixa };', ctx);
const render = (d) => { box.innerHTML = ''; ctx.api.renderCaixa(d); return box.innerHTML; };
const txt = (h) => h.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ');

const base = {
  parceiro: 'Feca [Eu]', moeda: 'USD', ligada: true, inicial: 0, data_corte: '2026-05-06',
  preso_corte: 0, n_preso_corte: 0, depositos: 3116.67, n_depositos: 8, saques: 0, n_saques: 0,
  ajustes: 2.88, n_ajustes: 1, pl: -2617.46, n_liquidadas: 577, aberto: 492.32, n_abertas: 19,
  banca: 502.09, disponivel: 9.77, pl_anterior: 0, n_anteriores: 0, n_sem_origem: 0,
  n_mov_outra_moeda: 0, tolerancia: 0.31,
};
const conf = (div, valor = 9.9, proj = 9.77) => ({ data: '2026-10-06', valor, projetado: proj, divergencia: div });

// A. a Polymarket entra
const carregar = fn('carregarCaixa');
ok(!/casaSelecionada === 'Polymarket'/.test(carregar), 'A: carregarCaixa ainda exclui a Polymarket');

// B. desligada
const des = render({ casa: 'Polymarket', moeda: 'USD', ligada: false, estado: 'desligada' });
ok(txt(des).includes('liga sozinha no próximo Sincronizar'), 'B: desligada diz que liga no Sincronizar');
ok(!des.includes('caixaAbrirModal'), 'B: desligada não oferece o Ativar');

// C. ligada
const lig = render({ ...base, casa: 'Polymarket', estado: 'confere', divergencia: 0.13, conferencia: conf(0.13) });
ok(!lig.includes('cx-conf-val'), 'C: não há campo de conferência à mão');
ok(!lig.includes('&quot;deposito&quot;') && !lig.includes('&quot;saque&quot;'), 'C: sem + Depósito / − Saque');
ok(lig.includes('&quot;ajuste&quot;'), 'C: o Ajuste continua');
ok(!lig.includes('cx__row--edit') && !lig.includes('&quot;inicial&quot;'), 'C: saldo inicial não é editável');
ok(txt(lig).includes('Início da carteira') && txt(lig).includes('Conferência automática'), 'C: diz que é automática');
ok(txt(lig).includes('vêm da carteira na blockchain'), 'C: a nota diz de onde vêm os lançamentos');

// D. bate com arredondamento: a diferença real
ok(/Bate com a carteira.*0,13.*arredondamento/.test(txt(lig)), 'D: mostra a diferença real de arredondamento');
const zero = render({ ...base, casa: 'Polymarket', estado: 'confere', divergencia: 0, conferencia: conf(0, 9.77) });
ok(/Bate com a carteira/.test(txt(zero)) && !/arredondamento/.test(txt(zero)), 'D: diferença zero não fala em arredondamento');

// E. divergente
const div = render({ ...base, casa: 'Polymarket', estado: 'divergente', disponivel: 270.32, divergencia: -260.42, conferencia: conf(-260.42, 9.9, 270.32) });
ok(/a carteira tinha/.test(txt(div)) && /a diferença está nas apostas/.test(txt(div)), 'E: divergência fala da carteira e aponta as apostas');
ok(!/saque não lançado/.test(txt(div)), 'E: não manda procurar saque não lançado');

// F. outra casa: como sempre
const bet = render({ ...base, casa: 'Betano', moeda: 'BRL', tolerancia: 0, estado: 'confere', divergencia: 0, conferencia: conf(0, 9.77) });
ok(bet.includes('cx-conf-val') && bet.includes('&quot;deposito&quot;') && bet.includes('&quot;saque&quot;'), 'F: Betano mantém campo e botões');
ok(bet.includes('cx__row--edit') && /Bate com a casa/.test(txt(bet)), 'F: Betano mantém o lápis e o "casa"');
const betDes = render({ casa: 'Betano', moeda: 'BRL', ligada: false, estado: 'desligada' });
ok(betDes.includes('&quot;inicial&quot;'), 'F: Betano desligada mantém o Ativar');

// G. o sync recarrega a Caixa
ok(/carregarCaixa\(\)/.test(fn('sincronizarPolymarket')), 'G: o Sincronizar recarrega a Caixa');

if (falhas) { console.error(`\n${falhas} falha(s)`); process.exit(1); }
console.log('ok: caixa da polymarket (tela)');
