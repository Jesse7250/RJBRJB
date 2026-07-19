import os
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Polygon, Wedge
import numpy as np

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "images")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Publication-friendly rcParams with Chinese support
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
    "neutral_black": "#272727",
    "gold": "#FFD700",
    "teal": "#42949E",
    "violet": "#9A4D8E",
    "magenta": "#EA84DD",
    "orange": "#F5A623",
    "bg": "#F7F8FA",
}


def save(fig, name):
    base = os.path.join(OUTPUT_DIR, name)
    fig.savefig(base + ".svg", bbox_inches="tight", facecolor="white")
    fig.savefig(base + ".png", dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def new_fig(w=8, h=6):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.patch.set_facecolor("white")
    return fig, ax


def box(ax, x, y, w, h, text, color=PALETTE["blue_main"], text_color="white",
        radius=0.05, fontsize=10, ha="center", va="center", linewidth=1.5):
    fb = FancyBboxPatch((x - w/2, y - h/2), w, h,
                        boxstyle=f"round,pad=0.02,rounding_size={radius}",
                        facecolor=color, edgecolor=PALETTE["neutral_black"],
                        linewidth=linewidth, zorder=2)
    ax.add_patch(fb)
    ax.text(x, y, text, fontsize=fontsize, color=text_color,
            ha=ha, va=va, fontweight="bold", zorder=3)
    return fb


def arrow(ax, x1, y1, x2, y2, color=PALETTE["neutral_dark"], lw=1.5):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color=color, lw=lw,
                                connectionstyle="arc3,rad=0"),
                zorder=1)


def curved_arrow(ax, x1, y1, x2, y2, color=PALETTE["neutral_dark"], lw=1.5, rad=0.2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color=color, lw=lw,
                                connectionstyle=f"arc3,rad={rad}"),
                zorder=1)


# ---------- Figure 1: Application scenarios ----------
def fig1():
    fig, ax = new_fig(8, 6)
    ax.set_title("图 1：智慧伴学应用场景示意图", fontsize=14, fontweight="bold", pad=20)
    center = (0.5, 0.5)
    # central hexagon-ish using round box
    box(ax, center[0], center[1], 0.28, 0.22, "智慧伴学\nEduMate",
        color=PALETTE["blue_main"], radius=0.08, fontsize=14)
    scenarios = [
        (0.18, 0.78, "课后自主\n学习"),
        (0.82, 0.78, "翻转课堂\n资源推送"),
        (0.18, 0.22, "考前薄弱点\n巩固"),
        (0.82, 0.22, "教师备课与\n学情分析"),
    ]
    for x, y, t in scenarios:
        box(ax, x, y, 0.22, 0.16, t, color=PALETTE["green_2"],
            text_color=PALETTE["neutral_black"], fontsize=10)
        arrow(ax, x, y, center[0], center[1] + 0.11 if y > 0.5 else center[1] - 0.11,
              color=PALETTE["neutral_mid"], lw=1.5)
    save(fig, "fig1-application-scenarios")


# ---------- Figure 2: Overall loop ----------
def fig2():
    fig, ax = new_fig(8, 8)
    ax.set_title("图 2：总体设计闭环", fontsize=14, fontweight="bold", pad=20)
    labels = ["对话输入", "学习画像", "知识图谱", "学习路径",
              "资源生成", "练习判题", "学习评估", "画像更新"]
    n = len(labels)
    r = 0.35
    cx, cy = 0.5, 0.5
    angles = np.linspace(90, 90 - 360, n, endpoint=False) * np.pi / 180
    for i, (ang, lab) in enumerate(zip(angles, labels)):
        x = cx + r * np.cos(ang)
        y = cy + r * np.sin(ang)
        box(ax, x, y, 0.18, 0.10, lab, color=PALETTE["blue_secondary"],
            radius=0.03, fontsize=9)
        # arrow to next
        ang2 = angles[(i + 1) % n]
        x2 = cx + r * np.cos(ang2)
        y2 = cy + r * np.sin(ang2)
        # compute tangent points
        t1 = (x - 0.09 * np.cos(ang), y - 0.05 * np.sin(ang))
        t2 = (x2 + 0.09 * np.cos(ang2), y2 + 0.05 * np.sin(ang2))
        curved_arrow(ax, t1[0], t1[1], t2[0], t2[1], color=PALETTE["neutral_dark"], lw=1.5, rad=0.15)
    # central label
    ax.text(cx, cy, "以学生为中心\n的个性化闭环", fontsize=11, ha="center", va="center",
            color=PALETTE["neutral_black"], fontweight="bold")
    save(fig, "fig2-overall-loop")


