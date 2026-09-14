// ── custos2.js — Custos (tela única) · FATIA 0: PRÉVIA, SÓ LEITURA ───────────
//
// Substitui, em prévia, as três telas de custo que o Feca não usava (Custos de
// Contas, Custo de Tipsters, Fornecedores & Parceiros). O desenho está no canvas
// "Custos e Retorno": topo fixo (filtros do sistema + KPIs + cascata + aviso do
// que falta) e quatro abas — Contas · Tipsters · Gerais · Raio-X.
//
// ⚠️ NADA AQUI GRAVA. A tela lê o que já está no ar e não cria estrutura nova:
//   · custoData          (gestao.js)  custo por PAR `fornecedor||casa`
//   · ctData / cgData    (app.js)     custo de tipster e geral, por mês
//   · _contasVida        (gestao.js)  cadastro com adquirida_em / arquivada_em
//   · DADOS / DADOS_ABERTAS          bilhetes
// O lançamento segue nas telas antigas até a Fatia 2. É de propósito: a prévia
// existe para o Feca navegar na base REAL antes de existir migração para desfazer.
//
// ⚠️ RÉGUA DIFERENTE DA VISÃO GERAL, e a tela diz isso na cara.
//   Visão Geral  → JANELA DE VIDA: custo cheio de toda conta VIVA no recorte
//                  (`calcCostFiltered`, CLAUDE.md "Custo de aquisição tem janela de vida").
//   Custos (aqui)→ LANÇAMENTO: o que foi PAGO no mês, ou seja, conta comprada no mês.
//   As duas estão certas e respondem perguntas diferentes. Sem o rótulo, uma
//   pareceria defeito da outra — é o caso "os dois números certos que pareciam
//   defeito" do CLAUDE.md. Qual vira a régua única é decisão da Fatia 2.

let _c2aba = 'contas';
let _c2fornOpen = null;   // accordion da tabela de preços: um fornecedor aberto por vez

// ── Peças de apoio ───────────────────────────────────────────────────────────

// Parse de valor gravado como string BR ("250,00"). É PARSE, não display: a regra de
// não usar .replace vale para a máscara de saída (UI_REFERENCE §5.2).
//
// Delega ao `parseNum` (app.js), que é o parser do projeto (UI_REFERENCE, item 6 da regra
// de UI: "não escreva um segundo parser"). A régua própria daqui apagava TODO ponto antes
// de converter, e com isso decidia milhar pela presença do separador em vez da FORMA do
// número: `179.90` virava 17.990,00. São 2 linhas na base real — `Só Chutes` jul/26 e
// `Curva Rápida` jul/26 — e mesmo assim o total de custo do sistema mudava de R$ 30.884
// para R$ 66.504 conforme a tela que lia. A régua certa: ponto só é milhar em grupos de
// três (`1.234`); um separador só, com outra contagem, é DECIMAL (s358).
function _c2num(v){
  if (typeof parseNum === 'function') return parseNum(v);
  // Sem o app.js (nenhum caminho de produção cai aqui): pior ser conservador que somar
  // errado — devolve 0 e a tela mostra o valor faltando em vez de um número inventado.
  return 0;
}

// Lista de meses "AAAA-MM" entre duas datas ISO, inclusive nas duas pontas.
function _c2meses(de, ate){
  const out = [];
  let y = +de.slice(0, 4), m = +de.slice(5, 7);
  const ye = +ate.slice(0, 4), me = +ate.slice(5, 7);
  let guard = 0;
  while ((y < ye || (y === ye && m <= me)) && guard++ < 240){
    out.push(y + '-' + String(m).padStart(2, '0'));
    if (++m > 12){ m = 1; y++; }
  }
  return out;
}
function _c2mesAnterior(ym){
  let y = +ym.slice(0, 4), m = +ym.slice(5, 7) - 1;
  if (m < 1){ m = 12; y--; }
  return y + '-' + String(m).padStart(2, '0');
}
function _c2mesRotulo(ym){
  if (!ym) return '—';
  return MESES_CURTOS[+ym.slice(5, 7) - 1].toLowerCase() + '/' + ym.slice(2, 4);
}

// A data do primeiro custo que existe: compra de conta, mês de custo de tipster ou
// de geral. É o começo de "Tudo" — inventar o mês corrente ali faria o botão prometer
// a série inteira e entregar um mês (medido: a aba somava R$ 0 e a tela antiga
// R$ 29.400 com o mesmo dado).
function _c2primeiraData(){
  let min = '';
  const marca = (d) => { if (d && (!min || d < min)) min = d; };
  (typeof _contasVida !== 'undefined' && _contasVida ? _contasVida : [])
    .forEach(p => marca(p.adquirida_em));
  Object.values((typeof ctData !== 'undefined' && ctData) || {})
    .forEach(m => Object.keys(m || {}).forEach(ym => marca(ym + '-01')));
  ((typeof cgData !== 'undefined' && cgData) || [])
    .forEach(r => Object.keys((r && r.values) || {}).forEach(ym => marca(ym + '-01')));
  return min;
}

// O recorte da tela. Sem período escolhido ("Tudo") vale desde o primeiro custo que
// existe até hoje — o rótulo do botão e o número têm de dizer a mesma coisa. Só quando
// não há dado nenhum é que "tudo" e "este mês" coincidem.
function _c2range(){
  const r = (typeof _selRange === 'function') ? _selRange('custos_v2') : null;
  const hoje = _ymd(new Date());
  const mesCorrente = _ymd(new Date(new Date().getFullYear(), new Date().getMonth(), 1));
  const de = r ? r.from : (_c2primeiraData() || mesCorrente);
  const ate = r ? r.to : hoje;
  const meses = _c2meses(de.slice(0, 7) + '-01', ate);
  return { de: de, ate: ate, meses: meses, mesRef: meses[meses.length - 1] || hoje.slice(0, 7) };
}

// Casas e fornecedores selecionados nos multiselects (Set vazio = todos).
function _c2sel(){
  const ca = (typeof msGet === 'function') ? msGet('ca_custos_v2') : null;
  const fo = (typeof msGet === 'function') ? msGet('fo_custos_v2') : null;
  const op = (typeof msGet === 'function') ? msGet('op_custos_v2') : null;
  return { ca: ca, fo: fo, op: op };
}
// Operador de uma CONTA. Ele nao e campo do cadastro: sai do bilhete, e quem ja o
// resolve e o `_contaVida` (gestao.js), indexado por "fornecedor||casa" -> conta.
// Reusar e obrigatorio -- derivar de novo aqui criaria uma segunda regua para a mesma
// pergunta, e as duas divergiriam no primeiro ajuste.
function _c2opDaConta(forn, casa, conta){
  if (typeof _contaVida === 'undefined' || !_contaVida) return '';
  const v = (_contaVida[forn + '||' + casa] || {})[conta || '__default__'];
  return (v && v.op) || '';
}
// `conta` e OPCIONAL, e a omissao e significativa: o eixo Operador so recorta onde a
// entidade TEM operador, que e a conta. A tabela de precos e por par
// fornecedor x casa, e preco nao pertence a operador nenhum.
function _c2passa(sel, casa, forn, conta){
  if (sel.ca && sel.ca.size && !sel.ca.has(casa)) return false;
  if (sel.fo && sel.fo.size && !sel.fo.has(forn)) return false;
  if (conta !== undefined && sel.op && sel.op.size && !sel.op.has(_c2opDaConta(forn, casa, conta))) return false;
  return true;
}

// ── Os três blocos de custo do recorte ───────────────────────────────────────

// CONTAS: comprada no período = `adquirida_em` dentro do recorte. O valor é o do
// par (fornecedor||casa), que é tudo o que existe hoje; custo POR CONTA é Fatia 2.
function _c2contas(){
  const r = _c2range(), sel = _c2sel();
  const out = [];
  (typeof _contasVida !== 'undefined' && _contasVida ? _contasVida : []).forEach(p => {
    if (!p.adquirida_em || p.adquirida_em < r.de || p.adquirida_em > r.ate) return;
    const forn = normForn(p.fornecedor);
    if (!_c2passa(sel, p.casa, forn, p.conta)) return;
    // As TRÊS camadas viajam separadas para a tela poder dizer de onde o número
    // veio. O total sai de `_custoDaConta`, que é a mesma função do KPI.
    const herdadoPar = (typeof custoData !== 'undefined' && custoData[forn + '||' + p.casa]) || 0;
    const degrau = _precoVigenteEm(_degrausPreco(forn, p.casa), p.adquirida_em);
    out.push({ id: p.id || null, casa: p.casa, conta: p.conta, forn: forn, data: p.adquirida_em,
               proprio: p.custo > 0 ? p.custo : 0,
               herdado: degrau ? degrau.valor : herdadoPar,
               degrau: degrau || null,
               custo: _custoDaConta(forn, p.casa, p.conta) });
  });
  out.sort((a, b) => (a.data === b.data ? a.casa.localeCompare(b.casa, 'pt-BR') : a.data.localeCompare(b.data)));
  return out;
}

