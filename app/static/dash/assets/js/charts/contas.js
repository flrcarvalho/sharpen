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

// Default `ambas`, por decisão do Feca (21/09). A aba nasceu em `inativas` porque essa é
// a régua honesta de DURABILIDADE — conta ativa ainda não morreu, e contá-la junto
// responde "quanto uma conta aguenta" com um número muito maior que a verdade (medido na
// base dele: 103 dias contra 20). Esse argumento continua verdadeiro e continua valendo
// para o número; o que mudou foi a pergunta com que a tela ABRE.
//
// Abrir escondendo as contas vivas faz a tela nascer descrevendo só o que já morreu, e o
// custo disso é maior que o ganho de precisão da mediana: o segmentado está ali, a um
// clique, para quem quiser a régua de durabilidade pura.
// Uma constante, e não um literal solto, porque o "Limpar tudo" precisa voltar ao MESMO
// estado em que a tela nasce.
const CN_POP_PADRAO = 'ambas';
let _cnPop = CN_POP_PADRAO;  // 'ativas' | 'inativas' | 'ambas'
let _cnAberta = '';       // casa expandida no drill ('' = nenhuma)
// Ordem de entrada = QUANTIDADE DE CONTAS, decrescente (pedido do Feca). O handoff
// pedia múltiplo, mas com 29 casas isso põe no topo a casa de UMA conta, cujo
// múltiplo é ruído de amostra — e a pergunta de quem abre a tela é "onde eu tenho
// contas", não "qual amostra de 1 rendeu mais".
let _cnSortCol = 'n';
let _cnSortDir = -1;
// A sub-tabela do drill ordena por conta PRÓPRIA, independente da tabela de casas: as
// duas têm colunas diferentes, e reusar um estado só faria a de baixo herdar uma chave
// que ela não tem (e cair no `undefined`, que ordena tudo como zero, calado).
//
// Ordem de entrada = ESTADO (pedido do Feca): as ativas em cima, e as inativas da ÚLTIMA
// a ser limitada para a primeira. Era `turn` desc, que é uma pergunta de histórico ("qual
// conta girou mais desde sempre") e põe no topo uma conta encerrada há meses. A pergunta
// de quem abre uma casa é outra: *"o histórico não representa fielmente o momento"*.
let _cnDrillCol = 'estado';
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

// ── Concordância por contagem, num lugar só ──────────────────────────────────
// Ela existe porque o erro foi MEDIDO na tela: o rodapé dizia *"25 contas PASSOU de 60
// dias e puxam o número para cima"* — eu pluralizei o verbo vizinho e deixei este fixo,
// na mesma frase. A varredura que veio depois achou outros três: com UMA conta, os
// painéis diriam "As 1 próprias entram" e "As 1 sem preço ficam fora".
//
// O modo de falha é ser invisível no caso comum: toda base real tem dezenas de contas,
// então o ramo do singular quase nunca roda e o texto errado só aparece no recorte
// estreito — um fornecedor filtrado, uma casa com conta única.
function _cnPl(n,sing,plur){return n===1?sing:plur;}

// A base de cálculo do painel, escrita por extenso. Substantivo E adjetivo concordam:
// "1 conta inativa" · "184 contas inativas".
function _cnBaseTxt(n){
  const base=n.toLocaleString('pt-BR')+' '+_cnPl(n,'conta','contas');
  if(_cnPop==='ativas')return base+' '+_cnPl(n,'ativa','ativas');
  if(_cnPop==='inativas')return base+' '+_cnPl(n,'inativa','inativas');
  return base;
}

// A frase da longevidade é FUNÇÃO e não string solta porque é a única com três palavras
// que concordam entre si (conta · passar · puxar), e é justamente aí que a concordância
// escapa. Sendo função, o gate exerce as duas formas.
function _cnFraseLongevas(n,media){
  if(!n)return'';
  return` A média fica em ${media} porque ${n} ${_cnPl(n,'conta','contas')} `
    +`${_cnPl(n,'passou','passaram')} de 60 dias e ${_cnPl(n,'puxa','puxam')} `
    +`o número para cima.`;
}

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
        // `pa` = 1ª APOSTA pura, sem o cadastro. É o eixo do painel "Últimas contas", por
        // decisão do Feca: *"ordenadas pela aposta 1"*. Difere do `ini`, que é a MENOR
        // entre `adquirida_em` e a 1ª aposta — e `adquirida_em` de base migrada foi
        // DEDUZIDO por backfill, então ordenar por ele misturaria data declarada com data
        // inferida. Conta cadastrada que nunca apostou não tem `pa`, e cai no `ini`.
        ini:v.ini, fim:v.fim, adq:v.adq, pa:v.pa,
        dur:dur, dias:m.dias.size, bets:m.bets,
        turn:m.turnPer, pl:m.plPer,
        // Compra + renovações pagas até o fim do recorte (s381): é o que a conta custou
        // de fato. A mesma soma que o `_custoNaJanela('vivo')` faz para o estoque.
        // "Tem preço" é outra pergunta que "quanto custou": R$ 0 digitado TEM preço (s381).
        temPreco:(typeof _temPrecoConta==='function')?_temPrecoConta(forn,casa,nome):false,
        custo:((typeof _custoDaConta==='function')?_custoDaConta(forn,casa,nome):0)
          +((typeof _renovacoesNaJanela==='function')?_renovacoesNaJanela(v,'0000-01-01',ate).total:0),
      });
    });
  });
  const pop=_cnPop==='ativas'?out.filter(c=>c.ativa)
          :_cnPop==='inativas'?out.filter(c=>!c.ativa):out;
  return {contas:pop, de:de, ate:ate, temPeriodo:!!range, casasSel:casasSel, opsSel:opsSel};
}

