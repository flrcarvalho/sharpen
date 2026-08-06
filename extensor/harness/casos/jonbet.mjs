// Jonbet (BetBy / sptpub) — captura por API `my_bets/list` (s248).
//
// Trava as leituras que o recon mediu cruzando o JSON com o card renderizado. Três delas
// são armadilhas que quebram a casa em silêncio se alguém "simplificar" o parser:
//
//   • `total_k` vem "0" em TODA PERDIDA (6 de 6 na base real), com `k` guardando a odd que o
//     card mostra. É o `betOdds` da KTO em outra roupa: ler `total_k` cru grava odd zero em
//     100% das perdas. Regra (a mesma do app da casa): total_k === 0 ? k : total_k.
//   • `timestamp` é float em SEGUNDOS e JÁ É hora local de São Paulo. Multiplicar por 1000 e
//     mais nada — converter fuso aqui pula um dia.
//   • stake é `sum` (não `stake`), string com PONTO decimal ("333.16"). Nunca o parser BR.
//
// A 1ª requisição da página sai SEM `Authorization` e a casa devolve 401 com um corpo que
// TEM uma chave `status` (que não é status de bilhete). O caso injeta exatamente isso como
// primeira resposta: se o inject aprender essa requisição para o replay, ele repagina sem
// token e colhe 401 em toda página — reportando `hook:true` + `respostas>0` + 0 bilhetes,
// o mesmo sintoma de "formato mudou". Aqui isso vira falha, não mistério.
//
// PAGINAÇÃO: provada ao vivo forçando `limit=3` sobre os 10 bilhetes (skip 0/3/6/9 → 3,3,3,1
// e skip=12 → 200 com lista VAZIA, sem erro e sem repetir a última página). O `responder`
// abaixo reproduz isso e, de propósito, **ignora o `limit` pedido** e devolve no máximo 3:
// é assim que se prova que o inject avança pelo tamanho que VOLTOU, não pelo que pediu.
import { rodarInject, carregarContent, fixture, linha } from "../sandbox.mjs";

export const casa = "JONBET";

// Cada valor abaixo foi lido do CARD da casa (print da aba "Todas" de 06/08/2026), não do
// que o código produz. `data` confere com o card até o minuto — os segundos vêm do
// `timestamp` (o card não os mostra).
//
// ⚠ Exceção honesta: o bilhete …617574 é o único que NÃO aparecia no print (era o 10º, fora
// da dobra). Os valores dele vêm do JSON. Se algum dia divergir da tela, é o suspeito.
// `evento` é a data que VAI PARA A COLUNA DATA do TSV (`MASTER_OUTPUT §4`) e é a que o card
// estampa no topo do bloco branco ("Hoje, 01:05" · "Ontem, 01:35" · "Anteontem, 22:40").
// ⚠ Em 7 dos 10 bilhetes ela cai num DIA diferente da colocação — a Jonbet é casa de badminton
// asiático, com jogos de madrugada apostados na tarde anterior. Travar só a colocação deixaria
// 70% da base no dia errado, que foi o defeito que a VaideBet levou a produção na s210.
const ESPERADO = {
  "2696892252130783466": { odd: "1,87", status: /em aberto/,    stake: "200,00", data: "05/08/2026 18:00:19", evento: "06/08/2026 01:05:00" },
  "2696881871849136836": { odd: "1,71", status: /em aberto/,    stake: "300,00", data: "05/08/2026 17:18:35", evento: "06/08/2026 00:15:00" },
  "2696878266291196409": { odd: "2,12", status: /em aberto/,    stake: "250,00", data: "05/08/2026 17:04:00", evento: "06/08/2026 01:55:00" },
  "2696533322854707365": { odd: "1,87", status: /^Ganho → W/,   stake: "333,16", data: "04/08/2026 18:13:28", evento: "05/08/2026 01:35:00" },
  "2696531434088309374": { odd: "1,87", status: /^Perdeu → L$/, stake: "333,16", data: "04/08/2026 18:06:35", evento: "05/08/2026 00:20:00" },
  "2696530168314475463": { odd: "2,49", status: /^Perdeu → L$/, stake: "138,35", data: "04/08/2026 18:02:15", evento: "04/08/2026 22:40:00" },
  "2696530168314475401": { odd: "1,85", status: /^Perdeu → L$/, stake: "242,98", data: "04/08/2026 18:02:07", evento: "04/08/2026 22:40:00" },
  "2696529775920550060": { odd: "2,22", status: /^Ganho → W/,   stake: "338,82", data: "04/08/2026 18:00:26", evento: "04/08/2026 22:00:00" },
  "2696529262982345196": { odd: "1,87", status: /^Perdeu → L$/, stake: "300,00", data: "04/08/2026 17:57:59", evento: "05/08/2026 01:00:00" },
  "2696528973386617574": { odd: "3,21", status: /^Perdeu → L$/, stake: "150,00", data: "04/08/2026 17:56:33", evento: "05/08/2026 00:40:00" },
};

// Retorno que o card estampa em "Você ganhou" — a odd do W tem de explicá-lo até o centavo.
const RETORNO_CARD = { "2696533322854707365": 623.01, "2696529775920550060": 752.18 };

const PAGINA_FALSA = 3;   // o servidor do teste devolve no MÁXIMO 3, ignorando o `limit` pedido

