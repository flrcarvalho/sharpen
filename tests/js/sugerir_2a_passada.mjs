// A 2ª passada do perfil DECLARADO (s310): ela existe, e a folga alta é o que a torna segura.
//
// Contexto: desde a s289 o caminho principal é a base rotulada (`app/matcher.py`). Ela sabe do
// tipster que viu mil vezes e **não sabe nada** de quem entrou semana passada — perfil sem
// histórico nem entra na disputa, e a coluna fica vazia em silêncio. O Feca tinha `Stake Final 3`
// escrito no perfil do Fusion e o Fusion era sugerido 0% das vezes.
//
// A 2ª passada devolve a voz ao que ele declarou, com dois cortes vindos do SERVIDOR:
//   · só sobre `novatos` (a base mal os viu);
//   · com `folga_declarada` bem acima dos 7 do caminho principal.
//
// A folga é o corte que faz a diferença, e é medível: com 7 o ganho na carteira do Feca é
// +148 acertos / +72 erros (2,1:1); com 25, +139 / +28 (5,0:1). O motivo é a escala de pesos do
// próprio declarativo — stake 25-50, esporte/mercado exclusivos 10, casa 5 — então exigir 25
// significa "só fale quando a assinatura de STAKE decidir sozinha". Esporte + mercado somados
// (10+10) deixam de bastar, e era daí que vinha o ruído (SóChutes→Arrudex, 83 confusões).
//
// O código sob teste é RECORTADO do `index.html`. Teste que reimplementa o código não detecta a
// mutação que o quebra — é a regra "teste verde não é teste que detecta" do CLAUDE.md.
//
// O que este teste NÃO cobre: a rota (está em `tests/test_rota_sugerir.py`), o `salvarTipsterVal`
// (rede) e a decisão de quem é novato (é do servidor, por desenho).
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const CR = String.fromCharCode(13), LF = String.fromCharCode(10);
const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const ALVO = process.env.ALVO_INDEX || path.join(RAIZ, 'app', 'static', 'index.html');
const html = fs.readFileSync(ALVO, 'utf8').split(CR + LF).join(LF);

const corte = (ini, fim) => {
  const a = html.indexOf(ini); if (a < 0) throw new Error('não achei: ' + ini);
  const b = html.indexOf(fim, a); if (b < 0) throw new Error('não achei fim de: ' + ini);
  return html.slice(a, b + fim.length);
};

const src = [
  // os tres primeiros sao arrow de uma linha; os demais, funcoes de bloco
  corte('const _sugNorm =', ';'),
  corte('const _sugSlug =', ';'),
  corte('const _sugSplit =', ';'),
  corte('function _numBR(', LF + '}'),
  corte('function _parseStakeSig(', LF + '}'),
  corte('function _parseCentavos(', LF + '}'),
  corte('function _stakeSignal(', LF + '}'),
  corte('function _declaraStake(', LF + '}'),
  corte('function _buildSugIndex(', LF + '}'),
  corte('function _sugRanqueia(', LF + '}'),
  corte('function _sugParaBilhete(', LF + '}'),
].join(LF);

// ── Ambiente dublado: só o que o código recortado toca. ──
const mk = (profs, dedicadas = {}) => {
  const amb = `
    const tipsterProfiles = ${JSON.stringify(profs)};
    const _casasDedicadas = ${JSON.stringify(dedicadas)};
  `;
  const f = new Function(amb + LF + src + LF +
    'return {_buildSugIndex,_sugParaBilhete,_sugRanqueia};');
  return f();
};
const P = (nome, o = {}) => ({ nome, esportes: '', casas: '', mercados: '', dica_stake: '', obs: '', ...o });

let falhas = 0;
const ok = (cond, msg) => { if (!cond) { falhas++; console.log('  FALHOU: ' + msg); } else console.log('  ok: ' + msg); };

