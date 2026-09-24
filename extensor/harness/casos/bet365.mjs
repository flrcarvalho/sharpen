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

  // ── 5. O BURACO FECHOU na s373: sem kickoff, a data vem da COLOCAÇÃO ────────
  // Este bilhete é um Criar Aposta de mesmo jogo: o confirmation manda a perna com
  // `TP=00010101000000`, sem kickoff. Até a s373 o bloco saía SEM linha de data e o backend
  // datava com a data de referência (= hoje) — 13 de 16 bilhetes de um lote de histórico
  // nasceram errados por isso. O Feca aprovou usar a COLOCAÇÃO (`da`/`tp`), que a casa
  // publica; o §4 mudou junto, e agora é ESTE caso que trava a decisão nova.
  //
  // `da=20260722233620` → 22/07 23:36 UK, BST em julho (BR = UK−4) → **22/07/2026 19:36 BR**.
  // A conversão é a mesma do kickoff de propósito: mesma API, mesmo formato de 14 dígitos.
  const DATA_COL = linha(txt, "Data (colocação):");
  if (DATA_COL !== "22/07/2026") {
    falhas.push(`${COMPLETO}: bet builder sem kickoff devia emitir "Data (colocação): 22/07/2026" ` +
                `(da=${c.da}, 23:36 UK em BST = 19:36 BR), veio "${DATA_COL || "(nada)"}". Sem essa ` +
                `linha o backend usa a data de referência e todo bilhete de histórico nasce datado de hoje`);
  }
  // A procedência tem de aparecer no RÓTULO: quem lê o bloco é a IA, e colocação sob o rótulo
  // de evento é mentira sobre a fonte — mesmo dando a data certa na maioria dos casos.
  if (linha(txt, "Data (evento):")) {
    falhas.push(`${COMPLETO}: a colocação saiu rotulada como "Data (evento):" — este bilhete não ` +
                `tem kickoff nenhum (TP=00010101000000). O rótulo diz de onde o número veio`);
  }
  if (!c.da || !c.tp) falhas.push(`${COMPLETO}: da/tp sumiram do merge — são a ÚNICA data ` +
                                  `disponível neste bilhete desde a s373`);

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

  // ── 6c. O CARIMBO DE COLOCAÇÃO sai VERBATIM, em todo bilhete ────────────────
  // É a única identidade estável que esta casa dá: o `ID` do summary é da VISÃO (24h no
  // namespace `D1`, 48h e Intervalo de Datas no `D0`) e muda outra vez quando a aposta
  // resolve. Sem o carimbo, aposta gravada como aberta não tem como ser reencontrada na
  // lista depois — sabe-se QUEM procurar e não ONDE.
  //
  // O que este teste trava é a parte que o olho não vê: que ele sai CRU. Passar pelo
  // `_dataKickoffB3` daria `22/07/2026`, que parece certo e destrói a chave de duas
  // maneiras — perde a hora (o desempate entre apostas do mesmo dia) e aplica uma
  // conversão UK→Brasília por fuso ASSUMIDO, que o outro lado do casamento teria de
  // repetir igual. Por isso o valor esperado é literal, tirado da fixture.
  {
    const esperado = { "49637455311": "20260722233620",    // tem `DA` (confirmation) e `TP`
                       "49635244290": "20260722150124",    // só `TP` (summary)
                       "49633134678": "20260721223826" };
    for (const [bsid, carimbo] of Object.entries(esperado)) {
      const b = por.get(bsid);
      if (!b) continue;
      const l = linha(fmt(b), "Carimbo");
      if (!l) {
        falhas.push(`${bsid}: o bloco saiu SEM a linha de carimbo. Sem ela o bilhete nasce ` +
                    `sem \`aposta_em\` e fica fora do "Resolver apostas abertas"`);
        continue;
      }
      const num = (l.match(/(\d{14})\s*$/) || [])[1];
      if (num !== carimbo) {
        falhas.push(`${bsid}: carimbo devia ser ${carimbo} (o TP/DA da casa, verbatim), veio ` +
                    `"${l}". Se virou data formatada, a chave perdeu a hora e ganhou uma ` +
                    `conversão de fuso que o outro lado do casamento não faz`);
      }
    }
    // Sem TP legível (o `TP=00010101…` do bet builder de mesmo jogo) NÃO sai linha nenhuma:
    // ausência viaja como ausência. Um carimbo falso aqui casaria a aposta errada.
    const semTP = { bsid: "9", code: "X", bc: "1", bt: "1", aberta: false, stake: "10",
                    ts: "10", rt: "0", oddFrac: "1/1", tp: "00010101000000",
                    sels: [{ na: "A x B", od: "1/1", cl: "1" }],
                    legs: [{ jogo: "A x B", na: "S", od: "1/1", cl: "1", res: "L" }] };
    if (linha(fmt(semTP), "Carimbo")) {
      falhas.push("bilhete com TP=00010101… (bet builder de mesmo jogo, sem carimbo real) " +
                  "ganhou linha de carimbo — data falsa é pior que data ausente, e aqui " +
                  "uma chave falsa casa a aposta errada");
    }
  }

  falhas.push(...duplaEEsportes(fmt));
  falhas.push(...dataDoEvento(fmt));
  falhas.push(...await expansao());
  falhas.push(...await resolverAbertas());
  falhas.push(...chavesDoStorage());
  falhas.push(...respostaSobeParaOTopo());
  falhas.push(...repassePreservaOPedido());
  return { falhas, testes: bets.length };
}

