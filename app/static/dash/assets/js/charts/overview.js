// ── overview.js — Gráficos e cards da Visão Geral ──────────────────────────────

// ── Cartão "Custo de Contas": bloco de contas em operação (s358) ───────────
// Três células, sem linha de nota embaixo. A nota repetia o número do topo — o que ela
// dizia de útil era o CORTE de cada número, e corte cabe em RÓTULO, que não custa linha:
//
//     CONTAS      JÁ PAGO        NO P/L
//     1 conta     R$ 800         R$ 79.300
//
//   · CONTAS  — quantas estão em operação HOJE (o rótulo vira `DESTE TIPSTER` com filtro)
//   · JÁ PAGO — o que elas custaram, acumulado. Saiu do bolso e NÃO está no P/L.
//   · NO P/L  — quanto do custo entrou no resultado do período. É o número do topo, e
//     só aparece quando houve compra: sem ela o topo já diz R$ 0 e a célula seria um zero
//     a mais na tela.
//
// O bloco IGNORA o filtro de período: é sempre "em operação hoje". Só o topo (e a 3ª
// célula, que é o mesmo número) obedecem ao intervalo.
function _blocoContas(costConta){
  if(window.MODO_PUBLICO)return null;
  const op=(typeof calcContasEmOperacao==='function')?calcContasEmOperacao('overview'):{total:0,nContas:0};
  if(!(op.total>0))return null;   // sem conta com custo: quem responde é a legenda do cartão
  const temTipster=(typeof msGet==='function')&&msGet('ti_overview').size>0;
  const cel=(l,v,cls)=>`<div class="kpi__cell"><div class="kpi__cl">${l}</div>`
    +`<div class="kpi__cv${cls||''}">${v}</div></div>`;
  // DUAS células, não três: medido em 1366, com três a célula fica com 57px e o valor
  // `R$ 29.400` (68px) é truncado. Duas cabem com folga em qualquer largura.
  //
  // E sem a linha de nota: ela repetia o número do topo. O que ela dizia de útil era o
  // CORTE de cada número, e isso cabe no RÓTULO — "custo delas" amarra o valor às contas
  // em operação, e por oposição deixa o topo como o custo do período.
  const cels=[
    cel(temTipster?'Deste tipster':'Em operação',`${op.nContas}<span class="u">${op.nContas===1?'conta':'contas'}</span>`),
    // Sem centavos (`fmtR`): o bloco é referência, não conferência de extrato.
    cel('Custo delas',fmtR(op.total),' is-cost'),
  ];
  return `<div class="kpi__duo">${cels.join('')}</div>`;
}

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
  // Custo de contas — o que foi PAGO no período (s358). Não deriva de `rows`: o período
  // da tela é que manda, tenha ou não sobrado aposta nele. Ver `calcCostFiltered`.
  const{costConta,nContas:nContasCusto}=calcCostFiltered('overview');
  const _blocoCt=_blocoContas(costConta);
  // Custo de tipster — só os meses do PERÍODO, e só os tipsters SELECIONADOS (s358).
  // A régua mora no `calcCustoTipsterFiltrado` (gestao.js), junto do custo de conta: as
  // duas linhas do mesmo card não podem medir de jeitos diferentes.
  if(!window.MODO_PUBLICO)ctLoad();   // público: /custos/store é autenticada (daria 401)
  const{total:costTipster,nTips:nTipsCusto}=(!window.MODO_PUBLICO&&typeof calcCustoTipsterFiltrado==='function')
    ?calcCustoTipsterFiltrado('overview'):{total:0,nTips:0};
  // Custos gerais — VPN, ferramentas, taxas (s358, etapa 4). Eram lançados e NÃO desciam
  // no P/L Líquido: o Jonathan tem R$ 987/mai, R$ 1.468/jun e R$ 1.321/jul que nunca
  // entraram na conta dele. Filtro nenhum recorta: a VPN é da operação inteira.
  const{total:costGeral,nLinhas:nGeralCusto}=(!window.MODO_PUBLICO&&typeof calcCustoGeralFiltrado==='function')
    ?calcCustoGeralFiltrado('overview'):{total:0,nLinhas:0};
  const totalCost=costConta+costTipster+costGeral;
  const lucroLiq=lucro-totalCost;

  // ── Andar 1: P/L Bruto → Custo Conta → Custo Tipster → P/L Líquido ────────
  // Público (vitrine de tipster): custo é conceito do DONO, não do cliente do
  // tipster — os dois cards sairiam sempre 0,00u. O andar 1 vira um único P/L
  // hero de largura cheia (bruto = líquido sem custos).
  const row1=window.MODO_PUBLICO?[
    {l:'P/L',v:fmtPL(lucro),c:lucro>=0?'pos':'neg',s:'resultado da carteira',accent:'hero',span:true},
  ]:[
    {l:'P/L Bruto',v:fmtPL(lucro),c:lucro>=0?'pos':'neg',s:'antes de custos',accent:''},
    // O rodapé faz o trabalho que a legenda fazia, e melhor: com a régua de caixa, um
    // período sem compra mostra `R$ 0` no topo, e sozinho isso lê como defeito. Embaixo
    // ficam as contas que estão rodando HOJE e o que elas já custaram — dinheiro que não
    // entra no P/L, e a ressalva diz isso na própria linha.
    // Sem bloco (nenhuma conta com custo), a legenda do cartão responde — e ela é a
    // mesma linha que os outros sete usam, então o cartão não fica órfão de contexto.
    {l:'Custo de Contas',v:costConta>0?fmtPL(-costConta):fmtR(0),c:costConta>0?'neg':'neu',
     accent:'',foot:_blocoCt,s:_blocoCt?'':'nenhuma conta com custo cadastrado'},
    {l:'Custo de Tipsters',v:costTipster>0?fmtPL(-costTipster):fmtR(0),c:costTipster>0?'neg':'neu',
     s:nTipsCusto?(nTipsCusto===1?'1 tipster no período':nTipsCusto+' tipsters no período'):'nenhuma assinatura no período',accent:''},
    // O card de GERAIS só existe quando há valor lançado. Sem ele o andar fica nos 4 de
    // sempre; com ele são 5, e é preciso que ele apareça: o P/L Líquido desconta esse
    // dinheiro, e KPI que desconta o que não está na tela é inauditável — é o sintoma de
    // "o KPI não bate com a soma que está logo abaixo dele" (CLAUDE.md).
    ...(costGeral>0?[{l:'Custos Gerais',v:fmtPL(-costGeral),c:'neg',
      s:nGeralCusto===1?'1 categoria no período':nGeralCusto+' categorias no período',accent:''}]:[]),
    {l:'P/L Líquido',v:fmtPL(lucroLiq),c:lucroLiq>=0?'pos':'neg',s:'resultado final',accent:'hero'},
  ];
  // ── Andar 2: Turnover → ROI → Odd Média → Win Rate ──────────────────────
  const row2=[
    {l:'Turnover',v:fmtR(stake),c:'neu',s:'volume apostado'},
    {l:'ROI',v:fmtPct(roi,2),c:roi>=0?'pos':'neg',s:n+' apostas'},
    {l:'Odd Média',v:fmtOdd(calcAvgOdd(rows)),c:'neu',s:'ponderada'},
    {l:'Win Rate',v:fmtPct(wr,1,false),c:'neu',s:settled+' encerradas',bar:wr},
  ];
  // Quatro colunas fixas, como a referência: os oito cartões em 4 + 4, todos com a mesma
  // altura (o CSS põe `min-height` nos oito, não só no de custo — altura solta num deles
  // esticaria a fileira). Os dois cortes vêm do desenho: 2 colunas abaixo de 1100px e
  // 1 abaixo de 560px. Sem `auto-fit`, que subia para 5 colunas em tela larga e deixava
  // buraco na 2ª linha.
  const gridCss=(n,mb)=>`display:grid;grid-template-columns:repeat(var(--kpi-cols,${n}),minmax(0,1fr));gap:14px;margin-bottom:${mb}`;
  document.getElementById('kpiGrid').innerHTML=
    `<div style="${gridCss(row1.length,'10px')}">`+
    row1.map(k=>`<div class="kpi ${k.accent||''}${k.foot?' has-duo':''}"${k.span?' style="grid-column:1/-1"':''}>`
      +`<div class="kpi-label"><span class="kpi-pipe"></span> ${k.l}</div>`
      +`<div class="kpi-val ${k.c}">${k.v}</div>`
      +(k.foot||'')
      +(k.s?`<div class="kpi-sub">${k.s}</div>`:'')
      +`</div>`).join('')+
    `</div>`+
    `<div style="${gridCss(4,'1.25rem')}">`+
    row2.map(k=>`<div class="kpi"><div class="kpi-label"><span class="kpi-pipe"></span> ${k.l}</div><div class="kpi-val ${k.c}">${k.v}</div>${k.bar!==undefined?`<div class="wrc"><div class="t"><div class="f" style="width:${Math.min(100,Math.max(0,k.bar)).toFixed(1)}%"></div></div></div>`:''}<div class="kpi-sub">${k.s}</div></div>`).join('')+
    `</div>`;
}

