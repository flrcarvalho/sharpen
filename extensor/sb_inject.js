// Mundo MAIN (só na Superbet): observa as requisições que a PRÓPRIA página faz à
// API de tickets e captura o header `sessionId` + a URL base. Repassa ao content
// script (mundo isolado) via postMessage. NÃO altera nada — só lê o que já passa.
// Com isso a extensão chama a mesma API sem clicar em nada.
(function () {
  function envia(url, sessionId) {
    if (!url || !sessionId) return;
    try {
      window.postMessage({ __sharpenupSB: true, url: String(url), sessionId: String(sessionId) }, "*");
    } catch (e) {}
  }

  // fetch
  const of = window.fetch;
  if (of && !of.__suWrapped) {
    const w = function (...a) {
      try {
        const url = (a[0] && a[0].url) || a[0];
        if (/\/tickets\//.test(String(url))) {
          let sid = "";
          const hh = (a[1] && a[1].headers) || (a[0] && a[0].headers);
          if (hh) {
            if (hh.get) sid = hh.get("sessionId") || hh.get("sessionid") || "";
            else if (hh.forEach) hh.forEach((v, k) => { if (/sessionid/i.test(k)) sid = v; });
            else Object.keys(hh).forEach((k) => { if (/sessionid/i.test(k)) sid = hh[k]; });
          }
          envia(url, sid);
        }
      } catch (e) {}
      return of.apply(this, a);
    };
    w.__suWrapped = true;
    window.fetch = w;
  }

  // XMLHttpRequest
  const oo = XMLHttpRequest.prototype.open,
        osh = XMLHttpRequest.prototype.setRequestHeader,
        os = XMLHttpRequest.prototype.send;
  if (!os.__suWrapped) {
    XMLHttpRequest.prototype.open = function (m, u) { this.__suU = u; this.__suSid = ""; return oo.apply(this, arguments); };
    XMLHttpRequest.prototype.setRequestHeader = function (k, v) {
      try { if (/sessionid/i.test(k)) this.__suSid = v; } catch (e) {}
      return osh.apply(this, arguments);
    };
    const sendW = function () {
      try { if (/\/tickets\//.test(String(this.__suU))) envia(this.__suU, this.__suSid); } catch (e) {}
      return os.apply(this, arguments);
    };
    sendW.__suWrapped = true;
    XMLHttpRequest.prototype.send = sendW;
  }
})();
