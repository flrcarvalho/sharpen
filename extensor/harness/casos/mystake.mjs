// MyStake (BetConstruct / sportsbook v4) — 4ª casa do MESMO motor, espelho de Tivo/Betfast/Faz1bet (s392).
//
// A MyStake (`mystake.bet`, sportsbook em `/br/sportsbook/mybets`) roda o mesmo motor no mesmo
// caminho de API (`POST /api/game/p/messagetosport` com `{name:"gethistory"}`), então reusa o
// `tv_inject.js` e o `formatTicketTV`. Fontes públicas atribuíam o sportsbook dela à Upgaming
// (rede Santeda): o F12 desmentiu. Vale o tráfego, não a review.
//
// ── O motor foi PROVADO no tráfego real, logado (03/10/2026) ─────────────────────────────
//   • o pedido é o mesmo das outras três: `{"name":"gethistory","message":"{\"countOnly\":false,
//     \"language\":33,\"from\":\"\",\"to\":\"\"}"}`, iniciado por `helpers.js?v=2.4.0`;
//   • a resposta é `{Error, Tickets, Count}` com o MESMO conjunto de chaves das fixtures
//     tivo/betfast/faz1bet; `Company: 28` é o id da casa dentro do motor (Tivo 291, Betfast 99,
//     Faz1bet 223);
//   • a mesma URL serve polling de 0,7 kB a cada ~5 s — o inject já decide pela FORMA da
//     resposta (`Tickets` em array), então o polling não entra.
//
// ── O que SÓ esta amostra trouxe (9 bilhetes reais, 9 perdidas, todas múltiplas de 3) ─────
//   • `TicketType: 3` = FREEBET. Bilhete 306558902, badge "F" vermelho ao lado do stake no
//     card; confirmado pelo dono ("usei dinheiro de freebet nessa aposta"). Até aqui o inject
//     DESCARTAVA o campo e as 83 apostas das outras três fixtures tinham `0`. O par de controle
//     é o 306558885: mesmas três pernas, mesmo `Koef` 29,7667, `TicketType 0` — tem de sair
//     SEM a marca. O bloco usa o rótulo que a Superbet já emite (`Freebet incluído:`), para a
//     regra global de freebet (etapa 2, decisão do Feca em 03/10/2026: dinheiro da casa,
//     perda = 0) ter UM rótulo só para ler. Este caso NÃO trava P/L: só a marca no bloco.
//   • `Items[].Result 6` = MEIA DERROTA. Duas pernas de handicap asiático partido, conferidas
//     contra a tela e contra o placar:
//        Macclesfield × Scarborough 2:2, fora −0,25  → metade perde, metade devolve
//        Dorking × Chatam 1:0,          fora +0,75  → metade perde, metade devolve
//     A tela pinta as duas de VERMELHO, igual à derrota cheia; só a API distingue. O P/L vem
//     do bilhete (`Result 3`), então isto mexe só na descrição da perna.
//   • `Items[].Result 1` = anulada/devolvida aparece de novo (Macclesfield, handicap 0, 2:2),
//     agora com a perna AMARELA no card — a mesma leitura que a Betfast provou pelo dinheiro.
//
// ── O que esta amostra NÃO cobre ─────────────────────────────────────────────────────────
//   Aberta, ganha (W), simples, sistema, cashout, `ItemType 6` e FREEBET GANHA (o dono diz que a
//   casa paga só o lucro; sem payload para conferir o `WinAmount`). Aberta/ganha/ItemType 6 já
//   estão travados pelos casos da Faz1bet e da Betfast, que exercitam o mesmo código.
//   O sinal do handicap com `hisminus:true` (a tela mostra `2 (0.75)` para `h:-0.75`) NÃO é
//   travado aqui: é defeito da família inteira e tem pacote próprio (BACKLOG).
//
// ── Como os valores abaixo foram obtidos ─────────────────────────────────────────────────
// Print da tela "Minhas Apostas" de 03/10/2026 (colunas `Status · ID · Data · Tipo · Valor
// Apostado · Probabilidades · Quantia`) e o detalhe aberto dos bilhetes 306558758 e 306558902.
// Os minutos da colocação vêm do card; os segundos e a odd inteira vêm do payload, que é o que
// o card arredonda. `tela` guarda a odd QUE A CASA MOSTRA — a prova do truncamento.
import { rodarInject, carregarContent, fixture, linha } from "../sandbox.mjs";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";

