// Locasbet (locas.bet · locasbetNN.com) — 7ª casa BetConstruct, ESPELHO da MyStake (s437).
//
// ⚠ LIGADA SEM CONTA, como a Jack (s424). Ninguém aqui tinha conta na Locasbet em 01/11/2026.
// O que foi MEDIDO, por fora:
//   • `POST /api/game/p/messagetosport` responde 401 e uma rota falsa 404, em `locasbet12.com`
//     (aba do Chrome) e em `locas.bet` (curl): a mesma prova que registrou a MyStake na s392;
//   • os dois domínios servem o mesmo `scripts/common/helpers.js`, com o mesmo hash de versão.
// O que NÃO foi medido: o `gethistory` logado, o `Company`, a moeda e o teto de `Count`.
//
// POR ISSO A FIXTURE É EMPRESTADA: é a da MyStake (9 bilhetes reais, conferidos no card),
// servida nos endereços da Locasbet. Este caso trava a LIGAÇÃO (o inject roda nos domínios da
// Locasbet e o formatador sai byte a byte igual ao da MyStake), NÃO os dados da casa.
//
// Três hosts de propósito: o fixo (`locas.bet`), o número do dia do registro (`locasbet12.com`)
// e o último adiantado (`locasbet20.com`). O domínio da casa RODA o número (CASA_LOCASBET §1).
// O que este caso NÃO cobre: que o `manifest.json` liste esses hosts (quem confere é o
// `audit_sharpenup`); o sandbox roda o inject em qualquer href.
//
// Quando a 1ª captura real chegar: salvar o payload como `fixtures/locasbet.gethistory.json`,
// conferir no card e trocar a fixture e as conferências por bilhetes da própria Locasbet.
import { rodarInject, carregarContent, fixture } from "../sandbox.mjs";

export const casa = "Locasbet";

const HOSTS = {
  locas:    { href: "https://locas.bet/en/sportsbook/mybets",      api: "https://locas.bet/api/game/p/messagetosport" },
  locas12:  { href: "https://locasbet12.com/en/sportsbook/mybets", api: "https://locasbet12.com/api/game/p/messagetosport" },
  locas20:  { href: "https://locasbet20.com/en/sportsbook/mybets", api: "https://locasbet20.com/api/game/p/messagetosport" },
  mystake:  { href: "https://mystake.bet/br/sportsbook/mybets",    api: "https://mystake.bet/api/game/p/messagetosport" },
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

  const fmt = carregarContent().pegar("formatTicketTV");
  const ms = await capturar(corpo, HOSTS.mystake);
  const m = new Map((((ms.ultima || {}).tickets) || []).map((t) => [String(t.id), t]));

  for (const nome of ["locas", "locas12", "locas20"]) {
    const h = HOSTS[nome];
    const host = new URL(h.href).host;
    const { ultima } = await capturar(corpo, h);
    testes++;
    if (!ultima) { falhas.push(`o inject não emitiu nenhuma mensagem em ${host}`); continue; }

    // ── 1. O inject roda a partir do host da Locasbet ──────────────────────────────────
    testes++;
    if (!ultima.hook) falhas.push(`o inject não sinalizou \`hook\` rodando em ${host}`);
    testes++;
    if (!ultima.fim) falhas.push(`${host}: o inject não sinalizou \`fim\` (o robô ficaria esperando o teto)`);
    const tickets = ultima.tickets || [];
    testes++;
    if (tickets.length !== 9) falhas.push(`${host}: esperava os 9 bilhetes da fixture, vieram ${tickets.length}`);

    // ── 2. O bloco da Locasbet é IDÊNTICO ao da MyStake — é isso que "espelho" quer dizer ─
    const porId = new Map(tickets.map((t) => [String(t.id), t]));
    testes++;
    const diferentes = [...porId].filter(([id, t]) => !m.get(id) || fmt(m.get(id)) !== fmt(t)).map(([id]) => id);
    if (m.size !== porId.size || diferentes.length) {
      falhas.push(`espelho: ${diferentes.length} bloco(s) diferem entre ${host} e mystake.bet (${diferentes.slice(0, 3).join(", ")})`);
    }

    // ── 3. Um bloco conferido por inteiro: marcador, odd completa e a freebet ──────────
    testes++;
    const fb = porId.get("306558902");
    const txt = fb ? fmt(fb) : "";
    if (!txt.startsWith("[Código: 306558902]")) falhas.push(`${host} 306558902: marcador [Código:] ausente/errado`);
    if (!txt.includes("29,7667")) falhas.push(`${host} 306558902: odd sem a precisão completa (29,7667)`);
    if (!txt.includes("Freebet incluído: 45,00")) falhas.push(`${host} 306558902: a freebet (TicketType 3) não subiu`);
  }

  return { falhas, testes };
}
