// ── Logs de extração (s433, entrega 1.4) ─────────────────────────────────────
// Uma linha por extração (`GET /extracoes/log`). Substitui o RAIO-X e o histórico que
// moravam na Extração e no navegador. O usuário vê o que entrou na planilha dele e o que
// pede ação; o caminho de cada aposta, as notas da IA e o custo só chegam para o admin
// (o servidor nem os manda para os outros).
//
// Reusa os componentes do dash: `.filters`/`.qbtn` (o mesmo seletor de período das outras
// telas) e `.tbl`. Nenhum número aqui é dinheiro em R$, então nada passa pelo `.money`;
// o custo do admin é USD, exceção do UI_REFERENCE §5.3.
let _lgDias = 1, _lgSoAviso = false, _lgAberto = null, _lgDados = [];

const _LG_SIT = { ok: ['ok', 'ok'], aviso: ['a conferir', 'aviso'], erro: ['erro', 'erro'] };

function _lgHora(iso) {
  // Fuso do navegador, nunca UTC (memória `data_fuso_local_nunca_utc`).
  const d = new Date(iso);
  if (isNaN(d)) return '';
  const hh = d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
  if (_lgDias === 1) return hh;
  return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }) + ' ' + hh;
}
function _lgNum(v) { return v == null ? '—' : Number(v).toLocaleString('pt-BR'); }
function _lgTempo(s) {
  const n = Math.round(Number(s) || 0);
  return n < 60 ? `${n} s` : `${Math.floor(n / 60)} min ${String(n % 60).padStart(2, '0')} s`;
}
function _lgEsc(s) {
  return String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function _lgFiltros() {
  const q = (d, rot) => `<button class="qbtn ${_lgDias === d ? 'active' : ''}" onclick="lgPeriodo(${d})">${rot}</button>`;
  return `<div class="filters">
    <div class="filter-group"><div class="filter-label">Período</div>
      <div class="quick-btns">${q(1, 'Hoje')}${q(7, '7d')}${q(30, '30d')}</div></div>
    <div class="filter-group"><div class="filter-label">Mostrar</div>
      <div class="quick-btns">
        <button class="qbtn ${_lgSoAviso ? '' : 'active'}" onclick="lgSoAviso(false)">Todas</button>
        <button class="qbtn ${_lgSoAviso ? 'active' : ''}" onclick="lgSoAviso(true)">Só com aviso</button>
      </div></div>
  </div>`;
}

function _lgDetalhe(r) {
  const avisos = (r.avisos || []).length
    ? `<ul class="lg-lista">${r.avisos.map(a => `<li>${_lgEsc(a)}</li>`).join('')}</ul>`
    : '<div class="lg-vazio">Nenhum aviso nesta extração.</div>';
  let adm = '';
  if (r.admin) {
    const a = r.admin, mot = Object.entries(a.motivos || {}).filter(([, n]) => n > 0);
    const custo = 'US$ ' + Number(a.custo_usd || 0).toLocaleString('pt-BR', { minimumFractionDigits: 4, maximumFractionDigits: 4 });
    adm = `<div class="lg-adm">
      <div class="filter-label">Só para o admin</div>
      <ul class="lg-lista">
        <li>Caminho: ${a.prontas == null ? '—' : `${_lgNum(a.prontas)} prontas antes da leitura · ${_lgNum(a.para_ia)} lidas pela IA`}</li>
        ${mot.length ? `<li>Motivo da leitura: ${mot.map(([m, n]) => `${_lgEsc(m)} ${n}`).join(' · ')}</li>` : ''}
        <li>Modelo: ${_lgEsc(a.modelo || '—')} · custo ${custo}</li>
      </ul>
      ${a.notas && a.notas !== 'Nenhuma' ? `<div class="lg-notas">${_lgEsc(a.notas)}</div>` : ''}
    </div>`;
  }
  return `<tr class="lg-det"><td colspan="7"><div class="lg-det-in">
    <div><div class="lg-det-h"><span class="lg-casa">${_lgEsc(r.casa)}</span> <span class="lg-conta">· ${_lgEsc(r.parceiro)} · ${_lgHora(r.criado_em)}</span></div>${avisos}</div>${adm}
  </div></td></tr>`;
}

function _lgTabela() {
  if (!_lgDados.length) {
    return `<div class="lg-vazio-tela">${_lgSoAviso
      ? 'Nenhuma extração com aviso neste período.'
      : 'Nenhuma extração neste período. Cada vez que você clica em Processar, ou o SharpenUp envia uma captura, ela aparece aqui com o que entrou na sua planilha.'}</div>`;
  }
  const linhas = _lgDados.map(r => {
    const [rot, cls] = _LG_SIT[r.situacao] || _LG_SIT.ok;
    const aberto = _lgAberto === r.id;
    return `<tr class="lg-row${aberto ? ' on' : ''}" onclick="lgAbrir(${r.id})" tabindex="0" onkeydown="if(event.key==='Enter')lgAbrir(${r.id})">
      <td class="td-l mono">${_lgHora(r.criado_em)}</td>
      <td class="td-l"><span class="lg-casa">${_lgEsc(r.casa)}</span> <span class="lg-conta">· ${_lgEsc(r.parceiro)}</span></td>
      <td class="td-num">${_lgNum(r.total)}</td>
      <td class="td-num">${_lgNum(r.novas)}</td>
      <td class="td-num">${_lgNum(r.atualizadas)}</td>
      <td class="td-num">${_lgTempo(r.segundos)}</td>
      <td class="td-l"><span class="lg-sit ${cls}">${rot}</span></td>
    </tr>${aberto ? _lgDetalhe(r) : ''}`;
  }).join('');
  return `<div class="tbl-wrap"><table class="tbl lg-tbl">
    <thead><tr><th class="th-l">Hora</th><th class="th-l">Casa · conta</th><th class="th-r">Apostas lidas</th>
      <th class="th-r">Novas</th><th class="th-r">Atualizadas</th><th class="th-r">Tempo</th><th class="th-l">Situação</th></tr></thead>
    <tbody>${linhas}</tbody></table></div>`;
}

function _lgPintar() {
  const el = document.getElementById('logsContent');
  if (!el) return;
  const avisos = _lgDados.filter(r => r.situacao !== 'ok').length;
  const sub = _lgDados.length
    ? `${_lgDados.length} extraç${_lgDados.length === 1 ? 'ão' : 'ões'}${avisos ? ` · ${avisos} com aviso` : ''} · clique numa linha para ver o detalhe`
    : '';
  el.innerHTML = _lgFiltros() + mkCard('lg_lista', 'Extrações',
    `<div class="lg-sub">${sub}</div>${_lgTabela()}`);
}

async function renderLogs() {
  const el = document.getElementById('logsContent');
  if (!el) return;
  if (!_lgDados.length) el.innerHTML = _lgFiltros() + mkCard('lg_lista', 'Extrações', '<div class="lg-vazio-tela">Carregando…</div>');
  try {
    const r = await fetch(`/extracoes/log?dias=${_lgDias}&so_aviso=${_lgSoAviso}`);
    if (!r.ok) throw new Error('HTTP ' + r.status);
    _lgDados = (await r.json()).extracoes || [];
    _lgPintar();
  } catch (e) {
    el.innerHTML = _lgFiltros() + mkCard('lg_lista', 'Extrações',
      '<div class="lg-vazio-tela">Não foi possível carregar os logs agora. Tente de novo em instantes.</div>');
  }
}
function lgPeriodo(d) { _lgDias = d; _lgAberto = null; renderLogs(); }
function lgSoAviso(v) { _lgSoAviso = v; _lgAberto = null; renderLogs(); }
function lgAbrir(id) { _lgAberto = _lgAberto === id ? null : id; _lgPintar(); }
