// ── performance.js — Esportes, Casas, Tipsters, Resultados por Casa ──────────────

// Helper: gera o markup completo de um tooltip de métrica (MetricTooltip)
function _mkTipAnchor(label,formula,desc,bench){
  return `<span class="tip-anchor"><button class="metric-info" type="button" aria-label="Sobre ${label}">i</button><div class="metric-tip" role="tooltip" hidden><span class="metric-tip__caret"></span>${formula?`<div class="metric-tip__formula">${formula}</div>`:''}<div class="metric-tip__desc">${desc}</div>${bench?`<div class="metric-tip__bench">${bench}</div>`:''}</div></span>`;
}

// Tooltip "Odd média ponderada" reusado em tabelas (cabeçalho) e cards .tcard.
// Quebra após o "=" : linha 1 = "Odd média ponderada =", linha 2 = a fórmula.
const _ODD_TIP_FORMULA='<span class="lbl">Odd média ponderada</span> <span class="op">=</span><br>Σ(odd <span class="op">×</span> stake) <span class="op">÷</span> Σ(stake)';
function _mkOddTip(){return _mkTipAnchor('Odd média ponderada',_ODD_TIP_FORMULA,'','');}

function _mkOddMediaTh(align='r',width=''){
  const cls=align==='r'?'th-r':align==='l'?'th-l':'th-c';
  const wS=width?` style="width:${width}"`:'';
  return`<th class="${cls}"${wS}><span class="th-k">Odd média ${_mkOddTip()}<span class="sort-icon"></span></span></th>`;
}

function rodapePValue(pv){
  const ativo=pv<0.001?'robusto':pv<0.05?'significativo':'inconclusivo';
  const corAtivo=ativo==='inconclusivo'?'var(--d-proj)':'var(--d-pos)';
  const seg=(lim,nome)=>nome===ativo
    ?`<b style="color:${corAtivo}">${lim} ${nome}</b>`
    :`<span style="color:var(--ink-soft)">${lim} ${nome}</span>`;
  return seg('&gt;&nbsp;0,05','inconclusivo')+' · '+seg('&lt;&nbsp;0,05','significativo')+' · '+seg('&lt;&nbsp;0,001','robusto');
}

// ── Sport tcard helpers ──────────────────────────────────────────────────────
let _sportEnts=null,_sportDays=null,_sportAllDays=null;
let _sportSort={k:'pl',dir:1};

function _mkSportCard(sport,pl,roi,stake,wr,bets,sparkSVG,avgStake,avgOdd){
  const plSign=pl>=0?'+':'−';
  const plCls=pl>=0?'pos':'neg';
  const roiCls=roi>=0?'pos':'neg';
  const plAmt=Math.abs(pl).toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2});
  const stakeInt=Math.round(stake).toLocaleString('pt-BR');
  const avgStakeStr=Math.round(avgStake||0).toLocaleString('pt-BR');
  const avgOddStr=fmtOdd(avgOdd);
  const betsStr=bets.toLocaleString('pt-BR');
  const roiStr=fmtPct(roi,1);
  const wrStr=fmtPct(wr,1,false);
  const wrPct=Math.min(wr,100).toFixed(1);
  const escAttr=esc(sport);
  return`<div class="tcard" data-sport="${escAttr}">`
    +`<div class="tcard__top"><span class="tcard__casa-hdr">${mkSpChip(sport)}<span class="nametag__nm" title="${escAttr}">${esc(sport)}</span></span><span class="tcard__vol"><b>${betsStr}</b>apostas</span></div>`
    +`<div class="tcard__hero"><span class="tcard__pl ${plCls}"><span class="tcard__cur">${plSign} R$</span>${plAmt}</span><div class="tcard__roi"><span class="tcard__roi-lbl">ROI</span><span class="tcard__roi-val ${roiCls}">${roiStr}</span></div></div>`
    +sparkSVG
    +`<div class="tcard__foot">`
      +`<div class="tcard__stat"><div class="tcard__stat-lbl">Turnover</div><div class="tcard__stat-val"><span class="tcard__cur--sm">R$</span>${stakeInt}</div></div>`
      +`<div class="tcard__stat"><div class="tcard__stat-lbl">Stake Média</div><div class="tcard__stat-val"><span class="tcard__cur--sm">R$</span>${avgStakeStr}</div></div>`
      +`<div class="tcard__stat"><div class="tcard__stat-lbl">Odd Média ${_mkOddTip()}</div><div class="tcard__stat-val">${avgOddStr}</div></div>`
      +`<div class="tcard__stat"><div class="tcard__stat-lbl">Win Rate</div><div class="tcard__stat-val">${wrStr}</div><div class="tcard__wrbar"><div class="tcard__wrfill" style="width:${wrPct}%"></div></div></div>`
    +`</div>`
    +`</div>`;
}

function _renderSportCards(){
  const el=document.getElementById('sportKpiCards');
  if(!el||!_sportEnts)return;
  if(!_sportEnts.length){el.innerHTML=mkEmpty('Nenhum esporte no período');return;}
  const{k,dir}=_sportSort;
  const fns={pl:([,d])=>d.l,roi:([,d])=>d.s>0?d.l/d.s*100:0,to:([,d])=>d.s,wr:([,d])=>wrFrac(d.w,d.hw,d.hl,d.t),vol:([,d])=>d.n};
  const fn=fns[k]||fns.pl;
  const sorted=[..._sportEnts].sort((a,b)=>dir*(fn(b)-fn(a)));
  el.innerHTML=sorted.map(([sport,d])=>{
    const roi=d.s>0?(d.l/d.s*100):0,wr=wrFrac(d.w,d.hw,d.hl,d.t);
    const avgStake=d.t>0?d.s/d.t:0,avgOdd=d.stk>0?d.wt/d.stk:0;
    return _mkSportCard(sport,d.l,roi,d.s,wr,d.n,_tipSparkSVG(_sportDays[sport]||{},_sportAllDays),avgStake,avgOdd);
  }).join('');
  el.onclick=function(e){if(e.target.closest('.tip-anchor'))return;const card=e.target.closest('.tcard');if(card&&card.dataset.sport)openSportDrill(card.dataset.sport);};
  document.querySelectorAll('#sportSeg button').forEach(btn=>btn.classList.toggle('active',btn.dataset.k===k));
  const dirBtn=document.getElementById('sportDir');
  if(dirBtn)dirBtn.textContent=dir<0?'↓':'↑';
}
window.sportSortBy=function(k){_sportSort.k=k;_sportSort.dir=1;_renderSportCards();};
window.sportSortDir=function(){_sportSort.dir*=-1;_renderSportCards();};

function renderSport(rows){
  const map={},dayMap={};
  rows.forEach(r=>{
    if(!map[r.esporte])map[r.esporte]={l:0,s:0,n:0,w:0,t:0,hw:0,hl:0,wt:0,stk:0};
    map[r.esporte].l+=r.lucro;if(r.resultado!=='V')map[r.esporte].s+=r.stake;map[r.esporte].n++;
    bumpWR(map[r.esporte],r.resultado);
    if(r.odd>0&&r.stake>0){map[r.esporte].wt+=r.odd*r.stake;map[r.esporte].stk+=r.stake;}
    const dk=r.data.slice(0,10);
    if(!dayMap[r.esporte])dayMap[r.esporte]={};
    dayMap[r.esporte][dk]=(dayMap[r.esporte][dk]||0)+r.lucro;
  });
  _sportEnts=Object.entries(map).filter(e=>e[0]&&e[0]!=='undefined');
  _sportDays=dayMap;
  _sportAllDays=[...new Set(rows.map(r=>r.data.slice(0,10)))].sort();

  // Portfolio KPIs
  const portPL=rows.reduce((a,r)=>a+r.lucro,0);
  const portS=calcTurnover(rows);   // turnover exclui Void
  const portROI=portS>0?(portPL/portS*100):0;
  const posCount=_sportEnts.filter(([,d])=>d.l>0).length;
  const negCount=_sportEnts.filter(([,d])=>d.l<0).length;
  const totalSp=_sportEnts.length;
  const plCls=portPL>=0?'pos':'neg';
  const roiCls=portROI>=0?'pos':'neg';
  const kpiEl=document.getElementById('sportPortfolioKPIs');
  if(kpiEl){
    kpiEl.innerHTML=
      `<div class="kpi">`+
        `<div class="kpi-label"><span class="kpi-pipe"></span> P/L Total</div>`+
        `<div class="kpi-val ${plCls}">${fmtPL(portPL)}</div>`+
        `<div class="kpi-sub">resultado total</div>`+
      `</div>`+
      `<div class="kpi">`+
        `<div class="kpi-label"><span class="kpi-pipe"></span> ROI</div>`+
        `<div class="kpi-val ${roiCls}">${fmtPct(portROI,2)}</div>`+
        `<div class="kpi-sub">Σ(P/L) / Σ(turnover)</div>`+
      `</div>`+
      `<div class="kpi">`+
        `<div class="kpi-label"><span class="kpi-pipe"></span> Esportes Positivos</div>`+
        `<div class="kpi-val neu">${posCount} / ${totalSp}</div>`+
        `<div class="kpi-sub">▲ ${posCount} · ▼ ${negCount} no vermelho</div>`+
      `</div>`+
      `<div class="kpi">`+
        `<div class="kpi-label"><span class="kpi-pipe"></span> Turnover Total</div>`+
        `<div class="kpi-val neu">${fmtR(portS)}</div>`+
        `<div class="kpi-sub">${rows.length.toLocaleString('pt-BR')} apostas</div>`+
      `</div>`;
  }

  _renderSportCards();

  const ents=[..._sportEnts].sort((a,b)=>b[1].l-a[1].l);

  // Tabela ACIMA do gráfico
  document.getElementById('sportTable').innerHTML=buildSummaryTable('tblSport','Esporte',ents);
  setTimeout(()=>makeSortable('tblSport',[1,3,4,5]),100);
  // Gráfico vertical abaixo
  const wrap=document.querySelector('#chartSport')?.parentElement;
  if(wrap)wrap.style.height='300px';
  const topN=ents.slice(0,20);
  const valLabelPlugin={id:'valLabels',afterDatasetsDraw(chart){
    const{ctx,scales:{x,y}}=chart;
    ctx.save();
    chart.getDatasetMeta(0).data.forEach((bar,i)=>{
      const v=topN[i]?.[1]?.l||0;
      const roi=topN[i]?.[1]?.s>0?(topN[i][1].l/topN[i][1].s*100):0;
      const lbl=(v>=0?'+':'')+fmtK(v);
      ctx.font='bold 10px JetBrains Mono, monospace';
      ctx.fillStyle=isDark()?'rgba(255,255,255,.9)':'rgba(0,0,0,.85)';
      ctx.textAlign='center';
      ctx.textBaseline=v>=0?'bottom':'top';
      ctx.fillText(lbl,bar.x,v>=0?bar.y-3:bar.y+3);
    });
    ctx.restore();
  }};
  mkChart('chartSport',{type:'bar',data:{labels:topN.map(e=>sportEmoji(e[0])+' '+e[0]),datasets:[{data:topN.map(e=>parseFloat(e[1].l.toFixed(2))),backgroundColor:topN.map(e=>e[1].l>=0?'rgba(0,214,143,.75)':'rgba(240,80,110,.75)'),borderRadius:4,borderSkipped:false}]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:{top:24,bottom:4}},plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx=>{const e=topN[ctx.dataIndex];const roi=e[1].s>0?(e[1].l/e[1].s*100):0;return[fmtPL(e[1].l),`ROI: ${fmtPct(roi,1)}`,`Apostas: ${e[1].n}`];}}}},scales:{x:{ticks:{color:tc(),font:{size:10},maxRotation:30},grid:{display:false},border:{display:false}},y:{ticks:{color:tc(),font:{size:10},callback:v=>fmtK(v)},grid:{color:gc()},border:{display:false}}}},plugins:[valLabelPlugin]});
}

function renderCasa(rows){
  const map={},dayMap={};
  rows.forEach(r=>{
    if(!map[r.casa])map[r.casa]={l:0,s:0,n:0,w:0,t:0,hw:0,hl:0,wt:0,stk:0};
    map[r.casa].l+=r.lucro;if(r.resultado!=='V')map[r.casa].s+=r.stake;map[r.casa].n++;
    bumpWR(map[r.casa],r.resultado);
    if(r.odd>0&&r.stake>0){map[r.casa].wt+=r.odd*r.stake;map[r.casa].stk+=r.stake;}
    const dk=r.data.slice(0,10);
    if(!dayMap[r.casa])dayMap[r.casa]={};
    dayMap[r.casa][dk]=(dayMap[r.casa][dk]||0)+r.lucro;
  });
  _casaEnts=Object.entries(map).filter(e=>e[0]&&e[0]!=='undefined');
  _casaDays=dayMap;
  _casaAllDays=[...new Set(rows.map(r=>r.data.slice(0,10)))].sort();

  // Portfolio KPIs
  const portPL=rows.reduce((a,r)=>a+r.lucro,0);
  const portS=calcTurnover(rows);   // turnover exclui Void
  const portROI=portS>0?(portPL/portS*100):0;
  const posCount=_casaEnts.filter(([,d])=>d.l>0).length;
  const negCount=_casaEnts.filter(([,d])=>d.l<0).length;
  const totalC=_casaEnts.length;
  const plCls=portPL>=0?'pos':'neg';
  const roiCls=portROI>=0?'pos':'neg';
  const el=document.getElementById('casaPortfolioKPIs');
  if(el){
    el.innerHTML=
      `<div class="kpi">`+
        `<div class="kpi-label"><span class="kpi-pipe"></span> P/L Total</div>`+
        `<div class="kpi-val ${plCls}">${fmtPL(portPL)}</div>`+
        `<div class="kpi-sub">resultado total</div>`+
      `</div>`+
      `<div class="kpi">`+
        `<div class="kpi-label"><span class="kpi-pipe"></span> ROI</div>`+
        `<div class="kpi-val ${roiCls}">${fmtPct(portROI,2)}</div>`+
        `<div class="kpi-sub">Σ(P/L) / Σ(turnover)</div>`+
      `</div>`+
      `<div class="kpi">`+
        `<div class="kpi-label"><span class="kpi-pipe"></span> Casas Positivas</div>`+
        `<div class="kpi-val neu">${posCount} / ${totalC}</div>`+
        `<div class="kpi-sub">▲ ${posCount} · ▼ ${negCount} no vermelho</div>`+
      `</div>`+
      `<div class="kpi">`+
        `<div class="kpi-label"><span class="kpi-pipe"></span> Turnover Total</div>`+
        `<div class="kpi-val neu">${fmtR(portS)}</div>`+
        `<div class="kpi-sub">${rows.length.toLocaleString('pt-BR')} apostas</div>`+
      `</div>`;
  }
  _renderCasaCards();
}

// ── Bookie cards + drill-down ────────────────────────────────────────────────
let _casaEnts=null,_casaDays=null,_casaAllDays=null;
let _casaSort={k:'pl',dir:1};
let _casaDrillEscHandler=null;
let _casaDrillBaseName=null,_casaDrillBaseRows=[],_casaDrillPeriodSt={qd:0,qt:'',df:'',dt:''};

