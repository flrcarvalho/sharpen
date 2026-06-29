// FONTE DE DADOS: servido pelo próprio Planilhador (mesma origem) → lê o Postgres,
// filtrado pelo login. Substitui o Apps Script/planilha (que segue vivo como backup
// congelado no GitHub Pages). Mesmo contrato {ok,data,builtAt,count} do Code.gs.
const APPS_SCRIPT_URL="/dashboard/data";
const BASE_BANK=100000;
// Mapa de ícones das casas (favicon via Google S2)
const CASA_ICONS={
  '7K':'https://www.google.com/s2/favicons?sz=128&domain=7k.bet.br',
  'Bateu':'https://www.google.com/s2/favicons?sz=128&domain=bateu.bet.br',
  'Bet365':'https://www.google.com/s2/favicons?sz=128&domain=bet365.com',
  'Betano':'https://www.google.com/s2/favicons?sz=128&domain=betano.com',
  'Betao':'https://www.google.com/s2/favicons?sz=128&domain=betao.bet.br',
  'Betão':'https://www.google.com/s2/favicons?sz=128&domain=betao.bet.br',
  'Betboom':'https://www.google.com/s2/favicons?sz=128&domain=betboom.bet.br',
  'Faz1bet':'https://www.google.com/s2/favicons?sz=128&domain=faz1.bet.br',
  'Polymarket':'https://www.google.com/s2/favicons?sz=128&domain=polymarket.com',
  'Betboo':'https://www.google.com/s2/favicons?sz=128&domain=betboo.com',
  'Betbra':'https://www.google.com/s2/favicons?sz=128&domain=betbra.bet.br',
  'BETesporte':'https://www.google.com/s2/favicons?sz=128&domain=betesporte.bet.br',
  'Betfair':'https://www.google.com/s2/favicons?sz=128&domain=betfair.com',
  'Betfast':'https://www.google.com/s2/favicons?sz=128&domain=betfast.bet.br',
  'Betfusion':'https://www.google.com/s2/favicons?sz=128&domain=betfusion.bet.br',
  'BetMGM':'https://www.google.com/s2/favicons?sz=128&domain=betmgm.bet.br',
  'Betnacional':'https://www.google.com/s2/favicons?sz=128&domain=betnacional.com',
  'Betpontobet':'https://www.google.com/s2/favicons?sz=128&domain=bet.com.br',
  'Bolsa de Aposta':'https://www.google.com/s2/favicons?sz=128&domain=bolsadeaposta.bet.br',
  'Casa de Apostas':'https://www.google.com/s2/favicons?sz=128&domain=casadeapostas.com',
  'Donald Bet':'https://www.google.com/s2/favicons?sz=128&domain=donald.bet.br',
  'Esportes da Sorte':'https://www.google.com/s2/favicons?sz=128&domain=esportesdasorte.com',
  'Esportiva':'https://www.google.com/s2/favicons?sz=128&domain=esportiva.bet.br',
  'Estrela Bet':'https://www.google.com/s2/favicons?sz=128&domain=estrelabet.com',
  'Fulltbet':'https://www.google.com/s2/favicons?sz=128&domain=fulltbet.bet.br',
  'KTO':'https://www.google.com/s2/favicons?sz=128&domain=kto.com',
  'Lance de Sorte':'https://www.google.com/s2/favicons?sz=128&domain=lancedesorte.bet.br',
  'Liderbet':'https://www.google.com/s2/favicons?sz=128&domain=lider.bet.br',
  'MatchBook':'https://www.google.com/s2/favicons?sz=128&domain=matchbook.com',
  'MultiBet':'https://www.google.com/s2/favicons?sz=128&domain=multi.bet.br',
  'Novibet':'https://www.google.com/s2/favicons?sz=128&domain=novibet.com',
  'Pinnacle':'https://www.google.com/s2/favicons?sz=128&domain=pinnacle.com',
  'PixBet':'https://www.google.com/s2/favicons?sz=128&domain=pixbet.com',
  'Rei do Pitaco':'https://www.google.com/s2/favicons?sz=128&domain=reidopitaco.com.br',
  'SportingBet':'https://www.google.com/s2/favicons?sz=128&domain=sportingbet.com',
  'Superbet':'https://www.google.com/s2/favicons?sz=128&domain=superbet.com',
  'Tivo':'https://www.google.com/s2/favicons?sz=128&domain=tivo.bet.br',
};
// Mapa de domínios para chips de casa (favicon via favicon())
// Para produção offline/nítida: substituir favicon() por assets/casas/NOME.png
const HOUSE_DOMAIN={
  '7K':'7k.bet.br',
  'Bateu':'bateu.bet.br',
  'Bet365':'bet365.com',
  'Betano':'betano.com',
  'Betao':'betao.bet.br',
  'Betão':'betao.bet.br',
  'Betboom':'betboom.bet.br',
  'Faz1bet':'faz1.bet.br',
  'Polymarket':'polymarket.com',
  'Betboo':'betboo.com',
  'Betbra':'betbra.bet.br',
  'BETesporte':'betesporte.bet.br',
  'Betfair':'betfair.com',
  'Betfast':'betfast.bet.br',
  'Betfusion':'betfusion.bet.br',
  'BetMGM':'betmgm.bet.br',
  'Betnacional':'betnacional.com',
  'Betpontobet':'betpontobet.bet.br',
  'Bolsa de Aposta':'bolsadeaposta.bet.br',
  'Casa de Apostas':'casadeapostas.com',
  'Donald Bet':'donald.bet.br',
  'Esportes da Sorte':'esportesdasorte.com',
  'Esportiva':'esportiva.bet.br',
  'Estrela Bet':'estrelabet.com',
  'Fulltbet':'fulltbet.bet.br',
  'KTO':'kto.com',
  'Lance de Sorte':'lancedesorte.bet.br',
  'Liderbet':'lider.bet.br',
  'MatchBook':'matchbook.com',
  'MultiBet':'multi.bet.br',
  'Novibet':'novibet.com',
  'Pinnacle':'pinnacle.com',
  'PixBet':'pixbet.com',
  'Rei do Pitaco':'reidopitaco.com.br',
  'SportingBet':'sportingbet.com',
  'Superbet':'superbet.com',
  'Tivo':'tivo.bet.br',
};
const MESES=['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro'];
const MESES_CURTOS=['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez'];
const TC_COLORS=['#2BC07E','#2E8BFF','#E0A21A','#7FB2FF','#E5524B','#34d399','#fbbf24','#60a5fa','#fb923c','#AEB7C2','#95A1B0','#1E7CF0','#fbbf24','#2BC07E','#2E8BFF'];

