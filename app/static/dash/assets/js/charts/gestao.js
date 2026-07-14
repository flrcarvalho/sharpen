// ── gestao.js — Custos, Parceiros, Métricas, Custo Tipster ──────────────────────

// Parceiros / Fornecedores
function normForn(f){return(!f||f==='—')?'Eu':f;}

// Persistent cost store — ESCOPADO POR DONO (isolamento entre usuários).
// A chave inclui o dono: os custos de um usuário nunca aparecem para outro.
// window.__dono vem do feed /dashboard/data (app.js). Fallback '_' = namespace
// vazio → nunca cai no store de outro dono.
function costKey(){return 'dash_custos_v2::'+(window.__dono||'_');}
// Seed histórico dos custos do FECA — aplicado SÓ para o dono 'Feca' (jamais semeia
// outro usuário; global, era a fonte do vazamento — cada usuário preenche o seu).
const CUSTO_SEED={
  "Annderson||Bet365":900,"JC||Betano":600,"JC||Superbet":500,
  "Move||Betano":600,"Move||Bet365":950,"Move||Superbet":600,
  "P2Pro||Betano":600,"P2Pro||Superbet":600,
  "Richard||Bet365":800,"Richard||Betano":500,"Richard||Superbet":400
};
let custoData={};
// Carregado quando o dono é conhecido (app.js, após o feed). Idempotente.
function loadCusto(){
  const k=costKey();
  // migração única do store legado (sem dono) → namespace do Feca, só na 1ª vez.
  try{
    const legacy=localStorage.getItem('dash_custos_v2');
    if(legacy&&window.__dono==='Feca'&&!localStorage.getItem(k))localStorage.setItem(k,legacy);
  }catch(e){}
  try{custoData=JSON.parse(localStorage.getItem(k)||'null')||{};}catch(e){custoData={};}
  if((!custoData||!Object.keys(custoData).length)&&window.__dono==='Feca'){
    custoData={...CUSTO_SEED};          // seed só do Feca; demais donos começam vazios
    try{localStorage.setItem(k,JSON.stringify(custoData));}catch(e){}
  }
}
function saveCusto(forn,casa,val){
  const k=forn+'||'+casa;
  const n=parseFloat(val.replace(/\./g,'').replace(',','.'));
  if(!isNaN(n)&&n>0)custoData[k]=n; else delete custoData[k];
  try{localStorage.setItem(costKey(),JSON.stringify(custoData));}catch(e){}
  recalcCustos();
  renderCostPies();
  // Atualiza card de custo na visão geral e na aba fornecedores
  renderOvCusto();
  const{allForns,allCasas,contaCount}=_costState;
  if(allForns&&allForns.length)renderCustoCards(allForns,allCasas,contaCount);
}
let _costState={allForns:[],allCasas:[],contaCount:{}};

// Mapa de primeira aposta por conta: _firstBetMap["forn||casa"]["conta"] = "YYYY-MM-DD"
let _firstBetMap=null;
function _buildFirstBetMap(){
  _firstBetMap={};
  if(typeof DADOS==='undefined'||!DADOS.length)return;
  DADOS.forEach(r=>{
    const k=normForn(r.fornecedor)+'||'+r.casa;
    if(!_firstBetMap[k])_firstBetMap[k]={};
    const c=r.conta||'__default__';
    if(!_firstBetMap[k][c]||r.data<_firstBetMap[k][c])_firstBetMap[k][c]=r.data;
  });
}

// Custo filtrado por data E escopo: só contas cuja primeira aposta esteja em
// [minDate, maxDate] (custo pertence ao período de aquisição) E que apareçam nos
// rows filtrados (respeita filtros de casa/tipster/esporte — auditoria A3)
function calcCostFiltered(rows){
  if(!rows||!rows.length)return{costConta:0};
  if(!_firstBetMap)_buildFirstBetMap();
  const minDate=rows.reduce((m,r)=>r.data<m?r.data:m,'9999-99-99');
  const maxDate=rows.reduce((m,r)=>r.data>m?r.data:m,'0000-00-00');
  // Contas presentes no recorte filtrado (mesma chave de _firstBetMap)
  const scope=new Set();
  rows.forEach(r=>scope.add(normForn(r.fornecedor)+'||'+r.casa+'||'+(r.conta||'__default__')));
  let total=0;
  Object.entries(custoData).forEach(([k,custoPorConta])=>{
    const contaMap=_firstBetMap[k]||{};
    Object.entries(contaMap).forEach(([conta,firstDate])=>{
      if(firstDate>=minDate&&firstDate<=maxDate&&scope.has(k+'||'+conta))total+=custoPorConta;
    });
  });
  return{costConta:total};
}

// Custo filtrado para uma casa específica: para uso no popup drill-down de Bookies
function calcCasaCost(nomeCasa,minDate,maxDate){
  if(!_firstBetMap)_buildFirstBetMap();
  let total=0,nContas=0;
  Object.entries(custoData).forEach(([k,custoPorConta])=>{
    const[,casa]=k.split('||');
    if(casa!==nomeCasa)return;
    const contaMap=_firstBetMap[k]||{};
    Object.values(contaMap).forEach(firstDate=>{
      if(firstDate>=minDate&&firstDate<=maxDate){total+=custoPorConta;nContas++;}
    });
  });
  return{total,nContas};
}

function buildCostState(rows){
  if(typeof DADOS!=='undefined'&&DADOS.length)_buildFirstBetMap();
  const normRows=rows.map(r=>({...r,fornecedor:normForn(r.fornecedor)}));
  const allForns=[...new Set(normRows.map(r=>r.fornecedor))].sort();
  const allCasasRaw=[...new Set(normRows.map(r=>r.casa).filter(Boolean))];
  const contaMap={};
  normRows.forEach(r=>{const k=r.casa+'||'+r.fornecedor;if(!contaMap[k])contaMap[k]=new Set();contaMap[k].add(r.conta);});
  const contaCount={};
  allForns.forEach(f=>allCasasRaw.forEach(c=>{const s=contaMap[c+'||'+f];contaCount[f+'||'+c]=s?s.size:0;}));
  const casaTotal={};allCasasRaw.forEach(c=>{casaTotal[c]=allForns.reduce((a,f)=>a+(contaCount[f+'||'+c]||0),0);});
  const allCasas=allCasasRaw.slice().sort((a,b)=>(casaTotal[b]||0)-(casaTotal[a]||0));
  _costState={allForns,allCasas,contaCount};
  return _costState;
}

function recalcCustos(){
  const{allForns,allCasas,contaCount}=_costState;
  let grandTot=0;
  const fornTotals={};allForns.forEach(f=>fornTotals[f]=0);
  document.querySelectorAll('#costTbody tr[data-casa]').forEach(tr=>{
    const casa=tr.dataset.casa;
    let rowTot=0;
    allForns.forEach(f=>{
      const k=f+'||'+casa;
      const custo=custoData[k]||0;
      const nContas=contaCount[k]||0;
      const tot=custo*nContas;
      rowTot+=tot;
      fornTotals[f]+=tot;
      const totEl=tr.querySelector('[data-tot-forn="'+f+'"]');
      if(totEl)totEl.textContent=tot>0?'R$ '+fmt(tot,0):'—';
    });
    grandTot+=rowTot;
    const rowTotEl=tr.querySelector('.cost-row-total');
    if(rowTotEl)rowTotEl.textContent=rowTot>0?'R$ '+fmt(rowTot,0):'—';
  });
  allForns.forEach(f=>{
    const el=document.getElementById('cost-col-tot-'+CSS.escape(f));
    if(el)el.textContent=fornTotals[f]>0?'R$ '+fmt(fornTotals[f],0):'—';
  });
  const gt=document.getElementById('cost-grand-total');
  if(gt)gt.textContent=grandTot>0?'R$ '+fmt(grandTot,0):'—';
  _renderCustosKpi();
}

