import asyncio,threading,http.server,functools
from playwright.async_api import async_playwright
ROOT='/workspace/shadowveil'; PORT=8911
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*a): pass
srv=http.server.ThreadingHTTPServer(('127.0.0.1',PORT),functools.partial(Q,directory=ROOT)); threading.Thread(target=srv.serve_forever,daemon=True).start()
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
        for V in ['apose','tpose','left','right','back']:
            pg=await b.new_page(); bad=[]
            pg.on('response',lambda r,bad=bad: bad.append(r.url.split(str(PORT))[1]) if r.status>=400 else None)
            await pg.goto(f'http://127.0.0.1:{PORT}/rig/index.html?view={V}')
            await pg.wait_for_function('typeof R!=="undefined"&&R&&R.im&&R.im.base',timeout=60000); await pg.wait_for_timeout(2500)
            print(V,bad,flush=True); await pg.close()
        await b.close()
asyncio.run(main())
