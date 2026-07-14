// ── Aparência ────────────────────────────────────────────────────────────────
// App 100% dark por enquanto (tema claro adiado). Sem seletor de tema no app:
// o dark é cravado no boot (index.html) e reforçado aqui.
function applyAparencia(){
  const h=document.documentElement;
  h.setAttribute('data-theme','dark');
  h.setAttribute('data-density','compact');
  h.classList.add('t-page-gradient');
  h.classList.add('kpi-azul');
}

// Helpers
function fmt(v,d=2){return Math.abs(v).toLocaleString('pt-BR',{minimumFractionDigits:d,maximumFractionDigits:d});}
function fmtPL(v){const cls=v>=0?'pos':'neg';return`<span class="money ${cls}"><span class="money-sign">${v>=0?'+':'−'}R$</span><span class="money-val">${fmt(Math.abs(v))}</span></span>`;}
function fmtR(v){return`<span class="money"><span class="money-sign">R$</span><span class="money-val">${fmt(v,0)}</span></span>`;}
function fmtPct(v,d=2,signed=true){const abs=Math.abs(v).toLocaleString('pt-BR',{minimumFractionDigits:d,maximumFractionDigits:d});if(!signed)return abs+'%';return(v>=0?'+':'−')+abs+'%';}
function fmtOdd(v){return Number(v||0).toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2});}
// fmtU — resultado em UNIDADES (Perfil de Tipster). Espelha fmtPL trocando R$→"u" como
// sufixo (+3,25u / −1,50u), 2 casas, minus U+2212, cor só no número (§5; formato cravado
// pelo Feca). Zero neutro (0,00u). Nota: o fmtPL acima trata zero como '+' (desvio herdado
// do §5); o fmtU segue a regra — zero sem sinal e sem cor.
function fmtU(v){const n=Number(v)||0;const cls=n>0?'pos':(n<0?'neg':'');const sign=n>0?'+':(n<0?'−':'');return`<span class="money ${cls}"><span class="money-val">${sign}${fmt(Math.abs(n))}<span class="money-u">u</span></span></span>`;}
// unidade_vigente (mirror JS do backend): degrau + clamp à esquerda. escada ordenada por
// data; null se vazia/data ilegível. Ver repository.py unidade_vigente.
function _uVigente(escada,dataISO){if(!escada||!escada.length||!dataISO)return null;const s=[...escada].sort((a,b)=>a.vigente_desde<b.vigente_desde?-1:1);let ap=s[0].valor;for(const seg of s){if(seg.vigente_desde<=dataISO)ap=seg.valor;else break;}return ap;}
// P/L em u por tipster sobre linhas JÁ FILTRADAS (respeita os filtros do dashboard).
// Sem escada: fallback = stake média das linhas do tipster (espelha resultado_em_unidades).
function _tipsterUnidades(rows,escadas){
  const by={};
  rows.forEach(r=>{if(!r.tipster)return;const d=by[r.tipster]||(by[r.tipster]={lin:[],stk:[]});d.lin.push({pl:r.lucro,data:(r.data||'').slice(0,10)});if(r.stake>0)d.stk.push(r.stake);});
  const out={};
  for(const t in by){const esc=(escadas&&escadas[t])||[];const stk=by[t].stk;const fb=(!esc.length&&stk.length)?stk.reduce((a,b)=>a+b,0)/stk.length:null;let u=0;by[t].lin.forEach(ln=>{let uu=_uVigente(esc,ln.data);if(uu==null)uu=fb;if(uu&&uu>0)u+=ln.pl/uu;});out[t]=u;}
  return out;
}
// Switch R$ ⇄ u da página Tipsters (preferência por dono).
let _tipUnit=(localStorage.getItem('dash_tipunit::'+(window.__dono||'_'))==='u')?'u':'reais';
let _tipEscadas=null;   // cache de GET /tipsters/escadas (buscado sob demanda ao trocar p/ u)
function tipSetUnit(u){_tipUnit=u;try{localStorage.setItem('dash_tipunit::'+(window.__dono||'_'),u);}catch(e){}renderTipsters();}
function destroyChart(id){if(charts[id]){charts[id].destroy();delete charts[id];}}
function mkChart(id,cfg){destroyChart(id);if(!document.getElementById(id))return;charts[id]=new Chart(document.getElementById(id),cfg);}
function isDark(){return document.documentElement.getAttribute('data-theme')==='dark';}
function gc(){return isDark()?'rgba(255,255,255,.05)':'rgba(0,0,0,.06)';}
function tc(){return isDark()?'#505060':'#a0a0b8';}
// Favicon via Google S2 — para produção offline trocar por: assets/casas/NOME.png
function favicon(domain){return`https://www.google.com/s2/favicons?domain=${domain}&sz=64`;}
function _houseDomain(nome){
  if(!nome)return'';
  if(HOUSE_DOMAIN[nome])return HOUSE_DOMAIN[nome];
  const k=Object.keys(HOUSE_DOMAIN).find(k=>k.toLowerCase()===nome.toLowerCase());
  return k?HOUSE_DOMAIN[k]:'';
}
function mkSpChip(sport){
  let key=SPORT_KEY[sport];
  if(!key){const k=Object.keys(SPORT_KEY).find(k=>k.toLowerCase()===sport?.toLowerCase());key=k?SPORT_KEY[k]:null;}
  return`<span class="sp-chip" style="filter:grayscale(1)">${SPORT_EMOJI[key]||'🏅'}</span>`;
}
// Fallback de favicon: substitui img por inicial mono quando imagem falha
document.addEventListener('error',e=>{
  const chip=e.target.closest?.('.house-chip');
  if(chip&&e.target.tagName==='IMG'){
    const init=chip.dataset.initial||'?';
    e.target.replaceWith(Object.assign(document.createElement('span'),{className:'chip-initial',textContent:init}));
  }
},true);
function mkHouseChip(nome){
  if(!nome)return`<span class="house-chip chip-initial">?</span>`;
  const domain=_houseDomain(nome);
  if(domain){
    const init=esc((nome[0]||'?').toUpperCase());
    const escNome=esc(nome);
    return`<span class="house-chip" data-initial="${init}" data-casa="${escNome}"><img src="${favicon(domain)}" alt="${escNome}"></span>`;
  }
  return`<span class="house-chip chip-initial">${esc((nome[0]||'?').toUpperCase())}</span>`;
}
function casaCell(nome){
  return`<span style="display:inline-flex;align-items:center;gap:6px">${mkHouseChip(nome)}${nome?esc(nome):'—'}</span>`;
}
function sportCell(esporte){
  return`<span style="display:inline-flex;align-items:center;gap:6px">${mkSpChip(esporte)}${esporte?esc(esporte):'—'}</span>`;
}
// Mantido para compatibilidade — use mkHouseChip para novas implementações
function casaImg(nome,size=14){
  const domain=_houseDomain(nome);
  if(!domain)return'';
  return`<img src="${favicon(domain)}" width="${size}" height="${size}" style="border-radius:3px;vertical-align:middle;margin-right:4px;flex-shrink:0" onerror="this.style.display='none'" loading="lazy">`;
}
function auditCasas(dados){
  const known=new Set(Object.keys(HOUSE_DOMAIN).map(k=>k.toLowerCase()));
  const reais=[...new Set(dados.map(r=>r.casa).filter(Boolean))];
  reais.forEach(c=>{if(!known.has(c.toLowerCase()))console.warn(`[audit-casas] "${c}" — sem domínio em HOUSE_DOMAIN`);});
}
// ── Normalização de nomes (evita duplicatas como "Faz1Bet" vs "Faz1bet") ────
function normalizeName(name){
  if(!name)return'';
  return name.trim().toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g,'').replace(/\s+/g,' ');
}
function getMostFrequentName(names){
  const freq={};names.forEach(n=>{if(n)freq[n]=(freq[n]||0)+1;});
  const ents=Object.entries(freq);if(!ents.length)return'';
  return ents.sort((a,b)=>b[1]-a[1])[0][0];
}
// Aplica o feed cru: normaliza nomes e SEPARA encerradas (→DADOS, base de todas
// as métricas) de abertas (→DADOS_ABERTAS, só listagem). Chamado nos 2 caminhos
// de loadData (cache local e fetch fresco) para o split ser único.
function aplicarFeed(dados){
  const norm=normalizeDados(dados);
  const ENCERRADAS=['W','L','V','HW','HL'];
  DADOS=norm.filter(r=>ENCERRADAS.includes(r.resultado));
  DADOS_ABERTAS=norm.filter(r=>r.resultado==='ABERTA');
}
function normalizeDados(dados){
  const fields=['tipster','casa','esporte'];
  const canonical={};
  fields.forEach(f=>{
    const groups={};
    dados.forEach(r=>{if(!r[f])return;const key=normalizeName(r[f]);if(!groups[key])groups[key]=[];groups[key].push(r[f]);});
    canonical[f]={};
    Object.entries(groups).forEach(([key,names])=>{canonical[f][key]=getMostFrequentName(names);});
  });
  return dados.map(r=>{
    const nr={...r};
    fields.forEach(f=>{if(nr[f])nr[f]=canonical[f][normalizeName(nr[f])]||nr[f];});
    return nr;
  });
}
function normalCDF(z){const t=1/(1+.2316419*Math.abs(z)),d=.3989423*Math.exp(-z*z/2);const p=d*t*(.3193815+t*(-.3565638+t*(1.781478+t*(-1.821256+t*1.330274))));return z>0?1-p:p;}
// Turnover canônico: soma da stake APENAS de apostas encerradas (exclui Void — stake devolvida)
function calcTurnover(rows){return rows.reduce((a,r)=>a+(r.resultado!=='V'?r.stake:0),0);}
function calcROI(rows){const s=calcTurnover(rows),l=rows.reduce((a,r)=>a+r.lucro,0);return s>0?(l/s)*100:0;}
// Win Rate com HW = meia vitória e HL = meia derrota (decisão do Feca, 11/07): a metade
// devolvida de HW/HL sai da conta, como o Void. As CONTAGENS exibidas seguem INTEIRAS
// (nunca "12,5"); só a % fraciona. Deriva das contagens inteiras já existentes — w (=W+HW),
// t (=encerradas, exclui V) — mais quantos são HW e HL:
//   wr = (w − ½·hw) / (t − ½·hw − ½·hl) × 100.
// Defensivo: hw/hl ausentes (0) → cai no win rate antigo (w/t), nunca NaN.
function wrFrac(w,hw,hl,t){hw=hw||0;hl=hl||0;const den=t-0.5*hw-0.5*hl;return den>0?((w-0.5*hw)/den)*100:0;}
// Acumula os contadores de um mapa (w=vitórias inteiras W+HW; hw/hl p/ a fração; t=encerradas).
function bumpWR(m,res){if(res==='V')return;m.t++;if(res==='W')m.w++;else if(res==='HW'){m.w++;m.hw=(m.hw||0)+1;}else if(res==='HL')m.hl=(m.hl||0)+1;}
function wrPctRows(rows){let w=0,hw=0,hl=0,t=0;for(const r of rows){const x=r.resultado;if(x==='V')continue;t++;if(x==='W')w++;else if(x==='HW'){w++;hw++;}else if(x==='HL')hl++;}return wrFrac(w,hw,hl,t);}
function calcWR(rows){return wrPctRows(rows);}
function calcAvgOdd(rows){const real=rows.filter(r=>r.odd>0&&r.stake>0);const ss=real.reduce((a,r)=>a+r.stake,0);return ss>0?real.reduce((a,r)=>a+r.odd*r.stake,0)/ss:0;}
// Drawdown REAL da carteira — fonte única de verdade.
// Agrega o P/L por DIA e percorre a curva em ordem CRONOLÓGICA (igual ao gráfico
// "Resultado Geral" em renderBankroll). A planilha de origem NÃO vem ordenada por data
// (é organizada por casa → parceiro, com linhas em branco), então a ordenação aqui é
// OBRIGATÓRIA: sem ela o drawdown seria o vale de uma curva fora de ordem — uma queda que
// nunca aconteceu. R$ e % saem do MESMO episódio pico→vale, sempre coerentes entre si.
// Retorna {mddReais, mddPct, peakDate, troughDate}.
function calcDrawdownReal(rows){
  const byDay={};
  for(const r of rows){const k=(r.data||'').slice(0,10);if(!k)continue;byDay[k]=(byDay[k]||0)+(r.lucro||0);}
  const days=Object.keys(byDay).sort();
  let cum=0,peak=0,peakDay=null,mdd=0,mddPct=0,peakDate=null,troughDate=null;
  for(const d of days){
    cum+=byDay[d];
    if(cum>peak){peak=cum;peakDay=d;}
    const dd=peak-cum;
    if(dd>mdd){mdd=dd;mddPct=dd/(BASE_BANK+peak)*100;peakDate=peakDay;troughDate=d;}
  }
  return{mddReais:mdd,mddPct:mddPct,peakDate:peakDate,troughDate:troughDate};
}
function calcMDDreais(rows){return calcDrawdownReal(rows).mddReais;}
function calcMDDpct(rows){return calcDrawdownReal(rows).mddPct;}
function mulberry32(a){return function(){a|=0;a=(a+0x6D2B79F5)|0;var t=Math.imul(a^(a>>>15),1|a);t=(t+Math.imul(t^(t>>>7),61|t))^t;return((t^(t>>>14))>>>0)/4294967296;};}
// ── Memoização do Monte Carlo ────────────────────────────────────────────────
// calcMCdrawdown e calcPValueMC são funções PURAS (semente derivada dos dados),
// então o resultado só depende de (conjunto de rows, sims). Voltar a uma aba com
// o mesmo filtro recalculava ~254M iterações à toa — o cache abaixo torna isso
// instantâneo. A assinatura (n + somas de P/L, stake e |P/L|) é O(n) barata e
// distingue conjuntos diferentes com colisão desprezível. Cache em memória, por
// sessão; invalida sozinho quando o filtro/dados mudam (assinatura nova).
var _mcCache=Object.create(null), _pvCache=Object.create(null);
function _rowsSig(rows){var n=rows.length,sl=0,ss=0,sa=0;for(var i=0;i<n;i++){var lv=+rows[i].lucro||0;sl+=lv;ss+=+rows[i].stake||0;sa+=lv<0?-lv:lv;}return n+'|'+sl.toFixed(2)+'|'+ss.toFixed(2)+'|'+sa.toFixed(2);}
function calcMCdrawdown(rows,sims){var k=(sims||5000)+'@'+_rowsSig(rows);var h=_mcCache[k];if(h)return h;return _mcCache[k]=_calcMCdrawdownRaw(rows,sims);}
function calcPValueMC(rows,sims){var k=(sims||0)+'@'+_rowsSig(rows);var h=_pvCache[k];if(h!==undefined)return h;return _pvCache[k]=_calcPValueMCraw(rows,sims);}
// ── Web Worker do Monte Carlo (não trava a UI) ───────────────────────────────
// O código do worker é GERADO a partir das mesmas funções _calcMCdrawdownRaw e
// _calcPValueMCraw (via .toString()) — garante número idêntico ao cálculo síncrono,
// sem duplicar a matemática. mcComputeAsync devolve uma Promise; alimenta o MESMO
// cache da memoização (_mcCache/_pvCache), então cache-hit resolve na hora (sem
// spinner). Fallback: se o navegador bloquear Worker (ex.: file://), computa em
// sync ADIADO (setTimeout) — a UI ao menos pinta antes de o cálculo travar.
var _mcWorker=null,_mcWorkerTried=false,_mcReqId=0,_mcPending=Object.create(null);
function _mcSyncFromArrays(L,S,sims){var n=L.length,rows=new Array(n);for(var i=0;i<n;i++)rows[i]={lucro:L[i],stake:S[i]};return{mc:_calcMCdrawdownRaw(rows,sims),pv:_calcPValueMCraw(rows,sims)};}
function _getMcWorker(){
  if(_mcWorkerTried)return _mcWorker;
  _mcWorkerTried=true;
  try{
    var src=mulberry32.toString()+'\n'+_calcMCdrawdownRaw.toString()+'\n'+_calcPValueMCraw.toString()+'\n'+
      'self.onmessage=function(e){var d=e.data,n=d.L.length,rows=new Array(n);for(var i=0;i<n;i++)rows[i]={lucro:d.L[i],stake:d.S[i]};'+
      'try{var mc=_calcMCdrawdownRaw(rows,d.sims),pv=_calcPValueMCraw(rows,d.sims);self.postMessage({id:d.id,mc:mc,pv:pv});}'+
      'catch(err){self.postMessage({id:d.id,err:String(err)});}};';
    _mcWorker=new Worker(URL.createObjectURL(new Blob([src],{type:'application/javascript'})));
    _mcWorker.onmessage=function(e){var d=e.data,p=_mcPending[d.id];if(!p)return;delete _mcPending[d.id];p.resolve(d.err?_mcSyncFromArrays(p.L,p.S,p.sims):{mc:d.mc,pv:d.pv});};
    _mcWorker.onerror=function(){_mcWorker=null;for(var id in _mcPending){var p=_mcPending[id];delete _mcPending[id];p.resolve(_mcSyncFromArrays(p.L,p.S,p.sims));}};
  }catch(e){_mcWorker=null;}
  return _mcWorker;
}
function mcComputeAsync(rows,sims){
  var sig=_rowsSig(rows),mcK=(sims||5000)+'@'+sig,pvK=(sims||0)+'@'+sig;
  var hMc=_mcCache[mcK],hPv=_pvCache[pvK];
  if(hMc&&hPv!==undefined)return Promise.resolve({mc:hMc,pv:hPv});
  var n=rows.length,L=new Float64Array(n),S=new Float64Array(n);
  for(var i=0;i<n;i++){L[i]=+rows[i].lucro||0;S[i]=+rows[i].stake||0;}
  var done=function(res){_mcCache[mcK]=res.mc;_pvCache[pvK]=res.pv;return res;};
  var w=_getMcWorker();
  if(w){
    return new Promise(function(resolve){
      var id=++_mcReqId;_mcPending[id]={resolve:resolve,L:L,S:S,sims:sims};
      try{w.postMessage({id:id,L:L,S:S,sims:sims});}catch(err){delete _mcPending[id];resolve(_mcSyncFromArrays(L,S,sims));}
    }).then(done);
  }
  return new Promise(function(resolve){setTimeout(function(){resolve(_mcSyncFromArrays(L,S,sims));},0);}).then(done);
}
function _calcPValueMCraw(rows,sims){var n=rows.length;if(n<30)return 1;sims=sims||(n>10000?3000:(n>3000?5000:10000));var L=new Float64Array(n),S=new Float64Array(n),sumL=0,sumS=0;for(var i=0;i<n;i++){L[i]=+rows[i].lucro||0;S[i]=+rows[i].stake||0;sumL+=L[i];sumS+=S[i];}if(sumS<=0)return 1;var yObs=sumL/sumS,r0=new Float64Array(n),q0=0;for(var j=0;j<n;j++){r0[j]=L[j]-yObs*S[j];q0+=r0[j]*r0[j];}var seObs=Math.sqrt(q0)/sumS;if(seObs<=0)return 1;var tObs=yObs/seObs;var seed=((n*2654435761)^(Math.round(Math.abs(sumL)*1000)|0))>>>0,rng=mulberry32(seed),cnt=0;for(var s=0;s<sims;s++){var rs=0,ss=0,rr=0,rsa=0,ssq=0;for(var b=0;b<n;b++){var k=(rng()*n)|0,rk=r0[k],sk=S[k];rs+=rk;ss+=sk;rr+=rk*rk;rsa+=rk*sk;ssq+=sk*sk;}if(ss<=0)continue;var ys=rs/ss,su2=rr-2*ys*rsa+ys*ys*ssq;if(su2>0&&ys*ss/Math.sqrt(su2)>=tObs)cnt++;}return(cnt+1)/(sims+1);}
function _calcMCdrawdownRaw(rows,sims){
  sims=sims||5000;
  var n=rows.length;
  if(n<2)return{xmdd:0,p50:0,p95:0,p99:0};
  var pls=new Float64Array(n),sumL=0;
  for(var i=0;i<n;i++){pls[i]=rows[i].lucro||0;sumL+=pls[i];}
  // O bootstrap reamostra o MULTICONJUNTO de P/L (iid) — a ordem do array só afeta a
  // realização semeada, não a distribuição. Ordenar os VALORES canoniza o array: o mesmo
  // conjunto de apostas dá o mesmo número em Métricas e nos drill-downs, independente da
  // ordem de entrada. (Ordenar por data não basta: apostas do mesmo dia empatam e a ordem
  // interna do empate ainda variaria entre telas.) Float64Array.sort() é numérico por padrão.
  pls.sort();
  // Semente derivada dos dados (independente da ordem) → determinístico entre renders e telas
  var seed=((n*2654435761)^(Math.round(Math.abs(sumL)*1000)|0))>>>0,rng=mulberry32(seed);
  var mdds=new Float64Array(sims);
  for(var s=0;s<sims;s++){
    var acc=0,peak=0,dd=0;
    for(var b=0;b<n;b++){acc+=pls[(rng()*n)|0];if(acc>peak)peak=acc;var t=peak-acc;if(t>dd)dd=t;}
    mdds[s]=dd;
  }
  var arr=Array.prototype.slice.call(mdds).sort(function(a,b){return a-b;});
  var q=function(f){return arr[Math.min(sims-1,Math.floor(f*sims))];};
  var sum=0;for(var k=0;k<sims;k++)sum+=arr[k];
  return{xmdd:sum/sims,p50:q(0.50),p95:q(0.95),p99:q(0.99)};
}
function calcRecoveryFactor(rows){
  var profit=0;for(var i=0;i<rows.length;i++)profit+=(rows[i].lucro||0);
  var mdd=calcMDDreais(rows);
  return mdd>0?profit/mdd:null;
}
function calcTopoDrawdown(rows){
  var s=rows.slice().sort(function(a,b){return a.data<b.data?-1:a.data>b.data?1:0;});
  var acc=0,peak=-Infinity,peakDate=null;
  for(var i=0;i<s.length;i++){acc+=(s[i].lucro||0);if(acc>peak){peak=acc;peakDate=s[i].data;}}
  var dd=peak-acc;
  return{topo:peak,topoData:peakDate,atual:acc,ddAtual:dd,ddAtualPct:peak>0?dd/peak:0};
}
function calcSolidez(o){
  var sEdge=o.pValue<0.001?1:o.pValue<0.05?0.5:0;
  var sFolga=o.profitXmdd>5?1:o.profitXmdd>=2?0.5:0;
  var sAmostra=o.nApostas>=1000?1:o.nApostas>=300?0.5:0;
  var sVar=o.oddMedia<=3?1:o.oddMedia<=10?0.5:0;
  var score=(sEdge*3+sFolga*3+sAmostra*2+sVar*2)/10;
  var faixa=score>=0.85?'Muito Alta':score>=0.65?'Alta':score>=0.45?'Média':score>=0.25?'Baixa':'Muito Baixa';
  return{score:score,faixa:faixa};
}


