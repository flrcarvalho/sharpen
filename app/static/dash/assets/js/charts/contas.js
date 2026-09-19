// ── Aba CONTAS · v4 (s372) ───────────────────────────────────────────────────
// Responde "quanto dura, quanto gira e quanto devolve uma conta nesta casa?".
//
// A fronteira com Bookies é a UNIDADE, e é ela que justifica esta aba existir:
// Bookies mede a APOSTA (onde as apostas rendem) e não sabe quantas contas geraram
// aquele P/L nem quanto tempo elas viveram. Aqui a unidade é a CONTA.
//
// ── O QUE A v4 MUDOU (handoff de design do Feca, `design_handoff_contas_v4`) ──
// A v1 entregava a resposta como PLANILHA: quatro KPIs neutros, uma tabela de dez
// colunas e o retorno mais importante num cartão no fim da página. A lógica de cálculo
// não mudou; mudou a ORDEM DA LEITURA, em três granularidades encadeadas:
//   1. três PAINÉIS respondem pela base inteira (longevidade · volume e margem ·
//      retorno sobre aquisição);
//   2. FICHAS por casa repetem a mesma ordem, uma linha por casa;
//   3. DRILL abre a conta individual, com a tabela larga.
//
// Três decisões de implementação que o handoff deixou em aberto ou que colidiam com o
// que já existe, e por que foram assim:
//
//   · **A barra de filtros continua sendo a do APP**, não o `.fv` desenhado no
//     protótipo. O handoff especifica um campo próprio, mas o app inteiro usa
//     `.filters`/`.filter-group`/multiselect, e adotar um segundo estilo só aqui é
//     exatamente o item 8 do checklist de UI ("há dois estilos para o mesmo papel?").
//     Do handoff entra o que é da TELA: régua, painéis, fichas, drill, definições.
//   · **Custo por dia de vida = custo ÷ SOMA das durações.** O README diz que o
//     protótipo assume a mediana, mas os NÚMEROS dele dizem soma: Novibet, R$ 9.800 ÷
//     15,22 = 644 dias = 28 contas × 23 de média. A soma também é a única régua
//     aditiva — "custo total ÷ mediana" mistura um total com uma estatística de
//     posição e não se confere na mão.
//   · **`Inativas`, nunca `Encerradas`** (decisão do Feca): a palavra já vem da base do
//     Sharpen, e um vocabulário só vale mais que a palavra mais bonita. Vale no
//     segmentado E no estado da conta dentro do drill.
//
// ⚠️ A régua do PERÍODO, que é onde esta tela poderia mentir:
//   · o período escolhe QUAIS CONTAS ENTRAM (vida intersectando a janela);
//   · duração e dias ativos são da VIDA INTEIRA da conta, nunca recortados — truncar a
//     vida ao filtro inventaria número: uma conta que viveu de janeiro a junho não
//     durou "zero dias" porque alguém filtrou setembro. Mesma família do
//     "data derivada por ESTIMATIVA é dado inventado" (CLAUDE.md);
//   · turnover, P/L e custo SEGUEM o período, como no resto do app;
//   · a tela DIZ isso (`#cnRegua`) — duas réguas vizinhas sem legenda leem como defeito.
//
// Esporte e tipster NÃO recortam: descrevem a aposta, não a conta. A Bet365 custou o
// que custou e durou o que durou, olhe-se tênis ou futebol. Mesmo motivo pelo qual
// `calcCostFiltered` não recebe `rows`.
//
// Nada aqui deriva custo por caminho próprio: o custo sai de `_custoNaJanela`
// (gestao.js), a MESMA função de `calcCostFiltered` e do drill de Bookies. Somar
// `_custoDaConta` à mão daria o mesmo número por um caminho novo, que é exatamente
// quando as duas telas passam a divergir.

// Default `inativas`: é a régua honesta de durabilidade. Conta ATIVA ainda não morreu,
// e contá-la junto responde "quanto uma conta aguenta" com um número muito maior que a
// verdade (medido na base do Feca: 103 dias contra 20). Uma constante, e não um literal
// solto, porque o "Limpar tudo" precisa voltar ao MESMO estado em que a tela nasce.
const CN_POP_PADRAO = 'inativas';
let _cnPop = CN_POP_PADRAO;  // 'ativas' | 'inativas' | 'ambas'
let _cnAberta = '';       // casa expandida no drill ('' = nenhuma)
let _cnSortCol = 'mult';  // o handoff pede múltiplo decrescente como ordem de entrada
let _cnSortDir = -1;
// A sub-tabela do drill ordena por conta PRÓPRIA, independente da tabela de casas: as
// duas têm colunas diferentes, e reusar um estado só faria a de baixo herdar uma chave
// que ela não tem (e cair no `undefined`, que ordena tudo como zero, calado).
let _cnDrillCol = 'turn';
let _cnDrillDir = -1;

// Régua fixa das barras de duração, em dias. Fixa é o ponto: com escala por linha, duas
// barras do mesmo tamanho significariam números diferentes e a comparação entre casas,
// que é o motivo da ficha existir, deixaria de valer.
const CN_REGUA_DIAS = 30;
// Escala do medidor de múltiplo. O piso (1,00×) cai em 10% dela.
const CN_GAUGE_MAX = 10;

// Mediana: o valor do MEIO da lista ordenada. Ela está na tela porque em TODA casa da
// base a mediana é cerca de metade da média (Superbet 5d contra 11d, Betano 8d contra
// 14d, Bet365 10d contra 19d): poucas contas longevas puxam a média, e quem lê só a
// média decide comprar achando que a conta dura o dobro do que dura.
function _cnMediana(xs){
  if(!xs.length)return 0;
  const a=xs.slice().sort((x,y)=>x-y);
  const m=a.length>>1;
  return a.length%2?a[m]:(a[m-1]+a[m])/2;
}
function _cnMedia(xs){return xs.length?xs.reduce((a,b)=>a+b,0)/xs.length:0;}

