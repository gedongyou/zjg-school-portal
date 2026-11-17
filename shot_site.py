# -*- coding: utf-8 -*-
import asyncio, os, sys, threading, http.server, socketserver, functools
from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(ROOT, "previews"); os.makedirs(OUT, exist_ok=True)

def serve():
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=ROOT)
    socketserver.TCPServer.allow_reuse_address = True
    srv = socketserver.TCPServer(("127.0.0.1", 8123), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv

SECTIONS = [
    ("01-首屏与轮播", ".head", ".cols"),
    ("02-概况与招生", "#about", "#admission"),
    ("03-专业与五心", "#majors", "#wuxin"),
    ("04-校园与页脚", "#campus", ".foot"),
]

async def main():
    serve()
    url = "http://127.0.0.1:8123/index.html"
    errs = []
    async with async_playwright() as p:
        b = await p.chromium.launch()
        # ---- desktop ----
        ctx = await b.new_context(viewport={"width":1440,"height":900}, device_scale_factor=1.5, locale="zh-CN")
        pg = await ctx.new_page()
        pg.on("console", lambda m: errs.append("console:"+m.text) if m.type=="error" else None)
        pg.on("pageerror", lambda e: errs.append("pageerror:"+str(e)))
        await pg.goto(url, wait_until="networkidle")
        await pg.wait_for_timeout(500)
        await pg.screenshot(path=os.path.join(OUT,"首页-整页.png"), full_page=True)
        for name, a, z in SECTIONS:
            box = await pg.evaluate("""([a,z])=>{
                const e1=document.querySelector(a), e2=document.querySelector(z);
                const r1=e1.getBoundingClientRect(), r2=e2.getBoundingClientRect();
                const y1=r1.top+scrollY, y2=r2.bottom+scrollY;
                return {x:0,y:Math.floor(y1)-6,width:document.documentElement.clientWidth,height:Math.ceil(y2-y1)+12};
            }""", [a,z])
            await pg.screenshot(path=os.path.join(OUT,f"首页-{name}.jpg"), clip=box, full_page=True, type="jpeg", quality=86)
        h = await pg.evaluate("document.documentElement.scrollHeight")
        print("desktop height", h)
        await ctx.close()

        # ---- mobile ----
        ctx = await b.new_context(viewport={"width":390,"height":844}, device_scale_factor=2, is_mobile=True, has_touch=True, locale="zh-CN")
        pg = await ctx.new_page()
        pg.on("pageerror", lambda e: errs.append("m-pageerror:"+str(e)))
        await pg.goto(url, wait_until="networkidle")
        await pg.wait_for_timeout(400)
        await pg.screenshot(path=os.path.join(OUT,"手机-整页.png"), full_page=True)
        await pg.screenshot(path=os.path.join(OUT,"手机-首屏.png"))
        print("mobile height", await pg.evaluate("document.documentElement.scrollHeight"))
        await ctx.close()
        await b.close()
    print("errors:", errs)

asyncio.run(main())