// TIPSTERS: uma linha por tipster que existe (união de cadastro, base e custo
// lançado — `_ctTipsters`), com o valor do mês de referência e o do mês anterior.
function _c2tipsters(){
  const r = _c2range();
  const ant = _c2mesAnterior(r.mesRef);
  return (typeof _ctTipsters === 'function' ? _ctTipsters() : []).map(nome => {
    const meses = (typeof ctData !== 'undefined' && ctData[nome]) || {};
    const vRef = _c2num(meses[r.mesRef]);
    // A situação e o arrasto saem do `gestao.js`, que é onde a regra mora — a tela
    // antiga lê a mesma, e duas cópias divergiriam.
    const sit = _ctSituacao(nome, r.mesRef);
    return {
      nome: nome, valor: vRef, anterior: _c2num(meses[ant]),
      cobranca: _ctCobranca(nome), parametro: _ctParametro(nome),
      situacao: sit, resolvido: sit !== 'pendente',
      sugestao: _ctSugestao(nome, r.mesRef, ant),
      noPeriodo: r.meses.reduce((a, m) => a + _c2num(meses[m]), 0)
    };
  });
}

// GERAIS: as linhas livres do custo geral (VPN, ferramentas, taxas).
function _c2gerais(){
  const r = _c2range();
  const ant = _c2mesAnterior(r.mesRef);
  return (typeof cgData !== 'undefined' && cgData ? cgData : []).map((row, i) => {
    const vals = row.values || {};
    // A situação e o arrasto saem do `gestao.js`, que é onde a regra mora — a mesma
    // `_arrasta` do custo de tipster.
    const sit = _cgSituacao(i, r.mesRef);
    return {
      i: i, tipo: (row.tipo || '').trim(),
      categoria: _cgCategoria(i), recorrencia: _cgRecorrencia(i),
      valor: _c2num(vals[r.mesRef]), anterior: _c2num(vals[ant]),
      situacao: sit, resolvido: sit !== 'pendente',
      sugestao: _cgSugestao(i, r.mesRef, ant),
      noPeriodo: r.meses.reduce((a, m) => a + _c2num(vals[m]), 0)
    };
  });
}

// Totais do recorte + o P/L bruto que a cascata compara.
function _c2totais(){
  const contas = _c2contas(), tips = _c2tipsters(), ger = _c2gerais();
  const tContas = contas.reduce((a, c) => a + c.custo, 0);
  const tTips = tips.reduce((a, t) => a + t.noPeriodo, 0);
  const tGer = ger.reduce((a, g) => a + g.noPeriodo, 0);
  const bruto = (typeof filtrarPagina === 'function' ? filtrarPagina('custos_v2') : [])
    .reduce((a, b) => a + (b.lucro || 0), 0);
  const custo = tContas + tTips + tGer;
  return {
    contas: contas, tips: tips, ger: ger,
    tContas: tContas, tTips: tTips, tGer: tGer,
    custo: custo, bruto: bruto, liquido: bruto - custo,
    tTipsMes: tips.reduce((a, t) => a + t.valor, 0),
    tGerMes: ger.reduce((a, g) => a + g.valor, 0),
    semCusto: contas.filter(c => !(c.custo > 0)).length,
    tipsPend: tips.filter(t => t.situacao === 'pendente').length,
    gerPend: ger.filter(g => !g.resolvido).length,
    // Previsto = só o que o arrasto REALMENTE preencheria. Somar o mês anterior de
    // um staking prometeria um número que muda todo mês.
    tipsPrev: tips.filter(t => t.situacao === 'pendente').reduce((a, t) => a + t.sugestao, 0),
    tipsRepetiveis: tips.filter(t => t.situacao === 'pendente' && t.sugestao > 0).length
  };
}

// ── Barra de filtros ─────────────────────────────────────────────────────────
// Composta com as PEÇAS de filters.js, nunca reescrita: duas barras de Período na
// mesma tela divergem no primeiro ajuste (regra da s317 no CLAUDE.md). Esporte e
// Tipster ficam de fora de propósito — descrevem a APOSTA e não recortam custo.
// Fornecedores que EXISTEM, que e cadastro uniao base -- nao so quem ja apareceu num
// bilhete. Esta e uma tela de CUSTO, e conta comprada custa antes da primeira aposta:
// ler so o bilhete some justamente com o caso que a tela existe para cobrar.
// Medido na base: 26 contas ativas cadastradas sem nenhum bilhete, e 4 fornecedores
// (`Fernanda`, `amigo`, `richard`, `xxxx`) que so existem no cadastro.
// `_contasCadastro` (gestao.js) chega por fetch DEPOIS do primeiro paint, entao esta
// lista nasce so com a base e se completa no `renderCustos2`, que roda depois do
// `contasLoad()` -- ver o `msRepintar` la embaixo.
function _c2Fornecedores(){
  const _todas = DADOS.concat(typeof DADOS_ABERTAS !== 'undefined' ? DADOS_ABERTAS : []);
  const s = new Set(_todas.map(r => normForn(r.fornecedor)).filter(Boolean));
  (typeof _contasCadastro !== 'undefined' && _contasCadastro ? _contasCadastro : [])
    .forEach(c => { const f = normForn(c.fornecedor); if (f) s.add(f); });
  return [...s].sort(cmpNome);
}

function buildFiltersCustos(p, casas){
  const forns = _c2Fornecedores();
  // Operador entra ao lado de Casa porque os dois descrevem a CONTA, e e por isso que
  // os dois recortam custo (`CLAUDE.md`: Esporte e Tipster descrevem a APOSTA e ficam
  // de fora). Ate a s358 a tela aplicava metade da regra. O `_grupoOperador` so desenha
  // para quem supervisiona mais de um: dono solo nao ganha eixo nenhum.
  return `<div class="filters">
${_grupoPeriodo(p)}
    ${_grupoCasa(p, casas)}
    <div class="filter-group"><div class="filter-label">Fornecedor</div>${buildMS('fo_' + p, forns, 'Todos os fornecedores', p, '')}</div>
    ${_grupoOperador(p)}
  </div>`;
}

// O período nasce no mês corrente (MTD): a tela é de fechamento mensal e "Tudo"
// não fecha mês nenhum. Semeado antes do buildHTML, que lê gfs() para pintar a barra.
(function _c2seedPeriodo(){
  if (typeof gfs !== 'function' || typeof _ymd !== 'function') return;
  const st = gfs('custos_v2');
  if (st.df || st.dt || st.qd || st.qt) return;
  const d = new Date();
  st.qt = 'mtd';
  st.df = _ymd(new Date(d.getFullYear(), d.getMonth(), 1));
  st.dt = _ymd(d);
})();

// ── Preço do fornecedor: a régua mora no gestao.js ───────────────────────────
// `precosFornLoad`, `_degrausPreco` e `_precoVigenteEm` vivem junto do
// `_custoNaJanela`, que é a fonte canônica do custo. Uma cópia aqui venceria a de
// lá por ordem de carga e deixaria o KPI da Visão Geral sem histórico de preço,
// sem erro nenhum.
let _c2precoAberto = null;     // "fornecedor||casa" com o editor de preço aberto
let _c2precoErro = '';         // mensagem do último POST recusado (aparece no formulário)
let _c2contaEditando = null;   // id do parceiro com o custo próprio em edição
let _c2contaErro = '';
let _c2tipErro = '';       // falha ao gravar custo/cobrança de tipster
let _c2geralErro = '';     // falha ao gravar custo geral

// Abre o calendário da marca — todo campo de data usa o SharpenCal (UI_REFERENCE §4).
window.c2Cal = function(id){
  const inp = document.getElementById(id);
  if (!inp || !window.SharpenCal) return;
  SharpenCal.abrir(inp, inp.value, v => { inp.value = v; }, { saida: 'iso' });
};

window.c2PrecoToggle = function(par){
  _c2precoAberto = (_c2precoAberto === par) ? null : par;
  _c2precoErro = '';
  renderCustos2();
};

