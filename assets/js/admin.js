/* admin.js — 内容后台：清单检索、新建/删除、编辑台、前后台预览、专业维护 */
(function () {
  'use strict';

  var D = window.ADMIN_DATA || { news: [], notices: [], majors: [] };
  var KEY_AUTH = 'zhjg_admin_auth';
  var KEY_DRAFT = 'zhjg_admin_draft';
  var KEY_AT = 'zhjg_admin_at';

  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  /* ---------- 草稿状态 ---------- */
  var draft = load();
  function load() {
    try {
      var raw = localStorage.getItem(KEY_DRAFT);
      if (raw) return JSON.parse(raw);
    } catch (e) {}
    return { news: clone(D.news), notices: clone(D.notices), majors: clone(D.majors) };
  }
  function clone(o) { return JSON.parse(JSON.stringify(o)); }
  function save() {
    try {
      localStorage.setItem(KEY_DRAFT, JSON.stringify(draft));
      localStorage.setItem(KEY_AT, String(Date.now()));
    } catch (e) {}
    paint();
    fillMajors();
  }
  function baseOf(kind) { return kind === 'news' ? D.news : D.notices; }
  function arrOf(kind) { return kind === 'news' ? draft.news : draft.notices; }
  // 按 id 比对初始内容，而不是按下标——新建或删除会让下标整体错位
  function baseById(kind, o) {
    var base = baseOf(kind);
    for (var k = 0; k < base.length; k++) if (base[k].id === o.id) return base[k];
    return null;          // 初始内容里没有 = 新建的
  }
  function isDirty(kind, i) {
    var o = arrOf(kind)[i];
    if (!o) return false;
    var b = baseById(kind, o);
    if (!b) return true;
    return JSON.stringify(b) !== JSON.stringify(o);
  }
  function dirtyCount() {
    var n = 0;
    ['news', 'notices'].forEach(function (kind) {
      arrOf(kind).forEach(function (o, i) { if (isDirty(kind, i)) n++; });
    });
    // 被删掉的条目也算改动
    ['news', 'notices'].forEach(function (k) {
      D[k].forEach(function (b) {
        var found = arrOf(k).some(function (o) { return o.id === b.id; });
        if (!found) n++;
      });
    });
    draft.majors.forEach(function (o, i) {
      if (JSON.stringify(o) !== JSON.stringify(D.majors[i])) n++;
    });
    return n;
  }

  /* ---------- 清单状态：必须在 enter() 之前声明，已登录时 enter 会在赋值前被调用 ---------- */
  var filter = { q: '', type: 'all', sort: 'date' };
  var mq = '';

  /* ---------- 登录 ---------- */
  var gate = $('#gate'), shell = $('#shell');
  function authed() {
    try { return localStorage.getItem(KEY_AUTH) === '1'; } catch (e) { return false; }
  }
  function enter() {
    gate.hidden = true;
    shell.hidden = false;
    paint();
    fillEditorList();
    fillMajors();
  }
  if (authed()) enter();

  $('#login-form').addEventListener('submit', function (e) {
    e.preventDefault();
    var u = this.u.value.trim(), p = this.p.value;
    if (u === 'admin' && p === 'admin123') {
      try { localStorage.setItem(KEY_AUTH, '1'); } catch (e2) {}
      enter();
    } else {
      $('#login-tip').textContent = '账号或密码不对。演示账号 admin，密码 admin123。';
      $('#login-tip').style.color = '#a8332a';
    }
  });
  $('#logout').addEventListener('click', function () {
    try { localStorage.removeItem(KEY_AUTH); } catch (e) {}
    location.reload();
  });

  /* ---------- 标签切换 ---------- */
  function goTab(name) {
    $$('.shell__nav button').forEach(function (x) { x.classList.toggle('on', x.dataset.tab === name); });
    $$('.pane').forEach(function (p) { p.classList.toggle('on', p.dataset.pane === name); });
  }
  $$('.shell__nav button').forEach(function (b) {
    b.addEventListener('click', function () { goTab(b.dataset.tab); });
  });

  /* ---------- 清单 ---------- */
  function paint() {
    $('[data-st-news]').textContent = draft.news.length;
    $('[data-st-notice]').textContent = draft.notices.length;
    $('[data-st-major]').textContent = draft.majors.length;
    $('[data-st-draft]').textContent = dirtyCount();
    $('[data-count-news]').textContent = draft.news.length + draft.notices.length;

    var at = null;
    try { at = Number(localStorage.getItem(KEY_AT)) || null; } catch (e) {}
    $('#lmeta').textContent = at ? ('草稿保存于 ' + fmtTime(at)) : '尚未保存过草稿';

    var rows = [];
    ['news', 'notices'].forEach(function (kind) {
      arrOf(kind).forEach(function (n, i) {
        rows.push({ kind: kind, i: i, o: n, dirty: isDirty(kind, i) });
      });
    });

    if (filter.type !== 'all' && filter.type !== 'dirty') {
      rows = rows.filter(function (r) { return (r.kind === 'news' ? 'news' : 'notice') === filter.type; });
    }
    if (filter.type === 'dirty') rows = rows.filter(function (r) { return r.dirty; });
    var q = filter.q.trim().toLowerCase();
    if (q) {
      rows = rows.filter(function (r) {
        return (r.o.title + ' ' + r.o.src + ' ' + r.o.date + ' ' + r.o.cat).toLowerCase().indexOf(q) > -1;
      });
    }
    rows.sort(function (a, b) {
      if (filter.sort === 'title') return a.o.title.localeCompare(b.o.title, 'zh');
      return String(b.o.date).localeCompare(String(a.o.date));
    });

    $('#lnone').hidden = rows.length > 0;
    if (!rows.length) $('#lnone').textContent = '没有符合条件的条目。换一个词，或点"全部"看清单。';

    $('#tbl-list tbody').innerHTML = rows.map(function (r) {
      var tag = r.kind === 'news' ? '<span class="tag">新闻</span>' : '<span class="tag tag--n">公告</span>';
      return '<tr>' +
        '<td>' + tag + '</td>' +
        '<td class="tt">' + (r.dirty ? '<i class="dot" title="有未发布的改动"></i>' : '') +
          esc(r.o.title) + '<span class="sub">' + esc(r.o.cat) + '</span></td>' +
        '<td class="dim">' + esc(r.o.date) + '</td>' +
        '<td class="dim">' + esc(r.o.src) + '</td>' +
        '<td class="ops"><button data-edit="' + r.kind + '" data-i="' + r.i + '">编辑</button>' +
          '<button class="del" data-del="' + r.kind + '" data-i="' + r.i + '">删除</button></td>' +
        '</tr>';
    }).join('');
  }

  function fmtTime(t) {
    var d = new Date(t), p = function (n) { return (n < 10 ? '0' : '') + n; };
    return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()) + ' ' + p(d.getHours()) + ':' + p(d.getMinutes());
  }

  function esc(s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  }

  $('#lq').addEventListener('input', function () { filter.q = this.value; paint(); });
  $('#lsort').addEventListener('change', function () { filter.sort = this.value; paint(); });
  $$('#ltype button').forEach(function (b) {
    b.addEventListener('click', function () {
      $$('#ltype button').forEach(function (x) { x.classList.toggle('on', x === b); });
      filter.type = b.dataset.type;
      paint();
    });
  });

  /* ---------- 新建 / 删除 ---------- */
  $('#lnew').addEventListener('click', function () {
    var d = new Date(), p = function (n) { return (n < 10 ? '0' : '') + n; };
    var o = {
      id: 'draft-' + Date.now(),
      title: '未命名稿件',
      date: d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()),
      cat: '校园新闻',
      src: '教务处',
      body: ['（正文第一段）']
    };
    draft.news.unshift(o);
    save();
    fillEditorList();
    goTab('edit');
    pick('news', 0);
    $('#edit-form').title.focus();
    $('#edit-form').title.select();
    toast('已新建一条，写完点保存');
  });

  var lastDel = null;
  function deleteItem(kind, i) {
    var arr = arrOf(kind);
    lastDel = { kind: kind, i: i, o: arr[i] };
    arr.splice(i, 1);
    if (cur && cur.kind === kind) {
      if (cur.index === i) cur = null;
      else if (cur.index > i) cur.index--;
    }
    save();
    fillEditorList();
    if (cur) pick(cur.kind, cur.index);
    else $('#edit-empty').hidden = false;
    toast('已删除，5 秒内可撤销', function () {
      var a = arrOf(lastDel.kind);
      a.splice(lastDel.i, 0, lastDel.o);
      save();
      fillEditorList();
      toast('已撤销删除');
    });
  }

  /* ---------- 编辑台 ---------- */
  var cur = null;

  function fillEditorList() {
    var out = [];
    ['news', 'notices'].forEach(function (kind) {
      arrOf(kind).forEach(function (n, i) {
        var lab = kind === 'news' ? '新闻' : '公告';
        out.push('<li><button data-pick="' + kind + '" data-i="' + i + '">' +
          (isDirty(kind, i) ? '<i class="dot" title="有未发布的改动"></i>' : '') +
          esc(n.title) +
          '<span class="d">' + lab + ' · ' + esc(n.date) + ' · ' + esc(n.src) + '</span></button></li>');
      });
    });
    $('#editor-list').innerHTML = out.join('');
  }

  function pick(kind, i) {
    cur = { kind: kind, index: i };
    var arr = arrOf(kind);
    var o = arr[i];
    if (!o) return;
    var f = $('#edit-form');
    f.title.value = o.title;
    f.date.value = o.date;
    f.cat.value = o.cat;
    f.src.value = o.src;
    f.body.value = o.body.join('\n');
    $('#edit-empty').hidden = true;
    $('#edit-meta').textContent = (kind === 'news' ? '新闻' : '公告') + ' 第 ' + (i + 1) + ' / ' + arr.length + ' 条';
    count();
    preview();
    $$('#editor-list button').forEach(function (b) {
      b.classList.toggle('on', b.dataset.pick === kind && Number(b.dataset.i) === i);
    });
  }

  function count() {
    var txt = $('#edit-form').body.value;
    var chars = txt.replace(/\s/g, '').length;
    var paras = txt.split('\n').map(function (s) { return s.trim(); }).filter(Boolean).length;
    $('#edit-count').textContent = chars + ' 字 · ' + paras + ' 段';
  }

  var pvOn = false;
  function preview() {
    if (!pvOn) return;
    var f = $('#edit-form');
    var paras = f.body.value.split('\n').map(function (s) { return s.trim(); }).filter(Boolean);
    var kind = cur ? cur.kind : 'news';
    $('#pv').innerHTML =
      '<article class="art">' +
      '<h1 class="art__t">' + esc(f.title.value || '未命名稿件') + '</h1>' +
      '<p class="art__meta">' + esc(f.cat.value) + '　·　' + esc(f.src.value) + '　·　' +
        esc(f.date.value) + '　·　' + (kind === 'news' ? '新闻' : '公告') + '</p>' +
      paras.map(function (p) { return '<p>' + esc(p) + '</p>'; }).join('') +
      '</article>';
  }

  $('#edit-form').addEventListener('input', function (e) {
    if (e.target.name === 'body') count();
    preview();
  });

  $('#pv-toggle').addEventListener('click', function () {
    pvOn = !pvOn;
    this.classList.toggle('on', pvOn);
    this.textContent = pvOn ? '收起预览' : '前台预览';
    $('#pv').hidden = !pvOn;
    preview();
  });

  document.addEventListener('click', function (e) {
    var b = e.target.closest('[data-pick]');
    if (b) { pick(b.dataset.pick, Number(b.dataset.i)); return; }
    var del = e.target.closest('[data-del]');
    if (del) { deleteItem(del.dataset.del, Number(del.dataset.i)); return; }
    var ed = e.target.closest('[data-edit]');
    if (ed) {
      goTab('edit');
      pick(ed.dataset.edit, Number(ed.dataset.i));
    }
  });

  $('#edit-form').addEventListener('submit', function (e) {
    e.preventDefault();
    if (!cur) return;
    var o = arrOf(cur.kind)[cur.index];
    o.title = this.title.value.trim() || '未命名稿件';
    o.date = this.date.value;
    o.cat = this.cat.value;
    o.src = this.src.value.trim();
    o.body = this.body.value.split('\n').map(function (s) { return s.trim(); }).filter(Boolean);
    save();
    fillEditorList();
    pick(cur.kind, cur.index);
    toast('草稿已保存');
  });

  $('#edit-reset').addEventListener('click', function () {
    if (!cur) return;
    var base = baseOf(cur.kind)[cur.index];
    if (!base) { toast('这是新建的条目，没有初始内容可还原'); return; }
    arrOf(cur.kind)[cur.index] = clone(base);
    save();
    fillEditorList();
    pick(cur.kind, cur.index);
    toast('已还原为初始内容');
  });

  /* ---------- 专业（mq 同样要在 enter 之前声明） ---------- */

  function fillMajors() {
    var rows = draft.majors.map(function (m, i) {
      return { m: m, i: i };
    });
    if (mq.trim()) {
      var q = mq.trim().toLowerCase();
      rows = rows.filter(function (r) {
        return (r.m.name + ' ' + r.m.dept + ' ' + r.m.core + ' ' + r.m.cert + ' ' + r.m.fit).toLowerCase().indexOf(q) > -1;
      });
    }
    $('#mnone').hidden = rows.length > 0;
    $('#tbl-majors tbody').innerHTML = rows.map(function (r) {
      var m = r.m, i = r.i;
      return '<tr>' +
        '<td data-label="专业" class="mname">' + esc(m.name) + '</td>' +
        '<td data-label="所属系部"><input data-m="dept" data-i="' + i + '" value="' + esc(m.dept) + '"></td>' +
        '<td data-label="主要课程"><textarea data-m="core" data-i="' + i + '" rows="2">' + esc(m.core) + '</textarea></td>' +
        '<td data-label="技能证书"><textarea data-m="cert" data-i="' + i + '" rows="2">' + esc(m.cert) + '</textarea></td>' +
        '<td data-label="适合考生"><textarea data-m="fit" data-i="' + i + '" rows="2">' + esc(m.fit) + '</textarea></td>' +
        '</tr>';
    }).join('');
  }

  $('#mq').addEventListener('input', function () { mq = this.value; fillMajors(); });

  $('#tbl-majors').addEventListener('input', function (e) {
    var el = e.target;
    if (!el.dataset.m) return;
    draft.majors[Number(el.dataset.i)][el.dataset.m] = el.value;
    save();
  });

  /* ---------- 清空草稿 ---------- */
  $('#ldrop').addEventListener('click', function () {
    if (!window.confirm('清空后，这个浏览器里的所有改动都会消失，回到初始内容。确定？')) return;
    try { localStorage.removeItem(KEY_DRAFT); localStorage.removeItem(KEY_AT); } catch (e) {}
    draft = { news: clone(D.news), notices: clone(D.notices), majors: clone(D.majors) };
    cur = null;
    $('#edit-empty').hidden = false;
    save();
    fillEditorList();
    toast('草稿已清空，回到初始内容');
  });

  /* ---------- 提示 ---------- */
  var tEl = null, tAct = null;
  function toast(msg, action) {
    if (!tEl) {
      tEl = document.createElement('div');
      tEl.className = 'toast';
      document.body.appendChild(tEl);
    }
    tEl.innerHTML = '<span>' + esc(msg) + '</span>';
    tAct = action || null;
    if (tAct) {
      var b = document.createElement('button');
      b.type = 'button';
      b.textContent = '撤销';
      b.addEventListener('click', function () {
        var f = tAct; tAct = null;
        tEl.classList.remove('show');
        if (f) f();
      });
      tEl.appendChild(b);
    }
    tEl.classList.add('show');
    clearTimeout(tEl._t);
    tEl._t = setTimeout(function () { tEl.classList.remove('show'); tAct = null; }, action ? 5000 : 2000);
  }
})();