// ── Os três estados de custo ─────────────────────────────────────────────────
// Própria (custo zero por natureza), COM PREÇO (qualquer valor lançado, R$ 0 incluído) e
// SEM PREÇO (nada lançado). Até a s381 a sem preço saía do ROI e do múltiplo. Decisão do
// Feca na s381: "zero é preço; sem custo lançado é sem preço. Em ambos os casos não
// tiraremos do PL e o ROI deve contá-las, mesmo que infle — porém deve-se informar o
// usuário que tem X contas sem preço". Então TODA conta entra no cálculo (a sem preço com
// custo zero) e a sem preço é MARCADA na linha e CONTADA no rodapé: o aviso é o que
// impede o ROI otimista de passar por medido.
function _cnTemPreco(c){return c.propria||!!c.temPreco;}

// O aviso das contas sem preço, UMA fonte para os rodapés do painel 2 e do 3 (duas
// cópias divergiriam no primeiro ajuste). Diz o que acontece com elas e o que fazer.
function _cnAvisoSemPreco(n){
  if(!n)return'';
  return(n===1
      ?` A <span class="cn-warnc">conta sem preço</span> entra com custo zero, e o retorno pode estar otimista.`
      :` As <span class="cn-warnc">${n} sem preço</span> entram com custo zero, e o retorno pode estar otimista.`)
    +` Lance o custo no card Custo da conta, na Extração (R$ 0 se foi grátis).`;
}

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
    if(!c.propria){if(c.temPreco)a.comPreco++;else a.semPreco++;}
    if(c.dur>0){a.durs.push(c.dur);a.somaDur+=c.dur;}
    if(c.dias>0)a.diasArr.push(c.dias);
    a.turn+=c.turn; a.pl+=c.pl; a.custo+=c.custo; a.bets+=c.bets;
    // Toda conta entra no líquido e no múltiplo (s381); a sem preço entra com custo zero.
    a.turnEleg+=c.turn;a.plEleg+=c.pl;
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
  const eleg=contas;   // toda conta entra no ROI (s381); a sem preço é avisada, não excluída
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
    nComPreco:contas.filter(c=>!c.propria&&c.temPreco).length,
    nProprias:contas.filter(c=>c.propria).length,
    nSemPreco:contas.filter(c=>!c.propria&&!c.temPreco).length,
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
  cont.innerHTML=_cnBlocoGeral(B,G,_cnPaineis(B,B.contas,''))+_cnBloco(B,linhas)+_cnDefinicoes();
}
window.renderContas=renderContas;

