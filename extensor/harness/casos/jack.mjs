// Jack (jack.com) — 5ª casa BetConstruct, ESPELHO da MyStake (s424).
//
// ⚠ LIGADA SEM CONTA. Ninguém aqui tinha conta na Jack em 20/10/2026. O que foi MEDIDO, por
// fora, na aba de `jack.com` (o curl para no desafio do Cloudflare):
//   • `POST /api/game/p/messagetosport` responde 401 e uma rota falsa responde 404, a mesma
//     prova que registrou a MyStake na s392;
//   • o sportsbook mora em `/br/sportsbook`, o caminho da MyStake.
// O que NÃO foi medido: o `gethistory` logado, o `Company`, a moeda e o teto de `Count`.
//
// POR ISSO A FIXTURE É EMPRESTADA: é a da MyStake (9 bilhetes reais, conferidos no card),
// servida no endereço da Jack. Este caso trava a LIGAÇÃO (o inject roda no domínio da Jack e
// o formatador sai byte a byte igual ao da MyStake), NÃO os dados da casa.
//
// Quando a 1ª captura real chegar: salvar o payload como `fixtures/jack.gethistory.json`,
// conferir no card e trocar a fixture e as conferências por bilhetes da própria Jack.
import { rodarInject, carregarContent, fixture } from "../sandbox.mjs";

export const casa = "Jack";

const HOSTS = {
  jack:    { href: "https://jack.com/br/sportsbook/mybets",    api: "https://jack.com/api/game/p/messagetosport" },
  mystake: { href: "https://mystake.bet/br/sportsbook/mybets", api: "https://mystake.bet/api/game/p/messagetosport" },
};

async function capturar(corpo, h) {
  return rodarInject({
    inject: "tv_inject.js",
    href: h.href,
    urlInicial: h.api,
    pedido: "__sharpenupTVReq",
    responder: (url) => (url.includes("messagetosport") ? corpo : null),
  });
}

export async function rodar() {
  const corpo = fixture("mystake.gethistory.json");
  const falhas = [];
  let testes = 0;

  const { ultima } = await capturar(corpo, HOSTS.jack);
  if (!ultima) return { falhas: ["o inject não emitiu nenhuma mensagem em jack.com"], testes: 1 };

  // ── 1. O inject roda a partir do host da Jack ────────────────────────────────────────
  testes++;
  if (!ultima.hook) falhas.push("o inject não sinalizou `hook` rodando em jack.com");
  testes++;
  if (!ultima.fim) falhas.push("o inject não sinalizou `fim` (o robô ficaria esperando o teto)");
  const tickets = ultima.tickets || [];
  testes++;
  if (tickets.length !== 9) falhas.push(`esperava os 9 bilhetes da fixture, vieram ${tickets.length}`);

  // ── 2. O bloco da Jack é IDÊNTICO ao da MyStake — é isso que "espelho" quer dizer ────
  const fmt = carregarContent().pegar("formatTicketTV");
  const porId = new Map(tickets.map((t) => [String(t.id), t]));
  const ms = await capturar(corpo, HOSTS.mystake);
  const m = new Map((((ms.ultima || {}).tickets) || []).map((t) => [String(t.id), t]));
  testes++;
  const diferentes = [...porId].filter(([id, t]) => !m.get(id) || fmt(m.get(id)) !== fmt(t)).map(([id]) => id);
  if (m.size !== porId.size || diferentes.length) {
    falhas.push(`espelho: ${diferentes.length} bloco(s) diferem entre jack.com e mystake.bet (${diferentes.slice(0, 3).join(", ")})`);
  }

  // ── 3. Um bloco conferido por inteiro: marcador, odd completa e a freebet ────────────
  testes++;
  const fb = porId.get("306558902");
  const txt = fb ? fmt(fb) : "";
  if (!txt.startsWith("[Código: 306558902]")) falhas.push("306558902: marcador [Código:] ausente/errado");
  if (!txt.includes("29,7667")) falhas.push("306558902: odd sem a precisão completa (29,7667)");
  if (!txt.includes("Freebet incluído: 45,00")) falhas.push("306558902: a freebet (TicketType 3) não subiu");

  return { falhas, testes };
}
