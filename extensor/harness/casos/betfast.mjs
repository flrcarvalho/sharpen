// Betfast (BetConstruct / sportsbook v4) — ESPELHO da Tivo (s211).
//
// A Betfast roda o MESMO motor da Tivo no mesmo caminho de API
// (`POST /api/game/p/messagetosport` com `{name:"gethistory"}`), então ela usa o
// `tv_inject.js` e o `formatTicketTV` sem uma linha duplicada. Este caso existe para
// travar DUAS coisas distintas:
//
//   1) O ESPELHO. O inject não pode ficar amarrado a `tivo.bet.br`: aqui ele roda a
//      partir de `www.betfast.bet.br` e tem de capturar igual. Se alguém hardcodar o
//      host um dia, este caso fica vermelho.
//   2) O QUE SÓ A BETFAST TROUXE. A amostra da Tivo (24 bilhetes) não tinha nenhum dos
//      dois casos abaixo; a da Betfast (50 bilhetes reais, conta do Feca) tem os dois.
//      Como o código é compartilhado, o que se trava aqui protege as duas casas.
//
// ── O que a Betfast provou e a Tivo não tinha ────────────────────────────────────
//
// `Result: 1` numa PERNA = ANULADA/DEVOLVIDA (void). A `CASA_TIVO §5` registrava esse
// enum como "natureza ainda não confirmada" desde a s196. A prova é aritmética e vem do
// bilhete `295698756`:
//     perna A  1.95  Result 1   ← saiu do cálculo
//     perna B  2.67  Result 2
//     Koef 5.2065 (= 1.95 × 2.67, as duas)   WinKoef 2.67 (= só a que valeu)
//     WinAmount 403.17 == 151 × 2.67, AO CENTAVO
// Ou seja: a casa recalculou o bilhete sem a perna void. A odd que vale é 2,67 (a régua
// global `retorno ÷ stake`), NÃO o `Koef` 5,2065 — e é justamente aqui que a odd exibida
// no card mentiria em dobro sobre o P/L.
//
// `ItemType: 6` = ODD OFERECIDA (bet builder promocional da casa). 4 dos 50 bilhetes.
// A perna vem com `Game`, `Market`, `Position` e `Sport` TODOS null — o bloco sairia mudo
// (`- [perdeu]` e nada mais) e a IA teria de inventar esporte e descrição. O conteúdo real
// está em `OfferedOddObject`, e vem EM INGLÊS (`Soccer`, `Match result`, `shots on
// target`), porque o `language: 33` do pedido não alcança esse objeto.
//
// FUSO da odd oferecida: o `OfferedOddObject.StartTime` é string ISO **sem offset**
// (`"2026-07-02T00:00:00"`), enquanto o resto do motor é epoch ms UTC. **Decisão do Feca
// (s211): tratar como horário do Brasil** — o inject carimba `-03:00` em vez de deixar o
// JS usar o fuso da máquina (que daria data diferente por operador). Os horários esperados
// abaixo são, portanto, o valor literal da string.
//
// ── Como os valores abaixo foram obtidos ────────────────────────────────────────
// Print da lista "Minhas apostas" de 27/07/2026, colunas `Status · Id · Data · Tipo ·
// Valor apostado · ODDS · Quantia`. Os 17 bilhetes visíveis foram conferidos UM A UM
// contra o JSON. O campo `tela` guarda a ODD QUE A CASA MOSTRA — ela não é a odd que
// usamos, é a prova de que a tela TRUNCA (floor) em 2 casas:
//     2.058 → "2.05"   ·   7.215 → "7.21"   ·   15.6087 → "15.60"   ·   3.3874 → "3.38"
// Arredondar daria 2.06 / 7.22 / 15.61 / 3.39. São 7 divergências em 17 bilhetes; ler a
// odd do card seria errar quase metade da conta.
import { rodarInject, carregarContent, fixture, linha } from "../sandbox.mjs";

export const casa = "Betfast";

