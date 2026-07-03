# `feature/frontend-command-center` 前端 Review 报告（第二轮）

> **日期**：2026-07-03  
> **Review 人**：后端/联调侧（Kimi Code CLI）  
> **被 Review 分支**：`feature/frontend-command-center`  
> **C 同学最新提交**：`b9f8dab feat(frontend): 完善指挥舱交互与更新报告`  
> **Review 侧追加提交**：`c30ff22 fix(frontend): 在 Command Center 画像面板恢复画像证据展示（适配 C 同学新版）`

---

## 一、总体评价

C 同学本轮提交**质量比上一轮高很多**，基本把第一轮 Review 里提出的 P0 功能回归问题都解决了。Command Center 视觉外壳保留，核心链路（画像 → 图谱 → 资源 → 对话 → 代码 → 进度）已经能真正接死后端，可以考虑在修复本轮剩余问题后合并到 `main`。

**当前状态：不建议直接合并，建议 C 同学按本清单再改一轮后，由后端/联调侧最终验收。**

---

## 二、已修复问题（表扬 👍）

| 第一轮问题 | 本轮状态 | 说明 |
|---|---|---|
| 苏格拉底辅导链退化成纯文本 | ✅ 已修复 | `SocraticPanel` 已接入聊天区，含阶段、提示、参考思路、继续引导按钮 |
| 掌握度热力图是装饰性网格 | ✅ 已修复 | 热力图现在按真实 `concept + mastery_probability + observation_count` 展示知识点卡片 |
| 学习资源页面只有壳 | ✅ 已修复 | 智能讲义/思维导图/练习题/代码案例/听觉讲解/审核报告 都能渲染 |
| 学习资源练习题显示的是答案 | ✅ 已修复 | 已区分题干、作答区、参考答案、判题结果 |
| 硬编码“Python 文件操作” | ⚠️ 部分修复 | 现在从 URL/localStorage 读取 `target_concept`，但 fallback 仍是“文件读写” |
| 代码沙箱变量快照不更新 | ✅ 已修复 | 运行后正确展示变量名/类型/值 |
| 后端接口对接 | ✅ 已完善 | 新增 `/resources/latest`、代码执行判题空输出保护、`PATCH /sessions/{id}/profile` 等 |

---

## 三、仍待修复问题

### P0 —— 合并前必须修完

#### 1. 去掉或标注“虚假数据”

**问题描述**：

页面中存在多处写死的好看数据，评委追问时容易穿帮。

**具体位置**：

| 位置 | 当前写死内容 | 建议处理 |
|---|---|---|
| `ProfilePanel` 底部状态条 | `画像置信度 92%` | 改为 `画像置信度 --（待后端支持）` 或隐藏 |
| `ProfilePanel` 底部状态条 | `学习轨迹：masteredCount / max(masteredCount+4, 8)` | 改为 `已掌握 X 个知识点` 或隐藏 |
| `AgentPanel` | 所有 Agent 在线、固定响应时间 `00:12` 等 | 改为“协作中枢在线”等概括性文案，不要写死具体时间 |
| 侧边栏 `LearningMeter` | 今日学习 42 分钟 / 目标 60 分钟 | 改为 `-- 分钟` 或标注“演示数据” |
| 侧边栏 `StreakCard` | 连续学习 7 天 | 改为 `-- 天` 或标注“演示数据” |

**验收标准**：

- 页面中不再出现“92%”、“42 分钟”、“7 天”等无法解释来源的数字。
- 所有展示型数据要么来自后端/统计，要么明确标注“演示数据”。

---

#### 2. 练习题 `expected_output` 缺失导致无法判题

**问题描述**：

资源生成后，很多练习题因为 `expected_output` 为空，页面提示“缺少期望输出，无法自动判题”。这会让 Demo 中“提交判题”按钮频繁不可用。

**根因分析**：

- 后端 `GeneratorAgent` 生成练习时 `expected_output` 本身为空；
- 本轮 C 同学把 `starter_code` 改为 TODO 注释（这是对的，防止答案泄露），但没有解决 `expected_output` 缺失问题。

**修改要求**：

1. **前端**：如果某题确实没有 `expected_output`，至少允许学生点击“运行”查看输出，而不是只能看参考答案。
2. **后端/GeneratorAgent**：尽量为每道练习题生成 `expected_output`；如果无法生成，则该题不放入 `exercises` 数组，或标记为 `auto_judge: false`。
3. **前端**：根据 `expected_output` 是否存在，动态显示“提交判题”或“运行查看输出”。

**验收标准**：

- 生成资源后，练习页至少 50% 以上题目可点击“提交判题”。
- 没有 `expected_output` 的题目也能通过“运行”按钮得到输出反馈。

**参考文件**：

- `backend/app/agents/generator.py`（`_build_package` 或练习生成逻辑）
- `frontend/src/App.tsx` 中 `ResourceLibraryPanel` 练习渲染部分

---

### P1 —— 建议本轮修完

#### 3. `App.tsx` 必须拆分

