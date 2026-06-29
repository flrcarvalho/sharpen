// ── shared.js — Helpers e constantes compartilhados ──────────────────────────

// ── Calendar Heatmap Helper ─────────────────────────────────────────────────
function mkCalendarHeatmap(selMonth, allDados, opts){
  // opts: {showNav, onPrev, onNext, onSelect}  — compact ignorado (design único)
  opts = opts || {};
  const months = [...new Set(allDados.map(r=>r.data.slice(0,7)))].sort().reverse();
  if(!months.length) return mkEmpty('Sem dados de apostas');
  const cur = selMonth || months[0];
  const [yr, mo] = cur.split('-');
  const moLabel = MESES[parseInt(mo)-1] + ' ' + yr;

  // Build day→{pl,n,turnover,wins,hw,losses,hl,voids} map
  const dayMap = {};
  allDados.filter(r=>r.data.slice(0,7)===cur).forEach(r=>{
    const d = r.data.slice(0,10);
    if(!dayMap[d]) dayMap[d]={pl:0,n:0,turnover:0,wins:0,hw:0,losses:0,hl:0,voids:0};
    const dm = dayMap[d];
    dm.pl += r.lucro;
    dm.n++;
    if(r.resultado!=='V') dm.turnover += (r.stake||0);   // turnover exclui Void
    const res = r.resultado;
    if(res==='W') dm.wins++;
    else if(res==='HW') dm.hw++;
    else if(res==='L') dm.losses++;
    else if(res==='HL') dm.hl++;
    else if(res==='V') dm.voids++;
  });

  // Month stats
  const mRows = allDados.filter(r=>r.data.slice(0,7)===cur);
  const mPL = mRows.reduce((a,r)=>a+r.lucro,0);
  const mN = mRows.length;
  const mTurnover = calcTurnover(mRows);  // exclui Void (stake devolvida)
  const mROI = mTurnover>0 ? mPL/mTurnover*100 : 0;
  const mWR = calcWR(mRows);            // canônico: vitórias / encerradas (exclui V)
  const mAvgOdd = calcAvgOdd(mRows);     // ponderada pela stake, filtra odd>0 && stake>0
  const mSettled = mRows.filter(r=>r.resultado!=='V').length;
  const mAvgStake = mSettled>0 ? mTurnover/mSettled : 0;  // turnover ÷ encerradas

  // Heatmap: opacidade proporcional ao |P/L|, escala 0.07→0.49
  const maxAbs = Math.max(1, ...Object.values(dayMap).map(d=>Math.abs(d.pl)));
  const heatBg = pl => {
    if(!pl) return '';
    const t = Math.min(Math.abs(pl)/maxAbs, 1);
    const op = (0.07 + t*0.42).toFixed(3);
    const rgb = pl>0 ? '43,192,126' : '229,82,75';
    return `background:rgba(${rgb},${op})`;
  };

  // Calendário: alinhamento começa na segunda
  const firstDay = new Date(parseInt(yr), parseInt(mo)-1, 1);
  const daysInMonth = new Date(parseInt(yr), parseInt(mo), 0).getDate();
  const startDow = (firstDay.getDay() + 6) % 7; // 0=Seg … 6=Dom
  const today = new Date();

  // Cabeçalho dias da semana
  const WK_LABELS = ['S','T','Q','Q','S','S','D'];
  const wkHeader = WK_LABELS.map((l,i)=>`<span${i>=5?' class="we"':''}>${l}</span>`).join('');

  // Células
  let cells = '';
  for(let i=0;i<startDow;i++) cells+=`<div class="cal__cell offset"></div>`;
  for(let d=1;d<=daysInMonth;d++){
    const key = `${yr}-${mo}-${String(d).padStart(2,'0')}`;
    const dm = dayMap[key];
    const isToday = today.getFullYear()===parseInt(yr) && today.getMonth()===parseInt(mo)-1 && today.getDate()===d;
    const colIdx = (startDow + d - 1) % 7;
    const isWE = colIdx >= 5;
    let cls = 'cal__cell';
    if(isWE) cls += ' we';
    if(isToday) cls += ' today';
    if(dm) {
      cls += ' has';
      const plSign = dm.pl>0?'+':dm.pl<0?'−':'';
      const plCls  = dm.pl>0?'pos':dm.pl<0?'neg':'';
      const plAbs  = Math.abs(dm.pl);
      const plFmt  = Math.round(plAbs).toLocaleString('pt-BR');
      cells += `<div class="${cls}" style="${heatBg(dm.pl)}"
        data-date="${key}" data-pl="${dm.pl.toFixed(2)}" data-n="${dm.n}"
        data-turnover="${dm.turnover.toFixed(2)}" data-wins="${dm.wins}"
        data-hw="${dm.hw}" data-losses="${dm.losses}" data-hl="${dm.hl}" data-voids="${dm.voids}"
        onclick="if(window._calHeatCb)window._calHeatCb('${key}')">
        <div class="top">
          <span class="dn">${d}</span>${isToday?'<span class="hoje">hoje</span>':''}
        </div>
        <div class="pl ${plCls}"><span class="cur">${plSign}R$</span>${plFmt}</div>
      </div>`;
    } else {
      cls += ' empty';
      cells += `<div class="${cls}">
        <div class="top"><span class="dn">${d}</span>${isToday?'<span class="hoje">hoje</span>':''}</div>
        ${isToday?'<div class="pl" style="color:var(--ink-mute)">—</div>':''}
      </div>`;
    }
  }

  // Toolbar
  const idxCur = months.indexOf(cur);
  let toolbarHTML;
  if(opts.showNav){
    const selectOpts = months.map(m=>{
      const[y2,m2]=m.split('-');
      return `<option value="${m}"${m===cur?' selected':''}>${MESES[parseInt(m2)-1]} ${y2}</option>`;
    }).join('');
    toolbarHTML = `<div class="cal__bar">
      <button class="cal__nav" onclick="${opts.onPrev||''}" aria-label="Mês anterior"${idxCur>=months.length-1?' disabled':''}>‹</button>
      <div class="cal__month">
        ${moLabel}<span class="caret">▾</span>
        <select onchange="${opts.onSelect||''}" style="position:absolute;inset:0;opacity:0;cursor:pointer;width:100%;height:100%">${selectOpts}</select>
      </div>
      <button class="cal__nav" onclick="${opts.onNext||''}" aria-label="Próximo mês"${idxCur<=0?' disabled':''}>›</button>
    </div>`;
  } else {
    toolbarHTML = `<div class="cal__bar"><div class="cal__month" style="pointer-events:none">${moLabel}</div></div>`;
  }

  // Hero P/L
  const heroSign = mPL>0?'+':mPL<0?'−':'';
  const heroCls  = mPL>0?'pos':mPL<0?'neg':'';
  const heroAbs  = Math.abs(Math.round(mPL)).toLocaleString('pt-BR');
  const heroHTML = `<div class="cal__hero">
    <div class="k"><span class="kpi-pipe"></span> P/L DO MÊS</div>
    <div class="v ${heroCls}"><span class="cur">${heroSign}R$</span>${heroAbs}</div>
    <div class="cal__sub">${mN} apostas</div>
  </div>`;

  // 5 KPI cards
  const roiSign = mROI>0?'+':mROI<0?'−':'';
  const roiCls  = mROI>=0?'pos':'neg';
  const roiFmt  = Math.abs(mROI).toFixed(2).replace('.',',')+'%';
  const wrFill  = Math.min(100,Math.max(0,mWR)).toFixed(1);
  const kpisHTML = mN>0 ? `<div class="cal__kpis">
    <div class="cal__kpi">
      <div class="k"><span class="kpi-pipe"></span> WIN RATE</div>
      <div class="v neu">${mWR.toFixed(1).replace('.',',')}%</div>
      <div class="cal__wr">
        <div class="track"><div class="fill" style="width:${wrFill}%"></div></div>
      </div>
      <div class="cal__sub">taxa de acerto</div>
    </div>
    <div class="cal__kpi">
      <div class="k"><span class="kpi-pipe"></span> Turnover</div>
      <div class="v"><span class="cur">R$</span>${Math.round(mTurnover).toLocaleString('pt-BR')}</div>
      <div class="cal__sub">no mês</div>
    </div>
    <div class="cal__kpi">
      <div class="k"><span class="kpi-pipe"></span> ROI</div>
      <div class="v ${roiCls}">${roiSign}${roiFmt}</div>
      <div class="cal__sub">Σ(P/L)/Σ(turnover)</div>
    </div>
    <div class="cal__kpi">
      <div class="k"><span class="kpi-pipe"></span> Odd Média</div>
      <div class="v">${mAvgOdd>0?fmtOdd(mAvgOdd):'—'}</div>
      <div class="cal__sub">ponderada</div>
    </div>
    <div class="cal__kpi">
      <div class="k"><span class="kpi-pipe"></span> Stake Média</div>
      <div class="v"><span class="cur">R$</span>${mAvgStake>0?Math.round(mAvgStake).toLocaleString('pt-BR'):'—'}</div>
      <div class="cal__sub">por aposta</div>
    </div>
  </div>` : '';

  return `<div style="display:flex;flex-direction:column;gap:0">
    ${toolbarHTML}
    ${mN>0?`<div class="cal__sum">${heroHTML}${kpisHTML}</div>`:''}
    <div class="cal__wk">${wkHeader}</div>
    <div class="cal__grid">${cells}</div>
  </div>`;
}

