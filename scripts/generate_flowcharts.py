#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate publication-quality vector flowcharts for the EduMate design document.
Backend: Python (matplotlib). Outputs SVG/PDF/PNG to docs/figures/.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from pathlib import Path

OUT_DIR = Path("D:/Gitproject/RJBRJB/docs/figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Palette & style
# ---------------------------------------------------------------------------
PALETTE = {
    "blue_main": "#0F4D92",
    "blue_secondary": "#3775BA",
    "teal": "#42949E",
    "green": "#8BCF8B",
    "violet": "#9A4D8E",
    "red": "#B64342",
    "gold": "#FFD700",
    "dark": "#4D4D4D",
    "mid": "#767676",
    "light": "#CFCECE",
    "bg": "#FFFFFF",
}


def apply_style(font_size=11):
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Microsoft YaHei", "DejaVu Sans", "Arial"],
        "axes.unicode_minus": False,
        "svg.fonttype": "none",
        "pdf.fonttype": 42,
        "font.size": font_size,
        "axes.spines.right": False,
        "axes.spines.top": False,
        "axes.linewidth": 0.8,
        "legend.frameon": False,
    })


def is_dark(hex_color, threshold=160):
    c = hex_color.lstrip('#')
    r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    return (0.299 * r + 0.587 * g + 0.114 * b) < threshold


def text_color_for(bg):
    return "white" if is_dark(bg) else PALETTE["dark"]


def draw_box(ax, xy, width, height, color, label, sublabels=None,
             label_size=11, sub_size=8, radius=0.015, alpha=1.0):
    box = FancyBboxPatch(
        xy, width, height,
        boxstyle=f"round,pad=0,rounding_size={radius}",
        facecolor=color, edgecolor=PALETTE["dark"], linewidth=1.2,
        alpha=alpha, zorder=2,
    )
    ax.add_patch(box)
    x, y = xy
    tcx = text_color_for(color)
    ax.text(x + width / 2, y + height - 0.015, label,
            ha='center', va='top', fontsize=label_size,
            fontweight='bold', color=tcx, zorder=3)
    if sublabels:
        sub_text = "\n".join(sublabels)
        ax.text(x + width / 2, y + height / 2 - 0.005, sub_text,
                ha='center', va='center', fontsize=sub_size,
                color=tcx, zorder=3, linespacing=1.25)
    return box


def draw_arrow(ax, start, end, color=PALETTE["dark"], lw=1.5,
               arrowstyle='-|>', mutation_scale=16, zorder=1,
               connectionstyle="arc3,rad=0"):
    ax.add_patch(FancyArrowPatch(
        start, end,
        arrowstyle=arrowstyle, mutation_scale=mutation_scale,
        linewidth=lw, color=color, zorder=zorder,
        connectionstyle=connectionstyle,
    ))


def save(fig, stem):
    base = OUT_DIR / stem
    for ext in ["svg", "pdf", "png"]:
        fig.savefig(f"{base}.{ext}", dpi=300, bbox_inches='tight',
                    facecolor='white', edgecolor='none')
    print(f"Saved {stem}.{{svg,pdf,png}}")


# ---------------------------------------------------------------------------
# Figure 3: System overall architecture
# ---------------------------------------------------------------------------
def fig3_system_architecture():
    apply_style(font_size=11)
    fig, ax = plt.subplots(figsize=(7, 9))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    layers = [
        ("前端展示层", PALETTE["blue_secondary"], [
            "课程门户 · 课程工作台 · 知识图谱可视化",
            "资源浏览 · AI 对话 · 代码沙箱 · 掌握进度",
            "frontend/src/",
        ]),
        ("API 网关层", PALETTE["teal"], [
            "用户认证 · 会话管理 · RESTful API",
            "SSE 流式接口 · 行为日志",
            "backend/app/api/",
        ]),
        ("多智能体编排层", PALETTE["violet"], [
            "Orchestrator · Profiler · Navigator",
            "Generator · Reviewer",
            "backend/app/agents/",
        ]),
        ("数据与知识层", PALETTE["green"], [
            "SQLite 持久化 · Neo4j 知识图谱 · 资源缓存",
            "BKT 追踪 · 行为证据",
            "backend/app/services/",
        ]),
        ("大模型层", PALETTE["blue_main"], [
            "统一 LLM 抽象",
            "DeepSeek / 讯飞星火 / Mock 一键切换",
            "backend/app/agents/llm.py",
        ]),
    ]

    n = len(layers)
    box_h = 0.14
    gap = 0.04
    total_h = n * box_h + (n - 1) * gap
    y0 = 0.5 + total_h / 2 - box_h
    x = 0.08
    w = 0.84

    centers = []
    for i, (name, color, subs) in enumerate(layers):
        y = y0 - i * (box_h + gap)
        draw_box(ax, (x, y), w, box_h, color, name, subs, label_size=13, sub_size=9)
        centers.append((x + w / 2, y + box_h / 2))

    for i in range(len(centers) - 1):
        draw_arrow(ax,
                   (centers[i][0], centers[i][1] - box_h / 2 - 0.005),
                   (centers[i + 1][0], centers[i + 1][1] + box_h / 2 + 0.005),
                   lw=2)

    fig.tight_layout(pad=0.5)
    save(fig, "fig3-system-architecture")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 4: Multi-agent architecture
