// Bet Panda (BetBy / sptpub) — 4ª casa do motor, ESPELHO da Jonbet/Betboom/Blaze (s391).
//
// SIGILO (decisão do Feca, 02/10/2026): casa normal no seletor, mas fora de aviso aos
// testers, changelog e home.
//
// A Bet Panda não tem inject, formatador nem robô próprios: reusa `jb_inject.js`,
// `formatTicketJB` e `roboJBPassive`. Este caso prova que o mesmo código lê a OUTRA casa
// contra o card DELA.
//
// O que sustenta o espelho, medido no recon (03/10/2026, conta do Feca, Chrome):
//   • `/pt/sportsbook/` carrega `betpanda.sptpub.com/bt-renderer.min.js` NA PRÓPRIA página
//     (sem iframe), e o objeto `BTRenderer` está no mundo da página;
//   • o tráfego sai em `api-a-c7818b61-600.sptpub.com` — MESMO hash de operador (`c7818b61`)
//     das outras três, host fora do padrão `api-NN-sp-…`, e o inject casa por PATH;
//   • mesma query, mesmo topo `{results, count}`, mesmo enum de status;
//   • `status` vazio = todas as abas; "Mostrar mais" pede `skip` 15 e 30, `count` 45
//     constante. A fixture é a conta inteira, na ordem da aba "Todas".
//
// O QUE É NOVO NESTA CASA: a MOEDA. A casa mede em dólar (`currency: "$"`, a URL pede
// `currency=USD`) e a carteira é Tether. A API não distingue um do outro, por isso a moeda
// é da CONTA no cadastro (`docs/PLANO_MOEDA_POR_CONTA.md`). O bloco leva `Moeda: $`, e os
// rótulos de dinheiro do formatador deixam de dizer "R$" — um "retorno R$ 126,00" numa conta
// USDT é rótulo errado na frente da IA. Casa em real continua com o texto byte a byte igual
// (o hash do `bloco_visto` não pode mudar); o fim deste caso trava isso com um clone em R$.
//
// ⚠ O QUE ESTE CASO **NÃO** COBRE, porque a conta não tinha: CASHOUT executado, REFUND,
// CANCELED (as três abas voltaram `count: 0`) e FREEBET. Esses ramos são compartilhados e
// provados nos casos da Jonbet e da Blaze; aqui ficam sem rede.
//
// ⚠ PROCEDÊNCIA DOS VALORES ESPERADOS. Os marcados `card` foram lidos na tela da casa em
// 03/10/2026 (abas Ganhas e Perdidas). Os marcados `json` vêm do corpo da resposta, que nos
// lidos bateu com o card até o centavo — dito em voz alta em vez de fingir leitura de tela.
// As datas são as do `_dhJB` (São Paulo); o card mostra as mesmas horas sem os segundos.
//
// AS ARMADILHAS QUE ESTE CASO TRAVA
//
// 1. `total_k: "0"` nas PERDIDAS SIMPLES, com `k` guardando a odd do card (6,80). Mas nas
//    MÚLTIPLAS perdidas o `total_k` NÃO zera sempre: `…1085` traz 7,59 e o card estampa
//    7.59; `…4089` traz 0 e o card estampa 3.422 (o `k`). Quem tratar "total_k = 0" como
//    regra da perdida lê um dos dois errado.
//
// 2. BOOST (`bonus.type: "comboboost"`, `total_multiplier: "1.05"`). Na GANHA `…8141`,
//    `k` = `total_k` = 9,004 (com boost) e `result_k` = 8,575 (o produto das pernas, sem
//    boost); a casa paga pela odd com boost (2,66 × 9,004 = 23,95). Na PERDIDA `…4829` os
//    dois divergem: `k` 10,781 e `total_k` 10,268, e o card estampa **10.268**. O caso trava
//    os dois lados: o `result_k` nunca vira odd, e na perdida vale o `total_k` da tela.
//
// 3. SISTEMA 2/3 (`…5814`): `k` 12,608 é a SOMA das 3 combinações e `total_k` 37,825 é o
//    produto das 3 pernas. O card estampa "Ganhaste 151.30 $" sobre aposta de 36: a odd do
//    W tem de explicar esse retorno (151,30 ÷ 36), não nenhum dos dois campos.
//
// 4. `cashout_amount` preenchido em ABERTA (`…9072`: 48 sobre aposta de 50) é a OFERTA de
//    venda antecipada, nunca retorno. O bloco não pode dizer "Cashout executado".
//
// 5. `timestamp` com FRAÇÃO de segundo (`1790983719.876…`): a data tem de sair inteira.
import { rodarInject, carregarContent, fixture, linha } from "../sandbox.mjs";

