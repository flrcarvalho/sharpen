// SharpenUp — content script (todas as casas). Dois modos, conforme o pareamento:
//   • modo PRINT (Superbet & cia): FAB → desenha a região 1x → moldura FIXA com
//     botão Snap; cada Snap tira o print da região e envia. Interior clicável.
//   • modo TEXTO (Betano): FAB (ou popup) → ROBÔ rola a página do topo ao fim,
//     colhe o texto dos bilhetes a cada passo e deduplica (a lista é virtualizada,
//     re-renderiza os mesmos ao rolar) → manda tudo como texto pro dashboard.
// Estado do pareamento em chrome.storage; a moldura persiste (sobrevive à navegação).
// Estilos via setProperty('...','important') pra não apanhar do CSS da casa.
(() => {
  if (window.__sharpenupCS) return;
  window.__sharpenupCS = true;

  const AZUL = "#2E8BFF", VERDE = "#2BC07E", Z = "2147483646";
  let fab = null, fabModo = "print", frame = null, box = null, toolbar = null, handle = null,
      drawRoot = null, capturando = false, safety = null, rectAtual = null, roboRodando = false;

  const S = (el, m) => { for (const k in m) el.style.setProperty(k, m[k], "important"); };
  const get = () => chrome.storage.local.get(["token", "modo", "frameAtivo", "frameRect", "frameCount"]);
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  // Tickets da Superbet capturados pelo sb_inject.js (mundo MAIN) — as RESPOSTAS
  // JSON que a própria página recebe da API. O robô só rola a lista p/ a página
  // paginar; a extensão lê o dado exato do site, sem clicar e sem requisição nova.
  // Duas abas: Liquidada (`status=finished`) e Em aberto (`status=active` → `__aberta:true`,
  // sem resultado). `sbById` guarda 1 ticket por ticketId — a versão LIQUIDADA vence a
  // ABERTA (quando o bilhete fecha na mesma sessão, a verdade da liquidação substitui).
  const sbById = new Map();          // ticketId → ticket (liquidada > aberta)
  let sbHookVivo = false, sbRespostas = 0;   // autodiagnóstico (espelha o da Betfair)
  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (d && d.__sharpenupSBData) {
      if (d.hook) sbHookVivo = true;
      if (typeof d.respostas === "number") sbRespostas = d.respostas;
      if (Array.isArray(d.tickets)) {
        for (const t of d.tickets) {
          const c = t && t.ticketId;
          if (!c) continue;
          const ex = sbById.get(c);
          if (!ex || (ex.__aberta && !t.__aberta)) sbById.set(c, t);   // liquidada vence aberta
        }
      }
    }
  });

  // Itens da BETesporte capturados pelo be_inject.js (mundo MAIN) — as RESPOSTAS JSON de
  // POST /api/bet/RequestUserTickets. Mesmo modelo passivo da Superbet: o robô só rola a
  // lista p/ a página buscar mais; a extensão lê o dado exato do site (id, odd, value,
  // status, date), sem clicar em "Ver Cupom".
  const beTickets = [];
  const beTicketSeen = new Set();
  let beHookVivo = false, beRespostas = 0;   // autodiagnóstico (espelha o da Betfair)
  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (d && d.__sharpenupBEData) {
      if (d.hook) beHookVivo = true;
      if (typeof d.respostas === "number") beRespostas = d.respostas;
      if (Array.isArray(d.items)) {
        for (const t of d.items) {
          const c = t && t.id;
          if (c != null && !beTicketSeen.has(c)) { beTicketSeen.add(c); beTickets.push(t); }
        }
      }
    }
  });

  // Bilhetes da Betano capturados pelo bn_inject.js (mundo MAIN) — as RESPOSTAS JSON de
  // GET /api/ma/bet/bet-history-v3?settled=true|false&page=N. Mesmo modelo passivo: o robô
  // só rola a lista p/ a página paginar (levas de 10, cursor lastId); a extensão lê o dado
  // exato (BetId, Stake, DecimalOdds, Status, PlacedAt, Legs/Selections), sem OCR.
  // Duas abas: Liquidada (resolvidas) e Em aberto (`__aberta:true`, sem resultado).
  // `bnById` guarda 1 bilhete por BetId — a versão LIQUIDADA vence a ABERTA (quando o
  // bilhete fecha na mesma sessão, a verdade da liquidação substitui a aberta). Fim
  // autoritativo é POR LISTA (`bnFimOpen`/`bnFimSettled`): a aba ativa decide qual usar.
  const bnById = new Map();          // BetId(string) → ticket (liquidada > aberta)
  let bnFimOpen = false, bnFimSettled = false;
  let bnHookVivo = false, bnRespostas = 0;   // autodiagnóstico (espelha o da Betfair)
  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (d && d.__sharpenupBNData) {
      if (d.hook) bnHookVivo = true;
      if (typeof d.respostas === "number") bnRespostas = d.respostas;
      if (Array.isArray(d.bets)) {
        for (const t of d.bets) {
          const c = t && t.BetId;
          if (c == null) continue;
          const key = String(c);
          const ex = bnById.get(key);
          // Entra se ainda não há nada; ou se o novo é LIQUIDADO e o guardado era ABERTO.
          if (!ex || (ex.__aberta && !t.__aberta)) bnById.set(key, t);
        }
      }
      if (d.fimOpen) bnFimOpen = true;
      if (d.fimSettled) bnFimSettled = true;
    }
  });

  // Bilhetes da BETFAIR capturados pelo bf_inject.js (mundo MAIN) — as RESPOSTAS JSON de
  // POST /activity/sportsbook. Mesmo modelo passivo: o robô só rola a lista p/ a página
  // paginar (levas de 10, cursor nextPageIndex); a extensão lê o dado exato (betId O/…,
  // settledDate, status WON/LOST/VOID, stake, odd, seleções), sem OCR nem extrato CSV.
  // `bfFimReal` = a página trouxe `moreAvailable:false` → fim autoritativo.
  const bfTickets = [];
  const bfTicketSeen = new Set();
  // Lista ABERTA (aba "Aberta"), balde separado: a mesma varredura sobe encerradas +
  // abertas num clique só (s197). Um bilhete que fechar entre duas capturas aparece nas
  // DUAS listas em capturas diferentes — o UPSERT por código resolve (a resolvida vence).
  const bfAbertas = [];
  const bfAbertaSeen = new Set();
  let bfFimReal = false;
  let bfPaginando = false;   // o inject está buscando páginas → não desistir por inatividade
  let bfHookVivo = false;   // o bf_inject respondeu → hook ativo na página (autodiagnóstico)
  let bfRespostas = 0;      // respostas de /activity/sportsbook que o hook viu
  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (d && d.__sharpenupBFData) {
      if (d.hook) bfHookVivo = true;
      if (typeof d.respostas === "number") bfRespostas = d.respostas;
      if (Array.isArray(d.bets)) {
        for (const t of d.bets) {
          const c = t && t.betId;
          if (c && !bfTicketSeen.has(c)) { bfTicketSeen.add(c); bfTickets.push(t); }
        }
      }
      if (Array.isArray(d.abertas)) {
        for (const t of d.abertas) {
          const c = t && t.betId;
          // Se o bilhete já veio na lista RESOLVIDA nesta mesma varredura, ele liquidou —
          // a versão resolvida vence e a aberta é descartada (nunca o contrário).
          if (c && !bfAbertaSeen.has(c) && !bfTicketSeen.has(c)) { bfAbertaSeen.add(c); bfAbertas.push(t); }
        }
      }
      if (typeof d.paginando === "boolean") bfPaginando = d.paginando;
      if (d.fim) bfFimReal = true;
    }
  });

  // Bilhetes da PINNACLE capturados pelo pn_inject.js (mundo MAIN) — as RESPOSTAS JSON de
  // POST /member-service/v2/wager-filter, já convertidas de array posicional p/ objeto
  // nomeado pelo inject. Mesmo modelo passivo + REPLAY ATIVO: o inject re-emite a busca das
  // duas abas (Decidido/Não decidido) e devolve tudo. `pnById` guarda 1 bilhete por id — a
  // versão SETTLED (resolvida) vence a ABERTA quando o bilhete fecha na mesma sessão.
  // `pnFimReal` = o inject terminou de re-emitir as duas abas → fim autoritativo.
  const pnById = new Map();          // id(string) → bilhete (resolvida > aberta)
  let pnFimReal = false;
  let pnHookVivo = false, pnRespostas = 0;   // autodiagnóstico (espelha o da Betfair)
  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (d && d.__sharpenupPNData) {
      if (d.hook) pnHookVivo = true;
      if (typeof d.respostas === "number") pnRespostas = d.respostas;
      if (Array.isArray(d.bets)) {
        for (const t of d.bets) {
          const c = t && t.id;
          if (c == null) continue;
          const key = String(c);
          const ex = pnById.get(key);
          // Entra se ainda não há nada; ou se o novo é RESOLVIDO e o guardado era ABERTO.
          if (!ex || (ex.aberta && !t.aberta)) pnById.set(key, t);
        }
      }
      if (d.fim) pnFimReal = true;
    }
  });

  // Cupons da KTO capturados pelo kto_inject.js (mundo MAIN) — as RESPOSTAS de
  // /coupon/history.json (Kambi), já normalizadas pelo inject. Mesmo modelo passivo + REPLAY
  // ATIVO: o inject repagina cada aba por `range_start` até `range.more === false`, então o
  // operador NÃO precisa clicar "Mostrar mais". `ktoById` guarda 1 cupom por couponRef (a
  // versão resolvida vence a aberta). `ktoFimReal` = o inject terminou → fim autoritativo.
  const ktoById = new Map();         // couponRef(string) → cupom
  let ktoFimReal = false;
  let ktoHookVivo = false, ktoRespostas = 0;   // autodiagnóstico (espelha Pinnacle/Betfair)
  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (d && d.__sharpenupKTOData) {
      if (d.hook) ktoHookVivo = true;
      if (typeof d.respostas === "number") ktoRespostas = d.respostas;
      if (Array.isArray(d.cupons)) {
        const aberto = (c) => (c.bets || []).some((b) => !b.status || b.status === "OPEN");
        for (const c of d.cupons) {
          if (!c || !c.ref) continue;
          const ex = ktoById.get(c.ref);
          if (!ex || (aberto(ex) && !aberto(c))) ktoById.set(c.ref, c);
        }
      }
      if (d.fim) ktoFimReal = true;
    }
  });

  // Bilhetes da TIVO capturados pelo tv_inject.js (mundo MAIN) — as RESPOSTAS do proxy
  // /api/game/p/messagetosport com {name:"gethistory"}, já normalizadas pelo inject. A Tivo
  // NÃO pagina: uma única chamada devolve a conta inteira e a própria casa carimba `Count`,
  // então `tvFimReal` chega junto com a primeira lista completa (fim autoritativo, não teto de
  // tempo). `tvById` guarda 1 bilhete por ID — a versão RESOLVIDA vence a ABERTA, porque o
  // mesmo bilhete volta liquidado numa consulta posterior.
  const tvById = new Map();          // ID(string) → bilhete
  let tvFimReal = false;
  let tvHookVivo = false, tvRespostas = 0;   // autodiagnóstico
  // Teto da consulta: a lista da casa para num limite (50 na Betfast) e não tem "mostrar
  // mais". `tvTetoSuspeito` = tocou o teto · `tvTetoResolvido` = a varredura retroativa foi
  // até o fim e não havia mais nada · `tvAlemDoTeto` = ela trouxe histórico que a tela esconde.
  let tvTetoSuspeito = false, tvTetoResolvido = false, tvAlemDoTeto = false;
  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (d && d.__sharpenupTVData) {
      if (d.hook) tvHookVivo = true;
      if (d.tetoSuspeito) tvTetoSuspeito = true;
      if (d.tetoResolvido) tvTetoResolvido = true;
      if (d.alemDoTeto) tvAlemDoTeto = true;
      if (typeof d.respostas === "number") tvRespostas = d.respostas;
      if (Array.isArray(d.tickets)) {
        const aberto = (t) => t.status === 5 || t.resultado === 0;
        // Espelha o `guardar` do tv_inject: CONTEÚDO vence esqueleto (bilhete que veio só com
        // o identificador). Sem isto o esqueleto ganhava por chegar primeiro — ele não parece
        // "aberto", então a regra resolvida-vence-aberta não o substituía (s198).
        const vazio = (t) => t.status == null && t.resultado == null && !(t.itens || []).length;
        for (const t of d.tickets) {
          if (!t || !t.id) continue;
          const ex = tvById.get(t.id);
          if (!ex) { tvById.set(t.id, t); continue; }
          if (vazio(t)) continue;
          if (vazio(ex) || (aberto(ex) && !aberto(t))) tvById.set(t.id, t);
        }
      }
      if (d.fim) tvFimReal = true;
    }
  });

  // Bilhetes da VAIDEBET capturados pelo vb_inject.js (mundo MAIN) — as respostas de
  // `POST …/WidgetReports/widgetExpandedBetHistory` (Altenar/BIA), já paginadas nas duas
  // abas pelo inject. O inject sobe o bilhete CRU (o JSON é nomeado e estável); quem
  // traduz status/esporte é o formatador abaixo + `casas/CASA_VAIDEBET.md`.
  const vbById = new Map();          // id(string) → bilhete cru
  let vbFimReal = false;
  let vbHookVivo = false, vbRespostas = 0;   // autodiagnóstico
  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (d && d.__sharpenupVBData) {
      if (d.hook) vbHookVivo = true;
      if (typeof d.respostas === "number") vbRespostas = d.respostas;
      if (Array.isArray(d.bets)) {
        // Resolvida vence aberta (o inject já aplica; aqui é a mesma regra do lado do
        // content, porque as mensagens chegam intercaladas e a última não é a mais completa).
        for (const b of d.bets) {
          if (!b || b.id == null) continue;
          const k = String(b.id);
          const ex = vbById.get(k);
          if (ex && ex.status !== 0 && b.status === 0) continue;
          vbById.set(k, b);
        }
      }
      if (d.fim) vbFimReal = true;
    }
  });

  // Bilhetes da BETNACIONAL capturados pelo bnc_inject.js (mundo MAIN) — as RESPOSTAS de
  // GET /api/v2/all-bets (BFF prod-betnacional-bets.bet6.com.br), já AGRUPADAS por
  // ticket_id pelo inject (a API devolve PERNAS soltas: múltipla de 4 = 4 objetos com o
  // mesmo ticket_id). Mesmo modelo passivo + REPLAY ATIVO: o inject varre janelas de datas
  // para trás até secar — a casa não expôs um `more:false`, então o fim é "N janelas sem
  // bilhete novo". `bncById` guarda 1 bilhete por ticket_id — a versão RESOLVIDA
  // (statusId !== 0) vence a ABERTA (Pendente), porque o bilhete volta liquidado depois.
  const bncById = new Map();         // ticket_id → bilhete agrupado
  let bncFimReal = false;
  let bncHookVivo = false, bncRespostas = 0;   // autodiagnóstico (espelha KTO/Pinnacle)
  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (d && d.__sharpenupBNCData) {
      if (d.hook) bncHookVivo = true;
      if (typeof d.respostas === "number") bncRespostas = d.respostas;
      if (Array.isArray(d.tickets)) {
        for (const t of d.tickets) {
          if (!t || !t.codigo) continue;
          const ex = bncById.get(t.codigo);
          if (ex && ex.statusId !== 0 && t.statusId === 0) continue;   // resolvida vence aberta
          bncById.set(t.codigo, t);
        }
      }
      if (d.fim) bncFimReal = true;
    }
  });

  // Bilhetes da BET365 capturados pelo b3_inject.js (mundo MAIN) — as RESPOSTAS de
  // /sportshistoryapi/summary + /confirmation (formato F|…), já parseadas pelo inject. Mesmo
  // modelo passivo + REPLAY ATIVO: o inject varre as duas listas (settled=1 resolvidas · settled=0
  // abertas) e busca o DETALHE de cada bilhete (jogo/mercado + código estável BR). `b3ById` guarda
  // 1 bilhete por bsid (chave da visão); o dedup final no backend é pelo código BR no texto.
  // `b3FimReal` = o inject terminou de varrer as listas e os detalhes → fim autoritativo.
  const b3ById = new Map();          // bsid(string) → bilhete mesclado (summary + confirmation)
  let b3FimReal = false;
  let b3HookVivo = false;
  let b3Driver = null;               // {feitos,pulados,falhas} do driver de UI (autodiagnóstico)
  let b3MsgTick = 0;                 // carimbo da última mensagem do inject → progresso do driver
  // Um inject POR FRAME responde (a área de membros da Bet365 é outra origem, em iframe).
  // Guardar por `href` em vez de uma variável única: com 2 frames, o último a falar
  // sobrescreveria o contador do outro — o top diria 0 e apagaria as respostas do iframe.
  const b3PorFrame = new Map();      // href → { respostas, history, topo }
  const b3Soma = (campo) => { let n = 0; for (const f of b3PorFrame.values()) n += (f[campo] || 0); return n; };
  window.addEventListener("message", (ev) => {
    const d = ev.data;
    if (d && d.__sharpenupB3Data) {
      b3MsgTick = Date.now();        // qualquer sinal do inject conta como "vivo" p/ o timeout
      if (d.hook) b3HookVivo = true;
      b3PorFrame.set(String(d.href || "?"), {
        respostas: typeof d.respostas === "number" ? d.respostas : 0,
        history: typeof d.history === "number" ? d.history : 0,
        topo: !!d.topo,
      });
      if (Array.isArray(d.bets)) {
        for (const t of d.bets) { if (t && t.bsid) b3ById.set(String(t.bsid), t); }
      }
      if (d.fim) b3FimReal = true;
      if (d.driver) b3Driver = d.driver;
    }
  });
  // Pede o acumulado + arranca o replay. Posta na própria window E em cada frame filho —
  // quem enxerga as chamadas da API é o inject dentro do iframe de `members.bet365.bet.br`,
  // e o postMessage do content só alcança a própria window. Cada inject repassa adiante.
  // `acao:"detalhar"` manda o inject abrir "Detalhes da Aposta" bilhete a bilhete — é o único
  // jeito de obter o código BR (só a página consegue chamar o /confirmation: o token
  // x-net-sync-term é exigido e rotaciona; provado na s178). `jaTem` = bsids já detalhados em
  // rodadas anteriores, p/ o driver pular e não pagar o clique de novo.
  function b3Pedir(dias, acao, jaTem) {
    const msg = { __sharpenupB3Req: true, dias: dias, acao: acao || "", jaTem: jaTem || [], saltos: 0 };
    try { window.postMessage(msg, "*"); } catch (e) {}
    for (let i = 0; i < window.frames.length && i < 24; i++) {
      try { window.frames[i].postMessage(msg, "*"); } catch (e) {}
    }
  }
  // Memória do DETALHE já obtido, por bsid: { code, da, legs }. Guarda o CONTEÚDO, não só a
  // marca de "já visto" — pular o clique sem ter o código faria o bilhete sair com
  // `[Código: ]` vazio e sem mercado/liga na 2ª rodada, e o UPSERT trocaria dado bom por pior.
  // Só entra quem foi capturado RESOLVIDO: bilhete detalhado enquanto aberto pode virar
  // cashout, e o bloco "Encerrar Aposta" só aparece no confirmation depois que ele resolve.
  const B3_MEM = "b3Detalhes";
  const B3_MEM_MAX = 3000;
  async function b3Lembrados() {
    try {
      const c = await chrome.storage.local.get([B3_MEM]);
      return (c[B3_MEM] && typeof c[B3_MEM] === "object") ? c[B3_MEM] : {};
    } catch (e) { return {}; }
  }
  async function b3Lembrar(novos) {
    try {
      const mapa = await b3Lembrados();
      for (const k in novos) mapa[k] = novos[k];
      const chaves = Object.keys(mapa);
      if (chaves.length > B3_MEM_MAX) {                       // poda os mais antigos
        for (const k of chaves.slice(0, chaves.length - B3_MEM_MAX)) delete mapa[k];
      }
      await chrome.storage.local.set({ [B3_MEM]: mapa });
    } catch (e) {}
  }

  function bladeSVG(w, h) {
    return '<svg viewBox="40 10 40 100" width="' + w + '" height="' + h + '" style="pointer-events:none">' +
      '<defs><linearGradient id="sharpenupBladeGrad" x1="60" y1="16" x2="60" y2="104" gradientUnits="userSpaceOnUse">' +
      '<stop offset="0" stop-color="#5BA9FF"></stop><stop offset="1" stop-color="#1E7CF0"></stop></linearGradient></defs>' +
      '<path d="M60 16 L60 90 L42 104 Z" fill="url(#sharpenupBladeGrad)"></path>' +
      '<path d="M60 16 L78 104 L60 90 Z" fill="#333B45"></path></svg>';
  }

  // ── FAB ─────────────────────────────────────────────────────────────────────
  function ensureFab(modo) {
    fabModo = modo;
    if (fab) { fab.title = modo === "texto" ? "SharpenUp — copiar bilhetes (robô)" : "SharpenUp — capturar"; return; }
    fab = document.createElement("div");
    fab.title = modo === "texto" ? "SharpenUp — copiar bilhetes (robô)" : "SharpenUp — capturar";
    S(fab, {
      position: "fixed", right: "22px", bottom: "22px", width: "52px", height: "52px",
      "border-radius": "50%", background: "linear-gradient(160deg,#161C24,#0B0E13)",
      border: "1px solid rgba(255,255,255,0.10)", display: "grid", "place-items": "center",
      cursor: "grab", "box-shadow": "0 8px 22px rgba(0,0,0,.5)", "z-index": Z,
      opacity: "0.62", transition: "opacity .18s, transform .18s, box-shadow .18s, border-color .18s",
      "touch-action": "none", "user-select": "none",
    });
    fab.innerHTML = bladeSVG(13, 29) +
      '<span style="position:absolute;right:-4px;top:-4px;width:16px;height:16px;border-radius:50%;' +
      'background:' + AZUL + ';border:2px solid #0B0E13;box-shadow:0 0 8px rgba(46,139,255,.7);' +
      'display:grid;place-items:center;pointer-events:none">' +
      '<svg viewBox="0 0 24 24" width="9" height="9" fill="none" stroke="#04101F" stroke-width="3.4" ' +
      'stroke-linecap="round" stroke-linejoin="round"><path d="M12 19V5M6 11l6-6 6 6"></path></svg></span>';

    let arr = false, mv = false, sx = 0, sy = 0, ox = 0, oy = 0;
    fab.addEventListener("pointerenter", () => { if (!arr) fabHover(true); });
    fab.addEventListener("pointerleave", () => { if (!arr) fabHover(false); });
    fab.addEventListener("pointerdown", (e) => {
      arr = true; mv = false; S(fab, { cursor: "grabbing" });
      const r = fab.getBoundingClientRect(); ox = r.left; oy = r.top; sx = e.clientX; sy = e.clientY;
      try { fab.setPointerCapture(e.pointerId); } catch (_) {}
    });
    fab.addEventListener("pointermove", (e) => {
      if (!arr) return;
      const dx = e.clientX - sx, dy = e.clientY - sy;
      if (Math.abs(dx) > 2 || Math.abs(dy) > 2) mv = true;
      const w = fab.offsetWidth, h = fab.offsetHeight;
      const x = Math.max(6, Math.min(ox + dx, innerWidth - w - 6));
      const y = Math.max(6, Math.min(oy + dy, innerHeight - h - 6));
      S(fab, { left: x + "px", top: y + "px", right: "auto", bottom: "auto" });
    });
    fab.addEventListener("pointerup", () => {
      if (!arr) return; arr = false; S(fab, { cursor: "grab" });
      if (mv) return;
      if (fabModo === "texto") iniciarRobo();
      else chrome.storage.local.set({ frameAtivo: true, frameCount: 0 });
    });
    document.documentElement.appendChild(fab);
  }
  function fabHover(on) {
    if (!fab) return;
    S(fab, {
      opacity: on ? "1" : "0.62", transform: on ? "scale(1.08)" : "none",
      "border-color": on ? "rgba(46,139,255,0.55)" : "rgba(255,255,255,0.10)",
      "box-shadow": on ? "0 10px 30px rgba(0,0,0,.55),0 0 0 4px rgba(46,139,255,.14)" : "0 8px 22px rgba(0,0,0,.5)",
    });
  }
  function removeFab() { if (fab) { fab.remove(); fab = null; } }

  // ── Desenho da região (1ª vez, modo print) ──────────────────────────────────
  function ensureDraw() {
    if (drawRoot) return;
    let dsx = 0, dsy = 0, drawing = false;
    drawRoot = document.createElement("div");
    S(drawRoot, { position: "fixed", inset: "0", "z-index": Z, cursor: "crosshair",
      background: "rgba(10,15,25,0.28)", "user-select": "none" });
    const db = document.createElement("div");
    S(db, { position: "fixed", border: "2px solid " + AZUL, "border-radius": "3px",
      "box-shadow": "0 0 0 9999px rgba(10,15,25,0.45)", display: "none", "pointer-events": "none" });
    drawRoot.appendChild(db);
    const dica = document.createElement("div");
    dica.textContent = "Arraste para enquadrar o bilhete · Esc cancela";
    S(dica, { position: "fixed", top: "16px", left: "50%", transform: "translateX(-50%)",
      background: "#0E1524", color: "#E6ECF5", font: "13px/1.4 system-ui,sans-serif",
      padding: "8px 14px", "border-radius": "8px", border: "1px solid rgba(46,139,255,0.55)",
      "pointer-events": "none", "z-index": Z });
    drawRoot.appendChild(dica);

    const pos = (x, y, w, h) => S(db, { left: x + "px", top: y + "px", width: w + "px", height: h + "px" });
    drawRoot.addEventListener("pointerdown", (e) => {
      if (e.button !== 0) return; drawing = true; dsx = e.clientX; dsy = e.clientY;
      pos(dsx, dsy, 0, 0); S(db, { display: "block" }); e.preventDefault();
    });
    drawRoot.addEventListener("pointermove", (e) => {
      if (!drawing) return;
      pos(Math.min(dsx, e.clientX), Math.min(dsy, e.clientY), Math.abs(e.clientX - dsx), Math.abs(e.clientY - dsy));
    });
    drawRoot.addEventListener("pointerup", () => {
      if (!drawing) return; drawing = false;
      const r = db.getBoundingClientRect();
      if (r.width < 12 || r.height < 12) { S(db, { display: "none" }); return; }
      chrome.storage.local.set({ frameRect: { left: r.left, top: r.top, width: r.width, height: r.height } });
    });
    const onKey = (e) => { if (e.key === "Escape") chrome.storage.local.set({ frameAtivo: false }); };
    document.addEventListener("keydown", onKey, true);
    drawRoot._cleanup = () => document.removeEventListener("keydown", onKey, true);
    document.documentElement.appendChild(drawRoot);
  }
  function removeDraw() { if (drawRoot) { if (drawRoot._cleanup) drawRoot._cleanup(); drawRoot.remove(); drawRoot = null; } }

  // ── Moldura fixa (modo print) ────────────────────────────────────────────────
  function ensureFrame(rect, count) {
    rectAtual = { left: rect.left, top: rect.top, width: rect.width, height: rect.height };
    if (frame) { atualizarContador(count); reposicionar(); return; }

    frame = document.createElement("div");
    S(frame, { position: "fixed", inset: "0", "pointer-events": "none", "z-index": Z });
    box = document.createElement("div");
    S(box, { position: "fixed", border: "2px solid " + AZUL, "border-radius": "3px",
      "box-shadow": "0 0 0 1px rgba(0,0,0,.35)", "pointer-events": "none",
      transition: "border-color .15s", "box-sizing": "border-box" });
    frame.appendChild(box);

    toolbar = document.createElement("div");
    S(toolbar, { position: "fixed", display: "inline-flex", "align-items": "center", gap: "4px",
      background: "#0E1524", border: "1px solid rgba(46,139,255,0.5)", "border-radius": "10px",
      padding: "4px 4px 4px 8px", "box-shadow": "0 8px 22px rgba(0,0,0,.5)", "pointer-events": "auto",
      cursor: "grab", "z-index": Z, font: "12px/1 system-ui,sans-serif", color: "#E6ECF5",
      "user-select": "none", "white-space": "nowrap" });
    const snap = botao(
      '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#04101F" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path><circle cx="12" cy="13" r="4"></circle></svg><b style="margin-left:5px">Snap</b>',
      { background: AZUL, color: "#04101F", padding: "7px 12px", "font-weight": "700" });
    const cnt = document.createElement("span");
    cnt.id = "su-cnt";
    S(cnt, { "font-family": "ui-monospace,monospace", "font-size": "11px", color: "#7FB2FF", padding: "0 6px" });
    const redraw = botao(
      '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 0 3-6.7L3 8"></path><path d="M3 3v5h5"></path></svg>',
      { background: "transparent", color: "#9AA6B6", padding: "7px 8px" }, "Redesenhar");
    const fechar = botao(
      '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6L6 18M6 6l12 12"></path></svg>',
      { background: "transparent", color: "#9AA6B6", padding: "7px 8px" }, "Fechar");
    toolbar.appendChild(snap); toolbar.appendChild(cnt); toolbar.appendChild(redraw); toolbar.appendChild(fechar);
    frame.appendChild(toolbar);

    handle = document.createElement("div");
    S(handle, { position: "fixed", width: "16px", height: "16px", background: AZUL,
      border: "2px solid #0B0E13", "border-radius": "4px", "pointer-events": "auto",
      cursor: "nwse-resize", "z-index": Z });
    frame.appendChild(handle);

    snap.addEventListener("click", dispararSnap);
    redraw.addEventListener("click", () => chrome.storage.local.remove("frameRect"));
    fechar.addEventListener("click", () => chrome.storage.local.set({ frameAtivo: false }));
    [snap, redraw, fechar].forEach((b) => b.addEventListener("pointerdown", (e) => e.stopPropagation()));

    arrastarBarra(); redimensionar();
    document.documentElement.appendChild(frame);
    atualizarContador(count); reposicionar();
  }

  function botao(html, estilos, titulo) {
    const b = document.createElement("button");
    b.innerHTML = html; if (titulo) b.title = titulo;
    S(b, Object.assign({ border: "none", "border-radius": "7px", cursor: "pointer",
      display: "inline-flex", "align-items": "center", "font-family": "inherit", "font-size": "12px" }, estilos));
    return b;
  }
  function reposicionar() {
    if (!box) return;
    const r = rectAtual;
    S(box, { left: r.left + "px", top: r.top + "px", width: r.width + "px", height: r.height + "px" });
    let ty = r.top - 44; if (ty < 6) ty = r.top + 6;
    S(toolbar, { left: Math.max(6, r.left) + "px", top: ty + "px" });
    S(handle, { left: (r.left + r.width - 8) + "px", top: (r.top + r.height - 8) + "px" });
  }
  function atualizarContador(count) {
    const el = document.getElementById("su-cnt");
    if (el) el.textContent = (count || 0) + " enviado" + ((count || 0) === 1 ? "" : "s");
  }
  function arrastarBarra() {
    let a = false, sx = 0, sy = 0, ol = 0, ot = 0;
    toolbar.addEventListener("pointerdown", (e) => {
      if (e.target.closest("button")) return;
      a = true; sx = e.clientX; sy = e.clientY; ol = rectAtual.left; ot = rectAtual.top;
      S(toolbar, { cursor: "grabbing" }); try { toolbar.setPointerCapture(e.pointerId); } catch (_) {} e.preventDefault();
    });
    toolbar.addEventListener("pointermove", (e) => {
      if (!a) return;
      rectAtual.left = Math.max(0, Math.min(ol + (e.clientX - sx), innerWidth - rectAtual.width));
      rectAtual.top = Math.max(0, Math.min(ot + (e.clientY - sy), innerHeight - rectAtual.height));
      reposicionar();
    });
    toolbar.addEventListener("pointerup", () => { if (!a) return; a = false; S(toolbar, { cursor: "grab" }); salvarRect(); });
  }
  function redimensionar() {
    let a = false;
    handle.addEventListener("pointerdown", (e) => { a = true; try { handle.setPointerCapture(e.pointerId); } catch (_) {} e.preventDefault(); e.stopPropagation(); });
    handle.addEventListener("pointermove", (e) => {
      if (!a) return;
      rectAtual.width = Math.max(40, Math.min(e.clientX - rectAtual.left, innerWidth - rectAtual.left));
      rectAtual.height = Math.max(40, Math.min(e.clientY - rectAtual.top, innerHeight - rectAtual.top));
      reposicionar();
    });
    handle.addEventListener("pointerup", () => { if (!a) return; a = false; salvarRect(); });
  }
  function salvarRect() {
    chrome.storage.local.set({ frameRect: { left: rectAtual.left, top: rectAtual.top, width: rectAtual.width, height: rectAtual.height } });
  }
  function dispararSnap() {
    if (capturando || !rectAtual) return;
    capturando = true;
    S(frame, { visibility: "hidden" });
    requestAnimationFrame(() => requestAnimationFrame(() => {
      chrome.runtime.sendMessage({ type: "CAPTURAR_REGIAO",
        rect: { x: rectAtual.left, y: rectAtual.top, width: rectAtual.width, height: rectAtual.height },
        vw: innerWidth, vh: innerHeight });
    }));
    clearTimeout(safety);
    safety = setTimeout(() => fimCaptura(false), 6000);
  }
  function fimCaptura(ok) {
    clearTimeout(safety); capturando = false;
    if (frame) S(frame, { visibility: "visible" });
    if (ok) {
      chrome.storage.local.get("frameCount").then(({ frameCount }) => chrome.storage.local.set({ frameCount: (frameCount || 0) + 1 }));
      if (box) { S(box, { "border-color": VERDE }); setTimeout(() => box && S(box, { "border-color": AZUL }), 350); }
    }
  }
  function removeFrame() {
    if (frame) { frame.remove(); frame = box = toolbar = handle = null; }
    capturando = false; clearTimeout(safety);
  }

  // ── Robô de texto (modo Betano) ──────────────────────────────────────────────
  const esDoc = (el) => el === document.scrollingElement || el === document.documentElement || el === document.body;
  const sTop = (el) => esDoc(el) ? (window.scrollY || document.documentElement.scrollTop) : el.scrollTop;
  const sMax = (el) => esDoc(el) ? (document.documentElement.scrollHeight - innerHeight) : (el.scrollHeight - el.clientHeight);
  const sClient = (el) => esDoc(el) ? innerHeight : el.clientHeight;
  const sTo = (el, y) => { if (esDoc(el)) scrollTo(0, y); else el.scrollTop = y; };

  function acharScroll() {
    let best = document.scrollingElement || document.documentElement;
    let score = best.scrollHeight - best.clientHeight;
    document.querySelectorAll("*").forEach((el) => {
      const ov = getComputedStyle(el).overflowY;
      if (ov !== "auto" && ov !== "scroll") return;
      const diff = el.scrollHeight - el.clientHeight;
      if (diff > score && el.clientHeight > 200) { best = el; score = diff; }
    });
    return best;
  }
  // Acha o maior grupo de elementos "irmãos parecidos" com texto médio = os cartões.
  function acharCards(root) {
    const scope = esDoc(root) ? document.body : root;
    const grupos = new Map();
    scope.querySelectorAll("*").forEach((el) => {
      const t = (el.innerText || "").trim();
      if (t.length < 40 || t.length > 3000) return;
      const cls = (typeof el.className === "string" ? el.className.trim().split(/\s+/)[0] : "") || "";
      const sig = el.tagName + "." + cls;
      if (!grupos.has(sig)) grupos.set(sig, []);
      grupos.get(sig).push(el);
    });
    let best = null, n = 0;
    grupos.forEach((arr) => { if (arr.length >= 3 && arr.length > n) { best = arr; n = arr.length; } });
    return best;
  }

  // Datas em pt-BR: "28/06/2026", "28/06/26", "28 de jun. de 2026", "28 de junho de 2026".
  const _MESES = { jan: 0, fev: 1, mar: 2, abr: 3, mai: 4, jun: 5, jul: 6, ago: 7, set: 8, out: 9, nov: 10, dez: 11 };
  function parseDatas(txt) {
    const out = [];
    let m;
    const re1 = /(\d{1,2})\/(\d{1,2})\/(\d{2,4})/g;
    while ((m = re1.exec(txt))) {
      let y = +m[3]; if (y < 100) y += 2000;
      const ts = Date.UTC(y, +m[2] - 1, +m[1]);
      if (!isNaN(ts)) out.push(ts);
    }
    const re2 = /(\d{1,2})\s+de\s+([a-zç]{3,})\.?\s+de\s+(\d{4})/g;
    while ((m = re2.exec(txt))) {
      const mes = _MESES[m[2].slice(0, 3)];
      if (mes !== undefined) out.push(Date.UTC(+m[3], mes, +m[1]));
    }
    return out;
  }

  async function iniciarRobo() {
    if (roboRodando) return;
    roboRodando = true;
    const painel = criarPainelRobo();
    let parar = false;
    painel.btnParar.onclick = () => { parar = true; };

    // Parada do robô: janela de N dias (look-back) OU até o ID do último bilhete
    // já extraído (copiar dele pra cima). Defensivo: sem data reconhecida, a janela
    // não corta → rola até o fim. Custo: o backend dedupa por ID antes da IA.
    const cfg = await chrome.storage.local.get(["lookbackDias", "casa", "stopId", "bfQtd", "bfDias", "bfFull"]);
    const N = Math.max(1, Number(cfg.lookbackDias) || 30);
    const cutoff = Date.now() - N * 86400000;
    const pisoSanidade = cutoff - 730 * 86400000;
    const casa = (cfg.casa || "").toLowerCase();
    const ctx = {
      cutoff, pisoSanidade,
      stopId: (cfg.stopId || "").trim().toUpperCase(),
      parar: () => parar,
      painel,
    };
    // Betfair: histórico ILIMITADO (não corta como a Betano) → freio por QUANTIDADE
    // (padrão 100) + dias opcional + "varrer conta inteira". A lista é por POSTAGEM
    // (a resolução fica fora de ordem), então quantidade é o freio previsível.
    if (casa === "betfair") {
      ctx.varrerTudo = !!cfg.bfFull;
      ctx.qtdMax = ctx.varrerTudo ? 0 : Math.max(1, Number(cfg.bfQtd) || 100);   // 0 = sem limite
      const dias = Number(cfg.bfDias);
      ctx.bfCutoff = (!ctx.varrerTudo && cfg.bfDias && dias > 0) ? (Date.now() - dias * 86400000) : -Infinity;
    }

    let blocos;
    if (casa === "superbet") {
      // Modo passivo (rola + lê o JSON que a página recebe). Se nada foi capturado
      // (sb_inject inativo), cai no modo clique/DOM.
      blocos = await roboSuperbetPassive(ctx);
      if (!blocos.length) { console.log("[SharpenUp] nada capturado da API → modo clique"); blocos = await roboSuperbet(ctx); }
    } else if (casa === "bet365") {
      // Passivo + detalhe por rota (b3_inject): dado exato via /sportshistoryapi (código BR
      // estável, resultado, data de encerramento, jogo/mercado). A API é a ÚNICA fonte — sem
      // fallback de DOM (raspava .myb-SettledBetItem sem código nem data; removido s182). Vazia =
      // aba do Histórico não aberta ou hook não injetado (recarregue a página com Ctrl+Shift+R).
      blocos = await roboBet365Passive(ctx);
    } else if (casa === "betesporte") {
      blocos = await roboBetesportePassive(ctx);
    } else if (casa === "betano") {
      blocos = await roboBetanoPassive(ctx);
      // Rede de segurança: se a API não trouxe NADA (aba aberta antes da extensão →
      // 1ª página perdida), cai no robô de texto atual — nunca fica pior que hoje.
      if (!blocos.length && !bnById.size) {
        console.log("[SharpenUp] Betano: API vazia → fallback texto");
        blocos = await roboScroll(ctx);
      }
    } else if (casa === "betfair") {
      // Passivo puro (bf_inject): dado exato com betId + settledDate. SEM fallback de
      // scrape DOM — a lista HTML da Betfair não tem data nem ID, scrape seria pior que
      // não enviar. API vazia (aba aberta antes da extensão) → o iniciarRobo avisa "nada
      // coletado"; basta recarregar a página da Betfair e rodar de novo.
      blocos = await roboBetfairPassive(ctx);
    } else if (casa === "pinnacle") {
      // Passivo + replay ativo (pn_inject): dado exato com id, das duas abas de uma vez
      // (Decidido na janela de dias + Não decidido inteira). SEM fallback de scrape DOM — a
      // tabela é a mesma resposta JSON que já lemos; scrape só perderia precisão. API vazia
      // (nenhum /wager-filter disparou) → o autodiagnóstico avisa; basta abrir a tela
      // "Minhas Apostas" e rodar de novo.
      blocos = await roboPinnaclePassive(ctx);
    } else if (casa === "kto") {
      // Passivo puro (kto_inject, API Kambi). SEM fallback de texto: o roboScroll genérico
      // NÃO serve para a KTO — a lista não tem linha em branco entre cupons, então o
      // innerText virava um bloco só (menu + rodapé + ~140 bilhetes) e a IA perdia o resto.
      blocos = await roboKTOPassive(ctx);
    } else if (casa === "betnacional") {
      // Passivo + replay por janelas de datas (bnc_inject). A lista da página só cobre a
      // janela exibida (~8 dias); o inject varre janelas para trás até secar. SEM fallback
      // de texto: os cards da BetNacional não têm linha em branco garantida entre bilhetes,
      // então o roboScroll genérico viraria um bloco só e a IA perderia o resto em silêncio
      // (lição da KTO, s192).
      blocos = await roboBNCPassive(ctx);
    } else if (casa === "tivo" || casa === "betfast") {
      // Passivo + replay de UMA chamada (tv_inject). O histórico não tem paginação: a casa
      // devolve a conta inteira com `Count`. SEM fallback de texto — a lista da Tivo é uma
      // tabela sem linha em branco entre bilhetes, então o roboScroll genérico viraria um
      // bloco só e a IA perderia o resto em silêncio.
      //
      // A BETFAST cai aqui de propósito (s211): é espelho da Tivo — mesmo motor
      // BetConstruct, mesmo `POST /api/game/p/messagetosport`, mesmos nomes de campo. Um
      // ramo, um inject, um formatador. O harness roda a mesma fixture pelos dois domínios
      // e compara os blocos byte a byte (`casos/betfast.mjs`).
      blocos = await roboTVPassive(ctx);
    } else if (casa === "vaidebet") {
      // Passivo + replay paginado (vb_inject). A lista NÃO carrega sozinha (a tela tem
      // "Mostrar mais apostas") e vem de 10 em 10 — o inject pagina por `pageNumber` nas duas
      // abas até `isLastPage`. SEM fallback de texto: os cards da VaideBet ficam colados num
      // grid, sem linha em branco entre bilhetes, então o roboScroll genérico viraria um
      // bloco só e a IA perderia o resto em silêncio (lição da KTO, s192).
      blocos = await roboVBPassive(ctx);
    } else {
      blocos = await roboScroll(ctx);   // genéricos
    }

    painel.remove();
    roboRodando = false;
    if (!blocos.length) {
      // Autodiagnóstico diferencial das casas-robô passivas (antes só a Betfair tinha; achado
      // #13). Distingue "hook NÃO carregou" (inject não injetou) de "endpoint mudou" (hook vivo,
      // 0 respostas) de "formato mudou / conta vazia" (respostas>0, 0 vistos). Antes tudo isso
      // caía num "Nada coletado" genérico → falha silenciosa quando a casa troca o DOM/endpoint.
      // Casas sem inject (genéricos) seguem no aviso genérico.
      const diag = {
        betfair:    { nome: "Betfair",    hook: bfHookVivo, resp: bfRespostas, vistos: bfTickets.length + bfAbertas.length },
        superbet:   { nome: "Superbet",   hook: sbHookVivo, resp: sbRespostas, vistos: sbById.size },
        betesporte: { nome: "BETesporte", hook: beHookVivo, resp: beRespostas, vistos: beTickets.length },
        betano:     { nome: "Betano",     hook: bnHookVivo, resp: bnRespostas, vistos: bnById.size },
        pinnacle:   { nome: "Pinnacle",   hook: pnHookVivo, resp: pnRespostas, vistos: pnById.size },
        kto:        { nome: "KTO",        hook: ktoHookVivo, resp: ktoRespostas, vistos: ktoById.size },
        betnacional: { nome: "BetNacional", hook: bncHookVivo, resp: bncRespostas, vistos: bncById.size },
        tivo:       { nome: "Tivo",       hook: tvHookVivo, resp: tvRespostas, vistos: tvById.size },
        // Espelho da Tivo: mesmo inject, mesmos contadores. Só o nome muda, para o
        // operador não ler "Tivo: 0 bilhetes" estando na Betfast.
        betfast:    { nome: "Betfast",    hook: tvHookVivo, resp: tvRespostas, vistos: tvById.size },
        vaidebet:   { nome: "VaideBet",   hook: vbHookVivo, resp: vbRespostas, vistos: vbById.size },
        bet365:     { nome: "Bet365",     hook: b3HookVivo, resp: b3Soma("respostas"), vistos: b3ById.size,
                      // Extras só da Bet365: em quantos frames o inject respondeu (a área de
                      // membros é outra origem, em iframe) e quantas URLs com "history" passaram
                      // sem casar o padrão — separa "não alcancei o frame certo" de "endpoint mudou".
                      extra: " · frames: " + b3PorFrame.size + " · outras URLs de histórico: " + b3Soma("history") },
      }[casa];
      if (diag) {
        const msg = diag.nome + ": 0 bilhetes. Hook: " + (diag.hook ? "ATIVO" : "NÃO carregou") +
                    " · respostas da API: " + diag.resp + " · bilhetes vistos: " + diag.vistos +
                    (diag.extra || "");
        toastLocal(msg, false);
        // Escala ao popup (persistente) SÓ na falha inequívoca: inject não carregou OU o endpoint
        // não respondeu nenhuma vez. "respostas>0 & 0 vistos" fica só no toast — pode ser conta
        // genuinamente vazia, e um alerta persistente viraria falso positivo.
        if (!diag.hook || diag.resp === 0) {
          try { chrome.storage.local.set({ lastError: msg + " — a extensão pode precisar de atualização; avise o suporte." }); } catch (e) {}
        }
      } else {
        toastLocal("Nada coletado — rolagem/estrutura não reconhecida.", false);
      }
      return;
    }
    try { chrome.storage.local.remove("lastError"); } catch (e) {}   // rodada OK → limpa diagnóstico antigo
    // BANCA antes de enviar. O envio é ÚNICO (tudo de uma vez, no fim da varredura). Se a
    // sessão morreu no meio da raspagem — restart do servidor (as sessões vivem em memória)
    // OU queda de rede — o POST volta 401/erro e, até aqui, os minutos de serviço raspado eram
    // DESCARTADOS sem recuperação (o `sendMessage` era fire-and-forget, ninguém via a falha).
    // Agora: guarda em `envioPendente`, ESPERA o {ok} do background e só limpa o banco se
    // enviou de fato. Falhou → mantém guardado e o popup mostra "Reenviar" (sem re-raspar nada).
    const texto = blocos.join("\n\n");
    try { await chrome.storage.local.set({ envioPendente: { texto: texto, n: blocos.length, casa: cfg.casa || "", ts: Date.now() } }); } catch (e) {}
    toastLocal(blocos.length + " bilhete(s) coletado(s), enviando…", true);
    let resp = null;
    try { resp = await chrome.runtime.sendMessage({ type: "ENVIAR_TEXTO", texto: texto }); } catch (e) {}
    if (resp && resp.ok) {
      try { await chrome.storage.local.remove("envioPendente"); } catch (e) {}
    } else {
      // NÃO perde nada: o texto fica bancado em `envioPendente`. O background já sinalizou a
      // causa (sessão expirou / falha de rede); aqui reforça na página que dá pra reenviar.
      toastLocal(blocos.length + " bilhete(s) guardados — a conexão caiu no envio. Reconecte no popup e clique Reenviar (nada foi perdido).", false);
    }
  }

  // Estratégia genérica (Betano & cia): rola e colhe blocos de texto, dedup por
  // conteúdo. Retorna os blocos coletados.
  async function roboScroll(ctx) {
    const cont = acharScroll();
    const vistos = new Set(), blocos = [];
    let passou = false;
    const push = (t) => {
      t = (t || "").trim();
      const k = t.replace(/\s+/g, " ").toLowerCase();
      if (k.length >= 20 && !vistos.has(k)) {
        vistos.add(k); blocos.push(t);
        for (const ts of parseDatas(k)) { if (ts < ctx.cutoff && ts > ctx.pisoSanidade) passou = true; }
      }
    };
    const coletar = () => {
      const raiz = esDoc(cont) ? document.body : cont;
      let partes = (raiz.innerText || "").split(/\n\s*\n+/);
      if (partes.length <= 2) {
        const cards = acharCards(cont);
        if (cards && cards.length) partes = cards.map((el) => el.innerText);
      }
      partes.forEach(push);
      ctx.painel.contador.textContent = blocos.length + " bilhete" + (blocos.length === 1 ? "" : "s");
    };
    sTo(cont, 0); await sleep(450);
    let estavel = 0, voltas = 0;
    while (!ctx.parar() && voltas < 400) {
      voltas++;
      coletar();
      if (passou && voltas >= 2) break;
      const top = sTop(cont), max = sMax(cont);
      if (top >= max - 2) { coletar(); break; }
      sTo(cont, top + sClient(cont) * 0.8);
      await sleep(380);
      if (Math.abs(sTop(cont) - top) < 2) { if (++estavel > 3) break; } else estavel = 0;
    }
    coletar();
    return blocos;
  }

  // ── Superbet modo API (sem clique) ───────────────────────────────────────────
  // Chama a MESMA API que a página usa (GET /tickets?status=finished, header
  // sessionId, paginação por lastId = o cursor de código). Dado estruturado e exato:
  // ticketId, coefficient (odd), payment.stake, status, dateReceived, events[].
  // Data → fuso America/São_Paulo (a API vem em UTC; sem conversão a data pula 1 dia).
  const _dbr = (iso) => {
    if (!iso) return "";
    const d = new Date(iso);
    if (isNaN(d)) return "";
    const p = new Intl.DateTimeFormat("pt-BR", { timeZone: "America/Sao_Paulo", day: "2-digit", month: "2-digit", year: "numeric" }).formatToParts(d);
    const g = (t) => (p.find((x) => x.type === t) || {}).value || "";
    return g("day") + "/" + g("month") + "/" + g("year");
  };
  const _brl = (x) => (typeof x === "number") ? x.toFixed(2).replace(".", ",") : (x != null ? String(x) : "");
  // Odd SEMPRE completa (regra primordial: nunca encurtar). Só tira ruído de float
  // (ex.: 2.2700000000000002 → 2,27), mantendo toda a precisão real.
  const _odd = (x) => (x == null) ? "" : (Math.round(x * 1e8) / 1e8).toString().replace(".", ",");
  // Betano: Stake/Return vêm como string BRL pt-BR ("R$1.914,56" = ponto milhar, vírgula
  // decimal) → número. Odd vem como string com PONTO decimal ("2.02", "33.32") → número.
  // São gramáticas diferentes: nunca usar o parser de dinheiro numa odd (comeria o ponto).
  const _brlNum = (s) => {
    if (typeof s === "number") return s;
    const n = parseFloat(String(s || "").replace(/[^\d,.-]/g, "").replace(/\./g, "").replace(",", "."));
    return isNaN(n) ? null : n;
  };
  const _oddNum = (x) => {
    if (typeof x === "number") return x;
    const n = parseFloat(String(x || "").replace(",", "."));
    return isNaN(n) ? null : n;
  };
  // BETesporte: `date` vem SEM timezone ("2026-07-02T10:55:18") = já local (America/São
  // Paulo). Só recorta AAAA-MM-DD → DD/MM/AAAA. NÃO usar `_dbr` (converte de UTC → pula 1 dia).
  const _dbrBE = (s) => {
    const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(s || ""));
    return m ? (m[3] + "/" + m[2] + "/" + m[1]) : "";
  };
  // Betfair: `settledDate`/`placedDate` vêm como "12-jul-26 17:33:53" — mês PT abreviado,
  // JÁ em horário local (o mesmo do extrato). Só converte DD-mmm-YY → DD/MM/AAAA. NÃO usar
  // `_dbr` (é p/ ISO UTC → pularia 1 dia). Espelha o `_betfair_data` do backend.
  //
  // O PONTO da abreviação é OPCIONAL (`\.?`). Em 25/07/2026 a Betfair passou a emitir
  // "18-jul.-26 12:12:42" (abreviação pt-BR correta, com ponto) no lugar de "18-jul-26".
  // O regex antigo casava "jul", esperava "-" e encontrava "." → NÃO casava → data vazia em
  // 100% dos bilhetes. Como Data é a 1ª coluna do TSV, a linha inteira saía deslocada e era
  // rejeitada no /salvar: 5 dias de bilhetes liquidados não entraram (sessão 191). Aceitar o
  // ponto é estritamente permissivo — o formato sem ponto segue casando igual.
  const _MESES_BF = { jan: "01", fev: "02", mar: "03", abr: "04", mai: "05", jun: "06",
                      jul: "07", ago: "08", set: "09", out: "10", nov: "11", dez: "12" };
  const _dbrBF = (s) => {
    const m = /^\s*(\d{1,2})-([a-zç]{3})\.?-(\d{2})/.exec(String(s || "").toLowerCase());
    if (!m) return "";
    const mes = _MESES_BF[m[2]];
    return mes ? (m[1].padStart(2, "0") + "/" + mes + "/20" + m[3]) : "";
  };

  function formatTicket(t) {
    const pay = t.payment || {};
    const win = t.win || {};
    const stake = pay.stake != null ? pay.stake : pay.total;
    const evs = t.events || [];
    // Bilhete da aba "Em aberto" (URL status=active): ainda não liquidou. Sobe SEM
    // resultado (a IA deixa a coluna Resultado vazia → o backend grava 'aberta'); a odd
    // vai a estrutural (coefficient). Quando fechar, a re-extração (mesmo ticketId) faz
    // UPSERT e atualiza resultado/odd. Nunca liquidar um aberto pelo status.
    const aberta = !!t.__aberta;
    const cashout = !aberta && !!win.isCashedOut;
    const L = [];
    L.push("[Código: " + (t.ticketId || "") + "]");
    // Data = a do EVENTO mais recente (quando o bilhete resolve), não a de criação.
    const datasEv = evs.map((e) => (e.date ? Date.parse(e.date) : NaN)).filter((x) => !isNaN(x));
    const dataJogo = datasEv.length ? new Date(Math.max.apply(null, datasEv)).toISOString() : t.dateReceived;
    L.push("Data: " + _dbr(dataJogo));
    L.push("Apostado em: " + _dbr(t.dateReceived));
    L.push("Stake: " + _brl(stake));
    if (pay.bonusAmount) L.push("Freebet incluído: " + _brl(pay.bonusAmount) + " (dinheiro real = stake − freebet)");
    // Odd COMPLETA p/ cálculo: em VITÓRIA com boost (SUPERTURBO) a coefficient é
    // PRÉ-boost → a odd efetiva (que reconstrói o retorno) = retorno ÷ stake. Aberta =
    // coefficient estrutural (sem retorno realizado ainda).
    const efetiva = (!aberta && t.status === "win" && !cashout && win.payoff > 0 && stake > 0)
      ? (win.payoff / stake) : t.coefficient;
    L.push("Odd total: " + _odd(efetiva));
    // Resultado bruto: a IA/CASA_SUPERBET aplica a regra (win→W, lost→L, cashout→V/W).
    let st = aberta ? "em aberto (aguardando resultado — NÃO liquidar; sem resultado)"
                    : (cashout ? "cashout" : (t.status || ""));
    // Em aberto, `win.payoff` é ganho POTENCIAL (não realizado) → rotula como tal.
    L.push("Status: " + st + (win.payoff != null ? ((aberta ? " · ganho potencial " : " · retorno ") + _brl(win.payoff)) : ""));
    L.push("Seleções (" + evs.length + "):");
    for (const e of evs) {
      const nome = Array.isArray(e.name) ? e.name.join(" — ") : (e.name || "");
      const mkt = (e.market && e.market.name) || "";
      let sel = (e.odd && e.odd.name) || "";
      if (sel && sel === mkt) sel = "";   // evita duplicação (mercado == seleção)
      let desc = [mkt, sel].filter(Boolean).join(" — ");
      // Criar Aposta / bet-builder: mercado/odd vazios no topo → as sub-seleções ficam
      // em eventComponents (cada uma: market.name + oddComponent.name).
      const comps = Array.isArray(e.eventComponents) ? e.eventComponents : [];
      if (!desc && comps.length) {
        desc = comps.map((c) => {
          const cm = (c.market && c.market.name) || "";
          const cs = (c.oddComponent && c.oddComponent.name) || "";
          return [cm, cs].filter(Boolean).join(": ");
        }).filter(Boolean).join(" + ");
      }
      const oc = e.odd && e.odd.coefficient;
      const dt = _dbr(e.date);
      L.push("  • " + (dt ? dt + " · " : "") + nome + (desc ? " · " + desc : "") +
             (oc != null ? " @ " + _odd(oc) : ""));
    }
    return L.join("\n");
  }

  // Modo passivo: rola a lista p/ a página paginar (lazy-load) e vai consumindo os
  // tickets que o sb_inject captura das RESPOSTAS da API (JSON exato do site). Sem
  // clique. Para no stopId (copiar dele pra cima) ou na janela de dias.
  // Scroller da lista: `.sb-my-bets__items` se ele mesmo rolar; senão o maior
  // scroller da página (geralmente o document).
  function acharScrollSuperbet() {
    const c = document.querySelector(".sb-my-bets__items");
    if (c && c.scrollHeight > c.clientHeight + 20) return c;
    return acharScroll();
  }

  async function roboSuperbetPassive(ctx) {
    const cont = acharScrollSuperbet();
    const blocos = [], usados = new Set();
    let travado = false;
    // Aba "Em aberto" (/minhas-apostas/abertos): abertas são recentes → a janela de dias
    // NÃO corta (senão uma liquidada velha ainda em memória interromperia antes das abertas).
    const naAbaAberta = /abertos/i.test(location.pathname);

    const processar = () => {
      for (const t of sbById.values()) {
        const cod = (t.ticketId || "").toUpperCase();
        if (!cod || usados.has(cod)) continue;
        if (ctx.stopId && cod === ctx.stopId) { travado = true; return; }   // último já extraído
        usados.add(cod);
        const dt = t.dateReceived ? Date.parse(t.dateReceived) : NaN;
        // Janela de dias corta só LIQUIDADAS e só fora da aba Em aberto.
        const passou = !naAbaAberta && !t.__aberta && !isNaN(dt) && dt < ctx.cutoff && dt > ctx.pisoSanidade;
        blocos.push(formatTicket(t));
        ctx.painel.contador.textContent = blocos.length + " bilhete" + (blocos.length === 1 ? "" : "s");
        if (passou) { travado = true; return; }   // passou da janela → para
      }
    };

    // Pede ao sb_inject o que ele já capturou (a 1ª página vem no load da página,
    // antes deste content script estar pronto pra ouvir).
    try { window.postMessage({ __sharpenupSBReq: true }, "*"); } catch (e) {}
    await sleep(250);
    processar();                 // o que já veio no load da página

    // Rola JANELA + container até o fim, repetidamente, até a página parar de trazer
    // bilhetes novos (dispara o lazy-load independe de qual elemento rola de fato).
    let semNovo = 0, ultTotal = -1, voltas = 0;
    while (!ctx.parar() && !travado && voltas < 500) {
      voltas++;
      try { window.scrollTo(0, document.documentElement.scrollHeight); } catch (e) {}
      try { if (cont && cont !== document.scrollingElement && cont !== document.documentElement) cont.scrollTop = cont.scrollHeight; } catch (e) {}
      await sleep(700);
      processar();
      if (travado) break;
      if (sbById.size > ultTotal) { ultTotal = sbById.size; semNovo = 0; }
      else if (++semNovo >= 5) break;   // 5 rolagens sem nada novo → fim da lista
    }
    processar();
    console.log("[SharpenUp] passivo: " + blocos.length + " bilhete(s) · sbById=" + sbById.size +
                " · aba=" + (naAbaAberta ? "abertas" : "liquidadas"));
    return blocos;
  }

  // ── BETesporte modo API (sem clique) ─────────────────────────────────────────
  // Formata 1 item da /api/bet/RequestUserTickets no bloco de texto que a IA lê
  // (mesmo marcador "[Código: …]" da Superbet → o backend split/dedupa por ele).
  // Status: 1=Perdido(L), 2=Ganho(W) — os únicos observados. Perna ABERTA (openBetsCount>0)
  // → sobe SEM resultado ('aberta'; UPSERT por código atualiza quando fechar). Devolvido/
  // Encerrado/Cancelado ainda sem amostra → "a conferir" (regra da casa: nunca chutar resultado).
  function formatTicketBE(t) {
    const L = [];
    L.push("[Código: " + (t.id != null ? t.id : "") + "]");
    L.push("Data: " + _dbrBE(t.date));
    L.push("Stake: " + _brl(t.value));
    L.push("Odd: " + _odd(t.odd));
    // "possibleReturn" = value × odd = retorno POTENCIAL (não o realizado). Rotulado
    // como tal p/ a IA nunca confundir o potencial de um bilhete PERDIDO com vitória —
    // quem decide W/L é o Status. Em W, potencial = realizado (cross-check: ÷ stake = odd).
    if (t.possibleReturn != null) L.push("Retorno potencial: " + _brl(t.possibleReturn));
    if (t.cashoutValue && t.cashoutValue > 0) L.push("Cashout: " + _brl(t.cashoutValue));
    let st;
    // Aberta (perna ainda não liquidada): sobe SEM resultado → o backend grava 'aberta'
    // e faz UPSERT por código quando o bilhete fechar (atualiza, não duplica). Sinal
    // explícito (igual à Betano) p/ a IA deixar a coluna Resultado vazia, nunca chutar.
    if (t.openBetsCount && t.openBetsCount > 0) st = "em aberto (aguardando resultado — NÃO liquidar; sem resultado)";
    else if (t.status === 1) st = "1 (Perdido → L)";
    else if (t.status === 2) st = "2 (Ganho → W)";
    else st = t.status + " (a conferir — não liquidar automaticamente)";
    L.push("Status: " + st);
    const mercado = (t.betNome || "").trim();
    const titulo = (t.partidaNome || t.homeTeamName || "").trim();
    if (mercado) L.push("Mercado: " + mercado);
    if (titulo && titulo !== mercado) L.push("Título: " + titulo);
    if (t.optionNome) L.push("Seleção: " + t.optionNome);
    return L.join("\n");
  }

  // ── Betano modo API (sem clique) ─────────────────────────────────────────────
  // Formata 1 bilhete da /api/ma/bet/bet-history-v3 no bloco de texto que a IA lê (mesmo
  // marcador "[Código: …]" das outras casas → o backend split/dedupa por ele). Datas em
  // UTC ("…Z") → America/São_Paulo (_dbr). Fiel ao CASA_BETANO §4/§5/§11:
  //   • Data = PlacedAt (colocação; proxy do evento p/ mesmo-dia — a casa não expõe a do jogo).
  //   • Status do bilhete: 2=Ganho→W · 3=Perdido→L · 0=Devolvido/Anulado→V. `Return` cruza
  //     (Ganhos=0→L, =Stake→V, >Stake→W) — quem decide W/L/V é o pipeline, não a extensão.
  //   • Odd: W = Return÷Stake com precisão total (respeita boost, §11) · L/V = odd combinada
  //     estrutural (DecimalOdds; já é o produto das seleções nas múltiplas).
  const _TIPO_BN = { Single: "Simples", Double: "Dupla", Triple: "Tripla" };
  function formatTicketBN(t) {
    const L = [];
    // Bilhete da aba "Em aberto": ainda não liquidou. Sobe SEM resultado (a IA deixa a
    // coluna Resultado vazia → o backend grava 'aberta'). A odd vai a estrutural
    // (DecimalOdds); quando o bilhete fechar, a re-extração (mesmo BetId) faz UPSERT e
    // atualiza resultado/odd. Nunca liquidar um bilhete aberto pelo Status numérico.
    const aberta = !!t.__aberta;
    const stake = _brlNum(t.Stake);
    const ret = _brlNum(t.Return);
    const legs = Array.isArray(t.Legs) ? t.Legs : [];
    const legItems = [];
    for (const lg of legs) for (const li of (lg.LegItems || [])) legItems.push(li);
    const criarAposta = legItems.some((li) => li.ComboLegType === 1);

    L.push("[Código: " + (t.BetId != null ? t.BetId : "") + "]");
    L.push("Data: " + _dbr(t.PlacedAt));
    let tipo = _TIPO_BN[t.Type];
    if (!tipo) {
      const acc = t.Accumulator || "";
      // "3-fold" etc. serve; o placeholder cru "{number}-fold" da API não → usa a contagem de pernas.
      if (acc && acc !== "Single" && acc.indexOf("{") < 0) tipo = acc;
      else if (legItems.length > 1) tipo = legItems.length + "-seleções";
      else tipo = t.Type || "";
    }
    if (criarAposta) tipo = (tipo ? tipo + " " : "") + "(Criar Aposta)";
    if (tipo) L.push("Tipo: " + tipo);
    L.push("Stake: " + _brl(stake));

    // Resultado bruto — a IA/CASA_BETANO aplica a regra final. Status do bilhete:
    //   2=Ganho→W · 3=Perdido→L · 0=Devolvido/Anulado→V · 6=Cash Out (regra financeira §7).
    // Cashout (Status 6, confirmado): sacado = stake → V (odd exibida) · ≠ stake → W
    // (Odd = Cashout÷Stake; cobre o parcial: retorno<stake vira W com odd<1, preserva o recuperado).
    const cashout = !aberta && ((t.Status === 6) || !!t.IsCreditCashout);
    const cashoutEqStake = cashout && ret != null && stake != null && Math.abs(ret - stake) < 0.005;
    let stTxt;
    if (aberta) stTxt = "em aberto (aguardando resultado — NÃO liquidar; sem resultado)";
    else if (cashoutEqStake) stTxt = "Cash Out (sacado = stake) → V";
    else if (cashout) stTxt = "Cash Out (sacado ≠ stake) → W";
    else if (t.Status === 2) stTxt = "Ganho → W";
    else if (t.Status === 3) stTxt = "Perdido → L";
    else if (t.Status === 0) stTxt = "Devolvido/Anulado → V";
    else stTxt = t.Status + " (a conferir — não liquidar automaticamente)";
    // Em aberto: `Return` é potencial (não realizado) → rotula como tal p/ a IA nunca
    // confundir com vitória. Liquidado: `Return` é o retorno real.
    L.push("Status: " + stTxt + (t.Return != null ? ((aberta ? " · Retorno potencial " : " · Retorno ") + t.Return) : ""));
    if (cashout && t.Return != null) L.push("Cash Out: " + t.Return);   // sinal explícito p/ o pipeline

    // Odd total: W (Ganho OU cashout≠stake) = Return÷Stake (respeita boost, §11); L/V/cashout=stake
    // e ABERTA = odd combinada estrutural (DecimalOdds; já é o produto das pernas nas múltiplas).
    const oddW = !aberta && ret != null && stake > 0 && (t.Status === 2 || (cashout && !cashoutEqStake));
    const oddTot = oddW ? (ret / stake)
                 : (typeof t.DecimalOdds === "number" ? t.DecimalOdds : _oddNum(t.Odds));
    L.push("Odd total: " + _odd(oddTot) + (oddW ? " (= Retorno ÷ Stake)" : ""));

    L.push("Seleções:");
    for (const li of legItems) {
      const legOdd = (typeof li.DecimalOdds === "number") ? li.DecimalOdds : _oddNum(li.Odds);
      const sels = Array.isArray(li.Selections) ? li.Selections : [];
      if (li.ComboLegType === 1 && sels.length > 1) {
        // Criar Aposta: sub-seleções combinadas numa perna, odd única (não repetir por sub).
        const game = (sels[0] && sels[0].Game) || "";
        L.push("  • [Criar Aposta @ " + _odd(legOdd) + "]" + (game ? " " + game : "") + ":");
        for (const s of sels) L.push("      - " + (s.Title || "") + (s.Market ? " · " + s.Market : ""));
      } else {
        for (const s of sels) {
          const so = _oddNum(s.Odd);
          const boost = (s.OddsBeforeEnhancement && s.OddsBeforeEnhancement !== s.Odd)
            ? " (sem boost " + String(s.OddsBeforeEnhancement).replace(".", ",") + ")" : "";
          const partes = [s.Sport, s.Game, s.Market, s.Title].filter(Boolean).join(" · ");
          L.push("  • " + partes + " @ " + _odd(so != null ? so : legOdd) + boost);
        }
      }
    }
    return L.join("\n");
  }

  // ── Betfair modo API (sem clique) ─────────────────────────────────────────────
  // Formata 1 bilhete do POST /activity/sportsbook no bloco de texto que a IA lê (mesmo
  // marcador "[Código: O/…]" das outras casas passivas → o backend split/dedupa por ele).
  // Datas: settledDate/placedDate vêm "DD-mmm-YY HH:MM:SS" JÁ em horário local (_dbrBF).
  // Fiel ao CASA_BETFAIR §4/§5/§11:
  //   • Data = settledDate (RESOLUÇÃO — existe até nas perdas, ao contrário do extrato CSV).
  //   • Status: WON→W · LOST→L · VOID→V · cashout (fullCashout/isPartialCashOut) → regra §7.
  //   • Odd: W = rawPotentialReturn÷rawStake (precisão total, respeita boost/ODDSBOOST) ·
  //     L/V = odd exibida (originalOdds.decimal, nunca 0/1) · múltipla = combinedOdds.
  const _TIPO_BF = { SGL: "Simples" };
  function formatTicketBF(t) {
    const L = [];
    const stake = (typeof t.rawStake === "number") ? t.rawStake : _brlNum(t.stake);
    const ret = (typeof t.rawPotentialReturn === "number") ? t.rawPotentialReturn : _brlNum(t.potentialReturn);
    const oddDec = _oddNum((t.originalOdds && t.originalOdds.decimal) || t.combinedOdds);
    const combined = _oddNum(t.combinedOdds);
    const parts = Array.isArray(t.parts) ? t.parts : null;
    const st = String(t.status || t.result || "").toUpperCase();
    const isMult = (t.betType && t.betType !== "SGL") || (parts && parts.length > 1) || combined != null;

    L.push("[Código: " + (t.betId || "") + "]");
    L.push("Data: " + _dbrBF(t.settledDate));   // resolução (col Data); nunca a colocação
    if (t.placedDate) L.push("Apostado em: " + _dbrBF(t.placedDate));
    if (t.sportName) L.push("Esporte (casa): " + t.sportName + (t.competitionName ? " · " + t.competitionName : ""));

    L.push("Tipo: " + (_TIPO_BF[t.betType] || (isMult ? "Múltipla" : "Simples")));
    L.push("Stake: " + _brl(stake));
    // Freebet faz PARTE do stake (dinheiro real = stake − freebet) → não pode ser MAIOR
    // que o stake. Valor absurdo (visto num Each Way de outright: 10000 num stake de 200)
    // = leitura errada do campo → não exibe, senão gera "dinheiro real" negativo.
    if (t.stakeBonus) {
      const fb = _brlNum(t.stakeBonus);
      if (fb != null && fb > 0 && fb <= stake)
        L.push("Freebet incluído: " + _brl(fb) + " (dinheiro real = stake − freebet)");
    }

    // Status/resultado bruto — a IA/CASA_BETFAIR aplica a regra final (nunca copiar o
    // código visual V/P/N da tela; aqui já vem o status textual limpo do JSON).
    const cashout = !!t.fullCashout || !!t.isPartialCashOut;

    // `status` fora de WON/LOST/VOID num bilhete JÁ LIQUIDADO → quem decide é a conferência
    // financeira do CASA_BETFAIR §5 (`Ganhos = 0` → L · `= Valor Apostado` → V · `>` → W).
    // Caso real: Each Way com `status:"PLACED"` (= "colocou", não "em aberto") e
    // `result:"SETTLED"` + `settledDate` — o código lia o status cru, dizia "a conferir", a
    // IA deixava a coluna Resultado vazia e o bilhete virava `aberta` para sempre; um W de
    // R$530 sobre R$200 ficou fora do P/L desde 20/07 (s195). Só age em bilhete liquidado:
    // aposta genuinamente em aberto NÃO tem `settledDate` nem `result` de liquidação, então
    // segue caindo no "a conferir" e sobe sem resultado, como deve.
    const _RES_LIQ = ["SETTLED", "WON", "LOST", "VOID", "CASHED_OUT"];
    const liquidado = !!t.settledDate || _RES_LIQ.indexOf(String(t.result || "").toUpperCase()) >= 0;
    let stFin = "";   // código deduzido pelo DINHEIRO quando o rótulo não resolve
    if (!cashout && liquidado && ret != null && stake > 0 &&
        st !== "WON" && st !== "LOST" && st !== "VOID") {
      if (ret === 0) stFin = "L";
      else if (Math.abs(ret - stake) < 0.005) stFin = "V";
      else if (ret > stake) stFin = "W";
      // 0 < Retorno < Stake não é coberto pelo §5 → fica "a conferir" (nunca chutar).
    }

    // ABERTA (aba "Aberta", `status:"OPEN"`): sem `settledDate` e sem `result` de liquidação.
    // Sobe SEM resultado — MASTER_RESULTADO §1.1: nunca chutar o resultado de uma aposta
    // aberta. A Data fica VAZIA de propósito (a coluna Data É a data de resolução, §4.A, e
    // ela ainda não existe); quando o bilhete liquidar, o UPSERT por código preenche.
    const aberta = !liquidado && (st === "OPEN" || !!t.__aberta);

    // CASH OUT: o rótulo `status` é INÚTIL aqui — o mesmo desfecho aparece como "LOST"
    // (bilhete O/…0001821) e como "WON" (O/…0001807). Quem decide é o dinheiro, como manda
    // o MASTER_RESULTADO §5.1.2 / §5.6: Cash Out == Stake → V (desistiu, saiu no zero) ·
    // Cash Out != Stake → W com odd = Cash Out ÷ Stake. Antes o código mandava "regra §7"
    // com "Odd total: 1", e a IA gravava W/odd 1 num bilhete que era V.
    const coIgualStake = cashout && ret != null && stake > 0 && Math.abs(ret - stake) < 0.005;

    let stTxt;
    if (aberta) stTxt = "em aberto (aguardando resultado — NÃO liquidar; deixe Resultado VAZIO)";
    else if (cashout) {
      stTxt = "Cash Out (" + (t.isPartialCashOut ? "parcial" : "total") + ") → " +
              (coIgualStake ? "V — Cash Out = Stake (§5.1.2), use a odd exibida"
                            : "W — odd = Cash Out ÷ Stake (§5.6)");
    }
    else if (st === "WON") stTxt = "WON → W";
    else if (st === "LOST") stTxt = "LOST → L";
    else if (st === "VOID") stTxt = "VOID → V";
    else if (stFin) stTxt = st + " (liquidado) → " + stFin + " — §5 conferência financeira (Retorno vs Stake)";
    else stTxt = st + " (a conferir — não liquidar automaticamente)";
    // Em aposta aberta o retorno é POTENCIAL (= Stake × Odd) e NUNCA decide W (§1.1) —
    // rotular é obrigatório, senão a IA lê um retorno > 0 e conclui vitória.
    const rotRet = aberta ? " · Retorno POTENCIAL (ainda não realizado) " : " · Retorno ";
    L.push("Status: " + stTxt + (t.potentialReturn != null ? (rotRet + t.potentialReturn) : ""));
    if (cashout && t.potentialReturn != null) L.push("Cash Out: " + t.potentialReturn);

    // Odd total: W (WON, W deduzido pelo §5, ou cashout com retorno) = Retorno÷Stake
    // (precisão total, respeita boost/ODDSBOOST); L/V = odd exibida; múltipla sem win =
    // combinedOdds estrutural.
    // Aberta NUNCA usa Retorno÷Stake (o retorno é potencial, §1.1) → cai na odd exibida.
    // Cash Out igual à stake é V → também usa a odd exibida, não 1.
    // Em CASHOUT o `status` não vale (1765 e 1807 vêm "WON" e são V): o ramo do cashout
    // decide sozinho, e o rótulo WON não pode reativar Retorno÷Stake por fora.
    const oddW = !aberta && ret != null && stake > 0 &&
                 (cashout ? (ret > 0 && !coIgualStake) : (st === "WON" || stFin === "W"));
    let oddTot = oddW ? (ret / stake) : (isMult && combined != null ? combined : oddDec);
    // Múltipla perdida às vezes vem SEM combinedOdds nem originalOdds.decimal → reconstrói
    // a odd combinada pelo PRODUTO das pernas (cada `part` traz a sua odd). Só quando TODAS
    // as pernas têm odd válida (senão deixa vazio, honesto — nunca inventa odd parcial).
    if (oddTot == null && isMult && parts && parts.length) {
      let prod = 1, ok = true;
      for (const p of parts) {
        const po = _oddNum((p.originalOdds && p.originalOdds.decimal) || p.odds || p.decimalOdds);
        if (po != null && po > 0) prod *= po; else { ok = false; break; }
      }
      if (ok) oddTot = prod;
    }
    L.push("Odd total: " + _odd(oddTot) + (oddW ? " (= Retorno ÷ Stake)" : ""));

    L.push("Seleções:");
    if (isMult && parts && parts.length) {
      for (const p of parts) {
        const po = _oddNum((p.originalOdds && p.originalOdds.decimal) || p.odds || p.decimalOdds);
        const desc = [p.eventDescription, p.marketName, p.selection].filter(Boolean).join(" · ");
        L.push("  • " + desc + (po != null ? " @ " + _odd(po) : ""));
      }
    } else {
      const mt = t.marketType ? " [" + t.marketType + "]" : "";
      const hcp = (t.handicap != null && t.handicap !== "") ? " (handicap " + t.handicap + ")" : "";
      const desc = [t.eventDescription, (t.marketName || t.eventMarketDescription || "") + mt, t.selection].filter(Boolean).join(" · ");
      L.push("  • " + desc + hcp + (oddDec != null ? " @ " + _odd(oddDec) : ""));
    }
    return L.join("\n");
  }

  // ── Pinnacle modo API (sem clique) ────────────────────────────────────────────
  // Formata 1 bilhete do POST /wager-filter (já convertido de array posicional p/ objeto
  // pelo pn_inject) no bloco de texto que a IA lê (mesmo marcador "[Código: …]" das outras
  // casas passivas → o backend split/dedupa por ele). Fiel à CASA_PINNACLE:
  //   • Data = data do EVENTO (§4: evento ≈ liquidação; a colocação NUNCA é usada).
  //   • Decimal exibido com PONTO → vírgula (§1). Odd preservada na precisão original (§11).
  //   • Sem boost e sem cashout (§6/§7) — mas isso NÃO torna a exibida autoritativa: em W a
  //     odd é Retorno÷Stake, e o Retorno sai do P/L (Stake + P/L). O P/L não é cross-check,
  //     é o insumo. A exibida vale só em L/V/HW/HL e nas abertas. Ver CASA_PINNACLE §11.
  //   • Resultado: WON→W · LOST→L · PUSHED/Void→V · quarto de handicap pode dar HW/HL (§5);
  //     a IA decide o código final — a extensão só entrega o rótulo cru + o P/L p/ conferir.
  //   • Aberta (status ≠ SETTLED): sobe SEM resultado → o backend grava 'aberta' e faz UPSERT
  //     por id quando o bilhete fechar (atualiza, não duplica).
  // Datas "YYYY-MM-DD" (evento) já são locais (America/São Paulo) → só recorta DD/MM/AAAA
  // (NÃO usar _dbr, que converte de UTC e pularia 1 dia).
  const _dbrPN = (s) => {
    const m = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(s || ""));
    return m ? (m[3] + "/" + m[2] + "/" + m[1]) : "";
  };
  // Odd Pinnacle: string com PONTO ("1.636", "18.060") → vírgula, precisão intacta.
  const _oddPN = (s) => {
    const str = String(s == null ? "" : s).trim();
    return str ? str.replace(".", ",") : "";
  };
  // Linha (handicap/total): número → texto pt-BR. NÃO força "+": em Over/Under a linha é um
  // total (ex.: 20,5, sem sinal) e um "+" seria enganoso; em handicap positivo a IA deduz o
  // sinal pelo contexto (seleção = time + linha), como a CASA_PINNACLE ensina. O "-" natural
  // do handicap negativo é preservado.
  const _linhaPN = (n) => (n == null || n === 0) ? "" : String(n).replace(".", ",");

  function formatTicketPN(t) {
    const L = [];
    L.push("[Código: " + (t.id != null ? t.id : "") + "]");
    L.push("Data: " + _dbrPN(t.dataEvento));                 // data do evento (a que vale)
    if (t.dataColoc) L.push("Apostado em: " + _dbrPN(t.dataColoc));
    L.push("Stake: " + _brl(t.stake));

    // Resultado bruto — a IA/CASA_PINNACLE aplica a regra final. Aberta = sem resultado.
    let stTxt;
    if (t.aberta) {
      stTxt = "em aberto (aguardando resultado — NÃO liquidar; sem resultado)";
    } else {
      const rot = String(t.resultLabel || t.resultRaw || "").toUpperCase();
      if (rot === "WON" || rot === "WIN") stTxt = "Ganho (WON) → W";
      else if (rot === "LOST" || rot === "LOSE") stTxt = "Perdeu (LOST) → L";
      else if (rot === "PUSHED" || rot === "PUSH" || rot === "VOID" || rot === "REFUND") stTxt = rot + " → V";
      else stTxt = (rot || "?") + " (a conferir — não liquidar automaticamente)";
    }
    // P/L líquido (Vitória/derrota) — cross-check p/ a IA distinguir HW/HL de W/L cheio.
    // Nunca é cashout (Pinnacle não tem): é o P/L de liquidação normal.
    const plTxt = (t.plNet != null && !t.aberta) ? " · P/L " + _brl(t.plNet) : "";
    L.push("Status: " + stTxt + plTxt);
    L.push("Odd total: " + _oddPN(t.odd));

    // Múltipla (Mix Parlay): sinaliza o tipo p/ a IA classificar (MASTER_ESPORTES: mistura de
    // esportes OU 3+ jogos diferentes → Múltiplos). Simples: esporte genérico (§13: nunca
    // promover p/ a liga). Localização (Tennis→Tênis…) fica com a IA/CASA_PINNACLE.
    if (t.pernas && t.pernas.length) {
      L.push("Tipo: Múltipla (" + t.pernas.length + " seleções)");
    } else if (t.esporte) {
      L.push("Esporte (casa): " + t.esporte + (t.liga ? " · " + t.liga : ""));
    }

    L.push("Seleções:");
    if (t.pernas && t.pernas.length) {
      // Múltipla (Mix Parlay): cada perna com seu confronto, seleção, linha, odd e data.
      for (const p of t.pernas) {
        const lin = _linhaPN(p.linha);
        const sel = (p.selecao + (lin ? " " + lin : "")).trim();
        const partes = [p.esporte, p.liga, sel, _confrontoPN(p.confronto)].filter(Boolean).join(" · ");
        const un = p.unidade ? " (" + p.unidade + ")" : "";
        L.push("  • " + partes + un +
               (p.odd ? " @ " + _oddPN(p.odd) : "") +
               (p.dataEvento ? " · " + _dbrPN(p.dataEvento) : ""));
      }
    } else {
      // Simples: seleção (ou lado "Mais de/Menos de" + prop) + linha, depois o confronto.
      const conf = _confrontoPN(t.confronto);
      const pick = t.selecao || [t.ladoSel, t.titulo].filter(Boolean).join(" ");
      const lin = _linhaPN(t.linha);
      const un = t.unidade ? " (" + t.unidade + ")" : "";
      const cat = t.categoria ? " [" + t.categoria + "]" : "";
      L.push("  • " + [(pick + (lin ? " " + lin : "")).trim(), conf].filter(Boolean).join(" · ") + un + cat);
    }
    return L.join("\n");
  }
  // Confronto: a Pinnacle usa "A -vs- B"; a descrição global usa "A v B". Normaliza aqui
  // (a IA também sabe, mas entregar já limpo evita ruído). Remove placar ao vivo "[0-0]".
  function _confrontoPN(s) {
    return String(s || "").replace(/\s*\[[0-9]+-[0-9]+\]\s*/g, " ")
      .replace(/\s*-vs-\s*/gi, " v ").replace(/\s+/g, " ").trim();
  }

  // Acha o elemento clicável VISÍVEL cujo rótulo contém a frase (menor texto = o mais
  // específico). Botões/links primeiro; se não achar, um elemento com o texto exato e
  // sobe pro ancestral clicável. Usado p/ "CARREGAR MAIS…" e "FILTRAR".
  const _normBtn = (s) => (s || "").replace(/\s+/g, " ").trim().toLowerCase();
  const _acharBotao = (frase) => {
    let best = null, bestLen = Infinity;
    for (const b of document.querySelectorAll("button, a, [role=button], .btn, input[type=button], input[type=submit]")) {
      if (b.offsetParent === null) continue;
      const t = _normBtn(b.textContent || b.value);
      if (t.includes(frase) && t.length < bestLen) { best = b; bestLen = t.length; }
    }
    if (best) return best;
    for (const el of document.querySelectorAll("div, span, p, li")) {
      if (el.offsetParent === null) continue;
      const t = _normBtn(el.textContent);
      if (t === frase || t.replace(/[.\s…]+$/, "") === frase) return el.closest("button, a, [role=button], .btn") || el;
    }
    return null;
  };
  // Clique robusto: Angular não checa isTrusted, mas alguns handlers querem a sequência
  // pointer/mouse completa. Dispara tudo + o .click() nativo.
  function _clicarForte(el) {
    try { el.scrollIntoView({ block: "center" }); } catch (e) {}
    const o = { bubbles: true, cancelable: true, view: window };
    for (const tipo of ["pointerdown", "mousedown", "pointerup", "mouseup"]) {
      try { el.dispatchEvent(new MouseEvent(tipo, o)); } catch (e) {}
    }
    try { el.click(); } catch (e) {}   // click nativo (sem duplicar com um dispatch de "click")
  }

  // Modo passivo (dado vem do be_inject: exato, com id). A BETesporte pagina por BOTÃO
  // "CARREGAR MAIS…" (não scroll infinito) → o robô CLICA o botão até ele sumir, e vai
  // consumindo o que a API entrega a cada página. Se a aba já estava aberta antes da
  // extensão, o be_inject pode ter perdido a 1ª página → o robô força um refetch clicando
  // "FILTRAR". Para no stopId (copiar dele pra cima) ou na janela de dias.
  async function roboBetesportePassive(ctx) {
    const blocos = [], usados = new Set();
    let travado = false;

    const processar = () => {
      for (const t of beTickets) {
        const cod = (t.id != null ? String(t.id) : "").toUpperCase();
        if (!cod || usados.has(cod)) continue;
        if (ctx.stopId && cod === ctx.stopId) { travado = true; return; }   // último já extraído
        usados.add(cod);
        const dt = t.date ? Date.parse(t.date) : NaN;
        const passou = !isNaN(dt) && dt < ctx.cutoff && dt > ctx.pisoSanidade;
        blocos.push(formatTicketBE(t));
        ctx.painel.contador.textContent = blocos.length + " bilhete" + (blocos.length === 1 ? "" : "s");
        if (passou) { travado = true; return; }   // passou da janela → para
      }
    };

    // Pede ao be_inject o que ele já capturou (a 1ª página vem no load da página).
    try { window.postMessage({ __sharpenupBEReq: true }, "*"); } catch (e) {}
    await sleep(350);
    processar();

    // be_inject perdeu a 1ª página (aba aberta antes da extensão)? Força um refetch
    // clicando "FILTRAR" (recarrega a lista com o filtro atual → a API dispara de novo).
    if (!blocos.length && beTickets.length === 0) {
      const filtrar = _acharBotao("filtrar");
      if (filtrar) { try { filtrar.click(); } catch (e) {} await sleep(1500); processar(); }
    }

    // Pagina clicando "CARREGAR MAIS…". ENCERRA sozinho após 5s sem bilhete novo —
    // INDEPENDENTE do botão continuar na tela (a BETesporte o mantém no fim). Usa RELÓGIO
    // (não contagem de voltas) → robusto a variação de tempo de rede. Ao sair do while, o
    // iniciarRobo envia automaticamente (sem precisar clicar Parar).
    let voltas = 0, ultTotal = -1, ultCresceu = Date.now();
    while (!ctx.parar() && !travado && voltas < 400) {
      voltas++;
      processar();
      if (travado) break;
      const mais = _acharBotao("carregar mais");
      if (mais) { _clicarForte(mais); await sleep(1000); }
      else { try { window.scrollTo(0, document.documentElement.scrollHeight); } catch (e) {} await sleep(600); }
      processar();
      if (beTickets.length > ultTotal) { ultTotal = beTickets.length; ultCresceu = Date.now(); }
      else if (Date.now() - ultCresceu > 5000) break;   // 5s sem bilhete novo → encerra e envia
    }
    processar();
    console.log("[SharpenUp] BETesporte: " + blocos.length + " bilhete(s) · beTickets capturados=" + beTickets.length);
    return blocos;
  }

  // Modo passivo (dado vem do bn_inject: exato, com BetId). A Betano pagina por SCROLL
  // infinito (levas de 10, cursor lastId) → o robô ROLA até o fundo repetidamente p/ a
  // página buscar mais, e vai consumindo o JSON. A ROLAGEM é idêntica à que já funciona
  // hoje (gruda no fundo); só a LEITURA muda (JSON exato, não scraping). Serve às DUAS
  // abas: liquidadas (com resultado) e Em aberto (sem resultado → o backend grava 'aberta') —
  // UMA POR RODADA: exporta só a lista da aba que está na tela (ver a guarda em `processar`).
  // Para no stopId (copiar dele pra cima), na janela de dias (só liquidadas), OU — sinal
  // autoritativo — quando a LISTA ATIVA chega à página FINAL sem LastId (fimAtivo). NUNCA
  // para no 1º obstáculo: só desiste por teto após MUITOS segundos parado sem sinal de fim.
  async function roboBetanoPassive(ctx) {
    const cont = acharScroll();
    const blocos = [], usados = new Set();
    let travado = false;
    // Aba "Em aberto" (/bethistory/open): abertas são sempre recentes → a janela de dias
    // NÃO corta (senão uma liquidada velha ainda em memória interromperia antes das abertas).
    const naAbaAberta = /\/open(\b|$|\/)/i.test(location.pathname);

    const processar = () => {
      for (const t of bnById.values()) {
        // SÓ a lista da aba ATIVA. `bnById` é acumulador da SESSÃO DA PÁGINA (a Betano é SPA:
        // trocar de aba não recarrega, então o hook nunca esquece o que já viu). Sem esta
        // guarda, rodar em "Em aberto" depois de ter passado pela "Liquidada" exportava as duas
        // listas juntas (s209: 25 bilhetes = 5 abertas + 20 liquidadas em memória) — token à toa
        // e, pior, com `stopId` de bilhete LIQUIDADO o `travado` disparava ANTES das abertas e
        // elas não saíam, sem erro na tela. Uma aba por rodada; para pegar tudo, rode nas duas.
        if (!!t.__aberta !== naAbaAberta) continue;
        const cod = (t.BetId != null ? String(t.BetId) : "").toUpperCase();
        if (!cod || usados.has(cod)) continue;
        if (ctx.stopId && cod === ctx.stopId) { travado = true; return; }   // último já extraído
        usados.add(cod);
        const dt = t.PlacedAt ? Date.parse(t.PlacedAt) : NaN;
        // Janela de dias corta só LIQUIDADAS e só fora da aba Em aberto.
        const passou = !naAbaAberta && !t.__aberta && !isNaN(dt) && dt < ctx.cutoff && dt > ctx.pisoSanidade;
        blocos.push(formatTicketBN(t));
        ctx.painel.contador.textContent = blocos.length + " bilhete" + (blocos.length === 1 ? "" : "s");
        if (passou) { travado = true; return; }   // passou da janela de dias → para
      }
    };
    // Fim autoritativo da paginação = o da LISTA que está aberta na tela.
    const fimAtivo = () => (naAbaAberta ? bnFimOpen : bnFimSettled);

    // Pede ao bn_inject o que já capturou (a 1ª página vem no load da página).
    try { window.postMessage({ __sharpenupBNReq: true }, "*"); } catch (e) {}
    await sleep(300);
    processar();

    // Rola do topo p/ garantir que nada da 1ª leva foi pulado, depois gruda no fundo.
    sTo(cont, 0); await sleep(400);
    let voltas = 0, ultTotal = -1, ultCresceu = Date.now();
    while (!ctx.parar() && !travado && !fimAtivo() && voltas < 3000) {
      voltas++;
      // Gruda no fundo p/ disparar o lazy-load da próxima leva (comportamento que já funciona).
      try { window.scrollTo(0, document.documentElement.scrollHeight); } catch (e) {}
      try { if (cont && cont !== document.scrollingElement && cont !== document.documentElement) cont.scrollTop = cont.scrollHeight; } catch (e) {}
      await sleep(700);
      processar();
      if (travado) break;
      if (bnById.size > ultTotal) { ultTotal = bnById.size; ultCresceu = Date.now(); }
      else if (Date.now() - ultCresceu > 12000) break;   // 12s parado, sem fim real → desiste (nunca no 1º obstáculo)
    }
    await sleep(400);
    processar();   // consome a última leva (inclusive a página final sem LastId)
    console.log("[SharpenUp] Betano: " + blocos.length + " bilhete(s) · bnById=" + bnById.size +
                " · aba=" + (naAbaAberta ? "abertas" : "liquidadas") + " · fimOpen=" + bnFimOpen + " · fimSettled=" + bnFimSettled);
    return blocos;
  }

  // Modo passivo (dado vem do bf_inject: exato, com betId O/…). A Betfair pagina por SCROLL
  // (levas de 10, cursor nextPageIndex) → o robô ROLA até o fundo repetidamente p/ a página
  // buscar mais, e vai consumindo o JSON. Para no stopId (copiar dele pra cima), na janela de
  // dias (por settledDate), OU — sinal autoritativo — quando a página traz `moreAvailable:false`
  // (bfFimReal). NUNCA para no primeiro obstáculo: só desiste por teto após MUITOS segundos
  // totalmente parado sem sinal de fim. Espelho do roboBetanoPassive.
  async function roboBetfairPassive(ctx) {
    const cont = acharScroll();
    const blocos = [], usados = new Set();
    let travado = false;

    const processar = () => {
      for (const t of bfTickets) {
        const cod = (t.betId || "").toUpperCase();
        if (!cod || usados.has(cod)) continue;
        if (ctx.stopId && cod === ctx.stopId) { travado = true; return; }   // último já extraído
        usados.add(cod);
        // Freio da Betfair (histórico ilimitado): QUANTIDADE (padrão 100) é o principal;
        // dias é opcional (janela pela settledDate); "varrer tudo" ignora ambos.
        const dbr = _dbrBF(t.settledDate);
        let dt = NaN;
        if (dbr) { const pp = dbr.split("/"); dt = Date.UTC(+pp[2], +pp[1] - 1, +pp[0]); }
        const passouDias = ctx.bfCutoff > -Infinity && !isNaN(dt) && dt < ctx.bfCutoff;
        blocos.push(formatTicketBF(t));
        ctx.painel.contador.textContent = blocos.length + " bilhete" + (blocos.length === 1 ? "" : "s");
        if (passouDias) { travado = true; return; }                                  // passou da janela de dias
        if (ctx.qtdMax && blocos.length >= ctx.qtdMax) { travado = true; return; }   // atingiu a quantidade
      }
    };

    // Pede ao bf_inject o estado + ARRANCA a paginação ativa até o teto (o bf_inject
    // pagina sozinho pela API — não depende do scroll da página). Varrer tudo → limite 0.
    try { window.postMessage({ __sharpenupBFReq: true, limite: (ctx.varrerTudo ? 0 : (ctx.qtdMax || 0)) }, "*"); } catch (e) {}
    await sleep(300);
    processar();

    // Rola do topo p/ garantir que nada da 1ª leva foi pulado, depois gruda no fundo.
    sTo(cont, 0); await sleep(400);
    let voltas = 0, ultTotal = -1, ultCresceu = Date.now();
    while (!ctx.parar() && !travado && !bfFimReal && voltas < 3000) {
      voltas++;
      try { window.scrollTo(0, document.documentElement.scrollHeight); } catch (e) {}
      try { if (cont && cont !== document.scrollingElement && cont !== document.documentElement) cont.scrollTop = cont.scrollHeight; } catch (e) {}
      await sleep(700);
      processar();
      if (travado) break;
      // `bfPaginando` conta como sinal de vida: o inject busca as páginas pela API e pode
      // levar mais de 12s entre levas. Sem isto o robô desistia no meio da paginação e o
      // lote saía curto — a mesma queixa de "não completa o número pedido".
      if (bfTickets.length > ultTotal || bfPaginando) { ultTotal = bfTickets.length; ultCresceu = Date.now(); }
      else if (Date.now() - ultCresceu > 12000) break;   // 12s parado, sem fim real → desiste
    }
    await sleep(400);
    processar();   // consome a última leva (inclusive a página final com moreAvailable:false)

    // ABERTAS no MESMO clique (s197). Vão INTEIRAS, sem os freios de quantidade/dias das
    // encerradas: são poucas por definição, são as mais recentes e o freio existe para não
    // varrer histórico ilimitado — o que não se aplica aqui. Entram DEPOIS das encerradas
    // na ordem do lote; o backend faz UPSERT por código quando cada uma liquidar.
    let nAb = 0;
    for (const t of bfAbertas) {
      const cod = (t.betId || "").toUpperCase();
      if (!cod || usados.has(cod)) continue;
      usados.add(cod);
      blocos.push(formatTicketBF(t));
      nAb++;
      ctx.painel.contador.textContent = blocos.length + " bilhete" + (blocos.length === 1 ? "" : "s");
    }

    console.log("[SharpenUp] Betfair: " + blocos.length + " bilhete(s) · bfTickets=" + bfTickets.length +
                " · abertas=" + nAb + "/" + bfAbertas.length +
                " · hook=" + bfHookVivo + " · respostas=" + bfRespostas + " · fimReal=" + bfFimReal);
    return blocos;
  }

  // Modo passivo + REPLAY ATIVO (dado vem do pn_inject: exato, com id). A Pinnacle NÃO rola
  // uma lista infinita: cada busca /wager-filter devolve o resultado inteiro de UMA aba. Então
  // o robô não precisa rolar — ele pede ao pn_inject que RE-EMITA as duas abas (Decidido, na
  // janela de dias, + Não decidido, todas) e espera o fim (`pnFimReal`). Depois formata tudo.
  // A janela de dias corta só as ENCERRADAS antigas (as abertas não filtram por data e são
  // sempre atuais). Dedup/estado é por id → janela folgada é segura (o backend faz UPSERT).
  async function roboPinnaclePassive(ctx) {
    const blocos = [], usados = new Set();
    let travado = false;
    const N = Math.max(1, Math.round((Date.now() - ctx.cutoff) / 86400000));   // janela de dias do popup

    const processar = () => {
      for (const t of pnById.values()) {
        const cod = (t.id != null ? String(t.id) : "").toUpperCase();
        if (!cod || usados.has(cod)) continue;
        if (ctx.stopId && cod === ctx.stopId) { travado = true; return; }   // último já extraído
        usados.add(cod);
        // Janela de dias corta só ENCERRADAS (pela data do evento). Abertas nunca cortam.
        const dt = t.dataEvento ? Date.parse(t.dataEvento) : NaN;
        const passou = !t.aberta && !isNaN(dt) && dt < ctx.cutoff && dt > ctx.pisoSanidade;
        blocos.push(formatTicketPN(t));
        ctx.painel.contador.textContent = blocos.length + " bilhete" + (blocos.length === 1 ? "" : "s");
        if (passou) { travado = true; return; }   // passou da janela → para
      }
    };

    // Pede ao pn_inject o acumulado + arranca o replay das duas abas (com a janela de dias).
    try { window.postMessage({ __sharpenupPNReq: true, dias: N }, "*"); } catch (e) {}
    await sleep(400);
    processar();

    // Espera o replay terminar as duas abas (pnFimReal), consumindo o que for chegando.
    // NUNCA para no 1º obstáculo: só desiste por teto após muitos segundos parado sem fim.
    let voltas = 0, ultTotal = -1, ultCresceu = Date.now();
    while (!ctx.parar() && !travado && !pnFimReal && voltas < 600) {
      voltas++;
      await sleep(500);
      processar();
      if (travado) break;
      if (pnById.size > ultTotal) { ultTotal = pnById.size; ultCresceu = Date.now(); }
      else if (Date.now() - ultCresceu > 15000) break;   // 15s parado, sem fim real → desiste
    }
    await sleep(400);
    processar();   // consome o que chegou por último
    console.log("[SharpenUp] Pinnacle: " + blocos.length + " bilhete(s) · pnById=" + pnById.size +
                " · hook=" + pnHookVivo + " · respostas=" + pnRespostas + " · fimReal=" + pnFimReal);
    return blocos;
  }

  // ── KTO modo API (passivo puro, Kambi) ────────────────────────────────────────
  // Formata 1 cupom lido do /coupon/history.json (parseado pelo kto_inject) no bloco de texto
  // que a IA lê — com o marcador "[Código: …]" das outras casas passivas, para o backend
  // fatiar/paralelizar e pré-dedupar por ID antes de gastar IA.
  //
  // Mapeamentos VALIDADOS cruzando o JSON com o texto renderizado pela própria página:
  //   • stake/odd/line vêm em MILÉSIMOS (stake 600000 = R$600,00 · line 8500 = 8.5) — o
  //     inject já dividiu por 1000.
  //   • `betOdds` é 0 em toda PERDIDA → a odd nunca sai dele sozinho.
  //   • ODDÃO+ tem duas naturezas: ODDS_BOOST (odd sobe: 1,34 → 2,00) e PROFIT_BOOST (lucro
  //     sobe X%: 2,15 → 2,3226). Nas duas, `payout ÷ stake` devolve a odd efetiva — que é
  //     exatamente a regra global "W → Retorno ÷ Stake". Nada de decidir boost aqui.
  //   • Aberta: `potentialPayout ÷ stake` é MAIS preciso que betOdds (que a Kambi trunca em
  //     3 casas): cupom 12939510404 → 2,0435 vs 2,043. Regra da odd sem truncar.
  //
  // O que NÃO é decidido aqui: o status final. O bloco leva o status CRU da API e uma leitura
  // derivada do dinheiro (objetiva). Status novo/desconhecido nunca vira W ou L por chute —
  // a CASA_KTO.md faz o de-para.

  // sport (Kambi) → rótulo pt-BR de apoio. A localização final é da CASA_KTO/MASTER_ESPORTES;
  // o bloco leva SEMPRE o enum cru + os eventGroups (que já vêm em português) por cima.
  const _SPORT_KTO = {
    FOOTBALL: "Futebol", TENNIS: "Tênis", BASKETBALL: "Basquete", VOLLEYBALL: "Vôlei",
    DARTS: "Dardos", BOXING: "Boxe", MARTIAL_ARTS: "UFC/MMA", MMA: "UFC/MMA",
    TABLE_TENNIS: "Tênis de Mesa", BADMINTON: "Badminton", HANDBALL: "Handebol",
    ICE_HOCKEY: "Hóquei no Gelo", AMERICAN_FOOTBALL: "Futebol Americano", BASEBALL: "Beisebol",
    SNOOKER: "Sinuca", CRICKET: "Críquete", RUGBY: "Rugby", GOLF: "Golfe", CYCLING: "Ciclismo",
    ATHLETICS: "Atletismo", MOTOR_SPORTS: "F1", FORMULA_ONE: "F1", ESPORTS: "eSports",
    SPECIAL_BETS: "(mercado especial — esporte pelo jogo/liga)",
  };

  const _somaKTO = (bets, campo) => (bets || []).reduce((a, b) => a + (typeof b[campo] === "number" ? b[campo] : 0), 0);
  const _abertaKTO = (c) => (c.bets || []).some((b) => !b.status || b.status === "OPEN");
  // Odd sem truncar (só tira ruído de float), decimal com vírgula — igual às outras casas.
  const _oddTxtKTO = (x) => (x == null || !isFinite(x)) ? "" : String(Math.round(x * 1e8) / 1e8).replace(".", ",");

  // UTC (ISO da Kambi) → horário de Brasília. `_dbr` já faz a data; aqui sai data + hora,
  // porque a KTO tem cupons repetidos no mesmo dia que só a hora separa.
  function _dhKTO(iso) {
    const d = iso ? new Date(iso) : null;
    if (!d || isNaN(d)) return "";
    const p = new Intl.DateTimeFormat("pt-BR", {
      timeZone: "America/Sao_Paulo", day: "2-digit", month: "2-digit", year: "numeric",
      hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false,
    }).formatToParts(d);
    const g = (t) => (p.find((x) => x.type === t) || {}).value || "";
    return g("day") + "/" + g("month") + "/" + g("year") + " " + g("hour") + ":" + g("minute") + ":" + g("second");
  }

  // Odd DECLARADA pela casa (a exibida no card). Só existe quando o cupom tem uma entrada só.
  // NUNCA sai de `oddBase` sozinha — ela é 0 nas perdidas.
  function _oddDeclKTO(c) {
    if ((c.bets || []).length !== 1) return null;
    const b = c.bets[0];
    return b.oddBoost != null ? b.oddBoost : b.odd;
  }

  // Concilia odd × dinheiro. As duas fontes têm erro conhecido e em direções opostas:
  //   • o RETORNO é arredondado ao centavo pela casa (cupom 12886595322: odd 2,15 × R$123,29 =
  //     R$265,0735, pago R$265,07 → retorno÷stake dá 2,14997161, que não é a odd de ninguém);
  //   • a ODD DECLARADA é truncada em 3 casas pela Kambi (cupom 12886593360: boost real
  //     2,3226 vem como 2,322; o cupom aberto 12939510404 é 2,0435 e vem como 2,043).
  // Critério: se a odd declarada explica o retorno **até o centavo**, ela é a verdadeira (quem
  // arredondou foi o dinheiro). Se não explica, o dinheiro manda (é lá que o boost/cashout
  // aparece inteiro). Nunca trunca nada — só escolhe a fonte exata.
  function _conciliaKTO(retorno, stake, declarada) {
    if (declarada != null && stake > 0 && Math.abs(retorno - declarada * stake) <= 0.01) return declarada;
    return retorno / stake;
  }

  // Odd efetiva. Ordem: retorno real (W, já com boost) → retorno potencial (aberta) → odd
  // exibida (perdida/devolvida, onde a odd não move P/L). Cupom com mais de uma entrada em
  // `bets` (sistema / stake dividida) não tem odd única: devolve null e a IA lê o detalhe.
  function _oddKTO(c) {
    const st = _somaKTO(c.bets, "stake");
    const pay = _somaKTO(c.bets, "payout");
    const decl = _oddDeclKTO(c);
    if (st > 0 && pay > 0 && Math.abs(pay - st) >= 0.005) return _conciliaKTO(pay, st, decl);   // ganho (inclui boost)
    if (_abertaKTO(c) && st > 0) {
      const pot = (c.bets || []).reduce((a, b) => a + (b.potencialBoost != null ? b.potencialBoost : (b.potencial || 0)), 0);
      if (pot > 0) return _conciliaKTO(pot, st, decl);
    }
    return decl;
  }

  // Leitura derivada do DINHEIRO (objetiva, não depende de conhecer todo enum de status).
  function _resultadoKTO(c) {
    if (_abertaKTO(c)) return "em aberto (aguardando resultado — NÃO liquidar; sem resultado)";
    const st = _somaKTO(c.bets, "stake"), pay = _somaKTO(c.bets, "payout");
    if (pay === 0) return "Perdeu → L";
    if (Math.abs(pay - st) < 0.005) return "Devolvida/void (retorno = stake) → V";
    if (pay > st) return "Ganho → W (retorno R$ " + _brl(pay) + ")";
    return "Retorno parcial (R$ " + _brl(pay) + " · conferir HW/HL ou cashout)";
  }

  function _tipoKTO(c) {
    const rows = c.rows || [];
    if (c.sistema > 0) return "Sistema (" + c.sistema + " combinação(ões) · " + rows.length + " seleções)";
    if (rows.length >= 2) return "Múltipla (" + rows.length + " seleções)";
    if (rows.length === 1) {
      const r = rows[0];
      if (r.tipo === "BET_BUILDER") return "Bet Builder (mesmo jogo · " + (r.sels || []).length + " seleções)";
      return "Simples";
    }
    return "";
  }

  function formatTicketKTO(c) {
    const L = [];
    L.push("[Código: " + c.ref + "]");
    const dh = _dhKTO(c.colocada);
    if (dh) L.push("Data (colocação): " + dh);
    L.push("Stake: " + _brl(_somaKTO(c.bets, "stake")));
    L.push("Status: " + _resultadoKTO(c));
    // Status CRU da API — é ele que a CASA_KTO.md traduz. Sem isso, um enum novo (cashout,
    // recusado, meio-ganho) viraria chute a partir do dinheiro.
    const brutos = Array.from(new Set((c.bets || []).map((b) => b.status).filter(Boolean)));
    if (brutos.length) L.push("Status (API): " + brutos.join(" + "));
    const odd = _oddKTO(c);
    if (odd != null) L.push("Odd: " + _oddTxtKTO(odd));
    const tipo = _tipoKTO(c);
    if (tipo) L.push("Tipo: " + tipo);

    // ODDÃO+ — o rótulo que a KTO estampa no card. Mostra a odd base e a turbinada para a IA
    // conferir contra a CASA_KTO §6 (boost), sem precisar recalcular.
    if (c.boostTipo) {
      const b = (c.bets || [])[0] || {};
      const partes = ["ODDÃO+ (" + c.boostTipo + (c.boostPct != null ? " " + c.boostPct + "%" : "") + ")"];
      // A odd de chegada é a MESMA da linha "Odd:" (efetiva), não a `betOddsBoosted` truncada —
      // duas grandezas parecidas no mesmo bloco só confundiriam a leitura.
      if (b.oddBase && b.oddBoost) partes.push("odd base " + _oddTxtKTO(b.oddBase) + " → " + _oddTxtKTO(odd != null ? odd : b.oddBoost));
      if (c.bonus) partes.push("bônus R$ " + _brl(c.bonus));
      L.push("Boost: " + partes.join(" · "));
    }
    // Stake dividida / aposta de sistema: o card mostra as duas entradas ("R$176.97R$61.52").
    if ((c.bets || []).length > 1) {
      L.push("Entradas (" + c.bets.length + "): " + c.bets.map((b) =>
        "stake R$ " + _brl(b.stake) + " → retorno R$ " + _brl(b.payout) + " [" + (b.status || "?") + "]").join(" · "));
    }
    for (const t of (c.tags || [])) L.push("Marcação da casa: " + t);

    L.push("Seleções:");
    for (const r of (c.rows || [])) {
      const sels = r.sels || [];
      const cab = sels.length > 1 ? "  · " : "- ";     // bet builder: pernas indentadas sob o jogo
      if (sels.length > 1 && sels[0] && sels[0].jogo) {
        L.push("- " + sels[0].jogo + " (Bet Builder — mesmo jogo, " + sels.length + " seleções)");
      }
      for (const s of sels) {
        const bits = [];
        if (s.mercado) bits.push(s.mercado + ":");
        bits.push(s.label || "");
        if (s.linha != null) bits.push("(linha " + String(s.linha).replace(".", ",") + ")");
        if (s.status) bits.push("[" + s.status + (s.antecipada ? " · liquidação antecipada" : "") + "]");
        L.push(cab + bits.join(" ").trim());
        const ctx2 = [];
        if (s.jogo && sels.length === 1) ctx2.push("Jogo: " + s.jogo);
        if (s.esporte) ctx2.push("Esporte: " + s.esporte + (_SPORT_KTO[s.esporte] ? " (" + _SPORT_KTO[s.esporte] + ")" : ""));
        if (s.grupos && s.grupos.length) ctx2.push("Liga: " + s.grupos.join(" / "));
        if (s.inicio) ctx2.push("Início: " + _dhKTO(s.inicio));
        if (ctx2.length) L.push("    " + ctx2.join(" · "));
        if (s.nota) L.push("    Obs. da casa: " + s.nota);
      }
      if (r.odd != null && sels.length > 1) L.push("    Odd da seleção: " + _oddTxtKTO(r.oddBoost != null ? r.oddBoost : r.odd));
      else if (r.odd != null && (c.rows || []).length > 1) L.push("    Odd da perna: " + _oddTxtKTO(r.oddBoost != null ? r.oddBoost : r.odd));
    }
    return L.join("\n");
  }

  async function roboKTOPassive(ctx) {
    const blocos = [], usados = new Set();
    let travado = false;

    const processar = () => {
      // Ordem estável: mais recente primeiro (a lista da KTO é assim), para o corte da janela
      // de dias cair no lugar certo.
      const todos = Array.from(ktoById.values()).sort((a, b) =>
        (Date.parse(b.colocada) || 0) - (Date.parse(a.colocada) || 0));
      for (const c of todos) {
        const cod = String(c.ref || "").toUpperCase();
        if (!cod || usados.has(cod)) continue;
        if (ctx.stopId && cod === ctx.stopId) { travado = true; return; }   // último já extraído
        usados.add(cod);
        // Janela de dias corta só as RESOLVIDAS (pela data de colocação, que é a que o card
        // mostra). Aberta nunca corta — senão uma resolvida velha interromperia antes delas.
        const dt = c.colocada ? Date.parse(c.colocada) : NaN;
        const passou = !_abertaKTO(c) && !isNaN(dt) && dt < ctx.cutoff && dt > ctx.pisoSanidade;
        blocos.push(formatTicketKTO(c));
        ctx.painel.contador.textContent = blocos.length + " bilhete" + (blocos.length === 1 ? "" : "s");
        if (passou) { travado = true; return; }   // passou da janela → para
      }
    };

    // Pede ao kto_inject o acumulado + arranca o replay (repagina cada aba até `more:false`).
    try { window.postMessage({ __sharpenupKTOReq: true }, "*"); } catch (e) {}
    await sleep(400);
    processar();

    // Espera o replay terminar (ktoFimReal), consumindo o que for chegando. Não para no 1º
    // obstáculo: só desiste por teto depois de muitos segundos sem crescer.
    let voltas = 0, ultTotal = -1, ultCresceu = Date.now();
    while (!ctx.parar() && !travado && !ktoFimReal && voltas < 600) {
      voltas++;
      await sleep(500);
      processar();
      if (travado) break;
      if (ktoById.size > ultTotal) { ultTotal = ktoById.size; ultCresceu = Date.now(); }
      else if (Date.now() - ultCresceu > 15000) break;   // 15s parado, sem fim real → desiste
    }
    await sleep(400);
    processar();   // consome o que chegou por último
    console.log("[SharpenUp] KTO: " + blocos.length + " bilhete(s) · ktoById=" + ktoById.size +
                " · hook=" + ktoHookVivo + " · respostas=" + ktoRespostas + " · fimReal=" + ktoFimReal);
    return blocos;
  }

  // ── BetNacional modo API (passivo + replay por janelas de datas) ──────────────
  // Formata 1 bilhete lido do /api/v2/all-bets (agrupado por ticket_id pelo bnc_inject) no
  // bloco de texto que a IA lê — com o marcador "[Código: …]" das outras casas passivas.
  //
  // Mapeamentos VALIDADOS cruzando o JSON com o card renderizado (recon s227):
  //   • dinheiro em STRING com ponto decimal, em reais ("150.00") — o inject já converteu.
  //   • `header_return` de bilhete PENDENTE é retorno POTENCIAL (card "Retorno R$ 135,00"
  //     com o jogo por começar) → aqui vira "Retorno potencial:", nunca ganho (VaideBet).
  //   • `total_odd` vem ARREDONDADA em 3 casas (4.144; real 4.14375): no W a odd sai de
  //     retorno ÷ stake quando a declarada não explica o retorno até o centavo.
  //   • `created_at`/`event_date` JÁ vêm em horário local (sem Z) — card "01/08/2026, às
  //     15h40" = "2026-08-01 15:40:08". Converter de UTC aqui deslocaria a hora.
  //
  // O que NÃO é decidido aqui: o status final. O bloco leva o enum CRU (`bet_status_name` +
  // `header_result`) e uma leitura derivada do dinheiro (objetiva). Status novo nunca vira
  // W/L por chute — a CASA_BETNACIONAL.md faz o de-para; perna sobe `return_type_id` cru.

  const _abertaBNC = (t) => t.statusId === 0;
  // Odd sem truncar (só tira ruído de float), decimal com vírgula — igual às outras casas.
  const _oddTxtBNC = (x) => (x == null || !isFinite(x)) ? "" : String(Math.round(x * 1e8) / 1e8).replace(".", ",");

  // Datas da casa JÁ vêm locais ("2026-08-01 15:40:08" / "2026-08-01T17:30:00") →
  // reformata por regex, sem Date/fuso (converter de UTC pularia a hora).
  function _dhBNC(s) {
    const m = /^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})(?::(\d{2}))?/.exec(String(s || ""));
    if (!m) return "";
    return m[3] + "/" + m[2] + "/" + m[1] + " " + m[4] + ":" + m[5] + ":" + (m[6] || "00");
  }

  // Concilia odd × dinheiro (mesma régua da KTO). As duas fontes erram em direções opostas:
  //   • `total_odd` é arredondada em 3 casas pela casa (4.144 × R$200 = 828,80 ≠ pago 828,75);
  //   • o retorno é arredondado ao centavo (1.857 × R$300 = 557,10 exato → declarada vence).
  // Critério: a declarada vence SE explicar o retorno até o centavo; senão o dinheiro manda.
  function _conciliaBNC(retorno, stake, declarada) {
    if (declarada != null && stake > 0 && Math.abs(retorno - declarada * stake) <= 0.01) return declarada;
    return retorno / stake;
  }

  // Odd efetiva. W → retorno ÷ stake (conciliado); aberta/perdida/void → odd estrutural
  // declarada (`total_odd`) — nelas a odd não move P/L e o retorno de aberta é potencial.
  function _oddBNC(t) {
    const st = t.stake || 0, ret = t.retorno || 0;
    if (!_abertaBNC(t) && st > 0 && ret > 0 && Math.abs(ret - st) >= 0.005) return _conciliaBNC(ret, st, t.oddTotal);
    return t.oddTotal;
  }

  // Leitura derivada do DINHEIRO + `header_result` (objetiva). Enum desconhecido sobe cru.
  function _resultadoBNC(t) {
    if (_abertaBNC(t)) return "em aberto (aguardando resultado — NÃO liquidar; sem resultado)";
    if (t.statusId === 1) {
      const st = t.stake || 0, ret = t.retorno || 0;
      if (t.resultado === 1 || ret > st) return "Ganhou → W (retorno R$ " + _brl(ret) + ")";
      if (ret === 0) return "Perdeu → L";
      if (Math.abs(ret - st) < 0.005) return "Devolvida/void (retorno = stake) → V";
      return "Retorno parcial (R$ " + _brl(ret) + " · conferir HW/HL ou cashout)";
    }
    return (t.statusNome || ("status " + t.statusId)) + " (a conferir — não liquidar automaticamente)";
  }

  function _tipoBNC(t) {
    const n = (t.pernas || []).length;
    return n >= 2 ? "Múltipla (" + n + " seleções)" : "Simples";
  }

  function formatTicketBNC(t) {
    const L = [];
    L.push("[Código: " + t.codigo + "]");
    const dh = _dhBNC(t.colocada);
    if (dh) L.push("Data (colocação): " + dh);
    L.push("Stake: " + _brl(t.stake));
    L.push("Status: " + _resultadoBNC(t));
    // Status CRU da API — é ele que a CASA_BETNACIONAL.md traduz. Sem isso, um enum novo
    // (cashout, cancelada) viraria chute a partir do dinheiro.
    L.push("Status (API): " + (t.statusNome || "?") + (t.resultado != null ? " · header_result=" + t.resultado : ""));
    // ABERTA: o header_return é POTENCIAL — rotulado como tal, nunca "Retorno:" seco.
    if (_abertaBNC(t) && t.retorno > 0) L.push("Retorno potencial: R$ " + _brl(t.retorno));
    const odd = _oddBNC(t);
    if (odd != null) L.push("Odd: " + _oddTxtBNC(odd));
    L.push("Tipo: " + _tipoBNC(t));
    // Super Odds — o produto de boost da casa (mercado especial com odd turbinada). No W a
    // regra global já cobre (retorno ÷ stake); o rótulo existe p/ a IA conferir na CASA §6.
    if (t.superOdds) L.push("Boost: Super Odds (odd turbinada pela casa)");
    if (t.outright) L.push("Marcação da casa: outright (vencedor de competição)");
    if (t.pagaEm) L.push("Liquidada em: " + _dhBNC(t.pagaEm));
    L.push("Seleções:");
    for (const p of (t.pernas || [])) {
      const bits = [];
      if (p.mercado) bits.push(p.mercado + ":");
      bits.push(p.selecao || "");
      if (p.specifier) bits.push("(" + p.specifier + ")");
      // Resultado da PERNA cru (return_type_id: 1/0/2/null) — de-para na CASA_BETNACIONAL §5.
      if (p.resultadoPerna != null) bits.push("[perna (API): return_type_id=" + p.resultadoPerna + "]");
      L.push("- " + bits.join(" ").trim());
      const ctx2 = [];
      if (p.casa || p.fora) ctx2.push("Jogo: " + p.casa + " x " + p.fora);
      if (p.esporte) ctx2.push("Esporte: " + p.esporte);
      if (p.liga) ctx2.push("Liga: " + p.liga);
      if (p.inicio) ctx2.push("Início: " + _dhBNC(p.inicio));
      if (ctx2.length) L.push("    " + ctx2.join(" · "));
      if (p.odd != null && (t.pernas || []).length > 1) L.push("    Odd da perna: " + _oddTxtBNC(p.odd));
    }
    return L.join("\n");
  }

  async function roboBNCPassive(ctx) {
    const blocos = [], usados = new Set();
    let travado = false;

    const processar = () => {
      // Ordem estável: mais recente primeiro. "YYYY-MM-DD HH:MM:SS" ordena por string —
      // sem Date/fuso, pelo mesmo motivo do _dhBNC.
      const todos = Array.from(bncById.values()).sort((a, b) =>
        String(b.colocada || "").localeCompare(String(a.colocada || "")));
      for (const t of todos) {
        const cod = String(t.codigo || "").toUpperCase();
        if (!cod || usados.has(cod)) continue;
        if (ctx.stopId && cod === ctx.stopId) { travado = true; return; }   // último já extraído
        usados.add(cod);
        // Janela de dias corta só as RESOLVIDAS (pela data de colocação, a que o card
        // mostra). Aberta nunca corta — senão uma resolvida velha interromperia antes delas.
        const dt = t.colocada ? Date.parse(String(t.colocada).replace(" ", "T")) : NaN;
        const passou = !_abertaBNC(t) && !isNaN(dt) && dt < ctx.cutoff && dt > ctx.pisoSanidade;
        blocos.push(formatTicketBNC(t));
        ctx.painel.contador.textContent = blocos.length + " bilhete" + (blocos.length === 1 ? "" : "s");
        if (passou) { travado = true; return; }   // passou da janela → para
      }
    };

    // Pede ao bnc_inject o acumulado + arranca o replay (varre janelas de datas p/ trás).
    try { window.postMessage({ __sharpenupBNCReq: true }, "*"); } catch (e) {}
    await sleep(400);
    processar();

    // Espera o replay terminar (bncFimReal), consumindo o que for chegando. Não para no 1º
    // obstáculo: só desiste por teto depois de muitos segundos sem crescer.
    let voltas = 0, ultTotal = -1, ultCresceu = Date.now();
    while (!ctx.parar() && !travado && !bncFimReal && voltas < 600) {
      voltas++;
      await sleep(500);
      processar();
      if (travado) break;
      if (bncById.size > ultTotal) { ultTotal = bncById.size; ultCresceu = Date.now(); }
      else if (Date.now() - ultCresceu > 15000) break;   // 15s parado, sem fim real → desiste
    }
    await sleep(400);
    processar();   // consome o que chegou por último
    console.log("[SharpenUp] BetNacional: " + blocos.length + " bilhete(s) · bncById=" + bncById.size +
                " · hook=" + bncHookVivo + " · respostas=" + bncRespostas + " · fimReal=" + bncFimReal);
    return blocos;
  }

  // ── Tivo modo API (passivo + replay de uma chamada) ───────────────────────────
  // Formata 1 bilhete lido do `gethistory` (normalizado pelo tv_inject) no bloco de texto que a
  // IA lê. Fiel ao que a Tivo entrega — as regras de tradução vivem em `casas/CASA_TIVO.md`:
  //   • Código = `ID` do bilhete (o "# 298710215" do card) → é o marcador de chunk e de dedup.
  //   • Data = `ActionTime` (COLOCAÇÃO — a coluna "Data" do card), epoch ms UTC → Brasília.
  //   • Odd = `Koef`, precisão COMPLETA. A tela trunca em 2 casas (208.4854 vira "208.48"),
  //     então o card não serve de fonte. No W, o dinheiro confirma: Koef × stake == retorno.
  //   • Aberta: `PossibleWin` é retorno POTENCIAL, nunca "retorno"; `WinKoef` vem null e
  //     `WinAmount` vem 0 — nenhum dos dois pode virar odd.
  //   • `Result` fora de {0,2,3} sobe CRU, marcado para conferência — nunca vira W/L por chute.

  const _abertaTV = (t) => t.status === 5 || t.resultado === 0;
  // Odd sem truncar (só tira ruído de float), decimal com vírgula.
  const _oddTxtTV = (x) => (x == null || !isFinite(x)) ? "" : String(Math.round(x * 1e8) / 1e8).replace(".", ",");
  const _numTxtTV = (x) => (x == null || !isFinite(x)) ? "" : String(x).replace(".", ",");

  // epoch ms UTC → data + hora de Brasília. Sem a conversão o bilhete pula de dia: o
  // 298710215 é 17:00:06Z, que é 14:00 em Brasília — e "14:00" é o que o card mostra.
  function _dhTV(ms) {
    const d = (typeof ms === "number" && isFinite(ms)) ? new Date(ms) : null;
    if (!d || isNaN(d)) return "";
    const p = new Intl.DateTimeFormat("pt-BR", {
      timeZone: "America/Sao_Paulo", day: "2-digit", month: "2-digit", year: "numeric",
      hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false,
    }).formatToParts(d);
    const g = (t) => (p.find((x) => x.type === t) || {}).value || "";
    return g("day") + "/" + g("month") + "/" + g("year") + " " + g("hour") + ":" + g("minute") + ":" + g("second");
  }

  // Data do EVENTO mais recente entre as pernas — é ela que vai para a 1ª coluna do TSV
  // (`MASTER_OUTPUT §4`: "em apostas múltiplas: usar a data da perna mais recente"). A coluna
  // "Data" do card da Tivo mostra a COLOCAÇÃO, que é outra coisa: na amostra real, 2 dos 24
  // bilhetes caem em dia diferente (o outright de F1 é colocado 22/07 para um evento em 25/07;
  // o de tênis é colocado 17/05 para 18/05). Usar a colocação gravaria os dois no dia errado.
  function _dataEventoTV(t) {
    let max = null;
    for (const i of (t.itens || [])) {
      // A oferta (`ItemType 6`) guarda o início do jogo no `OfferedOddObject`, não em
      // `Game` — que vem null. Sem esta terceira fonte, os 4 bilhetes de odd oferecida da
      // Betfast saíam SEM data de evento nenhuma, e Data é a 1ª coluna do TSV.
      const ini = i.jogo ? i.jogo.inicio
                : (i.outright ? i.outright.inicio
                : (i.oferta ? i.oferta.inicio : null));
      if (typeof ini === "number" && isFinite(ini) && (max === null || ini > max)) max = ini;
    }
    return max;
  }

  // Odd efetiva. O `Koef` é a fonte; o dinheiro só entra se o Koef NÃO explicar o retorno até
  // o centavo (é onde um boost futuro apareceria inteiro). Nunca trunca — só escolhe a fonte.
  function _oddTV(t) {
    const st = t.stake || 0, ret = t.retorno || 0;
    if (!_abertaTV(t) && st > 0 && ret > 0 && Math.abs(ret - st) >= 0.005) {
      if (t.koef != null && Math.abs(ret - t.koef * st) <= 0.01) return t.koef;
      return ret / st;
    }
    return t.koef;
  }

  // De-para do `Result` da Tivo. Enum desconhecido NÃO vira resultado: sobe cru para conferência.
  function _resultadoTV(t) {
    if (_abertaTV(t)) return "em aberto (aguardando resultado — NÃO liquidar; sem resultado)";
    if (t.resultado !== 2 && t.resultado !== 3) {
      return "Result " + t.resultado + " (a conferir — não liquidar automaticamente)";
    }
    const st = t.stake || 0, ret = t.retorno || 0;
    const pre = t.cashout ? "Cash Out · " : "";
    if (t.resultado === 3 || ret === 0) return pre + "Perdeu → L";
    if (Math.abs(ret - st) < 0.005) return pre + "Devolvida/void (retorno = stake) → V";
    if (ret > st) return pre + "Ganho → W (retorno R$ " + _brl(ret) + ")";
    return pre + "Retorno parcial (R$ " + _brl(ret) + " · conferir HW/HL ou cashout)";
  }

  function _tipoTV(t) {
    const itens = t.itens || [];
    const n = itens.length;
    // Odd oferecida: a casa conta UMA perna (`Items.length === 1`) e o card diz "Simples",
    // mas por dentro são N seleções do MESMO evento — é bet builder. Sem este rótulo a IA
    // classificaria como aposta simples e perderia as outras seleções da descrição
    // (`MASTER_ESPORTES` / regra dos múltiplos: bet builder fica com o esporte do jogo).
    const of = itens.find((i) => i.oferta && (i.oferta.selecoes || []).length);
    if (of) return "Aposta turbinada da casa (bet builder — " + of.oferta.selecoes.length +
                   " seleções do mesmo evento)";
    if (t.sistema) return "Sistema (" + n + " seleções)";
    if (n >= 2) return "Múltipla (" + n + " seleções)";
    if (n === 1) return "Simples";
    return "";
  }

  // O nome do mercado pode vir com placeholder do motor: "{p1_r} quarto - Total de pontos" +
  // FinalPosition.p1 = 3 → "3º quarto - Total de pontos". Sem isso vaza template cru para a IA.
  // Placeholder que não soubermos preencher fica como está (não inventamos rótulo).
  function _mercadoTV(i) {
    let m = String(i.mercado || "");
    if (i.p1 != null) m = m.replace(/\{p1_r\}/g, i.p1 + "º");
    return m.replace(/\s+/g, " ").trim();
  }

  // `Result` por perna. O `1` = ANULADA/DEVOLVIDA (void), confirmado pelo DINHEIRO na conta
  // da Betfast (s211), não por dedução — a `CASA_TIVO §5` carregava esse enum como "natureza
  // não confirmada" desde a s196. Prova, no bilhete 295698756:
  //     perna 1.95 (Result 1) + perna 2.67 (Result 2) → Koef 5,2065 (as duas)
  //     mas WinKoef = 2,67 (só a que valeu) e WinAmount = 151 × 2,67 = 403,17 AO CENTAVO.
  // A casa recalculou o bilhete sem a perna void. A odd efetiva sai da régua global
  // (`retorno ÷ stake`), que o `_oddTV` já aplica quando o Koef não explica o retorno.
  const _RESULT_PERNA_TV = { 0: "pendente", 1: "anulada/devolvida", 2: "ganhou", 3: "perdeu" };

  function formatTicketTV(t) {
    const L = [];
    L.push("[Código: " + t.id + "]");
    // Esqueleto: a casa devolveu só o identificador. Sai NOMEADO em vez de virar um bloco
    // mudo ("Status: Result undefined" + "Seleções:" vazio) que a IA tentava adivinhar. O
    // marcador acima fica de propósito: é por ele que a conferência de cobertura cobra o
    // bilhete de volta e manda reprocessar, em vez de o bilhete sumir da contagem (s198).
    if (t.status == null && t.resultado == null && !(t.itens || []).length) {
      L.push("SEM DETALHE — a casa devolveu só o identificador deste bilhete.");
      L.push("NÃO extraia esta aposta: recapture. Não invente stake, odd, data nem resultado.");
      return L.join("\n");
    }
    // Primeiro a data que vale para o TSV (evento mais recente), depois a colocação — que é a
    // que o card mostra e serve de contexto/ordem, nunca de coluna Data.
    const dev = _dhTV(_dataEventoTV(t));
    if (dev) L.push("Data (evento mais recente): " + dev);
    const dh = _dhTV(t.colocada);
    if (dh) L.push("Data (colocação): " + dh);
    if (t.stake != null) L.push("Stake: R$ " + _brl(t.stake));
    L.push("Status: " + _resultadoTV(t));
    // Enum CRU da API — é ele que a CASA_TIVO.md traduz. Sem isso, um estado novo (cashout,
    // recusado, meio-ganho) viraria chute a partir do dinheiro.
    L.push("Status (API): Status=" + t.status + " · Result=" + t.resultado);
    const odd = _oddTV(t);
    if (odd != null) L.push("Odd: " + _oddTxtTV(odd));
    const tipo = _tipoTV(t);
    if (tipo) L.push("Tipo: " + tipo);
    if (_abertaTV(t) && t.potencial != null) L.push("Retorno potencial: R$ " + _brl(t.potencial));
    if (t.bonus) L.push("Marcação da casa: aposta com bônus (IsBonus)");
    if (t.cashout) L.push("Marcação da casa: cashout (CashOut) — conferir valor no card");

    // Sinal para a IA classificar Múltipla × Bet Builder pelo MASTER_ESPORTES, sem que o
    // rótulo "Tipo" (que é o da casa) minta.
    const itens = t.itens || [];
    if (itens.length >= 2) {
      const jogos = new Set(itens.map((i) => i.jogo ? (i.jogo.casa + "|" + i.jogo.fora) : ("outright:" + i.id)));
      if (jogos.size === 1) L.push("Mesmo jogo: as " + itens.length + " seleções são do mesmo evento");
    }

    L.push("Seleções:");
    for (const i of itens) {
      // ── Odd oferecida (`ItemType 6`): bet builder promocional da casa ──────────
      // A perna vem com Game/Market/Position/Sport todos null; tudo que a IA precisa está
      // no OfferedOddObject. Sem este ramo o bloco saía "- [perdeu]" e nada mais — 4 dos
      // 50 bilhetes da Betfast (8%), e a IA teria de inventar esporte e descrição.
      // Os rótulos vêm em INGLÊS porque o `language: 33` do pedido não alcança este objeto;
      // avisamos explicitamente para a IA não tratá-los como mercado desconhecido.
      if (i.oferta) {
        const o = i.oferta;
        const cab = ["Aposta turbinada da casa (odd oferecida)"];
        if (o.jogo) cab.push("— " + o.jogo);
        L.push("- " + cab.join(" ") + " [" + (_RESULT_PERNA_TV[i.resultado] || ("Result " + i.resultado + " — a conferir")) + "]");
        L.push("    ⚠ Rótulos desta oferta vêm em inglês (a casa não traduz este bloco).");
        const ctxO = [];
        if (o.esporte) ctxO.push("Esporte: " + o.esporte);
        const ligaO = [o.regiao, o.campeonato].filter(Boolean).join(" / ");
        if (ligaO) ctxO.push("Liga: " + ligaO);
        if (o.inicio) ctxO.push("Início: " + _dhTV(o.inicio));
        if (ctxO.length) L.push("    " + ctxO.join(" · "));
        for (const s of (o.selecoes || [])) {
          const p = [];
          if (s.mercado) p.push(s.mercado + ":");
          p.push(s.selecao || "");
          if (s.odd != null) p.push("@ " + _oddTxtTV(s.odd));
          L.push("    • " + p.join(" ").replace(/\s+/g, " ").trim());
        }
        // A odd do bilhete é o `Koef` (já emitido acima). O produto das sub-seleções NÃO
        // bate com ele (6,4237 contra 9,51): a oferta tem preço negociado pela casa, e os
        // campos internos `RealPrice`/`CalcPrice` divergem entre si. Não emitimos nenhum
        // deles para não dar à IA uma segunda odd concorrente.
        continue;
      }
      const bits = [];
      if (i.outright) {
        // Outright: `Game` é null e o Market.Name é lixo interno do motor.
        if (i.outright.nome) bits.push(i.outright.nome + ":");
        bits.push(i.outright.selecao || i.selecao || "");
      } else {
        const m = _mercadoTV(i);
        if (m) bits.push(m + ":");
        bits.push(i.selecao || "");
        if (i.linha != null) bits.push("(linha " + _numTxtTV(i.linha) + ")");
      }
      const rp = _RESULT_PERNA_TV[i.resultado];
      bits.push("[" + (rp || ("Result " + i.resultado + " — a conferir")) + "]");
      L.push("- " + bits.join(" ").replace(/\s+/g, " ").trim());

      const ctx2 = [];
      if (i.jogo && (i.jogo.casa || i.jogo.fora)) ctx2.push("Jogo: " + i.jogo.casa + " - " + i.jogo.fora);
      if (i.esporte) ctx2.push("Esporte: " + i.esporte);
      const liga = [i.regiao, i.campeonato].filter(Boolean).join(" / ");
      if (liga) ctx2.push("Liga: " + liga);
      const ini = i.jogo ? i.jogo.inicio : (i.outright ? i.outright.inicio : null);
      if (ini) ctx2.push("Início: " + _dhTV(ini));
      if (ctx2.length) L.push("    " + ctx2.join(" · "));
      // Placar do jogo. NÃO emitimos Team1Score/Team2Score: eles são a estatística do mercado
      // (escanteios, cartões), e sairiam no bloco parecendo placar.
      if (i.placar) L.push("    Placar: " + i.placar);
      if (i.odd != null && itens.length > 1) L.push("    Odd da perna: " + _oddTxtTV(i.odd));
    }
    return L.join("\n");
  }

  async function roboTVPassive(ctx) {
    const blocos = [], usados = new Set();
    let travado = false;

    const processar = () => {
      // Mais recente primeiro (é a ordem do card), para o corte da janela cair no lugar certo.
      const todos = Array.from(tvById.values()).sort((a, b) => (b.colocada || 0) - (a.colocada || 0));
      for (const t of todos) {
        const cod = String(t.id || "").toUpperCase();
        if (!cod || usados.has(cod)) continue;
        if (ctx.stopId && cod === ctx.stopId) { travado = true; return; }   // último já extraído
        usados.add(cod);
        // A janela de dias corta só as RESOLVIDAS (pela colocação, que é a data do card).
        // Aberta nunca corta — senão uma resolvida velha interromperia antes delas.
        const dt = t.colocada;
        const passou = !_abertaTV(t) && typeof dt === "number" && dt < ctx.cutoff && dt > ctx.pisoSanidade;
        blocos.push(formatTicketTV(t));
        ctx.painel.contador.textContent = blocos.length + " bilhete" + (blocos.length === 1 ? "" : "s");
        if (passou) { travado = true; return; }
      }
    };

    // Pede o acumulado + arranca o replay. NÃO mandamos `dias`: o filtro `from`/`to` é do
    // servidor e cortaria também as ABERTAS antigas (aposta colocada há 60 dias com jogo
    // amanhã). Como a conta inteira vem numa chamada só, é mais barato e mais seguro trazer
    // tudo e deixar a janela para o corte acima, que sabe preservar aberta.
    // Vai para o topo E para os iframes: o inject que interessa está no frame do sportsbook v4
    // (mesma origem), e postMessage do topo não desce sozinho para os filhos.
    const pedir = () => {
      const msg = { __sharpenupTVReq: true };
      try { window.postMessage(msg, "*"); } catch (e) {}
      for (let i = 0; i < window.frames.length && i < 24; i++) {
        try { window.frames[i].postMessage(msg, "*"); } catch (e) {}
      }
    };
    pedir();
    await sleep(400);
    processar();

    // Espera o fim autoritativo, consumindo o que chegar. Não para no 1º obstáculo: só desiste
    // por teto depois de muitos segundos sem crescer.
    let voltas = 0, ultTotal = -1, ultCresceu = Date.now();
    while (!ctx.parar() && !travado && !tvFimReal && voltas < 600) {
      voltas++;
      await sleep(500);
      processar();
      if (travado) break;
      if (tvById.size > ultTotal) { ultTotal = tvById.size; ultCresceu = Date.now(); }
      else if (Date.now() - ultCresceu > 15000) break;
    }
    await sleep(400);
    processar();
    // A consulta tem teto e a lista da casa não tem "mostrar mais": `len == Count` significa
    // "encheu", não "acabou". O inject varre para trás por `to` e resolve sozinho — o toast
    // aqui é só para os dois desfechos que o operador precisa saber.
    // Nada é dito quando houve outro freio (janela de dias / stopId): aí o corte é nosso.
    if (tvTetoSuspeito && !travado) {
      if (tvAlemDoTeto) {
        toastLocal("A lista da casa para no teto, mas a captura foi além dele pela API: " +
                   tvById.size + " bilhetes no total — mais do que a tela mostra.", true);
      } else if (!tvTetoResolvido) {
        // A varredura não concluiu (rede caiu, teto de janelas). Não afirmar cobertura.
        toastLocal("Atenção: a casa devolveu " + tvById.size + " bilhetes, no limite da consulta, " +
                   "e não deu para conferir se há histórico mais antigo. Rode de novo antes de " +
                   "considerar o período fechado.", false);
      }
    }
    console.log("[SharpenUp] Tivo/Betfast: " + blocos.length + " bilhete(s) · tvById=" + tvById.size +
                " · hook=" + tvHookVivo + " · respostas=" + tvRespostas + " · fimReal=" + tvFimReal +
                " · teto=" + tvTetoSuspeito + " · resolvido=" + tvTetoResolvido + " · alemDoTeto=" + tvAlemDoTeto);
    return blocos;
  }

  // ── VaideBet (Altenar/BIA) ────────────────────────────────────────────────────
  // Formata 1 bilhete lido de `/WidgetReports/widgetExpandedBetHistory` (parseado pelo
  // vb_inject) no bloco de texto que a IA lê. Fiel ao que o card renderiza:
  //   • Código = `id` (o "ID:" do rodapé do card) — chave de dedup e do `[Código:]`.
  //   • Data do TSV = `eventDate` mais recente (UTC→Brasília). A colocação (`createdDate`)
  //     vai junto, como contexto: nas abertas do reconhecimento os dois campos caem em DIAS
  //     diferentes (colocada 26/07 para jogo em 27/07), e usar a colocação gravaria errado.
  //   • Odd = `totalOdds`, JÁ boostada (o riscado do card é `preBoostedPrice`, truncado na
  //     tela). No W vale a regra global (retorno ÷ stake); as duas concordam nesta casa.
  //   • ABERTA (`status:0`): `totalWin` é retorno POTENCIAL e vem preenchido — lê-lo como
  //     realizado transformaria toda aposta em aberto em vitória fantasma.
  //   • `status` fora de {0,1,2} sobe CRU, marcado para conferência — nunca vira W/L.

  const _abertaVB = (b) => b && b.status === 0;
  const _oddTxtVB = (x) => (x == null || !isFinite(x)) ? "" : String(Math.round(x * 1e8) / 1e8).replace(".", ",");

  // O payload não traz o NOME do esporte, só o id. Mapa ancorado no que foi confirmado
  // contra a tela; id fora do mapa sobe cru (a IA/CASA_VAIDEBET.md finaliza pelo evento).
  //
  // ⚠️ O rótulo TEM de ser o valor oficial do `MASTER_ESPORTES_2026` — a IA copia o que
  // está escrito aqui. No 1º lote real eu tinha escrito "Beisebol" (sinônimo, não o valor
  // oficial) e o banco saiu com as duas grafias: 3 linhas "Beisebol" + 1 "Baseball", que o
  // sistema conta como esportes DIFERENTES. O oficial é `Baseball` (`MASTER_ESPORTES §Baseball`,
  // onde BEISEBOL aparece como sinônimo de entrada, nunca como saída).
  const _ESPORTE_VB = { 1: "Futebol", 13: "Baseball" };
  const _RESULT_PERNA_VB = { 0: "pendente", 1: "ganhou", 2: "perdeu" };

  // ISO UTC ("2026-07-26T17:34:39.79Z") → epoch ms. Data inválida vira null (nunca 0, que
  // viraria 01/01/1970 no bloco).
  function _msVB(iso) {
    if (!iso) return null;
    const t = Date.parse(String(iso));
    return isFinite(t) ? t : null;
  }

  // epoch ms UTC → data + hora de Brasília. Sem converter, o bilhete pula de dia: o
  // 5232943733 é 01:55Z do dia 26, que é 22:55 do dia 25 em Brasília — e é isso que o card mostra.
  function _dhVB(ms) {
    const d = (typeof ms === "number" && isFinite(ms)) ? new Date(ms) : null;
    if (!d || isNaN(d)) return "";
    const p = new Intl.DateTimeFormat("pt-BR", {
      timeZone: "America/Sao_Paulo", day: "2-digit", month: "2-digit", year: "numeric",
      hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false,
    }).formatToParts(d);
    const g = (t) => (p.find((x) => x.type === t) || {}).value || "";
    return g("day") + "/" + g("month") + "/" + g("year") + " " + g("hour") + ":" + g("minute") + ":" + g("second");
  }

  // Data do EVENTO mais recente entre as seleções (`MASTER_OUTPUT §4`).
  function _dataEventoVB(b) {
    let max = null;
    for (const s of (b.selections || [])) {
      const t = _msVB(s && s.eventDate);
      if (t != null && (max === null || t > max)) max = t;
    }
    return max;
  }

  // Odd efetiva. `totalOdds` é a fonte (já contém o boost); o dinheiro só entra se a odd
  // declarada NÃO explicar o retorno até o centavo. Nunca trunca — só escolhe a fonte.
  function _oddVB(b) {
    const dec = (typeof b.totalOdds === "number" && isFinite(b.totalOdds)) ? b.totalOdds : null;
    if (_abertaVB(b)) return dec;
    const st = b.totalStake || 0, ret = b.totalWin || 0;
    if (b.status === 1 && st > 0 && ret > 0) {
      if (dec != null && Math.abs(ret - dec * st) <= 0.01) return dec;
      return ret / st;
    }
    return dec;
  }

  function _resultadoVB(b) {
    if (_abertaVB(b)) return "em aberto (aguardando resultado — NÃO liquidar; sem resultado)";
    if (b.status !== 1 && b.status !== 2) {
      return "status " + b.status + " (a conferir — não liquidar automaticamente)";
    }
    const st = b.totalStake || 0, ret = b.totalWin || 0;
    // Cashout: a conta do reconhecimento não tinha nenhum, então o campo nunca foi visto
    // preenchido. Se vier, o desfecho é marcado e o valor sai na linha própria — quem aplica
    // a regra (cashout = stake → V · ≠ stake → W com odd = cashout ÷ stake) é a IA com o MASTER.
    const pre = (b.cashOutValue > 0 || b.partialCashOut > 0) ? "Cash Out · " : "";
    if (b.status === 2) return pre + "Perdeu → L";
    if (ret === 0) return pre + "status 1 (ganha) com retorno ZERO — a conferir, não liquidar automaticamente";
    if (Math.abs(ret - st) < 0.005) return pre + "Devolvida/void (retorno = stake) → V";
    if (ret > st) return pre + "Ganho → W";
    return pre + "Retorno parcial (R$ " + _brl(ret) + " · conferir HW/HL ou cashout)";
  }

  function _tipoVB(b) {
    const sels = b.selections || [];
    if (sels.length >= 2) return "Múltipla (" + sels.length + " seleções)";
    const s = sels[0];
    if (s && s.isBetBuilder) {
      const n = (s.bbOdds || []).length;
      return "Bet Builder (mesmo jogo · " + (n || 1) + " seleções)";
    }
    return sels.length === 1 ? "Simples" : "";
  }

  function _esporteVB(b) {
    const s = (b.selections || [])[0];
    const id = s ? s.sportTypeId : null;
    if (id == null) return "";
    const nome = _ESPORTE_VB[id];
    return nome ? nome + " (sportTypeId " + id + ")"
                : "sportTypeId " + id + " (a conferir — id não mapeado na CASA_VAIDEBET)";
  }

  function formatTicketVB(b) {
    const L = [];
    L.push("[Código: " + b.id + "]");

    const dev = _dhVB(_dataEventoVB(b));
    if (dev) L.push("Data (evento mais recente): " + dev);
    const dco = _dhVB(_msVB(b.createdDate));
    if (dco) L.push("Data (colocação): " + dco);

    if (b.totalStake != null) L.push("Stake: R$ " + _brl(b.totalStake));
    L.push("Status: " + _resultadoVB(b));
    // Enum CRU da casa — é ele que a CASA_VAIDEBET.md traduz. Sem isso, um estado novo
    // (cashout, anulado, meio-ganho) viraria chute a partir do dinheiro.
    L.push("Status (API): status=" + b.status);

    const odd = _oddVB(b);
    if (odd != null) L.push("Odd: " + _oddTxtVB(odd));
    const tipo = _tipoVB(b);
    if (tipo) L.push("Tipo: " + tipo);
    const esp = _esporteVB(b);
    if (esp) L.push("Esporte: " + esp);

    // Dinheiro: o de uma ABERTA é POTENCIAL e sai com esse rótulo, nunca como "Retorno".
    if (_abertaVB(b)) {
      const pot = (b.remainingTotalWin != null) ? b.remainingTotalWin : b.totalWin;
      if (pot != null) L.push("Retorno potencial: R$ " + _brl(pot));
    } else if (b.totalWin) {
      L.push("Retorno: R$ " + _brl(b.totalWin));
    }
    if (b.cashOutValue > 0) L.push("Cash Out: R$ " + _brl(b.cashOutValue) + " — aplicar a regra de cashout (não é o retorno normal)");
    if (b.partialCashOut > 0) L.push("Cash Out parcial: R$ " + _brl(b.partialCashOut));
    if (b.bonus) L.push("Marcação da casa: aposta com bônus (R$ " + _brl(b.bonus) + ")");

    // Boost: o card mostra "2.33 » 3.00" (o riscado é a odd ANTES do boost, truncada na
    // tela). Sai como marcação para a IA não confundir com a odd válida, que é a de cima.
    const s0 = (b.selections || [])[0];
    const pre = s0 && s0.boostedSelection ? s0.boostedSelection.preBoostedPrice : null;
    if (pre != null && odd != null && Math.abs(pre - odd) > 0.0001) {
      L.push("Marcação da casa: odd turbinada — odd antes do boost " + _oddTxtVB(pre) + " · valendo " + _oddTxtVB(odd));
    }

    const sels = b.selections || [];
    if (sels.length >= 2) {
      const jogos = new Set(sels.map((s) => String(s.eventName || s.eventId || "")));
      if (jogos.size === 1) L.push("Mesmo jogo: as " + sels.length + " seleções são do mesmo evento");
    }

    L.push("Seleções:");
    for (const s of sels) {
      const pernas = (s.bbOdds || []);
      if (pernas.length) {
        // Bet builder: `name` já traz as pernas concatenadas por " | ", mas só `bbOdds` tem o
        // status de cada uma. Emitimos perna a perna (o separador canônico do projeto é " // ",
        // e é a IA que monta a descrição — aqui a lista fica explícita, uma por linha).
        for (const p of pernas) {
          const rp = _RESULT_PERNA_VB[p.status];
          L.push("- " + [p.marketName ? p.marketName + ":" : "", p.oddName || "",
                         "[" + (rp || ("status " + p.status + " — a conferir")) + "]"]
                        .join(" ").replace(/\s+/g, " ").trim());
        }
      } else {
        const rp = _RESULT_PERNA_VB[s.status];
        L.push("- " + [s.marketName ? s.marketName + ":" : "", s.name || "",
                       "[" + (rp || ("status " + s.status + " — a conferir")) + "]"]
                      .join(" ").replace(/\s+/g, " ").trim());
      }
      const ctx2 = [];
      if (s.eventName) ctx2.push("Jogo: " + s.eventName);
      const ini = _dhVB(_msVB(s.eventDate));
      if (ini) ctx2.push("Início: " + ini);
      if (s.isLive) ctx2.push("Ao vivo");
      if (ctx2.length) L.push("    " + ctx2.join(" · "));
      if (s.eventScore) L.push("    Placar: " + s.eventScore);
      if (s.price != null && sels.length > 1) L.push("    Odd da seleção: " + _oddTxtVB(s.price));
    }
    return L.join("\n");
  }

  async function roboVBPassive(ctx) {
    const blocos = [], usados = new Set();
    let travado = false;

    const processar = () => {
      // Mais recente primeiro (é a ordem do card), para o corte da janela cair no lugar certo.
      const todos = Array.from(vbById.values())
        .sort((a, b) => (_msVB(b.createdDate) || 0) - (_msVB(a.createdDate) || 0));
      for (const b of todos) {
        const cod = String(b.id || "").toUpperCase();
        if (!cod || usados.has(cod)) continue;
        if (ctx.stopId && cod === ctx.stopId) { travado = true; return; }   // último já extraído
        usados.add(cod);
        // A janela de dias corta só as RESOLVIDAS (pela colocação, que é o que o card mostra).
        // Aberta nunca corta — senão uma resolvida velha interromperia antes delas.
        const dt = _msVB(b.createdDate);
        const passou = !_abertaVB(b) && typeof dt === "number" && dt < ctx.cutoff && dt > ctx.pisoSanidade;
        blocos.push(formatTicketVB(b));
        ctx.painel.contador.textContent = blocos.length + " bilhete" + (blocos.length === 1 ? "" : "s");
        if (passou) { travado = true; return; }
      }
    };

    // Pede o acumulado + arranca o replay das duas abas. `dias` vai junto: é ele que vira o
    // `dateFrom` das RESOLVIDAS no servidor (as abertas o inject busca com janela larga de
    // propósito — aposta antiga com jogo amanhã não pode ser cortada pelo filtro).
    const dias = Math.max(1, Math.round((Date.now() - ctx.cutoff) / 86400000));
    const pedir = () => {
      const msg = { __sharpenupVBReq: true, dias: dias };
      try { window.postMessage(msg, "*"); } catch (e) {}
      for (let i = 0; i < window.frames.length && i < 24; i++) {
        try { window.frames[i].postMessage(msg, "*"); } catch (e) {}
      }
    };
    pedir();
    await sleep(400);
    processar();

    // Espera o fim autoritativo (`isLastPage` nas duas abas), consumindo o que chegar. Não
    // para no 1º obstáculo: só desiste por teto depois de muitos segundos sem crescer.
    let voltas = 0, ultTotal = -1, ultCresceu = Date.now();
    while (!ctx.parar() && !travado && !vbFimReal && voltas < 600) {
      voltas++;
      await sleep(500);
      processar();
      if (travado) break;
      if (vbById.size > ultTotal) { ultTotal = vbById.size; ultCresceu = Date.now(); }
      else if (Date.now() - ultCresceu > 15000) break;
    }
    await sleep(400);
    processar();
    console.log("[SharpenUp] VaideBet: " + blocos.length + " bilhete(s) · vbById=" + vbById.size +
                " · hook=" + vbHookVivo + " · respostas=" + vbRespostas + " · fimReal=" + vbFimReal);
    return blocos;
  }

  // ── Bet365 modo API (passivo + detalhe por rota) ──────────────────────────────
  // Formata 1 bilhete lido do /sportshistoryapi (parseado pelo b3_inject) no bloco de texto que a
  // IA lê (marcador "[Código: BR…]" das outras casas passivas → o backend split/dedupa por ele).
  // Fiel à CASA_BET365 + docs/PLANO_BET365_CAPTURA_API.md:
  //   • Código = BR (comprovante; ESTÁVEL aberta→resolvida). Sem detalhe (BR não veio) → vazio.
  //   • Data = ENCERRAMENTO: maior kickoff das pernas + folga do esporte, convertido UK→Brasília.
  //   • Resultado: RT do summary vs stake → W/L/V (cashout ≠ retorno cheio → W). Aberta = sem.
  //   • Odd fracionária ("21/20") → decimal com precisão completa (21/20 = 2,05).
  //   • Múltiplo (3+ jogos diferentes) → sinaliza o tipo p/ a IA classificar (MASTER_ESPORTES).

  // CL → esporte (âncora; a IA/CASA_BET365 finaliza a localização). eSoccer vem com CL=1 → o
  // handle "(gamer)" entre parênteses é o sinal (a IA trata). CL=15=Dardos (liga DARTS-MODUS,
  // "Vencedor da Partida") e CL=91=Vôlei (liga VB-*, "Handicap (Pontos)") — mapeados dos payloads
  // reais da conta marloncezar01 (s180/s188). CL=10=F1/Automobilismo (liga MOTORRACING, "GP …
  // · Treino/Carro Vencedor" — F1 é esporte oficial no MASTER_ESPORTES). CL=151 ainda desconhecido.
  const _CL_B3 = { "1": "Futebol", "10": "F1", "13": "Tênis", "15": "Dardos", "18": "Basquete", "91": "Vôlei", "94": "Badminton" };
  // Folga kickoff→liquidação por esporte (horas) — só p/ acertar o DIA perto da meia-noite.
  const _OFF_B3 = { "1": 2.5, "10": 2.5, "13": 3, "15": 1.5, "18": 2.5, "91": 2, "94": 1.5 };

  // Odd Bet365: fracionária "num/den" → decimal (num/den + 1), precisão completa, vírgula.
  const _oddB3 = (frac) => {
    const s = String(frac || ""); const i = s.indexOf("/");
    if (i < 0) return "";
    const a = parseFloat(s.slice(0, i)), b = parseFloat(s.slice(i + 1));
    if (!isFinite(a) || !isFinite(b) || b === 0) return "";
    return String(a / b + 1).replace(".", ",");
  };
  const _numB3 = (s) => parseFloat(String(s == null ? "" : s).replace(",", ".")) || 0;

  // Reino Unido (Europe/London) → Brasília (UTC-3, sem horário de verão). BST (fim mar→fim out) =
  // UTC+1 → BR = UK-4; GMT = UTC+0 → BR = UK-3. Retorna a DATA de Brasília (já com a folga).
  function _ehBST(y, mo, d) {
    if (mo < 3 || mo > 10) return false;
    if (mo > 3 && mo < 10) return true;
    const ultimoDom = (yy, mm) => { const x = new Date(Date.UTC(yy, mm, 0)); return x.getUTCDate() - x.getUTCDay(); };
    return mo === 3 ? d >= ultimoDom(y, 3) : d < ultimoDom(y, 10);
  }
  function _dataFimB3(kickoffTS, offsetH) {
    const m = /^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})/.exec(String(kickoffTS || ""));
    if (!m) return "";
    const y = +m[1], mo = +m[2], d = +m[3], h = +m[4], mi = +m[5];
    // Bet builder de mesmo jogo vem com TP=00010101000000 (sem kickoff). Sem esta guarda o
    // bilhete ganhava "Data (encerramento): 01/01/0001" — data falsa é pior que data ausente.
    if (y < 2000) return "";
    const uk = Date.UTC(y, mo - 1, d, h, mi);                       // hora de parede UK como pseudo-UTC
    const ukToBr = _ehBST(y, mo, d) ? 4 : 3;
    const br = new Date(uk - (ukToBr - offsetH) * 3600000);
    const p = (n) => String(n).padStart(2, "0");
    return p(br.getUTCDate()) + "/" + p(br.getUTCMonth() + 1) + "/" + br.getUTCFullYear();
  }

  // Resultado bruto p/ a IA (RT do summary vs stake). Cashout ≠ retorno cheio → W (regra do MASTER).
  function _resultadoB3(t) {
    if (t.aberta || t.rt == null) return "em aberto (aguardando resultado — NÃO liquidar; sem resultado)";
    const st = _numB3(t.ts != null ? t.ts : t.stake), rt = _numB3(t.rt);
    if (rt === 0) return "Perdeu → L";
    if (Math.abs(rt - st) < 0.005) return "Devolvida/void (retorno = stake) → V";
    if (rt > st) return "Ganho → W (retorno R$ " + rt.toFixed(2).replace(".", ",") + ")";
    return "Ganho/perda parcial (retorno R$ " + rt.toFixed(2).replace(".", ",") + " · a conferir HW/HL)";
  }

  function formatTicketB3(t) {
    const L = [];
    L.push("[Código: " + (t.code || "") + "]");
    const legs = (t.legs && t.legs.length) ? t.legs : [];
    // Sem detalhe (o "Detalhes da Aposta" ainda não foi aberto) o esporte e a contagem de
    // jogos saem do summary — antes vinham só das pernas e o bilhete ficava sem esporte.
    const base = legs.length ? legs : (t.sels || []);
    const cls = Array.from(new Set(base.map((l) => l.cl).filter(Boolean)));
    const jogos = new Set(base.map((l) => l.jogo || l.na).filter(Boolean));
    const multiplo = jogos.size >= 3 || cls.length > 1;
    // data de encerramento = maior kickoff+folga entre as pernas
    let dataFim = "", maxMs = -Infinity;
    for (const l of legs) {
      const off = _OFF_B3[l.cl] != null ? _OFF_B3[l.cl] : 2.5;
      const dd = _dataFimB3(l.kickoff, off);
      if (dd) { const p = dd.split("/"); const ms = Date.UTC(+p[2], +p[1] - 1, +p[0]); if (ms > maxMs) { maxMs = ms; dataFim = dd; } }
    }
    if (dataFim) L.push("Data (encerramento): " + dataFim);
    L.push("Stake: " + _brl(_numB3(t.ts != null ? t.ts : t.stake)));
    L.push("Status: " + _resultadoB3(t));
    if (!multiplo && t.oddFrac) L.push("Odd: " + _oddB3(t.oddFrac));
    if (multiplo) L.push("Tipo: Múltipla (" + legs.length + " seleções)");
    else if (cls.length) L.push("Esporte (casa): CL=" + cls[0] + (_CL_B3[cls[0]] ? " (" + _CL_B3[cls[0]] + ")" : ""));

    L.push("Seleções:");
    // BET BUILDER (mesmo jogo): a perna traz `subs` — o cabeçalho é o JOGO e cada sub é uma
    // seleção com seu mercado. Sem isto o bilhete saía com 1 linha só (bug da s178).
    // O separador entre seleções continua sendo ' // ' no texto final (regra #19); aqui as
    // linhas são cruas, para a IA montar a descrição.
    if (legs.length) {
      for (const l of legs) {
        if (l.subs && l.subs.length) {
          const jogo = l.jogo || l.sel;
          // A perna de bet builder vem com OD=0/1 (odd 1,00): a odd é do BILHETE, já impressa
          // acima. Imprimir "@ 1" aqui daria à IA uma odd falsa por seleção.
          const od = _oddB3(l.oddFrac);
          L.push("  • " + jogo + (od && od !== "1" ? " @ " + od : "") + (l.liga ? " · " + l.liga : ""));
          for (const s of l.subs) L.push("      – " + [s.mercado, s.na].filter(Boolean).join(" · "));
        } else {
          const partes = [l.jogo, l.mercado, l.sel].filter(Boolean).join(" · ");
          L.push("  • " + partes + (l.oddFrac ? " @ " + _oddB3(l.oddFrac) : "") + (l.liga ? " · " + l.liga : ""));
        }
      }
    } else if (t.sels && t.sels.length) {
      for (const s of t.sels) {                                  // só summary (detalhe não veio)
        L.push("  • " + s.na + (s.od ? " @ " + _oddB3(s.od) : ""));
        if (s.subs && s.subs.length) {
          for (const sb of s.subs) L.push("      – " + [sb.mercado, sb.na].filter(Boolean).join(" · "));
        }
      }
    }
    return L.join("\n");
  }

  // Modo passivo + DRIVER DE UI. O `b3_inject` (que roda DENTRO do iframe de membros, onde a
  // lista existe) escuta as respostas que a página baixa e, a pedido, abre "Detalhes da Aposta"
  // de cada bilhete — é o clique que faz a página pedir o `/confirmation`, de onde vêm o código
  // BR, jogo, mercado, liga e kickoff. Não dá para chamar a API direto: o token
  // `x-net-sync-term` é exigido e rotaciona por requisição (provado ao vivo na s178).
  // O robô aqui só coordena: pede, acompanha o contador e formata o estado final.
  // JANELA: use "Últimas 24/48 horas" na tela. Ao voltar de um detalhe a lista reinicia no topo
  // e perde as páginas carregadas, então lista curta = captura rápida; lista longa = o driver
  // para no fim da 1ª página e avisa (melhor que rolar n² vezes).
  async function roboBet365Passive(ctx) {
    let travado = false;
    const N = Math.max(1, Math.round((Date.now() - ctx.cutoff) / 86400000));

    // Memória de rodadas passadas ({ bsid: {code,da,legs} }) — carregada ANTES de tudo porque o
    // "acabou?" e o painel dependem dela (ver `pronto`).
    const lembrados = await b3Lembrados();
    // "pronto" = já tem código NESTA rodada OU está na memória (será re-hidratado no fim, não
    // precisa ser re-buscado). Sem tratar a memória como pronta, o driver detalhava só os NOVOS
    // e o laço ficava girando em vazio achando que faltavam os já-conhecidos → TRAVA em lote
    // grande com memória cheia (114 vistos, só 2 novos detalhados, painel preso em "114").
    const pronto = (t) => !!(t.code || lembrados[String(t.bsid)]);

    const contar = () => {
      let n = 0, c = 0;
      for (const t of b3ById.values()) {
        if (ctx.stopId && t.code && String(t.code).toUpperCase() === ctx.stopId) { travado = true; break; }
        n++;
        if (pronto(t)) c++;
      }
      // Fase 1 (recolhendo a lista): só o total sobe. Fase 2 (detalhando): o total fica parado e
      // sobe o "prontos" — mostrar os dois mata o "parece que travou" no lote grande.
      ctx.painel.contador.textContent = (c < n)
        ? c + " de " + n + " prontos"
        : n + " bilhete" + (n === 1 ? "" : "s");
    };
    // Progresso p/ o timeout de inatividade: vistos + com código. Enquanto o driver abre os
    // detalhes a QUANTIDADE não cresce (só o conteúdo) — medir só o tamanho mataria o robô no
    // meio da varredura.
    const progresso = () => {
      let n = 0;
      for (const t of b3ById.values()) if (t.code) n++;
      return b3ById.size + n;
    };

    b3Pedir(N);                                   // 1º: recolhe o que o inject já viu
    await sleep(600);
    contar();
    b3Pedir(N, "detalhar", Object.keys(lembrados)); // 2º: manda abrir os detalhes que faltam

    // Sobra = bilhete visto que ainda NÃO está pronto (sem código E fora da memória). Um `fim` de
    // UMA passada NÃO encerra enquanto sobrar: em lista grande (período) os bilhetes chegam em
    // LOTES e a 1ª passada fecha só o que estava na mão; o resto precisa de mais passadas. 24h/48h
    // fecham tudo na 1ª → sobra 0 → encerra na hora. **Memória cheia → os já-conhecidos contam
    // como prontos → sobra 0 deles → não trava mais** (era o bug: contava-os como pendentes).
    const semCodigo = () => { let n = 0; for (const t of b3ById.values()) if (!pronto(t)) n++; return n; };
    let voltas = 0, ultProg = -1, ultCresceu = Date.now(), ultMsg = b3MsgTick;
    while (!ctx.parar() && !travado && voltas < 6000) {
      voltas++;
      await sleep(500);
      const resta = semCodigo();
      if (b3FimReal && resta === 0) break;                 // fim de verdade: nada mais sem código
      // Enquanto sobrar sem código, re-pede "detalhar" e REABRE a janela de `fim` (a próxima
      // passada precisa poder anunciar o seu próprio fim). Pega os bilhetes que chegaram depois.
      if (resta > 0 && voltas % 12 === 0) { b3FimReal = false; b3Pedir(N, "detalhar", Object.keys(lembrados)); }
      contar();
      if (travado) break;
      // Progresso = bilhetes/códigos crescendo OU qualquer sinal do inject (o driver manda um
      // ping a cada "Mostrar Mais"/detalhe → não morre durante a expansão, quando a contagem
      // não cresce mas o trabalho continua).
      const p = progresso();
      if (p > ultProg || b3MsgTick > ultMsg) { ultProg = p; ultMsg = b3MsgTick; ultCresceu = Date.now(); }
      else if (Date.now() - ultCresceu > 45000) break;   // 45s realmente parado → desiste
    }
    await sleep(400);

    // Re-hidrata o que o driver pulou: o detalhe não voltou nesta rodada, mas está guardado.
    // Sem isto o bilhete pulado sairia sem código e sem mercado/liga.
    for (const t of b3ById.values()) {
      if (t.code) continue;
      const m = lembrados[String(t.bsid)];
      if (m) { t.code = m.code; t.da = m.da; t.legs = m.legs; }
    }

    // Memória: só bilhete RESOLVIDO com código entra. Aberto fica de fora de propósito — se
    // resolver por cashout, o bloco "Encerrar Aposta" só aparece no confirmation depois, e
    // pular o detalhe dele na próxima rodada perderia a data exata do encerramento.
    const paraLembrar = {};
    let novos = 0;
    for (const t of b3ById.values()) {
      if (!t.code || t.aberta !== false) continue;
      if (lembrados[String(t.bsid)]) continue;
      paraLembrar[String(t.bsid)] = { code: t.code, da: t.da, legs: t.legs || [] };
      novos++;
    }
    if (novos) await b3Lembrar(paraLembrar);

    // Monta os blocos do ESTADO FINAL (os detalhes que chegaram por último já entraram).
    const blocos = [];
    for (const t of b3ById.values()) {
      if (ctx.stopId && t.code && String(t.code).toUpperCase() === ctx.stopId) break;   // até o já-exportado
      blocos.push(formatTicketB3(t));
    }
    let comCodigo = 0;
    for (const t of b3ById.values()) if (t.code) comCodigo++;
    console.log("[SharpenUp] Bet365 API: " + blocos.length + " bilhete(s) · com código=" + comCodigo +
                "/" + b3ById.size + " · hook=" + b3HookVivo + " · frames=" + b3PorFrame.size +
                " · respostas=" + b3Soma("respostas") + " · fimReal=" + b3FimReal +
                " · driver=" + (b3Driver ? JSON.stringify(b3Driver) : "não rodou"));
    if (comCodigo < b3ById.size) {
      console.log("[SharpenUp] Bet365: " + (b3ById.size - comCodigo) + " bilhete(s) SEM código BR — " +
                  "provável lista longa demais (ao voltar de um detalhe ela reinicia no topo). " +
                  "Use 'Últimas 24 horas' ou 'Últimas 48 horas' e rode de novo.");
    }
    for (const [href, f] of b3PorFrame) {
      console.log("[SharpenUp] Bet365 frame " + (f.topo ? "TOPO" : "iframe") +
                  " · respostas=" + f.respostas + " · history=" + f.history + " · " + href.slice(0, 120));
    }
    return blocos;
  }

  // Estratégia Superbet (fallback): cada card da lista (.bet-list-item__container) tem
  // o CÓDIGO no atributo `id` (exato, sem OCR). Simples já vêm inteiros; múltiplas
  // colapsam as pernas ("+N mais seleções") → o robô CLICA pra carregar o detalhe
  // completo e lê o texto mais rico (card expandido, selecionado ou painel da
  // direita — auto-descoberto). Para no stopId (copiar dele pra cima) ou na janela.
  async function roboSuperbet(ctx) {
    const cont = document.querySelector(".sb-my-bets__items") || acharScroll();
    const vistos = new Set(), blocos = [];
    let travado = false;
    const atualiza = () => ctx.painel.contador.textContent = blocos.length + " bilhete" + (blocos.length === 1 ? "" : "s");

    const proximoCard = () =>
      [...document.querySelectorAll(".bet-list-item__container")]
        .find((c) => c.id && !vistos.has(c.id.trim().toUpperCase()));

    const processarVisiveis = async () => {
      // Re-consulta o DOM a cada card: clicar/rolar troca a lista virtualizada.
      while (!ctx.parar() && !travado) {
        const card = proximoCard();
        if (!card) return;
        const codigo = card.id.trim().toUpperCase();
        if (ctx.stopId && codigo === ctx.stopId) { travado = true; return; }   // chegou no último já extraído
        vistos.add(codigo);

        // Data da janela: do cabeçalho do card (a Superbet ordena por ela).
        const baseText = card.innerText || "";
        const passou = parseDatas(baseText.toLowerCase())
          .some((ts) => ts < ctx.cutoff && ts > ctx.pisoSanidade);

        // SEMPRE clica p/ ler o DETALHE da direita — só ele traz TODAS as pernas, a
        // data por seleção, ODDS TOTAIS, STATUS/SACADO e o freebet. A lista da esquerda
        // é resumo (colapsa múltiplas e não tem data por perna). Fallback = card.
        let texto = baseText;
        try {
          (card.querySelector(".bet-list-item") || card).click();
          const rico = await esperarDetalhe(codigo);
          if (rico && rico.length > texto.length) texto = rico;
        } catch (_) {}

        texto = texto.trim();
        if (texto.length >= 10) { blocos.push("[Código: " + codigo + "]\n" + texto); atualiza(); }
        if (passou) { travado = true; return; }   // passou da janela de dias → para
      }
    };

    sTo(cont, 0); await sleep(500);
    // A Superbet carrega mais bilhetes (lazy-load) ao chegar no fim. NÃO paramos no
    // primeiro "fundo": ao encostar, grudamos no fim p/ disparar o loader e esperamos;
    // só desistimos após várias esperas SEM novidade (nem card novo, nem a página
    // crescer). Isso resolve o "pegou 10, depois 18" — a lista ainda estava crescendo.
    let voltas = 0, semNovidade = 0, ultTotal = 0, ultMax = -1;
    while (!ctx.parar() && !travado && voltas < 2000) {
      voltas++;
      await processarVisiveis();
      if (travado) break;
      const top = sTop(cont), max = sMax(cont);
      const cresceu = blocos.length > ultTotal || max > ultMax + 4;
      ultTotal = blocos.length; ultMax = max;
      if (top >= max - 4) {                 // no fundo atual → espera o lazy-load
        sTo(cont, max);                     // gruda no fim p/ disparar o carregamento
        if (cresceu) semNovidade = 0;
        else if (++semNovidade >= 4) { await processarVisiveis(); break; }
        await sleep(650);
      } else {
        semNovidade = 0;
        sTo(cont, top + sClient(cont) * 0.85);
        await sleep(420);
      }
    }
    return blocos;
  }

  // Após clicar um bilhete, espera o painel de DETALHE carregar e devolve seu texto.
  // O detalhe é a MENOR div que contém, juntos: o código + "ODDS TOTAIS" + um marcador
  // de resultado (STATUS/PRÊMIO/SACADO/Ganhou/Perdido/Reembolso) — isso isola o painel
  // da direita (com todas as pernas E a data por seleção), sem pegar a página toda.
  // Também considera o card selecionado como candidato. Rejeita "+N mais seleções" e
  // devolve o texto mais rico (o que tem as datas por perna costuma ser o maior).
  // Rodapé do painel = código + ODDS TOTAIS + resultado (financeiro).
  const _MARC = /(status|pr[êe]mio|sacado|ganhou|perdido|reembols|devolvid)/i;
  // Pernas/seleções (só no painel de detalhe, não no rodapé): data por seleção (dia
  // da semana) OU nome de mercado. É o sinal p/ saber que subimos até incluir as pernas.
  const _PERNA = /(seg|ter|qua|qui|sex|s[áa]b|dom)[a-z]*\.?\s*\d{1,2}|total de|menos de|mais de|resultado final|handicap|jogador\b|1[ºo]? tempo|2[ºo]? tempo|ambas|escanteios|cart[õo]es|impedimento|finaliza|chutes|gols|faltas|desarme/i;
  function limparPainel(txt) {
    return txt.split("\n").filter((l) => {
      const s = l.trim();
      if (!s) return false;
      if (/interaja com a comunidade|inspire outros jogadores|entrar no supersocial/i.test(s)) return false;
      if (/^mozilla\/5\.0/i.test(s)) return false;
      if (/^[a-f0-9]{8}-[a-f0-9]{4}-/i.test(s)) return false;   // hash tipo uuid
      if (/^[a-f0-9]{24,}$/i.test(s)) return false;             // hash longo
      return true;
    }).join("\n").trim();
  }
  async function esperarDetalhe(codigo) {
    for (let i = 0; i < 14; i++) {
      await sleep(150);
      // Rodapé: MENOR div com código + ODDS TOTAIS + resultado (isola o painel certo).
      const foot = [...document.querySelectorAll("div")].filter((d) => {
        const t = d.textContent || "";
        return t.includes(codigo) && /odds totais/i.test(t) && _MARC.test(t);
      }).sort((a, b) => (a.textContent || "").length - (b.textContent || "").length)[0];
      if (!foot) continue;
      // Sobe do rodapé até o container que TAMBÉM tem as pernas (o painel completo).
      let el = foot, alvo = foot;
      for (let k = 0; k < 10 && el.parentElement; k++) {
        el = el.parentElement;
        if (_PERNA.test(el.textContent || "")) { alvo = el; break; }
      }
      const txt = limparPainel(alvo.innerText || "");
      if (txt && !/mais sele/i.test(txt) && txt.includes(codigo)) return txt;
    }
    return null;
  }

  function criarPainelRobo() {
    const p = document.createElement("div");
    S(p, { position: "fixed", bottom: "24px", left: "50%", transform: "translateX(-50%)",
      "z-index": "2147483647", display: "inline-flex", "align-items": "center", gap: "12px",
      background: "#0E1524", border: "1px solid rgba(46,139,255,0.5)", "border-radius": "12px",
      padding: "10px 12px 10px 14px", color: "#E6ECF5", font: "13px/1 system-ui,sans-serif",
      "box-shadow": "0 12px 40px rgba(0,0,0,.55)", "user-select": "none" });
    p.innerHTML = bladeSVG(9, 20) +
      '<span style="margin-left:2px">Coletando bilhetes… <b id="su-robo-n" style="font-family:ui-monospace,monospace;color:#7FB2FF">0 bilhetes</b></span>';
    const btn = document.createElement("button");
    btn.textContent = "Parar";
    S(btn, { background: "transparent", color: "#9AA6B6", border: "1px solid rgba(255,255,255,.12)",
      "border-radius": "7px", padding: "6px 12px", cursor: "pointer", font: "inherit", "font-weight": "600" });
    p.appendChild(btn);
    document.documentElement.appendChild(p);
    return { remove: () => p.remove(), contador: p.querySelector("#su-robo-n"), btnParar: btn };
  }

  function toastLocal(texto, ok) {
    const t = document.createElement("div");
    t.textContent = texto;
    S(t, { position: "fixed", bottom: "24px", left: "50%", transform: "translateX(-50%)",
      "z-index": "2147483647", font: "13px/1.4 system-ui,sans-serif", color: "#fff",
      background: ok ? "#1B7F4E" : "#B3363B", padding: "10px 16px", "border-radius": "10px",
      "box-shadow": "0 8px 24px rgba(0,0,0,.35)" });
    document.documentElement.appendChild(t);
    setTimeout(() => t.remove(), 2600);
  }

  // ── Orquestração ────────────────────────────────────────────────────────────
  async function sync() {
    let st; try { st = await get(); } catch (_) { return; }
    if (!st.token) { removeFab(); removeFrame(); removeDraw(); return; }
    if (st.modo === "texto") { removeFrame(); removeDraw(); ensureFab("texto"); return; }
    // modo print
    if (st.frameAtivo) {
      removeFab();
      if (st.frameRect) { removeDraw(); ensureFrame(st.frameRect, st.frameCount || 0); }
      else { removeFrame(); ensureDraw(); }
    } else { removeFrame(); removeDraw(); ensureFab("print"); }
  }

  chrome.storage.onChanged.addListener((ch, area) => {
    if (area !== "local") return;
    if ("frameCount" in ch && frame && !("frameAtivo" in ch) && !("frameRect" in ch)) { atualizarContador(ch.frameCount.newValue); return; }
    if ("token" in ch || "modo" in ch || "frameAtivo" in ch || "frameRect" in ch) sync();
  });
  chrome.runtime.onMessage.addListener((msg) => {
    if (!msg) return;
    if (msg.type === "CAPTURA_FIM") fimCaptura(!!msg.ok);
    else if (msg.type === "START_ROBOT") iniciarRobo();
  });

  sync();
})();
