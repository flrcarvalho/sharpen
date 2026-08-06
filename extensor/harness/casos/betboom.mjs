// Betboom (BetBy / sptpub) — ESPELHO da Jonbet (s250).
//
// A Betboom não tem inject, formatador nem robô próprios: ela reusa `jb_inject.js`,
// `formatTicketJB` e `roboJBPassive`, como a Betfast reusa os da Tivo. Este caso existe
// justamente porque o compartilhamento é a parte perigosa — ele prova que o mesmo código
// lê a OUTRA casa contra o card DELA, e não que "deve funcionar porque é igual".
//
// O que sustenta o espelho, medido no recon e não deduzido:
//   • as duas rodam BetBy, com o MESMO hash de operador (`c7818b61`) e clusters diferentes
//     (`api-32-…` × `api-31-…`) — e o inject casa por PATH (`/my_bets/list`), nunca por host;
//   • mesma query, mesmo topo `{results, count}`, mesmo enum de status;
//   • `status` vazio = todas as abas (confirmado ao vivo aqui, `count: 7`).
//
// A ARMADILHA DA ODD se reproduz inteira, e o card é a prova: as duas PERDIDAS estampam
// "Total de odds 1.87" e "1.71" na tela, enquanto o JSON traz `total_k: "0"` — e `result_k`
// acompanha o zero, então não serve de resgate. Ler o campo cru gravaria odd zero em 100%
// das perdas. Regra (a mesma do app da casa): total_k === 0 ? k : total_k.
//
// PAGINAÇÃO provada ao vivo NESTA casa, forçando `limit=3` sobre os 7 bilhetes:
// skip 0/3/6 → 3,3,1 (soma exata de `count`, sem id repetido nem pulado), `count` constante,
// e **skip=9 → 200 com lista VAZIA**, nunca erro, nunca repetição da última página. O
// `responder` reproduz isso e, de propósito, **ignora o `limit` pedido** e devolve no máximo
// 3: é assim que se prova que o inject avança pelo tamanho que VOLTOU, não pelo que pediu.
import { rodarInject, carregarContent, fixture, linha } from "../sandbox.mjs";

export const casa = "BETBOOM";

// Cada valor abaixo foi lido do CARD (print da aba "Todas" de 06/08/2026) — os 7 bilhetes
// da conta estavam visíveis de uma vez, então aqui NÃO há a exceção honesta que o caso da
// Jonbet precisou abrir para o 10º bilhete.
//
// `evento` é a data que VAI PARA A COLUNA DATA do TSV (`MASTER_OUTPUT §4`) e é a que o card
// estampa no topo do bloco branco ("Amanhã, 01:40" · "Hoje, 01:05").
// ⚠ Nesta casa os **7 de 7** caem num DIA diferente da colocação — badminton coreano de
// madrugada apostado na tarde anterior. É a divergência da Jonbet (7 de 10) ainda mais
// extrema: travar só a colocação poria a base INTEIRA no dia errado.
const ESPERADO = {
  "2697206242308395133": { odd: "1,87", status: /em aberto/,    stake: "350,00", data: "06/08/2026 14:45:58", evento: "07/08/2026 01:40:00" },
  "2697202348291400179": { odd: "5",    status: /em aberto/,    stake: "100,00", data: "06/08/2026 14:30:46", evento: "07/08/2026 05:00:00" },
  "2697202108746305608": { odd: "2,72", status: /em aberto/,    stake: "300,00", data: "06/08/2026 14:29:50", evento: "07/08/2026 01:40:00" },
  "2696893043805663332": { odd: "1,87", status: /^Perdeu → L$/, stake: "500,00", data: "05/08/2026 18:02:18", evento: "06/08/2026 01:05:00" },
  "2696882168784883758": { odd: "1,71", status: /^Perdeu → L$/, stake: "700,00", data: "05/08/2026 17:18:25", evento: "06/08/2026 01:30:00" },
  "2696881722674520125": { odd: "3,02", status: /^Ganho → W/,   stake: "300,00", data: "05/08/2026 17:16:38", evento: "06/08/2026 02:30:00" },
  "2696880331386138910": { odd: "2,12", status: /^Ganho → W/,   stake: "500,00", data: "05/08/2026 17:10:58", evento: "06/08/2026 01:55:00" },
};

