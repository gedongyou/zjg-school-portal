/* site.js — 首页交互：轮播、栏目高亮、站内索引、回到顶部 */
(function () {
  'use strict';

  /* ---------- 2. 轮播 ---------- */
  (function hero() {
    var root = document.querySelector('[data-hero]');
    if (!root) return;
    var track = root.querySelector('[data-hero-track]');
    var items = track.children;
    var n = items.length;
    var dots = root.querySelector('[data-hero-dots]');
    var i = 0, timer = null;

    for (var k = 0; k < n; k++) {
      var d = document.createElement('button');
      d.type = 'button';
      d.setAttribute('aria-label', '第 ' + (k + 1) + ' 张');
      d.dataset.go = String(k);
      dots.appendChild(d);
    }

    function paint() {
      track.style.transform = 'translateX(' + (-i * 100) + '%)';
      Array.prototype.forEach.call(dots.children, function (b, j) {
        b.classList.toggle('on', j === i);
      });
    }
    function go(k) { i = (k + n) % n; paint(); }
    function play() { stop(); timer = setInterval(function () { go(i + 1); }, 6500); }
    function stop() { if (timer) { clearInterval(timer); timer = null; } }

    root.querySelector('[data-hero-prev]').addEventListener('click', function () { go(i - 1); play(); });
    root.querySelector('[data-hero-next]').addEventListener('click', function () { go(i + 1); play(); });
    dots.addEventListener('click', function (e) {
      var b = e.target.closest('[data-go]');
      if (b) { go(Number(b.dataset.go)); play(); }
    });
    root.addEventListener('mouseenter', stop);
    root.addEventListener('mouseleave', play);
    root.addEventListener('focusin', stop);

    var x0 = null;
    root.addEventListener('touchstart', function (e) { x0 = e.touches[0].clientX; stop(); }, { passive: true });
    root.addEventListener('touchend', function (e) {
      if (x0 === null) return;
      var dx = e.changedTouches[0].clientX - x0;
      if (Math.abs(dx) > 40) go(i + (dx < 0 ? 1 : -1));
      x0 = null; play();
    });
    document.addEventListener('visibilitychange', function () {
      document.hidden ? stop() : play();
    });

    paint();
    play();
  })();

  /* ---------- 3. 栏目高亮 + 回到顶部 ---------- */
  (function navState() {
    var top = document.querySelector('[data-top]');
    var ticking = false;
    function onScroll() {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(function () {
        if (top) top.classList.toggle('show', window.scrollY > 520);
        ticking = false;
      });
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
    if (top) top.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  })();

  /* ---------- 4. 站内索引（读构建时生成的全站索引） ---------- */
  (function finder() {
    var box = document.getElementById('finder');
    if (!box) return;
    var input = box.querySelector('[data-finder-input]');
    var list = box.querySelector('[data-finder-list]');
    var tip = box.querySelector('[data-finder-tip]');
    var lastFocus = null;
    var INDEX = (window.SITE_INDEX || []).slice();
    var up = document.body.dataset.up || '';

    function render(q) {
      q = (q || '').trim().toLowerCase();
      var out = INDEX;
      if (q) {
        var words = q.split(/\s+/);
        out = INDEX.filter(function (o) {
          var s = (o.t + ' ' + o.m + ' ' + (o.k || '')).toLowerCase();
          return words.every(function (w) { return s.indexOf(w) > -1; });
        });
      }
      var total = out.length;
      out = out.slice(0, 20);
      list.innerHTML = out.map(function (o) {
        return '<li><a href="' + up + o.u + '"><span>' + esc(o.t) + '</span><span class="fm">' + esc(o.m) + '</span></a></li>';
      }).join('');
      tip.textContent = q
        ? (total ? '找到 ' + total + ' 条' : '没有匹配的条目，换个词试试')
        : '共 ' + INDEX.length + ' 条，输入关键词过滤';
    }

    function esc(s) {
      return String(s).replace(/[&<>"]/g, function (c) {
        return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
      });
    }

    function open(q) {
      lastFocus = document.activeElement;
      box.hidden = false;
      document.body.style.overflow = 'hidden';
      input.value = q || '';
      render(input.value);
      setTimeout(function () { input.focus(); }, 30);
    }
    function close() {
      box.hidden = true;
      document.body.style.overflow = '';
      if (lastFocus && lastFocus.focus) lastFocus.focus();
    }

    document.addEventListener('click', function (e) {
      if (e.target.closest('[data-finder]')) { e.preventDefault(); open(''); return; }
      if (e.target.closest('[data-finder-close]')) { close(); return; }
      if (e.target === box) { close(); return; }
    });

    // 头部搜索框：回车或点按钮都交给索引弹层，不跳页
    var form = document.querySelector('.head__search');
    if (form) {
      form.addEventListener('submit', function (e) {
        e.preventDefault();
        open(form.querySelector('input').value);
      });
    }

    list.addEventListener('click', function (e) {
      if (e.target.closest('a')) close();
    });
    input.addEventListener('input', function () { render(input.value); });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && !box.hidden) { close(); return; }
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        box.hidden ? open('') : close();
      }
    });
  })();

  /* ---------- 5. 专业对照：勾选 → 抽屉 → 并排表 ---------- */
  (function compare() {
    var bar = document.querySelector('[data-cmp-bar]');
    var modal = document.querySelector('[data-cmp-modal]');
    if (!bar) return;

    var MAX = 3;
    var nEl = bar.querySelector('[data-cmp-n]');
    var chipsEl = bar.querySelector('[data-cmp-chips]');
    var goBtn = bar.querySelector('[data-cmp-go]');
    var clearBtn = bar.querySelector('[data-cmp-clear]');
    var bodyEl = modal ? modal.querySelector('[data-cmp-body]') : null;
    var picks = Array.prototype.slice.call(document.querySelectorAll('.mj__pick input'));
    var picked = [];   // 存 data-name

    function card(name) {
      return document.querySelector('.mj[data-name="' + name.replace(/"/g, '\\"') + '"]');
    }

    function paint() {
      nEl.textContent = picked.length;
      bar.hidden = picked.length === 0;
      bar.classList.toggle('show', picked.length > 0);
      goBtn.disabled = picked.length < 2;

      chipsEl.innerHTML = picked.map(function (name) {
        return '<span class="cmp__chip">' + esc(name) +
          '<button type="button" data-cmp-del="' + esc(name) + '" aria-label="移出 ' + esc(name) + '">×</button></span>';
      }).join('');

      picks.forEach(function (cb) {
        var on = picked.indexOf(cb.value) > -1;
        cb.checked = on;
        var cardEl = cb.closest('.mj');
        if (cardEl) cardEl.classList.toggle('is-picked', on);
      });
    }

    function esc(s) {
      return String(s).replace(/[&<>"]/g, function (c) {
        return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
      });
    }

    picks.forEach(function (cb) {
      cb.addEventListener('change', function () {
        var name = cb.value;
        var i = picked.indexOf(name);
        if (cb.checked) {
          if (i > -1) return;
          if (picked.length >= MAX) {
            cb.checked = false;
            tip('最多同时对照 ' + MAX + ' 个专业');
            return;
          }
          picked.push(name);
        } else if (i > -1) {
          picked.splice(i, 1);
        }
        paint();
      });
    });

    chipsEl.addEventListener('click', function (e) {
      var b = e.target.closest('[data-cmp-del]');
      if (!b) return;
      var i = picked.indexOf(b.dataset.cmpDel);
      if (i > -1) picked.splice(i, 1);
      paint();
    });

    clearBtn.addEventListener('click', function () { picked = []; paint(); });

    function tip(msg) {
      var el = document.querySelector('[data-cmp-tip]');
      if (!el) {
        el = document.createElement('div');
        el.className = 'cmp__tip';
        el.setAttribute('data-cmp-tip', '');
        bar.appendChild(el);
      }
      el.textContent = msg;
      el.classList.add('on');
      clearTimeout(el._t);
      el._t = setTimeout(function () { el.classList.remove('on'); }, 1800);
    }

    function rows() {
      return [
        ['所属系部', function (c) { return c.dataset.dept; }],
        ['培养方向', function (c) { return c.dataset.core; }],
        ['技能证书', function (c) { return c.dataset.cert; }],
        ['毕业学历', function (c) { return c.dataset.degree; }],
        ['适合考生', function (c) { return c.dataset.fit; }]
      ];
    }

    goBtn.addEventListener('click', function () {
      if (picked.length < 2 || !modal) return;
      var cards = picked.map(function (n) { return card(n); }).filter(Boolean);
      var head = '<tr><th scope="col">对照项</th>' + cards.map(function (c) {
        return '<th scope="col">' + esc(c.dataset.name) + '</th>';
      }).join('') + '</tr>';
      var body = rows().map(function (r) {
        return '<tr><th scope="row">' + r[0] + '</th>' +
          cards.map(function (c) { return '<td>' + esc(r[1](c)) + '</td>'; }).join('') + '</tr>';
      }).join('');
      bodyEl.innerHTML = '<table class="cmp-table"><thead>' + head + '</thead><tbody>' + body + '</tbody></table>';
      modal.hidden = false;
      document.body.style.overflow = 'hidden';
    });

    function close() {
      if (!modal) return;
      modal.hidden = true;
      document.body.style.overflow = '';
    }

    if (modal) {
      modal.addEventListener('click', function (e) {
        if (e.target.closest('[data-cmp-close]') || e.target.hasAttribute('data-cmp-modal')) close();
      });
      document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && !modal.hidden) close();
      });
    }

    paint();
  })();
})();
