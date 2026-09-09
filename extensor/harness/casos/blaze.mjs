// Blaze (BetBy / sptpub) — 3ª casa do motor, ESPELHO da Jonbet/Betboom (s336).
//
// A Blaze não tem inject, formatador nem robô próprios: reusa `jb_inject.js`,
// `formatTicketJB` e `roboJBPassive`. Este caso existe porque o compartilhamento é
// justamente a parte perigosa — ele prova que o mesmo código lê a OUTRA casa contra o
// card DELA, e não que "deve funcionar porque é igual".
//
// O que sustenta o espelho, medido no recon (09/09/2026) e não deduzido:
//   • a home de `/pt/sports` carrega `blaze.sptpub.com/bt-renderer…` NA PRÓPRIA página;
//   • o tráfego sai em `api-31-sp-c7818b61-584.sptpub.com` — MESMO cluster (`31`) e MESMO
//     hash de operador (`c7818b61`) da Jonbet, e o inject casa por PATH (`/my_bets/list`),
//     nunca por host;
//   • mesma query, mesmo topo `{results, count}`, mesmo enum de status;
//   • `status` vazio = todas as abas (varredura ao vivo fechou em `count: 165`).
//
// ⚠ O QUE ESTE CASO **NÃO** COBRE, porque a conta do recon não tinha:
//   aposta ABERTA (zero no momento da varredura), CASHOUT executado (a aba
//   `status=cashed_out` voltou `count: 0`), BOOST, FREEBET e bilhete de SISTEMA
//   (`combinations` vazio em 165 de 165). Esses ramos são compartilhados e já provados
//   pelos casos da Jonbet e da Betboom — aqui eles ficam sem rede. Verde neste arquivo
//   não é promessa sobre eles.
//
// ⚠ PROCEDÊNCIA DOS VALORES ESPERADOS. Cinco dos oito cards foram lidos verbatim na tela
// (marcados `card` abaixo). Os três de março/2025 estão ~100 posições abaixo na lista, o
// filtro "Personalizado" da casa travou carregando e a página se recarregou sozinha — para
// eles o esperado vem do PRÓPRIO corpo da resposta (`total_k`/`k` e `result_sum`), que nos
// cinco lidos bateu com o card até o centavo. Está dito em voz alta em vez de fingir
// leitura de tela.
//
// AS ARMADILHAS QUE ESTE CASO TRAVA
//
// 1. `total_k: "0"` em 86 de 86 PERDIDAS da conta (100%), com `k` guardando a odd que o
//    card estampa — `2525430461438767391` mostra "Total de odds 1.75" na tela com
//    `total_k: "0"` no JSON. `result_k` acompanha o zero e não serve de resgate.
//
// 2. ⚠ A NOVA, e é dela que este caso existe: em 4 das 86 perdidas **`k` TAMBÉM vem "0"**,
//    e aí a odd só existe dentro da seleção. No card a linha "Total de odds" aparece
//    **VAZIA** — a casa também não tem o número e NÃO escreve zero nenhum. Ler o campo cru
//    grava `0` numa coluna Odd, que é a família do "zero não é ausência" (CLAUDE.md): passa
//    em toda checagem de forma porque tem cara de conta feita. O degrau que faltava é o
//    produto das odds das seleções.
//
// 3. `refund` e `canceled` ACHATAM `k`/`total_k` para `"1"` com `result_sum` = `sum`. Aqui
//    o 1 é a verdade da tela (o card estampa "Total de odds 1"), e o produto das seleções
//    (2,5 e 1,5) seria uma invenção. Por isso o degrau novo só pode disparar quando os DOIS
//    campos vêm zerados — este caso trava os dois lados.
//
// 4. Múltipla vem com `k` TRUNCADO em 3 casas (`1.598` para 1,12 × 1,22 × 1,17 = 1,5987) e
//    o dinheiro guarda o valor cheio (`result_sum` 639,48 sobre stake 400). Quem gravar a
//    declarada perde 0,28 de retorno na conta.
//
// PAGINAÇÃO, provada ao vivo NESTA casa: pedi `limit=100` e a Blaze devolveu **21 por
// página**, oito páginas, `count` constante em 165, última parcial (18), sem id repetido
// nem pulado. Ou seja: a casa IGNORA o `limit` pedido. O `responder` abaixo reproduz isso
// devolvendo no máximo 3 — é assim que se prova que o inject avança pelo tamanho que
// VOLTOU, e não pelo que pediu. Avançar pelo `PAGINA` pularia 79 bilhetes por página.
import { rodarInject, carregarContent, fixture, linha } from "../sandbox.mjs";

export const casa = "BLAZE";

