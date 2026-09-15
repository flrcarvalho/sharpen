/* sb-tipster.js — bloco de tipster na sidebar, COMPARTILHADO pelas duas cascas (s362).
 *
 * Quem usa:
 *   · host  (/app, app/static/app.html)            → modo 'host', dinheiro em R$
 *   · vitrine (/tipsters/<slug>, dash/index.html)  → modo 'vitrine', resultado em u
 *
 * Por que um arquivo só: o mesmo bloco pintado por dois markups diverge no primeiro
 * ajuste, e as duas telas mostram A MESMA CONTA. O CSS segue a mesma regra e mora no
 * /static/shell.css (fatia 2).
 *
 * O que o bloco NÃO faz: ele é contexto da CONTA, não da consulta. Filtro de tela
 * (período, esporte, casa) não o recorta — os números são sempre mês corrente contra
 * vida inteira, servidos pelo /conta/perfil (host) ou derivados do feed (vitrine).
 *
 * Máscara de dinheiro: reusa os helpers canônicos quando a casca já os tem (o
 * Dashboard define fmtPL/fmtU/fmtPct em assets/js/app.js). Só no host, que não carrega
 * aquele bundle, as mesmas funções são definidas aqui — mesma máscara, nunca uma
 * segunda. A escolha é feita na CHAMADA, não no load, para a ordem das tags <script>
 * não decidir qual régua o dinheiro usa.
 */
