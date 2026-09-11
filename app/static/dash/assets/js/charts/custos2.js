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

// ── Peças de apoio ───────────────────────────────────────────────────────────

// Parse de valor gravado como string BR ("250,00"). É PARSE, não display: a regra
// de não usar .replace vale para a máscara de saída (UI_REFERENCE §5.2).
function _c2num(v){
  const n = parseFloat((v == null ? '' : v).toString().replace(/\./g, '').replace(',', '.'));
  return isNaN(n) ? 0 : n;
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

// O recorte da tela. Sem período escolhido ("Tudo") o fechamento não faz sentido,
// então cai no mês corrente — e o rótulo diz qual é.
function _c2range(){
  const r = (typeof _selRange === 'function') ? _selRange('custos_v2') : null;
  const hoje = _ymd(new Date());
  const de = r ? r.from : _ymd(new Date(new Date().getFullYear(), new Date().getMonth(), 1));
  const ate = r ? r.to : hoje;
  const meses = _c2meses(de.slice(0, 7) + '-01', ate);
  return { de: de, ate: ate, meses: meses, mesRef: meses[meses.length - 1] || hoje.slice(0, 7) };
}

// Casas e fornecedores selecionados nos multiselects (Set vazio = todos).
function _c2sel(){
  const ca = (typeof msGet === 'function') ? msGet('ca_custos_v2') : null;
  const fo = (typeof msGet === 'function') ? msGet('fo_custos_v2') : null;
  return { ca: ca, fo: fo };
}
function _c2passa(sel, casa, forn){
  if (sel.ca && sel.ca.size && !sel.ca.has(casa)) return false;
  if (sel.fo && sel.fo.size && !sel.fo.has(forn)) return false;
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
    if (!_c2passa(sel, p.casa, forn)) return;
    const custo = (typeof custoData !== 'undefined' && custoData[forn + '||' + p.casa]) || 0;
    out.push({ casa: p.casa, conta: p.conta, forn: forn, data: p.adquirida_em, custo: custo });
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
    const vAnt = _c2num(meses[ant]);
    const temRef = !!(meses[r.mesRef] && vRef > 0);
    return {
      nome: nome, valor: vRef, anterior: vAnt, resolvido: temRef,
      noPeriodo: r.meses.reduce((a, m) => a + _c2num(meses[m]), 0)
    };
  });
}

