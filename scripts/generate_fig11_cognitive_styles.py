"""
生成图 11：认知风格自适应渲染对比
将 4 张等尺寸资源页截图拼接为 2×2 四宫格。

用法：
    python scripts/generate_fig11_cognitive_styles.py \
        "docs/test-screenshots/student_flow_08_resources_page.png" \
        "docs/test-screenshots/student_flow_09_resources_timeline_and_evolution.png" \
        "docs/test-screenshots/auditory_style.png" \
        "docs/test-screenshots/student_flow_08_resources_page.png"

第 3 张（听觉型）目前需要手动截取；在补齐前，可先用同一张图占位，
但提交前务必替换为真实的听觉型界面截图。
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import gridspec, font_manager as fm
from PIL import Image

# 强制使用系统中文字体
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"],
    "axes.unicode_minus": False,
})

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "images"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LABELS = ["文字型", "视觉型", "听觉型", "动觉型"]


def main():
    if len(sys.argv) >= 5:
        paths = [Path(p) for p in sys.argv[1:5]]
    else:
        # 默认占位：文字型/动觉型用同一张，视觉型用时间线，听觉型重复占位
        base = Path(__file__).resolve().parent.parent / "docs" / "test-screenshots"
        paths = [
            base / "student_flow_08_resources_page.png",
            base / "student_flow_09_resources_timeline_and_evolution.png",
            base / "student_flow_08_resources_page.png",  # TODO: 替换为听觉型截图
            base / "student_flow_08_resources_page.png",
        ]

    images = [Image.open(p) for p in paths]

    # 统一尺寸：以最小宽高为准，避免拉伸
    min_w = min(img.width for img in images)
    min_h = min(img.height for img in images)
    images = [img.crop((0, 0, min_w, min_h)).resize((min_w, min_h)) for img in images]

    fig = plt.figure(figsize=(14, 10))
    gs = gridspec.GridSpec(2, 2, figure=fig, wspace=0.05, hspace=0.12)

    for idx, (img, label) in enumerate(zip(images, LABELS)):
        ax = fig.add_subplot(gs[idx // 2, idx % 2])
        ax.imshow(img)
        ax.axis("off")
        ax.set_title(label, fontsize=14, fontweight="bold", pad=8)

    fig.suptitle("图 11：认知风格自适应渲染对比", fontsize=16, fontweight="bold", y=0.98)

    base = OUTPUT_DIR / "fig11-cognitive-styles"
    fig.savefig(base.with_suffix(".png"), dpi=150, bbox_inches="tight", facecolor="white")
    fig.savefig(base.with_suffix(".svg"), bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("Generated fig11-cognitive-styles in", OUTPUT_DIR)
    print("说明：当前拼图基于现有测试截图生成；如后续捕获到更典型的听觉型/动觉型界面截图，可直接替换对应子图来源。")


if __name__ == "__main__":
    main()
