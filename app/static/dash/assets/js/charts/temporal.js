// ── temporal.js — Aba RESULTADOS (unificada) ─────────────────────────────────
// Substitui as antigas Consolidado, Mensal, Diário, Semana e Por Casa.
// Conteúdo:
//   1. KPIs do período
//   2. Matriz tipster × tempo (Ano = meses · Mês = dias · Semana = seg→dom)
//   3. Resultado Geral (gráfico acumulado + diário)
//   4. Calendário — resultados diários
//   5. Desempenho por Dia da Semana          (novo — não existia em outra aba)
//   6. Contribuição & Consistência por Tipster (novo)
//   7. Correlação entre Tipsters             (novo)
// Filtro de dados é o da página (buildFilters → filtrarPagina('resultados')).
// O seletor Ano/Mês/Semana controla SÓ a granularidade da matriz.

// ── Estado (module-level, persiste entre re-renders) ─────────────────────────
window._resMatMode     = window._resMatMode     || 'ano';   // 'ano' | 'mes' | 'semana'
window._resMatMonth    = window._resMatMonth     || null;    // 'YYYY-MM' (modo mes)
window._resMatWeek     = window._resMatWeek      || null;    // 'YYYY-MM-DD' segunda (modo semana)
window._resCalMonth    = window._resCalMonth     || null;    // 'YYYY-MM' (calendário)
window._resContribSort = window._resContribSort  || {k:'pl',dir:-1};

// ── Helpers ──────────────────────────────────────────────────────────────────
// P/L em texto puro — fmtPL devolve HTML com aspas e NÃO pode entrar em title=""
function _txtPL(v){return (v>=0?'+':'−')+'R$ '+fmt(Math.abs(v));}

function _resMonday(dateStr){
  const d=new Date(dateStr+'T12:00:00');
  const day=d.getDay();
  const diff=day===0?-6:1-day; // Segunda = início da semana
  d.setDate(d.getDate()+diff);
  return d.toISOString().slice(0,10);
}

// Escala de cor do heatmap (mesma lógica dos heatmaps existentes; rgba data-viz)
function _resHeat(maxAbs){
  return {
    bg:v=>{if(!v)return'transparent';const a=0.12+Math.min(1,Math.abs(v)/maxAbs)*0.82;return v>0?`rgba(0,160,100,${a})`:`rgba(200,40,60,${a})`;},
    txt:v=>{if(v===0)return'var(--ink-mute)';const a=0.12+Math.min(1,Math.abs(v)/maxAbs)*0.82;return a>0.5?(v>0?'#d0fff0':'#ffe0e5'):(v>0?'var(--pos)':'var(--neg)');}
  };
}

