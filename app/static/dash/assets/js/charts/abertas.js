// ── abertas.js — "Em Aberto": exposição viva das apostas não liquidadas ───────
//
// Tela irmã da "Minha Base" (charts/apostas.js). A base é DADOS_ABERTAS — as linhas
// que `aplicarFeed` separa por resultado==='ABERTA' e que NENHUMA métrica do
// dashboard soma (não há P/L: nada resolveu ainda).
//
// Três decisões que valem repetir, porque são o que diferencia esta tela:
//
// 1) SEM FILTRO DE PERÍODO. Aposta em aberto aponta para o FUTURO. Um filtro de
//    data "últimos 30 dias" esconderia justamente o jogo de amanhã — o oposto do
//    que a tela existe para mostrar. Só filtram esporte/casa/tipster/operador
//    (buildFiltersSemData). `filtrarAbertas` lê df/dt de gfs('abertas'), que
//    permanece vazio porque a tela nunca escreve lá.
//
// 2) NADA DE VERDE/VERMELHO. Sem resultado não há lucro nem prejuízo: pintar de
//    verde um "retorno potencial" seria prometer o que não aconteceu. Exposição =
//    âmbar (--warn, o mesmo "pendente" do Início); projeção = azul (--accent-2).
//
// 3) A DATA É A DO EVENTO. Todo agrupamento temporal aqui responde "para quando
//    é a aposta", não "quando ela foi feita" — é o que o calendário mede.

// Mês exibido no calendário (AAAA-MM). Vive fora da função p/ sobreviver ao
// re-render que o filtro dispara; a nav ‹ › só anda em meses que TÊM aposta aberta.
let _abrtMes = null;

// ── Helpers de data (sempre fuso local — nunca toISOString; ver filters.js) ──
function _abrtHojeISO() { return _ymd(new Date()); }
function _abrtISOmais(dias) { const d = new Date(); d.setDate(d.getDate() + dias); return _ymd(d); }
function _abrtBR(iso) { const p = (iso || '').slice(0, 10).split('-'); return p.length === 3 ? `${p[2]}/${p[1]}/${p[0]}` : (iso || ''); }
// Distância em dias entre duas datas ISO, imune a horário de verão (meio-dia como âncora).
function _abrtDias(deISO, ateISO) {
  const a = new Date(deISO + 'T12:00:00'), b = new Date(ateISO + 'T12:00:00');
  return Math.round((b - a) / 86400000);
}
// Rótulo relativo do evento: "hoje", "amanhã", "em 3 dias", "atrasada 2d".
// `atrasada` = o evento já passou e a aposta continua sem resultado — sinal de
// captura pendente na casa, não de erro do dado.
function _abrtQuando(iso) {
  const d = _abrtDias(_abrtHojeISO(), iso);
  if (d === 0) return { txt: 'hoje', cls: 'hoje' };
  if (d === 1) return { txt: 'amanhã', cls: '' };
  if (d > 1) return { txt: 'em ' + d + ' dias', cls: '' };
  return { txt: 'atrasada ' + (-d) + 'd', cls: 'atrasada' };
}

// Retorno potencial de UMA aposta = stake × odd (retorno bruto, stake incluída —
// é o valor que cai na conta se ela ganhar). Odd ausente/zerada (a casa ainda não
// publicou) não vira 1: devolve 0 e a linha fica fora do total, contada à parte.
function _abrtRetorno(r) {
  const odd = Number(r.odd) || 0, stake = Number(r.stake) || 0;
  return odd > 0 ? stake * odd : 0;
}

// Agregado {stake, n, retorno} por chave (casa, tipster, esporte, dia…).
function _abrtAgrupar(rows, chave) {
  const m = {};
  rows.forEach(r => {
    const k = (typeof chave === 'function' ? chave(r) : r[chave]) || '';
    const d = m[k] || (m[k] = { stake: 0, n: 0, retorno: 0 });
    d.stake += Number(r.stake) || 0;
    d.n++;
    d.retorno += _abrtRetorno(r);
  });
  return m;
}

// ── Render principal ────────────────────────────────────────────────────────
function renderAbertas() {
  const rows = filtrarAbertas('abertas');
  _abrtKPIs(rows);
  _abrtCalendario(rows);
  _abrtBarras('abertasCasas', rows, 'casa', true);
  _abrtBarras('abertasTipsters', rows, r => r.tipster || 'sem tipster', false);
  _abrtLista(rows);
}

