// Esportiva (Altenar / BIA) — ESPELHO da VaideBet (s254).
//
// A Esportiva não tem inject, formatador nem robô próprios: ela reusa `vb_inject.js`,
// `formatTicketVB` e `roboVBPassive`, como a Betfast reusa os da Tivo e a Betboom os da
// Jonbet. Este caso existe justamente porque o compartilhamento é a parte perigosa — ele
// prova que o MESMO código lê a OUTRA casa contra o card DELA, e não que "deve funcionar
// porque é igual".
//
// O que sustenta o espelho, MEDIDO no recon ao vivo (09/08/2026) e não deduzido:
//   • a home carrega `sb2frontend-altenar2.biahosted.com` com `integration=esportiva` —
//     dá para confirmar o motor SEM login, como no BetBy;
//   • o histórico sai do MESMO endpoint, no MESMO host de gateway:
//     `POST https://sb2bethistory-gateway-altenar2.biahosted.com/api/WidgetReports/widgetExpandedBetHistory`
//     — e o `RX` do inject casa por PATH (`/widgetExpandedBetHistory`), sem citar host nenhum;
//   • mesmos arrays `statuses` no corpo (Aberto `[0,10,3,20,17]` · Processado `[1,8,2,4,18]`),
//     mesmo `pageNumber`/`pageSize:10`, mesmo fim autoritativo `isLastPage`;
//   • paginação provada AO VIVO nesta conta: `pageNumber:2` devolveu 10 ids novos, nenhum
//     repetido, com `isLastPage:false` (ainda havia mais);
//   • mesmo enum, conferido contra a faixa do card: 0=ABERTO · 1=GANHOU/VENCIDO · 2=PERDIDO.
//
// A ARMADILHA DA CASA se reproduz inteira, e o card é a prova: as 3 ABERTAS estampam
// "Ganho total R$54,00 / R$47,10 / R$125,00" com o jogo ainda rolando (60' , placar 1:0).
// É retorno POTENCIAL. Lê-lo como realizado viraria vitória fantasma em toda aposta em
// aberto — o incidente que a VaideBet levou a produção na s210. Só `status:1` autoriza
// `retorno ÷ stake`.
//
// E o cashout repete o mesmo silêncio da VaideBet: os 2 bilhetes abertos com botão
// "Cashout R$37,25" / "R$23,31" na tela vêm com `cashOutValue: 0.0` no payload (o valor
// oferecido mora em `GetOpenBetsCashoutValues`, outro endpoint). Ou seja: oferta de venda
// NÃO aparece aqui — e é bom que não apareça, senão viraria "Cash Out" num bilhete aberto.
import { rodarInject, carregarContent, fixture, linha } from "../sandbox.mjs";

export const casa = "Esportiva";