// Retorno que o card estampa em "Você ganhou" — a odd do W tem de explicá-lo até o centavo.
const RETORNO_CARD = { "2696881722674520125": 906.00, "2696880331386138910": 1060.00 };

// O bilheteode cashout ABERTO: `cashout_amount: "270"` com o card mostrando o botão
// "CASH OUT R$ 270,00". É OFERTA de venda antecipada, não cashout executado — se o bloco
// emitir "Cashout executado" aqui, vira vitória fantasma (a armadilha do `totalWin` da
// VaideBet, s210). Este caso trava que NÃO sai.
const ABERTO_COM_OFERTA_DE_CASHOUT = "2697202108746305608";

const PAGINA_FALSA = 3;   // o servidor do teste devolve no MÁXIMO 3, ignorando o `limit` pedido

export async function rodar() {
  const base = "https://api-32-sp-c7818b61-598.sptpub.com/api/v1/my_bets/list";
  const todos = JSON.parse(fixture("betboom.my_bets_all.json")).results;
  // ⚠ Corpo do 401 REUSADO da Jonbet, de propósito e declarado: é o mesmo motor BetBy, mas
  // na Betboom a 1ª chamada sem token NÃO foi capturada ao vivo (o gancho do recon entrou
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

  const alvo = `${base}?currency=BRL&lang=pt-BR&limit=15&skip=0&status=open&timestamp_from&timestamp_to`;
  const { ultima, urls } = await rodarInject({
    inject: "jb_inject.js",          // ← o MESMO da Jonbet, sem uma linha de diferença
    href: "https://betboom.bet.br/sport/bets",
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
  if (bilhetes.length !== 7) falhas.push(`esperava 7 bilhetes normalizados, vieram ${bilhetes.length}`);

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
    // A armadilha, dita em voz alta: perdida NUNCA pode sair com odd zerada.
    if (/Perdeu/.test(status) && /^0*(,0*)?$/.test(odd)) falhas.push(`${b.id}: odd zerada numa PERDIDA — leu total_k cru`);
    // O status cru precisa subir junto: é ele que a CASA_BETBOOM.md traduz.
    if (!linha(txt, "Status (API):")) falhas.push(`${b.id}: falta o status cru da API`);
    // Oferta de cashout em bilhete ABERTO não pode virar cashout executado.
    if (b.id === ABERTO_COM_OFERTA_DE_CASHOUT && /Cashout executado/.test(txt)) {
      falhas.push(`${b.id}: emitiu "Cashout executado" num bilhete ABERTO — é oferta de venda, não liquidação`);
    }
    // W: a odd tem de explicar o retorno do card até o centavo.
    const ret = RETORNO_CARD[b.id];
    if (ret != null) {
      const n = Number(odd.replace(",", "."));
      const st = Number(e.stake.replace(".", "").replace(",", "."));
      if (!(Math.abs(n * st - ret) <= 0.01)) falhas.push(`${b.id}: odd ${odd} × stake ${e.stake} não explica o retorno ${ret} do card`);
    }
  }
  if (servidas < 3) falhas.push(`o replay pediu só ${servidas} página(s) autenticada(s) — não varreu a lista`);
  // Prova que a guarda do token foi mesmo exercitada: se o 401 nunca chegou a ser servido, o
  // teste acima não significa nada (era o buraco da 1ª versão do caso da Jonbet).
  if (!negadas) falhas.push("o corpo 401 nunca foi servido — a guarda do token não foi exercitada");
  // E que o replay nunca repetiu a chamada sem token (seria 401 em loop na casa real).
  if (negadas > 1) falhas.push(`${negadas} requisições sem Bearer — o replay está repaginando sem token`);
  if (urls.length < 4) falhas.push(`replay não repaginou o bastante (só ${urls.length} requisição(ões) para 7 bilhetes em páginas de ${PAGINA_FALSA})`);
  return { falhas, testes };
}
