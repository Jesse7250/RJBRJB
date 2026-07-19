#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Adjust figure placeholders in docs/作品设计文档.md:
- Remove AI-looking / text-replaceable conceptual figures.
- Renumber and rewrite kept figures to use real UI screenshots or clean vector diagrams.
- Update Appendix F figure list.
"""
from pathlib import Path
import re

DOC = Path("D:/Gitproject/RJBRJB/docs/作品设计文档.md")

# New caption blocks keyed by OLD figure number.
# None means delete.  New figures are inserted in document order.
NEW_BLOCKS = {
    1: """> **图 1：智慧伴学课程门户首页**
> 建议放置位置：docs/images/fig1-portal-home.png
> 内容：课程门户首页真实截图，展示课程中心、推荐课程卡片、搜索栏与登录入口，体现系统面向高等教育 Python 程序设计课程的入口设计。
> 来源截图：docs/test-screenshots/student_flow_01_portal_landing.png
""",
    2: """> **图 2：系统总体数据闭环**
> 建议放置位置：docs/images/fig2-overall-loop.png
> 内容：由四张真实 UI 截图组成的复合图，以箭头串联“学习画像 → 知识图谱路径 → 个性化资源 → 掌握度评估”的数据闭环；左上图来自学习画像页，右上图来自知识图谱页，左下图来自学习资源页，右下图来自掌握进度页。避免使用抽象图标或装饰性元素。
> 来源截图：docs/test-screenshots/student_flow_20_profile.png、student_flow_04_graph_path_planned.png、student_flow_08_resources_page.png、student_flow_18_progress_heatmap.png
""",
    3: """> **图 3：系统总体架构图**
> 建议放置位置：docs/images/fig3-system-architecture.png
> 内容：白底技术架构图，自上而下分为前端展示层、API 网关层、多智能体编排层、数据与知识层、大模型层；每层标注主要模块与对应代码目录，箭头表示数据流向。使用简洁矩形、无衬线字体与克制配色，避免装饰性插画。
> 绘制方式：使用 matplotlib / PlantUML / draw.io 生成矢量图，禁止 AI 生成图。
""",
    4: """> **图 4：多智能体协同架构图**
> 建议放置位置：docs/images/fig4-agent-architecture.png
> 内容：展示 Orchestrator、Profiler、Navigator、Generator、Reviewer 五个角色及统一 AgentMessage 协议；Reviewer 内部放大显示 Expert / Teacher / Student-Sim / Guardian 四个审核视角；右侧标注知识图谱、SQLite、LLM 提供者等外部依赖。使用颜色区分的简洁矩形与有向箭头。
> 绘制方式：使用 matplotlib / PlantUML / draw.io 生成矢量图，禁止 AI 生成图。
""",
    5: """> **图 5：学习画像与 Agent 协作追踪**
> 建议放置位置：docs/images/fig5-profile-evidence.png
> 内容：学习画像页面真实截图，左侧展示学生多维画像、证据列表与画像置信度；右侧展示 Agent 协作面板，记录 Profiler、Navigator、Generator、Reviewer 等角色的调用状态与耗时，体现“基于证据的动态画像”与多智能体透明性。
> 来源截图：docs/test-screenshots/student_flow_20_profile.png
""",
    6: """> **图 6：神经符号约束流程**
> 建议放置位置：docs/images/fig6-neuro-symbolic.png
> 内容：三阶段技术流程图：左侧为知识图谱抽取的约束（前置知识、难度、易错点、禁止概念）；中间为 Generator 生成资源；右侧为 AST 语法检查、导入白名单、未学概念检测等生成后校验。使用真实知识点示例与代码片段标注，避免抽象图标。
> 绘制方式：使用 matplotlib / PlantUML / draw.io 生成矢量图，禁止 AI 生成图。
""",
    7: """> **图 7：资源生成与辩论审核追踪**
> 建议放置位置：docs/images/fig7-resource-review-trace.png
> 内容：学习资源页面真实截图，左侧为已生成的资源包（智能讲义、思维导图、练习题、代码案例）；右侧 Agent 生成过程面板展示 Navigator、Generator、Reviewer 的调用顺序与状态，体现多智能体协同与审核闭环。
> 来源截图：docs/test-screenshots/student_flow_09_resources_timeline_and_evolution.png
""",
    8: """> **图 8：知识图谱与学习路径规划**
> 建议放置位置：docs/images/fig8-learning-path.png
> 内容：知识图谱页面真实截图，展示从已掌握节点到目标节点的金色高亮学习路径、节点掌握度、前置依赖关系，以及右侧路径解释与数字人助教。
> 来源截图：docs/test-screenshots/student_flow_04_graph_path_planned.png
""",
    9: """> **图 9：AI 学习对话与苏格拉底辅导**
> 建议放置位置：docs/images/fig9-chat-socratic.png
> 内容：学习对话页面真实截图，展示 Socrates、Profiler 等多角色对同一学生问题的协同回答，包含引导式提问、画像更新与快捷提示按钮，体现苏格拉底辅导与多智能体协同。
> 来源截图：docs/test-screenshots/student_flow_12_chat_reply.png
""",
    11: """> **图 10：BKT 掌握度热力图**
> 建议放置位置：docs/images/fig10-bkt-heatmap.png
> 内容：掌握进度页面真实截图，展示基于 BKT 的知识点掌握度热力图、平均掌握率、稳定掌握/薄弱预警统计，以及认知风格切换按钮。
> 来源截图：docs/test-screenshots/student_flow_18_progress_heatmap.png
""",
    13: """> **图 11：认知风格自适应渲染对比**