// ── Dia da semana (Visão Geral) ───────────────────────────────────────────────
// Ao contrário do calendário logo acima, este cartão SEGUE o período do filtro
// (recebe `rows`, o mesmo recorte dos KPIs do topo). O calendário é do mês por
// desenho e tem navegação própria; aqui a pergunta é "no que estou olhando, em
// que dia da semana eu ganho dinheiro" — dois cartões vizinhos com réguas
// diferentes, e é por isso que o calendário carrega a nota de escopo e este não.
function renderOvDow(rows){
  const el=document.getElementById('ovDowContent');
  if(!el)return;
  if(!rows.length){el.innerHTML=mkEmpty('Sem apostas no período/filtro');return;}
  el.innerHTML=mkDowRanking(rows,{id:'ov'});
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
    html+=`<tr><th style="text-align:right;padding-right:8px;color:var(--ink-soft);font-size:10px;white-space:nowrap">${ano}</th>`;
    for(let m=0;m<12;m++){
      const k=ano+'-'+m;
      if(byM[k]){
        const v=byM[k].l;
        const roi=byM[k].s>0?fmtPct(v/byM[k].s*100,2,false):'0,00%';
        const ttl=`${MESES_CURTOS[m]}/${ano}: ${(v>0?'+':(v<0?'−':''))+(window.MODO_PUBLICO?fmt(Math.abs(v))+'u':'R$ '+fmt(Math.abs(v)))} (ROI ${roi})`;
        html+=`<td class="heat-cell" style="background:${heatBg(v)};color:${heatTxt(v)}" title="${ttl}">${roi}</td>`;
      } else html+=`<td class="heat-empty"></td>`;
    }
    html+='</tr>';
  });
  html+='</tbody></table>';
  document.getElementById('heatmapWrap').innerHTML=html;
}

