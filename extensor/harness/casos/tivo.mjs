// Tivo (BetConstruct / sportsbook v4) — captura por API `POST /api/game/p/messagetosport`
// com `{name:"gethistory"}` (s196).
//
// Trava o que o reconhecimento provou ao vivo, cruzando o JSON com o que a própria lista
// "Minhas apostas" renderiza:
//   • ODD: a TELA TRUNCA em 2 casas (floor, não arredonda) — 208.4854 aparece como "208.48"
//     e 16.047 como "16.04". A odd que vale é `Koef`, com precisão completa (regra primordial
//     do projeto: odd nunca truncada). Confere: Koef == produto exato das pernas, e
//     `Koef × Amount` explica o `WinAmount` até o centavo (12,4231 × 150 = 1.863,46).
//   • DATA: `ActionTime` é epoch em MILISSEGUNDOS UTC → America/Sao_Paulo. Sem converter, o
//     bilhete pula de dia: 1784998806840 = 17:00:06Z = 14:00 BRT, que é o que o card mostra.
//   • ABERTA: `Status:5` + `Result:0`; o retorno é `PossibleWin` (POTENCIAL, nunca "retorno").
//     Nesse bilhete `WinKoef` vem null e `WinAmount` vem 0.0 — nenhum dos dois pode virar odd.
//   • OUTRIGHT (F1): `Game` é null; a seleção vive em `OutrightGame.Team1.Name` + `Outright`,
//     e o `Market.Name` é lixo interno ("Free text multiwinner market").
//   • `CalculatedBetAmount` NÃO é stake — é o rateio da stake por perna. Stake é `Amount`.
//   • `Team1Score`/`Team2Score` NÃO são placar — são a estatística do mercado (9 escanteios).
//     O placar é `LiveScore` ("4:2").
//
// FONTE DA ODD = `Koef`, SEMPRE. No 298394294 (outright de F1) a tela mostra "4.34" e o
// `Koef` diz 4.35 — única divergência em 21 bilhetes. Fica com o `Koef`: é o campo
// estrutural (== produto das pernas, e explica o WinAmount ao centavo nas ganhas), enquanto
// a tela é superfície derivada e truncada. O bilhete é L, então não há retorno para
// desempatar e o P/L é −stake de qualquer jeito: a diferença de 0,01 não toca em nada.
import { rodarInject, carregarContent, fixture, linha } from "../sandbox.mjs";

export const casa = "Tivo";