function _mkCasaCard(name,pl,roi,stake,wr,bets,sparkSVG,avgStake,avgOdd){
  const plSign=pl>=0?'+':'−';
  const plCls=pl>=0?'pos':'neg';
  const roiCls=roi>=0?'pos':'neg';
  const plAmt=Math.abs(pl).toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2});
  const stakeInt=Math.round(stake).toLocaleString('pt-BR');
  const avgStakeStr=Math.round(avgStake||0).toLocaleString('pt-BR');
  const avgOddStr=fmtOdd(avgOdd);
  const betsStr=bets.toLocaleString('pt-BR');
  const roiStr=fmtPct(roi,1);
  const wrStr=fmtPct(wr,1,false);
  const wrPct=Math.min(wr,100).toFixed(1);
  const escAttr=esc(name);
  return`<div class="tcard" data-casa="${escAttr}">`
    +`<div class="tcard__top"><span class="tcard__casa-hdr">${mkHouseChip(name)}<span class="nametag__nm" title="${escAttr}">${esc(name)}</span></span><span class="tcard__vol"><b>${betsStr}</b>apostas</span></div>`
    +`<div class="tcard__hero"><span class="tcard__pl ${plCls}"><span class="tcard__cur">${plSign} R$</span>${plAmt}</span><div class="tcard__roi"><span class="tcard__roi-lbl">ROI</span><span class="tcard__roi-val ${roiCls}">${roiStr}</span></div></div>`
    +sparkSVG
    +`<div class="tcard__foot">`
      +`<div class="tcard__stat"><div class="tcard__stat-lbl">Turnover</div><div class="tcard__stat-val"><span class="tcard__cur--sm">R$</span>${stakeInt}</div></div>`
      +`<div class="tcard__stat"><div class="tcard__stat-lbl">Stake Média</div><div class="tcard__stat-val"><span class="tcard__cur--sm">R$</span>${avgStakeStr}</div></div>`
      +`<div class="tcard__stat"><div class="tcard__stat-lbl">Odd Média ${_mkOddTip()}</div><div class="tcard__stat-val">${avgOddStr}</div></div>`
      +`<div class="tcard__stat"><div class="tcard__stat-lbl">Win Rate</div><div class="tcard__stat-val">${wrStr}</div><div class="tcard__wrbar"><div class="tcard__wrfill" style="width:${wrPct}%"></div></div></div>`
    +`</div>`
    +`</div>`;
}

function _renderCasaCards(){
  const el=document.getElementById('casaKpiCards');
  if(!el||!_casaEnts)return;
  if(!_casaEnts.length){el.innerHTML=mkEmpty('Nenhuma casa no período');return;}
  const{k,dir}=_casaSort;
  const fns={pl:([,d])=>d.l,roi:([,d])=>d.s>0?d.l/d.s*100:0,to:([,d])=>d.s,wr:([,d])=>wrFrac(d.w,d.hw,d.hl,d.t),vol:([,d])=>d.n};
  const fn=fns[k]||fns.pl;
  const sorted=[..._casaEnts].sort((a,b)=>dir*(fn(b)-fn(a)));
  el.innerHTML=sorted.map(([c,d])=>{
    const roi=d.s>0?(d.l/d.s*100):0,wr=wrFrac(d.w,d.hw,d.hl,d.t);
    const avgStake=d.t>0?d.s/d.t:0,avgOdd=d.stk>0?d.wt/d.stk:0;
    return _mkCasaCard(c,d.l,roi,d.s,wr,d.n,_tipSparkSVG(_casaDays[c]||{},_casaAllDays),avgStake,avgOdd);
  }).join('');
  el.onclick=function(e){if(e.target.closest('.tip-anchor'))return;const card=e.target.closest('.tcard');if(card&&card.dataset.casa)openCasaDrill(card.dataset.casa);};
  document.querySelectorAll('#casaSeg button').forEach(btn=>btn.classList.toggle('active',btn.dataset.k===k));
  const dirBtn=document.getElementById('casaDir');
  if(dirBtn)dirBtn.textContent=dir<0?'↓':'↑';
}
window.casaSortBy=function(k){_casaSort.k=k;_casaSort.dir=1;_renderCasaCards();};
window.casaSortDir=function(){_casaSort.dir*=-1;_renderCasaCards();};

// ── Período herdado do painel (compartilhado pelos 3 drills) ─────────────────
// O drill abre já recortado pelo período ativo da aba de origem (gfs(p)).
// Quando qt é um deslocamento (Hoje/MTD com setinha ≠ 0), o chip padrão do
// drill apontaria pro dia/mês corrente — então o qt é descartado e o intervalo
// concreto fica só em df/dt (vira o chip herdado custom).
function _seedDrillFromPage(p){
  const st=gfs(p);
  const shifted=(st.qt==='hoje'&&(st.dayOff||0)!==0)||(st.qt==='mtd'&&(st.monthOff||0)!==0);
  return{qd:st.qd||0,qt:shifted?'':(st.qt||''),df:st.df||'',dt:st.dt||''};
}

function _sliceByPeriod(rows,st){
  const today=_today();
  let df='',dt='';
  if(st.qt==='hoje'){df=dt=today;}
  else if(st.qt==='wtd'){df=_wtdStart();dt=today;}
  else if(st.qt==='mtd'){df=_mtdStart();dt=today;}
  else if(st.qt==='ytd'){df=new Date().getFullYear()+'-01-01';dt=today;}
  else if(st.qd>0){df=_ymd(new Date(Date.now()-st.qd*864e5));}
  else{df=st.df||'';dt=st.dt||'';}
  if(!df&&!dt)return rows;
  return rows.filter(r=>{
    if(df&&r.data<df)return false;
    if(dt&&r.data>dt)return false;
    return true;
  });
}

function _rangeLabel(st){
  const cy=String(new Date().getFullYear());
  const f=d=>{const p=d.split('-');return p[2]+'/'+p[1]+(p[0]!==cy?'/'+p[0].slice(2):'');};
  if(st.df&&st.dt)return st.df===st.dt?f(st.df):f(st.df)+' → '+f(st.dt);
  return st.df?'desde '+f(st.df):'até '+f(st.dt);
}

// Intervalo custom = herdado sem chip padrão equivalente (só df/dt)
function _isCustomRange(st){return !!st&&!st.qt&&!st.qd&&!!(st.df||st.dt);}

function _updateDrillPeriodBar(barId,st,inh){
  const bar=document.getElementById(barId);
  if(!bar)return;
  bar.querySelectorAll('.qbtn').forEach(b=>{
    let a=false;
    if(b.dataset.inherit){
      const show=_isCustomRange(inh);
      b.style.display=show?'':'none';
      if(show){
        b.textContent=_rangeLabel(inh);
        a=(!st.qt&&!st.qd&&st.df===inh.df&&st.dt===inh.dt);
      }
    }
    else if(b.dataset.all)a=(st.qd===0&&!st.qt&&!st.df&&!st.dt);
    else if(b.dataset.days)a=(st.qd===parseInt(b.dataset.days));
    else if(b.dataset.qt)a=(st.qt===b.dataset.qt);
    b.classList.toggle('active',a);
  });
}

// ── Bookie drill-down ────────────────────────────────────────────────────────
let _casaDrillInheritSt=null;
function _sliceCasaDrillRows(){return _sliceByPeriod(_casaDrillBaseRows,_casaDrillPeriodSt);}

function _updateCasaDrillChips(){_updateDrillPeriodBar('casaDrillPeriodBar',_casaDrillPeriodSt,_casaDrillInheritSt);}

window.setDrillCasaQuick=function(d){_casaDrillPeriodSt={qd:d,qt:'',df:'',dt:''};_updateCasaDrillChips();renderCasaDrill(_sliceCasaDrillRows());};
window.setDrillCasaType=function(qt){_casaDrillPeriodSt={qd:0,qt:qt,df:'',dt:''};_updateCasaDrillChips();renderCasaDrill(_sliceCasaDrillRows());};
window.setDrillCasaAll=function(){_casaDrillPeriodSt={qd:0,qt:'',df:'',dt:''};_updateCasaDrillChips();renderCasaDrill(_sliceCasaDrillRows());};
window.setDrillCasaInherit=function(){if(!_casaDrillInheritSt)return;_casaDrillPeriodSt={..._casaDrillInheritSt};_updateCasaDrillChips();renderCasaDrill(_sliceCasaDrillRows());};

// Singleton tooltip para linha "Outros"
let _outrosTip=null;
function _getOutrosTip(){
  if(!_outrosTip){
    _outrosTip=document.createElement('div');
    _outrosTip.style.cssText='position:fixed;z-index:9999;background:var(--bg2);border:1px solid var(--line);border-radius:8px;padding:8px 12px;font-size:11px;font-family:var(--font-mono);color:var(--ink-soft);max-width:320px;line-height:1.8;pointer-events:none;display:none;box-shadow:0 4px 20px rgba(0,0,0,.4)';
    document.body.appendChild(_outrosTip);
  }
  return _outrosTip;
}

function _casaBreakdownTbl(rows,dimKey,labelFn,maxVisible=10,tableId=''){
  const cutoff30=_ymd(new Date(Date.now()-30*864e5));
  const cutoff15=_ymd(new Date(Date.now()-15*864e5));
  const map={};
  rows.forEach(r=>{
    const k=r[dimKey];if(!k)return;
    if(!map[k])map[k]={l:0,s:0,n:0,w:0,t:0,hw:0,hl:0,wt:0,stk:0,r30s:0,r15s:0};
    map[k].l+=r.lucro;if(r.resultado!=='V')map[k].s+=r.stake;map[k].n++;
    bumpWR(map[k],r.resultado);
    if(r.odd>0&&r.stake>0){map[k].wt+=r.odd*r.stake;map[k].stk+=r.stake;}
    if(dimKey==='tipster'&&r.resultado!=='V'){   // turnover recente exclui Void
      if(r.data>=cutoff30)map[k].r30s+=r.stake;
      if(r.data>=cutoff15)map[k].r15s+=r.stake;
    }
  });
  const sortFn=dimKey==='tipster'
    ?(a,b)=>(b[1].r30s-a[1].r30s)||b[1].s-a[1].s
    :(a,b)=>b[1].s-a[1].s;
  const ents=Object.entries(map).sort(sortFn);
  if(!ents.length)return mkEmpty('Sem dados no período');
  const visible=ents.slice(0,maxVisible);
  const rest=ents.slice(maxVisible);
  const mkRow=([k,d],isOutros=false,outrosLabel='Outros',outrosNames='',muted=false)=>{
    const roi=d.s>0?(d.l/d.s*100):0,wr=wrFrac(d.w,d.hw,d.hl,d.t);
    const avgOdd=d.stk>0?d.wt/d.stk:0,avgStake=d.t>0?d.s/d.t:0;
    const lc=d.l>=0?'color:var(--pos)':'color:var(--neg)';
    const rc=roi>=0?'color:var(--pos)':'color:var(--neg)';
    const trStyle=muted?' style="opacity:0.45"':'';
    const labelCell=isOutros
      ?`<td><span class="outros-anchor" data-outros="${esc(outrosNames)}" style="cursor:help;border-bottom:1px dashed var(--ink-mute);color:var(--ink-mute)">${esc(outrosLabel)} (${esc(k)})</span></td>`
      :`<td>${labelFn(k)}</td>`;
    return`<tr${trStyle}>${labelCell}<td class="td-num">${d.n.toLocaleString('pt-BR')}</td><td class="td-num" style="${lc}">${fmtPL(d.l)}</td><td class="td-num">${fmtR(d.s)}</td><td class="td-num" style="${rc}">${fmtPct(roi,2)}</td><td class="td-num">${mkWRC(wr)}</td><td class="td-num">${fmtR(avgStake)}</td><td class="td-num">${fmtOdd(avgOdd)}</td></tr>`;
  };
  let tRows=visible.map(e=>mkRow(e)).join('');
  if(dimKey==='tipster'){
    const outrosAtivos=rest.filter(([,d])=>d.r15s>0);
    const inativos=rest.filter(([,d])=>d.r15s===0);
    if(outrosAtivos.length>0){
      const agg={l:0,s:0,n:0,w:0,t:0,hw:0,hl:0,wt:0,stk:0};
      outrosAtivos.forEach(([,d])=>{agg.l+=d.l;agg.s+=d.s;agg.n+=d.n;agg.w+=d.w;agg.t+=d.t;agg.hw+=d.hw;agg.hl+=d.hl;agg.wt+=d.wt;agg.stk+=d.stk;});
      tRows+=mkRow([String(outrosAtivos.length),agg],true,'Outros',outrosAtivos.map(([k])=>k).join(' · '),false);
    }
    if(inativos.length>0){
      const agg={l:0,s:0,n:0,w:0,t:0,hw:0,hl:0,wt:0,stk:0};
      inativos.forEach(([,d])=>{agg.l+=d.l;agg.s+=d.s;agg.n+=d.n;agg.w+=d.w;agg.t+=d.t;agg.hw+=d.hw;agg.hl+=d.hl;agg.wt+=d.wt;agg.stk+=d.stk;});
      tRows+=mkRow([String(inativos.length),agg],true,'Inativos +15d',inativos.map(([k])=>k).join(' · '),true);
    }
  } else if(rest.length>0){
    const agg={l:0,s:0,n:0,w:0,t:0,hw:0,hl:0,wt:0,stk:0};
    rest.forEach(([,d])=>{agg.l+=d.l;agg.s+=d.s;agg.n+=d.n;agg.w+=d.w;agg.t+=d.t;agg.hw+=d.hw;agg.hl+=d.hl;agg.wt+=d.wt;agg.stk+=d.stk;});
    tRows+=mkRow([String(rest.length),agg],true,'Outros',rest.map(([k])=>k).join(' · '),false);
  }
  const th=dimKey==='tipster'?'Tipster':dimKey==='casa'?'Casa':'Esporte';
  const idAttr=tableId?` id="${tableId}"`:'';
  const oddTh=_mkOddMediaTh('r','88px');
  return`<table class="tbl"${idAttr}><thead><tr>${mkTh(th,'','l')+mkTh('Bets','','r')+mkTh('P/L','','r')+mkTh('Turnover','','r')+mkTh('ROI','','r')+mkTh('Win Rate','','r')+mkTh('Stake média','','r')+oddTh}</tr></thead><tbody>${tRows}</tbody></table>`;
}