> 建议放置位置：docs/images/fig11-cognitive-styles.png
> 内容：同一知识点“文件操作”在文字型、视觉型、听觉型、动觉型四种模式下的界面对比；分别展示纯 Markdown 讲义、B站讲解视频、语音讲解稿与朗读按钮、代码沙箱入口。由四张真实 UI 截图拼接而成。
> 来源截图：docs/test-screenshots/student_flow_08_resources_page.png（文字型/动觉型基础）、student_flow_09_resources_timeline_and_evolution.png（视觉型）；听觉型需补充切换后的截图。
""",
    15: """> **图 12：课程工作台主界面**
> 建议放置位置：docs/images/fig12-course-workspace.png
> 内容：课程工作台真实截图，展示左侧导航栏、顶部学习目标与会话信息、中间学习资源主内容区、右侧 Agent 协作与数字人助教，体现“课程门户 + Command Center 工作台”的双模式设计。
> 来源截图：docs/test-screenshots/student_flow_08_resources_page.png
""",
    23: """> **图 14：性能优化前后对比**
> 建议放置位置：docs/images/fig14-performance.png
> 内容：基于真实测试数据的柱状图，对比资源生成响应时间（约 3 s → 约 0.02 s）、前端主包大小（465 KB → 约 98 KB）、代码沙箱平均延迟；标注测试环境（mock 模式、Chrome、FastAPI 端口 8001）。
> 绘制方式：使用 matplotlib 生成，数据与正文表格严格一致。
""",
}

# Figures to delete entirely: old numbers not in NEW_BLOCKS.
# Innovation-section figures 25-34 and redundant placeholders 10,12,14,16-22,24 are deleted.

EXTRA_BLOCK = """> **图 13：代码沙箱运行与自动判题**
> 建议放置位置：docs/images/fig13-code-sandbox.png
> 内容：代码沙箱页面真实截图，展示 Monaco 编辑器中的 Python 代码、运行输出、变量快照与数字人助教，体现后端受控执行与即时反馈。
> 来源截图：docs/test-screenshots/student_flow_15_code_run_output.png
"""

APPENDIX_ROWS = """| 图 1 | fig1-portal-home.png | 智慧伴学课程门户首页 | 1.1 |
| 图 2 | fig2-overall-loop.png | 系统总体数据闭环 | 2.1 |
| 图 3 | fig3-system-architecture.png | 系统总体架构图 | 2.2 |
| 图 4 | fig4-agent-architecture.png | 多智能体协同架构图 | 2.3 |
| 图 5 | fig5-profile-evidence.png | 学习画像与 Agent 协作追踪 | 2.4 |
| 图 6 | fig6-neuro-symbolic.png | 神经符号约束流程 | 2.5 |
| 图 7 | fig7-resource-review-trace.png | 资源生成与辩论审核追踪 | 2.6 |
| 图 8 | fig8-learning-path.png | 知识图谱与学习路径规划 | 2.7 |
| 图 9 | fig9-chat-socratic.png | AI 学习对话与苏格拉底辅导 | 2.8 |
| 图 10 | fig10-bkt-heatmap.png | BKT 掌握度热力图 | 2.9 |
| 图 11 | fig11-cognitive-styles.png | 认知风格自适应渲染对比 | 2.11 |
| 图 12 | fig12-course-workspace.png | 课程工作台主界面 | 3.2 |
| 图 13 | fig13-code-sandbox.png | 代码沙箱运行与自动判题 | 3.4 |
| 图 14 | fig14-performance.png | 性能优化前后对比 | 4.2 |"""


def replace_figure_blocks(text: str) -> str:
    lines = text.splitlines(keepends=True)
    out = []
    i = 0
    n = len(lines)
    inserted_code_sandbox = False
    while i < n:
        line = lines[i]
        m = re.match(r"> \*\*图 (\d+)：[^*]+\*\*\s*\n?", line)
        if m:
            old_no = int(m.group(1))
            # consume the whole block (consecutive > lines)
            j = i
            while j < n and lines[j].startswith("> "):
                j += 1
            replacement = NEW_BLOCKS.get(old_no)
            if replacement is not None:
                out.append(replacement)
            # If we just removed the old fig20 (evaluation loop) block at the end of 3.4,
            # insert the code-sandbox figure once, before the following section header.
            if old_no == 20 and not inserted_code_sandbox:
                out.append("\n")
                out.append(EXTRA_BLOCK)
                inserted_code_sandbox = True
            i = j
            continue
        out.append(line)
        i += 1
    return "".join(out)


def update_appendix(text: str) -> str:
    lines = text.splitlines(keepends=True)
    out = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if re.match(r"\| 图 \d+ \|", line):
            # skip all existing data rows
            while i < n and re.match(r"\| 图 \d+ \|", lines[i]):
                i += 1
            out.append(APPENDIX_ROWS + "\n")
            continue
        out.append(line)
        i += 1
    return "".join(out)


def main():
    text = DOC.read_text(encoding="utf-8")
    text = replace_figure_blocks(text)
    text = update_appendix(text)
    # bump version stamp
    text = text.replace("*文档版本：v2.0*", "*文档版本：v2.1*")
    text = text.replace("*最后更新：2026-07-15*", "*最后更新：2026-07-15*")
    DOC.write_text(text, encoding="utf-8")
    print(f"Updated {DOC}")


if __name__ == "__main__":
    main()