// GERAIS: as linhas livres do custo geral (VPN, ferramentas, taxas).
function _c2gerais(){
  const r = _c2range();
  const ant = _c2mesAnterior(r.mesRef);
  return (typeof cgData !== 'undefined' && cgData ? cgData : []).map(row => {
    const vals = row.values || {};
    const vRef = _c2num(vals[r.mesRef]);
    return {
      tipo: (row.tipo || '').trim(), valor: vRef, anterior: _c2num(vals[ant]),
      resolvido: !!(vals[r.mesRef] && vRef > 0),
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
    tipsPend: tips.filter(t => !t.resolvido).length,
    gerPend: ger.filter(g => !g.resolvido).length,
    tipsPrev: tips.filter(t => !t.resolvido).reduce((a, t) => a + t.anterior, 0)
  };
}

// ── Barra de filtros ─────────────────────────────────────────────────────────
// Composta com as PEÇAS de filters.js, nunca reescrita: duas barras de Período na
// mesma tela divergem no primeiro ajuste (regra da s317 no CLAUDE.md). Esporte e
// Tipster ficam de fora de propósito — descrevem a APOSTA e não recortam custo.
function buildFiltersCustos(p, casas){
  const _todas = DADOS.concat(typeof DADOS_ABERTAS !== 'undefined' ? DADOS_ABERTAS : []);
  const forns = [...new Set(_todas.map(r => normForn(r.fornecedor)).filter(Boolean))]
    .sort((a, b) => a.localeCompare(b, 'pt-BR'));
  return `<div class="filters">
${_grupoPeriodo(p)}
    ${_grupoCasa(p, casas)}
    <div class="filter-group"><div class="filter-label">Fornecedor</div>${buildMS('fo_' + p, forns, 'Todos os fornecedores', p, '')}</div>
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

// ── Render ───────────────────────────────────────────────────────────────────

window.c2Tab = function(aba){ _c2aba = aba; renderCustos2(); };

function renderCustos2(){
  const host = document.getElementById('c2Body');
  if (!host) return;
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
  const legenda = (cor, nome, valor) => `<div class="c2-leg"><span class="c2-leg__dot" style="background:${cor}"></span><span class="c2-leg__lbl">${nome}</span><span class="c2-leg__val">${fmtR(valor)}</span></div>`;
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
      ${legenda('var(--pos)', 'P/L Líquido', t.liquido)}
      ${legenda('var(--accent)', 'Contas', t.tContas)}
      ${legenda('rgba(var(--accent-rgb),.68)', 'Tipsters', t.tTips)}
      ${legenda('rgba(var(--accent-rgb),.40)', 'Gerais', t.tGer)}
      <div class="c2-leg c2-leg--fim"><span class="c2-leg__lbl">P/L Bruto</span><span class="c2-leg__val">${fmtR(t.bruto)}</span></div>
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
    return _c2card('Contas compradas em ' + rotulo, 'custo único, pago na compra',
      _c2vazio('Nenhuma conta comprada neste recorte. O cadastro guarda a data de compra em <strong>Comprada em</strong>, no Painel de Contas.'))
      + _c2viewPrecos();
  }
  const linhas = t.contas.map(c => {
    const temCusto = c.custo > 0;
    return `<tr>
      <td class="th-l">${casaCell(c.casa)}</td>
      <td class="th-l c2-ident">${esc(c.conta)}</td>
      <td class="th-l c2-ident">${esc(c.forn)}</td>
      <td class="th-l c2-dt">${_c2dataBR(c.data)}</td>
      <td class="th-l">${temCusto
        ? '<span class="c2-orig">tabela do fornecedor</span>'
        : '<span class="c2-orig c2-orig--todo">sem preço lançado</span>'}</td>
      <td class="td-num">${temCusto ? fmtR(c.custo) : '<span class="c2-vazio-cel">—</span>'}</td>
    </tr>`;
  }).join('');
  const corpo = `<div class="tbl-wrap"><table class="tbl c2-tbl">
      <thead><tr>
        <th class="th-l">Casa</th><th class="th-l">Conta</th><th class="th-l">Fornecedor</th>
        <th class="th-l">Lançamento</th><th class="th-l">Origem do valor</th><th class="td-num">Valor</th>
      </tr></thead>
      <tbody>${linhas}</tbody>
    </table></div>
    <div class="c2-rodape">
      <span class="c2-meta">${t.contas.length} ${t.contas.length === 1 ? 'conta' : 'contas'} no recorte${t.semCusto ? ' · ' + t.semCusto + ' sem preço' : ''}</span>
      <span class="c2-total">${fmtR(t.tContas)}</span>
    </div>`;
  return _c2card('Contas compradas em ' + rotulo, 'custo único, pago na compra', corpo) + _c2viewPrecos();
}

// A tabela de precos, como ela existe HOJE: um valor por par `fornecedor||casa`.
// Fonte: `custoData` (gestao.js). A contagem de contas usa a UNIAO cadastro ∪
// bilhetes, que e a regra do `buildCostState` — 130 contas do Feca so existem em
// bilhete, e contar so o cadastro as esconderia.
function _c2precos(){
  const sel = _c2sel();
  const contas = {};   // "forn||casa" -> Set(conta)
  const _add = (forn, casa, conta) => {
    if (!casa) return;
    const k = normForn(forn) + '||' + casa;
    (contas[k] = contas[k] || new Set()).add(conta || '__sem_nome__');
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
    const preco = (typeof custoData !== 'undefined' && custoData[k]) || 0;
    const n = contas[k] ? contas[k].size : 0;
    linhas.push({ forn: forn, casa: casa, preco: preco, n: n, total: preco * n });
  });
  linhas.sort((a, b) => a.forn === b.forn
    ? b.total - a.total || a.casa.localeCompare(b.casa, 'pt-BR')
    : a.forn.localeCompare(b.forn, 'pt-BR'));
  return linhas;
}

function _c2viewPrecos(){
  const linhas = _c2precos();
  if (!linhas.length){
    return _c2card('Tabela de preços por fornecedor', 'o preço que vale hoje',
      _c2vazio('Nenhum preço lançado e nenhuma conta viva. Os preços de hoje são lançados em <strong>Custos de Contas</strong>.'));
  }
  const semPreco = linhas.filter(l => !(l.preco > 0) && l.n > 0).length;
  const total = linhas.reduce((a, l) => a + l.total, 0);
  let ultimo = null;
  const corpo = `<div class="c2-nota">Esta tabela <strong>não é do recorte</strong>: ela mostra o preço que vale hoje, enquanto a lista acima mostra as compras do período. O preço ainda é do <strong>par fornecedor e casa</strong>, então duas contas do mesmo par não podem custar diferente. Preço com <strong>data de vigência</strong> e custo <strong>por conta</strong> são as Fatias 1 e 2.</div>
    <div class="tbl-wrap"><table class="tbl c2-tbl">
      <thead><tr>
        <th class="th-l">Fornecedor</th><th class="th-l">Casa</th>
        <th class="td-num">Preço por conta</th><th class="td-num">Contas</th><th class="td-num">Total</th>
      </tr></thead>
      <tbody>${linhas.map(l => {
        const novo = l.forn !== ultimo; ultimo = l.forn;
        return `<tr>
          <td class="th-l">${novo ? `<span class="c2-ident">${esc(l.forn)}</span>` : '<span class="c2-vazio-cel">&#8942;</span>'}</td>
          <td class="th-l">${casaCell(l.casa)}</td>
          <td class="td-num">${l.preco > 0 ? fmtR(l.preco) : '<span class="c2-orig c2-orig--todo">sem preço</span>'}</td>
          <td class="td-num c2-ref">${l.n || '<span class="c2-vazio-cel">&#8212;</span>'}</td>
          <td class="td-num">${l.total > 0 ? fmtR(l.total) : '<span class="c2-vazio-cel">&#8212;</span>'}</td>
        </tr>`;
      }).join('')}</tbody>
    </table></div>
    <div class="c2-rodape">
      <span class="c2-meta">${linhas.length} ${linhas.length === 1 ? 'par' : 'pares'} fornecedor e casa${semPreco ? ' · ' + semPreco + ' com conta viva e sem preço' : ''}</span>
      <span class="c2-total">${fmtR(total)}</span>
    </div>`;
  return _c2card('Tabela de preços por fornecedor', 'o preço que vale hoje', corpo);
}

// ── Aba Tipsters ─────────────────────────────────────────────────────────────
function _c2viewTipsters(t, mes, mesAnt, umMes, rotuloPeriodo){
  if (!t.tips.length){
    return _c2card('Tipsters em ' + mes, 'assinatura, staking ou temporada',
      _c2vazio('Nenhum tipster na base ainda.'));
  }
  const linhas = t.tips.map(x => `<tr>
      <td class="th-l c2-ident">${esc(x.nome)}</td>
      <td class="th-l"><span class="c2-orig c2-orig--vazio">a definir</span></td>
      <td class="td-num c2-ref">${x.anterior > 0 ? fmtR(x.anterior) : '<span class="c2-vazio-cel">—</span>'}</td>
      <td class="td-num">${x.resolvido ? fmtR(x.valor) : '<span class="c2-vazio-cel">—</span>'}</td>
      <td class="th-l">${x.resolvido
        ? '<span class="c2-badge c2-badge--ok">Confirmado</span>'
        : '<span class="c2-badge c2-badge--wait">Pendente</span>'}</td>
    </tr>`).join('');
  const corpo = `<div class="c2-nota">${umMes ? '' : `O recorte é <strong>${rotuloPeriodo}</strong>, mas a lista abaixo é de <strong>${mes}</strong>: assinatura se lança mês a mês. O KPI lá em cima soma o período inteiro. `}A coluna <strong>Cobrança</strong> nasce vazia porque o tipo (mensalidade, staking, temporada) ainda não existe no banco: ele entra na Fatia 3, e é ele que decide se o valor do mês anterior se arrasta sozinho.</div>
    <div class="tbl-wrap"><table class="tbl c2-tbl">
      <thead><tr>
        <th class="th-l">Tipster</th><th class="th-l">Cobrança</th>
        <th class="td-num">${mesAnt}</th><th class="td-num">Custo de ${mes}</th><th class="th-l">Situação</th>
      </tr></thead>
      <tbody>${linhas}</tbody>
    </table></div>
    <div class="c2-rodape">
      <span class="c2-meta">confirmado em ${mes} <span class="c2-total">${fmtR(t.tTipsMes)}</span>${umMes ? '' : ` · ${rotuloPeriodo} soma <span class="c2-total">${fmtR(t.tTips)}</span>`}</span>
      ${t.tipsPrev > 0 ? `<span class="c2-prev">+ ${fmtR(t.tipsPrev)} previsto nos ${t.tipsPend} pendentes</span>` : ''}
    </div>`;
  return _c2card('Tipsters em ' + mes, t.tips.length - t.tipsPend + ' de ' + t.tips.length + ' resolvidos', corpo);
}

// ── Aba Gerais ───────────────────────────────────────────────────────────────
function _c2viewGerais(t, mes, mesAnt, umMes, rotuloPeriodo){
  if (!t.ger.length){
    return _c2card('Custos gerais em ' + mes, 'infraestrutura, ferramentas, taxas',
      _c2vazio('Nenhum custo geral lançado ainda.'));
  }
  const linhas = t.ger.map(g => `<tr>
      <td class="th-l c2-ident">${esc(g.tipo || 'sem descrição')}</td>
      <td class="th-l"><span class="c2-orig c2-orig--vazio">a definir</span></td>
      <td class="td-num c2-ref">${g.anterior > 0 ? fmtR(g.anterior) : '<span class="c2-vazio-cel">—</span>'}</td>
      <td class="td-num">${g.resolvido ? fmtR(g.valor) : '<span class="c2-vazio-cel">—</span>'}</td>
      <td class="th-l">${g.resolvido
        ? '<span class="c2-badge c2-badge--ok">Confirmado</span>'
        : '<span class="c2-badge c2-badge--wait">Pendente</span>'}</td>
    </tr>`).join('');
  const corpo = `<div class="c2-nota">${umMes ? '' : `O recorte é <strong>${rotuloPeriodo}</strong>, mas a lista abaixo é de <strong>${mes}</strong>. O KPI lá em cima soma o período inteiro. `}Categoria e recorrência entram na Fatia 4, com as três de fábrica (Infra, Ferramenta, Taxa) mais as que você criar.</div>
    <div class="tbl-wrap"><table class="tbl c2-tbl">
      <thead><tr>
        <th class="th-l">Descrição</th><th class="th-l">Categoria</th>
        <th class="td-num">${mesAnt}</th><th class="td-num">Custo de ${mes}</th><th class="th-l">Situação</th>
      </tr></thead>
      <tbody>${linhas}</tbody>
    </table></div>
    <div class="c2-rodape">
      <span class="c2-meta">confirmado em ${mes} <span class="c2-total">${fmtR(t.tGerMes)}</span>${umMes ? '' : ` · ${rotuloPeriodo} soma <span class="c2-total">${fmtR(t.tGer)}</span>`}</span>
      ${t.gerPend ? `<span class="c2-prev">${t.gerPend} pendente${t.gerPend > 1 ? 's' : ''}</span>` : ''}
    </div>`;
  return _c2card('Custos gerais em ' + mes, 'infraestrutura, ferramentas, taxas', corpo);
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
