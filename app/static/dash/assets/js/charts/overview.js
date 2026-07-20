// ── overview.js — Gráficos e cards da Visão Geral ──────────────────────────────

function renderKPI(rows){
  const lucro=rows.reduce((a,r)=>a+r.lucro,0),stake=calcTurnover(rows);
  const roi=calcROI(rows),n=rows.length;
  const W=rows.filter(r=>r.resultado==='W').length;
  const L=rows.filter(r=>r.resultado==='L').length;
  const HW=rows.filter(r=>r.resultado==='HW').length;
  const HL=rows.filter(r=>r.resultado==='HL').length;
  const V=rows.filter(r=>r.resultado==='V').length;
  const settled=rows.filter(r=>r.resultado!=='V').length;
  const wins=W+HW;
  const wr=wrFrac(wins,HW,HL,settled);
  const{costConta}=calcCostFiltered(rows);
  // Custo de tipster — soma SÓ os meses dentro do período filtrado (assinatura é mensal;
  // espelha o custo de conta, que já respeita a data via calcCostFiltered). Mês "YYYY-MM"
  // entra se estiver no intervalo [menor, maior] mês das apostas filtradas. Sem filtro (tudo),
  // o span cobre todos os meses → mesmo número de antes; só as visões filtradas mudam (fim
  // do double-count: filtrar "julho" descontava jan..jul do custo). Ver achado Turbo overview.js.
  ctLoad();
  const _ymMin=rows.length?rows.reduce((m,r)=>r.data<m?r.data:m,'9999-99-99').slice(0,7):null;
  const _ymMax=rows.length?rows.reduce((m,r)=>r.data>m?r.data:m,'0000-00-00').slice(0,7):null;
  const costTipster=!_ymMin?0:Object.values(ctData).reduce((total,monthsObj)=>{
    return total+Object.entries(monthsObj||{}).reduce((a,[m,v])=>{
      if(m<_ymMin||m>_ymMax)return a;   // mês fora do período filtrado → não conta
      return a+(parseFloat((v||'').toString().replace(',','.'))||0);
    },0);
  },0);
  const totalCost=costConta+costTipster;
  const lucroLiq=lucro-totalCost;

  // ── Andar 1: P/L Bruto → Custo Conta → Custo Tipster → P/L Líquido ────────
  const row1=[
    {l:'P/L Bruto',v:fmtPL(lucro),c:lucro>=0?'pos':'neg',s:'antes de custos',accent:''},
    {l:'Custo de Contas',v:costConta>0?fmtPL(-costConta):fmtR(0),c:costConta>0?'neg':'neu',s:'total aquisição',accent:''},
    {l:'Custo de Tipsters',v:costTipster>0?fmtPL(-costTipster):fmtR(0),c:costTipster>0?'neg':'neu',s:'assinaturas / serviços',accent:''},
    {l:'P/L Líquido',v:fmtPL(lucroLiq),c:lucroLiq>=0?'pos':'neg',s:'resultado final',accent:'hero'},
  ];
  // ── Andar 2: Turnover → ROI → Odd Média → Win Rate ──────────────────────
  const row2=[
    {l:'Turnover',v:fmtR(stake),c:'neu',s:'volume apostado'},
    {l:'ROI',v:fmtPct(roi,2),c:roi>=0?'pos':'neg',s:n+' apostas'},
    {l:'Odd Média',v:fmtOdd(calcAvgOdd(rows)),c:'neu',s:'ponderada'},
    {l:'Win Rate',v:fmtPct(wr,1,false),c:'neu',s:settled+' encerradas',bar:wr},
  ];
  const divider=`<div style="grid-column:1/-1;height:1px;background:var(--line-2);margin:2px 0;opacity:.6"></div>`;
  document.getElementById('kpiGrid').innerHTML=
    `<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;align-items:stretch;margin-bottom:1.25rem">`+
    row1.map(k=>`<div class="kpi ${k.accent||''}"><div class="kpi-label"><span class="kpi-pipe"></span> ${k.l}</div><div class="kpi-val ${k.c}">${k.v}</div><div class="kpi-sub">${k.s}</div></div>`).join('')+
    row2.map(k=>`<div class="kpi"><div class="kpi-label"><span class="kpi-pipe"></span> ${k.l}</div><div class="kpi-val ${k.c}">${k.v}</div>${k.bar!==undefined?`<div class="wrc"><div class="t"><div class="f" style="width:${Math.min(100,Math.max(0,k.bar)).toFixed(1)}%"></div></div></div>`:''}<div class="kpi-sub">${k.s}</div></div>`).join('')+
    `</div>`;
}

