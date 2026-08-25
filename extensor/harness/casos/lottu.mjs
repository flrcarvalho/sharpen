// Lottu (motor NGBras) — captura por API `/bet` + detalhe por item (s290).
//
// Motor NOVO no Sharpen, o segundo em dois dias: não é Altenar, BetBy, BetConstruct, Kambi,
// BlueBrown nem bwin/Entain. Confirmado ANTES do login, pelo método de sempre — a home não
// carrega asset de motor nenhum (só `widgets.sir.sportradar.com`, que é widget de
// estatística, não plataforma de apostas), e a API vive em host próprio.
//
// O que sustenta o modo, MEDIDO ao vivo (24/08/2026), não deduzido:
//   • `GET /bet?initial_date=…Z&final_date=…Z&status=ALL` devolve a FAIXA INTEIRA numa
//     chamada — 152 bilhetes, 84 KB, sem paginação e sem cursor. É o "peça a FAIXA" do
//     CLAUDE.md acontecendo de graça;
//   • as ABERTAS têm forma própria: `GET /bet?status=OPEN&page=N` (paginado, sem datas);
//   • autenticação por header (`authorization` + `ngx-source`), não cookie: uma chamada
//     sem eles morre no CORS. O replay reusa os headers da requisição REAL;
//   • **a lista NÃO traz as seleções** — só `events_qty`. Jogo, mercado e a data do EVENTO
//     (que é a coluna Data do TSV) só existem em `GET /bet/{_id}`, uma chamada POR BILHETE.
//     É o anti-padrão do CLAUDE.md ("API externa por item"), aqui inevitável: o freio de
//     dias + `stopId` é o que impede as 152 chamadas virarem rotina.
//
// ⚠️ A ARMADILHA CENTRAL DESTA CASA, e ela é pior que a da VaideBet.
// `return_value`/`gross_return_value` são o retorno **POTENCIAL**, sempre — inclusive nas
// PERDIDAS. Medido nos 152 bilhetes da conta: **114 de 114 perdidas** têm retorno
// preenchido, e em **114 de 114** ele é exatamente `stake × odd`. Na VaideBet o campo só
// mentia na aberta; aqui ele mente em toda linha que não ganhou. Ler dinheiro como
// realizado transformaria **toda perdida em vitória**.
// Consequência de desenho: nesta casa **só o `status` decide** W/L. O dinheiro não é régua.
import { rodarInject, carregarContent, fixture, linha } from "../sandbox.mjs";

export const casa = "Lottu";

// ⚠️ TIPO: os dois bilhetes são "Simples de X" no card e têm UMA seleção na API — e mesmo
// assim são MÚLTIPLA. `CASA_LOTTU §2.2` (s41, escrita a partir do print) já dizia: a Lottu
// vende Desafios, condições combinadas sobre o mesmo jogo, e o `&` na resposta é a marca.
// Classificar pela estrutura da API mandaria todos para "Simples" — a regra da casa é mais
// velha que a captura e vence.
//
// Valores lidos do CARD da Lottu (aba Todas, filtro 01/06→24/08 de 2026), não do código.
// As duas datas são ISO UTC e viram America/Sao_Paulo.
const ESPERADO = {
  // Ganha. Card: "6512222 · Simples de 3.50 · Aposta R$ 50,00 · Retorno R$ 175,00".
  "6512222": { evento: "29/07/2026 21:29:25", colocacao: "29/07/2026 00:27:30", odd: "3,5",
               stake: "50,00", status: /^Ganho → W/, tipo: /^Múltipla \(Desafio · 2 condições no mesmo jogo\)$/, retorno: "175,00",
               jogo: "Vitória x Palmeiras" },

  // Perdida — e é ELA que prova a armadilha: o card estampa "Retorno R$ 125,00" numa aposta
  // que PERDEU, porque 25 × 5 = 125 é o potencial. O bloco não pode chamar isso de retorno.
  "6585838": { evento: "01/08/2026 17:29:52", colocacao: "01/08/2026 15:45:55", odd: "5",
               stake: "25,00", status: /^Perdeu → L$/, tipo: /^Múltipla \(Desafio · 2 condições no mesmo jogo\)$/, potencialMentiroso: "125,00",
               jogo: "Vasco x Fluminense" },
};

const HOST = "https://alpha-sb.ngbras.com";
const HREF = "https://www.lottu.bet.br/user-dashboard/my-bets?option=MY-BETS_MAIN";