function _renderCustosKpi(){
  const el=document.getElementById('custosKpi');
  if(!el)return;
  const{allForns,allCasas,contaCount}=_costState;
  if(!allForns||!allForns.length){el.innerHTML='';return;}
  const fornTots={};
  allForns.forEach(f=>{fornTots[f]=allCasas.reduce((a,c)=>{const k=f+'||'+c;return a+(custoData[k]||0)*(contaCount[k]||0);},0);});
  const grandCost=Object.values(fornTots).reduce((a,v)=>a+v,0);
  const totalContas=allForns.reduce((a,f)=>a+allCasas.reduce((b,c)=>b+(contaCount[f+'||'+c]||0),0),0);
  const contasComPreco=allForns.reduce((a,f)=>a+allCasas.reduce((b,c)=>{const k=f+'||'+c;return b+((custoData[k]||0)>0?(contaCount[k]||0):0);},0),0);
  const avgCost=contasComPreco>0?grandCost/contasComPreco:0;
  const fornsAtivos=allForns.filter(f=>fornTots[f]>0).length;
  const mkK=(l,v,c,s)=>`<div class="kpi"><div class="kpi-label"><span class="kpi-pipe"></span> ${l}</div><div class="kpi-val ${c}">${v}</div><div class="kpi-sub">${s}</div></div>`;
  el.innerHTML=`<div class="kpi-grid" style="margin-bottom:1.25rem">
    ${mkK('Total de Custos',grandCost>0?'R$ '+fmt(grandCost,0):'—','neu',contasComPreco+' contas com custo')}
    ${mkK('Custo Médio/Conta',avgCost>0?'R$ '+fmt(avgCost,0):'—','neu','entre contas com custo')}
    ${mkK('Contas Ativas',totalContas||'—','neu',contasComPreco+' com preço definido')}
    ${mkK('Fornecedores',fornsAtivos||'—','neu',allForns.length+' no total')}
  </div>`;
}

function renderCostPies(){
  const{allForns,allCasas,contaCount}=_costState;
  if(!document.getElementById('chartCostForn'))return;
  const fornTots={};
  allForns.forEach(f=>{fornTots[f]=allCasas.reduce((a,c)=>{const k=f+'||'+c;return a+(custoData[k]||0)*(contaCount[k]||0);},0);});
  const fEnts=Object.entries(fornTots).filter(e=>e[1]>0).sort((a,b)=>b[1]-a[1]);
  const casaTots={};
  allCasas.forEach(c=>{casaTots[c]=allForns.reduce((a,f)=>{const k=f+'||'+c;return a+(custoData[k]||0)*(contaCount[k]||0);},0);});
  const cEnts=Object.entries(casaTots).filter(e=>e[1]>0).sort((a,b)=>b[1]-a[1]);
  const PIE_COLORS=['#2BC07E','#2E8BFF','#E0A21A','#7FB2FF','#95A1B0','#E5524B','#4FC79A','#D6A45A','#4DA3FF','#AEB7C2','#5E6775','#E0A21A','#1E7CF0','#AEB7C2','#4DA3FF'];
  if(!fEnts.length){destroyChart('chartCostForn');destroyChart('chartCostCasa');return;}
  const txtColor=isDark()?'#eeedf0':'#0f0f18';
  const pieOpts=(totalVal)=>({responsive:true,maintainAspectRatio:false,cutout:'62%',plugins:{
    legend:{display:true,position:'bottom',align:'center',labels:{
      color:txtColor,
      font:{size:11,family:"'Manrope',sans-serif"},
      boxWidth:10,boxHeight:10,padding:10,borderRadius:3,useBorderRadius:true,
      generateLabels(chart){const ds=chart.data.datasets[0];return chart.data.labels.map((lbl,i)=>{
        const v=ds.data[i];const pct=totalVal>0?fmtPct(v/totalVal*100,1,false):'0%';
        const shortLbl=lbl.length>14?lbl.slice(0,13)+'…':lbl;
        return{text:`${shortLbl}  ${pct}  ·  R$${fmt(v,0)}`,fillStyle:ds.backgroundColor[i],strokeStyle:'transparent',hidden:false,index:i};
      });}}},
    tooltip:{callbacks:{label:ctx=>{const pct=totalVal>0?fmtPct(ctx.raw/totalVal*100,1,false):'0%';return`${ctx.label}: R$ ${fmt(ctx.raw,0)} (${pct})`}}}}});
  const fTotal=fEnts.reduce((a,e)=>a+e[1],0);
  mkChart('chartCostForn',{type:'doughnut',data:{labels:fEnts.map(e=>e[0]),datasets:[{data:fEnts.map(e=>parseFloat(e[1].toFixed(2))),backgroundColor:PIE_COLORS.slice(0,fEnts.length),borderWidth:3,borderColor:isDark()?'#0A0D12':'#fff',hoverOffset:8}]},options:pieOpts(fTotal)});
  const cTotal=cEnts.reduce((a,e)=>a+e[1],0);
  mkChart('chartCostCasa',{type:'doughnut',data:{labels:cEnts.map(e=>e[0]),datasets:[{data:cEnts.map(e=>parseFloat(e[1].toFixed(2))),backgroundColor:PIE_COLORS.slice(0,cEnts.length),borderWidth:3,borderColor:isDark()?'#0A0D12':'#fff',hoverOffset:8}]},options:pieOpts(cTotal)});
}