# ---------------------------------------------------------------------------
def fig4_agent_architecture():
    apply_style(font_size=10)
    fig, ax = plt.subplots(figsize=(14, 8))
    ax.set_xlim(0, 1.08)
    ax.set_ylim(0, 1)
    ax.axis('off')

    # Orchestrator
    orch_xy = (0.24, 0.76)
    orch_wh = (0.42, 0.14)
    draw_box(ax, orch_xy, *orch_wh, PALETTE["blue_main"], "Orchestrator",
             ["意图识别 · 会话状态 · 路由 · 熔断降级 · AgentMessage 统一协议"],
             label_size=14, sub_size=10)

    # User input
    user_xy = (0.03, 0.77)
    user_wh = (0.12, 0.12)
    draw_box(ax, user_xy, *user_wh, PALETTE["mid"], "User Input",
             ["学生 / 教师"], label_size=11, sub_size=10)
    draw_arrow(ax,
               (user_xy[0] + user_wh[0], user_xy[1] + user_wh[1] / 2),
               (orch_xy[0], orch_xy[1] + orch_wh[1] / 2),
               lw=2)

    # Four roles
    role_specs = [
        ("Profiler", PALETTE["blue_secondary"]),
        ("Navigator", PALETTE["teal"]),
        ("Generator", PALETTE["violet"]),
        ("Reviewer", PALETTE["red"]),
    ]
    role_w, role_h = 0.18, 0.20
    role_y = 0.44
    role_xs = [0.06, 0.28, 0.50, 0.72]
    roles = []
    for (name, color), rx in zip(role_specs, role_xs):
        if name == "Reviewer":
            r_w, r_h = 0.20, 0.28
            ry = role_y - 0.04
            box = FancyBboxPatch(
                (rx, ry), r_w, r_h,
                boxstyle="round,pad=0,rounding_size=0.015",
                facecolor=color, edgecolor=PALETTE["dark"], linewidth=1.5, zorder=2,
            )
            ax.add_patch(box)
            ax.text(rx + r_w / 2, ry + r_h - 0.015, name,
                    ha='center', va='top', fontsize=13, fontweight='bold',
                    color='white', zorder=3)
            # 2x2 council
            council = [
                ("Expert", "技术准确性"),
                ("Teacher", "教学合理性"),
                ("Student-Sim", "初学者可理解性"),
                ("Guardian", "安全 / 一票否决"),
            ]
            inner_w = (r_w - 0.018) / 2
            inner_h = (r_h - 0.09) / 2
            for idx, (cname, cdesc) in enumerate(council):
                col = idx % 2
                row = idx // 2
                sx = rx + 0.006 + col * (inner_w + 0.006)
                sy = ry + 0.006 + row * (inner_h + 0.006)
                sub = FancyBboxPatch(
                    (sx, sy), inner_w, inner_h,
                    boxstyle="round,pad=0,rounding_size=0.006",
                    facecolor='#D66B6B', edgecolor='white', linewidth=0.8, zorder=3,
                )
                ax.add_patch(sub)
                ax.text(sx + inner_w / 2, sy + inner_h - 0.004, cname,
                        ha='center', va='top', fontsize=9, fontweight='bold',
                        color='white', zorder=4)
                ax.text(sx + inner_w / 2, sy + inner_h / 2 - 0.003, cdesc,
                        ha='center', va='center', fontsize=8,
                        color='white', zorder=4)
            cx, cy = rx + r_w / 2, ry + r_h / 2
            top = ry + r_h
            roles.append({'name': name, 'cx': cx, 'cy': cy,
                          'top': top, 'right': rx + r_w, 'left': rx})
        else:
            draw_box(ax, (rx, role_y), role_w, role_h, color, name,
                     label_size=13, sub_size=9)
            cx, cy = rx + role_w / 2, role_y + role_h / 2
            roles.append({'name': name, 'cx': cx, 'cy': cy,
                          'top': role_y + role_h, 'right': rx + role_w, 'left': rx})

    # Orchestrator -> roles
    orch_bottom = (orch_xy[0] + orch_wh[0] / 2, orch_xy[1])
    for r in roles:
        draw_arrow(ax, orch_bottom, (r['cx'], r['top']), lw=1.8)

    # External dependencies
    deps = [
        ("LLM Providers", PALETTE["blue_main"]),
        ("Knowledge Graph", PALETTE["teal"]),
        ("SQLite DB", PALETTE["green"]),
    ]
    dep_w, dep_h = 0.10, 0.12
    dep_x = 0.96
    dep_ys = [0.70, 0.52, 0.30]
    dep_boxes = []
    for (dname, dcolor), dy in zip(deps, dep_ys):
        draw_box(ax, (dep_x, dy), dep_w, dep_h, dcolor, dname,
                 label_size=10, sub_size=8)
        dep_boxes.append({'name': dname, 'left': dep_x,
                          'cy': dy + dep_h / 2,
                          'top': dy + dep_h, 'bottom': dy})

    # Dependency arrows (curved to avoid overlap)
    # Generator -> LLM
    draw_arrow(ax,
               (roles[2]['right'], roles[2]['cy']),
               (dep_boxes[0]['left'], dep_boxes[0]['cy']),
               lw=1.4, connectionstyle="arc3,rad=0.25")
    # Navigator -> Knowledge Graph
    draw_arrow(ax,
               (roles[1]['right'], roles[1]['cy']),
               (dep_boxes[1]['left'], dep_boxes[1]['cy']),
               lw=1.4, connectionstyle="arc3,rad=-0.25")
    # Profiler -> SQLite
    draw_arrow(ax,
               (roles[0]['right'], roles[0]['cy']),
               (dep_boxes[2]['left'], dep_boxes[2]['cy']),
               lw=1.4, connectionstyle="arc3,rad=0.25")
    # Reviewer -> SQLite (audit)
    draw_arrow(ax,
               (roles[3]['right'], roles[3]['cy'] - 0.08),
               (dep_boxes[2]['left'], dep_boxes[2]['top']),
               lw=1.4, connectionstyle="arc3,rad=-0.15")

    fig.tight_layout(pad=0.5)
    save(fig, "fig4-agent-architecture")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Figure 6: Neuro-symbolic constraint flow
