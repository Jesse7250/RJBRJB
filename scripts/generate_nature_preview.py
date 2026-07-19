"""
使用 Python / matplotlib 生成智慧伴学设计文档的 3 张 Nature-style 预览图：
- fig23: 性能对比柱状图
- fig24: 竞争优势雷达图
- fig1:  应用场景信息图

输出: docs/figures/{name}.svg + .png + .pdf
"""
import os
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

# Nature-style palette (from image_prompts.md project palette)
PALETTE = {
    "blue_main": "#0F4D92",
    "blue_secondary": "#3775BA",
    "green_1": "#DDF3DE",
    "green_2": "#AADCA9",
    "green_3": "#8BCF8B",
    "red_1": "#F6CFCB",
    "red_strong": "#B64342",
    "neutral_light": "#CFCECE",
    "neutral_mid": "#767676",
    "neutral_dark": "#4D4D4D",
    "gold": "#FFD700",
    "teal": "#42949E",
    "violet": "#9A4D8E",
    "purple": "#9A4D8E",
    "white": "#FFFFFF",
    "bg": "#F7F8FA",
}

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Microsoft YaHei", "SimHei", "Arial", "DejaVu Sans", "Liberation Sans"],
    "axes.unicode_minus": False,
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "font.size": 9,
    "axes.spines.right": False,
    "axes.spines.top": False,
    "axes.linewidth": 0.8,
    "legend.frameon": False,
    "figure.dpi": 150,
})


def save_all(fig, name):
    base = OUT_DIR / name
    fig.savefig(f"{base}.svg", bbox_inches="tight")
    fig.savefig(f"{base}.pdf", bbox_inches="tight")
    fig.savefig(f"{base}.png", dpi=300, bbox_inches="tight")
    print(f"Saved {base}.{{svg,png,pdf}}")


def finalize(fig, name, pad=1.5, tight=True):
    if tight:
        fig.tight_layout(pad=pad)
    save_all(fig, name)
    plt.close(fig)


# ---------------------------------------------------------------------------
# 图 23: 性能对比柱状图
# ---------------------------------------------------------------------------
def make_fig23():
    fig, axes = plt.subplots(1, 3, figsize=(9, 3.2), sharey=False)
    fig.suptitle("图 23  系统关键性能指标对比", fontsize=12, fontweight="bold", y=1.02)

    categories = ["优化前", "优化后"]
    before_color = PALETTE["neutral_mid"]
    after_color = PALETTE["blue_main"]

    # 子图 1: 响应时间 (log 轴)
    ax = axes[0]
    vals = [3.0, 0.02]
    bars = ax.bar(categories, vals, color=[before_color, after_color], edgecolor="black", linewidth=0.8, width=0.6)
    ax.set_ylabel("响应时间 (s)", fontsize=9)
    ax.set_yscale("log")
    ax.set_ylim(1e-3, 10)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, v*1.3, f"{v} s", ha="center", va="bottom", fontsize=8)
    ax.annotate("", xy=(1, 0.02), xytext=(1, 3.0),
                arrowprops=dict(arrowstyle="->", color=PALETTE["red_strong"], lw=1.2))
    ax.text(1.15, 0.25, "150×↓", fontsize=8, color=PALETTE["red_strong"], fontweight="bold")

    # 子图 2: 前端主包大小
    ax = axes[1]
    vals = [465, 98]
    bars = ax.bar(categories, vals, color=[before_color, after_color], edgecolor="black", linewidth=0.8, width=0.6)
    ax.set_ylabel("主包大小 (KB)", fontsize=9)
    ax.set_ylim(0, 550)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, v + 15, f"{v} KB", ha="center", va="bottom", fontsize=8)
    ax.annotate("", xy=(1, 98), xytext=(1, 465),
                arrowprops=dict(arrowstyle="->", color=PALETTE["red_strong"], lw=1.2))
    ax.text(1.15, 250, "4.7×↓", fontsize=8, color=PALETTE["red_strong"], fontweight="bold")

    # 子图 3: 代码沙箱延迟
    ax = axes[2]
    vals = [500, 0]
    bars = ax.bar(["后端沙箱", "浏览器端\nPyodide"], vals, color=[before_color, PALETTE["green_3"]], edgecolor="black", linewidth=0.8, width=0.6)
    ax.set_ylabel("延迟 (ms)", fontsize=9)
    ax.set_ylim(0, 600)
    for bar, v in zip(bars, vals):
        label = f"{v} ms" if v > 0 else "0 ms\n(本地)"
        ax.text(bar.get_x() + bar.get_width()/2, v + 20, label, ha="center", va="bottom", fontsize=8)

    for ax in axes:
        ax.tick_params(axis="x", labelsize=8)
        ax.tick_params(axis="y", labelsize=8)

    finalize(fig, "fig23_performance")