function buildCostTable(allForns,allCasas,contaCount){
  _costState={allForns,allCasas,contaCount};
  // ── header ──
  const nCols=allForns.map(f=>`<th style="text-align:center;min-width:70px">${esc(f)}<br><span style="font-size:9px;color:var(--accent);font-weight:400;font-family:'JetBrains Mono',monospace">Contas</span></th>`).join('');
  const cCols=allForns.map(f=>`<th style="text-align:center;min-width:100px">${esc(f)}<br><span style="font-size:9px;color:var(--warn);font-weight:400;font-family:'JetBrains Mono',monospace">Custo/conta</span></th>`).join('');
  const tCols=allForns.map(f=>`<th style="text-align:center;min-width:90px">${esc(f)}<br><span style="font-size:9px;color:var(--pos);font-weight:400;font-family:'JetBrains Mono',monospace">Total</span></th>`).join('');
  const header=`<tr><th style="text-align:left;position:sticky;left:0;background:var(--field);z-index:2;min-width:140px">Casa</th>${nCols}${cCols}${tCols}<th style="text-align:center;border-left:1px solid var(--line);min-width:100px">Total Geral</th></tr>`;

  // ── total row (topo) ──
  const grandTot=allCasas.reduce((a,c)=>a+allForns.reduce((b,f)=>{const k=f+'||'+c;return b+(custoData[k]||0)*(contaCount[k]||0);},0),0);
  const totNcols=allForns.map(f=>{const n=allCasas.reduce((a,c)=>a+(contaCount[f+'||'+c]||0),0);return`<td style="text-align:center;font-weight:700;font-family:'JetBrains Mono',monospace;font-size:11px">${n||'—'}</td>`;}).join('');
  const totEmptyCols=allForns.map(()=>`<td></td>`).join('');
  const totFornCols=allForns.map(f=>{const tot=allCasas.reduce((a,c)=>{const k=f+'||'+c;return a+(custoData[k]||0)*(contaCount[k]||0);},0);return`<td id="cost-col-tot-${esc(f)}" style="text-align:center;font-weight:700;font-family:'JetBrains Mono',monospace;font-size:11px">${tot>0?'R$ '+fmt(tot,0):'—'}</td>`;}).join('');
  const totalRow=`<tr class="total-row" style="border-bottom:2px solid var(--line)"><td style="position:sticky;left:0;background:var(--field);z-index:1;font-weight:700">Total</td>${totNcols}${totEmptyCols}${totFornCols}<td id="cost-grand-total" style="text-align:center;font-weight:700;border-left:1px solid var(--line);font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--warn)">${grandTot>0?'R$ '+fmt(grandTot,0):'—'}</td></tr>`;

  // ── body rows ──
  const bodyRows=allCasas.map(c=>{
    const nCells=allForns.map(f=>{const n=contaCount[f+'||'+c]||0;return`<td style="text-align:center;font-weight:600;color:${n>0?'var(--ink)':'var(--ink-mute)'};font-family:'JetBrains Mono',monospace;font-size:11px">${n||'—'}</td>`;}).join('');
    const inputCells=allForns.map(f=>{
      const k=f+'||'+c;const saved=custoData[k]?custoData[k].toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2}):'';const n=contaCount[k]||0;
      // safe_*: JS-string escaping (\ e ') + HTML-escaping (esc) — entram em onclick/onblur="…'…'…"
      const safe_f=esc(f.replace(/\\/g,'\\\\').replace(/'/g,"\\'"));const safe_c=esc(c.replace(/\\/g,'\\\\').replace(/'/g,"\\'"));
      return`<td style="text-align:center;padding:3px 5px">${n>0?`<input type="text" value="${esc(saved)}" placeholder="0,00" style="width:84px;text-align:right;padding:3px 7px;background:var(--elevated);border:1px solid var(--line);color:var(--ink);border-radius:4px;font-family:'JetBrains Mono',monospace;font-size:11px;outline:none" onfocus="this.style.borderColor='var(--pos)'" onblur="this.style.borderColor='var(--line)';saveCusto('${safe_f}','${safe_c}',this.value)" onkeydown="if(event.key==='Enter')this.blur()">`:'<span style="color:var(--ink-mute);font-size:11px">—</span>'}</td>`;
    }).join('');
    const totalCells=allForns.map(f=>{const k=f+'||'+c;const n=contaCount[k]||0;const custo=custoData[k]||0;const tot=custo*n;return`<td data-tot-forn="${esc(f)}" style="text-align:center;font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--ink-soft)">${tot>0?'R$ '+fmt(tot,0):'—'}</td>`;}).join('');
    const rowTot=allForns.reduce((a,f)=>{const k=f+'||'+c;return a+(custoData[k]||0)*(contaCount[k]||0);},0);
    return`<tr data-casa="${esc(c)}"><td style="font-weight:600;color:var(--ink);position:sticky;left:0;background:var(--surface-2);z-index:1;padding:4px 8px">${casaCell(c)}</td>${nCells}${inputCells}${totalCells}<td class="cost-row-total" style="text-align:center;font-weight:700;border-left:1px solid var(--line);font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--ink)">${rowTot>0?'R$ '+fmt(rowTot,0):'—'}</td></tr>`;
  }).join('');

  document.getElementById('costTableWrap').innerHTML=`
    <p style="font-size:11px;color:var(--ink-mute);margin-bottom:.75rem;font-family:var(--font-sans)">💡 Insira o custo de cada conta comprada por fornecedor/casa. O total é calculado pelo nº de contas ativas. Valores salvos automaticamente no navegador.</p>
    <div class="tbl-wrap"><table class="tbl" id="tblCost"><thead>${header}</thead><tbody id="costTbody">${totalRow}${bodyRows}</tbody></table></div>`;
  setTimeout(()=>makeSortable('tblCost',[]),100);
  renderCostPies();
}

