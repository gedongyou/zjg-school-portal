/* search.js — 站内搜索页：读 window.SITE_INDEX，按词匹配并高亮 */
(function () {
  'use strict';

  var IDX = window.SITE_INDEX || [];
  var form = document.querySelector('[data-srch]');
  var input = document.querySelector('[data-srch-input]');
  var tip = document.querySelector('[data-srch-tip]');
  var list = document.querySelector('[data-srch-list]');
  if (!form) return;

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  function mark(text, words) {
    var out = esc(text);
    words.forEach(function (w) {
      if (!w) return;
      var re = new RegExp('(' + w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'gi');
      out = out.replace(re, '<em>$1</em>');
    });
    return out;
  }

  function run(q) {
    q = (q || '').trim();
    var words = q ? q.split(/\s+/).filter(Boolean) : [];
    var out = IDX;
    if (words.length) {
      out = IDX.filter(function (o) {
        var s = (o.t + ' ' + o.m + ' ' + (o.k || '')).toLowerCase();
        return words.every(function (w) { return s.indexOf(w.toLowerCase()) > -1; });
      });
    }
    var total = out.length;
    out = out.slice(0, 40);

    tip.textContent = words.length
      ? (total ? '找到 ' + total + ' 条结果' + (total > 40 ? '，显示前 40 条' : '') : '没有找到匹配的内容')
      : '共 ' + IDX.length + ' 条可检索内容，输入关键词开始';

    list.innerHTML = out.map(function (o) {
      return '<li><a href="' + o.u + '"><div class="t">' + mark(o.t, words) +
        '</div><div class="m">' + esc(o.m) + '</div></a></li>';
    }).join('');

    // 把查询写进地址栏，方便直接分享某次搜索结果
    var url = new URL(location.href);
    if (q) url.searchParams.set('q', q); else url.searchParams.delete('q');
    history.replaceState(null, '', url);
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    run(input.value);
  });
  input.addEventListener('input', function () {
    clearTimeout(input._t);
    input._t = setTimeout(function () { run(input.value); }, 180);
  });

  var q0 = new URL(location.href).searchParams.get('q') || '';
  input.value = q0;
  run(q0);
  if (!q0) input.focus();
})();