// ── O bloco Geral, e por que a régua NÃO se recolhe com ele ──────────────────
// O Feca: *"essa parte, com o Geral das casas deveria ser um bloco só e possível de
// minimizar para facilitar a leitura de casa a casa abaixo"*. Eram três coisas soltas
// (a faixa de escopo, os três painéis, e a seção Por casa mais abaixo) lendo como três
// seções irmãs da tela, quando as duas primeiras são UMA: o agregado da base inteira.
//
// O cabeçalho é o MESMO `.cn-secao__top` da seção "Por casa", de propósito: as duas
// seções da tela são irmãs e um segundo estilo para o mesmo papel é o item 8 do
// checklist. O acordeão também não é novo — `is-open` + caret que gira 90° é o idioma
// que o `.c2-acc` (tela Custos) já usa, que por sua vez copiou o `_tmBox`.
//
// ⚠️ A RÉGUA FICA FORA DO QUE SE RECOLHE, e isso é decisão, não descuido. Ela existe
// para impedir a tela de mentir sobre o que o filtro de período corta, e a tabela de
// baixo TAMBÉM tem coluna de duração. Recolhê-la junto esconderia o aviso exatamente
// na hora em que o usuário está lendo casa a casa, que é o momento para que o aviso
// foi escrito. Some o que é resposta; fica o que é ressalva.
function _cnBlocoGeral(B,G,corpo){
  const ab=_cnGeralAberto();
  return`<section class="cn-geral${ab?' is-open':''}" id="cnGeral">`
    +`<div class="cn-secao__top cn-geral__top" onclick="cnGeralToggle()" role="button" `
    +`tabindex="0" aria-expanded="${ab}" aria-controls="cnGeralCorpo" `
    +`onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();cnGeralToggle();}">`
    +`<span class="kpi-pipe"></span><span class="t">Geral</span>`
    +`<span class="m">${_cnBaseTxt(G.n)}</span>`
    +`<span class="cn-geral__acao" aria-hidden="true"></span>`
    +`<span class="cn-geral__caret" aria-hidden="true">▸</span></div>`
    +_cnRegua(B,G)
    +`<div class="cn-geral__corpo" id="cnGeralCorpo">${corpo}</div>`
    +`</section>`;
}

// Recolher um painel é conveniência DAQUELE navegador, não dado do usuário: é o exemplo
// que o `CLAUDE.md` cita como uso legítimo do `localStorage`. Nada aqui é digitado, nada
// precisa voltar ao servidor, e perder a preferência numa limpeza de dados custa um
// clique. Leitura e escrita em `try/catch` porque o acessor lança em janela anônima.
const CN_GERAL_KEY='cn_geral_aberto';
function _cnGeralAberto(){
  try{return localStorage.getItem(CN_GERAL_KEY)!=='0';}catch(e){return true;}
}
// Troca a CLASSE, nunca repinta a tela: repintar aqui recalcularia os agregados todos
// para mudar um `display`, e o estado do drill aberto embaixo se perderia junto.
window.cnGeralToggle=function(){
  const el=document.getElementById('cnGeral');
  if(!el)return;
  const ab=!el.classList.contains('is-open');
  el.classList.toggle('is-open',ab);
  const top=el.querySelector('.cn-geral__top');
  if(top)top.setAttribute('aria-expanded',ab?'true':'false');
  try{localStorage.setItem(CN_GERAL_KEY,ab?'1':'0');}catch(e){}
};

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
// Os três painéis servem DOIS níveis com o mesmo código: a base inteira no topo da tela
// e UMA CASA dentro do drill.
//
// Foi o Feca quem pediu o segundo nível, e o motivo é de negócio: *"a limitação de uma
// Superbet não tem nada a ver com a Betano e nada a ver com a 365"*. O agregado do topo
// mistura durabilidades que não se comparam — a mediana geral não descreve casa nenhuma.
// A alternativa que eu tinha proposto (chips de casa no painel) filtrava a TELA inteira e
// fazia perder o contexto geral; os painéis por casa mostram os dois ao mesmo tempo.
//
// `casa` preenchido muda três coisas, e só elas: o custo é pedido ao `_custoNaJanela` com
// `soCasa` (a régua única continua sendo a mesma função), o ranking deixa de ser de casas
// e passa a ser das CONTAS daquela casa, e o bloco ganha `compacto`.
// ── 4º painel: as últimas contas, só DENTRO da casa ────────────────────────
// Pedido do Feca (21/09): *"o histórico não representa fielmente o momento, então mostrar
// o que tá acontecendo recentemente vai ser importante"*. Os três painéis irmãos leem a
// vida inteira da casa; este lê só a ponta, e põe as duas leituras lado a lado — sem o
// histórico ao lado, o número recente não diz se melhorou ou piorou.
//
// Só na casa, nunca no Geral (ele foi explícito: *"apenas dentro da visa da casa"*), e a
// razão é a mesma que levou os três painéis a ganhar nível de casa: a durabilidade de
// uma Superbet não se compara com a de uma Bet365, e uma "mediana recente" da base
// inteira seria a média de coisas que não se comparam.
const CN_RECENTE_N = 10;     // quantas contas entram na CONTA
const CN_RECENTE_LISTA = 5;  // quantas aparecem na lista (ele: "não precisa ser as últimas 10")

// Eixo = 1ª APOSTA (`pa`), com o `ini` de reserva para quem nunca apostou. Decisão dele:
// *"as 10 ultimas compradas (ordenadas pela aposta 1) independente de estar on ou ja
// limitada"*. Conta sem data nenhuma fica FORA: ordenar um vazio como se fosse antigo (ou
// recente) inventaria uma posição que o dado não tem.
function _cnUltimas(contas,n){
  return contas.filter(c=>c.pa||c.ini)
    .slice().sort((a,b)=>String(b.pa||b.ini).localeCompare(String(a.pa||a.ini)))
    .slice(0,n);
}

