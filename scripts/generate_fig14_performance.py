"""
生成图 14：性能优化前后对比
数据与正文 4.2 节表格严格一致。
输出：docs/images/fig14-performance.png / .svg
"""
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "images"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Arial", "DejaVu Sans"],
    "axes.unicode_minus": False,
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "font.size": 10,
    "axes.spines.right": False,
    "axes.spines.top": False,
    "axes.linewidth": 0.8,
    "legend.frameon": False,
})

PALETTE = {
    "before": "#B64342",
    "after": "#0F4D92",
    "bg": "#F7F8FA",
    "text": "#272727",
    "grid": "#CFCECE",
}


def save(fig, name):
    base = OUTPUT_DIR / name
    fig.savefig(base.with_suffix(".svg"), bbox_inches="tight", facecolor="white")
    fig.savefig(base.with_suffix(".png"), dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main():
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.5))
    fig.patch.set_facecolor("white")

    categories = ["优化前", "优化后"]
    x = np.arange(len(categories))
    width = 0.5

    # 子图 1：资源生成响应时间（对数轴）
    ax = axes[0]
    values = [3.0, 0.02]
    bars = ax.bar(x, values, width, color=[PALETTE["before"], PALETTE["after"]])
    ax.set_ylabel("响应时间（秒）")
    ax.set_title("资源生成响应时间")
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.set_yscale("log")
    ax.set_ylim(0.005, 5)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height()*1.2,
                f"{val}s", ha="center", va="bottom", fontsize=10, fontweight="bold")

    # 子图 2：前端主包大小
    ax = axes[1]
    values = [465, 98]
    bars = ax.bar(x, values, width, color=[PALETTE["before"], PALETTE["after"]])
    ax.set_ylabel("大小（KB）")
    ax.set_title("前端主包大小")
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.set_ylim(0, 550)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 15,
                f"{val}KB", ha="center", va="bottom", fontsize=10, fontweight="bold")

    # 子图 3：代码沙箱平均延迟
    ax = axes[2]
    values = [1.0, 0.5]  # 示意：后端网络往返 vs 后端执行平均 <500ms
    bars = ax.bar(x, values, width, color=[PALETTE["before"], PALETTE["after"]])
    ax.set_ylabel("延迟（秒）")
    ax.set_title("代码沙箱平均延迟")
    ax.set_xticks(x)
    ax.set_xticklabels(["后端网络往返", "后端执行\n<500ms"])
    ax.set_ylim(0, 1.2)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    for bar, val in zip(bars, values):
        label = f"{val}s" if val >= 1 else f"{int(val*1000)}ms"
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.04,
                label, ha="center", va="bottom", fontsize=10, fontweight="bold")

    fig.suptitle("图 14：性能优化前后对比（mock 模式 / Chrome / FastAPI 端口 8001）",
                 fontsize=13, fontweight="bold", y=1.02)
    plt.tight_layout()
    save(fig, "fig14-performance")
    print("Generated fig14-performance in", OUTPUT_DIR)


if __name__ == "__main__":
    main()