# ---------------------------------------------------------------------------
# 图 24: 竞争优势雷达图
# ---------------------------------------------------------------------------
def make_fig24():
    labels = ["个性化", "准确性", "安全性", "闭环性", "体验", "可扩展性"]
    n = len(labels)
    angles = np.linspace(0, 2*np.pi, n, endpoint=False).tolist()
    angles += angles[:1]

    data = {
        "智慧伴学": ([4.8, 4.5, 4.6, 4.7, 4.4, 4.3], PALETTE["blue_main"]),
        "传统 LMS": ([2.0, 3.5, 3.0, 1.5, 3.0, 2.5], PALETTE["neutral_mid"]),
        "单一 LLM": ([3.5, 2.5, 1.5, 2.0, 3.5, 3.0], PALETTE["red_strong"]),
        "知识图谱系统": ([2.5, 4.0, 3.5, 2.0, 2.5, 3.0], PALETTE["green_3"]),
        "题库系统": ([1.5, 3.5, 3.0, 1.0, 2.5, 2.0], PALETTE["gold"]),
    }

    fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    for name, (values, color) in data.items():
        values = values + values[:1]
        lw = 2.5 if name == "智慧伴学" else 1.2
        alpha = 0.18 if name == "智慧伴学" else 0.08
        ax.plot(angles, values, color=color, linewidth=lw, label=name)
        ax.fill(angles, values, color=color, alpha=alpha)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylim(0, 5)
    ax.set_yticks([1, 2, 3, 4, 5])
    ax.set_yticklabels(["1", "2", "3", "4", "5"], fontsize=7, color=PALETTE["neutral_mid"])
    ax.grid(linewidth=0.5, color=PALETTE["neutral_light"])

    ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.1), fontsize=8)
    ax.set_title("图 24  智慧伴学与现有方案竞争优势对比", fontsize=12, fontweight="bold", y=1.08)

    finalize(fig, "fig24_competitive_radar")



# ---------------------------------------------------------------------------
# 图 1: 应用场景信息图 (2×2 四象限 + 中央系统面板)
# ---------------------------------------------------------------------------
def draw_panel_title(ax, title, color):
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.set_facecolor("none")
    rect = FancyBboxPatch((0.02, 0.87), 0.96, 0.11,
                          boxstyle="round,pad=0.005,rounding_size=0.02",
                          facecolor=color, edgecolor="none", transform=ax.transAxes)
    ax.add_patch(rect)
    ax.text(0.5, 0.925, title, ha="center", va="center",
            fontsize=11, fontweight="bold", color="white", transform=ax.transAxes)


