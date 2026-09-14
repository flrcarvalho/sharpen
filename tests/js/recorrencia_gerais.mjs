// Custo geral: categoria e recorrência (s348, Fatia 4).
//
// Executa as funções RECORTADAS do `gestao.js` de produção — nunca copia o trecho.
//
// Duas coisas se provam aqui, e elas falham de jeitos diferentes:
//   1. a RECORRÊNCIA decide o arrasto, e ela usa o MESMO `_arrasta` do tipster;
//   2. a lista de CATEGORIAS é derivada das linhas, então não há lista para manter
//      nem categoria órfã para limpar — mas a ordem e a deduplicação importam.
//
// O que NÃO está coberto: o render da aba e a gravação (`ctSave` → /custos/store).
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const AQUI = dirname(fileURLToPath(import.meta.url));
const RAIZ = join(AQUI, '..', '..');
// ALVO_GESTAO existe para a prova por MUTAÇÃO: o pytest aponta para uma cópia
// estragada e exige que este arquivo fique VERMELHO.
const GESTAO = readFileSync(process.env.ALVO_GESTAO ||
  join(RAIZ, 'app', 'static', 'dash', 'assets', 'js', 'charts', 'gestao.js'), 'utf8');
const LF = '\n';

let falhas = 0;
const ok = (cond, msg) => { if (!cond) { console.error('  ✗ ' + msg); falhas++; } };

const recorteFn = (src, nome) => {
  const m = src.match(new RegExp('^function ' + nome + '\\([^)]*\\)\\{[\\s\\S]*?^\\}', 'm'));
  if (!m) throw new Error('não achei a função ' + nome + ' no gestao.js');
  return m[0];
};
const recorteConst = (src, nome) => {
  const m = src.match(new RegExp('^const ' + nome + '=.*$', 'm'));
  if (!m) throw new Error('não achei a const ' + nome + ' no gestao.js');
  return m[0];
};

const FONTE = [
  recorteConst(GESTAO, '_ARRASTA'),
  recorteConst(GESTAO, 'CG_CATEGORIAS_BASE'),
  ...['_arrasta', '_cgLinha', '_cgCategoria', '_cgRecorrencia', '_cgValor',
      '_cgSugestao', '_cgSituacao', '_cgCategorias', '_cgEhDeFabrica'].map(n => recorteFn(GESTAO, n)),
].join(LF);

const API = new Function(`
  let cgData = [];
  ${FONTE}
  return {
    set(linhas) { cgData = linhas || []; },
    _cgSugestao, _cgSituacao, _cgCategorias, _cgCategoria, _cgRecorrencia,
    _cgValor, _cgEhDeFabrica,
  };
`)();

const MES = '2026-09', ANT = '2026-08';
const linha = (o) => Object.assign({ id: 1, tipo: 'X', values: {} }, o);

// ── 1. Mensal ARRASTA ────────────────────────────────────────────────────────
{
  API.set([linha({ recorrencia: 'mensal', values: { [ANT]: '680,00' } })]);
  ok(API._cgSugestao(0, MES, ANT) === 680, 'mensal deveria arrastar 680, veio ' + API._cgSugestao(0, MES, ANT));
  ok(API._cgSituacao(0, MES) === 'pendente', 'sem valor no mês, mensal é pendente');
}

// ── 2. Variável e avulso NÃO arrastam ────────────────────────────────────────
// A API de extração custou R$ 612 num mês e R$ 471 no outro: repetir o anterior
// publicaria um número que já mudou, e ele passa por conferência de forma intacto.
{
  for (const r of ['variavel', 'avulso']) {
    API.set([linha({ recorrencia: r, values: { [ANT]: '612,00' } })]);
    ok(API._cgSugestao(0, MES, ANT) === 0, `«${r}» não pode arrastar, veio ` + API._cgSugestao(0, MES, ANT));
  }
}

// ── 3. Recorrência não declarada também não arrasta ──────────────────────────
// Linha antiga (anterior à Fatia 4) não tem `recorrencia`. Tratar a ausência como
// mensal preencheria sozinha a linha de alguém que nunca disse que é mensal.
{
  API.set([linha({ values: { [ANT]: '680,00' } })]);
  ok(API._cgSugestao(0, MES, ANT) === 0, 'sem recorrência declarada não arrasta');
  ok(API._cgRecorrencia(0) === '', 'linha antiga lê recorrência vazia');
}

// ── 4. Valor no mês confirma, qualquer que seja a recorrência ────────────────
{
  for (const r of ['mensal', 'variavel', 'avulso', '']) {
    API.set([linha({ recorrencia: r, values: { [MES]: '39,00' } })]);
    ok(API._cgSituacao(0, MES) === 'confirmado', `valor no mês deveria confirmar («${r}»)`);
  }
}

// ── 5. Linha inexistente não explode ─────────────────────────────────────────
// A aba re-renderiza a cada gravação, e apagar uma linha reordena os índices.
{
  API.set([]);
  ok(API._cgValor(0, MES) === 0, 'índice fora da lista devolve 0');
  ok(API._cgSituacao(0, MES) === 'pendente', 'índice fora da lista não pode confirmar');
  ok(API._cgCategoria(7) === '', 'índice fora da lista devolve categoria vazia');
}

// ── 6. Categorias: as três de fábrica sempre existem ─────────────────────────
{
  API.set([]);
  const c = API._cgCategorias();
  ok(JSON.stringify(c) === JSON.stringify(['Infra', 'Ferramenta', 'Taxa']),
     'sem linha nenhuma, só as de fábrica, veio ' + JSON.stringify(c));
}

// ── 7. Categoria do dono entra na lista, sem duplicar as de fábrica ─────────
{
  API.set([
    linha({ id: 1, categoria: 'Infra' }),
    linha({ id: 2, categoria: 'IA · Extração' }),
    linha({ id: 3, categoria: 'Contabilidade' }),
    linha({ id: 4, categoria: 'IA · Extração' }),   // repetida: entra uma vez só
    linha({ id: 5, categoria: '' }),                // vazia: não vira categoria
  ]);
  const c = API._cgCategorias();
  ok(JSON.stringify(c) === JSON.stringify(['Infra', 'Ferramenta', 'Taxa', 'Contabilidade', 'IA · Extração']),
     'fábrica primeiro, depois as do dono em ordem pt-BR, veio ' + JSON.stringify(c));
}

// ── 8. Quem é de fábrica e quem é do dono ────────────────────────────────────
// A tela marca as do dono; confundir as duas faria a de fábrica parecer criada por
// ele e virar candidata a "apagar".
{
  ok(API._cgEhDeFabrica('Infra') === true, 'Infra é de fábrica');
  ok(API._cgEhDeFabrica('  Taxa  ') === true, 'espaço em volta não muda o que a categoria é');
  ok(API._cgEhDeFabrica('IA · Extração') === false, 'categoria do dono não é de fábrica');
  ok(API._cgEhDeFabrica('') === false, 'vazio não é categoria de fábrica');
}

// ── 9. O valor lê o formato BR gravado pela tela ─────────────────────────────
{
  API.set([linha({ values: { [MES]: '1.234,50' } })]);
  ok(API._cgValor(0, MES) === 1234.5, 'deveria ler 1.234,50 como 1234.5, veio ' + API._cgValor(0, MES));
}

if (falhas) { console.error(LF + falhas + ' verificação(ões) falharam.'); process.exit(1); }
console.log('recorrencia_gerais.mjs: OK');
