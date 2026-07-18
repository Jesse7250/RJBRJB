"""
generate_engineering_figures.py
================================
按软件工程/学术论文规范重新绘制 EduHive 设计文档配图（v2 风格统一版）。

输出：
  docs/images/fig{1..16}-*.svg  （可编辑矢量）
  docs/images/fig{1..16}-*.png  （300 dpi 预览）

设计原则：
  - 统一配色、线宽、圆角、字号层级；
  - 所有矩形节点先计算文字是否溢出，必要时自动换行；
  - 流程图采用标准 ANSI/ISO 符号，箭头只接在节点边缘；
  - 真实 UI 截图统一加标题条，与矢量图风格一致。
"""
import math
import textwrap
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import (
    FancyBboxPatch,
    FancyArrowPatch,
    Rectangle,
    Circle,
    Polygon,
)
from matplotlib.lines import Line2D
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ──────────────────────────────────────────────────────────────────────────────
# 全局样式
# ──────────────────────────────────────────────────────────────────────────────
mpl.use("Agg")
mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Microsoft YaHei", "Arial", "Helvetica", "DejaVu Sans"],
    "svg.fonttype": "none",
    "pdf.fonttype": 42,
    "font.size": 9,
    "axes.linewidth": 0.8,
})

OUT_DIR = Path(__file__).parent.parent / "docs" / "images"
OUT_DIR.mkdir(parents=True, exist_ok=True)
DPI = 300

# 统一配色：低饱和、打印安全、与 UI 截图不冲突
PALETTE = {
    "bg": "#FAFAFA",
    "panel": "#FFFFFF",
    "primary": "#1E5AA8",      # 深蓝：核心/编排
    "secondary": "#3B82F6",    # 亮蓝：处理节点
    "teal": "#0D9488",         # 青绿：数据/图谱
    "accent": "#16A34A",       # 绿：通过/成功
    "warm": "#EA580C",         # 橙：警告/拒绝
    "danger": "#DC2626",       # 红：错误/熔断
    "neutral": "#4B5563",      # 灰：文字/边框
    "neutral_light": "#D1D5DB",
    "text": "#1F2937",
    "white": "#FFFFFF",
    # 泳道背景
    "lane_user": "#E8F0FE",
    "lane_frontend": "#E6F4F1",
    "lane_api": "#FFF7ED",
    "lane_agent": "#F3E8FF",
    "lane_data": "#ECFEFF",
    "lane_external": "#F3F4F6",
    "lane_validation": "#F0FDF4",
}


# ──────────────────────────────────────────────────────────────────────────────
# 文字工具
# ──────────────────────────────────────────────────────────────────────────────
def fit_text(text: str, max_chars: int) -> str:
    """按最大字符数自动插入换行；优先按空格分词，长英文词再按字符截断。"""
    lines = []
    for raw_line in text.split("\n"):
        if len(raw_line) <= max_chars:
            lines.append(raw_line)
            continue
        # 先按空格分词，保留中文单字作为独立词
        tokens = []
        buf = ""
        for ch in raw_line:
            if ch == " ":
                if buf:
                    tokens.append(buf)
                    buf = ""
                tokens.append(" ")
            else:
                buf += ch
        if buf:
            tokens.append(buf)
        # 将超长词再拆分
        split_tokens = []
        for tok in tokens:
            if tok == " ":
                split_tokens.append(tok)
                continue
            while len(tok) > max_chars:
                split_tokens.append(tok[:max_chars])
                tok = tok[max_chars:]
            if tok:
                split_tokens.append(tok)
        # 组装行
        cur_line = ""
        for tok in split_tokens:
            if tok == " ":
                if cur_line and not cur_line.endswith(" "):
                    cur_line += " "
                continue
            sep = " " if cur_line and not cur_line.endswith(" ") else ""
            candidate = cur_line + sep + tok if cur_line else tok
            if len(candidate) > max_chars and cur_line:
                lines.append(cur_line.rstrip())
                cur_line = tok
            else:
                cur_line = candidate
        if cur_line:
            lines.append(cur_line.rstrip())
    return "\n".join(lines)


def clean_ax(ax):
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    ax.set_facecolor(PALETTE["bg"])


# ──────────────────────────────────────────────────────────────────────────────
# 基础绘图原语
# ──────────────────────────────────────────────────────────────────────────────
def rounded_box(ax, xy, w, h, text, facecolor, edgecolor=None, text_color="white",
                fontsize=8, radius=0.015, lw=1.2, bold=False, ha="center", va="center",
                max_chars=0):
    """圆角矩形节点，支持自动换行避免溢出。"""
    edgecolor = edgecolor or PALETTE["text"]
    if max_chars > 0:
        text = fit_text(text, max_chars)
    box = FancyBboxPatch(
        xy, w, h, boxstyle=f"round,pad=0,rounding_size={radius * 100}",
        facecolor=facecolor, edgecolor=edgecolor, linewidth=lw,
        transform=ax.transData, clip_on=False,
    )
    ax.add_patch(box)
    weight = "bold" if bold else "normal"
    ax.text(xy[0] + w / 2, xy[1] + h / 2, text, ha=ha, va=va,
            fontsize=fontsize, color=text_color, weight=weight,
            wrap=False, linespacing=1.15)
    return box


def process_box(ax, xy, w, h, text, facecolor=PALETTE["panel"],
                edgecolor=PALETTE["primary"], fontsize=8, max_chars=0):
    """标准处理矩形（DFD/流程图）。"""
    rounded_box(ax, xy, w, h, text, facecolor=facecolor, edgecolor=edgecolor,
                text_color=PALETTE["text"], fontsize=fontsize, radius=0.012,
                max_chars=max_chars)


