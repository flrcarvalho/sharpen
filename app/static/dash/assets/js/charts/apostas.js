// ── apostas.js — Espelho da base com virtual scroll ─────────────────────────────

let apostasFiltered=[], apostasSortCol=0, apostasSortAsc=false;
let apostasColFilters={};
let apostasTabela=[], apostasAbertasFiltered=[]; // tabela = abertas (topo) + encerradas
let _apInlineEditing=false; // enquanto true, o virtual-scroll não re-renderiza (não mata o editor da célula)

const BTBL_ROW_H=68; // altura de linha da tabela de apostas

// Match dos filtros de coluna (texto por coluna) — reusado p/ encerradas e abertas.
function _apostasColMatch(r){
  return APOSTAS_COLS.every((col,i)=>{
    const f=(apostasColFilters[i]||'').toLowerCase().trim();
    if(!f)return true;
    const v=col==='lucro'?r.lucro.toFixed(2):col==='stake'?r.stake.toString():col==='odd'?r.odd.toString():(r[col]||'').toString();
    return v.toLowerCase().includes(f);
  });
}

function renderApostas(){
  const baseRows=filtrarPagina('apostas');
  apostasFiltered=baseRows.filter(_apostasColMatch);
  // Abertas: mesmos filtros da página; NÃO entram nos KPIs (ainda sem resultado).
  // Ficam no topo da tabela, mais recentes primeiro.
  apostasAbertasFiltered=filtrarAbertas('apostas').filter(_apostasColMatch)
    .sort((a,b)=>a.data<b.data?1:a.data>b.data?-1:0);
  apostasFiltered.sort((a,b)=>{
    const col=APOSTAS_COLS[apostasSortCol];
    const av=APOSTAS_NUM.includes(apostasSortCol)?parseFloat(a[col]||0):String(a[col]||'');
    const bv=APOSTAS_NUM.includes(apostasSortCol)?parseFloat(b[col]||0):String(b[col]||'');
    const res=APOSTAS_NUM.includes(apostasSortCol)?(av-bv):av.localeCompare(bv);
    return apostasSortAsc?res:-res;
  });
  apostasTabela=apostasAbertasFiltered.concat(apostasFiltered); // abertas no topo
  // KPI
  const pl=apostasFiltered.reduce((a,r)=>a+r.lucro,0);
  const stake=calcTurnover(apostasFiltered);   // turnover exclui Void
  const roi=stake>0?(pl/stake*100):0;
  const wins=apostasFiltered.filter(r=>['W','HW'].includes(r.resultado)).length;
  const settled=apostasFiltered.filter(r=>r.resultado!=='V').length;
  const wr=wrPctRows(apostasFiltered);
  const avgOddAp=calcAvgOdd(apostasFiltered);
  const avgStakeAp=settled>0?stake/settled:0;   // turnover ÷ encerradas (exclui Void)
  const kpiEl=document.getElementById('apostasKPI');
  if(kpiEl){
    const mkKA=(l,v,c,sub,bar)=>`<div class="kpi" style="height:110px;box-sizing:border-box;display:flex;flex-direction:column;justify-content:flex-start;padding:14px 16px;overflow:hidden"><div class="kpi-label" style="font-size:10px;text-transform:uppercase;letter-spacing:.1em;color:var(--ink-mute);margin-bottom:8px;white-space:nowrap;flex-shrink:0">${l}</div><div class="kpi-val ${c}" style="font-size:22px;line-height:1;font-variant-numeric:tabular-nums;white-space:nowrap;flex-shrink:0">${v}</div>${bar!==undefined?`<div class="wrc"><div class="t"><div class="f" style="width:${Math.min(100,Math.max(0,bar)).toFixed(1)}%"></div></div></div>`:''}<div class="kpi-sub" style="font-size:10px;margin-top:8px;font-family:'JetBrains Mono',monospace;display:flex;flex-wrap:wrap;gap:2px 5px;overflow:hidden">${sub||''}</div></div>`;
    const betsBreak=[
      apostasFiltered.filter(r=>r.resultado==='W').length?`<span class="res-w">W:${apostasFiltered.filter(r=>r.resultado==='W').length}</span>`:'',
      apostasFiltered.filter(r=>r.resultado==='HW').length?`<span class="res-hw">HW:${apostasFiltered.filter(r=>r.resultado==='HW').length}</span>`:'',
      apostasFiltered.filter(r=>r.resultado==='L').length?`<span class="res-l">L:${apostasFiltered.filter(r=>r.resultado==='L').length}</span>`:'',
      apostasFiltered.filter(r=>r.resultado==='HL').length?`<span class="res-hl">HL:${apostasFiltered.filter(r=>r.resultado==='HL').length}</span>`:'',
      apostasFiltered.filter(r=>r.resultado==='V').length?`<span class="res-v">V:${apostasFiltered.filter(r=>r.resultado==='V').length}</span>`:'',
      apostasAbertasFiltered.length?`<span style="color:var(--warn)">Abertas:${apostasAbertasFiltered.length}</span>`:''
    ].filter(Boolean).join('');
    const activeTips=[...new Set(apostasFiltered.map(r=>r.tipster).filter(Boolean))];
    const row1=[
      mkKA('P/L', fmtPL(pl), pl>=0?'pos':'neg', ''),
      mkKA('Turnover', fmtR(stake), 'neu', ''),
      mkKA('ROI', fmtPct(roi,2), roi>=0?'pos':'neg', ''),
      mkKA('Tipsters Ativos', activeTips.length.toString(), 'neu', activeTips.slice(0,3).map(esc).join(', ')+(activeTips.length>3?'...':'')),
    ];
    const row2=[
      mkKA('Apostas', apostasFiltered.length.toLocaleString('pt-BR'), 'neu', betsBreak),
      mkKA('Stake Média', fmtR(avgStakeAp), 'neu', 'por aposta'),
      mkKA('Odd Média', fmtOdd(avgOddAp), 'neu', 'ponderada'),
      mkKA('Win Rate', fmtPct(wr,1,false), 'neu', settled+' encerradas', wr),
    ];
    kpiEl.innerHTML=
      `<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:8px;width:100%">${row1.join('')}</div>`+
      `<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:1rem;width:100%">${row2.join('')}</div>`;
  }
  // Contador e sort arrows no header da tabela
  const counter=document.getElementById('apostasCounter');
  if(counter){
    counter.textContent=`${apostasFiltered.length.toLocaleString('pt-BR')} de ${baseRows.length.toLocaleString('pt-BR')} apostas`
      +(apostasAbertasFiltered.length?` · ${apostasAbertasFiltered.length.toLocaleString('pt-BR')} aberta${apostasAbertasFiltered.length>1?'s':''}`:'');
  }
  document.querySelectorAll('.btbl-th.sortable').forEach(th=>{
    const ci=parseInt(th.dataset.col);
    const arrow=th.querySelector('.sort-arrow');
    th.classList.toggle('sort-active',ci===apostasSortCol);
    if(arrow)arrow.textContent=ci===apostasSortCol?(apostasSortAsc?'↑':'↓'):'↕';
  });
  // Virtual scroll
  renderApostasVirt();
  const _ac=document.getElementById('apostasCont');
  if(_ac){let _raf=null;_ac.onscroll=function(){if(_raf)return;_raf=requestAnimationFrame(()=>{renderApostasVirt();_raf=null;});};}
}