// Fornecedores do universo (cadastro ∪ base), para o multiselect. `normForn` manda:
// conta sem `[Fornecedor]` no nome é PRÓPRIA e aparece como "Eu" — são 59 das 182
// contas do Feca, um terço da base, e é o que distingue "custo zero de verdade" de
// "não lancei o preço".
function _cnFornecedores(){
  if(!_contaVida)_buildContaVida();
  const s=new Set();
  Object.keys(_contaVida).forEach(k=>{s.add(k.slice(0,k.indexOf('||')));});
  return [...s].sort((a,b)=>a.localeCompare(b,'pt-BR'));
}

// Universo de contas com vida + métricas. Uma função só, porque os painéis, as fichas e
// o drill têm de sair do MESMO recorte — derivar de novo em cada bloco é como a tela
// ganha dois números que discordam.
function _cnBase(){
  if(!_contaVida)_buildContaVida();
  const range=(typeof _selRange==='function')?_selRange('contas'):null;
  const de=range?range.from:'0000-01-01';
  const ate=range?range.to:'9999-12-31';
  const casasSel=msGet('ca_contas'), fornSel=msGet('fo_contas'), opsSel=msGet('op_contas');

  // Métricas por conta. Dias ativos e a vida vêm de LIQUIDADAS + ABERTAS (só `DADOS`
  // deixaria de fora a conta que tem aposta viva e nenhuma encerrada — o ponto cego da
  // s239); turnover e P/L só de `DADOS`, porque aposta aberta não tem resultado.
  const met={};
  const slot=k=>met[k]||(met[k]={dias:new Set(),turnPer:0,plPer:0,bets:0});
  const chave=r=>(normForn(r.fornecedor)+'||'+r.casa+'||'+(r.conta||'__default__'));
  (typeof DADOS!=='undefined'?DADOS:[]).forEach(r=>{
    if(!r.data)return;
    const m=slot(chave(r));
    m.dias.add(r.data);                              // vida inteira: sem corte de período
    if(r.data<de||r.data>ate)return;                 // dinheiro: dentro do período
    m.bets++;
    m.plPer+=r.lucro;
    if(r.resultado!=='V')m.turnPer+=r.stake;
  });
  (typeof DADOS_ABERTAS!=='undefined'?DADOS_ABERTAS:[]).forEach(r=>{
    if(!r.data)return;
    slot(chave(r)).dias.add(r.data);
  });

  const out=[];
  Object.entries(_contaVida).forEach(([k,contas])=>{
    const i=k.indexOf('||');
    const forn=k.slice(0,i), casa=k.slice(i+2);
    if(casasSel.size&&!casasSel.has(casa))return;
    if(fornSel.size&&!fornSel.has(forn))return;
    Object.entries(contas).forEach(([nome,v])=>{
      if(opsSel.size&&v.op&&!opsSel.has(v.op))return;
      // O período escolhe quem ENTRA: vida disjunta da janela → a conta não existia ali.
      if(v.ini&&v.fim&&(v.fim<de||v.ini>ate))return;
      const m=met[forn+'||'+casa+'||'+nome]||{dias:new Set(),turnPer:0,plPer:0,bets:0};
      // Ativa = cadastrada e não arquivada. `_buildContaVida` marca isso pondo o fim em
      // HOJE; conta sem cadastro tem o fim na última aposta e lê como inativa, que é
      // tudo o que se sabe dela.
      const ativa=!!(v.fim&&v.fim===(typeof _ymd==='function'?_ymd(new Date()):''));
      let dur=0;
      if(v.ini&&v.fim){
        dur=Math.round((new Date(v.ini+'T00:00:00')-0-(new Date(v.fim+'T00:00:00')-0))/-864e5)+1;
      }
      out.push({
        casa:casa, forn:forn, conta:nome, chave:forn+'||'+casa+'||'+nome,
        ativa:ativa, propria:forn==='Eu',
        ini:v.ini, fim:v.fim, adq:v.adq,
        dur:dur, dias:m.dias.size, bets:m.bets,
        turn:m.turnPer, pl:m.plPer,
        custo:(typeof _custoDaConta==='function')?_custoDaConta(forn,casa,nome):0,
      });
    });
  });
  const pop=_cnPop==='ativas'?out.filter(c=>c.ativa)
          :_cnPop==='inativas'?out.filter(c=>!c.ativa):out;
  return {contas:pop, de:de, ate:ate, temPeriodo:!!range, casasSel:casasSel, opsSel:opsSel};
}

// ── Os três estados de custo ─────────────────────────────────────────────────
// Regra de negócio crítica do handoff, e a única que não pode ser perdida:
// conta PRÓPRIA entra no cálculo com custo zero VERDADEIRO; conta SEM PREÇO lançado
// fica FORA do múltiplo e do ROI líquido. São estados diferentes e nunca se fundem —
// somar a segunda como zero inflaria o retorno com custo que existe e não foi
// declarado (a ausência se disfarçando de zero).
function _cnTemPreco(c){return c.propria||c.custo>0;}