// ── 1) KPIs ────────────────────────────────────────────────────────────────
// Valor em Aberto / Apostas / Odd Média / Retorno Potencial. Todo R$ agregado sai
// por fmtR (inteiro, UI_REFERENCE §5.1); nada aqui recebe cor de sinal.
function _abrtKPIs(rows) {
  const host = document.getElementById('abertasKPI');
  if (!host) return;
  const stake = rows.reduce((a, r) => a + (Number(r.stake) || 0), 0);
  const comOdd = rows.filter(r => Number(r.odd) > 0);
  const semOdd = rows.length - comOdd.length;
  const retorno = rows.reduce((a, r) => a + _abrtRetorno(r), 0);
  // Odd média PONDERADA pela stake — mesma definição de calcAvgOdd (app.js), aqui
  // aplicada só às abertas com odd publicada.
  const stakeComOdd = comOdd.reduce((a, r) => a + (Number(r.stake) || 0), 0);
  const oddMedia = stakeComOdd > 0 ? comOdd.reduce((a, r) => a + r.odd * r.stake, 0) / stakeComOdd : 0;
  const lucroPot = retorno > 0 ? retorno - stakeComOdd : 0;
  const casas = new Set(rows.map(r => r.casa).filter(Boolean)).size;
  const contas = new Set(rows.map(r => (r.casa || '') + '||' + (r.parceiro || '')).filter(k => k !== '||')).size;

  const mk = (label, val, sub) =>
    `<div class="kpi">` +
      `<div class="kpi-label"><span class="kpi-pipe"></span> ${label}</div>` +
      `<div class="kpi-val neu">${val}</div>` +
      `<div class="kpi-sub">${sub || ''}</div>` +
    `</div>`;

  host.innerHTML = `<div class="kpi-grid" style="margin-bottom:1.25rem">` +
    mk('Valor em Aberto', fmtR(stake),
       casas ? `em ${casas} ${casas === 1 ? 'casa' : 'casas'} · ${contas} ${contas === 1 ? 'conta' : 'contas'}` : 'nenhuma exposição') +
    mk('Apostas', rows.length.toLocaleString('pt-BR'),
       rows.length ? 'aguardando liquidação' : 'nada em aberto') +
    mk('Odd Média', oddMedia > 0 ? fmtOdd(oddMedia) : '—',
       semOdd ? `ponderada · ${semOdd} sem odd` : 'ponderada pela stake') +
    mk('Retorno Potencial', fmtR(retorno),
       retorno > 0 ? `lucro de ${fmtR(lucroPot)} se todas ganharem` : 'sem odd publicada') +
  `</div>`;
}