function renderParceiros(rows){
  const normRows=rows.map(r=>({...r,fornecedor:normForn(r.fornecedor)}));
  // ── Resumo por fornecedor ──
  const byForn={};
  normRows.forEach(r=>{const f=r.fornecedor;if(!byForn[f])byForn[f]={l:0,s:0,n:0,contas:new Set()};byForn[f].l+=r.lucro;if(r.resultado!=='V')byForn[f].s+=r.stake;byForn[f].n++;byForn[f].contas.add(r.conta);});
  const fornEnts=Object.entries(byForn).sort((a,b)=>b[1].l-a[1].l);
  const parcKpiEl=document.getElementById('parcKpiGrid');
  if(parcKpiEl)parcKpiEl.innerHTML=mkKpiGrid(normRows,{plLabel:'P/L dos Parceiros',contextLabel:'Fornecedores',contextVal:fornEnts.length,contextSub:fornEnts.map(e=>e[0]).join(' · ')});
  const fornNames=fornEnts.map(e=>e[0]);const fornVals=fornEnts.map(e=>parseFloat(e[1].l.toFixed(2)));
  mkChart('chartForn',{type:'bar',data:{labels:fornNames,datasets:[{data:fornVals,backgroundColor:fornVals.map(v=>v>=0?'rgba(0,214,143,.65)':'rgba(240,80,110,.65)'),borderRadius:4}]},options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx=>'R$ '+fmt(ctx.raw)}}},scales:{x:{ticks:{color:tc(),font:{size:10},callback:v=>'R$'+fmt(v,0)},grid:{color:gc()},border:{display:false}},y:{ticks:{color:tc(),font:{size:11}},grid:{display:false},border:{display:false}}}}});
  const{allForns,allCasas,contaCount}=buildCostState(rows);
  const casaTotal={};allCasas.forEach(c=>{casaTotal[c]=allForns.reduce((a,f)=>a+(contaCount[f+'||'+c]||0),0);});

  // Resumo com custo integrado
  const fornRows=fornEnts.map(([f,d])=>{
    const roi=d.s>0?(d.l/d.s*100):0;
    const custo=allCasas.reduce((a,c)=>{const k=f+'||'+c;return a+(custoData[k]||0)*(contaCount[k]||0);},0);
    const lc=d.l>=0?'color:var(--pos)':'color:var(--neg)';
    const rc=roi>=0?'color:var(--pos)':'color:var(--neg)';
    const cc=custo>0?'color:var(--warn)':'color:var(--ink-mute)';
    return`<tr><td style="font-weight:700;color:var(--ink)">${esc(f)}</td><td>${d.contas.size}</td><td>${d.n}</td><td>${fmtR(d.s)}</td><td style="${lc}">${fmtPL(d.l)}</td><td style="${rc}">${fmtPct(roi,2)}</td><td style="${cc}">${custo>0?'R$ '+fmt(custo,0):'—'}</td></tr>`;
  }).join('');
  const totFornPL=fornEnts.reduce((a,[,d])=>a+d.l,0);
  const totFornS=fornEnts.reduce((a,[,d])=>a+d.s,0);
  const totFornN=fornEnts.reduce((a,[,d])=>a+d.n,0);
  const totFornContas=fornEnts.reduce((a,[,d])=>a+d.contas.size,0);
  const totFornCusto=fornEnts.reduce((a,[f])=>a+allCasas.reduce((b,c)=>{const k=f+'||'+c;return b+(custoData[k]||0)*(contaCount[k]||0);},0),0);
  const totFornROI=totFornS>0?(totFornPL/totFornS*100):0;
  const totFornLC=totFornPL>=0?'color:var(--pos)':'color:var(--neg)';
  const totFornRC=totFornROI>=0?'color:var(--pos)':'color:var(--neg)';
  const fornTotalRow=`<tr class="total-row"><td style="font-weight:700">Total</td><td>${totFornContas}</td><td>${totFornN}</td><td>${fmtR(totFornS)}</td><td style="${totFornLC}">${fmtPL(totFornPL)}</td><td style="${totFornRC}">${fmtPct(totFornROI,2)}</td><td style="color:var(--warn)">${totFornCusto>0?'R$ '+fmt(totFornCusto,0):'—'}</td></tr>`;
  document.getElementById('fornTable').innerHTML=`<table class="tbl" id="tblForn"><thead><tr><th>Fornecedor<span class="sort-icon"></span></th><th>Contas<span class="sort-icon"></span></th><th>Apostas<span class="sort-icon"></span></th><th>Turnover<span class="sort-icon"></span></th><th>Lucro<span class="sort-icon"></span></th><th>ROI<span class="sort-icon"></span></th><th>Custo<span class="sort-icon"></span></th></tr></thead><tbody>${fornTotalRow}${fornRows}</tbody></table>`;
  setTimeout(()=>makeSortable('tblForn',[1,2,3,4,5,6]),100);
  const grandTotal=allCasas.reduce((a,c)=>a+(casaTotal[c]||0),0);
  const totRowCross=`<tr class="total-row" style="border-bottom:2px solid var(--line)"><td style="position:sticky;left:0;background:var(--field);z-index:1;font-weight:700">Total</td>${allForns.map(f=>{const n=allCasas.reduce((a,c)=>a+(contaCount[f+'||'+c]||0),0);return`<td style="text-align:center;font-weight:700">${n||'—'}</td>`;}).join('')}<td style="text-align:center;font-weight:700;border-left:1px solid var(--line)">${grandTotal}</td></tr>`;
  const crossHeader=`<tr><th style="text-align:left;position:sticky;left:0;background:var(--field);z-index:2">Casa</th>${allForns.map(f=>`<th style="text-align:center">${esc(f)}<span class="sort-icon"></span></th>`).join('')}<th style="text-align:center;border-left:1px solid var(--line)">Total<span class="sort-icon"></span></th></tr>`;
  const crossRows=allCasas.map(c=>{const cells=allForns.map(f=>{const n=contaCount[f+'||'+c]||0;return`<td style="text-align:center;color:${n>0?'var(--ink)':'var(--ink-mute)'}">${n||'—'}</td>`;}).join('');const tot=casaTotal[c];return`<tr><td style="font-weight:600;color:var(--ink);position:sticky;left:0;background:var(--surface-2);z-index:1;padding:4px 8px">${casaCell(c)}</td>${cells}<td style="text-align:center;font-weight:700;border-left:1px solid var(--line)">${tot||'—'}</td></tr>`;}).join('');
  document.getElementById('crossTable').innerHTML=`<div class="tbl-wrap"><table class="tbl" id="tblCross"><thead>${crossHeader}</thead><tbody>${totRowCross}${crossRows}</tbody></table></div>`;
  setTimeout(()=>{makeSortable('tblCross',[...Array(allForns.length+1).keys()].slice(1));},100);

  // ── Cards de custo por fornecedor (lê custoData salvo) ──
  renderCustoCards(allForns,allCasas,contaCount);


  // ── Contas Individuais ──
  const map={};
  normRows.forEach(r=>{const key=r.fornecedor+'||'+r.conta+'||'+r.casa;if(!map[key])map[key]={conta:r.conta,forn:r.fornecedor,casa:r.casa,n:0,s:0,l:0,datas:[]};map[key].n++;if(r.resultado!=='V')map[key].s+=r.stake;map[key].l+=r.lucro;map[key].datas.push(r.data);});
  const accRows=Object.values(map).sort((a,b)=>b.l-a.l).map(e=>{const roi=e.s>0?(e.l/e.s*100):0;const lc=e.l>=0?'color:var(--pos)':'color:var(--neg)';const rc=roi>=0?'color:var(--pos)':'color:var(--neg)';const sorted=e.datas.slice().sort();const d1=sorted[0].slice(0,10).split('-'),d2=sorted[sorted.length-1].slice(0,10).split('-');const dias=Math.round((new Date(sorted[sorted.length-1])-new Date(sorted[0]))/864e5);return`<tr><td style="font-weight:700;color:var(--ink)">${esc(e.forn)}</td><td>${esc(e.conta)}</td><td>${casaCell(e.casa)}</td><td>${e.n}</td><td>${fmtR(e.s)}</td><td style="${lc}">${fmtPL(e.l)}</td><td style="${rc}">${fmtPct(roi,1)}</td><td>${d1[2]}/${d1[1]}/${d1[0].slice(2)}</td><td>${d2[2]}/${d2[1]}/${d2[0].slice(2)}</td><td>${dias}d</td></tr>`;}).join('');
  document.getElementById('parcTable').innerHTML=`<table class="tbl" id="tblParc"><thead><tr><th>Fornecedor<span class="sort-icon"></span></th><th>Conta<span class="sort-icon"></span></th><th>Casa<span class="sort-icon"></span></th><th>Bets<span class="sort-icon"></span></th><th>Turnover<span class="sort-icon"></span></th><th>Profit<span class="sort-icon"></span></th><th>ROI<span class="sort-icon"></span></th><th>1ª Aposta<span class="sort-icon"></span></th><th>Última<span class="sort-icon"></span></th><th>Período<span class="sort-icon"></span></th></tr></thead><tbody>${accRows}</tbody></table>`;
  setTimeout(()=>makeSortable('tblParc',[3,4,5,6,9]),100);
}

