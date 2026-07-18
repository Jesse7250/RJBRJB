from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path('docs/new_image/evidence')
ROOT.mkdir(parents=True, exist_ok=True)

FONT_PATH = Path('C:/Windows/Fonts/msyh.ttc')
TITLE_FONT = ImageFont.truetype(str(FONT_PATH), 32)

def crop(src, box, out_name):
    img = Image.open(src).convert('RGB')
    crop_img = img.crop(box)
    crop_img.save(ROOT / out_name, quality=95)
    print('saved', out_name)

# 5.2 Agent 协作面板（从学习画像页面裁剪）
crop(ROOT / 'ui_profile_full.png', (1500, 150, 2549, 650), '5_2_agent_collaboration.png')

# 5.3 学习画像证据（从学习画像页面裁剪）
crop(ROOT / 'ui_profile_full.png', (350, 150, 1800, 650), '5_3_profile_evidence.png')

# 5.4 认知风格 2x2 四宫格
def load_crop(path, box, size=(1200, 600)):
    img = Image.open(path).convert('RGB')
    c = img.crop(box).resize(size, Image.LANCZOS)
    return c

panels = [
    ('文字型', load_crop(ROOT / 'ui_resources.png', (350, 850, 1600, 1242))),
    ('视觉型', load_crop(ROOT / 'ui_graph_scrolled2.png', (350, 0, 1600, 700))),
    ('听觉型', load_crop(ROOT / 'ui_profile_full.png', (2050, 620, 2549, 1050))),
    ('动觉型', load_crop(ROOT / 'ui_code_sandbox.png', (350, 850, 1600, 1242))),
]

W, H = 1200, 600
margin = 20
title_h = 50
canvas = Image.new('RGB', (W*2 + margin*3, H*2 + title_h*2 + margin*4), 'white')
draw = ImageDraw.Draw(canvas)
for idx, (label, panel) in enumerate(panels):
    x = margin + (idx % 2) * (W + margin)
    y = margin + (idx // 2) * (H + title_h + margin)
    draw.rectangle([x, y, x + W, y + title_h], fill='#1976D2')
    draw.text((x + 16, y + 10), label, fill='white', font=TITLE_FONT)
    canvas.paste(panel, (x, y + title_h))
canvas.save(ROOT / '5_4_cognitive_styles.png', quality=95)
print('saved 5_4_cognitive_styles.png')

# 5.5 BKT 热力图（保持完整截图即可）
print('5_5_bkt_heatmap.png kept as full screenshot')
