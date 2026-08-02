// BetNacional — captura por API `/api/v2/all-bets` (s227).
//
// Trava as leituras que o recon cruzou entre o JSON e o card renderizado da casa:
//   • `bets[]` é lista de PERNAS, não de bilhetes: o agrupamento é por `ticket_id`
//     (o "ID da aposta" do card, `NXBNAC…`) — múltipla de 4 = 4 objetos no array.
//   • dinheiro vem em STRING com ponto decimal em reais ("150.00") — não é milésimo.
//   • `header_return` de bilhete PENDENTE é retorno POTENCIAL (card "Retorno R$ 135,00"
//     com o jogo ainda por começar) — nunca pode virar ganho (armadilha VaideBet).
//   • `total_odd` vem arredondada em 3 casas (18.795; o card mostra 18.80): no W a odd
//     verdadeira sai de retorno ÷ stake quando a declarada não explica o retorno até o
//     centavo (828,75 ÷ 200 = 4,14375 ≠ 4,144 × 200 = 828,80).
//   • `created_at` já vem em horário LOCAL (sem Z): "2026-08-01 15:40:08" = card
//     "01/08/2026, às 15h40" — converter de UTC aqui PULARIA a hora.
//   • Super Odds (`is_super_odds`): home/away vazios e a descrição vive em market_name.
import { rodarInject, carregarContent, fixture, linha } from "../sandbox.mjs";

export const casa = "BETNACIONAL";

const ESPERADO = {
  "NXBNAC000142211281784902500857": { odd: "7,6",     status: /^Perdeu → L$/, tipo: /Múltipla \(4 seleções\)/, data: "24/07/2026 11:15:09" },
  "NXBNAC000142211281784913861336": { odd: "2,4",     status: /^Perdeu → L$/, tipo: /Simples/,                 data: "24/07/2026 14:24:21", boost: /Super Odds/ },
  "NXBNAC000142211281784913943635": { odd: "2",       status: /^Ganhou → W/,  tipo: /Simples/,                 data: "24/07/2026 14:25:44" },
  "NXBNAC000142211281785345269551": { odd: "1,857",   status: /^Ganhou → W/,  tipo: /Múltipla \(2 seleções\)/, data: "29/07/2026 14:14:30" },
  "NXBNAC000142211281785507470810": { odd: "4,14375", status: /^Ganhou → W/,  tipo: /Múltipla \(3 seleções\)/, data: "31/07/2026 11:17:51" },
  "NXBNAC000142211281785523440772": { odd: "1,727",   status: /^Perdeu → L$/, tipo: /Simples/,                 data: "31/07/2026 15:44:01" },
  "NXBNAC000142211281785595145532": { odd: "60,48",   status: /em aberto/,    tipo: /Múltipla \(3 seleções\)/, data: "01/08/2026 11:39:06", potencial: "R$ 3628,80" },
  "NXBNAC000142211281785609607878": { odd: "2,7",     status: /em aberto/,    tipo: /Simples/,                 data: "01/08/2026 15:40:08", boost: /Super Odds/, potencial: "R$ 135,00" },
};

