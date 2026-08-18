// Bet365 — captura passiva por `/sportshistoryapi` (summary + confirmation), formato `F|…`.
//
// POR QUE ESTE CASO EXISTE (s244): a bet365 era a ÚNICA casa de robô sem regressão travada, e o
// parser dela já tinha quebrado 3 vezes. O que finalmente cobrou o preço foi outra coisa: numa
// captura de 206 bilhetes da conta `marloncezar01`, **139 subiram sem o `confirmation`** — sem
// código BR, sem data e com a seleção pelada. Todos os 139 entraram datados de HOJE (o backend
// cai na data de referência quando o bloco não traz linha de data) e 84 tinham par exato num
// bilhete que já existia com código: duplicata com data errada, direto no P/L.
//
// O que este caso trava:
//   1. o `summary` sozinho NÃO produz bilhete emissível (a guarda `b3Emissivel`);
//   2. o merge summary+confirmation entrega código BR, liga e as pernas de bet builder;
//   3. o `confirmation` NÃO vaza o bloco KYC (`01;TY=DI` em diante: nome, endereço, CPF);
//   4. a odd fracionária vira decimal com precisão completa;
//   5. o buraco CONHECIDO da data em bet builder de mesmo jogo (ver `SEM_DATA`, abaixo);
//   6. SISTEMA (`N x Duplas`): a odd é a MÉDIA das linhas, nunca o produto das odds (s265).
import fs from "node:fs";
import path from "node:path";
import { rodarInject, carregarContent, fixture, linha, EXT } from "../sandbox.mjs";

export const casa = "Bet365";

// Único bilhete da fixture que tem `confirmation` salvo — é o bet builder de mesmo jogo.
const COMPLETO = "49637455311";
// Os outros dois só têm `summary`: é exatamente a forma dos 139 bilhetes defeituosos da s244.
const SO_SUMMARY = ["49635244290", "49633134678"];