function renderBankroll(rows){
  const byDay={};rows.forEach(r=>{const k=r.data.slice(0,10);if(!byDay[k])byDay[k]=0;byDay[k]+=r.lucro;});
  const days=Object.keys(byDay).sort();
  const dpL=days.map(k=>byDay[k]);
  let cum=0;const cumPL=dpL.map(v=>{cum+=v;return parseFloat(cum.toFixed(2));});
  // Labels every ~30 days to avoid clutter, shown vertically
  const labelStep=Math.max(1,Math.floor(days.length/14));
  const lbl=days.map((d,i)=>{
    if(i%labelStep!==0&&i!==days.length-1)return'';
    const p=d.split('-');return p[2]+'/'+p[1];
  });
  const ptR=cumPL.map((_,i)=>i===cumPL.length-1?5:0);
  mkChart('chartBankroll',{type:'bar',data:{labels:lbl,datasets:[
    {type:'line',data:cumPL,
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
      tooltip:{callbacks:{label:ctx=>(ctx.dataset.label||'')+': '+fmtK(ctx.raw),title:ctx=>{const i=ctx[0].dataIndex;return days[i]?.split('-').reverse().join('/')||'';},}}},
    scales:{
      x:{display:false},
      y:{ticks:{color:tc(),font:{size:10},callback:v=>fmtK(v)},grid:{color:gc()},border:{display:false},position:'left'},
      y1:{ticks:{color:tc(),font:{size:10},callback:v=>fmtK(v)},grid:{display:false},border:{display:false},position:'right'}
    }}});
}

function renderROIMonthly(rows,refKey){
  const byM={};rows.forEach(r=>{const d=new Date(r.data+'T12:00:00');const k=`${d.getFullYear()}-${String(d.getMonth()).padStart(2,'0')}`;if(!byM[k])byM[k]={pl:0,s:0,mes:d.getMonth(),ano:d.getFullYear()};byM[k].pl+=r.lucro;if(r.resultado!=='V')byM[k].s+=r.stake;});
  const mks=Object.keys(byM).sort();
  const lbl=mks.map(k=>{const v=byM[k];return MESES_CURTOS[v.mes]+' '+String(v.ano).slice(2);});
  const vals=mks.map(k=>byM[k].s>0?parseFloat((byM[k].pl/byM[k].s*100).toFixed(2)):0);
  const refIdx=refKey?mks.indexOf(refKey):-1;   // mês de referência do período → brilho azul
  const accent=(getComputedStyle(document.documentElement).getPropertyValue('--accent')||'#2E8BFF').trim();
  function roiColor(v){
    if(v<=-10)return'rgba(180,20,40,.9)';
    if(v<-3)return'rgba(240,80,110,.75)';
    if(v<0)return'rgba(240,80,110,.45)';
    if(v<3)return'rgba(0,214,143,.4)';
    if(v<8)return'rgba(0,214,143,.65)';
    return'rgba(0,214,143,.9)';
  }
  // Use afterDraw plugin to draw labels directly on bars
  const roiLabelPlugin={id:'roiLabels',afterDatasetsDraw(chart){
    const{ctx,data,scales:{x,y}}=chart;
    ctx.save();
    data.datasets[0].data.forEach((val,i)=>{
      const bar=chart.getDatasetMeta(0).data[i];
      if(!bar)return;
      ctx.font='bold 10px JetBrains Mono, monospace';
      ctx.fillStyle=isDark()?'rgba(255,255,255,.85)':'rgba(0,0,0,.75)';
      ctx.textAlign='center';
      ctx.textBaseline=val>=0?'bottom':'top';
      const yPos=val>=0?bar.y-3:bar.y+3;
      ctx.fillText(fmtPct(val,2),bar.x,yPos);
    });
    ctx.restore();
  }};
  // Brilho azul no mês de referência: contorno + glow (shadowBlur), mantendo a cor de ROI da barra
  const refGlowPlugin={id:'roiRefGlow',afterDatasetsDraw(chart){
    if(refIdx<0)return;
    const el=chart.getDatasetMeta(0).data[refIdx];if(!el)return;
    const pr=el.getProps(['x','y','base','width'],true);
    const w=pr.width,left=pr.x-w/2,top=Math.min(pr.y,pr.base),h=Math.max(2,Math.abs(pr.base-pr.y)),r=3;
    const{ctx}=chart;ctx.save();
    ctx.shadowColor=accent;ctx.shadowBlur=14;ctx.strokeStyle=accent;ctx.lineWidth=2;
    ctx.beginPath();
    ctx.moveTo(left+r,top);
    ctx.arcTo(left+w,top,left+w,top+h,r);
    ctx.arcTo(left+w,top+h,left,top+h,r);
    ctx.arcTo(left,top+h,left,top,r);
    ctx.arcTo(left,top,left+w,top,r);
    ctx.closePath();ctx.stroke();ctx.restore();
  }};
  const bBorder=vals.map((v,i)=>i===refIdx?accent:'transparent');
  const bWidth=vals.map((v,i)=>i===refIdx?1.5:0);
  mkChart('chartROI',{type:'bar',data:{labels:lbl,datasets:[{data:vals,backgroundColor:vals.map(roiColor),borderColor:bBorder,borderWidth:bWidth,borderRadius:3,label:'ROI%'}]},options:{responsive:true,maintainAspectRatio:false,layout:{padding:{top:18,bottom:4}},plugins:{legend:{display:false},tooltip:{callbacks:{label:ctx=>fmtPct(ctx.raw,2)}}},scales:{x:{ticks:{color:tc(),font:{size:10},maxRotation:30},grid:{display:false},border:{display:false}},y:{ticks:{color:tc(),font:{size:10},callback:v=>fmtPct(v,1,v<0)},grid:{color:gc()},border:{display:false}}}},plugins:[refGlowPlugin,roiLabelPlugin]});
}

function renderOddsDist(rows,canvasId='chartOddsDist'){
  const bins=[1,1.5,2.0,2.5,3.0,4.0,6.0,10.0,30.0,100.0,Infinity];
  const lbls=['1.0–1.5','1.5–2.0','2.0–2.5','2.5–3.0','3.0–4.0','4.0–6.0','6.0–10','10–30','30–100','100+'];
  const bdata=lbls.map(()=>({n:0,w:0,hw:0,hl:0,pl:0,s:0}));
  rows.filter(r=>r.resultado!=='V').forEach(r=>{
    for(let i=0;i<bins.length-1;i++){
      if(r.odd>=bins[i]&&r.odd<bins[i+1]){bdata[i].n++;bdata[i].pl+=r.lucro;bdata[i].s+=r.stake;if(r.resultado==='W')bdata[i].w++;else if(r.resultado==='HW'){bdata[i].w++;bdata[i].hw++;}else if(r.resultado==='HL')bdata[i].hl++;break;}
    }
  });
  const counts=bdata.map(b=>b.n);
  const wrs=bdata.map(b=>b.n>0?parseFloat(wrFrac(b.w,b.hw,b.hl,b.n).toFixed(1)):null);
  const rois=bdata.map(b=>b.s>0?parseFloat((b.pl/b.s*100).toFixed(2)):null);
  mkChart(canvasId,{type:'bar',data:{labels:lbls,datasets:[
    {type:'bar',data:counts,backgroundColor:'rgba(46,139,255,.55)',borderRadius:3,label:'Apostas',yAxisID:'y'},
    {type:'line',data:wrs,borderColor:'#2BC07E',backgroundColor:'transparent',tension:.3,pointRadius:5,pointBackgroundColor:'#2BC07E',borderWidth:2,label:'Win Rate %',yAxisID:'y1',spanGaps:false},
    {type:'line',data:rois,borderColor:'#E0A21A',backgroundColor:'transparent',tension:.3,pointRadius:5,pointBackgroundColor:'#E0A21A',borderWidth:2,label:'ROI %',yAxisID:'y2',borderDash:[4,3],spanGaps:false}
  ]},options:{responsive:true,maintainAspectRatio:false,interaction:{mode:'index',intersect:false},
    plugins:{legend:{display:true,position:'top',labels:{color:tc(),font:{size:11},boxWidth:12,padding:16}},
      tooltip:{callbacks:{label:ctx=>{if(ctx.datasetIndex===0)return'Apostas: '+ctx.raw;if(ctx.datasetIndex===1)return'Win Rate: '+(ctx.raw!=null?fmtPct(ctx.raw,1,false):'—');return'ROI: '+(ctx.raw!=null?fmtPct(ctx.raw,2):'—');}}}},
    scales:{
      x:{ticks:{color:tc(),font:{size:10}},grid:{display:false},border:{display:false}},
      y:{ticks:{color:tc(),font:{size:10}},grid:{color:gc()},border:{display:false},position:'left'},
      y1:{min:0,max:100,ticks:{color:'#2BC07E',font:{size:10},callback:v=>v+'%'},grid:{display:false},border:{display:false},position:'right'},
      y2:{ticks:{color:'#E0A21A',font:{size:10},callback:v=>v+'%'},grid:{display:false},border:{display:false},position:'right',offset:true}
    }}});
}

function renderHeatmap(rows){
  const byM={};rows.forEach(r=>{const d=new Date(r.data+'T12:00:00');const k=d.getFullYear()+'-'+d.getMonth();if(!byM[k])byM[k]={l:0,s:0,mes:d.getMonth(),ano:d.getFullYear()};byM[k].l+=r.lucro;if(r.resultado!=='V')byM[k].s+=r.stake;});
  const anos=[...new Set(Object.values(byM).map(v=>v.ano))].sort();
  const vals=Object.values(byM).map(v=>v.l);
  const maxAbs=Math.max(...vals.map(Math.abs),1);
  // Same color logic as daily heatmap
  function heatBg(v){const a=0.12+Math.min(1,Math.abs(v)/maxAbs)*0.82;return v>0?`rgba(0,160,100,${a})`:v<0?`rgba(200,40,60,${a})`:'transparent';}
  function heatTxt(v){
    if(v===0)return'var(--ink-mute)';
    const a=0.12+Math.min(1,Math.abs(v)/maxAbs)*0.82;
    return a>0.5?(v>0?'#d0fff0':'#ffe0e5'):(v>0?'var(--pos)':'var(--neg)');
  }
  let html=`<table class="heatmap-table"><thead><tr><th></th>${MESES.map(m=>`<th style="text-align:center">${m}</th>`).join('')}</tr></thead><tbody>`;
  anos.forEach(ano=>{
    html+=`<tr><th style="text-align:right;padding-right:8px;color:var(--ink-mute);font-size:10px;white-space:nowrap">${ano}</th>`;
    for(let m=0;m<12;m++){
      const k=ano+'-'+m;
      if(byM[k]){
        const v=byM[k].l;
        const roi=byM[k].s>0?fmtPct(v/byM[k].s*100,2,false):'0,00%';
        const ttl=`${MESES_CURTOS[m]}/${ano}: ${(v>0?'+':(v<0?'−':''))+'R$ '+fmt(Math.abs(v))} (ROI ${roi})`;
        html+=`<td class="heat-cell" style="background:${heatBg(v)};color:${heatTxt(v)}" title="${ttl}">${roi}</td>`;
      } else html+=`<td class="heat-empty"></td>`;
    }
    html+='</tr>';
  });
  html+='</tbody></table>';
  document.getElementById('heatmapWrap').innerHTML=html;
}

// ── Overview Heatmap Calendar ─────────────────────────────────────────────────
function renderOvHeatmap(){
  const cont=document.getElementById('ovHeatmapContent');if(!cont)return;
  if(!DADOS||!DADOS.length){cont.innerHTML=mkEmpty('Sem dados carregados');return;}
  // Acompanha o filtro: quando o mês de referência do período MUDA, o calendário
  // pula p/ esse mês. Enquanto o mês não muda, a nav própria (‹ ›) segue livre.
  const st=gfs('overview');
  const refM=st.dt?st.dt.slice(0,7):(st.qd>0?_today().slice(0,7):null);
  if(refM&&refM!==window._ovHeatRefLast){window._ovHeatMonth=refM;window._ovHeatRefLast=refM;}
  if(!window._ovHeatMonth){
    const months=[...new Set(DADOS.map(r=>r.data.slice(0,7)))].sort().reverse();
    window._ovHeatMonth=months[0]||'';
  }
  const range=_selRange('overview');   // dias dentro do período → contorno azul
  window._calHeatCb=null; // no click action on overview
  cont.innerHTML=mkCalendarHeatmap(window._ovHeatMonth,DADOS,{
    showNav:true,
    onPrev:"window._ovHeatMonth=(function(){const m=[...new Set(DADOS.map(r=>r.data.slice(0,7)))].sort().reverse();const i=m.indexOf(window._ovHeatMonth);return i<m.length-1?m[i+1]:window._ovHeatMonth;})();renderOvHeatmap()",
    onNext:"window._ovHeatMonth=(function(){const m=[...new Set(DADOS.map(r=>r.data.slice(0,7)))].sort().reverse();const i=m.indexOf(window._ovHeatMonth);return i>0?m[i-1]:window._ovHeatMonth;})();renderOvHeatmap()",
    onSelect:"window._ovHeatMonth=this.value;renderOvHeatmap()",
    range,
    compact:true
  });
}

// ── Card de cenário atual na Visão Geral ──
function renderOvStreaks(rows){
  const el=document.getElementById('ovStreaksContent');
  if(!el)return;
  // Filtro que zera o período → estado vazio explícito, senão o card ficava com os
  // números do filtro ANTERIOR (o KPI ao lado já zera → incoerência). Espelha o heatmap.
  if(!rows.length){el.innerHTML=mkEmpty('Sem apostas no período/filtro');return;}
  const _td=calcTopoDrawdown(rows);
  const _rf=calcRecoveryFactor(rows);
  const _dd=calcDrawdownReal(rows);
  const _mddR=_dd.mddReais;
  const _mddP=_dd.mddPct;
  const kS='display:flex;flex-direction:column;min-width:0;overflow:visible';
  const vS='font-size:16px';
  const sbS='margin-top:auto;padding-top:6px';
  const _fmtD=d=>{if(!d)return'—';const p=d.slice(0,10).split('-');return p[2]+'/'+p[1]+'/'+p[0];};
  const _ddDias=(a,b)=>{if(!a||!b)return null;return Math.round((new Date(b.slice(0,10))-new Date(a.slice(0,10)))/86400000);};
  const _mddDias=_ddDias(_dd.peakDate,_dd.troughDate);
  const _mddSub=(_dd.peakDate&&_dd.troughDate)?`${fmtPct(_mddP,1,false)} · ${_fmtD(_dd.peakDate)} - ${_fmtD(_dd.troughDate)} - ${_mddDias} dia${_mddDias===1?'':'s'}`:`${fmtPct(_mddP,1,false)} · pior real`;
  const _mddBench=_dd.troughDate?`<span class="lbl">vale em ${_fmtD(_dd.troughDate)}</span> · <span class="thr">quanto menor, melhor</span>`:'<span class="thr">quanto menor, melhor</span>';
  el.innerHTML=
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
        `<div class="kpi-sub" style="${sbS}">${_mddSub}</div>`+
      `</div>`+
      `<div class="kpi" style="${kS}">`+
        `<div class="kpi-label"><span class="kpi-pipe"></span>Recovery Factor ${_mkTipAnchor('Recovery Factor','<span class="lbl">RF</span> <span class="op">=</span> Lucro <span class="op">÷</span> Máx. Drawdown','Quantas vezes o lucro total <b>cobre a maior queda</b> da banca.','<span class="scale"><i></i><i></i><i></i><i class="on"></i><i class="on"></i></span> <span class="thr">&gt; 5</span> <span class="good">muito bom</span>')}</div>`+
        `<div class="fdc-kpi__value" data-state="info" style="${vS};text-align:right">${_rf!==null?fmtOdd(_rf)+'×':'—'}</div>`+
        `<div class="kpi-sub" style="${sbS}">qualidade</div>`+
      `</div>`+
    `</div>`;
}

// ── Card de diagnóstico de risco na Visão Geral ──
// Monte Carlo (p-value, DD Médio, DD Extremo, Solidez) roda em Web Worker via
// mcComputeAsync: o painel pinta na hora com "calculando…" e os valores entram
// quando o worker responde. Cache-hit (mesmo filtro) resolve no mesmo frame —
// sem flash de spinner (microtask antes do paint). _reqId evita corrida quando
// o usuário troca de filtro/aba antes de o cálculo anterior voltar.
let _ovRiscoReq=0;
function renderOvRisco(rows){
  const el=document.getElementById('ovRiscoContent');
  if(!el)return;
  if(!rows.length){el.innerHTML=mkEmpty('Sem apostas no período/filtro');return;}
  const kS='display:flex;flex-direction:column;min-width:0;overflow:visible';
  const vS='font-size:16px';
  const sbS='margin-top:auto;padding-top:6px';
  const spin='<span style="display:inline-flex;align-items:center;gap:6px;color:var(--ink-mute);font-family:var(--font-mono);font-size:11px"><svg width="14" height="14" viewBox="0 0 16 16" style="flex-shrink:0"><circle cx="8" cy="8" r="6" fill="none" stroke="var(--ink-mute)" stroke-width="2" stroke-dasharray="26" stroke-linecap="round"><animateTransform attributeName="transform" type="rotate" from="0 8 8" to="360 8 8" dur="0.8s" repeatCount="indefinite"/></circle></svg>calculando…</span>';
  // tooltips estáticos (não dependem do Monte Carlo)
  const tipDDmed=_mkTipAnchor('DD Médio','<span class="lbl">média</span> dos DD simulados','Queda <b>típica projetada</b> (média das 10.000 simulações de Monte Carlo). <b>Não aconteceu</b> — é estimativa.','<span class="lbl">projetado · média</span>');
  const tipDDext=_mkTipAnchor('DD Extremo','<span class="lbl">pior</span> DD simulado (p99)','Pior queda plausível (<b>1 em 100</b> cenários) — <b>não aconteceu</b>, é projeção de 10.000 reamostragens. Dimensiona a banca.','<span class="lbl">projetado · cauda · p99</span>');
  const tipSol=_mkTipAnchor('Nível de Solidez','<span class="lbl">índice composto</span>','P-value, drawdown e consistência <b>num selo só</b>.','<span class="lbl">Escala</span> <span class="scale"><i></i><i></i><i></i><i class="on"></i><i class="on"></i></span> <span class="good">Baixa → Alta</span>');
  // monta o painel; cada slot dinâmico é preenchido com `spin` (skeleton) ou o valor final
  const _frame=(pvLabel,pvVal,pvSub,ddMed,ddExt,solBlock)=>
    `<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:.75rem">`+
      `<div class="kpi" style="${kS}">`+
        `<div class="kpi-label"><span class="kpi-pipe"></span>p-value ${pvLabel}</div>`+
        `<div class="fdc-kpi__value" data-state="${pvVal.state}" style="${vS}">${pvVal.html}</div>`+
        `<div class="kpi-sub" style="${sbS}">${pvSub}</div>`+
      `</div>`+
      `<div class="kpi" style="${kS}">`+
        `<div class="kpi-label"><span class="kpi-pipe"></span>DD Médio ${tipDDmed}</div>`+
        `<div class="fdc-kpi__value" data-state="proj" style="${vS}">${ddMed}</div>`+
        `<div class="kpi-sub" style="${sbS}">projetado · média</div>`+
      `</div>`+
      `<div class="kpi" style="${kS}">`+
        `<div class="kpi-label"><span class="kpi-pipe"></span>DD Extremo ${tipDDext}</div>`+
        `<div class="fdc-kpi__value" data-state="proj" style="${vS}">${ddExt}</div>`+
        `<div class="kpi-sub" style="${sbS}">projetado · 1 em 100</div>`+
      `</div>`+
      `<div class="kpi" style="${kS}">`+
        `<div class="kpi-label"><span class="kpi-pipe"></span>Nível de Solidez ${tipSol}</div>`+
        `${solBlock}`+
      `</div>`+
    `</div>`;
  // skeleton: tooltip de p-value sem rodapé (depende do valor), valores = spinner
  const pvTipSkel=_mkTipAnchor('P-Value','<span class="lbl">p</span> <span class="op">=</span> P(resultado <span class="lbl">|</span> acaso)','Indicador heurístico (bootstrap): quão improvável seria seu resultado por <b>acaso</b>, sem vantagem. Menor = destaca-se mais do acaso — <b>não é prova estatística nem recomendação</b>.','');
  el.innerHTML=_frame(pvTipSkel,{state:'proj',html:spin},'<span style="color:var(--ink-mute)">—</span>',spin,spin,
    `<div class="fdc-risk-meter" style="margin-top:auto">${spin}</div>`);
  // dispara o cálculo (worker) e preenche quando voltar — descarta se já houve novo render
  const req=++_ovRiscoReq;
  mcComputeAsync(rows,10000).then(({mc:_mc,pv:_pv})=>{
    if(req!==_ovRiscoReq||!document.getElementById('ovRiscoContent'))return;
    const _td=calcTopoDrawdown(rows);
    const _profit=_td.atual;
    const _sol=calcSolidez({pValue:_pv,profitXmdd:_mc.xmdd>0?_profit/_mc.xmdd:0,nApostas:rows.length,oddMedia:calcAvgOdd(rows)});
    const _solCor=_sol.score>=0.65?'var(--d-pos)':_sol.score>=0.45?'var(--d-proj)':'var(--d-neg)';
    const pvTip=_mkTipAnchor('P-Value','<span class="lbl">p</span> <span class="op">=</span> P(resultado <span class="lbl">|</span> acaso)','Indicador heurístico (bootstrap): quão improvável seria seu resultado por <b>acaso</b>, sem vantagem. Menor = destaca-se mais do acaso — <b>não é prova estatística nem recomendação</b>.',rodapePValue(_pv));
    el.innerHTML=_frame(
      pvTip,
      {state:_pv<0.05?'pos':'proj',html:_pv<0.001?'< 0,001':fmt(_pv,4)},
      _pv<0.001?'sinal forte':_pv<0.05?'destaca do acaso':'inconclusivo',
      fmtPL(-_mc.xmdd),
      fmtPL(-_mc.p99),
      `<div class="fdc-risk-meter" style="margin-top:auto">`+
        `<span class="fdc-risk-meter__tag" style="color:${_solCor}">${_sol.faixa}</span>`+
        `<div class="fdc-risk-meter__track">`+
          `<span class="fdc-risk-meter__knob" style="--value:${(_sol.score*100).toFixed(1)}%"></span>`+
        `</div>`+
      `</div>`);
  });
}

// ── Card de custo na Visão Geral ──
function renderOvCusto(){
  const el=document.getElementById('ovCustoContent');
  if(!el)return;
  if((!_costState.allForns||!_costState.allForns.length)&&DADOS&&DADOS.length){
    buildCostState(DADOS);
  }
  const{allForns,allCasas,contaCount}=_costState;
  if(!allForns||!allForns.length){
    el.innerHTML=`<div style="text-align:center;padding:1.5rem;color:var(--ink-mute);font-size:12px;font-family:var(--font-sans)">Aguardando dados...</div>`;
    return;
  }
  const PIE_COLORS=['#2BC07E','#2E8BFF','#E0A21A','#7FB2FF','#95A1B0','#E5524B','#4FC79A','#D6A45A','#4DA3FF','#AEB7C2','#5E6775'];
  const fornTots={};
  allForns.forEach(f=>{fornTots[f]=allCasas.reduce((a,c)=>{const k=f+'||'+c;return a+(custoData[k]||0)*(contaCount[k]||0);},0);});
  const grandCost=Object.values(fornTots).reduce((a,v)=>a+v,0);
  if(!grandCost){
    el.innerHTML=`<div style="text-align:center;padding:1.5rem;color:var(--ink-mute);font-size:12px;font-family:var(--font-sans)">💡 Preencha os custos na aba <strong style="color:var(--warn)">Custos de Contas</strong> para ver o resumo aqui.</div>`;
    return;
  }
  const totalContas=allForns.reduce((a,f)=>a+allCasas.reduce((b,c)=>b+(contaCount[f+'||'+c]||0),0),0);
  // Custo médio só de contas que têm preço configurado (exclui contas grátis)
  const contasComPreco=allForns.reduce((a,f)=>a+allCasas.reduce((b,c)=>{const k=f+'||'+c;return b+((custoData[k]||0)>0?(contaCount[k]||0):0);},0),0);
  const avgCostPago=contasComPreco>0?grandCost/contasComPreco:0;
  const lucroTotal=DADOS.reduce((a,r)=>a+r.lucro,0);
  const lucroLiq=lucroTotal-grandCost;
  const casaTots={};
  allCasas.forEach(c=>{casaTots[c]=allForns.reduce((a,f)=>{const k=f+'||'+c;return a+(custoData[k]||0)*(contaCount[k]||0);},0);});
  const casasComCusto=allCasas.filter(c=>casaTots[c]>0);
  const avgPorCasa=casasComCusto.length>0?grandCost/casasComCusto.length:0;

  // Mini cards por casa — logo, nome em negrito, total acima, custo médio abaixo
  const casaCards=casasComCusto.sort((a,b)=>casaTots[b]-casaTots[a]).map(c=>{
    const nContas=allForns.reduce((a,f)=>a+(contaCount[f+'||'+c]||0),0);
    const nPago=allForns.reduce((a,f)=>{const k=f+'||'+c;return a+((custoData[k]||0)>0?(contaCount[k]||0):0);},0);
    const avg=nPago>0?casaTots[c]/nPago:0;
    return`<div style="background:var(--surface);border:1px solid var(--line);border-radius:var(--r-lg);padding:16px 22px;display:flex;align-items:center;gap:12px;min-width:220px">
      <div style="flex-shrink:0;transform:scale(1.3)">${casaImg(c,16)||''}</div>
      <div style="flex:1">
        <div style="font-size:13px;font-weight:700;color:var(--ink);margin-bottom:2px">${esc(c)}</div>
        <div style="font-size:10px;color:var(--ink-mute);font-family:'JetBrains Mono',monospace;margin-bottom:6px">${nContas} contas</div>
        <div style="display:flex;align-items:baseline;gap:10px">
          <span style="font-size:18px;font-weight:700;color:var(--warn);font-family:'JetBrains Mono',monospace">R$ ${fmt(casaTots[c],0)}</span>
          <span style="font-size:13px;font-weight:600;color:var(--ink-soft);font-family:'JetBrains Mono',monospace">R$${fmt(avg,0)}/conta</span>
        </div>
      </div>
    </div>`;
  }).join('');

  // Cards por fornecedor (idênticos ao card de Fornecedores & Parceiros)
  const fornCards=allForns.filter(f=>fornTots[f]>0).sort((a,b)=>fornTots[b]-fornTots[a]).map((f,i)=>{
    const tot=fornTots[f];
    const pct=grandCost>0?(tot/grandCost*100).toFixed(1):0;
    const nContas=allCasas.reduce((a,c)=>a+(contaCount[f+'||'+c]||0),0);
    const avgF=nContas>0?tot/nContas:0;
    const color=PIE_COLORS[i%PIE_COLORS.length];
    const casasComCustoF=allCasas.filter(c=>{const k=f+'||'+c;return (custoData[k]||0)>0&&(contaCount[k]||0)>0;});
    const casasF=casasComCustoF.sort((a,b)=>{const ka=f+'||'+a,kb=f+'||'+b;return (custoData[kb]||0)*(contaCount[kb]||0)-(custoData[ka]||0)*(contaCount[ka]||0);}).slice(0,5);
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
    const moreCount=casasComCustoF.length-5;
    return`<div style="background:var(--surface);border:1px solid var(--line);border-top:2px solid ${color};border-radius:var(--r-lg);padding:20px 22px;flex:1;min-width:200px;max-width:340px">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:.5rem">
        <div style="width:8px;height:8px;border-radius:50%;background:${color};flex-shrink:0"></div>
        <div style="font-size:13px;font-weight:700;color:var(--ink)">${esc(f)}</div>
        <div style="margin-left:auto;font-size:10px;font-family:'JetBrains Mono',monospace;color:var(--ink-mute)">${pct}% do total</div>
      </div>
      <div style="font-size:22px;font-weight:700;color:var(--warn);font-family:'JetBrains Mono',monospace;letter-spacing:-.02em;margin-bottom:2px">R$ ${fmt(tot,0)}</div>
      <div style="font-size:10px;color:var(--ink-mute);font-family:'JetBrains Mono',monospace;margin-bottom:.75rem">${nContas} contas · média R$${fmt(avgF,0)}/conta</div>
      <div>${casaRows}</div>
      ${moreCount>0?`<div style="font-size:10px;color:var(--ink-mute);font-family:'JetBrains Mono',monospace;margin-top:5px;text-align:center">+ ${moreCount} casas</div>`:''}
    </div>`;
  }).join('');

  el.innerHTML=`
    <div class="kpi-grid" style="margin-bottom:1rem">
      <div class="kpi"><div class="kpi-label">Custo Total</div><div class="kpi-val neg">R$ ${fmt(grandCost,0)}</div><div class="kpi-sub">${totalContas} contas · ${allForns.filter(f=>fornTots[f]>0).length} fornecedores</div></div>

      <div class="kpi"><div class="kpi-label">Custo Médio/Conta</div><div class="kpi-val neu">R$ ${fmt(avgCostPago,0)}</div><div class="kpi-sub">${contasComPreco} contas com preço</div></div>
      <div class="kpi"><div class="kpi-label">Custo Médio/Casa</div><div class="kpi-val neu">R$ ${fmt(avgPorCasa,0)}</div><div class="kpi-sub">${casasComCusto.length} casas com custo</div></div>
    </div>
    ${casasComCusto.length>0?`<div style="display:flex;flex-wrap:wrap;gap:.5rem;margin-bottom:1rem;padding-bottom:1rem;border-bottom:1px solid var(--line-2)">${casaCards}</div>`:''}
    <div style="display:flex;flex-wrap:wrap;gap:.75rem">${fornCards}</div>`;
}
