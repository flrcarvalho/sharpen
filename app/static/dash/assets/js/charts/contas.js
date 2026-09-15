// ── Aba CONTAS (s365) ────────────────────────────────────────────────────────
// Responde "quanto dura, quanto gira e quanto devolve uma conta nesta casa?".
//
// A fronteira com Bookies é a UNIDADE, e é ela que justifica esta aba existir:
// Bookies mede a APOSTA (onde as apostas rendem) e não sabe quantas contas geraram
// aquele P/L nem quanto tempo elas viveram. Aqui a unidade é a CONTA.
//
// ⚠️ A régua do PERÍODO, que é onde esta tela poderia mentir:
//   · o período escolhe QUAIS CONTAS ENTRAM (vida intersectando a janela);
//   · duração e dias ativos são da VIDA INTEIRA da conta, nunca recortados — truncar a
//     vida ao filtro inventaria número: uma conta que viveu de janeiro a junho não
//     durou "zero dias" porque alguém filtrou setembro. Mesma família do
//     "data derivada por ESTIMATIVA é dado inventado" (CLAUDE.md);
//   · turnover, P/L e custo SEGUEM o período, como no resto do app;
//   · a tela DIZ isso (`#cnRegua`) — duas réguas vizinhas sem legenda leem como defeito.
//
// Esporte e tipster NÃO recortam: descrevem a aposta, não a conta. A Bet365 custou o
// que custou e durou o que durou, olhe-se tênis ou futebol. Mesmo motivo pelo qual
// `calcCostFiltered` não recebe `rows`.
//
// Nada aqui deriva custo por caminho próprio: o custo sai de `_custoNaJanela`
// (gestao.js), a MESMA função de `calcCostFiltered` e do drill de Bookies. Somar
// `_custoDaConta` à mão daria o mesmo número por um caminho novo, que é exatamente
// quando as duas telas passam a divergir.

let _cnPop = 'ambas';     // 'ativas' | 'inativas' | 'ambas'
let _cnAberta = '';       // casa expandida no drill ('' = nenhuma)
let _cnSortCol = 'turn';
let _cnSortDir = -1;

// Mediana: o valor do MEIO da lista ordenada. Ela está na tela porque em TODA casa da
// base a mediana é cerca de metade da média (Superbet 5d contra 11d, Betano 8d contra
// 14d, Bet365 10d contra 19d): poucas contas longevas puxam a média, e quem lê só a
// média decide comprar achando que a conta dura o dobro do que dura.
function _cnMediana(xs){
  if(!xs.length)return 0;
  const a=xs.slice().sort((x,y)=>x-y);
  const m=a.length>>1;
  return a.length%2?a[m]:(a[m-1]+a[m])/2;
}
function _cnMedia(xs){return xs.length?xs.reduce((a,b)=>a+b,0)/xs.length:0;}

// Fornecedores do universo (cadastro ∪ base), para o multiselect. `normForn` manda:
// conta sem `[Fornecedor]` no nome é PRÓPRIA e aparece como "Eu" — são 59 das 182
// contas do Feca, um terço da base, e é o que distingue "custo zero de verdade" de
// "não lancei o preço".
function _cnFornecedores(){
  if(!_contaVida)_buildContaVida();
  const s=new Set();
  Object.keys(_contaVida).forEach(k=>{s.add(k.slice(0,k.indexOf('||')));});
  return [...s].sort((a,b)=>a.localeCompare(b,'pt-BR'));
}

