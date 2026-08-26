// SharpenUp — coletor de reconhecimento (Fase 0 de casa nova)
//
// PARA QUE SERVE: construir a captura de uma casa **sem ter conta nela**. Quem tem a conta
// cola este script no console, usa a casa por 30 segundos e manda um arquivo. Nada mais.
//
// A PREMISSA, que é o ponto todo: para escrever um `xx_inject.js` a gente precisa da FORMA
// do que a casa entrega — endpoint, campos, paginação, sinal de fim —, **nunca da sessão**.
// O inject aprende url + headers de uma requisição real dentro do navegador do próprio dono,
// em tempo de execução (ver `nv_inject.js::capturarReq`). O token nunca precisa sair de lá,
// e por isso este coletor **apaga o valor** de todo header de credencial antes de salvar,
// guardando só o NOME — que é o que importa para saber que ele existe e é obrigatório.
//
// ⚠ O QUE ELE NÃO PROTEGE: o corpo da resposta **é** o histórico de apostas da pessoa. Isso
// é dado financeiro pessoal e não tem como ser removido — é justamente o que precisamos ler.
// A varredura de PII abaixo é por NOME DE CAMPO e é best-effort: pega `email`, `cpf`,
// `telefone` e afins, e **não** pega o que a casa chamar de outro jeito. Quem coleta tem de
// saber o que está mandando, e o arquivo tem de ser conferido à mão antes de virar fixture
// (`extensor/harness/fixtures/` vai para o git).
//
// ── COMO USAR (roteiro para passar ao tester) ────────────────────────────────────────────
//
//   1. Logado na casa, abra a página **"Minhas apostas"** (o histórico de bilhetes).
//   2. F12 → aba **Console**. Se o Chrome pedir, digite `allow pasting` e dê Enter.
//   3. Cole este arquivo inteiro e dê Enter. Ele responde "coletor ligado".
//   4. **Use a casa normalmente por ~30 segundos**, cobrindo:
//        • a aba de apostas **resolvidas** e a de **em aberto**;
//        • rolar até o fim da lista / clicar "mostrar mais" **pelo menos duas vezes**
//          (é isso que revela como a próxima página é pedida e como a casa diz que acabou);
//        • abrir o **detalhe** de um bilhete, se houver.
//   5. Rode `SharpenUpRecon.resumo()` — sai uma tabela do que foi pego.
//   6. Rode `SharpenUpRecon.salvar()` — baixa `recon-<casa>-<data>.json`. Mande esse arquivo.
//
// A amostra ideal cobre **1 ganha · 1 perdida · 1 aberta · 1 múltipla · 1 com boost**. Sem
// essa cobertura o harness da casa não trava armadilha nenhuma (ver `harness/README.md`).
//
// ── POR QUE CONSOLE-ONLY ─────────────────────────────────────────────────────────────────
// Nada de badge flutuante ou painel na página. Um overlay seria UI nova, e UI nova neste
// projeto passa pelo checklist de marca (`/nova-ui`) — gate que não faz sentido gastar num
// utilitário de debug que roda no site de terceiro. O feedback sai por `console.log`.
//
// Gate de sintaxe: `node --check tools/recon_casa.js`.