// `data` = ActionTime (COLOCAÇÃO, UTC→BRT), que é o que o card mostra na coluna "Data".
// `evento` = StartTime da perna mais recente — é ESTA que vai para a 1ª coluna do TSV
// (`MASTER_OUTPUT §4`: "em apostas múltiplas: usar a data da perna mais recente").
// Os dois bilhetes marcados como DIA DIFERENTE são a prova de que a colocação não pode virar
// a coluna Data: sem essa distinção, os dois entrariam na planilha no dia errado.
// Odd = Koef com precisão completa · tipo pelo nº de pernas.
const ESPERADO = {
  "298710215": { data: "25/07/2026 14:00:06", evento: "25/07/2026 20:30:00", odd: "354,1322", status: /^Perdeu → L/, tipo: /Múltipla \(6 seleções\)/ },
  "298692618": { data: "25/07/2026 11:24:48", evento: "25/07/2026 23:30:00", odd: "19,7781",  status: /em aberto/,   tipo: /Múltipla \(4 seleções\)/ },
  "298577562": { data: "24/07/2026 09:15:37", evento: "24/07/2026 21:30:00", odd: "16,0528",  status: /^Perdeu → L/, tipo: /Múltipla \(4 seleções\)/ },
  "298504219": { data: "23/07/2026 13:25:17", evento: "23/07/2026 21:30:00", odd: "11,5005",  status: /^Ganho → W/,  tipo: /Múltipla \(3 seleções\)/ },
  "298490076": { data: "23/07/2026 10:57:41", evento: "23/07/2026 21:30:00", odd: "60,8022",  status: /^Perdeu → L/, tipo: /Múltipla \(5 seleções\)/ },
  // DIA DIFERENTE — outright de F1: colocado 22/07, evento 25/07. A tela mostra 4.34; vale o Koef.
  "298394294": { data: "22/07/2026 10:18:44", evento: "25/07/2026 11:00:00", odd: "4,35",     status: /^Perdeu → L/, tipo: /Simples/ },
  "298391760": { data: "22/07/2026 09:45:47", evento: "22/07/2026 21:30:00", odd: "208,4854", status: /^Perdeu → L/, tipo: /Múltipla \(6 seleções\)/ },
  "297823698": { data: "16/07/2026 11:06:41", evento: "16/07/2026 21:30:00", odd: "12,4231",  status: /^Ganho → W/,  tipo: /Múltipla \(4 seleções\)/ },
  "293195339": { data: "04/06/2026 04:41:18", evento: "04/06/2026 05:04:00", odd: "1,75",     status: /^Ganho → W/,  tipo: /Simples/ },
  "291953402": { data: "24/05/2026 12:02:19", evento: "24/05/2026 18:30:00", odd: "4,5326",   status: /^Perdeu → L/, tipo: /Múltipla \(2 seleções\)/ },
  "291794373": { data: "23/05/2026 11:17:53", evento: "23/05/2026 19:00:00", odd: "40,7785",  status: /^Perdeu → L/, tipo: /Múltipla \(5 seleções\)/ },
  "291794327": { data: "23/05/2026 11:17:34", evento: "23/05/2026 16:00:00", odd: "6,7317",   status: /^Perdeu → L/, tipo: /Múltipla \(3 seleções\)/ },
  "291794114": { data: "23/05/2026 11:16:11", evento: "23/05/2026 21:30:00", odd: "21,2454",  status: /^Perdeu → L/, tipo: /Múltipla \(4 seleções\)/ },
  "291793688": { data: "23/05/2026 11:12:40", evento: "23/05/2026 20:30:00", odd: "18,7072",  status: /^Perdeu → L/, tipo: /Múltipla \(4 seleções\)/ },
  "291561212": { data: "21/05/2026 13:57:59", evento: "21/05/2026 21:00:00", odd: "16,047",   status: /^Perdeu → L/, tipo: /Múltipla \(4 seleções\)/ },
  "291561114": { data: "21/05/2026 13:57:18", evento: "21/05/2026 19:00:00", odd: "14,7612",  status: /^Perdeu → L/, tipo: /Múltipla \(4 seleções\)/ },
  "291560643": { data: "21/05/2026 13:53:52", evento: "21/05/2026 21:30:00", odd: "32,7499",  status: /^Perdeu → L/, tipo: /Múltipla \(4 seleções\)/ },
  // DIA DIFERENTE — tênis de Roland Garros: colocado 17/05, primeiro jogo só em 18/05.
  "291122540": { data: "17/05/2026 14:12:16", evento: "18/05/2026 10:15:00", odd: "1,6864",   status: /^Perdeu → L/, tipo: /Múltipla \(2 seleções\)/ },
  "291116286": { data: "17/05/2026 13:44:27", evento: "17/05/2026 15:45:00", odd: "8,775",    status: /^Perdeu → L/, tipo: /Múltipla \(3 seleções\)/ },
  "291115928": { data: "17/05/2026 13:42:47", evento: "17/05/2026 16:15:00", odd: "14,3052",  status: /^Perdeu → L/, tipo: /Múltipla \(3 seleções\)/ },
  "291115799": { data: "17/05/2026 13:42:05", evento: "17/05/2026 19:00:00", odd: "11,9175",  status: /^Perdeu → L/, tipo: /Múltipla \(3 seleções\)/ },
};