// ── Matriz genérica tipster × coluna ─────────────────────────────────────────
// cols: [{key,label}] ; colKeyOf(r) → key da coluna
function _resMatrixHTML(rows, cols, colKeyOf){
  const tips=[...new Set(rows.map(r=>r.tipster).filter(Boolean))];
  if(!tips.length||!cols.length) return mkEmpty('Sem dados no período');
  const colSet={}; cols.forEach(c=>colSet[c.key]={pl:0,n:0});
  const agg={}, accT={};
  tips.forEach(t=>{agg[t]={}; accT[t]={pl:0,n:0};});
  rows.forEach(r=>{
    const t=r.tipster; if(!t)return;
    const ck=colKeyOf(r); if(!(ck in colSet))return;   // fora das colunas exibidas
    if(!agg[t][ck])agg[t][ck]={pl:0,n:0,s:0};
    const cell=agg[t][ck]; cell.pl+=r.lucro; cell.n++; if(r.resultado!=='V')cell.s+=r.stake;
    accT[t].pl+=r.lucro; accT[t].n++;
    colSet[ck].pl+=r.lucro; colSet[ck].n++;
  });
  tips.sort((a,b)=>accT[b].pl-accT[a].pl);
  let maxAbs=1;
  tips.forEach(t=>cols.forEach(c=>{const cell=agg[t][c.key];if(cell)maxAbs=Math.max(maxAbs,Math.abs(cell.pl));}));
  const heat=_resHeat(maxAbs);
  const totPL=tips.reduce((a,t)=>a+accT[t].pl,0);
  const totN=tips.reduce((a,t)=>a+accT[t].n,0);

  const hBg='background:var(--field)';
  const rBg='background:var(--surface-2)';
  const sT ='position:sticky;left:0;z-index:2;white-space:nowrap;'+rBg+';';
  const sA ='position:sticky;left:140px;z-index:2;white-space:nowrap;border-right:1px solid var(--line);'+rBg+';';
  const sTh='position:sticky;left:0;z-index:3;'+hBg+';';
  const sAh='position:sticky;left:140px;z-index:3;border-right:1px solid var(--line);'+hBg+';';
  const thBase='padding:6px 10px;text-align:right;font-size:9px;text-transform:uppercase;letter-spacing:.08em;color:var(--ink-mute);white-space:nowrap;';

  const head=`<tr style="border-bottom:1px solid var(--line)">
    <th style="${sTh}${thBase}text-align:left;min-width:140px">Tipster</th>
    <th style="${sAh}${thBase}min-width:100px">Acumulado</th>
    ${cols.map(c=>`<th style="${hBg};${thBase}min-width:104px">${c.label}</th>`).join('')}
  </tr>`;

  const totCells=cols.map(c=>{
    const d=colSet[c.key];
    if(!d||d.n===0)return`<td style="${hBg};text-align:right;padding:5px 8px;color:var(--ink-mute);font-size:11px">—</td>`;
    return`<td style="background:${heat.bg(d.pl)};color:${heat.txt(d.pl)};border-radius:3px;text-align:right;padding:5px 8px;font-weight:700;white-space:nowrap;font-size:11px">${fmtPL(d.pl)}<br><span style="font-size:9px;opacity:.7">${d.n}b</span></td>`;
  }).join('');
  const totRow=`<tr style="border-bottom:2px solid var(--line)">
    <td style="${sT}font-weight:700;color:var(--ink);padding:6px 10px;border-right:1px solid var(--line)">Total</td>
    <td style="${sA}color:${totPL>=0?'var(--pos)':'var(--neg)'};text-align:right;padding:6px 10px;font-weight:700">${fmtPL(totPL)}<br><span style="font-size:9px;opacity:.55;color:var(--ink-mute)">${totN}b</span></td>
    ${totCells}
  </tr>`;

  const body=tips.map(t=>{
    const acc=accT[t];
    const accC=acc.pl>=0?'var(--pos)':'var(--neg)';
    const cells=cols.map(c=>{
      const d=agg[t][c.key];
      if(!d||d.n===0)return`<td style="${hBg};border-radius:3px;text-align:right;padding:5px 8px;color:var(--ink-mute);font-size:11px">—</td>`;
      const roi=d.s>0?(d.pl/d.s*100):0;
      const title=`${t} · ${c.label}: ${_txtPL(d.pl)} — ${d.n} bets · ROI ${fmtPct(roi,2)}`;
      return`<td title="${title}" style="background:${heat.bg(d.pl)};color:${heat.txt(d.pl)};border-radius:3px;text-align:right;padding:5px 8px;font-weight:600;white-space:nowrap;font-size:11px">${fmtPL(d.pl)}<br><span style="font-size:9px;opacity:.7">${fmtPct(roi,1)} · ${d.n}b</span></td>`;
    }).join('');
    return`<tr>
      <td style="${sT}font-weight:700;color:var(--ink);padding:5px 10px;border-right:1px solid var(--line);font-size:12px">${t}</td>
      <td style="${sA}color:${accC};text-align:right;padding:5px 10px;font-weight:700;font-size:12px">${fmtPL(acc.pl)}<br><span style="font-size:9px;opacity:.55;color:var(--ink-mute)">${acc.n}b</span></td>
      ${cells}
    </tr>`;
  }).join('');

  return`<div style="overflow-x:auto"><table style="border-collapse:separate;border-spacing:2px;font-family:'JetBrains Mono',monospace;font-variant-numeric:tabular-nums">
    <thead>${head}</thead><tbody>${totRow}${body}</tbody></table></div>`;
}