# ---------------------------------------------------------------------------
def fig6_neuro_symbolic():
    apply_style(font_size=10)
    fig, ax = plt.subplots(figsize=(11.5, 5.2))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    box_w, box_h = 0.26, 0.62
    ys = 0.19
    xs = [0.06, 0.37, 0.68]

    draw_box(ax, (xs[0], ys), box_w, box_h, PALETTE["teal"], "生成前约束",
             [
                 "目标知识点：文件操作",
                 "前置知识：变量、数据类型",
                 "难度：中等",
                 "易错点：Windows 路径转义",
                 "禁止概念：类、异常处理",
                 "允许模块：os、pathlib",
             ], label_size=12, sub_size=9)

    draw_box(ax, (xs[1], ys), box_w, box_h, PALETTE["violet"], "Generator 生成资源",
             [
                 "注入 GraphRAG Prompt",
                 "调用 LLM 生成：",
                 "· 智能讲义  · 思维导图",
                 "· 练习题    · 代码案例",
                 "· 语音讲解稿",
             ], label_size=12, sub_size=9)

    draw_box(ax, (xs[2], ys), box_w, box_h, PALETTE["red"], "生成后校验",
             [
                 "AST 语法检查",
                 "导入模块白名单",
                 "未学概念扫描",
                 "输出：approved /",
                 "modified / rejected",
             ], label_size=12, sub_size=9)

    for i in range(2):
        draw_arrow(ax,
                   (xs[i] + box_w + 0.005, ys + box_h / 2),
                   (xs[i + 1] - 0.005, ys + box_h / 2),
                   lw=2.5, color=PALETTE["dark"])

    draw_arrow(ax,
               (xs[2] + box_w / 2, ys - 0.01),
               (xs[1] + box_w / 2, ys - 0.01),
               lw=1.5, color=PALETTE["red"],
               arrowstyle='->', mutation_scale=14,
               connectionstyle="arc3,rad=-0.3")
    ax.text(xs[1] + box_w / 2 + 0.15, ys - 0.08, "拒绝时修订",
            ha='center', va='top', fontsize=9, color=PALETTE["red"])

    ax.text(0.5, 0.93, "神经符号认知架构：知识图谱约束 + AST 校验抑制幻觉与超纲",
            ha='center', va='top', fontsize=13, fontweight='bold',
            color=PALETTE["dark"])

    fig.tight_layout(pad=0.5)
    save(fig, "fig6-neuro-symbolic")
    plt.close(fig)


if __name__ == "__main__":
    apply_style()
    fig3_system_architecture()
    fig4_agent_architecture()
    fig6_neuro_symbolic()
    print("All flowcharts generated.")