// ── Overview Heatmap Calendar ─────────────────────────────────────────────────
// Linhas que alimentam o calendário: respeitam Esporte / Casa / Tipster / Operador,
// mas NÃO o corte por data — o cartão é um calendário de MÊS, com navegação própria,
// e recortá-lo pelo período o esvaziaria fora do intervalo. Mesmo motivo do ROI
// Mensal (filters.js:filtrarSemData).
// Até a s319 ele recebia DADOS cru e ignorava também os quatro filtros: escolher um
// tipster mudava os KPIs de cima e não mudava nada aqui.
function _ovCalRows(){return filtrarSemData('overview');}
// Espelha a lista de meses do mkCalendarHeatmap (que inclui o mês selecionado mesmo
// sem linha), senão a nav ‹ › e o cartão discordam sobre onde estão as pontas.
function _ovCalMeses(){
  return [...new Set([..._ovCalRows().map(r=>r.data.slice(0,7)),window._ovHeatMonth].filter(Boolean))].sort().reverse();
}
function renderOvHeatmap(){
  const cont=document.getElementById('ovHeatmapContent');if(!cont)return;
  if(!DADOS||!DADOS.length){cont.innerHTML=mkEmpty('Sem dados carregados');return;}
  const rows=_ovCalRows();
  if(!rows.length){cont.innerHTML=mkEmpty('Sem apostas no filtro');return;}
  // Acompanha o filtro: quando o mês de referência do período MUDA, o calendário
  // pula p/ esse mês. Enquanto o mês não muda, a nav própria (‹ ›) segue livre.
  const st=gfs('overview');
  const refM=st.dt?st.dt.slice(0,7):(st.qd>0?_today().slice(0,7):null);
  if(refM&&refM!==window._ovHeatRefLast){window._ovHeatMonth=refM;window._ovHeatRefLast=refM;}
  if(!window._ovHeatMonth){
    const months=[...new Set(rows.map(r=>r.data.slice(0,7)))].sort().reverse();
    window._ovHeatMonth=months[0]||'';
  }
  const range=_selRange('overview');   // dias dentro do período → contorno azul
  window._calHeatCb=null; // no click action on overview
  cont.innerHTML=mkCalendarHeatmap(window._ovHeatMonth,rows,{
    showNav:true,
    onPrev:"window._ovHeatMonth=(function(){const m=_ovCalMeses();const i=m.indexOf(window._ovHeatMonth);return i<m.length-1?m[i+1]:window._ovHeatMonth;})();renderOvHeatmap()",
    onNext:"window._ovHeatMonth=(function(){const m=_ovCalMeses();const i=m.indexOf(window._ovHeatMonth);return i>0?m[i-1]:window._ovHeatMonth;})();renderOvHeatmap()",
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
        `<div class="fdc-kpi__value"${_td.topo>0?' data-state="pos"':''} style="${vS}">${fmtPL(_td.topo)}</div>`+
        `<div class="kpi-sub" style="${sbS}">${topoSub(_td)}</div>`+
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
