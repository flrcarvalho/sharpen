// Betano — roteamento POR ABA do robô passivo (`roboBetanoPassive`), s209.
//
// ARMADILHA TRAVADA AQUI: `bnById` é acumulador da SESSÃO DA PÁGINA. A Betano é SPA — trocar
// "Liquidada" ↔ "Em aberto" NÃO recarrega, então o hook guarda as duas listas ao mesmo tempo.
// Até a s209 o `processar()` varria o mapa inteiro, e rodar na aba "Em aberto" depois de ter
// passado pela "Liquidada" exportava as duas juntas (caso real: 25 bilhetes = as 5 abertas
// corretas + 20 liquidadas que sobraram em memória). Dois estragos:
//   • token à toa — o pré-dedup do `/extrair` só descarta o que já está RESOLVIDO no banco;
//   • perda SILENCIOSA das abertas — o mapa é percorrido em ordem de inserção; com o campo
//     "parar no ID" preenchido com um bilhete LIQUIDADO, o `travado` disparava antes de chegar
//     nas abertas e elas não saíam, sem erro nenhum na tela.
//
// Este caso é de ROTEAMENTO, não de parsing: alimenta o `bnById` direto e confere QUAIS
// bilhetes saem em cada aba. Os valores de cada campo (odd, data, boost, Criar Aposta) ainda
// não estão travados — falta a fixture real do `GET /api/ma/bet/bet-history-v3` (F12 → Network
// → Copy response). Quando ela existir, este arquivo ganha a parte de valores, como na Tivo.
//
// Os bilhetes abaixo são os do caso real, reduzidos aos campos que o roteamento usa.
import { carregarContent, linha } from "../sandbox.mjs";

export const casa = "Betano";

const ABERTAS = ["20717173506", "20716925556", "20712190506", "20711454676", "20708244036"];
const LIQUIDADAS = ["20713079396", "20712642016", "20711417696", "20711415656", "20708999896"];

// Ordem de inserção IGUAL à do caso real: a aba Liquidada foi visitada ANTES da Em aberto,
// então as liquidadas entram primeiro no mapa. É essa ordem que fazia o `stopId` decepar.
function semear(bnById) {
  bnById.clear();
  for (const id of LIQUIDADAS) {
    bnById.set(id, { BetId: Number(id), __aberta: false, Type: "Single", Status: 3,
                     Stake: "R$150,00", Return: "R$0,00", DecimalOdds: 2.5,
                     PlacedAt: "2026-07-26T12:00:00Z", Legs: [] });
  }
  for (const id of ABERTAS) {
    bnById.set(id, { BetId: Number(id), __aberta: true, Type: "Single", Status: 1,
                     Stake: "R$205,00", Return: "R$440,75", DecimalOdds: 2.15,
                     PlacedAt: "2026-07-26T22:13:00Z", Legs: [] });
  }
}

function ctxFake(stopId = "") {
  return { stopId, cutoff: Date.parse("2026-06-26T00:00:00Z"),
           pisoSanidade: Date.parse("2024-06-26T00:00:00Z"),
           parar: () => false, painel: { contador: { textContent: "" } } };
}

const codigos = (blocos) => blocos.map((b) => linha(b, "[Código:").replace(/[\[\]]/g, "").trim())
                                  .map((s) => s.replace(/^Código:\s*/, ""));

export async function rodar() {
  const { pegar } = carregarContent();
  const robo = pegar("roboBetanoPassive");
  const bnById = pegar("bnById");
  const loc = pegar("location");
  const falhas = [];
  let testes = 0;

  // Sem paginação a fazer: o fim autoritativo das DUAS listas já chegou (é o que o robô vê
  // quando a página terminou de carregar as duas abas).
  pegar("bnFimOpen = true");
  pegar("bnFimSettled = true");

  // 1) Aba "Em aberto" → só as abertas, nunca as liquidadas que ficaram em memória.
  semear(bnById);
  loc.pathname = "/myaccount/bethistory/open";
  let saiu = codigos(await robo(ctxFake()));
  testes++;
  if (saiu.length !== ABERTAS.length || ABERTAS.some((id) => !saiu.includes(id)))
    falhas.push(`aba Em aberto: esperava as ${ABERTAS.length} abertas, saíram ${saiu.length} (${saiu.join(", ")})`);
  const vazouL = saiu.filter((id) => LIQUIDADAS.includes(id));
  if (vazouL.length) falhas.push(`aba Em aberto vazou ${vazouL.length} LIQUIDADA(s): ${vazouL.join(", ")}`);

  // 2) Aba "Liquidada" → só as liquidadas (o espelho: abertas em memória não vazam).
  semear(bnById);
  loc.pathname = "/myaccount/bethistory/settled";
  saiu = codigos(await robo(ctxFake()));
  testes++;
  if (saiu.length !== LIQUIDADAS.length || LIQUIDADAS.some((id) => !saiu.includes(id)))
    falhas.push(`aba Liquidada: esperava as ${LIQUIDADAS.length} liquidadas, saíram ${saiu.length} (${saiu.join(", ")})`);
  const vazouA = saiu.filter((id) => ABERTAS.includes(id));
  if (vazouA.length) falhas.push(`aba Liquidada vazou ${vazouA.length} ABERTA(s): ${vazouA.join(", ")}`);

  // 3) A perda silenciosa: "parar no ID" apontando para um bilhete LIQUIDADO não pode
  //    decepar a aba Em aberto — o liquidado nem deveria ser olhado ali.
  semear(bnById);
  loc.pathname = "/myaccount/bethistory/open";
  saiu = codigos(await robo(ctxFake(LIQUIDADAS[0])));
  testes++;
  if (saiu.length !== ABERTAS.length)
    falhas.push(`stopId de bilhete liquidado decepou a aba Em aberto: saíram ${saiu.length} de ${ABERTAS.length}`);

  // 4) O stopId continua valendo DENTRO da própria aba (copiar do último extraído pra cima).
  semear(bnById);
  loc.pathname = "/myaccount/bethistory/open";
  saiu = codigos(await robo(ctxFake(ABERTAS[2])));
  testes++;
  if (saiu.length !== 2 || saiu[0] !== ABERTAS[0] || saiu[1] !== ABERTAS[1])
    falhas.push(`stopId na própria aba deveria parar nos 2 primeiros, saíram ${saiu.length} (${saiu.join(", ")})`);

  // 5) O bloco da aberta precisa dizer à IA que NÃO é para liquidar.
  const fmt = pegar("formatTicketBN");
  const bloco = fmt(bnById.get(ABERTAS[0]));
  testes++;
  if (!/^em aberto \(aguardando resultado/.test(linha(bloco, "Status:")))
    falhas.push(`bilhete aberto sem o status "em aberto": "${linha(bloco, "Status:")}"`);
  if (!/Retorno potencial/.test(bloco))
    falhas.push("bilhete aberto: o retorno precisa ser rotulado POTENCIAL (senão a IA lê como vitória)");

  return { falhas, testes };
}
