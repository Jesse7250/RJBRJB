"""
将 docs/作品设计文档.md 中的图片占位块引号转换为实际图片引用，
并更新附录 F 配图清单与状态说明。
"""
import re
from pathlib import Path

DOC = Path("D:/Gitproject/RJBRJB/docs/作品设计文档.md")

# 图号 -> 相对 docs/ 目录的图片路径
FIG_PATH = {
    1: "images/fig1-application-scenarios.png",
    2: "images/fig2-overall-loop.png",
    3: "figures/fig3-system-architecture.png",     # 高清版
    4: "figures/fig4-agent-architecture.png",      # 高清版
    5: "images/fig5-profile-evidence.png",
    6: "figures/fig6-neuro-symbolic.png",          # 高清版
    7: "images/fig7-resource-pipeline.png",
    8: "images/fig8-learning-path.png",
    9: "images/fig9-chat-socratic.png",
    10: "images/fig10-bkt-heatmap.png",
    11: "images/fig11-cognitive-styles.png",
    12: "images/fig12-course-workspace.png",
    13: "images/fig13-code-sandbox.png",
    14: "images/fig14-performance.png",
    15: "images/fig15-digital-human.png",
}

lines = DOC.read_text(encoding="utf-8").splitlines()
out = []
i = 0
while i < len(lines):
    line = lines[i]
    if line.startswith("> "):
        # 收集连续块引号
        block = []
        while i < len(lines) and lines[i].startswith(">"):
            block.append(lines[i])
            i += 1
        # 解析标题
        title_line = block[0]
        m = re.match(r"> \*\*图 (\d+)[：:](.*?)\*\*", title_line)
        if not m:
            # 非图片块，原样保留
            out.extend(block)
            out.append("")
            continue
        fig_num = int(m.group(1))
        caption = m.group(2).strip()
        # 解析内容说明
        desc = ""
        for b in block:
            if b.startswith("> 内容说明："):
                desc = b[len("> 内容说明："):].strip()
                break
        img_path = FIG_PATH.get(fig_num, f"images/fig{fig_num:02d}.png")
        out.append(f"![图 {fig_num}：{caption}]({img_path})")
        out.append("")
        out.append(f"**图 {fig_num}：{caption}**。{desc}")
        out.append("")
        continue
    else:
        out.append(line)
        i += 1

# 更新附录 F 表格
content = "\n".join(out)

table = """| 图号 | 文件位置（相对 `docs/`） | 类型 | 内容说明 | 对应章节 | 来源/制作方式 |
|------|------------------------|------|---------|---------|--------------|
| 图 1 | `images/fig1-application-scenarios.png` | 示意图 | 智慧伴学应用场景示意图（课后自主学习、翻转课堂、考前巩固、教师学情分析） | 1.1 | `scripts/generate_design_figures.py` |
| 图 2 | `images/fig2-overall-loop.png` | 示意图 | 系统总体数据闭环 | 2.1 | `scripts/generate_design_figures.py` |
| 图 3 | `figures/fig3-system-architecture.png` | 架构图 | 系统总体五层架构（高清版） | 2.2 | `scripts/generate_design_figures.py` / `scripts/generate_flowcharts.py` |
| 图 4 | `figures/fig4-agent-architecture.png` | 架构图 | 5 角色多智能体协同架构（高清版） | 2.3 | `scripts/generate_design_figures.py` / `scripts/generate_flowcharts.py` |
| 图 5 | `images/fig5-profile-evidence.png` | 真实截图 | 学习画像与 Agent 协作追踪 | 2.4 | `docs/test-screenshots/student_flow_20_profile.png` |
| 图 6 | `figures/fig6-neuro-symbolic.png` | 流程图 | 神经符号约束流程（高清版） | 2.5 | `scripts/generate_design_figures.py` |
| 图 7 | `images/fig7-resource-pipeline.png` | 流程图 | 资源生成与审核流程 | 2.6 | `scripts/generate_design_figures.py` |
| 图 8 | `images/fig8-learning-path.png` | 真实截图 | 知识图谱与学习路径规划 | 2.7 | `docs/test-screenshots/student_flow_04_graph_path_planned.png` |
| 图 9 | `images/fig9-chat-socratic.png` | 真实截图 | AI 学习对话与苏格拉底辅导 | 2.8 | `docs/test-screenshots/student_flow_12_chat_reply.png` |
| 图 10 | `images/fig10-bkt-heatmap.png` | 真实截图 | BKT 掌握度热力图 | 2.9 | `docs/test-screenshots/student_flow_18_progress_heatmap.png` |
| 图 11 | `images/fig11-cognitive-styles.png` | 截图拼图 | 认知风格自适应渲染对比（2×2 四宫格） | 2.11 | `scripts/generate_fig11_cognitive_styles.py`（基于 4 张资源页真实截图） |
| 图 12 | `images/fig12-course-workspace.png` | 真实截图 | 课程工作台主界面 | 3.2 | `docs/test-screenshots/student_flow_08_resources_page.png` |
| 图 13 | `images/fig13-code-sandbox.png` | 真实截图 | 代码沙箱运行与自动判题 | 3.4 | `docs/test-screenshots/student_flow_15_code_run_output.png` |
| 图 14 | `images/fig14-performance.png` | 统计图 | 性能优化前后对比 | 4.2 | `scripts/generate_fig14_performance.py` |
| 图 15 | `images/fig15-digital-human.png` | 示意图 | 数字人助教界面效果 | 2.12 | `scripts/generate_design_figures.py`（原 `fig10()` 输出重命名） |"""

# 替换附录表格
pattern_table = re.compile(
    r"(### 附录 F：文档配图清单\s*\n\s*\| 图号 \|.*?\n)\|.*?\n(?=\s*#### 配图状态说明)",
    re.DOTALL,
)
content = pattern_table.sub(r"\1" + table + "\n", content)

status = """#### 配图状态说明

- **最终保留并嵌入正文**：图 1–15 已全部生成/整理完毕，路径与来源见上表；正文中已使用 Markdown 图片语法实际引用，可直接渲染。
- **高清版本说明**：图 3、图 4、图 6 优先使用 `docs/figures/` 下的高清 PNG；同目录下还提供对应 SVG/PDF，便于印刷或二次编辑。
- **新增图片**：
  - 图 11：使用 `scripts/generate_fig11_cognitive_styles.py` 将 4 张真实资源页截图拼接为 2×2 四宫格。
  - 图 14：使用 `scripts/generate_fig14_performance.py` 生成 matplotlib 性能对比图，数据与正文 4.2 节严格一致。
- **删除/废弃**：以下图片已移动至 `docs/images/deprecated/`，不再作为正式配图引用：
  - `fig9-socratic-stages.png/.svg`（与图 9 真实截图重复，且未在最终方案中采用）
  - `fig10-digital-human.png/.svg`（已重命名为图 15）
  - `fig5-profile-evidence.svg`（图 5 已改为真实截图，原矢量占位图废弃）
  - `fig8-learning-path.svg`（图 8 已改为真实截图，原矢量占位图废弃）
- **备用素材**：`docs/test-screenshots/` 目录保留 22 张端到端测试截图，可用于答辩演示或替换局部细节。"""

pattern_status = re.compile(
    r"#### 配图状态说明\s*\n.*?\n(?=---\s*\n\s*\*文档版本)",
    re.DOTALL,
)
content = pattern_status.sub(status + "\n\n", content)

DOC.write_text(content, encoding="utf-8")
print("Document image plan finalized.")