function renderApostasVirt(){
  if(_apInlineEditing)return; // edição inline aberta: não reconstruir a janela (mataria o input)
  const cont=document.getElementById('apostasCont');
  if(!cont)return;
  const rows=apostasTabela;
  const total=rows.length;
  const wrapper=document.getElementById('apostasCardWrap');
  if(!wrapper)return;
  const scrollTop=cont.scrollTop;
  const contH=cont.clientHeight||600;
  const buf=10;
  const startIdx=Math.max(0,Math.floor(scrollTop/BTBL_ROW_H)-buf);
  const endIdx=Math.min(total,Math.ceil((scrollTop+contH)/BTBL_ROW_H)+buf);
  const topPad=startIdx*BTBL_ROW_H;
  const botPad=Math.max(0,(total-endIdx)*BTBL_ROW_H);
  const RES_SHORT={W:'W',HW:'HW',L:'L',HL:'HL',V:'V',ABERTA:'Aberta'};
  const lines=rows.slice(startIdx,endIdx).map(r=>{
    const d=r.data.slice(0,10);
    const [yr,mo,dy]=d.split('-');
    const dateStr=`${dy}/${mo}/${yr}`;
    const resClass=`bet-res-${r.resultado}`;
    const resLabel=RES_SHORT[r.resultado]||r.resultado;
    const parceiro=r.parceiro&&r.parceiro!=='—'?r.parceiro:'';
    // Editável só quando há id (Postgres) E a linha é do dono efetivo. Linha de
    // planilha ao vivo (sem id) ou de operador numa visão consolidada → view-only.
    const editavel=r.id!=null&&r.operador===window.__dono;
    // Duplo-clique edita a célula in loco — só nas linhas editáveis (df() emite o
    // marcador data-field; o handler _apInlineStart valida de novo). `ap-edit` dá o
    // cursor de edição.
    const df=f=>editavel?` data-field="${f}" class="ap-edit"`:'';
    return`<div class="btbl-cols btbl-data-row"${r.id!=null?` data-id="${r.id}"`:''} style="height:${BTBL_ROW_H}px">
      <div class="btbl-cell btbl-date"${editavel?` data-field="data" class="btbl-cell btbl-date ap-edit"`:''}>${dateStr}</div>
      <div class="btbl-cell">
        ${r.aposta?`<div class="btbl-tipo"${df('aposta')}>${esc(r.aposta)}</div>`:''}
        <div class="btbl-desc"${editavel?` data-field="descricao" class="btbl-desc ap-edit"`:''}>${esc(r.descricao||r.aposta||'—')}</div>
      </div>
      <div class="btbl-cell btbl-sport"${editavel?` data-field="esporte" class="btbl-cell btbl-sport ap-edit"`:''}>${mkSpChip(r.esporte)}<span>${esc(r.esporte||'—')}</span></div>
      <div class="btbl-cell btbl-tipster"${editavel?` data-field="tipster" class="btbl-cell btbl-tipster ap-edit"`:''}>${esc(r.tipster||'—')}</div>
      <div class="btbl-cell btbl-casa">
        ${mkHouseChip(r.casa)}
        <div class="btbl-casa-sub">
          <span class="btbl-casa-nome"${df('casa')}>${esc(r.casa||'—')}</span>
          ${parceiro?`<span class="btbl-casa-conta"${df('parceiro')}>${esc(parceiro)}</span>`:''}
        </div>
      </div>
      <div class="btbl-cell btbl-num"${editavel?` data-field="stake" class="btbl-cell btbl-num ap-edit"`:''}>${fmtR(r.stake)}</div>
      <div class="btbl-cell btbl-num"${editavel?` data-field="odd" class="btbl-cell btbl-num ap-edit"`:''}>${fmtOdd(r.odd)}</div>
      <div class="btbl-cell"${editavel?` data-field="resultado" class="btbl-cell ap-edit"`:''} style="display:flex;align-items:center;justify-content:center">
        <span class="bet-res-pill ${resClass}">${resLabel}</span>
      </div>
      <div class="btbl-cell btbl-pl">${r.resultado==='ABERTA'?'<span style="color:var(--ink-mute)">—</span>':fmtPL(r.lucro)}</div>
      <div class="btbl-cell btbl-acts">${editavel
        ? `<button class="act-btn" title="Editar aposta" onclick="abrirEdicaoApostas(${r.id})">✎</button><button class="act-btn del" title="Deletar aposta" onclick="deletarApostas(${r.id})">✕</button>`
        : `<span class="act-btn off" title="Linha da planilha ao vivo ou de um operador — edite na origem">✎</span>`}</div>
    </div>`;
  }).join('');
  wrapper.innerHTML=
    `<div class="virt-spacer" style="height:${topPad}px"></div>`+
    lines+
    `<div class="virt-spacer" style="height:${botPad}px"></div>`;
}