function renderCasaDrill(rows){
  const nome=_casaDrillBaseName;
  const pl=rows.reduce((a,r)=>a+r.lucro,0);
  const s=calcTurnover(rows);   // turnover exclui Void
  const roi=s>0?pl/s*100:0;
  const settled=rows.filter(r=>r.resultado!=='V');
  const wins=settled.filter(r=>['W','HW'].includes(r.resultado)).length;
  const wr=wrPctRows(rows);
  const wt=rows.reduce((a,r)=>r.odd>0&&r.stake>0?a+r.odd*r.stake:a,0);
  const stk=rows.reduce((a,r)=>r.odd>0&&r.stake>0?a+r.stake:a,0);
  const avgOdd=stk>0?wt/stk:0;
  const plCls=pl>=0?'pos':'neg';
  const roiCls=roi>=0?'pos':'neg';
  const _minDate=rows.length?rows.reduce((m,r)=>r.data<m?r.data:m,'9999-99-99'):'';
  const _maxDate=rows.length?rows.reduce((m,r)=>r.data>m?r.data:m,'0000-00-00'):'';
  const{total:custoTotal,nContas:nContasCusto}=(_minDate&&typeof calcCasaCost==='function')?calcCasaCost(nome,_minDate,_maxDate):{total:0,nContas:0};
  const plLiq=pl-custoTotal;
  const roiLiq=s>0?plLiq/s*100:0;

  const _td=calcTopoDrawdown(rows),_rf=calcRecoveryFactor(rows),_dd=calcDrawdownReal(rows),_mddR=_dd.mddReais,_mddP=_dd.mddPct;
  const _fmtD=d=>{if(!d)return'—';const p=d.slice(0,10).split('-');return p[2]+'/'+p[1]+'/'+p[0];};
  const _mddBench=_dd.troughDate?`<span class="lbl">vale em ${_fmtD(_dd.troughDate)}</span> · <span class="thr">quanto menor, melhor</span>`:'<span class="thr">quanto menor, melhor</span>';

  const body=document.getElementById('casaDrillBody');
  if(!body)return;

  const avgStake=settled.length?s/settled.length:0;   // turnover ÷ encerradas (exclui Void)
  const kS='display:flex;flex-direction:column;min-width:0;overflow:visible';
  const sbS='margin-top:auto;padding-top:6px';
  const vS='font-size:16px';

  const _custoCls=custoTotal>0?'neg':'neu';
  const _custoVal=custoTotal>0?fmtPL(-custoTotal):fmtR(0);
  const _custoSub=custoTotal>0?`${nContasCusto} conta${nContasCusto!==1?'s':''} no período`:'sem custo configurado';
  const _roiLiqCls=roiLiq>=0?'pos':'neg';

  body.innerHTML=
    `<div class="analise-popup-section">`+
      `<div class="analise-popup-section-title">Resultado Geral</div>`+
      `<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:8px;align-items:stretch;width:100%;margin-bottom:8px">`+
        `<div class="kpi" style="${kS}"><div class="kpi-label"><span class="kpi-pipe"></span>P/L Bruto</div><div class="kpi-val ${plCls}" style="${vS}">${fmtPL(pl)}</div><div class="kpi-sub" style="${sbS}">antes dos custos</div></div>`+
        `<div class="kpi" style="${kS}"><div class="kpi-label"><span class="kpi-pipe"></span>ROI Bruto</div><div class="kpi-val ${roiCls}" style="${vS}">${fmtPct(roi,2)}</div><div class="kpi-sub" style="${sbS}">Σ(P/L)/Σ(turnover)</div></div>`+
        `<div class="kpi" style="${kS}"><div class="kpi-label"><span class="kpi-pipe"></span>Custo</div><div class="kpi-val ${_custoCls}" style="${vS}">${_custoVal}</div><div class="kpi-sub" style="${sbS}">${_custoSub}</div></div>`+
        `<div class="kpi" style="${kS}"><div class="kpi-label"><span class="kpi-pipe"></span>P/L Líquido</div><div class="kpi-val ${plLiq>=0?'pos':'neg'}" style="${vS}">${fmtPL(plLiq)}</div><div class="kpi-sub" style="${sbS}">após custos</div></div>`+
        `<div class="kpi" style="${kS}"><div class="kpi-label"><span class="kpi-pipe"></span>ROI Líquido</div><div class="kpi-val ${_roiLiqCls}" style="${vS}">${fmtPct(roiLiq,2)}</div><div class="kpi-sub" style="${sbS}">Σ(P/L líq)/Σ(turnover)</div></div>`+
      `</div>`+
      `<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:8px;align-items:stretch;width:100%">`+
        `<div class="kpi" style="${kS}"><div class="kpi-label"><span class="kpi-pipe"></span>Turnover</div><div class="kpi-val neu" style="${vS}">${fmtR(s)}</div><div class="kpi-sub" style="${sbS}">volume apostado</div></div>`+
        `<div class="kpi" style="${kS}"><div class="kpi-label"><span class="kpi-pipe"></span>Volume</div><div class="kpi-val neu" style="${vS}">${rows.length.toLocaleString('pt-BR')}</div><div class="kpi-sub" style="${sbS}">apostas no período</div></div>`+
        `<div class="kpi" style="${kS}"><div class="kpi-label"><span class="kpi-pipe"></span>Stake Média</div><div class="kpi-val neu" style="${vS}">${fmtR(avgStake)}</div><div class="kpi-sub" style="${sbS}">por aposta</div></div>`+
        `<div class="kpi" style="${kS}"><div class="kpi-label"><span class="kpi-pipe"></span>Odd Média</div><div class="kpi-val neu" style="${vS}">${fmtOdd(avgOdd)}</div><div class="kpi-sub" style="${sbS}">ponderada</div></div>`+
        `<div class="kpi" style="${kS}"><div class="kpi-label"><span class="kpi-pipe"></span>Win Rate</div><div class="kpi-val neu" style="${vS}">${fmtPct(wr,1,false)}</div><div style="width:100%;height:5px;border-radius:3px;background:rgba(255,255,255,.07);overflow:hidden;margin-top:6px"><div style="height:100%;background:var(--accent-2);border-radius:3px;width:${Math.min(100,Math.max(0,wr)).toFixed(1)}%"></div></div><div class="kpi-sub" style="${sbS}">taxa de acerto</div></div>`+
      `</div>`+
    `</div>`+
    `<div class="analise-popup-section">`+
      `<div class="analise-popup-section-title" style="display:flex;align-items:center;justify-content:space-between">Evolução<span style="font-family:JetBrains Mono,monospace;font-size:9px;text-transform:uppercase;letter-spacing:.18em;color:var(--ink-soft);opacity:.7">P/L diário · evolução acumulada</span></div>`+
      `<div style="display:flex;gap:16px;align-items:center;margin-bottom:10px;flex-wrap:wrap">`+
        `<span style="display:flex;align-items:center;gap:6px;font-size:11px;font-family:var(--font-mono);color:var(--ink-mute)"><span style="display:inline-block;width:20px;height:2px;background:#2E8BFF;border-radius:1px;flex-shrink:0"></span>P/L acumulado</span>`+
        `<span style="display:flex;align-items:center;gap:6px;font-size:11px;font-family:var(--font-mono);color:var(--ink-mute)"><span style="display:inline-block;width:12px;height:12px;background:rgba(43,192,126,.8);border-radius:2px;flex-shrink:0"></span>Dia positivo</span>`+
        `<span style="display:flex;align-items:center;gap:6px;font-size:11px;font-family:var(--font-mono);color:var(--ink-mute)"><span style="display:inline-block;width:12px;height:12px;background:rgba(229,82,75,.8);border-radius:2px;flex-shrink:0"></span>Dia negativo</span>`+
      `</div>`+
      `<div class="chart-wrap" style="height:220px"><canvas id="casaDrillLine"></canvas></div>`+
    `</div>`+
    `<div class="analise-popup-section">`+
      `<div class="analise-popup-section-title">Cenário Atual <span style="font-size:9px;color:var(--ink-mute);text-transform:none;letter-spacing:0">(dados reais · histórico)</span></div>`+
      `<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:.75rem">`+
        `<div class="kpi" style="${kS}"><div class="kpi-label"><span class="kpi-pipe"></span>Topo Histórico ${_mkTipAnchor('Topo Histórico','','Maior saldo que esta casa <b>já atingiu</b> no período.','<span class="lbl">marco</span>')}</div><div class="fdc-kpi__value" data-state="pos" style="${vS}">${fmtPL(_td.topo)}</div><div class="kpi-sub" style="${sbS}">atingido em ${_fmtD(_td.topoData)}</div></div>`+
        `<div class="kpi" style="${kS}"><div class="kpi-label"><span class="kpi-pipe"></span>Drawdown Atual ${_mkTipAnchor('Drawdown Atual','<span class="lbl">DD</span> <span class="op">=</span> Topo <span class="op">→</span> Saldo atual','Quanto o saldo nesta casa está <b>abaixo do último pico</b>, agora.','<span class="thr">perto de 0</span> <span class="good">é o ideal</span>')}</div><div class="fdc-kpi__value" data-state="real" style="${vS}">${fmtPL(-_td.ddAtual)}</div><div class="kpi-sub" style="${sbS}">${fmtPct(_td.ddAtualPct*100,1,false)} do topo</div></div>`+
        `<div class="kpi" style="${kS}"><div class="kpi-label"><span class="kpi-pipe"></span>Max Drawdown ${_mkTipAnchor('Max Drawdown','<span class="lbl">MDD</span> <span class="op">=</span> Pico <span class="op">→</span> Vale','A <b>maior queda real</b> do pico ao vale nesta casa, medida <b>dia a dia</b> em ordem cronológica.',_mddBench)}</div><div class="fdc-kpi__value" data-state="real" style="${vS}">${fmtPL(-_mddR)}</div><div class="kpi-sub" style="${sbS}">${fmtPct(_mddP,1,false)} · pior real</div></div>`+
        `<div class="kpi" style="${kS}"><div class="kpi-label"><span class="kpi-pipe"></span>Recovery Factor ${_mkTipAnchor('Recovery Factor','<span class="lbl">RF</span> <span class="op">=</span> Lucro <span class="op">÷</span> Máx. Drawdown','Quantas vezes o lucro total <b>cobre a maior queda</b>.','<span class="scale"><i></i><i></i><i></i><i class="on"></i><i class="on"></i></span> <span class="thr">&gt; 5</span> <span class="good">muito bom</span>')}</div><div class="fdc-kpi__value" data-state="info" style="${vS}">${_rf!==null?fmtOdd(_rf)+'×':'—'}</div><div class="kpi-sub" style="${sbS}">qualidade</div></div>`+
      `</div>`+
    `</div>`+
    `<div class="analise-popup-section">`+
      `<div class="analise-popup-section-title">Análise Mensal</div>`+
      `<div class="tbl-wrap drill-tbl"><table class="tbl" id="casaDrillTblMensal"><thead><tr>${mkTh('Mês','','l')+mkTh('Bets','','r')+mkTh('P/L','','r')+mkTh('Turnover','','r')+mkTh('ROI','','r')+mkTh('Win Rate','','r')+mkTh('Stake média','','r')+_mkOddMediaTh('r','88px')}</tr></thead><tbody>${_tipMonthTbody(rows)}</tbody></table></div>`+
    `</div>`+
    `<div class="analise-popup-section">`+
      `<div class="analise-popup-section-title">Por Tipster</div>`+
      `<div class="tbl-wrap drill-tbl">${_casaBreakdownTbl(rows,'tipster',t=>esc(t),10,'casaDrillTblTipster')}</div>`+
    `</div>`+
    `<div class="analise-popup-section">`+
      `<div class="analise-popup-section-title">Por Esporte</div>`+
      `<div class="tbl-wrap drill-tbl">${_casaBreakdownTbl(rows,'esporte',sportCell,10,'casaDrillTblEsporte')}</div>`+
    `</div>`;

  // Gráfico Resultado Geral
  const byDayCh={};rows.forEach(r=>{const k=r.data.slice(0,10);byDayCh[k]=(byDayCh[k]||0)+r.lucro;});
  const daysCh=Object.keys(byDayCh).sort();
  if(daysCh.length>=2){
    const dpL=daysCh.map(k=>byDayCh[k]);
    let cum=0;const cumPLCh=dpL.map(v=>{cum+=v;return parseFloat(cum.toFixed(2));});
    const labelStep=Math.max(1,Math.floor(daysCh.length/14));
    const lbl=daysCh.map((d,i)=>{if(i%labelStep!==0&&i!==daysCh.length-1)return'';const p=d.split('-');return p[2]+'/'+p[1];});
    const ptR=cumPLCh.map((_,i)=>i===cumPLCh.length-1?5:0);
    mkChart('casaDrillLine',{type:'bar',data:{labels:lbl,datasets:[
      {type:'line',data:cumPLCh,borderColor:'#2E8BFF',
       backgroundColor:(ctx)=>{const c=ctx.chart,{ctx:cx,chartArea:ca}=c;if(!ca)return'rgba(46,139,255,0)';const g=cx.createLinearGradient(0,ca.top,0,ca.bottom);g.addColorStop(0,'rgba(46,139,255,.16)');g.addColorStop(1,'rgba(46,139,255,0)');return g;},
       tension:.4,fill:true,borderWidth:2,pointRadius:ptR,pointBackgroundColor:'#2E8BFF',pointBorderColor:isDark()?'#12161D':'#ffffff',pointBorderWidth:2,yAxisID:'y1',label:'P/L acumulado'},
      {type:'bar',data:dpL,backgroundColor:dpL.map(v=>v>=0?'rgba(43,192,126,.55)':'rgba(229,82,75,.55)'),hoverBackgroundColor:dpL.map(v=>v>=0?'rgba(43,192,126,.8)':'rgba(229,82,75,.8)'),borderRadius:1,yAxisID:'y',label:'P/L diário',barPercentage:0.9,categoryPercentage:1.0}
    ]},options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx=>(ctx.dataset.label||'')+': '+fmtK(ctx.raw),title:ctx=>{const i=ctx[0].dataIndex;return daysCh[i]?.split('-').reverse().join('/')||'';},}}},
      scales:{x:{display:false},y:{ticks:{color:tc(),font:{size:10},callback:v=>fmtK(v)},grid:{color:gc()},border:{display:false},position:'left'},y1:{ticks:{color:tc(),font:{size:10},callback:v=>fmtK(v)},grid:{display:false},border:{display:false},position:'right'}}
    }});
  }

  // Tooltip para linhas "Outros"
  const tip=_getOutrosTip();
  body.addEventListener('mouseover',function(e){
    const anchor=e.target.closest('.outros-anchor');
    if(!anchor)return;
    const names=anchor.dataset.outros||'';
    tip.textContent=names;
    const r=anchor.getBoundingClientRect();
    tip.style.display='block';
    const tw=tip.offsetWidth;
    tip.style.left=Math.min(r.left,window.innerWidth-tw-16)+'px';
    tip.style.top=(r.bottom+6)+'px';
  });
  body.addEventListener('mouseout',function(e){
    if(!e.target.closest('.outros-anchor'))return;
    tip.style.display='none';
  });

  setTimeout(()=>{
    makeSortable('casaDrillTblMensal',[1,2,3,4,5,6,7]);
    makeSortable('casaDrillTblTipster',[1,2,3,4,5,6,7]);
    makeSortable('casaDrillTblEsporte',[1,2,3,4,5,6,7]);
  },0);
}

