// ── Núcleo do Monte Carlo — FONTE ÚNICA da matemática (página + Web Worker) ──
// mulberry32, _calcMCdrawdownRaw e _calcPValueMCraw vivem AQUI e em nenhum outro
// lugar. A página carrega este arquivo por <script src="assets/js/mc-core.js">; o
// worker carrega o MESMO arquivo por importScripts (ver mc-worker.js). Os dois
// caminhos rodam byte a byte o mesmo código — número idêntico, sem duplicar fórmula.
//
// POR QUE ESTE ARQUIVO EXISTE (s217): antes o worker era GERADO em tempo de execução
// a partir de `.toString()` das funções, embrulhado num Blob e instanciado com
// `new Worker(URL.createObjectURL(blob))`. Isso funcionava em 29/06 e morreu em 03/07,
// quando a CSP entrou: `default-src 'self'` sem `worker-src` NÃO permite `blob:` como
// worker → o construtor era bloqueado, o `onerror` zerava `_mcWorker` e todo cálculo
// caía no fallback SÍNCRONO, na thread principal. Calado, porque o fallback devolve o
// número certo. Medido na base do Feca (30.851 apostas): long task de 52,7 s no boot
// do dashboard — a aba congelava e o Chrome oferecia "aguardar ou fechar".
// Worker servido como arquivo de mesma origem cabe em `script-src 'self'` sem afrouxar
// a CSP. Travado em tests/test_monte_carlo_worker.py.
//
// Estas funções são PURAS e determinísticas (semente derivada dos dados) — a mesma
// entrada dá o mesmo número em qualquer tela e nos dois caminhos de execução.

function mulberry32(a){return function(){a|=0;a=(a+0x6D2B79F5)|0;var t=Math.imul(a^(a>>>15),1|a);t=(t+Math.imul(t^(t>>>7),61|t))^t;return((t^(t>>>14))>>>0)/4294967296;};}

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
