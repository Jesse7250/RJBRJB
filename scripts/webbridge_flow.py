import json
import time
import urllib.request
from pathlib import Path

OUT = Path('docs/new_image/evidence')
OUT.mkdir(parents=True, exist_ok=True)

SESSION = 'eduhive'

def cmd(action, args=None):
    payload = {'action': action, 'args': args or {}, 'session': SESSION}
    data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    req = urllib.request.Request(
        'http://127.0.0.1:10086/command',
        data=data,
        headers={'Content-Type': 'application/json; charset=utf-8'},
    )
    return json.loads(urllib.request.urlopen(req, timeout=30).read().decode('utf-8'))

def click_text(text):
    code = (
        "(() => {"
        "const els = Array.from(document.querySelectorAll('button, a'));"
        "const t = els.find(e => e.innerText && e.innerText.trim().includes('" + text + "'));"
        "if (t) { t.click(); return 'clicked ' + t.innerText; }"
        "return 'not found " + text + "';"
        "})()"
    )
    return cmd('evaluate', {'code': code})

def shot(path):
    return cmd('screenshot', {'path': str(OUT / path)})

def scroll_graph():
    code = (
        "(() => {"
        "const els = Array.from(document.querySelectorAll('*'));"
        "for (const el of els) {"
        "if (el.scrollHeight > el.clientHeight + 50) { el.scrollTop += 600; }"
        "}"
        "return 'scrolled';"
        "})()"
    )
    return cmd('evaluate', {'code': code})

print(cmd('navigate', {'url': 'http://localhost:5173', 'newTab': True}))
time.sleep(3)
print(click_text('进入推荐课程'))
time.sleep(3)
print(shot('ui_start.png'))