export async function rodar() {
  const falhas = [];
  const { ultima, urls } = await rodarInject({
    inject: "b3_inject.js",
    href: "https://members.bet365.bet.br/members/",
    urlInicial: "https://members.bet365.bet.br/sportshistoryapi/summary?settled=1",
    // A página é quem busca o detalhe (o inject só navega por `location.hash`, que não existe
    // fora do navegador) → o harness entrega a resposta do confirmation na mão.
    urlsExtra: [`https://members.bet365.bet.br/sportshistoryapi/confirmation?bsid=${COMPLETO}`],
    responder: (url) => {
      if (/\/sportshistoryapi\/summary/.test(url)) return fixture("bet365.summary.txt");
      if (/\/sportshistoryapi\/confirmation/.test(url)) return fixture("bet365.confirmation.txt");
      return null;
    },
    ms: 200,
  });

  if (!ultima) return { falhas: ["o inject não emitiu nenhuma mensagem"], testes: 0 };
  if (urls.length !== 2) falhas.push(`esperava 2 requisições (summary + confirmation), vieram ${urls.length}`);

  const bets = ultima.bets || [];
  if (bets.length !== 3) falhas.push(`esperava 3 bilhetes no summary, vieram ${bets.length}`);
  const por = new Map(bets.map((b) => [String(b.bsid), b]));

  const { pegar } = carregarContent();
  const emissivel = pegar("b3Emissivel");
  const fmt = pegar("formatTicketB3");

  // ── 1. A GUARDA: só sobe quem tem o confirmation ────────────────────────────
  // Esta é a regressão da s244. Se alguém remover a guarda, os dois bilhetes só-summary
  // voltam a subir sem código e sem data — e o defeito das 139 linhas volta inteiro.
  for (const bsid of SO_SUMMARY) {
    const b = por.get(bsid);
    if (!b) { falhas.push(`bilhete ${bsid} não foi parseado do summary`); continue; }
    if (b.code) falhas.push(`${bsid}: não devia ter código (não tem confirmation), veio "${b.code}"`);
    if ((b.legs || []).length) falhas.push(`${bsid}: não devia ter pernas (não tem confirmation)`);
    if (emissivel(b)) falhas.push(`${bsid}: b3Emissivel devolveu TRUE para bilhete sem confirmation ` +
                                  `— é exatamente o defeito da s244 (sobe sem código, datado de hoje)`);
    // O summary sozinho SÓ tem a seleção crua: é a "descrição decapitada" que o Feca viu na grade.
    if (!(b.sels || []).length) falhas.push(`${bsid}: o summary devia trazer ao menos 1 seleção`);
  }

  const c = por.get(COMPLETO);
  if (!c) return { falhas: [...falhas, `bilhete ${COMPLETO} não foi parseado`], testes: 0 };
  if (!emissivel(c)) falhas.push(`${COMPLETO}: b3Emissivel devolveu FALSE mesmo com confirmation ` +
                                 `(code="${c.code}", legs=${(c.legs || []).length}) — travaria captura boa`);

  // ── 2. O merge summary + confirmation ───────────────────────────────────────
  if (c.code !== "JR8714690761I") falhas.push(`${COMPLETO}: código BR esperado JR8714690761I, veio "${c.code}"`);
  if ((c.legs || []).length !== 1) falhas.push(`${COMPLETO}: esperava 1 perna (bet builder de mesmo jogo), veio ${(c.legs || []).length}`);
  const perna = (c.legs || [])[0] || {};
  if ((perna.subs || []).length !== 3) falhas.push(`${COMPLETO}: esperava 3 sub-seleções de bet builder, vieram ${(perna.subs || []).length}`);
  if (perna.liga !== "Campeonato Bras") falhas.push(`${COMPLETO}: liga esperada "Campeonato Bras", veio "${perna.liga}"`);

  // ── 3. KYC não vaza ─────────────────────────────────────────────────────────
  // Depois de `01;TY=DI` o payload traz nome, endereço e CPF. O parser corta ali; sem esse corte
  // os dados pessoais viravam "perna" do bilhete e subiriam para o servidor junto com a aposta.
  const txt = fmt(c);
  if (/REDIGIDO/i.test(txt)) falhas.push(`${COMPLETO}: bloco KYC (01;TY=DI) vazou para o texto do bilhete`);

  // ── 4. O bloco que a IA lê ──────────────────────────────────────────────────
  if (!txt.startsWith(`[Código: ${c.code}]`)) falhas.push(`${COMPLETO}: marcador [Código:] ausente/errado`);
  const odd = linha(txt, "Odd:");
  if (odd !== "4") falhas.push(`${COMPLETO}: odd fracionária 3/1 devia virar 4, veio "${odd}"`);
  const status = linha(txt, "Status:");
  if (!/^Perdeu → L$/.test(status)) falhas.push(`${COMPLETO}: status "${status}" (RT=0 → L)`);
  if (linha(txt, "Stake:") !== "96,00") falhas.push(`${COMPLETO}: stake "${linha(txt, "Stake:")}"`);
  if (!/CL=1 \(Futebol\)/.test(linha(txt, "Esporte (casa):"))) falhas.push(`${COMPLETO}: esporte "${linha(txt, "Esporte (casa):")}"`);
  // As 3 pernas do bet builder precisam sair como `mercado · seleção` (bug da s178: saía 1 linha só).
  for (const [mercado, sel] of [["Escanteios", "Mais de 12 Escanteios"],
                                ["Para Marcar a Qualquer Momento", "Igor Felisberto - Para Marcar"],
                                ["Jogador a Dar Assistência", "Igor Felisberto - Para Dar Assistência"]]) {
    if (!txt.includes(`– ${mercado} · ${sel}`)) falhas.push(`${COMPLETO}: perna de bet builder ausente: ${mercado} · ${sel}`);
  }

  // ── 5. BURACO CONHECIDO, travado de propósito ───────────────────────────────
  // Bet builder de MESMO JOGO vem com `TP=00010101000000` no confirmation (sem kickoff), então
  // `_dataFimB3` devolve "" e o bloco sai SEM linha de data — e o backend cai na data de
  // referência (= hoje). O bilhete tem `da=20260722233620` (confirmation) e `tp=20260722233620000`
  // (summary), ambos data de COLOCAÇÃO e ambos sem uso hoje. Usá-los seria contrariar a
  // `CASA_BET365.md §4` ("colocação nunca", decisão registrada) → mudança de REGRA, precisa de
  // aprovação humana. Este teste trava o estado atual: se alguém mexer, ele falha e obriga a
  // decisão consciente (e a atualizar o §4 junto).
  const SEM_DATA = !linha(txt, "Data (");
  if (!SEM_DATA) falhas.push(`${COMPLETO}: passou a emitir linha de data ("${linha(txt, "Data (")}") — ` +
                             `se foi de propósito, atualize CASA_BET365 §4 e este caso; a regra vigente ` +
                             `é "evento → informada → Brasília-hoje", colocação nunca`);
  if (!c.da || !c.tp) falhas.push(`${COMPLETO}: da/tp sumiram do merge — são a única data disponível ` +
                                  `neste bilhete se algum dia o §4 mudar`);

  // ── 6. SISTEMA: odd = MÉDIA das linhas, nunca o produto (s265) ──────────────
  // O bilhete 49633134678 da fixture é um `3 x Duplas` REAL: `BT=2 · BC=3 · ST=175 · TS=525`,
  // odds 15/8 · 5/4 · 7/4 (= 2,875 · 2,25 · 2,75).
  //   correto : (2,875×2,25 + 2,875×2,75 + 2,25×2,75) ÷ 3 = 6,854166666666667
  //   o bug   : 2,875 × 2,25 × 2,75                        = 17,7890625  ← a odd da TRIPLA
  // Era isso que subia: `3 x Duplas` e a tripla das MESMAS seleções produziam blocos idênticos
  // e a IA multiplicava nos dois. Em W o `Retorno ÷ Aposta` mascarava; em ABERTA e em L (RT=0,
  // que é o caso deste bilhete) não havia nada para mascarar.
  // Chamamos `fmt()` num bilhete só-summary de propósito: a fixture não tem o confirmation deste
  // bsid, e a aritmética do sistema não depende dele (as odds por linha vêm do `03` do summary —
  // que é a fonte certa mesmo quando HÁ confirmation, porque em bet builder a perna vem OD=0/1).
  const dup = por.get("49633134678");
  if (!dup) {
    falhas.push("49633134678 (3 x Duplas) não foi parseado do summary");
  } else {
    if (String(dup.bc) !== "3") falhas.push(`49633134678: BC esperado "3" (nº de apostas), veio "${dup.bc}" ` +
                                            `— sem BC o sistema é indistinguível de uma múltipla comum`);
    if (String(dup.bt) !== "2") falhas.push(`49633134678: BT esperado "2" (seleções por aposta), veio "${dup.bt}"`);
    if (dup.tipo !== "Duplas") falhas.push(`49633134678: tipo esperado "Duplas", veio "${dup.tipo}"`);
    const td = fmt(dup);
    const tipo = linha(td, "Tipo:");
    if (!/^SISTEMA Duplas — 3 apostas de 2 seleção\(ões\), sobre 3 seleções/.test(tipo)) {
      falhas.push(`49633134678: linha de estrutura errada: "${tipo}"`);
    }
    if (!/aposta unitária R\$ 175,00 · total R\$ 525,00/.test(tipo)) {
      falhas.push(`49633134678: unitária/total errados na linha de estrutura: "${tipo}"`);
    }
    const oddSis = linha(td, "Odd (estrutural do sistema):");
    if (!oddSis.startsWith("6,854166666666667")) {
      falhas.push(`49633134678: odd do sistema esperada 6,854166666666667 (média das 3 duplas), ` +
                  `veio "${oddSis}"`);
    }
    if (/17,789/.test(td)) {
      falhas.push("49633134678: o bloco traz 17,7890625 — o PRODUTO das 3 odds. Esse é o bug da " +
                  "s265: é a odd da tripla, não a do sistema de duplas");
    }
    // Num sistema a linha `Odd:` (odd do bilhete) seria a odd de UMA seleção → mandaria a IA
    // para o número errado. Tem de estar ausente.
    if (linha(td, "Odd:")) falhas.push(`49633134678: linha "Odd:" não devia existir em sistema (veio "${linha(td, "Odd:")}")`);
    if (linha(td, "Stake:") !== "525,00") falhas.push(`49633134678: Stake devia ser o TOTAL 525,00, veio "${linha(td, "Stake:")}"`);
  }

  // ── 6b. O INVERSO: bilhete de 1 linha NÃO pode virar sistema ────────────────
  // `BC=1` é múltipla comum (ou simples) e ali o produto das odds está CERTO. Se a linha de
  // sistema aparecer aqui, o conserto da s265 virou o defeito oposto.
  for (const bsid of ["49635244290", COMPLETO]) {
    const b = por.get(bsid);
    if (!b) continue;
    const bl = fmt(b);
    if (linha(bl, "Tipo:").startsWith("SISTEMA")) {
      falhas.push(`${bsid}: BC=${b.bc} (1 aposta) não é sistema, mas o bloco saiu como SISTEMA`);
    }
    if (linha(bl, "Odd (estrutural do sistema):")) {
      falhas.push(`${bsid}: bilhete de 1 linha ganhou odd de sistema`);
    }
  }

  falhas.push(...duplaEEsportes(fmt));
  falhas.push(...await expansao());
  return { falhas, testes: bets.length };
}

