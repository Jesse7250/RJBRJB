# 2026-07-03 后端真实数据闭环更新报告

## 1. 提交分支

- 当前分支：`feature/frontend-command-center`
- 对应分工：后端支持成员 C 的 Command Center 前端，补齐画像证据、Agent 状态、学习时长等真实字段。
- 提交哈希：`b2cb994`
- 远程仓库：`PeiChen1215/RJB_demo`

## 2. 今日主要更新内容

### 2.1 学习画像真实数据闭环

- 在 `backend/app/services/database.py` 中实现：
  - `calculate_learning_minutes(session_id)`：基于 `learning_events` 的有效事件时间间隔计算学习时长，空闲阈值 300 秒。
  - `calculate_streak_days(session_id)`：基于有效学习事件的日期去重，计算连续学习天数。
  - `calculate_profile_confidence(session_id)`：基于 `cognitive_profile_evidence` 证据权重累计计算画像置信度（上限 0.95）。
- 在 `backend/app/api/sessions.py` 中：
  - `GET /api/sessions/{id}/profile/evidence` 返回按维度聚合的画像证据，以及 `confidence` 字段。
  - `GET /api/sessions/{id}/stats` 返回 `daily_learning_minutes` 和 `streak_days`。

### 2.2 Agent 协作状态真实接口

- 在 `backend/app/services/database.py` 中新增 Agent trace 读写函数。
- 在 `backend/app/api/sessions.py` 中新增 `GET /api/sessions/{id}/agent-trace`。
- 前端 `frontend/src/App.tsx` 的 `AgentPanel` 改为每 6 秒拉取真实 trace，展示：
  - 每个 Agent 最近一次调用耗时。
  - 运行中 / 失败 / 在线状态。
  - 活跃任务数与链路健康度。

### 2.3 练习题 expected_output 自动推导

- 修改 `backend/app/agents/generator.py`：
  - 生成资源包后调用 `_normalize_exercises`，对缺失 `expected_output` 的练习题执行 `solution` 代码，将 stdout 作为期望输出回填。
  - 在生成 Prompt 中明确强调每道练习题必须提供 `expected_output`。
- 效果：资源生成后，能输出可执行结果的练习题可自动判题；solution 无输出的题目仍保留空 `expected_output`，前端提示用户查看参考答案。

### 2.4 苏格拉底辅导上下文连续性

- 在 `backend/app/agents/orchestrator.py` 中：
  - `_route` 优先判断 `_is_continue_tutor`，避免“继续引导”被意图分类抢走。
  - `_tutor_flow` 从 `session["socratic_depth"]` 读取并回写轮次，支持多轮苏格拉底追问。

### 2.5 其他修复

- `backend/app/agents/llm.py`：对 `LLM_PROVIDER` 环境变量增加 `.strip().lower()`，兼容首尾空格导致的提供者解析失败。

## 3. 涉及文件

- `backend/app/services/database.py`
- `backend/app/api/sessions.py`
- `backend/app/agents/orchestrator.py`
- `backend/app/agents/generator.py`
- `backend/app/agents/llm.py`
- `frontend/src/App.tsx`
- `frontend/src/services/api.ts`

## 4. 验证结果

### 4.1 C4 Demo 主链路联调

运行 `logs/c4_demo_chain.py`（端口 8000），全部节点通过：

- 创建会话
- 初始画像证据为空
- 学习资源请求返回路径与概念
- 代码判题通过（`expected_output: 30`，`passed: true`）
- 苏格拉底辅导第 1 轮进入 `clarification` 阶段
- 继续引导第 2 轮进入 `assumption_probe` 阶段
- 学习评估返回薄弱点
- 会话统计返回 `daily_learning_minutes: 1`，`streak_days: 1`
- 模拟前端行为埋点后画像证据聚合成功，`confidence: 0.9`

### 4.2 后端测试

```powershell
cd backend
$env:LLM_PROVIDER='mock'
.\venv\Scripts\python.exe -m pytest tests/test_api.py tests/test_database.py tests/test_main_chain_integration.py tests/test_code_executor.py -q
```

结果：**20 passed**

### 4.3 前端构建

```powershell
cd frontend
npm run build
```

结果：TypeScript 检查与 Vite 打包均通过。

## 5. 本次后续补充（同日完成）

- **前端 `App.tsx` 单文件拆分**：已将 `ProfilePanel`、`AgentPanel`、`LearningMeter`、`StreakCard`、`HeatmapPanel`、`ResourceLibraryPanel`、`TopBar`、`WorkspaceDock` 抽到 `frontend/src/components/command-center/`，公共类型抽到 `types.ts`。`App.tsx` 从约 2814 行降至约 1707 行，`npm run build` 通过。

## 6. 仍需后续处理
- **知识图谱后端驱动布局**：C 同学报告 4.4 提到由后端返回节点坐标/路径，可后续在 `backend/app/api/graph.py` 补充 `/graph/layout` 与 `/graph/path`。
- **BKT 默认参数说明**：C 同学报告 5.6 提到默认 guess/slip 容易误导，可在 `backend/app/services/bkt.py` 返回 `is_default`、`sample_count`、`last_updated` 等字段。
- **资源生成接口改为 POST JSON body**：C 同学报告 5.7 提到复杂 profile 不适合 query 参数，可后续统一为 JSON body。

## 7. 与 C 同学更新报告的对应关系

| C 同学报告章节 | 本次后端处理 |
|---|---|
| 4.1 / 5.3 画像证据与置信度 | 已实现真实 `profile_confidence` 与按维度聚合证据 |
| 4.2 / 5.4 Agent 状态接口 | 已实现 `/agent-trace` 并接入前端展示 |
| 4.3 / 5.5 学习时长与连续天数 | 已实现按事件的真实计算 |
| 4.7 苏格拉底上下文连续性 | 已修复 `_is_continue_tutor` 优先级与 `socratic_depth` 持久化 |
| 5.8 后端中文编码 | 验证数据库/文件操作使用 Python UTF-8 脚本 |