// Grava um degrau. O servidor reespelha o vigente de hoje em `custo_conta`, então
// o `custoData` local é atualizado junto: sem isso o KPI de Contas e a aba Contas
// seguiriam com o preço velho até o próximo F5.
window.c2PrecoSalvar = async function(forn, casa){
  const valor = (document.getElementById('c2pv') || {}).value || '';
  const desde = (document.getElementById('c2pd') || {}).value || '';
  const n = parseFloat(valor.toString().replace(/\./g, '').replace(',', '.'));
  if (!(n > 0)) { _c2precoErro = 'O preço tem de ser maior que zero.'; renderCustos2(); return; }
  if (!/^\d{4}-\d{2}-\d{2}$/.test(desde)) { _c2precoErro = 'Escolha a data em que este preço passou a valer.'; renderCustos2(); return; }
  try {
    const r = await fetch('/custos/fornecedor', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ fornecedor: forn, casa: casa, valor: n, vigente_desde: desde })
    });
    if (!r.ok) {
      const d = await r.json().catch(() => ({}));
      _c2precoErro = d.detail || 'Não consegui gravar o preço.';
      renderCustos2(); return;
    }
    const d = await r.json();
    if (typeof custoData !== 'undefined'){
      const k = forn + '||' + casa;
      if (d.vigente_hoje == null) delete custoData[k]; else custoData[k] = d.vigente_hoje;
    }
    _c2precoErro = '';
    await precosFornLoad(true);
    renderCustos2();
  } catch (e) { _c2precoErro = 'Falha de rede ao gravar.'; renderCustos2(); }
};

window.c2PrecoRemover = async function(id, forn, casa){
  try {
    const r = await fetch('/custos/fornecedor/' + id, { method: 'DELETE' });
    if (!r.ok) { _c2precoErro = 'Não consegui remover este degrau.'; renderCustos2(); return; }
  } catch (e) { _c2precoErro = 'Falha de rede ao remover.'; renderCustos2(); return; }
  await precosFornLoad(true);
  // o espelho pode ter mudado: o degrau anterior volta a valer, ou o par fica sem preço
  const vig = _precoVigenteEm(_degrausPreco(forn, casa), _ymd(new Date()));
  if (typeof custoData !== 'undefined'){
    const k = forn + '||' + casa;
    if (vig) custoData[k] = vig.valor; else delete custoData[k];
  }
  renderCustos2();
};

// ── Custo PRÓPRIO da conta (Fatia 2) ─────────────────────────────────────────
// Editar aqui vale SÓ para esta conta: o fornecedor não é tocado. Limpar o campo
// devolve a conta à herança — e vazio é diferente de zero, que seria conta de graça.
window.c2ContaEditar = function(id){
  _c2contaEditando = (_c2contaEditando === id) ? null : id;
  _c2contaErro = '';
  renderCustos2();
};

window.c2ContaSalvar = async function(id, limpar){
  const el = document.getElementById('c2cv');
  const bruto = limpar ? '' : ((el && el.value) || '').toString().trim();
  let custo = null;
  if (bruto){
    const n = parseFloat(bruto.replace(/\./g, '').replace(',', '.'));
    if (!(n > 0)) { _c2contaErro = 'O custo tem de ser maior que zero. Deixe vazio para herdar do fornecedor.'; renderCustos2(); return; }
    custo = n;
  }
  try {
    const r = await fetch('/parceiros/' + id + '/custo', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ custo: custo })
    });
    if (!r.ok){
      const d = await r.json().catch(() => ({}));
      _c2contaErro = d.detail || 'Não consegui gravar o custo desta conta.';
      renderCustos2(); return;
    }
  } catch (e) { _c2contaErro = 'Falha de rede ao gravar.'; renderCustos2(); return; }
  // O cadastro é a fonte de `_contasVida`; recarregá-lo refaz a janela de vida e,
  // com ela, o KPI. Sem isso a tela mostraria o valor novo e o total o antigo.
  _contasCadastro = null;
  await contasLoad();
  _contaVida = null;
  _c2contaEditando = null;
  _c2contaErro = '';
  renderCustos2();
};

// ── Custo de tipster: gravar o mês e o tipo de cobrança (Fatia 3) ────────────
window.c2CobrancaSet = async function(nome, cobranca, ate){
  const antes = (typeof ctMeta !== 'undefined' && ctMeta[nome]) ? { ...ctMeta[nome] } : null;
  const ateFinal = (ate !== undefined) ? (ate || '') : ((antes && antes.ate) || '');
  try {
    const r = await fetch('/custos/tipster/cobranca', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tipster: nome, cobranca: cobranca,
                             parametro: (antes && antes.parametro) || '',
                             ate: ateFinal })
    });
    if (!r.ok) { _c2tipErro = 'Não consegui gravar a cobrança.'; renderCustos2(); return; }
  } catch (e) { _c2tipErro = 'Falha de rede ao gravar a cobrança.'; renderCustos2(); return; }
  if (typeof ctMeta !== 'undefined'){
    if (!cobranca) delete ctMeta[nome];
    else ctMeta[nome] = Object.assign({}, antes, { cobranca: cobranca, ate: ateFinal });
  }
  _c2tipErro = '';
  renderCustos2();
};

// O valor do MÊS. Reusa o `ctSave` do app.js, que é quem fala com /custos/store —
// um segundo caminho de escrita para o mesmo blob criaria duas fontes.
window.c2CustoTipsterSalvar = function(nome, bruto){
  const txt = (bruto == null ? '' : bruto).toString().trim();
  const ym = _c2range().mesRef;
  if (typeof ctData === 'undefined') return;
  if (!ctData[nome]) ctData[nome] = {};
  if (txt){
    const n = parseFloat(txt.replace(/\./g, '').replace(',', '.'));
    if (!(n > 0)) { _c2tipErro = 'O custo do mês tem de ser maior que zero. Deixe vazio para limpar.'; renderCustos2(); return; }
    ctData[nome][ym] = txt;
  } else {
    delete ctData[nome][ym];
  }
  _c2tipErro = '';
  if (typeof ctSave === 'function') ctSave();
  renderCustos2();
};

// Aceita o valor do mês anterior em TODOS os pendentes que arrastam. Só mensalidade
// entra: `_ctSugestao` devolve 0 para staking e temporada, e o filtro é por isso.
window.c2RepetirMes = function(){
  const r = _c2range();
  const ant = _c2mesAnterior(r.mesRef);
  let n = 0;
  (_c2tipsters() || []).forEach(t => {
    if (t.situacao !== 'pendente') return;
    const v = _ctSugestao(t.nome, r.mesRef, ant);
    if (!(v > 0)) return;
    if (!ctData[t.nome]) ctData[t.nome] = {};
    ctData[t.nome][r.mesRef] = fmt(v, 2);
    n++;
  });
  if (n && typeof ctSave === 'function') ctSave();
  renderCustos2();
};

// ── Custo geral: descrição, categoria, recorrência e valor (Fatia 4) ─────────
// Tudo grava pelo `ctSave` do app.js, que é quem fala com /custos/store — um
// segundo caminho de escrita para o mesmo blob criaria duas fontes.
function _c2cgSet(i, campo, valor){
  if (typeof cgData === 'undefined' || !cgData[i]) return;
  const v = (valor == null ? '' : valor).toString().trim();
  if (v) cgData[i][campo] = v; else delete cgData[i][campo];
  if (typeof ctSave === 'function') ctSave();
}

window.c2GeralCampo = function(i, campo, valor){
  _c2cgSet(i, campo, valor);
  _c2geralErro = '';
  renderCustos2();
};

window.c2GeralValor = function(i, bruto){
  if (typeof cgData === 'undefined' || !cgData[i]) return;
  const ym = _c2range().mesRef;
  const txt = (bruto == null ? '' : bruto).toString().trim();
  if (!cgData[i].values) cgData[i].values = {};
  if (txt){
    const n = parseFloat(txt.replace(/\./g, '').replace(',', '.'));
    if (!(n > 0)) { _c2geralErro = 'O valor do mês tem de ser maior que zero. Deixe vazio para limpar.'; renderCustos2(); return; }
    cgData[i].values[ym] = txt;
  } else {
    delete cgData[i].values[ym];
  }
  _c2geralErro = '';
  if (typeof ctSave === 'function') ctSave();
  renderCustos2();
};

window.c2GeralAdd = function(){
  if (typeof cgData === 'undefined') return;
  // Nasce SEM categoria e SEM recorrência de propósito: um default ("mensal")
  // faria a linha começar a arrastar sozinha um valor que ninguém classificou.
  cgData.push({ id: Date.now(), tipo: '', values: {} });
  if (typeof ctSave === 'function') ctSave();
  renderCustos2();
  // foca a descrição da linha nova, que é o único campo obrigatório na prática
  setTimeout(() => { const el = document.getElementById('c2cg-desc-' + (cgData.length - 1)); if (el) el.focus(); }, 0);
};