// Formatação de eixos com ponto como separador de milhar
function fmtK(v){
  const abs=Math.abs(Math.round(v));
  const s=abs.toLocaleString('pt-BR',{minimumFractionDigits:0,maximumFractionDigits:0});
  return(v<0?'−':'')+'R$ '+s;
}
const sortState={};
function parseNum(raw){
  // Remove R$, spaces, %, +, then handle Brazilian number format (dot=thousand, comma=decimal)
  const s=raw.replace(/R\$\s*/g,'').replace(/[+\s%]/g,'').trim();
  // Remove thousand separators (dots before groups of 3 digits) then replace comma with dot
  const n=parseFloat(s.replace(/\.(?=\d{3}[,\.])/g,'').replace(',','.'));
  return isNaN(n)?0:n;
}
function sortTable(tableId,colIdx,numeric){
  if(!sortState[tableId])sortState[tableId]={col:-1,asc:true};
  const st=sortState[tableId];
  st.asc=st.col===colIdx?!st.asc:true;
  st.col=colIdx;
  const table=document.getElementById(tableId);
  if(!table)return;
  const tbody=table.querySelector('tbody');
  const rows=[...tbody.querySelectorAll('tr:not(.total-row)')];
  rows.sort((a,b)=>{
    const ac=a.cells[colIdx],bc=b.cells[colIdx];
    const at=ac?.dataset.sort||ac?.textContent||'';
    const bt=bc?.dataset.sort||bc?.textContent||'';
    const res=numeric?(parseNum(at)-parseNum(bt)):(at.trim().localeCompare(bt.trim()));
    return st.asc?res:-res;
  });
  const totalRow=tbody.querySelector('.total-row');
  rows.forEach(r=>tbody.appendChild(r));
  if(totalRow)tbody.appendChild(totalRow);
  table.querySelectorAll('th').forEach((th,i)=>{
    th.classList.remove('sort-asc','sort-desc');
    if(i===colIdx)th.classList.add(st.asc?'sort-asc':'sort-desc');
    if(!th.querySelector('.sort-icon')){const si=document.createElement('span');si.className='sort-icon';th.appendChild(si);}
  });
}
function makeSortable(tableId,numericCols=[]){
  const table=document.getElementById(tableId);
  if(!table)return;
  table.querySelectorAll('th').forEach((th,i)=>{
    if(!th.querySelector('.sort-icon')){const si=document.createElement('span');si.className='sort-icon';th.appendChild(si);}
    th.style.cursor='pointer';
    th.onclick=()=>sortTable(tableId,i,numericCols.includes(i));
    addColResizer(th,tableId,i);
  });
}