// Cada valor abaixo foi lido do CARD da Esportiva (aba Processado/Aberto de 09/08/2026,
// com "Expandir tudo" ligado), não do código.
//
// `evento` é a data que VAI PARA A COLUNA DATA do TSV (`MASTER_OUTPUT §4`) — o card a
// estampa no bloco branco ("09/08 • 16:00"). `data` é a colocação, do rodapé cinza
// ("09/08 • 11:56"). `odd` é a "Cotações totais". `pre` é o riscado do boost, que a tela
// TRUNCA (1.625 → "1.62"): o bloco tem de emitir o valor cheio.
const ESPERADO = {
  // ── resolvidas (aba Processado) ────────────────────────────────────────────────
  "5277994379": { evento: "09/08/2026 16:00:00", data: "09/08/2026 11:56:33", odd: "1,8",  stake: "30,00",  status: /^Perdeu → L$/,  tipo: /^Simples$/, pre: "1,625", tela: "1.62" },
  "5277928754": { evento: "09/08/2026 18:30:00", data: "09/08/2026 11:38:13", odd: "1,65", stake: "30,00",  status: /^Ganho → W/,    tipo: /^Simples$/, pre: "1,48",  retorno: "49,50" },
  "5277915894": { evento: "09/08/2026 18:30:00", data: "09/08/2026 11:35:04", odd: "2",    stake: "30,00",  status: /^Perdeu → L$/,  tipo: /^Simples$/, pre: "1,8889", tela: "1.88" },
  "5277908099": { evento: "09/08/2026 18:30:00", data: "09/08/2026 11:33:10", odd: "1,6",  stake: "30,00",  status: /^Perdeu → L$/,  tipo: /^Bet Builder \(mesmo jogo · 2 seleções\)$/ },
  "5277888002": { evento: "09/08/2026 18:30:00", data: "09/08/2026 11:27:56", odd: "1,75", stake: "30,00",  status: /^Perdeu → L$/,  tipo: /^Bet Builder \(mesmo jogo · 2 seleções\)$/ },
  "5277883199": { evento: "09/08/2026 16:00:00", data: "09/08/2026 11:26:19", odd: "1,65", stake: "30,00",  status: /^Perdeu → L$/,  tipo: /^Bet Builder \(mesmo jogo · 2 seleções\)$/ },
  "5277875995": { evento: "09/08/2026 16:00:00", data: "09/08/2026 11:23:59", odd: "1,6",  stake: "30,00",  status: /^Perdeu → L$/,  tipo: /^Simples$/ },
  "5277868049": { evento: "09/08/2026 16:00:00", data: "09/08/2026 11:21:36", odd: "1,6",  stake: "30,00",  status: /^Perdeu → L$/,  tipo: /^Simples$/ },
  "5277858243": { evento: "09/08/2026 16:00:00", data: "09/08/2026 11:18:49", odd: "1,6",  stake: "30,00",  status: /^Perdeu → L$/,  tipo: /^Bet Builder \(mesmo jogo · 2 seleções\)$/ },
  // O W de stake alta: o card mostra "Valor total de aposta R$124.00 · Ganho total R$198.40".
  "5277832732": { evento: "09/08/2026 16:00:00", data: "09/08/2026 11:10:09", odd: "1,6",  stake: "124,00", status: /^Ganho → W/,    tipo: /^Simples$/, pre: "1,48", retorno: "198,40" },

  // ── abertas (aba Aberto) ──────────────────────────────────────────────────────
  "5277937480": { evento: "09/08/2026 19:30:00", data: "09/08/2026 11:40:34", odd: "1,8",  stake: "30,00", status: /em aberto/, tipo: /^Simples$/, aberta: true, potencial: "54,00", pre: "1,6364", tela: "1.63" },
  "5277934164": { evento: "09/08/2026 19:30:00", data: "09/08/2026 11:39:42", odd: "1,57", stake: "30,00", status: /em aberto/, tipo: /^Bet Builder \(mesmo jogo · 2 seleções\)$/, aberta: true, potencial: "47,10", pre: "1,4167", tela: "1.41" },
  // ⚠ DIA DIFERENTE: colocada 08/08 23:50, jogo em 09/08 19:30. É o bilhete que prova, NESTA
  // casa, por que a coluna Data sai do evento e não da colocação — travar só a colocação
  // poria esta linha no dia errado.
  "5276761434": { evento: "09/08/2026 19:30:00", data: "08/08/2026 23:50:35", odd: "2,5",  stake: "50,00", status: /em aberto/, tipo: /^Simples$/, aberta: true, potencial: "125,00", pre: "2,05" },
};

// Os 2 abertos que a tela oferece cashout (botão verde), mas cujo payload traz
// `cashOutValue: 0.0`. Se um dia o campo passar a vir preenchido no bilhete ABERTO, este
// caso acusa — é oferta de venda, não liquidação (a lição da Betboom, s250).
const ABERTO_COM_OFERTA_DE_CASHOUT = ["5277937480", "5277934164"];

