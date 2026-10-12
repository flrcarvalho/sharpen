// CRU para o servidor (s409, Projeto Ficha Sharpen). Carregado pelo background.js.
//
// O content.js junta o objeto da CASA de cada bilhete (o campo `cru` que os injects mandam) e
// pede o envio aqui, SEPARADO do texto e sem esperar resposta. O servidor guarda o cru e monta
// a Ficha com o adaptador da família (`app/adaptadores/`). Regras do Feca (11/10):
//
//   • falha aqui NUNCA afeta a captura de hoje: nada lança, nada sinaliza na tela, e o 401
//     não mexe no token (quem cuida da sessão é o envio do texto);
//   • só é marcado como enviado depois do 200; o 409 (cru do site de outra casa) é resposta
//     FINAL: marca como tratado e não reenvia;
//   • o registro de "já enviado" tem limite (CRU_DIAS e CRU_MAX_REGISTRO) e apaga o antigo;
//   • o FILTRO é por nome EXATO numa lista fechada (a mesma de `app/cru.py`; um teste
//     confere as duas). Nunca por pedaço do nome, nunca por formato do valor; e-mail pelo valor.

const CRU_NOMES_FILTRADOS = new Set([
  "client_ip", "ip_address", "user", "username", "login-id", "loginDomainId",
  "BonusUserId", "CurrentBalance",
  "email", "password", "cpf", "phone", "cookie", "authorization", "access_token",
  "refresh_token",
  "CurrentBalanceDetails", "CustomerId", "CustomerCode", "playerId",
].map((n) => n.toLowerCase()));
const CRU_EMAIL = /^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$/;
const CRU_LOTE = 200;
const CRU_DIAS = 60;
const CRU_MAX_REGISTRO = 20000;
const CRU_CHAVE = "cruEnviado";

function cruFiltrar(o) {
  if (Array.isArray(o)) return o.map(cruFiltrar);
  if (!o || typeof o !== "object") return o;
  const r = {};
  for (const k of Object.keys(o)) {
    if (CRU_NOMES_FILTRADOS.has(String(k).toLowerCase())) continue;
    const v = o[k];
    if (typeof v === "string" && CRU_EMAIL.test(v.trim())) continue;
    r[k] = cruFiltrar(v);
  }
  return r;
}

// Texto estável (chaves em ordem): o mesmo cru dá sempre o mesmo hash.
function cruCanonico(o) {
  if (Array.isArray(o)) return "[" + o.map(cruCanonico).join(",") + "]";
  if (o && typeof o === "object") {
    return "{" + Object.keys(o).sort().map((k) => JSON.stringify(k) + ":" + cruCanonico(o[k])).join(",") + "}";
  }
  return JSON.stringify(o === undefined ? null : o);
}

async function cruHash(o) {
  const dados = new TextEncoder().encode(cruCanonico(o));
  const d = await crypto.subtle.digest("SHA-256", dados);
  return Array.from(new Uint8Array(d)).map((b) => b.toString(16).padStart(2, "0")).join("");
}

// Apaga o que passou de CRU_DIAS e, se ainda sobrar demais, os mais antigos.
function cruPodar(reg, agora) {
  const limite = agora - CRU_DIAS * 86400000;
  let chaves = Object.keys(reg).filter((k) => reg[k] && reg[k].t >= limite);
  if (chaves.length > CRU_MAX_REGISTRO) {
    chaves.sort((a, b) => reg[b].t - reg[a].t);
    chaves = chaves.slice(0, CRU_MAX_REGISTRO);
  }
  const novo = {};
  for (const k of chaves) novo[k] = reg[k];
  return novo;
}

/** Envia o cru de um lote. Devolve um resumo (só para log e teste); NUNCA lança. */
async function enviarCru(familia, itens, tab) {
  const resumo = { enviados: 0, iguais: 0, falhas: 0, tratados409: 0 };
  try {
    const { token } = await chrome.storage.local.get("token");
    if (!token || !familia || !Array.isArray(itens) || !itens.length) return resumo;
    const origem = hostDaAba(tab);
    const agora = Date.now();
    const guardado = (await chrome.storage.local.get(CRU_CHAVE))[CRU_CHAVE] || {};
    let reg = cruPodar(guardado, agora);

    const pendentes = [];
    for (const it of itens) {
      if (!it || it.codigo == null || it.codigo === "" || !it.cru || typeof it.cru !== "object") continue;
      const cru = cruFiltrar(it.cru);
      const hash = await cruHash(cru);
      const chave = origem + "|" + familia + "|" + it.codigo;
      if (reg[chave] && reg[chave].h === hash) { resumo.iguais++; continue; }
      pendentes.push({ chave, item: { codigo: String(it.codigo), hash, cru } });
    }

    const base = await getApiBase();
    for (let i = 0; i < pendentes.length; i += CRU_LOTE) {
      const lote = pendentes.slice(i, i + CRU_LOTE);
      let r;
      try {
        r = await fetch(`${base}/captura/ficha`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token, versao: chrome.runtime.getManifest().version, origem,
                                 familia, itens: lote.map((p) => p.item) }),
        });
      } catch (e) { resumo.falhas += lote.length; continue; }
      if (r.ok || r.status === 409) {
        for (const p of lote) reg[p.chave] = { h: p.item.hash, t: agora };
        if (r.ok) resumo.enviados += lote.length; else resumo.tratados409 += lote.length;
      } else {
        resumo.falhas += lote.length;      // 401, 400, 5xx: fica para a próxima varredura
      }
    }
    reg = cruPodar(reg, agora);
    await chrome.storage.local.set({ [CRU_CHAVE]: reg });
  } catch (e) {
    resumo.falhas++;
  }
  return resumo;
}