// Monta a seção matriz conforme o modo → {html, nav}
function _resMatrixSection(rows){
  const mode=window._resMatMode;
  let cols=[], colKeyOf=r=>r.data.slice(0,7), nav='';
  if(mode==='ano'){
    const yms=[...new Set(rows.map(r=>r.data.slice(0,7)))].sort().reverse();
    cols=yms.map(ym=>{const[y,m]=ym.split('-');return{key:ym,label:MESES_CURTOS[parseInt(m)-1]+' '+y};});
    colKeyOf=r=>r.data.slice(0,7);
  } else if(mode==='mes'){
    const months=[...new Set(rows.map(r=>r.data.slice(0,7)))].sort().reverse();
    if(!months.length)return{html:mkEmpty('Sem dados no período'),nav:''};
    let sel=window._resMatMonth; if(!months.includes(sel))sel=months[0];
    window._resMatMonth=sel;
    const days=[...new Set(rows.filter(r=>r.data.slice(0,7)===sel).map(r=>r.data.slice(0,10)))].sort();
    const DOWS=['Dom','Seg','Ter','Qua','Qui','Sex','Sáb'];
    cols=days.map(d=>{const dp=new Date(d+'T12:00:00');return{key:d,label:DOWS[dp.getDay()]+' '+d.slice(8)};});
    colKeyOf=r=>r.data.slice(0,10);
    const[y,m]=sel.split('-');
    nav=`<button class="qbtn" onclick="resMatNav(-1)" aria-label="Mês anterior">◀</button><span style="font-family:var(--font-mono);font-size:11px;color:var(--ink-soft);min-width:120px;text-align:center;display:inline-block">${MESES[parseInt(m)-1]+' '+y}</span><button class="qbtn" onclick="resMatNav(1)" aria-label="Próximo mês">▶</button>`;
  } else { // semana
    const allDays=[...new Set(rows.map(r=>r.data.slice(0,10)))].sort();
    const weeks=[...new Set(allDays.map(d=>_resMonday(d)))].sort().reverse();
    if(!weeks.length)return{html:mkEmpty('Sem dados no período'),nav:''};
    let sel=window._resMatWeek; if(!weeks.includes(sel))sel=weeks[0];
    window._resMatWeek=sel;
    const DOWS=['Dom','Seg','Ter','Qua','Qui','Sex','Sáb'];
    const wdays=[];{const d=new Date(sel+'T12:00:00');for(let i=0;i<7;i++){wdays.push(d.toISOString().slice(0,10));d.setDate(d.getDate()+1);}}
    cols=wdays.map(d=>{const dp=new Date(d+'T12:00:00');const[,mm,dd]=d.split('-');return{key:d,label:DOWS[dp.getDay()]+' '+dd+'/'+mm};});
    colKeyOf=r=>r.data.slice(0,10);
    const end=new Date(sel+'T12:00:00');end.setDate(end.getDate()+6);
    const[,ms,dsv]=sel.split('-');const[,me,de]=end.toISOString().slice(0,10).split('-');
    nav=`<button class="qbtn" onclick="resMatNav(-1)" aria-label="Semana anterior">◀</button><span style="font-family:var(--font-mono);font-size:11px;color:var(--ink-soft);min-width:140px;text-align:center;display:inline-block">${dsv}/${ms} → ${de}/${me}</span><button class="qbtn" onclick="resMatNav(1)" aria-label="Próxima semana">▶</button>`;
  }
  return{html:_resMatrixHTML(rows,cols,colKeyOf),nav};
}

