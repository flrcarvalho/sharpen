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
    const mkKA=(l,v,c,sub,bar)=>`<div class="kpi" style="height:110px;box-sizing:border-box;display:flex;flex-direction:column;justify-content:flex-start;padding:14px 16px;overflow:hidden"><div class="kpi-label" style="font-size:10px;text-transform:uppercase;letter-spacing:.1em;color:var(--ink-soft);margin-bottom:8px;white-space:nowrap;flex-shrink:0">${l}</div><div class="kpi-val ${c}" style="font-size:22px;line-height:1;font-variant-numeric:tabular-nums;white-space:nowrap;flex-shrink:0">${v}</div>${bar!==undefined?`<div class="wrc"><div class="t"><div class="f" style="width:${Math.min(100,Math.max(0,bar)).toFixed(1)}%"></div></div></div>`:''}<div class="kpi-sub" style="font-size:10px;margin-top:8px;font-family:'JetBrains Mono',monospace;display:flex;flex-wrap:wrap;gap:2px 5px;overflow:hidden">${sub||''}</div></div>`;
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
    // Duplo-clique edita a célula in loco — só nas linhas editáveis. `df()` emite o
    // marcador data-field (o handler _apInlineStart valida de novo) e `ec` concatena a
    // classe `ap-edit` (cursor) na classe-base. UM só atributo class por célula: um
    // segundo class= era descartado pelo parser → o cursor de edição nunca aparecia.
    const df=f=>editavel?` data-field="${f}"`:'';
    const ec=editavel?' ap-edit':'';
    return`<div class="btbl-cols btbl-data-row"${r.id!=null?` data-id="${r.id}"`:''} style="height:${BTBL_ROW_H}px">
      <div class="btbl-cell btbl-date${ec}"${df('data')}>${dateStr}</div>
      <div class="btbl-cell">
        ${r.aposta?`<div class="btbl-tipo${ec}"${df('aposta')}>${esc(r.aposta)}</div>`:''}
        <div class="btbl-desc${ec}"${df('descricao')}>${esc(r.descricao||r.aposta||'—')}</div>
      </div>
      <div class="btbl-cell btbl-sport${ec}"${df('esporte')}>${mkSpChip(r.esporte)}<span>${esc(r.esporte||'—')}</span></div>
      <div class="btbl-cell btbl-tipster${ec}"${df('tipster')}>${esc(r.tipster||'—')}</div>
      <div class="btbl-cell btbl-casa">
        ${mkHouseChip(r.casa)}
        <div class="btbl-casa-sub">
          <span class="btbl-casa-nome${ec}"${df('casa')}>${esc(r.casa||'—')}</span>
          ${parceiro?`<span class="btbl-casa-conta${ec}"${df('parceiro')}>${esc(parceiro)}</span>`:''}
        </div>
      </div>
      <div class="btbl-cell btbl-num${ec}"${df('stake')}>${fmtR(r.stake)}</div>
      <div class="btbl-cell btbl-num${ec}"${df('odd')}>${fmtOdd(r.odd)}</div>
      <div class="btbl-cell${ec}"${df('resultado')} style="display:flex;align-items:center;justify-content:center">
        <span class="bet-res-pill ${resClass}">${resLabel}</span>
      </div>
      <div class="btbl-cell btbl-pl">${r.resultado==='ABERTA'?'<span style="color:var(--ink-mute)">—</span>':fmtPL(r.lucro)}</div>
      <div class="btbl-cell btbl-acts">${window.MODO_PUBLICO?'':(editavel
        ? `<button class="act-btn" title="Editar aposta" onclick="abrirEdicaoApostas(${r.id})">✎</button><button class="act-btn del" title="Deletar aposta" onclick="deletarApostas(${r.id})">✕</button>`
        : `<span class="act-btn off" title="Linha da planilha ao vivo ou de um operador — edite na origem">✎</span>`)}</div>
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

// ── Autocomplete de tipster (modal + edição inline) ─────────────────────────
// Feedback do tester João Henrique (14/08): "ser possível selecionar os tipsters já
// cadastrados ao invés de digitar manualmente, assim como já acontece durante o
// cadastro da aposta". Na Extração o dropdown existe desde sempre (`.ac-menu`, no
// index.html); aqui os dois campos de tipster eram `<input>` cru.
//
// TEXTO LIVRE CONTINUA VALENDO — o menu sugere, não restringe. Um `<select>` fecharia
// a porta para o tipster que ainda não existe, e é justamente na edição que ele
// costuma nascer. Por isso a lista é sugestão, e nada valida o que foi digitado.
//
// As opções saem da mesma união de gestao.js `_ctTipsters`, MENOS a fonte `ctData`:
// custo só está carregado se o dono passou pela aba de custos nesta sessão, e uma
// sugestão que aparece ou não conforme a aba visitada antes é pior que não ter.
let _acMenu=null;      // <div.ac-menu> — criado sob demanda, vive no body
let _acInp=null;       // input ligado no momento
let _acItens=[];       // opções visíveis agora
let _acIdx=-1;         // índice destacado (navegação por teclado)
let _acCb=null;        // callback de escolha do input ligado

function _apTipsterOpcoes(){
  const s=new Set();
  const cad=(typeof _tipsCadastro!=='undefined'&&_tipsCadastro)?_tipsCadastro:[];
  cad.forEach(n=>s.add(n));
  const _liq=(typeof DADOS!=='undefined'&&DADOS)?DADOS:[];
  const _ab=(typeof DADOS_ABERTAS!=='undefined'&&DADOS_ABERTAS)?DADOS_ABERTAS:[];
  _liq.concat(_ab).forEach(r=>{if(r.tipster)s.add(r.tipster);});
  return [...s].sort((a,b)=>a.localeCompare(b,'pt-BR'));
}
function _acEl(){
  if(_acMenu)return _acMenu;
  _acMenu=document.createElement('div');
  _acMenu.className='ac-menu';
  document.body.appendChild(_acMenu);
  // mousedown, NÃO click: dispara antes do blur, então o editor inline não salva no
  // meio do clique e o `preventDefault` mantém o foco no input. Mesmo truque que o
  // SharpenCal usa para conviver com o `blur`→`finish(true)` da edição inline.
  _acMenu.addEventListener('mousedown',e=>{
    const it=e.target.closest&&e.target.closest('.ac-item');
    if(!it)return;
    e.preventDefault();
    _acAplicar(parseInt(it.dataset.i,10));
  });
  return _acMenu;
}
function _acAberto(){return !!_acMenu&&_acMenu.style.display!=='none';}
function _acFechar(){if(_acMenu)_acMenu.style.display='none';_acItens=[];_acIdx=-1;}
function _acSoltar(){_acFechar();_acInp=null;_acCb=null;}
function _acPintar(){
  if(!_acMenu)return;
  Array.from(_acMenu.children).forEach((el,i)=>el.classList.toggle('active',i===_acIdx));
  const at=_acMenu.children[_acIdx];
  if(at)at.scrollIntoView({block:'nearest'});
}
function _acAplicar(i){
  if(i<0||i>=_acItens.length||!_acInp)return;
  const v=_acItens[i],cb=_acCb;
  _acInp.value=v;
  _acFechar();
  if(cb)cb(v);
}
// `filtrar` = já digitou algo (filtra pelo texto); no foco abre a lista inteira.
function _acRender(filtrar){
  if(!_acInp)return;
  const m=_acEl();
  const q=_acInp.value.trim().toLowerCase();
  let ops=_apTipsterOpcoes();
  if(filtrar&&q){
    ops=ops.filter(t=>t.toLowerCase().includes(q))
      .sort((a,b)=>(b.toLowerCase().startsWith(q)?1:0)-(a.toLowerCase().startsWith(q)?1:0));
  }
  ops=ops.slice(0,50);
  _acItens=ops;
  if(!ops.length){_acFechar();return;}   // nome novo: sem menu, o campo segue livre
  m.innerHTML=ops.map((t,i)=>`<div class="ac-item" data-i="${i}">${esc(t)}</div>`).join('');
  m.style.display='block';
  // Ancoragem: `position:fixed` + rect do input. Vira para CIMA quando não cabe
  // abaixo — sem isso, editar uma linha do rodapé da tabela abriria o menu fora da tela.
  const r=_acInp.getBoundingClientRect();
  m.style.minWidth=Math.max(r.width,160)+'px';
  m.style.left=Math.max(4,Math.min(r.left,window.innerWidth-m.offsetWidth-4))+'px';
  const abaixo=window.innerHeight-r.bottom;
  m.style.top=(abaixo<m.offsetHeight+8&&r.top>abaixo)
    ? Math.max(4,r.top-m.offsetHeight-2)+'px'
    : (r.bottom+2)+'px';
  _acIdx=(filtrar&&q)?0:-1;   // melhor match já destacado → Enter aceita direto
  _acPintar();
}
// Liga o dropdown num input de tipster. `aoEscolher` roda depois de preencher o campo
// (a edição inline aproveita para salvar na hora, como o SharpenCal faz na data).
// O keydown é registrado AQUI, antes dos handlers de quem chama: com o menu aberto,
// Enter/Esc/setas são do menu e param por `stopImmediatePropagation` — sem isso o
// Enter salvaria a linha em vez de aceitar a sugestão, e o Esc cancelaria a edição
// inteira em vez de só fechar a lista. Um 2º Esc (menu fechado) cancela, como antes.
function _acLigar(inp,aoEscolher){
  if(!inp)return;
  const focar=()=>{_acInp=inp;_acCb=aoEscolher||null;_acRender(false);};
  inp.addEventListener('focus',focar);
  inp.addEventListener('input',()=>{_acInp=inp;_acCb=aoEscolher||null;_acRender(true);});
  inp.addEventListener('blur',()=>{if(_acInp===inp)_acSoltar();});
  inp.addEventListener('keydown',e=>{
    if(_acInp!==inp)return;
    if(e.key==='ArrowDown'||e.key==='ArrowUp'){
      if(!_acAberto()){_acRender(true);if(!_acAberto())return;}
      e.preventDefault();e.stopImmediatePropagation();
      const n=_acItens.length;
      _acIdx=(e.key==='ArrowDown')?(_acIdx+1>=n?0:_acIdx+1):(_acIdx-1<0?n-1:_acIdx-1);
      _acPintar();
    }else if(e.key==='Enter'&&_acAberto()&&_acIdx>=0){
      e.preventDefault();e.stopImmediatePropagation();
      _acAplicar(_acIdx);
    }else if(e.key==='Escape'&&_acAberto()){
      e.preventDefault();e.stopImmediatePropagation();
      _acFechar();
    }else if(e.key==='Tab'){_acFechar();}
  });
  // Ancoragem é por coordenada: rolar ou redimensionar deixaria o menu órfão no lugar
  // antigo. Captura porque o scroll que interessa é o da tabela virtual, não o do body.
  if(!_acLigar._glob){
    _acLigar._glob=true;
    window.addEventListener('scroll',()=>{if(_acAberto())_acFechar();},true);
    window.addEventListener('resize',()=>{if(_acAberto())_acFechar();});
  }
}
// Carga do cadastro (gestao.js, cacheada por sessão). Assíncrona: se o menu já estiver
// aberto quando a resposta chegar, repinta — senão a 1ª abertura mostraria só a base.
function _acCarregar(){
  if(typeof tipstersCadastroLoad!=='function')return;
  tipstersCadastroLoad().then(()=>{if(_acAberto())_acRender(!!_acInp&&!!_acInp.value.trim());}).catch(()=>{});
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
// Botão de calendário do campo Data do modal: abre o SharpenCal (calendário da
// marca) ancorado no input; escolher um dia devolve DD/MM/AAAA ao campo digitável.
function apEdAbrirCalendario(){
  const txt=document.getElementById('ap-ed-data');
  if(!txt||!window.SharpenCal)return;
  SharpenCal.abrir(txt,txt.value,v=>{txt.value=v;});
}
window.apEdAbrirCalendario=apEdAbrirCalendario;
function abrirEdicaoApostas(id){
  const r=_apRowById(id);
  if(!r)return;
  apEditId=id;
  AP_ED_CAMPOS.forEach(c=>{const el=document.getElementById('ap-ed-'+c);if(el)el.value=_apEditVal(r,c);});
  // Tipster: dropdown dos já cadastrados. O input é estático (nasce no buildHTML), então
  // liga UMA vez — reabrir o modal empilharia listeners. Sem callback: no modal a escolha
  // só preenche o campo; quem salva é o botão, como nos outros 9 campos.
  const elTip=document.getElementById('ap-ed-tipster');
  if(elTip&&!elTip.dataset.acOn){elTip.dataset.acOn='1';_acLigar(elTip,null);}
  _acCarregar();
  const err=document.getElementById('apEditErr');if(err){err.style.display='none';err.textContent='';}
  const ov=document.getElementById('apEditOverlay');
  if(ov){ov.style.display='flex';document.body.style.overflow='hidden';}
}
window.abrirEdicaoApostas=abrirEdicaoApostas;
// Alguma edição pendente? Compara com o valor carregado na abertura — o modal
// nasce cheio, então "sujo" é o que o operador mudou, não o que está preenchido.
function _apEditSujo(){
  const r=apEditId!=null?_apRowById(apEditId):null;
  if(!r)return false;
  return AP_ED_CAMPOS.some(c=>{const el=document.getElementById('ap-ed-'+c);return el&&el.value!==_apEditVal(r,c);});
}
function fecharEdicaoApostas(e){
  if(e&&e.target!==document.getElementById('apEditOverlay'))return;
  // Clique no fundo é gesto fácil de disparar sem querer e o modal reabre do zero:
  // com edição pendente ele não fecha, só sacode. ✕/Cancelar chamam sem evento e
  // fecham sempre (intenção explícita).
  if(e&&_apEditSujo()){
    const m=document.getElementById('apEditModal');
    if(m){m.classList.remove('modal--shake');void m.offsetWidth;m.classList.add('modal--shake');setTimeout(()=>m.classList.remove('modal--shake'),400);}
    return;
  }
  const ov=document.getElementById('apEditOverlay');
  if(ov)ov.style.display='none';
  document.body.style.overflow='';
  _acSoltar();   // o menu vive no body: fechar o modal sem soltá-lo o deixaria na tela
  apEditId=null;
}
window.fecharEdicaoApostas=fecharEdicaoApostas;
function _apEditErro(msg){const err=document.getElementById('apEditErr');if(err){err.textContent=msg;err.style.display='block';}}
async function salvarEdicaoApostas(){
  if(window.MODO_PUBLICO)return;   // vitrine pública: nunca escreve (nem via console)
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
  if(window.MODO_PUBLICO)return;   // vitrine pública: nunca escreve (nem via console)
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
    if(window.SharpenCal)SharpenCal.fechar();
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
  // Tipster: mesmo dropdown do modal, ligado ANTES dos handlers abaixo — com o menu
  // aberto ele consome Enter/Esc/setas (ver `_acLigar`). Escolher preenche e SALVA na
  // hora, igual ao SharpenCal na data; o campo continua aceitando nome digitado.
  if(field==='tipster'){_acLigar(editor,()=>finish(true));_acCarregar();}
  editor.addEventListener('keydown',e=>{
    if(e.key==='Enter'){e.preventDefault();finish(true);}
    else if(e.key==='Escape'){e.preventDefault();finish(false);}
  });
  editor.addEventListener('blur',()=>finish(true));
  if(field==='resultado')editor.addEventListener('change',()=>finish(true));
  // Data: o SharpenCal abre junto do input (digitar continua valendo). Escolher um
  // dia preenche e salva; o popover segura o foco no editor (mousedown preventDefault),
  // então o blur não dispara no meio do clique.
  if(field==='data'&&window.SharpenCal)
    SharpenCal.abrir(editor,cur,v=>{if(v){editor.value=v;finish(true);}});
}
document.addEventListener('dblclick',e=>{
  if(window.MODO_PUBLICO)return;   // vitrine pública: sem edição inline
  const cell=e.target.closest&&e.target.closest('#page-apostas [data-field]');
  if(cell)_apInlineStart(cell);
});
