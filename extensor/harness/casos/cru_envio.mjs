// O ENVIO do cru (s409, Projeto Ficha Sharpen): `extensor/cru.js` (service worker) e o
// pedaço do `content.js` que junta o cru e pede o envio. Não é uma casa: é o gate das
// condições do Feca para a atualização única do SharpenUp.
//
//   (b) erro ao MANDAR o cru não afeta o texto: o `content.js` pede o envio DEPOIS do texto,
//       sem `await`, e nada ali lança, nem com o `sendMessage` explodindo;
//   (d) o registro de "já enviado" tem limite: apaga o que passou de CRU_DIAS e, acima de
//       CRU_MAX_REGISTRO, os mais antigos;
//   e as regras do envio: só marca enviado no 200; o 409 é final (marca tratado, não
//   reenvia); 401/5xx/rede ficam para a próxima; cru igual ao já enviado não sai de novo;
//   o filtro é por NOME EXATO (o mesmo de `app/cru.py`, conferido por `tests/test_cru.py`).
//
// O que NÃO cobre: o navegador de verdade (fetch, chrome.storage e crypto são dublês).
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";
import { webcrypto } from "node:crypto";
import { EXT, carregarContent } from "../sandbox.mjs";

export const casa = "CRU (envio)";

function carregarCru({ respostas = [], token = "tok", storage = {} } = {}) {
  const chamadas = [];
  const ctx = {
    console, JSON, Math, Date, Array, Object, String, Number, Set, Map, Promise,
    TextEncoder, Uint8Array, crypto: webcrypto,
    chrome: {
      storage: { local: {
        get: async (k) => (k === "token" ? (token ? { token } : {}) : (k in storage ? { [k]: storage[k] } : {})),
        set: async (o) => { Object.assign(storage, o); },
      } },
      runtime: { getManifest: () => ({ version: "9.9.9" }) },
    },
    getApiBase: async () => "https://sharpen.test",
    hostDaAba: () => "dexsport.io",
    fetch: async (url, opts) => {
      chamadas.push({ url, corpo: JSON.parse(opts.body) });
      const r = respostas.length ? respostas.shift() : 200;
      if (r === "rede") throw new TypeError("Failed to fetch");
      return { ok: r >= 200 && r < 300, status: r };
    },
  };
  vm.createContext(ctx);
  vm.runInContext(fs.readFileSync(path.join(EXT, "cru.js"), "utf8") +
    "\nglobalThis.__cru = { enviarCru, cruFiltrar, cruPodar, CRU_DIAS, CRU_MAX_REGISTRO, CRU_CHAVE };",
    ctx, { filename: "cru.js" });
  return { ...ctx.__cru, chamadas, storage };
}

const ITEM = (cod, extra) => ({ codigo: cod, cru: Object.assign({ id: cod, amount: 25 }, extra || {}) });