// Corpos que a página da Esportiva emite ao abrir cada aba (colados do Payload real do F12
// desta conta — repare no `"integration":"esportiva"`, a única diferença para a VaideBet).
const CORPO_RESOLVIDAS = '{"culture":"pt-BR","timezoneOffset":180,"integration":"esportiva","deviceType":1,"countryCode":"BR","dateFrom":"2026-07-30T03:00:00.000Z","dateTo":"2026-08-10T02:59:59.999Z","liveOnly":false,"numFormat":"en-GB","pageNumber":1,"pageSize":10,"statuses":[1,8,2,4,18]}';
const CORPO_ABERTAS   = '{"culture":"pt-BR","timezoneOffset":180,"integration":"esportiva","deviceType":1,"countryCode":"BR","dateFrom":"2026-07-30T03:00:00.000Z","dateTo":"2026-08-10T02:59:59.999Z","liveOnly":false,"numFormat":"en-GB","pageNumber":1,"pageSize":10,"statuses":[0,10,3,20,17]}';

const URL_API = "https://sb2bethistory-gateway-altenar2.biahosted.com/api/WidgetReports/widgetExpandedBetHistory";
const HREF = "https://esportiva.bet.br/sports/my-bets";

// Servidor de mentira: responde pelo `statuses` e pelo `pageNumber` do corpo, como a casa
// faz. A página 1 das resolvidas volta `isLastPage:false` (é o valor REAL da resposta desta
// conta) → o inject TEM de pedir a página 2.
function servidor() {
  const resolvidas = fixture("esportiva.settled.json");   // 10 bilhetes · isLastPage:false
  const abertas = fixture("esportiva.open.json");         //  3 bilhetes · isLastPage:true
  const pedidos = [];
  const resp = (url, opts) => {
    const body = String((opts && opts.body) || "");
    if (!url.includes("widgetExpandedBetHistory")) return null;
    pedidos.push(body);
    let o = null;
    try { o = JSON.parse(body); } catch (e) { return null; }
    const sts = Array.isArray(o.statuses) ? o.statuses : [];
    const pag = Number(o.pageNumber) || 1;
    if (sts.includes(0)) return pag === 1 ? abertas : JSON.stringify({ isLastPage: true, bets: [] });
    if (pag === 1) return resolvidas;
    return JSON.stringify({ isLastPage: true, bets: [] });
  };
  return { resp, pedidos };
}

async function umClique(corpoInicial, href) {
  const srv = servidor();
  const { ultima, urls } = await rodarInject({
    inject: "vb_inject.js",          // ← o MESMO da VaideBet, sem uma linha de diferença
    href: href || HREF,
    urlInicial: URL_API,
    corpoInicial: corpoInicial,
    pedido: "__sharpenupVBReq",
    ms: 1200,
    responder: srv.resp,
  });
  return { ultima, pedidos: srv.pedidos, urls };
}