// Agrega por casa.
function _cnPorCasa(contas){
  const by={};
  contas.forEach(c=>{
    const a=by[c.casa]||(by[c.casa]={casa:c.casa,n:0,ativas:0,inativas:0,proprias:0,semPreco:0,
                                     durs:[],diasArr:[],turn:0,pl:0,custo:0,comPreco:0,bets:0,
                                     somaDur:0,turnEleg:0,plEleg:0});
    a.n++;
    if(c.ativa)a.ativas++;else a.inativas++;
    if(c.propria)a.proprias++;
    if(c.custo>0)a.comPreco++;else if(!c.propria)a.semPreco++;
    if(c.dur>0){a.durs.push(c.dur);a.somaDur+=c.dur;}
    if(c.dias>0)a.diasArr.push(c.dias);
    a.turn+=c.turn; a.pl+=c.pl; a.custo+=c.custo; a.bets+=c.bets;
    // Elegível = tem preço declarado (comprada com valor, ou própria a custo zero). É
    // sobre ELE que o líquido e o múltiplo se calculam.
    if(_cnTemPreco(c)){a.turnEleg+=c.turn;a.plEleg+=c.pl;}
  });
  return Object.values(by).map(a=>{
    const plLiq=a.plEleg-a.custo;
    return {
      ...a,
      dur:_cnMedia(a.durs), durMed:_cnMediana(a.durs), dias:_cnMedia(a.diasArr),
      turnConta:a.n?a.turn/a.n:0,
      // ROI é sobre TURNOVER (a régua do app inteiro), e não sobre custo — quem mede
      // retorno sobre custo é o Múltiplo. Dois denominadores pedem dois nomes.
      roi:a.turn>0?(a.pl/a.turn*100):0,
      // ROI LÍQUIDO = (P/L − custo) ÷ turnover, só sobre as contas elegíveis.
      roiLiq:a.turnEleg>0?(plLiq/a.turnEleg*100):null,
      plLiq:plLiq,
      // Custo por dia de VIDA: custo ÷ soma das durações (ver cabeçalho). Coloca conta
      // cara e longa na mesma régua que conta barata e curta.
      custoDia:a.somaDur>0&&a.custo>0?(a.custo/a.somaDur):null,
      // O múltiplo só existe onde há custo lançado. Sem ele não há múltiplo — nem zero,
      // nem infinito.
      mult:a.custo>0?(a.plEleg/a.custo):null,
    };
  });
}

// ── Histograma de vida, em 5 faixas ──────────────────────────────────────────
// Ele existe porque a média sozinha não descreve nenhuma conta: 41% das contas do Feca
// morrem em 7 dias ou menos, e são as poucas acima de 60 dias que puxam a média para o
// dobro da mediana. A distribuição mostra isso de uma vez.
// `dias` por extenso, e não `d`: a abreviação economiza 3 caracteres numa coluna que
// tem espaço de sobra e cobra do leitor a tradução (pedido do Feca). A última faixa é
// `mais de 60 dias` em vez de `60 d +`, porque `+` depois do número lê como soma.
const CN_FAIXAS=[
  ['0 a 7 dias',0,7],
  ['8 a 14 dias',8,14],
  ['15 a 30 dias',15,30],
  ['31 a 60 dias',31,60],
  ['mais de 60 dias',61,Infinity],
];
function _cnHistograma(durs){
  const total=durs.length||1;
  const linhas=CN_FAIXAS.map(([rot,a,b],i)=>{
    const n=durs.filter(d=>d>=a&&d<=b).length;
    // `primeira` marca a faixa de alerta (0 a 7 dias) por POSIÇÃO, não comparando o
    // rótulo: texto é copy e muda; índice é estrutura. Foi um `l.rot==='0-7 d'` que
    // quase deixou a faixa sem o âmbar quando os rótulos foram reescritos.
    return {rot:rot, n:n, pct:n/total*100, primeira:i===0};
  });
  const topo=Math.max(...linhas.map(l=>l.n),1);
  linhas.forEach(l=>{l.larg=l.n/topo*100;});
  return linhas;
}

// Agregado da base inteira — alimenta os três painéis. Sai do MESMO array de contas que
// as fichas, e é isso que impede o topo de discordar da lista logo abaixo.
function _cnGeral(contas,linhas){
  const durs=contas.filter(c=>c.dur>0).map(c=>c.dur);
  const dias=contas.filter(c=>c.dias>0).map(c=>c.dias);
  const eleg=contas.filter(_cnTemPreco);
  const turnEleg=eleg.reduce((a,c)=>a+c.turn,0);
  const plEleg=eleg.reduce((a,c)=>a+c.pl,0);
  const turnTot=contas.reduce((a,c)=>a+c.turn,0);
  const plTot=contas.reduce((a,c)=>a+c.pl,0);
  return {
    n:contas.length,
    nAtivas:contas.filter(c=>c.ativa).length,
    durMed:_cnMediana(durs), durMedia:_cnMedia(durs),
    diasMedia:_cnMedia(dias),
    hist:_cnHistograma(durs),
    longevas:durs.filter(d=>d>60).length,
    turnConta:contas.length?turnTot/contas.length:0,
    roi:turnTot>0?(plTot/turnTot*100):0,
    // Os dois ROIs do painel 2 saem do MESMO denominador elegível: comparar um líquido
    // recortado com um bruto da base inteira faria a margem parecer menor do que é.
    roiBruto:turnEleg>0?(plEleg/turnEleg*100):0,
    ranking:linhas.slice().sort((a,b)=>b.turnConta-a.turnConta).slice(0,5),
    nComPreco:contas.filter(c=>!c.propria&&c.custo>0).length,
    nProprias:contas.filter(c=>c.propria).length,
    nSemPreco:contas.filter(c=>!c.propria&&c.custo<=0).length,
    plEleg:plEleg,
  };
}

function _cnPopSub(){
  return _cnPop==='ativas'?'ainda rodando · a vida delas não terminou'
       :_cnPop==='inativas'?'a régua honesta de durabilidade'
       :'todas as contas que existiram no período';
}
// A barra NÃO repinta junto com o conteúdo (repintá-la fecharia um multiselect aberto e
// perderia o foco da busca dentro dele), então quem muda o estado atualiza o segmentado
// à mão. Mesma razão pela qual o `rqb` existe para os botões de período.
function cnPop(v){
  _cnPop=v;
  document.querySelectorAll('#cnSeg button').forEach(b=>b.classList.toggle('active',b.dataset.k===v));
  const s=document.querySelector('.cn-popsub');
  if(s)s.textContent=_cnPopSub();
  renderContas();
}
function cnToggle(casa){_cnAberta=(_cnAberta===casa?'':casa);renderContas();}
function cnSort(col){
  if(_cnSortCol===col)_cnSortDir=-_cnSortDir;else{_cnSortCol=col;_cnSortDir=-1;}
  renderContas();
}
function cnDrillSort(col){
  if(_cnDrillCol===col)_cnDrillDir=-_cnDrillDir;else{_cnDrillCol=col;_cnDrillDir=-1;}
  renderContas();
}
window.cnPop=cnPop;window.cnToggle=cnToggle;window.cnSort=cnSort;window.cnDrillSort=cnDrillSort;