# ---------- Figure 3: System architecture ----------
def fig3():
    fig, ax = new_fig(7, 8)
    ax.set_title("图 3：系统总体架构", fontsize=14, fontweight="bold", pad=20)
    layers = [
        ("前端展示层", "课程门户 / Command Center / 知识图谱 / 资源 / 对话 / 沙箱", PALETTE["green_2"]),
        ("API 网关层", "Auth / Sessions / Chat / Resources / Code / Graph / Eval", PALETTE["blue_secondary"]),
        ("多智能体编排层", "Orchestrator / Profiler / Navigator / Generator / Reviewer", PALETTE["blue_main"]),
        ("数据与知识层", "SQLite / Neo4j 知识图谱 / 资源缓存 / BKT / 行为证据", PALETTE["violet"]),
        ("大模型层", "DeepSeek / 讯飞星火 / Mock 可插拔", PALETTE["teal"]),
    ]
    y = 0.88
    w = 0.8
    h = 0.12
    for name, desc, color in layers:
        box(ax, 0.5, y, w, h, name, color=color, fontsize=12)
        ax.text(0.5, y - 0.10, desc, fontsize=8, ha="center", va="top", color=PALETTE["neutral_dark"])
        if y > 0.2:
            arrow(ax, 0.5, y - h/2 - 0.02, 0.5, y - h - 0.06, color=PALETTE["neutral_mid"], lw=2)
        y -= 0.18
    save(fig, "fig3-system-architecture")


# ---------- Figure 4: Agent architecture ----------
def fig4():
    fig, ax = new_fig(10, 7)
    ax.set_title("图 4：多智能体协同架构", fontsize=14, fontweight="bold", pad=20)
    # User
    box(ax, 0.08, 0.5, 0.12, 0.12, "学生", color=PALETTE["neutral_light"],
        text_color=PALETTE["neutral_black"], fontsize=11)
    # Orchestrator
    box(ax, 0.30, 0.5, 0.18, 0.14, "Orchestrator\n总调度", color=PALETTE["blue_main"], fontsize=11)
    arrow(ax, 0.14, 0.5, 0.21, 0.5, lw=2)
    # Four agents below
    agents = [("Profiler\n画像构建", 0.30, PALETTE["blue_secondary"]),
              ("Navigator\n路径规划", 0.50, PALETTE["teal"]),
              ("Generator\n资源生成", 0.70, PALETTE["violet"]),
              ("Reviewer\n审核/辅导/评估", 0.90, PALETTE["red_strong"])]
    for name, x, c in agents:
        box(ax, x, 0.22, 0.16, 0.14, name, color=c, fontsize=9)
        arrow(ax, 0.30, 0.5 - 0.07, x, 0.22 + 0.07, lw=1.5)
    # Reviewer internal
    box(ax, 0.90, 0.22, 0.16, 0.14, "Reviewer", color=PALETTE["red_strong"], fontsize=9)
    reviewers = [("Expert", 0.82), ("Teacher", 0.90), ("Student-Sim", 0.98), ("Guardian", 1.06)]
    for name, xx in reviewers:
        box(ax, xx, 0.06, 0.10, 0.07, name, color=PALETTE["red_1"],
            text_color=PALETTE["neutral_black"], fontsize=7)
        arrow(ax, 0.90, 0.22 - 0.07, xx, 0.06 + 0.035, lw=1)
    # Data/LLM stack on right
    box(ax, 1.25, 0.70, 0.18, 0.12, "知识图谱\nNeo4j", color=PALETTE["green_2"],
        text_color=PALETTE["neutral_black"], fontsize=9)
    box(ax, 1.25, 0.50, 0.18, 0.12, "SQLite\n数据库", color=PALETTE["green_2"],
        text_color=PALETTE["neutral_black"], fontsize=9)
    box(ax, 1.25, 0.30, 0.18, 0.12, "LLM Provider\n可插拔", color=PALETTE["green_2"],
        text_color=PALETTE["neutral_black"], fontsize=9)
    arrow(ax, 0.90, 0.5, 1.16, 0.70, lw=1.5)
    arrow(ax, 0.70, 0.22 + 0.07, 1.16, 0.30, lw=1.5)
    ax.set_xlim(-0.02, 1.38)
    save(fig, "fig4-agent-architecture")


