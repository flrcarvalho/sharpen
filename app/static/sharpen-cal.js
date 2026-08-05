// ── SharpenCal — calendário da marca ─────────────────────────────────────────
// Popover de seleção de dia desenhado com os tokens do design system, no lugar
// do popup nativo do Chrome (que não aceita estilo nenhum — fica branco no app
// dark). Um único popover por página, reutilizado por todos os campos de data:
// modais de edição, edição inline da Minha Base e inputs type=date (nestes, o
// indicador nativo some via CSS e o botão da página chama o SharpenCal).
//
// API:
//   SharpenCal.abrir(anchor, valor, onPick, opts)
//     anchor — elemento que ancora o popover (input ou botão)
//     valor  — 'DD/MM/AAAA' ou 'AAAA-MM-DD' (vazio = sem seleção, abre no mês atual)
//     onPick — recebe a data escolhida no formato de opts.saida ('' no Limpar)
//     opts   — { saida: 'br' (default) | 'iso' }
//   SharpenCal.fechar() · SharpenCal.aberto()
//
// Datas sempre em fuso LOCAL (nunca toISOString/UTC — "Hoje" virava amanhã).
(function () {
  const MESES = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
    'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'];
  const SEMANA = ['D', 'S', 'T', 'Q', 'Q', 'S', 'S'];
  let pop = null, cb = null, saida = 'br', viewY = 0, viewM = 0, sel = null;

  const CSS = `
.shcal{position:fixed;z-index:10000;display:none;width:252px;background:var(--surface-2);border:1px solid var(--line);border-radius:var(--r-md);box-shadow:0 12px 32px rgba(0,0,0,.45);padding:10px;font-family:var(--font-sans)}
.shcal__hdr{display:flex;align-items:center;gap:2px;padding:2px 2px 8px}
.shcal__mes{flex:1;font-size:13px;font-weight:700;color:var(--ink)}
.shcal__nav{width:24px;height:24px;display:flex;align-items:center;justify-content:center;background:transparent;border:0;border-radius:var(--r-sm);color:var(--ink-soft);cursor:pointer;font-size:11px;padding:0}
.shcal__nav:hover{background:rgba(var(--accent-rgb),.14);color:var(--ink)}
.shcal__sem{display:grid;grid-template-columns:repeat(7,1fr);margin-bottom:2px}
.shcal__sem span{font-family:var(--font-mono);font-size:9.5px;letter-spacing:.08em;color:var(--ink-soft);text-align:center;padding:3px 0}
.shcal__grid{display:grid;grid-template-columns:repeat(7,1fr);gap:2px}
.shcal__dia{height:28px;display:flex;align-items:center;justify-content:center;background:transparent;border:1px solid transparent;border-radius:var(--r-sm);font-family:var(--font-mono);font-size:12px;color:var(--ink);cursor:pointer;padding:0}
.shcal__dia:hover{background:rgba(var(--accent-rgb),.14)}
.shcal__dia.fora{color:var(--ink-mute)}
.shcal__dia.hoje{border-color:var(--accent)}
.shcal__dia.sel{background:var(--accent);color:#fff}
.shcal__foot{display:flex;justify-content:space-between;padding:8px 2px 0}
.shcal__act{background:transparent;border:0;padding:2px 6px;font-family:var(--font-sans);font-size:11px;font-weight:600;color:var(--accent-2);cursor:pointer;border-radius:var(--r-sm)}
.shcal__act:hover{background:rgba(var(--accent-rgb),.14)}`;

  function parse(s) {
    let m = (s || '').trim().match(/^(\d{2})\/(\d{2})\/(\d{4})$/);
    if (m) return { y: +m[3], mo: +m[2] - 1, d: +m[1] };
    m = (s || '').trim().match(/^(\d{4})-(\d{2})-(\d{2})/);
    if (m) return { y: +m[1], mo: +m[2] - 1, d: +m[3] };
    return null;
  }
  const p2 = n => String(n).padStart(2, '0');
  const fmt = (y, mo, d) => saida === 'iso' ? `${y}-${p2(mo + 1)}-${p2(d)}` : `${p2(d)}/${p2(mo + 1)}/${y}`;

  function garantir() {
    if (pop) return;
    const st = document.createElement('style');
    st.id = 'shcal-css';
    st.textContent = CSS;
    document.head.appendChild(st);
    pop = document.createElement('div');
    pop.className = 'shcal';
    // mousedown não pode roubar o foco do campo em edição: o blur do editor
    // inline salvaria ANTES do clique no dia chegar ao calendário.
    pop.addEventListener('mousedown', e => e.preventDefault());
    document.body.appendChild(pop);
    document.addEventListener('mousedown', e => {
      if (aberto() && !pop.contains(e.target)) fechar();
    }, true);
    document.addEventListener('keydown', e => {
      // captura: com o calendário aberto, Esc fecha SÓ ele (o modal por trás fica)
      if (e.key === 'Escape' && aberto()) { e.stopPropagation(); e.preventDefault(); fechar(); }
    }, true);
    window.addEventListener('resize', fechar);
  }

  function render() {
    const hoje = new Date();
    const hy = hoje.getFullYear(), hm = hoje.getMonth(), hd = hoje.getDate();
    const prim = new Date(viewY, viewM, 1);
    const ini = new Date(viewY, viewM, 1 - prim.getDay());   // volta ao domingo
    let dias = '';
    for (let i = 0; i < 42; i++) {
      const dt = new Date(ini.getFullYear(), ini.getMonth(), ini.getDate() + i);
      const y = dt.getFullYear(), mo = dt.getMonth(), d = dt.getDate();
      const cls = ['shcal__dia'];
      if (mo !== viewM) cls.push('fora');
      if (y === hy && mo === hm && d === hd) cls.push('hoje');
      if (sel && y === sel.y && mo === sel.mo && d === sel.d) cls.push('sel');
      dias += `<button type="button" class="${cls.join(' ')}" data-ymd="${y}-${p2(mo + 1)}-${p2(d)}">${d}</button>`;
    }
    const nome = MESES[viewM];
    pop.innerHTML =
      `<div class="shcal__hdr">` +
        `<span class="shcal__mes">${nome.charAt(0).toUpperCase() + nome.slice(1)} de ${viewY}</span>` +
        `<button type="button" class="shcal__nav" data-nav="-1" aria-label="Mês anterior">&#9664;</button>` +
        `<button type="button" class="shcal__nav" data-nav="1" aria-label="Próximo mês">&#9654;</button>` +
      `</div>` +
      `<div class="shcal__sem">${SEMANA.map(s => `<span>${s}</span>`).join('')}</div>` +
      `<div class="shcal__grid">${dias}</div>` +
      `<div class="shcal__foot">` +
        `<button type="button" class="shcal__act" data-act="limpar">Limpar</button>` +
        `<button type="button" class="shcal__act" data-act="hoje">Hoje</button>` +
      `</div>`;
    pop.querySelectorAll('[data-nav]').forEach(b => b.addEventListener('click', () => {
      viewM += +b.dataset.nav;
      if (viewM < 0) { viewM = 11; viewY--; } else if (viewM > 11) { viewM = 0; viewY++; }
      render();
    }));
    pop.querySelectorAll('[data-ymd]').forEach(b => b.addEventListener('click', () => {
      const [y, mo, d] = b.dataset.ymd.split('-').map(Number);
      entregar(fmt(y, mo - 1, d));
    }));
    pop.querySelector('[data-act="hoje"]').addEventListener('click', () => entregar(fmt(hy, hm, hd)));
    pop.querySelector('[data-act="limpar"]').addEventListener('click', () => entregar(''));
  }

  function entregar(v) { const f = cb; fechar(); if (f) f(v); }

  function abrir(anchor, valor, onPick, opts) {
    garantir();
    cb = onPick || null;
    saida = (opts && opts.saida) === 'iso' ? 'iso' : 'br';
    sel = parse(valor);
    if (sel) { viewY = sel.y; viewM = sel.mo; }
    else { const h = new Date(); viewY = h.getFullYear(); viewM = h.getMonth(); }
    render();
    pop.style.display = 'block';
    const r = anchor.getBoundingClientRect();
    const pw = pop.offsetWidth, ph = pop.offsetHeight;
    const x = Math.min(Math.max(8, r.left), window.innerWidth - pw - 8);
    let y = r.bottom + 6;
    if (y + ph > window.innerHeight - 8) y = Math.max(8, r.top - ph - 6);
    pop.style.left = x + 'px';
    pop.style.top = y + 'px';
  }

  function fechar() { if (pop) pop.style.display = 'none'; cb = null; }
  function aberto() { return !!pop && pop.style.display !== 'none'; }

  window.SharpenCal = { abrir, fechar, aberto };
})();