function openCasaDrill(nome){
  const overlay=document.getElementById('casaDrillOverlay');
  if(!overlay)return;
  const nameEl=document.getElementById('casaDrillName');
  if(nameEl)nameEl.textContent=nome;
  const chipEl=document.getElementById('casaDrillChip');
  if(chipEl)chipEl.innerHTML=mkHouseChip(nome);

  const sp=msGet('sp_casas');
  _casaDrillBaseName=nome;
  _casaDrillBaseRows=DADOS.filter(r=>{
    if(r.casa!==nome)return false;
    if(sp.size>0&&!sp.has(r.esporte))return false;
    return true;
  });
  _casaDrillPeriodSt=_seedDrillFromPage('casas');
  _casaDrillInheritSt={..._casaDrillPeriodSt};
  _updateCasaDrillChips();

  overlay.style.display='flex';
  document.body.style.overflow='hidden';
  const modal=document.getElementById('casaDrillModal');
  if(modal)modal.scrollTop=0;

  renderCasaDrill(_sliceCasaDrillRows());

  if(_casaDrillEscHandler)document.removeEventListener('keydown',_casaDrillEscHandler);
  _casaDrillEscHandler=function(e){if(e.key==='Escape')closeCasaDrill();};
  document.addEventListener('keydown',_casaDrillEscHandler);
}
window.openCasaDrill=openCasaDrill;

function closeCasaDrill(e){
  if(e&&e.target!==document.getElementById('casaDrillOverlay'))return;
  const overlay=document.getElementById('casaDrillOverlay');
  if(overlay)overlay.style.display='none';
  document.body.style.overflow='';
  if(_casaDrillEscHandler){document.removeEventListener('keydown',_casaDrillEscHandler);_casaDrillEscHandler=null;}
}
window.closeCasaDrill=closeCasaDrill;

window.copyCasaDrill=async function(){
  const modal=document.getElementById('casaDrillModal');
  if(!modal)return;
  const btn=modal.querySelector('.copy-casa-drill-btn');
  const btnOrig=btn?btn.innerHTML:null;
  if(btn){btn.disabled=true;btn.innerHTML='…';}
  const ok=await _waitH2C();
  if(!ok){if(btn){btn.disabled=false;btn.innerHTML=btnOrig;}return;}
  const{canvas}=await _buildDrillCanvas(modal);
  if(!canvas){if(btn){btn.disabled=false;btn.innerHTML=btnOrig;}return;}
  canvas.toBlob(async blob=>{
    try{
      await navigator.clipboard.write([new ClipboardItem({'image/png':blob})]);
      if(btn){btn.innerHTML='✓';setTimeout(()=>{btn.disabled=false;btn.innerHTML=btnOrig;},2000);}
    }catch(e){
      if(btn){btn.innerHTML='✗';setTimeout(()=>{btn.disabled=false;btn.innerHTML=btnOrig;},1500);}
    }
  },'image/png');
};

window.saveCasaDrill=async function(){
  const modal=document.getElementById('casaDrillModal');
  if(!modal)return;
  const btn=modal.querySelector('.save-casa-drill-btn');
  const btnOrig=btn?btn.innerHTML:null;
  if(btn){btn.disabled=true;btn.innerHTML='…';}
  const ok=await _waitH2C();
  if(!ok){if(btn){btn.disabled=false;btn.innerHTML=btnOrig;}return;}
  const{canvas}=await _buildDrillCanvas(modal);
  if(!canvas){if(btn){btn.disabled=false;btn.innerHTML=btnOrig;}return;}
  canvas.toBlob(blob=>{
    const url=URL.createObjectURL(blob);
    const a=Object.assign(document.createElement('a'),{href:url,download:'bookie-'+((_casaDrillBaseName||'drill').replace(/\s+/g,'_'))+'.png'});
    a.click();
    setTimeout(()=>URL.revokeObjectURL(url),5000);
    if(btn){btn.innerHTML='✓';setTimeout(()=>{btn.disabled=false;btn.innerHTML=btnOrig;},2000);}
  },'image/png');
};

// ── Sport drill-down ─────────────────────────────────────────────────────────
let _sportDrillEscHandler=null;
let _sportDrillBaseName=null,_sportDrillBaseRows=[],_sportDrillPeriodSt={qd:0,qt:'',df:'',dt:''},_sportDrillInheritSt=null;

function _sliceSportDrillRows(){return _sliceByPeriod(_sportDrillBaseRows,_sportDrillPeriodSt);}

function _updateSportDrillChips(){_updateDrillPeriodBar('sportDrillPeriodBar',_sportDrillPeriodSt,_sportDrillInheritSt);}

window.setDrillSportQuick=function(d){_sportDrillPeriodSt={qd:d,qt:'',df:'',dt:''};_updateSportDrillChips();renderSportDrill(_sliceSportDrillRows());};
window.setDrillSportType=function(qt){_sportDrillPeriodSt={qd:0,qt:qt,df:'',dt:''};_updateSportDrillChips();renderSportDrill(_sliceSportDrillRows());};
window.setDrillSportAll=function(){_sportDrillPeriodSt={qd:0,qt:'',df:'',dt:''};_updateSportDrillChips();renderSportDrill(_sliceSportDrillRows());};
window.setDrillSportInherit=function(){if(!_sportDrillInheritSt)return;_sportDrillPeriodSt={..._sportDrillInheritSt};_updateSportDrillChips();renderSportDrill(_sliceSportDrillRows());};

function renderSportDrill(rows){
  const pl=rows.reduce((a,r)=>a+r.lucro,0);
  const s=calcTurnover(rows);   // turnover exclui Void
  const roi=s>0?pl/s*100:0;
  const settled=rows.filter(r=>r.resultado!=='V');
  const wins=settled.filter(r=>['W','HW'].includes(r.resultado)).length;
  const wr=wrPctRows(rows);
  const wt=rows.reduce((a,r)=>r.odd>0&&r.stake>0?a+r.odd*r.stake:a,0);
  const stk=rows.reduce((a,r)=>r.odd>0&&r.stake>0?a+r.stake:a,0);
  const avgOdd=stk>0?wt/stk:0;
  const avgStake=settled.length?s/settled.length:0;   // turnover ÷ encerradas (exclui Void)
  const plCls=pl>=0?'pos':'neg';
  const roiCls=roi>=0?'pos':'neg';

  const _td=calcTopoDrawdown(rows),_rf=calcRecoveryFactor(rows),_dd=calcDrawdownReal(rows),_mddR=_dd.mddReais,_mddP=_dd.mddPct;
  const _fmtD=d=>{if(!d)return'—';const p=d.slice(0,10).split('-');return p[2]+'/'+p[1]+'/'+p[0];};
  const _mddBench=_dd.troughDate?`<span class="lbl">vale em ${_fmtD(_dd.troughDate)}</span> · <span class="thr">quanto menor, melhor</span>`:'<span class="thr">quanto menor, melhor</span>';

  const body=document.getElementById('sportDrillBody');
  if(!body)return;

  const kS='display:flex;flex-direction:column;min-width:0;overflow:visible';
  const sbS='margin-top:auto;padding-top:6px';
  const vS='font-size:16px';

  body.innerHTML=
    `<div class="analise-popup-section">`+
      `<div class="analise-popup-section-title">Resultado Geral</div>`+
      `<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;align-items:stretch;width:100%;margin-bottom:8px">`+
        `<div class="kpi" style="${kS}"><div class="kpi-label"><span class="kpi-pipe"></span>P/L</div><div class="kpi-val ${plCls}" style="${vS}">${fmtPL(pl)}</div><div class="kpi-sub" style="${sbS}">resultado no período</div></div>`+
        `<div class="kpi" style="${kS}"><div class="kpi-label"><span class="kpi-pipe"></span>ROI</div><div class="kpi-val ${roiCls}" style="${vS}">${fmtPct(roi,2)}</div><div class="kpi-sub" style="${sbS}">Σ(P/L)/Σ(turnover)</div></div>`+
        `<div class="kpi" style="${kS}"><div class="kpi-label"><span class="kpi-pipe"></span>Turnover</div><div class="kpi-val neu" style="${vS}">${fmtR(s)}</div><div class="kpi-sub" style="${sbS}">volume apostado</div></div>`+
        `<div class="kpi" style="${kS}"><div class="kpi-label"><span class="kpi-pipe"></span>Win Rate</div><div class="kpi-val neu" style="${vS}">${fmtPct(wr,1,false)}</div><div style="width:100%;height:5px;border-radius:3px;background:rgba(255,255,255,.07);overflow:hidden;margin-top:6px"><div style="height:100%;background:var(--accent-2);border-radius:3px;width:${Math.min(100,Math.max(0,wr)).toFixed(1)}%"></div></div><div class="kpi-sub" style="${sbS}">taxa de acerto</div></div>`+
      `</div>`+
      `<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;align-items:stretch;width:100%">`+
        `<div class="kpi" style="${kS}"><div class="kpi-label"><span class="kpi-pipe"></span>Volume</div><div class="kpi-val neu" style="${vS}">${rows.length.toLocaleString('pt-BR')}</div><div class="kpi-sub" style="${sbS}">apostas no período</div></div>`+
        `<div class="kpi" style="${kS}"><div class="kpi-label"><span class="kpi-pipe"></span>Encerradas</div><div class="kpi-val neu" style="${vS}">${settled.length.toLocaleString('pt-BR')}</div><div class="kpi-sub" style="${sbS}">exclui Void</div></div>`+
        `<div class="kpi" style="${kS}"><div class="kpi-label"><span class="kpi-pipe"></span>Stake Média</div><div class="kpi-val neu" style="${vS}">${fmtR(avgStake)}</div><div class="kpi-sub" style="${sbS}">por aposta</div></div>`+
        `<div class="kpi" style="${kS}"><div class="kpi-label"><span class="kpi-pipe"></span>Odd Média</div><div class="kpi-val neu" style="${vS}">${fmtOdd(avgOdd)}</div><div class="kpi-sub" style="${sbS}">ponderada</div></div>`+
      `</div>`+
    `</div>`+
    `<div class="analise-popup-section">`+
      `<div class="analise-popup-section-title" style="display:flex;align-items:center;justify-content:space-between">Evolução<span style="font-family:JetBrains Mono,monospace;font-size:9px;text-transform:uppercase;letter-spacing:.18em;color:var(--ink-soft);opacity:.7">P/L diário · evolução acumulada</span></div>`+
      `<div style="display:flex;gap:16px;align-items:center;margin-bottom:10px;flex-wrap:wrap">`+
        `<span style="display:flex;align-items:center;gap:6px;font-size:11px;font-family:var(--font-mono);color:var(--ink-mute)"><span style="display:inline-block;width:20px;height:2px;background:#2E8BFF;border-radius:1px;flex-shrink:0"></span>P/L acumulado</span>`+
        `<span style="display:flex;align-items:center;gap:6px;font-size:11px;font-family:var(--font-mono);color:var(--ink-mute)"><span style="display:inline-block;width:12px;height:12px;background:rgba(43,192,126,.8);border-radius:2px;flex-shrink:0"></span>Dia positivo</span>`+
        `<span style="display:flex;align-items:center;gap:6px;font-size:11px;font-family:var(--font-mono);color:var(--ink-mute)"><span style="display:inline-block;width:12px;height:12px;background:rgba(229,82,75,.8);border-radius:2px;flex-shrink:0"></span>Dia negativo</span>`+
      `</div>`+
      `<div class="chart-wrap" style="height:220px"><canvas id="sportDrillLine"></canvas></div>`+
    `</div>`+
    `<div class="analise-popup-section">`+
      `<div class="analise-popup-section-title">Cenário Atual <span style="font-size:9px;color:var(--ink-mute);text-transform:none;letter-spacing:0">(dados reais · histórico)</span></div>`+
      `<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:.75rem">`+
        `<div class="kpi" style="${kS}"><div class="kpi-label"><span class="kpi-pipe"></span>Topo Histórico ${_mkTipAnchor('Topo Histórico','','Maior saldo que este esporte <b>já atingiu</b> no período.','<span class="lbl">marco</span>')}</div><div class="fdc-kpi__value" data-state="pos" style="${vS}">${fmtPL(_td.topo)}</div><div class="kpi-sub" style="${sbS}">atingido em ${_fmtD(_td.topoData)}</div></div>`+
        `<div class="kpi" style="${kS}"><div class="kpi-label"><span class="kpi-pipe"></span>Drawdown Atual ${_mkTipAnchor('Drawdown Atual','<span class="lbl">DD</span> <span class="op">=</span> Topo <span class="op">→</span> Saldo atual','Quanto o saldo neste esporte está <b>abaixo do último pico</b>, agora.','<span class="thr">perto de 0</span> <span class="good">é o ideal</span>')}</div><div class="fdc-kpi__value" data-state="real" style="${vS}">${fmtPL(-_td.ddAtual)}</div><div class="kpi-sub" style="${sbS}">${fmtPct(_td.ddAtualPct*100,1,false)} do topo</div></div>`+
        `<div class="kpi" style="${kS}"><div class="kpi-label"><span class="kpi-pipe"></span>Max Drawdown ${_mkTipAnchor('Max Drawdown','<span class="lbl">MDD</span> <span class="op">=</span> Pico <span class="op">→</span> Vale','A <b>maior queda real</b> do pico ao vale neste esporte, medida <b>dia a dia</b> em ordem cronológica.',_mddBench)}</div><div class="fdc-kpi__value" data-state="real" style="${vS}">${fmtPL(-_mddR)}</div><div class="kpi-sub" style="${sbS}">${fmtPct(_mddP,1,false)} · pior real</div></div>`+
        `<div class="kpi" style="${kS}"><div class="kpi-label"><span class="kpi-pipe"></span>Recovery Factor ${_mkTipAnchor('Recovery Factor','<span class="lbl">RF</span> <span class="op">=</span> Lucro <span class="op">÷</span> Máx. Drawdown','Quantas vezes o lucro total <b>cobre a maior queda</b>.','<span class="scale"><i></i><i></i><i></i><i class="on"></i><i class="on"></i></span> <span class="thr">&gt; 5</span> <span class="good">muito bom</span>')}</div><div class="fdc-kpi__value" data-state="info" style="${vS}">${_rf!==null?fmtOdd(_rf)+'×':'—'}</div><div class="kpi-sub" style="${sbS}">qualidade</div></div>`+
      `</div>`+
    `</div>`+
    `<div class="analise-popup-section">`+
      `<div class="analise-popup-section-title">Análise Mensal</div>`+
      `<div class="tbl-wrap drill-tbl"><table class="tbl" id="sportDrillTblMensal"><thead><tr>${mkTh('Mês','','l')+mkTh('Bets','','r')+mkTh('P/L','','r')+mkTh('Turnover','','r')+mkTh('ROI','','r')+mkTh('Win Rate','','r')+mkTh('Stake média','','r')+_mkOddMediaTh('r','88px')}</tr></thead><tbody>${_tipMonthTbody(rows)}</tbody></table></div>`+
    `</div>`+
    `<div class="analise-popup-section">`+
      `<div class="analise-popup-section-title">Por Casa</div>`+
      `<div class="tbl-wrap drill-tbl">${_casaBreakdownTbl(rows,'casa',casaCell,10,'sportDrillTblCasa')}</div>`+
    `</div>`+
    `<div class="analise-popup-section">`+
      `<div class="analise-popup-section-title">Por Tipster</div>`+
      `<div class="tbl-wrap drill-tbl">${_casaBreakdownTbl(rows,'tipster',t=>esc(t),10,'sportDrillTblTipster')}</div>`+
    `</div>`;

  // Gráfico Resultado Geral
  const byDayCh={};rows.forEach(r=>{const k=r.data.slice(0,10);byDayCh[k]=(byDayCh[k]||0)+r.lucro;});
  const daysCh=Object.keys(byDayCh).sort();
  if(daysCh.length>=2){
    const dpL=daysCh.map(k=>byDayCh[k]);
    let cum=0;const cumPLCh=dpL.map(v=>{cum+=v;return parseFloat(cum.toFixed(2));});
    const labelStep=Math.max(1,Math.floor(daysCh.length/14));
    const lbl=daysCh.map((d,i)=>{if(i%labelStep!==0&&i!==daysCh.length-1)return'';const p=d.split('-');return p[2]+'/'+p[1];});
    const ptR=cumPLCh.map((_,i)=>i===cumPLCh.length-1?5:0);
    mkChart('sportDrillLine',{type:'bar',data:{labels:lbl,datasets:[
      {type:'line',data:cumPLCh,borderColor:'#2E8BFF',
       backgroundColor:(ctx)=>{const c=ctx.chart,{ctx:cx,chartArea:ca}=c;if(!ca)return'rgba(46,139,255,0)';const g=cx.createLinearGradient(0,ca.top,0,ca.bottom);g.addColorStop(0,'rgba(46,139,255,.16)');g.addColorStop(1,'rgba(46,139,255,0)');return g;},
       tension:.4,fill:true,borderWidth:2,pointRadius:ptR,pointBackgroundColor:'#2E8BFF',pointBorderColor:isDark()?'#12161D':'#ffffff',pointBorderWidth:2,yAxisID:'y1',label:'P/L acumulado'},
      {type:'bar',data:dpL,backgroundColor:dpL.map(v=>v>=0?'rgba(43,192,126,.55)':'rgba(229,82,75,.55)'),hoverBackgroundColor:dpL.map(v=>v>=0?'rgba(43,192,126,.8)':'rgba(229,82,75,.8)'),borderRadius:1,yAxisID:'y',label:'P/L diário',barPercentage:0.9,categoryPercentage:1.0}
    ]},options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx=>(ctx.dataset.label||'')+': '+fmtK(ctx.raw),title:ctx=>{const i=ctx[0].dataIndex;return daysCh[i]?.split('-').reverse().join('/')||'';},}}},
      scales:{x:{display:false},y:{ticks:{color:tc(),font:{size:10},callback:v=>fmtK(v)},grid:{color:gc()},border:{display:false},position:'left'},y1:{ticks:{color:tc(),font:{size:10},callback:v=>fmtK(v)},grid:{display:false},border:{display:false},position:'right'}}
    }});
  }

  // Tooltip para linhas "Outros"
  const tip=_getOutrosTip();
  body.addEventListener('mouseover',function(e){
    const anchor=e.target.closest('.outros-anchor');
    if(!anchor)return;
    const names=anchor.dataset.outros||'';
    tip.textContent=names;
    const r=anchor.getBoundingClientRect();
    tip.style.display='block';
    const tw=tip.offsetWidth;
    tip.style.left=Math.min(r.left,window.innerWidth-tw-16)+'px';
    tip.style.top=(r.bottom+6)+'px';
  });
  body.addEventListener('mouseout',function(e){
    if(!e.target.closest('.outros-anchor'))return;
    tip.style.display='none';
  });

  setTimeout(()=>{
    makeSortable('sportDrillTblMensal',[1,2,3,4,5,6,7]);
    makeSortable('sportDrillTblCasa',[1,2,3,4,5,6,7]);
    makeSortable('sportDrillTblTipster',[1,2,3,4,5,6,7]);
  },0);
}

