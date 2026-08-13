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
import { rodarInject, carregarContent, fixture, linha } from "../sandbox.mjs";

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

  return { falhas, testes: bets.length };
}