# ---------- Figure 5: Profile evidence ----------
def fig5():
    fig, ax = new_fig(10, 6)
    ax.set_title("图 5：画像构建与证据更新流程", fontsize=14, fontweight="bold", pad=20)
    # Events column
    events = ["对话", "点击导图", "播放音频", "执行代码", "求助提示", "自主探索"]
    y0 = 0.78
    for i, ev in enumerate(events):
        box(ax, 0.12, y0 - i * 0.13, 0.16, 0.09, ev, color=PALETTE["green_2"],
            text_color=PALETTE["neutral_black"], fontsize=9)
        arrow(ax, 0.20, y0 - i * 0.13, 0.32, 0.5, color=PALETTE["neutral_mid"], lw=1)
    # Middle evidence box
    box(ax, 0.42, 0.5, 0.22, 0.18, "画像证据\n加权投票 + 阈值", color=PALETTE["blue_secondary"], fontsize=10)
    arrow(ax, 0.53, 0.59, 0.68, 0.5, lw=2)
    # Radar chart on right
    ax_radar = fig.add_axes([0.68, 0.18, 0.30, 0.64], polar=True)
    cats = ["知识水平", "认知模态", "场依存", "学习节奏", "目标导向", "错误模式"]
    N = len(cats)
    vals = [0.7, 0.6, 0.5, 0.4, 0.8, 0.3]
    vals += vals[:1]
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]
    ax_radar.plot(angles, vals, color=PALETTE["blue_main"], linewidth=2)
    ax_radar.fill(angles, vals, color=PALETTE["blue_main"], alpha=0.25)
    ax_radar.set_xticks(angles[:-1])
    ax_radar.set_xticklabels(cats, fontsize=8)
    ax_radar.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax_radar.set_yticklabels(["", "", "", "", ""])
    ax_radar.set_ylim(0, 1)
    ax_radar.set_title("学生画像六维模型", fontsize=10, pad=15)
    save(fig, "fig5-profile-evidence")


# ---------- Figure 6: Neuro-symbolic ----------
def fig6():
    fig, ax = new_fig(11, 4.5)
    ax.set_title("图 6：神经符号约束流程", fontsize=14, fontweight="bold", pad=20)
    y = 0.5
    # KG
    box(ax, 0.10, y, 0.16, 0.22, "知识图谱\n33概念 / 37边", color=PALETTE["green_3"],
        text_color=PALETTE["neutral_black"], fontsize=9)
    arrow(ax, 0.18, y, 0.30, y, lw=2)
    # Prompt
    box(ax, 0.38, y, 0.16, 0.22, "约束 Prompt\n注入", color=PALETTE["blue_secondary"], fontsize=9)
    arrow(ax, 0.46, y, 0.55, y, lw=2)
    # Generator
    box(ax, 0.63, y, 0.14, 0.22, "Generator\n生成资源", color=PALETTE["violet"], fontsize=9)
    arrow(ax, 0.70, y, 0.79, y, lw=2)
    # Validator
    box(ax, 0.88, y, 0.18, 0.22, "神经符号校验\nAST / 白名单 / 超纲", color=PALETTE["red_strong"], fontsize=9)
    # Output
    arrow(ax, 0.97, y, 1.08, y, lw=2)
    box(ax, 1.17, y, 0.14, 0.22, "可用\n资源", color=PALETTE["teal"], fontsize=9)
    save(fig, "fig6-neuro-symbolic")