def make_fig1():
    fig = plt.figure(figsize=(14, 10))
    fig.patch.set_facecolor("white")
    fig.text(0.5, 0.97, "图 1  智慧伴学应用场景与数据价值示意",
             ha="center", va="top", fontsize=15, fontweight="bold", color=PALETTE["neutral_dark"])

    # 四象限 axes
    ax_tl = fig.add_axes([0.06, 0.55, 0.36, 0.36])   # 课后自主学习
    ax_tr = fig.add_axes([0.58, 0.55, 0.36, 0.36])   # 翻转课堂
    ax_bl = fig.add_axes([0.06, 0.10, 0.36, 0.36])   # 考前复习
    ax_br = fig.add_axes([0.58, 0.10, 0.36, 0.36])   # 教师学情

    # 中央系统面板 (最后添加，置顶；缩小并居中，避免遮挡文字)
    ax_center = fig.add_axes([0.40, 0.40, 0.20, 0.20])
    ax_center.set_xlim(0, 1)
    ax_center.set_ylim(0, 1)
    ax_center.axis("off")
    ax_center.set_facecolor("none")
    center_box = FancyBboxPatch((0.05, 0.10), 0.90, 0.80,
                                boxstyle="round,pad=0.02,rounding_size=0.06",
                                facecolor=PALETTE["blue_main"], edgecolor=PALETTE["gold"], linewidth=2.5)
    ax_center.add_patch(center_box)
    ax_center.text(0.5, 0.62, "智慧伴学", ha="center", va="center",
                   fontsize=14, fontweight="bold", color="white")
    ax_center.text(0.5, 0.40, "EduMate", ha="center", va="center",
                   fontsize=11, color="white", style="italic")
    ax_center.text(0.5, 0.22, "33 知识点 · 5 Agent · 4 审核视角", ha="center", va="center",
                   fontsize=8, color=PALETTE["neutral_light"])

    # 连接箭头：从各面板最近中央的角指向中央面板边缘，避免穿过文字
    arrow_style = "Simple, tail_width=0.5, head_width=5, head_length=5"
    kw = dict(arrowstyle=arrow_style, color=PALETTE["neutral_mid"], lw=1.5,
              mutation_scale=1, zorder=0)
    # TL 面板右下角 -> 中央面板左上
    fig.patches.append(FancyArrowPatch((0.42, 0.55), (0.40, 0.60),
                                       connectionstyle="arc3,rad=0.1", **kw, transform=fig.transFigure))
    # TR 面板左下角 -> 中央面板右上
    fig.patches.append(FancyArrowPatch((0.58, 0.55), (0.60, 0.60),
                                       connectionstyle="arc3,rad=-0.1", **kw, transform=fig.transFigure))
    # BL 面板右上角 -> 中央面板左下
    fig.patches.append(FancyArrowPatch((0.42, 0.46), (0.40, 0.40),
                                       connectionstyle="arc3,rad=-0.1", **kw, transform=fig.transFigure))
    # BR 面板左上角 -> 中央面板右下
    fig.patches.append(FancyArrowPatch((0.58, 0.46), (0.60, 0.40),
                                       connectionstyle="arc3,rad=0.1", **kw, transform=fig.transFigure))

    # ---- 左上：课后自主学习 ----
    draw_panel_title(ax_tl, "课后自主学习", PALETTE["blue_secondary"])
    # 头像 + 画像
    circle = plt.Circle((0.15, 0.72), 0.08, color=PALETTE["blue_secondary"], alpha=0.2, transform=ax_tl.transAxes)
    ax_tl.add_patch(circle)
    ax_tl.text(0.15, 0.72, "S", ha="center", va="center", fontsize=14,
               fontweight="bold", color=PALETTE["blue_secondary"], transform=ax_tl.transAxes)
    ax_tl.text(0.32, 0.78, "学生画像", fontsize=9, fontweight="bold", color=PALETTE["neutral_dark"], transform=ax_tl.transAxes)
    ax_tl.text(0.32, 0.71, "知识水平 2.2/5\n认知风格 动觉型\n目标 文件读写",
               fontsize=8, color=PALETTE["neutral_dark"], va="top", linespacing=1.4, transform=ax_tl.transAxes)
    # 资源卡片
    resources = [("Markdown 讲义", 1, PALETTE["green_2"]),
                 ("Mermaid 导图", 1, PALETTE["green_2"]),
                 ("练习题", 3, PALETTE["green_3"]),
                 ("代码案例", 2, PALETTE["green_3"]),
                 ("语音稿", 1, PALETTE["green_2"])]
    ax_tl.text(0.06, 0.55, "生成资源", fontsize=9, fontweight="bold", color=PALETTE["neutral_dark"], transform=ax_tl.transAxes)
    x0, y0 = 0.08, 0.45
    for i, (name, count, color) in enumerate(resources):
        y = y0 - i * 0.09
        rect = FancyBboxPatch((x0, y - 0.035), 0.30, 0.07,
                              boxstyle="round,pad=0.005,rounding_size=0.01",
                              facecolor=color, edgecolor=PALETTE["neutral_dark"], linewidth=0.5,
                              transform=ax_tl.transAxes)
        ax_tl.add_patch(rect)
        ax_tl.text(x0 + 0.15, y, name, ha="center", va="center", fontsize=7, color=PALETTE["neutral_dark"], transform=ax_tl.transAxes)
        ax_tl.text(x0 + 0.34, y, f"×{count}", ha="left", va="center", fontsize=7, color=PALETTE["neutral_dark"], transform=ax_tl.transAxes)
    ax_tl.text(0.08, 0.03, "平均学习 18 min  |  练习正确率 85%",
               fontsize=8, color=PALETTE["blue_main"], fontweight="bold", transform=ax_tl.transAxes)

    # ---- 右上：翻转课堂资源推送 ----
    draw_panel_title(ax_tr, "翻转课堂资源推送", PALETTE["green_3"])
    # 教师端线框
    rect = FancyBboxPatch((0.06, 0.65), 0.42, 0.18,
                          boxstyle="round,pad=0.01,rounding_size=0.02",
                          facecolor="white", edgecolor=PALETTE["neutral_dark"], linewidth=0.8,
                          transform=ax_tr.transAxes)
    ax_tr.add_patch(rect)
    ax_tr.text(0.27, 0.77, "教师端", fontsize=9, fontweight="bold", color=PALETTE["neutral_dark"], transform=ax_tr.transAxes)
    ax_tr.text(0.10, 0.70, "课程目标：Python 文件读写", fontsize=8, color=PALETTE["neutral_dark"], transform=ax_tr.transAxes)
    ax_tr.text(0.10, 0.66, "班级人数：35", fontsize=8, color=PALETTE["neutral_dark"], transform=ax_tr.transAxes)
    # 分组柱状图 (inset axes)
    ax_tr.text(0.58, 0.78, "差异化分发", fontsize=9, fontweight="bold", color=PALETTE["neutral_dark"], transform=ax_tr.transAxes)
    inset_ax = fig.add_axes([0.74, 0.67, 0.16, 0.16])
    groups = ["基础", "标准", "进阶"]
    counts = [5, 22, 8]
    bars = inset_ax.barh(groups, counts, color=[PALETTE["neutral_mid"], PALETTE["blue_secondary"], PALETTE["gold"]],
                         edgecolor="black", linewidth=0.5)
    inset_ax.set_xlim(0, 30)
    inset_ax.set_xticks([0, 10, 20, 30])
    inset_ax.tick_params(labelsize=7)
    for spine in ["top", "right"]:
        inset_ax.spines[spine].set_visible(False)
    for bar, c in zip(bars, counts):
        inset_ax.text(c + 1, bar.get_y() + bar.get_height()/2, str(c), va="center", fontsize=7)
    # 完成率
    ax_tr.text(0.58, 0.58, "完成率：68% / 82% / 91%",
               fontsize=8, color=PALETTE["neutral_dark"], transform=ax_tr.transAxes)

    # ---- 左下：考前复习与薄弱点巩固 ----
    draw_panel_title(ax_bl, "考前复习与薄弱点巩固", PALETTE["violet"])
    # 倒计时
    ax_bl.text(0.08, 0.76, "距离考试 7 天", fontsize=11, fontweight="bold", color=PALETTE["neutral_dark"], transform=ax_bl.transAxes)
    # 热力图 4x4
    grid_ax = fig.add_axes([0.10, 0.18, 0.14, 0.18])
    np.random.seed(42)
    vals = np.random.rand(4, 4)
    vals[3, 2] = 0.18  # 薄弱点
    vals[3, 3] = 0.22
    cmap = plt.cm.RdYlGn
    for i in range(4):
        for j in range(4):
            color = cmap(vals[i, j])
            rect = plt.Rectangle((j, 3-i), 1, 1, facecolor=color, edgecolor="white", linewidth=0.5)
            grid_ax.add_patch(rect)
    grid_ax.set_xlim(0, 4)
    grid_ax.set_ylim(0, 4)
    grid_ax.axis("off")
    ax_bl.text(0.42, 0.74, "BKT 掌握度热力图（33 知识点）", fontsize=9, color=PALETTE["neutral_dark"], transform=ax_bl.transAxes)
    ax_bl.text(0.42, 0.66, "薄弱点：函数定义、文件读写", fontsize=8, color=PALETTE["red_strong"], fontweight="bold", transform=ax_bl.transAxes)
    ax_bl.text(0.42, 0.58, "推荐路径：变量 → 函数定义 → 文件读写", fontsize=8, color=PALETTE["neutral_dark"], transform=ax_bl.transAxes)
    ax_bl.text(0.08, 0.12, "高亮薄弱知识点 + 自动规划复习路径",
               fontsize=8, color=PALETTE["violet"], fontweight="bold", transform=ax_bl.transAxes)

    # ---- 右下：教师备课与学情分析 ----
    draw_panel_title(ax_br, "教师备课与学情分析", PALETTE["teal"])
    # 折线图 inset
    line_ax = fig.add_axes([0.62, 0.10, 0.28, 0.18])
    weeks = ["W1", "W2", "W3", "W4"]
    err_rate = [0.25, 0.38, 0.62, 0.45]
    line_ax.plot(weeks, err_rate, marker="o", color=PALETTE["violet"], linewidth=2, markersize=5)
    line_ax.axhline(0.60, color=PALETTE["gold"], linestyle="--", linewidth=1)
    line_ax.set_ylim(0, 1)
    line_ax.set_title("")
    line_ax.set_ylabel("错误率", fontsize=8, labelpad=10)
    line_ax.tick_params(labelsize=7)
    for spine in ["top", "right"]:
        line_ax.spines[spine].set_visible(False)
    line_ax.text(3.2, 0.63, "阈值 0.6", fontsize=7, color=PALETTE["gold"], ha="right")
    # 知识熔炉提示
    ax_br.text(0.08, 0.76, "知识熔炉触发提示", fontsize=9, fontweight="bold", color=PALETTE["neutral_dark"], transform=ax_br.transAxes)
    ax_br.text(0.08, 0.68, "“文件读写”错误率 62%，已自动触发资源重审", fontsize=8, color=PALETTE["red_strong"], transform=ax_br.transAxes)
    ax_br.text(0.08, 0.60, "资源版本：v1.0 → v1.1 → v1.2", fontsize=8, color=PALETTE["neutral_dark"], transform=ax_br.transAxes)
    ax_br.text(0.08, 0.54, "累计 1,247 次练习提交  |  生成 86 份个性化资源",
               fontsize=8, color=PALETTE["teal"], fontweight="bold", transform=ax_br.transAxes)

    finalize(fig, "fig1_application_scenarios", tight=False)


if __name__ == "__main__":
    print("Generating fig23 ...")
    make_fig23()
    print("Generating fig24 ...")
    make_fig24()
    print("Generating fig1 ...")
    make_fig1()
    print("All preview figures generated.")