// ── 7. EXPANSÃO DA LISTA — o "Mostrar Mais" automático (s279) ─────────────────
// Quem clica é o `b3_expand.js`, no mundo ISOLATED (o porquê está no cabeçalho dele). O que se
// prova aqui é o LOOP, não o parser: que ele clica e — o que realmente importa — que ele
// TERMINA pelas duas saídas.
//
// Por que isto merece regressão própria: até a v0.6.47 o operador clicava "Mostrar Mais" à mão
// e, se parasse antes do fim, o robô capturava só o 1º lote **sem erro nenhum**, como se aquilo
// fosse a lista inteira. Trocar um gesto humano por um laço automático move a falha silenciosa
// de lugar: laço que não termina trava a captura, e laço que termina cedo demais reproduz
// exatamente o defeito antigo.
//
// O QUE ISTO **NÃO** COBRE (medido por mutação, s279): o clique de verdade. `btn.click()` num
// objeto dublado sempre "funciona" — foi por isso que a 1ª versão passou verde no harness e
// deu 8 cliques com ZERO requisição na casa. Este caso trava o laço; quem prova o clique é a
// aba real, e o tell lá é o log `[SharpenUp b3_expand] #N · altura … · cards …`: altura parada
// com cliques subindo = o clique não está acionando a casa.
// DOM dublado: botão que aceita `limite` cliques e depois some, e uma altura que só cresce
// quando `crescer` é verdadeiro. É o mínimo que o laço lê.
function domFalso({ limite, crescer }) {
  const est = { cliques: 0, altura: 1000 };
  const botao = {
    scrollIntoView() {},
    click() { est.cliques++; if (crescer) est.altura += 800; },
  };
  est.doc = () => ({
    body: { get scrollHeight() { return est.altura; } },
    querySelector: (sel) => (sel === '.hl-SummaryRenderer_ShowMore'
      ? (est.cliques >= limite ? null : botao) : null),
    querySelectorAll: () => [],
  });
  return est;
}