(function () {
  "use strict";

  if (window.SharpenUpRecon && window.SharpenUpRecon.__ativo) {
    console.log("%c[SharpenUp recon] já estava ligado — nada refeito.", "color:#7a8794");
    return;
  }

  const VERSAO = 1;
  const TETO_RESPOSTA = 4 * 1024 * 1024;   // por resposta; acima disso guarda só o começo
  const TETO_TOTAL = 24 * 1024 * 1024;     // do arquivo inteiro, para o download não travar
  const TETO_CAPTURAS = 400;

  // Hosts que só geram ruído. Não é segurança, é higiene: sem isso o arquivo vira 40 MB de
  // analytics e o dado que interessa se perde no meio.
  const RUIDO = /(?:google|googletagmanager|doubleclick|facebook|hotjar|sentry|segment|mixpanel|amplitude|clarity\.ms|newrelic|datadoghq|cloudflareinsights|recaptcha|gstatic|jsdelivr|unpkg)\./i;

  // Caminhos que CHEIRAM a histórico de bilhetes. Só ordena o resumo — nunca filtra nada,
  // porque casa nova é exatamente onde o palpite falha (a Pitaco fala protobuf, a Novibet
  // chama o endereço de `historytickets`, a bet365 de `sportshistoryapi`).
  //
  // ⚠ ISTO EXISTE POR MEDIÇÃO, não por elegância. Ranqueando só por TAMANHO, o topo da
  // tabela na 1xBet era o FEED DE ODDS (`Get1x2_VZip`, 77 KB por resposta, repetido a cada
  // poucos segundos) — o tester seria mandado direto para a requisição errada, que é
  // justamente o passo em que a Fase 0 costuma travar com quem não é técnico.
  const PISTA = /(?:bet|aposta|ticket|cupom|coupon|wager|history|historic|hist[oó]ri|betslip|mybets|my_bets|slip|account|conta|transaction)/i;

  // Headers cujo VALOR nunca é salvo. O nome fica — saber que a casa exige `authorization`
  // é metade do recon; saber o token não serve para nada e é passivo de segurança.
  const HEADER_SEGREDO = /^(?:authorization|cookie|set-cookie|proxy-authorization|x-[a-z0-9-]*(?:auth|token|key|session|sig|signature)[a-z0-9-]*|.*api[-_]?key.*|.*access[-_]?token.*|.*session[-_]?id.*)$/i;

  // Chaves de identidade pessoal, apagadas do corpo e da resposta por NOME. Best-effort,
  // e assumidamente incompleto — ver o aviso do cabeçalho.
  //
  // ⚠ `lat`/`long` entraram aqui DEPOIS, por medição: a 1xBet manda
  // `x-location-latitude: -25.4278` / `x-location-longitude: -49.2731` em TODA requisição.
  // São as coordenadas de quem coletou (deu Curitiba, ao quarteirão), viajavam no recon e
  // iriam parar numa fixture versionada no git. Nenhum header de credencial casava com elas
  // e nenhum campo de identidade se chamava assim — geolocalização é uma TERCEIRA família,
  // e não estava coberta. Vale procurá-la em casa nova: é silenciosa e não parece segredo.
  const PII = /^(?:e?-?mail|cpf|cnpj|rg|documento|document|documentnumber|phone|telefone|celular|mobile|msisdn|firstname|lastname|fullname|nome|nomecompleto|name|username|login|birth\w*|nascimento|address|endereco|zip\w*|cep|ip|ipaddress|password|senha|(?:x-)?(?:location-)?(?:lat|latitude|lon|lng|long|longitude|geo|coords?)|.*-(?:latitude|longitude))$/i;

  const est = {
    capturas: [],
    descartados: { ruido: 0, semCorpo: 0, teto: 0 },
    bytes: 0,
    seq: 0,
  };

  const LOG = (...a) => { try { console.log("%c[SharpenUp recon]", "color:#22c55e", ...a); } catch (e) {} };

  // ── util ────────────────────────────────────────────────────────────────────────────────

  function ehRuido(url) {
    try { return RUIDO.test(new URL(url, location.href).host); } catch (e) { return false; }
  }

  // Query string pode carregar token. Guardamos a URL com os valores sensíveis apagados e,
  // separado, a lista de parâmetros — quase sempre é o nome do parâmetro (`skip`, `take`,
  // `range_start`) que ensina a paginação, não o valor.
  function limparUrl(u) {
    try {
      const url = new URL(u, location.href);
      const params = {};
      url.searchParams.forEach((v, k) => {
        params[k] = HEADER_SEGREDO.test(k) || PII.test(k) ? "<REDIGIDO>" : v;
      });
      const limpa = new URL(url.origin + url.pathname);
      Object.keys(params).forEach((k) => limpa.searchParams.set(k, params[k]));
      return { url: limpa.toString(), path: url.pathname, params: params };
    } catch (e) {
      return { url: String(u), path: String(u), params: {} };
    }
  }

  function limparHeaders(h) {
    const o = {};
    try {
      if (!h) return o;
      // Dois crivos, não um. `HEADER_SEGREDO` pega credencial; `PII` pega identidade — e é
      // por ele que a geolocalização cai (`x-location-latitude`), que não é segredo nenhum
      // e mesmo assim é dado pessoal. Header só passa inteiro se escapar dos dois.
      const por = (k, v) => {
        const nome = String(k).toLowerCase();
        o[nome] = (HEADER_SEGREDO.test(nome) || PII.test(nome))
          ? "<REDIGIDO · " + String(v == null ? "" : v).length + " chars>"
          : String(v);
      };
      if (typeof h.forEach === "function") h.forEach((v, k) => por(k, v));
      else if (typeof h === "object") for (const k in h) por(k, h[k]);
    } catch (e) {}
    return o;
  }

  // Varre objeto/array recursivamente apagando valor de chave que pareça identidade pessoal.
  // Preserva a ESTRUTURA (a chave continua lá) — o recon precisa saber que o campo existe.
  function limparPII(v, prof) {
    prof = prof || 0;
    if (prof > 12 || v == null) return v;
    if (Array.isArray(v)) return v.map((x) => limparPII(x, prof + 1));
    if (typeof v !== "object") return v;
    const o = {};
    for (const k in v) {
      if (!Object.prototype.hasOwnProperty.call(v, k)) continue;
      o[k] = PII.test(k) ? "<REDIGIDO>" : limparPII(v[k], prof + 1);
    }
    return o;
  }

  function talvezJson(txt) {
    if (typeof txt !== "string") return null;
    const t = txt.trim();
    if (!t || (t[0] !== "{" && t[0] !== "[")) return null;
    try { return JSON.parse(t); } catch (e) { return null; }
  }

  function b64(buf) {
    try {
      const bytes = new Uint8Array(buf);
      let s = "";
      for (let i = 0; i < bytes.length; i++) s += String.fromCharCode(bytes[i]);
      return btoa(s);
    } catch (e) { return null; }
  }

  // Guarda uma captura. `resposta` já vem tratada; `erroLeitura` é achado de primeira
  // linha — casa cujo clone da resposta rejeita é casa em que o MODO PASSIVO É IMPOSSÍVEL
  // (Pitaco s270, Novibet s271), e isso decide o desenho do inject.
  function guardar(reg) {
    if (est.capturas.length >= TETO_CAPTURAS || est.bytes >= TETO_TOTAL) {
      est.descartados.teto++;
      return;
    }
    reg.n = ++est.seq;
    est.bytes += reg.bytes || 0;
    est.capturas.push(reg);
    LOG(reg.metodo, reg.path, "·", reg.status, "·", (reg.bytes / 1024).toFixed(1) + " KB",
        reg.erroLeitura ? "· ⚠ corpo inalcançável: " + reg.erroLeitura : "");
  }

  function registrar(o) {
    const { metodo, url, headers, corpo, status, tipo, texto, buffer, erroLeitura } = o;
    if (ehRuido(url)) { est.descartados.ruido++; return; }

    const lu = limparUrl(url);
    let resposta = null, formato = "vazio", bytes = 0;

    if (typeof texto === "string" && texto.length) {
      bytes = texto.length;
      const j = talvezJson(texto);
      if (j) { resposta = limparPII(j); formato = "json"; }
      else { resposta = texto.slice(0, TETO_RESPOSTA); formato = "texto"; }
    } else if (buffer && buffer.byteLength) {
      // Transporte binário (gRPC-Web/protobuf, como a Pitaco). Base64 é obrigatório: ler
      // binário por `text()` passa pelo decode UTF-8 e corrompe todo byte 0x80-0xFF.
      bytes = buffer.byteLength;
      resposta = { b64: b64(buffer.slice(0, TETO_RESPOSTA)) };
      formato = "binario";
    } else if (!erroLeitura) {
      est.descartados.semCorpo++;
      return;
    }

    guardar({
      metodo: metodo || "GET",
      url: lu.url,
      path: lu.path,
      params: lu.params,
      headers: limparHeaders(headers),
      corpo: typeof corpo === "string"
        ? (talvezJson(corpo) ? limparPII(talvezJson(corpo)) : corpo.slice(0, 64 * 1024))
        : null,
      status: status == null ? null : status,
      tipo: tipo || "",
      formato: formato,
      bytes: bytes,
      // Só uma pista para ordenar o resumo. NÃO filtra: quem decide é quem lê o arquivo.
      suspeito: PISTA.test(lu.path),
      erroLeitura: erroLeitura || null,
      resposta: resposta,
    });
  }

  // ── hook de fetch ───────────────────────────────────────────────────────────────────────

  const fetchOriginal = window.fetch;

  window.fetch = function (...a) {
    const req = (a[0] && typeof a[0] === "object" && a[0].url) ? a[0] : null;
    const url = req ? req.url : a[0];
    const opts = a[1] || {};
    const metodo = (req ? req.method : opts.method) || "GET";
    const headers = req ? req.headers : opts.headers;

    let corpo = typeof opts.body === "string" ? opts.body : null;
    if (req && !corpo) { try { req.clone().text().then((t) => { corpo = t; }); } catch (e) {} }

    return fetchOriginal.apply(this, a).then((r) => {
      try {
        if (ehRuido(url)) { est.descartados.ruido++; return r; }
        const tipo = (r.headers && r.headers.get("content-type")) || "";
        const binario = tipo && !/json|text|xml|javascript|urlencoded|plain/i.test(tipo);
        const clone = r.clone();
        const base = { metodo, url, headers, corpo, status: r.status, tipo };

        // O `.catch` NÃO é higiene: quando o clone rejeita ("The user aborted a request"),
        // isso É o achado — a casa cancela o stream da própria resposta e o inject vai ter
        // de buscar o dado ele mesmo em vez de escutar passivamente.
        (binario ? clone.arrayBuffer().then((b) => registrar({ ...base, buffer: b }))
                 : clone.text().then((t) => registrar({ ...base, texto: t })))
          .catch((e) => registrar({ ...base, erroLeitura: String((e && e.message) || e) }));
      } catch (e) {}
      return r;
    });
  };

  // ── hook de XHR ─────────────────────────────────────────────────────────────────────────
  // Várias casas usam XHR, e o `HttpClient` do Angular pode cair nele conforme a config.

  const xhrOpen = XMLHttpRequest.prototype.open;
  const xhrSend = XMLHttpRequest.prototype.send;
  const xhrSet = XMLHttpRequest.prototype.setRequestHeader;

  XMLHttpRequest.prototype.open = function (m, u) {
    this.__reconM = m; this.__reconU = u; this.__reconH = {};
    return xhrOpen.apply(this, arguments);
  };
  XMLHttpRequest.prototype.setRequestHeader = function (k, v) {
    try { this.__reconH[k] = v; } catch (e) {}
    return xhrSet.apply(this, arguments);
  };
  XMLHttpRequest.prototype.send = function (body) {
    try {
      const self = this;
      this.addEventListener("load", function () {
        try {
          const base = {
            metodo: self.__reconM, url: self.__reconU, headers: self.__reconH,
            corpo: typeof body === "string" ? body : null,
            status: self.status,
            tipo: (self.getResponseHeader && self.getResponseHeader("content-type")) || "",
          };
          const t = self.responseType;
          // ⚠ Em `responseType: "json"`, ler `responseText` LANÇA InvalidStateError — o corpo
          // só existe em `.response`, já desserializado. Ignorar isso mata a captura calada.
          if (t === "" || t === "text") registrar({ ...base, texto: self.responseText });
          else if (t === "json") registrar({ ...base, texto: JSON.stringify(self.response) });
          else if (t === "arraybuffer") registrar({ ...base, buffer: self.response });
          else registrar({ ...base, erroLeitura: "responseType não lido: " + t });
        } catch (e) {
          try {
            registrar({ metodo: self.__reconM, url: self.__reconU, headers: self.__reconH,
                        status: self.status, erroLeitura: String((e && e.message) || e) });
          } catch (e2) {}
        }
      });
    } catch (e) {}
    return xhrSend.apply(this, arguments);
  };

  // ── API pública ─────────────────────────────────────────────────────────────────────────

  function nomeCasa() {
    try { return location.host.replace(/^www\./, "").split(".")[0].toLowerCase(); }
    catch (e) { return "casa"; }
  }

  const API = {
    __ativo: true,

    // Tabela do que foi pego. Ordena os CANDIDATOS a histórico primeiro e só depois por
    // tamanho — ordenar só por tamanho põe o feed de odds no topo (medido na 1xBet: as
    // quatro maiores respostas da home eram `Get1x2_VZip`, nenhuma delas bilhete).
    resumo() {
      const linhas = est.capturas
        .slice()
        .sort((a, b) => (b.suspeito - a.suspeito) || (b.bytes - a.bytes))
        .map((c) => ({
          "#": c.n, aposta: c.suspeito ? "◆" : "", método: c.metodo, caminho: c.path,
          status: c.status, formato: c.formato, KB: +(c.bytes / 1024).toFixed(1),
          "corpo inalcançável": c.erroLeitura ? "SIM" : "",
        }));
      console.table(linhas);
      const n = est.capturas.filter((c) => c.suspeito).length;
      LOG(est.capturas.length, "capturas ·", (est.bytes / 1024 / 1024).toFixed(2),
          "MB · descartados:", JSON.stringify(est.descartados));
      LOG(n ? "◆ " + n + " parecem ser de aposta — mas mande o arquivo INTEIRO, o palpite erra."
            : "Nenhuma pareceu ser de aposta. Confira se está na página de histórico e use a lista de novo.");
      LOG("Agora rode: SharpenUpRecon.salvar()");
      return linhas.length;
    },

    // Uma captura inteira, para inspecionar antes de mandar.
    ver(n) { return est.capturas.find((c) => c.n === n) || null; },

    // Remove uma captura do pacote — para quem quiser tirar algo antes de enviar.
    remover(n) {
      const i = est.capturas.findIndex((c) => c.n === n);
      if (i < 0) return false;
      est.bytes -= est.capturas[i].bytes || 0;
      est.capturas.splice(i, 1);
      return true;
    },

    salvar(nome) {
      const pacote = {
        meta: {
          versao: VERSAO,
          casa: nomeCasa(),
          host: location.host,
          href: limparUrl(location.href).url,
          userAgent: navigator.userAgent,
          fuso: Intl.DateTimeFormat().resolvedOptions().timeZone,
          gerado: new Date().toISOString(),
          capturas: est.capturas.length,
          descartados: est.descartados,
          aviso: "Valores de header de credencial e campos de identidade foram apagados. "
               + "O corpo das respostas É o histórico de apostas — confira antes de enviar.",
        },
        capturas: est.capturas,
      };
      const txt = JSON.stringify(pacote, null, 1);
      const arq = (nome || "recon-" + nomeCasa() + "-" + new Date().toISOString().slice(0, 10)) + ".json";
      const a = document.createElement("a");
      a.href = URL.createObjectURL(new Blob([txt], { type: "application/json" }));
      a.download = arq;
      a.click();
      setTimeout(() => URL.revokeObjectURL(a.href), 5000);
      LOG("salvo:", arq, "·", (txt.length / 1024 / 1024).toFixed(2), "MB");
      return arq;
    },

    // Devolve os hooks originais. A página volta ao normal sem recarregar.
    parar() {
      window.fetch = fetchOriginal;
      XMLHttpRequest.prototype.open = xhrOpen;
      XMLHttpRequest.prototype.send = xhrSend;
      XMLHttpRequest.prototype.setRequestHeader = xhrSet;
      API.__ativo = false;
      LOG("coletor desligado. As capturas continuam em memória — dá para salvar ainda.");
    },
  };

  window.SharpenUpRecon = API;

  LOG("coletor ligado em " + location.host + ".");
  LOG("Use a casa: abra as DUAS abas (resolvidas e em aberto) e role até o fim da lista.");
  LOG("Depois: SharpenUpRecon.resumo()  →  SharpenUpRecon.salvar()");
})();