function openSportDrill(sport){
  const overlay=document.getElementById('sportDrillOverlay');
  if(!overlay)return;
  const nameEl=document.getElementById('sportDrillName');
  if(nameEl)nameEl.textContent=sport;
  const chipEl=document.getElementById('sportDrillChip');
  if(chipEl)chipEl.innerHTML=mkSpChip(sport);

  const ca=msGet('ca_sports');
  _sportDrillBaseName=sport;
  _sportDrillBaseRows=DADOS.filter(r=>{
    if(r.esporte!==sport)return false;
    if(ca.size>0&&!ca.has(r.casa))return false;
    return true;
  });
  _sportDrillPeriodSt=_seedDrillFromPage('sports');
  _sportDrillInheritSt={..._sportDrillPeriodSt};
  _updateSportDrillChips();

  overlay.style.display='flex';
  document.body.style.overflow='hidden';
  const modal=document.getElementById('sportDrillModal');
  if(modal)modal.scrollTop=0;

  renderSportDrill(_sliceSportDrillRows());

  if(_sportDrillEscHandler)document.removeEventListener('keydown',_sportDrillEscHandler);
  _sportDrillEscHandler=function(e){if(e.key==='Escape')closeSportDrill();};
  document.addEventListener('keydown',_sportDrillEscHandler);
}
window.openSportDrill=openSportDrill;

function closeSportDrill(e){
  if(e&&e.target!==document.getElementById('sportDrillOverlay'))return;
  const overlay=document.getElementById('sportDrillOverlay');
  if(overlay)overlay.style.display='none';
  document.body.style.overflow='';
  if(_sportDrillEscHandler){document.removeEventListener('keydown',_sportDrillEscHandler);_sportDrillEscHandler=null;}
}
window.closeSportDrill=closeSportDrill;

window.copySportDrill=async function(){
  const modal=document.getElementById('sportDrillModal');
  if(!modal)return;
  const btn=modal.querySelector('.copy-sport-drill-btn');
  const btnOrig=btn?btn.innerHTML:null;
  if(btn){btn.disabled=true;btn.innerHTML='…';}
  const ok=await _waitH2C();
  if(!ok){if(btn){btn.disabled=false;btn.innerHTML=btnOrig;}return;}
  const{canvas}=await _buildDrillCanvas(modal);
  if(!canvas){if(btn){btn.disabled=false;btn.innerHTML=btnOrig;}return;}
  canvas.toBlob(async blob=>{
    try{
      await navigator.clipboard.write([new ClipboardItem({'image/png':blob})]);
      if(btn){btn.innerHTML='✓';setTimeout(()=>{btn.disabled=false;btn.innerHTML=btnOrig;},2000);}
    }catch(e){
      if(btn){btn.innerHTML='✗';setTimeout(()=>{btn.disabled=false;btn.innerHTML=btnOrig;},1500);}
    }
  },'image/png');
};

window.saveSportDrill=async function(){
  const modal=document.getElementById('sportDrillModal');
  if(!modal)return;
  const btn=modal.querySelector('.save-sport-drill-btn');
  const btnOrig=btn?btn.innerHTML:null;
  if(btn){btn.disabled=true;btn.innerHTML='…';}
  const ok=await _waitH2C();
  if(!ok){if(btn){btn.disabled=false;btn.innerHTML=btnOrig;}return;}
  const{canvas}=await _buildDrillCanvas(modal);
  if(!canvas){if(btn){btn.disabled=false;btn.innerHTML=btnOrig;}return;}
  canvas.toBlob(blob=>{
    const url=URL.createObjectURL(blob);
    const a=Object.assign(document.createElement('a'),{href:url,download:'esporte-'+((_sportDrillBaseName||'drill').replace(/\s+/g,'_'))+'.png'});
    a.click();
    setTimeout(()=>URL.revokeObjectURL(url),5000);
    if(btn){btn.innerHTML='✓';setTimeout(()=>{btn.disabled=false;btn.innerHTML=btnOrig;},2000);}
  },'image/png');
};

// ── tcard helpers (T-1) ─────────────────────────────────────────────────────
let _tipsterEnts=null,_tipsterDays=null,_tipsterAllDays=null;
let _tipsterSort={k:'pl',dir:1};

function _tipSparkSVG(dayMap,allDays){
  let cum=0;
  const vals=allDays.map(d=>{cum+=(dayMap[d]||0);return cum;});
  if(vals.length<2)return'<svg class="tcard__spark" viewBox="0 0 240 30" preserveAspectRatio="none"></svg>';
  const min=Math.min(...vals),max=Math.max(...vals),rng=max-min||1;
  const W=240,H=30,pad=2;
  const ptStr=vals.map((v,i)=>{
    const x=pad+(i/(vals.length-1))*(W-pad*2);
    const y=H-pad-((v-min)/rng)*(H-pad*2);
    return x.toFixed(1)+','+y.toFixed(1);
  }).join(' ');
  const last=ptStr.split(' ').pop().split(',');
  return`<svg class="tcard__spark" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none">`
    +`<polyline points="${ptStr}" fill="none" stroke="var(--ink-mute)" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round" opacity="0.75" vector-effect="non-scaling-stroke"/>`
    +`<circle cx="${last[0]}" cy="${last[1]}" r="2.6" fill="var(--accent)" vector-effect="non-scaling-stroke"/>`
    +`</svg>`;
}

function _mkTipCard(name,pl,roi,stake,wr,bets,sparkSVG,avgStake,avgOdd){
  const plSign=pl>=0?'+':'−';
  const plCls=pl>=0?'pos':'neg';
  const roiCls=roi>=0?'pos':'neg';
  const plAmt=Math.abs(pl).toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2});
  const stakeInt=Math.round(stake).toLocaleString('pt-BR');
  const avgStakeStr=Math.round(avgStake||0).toLocaleString('pt-BR');
  const avgOddStr=fmtOdd(avgOdd);
  const betsStr=bets.toLocaleString('pt-BR');
  const roiStr=fmtPct(roi,1);
  const wrStr=fmtPct(wr,1,false);
  const wrPct=Math.min(wr,100).toFixed(1);
  const escAttr=esc(name);
  return`<div class="tcard" data-name="${escAttr}">`
    +`<div class="tcard__top"><span class="nametag"><span class="nametag__nm" title="${escAttr}">${esc(name)}</span></span><span class="tcard__vol"><b>${betsStr}</b>apostas</span></div>`
    +`<div class="tcard__hero"><span class="tcard__pl ${plCls}"><span class="tcard__cur">${plSign} R$</span>${plAmt}</span><div class="tcard__roi"><span class="tcard__roi-lbl">ROI</span><span class="tcard__roi-val ${roiCls}">${roiStr}</span></div></div>`
    +sparkSVG
    +`<div class="tcard__foot">`
      +`<div class="tcard__stat"><div class="tcard__stat-lbl">Turnover</div><div class="tcard__stat-val"><span class="tcard__cur--sm">R$</span>${stakeInt}</div></div>`
      +`<div class="tcard__stat"><div class="tcard__stat-lbl">Stake Média</div><div class="tcard__stat-val"><span class="tcard__cur--sm">R$</span>${avgStakeStr}</div></div>`
      +`<div class="tcard__stat"><div class="tcard__stat-lbl">Odd Média ${_mkOddTip()}</div><div class="tcard__stat-val">${avgOddStr}</div></div>`
      +`<div class="tcard__stat"><div class="tcard__stat-lbl">Win Rate</div><div class="tcard__stat-val">${wrStr}</div><div class="tcard__wrbar"><div class="tcard__wrfill" style="width:${wrPct}%"></div></div></div>`
    +`</div>`
    +`</div>`;
}

function _renderTipCards(){
  const el=document.getElementById('tipsterKpiCards');
  if(!el||!_tipsterEnts)return;
  if(!_tipsterEnts.length){el.innerHTML=mkEmpty('Nenhum tipster no período');return;}
  const {k,dir}=_tipsterSort;
  const fns={pl:([,d])=>d.l,roi:([,d])=>d.s>0?d.l/d.s*100:0,to:([,d])=>d.s,wr:([,d])=>wrFrac(d.w,d.hw,d.hl,d.t),vol:([,d])=>d.n};
  const fn=fns[k]||fns.pl;
  const sorted=[..._tipsterEnts].sort((a,b)=>dir*(fn(b)-fn(a)));
  el.innerHTML=sorted.map(([t,d])=>{
    const roi=d.s>0?(d.l/d.s*100):0,wr=wrFrac(d.w,d.hw,d.hl,d.t);
    const avgStake=d.t>0?d.s/d.t:0,avgOdd=d.stk>0?d.wt/d.stk:0;
    return _mkTipCard(t,d.l,roi,d.s,wr,d.n,_tipSparkSVG(_tipsterDays[t]||{},_tipsterAllDays),avgStake,avgOdd);
  }).join('');
  el.onclick=function(e){if(e.target.closest('.tip-anchor'))return;const card=e.target.closest('.tcard');if(card&&card.dataset.name)openTipsterDrill(card.dataset.name);};
  document.querySelectorAll('#tipsterSeg button').forEach(btn=>btn.classList.toggle('active',btn.dataset.k===k));
  const dirBtn=document.getElementById('tipsterDir');
  if(dirBtn)dirBtn.textContent=dir<0?'↓':'↑';
}
window.tipsterSortBy=function(k){_tipsterSort.k=k;_tipsterSort.dir=1;_renderTipCards();};
window.tipsterSortDir=function(){_tipsterSort.dir*=-1;_renderTipCards();};

// ── T-6: drill-down popup ────────────────────────────────────────────────────
let _drillEscHandler=null;
let _drillBaseName=null,_drillBaseRows=[],_drillPeriodSt={qd:0,qt:'',df:'',dt:''},_drillInheritSt=null;

function _sliceDrillRows(){return _sliceByPeriod(_drillBaseRows,_drillPeriodSt);}

function _updateDrillChips(){_updateDrillPeriodBar('tipsterDrillPeriodBar',_drillPeriodSt,_drillInheritSt);}