async function rodarExpand(est) {
  return rodarInject({
    inject: 'b3_expand.js',
    href: 'https://members.bet365.bet.br/members/',
    urlInicial: 'https://members.bet365.bet.br/x',
    relogio: 'turbo',
    dom: () => est.doc(),
    pedidoMsg: { __sharpenupB3Expandir: true },
    responder: () => null,
    ms: 500,
  });
}

async function expansao() {
  const falhas = [];

  // ── 7a. Botão some depois de 2 cliques → para em 2 ──────────────────────────
  {
    const est = domFalso({ limite: 2, crescer: true });
    await rodarExpand(est);
    if (est.cliques !== 2) {
      falhas.push(`expansão: esperava 2 cliques (o botão some no 3º), foram ${est.cliques} — ` +
                  `mais que isso é laço que não vê o fim da lista; menos, é a captura parando ` +
                  `no 1º lote (o defeito que a s279 resolveu)`);
    }
  }

  // ── 7b. Botão eterno e altura parada → para por estagnação ──────────────────
  // Sem esta saída o laço giraria enquanto a aba estivesse aberta. `SEM_MUDANCA_MAX` é 8 no
  // `b3_expand`; o teto duro (`MAX_CLIQUES`, 400) não pode ser o que segura este caso.
  {
    const est = domFalso({ limite: Infinity, crescer: false });
    await rodarExpand(est);
    if (est.cliques !== 8) {
      falhas.push(`expansão: com o botão eterno e a altura da página parada (o critério de fim, ` +
                  `igual ao da extensão que funciona), esperava parar em 8 cliques, parou em ` +
                  `${est.cliques}. ${est.cliques > 8
                    ? 'Laço sem freio: numa aba real ele clicaria até o teto de 400.'
                    : 'Freio curto demais: a casa às vezes demora a entregar o lote e a lista ' +
                      'ficaria pela metade, em silêncio.'}`);
    }
  }

  // ── 7c. A PONTE não trava quando o `b3_expand` não responde ─────────────────
  // O `b3_inject` pede a expansão e espera. Se o `b3_expand` não estiver lá (extensão
  // desatualizada, frame sem lista), ele tem de seguir para o detalhamento em vez de esperar o
  // teto de 7 minutos — senão uma versão velha do content script trava a captura inteira.
  {
    const { ultima } = await rodarInject({
      inject: 'b3_inject.js',
      href: 'https://members.bet365.bet.br/members/',
      urlInicial: 'https://members.bet365.bet.br/sportshistoryapi/summary?settled=1',
      relogio: 'turbo',
      // Ninguém responde ao `__sharpenupB3Expandir`: é exatamente o cenário do b3_expand ausente.
      pedidoMsg: { __sharpenupB3Req: true, acao: 'detalhar',
                   jaTem: ['49637455311', '49635244290', '49633134678'] },
      responder: (url) => (/\/sportshistoryapi\/summary/.test(url) ? fixture('bet365.summary.txt') : null),
      // 2,5 s de forno: a espera pelo ACK é de 1,5 s em tempo REAL (o relógio turbo do sandbox
      // acelera `setTimeout`, não `Date.now()`). Colher antes disso mediria o teste, não o código.
      ms: 2500,
    });
    if (!ultima || !ultima.fim) {
      falhas.push('ponte: sem o `b3_expand` respondendo, o inject não chegou a anunciar `fim` — ' +
                  'a espera pelo ACK não está soltando e a captura travaria na expansão');
    }
  }

  // ── 7d. O robô não pode encerrar ANTES de a expansão acabar ─────────────────
  // Teste ESTRUTURAL (lê o texto do `content.js`), e é de propósito: exercitar
  // `roboBet365Passive` de verdade exigiria dublar painel, ctx e o relógio da captura inteira,
  // e o que se quer travar são duas linhas específicas.
  //
  // O bug que ele guarda (s279, visto ao vivo): `b3FimReal` é variável de MÓDULO e ficava
  // `true` desde a captura anterior — a página não recarrega entre rodadas. Com a memória
  // cheia (`resta === 0`), o laço encerrava na 1ª volta, 500ms depois de começar, **enquanto o
  // `b3_expand` ainda clicava**. O console mostrava o `Bet365 API: N bilhete(s)` sair ANTES das
  // linhas `[b3_expand] #N`, e a captura ficava com o que a lista tinha no começo.
  {
    const src = fs.readFileSync(path.join(EXT, "content.js"), "utf8");
    const corpo = src.slice(src.indexOf("async function roboBet365Passive"));
    if (!/^\s*b3FimReal = false;/m.test(corpo.slice(0, 2000))) {
      falhas.push("content.js: `roboBet365Passive` não reseta `b3FimReal` no início — estado da " +
                  "rodada anterior vaza e o robô encerra na 1ª volta quando a memória está cheia");
    }
    if (!/^\s*b3Expandindo = false;/m.test(corpo.slice(0, 2000))) {
      falhas.push("content.js: `roboBet365Passive` não reseta `b3Expandindo` no início");
    }
    if (!/if \(b3FimReal && resta === 0 && !b3Expandindo\) break;/.test(corpo)) {
      falhas.push("content.js: a condição de fim do robô não exige `!b3Expandindo` — o robô pode " +
                  "encerrar no meio do 'Mostrar Mais' e perder tudo o que a lista carregar depois");
    }
    const inj = fs.readFileSync(path.join(EXT, "b3_inject.js"), "utf8");
    if (!/enviar\(false, \{ expandindo: false \}\)/.test(inj)) {
      falhas.push("b3_inject.js: a expansão não sinaliza `expandindo:false` ao terminar — a flag " +
                  "ficaria presa em true e o robô só sairia pelo timeout de 45s");
    }
  }

  return falhas;
}