// `data` = colocação · `evento` = data da perna mais recente, que é a que vai para a coluna
// Data do TSV (`MASTER_OUTPUT §4`). Repare em `2525430461438767391`: o evento (13:30) é
// ANTES da colocação (14:30) — aposta ao vivo. E em `2518879929848968006` a distância é de
// cinco dias. Travar só a colocação poria bilhete no dia errado nos dois sentidos.
const ESPERADO = {
  // — cards lidos verbatim na tela (09/09/2026) —
  "2550618250014765290": { odd: "1,96",   status: /^Ganho → W/,   stake: "3,00",   data: "28/06/2025 02:41:49", evento: "28/06/2025 15:00:00" },
  "2525430461438767391": { odd: "1,75",   status: /^Perdeu → L$/, stake: "132,00", data: "19/04/2025 14:30:07", evento: "19/04/2025 13:30:00" },
  "2518879929848968006": { odd: "1,92",   status: /^Perdeu → L$/, stake: "10,03",  data: "01/04/2025 12:41:31", evento: "06/04/2025 06:00:00" },
  "2525418650672964347": { odd: "1",      status: /→ V$/,         stake: "111,00", data: "19/04/2025 13:43:18", evento: "19/04/2025 12:00:00" },
  "2512818070402249307": { odd: "1",      status: /→ V$/,         stake: "156,00", data: "15/03/2025 19:13:20", evento: "16/03/2025 16:00:00" },
  // — os três de março: esperado tirado do corpo da resposta, não da tela (ver cabeçalho) —
  "2517462925057331668": { odd: "1,5987", status: /^Ganho → W/,   stake: "400,00", data: "28/03/2025 14:50:30", evento: "28/03/2025 23:00:00" },
  "2510179906730729604": { odd: "10,841", status: /^Perdeu → L$/, stake: "15,27",  data: "08/03/2025 12:29:44", evento: "08/03/2025 22:00:00" },
  "2507739696281559611": { odd: "7,572",  status: /^Perdeu → L$/, stake: "200,00", data: "01/03/2025 18:53:37", evento: "02/03/2025 11:30:00" },
};

// Retorno que o card estampa em "Você ganhou" — a odd do W tem de explicá-lo até o centavo.
// O 5,88 foi lido na tela; o 639,48 é o `result_sum` do bilhete de 28/03 (ver cabeçalho).
const RETORNO_CARD = { "2550618250014765290": 5.88, "2517462925057331668": 639.48 };

// O bilhete em que a casa NÃO TEM odd: `k` e `total_k` zerados juntos, odd viva só na
// seleção (1,92) e "Total de odds" VAZIO no card. É o caso que o degrau do produto resolve.
const SEM_ODD_NO_TOPO = "2518879929848968006";

// Os dois em que o `1` é a VERDADE da tela, não uma ausência: o produto das seleções aqui
// (2,5 e 1,5) seria invenção. Trava o outro lado do mesmo degrau.
const ODD_UM_LEGITIMA = { "2525418650672964347": 2.5, "2512818070402249307": 1.5 };

const PAGINA_FALSA = 3;   // o servidor do teste devolve no MÁXIMO 3, ignorando o `limit` pedido

