# 智学蜂巢 EduHive —— 基于多智能体协同的 Python 个性化学习系统

> 第十五届中国软件杯大赛 A组参赛作品  
> 赛题：基于大模型的个性化资源生成与学习多智能体系统开发  
> 出题企业：科大讯飞股份有限公司

---

## 项目简介

智学蜂巢（EduHive）是一个面向高等教育 **Python 程序设计课程** 的多智能体协同个性化学习系统。系统融合 **DeepSeek / 讯飞星火大模型**、**Neo4j / 内存知识图谱** 与自定义多智能体编排，通过对话式画像构建、神经符号约束生成、多 Agent 辩论议会审核、学习行为评估闭环、认知风格自适应渲染，实现“因材施教”的数字化落地。

---

## 核心亮点

1. **神经符号认知架构（Neuro-Symbolic）**  
   Neo4j 知识图谱为生成提供硬约束：前置知识、难度等级、易错点、禁用知识点，生成后通过 AST 校验防止“超纲”与幻觉。

2. **5 角色分层 + Society of Mind 辩论议会**  
   Orchestrator / Profiler / Navigator / Generator / Reviewer 五个执行角色通过统一消息总线协作；Reviewer 内部保留 Expert / Teacher / Student-Sim / Guardian 四个审核视角 Prompt 议会，投票通过后方可输出。

3. **认知风格自适应渲染引擎**  
   同一资源根据学生的场依存/独立、视觉/听觉/动觉偏好，呈现不同 UI 形态。

4. **Pyodide 浏览器 Python 沙箱**  
   代码实时运行、零网络延迟，Demo 体验极佳。

5. **构建与缓存优化**  
   - 后端 `resource_cache` 按 `(concept, profile_hash)` 缓存已审核资源，重复生成从 ~3s 降至 ~0.02s。
   - 前端 `KnowledgeGraph`、`PyodideSandbox`、`ResourceViewer` 使用 React.lazy 懒加载，`index` 主 chunk 从 465KB 降至 ~98KB。

---

## Agent 架构（5 角色分层）

```
User ──► Orchestrator ──► Profiler ──► Navigator ──► Generator ──► Reviewer
                              ▲                                    │
                              └────────── 学习事件反馈 ──────────────┘
```

| 角色 | 职责 | 备注 |
|------|------|------|
| **Orchestrator** | 意图识别、会话状态维护、按 SOP 路由消息 | 对外保持 `handle_chat` / `generate_resource` 等接口稳定 |
| **Profiler** | 解析学生输入，更新认知画像 | 输出视觉/听觉/动觉、场依存/独立等维度 |
| **Navigator** | 基于知识图谱规划学习路径 | 推荐前置/当前/后续知识点 |
| **Generator** | 生成个性化教学资源包 | 含讲义、示例、练习、代码题 |
| **Reviewer** | 资源审核、苏格拉底辅导、学习评估 | 内部 4-Prompt 辩论议会 + BKT 评估 |

所有 Agent 通过 `AgentMessage` 协议通信，便于后续迁移至 LangGraph / AutoGen 等框架。

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React 18 + Vite + TypeScript + Tailwind CSS + shadcn/ui + Monaco Editor + Pyodide |
| 后端 | FastAPI + Python 3.10+ |
| 大模型 | DeepSeek-V2 / 讯飞星火 4.0 / Mock（可切换） |
| 多智能体 | 自定义 Agent Orchestrator（5 角色消息总线）+ Reviewer 内部 4-Prompt 辩论议会 |
| 知识图谱 | Neo4j Community / 内存图（无 Docker 自动降级） |
| 数据库 | SQLite（用户、会话、学习记录、资源缓存） |
| 认证 | JWT + bcrypt |
| 性能优化 | SQLite 资源缓存、前端组件懒加载 |
| 部署 | Docker Compose / 本地开发 |

---

## 快速启动

### 方式一：Docker Compose 一键启动（推荐，用于比赛交付）

```bash
cp backend/.env.example backend/.env
# 编辑 backend/.env，填入你的讯飞 API Key
docker-compose up --build
```

