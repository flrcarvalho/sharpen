// A linha de casa NÃO CURADA não pode se parecer com uma curada (s288).
//
// Bug reportado pelo Feca: "Casas dedicadas a 1 Tipster também não está funcionando." A tela
// mostrava Stake → Dedicada → Arrudex e VaideBet → Dedicada → Peixe; medido no Postgres,
// `casa_config` do dono tinha ZERO linhas. `_casaState` semeava o estado de trabalho com a
// SUGESTÃO do backend quando não havia config salva, então o toggle "Dedicada" acendia e o
// multi-select já vinha preenchido — idêntico a uma casa curada. O matcher lê
// `modo === 'dedicada'` do banco, não achava nada, e a casa-feudo nunca valeu.
//
// Aqui se prova que a linha renderizada distingue os três estados. O código sob teste é
// RECORTADO do `gestao.js` — nunca reescrito aqui: teste que reimplementa o código não detecta
// a mutação que o quebra (a regra "teste verde não é teste que detecta" do CLAUDE.md).
//
// O que este teste NÃO cobre: o POST em `/casas/config` (rede), a leitura pelo matcher (outro
// arquivo) e o layout real no navegador. Cobre a decisão de renderização, que é onde o bug vivia.
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const CR = String.fromCharCode(13), LF = String.fromCharCode(10);
const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const ALVO = process.env.ALVO_GESTAO || path.join(RAIZ, 'app', 'static', 'dash', 'assets', 'js', 'charts', 'gestao.js');
const js = fs.readFileSync(ALVO, 'utf8').split(CR + LF).join(LF);

const corte = (ini, fim) => {
  const a = js.indexOf(ini); if (a < 0) throw new Error('não achei: ' + ini);
  const b = js.indexOf(fim, a); if (b < 0) throw new Error('não achei fim de: ' + ini);
  return js.slice(a, b + fim.length);
};

const src = [
  corte('function _casaState(c){', LF + '}'),
  corte('function _casaSug(c){', LF + '}'),
  corte('function _orgTag(c){', LF + '}'),
  corte('function _casaMetaTxt(nDed,nComp,nSem,nVenc){', LF + '}'),
  corte('function _casaRowGrid(c){', LF + '}'),
].join(LF);

// ── Ambiente dublado: só o que o código recortado toca. Nada aqui é o código sob teste. ──
const amb = `
  let _casasEdit = {};
  const _tmSplit = s => (s || '').split(',').map(x => x.trim()).filter(Boolean);
  const _tmJs = s => (s || '').replace(/'/g, "\\\\'");
  const esc = s => String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;');
  const fmt = (n) => String(n);
  const fmtPct = (n) => n + '%';
  const favicon = d => 'ico/' + d;
  const _houseDomain = () => '';
  const _mselLbl = t => (t && t.length) ? '<span>' + esc(t[0]) + '</span>' : '<span class="ph">— selecionar tipster —</span>';
  const _CHV = '<svg class="chv"></svg>';
  const _PEN = '<svg class="pen"></svg>';
  const _SPARK = '<svg class="spark"></svg>';
`;

const mk = () => {
  const f = new Function(amb + LF + src + LF +
    'return {_casaState,_casaSug,_orgTag,_casaMetaTxt,_casaRowGrid,reset:()=>{_casasEdit={};}};');
  return f();
};

let falhas = 0;
const ok = (cond, msg) => { if (!cond) { falhas++; console.log('  FALHOU: ' + msg); } else console.log('  ok: ' + msg); };

// A casa que abriu o caso: 81 apostas, 100% Arrudex, o backend SUGERE dedicada — e nada foi curado.
const stakeNaoCurada = {
  casa: 'Stake', total: 81, n_tipsters: 1, top: 'Arrudex', top_share: 100,
  sugestao_modo: 'dedicada', sugestao_tipsters: ['Arrudex'],
  modo: null, tipsters: '', origem: null,
};
const stakeCurada = { ...stakeNaoCurada, modo: 'dedicada', tipsters: 'Arrudex', origem: 'custom' };
const bet365Multi = {
  casa: 'Bet365', total: 2059, n_tipsters: 9, top: 'SóChutes', top_share: 42,
  sugestao_modo: 'multi', sugestao_tipsters: [], modo: 'multi', tipsters: '', origem: 'sharpen',
};

console.log('1) casa NÃO curada não pode aparecer como curada');
{
  const G = mk();
  const st = G._casaState(stakeNaoCurada);
  ok(st.modo === null, 'estado de trabalho nasce sem modo (não semeia da sugestão)');
  ok(st.tipsters.length === 0, 'estado de trabalho nasce sem tipster');
  G.reset();
  const html = G._casaRowGrid(stakeNaoCurada);
  ok(!/data-attr="dedicated" class="on"/.test(html), 'toggle "Dedicada" NÃO acende');
  ok(!/data-attr="shared" class="on"/.test(html), 'toggle "Compartilhada" NÃO acende');
  ok(!/class="msel"/.test(html), 'multi-select de dono não aparece');
  ok(/A definir/.test(html), 'tag de origem diz "A definir"');
  ok(!/org--sharpen/.test(html), 'não se disfarça de sugestão já aplicada');
  ok(/dedsug/.test(html) && /Arrudex/.test(html), 'a sugestão aparece — como sugestão');
  ok(!/class="crow dedic"/.test(html), 'a linha não ganha o realce de feudo curado');
}

