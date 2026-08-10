// Stake (stake.bet.br) — captura por API `POST /restapi/v1/betslip/history` (recon s257).
//
// A Stake roda KAMBI, o mesmo motor da KTO — provado pelo vocabulário, não pela aparência:
// a string `Total de Escanteio por Philadelphia Union` aparece LITERALMENTE nas duas
// fixtures, junto de `Resultado Final`, esportes em caixa alta e a paginação
// `range_start`/`range_size`. Mas ela NÃO expõe a Kambi: embrulha num REST próprio, com
// nomes snake_case, dinheiro em REAIS (não milésimos) e status em INTEIRO (não string).
// Por isso é casa espelho na LEITURA (`CASA_STAKE.md §9` copia o mapa da KTO) e casa nova
// na CAPTURA — o `kto_inject.js` é o molde, não o arquivo.
//
// Trava as 5 leituras que o recon custou, cada uma cruzada com o card renderizado:
//
//   • `bet_total_stake` vem 0 em TODA anulada — o valor real está em `bet_request_stake`
//     (bilhete 8360137: o campo diz 0, o card diz R$34,45). Mesma família do `betOdds:0`
//     da KTO. Quem ler o campo óbvio grava stake zero em 100% das anuladas.
//
//   • O DINHEIRO NÃO DISTINGUE ANULADA DE PERDIDA: as duas têm `bet_payout: 0`. A KTO
//     deriva o resultado do dinheiro (`_resultadoKTO`) porque lá isso é objetivo; aqui a
//     mesma heurística marcaria as 3 anuladas como L. **Na Stake o enum manda** — o
//     de-para vive em `CASA_STAKE.md §5`, e status desconhecido sobe cru.
//
//   • `bet_total_odds` é ARREDONDADA a 2 casas (`3.7` onde o real é 3,702056). A odd exata
//     é o produto das `bet_selection_odd`, e ela se prova contra o dinheiro até o centavo:
//     3,702056 × 150 = 555,3084 → pago 555,31 ✓. É a mesma conciliação do `_conciliaKTO`,
//     só que aqui a "declarada" é o produto das pernas, não um campo.
//
//   • Na PERDIDA `bet_potential_payout` também é 0 → a odd só pode sair do produto das
//     pernas. Não existe caminho pelo dinheiro.
//
//   • O ID que o card mostra é `internal_bet_id` (7 dígitos), NÃO `ticket_id` (11 dígitos).
//     Conferido abrindo o bilhete no site: o modal estampa `ID 8342050`, que é o
//     `internal_bet_id` do ticket 12980227100. Usar o ticket_id faria print e captura
//     gerarem códigos diferentes para o mesmo bilhete, e a dedup por código morreria.
//
// Data: `ticket_placed_date` é UTC com `+00:00` → America/Sao_Paulo (14:11 UTC = 11:11 no
// card). É a 1ª coluna do TSV; errar desloca tudo.
//
// NÃO COBERTO pela fixture (a conta só tem 17 bilhetes): simples (`bet_type` foi 1 nas 17),
// boost (`*_boosted` todos null), cashout liquidado (os campos `bet_cashout_*` só existem
// no endpoint de ABERTAS — que `bet_status` sobra depois de sacar é desconhecido), freebet,
// bet builder e eSports. Nada disso está travado aqui; quando aparecer, vira linha nova.
import { rodarInject, carregarContent, fixture, linha } from "../sandbox.mjs";

export const casa = "Stake";