访问：http://localhost:5173

### 方式二：本地开发

#### 1. 启动 Neo4j（可选，未启动时自动使用内存图）

```bash
docker run -d \
  --name eduhive-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/eduhive123 \
  neo4j:5.15-community
```

#### 2. 启动后端

```bash
cd backend
copy .env.example .env
# 编辑 .env，填入 DEEPSEEK_API_KEY 或讯飞相关 Key
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

---

## 主要 API 接口

| 接口 | 说明 |
|------|------|
| `GET /health` | 健康检查 |
| `GET /health/detail` | 服务与数据库统计 |
| `POST /api/auth/register` | 用户注册 |
| `POST /api/auth/login` | 用户登录，返回 JWT |
| `POST /api/sessions/` | 创建学习会话（可选 Bearer Token） |
| `GET /api/sessions/` | 获取当前用户会话列表 |
| `POST /api/sessions/{id}/chat` | 同步对话 |
| `GET /api/sessions/{id}/chat-stream` | SSE 流式对话 |
| `POST /api/sessions/{id}/events` | 提交学习事件 |
| `POST /api/sessions/{id}/evaluate` | 学习效果评估 |
| `POST /api/resources/generate` | 同步生成资源 |
| `GET /api/resources/stream-generate` | SSE 流式生成资源 |
| `POST /api/code/execute` | Python 代码执行 |
| `POST /api/code/judge` | 代码判题 |
| `GET /api/graph/` | 知识图谱数据 |

## 测试

后端一键测试（11 个脚本）：

```bash
cd backend
.\venv\Scripts\python.exe run_tests.py
```

前端构建验证：

```bash
cd frontend
npm run build
```

---

## 项目结构

```
RJB_Demo/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── agents/          # 多智能体实现
│   │   │   ├── generator.py       # GeneratorAgent（原 BuilderAgent）
│   │   │   ├── reviewer/          # ReviewerAgent（含 debate / socrates / evaluator）
│   │   │   └── orchestrator.py    # 5 角色消息路由编排
│   │   ├── api/             # RESTful API
│   │   ├── core/            # 配置、安全
│   │   ├── middleware/      # 请求日志中间件
│   │   ├── models/          # Pydantic 数据模型
│   │   └── services/        # 业务服务（LLM、Neo4j、SQLite、缓存）
│   └── *.py                 # 测试脚本
├── frontend/                # React 前端
│   └── src/
│       ├── components/      # 组件库
│       ├── pages/           # 页面
│       ├── hooks/           # 自定义 Hooks
│       ├── services/        # API 服务
│       ├── stores/          # Zustand 状态管理
│       └── types/           # TypeScript 类型
├── data/                    # 知识图谱种子数据
├── docs/                    # 比赛文档
├── docker-compose.yml
└── README.md
```

---

## 讯飞工具使用说明

| 工具 | 用途 | 说明 |
|------|------|------|
| 讯飞星火 4.5 Max | 主推理模型 | 资源生成、路径规划、辩论判断 |
| 讯飞星火 Spark Pro | 辅助模型 | 意图识别、快速问答 |
| 讯飞语音合成 TTS | 语音讲解 | 知识点音频讲解 |
| 讯飞 iFlyCode | 代码辅助 | 实操案例代码生成辅助 |

---

## 开源组件与协议

| 组件 | 协议 | 用途 |
|------|------|------|
| AutoGen | MIT | 多智能体框架 |
| FastAPI | MIT | Web 框架 |
| Neo4j Community | GPL v3 | 知识图谱 |
| Pyodide | MPL 2.0 | 浏览器 Python 执行 |
| Monaco Editor | MIT | 代码编辑器 |
| Mermaid.js | MIT | 思维导图渲染 |
| React | MIT | 前端框架 |
| shadcn/ui | MIT | UI 组件库 |

---

## 团队与版本

- 团队：智学蜂巢项目组
- 版本：v1.0
- 赛事：第十五届中国软件杯大赛 A组