// Os filtros são montados UMA vez, no primeiro render da aba, e não no `buildHTML`: a
// lista de fornecedores sai do `_contaVida`, que só existe depois do `contasLoad()`.
// Montar cedo demais daria um multiselect vazio, em silêncio.
function _cnMontarFiltros(){
  const box=document.getElementById('contasFiltros');
  if(!box||box.dataset.pronto)return;
  box.innerHTML=buildFiltrosContas((typeof _LISTAS!=='undefined'&&_LISTAS.casas)||[]);
  box.dataset.pronto='1';
}
window._cnMontarFiltros=_cnMontarFiltros;

// ⚠️ O DOM pode AINDA NÃO EXISTIR quando as cargas resolvem, e o sintoma é a aba em
// branco — intermitente, porque é corrida. Medido no headless: o boot do dashboard é
// assíncrono e a casca (`app.html`) chama `showPage` no evento `load` do iframe, que
// dispara antes do `buildHTML` montar o `#contasContent`. O `renderPage` prematuro
// escreve no vazio E MARCA a assinatura da página; o `showPage` que o `buildHTML` faz
// logo depois é então engolido pelo guard `id===_lastPage&&sig===_lastPageSig`, e não
// há segunda chance.
//
// A espera curta resolve isto AQUI, sem tocar no roteador que todas as telas usam —
// o guard do `showPage` é defeito compartilhado e anterior a esta aba, e consertá-lo
// de verdade é mudança própria, com a suíte inteira por perto.
function _cnPintarQuandoPronto(tentativa){
  const t=tentativa||0;
  if(!document.getElementById('contasContent')){
    if(t<40)setTimeout(()=>_cnPintarQuandoPronto(t+1),100);   // teto de 4s, depois desiste
    return;
  }
  _cnMontarFiltros();
  renderContas();
}
window._cnPintarQuandoPronto=_cnPintarQuandoPronto;

// Barra própria, NÃO o `buildFilters` genérico: esporte e tipster não recortam esta
// tela, e oferecê-los faria o número mudar por um eixo que não descreve a conta.
// As peças são as mesmas do `filters.js` — copiar o markup criaria dois Períodos que
// divergem no primeiro ajuste (a lição da s317).
function buildFiltrosContas(casas){
  const seg=[['ativas','Ativas'],['inativas','Inativas'],['ambas','Ambas']].map(([k,lbl])=>
    `<button data-k="${k}" class="${_cnPop===k?'active':''}" onclick="cnPop('${k}')">${lbl}</button>`
  ).join('');
  return`<div class="filters">
${_grupoPeriodo('contas')}
    ${_grupoCasa('contas',casas,'renderContas()')}
    <div class="filter-group"><div class="filter-label">Fornecedor</div>${buildMS('fo_contas',_cnFornecedores(),'Todos os fornecedores','contas','renderContas()')}</div>
    ${_grupoOperador('contas','renderContas()')}
    ${_grupoLimpar('contas')}
    <div class="filter-group cn-fgpop">
      <div class="filter-label">População</div>
      <div class="tcard-seg" id="cnSeg" style="padding-top:2px">${seg}</div>
      <div class="cn-popsub">${_cnPopSub()}</div>
    </div>
  </div>`;
}

// O seg de População é filtro LOCAL desta tela: o "Limpar tudo" da barra não o enxerga
// pelo `MSS`, e um botão que limpa metade da tela mente no próprio rótulo. Limpar aqui é
// voltar ao estado em que a tela nasce, que na v4 é `inativas` e não mais `ambas`.
//
// O `limpar` também repinta o SEGMENTADO: a barra de filtros não é remontada a cada
// render (remontá-la fecharia um multiselect aberto), então quem muda `_cnPop` por fora
// do `cnPop` precisa mexer nas classes à mão — senão o botão aceso continua sendo o
// antigo, com a tela já mostrando outra população.
LIMPAR_EXTRA.contas={
  ativo:()=>_cnPop!==CN_POP_PADRAO,
  limpar:()=>{                     // quem repinta o CONTEÚDO é o `limparFiltrosPagina`
    _cnPop=CN_POP_PADRAO;
    document.querySelectorAll('#cnSeg button').forEach(b=>
      b.classList.toggle('active',b.dataset.k===CN_POP_PADRAO));
    const s=document.querySelector('.cn-popsub');
    if(s)s.textContent=_cnPopSub();
  },
};

// O "i" da mediana reusa o padrão `.tip-anchor` + `.metric-info` + `.metric-tip` do
// projeto (o `_gTip` global clona e posiciona, por delegação no `document`) — nenhum
// tooltip novo.
function _cnTipMediana(){
  return`<span class="tip-anchor"><button class="metric-info" aria-label="Sobre a mediana" onclick="event.stopPropagation()">i</button>`
    +`<div class="metric-tip" role="tooltip" hidden><span class="metric-tip__caret"></span>`
    +`<div class="metric-tip__formula"><span class="lbl">metade durou menos</span><span class="op">·</span><span class="lbl">metade durou mais</span></div>`
    +`<div class="metric-tip__desc">O valor do <b>meio</b>, com as contas enfileiradas da mais curta para a mais longa. `
    +`Quando a mediana é bem menor que a média, poucas contas longevas estão puxando a média para cima, `
    +`e é a <b>mediana</b> que descreve a conta típica.</div>`
    +`<div class="metric-tip__bench"><span>calculada no período do filtro</span></div></div></span>`;
}

// Máscara do MÚLTIPLO (razão P/L ÷ custo). O `UI_REFERENCE §5` cobre R$, %, odd e
// saldo; a razão não é nenhum dos quatro, então ela espelha a gramática do `.money`:
// mono, 2 casas, o `×` neutro e menor como o `R$`, e cor SÓ abaixo de 1,00 — que é a
// conta que não devolveu o que custou. Ver `UI_REFERENCE §5.6`.
function _cnMult(v){
  if(v===null||v===undefined)return'<span class="cn-sem">·</span>';
  const n=v.toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2});
  return`<span class="cn-mult ${v<1?'neg':''}">${n}<span class="cn-mult__x">×</span></span>`;
}
function _cnPctTxt(v,cls){
  if(v===null||v===undefined)return'<span class="cn-sem">·</span>';
  return`<span class="${cls||(v>=0?'cn-roi-pos':'cn-roi-neg')}">${fmtPct(v,2)}</span>`;
}