// Universo de contas com vida + métricas. Uma função só, porque os KPIs, a tabela por
// casa e o drill têm de sair do MESMO recorte — derivar de novo em cada bloco é como a
// tela ganha dois números que discordam.
function _cnBase(){
  if(!_contaVida)_buildContaVida();
  const range=(typeof _selRange==='function')?_selRange('contas'):null;
  const de=range?range.from:'0000-01-01';
  const ate=range?range.to:'9999-12-31';
  const casasSel=msGet('ca_contas'), fornSel=msGet('fo_contas'), opsSel=msGet('op_contas');

  // Métricas por conta. Dias ativos e a vida vêm de LIQUIDADAS + ABERTAS (só `DADOS`
  // deixaria de fora a conta que tem aposta viva e nenhuma encerrada — o ponto cego da
  // s239); turnover e P/L só de `DADOS`, porque aposta aberta não tem resultado.
  const met={};
  const slot=k=>met[k]||(met[k]={dias:new Set(),turnPer:0,plPer:0,bets:0});
  const chave=r=>(normForn(r.fornecedor)+'||'+r.casa+'||'+(r.conta||'__default__'));
  (typeof DADOS!=='undefined'?DADOS:[]).forEach(r=>{
    if(!r.data)return;
    const m=slot(chave(r));
    m.dias.add(r.data);                              // vida inteira: sem corte de período
    if(r.data<de||r.data>ate)return;                 // dinheiro: dentro do período
    m.bets++;
    m.plPer+=r.lucro;
    if(r.resultado!=='V')m.turnPer+=r.stake;
  });
  (typeof DADOS_ABERTAS!=='undefined'?DADOS_ABERTAS:[]).forEach(r=>{
    if(!r.data)return;
    slot(chave(r)).dias.add(r.data);
  });

  const out=[];
  Object.entries(_contaVida).forEach(([k,contas])=>{
    const i=k.indexOf('||');
    const forn=k.slice(0,i), casa=k.slice(i+2);
    if(casasSel.size&&!casasSel.has(casa))return;
    if(fornSel.size&&!fornSel.has(forn))return;
    Object.entries(contas).forEach(([nome,v])=>{
      if(opsSel.size&&v.op&&!opsSel.has(v.op))return;
      // O período escolhe quem ENTRA: vida disjunta da janela → a conta não existia ali.
      if(v.ini&&v.fim&&(v.fim<de||v.ini>ate))return;
      const m=met[forn+'||'+casa+'||'+nome]||{dias:new Set(),turnPer:0,plPer:0,bets:0};
      // Ativa = cadastrada e não arquivada. `_buildContaVida` marca isso pondo o fim em
      // HOJE; conta sem cadastro tem o fim na última aposta e lê como encerrada, que é
      // tudo o que se sabe dela.
      const ativa=!!(v.fim&&v.fim===(typeof _ymd==='function'?_ymd(new Date()):''));
      let dur=0;
      if(v.ini&&v.fim){
        dur=Math.round((new Date(v.ini+'T00:00:00')-0-(new Date(v.fim+'T00:00:00')-0))/-864e5)+1;
      }
      out.push({
        casa:casa, forn:forn, conta:nome, chave:forn+'||'+casa+'||'+nome,
        ativa:ativa, propria:forn==='Eu',
        ini:v.ini, fim:v.fim, adq:v.adq,
        dur:dur, dias:m.dias.size, bets:m.bets,
        turn:m.turnPer, pl:m.plPer,
        custo:(typeof _custoDaConta==='function')?_custoDaConta(forn,casa,nome):0,
      });
    });
  });
  const pop=_cnPop==='ativas'?out.filter(c=>c.ativa)
          :_cnPop==='inativas'?out.filter(c=>!c.ativa):out;
  return {contas:pop, de:de, ate:ate, temPeriodo:!!range, casasSel:casasSel, opsSel:opsSel};
}

// Agrega por casa. `semPreco` só conta a COMPRADA sem valor: conta própria tem custo
// zero de VERDADE e não é buraco de dado.
function _cnPorCasa(contas){
  const by={};
  contas.forEach(c=>{
    const a=by[c.casa]||(by[c.casa]={casa:c.casa,n:0,ativas:0,inativas:0,proprias:0,semPreco:0,
                                     durs:[],diasArr:[],turn:0,pl:0,custo:0,comPreco:0});
    a.n++;
    if(c.ativa)a.ativas++;else a.inativas++;
    if(c.propria)a.proprias++;
    if(c.custo>0)a.comPreco++;else if(!c.propria)a.semPreco++;
    if(c.dur>0)a.durs.push(c.dur);
    if(c.dias>0)a.diasArr.push(c.dias);
    a.turn+=c.turn; a.pl+=c.pl; a.custo+=c.custo;
  });
  return Object.values(by).map(a=>({
    ...a,
    dur:_cnMedia(a.durs), durMed:_cnMediana(a.durs), dias:_cnMedia(a.diasArr),
    // O múltiplo só existe onde há preço. Somar a conta sem preço como zero inflaria o
    // retorno com custo que EXISTE e não foi declarado — o zero se disfarçando de conta
    // feita, ao contrário da própria, cujo zero é declarado.
    mult:a.custo>0?(a.pl/a.custo):null,
  }));
}