export const casa = "MyStake";

const HREF = "https://mystake.bet/br/sportsbook/mybets";
const API = "https://mystake.bet/api/game/p/messagetosport";

// Todas perdidas (`Status 10 · Result 3`, "Quantia 0.00" no card) e todas "Expresso" de 3 pernas.
// A colocação é 02/10 à noite e o jogo é 03/10 em TODAS: a coluna Data do TSV é a do evento.
const ESPERADO = {
  "306558902": { data: "02/10/2026 23:11:27", evento: "03/10/2026 12:00:00", odd: "29,7667", tela: "29.76", stake: "45,00",  freebet: "45,00" },
  "306558885": { data: "02/10/2026 23:10:54", evento: "03/10/2026 12:00:00", odd: "29,7667", tela: "29.76", stake: "70,00" },
  "306558758": { data: "02/10/2026 23:08:02", evento: "03/10/2026 11:00:00", odd: "39,1813", tela: "39.18", stake: "100,00" },
  "306558711": { data: "02/10/2026 23:06:34", evento: "03/10/2026 18:30:00", odd: "8,0604",  tela: "8.06",  stake: "100,00" },
  "306558636": { data: "02/10/2026 23:04:52", evento: "03/10/2026 21:00:00", odd: "22,7136", tela: "22.71", stake: "100,00" },
  "306558529": { data: "02/10/2026 23:03:08", evento: "03/10/2026 21:00:00", odd: "10,5743", tela: "10.57", stake: "100,00" },
  "306558418": { data: "02/10/2026 23:00:47", evento: "03/10/2026 17:00:00", odd: "12,288",  tela: "12.28", stake: "100,00" },
  "306558357": { data: "02/10/2026 22:58:56", evento: "03/10/2026 22:30:00", odd: "14,6475", tela: "14.64", stake: "100,00" },
  "306558258": { data: "02/10/2026 22:56:36", evento: "03/10/2026 18:30:00", odd: "12,235",  tela: "12.23", stake: "100,00" },
};

// Pernas conferidas contra a tela: cor do card + placar. `trecho` identifica a linha da perna
// no bloco; `marca` é o que tem de aparecer entre colchetes no fim dela.
const PERNAS = [
  { bilhete: "306558636", trecho: "Macclesfield FC - Scarborough Athletic", marca: "[meia derrota]" },
  { bilhete: "306558758", trecho: "Dorking Wanderers - Chatam Town",       marca: "[meia derrota]" },
  { bilhete: "306558758", trecho: "Macclesfield FC - Scarborough Athletic", marca: "[anulada/devolvida]" },
];

// A linha "- mercado: seleção [marca]" vem ANTES da linha "    Jogo: A - B · …" da mesma perna.
function marcaDaPerna(txt, jogo) {
  const ls = txt.split("\n");
  const i = ls.findIndex((l) => l.includes("Jogo: " + jogo));
  if (i < 1) return null;
  const m = ls[i - 1].match(/\[[^\]]*\]\s*$/);
  return m ? m[0] : ls[i - 1];
}

