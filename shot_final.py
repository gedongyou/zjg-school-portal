"""shot_final.py — 交付图：内页 + 后台，桌面与手机"""
import asyncio, os, subprocess, sys, time
from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "previews")
PORT = int(os.environ.get("PORT", "8171"))
os.makedirs(OUT, exist_ok=True)

srv = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1",
                        "--directory", ROOT], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1.2)
BASE = "http://127.0.0.1:%d" % PORT


async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1.5, locale="zh-CN")
        page = await ctx.new_page()
        page.on("pageerror", lambda e: errors.append("pageerror: %s" % e))
        page.on("console", lambda m: errors.append("console: " + m.text) if m.type == "error" else None)

        for path, name, full in [
            ("/news/index.html", "内页-01-新闻中心", True),
            ("/news/n01.html", "内页-02-新闻详情", True),
            ("/majors/index.html", "内页-03-专业设置", True),
            ("/majors/m13.html", "内页-04-专业详情", True),
            ("/admission.html", "内页-05-招生就业", True),
            ("/about.html", "内页-06-学校概况", True),
            ("/campus.html", "内页-07-校园生活", True),
        ]:
            await page.goto(BASE + path)
            await page.wait_for_timeout(350)
            await page.screenshot(path=os.path.join(OUT, name + ".jpg"), quality=80, full_page=full, type="jpeg")

        await page.goto(BASE + "/search.html?q=%E4%B8%93%E4%B8%9A")
        await page.wait_for_timeout(500)
        n = await page.eval_on_selector_all("[data-srch-list] li", "e=>e.length")
        print("search '专业' ->", n)
        await page.screenshot(path=os.path.join(OUT, "内页-08-站内搜索.jpg"), quality=80, type="jpeg")

        # 后台
        await page.goto(BASE + "/admin.html")
        await page.wait_for_timeout(300)
        await page.screenshot(path=os.path.join(OUT, "后台-01-登录.jpg"), quality=80, type="jpeg")
        await page.fill("#login-form input[name=u]", "admin")
        await page.fill("#login-form input[name=p]", "admin123")
        await page.click("#login-form button[type=submit]")
        await page.wait_for_timeout(500)
        await page.screenshot(path=os.path.join(OUT, "后台-02-内容清单.jpg"), quality=80, type="jpeg")
        await page.click("[data-tab=edit]")
        await page.wait_for_timeout(200)
        await page.click("#editor-list button")
        await page.wait_for_timeout(300)
        await page.screenshot(path=os.path.join(OUT, "后台-03-文章编辑台.jpg"), quality=80, type="jpeg")
        await page.click("[data-tab=majors]")
        await page.wait_for_timeout(300)
        await page.screenshot(path=os.path.join(OUT, "后台-04-专业信息.jpg"), quality=80, type="jpeg")

        # 手机
        m = await b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2,
                                is_mobile=True, has_touch=True, locale="zh-CN")
        mp = await m.new_page()
        mp.on("pageerror", lambda e: errors.append("m-pageerror: %s" % e))
        for path, name in [("/index.html", "手机-01-首页"), ("/news/index.html", "手机-02-新闻中心"),
                           ("/majors/m13.html", "手机-03-专业详情"), ("/admission.html", "手机-04-招生")]:
            await mp.goto(BASE + path)
            await mp.wait_for_timeout(400)
            sw = await mp.evaluate("()=>document.documentElement.scrollWidth")
            print(name, "scrollWidth", sw)
            await mp.screenshot(path=os.path.join(OUT, name + ".jpg"), quality=80, full_page=True, type="jpeg")

        await mp.goto(BASE + "/admin.html")
        await mp.fill("#login-form input[name=u]", "admin")
        await mp.fill("#login-form input[name=p]", "admin123")
        await mp.click("#login-form button[type=submit]")
        await mp.wait_for_timeout(500)
        await mp.screenshot(path=os.path.join(OUT, "手机-05-后台清单.jpg"), quality=80, type="jpeg")
        await mp.click("[data-tab=majors]")
        await mp.wait_for_timeout(300)
        await mp.screenshot(path=os.path.join(OUT, "手机-06-后台专业.jpg"), quality=80, type="jpeg")

        await b.close()
    print("errors:", errors)

asyncio.run(main())
srv.terminate()