// código (internal_bet_id) → o que o CARD da Stake mostra.
// stake = "Valor Total" · odd = "Probabilidades" (o card arredonda a 2 casas; aqui fica a
// exata, que é a que explica o "Pagamento" até o centavo) · data = cabeçalho do card.
const ESPERADO = {
  "8360137": { stake: "34,45",  odd: "3,15315",     status: /→ V$/,          tipo: /Múltipla \(3 seleções\)/, data: "09/08/2026 11:11:05" },
  "8360136": { stake: "265,55", odd: "3,15315",     status: /em aberto/,     tipo: /Múltipla \(3 seleções\)/, data: "09/08/2026 11:11:04" },
  "8360107": { stake: "100,19", odd: "3,808035",    status: /→ V$/,          tipo: /Múltipla \(3 seleções\)/, data: "09/08/2026 11:06:55" },
  "8360106": { stake: "199,81", odd: "3,808035",    status: /^Perdeu → L$/,  tipo: /Múltipla \(3 seleções\)/, data: "09/08/2026 11:06:55" },
  "8357256": { stake: "150,00", odd: "3,702056",    status: /^Ganho → W/,    tipo: /Múltipla \(3 seleções\)/, data: "08/08/2026 23:11:20" },
  "8357249": { stake: "200,00", odd: "2,82802",     status: /^Perdeu → L$/,  tipo: /Múltipla \(3 seleções\)/, data: "08/08/2026 23:10:49" },
  "8357246": { stake: "1,09",   odd: "13,6413635",  status: /→ V$/,          tipo: /Múltipla \(4 seleções\)/, data: "08/08/2026 23:10:16" },
  "8357245": { stake: "148,91", odd: "13,6413635",  status: /^Perdeu → L$/,  tipo: /Múltipla \(4 seleções\)/, data: "08/08/2026 23:10:16" },
  "8347538": { stake: "44,69",  odd: "2,0449",      status: /^Ganho → W/,    tipo: /Múltipla \(2 seleções\)/, data: "08/08/2026 13:02:19" },
  "8347537": { stake: "255,31", odd: "2,0449",      status: /^Ganho → W/,    tipo: /Múltipla \(2 seleções\)/, data: "08/08/2026 13:02:19" },
  "8342052": { stake: "250,00", odd: "5,07428064",  status: /^Ganho → W/,    tipo: /Múltipla \(4 seleções\)/, data: "07/08/2026 22:17:09" },
  "8342050": { stake: "18,88",  odd: "3,95076",     status: /^Perdeu → L$/,  tipo: /Múltipla \(3 seleções\)/, data: "07/08/2026 22:16:48" },
  "8342049": { stake: "281,12", odd: "3,95076",     status: /^Perdeu → L$/,  tipo: /Múltipla \(3 seleções\)/, data: "07/08/2026 22:16:48" },
  "8342041": { stake: "126,28", odd: "3,290192",    status: /^Perdeu → L$/,  tipo: /Múltipla \(3 seleções\)/, data: "07/08/2026 22:16:10" },
  "8342040": { stake: "273,72", odd: "3,290192",    status: /^Perdeu → L$/,  tipo: /Múltipla \(3 seleções\)/, data: "07/08/2026 22:16:09" },
  "8342033": { stake: "76,03",  odd: "7,605",       status: /^Perdeu → L$/,  tipo: /Múltipla \(3 seleções\)/, data: "07/08/2026 22:15:23" },
  "8342032": { stake: "73,97",  odd: "7,605",       status: /^Perdeu → L$/,  tipo: /Múltipla \(3 seleções\)/, data: "07/08/2026 22:15:22" },
};

// As 7 apostas que a Stake PARTIU em dois bilhetes: mesmas seleções, mesmo segundo, IDs
// distintos, stakes somando número redondo (a leitura mais provável é limitação de conta —
// parte aceita, resto devolvido). São bilhetes DIFERENTES e têm de sobreviver os dois: se
// alguma dedup por conteúdo entrar no caminho, metade do histórico do Feca some.
const GEMEOS = [
  ["8360137", "8360136", 300],   // 34,45 + 265,55 — a 2ª metade anulada
  ["8360107", "8360106", 300],   // 100,19 + 199,81
  ["8357246", "8357245", 150],   // 1,09 + 148,91
  ["8347538", "8347537", 300],   // 44,69 + 255,31 — as duas ganhas
  ["8342050", "8342049", 300],   // 18,88 + 281,12
  ["8342041", "8342040", 400],   // 126,28 + 273,72
  ["8342033", "8342032", 150],   // 76,03 + 73,97
];

