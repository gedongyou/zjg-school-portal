# -*- coding: utf-8 -*-
"""shot_docs.py — 为毕业设计三件套出图（桌面 1600x950 dsf1.25 / 手机 390x844 dsf2）"""
import asyncio, os, subprocess, sys, time
from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = "/root/DSH_WorkSpace/完成zyx/图"
PORT = int(os.environ.get("PORT", "8187"))
os.makedirs(OUT, exist_ok=True)

srv = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1",
                        "--directory", ROOT], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1.2)
BASE = "http://127.0.0.1:%d" % PORT
SECS = [("02-首页栏目区", "main .cols"),
        ("03-首页学校概况", "#about"),
        ("04-首页招生", "#admission"),
        ("05-首页专业", "#majors"),
        ("06-首页五心", "#wuxin"),
        ("07-首页校园与页脚", "#campus"),
        ("08-首页校园生活", "#campus")]

async def main():
    errors = []
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={"width": 1600, "height": 950},
                                  device_scale_factor=1.25, locale="zh-CN")
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errors.append("pageerror: %s" % e))
        await pg.goto(BASE + "/index.html"); await pg.wait_for_timeout(600)
        await pg.add_style_tag(content=".to-top{display:none!important}")
        await pg.screenshot(path=os.path.join(OUT, "01-首页首屏.jpg"), quality=86, type="jpeg")
        print("   01-首页首屏")
        for name, sel in SECS[:5]:
            el = pg.locator(sel).first
            box = await el.bounding_box(); sy = await pg.evaluate("()=>window.scrollY")
            await pg.screenshot(path=os.path.join(OUT, name + ".jpg"),
                                clip={"x": 0, "y": box["y"] + sy, "width": 1600, "height": box["height"]},
                                quality=86, type="jpeg", full_page=True)
            print("  ", name, int(box["height"]))
        # 校园 + 页脚（一整段）
        box = await pg.evaluate("""()=>{const a=document.querySelector('#campus').getBoundingClientRect();
            const z=document.querySelector('.foot').getBoundingClientRect();
            return {y:a.top+scrollY,h:z.bottom-a.top};}""")
        await pg.screenshot(path=os.path.join(OUT, "07-首页校园与页脚.jpg"),
                            clip={"x": 0, "y": box["y"], "width": 1600, "height": box["h"]},
                            quality=86, type="jpeg", full_page=True)
        print("   07-首页校园与页脚", int(box["h"]))
        await pg.screenshot(path=os.path.join(OUT, "01b-首页整页.jpg"), quality=80,
                            full_page=True, type="jpeg")

        async def shot(path, name, full=False, wait=450):
            await pg.goto(BASE + path); await pg.wait_for_timeout(wait)
            await pg.screenshot(path=os.path.join(OUT, name + ".jpg"), quality=86,
                                full_page=full, type="jpeg")
            print("  ", name)

        await shot("/majors/index.html", "08-首页校园生活")
        await shot("/about.html", "17-学校概况")
        await shot("/news/index.html", "12-新闻中心")
        await shot("/news/n01.html", "13-新闻详情")
        await shot("/majors/index.html", "14-专业设置")
        await shot("/majors/m13.html", "15-专业详情")
        await shot("/admission.html", "16-招生就业")
        await shot("/campus.html", "18-校园生活")
        await shot("/notices/index.html", "19-通知公告")
        await shot("/search.html?q=%E4%BA%91%E8%AE%A1%E7%AE%97", "11-站内搜索页")

        # 专业对照（在专业设置页勾三个）
        await pg.goto(BASE + "/majors/index.html"); await pg.wait_for_timeout(500)
        boxes = pg.locator(".mj__pick input")
        for i in (10, 11, 12):
            await boxes.nth(i).click(); await pg.wait_for_timeout(150)
        await pg.locator("[data-cmp-go]").click(); await pg.wait_for_timeout(500)
        await pg.screenshot(path=os.path.join(OUT, "09-专业对照表.jpg"), quality=86, type="jpeg")
        print("   09-专业对照表")
        await pg.keyboard.press("Escape")

        # 站内索引
        await pg.goto(BASE + "/index.html"); await pg.wait_for_timeout(500)
        await pg.locator("[data-finder]").first.click(); await pg.wait_for_timeout(300)
        await pg.fill("[data-finder-input]", "实训"); await pg.wait_for_timeout(400)
        await pg.screenshot(path=os.path.join(OUT, "10-站内索引.jpg"), quality=86, type="jpeg")
        print("   10-站内索引")
        await pg.keyboard.press("Escape")

        # 后台
        await pg.goto(BASE + "/admin.html"); await pg.wait_for_timeout(400)
        await pg.screenshot(path=os.path.join(OUT, "20-后台登录.jpg"), quality=86, type="jpeg")
        await pg.fill("#login-form input[name=u]", "admin")
        await pg.fill("#login-form input[name=p]", "admin123")
        await pg.click("#login-form button[type=submit]"); await pg.wait_for_timeout(700)
        await pg.screenshot(path=os.path.join(OUT, "21-后台内容清单.jpg"), quality=86, type="jpeg")
        await pg.click("[data-tab=edit]"); await pg.wait_for_timeout(300)
        await pg.click("#editor-list button"); await pg.wait_for_timeout(400)
        await pg.screenshot(path=os.path.join(OUT, "22-后台文章编辑台.jpg"), quality=86, type="jpeg")
        await pg.click("[data-tab=majors]"); await pg.wait_for_timeout(400)
        await pg.screenshot(path=os.path.join(OUT, "23-后台专业信息.jpg"), quality=86, type="jpeg")
        print("   20-23 后台")
        await ctx.close()

        m = await b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2,
                                is_mobile=True, has_touch=True, locale="zh-CN")
        mp = await m.new_page()
        mp.on("pageerror", lambda e: errors.append("m pageerror: %s" % e))
        for path, name, full in [("/index.html", "24-手机首页", False),
                                 ("/majors/m13.html", "25-手机专业详情", False),
                                 ("/admission.html", "26-手机招生", False),
                                 ("/news/index.html", "27-手机新闻中心", False),
                                 ("/index.html", "28-手机首页整页", True)]:
            await mp.goto(BASE + path); await mp.wait_for_timeout(500)
            await mp.add_style_tag(content=".to-top{display:none!important}")
            await mp.screenshot(path=os.path.join(OUT, name + ".jpg"), quality=86,
                                full_page=full, type="jpeg")
            sw = await mp.evaluate("()=>document.documentElement.scrollWidth")
            print("  ", name, "scrollWidth", sw)
        await m.close(); await b.close()
    print("errors:", errors)

asyncio.run(main())
srv.terminate()