# ---------- Figure 7: Resource pipeline ----------
def fig7():
    fig, ax = new_fig(12, 6)
    ax.set_title("图 7：资源生成与审核流程", fontsize=14, fontweight="bold", pad=20)
    y = 0.55
    # Input
    box(ax, 0.08, y, 0.14, 0.18, "画像 +\n目标概念", color=PALETTE["neutral_light"],
        text_color=PALETTE["neutral_black"], fontsize=9)
    arrow(ax, 0.15, y, 0.23, y, lw=1.5)
    # Navigator
    box(ax, 0.30, y, 0.12, 0.16, "Navigator\n路径规划", color=PALETTE["teal"], fontsize=8)
    arrow(ax, 0.36, y, 0.43, y, lw=1.5)
    # Generator
    box(ax, 0.50, y, 0.14, 0.20, "Generator\n5类资源", color=PALETTE["violet"], fontsize=8)
    # Validator
    arrow(ax, 0.57, y, 0.66, y, lw=1.5)
    box(ax, 0.73, y, 0.14, 0.18, "神经符号\n校验", color=PALETTE["red_strong"], fontsize=8)
    # Debate
    arrow(ax, 0.80, y, 0.89, y, lw=1.5)
    box(ax, 0.96, y, 0.14, 0.20, "4-Prompt\n辩论议会", color=PALETTE["blue_main"], fontsize=8)
    # Decision split
    arrow(ax, 1.03, y, 1.12, y, lw=1.5)
    # Passed output
    box(ax, 1.22, 0.78, 0.12, 0.14, "通过/修改\n缓存输出", color=PALETTE["green_3"],
        text_color=PALETTE["neutral_black"], fontsize=8)
    arrow(ax, 1.18, 0.62, 1.22, 0.71, lw=1.5)
    # Rejected revise
    box(ax, 1.22, 0.32, 0.12, 0.14, "拒绝\n返回修订", color=PALETTE["red_1"],
        text_color=PALETTE["neutral_black"], fontsize=8)
    arrow(ax, 1.18, 0.48, 1.22, 0.39, lw=1.5)
    # Loop back
    curved_arrow(ax, 1.22, 0.32, 0.50, 0.45, color=PALETTE["red_strong"], lw=1.5, rad=-0.35)
    ax.set_xlim(-0.02, 1.32)
    save(fig, "fig7-resource-pipeline")


# ---------- Figure 8: Learning path ----------
def fig8():
    fig, ax = new_fig(9, 5)
    ax.set_title("图 8：个性化学习路径规划", fontsize=14, fontweight="bold", pad=20)
    nodes = {
        "Python简介": (0.12, 0.5),
        "变量与赋值": (0.30, 0.7),
        "基本数据类型": (0.30, 0.3),
        "条件语句": (0.50, 0.7),
        "循环结构": (0.50, 0.3),
        "函数定义": (0.72, 0.5),
        "文件读写": (0.90, 0.5),
    }
    edges = [
        ("Python简介", "变量与赋值"),
        ("Python简介", "基本数据类型"),
        ("变量与赋值", "条件语句"),
        ("基本数据类型", "循环结构"),
        ("条件语句", "函数定义"),
        ("循环结构", "函数定义"),
        ("函数定义", "文件读写"),
    ]
    path = ["Python简介", "变量与赋值", "条件语句", "函数定义", "文件读写"]
    path_set = set([(path[i], path[i+1]) for i in range(len(path)-1)])
    for a, b in edges:
        x1, y1 = nodes[a]
        x2, y2 = nodes[b]
        col = PALETTE["gold"] if (a, b) in path_set else PALETTE["neutral_light"]
        lw = 2.5 if (a, b) in path_set else 1.5
        arrow(ax, x1, y1, x2, y2, color=col, lw=lw)
    for name, (x, y) in nodes.items():
        in_path = name in path
        col = PALETTE["blue_main"] if in_path else PALETTE["neutral_mid"]
        box(ax, x, y, 0.14, 0.12, name, color=col, fontsize=8)
    # legend
    ax.plot([], [], color=PALETTE["gold"], lw=2.5, label="推荐学习路径")
    ax.plot([], [], color=PALETTE["neutral_light"], lw=1.5, label="知识图谱依赖")
    ax.legend(loc="upper right", fontsize=9)
    save(fig, "fig8-learning-path")


