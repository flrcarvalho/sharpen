// Mundo ISOLATED da Bet365 (todos os frames): clica "Mostrar Mais" até a lista acabar.
//
// POR QUE UM ARQUIVO SÓ PARA ISTO, se o `b3_inject` já roda neste mesmo frame: ele roda no
// mundo **MAIN**, e ali o clique não aciona nada. Medido ao vivo na s279, na conta do Feca:
// 8 cliques no `div.hl-SummaryRenderer_ShowMore` → `respostas=1`, nenhuma requisição nova. O
// MESMO `.click()`, no MESMO elemento, disparado do console (que também é MAIN) funcionou três
// vezes seguidas (10→20→30→40) — ou seja, o gesto é válido e a causa continua sem nome.
//
// O que foi DESCARTADO por medição, não por dedução (console do frame `members`, s279):
//   • patch de protótipo — `HTMLElement.prototype.click` é `[native code]`;
//   • barreira `isTrusted` — o clique sintético carregou 10 bilhetes três vezes;
//   • handler num filho — o div não tem filho nenhum, `elementFromPoint` devolve ele mesmo;
//   • viewport — o iframe não rola (cresce com o conteúdo, `innerHeight` 4154), o botão está
//     sempre dentro dela, e clicar sem rolar funcionou igual.
//
// Sobrou o **mundo**. Em vez de continuar caçando a causa, replicamos o ambiente que
// comprovadamente funciona: a extensão de terceiro que o Feca testou ("auto-show-more", do
// arrudex) faz exatamente isto, no ISOLATED, e expande a lista inteira. A lógica abaixo é a
// dela — inclusive o critério de parada por ALTURA DA PÁGINA. Não trocar por contagem de
// bilhetes capturados: foi essa "melhoria" que escondeu o problema na 1ª tentativa (o inject
// media `byBsid`, que depende do hook ver a resposta, e não a tela).
(() => {
  const SEL       = ".hl-SummaryRenderer_ShowMore";   // "Mostrar Mais"
  const SEL_CARD  = ".h-BetSummary_BetDetails";       // 1 por bilhete — só para o log
  const INTERVALO = 900;      // ms entre cliques (a casa não entrega o lote em menos que isso)
  const SEM_MUDANCA_MAX = 8;  // ciclos com a altura parada até declarar fim
  const MAX_CLIQUES = 400;    // trava de tempo; 400 × ~10 bilhetes cobre qualquer histórico

  const LOG = (...a) => { try { console.log("[SharpenUp b3_expand]", ...a); } catch (e) {} };
  const espera = (ms) => new Promise((r) => setTimeout(r, ms));
  const alt   = () => { try { return (document.body && document.body.scrollHeight) || 0; } catch (e) { return 0; } };
  const cards = () => { try { return document.querySelectorAll(SEL_CARD).length; } catch (e) { return 0; } };
  const botao = () => { try { return document.querySelector(SEL); } catch (e) { return null; } };

  let rodando = false;

  const avisar = (msg) => { try { window.postMessage(msg, "*"); } catch (e) {} };

  async function expandir() {
    if (rodando) return;
    rodando = true;
    let cliques = 0, semMudanca = 0, ultima = alt(), motivo = "teto de cliques";
    try {
      LOG("começando · altura " + ultima + " · cards " + cards());
      if (!botao()) {
        motivo = "sem botão (lista já completa ou frame sem lista)";
      } else {
        while (cliques < MAX_CLIQUES) {
          const btn = botao();
          if (!btn) { motivo = "o botão sumiu → fim da lista"; break; }
          try { btn.scrollIntoView({ block: "center", behavior: "instant" }); } catch (e) {}
          btn.click();
          cliques++;
          await espera(INTERVALO);
          const nova = alt();
          if (nova === ultima) semMudanca++; else semMudanca = 0;
          ultima = nova;
          LOG("#" + cliques + " · altura " + nova + " · cards " + cards());
          if (semMudanca >= SEM_MUDANCA_MAX) { motivo = "altura parada por " + SEM_MUDANCA_MAX + " ciclos"; break; }
        }
      }
    } catch (e) {
      motivo = "erro: " + (e && e.message);
    } finally {
      rodando = false;
      LOG("fim · " + cliques + " clique(s) · cards " + cards() + " · " + motivo);
      avisar({ __sharpenupB3Expandido: true, cliques: cliques, cards: cards(), motivo: motivo });
    }
  }

  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (!d || !d.__sharpenupB3Expandir) return;
    // ACK imediato: o inject espera 1,5 s por ele. Sem ACK (extensão velha, frame sem este
    // script) o inject segue direto para o detalhamento em vez de travar esperando o fim.
    avisar({ __sharpenupB3ExpandAck: true });
    expandir();
  });

  LOG("pronto em", location.href.slice(0, 80));
})();
