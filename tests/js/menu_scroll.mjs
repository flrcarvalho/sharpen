// Rolar o menu não pode FECHAR o menu, e rolar a tabela não pode CONGELAR a tela (s287).
//
// Bug reportado pelo tester Marlon: "o scroll/barra lateral não estão funcionando". Eram
// dois, em cadeia, e nenhum dava erro:
//
//   1. o handler de scroll é registrado em CAPTURA no `window` (scroll não borbulha), então
//      ele recebia também o scroll de DENTRO do `.ac-menu` — rolar a lista para achar um
//      mercado fechava o menu na cara do usuário. Latente desde sempre: o menu de tipster
//      cabia na tela, o de mercado tem 27+ itens e SEMPRE precisa rolar;
//   2. com a edição inline aberta, `renderApostasVirt` volta cedo (`_apInlineEditing`), então
//      rolar a tabela movia a barra e não redesenhava linha nenhuma. A tela parecia travada,
//      e era só o editor seguindo aberto atrás. Encerrar com commit ao rolar devolve o
//      scroll na hora — mesma semântica do blur, que já salva ao clicar fora.
//
// Aqui se prova a LÓGICA de roteamento, recortada do `apostas.js`, sobre um DOM dublado —
// roda em qualquer lugar, sem navegador. O roteamento REAL do evento (captura no window de
// um evento que não borbulha, `e.target` sendo o nó rolado) foi provado à parte, no Chrome
// headless, na sessão em que o bug foi corrigido.
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const CR = String.fromCharCode(13), LF = String.fromCharCode(10);
const RAIZ = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const ALVO = process.env.ALVO_DASH || path.join(RAIZ, 'app', 'static', 'dash', 'assets', 'js', 'charts', 'apostas.js');
const js = fs.readFileSync(ALVO, 'utf8').split(CR + LF).join(LF);

const corte = (ini, fim) => {
  const a = js.indexOf(ini); if (a < 0) throw new Error('não achei: ' + ini);
  const b = js.indexOf(fim, a); if (b < 0) throw new Error('não achei fim de: ' + ini);
  return js.slice(a, b + fim.length);
};
const src = corte('function _acRolagemInterna(e){', LF + '}')
  + LF + corte('function _acScrollFora(){', LF + '}');
// A LIGAÇÃO também é recortada do arquivo, não reescrita aqui: na 1ª versão deste teste o
// harness reimplementava `if (!interna) fora()`, e a mutação que removia o guard do
// listener real passava verde. Teste que reescreve o código sob teste não testa nada.
const srcLigacao = corte("window.addEventListener('scroll',e=>", '},true);');

// ── DOM dublado: só o que as duas funções tocam (nodeType, closest) ──────────
const no = (classes, pai) => {
  const self = {
    nodeType: 1,
    _classes: classes || [],
    _pai: pai || null,
    closest(sel) {
      const alvos = sel.split(',').map(s => s.trim().replace('.', ''));
      let n = self;
      while (n) {
        if (n._classes.some(c => alvos.includes(c))) return n;
        n = n._pai;
      }
      return null;
    },
  };
  return self;
};
const menu = no(['ac-menu']);
const itemDoMenu = no(['ac-item'], menu);
const calendario = no(['shcal']);
const diaDoCal = no(['shcal__dia'], calendario);
const tabela = no(['btbl-wrap']);
const celula = no(['btbl-cell'], tabela);
const documento = { nodeType: 9 };            // scroll do document: sem closest

const mk = () => {
  // `commits` guarda o ARGUMENTO de cada finish: rolar tem de encerrar com commit (true),
  // como o blur faz. Com `false` o que o usuário digitou seria descartado em silêncio —
  // e a 1ª versão deste teste não olhava o argumento, então essa mutação escapava.
  const est = { menuAberto: true, edicaoAberta: true, commits: [] };
  const ctx = new Function('estado', `
    let _apInlineFim = commit => { estado.edicaoAberta = false; estado.commits.push(commit); };
    const _acAberto = () => estado.menuAberto;
    const _acFechar = () => { estado.menuAberto = false; };
    ${src}
    let handler = null;
    const window = { addEventListener: (ev, fn) => { if (ev === 'scroll') handler = fn; } };
    ${srcLigacao}
    return {
      rolar: alvo => handler({ target: alvo }),
      semEdicao: () => { _apInlineFim = null; },
    };
  `)(est);
  return { est, ...ctx };
};

let ok = 0, ko = 0;
const t = (nome, cond) => { if (cond) { ok++; console.log('  ✓', nome); } else { ko++; console.log('  ✗', nome); } };

console.log(LF + '1) rolar DENTRO de um popover ancorado não fecha nada');
let c = mk(); c.rolar(menu);
t('o menu segue aberto', c.est.menuAberto);
t('a edição segue aberta', c.est.edicaoAberta);
c = mk(); c.rolar(itemDoMenu);
t('scroll vindo de um FILHO do menu também é interno', c.est.menuAberto && c.est.edicaoAberta);
c = mk(); c.rolar(calendario);
t('o calendário da marca conta como interno', c.est.menuAberto);
c = mk(); c.rolar(diaDoCal);
t('e o filho dele também', c.est.menuAberto);

console.log(LF + '2) rolar FORA fecha o menu e encerra a edição');
c = mk(); c.rolar(tabela);
t('o menu fecha', !c.est.menuAberto);
t('a edição encerra — é isso que destrava o virtual scroll', !c.est.edicaoAberta);
t('encerra com COMMIT, não descartando o que foi digitado', c.est.commits.length === 1 && c.est.commits[0] === true);
c = mk(); c.rolar(celula);
t('scroll de qualquer nó fora do menu também encerra', !c.est.menuAberto && !c.est.edicaoAberta);

console.log(LF + '3) casos de borda');
c = mk(); c.rolar(documento);
t('scroll do próprio document (sem closest) não quebra', !c.est.menuAberto);
c = mk(); c.rolar(tabela); c.rolar(tabela);
t('o finish não roda duas vezes (a referência é limpa após a 1ª)', c.est.commits.length === 1);
c = mk(); c.semEdicao(); c.rolar(tabela);
t('sem edição aberta, rolar apenas fecha o menu', !c.est.menuAberto && c.est.commits.length === 0);

console.log(LF + ok + ' passaram · ' + ko + ' falharam');
process.exit(ko ? 1 : 0);