// Servidor de mentira: responde pelo `status` da QUERY e serve o detalhe por `_id`, como a
// casa faz. A aba OPEN volta vazia (a conta não tinha aposta viva no reconhecimento).
function servidor() {
  const lista = JSON.parse(fixture("lottu.bets.json"));
  const detalhes = JSON.parse(fixture("lottu.detalhes.json"));
  const pedidos = [];
  const resp = (url) => {
    const u = String(url);
    if (!u.includes("/bet")) return null;
    pedidos.push(u);
    const det = /\/bet\/([a-f0-9]{24})/i.exec(u);
    if (det) {
      const d = detalhes.find((x) => x._id === det[1]);
      return d ? JSON.stringify(d) : JSON.stringify({});
    }
    const q = new URL(u).searchParams;
    if (q.get("status") === "OPEN") return "[]";          // sem aposta viva na amostra
    return JSON.stringify(lista);
  };
  return { resp, pedidos };
}

async function umClique() {
  const srv = servidor();
  const { ultima } = await rodarInject({
    inject: "lt_inject.js",
    href: HREF,
    urlInicial: HOST + "/bet?status=OPEN&page=0",
    // Os headers são o ponto: o inject SÓ aprende uma requisição que traga `authorization`.
    // Guardar uma sem ele deixaria o replay batendo em CORS/401 para sempre, e a casa
    // devolveria lista vazia com HTTP 200 — falha muda. Sem `optsInicial` o replay nem
    // arranca, e é assim que este caso prova a guarda.
    optsInicial: { method: "GET", headers: { "authorization": "Bearer TOKEN_DE_TESTE",
                                             "ngx-source": "DESKTOP", "accept": "application/json" } },
    pedido: "__sharpenupLTReq",
    ms: 1500,
    responder: srv.resp,
  });
  return { ultima, pedidos: srv.pedidos };
}