// ── 8. DUPLA do mesmo esporte: a odd é o PRODUTO, não a da 1ª seleção ────────
// Bug medido na captura de 129 bilhetes da s279 (o "Mostrar Mais" automático não o criou —
// ampliou a amostra até ele aparecer). O gatilho é escapar de `multiplo`, que exige 3+ jogos
// OU 2 esportes: uma DUPLA do mesmo esporte não é nenhum dos dois, e o bloco imprimia `Odd:`
// com `t.oddFrac` = a odd da PRIMEIRA seleção.
//
// Quatro casos reais na exportação; os números abaixo são do `QA8502058091I`:
//   stake 46 · retorno 1173 → 25,5 · odds 4,25 e 6 → produto 25,5 · o bloco dizia 4,25.
// Em `W` a IA se salva pelo `Retorno ÷ Aposta`; em `L` (`PA9555804861I`: 3,25 onde o certo era
// 11,7) não há retorno para mascarar — é a mesma família do bug de sistema da s265.
//
// Bilhete SINTÉTICO de propósito: a fixture salva não tem dupla do mesmo esporte (foi por isso
// que o caso passou verde por 35 sessões). Os valores são do bilhete real, não inventados.
function duplaEEsportes(fmt) {
  const falhas = [];
  const perna = (jogo, sel, odd, cl, liga) => ({ sel, jogo, mercado: "Resultado Final",
    oddFrac: odd, cl, liga, kickoff: "20260812180000", subs: [] });
  const dupla = {
    bsid: "1", code: "QA8502058091I", bc: "1", bt: "2", aberta: false,
    stake: "46.00", ts: "46.00", rt: "1173.00", tipo: "Dupla", oddFrac: "13/4",   // 4,25
    sels: [{ na: "Bragantino x Atletico Mineiro", od: "13/4", cl: "1" },
           { na: "Tigre x Montevideo City Torque", od: "5/1", cl: "1" }],
    legs: [perna("Bragantino x Atletico Mineiro", "Atletico-MG", "13/4", "1", "SOC-COPA-SUDA"),
           perna("Tigre x Montevideo City Torque", "Montevideo City Torque", "5/1", "1", "SOC-COPA-SUDA")],
  };
  const txt = fmt(dupla);
  if (linha(txt, "Odd:")) {
    falhas.push(`dupla: o bloco emitiu "Odd: ${linha(txt, "Odd:")}" num bilhete de 2 seleções — ` +
                `essa é a odd da PRIMEIRA seleção (4,25), não a do bilhete (25,5 = 1173/46). ` +
                `Em L não há Retorno÷Aposta para mascarar e o número errado vai para o banco`);
  }
  if (!/^Tipo: 2 seleções/m.test(txt)) {
    falhas.push("dupla: falta a linha de estrutura dizendo que a odd é o PRODUTO das seleções — " +
                "sem `Odd:` e sem ela, a IA fica sem saber de onde tirar a odd do bilhete");
  }

  // O INVERSO: bilhete de 1 seleção (e bet builder de mesmo jogo, que também é 1 perna) TEM de
  // continuar imprimindo `Odd:`. Se o conserto matar isso, todo bilhete simples perde a odd.
  const simples = { bsid: "2", code: "X", bc: "1", bt: "1", aberta: false, stake: "100.00",
    ts: "100.00", rt: "0", oddFrac: "4/5",   // 1,8
    sels: [{ na: "A x B", od: "4/5", cl: "1" }],
    legs: [perna("A x B", "Mais de 2.5", "4/5", "1", "LIGA")] };
  if (linha(fmt(simples), "Odd:") !== "1,8") {
    falhas.push(`simples: perdeu a linha "Odd:" (veio "${linha(fmt(simples), "Odd:")}") — o ` +
                `conserto da dupla não pode atingir bilhete de 1 seleção`);
  }

  // ── Esportes mapeados na s279 (nomes já canônicos no MASTER_ESPORTES §4) ────
  for (const [cl, nome] of [["151", "E-Sports"], ["162", "MMA"], ["8", "Rugby"]]) {
    const b = { bsid: "3", code: "Y", bc: "1", bt: "1", aberta: false, stake: "10", ts: "10",
      rt: "0", oddFrac: "1/1", sels: [{ na: "A x B", od: "1/1", cl }],
      legs: [perna("A x B", "S", "1/1", cl, "L")] };
    const esp = linha(fmt(b), "Esporte (casa):");
    if (!esp.includes(`(${nome})`)) {
      falhas.push(`CL=${cl} devia sair como "${nome}", veio "${esp}" — sem o nome a IA ` +
                  `classifica pela liga e o esporte vira chute`);
    }
  }
  // E os NÃO mapeados continuam crus, de propósito (ver o comentário do `_CL_B3`).
  for (const cl of ["107", "16"]) {
    const b = { bsid: "4", code: "Z", bc: "1", bt: "1", aberta: false, stake: "10", ts: "10",
      rt: "0", oddFrac: "1/1", sels: [{ na: "A x B", od: "1/1", cl }],
      legs: [perna("A x B", "S", "1/1", cl, "L")] };
    if (/\(/.test(linha(fmt(b), "Esporte (casa):"))) {
      falhas.push(`CL=${cl} ganhou nome de esporte. 107 é squash (NÃO existe no MASTER — criar ` +
                  `esporte é decisão humana + propagação) e 16 tem uma amostra só, com o CL=18 ` +
                  `já sendo Basquete. Se foi de propósito, atualize os MASTERs e este teste`);
    }
  }
  return falhas;
}