// ── 2) Calendário: para quando são as apostas ──────────────────────────────
// Grade mensal (segunda→domingo) com a exposição de cada dia. O heat é a fração
// da stake do dia sobre o maior dia do mês — âmbar, nunca verde/vermelho.
// Acima da grade, o horizonte em 5 faixas: é o que responde "quanto é pra quarta,
// quanto pro sábado" sem precisar ler célula por célula.
function _abrtCalendario(rows) {
  const host = document.getElementById('abertasCal');
  if (!host) return;
  if (!rows.length) { host.innerHTML = mkEmpty('Nenhuma aposta em aberto no filtro'); return; }

  const hoje = _abrtHojeISO();
  const amanha = _abrtISOmais(1), sem = _abrtISOmais(7);
  const faixas = [
    ['Atrasadas', rows.filter(r => r.data < hoje), 'evento já passou'],
    ['Hoje', rows.filter(r => r.data === hoje), _abrtBR(hoje)],
    ['Amanhã', rows.filter(r => r.data === amanha), _abrtBR(amanha)],
    ['Próximos 7 dias', rows.filter(r => r.data > amanha && r.data <= sem), 'até ' + _abrtBR(sem)],
    ['Depois', rows.filter(r => r.data > sem), 'mais de uma semana'],
  ];
  const horizonte = `<div class="abrt-horiz">` + faixas.map(([lbl, rs, sub]) => {
    const st = rs.reduce((a, r) => a + (Number(r.stake) || 0), 0);
    return `<div class="abrt-horiz__c ${rs.length ? 'on' : 'vazia'}">` +
      `<div class="abrt-horiz__k">${lbl}</div>` +
      `<div class="abrt-horiz__v">${fmtR(st)}</div>` +
      `<div class="abrt-horiz__s">${rs.length ? rs.length + (rs.length === 1 ? ' aposta · ' : ' apostas · ') + sub : '—'}</div>` +
    `</div>`;
  }).join('') + `</div>`;

  // Meses COM aposta aberta, em ordem cronológica. A nav só anda dentro deles —
  // não faz sentido paginar por um mês vazio.
  const meses = [...new Set(rows.map(r => r.data.slice(0, 7)))].sort();
  const mesHoje = hoje.slice(0, 7);
  if (!_abrtMes || meses.indexOf(_abrtMes) === -1) {
    _abrtMes = meses.indexOf(mesHoje) >= 0 ? mesHoje : (meses.find(m => m >= mesHoje) || meses[meses.length - 1]);
  }
  const idx = meses.indexOf(_abrtMes);
  const [yr, mo] = _abrtMes.split('-');
  const dia = _abrtAgrupar(rows.filter(r => r.data.slice(0, 7) === _abrtMes), r => r.data.slice(0, 10));
  const maxStake = Math.max(1, ...Object.values(dia).map(d => d.stake));

  const primeiro = new Date(parseInt(yr), parseInt(mo) - 1, 1);
  const nDias = new Date(parseInt(yr), parseInt(mo), 0).getDate();
  const offset = (primeiro.getDay() + 6) % 7;   // 0 = segunda … 6 = domingo

  // Monta célula a célula e SÓ DEPOIS corta as semanas mortas (ver abaixo).
  const cels = [];
  for (let i = 0; i < offset; i++) cels.push({ vazia: true, html: `<div class="abrt-cal__cell offset"></div>` });
  for (let d = 1; d <= nDias; d++) {
    const key = `${yr}-${mo}-${String(d).padStart(2, '0')}`;
    const dd = dia[key];
    const col = (offset + d - 1) % 7;
    let cls = 'abrt-cal__cell';
    if (col >= 5) cls += ' we';
    if (key === hoje) cls += ' hoje';
    if (key < hoje) cls += ' passado';
    if (!dd) {
      cels.push({ vazia: key !== hoje, html:
        `<div class="${cls} vazio"><div class="top"><span class="dn">${d}</span>` +
        `${key === hoje ? '<span class="marca">hoje</span>' : ''}</div></div>` });
      continue;
    }
    const t = Math.min(dd.stake / maxStake, 1);
    const bg = `background:rgba(var(--warn-rgb),${(0.08 + t * 0.34).toFixed(3)})`;
    cels.push({ vazia: false, html:
      `<div class="${cls}" style="${bg}" title="${_abrtBR(key)} — ${dd.n} ${dd.n === 1 ? 'aposta' : 'apostas'}">` +
      `<div class="top"><span class="dn">${d}</span>` +
      `${key === hoje ? '<span class="marca">hoje</span>' : `<span class="qtd">${dd.n}×</span>`}</div>` +
      `<div class="val">${fmtR(dd.stake)}</div>` +
    `</div>` });
  }
  // Poda as SEMANAS totalmente vazias das pontas. Aposta em aberto ocupa poucos
  // dias: sem isso, ver 4 semanas em branco antes da primeira aposta é a regra,
  // não a exceção — o dado real fica espremido no rodapé de um mês oco. As
  // semanas vazias no MEIO ficam (senão o calendário mentiria sobre a distância
  // entre as datas) e a semana de hoje nunca é podada.
  const semanas = [];
  for (let i = 0; i < cels.length; i += 7) semanas.push(cels.slice(i, i + 7));
  while (semanas.length > 1 && semanas[0].every(c => c.vazia)) semanas.shift();
  while (semanas.length > 1 && semanas[semanas.length - 1].every(c => c.vazia)) semanas.pop();
  const grade = semanas.flat().map(c => c.html).join('');

  const barra = `<div class="abrt-cal__bar">
    <button class="cal__nav" onclick="abrtNavMes(-1)" aria-label="Mês anterior"${idx <= 0 ? ' disabled' : ''}>‹</button>
    <div class="cal__month" style="pointer-events:none">${MESES[parseInt(mo) - 1]} ${yr}</div>
    <button class="cal__nav" onclick="abrtNavMes(1)" aria-label="Próximo mês"${idx >= meses.length - 1 ? ' disabled' : ''}>›</button>
    <span class="abrt-cal__spacer"></span>
    <span class="abrt-cal__legend"><i></i>exposição do dia</span>
  </div>`;
  const WK = ['S', 'T', 'Q', 'Q', 'S', 'S', 'D'];

  host.innerHTML = horizonte + barra +
    `<div class="abrt-cal__wk">${WK.map((l, i) => `<span${i >= 5 ? ' class="we"' : ''}>${l}</span>`).join('')}</div>` +
    `<div class="abrt-cal__grid">${grade}</div>`;
}
function abrtNavMes(delta) {
  const rows = filtrarAbertas('abertas');
  const meses = [...new Set(rows.map(r => r.data.slice(0, 7)))].sort();
  const i = meses.indexOf(_abrtMes);
  if (i < 0) return;
  const alvo = i + delta;
  if (alvo < 0 || alvo >= meses.length) return;
  _abrtMes = meses[alvo];
  _abrtCalendario(rows);
}
window.abrtNavMes = abrtNavMes;