// ── Desempenho por dia da semana ─────────────────────────────────────────────
function _resWeekdayHTML(rows){
  const NAMES=['Domingo','Segunda','Terça','Quarta','Quinta','Sexta','Sábado'];
  const ORDER=[1,2,3,4,5,6,0]; // seg → dom
  const by={}; ORDER.forEach(i=>by[i]={pl:0,s:0,n:0,t:0,w:0});
  rows.forEach(r=>{
    const i=new Date(r.data.slice(0,10)+'T12:00:00').getDay();
    const d=by[i]; d.pl+=r.lucro; d.n++;
    if(r.resultado!=='V'){d.s+=r.stake;d.t++;}
    if(r.resultado==='W'||r.resultado==='HW')d.w++;
  });
  const maxAbs=Math.max(...ORDER.map(i=>Math.abs(by[i].pl)),1);
  const rowsH=ORDER.map(i=>{
    const d=by[i];
    const roi=d.s>0?(d.pl/d.s*100):0, wr=d.t>0?(d.w/d.t*100):0;
    const barW=Math.abs(d.pl)/maxAbs*100;
    const c=d.pl>=0?'var(--pos)':'var(--neg)';
    return`<tr>
      <td style="font-weight:600;color:var(--ink)">${NAMES[i]}</td>
      <td class="td-c">${d.n}</td>
      <td class="td-num" style="color:${c};font-weight:600">${d.n?fmtPL(d.pl):'—'}</td>
      <td class="td-num">${fmtR(d.s)}</td>
      <td class="td-c" style="color:${roi>=0?'var(--pos)':'var(--neg)'}">${d.t?fmtPct(roi,2):'—'}</td>
      <td class="td-c">${d.t?mkWRC(wr):'—'}</td>
      <td style="width:120px"><div style="height:10px;background:var(--elevated);border-radius:3px;overflow:hidden"><div style="height:100%;width:${barW.toFixed(1)}%;background:${c};opacity:.8;border-radius:3px"></div></div></td>
    </tr>`;
  }).join('');
  return`<div class="tbl-wrap"><table class="tbl" id="tblResWeekday">
    <thead><tr>${mkTh('Dia da semana','','l')}${mkTh('Bets','','r')}${mkTh('P/L','','r')}${mkTh('Turnover','','r')}${mkTh('ROI','','r')}${mkTh('Win Rate','','r')}<th></th></tr></thead>
    <tbody>${rowsH}</tbody></table></div>
    <p style="font-size:10px;color:var(--ink-mute);margin-top:10px;font-family:var(--font-mono)">P/L somado por dia da semana em todo o período filtrado — revela vícios de calendário (ex.: sábado com jogos de menor valor).</p>`;
}

