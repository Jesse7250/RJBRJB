# 智慧伴学 EduMate 更新报告

**日期**：2026-06-30  
**版本**：main@c542a82  
**主题**：A/B 前后端接口联调收尾（C9/C10/C11 + 判题→知识熔炉链路）

---

## 一、本次完成内容

### 1. 后端：判题 → 知识熔炉触发链路
- `backend/app/api/code.py`
  - 新增 `POST /api/code/seed-failed-submissions` 测试端点，用于快速制造失败提交并触发资源重审。
  - `POST /api/code/judge` 在判题失败且指定知识点时，后台调用 `trigger_resource_review(concept, "error_rate")`。
- `backend/app/services/knowledge_furnace.py`
  - 当全局错误率 ≥ 阈值且样本数足够时，自动生成新版本并写入 `resource_version`。

### 2. 后端稳定性修复
- `backend/app/services/database.py`：修复 `NotFoundError` 未捕获导致 500 的问题；新增 `find_latest_generation_task_by_concept`。
- `backend/app/agents/reviewer/reviewer_agent.py`：修复缓存命中时 Pydantic 对象未转 dict 的 bug。
- `backend/app/agents/orchestrator.py`：`_safe_run/_safe_run_async` 增加 30s 超时 + 连续失败熔断 + 降级模板。
- `backend/app/services/deepseek_llm.py` / `backend/app/core/config.py`：LLM 已切换至 `deepseek-v4-flash`。
- 多处 `datetime.utcnow()` 改为 `datetime.now(timezone.utc)`，消除弃用警告。

### 3. 前端：C9 / C10 / C11 可解释组件
- 新增 `frontend/src/components/resources/ThinkingPathReplay.tsx`（C9）
  - 调用 `/api/resources/thinking-path`，以步骤条形式回放资源生成过程。
- 新增 `frontend/src/components/resources/VariableVisualizer.tsx`（C10）
  - 在练习/代码案例中解析并展示顶层变量赋值。
- 新增 `frontend/src/components/resources/FurnaceTimeline.tsx`（C11）
  - 调用 `/api/resources/versions`，以垂直时间线展示知识熔炉版本演进。
- `frontend/src/components/resources/ResourceViewer.tsx`
  - 扩展为 6 标签页：文档 / 导图 / 练习 / 审核 / 思维路径 / 版本。
- `frontend/src/services/api.ts`：新增 `ResourceVersion`、`ThinkingStep` 类型及对应接口。
- `frontend/src/App.tsx`：集成新组件与标签切换。

### 4. 测试修复
- `backend/tests/test_knowledge_furnace.py`
  - `test_trigger_resource_review_creates_version` 改用 UUID 唯一概念，避免历史测试数据导致版本号断言失败。

---

## 二、联调验证结果

| 验证项 | 方式 | 结果 |
|--------|------|------|
| 判题→知识熔炉触发 | `/api/code/seed-failed-submissions` + 查看 `/api/resources/versions` | 生成版本 2，`triggered_by=error_rate` |
| 前端版本时间线 | WebBridge 截图 | “知识熔炉 · 版本演进”正常渲染版本 2、变更原因、触发来源 |
| 掌握进度热力图 | 构造真实提交 → `/api/evaluation/analyze` → WebBridge 截图 | 正确显示“变量与赋值 100% / 8 次练习 / 已掌握” |
| 前端生产构建 | `npm run build` | 通过（仅 pyodide Node 模块 externalize 警告） |
| 后端回归测试 | mock 模式 pytest | **11 passed** |

---

## 三、已知待跟进

- 热力图测试数据构造过程中发现：PowerShell 直接发 JSON 时中文概念名可能变成 `?????`，建议后续脚本统一使用 Python `requests` 发送 UTF-8 请求。
- 完整 pytest 在真实 DeepSeek 模式下耗时过长，建议 CI 固定使用 `LLM_PROVIDER=mock`。
- 前端 Radix Tabs 在 WebBridge 合成点击事件下未能切换，需通过 React Provider 状态直接设置，已作为验证技巧记录，不影响真实用户操作。

---

## 四、提交记录

- **Commit**：`c542a82`
- **Push**：`origin/main`（`b65673e..c542a82`）
- **变更文件数**：15 个文件，730 行新增，27 行删除