def external_entity(ax, xy, w, h, text, facecolor=PALETTE["panel"],
                    edgecolor=PALETTE["neutral"], fontsize=8, max_chars=0):
    """外部实体：普通矩形。"""
    rounded_box(ax, xy, w, h, text, facecolor=facecolor, edgecolor=edgecolor,
                text_color=PALETTE["text"], fontsize=fontsize, radius=0.005,
                max_chars=max_chars)


def data_store(ax, xy, w, h, text, facecolor=PALETTE["panel"],
               edgecolor=PALETTE["neutral"], fontsize=8, max_chars=0):
    """数据存储：右侧开口矩形。"""
    x, y = xy
    ax.plot([x, x], [y, y + h], color=edgecolor, lw=1.2)
    ax.plot([x, x + w], [y + h, y + h], color=edgecolor, lw=1.2)
    ax.plot([x, x + w], [y, y], color=edgecolor, lw=1.2)
    ax.plot([x + w, x + w], [y, y + h], color=edgecolor, lw=1.2, linestyle="--")
    if max_chars > 0:
        text = fit_text(text, max_chars)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fontsize, color=PALETTE["text"], linespacing=1.1)


def decision(ax, xy, size, text, facecolor=PALETTE["panel"],
             edgecolor=PALETTE["warm"], fontsize=8):
    """菱形判断节点。"""
    x, y = xy
    d = size
    poly = Polygon([(x, y + d / 2), (x + d / 2, y + d),
                    (x + d, y + d / 2), (x + d / 2, y)],
                   facecolor=facecolor, edgecolor=edgecolor, linewidth=1.5)
    ax.add_patch(poly)
    ax.text(x + d / 2, y + d / 2, text, ha="center", va="center",
            fontsize=fontsize, color=PALETTE["text"], weight="bold")
    return poly


def arrow(ax, start, end, text=None, color=PALETTE["text"], lw=1.2,
          fontsize=8, connectionstyle="arc3,rad=0", text_offset=(0, 1.2),
          arrowstyle="->", mutation_scale=12):
    """带可选标签的箭头，标签自动加半透背景避免压线。"""
    arr = FancyArrowPatch(
        start, end, arrowstyle=arrowstyle, color=color, lw=lw,
        connectionstyle=connectionstyle, mutation_scale=mutation_scale,
        transform=ax.transData, clip_on=False,
    )
    ax.add_patch(arr)
    if text:
        mx = (start[0] + end[0]) / 2 + text_offset[0]
        my = (start[1] + end[1]) / 2 + text_offset[1]
        ax.text(mx, my, text, fontsize=fontsize, color=color,
                ha="center", va="bottom",
                bbox=dict(boxstyle="round,pad=0.2", facecolor=PALETTE["bg"],
                          edgecolor="none", alpha=0.9))
    return arr


def orthogonal_arrow(ax, points, text=None, color=PALETTE["text"], lw=1.2,
                     fontsize=8, text_offset=(0, 1.2)):
    """绘制折线箭头（正交路径），并在路径中点附近标注文本。"""
    # 绘制线段
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    ax.plot(xs, ys, color=color, lw=lw, solid_capstyle="round")
    # 终点箭头
    x0, y0 = points[-2]
    x1, y1 = points[-1]
    ang = math.atan2(y1 - y0, x1 - x0)
    head_len = 1.2
    head_ang = 0.35
    p_a = (x1 - head_len * math.cos(ang - head_ang),
           y1 - head_len * math.sin(ang - head_ang))
    p_b = (x1 - head_len * math.cos(ang + head_ang),
           y1 - head_len * math.sin(ang + head_ang))
    tri = Polygon([p_a, p_b, (x1, y1)], facecolor=color, edgecolor=color)
    ax.add_patch(tri)
    if text:
        # 按路径长度找中点所在的线段
        dists = [math.hypot(points[i][0] - points[i - 1][0],
                            points[i][1] - points[i - 1][1])
                 for i in range(1, len(points))]
        total = sum(dists)
        half = total / 2
        acc = 0
        mx, my = points[0]
        for i, d in enumerate(dists, start=1):
            if acc + d >= half:
                ratio = (half - acc) / d
                x0, y0 = points[i - 1]
                x1, y1 = points[i]
                mx = x0 + (x1 - x0) * ratio
                my = y0 + (y1 - y0) * ratio
                break
            acc += d
        ax.text(mx + text_offset[0], my + text_offset[1], text,
                fontsize=fontsize, color=color, ha="center", va="bottom",
                bbox=dict(boxstyle="round,pad=0.2", facecolor=PALETTE["bg"],
                          edgecolor="none", alpha=0.9))


def lane_background(ax, y, height, color, label, fontsize=10, bold=True):
    """水平泳道背景。"""
    rect = Rectangle((0, y), 100, height, facecolor=color,
                      edgecolor=PALETTE["neutral_light"], linewidth=1,
                      linestyle="--", transform=ax.transData, clip_on=False,
                      zorder=0)
    ax.add_patch(rect)
    weight = "bold" if bold else "normal"
    ax.text(1.5, y + height / 2, label, ha="left", va="center",
            fontsize=fontsize, color=PALETTE["text"], weight=weight,
            rotation=90, rotation_mode="anchor")


def set_title(ax, text, fontsize=14):
    ax.set_title(text, fontsize=fontsize, fontweight="bold", pad=15, color=PALETTE["text"])


def save(fig, name):
    base = OUT_DIR / name
    fig.savefig(base.with_suffix(".svg"), bbox_inches="tight", pad_inches=0.15)
    fig.savefig(base.with_suffix(".png"), dpi=DPI, bbox_inches="tight", pad_inches=0.15)
    print(f"Saved {base.name}.svg/.png")
    plt.close(fig)


