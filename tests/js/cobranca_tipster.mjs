// Cobrança do tipster (s348, Fatia 3) — o TIPO decide se o valor se arrasta.
//
// Executa as funções RECORTADAS do `gestao.js` de produção. Nunca copia o trecho:
// teste que reimplementa o código sob teste é o 1º modo de falso verde do CLAUDE.md.
//
// A regra, na voz do Feca: "o número do mês anterior se arrasta se não for
// atualizado. Lançamento variável não atualiza pro próximo mês."
//
// O que este arquivo NÃO cobre: o render (a coluna, o botão "Repetir", o selo) e a
// gravação (`/custos/tipster/cobranca`), que vivem no `custos2.js` e no repositório.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const AQUI = dirname(fileURLToPath(import.meta.url));
const RAIZ = join(AQUI, '..', '..');
// ALVO_GESTAO existe para a prova por MUTACAO: o pytest aponta para uma copia
// estragada e exige que este arquivo fique VERMELHO. Sem ele a mutacao nao seria
// exercida pelo codigo real.
const GESTAO = readFileSync(process.env.ALVO_GESTAO || join(RAIZ, 'app', 'static', 'dash', 'assets', 'js', 'charts', 'gestao.js'), 'utf8');
const LF = '\n';

let falhas = 0;
const ok = (cond, msg) => { if (!cond) { console.error('  ✗ ' + msg); falhas++; } };

// Recorta uma função de topo de nível: o `}` de fechamento é o único na coluna 0.
const recorteFn = (src, nome) => {
  const m = src.match(new RegExp('^function ' + nome + '\\([^)]*\\)\\{[\\s\\S]*?^\\}', 'm'));
  if (!m) throw new Error('não achei a função ' + nome + ' no gestao.js');
  return m[0];
};

// `_ARRASTA` é const, não função: o recorte por assinatura não o pega. Ele é a
// regra do arrasto escrita uma vez, compartilhada com o custo geral (Fatia 4).
const recorteConst = (src, nome) => {
  const m = src.match(new RegExp('^const ' + nome + '=.*$', 'm'));
  if (!m) throw new Error('não achei a const ' + nome + ' no gestao.js');
  return m[0];
};

const FONTE = [recorteConst(GESTAO, '_ARRASTA'),
  ...['_arrasta', '_ctCobranca', '_ctParametro', '_ctTemporadaAte', '_ctValor',
      '_ctSugestao', '_ctSituacao', '_ctRepetiveis'].map(n => recorteFn(GESTAO, n)),
].join(LF);

const API = new Function(`
  let ctData = {}, ctMeta = {};
  ${FONTE}
  return {
    set(cfg) { ctData = cfg.custos || {}; ctMeta = cfg.meta || {}; },
    _ctSugestao, _ctSituacao, _ctRepetiveis, _ctCobranca, _ctValor, _arrasta,
  };
`)();

const MES = '2026-09', ANT = '2026-08';

// ── 1. Mensalidade ARRASTA ───────────────────────────────────────────────────
{
  API.set({ custos: { Ze: { [ANT]: '250,00' } }, meta: { Ze: { cobranca: 'mensalidade' } } });
  ok(API._ctSugestao('Ze', MES, ANT) === 250, 'mensalidade deveria arrastar 250, veio ' + API._ctSugestao('Ze', MES, ANT));
  ok(API._ctSituacao('Ze', MES) === 'pendente', 'sem valor no mês, mensalidade é pendente');
}

// ── 2. Staking NUNCA arrasta ─────────────────────────────────────────────────
// É a metade da regra que mais custa se errar: repetir um staking publica um número
// que já mudou, e ele passa por conferência de forma sem um arranhão.
{
  API.set({ custos: { Ze: { [ANT]: '1.240,00' } }, meta: { Ze: { cobranca: 'staking' } } });
  ok(API._ctSugestao('Ze', MES, ANT) === 0, 'staking não pode arrastar, veio ' + API._ctSugestao('Ze', MES, ANT));
  ok(API._ctSituacao('Ze', MES) === 'pendente', 'staking sem valor no mês é pendente');
}

// ── 3. "A definir" também não arrasta ────────────────────────────────────────
// Ausência de resposta não é mensalidade. Tratar vazio como mensalidade preencheria
// sozinho o mês de um tipster cujo tipo ninguém declarou.
{
  API.set({ custos: { Ze: { [ANT]: '250,00' } }, meta: {} });
  ok(API._ctSugestao('Ze', MES, ANT) === 0, 'tipo vazio não pode arrastar');
  ok(API._ctCobranca('Ze') === '', 'sem meta, a cobrança é string vazia');
}