// Column resize
const colWidths={};
function addColResizer(th,tableId,colIdx){
  th.style.position='relative';
  const rsz=document.createElement('div');
  rsz.className='col-rsz';
  rsz.addEventListener('mousedown',e=>{
    e.stopPropagation();e.preventDefault();
    rsz.classList.add('active');
    const startX=e.clientX,startW=th.offsetWidth;
    const key=tableId+'_'+colIdx;
    function onMove(ev){
      const nw=Math.max(40,startW+ev.clientX-startX);
      th.style.width=nw+'px';th.style.minWidth=nw+'px';
      colWidths[key]=nw;
      // Apply to td cells too
      const tbl=document.getElementById(tableId);
      if(tbl){tbl.querySelectorAll('tbody tr').forEach(tr=>{const td=tr.cells[colIdx];if(td){td.style.width=nw+'px';td.style.maxWidth=nw+'px';}});}
    }
    function onUp(){rsz.classList.remove('active');document.removeEventListener('mousemove',onMove);document.removeEventListener('mouseup',onUp);}
    document.addEventListener('mousemove',onMove);
    document.addEventListener('mouseup',onUp);
  });
  th.appendChild(rsz);
}

// ── Resize de colunas da lista de Apostas (grid .btbl) ──────────────────────
// A largura de cada coluna fica numa CSS var (--btbl-grid) no .btbl-wrap; como o
// header e as linhas virtuais compartilham .btbl-cols, todas seguem a var sozinhas.
// 'flex' = coluna Aposta/Evento (minmax 1fr) — absorve o resto, sem alça própria.
const BTBL_W_DEFAULT=[80,'flex',108,114,168,92,68,80,108,72];
const BTBL_W_KEY='btbl_colw_v2';   // v2: +coluna Ações (10 col) — v1 (9 col) cai no default pelo length-check
let btblColW=BTBL_W_DEFAULT.slice();
function _btblGridStr(){return btblColW.map(w=>w==='flex'?'minmax(160px,1fr)':w+'px').join(' ');}
function _btblApplyGrid(){const wrap=document.querySelector('.btbl-wrap');if(wrap)wrap.style.setProperty('--btbl-grid',_btblGridStr());}
function _btblLoadW(){try{const s=JSON.parse(localStorage.getItem(BTBL_W_KEY));if(Array.isArray(s)&&s.length===BTBL_W_DEFAULT.length)btblColW=s.map((w,i)=>BTBL_W_DEFAULT[i]==='flex'?'flex':(+w||BTBL_W_DEFAULT[i]));}catch(e){}}
function _btblSaveW(){try{localStorage.setItem(BTBL_W_KEY,JSON.stringify(btblColW));}catch(e){}}
function initBtblResize(){
  _btblLoadW();_btblApplyGrid();
  document.querySelectorAll('.btbl-hdr-row .btbl-th').forEach((th,i)=>{
    if(btblColW[i]==='flex')return;               // coluna flexível não tem alça
    th.style.position='relative';
    if(th.querySelector('.btbl-rsz'))return;
    const rsz=document.createElement('div');
    rsz.className='btbl-rsz';
    rsz.title='Arraste para ajustar · duplo-clique reseta tudo';
    rsz.addEventListener('click',e=>e.stopPropagation()); // não dispara o sort
    rsz.addEventListener('mousedown',e=>{
      e.stopPropagation();e.preventDefault();
      rsz.classList.add('active');
      document.body.style.cursor='col-resize';document.body.style.userSelect='none';
      const startX=e.clientX,startW=th.getBoundingClientRect().width;
      function onMove(ev){btblColW[i]=Math.max(48,Math.round(startW+ev.clientX-startX));_btblApplyGrid();}
      function onUp(){rsz.classList.remove('active');document.body.style.cursor='';document.body.style.userSelect='';document.removeEventListener('mousemove',onMove);document.removeEventListener('mouseup',onUp);_btblSaveW();}
      document.addEventListener('mousemove',onMove);document.addEventListener('mouseup',onUp);
    });
    rsz.addEventListener('dblclick',e=>{e.stopPropagation();btblColW=BTBL_W_DEFAULT.slice();_btblApplyGrid();_btblSaveW();});
    th.appendChild(rsz);
  });
}

// Result coloring helper
function resClass(r){
  if(r==='W')return'res-w';
  if(r==='HW')return'res-hw';
  if(r==='L')return'res-l';
  if(r==='HL')return'res-hl';
  return'res-v';
}
function resColor(r){
  const m={'W':'var(--pos)','HW':'var(--hw)','L':'var(--neg)','HL':'var(--hl)','V':'var(--ink-mute)'};
  return m[r]||'var(--ink-soft)';
}

function mkCard(id,title,bodyHTML,extraHdrHTML=''){
  return`<div class="card" id="card-${id}">
    <div class="card-hdr">
      <div class="card-title">${title}</div>
      ${extraHdrHTML}
    </div>
    <div class="card-body">${bodyHTML}</div>
  </div>`;
}

// Nav
const PAGE_META={
  'overview':       ['Visão Geral',              'performance consolidada'],
  'sports':         ['Esportes',                 'performance por modalidade esportiva'],
  'casas':          ['Bookies',                  'performance e ROI por bookmaker'],
  'apostas':        ['Apostas',                  'espelho completo da base de dados'],
  'tipsters':       ['Tipsters',                 'análise comparativa e individual'],
  'resultados':     ['Resultados',               'matriz por período, calendário e análises'],
  'parceiros':      ['Fornecedores & Parceiros', 'turnover, lucro e período por conta'],
  'custos':         ['Custos de Contas',         'custo de aquisição por conta e fornecedor'],
  'custos_tipster': ['Custo de Tipsters',        'assinaturas, serviços e pagamentos'],
  'metrics':        ['Métricas',                 'base de conhecimento e valores atuais'],
};
// Deep-link: os atalhos do Planilhador chegam como /dashboard/#<id>. Sem âncora
// (ou âncora desconhecida) cai na Visão Geral, preservando o comportamento antigo.
function _pageFromHash(){
  const h=(location.hash||'').replace(/^#/,'');
  return PAGE_META[h]?h:'overview';
}
// Deep-link com o SPA já aberto: reage a mudança de âncora na URL.
window.addEventListener('hashchange',()=>{const id=_pageFromHash();if(document.getElementById('page-'+id))showPage(id);});
function updateTopbarTitle(id){
  const meta=PAGE_META[id]||[id,''];
  const t=document.getElementById('topbarTitle');
  const s=document.getElementById('topbarSub');
  if(t)t.textContent=meta[0];
  if(s)s.textContent=meta[1];
}
let _lastPage='',_lastPageSig='';
function _pageSig(id){return JSON.stringify(gfs(id))+'|'+[...msGet('sp_'+id)].sort().join(',')+'|'+[...msGet('ca_'+id)].sort().join(',')+'|'+[...msGet('ti_'+id)].sort().join(',');}
function showPage(id){
  updateTopbarTitle(id);
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n=>n.classList.remove('active'));
  document.getElementById('page-'+id)?.classList.add('active');
  document.getElementById('nav-'+id)?.classList.add('active');
  const sig=_pageSig(id);
  if(id===_lastPage&&sig===_lastPageSig)return;
  _lastPage=id;_lastPageSig=sig;
  renderPage(id);
}
function renderPage(id){
  _filterCache={};_lastPage=id;_lastPageSig=_pageSig(id);
  const rows=filtrarPagina(id);
  if(id==='overview'){renderKPI(rows);renderBankroll(rows);renderROIMonthly(filtrarSemData('overview'),_refMonthKey('overview'));renderOddsDist(rows);renderOvStreaks(rows);renderOvRisco(rows);renderOvHeatmap();}
  else if(id==='sports'){renderSport(rows);}
  else if(id==='casas'){renderCasa(rows);}
  else if(id==='tipsters'){renderTipsters();}
  else if(id==='apostas'){renderApostas();}
  else if(id==='parceiros'){renderParceiros(rows);}
  else if(id==='custos'){renderCustos(rows);}
  else if(id==='custos_tipster'){renderCustoTipster();}
  else if(id==='metrics'){renderMetrics(filtrarPagina('metrics'));}
  else if(id==='resultados'){renderResultados();}
}