// ── Custo cards na aba Fornecedores ──
function renderCustoCards(allForns,allCasas,contaCount){
  const el=document.getElementById('fornCustoCards');
  if(!el)return;
  const PIE_COLORS=['#2BC07E','#2E8BFF','#E0A21A','#7FB2FF','#95A1B0','#E5524B','#4FC79A','#D6A45A','#4DA3FF','#AEB7C2','#5E6775'];
  const fornTots={};
  allForns.forEach(f=>{fornTots[f]=allCasas.reduce((a,c)=>{const k=f+'||'+c;return a+(custoData[k]||0)*(contaCount[k]||0);},0);});
  const grandCost=Object.values(fornTots).reduce((a,v)=>a+v,0);

  if(!grandCost){
    el.innerHTML=`<div style="text-align:center;padding:2rem;font-size:12px;color:var(--ink-mute);font-family:var(--font-sans)">
      💡 Preencha os custos de contas na aba <strong style="color:var(--warn)">Custos de Contas</strong> para ver o resumo aqui.
    </div>`;
    return;
  }

  const totalContas=allForns.reduce((a,f)=>a+allCasas.reduce((b,c)=>b+(contaCount[f+'||'+c]||0),0),0);
  const contasComPreco=allForns.reduce((a,f)=>a+allCasas.reduce((b,c)=>{const k=f+'||'+c;return b+((custoData[k]||0)>0?(contaCount[k]||0):0);},0),0);
  const avgCostPago=contasComPreco>0?grandCost/contasComPreco:0;

  // Card total consolidado
  const totalCard=`<div style="background:var(--surface);border:1px solid var(--line);border-radius:var(--r-lg);padding:20px 22px;min-width:200px;flex-shrink:0;display:flex;flex-direction:column;justify-content:center">
    <div style="font-size:10px;font-weight:700;color:var(--ink-mute);text-transform:uppercase;letter-spacing:.08em;margin-bottom:.5rem;font-family:'JetBrains Mono',monospace">Total</div>
    <div style="font-size:26px;font-weight:700;color:var(--warn);font-family:'JetBrains Mono',monospace;letter-spacing:-.02em">R$ ${fmt(grandCost,0)}</div>
    <div style="font-size:11px;color:var(--ink-soft);font-family:'JetBrains Mono',monospace;margin-top:4px">${contasComPreco} contas · R$${fmt(avgCostPago,0)}/conta</div>
    <div style="font-size:10px;color:var(--ink-mute);font-family:'JetBrains Mono',monospace;margin-top:2px">${allForns.filter(f=>fornTots[f]>0).length} fornecedores</div>
  </div>`;

  // Apenas os cards por fornecedor
  const fornCards=allForns.filter(f=>fornTots[f]>0).sort((a,b)=>fornTots[b]-fornTots[a]).map((f,i)=>{
    const tot=fornTots[f];
    const pct=grandCost>0?(tot/grandCost*100).toFixed(1):0;
    const nContas=allCasas.reduce((a,c)=>a+(contaCount[f+'||'+c]||0),0);
    const nPago=allCasas.reduce((a,c)=>{const k=f+'||'+c;return a+((custoData[k]||0)>0?(contaCount[k]||0):0);},0);
    const avgF=nPago>0?tot/nPago:0;
    const color=PIE_COLORS[i%PIE_COLORS.length];
    const casasComCusto=allCasas.filter(c=>{const k=f+'||'+c;return (custoData[k]||0)>0&&(contaCount[k]||0)>0;});
    const casasF=casasComCusto.sort((a,b)=>{const ka=f+'||'+a,kb=f+'||'+b;return (custoData[kb]||0)*(contaCount[kb]||0)-(custoData[ka]||0)*(contaCount[ka]||0);}).slice(0,5);
    const casaRows=casasF.map(c=>{
      const k=f+'||'+c;const custo=custoData[k]||0;const n=contaCount[k]||0;const subtot=custo*n;
      return`<div style="display:flex;align-items:center;justify-content:space-between;padding:4px 0;border-bottom:1px solid var(--line-2)">
        <div style="display:flex;align-items:center;gap:6px;font-size:11px;color:var(--ink-soft)">${casaCell(c)}</div>
        <div style="text-align:right;font-size:11px;font-family:'JetBrains Mono',monospace">
          <span style="color:var(--ink-mute)">${n}×R$${fmt(custo,0)}</span>
          <span style="color:var(--ink);font-weight:600;margin-left:8px">R$${fmt(subtot,0)}</span>
        </div>
      </div>`;
    }).join('');
    const moreCount=casasComCusto.length-5;
    return`<div style="background:var(--surface);border:1px solid var(--line);border-top:2px solid ${color};border-radius:var(--r-lg);padding:20px 22px;flex:1;min-width:220px;max-width:340px">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:.5rem">
        <div style="width:8px;height:8px;border-radius:50%;background:${color};flex-shrink:0"></div>
        <div style="font-size:13px;font-weight:700;color:var(--ink)">${esc(f)}</div>
        <div style="margin-left:auto;font-size:10px;font-family:'JetBrains Mono',monospace;color:var(--ink-mute)">${pct}% do total</div>
      </div>
      <div style="font-size:24px;font-weight:700;color:var(--warn);font-family:'JetBrains Mono',monospace;letter-spacing:-.02em;margin-bottom:2px">R$ ${fmt(tot,0)}</div>
      <div style="font-size:10px;color:var(--ink-mute);font-family:'JetBrains Mono',monospace;margin-bottom:.75rem">${nContas} contas · média R$${fmt(avgF,0)}/conta</div>
      <div>${casaRows}</div>
      ${moreCount>0?`<div style="font-size:10px;color:var(--ink-mute);font-family:'JetBrains Mono',monospace;margin-top:5px;text-align:center">+ ${moreCount} casas</div>`:''}
    </div>`;
  }).join('');

  el.innerHTML=`<div style="display:flex;flex-wrap:wrap;gap:.75rem">${totalCard}${fornCards}</div>`;
}

// ── Aba Custos de Contas ──
function renderCustos(rows){
  // rows vem do filtrarPagina — sempre disponível após o fetch
  const fonte=rows&&rows.length?rows:DADOS;
  if(!fonte||!fonte.length){
    const wrap=document.getElementById('costTableWrap');
    if(wrap)wrap.innerHTML=`<div style="text-align:center;padding:2rem;color:var(--ink-mute);font-family:var(--font-sans);font-size:12px">Aguardando carregamento dos dados...</div>`;
    return;
  }
  // Sempre usa DADOS completo para o estado (custos devem refletir todas as contas, não filtradas)
  buildCostState(DADOS.length?DADOS:fonte);
  const{allForns,allCasas,contaCount}=_costState;
  buildCostTable(allForns,allCasas,contaCount);
  _renderCustosKpi();
}