function renderContas(){
  const cont=document.getElementById('contasContent');
  if(!cont)return;
  const B=_cnBase();
  const linhas=_cnPorCasa(B.contas);
  const G=_cnGeral(B.contas,linhas);

  // ⚠️ Estado VAZIO com a saída junto, e não uma tela em branco. Ele não é hipotético:
  // com o default `inativas`, um dono cujas contas estejam todas ativas abre a aba e vê
  // três painéis zerados, sem nada dizendo que basta trocar a população. Medido no
  // `servidor_demo`, onde as 102 contas são ativas — a tela nasceu vazia.
  //
  // "Vazio" aqui é um recorte que não tem linha, nunca "não há dado": a diferença está
  // na mensagem, porque a ação de quem lê é outra em cada caso.
  if(!B.contas.length){
    cont.innerHTML=_cnRegua(B,G)+_cnVazio(B);
    return;
  }
  cont.innerHTML=_cnRegua(B,G)+_cnPaineis(B,G)+_cnBloco(B,linhas)+_cnDefinicoes();
}
window.renderContas=renderContas;

// A mensagem aponta o filtro MAIS PROVÁVEL de ter esvaziado a tela, e oferece o clique
// que desfaz só ele. Botão que "limpa tudo" já existe na barra; repeti-lo aqui tiraria
// do usuário a informação de qual eixo é o culpado.
function _cnVazio(B){
  const outras=['ativas','inativas','ambas'].filter(k=>k!==_cnPop);
  const rot=k=>k==='ativas'?'Ativas':k==='inativas'?'Inativas':'Ambas';
  const atalhos=outras.map(k=>
    `<button class="cn-empty__btn" onclick="cnPop('${k}')">Ver ${rot(k)}</button>`).join('');
  // Singular, porque a frase é "nenhuma CONTA ativa" e não "nenhuma conta ativas". O
  // rótulo do segmentado é plural por natureza (ele nomeia o conjunto), então aqui ele
  // não serve — medido na tela, saía "Nenhuma conta inativas no recorte".
  const sing={ativas:'ativa',inativas:'inativa'};
  const porPop=_cnPop!=='ambas'
    ? `Nenhuma conta <b>${sing[_cnPop]}</b> no recorte.`
    : 'Nenhuma conta no recorte.';
  const porFiltro=(B.temPeriodo||B.casasSel.size||B.opsSel.size)
    ? ' O período e os filtros da barra também recortam esta tela.' : '';
  return`<div class="cn-empty"><div class="cn-empty__t">${porPop}</div>`
    +`<p>${_cnPop==='inativas'
        ? 'A aba abre em <b>Inativas</b> porque é a população que responde quanto uma conta aguenta. Se todas as suas contas ainda estão vivas, não há o que medir aqui ainda.'
        : 'Troque a população ou alargue o período.'}${porFiltro}</p>`
    +`<div class="cn-empty__acoes">${atalhos}</div></div>`;
}

// ── Régua de escopo ──────────────────────────────────────────────────────────
// Faixa fixa que impede a tela de mentir sobre o que o filtro de período corta.
function _cnRegua(B,G){
  return`<div class="cn-regua" id="cnRegua">`
    +`<span class="cn-regua__dot"></span>`
    +`<span><b>Duração</b> e <b>dias ativos</b> consideram a vida inteira da conta e não são `
    +`cortados pelo filtro de período. <b>Turnover</b>, <b>P/L</b> e <b>custo</b> seguem o período `
    +`selecionado. Esporte e tipster não recortam esta tela.</span>`
    +`<span class="cn-regua__esc">${G.nComPreco} com preço · ${G.nProprias} próprias · ${G.nSemPreco} sem preço</span>`
    +`</div>`;
}

