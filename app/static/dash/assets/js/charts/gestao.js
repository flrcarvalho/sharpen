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

// ── Aba "Tipster / Método" (Gestão) — v2: lista de tipsters em BOXES (accordion). Cada box
// abre em 2 colunas — ESQUERDA você preenche (casas/mercados/obs/escada), DIREITA o
// "Sharpen sugere" analisa as apostas do tipster na base e dá casas/mercados/stake típica
// em chips que você tica. O drill (extrato) é só-leitura. Endpoints já no ar:
// /tipsters/cadastro · /tipsters/{id}/info · /tipsters/unidades.
let _tmCadastro=null;   // nome -> {id, casas, mercados, obs, completo, ...}
let _tmOpen=null;       // tipster com o box expandido (accordion: 1 aberto por vez)
let _tmAgg=null;        // nome -> agregado das apostas da base (casas/mercados/stakes)
let _tmQ='';            // termo da busca

const _tmIV='background:var(--surface-2);border:1px solid var(--line);border-radius:8px;padding:8px 10px;color:var(--ink);font-size:13px;font-family:var(--font-sans);outline:none;width:100%;box-sizing:border-box';
const _tmLB='font-family:var(--font-mono);font-size:9px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-mute);margin-bottom:5px;display:block';
const _tmBT='background:var(--accent);color:#fff;border:0;border-radius:8px;padding:8px 14px;font-size:12px;font-weight:600;font-family:var(--font-sans);cursor:pointer;flex-shrink:0';
const _tmBTG='background:none;border:1px solid var(--accent);color:var(--accent);border-radius:8px;padding:8px 14px;font-size:12px;font-weight:600;font-family:var(--font-sans);cursor:pointer;flex-shrink:0';
const _tmBX='background:none;border:1px solid var(--line);color:var(--neg);border-radius:6px;padding:4px 9px;cursor:pointer;font-size:11px;flex-shrink:0';