// ── 9. DATA = KICKOFF, sem folga (s339) ──────────────────────────────────────
// O que este bloco trava, e por que ele não existia antes: até a s339 a data era o kickoff MAIS
// uma "folga de encerramento" por esporte (2,5 h em basquete, 3 h em tênis…), para estimar o
// instante da liquidação. O harness ficava verde porque nenhum caso conferia a data — o único
// que a mencionava (`SEM_DATA`, acima) prova a AUSÊNCIA dela em bet builder de mesmo jogo.
//
// O preço: todo dia, entre ~21h e a meia-noite, o bilhete nascia datado de AMANHÃ. No dia
// 09/09/2026 às 22:50 o tipster Ctrl Alt Green tinha 8 vitórias de eBasket (+R$ 928,00) datadas
// de 10/09; o MTD recorta `[1º do mês, hoje]`, então as 8 caíam fora e o mês fechava
// -R$ 892,87 em vez de +R$ 35,13. Sinal trocado. Piso medido na base: 188 linhas da Bet365.
// O eBasket é o caso que fecha a discussão: ele chega como `CL=18` (Basquete — a casa não os
// separa) e levava 2,5 h de folga num jogo que dura ~4 minutos.
//
// A conversão UK→Brasília NÃO é a folga e continua obrigatória: o payload traz hora de parede
// de Londres. Os dois primeiros casos abaixo separam uma coisa da outra, e é essa separação que
// impede o conserto de virar o defeito espelhado (data um dia ATRASADA).
//
// PROVADO POR MUTAÇÃO (s339) — 5 mutações, 5 detectadas:
//   folga de 2,5 h de volta · conversão de fuso removida · `ukToBr` fixo em 4 · fixo em 3 ·
//   guarda `y < 2000` removida.
// A terceira ESCAPOU na primeira rodada e é o motivo dos dois casos de 03:30: fora da faixa
// 03:00–04:00 UK, UK−3 e UK−4 caem no mesmo dia e o teste ficava verde com o fuso errado.
//
// O QUE ESTE BLOCO NÃO COBRE: bilhete de MÚLTIPLA com pernas em dias diferentes (a escolha da
// perna mais recente é exercida pelas fixtures reais, não aqui) e a transição exata do BST no
// último domingo de março/outubro — `_ehBST` decide por data, sem hora, então um jogo entre
// 00:00 e 01:00 UK no próprio dia da virada pode sair uma hora deslocado. Só muda o DIA se cair
// na faixa das 03h, e não houve amostra medida disso.
function dataDoEvento(fmt) {
  const falhas = [];
  const bilhete = (kickoff) => ({
    bsid: "9", code: "DT1", bc: "1", bt: "1", aberta: false, stake: "100", ts: "100", rt: "0",
    oddFrac: "1/1", sels: [{ na: "A x B", od: "1/1", cl: "18" }],
    legs: [{ sel: "S", jogo: "A x B", mercado: "M", oddFrac: "1/1", cl: "18", liga: "L",
             kickoff, subs: [] }],
  });
  // Rótulo EXATO de propósito: se ele mudar, estes casos falham com `veio ""` e obrigam a
  // decisão consciente — que é o mesmo que o teste de rótulo, logo abaixo, cobra por escrito.
  const dataDe = (kickoff) => linha(fmt(bilhete(kickoff)), "Data (evento):");

  // O caso REAL da s339, com a folga do basquete (CL=18). BST em setembro → BR = UK−4.
  // Kickoff 02:35 UK = 22:35 BR do dia 09. Com a folga de 2,5 h dava 01:05 → "10/09/2026".
  for (const [kickoff, esperado, porque] of [
    ["20260910023500", "09/09/2026", "kickoff 02:35 UK em BST = 22:35 BR do dia ANTERIOR; " +
      "com a folga de 2,5 h do CL=18 isto voltava a ser 10/09 e saía do MTD"],
    ["20260909220000", "09/09/2026", "22:00 UK = 18:00 BR do MESMO dia; a folga empurrava " +
      "para 20:30 BR, que por acaso ainda é o dia certo — é assim que o defeito se esconde"],
    ["20260909233000", "09/09/2026", "23:30 UK = 19:30 BR; com folga, 22:00 BR. O dia só muda " +
      "quando a soma cruza a meia-noite, e é por isso que a folga passava despercebida"],
    ["20260115020000", "14/01/2026", "janeiro é GMT (BR = UK−3): 02:00 UK = 23:00 BR do dia 14. " +
      "Se a conversão de fuso cair junto com a folga, a data vira 15/01 e o defeito volta pelo " +
      "outro lado, com o P/L um dia ADIANTADO"],
    // Os DOIS abaixo existem por uma mutação que ESCAPOU: fixar `ukToBr = 4` deixava o harness
    // verde, porque nos casos acima a diferença entre UK−3 e UK−4 cai dentro do mesmo dia. O
    // horário de verão britânico só troca o DIA na faixa 03:00–04:00 UK, então é ali que ele
    // precisa ser medido — nos dois sentidos, senão só um dos erros é pego.
    ["20260115033000", "15/01/2026", "GMT, 03:30 UK = 00:30 BR do MESMO dia 15. Com UK−4 fixo " +
      "viraria 14/01: é a mutação que passou verde antes destes dois casos existirem"],
    ["20260715033000", "14/07/2026", "BST, 03:30 UK = 23:30 BR do dia ANTERIOR. Com UK−3 fixo " +
      "viraria 15/07 — o mesmo erro espelhado, do outro lado do calendário"],
  ]) {
    const veio = dataDe(kickoff);
    if (veio !== esperado) falhas.push(`data: kickoff ${kickoff} devia sair "${esperado}", veio "${veio}" — ${porque}`);
  }

  // O rótulo é lido pela IA e casado por PREFIXO no `app/tradutor.py`. `(encerramento)` mandava
  // a IA datar o fim de um evento que o payload não tem.
  const txt = fmt(bilhete("20260910023500"));
  if (/Data \(encerramento\)/.test(txt)) {
    falhas.push('data: o bloco voltou a emitir "Data (encerramento):" — o rótulo é o que a IA ' +
                "lê, e ele descreve um instante que a bet365 não informa. O vigente é " +
                '"Data (evento):" (= kickoff). Se a regra mudou, atualize CASA_BET365 §4 junto');
  }
  // USO, não menção: o corpo da função cita `_OFF_B3` no comentário que explica por que a folga
  // saiu. Procurar o nome cru acusaria o próprio aviso e o teste nasceria vermelho.
  if (/_OFF_B3\s*\[|_dataFimB3\s*\(/.test(String(fmt))) {
    falhas.push("data: a folga por esporte (`_OFF_B3`/`_dataFimB3`) voltou ao formatador. Ela " +
                "cria uma janela diária de ~21h→00h em que o bilhete nasce datado de amanhã e " +
                "some do MTD (s339, 188 linhas medidas). Data = kickoff, decisão registrada");
  }

  // A guarda `y < 2000` continua de pé: `TP=00010101000000` NUNCA pode virar "01/01/0001".
  // O que mudou na s373 é para onde ela cai — antes, nada; agora, a COLOCAÇÃO (bloco 5).
  if (dataDe("00010101000000")) {
    falhas.push(`data: bilhete sem kickoff emitiu "Data (evento): ${dataDe("00010101000000")}" — ` +
                "`TP=00010101000000` não é kickoff, é a ausência dele (a guarda `y < 2000`). " +
                "Sem kickoff a data sai como `Data (colocação):`, nunca como evento");
  }

  // ── A colocação NUNCA compete com o kickoff ────────────────────────────────
  // O bilhete abaixo tem os DOIS: kickoff da perna e `da` de colocação, em dias diferentes de
  // propósito. Se alguém inverter a precedência (ou trocar o `else` por um `if` solto), a data
  // do evento é substituída pela da aposta em TODO bilhete que tenha as duas — e o erro é
  // invisível, porque os dois números são datas plausíveis do mesmo bilhete.
  const comAmbos = { ...bilhete("20260910023500"), da: "20260705120000", tp: "20260705120000000" };
  const txtAmbos = fmt(comAmbos);
  if (linha(txtAmbos, "Data (evento):") !== "09/09/2026") {
    falhas.push(`data: com kickoff E colocação, o evento tem de mandar — esperado ` +
                `"Data (evento): 09/09/2026", veio "${linha(txtAmbos, "Data (evento):") || "(nada)"}"`);
  }
  if (linha(txtAmbos, "Data (colocação):")) {
    falhas.push(`data: o bloco emitiu as DUAS linhas de data ("${linha(txtAmbos, "Data (colocação):")}"). ` +
                "O tradutor casa a primeira chave que começa com `Data` (`app/tradutor.py`), então " +
                "duas linhas deixam a escolha ao acaso da ordem");
  }

  // E sem NENHUM dos dois, o bloco continua saindo sem data — o backend decide.
  // Data falsa é pior que data ausente, e é isto que impede a colocação de virar um "" datado.
  const semNada = { ...bilhete("00010101000000"), da: "", tp: "" };
  if (linha(fmt(semNada), "Data (")) {
    falhas.push(`data: sem kickoff e sem colocação o bloco emitiu "${linha(fmt(semNada), "Data (")}" — ` +
                "devia sair sem linha de data nenhuma e deixar o backend usar a data de referência");
  }
  return falhas;
}

// ── 10. "RESOLVER APOSTAS ABERTAS": a busca por carimbo na LISTA (s382) ───────
// Desenho em `docs/PLANO_RESOLVER_ABERTAS.md`. O contrato abaixo foi MEDIDO no F12, em
// conta real, 23/09: a lista vem ordenada por `TP` decrescente, a página é de 10, o `to` é
// inclusivo e é o CURSOR — a página seguinte repete a chamada trocando só o `to`.
//
// O que se prova aqui é o LAÇO, contra uma casa dublada que pagina igual à de verdade. O
// payload é montado no formato real (`F|00;…|01;…`), não um objeto conveniente: é o mesmo
// `parseSummary` da captura que lê os dois.
//
// O QUE ISTO NÃO COBRE: se a casa se comporta como o dublê. Isso só a aba real responde, e
// o contrato veio de lá — três chamadas reais, coladas do F12.
//
// Mutação provada, 5 de 6: o cursor deixa de ser empurrado quando trava · página cheia vira
// fim de lista · a odd viaja fracionária · sem referência de URL o laço chuta em vez de
// recusar · retorno ausente vira zero. Todas ficaram vermelhas.
//
// A 6ª ESCAPA e é INÓCUA **contra este dublê**: tirar o `if (proximo < piso) break` não muda
// nada, porque o `from` da requisição JÁ É o piso e a casa dublada respeita o `from` — a
// página seguinte vem curta e o laço para pelo outro critério. Ela deixa de ser inócua
// contra uma casa que IGNORE o `from`, e é por isso que a linha fica: é defesa em
// profundidade, não redundância. Registrado aqui em vez de virar asserção inventada.
//
// Duas coisas que a 1ª versão destes testes errou, e que valem mais que o verde de agora:
// o dublê punha DOIS bilhetes no mesmo segundo (o cursor só trava quando a PÁGINA INTEIRA
// cai no mesmo segundo), e o teste da URL chutada aceitava qualquer `erro` — mas uma URL
// chutada dá 404, que também é `erro`. Nos dois casos a mutação passou verde primeiro.
function payloadSummary(bilhetes) {
  let s = "F|00;IT=betsummaries;TY=BS;PC=;PT=2026-09-23T12:00:00.0Z;";
  for (const b of bilhetes) {
    s += `|01;ID=${b.id};BT=1;BS=1;BC=1;RA=;TP=${b.tp};PD=#HICO#BSSB#C${b.id}#D0#;`;
    s += "|02;TY=SR;";
    s += `|03;NA=${b.na || "Sel"};FN=${b.na || "Sel"};OD=${b.od || "1/1"};CL=1;FP=0;BA=0;FA=1;FR=0;SY=a;`;
    s += `|02;TY=SD;EW=0;BM=0;ST=${b.st};BC=1;BB=0;NA=Simples;BT=1;TS=${b.st};AB=0;AT=0;MB=0;FR=0;OD=${b.od || "1/1"};`;
    // Aposta ainda aberta vem SEM `RT` — medido nas pendentes reais (settled=0).
    s += b.rt == null ? `|02;TY=ST;ST=${b.st};` : `|02;TY=ST;ST=${b.st};RT=${b.rt};`;
  }
  return s + "|";
}

// Uma casa com N bilhetes servindo páginas de 10 por cursor de tempo, como a real.
// `passoMin` espaça os bilhetes: com 10 min todos cabem na janela de 27h; com 60 min a
// janela CORTA, que é o que prova o piso.
function casaDublada(n, opts) {
  const o = opts || {};
  const passo = (o.passoMin || 10) * 60e3;
  const base = Date.UTC(2026, 8, 23, 18, 0, 0);      // 23/09/2026 18:00, hora "da casa"
  const todos = [];
  for (let i = 0; i < n; i++) {
    const d = new Date(base - i * passo);
    const p = (x) => String(x).padStart(2, "0");
    const tp = `${d.getUTCFullYear()}${p(d.getUTCMonth() + 1)}${p(d.getUTCDate())}` +
               `${p(d.getUTCHours())}${p(d.getUTCMinutes())}${p(d.getUTCSeconds())}000`;
    todos.push({ id: String(49900000000 + i), tp, st: "100.00",
                 rt: o.semRT ? null : "180.00", od: "4/5" });
  }
  // A armadilha nº 2 só morde quando a PÁGINA INTEIRA cai no mesmo segundo: aí o menor
  // carimbo da página é igual ao `to` que a pediu, e repetir a chamada devolve a mesma
  // página para sempre. Dois bilhetes soltos no mesmo segundo NÃO travam nada — foi o que
  // a 1ª versão deste dublê fazia, e a mutação passou verde por isso.
  // Com a folga de 3h e passo de 10 min, o cursor inicial cai 18 posições ACIMA do alvo —
  // é nesse vão que o bloco repetido precisa estar para a página inteira sair no mesmo
  // segundo. Posto em qualquer outro lugar ele fica fora da janela e não prova nada.
  if (o.repetirDe != null) {
    for (let i = o.repetirDe; i < o.repetirDe + 14 && i < todos.length; i++) {
      todos[i].tp = todos[o.repetirDe].tp;
    }
  }
  const chamadas = [];
  return {
    todos,
    chamadas,
    responder(url) {
      if (!/\/sportshistoryapi\/summary/.test(url)) return null;
      const u = new URL(url, "https://members.bet365.bet.br");
      const to = u.searchParams.get("to"), from = u.searchParams.get("from");
      if (!to) return payloadSummary(todos.slice(0, 10));   // 1ª carga da página
      chamadas.push({ to, from });
      const msTo = Date.parse(to), msFrom = Date.parse(from || "1970-01-01T00:00:00Z");
      // ⚠️ O `TP` é hora do REINO UNIDO e o `from`/`to` é UTC — a casa real converte, e o
      // dublê tem de converter também. Sem isto o teste ficaria verde com um código que
      // ignora o fuso, e na aba de verdade a janela erraria por uma hora em silêncio.
      const OFF_UK_UTC = -60 * 60e3;              // BST (UTC+1), o dia medido
      const ms = (b) => Date.parse(
        `${b.tp.slice(0, 4)}-${b.tp.slice(4, 6)}-${b.tp.slice(6, 8)}T` +
        `${b.tp.slice(8, 10)}:${b.tp.slice(10, 12)}:${b.tp.slice(12, 14)}Z`) + OFF_UK_UTC;
      // `to` INCLUSIVO e ordenação decrescente — como a casa real.
      const jan = todos.filter((b) => ms(b) <= msTo && ms(b) >= msFrom)
                       .sort((a, b) => ms(b) - ms(a));
      return payloadSummary(jan.slice(0, 10));
    },
  };
}

// O mecanismo de TOKEN da casa, dublado. Medido: a página expõe um objeto onde se escreve
// a URL alvo, dispara-se um evento com um id e o token assinado volta em `xcft<id>`. Sem
// token a casa devolve **200 com corpo VAZIO** — que é o mesmo que ela devolve quando não há
// aposta na janela. Este dublê reproduz as duas coisas, porque é a confusão entre elas que o
// gate do código precisa desfazer.
//
// `tzaMin` é o ajuste UK → hora local que a casa publica (medido: −240 em BST). Com ele o
// inject calcula a janela de 1 segundo; sem ele (undefined) cai na janela cega e pagina.
function casaComToken(opts) {
  const o = opts || {};
  const estado = { termos: 0, semToken: 0, urlDoUltimoTermo: "" };
  const janelaExtra = {
    ns_gen5_net: { url: "", body: "" },
    Locator: { Guid: "guid-de-teste",
               user: o.tzaMin === undefined ? {} : { timeZoneAdjustment: o.tzaMin } },
  };
  // Quem responde ao pedido de token é a própria "página": escuta `xcftr` e devolve.
  janelaExtra.__aoMontar = (janela) => {
    janela.addEventListener("xcftr", (ev) => {
      const id = ev && ev.detail;
      if (o.tokenMorto) return;                       // a casa renomeou algo: ninguém responde
      estado.termos++;
      estado.urlDoUltimoTermo = janela.ns_gen5_net.url;
      const termo = "T" + estado.urlDoUltimoTermo;    // assinado SOBRE a url, como a real
      janela.dispatchEvent({ type: "xcft" + id, detail: termo });
    });
  };
  return { janelaExtra, estado };
}

async function resolverAbertas() {
  const falhas = [];

  const rodar = async (casa, carimbos, opts) => {
    const o = opts || {};
    const tok = casaComToken({ tzaMin: o.semFuso ? undefined : -240, tokenMorto: o.tokenMorto });
    const { todas, urls } = await rodarInject({
      inject: "b3_inject.js",
      href: "https://members.bet365.bet.br/members/",
      // A 1ª chamada da PÁGINA é o que dá ao inject a referência de URL (origin, lid, cid).
      // Sem ela o laço se recusa a chutar — e isso é uma das coisas provadas abaixo.
      urlInicial: "https://members.bet365.bet.br/sportshistoryapi/summary?settled=1&lid=33&cid=28",
      relogio: "turbo",
      janelaExtra: tok.janelaExtra,
      pedidoMsg: { __sharpenupB3Req: true, acao: "resolver",
                   pedido: { alvos: carimbos, controle: o.controle } },
      // ⚠️ O dublê SÓ responde com token, como a casa real. Sem isso, um código que
      // esquecesse o token passaria verde aqui e devolveria branco na aba de verdade —
      // que foi exatamente o defeito que este caminho teve de corrigir.
      // A requisição INICIAL é a da página (o harness a dispara para dar a referência de
      // URL ao inject) e vem marcada: ela não conta como "o inject esqueceu o token".
      optsInicial: { headers: { "X-Harness-Pagina": "1" } },
      responder: (url, opt) => {
        const daPagina = !!(opt && opt.headers && opt.headers["X-Harness-Pagina"]);
        const temToken = !!(opt && opt.headers && opt.headers["X-Net-Sync-Term"]);
        if (/\/sportshistoryapi\/summary/.test(url) && !temToken && !daPagina) {
          tok.estado.semToken++;
          return "";                       // 200 com corpo VAZIO, como a casa faz
        }
        return casa ? casa.responder(url) : null;
      },
      ms: 1200,
    });
    const msg = (todas || []).filter((m) => m && m.__sharpenupB3Resolver).pop();
    return { msg, urls, tok: tok.estado };
  };

  // ── 10a. Acha o alvo que está a três páginas de distância ───────────────────
  {
    const casa = casaDublada(40);
    const alvo = casa.todos[25].tp.slice(0, 14);          // 26º bilhete → 3ª página
    const { msg } = await rodar(casa, [alvo]);
    if (!msg) {
      falhas.push("resolver: o inject não respondeu `__sharpenupB3Resolver`");
    } else if (msg.encontrados.length !== 1 || msg.encontrados[0].carimbo !== alvo) {
      falhas.push(`resolver: esperava achar o carimbo ${alvo} paginando, veio ` +
                  `${JSON.stringify((msg.encontrados[0] || {}).carimbo)} em ${msg.chamadas} chamada(s)`);
    } else if (msg.chamadas > 5) {
      falhas.push(`resolver: ${msg.chamadas} chamadas para achar um bilhete a 3 páginas — o ` +
                  `cursor não está andando, e cada chamada é uma ida à casa (teto medido: ` +
                  `600 a 1.000 por conta antes do bloqueio)`);
    }
  }

  // ── 10b. O RETORNO viaja, e é dele que sai o resultado ──────────────────────
  {
    const casa = casaDublada(12);
    const alvo = casa.todos[2].tp.slice(0, 14);
    const { msg } = await rodar(casa, [alvo]);
    const e = msg && msg.encontrados[0];
    if (!e || e.retorno !== "180.00" || e.stake !== "100.00") {
      falhas.push(`resolver: o item devia trazer stake e RETORNO da casa, veio ${JSON.stringify(e)}`);
    } else if (e.odd !== "1.8") {
      falhas.push(`resolver: a odd tem de viajar em DECIMAL (4/5 → 1.8), veio "${e.odd}" — o ` +
                  `casamento do outro lado normaliza decimal, e fracionária não casa nunca`);
    }
  }

  // ── 10c. Carimbo REPETIDO não trava o laço ──────────────────────────────────
  // Dois bilhetes no mesmo segundo fazem o menor `TP` da página ser igual ao `to` que a
  // pediu. Sem empurrar o cursor, a chamada seguinte é idêntica e o laço gira para sempre.
  // Medido: 2,03% dos bilhetes compartilham carimbo com outro (639 reais, s382).
  {
    const casa = casaDublada(40, { repetirDe: 12 });   // índices 12..25 no mesmo segundo
    const alvo = casa.todos[30].tp.slice(0, 14);       // abaixo do bloco repetido
    const { msg } = await rodar(casa, [alvo]);
    if (!msg) {
      falhas.push("resolver (carimbo repetido): o inject não respondeu — laço preso?");
    } else if (!msg.encontrados.length) {
      falhas.push(`resolver (carimbo repetido): não achou o alvo em ${msg.chamadas} chamada(s); ` +
                  `o cursor parou de andar quando a página inteira caiu no mesmo segundo`);
    } else if (msg.chamadas > 8) {
      falhas.push(`resolver (carimbo repetido): ${msg.chamadas} chamadas — o cursor está ` +
                  `andando de 1 segundo em vez de pular o bloco`);
    }
  }

  // ── 10d. Alvo que NÃO existe termina, em vez de varrer para sempre ──────────
  {
    // 100 bilhetes de HORA em hora: a casa tem 100h de histórico e a janela do laço cobre 27h.
    // O alvo é um carimbo que NÃO existe, no meio do primeiro dia — se a parada fosse o teto
    // de páginas, o laço varreria os 100; com o piso, ele desiste ao sair da janela.
    const casa = casaDublada(100, { passoMin: 60 });
    const { msg } = await rodar(casa, ["20260923173000"]);
    if (!msg) {
      falhas.push("resolver (alvo inexistente): o inject não respondeu — laço sem fim?");
    } else if (msg.encontrados.length) {
      falhas.push("resolver (alvo inexistente): inventou um casamento");
    } else if (msg.chamadas > 5) {
      falhas.push(`resolver (alvo inexistente): ${msg.chamadas} chamadas atrás de uma aposta ` +
                  `que não existe — a parada tem de ser o PISO da janela (27h ÷ 10 por página ` +
                  `≈ 3 chamadas), nunca o teto de páginas`);
    }
  }

  // ── 10e. Sem referência de URL, RECUSA em vez de chutar ─────────────────────
  // O inject roda em todos os frames, e a lista mora no `members`. Sem ter visto uma
  // chamada da própria página, ele não sabe o origin nem `lid`/`cid` — e chutar daria 404
  // silencioso, que vira "não achou nada" para o operador.
  {
    const { todas } = await rodarInject({
      inject: "b3_inject.js",
      href: "https://www.bet365.bet.br/",
      urlInicial: "https://www.bet365.bet.br/nada",     // nunca é um summary
      relogio: "turbo",
      pedidoMsg: { __sharpenupB3Req: true, acao: "resolver", carimbos: ["20260923180000"] },
      responder: () => null,
      ms: 600,
    });
    const msg = (todas || []).filter((m) => m && m.__sharpenupB3Resolver).pop();
    if (!msg) {
      falhas.push("resolver (sem referência): não respondeu nada — quem pediu fica esperando");
    } else if (!msg.erro) {
      falhas.push("resolver (sem referência): devia devolver ERRO explicando que falta abrir o " +
                  "histórico, e devolveu silêncio");
    } else if (msg.chamadas > 0) {
      falhas.push(`resolver (sem referência): CHAMOU a casa ${msg.chamadas} vez(es) com URL ` +
                  `chutada. Recusar é não chamar — uma URL chutada dá 404 e o erro parece o ` +
                  `mesmo, que foi como a 1ª versão deste teste passou verde com o chute ligado`);
    } else if (msg.apto !== false) {
      // MEDIDO NA CASA (s382): o inject roda em TODOS os frames e o de cima responde
      // PRIMEIRO, porque falha na hora. Quem pediu pegava essa resposta e dizia "abra o
      // Histórico antes" com a lista aberta na tela. A marca `apto` é o que deixa o
      // chamador esperar o frame que realmente pode buscar.
      falhas.push("resolver (sem referência): a resposta não veio marcada como `apto:false`. " +
                  "Sem essa marca, o frame que NÃO pode buscar responde primeiro e ganha");
    }
  }

  // ── 10l. A URL sai com os DOIS-PONTOS LITERAIS, como a da página ───────────
  // O token é assinado SOBRE A URL. `URLSearchParams` percent-encoda os dois-pontos do
  // ISO (`14:35:09` → `14%3A35%3A09`) e a página da casa nunca manda assim, então a
  // assinatura não bate e a resposta vem **200 com corpo de 0 byte** — idêntico, de fora,
  // a "não há aposta nessa janela".
  //
  // Medido em 24/09 com o log de diagnóstico: 19 de 19 chamadas com corpo zero, e a URL
  // no log saindo com `%3A`. Este teste olha a URL que o laço realmente pediu.
  {
    const casa = casaDublada(12);
    const alvo = casa.todos[1].tp.slice(0, 14);
    const { urls } = await rodar(casa, [alvo]);
    const doResolver = (urls || []).filter((u) => /from=/.test(u));
    if (!doResolver.length) {
      falhas.push("resolver: nenhuma URL com janela foi pedida — o teste não mediu nada");
    } else if (doResolver.some((u) => u.includes("%3A"))) {
      falhas.push(`resolver: a URL saiu com dois-pontos ESCAPADOS (${doResolver[0].slice(0, 110)}). ` +
                  `A casa assina a URL e a dela usa ':' literal — escapado, a resposta volta ` +
                  `200 com corpo VAZIO, que parece "não achei" e não é`);
    }
  }

  // ── 10g. O TOKEN é pedido, e assinado sobre a URL RELATIVA ─────────────────
  // A casa devolve 200 com corpo VAZIO para quem não manda o token, e o termo é assinado
  // sobre a URL que se escreve no objeto dela. Mandar a absoluta devolve termo válido e
  // resposta vazia — o pior dos mundos, porque parece funcionar.
  {
    const casa = casaDublada(12);
    const alvo = casa.todos[1].tp.slice(0, 14);
    const { msg, tok } = await rodar(casa, [alvo]);
    if (!tok.termos) {
      falhas.push("resolver: nenhum token foi pedido — a casa devolve vazio sem ele");
    } else if (tok.semToken) {
      falhas.push(`resolver: ${tok.semToken} requisição(ões) saíram SEM token`);
    } else if (/^https?:/i.test(tok.urlDoUltimoTermo)) {
      falhas.push(`resolver: o token foi pedido para a URL ABSOLUTA ("${tok.urlDoUltimoTermo}"). ` +
                  `A casa assina a relativa, e a absoluta devolve termo válido com resposta ` +
                  `vazia — parece que funciona e não funciona`);
    }
    if (msg && !msg.encontrados.length) {
      falhas.push("resolver: com token válido, devia ter achado o alvo");
    } else if (msg && msg.apto !== true) {
      falhas.push("resolver: o frame que ACHOU a aposta não se marcou como apto — quem pediu " +
                  "vai descartar a resposta boa e esperar uma que nunca vem");
    }
  }

  // ── 10h. O GATE: vazio NÃO quer dizer "a aposta segue aberta" ───────────────
  // Se a casa renomear qualquer peça do mecanismo, a resposta passa a vir vazia — o MESMO
  // sintoma de "não há aposta nessa janela". Sem o gate, o botão diria "todas ainda
  // abertas" para sempre, sem erro em lugar nenhum. É a família de defeito mais cara aqui.
  {
    const casa = casaDublada(12);
    const controle = { carimbo: casa.todos[0].tp.slice(0, 14) };
    const { msg } = await rodar(casa, ["20250101120000"], { controle, tokenMorto: true });
    if (!msg) {
      falhas.push("resolver (token morto): o inject não respondeu");
    } else if (msg.confiavel) {
      falhas.push("resolver (token morto): devolveu `confiavel: true` sem o mecanismo " +
                  "funcionar — quem ler isso vai concluir que as apostas seguem abertas");
    } else if (!msg.mecanismo) {
      falhas.push("resolver (token morto): marcou não-confiável sem dizer POR QUÊ");
    }
  }

  // ── 10i. Falta alguém + controle VIVO ⇒ é confiável mesmo assim ─────────────
  // O par do teste acima: sem ele, bastaria marcar tudo como não-confiável para ficar
  // verde, e o botão nunca resolveria nada.
  {
    const casa = casaDublada(12);
    const controle = { carimbo: casa.todos[0].tp.slice(0, 14) };
    const alvo = casa.todos[3].tp.slice(0, 14);
    const { msg } = await rodar(casa, [alvo, "20250101120000"], { controle });
    if (!msg) {
      falhas.push("resolver (controle vivo): o inject não respondeu");
    } else if (!msg.confiavel) {
      falhas.push(`resolver (controle vivo): marcou não-confiável ("${msg.mecanismo}") com a ` +
                  `aposta de controle respondendo normalmente`);
    } else if (msg.encontrados.length !== 1) {
      falhas.push(`resolver (controle vivo): esperava 1 achado, veio ${msg.encontrados.length}`);
    }
  }

  // ── 10j. Com tudo achado, NÃO gasta a requisição de controle ────────────────
  // Cada chamada conta contra o teto de volume da conta (três foram bloqueadas em 20/09).
  // Confirmar o que já se sabe é requisição jogada fora.
  {
    const casa = casaDublada(12);
    const controle = { carimbo: casa.todos[0].tp.slice(0, 14) };
    const alvo = casa.todos[2].tp.slice(0, 14);
    const { msg } = await rodar(casa, [alvo], { controle });
    if (msg && msg.chamadas > 1) {
      falhas.push(`resolver (tudo achado): ${msg.chamadas} chamadas para 1 aposta — o gate de ` +
                  `controle só deve rodar quando alguém NÃO foi achado`);
    }
  }

  // ── 10k. Com o fuso LIDO da casa, é UMA chamada por aposta ─────────────────
  // O carimbo é hora do Reino Unido e a janela é UTC. A casa publica o ajuste em minutos;
  // com ele a janela tem 1 segundo e a aposta vem sozinha. Sem ele, o código abre a janela
  // cega e pagina — funciona, mas custa mais chamadas, e é isso que se mede aqui.
  {
    const casa = casaDublada(40, { passoMin: 10 });
    const alvo = casa.todos[25].tp.slice(0, 14);
    const comFuso = await rodar(casa, [alvo]);
    const semFuso = await rodar(casa, [alvo], { semFuso: true });
    if (!comFuso.msg || !comFuso.msg.encontrados.length) {
      falhas.push("resolver (com fuso): não achou o alvo com a janela de 1 segundo");
    } else if (comFuso.msg.chamadas !== 1) {
      falhas.push(`resolver (com fuso): ${comFuso.msg.chamadas} chamadas para achar UMA aposta ` +
                  `cujo instante exato é conhecido — a janela devia ser de 1 segundo`);
    } else if (comFuso.msg.janelaCega) {
      falhas.push("resolver (com fuso): marcou janela cega com o ajuste disponível");
    }
    if (!semFuso.msg || !semFuso.msg.encontrados.length) {
      falhas.push("resolver (sem fuso): a janela cega tem de achar o alvo mesmo assim");
    } else if (!semFuso.msg.janelaCega) {
      falhas.push("resolver (sem fuso): não avisou que a janela foi cega — quem lê o custo " +
                  "precisa saber por que foram mais chamadas");
    }
    // O MESMO teste com apostas de MINUTO em minuto. Com 10 min entre elas, uma janela
    // afrouxada para 1 hora ainda cabe numa página de 10 e ninguém percebe — foi assim que
    // a mutação "a janela de 1s virou 1h" passou verde na 1ª rodada. Com 1 min, afrouxar
    // empurra o alvo para a 7ª página e o custo aparece.
    const denso = casaDublada(90, { passoMin: 1 });
    const alvoDenso = denso.todos[70].tp.slice(0, 14);
    const r = await rodar(denso, [alvoDenso]);
    if (!r.msg || !r.msg.encontrados.length) {
      falhas.push("resolver (lista densa): não achou o alvo");
    } else if (r.msg.chamadas !== 1) {
      falhas.push(`resolver (lista densa): ${r.msg.chamadas} chamadas. Com o instante exato ` +
                  `conhecido a janela é de 1 SEGUNDO e traz só aquela aposta; qualquer folga ` +
                  `a mais enche a página de vizinhos e paga páginas por nada`);
    }
  }

  // ── 10f. RETORNO AUSENTE viaja como ausência, nunca como zero ──────────────
  // A casa manda aposta ainda aberta SEM `RT` (medido nas pendentes). Achatar isso em "0"
  // faz o bilhete GANHO virar `L` do outro lado, e ninguém vê erro nenhum.
  {
    const casa = casaDublada(12, { semRT: true });
    const alvo = casa.todos[2].tp.slice(0, 14);
    const { msg } = await rodar(casa, [alvo]);
    const e = msg && msg.encontrados[0];
    if (!e) {
      falhas.push("resolver (sem RT): não achou o bilhete — sem retorno ele ainda EXISTE");
    } else if (e.retorno !== null) {
      falhas.push(`resolver (sem RT): retorno devia viajar como null, veio ${JSON.stringify(e.retorno)}`);
    }
  }

  return falhas;
}

// ── 11. O `sync` só enxerga as chaves que o `get()` PEDE (s382) ──────────────
// `chrome.storage.local.get([...])` devolve só o que está na lista, e chave ausente chega
// como `undefined` — **sem erro, sem aviso, sem log**. O código roda inteiro e a condição
// que depende dela é sempre falsa.
//
// Foi exatamente assim que o botão "Resolver apostas abertas" nasceu INVISÍVEL: o `sync`
// testava `st.casa` para saber se a aba é da bet365, e `casa` não estava no `get()`. Tudo
// passou — sintaxe, harness, suíte — e o tester atualizou, conectou na conta certa e não
// viu botão nenhum. Nada em lugar nenhum acusou.
//
// Este teste é ESTRUTURAL (lê o texto do `content.js`) de propósito: o que se quer travar
// é a correspondência entre duas listas, não o comportamento de uma função.
// ── 12. TODA resposta do inject sobe para o TOPO (s382) ──────────────────────
// O `content.js` roda com `all_frames: false` — **só no topo**. O inject roda em TODOS os
// frames, e a lista da bet365 mora num iframe do `members`. Mensagem postada apenas no
// `window` daquele frame não chega a ninguém: quem escuta está noutro documento.
//
// O `enviar()` (a captura) sempre soube disso e posta nos dois. O "Resolver apostas
// abertas" nasceu postando só no próprio frame, e o sintoma foi cruel: a ÚNICA resposta
// que o content recebia era a do frame de cima, que é justamente o que não tem a lista.
// O botão dizia "abra o Histórico uma vez antes" com o Histórico aberto na tela, e nem a
// marca `apto` salvava — a resposta apta nunca chegava.
//
// Teste ESTRUTURAL porque o sandbox tem um documento só: hierarquia de frames é
// exatamente o que ele não dubla, e é aqui que mora a armadilha.
// ── 13. O REPASSE entre frames leva o PEDIDO inteiro (s382) ─────────────────
// O inject repassa o pedido aos frames de dentro copiando CAMPO A CAMPO. Campo novo que
// alguém esquecer de acrescentar chega `undefined` no frame que faz o trabalho — sem erro,
// sem log, sem nada.
//
// Medido na casa: o frame de cima recebeu os 22 alvos e não tinha como buscar; o frame do
// `members` tinha como buscar e recebeu ZERO. O console dizia `0/22` num e `0/0` no outro,
// e as duas linhas pareciam normais.
//
// Estrutural, e pela mesma razão do gate 12: o sandbox tem um documento só.
function repassePreservaOPedido() {
  const falhas = [];
  const src = fs.readFileSync(path.join(EXT, "b3_inject.js"), "utf8");
  const i = src.indexOf("window.frames[i].postMessage({ __sharpenupB3Req");
  if (i < 0) {
    falhas.push("b3_inject.js: não achei o repasse do pedido aos frames — se ele mudou de " +
                "forma, este gate precisa acompanhar");
    return falhas;
  }
  const trecho = src.slice(i, i + 400);
  // Todo campo que o CONTENT manda no pedido tem de aparecer no repasse.
  const content = fs.readFileSync(path.join(EXT, "content.js"), "utf8");
  const j = content.indexOf("__sharpenupB3Req: true, acao: \"resolver\"");
  const doContent = j < 0 ? "" : content.slice(j, j + 200);
  for (const campo of ["pedido", "acao", "jaTem"]) {
    if (!trecho.includes(campo + ":")) {
      falhas.push(`b3_inject.js: o repasse aos frames não leva \`${campo}\`. O frame de ` +
                  `dentro é quem faz o trabalho e receberia esse campo vazio, sem erro nenhum`);
    }
  }
  if (doContent && !doContent.includes("pedido:")) {
    falhas.push("content.js: o pedido de `resolver` não manda `pedido` — o gate acima está " +
                "conferindo um campo que ninguém envia, e viraria falso verde");
  }
  return falhas;
}

function respostaSobeParaOTopo() {
  const falhas = [];
  const src = fs.readFileSync(path.join(EXT, "b3_inject.js"), "utf8");
  // Todo ponto que devolve dado ao content tem de passar por um caminho que também poste
  // no topo. Hoje são dois: `enviar()` (captura) e `responder()` (resolver abertas).
  const sobeAoTopo = (trecho) =>
    /window\.top\s*&&\s*window\.top\s*!==\s*window/.test(trecho) &&
    /window\.top\.postMessage/.test(trecho);
  for (const [nome, marca] of [["enviar (captura)", "function enviar(fim, driver)"],
                               ["responder (resolver abertas)", "function responder(msg)"]]) {
    const i = src.indexOf(marca);
    if (i < 0) {
      falhas.push(`b3_inject.js: não achei \`${marca}\` — se a função mudou de nome, este ` +
                  `gate precisa acompanhar, senão vira falso verde`);
      continue;
    }
    if (!sobeAoTopo(src.slice(i, i + 900))) {
      falhas.push(`b3_inject.js: \`${nome}\` não posta para \`window.top\`. O content roda ` +
                  `SÓ no topo (all_frames: false) e a lista vive num iframe do members — ` +
                  `mensagem que fica no frame não chega a ninguém, sem erro nenhum`);
    }
  }
  return falhas;
}

function chavesDoStorage() {
  const falhas = [];
  const src = fs.readFileSync(path.join(EXT, "content.js"), "utf8");
  const mGet = /chrome\.storage\.local\.get\(\s*\[([^\]]+)\]/.exec(src);
  if (!mGet) {
    falhas.push("content.js: não achei a lista de chaves do `chrome.storage.local.get` — se ela " +
                "mudou de forma, este gate precisa acompanhar, senão vira falso verde");
    return falhas;
  }
  const pedidas = new Set(
    mGet[1].split(",").map((x) => x.trim().replace(/^["']|["']$/g, "")).filter(Boolean));
  // ⚠️ SÓ o trecho do `sync` e do que ele chama. Varrer o arquivo inteiro daria falso
  // positivo em cima de outras variáveis chamadas `st` (há uma no `_resultadoB3`, e
  // `st.scrollHeight` noutro ponto) — a 1ª versão deste gate fazia isso e teria ficado
  // vermelha para sempre, por motivo nenhum.
  const ini = src.indexOf("function ensureResolver(");
  const fim = src.indexOf("chrome.storage.onChanged", ini);
  if (ini < 0 || fim < 0) {
    falhas.push("content.js: não achei o trecho do `sync` para conferir as chaves lidas");
    return falhas;
  }
  const trecho = src.slice(ini, fim);
  const usadas = new Set();
  for (const m of trecho.matchAll(/\bst\.([A-Za-z_$][\w$]*)/g)) usadas.add(m[1]);
  const faltando = [...usadas].filter((k) => !pedidas.has(k));
  if (faltando.length) {
    falhas.push(`content.js: o código lê ${faltando.map((k) => "st." + k).join(", ")} mas ` +
                `\`get()\` não pede ${faltando.join(", ")}. Chave que não se pede chega ` +
                `undefined SEM ERRO, e toda condição que depende dela fica falsa em silêncio ` +
                `— foi o que deixou o botão da bet365 invisível na 0.7.19`);
  }
  return falhas;
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

  // ── 8b. O STATUS SEPARA MEIA VITÓRIA DE VITÓRIA CHEIA (s382) ────────────────
  // Até aqui o Status só comparava retorno com stake, e meia vitória PAGA MAIS QUE A STAKE —
  // então saía como `Ganho → W`. O rótulo é uma ORDEM: a IA obedecia e fechava a conta pela
  // regra de cashout (`odd = retorno ÷ stake`), gravando um W internamente consistente com
  // uma odd que a casa nunca imprimiu. Foram 39 bilhetes na s356 e mais 65 na s382.
  //
  // Os números aqui são de bilhetes REAIS corrigidos na s382, não inventados: a meia vitória
  // é o `#269465` (stake 180, odd 1,9, retorno 261) e a meia derrota é o `#213760`.
  //
  // Mutação provada, 4 de 5: some o ramo de HW · `V` deixa de vir antes de HW · `HL` deixa de
  // exigir linha partida · a odd passa a valer em SISTEMA. Todas ficaram vermelhas.
  //
  // A 5ª ESCAPOU, e é INÓCUA — fica registrado em vez de virar asserção inventada (regra do
  // `CLAUDE.md`). Desligar o ramo de `W` não muda resultado nenhum: `W` e `HW` só dão o mesmo
  // número quando `odd = 1,00`, e aí o retorno é igual à stake, que o `V` já capturou uma
  // linha acima. Sem o ramo de `W`, a vitória cheia cai no `rt > st` do fim e sai com o mesmo
  // rótulo. A linha continua no código porque ela documenta a ordem do MASTER e volta a ser
  // load-bearing se alguém mexer na posição do `V`.
  {
    const bilhete = (rt, oddFrac, sel, extra) => Object.assign({
      bsid: "8", code: "MV", bc: "1", bt: "1", aberta: false,
      stake: "180.00", ts: "180.00", rt, oddFrac,
      sels: [{ na: sel, od: oddFrac, cl: "1" }],
      legs: [perna("A x B", sel, oddFrac, "1", "LIGA")],
    }, extra || {});
    const status = (b) => linha(fmt(b), "Status:");
    const casos = [
      // retorno, odd, seleção, começo esperado do Status, porquê
      ["261.00", "9/10", "Under 3.0,3.5 Gols", "Meia vitória → HW",
       "(180/2 × 1,9) + 90 = 261 — a conta do HW fecha exata"],
      ["342.00", "9/10", "Under 3.0,3.5 Gols", "Ganho → W",
       "180 × 1,9 = 342 — vitória CHEIA não pode virar HW"],
      ["180.00", "9/10", "Under 3.0,3.5 Gols", "Devolvida/void",
       "retorno = stake é V, e V é testado ANTES de W e de HW"],
      ["0", "9/10", "Under 3.0,3.5 Gols", "Perdeu → L", "retorno zero"],
      ["90.00", "9/10", "Under 3.0,3.5 Gols", "Meia derrota → HL",
       "metade da stake de volta, COM linha partida na seleção"],
      ["90.00", "9/10", "Under 3.5 Gols", "Ganho/perda parcial",
       "metade da stake SEM linha partida é cashout de metade, não HL — trocar isso é o " +
       "ruído por ruído que o CLAUDE.md proíbe"],
      ["180.00", "0/1", "Resultado Final", "Devolvida/void",
       "odd 1,00: a fórmula de HW dá exatamente a stake, e só a ordem (V antes) evita que " +
       "um void vire meia vitória — foi esse o erro da 1ª versão do script da s356"],
    ];
    for (const [rt, oddFrac, sel, esperado, porque] of casos) {
      const s = status(bilhete(rt, oddFrac, sel));
      if (!s.startsWith(esperado)) {
        falhas.push(`Status com retorno ${rt} e odd ${oddFrac}: esperava "${esperado}…", veio ` +
                    `"${s}" — ${porque}`);
      }
    }
    // SISTEMA: a odd do bilhete é a MÉDIA das apostas, não a da linha. Testar a fórmula de HW
    // com ela rotula errado — é a mesma exceção que o backend faz com `odd_bloco_manda=False`.
    const sis = bilhete("261.00", "9/10", "Under 3.0,3.5 Gols", {
      bc: "3", bt: "2",
      sels: [{ na: "A x B", od: "9/10", cl: "1" }, { na: "C x D", od: "9/10", cl: "1" },
             { na: "E x F", od: "9/10", cl: "1" }],
      legs: [perna("A x B", "Under 3.0,3.5 Gols", "9/10", "1", "LIGA"),
             perna("C x D", "Under 3.0,3.5 Gols", "9/10", "1", "LIGA"),
             perna("E x F", "Under 3.0,3.5 Gols", "9/10", "1", "LIGA")],
    });
    const sSis = linha(fmt(sis), "Status:");
    if (sSis.startsWith("Meia vitória")) {
      falhas.push(`SISTEMA: o Status usou a odd do bilhete para decidir meia vitória ("${sSis}"). ` +
                  `Num sistema essa odd é a MÉDIA das apostas e não descreve a linha`);
    }
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