// ── 4. Temporada: paga antes e dentro do prazo → COBERTO ─────────────────────
{
  API.set({ custos: { Ze: { '2026-03': '1.200,00' } },
            meta: { Ze: { cobranca: 'temporada', ate: '2026-12' } } });
  ok(API._ctSituacao('Ze', MES) === 'coberto', 'temporada paga e no prazo deveria ser coberto, veio ' + API._ctSituacao('Ze', MES));
  ok(API._ctSugestao('Ze', MES, ANT) === 0, 'temporada não arrasta');
}

// ── 5. Temporada VENCIDA volta a pedir ───────────────────────────────────────
// Sem esta, "temporada" viraria "pagou uma vez, nunca mais cobra" — custo que some
// do mês em silêncio.
{
  API.set({ custos: { Ze: { '2026-03': '1.200,00' } },
            meta: { Ze: { cobranca: 'temporada', ate: '2026-08' } } });
  ok(API._ctSituacao('Ze', MES) === 'pendente', 'temporada vencida deveria voltar a pendente, veio ' + API._ctSituacao('Ze', MES));
}

// ── 6. Temporada SEM pagamento anterior é pendente, não coberta ──────────────
{
  API.set({ custos: {}, meta: { Ze: { cobranca: 'temporada', ate: '2026-12' } } });
  ok(API._ctSituacao('Ze', MES) === 'pendente', 'temporada sem pagamento nenhum não pode estar coberta');
}

// ── 7. Temporada sem prazo declarado cobre enquanto houver pagamento ─────────
// Decisão registrada: `ate` vazio = sem prazo. A tela oferece o campo, então isto é
// escolha do dono e não efeito de não haver onde digitar.
{
  API.set({ custos: { Ze: { '2026-03': '1.200,00' } }, meta: { Ze: { cobranca: 'temporada' } } });
  ok(API._ctSituacao('Ze', MES) === 'coberto', 'temporada sem prazo segue cobrindo');
}

// ── 8. Sem cobrança resolve a linha sem valor ────────────────────────────────
{
  API.set({ custos: {}, meta: { Ze: { cobranca: 'sem_cobranca' } } });
  ok(API._ctSituacao('Ze', MES) === 'sem_custo', 'sem_cobranca deveria resolver a linha, veio ' + API._ctSituacao('Ze', MES));
}

// ── 9. Valor no mês vence tudo: é confirmado, seja qual for o tipo ───────────
{
  for (const tipo of ['mensalidade', 'staking', 'temporada', 'sem_cobranca', '']) {
    API.set({ custos: { Ze: { [MES]: '99,00' } }, meta: tipo ? { Ze: { cobranca: tipo } } : {} });
    ok(API._ctSituacao('Ze', MES) === 'confirmado', `valor no mês deveria confirmar (${tipo || 'a definir'})`);
  }
}

// ── 10. `_ctRepetiveis` só conta quem realmente aceitaria o clique ───────────
{
  API.set({
    custos: { Mensal: { [ANT]: '250,00' }, Stake: { [ANT]: '900,00' },
              Vazio: {}, Feito: { [MES]: '300,00', [ANT]: '300,00' } },
    meta: { Mensal: { cobranca: 'mensalidade' }, Stake: { cobranca: 'staking' },
            Vazio: { cobranca: 'mensalidade' }, Feito: { cobranca: 'mensalidade' } },
  });
  const rep = API._ctRepetiveis(['Mensal', 'Stake', 'Vazio', 'Feito'], MES, ANT);
  ok(rep.length === 1 && rep[0] === 'Mensal',
     'só a mensalidade pendente COM valor anterior repete, veio ' + JSON.stringify(rep));
}

// ── 11. O valor lê o formato BR gravado pela tela ────────────────────────────
{
  API.set({ custos: { Ze: { [MES]: '1.234,50' } }, meta: {} });
  ok(API._ctValor('Ze', MES) === 1234.5, 'deveria ler 1.234,50 como 1234.5, veio ' + API._ctValor('Ze', MES));
}

// ── 12. A regra compartilhada do arrasto ────────────────────────────────────
// `_arrasta` é usada pelo tipster E pelo custo geral (Fatia 4). Uma regra escrita
// duas vezes divergiria no dia em que um terceiro tipo aparecesse.
{
  ok(API._arrasta('mensalidade') === true, 'mensalidade arrasta');
  ok(API._arrasta('mensal') === true, 'mensal (custo geral) arrasta');
  for (const t of ['staking', 'temporada', 'sem_cobranca', 'variavel', 'avulso', '', undefined]) {
    ok(API._arrasta(t) === false, `«${t}» não pode arrastar`);
  }
}

if (falhas) { console.error(LF + falhas + ' verificação(ões) falharam.'); process.exit(1); }
console.log('cobranca_tipster.mjs: OK');