function _cnPopSub(){
  return _cnPop==='ativas'?'ainda rodando · a vida delas não terminou'
       :_cnPop==='inativas'?'encerradas · a régua honesta de durabilidade'
       :'todas as contas que existiram no período';
}
// A barra NÃO repinta junto com o conteúdo (repintá-la fecharia um multiselect aberto e
// perderia o foco da busca dentro dele), então quem muda o estado atualiza o segmentado
// à mão. Mesma razão pela qual o `rqb` existe para os botões de período.
function cnPop(v){
  _cnPop=v;
  document.querySelectorAll('#cnSeg button').forEach(b=>b.classList.toggle('active',b.dataset.k===v));
  const s=document.querySelector('.cn-popsub');
  if(s)s.textContent=_cnPopSub();
  renderContas();
}
function cnToggle(casa){_cnAberta=(_cnAberta===casa?'':casa);renderContas();}
function cnSort(col){
  if(_cnSortCol===col)_cnSortDir=-_cnSortDir;else{_cnSortCol=col;_cnSortDir=-1;}
  renderContas();
}
window.cnPop=cnPop;window.cnToggle=cnToggle;window.cnSort=cnSort;

// Os filtros são montados UMA vez, no primeiro render da aba, e não no `buildHTML`: a
// lista de fornecedores sai do `_contaVida`, que só existe depois do `contasLoad()`.
// Montar cedo demais daria um multiselect vazio, em silêncio.
function _cnMontarFiltros(){
  const box=document.getElementById('contasFiltros');
  if(!box||box.dataset.pronto)return;
  box.innerHTML=buildFiltrosContas((typeof _LISTAS!=='undefined'&&_LISTAS.casas)||[]);
  box.dataset.pronto='1';
}
window._cnMontarFiltros=_cnMontarFiltros;

// ⚠️ O DOM pode AINDA NÃO EXISTIR quando as cargas resolvem, e o sintoma é a aba em
// branco — intermitente, porque é corrida. Medido no headless: o boot do dashboard é
// assíncrono e a casca (`app.html`) chama `showPage` no evento `load` do iframe, que
// dispara antes do `buildHTML` montar o `#contasContent`. O `renderPage` prematuro
// escreve no vazio E MARCA a assinatura da página; o `showPage` que o `buildHTML` faz
// logo depois é então engolido pelo guard `id===_lastPage&&sig===_lastPageSig`, e não
// há segunda chance.
//
// A espera curta resolve isto AQUI, sem tocar no roteador que todas as telas usam —
// o guard do `showPage` é defeito compartilhado e anterior a esta aba, e consertá-lo
// de verdade é mudança própria, com a suíte inteira por perto.
function _cnPintarQuandoPronto(tentativa){
  const t=tentativa||0;
  if(!document.getElementById('contasContent')){
    if(t<40)setTimeout(()=>_cnPintarQuandoPronto(t+1),100);   // teto de 4s, depois desiste
    return;
  }
  _cnMontarFiltros();
  renderContas();
}
window._cnPintarQuandoPronto=_cnPintarQuandoPronto;

