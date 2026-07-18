"""
按学术论文通用审美重新生成图 1：schematic-led composite。
结构：上方大 schematic 展示四应用场景与中央系统，下方 3 个小 quant 面板给出数据证据。
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

# ---------------------------------------------------------------------------
# 基础配置
# ---------------------------------------------------------------------------
OUT_DIR = Path(__file__).resolve().parent.parent / "docs" / "figures"
OUT_DIR.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Microsoft YaHei", "Arial", "DejaVu Sans", "Liberation Sans"],
    "axes.unicode_minus": False,
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "font.size": 7,
    "axes.spines.right": False,
    "axes.spines.top": False,
    "axes.linewidth": 0.8,
    "legend.frameon": False,
    "figure.dpi": 150,
})

PALETTE = {
    "blue_main": "#0F4D92",
    "blue_secondary": "#3775BA",
    "blue_light": "#D0E4F2",
    "green_light": "#DDF3DE",
    "purple_light": "#EAD3E8",
    "teal_light": "#D0E8EA",
    "red_strong": "#B64342",
    "gold": "#FFD700",
    "neutral_dark": "#2E2E2E",
    "neutral_mid": "#767676",
    "neutral_light": "#CFCECE",
}


def save_all(fig, name):
    base = OUT_DIR / name
    fig.savefig(f"{base}.svg", bbox_inches="tight")
    fig.savefig(f"{base}.pdf", bbox_inches="tight")
    fig.savefig(f"{base}.png", dpi=300, bbox_inches="tight")
    print(f"Saved {base}.{{svg,png,pdf}}")


def add_panel_label(ax, label, x=-0.06, y=1.02, fontsize=10, color="black"):
    ax.text(x, y, label, transform=ax.transAxes, fontsize=fontsize,
            fontweight="bold", color=color, ha="left", va="bottom")


# ---------------------------------------------------------------------------
# 图 1：schematic-led composite
# ---------------------------------------------------------------------------
def make_fig1():
    fig = plt.figure(figsize=(7.2, 5.5))
    gs = fig.add_gridspec(
        2, 3,
        height_ratios=[1.8, 1.0],
        hspace=0.32,
        wspace=0.35,
        left=0.08, right=0.94, top=0.92, bottom=0.10,
    )

    ax_a = fig.add_subplot(gs[0, :])
    ax_b = fig.add_subplot(gs[1, 0])
    ax_c = fig.add_subplot(gs[1, 1])
    ax_d = fig.add_subplot(gs[1, 2])

    # ---- Panel a: 主流程示意图 ----
    ax_a.set_xlim(0, 10)
    ax_a.set_ylim(0, 10)
    ax_a.axis("off")
    ax_a.set_facecolor("white")

    # 中央系统
    center = FancyBboxPatch(
        (3.75, 4.4), 2.5, 1.2,
        boxstyle="round,pad=0.05,rounding_size=0.2",
        facecolor=PALETTE["blue_main"],
        edgecolor=PALETTE["blue_main"],
        linewidth=1.5,
    )
    ax_a.add_patch(center)
    ax_a.text(5.0, 5.25, "EduHive", ha="center", va="center",
              fontsize=11, fontweight="bold", color="white")
    ax_a.text(5.0, 4.75, "33 知识点 · 5 Agent · 4 审核视角", ha="center", va="center",
              fontsize=7, color="white")

    # 四个应用场景
    scenarios = [
        {
            "name": "课后自主学习",
            "data": "资源包：讲义/导图/练习/代码/语音",
            "pos": (1.0, 7.0),
            "color": PALETTE["blue_light"],
            "anchor": (3.75, 5.6),
        },
        {
            "name": "翻转课堂资源推送",
            "data": "班级 35 人 · 完成率 68/82/91%",
            "pos": (7.0, 7.0),
            "color": PALETTE["green_light"],
            "anchor": (6.25, 5.6),
        },
        {
            "name": "考前复习与薄弱点巩固",
            "data": "33 知识点 BKT 热力图",
            "pos": (1.0, 1.0),
            "color": PALETTE["purple_light"],
            "anchor": (3.75, 4.4),
        },
        {
            "name": "教师备课与学情分析",
            "data": "错误率 62% · 触发资源重审",
            "pos": (7.0, 1.0),
            "color": PALETTE["teal_light"],
            "anchor": (6.25, 4.4),
        },
    ]

    for s in scenarios:
        x, y = s["pos"]
        rect = FancyBboxPatch(
            (x, y), 2.2, 1.4,
            boxstyle="round,pad=0.03,rounding_size=0.15",
            facecolor=s["color"],
            edgecolor=PALETTE["neutral_mid"],
            linewidth=1.0,
        )
        ax_a.add_patch(rect)
        ax_a.text(x + 1.1, y + 1.0, s["name"], ha="center", va="center",
                  fontsize=8, fontweight="bold", color=PALETTE["neutral_dark"])
        ax_a.text(x + 1.1, y + 0.45, s["data"], ha="center", va="center",
                  fontsize=6.5, color=PALETTE["neutral_dark"])
        # 箭头
        arrow = FancyArrowPatch(
            s["anchor"], (x + 1.1, y + 0.7 if s["anchor"][1] > y else y + 0.7),
            arrowstyle="->", color=PALETTE["neutral_mid"], lw=1.2,
            connectionstyle="arc3,rad=0.1",
        )
        ax_a.add_patch(arrow)

    # 顶部标题
    ax_a.text(0.5, 1.02, "EduHive 通过统一平台服务四类教学场景",
              transform=ax_a.transAxes, ha="center", va="bottom",
              fontsize=9, fontweight="bold", color=PALETTE["neutral_dark"])
    add_panel_label(ax_a, "a", x=-0.02, y=1.02)

    # ---- Panel b: 资源类型分布（课后自主学习示例） ----
    resources = ["讲义", "导图", "练习", "代码", "语音"]
    counts = [1, 1, 3, 2, 1]
    y_pos = np.arange(len(resources))
    bars = ax_b.barh(y_pos, counts, color=PALETTE["blue_secondary"], edgecolor="black", linewidth=0.6, height=0.6)
    ax_b.set_yticks(y_pos)
    ax_b.set_yticklabels(resources, fontsize=7)
    ax_b.set_xlabel("数量", fontsize=7)
    ax_b.set_xlim(0, 4)
    for bar, c in zip(bars, counts):
        ax_b.text(c + 0.15, bar.get_y() + bar.get_height()/2, str(c),
                  va="center", ha="left", fontsize=7, color=PALETTE["neutral_dark"])
    ax_b.set_title("课后自主学习资源包", fontsize=8, fontweight="bold", pad=6)
    add_panel_label(ax_b, "b")

    # ---- Panel c: BKT 掌握度热力图（33 知识点缩影） ----
    np.random.seed(1)
    heat = np.random.rand(5, 7)
    heat[3, 5] = 0.18  # 薄弱点
    heat[4, 6] = 0.22
    im = ax_c.imshow(heat, cmap="RdYlGn", aspect="auto", vmin=0, vmax=1)
    ax_c.set_xticks([])
    ax_c.set_yticks([])
    ax_c.set_frame_on(False)
    # 标注薄弱点
    ax_c.text(5, 3, "弱", ha="center", va="center", fontsize=7, color="white", fontweight="bold")
    ax_c.text(6, 4, "弱", ha="center", va="center", fontsize=7, color="white", fontweight="bold")
    cbar = fig.colorbar(im, ax=ax_c, fraction=0.046, pad=0.04)
    cbar.set_label("掌握度", fontsize=6)
    cbar.ax.tick_params(labelsize=6)
    ax_c.set_title("考前复习：知识点掌握度", fontsize=8, fontweight="bold", pad=6)
    add_panel_label(ax_c, "c")

    # ---- Panel d: 班级错误率趋势 ----
    weeks = np.array([1, 2, 3, 4])
    error_rate = np.array([0.25, 0.38, 0.62, 0.45])
    ax_d.plot(weeks, error_rate, marker="o", color=PALETTE["red_strong"], linewidth=1.5, markersize=5)
    ax_d.axhline(0.60, color=PALETTE["gold"], linestyle="--", linewidth=1.2)
    ax_d.set_ylim(0, 1)
    ax_d.set_xlabel("周次", fontsize=7)
    ax_d.set_ylabel("错误率", fontsize=7)
    ax_d.set_xticks(weeks)
    ax_d.text(1.2, 0.68, "阈值 0.6", fontsize=6.5, color=PALETTE["gold"], ha="left")
    ax_d.set_title("教师学情：文件读写错误率", fontsize=8, fontweight="bold", pad=6)
    add_panel_label(ax_d, "d")

    save_all(fig, "fig1_application_scenarios")
    plt.close(fig)


if __name__ == "__main__":
    make_fig1()
    print("Done.")