console.log('2) casa CURADA como dedicada aparece curada');
{
  const G = mk();
  const st = G._casaState(stakeCurada);
  ok(st.modo === 'dedicada' && st.tipsters[0] === 'Arrudex', 'estado vem do que está salvo');
  G.reset();
  const html = G._casaRowGrid(stakeCurada);
  ok(/data-attr="dedicated" class="on"/.test(html), 'toggle "Dedicada" acende');
  ok(/class="msel"/.test(html), 'multi-select de dono aparece');
  ok(/org--custom/.test(html), 'tag de origem diz Personalizado');
  ok(!/A definir/.test(html), 'não diz "A definir"');
  ok(/class="crow dedic"/.test(html), 'a linha ganha o realce de feudo');
}

console.log('3) casa curada como compartilhada');
{
  const G = mk();
  const html = G._casaRowGrid(bet365Multi);
  ok(/data-attr="shared" class="on"/.test(html), 'toggle "Compartilhada" acende');
  ok(!/data-attr="dedicated" class="on"/.test(html), 'toggle "Dedicada" não acende');
  ok(/não aplicável/.test(html), 'coluna de dono diz "não aplicável"');
  ok(/org--sharpen/.test(html), 'origem Sharpen (curada aplicando a sugestão)');
}

console.log('4) o contador do cabeçalho conta o que está CURADO');
{
  const G = mk();
  ok(/2<\/b> a definir/.test(G._casaMetaTxt(1, 3, 2, 0)), 'pendência aparece quando existe');
  ok(!/a definir/.test(G._casaMetaTxt(1, 3, 0, 0)), 'some quando tudo está curado');
}

// ── s310 ────────────────────────────────────────────────────────────────────────────────────
// CURADORIA VENCIDA: a linha salva não passa mais na regra que a sugeriu. O backend decide
// (`repository.casas_visao`) e manda `curadoria_vencida`; aqui se prova que a TELA a mostra.
//
// Por que importa: casa dedicada é resolvida ANTES do matcher e, com 2 nomes, restringe o pool
// a eles — o resto da carteira sai da cédula sem o modelo ser ouvido. Medido na s310, a
// `Betnacional` do Feca (curada em 25/08, caída para 82%) fazia 24 erros em 143 bilhetes contra
// 2 do modelo livre, e NADA na tela dizia isso. O aviso é o que torna o silêncio audível.
console.log('5) curadoria VENCIDA aparece na linha e no cabeçalho');
{
  const G = mk();
  const vencida = {
    casa: 'Betnacional', total: 223, n_tipsters: 10, top: 'Peixe', top_share: 60,
    sugestao_modo: 'multi', sugestao_tipsters: [],
    modo: 'dedicada', tipsters: 'Peixe,Arrudex', origem: 'sharpen',
    curadoria_vencida: true, fora_do_pool: 40,
  };
  const html = G._casaRowGrid(vencida);
  ok(/class="cwarn"/.test(html), 'o aviso é renderizado');
  ok(/40<\/b> de <b>223<\/b>/.test(html), 'nomeia o CUSTO em apostas (40 de 223), não só "vencida"');
  ok(/crow dedic vencida/.test(html), 'a linha ganha a marca de vencida sem perder a de feudo');
  ok(/data-attr="dedicated" class="on"/.test(html), 'o toggle segue mostrando o que está SALVO');
  ok(/org--sharpen/.test(html), 'a origem da curadoria continua visível');

  G.reset();
  const sadia = { ...vencida, sugestao_modo: 'dedicada', sugestao_tipsters: ['Peixe'],
                  curadoria_vencida: false, fora_do_pool: 0 };
  const htmlOk = G._casaRowGrid(sadia);
  ok(!/class="cwarn"/.test(htmlOk), 'casa que ainda se sustenta NÃO acende o aviso');
  ok(!/vencida/.test(htmlOk), 'e não ganha a marca na linha');

  ok(/1 a revisar/.test(G._casaMetaTxt(1, 3, 0, 1)), 'o cabeçalho conta as vencidas');
  ok(!/a revisar/.test(G._casaMetaTxt(1, 3, 0, 0)), 'e some quando não há nenhuma');
  ok(/class="w"/.test(G._casaMetaTxt(1, 3, 0, 1)), 'usa a classe `.w` de warn que já existia');
}

console.log(falhas ? `\n${falhas} FALHA(S)` : '\nTUDO VERDE');
process.exit(falhas ? 1 : 0);