// Barra própria, NÃO o `buildFilters` genérico: esporte e tipster não recortam esta
// tela, e oferecê-los faria o número mudar por um eixo que não descreve a conta.
// As peças são as mesmas do `filters.js` — copiar o markup criaria dois Períodos que
// divergem no primeiro ajuste (a lição da s317).
function buildFiltrosContas(casas){
  const seg=['ativas','inativas','ambas'].map(k=>{
    const lbl=k==='ativas'?'Ativas':k==='inativas'?'Inativas':'Ambas';
    return`<button data-k="${k}" class="${_cnPop===k?'active':''}" onclick="cnPop('${k}')">${lbl}</button>`;
  }).join('');
  const sub=_cnPopSub();
  return`<div class="filters">
${_grupoPeriodo('contas')}
    ${_grupoCasa('contas',casas,'renderContas()')}
    <div class="filter-group"><div class="filter-label">Fornecedor</div>${buildMS('fo_contas',_cnFornecedores(),'Todos os fornecedores','contas','renderContas()')}</div>
    ${_grupoOperador('contas','renderContas()')}
    <div class="filter-group">
      <div class="filter-label">População</div>
      <div class="tcard-seg" id="cnSeg" style="padding-top:2px">${seg}</div>
      <div class="cn-popsub">${sub}</div>
    </div>
  </div>`;
}

// O "i" da mediana reusa o padrão `.tip-anchor` + `.metric-info` + `.metric-tip` do
// projeto (o `_gTip` global clona e posiciona, por delegação no `document`) — nenhum
// tooltip novo. O `stopPropagation` é obrigatório: o `<th>` inteiro é o gatilho do
// sort, e sem ele abrir a ajuda reordenaria a tabela por baixo do cursor.
function _cnTipMediana(){
  return`<span class="tip-anchor">Mediana<button class="metric-info" aria-label="Sobre a mediana" onclick="event.stopPropagation()">i</button>`
    +`<div class="metric-tip" role="tooltip" hidden><span class="metric-tip__caret"></span>`
    +`<div class="metric-tip__formula"><span class="lbl">metade durou menos</span><span class="op">·</span><span class="lbl">metade durou mais</span></div>`
    +`<div class="metric-tip__desc">O valor do <b>meio</b>, com as contas enfileiradas da mais curta para a mais longa. `
    +`Quando a mediana é bem menor que a média, poucas contas longevas estão puxando a média — e a <b>mediana</b> é que descreve a conta típica.</div>`
    +`<div class="metric-tip__bench"><span>calculada no período do filtro</span></div></div></span>`;
}