// ── Os três painéis ──────────────────────────────────────────────────────────
function _cnPaineis(B,G){
  // UMA chamada de custo por render. `_custoNaJanela` percorre o `_contaVida` inteiro;
  // chamá-la por painel repetiria a varredura e, pior, abriria a porta para dois
  // painéis vizinhos mostrarem custos diferentes se alguém mudasse um dos argumentos.
  const custo=_cnCustoTotal(B);
  const turnEleg=B.contas.filter(_cnTemPreco).reduce((a,c)=>a+c.turn,0);
  // ── Anatomia do painel ───────────────────────────────────────────────────
  // O TÍTULO segue o `.kpi-label` + `.kpi-pipe` do produto (mono 11/700, `.08em`, com a
  // barra azul de 4×13px). O handoff pedia um eyebrow em `--accent-2` sem barra, mas
  // "título de painel" já tem forma no Sharpen e duas formas para o mesmo papel é o item
  // 8 do checklist. O azul fica na barra, que é onde ele é sinal.
  //
  // A FIGURA virou um PAR ROTULADO, e essa é a correção que o Feca pediu: antes saía
  // `12 dias · mediana  média 34 dias`, com o rótulo DEPOIS do valor e colado no vizinho,
  // então os dois números se fundiam numa frase só e nada dizia qual era qual. Agora cada
  // número tem o rótulo EMBAIXO dele, na mesma coluna, e um divisor separa os dois.
  const painel=(eyebrow,ctx,pergunta,figs,corpo,rodape)=>
    `<div class="cn-qp">`
    +`<div class="cn-qh"><span class="kpi-pipe"></span><span class="t">${eyebrow}</span>`
    +`<span class="s">${ctx}</span></div>`
    +`<div class="cn-qq">${pergunta}</div>`
    +`<div class="cn-figs">`
    +figs.map((f,i)=>
      `<div class="cn-fig ${f.fraca?'fraca':''}">`
      +`<span class="v">${f.valor}</span>`
      +`<span class="lb">${f.rotulo}</span></div>`
     ).join('<span class="cn-figsep"></span>')
    +`</div>`
    +corpo
    +`<div class="cn-foot">${rodape}</div></div>`;

  // ── 1 · LONGEVIDADE ──
  const hist=G.hist.map(l=>
    `<div class="cn-drow"><span class="lb">${l.rot}</span>`
    +`<span class="cn-dbar"><i class="${l.primeira?'hot':''}" style="width:${l.larg.toFixed(1)}%"></i></span>`
    +`<span class="rv">${l.n} · ${Math.round(l.pct)}%</span></div>`
  ).join('');
  const med=Math.round(G.durMed), media=Math.round(G.durMedia);
  // ⚠️ O rodapé diz O QUE FAZER com os dois números, não o que eles SÃO. A redação
  // anterior ("Mediana é a conta do meio… Média incorpora as exceções e mede o prêmio da
  // cauda") era uma aula de estatística que não respondia nem *por que estou vendo isso*
  // — o Feca leu e disse que nem ele entendia. A régua que ficou: cada frase cita um
  // número DESTA base e termina numa consequência para quem lê.
  const pctCurto=G.hist.length?Math.round(G.hist[0].pct):0;
  const p1=painel('Longevidade',
    `${G.n.toLocaleString('pt-BR')} ${_cnPop==='ativas'?'ativas':_cnPop==='inativas'?'inativas':'contas'}`,
    'Quanto tempo uma conta permanece operacional?',
    [{valor:med+' dias',rotulo:'Mediana'},
     {valor:media+' dias',rotulo:'Média',fraca:true}],
    `<div class="cn-dist">${hist}</div>`,
    `<b>Metade das suas contas durou menos de ${med} dias</b>`
    +(pctCurto?`, e ${pctCurto}% não passou da primeira semana.`:'.')
    +(media>med&&G.longevas
      ? ` A média é maior (${media}) porque ${G.longevas} conta${G.longevas===1?'':'s'} `
        +`passou de 60 dias e puxa${G.longevas===1?'':'m'} o número para cima. `
        +`<b>Para estimar a próxima compra, use ${med}, não ${media}.</b>`
      : ''));

  // ── 2 · VOLUME E MARGEM ──
  const rank=G.ranking.map(c=>
    `<div class="cn-mrow"><span class="nm">${esc(c.casa)}</span>`
    +`<span class="vv"><b>${fmtR(c.turnConta)}</b> · ${_cnPctTxt(c.roiLiq)}</span></div>`
  ).join('')||'<div class="cn-vazio">Sem casa no recorte.</div>';
  const roiLiq=turnEleg>0?((G.plEleg-custo)/turnEleg*100):0;
  const p2=painel('Volume e margem', B.temPeriodo?'no período':'histórico',
    'Quanto cada conta movimenta e que margem sobra?',
    [{valor:fmtPct(roiLiq,2),rotulo:'ROI líquido'},
     {valor:fmtPct(G.roiBruto,2),rotulo:'ROI bruto',fraca:true}],
    `<div class="cn-mini">${rank}</div>`,
    `Cada conta movimentou ${fmtR(G.turnConta)} em ${Math.round(G.diasMedia)} dias ativos, `
    +`em média. <b>O líquido é o que sobra depois do custo da conta</b>; a diferença para o `
    +`bruto é o quanto a aquisição come da margem.`);

  // ── 3 · RETORNO SOBRE AQUISIÇÃO ──
  const nEleg=G.nComPreco+G.nProprias;
  const mult=custo>0?(G.plEleg/custo):null;
  // ⚠️ O handoff rotula esta linha com uma das TRÊS PALAVRAS BANIDAS do produto (gate:
  // `test_o_vocabulario_proibido_nao_volta_ao_produto`, que lista as três). Aqui ela é
  // "Custo das contas", e o rodapé fala em "valor pago na aquisição": mesmo número, a
  // palavra que o produto usa. O gate varre o arquivo inteiro, comentário incluído —
  // então nem para explicar a regra se escreve a palavra, como a s364 já aprendeu.
  const comp=[
    ['Custo das contas',fmtR(custo)],
    ['P/L bruto gerado',fmtPL(G.plEleg)],
    ['Resultado líquido',fmtPL(G.plEleg-custo)],
  ].map(([l,v])=>`<div class="cn-crow"><span class="cl">${l}</span><span class="cn">${v}</span></div>`).join('');
  const tot=G.n||1;
  const cov=`<div class="cn-covwrap"><div class="cn-covbar">`
    +`<i style="background:var(--accent);width:${G.nComPreco/tot*100}%"></i>`
    +`<i style="background:var(--ink-soft);width:${G.nProprias/tot*100}%"></i>`
    +`<i style="background:var(--warn);width:${G.nSemPreco/tot*100}%"></i></div>`
    +`<div class="cn-covleg">`
    +`<span><em style="background:var(--accent)"></em>${G.nComPreco} com preço</span>`
    +`<span><em style="background:var(--ink-soft)"></em>${G.nProprias} próprias</span>`
    +`<span><em style="background:var(--warn)"></em>${G.nSemPreco} sem preço</span>`
    +`</div></div>`;
  // O rodapé só fala dos estados que EXISTEM no recorte. Com cobertura de preço em 100%
  // a frase do handoff viraria "As 0 próprias entram… As 0 sem preço ficam fora", que é
  // ruído com cara de explicação — e o handoff já prevê o caso ("a faixa âmbar some").
  const notaProp=G.nProprias
    ? ` As ${G.nProprias} próprias entram com custo zero real.` : '';
  const notaSem=G.nSemPreco
    ? ` As <span class="cn-warnc">${G.nSemPreco} sem preço</span> ficam fora do cálculo, `
      +`porque tratá-las como zero inflaria o retorno.`
    : ' Toda conta do recorte tem preço lançado.';
  const multTxt=mult===null?'·'
    :mult.toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2})+'×';
  const p3=painel('Retorno sobre aquisição', `${nEleg} de ${G.n} contas`,
    'Quanto o custo das contas devolveu?',
    [{valor:multTxt,rotulo:'Múltiplo'},
     {valor:'1,00×',rotulo:'Piso',fraca:true}],
    `<div class="cn-comp">${comp}</div>${cov}`,
    (mult!==null
      ? `<b>Cada R$ 1 gasto em conta voltou ${multTxt.replace('×','')} reais.</b> `
        +`Abaixo de 1,00× a conta não devolveu o que custou.`
      : 'Sem preço lançado não há múltiplo: ele compara o P/L com o que foi pago.')
    +notaProp+notaSem);

  return`<div class="cn-q3">${p1}${p2}${p3}</div>`;
}

