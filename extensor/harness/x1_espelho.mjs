// Conferência comum das casas ESPELHO da 1xBet (s391): SapphireBet, PariPesa e Megapari.
//
// As três servem o MESMO `GetBetInfoHistoryWithSummaryByDates` da 1xBet, com o MESMO JSON
// (`{BetInfos, BetsSummaryInfo}`), num caminho diferente: `/bethistory-api/Web/` no lugar de
// `/service/bethistory/`. Recon de 03/10/2026, uma conta do Feca em cada casa. As três falam
// em dólar (SapphireBet em USD, as outras em USDT): é a moeda que este arquivo mais trava.
//
// Fica FORA de `casos/` de propósito: o `run.mjs` roda todo `.mjs` de lá como caso.
//
// O que cada caso trava, além do que a 1xBet já trava:
//   • o inject CASA o caminho novo (sem isso a captura fica muda, sem erro nenhum);
//   • `Moeda: <moeda>` no bloco e NENHUM "R$" — dinheiro rotulado como real numa conta em dólar
//     é a stake que o servidor converteria de novo;
//   • o carimbo de colocação (`AAAAMMDDhhmmss`, São Paulo), que decide o dia da cotação;
//   • controle negativo: o mesmo bilhete com `BRL` volta ao bloco de sempre (sem `Moeda:`,
//     sem carimbo, com "R$") — casa em real fica byte a byte igual.
//
// NÃO coberto: troca de domínio do espelho (é o popup e o manifest, não o inject) e a
// conversão em R$ (é do servidor, `tests/test_moeda_captura.py`).
import { rodarInject, carregarContent, fixture, linha } from "./sandbox.mjs";

export async function conferirEspelho({ arquivo, href, url, moeda, esperado, carimbo }) {
  const payload = JSON.parse(fixture(arquivo));
  const TODOS = payload.BetInfos;
  const DIA = 86400;
  const AGORA = Math.floor(Date.parse("2026-10-03T12:00:00Z") / 1000);
  const corpoInicial = JSON.stringify({
    BetStatuses: [], BetTypes: [], BonusUserId: 0, CfView: 3, Count: 300,
    DateFrom: AGORA - 7 * DIA, DateTo: AGORA, Language: "br", PartnerGroupId: 1, PartnerId: 1,
    SortType: 0,
  });

  const pedidos = [];
  const responder = (u) => {
    if (!/\/bethistory-api\/Web\/GetBetInfoHistoryWithSummaryByDates/.test(String(u))) return null;
    pedidos.push(String(u));
    return JSON.stringify({ BetsSummaryInfo: { Count: TODOS.length }, BetInfos: TODOS });
  };

  const { ultima } = await rodarInject({
    inject: "x1_inject.js",
    href,
    urlInicial: url,
    optsInicial: { method: "POST", headers: { "accept": "application/json", "content-type": "application/json" }, body: corpoInicial },
    pedido: "__sharpenupX1Req",
    responder,
    ms: 900,
  });

  const falhas = [];
  if (!ultima) return { falhas: ["o inject não emitiu nenhuma mensagem — o caminho `/bethistory-api/Web/` não casou"], testes: 0 };
  if (!ultima.hook) falhas.push("o inject não emitiu `hook:true`");
  if (!ultima.fim) falhas.push("o inject não sinalizou `fim`");
  const bilhetes = ultima.bilhetes || [];
  if (bilhetes.length !== TODOS.length) falhas.push(`esperava ${TODOS.length} bilhetes, vieram ${bilhetes.length}`);

  const fmt = carregarContent().pegar("formatTicket1X");
  let testes = 0;
  for (const b of bilhetes) {
    const txt = fmt(b);
    // ── moeda, em TODO bilhete ──
    if (linha(txt, "Moeda:") !== moeda) falhas.push(`${b.ref}: faltou "Moeda: ${moeda}"`);
    if (/R\$/.test(txt)) falhas.push(`${b.ref}: bloco em ${moeda} com "R$" — o servidor converteria de novo`);
    if (!/^\d{14}$/.test(linha(txt, "Carimbo de colocação:") || "")) falhas.push(`${b.ref}: carimbo de colocação ausente`);

    const e = esperado[b.ref];
    if (!e) continue;
    testes++;
    if (!txt.startsWith(`[Código: ${b.ref}]`)) falhas.push(`${b.ref}: marcador [Código:] ausente/errado`);
    if (linha(txt, "Stake:") !== e.stake) falhas.push(`${b.ref}: stake esperada ${e.stake}, veio "${linha(txt, "Stake:")}"`);
    const odd = linha(txt, "Odd:");
    if (e.odd === null) {
      if (!/VAZIA/.test(odd || "")) falhas.push(`${b.ref}: sistema sem cotação tinha de dizer a odd VAZIA, veio "${odd}"`);
    } else if (odd !== e.odd && odd !== `${e.odd} (= Retorno ÷ Stake)`) {
      falhas.push(`${b.ref}: odd esperada ${e.odd}, veio "${odd}"`);
    }
    const st = linha(txt, "Status:");
    if (!e.status.test(st)) falhas.push(`${b.ref}: status "${st}"`);
    if (e.evento && linha(txt, "Data (evento):") !== e.evento) {
      falhas.push(`${b.ref}: evento esperado ${e.evento}, veio "${linha(txt, "Data (evento):")}"`);
    }
    if (e.tipo && !e.tipo.test(linha(txt, "Tipo:") || "")) falhas.push(`${b.ref}: tipo "${linha(txt, "Tipo:")}"`);
    if (e.retorno && linha(txt, "Retorno:") !== `${e.retorno} ${moeda}`) {
      falhas.push(`${b.ref}: retorno esperado ${e.retorno} ${moeda}, veio "${linha(txt, "Retorno:")}"`);
    }
    if (e.potencial) {
      const pot = linha(txt, "Retorno potencial:") || "";
      if (!pot.startsWith(`${e.potencial} ${moeda}`)) falhas.push(`${b.ref}: potencial esperado ${e.potencial} ${moeda}, veio "${pot}"`);
      if (linha(txt, "Retorno:")) falhas.push(`${b.ref}: bilhete ABERTO emitiu "Retorno:"`);
    }
  }

  // ── carimbo exato num bilhete conferido à mão (UTC → São Paulo) ──
  const alvo = bilhetes.find((b) => b.ref === carimbo.ref);
  const c = alvo ? linha(fmt(alvo), "Carimbo de colocação:") : null;
  if (c !== carimbo.valor) falhas.push(`${carimbo.ref}: carimbo esperado ${carimbo.valor}, veio "${c}"`);
  testes++;

  // ── controle negativo: o mesmo bilhete em real volta ao bloco de sempre ──
  if (alvo) {
    const real = fmt(Object.assign({}, alvo, { moeda: "BRL" }));
    if (linha(real, "Moeda:")) falhas.push("bilhete em BRL ganhou linha \"Moeda:\"");
    if (linha(real, "Carimbo de colocação:")) falhas.push("bilhete em BRL ganhou carimbo — casa em real deixaria de ser byte a byte igual");
    if (!/R\$/.test(real)) falhas.push("bilhete em BRL perdeu o \"R$\"");
  }
  testes++;

  if (!pedidos.length) falhas.push("o replay não pediu nada no caminho `/bethistory-api/Web/`");
  return { falhas, testes };
}