// ── Shared KPI grid builder (2 rows × 4) ────────────────────────────────────
function mkKpiGrid(rows,{plLabel,contextLabel,contextVal,contextSub}){
  const pl=rows.reduce((a,r)=>a+r.lucro,0);
  const stake=calcTurnover(rows);   // turnover exclui Void
  const roi=stake>0?(pl/stake*100):0;
  const n=rows.length;
  const W=rows.filter(r=>r.resultado==='W').length;
  const HW=rows.filter(r=>r.resultado==='HW').length;
  const L=rows.filter(r=>r.resultado==='L').length;
  const HL=rows.filter(r=>r.resultado==='HL').length;
  const V=rows.filter(r=>r.resultado==='V').length;
  const settled=rows.filter(r=>r.resultado!=='V').length;
  const wr=calcWR(rows);
  const avgOdd=calcAvgOdd(rows);
  const avgStake=settled>0?stake/settled:0;   // turnover ÷ encerradas (exclui Void)
  const betsBreak=[W?`<span class="res-w">W:${W}</span>`:'',HW?`<span class="res-hw">HW:${HW}</span>`:'',L?`<span class="res-l">L:${L}</span>`:'',HL?`<span class="res-hl">HL:${HL}</span>`:'',V?`<span class="res-v">V:${V}</span>`:''].filter(Boolean).join(' ');
  const mkK=(l,v,c,s,subFlex,bar)=>`<div class="kpi"><div class="kpi-label"><span class="kpi-pipe"></span> ${l}</div><div class="kpi-val ${c}">${v}</div>${bar!==undefined?`<div class="wrc"><div class="t"><div class="f" style="width:${Math.min(100,Math.max(0,bar)).toFixed(1)}%"></div></div></div>`:''}<div class="kpi-sub"${subFlex?' style="display:flex;flex-wrap:wrap;gap:2px 5px"':''}>${s}</div></div>`;
  const row1=[
    mkK(plLabel,fmtPL(pl),pl>=0?'pos':'neg','Turnover: '+fmtR(stake)),
    mkK('Turnover',fmtR(stake),'neu',n+' apostas'),
    mkK('ROI',fmtPct(roi,2),roi>=0?'pos':'neg',(settled)+' encerradas'),
    mkK('Apostas',n.toLocaleString('pt-BR'),'neu',betsBreak,true),
  ].join('');
  const row2=[
    mkK('Win Rate',fmtPct(wr,1,false),'neu',settled+' encerradas',false,wr),
    mkK('Odd Média',fmtOdd(avgOdd),'neu','ponderada'),
    mkK('Stake Média',fmtR(avgStake),'neu','por aposta'),
    mkK(contextLabel,contextVal,'neu',contextSub),
  ].join('');
  return`<div class="kpi-grid" style="margin-bottom:.5rem">${row1}</div><div class="kpi-grid" style="margin-bottom:1.25rem">${row2}</div>`;
}


