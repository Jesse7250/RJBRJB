# 智慧伴学 EduMate — RJBRJB 端到端测试报告

- **测试日期**：2026-07-15
- **测试仓库**：`Jesse7250/RJBRJB`（本地路径 `D:\Gitproject\RJBRJB`）
- **测试方式**：Kimi WebBridge 自动化浏览器测试 + 后端 API 校验
- **测试脚本**：`scripts/webbridge-tests/deep_student_flow_test.py`
- **构建模式**：`npm run build && npm run preview`（端口 4173）
- **后端模式**：`uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload`，`LLM_PROVIDER=mock`
- **会话 ID**：`ff8750b3-c6ba-45a5-95a3-27c4b03b7820`
- **URL 目标概念**：`文件读写`
- **UI 实际目标概念**：`Python简介`（见问题 1）

---

## 一、测试环境

| 组件 | 版本/配置 | 备注 |
|------|----------|------|
| Python | 3.13.12 | 后端虚拟环境 `backend/venv` |
| Node.js | 18+ | 前端依赖 `frontend/node_modules` |
| FastAPI / Uvicorn | 按 `requirements.txt` 安装 | 端口 8001 |
| Vite | 5.4.21 | 生产构建 + preview |
| LLM 提供者 | `mock` | 无需外部 API Key |
| 浏览器 | Chrome（通过 Kimi WebBridge 控制） | 扩展版本 1.10.3 |

---

## 二、测试范围

本次测试覆盖学生视角核心学习闭环：

1. 课程门户加载
2. 进入 Python 课程工作台
3. 知识图谱渲染与节点交互
4. 生成目标资源
5. 学习资源页面
6. AI 学习对话（Socrates / Profiler）
7. 代码沙箱运行
8. 掌握进度 / BKT 热力图
9. 学习画像
10. portrait 路由别名检查
11. 刷新持久化
12. 后端数据校验（判题、资源生成、热力图、学习规划）

---

## 三、执行结果汇总

| 检查项 | 结果 | 说明 |
|--------|------|------|
| 前端 `npm run build` | ✅ 通过 | 已先修复 3 处 TS `never read` 错误 |
| 后端 `/health` | ✅ 正常 | `{"status":"ok"}` |
| 课程门户 | ✅ 正常 | 渲染课程卡片与登录面板 |
| 进入课程工作台 | ✅ 正常 | 自动创建会话，topbar 显示会话 ID |
| 知识图谱 | ✅ 正常 | 路径渲染、节点可点击 |
| 规划路径 | ✅ 正常 | 点击后更新路径状态 |
| 生成目标资源 | ✅ 正常 | 按钮点击后接口返回 200 |
| 学习资源 | ✅ 正常 | 页面渲染，包含认知风格切换 |
| AI 对话 | ✅ 正常 | 用户提问后收到 Socrates / Profiler 回复 |
| 代码沙箱 | ✅ 正常 | 默认代码与自定义代码均可运行 |
| 掌握进度 / 热力图 | ✅ 正常 | 显示真实练习记录 `Python简介 88%` |
| 学习画像 | ✅ 正常 | 画像、Agent 协作、工作区均渲染 |
| 后端 API 校验 | ✅ 正常 | judge passed、资源生成 200、heatmap 有数据 |
| **目标概念保留** | ❌ **失败** | URL 指定 `文件读写`，UI 实际目标为 `Python简介` |
| **会话刷新持久化** | ❌ **失败** | 刷新后会话 ID 改变，学习时长归零 |
| **图谱视图切换** | ⚠️ 未命中 | 测试脚本未找到“力导向结构”“六边形路径”按钮 |

---

## 四、截图清单

所有截图保存在 `docs/test-screenshots/`：

| 序号 | 文件名 | 说明 |
|------|--------|------|
| 01 | `student_flow_01_portal_landing.png` | 课程门户首页 |
| 01b | `student_flow_01b_course_bootstrapped.png` | 进入课程后工作台初始化 |
| 02 | `student_flow_02_graph_path_loaded.png` | 知识图谱路径加载完成 |
| 03 | `student_flow_03_graph_node_selected.png` | 点击知识节点后 |
| 04 | `student_flow_04_graph_path_planned.png` | 点击“规划路径”后 |
| 05 | `student_flow_05_graph_structure_view.png` | 尝试切换力导向结构视图 |
| 06 | `student_flow_06_graph_back_to_path.png` | 尝试返回六边形路径视图 |
| 07 | `student_flow_07_generate_resource_clicked.png` | 点击“生成目标资源” |
| 08 | `student_flow_08_resources_page.png` | 学习资源页面 |
| 09 | `student_flow_09_resources_timeline_and_evolution.png` | 资源时间线与演进 |
| 10 | `student_flow_10_chat_empty.png` | AI 对话空态 |
| 11 | `student_flow_11_chat_typed.png` | 输入问题后 |
| 12 | `student_flow_12_chat_reply.png` | 收到 AI 回复 |
| 13 | `student_flow_13_chat_followup.png` | 追问后 |
| 14 | `student_flow_14_code_initial.png` | 代码沙箱初始状态 |
| 15 | `student_flow_15_code_run_output.png` | 运行默认代码输出 |
| 16 | `student_flow_16_code_custom_run.png` | 运行自定义代码 |
| 17 | `student_flow_17_progress_top.png` | 掌握进度顶部统计 |
| 18 | `student_flow_18_progress_heatmap.png` | 掌握度热力图 |
| 19 | `student_flow_19_progress_heatmap_focus.png` | 热力图聚焦 |
| 20 | `student_flow_20_profile.png` | 学习画像页面 |
| 21 | `student_flow_21_portrait_alias_check.png` | portrait 路由兼容性检查 |
| 22 | `student_flow_22_after_refresh.png` | 刷新页面后会话状态 |