// ── 3) Barras de exposição (por casa · por tipster) ────────────────────────
// Ordena por stake desc. A barra é proporcional ao MAIOR item, não ao total —
// o que a torna legível quando uma casa concentra quase tudo.
function _abrtBarras(hostId, rows, chave, comChip) {
  const host = document.getElementById(hostId);
  if (!host) return;
  if (!rows.length) { host.innerHTML = mkEmpty('Nenhuma aposta em aberto no filtro'); return; }
  const ents = Object.entries(_abrtAgrupar(rows, chave)).sort((a, b) => b[1].stake - a[1].stake);
  const max = Math.max(1, ...ents.map(([, d]) => d.stake));
  const total = ents.reduce((a, [, d]) => a + d.stake, 0);
  host.innerHTML = `<div class="abrt-bars">` + ents.map(([nome, d]) => {
    const pct = total > 0 ? d.stake / total * 100 : 0;
    return `<div class="abrt-bar">` +
      `<span class="abrt-bar__id" title="${esc(nome)}">${comChip ? mkHouseChip(nome) : ''}${esc(nome || '—')}</span>` +
      `<span class="abrt-bar__track"><span class="abrt-bar__fill" style="width:${(d.stake / max * 100).toFixed(1)}%"></span></span>` +
      `<span class="abrt-bar__val">${fmtR(d.stake)}` +
        `<span class="abrt-bar__meta">${d.n} ${d.n === 1 ? 'aposta' : 'apostas'} · ${fmtPct(pct, 1, false)}</span>` +
      `</span>` +
    `</div>`;
  }).join('') + `</div>`;
}

// ── 4) Lista completa ──────────────────────────────────────────────────────
// Ordem: data do evento CRESCENTE — o que resolve primeiro fica no topo (numa tela
// de exposição viva, o próximo a liquidar é o que importa). Editar/deletar reusam
// o modal e os endpoints da Minha Base (abrirEdicaoApostas / deletarApostas);
// `_apRowById` já procura em DADOS_ABERTAS, então a linha é encontrada.
function _abrtLista(rows) {
  const host = document.getElementById('abertasLista');
  const cont = document.getElementById('abertasContagem');
  if (!host) return;
  if (cont) {
    const st = rows.reduce((a, r) => a + (Number(r.stake) || 0), 0);
    cont.innerHTML = rows.length
      ? `${rows.length.toLocaleString('pt-BR')} ${rows.length === 1 ? 'aposta' : 'apostas'} · ${fmtR(st)} em jogo`
      : 'nenhuma aposta em aberto';
  }
  if (!rows.length) { host.innerHTML = mkEmpty('Nenhuma aposta em aberto no filtro'); return; }
  const ord = rows.slice().sort((a, b) => (a.data < b.data ? -1 : a.data > b.data ? 1 : b.stake - a.stake));
  host.innerHTML = ord.map(r => {
    const q = _abrtQuando(r.data);
    const parceiro = r.parceiro && r.parceiro !== '—' ? r.parceiro : '';
    const ret = _abrtRetorno(r);
    // Editável só com id (Postgres) E linha do dono efetivo — mesma régua da Minha Base.
    const editavel = r.id != null && r.operador === window.__dono;
    return `<div class="abrt-row abrt-linha">` +
      `<div class="abrt-quando"><span class="dia">${_abrtBR(r.data)}</span><span class="rel ${q.cls}">${q.txt}</span></div>` +
      `<div>${r.aposta ? `<div class="abrt-tipo">${esc(r.aposta)}</div>` : ''}` +
        `<div class="abrt-desc" title="${esc(r.descricao || r.aposta || '')}">${esc(r.descricao || r.aposta || '—')}</div></div>` +
      `<div class="abrt-txt">${mkSpChip(r.esporte)}<span>${esc(r.esporte || '—')}</span></div>` +
      `<div class="abrt-txt">${esc(r.tipster || '—')}</div>` +
      `<div class="abrt-casa-cel">${mkHouseChip(r.casa)}<div class="abrt-conta">` +
        `<span class="nome">${esc(r.casa || '—')}</span>` +
        `${parceiro ? `<span class="sub">${esc(parceiro)}</span>` : ''}</div></div>` +
      `<div class="abrt-num">${fmtR(r.stake)}</div>` +
      `<div class="abrt-num">${Number(r.odd) > 0 ? fmtOdd(r.odd) : '—'}</div>` +
      `<div class="abrt-num abrt-ret">${ret > 0 ? fmtR(ret) : '<span style="color:var(--ink-mute)">—</span>'}</div>` +
      `<div class="abrt-acts">${editavel
        ? `<button class="act-btn" title="Editar aposta" onclick="abrirEdicaoApostas(${r.id})">✎</button>` +
          `<button class="act-btn del" title="Deletar aposta" onclick="deletarApostas(${r.id})">✕</button>`
        : `<span class="act-btn off" title="Linha da planilha ao vivo ou de um operador — edite na origem">✎</span>`}</div>` +
    `</div>`;
  }).join('');
}