// Estado vazio reutilizável (ícone neutro + mensagem mono)
function mkEmpty(msg){
  const icon=`<svg class="empty-state-icon" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/></svg>`;
  return `<div class="empty-state">${icon}<p class="empty-state-msg">${msg||'Nenhuma aposta no período'}</p></div>`;
}

// Win Rate bar component (número + barra azul proporcional)
function mkWRC(wr){
  const pct=Math.min(100,Math.max(0,wr));
  return `<div class="wrc"><span class="mono">${fmtPct(wr,1,false)}</span><div class="t"><div class="f" style="width:${pct.toFixed(1)}%"></div></div></div>`;
}

// Sports & Casas
function buildSummaryTable(tableId,label,ents,isCasa=false){
  const rows=ents.map(([nome,d])=>{
    const roi=d.s>0?(d.l/d.s*100):0,wr=d.t>0?(d.w/d.t*100):0;
    const lc=d.l>=0?'color:var(--pos)':'color:var(--neg)';
    const rc=roi>=0?'color:var(--pos)':'color:var(--neg)';
    const label_cell=isCasa?casaCell(nome):sportCell(nome);
    return`<tr><td style="font-weight:600;color:var(--ink)">${label_cell}</td><td class="td-c">${d.n}</td><td class="td-c">${mkWRC(wr)}</td><td class="td-num">${fmtR(d.s)}</td><td class="td-num" style="${lc}">${fmtPL(d.l)}</td><td class="td-c" style="${rc}">${fmtPct(roi,2)}</td></tr>`;
  }).join('');
  const tot=ents.reduce((a,[,d])=>({n:a.n+d.n,w:a.w+d.w,t:a.t+d.t,s:a.s+d.s,l:a.l+d.l}),{n:0,w:0,t:0,s:0,l:0});
  const tRoi=tot.s>0?(tot.l/tot.s*100):0,tWr=tot.t>0?(tot.w/tot.t*100):0;
  const tlc=tot.l>=0?'color:var(--pos)':'color:var(--neg)';const trc=tRoi>=0?'color:var(--pos)':'color:var(--neg)';
  return`<div class="tbl-wrap" style="margin-top:.75rem"><table class="tbl" id="${tableId}"><thead><tr>${mkTh(label,'','l')}${mkTh('Bets','','r')}${mkTh('Win Rate','','r')}${mkTh('Turnover','','r')}${mkTh('P/L','','r')}${mkTh('ROI','','r')}</tr></thead><tbody>${rows}<tr class="total-row"><td>Total</td><td class="td-c">${tot.n}</td><td class="td-c">${mkWRC(tWr)}</td><td class="td-num">${fmtR(tot.s)}</td><td class="td-num" style="${tlc}">${fmtPL(tot.l)}</td><td class="td-c" style="${trc}">${fmtPct(tRoi,2)}</td></tr></tbody></table></div>`;
}