function apostasSort(colIdx){
  if(apostasSortCol===colIdx)apostasSortAsc=!apostasSortAsc;
  else{apostasSortCol=colIdx;apostasSortAsc=false;}
  renderApostas();
}
function apostasFilter(colIdx,val){apostasColFilters[colIdx]=val;renderApostas();}
function clearApostasFilters(){
  apostasColFilters={};
  document.querySelectorAll('.acf').forEach(el=>el.value='');
  renderApostas();
}

// ── Editar / deletar aposta (modal) ─────────────────────────────────────────
// Reusa os endpoints do extrator: PATCH e DELETE /bilhetes/{id}. O modal (DOM em
// app.js buildHTML) edita os 10 campos. Só linhas do dono efetivo COM id (Postgres)
// chegam editáveis — ver `editavel` em renderApostasVirt. Após salvar/deletar,
// re-busca o feed (loadData) para P/L derivado, KPIs e gating baterem com o servidor.
let apEditId=null;
const AP_ED_CAMPOS=['data','esporte','tipster','casa','parceiro','stake','odd','aposta','descricao','resultado'];
function _apRowById(id){
  return apostasTabela.find(r=>r.id===id)
    || (typeof DADOS!=='undefined'?DADOS.find(r=>r.id===id):null)
    || (typeof DADOS_ABERTAS!=='undefined'?DADOS_ABERTAS.find(r=>r.id===id):null)
    || null;
}
function _apIsoToBR(s){const m=(s||'').match(/^(\d{4})-(\d{2})-(\d{2})/);return m?`${m[3]}/${m[2]}/${m[1]}`:(s||'');}
// Valor mostrado no input para cada campo. Odd/stake em precisão TOTAL (String) —
// a odd nunca é truncada; como o patch só leva campos alterados, uma odd intocada
// jamais é reenviada (não corrompe o P/L derivado).
function _apEditVal(r,c){
  if(c==='data')return _apIsoToBR(r.data);
  if(c==='resultado')return r.resultado==='ABERTA'?'':(r.resultado||'');
  return r[c]!=null?String(r[c]):'';
}
function abrirEdicaoApostas(id){
  const r=_apRowById(id);
  if(!r)return;
  apEditId=id;
  AP_ED_CAMPOS.forEach(c=>{const el=document.getElementById('ap-ed-'+c);if(el)el.value=_apEditVal(r,c);});
  const err=document.getElementById('apEditErr');if(err){err.style.display='none';err.textContent='';}
  const ov=document.getElementById('apEditOverlay');
  if(ov){ov.style.display='flex';document.body.style.overflow='hidden';}
}
window.abrirEdicaoApostas=abrirEdicaoApostas;
function fecharEdicaoApostas(e){
  if(e&&e.target!==document.getElementById('apEditOverlay'))return;
  const ov=document.getElementById('apEditOverlay');
  if(ov)ov.style.display='none';
  document.body.style.overflow='';
  apEditId=null;
}
window.fecharEdicaoApostas=fecharEdicaoApostas;
function _apEditErro(msg){const err=document.getElementById('apEditErr');if(err){err.textContent=msg;err.style.display='block';}}
async function salvarEdicaoApostas(){
  if(apEditId==null)return;
  const r=_apRowById(apEditId);
  if(!r){fecharEdicaoApostas();return;}
  const patch={};
  AP_ED_CAMPOS.forEach(c=>{
    const el=document.getElementById('ap-ed-'+c);
    if(!el)return;
    const v=el.value.trim();
    if(_apEditVal(r,c)!==v)patch[c]=v;   // só o que mudou
  });
  if(!Object.keys(patch).length){fecharEdicaoApostas();return;}
  try{
    const res=await fetch(`/bilhetes/${apEditId}`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify(patch)});
    if(!res.ok)throw new Error();
    fecharEdicaoApostas();
    await loadData(false);
  }catch(_){_apEditErro('Erro ao salvar. Confira os campos (data DD/MM/AAAA, stake/odd numéricos, resultado W/L/V/HW/HL).');}
}
window.salvarEdicaoApostas=salvarEdicaoApostas;
// Chamado com id (botão ✕ da linha) ou sem arg (botão do modal → usa apEditId).
async function deletarApostas(id){
  const alvo=(id!=null)?id:apEditId;
  if(alvo==null)return;
  if(!confirm('Deletar esta aposta? A linha será removida da base.'))return;
  try{
    const res=await fetch(`/bilhetes/${alvo}`,{method:'DELETE'});
    if(!res.ok)throw new Error();
    fecharEdicaoApostas();
    await loadData(false);
  }catch(_){
    if(apEditId!=null)_apEditErro('Erro ao deletar.');
    else alert('Erro ao deletar a aposta.');
  }
}
window.deletarApostas=deletarApostas;