// KPI
function buildHTML(){
  const tipsters=[...new Set(DADOS.map(r=>r.tipster).filter(Boolean))].sort();
  const sports=[...new Set(DADOS.map(r=>r.esporte).filter(Boolean))].sort();
  const casas=[...new Set(DADOS.map(r=>r.casa).filter(Boolean))].sort();
  ['overview','sports','casas','apostas','tipsters','resultados','parceiros','custos','metrics'].forEach(p=>{msInit('sp_'+p);msInit('ca_'+p);msInit('ti_'+p);});
  msInit('tipsters');

  document.getElementById('root').innerHTML=`
  <div class="topbar">
    <div class="topbar-left">
      <div class="page-title" id="topbarTitle">Visão Geral</div>
      <div class="page-sub" id="topbarSub">performance consolidada</div>
    </div>
  </div>
  <div class="app">
    <aside class="sidebar">
      <div class="sidebar-brand">
        <img src="brand/sharpen-lockup-dark.svg" class="logo-dark" alt="Sharpen" draggable="false">
        <img src="brand/sharpen-lockup-light.svg" class="logo-light" alt="Sharpen" draggable="false">
      </div>
      <nav class="sidebar-nav">
        <div class="nav-group">Operação</div>
        <a class="nav-item" href="/" style="text-decoration:none" title="Abrir a Extração e Captura — leitura e edição de bilhetes"><svg class="nav-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6"><rect x="1.5" y="1.5" width="13" height="13" rx="1"/><path d="M1.5 5.5h13M1.5 9.5h13M5.5 1.5v13"/></svg>Extração e Captura</a>
        <div class="nav-group">Análise</div>
        ${[
          ['overview','Visão Geral','<rect x="1" y="1" width="6" height="6" rx="1"/><rect x="9" y="1" width="6" height="6" rx="1"/><rect x="1" y="9" width="6" height="6" rx="1"/><rect x="9" y="9" width="6" height="6" rx="1"/>'],
          ['sports','Esportes','<path d="M2 12l4-4 3 3 5-6"/>'],
          ['casas','Bookies','<rect x="1" y="3" width="14" height="10" rx="1"/><path d="M1 8h14M5 3v10"/>'],
          ['apostas','Apostas','<path d="M2 4h12M2 8h12M2 12h8"/><rect x="1" y="2" width="14" height="12" rx="1"/>'],
          ['tipsters','Tipsters','<circle cx="6" cy="5" r="2.5"/><path d="M1 13c0-2.5 2.2-4 5-4s5 1.5 5 4"/><circle cx="12" cy="5" r="2"/><path d="M12 9c1.5.3 3 1.2 3 4"/>'],
        ].map(([id,label,icon])=>`<div class="nav-item" id="nav-${id}" onclick="showPage('${id}')"><svg class="nav-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6">${icon}</svg>${label}</div>`).join('')}
        <div class="nav-group">Resultados</div>
        ${[
          ['resultados','Resultados','<rect x="1" y="1" width="14" height="14" rx="1"/><path d="M1 6h14M1 11h14M6 1v14M11 1v14"/>'],
        ].map(([id,label,icon])=>`<div class="nav-item" id="nav-${id}" onclick="showPage('${id}')"><svg class="nav-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6">${icon}</svg>${label}</div>`).join('')}
        <div class="nav-group">Gestão</div>
        ${[
          ['parceiros','Fornecedores & Parceiros','<rect x="2" y="4" width="12" height="9" rx="1"/><path d="M5 4V3a1 1 0 011-1h4a1 1 0 011 1v1"/>'],
          ['custos','Custos de Contas','<path d="M8 2v12M5 5h4.5a2 2 0 010 4H5m0 0h5a2 2 0 010 4H5"/>'],
          ['custos_tipster','Custo de Tipsters','<circle cx="6" cy="5" r="2.5"/><path d="M1 13.5C1 11 3 10 6 10s5 1 5 3.5"/><circle cx="12" cy="5" r="2"/><path d="M10 13.2c.6-.5 2-.7 2-.7"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="10" y1="10" x2="14" y2="10"/>'],
          ['metrics','Métricas','<path d="M8 2v2M8 12v2M2 8h2m8 0h2"/><circle cx="8" cy="8" r="3"/>'],
        ].map(([id,label,icon])=>`<div class="nav-item" id="nav-${id}" onclick="showPage('${id}')"><svg class="nav-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6">${icon}</svg>${label}</div>`).join('')}
      </nav>
      <div class="sidebar-bottom">
        <div class="last-update" id="lastUpdate"><span class="pulse-dot"></span><span id="lastUpdateText">carregando…</span></div>
        <a class="sb-csv" href="/exportar.csv" title="Baixar toda a base como CSV (backup)"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12M7 10l5 5 5-5M5 21h14"/></svg>Baixar base (CSV)</a>
        <button class="update-btn" id="updateBtn" onclick="loadData(true)"><span class="update-ico">↻</span><span class="update-lbl">Atualizar dados</span></button>
        <div class="sb-endorse">by FDC Capital</div>
      </div>
    </aside>
    <main class="main"><div class="main-content">

      <!-- VISÃO GERAL -->
      <div class="page" id="page-overview">
        ${buildFilters('overview',sports,casas,tipsters)}
        <div class="kpi-grid" id="kpiGrid"></div>
        ${mkCard('bankroll','Resultado Geral','<div style="display:flex;gap:16px;align-items:center;margin-bottom:10px;flex-wrap:wrap"><span style="display:flex;align-items:center;gap:6px;font-size:11px;font-family:var(--font-mono);color:var(--ink-mute)"><span style="display:inline-block;width:20px;height:2px;background:#2E8BFF;border-radius:1px;flex-shrink:0"></span>P/L acumulado</span><span style="display:flex;align-items:center;gap:6px;font-size:11px;font-family:var(--font-mono);color:var(--ink-mute)"><span style="display:inline-block;width:12px;height:12px;background:rgba(43,192,126,.8);border-radius:2px;flex-shrink:0"></span>Dia positivo</span><span style="display:flex;align-items:center;gap:6px;font-size:11px;font-family:var(--font-mono);color:var(--ink-mute)"><span style="display:inline-block;width:12px;height:12px;background:rgba(229,82,75,.8);border-radius:2px;flex-shrink:0"></span>Dia negativo</span></div><div class="chart-wrap" style="min-height:380px"><canvas id="chartBankroll" role="img" aria-label="P/L"></canvas></div>','<span style="margin-left:auto;margin-right:8px;font-family:JetBrains Mono,monospace;font-size:9px;text-transform:uppercase;letter-spacing:.18em;color:var(--ink-soft);opacity:.7">P/L diário · evolução acumulada</span>')}
        ${mkCard('ov_streaks','Cenário Atual','<div id="ovStreaksContent"></div>','<span style="margin-left:auto;display:inline-flex;align-items:center;gap:5px;font-family:var(--font-mono);font-size:9px;text-transform:uppercase;letter-spacing:.18em;color:var(--ink-mute)"><span style="width:5px;height:5px;border-radius:50%;background:var(--d-info)"></span>Dados reais · histórico</span>')}
        ${mkCard('ov_risco','Diagnóstico de Risco','<div id="ovRiscoContent"></div>','<span style="margin-left:auto;display:inline-flex;align-items:center;gap:5px;font-family:var(--font-mono);font-size:9px;text-transform:uppercase;letter-spacing:.18em;color:var(--ink-mute)"><span style="width:5px;height:5px;border-radius:50%;background:var(--d-proj)"></span>Simulado · Monte Carlo · 10.000</span>')}
        ${mkCard('ov_heatmap','Calendário','<div id="ovHeatmapContent"></div>')}
        ${mkCard('roi_monthly','ROI Mensal (%)','<div class="chart-wrap" style="min-height:220px"><canvas id="chartROI" role="img" aria-label="ROI mensal"></canvas></div>')}
        ${mkCard('odds_dist','Distribuição de Odds — Apostas, Win Rate e ROI por faixa','<div class="chart-wrap" style="height:240px"><canvas id="chartOddsDist" role="img" aria-label="Odds dist"></canvas></div>')}
      </div>

      <!-- RESULTADOS (matriz por período + calendário + análises) -->
      <div class="page" id="page-resultados">
        ${buildFilters('resultados',sports,casas,tipsters)}
        <div id="resultadosContent"></div>
      </div>

      <!-- ESPORTES -->
      <div class="page" id="page-sports">
        ${buildFilters('sports',sports,casas)}
        ${mkCard('sport_kpi','Resumo por Esporte','<div id="sportPortfolioKPIs" style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:.75rem;margin-bottom:.75rem"></div><div class="tcard-sort"><span class="tcard-sort__lbl">Ordenar</span><div class="tcard-seg" id="sportSeg"><button data-k="pl" class="active" onclick="sportSortBy(this.dataset.k)">P/L</button><button data-k="roi" onclick="sportSortBy(this.dataset.k)">ROI</button><button data-k="to" onclick="sportSortBy(this.dataset.k)">Turnover</button><button data-k="wr" onclick="sportSortBy(this.dataset.k)">Win Rate</button><button data-k="vol" onclick="sportSortBy(this.dataset.k)">Volume</button></div><button class="tcard-dir" id="sportDir" onclick="sportSortDir()">↓</button></div><div class="tcard-grid" id="sportKpiCards"></div>')}
        ${mkCard('sport_chart','P/L por Esporte','<div id="sportTable"></div><div class="chart-wrap" style="min-height:300px;margin-top:.75rem"><canvas id="chartSport" role="img" aria-label="Esportes"></canvas></div>')}
      </div>

      <!-- CASAS DE APOSTAS -->
      <div class="page" id="page-casas">
        ${buildFilters('casas',sports,casas)}
        ${mkCard('casa_kpi','Bookies — Visão Geral','<div id="casaPortfolioKPIs" style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:.75rem;margin-bottom:.75rem"></div><div class="tcard-sort"><span class="tcard-sort__lbl">Ordenar</span><div class="tcard-seg" id="casaSeg"><button data-k="pl" class="active" onclick="casaSortBy(this.dataset.k)">P/L</button><button data-k="roi" onclick="casaSortBy(this.dataset.k)">ROI</button><button data-k="to" onclick="casaSortBy(this.dataset.k)">Turnover</button><button data-k="wr" onclick="casaSortBy(this.dataset.k)">Win Rate</button><button data-k="vol" onclick="casaSortBy(this.dataset.k)">Volume</button></div><button class="tcard-dir" id="casaDir" onclick="casaSortDir()">↓</button></div><div class="tcard-grid" id="casaKpiCards"></div>')}
      </div>

      <!-- APOSTAS -->
      <div class="page" id="page-apostas">
        ${buildFilters('apostas',sports,casas,tipsters)}
        <div id="apostasKPI" style="margin-bottom:1rem"></div>
        <!-- Busca rápida por coluna -->
        <div style="display:flex;gap:8px;align-items:flex-start;margin-bottom:16px;flex-wrap:wrap;padding:16px 22px;background:var(--surface);border:1px solid var(--line);border-radius:var(--r-lg)">
          <div style="display:flex;gap:6px;flex-wrap:wrap;flex:1">
            ${[['Aposta/Tipo',5],['Descrição/Evento',6],['Esporte',1],['Tipster',2],['Casa',3],['Parceiro',4]].map(([lbl,i])=>`<input class="apostas-filter-inp acf" type="text" placeholder="${lbl}..." oninput="apostasFilter(${i},this.value)">`).join('')}
          </div>
          <button onclick="clearApostasFilters()" style="font-size:10px;padding:5px 10px;background:transparent;border:1px solid var(--line);color:var(--ink-mute);border-radius:5px;cursor:pointer;font-family:'JetBrains Mono',monospace;white-space:nowrap;flex-shrink:0">✕ Limpar</button>
        </div>
        <!-- Tabela de apostas -->
        <div class="btbl-wrap">
          <!-- Header fixo da tabela -->
          <div class="btbl-cols btbl-hdr-row">
            <div class="btbl-th sortable" data-col="0" onclick="apostasSort(0)">Data <span class="sort-arrow">↓</span></div>
            <div class="btbl-th">Aposta / Evento</div>
            <div class="btbl-th">Esporte</div>
            <div class="btbl-th">Tipster</div>
            <div class="btbl-th">Casa · Parceiro</div>
            <div class="btbl-th sortable" data-col="7" onclick="apostasSort(7)">Stake <span class="sort-arrow">↕</span></div>
            <div class="btbl-th sortable" data-col="8" onclick="apostasSort(8)">Odd <span class="sort-arrow">↕</span></div>
            <div class="btbl-th">Resultado</div>
            <div class="btbl-th sortable" data-col="10" onclick="apostasSort(10)" style="text-align:right">P/L <span class="sort-arrow">↕</span></div>
            <div class="btbl-th" style="text-align:center">Ações</div>
          </div>
          <!-- Contador -->
          <div id="apostasCounter" class="btbl-counter"></div>
          <!-- Linhas virtualizadas -->
          <div id="apostasCont" style="height:calc(100vh - 440px);overflow-y:auto">
            <div id="apostasCardWrap"></div>
          </div>
        </div>
      </div>

      <!-- TIPSTERS -->
      <div class="page" id="page-tipsters">
        ${buildFilters('tipsters',sports,casas,tipsters)}
        ${mkCard('tipster_kpi','Tipsters — Visão Geral','<div class="tip-unit-row"><span class="tip-unit-lbl">Exibir P/L em</span><div class="tcard-seg" id="tipUnitSeg"><button data-u="reais" onclick="tipSetUnit(&quot;reais&quot;)">R$</button><button data-u="u" onclick="tipSetUnit(&quot;u&quot;)" title="Resultado em unidades (escada de stake por tipster)">u</button></div></div><div id="tipsterPortfolioKPIs" style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:.75rem;margin-bottom:.75rem"></div><div class="tcard-sort"><span class="tcard-sort__lbl">Ordenar</span><div class="tcard-seg" id="tipsterSeg"><button data-k="pl" class="active" onclick="tipsterSortBy(this.dataset.k)">P/L</button><button data-k="roi" onclick="tipsterSortBy(this.dataset.k)">ROI</button><button data-k="to" onclick="tipsterSortBy(this.dataset.k)">Turnover</button><button data-k="wr" onclick="tipsterSortBy(this.dataset.k)">Win Rate</button><button data-k="vol" onclick="tipsterSortBy(this.dataset.k)">Volume</button></div><button class="tcard-dir" id="tipsterDir" onclick="tipsterSortDir()">↓</button></div><div class="tcard-grid" id="tipsterKpiCards"></div>')}
        ${mkCard('tipster_comp','Comparativo Geral','<div class="tbl-wrap" id="tipsterCompTable"></div>')}
      </div>

      <!-- FORNECEDORES & PARCEIROS -->
      <div class="page" id="page-parceiros">
        ${buildFilters('parceiros',sports,casas)}
        <div id="parcKpiGrid"></div>
        ${mkCard('forn_custo_cards','Custo de Contas por Fornecedor','<div id="fornCustoCards"></div>')}
        <div class="row2">
          ${mkCard('forn_chart','Lucro por Fornecedor','<div class="chart-wrap" style="min-height:220px"><canvas id="chartForn" role="img" aria-label="Fornecedores"></canvas></div>')}
          ${mkCard('forn_table','Resumo por Fornecedor','<div class="tbl-wrap" id="fornTable"></div>')}
        </div>
        ${mkCard('cross_table','Contas por Casa × Fornecedor','<div id="crossTable"></div>')}
        ${mkCard('parc_table','Contas Individuais','<div class="tbl-wrap" id="parcTable"></div>')}
      </div>

      <!-- CUSTOS DE CONTAS -->
      <div class="page" id="page-custos">
        <div id="custosKpi"></div>
        <div id="custosContent">
          ${mkCard('custos_table','Tabela de Custos por Casa × Fornecedor',`
            <p style="font-size:11px;color:var(--ink-mute);margin-bottom:.75rem;font-family:var(--font-sans)">💡 Insira o custo de cada conta por fornecedor/casa. O total é calculado pelo nº de contas. Valores salvos permanentemente no navegador.</p>
            <div id="costTableWrap"></div>`)}
        </div>
      </div>

      <!-- CUSTO DE TIPSTERS -->
      <div class="page" id="page-custos_tipster">
        <div id="custoTipsterContent"></div>
      </div>

      <!-- MÉTRICAS -->
      <div class="page" id="page-metrics">
        ${buildFilters('metrics',sports,casas)}
        <div class="kpi-grid" id="metricsKPI"></div>

        <div class="metric-section">
          <div class="metric-title">Fundamentais</div>

          ${mkCard('m_roi','ROI — Return on Investment',`
            <div class="metric-desc">Mede o retorno percentual sobre tudo o que foi apostado. É a métrica central de rentabilidade no longo prazo: enquanto o P/L diz <i>quanto</i> você ganhou, o ROI diz <i>com que eficiência</i>.</div>
            <div class="metric-formula">ROI (%) = (Lucro Líquido <span class="op">÷</span> Turnover) <span class="op">×</span> 100</div>
            <div class="metric-example">Exemplo: apostou R$ 10.000 (turnover) e lucrou R$ 500 → ROI = +5,00%. A cada R$ 100 apostados, R$ 5 de lucro.</div>
            <div class="metric-note">O Turnover (denominador) exclui apostas Void — a stake anulada é devolvida e não conta como volume.</div>
            <div class="metric-warn">ROI positivo no curto prazo pode ser variância. Use o P-Value como indicador heurístico de apoio — ele não confirma vantagem por si só.</div>`,`<span class="metric-live" id="mv_roi">—</span>`)}

          ${mkCard('m_turnover','Turnover — Volume Apostado',`
            <div class="metric-desc">Volume total efetivamente apostado. É o denominador do ROI e da Stake Média — a base sobre a qual toda a rentabilidade é medida.</div>
            <div class="metric-formula">Turnover = Σ stake &nbsp;(apenas apostas encerradas)</div>
            <div class="metric-note">Apostas Void (anuladas) NÃO entram: a stake é devolvida, então não é volume nem afeta ROI/Stake Média.</div>
            <div class="metric-example">Exemplo: 10 apostas de R$ 100, 1 anulada → Turnover = R$ 900 (não R$ 1.000).</div>`,`<span class="metric-live neu" id="mv_turnover">—</span>`)}

          ${mkCard('m_wr','Win Rate',`
            <div class="metric-desc">Percentual de apostas ganhas entre as encerradas. Indicador de consistência — mas sozinho não diz se há lucro.</div>
            <div class="metric-formula">Win Rate (%) = (W + ½·HW) <span class="op">÷</span> (W <span class="op">+</span> L <span class="op">+</span> ½·HW <span class="op">+</span> ½·HL) <span class="op">×</span> 100</div>
            <div class="metric-note">W = vitória cheia, HW = meia vitória; L = derrota cheia, HL = meia derrota; V (Void) e a metade devolvida de HW/HL ficam de fora.</div>
            <div class="metric-warn">Win Rate alto não garante lucro: ganhar 70% em odd 1,20 ainda pode dar ROI negativo. Leia sempre junto com a Odd Média.</div>`,`<span class="metric-live neu" id="mv_wr">—</span>`)}

          ${mkCard('m_odd','Odd Média Ponderada',`
            <div class="metric-desc">Odd média ponderada pelo tamanho de cada aposta — apostas maiores pesam mais. Mais fiel que a média simples e usada como medida de variância da operação.</div>
            <div class="metric-formula">Odd Média = Σ(odd <span class="op">×</span> stake) <span class="op">÷</span> Σ(stake)</div>
            <div class="metric-example">R$ 1.000 em odd 2,00 e R$ 100 em odd 50,00 → (2.000 + 5.000) ÷ 1.100 = 6,36 (não 26,0).</div>`,`<span class="metric-live neu" id="mv_odd">—</span>`)}

          ${mkCard('m_stake','Stake Média',`
            <div class="metric-desc">Valor médio apostado por aposta encerrada. Ajuda a entender o tamanho típico de exposição em cada evento.</div>
            <div class="metric-formula">Stake Média = Turnover <span class="op">÷</span> nº de apostas encerradas</div>
            <div class="metric-note">Mesmo critério do Turnover: Void fica fora do numerador e do denominador.</div>`,`<span class="metric-live neu" id="mv_stake">—</span>`)}

          ${mkCard('m_pl','P/L Líquido',`
            <div class="metric-desc">Resultado financeiro acumulado: a soma do lucro/prejuízo de cada aposta. É o número que mais importa no fim — entra em todas as métricas de risco abaixo.</div>
            <div class="metric-formula">P/L = Σ lucro de cada aposta</div>
            <div class="metric-note">Como cada resultado vira lucro — W: +stake×(odd−1) · L: −stake · HW: +½·stake×(odd−1) · HL: −½·stake · V: 0 (devolvida).</div>`,`<span class="metric-live" id="mv_pl">—</span>`)}
        </div>

        <div class="metric-section">
          <div class="metric-title">Risco &amp; Drawdown</div>

          ${mkCard('m_mdd','Max Drawdown Real',`
            <div class="metric-desc">A maior queda <b>real</b> que a banca já sofreu, medida do pico ao vale seguinte. Mede o pior momento já vivido — em reais e em percentual da banca.</div>
            <div class="metric-formula">MDD (R$) = máx(pico_acumulado <span class="op">−</span> saldo_atual)<br>MDD (%) = MDD <span class="op">÷</span> (Banca base + pico) <span class="op">×</span> 100</div>
            <div class="metric-note">Calculado sobre o P/L agregado por dia e percorrido em ordem cronológica. A planilha não vem ordenada por data, então a ordenação é obrigatória — R$ e % saem do mesmo episódio pico→vale.</div>
            <div class="metric-example">Saldo +R$ 50.000 (pico) → +R$ 30.000 (vale) → MDD = R$ 20.000.</div>
            <div class="metric-warn">MDD alto = volatilidade alta. Mesmo com ROI positivo, um drawdown grande pode levar ao abandono psicológico da estratégia.</div>`,`<span class="metric-live-wrap"><span class="metric-live d-neg" id="mv_mdd_r">—</span><span class="metric-live d-neg" id="mv_mdd_p">—</span></span>`)}

          ${mkCard('m_rf','Recovery Factor',`
            <div class="metric-desc">Quantas vezes o lucro total cobre a maior queda já vivida (o Max Drawdown real). Quanto maior, mais eficiente a operação em transformar risco realizado em resultado.</div>
            <div class="metric-formula">Recovery Factor = Lucro Total <span class="op">÷</span> MDD Real (R$)</div>
            <div class="term-grid">
              <div class="term-card"><div class="term-name">&gt; 5×</div><div class="term-def">Excelente — o lucro domina largamente a maior queda.</div></div>
              <div class="term-card"><div class="term-name">2× – 5×</div><div class="term-def">Bom — lucro consistente acima do risco vivido.</div></div>
              <div class="term-card"><div class="term-name">1× – 2×</div><div class="term-def">Marginal — risco e retorno próximos.</div></div>
              <div class="term-card"><div class="term-name">&lt; 1×</div><div class="term-def">Ruim — a maior queda superou o lucro acumulado.</div></div>
            </div>`,`<span class="metric-live" id="mv_rf">—</span>`)}

          ${mkCard('m_emdd','Drawdown Médio Esperado',`
            <div class="metric-desc">A queda <b>típica</b> que você deve esperar ao longo da operação. Não é o que aconteceu — é o que tende a acontecer, dada a dispersão dos seus resultados.</div>
            <div class="metric-formula">Drawdown Médio = média dos MDD de 10.000 reamostragens (bootstrap) dos P/L reais</div>
            <div class="metric-note">O bootstrap reamostra seus próprios resultados milhares de vezes — herda a dispersão real da carteira, sem supor distribuição teórica. É o mesmo número exibido no Nível de Solidez dos drill-downs. Assume apostas <b>independentes e de mesma distribuição</b> — pode subestimar a cauda se houver sequências, mudança de regime ou stakes correlacionadas. Indicador heurístico, não garantia de risco máximo.</div>`,`<span class="metric-live d-proj" id="mv_xmdd">—</span>`)}

          ${mkCard('m_p95','Drawdown p95 (risco)',`
            <div class="metric-desc">O cenário <b>ruim-mas-plausível</b> para dimensionar a banca: em 95% das reamostragens a queda ficou abaixo deste valor; só 5% foram piores.</div>
            <div class="metric-formula">Drawdown p95 = percentil 95 dos MDD de 10.000 reamostragens</div>
            <div class="metric-warn">Risco mora na cauda, não na média — o p95 costuma ser ~2× o Drawdown Médio. Use-o para decidir quanta banca segurar.</div>`,`<span class="metric-live d-proj" id="mv_p95">—</span>`)}

          ${mkCard('m_p99','DD Extremo (p99)',`
            <div class="metric-desc">O pior caso plausível: pior que 99% das reamostragens (1 em 100). Serve de margem de segurança extra para a gestão de banca.</div>
            <div class="metric-formula">DD Extremo = percentil 99 dos MDD de 10.000 reamostragens</div>
            <div class="metric-note">Não é "o máximo possível" — é a cauda extrema simulada. Chamado de DD Extremo para não confundir com o Max Drawdown real (fato histórico).</div>`,`<span class="metric-live d-proj" id="mv_p99">—</span>`)}

          ${mkCard('m_pemdd','Profit / Drawdown',`
            <div class="metric-desc">Eficiência da estratégia: quanto lucro para cada unidade de risco típico (análogo ao Calmar). Usa o Drawdown Médio — não o p95 — para casar com o Nível de Solidez.</div>
            <div class="metric-formula">Profit / Drawdown = Lucro Total <span class="op">÷</span> Drawdown Médio Esperado</div>
            <div class="term-grid">
              <div class="term-card"><div class="term-name">&gt; 5</div><div class="term-def">Método excelente. Alto retorno para o risco tomado.</div></div>
              <div class="term-card"><div class="term-name">2 – 5</div><div class="term-def">Método bom. Adequado para operação profissional.</div></div>
              <div class="term-card"><div class="term-name">&lt; 2</div><div class="term-def">Método marginal. Risco elevado em relação ao retorno.</div></div>
              <div class="term-card"><div class="term-name">&lt; 1</div><div class="term-def">Risco maior que retorno. Revisar estratégia.</div></div>
            </div>`,`<span class="metric-live" id="mv_pdd">—</span>`)}
        </div>

        <div class="metric-section">
          <div class="metric-title">Significância — indicadores heurísticos</div>

          ${mkCard('m_pval','P-Value',`
            <div class="metric-desc"><b>Indicador heurístico</b> (simulação bootstrap) de quão improvável seria o seu resultado por acaso, caso você não tivesse vantagem (edge). Quanto menor, mais o resultado se destaca do acaso — mas <b>não é uma prova estatística nem recomendação financeira</b>.</div>
            <div class="metric-formula">P-Value = bootstrap t-test sobre os resíduos de (lucro ~ yₒ <span class="op">·</span> stake), 10.000 reamostragens · H₀ = sem edge</div>
            <div class="metric-note">Estima se o seu lucro por unidade apostada resiste ao acaso — NÃO é um teste sobre o Win Rate. Precisa de ≥ 30 apostas; abaixo disso fica inconclusivo. É um sinal de apoio, não uma garantia de edge.</div>
            <div class="term-grid">
              <div class="term-card"><div class="term-name">&lt; 5% (0,05)</div><div class="term-def">Sinal heurístico de que o resultado se destaca do acaso — não confirma edge sozinho.</div></div>
              <div class="term-card"><div class="term-name">&lt; 1% (0,01)</div><div class="term-def">Sinal forte (heurístico). Sugere destaque do acaso, não prova de edge real.</div></div>
              <div class="term-card"><div class="term-name">&lt; 0,1% (0,001)</div><div class="term-def">Limiar rigoroso da pesquisa acadêmica. Aqui segue sendo indicador, não prova.</div></div>
              <div class="term-card"><div class="term-name">&gt; 5%</div><div class="term-def">Inconclusivo. Amostra insuficiente para destacar do acaso.</div></div>
            </div>
            <div class="metric-warn">Métrica heurística de apoio — não é prova estatística de vantagem nem recomendação de aposta.</div>`,`<span class="metric-live" id="mv_pval">—</span>`)}

          ${mkCard('m_solidez','Nível de Solidez',`
            <div class="metric-desc"><b>Indicador heurístico</b> composto que resume <b>4 pilares</b> numa nota (0 a 1) e numa faixa, como um resumo rápido — <b>não é um selo certificado nem recomendação financeira</b>. Os pesos são calibragem interna, não um padrão estatístico.</div>
            <div class="metric-formula">Score = (Edge<span class="op">×</span>3 + Folga<span class="op">×</span>3 + Amostra<span class="op">×</span>2 + Variância<span class="op">×</span>2) <span class="op">÷</span> 10</div>
            <div class="term-grid">
              <div class="term-card"><div class="term-name">Edge · peso 3</div><div class="term-def">P-Value — o resultado se destaca do acaso? (heurístico)</div></div>
              <div class="term-card"><div class="term-name">Folga · peso 3</div><div class="term-def">Profit / Drawdown — o lucro folga bem sobre o risco típico?</div></div>
              <div class="term-card"><div class="term-name">Amostra · peso 2</div><div class="term-def">Nº de apostas — há histórico suficiente para confiar?</div></div>
              <div class="term-card"><div class="term-name">Variância · peso 2</div><div class="term-def">Odd Média — odds moderadas pesam menos no risco.</div></div>
            </div>
            <div class="metric-note">Faixas: ≥ 0,85 Muito Alta · ≥ 0,65 Alta · ≥ 0,45 Média · ≥ 0,25 Baixa · &lt; 0,25 Muito Baixa.</div>
            <div class="metric-warn">Indicador heurístico de apoio — não é um selo estatístico certificado nem recomendação financeira.</div>`,`<span class="metric-live" id="mv_solidez">—</span>`)}
        </div>

        <div class="metric-section">
          <div class="metric-title">Glossário</div>

          ${mkCard('m_gloss','Resultados &amp; Termos',`
            <div class="term-grid">
              <div class="term-card"><div class="term-name">W — Win</div><div class="term-def">Aposta totalmente ganha. Retorno = stake × odd.</div></div>
              <div class="term-card"><div class="term-name">L — Loss</div><div class="term-def">Aposta totalmente perdida. Retorno = 0. Lucro = −stake.</div></div>
              <div class="term-card"><div class="term-name">HW — Half Win</div><div class="term-def">Metade da stake ganha, metade devolvida (handicap asiático). Retorno = (stake/2)×odd + stake/2.</div></div>
              <div class="term-card"><div class="term-name">HL — Half Loss</div><div class="term-def">Metade da stake perdida, metade devolvida. Retorno = stake/2. Lucro = −stake/2.</div></div>
              <div class="term-card"><div class="term-name">V — Void</div><div class="term-def">Aposta anulada. Stake devolvida integralmente. Fica fora de Turnover, ROI, Stake Média e Win Rate.</div></div>
              <div class="term-card"><div class="term-name">Turnover</div><div class="term-def">Volume apostado: soma das stakes das apostas <b>encerradas</b> (exclui Void).</div></div>
              <div class="term-card"><div class="term-name">Edge / Value</div><div class="term-def">Vantagem real sobre a casa. Existe quando a odd oferecida é maior que a probabilidade real do evento.</div></div>
              <div class="term-card"><div class="term-name">Bankroll</div><div class="term-def">Capital total disponível. O gerenciamento do bankroll define o tamanho das stakes e controla o risco de ruína.</div></div>
              <div class="term-card"><div class="term-name">Banca base</div><div class="term-def">Referência fixa (R$ 100.000) usada como denominador do MDD em % e das simulações.</div></div>
              <div class="term-card"><div class="term-name">Bootstrap</div><div class="term-def">Reamostragem dos próprios resultados, com reposição, milhares de vezes — gera a distribuição de cenários de drawdown.</div></div>
              <div class="term-card"><div class="term-name">Percentil (p95 / p99)</div><div class="term-def">Valor abaixo do qual ficam 95% (ou 99%) dos cenários simulados. Quanto maior o percentil, mais para a cauda do risco.</div></div>
              <div class="term-card"><div class="term-name">Drawdown</div><div class="term-def">Distância entre o pico acumulado e um vale posterior. Mede o tamanho de uma queda.</div></div>
            </div>`)}
        </div>
      </div>

    </div></main>

    <!-- Tipster drill-down popup (T-6) -->
    <div class="analise-popup-overlay" id="tipsterDrillOverlay" onclick="closeTipsterDrill(event)">
      <div class="analise-popup-modal" id="tipsterDrillModal" onclick="event.stopPropagation()">
        <div class="analise-popup-hdr" style="gap:12px;align-items:center">
          <div style="display:flex;align-items:center;flex-shrink:0">
            <img src="brand/sharpen-lockup-dark-tight.svg" height="70" alt="Sharpen" class="drill-brand-logo" style="flex-shrink:0;filter:brightness(1.15)" crossorigin="anonymous">
            <div style="width:1px;height:32px;background:var(--line);flex-shrink:0;margin-left:10px;margin-right:14px"></div>
            <div style="flex-shrink:0;display:flex;flex-direction:column;gap:2px">
              <span style="font-family:var(--font-mono);font-size:9px;text-transform:uppercase;letter-spacing:0.18em;color:var(--ink-mute)">TIPSTER</span>
              <span id="tipsterDrillName" style="font-size:28px;font-weight:800;letter-spacing:-.02em;color:var(--text1);font-family:var(--font-sans);line-height:1.1"></span>
            </div>
          </div>
          <div style="flex:1"></div>
          <button class="no-export copy-drill-btn" onclick="copyDrill()" style="width:32px;height:32px;display:flex;align-items:center;justify-content:center;background:var(--fdc-steel);border:1px solid var(--line);color:var(--accent-2);border-radius:8px;cursor:pointer;flex-shrink:0" title="Copiar como imagem"><svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="1" width="9" height="10" rx="2"/><rect x="1" y="4" width="9" height="10" rx="2"/></svg></button>
          <button class="no-export save-drill-btn" onclick="saveDrill()" style="width:32px;height:32px;display:flex;align-items:center;justify-content:center;background:var(--fdc-steel);border:1px solid var(--line);color:var(--ink-soft);border-radius:8px;cursor:pointer;flex-shrink:0" title="Baixar PNG"><svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M7.5 2v8"/><path d="M4.5 7l3 3 3-3"/><path d="M2 13h11"/></svg></button>
          <button class="no-export" onclick="closeTipsterDrill()" style="width:32px;height:32px;display:flex;align-items:center;justify-content:center;background:var(--fdc-steel);border:1px solid var(--line);color:var(--ink-soft);border-radius:8px;cursor:pointer;font-size:15px;flex-shrink:0" title="Fechar">✕</button>
        </div>
        <div id="tipsterDrillPeriodBar" class="no-export" style="padding:.6rem 1.5rem;border-bottom:1px solid var(--line);display:flex;flex-wrap:wrap;gap:6px;align-items:center">
          <button class="qbtn" data-inherit="1" style="display:none" onclick="setDrillInherit()" title="Período filtrado no painel"></button>
          <button class="qbtn" data-qt="hoje" onclick="setDrillType('hoje')">Hoje</button>
          <button class="qbtn" data-qt="wtd" onclick="setDrillType('wtd')">WTD</button>
          <button class="qbtn" data-qt="mtd" onclick="setDrillType('mtd')">MTD</button>
          <button class="qbtn" data-qt="ytd" onclick="setDrillType('ytd')">YTD</button>
          <button class="qbtn" data-days="7" onclick="setDrillQuick(7)">7d</button>
          <button class="qbtn" data-days="30" onclick="setDrillQuick(30)">30d</button>
          <button class="qbtn" data-days="90" onclick="setDrillQuick(90)">90d</button>
          <button class="qbtn" data-all="1" onclick="setDrillAll()">Tudo</button>
        </div>
        <div id="tipsterDrillBody"></div>
      </div>
    </div>

    <!-- Bookie drill-down popup -->
    <div class="analise-popup-overlay" id="casaDrillOverlay" onclick="closeCasaDrill(event)">
      <div class="analise-popup-modal" id="casaDrillModal" onclick="event.stopPropagation()">
        <div class="analise-popup-hdr" style="gap:12px;align-items:center">
          <div style="display:flex;align-items:center;flex-shrink:0">
            <img src="brand/sharpen-lockup-dark-tight.svg" height="70" alt="Sharpen" class="drill-brand-logo" style="flex-shrink:0;filter:brightness(1.15)" crossorigin="anonymous">
            <div style="width:1px;height:32px;background:var(--line);flex-shrink:0;margin-left:10px;margin-right:14px"></div>
            <div style="flex-shrink:0;display:flex;flex-direction:column;gap:2px">
              <span style="font-family:var(--font-mono);font-size:9px;text-transform:uppercase;letter-spacing:0.18em;color:var(--ink-mute)">BOOKIE</span>
              <div style="display:flex;align-items:center;gap:8px;line-height:1">
                <span id="casaDrillChip"></span>
                <span id="casaDrillName" style="font-size:22px;font-weight:800;letter-spacing:-.02em;color:var(--text1);font-family:var(--font-sans)"></span>
              </div>
            </div>
          </div>
          <div style="flex:1"></div>
          <button class="no-export copy-casa-drill-btn" onclick="copyCasaDrill()" style="width:32px;height:32px;display:flex;align-items:center;justify-content:center;background:var(--fdc-steel);border:1px solid var(--line);color:var(--accent-2);border-radius:8px;cursor:pointer;flex-shrink:0" title="Copiar como imagem"><svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="1" width="9" height="10" rx="2"/><rect x="1" y="4" width="9" height="10" rx="2"/></svg></button>
          <button class="no-export save-casa-drill-btn" onclick="saveCasaDrill()" style="width:32px;height:32px;display:flex;align-items:center;justify-content:center;background:var(--fdc-steel);border:1px solid var(--line);color:var(--ink-soft);border-radius:8px;cursor:pointer;flex-shrink:0" title="Baixar PNG"><svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M7.5 2v8"/><path d="M4.5 7l3 3 3-3"/><path d="M2 13h11"/></svg></button>
          <button class="no-export" onclick="closeCasaDrill()" style="width:32px;height:32px;display:flex;align-items:center;justify-content:center;background:var(--fdc-steel);border:1px solid var(--line);color:var(--ink-soft);border-radius:8px;cursor:pointer;font-size:15px;flex-shrink:0" title="Fechar">✕</button>
        </div>
        <div id="casaDrillPeriodBar" class="no-export" style="padding:.6rem 1.5rem;border-bottom:1px solid var(--line);display:flex;flex-wrap:wrap;gap:6px;align-items:center">
          <button class="qbtn" data-inherit="1" style="display:none" onclick="setDrillCasaInherit()" title="Período filtrado no painel"></button>
          <button class="qbtn" data-qt="hoje" onclick="setDrillCasaType('hoje')">Hoje</button>
          <button class="qbtn" data-qt="wtd" onclick="setDrillCasaType('wtd')">WTD</button>
          <button class="qbtn" data-qt="mtd" onclick="setDrillCasaType('mtd')">MTD</button>
          <button class="qbtn" data-qt="ytd" onclick="setDrillCasaType('ytd')">YTD</button>
          <button class="qbtn" data-days="7" onclick="setDrillCasaQuick(7)">7d</button>
          <button class="qbtn" data-days="30" onclick="setDrillCasaQuick(30)">30d</button>
          <button class="qbtn" data-days="90" onclick="setDrillCasaQuick(90)">90d</button>
          <button class="qbtn active" data-all="1" onclick="setDrillCasaAll()">Tudo</button>
        </div>
        <div id="casaDrillBody"></div>
      </div>
    </div>

    <!-- Sport drill-down popup -->
    <div class="analise-popup-overlay" id="sportDrillOverlay" onclick="closeSportDrill(event)">
      <div class="analise-popup-modal" id="sportDrillModal" onclick="event.stopPropagation()">
        <div class="analise-popup-hdr" style="gap:12px;align-items:center">
          <div style="display:flex;align-items:center;flex-shrink:0">
            <img src="brand/sharpen-lockup-dark-tight.svg" height="70" alt="Sharpen" class="drill-brand-logo" style="flex-shrink:0;filter:brightness(1.15)" crossorigin="anonymous">
            <div style="width:1px;height:32px;background:var(--line);flex-shrink:0;margin-left:10px;margin-right:14px"></div>
            <div style="flex-shrink:0;display:flex;flex-direction:column;gap:2px">
              <span style="font-family:var(--font-mono);font-size:9px;text-transform:uppercase;letter-spacing:0.18em;color:var(--ink-mute)">ESPORTE</span>
              <div style="display:flex;align-items:center;gap:8px;line-height:1">
                <span id="sportDrillChip"></span>
                <span id="sportDrillName" style="font-size:22px;font-weight:800;letter-spacing:-.02em;color:var(--text1);font-family:var(--font-sans)"></span>
              </div>
            </div>
          </div>
          <div style="flex:1"></div>
          <button class="no-export copy-sport-drill-btn" onclick="copySportDrill()" style="width:32px;height:32px;display:flex;align-items:center;justify-content:center;background:var(--fdc-steel);border:1px solid var(--line);color:var(--accent-2);border-radius:8px;cursor:pointer;flex-shrink:0" title="Copiar como imagem"><svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="1" width="9" height="10" rx="2"/><rect x="1" y="4" width="9" height="10" rx="2"/></svg></button>
          <button class="no-export save-sport-drill-btn" onclick="saveSportDrill()" style="width:32px;height:32px;display:flex;align-items:center;justify-content:center;background:var(--fdc-steel);border:1px solid var(--line);color:var(--ink-soft);border-radius:8px;cursor:pointer;flex-shrink:0" title="Baixar PNG"><svg width="15" height="15" viewBox="0 0 15 15" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M7.5 2v8"/><path d="M4.5 7l3 3 3-3"/><path d="M2 13h11"/></svg></button>
          <button class="no-export" onclick="closeSportDrill()" style="width:32px;height:32px;display:flex;align-items:center;justify-content:center;background:var(--fdc-steel);border:1px solid var(--line);color:var(--ink-soft);border-radius:8px;cursor:pointer;font-size:15px;flex-shrink:0" title="Fechar">✕</button>
        </div>
        <div id="sportDrillPeriodBar" class="no-export" style="padding:.6rem 1.5rem;border-bottom:1px solid var(--line);display:flex;flex-wrap:wrap;gap:6px;align-items:center">
          <button class="qbtn" data-inherit="1" style="display:none" onclick="setDrillSportInherit()" title="Período filtrado no painel"></button>
          <button class="qbtn" data-qt="hoje" onclick="setDrillSportType('hoje')">Hoje</button>
          <button class="qbtn" data-qt="wtd" onclick="setDrillSportType('wtd')">WTD</button>
          <button class="qbtn" data-qt="mtd" onclick="setDrillSportType('mtd')">MTD</button>
          <button class="qbtn" data-qt="ytd" onclick="setDrillSportType('ytd')">YTD</button>
          <button class="qbtn" data-days="7" onclick="setDrillSportQuick(7)">7d</button>
          <button class="qbtn" data-days="30" onclick="setDrillSportQuick(30)">30d</button>
          <button class="qbtn" data-days="90" onclick="setDrillSportQuick(90)">90d</button>
          <button class="qbtn active" data-all="1" onclick="setDrillSportAll()">Tudo</button>
        </div>
        <div id="sportDrillBody"></div>
      </div>
    </div>

    <!-- Editar aposta (página Apostas) — edita os 10 campos via PATCH /bilhetes/{id} -->
    <div class="analise-popup-overlay" id="apEditOverlay" onclick="fecharEdicaoApostas(event)">
      <div class="analise-popup-modal" id="apEditModal" style="max-width:560px" onclick="event.stopPropagation()">
        <div class="analise-popup-hdr" style="align-items:center">
          <div style="flex-shrink:0;display:flex;flex-direction:column;gap:2px">
            <span style="font-family:var(--font-mono);font-size:9px;text-transform:uppercase;letter-spacing:0.18em;color:var(--ink-mute)">EDITAR</span>
            <span style="font-size:20px;font-weight:800;letter-spacing:-.02em;color:var(--text1);font-family:var(--font-sans);line-height:1.1">Aposta</span>
          </div>
          <div style="flex:1"></div>
          <button onclick="fecharEdicaoApostas()" style="width:32px;height:32px;display:flex;align-items:center;justify-content:center;background:var(--fdc-steel);border:1px solid var(--line);color:var(--ink-soft);border-radius:8px;cursor:pointer;font-size:15px;flex-shrink:0" title="Fechar">✕</button>
        </div>
        <div style="padding:var(--sp-5) var(--sp-6);display:grid;grid-template-columns:1fr 1fr;gap:12px 14px">
          <div class="apedit-field"><label class="apedit-label" for="ap-ed-data">Data</label><input class="apedit-inp" id="ap-ed-data" type="text" placeholder="DD/MM/AAAA" spellcheck="false" autocomplete="off"></div>
          <div class="apedit-field"><label class="apedit-label" for="ap-ed-resultado">Resultado</label>
            <select class="apedit-inp" id="ap-ed-resultado">
              <option value="">— aberta —</option>
              <option value="W">W · Green</option>
              <option value="L">L · Red</option>
              <option value="V">V · Void</option>
              <option value="HW">HW · Meio green</option>
              <option value="HL">HL · Meio red</option>
            </select>
          </div>
          <div class="apedit-field"><label class="apedit-label" for="ap-ed-esporte">Esporte</label><input class="apedit-inp" id="ap-ed-esporte" type="text" spellcheck="false" autocomplete="off"></div>
          <div class="apedit-field"><label class="apedit-label" for="ap-ed-tipster">Tipster</label><input class="apedit-inp" id="ap-ed-tipster" type="text" spellcheck="false" autocomplete="off"></div>
          <div class="apedit-field"><label class="apedit-label" for="ap-ed-casa">Casa</label><input class="apedit-inp" id="ap-ed-casa" type="text" spellcheck="false" autocomplete="off"></div>
          <div class="apedit-field"><label class="apedit-label" for="ap-ed-parceiro">Parceiro</label><input class="apedit-inp" id="ap-ed-parceiro" type="text" spellcheck="false" autocomplete="off"></div>
          <div class="apedit-field"><label class="apedit-label" for="ap-ed-stake">Stake</label><input class="apedit-inp" id="ap-ed-stake" type="text" spellcheck="false" autocomplete="off"></div>
          <div class="apedit-field"><label class="apedit-label" for="ap-ed-odd">Odd</label><input class="apedit-inp" id="ap-ed-odd" type="text" spellcheck="false" autocomplete="off"></div>
          <div class="apedit-field" style="grid-column:1/-1"><label class="apedit-label" for="ap-ed-aposta">Aposta / Tipo</label><input class="apedit-inp" id="ap-ed-aposta" type="text" spellcheck="false" autocomplete="off"></div>
          <div class="apedit-field" style="grid-column:1/-1"><label class="apedit-label" for="ap-ed-descricao">Descrição / Evento</label><textarea class="apedit-inp" id="ap-ed-descricao" spellcheck="false"></textarea></div>
        </div>
        <div id="apEditErr" style="display:none;margin:0 var(--sp-6) 4px;color:var(--neg);font-size:12px;font-family:var(--font-sans)"></div>
        <div style="display:flex;align-items:center;gap:8px;padding:var(--sp-4) var(--sp-6);border-top:1px solid var(--line)">
          <button class="apedit-btn-ghost" style="border-color:transparent;color:var(--neg)" onclick="deletarApostas()">🗑 Deletar</button>
          <div style="flex:1"></div>
          <button class="apedit-btn-ghost" onclick="fecharEdicaoApostas()">Cancelar</button>
          <button class="apedit-btn-primary" onclick="salvarEdicaoApostas()">Salvar</button>
        </div>
      </div>
    </div>
  </div>`;

  showPage(_pageFromHash());
  initBtblResize();
}