// Apostas — constantes globais (devem vir antes do buildHTML)
// ── Sparkline ────────────────────────────────────────────────────────────────
function mkSparkline(data,w=88,h=28){
  if(!data||data.length<2)return'';
  const min=Math.min(...data),max=Math.max(...data);
  const range=max-min||1;
  const pad=2;
  const pts=data.map((v,i)=>{
    const x=pad+(i/(data.length-1))*(w-pad*2);
    const y=h-pad-(v-min)/range*(h-pad*2);
    return`${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');
  const last=data[data.length-1];
  const lx=parseFloat(pts.split(' ').pop().split(',')[0]);
  const ly=parseFloat(pts.split(' ').pop().split(',')[1]);
  return`<svg viewBox="0 0 ${w} ${h}" width="${w}" height="${h}" xmlns="http://www.w3.org/2000/svg" style="overflow:visible"><polyline points="${pts}" fill="none" stroke="var(--ink-soft,#95A1B0)" stroke-width="1.2" stroke-linejoin="round" stroke-linecap="round"/><circle cx="${lx.toFixed(1)}" cy="${ly.toFixed(1)}" r="2.5" fill="var(--accent,#2E8BFF)" stroke="var(--bg,#0A0D12)" stroke-width="1.5"/></svg>`;
}

// Cabecalho de tabela: rotulo (linha 1) + unidade opcional (linha 2), alinhado por tipo.
// align: 'l' | 'c' | 'r'  (default 'c')
function mkTh(label, unit, align = 'c', extra = '') {
  const alignCls = align === 'r' ? 'th-r' : align === 'l' ? 'th-l' : 'th-c';
  const classAttr = `${alignCls} ${extra}`.trim();
  return `<th class="${classAttr}">`
       + `<span class="th-k">${label}<span class="sort-icon"></span></span>`
       + (unit ? `<span class="th-u">${unit}</span>` : '')
       + `</th>`;
}

const APOSTAS_COLS=['data','esporte','tipster','casa','parceiro','aposta','descricao','stake','odd','resultado','lucro'];
const APOSTAS_HDRS=['Data','Esporte','Tipster','Casa','Parceiro','Aposta','Descrição','Stake','Odd','Resultado','P/L'];
const APOSTAS_NUM=[7,8,10];
const ROW_H=34;
const CARD_H=76; // card height in px for virtual scroll