console.log('1) a ASSINATURA DE STAKE sozinha passa na folga alta — é para isso que a 2ª passada existe');
{
  // O caso real do Feca: o Fusion declara "Stake Final 3" e mais nada. A base nunca o viu.
  const G = mk([P('Fusion', { dica_stake: 'Stake Final 3' }), P('Outro', { esportes: 'Tênis' })]);
  const idx = G._buildSugIndex();
  const b = { casa: 'Bet365', esporte: 'Futebol', aposta: 'Múltipla', stake: '503,00', descricao: 'A // B' };
  ok(G._sugParaBilhete(b, idx, 25) === 'Fusion', 'final 3 declarado decide sozinho e vence a folga 25');
  const b2 = { ...b, stake: '500,00' };   // final 0 — não é a assinatura dele
  ok(G._sugParaBilhete(b2, idx, 25) === null, 'stake que não bate a assinatura NÃO passa');
}

console.log('2) folga alta cala o acerto barato de esporte + mercado + casa');
{
  // `Grande` soma 10 (esporte exclusivo) + 10 (mercado exclusivo) + 1 (casa compartilhada) = 21.
  // `Vizinho` fica com 1 (só a casa). Folga 20: passa em 7, não passa em 25.
  const G = mk([P('Grande', { esportes: 'Futebol', mercados: 'Múltipla', casas: 'Bet365' }),
                P('Vizinho', { casas: 'Bet365' })]);
  const idx = G._buildSugIndex();
  const b = { casa: 'Bet365', esporte: 'Futebol', aposta: 'Múltipla', stake: '77,00', descricao: 'A' };
  ok(G._sugParaBilhete(b, idx, 7) === 'Grande', 'com folga 7 ele é sugerido (é o comportamento de hoje)');
  ok(G._sugParaBilhete(b, idx, 25) === null,
     'com folga 25 ele se cala — somar rótulos declarados não basta, é preciso a stake');
}

console.log('3) o default continua 7 — o caminho principal (dono sem histórico) não muda');
{
  const G = mk([P('Grande', { esportes: 'Futebol', mercados: 'Múltipla', casas: 'Bet365' }),
                P('Vizinho', { casas: 'Bet365' })]);
  const idx = G._buildSugIndex();
  const b = { casa: 'Bet365', esporte: 'Futebol', aposta: 'Múltipla', stake: '77,00', descricao: 'A' };
  ok(G._sugParaBilhete(b, idx) === 'Grande', 'sem passar folga, vale 7');
  ok(G._sugRanqueia(b, idx, null) === 'Grande', 'idem no ranqueador');
}

console.log('4) DONO ÚNICO DO ESPORTE dispensa a folga — e é ele que salva o Bad Milton / MMA');
{
  // Comportamento anterior à s310, preservado de propósito: se o filtro duro de esporte deixa
  // UM sobrevivente e o esporte é dele, não há concorrente contra quem ter folga. É o que faz
  // o único tipster de Badminton (ou de MMA) da carteira ser sugerido mesmo sem assinatura.
  const G = mk([P('BadMilton', { esportes: 'Badminton' }), P('Outro', { esportes: 'Tênis' })]);
  const idx = G._buildSugIndex();
  const b = { casa: 'Betboom', esporte: 'Badminton', aposta: 'ML', stake: '77,00', descricao: 'A' };
  ok(G._sugParaBilhete(b, idx, 999) === 'BadMilton', 'único do esporte passa com qualquer folga');
}

console.log('5) casa dedicada a 1 dono segue cravando, folga nenhuma a impede');
{
  const G = mk([P('Fusion', { dica_stake: 'Stake Final 3' }), P('Outro', { esportes: 'Tênis' })],
               { bet365: ['Fusion'] });
  const idx = G._buildSugIndex();
  const b = { casa: 'Bet365', esporte: 'Futebol', aposta: 'Múltipla', stake: '77,00', descricao: 'A' };
  ok(G._sugParaBilhete(b, idx, 999) === 'Fusion', 'curadoria humana explícita está acima da folga');
}

console.log(falhas ? (LF + falhas + ' FALHA(S)') : (LF + 'TUDO VERDE'));
process.exit(falhas ? 1 : 0);