export async function rodar() {
  const base = "https://api-31-sp-c7818b61-584.sptpub.com/api/v1/my_bets/list";
  const todos = JSON.parse(fixture("jonbet.my_bets_all.json")).results;
  const err401 = fixture("jonbet.my_bets_401.json");
  let servidas = 0, negadas = 0;

  const responder = (url, opts) => {
    if (!/my_bets\/list/.test(url)) return null;
    // Sem Bearer = a chamada que a página dispara antes de autenticar. Corpo REAL do 401.
    const h = (opts && opts.headers) || {};
    if (!(h.Authorization || h.authorization)) { negadas++; return err401; }
    servidas++;
    let skip = 0;
    try { skip = Number(new URL(url).searchParams.get("skip")) || 0; } catch (e) {}
    // `count` é sempre o total do filtro (constante entre páginas) — é o fim autoritativo.
    // Além do fim a casa devolve 200 com lista vazia; nunca erro, nunca repetição.
    return JSON.stringify({ results: todos.slice(skip, skip + PAGINA_FALSA), count: todos.length });
  };

  const alvo = `${base}?currency=BRL&lang=pt-BR&limit=15&skip=0&status=open&timestamp_from&timestamp_to`;
  const { ultima, urls } = await rodarInject({
    inject: "jb_inject.js",
    href: "https://jonbet.bet.br/pt/sports?bt-path=%2Fbets",
    // Sequência REAL da casa: a página dispara a lista ANTES de o token chegar (→ 401) e só
    // depois refaz autenticada. O inject tem de ignorar a primeira e aprender a segunda.
    urlInicial: alvo,
    optsInicial: { method: "GET", headers: { "Content-Type": "application/json" } },
    urlsExtra: [{ url: alvo, opts: { method: "GET", headers: { "Content-Type": "application/json", Authorization: "Bearer harness.token.falso" } } }],
    pedido: "__sharpenupJBReq",
    responder,
  });

  const falhas = [];
  if (!ultima) return { falhas: ["o inject não emitiu nenhuma mensagem"], testes: 0 };
  if (!ultima.hook) falhas.push("o inject não emitiu `hook:true` (autodiagnóstico cego)");
  if (!ultima.fim) falhas.push("o inject não sinalizou `fim` (o robô ficaria esperando o teto)");
  if (urls.length < 4) falhas.push(`replay não repaginou o bastante (só ${urls.length} requisição(ões) para 10 bilhetes em páginas de ${PAGINA_FALSA})`);

  const bilhetes = ultima.bilhetes || [];
  if (bilhetes.length !== 10) falhas.push(`esperava 10 bilhetes normalizados, vieram ${bilhetes.length}`);

  const fmt = carregarContent().pegar("formatTicketJB");
  let testes = 0;
  for (const b of bilhetes) {
    const e = ESPERADO[b.id];
    if (!e) { falhas.push(`bilhete inesperado na fixture: ${b.id}`); continue; }
    const txt = fmt(b);
    testes++;
    if (!txt.startsWith(`[Código: ${b.id}]`)) falhas.push(`${b.id}: marcador [Código:] ausente/errado`);
    const odd = linha(txt, "Odd:");
    const status = linha(txt, "Status:");
    const stake = linha(txt, "Stake:");
    const data = linha(txt, "Data (colocação):");
    const evento = linha(txt, "Data (evento mais recente):");
    if (evento !== e.evento) falhas.push(`${b.id}: data do EVENTO esperada ${e.evento}, veio "${evento}" (é ela que vai para a coluna Data)`);
    if (odd !== e.odd) falhas.push(`${b.id}: odd esperada ${e.odd}, veio "${odd}"`);
    if (!e.status.test(status)) falhas.push(`${b.id}: status "${status}"`);
    if (stake !== e.stake) falhas.push(`${b.id}: stake esperada ${e.stake}, veio "${stake}"`);
    if (data !== e.data) falhas.push(`${b.id}: data esperada ${e.data}, veio "${data}"`);
    // A armadilha, dita em voz alta: perdida NUNCA pode sair com odd zerada.
    if (/Perdeu/.test(status) && /^0*(,0*)?$/.test(odd)) falhas.push(`${b.id}: odd zerada numa PERDIDA — leu total_k cru`);
    // O status cru precisa subir junto: é ele que a CASA_JONBET.md traduz.
    if (!linha(txt, "Status (API):")) falhas.push(`${b.id}: falta o status cru da API`);
    // W: a odd tem de explicar o retorno do card até o centavo.
    const ret = RETORNO_CARD[b.id];
    if (ret != null) {
      const n = Number(odd.replace(",", "."));
      const st = Number(e.stake.replace(".", "").replace(",", "."));
      if (!(Math.abs(n * st - ret) <= 0.01)) falhas.push(`${b.id}: odd ${odd} × stake ${e.stake} não explica o retorno ${ret} do card`);
    }
  }
  if (servidas < 4) falhas.push(`o replay pediu só ${servidas} página(s) autenticada(s) — não varreu a lista`);
  // Prova que a guarda do token foi mesmo exercitada: se o 401 nunca chegou a ser servido, o
  // teste acima não significa nada (era o buraco da 1ª versão deste caso).
  if (!negadas) falhas.push("o corpo 401 nunca foi servido — a guarda do token não foi exercitada");
  // E que o replay nunca repetiu a chamada sem token (seria 401 em loop na casa real).
  if (negadas > 1) falhas.push(`${negadas} requisições sem Bearer — o replay está repaginando sem token`);
  return { falhas, testes };
}