// ── CUSTO DE TIPSTERS ───────────────────────────────────────────────────────
const CT_KEY='custoTipsterData'; // {tipster: {YYYY-MM: value}, ...}
const CG_KEY='custoGeralData';   // [{id, tipo, values: {YYYY-MM: value}}, ...]
let ctData={}, cgData=[];

function ctLoad(){
  try{ctData=JSON.parse(localStorage.getItem(CT_KEY)||'{}');}catch(e){ctData={};}
  try{cgData=JSON.parse(localStorage.getItem(CG_KEY)||'[]');}catch(e){cgData=[];}
}
function ctSave(){localStorage.setItem(CT_KEY,JSON.stringify(ctData));localStorage.setItem(CG_KEY,JSON.stringify(cgData));}

function ctGetMonths(){
  // Last 6 months ending current month
  const months=[];const now=new Date();
  for(let i=5;i>=0;i--){const d=new Date(now.getFullYear(),now.getMonth()-i,1);months.push(`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}`);}
  return months;
}
function ctFmtMonth(ym){const[y,m]=ym.split('-');return MESES_CURTOS[parseInt(m)-1]+'/'+y.slice(2);}

window.saveCT=function(el){
  const t=el.dataset.ct, m=el.dataset.ctm, v=el.value.trim();
  if(!ctData[t])ctData[t]={};
  if(v)ctData[t][m]=v; else delete ctData[t][m];
  ctSave(); renderCustoTipster();
};
window.saveCG=function(el){
  const idx=parseInt(el.dataset.cgidx), m=el.dataset.cgm, v=el.value.trim();
  if(!cgData[idx])return;
  if(!cgData[idx].values)cgData[idx].values={};
  if(v)cgData[idx].values[m]=v; else delete cgData[idx].values[m];
  ctSave(); renderCustoTipster();
};
window.saveCGTipo=function(el){
  const idx=parseInt(el.dataset.cgidx);
  if(!cgData[idx])return;
  cgData[idx].tipo=el.value.trim();
  ctSave();
};
window.addCG=function(){
  cgData.push({id:Date.now(),tipo:'',values:{}});
  ctSave(); renderCustoTipster();
};
window.deleteCG=function(idx){
  cgData.splice(idx,1);
  ctSave(); renderCustoTipster();
};

