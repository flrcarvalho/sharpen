// Filter state
const FS={};
function gfs(p){if(!FS[p])FS[p]={df:'',dt:'',qd:0,qt:'',dayOff:0,monthOff:0};return FS[p];}

// Cache de filtro (limpo no início de cada renderPage) + debounce
let _filterCache={};
let _renderDebounceT;
let _dateDebouncT;
function _renderPageDebounced(p){clearTimeout(_renderDebounceT);_renderDebounceT=setTimeout(()=>renderPage(p),120);}
// Debounce longo para inputs de data: aguarda o usuário terminar dia+mês+ano antes de renderizar
function _renderPageDebouncedDate(p){clearTimeout(_dateDebouncT);clearTimeout(_renderDebounceT);_dateDebouncT=setTimeout(()=>renderPage(p),700);}

// Date helpers for WTD/MTD/YTD/Hoje
// SEMPRE fuso local (nunca toISOString/UTC): à noite no Brasil (UTC−3) o relógio
// UTC já virou o dia seguinte, e "Hoje" resolveria para amanhã. _ymd() formata a
// data no fuso do usuário, igual ao hojeISO() do index.html.
function _ymd(d){return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');}
function _today(){return _ymd(new Date());}
function _wtdStart(){const d=new Date(),day=d.getDay()||7;d.setDate(d.getDate()-(day-1));return _ymd(d);}
function _mtdStart(){const d=new Date();return _ymd(new Date(d.getFullYear(),d.getMonth(),1));}
function _ytdStart(){return new Date().getFullYear()+'-01-01';}

function _dayNavLabel(off){
  if(off===0)return'Hoje';
  const d=new Date();d.setDate(d.getDate()+off);
  return(d.getDate()+'').padStart(2,'0')+'/'+((d.getMonth()+1)+'').padStart(2,'0')+'/'+d.getFullYear();
}

function navDay(p,delta){
  const st=gfs(p);
  const newOff=Math.min(0,st.dayOff+delta);
  st.dayOff=newOff;st.qt='hoje';st.qd=0;
  const d=new Date();d.setDate(d.getDate()+newOff);
  const iso=_ymd(d);
  st.df=iso;st.dt=iso;
  const fEl=document.getElementById('df_f_'+p);if(fEl)fEl.value=iso;
  const tEl=document.getElementById('df_t_'+p);if(tEl)tEl.value=iso;
  rqb(p);_renderPageDebounced(p);
}

const _MESES_NAV=['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez'];
function _monthNavLabel(off){
  if(off===0)return'Este mês';
  const d=new Date();d.setDate(1);d.setMonth(d.getMonth()+off);
  return _MESES_NAV[d.getMonth()]+'/'+d.getFullYear();
}

function navMonth(p,delta){
  const st=gfs(p);
  const newOff=Math.min(0,st.monthOff+delta);
  st.monthOff=newOff;st.qt='mtd';st.qd=0;
  const d=new Date();d.setDate(1);d.setMonth(d.getMonth()+newOff);
  const firstDay=_ymd(new Date(d.getFullYear(),d.getMonth(),1));
  const lastDay=newOff===0?_today():_ymd(new Date(d.getFullYear(),d.getMonth()+1,0));
  st.df=firstDay;st.dt=lastDay;
  const fEl=document.getElementById('df_f_'+p);if(fEl)fEl.value=firstDay;
  const tEl=document.getElementById('df_t_'+p);if(tEl)tEl.value=lastDay;
  rqb(p);_renderPageDebounced(p);
}

function filtrarPagina(p){
  if(_filterCache[p])return _filterCache[p];
  const st=gfs(p);
  const sp=msGet('sp_'+p),ca=msGet('ca_'+p),ti=msGet('ti_'+p),op=msGet('op_'+p);
  const lim=st.qd>0?_ymd(new Date(Date.now()-st.qd*864e5)):'';
  const res=DADOS.filter(r=>{
    if(st.df&&r.data<st.df)return false;
    if(st.dt&&r.data>st.dt)return false;
    if(lim&&r.data<lim)return false;
    if(sp.size>0&&!sp.has(r.esporte))return false;
    if(ca.size>0&&!ca.has(r.casa))return false;
    if(ti.size>0&&!ti.has(r.tipster))return false;
    if(op.size>0&&!op.has(r.operador))return false;
    return true;
  });
  _filterCache[p]=res;
  return res;
}

// Apostas abertas que passam pelos MESMOS filtros da página (data/esporte/casa/
// tipster/operador). Espelha filtrarPagina, mas sobre DADOS_ABERTAS. Sem cache:
// são poucas (planilhadas antes do encerramento) e não valem a invalidção.
function filtrarAbertas(p){
  if(!DADOS_ABERTAS.length)return [];
  const st=gfs(p);
  const sp=msGet('sp_'+p),ca=msGet('ca_'+p),ti=msGet('ti_'+p),op=msGet('op_'+p);
  const lim=st.qd>0?_ymd(new Date(Date.now()-st.qd*864e5)):'';
  return DADOS_ABERTAS.filter(r=>{
    if(st.df&&r.data<st.df)return false;
    if(st.dt&&r.data>st.dt)return false;
    if(lim&&r.data<lim)return false;
    if(sp.size>0&&!sp.has(r.esporte))return false;
    if(ca.size>0&&!ca.has(r.casa))return false;
    if(ti.size>0&&!ti.has(r.tipster))return false;
    if(op.size>0&&!op.has(r.operador))return false;
    return true;
  });
}

// Igual a filtrarPagina, mas SEM o corte por data (respeita esporte/casa/tipster/
// operador). Usado pelo ROI Mensal, que mostra todos os meses e só DESTACA o mês
// de referência — filtrar por data o reduziria a uma barra só.
function filtrarSemData(p){
  const sp=msGet('sp_'+p),ca=msGet('ca_'+p),ti=msGet('ti_'+p),op=msGet('op_'+p);
  return DADOS.filter(r=>{
    if(sp.size>0&&!sp.has(r.esporte))return false;
    if(ca.size>0&&!ca.has(r.casa))return false;
    if(ti.size>0&&!ti.has(r.tipster))return false;
    if(op.size>0&&!op.has(r.operador))return false;
    return true;
  });
}

// Chave "AAAA-MM" (mês 0-based, igual às chaves do ROI Mensal) do mês de referência
// do período selecionado: fim do intervalo (st.dt), ou hoje p/ janelas 7/30/90d,
// ou null p/ "Tudo" (sem destaque).
function _refMonthKey(p){
  const st=gfs(p);
  const ref=st.dt||(st.qd>0?_today():'');
  if(!ref)return null;
  const d=new Date(ref+'T12:00:00');
  return `${d.getFullYear()}-${String(d.getMonth()).padStart(2,'0')}`;
}

// Intervalo de datas selecionado (ISO AAAA-MM-DD) do período: {from,to} ou null p/
// "Tudo". Usado p/ o calendário contornar de azul os dias dentro do período.
function _selRange(p){
  const st=gfs(p);
  if(st.df||st.dt)return{from:st.df||'0000-01-01',to:st.dt||'9999-12-31'};
  if(st.qd>0)return{from:_ymd(new Date(Date.now()-st.qd*864e5)),to:_today()};
  return null;
}

function setDateF(p,type,val){const st=gfs(p);st.qd=0;st.qt='';st.dayOff=0;st.monthOff=0;if(type==='f')st.df=val;else st.dt=val;rqb(p);_renderPageDebouncedDate(p);}

function setQuick(p,days){
  const st=gfs(p);st.qd=days;st.qt='';st.dayOff=0;st.monthOff=0;st.df='';st.dt='';
  ['df_f_'+p,'df_t_'+p].forEach(id=>{const el=document.getElementById(id);if(el)el.value='';});
  rqb(p);_renderPageDebounced(p);
}

function setQuickType(p,qt){
  const st=gfs(p);
  st.qt=qt;st.qd=0;st.dayOff=0;st.monthOff=0;
  const today=_today();
  const f=qt==='hoje'?today:qt==='wtd'?_wtdStart():qt==='mtd'?_mtdStart():qt==='ytd'?_ytdStart():'';
  st.df=f;st.dt=today;
  const fEl=document.getElementById('df_f_'+p);if(fEl)fEl.value=f;
  const tEl=document.getElementById('df_t_'+p);if(tEl)tEl.value=today;
  rqb(p);_renderPageDebounced(p);
}

function clearDate(p){const st=gfs(p);st.qd=0;st.qt='';st.dayOff=0;st.monthOff=0;st.df='';st.dt='';['df_f_'+p,'df_t_'+p].forEach(id=>{const el=document.getElementById(id);if(el)el.value='';});rqb(p);_renderPageDebounced(p);}

function rqb(p){
  const st=gfs(p);
  document.querySelectorAll('#page-'+p+' .qbtn').forEach(b=>{
    let active=false;
    if(b.dataset.all)active=(st.qd===0&&!st.qt&&!st.df&&!st.dt);
    else if(b.dataset.days)active=(st.qd===parseInt(b.dataset.days));
    else if(b.dataset.qt)active=(st.qt===b.dataset.qt);
    b.classList.toggle('active',active);
  });
  const nav=document.getElementById('dayNav_'+p);
  if(nav){
    const isHoje=st.qt==='hoje';
    nav.style.display=isHoje?'flex':'none';
    const lbl=document.getElementById('dayNavLbl_'+p);
    if(lbl)lbl.textContent=_dayNavLabel(st.dayOff||0);
    const fwd=document.getElementById('dayNavFwd_'+p);
    if(fwd)fwd.disabled=(st.dayOff||0)>=0;
  }
  const mnav=document.getElementById('monthNav_'+p);
  if(mnav){
    const isMtd=st.qt==='mtd';
    mnav.style.display=isMtd?'flex':'none';
    const mlbl=document.getElementById('monthNavLbl_'+p);
    if(mlbl)mlbl.textContent=_monthNavLabel(st.monthOff||0);
    const mfwd=document.getElementById('monthNavFwd_'+p);
    if(mfwd)mfwd.disabled=(st.monthOff||0)>=0;
  }
}

// Multiselect
const MSS={};
function msGet(id){return MSS[id]||new Set();}
function msInit(id){MSS[id]=new Set();}
function msToggle(id,val){if(!MSS[id])MSS[id]=new Set();if(val==='__all__'){MSS[id]=new Set();return;}if(MSS[id].has(val))MSS[id].delete(val);else MSS[id].add(val);}

function buildMS(id,items,ph,page,cb,withIcons=false){
  if(!MSS[id])MSS[id]=new Set();
  const hs=MSS[id]?.size>0;
  const optItems=items.map(it=>{
    const ico=withIcons?casaImg(it,13):'';
    const isSport=id.startsWith('sp_');
    const emo=isSport?sportEmoji(it):'';
    // safe: JS-string escaping (\ e ') + HTML-escaping (esc) — vai dentro de onclick="…'…'…"
    const safe=esc(it.replace(/\\/g,'\\\\').replace(/'/g,"\\'"));
    const safeAttr=esc(it);
    return`<div class="ms-opt ${MSS[id]?.has(it)?'sel':''}" data-val="${safeAttr}" onclick="toggleMS('${id}','${safe}','${page}','${cb||''}')"><span class="ms-chk">${MSS[id]?.has(it)?'✓':''}</span><span style="display:inline-flex;align-items:center;gap:2px">${ico}${emo?`<span class="sport-emoji">${emo}</span>`:''}${esc(it)}</span></div>`;
  }).join('');
  const selLbl=hs?(MSS[id].size===1?esc([...MSS[id]][0]):MSS[id].size+' sel.'):ph;
  return`<div class="ms-wrap" id="msw_${id}">
    <div class="ms-btn ${hs?'asel':''}" id="msb_${id}" data-ph="${ph}" data-page="${page}" data-cb="${cb||''}" data-icons="${withIcons?1:0}" onclick="openMS(event,'${id}','${page}','${cb||''}')">
      <span id="msl_${id}">${hs&&withIcons&&MSS[id].size===1?casaImg([...MSS[id]][0],13)+esc([...MSS[id]][0]):selLbl}</span>
      <svg width="10" height="6" viewBox="0 0 10 6"><path d="M1 1l4 4 4-4" stroke="currentColor" stroke-width="1.5" fill="none"/></svg>
    </div>
    <div class="ms-dd" id="msd_${id}">
      <input class="ms-search" style="margin:6px 10px 4px;font-size:11px;padding:4px 8px;background:var(--field);border:1px solid var(--line);color:var(--ink-soft);border-radius:4px;font-family:'JetBrains Mono',monospace;outline:none;flex-shrink:0" type="text" placeholder="Buscar..." oninput="filterMSOpts('${id}')" onclick="event.stopPropagation()">
      <div class="ms-opts-scroll" id="ms-opts-${id}">
        <div class="ms-opt ${!hs?'sel':''}" onclick="toggleMS('${id}','__all__','${page}','${cb||''}')"><span class="ms-chk">${!hs?'✓':''}</span><span>Todos</span></div>
        ${optItems}
      </div>
      <div class="ms-footer">
        <span class="ms-cl" onclick="toggleMS('${id}','__all__','${page}','${cb||''}');event.stopPropagation()">Limpar</span>
        <button class="ms-ok" onclick="applyMS('${id}','${page}','${cb||''}');event.stopPropagation()">OK</button>
      </div>
    </div>
  </div>`;
}

function filterMSOpts(id){
  const inp=document.querySelector(`#msd_${id} .ms-search`);
  if(!inp)return;
  const q=inp.value.toLowerCase();
  const optsWrap=document.getElementById('ms-opts-'+id);
  if(!optsWrap)return;
  optsWrap.querySelectorAll('.ms-opt').forEach((o,i)=>{
    if(i===0){o.style.display='';return;}
    const v=o.querySelector('span:last-child')?.textContent||'';
    o.style.display=v.toLowerCase().includes(q)?'':'none';
  });
}

function openMS(e,id,page,cb){
  e.stopPropagation();
  const btn=document.getElementById('msb_'+id),drop=document.getElementById('msd_'+id);
  if(!drop)return;
  const isOpen=drop.classList.contains('open');
  document.querySelectorAll('.ms-dd.open').forEach(d=>d.classList.remove('open'));
  if(!isOpen){
    const rect=btn.getBoundingClientRect();
    const dropdownHeight=300;
    const dropW=Math.max(200,btn.offsetWidth);
    // Abrir para cima se não houver espaço abaixo
    const spaceBelow=window.innerHeight-rect.bottom;
    if(spaceBelow<dropdownHeight){
      drop.style.top='auto';
      drop.style.bottom='100%';
    }else{
      drop.style.top='100%';
      drop.style.bottom='auto';
    }
    // Evitar overflow na borda direita da viewport
    drop.style.left='0';
    drop.style.right='auto';
    const rightOverflow=rect.left+dropW-window.innerWidth;
    if(rightOverflow>0){
      drop.style.left=`${-rightOverflow-8}px`;
    }
    drop.style.minWidth=dropW+'px';
    drop.classList.add('open');
    setTimeout(()=>{const s=drop.querySelector('.ms-search');if(s){s.value='';filterMSOpts(id);s.focus();}},50);
  }
}

document.addEventListener('click',(e)=>{if(!e.target.closest('.ms-dd')&&!e.target.closest('.ms-btn'))document.querySelectorAll('.ms-dd.open').forEach(d=>d.classList.remove('open'));});

function toggleMS(id,val,page,cb){
  msToggle(id,val);
  refreshMS(id);
  const optsWrap=document.getElementById('ms-opts-'+id);
  if(optsWrap){
    if(val==='__all__'){
      optsWrap.querySelectorAll('.ms-opt').forEach((o,i)=>{
        o.classList.toggle('sel',i===0);
        const chk=o.querySelector('.ms-chk');if(chk)chk.textContent=i===0?'✓':'';
      });
    } else {
      const hs=MSS[id]?.size>0;
      const todos=optsWrap.querySelector('.ms-opt:first-child');
      if(todos){todos.classList.toggle('sel',!hs);const chk=todos.querySelector('.ms-chk');if(chk)chk.textContent=!hs?'✓':'';}
      optsWrap.querySelectorAll('.ms-opt').forEach(o=>{
        const v=o.dataset.val;if(v===undefined)return;
        const sel=MSS[id]?.has(v);
        o.classList.toggle('sel',sel);
        const chk=o.querySelector('.ms-chk');if(chk)chk.textContent=sel?'✓':'';
      });
    }
  }
}

function applyMS(id,page,cb){
  document.querySelectorAll('.ms-dd.open').forEach(d=>d.classList.remove('open'));
  if(cb&&window[cb])window[cb](page);else _renderPageDebounced(page);
}

function clickMS(id,val,page,cb){msToggle(id,val);refreshMS(id);if(cb&&window[cb])window[cb](page);else _renderPageDebounced(page);}

function refreshMS(id){
  const hs=MSS[id]?.size>0;
  const btn=document.getElementById('msb_'+id),lbl=document.getElementById('msl_'+id),drop=document.getElementById('msd_'+id);
  const ph=btn?.dataset?.ph||'';
  const withIcons=btn?.dataset?.icons==='1';
  if(lbl){
    if(hs){
      if(withIcons&&MSS[id].size===1){lbl.innerHTML=casaImg([...MSS[id]][0],13)+esc([...MSS[id]][0]);}
      else lbl.textContent=MSS[id].size===1?[...MSS[id]][0]:MSS[id].size+' sel.';
    }else lbl.textContent=ph;
  }
  if(btn)btn.className='ms-btn'+(hs?' asel':'');
  if(drop){
    const optsWrap=document.getElementById('ms-opts-'+id);
    if(optsWrap)optsWrap.querySelectorAll('.ms-opt').forEach((o,i)=>{
      if(i===0){o.className='ms-opt'+(!hs?' sel':'');o.querySelector('.ms-chk').textContent=!hs?'✓':'';return;}
      const v=o.querySelector('span:last-child')?.textContent||o.querySelector('span:last-child')?.innerText||'';
      const s=MSS[id]?.has(v);
      o.className='ms-opt'+(s?' sel':'');
      o.querySelector('.ms-chk').textContent=s?'✓':'';
    });
    const cl=drop.querySelector('.ms-cl');
    if(hs&&!cl){const d=document.createElement('div');d.className='ms-cl';d.textContent='Limpar seleção';d.onclick=()=>{msToggle(id,'__all__');refreshMS(id);renderPage(id.split('_').pop());};drop.appendChild(d);}
    else if(!hs&&cl)cl.remove();
  }
}

function buildFilters(p,sports,casas,tipsters){
  const st=gfs(p);
  const isAll=st.qd===0&&!st.qt&&!st.df&&!st.dt;
  return`<div class="filters">
    <div class="filter-group">
      <div class="filter-label">Período</div>
      <div class="date-row">
        <input type="date" id="df_f_${p}" value="${st.df}" onchange="setDateF('${p}','f',this.value)">
        <span class="date-sep">→</span>
        <input type="date" id="df_t_${p}" value="${st.dt}" onchange="setDateF('${p}','t',this.value)">
      </div>
      <div class="quick-btns">
        <button class="qbtn ${st.qt==='hoje'?'active':''}" data-qt="hoje" onclick="setQuickType('${p}','hoje')">Hoje</button>
        <button class="qbtn ${st.qt==='wtd'?'active':''}" data-qt="wtd" onclick="setQuickType('${p}','wtd')">WTD</button>
        <button class="qbtn ${st.qt==='mtd'?'active':''}" data-qt="mtd" onclick="setQuickType('${p}','mtd')">MTD</button>
        <button class="qbtn ${st.qt==='ytd'?'active':''}" data-qt="ytd" onclick="setQuickType('${p}','ytd')">YTD</button>
        <button class="qbtn ${st.qd===7?'active':''}" data-days="7" onclick="setQuick('${p}',7)">7d</button>
        <button class="qbtn ${st.qd===30?'active':''}" data-days="30" onclick="setQuick('${p}',30)">30d</button>
        <button class="qbtn ${st.qd===90?'active':''}" data-days="90" onclick="setQuick('${p}',90)">90d</button>
        <button class="qbtn ${isAll?'active':''}" data-all="1" onclick="clearDate('${p}')">Tudo</button>
      </div>
      <div class="day-nav" id="dayNav_${p}" style="display:${st.qt==='hoje'?'flex':'none'}">
        <button class="day-nav-arrow" onclick="navDay('${p}',-1)" aria-label="Dia anterior">&#9664;</button>
        <span class="day-nav-label" id="dayNavLbl_${p}">${_dayNavLabel(st.dayOff||0)}</span>
        <button class="day-nav-arrow" id="dayNavFwd_${p}" onclick="navDay('${p}',1)" aria-label="Próximo dia"${(st.dayOff||0)>=0?' disabled':''}>&#9654;</button>
      </div>
      <div class="day-nav" id="monthNav_${p}" style="display:${st.qt==='mtd'?'flex':'none'}">
        <button class="day-nav-arrow" onclick="navMonth('${p}',-1)" aria-label="Mês anterior">&#9664;</button>
        <span class="day-nav-label" id="monthNavLbl_${p}">${_monthNavLabel(st.monthOff||0)}</span>
        <button class="day-nav-arrow" id="monthNavFwd_${p}" onclick="navMonth('${p}',1)" aria-label="Próximo mês"${(st.monthOff||0)>=0?' disabled':''}>&#9654;</button>
      </div>
    </div>
    <div class="filter-group"><div class="filter-label">Esporte</div>${buildMS('sp_'+p,sports,'Todos os esportes',p)}</div>
    <div class="filter-group"><div class="filter-label">Casa</div>${buildMS('ca_'+p,casas,'Todas as casas',p,'',true)}</div>
    ${tipsters?`<div class="filter-group"><div class="filter-label">Tipster</div>${buildMS('ti_'+p,tipsters,'Todos os tipsters',p)}</div>`:''}
    ${(()=>{const ops=[...new Set(DADOS.map(r=>r.operador).filter(Boolean))].sort();return ops.length>1?`<div class="filter-group"><div class="filter-label">Operador</div>${buildMS('op_'+p,ops,'Todos os operadores',p)}</div>`:'';})()}
  </div>`;
}
