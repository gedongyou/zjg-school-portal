"""shot_pages.py — 内页与后台截图 / 交互验证"""
import asyncio, os, subprocess, sys, time
from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "previews")
PORT = int(os.environ.get("PORT", "8137"))

os.makedirs(OUT, exist_ok=True)

srv = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1",
                        "--directory", ROOT], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1.2)
BASE = "http://127.0.0.1:%d" % PORT


async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1.5,
                                  locale="zh-CN")
        page = await ctx.new_page()
        page.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append("pageerror: %s" % e))

        # ---------- 新闻列表 ----------
        await page.goto(BASE + "/news/index.html")
        await page.wait_for_timeout(400)
        await page.screenshot(path=os.path.join(OUT, "内页-01-新闻列表.jpg"), quality=82,
                              full_page=True, type="jpeg")

        # ---------- 新闻详情 ----------
        await page.goto(BASE + "/news/n01.html")
        await page.wait_for_timeout(400)
        await page.screenshot(path=os.path.join(OUT, "内页-02-新闻详情.jpg"), quality=82,
                              full_page=True, type="jpeg")

        # ---------- 专业列表 ----------
        await page.goto(BASE + "/majors/index.html")
        await page.wait_for_timeout(400)
        await page.screenshot(path=os.path.join(OUT, "内页-03-专业列表.jpg"), quality=82,
                              full_page=True, type="jpeg")

        # ---------- 专业详情 ----------
        await page.goto(BASE + "/majors/m13.html")
        await page.wait_for_timeout(400)
        await page.screenshot(path=os.path.join(OUT, "内页-04-专业详情.jpg"), quality=82,
                              full_page=True, type="jpeg")

        # ---------- 招生 ----------
        await page.goto(BASE + "/admission.html")
        await page.wait_for_timeout(400)
        await page.screenshot(path=os.path.join(OUT, "内页-05-招生就业.jpg"), quality=82,
                              full_page=True, type="jpeg")

        # ---------- 搜索页 ----------
        await page.goto(BASE + "/search.html?q=%E4%BA%91")
        await page.wait_for_timeout(600)
        n = await page.eval_on_selector_all("[data-srch-list] li", "e=>e.length")
        print("search '云' results:", n)
        await page.screenshot(path=os.path.join(OUT, "内页-06-搜索结果.jpg"), quality=82,
                              full_page=False, type="jpeg")

        # ---------- 站内索引弹层（在详情页上，验证相对路径） ----------
        await page.goto(BASE + "/news/n01.html")
        await page.wait_for_timeout(300)
        await page.click("[data-finder]")
        await page.wait_for_timeout(300)
        await page.fill("[data-finder-input]", "专业")
        await page.wait_for_timeout(300)
        n2 = await page.eval_on_selector_all("[data-finder-list] li", "e=>e.length")
        href = await page.eval_on_selector("[data-finder-list] li a", "e=>e.getAttribute('href')")
        print("finder on subpage results:", n2, "first href:", href)
        await page.screenshot(path=os.path.join(OUT, "内页-07-索引弹层.jpg"), quality=82)

        # ---------- 后台 ----------
        await page.goto(BASE + "/admin.html")
        await page.wait_for_timeout(400)
        await page.screenshot(path=os.path.join(OUT, "后台-01-登录.jpg"), quality=82)

        await page.fill("#login-form input[name=u]", "admin")
        await page.fill("#login-form input[name=p]", "admin123")
        await page.click("#login-form button[type=submit]")
        await page.wait_for_timeout(600)
        await page.screenshot(path=os.path.join(OUT, "后台-02-内容清单.jpg"), quality=82, full_page=True)

        # 编辑台
        await page.click("[data-tab=edit]")
        await page.wait_for_timeout(300)
        await page.click("#editor-list button")
        await page.wait_for_timeout(300)
        await page.screenshot(path=os.path.join(OUT, "后台-03-编辑台.jpg"), quality=82)

        # 改一条标题并存草稿
        await page.fill("#edit-form input[name=title]", "测试标题：改动是否保存")
        await page.click("#edit-form button[type=submit]")
        await page.wait_for_timeout(400)
        saved = await page.evaluate("()=>JSON.parse(localStorage.getItem('zhjg_admin_draft')).news[0].title")
        print("draft saved title:", saved)

        # 专业
        await page.click("[data-tab=majors]")
        await page.wait_for_timeout(300)
        await page.screenshot(path=os.path.join(OUT, "后台-04-专业信息.jpg"), quality=82)

        # ---------- 手机端内页 ----------
        m = await b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2,
                                is_mobile=True, has_touch=True, locale="zh-CN")
        mp = await m.new_page()
        mp.on("pageerror", lambda e: errors.append("m-pageerror: %s" % e))
        for path, name in [("/news/index.html", "内页-08-手机-新闻列表"),
                           ("/majors/m13.html", "内页-09-手机-专业详情"),
                           ("/admin.html", "后台-07-手机")]:
            await mp.goto(BASE + path)
            await mp.wait_for_timeout(400)
            sw = await mp.evaluate("()=>document.documentElement.scrollWidth")
            print(name, "scrollWidth", sw)
            await mp.screenshot(path=os.path.join(OUT, name + ".jpg"), quality=82, full_page=True)

        # 后台手机端登录后的布局
        await mp.goto(BASE + "/admin.html")
        await mp.fill("#login-form input[name=u]", "admin")
        await mp.fill("#login-form input[name=p]", "admin123")
        await mp.click("#login-form button[type=submit]")
        await mp.wait_for_timeout(500)
        await mp.screenshot(path=os.path.join(OUT, "后台-08-手机-清单.jpg"), quality=82)
        await mp.click("[data-tab=majors]")
        await mp.wait_for_timeout(400)
        await mp.screenshot(path=os.path.join(OUT, "后台-09-手机-专业表.jpg"), quality=82)
        await mp.click("[data-tab=edit]")
        await mp.wait_for_timeout(300)
        await mp.click("#editor-list button")
        await mp.wait_for_timeout(300)
        await mp.screenshot(path=os.path.join(OUT, "后台-10-手机-编辑台.jpg"), quality=82)

        await b.close()

    print("errors:", errors)

asyncio.run(main())
srv.terminate()