function renderTipsterDrill(rows){
  const nome=_drillBaseName;
  const pl=rows.reduce((a,r)=>a+r.lucro,0);
  const s=calcTurnover(rows);   // turnover exclui Void
  const roi=s>0?pl/s*100:0;
  const settled=rows.filter(r=>r.resultado!=='V');
  const wins=settled.filter(r=>['W','HW'].includes(r.resultado)).length;
  const wr=wrPctRows(rows);
  const wt=rows.reduce((a,r)=>r.odd>0&&r.stake>0?a+r.odd*r.stake:a,0);
  const stk=rows.reduce((a,r)=>r.odd>0&&r.stake>0?a+r.stake:a,0);
  const avgOdd=stk>0?wt/stk:0;
  const plCls=pl>=0?'pos':'neg';
  const roiCls=roi>=0?'pos':'neg';

  // Diagnóstico de risco
  const _td=calcTopoDrawdown(rows),_mc=calcMCdrawdown(rows,10000),_rf=calcRecoveryFactor(rows),_pv=calcPValueMC(rows,10000),_dd=calcDrawdownReal(rows),_mddR=_dd.mddReais,_mddP=_dd.mddPct,_profit=_td.atual;
  const _sol=calcSolidez({pValue:_pv,profitXmdd:_mc.xmdd>0?_profit/_mc.xmdd:0,nApostas:rows.length,oddMedia:calcAvgOdd(rows)});
  const _solCor=_sol.score>=0.65?'var(--d-pos)':_sol.score>=0.45?'var(--d-proj)':'var(--d-neg)';
  const _fmtD=d=>{if(!d)return'—';const p=d.slice(0,10).split('-');return p[2]+'/'+p[1]+'/'+p[0];};
  const _mddBench=_dd.troughDate?`<span class="lbl">vale em ${_fmtD(_dd.troughDate)}</span> · <span class="thr">quanto menor, melhor</span>`:'<span class="thr">quanto menor, melhor</span>';

  const body=document.getElementById('tipsterDrillBody');
  if(!body)return;

  // KPIs — 5 cards simétricos (1 row, repeat 5, font-xl para caber)
  const avgStake=settled.length?s/settled.length:0;   // turnover ÷ encerradas (exclui Void)
  const kS='display:flex;flex-direction:column;min-width:0;overflow:visible';
  const sbS='margin-top:auto;padding-top:6px';
  const vS='font-size:16px';

  body.innerHTML=
    `<div class="analise-popup-section">`+
      `<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:8px;align-items:stretch;width:100%">`+
        `<div class="kpi" style="${kS}"><div class="kpi-label"><span class="kpi-pipe"></span>P/L</div><div class="kpi-val ${plCls}" style="${vS}">${fmtPL(pl)}</div><div class="kpi-sub" style="${sbS}">${rows.length.toLocaleString('pt-BR')} apostas</div></div>`+
        `<div class="kpi" style="${kS}"><div class="kpi-label"><span class="kpi-pipe"></span>ROI</div><div class="kpi-val ${roiCls}" style="${vS}">${fmtPct(roi,2)}</div><div class="kpi-sub" style="${sbS}">Σ(P/L)/Σ(turnover)</div></div>`+
        `<div class="kpi" style="${kS}"><div class="kpi-label"><span class="kpi-pipe"></span>Stake Média</div><div class="kpi-val neu" style="${vS}">${fmtR(avgStake)}</div><div class="kpi-sub" style="${sbS}">por aposta</div></div>`+
        `<div class="kpi" style="${kS}"><div class="kpi-label"><span class="kpi-pipe"></span>Odd Média</div><div class="kpi-val neu" style="${vS}">${fmtOdd(avgOdd)}</div><div class="kpi-sub" style="${sbS}">ponderada</div></div>`+
        `<div class="kpi" style="${kS}"><div class="kpi-label"><span class="kpi-pipe"></span>Win Rate</div><div class="kpi-val neu" style="${vS}">${fmtPct(wr,1,false)}</div><div style="width:100%;height:5px;border-radius:3px;background:rgba(255,255,255,.07);overflow:hidden;margin-top:6px"><div style="height:100%;background:var(--accent-2);border-radius:3px;width:${Math.min(100,Math.max(0,wr)).toFixed(1)}%"></div></div><div class="kpi-sub" style="${sbS}">taxa de acerto</div></div>`+
      `</div>`+
    `</div>`+
    `<div class="analise-popup-section" id="tipDrillGestao"></div>`+
    `<div class="analise-popup-section">`+
      `<div class="analise-popup-section-title" style="display:flex;align-items:center;justify-content:space-between">Resultado Geral<span style="font-family:JetBrains Mono,monospace;font-size:9px;text-transform:uppercase;letter-spacing:.18em;color:var(--ink-soft);opacity:.7">P/L diário · evolução acumulada</span></div>`+
      `<div style="display:flex;gap:16px;align-items:center;margin-bottom:10px;flex-wrap:wrap">`+
        `<span style="display:flex;align-items:center;gap:6px;font-size:11px;font-family:var(--font-mono);color:var(--ink-mute)"><span style="display:inline-block;width:20px;height:2px;background:#2E8BFF;border-radius:1px;flex-shrink:0"></span>P/L acumulado</span>`+
        `<span style="display:flex;align-items:center;gap:6px;font-size:11px;font-family:var(--font-mono);color:var(--ink-mute)"><span style="display:inline-block;width:12px;height:12px;background:rgba(43,192,126,.8);border-radius:2px;flex-shrink:0"></span>Dia positivo</span>`+
        `<span style="display:flex;align-items:center;gap:6px;font-size:11px;font-family:var(--font-mono);color:var(--ink-mute)"><span style="display:inline-block;width:12px;height:12px;background:rgba(229,82,75,.8);border-radius:2px;flex-shrink:0"></span>Dia negativo</span>`+
      `</div>`+
      `<div class="chart-wrap" style="height:220px"><canvas id="tipsterDrillLine"></canvas></div>`+
    `</div>`+
    `<div class="analise-popup-section">`+
      `<div class="analise-popup-section-title">Cenário Atual <span style="font-size:9px;color:var(--ink-mute);text-transform:none;letter-spacing:0">(dados reais · histórico)</span></div>`+
      `<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:.75rem">`+
        `<div class="kpi" style="${kS}">`+
          `<div class="kpi-label"><span class="kpi-pipe"></span>Topo Histórico ${_mkTipAnchor('Topo Histórico','','Maior saldo que a banca <b>já atingiu</b> no período.','<span class="lbl">marco</span>')}</div>`+
          `<div class="fdc-kpi__value" data-state="pos" style="${vS}">${fmtPL(_td.topo)}</div>`+
          `<div class="kpi-sub" style="${sbS}">atingido em ${_fmtD(_td.topoData)}</div>`+
        `</div>`+
        `<div class="kpi" style="${kS}">`+
          `<div class="kpi-label"><span class="kpi-pipe"></span>Drawdown Atual ${_mkTipAnchor('Drawdown Atual','<span class="lbl">DD</span> <span class="op">=</span> Topo <span class="op">→</span> Saldo atual','Quanto a banca está <b>abaixo do último pico</b>, agora.','<span class="thr">perto de 0</span> <span class="good">é o ideal</span>')}</div>`+
          `<div class="fdc-kpi__value" data-state="real" style="${vS}">${fmtPL(-_td.ddAtual)}</div>`+
          `<div class="kpi-sub" style="${sbS}">${fmtPct(_td.ddAtualPct*100,1,false)} do topo</div>`+
        `</div>`+
        `<div class="kpi" style="${kS}">`+
          `<div class="kpi-label"><span class="kpi-pipe"></span>Max Drawdown ${_mkTipAnchor('Max Drawdown','<span class="lbl">MDD</span> <span class="op">=</span> Pico <span class="op">→</span> Vale','A <b>maior queda real</b> do pico ao vale da banca, medida <b>dia a dia</b> em ordem cronológica — a mesma curva do gráfico.',_mddBench)}</div>`+
          `<div class="fdc-kpi__value" data-state="real" style="${vS}">${fmtPL(-_mddR)}</div>`+
          `<div class="kpi-sub" style="${sbS}">${fmtPct(_mddP,1,false)} · pior real</div>`+
        `</div>`+
        `<div class="kpi" style="${kS}">`+
          `<div class="kpi-label"><span class="kpi-pipe"></span>Recovery Factor ${_mkTipAnchor('Recovery Factor','<span class="lbl">RF</span> <span class="op">=</span> Lucro <span class="op">÷</span> Máx. Drawdown','Quantas vezes o lucro total <b>cobre a maior queda</b> da banca.','<span class="scale"><i></i><i></i><i></i><i class="on"></i><i class="on"></i></span> <span class="thr">&gt; 5</span> <span class="good">muito bom</span>')}</div>`+
          `<div class="fdc-kpi__value" data-state="info" style="${vS};text-align:right">${_rf!==null?fmtOdd(_rf)+'×':'—'}</div>`+
          `<div class="kpi-sub" style="${sbS}">qualidade</div>`+
        `</div>`+
      `</div>`+
    `</div>`+
    `<div class="analise-popup-section">`+
      `<div class="analise-popup-section-title">Diagnóstico de Risco <span style="font-size:9px;color:var(--ink-mute);text-transform:none;letter-spacing:0">(Monte Carlo · 10.000 simulações)</span></div>`+
      `<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:.75rem">`+
        `<div class="kpi" style="${kS}">`+
          `<div class="kpi-label"><span class="kpi-pipe"></span>p-value ${_mkTipAnchor('P-Value','<span class="lbl">p</span> <span class="op">=</span> P(resultado <span class="lbl">|</span> acaso)','Indicador heurístico (bootstrap): quão improvável seria seu resultado por <b>acaso</b>, sem vantagem. Menor = destaca-se mais do acaso — <b>não é prova estatística nem recomendação</b>.',rodapePValue(_pv))}</div>`+
          `<div class="fdc-kpi__value" data-state="${_pv<0.05?'pos':'proj'}" style="${vS}">${_pv<0.001?'< 0,001':fmt(_pv,4)}</div>`+
          `<div class="kpi-sub" style="${sbS}">${_pv<0.001?'sinal forte':_pv<0.05?'destaca do acaso':'inconclusivo'}</div>`+
        `</div>`+
        `<div class="kpi" style="${kS}">`+
          `<div class="kpi-label"><span class="kpi-pipe"></span>DD Médio ${_mkTipAnchor('DD Médio','<span class="lbl">média</span> dos DD simulados','Queda <b>típica projetada</b> (média das 10.000 simulações de Monte Carlo). <b>Não aconteceu</b> — é estimativa.','<span class="lbl">projetado · média</span>')}</div>`+
          `<div class="fdc-kpi__value" data-state="proj" style="${vS}">${fmtPL(-_mc.xmdd)}</div>`+
          `<div class="kpi-sub" style="${sbS}">projetado · média</div>`+
        `</div>`+
        `<div class="kpi" style="${kS}">`+
          `<div class="kpi-label"><span class="kpi-pipe"></span>DD Extremo ${_mkTipAnchor('DD Extremo','<span class="lbl">pior</span> DD simulado (p99)','Pior queda plausível (<b>1 em 100</b> cenários) — <b>não aconteceu</b>, é projeção de 10.000 reamostragens. Dimensiona a banca.','<span class="lbl">projetado · cauda · p99</span>')}</div>`+
          `<div class="fdc-kpi__value" data-state="proj" style="${vS}">${fmtPL(-_mc.p99)}</div>`+
          `<div class="kpi-sub" style="${sbS}">projetado · 1 em 100</div>`+
        `</div>`+
        `<div class="kpi" style="${kS}">`+
          `<div class="kpi-label"><span class="kpi-pipe"></span>Nível de Solidez ${_mkTipAnchor('Nível de Solidez','<span class="lbl">índice composto</span>','P-value, drawdown e consistência <b>num selo só</b>.','<span class="lbl">Escala</span> <span class="scale"><i></i><i></i><i></i><i class="on"></i><i class="on"></i></span> <span class="good">Baixa → Alta</span>')}</div>`+
          `<div class="fdc-risk-meter" style="margin-top:auto">`+
            `<span class="fdc-risk-meter__tag" style="color:${_solCor}">${_sol.faixa}</span>`+
            `<div class="fdc-risk-meter__track">`+
              `<span class="fdc-risk-meter__knob" style="--value:${(_sol.score*100).toFixed(1)}%"></span>`+
            `</div>`+
          `</div>`+
        `</div>`+
      `</div>`+
    `</div>`+
    `<div class="analise-popup-section">`+
      `<div class="analise-popup-section-title">Análise Mensal</div>`+
      `<div class="tbl-wrap drill-tbl"><table class="tbl" id="tipDrillTblMensal"><thead><tr>${mkTh('Mês','','l')+mkTh('Bets','','r')+mkTh('P/L','','r')+mkTh('Turnover','','r')+mkTh('ROI','','r')+mkTh('Win Rate','','r')+mkTh('Stake média','','r')+_mkOddMediaTh('r','88px')}</tr></thead><tbody>${_tipMonthTbody(rows)}</tbody></table></div>`+
    `</div>`+
    `<div class="analise-popup-section">`+
      `<div class="analise-popup-section-title">Distribuição de Odds <span style="font-size:9px;color:var(--ink-mute);text-transform:none;letter-spacing:0">(apostas, win rate e ROI por faixa)</span></div>`+
      `<div class="chart-wrap" style="height:240px;margin-top:.75rem"><canvas id="tipsterDrillOdds" role="img" aria-label="Distribuição de odds do tipster"></canvas></div>`+
    `</div>`+
    `<div class="analise-popup-section">`+
      `<div class="analise-popup-section-title">Por Casa</div>`+
      `<div class="tbl-wrap drill-tbl">${_tipBreakdownTbl(rows,'casa',casaCell,'tipDrillTblCasa')}</div>`+
    `</div>`+
    `<div class="analise-popup-section">`+
      `<div class="analise-popup-section-title">Por Esporte</div>`+
      `<div class="tbl-wrap drill-tbl">${_tipBreakdownTbl(rows,'esporte',sportCell,'tipDrillTblEsporte')}</div>`+
    `</div>`;

  // Gráfico Resultado Geral — clone do renderBankroll, scoped ao tipster
  const byDayCh={};rows.forEach(r=>{const k=r.data.slice(0,10);byDayCh[k]=(byDayCh[k]||0)+r.lucro;});
  const daysCh=Object.keys(byDayCh).sort();
  if(daysCh.length>=2){
    const dpL=daysCh.map(k=>byDayCh[k]);
    let cum=0;const cumPLCh=dpL.map(v=>{cum+=v;return parseFloat(cum.toFixed(2));});
    const labelStep=Math.max(1,Math.floor(daysCh.length/14));
    const lbl=daysCh.map((d,i)=>{if(i%labelStep!==0&&i!==daysCh.length-1)return'';const p=d.split('-');return p[2]+'/'+p[1];});
    const ptR=cumPLCh.map((_,i)=>i===cumPLCh.length-1?5:0);
    mkChart('tipsterDrillLine',{type:'bar',data:{labels:lbl,datasets:[
      {type:'line',data:cumPLCh,
       borderColor:'#2E8BFF',
       backgroundColor:(ctx)=>{const c=ctx.chart,{ctx:cx,chartArea:ca}=c;if(!ca)return'rgba(46,139,255,0)';const g=cx.createLinearGradient(0,ca.top,0,ca.bottom);g.addColorStop(0,'rgba(46,139,255,.16)');g.addColorStop(1,'rgba(46,139,255,0)');return g;},
       tension:.4,fill:true,borderWidth:2,
       pointRadius:ptR,pointBackgroundColor:'#2E8BFF',pointBorderColor:isDark()?'#12161D':'#ffffff',pointBorderWidth:2,
       yAxisID:'y1',label:'P/L acumulado'},
      {type:'bar',data:dpL,
       backgroundColor:dpL.map(v=>v>=0?'rgba(43,192,126,.55)':'rgba(229,82,75,.55)'),
       hoverBackgroundColor:dpL.map(v=>v>=0?'rgba(43,192,126,.8)':'rgba(229,82,75,.8)'),
       borderRadius:1,yAxisID:'y',label:'P/L diário',barPercentage:0.9,categoryPercentage:1.0}
    ]},options:{responsive:true,maintainAspectRatio:false,
      plugins:{
        legend:{display:false},
        tooltip:{callbacks:{label:ctx=>(ctx.dataset.label||'')+': '+fmtK(ctx.raw),title:ctx=>{const i=ctx[0].dataIndex;return daysCh[i]?.split('-').reverse().join('/')||'';},}}},
      scales:{
        x:{display:false},
        y:{ticks:{color:tc(),font:{size:10},callback:v=>fmtK(v)},grid:{color:gc()},border:{display:false},position:'left'},
        y1:{ticks:{color:tc(),font:{size:10},callback:v=>fmtK(v)},grid:{display:false},border:{display:false},position:'right'}
      }}});
  }

  // Distribuição de Odds — scoped ao tipster (mesmo gráfico da Visão Geral)
  renderOddsDist(rows,'tipsterDrillOdds');

  setTimeout(()=>{
    makeSortable('tipDrillTblMensal',[1,2,3,4,5,6,7]);
    makeSortable('tipDrillTblCasa',[1,2,3,4,5,6,7]);
    makeSortable('tipDrillTblEsporte',[1,2,3,4,5,6,7]);
  },0);
  renderGestaoTipster(nome);
}