export async function rodar() {
  const corpo = fixture("stake.betslip_all.json");
  const URL_LISTA = "https://web-api.stake.bet.br/restapi/v1/betslip/history";
  // O corpo REAL que a página envia. O `token` é de sessão e o replay tem de reaproveitá-lo:
  // sem ele a requisição volta vazia, e o inject não tem como inventá-lo.
  const corpoInicial = JSON.stringify({ token: "harness-token", range_start: 0, range_size: 10, status: 1 });

  const { ultima, urls } = await rodarInject({
    inject: "stk_inject.js",
    href: "https://stake.bet.br/esportes/home/my-bets?status=settled",
    urlInicial: URL_LISTA,
    optsInicial: {
      method: "POST",
      headers: { authorization: "Bearer harness", "content-type": "application/json" },
      body: corpoInicial,
    },
    pedido: "__sharpenupSTKReq",
    // A fixture responde `next_page_exists:false` → o replay encerra em 1 página por variante.
    responder: (url) => (String(url).includes("/restapi/v1/betslip/") ? corpo : null),
  });

  const falhas = [];
  if (!ultima) return { falhas: ["o inject não emitiu nenhuma mensagem"], testes: 0 };
  if (!ultima.hook) falhas.push("o inject não emitiu `hook:true` (autodiagnóstico cego)");
  if (typeof ultima.respostas !== "number" || ultima.respostas < 1) {
    falhas.push(`\`respostas\` ausente ou zerado (veio ${ultima.respostas})`);
  }
  if (!ultima.fim) falhas.push("o inject não sinalizou `fim` (o robô ficaria esperando o teto)");
  if (urls.length < 2) falhas.push(`replay não repaginou (só ${urls.length} requisição)`);

  const bilhetes = ultima.bilhetes || [];
  if (bilhetes.length !== 17) falhas.push(`esperava 17 bilhetes normalizados, vieram ${bilhetes.length}`);

  const porRef = new Map();
  const fmt = carregarContent().pegar("formatTicketSTK");
  let testes = 0;
  for (const b of bilhetes) {
    const e = ESPERADO[b.ref];
    if (!e) { falhas.push(`bilhete inesperado na fixture: ${b.ref}`); continue; }
    const txt = fmt(b);
    porRef.set(b.ref, txt);
    testes++;
    if (!txt.startsWith(`[Código: ${b.ref}]`)) falhas.push(`${b.ref}: marcador [Código:] ausente/errado`);
    const stake = linha(txt, "Stake:");
    const odd = linha(txt, "Odd:");
    const status = linha(txt, "Status:");
    const tipo = linha(txt, "Tipo:");
    const data = linha(txt, "Data (colocação):");
    if (stake !== e.stake) falhas.push(`${b.ref}: stake esperado ${e.stake}, veio "${stake}"`);
    if (odd !== e.odd) falhas.push(`${b.ref}: odd esperada ${e.odd}, veio "${odd}"`);
    if (!e.status.test(status)) falhas.push(`${b.ref}: status "${status}"`);
    if (!e.tipo.test(tipo)) falhas.push(`${b.ref}: tipo "${tipo}"`);
    if (data !== e.data) falhas.push(`${b.ref}: data esperada ${e.data}, veio "${data}"`);
    // O status CRU da API tem de subir junto: é ele que a CASA_STAKE.md traduz, e é o que
    // permite reconhecer um enum novo (cashout, meio-ganho) em vez de chutá-lo pelo dinheiro.
    if (!linha(txt, "Status (API):")) falhas.push(`${b.ref}: linha "Status (API):" ausente`);
  }

  // As gêmeas: os dois lados existem, com códigos distintos, e as stakes somam o redondo.
  const num = (s) => Number(String(s).replace(/\./g, "").replace(",", ".")) || 0;
  for (const [a, z, soma] of GEMEOS) {
    if (!porRef.has(a) || !porRef.has(z)) { falhas.push(`gêmeas ${a}+${z}: um dos lados sumiu`); continue; }
    const s = num(linha(porRef.get(a), "Stake:")) + num(linha(porRef.get(z), "Stake:"));
    if (Math.abs(s - soma) > 0.005) falhas.push(`gêmeas ${a}+${z}: stakes somam ${s.toFixed(2)}, esperado ${soma}`);
  }

  // Anulada NÃO pode virar L. É a armadilha nº 2 e ela só aparece se alguém derivar o
  // resultado do dinheiro (payout 0 nas duas).
  for (const ref of ["8360137", "8360107", "8357246"]) {
    const txt = porRef.get(ref);
    if (txt && /Perdeu/.test(linha(txt, "Status:"))) {
      falhas.push(`${ref}: anulada lida como perdida — o dinheiro não distingue as duas na Stake`);
    }
  }

  return { falhas, testes };
}