(function (global) {
  'use strict';

  // ── Máscara monetária (UI_REFERENCE §5) ───────────────────────────────────
  // A escolha "helper da casca ou cópia local" é feita NA CHAMADA, nunca no carregamento
  // do arquivo: amarrar no load faria a ordem das tags <script> decidir qual máscara a
  // tela usa, e um reordenamento futuro trocaria a régua do dinheiro em silêncio.
  function _fmt(v, d) {
    d = (d === undefined) ? 2 : d;
    return Math.abs(v).toLocaleString('pt-BR', { minimumFractionDigits: d, maximumFractionDigits: d });
  }
  function _fmtPL(v) {
    var cls = v > 0 ? 'pos' : (v < 0 ? 'neg' : '');
    var sign = v > 0 ? '+' : (v < 0 ? '−' : '');
    return '<span class="money ' + cls + '"><span class="money-sign">' + sign +
           'R$</span><span class="money-val">' + fmt(Math.abs(v)) + '</span></span>';
  }
  function _fmtU(v) {
    var n = Number(v) || 0;
    var cls = n > 0 ? 'pos' : (n < 0 ? 'neg' : '');
    var sign = n > 0 ? '+' : (n < 0 ? '−' : '');
    return '<span class="money ' + cls + '"><span class="money-val">' + sign +
           fmt(Math.abs(n)) + '<span class="money-u">u</span></span></span>';
  }
  function _fmtPct(v, d, signed) {
    d = (d === undefined) ? 2 : d;
    var abs = Math.abs(v).toLocaleString('pt-BR', { minimumFractionDigits: d, maximumFractionDigits: d });
    if (signed === false) return abs + '%';
    return (v >= 0 ? '+' : '−') + abs + '%';
  }
  function fmt(v, d)    { return (global.fmt    || _fmt)(v, d); }
  function fmtPL(v)     { return (global.fmtPL  || _fmtPL)(v); }
  function fmtU(v)      { return (global.fmtU   || _fmtU)(v); }
  function fmtPct(v, d) { return (global.fmtPct || _fmtPct)(v, d); }

  /* Nome, plano e monograma entram por `textContent`, nunca por innerHTML: o nome vem
   * do banco e do registro, e escapar à mão é o tipo de coisa que se esquece uma vez.
   * Só os NÚMEROS são montados como HTML, e eles passam pelos helpers monetários.
   */

  /* Monograma: duas iniciais das duas primeiras palavras; nome de uma palavra usa as
   * duas primeiras letras dela (`Sharpen` → `SH`). Derivado do nome, nunca guardado —
   * renomear a conta não pode deixar um monograma velho para trás. */
  function iniciais(nome) {
    var partes = String(nome || '').trim().split(/\s+/).filter(Boolean);
    if (!partes.length) return '?';
    if (partes.length === 1) return partes[0].slice(0, 2).toUpperCase();
    return (partes[0][0] + partes[1][0]).toUpperCase();
  }

  /* Uma célula da matriz. `n` é a contagem de apostas resolvidas da janela: zero não é
   * "P/L 0,00", é "não dá para calcular" — e a célula vira travessão em --ink-mute.
   * Conta nova mostrando +0,00% leria como desempenho neutro medido. */
  function celula(valor, n, tipo, unidade, secundaria) {
    if (!n) return '<span' + (secundaria ? ' class="lo vazio"' : ' class="vazio"') + '>—</span>';
    if (tipo === 'roi') {
      var c = valor >= 0 ? 'pos' : 'neg';
      var corpo = '<span class="money ' + c + '"><span class="money-val">' + fmtPct(valor, 2) + '</span></span>';
      return '<span' + (secundaria ? ' class="lo"' : '') + '>' + corpo + '</span>';
    }
    return '<span' + (secundaria ? ' class="lo"' : '') + '>' +
           (unidade === 'u' ? fmtU(valor) : fmtPL(valor)) + '</span>';
  }

  var CHEV = '<svg class="sb-tipster__chev" viewBox="0 0 24 24" aria-hidden="true"><path d="M8 10l4 4 4-4"/></svg>';
  var ACEITA = 'image/png,image/jpeg,image/webp,image/svg+xml';

  /* Monta o bloco e devolve a API para atualizá-lo.
   *
   * cfg:
   *   editavel  — true no host (o dono está logado e pode trocar a logo);
   *               false na vitrine, onde não há sessão para autorizar upload nenhum.
   *   unidade   — 'reais' | 'u'
   *   logoUrl   — rota que serve a logo (sem ela o avatar fica no monograma)
   *   onMenu    — callback(menuEl) para a casca acrescentar itens próprios
   *               (o "Ver base de" do host entra por aqui, e não hard-coded, porque a
   *               vitrine não tem esse conceito)
   */
  function montar(cfg) {
    cfg = cfg || {};
    var editavel = !!cfg.editavel;
    var unidade = cfg.unidade === 'u' ? 'u' : 'reais';

    var el = document.createElement('div');
    el.className = 'sb-tipster';
    el.hidden = true;                       // só aparece quando há perfil (nada de esqueleto piscando)
    var tagAv = editavel ? 'button' : 'span';
    el.innerHTML =
      '<div class="sb-tipster__top">' +
        '<' + tagAv + ' class="sb-tipster__av"' +
          (editavel ? ' type="button" title="Trocar a logo (clique ou arraste uma imagem)"' : '') + '>' +
          '<span class="sb-tipster__mono" aria-hidden="true"></span>' +
          '<img class="sb-tipster__img" alt="" hidden>' +
          (editavel ? '<span class="sb-tipster__ring" aria-hidden="true"></span>' : '') +
        '</' + tagAv + '>' +
        (editavel
          ? '<button class="sb-tipster__id" type="button" aria-haspopup="menu" aria-expanded="false">' +
              '<span class="sb-tipster__tx">' +
                '<span class="sb-tipster__nm"></span><span class="sb-tipster__plan"></span>' +
              '</span>' + CHEV +
            '</button>'
          : '<span class="sb-tipster__id" style="cursor:default">' +
              '<span class="sb-tipster__tx">' +
                '<span class="sb-tipster__nm"></span><span class="sb-tipster__plan"></span>' +
              '</span>' +
            '</span>') +
      '</div>' +
      '<div class="sb-tipster__stats"></div>' +
      '<div class="sb-tipster__erro" hidden role="alert"></div>' +
      (editavel ? '<div class="sb-tipster__menu" hidden role="menu"></div>' +
                  '<input type="file" class="sb-tipster__file" accept="' + ACEITA + '" hidden>' : '');

    var av = el.querySelector('.sb-tipster__av');
    var mono = el.querySelector('.sb-tipster__mono');
    var img = el.querySelector('.sb-tipster__img');
    var nm = el.querySelector('.sb-tipster__nm');
    var plan = el.querySelector('.sb-tipster__plan');
    var idBtn = el.querySelector('.sb-tipster__id');
    var stats = el.querySelector('.sb-tipster__stats');
    var erro = el.querySelector('.sb-tipster__erro');
    var menu = el.querySelector('.sb-tipster__menu');
    var file = el.querySelector('.sb-tipster__file');
    var perfilAtual = null;

    function avisar(texto) {
      erro.textContent = texto || '';
      erro.hidden = !texto;
    }

    /* A logo entra com cache-bust pelo carimbo: a URL é estável (/conta/logo), então
     * sem isso a imagem nova ficaria escondida atrás da antiga no cache do navegador
     * — o upload "não faria nada" aos olhos de quem clicou. */
    function pintarLogo(temLogo, versao) {
      if (!cfg.logoUrl || temLogo === false) { img.hidden = true; img.removeAttribute('src'); return; }
      // `temLogo` indefinido = "tenta": a vitrine pública não recebe esse booleano (a
      // rota do perfil é autenticada) e descobre pela própria imagem. O onerror é o
      // que faz a conta sem logo cair no monograma em vez de mostrar ícone quebrado.
      img.onerror = function () { img.hidden = true; img.removeAttribute('src'); };
      img.src = cfg.logoUrl + '?v=' + (versao || Date.now());
      img.alt = 'Logo de ' + (perfilAtual && perfilAtual.nome ? perfilAtual.nome : 'tipster');
      img.hidden = false;
    }

    function pintarStats(p) {
      var mes = p.mes || {}, hist = p.historico || {};
      stats.innerHTML =
        '<span class="hd rw"></span><span class="hd">Mês</span><span class="hd">Histórico</span>' +
        '<span class="rw">ROI</span>' +
        celula(mes.roi, mes.apostas, 'roi', unidade, false) +
        celula(hist.roi, hist.apostas, 'roi', unidade, true) +
        '<span class="rw pb">P/L</span>' +
        celula(mes.pl, mes.apostas, 'pl', unidade, false) +
        celula(hist.pl, hist.apostas, 'pl', unidade, true);
      // A última linha ganha a folga de baixo depois de montada: marcar no template
      // exigiria duplicar a classe em três lugares que já variam por estado.
      var filhos = stats.children;
      for (var i = filhos.length - 3; i < filhos.length; i++) filhos[i].classList.add('pb');
      // Aperto medido, não adivinhado: P/L de 7 dígitos em R$ não cabe em duas colunas
      // na sidebar de 264px, e em unidades sobra espaço de sobra. Quem sabe se coube é
      // o layout — daí a leitura do scrollWidth. O que encolhe é o espaço em volta
      // (padding, tracking), nunca o número: 13px é o piso da Escada de Tinta para
      // valor numérico, e abaixo dele o dado deixa de se ler.
      stats.classList.remove('apertado');
      if (stats.scrollWidth > stats.clientWidth) stats.classList.add('apertado');
    }

    function aplicar(p) {
      if (!p) return;
      perfilAtual = p;
      var nome = p.nome || p.dono || '';
      nm.textContent = nome;
      nm.title = nome;
      mono.textContent = iniciais(nome);
      // Vendo a base de outro: o aviso ocupa o lugar do plano, em --accent. É o sinal
      // que o .sb-operador dava com o rótulo "Vendo", e ele não pode se perder na
      // mudança — quem escreve achando que é a própria base escreve na do vizinho.
      if (p.vendo) {
        plan.textContent = 'Vendo · ' + (p.dono || '');
        plan.className = 'sb-tipster__plan vendo';
        el.classList.add('vendo');
      } else {
        plan.textContent = p.plano ? ('Plano ' + p.plano) : 'Sem plano';
        plan.className = 'sb-tipster__plan' + (p.plano ? '' : ' sem');
        el.classList.remove('vendo');
      }
      pintarStats(p);
      pintarLogo(p.tem_logo, p.logo_versao);
      el.hidden = false;
    }

    // ── Upload: clique, teclado e arrastar-e-soltar ─────────────────────────
    if (editavel) {
      var enviando = false;

      function enviar(arquivo) {
        if (!arquivo || enviando) return;
        enviando = true;
        avisar('');
        av.classList.add('is-loading');
        // Preview otimista: a arte aparece antes da confirmação do servidor. Se ele
        // recusar, o objectURL é descartado e o avatar volta ao estado anterior.
        var previa = URL.createObjectURL(arquivo);
        var antes = { src: img.getAttribute('src'), hidden: img.hidden };
        img.src = previa; img.hidden = false;
        var corpo = new FormData();
        corpo.append('arquivo', arquivo);
        fetch('/conta/logo', { method: 'POST', body: corpo })
          .then(function (r) { return r.json().then(function (j) { return { ok: r.ok, j: j }; }); })
          .then(function (res) {
            URL.revokeObjectURL(previa);
            if (!res.ok) throw new Error((res.j && res.j.detail) || 'Não consegui salvar a logo.');
            if (perfilAtual) perfilAtual.tem_logo = true;
            pintarLogo(true, Date.now());
            montarMenu();
          })
          .catch(function (e) {
            URL.revokeObjectURL(previa);
            if (antes.src) { img.src = antes.src; img.hidden = antes.hidden; }
            else { img.removeAttribute('src'); img.hidden = true; }
            avisar(e.message || 'Não consegui salvar a logo.');
          })
          .then(function () { enviando = false; av.classList.remove('is-loading'); });
      }

      av.addEventListener('click', function (e) { e.stopPropagation(); file.click(); });
      file.addEventListener('change', function () {
        enviar(file.files && file.files[0]);
        file.value = '';   // mesmo arquivo duas vezes seguidas precisa disparar 'change' de novo
      });
      ['dragenter', 'dragover'].forEach(function (ev) {
        av.addEventListener(ev, function (e) { e.preventDefault(); av.classList.add('is-drop'); });
      });
      ['dragleave', 'dragend'].forEach(function (ev) {
        av.addEventListener(ev, function () { av.classList.remove('is-drop'); });
      });
      av.addEventListener('drop', function (e) {
        e.preventDefault();
        av.classList.remove('is-drop');
        var dt = e.dataTransfer;
        enviar(dt && dt.files && dt.files[0]);
      });

      function remover() {
        fetch('/conta/logo', { method: 'DELETE' })
          .then(function () {
            if (perfilAtual) perfilAtual.tem_logo = false;
            pintarLogo(false);
            montarMenu();
          })
          .catch(function () { avisar('Não consegui remover a logo.'); });
      }

      function item(texto, aoClicar, classe) {
        var b = document.createElement('button');
        b.type = 'button';
        b.setAttribute('role', 'menuitem');
        b.textContent = texto;
        if (classe) b.className = classe;
        b.addEventListener('click', function (e) { e.stopPropagation(); fechar(); aoClicar(); });
        return b;
      }

      function montarMenu() {
        menu.innerHTML = '';
        menu.appendChild(item('Trocar logo', function () { file.click(); }));
        if (perfilAtual && perfilAtual.tem_logo) menu.appendChild(item('Remover logo', remover));
        if (typeof cfg.onMenu === 'function') cfg.onMenu(menu, { item: item, fechar: fechar });
      }

      function fechar() {
        menu.hidden = true;
        el.classList.remove('open');
        idBtn.setAttribute('aria-expanded', 'false');
      }
      function alternar() {
        var abrir = menu.hidden;
        montarMenu();
        menu.hidden = !abrir;
        el.classList.toggle('open', abrir);
        idBtn.setAttribute('aria-expanded', abrir ? 'true' : 'false');
      }

      idBtn.addEventListener('click', function (e) { e.stopPropagation(); alternar(); });
      document.addEventListener('click', function (e) { if (!el.contains(e.target)) fechar(); });
      document.addEventListener('keydown', function (e) { if (e.key === 'Escape') fechar(); });
    }

    return { el: el, aplicar: aplicar, avisar: avisar };
  }

  global.SbTipster = { montar: montar, iniciais: iniciais };
})(window);
