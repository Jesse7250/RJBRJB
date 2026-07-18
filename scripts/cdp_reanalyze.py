import base64
import json
import time
import urllib.request
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / '.deps'))
import websocket  # type: ignore

OUT = Path('docs/new_image/evidence')

DEBUG_URL = 'http://localhost:9222/json'

def get_page_ws_url():
    targets = json.loads(urllib.request.urlopen(DEBUG_URL, timeout=5).read().decode('utf-8'))
    for t in targets:
        if t.get('type') == 'page':
            return t['webSocketDebuggerUrl']
    raise RuntimeError('no page target')

class CDP:
    def __init__(self, ws_url):
        self.ws = websocket.create_connection(ws_url, timeout=30)
        self.id = 0

    def send(self, method, params=None):
        self.id += 1
        msg = {'id': self.id, 'method': method, 'params': params or {}}
        self.ws.send(json.dumps(msg, ensure_ascii=False))
        while True:
            resp = json.loads(self.ws.recv())
            if resp.get('id') == self.id:
                return resp

    def evaluate(self, code):
        resp = self.send('Runtime.evaluate', {'expression': code, 'returnByValue': True})
        return resp.get('result', {}).get('result', {}).get('value')

    def screenshot(self, path):
        resp = self.send('Page.captureScreenshot', {'format': 'png', 'captureBeyondViewport': True, 'fromSurface': True})
        data = resp.get('result', {}).get('data')
        Path(path).write_bytes(base64.b64decode(data))
        print('saved', path)

    def close(self):
        self.ws.close()


def click_text(cdp, text):
    code = (
        "(() => {"
        "const els = Array.from(document.querySelectorAll('button, a'));"
        "const t = els.find(e => e.innerText && e.innerText.trim().includes('" + text + "'));"
        "if (t) { t.click(); return 'clicked ' + t.innerText; }"
        "return 'not found " + text + "';"
        "})()"
    )
    return cdp.evaluate(code)


def main():
    ws_url = get_page_ws_url()
    cdp = CDP(ws_url)
    cdp.send('Page.enable')
    cdp.send('Runtime.enable')
    print('current url:', cdp.evaluate('location.href'))
    print(click_text(cdp, '掌握进度'))
    time.sleep(3)
    print(click_text(cdp, '重新分析'))
    time.sleep(8)
    cdp.screenshot(OUT / '5_5_bkt_heatmap.png')
    cdp.close()

if __name__ == '__main__':
    main()