function renderContas(){
  const cont=document.getElementById('contasContent');
  if(!cont)return;
  const B=_cnBase();
  const linhas=_cnPorCasa(B.contas);

  // ── KPIs de vida ──────────────────────────────────────────────────────────
  const durs=B.contas.filter(c=>c.dur>0).map(c=>c.dur);
  const dias=B.contas.filter(c=>c.dias>0).map(c=>c.dias);
  const turns=B.contas.filter(c=>c.turn>0).map(c=>c.turn);
  const nAtivas=B.contas.filter(c=>c.ativa).length;
  const kpi=(lbl,val,sub)=>`<div class="kpi"><div class="kpi-label"><span class="kpi-pipe"></span>${lbl}</div>`
    +`<div class="kpi-val" style="margin-top:auto">${val}</div><div class="kpi-sub">${sub}</div></div>`;
  const kpis=`<div class="kpi-grid">`
    +kpi('Contas',B.contas.length.toLocaleString('pt-BR'),
         `${nAtivas} ativas · ${B.contas.length-nAtivas} inativas`)
    +kpi('Duração média',Math.round(_cnMedia(durs))+'d','mediana '+Math.round(_cnMediana(durs))+'d')
    +kpi('Dias ativos',Math.round(_cnMedia(dias))+'d','mediana '+Math.round(_cnMediana(dias))+'d')
    +kpi('Turnover / conta',fmtR(_cnMedia(turns)),'mediana '+fmtR(_cnMediana(turns)))
    +`</div>`;

  // ── régua (a linha que impede duas leituras) ──────────────────────────────
  const regua=`<div class="cn-regua" id="cnRegua">`
    +`<svg width="13" height="13" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="8" cy="8" r="6.4"/><path d="M8 7.2v4M8 4.8v.1"/></svg>`
    +`<div>O período escolhe <b>quais contas entram</b>. <b>Duração e dias ativos são da vida inteira</b> da conta, `
    +`nunca cortados pelo filtro. <b>Turnover, P/L e custo seguem o período</b>. Esporte e tipster não recortam esta tela.</div>`
    +`</div>`;

  // ── tabela por casa ───────────────────────────────────────────────────────
  const dir=_cnSortDir;
  const key=_cnSortCol;
  linhas.sort((a,b)=>{
    const va=key==='casa'?a.casa:a[key], vb=key==='casa'?b.casa:b[key];
    if(key==='casa')return va.localeCompare(vb,'pt-BR')*(-dir);
    return ((va||0)-(vb||0))*dir;
  });
  const th=(col,lbl,cls)=>`<th class="${cls||'th-r'} ${_cnSortCol===col?'sort-'+(dir<0?'desc':'asc'):''}" onclick="cnSort('${col}')">${lbl}<span class="sort-icon"></span></th>`;
  const corpo=linhas.map(a=>{
    const aberta=_cnAberta===a.casa;
    const plCls=a.pl>=0?'':'';
    const chev=`<svg class="cn-chev ${aberta?'on':''}" width="9" height="9" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 3l5 5-5 5"/></svg>`;
    let html=`<tr class="cn-row ${aberta?'cn-row--on':''}" data-sort="${esc(a.casa)}" onclick="cnToggle('${esc(a.casa).replace(/'/g,"\\'")}')">`
      +`<td class="cn-casa">${chev}${casaCell(a.casa)}</td>`
      +`<td class="td-num cn-ink">${a.n} <span class="cn-split">${a.ativas}·${a.inativas}</span></td>`
      +`<td class="td-num cn-ink">${Math.round(a.dur)}d</td>`
      +`<td class="td-num cn-ink">${Math.round(a.durMed)}d</td>`
      +`<td class="td-num">${Math.round(a.dias)}d</td>`
      +`<td class="td-num">${fmtR(a.turn)}</td>`
      +`<td class="td-num">${fmtPL(a.pl)}</td>`
      +`</tr>`;
    if(aberta)html+=_cnDrill(a,B.contas.filter(c=>c.casa===a.casa));
    return html;
  }).join('');

  const tabela=mkCardHTML('Vida das contas por casa',
    `<span class="cn-escopo">${_cnEscopoTxt(B)}</span>`,
    `<div class="tbl-wrap"><table class="tbl" id="tblContas"><thead><tr>`
    +th('casa','Casa','th-l')
    +th('n','Contas')
    +th('dur','Duração')
    +`<th class="th-r ${_cnSortCol==='durMed'?'sort-'+(dir<0?'desc':'asc'):''}" onclick="cnSort('durMed')">${_cnTipMediana()}<span class="sort-icon"></span></th>`
    +th('dias','Dias ativos')
    +th('turn','Turnover')
    +th('pl','P/L')
    +`</tr></thead><tbody>${corpo||'<tr><td colspan="7" class="cn-vazio">Nenhuma conta no recorte.</td></tr>'}</tbody></table></div>`);

  cont.innerHTML=kpis+regua+tabela+_cnCustoCard(B,linhas);
}
window.renderContas=renderContas;

function _cnEscopoTxt(B){
  const n=B.contas.length;
  const rot=_cnPop==='ativas'?'Só ativas':_cnPop==='inativas'?'Só inativas':'Ativas e inativas';
  return `${rot} · ${n} conta${n===1?'':'s'}`+(B.temPeriodo?' · no período':'');
}

// Card montado à mão (não pelo `mkCard` do app.js, que só roda no primeiro paint e
// guarda estado de colapso por id) — esta tela repinta inteira a cada filtro.
function mkCardHTML(titulo,extra,corpo){
  return`<div class="card"><div class="card-hdr"><div class="card-title">${titulo}</div>${extra||''}</div>`
    +`<div class="card-body">${corpo}</div></div>`;
}