**问题描述**：

`frontend/src/App.tsx` 仍然是 1700+ 行的 monolith。所有子组件（`ProfilePanel / KnowledgePanel / ResourceLibraryPanel / ChatCommand / CodeCommand / HeatmapPanel / WorkspaceDock` 等）全写在一个文件里。

**影响**：

- 三人联调、Bug 修复、合并冲突会极度困难。
- 不符合我们之前建立的前端组件化规范。

**修改要求**：

把 `App.tsx` 中的子组件拆到独立文件，建议目录结构：

```
frontend/src/components/command-center/
  index.tsx                 # 导出 App
  App.tsx                   # 只负责导航和全局状态
  ProfilePanel.tsx
  AgentPanel.tsx
  KnowledgePanel.tsx
  ResourceLibraryPanel.tsx
  ChatCommand.tsx
  CodeCommand.tsx
  HeatmapPanel.tsx
  WorkspaceDock.tsx
  TopBar.tsx
  SideNav.tsx
  HexBackdrop.tsx
  MindmapReadable.tsx
  RichLearningText.tsx
  ...
```

**验收标准**：

- `frontend/src/App.tsx` 不存在，或行数 ≤ 400 行。
- `npm run build` 通过。
- 各页面功能与拆分前一致。

---

#### 4. 知识图谱路径建议由后端驱动

**问题描述**：

当前知识图谱节点布局是前端硬编码坐标，路径高亮也是前端根据 `plannedPath` 简单匹配。如果后端图谱结构变化，前端需要同步改代码。

**修改要求**：

短期（本轮）：
- 保持当前前端布局，但把节点坐标、路径边、推荐理由等抽到配置文件或从后端读取。

长期（决赛前）：
- 后端增加 `/api/graph/layout` 和 `POST /api/graph/path` 接口，返回节点坐标/层级、路径节点列表、推荐理由。
- 前端只负责渲染。

**验收标准（本轮）**：

- 节点坐标、路径高亮逻辑不在 `App.tsx` 里写死，至少抽到独立的 graph config 文件中。

---

#### 5. 代码沙箱离线能力丢失

**问题描述**：

新版 `CodeCommand` 只调用后端 `/code/execute`，失去了之前 `PyodideSandbox` 的浏览器本地执行能力。

**修改要求**：

二选一：
- **方案 A**：保留后端执行为主，但增加“离线模式”回退到 `PyodideSandbox`。
- **方案 B**：明确代码沙箱必须依赖后端，在页面增加提示“需连接后端服务”。

**验收标准**：

- 后端不可用时，代码沙箱有友好提示，或能降级到本地执行。

---

### P2 —— 可选优化

#### 6. 学习画像真实数据闭环

当前 `PATCH /sessions/{id}/profile` 已允许前端更新画像，但后端还没有根据行为事件自动推断画像变化的逻辑。这个可以作为后端后续任务，但 C 同学需要在画像页明确提示“当前为冷启动默认画像，后续由学习行为更新”。

#### 7. 认知风格切换后资源渲染

当前 `styleMode` 切换只改变全局 class，但没有像之前 `CognitiveStyleRenderer` 那样针对资源文档做视觉/听觉/动觉差异化渲染。建议把 `CognitiveStyleRenderer` 接回资源文档页。

---

## 四、特别提醒

### 1. 画像证据面板已重新集成

Review 侧已经在本分支上把第一轮被覆盖的 **B10 画像证据面板**重新集成到新版 `ProfilePanel` 中，提交为 `c30ff22`。

**C 同学继续修改前，请先执行**：

```bash
git pull origin feature/frontend-command-center
```

避免覆盖 `c30ff22`。

### 2. 不要直接合并到 `main`

当前分支虽然功能基本可用，但仍有 P0/P1 问题未解决，直接合并会导致 `main` 上出现“虚假数据”和难以维护的 monolith。

---

## 五、验收 Checklist

C 同学改完后，请逐项自检：

- [ ] 页面中不再出现“92%”、“42 分钟”、“7 天”等无来源数字。
- [ ] 生成资源后，练习页大部分题目可点击“提交判题”。
- [ ] 没有 `expected_output` 的题目可通过“运行”按钮得到输出反馈。
- [ ] `frontend/src/App.tsx` 行数 ≤ 400 行，或已不存在。
- [ ] `npm run build` 通过。
- [ ] `npm run lint` 无严重错误。
- [ ] 画像证据面板正常展示（拉取 `c30ff22` 后验证）。
- [ ] 苏格拉底辅导链可连续点击“继续引导”推进 5 个阶段。
- [ ] 热力图按真实知识点展示掌握度。
- [ ] 学习资源页可查看讲义、导图、练习、代码案例、审核报告。

全部勾选后，通知后端/联调侧做最终验收。

---

## 六、参考文档

- 第一轮 Review：`docs/frontend_command_center_review_20260702.md`
- C 同学更新报告：`docs/update_report_20260703_frontend_command_center.md`
- 后端联调脚本：`logs/c4_demo_chain.py`