export async function rodar() {
  const corpo = fixture("tivo.gethistory.json");

  const { ultima } = await rodarInject({
    inject: "tv_inject.js",
    href: "https://tivo.bet.br/br/sportsbook/prematch#/mybets",
    urlInicial: "https://tivo.bet.br/api/game/p/messagetosport",
    pedido: "__sharpenupTVReq",
    // Uma única chamada traz a conta inteira (`Count` == Tickets.length): não há paginação.
    responder: (url) => (url.includes("messagetosport") ? corpo : null),
  });

  const falhas = [];
  if (!ultima) return { falhas: ["o inject não emitiu nenhuma mensagem"], testes: 0 };
  if (!ultima.hook) falhas.push("o inject não sinalizou `hook` (injeção não reportada)");
  if (!ultima.fim) falhas.push("o inject não sinalizou `fim` (o robô ficaria esperando o teto)");

  const tickets = ultima.tickets || [];
  if (tickets.length !== 24) falhas.push(`esperava 24 bilhetes na fixture, vieram ${tickets.length}`);

  const fmt = carregarContent().pegar("formatTicketTV");
  let testes = 0;
  for (const t of tickets) {
    const id = String(t.id);
    const e = ESPERADO[id];
    // Os 3 bilhetes mais antigos ficaram abaixo do corte do print; entram na contagem, mas
    // não têm leitura de tela para travar valor a valor.
    if (!e) continue;
    const txt = fmt(t);
    testes++;

    if (!txt.startsWith(`[Código: ${id}]`)) falhas.push(`${id}: marcador [Código:] ausente/errado`);

    const evento = linha(txt, "Data (evento mais recente):");
    if (evento !== e.evento) falhas.push(`${id}: data do EVENTO esperada ${e.evento}, veio "${evento}" (é ela que vai para a coluna Data do TSV)`);

    const data = linha(txt, "Data (colocação):");
    if (data !== e.data) falhas.push(`${id}: data de colocação esperada ${e.data}, veio "${data}"`);

    const status = linha(txt, "Status:");
    if (!e.status.test(status)) falhas.push(`${id}: status "${status}"`);

    const tipo = linha(txt, "Tipo:");
    if (!e.tipo.test(tipo)) falhas.push(`${id}: tipo "${tipo}"`);

    if (e.odd != null) {
      const odd = linha(txt, "Odd:").split(" ")[0];
      if (odd !== e.odd) falhas.push(`${id}: odd esperada ${e.odd}, veio "${odd}" (a tela trunca; vale o Koef inteiro)`);
    }
  }

  // ── Esqueleto: bilhete que volta só com o identificador (s198) ─────────────────
  // Aconteceu ao vivo em 3 dos 25 bilhetes do lote de 26/07 — os MESMOS IDs que vêm
  // cheios nesta fixture. Como um esqueleto não parece "aberto" (status undefined), a
  // regra resolvida-vence-aberta não o substituía: quem chegasse PRIMEIRO ganhava, e o
  // bilhete cheio era descartado em silêncio. Aqui os dois vêm na mesma resposta, um com
  // o esqueleto ANTES e outro com o esqueleto DEPOIS — as duas ordens têm de sobreviver.
  const bruto = JSON.parse(corpo);
  const cheio = (id) => bruto.Tickets.find((t) => String(t.ID) === id);
  const A = cheio("291115424"), B = cheio("291115639");
  // Sem `Count` de propósito: o fim autoritativo (`Error:null` + sem Count) segue valendo.
  const misturado = JSON.stringify({ Error: null, Tickets: [{ ID: A.ID }, A, B, { ID: B.ID }] });

  const r2 = await rodarInject({
    inject: "tv_inject.js",
    href: "https://tivo.bet.br/br/sportsbook/prematch#/mybets",
    urlInicial: "https://tivo.bet.br/api/game/p/messagetosport",
    pedido: "__sharpenupTVReq",
    responder: (url) => (url.includes("messagetosport") ? misturado : null),
  });
  const t2 = (r2.ultima && r2.ultima.tickets) || [];
  testes++;
  if (t2.length !== 2) {
    falhas.push(`esqueleto: esperava 2 bilhetes (um por ID), vieram ${t2.length}`);
  } else {
    for (const t of t2) {
      testes++;
      if (!(t.itens || []).length || t.status == null) {
        falhas.push(`esqueleto: o bilhete ${t.id} ficou VAZIO — o esqueleto venceu o bilhete cheio`);
      }
    }
  }

  // Esqueleto SOZINHO (nenhuma versão cheia): tem de subir NOMEADO, mantendo o marcador
  // [Código:] — é por ele que a conferência de cobertura cobra o bilhete e manda recapturar.
  // O que não pode é virar bloco mudo, que a IA tentava adivinhar.
  testes++;
  const so = fmt({ id: "291115424" });
  if (!so.startsWith("[Código: 291115424]")) falhas.push("esqueleto sozinho: perdeu o marcador [Código:]");
  if (!/SEM DETALHE/.test(so)) falhas.push("esqueleto sozinho: subiu sem o aviso SEM DETALHE");
  if (/Status \(API\)|Stake:|Odd:/.test(so)) falhas.push("esqueleto sozinho: emitiu campo que não existe no dado");

  return { falhas, testes };
}