// O custo total sai do `_custoNaJanela` — régua ÚNICA com `calcCostFiltered`, com a
// Visão Geral e com o drill de Bookies. Somar `_custoDaConta` linha a linha daria hoje
// o mesmo número por um caminho novo, e duas derivações para a mesma pergunta divergem
// no primeiro caso de borda.
function _cnCustoTotal(B){
  const contasOk=new Set(B.contas.map(c=>c.chave));
  if(typeof _custoNaJanela!=='function')return B.contas.reduce((a,c)=>a+c.custo,0);
  return _custoNaJanela(B.de,B.ate,B.casasSel,B.opsSel,'','pago',contasOk).total;
}

// ── Bloco "Por casa": cabeçalho, legenda e as fichas ─────────────────────────
function _cnBloco(B,linhas){
  const dir=_cnSortDir, key=_cnSortCol;
  linhas.sort((a,b)=>{
    if(key==='casa')return a.casa.localeCompare(b.casa,'pt-BR')*(-dir);
    const va=a[key], vb=b[key];
    // `null` (sem preço, sem múltiplo) vai sempre para o FIM, nas duas direções: ele não
    // é "zero", é ausência, e deixá-lo ordenar como zero misturaria os dois estados que
    // esta tela existe para separar.
    if(va===null&&vb===null)return 0;
    if(va===null)return 1;
    if(vb===null)return -1;
    return ((va||0)-(vb||0))*dir;
  });

  const th=(col,lbl,cls)=>`<span class="${cls||'r'} ${key===col?'sort-'+(dir<0?'desc':'asc'):''}"`
    +` onclick="cnSort('${col}')">${lbl}<span class="sort-icon"></span></span>`;

  const fichas=linhas.map(a=>{
    const aberta=_cnAberta===a.casa;
    const pMed=Math.min(a.durMed/CN_REGUA_DIAS*100,100);
    const pAvg=Math.min(a.dur/CN_REGUA_DIAS*100,100);
    const gMult=a.mult===null?0:Math.max(Math.min(Math.abs(a.mult)/CN_GAUGE_MAX*100,100),1.5);
    const under=a.mult!==null&&a.mult<1;
    let html=`<div class="cn-ficha ${aberta?'open':''}" onclick="cnToggle('${esc(a.casa).replace(/'/g,"\\'")}')">`
      +`<div class="cn-fname">${casaCell(a.casa)}`
      +`<span class="sub">${a.n} conta${a.n===1?'':'s'} · ${a.ativas} ativa${a.ativas===1?'':'s'}</span></div>`
      +`<div class="cn-life">`
      +  `<div class="cn-track"><i class="med" style="width:${pMed.toFixed(1)}%"></i>`
      +  `<i class="avg" style="left:${pAvg.toFixed(1)}%"></i></div>`
      +  `<div class="cn-lifelab"><span>mediana <b>${Math.round(a.durMed)} d</b></span>`
      +  `<span>média <b>${Math.round(a.dur)} d</b></span>`
      +  `<span>ativos <b>${Math.round(a.dias)}</b></span></div>`
      +`</div>`
      +`<div class="cn-fcell"><div class="n">${fmtR(a.turnConta)}</div>`
      +  `<div class="s">líq. ${_cnPctTxt(a.roiLiq)} · bruto ${fmtPct(a.roi,2)}</div></div>`
      +`<div class="cn-fcell"><div class="n">${a.custoDia===null?'<span class="cn-sem">·</span>':_cnMoney2(a.custoDia)}</div>`
      +  `<div class="s">${a.custo>0?'custo '+fmtR(a.custo):'<span class="cn-sem">sem custo lançado</span>'}</div></div>`
      +`<div class="cn-multwrap"><div class="n">${_cnMult(a.mult)}</div>`
      +  `<div class="cn-gauge"><i class="${under?'under':''}" style="width:${gMult.toFixed(1)}%"></i>`
      +  `<span class="th" style="left:${100/CN_GAUGE_MAX}%"></span></div></div>`
      +`</div>`;
    if(aberta)html+=_cnDrill(a,B.contas.filter(c=>c.casa===a.casa));
    return html;
  }).join('')||'<div class="cn-vazio">Nenhuma conta no recorte.</div>';

  return`<div class="cn-blockh"><span class="t">Por casa</span>`
    +`<span class="m">clique na casa para abrir as contas · ordenável por qualquer coluna</span></div>`
    +`<div class="cn-why2"><span class="cn-mks">`
    +`<span class="cn-mk2"><i class="s"></i>mediana</span>`
    +`<span class="cn-mk2"><i class="d"></i>média</span></span>`
    +`<p>Barra sólida curta com o pontilhado distante indica <b>casa que depende de exceções</b>: `
    +`a conta típica encerra cedo e o resultado vem de poucas sobreviventes. `
    +`Ambas na mesma régua de 0 a ${CN_REGUA_DIAS} dias.</p></div>`
    +`<div class="cn-ovf"><div class="cn-fichas">`
    +`<div class="cn-fhead">${th('casa','Casa','l')}`
    +`${th('durMed','Duração: mediana e média (0 a '+CN_REGUA_DIAS+' dias) '+_cnTipMediana(),'l')}`
    +`${th('turnConta','Turnover e ROI líquido')}`
    +`${th('custoDia','Custo por dia de vida')}`
    +`${th('mult','Múltiplo')}</div>`
    +fichas+`</div></div>`;
}