function _cnDrill(agg,contas){
  const rows=contas.slice().sort((a,b)=>b.turn-a.turn).slice(0,12).map(c=>{
    const liq=c.pl-c.custo;
    const est=c.ativa?'<span class="cn-est cn-est--on">ativa</span>':'<span class="cn-est">encerrada</span>';
    const custo=c.propria?'<span class="cn-propria">própria</span>'
              :c.custo>0?fmtR(c.custo)
              :'<span class="cn-sem">sem preço</span>';
    // Sem preço lançado não há líquido: mostrar o P/L cru na coluna de líquido faria a
    // conta parecer mais lucrativa do que se sabe que ela é.
    const cliq=(c.propria||c.custo>0)?fmtPL(liq):'<span class="cn-sem">·</span>';
    return`<tr>`
      +`<td class="th-l cn-ink">${esc(c.conta)}</td>`
      +`<td class="th-l">${esc(c.forn)}</td>`
      +`<td class="th-l">${est}</td>`
      +`<td class="td-num">${_cnData(c.ini)}</td>`
      +`<td class="td-num">${_cnData(c.fim)}</td>`
      +`<td class="td-num cn-ink">${c.dur}d</td>`
      +`<td class="td-num">${c.dias}d</td>`
      +`<td class="td-num">${fmtR(c.turn)}</td>`
      +`<td class="td-num">${custo}</td>`
      +`<td class="td-num">${cliq}</td>`
      +`</tr>`;
  }).join('');
  const resto=contas.length>12?`<span class="cn-nota">… mais ${contas.length-12} contas</span>`:'';
  const alerta=agg.semPreco>0
    ?`<span class="cn-alerta"><svg width="11" height="11" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M8 2l6 11H2z"/><path d="M8 6.5v3M8 11.2v.1"/></svg>`
     +`${agg.semPreco} conta${agg.semPreco===1?'':'s'} sem preço lançado fica${agg.semPreco===1?'':'m'} fora do múltiplo</span>`:'';
  return`<tr class="cn-drill"><td colspan="7"><div class="cn-drill-box">`
    +`<table class="tbl"><thead><tr>`
    +`<th class="th-l">Conta</th><th class="th-l">Fornecedor</th><th class="th-l">Estado</th>`
    +`<th class="th-r">Comprada</th><th class="th-r">Última</th><th class="th-r">Duração</th>`
    +`<th class="th-r">Dias at.</th><th class="th-r">Turnover</th><th class="th-r">Custo</th>`
    +`<th class="th-r">P/L líquido</th>`
    +`</tr></thead><tbody>${rows}</tbody></table>`
    +(resto||alerta?`<div class="cn-drill-foot">${resto}${alerta}</div>`:'')
    +`</div></td></tr>`;
}

function _cnData(iso){
  if(!iso)return'<span class="cn-sem">·</span>';
  const p=iso.split('-');
  return`<span data-sort="${iso}">${p[2]}/${p[1]}/${p[0].slice(2)}</span>`;
}