export async function rodar() {
  const corpo = fixture("mystake.gethistory.json");
  const falhas = [];
  let testes = 0;

  // ── 0. A fixture é dado real de cliente: não pode carregar o e-mail da conta ─────────
  testes++;
  const cru = readFileSync(fileURLToPath(new URL("../fixtures/mystake.gethistory.json", import.meta.url)), "utf8");
  if (cru.includes("@")) falhas.push("a fixture da MyStake carrega um e-mail (Player.Name) — apague antes de versionar");

  const { ultima } = await rodarInject({
    inject: "tv_inject.js",
    href: HREF,
    urlInicial: API,
    pedido: "__sharpenupTVReq",
    responder: (url) => (url.includes("messagetosport") ? corpo : null),
  });

  if (!ultima) return { falhas: ["o inject não emitiu nenhuma mensagem"], testes };

  // ── 1. O espelho funciona a partir do host da MyStake ────────────────────────────────
  testes++;
  if (!ultima.hook) falhas.push("o inject não sinalizou `hook` rodando em mystake.bet");
  testes++;
  if (!ultima.fim) falhas.push("o inject não sinalizou `fim` (o robô ficaria esperando o teto)");

  const tickets = ultima.tickets || [];
  testes++;
  if (tickets.length !== 9) falhas.push(`esperava 9 bilhetes na fixture, vieram ${tickets.length}`);

  // `Count: 9` está longe do `TETO_ALERTA` (50): a varredura retroativa não pode acordar.
  testes++;
  if (ultima.tetoSuspeito) falhas.push("`tetoSuspeito` ligado com Count:9 — a consulta não encheu");

  const fmt = carregarContent().pegar("formatTicketTV");
  const porId = new Map(tickets.map((t) => [String(t.id), t]));

  // ── 2. Os 9 bilhetes conferidos contra o card ────────────────────────────────────────
  for (const [id, e] of Object.entries(ESPERADO)) {
    const t = porId.get(id);
    if (!t) { falhas.push(`${id}: não veio na captura`); continue; }
    const txt = fmt(t);
    testes++;

    if (!txt.startsWith(`[Código: ${id}]`)) falhas.push(`${id}: marcador [Código:] ausente/errado`);

    const evento = linha(txt, "Data (evento mais recente):");
    if (evento !== e.evento) falhas.push(`${id}: data do EVENTO esperada ${e.evento}, veio "${evento}" (é ela que vai para a coluna Data do TSV)`);

    const data = linha(txt, "Data (colocação):");
    if (data !== e.data) falhas.push(`${id}: colocação esperada ${e.data}, veio "${data}"`);

    const stake = linha(txt, "Stake:");
    if (stake !== `R$ ${e.stake}`) falhas.push(`${id}: stake esperada R$ ${e.stake}, veio "${stake}"`);

    const odd = linha(txt, "Odd:");
    if (odd !== e.odd) falhas.push(`${id}: odd esperada ${e.odd}, veio "${odd}" (a tela mostra ${e.tela} — trunca; vale o Koef inteiro)`);

    const tipo = linha(txt, "Tipo:");
    if (tipo !== "Múltipla (3 seleções)") falhas.push(`${id}: tipo esperado "Múltipla (3 seleções)", veio "${tipo}"`);

    const status = linha(txt, "Status:");
    if (!/^Perdeu → L/.test(status || "")) falhas.push(`${id}: status "${status}"`);

    // ── 3. Freebet: marca SÓ onde a casa marcou ─────────────────────────────────────────
    testes++;
    const fb = linha(txt, "Freebet incluído:");
    if (e.freebet) {
      if (fb !== `${e.freebet} (dinheiro real = stake − freebet)`) {
        falhas.push(`${id}: bilhete de FREEBET (TicketType 3, badge "F" no card) saiu sem a marca — veio "${fb}". ` +
                    `Sem ela a regra global trataria R$ ${e.freebet} da casa como dinheiro do apostador`);
      }
    } else if (fb) {   // `linha()` devolve "" quando o rótulo não existe
      falhas.push(`${id}: bilhete com TicketType 0 saiu marcado como freebet ("${fb}")`);
    }
  }

  // ── 4. O resultado POR PERNA que só a API distingue ──────────────────────────────────
  for (const p of PERNAS) {
    const t = porId.get(p.bilhete);
    if (!t) continue;
    testes++;
    const m = marcaDaPerna(fmt(t), p.trecho);
    if (m !== p.marca) {
      falhas.push(`${p.bilhete} / ${p.trecho}: perna esperada ${p.marca}, veio "${m}"`);
    }
  }

  // ── 5. O bloco da MyStake é IDÊNTICO ao da Tivo ──────────────────────────────────────
  // A mesma fixture, rodada por outro host, tem de render bloco byte a byte igual. Se alguém
  // amarrar o inject a um domínio, ou ramificar o formatador por casa, fica vermelho.
  const r = await rodarInject({
    inject: "tv_inject.js",
    href: "https://tivo.bet.br/br/sportsbook/prematch#/mybets",
    urlInicial: "https://tivo.bet.br/api/game/p/messagetosport",
    pedido: "__sharpenupTVReq",
    responder: (url) => (url.includes("messagetosport") ? corpo : null),
  });
  const m = new Map((((r.ultima || {}).tickets) || []).map((t) => [String(t.id), t]));
  testes++;
  const diferentes = [...porId].filter(([id, t]) => !m.get(id) || fmt(m.get(id)) !== fmt(t)).map(([id]) => id);
  if (m.size !== porId.size || diferentes.length) {
    falhas.push(`espelho: ${diferentes.length} bloco(s) diferem entre mystake.bet e tivo.bet.br (${diferentes.slice(0, 3).join(", ")})`);
  }

  return { falhas, testes };
}