// ── Contribuição & Consistência por tipster ──────────────────────────────────
function _resContribSeg(){
  const s=window._resContribSort;
  const b=(k,l)=>`<button data-k="${k}" class="${s.k===k?'active':''}" onclick="resContribSortBy('${k}')">${l}</button>`;
  return`<div class="tcard-sort" style="margin-bottom:12px"><span class="tcard-sort__lbl">Ordenar</span><div class="tcard-seg">${b('pl','P/L')}${b('peso','Peso')}${b('vol','Volatilidade')}${b('forma','Forma')}</div><button class="tcard-dir" onclick="resContribSortDir()">${s.dir<0?'↓':'↑'}</button></div>`;
}
function _resContribHTML(rows){
  const tips=[...new Set(rows.map(r=>r.tipster).filter(Boolean))];
  if(!tips.length)return mkEmpty('Sem dados no período');
  const totPL=rows.reduce((a,r)=>a+r.lucro,0);
  // janelas de "forma": últimos 30d vs 30d anteriores (ancorado na última data do conjunto)
  const maxDate=rows.reduce((m,r)=>r.data>m?r.data:m,'').slice(0,10);
  const _shift=(base,days)=>{const d=new Date(base+'T12:00:00');d.setDate(d.getDate()+days);return d.toISOString().slice(0,10);};
  const lim30=maxDate?_shift(maxDate,-30):'', lim60=maxDate?_shift(maxDate,-60):'';
  const data=tips.map(t=>{
    const tr=rows.filter(r=>r.tipster===t);
    const pl=tr.reduce((a,r)=>a+r.lucro,0);
    const byM={}; tr.forEach(r=>{const ym=r.data.slice(0,7);byM[ym]=(byM[ym]||0)+r.lucro;});
    const months=Object.keys(byM).sort();
    const series=months.map(m=>byM[m]);
    const mean=series.length?series.reduce((a,b)=>a+b,0)/series.length:0;
    const vol=series.length?Math.sqrt(series.reduce((a,b)=>a+(b-mean)**2,0)/series.length):0;
    let best=null,worst=null;
    months.forEach(m=>{if(best===null||byM[m]>byM[best])best=m;if(worst===null||byM[m]<byM[worst])worst=m;});
    const last30=tr.filter(r=>r.data.slice(0,10)>lim30).reduce((a,r)=>a+r.lucro,0);
    const prev30=tr.filter(r=>{const d=r.data.slice(0,10);return d>lim60&&d<=lim30;}).reduce((a,r)=>a+r.lucro,0);
    return{t,pl,vol,best,worst,bestV:best?byM[best]:0,worstV:worst?byM[worst]:0,forma:last30-prev30};
  });
  const {k,dir}=window._resContribSort;
  const key=d=>k==='vol'?d.vol:k==='forma'?d.forma:k==='peso'?(totPL?d.pl/totPL:0):d.pl;
  data.sort((a,b)=>(key(a)-key(b))*dir);
  const mLbl=ym=>{if(!ym)return'—';const[y,m]=ym.split('-');return MESES_CURTOS[parseInt(m)-1]+' '+y.slice(2);};
  const body=data.map(d=>{
    const peso=totPL?(d.pl/totPL*100):0;
    const lc=d.pl>=0?'color:var(--pos)':'color:var(--neg)';
    const arrow=d.forma>0?'▲':d.forma<0?'▼':'■';
    const fc=d.forma>0?'var(--pos)':d.forma<0?'var(--neg)':'var(--ink-mute)';
    return`<tr>
      <td style="font-weight:700;color:var(--ink)">${d.t}</td>
      <td class="td-num" style="${lc};font-weight:600">${fmtPL(d.pl)}</td>
      <td class="td-c" style="color:var(--ink-soft)">${fmtPct(peso,1)}</td>
      <td class="td-num" style="color:var(--ink-soft)">${fmtR(d.vol)}</td>
      <td class="td-c" style="color:${fc};white-space:nowrap">${arrow} ${fmtPL(d.forma)}</td>
      <td class="td-c" style="font-size:11px"><span style="color:var(--ink-soft)">${mLbl(d.best)}</span><br><span style="color:var(--pos);font-size:10px">${d.best?fmtPL(d.bestV):''}</span></td>
      <td class="td-c" style="font-size:11px"><span style="color:var(--ink-soft)">${mLbl(d.worst)}</span><br><span style="color:var(--neg);font-size:10px">${d.worst?fmtPL(d.worstV):''}</span></td>
    </tr>`;
  }).join('');
  return _resContribSeg()+`<div class="tbl-wrap"><table class="tbl">
    <thead><tr>${mkTh('Tipster','','l')}${mkTh('P/L','','r')}${mkTh('Peso','','r')}${mkTh('Volatilidade','','r')}${mkTh('Forma 30d','','c')}${mkTh('Melhor mês','','c')}${mkTh('Pior mês','','c')}</tr></thead>
    <tbody>${body}</tbody></table></div>
    <p style="font-size:10px;color:var(--ink-mute);margin-top:10px;font-family:var(--font-mono);line-height:1.7">
      <b style="color:var(--ink-soft)">Peso</b>: fração do P/L líquido total (soma 100%). ·
      <b style="color:var(--ink-soft)">Volatilidade</b>: desvio-padrão dos P/L mensais — quanto maior, mais "serra". ·
      <b style="color:var(--ink-soft)">Forma 30d</b>: P/L dos últimos 30 dias vs. os 30 anteriores.</p>`;
}
window.resContribSortBy=function(k){const s=window._resContribSort;if(s.k===k)s.dir*=-1;else{s.k=k;s.dir=-1;}renderResultados();};
window.resContribSortDir=function(){window._resContribSort.dir*=-1;renderResultados();};