export async function rodar() {
  const base = "https://api-31-sp-c7818b61-584.sptpub.com/api/v1/my_bets/list";
  const todos = JSON.parse(fixture("blaze.my_bets.json")).results;
  // ⚠ Corpo do 401 REUSADO da Jonbet, de propósito e declarado: é o mesmo motor BetBy, mas
  // na Blaze a 1ª chamada sem token NÃO foi capturada ao vivo (o gancho do recon entrou
  // depois do load). A guarda que este caso exercita é a do inject, que é compartilhada.
  const err401 = fixture("jonbet.my_bets_401.json");
  let servidas = 0, negadas = 0;

  const responder = (url, opts) => {
    if (!/my_bets\/list/.test(url)) return null;
    // Sem Bearer = a chamada que a página dispara antes de autenticar. O corpo TEM uma chave
    // `status` que não é status de bilhete — quem checar só "veio JSON" cai nela.
    const h = (opts && opts.headers) || {};
    if (!(h.Authorization || h.authorization)) { negadas++; return err401; }
    servidas++;
    let skip = 0;
    try { skip = Number(new URL(url).searchParams.get("skip")) || 0; } catch (e) {}
    // `count` é sempre o total do filtro (constante entre páginas) — é o fim autoritativo.
    // Além do fim a casa devolve 200 com lista vazia; nunca erro, nunca repetição.
    return JSON.stringify({ results: todos.slice(skip, skip + PAGINA_FALSA), count: todos.length });
  };

  // Query REAL que a Blaze dispara ao abrir "As Minhas Apostas" (capturada no recon):
  // a aba "Apostas abertas" é a primeira, então `status=open` com `limit=15`.
  const alvo = `${base}?currency=BRL&lang=pt-BR&limit=15&skip=0&status=open&timestamp_from&timestamp_to`;
  const { ultima, urls } = await rodarInject({
    inject: "jb_inject.js",          // ← o MESMO da Jonbet/Betboom, sem uma linha de diferença
    href: "https://blaze.bet.br/pt/sports?bt-path=%2Fbets",
    // Sequência real do motor: a página dispara a lista ANTES de o token chegar (→ 401) e só
    // depois refaz autenticada. O inject tem de ignorar a primeira e aprender a segunda.
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
  if (bilhetes.length !== 8) falhas.push(`esperava 8 bilhetes normalizados, vieram ${bilhetes.length}`);

  const fmt = carregarContent().pegar("formatTicketJB");   // ← formatador compartilhado
  let testes = 0;
  for (const b of bilhetes) {
    const e = ESPERADO[b.id];
    if (!e) { falhas.push(`bilhete inesperado na fixture: ${b.id}`); continue; }
    const txt = fmt(b);
    testes++;
    if (!txt.startsWith(`[Código: ${b.id}]`)) falhas.push(`${b.id}: marcador [Código:] ausente/errado`);
    const odd = linha(txt, "Odd:");
    const status = linha(txt, "Status:");
    const stake = linha(txt, "Stake:");
    const data = linha(txt, "Data (colocação):");
    const evento = linha(txt, "Data (evento mais recente):");
    if (evento !== e.evento) falhas.push(`${b.id}: data do EVENTO esperada ${e.evento}, veio "${evento}" (é ela que vai para a coluna Data)`);
    if (odd !== e.odd) falhas.push(`${b.id}: odd esperada ${e.odd}, veio "${odd}"`);
    if (!e.status.test(status)) falhas.push(`${b.id}: status "${status}"`);
    if (stake !== e.stake) falhas.push(`${b.id}: stake esperada ${e.stake}, veio "${stake}"`);
    if (data !== e.data) falhas.push(`${b.id}: data esperada ${e.data}, veio "${data}"`);
    // A armadilha 1, dita em voz alta: perdida NUNCA pode sair com odd zerada.
    if (/Perdeu/.test(status) && /^0*(,0*)?$/.test(odd)) falhas.push(`${b.id}: odd zerada numa PERDIDA — leu total_k cru`);
    // O status cru precisa subir junto: é ele que a CASA_BLAZE.md traduz.
    if (!linha(txt, "Status (API):")) falhas.push(`${b.id}: falta o status cru da API`);
    // Armadilha 2: com os DOIS campos do topo zerados, a odd tem de vir da seleção.
    if (b.id === SEM_ODD_NO_TOPO) {
      if (b.oddTotal !== 0 || b.oddBilhete !== 0) {
        falhas.push(`${SEM_ODD_NO_TOPO}: a fixture deixou de ter total_k E k zerados — o caso perdeu o que travava`);
      }
      if (!(b.sels || []).length || b.sels[0].odd !== 1.92) {
        falhas.push(`${SEM_ODD_NO_TOPO}: a odd da seleção (1,92) sumiu da normalização — sem ela não há de onde derivar`);
      }
    }
    // Armadilha 3: no refund/canceled o `1` é a tela, não uma ausência — o produto das
    // seleções NÃO pode vencer. Sem esta trava, o degrau novo passaria a inventar odd aqui.
    const prod = ODD_UM_LEGITIMA[b.id];
    if (prod != null && odd === String(prod).replace(".", ",")) {
      falhas.push(`${b.id}: odd ${odd} é o produto das seleções — mas o card estampa "Total de odds 1" (V não é ausência de odd)`);
    }
    // W: a odd tem de explicar o retorno até o centavo.
    const ret = RETORNO_CARD[b.id];
    if (ret != null) {
      const n = Number(odd.replace(",", "."));
      const st = Number(e.stake.replace(".", "").replace(",", "."));
      if (!(Math.abs(n * st - ret) <= 0.01)) falhas.push(`${b.id}: odd ${odd} × stake ${e.stake} não explica o retorno ${ret}`);
    }
  }
  if (servidas < 3) falhas.push(`o replay pediu só ${servidas} página(s) autenticada(s) — não varreu a lista`);
  // Prova que a guarda do token foi mesmo exercitada: se o 401 nunca chegou a ser servido, o
  // teste acima não significa nada (era o buraco da 1ª versão do caso da Jonbet).
  if (!negadas) falhas.push("o corpo 401 nunca foi servido — a guarda do token não foi exercitada");
  // E que o replay nunca repetiu a chamada sem token (seria 401 em loop na casa real).
  if (negadas > 1) falhas.push(`${negadas} requisições sem Bearer — o replay está repaginando sem token`);
  if (urls.length < 4) falhas.push(`replay não repaginou o bastante (só ${urls.length} requisição(ões) para 8 bilhetes em páginas de ${PAGINA_FALSA})`);
  return { falhas, testes };
}