function _tmVal(id){const e=document.getElementById(id);return e?e.value:'';}
function _tmIsoBR(iso){const m=/^(\d{4})-(\d{2})-(\d{2})$/.exec(iso||'');return m?m[3]+'/'+m[2]+'/'+m[1]:(iso||'');}
// Valor unitário → .money 2 casas (UI_REFERENCE §5.1: stake/valor unitário). width:auto
// para NÃO herdar o width:100%/space-between do .money de tabela (senão estica no inline).
function _tmMoney(v){return`<span class="money" style="width:auto"><span class="money-sign">R$</span><span class="money-val">${fmt(Number(v)||0,2)}</span></span>`;}
// nome dentro de onclick="…('…')" — escapa \ e '
function _tmJs(s){return String(s).replace(/\\/g,'\\\\').replace(/'/g,"\\'");}

let _tmSelCasas=[],_tmSelMkts=[],_tmSelEsp=[];   // seleção do editor aberto
let _tmAllCasas=[],_tmAllMkts=[],_tmAllEsp=[];   // universo da base (p/ os menus)
let _tmMktOwners={},_tmEspOwners={};             // key -> nº de tipsters DISTINTOS que usam
// Agrega as apostas da base por tipster (1 passada em DADOS): contagem por casa, mercado
// (r.aposta), esporte e valor de stake (exclui Void) — fonte do "Sharpen sugere". Na mesma
// passada monta o universo de casas/mercados/esportes e a contagem de tipsters DISTINTOS
// por mercado/esporte (exclusividade: 1 tipster = sinal forte; vários = cuidado).
function _tmBuildAgg(){
  const agg={},casaSet=new Set(),mktSet=new Set(),espSet=new Set(),mo={},eo={};
  if(typeof DADOS==='undefined'||!DADOS){_tmAllCasas=[];_tmAllMkts=[];_tmAllEsp=[];_tmMktOwners={};_tmEspOwners={};return agg;}
  DADOS.forEach(r=>{
    if(r.casa)casaSet.add(r.casa);
    if(r.aposta)mktSet.add(r.aposta);
    if(r.esporte)espSet.add(r.esporte);
    if(!r.tipster)return;
    if(r.aposta)(mo[r.aposta]||(mo[r.aposta]=new Set())).add(r.tipster);
    if(r.esporte)(eo[r.esporte]||(eo[r.esporte]=new Set())).add(r.tipster);
    const a=agg[r.tipster]||(agg[r.tipster]={n:0,pl:0,casas:{},mkts:{},esp:{},stakes:{}});
    a.n++;a.pl+=(r.lucro||0);
    if(r.casa)a.casas[r.casa]=(a.casas[r.casa]||0)+1;
    if(r.aposta)a.mkts[r.aposta]=(a.mkts[r.aposta]||0)+1;
    if(r.esporte)a.esp[r.esporte]=(a.esp[r.esporte]||0)+1;
    if(r.resultado!=='V'&&r.stake>0)a.stakes[r.stake]=(a.stakes[r.stake]||0)+1;
  });
  _tmAllCasas=[...casaSet].sort((a,b)=>a.localeCompare(b,'pt-BR'));
  _tmAllMkts=[...mktSet].sort((a,b)=>a.localeCompare(b,'pt-BR'));
  _tmAllEsp=[...espSet].sort((a,b)=>a.localeCompare(b,'pt-BR'));
  _tmMktOwners={};Object.keys(mo).forEach(m=>{_tmMktOwners[m]=mo[m].size;});
  _tmEspOwners={};Object.keys(eo).forEach(e=>{_tmEspOwners[e]=eo[e].size;});
  return agg;
}
// lista "a, b, c" -> array único e limpo (e volta com join(', '))
function _tmSplit(s){return [...new Set(String(s||'').split(',').map(x=>x.trim()).filter(Boolean))];}
// Tag de exclusividade: quantos tipsters DISTINTOS usam essa chave (mercado/esporte).
function _tmOwnerTag(map,key){
  const o=(map||{})[key]||0;
  if(o===1)return`<span style="font-family:var(--font-mono);font-size:9px;color:var(--pos);background:rgba(var(--pos-rgb),.12);border-radius:999px;padding:1px 6px;margin-left:2px">exclusivo</span>`;
  if(o>1)return`<span style="font-family:var(--font-mono);font-size:9px;color:var(--warn);background:rgba(var(--warn-rgb),.12);border-radius:999px;padding:1px 6px;margin-left:2px">${o} tipsters</span>`;
  return'';
}
function _tmMktTag(m){return _tmOwnerTag(_tmMktOwners,m);}
function _tmEspTag(e){return _tmOwnerTag(_tmEspOwners,e);}
function _tmTop(obj,lim){return Object.entries(obj||{}).map(([k,c])=>({k,c})).sort((a,b)=>b.c-a.c).slice(0,lim||99);}
// Stake típica HONESTA: top-3 valores de stake com share. `dominante` = o mais comum
// cobre ≥50% (aí vale mostrar um número só); senão é "stake variada" (mostra a lista).
function _tmStakeTipica(stakes){
  const ent=Object.entries(stakes||{});
  if(!ent.length)return null;
  const tot=ent.reduce((a,[,c])=>a+c,0);
  ent.sort((a,b)=>b[1]-a[1]);
  const top=ent.slice(0,3).map(([v,c])=>({valor:Number(v),share:c/tot}));
  return {top:top,dominante:top[0].share>=0.5,n:tot};
}

async function renderTipsterMetodo(){
  const cont=document.getElementById('tipsterMetodoContent');
  if(!cont)return;
  let lista=[];
  try{const r=await fetch('/tipsters/cadastro?arquivados=1');const d=await r.json();lista=d.tipsters||[];}catch(e){lista=[];}
  _tmCadastro={};lista.forEach(t=>{_tmCadastro[t.nome]=t;});
  _tmAgg=_tmBuildAgg();
  const nomes=_tmSortNomes(lista.map(t=>t.nome));
  const nInc=lista.filter(t=>!t.completo&&!t.arquivado).length;   // só ativos incompletos

  const nAtivos=lista.filter(t=>!t.arquivado).length;
  const _sSvg=`<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4"/></svg>`;

  const intro=`<div class="intro">Cada tipster tem um box abaixo. Clique para abrir e preencher <b>casas, mercados e a escada de unidade</b> — ou deixe o <b>Sharpen sugerir</b> a partir das apostas dele na base. Prepara o terreno para o Sharpen atribuir o tipster sozinho na extração <span class="em">em construção</span>.</div>`;
  const toolbar=`<div class="toolbar"><div class="search">${_sSvg}<input id="tmBusca" value="${esc(_tmQ)}" oninput="tmBusca(this.value)" placeholder="Buscar tipster…"></div>${nInc?`<span class="pill-warn">${nInc} sem info</span>`:''}</div>`;

  let corpo;
  if(!nomes.length){
    corpo=`<div style="color:var(--ink-mute);font-size:12px;padding:20px">Nenhum tipster cadastrado ainda. Eles aparecem aqui automaticamente quando você atribui um nome na extração.</div>`;
  }else{
    const filtro=_tmQ.trim().toLowerCase();
    const vis=nomes.filter(n=>!filtro||n.toLowerCase().includes(filtro));
    corpo=vis.length?vis.map(_tmBox).join(''):`<div style="color:var(--ink-mute);font-size:12px;padding:20px">Nenhum tipster encontrado.</div>`;
  }
  const paneTP=`<section class="pane" id="paneTP"><div class="panel"><div class="panel__head"><span class="tick"></span><h2>Tipster / Método</h2></div>${intro}${toolbar}<div id="tmLista" style="padding:6px 14px 14px">${corpo}</div></div></section>`;
  const paneCasas=`<section class="pane" id="paneCasas" hidden></section>`;
  const kpis=`<span class="tm-kpi" id="kpiTP"><b>${nAtivos}</b> tipsters${nInc?` · <span class="w">${nInc} sem info</span>`:''}</span>`
    +`<span class="tm-kpi" id="kpiCasas" style="display:none"><b id="kpiCasasN">—</b> casas · <span class="w" id="kpiCasasSug">—</span></span>`;
  const tabs=`<div class="tabbar" role="tablist">`
    +`<button data-tab="tp" class="on" onclick="tmTab('tp')"><span>Tipster / Método</span><span class="n">${nAtivos}</span></button>`
    +`<button data-tab="casas" onclick="tmTab('casas')"><span>Casas</span><span class="n" id="tabCasasN">—</span></button></div>`;
  cont.innerHTML=`<div class="tm-wrap"><div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;margin-bottom:6px">${tabs}<span style="margin-left:auto;display:flex;gap:8px;flex-wrap:wrap">${kpis}</span></div>${paneTP}${paneCasas}</div>`;
  if(_tmOpen&&_tmCadastro[_tmOpen])tmRenderEditor(_tmOpen);
  renderCasasFeudo();
}
// Troca de aba: alterna panes + KPIs no header.
function tmTab(t){
  const isTP=t==='tp';
  document.querySelectorAll('.tm-wrap .tabbar button').forEach(b=>b.classList.toggle('on',b.dataset.tab===t));
  const p1=document.getElementById('paneTP'),p2=document.getElementById('paneCasas');
  if(p1)p1.hidden=!isTP; if(p2)p2.hidden=isTP;
  const k1=document.getElementById('kpiTP'),k2=document.getElementById('kpiCasas');
  if(k1)k1.style.display=isTP?'':'none'; if(k2)k2.style.display=isTP?'none':'';
}
window.tmTab=tmTab;
window.renderTipsterMetodo=renderTipsterMetodo;

// ── Casas · aba "Atribuição por casa" (pack Tipster/Método do Feca) ────────────
// Tabela em grade (Casa · Volume/dono · Atribuição · Tipster dedicado · Origem). O dono
// declara casa→tipster(s): 'dedicada' (1-2) ou 'compartilhada'. Multi-select com busca;
// tag Origem (Sharpen=sugerido / Personalizado=editado). Persiste em /casas/config (com
// origem). Classes do pack em tipster-metodo.css. Liga no atribuidor (matcher) quando dedicada.
let _casasVisao=[];        // [{casa,total,n_tipsters,top,top_share,sugestao_modo,sugestao_tipsters,modo,tipsters,origem}]
let _casasEdit={};         // casa -> {modo, tipsters:[...]}  (estado de trabalho da tela)
let _casasQ='';            // termo da busca
const _CK='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg>';
const _CHV='<svg class="chv" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M6 9l6 6 6-6"/></svg>';
const _SPARK='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l1.6 4.2L18 9l-4.4 1.8L12 15l-1.6-4.2L6 9l4.4-1.8L12 3Z"/></svg>';
const _PEN='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.05 2.05 0 0 1 2.9 2.9L7 19l-4 1 1-4z"/></svg>';

function _casaAtivos(){
  return Object.values(_tmCadastro||{}).filter(t=>!t.arquivado).map(t=>t.nome).sort((a,b)=>a.localeCompare(b,'pt-BR'));
}
// Tipsters ativos + contagem de apostas (p/ o multi-select), da base agregada _tmAgg.
function _casaAtivosDetalhe(){
  return _casaAtivos().map(n=>{const a=(_tmAgg||{})[n];return {n,bets:a&&a.n?a.n.toLocaleString('pt-BR'):''};});
}
// Estado inicial de uma casa: config salva > sugestão do backend > 'multi' vazio.
function _casaState(c){
  if(_casasEdit[c.casa])return _casasEdit[c.casa];
  let st;
  if(c.modo)st={modo:c.modo,tipsters:_tmSplit(c.tipsters)};
  else if(c.sugestao_modo)st={modo:c.sugestao_modo,tipsters:(c.sugestao_tipsters||[]).slice(0,2)};
  else st={modo:'multi',tipsters:[]};
  _casasEdit[c.casa]=st;return st;
}

async function renderCasasFeudo(){
  const pane=document.getElementById('paneCasas');
  if(!pane)return;
  try{const r=await fetch('/casas/config');const d=await r.json();_casasVisao=d.casas||[];}
  catch(e){_casasVisao=[];}
  _casasEdit={};
  const pend=_casasVisao.filter(c=>!c.modo&&c.sugestao_modo).length;
  const nDed=_casasVisao.filter(c=>c.modo==='dedicada').length, nComp=_casasVisao.length-nDed;
  const set=(id,html)=>{const e=document.getElementById(id);if(e)e.innerHTML=html;};
  set('tabCasasN',String(_casasVisao.length));
  set('kpiCasasN',String(_casasVisao.length));
  set('kpiCasasSug',pend?(pend+' sugestões'):'curado');
  const sSvg='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4"/></svg>';
  const intro='<div class="intro">Casa de nicho costuma ser de <b>um tipster só</b> — na BETesporte é sempre o mesmo, independente do valor. Marque cada casa como <b>Dedicada</b> (1-2 tipsters) ou <b>Compartilhada</b>. As sugestões vêm da sua própria base. <span class="em">liga no atribuidor quando você curar</span></div>';
  const toolbar='<div class="toolbar"><div class="search">'+sSvg+'<input id="casaSearch" value="'+esc(_casasQ)+'" oninput="casasBusca(this.value)" placeholder="Buscar casa…"></div>'
    +(pend?'<button class="btn btn--primary" id="applySug" onclick="casasAplicarSugestoes()">Aplicar '+pend+' sugestões</button>':'')+'</div>';
  const chead='<div class="chead"><div>Casa</div><div>Volume · dono na base</div><div>Atribuição</div><div>Tipster dedicado</div><div class="r">Origem</div></div>';
  pane.innerHTML='<div class="panel"><div class="panel__head"><span class="tick"></span><h2>Atribuição por casa</h2>'
    +'<span class="meta"><b>'+nDed+'</b> dedicadas · <b>'+nComp+'</b> compartilhadas</span></div>'+intro+toolbar+chead+'<div id="casasList"></div></div>';
  renderCasasLista();
}
window.renderCasasFeudo=renderCasasFeudo;

function casasBusca(v){_casasQ=v;renderCasasLista();}

// Feudos (dedicada, curada ou sugerida) primeiro por pureza; o resto por volume.
function _casaEhFeudo(c){return c.modo==='dedicada'||(!c.modo&&c.sugestao_modo==='dedicada');}
function renderCasasLista(){
  const box=document.getElementById('casasList');if(!box)return;
  const q=_casasQ.trim().toLowerCase();
  const vis=_casasVisao.filter(c=>!q||(c.casa||'').toLowerCase().includes(q)).slice().sort((a,b)=>{
    const fa=_casaEhFeudo(a)?0:1,fb=_casaEhFeudo(b)?0:1;
    return fa!==fb?fa-fb:(fa===0?(b.top_share-a.top_share):(b.total-a.total));
  });
  box.innerHTML=vis.length?vis.map(_casaRowGrid).join('')
    :`<div style="padding:22px 20px;color:var(--ink-mute);font-size:12px">Nenhuma casa encontrada.</div>`;
}

// Rótulo do multi-select: "—", "Nome" ou "Nome +N".
function _mselLbl(tips){
  if(!tips||!tips.length)return '<span class="ph">— selecionar tipster —</span>';
  if(tips.length===1)return '<span>'+esc(tips[0])+'</span>';
  return '<span>'+esc(tips[0])+'</span><span class="cnt">+'+(tips.length-1)+'</span>';
}
// Tag Origem: Sharpen (sugerido/aplicado) ou Personalizado (editado à mão). Casa não curada
// mas com sugestão → mostra Sharpen (é a opinião do sistema); sem nada → vazio.
function _orgTag(c){
  const o=c.origem||(c.sugestao_modo?'sharpen':null);
  if(o==='custom')return '<span class="org org--custom">'+_PEN+'Personalizado</span>';
  if(o==='sharpen')return '<span class="org org--sharpen">'+_SPARK+'Sharpen</span>';
  return '';
}
function _casaRowGrid(c){
  const st=_casaState(c),cj=_tmJs(c.casa),isD=st.modo==='dedicada';
  const dom=(typeof _houseDomain==='function')?_houseDomain(c.casa):'';
  const ic=dom?('<img src="'+favicon(dom)+'" alt="">'):esc((c.casa||'?').slice(0,2).toUpperCase());
  const cstats='<b>'+fmt(c.total,0)+'</b> apostas · '+esc(c.top||'—')+' '+fmtPct(c.top_share,0,false)+' · '+c.n_tipsters+' tipsters';
  const attr='<div class="attr"><button data-attr="dedicated" class="'+(isD?'on':'')+'" onclick="casaModo(\''+cj+'\',\'dedicada\')">Dedicada</button>'
    +'<button data-attr="shared" class="'+(isD?'':'on')+'" onclick="casaModo(\''+cj+'\',\'multi\')">Compartilhada</button></div>';
  const ded=isD
    ? '<div class="msel"><button class="msel__btn" onclick="casaMselToggle(\''+cj+'\',event)">'+_mselLbl(st.tipsters)+_CHV+'</button></div>'
    : '<span class="dedmut">— não aplicável —</span>';
  return '<div class="crow'+(isD?' dedic':'')+'" data-name="'+esc((c.casa||'').toLowerCase())+'">'
    +'<div class="casa"><span class="ic">'+ic+'</span><span class="nm" title="'+esc(c.casa)+'">'+esc(c.casa)+'</span></div>'
    +'<div class="cstats">'+cstats+'</div>'
    +'<div>'+attr+'</div>'
    +'<div>'+ded+'</div>'
    +'<div class="r">'+_orgTag(c)+'</div>'
  +'</div>';
}

// ── Multi-select "Tipster dedicado" (busca + checkboxes, cap 2, in-place) ──────
function casaMselToggle(casa,ev){
  ev.stopPropagation();
  const msel=ev.target.closest('.msel');if(!msel)return;
  const wasOpen=msel.classList.contains('open');
  document.querySelectorAll('.tm-wrap .msel.open').forEach(x=>x.classList.remove('open'));
  if(wasOpen)return;
  _casaMselBuild(msel,casa);
  msel.classList.add('open');
  const s=msel.querySelector('.msel__pop .srch input');if(s)s.focus();
}
function _casaMselBuild(msel,casa){
  const c=_casasVisao.find(x=>x.casa===casa);if(!c)return;
  const st=_casaState(c),cap=st.tipsters.length>=2;
  const rows=_casaAtivosDetalhe().map(t=>{
    const on=st.tipsters.indexOf(t.n)>-1,dim=(!on&&cap);
    return '<div class="msopt'+(on?' on':'')+'" data-name="'+esc(t.n)+'"'+(dim?' style="opacity:.4;pointer-events:none"':'')
      +' onclick="casaMselPick(\''+_tmJs(casa)+'\',\''+_tmJs(t.n)+'\',event)"><span class="box">'+_CK+'</span><span class="n">'+esc(t.n)+'</span><span class="vol">'+esc(t.bets)+'</span></div>';
  }).join('');
  let pop=msel.querySelector('.msel__pop');
  if(!pop){pop=document.createElement('div');pop.className='msel__pop';msel.appendChild(pop);}
  const hint=cap?'<div style="font-family:var(--font-mono);font-size:9px;color:var(--ink-mute);padding:2px 4px 6px">máx. 2 — desmarque um para trocar</div>':'';
  pop.innerHTML='<div class="srch"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4-4"/></svg>'
    +'<input placeholder="buscar tipster…" oninput="_casaMselFilter(this)" onclick="event.stopPropagation()"></div>'+hint+'<div class="msel__list">'+rows+'</div>';
}
function _casaMselFilter(inp){
  const q=inp.value.toLowerCase();
  inp.closest('.msel__pop').querySelectorAll('.msopt').forEach(o=>{o.style.display=o.dataset.name.toLowerCase().indexOf(q)>-1?'':'none';});
}
function casaMselPick(casa,nome,ev){
  ev.stopPropagation();
  const opt=ev.target.closest('.msopt');if(!opt)return;
  const c=_casasVisao.find(x=>x.casa===casa);if(!c)return;
  const st=_casaState(c),p=st.tipsters.indexOf(nome);
  if(p>-1){st.tipsters.splice(p,1);opt.classList.remove('on');}
  else{ if(st.tipsters.length>=2)return; st.tipsters.push(nome);opt.classList.add('on'); }
  const msel=opt.closest('.msel'); if(msel){const btn=msel.querySelector('.msel__btn');if(btn)btn.innerHTML=_mselLbl(st.tipsters)+_CHV;}
  const row=opt.closest('.crow'); if(row){const rc=row.querySelector('.r');if(rc){c.origem='custom';rc.innerHTML=_orgTag(c);}}
  casaSalvar(casa,'custom');
}
document.addEventListener('click',function(){document.querySelectorAll('.tm-wrap .msel.open').forEach(x=>x.classList.remove('open'));});

// Atribuição (Dedicada/Compartilhada). Toggle marca a casa como Personalizado e re-renderiza
// (a forma da linha muda: some/entra o multi-select). Dedicada nasce semeada da sugestão.
function casaModo(casa,modo){
  const c=_casasVisao.find(x=>x.casa===casa);if(!c)return;
  const st=_casaState(c);
  if(st.modo===modo)return;
  st.modo=modo;
  if(modo==='multi')st.tipsters=[];
  else if(!st.tipsters.length){st.tipsters=(c.sugestao_tipsters||[]).slice(0,2).filter(n=>_casaAtivos().includes(n));}
  c.origem='custom';
  if(modo==='multi'||st.tipsters.length)casaSalvar(casa,'custom');
  renderCasasLista(); _casaUpdMeta();
}
// Persiste a casa (com origem). NÃO re-renderiza (o multi-select atualiza in-place). Dedicada
// sem tipster ainda → não salva (aguarda a escolha). Retorna bool.
async function casaSalvar(casa,origem){
  const st=_casasEdit[casa];if(!st)return false;
  const tips=st.modo==='dedicada'?st.tipsters.filter(Boolean):[];
  if(st.modo==='dedicada'&&!tips.length)return false;
  try{
    const r=await fetch('/casas/config',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({casa:casa,modo:st.modo,tipsters:tips.join(','),origem:origem||'custom'})});
    if(!r.ok)throw 0;
    const c=_casasVisao.find(x=>x.casa===casa);if(c){c.modo=st.modo;c.tipsters=tips.join(',');c.origem=origem||'custom';}
    return true;
  }catch(e){alert('Erro ao salvar a casa.');return false;}
}
// Aplica todas as sugestões pendentes (origem = Sharpen, não Personalizado).
async function casasAplicarSugestoes(){
  const pend=_casasVisao.filter(c=>!c.modo&&c.sugestao_modo);
  for(const c of pend){
    const st=_casaState(c);
    st.modo=c.sugestao_modo;
    st.tipsters=(c.sugestao_modo==='dedicada')?(c.sugestao_tipsters||[]).slice(0,2):[];
    await casaSalvar(c.casa,'sharpen');
  }
  renderCasasFeudo();
}
// Atualiza o contador do cabeçalho (dedicadas · compartilhadas) sem re-render completo.
function _casaUpdMeta(){
  const nDed=_casasVisao.filter(c=>c.modo==='dedicada').length,nComp=_casasVisao.length-nDed;
  const m=document.querySelector('#paneCasas .panel__head .meta');
  if(m)m.innerHTML='<b>'+nDed+'</b> dedicadas · <b>'+nComp+'</b> compartilhadas';
}

// Ordena: ATIVOS primeiro (alfabético), INATIVOS no fim (alfabético). Ver _tmBox/tmSetInativo.
function _tmSortNomes(nomes){
  return nomes.slice().sort((a,b)=>{
    const aa=(_tmCadastro[a]||{}).arquivado?1:0,ab=(_tmCadastro[b]||{}).arquivado?1:0;
    return aa!==ab?aa-ab:a.localeCompare(b,'pt-BR');
  });
}
// Box do accordion. Colapsado: nome + tick "inativo" + sinal de completude + volume/P/L.
// Expandido (_tmOpen===nome): injeta o editor 2-colunas em #tmEditor (via tmRenderEditor).
function _tmBox(nome){
  const t=_tmCadastro[nome]||{};
  const ag=(_tmAgg||{})[nome];
  const aberto=_tmOpen===nome;
  const arq=!!t.arquivado;
  const badge=arq
    ?`<span style="font-family:var(--font-mono);font-size:9px;letter-spacing:.06em;text-transform:uppercase;color:var(--ink-mute);background:var(--elevated);border:1px solid var(--line);border-radius:999px;padding:2px 8px">inativo</span>`
    :(!t.completo
      ?`<span style="font-family:var(--font-mono);font-size:9px;letter-spacing:.06em;text-transform:uppercase;color:var(--accent);background:rgba(var(--accent-rgb),.12);border-radius:999px;padding:2px 8px">falta info</span>`
      :`<span style="font-family:var(--font-mono);font-size:9px;letter-spacing:.06em;text-transform:uppercase;color:var(--pos);background:rgba(var(--pos-rgb),.12);border-radius:999px;padding:2px 8px">completo</span>`);
  // Só a quantidade de apostas importa nesta página (P/L removido, pedido do Feca). Largura
  // fixa + nowrap + right → a contagem e o tick de inativo alinham milimetricamente entre linhas.
  const vol=`<span style="font-family:var(--font-mono);font-size:11px;color:var(--ink-mute);white-space:nowrap;min-width:104px;text-align:right">${ag?ag.n.toLocaleString('pt-BR')+' apostas':''}</span>`;
  const caret=`<span style="color:var(--ink-mute);font-size:12px;display:inline-block;transform:rotate(${aberto?'90':'0'}deg)">▸</span>`;
  // tick "inativo" — para de expandir o box (stopPropagation) e arquiva/reativa o tipster.
  const tick=`<label onclick="event.stopPropagation()" title="Marcar como inativo (não sigo mais)" style="display:inline-flex;align-items:center;gap:5px;font-family:var(--font-mono);font-size:10px;text-transform:uppercase;letter-spacing:.06em;color:var(--ink-mute);cursor:pointer"><input type="checkbox" ${arq?'checked':''} onchange="tmSetInativo(${t.id},this.checked,'${_tmJs(nome)}')" style="accent-color:var(--accent);cursor:pointer">inativo</label>`;
  const header=`<div onclick="tmToggle('${_tmJs(nome)}')" style="display:flex;align-items:center;gap:12px;padding:12px 14px;cursor:pointer;user-select:none">`
    +caret+`<span style="font-weight:700;color:var(--ink);font-size:14px">${esc(nome)}</span>`+badge
    +`<span style="margin-left:auto;display:flex;align-items:center;gap:20px">${vol}${tick}</span></div>`;
  const body=aberto?`<div id="tmEditor" style="padding:0 14px 16px;border-top:1px solid var(--line-2)"></div>`:'';
  return`<div style="background:var(--surface-2);border:1px solid var(--line);border-radius:12px;margin-bottom:8px;overflow:hidden;opacity:${arq?'.5':'1'}">${header}${body}</div>`;
}

// Busca: re-renderiza SÓ a lista (#tmLista); o input de busca fica fora → não perde foco.
function tmBusca(v){
  _tmQ=v;
  const lista=document.getElementById('tmLista');
  if(!lista)return;
  const filtro=(v||'').trim().toLowerCase();
  const nomes=_tmSortNomes(Object.keys(_tmCadastro||{}));
  const vis=nomes.filter(n=>!filtro||n.toLowerCase().includes(filtro));
  lista.innerHTML=vis.length?vis.map(_tmBox).join(''):`<div style="color:var(--ink-mute);font-size:12px;padding:1rem 0">Nenhum tipster encontrado.</div>`;
  if(_tmOpen&&vis.includes(_tmOpen))tmRenderEditor(_tmOpen);
}
window.tmBusca=tmBusca;

function tmToggle(nome){_tmOpen=(_tmOpen===nome)?null:nome;tmBusca(_tmQ);}
window.tmToggle=tmToggle;

// Tick "inativo": arquiva (não sigo mais) ou reativa o tipster e reordena a lista (inativos
// no fim). Atualiza o flag local e re-renderiza — sem refetch (mais rápido, mantém o agg).
async function tmSetInativo(id,inativo,nome){
  const url='/tipsters/'+id+'/'+(inativo?'arquivar':'reativar');
  try{
    const r=await fetch(url,{method:'POST'});
    if(!r.ok)throw 0;
    if(_tmCadastro[nome])_tmCadastro[nome].arquivado=inativo;
    if(inativo&&_tmOpen===nome)_tmOpen=null;   // fecha o editor se arquivou o aberto
    tmBusca(_tmQ);
  }catch(e){alert('Não foi possível atualizar o status do tipster.');}
}
window.tmSetInativo=tmSetInativo;

function tmRenderEditor(nome){
  const box=document.getElementById('tmEditor');
  if(!box)return;
  const t=(_tmCadastro||{})[nome]||null;
  if(!t){box.innerHTML=`<div style="color:var(--ink-mute);font-size:12px;padding:12px 0">Tipster não encontrado no cadastro.</div>`;return;}
  const iv=_tmIV,lb=_tmLB,bt=_tmBT;
  const secTit='font-family:var(--font-mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;margin:14px 0 12px';
  // ESQUERDA — você preenche. A escada mora em #tmEscada (container próprio): adicionar/
  // remover degrau re-renderiza SÓ ela, sem apagar os inputs não salvos (bug do Feca).
  _tmSelCasas=_tmSplit(t.casas);_tmSelMkts=_tmSplit(t.mercados);_tmSelEsp=_tmSplit(t.esportes);
  const dlMkts=`<datalist id="tmMktDL">${_tmAllMkts.map(m=>`<option value="${esc(m)}">`).join('')}</datalist>`;
  const esquerda=`<div>`
    +`<div style="${secTit};color:var(--ink-soft)">Suas informações</div>`
    +`<div style="margin-bottom:12px"><label style="${lb}">Casas principais</label><div id="tmCasasBox"></div></div>`
    +`<div style="margin-bottom:12px"><label style="${lb}">Esportes</label><div id="tmEspBox"></div></div>`
    +`<div style="margin-bottom:12px"><label style="${lb}">Mercados</label><div id="tmMktBox"></div>${dlMkts}</div>`
    +`<div style="margin-bottom:12px"><label style="${lb}">Dica de stake</label><input id="tmDica" style="${iv}" value="${esc(t.dica_stake||'')}" placeholder="Ex.: unidade 500, mas passo 501 (ou 500,01) pra facilitar a leitura"></div>`
    +`<div style="margin-bottom:12px"><label style="${lb}">Observações gerais</label><input id="tmObs" style="${iv}" value="${esc(t.obs||'')}" placeholder="Método, gestão, contato…"></div>`
    +`<div style="display:flex;justify-content:flex-end;margin-bottom:16px"><button style="${bt}" onclick="tmSaveInfo(${t.id})">Salvar info</button></div>`
    +`</div>`;
  // DIREITA — Sharpen sugere (analisa a base)
  const direita=`<div>`
    +`<div style="${secTit};color:var(--accent)">Sharpen sugere <span style="color:var(--ink-mute);text-transform:none;letter-spacing:0">— das apostas na base</span></div>`
    +_tmSugestoes(nome)
    +`</div>`;
  box.innerHTML=`<div style="display:grid;grid-template-columns:1fr 1fr;gap:24px;align-items:start">${esquerda}${direita}</div><div id="tmEscada" style="margin-top:22px"></div>`;
  _tmRenderCasas();_tmRenderEsp();_tmRenderMkts();
  tmRenderEscada(nome);
}

// Chip de item já selecionado (com ✕). grp: 'casa' | 'mkt'. tag: HTML extra (exclusividade).
function _tmSelChip(grp,val,tag){
  const del={casa:'tmCasaDel',mkt:'tmMktDel',esp:'tmEspDel'}[grp];
  return`<span style="display:inline-flex;align-items:center;gap:6px;background:var(--surface);border:1px solid var(--line);border-radius:999px;padding:4px 6px 4px 10px;font-size:12px;color:var(--ink)">${esc(val)}${tag||''}<button onclick="${del}('${_tmJs(val)}')" title="Remover" style="background:none;border:0;color:var(--ink-mute);cursor:pointer;font-size:13px;line-height:1;padding:0 2px">✕</button></span>`;
}
// Casas principais = chips selecionados + menu suspenso das casas da base (sem digitar).
function _tmRenderCasas(){
  const el=document.getElementById('tmCasasBox');if(!el)return;
  const chips=_tmSelCasas.map(c=>_tmSelChip('casa',c,'')).join('');
  const opts=_tmAllCasas.filter(c=>!_tmSelCasas.includes(c)).map(c=>`<option value="${esc(c)}">${esc(c)}</option>`).join('');
  el.innerHTML=`<div style="display:flex;flex-wrap:wrap;gap:6px;align-items:center">${chips}`
    +`<select onchange="tmCasaAdd(this.value);this.selectedIndex=0" style="${_tmIV};width:auto;max-width:200px"><option value="">+ adicionar casa</option>${opts}</select></div>`;
}
// Mercados = chips (com tag de exclusividade) + input inteligente (autocomplete via datalist).
function _tmRenderMkts(){
  const el=document.getElementById('tmMktBox');if(!el)return;
  const chips=_tmSelMkts.map(m=>_tmSelChip('mkt',m,_tmMktTag(m))).join('');
  el.innerHTML=(chips?`<div style="display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-bottom:6px">${chips}</div>`:'')
    +`<div style="display:flex;gap:6px;align-items:center"><input id="tmMktInp" list="tmMktDL" placeholder="Digite um mercado…" onkeydown="if(event.key==='Enter'){event.preventDefault();tmMktAdd();}" style="${_tmIV};max-width:220px"><button onclick="tmMktAdd()" style="${_tmBTG};padding:6px 12px">+ adicionar</button></div>`;
}
function tmCasaAdd(v){v=(v||'').trim();if(v&&!_tmSelCasas.includes(v)){_tmSelCasas.push(v);_tmRenderCasas();}}
function tmCasaDel(v){_tmSelCasas=_tmSelCasas.filter(x=>x!==v);_tmRenderCasas();}
function tmMktAdd(){const i=document.getElementById('tmMktInp');if(!i)return;const v=(i.value||'').trim();if(v&&!_tmSelMkts.includes(v))_tmSelMkts.push(v);_tmRenderMkts();const n=document.getElementById('tmMktInp');if(n)n.focus();}
function tmMktDel(v){_tmSelMkts=_tmSelMkts.filter(x=>x!==v);_tmRenderMkts();}
window.tmCasaAdd=tmCasaAdd;window.tmCasaDel=tmCasaDel;window.tmMktAdd=tmMktAdd;window.tmMktDel=tmMktDel;
// Esportes = chips (com tag de exclusividade) + menu suspenso dos esportes da base.
function _tmRenderEsp(){
  const el=document.getElementById('tmEspBox');if(!el)return;
  const chips=_tmSelEsp.map(e=>_tmSelChip('esp',e,_tmEspTag(e))).join('');
  const opts=_tmAllEsp.filter(e=>!_tmSelEsp.includes(e)).map(e=>`<option value="${esc(e)}">${esc(e)}</option>`).join('');
  el.innerHTML=`<div style="display:flex;flex-wrap:wrap;gap:6px;align-items:center">${chips}`
    +`<select onchange="tmEspAdd(this.value);this.selectedIndex=0" style="${_tmIV};width:auto;max-width:200px"><option value="">+ adicionar esporte</option>${opts}</select></div>`;
}
function tmEspAdd(v){v=(v||'').trim();if(v&&!_tmSelEsp.includes(v)){_tmSelEsp.push(v);_tmRenderEsp();}}
function tmEspDel(v){_tmSelEsp=_tmSelEsp.filter(x=>x!==v);_tmRenderEsp();}
window.tmEspAdd=tmEspAdd;window.tmEspDel=tmEspDel;

// Painel "Sharpen sugere": stake típica (moda das stakes) + chips TICKÁVEIS das casas e
// mercados mais usados pelo tipster. "Usar selecionados" copia os ticados p/ os inputs.
function _tmSugestoes(nome){
  const ag=(_tmAgg||{})[nome];
  const lb=_tmLB;
  if(!ag||!ag.n)return`<div style="color:var(--ink-mute);font-size:12px">Sem apostas deste tipster na base ainda — preencha à mão.</div>`;
  const st=_tmStakeTipica(ag.stakes);
  const stakeBox='background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin-bottom:14px';
  let stakeCard='';
  if(st&&st.dominante){
    const t0=st.top[0];
    stakeCard=`<div style="${stakeBox}"><div style="${lb}">Stake típica</div>`
      +`<div style="display:flex;align-items:baseline;gap:10px"><div style="font-size:18px">${_tmMoney(t0.valor)}</div><div style="font-family:var(--font-mono);font-size:11px;color:var(--ink-mute)">${fmtPct(t0.share*100,0,false)} das apostas</div></div>`
      +`<div style="font-size:11px;color:var(--ink-soft);margin-top:4px">É o valor de aposta mais comum — bom ponto de partida para a unidade (1u) na escada ao lado.</div></div>`;
  }else if(st){
    const lista=st.top.map(x=>`<span style="display:inline-flex;align-items:baseline;gap:5px">${_tmMoney(x.valor)}<span style="font-family:var(--font-mono);font-size:10px;color:var(--ink-mute)">${fmtPct(x.share*100,0,false)}</span></span>`).join('<span style="color:var(--ink-mute)"> · </span>');
    stakeCard=`<div style="${stakeBox}"><div style="${lb}">Stake variada</div>`
      +`<div style="display:flex;flex-wrap:wrap;gap:6px 4px;align-items:baseline;margin-top:2px">${lista}</div>`
      +`<div style="font-size:11px;color:var(--ink-soft);margin-top:4px">Não há um valor dominante. A escada de unidade (ao lado) resolve: defina 1u por período e o resultado sai em u mesmo com stake variável.</div></div>`;
  }
  const chip=(grp,k,c,tag)=>`<label style="display:inline-flex;align-items:center;gap:6px;background:var(--surface);border:1px solid var(--line);border-radius:999px;padding:4px 10px;margin:0 6px 6px 0;cursor:pointer;font-size:12px;color:var(--ink)"><input type="checkbox" data-tmchip="${grp}" value="${esc(k)}" checked style="accent-color:var(--accent);cursor:pointer">${esc(k)} <span style="font-family:var(--font-mono);font-size:10px;color:var(--ink-mute)">${c}</span>${tag||''}</label>`;
  const dash='<span style="color:var(--ink-mute);font-size:12px">—</span>';
  const casasChips=_tmTop(ag.casas,8).map(x=>chip('casa',x.k,x.c)).join('')||dash;
  const espChips=_tmTop(ag.esp,8).map(x=>chip('esp',x.k,x.c,_tmEspTag(x.k))).join('')||dash;
  const mktsChips=_tmTop(ag.mkts,10).map(x=>chip('mkt',x.k,x.c,_tmMktTag(x.k))).join('')||dash;
  const legenda=`<div style="font-size:11px;color:var(--ink-mute);margin-top:4px;display:flex;gap:16px;flex-wrap:wrap"><span><span style="color:var(--pos);font-weight:600">exclusivo</span> = só um tipster nessa categoria, fácil identificar</span><span><span style="color:var(--warn);font-weight:600">N tipsters</span> = compartilhado, mais cuidado</span></div>`;
  return stakeCard
    +`<div style="margin-bottom:12px"><div style="${lb}">Casas mais usadas</div><div>${casasChips}</div></div>`
    +`<div style="margin-bottom:12px"><div style="${lb}">Esportes mais apostados</div><div>${espChips}</div></div>`
    +`<div style="margin-bottom:8px"><div style="${lb}">Mercados mais usados</div><div>${mktsChips}</div>${legenda}</div>`
    +`<button style="${_tmBTG};margin-top:12px" onclick="tmUsarSugestoes()">Usar selecionados →</button>`
    +`<div style="font-size:11px;color:var(--ink-mute);margin-top:8px">Tique os que fazem sentido e clique — casas, esportes e mercados entram na esquerda. Depois é só “Salvar info”.</div>`;
}
// Copia os chips ticados para a seleção da esquerda (MERGE — não apaga o que já estava).
function tmUsarSugestoes(){
  const sel=g=>[...document.querySelectorAll('[data-tmchip="'+g+'"]:checked')].map(c=>c.value);
  _tmSelCasas=[...new Set([..._tmSelCasas,...sel('casa')])];
  _tmSelEsp=[...new Set([..._tmSelEsp,...sel('esp')])];
  _tmSelMkts=[...new Set([..._tmSelMkts,...sel('mkt')])];
  _tmRenderCasas();_tmRenderEsp();_tmRenderMkts();
}
window.tmUsarSugestoes=tmUsarSugestoes;

// Escada de unidade — form à esquerda + LINHA DO TEMPO horizontal (mais novo à esquerda).
// Classes do pack (.ladder/.tl-node). Valor em R$ 2 casas via fmt (mesmo formatador do .money);
// R$ menor via .tl-val .cur; delta ▲/▼ entre períodos. Reusa tmAddSeg/tmDelSeg (persistência).
async function tmRenderEscada(nome){
  const el=document.getElementById('tmEscada');
  if(!el)return;
  let segs=[];
  try{const r=await fetch('/tipsters/unidades?tipster='+encodeURIComponent(nome));const d=await r.json();segs=d.escada||[];}catch(e){}
  segs=segs.slice().sort((a,b)=>(b.vigente_desde||'').localeCompare(a.vigente_desde||''));   // mais novo primeiro
  const brl=v=>fmt(Number(v)||0,2);
  const X='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M5 5l14 14M19 5L5 19"/></svg>';
  const note=segs.length
    ? `Unidade atual: <b>R$ ${brl(segs[0].valor)}</b> desde <b>${esc(_tmIsoBR(segs[0].vigente_desde))}</b>. Adicione um novo valor sempre que a unidade mudar.`
    : `Sem escada — o resultado em unidades usa a stake média até você definir o valor da unidade.`;
  let tl;
  if(!segs.length){
    tl=`<div class="tl-empty">Nenhuma alteração registrada ainda.<br>O primeiro valor que você adicionar vira a unidade atual.</div>`;
  }else{
    const nodes=segs.map((s,i)=>{
      const older=segs[i+1];let delta='';
      if(older){const dd=(Number(s.valor)||0)-(Number(older.valor)||0);if(dd!==0)delta=`<div class="tl-delta ${dd>0?'up':'down'}">${dd>0?'▲':'▼'} R$ ${brl(Math.abs(dd))}</div>`;}
      return `<div class="tl-node${i===0?' cur':''}"><span class="tl-dot"></span><div class="tl-b"><div class="tl-top"><span class="tl-date">desde ${esc(_tmIsoBR(s.vigente_desde))}</span>${i===0?'<span class="tl-badge">atual</span>':''}</div><div class="tl-val"><span class="cur">R$</span> ${brl(s.valor)}</div>${delta}</div><button class="tl-rm" title="Remover" onclick="tmDelSeg(${s.id})">${X}</button></div>`;
    }).join('');
    tl=`<div class="tl-hd">Histórico</div><div class="tl-list">${nodes}</div>`;
  }
  el.innerHTML=`<div class="ladder"><div class="ladder__hd"><span class="eye">Escada de unidade — quanto vale 1u em R$ no tempo</span></div>`
    +`<div class="ladder__bd"><div class="ladder__form"><p class="ladder__note">${note}</p>`
      +`<div class="ladder__row"><input id="tmData" class="inp" type="date" style="color-scheme:dark" title="Dia em que a unidade passa a valer — clique p/ o calendário ou digite"><input id="tmValor" class="inp" placeholder="R$ por unidade"><button class="btn btn--primary" onclick="tmAddSeg()">Adicionar</button></div>`
    +`</div><div class="ladder__tl">${tl}</div></div></div>`;
}
window.tmRenderEscada=tmRenderEscada;

async function tmSaveInfo(id){
  const body={casas:_tmSelCasas.join(', '),mercados:_tmSelMkts.join(', '),esportes:_tmSelEsp.join(', '),obs:_tmVal('tmObs'),dica_stake:_tmVal('tmDica')};
  try{const r=await fetch('/tipsters/'+id+'/info',{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});if(!r.ok)throw 0;_tmCadastro=null;if(typeof _tipCadastro!=='undefined')_tipCadastro=null;renderTipsterMetodo();}catch(e){alert('Erro ao salvar as informações.');}
}
window.tmSaveInfo=tmSaveInfo;
async function tmAddSeg(){
  const nome=_tmOpen,data=_tmVal('tmData'),valor=_tmVal('tmValor');
  if(!data||!valor){alert('Informe a data e o valor da unidade.');return;}
  try{const r=await fetch('/tipsters/unidades',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({tipster:nome,vigente_desde:data,valor:valor})});const d=await r.json().catch(()=>({}));if(!r.ok){alert(d.detail||'Não foi possível salvar.');return;}if(typeof _tipEscadas!=='undefined')_tipEscadas=null;tmRenderEscada(nome);}catch(e){alert('Erro ao adicionar o degrau.');}
}
window.tmAddSeg=tmAddSeg;
async function tmDelSeg(id){
  const nome=_tmOpen;
  try{const r=await fetch('/tipsters/unidades/'+id,{method:'DELETE'});if(!r.ok)throw 0;if(typeof _tipEscadas!=='undefined')_tipEscadas=null;tmRenderEscada(nome);}catch(e){alert('Erro ao remover o degrau.');}
}
window.tmDelSeg=tmDelSeg;