// ⚠️ A mediana de duração sai SÓ das contas já ENCERRADAS. Duração de conta ativa é
// CENSURADA: ela ainda vai crescer, e misturá-la puxa a mediana para baixo dizendo que a
// casa piorou quando o que aconteceu foi só a conta ser nova — e o painél existe
// justamente para responder se a casa piorou. Mesma família de "zero se disfarça de conta
// feita": aqui um número incompleto se disfarçaria de número. Quando nenhuma das recentes
// encerrou não há mediana, vai `·`, e o rodapé diz por quê.
function _cnAgregadoRecente(recs,custo){
  const durs=recs.filter(c=>!c.ativa&&c.dur>0).map(c=>c.dur);
  const eleg=recs;   // mesma régua do geral (s381)
  const turn=eleg.reduce((a,c)=>a+c.turn,0);
  const pl=eleg.reduce((a,c)=>a+c.pl,0);
  return {
    n:recs.length, nAtivas:recs.filter(c=>c.ativa).length, nFechadas:durs.length,
    durMed:durs.length?_cnMediana(durs):null,
    roiLiq:turn>0?((pl-custo)/turn*100):null,
    mult:custo>0?(pl/custo):null,
    desde:recs.length?(recs[recs.length-1].pa||recs[recs.length-1].ini):'',
  };
}

// `hist` chega PRONTO dos painéis irmãos, nunca recalculado aqui: dois caminhos para o
// mesmo número é exatamente quando duas partes da tela começam a divergir, e a comparação
// deste painel perde o sentido se o lado "casa" não for o mesmo que está ao lado.
function _cnPainelRecente(B,contas,casa,hist,painel){
  const recs=_cnUltimas(contas,CN_RECENTE_N);
  if(!recs.length)return'';
  // Custo pela RÉGUA ÚNICA (`_custoNaJanela`, via `_cnCustoTotal`), com as recentes como
  // recorte. Somar `c.custo` à mão daria o mesmo número por um caminho novo.
  const R=_cnAgregadoRecente(recs,_cnCustoTotal(B,recs,casa));
  const dd=v=>v?v.slice(8,10)+'/'+v.slice(5,7):'';
  const dias=v=>v===null?'<span class="cn-sem">·</span>':Math.round(v)+' dias';
  const pct=v=>v===null?'<span class="cn-sem">·</span>':_cnPctTxt(v);
  const mlt=v=>v===null?'<span class="cn-sem">·</span>'
    :`<span class="${v>=1?'cn-roi-pos':'cn-roi-neg'}">`
     +v.toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2})+'×</span>';

  const cmp=(rot,a,b)=>`<div class="cn-crow cn-crow--cmp"><span class="cl">${rot}</span>`
    +`<span class="cn">${a}</span><span class="ch">${b}</span></div>`;
  const comp=`<div class="cn-crow cn-crow--cmp cn-crow--head"><span class="cl"></span>`
    +`<span class="cn">recentes</span><span class="ch">casa</span></div>`
    +cmp('ROI líquido',pct(R.roiLiq),pct(hist.roiLiq))
    +cmp('Múltiplo',mlt(R.mult),mlt(hist.mult));

  // A lista é curta de propósito: a tabela logo abaixo tem TODAS, e repetir dez linhas
  // aqui deixaria o painel muito mais alto que os três irmãos, que é o defeito de
  // composição do item 8 do checklist.
  const lista=recs.slice(0,CN_RECENTE_LISTA).map(c=>
    `<div class="cn-urow"><span class="nm">${esc(c.conta)}</span>`
    +`<span class="du">${c.dur} d</span>`
    +`<span class="es">${c.ativa?'<span class="cn-tag cn-tag--on">ativa</span>'
                                :'<span class="cn-tag">inativa</span>'}</span></div>`).join('');

  // O rodapé diz o que ficou FORA da conta. Sem isso, um `·` na mediana lê como defeito.
  let foot;
  if(R.durMed===null){
    foot=`Nenhuma das ${R.n} ${_cnPl(R.n,'conta','contas')} mais `
      +`${_cnPl(R.n,'recente','recentes')} encerrou, então ainda não há duração fechada `
      +`para comparar com a casa.`;
  }else{
    const hm=Math.round(hist.durMed), rm=Math.round(R.durMed), dif=Math.abs(rm-hm);
    foot=`As ${R.n} ${_cnPl(R.n,'conta','contas')} mais ${_cnPl(R.n,'recente','recentes')} `
      +`${_cnPl(R.n,'durou','duraram')} `
      +(rm===hm?'o mesmo que':`${dif} ${_cnPl(dif,'dia','dias')} `
        +`${rm<hm?'a menos':'a mais'} que`)
      +` a mediana da casa.`;
    if(R.nAtivas)foot+=` ${R.nAtivas} ${_cnPl(R.nAtivas,'segue ativa','seguem ativas')} e `
      +`${_cnPl(R.nAtivas,'fica','ficam')} fora da conta de duração.`;
  }

  return painel(`Últimas ${R.n} ${_cnPl(R.n,'conta','contas')}`,
    R.desde?`desde ${dd(R.desde)}`:'',
    'Está durando o mesmo de antes?',
    [{valor:dias(R.durMed),rotulo:'Mediana recente'},
     {valor:dias(hist.durMed),rotulo:'Mediana da casa',fraca:true}],
    `<div class="cn-comp">${comp}</div>`
    +`<div class="cn-ulist"><div class="cn-ulist__t">`
    +`as ${Math.min(CN_RECENTE_LISTA,recs.length)} mais recentes</div>${lista}</div>`,
    foot);
}