function openTipsterDrill(nome){
  const overlay=document.getElementById('tipsterDrillOverlay');
  if(!overlay)return;
  const nameEl=document.getElementById('tipsterDrillName');
  if(nameEl)nameEl.textContent=nome;

  // Base: respeita esporte/casa mas ignora período global
  const sp=msGet('sp_tipsters'),ca=msGet('ca_tipsters');
  _drillBaseName=nome;
  _drillBaseRows=DADOS.filter(r=>{
    if(r.tipster!==nome)return false;
    if(sp.size>0&&!sp.has(r.esporte))return false;
    if(ca.size>0&&!ca.has(r.casa))return false;
    return true;
  });
  _drillPeriodSt=_seedDrillFromPage('tipsters');
  _drillInheritSt={..._drillPeriodSt};
  _updateDrillChips();

  overlay.style.display='flex';
  document.body.style.overflow='hidden';
  const modal=document.getElementById('tipsterDrillModal');
  if(modal)modal.scrollTop=0;

  renderTipsterDrill(_sliceDrillRows());

  if(_drillEscHandler)document.removeEventListener('keydown',_drillEscHandler);
  _drillEscHandler=function(e){if(e.key==='Escape')closeTipsterDrill();};
  document.addEventListener('keydown',_drillEscHandler);
}
window.openTipsterDrill=openTipsterDrill;

window.setDrillQuick=function(days){_drillPeriodSt={qd:days,qt:'',df:'',dt:''};_updateDrillChips();renderTipsterDrill(_sliceDrillRows());};
window.setDrillType=function(qt){_drillPeriodSt={qd:0,qt:qt,df:'',dt:''};_updateDrillChips();renderTipsterDrill(_sliceDrillRows());};
window.setDrillAll=function(){_drillPeriodSt={qd:0,qt:'',df:'',dt:''};_updateDrillChips();renderTipsterDrill(_sliceDrillRows());};
window.setDrillInherit=function(){if(!_drillInheritSt)return;_drillPeriodSt={..._drillInheritSt};_updateDrillChips();renderTipsterDrill(_sliceDrillRows());};

function closeTipsterDrill(e){
  if(e&&e.target!==document.getElementById('tipsterDrillOverlay'))return;
  const overlay=document.getElementById('tipsterDrillOverlay');
  if(overlay)overlay.style.display='none';
  document.body.style.overflow='';
  if(_drillEscHandler){document.removeEventListener('keydown',_drillEscHandler);_drillEscHandler=null;}
}
window.closeTipsterDrill=closeTipsterDrill;

// ── Gestão do tipster DENTRO do drill (Perfil de Tipster) — AGORA SÓ-LEITURA.
// A edição (info + escada de unidade) mora na aba "Tipster / Método" (Gestão). Aqui o
// extrato apenas EXIBE o que já foi configurado: Stake Atual (valor da unidade vigente),
// Última alteração (data desse degrau) e Custo (soma lançada na aba Custo de Tipsters).
async function renderGestaoTipster(nome){
  const box=document.getElementById('tipDrillGestao');
  if(!box)return;
  let segs=[];
  try{const r=await fetch('/tipsters/unidades?tipster='+encodeURIComponent(nome));const d=await r.json();segs=d.escada||[];}catch(e){}
  const hoje=(typeof _today==='function')?_today():new Date().toISOString().slice(0,10);
  // Stake Atual = valor da unidade vigente hoje (último degrau com vigente_desde <= hoje).
  const sorted=[...segs].sort((a,b)=>a.vigente_desde<b.vigente_desde?-1:1);
  let atual=null,desde=null;
  sorted.forEach(s=>{if(s.vigente_desde<=hoje){atual=s.valor;desde=s.vigente_desde;}});
  // Custo do tipster = soma lançada na aba "Custo de Tipsters" (mesmo store, ctData).
  if(typeof ctLoad==='function'){try{ctLoad();}catch(e){}}
  const ct=(typeof ctData!=='undefined'&&ctData[nome])?ctData[nome]:{};
  const custo=Object.values(ct).reduce((a,v)=>a+(parseFloat((v||'').toString().replace(',','.'))||0),0);
  const money2=v=>`<span class="money"><span class="money-sign">R$</span><span class="money-val">${(Number(v)||0).toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2})}</span></span>`;
  const fmtBR=iso=>{const m=/^(\d{4})-(\d{2})-(\d{2})$/.exec(iso||'');return m?m[3]+'/'+m[2]+'/'+m[1]:'—';};
  const kS='display:flex;flex-direction:column;min-width:0';
  const sbS='margin-top:auto;padding-top:6px';
  const vS='font-size:16px';
  const dash='<span style="color:var(--ink-mute)">—</span>';
  box.innerHTML=
    `<div class="analise-popup-section-title" style="display:flex;align-items:center;justify-content:space-between">Gestão do tipster<span style="font-family:JetBrains Mono,monospace;font-size:9px;text-transform:uppercase;letter-spacing:.18em;color:var(--ink-soft);opacity:.7">configure na aba Tipster / Método</span></div>`
    +`<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:.6rem">`
      +`<div class="kpi" style="${kS}"><div class="kpi-label"><span class="kpi-pipe"></span>Stake Atual</div><div class="kpi-val neu" style="${vS}">${atual!=null?money2(atual):dash}</div><div class="kpi-sub" style="${sbS}">valor de 1u vigente</div></div>`
      +`<div class="kpi" style="${kS}"><div class="kpi-label"><span class="kpi-pipe"></span>Última alteração</div><div class="kpi-val neu" style="${vS};font-family:var(--font-mono)">${fmtBR(desde)}</div><div class="kpi-sub" style="${sbS}">${desde?'da unidade':'sem escada definida'}</div></div>`
      +`<div class="kpi" style="${kS}"><div class="kpi-label"><span class="kpi-pipe"></span>Custo</div><div class="kpi-val neu" style="${vS}">${custo>0?fmtR(custo):dash}</div><div class="kpi-sub" style="${sbS}">aba Custo de Tipsters</div></div>`
    +`</div>`;
}
window.renderGestaoTipster=renderGestaoTipster;

// Renderiza emoji em canvas 24×24 e retorna data URL grayscale
async function _emojiToGrayDataUrl(emoji){
  const s=24,c=document.createElement('canvas');
  c.width=c.height=s;
  const cx=c.getContext('2d');
  cx.font=`${Math.round(s*0.72)}px serif`;
  cx.textAlign='center';cx.textBaseline='middle';
  cx.fillText(emoji,s/2,s/2);
  const id=cx.getImageData(0,0,s,s),d=id.data;
  for(let i=0;i<d.length;i+=4){const g=Math.round(0.299*d[i]+0.587*d[i+1]+0.114*d[i+2]);d[i]=d[i+1]=d[i+2]=g;}
  cx.putImageData(id,0,0);
  return c.toDataURL('image/png');
}

// Emoldura a captura crua do drill: fundo escuro da marca OPACO (mata os cantos
// brancos do html2canvas em QUALQUER fundo onde a imagem for colada) + contorno
// azul da marca arredondado com brilho suave. O fundo é um retângulo cheio (cantos
// externos retos) DE PROPÓSITO: canto arredondado exigiria transparência fora dele,
// que vira branco em fundo claro (WhatsApp/Windows) — foi o que o Feca reportou.
// Cor e raio saem dos TOKENS lidos em runtime (getComputedStyle) → segue dark/light
// e nunca desalinha da paleta. O fallback literal espelha o azul canônico (--fdc-blue).
function _frameExportCanvas(raw,modal){
  const cs=getComputedStyle(document.documentElement);
  const blue=(cs.getPropertyValue('--accent')||'#2E8BFF').trim();
  const bg=getComputedStyle(modal).backgroundColor||'#12161D';   // resolve var(--bg2)
  const S=raw.width/Math.max(1,modal.offsetWidth);               // escala do html2canvas (~2)
  const modalR=(parseFloat(getComputedStyle(modal).borderRadius)||12)*S;
  const pad=Math.round(24*S);                     // respiro entre o card e a borda da imagem
  const bw=Math.max(2,Math.round(2.5*S));         // espessura do contorno azul
  const gap=Math.round(7*S);                      // folga entre o card e o contorno
  const W=raw.width+pad*2, H=raw.height+pad*2;
  const out=document.createElement('canvas');
  out.width=W; out.height=H;
  const ctx=out.getContext('2d');
  // Path de retângulo arredondado (sem depender de ctx.roundRect, ausente em navegadores antigos)
  const rr=(x,y,w,h,r)=>{r=Math.min(r,w/2,h/2);ctx.beginPath();ctx.moveTo(x+r,y);ctx.arcTo(x+w,y,x+w,y+h,r);ctx.arcTo(x+w,y+h,x,y+h,r);ctx.arcTo(x,y+h,x,y,r);ctx.arcTo(x,y,x+w,y,r);ctx.closePath();};
  // 1) fundo escuro da marca preenchendo TODO o retângulo (opaco) — nenhum canto
  //    fica transparente, então nunca aparece branco, em nenhum fundo
  ctx.fillStyle=bg; ctx.fillRect(0,0,W,H);
  // 2) a captura, recortada exatamente nos cantos do modal
  ctx.save(); rr(pad,pad,raw.width,raw.height,modalR); ctx.clip(); ctx.drawImage(raw,pad,pad); ctx.restore();
  // 3) contorno azul da marca abraçando o card, com brilho suave
  const fx=pad-gap, fy=pad-gap, fw=raw.width+gap*2, fh=raw.height+gap*2, rF=modalR+gap;
  ctx.save();
  ctx.shadowColor=blue; ctx.shadowBlur=Math.round(18*S);
  ctx.strokeStyle=blue; ctx.lineWidth=bw;
  rr(fx+bw/2,fy+bw/2,fw-bw,fh-bw,rF); ctx.stroke();
  ctx.restore();
  ctx.strokeStyle=blue; ctx.lineWidth=bw;         // passada nítida por cima do brilho
  rr(fx+bw/2,fy+bw/2,fw-bw,fh-bw,rF); ctx.stroke();
  return out;
}

// Prepara o modal para captura com html2canvas; retorna {canvas} ou {canvas:null} em erro
async function _buildDrillCanvas(modal){
  const logoEl=modal.querySelector('.drill-brand-logo');
  let origLogoSrc=null;
  if(logoEl){
    origLogoSrc=logoEl.getAttribute('src');
    try{const r=await fetch(origLogoSrc);const svg=await r.text();logoEl.src='data:image/svg+xml;base64,'+btoa(unescape(encodeURIComponent(svg)));}catch(e){}
  }
  // Casas: converte favicons para blob URLs same-origin (html2canvas não lê cross-origin sem CORS)
  const houseChips=[...modal.querySelectorAll('.house-chip')];
  const _houseRestoreData=[];
  for(const span of houseChips){
    const img=span.querySelector('img');
    const casaNome=span.dataset.casa||(img?.getAttribute('alt')||'');
    const origSrc=img?img.getAttribute('src'):(casaNome&&_houseDomain(casaNome)?favicon(_houseDomain(casaNome)):'');
    let blobUrl=null;
    if(origSrc){try{const r=await fetch(origSrc,{mode:'no-cors'});const blob=await r.blob();if(blob.size>0)blobUrl=URL.createObjectURL(blob);}catch(e){}}
    if(blobUrl){
      if(img){img.src=blobUrl;_houseRestoreData.push({img,origSrc,blobUrl,tempImg:false,initEl:null,restoredChipInit:null});}
      else{const chipInit=span.querySelector('.chip-initial');if(chipInit)chipInit.style.display='none';const newImg=document.createElement('img');newImg.style.cssText='width:18px;height:18px;border-radius:3px;display:block';newImg.src=blobUrl;span.insertBefore(newImg,span.firstChild);_houseRestoreData.push({img:newImg,origSrc:null,blobUrl,tempImg:true,initEl:null,restoredChipInit:chipInit||null});}
    }else if(img){
      img.style.display='none';
      const init=span.dataset.initial||(img.getAttribute('alt')?.[0]?.toUpperCase()??'?');
      const initEl=Object.assign(document.createElement('span'),{textContent:init,className:'chip-initial'});
      span.appendChild(initEl);
      _houseRestoreData.push({img,origSrc,blobUrl:null,tempImg:false,initEl,restoredChipInit:null});
    }else{_houseRestoreData.push({img:null,origSrc:null,blobUrl:null,tempImg:false,initEl:null,restoredChipInit:null});}
  }
  // Esportes: html2canvas não suporta CSS filter em emoji — converte via canvas grayscale
  const spChips=[...modal.querySelectorAll('.sp-chip')];
  const _spRestoreData=[];
  for(const el of spChips){
    const emoji=el.textContent.trim();
    const dataUrl=await _emojiToGrayDataUrl(emoji);
    const origHTML=el.innerHTML;
    const origStyle=el.getAttribute('style');
    const img=Object.assign(document.createElement('img'),{src:dataUrl});
    img.style.cssText='width:14px;height:14px;display:block';
    el.innerHTML='';el.appendChild(img);
    el.style.removeProperty('filter');
    _spRestoreData.push({el,origHTML,origStyle});
  }
  const prevMaxH=modal.style.maxHeight;modal.style.maxHeight='none';
  const prevOv=modal.style.overflowY;modal.style.overflowY='visible';
  const _restore=()=>{
    modal.style.maxHeight=prevMaxH;modal.style.overflowY=prevOv;
    if(logoEl&&origLogoSrc)logoEl.src=origLogoSrc;
    _houseRestoreData.forEach(({img,origSrc,blobUrl,tempImg,initEl,restoredChipInit})=>{if(tempImg&&img)img.remove();if(restoredChipInit)restoredChipInit.style.display='';if(!tempImg&&img&&origSrc)img.src=origSrc;if(!tempImg&&img)img.style.display='';if(initEl)initEl.remove();if(blobUrl)URL.revokeObjectURL(blobUrl);});
    _spRestoreData.forEach(({el,origHTML,origStyle})=>{el.innerHTML=origHTML;if(origStyle!==null)el.setAttribute('style',origStyle);else el.removeAttribute('style');});
  };
  try{
    // Captura com fundo TRANSPARENTE (backgroundColor:null): o padrão do html2canvas
    // é branco e vazava nos cantos arredondados do modal (os "cantinhos brancos").
    // A moldura da marca é composta depois, em _frameExportCanvas.
    const raw=await html2canvas(modal,{scale:2,useCORS:true,backgroundColor:null,
      ignoreElements:el=>el.classList&&el.classList.contains('no-export')});
    _restore();
    return{canvas:_frameExportCanvas(raw,modal)};
  }catch(e){
    _restore();
    console.error('_buildDrillCanvas error:',e);
    return{canvas:null};
  }
}