// ── Correlação entre tipsters (P/L mensal) ───────────────────────────────────
function _resCorrHTML(rows){
  const tips=[...new Set(rows.map(r=>r.tipster).filter(Boolean))];
  if(tips.length<2)return mkEmpty('Tipsters insuficientes para correlação');
  const toByT={}; tips.forEach(t=>toByT[t]=0);
  rows.forEach(r=>{if(r.resultado!=='V'&&r.tipster)toByT[r.tipster]+=r.stake;});
  const top=tips.slice().sort((a,b)=>toByT[b]-toByT[a]).slice(0,8);
  const months=[...new Set(rows.map(r=>r.data.slice(0,7)))].sort();
  const series={}, present={};
  top.forEach(t=>{const m={};months.forEach(ym=>m[ym]=0);series[t]=m;present[t]=new Set();});
  rows.forEach(r=>{if(series[r.tipster]&&(r.data.slice(0,7) in series[r.tipster])){series[r.tipster][r.data.slice(0,7)]+=r.lucro;present[r.tipster].add(r.data.slice(0,7));}});
  function pearson(a,b){
    const common=months.filter(m=>present[a].has(m)&&present[b].has(m));
    if(common.length<3)return null;
    const x=common.map(m=>series[a][m]), y=common.map(m=>series[b][m]), n=x.length;
    const mx=x.reduce((p,q)=>p+q,0)/n, my=y.reduce((p,q)=>p+q,0)/n;
    let sxy=0,sxx=0,syy=0;
    for(let i=0;i<n;i++){const dx=x[i]-mx,dy=y[i]-my;sxy+=dx*dy;sxx+=dx*dx;syy+=dy*dy;}
    if(sxx===0||syy===0)return null;
    return sxy/Math.sqrt(sxx*syy);
  }
  const short=t=>t.length>9?t.slice(0,8)+'…':t;
  const num2=v=>v.toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2});
  const cell=v=>{
    if(v===null)return`<td style="background:var(--field);text-align:center;padding:6px 8px;color:var(--ink-mute);font-size:11px">—</td>`;
    const a=0.12+Math.min(1,Math.abs(v))*0.78;
    const bg=v>0?`rgba(200,40,60,${a})`:`rgba(0,160,100,${a})`;
    const tc=a>0.5?'#fff':(v>0?'var(--neg)':'var(--pos)');
    return`<td style="background:${bg};color:${tc};text-align:center;padding:6px 8px;font-size:11px;font-weight:600">${num2(v)}</td>`;
  };
  const thBase='padding:6px 8px;font-size:9px;text-transform:uppercase;letter-spacing:.06em;color:var(--ink-mute);white-space:nowrap;';
  const head=`<tr><th style="${thBase}background:var(--field);text-align:left;position:sticky;left:0;z-index:2;min-width:120px"></th>${top.map(t=>`<th title="${t}" style="${thBase}text-align:center;min-width:74px">${short(t)}</th>`).join('')}</tr>`;
  const body=top.map(a=>`<tr>
    <td style="${thBase}background:var(--field);text-align:left;color:var(--ink);font-weight:700;position:sticky;left:0;z-index:1;font-size:11px">${short(a)}</td>
    ${top.map(b=>a===b?`<td style="background:var(--elevated);text-align:center;padding:6px 8px;color:var(--ink-mute);font-size:11px">—</td>`:cell(pearson(a,b))).join('')}
  </tr>`).join('');
  return`<div style="overflow-x:auto"><table style="border-collapse:separate;border-spacing:2px;font-family:'JetBrains Mono',monospace;font-variant-numeric:tabular-nums">
    <thead>${head}</thead><tbody>${body}</tbody></table></div>
    <p style="font-size:10px;color:var(--ink-mute);margin-top:10px;font-family:var(--font-mono);line-height:1.7">
      Correlação do P/L mensal entre os 8 tipsters de maior turnover (meses com atividade em ambos; mín. 3). ·
      <b style="color:var(--pos)">Verde</b> = sobem e caem em direções opostas (carteira diversificada). ·
      <b style="color:var(--neg)">Vermelho</b> = vencem e perdem juntos (risco concentrado).</p>`;
}