export const casa = "BETPANDA";

const W = /^Ganho → W \(retorno [\d.]+,\d{2} \$\)$/;   // rótulo na moeda da CASA, nunca "R$"
const L = /^Perdeu → L$/;
const AB = /^em aberto \(aguardando resultado/;

const ESPERADO = {
  // — ganhas (card) —
  "2717948654752248251": { odd: "1,8",   status: W, stake: "70,00", data: "02/10/2026 20:28:39", evento: "03/10/2026 06:30:00", ret: 126,    p: "card" },
  "2717622591195066843": { odd: "1,9",   status: W, stake: "70,18", data: "01/10/2026 22:53:33", evento: "02/10/2026 11:55:00", ret: 133.34, p: "card" },
  "2717570154962755919": { odd: "1,9",   status: W, stake: "98,37", data: "01/10/2026 19:24:38", evento: "02/10/2026 09:15:00", ret: 186.90, p: "card" },
  "2717477091854651739": { odd: "1,83",  status: W, stake: "25,00", data: "01/10/2026 13:14:44", evento: "02/10/2026 13:00:00", ret: 45.75,  p: "card" },
  "2717464096248308141": { odd: "9,004", status: W, stake: "2,66",  data: "01/10/2026 12:23:05", evento: "01/10/2026 23:00:00", ret: 23.95,  p: "card (odd e aposta) · json (retorno)" },
  "2717463857143615814": { odd: null,    status: W, stake: "36,00", data: "01/10/2026 12:22:11", evento: "01/10/2026 23:00:00", ret: 151.30, p: "card" },
  // — perdidas (card) —
  "2718024238408802582": { odd: "6,8",    status: L, stake: "15,00", data: "03/10/2026 01:29:30", evento: "03/10/2026 01:30:00", p: "card" },
  "2717991405585834099": { odd: "3,422",  status: L, stake: "25,00", data: "02/10/2026 23:18:49", evento: "03/10/2026 12:00:00", p: "card" },
  "2717965946273801085": { odd: "7,59",   status: L, stake: "25,00", data: "02/10/2026 21:37:24", evento: "03/10/2026 02:00:00", p: "card" },
  "2717516692963074829": { odd: "10,268", status: L, stake: "25,00", data: "01/10/2026 15:52:01", evento: "02/10/2026 15:45:00", p: "card" },
  // — abertas (json) —
  "2718153629814109072": { odd: "2",      status: AB, stake: "50,00", data: "03/10/2026 10:03:10", evento: "03/10/2026 10:30:00", potencial: "100,00 $", p: "json" },
  "2717826586882744380": { odd: "12,285", status: AB, stake: "25,00", data: "02/10/2026 12:23:17", evento: "03/10/2026 17:00:00", potencial: "307,13 $", p: "json" },
};

const SISTEMA = "2717463857143615814";
const BOOST_GANHO = { id: "2717464096248308141", semBoost: "8,575" };
const BOOST_PERDIDO = { id: "2717516692963074829", k: "10,781" };
const CASHOUT_OFERTA = "2718153629814109072";

const PAGINA_FALSA = 7;   // o servidor do teste devolve no MÁXIMO 7, ignorando o `limit` pedido

export async function rodar() {
  const base = "https://api-a-c7818b61-600.sptpub.com/api/v1/my_bets/list";
  const todos = JSON.parse(fixture("betpanda.my_bets.json")).results;
  // ⚠ Corpo do 401 REUSADO da Jonbet, declarado: o gancho do recon entrou depois do load e
  // não viu a 1ª chamada sem token. A guarda exercitada é a do inject, compartilhada.
  const err401 = fixture("jonbet.my_bets_401.json");
  let servidas = 0, negadas = 0;

  const responder = (url, opts) => {
    if (!/my_bets\/list/.test(url)) return null;
    const h = (opts && opts.headers) || {};
    if (!(h.Authorization || h.authorization)) { negadas++; return err401; }
    servidas++;
    let skip = 0;
    try { skip = Number(new URL(url).searchParams.get("skip")) || 0; } catch (e) {}
    return JSON.stringify({ results: todos.slice(skip, skip + PAGINA_FALSA), count: todos.length });
  };

  // Query REAL da aba "Todas" (capturada no recon): `status` vazio, `currency=USD`.
  const alvo = `${base}?currency=USD&lang=pt&limit=15&skip=0&status=&timestamp_from=&timestamp_to=`;
  const { ultima, urls } = await rodarInject({
    inject: "jb_inject.js",          // ← o MESMO das outras três BetBy
    href: "https://betpandacasino.io/pt/sportsbook/?bt-path=%2Fbets",
    urlInicial: alvo,
    optsInicial: { method: "GET", headers: { "Content-Type": "application/json" } },
    urlsExtra: [{ url: alvo, opts: { method: "GET", headers: { "Content-Type": "application/json", Authorization: "Bearer harness.token.falso" } } }],
    pedido: "__sharpenupJBReq",
    responder,
  });

  const falhas = [];
  if (!ultima) return { falhas: ["o inject não emitiu nenhuma mensagem"], testes: 0 };
  if (!ultima.hook) falhas.push("o inject não emitiu `hook:true` (autodiagnóstico cego)");
  if (!ultima.fim) falhas.push("o inject não sinalizou `fim` (o robô ficaria esperando o teto)");

  const bilhetes = ultima.bilhetes || [];
  if (bilhetes.length !== todos.length) falhas.push(`esperava ${todos.length} bilhetes normalizados, vieram ${bilhetes.length}`);

  const fmt = carregarContent().pegar("formatTicketJB");
  const porId = new Map(bilhetes.map((b) => [b.id, b]));
  let testes = 0;

  // Toda linha da conta: marcador, moeda e nenhum "R$" — a conta é USDT, a casa fala "$".
  for (const b of bilhetes) {
    const txt = fmt(b);
    if (!txt.startsWith(`[Código: ${b.id}]`)) falhas.push(`${b.id}: marcador [Código:] ausente/errado`);
    if (linha(txt, "Moeda:") !== "$") falhas.push(`${b.id}: faltou a linha "Moeda: $" (o servidor não saberia que a casa falou em dólar)`);
    if (/R\$/.test(txt)) falhas.push(`${b.id}: o bloco diz "R$" numa conta em dólar: ${txt.split("\n").find((l) => /R\$/.test(l))}`);
    if (!linha(txt, "Status (API):")) falhas.push(`${b.id}: falta o status cru da API`);
  }

  for (const [id, e] of Object.entries(ESPERADO)) {
    const b = porId.get(id);
    if (!b) { falhas.push(`${id} (${e.p}): sumiu da normalização`); continue; }
    const txt = fmt(b);
    testes++;
    const odd = linha(txt, "Odd:"), status = linha(txt, "Status:"), stake = linha(txt, "Stake:");
    const data = linha(txt, "Data (colocação):"), evento = linha(txt, "Data (evento mais recente):");
    if (e.odd != null && odd !== e.odd) falhas.push(`${id} (${e.p}): odd esperada ${e.odd}, veio "${odd}"`);
    if (!e.status.test(status)) falhas.push(`${id} (${e.p}): status "${status}"`);
    if (stake !== e.stake) falhas.push(`${id} (${e.p}): stake esperada ${e.stake}, veio "${stake}"`);
    if (data !== e.data) falhas.push(`${id}: data de colocação esperada ${e.data}, veio "${data}" (o timestamp tem fração de segundo)`);
    if (evento !== e.evento) falhas.push(`${id}: data do EVENTO esperada ${e.evento}, veio "${evento}" (é ela que vai para a coluna Data)`);
    if (L.test(status) && /^0*(,0*)?$/.test(odd)) falhas.push(`${id}: odd zerada numa PERDIDA — leu total_k cru`);
    // W: a odd tem de explicar o retorno do card até o centavo.
    if (e.ret != null) {
      const n = Number(String(odd).replace(",", "."));
      const st = Number(e.stake.replace(".", "").replace(",", "."));
      if (!(Math.abs(n * st - e.ret) <= 0.01)) falhas.push(`${id} (${e.p}): odd ${odd} × stake ${e.stake} não explica o retorno ${e.ret}`);
    }
    if (e.potencial != null && linha(txt, "Retorno potencial:") !== e.potencial) {
      falhas.push(`${id}: retorno potencial esperado "${e.potencial}", veio "${linha(txt, "Retorno potencial:")}"`);
    }
  }

  // Armadilha 2: o `result_k` (sem boost) nunca vira a odd da ganha; e na perdida com boost
  // vale o `total_k` que o card estampa, não o `k`.
  {
    const g = porId.get(BOOST_GANHO.id);
    if (g && linha(fmt(g), "Odd:") === BOOST_GANHO.semBoost) falhas.push(`${BOOST_GANHO.id}: odd ${BOOST_GANHO.semBoost} é o result_k SEM boost — a casa pagou 9,004`);
    if (g && !/comboboost/.test(linha(fmt(g), "Bônus aplicado:"))) falhas.push(`${BOOST_GANHO.id}: o bônus sumiu do bloco (a IA não saberia que a odd tem boost)`);
    const p = porId.get(BOOST_PERDIDO.id);
    if (p && linha(fmt(p), "Odd:") === BOOST_PERDIDO.k) falhas.push(`${BOOST_PERDIDO.id}: odd ${BOOST_PERDIDO.k} é o k — o card estampa 10.268 (total_k)`);
  }
  // Armadilha 3: o sistema se declara como sistema.
  {
    const s = porId.get(SISTEMA);
    if (s && !/^Sistema \(3 combinação/.test(linha(fmt(s), "Tipo:"))) falhas.push(`${SISTEMA}: tipo "${linha(fmt(s), "Tipo:")}" — o 2/3 não foi lido como sistema`);
  }
  // Armadilha 4: oferta de cashout em aberta não é cashout executado.
  {
    const a = porId.get(CASHOUT_OFERTA);
    if (a && a.cashout !== 48) falhas.push(`${CASHOUT_OFERTA}: a fixture deixou de ter a oferta de cashout (48) — o caso perdeu o que travava`);
    if (a && /Cashout executado/.test(fmt(a))) falhas.push(`${CASHOUT_OFERTA}: oferta de cashout de uma ABERTA virou "Cashout executado"`);
  }

  // Casa em REAL não pode mudar um byte: o mesmo bilhete com `moeda` R$ e vazia tem de sair
  // com os rótulos "R$" de sempre e sem linha `Moeda:`. É o que protege o hash do
  // `bloco_visto` da Jonbet, da Betboom e da Blaze.
  for (const m of ["R$", "BRL", ""]) {
    const g = { ...porId.get("2717948654752248251"), moeda: m };
    const a = { ...porId.get(CASHOUT_OFERTA), moeda: m };
    const tg = fmt(g), ta = fmt(a);
    if (linha(tg, "Status:") !== "Ganho → W (retorno R$ 126,00)") falhas.push(`moeda "${m}": o rótulo do ganho mudou para "${linha(tg, "Status:")}" (casa em real tem de ficar igual)`);
    if (linha(ta, "Retorno potencial:") !== "R$ 100,00") falhas.push(`moeda "${m}": o retorno potencial mudou para "${linha(ta, "Retorno potencial:")}"`);
    if (linha(tg, "Moeda:")) falhas.push(`moeda "${m}": casa em real ganhou linha "Moeda:"`);
  }

  if (servidas < 3) falhas.push(`o replay pediu só ${servidas} página(s) autenticada(s) — não varreu a lista`);
  if (!negadas) falhas.push("o corpo 401 nunca foi servido — a guarda do token não foi exercitada");
  if (negadas > 1) falhas.push(`${negadas} requisições sem Bearer — o replay está repaginando sem token`);
  if (urls.length < 4) falhas.push(`replay não repaginou o bastante (só ${urls.length} requisição(ões) para ${todos.length} bilhetes em páginas de ${PAGINA_FALSA})`);
  return { falhas, testes };
}