export async function rodar() {
  const corpo = fixture("betnacional.all-bets.json");
  const base = "https://prod-betnacional-bets.bet6.com.br/api/v2/all-bets";

  const { ultima, urls } = await rodarInject({
    inject: "bnc_inject.js",
    href: "https://betnacional.bet.br/perfil/minhas-apostas",
    urlInicial: `${base}?status=all&paginationDirection=next&limit=20&date_start=2026-07-25&date_end=2026-08-01&startDate=2026-07-25&endDate=2026-08-01`,
    pedido: "__sharpenupBNCReq",
    // A fixture responde a MESMA janela para qualquer data → o replay tem de parar
    // sozinho pela regra "janelas seguidas sem bilhete novo" (anti-loop), não por teto.
    responder: (url) => (url.includes("/api/v2/all-bets") ? corpo : null),
    ms: 800,
  });

  const falhas = [];
  if (!ultima) return { falhas: ["o inject não emitiu nenhuma mensagem"], testes: 0 };
  if (!ultima.hook) falhas.push("mensagem sem hook:true (autodiagnóstico cego)");
  if (!ultima.fim) falhas.push("o inject não sinalizou `fim` (o robô ficaria esperando o teto)");
  if (urls.length < 2) falhas.push(`replay não varreu janelas para trás (só ${urls.length} requisição)`);

  const tickets = ultima.tickets || [];
  if (tickets.length !== 24) falhas.push(`esperava 24 bilhetes agrupados (52 pernas), vieram ${tickets.length}`);
  const m4 = tickets.find((t) => t.codigo === "NXBNAC000142211281784902500857");
  if (m4 && (m4.pernas || []).length !== 4) falhas.push(`múltipla de 4 agrupou ${(m4.pernas || []).length} perna(s)`);

  const fmt = carregarContent().pegar("formatTicketBNC");
  let testes = 0;
  for (const t of tickets) {
    const e = ESPERADO[t.codigo];
    if (!e) continue;                       // a fixture tem 24; travamos os 8 conferidos no card
    const txt = fmt(t);
    testes++;
    if (!txt.startsWith(`[Código: ${t.codigo}]`)) falhas.push(`${t.codigo}: marcador [Código:] ausente/errado`);
    const odd = linha(txt, "Odd:");
    const status = linha(txt, "Status:");
    const tipo = linha(txt, "Tipo:");
    const data = linha(txt, "Data (colocação):");
    if (odd !== e.odd) falhas.push(`${t.codigo}: odd esperada ${e.odd}, veio "${odd}"`);
    if (!e.status.test(status)) falhas.push(`${t.codigo}: status "${status}"`);
    if (!e.tipo.test(tipo)) falhas.push(`${t.codigo}: tipo "${tipo}"`);
    if (data !== e.data) falhas.push(`${t.codigo}: data esperada ${e.data}, veio "${data}"`);
    const pot = linha(txt, "Retorno potencial:");
    if (e.potencial) {
      if (pot !== e.potencial) falhas.push(`${t.codigo}: retorno potencial esperado ${e.potencial}, veio "${pot}"`);
      if (/^Retorno:/m.test(txt)) falhas.push(`${t.codigo}: bilhete ABERTO com linha "Retorno:" seca (viraria ganho fantasma)`);
    } else if (pot) {
      falhas.push(`${t.codigo}: bilhete resolvido com "Retorno potencial:" (só aberta leva)`);
    }
    const boost = linha(txt, "Boost:");
    if (e.boost && !e.boost.test(boost)) falhas.push(`${t.codigo}: boost esperado, veio "${boost}"`);
    if (!e.boost && boost) falhas.push(`${t.codigo}: boost inesperado "${boost}"`);
  }
  if (testes !== Object.keys(ESPERADO).length)
    falhas.push(`só ${testes} dos ${Object.keys(ESPERADO).length} bilhetes do gabarito apareceram`);

  // "Cancelado" = void com devolução integral — confirmado ao vivo (s228): card "Cancelada",
  // Aposta R$ 25,00 = Ganho R$ 25,00 (NXBNAC…459206253). A fixture não tem o payload cru
  // desse bilhete (capturado só formatado), então o teste alimenta o formatador com o
  // OBJETO AGRUPADO que o inject emite — os valores vêm do card real; `statusId: 2` é o
  // único campo não confirmado (o formatador decide pelo NOME, não pelo id).
  const cancelada = {
    codigo: "NXBNAC000142211281783459206253", statusId: 2, statusNome: "Cancelado",
    resultado: 1, stake: 25, retorno: 25, oddTotal: 26, tipoNome: "Simples",
    colocada: "2026-07-07 18:20:06", pagaEm: "2026-07-07 19:03:34",
    superOdds: true, outright: false,
    pernas: [{ idx: 1, mercado: "Melhor Marcador de Cada Seleção - Vini Jr (Brasil), Messi (Argentina), Mbappé (França) e Harry Kane (Inglaterra)", selecao: "Sim", specifier: "", odd: 26, resultadoPerna: 2, casa: "", fora: "", esporte: "Futebol", liga: "Copa do Mundo FIFA", inicio: "2026-06-11 16:00:00" }],
  };
  const txtCanc = fmt(cancelada);
  testes++;
  const stCanc = linha(txtCanc, "Status:");
  if (!/Cancelada\/void \(retorno = stake\) → V$/.test(stCanc))
    falhas.push(`cancelada: esperava void → V, veio "${stCanc}"`);
  if (linha(txtCanc, "Odd:") !== "26")
    falhas.push(`cancelada: void exibe a odd do bilhete (26), veio "${linha(txtCanc, "Odd:")}"`);
  // Cancelado SEM devolução integral não pode virar V no chute — segue "a conferir".
  const stMeia = linha(fmt({ ...cancelada, retorno: 12.5 }), "Status:");
  if (!/a conferir — não liquidar automaticamente/.test(stMeia))
    falhas.push(`cancelada sem devolução integral: esperava "a conferir", veio "${stMeia}"`);

  return { falhas, testes };
}