// Metrics knowledge base — preenche a faixa de KPIs de resumo e o badge de valor
// ao vivo (#mv_*) de cada card. Todos os cálculos vêm das funções canônicas de app.js.
function renderMetrics(rows){
  // Fundamentais
  const pl=rows.reduce((a,r)=>a+(r.lucro||0),0);
  const roi=calcROI(rows),wr=calcWR(rows),avgOdd=calcAvgOdd(rows);
  const turn=calcTurnover(rows);
  const settled=rows.filter(r=>r.resultado!=='V').length;
  const avgStake=settled>0?turn/settled:0;
  // Risco & Drawdown
  const dr=calcDrawdownReal(rows),mddR=dr.mddReais,mddPct=dr.mddPct;
  const rf=calcRecoveryFactor(rows);
  // Bootstrap dos P/L reais (mesmo motor dos drill-downs): média = drawdown típico,
  // p95 = cauda de risco, p99 = cauda extrema.
  const _mc=calcMCdrawdown(rows,10000),xmdd=_mc.xmdd,ddP95=_mc.p95,ddP99=_mc.p99;
  const profDdRaw=xmdd>0?pl/xmdd:null;
  // Significância
  const pval=calcPValueMC(rows,10000);
  const sol=calcSolidez({pValue:pval,profitXmdd:profDdRaw!==null?profDdRaw:0,nApostas:rows.length,oddMedia:avgOdd});

  // Preenche um badge: só o texto se cls===undefined (mantém a classe semântica do markup);
  // troca a classe quando o sinal/limiar é dinâmico (ROI, P/L, RF, Profit/DD, P-Value, Solidez).
  const setLive=(id,txt,cls)=>{const el=document.getElementById(id);if(!el)return;el.textContent=txt;if(cls!==undefined)el.className='metric-live'+(cls?' '+cls:'');};
  const plTxt=(pl>=0?'+R$ ':'−R$ ')+fmt(pl,0);

  setLive('mv_roi',fmtPct(roi,2,true),roi>=0?'pos':'neg');
  setLive('mv_turnover','R$ '+fmt(turn,0));
  setLive('mv_wr',fmtPct(wr,1,false));
  setLive('mv_odd',fmtOdd(avgOdd));
  setLive('mv_stake','R$ '+fmt(avgStake,0));
  setLive('mv_pl',plTxt,pl>=0?'pos':'neg');

  setLive('mv_mdd_r','R$ '+fmt(mddR,0));
  setLive('mv_mdd_p',fmtPct(mddPct,2,false));
  setLive('mv_rf',rf===null?'—':fmtOdd(rf)+'×',rf===null?'neu':rf>=2?'d-pos':rf>=1?'d-info':'d-neg');
  setLive('mv_xmdd','R$ '+fmt(xmdd,0));
  setLive('mv_p95','R$ '+fmt(ddP95,0));
  setLive('mv_p99','R$ '+fmt(ddP99,0));
  setLive('mv_pdd',profDdRaw===null?'—':fmtOdd(profDdRaw)+'×',profDdRaw===null?'neu':profDdRaw>=2?'d-pos':profDdRaw>=1?'d-info':'d-neg');

  setLive('mv_pval',pval<0.001?'< 0,001':fmt(pval,3),pval<0.05?'d-pos':pval<0.15?'d-info':'neu');
  setLive('mv_solidez',sol.faixa,sol.score>=0.65?'d-pos':sol.score>=0.45?'d-info':sol.score>=0.25?'d-proj':'d-neg');

  // Faixa de KPIs no topo — resumo headline (não duplica os cards)
  document.getElementById('metricsKPI').innerHTML=[
    {l:'P/L Líquido',v:plTxt,c:pl>=0?'pos':'neg'},
    {l:'ROI',v:fmtPct(roi,2,true),c:roi>=0?'pos':'neg'},
    {l:'Win Rate',v:fmtPct(wr,1,false),c:'neu'},
    {l:'MDD Real',v:'R$ '+fmt(mddR,0),c:mddPct<15?'pos':mddPct<30?'neu':'neg'},
    {l:'Drawdown Médio',v:'R$ '+fmt(xmdd,0),c:'neu'},
    {l:'Nível de Solidez',v:sol.faixa,c:sol.score>=0.65?'pos':sol.score>=0.45?'neu':'neg'},
  ].map(k=>`<div class="kpi"><div class="kpi-label">${k.l}</div><div class="kpi-val ${k.c}">${k.v}</div></div>`).join('');
}