// Apagar uma linha leva os meses dela junto, então passa pela confirmação da marca
// — e ela diz quanto está sendo apagado, que é o que o dono precisa para decidir.
window.c2GeralRemover = async function(i){
  if (typeof cgData === 'undefined' || !cgData[i]) return;
  const linha = cgData[i];
  const nome = (linha.tipo || '').trim() || 'esta linha sem descrição';
  const total = Object.values(linha.values || {}).reduce((a, v) => a + _c2num(v), 0);
  const meses = Object.keys(linha.values || {}).filter(m => _c2num(linha.values[m]) > 0).length;
  const corpo = meses
    ? `Isto apaga <b>${esc(nome)}</b> e os <b>${meses} ${meses === 1 ? 'mês' : 'meses'}</b> lançados nela, somando ${fmtR(total)}.`
    : `Isto apaga <b>${esc(nome)}</b>. Ela ainda não tem valor lançado.`;
  if (typeof shConfirm !== 'function'){ return; }
  const ok = await shConfirm({ eyebrow: 'REMOVER CUSTO GERAL', titulo: nome,
                               corpo: corpo, acao: 'Remover', perigo: true });
  if (ok === null) return;
  cgData.splice(i, 1);
  if (typeof ctSave === 'function') ctSave();
  renderCustos2();
};

// ── Render ───────────────────────────────────────────────────────────────────