// ── Gráfico Resultado Geral (acumulado + diário) ─────────────────────────────
function _resChartData(rows){
  const byDay={};
  rows.forEach(r=>{const d=r.data.slice(0,10);byDay[d]=(byDay[d]||0)+r.lucro;});
  const days=Object.keys(byDay).sort();
  let cum=0; const labels=[],cumv=[],dailyv=[];
  days.forEach(d=>{const pl=byDay[d];cum+=pl;const[,m,dd]=d.split('-');labels.push(dd+'/'+m);cumv.push(parseFloat(cum.toFixed(2)));dailyv.push(parseFloat(pl.toFixed(2)));});
  return{labels,cumv,dailyv};
}

// ── Render principal ─────────────────────────────────────────────────────────
function renderResultados(){
  const cont=document.getElementById('resultadosContent'); if(!cont)return;
  if(!DADOS||!DADOS.length){cont.innerHTML='<p style="color:var(--ink-mute);padding:2rem">Carregando dados…</p>';return;}
  const rows=filtrarPagina('resultados');
  if(!rows.length){cont.innerHTML=mkEmpty('Sem apostas no período selecionado');return;}
  const nTip=[...new Set(rows.map(r=>r.tipster).filter(Boolean))].length;

  // KPIs
  const kpiHTML=mkKpiGrid(rows,{plLabel:'P/L Total',contextLabel:'Tipsters',contextVal:nTip,contextSub:nTip+' tipsters ativos'});

  // Matriz (hero) — seletor de granularidade + navegação no cabeçalho
  const mode=window._resMatMode;
  const seg=`<div class="tcard-seg" style="margin-left:auto">
    <button class="${mode==='ano'?'active':''}" onclick="setResMatMode('ano')">Ano</button>
    <button class="${mode==='mes'?'active':''}" onclick="setResMatMode('mes')">Mês</button>
    <button class="${mode==='semana'?'active':''}" onclick="setResMatMode('semana')">Semana</button>
  </div>`;
  const mat=_resMatrixSection(rows);
  const navWrap=mat.nav?`<div style="display:flex;align-items:center;gap:6px;margin-left:12px">${mat.nav}</div>`:'';
  const matrixCard=mkCard('res_matrix','Matriz — P/L por Período',mat.html,seg+navWrap);

  // Gráfico
  const chartCard=mkCard('res_chart','Resultado Geral','<div class="chart-wrap" style="height:280px"><canvas id="chartResGeral" role="img" aria-label="P/L acumulado"></canvas></div>','<span style="margin-left:auto;font-family:JetBrains Mono,monospace;font-size:9px;text-transform:uppercase;letter-spacing:.18em;color:var(--ink-soft);opacity:.7">P/L diário · evolução acumulada</span>');

  // Calendário
  if(!window._resCalMonth||!rows.some(r=>r.data.slice(0,7)===window._resCalMonth)){
    const ms=[...new Set(rows.map(r=>r.data.slice(0,7)))].sort().reverse();
    window._resCalMonth=ms[0]||'';
  }
  window._calHeatCb=null;
  const calCard=mkCard('res_cal','Calendário — Resultados Diários',
    `<div id="resCalWrap">${mkCalendarHeatmap(window._resCalMonth,rows,{showNav:true,
      onPrev:"resCalNav(-1)",onNext:"resCalNav(1)",onSelect:"resCalSel(this.value)"})}</div>`);

  // Análises novas
  const weekdayCard=mkCard('res_weekday','Desempenho por Dia da Semana',_resWeekdayHTML(rows));
  const contribCard=mkCard('res_contrib','Contribuição & Consistência por Tipster',_resContribHTML(rows));
  const corrCard=mkCard('res_corr','Correlação entre Tipsters',_resCorrHTML(rows));

  cont.innerHTML=kpiHTML+matrixCard+chartCard+calCard+weekdayCard+contribCard+corrCard;

  setTimeout(()=>{
    makeSortable('tblResWeekday',[1,2,3,4,5]);
    const cd=_resChartData(rows);
    mkChart('chartResGeral',{type:'bar',data:{labels:cd.labels,datasets:[
      {type:'line',data:cd.cumv,borderColor:'#2E8BFF',backgroundColor:'rgba(46,139,255,.10)',tension:.35,pointRadius:0,fill:true,borderWidth:2,yAxisID:'y1',label:'Acumulado'},
      {type:'bar',data:cd.dailyv,backgroundColor:cd.dailyv.map(v=>v>=0?'rgba(43,192,126,.6)':'rgba(229,82,75,.6)'),borderRadius:2,yAxisID:'y',label:'Diário'}
    ]},options:{responsive:true,maintainAspectRatio:false,
      plugins:{legend:{display:true,position:'bottom',labels:{color:isDark()?'#AEB7C2':'#666E7A',font:{size:11},boxWidth:10,padding:12}},
        tooltip:{callbacks:{label:ctx=>(ctx.dataset.label||'')+': '+_txtPL(ctx.raw)}}},
      scales:{
        x:{ticks:{color:tc(),font:{size:10},maxTicksLimit:16},grid:{display:false},border:{display:false}},
        y:{ticks:{color:tc(),font:{size:10},callback:v=>fmtK(v)},grid:{color:gc()},border:{display:false},position:'left'},
        y1:{ticks:{color:tc(),font:{size:10},callback:v=>fmtK(v)},grid:{display:false},border:{display:false},position:'right'}
      }}});
  },60);
}