// ── Cache local (IndexedDB) ──────────────────────────────────────────────────
// O payload do Apps Script tem ~8 MB — excede o limite do localStorage (~5 MB),
// por isso o cache de dados vai em IndexedDB. Guarda o json.data CRU (re-normaliza
// ao ler, para acompanhar mudanças no normalizeDados). Estratégia: stale-while-
// revalidate — boot instantâneo com o último dado salvo + atualização em 2º plano.
const _IDB_NAME='fdc_dash', _IDB_STORE='kv', _IDB_KEY='dados_v1';
function _idbOpen(){
  return new Promise((resolve,reject)=>{
    let req;
    try{req=indexedDB.open(_IDB_NAME,1);}catch(e){return reject(e);}
    req.onupgradeneeded=()=>{const db=req.result;if(!db.objectStoreNames.contains(_IDB_STORE))db.createObjectStore(_IDB_STORE);};
    req.onsuccess=()=>resolve(req.result);
    req.onerror=()=>reject(req.error);
  });
}
function _idbGetData(){
  return _idbOpen().then(db=>new Promise((resolve,reject)=>{
    const rq=db.transaction(_IDB_STORE,'readonly').objectStore(_IDB_STORE).get(_IDB_KEY);
    rq.onsuccess=()=>resolve(rq.result||null);
    rq.onerror=()=>reject(rq.error);
  }));
}
function _idbSetData(val){
  return _idbOpen().then(db=>new Promise((resolve,reject)=>{
    const tx=db.transaction(_IDB_STORE,'readwrite');
    tx.objectStore(_IDB_STORE).put(val,_IDB_KEY);
    tx.oncomplete=()=>resolve();
    tx.onerror=()=>reject(tx.error);
  }));
}
// Mostra QUANDO O SERVIDOR reconstruiu os dados (builtAt), não quando o navegador buscou.
// Assim, se o gatilho rebuildCache travar, o horário fica visivelmente velho.
function _setLastUpdate(ms,updating){
  const lu=document.getElementById('lastUpdateText');
  if(!lu)return;
  if(ms){
    const d=new Date(ms);
    lu.textContent='último sync: '+d.toLocaleString('pt-BR',{day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'});
  }else{
    lu.textContent=updating?'sincronizando…':'carregando…';
  }
}

// Feedback do botão "Atualizar dados": enquanto o refresh roda, o ↻ gira e o
// botão fica desabilitado ("Atualizando…"). Antes o botão parecia morto — nenhum
// sinal de que o clique disparou algo. Duração mínima (600ms) evita piscada.
function _setUpdating(on){
  const b=document.getElementById('updateBtn');
  if(!b)return;
  const lbl=b.querySelector('.update-lbl');
  if(on){
    window._updT0=Date.now();
    b.classList.add('is-loading');
    b.disabled=true;
    if(lbl)lbl.textContent='Atualizando…';
    return;
  }
  const done=()=>{
    b.classList.remove('is-loading');
    b.disabled=false;
    if(lbl)lbl.textContent='Atualizar dados';
  };
  const dt=Date.now()-(window._updT0||0);
  if(dt<600)setTimeout(done,600-dt);else done();
}
function _errBanner(msg){
  const banner=document.createElement('div');
  banner.style.cssText='position:fixed;top:44px;left:220px;right:0;z-index:9998;background:rgba(229,82,75,0.12);border-bottom:1px solid rgba(229,82,75,0.3);padding:8px 20px;display:flex;align-items:center;gap:10px;font-size:12px;font-family:var(--font-mono);color:#E5524B';
  banner.innerHTML=`<span>⚠ Não foi possível carregar os dados — ${msg}</span><button onclick="loadData(true)" style="margin-left:auto;padding:4px 12px;background:transparent;border:1px solid rgba(229,82,75,0.4);color:#E5524B;border-radius:4px;cursor:pointer;font-size:11px;font-family:var(--font-mono)">↻ Tentar novamente</button><button onclick="this.parentElement.remove()" style="padding:2px 8px;background:transparent;border:none;color:#E5524B;cursor:pointer;font-size:14px">×</button>`;
  document.body.appendChild(banner);
}

// Máscara de revalidação: enquanto o cache velho é substituído pelo dado fresco
// (~20-30s), escurece o gráfico e mostra um pill "sincronizando…" para o número
// desatualizado não ser lido como real. Só no boot por cache (não no refresh manual).
function _revalOn(){
  document.body.classList.add('is-revalidating');
  if(!document.getElementById('revalPill')){
    const p=document.createElement('div');
    p.id='revalPill';p.className='reval-pill';p.setAttribute('aria-live','polite');
    p.innerHTML='<span class="reval-spin"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-2.64-6.36"/><path d="M21 4v5h-5"/></svg></span><span>Sincronizando dados… os números podem estar desatualizados</span>';
    document.body.appendChild(p);
  }
}
function _revalOff(){
  document.body.classList.remove('is-revalidating');
  document.getElementById('revalPill')?.remove();
}

async function loadData(force){
  const _rebuild=!document.getElementById('page-overview'); // primeira carga? (DOM ainda não montado)
  let servedFromCache=false;

  // ── 1) Primeira carga: tenta o cache local para boot instantâneo ───────────
  if(_rebuild){
    try{
      const cached=await _idbGetData();
      if(cached&&Array.isArray(cached.data)&&cached.data.length){
        aplicarFeed(cached.data);
        auditCasas(DADOS);
        buildHTML();
        applyAparencia();
        window._dataLoadMs=cached.savedAt||Date.now();
        window._dataBuiltMs=cached.builtAt||cached.savedAt||Date.now();
        _setLastUpdate(window._dataBuiltMs,true); // mostra a hora de build do servidor + "atualizando…"
        _revalOn(); // gráfico provisório até o dado fresco chegar
        servedFromCache=true;
      }
    }catch(e){/* IndexedDB indisponível (modo privado etc.) — segue para o loader */}

    // Sem cache: loader original (0→90% calibrado para o fetch longo)
    if(!servedFromCache){
      document.getElementById('root').innerHTML=`<div class="loader" id="loaderEl"><div class="loader-content"><img src="brand/sharpen-lockup-dark.svg" alt="Sharpen" style="width:676px;max-width:88vw;display:block;object-fit:contain;opacity:.97" draggable="false"><div class="loader-bottom"><div class="loader-bar-wrap"><div class="loader-bar-fill p1" id="loaderBar"></div></div><div class="loader-pct" id="loaderPct">0%</div></div></div></div>`;
      const _pctT0=Date.now();
      (function _tick(){const pEl=document.getElementById('loaderPct');if(!pEl)return;const t=Math.min((Date.now()-_pctT0)/90000,1);const e=1-Math.pow(1-t,3);pEl.textContent=Math.round(e*90)+'%';if(t<1)requestAnimationFrame(_tick);})();
    }
  }

  // ── 2) Busca dados frescos (em paralelo com a UI já visível, quando houver cache) ──
  if(force)_setUpdating(true);                            // clique manual: gira o botão
  if(!_rebuild)_setLastUpdate(window._dataBuiltMs,true);  // refresh manual: feedback "sincronizando…"
  let _fetchErr=null;
  try{
    // Boot/revalidação em 2º plano usam o cache rápido do Drive; o clique manual em
    // "Atualizar dados" (force=true) força reconstrução ao vivo da planilha (?refresh=1).
    const url=force?APPS_SCRIPT_URL+(APPS_SCRIPT_URL.includes('?')?'&':'?')+'refresh=1':APPS_SCRIPT_URL;
    const res=await fetch(url);
    const json=await res.json();
    if(!json.ok)throw new Error(json.error||'Erro desconhecido');
    // dono efetivo: o store de custos é escopado por ele (isolamento entre usuários).
    // Fallback '_' (namespace vazio) se ausente — nunca cai no store de outro dono.
    window.__dono=json.dono||(json.operadores&&json.operadores[0])||'_';
    if(typeof loadCusto==='function')loadCusto();
    aplicarFeed(json.data);
    auditCasas(DADOS);
    // builtAt = quando o servidor reconstruiu o cache (fonte de verdade da frescura dos dados)
    window._dataBuiltMs=json.builtAt?Date.parse(json.builtAt):Date.now();
    _idbSetData({data:json.data,savedAt:Date.now(),builtAt:window._dataBuiltMs}).catch(()=>{}); // grava cache sem bloquear
  }catch(err){
    _fetchErr=err.message||'Falha na conexão';
    if(!servedFromCache)DADOS=[]; // com cache, mantém o dado velho; sem cache, zera
  }

  // ── 3a) DOM já montado (cache servido OU refresh manual): atualiza silencioso ──
  if(servedFromCache||!_rebuild){
    if(force)_setUpdating(false); // encerra o giro do botão (sucesso ou erro)
    _revalOff(); // dado fresco chegou (ou falhou) → tira a máscara de sincronização
    if(!_fetchErr){
      window._dataLoadMs=Date.now();
      _setLastUpdate(window._dataBuiltMs,false);
      if(_lastPage)renderPage(_lastPage); // redesenha a view ativa com o dado novo
    }else{
      _setLastUpdate(window._dataBuiltMs,false); // mantém o que já está na tela
      if(!servedFromCache)_errBanner(_fetchErr); // refresh manual falhou e não há cache em tela
    }
    return;
  }

  // ── 3b) Primeira carga sem cache: completa o loader, faz fade e monta a UI ──
  const bar=document.getElementById('loaderBar');
  const loader=document.getElementById('loaderEl');
  const pctEl=document.getElementById('loaderPct');
  if(pctEl)pctEl.textContent='100%';
  if(bar){bar.classList.remove('p1');bar.style.width='100%';}
  await new Promise(r=>setTimeout(r,320));
  if(loader){loader.style.opacity='0';}
  await new Promise(r=>setTimeout(r,360));
  buildHTML();
  applyAparencia();
  if(_fetchErr){
    _errBanner(_fetchErr);
  }else{
    _setLastUpdate(window._dataBuiltMs,false);
    window._dataLoadMs=Date.now();
  }
}
// Apply persisted Aparência before first render (theme, density, etc.)
applyAparencia();
loadData();

// MetricTooltip global — appendado ao body para escapar de backdrop-filter stacking contexts
const _gTip=(()=>{const d=document.createElement('div');d.className='metric-tip';d.style.cssText='display:none;position:fixed;z-index:99999;pointer-events:none;';document.body.appendChild(d);return d;})();
function _showTip(btn){
  const anchor=btn.closest('.tip-anchor');
  if(!anchor)return;
  const src=anchor.querySelector('.metric-tip');
  if(!src)return;
  _gTip.innerHTML=src.innerHTML;
  _gTip.style.visibility='hidden';
  _gTip.style.display='block';
  const th=_gTip.offsetHeight;
  _gTip.style.visibility='';
  const r=btn.getBoundingClientRect();
  let left=r.left-4;
  if(left+286>window.innerWidth-8)left=window.innerWidth-294;
  if(left<8)left=8;
  let top=r.bottom+6;
  const flipped=top+th>window.innerHeight-8;
  if(flipped)top=r.top-th-6;
  if(top<8)top=8;
  _gTip.style.top=top+'px';
  _gTip.style.left=left+'px';
  const caret=_gTip.querySelector('.metric-tip__caret');
  if(caret){
    if(flipped){caret.style.display='none';}
    else{caret.style.display='';caret.style.left=Math.max(10,Math.min(r.left+r.width/2-left-6,260))+'px';}
  }
}
document.addEventListener('mouseover',function(e){
  const btn=e.target.closest('.metric-info');if(!btn)return;_showTip(btn);
});
document.addEventListener('mouseout',function(e){
  const btn=e.target.closest('.metric-info');if(!btn)return;_gTip.style.display='none';
});
document.addEventListener('focusin',function(e){
  const btn=e.target.closest('.metric-info');if(!btn)return;_showTip(btn);
});
document.addEventListener('focusout',function(e){
  const btn=e.target.closest('.metric-info');if(!btn)return;_gTip.style.display='none';
});
document.addEventListener('keydown',function(e){
  if(e.key==='Escape'){ _gTip.style.display='none'; _calTip.style.display='none'; }
});

// Tooltip para células do calendário — segue o cursor, visual idêntico ao .metric-tip
const _calTip=(()=>{const d=document.createElement('div');d.className='cal-tip';document.body.appendChild(d);return d;})();
function _showCalTip(cell,cx,cy){
  const pl  =parseFloat(cell.dataset.pl||0);
  const n   =parseInt(cell.dataset.n||0);
  const tv  =parseFloat(cell.dataset.turnover||0);
  const W   =parseInt(cell.dataset.wins||0);
  const HW  =parseInt(cell.dataset.hw||0);
  const L   =parseInt(cell.dataset.losses||0);
  const HL  =parseInt(cell.dataset.hl||0);
  const date=cell.dataset.date||'';
  const roi =tv>0?pl/tv*100:0;
  const settled=W+HW+L+HL;
  const wr  =wrFrac(W+HW,HW,HL,settled);
  const sm  =n>0?tv/n:0;
  const[y,m,d2]=date.split('-');
  const DIAS_SHORT=['DOM','SEG','TER','QUA','QUI','SEX','SÁB'];
  const dow=new Date(parseInt(y),parseInt(m)-1,parseInt(d2)).getDay();
  const dateFmt=`${DIAS_SHORT[dow]}, ${d2} ${(MESES_CURTOS[parseInt(m)-1]||'').toUpperCase()}`;
  const plSign=pl>0?'+':pl<0?'−':'';
  const plCls =pl>0?'pos':pl<0?'neg':'';
  const roiSign=roi>0?'+':roi<0?'−':'';
  const roiCls=roi>=0?'pos':'neg';
  const nf=v=>Math.abs(Math.round(v)).toLocaleString('pt-BR');
  _calTip.innerHTML=`
    <div class="ct-date">${dateFmt}</div>
    <div class="ct-pl ${plCls}"><span class="cur">${plSign}R$</span>${nf(pl)}</div>
    <div class="ct-sep"></div>
    <div class="ct-grid">
      <div class="ct-item"><span class="lbl">ROI</span><span class="val ${roiCls}">${roiSign}${Math.abs(roi).toFixed(2).replace('.',',')}%</span></div>
      <div class="ct-item"><span class="lbl">WIN RATE</span><span class="val">${wr.toFixed(1).replace('.',',')}%</span></div>
      <div class="ct-item"><span class="lbl">Apostas</span><span class="val">${n}</span></div>
      <div class="ct-item"><span class="lbl">Turnover</span><span class="val"><span class="cur">R$</span>${nf(tv)}</span></div>
      <div class="ct-item"><span class="lbl">Stake Méd.</span><span class="val"><span class="cur">R$</span>${nf(sm)}</span></div>
      <div class="ct-item"><span class="lbl">W / L</span><span class="val"><b class="w">${W}</b> · <b class="l">${L}</b></span></div>
    </div>`;
  _calTip.style.display='block';
  _calTip.style.visibility='hidden';
  const tw=_calTip.offsetWidth,th=_calTip.offsetHeight;
  _calTip.style.visibility='';
  let left=cx+14;
  if(left+tw>window.innerWidth-8)left=cx-tw-14;
  if(left<8)left=8;
  let top=cy+14;
  if(top+th>window.innerHeight-8)top=cy-th-14;
  if(top<8)top=8;
  _calTip.style.left=left+'px';
  _calTip.style.top=top+'px';
}
document.addEventListener('mouseover',function(e){
  const cell=e.target.closest('.cal__cell.has');if(!cell)return;
  _showCalTip(cell,e.clientX,e.clientY);
});
document.addEventListener('mousemove',function(e){
  if(!_calTip.style.display||_calTip.style.display==='none')return;
  const cell=e.target.closest('.cal__cell.has');
  if(!cell){_calTip.style.display='none';return;}
  _showCalTip(cell,e.clientX,e.clientY);
});
document.addEventListener('mouseout',function(e){
  if(e.target.closest('.cal__cell'))_calTip.style.display='none';
});