// Build HTML
function renderCustoTipster(){
  ctLoad();
  const cont=document.getElementById('custoTipsterContent');
  if(!cont)return;
  const tipsters=[...new Set(DADOS.map(r=>r.tipster).filter(Boolean))].sort();
  const months=ctGetMonths();

  // ── CUSTOS GERAIS ──
  function buildCGRows(){
    return cgData.map((row,idx)=>{
      const totalRow=months.reduce((a,m)=>a+(parseFloat((row.values[m]||'').toString().replace(',','.'))||0),0);
      const vals=months.map(m=>{
        const v=row.values[m]||'';
        return`<td style="padding:3px 5px;text-align:center"><input type="text" value="${esc(v)}" placeholder="0,00" data-cgidx="${idx}" data-cgm="${esc(m)}" style="width:74px;text-align:right;padding:3px 7px;background:var(--elevated);border:1px solid var(--line);color:var(--ink);border-radius:4px;font-family:'JetBrains Mono',monospace;font-size:11px;outline:none" onfocus="this.style.borderColor='var(--pos)'" onblur="this.style.borderColor='var(--line)';saveCG(this)" onkeydown="if(event.key==='Enter')this.blur()"></td>`;
      }).join('');
      const tc2=totalRow>0?'color:var(--warn)':'color:var(--ink-mute)';
      return`<tr>
        <td style="padding:4px 8px"><input type="text" value="${esc(row.tipo||'')}" placeholder="Descrição do custo" data-cgidx="${idx}" data-cgtipo="1" style="width:160px;padding:3px 7px;background:var(--elevated);border:1px solid var(--line);color:var(--ink);border-radius:4px;font-family:var(--font-sans);font-size:12px;outline:none;font-weight:600" onfocus="this.style.borderColor='var(--pos)'" onblur="this.style.borderColor='var(--line)';saveCGTipo(this)" onkeydown="if(event.key==='Enter')this.blur()"></td>
        ${vals}
        <td style="text-align:center;font-weight:700;font-family:'JetBrains Mono',monospace;font-size:11px;border-left:1px solid var(--line);padding:0 8px;${tc2}">${totalRow>0?'R$ '+fmt(totalRow,0):'—'}</td>
        <td style="text-align:center;padding:0 6px"><button onclick="deleteCG(${idx})" style="background:none;border:none;cursor:pointer;color:var(--ink-mute);font-size:13px;line-height:1;padding:2px 4px;border-radius:3px" onmouseover="this.style.color='var(--neg)'" onmouseout="this.style.color='var(--ink-mute)'">✕</button></td>
      </tr>`;
    }).join('');
  }

  function buildCGTotal(){
    return months.map(m=>{
      const tot=cgData.reduce((a,r)=>a+(parseFloat((r.values[m]||'').toString().replace(',','.'))||0),0);
      return`<td style="text-align:center;font-weight:700;font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--warn)">${tot>0?'R$ '+fmt(tot,0):'—'}</td>`;
    }).join('');
  }

  // ── CUSTO TIPSTERS ──
  function buildCTRows(){
    return tipsters.map(t=>{
      if(!ctData[t])ctData[t]={};
      const totalT=months.reduce((a,m)=>a+(parseFloat((ctData[t][m]||'').toString().replace(',','.'))||0),0);
      const vals=months.map(m=>{
        const v=ctData[t][m]||'';
        return`<td style="padding:3px 5px;text-align:center"><input type="text" value="${esc(v)}" placeholder="0,00" data-ct="${esc(t)}" data-ctm="${esc(m)}" style="width:74px;text-align:right;padding:3px 7px;background:var(--elevated);border:1px solid var(--line);color:var(--ink);border-radius:4px;font-family:'JetBrains Mono',monospace;font-size:11px;outline:none" onfocus="this.style.borderColor='var(--pos)'" onblur="this.style.borderColor='var(--line)';saveCT(this)" onkeydown="if(event.key==='Enter')this.blur()"></td>`;
      }).join('');
      const tc2=totalT>0?'color:var(--warn)':'color:var(--ink-mute)';
      return`<tr><td style="font-weight:700;color:var(--ink);padding:4px 8px">${esc(t)}</td>${vals}<td style="text-align:center;font-weight:700;font-family:'JetBrains Mono',monospace;font-size:11px;border-left:1px solid var(--line);padding:0 8px;${tc2}">${totalT>0?'R$ '+fmt(totalT,0):'—'}</td></tr>`;
    }).join('');
  }

  function buildCTTotal(){
    return months.map(m=>{
      const tot=tipsters.reduce((a,t)=>a+(parseFloat(((ctData[t]||{})[m]||'').toString().replace(',','.'))||0),0);
      return`<td style="text-align:center;font-weight:700;font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--warn)">${tot>0?'R$ '+fmt(tot,0):'—'}</td>`;
    }).join('');
  }

  const monthHdrs=months.map(m=>`<th style="text-align:center;min-width:90px">${ctFmtMonth(m)}</th>`).join('');

  const _ctTotal=Object.values(ctData).reduce((a,m)=>a+Object.values(m).reduce((b,v)=>b+(parseFloat((v||'').toString().replace(',','.'))||0),0),0);
  const _cgTotal=cgData.reduce((a,r)=>a+Object.values(r.values||{}).reduce((b,v)=>b+(parseFloat((v||'').toString().replace(',','.'))||0),0),0);
  const _ctGrand=_ctTotal+_cgTotal;
  const _tipsCom=Object.keys(ctData).filter(t=>Object.values(ctData[t]||{}).some(v=>(parseFloat((v||'').toString().replace(',','.'))||0)>0)).length;
  const _mkKt=(l,v,c,s)=>`<div class="kpi"><div class="kpi-label"><span class="kpi-pipe"></span> ${l}</div><div class="kpi-val ${c}">${v}</div><div class="kpi-sub">${s}</div></div>`;
  const _ctKpiHTML=`<div class="kpi-grid" style="margin-bottom:1.25rem">
    ${_mkKt('Total Geral',_ctGrand>0?'R$ '+fmt(_ctGrand,0):'—','neu','tipsters + gerais')}
    ${_mkKt('Custo Tipsters',_ctTotal>0?'R$ '+fmt(_ctTotal,0):'—','neu',_tipsCom+' tipster(s) com custo')}
    ${_mkKt('Custos Gerais',_cgTotal>0?'R$ '+fmt(_cgTotal,0):'—','neu',cgData.length+' categori'+(cgData.length===1?'a':'as'))}
    ${_mkKt('Tipsters com Custo',_tipsCom||'—','neu',tipsters.length+' tipsters no total')}
  </div>`;

  cont.innerHTML=_ctKpiHTML+`
    <div style="margin-bottom:1rem">
      ${mkCard('cg_table','Custos Gerais',`
        <p style="font-size:11px;color:var(--ink-mute);margin-bottom:.75rem">💡 Adicione qualquer custo fixo ou variável: VPN, ferramentas, taxas, etc. Preencha mensalmente. Valores salvos no navegador.</p>
        <div class="tbl-wrap"><table class="tbl" id="tblCG">
          <thead><tr><th style="text-align:left;min-width:180px">Tipo / Descrição</th>${monthHdrs}<th style="text-align:center;border-left:1px solid var(--line)">Total</th><th></th></tr></thead>
          <tbody id="cgTbody">
            <tr class="total-row"><td style="font-weight:700">Total</td>${buildCGTotal()}<td style="border-left:1px solid var(--line)"></td><td></td></tr>
            ${buildCGRows()}
          </tbody>
        </table></div>
        <button onclick="addCG()" style="margin-top:.75rem;padding:5px 14px;background:transparent;border:1px solid var(--line);color:var(--ink-soft);border-radius:5px;cursor:pointer;font-size:11px;font-family:var(--font-sans);display:flex;align-items:center;gap:5px" onmouseover="this.style.borderColor='var(--pos)';this.style.color='var(--pos)'" onmouseout="this.style.borderColor='var(--line)';this.style.color='var(--ink-soft)'">+ Adicionar linha</button>
      `)}
    </div>
    <div>
      ${mkCard('ct_table','Custo por Tipster',`
        <p style="font-size:11px;color:var(--ink-mute);margin-bottom:.75rem">💡 Preencha mensalmente o custo de assinatura/serviço de cada tipster ativo. Valores salvos permanentemente no navegador.</p>
        <div class="tbl-wrap"><table class="tbl" id="tblCT">
          <thead><tr><th style="text-align:left;min-width:130px">Tipster</th>${monthHdrs}<th style="text-align:center;border-left:1px solid var(--line)">Total</th></tr></thead>
          <tbody>
            <tr class="total-row"><td style="font-weight:700">Total</td>${buildCTTotal()}<td style="border-left:1px solid var(--line)"></td></tr>
            ${buildCTRows()}
          </tbody>
        </table></div>
      `)}
    </div>`;
}

// ── Aba "Tipster / Método" (Gestão) — cadastro EDITÁVEL do tipster + escada de unidade +
// dicas de detecção. O drill (extrato) virou só-leitura: TODA a edição do tipster mora aqui.
// Reusa os endpoints /tipsters/cadastro · /tipsters/{id}/info · /tipsters/unidades já no ar.
let _tmCadastro=null;   // nome -> {id, casas, mercados, obs, completo, ...}
let _tmSel=null;        // tipster selecionado no seletor
function _tmVal(id){const e=document.getElementById(id);return e?e.value:'';}
function _tmIsoBR(iso){const m=/^(\d{4})-(\d{2})-(\d{2})$/.exec(iso||'');return m?m[3]+'/'+m[2]+'/'+m[1]:(iso||'');}
// Valor unitário da escada → .money 2 casas (UI_REFERENCE §5.1: stake/valor unitário).
function _tmMoney(v){return`<span class="money"><span class="money-sign">R$</span><span class="money-val">${fmt(Number(v)||0,2)}</span></span>`;}
function _tmDica(titulo,txt){return`<div style="background:var(--surface-2);border:1px solid var(--line);border-radius:10px;padding:12px 14px">`
  +`<div style="font-family:var(--font-mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--accent);margin-bottom:6px">${titulo}</div>`
  +`<div style="font-size:12px;color:var(--ink-soft);font-family:var(--font-sans);line-height:1.45">${txt}</div></div>`;}