// ── Callbacks de navegação ───────────────────────────────────────────────────
window.setResMatMode=function(m){window._resMatMode=m;renderResultados();};
window.resMatNav=function(dir){
  const rows=filtrarPagina('resultados');
  if(window._resMatMode==='mes'){
    const months=[...new Set(rows.map(r=>r.data.slice(0,7)))].sort().reverse();
    let i=months.indexOf(window._resMatMonth); if(i<0)i=0;
    const ni=i-dir; if(ni>=0&&ni<months.length){window._resMatMonth=months[ni];renderResultados();}
  } else if(window._resMatMode==='semana'){
    const allDays=[...new Set(rows.map(r=>r.data.slice(0,10)))].sort();
    const weeks=[...new Set(allDays.map(d=>_resMonday(d)))].sort().reverse();
    let i=weeks.indexOf(window._resMatWeek); if(i<0)i=0;
    const ni=i-dir; if(ni>=0&&ni<weeks.length){window._resMatWeek=weeks[ni];renderResultados();}
  }
};
window.resCalNav=function(dir){
  const rows=filtrarPagina('resultados');
  const ms=[...new Set(rows.map(r=>r.data.slice(0,7)))].sort().reverse();
  let i=ms.indexOf(window._resCalMonth); if(i<0)i=0;
  const ni=i-dir; if(ni>=0&&ni<ms.length){window._resCalMonth=ms[ni];renderResultados();}
};
window.resCalSel=function(v){window._resCalMonth=v;renderResultados();};