// Mapa de emojis por chave de esporte — fallback universal: 🏅
const SPORT_EMOJI={
  futebol:'⚽', basquete:'🏀', tenis:'🎾', mma:'🥊', f1:'🏎️',
  nfl:'🏈', nhl:'🏒', baseball:'⚾', volei:'🏐', handbol:'🤾',
  dardos:'🎯', esports:'🎮', multiplos:'🔗', peixe:'🐟',
  snooker:'🎱', golf:'⛳', rugby:'🏉',
};
// Sport SVG icons — minimal line style
const SPORT_SVG={
  futebol:`<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6.2"/><polygon points="8,4.5 9.8,6.2 9.2,8.4 6.8,8.4 6.2,6.2" stroke-width="1.2"/><line x1="8" y1="1.8" x2="8" y2="4.5"/><line x1="13.4" y1="5.2" x2="9.8" y2="6.2"/><line x1="11.6" y1="12.5" x2="9.2" y2="8.4"/><line x1="4.8" y1="12.5" x2="6.8" y2="8.4"/><line x1="2.6" y1="5.2" x2="6.2" y2="6.2"/></svg>`,
  basquete:`<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"><circle cx="8" cy="8" r="6.2"/><path d="M8 1.8 Q11.5 8 8 14.2"/><path d="M8 1.8 Q4.5 8 8 14.2"/><line x1="1.8" y1="8" x2="14.2" y2="8"/></svg>`,
  tenis:`<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="8" r="6.2"/><path d="M3.2 11.8 Q8 6 12.8 11.8"/><path d="M3.2 4.2 Q8 10 12.8 4.2"/></svg>`,
  mma:`<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12 L4 8 Q4 5 7 5 L9 5 Q11 5 12 7 L13 9"/><path d="M4 8 L7 8"/><circle cx="11" cy="4.5" r="1.5"/></svg>`,
  f1:`<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><path d="M1.5 10 L3 9 L5 9.5 L8 8 L12 8.5 L14.5 7.5"/><path d="M5 9.5 L5 11.5 Q5 12 5.5 12 L10.5 12 Q11 12 11 11.5 L11 10 L8 8"/><circle cx="5.5" cy="12.5" r="1" fill="currentColor" stroke="none"/><circle cx="10.5" cy="12.5" r="1" fill="currentColor" stroke="none"/></svg>`,
  nfl:`<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="8" cy="8" rx="6" ry="4"/><line x1="8" y1="4" x2="8" y2="12"/><line x1="5.5" y1="5.5" x2="5.5" y2="10.5"/><line x1="10.5" y1="5.5" x2="10.5" y2="10.5"/></svg>`,
  nhl:`<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5 L5 5 L8 11 L11 5 L13 5"/><line x1="3" y1="5" x2="13" y2="5"/><ellipse cx="8" cy="13" rx="4" ry="1.2"/></svg>`,
  baseball:`<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"><circle cx="8" cy="8" r="6.2"/><path d="M5.5 2.5 Q6.5 8 5.5 13.5"/><path d="M10.5 2.5 Q9.5 8 10.5 13.5"/></svg>`,
  volei:`<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"><circle cx="8" cy="8" r="6.2"/><path d="M1.8 8 Q5 5 8 8 Q11 11 14.2 8"/><path d="M4.5 3.2 Q6 8 4.5 12.8"/><path d="M11.5 3.2 Q10 8 11.5 12.8"/></svg>`,
  handbol:`<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><circle cx="7" cy="4.5" r="1.8"/><path d="M7 6.3 L7 10 L5 13"/><path d="M7 10 L9 13"/><path d="M5 8 L9 8"/></svg>`,
  dardos:`<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"><circle cx="8" cy="8" r="6.2"/><circle cx="8" cy="8" r="3.5"/><circle cx="8" cy="8" r="1.2"/><line x1="8" y1="1.8" x2="8" y2="4.6"/><line x1="8" y1="11.4" x2="8" y2="14.2"/></svg>`,
  esports:`<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="5" width="12" height="7" rx="2"/><line x1="8" y1="7" x2="8" y2="10"/><line x1="6.5" y1="8.5" x2="9.5" y2="8.5"/><circle cx="11" cy="8.5" r=".8" fill="currentColor" stroke="none"/></svg>`,
  multiplos:`<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="5.5" height="5.5" rx="1"/><rect x="8.5" y="2" width="5.5" height="5.5" rx="1"/><rect x="2" y="8.5" width="5.5" height="5.5" rx="1"/><rect x="8.5" y="8.5" width="5.5" height="5.5" rx="1"/></svg>`,
  peixe:`<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><path d="M9 8 Q13 4 15 8 Q13 12 9 8Z"/><path d="M9 8 Q5 6 2 8 Q5 10 9 8"/><path d="M2 6 L1 8 L2 10"/><circle cx="12.5" cy="7" r=".6" fill="currentColor" stroke="none"/></svg>`,
  snooker:`<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"><circle cx="8" cy="8" r="6.2"/><circle cx="8" cy="7" r="2.2"/><line x1="8" y1="9.2" x2="8" y2="13"/></svg>`,
  golf:`<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="2" x2="8" y2="12"/><path d="M8 2 L13 4.5 L8 7Z"/><ellipse cx="8" cy="13.5" rx="4" ry="1.2"/></svg>`,
  rugby:`<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"><ellipse cx="8" cy="8" rx="5.5" ry="3.5"/><line x1="8" y1="4.5" x2="8" y2="11.5"/><line x1="5.2" y1="6.5" x2="10.8" y2="6.5"/><line x1="5.2" y1="9.5" x2="10.8" y2="9.5"/></svg>`,
  outro:`<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"><circle cx="8" cy="8" r="6.2"/><line x1="8" y1="5" x2="8" y2="8.5"/><circle cx="8" cy="11" r=".8" fill="currentColor" stroke="none"/></svg>`,
};
// Alias map: sport name → svg key
const SPORT_KEY={
  'Futebol':'futebol','Fútbol':'futebol','Soccer':'futebol',
  'NBA':'basquete','Basquete':'basquete','Basquetebol':'basquete','Basketball':'basquete','Nba':'basquete',
  'Tênis':'tenis','Tenis':'tenis','Tennis':'tenis','Tênis de Mesa':'tenis','Ping Pong':'tenis',
  'MMA':'mma','UFC':'mma','Boxe':'mma','Boxing':'mma','Luta':'mma',
  'F1':'f1','Formula 1':'f1','Fórmula 1':'f1','Formula1':'f1',
  'NFL':'nfl','Futebol Americano':'nfl',
  'NHL':'nhl','Hóquei':'nhl','Hockey':'nhl',
  'MLB':'baseball','Baseball':'baseball','Beisebol':'baseball',
  'Vôlei':'volei','Volei':'volei','Volleyball':'volei',
  'Handeball':'handbol','Handebol':'handbol','Handball':'handbol',
  'Dardos':'dardos','Darts':'dardos',
  'CS':'esports','CS:GO':'esports','Counter-Strike':'esports','E-Sports':'esports','Esports':'esports','eSports':'esports',
  'Multiplos':'multiplos','Múltiplos':'multiplos','Multiple':'multiplos',
  'Peixe':'peixe','Fish':'peixe',
  'Snooker':'snooker',
  'Golf':'golf','Golfe':'golf',
  'Rugby':'rugby','Cricket':'rugby',
  'Outro':'outro','Other':'outro','Outros':'outro',
};
function sportSvg(nome,size=14){
  if(!nome)return'';
  let key=SPORT_KEY[nome];
  if(!key){const k=Object.keys(SPORT_KEY).find(k=>k.toLowerCase()===nome.toLowerCase());key=k?SPORT_KEY[k]:'outro';}
  const svg=SPORT_SVG[key]||SPORT_SVG.outro;
  return`<span style="display:inline-flex;align-items:center;justify-content:center;width:${size}px;height:${size}px;flex-shrink:0;opacity:.75">${svg}</span>`;
}
function sportEmoji(nome){
  if(!nome)return'🏅';
  let key=SPORT_KEY[nome];
  if(!key){const k=Object.keys(SPORT_KEY).find(k=>k.toLowerCase()===nome.toLowerCase());key=k?SPORT_KEY[k]:null;}
  return SPORT_EMOJI[key]||'🏅';
}
function sportCell(nome){
  let key=SPORT_KEY[nome];
  if(!key){const k=Object.keys(SPORT_KEY).find(k=>k.toLowerCase()===nome?.toLowerCase());key=k?SPORT_KEY[k]:null;}
  const emoji=SPORT_EMOJI[key]||'🏅';
  return`<span style="display:inline-flex;align-items:center;gap:6px"><span class="sp-chip">${emoji}</span>${nome||'—'}</span>`;
}

let DADOS=[], charts={};

// Theme