function _cnPaineis(B,contas,casa){
  const linhas=casa?[]:_cnPorCasa(contas);
  const G=_cnGeral(contas,linhas);
  // UMA chamada de custo por render. `_custoNaJanela` percorre o `_contaVida` inteiro;
  // chamá-la por painel repetiria a varredura e, pior, abriria a porta para dois
  // painéis vizinhos mostrarem custos diferentes se alguém mudasse um dos argumentos.
  const custo=_cnCustoTotal(B,contas,casa);
  const turnEleg=contas.reduce((a,c)=>a+c.turn,0);   // toda conta entra (s381)
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
  // ⚠️ O rodapé conta O QUE OS NÚMEROS DIZEM sobre esta base, e PARA AÍ.
  //
  // Duas correções empilhadas, em duas rodadas do Feca. A redação original ("Mediana é a
  // conta do meio… Média incorpora as exceções e mede o prêmio da cauda") era uma aula de
  // estatística que não respondia nem *por que estou vendo isso* — ele leu e disse que
  // nem ele entendia. A segunda tentativa consertou isso e foi longe demais: terminava em
  // *"Para estimar a próxima compra, use 12, não 34"*, e ali o produto deixou de informar
  // e passou a ACONSELHAR.
  //
  // **O produto informa; quem conclui é o dono.** É a mesma régua que ele já tinha
  // cravado no handoff sobre não comparar durabilidade entre fornecedores ("nós não somos
  // quem vai falar q joão dura mais q francisco"): a informação aparece, o veredito não.
  // Gate: `test_a_tela_nao_aconselha_o_usuario`.
  //
  // A régua do texto, então: cada frase cita um número DESTA base e explica o que ele
  // descreve. Nenhuma frase diz o que fazer com ele.
  const pctCurto=G.hist.length?Math.round(G.hist[0].pct):0;
  const p1=painel('Longevidade',
    // O contexto do painel é a BASE DE CÁLCULO dele, então ele diz o que está contando:
    // "184 contas inativas", nunca "184 inativas" (o Feca leu e precisou perguntar se
    // era isso mesmo). O ADJETIVO concorda junto — escrevi "1 conta inativas" na
    // primeira tentativa, que é o mesmo erro que ele tinha acabado de apontar.
    _cnBaseTxt(G.n),
    'Quanto tempo uma conta permanece operacional?',
    [{valor:med+' dias',rotulo:'Mediana'},
     {valor:media+' dias',rotulo:'Média',fraca:true}],
    `<div class="cn-dist">${hist}</div>`,
    `<b>Metade ${casa?'das contas da '+esc(casa):'das suas contas'} durou menos de ${med} dias</b>`
    +(pctCurto?`, e ${pctCurto}% não passou da primeira semana.`:'.')
    +(media>med?_cnFraseLongevas(G.longevas,media):''));

  // ── 2 · VOLUME E MARGEM ──
  // Dentro de uma casa o ranking de CASAS não diz nada (é sempre uma linha), então ali
  // ele vira o ranking das CONTAS daquela casa por turnover. Mesma forma, outro eixo.
  // O ranking lista as casas onde MAIS CONTAS FORAM COMPRADAS, não as de maior
  // turnover (pedido do Feca: "o importante é estar as casas q mais contas foram
  // compradas"). Casa cujas contas são todas PRÓPRIAS fica de fora: ela não foi
  // comprada, então não disputa esse lugar — era o caso da Polymarket, com 1 conta
  // própria ocupando uma das cinco linhas.
  const rank=(casa
    ? contas.slice().sort((a,b)=>b.turn-a.turn).slice(0,5).map(c=>{
        // Conta sem preço fica FORA do ROI (ausência não é zero) e a linha DIZ isso
        // (s381). O "·" mudo leu como "não puxou o P/L" para o tester Gabriel, em duas
        // contas arquivadas cujo P/L estava certo e só faltava o custo.
        const semPreco=!_cnTemPreco(c);
        const roiC=c.turn>0?((c.pl-c.custo)/c.turn*100):null;
        return`<div class="cn-mrow"><span class="nm">${esc(c.conta)}${semPreco
            ?' <span class="cn-sem cn-warnc" title="Sem custo lançado: a conta entra no ROI com custo zero. Lance o custo no card Custo da conta, na Extração (R$ 0 se foi grátis).">sem preço</span>'
            :''}</span>`
          +`<span class="vv vv--conta"><b>${fmtR(c.turn)}</b> · ${_cnPctTxt(roiC)}</span></div>`;
      })
    : linhas.filter(c=>c.comPreco>0).sort((a,b)=>b.comPreco-a.comPreco).slice(0,5).map(c=>
        `<div class="cn-mrow"><span class="nm">${mkHouseChip(c.casa)}${esc(c.casa)}</span>`
        +`<span class="vv"><b class="q">${c.comPreco}</b>`
        +`<span class="u">${_cnPl(c.comPreco,'conta','contas')}</span>`
        +`<span class="p">${_cnPctTxt(c.roiLiq)}</span></span></div>`)
    ).join('')||`<div class="cn-vazio">Nenhuma conta comprada no recorte.</div>`;
  const roiLiq=turnEleg>0?((G.plEleg-custo)/turnEleg*100):0;
  const p2=painel('Volume e margem', B.temPeriodo?'no período':'histórico',
    'Quanto cada conta movimenta e que margem sobra?',
    [{valor:fmtPct(roiLiq,2),rotulo:'ROI líquido'},
     {valor:fmtPct(G.roiBruto,2),rotulo:'ROI bruto',fraca:true}],
    `<div class="cn-mini">${rank}</div>`,
    `Cada conta movimentou ${fmtR(G.turnConta)} em ${Math.round(G.diasMedia)} dias ativos, `
    +`em média. <b>O líquido é o que sobra depois do custo da conta</b>; a diferença para o `
    +`bruto é o quanto a aquisição come da margem.`
    // As sem preço entram nos dois ROIs com custo zero (s381): o aviso diz quantas são.
    +_cnAvisoSemPreco(G.nSemPreco));

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
    ? (G.nProprias===1
        ? ' A conta própria entra com custo zero real.'
        : ` As ${G.nProprias} próprias entram com custo zero real.`)
    : '';
  const notaSem=G.nSemPreco?_cnAvisoSemPreco(G.nSemPreco):' Toda conta do recorte tem preço lançado.';
  const multTxt=mult===null?'·'
    :mult.toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2})+'×';
  // Título do Feca. Ele resolve o português ruim de "quanto o CUSTO devolveu" (custo não
  // devolve) sem tocar no vocabulário que o `test_o_vocabulario_proibido_nao_volta_ao_produto`
  // barra desde a s358. A primeira sugestão dele caía numa VARIANTE de grafia de uma das
  // três palavras de lá: o gate só lista a forma exata, e entrar pela variante seria
  // driblar uma regra dele com um sinônimo. Por isso a palavra usada aqui é `custo`.
  //
  // Com o título dizendo "retorno sobre o custo", a pergunta antiga virava eco. Ela
  // passa a ser a DECISÃO que o múltiplo informa, que é outra coisa: acima de 1,00× a
  // conta se pagou, abaixo não.
  //
  // "das contas" saiu por MEDIDA, nao por gosto: em 1366 o titulo inteiro quebrava em
  // duas linhas (28px contra os 14px dos vizinhos) e empurrava a figura 14px para baixo,
  // desalinhando os tres paineis. O contexto a direita ja diz "N de N contas".
  const p3=painel('Retorno sobre o custo',
    `${nEleg} de ${G.n} ${_cnPl(G.n,'conta','contas')}`,
    'As contas se pagaram?',
    [{valor:multTxt,rotulo:'Múltiplo'}],
    `<div class="cn-comp">${comp}</div>${cov}`,
    (mult!==null
      ? `<b>Cada R$ 1 gasto em conta voltou ${multTxt.replace('×','')} reais.</b> `
        +`Abaixo de 1,00× a conta não devolveu o que custou.`
      : 'Sem preço lançado não há múltiplo: ele compara o P/L com o que foi pago.')
    +notaProp+notaSem);

  // O 4º painel só existe DENTRO da casa, e recebe os números históricos JÁ CALCULADOS
  // pelos irmãos (`roiLiq` é o mesmo do p2, `mult` o mesmo do p3, `durMed` o mesmo do p1).
  // Recalcular aqui criaria um segundo caminho para o mesmo número, e a comparação perde
  // o sentido no dia em que os dois divergirem.
  const p4=casa?_cnPainelRecente(B,contas,casa,
    {durMed:G.durMed,roiLiq:roiLiq,mult:mult},painel):'';
  return`<div class="cn-q3 ${casa?'compacto':''} ${p4?'q4':''}">${p1}${p2}${p3}${p4}</div>`;
}