export async function rodar() {
  const falhas = [];
  let testes = 0;
  const ok = (cond, msg) => { testes++; if (!cond) falhas.push(msg); };

  // ── o filtro: nome EXATO, e-mail pelo valor ─────────────────────────────────────
  {
    const { cruFiltrar } = carregarCru();
    const r = cruFiltrar({ id: "1d15646f-c666", CurrentBalance: 9, CurrentBetBalance: 5,
                           user: { a: 1 }, total_multiplier: "1.05", contato: "a@b.com",
                           pernas: [{ Email: "x", odd: 2 }] });
    ok(JSON.stringify(r) === JSON.stringify({ id: "1d15646f-c666", CurrentBetBalance: 5,
                                              total_multiplier: "1.05", pernas: [{ odd: 2 }] }),
       "filtro: devia tirar só os nomes da lista (e o e-mail pelo valor), veio " + JSON.stringify(r));
  }

  // ── 200 marca; o mesmo cru não sai de novo; cru mudado sai ─────────────────────
  {
    const e = carregarCru();
    let r = await e.enviarCru("dx", [ITEM("A"), ITEM("B")], {});
    ok(r.enviados === 2 && e.chamadas.length === 1, "200: devia enviar os 2 num lote só");
    ok(e.chamadas[0].corpo.familia === "dx" && e.chamadas[0].corpo.itens[0].hash.length === 64,
       "o corpo leva família e o hash de cada item");
    r = await e.enviarCru("dx", [ITEM("A"), ITEM("B")], {});
    ok(r.iguais === 2 && e.chamadas.length === 1, "cru IGUAL ao já enviado não pode sair de novo");
    r = await e.enviarCru("dx", [ITEM("A", { payout: 50 })], {});
    ok(r.enviados === 1 && e.chamadas.length === 2, "cru MUDADO (aberta que liquidou) tem de sair");
  }

  // ── só marca no 200: 401, 500 e rede ficam para a próxima ───────────────────────
  for (const resp of [401, 500, "rede"]) {
    const e = carregarCru({ respostas: [resp, 200] });
    const r1 = await e.enviarCru("dx", [ITEM("A")], {});
    ok(r1.falhas === 1, `${resp}: devia contar falha`);
    const r2 = await e.enviarCru("dx", [ITEM("A")], {});
    ok(r2.enviados === 1, `${resp}: o item NÃO podia ter sido marcado; tinha de sair na próxima`);
  }

  // ── 409 é resposta FINAL: marca tratado e não reenvia ────────────────────────────
  {
    const e = carregarCru({ respostas: [409] });
    const r1 = await e.enviarCru("dx", [ITEM("A")], {});
    const r2 = await e.enviarCru("dx", [ITEM("A")], {});
    ok(r1.tratados409 === 1 && r2.iguais === 1 && e.chamadas.length === 1,
       "409: devia marcar como tratado e não reenviar");
  }

  // ── lotes de até 200 ─────────────────────────────────────────────────────────────
  {
    const e = carregarCru();
    const itens = Array.from({ length: 450 }, (_, i) => ITEM("C" + i));
    await e.enviarCru("dx", itens, {});
    ok(e.chamadas.map((c) => c.corpo.itens.length).join(",") === "200,200,50",
       "450 itens deviam sair em lotes de 200, 200 e 50");
  }

  // ── sem token não chama ninguém; erro em qualquer ponto não lança ────────────────
  {
    const e = carregarCru({ token: "" });
    const r = await e.enviarCru("dx", [ITEM("A")], {});
    ok(e.chamadas.length === 0 && r.enviados === 0, "sem token não pode chamar a rota");
    const q = carregarCru();
    let lancou = false;
    try { await q.enviarCru("dx", [null, { codigo: "", cru: {} }, { codigo: "X" }, ITEM("B")], {}); }
    catch (err) { lancou = true; }
    ok(!lancou && q.chamadas[0].corpo.itens.length === 1, "itens ruins são pulados, sem lançar");
  }

  // ── (d) o registro tem limite ─────────────────────────────────────────────────────
  {
    const { cruPodar, CRU_DIAS, CRU_MAX_REGISTRO } = carregarCru();
    const agora = Date.UTC(2026, 9, 12);
    const velho = agora - (CRU_DIAS + 1) * 86400000;
    const reg = { velho: { h: "x", t: velho }, novo: { h: "y", t: agora } };
    const p = cruPodar(reg, agora);
    ok(!("velho" in p) && "novo" in p, `registro: o que passou de ${CRU_DIAS} dias tem de sair`);
    const muitos = {};
    for (let i = 0; i < CRU_MAX_REGISTRO + 10; i++) muitos["k" + i] = { h: "h", t: agora - i };
    const q = cruPodar(muitos, agora);
    ok(Object.keys(q).length === CRU_MAX_REGISTRO && "k0" in q && !(("k" + (CRU_MAX_REGISTRO + 5)) in q),
       `registro: acima de ${CRU_MAX_REGISTRO} entradas, saem as MAIS ANTIGAS`);
    const e = carregarCru({ storage: { cruEnviado: { velho: { h: "x", t: Date.now() - (CRU_DIAS + 1) * 86400000 } } } });
    await e.enviarCru("dx", [ITEM("A")], {});
    ok(!("velho" in e.storage.cruEnviado), "o envio poda o registro antes de gravar");
  }

  // ── (b) o content.js: pedir o envio nunca lança e vem DEPOIS do texto ────────────
  {
    const c = carregarContent();
    const fonte = fs.readFileSync(path.join(EXT, "content.js"), "utf8");
    const iTexto = fonte.indexOf('type: "ENVIAR_TEXTO", texto: texto');
    const iCru = fonte.indexOf("_enviarCruDaRodada();");
    ok(iTexto > 0 && iCru > iTexto && fonte.indexOf("await _enviarCruDaRodada") < 0,
       "content.js: o cru tem de ser pedido DEPOIS do envio do texto, e sem await");
    let lancou = false;
    try { c.pegar("_enviarCruDaRodada")(); } catch (e) { lancou = true; }
    ok(!lancou, "content.js: _enviarCruDaRodada não pode lançar");
  }

  return { falhas, testes };
}