const HREF = "https://www.betfast.bet.br/br#/mybets";
const API = "https://www.betfast.bet.br/api/game/p/messagetosport";

// `data` = colocação (`ActionTime`, UTC→BRT) — é o que a coluna "Data" do card mostra.
// `evento` = `Game.StartTime` da perna mais recente — é ESTA que vai para a 1ª coluna do
// TSV (`MASTER_OUTPUT §4`). Os 4 marcados DIA DIFERENTE provam por que a distinção existe:
// sem ela, esses bilhetes entrariam na planilha no dia errado.
// `odd` = a odd que o bloco deve emitir, com precisão COMPLETA. `tela` = o que o card
// mostra (truncado) — nunca é o que usamos.
const ESPERADO = {
  "298801814": { data: "26/07/2026 12:22:02", evento: "26/07/2026 18:30:00", odd: "2,058",   tela: "2.05",  pernas: 2, status: /^Perdeu → L/ },
  "298801782": { data: "26/07/2026 12:21:42", evento: "26/07/2026 18:30:00", odd: "24,2888", tela: "24.28", pernas: 4, status: /^Perdeu → L/ },
  "298782094": { data: "26/07/2026 09:15:33", evento: "26/07/2026 18:30:00", odd: "27,55",   tela: "27.55", pernas: 4, status: /^Perdeu → L/ },
  // Tem UMA perna void (Result 1) e mesmo assim é L: o bilhete perdeu por outra perna.
  // A odd continua sendo o `Koef` cheio — em L não há retorno para recalcular nada.
  "298710145": { data: "25/07/2026 13:59:29", evento: "25/07/2026 20:30:00", odd: "18,3698", tela: "18.36", pernas: 3, status: /^Perdeu → L/, void: 1 },
  "298710118": { data: "25/07/2026 13:59:15", evento: "25/07/2026 20:30:00", odd: "19,278",  tela: "19.27", pernas: 3, status: /^Perdeu → L/ },
  "298586333": { data: "24/07/2026 11:08:03", evento: "24/07/2026 21:30:00", odd: "16,0528", tela: "16.05", pernas: 4, status: /^Perdeu → L/ },
  // DIA DIFERENTE — colocado 23/07, o jogo mais tarde é 24/07 09:16.
  "298506257": { data: "23/07/2026 13:42:39", evento: "24/07/2026 09:16:00", odd: "36,4222", tela: "36.42", pernas: 5, status: /^Perdeu → L/ },
  "298490008": { data: "23/07/2026 10:56:46", evento: "23/07/2026 19:30:00", odd: "8,2248",  tela: "8.22",  pernas: 2, status: /^Perdeu → L/ },
  "298489971": { data: "23/07/2026 10:56:14", evento: "23/07/2026 21:30:00", odd: "7,215",   tela: "7.21",  pernas: 3, status: /^Perdeu → L/ },
  "298391099": { data: "22/07/2026 09:38:10", evento: "22/07/2026 21:30:00", odd: "6,8543",  tela: "6.85",  pernas: 3, status: /^Perdeu → L/ },
  "298391089": { data: "22/07/2026 09:37:57", evento: "22/07/2026 21:30:00", odd: "15,6087", tela: "15.60", pernas: 3, status: /^Perdeu → L/ },
  // O ÚNICO W entre os visíveis. O card mostra "Quantia 1.604,28" e a conta fecha ao
  // centavo com a odd cheia: 101 × 15,884 = 1.604,284. Dinheiro e odd concordam aqui —
  // é o contraste com o 295698756 lá embaixo, onde NÃO concordam.
  "298388575": { data: "22/07/2026 09:02:32", evento: "22/07/2026 21:30:00", odd: "15,884",  tela: "15.88", pernas: 3, status: /^Ganho → W \(retorno R\$ 1604,28\)/ },
  "298304861": { data: "21/07/2026 11:11:47", evento: "21/07/2026 20:00:00", odd: "3,3874",  tela: "3.38",  pernas: 3, status: /^Perdeu → L/ },
  "298304533": { data: "21/07/2026 11:06:51", evento: "21/07/2026 21:35:00", odd: "23,9456", tela: "23.94", pernas: 4, status: /^Perdeu → L/ },
  // DIA DIFERENTE
  "298304503": { data: "21/07/2026 11:06:25", evento: "22/07/2026 10:32:50", odd: "17,1121", tela: "17.11", pernas: 4, status: /^Perdeu → L/ },
  // DIA DIFERENTE
  "298255971": { data: "20/07/2026 16:26:02", evento: "21/07/2026 08:00:00", odd: "93,3987", tela: "93.39", pernas: 5, status: /^Perdeu → L/ },
  // DIA DIFERENTE
  "298254792": { data: "20/07/2026 16:12:47", evento: "21/07/2026 13:00:47", odd: "10,8108", tela: "10.81", pernas: 3, status: /^Perdeu → L/ },
};