function _waitH2C(ms=8000){
  if(typeof html2canvas!=='undefined')return Promise.resolve(true);
  return new Promise(r=>{const t=Date.now();const c=()=>{if(typeof html2canvas!=='undefined')r(true);else if(Date.now()-t<ms)setTimeout(c,150);else r(false);};setTimeout(c,150);});
}

window.copyDrill=async function(){
  const modal=document.getElementById('tipsterDrillModal');
  if(!modal)return;
  const btn=modal.querySelector('.copy-drill-btn');
  const btnOrig=btn?btn.innerHTML:null;
  if(btn){btn.disabled=true;btn.innerHTML='…';}
  const ok=await _waitH2C();
  if(!ok){if(btn){btn.disabled=false;btn.innerHTML=btnOrig;}return;}
  const{canvas}=await _buildDrillCanvas(modal);
  if(!canvas){if(btn){btn.disabled=false;btn.innerHTML=btnOrig;}return;}
  canvas.toBlob(async blob=>{
    try{
      await navigator.clipboard.write([new ClipboardItem({'image/png':blob})]);
      if(btn){btn.innerHTML='✓';setTimeout(()=>{btn.disabled=false;btn.innerHTML=btnOrig;},2000);}
    }catch(e){
      if(btn){btn.innerHTML='✗';setTimeout(()=>{btn.disabled=false;btn.innerHTML=btnOrig;},1500);}
      console.error('copyDrill clipboard error:',e);
    }
  },'image/png');
};

window.saveDrill=async function(){
  const modal=document.getElementById('tipsterDrillModal');
  if(!modal)return;
  const btn=modal.querySelector('.save-drill-btn');
  const btnOrig=btn?btn.innerHTML:null;
  if(btn){btn.disabled=true;btn.innerHTML='…';}
  const ok=await _waitH2C();
  if(!ok){if(btn){btn.disabled=false;btn.innerHTML=btnOrig;}return;}
  const{canvas}=await _buildDrillCanvas(modal);
  if(!canvas){if(btn){btn.disabled=false;btn.innerHTML=btnOrig;}return;}
  canvas.toBlob(blob=>{
    const url=URL.createObjectURL(blob);
    const a=Object.assign(document.createElement('a'),{href:url,download:'tipster-'+((_drillBaseName||'drill').replace(/\s+/g,'_'))+'.png'});
    a.click();
    setTimeout(()=>URL.revokeObjectURL(url),5000);
    if(btn){btn.innerHTML='✓';setTimeout(()=>{btn.disabled=false;btn.innerHTML=btnOrig;},2000);}
  },'image/png');
};

// ── Helpers extraídos para reuso no popup ───────────────────────────────────
function _tipMonthTbody(rows){
  const byM={};
  rows.forEach(r=>{const d=new Date(r.data+'T12:00:00'),k=`${d.getFullYear()}-${String(d.getMonth()).padStart(2,'0')}`;if(!byM[k])byM[k]={bets:0,pl:0,s:0,w:0,t:0,hw:0,hl:0,wt:0,stk:0,ano:d.getFullYear(),mes:d.getMonth()};byM[k].bets++;byM[k].pl+=r.lucro;if(r.resultado!=='V')byM[k].s+=r.stake;bumpWR(byM[k],r.resultado);if(r.odd>0&&r.stake>0){byM[k].wt+=r.odd*r.stake;byM[k].stk+=r.stake;}});
  let totPL=0,totS=0,totB=0,totW=0,totT=0,totHW=0,totHL=0;
  const mHTML=Object.keys(byM).sort().map(k=>{
    const v=byM[k];const roi=v.s>0?(v.pl/v.s*100):0,wr=wrFrac(v.w,v.hw,v.hl,v.t);
    const avgOdd=v.stk>0?v.wt/v.stk:0,avgStake=v.t>0?v.s/v.t:0;
    totPL+=v.pl;totS+=v.s;totB+=v.bets;totW+=v.w;totT+=v.t;totHW+=v.hw;totHL+=v.hl;
    const pc=v.pl>=0?'color:var(--pos)':'color:var(--neg)';
    const rc=roi>=0?'color:var(--pos)':'color:var(--neg)';
    return`<tr><td data-sort="${k}" style="white-space:nowrap">${MESES[v.mes]} ${v.ano}</td><td class="td-num">${v.bets.toLocaleString('pt-BR')}</td><td class="td-num" style="${pc}">${fmtPL(v.pl)}</td><td class="td-num">${fmtR(v.s)}</td><td class="td-num" style="${rc}">${fmtPct(roi,2)}</td><td class="td-num">${mkWRC(wr)}</td><td class="td-num">${fmtR(avgStake)}</td><td class="td-num">${fmtOdd(avgOdd)}</td></tr>`;
  }).join('');
  const tRoi=totS>0?(totPL/totS*100):0,tWr=wrFrac(totW,totHW,totHL,totT);
  const tc2=totPL>=0?'color:var(--pos)':'color:var(--neg)';const rc2=tRoi>=0?'color:var(--pos)':'color:var(--neg)';
  return mHTML+`<tr class="total-row"><td>Total</td><td class="td-num">${totB.toLocaleString('pt-BR')}</td><td class="td-num" style="${tc2}">${fmtPL(totPL)}</td><td class="td-num">${fmtR(totS)}</td><td class="td-num" style="${rc2}">${fmtPct(tRoi,2)}</td><td class="td-num">${mkWRC(tWr)}</td><td class="td-num">${totT>0?fmtR(totS/totT):'—'}</td><td class="td-num">—</td></tr>`;
}

function _tipBreakdownTbl(rows,dimKey,labelFn,tableId=''){
  const map={};
  rows.forEach(r=>{
    const k=r[dimKey];if(!k)return;
    if(!map[k])map[k]={l:0,s:0,n:0,w:0,t:0,hw:0,hl:0,wt:0,stk:0};
    map[k].l+=r.lucro;if(r.resultado!=='V')map[k].s+=r.stake;map[k].n++;
    bumpWR(map[k],r.resultado);
    if(r.odd>0&&r.stake>0){map[k].wt+=r.odd*r.stake;map[k].stk+=r.stake;}
  });
  const ents=Object.entries(map).sort((a,b)=>b[1].l-a[1].l);
  if(!ents.length)return mkEmpty('Sem dados no período');
  const tRows=ents.map(([k,d])=>{
    const roi=d.s>0?(d.l/d.s*100):0,wr=wrFrac(d.w,d.hw,d.hl,d.t);
    const avgOdd=d.stk>0?d.wt/d.stk:0;
    const avgStake=d.t>0?d.s/d.t:0;
    const lc=d.l>=0?'color:var(--pos)':'color:var(--neg)';
    const rc=roi>=0?'color:var(--pos)':'color:var(--neg)';
    return`<tr><td>${labelFn(k)}</td><td class="td-num">${d.n.toLocaleString('pt-BR')}</td><td class="td-num" style="${lc}">${fmtPL(d.l)}</td><td class="td-num">${fmtR(d.s)}</td><td class="td-num" style="${rc}">${fmtPct(roi,2)}</td><td class="td-num">${mkWRC(wr)}</td><td class="td-num">${fmtR(avgStake)}</td><td class="td-num">${fmtOdd(avgOdd)}</td></tr>`;
  }).join('');
  const th=dimKey==='casa'?'Casa':'Esporte';
  const idAttr=tableId?` id="${tableId}"`:'';
  const oddTh=_mkOddMediaTh('r','88px');
  return`<table class="tbl"${idAttr}><thead><tr>${mkTh(th,'','l')+mkTh('Bets','','r')+mkTh('P/L','','r')+mkTh('Turnover','','r')+mkTh('ROI','','r')+mkTh('Win Rate','','r')+mkTh('Stake média','','r')+oddTh}</tr></thead><tbody>${tRows}</tbody></table>`;
}

// Tipsters
function renderTipsters(){
  const selT=msGet('tipsters');
  const baseRows=filtrarPagina('tipsters');
  const allT=[...new Set(DADOS.map(r=>r.tipster).filter(Boolean))].sort();
  const activeT=selT.size>0?[...selT]:allT;
  // Switch R$⇄u (Perfil de Tipster): reflete o estado no seg e, se em "u", garante as
  // escadas em cache (busca uma vez). O u é computado sobre as linhas JÁ FILTRADAS.
  const _seg=document.getElementById('tipUnitSeg');
  if(_seg)_seg.querySelectorAll('button').forEach(b=>b.classList.toggle('active',b.dataset.u===_tipUnit));
  if(_tipUnit==='u'&&_tipEscadas===null){
    _tipEscadas={};   // trava anti-refetch concorrente; sobrescrito quando o fetch chega
    fetch('/tipsters/escadas').then(r=>r.json()).then(d=>{_tipEscadas=d.escadas||{};renderTipsters();}).catch(()=>{_tipEscadas={};});
  }
  const emU=_tipUnit==='u';
  const uMap=emU?_tipsterUnidades(baseRows.filter(r=>activeT.includes(r.tipster)),_tipEscadas||{}):null;
  // Tipster KPI cards — .tcard design (T-1)
  {
    const tipMap={},tipDays={};
    baseRows.filter(r=>activeT.includes(r.tipster)).forEach(r=>{
      if(!tipMap[r.tipster])tipMap[r.tipster]={l:0,s:0,n:0,w:0,t:0,hw:0,hl:0,wt:0,stk:0};
      tipMap[r.tipster].l+=r.lucro;if(r.resultado!=='V')tipMap[r.tipster].s+=r.stake;tipMap[r.tipster].n++;
      bumpWR(tipMap[r.tipster],r.resultado);
      if(r.odd>0&&r.stake>0){tipMap[r.tipster].wt+=r.odd*r.stake;tipMap[r.tipster].stk+=r.stake;}
      const dk=r.data.slice(0,10);
      if(!tipDays[r.tipster])tipDays[r.tipster]={};
      tipDays[r.tipster][dk]=(tipDays[r.tipster][dk]||0)+r.lucro;
    });
    _tipsterEnts=Object.entries(tipMap);
    _tipsterDays=tipDays;
    _tipsterAllDays=[...new Set(baseRows.map(r=>r.data.slice(0,10)))].sort();
    // T-5: Portfolio KPIs
    {
      const kpiRows=baseRows.filter(r=>activeT.includes(r.tipster));
      const portPL=kpiRows.reduce((a,r)=>a+r.lucro,0);
      const portROI=calcROI(kpiRows);
      const portStake=calcTurnover(kpiRows);   // turnover exclui Void
      const portN=kpiRows.length;
      const posCount=_tipsterEnts.filter(([,d])=>d.l>0).length;
      const negCount=_tipsterEnts.filter(([,d])=>d.l<0).length;
      const totalT=_tipsterEnts.length;
      const portU=emU?activeT.reduce((a,t)=>a+((uMap&&uMap[t])||0),0):0;
      const plCls=(emU?portU:portPL)>=0?'pos':'neg';
      const roiCls=portROI>=0?'pos':'neg';
      const roiStr=fmtPct(portROI,2);
      const el=document.getElementById('tipsterPortfolioKPIs');
      if(el){
        el.innerHTML=
          `<div class="kpi">`+
            `<div class="kpi-label"><span class="kpi-pipe"></span> P/L Carteira</div>`+
            `<div class="kpi-val ${plCls}">${emU?fmtU(portU):fmtPL(portPL)}</div>`+
            `<div class="kpi-sub">${emU?'em unidades · escada por tipster':'resultado do conjunto'}</div>`+
          `</div>`+
          `<div class="kpi">`+
            `<div class="kpi-label"><span class="kpi-pipe"></span> ROI</div>`+
            `<div class="kpi-val ${roiCls}">${roiStr}</div>`+
            `<div class="kpi-sub">Σ(P/L) / Σ(turnover)</div>`+
          `</div>`+
          `<div class="kpi">`+
            `<div class="kpi-label"><span class="kpi-pipe"></span> Tipsters Positivos</div>`+
            `<div class="kpi-val neu">${posCount} / ${totalT}</div>`+
            `<div class="kpi-sub">▲ ${posCount} · ▼ ${negCount} no vermelho</div>`+
          `</div>`+
          `<div class="kpi">`+
            `<div class="kpi-label"><span class="kpi-pipe"></span> Turnover Total</div>`+
            `<div class="kpi-val neu">${fmtR(portStake)}</div>`+
            `<div class="kpi-sub">${portN.toLocaleString('pt-BR')} apostas</div>`+
          `</div>`;
      }
    }
    _renderTipCards();
  }

  // Comparativo Geral
  const map={};
  baseRows.filter(r=>activeT.includes(r.tipster)).forEach(r=>{if(!map[r.tipster])map[r.tipster]={l:0,s:0,n:0,w:0,t:0,hw:0,hl:0,wt:0,stk:0};map[r.tipster].l+=r.lucro;if(r.resultado!=='V')map[r.tipster].s+=r.stake;map[r.tipster].n++;bumpWR(map[r.tipster],r.resultado);if(r.odd>0&&r.stake>0){map[r.tipster].wt+=r.odd*r.stake;map[r.tipster].stk+=r.stake;}});
  const ents=Object.entries(map).sort((a,b)=>b[1].l-a[1].l);
  const compRows=ents.map(([t,d])=>{
    const roi=d.s>0?(d.l/d.s*100):0,wr=wrFrac(d.w,d.hw,d.hl,d.t);
    const avgOdd=d.stk>0?d.wt/d.stk:0,avgStake=d.t>0?d.s/d.t:0;
    const plVal=emU?((uMap&&uMap[t])||0):d.l;
    const lc=plVal>=0?'color:var(--pos)':'color:var(--neg)';
    const rc=roi>=0?'color:var(--pos)':'color:var(--neg)';
    return`<tr><td style="font-weight:700;color:var(--ink)">${esc(t)}</td><td>${d.n}</td><td class="td-num">${mkWRC(wr)}</td><td>${fmtR(d.s)}</td><td style="${lc}">${emU?fmtU(plVal):fmtPL(d.l)}</td><td style="${rc}">${fmtPct(roi,2)}</td><td>${fmtOdd(avgOdd)}</td><td>${fmtR(avgStake)}</td></tr>`;
  }).join('');
  document.getElementById('tipsterCompTable').innerHTML=`<table class="tbl" id="tblTipComp"><thead><tr>${mkTh('Tipster','','l')+mkTh('Bets','','r')+mkTh('Win Rate','','r')+mkTh('Turnover','','r')+mkTh('P/L','','r')+mkTh('ROI','','r')+_mkOddMediaTh('r')+mkTh('Stake média','','r')}</tr></thead><tbody>${compRows}</tbody></table>`;
  setTimeout(()=>makeSortable('tblTipComp',[1,3,4,5,6,7]),100);
}

// ── Resultados por Casa: removido (consolidado na aba "Resultados") ──
// A análise por casa vive na aba Bookies (cards .tcard + drill-down completo).