window.c2Tab = function(aba){ _c2aba = aba; renderCustos2(); };
window.c2FornToggle = function(forn){ _c2fornOpen = (_c2fornOpen === forn) ? null : forn; renderCustos2(); };
// nome dentro de onclick="…('…')" — escapa \ e ', como o _tmJs de gestao.js
function _c2js(x){ return String(x).replace(/\\/g, '\\\\').replace(/'/g, "\\'"); }

function renderCustos2(){
  const host = document.getElementById('c2Body');
  if (!host) return;
  // O cadastro de contas so chega aqui (o `contasLoad()` do renderPage). E o unico ponto
  // em que o seletor de Fornecedor pode ganhar quem foi comprado e ainda nao apostou.
  // `msRepintar` preserva a selecao e a busca digitada, entao repintar sempre e barato.
  if (typeof msRepintar === 'function') msRepintar('fo_custos_v2', _c2Fornecedores());
  const r = _c2range(), t = _c2totais();
  const mes = _c2mesRotulo(r.mesRef);
  const umMes = r.meses.length === 1;
  const rotuloPeriodo = umMes ? mes : (_c2mesRotulo(r.meses[0]) + ' a ' + mes);

  // ── KPIs ──
  const pend = (n) => n > 0
    ? `<span class="c2-badge c2-badge--wait">${n === 1 ? 'Falta 1' : 'Faltam ' + n}</span>`
    : `<span class="c2-badge c2-badge--ok">Completo</span>`;
  const mkK = (label, valor, sub, extra, hero) => `<div class="kpi${hero ? ' hero' : ''}">
      <div class="kpi-label"><span class="kpi-pipe"></span> ${label}</div>
      <div class="kpi-val neu">${valor}</div>
      <div class="kpi-sub c2-kpi-sub">${sub}${extra || ''}</div>
    </div>`;
  const blocosFechados = [t.semCusto === 0, t.tipsPend === 0, t.gerPend === 0].filter(Boolean).length;
  const previsto = t.custo + t.tipsPrev;
  document.getElementById('c2Kpi').innerHTML = `<div class="kpi-grid" style="margin-bottom:var(--sp-3)">
    ${mkK('Total de ' + rotuloPeriodo, fmtR(t.custo),
        `${blocosFechados} de 3 blocos fechados`,
        t.tipsPrev > 0 ? ` · previsto ${fmtR(previsto)}` : '', true)}
    ${mkK('Contas', fmtR(t.tContas),
        `${t.contas.length} ${t.contas.length === 1 ? 'conta comprada' : 'contas compradas'}`, pend(t.semCusto))}
    ${mkK('Tipsters', fmtR(t.tTips),
        `${t.tips.length - t.tipsPend} de ${t.tips.length} resolvidos`, pend(t.tipsPend))}
    ${mkK('Gerais', fmtR(t.tGer),
        `${t.ger.length - t.gerPend} de ${t.ger.length} confirmados`, pend(t.gerPend))}
  </div>`;

  // ── Cascata em fita: o bruto é a barra inteira e o custo come dela ──
  const base = t.bruto > 0 ? t.bruto : (t.custo || 1);
  const pct = (v) => Math.max(0, Math.min(100, (v / base) * 100));
  const pLiq = t.bruto > 0 ? pct(t.liquido) : 0;
  // Custo e AGREGADO (fmtR, inteiro e sem sinal); P/L e P/L (fmtPL, 2 casas, sinal
  // colado e minus U+2212). Sao mascaras diferentes por PAPEL, nao por estilo:
  // com fmtR um liquido negativo sai como se fosse lucro. UI_REFERENCE 5.1.
  const legenda = (cor, nome, valor) => `<div class="c2-leg"><span class="c2-leg__dot" style="background:${cor}"></span><span class="c2-leg__lbl">${nome}</span><span class="c2-leg__val">${fmtR(valor)}</span></div>`;
  const legendaPL = (cor, nome, valor) => `<div class="c2-leg">${cor ? `<span class="c2-leg__dot" style="background:${cor}"></span>` : ''}<span class="c2-leg__lbl">${nome}</span><span class="c2-leg__val">${fmtPL(valor)}</span></div>`;
  document.getElementById('c2Cascata').innerHTML = `<div class="card c2-cascata">
    <div class="c2-cascata__hdr">
      <span class="c2-eyebrow">Do bruto ao líquido · ${rotuloPeriodo}</span>
      <span class="c2-meta">${t.bruto > 0 ? 'o custo levou ' + fmtPct(t.custo / t.bruto * 100, 1, false) + ' do bruto' : 'sem P/L no recorte'}</span>
    </div>
    <div class="c2-fita">
      <div class="c2-fita__seg" style="width:${pLiq}%;background:var(--pos)"></div>
      <div class="c2-fita__seg" style="width:${pct(t.tContas)}%;background:var(--accent)"></div>
      <div class="c2-fita__seg" style="width:${pct(t.tTips)}%;background:rgba(var(--accent-rgb),.68)"></div>
      <div class="c2-fita__seg" style="width:${pct(t.tGer)}%;background:rgba(var(--accent-rgb),.40)"></div>
    </div>
    <div class="c2-legs">
      ${legendaPL('var(--pos)', 'P/L Líquido', t.liquido)}
      ${legenda('var(--accent)', 'Contas', t.tContas)}
      ${legenda('rgba(var(--accent-rgb),.68)', 'Tipsters', t.tTips)}
      ${legenda('rgba(var(--accent-rgb),.40)', 'Gerais', t.tGer)}
      <div class="c2-leg c2-leg--fim"><span class="c2-leg__lbl">P/L Bruto</span><span class="c2-leg__val">${fmtPL(t.bruto)}</span></div>
    </div>
    <div class="c2-corte">Custo <strong>lançado</strong> no recorte, ou seja, conta comprada aqui dentro. A Visão Geral mede pela <strong>janela de vida</strong> e cobra toda conta viva no período: os dois números são diferentes de propósito.</div>
  </div>`;

  // ── Aviso do que falta, e de qual mês ──
  const faltam = t.semCusto + t.tipsPend + t.gerPend;
  document.getElementById('c2Aviso').innerHTML = faltam === 0
    ? `<div class="c2-aviso c2-aviso--ok">
        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="var(--pos)" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>
        <div class="c2-aviso__txt"><strong>${rotuloPeriodo} está fechado.</strong> Nenhum lançamento em aberto no recorte.</div>
      </div>`
    : `<div class="c2-aviso">
        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="var(--warn)" stroke-width="1.6" stroke-linecap="round"><path d="M12 8.5v5M12 16.6v.4"/><path d="M10.3 3.9L2.6 17.4A2 2 0 004.3 20.4h15.4a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z"/></svg>
        <div class="c2-aviso__txt">
          <strong>${faltam} ${faltam === 1 ? 'lançamento em aberto' : 'lançamentos em aberto'} em ${rotuloPeriodo}</strong>
          <span>${[t.semCusto ? t.semCusto + ' conta' + (t.semCusto > 1 ? 's' : '') + ' sem custo' : '',
                   t.tipsPend ? t.tipsPend + ' tipster' + (t.tipsPend > 1 ? 's' : '') : '',
                   t.gerPend ? t.gerPend + ' geral' + (t.gerPend > 1 ? 'is' : '') : ''].filter(Boolean).join(' · ')}. Enquanto não fecha, o líquido acima está otimista.</span>
        </div>
      </div>`;

  // ── Abas ──
  const abas = [
    ['contas', 'Contas', t.contas.length],
    ['tipsters', 'Tipsters', t.tips.length],
    ['gerais', 'Gerais', t.ger.length],
    ['raiox', 'Raio-X', null]
  ];
  document.getElementById('c2Tabs').innerHTML = `<div class="c2-tabs">${abas.map(([id, lbl, n]) =>
    `<button class="c2-tab${_c2aba === id ? ' is-on' : ''}" onclick="c2Tab('${id}')">${lbl}${n === null ? '' : `<span class="c2-tab__ct">${n}</span>`}</button>`
  ).join('')}</div>`;

  // ── Corpo da aba ──
  if (_c2aba === 'contas') host.innerHTML = _c2viewContas(t, rotuloPeriodo);
  else if (_c2aba === 'tipsters') host.innerHTML = _c2viewTipsters(t, mes, _c2mesRotulo(_c2mesAnterior(r.mesRef)), umMes, rotuloPeriodo);
  else if (_c2aba === 'gerais') host.innerHTML = _c2viewGerais(t, mes, _c2mesRotulo(_c2mesAnterior(r.mesRef)), umMes, rotuloPeriodo);
  else host.innerHTML = _c2viewRaioX(t, r, rotuloPeriodo);
}

// ── Aba Contas ───────────────────────────────────────────────────────────────
// Ordem das colunas cravada pelo Feca: Casa · Conta · Fornecedor · Lançamento ·
// Origem do valor · Valor.
function _c2viewContas(t, rotulo){
  if (!t.contas.length){
    return _c2card('Contas compradas em ' + rotulo, 'custo \u00fanico, pago na compra',
      _c2vazio('Nenhuma conta comprada neste recorte. O cadastro guarda a data de compra em <strong>Comprada em</strong>, no Painel de Contas.'))
      + _c2viewPrecos();
  }
  const linhas = t.contas.map(c => {
    const temCusto = c.custo > 0;
    const editando = c.id && _c2contaEditando === c.id;
    // A origem é derivada da MESMA cadeia que define o custo (`_custoDaConta`), nunca
    // de um flag à parte: flag e valor divergem no primeiro caso de borda.
    let origem, extra = '';
    if (c.proprio > 0){
      origem = '<span class="c2-orig c2-orig--edit">editado nesta conta</span>';
      if (c.herdado > 0) extra = `<span class="c2-dt">fornecedor ${fmtR(c.herdado)}</span>`;
    } else if (c.degrau){
      origem = '<span class="c2-orig">tabela do fornecedor</span>';
      extra = `<span class="c2-dt">desde ${_c2dataBR(c.degrau.vigente_desde)}</span>`;
    } else if (temCusto){
      origem = '<span class="c2-orig">tabela do fornecedor</span>';
      extra = '<span class="c2-dt">sem data</span>';
    } else {
      origem = '<span class="c2-orig c2-orig--todo">sem pre\u00e7o lan\u00e7ado</span>';
    }
    return `<tr>
      <td class="th-l">${casaCell(c.casa)}</td>
      <td class="th-l c2-ident">${esc(c.conta)}</td>
      <td class="th-l c2-ident">${esc(c.forn)}</td>
      <td class="th-l c2-dt">${_c2dataBR(c.data)}</td>
      <td class="th-l">${origem}${extra ? ' ' + extra : ''}</td>
      <td class="td-num">${temCusto ? fmtR(c.custo) : '<span class="c2-vazio-cel">\u2014</span>'}</td>
      <td class="td-num">${c.id
        ? `<button class="c2-preco__btn${editando ? ' is-on' : ''}" onclick="c2ContaEditar(${c.id})">${editando ? 'Fechar' : 'Editar'}</button>`
        : '<span class="c2-vazio-cel" title="Conta que s\u00f3 existe em bilhete, sem cadastro">\u2014</span>'}</td>
    </tr>${editando ? `<tr><td colspan="7" class="c2-conta-edit">${_c2contaEditor(c)}</td></tr>` : ''}`;
  }).join('');

  const proprios = t.contas.filter(c => c.proprio > 0).length;
  const corpo = `<div class="tbl-wrap"><table class="tbl c2-tbl">
      <thead><tr>
        <th class="th-l">Casa</th><th class="th-l">Conta</th><th class="th-l">Fornecedor</th>
        <th class="th-l">Lan\u00e7amento</th><th class="th-l">Origem do valor</th>
        <th class="td-num">Valor</th><th class="td-num"></th>
      </tr></thead>
      <tbody>${linhas}</tbody>
    </table></div>
    <div class="c2-rodape">
      <span class="c2-meta">${t.contas.length} ${t.contas.length === 1 ? 'conta' : 'contas'} no recorte${t.semCusto ? ' \u00b7 ' + t.semCusto + ' sem pre\u00e7o' : ''}${proprios ? ' \u00b7 ' + proprios + ' com custo pr\u00f3prio' : ''}</span>
      <span class="c2-total">${fmtR(t.tContas)}</span>
    </div>`;
  return _c2card('Contas compradas em ' + rotulo, 'custo \u00fanico, pago na compra', corpo) + _c2viewPrecos();
}

// Editor do custo de UMA conta. O texto diz o que o campo vazio faz, porque
// "limpar para herdar" não é adivinhável.
function _c2contaEditor(c){
  const herdado = c.herdado > 0
    ? `<span class="c2-meta">Sem valor pr\u00f3prio, esta conta herda ${fmtR(c.herdado)} do fornecedor${c.degrau ? ' (desde ' + _c2dataBR(c.degrau.vigente_desde) + ')' : ''}.</span>`
    : '<span class="c2-meta">O fornecedor ainda n\u00e3o tem pre\u00e7o para esta casa.</span>';
  return `<div class="c2-preco__editor">
    <div class="c2-preco__form">
      <label class="c2-preco__campo">
        <span class="c2-eyebrow">Custo desta conta</span>
        <span class="c2-preco__inp"><span class="cur">R$</span><input id="c2cv" type="text" inputmode="decimal" placeholder="0,00" value="${c.proprio > 0 ? fmt(c.proprio, 2) : ''}" autocomplete="off"></span>
      </label>
      <button class="c2-preco__ok" onclick="c2ContaSalvar(${c.id}, false)">Salvar</button>
      ${c.proprio > 0 ? `<button class="c2-preco__btn" onclick="c2ContaSalvar(${c.id}, true)">Voltar a herdar</button>` : ''}
    </div>
    ${_c2contaErro ? `<div class="c2-preco__erro">${esc(_c2contaErro)}</div>` : ''}
    <div class="c2-preco__hist">${herdado} <span class="c2-meta">Mudar aqui vale <strong>s\u00f3 para esta conta</strong>; o fornecedor n\u00e3o \u00e9 tocado.</span></div>
  </div>`;
}

// ── Aba Tipsters ─────────────────────────────────────────────────────────────
function _c2precos(){
  const sel = _c2sel();
  const contas = {};   // "forn||casa" -> Set(conta)
  const _add = (forn, casa, conta) => {
    if (!casa) return;
    const f = normForn(forn);
    // A CONTAGEM de contas do par tem de obedecer o recorte de Operador, senao a coluna
    // "n contas" contaria conta que o filtro acabou de tirar da tela de cima.
    if (!_c2passa(sel, casa, f, conta)) return;
    (contas[f + '||' + casa] = contas[f + '||' + casa] || new Set()).add(conta || '__sem_nome__');
  };
  (typeof _contasVida !== 'undefined' && _contasVida ? _contasVida : [])
    .forEach(p => { if (!p.arquivado) _add(p.fornecedor, p.casa, p.conta); });
  DADOS.concat(typeof DADOS_ABERTAS !== 'undefined' ? DADOS_ABERTAS : [])
    .forEach(r => _add(r.fornecedor, r.casa, r.conta));

  // Universo = par com preco lancado OU par com conta viva. Os dois lados importam:
  // preco sem conta e resto de conta que saiu, conta sem preco e o que falta lancar.
  const chaves = new Set(Object.keys(contas));
  Object.keys(typeof custoData !== 'undefined' ? custoData : {}).forEach(k => chaves.add(k));

  const linhas = [];
  chaves.forEach(k => {
    const i = k.indexOf('||');
    const forn = k.slice(0, i), casa = k.slice(i + 2);
    if (!_c2passa(sel, casa, forn)) return;
    // O preço com data manda; o do `custoData` é o herdado, que ainda não tem
    // vigência. Os dois convivem até o dono registrar o primeiro degrau.
    const vig = _precoVigenteEm(_degrausPreco(forn, casa), _ymd(new Date()));
    const preco = vig ? vig.valor : ((typeof custoData !== 'undefined' && custoData[k]) || 0);
    const n = contas[k] ? contas[k].size : 0;
    linhas.push({ forn: forn, casa: casa, preco: preco, n: n });
  });
  // Dentro do fornecedor a ordem e pelo PRECO, que e o que a tela mostra. Ordenar
  // por `preco x contas` faria o total recusado pelo Feca voltar como criterio.
  linhas.sort((a, b) => a.forn === b.forn
    ? b.preco - a.preco || a.casa.localeCompare(b.casa, 'pt-BR')
    : a.forn.localeCompare(b.forn, 'pt-BR'));
  return linhas;
}

function _c2viewPrecos(){
  const linhas = _c2precos();
  if (!linhas.length){
    return _c2card('Tabela de pre\u00e7os por fornecedor', 'o pre\u00e7o que vale hoje',
      _c2vazio('Nenhum pre\u00e7o lan\u00e7ado e nenhuma conta viva.'));
  }
  const hoje = _ymd(new Date());

  const porForn = [];
  const idx = {};
  linhas.forEach(l => {
    if (idx[l.forn] === undefined){ idx[l.forn] = porForn.length; porForn.push({ forn: l.forn, casas: [] }); }
    porForn[idx[l.forn]].casas.push(l);
  });

  const boxes = porForn.map(g => {
    const aberto = _c2fornOpen === g.forn;
    const semPreco = g.casas.filter(c => !(c.preco > 0) && c.n > 0).length;
    const nContas = g.casas.reduce((a, c) => a + c.n, 0);
    const selo = semPreco
      ? `<span class="c2-badge c2-badge--wait">${semPreco === 1 ? 'falta 1 pre\u00e7o' : 'faltam ' + semPreco + ' pre\u00e7os'}</span>`
      : `<span class="c2-badge c2-badge--ok">Completo</span>`;
    const corpo = aberto ? `<div class="c2-acc__body">${g.casas.map(c => {
      const par = c.forn + '||' + c.casa;
      const degraus = _degrausPreco(c.forn, c.casa);
      const vig = _precoVigenteEm(degraus, hoje);
      const editando = _c2precoAberto === par;
      // "desde" só aparece quando existe degrau: preço herdado do custo_conta não
      // tem data, e inventar uma seria dado derivado por estimativa.
      const desde = vig
        ? `<span class="c2-dt">desde ${_c2dataBR(vig.vigente_desde)}</span>`
        : (c.preco > 0 ? '<span class="c2-dt">sem data</span>' : '');
      return `<div class="c2-preco">
        <div class="c2-acc__linha">
          <span class="c2-acc__casa">${casaCell(c.casa)}</span>
          ${desde}
          <span class="c2-acc__preco">${c.preco > 0 ? fmtR(c.preco) : '<span class="c2-orig c2-orig--todo">sem pre\u00e7o</span>'}</span>
          <button class="c2-preco__btn${editando ? ' is-on' : ''}" onclick="c2PrecoToggle('${_c2js(par)}')" title="Registrar um pre\u00e7o novo a partir de uma data">${editando ? 'Fechar' : 'Novo pre\u00e7o'}</button>
        </div>
        ${editando ? _c2precoEditor(c.forn, c.casa, degraus, hoje) : ''}
      </div>`;
    }).join('')}</div>` : '';
    return `<div class="c2-acc${aberto ? ' is-open' : ''}">
      <div class="c2-acc__head" onclick="c2FornToggle('${_c2js(g.forn)}')">
        <span class="c2-acc__caret">\u25b8</span>
        <span class="c2-acc__nome">${esc(g.forn)}</span>
        <span class="c2-acc__dir">
          <span class="c2-acc__selo">${selo}</span>
          <span class="c2-acc__meta">${g.casas.length} ${g.casas.length === 1 ? 'casa' : 'casas'} \u00b7 ${nContas} ${nContas === 1 ? 'conta' : 'contas'}</span>
        </span>
      </div>${corpo}
    </div>`;
  }).join('');

  const totalSem = linhas.filter(l => !(l.preco > 0) && l.n > 0).length;
  const corpo = `<div class="c2-nota">Esta tabela <strong>n\u00e3o \u00e9 do recorte</strong>: ela mostra o pre\u00e7o que vale hoje, enquanto a lista acima mostra as compras do per\u00edodo. \u00c9 s\u00f3 o <strong>lugar do pre\u00e7o</strong>, sem total: hoje ele vale para o <strong>par fornecedor e casa</strong>, e a partir da Fatia 2 cada conta pode ter o seu. <strong>Pre\u00e7o novo n\u00e3o \u00e9 retroativo</strong>: quem foi comprado antes mant\u00e9m o que custou.</div>
    ${boxes}
    <div class="c2-rodape">
      <span class="c2-meta">${porForn.length} ${porForn.length === 1 ? 'fornecedor' : 'fornecedores'} \u00b7 ${linhas.length} ${linhas.length === 1 ? 'casa' : 'casas'}</span>
      ${totalSem ? `<span class="c2-prev">${totalSem} sem pre\u00e7o lan\u00e7ado</span>` : '<span class="c2-meta">todos com pre\u00e7o</span>'}
    </div>`;
  return _c2card('Tabela de pre\u00e7os por fornecedor', 'o pre\u00e7o que vale hoje', corpo);
}

// Editor de um par: o formulário de um degrau novo e o histórico do que já houve.
function _c2precoEditor(forn, casa, degraus, hoje){
  // O selo sai da MESMA régua que decide o preço da tela (`_precoVigenteEm`): o
  // último degrau que já começou. Derivar de "tem alguém depois de mim na lista"
  // marca o vigente como encerrado assim que existe um preço AGENDADO — medido.
  const atual = _precoVigenteEm(degraus, hoje);
  const hist = degraus.map((p, k) => {
    const proximo = degraus[k - 1];   // degraus vêm do mais novo para o mais velho
    const ate = proximo ? _c2dataBR(_c2diaAntes(proximo.vigente_desde)) : null;
    const vigente = !!atual && atual.id === p.id;
    const futuro = p.vigente_desde > hoje;
    return `<div class="c2-degrau">
      <span class="c2-degrau__val">${fmtR(p.valor)}</span>
      <span class="c2-degrau__per">${ate
        ? 'de ' + _c2dataBR(p.vigente_desde) + ' a ' + ate
        : (futuro ? 'a partir de ' + _c2dataBR(p.vigente_desde) : 'desde ' + _c2dataBR(p.vigente_desde))}</span>
      ${vigente ? '<span class="c2-badge c2-badge--ok">Vigente</span>' : (futuro ? '<span class="c2-badge c2-badge--wait">Futuro</span>' : '<span class="c2-badge">Encerrado</span>')}
      <button class="c2-degrau__x" onclick="c2PrecoRemover(${p.id},'${_c2js(forn)}','${_c2js(casa)}')" title="Remover este registro">\u2715</button>
    </div>`;
  }).join('') || '<div class="c2-meta" style="padding:6px 0">Nenhum degrau com data ainda. O primeiro que voc\u00ea registrar come\u00e7a o hist\u00f3rico.</div>';

  return `<div class="c2-preco__editor">
    <div class="c2-preco__form">
      <label class="c2-preco__campo">
        <span class="c2-eyebrow">Pre\u00e7o por conta</span>
        <span class="c2-preco__inp"><span class="cur">R$</span><input id="c2pv" type="text" inputmode="decimal" placeholder="0,00" autocomplete="off"></span>
      </label>
      <label class="c2-preco__campo">
        <span class="c2-eyebrow">Passa a valer em</span>
        <span class="shcal-datewrap c2-preco__data"><input id="c2pd" type="date" value="${hoje}"><button type="button" class="shcal-databtn" onclick="c2Cal('c2pd')" aria-label="Abrir calend\u00e1rio"><svg width="13" height="13" viewBox="0 0 15 15" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"><rect x="1.5" y="2.5" width="12" height="11" rx="2"/><path d="M1.5 6.5h12M4.5 1v3M10.5 1v3"/></svg></button></span>
      </label>
      <button class="c2-preco__ok" onclick="c2PrecoSalvar('${_c2js(forn)}','${_c2js(casa)}')">Registrar</button>
    </div>
    ${_c2precoErro ? `<div class="c2-preco__erro">${esc(_c2precoErro)}</div>` : ''}
    <div class="c2-preco__hist">${hist}</div>
  </div>`;
}

// Véspera de uma data ISO, para fechar o período do degrau anterior.
function _c2diaAntes(iso){
  const d = new Date(iso + 'T12:00:00');
  d.setDate(d.getDate() - 1);
  return _ymd(d);
}

// ── Aba Tipsters ─────────────────────────────────────────────────────────────

function _c2viewTipsters(t, mes, mesAnt, umMes, rotuloPeriodo){
  if (!t.tips.length){
    return _c2card('Tipsters em ' + mes, 'assinatura, staking ou temporada',
      _c2vazio('Nenhum tipster na base ainda.'));
  }
  const COBRANCAS = [
    ['', 'a definir'],
    ['mensalidade', 'Mensalidade'],
    ['staking', 'Staking'],
    ['temporada', 'Temporada'],
    ['sem_cobranca', 'Sem cobran\u00e7a'],
  ];
  const selo = {
    confirmado: '<span class="c2-badge c2-badge--ok">Confirmado</span>',
    coberto: '<span class="c2-badge c2-badge--ok">Coberto</span>',
    sem_custo: '<span class="c2-badge">Sem custo</span>',
    pendente: '<span class="c2-badge c2-badge--wait">Pendente</span>',
  };

  const linhas = t.tips.map(x => {
    const sel = `<select class="c2-sel" onchange="c2CobrancaSet('${_c2js(x.nome)}', this.value)">${
      COBRANCAS.map(([v, r]) => `<option value="${v}"${x.cobranca === v ? ' selected' : ''}>${r}</option>`).join('')
    }</select>${x.cobranca === 'temporada'
      ? `<input class="c2-ate" type="month" value="${esc(_ctTemporadaAte(x.nome))}" title="Cobre at\u00e9 que m\u00eas" onchange="c2CobrancaSet('${_c2js(x.nome)}', 'temporada', this.value)">`
      : (x.parametro ? `<span class="c2-dt"> ${esc(x.parametro)}</span>` : '')}`;
    // A coluna do mês anterior muda de PAPEL por tipo: na mensalidade ela é uma
    // oferta clicável; no staking é só referência, e dizer isso é o ponto.
    const ref = x.situacao === 'pendente' && x.sugestao > 0
      ? `<button class="c2-usar" onclick="c2CustoTipsterSalvar('${_c2js(x.nome)}', '${fmt(x.sugestao, 2)}')">usar ${fmtR(x.sugestao)}</button>`
      : (x.anterior > 0
          ? `<span class="c2-ref-val">${fmtR(x.anterior)}${x.cobranca === 'staking' ? '<span class="c2-dt"> · n\u00e3o repete</span>' : ''}</span>`
          : '<span class="c2-vazio-cel">\u2014</span>');
    const campo = x.situacao === 'coberto' || x.situacao === 'sem_custo'
      ? '<span class="c2-vazio-cel">\u2014</span>'
      : `<span class="c2-preco__inp c2-inp-mes${x.valor > 0 ? ' is-ok' : ''}"><span class="cur">R$</span><input type="text" inputmode="decimal" placeholder="0,00" value="${x.valor > 0 ? fmt(x.valor, 2) : ''}" onblur="c2CustoTipsterSalvar('${_c2js(x.nome)}', this.value)" onkeydown="if(event.key==='Enter')this.blur()"></span>`;
    return `<tr>
      <td class="th-l c2-ident">${esc(x.nome)}</td>
      <td class="th-l">${sel}</td>
      <td class="td-num">${ref}</td>
      <td class="td-num">${campo}</td>
      <td class="th-l">${selo[x.situacao] || selo.pendente}</td>
    </tr>`;
  }).join('');

  const corpo = `<div class="c2-nota">${umMes ? '' : `O recorte \u00e9 <strong>${rotuloPeriodo}</strong>, mas a lista abaixo \u00e9 de <strong>${mes}</strong>: assinatura se lan\u00e7a m\u00eas a m\u00eas. O KPI l\u00e1 em cima soma o per\u00edodo inteiro. `}<strong>Mensalidade</strong> traz o valor do m\u00eas anterior para voc\u00ea aceitar num clique. <strong>Staking</strong> nunca se arrasta, porque o valor muda todo m\u00eas. <strong>Temporada</strong> j\u00e1 foi paga e n\u00e3o pede nada at\u00e9 vencer.</div>
    ${_c2tipErro ? `<div class="c2-preco__erro">${esc(_c2tipErro)}</div>` : ''}
    <div class="tbl-wrap"><table class="tbl c2-tbl">
      <thead><tr>
        <th class="th-l">Tipster</th><th class="th-l">Cobran\u00e7a</th>
        <th class="td-num">${mesAnt}</th><th class="td-num">Custo de ${mes}</th><th class="th-l">Situa\u00e7\u00e3o</th>
      </tr></thead>
      <tbody>${linhas}</tbody>
    </table></div>
    <div class="c2-rodape">
      <span class="c2-meta">confirmado em ${mes} <span class="c2-total">${fmtR(t.tTipsMes)}</span>${umMes ? '' : ` \u00b7 ${rotuloPeriodo} soma <span class="c2-total">${fmtR(t.tTips)}</span>`}</span>
      ${t.tipsPrev > 0 ? `<span class="c2-prev">+ ${fmtR(t.tipsPrev)} previsto nos ${t.tipsRepetiveis} que repetem</span>` : ''}
    </div>`;

  const acao = t.tipsRepetiveis > 0
    ? `<button class="c2-preco__ok" onclick="c2RepetirMes()">Repetir ${mesAnt} nos ${t.tipsRepetiveis}</button>`
    : `<span class="c2-eyebrow">${t.tips.length - t.tipsPend} de ${t.tips.length} resolvidos</span>`;
  return `<div class="card">
    <div class="card-hdr"><div class="card-title">Tipsters em ${mes}</div>${acao}</div>
    <div class="card-body">${corpo}</div>
  </div>`;
}

// ── Aba Gerais ───────────────────────────────────────────────────────────────
function _c2viewGerais(t, mes, mesAnt, umMes, rotuloPeriodo){
  const cats = _cgCategorias();
  const RECORRENCIAS = [
    ['', 'a definir'],
    ['mensal', 'Mensal'],
    ['variavel', 'Vari\u00e1vel'],
    ['avulso', 'Avulso'],
  ];
  const listaCats = `<datalist id="c2cats">${cats.map(c => `<option value="${esc(c)}"></option>`).join('')}</datalist>`;

  const linhas = t.ger.map(g => {
    const ref = g.situacao === 'pendente' && g.sugestao > 0
      ? `<button class="c2-usar" onclick="c2GeralValor(${g.i}, '${fmt(g.sugestao, 2)}')">usar ${fmtR(g.sugestao)}</button>`
      : (g.anterior > 0
          ? `<span class="c2-ref-val">${fmtR(g.anterior)}${_arrasta(g.recorrencia) ? '' : '<span class="c2-dt"> · n\u00e3o repete</span>'}</span>`
          : '<span class="c2-vazio-cel">\u2014</span>');
    return `<tr>
      <td class="th-l"><input id="c2cg-desc-${g.i}" class="c2-inp-txt" type="text" value="${esc(g.tipo)}" placeholder="Descri\u00e7\u00e3o do custo" onblur="c2GeralCampo(${g.i}, 'tipo', this.value)" onkeydown="if(event.key==='Enter')this.blur()"></td>
      <td class="th-l"><input class="c2-inp-txt c2-inp-cat${g.categoria && !_cgEhDeFabrica(g.categoria) ? ' is-propria' : ''}" type="text" list="c2cats" value="${esc(g.categoria)}" placeholder="a definir" onchange="c2GeralCampo(${g.i}, 'categoria', this.value)"></td>
      <td class="th-l"><select class="c2-sel" onchange="c2GeralCampo(${g.i}, 'recorrencia', this.value)">${
        RECORRENCIAS.map(([v, r]) => `<option value="${v}"${g.recorrencia === v ? ' selected' : ''}>${r}</option>`).join('')
      }</select></td>
      <td class="td-num">${ref}</td>
      <td class="td-num"><span class="c2-preco__inp c2-inp-mes${g.valor > 0 ? ' is-ok' : ''}"><span class="cur">R$</span><input type="text" inputmode="decimal" placeholder="0,00" value="${g.valor > 0 ? fmt(g.valor, 2) : ''}" onblur="c2GeralValor(${g.i}, this.value)" onkeydown="if(event.key==='Enter')this.blur()"></span></td>
      <td class="th-l">${g.situacao === 'confirmado'
        ? '<span class="c2-badge c2-badge--ok">Confirmado</span>'
        : '<span class="c2-badge c2-badge--wait">Pendente</span>'}</td>
      <td class="td-num"><button class="c2-lixo" title="Remover esta linha" onclick="c2GeralRemover(${g.i})">\u2715</button></td>
    </tr>`;
  }).join('');

  const proprias = cats.filter(c => !_cgEhDeFabrica(c));
  const corpo = `<div class="c2-nota">${umMes ? '' : `O recorte \u00e9 <strong>${rotuloPeriodo}</strong>, mas a lista abaixo \u00e9 de <strong>${mes}</strong>. O KPI l\u00e1 em cima soma o per\u00edodo inteiro. `}Tudo o que a opera\u00e7\u00e3o paga e n\u00e3o \u00e9 conta nem tipster. <strong>Mensal</strong> traz o valor do m\u00eas anterior num clique; <strong>vari\u00e1vel</strong> e <strong>avulso</strong> nunca repetem.</div>
    ${_c2geralErro ? `<div class="c2-preco__erro">${esc(_c2geralErro)}</div>` : ''}
    ${listaCats}
    ${t.ger.length ? `<div class="tbl-wrap"><table class="tbl c2-tbl">
      <thead><tr>
        <th class="th-l">Descri\u00e7\u00e3o</th><th class="th-l">Categoria</th><th class="th-l">Recorr\u00eancia</th>
        <th class="td-num">${mesAnt}</th><th class="td-num">Custo de ${mes}</th>
        <th class="th-l">Situa\u00e7\u00e3o</th><th class="td-num"></th>
      </tr></thead>
      <tbody>${linhas}</tbody>
    </table></div>` : _c2vazio('Nenhum custo geral ainda. Use <strong>Adicionar custo</strong> para lan\u00e7ar VPN, servidor, ferramenta ou taxa.')}
    <div class="c2-cats">
      <span class="c2-meta">De f\u00e1brica: ${CG_CATEGORIAS_BASE.join(' \u00b7 ')}</span>
      ${proprias.length ? `<span class="c2-meta c2-cats__suas">Suas: ${esc(proprias.join(' \u00b7 '))}</span>` : '<span class="c2-meta">Digite um nome novo na coluna Categoria para criar a sua.</span>'}
    </div>
    <div class="c2-rodape">
      <span class="c2-meta">confirmado em ${mes} <span class="c2-total">${fmtR(t.tGerMes)}</span>${umMes ? '' : ` \u00b7 ${rotuloPeriodo} soma <span class="c2-total">${fmtR(t.tGer)}</span>`}</span>
      ${t.gerPend ? `<span class="c2-prev">${t.gerPend} pendente${t.gerPend > 1 ? 's' : ''}</span>` : ''}
    </div>`;

  return `<div class="card">
    <div class="card-hdr"><div class="card-title">Custos gerais em ${mes}</div>
      <button class="c2-preco__ok" onclick="c2GeralAdd()">+ Adicionar custo</button></div>
    <div class="card-body">${corpo}</div>
  </div>`;
}

// ── Aba Raio-X ───────────────────────────────────────────────────────────────
// Feed por MÊS, e dentro dele as contas por dia. Tipster e geral não têm dia no
// banco (são valor mensal), então entram num bloco "mensais" ao fim do mês —
// inventar um dia para eles seria data derivada por estimativa, que o CLAUDE.md
// barra. O dia real deles chega na Fatia 3.
function _c2viewRaioX(t, r, rotulo){
  const porMes = {};
  r.meses.forEach(m => porMes[m] = { contas: {}, mensais: [], total: 0 });
  t.contas.forEach(c => {
    const m = c.data.slice(0, 7);
    if (!porMes[m]) return;
    (porMes[m].contas[c.data] = porMes[m].contas[c.data] || []).push(c);
    porMes[m].total += c.custo;
  });
  t.tips.forEach(x => r.meses.forEach(m => {
    const v = _c2num(((typeof ctData !== 'undefined' && ctData[x.nome]) || {})[m]);
    if (v > 0){ porMes[m].mensais.push({ nome: x.nome, sub: 'tipster', valor: v }); porMes[m].total += v; }
  }));
  t.ger.forEach((g, i) => r.meses.forEach(m => {
    const v = _c2num(((cgData[i] || {}).values || {})[m]);
    if (v > 0){ porMes[m].mensais.push({ nome: g.tipo || 'sem descrição', sub: 'geral', valor: v }); porMes[m].total += v; }
  }));

  const icoConta = '<svg viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="var(--accent-2)" stroke-width="1.6"><rect x="2" y="4" width="12" height="9" rx="1"/><path d="M5 4V3a1 1 0 011-1h4a1 1 0 011 1v1"/></svg>';
  const icoMes = '<svg viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="var(--accent-2)" stroke-width="1.6"><rect x="2" y="3.5" width="12" height="10" rx="1.5"/><path d="M2 6.5h12M5.5 2v3M10.5 2v3"/></svg>';

  const feed = r.meses.slice().reverse().map(m => {
    const bloco = porMes[m];
    if (!bloco.total) return '';
    const dias = Object.keys(bloco.contas).sort().reverse().map(d => `<div class="c2-dia">
        <div class="c2-dia__data">${d.slice(8, 10)}/${d.slice(5, 7)}</div>
        <div class="c2-dia__itens">${bloco.contas[d].map(c => `<div class="c2-item">
            <span class="c2-item__ico">${icoConta}</span>
            <div class="c2-item__txt"><div class="c2-ident">${esc(c.casa)}</div><div class="c2-meta">${esc(c.conta)} · ${esc(c.forn)}</div></div>
            <span class="c2-item__val">${c.custo > 0 ? fmtR(c.custo) : '<span class="c2-vazio-cel">sem preço</span>'}</span>
          </div>`).join('')}</div>
      </div>`).join('');
    const mensais = bloco.mensais.length ? `<div class="c2-dia">
        <div class="c2-dia__data c2-dia__data--mes">no mês</div>
        <div class="c2-dia__itens">${bloco.mensais.sort((a, b) => b.valor - a.valor).map(x => `<div class="c2-item">
            <span class="c2-item__ico">${icoMes}</span>
            <div class="c2-item__txt"><div class="c2-ident">${esc(x.nome)}</div><div class="c2-meta">${x.sub}</div></div>
            <span class="c2-item__val">${fmtR(x.valor)}</span>
          </div>`).join('')}</div>
      </div>` : '';
    return `<div class="c2-mes">
        <div class="c2-mes__hdr"><span class="c2-eyebrow">${_c2mesRotulo(m)}</span><span class="c2-total">${fmtR(bloco.total)}</span></div>
        ${dias}${mensais}
      </div>`;
  }).join('') || _c2vazio('Nenhum custo lançado neste recorte.');

  // Composição: um tom só, porque magnitude não é identidade (azul é o acento único).
  const barra = (nome, valor, sub) => {
    const p = t.custo > 0 ? (valor / t.custo * 100) : 0;
    return `<div class="c2-comp">
      <div class="c2-comp__top"><span class="c2-comp__nome">${nome}</span><span class="c2-comp__val">${fmtR(valor)} <span class="c2-meta">${fmtPct(p, 1, false)}</span></span></div>
      <div class="c2-comp__trilho"><div class="c2-comp__barra" style="width:${p}%"></div></div>
      <div class="c2-meta">${sub}</div>
    </div>`;
  };

  const maxMes = Math.max(1, ...r.meses.map(m => porMes[m].total));
  const colunas = r.meses.map(m => {
    const h = Math.round(porMes[m].total / maxMes * 70);
    const ult = m === r.mesRef;
    return `<div class="c2-col"><div class="c2-col__barra${ult ? ' is-on' : ''}" style="height:${Math.max(2, h)}px"></div></div>`;
  }).join('');
  const rotulos = r.meses.map(m => `<div class="c2-col__lbl${m === r.mesRef ? ' is-on' : ''}">${_c2mesRotulo(m).split('/')[0]}</div>`).join('');

  return `<div class="c2-raiox">
    <div class="card">
      <div class="card-hdr"><div class="card-title">O que a operação pagou</div><span class="c2-eyebrow">feed do recorte</span></div>
      <div class="card-body c2-feed">${feed}</div>
    </div>
    <div class="c2-raiox__lado">
      <div class="card">
        <div class="card-hdr"><div class="card-title">Onde o dinheiro foi</div>
          <span class="c2-hdr-val"><span class="c2-total">${fmtR(t.custo)}</span><span class="c2-eyebrow">em ${rotulo}</span></span></div>
        <div class="card-body">
          ${barra('Contas', t.tContas, t.contas.length + (t.contas.length === 1 ? ' conta comprada' : ' contas compradas'))}
          ${barra('Tipsters', t.tTips, (t.tips.length - t.tipsPend) + ' de ' + t.tips.length + ' resolvidos')}
          ${barra('Gerais', t.tGer, (t.ger.length - t.gerPend) + ' de ' + t.ger.length + ' confirmados')}
        </div>
      </div>
      <div class="card">
        <div class="card-hdr"><div class="card-title">Mês a mês</div><span class="c2-eyebrow">custo total da operação</span></div>
        <div class="card-body">
          <div class="c2-cols">${colunas}</div>
          <div class="c2-cols c2-cols--lbl">${rotulos}</div>
          <div class="c2-nota c2-nota--fim">Acompanha o período escolhido lá em cima. Escolha <strong>YTD</strong> ou <strong>Tudo</strong> para abrir a série inteira.</div>
        </div>
      </div>
    </div>
  </div>`;
}

// ── Casca dos cards ──────────────────────────────────────────────────────────
function _c2card(titulo, nota, corpo){
  return `<div class="card">
    <div class="card-hdr"><div class="card-title">${titulo}</div><span class="c2-eyebrow">${nota}</span></div>
    <div class="card-body">${corpo}</div>
  </div>`;
}
function _c2vazio(txt){ return `<div class="c2-empty">${txt}</div>`; }
function _c2dataBR(iso){
  const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(iso || '');
  return m ? m[3] + '/' + m[2] + '/' + m[1].slice(2) : '—';
}