# ──────────────────────────────────────────────────────────────────────────────
# 真实截图统一标题条处理
# ──────────────────────────────────────────────────────────────────────────────
SCREENSHOT_TITLES = {
    "fig5-profile-evidence": "图 5：学习画像与证据追踪",
    "fig8-learning-path": "图 8：知识图谱与学习路径规划",
    "fig9-socratic-stages": "图 9：苏格拉底辅导五阶段流程",
    "fig10-bkt-heatmap": "图 10：BKT 掌握度热力图",
    "fig12-course-workspace": "图 12：课程工作台主界面",
    "fig13-code-sandbox": "图 13：代码沙箱运行与自动判题",
}


def screenshot_figure(src_name: str, dst_name: str):
    """给真实 UI 截图顶部加统一标题条，输出到 docs/images。"""
    src = Path(__file__).parent.parent / "docs" / "test-screenshots" / src_name
    dst = OUT_DIR / f"{dst_name}.png"
    img = Image.open(src).convert("RGB")
    w, h = img.size
    banner_h = int(h * 0.075)
    # 新建画布：顶部标题条 + 原图
    new = Image.new("RGB", (w, h + banner_h), PALETTE["bg"])
    draw = ImageDraw.Draw(new)
    # 标题条背景
    draw.rectangle([0, 0, w, banner_h], fill=PALETTE["primary"])
    # 字体
    try:
        font = ImageFont.truetype("msyh.ttc", int(banner_h * 0.45))
    except Exception:
        try:
            font = ImageFont.truetype("Microsoft YaHei.ttf", int(banner_h * 0.45))
        except Exception:
            font = ImageFont.load_default()
    title = SCREENSHOT_TITLES[dst_name]
    bbox = draw.textbbox((0, 0), title, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text(((w - tw) / 2, (banner_h - th) / 2), title,
              fill=PALETTE["white"], font=font)
    # 粘贴原图
    new.paste(img, (0, banner_h))
    # 加细边框
    draw.rectangle([0, banner_h, w - 1, new.height - 1], outline=PALETTE["neutral_light"], width=2)
    new.save(dst, "PNG", dpi=(DPI, DPI))
    print(f"Saved {dst.name}")



# ──────────────────────────────────────────────────────────────────────────────
# 图 1：应用场景用例图（rich cards）
# ──────────────────────────────────────────────────────────────────────────────
def fig1_application_scenarios():
    fig, ax = plt.subplots(figsize=(10, 7))
    clean_ax(ax)

    # 中心中枢
    hub = Circle((50, 50), 11, facecolor=PALETTE["primary"],
                 edgecolor=PALETTE["text"], linewidth=2, clip_on=False)
    ax.add_patch(hub)
    ax.text(50, 52, "智学蜂巢", ha="center", va="center",
            fontsize=12, color=PALETTE["white"], weight="bold")
    ax.text(50, 48, "EduHive", ha="center", va="center",
            fontsize=10, color=PALETTE["white"])

    # 四个场景卡片：标题 + 3 条价值点
    scenarios = [
        (12, 70, "课后自主学习", "AI 个性化讲义/练习\n多智能体苏格拉底辅导\n自动规划薄弱点路径", PALETTE["secondary"]),
        (62, 70, "翻转课堂资源推送", "课前微课 + 预习诊断\n课堂实时数据看板\n课后分层作业", PALETTE["teal"]),
        (12, 20, "考前薄弱点巩固", "BKT 掌握度诊断\n错题重练 + 变式题\n考前冲刺路径", PALETTE["accent"]),
        (62, 20, "教师备课与学情分析", "班级掌握度热力图\n资源版本演进\nAI 辅助备课建议", PALETTE["warm"]),
    ]
    card_w, card_h = 30, 24
    for x, y, title, body, color in scenarios:
        rounded_box(ax, (x, y), card_w, card_h, "",
                    facecolor=PALETTE["panel"], edgecolor=color, lw=2, radius=0.02)
        rounded_box(ax, (x + 1, y + card_h - 7), card_w - 2, 6, title,
                    facecolor=color, fontsize=9, radius=0.015, bold=True)
        ax.text(x + card_w / 2, y + card_h / 2 - 2, body,
                ha="center", va="center", fontsize=8, color=PALETTE["text"],
                linespacing=1.3)
        # 卡片指向中枢
        cx = x + card_w if x < 50 else x
        cy = y + card_h / 2
        arr_x = 50 - 11 if x < 50 else 50 + 11
        arr_y = 50 + (cy - 50) * 0.4
        arrow(ax, (cx, cy), (arr_x, arr_y), color=color, lw=1.3,
              connectionstyle="arc3,rad=0.1")

    # 参与者
    external_entity(ax, (2, 40), 10, 20, "学生", fontsize=10)
    external_entity(ax, (88, 40), 10, 20, "教师", fontsize=10)

    # 参与者到场景
    arrow(ax, (12, 55), (12, 73), color=PALETTE["neutral"], lw=1)
    arrow(ax, (12, 45), (12, 42), color=PALETTE["neutral"], lw=1)
    arrow(ax, (88, 55), (88, 73), color=PALETTE["neutral"], lw=1)
    arrow(ax, (88, 45), (88, 42), color=PALETTE["neutral"], lw=1)

    set_title(ax, "图 1：智学蜂巢应用场景示意图")
    save(fig, "fig1-application-scenarios")


# ──────────────────────────────────────────────────────────────────────────────
# 图 2：系统总体数据闭环（rich ring with labeled flows）
# ──────────────────────────────────────────────────────────────────────────────
def fig2_overall_loop():
    fig, ax = plt.subplots(figsize=(9, 9))
    clean_ax(ax)

    center = (50, 50)
    radius = 32
    stages = [
        ("对话输入", "文本/语音问题"),
        ("学习画像", "6 维画像证据"),
        ("知识图谱", "Neo4j / GraphRAG"),
        ("学习路径", "A* 路径规划"),
        ("资源生成", "5 类资源包"),
        ("练习判题", "代码/选择/填空"),
        ("学习评估", "BKT 掌握度"),
        ("画像更新", "证据聚合投票"),
    ]
    n = len(stages)
    angles = np.linspace(90, 90 - 360, n + 1)[:-1]

    nodes = []
    for ang, (st, sub) in zip(angles, stages):
        rad = math.radians(ang)
        x = center[0] + radius * math.cos(rad)
        y = center[1] + radius * math.sin(rad)
        nodes.append((x, y))
        rounded_box(ax, (x - 12, y - 6), 24, 12, f"{st}\n{sub}",
                    facecolor=PALETTE["secondary"], fontsize=7.5, radius=0.02,
                    max_chars=12)

    # 主循环箭头
    for i in range(n):
        x1, y1 = nodes[i]
        x2, y2 = nodes[(i + 1) % n]
        ang1 = math.atan2(y2 - y1, x2 - x1)
        off = 12
        arrow(ax, (x1 + off * math.cos(ang1), y1 + off * math.sin(ang1)),
              (x2 - off * math.cos(ang1), y2 - off * math.sin(ang1)),
              color=PALETTE["neutral"], lw=1.2, connectionstyle="arc3,rad=0.15")

    # 中心
    rounded_box(ax, (36, 40), 28, 20,
                "以学生为中心的\n个性化学习闭环",
                facecolor=PALETTE["primary"], fontsize=11, radius=0.02, bold=True)

    set_title(ax, "图 2：系统总体数据闭环")
    save(fig, "fig2-overall-loop")



# ──────────────────────────────────────────────────────────────────────────────
# 图 3：系统总体五层架构（分层清晰、无溢出）
# ──────────────────────────────────────────────────────────────────────────────
def fig3_system_architecture():
    fig, ax = plt.subplots(figsize=(11, 7.5))
    clean_ax(ax)

    layers = [
        (82, "L1 用户接入", PALETTE["lane_user"],
         ["Web 浏览器", "课程门户", "数字人浮窗", "语音输入"]),
        (63, "L2 前端展示", PALETTE["lane_frontend"],
         ["React + Vite + TS", "ChatPanel", "Knowledge\nGraph", "Resource\nViewer",
          "Code\nSandbox", "Digital\nHuman", "Progress"]),
        (44, "L3 API 网关", PALETTE["lane_api"],
         ["FastAPI", "/auth", "/sessions", "/resources", "/graph", "/code",
          "/evaluation", "/plan", "/tts"]),
        (25, "L4 智能体与服务", PALETTE["lane_agent"],
         ["Orchestrator", "Profiler", "Navigator", "Generator", "Reviewer",
          "LLM / KG\n/ Cache", "BKT /\nExecutor /\nNeuro-Symbolic"]),
        (6, "L5 数据与基础设施", PALETTE["lane_data"],
         ["SQLite\n业务库", "Neo4j\n知识图谱", "资源缓存",
          "Docker\nCompose", "DeepSeek /\nSpark /\nMock"]),
    ]

    lane_h = 17
    max_chars_by_layer = {"L1": 12, "L2": 12, "L3": 12, "L4": 15, "L5": 12}
    for y, label, color, items in layers:
        lane_background(ax, y, lane_h, color, label, fontsize=8)
        n = len(items)
        gap = 1.4
        total_gap = gap * (n + 1)
        w = (96 - total_gap) / n
        x = 2 + gap
        max_chars = max_chars_by_layer[label.split()[0]]
        for it in items:
            plain_len = len(it.replace("\n", ""))
            fs = 6.0 if plain_len > 22 else (6.5 if plain_len > 12 else 7.5)
            rounded_box(ax, (x, y + 3), w, lane_h - 6, it,
                        facecolor=PALETTE["panel"], edgecolor=PALETTE["neutral"],
                        text_color=PALETTE["text"], fontsize=fs, radius=0.01,
                        max_chars=max_chars)
            x += w + gap

    # 层间垂直箭头
    for y, _, _, _ in layers[:-1]:
        arrow(ax, (50, y), (50, y - 2.5), color=PALETTE["neutral"], lw=1.5,
              arrowstyle="->", mutation_scale=14)

    set_title(ax, "图 3：系统总体五层架构")
    save(fig, "fig3-system-architecture")


# ──────────────────────────────────────────────────────────────────────────────
# 图 4：多智能体协同架构（箭头清晰、议会独立）
# ──────────────────────────────────────────────────────────────────────────────
def fig4_agent_architecture():
    fig, ax = plt.subplots(figsize=(11, 7.5))
    clean_ax(ax)

    lane_background(ax, 82, 16, PALETTE["lane_user"], "用户层", fontsize=9)
    lane_background(ax, 62, 18, PALETTE["lane_api"], "编排层", fontsize=9)
    lane_background(ax, 36, 24, PALETTE["lane_agent"], "执行角色层", fontsize=9)
    lane_background(ax, 6, 28, PALETTE["lane_data"], "外部依赖", fontsize=9)

    # 用户
    external_entity(ax, (45, 86), 10, 8, "学生/教师", fontsize=9)

    # Orchestrator
    rounded_box(ax, (38, 65), 24, 12,
                "Orchestrator\n意图识别 · 路由 · 熔断降级",
                facecolor=PALETTE["primary"], fontsize=9, radius=0.02)

    # 执行角色
    agents = [
        (6, 50, "Profiler\n画像构建"),
        (25, 50, "Navigator\n路径规划"),
        (44, 50, "Generator\n资源生成"),
        (63, 50, "Reviewer\n审核+辅导+评估"),
    ]
    for x, y, t in agents:
        rounded_box(ax, (x, y), 16, 10, t, facecolor=PALETTE["secondary"],
                    fontsize=8, radius=0.015)

    # Debate Council（Reviewer 右侧，竖排）
    rev_x = 83
    ax.text(rev_x + 6, 61, "Debate Council", ha="center", va="bottom",
            fontsize=9, color=PALETTE["primary"], weight="bold")
    reviewers = [
        (rev_x, 55, "Expert\n专家视角"),
        (rev_x, 46, "Teacher\n教师视角"),
        (rev_x, 37, "Student-Sim\n学生模拟"),
        (rev_x, 28, "Guardian\n安全守护"),
    ]
    for x, y, t in reviewers:
        rounded_box(ax, (x, y), 14, 7, t, facecolor=PALETTE["panel"],
                    edgecolor=PALETTE["secondary"], text_color=PALETTE["text"],
                    fontsize=7, radius=0.01, max_chars=12)

    # 外部依赖
    deps = [
        (8, 14, "Neo4j\n知识图谱"),
        (36, 14, "SQLite\n业务数据"),
        (64, 14, "LLM Provider\nDeepSeek / Spark / Mock"),
    ]
    for x, y, t in deps:
        mc = 20 if "LLM" in t else 12
        data_store(ax, (x, y), 20, 10, t, fontsize=8, max_chars=mc)

    # 主要箭头
    arrow(ax, (50, 86), (50, 77), color=PALETTE["text"], lw=1.5)
    arrow(ax, (50, 65), (50, 62), color=PALETTE["text"], lw=1.5)

    # Orchestrator -> agents（水平散开）
    for x, y, _ in agents:
        arrow(ax, (50, 62), (x + 8, 60), color=PALETTE["text"], lw=1.2)

    # Reviewer -> Debate Council
    arrow(ax, (79, 55), (83, 58.5), color=PALETTE["secondary"], lw=1)
    arrow(ax, (79, 52), (83, 49.5), color=PALETTE["secondary"], lw=1)
    arrow(ax, (79, 49), (83, 40.5), color=PALETTE["secondary"], lw=1)
    arrow(ax, (79, 46), (83, 31.5), color=PALETTE["secondary"], lw=1)

    # agents -> 依赖
    arrow(ax, (14, 50), (18, 24), text="查询", fontsize=7,
          color=PALETTE["neutral"], lw=1, text_offset=(0, 0.5))
    arrow(ax, (33, 50), (46, 24), text="读写", fontsize=7,
          color=PALETTE["neutral"], lw=1, text_offset=(0, 0.5))
    orthogonal_arrow(ax, [(52, 50), (52, 26), (74, 26), (74, 24)],
                     text="调用", fontsize=7, color=PALETTE["neutral"],
                     lw=1, text_offset=(0, 1.0))
    arrow(ax, (71, 50), (74, 24), text="审核", fontsize=7,
          color=PALETTE["neutral"], lw=1, text_offset=(0, 0.5))

    set_title(ax, "图 4：多智能体协同架构")
    save(fig, "fig4-agent-architecture")



# ──────────────────────────────────────────────────────────────────────────────
# 图 6：神经符号约束流程（泳道 + 清晰分支）
# ──────────────────────────────────────────────────────────────────────────────
def fig6_neuro_symbolic():
    fig, ax = plt.subplots(figsize=(11, 6.5))
    clean_ax(ax)

    lane_background(ax, 62, 35, PALETTE["lane_data"], "约束提取", fontsize=9)
    lane_background(ax, 32, 28, PALETTE["lane_agent"], "LLM 生成", fontsize=9)
    lane_background(ax, 0, 30, PALETTE["lane_validation"], "生成后校验", fontsize=9)

    # 约束提取
    rounded_box(ax, (6, 74), 18, 12, "知识图谱\nGraphRAG",
                facecolor=PALETTE["teal"], fontsize=8)
    constraints = [
        (4, 60, "前置知识"),
        (17, 60, "难度等级"),
        (30, 60, "易错点"),
        (4, 52, "禁止概念"),
        (17, 52, "允许模块"),
    ]
    for x, y, t in constraints:
        rounded_box(ax, (x, y), 11, 6, t, facecolor=PALETTE["panel"],
                    edgecolor=PALETTE["teal"], text_color=PALETTE["text"],
                    fontsize=7, radius=0.01)

    # Generator
    rounded_box(ax, (40, 50), 18, 16,
                "Generator\n(LLM 资源生成)",
                facecolor=PALETTE["primary"], fontsize=9, radius=0.02)

    # 校验器（单列，间距更大）
    validators = [
        (68, 70, "AST 语法检查"),
        (68, 58, "导入白名单"),
        (68, 46, "未学概念检测"),
        (68, 34, "事实一致性校验"),
    ]
    for x, y, t in validators:
        rounded_box(ax, (x, y), 18, 10, t, facecolor=PALETTE["panel"],
                    edgecolor=PALETTE["accent"], text_color=PALETTE["text"],
                    fontsize=8, radius=0.01)

    # 输出 / 反馈
    rounded_box(ax, (40, 12), 18, 10, "资源输出",
                facecolor=PALETTE["accent"], fontsize=9)
    rounded_box(ax, (68, 12), 18, 10, "反馈修订",
                facecolor=PALETTE["warm"], fontsize=9)

    # 约束 -> Generator
    arrow(ax, (34, 54), (40, 54), text="约束注入", fontsize=7)

    # Generator -> 校验器（从 Generator 右侧到各校验器左侧）
    arrow(ax, (58, 58), (68, 75), fontsize=7)
    arrow(ax, (58, 54), (68, 63), fontsize=7)
    arrow(ax, (58, 50), (68, 51), fontsize=7)
    arrow(ax, (58, 46), (68, 39), fontsize=7)

    # 校验结果分支（正交路径避免交叉，出口居中）
    orthogonal_arrow(ax, [(72, 39), (55, 39), (55, 22), (49, 22)],
                     text="通过", fontsize=8,
                     color=PALETTE["accent"], text_offset=(0, 1.5))
    orthogonal_arrow(ax, [(82, 39), (82, 22), (77, 22)],
                     text="不通过", fontsize=8,
                     color=PALETTE["danger"], text_offset=(1.2, 1.2))

    # 反馈修订 -> Generator（从下方绕回）
    orthogonal_arrow(ax, [(68, 17), (55, 17), (55, 48), (58, 48)],
                     text="修订反馈", fontsize=8,
                     color=PALETTE["danger"], lw=1.2,
                     text_offset=(-2.5, 0))

    set_title(ax, "图 6：神经符号约束流程")
    save(fig, "fig6-neuro-symbolic")


# ──────────────────────────────────────────────────────────────────────────────
# 图 7：资源生成与审核流程（ANSI 流程图）
# ──────────────────────────────────────────────────────────────────────────────
def fig7_resource_pipeline():
    fig, ax = plt.subplots(figsize=(12, 6.5))
    clean_ax(ax)

    # 顶部主流程节点
    nodes = [
        (3, 74, "目标确认\nOrchestrator"),
        (20, 74, "路径规划\nNavigator"),
        (37, 74, "生成 5 类资源\nGenerator"),
        (54, 74, "结果补齐\n与修正"),
        (71, 74, "神经符号\n校验"),
        (88, 74, "4-Prompt\n辩论议会"),
    ]
    for x, y, t in nodes:
        process_box(ax, (x, y), 14, 12, t, fontsize=7, max_chars=12)

    for i in range(len(nodes) - 1):
        x1 = nodes[i][0] + 14
        y1 = nodes[i][1] + 6
        x2 = nodes[i + 1][0]
        y2 = nodes[i + 1][1] + 6
        arrow(ax, (x1, y1), (x2, y2), lw=1.2)

    # 决策菱形
    decision(ax, (89, 48), 10, "通过？")

    # 分支结果
    process_box(ax, (70, 30), 16, 12, "通过 / 修改通过\n缓存并输出",
                facecolor=PALETTE["accent"], fontsize=8, max_chars=10)
    process_box(ax, (88, 30), 16, 12, "拒绝\n返回 Generator 修订",
                facecolor=PALETTE["warm"], fontsize=8, max_chars=10)

    # 分支箭头
    arrow(ax, (95, 48), (95, 42), text="否", fontsize=8)
    arrow(ax, (95, 42), (95, 38), color=PALETTE["danger"], lw=1.2)
    arrow(ax, (93, 48), (93, 42), text="是", fontsize=8)
    arrow(ax, (93, 42), (86, 38), color=PALETTE["accent"], lw=1.2)

    # 拒绝返回 Generator（沿底部绕回）
    arrow(ax, (96, 30), (96, 22), color=PALETTE["danger"], lw=1.2)
    arrow(ax, (96, 22), (44, 22), color=PALETTE["danger"], lw=1.2)
    arrow(ax, (44, 22), (44, 72), color=PALETTE["danger"], lw=1.2)
    ax.text(70, 25, "修订反馈", fontsize=8, color=PALETTE["danger"], ha="center")

    set_title(ax, "图 7：资源生成与审核流程")
    save(fig, "fig7-resource-pipeline")



# ──────────────────────────────────────────────────────────────────────────────
# 图 11：认知风格自适应渲染对比（rich wireframes）
# ──────────────────────────────────────────────────────────────────────────────
def fig11_cognitive_styles():
    fig, ax = plt.subplots(figsize=(10, 8))
    clean_ax(ax)

    panels = [
        (4, 54, "文字型", "纯 Markdown 讲义\n干净无干扰", PALETTE["neutral"], "text"),
        (54, 54, "视觉型", "B站讲解视频 + 思维导图\n颜色与结构高亮", PALETTE["secondary"], "visual"),
        (4, 6, "听觉型", "语音讲解稿 + TTS 朗读\n可控制语速", PALETTE["accent"], "audio"),
        (54, 6, "动觉型", "代码案例 + 练习题\n进入代码沙箱", PALETTE["warm"], "kinesthetic"),
    ]

    for x, y, label, desc, color, ptype in panels:
        rounded_box(ax, (x, y), 44, 42, "", facecolor=PALETTE["panel"],
                    edgecolor=color, lw=2, radius=0.02)
        rounded_box(ax, (x + 2, y + 34), 40, 6, label,
                    facecolor=color, fontsize=10, radius=0.015, bold=True)
        ax.text(x + 22, y + 26, desc, ha="center", va="center",
                fontsize=8.5, color=PALETTE["text"], linespacing=1.25)

        # 每个面板画一个简化的内部示意
        inner_x = x + 6
        inner_y = y + 4
        inner_w = 32
        inner_h = 16
        rounded_box(ax, (inner_x, inner_y), inner_w, inner_h, "",
                    facecolor=PALETTE["bg"], edgecolor=PALETTE["neutral_light"],
                    lw=0.8, radius=0.01)

        if ptype == "text":
            for i, yy in enumerate([inner_y + 11, inner_y + 7, inner_y + 3]):
                w = inner_w - 8 - i * 4
                rect = Rectangle((inner_x + 4, yy), w, 2,
                                 facecolor=PALETTE["neutral_light"])
                ax.add_patch(rect)
        elif ptype == "visual":
            # 左侧“视频”框
            rounded_box(ax, (inner_x + 3, inner_y + 3), 14, 10, "播放 视频",
                        facecolor=PALETTE["secondary"], fontsize=7)
            # 右侧“导图”节点
            for cx, cy in [(inner_x + 24, inner_y + 11), (inner_x + 20, inner_y + 5),
                           (inner_x + 28, inner_y + 5)]:
                circle = Circle((cx, cy), 1.8, facecolor=PALETTE["accent"])
                ax.add_patch(circle)
            ax.plot([inner_x + 24, inner_x + 20], [inner_y + 9, inner_y + 6.8],
                    color=PALETTE["neutral"], lw=1)
            ax.plot([inner_x + 24, inner_x + 28], [inner_y + 9, inner_y + 6.8],
                    color=PALETTE["neutral"], lw=1)
        elif ptype == "audio":
            # 波形
            xx = np.linspace(inner_x + 4, inner_x + inner_w - 4, 40)
            yy = inner_y + inner_h / 2 + 3 * np.sin(xx * 1.2)
            ax.plot(xx, yy, color=color, lw=1.5)
            ax.text(inner_x + inner_w / 2, inner_y + 3, "TTS 朗读中...",
                    ha="center", fontsize=7, color=PALETTE["text"])
        elif ptype == "kinesthetic":
            # 代码行
            for i, yy in enumerate([inner_y + 11, inner_y + 8, inner_y + 5]):
                rect = Rectangle((inner_x + 4, yy), inner_w - 8, 2,
                                 facecolor=PALETTE["neutral_light"])
                ax.add_patch(rect)
            rounded_box(ax, (inner_x + inner_w - 12, inner_y + 2), 8, 3, "Run",
                        facecolor=color, fontsize=6)

    set_title(ax, "图 11：认知风格自适应渲染对比")
    save(fig, "fig11-cognitive-styles")


# ──────────────────────────────────────────────────────────────────────────────
# 图 14：性能优化前后对比（带提升倍数标注）
# ──────────────────────────────────────────────────────────────────────────────
def fig14_performance():
    fig, axes = plt.subplots(1, 3, figsize=(9.5, 4.2))
    panels = [
        ("资源生成\n响应时间(s)", 3.0, 0.02, "s", "150×"),
        ("前端主包\n大小(KB)", 465, 98, "KB", "4.7×"),
        ("代码沙箱\n延迟(ms)", 600, 120, "ms", "5×"),
    ]
    for ax, (metric, before, after, unit, gain) in zip(axes, panels):
        bars = ax.bar(["优化前", "优化后"], [before, after],
                      color=[PALETTE["neutral"], PALETTE["accent"]],
                      edgecolor="black", linewidth=1.2, width=0.5)
        ax.set_ylabel(unit, fontsize=9)
        ax.set_title(metric, fontsize=10, fontweight="bold")
        ax.set_ylim(0, max(before, after) * 1.35)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        for bar in bars:
            height = bar.get_height()
            label = f"{height:.2f}" if unit == "s" else f"{int(height)}"
            ax.text(bar.get_x() + bar.get_width() / 2, height * 1.03,
                    label, ha="center", va="bottom", fontsize=9)
        # 提升倍数箭头
        ax.annotate("", xy=(1, after * 1.18), xytext=(0, before * 1.05),
                    arrowprops=dict(arrowstyle="->", color=PALETTE["danger"], lw=1.2))
        ax.text(0.5, (before + after) / 2 * 1.2, f"↓ {gain}",
                ha="center", fontsize=9, color=PALETTE["danger"], weight="bold")
    fig.suptitle("图 14：性能优化前后对比", fontsize=13, fontweight="bold", y=1.02)
    save(fig, "fig14-performance")


# ──────────────────────────────────────────────────────────────────────────────
# 图 15：数字人助教界面效果（状态机 + 控制面板）
# ──────────────────────────────────────────────────────────────────────────────
def fig15_digital_human():
    fig, ax = plt.subplots(figsize=(9, 7))
    clean_ax(ax)

    # 左侧状态机
    states = [
        (15, 78, "待机", "呼吸光环\n慢速旋转"),
        (40, 78, "朗读", "声波扩散\n口型同步"),
        (15, 58, "互动", "倾听输入\n表情反馈"),
        (40, 58, "静音", "停止播放\n保持显示"),
    ]
    for x, y, label, desc in states:
        rounded_box(ax, (x, y), 18, 14, f"{label}\n{desc}",
                    facecolor=PALETTE["panel"], edgecolor=PALETTE["secondary"],
                    text_color=PALETTE["text"], fontsize=8, radius=0.015)

    # 状态转移
    arrow(ax, (33, 85), (40, 85), color=PALETTE["secondary"], lw=1.2)
    arrow(ax, (24, 78), (24, 72), color=PALETTE["secondary"], lw=1.2)
    arrow(ax, (33, 65), (40, 65), color=PALETTE["secondary"], lw=1.2)
    arrow(ax, (49, 72), (49, 78), color=PALETTE["secondary"], lw=1.2,
          connectionstyle="arc3,rad=0.15")

    # 右侧数字人浮窗示意
    rounded_box(ax, (62, 30), 32, 60, "", facecolor=PALETTE["bg"],
                edgecolor=PALETTE["primary"], lw=2, radius=0.03)
    # 头像（略下移，给声波环与面板顶边留间距）
    avatar_cy = 75
    circle = Circle((78, avatar_cy), 9, facecolor=PALETTE["lane_agent"],
                    edgecolor=PALETTE["primary"], linewidth=2)
    ax.add_patch(circle)
    ax.text(78, avatar_cy, "小蜂\nAvatar", ha="center", va="center",
            fontsize=10, color=PALETTE["primary"], weight="bold")
    # 声波
    for r in [7, 9, 11]:
        circle = Circle((78, avatar_cy), r, facecolor="none",
                        edgecolor=PALETTE["secondary"], linewidth=1, linestyle="--")
        ax.add_patch(circle)
    # 控制项（整体下移，避免与声波环近邻）
    controls = [
        (68, 56, "语速控制", "0.5x  1x  2x"),
        (68, 48, "当前知识点", "文件操作"),
        (68, 40, "语音输入", "点击说话"),
        (68, 32, "引导问题", "为什么 open 要 encoding？"),
    ]
    for x, y, label, val in controls:
        ax.text(x, y + 2.5, label, fontsize=8, color=PALETTE["text"], weight="bold")
        rounded_box(ax, (x, y - 2), 24, 3.5, val, facecolor=PALETTE["panel"],
                    edgecolor=PALETTE["neutral_light"], text_color=PALETTE["text"],
                    fontsize=7, radius=0.01)

    # 数字人与状态机之间的“驱动”箭头
    arrow(ax, (58, 65), (62, 68), text="状态驱动", fontsize=8,
          color=PALETTE["primary"], connectionstyle="arc3,rad=0.1",
          text_offset=(0, 1.5))

    set_title(ax, "图 15：数字人助教界面效果")
    save(fig, "fig15-digital-human")


# ──────────────────────────────────────────────────────────────────────────────
# 图 16：学习闭环数据流图（DFD，正交布线）
# ──────────────────────────────────────────────────────────────────────────────
def fig16_learning_dfd():
    fig, ax = plt.subplots(figsize=(11, 7))
    clean_ax(ax)

    # 外部实体（左列）
    external_entity(ax, (4, 76), 12, 9, "学生", fontsize=9)
    external_entity(ax, (4, 16), 12, 9, "教师", fontsize=9)

    # 处理过程：左上 / 左下 / 右上 / 右下
    process_box(ax, (24, 72), 18, 11, "EduHive\n学习会话处理", fontsize=8)
    process_box(ax, (24, 36), 18, 11, "画像与路径\n推理", fontsize=8)
    process_box(ax, (54, 72), 18, 11, "资源生成\n与审核", fontsize=8)
    process_box(ax, (54, 36), 18, 11, "评估与\n知识熔炉", fontsize=8)

    # 数据存储（右列）
    data_store(ax, (84, 72), 11, 13, "知识图谱\nNeo4j", fontsize=8)
    data_store(ax, (84, 36), 11, 13, "SQLite\n业务库", fontsize=8)

    # 数据流
    # 学生 -> P1
    arrow(ax, (16, 80.5), (24, 77.5), text="学习目标/对话", fontsize=7)
    # 教师 -> P1（左侧绕行）
    orthogonal_arrow(ax, [(16, 20.5), (18, 20.5), (18, 68), (24, 68)],
                     text="学情查看请求", fontsize=7, text_offset=(0, 1.3))
    # P1 -> P2
    arrow(ax, (33, 72), (33, 47), text="学生行为/画像", fontsize=7,
          text_offset=(1.2, 0))
    # P1 -> P3
    arrow(ax, (42, 77.5), (54, 77.5), text="目标概念/约束", fontsize=7)
    # P2 -> P3（从 P2 右侧水平进入 P3 底部，避免与 P3->P4 标签交叉）
    orthogonal_arrow(ax, [(42, 43), (54, 43), (54, 66.5)],
                     text="前置依赖/路径", fontsize=7, text_offset=(0, 1.5))
    # P2 -> Neo4j（中腰右行）
    orthogonal_arrow(ax, [(46, 38), (84, 38), (84, 76)],
                     text="查询/路径", fontsize=7, text_offset=(0, -1.5))
    # Neo4j -> P3
    arrow(ax, (84, 73), (72, 73), text="前置依赖/约束", fontsize=7)
    # P3 -> P4
    arrow(ax, (63, 72), (63, 47), text="资源包/反馈", fontsize=7,
          text_offset=(1.5, 0))
    # P4 -> P2（掌握度反馈）
    orthogonal_arrow(ax, [(54, 40.5), (42, 40.5), (42, 47)],
                     text="掌握度/BKT", fontsize=7, text_offset=(-1.5, 1.0))
    # P4 -> SQLite
    arrow(ax, (72, 42.5), (84, 42.5), text="练习结果", fontsize=7)
    # SQLite -> P4
    arrow(ax, (84, 44.5), (72, 44.5), text="历史记录", fontsize=7)
    # P2 -> SQLite（写入画像/行为）
    orthogonal_arrow(ax, [(33, 36), (33, 30), (89.5, 30), (89.5, 36)],
                     text="画像/行为", fontsize=7, text_offset=(0, -1.5))
    # P2 -> 教师（学习建议）
    orthogonal_arrow(ax, [(24, 41.5), (22, 41.5), (22, 20.5), (16, 20.5)],
                     text="学习建议", fontsize=7, text_offset=(0, 1.3))

    set_title(ax, "图 16：学习闭环数据流图（DFD）")
    save(fig, "fig16-learning-dfd")


# ──────────────────────────────────────────────────────────────────────────────
# 真实 UI 截图加标题条
# ──────────────────────────────────────────────────────────────────────────────
def generate_screenshot_figures():
    mapping = [
        ("student_flow_20_profile.png", "fig5-profile-evidence"),
        ("student_flow_04_graph_path_planned.png", "fig8-learning-path"),
        ("student_flow_12_chat_reply.png", "fig9-socratic-stages"),
        ("student_flow_18_progress_heatmap.png", "fig10-bkt-heatmap"),
        ("student_flow_08_resources_page.png", "fig12-course-workspace"),
        ("student_flow_15_code_run_output.png", "fig13-code-sandbox"),
    ]
    for src, dst in mapping:
        screenshot_figure(src, dst)


# ──────────────────────────────────────────────────────────────────────────────
# 主入口
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    fig1_application_scenarios()
    fig2_overall_loop()
    fig3_system_architecture()
    fig4_agent_architecture()
    fig6_neuro_symbolic()
    fig7_resource_pipeline()
    fig11_cognitive_styles()
    fig14_performance()
    fig15_digital_human()
    fig16_learning_dfd()
    generate_screenshot_figures()
    print("All engineering figures generated.")
