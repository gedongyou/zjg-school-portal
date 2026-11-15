# 江苏省张家港中等专业学校 · 门户网站（毕业设计作品）

信息工程系 2022 级毕业设计。选题：学校门户网站设计与实现（含后台管理）。
纯静态站点，不需要服务器与数据库，可以直接放在 GitHub Pages、或者任意静态托管上。

> 本站为毕业设计演示作品，不是学校官方站点。校名、校徽、地址与招生电话取自学校公开信息，
> 新闻与公告正文为依据官网标题与时间改写的演示文本，非官网原文。

## 目录结构

```
index.html              首页
about.html              学校概况
admission.html          招生就业
campus.html             校园生活
search.html             站内搜索
admin.html              内容后台
news/index.html         新闻中心（列表）
news/n01.html …         新闻详情（12 篇，构建生成）
notices/index.html      通知公告（列表）
notices/g01.html …      公告详情（8 篇，构建生成）
majors/index.html       专业设置（按系部分组）
majors/m01.html …       专业详情（18 个，构建生成）

src/                    页面模板（chrome.html 是全站骨架）
content/                内容数据（唯一数据源）
  news.json               12 条新闻
  notices.json            8 条公告
  majors.json             18 个专业
  build_content.py        生成上面两个 JSON 的脚本（含正文改写）
build.py                构建脚本：content/*.json + src/*.html → 47 个 html
assets/css/site.css     前台样式
assets/css/admin.css    后台样式
assets/js/site.js       前台交互（轮播、索引、专业对照、回顶）
assets/js/search.js     搜索页
assets/js/admin.js      后台
assets/js/index-data.js 全站索引（构建生成，勿手改）
assets/img/             校徽、二维码、实景照片
previews/               交付用截图
_archive/               早期版本（书/报纸版、校历版）与一次性脚本，不参与构建
```

## 怎么改内容

两条路，选一条。

**一、改源文件（推荐，改动可提交）**

1. 编辑 `content/news.json`、`content/notices.json` 或 `content/majors.json`
2. 运行 `python3 build.py`
3. 重新生成的页面会覆盖旧的 html

**二、用后台改**

1. 打开 `admin.html`，账号 `admin`，密码 `admin123`
2. 内容清单可直接搜标题/部门/日期，按新闻、公告或"有改动"筛选，按日期或标题排序
3. 点"新建文章"建稿，点"编辑"改稿，点"删除"删除（5 秒内可撤销）
4. 编辑台右侧可展开"前台预览"，按详情页样式实时排版，并显示字数与段数
5. 改完点"保存草稿"——草稿存在浏览器 localStorage，刷新不丢，换电脑就没了
6. 后台没有导出功能，草稿只用于预览效果；正式发布仍需按第一种方式写回 JSON

> 后台是纯前端演示。静态站点没有服务端，登录只是把 `localStorage.zhjg_admin_auth` 置为 `1`，
> 不具备真实的权限控制。这一点在答辩时需要说明。

## 本地预览

```bash
cd portal2
python3 -m http.server 8091 --bind 0.0.0.0
```

然后访问 `http://<本机 IP>:8091/`。构建后的站点是纯静态文件，直接双击 `index.html` 也能看，
但 `fetch` 与相对路径在 `file://` 下会有差异，建议起本地服务。

## 与常见"学校官网模板"的不同之处

1. **专业对照**（首页）：勾选最多 3 个专业并排比较五个字段，其中"适合考生"一列是写给考生自己看的。
2. **系部筛选是真筛**：点系部只留该系的专业，职教高考部会显示"不设固定专业"的说明空态。
3. **站内索引**：`Ctrl/Cmd+K` 或点页眉"检"，输入即过滤，索引来自构建时生成的 `index-data.js`，
   不是前端遍历 DOM，所以内页也能搜到全站内容。
4. **构建式内容管理**：47 个页面由 `content/*.json` 生成，新闻/公告/专业改一处，列表页、
   详情页、搜索索引、首页卡片同时变。这是"含后台管理"这一命题的落点。

## 已知限制

- 无服务端，后台无真实鉴权，草稿不落盘到 JSON（见上）
- 后台的新建/删除只作用于本地草稿，不会生成或删除 `content/*.json` 里的条目
- 站内搜索是前端字符串匹配，不做分词，输入"云"能命中"云计算技术应用"，
  但输入"计应"这类简称搜不到
- 新闻配图复用同一批 13 张实景照片，与具体新闻内容不严格对应
- 分数线未列具体分值，因每年公布口径不同，避免写死