// ── Custo × Retorno ──────────────────────────────────────────────────────────
// Escopo PRÓPRIO, dito no cabeçalho: só as casas com preço lançado mais as próprias.
// Um múltiplo que dividisse o lucro de 48 casas pelo custo de 3 seria mentira com cara
// de precisão — e na base do Feca são exatamente 3 casas com preço.
function _cnCustoCard(B,linhas){
  const comPreco=linhas.filter(a=>a.custo>0);
  const nProprias=B.contas.filter(c=>c.propria).length;
  const nSemPreco=B.contas.filter(c=>!c.propria&&c.custo<=0).length;
  if(!comPreco.length&&!nProprias)return'';

  // O custo TOTAL sai do `_custoNaJanela`, régua única com Bookies e a Visão Geral —
  // nunca de uma soma própria das linhas.
  const contasOk=new Set(B.contas.map(c=>c.chave));
  const {total:custoTotal}=(typeof _custoNaJanela==='function')
    ? _custoNaJanela(B.de,B.ate,B.casasSel,B.opsSel,'','pago',contasOk)
    : {total:comPreco.reduce((a,x)=>a+x.custo,0)};

  const elegiveis=B.contas.filter(c=>c.propria||c.custo>0);
  const plElegivel=elegiveis.reduce((a,c)=>a+c.pl,0);
  const multGeral=custoTotal>0?(plElegivel/custoTotal):null;

  const tile=(lbl,val,cls,sub)=>`<div class="cn-tile"><span class="cn-tile__lab">${lbl}</span>`
    +`<span class="cn-tile__val ${cls||''}">${val}</span><span class="cn-tile__sub">${sub}</span></div>`;

  const tiles=`<div class="cn-tiles">`
    +tile('Custo de contas',fmtR(custoTotal),'warn',`${B.contas.filter(c=>c.custo>0).length} de ${B.contas.length} contas`)
    // O `.money` dentro de uma FRASE precisa do carve-out do `UI_REFERENCE §5.5` — ele é
    // `width:100%` com `min-width:10ch` por desenho (para alinhar coluna de tabela), e
    // solto num parágrafo ele quebra a linha. O carve-out está no `.cn-tile__sub .money`.
    +tile('P/L nessas casas',fmtPL(plElegivel),'',`após o custo: ${fmtPL(plElegivel-custoTotal)}`)
    +tile('Múltiplo do custo',_cnMult(multGeral),'',
          multGeral===null?'sem preço lançado'
          :_cnPop==='ativas'?'ainda rodando · não é final'
          :`cada R$ 1 voltou R$ ${multGeral.toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2})}`)
    +`</div>`;

  const rows=comPreco.slice().sort((a,b)=>b.custo-a.custo).map(a=>{
    const liq=a.pl-a.custo;
    return`<tr>`
      +`<td class="th-l cn-casa">${casaCell(a.casa)}</td>`
      +`<td class="td-num cn-ink">${a.n}</td>`
      +`<td class="td-num">${fmtR(a.custo)}</td>`
      +`<td class="td-num">${fmtR(a.custo/Math.max(a.comPreco,1))}</td>`
      +`<td class="td-num">${fmtPL(a.pl)}</td>`
      +`<td class="td-num">${fmtPL(liq)}</td>`
      +`<td class="td-num">${_cnMult(a.mult)}</td>`
      +`</tr>`;
  }).join('');

  const nota=`<div class="cn-nota-box">`
    +`<svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="8" cy="8" r="6.4"/><path d="M8 7.2v4M8 4.8v.1"/></svg>`
    +`<div><b>Conta própria entra com custo zero</b>, e o P/L líquido dela é o P/L cheio. `
    +`<b>Conta comprada sem preço lançado fica de fora</b> do múltiplo: somá-la como zero inflaria o retorno com custo que existe e não foi declarado.</div>`
    +`</div>`;

  const escopo=`<span class="cn-escopo">${comPreco.length} casa${comPreco.length===1?'':'s'} com preço`
    +` · ${nProprias} conta${nProprias===1?'':'s'} própria${nProprias===1?'':'s'}`
    +` · ${nSemPreco} sem preço</span>`;

  return mkCardHTML('Custo × Retorno',escopo,tiles
    +`<div class="tbl-wrap"><table class="tbl" id="tblContasCusto"><thead><tr>`
    +`<th class="th-l">Casa</th><th class="th-r">Contas</th><th class="th-r">Custo</th>`
    +`<th class="th-r">Custo / conta</th><th class="th-r">P/L bruto</th>`
    +`<th class="th-r">P/L líquido</th><th class="th-r">Múltiplo</th>`
    +`</tr></thead><tbody>${rows}</tbody></table></div>`+nota);
}


// Máscara do MÚLTIPLO (razão P/L ÷ custo). O `UI_REFERENCE §5` cobre R$, %, odd e
// saldo; a razão não é nenhum dos quatro, então ela espelha a gramática do `.money`:
// mono, 2 casas, o `×` neutro e menor como o `R$`, e cor SÓ abaixo de 1,00 — que é a
// conta que não devolveu o que custou. Decisão registrada no `UI_REFERENCE §5.6`.
function _cnMult(v){
  if(v===null||v===undefined)return'<span class="cn-sem">·</span>';
  const n=v.toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2});
  return`<span class="cn-mult ${v<1?'neg':''}">${n}<span class="cn-mult__x">×</span></span>`;
}
