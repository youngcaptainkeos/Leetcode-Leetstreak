"""Synthetic browser checks; API requests stay inside TestClient, providers are mocked.

Run from any directory with backend test dependencies and Playwright installed.
Optionally set LEETSTREAK_CHROME_EXECUTABLE and LEETSTREAK_BROWSER_EVIDENCE_DIR.
Build both clients first. This checks popup UI in browser-preview mode; native
extension background/content-script acceptance is tracked separately in M3.
"""
import asyncio, json, sys, threading, re, os, tempfile
import httpx
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlsplit
from unittest.mock import AsyncMock, patch

root=Path(__file__).resolve().parents[2]
private=Path(os.environ.get('LEETSTREAK_BROWSER_EVIDENCE_DIR') or tempfile.mkdtemp(prefix='leetstreak-browser-check-')).resolve()
private.mkdir(mode=0o700, parents=True, exist_ok=True)
sys.path[:0]=[str(root/'backend/tests'),str(root/'backend')]
import test_access as fixtures
from app import main
from playwright.async_api import async_playwright, expect

class Handler(SimpleHTTPRequestHandler):
    def translate_path(self,path):
        path=urlsplit(path).path
        if path.startswith('/extension/'):
            return str(root/'extension/dist'/path.removeprefix('/extension/'))
        if path.startswith('/web-assets/'):
            return str(root/'backend/web/assets'/path.removeprefix('/web-assets/'))
        return str(root/'backend/web/index.html')
    def log_message(self,*args):pass

async def run():
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    origin=f'http://127.0.0.1:{server.server_port}'
    results=[]
    provider_client=httpx.AsyncClient
    try:
        async with async_playwright() as playwright:
            browser=await playwright.chromium.launch(executable_path=os.environ.get('LEETSTREAK_CHROME_EXECUTABLE'),headless=True,args=['--no-sandbox'])
            for client,width,path in [('extension',380,'/extension/index.html'),('website',1366,'/login')]:
                fixture=fixtures.AccessTests('test_coding_profiles_are_viewable_without_private_fields'); fixture.setUp()
                context=await browser.new_context(viewport={'width':width,'height':800})
                calls=[];errors=[]
                async def intercept(route):
                    req=route.request; parsed=urlsplit(req.url)
                    if parsed.path.startswith('/api/'):
                        if req.method=='OPTIONS':
                            await route.fulfill(status=204,headers={'Access-Control-Allow-Origin':'*','Access-Control-Allow-Headers':'*','Access-Control-Allow-Methods':'*'});return
                        headers={k:v for k,v in req.headers.items() if k in ['authorization','content-type']}
                        response=await asyncio.to_thread(fixture.client.request,req.method,parsed.path+('?' + parsed.query if parsed.query else ''),headers=headers,content=req.post_data)
                        calls.append({'path':parsed.path,'status':response.status_code})
                        await route.fulfill(status=response.status_code,body=response.content,headers={'Content-Type':'application/json','Access-Control-Allow-Origin':'*'})
                    elif parsed.hostname=='127.0.0.1':await route.continue_()
                    else:await route.abort()
                await context.route('**/*',intercept)
                page=await context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
                try:
                    with patch.object(main,'fetch_today_daily_challenge_slug',new=AsyncMock(return_value=None)), patch.object(httpx, 'AsyncClient', side_effect=lambda **kwargs: provider_client(**kwargs, transport=httpx.MockTransport(lambda request: httpx.Response(200, json={'data': {'activeDailyCodingChallengeQuestion': None}})))):
                        await page.goto(origin+path)
                        await page.get_by_placeholder('e.g. alex@example.com').fill('demo1@example.com')
                        await page.get_by_placeholder('••••••••').fill('synthetic-password')
                        await page.locator('form').get_by_role('button',name='Log In',exact=True).click()
                        settings=page.locator('button[title="Account Settings (Change LeetCode Username)"]')
                        await settings.wait_for()
                        await settings.click()
                        modal=page.locator('.settings-modal');await modal.wait_for()
                        checkbox=modal.locator('input[type="checkbox"]')
                        await expect(checkbox).to_be_checked();await modal.locator('label.settings-switch').click()
                        await expect(checkbox).not_to_be_checked()
                        for _ in range(100):
                            if any(c['path']=='/api/users/1/settings' and c['status']==200 for c in calls):break
                            await asyncio.sleep(.05)
                        assert fixture.client.get('/api/users/1/dashboard',headers=fixture.headers()).json()['show_global_leaderboard'] is False
                        await modal.locator('.modal-close').click()
                        await page.reload();await settings.wait_for();await settings.click();await modal.wait_for()
                        await expect(modal.locator('input[type="checkbox"]')).not_to_be_checked()
                        old=await page.evaluate("localStorage.getItem('codestreak_access_token')")
                        assert old
                        await modal.locator('input[autocomplete="current-password"]').fill('synthetic-password')
                        await modal.locator('input[autocomplete="new-password"]').fill('a synthetic browser passphrase')
                        await modal.get_by_role('button',name='Change password',exact=True).click()
                        await page.get_by_text('Password changed. Your other sessions have been signed out.',exact=True).wait_for()
                        assert fixture.client.get('/api/users/1/dashboard',headers={'Authorization':'Bearer '+old}).status_code==401
                        await page.wait_for_function("old => localStorage.getItem('codestreak_access_token') !== old", arg=old, timeout=3000)
                        await page.screenshot(path=str(private/f'm1-{client}-settings.png'),full_page=True)
                        # A revoked token from another device must end the displayed session.
                        fixture.db.expire_all();user=fixture.db.query(fixtures.User).filter_by(id=1).one();user.session_version+=1;fixture.db.commit()
                        await page.reload()
                        await page.get_by_placeholder('e.g. alex@example.com').wait_for()
                        assert await page.evaluate("localStorage.getItem('codestreak_access_token')") is None
                        assert not errors,errors
                        results.append({'client':client,'login':True,'preference_persisted':True,'password_change_revoked_old_token':True,'expired_session_returned_to_signin':True,'runtime_errors':len(errors)})
                except Exception:
                    await page.screenshot(path=str(private/f'm1-{client}-failure.png'),full_page=True)
                    (private/f'm1-{client}-failure.txt').write_text((await page.locator('body').inner_text())[:14000])
                    raise
                finally:
                    await context.close();fixture.tearDown()
            await browser.close()
        (private/'m1-browser-results.json').write_text(json.dumps(results,indent=2));print(json.dumps(results))
    finally:server.shutdown();server.server_close()

asyncio.run(run())