export async function rodar() {
  const falhas = [];
  let testes = 0;

  const { ultima, pedidos } = await umClique();
  testes++;
  if (!ultima) return { falhas: ["o inject não emitiu nenhuma mensagem"], testes };
  if (!ultima.hook) falhas.push("não sinalizou 'hook' — o autodiagnóstico fica cego");
  if (typeof ultima.respostas !== "number" || ultima.respostas < 1)
    falhas.push("'respostas' não reportado — não separa \"não injetei\" de \"endpoint mudou\"");
  if (!ultima.fim) falhas.push("não sinalizou 'fim' — o robô esperaria o teto");

  const bets = ultima.bets || [];
  if (bets.length !== 2) falhas.push(`esperava 2 bilhetes na fixture, vieram ${bets.length}`);

  // A LISTA tem de ser pedida por FAIXA DE DATAS. Sem `initial_date`/`final_date` a casa
  // responde 200 com `[]` — foi o que aconteceu no reconhecimento e me fez achar, por um
  // momento, que a conta estava vazia. Falha silenciosa: HTTP 200, zero bilhete.
  testes++;
  const comFaixa = pedidos.find((u) => /initial_date=/.test(u) && /final_date=/.test(u));
  if (!comFaixa) falhas.push("nenhuma requisição mandou initial_date/final_date — a casa devolveria [] com HTTP 200");

  // As ABERTAS têm forma PRÓPRIA (status=OPEN, paginado). Sem este pedido, aposta viva
  // sumiria do lote — e ela é justamente a que ainda não tem amostra nesta conta.
  testes++;
  if (!pedidos.some((u) => /status=OPEN/.test(u)))
    falhas.push("nunca pediu a aba OPEN — aposta viva sumiria do lote");

  // O DETALHE por item é o que traz jogo, mercado e a data do evento. Um bilhete sem
  // detalhe não tem coluna Data.
  testes++;
  const detalhes = pedidos.filter((u) => /\/bet\/[a-f0-9]{24}/i.test(u));
  if (detalhes.length !== 2)
    falhas.push(`esperava 1 detalhe por bilhete (2), vieram ${detalhes.length}`);

  // ── Leitura bilhete a bilhete, contra o card ──────────────────────────────────
  const fmt = carregarContent().pegar("formatTicketLT");
  for (const b of bets) {
    const id = String(b.code || "");
    const e = ESPERADO[id];
    if (!e) { falhas.push(`bilhete inesperado na fixture: ${id}`); continue; }
    const txt = fmt(b);
    testes++;

    if (!txt.startsWith(`[Código: ${id}]`)) falhas.push(`${id}: marcador [Código:] ausente/errado na 1ª linha`);

    const evento = linha(txt, "Data (evento mais recente):");
    if (evento !== e.evento) falhas.push(`${id}: data do EVENTO esperada ${e.evento}, veio "${evento}"`);

    const colocacao = linha(txt, "Data (colocação):");
    if (colocacao !== e.colocacao) falhas.push(`${id}: colocação esperada ${e.colocacao}, veio "${colocacao}"`);

    const stake = linha(txt, "Stake:");
    if (stake !== "R$ " + e.stake) falhas.push(`${id}: stake esperada R$ ${e.stake}, veio "${stake}"`);

    const status = linha(txt, "Status:");
    if (!e.status.test(status)) falhas.push(`${id}: status "${status}"`);

    if (!/status=\w+/.test(linha(txt, "Status (API):")))
      falhas.push(`${id}: faltou o enum cru na linha "Status (API):"`);

    const odd = linha(txt, "Odd:").split(" ")[0];
    if (odd !== e.odd) falhas.push(`${id}: odd esperada ${e.odd}, veio "${odd}"`);

    const tipo = linha(txt, "Tipo:");
    if (!e.tipo.test(tipo)) falhas.push(`${id}: tipo "${tipo}"`);

    if (!txt.includes(e.jogo)) falhas.push(`${id}: o jogo "${e.jogo}" não aparece no bloco — veio do detalhe?`);

    // ⚠️ A casa NÃO informa esporte em campo nenhum (só `championship` e `country`). O bloco
    // tem de dizer isso explicitamente, senão a IA inventa a coluna Esporte em silêncio.
    const esp = linha(txt, "Esporte:");
    if (!/não informad/i.test(esp))
      falhas.push(`${id}: "Esporte:" devia declarar que a casa não informa, veio "${esp}"`);

    if (e.retorno) {
      const r = linha(txt, "Retorno:");
      if (r !== "R$ " + e.retorno) falhas.push(`${id}: retorno esperado R$ ${e.retorno}, veio "${r}"`);
    }

    // O CORAÇÃO DO CASO: na PERDIDA, o campo de dinheiro é potencial e NÃO pode sair como
    // "Retorno:". Se sair, a IA lê lucro onde houve prejuízo — 114 linhas da conta.
    if (e.potencialMentiroso) {
      if (linha(txt, "Retorno:"))
        falhas.push(`${id}: PERDIDA emitiu "Retorno:" — o campo é potencial (${e.potencialMentiroso}), não dinheiro recebido`);
      if (/Ganho → W/.test(txt)) falhas.push(`${id}: PERDIDA virou vitória`);
      // Exige o valor E o aviso na mesma linha: o número sozinho não protege ninguém — é a
      // frase que impede a IA de ler 125 como dinheiro recebido numa aposta perdida.
      const pot = linha(txt, "Retorno potencial:");
      if (!pot.startsWith("R$ " + e.potencialMentiroso))
        falhas.push(`${id}: esperava "Retorno potencial: R$ ${e.potencialMentiroso}…", veio "${pot}"`);
      if (!/POTENCIAL|não é ganho/i.test(pot))
        falhas.push(`${id}: a linha do potencial não avisa que o valor NÃO é ganho — o número sozinho engana`);
    }
  }

  // ── CONTROLE NEGATIVO ─────────────────────────────────────────────────────────
  {
    const perdida = JSON.parse(fixture("lottu.detalhes.json")).find((b) => b.status === "LOST");
    testes++;
    // (a) o MESMO bilhete, com status WON, TEM de virar W com "Retorno:" — se não virar, a
    //     asserção da perdida não estava provando nada.
    const comoW = fmt({ ...perdida, status: "WON" });
    if (!/Ganho → W/.test(comoW) || !linha(comoW, "Retorno:"))
      falhas.push("controle negativo: o bilhete com status=WON não virou W com 'Retorno:' — o teste da PERDIDA era vácuo");

    testes++;
    // (b) estado fora de {WON,LOST,OPEN,...} sobe CRU e marcado. Aqui isso pesa mais que em
    //     qualquer outra casa: como o dinheiro vem preenchido em TODA linha, um estado
    //     desconhecido tratado pelo dinheiro viraria W automático.
    const inedito = fmt({ ...perdida, status: "CASHED_OUT" });
    if (!/a conferir/.test(inedito)) falhas.push("estado desconhecido não foi marcado 'a conferir' — vira chute");
    if (/Ganho → W|Perdeu → L/.test(inedito)) falhas.push("estado desconhecido foi convertido em resultado — proibido");
  }

  return { falhas, testes };
}