// O custo total sai do `_custoNaJanela` — régua ÚNICA com `calcCostFiltered`, com a
// Visão Geral e com o drill de Bookies. Somar `_custoDaConta` linha a linha daria hoje
// o mesmo número por um caminho novo, e duas derivações para a mesma pergunta divergem
// no primeiro caso de borda.
function _cnCustoTotal(B,contas,soCasa){
  const alvo=contas||B.contas;
  const contasOk=new Set(alvo.map(c=>c.chave));
  if(typeof _custoNaJanela!=='function')return alvo.reduce((a,c)=>a+c.custo,0);
  // `soCasa` é parâmetro da PRÓPRIA `_custoNaJanela`: recortar por casa aqui continua
  // sendo a régua única, e não uma soma paralela.
  return _custoNaJanela(B.de,B.ate,B.casasSel,B.opsSel,soCasa||'','pago',contasOk).total;
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
      +`<span class="sub">${a.ativas} ${_cnPl(a.ativas,'ativa','ativas')}</span></div>`
      +`<div class="cn-fcell"><div class="n">${a.n}</div>`
      +  `<div class="s">${_cnPl(a.n,'conta','contas')}</div></div>`
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
      // Casa só com contas de R$ 0 digitado TEM custo lançado: ele é zero (s381).
      +  `<div class="s">${a.custo>0||a.comPreco>0?'custo '+fmtR(a.custo):'<span class="cn-sem">sem custo lançado</span>'}</div></div>`
      +`<div class="cn-multwrap"><div class="n">${_cnMult(a.mult)}</div>`
      +  `<div class="cn-gauge"><i class="${under?'under':''}" style="width:${gMult.toFixed(1)}%"></i>`
      +  `<span class="th" style="left:${100/CN_GAUGE_MAX}%"></span></div></div>`
      +`</div>`;
    if(aberta)html+=_cnDrill(B,a,B.contas.filter(c=>c.casa===a.casa));
    return html;
  }).join('')||'<div class="cn-vazio">Nenhuma conta no recorte.</div>';

  // UMA faixa, não duas. O título "Por casa", a dica de clique e a legenda da barra
  // eram três blocos soltos e liam como seções diferentes da tela (o Feca: "parece
  // inclusive que são duas sessões"). Agora é um cabeçalho só, com a legenda dentro
  // dele, encostado na tabela que ele apresenta.
  return`<div class="cn-secao">`
    +`<div class="cn-secao__top"><span class="kpi-pipe"></span><span class="t">Por casa</span>`
    +`<span class="m">clique na casa para abrir as contas · ordenável por qualquer coluna</span></div>`
    +`<div class="cn-secao__leg"><span class="cn-mks">`
    +`<span class="cn-mk2"><i class="s"></i>mediana</span>`
    +`<span class="cn-mk2"><i class="d"></i>média</span></span>`
    +`<p>Barra sólida curta com o pontilhado distante indica <b>casa que depende de exceções</b>: `
    +`a conta típica encerra cedo e o resultado vem de poucas sobreviventes. `
    +`Ambas na mesma régua de 0 a ${CN_REGUA_DIAS} dias.</p></div></div>`
    +`<div class="cn-ovf"><div class="cn-fichas">`
    +`<div class="cn-fhead">${th('casa','Casa','l')}`
    +`${th('n','Contas')}`
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
// Ordenação da sub-tabela do drill, FORA do `_cnDrill` para poder ser executada por
// teste: recortar a função que monta o HTML arrastaria `fmtR`, `fmtPL`, `esc` e o
// resto junto, e a alternativa (reimplementar o comparador no teste) é o primeiro
// modo de falso verde que o `CLAUDE.md` lista.
//
// ⚠️ O desempate de ESTADO é explícito, e não herdado da ordem natural do array. O sort
// do V8 é estável, então um empate "acerta" sozinho sempre que a ordem de entrada já for
// a esperada — e aí o critério não está sendo exercido, só parecendo funcionar. Aqui o
// grupo `inativa` empata SEMPRE (todas valem 0), então sem esta linha a ordem dentro
// dele seria a de construção, que é a do cadastro.
//
// Recência = `fim` (a régua de `_buildContaVida`: a MAIOR entre a última aposta e o
// `arquivada_em`). Para a conta ativa e cadastrada `fim` é HOJE, então as ativas também
// empatam entre si e caem no segundo desempate, `ini` — a última comprada em cima, que é
// a leitura certa para quem ainda não morreu.
function _cnOrdenarDrill(contas,key,dir){
  const txt=k=>k==='conta'||k==='forn';
  const val=(c,k)=>{
    if(k==='estado')return c.ativa?1:0;
    if(k==='liq')return c.pl-c.custo;
    if(k==='roiLiq')return c.turn>0?((c.pl-c.custo)/c.turn):null;
    return c[k];
  };
  const recente=(a,b)=>String(b.fim||'').localeCompare(String(a.fim||''))
                     ||String(b.ini||'').localeCompare(String(a.ini||''));
  return contas.slice().sort((a,b)=>{
    if(txt(key))return a[key].localeCompare(b[key],'pt-BR')*(-dir);
    if(key==='ini'||key==='fim')return String(a[key]||'').localeCompare(String(b[key]||''))*dir;
    const va=val(a,key), vb=val(b,key);
    if(va===null&&vb===null)return 0;
    if(va===null)return 1;
    if(vb===null)return -1;
    if(va===vb&&key==='estado')return recente(a,b);
    return ((va||0)-(vb||0))*dir;
  });
}

