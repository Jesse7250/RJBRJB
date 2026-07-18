import base64
import json
import time
import urllib.request
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / '.deps'))
import websocket  # type: ignore

OUT = Path('docs/new_image/evidence')
OUT.mkdir(parents=True, exist_ok=True)

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
        if not data:
            raise RuntimeError('no screenshot data: ' + str(resp))
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

    time.sleep(2)
    print('start url:', cdp.evaluate('location.href'))

    # 进入推荐课程
    print(click_text(cdp, '进入推荐课程'))
    time.sleep(3)
    cdp.screenshot(OUT / 'ui_workspace.png')

    # 知识图谱滚动
    cdp.evaluate(
        "(() => {"
        "const els = Array.from(document.querySelectorAll('*'));"
        "for (const el of els) { if (el.scrollHeight > el.clientHeight + 50) { el.scrollTop += 600; } }"
        "return 'ok';"
        "})()"
    )
    time.sleep(1)
    cdp.screenshot(OUT / 'ui_graph.png')

    # 规划路径
    print(click_text(cdp, '规划路径'))
    time.sleep(3)
    cdp.screenshot(OUT / 'ui_graph_path.png')

    # 生成目标资源
    print(click_text(cdp, '生成目标资源'))
    time.sleep(15)
    cdp.screenshot(OUT / 'ui_after_generate.png')

    # 学习资源
    print(click_text(cdp, '学习资源'))
    time.sleep(3)
    cdp.screenshot(OUT / 'ui_resources.png')

    # 代码沙箱
    print(click_text(cdp, '代码沙箱'))
    time.sleep(3)
    print(click_text(cdp, '运行'))
    time.sleep(3)
    cdp.screenshot(OUT / 'ui_code_sandbox.png')

    # 掌握进度
    print(click_text(cdp, '掌握进度'))
    time.sleep(3)
    cdp.screenshot(OUT / '5_5_bkt_heatmap.png')

    # 学习画像
    print(click_text(cdp, '学习画像'))
    time.sleep(3)
    cdp.screenshot(OUT / 'ui_profile_full.png')

    cdp.close()


if __name__ == '__main__':
    main()
