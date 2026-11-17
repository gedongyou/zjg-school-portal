#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build.py — 把 src/*.html 片段与 content/*.json 组装成静态站点。

为什么用构建而不是纯手写：新闻详情、专业详情页面数量多且内容重复，
手写会产生大量复制粘贴的模板标记，改一处要改十几处。
构建把"版式"和"内容"分开，内容只在 content/*.json 里维护。

用法：python3 build.py
产物：index.html、news/index.html、news/<id>.html、majors/index.html、
      majors/<id>.html、notices/index.html、notices/<id>.html、search.html
"""
import json, os, re, shutil, html
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")
CONTENT = os.path.join(HERE, "content")

def asset_v():
    """静态资源版本号：取 css/js 的最新修改时间，用于给 <link>/<script> 加 ?v=，
    避免改了样式用户浏览器还拿旧缓存（这是之前"改了没生效"的直接原因）。"""
    latest = 0
    for root, _dirs, files in os.walk(HERE):
        if "_archive" in root or "previews" in root or "shot" in root:
            continue
        for f in files:
            if f.endswith((".css", ".js")):
                latest = max(latest, int(os.path.getmtime(os.path.join(root, f))))
    return str(latest)

def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()

def write(p, s):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(s)

def esc(s):
    return html.escape(s, quote=True)

def jread(name):
    return json.loads(read(os.path.join(CONTENT, name)))

# ---------------------------------------------------------------- 站点数据

NAV = [
    ("首页", "index.html"),
    ("学校概况", "about.html"),
    ("新闻中心", "news/index.html"),
    ("通知公告", "notices/index.html"),
    ("招生就业", "admission.html"),
    ("专业设置", "majors/index.html"),
    ("校园生活", "campus.html"),
]

DEPT_ORDER = ["智能控制系", "机械与汽车工程系", "信息工程系", "经济贸易系", "能源材料系"]

DEPT_DESC = {
    "智能控制系": "面向智能制造与新能源装备，实训以 PLC 控制、工业机器人与自动化产线调试为主。",
    "机械与汽车工程系": "以数控加工、模具设计与汽车检测为两条主线，拥有数控与汽修两个实训中心。",
    "信息工程系": "覆盖计算机应用、网络、云计算与人工智能，承担全校信息技术类公共课程。",
    "经济贸易系": "以会计、国际商务与跨境电子商务为主，建有跨境电商实训基地与模拟银行。",
    "能源材料系": "面向化工、新材料与服装产业，建有化工虚拟仿真实训基地与分析检验实训室。",
    "职教高考部": "不设固定专业，按语文、数学、英语加专业综合组织教学，学生三年后参加江苏省职教高考。",
}

def cn_date(d):
    y, m, dd = d.split("-")
    return "%s 年 %d 月 %d 日" % (y, int(m), int(dd))

def short_date(d):
    return d[5:]

# ---------------------------------------------------------------- 页面骨架

def chrome(title, desc, active, body, depth=0, extra_head=""):
    """depth=1 表示产物位于子目录（news/、majors/ 等），静态资源要回退一级。"""
    up = "../" if depth else ""
    nav = []
    for label, href in NAV:
        on = ' class="on"' if href.split("/")[0] == active else ""
        nav.append('<a%s href="%s%s">%s</a>' % (on, up, href, label))
    tpl = read(os.path.join(SRC, "chrome.html"))
    return (tpl
            .replace("{{TITLE}}", esc(title))
            .replace("{{DESC}}", esc(desc))
            .replace("{{UP}}", up)
            .replace("{{NAV}}", "\n    ".join(nav))
            .replace("{{ACTIVE}}", active)
            .replace("{{BODY}}", body)
            .replace("{{EXTRA_HEAD}}", extra_head)
            .replace("{{TODAY}}", cn_date(date.today().isoformat()))
            .replace("{{V}}", asset_v()))

def breadcrumb(items, up=""):
    """items = [(label, href|None), ...]"""
    out = ['<nav class="crumb" aria-label="当前位置"><div class="wrap"><a href="%sindex.html">首页</a>' % up]
    for label, href in items:
        out.append('<span aria-hidden="true">›</span>')
        if href:
            out.append('<a href="%s">%s</a>' % (href, esc(label)))
        else:
            out.append('<span aria-current="page">%s</span>' % esc(label))
    out.append("</div></nav>")
    return "".join(out)

# ---------------------------------------------------------------- 首页

def build_home():
    news = jread("news.json")
    notices = jread("notices.json")
    majors = jread("majors.json")

    rows = []
    for i, n in enumerate(news[:6]):
        rows.append('<li><a href="news/%s.html"><span class="tt">%s</span><span class="dt">%s</span></a></li>'
                    % (n["id"], esc(n["title"]), short_date(n["date"])))
    news_a = "\n".join(rows)
    rows = []
    for n in news[6:12]:
        rows.append('<li><a href="news/%s.html"><span class="tt">%s</span><span class="dt">%s</span></a></li>'
                    % (n["id"], esc(n["title"]), short_date(n["date"])))
    news_b = "\n".join(rows)

    rows = []
    for n in notices[:6]:
        rows.append('<li><a href="notices/%s.html"><span class="tt">%s</span><span class="dt">%s</span></a></li>'
                    % (n["id"], esc(n["title"]), short_date(n["date"])))
    notice_list = "\n".join(rows)

    lead = news[0]
    rows = []
    for n in news[1:5]:
        rows.append('<li><a href="news/%s.html"><span class="tt">%s</span><span class="dt">%s</span></a></li>'
                    % (n["id"], esc(n["title"]), short_date(n["date"])))
    news_lead_list = "\n".join(rows)

    rows = []
    for dept in DEPT_ORDER:
        items = [m for m in majors if m["dept"] == dept]
        links = "、".join(
            '<a href="majors/%s.html">%s</a>' % (m["id"], esc(m["name"])) for m in items)
        rows.append(
            '<div class="dept-row">\n'
            '        <div class="dept-row__h"><a href="majors/index.html#%s">%s</a>'
            '<small>%d 个专业</small></div>\n'
            '        <p class="dept-row__b">%s</p>\n'
            '      </div>' % (esc(dept), esc(dept), len(items), links))
    dept_index = '\n      '.join(rows)

    # 首页大图：只放一张校园全景，原图 1920x900 不裁切
    hero_html = (
        '<img src="assets/img/photo/banner.jpg" width="1920" height="400" '
        'alt="江苏省张家港中等专业学校校门与校园全景">'
    )

    body = read(os.path.join(SRC, "home.html"))
    body = (body
            .replace("{{HERO}}", hero_html)
            .replace("{{NOTICES}}", notice_list)
            .replace("{{NEWS_A}}", news_a)
            .replace("{{NEWS_B}}", news_b)
            .replace("{{LEAD_TITLE}}", esc(lead["title"]))
            .replace("{{LEAD_BODY}}", esc(lead["body"][0]))
            .replace("{{LEAD_META}}", "%s　%s" % (esc(lead["src"]), cn_date(lead["date"])))
            .replace("{{LEAD_ID}}", lead["id"])
            .replace("{{NEWS_LEAD_LIST}}", news_lead_list)
            .replace("{{DEPT_INDEX}}", dept_index))

    write(os.path.join(HERE, "index.html"),
          chrome("江苏省张家港中等专业学校",
                 "江苏省张家港中等专业学校（江苏联合职业技术学院张家港分院）首页，含学校概况、通知公告、校园新闻、招生就业、专业设置、校园生活。",
                 "index.html", body))

# ---------------------------------------------------------------- 新闻

def build_news():
    news = jread("news.json")
    cats = []
    for n in news:
        if n["cat"] not in cats:
            cats.append(n["cat"])

    # 列表页
    blocks = []
    for c in cats:
        rows = []
        for n in [x for x in news if x["cat"] == c]:
            rows.append(
                '<li><a href="%s.html"><span class="dt">%s</span><span class="tt">%s</span></a></li>'
                % (n["id"], n["date"], esc(n["title"])))
        blocks.append(
            '<section class="blk">\n        <h2 class="blk__t">%s</h2>\n        <ul class="list list--date">\n          %s\n        </ul>\n      </section>'
            % (esc(c), "\n          ".join(rows)))

    body = ('<div class="wrap page">\n'
            '<div class="page__hd"><h1>新闻中心</h1>'
            '<p>校内新闻与部门动态，按发布时间排列</p></div>\n'
            '<div class="page__body">\n      ' + "\n      ".join(blocks) + '\n      </div>\n'
            '</div>')
    html_out = breadcrumb([("新闻中心", None)], "../") + body
    write(os.path.join(HERE, "news", "index.html"),
          chrome("新闻中心 - 江苏省张家港中等专业学校",
                 "江苏省张家港中等专业学校校园新闻与部门新闻列表。",
                 "news", html_out, depth=1))

    # 详情页
    for i, n in enumerate(news):
        prev_n = news[i - 1] if i > 0 else None
        next_n = news[i + 1] if i + 1 < len(news) else None
        paras = "\n          ".join("<p>%s</p>" % esc(p) for p in n["body"])
        nav = []
        if prev_n:
            nav.append('<a href="%s.html"><span>上一篇</span>%s</a>' % (prev_n["id"], esc(prev_n["title"])))
        else:
            nav.append('<span><span>上一篇</span>没有了</span>')
        if next_n:
            nav.append('<a href="%s.html"><span>下一篇</span>%s</a>' % (next_n["id"], esc(next_n["title"])))
        else:
            nav.append('<span><span>下一篇</span>没有了</span>')

        body = ('<div class="wrap page">\n'
                '  <article class="art">\n'
                '    <h1 class="art__t">%s</h1>\n'
                '    <div class="art__meta"><span>%s</span><span>%s</span><span>%s</span></div>\n'
                '    <figure class="art__fig"><img src="../assets/img/photo/news-%d.jpg" alt=""><figcaption>%s</figcaption></figure>\n'
                '    <div class="art__body">\n          %s\n    </div>\n'
                '    <div class="art__note">本文为毕业设计演示文本，依据学校官网公开报道的标题与时间改写，非官网原文。</div>\n'
                '    <nav class="art__nav" aria-label="上下篇">\n      %s\n    </nav>\n'
                '  </article>\n'
                '</div>') % (esc(n["title"]), esc(n["cat"]), esc(n["src"]), cn_date(n["date"]),
                             (i % 13) + 1, esc(n["title"]), paras, "\n      ".join(nav))
        html_out = breadcrumb([("新闻中心", "index.html"), (n["cat"], None), (n["title"], None)], "../") + body
        write(os.path.join(HERE, "news", "%s.html" % n["id"]),
              chrome("%s - 新闻中心 - 江苏省张家港中等专业学校" % n["title"], n["title"],
                     "news", html_out, depth=1))

# ---------------------------------------------------------------- 通知公告

def build_notices():
    notices = jread("notices.json")
    cats = []
    for n in notices:
        if n["cat"] not in cats:
            cats.append(n["cat"])

    blocks = []
    for c in cats:
        rows = []
        for n in [x for x in notices if x["cat"] == c]:
            rows.append(
                '<li><a href="%s.html"><span class="dt">%s</span><span class="tt">%s</span></a></li>'
                % (n["id"], n["date"], esc(n["title"])))
        blocks.append(
            '<section class="blk">\n        <h2 class="blk__t">%s</h2>\n        <ul class="list list--date">\n          %s\n        </ul>\n      </section>'
            % (esc(c), "\n          ".join(rows)))

    body = ('<div class="wrap page">\n'
            '<div class="page__hd"><h1>通知公告</h1>'
            '<p>教务处、总务处、人事处等部门发布的通知</p></div>\n'
            '<div class="page__body">\n      ' + "\n      ".join(blocks) + '\n      </div>\n'
            '</div>')
    html_out = breadcrumb([("通知公告", None)], "../") + body
    write(os.path.join(HERE, "notices", "index.html"),
          chrome("通知公告 - 江苏省张家港中等专业学校",
                 "江苏省张家港中等专业学校通知公告列表。",
                 "notices", html_out, depth=1))

    for i, n in enumerate(notices):
        prev_n = notices[i - 1] if i > 0 else None
        next_n = notices[i + 1] if i + 1 < len(notices) else None
        paras = "\n          ".join("<p>%s</p>" % esc(p) for p in n["body"])
        nav = []
        if prev_n:
            nav.append('<a href="%s.html"><span>上一条</span>%s</a>' % (prev_n["id"], esc(prev_n["title"])))
        else:
            nav.append('<span><span>上一条</span>没有了</span>')
        if next_n:
            nav.append('<a href="%s.html"><span>下一条</span>%s</a>' % (next_n["id"], esc(next_n["title"])))
        else:
            nav.append('<span><span>下一条</span>没有了</span>')

        body = ('<div class="wrap page">\n'
                '  <article class="art art--notice">\n'
                '    <h1 class="art__t">%s</h1>\n'
                '    <div class="art__meta"><span>%s</span><span>%s</span><span>%s</span></div>\n'
                '    <div class="art__body">\n          %s\n    </div>\n'
                '    <div class="art__note">本文为毕业设计演示文本，依据学校官网公开公告的标题与时间改写，非官网原文。</div>\n'
                '    <nav class="art__nav" aria-label="上下条">\n      %s\n    </nav>\n'
                '  </article>\n'
                '</div>') % (esc(n["title"]), esc(n["cat"]), esc(n["src"]), cn_date(n["date"]), paras,
                             "\n      ".join(nav))
        html_out = breadcrumb([("通知公告", "index.html"), (n["cat"], None), (n["title"], None)], "../") + body
        write(os.path.join(HERE, "notices", "%s.html" % n["id"]),
              chrome("%s - 通知公告 - 江苏省张家港中等专业学校" % n["title"], n["title"],
                     "notices", html_out, depth=1))

# ---------------------------------------------------------------- 专业

DEPT_LAB = {
    "智能控制系": "系里的实训以电气控制和机器人为主：PLC 实训台、液压气动实训台、工业机器人工作站，还有一条小型自动化产线用来练整线调试。",
    "机械与汽车工程系": "数控加工中心、CAD/CAM 机房、汽车整车与总成实训区；工业设计方向另有产品造型与三维建模的工作室。",
    "信息工程系": "网络实训室、云计算实训中心、综合布线与组网实训台；计算机应用方向另有多媒体与办公自动化的机房。",
    "经济贸易系": "会计手工与电算化实训室、跨境电商实训基地、国际商务谈判与单证实训室。",
    "能源材料系": "化工单元操作实训装置、分析检测实验室；服装设计与工艺方向有制版与缝制车间。",
}

DEPT_OUT = {
    "智能控制系": "毕业生多去本地的装备制造、汽车零部件和电力配套企业，做设备调试、电气维修、产线运维；也有去机器人集成商做现场支持的。",
    "机械与汽车工程系": "主要去向是机械加工、模具、汽车维修与整车厂。岗位一般从数控操作起步，做几年后转向编程、工艺或班组管理。",
    "信息工程系": "去企业做网络运维、桌面运维、云资源管理，或者进软件与信息服务公司；也有人自己接小程序开发、做短视频运营。",
    "经济贸易系": "去外贸公司、货代、电商企业做单证、跟单、店铺运营与跨境直播；会计方向多进中小企业做账务与出纳。",
    "能源材料系": "化工与新材料企业是主要去向，岗位有工艺操作、分析检验、设备维护；服装方向进制版、样衣与生产管理。",
}

CMP_BAR = """
<div class="cmp" data-cmp-bar hidden>
  <div class="cmp__in">
    <span class="cmp__t">已选 <b data-cmp-n>0</b> 个专业</span>
    <div class="cmp__chips" data-cmp-chips></div>
    <button class="cmp__clear" type="button" data-cmp-clear>清空</button>
    <button class="cmp__go" type="button" data-cmp-go disabled>并排对照</button>
  </div>
</div>
"""

CMP_MODAL = """
<div class="cmp-modal" data-cmp-modal role="dialog" aria-modal="true" aria-labelledby="cmp-h" hidden>
  <div class="cmp-modal__mask" data-cmp-close></div>
  <div class="cmp-modal__box">
    <div class="cmp-modal__hd">
      <h2 id="cmp-h">专业对照</h2>
      <button type="button" data-cmp-close aria-label="关闭">×</button>
    </div>
    <div data-cmp-body></div>
    <div class="cmp-modal__ft">
      培养方向与证书依据学校现行专业教学标准整理，2026 年招生专业与计划以省教育厅下达文件及学校招生简章为准。
    </div>
  </div>
</div>
"""


def build_majors():
    majors = jread("majors.json")

    # 列表页：按系部分组，与首页的卡片网格不同，用表格式索引
    blocks = []
    for dept in DEPT_ORDER:
        items = [m for m in majors if m["dept"] == dept]
        rows = []
        for m in items:
            rows.append(
                '<li data-mj data-name="%(name)s" data-dept="%(dept)s" data-core="%(core)s" '
                'data-cert="%(cert)s" data-degree="五年制高职（大专）" data-fit="%(fit)s">\n'
                '            <a href="%(id)s.html"><span class="nm">%(name)s</span>'
                '<span class="ds">%(core)s</span><span class="go">查看 ›</span></a>\n'
                '            <label class="mj__pick"><input type="checkbox" value="%(name)s" '
                'aria-label="选择%(name)s加入对比"><span>对比</span></label>\n'
                '          </li>' % {
                    "id": m["id"], "name": esc(m["name"]), "dept": esc(m["dept"]),
                    "core": esc(m["core"]), "cert": esc(m["cert"]), "fit": esc(m["fit"]),
                })
        blocks.append(
            '<section class="blk" id="%s">\n'
            '        <h2 class="blk__t">%s<small>%d 个专业</small></h2>\n'
            '        <p class="blk__d">%s</p>\n'
            '        <ul class="mj-list mj-list--cmp">\n          %s\n        </ul>\n'
            '      </section>'
            % (esc(dept), esc(dept), len(items), esc(DEPT_DESC[dept]), "\n          ".join(rows)))
    blocks.append(
        '<section class="blk" id="职教高考部">\n'
        '        <h2 class="blk__t">职教高考部<small>不设固定专业</small></h2>\n'
        '        <p class="blk__d">%s</p>\n'
        '      </section>' % esc(DEPT_DESC["职教高考部"]))

    body = ('<div class="wrap page">\n'
            '<div class="page__hd"><h1>专业设置</h1>'
            '<p>五个系，共 18 个五年一贯制专业　·　勾选 2—3 个可并排对照</p></div>\n'
            '<div class="page__body">\n      ' + "\n      ".join(blocks) + '\n      </div>\n'
            '</div>' + CMP_BAR + CMP_MODAL)
    html_out = breadcrumb([("专业设置", None)], "../") + body
    write(os.path.join(HERE, "majors", "index.html"),
          chrome("专业设置 - 江苏省张家港中等专业学校",
                 "江苏省张家港中等专业学校五个系 18 个五年一贯制专业介绍。",
                 "majors", html_out, depth=1))

    # 详情页
    for i, m in enumerate(majors):
        prev_m = majors[i - 1] if i > 0 else None
        next_m = majors[i + 1] if i + 1 < len(majors) else None
        sibs = [x for x in majors if x["dept"] == m["dept"] and x["id"] != m["id"]]
        sib_html = "\n        ".join(
            '<li><a href="%s.html">%s</a></li>' % (s["id"], esc(s["name"])) for s in sibs)

        rows = [
            ("所属系部", m["dept"]),
            ("学制与学历", "五年一贯制高职（大专）"),
            ("主要课程", m["core"]),
            ("技能证书", m["cert"]),
            ("适合考生", m["fit"]),
        ]
        dl = "\n        ".join('<div><dt>%s</dt><dd>%s</dd></div>' % (esc(k), esc(v)) for k, v in rows)

        nav = []
        if prev_m:
            nav.append('<a href="%s.html"><span>上一个专业</span>%s</a>' % (prev_m["id"], esc(prev_m["name"])))
        else:
            nav.append('<span><span>上一个专业</span>没有了</span>')
        if next_m:
            nav.append('<a href="%s.html"><span>下一个专业</span>%s</a>' % (next_m["id"], esc(next_m["name"])))
        else:
            nav.append('<span><span>下一个专业</span>没有了</span>')

        body = ('<div class="wrap page">\n'
                '  <article class="art art--major">\n'
                '    <div class="art__meta"><span>%s</span><span>五年一贯制</span></div>\n'
                '    <h1 class="art__t">%s</h1>\n'
                '    <dl class="kv">\n        %s\n    </dl>\n'
                '    <div class="art__body">\n'
                '      <p><b>这五年怎么过。</b>前两年以文化课与专业基础课为主，第三、四年进入专业课与实训，第五年安排顶岗实习，同时可以报名参加专转本考试。实训安排随系部教学计划调整，具体以每学期的课表为准。</p>\n'
                '      <p><b>在哪儿练。</b>%s</p>\n'
                '      <p><b>毕业去哪儿。</b>%s想继续读本科的，在第五年参加江苏省普通高校专转本考试，录取后进本科院校三年级。</p>\n'
                '      <p><b>还想再问点什么。</b>可以打招生电话 0512-58269608 问课程安排，也可以到系部实训室看一看。首页的“专业对照”能把几个专业并排放在一起，比单看一页更容易分出差别。</p>\n'
                '    </div>\n'
                '    <div class="art__note">培养方向与证书依据学校现行专业教学标准整理；2026 年招生专业与计划以省教育厅下达文件及学校招生简章为准。</div>\n'
                '    <section class="sib">\n'
                '      <h2>%s的其他专业</h2>\n'
                '      <ul>\n        %s\n      </ul>\n'
                '    </section>\n'
                '    <nav class="art__nav" aria-label="上下专业">\n      %s\n    </nav>\n'
                '  </article>\n'
                '</div>') % (esc(m["dept"]), esc(m["name"]), dl,
                             esc(DEPT_LAB.get(m["dept"], "实训安排以系部教学计划为准。")),
                             esc(DEPT_OUT.get(m["dept"], "毕业生以本地就业为主。")),
                             esc(m["dept"]), sib_html, "\n      ".join(nav))
        html_out = breadcrumb([("专业设置", "index.html"), (m["dept"], None), (m["name"], None)], "../") + body
        write(os.path.join(HERE, "majors", "%s.html" % m["id"]),
              chrome("%s - 专业设置 - 江苏省张家港中等专业学校" % m["name"],
                     "%s：%s" % (m["name"], m["core"]), "majors", html_out, depth=1))

# ---------------------------------------------------------------- 单页内页

PAGES = {
    "about": ("about.html", "学校概况",
              "江苏省张家港中等专业学校概况：办学历史、校区、系部与专业设置。"),
    "admission": ("admission.html", "招生就业",
                  "江苏省张家港中等专业学校 2026 年招生办学形式、专业与咨询方式。"),
    "campus": ("campus.html", "校园生活",
               "江苏省张家港中等专业学校校园环境、实训场所与就业活动。"),
}

def build_pages():
    for key, (fname, title, desc) in PAGES.items():
        src = os.path.join(SRC, "%s.html" % key)
        if not os.path.exists(src):
            continue
        body = read(src)
        body = body.replace("{{MAJOR_COUNT}}", str(len(jread("majors.json"))))
        html_out = breadcrumb([(title, None)]) + body
        write(os.path.join(HERE, fname), chrome("%s - 江苏省张家港中等专业学校" % title, desc, fname, html_out))

# ---------------------------------------------------------------- 搜索页

def build_search():
    news = jread("news.json")
    notices = jread("notices.json")
    majors = jread("majors.json")
    idx = []
    for m in majors:
        idx.append({"t": m["name"], "m": "专业 · " + m["dept"], "u": "majors/%s.html" % m["id"],
                    "k": m["name"] + " " + m["core"] + " " + m["cert"] + " " + m["dept"]})
    for n in news:
        idx.append({"t": n["title"], "m": "新闻 · " + n["date"], "u": "news/%s.html" % n["id"],
                    "k": n["title"] + " " + n["cat"] + " " + n["src"] + " " + " ".join(n["body"])})
    for n in notices:
        idx.append({"t": n["title"], "m": "公告 · " + n["date"], "u": "notices/%s.html" % n["id"],
                    "k": n["title"] + " " + n["cat"] + " " + n["src"] + " " + " ".join(n["body"])})
    for dept in DEPT_ORDER + ["职教高考部"]:
        idx.append({"t": dept, "m": "系部", "u": "majors/index.html#%s" % dept, "k": dept + " 系部 专业"})

    data = json.dumps(idx, ensure_ascii=False, separators=(",", ":"))
    # 全站共用一份索引：站内索引弹层与搜索页都读它，避免每个页面各抓一遍 DOM
    write(os.path.join(HERE, "assets", "js", "index-data.js"),
          "window.SITE_INDEX = %s;\n" % data)

    body = ('<div class="wrap page">\n'
            '<div class="page__hd"><h1>站内搜索</h1>'
            '<p>输入关键词，检索专业、新闻与公告</p></div>\n'
            '<form class="srch" role="search" data-srch>\n'
            '  <input type="search" name="q" placeholder="例如：云计算、招生、技能大赛" aria-label="搜索关键词" data-srch-input>\n'
            '  <button type="submit">搜索</button>\n'
            '</form>\n'
            '<div class="srch__tip" data-srch-tip></div>\n'
            '<ul class="srch__list" data-srch-list></ul>\n'
            '</div>')
    html_out = breadcrumb([("站内搜索", None)]) + body
    write(os.path.join(HERE, "search.html"),
          chrome("站内搜索 - 江苏省张家港中等专业学校", "站内搜索专业、新闻与公告。", "search", html_out,
                 extra_head='<script src="assets/js/index-data.js?v=%s"></script>\n<script src="assets/js/search.js?v=%s" defer></script>' % (asset_v(), asset_v())))

# ---------------------------------------------------------------- 后台

def build_admin():
    data = {
        "news": jread("news.json"),
        "notices": jread("notices.json"),
        "majors": jread("majors.json"),
    }
    admin = read(os.path.join(SRC, "admin.html"))
    admin = (admin
             .replace("{{V}}", asset_v())
             .replace("{{DATA}}", json.dumps(data, ensure_ascii=False, separators=(",", ":"))))
    write(os.path.join(HERE, "admin.html"), admin)

# ---------------------------------------------------------------- 主流程

def main():
    build_home()
    build_news()
    build_notices()
    build_majors()
    build_pages()
    build_search()
    build_admin()
    n = 1 + 1 + len(jread("news.json")) + 1 + len(jread("notices.json")) + 1 \
        + len(jread("majors.json")) + len(PAGES) + 1 + 1
    print("生成 %d 个页面" % n)

if __name__ == "__main__":
    main()