async function renderTipsterMetodo(){
  const cont=document.getElementById('tipsterMetodoContent');
  if(!cont)return;
  let lista=[];
  try{const r=await fetch('/tipsters/cadastro?arquivados=0');const d=await r.json();lista=d.tipsters||[];}catch(e){lista=[];}
  _tmCadastro={};lista.forEach(t=>{_tmCadastro[t.nome]=t;});
  const nomes=lista.map(t=>t.nome).sort((a,b)=>a.localeCompare(b,'pt-BR'));
  const nInc=lista.filter(t=>!t.completo).length;
  if(!_tmSel||!_tmCadastro[_tmSel])_tmSel=nomes[0]||null;

  // Dicas — esqueleto da auto-atribuição (só-texto; a detecção real é etapa seguinte).
  const dicas=`<p style="font-size:12px;color:var(--ink-soft);font-family:var(--font-sans);line-height:1.5;margin-bottom:.9rem">`
    +`Hoje o tipster é atribuído <strong style="color:var(--ink)">manualmente</strong> depois da extração — a IA nunca lê o tipster do bilhete. `
    +`Preenchendo o cadastro abaixo você prepara o terreno para o Sharpen <strong style="color:var(--accent)">sugerir o tipster automaticamente</strong> durante a extração <span style="font-family:var(--font-mono);font-size:10px;text-transform:uppercase;letter-spacing:.1em;color:var(--ink-mute)">(em construção)</span>.</p>`
    +`<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px">`
    +_tmDica('Nome consistente','Use sempre o MESMO nome para o mesmo tipster (ex.: sempre &ldquo;SóChutes&rdquo;, nunca &ldquo;so chutes&rdquo;). O nome é a chave do cadastro e da atribuição.')
    +_tmDica('Casas &amp; mercados','Informe onde o tipster opera e os mercados típicos. Um bilhete numa casa ou mercado que não é dele tem menos chance de ser atribuído a ele.')
    +_tmDica('Escada de unidade','Defina quanto vale 1u em R$ ao longo do tempo. É o que converte o resultado em unidades e ancora a stake típica do tipster.')
    +`</div>`;

  const iv='background:var(--surface-2);border:1px solid var(--line);border-radius:8px;padding:8px 10px;color:var(--ink);font-size:13px;font-family:var(--font-sans);outline:none;width:100%;box-sizing:border-box';
  const lb='font-family:var(--font-mono);font-size:9px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-mute);margin-bottom:5px;display:block';
  const aviso=nInc?`<span style="font-family:var(--font-mono);font-size:10px;color:var(--accent);background:rgba(var(--accent-rgb),.12);border:1px solid var(--line);border-radius:999px;padding:3px 10px">${nInc} sem info preenchida</span>`:'';
  const selector=nomes.length
    ?`<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:1rem"><label style="${lb};margin:0">Tipster</label>`
      +`<select id="tmSelect" onchange="tmPick(this.value)" style="${iv};max-width:300px">${nomes.map(n=>`<option value="${esc(n)}"${n===_tmSel?' selected':''}>${esc(n)}${_tmCadastro[n].completo?'':' · incompleto'}</option>`).join('')}</select>${aviso}</div><div id="tmEditor"></div>`
    :`<div style="color:var(--ink-mute);font-size:12px;font-family:var(--font-sans);padding:1rem 0">Nenhum tipster cadastrado ainda. Eles aparecem aqui automaticamente quando você atribui um nome na extração.</div>`;

  cont.innerHTML=mkCard('tm_dicas','Como o Sharpen detecta o tipster',dicas)+mkCard('tm_cad','Cadastro do tipster',selector);
  if(_tmSel)tmRenderEditor(_tmSel);
}
window.renderTipsterMetodo=renderTipsterMetodo;

function tmPick(nome){_tmSel=nome;tmRenderEditor(nome);}
window.tmPick=tmPick;

async function tmRenderEditor(nome){
  const box=document.getElementById('tmEditor');
  if(!box)return;
  const t=(_tmCadastro||{})[nome]||null;
  let segs=[];
  try{const r=await fetch('/tipsters/unidades?tipster='+encodeURIComponent(nome));const d=await r.json();segs=d.escada||[];}catch(e){}
  const iv='background:var(--surface-2);border:1px solid var(--line);border-radius:8px;padding:8px 10px;color:var(--ink);font-size:13px;font-family:var(--font-sans);outline:none;width:100%;box-sizing:border-box';
  const lb='font-family:var(--font-mono);font-size:9px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-mute);margin-bottom:5px;display:block';
  const bt='background:var(--accent);color:#fff;border:0;border-radius:8px;padding:8px 14px;font-size:12px;font-weight:600;font-family:var(--font-sans);cursor:pointer;flex-shrink:0';
  const bx='background:none;border:1px solid var(--line);color:var(--neg);border-radius:6px;padding:4px 9px;cursor:pointer;font-size:11px;flex-shrink:0';
  const info=t
    ?`<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">`
      +`<div><label style="${lb}">Casas principais</label><input id="tmCasas" style="${iv}" value="${esc(t.casas||'')}" placeholder="Ex.: Bet365, Betano"></div>`
      +`<div><label style="${lb}">Mercados</label><input id="tmMercados" style="${iv}" value="${esc(t.mercados||'')}" placeholder="Ex.: Under/Over gols"></div>`
      +`<div style="grid-column:1/-1"><label style="${lb}">Observações</label><input id="tmObs" style="${iv}" value="${esc(t.obs||'')}" placeholder="Anotações sobre o método, gestão, contato…"></div>`
      +`<div style="grid-column:1/-1;display:flex;justify-content:flex-end"><button style="${bt}" onclick="tmSaveInfo(${t.id})">Salvar info</button></div>`
    +`</div>`
    :`<div style="color:var(--ink-mute);font-size:12px">Tipster não encontrado no cadastro.</div>`;
  const segRows=segs.length
    ?segs.map(s=>`<div style="display:flex;align-items:center;gap:12px;padding:8px 2px;border-bottom:1px solid var(--line-2)"><span style="font-family:var(--font-mono);font-size:11px;color:var(--ink-soft)">desde ${esc(_tmIsoBR(s.vigente_desde))}</span><span style="margin-left:auto">${_tmMoney(s.valor)}</span><button style="${bx}" title="Remover" onclick="tmDelSeg(${s.id})">✕</button></div>`).join('')
    :`<div style="color:var(--ink-mute);font-size:12px;padding:6px 0">Sem escada — o resultado em unidades usa a stake média até você definir o valor da unidade.</div>`;
  box.innerHTML=info
    +`<div style="margin-top:20px"><label style="${lb}">Escada de unidade — quanto vale 1u em R$ no tempo</label>${segRows}`
      +`<div style="display:flex;gap:8px;margin-top:12px;align-items:center"><input id="tmData" style="${iv};max-width:130px;font-family:var(--font-mono)" placeholder="DD/MM/AAAA"><input id="tmValor" style="${iv};max-width:160px" placeholder="R$ por unidade"><button style="${bt}" onclick="tmAddSeg()">Adicionar</button></div>`
    +`</div>`;
}

async function tmSaveInfo(id){
  const body={casas:_tmVal('tmCasas'),mercados:_tmVal('tmMercados'),obs:_tmVal('tmObs')};
  try{const r=await fetch('/tipsters/'+id+'/info',{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});if(!r.ok)throw 0;_tmCadastro=null;if(typeof _tipCadastro!=='undefined')_tipCadastro=null;renderTipsterMetodo();}catch(e){alert('Erro ao salvar as informações.');}
}
window.tmSaveInfo=tmSaveInfo;
async function tmAddSeg(){
  const nome=_tmSel,data=_tmVal('tmData'),valor=_tmVal('tmValor');
  if(!data||!valor){alert('Informe a data e o valor da unidade.');return;}
  try{const r=await fetch('/tipsters/unidades',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({tipster:nome,vigente_desde:data,valor:valor})});const d=await r.json().catch(()=>({}));if(!r.ok){alert(d.detail||'Não foi possível salvar.');return;}if(typeof _tipEscadas!=='undefined')_tipEscadas=null;tmRenderEditor(nome);}catch(e){alert('Erro ao adicionar o degrau.');}
}
window.tmAddSeg=tmAddSeg;
async function tmDelSeg(id){
  const nome=_tmSel;
  try{const r=await fetch('/tipsters/unidades/'+id,{method:'DELETE'});if(!r.ok)throw 0;if(typeof _tipEscadas!=='undefined')_tipEscadas=null;tmRenderEditor(nome);}catch(e){alert('Erro ao remover o degrau.');}
}
window.tmDelSeg=tmDelSeg;