// Dinheiro com centavos fora do `.money` de coluna: o custo por dia é um valor
// unitário pequeno (R$ 15,22), e `fmtR` o arredondaria para R$ 15. Usa a régua do
// `moneyStake`/`fmtSaldo` do `UI_REFERENCE §5.1` — 2 casas, sem cor.
function _cnMoney2(v){
  return`<span class="money"><span class="money-sign">R$</span><span class="money-val">`
    +Number(v||0).toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2})
    +`</span></span>`;
}

// ── Drill ────────────────────────────────────────────────────────────────────
// Lista TODAS as contas da casa e ordena por qualquer coluna.
//
// ⚠️ O corte antigo em 12 linhas por turnover não era só incômodo: ele **escondia a
// única conta ATIVA da Betano** (`cleisonglsports [Gustavo]`), porque ela não estava
// entre as 12 de maior giro. O cabeçalho dizia `1 ativa` e a lista abaixo mostrava 12
// inativas, então a tela parecia estar contando errado — e não estava. **Recorte que
// não é do filtro faz a tabela contradizer o próprio total.**
function _cnDrill(agg,contas){
  const dir=_cnDrillDir, key=_cnDrillCol;
  const txt=k=>k==='conta'||k==='forn';
  const val=(c,k)=>{
    if(k==='estado')return c.ativa?1:0;
    if(k==='liq')return _cnTemPreco(c)?(c.pl-c.custo):null;
    if(k==='roiLiq')return _cnTemPreco(c)&&c.turn>0?((c.pl-c.custo)/c.turn):null;
    return c[k];
  };
  const ord=contas.slice().sort((a,b)=>{
    if(txt(key))return a[key].localeCompare(b[key],'pt-BR')*(-dir);
    if(key==='ini'||key==='fim')return String(a[key]||'').localeCompare(String(b[key]||''))*dir;
    const va=val(a,key), vb=val(b,key);
    if(va===null&&vb===null)return 0;
    if(va===null)return 1;
    if(vb===null)return -1;
    return ((va||0)-(vb||0))*dir;
  });

  const rows=ord.map(c=>{
    const tem=_cnTemPreco(c);
    const liq=c.pl-c.custo;
    const roiLiq=c.turn>0?(liq/c.turn*100):null;
    const est=c.ativa?'<span class="cn-est on">ativa</span>':'<span class="cn-est">inativa</span>';
    // Os três estados de custo, visualmente distintos. `sem preço` em `--warn`, e o
    // líquido e o ROI líquido viram `·`: mostrar o P/L cru na coluna de líquido faria a
    // conta parecer mais lucrativa do que se sabe que ela é.
    const custo=c.propria?'<span class="cn-propria">própria</span>'
              :c.custo>0?fmtR(c.custo)
              :'<span class="cn-warnc">sem preço</span>';
    return`<tr>`
      +`<td class="l">${esc(c.conta)}</td>`
      +`<td class="l">${esc(c.forn)}</td>`
      +`<td class="l">${est}</td>`
      +`<td>${c.dur} d</td>`
      +`<td>${c.dias}</td>`
      +`<td>${c.bets.toLocaleString('pt-BR')}</td>`
      +`<td>${fmtR(c.turn)}</td>`
      +`<td>${fmtPL(c.pl)}</td>`
      +`<td>${custo}</td>`
      +`<td class="k">${tem?fmtPL(liq):'<span class="cn-sem">·</span>'}</td>`
      +`<td class="k">${tem&&roiLiq!==null?_cnPctTxt(roiLiq):'<span class="cn-sem">·</span>'}</td>`
      +`</tr>`;
  }).join('');

  // O `stopPropagation` em cada `<th>` é obrigatório: a LINHA DA CASA abre e fecha o
  // drill no clique, e sem ele ordenar a sub-tabela fecharia o painel inteiro.
  const dth=(col,lbl,cls)=>`<th class="${cls||''} ${key===col?'sort-'+(dir<0?'desc':'asc'):''}"`
    +` onclick="event.stopPropagation();cnDrillSort('${col}')">${lbl}<span class="sort-icon"></span></th>`;
  const aviso=agg.semPreco>0
    ?`<span class="w">${agg.semPreco} conta${agg.semPreco===1?'':'s'} sem preço fora do múltiplo</span>`:'';
  return`<div class="cn-drill" onclick="event.stopPropagation()"><table class="cn-tbl"><thead><tr>`
    +dth('conta','Conta','l')+dth('forn','Fornecedor','l')+dth('estado','Estado','l')
    +dth('dur','Duração')+dth('dias','Dias ativos')+dth('bets','Apostas')+dth('turn','Turnover')
    +dth('pl','P/L bruto')+dth('custo','Custo')+dth('liq','P/L líquido')+dth('roiLiq','ROI líq.')
    +`</tr></thead><tbody>${rows}</tbody></table>`
    +`<div class="cn-drillfoot"><span>${contas.length} conta${contas.length===1?'':'s'} nesta casa</span>`
    +`<span>P/L líquido = bruto − custo · ROI líq. = líquido ÷ turnover</span>${aviso}</div>`
    +`</div>`;
}

// ── Definições ───────────────────────────────────────────────────────────────
// O glossário fica NA TELA, e não num tooltip, porque quatro das métricas daqui não
// existem em nenhuma outra aba: quem abre esta tela pela primeira vez precisa das
// definições à mão, não escondidas atrás de hover.
function _cnDefinicoes(){
  const def=(t,p)=>`<div class="cn-def"><div class="dt">${t}</div><p>${p}</p></div>`;
  return`<div class="cn-defs">`
    +def('Duração','Dias entre a compra e o encerramento da conta. Considera a vida inteira, '
        +'fora do filtro de período. Contas ativas contam até hoje.')
    +def('ROI líquido','(P/L − custo) ÷ turnover. Margem real sobre o valor apostado. '
        +'O bruto acompanha ao lado, em cinza.')
    +def('Múltiplo','P/L ÷ custo das contas. Retorno sobre o valor pago na aquisição. '
        +'A marca no medidor é 1,00×.')
    +def('Custo por dia de vida','Custo ÷ soma das durações da casa. Coloca conta cara e longa '
        +'na mesma régua que conta barata e curta.')
    +`</div>`;
}