// Os 4 `ItemType: 6`. `evento` = o `OfferedOddObject.StartTime` lido como horário do Brasil
// (= o valor literal da string). `odd` é o `Koef` do bilhete — não o `RealPrice` nem o
// `CalcPrice` da oferta, que são preços internos do motor e divergem (6.17 / 7.1 contra 9.51).
const OFERTAS = {
  "297302630": { data: "10/07/2026 22:18:17", evento: "11/07/2026 21:00:00", odd: "9,51",
                 jogo: "Norway - England", esporte: "Soccer", liga: "World Cup / Quarter-finals",
                 subs: ["Match result: 2", "Kane, Harry shots on target: 2 and more", "Haaland, Erling shots on target: 2 and more"] },
  "297051837": { data: "08/07/2026 12:34:00", evento: "09/07/2026 20:00:00", odd: "6,14",
                 jogo: "France - Morocco", esporte: "Soccer", liga: "World Cup / Quarter-finals",
                 subs: ["Match result: 1", "Mbappe, Kylian shots on target: 2 and more", "Total cards: Over"] },
  // O único dos 4 em que o fuso troca o DIA: 01/07 se a string fosse UTC, 02/07 como local.
  // Fica em 02/07 pela decisão do Feca — e é a linha que acusa se alguém reverter o offset.
  "296275825": { data: "01/07/2026 20:55:56", evento: "02/07/2026 00:00:00", odd: "12,56",
                 jogo: "USA - Bosnia & Herzegovina", esporte: "Soccer", liga: "World Cup / 1/16-finals",
                 subs: ["Match result: 1", "Balogun, Folarin shots on target: 2 and more", "Pulisic, Christian shots on target: 2 and more"] },
  "295233005": { data: "22/06/2026 16:56:59", evento: "22/06/2026 21:00:00", odd: "4,93",
                 jogo: "France - Iraq", esporte: "Soccer", liga: "World Cup / Group Stage",
                 subs: ["Total: Over", "Mbappe, Kylian shots on target: 2 and more", "Total corners: Over"] },
};