// ── Edição inline por duplo-clique ──────────────────────────────────────────
// Duplo-clique numa célula editável (data-field) troca o conteúdo por um input
// (ou <select> no resultado). Enter/blur salva via PATCH /bilhetes/{id} e re-busca
// o feed; Esc cancela. Enquanto edita, _apInlineEditing trava o virtual-scroll.
function _apInlineStart(cell){
  if(_apInlineEditing)return;
  const field=cell.dataset.field;
  if(!field)return;
  const rowEl=cell.closest('.btbl-data-row');
  if(!rowEl||!rowEl.dataset.id)return;
  const id=parseInt(rowEl.dataset.id,10);
  const r=_apRowById(id);
  if(!r||r.operador!==window.__dono)return;   // só o dono efetivo edita
  const cur=_apEditVal(r,field);
  const orig=cell.innerHTML;
  _apInlineEditing=true;
  let editor;
  if(field==='resultado'){
    editor=document.createElement('select');
    editor.innerHTML='<option value="">— aberta —</option>'+['W','L','V','HW','HL'].map(x=>`<option value="${x}"${x===cur?' selected':''}>${x}</option>`).join('');
  }else{
    editor=document.createElement('input');
    editor.type='text';
    editor.value=cur;
  }
  editor.className='ap-inline-inp';
  cell.innerHTML='';
  cell.appendChild(editor);
  editor.focus();
  if(editor.select)editor.select();
  let done=false;
  const finish=async(commit)=>{
    if(done)return;
    done=true;
    const val=editor.value.trim();
    _apInlineEditing=false;
    if(!commit||val===cur){cell.innerHTML=orig;return;}
    try{
      const res=await fetch(`/bilhetes/${id}`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({[field]:val})});
      if(!res.ok)throw new Error();
      await loadData(false);   // feed fresco → P/L derivado, KPIs e gating batem com o servidor
    }catch(_){
      cell.innerHTML=orig;
      alert('Erro ao salvar. Confira o valor (data DD/MM/AAAA, stake/odd numéricos, resultado W/L/V/HW/HL).');
    }
  };
  editor.addEventListener('keydown',e=>{
    if(e.key==='Enter'){e.preventDefault();finish(true);}
    else if(e.key==='Escape'){e.preventDefault();finish(false);}
  });
  editor.addEventListener('blur',()=>finish(true));
  if(field==='resultado')editor.addEventListener('change',()=>finish(true));
}
document.addEventListener('dblclick',e=>{
  const cell=e.target.closest&&e.target.closest('#page-apostas [data-field]');
  if(cell)_apInlineStart(cell);
});