export async function rodar() {
  const falhas = [];
  let testes = 0;

  // ── 1. Um clique = as duas listas, partindo de QUALQUER aba ───────────────────
  let colhido = null;
  for (const [rotulo, corpo] of [["aba Processado", CORPO_RESOLVIDAS], ["aba Aberto", CORPO_ABERTAS]]) {
    const { ultima, pedidos } = await umClique(corpo);
    testes++;
    if (!ultima) { falhas.push(`${rotulo}: o inject não emitiu nenhuma mensagem`); continue; }
    if (!ultima.hook) falhas.push(`${rotulo}: o inject não sinalizou 'hook' rodando em esportiva.bet.br (autodiagnóstico cego)`);
    if (typeof ultima.respostas !== "number" || ultima.respostas < 1)
      falhas.push(`${rotulo}: 'respostas' não foi reportado — não dá para separar "não injetei" de "endpoint mudou"`);

    const bets = ultima.bets || [];
    if (bets.length !== 13) falhas.push(`${rotulo}: esperava 13 bilhetes (10 resolvidas + 3 abertas), vieram ${bets.length}`);
    if (!ultima.fim) falhas.push(`${rotulo}: não sinalizou 'fim' — o robô ficaria esperando o teto`);

    // A página 2 das resolvidas só é pedida se a paginação ativa funcionar. Ela existe DE
    // VERDADE nesta conta (o recon confirmou 10 ids novos na pág. 2) — sem isto o lote
    // pararia nos 10 primeiros e ninguém saberia.
    const p2 = pedidos.find((b) => { try { const o = JSON.parse(b); return o.pageNumber === 2 && !o.statuses.includes(0); } catch (e) { return false; } });
    if (!p2) falhas.push(`${rotulo}: nenhuma requisição pediu a página 2 das resolvidas — paginação ativa não avançou`);
    else if (!/"pageSize"\s*:\s*10/.test(p2)) falhas.push(`${rotulo}: pageSize foi corrompido ao avançar a página → ${p2}`);

    const temAbertas = pedidos.some((b) => { try { return JSON.parse(b).statuses.includes(0); } catch (e) { return false; } });
    const temResolvidas = pedidos.some((b) => { try { return JSON.parse(b).statuses.includes(1); } catch (e) { return false; } });
    if (!temAbertas) falhas.push(`${rotulo}: nunca pediu a aba ABERTA (statuses com 0) — aposta em aberto sumiria`);
    if (!temResolvidas) falhas.push(`${rotulo}: nunca pediu a aba PROCESSADO (statuses com 1)`);

    if (!colhido && bets.length) colhido = bets;
  }

  if (!colhido) return { falhas: falhas.concat(["nenhum bilhete colhido — o resto do caso não roda"]), testes };

  // ── 2. Leitura bilhete a bilhete, contra o card DA ESPORTIVA ──────────────────
  const fmt = carregarContent().pegar("formatTicketVB");   // ← formatador compartilhado
  for (const b of colhido) {
    const id = String(b.id);
    const e = ESPERADO[id];
    if (!e) { falhas.push(`bilhete inesperado na fixture: ${id}`); continue; }
    const txt = fmt(b);
    testes++;

    if (!txt.startsWith(`[Código: ${id}]`)) falhas.push(`${id}: marcador [Código:] ausente/errado na 1ª linha`);

    const evento = linha(txt, "Data (evento mais recente):");
    if (evento !== e.evento) falhas.push(`${id}: data do EVENTO esperada ${e.evento}, veio "${evento}" (é ela que vai para a coluna Data do TSV)`);

    const data = linha(txt, "Data (colocação):");
    if (data !== e.data) falhas.push(`${id}: colocação esperada ${e.data}, veio "${data}"`);

    const stake = linha(txt, "Stake:");
    if (stake !== "R$ " + e.stake) falhas.push(`${id}: stake esperada R$ ${e.stake}, veio "${stake}"`);

    const status = linha(txt, "Status:");
    if (!e.status.test(status)) falhas.push(`${id}: status "${status}"`);

    // Enum CRU da casa — é ele que a CASA_ESPORTIVA.md traduz.
    if (!/status=\d+/.test(linha(txt, "Status (API):")))
      falhas.push(`${id}: faltou o enum cru na linha "Status (API):" — um estado novo viraria chute`);

    const odd = linha(txt, "Odd:").split(" ")[0];
    if (odd !== e.odd) falhas.push(`${id}: odd esperada ${e.odd}, veio "${odd}"`);

    const tipo = linha(txt, "Tipo:");
    if (!e.tipo.test(tipo)) falhas.push(`${id}: tipo "${tipo}"`);

    // Toda a amostra desta conta é futebol (`sportTypeId 1`). O rótulo é copiado pela IA
    // para a coluna Esporte: se não for o valor OFICIAL do MASTER_ESPORTES, o mesmo esporte
    // entra no banco com duas grafias (foi o "Beisebol" × "Baseball" da VaideBet, s210).
    const esp = linha(txt, "Esporte:");
    if (!/^Futebol\b/.test(esp)) falhas.push(`${id}: esporte "${esp}" não é o valor oficial do MASTER_ESPORTES`);

    // Boost: TODOS os 13 bilhetes desta conta são "TURBINADA" (`boostProperty: 3`). A odd
    // válida é a boostada (`totalOdds`); o riscado do card é `preBoostedPrice` e a tela
    // TRUNCA (1.625 → "1.62"). O bloco tem de emitir o valor cheio, nunca o da tela.
    if (e.pre) {
      const marca = txt.split("\n").find((l) => l.startsWith("Marcação da casa: odd turbinada")) || "";
      if (!marca) {
        falhas.push(`${id}: bilhete turbinado sem a marcação de boost — a IA não saberia que o riscado do card não é a odd`);
      } else {
        // Comparação EXATA, não `includes`: "1,62" é prefixo de "1,625" e um `includes`
        // daria vermelho no valor certo (e verde no truncado, que é o erro que importa).
        const m = /antes do boost ([\d,]+)/.exec(marca);
        const emitida = m ? m[1] : "";
        if (emitida !== e.pre) falhas.push(`${id}: odd pré-boost esperada ${e.pre}, veio "${emitida}"`);
        if (e.tela && emitida === e.tela.replace(".", ",")) {
          falhas.push(`${id}: emitiu a odd pré-boost TRUNCADA do card (${e.tela}) em vez do valor cheio ${e.pre}`);
        }
      }
    }

    if (e.retorno) {
      const r = linha(txt, "Retorno:");
      if (r !== "R$ " + e.retorno) falhas.push(`${id}: retorno esperado R$ ${e.retorno}, veio "${r}"`);
      // A odd do W tem de explicar o retorno do card até o centavo.
      const n = Number(e.odd.replace(",", "."));
      const st = Number(e.stake.replace(".", "").replace(",", "."));
      const ret = Number(e.retorno.replace(".", "").replace(",", "."));
      if (!(Math.abs(n * st - ret) <= 0.01)) falhas.push(`${id}: odd ${e.odd} × stake ${e.stake} não explica o retorno ${e.retorno} do card`);
    }

    if (e.aberta) {
      // O CORAÇÃO DESTA CASA: `totalWin` de uma aberta é POTENCIAL. O 5276761434 tem stake
      // 50 e totalWin 125 — se escorregar para a regra do W, vira lucro fantasma de R$ 75.
      if (/→ [WLV]\b/.test(status)) falhas.push(`${id}: aberta recebeu código de resultado — proibido`);
      if (/Ganho → W/.test(txt)) falhas.push(`${id}: ABERTA virou vitória — totalWin foi lido como retorno realizado`);
      const pot = linha(txt, "Retorno potencial:");
      if (pot !== "R$ " + e.potencial) falhas.push(`${id}: retorno potencial esperado R$ ${e.potencial}, veio "${pot}"`);
      if (linha(txt, "Retorno:")) falhas.push(`${id}: aberta emitiu linha "Retorno:" — só potencial é permitido`);
      // Oferta de cashout em bilhete ABERTO não pode virar cashout executado.
      if (ABERTO_COM_OFERTA_DE_CASHOUT.includes(id) && /Cash *Out/i.test(txt)) {
        falhas.push(`${id}: emitiu "Cash Out" num bilhete ABERTO — o botão da tela é oferta de venda, não liquidação`);
      }
    }
  }

  // ── 3. CONTROLE NEGATIVO ──────────────────────────────────────────────────────
  // Caso espelho passa verde de primeira, e isso NÃO é evidência. Aqui provamos que as duas
  // asserções centrais têm dente: se o código deixasse de distinguir aberta de resolvida, o
  // bloco mudaria — e é essa mudança que o teste acima detecta.
  {
    const abertaCrua = JSON.parse(fixture("esportiva.open.json")).bets.find((b) => String(b.id) === "5276761434");
    testes++;
    // (a) o MESMO bilhete, com status 1, tem de sair como W com "Retorno:" — se sair igual
    //     ao aberto, a asserção da aberta era vácuo.
    const comoResolvido = fmt({ ...abertaCrua, status: 1 });
    if (!/Ganho → W/.test(comoResolvido) || !linha(comoResolvido, "Retorno:")) {
      falhas.push("controle negativo: o bilhete com status=1 não virou W com 'Retorno:' — " +
                  "o teste da ABERTA não estava provando nada");
    }
    testes++;
    // (b) status fora de {0,1,2} sobe CRU e marcado — nunca vira W/L pelo dinheiro.
    const desconhecido = fmt({ ...abertaCrua, status: 17 });
    if (!/a conferir/.test(desconhecido)) falhas.push("status desconhecido (17) não foi marcado 'a conferir' — vira chute");
    if (/Ganho → W|Perdeu → L/.test(desconhecido)) falhas.push("status desconhecido (17) foi convertido em resultado — proibido");
  }

  // ── 4. O bloco da Esportiva é IDÊNTICO ao da VaideBet — é isso que "espelho" quer dizer ──
  // Roda a MESMA fixture pelos dois hosts e compara byte a byte. Se um dia alguém amarrar o
  // inject ou o formatador ao domínio, isto acusa na hora.
  {
    const { ultima: pelaVB } = await umClique(CORPO_RESOLVIDAS,
      "https://www.vaidebet.bet.br/sports?shareCode=IHLBJGT77FZ#/betHistory");
    const vb = new Map(((pelaVB && pelaVB.bets) || []).map((b) => [String(b.id), b]));
    const es = new Map(colhido.map((b) => [String(b.id), b]));
    testes++;
    if (vb.size !== es.size) {
      falhas.push(`espelho: host vaidebet capturou ${vb.size} e host esportiva ${es.size} — a captura não pode depender do domínio`);
    } else {
      const diferentes = [];
      for (const [id, b] of es) {
        const o = vb.get(id);
        if (!o || fmt(o) !== fmt(b)) diferentes.push(id);
      }
      if (diferentes.length) {
        falhas.push(`espelho: ${diferentes.length} bloco(s) diferem entre os dois hosts (${diferentes.slice(0, 3).join(", ")}…)`);
      }
    }
  }

  // ── 5. ANULADA (`status 8`) e o órfão (`status 7`) — bilhetes REAIS, s285 ─────
  // Medido na conta anapetry03 em 23/08/2026: 250 bilhetes de 2026 inteiro trazem SÓ os
  // enums 0, 1, 2, 7 e 8. Os quatro `status:8` são anulações de verdade — a faixa do card
  // diz ANULADA e o "Ganho total" repete o "Valor total de aposta". Até a s285 eles subiam
  // como "a conferir": a IA devolvia resultado vazio, a linha nascia "aguardando" e ficava
  // assim para sempre, porque toda recaptura repetia o mesmo bloco.
  //
  // Detalhe que engana quem for conferir na tela: a casa lista as anuladas dentro do filtro
  // **Ganho** (`statuses:[1,8]`), não num filtro de anuladas.
  {
    const anuladas = JSON.parse(fixture("esportiva.anuladas.json")).bets;
    // Devolução = o "Ganho total" do card, que nas 4 é idêntico ao "Valor total de aposta".
    const DEVOLUCAO = { "5317731393": "1,00", "5306439522": "124,00", "5296262805": "100,00", "5281584944": "30,00" };
    for (const b of anuladas) {
      const id = String(b.id);
      const txt = fmt(b);
      const st = linha(txt, "Status:");
      testes++;

      if (id === "5310191599") {
        // O ÓRFÃO. `status 7`, as DUAS pernas do bet builder ganhas (`status 1`, placar 2:1)
        // e ainda assim `totalWin: 0` — sem cashout. É o contraexemplo que proíbe deduzir
        // desfecho pelo dinheiro: uma régua "retorno 0 → L" o marcaria como perda, e uma
        // "pernas ganhas → W" o marcaria como ganho. Nenhuma das duas tem prova.
        if (!/a conferir/.test(st)) falhas.push(`${id}: status 7 não foi marcado "a conferir" — vira chute`);
        if (/→ [WLV]\b/.test(st)) falhas.push(`${id}: status 7 recebeu código de resultado — proibido`);
        continue;
      }

      if (st !== "Anulada/void (stake devolvido) → V")
        falhas.push(`${id}: anulada devia sair "Anulada/void (stake devolvido) → V", veio "${st}"`);

      // A odd do V é a EXIBIDA no card (`MASTER_RESULTADO §5.1.2`), nunca 1,00. Se o bloco
      // chamasse a devolução de "Retorno", a IA aplicaria retorno ÷ stake e gravaria 1,00 —
      // o 5317731393 (odd 51,42) mostra o tamanho do estrago.
      const odd = linha(txt, "Odd:").split(" ")[0];
      const oddCard = String(Math.round(b.totalOdds * 1e8) / 1e8).replace(".", ",");
      if (odd !== oddCard) falhas.push(`${id}: odd da anulada esperada ${oddCard} (a exibida), veio "${odd}"`);
      if (linha(txt, "Retorno:")) falhas.push(`${id}: anulada emitiu "Retorno:" — é devolução de stake, não ganho`);
      const dev = linha(txt, "Devolução do stake:");
      if (dev !== "R$ " + DEVOLUCAO[id] + " (aposta anulada — não é ganho)")
        falhas.push(`${id}: devolução esperada "R$ ${DEVOLUCAO[id]} (aposta anulada — não é ganho)", veio "${dev}"`);
      if (!/status=8/.test(linha(txt, "Status (API):")))
        falhas.push(`${id}: perdeu o enum cru na linha "Status (API):" — o de-para da casa fica cego`);
    }

    // A rede de segurança do PRÓXIMO enum: processado + retorno = stake → V. E o limite dela,
    // que é o que impede a vitória fantasma de voltar por outra porta: o MESMO dinheiro num
    // enum da família ABERTA (17) continua sem liquidar, porque ali `totalWin` é potencial.
    const base = anuladas.find((b) => String(b.id) === "5296262805");
    testes++;
    const inedito = fmt({ ...base, status: 4 });
    if (!/→ V$/.test(linha(inedito, "Status:")))
      falhas.push("rede de segurança: status 4 (processado) com retorno = stake não virou V");
    testes++;
    const aberto = fmt({ ...base, status: 17 });
    if (/→ [WLV]\b/.test(linha(aberto, "Status:")))
      falhas.push("status 17 é da família ABERTA (totalWin é potencial) e não pode liquidar por retorno = stake");
  }

  // ── 6. O `status 7` tem de ser PEDIDO, senão o bilhete não existe ─────────────
  // Ele não está em nenhum dos cinco filtros da casa (Aberto `[0,10,3,20,17]` · Processado
  // `[1,8,2,4,18]` · Ganho `[1,8]` · Perdida `[2]` · Cashout `[4,18]`): sem pedi-lo de
  // propósito, o bilhete some da captura E da tela, sem erro nenhum. O gateway aceita o valor
  // extra (medido ao vivo: `statuses:[7,8]` devolveu os dois).
  {
    const { pedidos } = await umClique(CORPO_RESOLVIDAS);
    testes++;
    const pediu7 = pedidos.some((b) => {
      try { return (JSON.parse(b).statuses || []).includes(7); } catch (e) { return false; }
    });
    if (!pediu7) falhas.push("nenhuma requisição pediu `status 7` — bilhete nesse estado sumiria em silêncio");
  }

  return { falhas, testes };
}
