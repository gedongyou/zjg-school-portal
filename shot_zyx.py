"""shot_zyx.py — 为毕业设计三件套重新出图（桌面 1600 宽 + 手机 390 宽）"""
import asyncio, os, subprocess, sys, time
from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = "/root/DSH_WorkSpace/完成zyx/图"
PORT = int(os.environ.get("PORT", "8181"))
os.makedirs(OUT, exist_ok=True)

srv = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1",
                        "--directory", ROOT], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1.2)
BASE = "http://127.0.0.1:%d" % PORT

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={"width": 1600, "height": 950},
                                  device_scale_factor=1.25, locale="zh-CN")
        page = await ctx.new_page()
        page.on("pageerror", lambda e: errors.append("pageerror: %s" % e))

        async def shot(path, name, full=False, wait=400):
            await page.goto(BASE + path)
            await page.wait_for_timeout(wait)
            await page.screenshot(path=os.path.join(OUT, name + ".jpg"),
                                  quality=86, full_page=full, type="jpeg")
            print("  ", name)

        # 桌面逐页
        await shot("/index.html", "01-首页首屏")
        await shot("/index.html", "01b-首页整页", full=True)
        await shot("/about.html", "02-学校概况")
        await shot("/news/index.html", "03-新闻中心")
        await shot("/news/n01.html", "04-新闻详情")
        await shot("/majors/index.html", "05-专业设置")
        await shot("/majors/m13.html", "06-专业详情-计算机网络技术")
        await shot("/admission.html", "07-招生就业")
        await shot("/campus.html", "08-校园生活")
        await shot("/search.html?q=%E4%BA%91%E8%AE%A1%E7%AE%97", "09-站内搜索")
        await shot("/notices/index.html", "10-通知公告")

        # 专业对照（勾三个）
        await page.goto(BASE + "/index.html")
        await page.wait_for_timeout(400)
        boxes = page.locator(".mj__pick input")
        for i in (12, 13, 14):
            await boxes.nth(i).click()
            await page.wait_for_timeout(150)
        await page.locator("[data-cmp-go]").click()
        await page.wait_for_timeout(500)
        await page.screenshot(path=os.path.join(OUT, "11-专业对照表.jpg"), quality=86, type="jpeg")
        print("   11-专业对照表")
        await page.keyboard.press("Escape")

        # 站内索引弹层
        await page.locator("[data-finder]").first.click()
        await page.wait_for_timeout(300)
        await page.fill("[data-finder-input]", "实训")
        await page.wait_for_timeout(400)
        await page.screenshot(path=os.path.join(OUT, "12-站内索引.jpg"), quality=86, type="jpeg")
        print("   12-站内索引")
        await page.keyboard.press("Escape")

        # 后台
        await page.goto(BASE + "/admin.html")
        await page.wait_for_timeout(400)
        await page.screenshot(path=os.path.join(OUT, "13-后台登录.jpg"), quality=86, type="jpeg")
        print("   13-后台登录")
        await page.fill("#login-form input[name=u]", "admin")
        await page.fill("#login-form input[name=p]", "admin123")
        await page.click("#login-form button[type=submit]")
        await page.wait_for_timeout(700)
        await page.screenshot(path=os.path.join(OUT, "14-后台内容清单.jpg"), quality=86, type="jpeg")
        print("   14-后台内容清单")
        await page.click("[data-tab=edit]")
        await page.wait_for_timeout(300)
        await page.click("#editor-list button")
        await page.wait_for_timeout(400)
        await page.screenshot(path=os.path.join(OUT, "15-后台文章编辑台.jpg"), quality=86, type="jpeg")
        print("   15-后台文章编辑台")
        await page.click("[data-tab=majors]")
        await page.wait_for_timeout(400)
        await page.screenshot(path=os.path.join(OUT, "16-后台专业信息.jpg"), quality=86, type="jpeg")
        print("   16-后台专业信息")
        await ctx.close()

        # 手机
        m = await b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2,
                                is_mobile=True, has_touch=True, locale="zh-CN")
        mp = await m.new_page()
        mp.on("pageerror", lambda e: errors.append("m pageerror: %s" % e))
        async def mshot(path, name, full=False, wait=450):
            await mp.goto(BASE + path)
            await mp.wait_for_timeout(wait)
            await mp.screenshot(path=os.path.join(OUT, name + ".jpg"), quality=86,
                                full_page=full, type="jpeg")
            sw = await mp.evaluate("()=>document.documentElement.scrollWidth")
            print("  ", name, "scrollWidth", sw)
        await mshot("/index.html", "20-手机首页首屏")
        await mshot("/majors/m13.html", "21-手机专业详情")
        await mshot("/admission.html", "22-手机招生")
        await mshot("/news/index.html", "23-手机新闻中心")
        await mshot("/index.html", "24-手机首页整页", full=True)
        await m.close()
        await b.close()
    print("errors:", errors)

asyncio.run(main())
srv.terminate()