export async function rodar() {
  const corpo = fixture("betfast.gethistory.json");
  const falhas = [];
  let testes = 0;

  const { ultima } = await rodarInject({
    inject: "tv_inject.js",
    href: HREF,
    urlInicial: API,
    pedido: "__sharpenupTVReq",
    responder: (url) => (url.includes("messagetosport") ? corpo : null),
  });

  if (!ultima) return { falhas: ["o inject não emitiu nenhuma mensagem"], testes: 0 };

  // ── 1. O espelho funciona a partir do host da Betfast ──────────────────────────
  testes++;
  if (!ultima.hook) falhas.push("o inject não sinalizou `hook` rodando em www.betfast.bet.br");
  testes++;
  if (!ultima.fim) falhas.push("o inject não sinalizou `fim` (o robô ficaria esperando o teto)");

  const tickets = ultima.tickets || [];
  testes++;
  if (tickets.length !== 50) falhas.push(`esperava 50 bilhetes na fixture, vieram ${tickets.length}`);

  // ── 2. Teto do `Count` — a consulta encheu, então tem de conferir atrás ───────
  // Esta conta responde `Count: 50` == `Tickets.length`, e o operador confirmou que a lista
  // **para nas 50 e não tem "mostrar mais"** (s211): `len == Count` significa "a consulta
  // encheu", não "a conta acabou". O inject marca o teto e varre para trás por `to`.
  // Aqui o `responder` devolve sempre o MESMO corpo, então a 1ª janela retroativa não traz
  // nada novo → a varredura conclui que os 50 são tudo (`tetoResolvido`).
  testes++;
  if (!ultima.tetoSuspeito) {
    falhas.push("Count:50 == Tickets.length e o inject não marcou `tetoSuspeito` — " +
                "sem isso ele declara fim sem conferir se há histórico além do teto");
  }
  testes++;
  if (!ultima.tetoResolvido) {
    falhas.push("a varredura retroativa não rodou (ou não concluiu): sem ela, bilhete " +
                "anterior ao teto fica invisível PARA SEMPRE, sem erro nenhum");
  }
  testes++;
  if (ultima.alemDoTeto) {
    falhas.push("`alemDoTeto` ligado sendo que a janela retroativa não trouxe bilhete novo");
  }

  const fmt = carregarContent().pegar("formatTicketTV");
  const porId = new Map(tickets.map((t) => [String(t.id), t]));

  // ── 3. Os 17 bilhetes conferidos contra o card ────────────────────────────────
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

    const status = linha(txt, "Status:");
    if (!e.status.test(status)) falhas.push(`${id}: status "${status}"`);

    const odd = linha(txt, "Odd:");
    if (odd !== e.odd) falhas.push(`${id}: odd esperada ${e.odd}, veio "${odd}" (a tela mostra ${e.tela} — trunca; vale o Koef inteiro)`);

    // Nos bilhetes em que a tela TRUNCA (7 dos 17), a odd emitida jamais pode ser a do card
    // — é esse o erro que a casa induz. Onde o Koef já tem 2 casas (ex.: 27.55) os dois
    // valores coincidem legitimamente e não há o que comparar.
    if (e.tela.replace(".", ",") !== e.odd && odd === e.tela.replace(".", ",")) {
      falhas.push(`${id}: emitiu a odd TRUNCADA do card (${e.tela}) em vez do Koef ${e.odd}`);
    }

    const tipo = linha(txt, "Tipo:");
    const esperaTipo = e.pernas >= 2 ? `Múltipla (${e.pernas} seleções)` : "Simples";
    if (tipo !== esperaTipo) falhas.push(`${id}: tipo esperado "${esperaTipo}", veio "${tipo}"`);

    // Perna anulada tem de sair NOMEADA, não como "Result 1 — a conferir".
    if (e.void) {
      testes++;
      const anuladas = (txt.match(/\[anulada\/devolvida\]/g) || []).length;
      if (anuladas !== e.void) falhas.push(`${id}: esperava ${e.void} perna(s) [anulada/devolvida], achei ${anuladas}`);
      if (/Result 1 — a conferir/.test(txt)) falhas.push(`${id}: perna void ainda sai como enum cru`);
    }
  }

  // ── 4. O W recalculado sem a perna void (295698756) ───────────────────────────
  // O bilhete mais importante do lote: é o único onde a odd do card mente sobre o P/L.
  {
    const id = "295698756";
    const t = porId.get(id);
    testes++;
    if (!t) {
      falhas.push(`${id}: não veio na captura`);
    } else {
      const txt = fmt(t);
      const odd = linha(txt, "Odd:");
      // 403,17 ÷ 151 = 2,67 exato. O `Koef` (5,2065) daria retorno 786,18 — quase o DOBRO.
      if (odd !== "2,67") {
        falhas.push(`${id}: odd esperada 2,67 (= retorno 403,17 ÷ stake 151, perna void fora), veio "${odd}"` +
                    (odd === "5,2065" ? " — pegou o Koef CHEIO, que inclui a perna anulada e dobraria o P/L" : ""));
      }
      testes++;
      const status = linha(txt, "Status:");
      if (!/^Ganho → W \(retorno R\$ 403,17\)/.test(status)) falhas.push(`${id}: status "${status}"`);
      testes++;
      if (!/\[anulada\/devolvida\]/.test(txt)) falhas.push(`${id}: a perna void (1,95) não saiu nomeada`);
      testes++;
      if (linha(txt, "Data (evento mais recente):") !== "27/06/2026 06:15:00") {
        falhas.push(`${id}: evento "${linha(txt, "Data (evento mais recente):")}"`);
      }
    }
  }

  // ── 5. Os 4 `ItemType: 6` (odd oferecida) ─────────────────────────────────────
  for (const [id, e] of Object.entries(OFERTAS)) {
    const t = porId.get(id);
    if (!t) { falhas.push(`${id}: não veio na captura`); continue; }
    const txt = fmt(t);
    testes++;

    // O sintoma que este bloco existe para matar: bilhete sem nenhum conteúdo legível.
    if (/^- \[(perdeu|ganhou)\]$/m.test(txt)) {
      falhas.push(`${id}: bloco MUDO — a perna saiu sem jogo, mercado nem esporte (ItemType 6 não lido)`);
    }
    if (!txt.includes(e.jogo)) falhas.push(`${id}: o jogo "${e.jogo}" não apareceu no bloco`);
    if (!txt.includes(e.esporte)) falhas.push(`${id}: o esporte "${e.esporte}" não apareceu no bloco`);
    if (!txt.includes(e.liga)) falhas.push(`${id}: a liga "${e.liga}" não apareceu no bloco`);
    for (const s of e.subs) {
      if (!txt.includes(s)) falhas.push(`${id}: a seleção "${s}" não apareceu no bloco`);
    }

    const evento = linha(txt, "Data (evento mais recente):");
    if (evento !== e.evento) falhas.push(`${id}: evento esperado ${e.evento}, veio "${evento}" (StartTime do OfferedOddObject, lido como horário do Brasil)`);
    const data = linha(txt, "Data (colocação):");
    if (data !== e.data) falhas.push(`${id}: colocação esperada ${e.data}, veio "${data}"`);
    const odd = linha(txt, "Odd:");
    if (odd !== e.odd) falhas.push(`${id}: odd esperada ${e.odd} (Koef do bilhete), veio "${odd}"`);

    // O rótulo da casa diz "Simples" (Items.length === 1), mas são N seleções do MESMO
    // evento — é bet builder. A IA precisa desse sinal para não classificar como simples
    // (`MASTER_ESPORTES` / regra dos múltiplos: bet builder fica com o esporte do jogo).
    testes++;
    const tipo = linha(txt, "Tipo:");
    if (!/bet builder/i.test(tipo) || !tipo.includes(String(e.subs.length))) {
      falhas.push(`${id}: tipo "${tipo}" — deveria anunciar bet builder com ${e.subs.length} seleções do mesmo evento`);
    }
    // O idioma da oferta é inglês e a casa não traduz. Avisar a IA evita que ela trate
    // "Match result" como mercado desconhecido.
    testes++;
    if (!/inglês/i.test(txt)) falhas.push(`${id}: o bloco não avisa que os rótulos da oferta vêm em inglês`);
  }

  // ── 6. O bloco da Betfast é IDÊNTICO ao da Tivo — é isso que "espelho" quer dizer ──
  // Roda a MESMA fixture pelos dois hosts e compara byte a byte. Se um dia alguém ramificar
  // o formatador por casa, isto acusa na hora.
  {
    const rTivo = await rodarInject({
      inject: "tv_inject.js",
      href: "https://tivo.bet.br/br/sportsbook/prematch#/mybets",
      urlInicial: "https://tivo.bet.br/api/game/p/messagetosport",
      pedido: "__sharpenupTVReq",
      responder: (url) => (url.includes("messagetosport") ? corpo : null),
    });
    const tv = new Map(((rTivo.ultima && rTivo.ultima.tickets) || []).map((t) => [String(t.id), t]));
    testes++;
    if (tv.size !== porId.size) {
      falhas.push(`espelho: host tivo capturou ${tv.size} e host betfast ${porId.size} — a captura não pode depender do domínio`);
    } else {
      const diferentes = [];
      for (const [id, t] of porId) {
        const o = tv.get(id);
        if (!o || fmt(o) !== fmt(t)) diferentes.push(id);
      }
      if (diferentes.length) {
        falhas.push(`espelho: ${diferentes.length} bloco(s) diferem entre os dois hosts (${diferentes.slice(0, 3).join(", ")}…)`);
      }
    }
  }

  // ── 7. A varredura TRAZ o histórico que a tela esconde ────────────────────────
  // O teste acima cobre "não havia mais nada". Este cobre o caso que dói: a conta TEM
  // bilhete além do teto e a tela não mostra. Simulamos a casa de verdade — a consulta sem
  // `to` devolve as 50 do teto; com `to` devolve o que é mais antigo que aquele instante.
  // Sem a varredura, esses bilhetes seriam invisíveis para sempre, sem erro nenhum.
  {
    const bruto = JSON.parse(corpo);
    const ordenado = [...bruto.Tickets].sort((a, b) => (b.ActionTime || 0) - (a.ActionTime || 0));
    const teto = ordenado.slice(0, 50);                       // o que a tela mostra
    // Dois bilhetes fabricados ANTES do mais antigo real (23/05/2026) — a "página 2" que só
    // existe pela API. Marcados como sintéticos: não são leitura de card.
    const antigos = [
      { ...ordenado[ordenado.length - 1], ID: 111111111, ActionTime: Date.parse("2026-04-10T14:00:00Z") },
      { ...ordenado[ordenado.length - 1], ID: 222222222, ActionTime: Date.parse("2026-03-01T14:00:00Z") },
    ];
    const corpoDe = (lista) => JSON.stringify({ Error: null, Tickets: lista, Count: lista.length });

    const r3 = await rodarInject({
      inject: "tv_inject.js",
      href: HREF,
      urlInicial: API,
      pedido: "__sharpenupTVReq",
      ms: 900,
      responder: (url, opts) => {
        if (!url.includes("messagetosport")) return null;
        let ate = null;
        try {
          const o = JSON.parse((opts && opts.body) || "{}");
          const m = JSON.parse(o.message || "{}");
          if (typeof m.to === "number") ate = m.to;
        } catch (e) {}
        if (ate == null) return corpoDe(teto);                       // a lista da tela
        const fatia = antigos.filter((t) => t.ActionTime <= ate);    // só o que é mais antigo
        return corpoDe(fatia);
      },
    });

    const t3 = (r3.ultima && r3.ultima.tickets) || [];
    testes++;
    if (t3.length !== 52) {
      falhas.push(`varredura: esperava 52 bilhetes (50 do teto + 2 além dele), vieram ${t3.length}` +
                  (t3.length === 50 ? " — a varredura NÃO furou o teto; o histórico antigo ficaria invisível" : ""));
    }
    testes++;
    if (!r3.ultima || !r3.ultima.alemDoTeto) {
      falhas.push("varredura: trouxe bilhete além do teto mas não sinalizou `alemDoTeto`");
    }
    testes++;
    const ids3 = new Set(t3.map((t) => String(t.id)));
    for (const id of ["111111111", "222222222"]) {
      if (!ids3.has(id)) falhas.push(`varredura: o bilhete ${id}, anterior ao teto, não foi capturado`);
    }
    // E não pode virar laço: a casa devolve lista vazia quando não há mais nada atrás.
    testes++;
    if (!r3.ultima.fim) falhas.push("varredura: não sinalizou `fim` — o robô ficaria esperando o teto de tempo");
  }

  return { falhas, testes };
}