# ---------- Figure 9: Socratic stages ----------
def fig9():
    fig, ax = new_fig(8, 8)
    ax.set_title("图 9：苏格拉底辅导五阶段", fontsize=14, fontweight="bold", pad=20)
    stages = [
        ("澄清", "这个错误提示你注意到了\n什么关键信息？"),
        ("假设探查", "你觉得这个知识点的\n哪个特性可能导致错误？"),
        ("证据检查", "你能从代码中找到\n支持或反驳的线索吗？"),
        ("反例验证", "如果换一个输入，\n代码还能正确运行吗？"),
        ("收敛", "所以本质上，\n这个问题应该怎么解决？"),
    ]
    y = 0.88
    for i, (stage, q) in enumerate(stages):
        box(ax, 0.5, y, 0.70, 0.12, f"{i+1}. {stage}\n{q}", color=PALETTE["blue_secondary"],
            fontsize=9, radius=0.04)
        if i < len(stages) - 1:
            arrow(ax, 0.5, y - 0.06, 0.5, y - 0.12, lw=2)
        y -= 0.17
    save(fig, "fig9-socratic-stages")


# ---------- Figure 10: Digital human ----------
def fig10():
    fig, ax = new_fig(6, 8)
    ax.set_title("图 10：数字人助教界面效果", fontsize=14, fontweight="bold", pad=20)
    # Teacher face
    cx, cy = 0.5, 0.62
    # Halos
    halo1 = Circle((cx, cy), 0.22, fill=False, edgecolor=PALETTE["gold"], lw=2, alpha=0.7)
    halo2 = Circle((cx, cy), 0.26, fill=False, edgecolor=PALETTE["violet"], lw=1.5, alpha=0.5)
    ax.add_patch(halo1)
    ax.add_patch(halo2)
    face = Circle((cx, cy), 0.18, facecolor=PALETTE["neutral_light"], edgecolor=PALETTE["neutral_dark"], lw=2)
    ax.add_patch(face)
    # Eyes
    ax.plot([cx-0.05, cx-0.05], [cy+0.02, cy+0.02], color=PALETTE["neutral_black"], lw=3)
    ax.plot([cx+0.05, cx+0.05], [cy+0.02, cy+0.02], color=PALETTE["neutral_black"], lw=3)
    # Mouth smile
    smile = mpatches.Arc((cx, cy-0.02), 0.08, 0.06, angle=0, theta1=200, theta2=340,
                         color=PALETTE["red_strong"], lw=2)
    ax.add_patch(smile)
    # Sound rings
    for r in [0.30, 0.35, 0.40]:
        ring = Circle((cx, cy), r, fill=False, edgecolor=PALETTE["gold"], lw=1, alpha=0.4)
        ax.add_patch(ring)
    # Audio bars
    bar_x = np.linspace(0.35, 0.65, 7)
    for bx in bar_x:
        h = np.random.uniform(0.03, 0.08)
        rect = mpatches.Rectangle((bx - 0.015, cy - 0.38), 0.03, h,
                                  facecolor=PALETTE["blue_secondary"], alpha=0.8)
        ax.add_patch(rect)
    # Buttons
    box(ax, 0.5, 0.18, 0.30, 0.08, "朗读讲解", color=PALETTE["blue_main"], fontsize=11)
    ax.text(0.5, 0.10, "语速：0.5x   1x   2x", fontsize=9, ha="center", va="center",
            color=PALETTE["neutral_dark"])
    ax.text(0.5, 0.04, "讲解知识点：变量与赋值", fontsize=9, ha="center", va="center",
            color=PALETTE["neutral_mid"])
    save(fig, "fig10-digital-human")


if __name__ == "__main__":
    fig1()
    fig2()
    fig3()
    fig4()
    fig5()
    fig6()
    fig7()
    fig8()
    fig9()
    fig10()
    print("Generated 10 figures in", OUTPUT_DIR)