function _cnDrill(B,agg,contas){
  // `key`/`dir` continuam aqui porque o CABECALHO tambem os le (a seta de ordenacao no
  // `<th>`), e nao so o comparador.
  const dir=_cnDrillDir, key=_cnDrillCol;
  const ord=_cnOrdenarDrill(contas,key,dir);

  const rows=ord.map(c=>{
    const liq=c.pl-c.custo;
    const roiLiq=c.turn>0?(liq/c.turn*100):null;
    // Tag, não texto com bolinha: "· inativa" ficava como sobra de linha, e o estado é
    // o eixo que a tela inteira usa para separar população. Pedido do Feca.
    const est=c.ativa
      ? '<span class="cn-tag cn-tag--on">ativa</span>'
      : '<span class="cn-tag">inativa</span>';
    // Os três estados de custo, visualmente distintos. `sem preço` em `--warn`; o
    // líquido e o ROI líquido saem com custo zero (s381) e o rodapé avisa. R$ 0 digitado
    // é preço e aparece como R$ 0, igual a qualquer valor.
    const custo=c.propria?'<span class="cn-propria">própria</span>'
              :c.temPreco?fmtR(c.custo)
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
      +`<td class="k">${fmtPL(liq)}</td>`
      +`<td class="k">${roiLiq!==null?_cnPctTxt(roiLiq):'<span class="cn-sem">·</span>'}</td>`
      +`</tr>`;
  }).join('');

  // O `stopPropagation` em cada `<th>` é obrigatório: a LINHA DA CASA abre e fecha o
  // drill no clique, e sem ele ordenar a sub-tabela fecharia o painel inteiro.
  const dth=(col,lbl,cls)=>`<th class="${cls||''} ${key===col?'sort-'+(dir<0?'desc':'asc'):''}"`
    +` onclick="event.stopPropagation();cnDrillSort('${col}')">${lbl}<span class="sort-icon"></span></th>`;
  const aviso=agg.semPreco>0
    ?`<span class="w">${agg.semPreco} ${_cnPl(agg.semPreco,'conta','contas')} sem preço, com custo zero no cálculo</span>`:'';
  // Os TRÊS PAINÉIS da casa vêm antes da tabela: é o pedido do Feca de ter "isso dentro
  // de cada casa seguido da tabela com a lista". O agregado do topo mistura casas que não
  // se comparam; aqui cada uma responde por si, na mesma linguagem visual.
  return`<div class="cn-drill" onclick="event.stopPropagation()">`
    +_cnPaineis(B,contas,agg.casa)
    +`<table class="cn-tbl"><thead><tr>`
    +dth('conta','Conta','l')+dth('forn','Fornecedor','l')+dth('estado','Estado','l')
    +dth('dur','Duração')+dth('dias','Dias ativos')+dth('bets','Apostas')+dth('turn','Turnover')
    +dth('pl','P/L bruto')+dth('custo','Custo')+dth('liq','P/L líquido')+dth('roiLiq','ROI líq.')
    +`</tr></thead><tbody>${rows}</tbody></table>`
    +`<div class="cn-drillfoot"><span>${contas.length} ${_cnPl(contas.length,'conta','contas')} nesta casa</span>`
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