---

## 五、发现的问题

### 问题 1：目标概念 fallback 策略错误（高优先级）

**现象**：
- 测试 URL：`http://localhost:4173/#/portal?target_concept=文件读写`
- UI 实际目标：`Python简介`
- 导致练习判题、资源生成、学习画像均围绕 `Python简介` 进行。

**根因**：`frontend/src/App.tsx` 中 `bootstrap()` 只有在目标属于“基础/难度 ≤ 2”节点时才保留，否则回退到最基础节点。`文件读写` 不是基础节点，因此被强制改回 `Python简介`。

**建议**：只要目标概念存在于知识图谱节点列表中即保留；仅当目标不存在或不合法时才回退。

---

### 问题 2：刷新后会话丢失（高优先级）

**现象**：
- 刷新前 topbar 会话 ID：`EH-FF8750B3-C6B`
- 刷新后 topbar 会话 ID：`EH-F3FF2BED-59F`
- `localStorage.getItem('eduhive.session_id')` 为 `None`
- 今日学习时长从 2 分钟变回 0 分钟。

**根因**：新仓库没有在 `localStorage` 中持久化 `session_id`，刷新后 `App.tsx` 会重新调用 `sessionApi.create()` 创建新会话。

**建议**：
1. 创建会话后将 `session_id` 写入 `localStorage`。
2. 启动时若 `localStorage` 中有有效 `session_id`，优先调用 `GET /api/sessions/{id}` 恢复旧会话，避免重复创建。

---

### 问题 3：同一页面目标概念显示不一致（中优先级）

**现象**：在多个页面中同时出现以下不同目标：
- topbar 学习目标：`Python简介`
- 顶部 banner：“当前正在学习「文件操作」”
- 学习对话当前目标：`Python简介`
- 右侧资源工作区：`文件操作`
- 学习画像目标：`Python简介`

**根因**：不同组件使用了不同的状态源（`targetConcept`、`selectedConcept`、`resourceConcept`、`session.target_concept`），且 fallback 逻辑导致它们不同步。

**建议**：统一使用单一数据源（如 `session.target_concept`），并在 `bootstrap()` 中一次性写入所有相关状态。

---

### 问题 4：热力图单条记录时布局拉伸（中优先级）

**现象**：当只有 1 条非默认掌握记录时，热力格占满整行，视觉比例失衡。

**根因**：`.heatmap-grid` 使用 `grid-template-columns: repeat(auto-fit, minmax(150px, 1fr))`，单元素时会拉伸到 `1fr`。

**建议**：限制单格最大宽度，例如 `max-width: 240px`，或增加 `fit-content` 约束。

---

### 问题 5：知识图谱视图切换按钮未命中（低优先级）

**现象**：测试脚本点击“力导向结构”“六边形路径”失败。

**可能原因**：新仓库的视图切换按钮文案或 DOM 结构与旧仓库不同。

**建议**：确认新仓库的视图切换实现，并同步更新测试脚本中的按钮文本。

---

## 六、后端数据校验

| 接口 | 请求 | 结果 |
|------|------|------|
| `POST /api/code/judge` | 文件读写代码 + expected_output=hello | `passed=true` |
| `POST /api/resources/generate-for-session/{id}` | concept=Python简介 | HTTP 200 |
| `GET /api/evaluation/heatmap` | session_id=ff8750b3-... | 1 条非默认记录：`Python简介 0.8811` |
| `GET /api/learning-plan/{id}` | session_id=ff8750b3-... | HTTP 200 |

---

## 七、结论

本次测试表明，新仓库 `RJBRJB` 的整体功能链路已基本跑通：前端构建、后端 API、AI 对话、代码沙箱、资源生成、BKT 热力图等核心功能均可正常工作。但存在两个高优先级稳定性问题：

1. **目标概念 fallback 错误** 会导致用户自定义目标被强制改回基础节点。
2. **会话刷新丢失** 会导致学习记录无法持续累积，严重影响学习闭环。

建议优先修复这两个问题后再继续扩展新功能。

---

## 八、后续行动建议

1. **修复目标概念 fallback**（参考旧仓库 `RJB_Demo` 提交 `fda1ccb`）。
2. **修复会话持久化**：在 `localStorage` 保存并恢复 `session_id`。
3. **统一目标概念状态源**，消除同一页面显示不一致。
4. **优化热力图布局**，限制单格最大宽度。
5. **确认知识图谱视图切换文案**，更新测试脚本。
6. **推送当前已提交的改动**（`612c52d`）到远端，需先解决 GitHub 写权限问题。

---

*报告生成时间：2026-07-15*  
*生成工具：Kimi WebBridge 端到端测试脚本*
