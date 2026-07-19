# 智慧伴学 EduMate

> 第十五届中国软件杯 A 组参赛作品
> 赛题方向：基于大模型的个性化资源生成与学习多智能体系统开发
> 项目定位：面向 Python 程序设计课程的多智能体个性化学习平台

## 项目简介

智慧伴学 EduMate 是一个面向学生、教师和管理员的智能学习平台。系统以 Python 程序设计课程为核心场景，整合知识图谱、学习资源生成、AI 学习对话、代码沙箱、掌握度评估、教师课程建设、管理员课程审核和数字人导学等功能。

平台后端基于 FastAPI，前端基于 React + Vite + TypeScript。多智能体链路围绕学习画像、路径规划、资源生成、苏格拉底式引导、资源审核和掌握度评估展开，支持接入 DeepSeek 大模型、讯飞语音合成和 Neo4j 知识图谱；在外部服务不可用时，可使用本地内存图谱与降级逻辑保证基础演示可运行。

## 核心功能

- 课程广场：登录、注册、角色入口、课程筛选与课程进入。
- 学生学习工作台：知识图谱、学习资源、学习对话、代码沙箱、掌握进度、学习画像。
- 知识图谱：展示课程知识点关系、路径终点、节点详情、动态路径与节点资源生成入口。
- 学习资源：讲义、导图、练习题、代码案例、视频讲解、听觉型讲解、审核报告与资源反馈。
- 学习对话：面向学习问题的 AI 辅导、苏格拉底式追问、学习画像联动与 Agent 状态展示。
- 代码沙箱：运行 Python 示例代码，展示输出与变量快照，并支持练习题判题。
- 掌握进度：基于学习行为和练习结果展示掌握度、热力图和学习建议。
- 教师端：创建课程、维护课程资料、提交课程发布审核、删除本人课程。
- 管理端：审核教师提交的课程，管理课程发布状态、学生和教师用户。
- 数字人导学：课程广场和课程内均保留数字人入口，用于页面使用引导和学习辅助。

## 技术栈

| 层级 | 技术 |
| --- | --- |
| 前端 | React 18、Vite、TypeScript、Tailwind CSS、Framer Motion、Monaco Editor、Mermaid、ECharts |
| 后端 | FastAPI、Python 3.11、Pydantic、SQLite、JWT、bcrypt |
| 多智能体 | Orchestrator、Profiler、Navigator、Generator、Reviewer、Socrates |
| 大模型 | DeepSeek API，保留讯飞星火配置入口，支持 mock/auto 降级 |
| 语音合成 | 讯飞 TTS，浏览器语音作为前端降级 |
| 知识图谱 | 内存图谱默认可用，可选 Neo4j |
| 部署 | 本地启动脚本、Conda、Docker Compose |

## 快速启动

推荐使用当前项目约定端口：

- 后端：`http://127.0.0.1:8001`
- 前端：`http://127.0.0.1:5173`
- 前端代理：`/api` 和 `/health` 均转发到后端 `8001`

### 方式零：双击启动

Windows 环境下可直接双击根目录的 `启动项目.bat`。

该脚本会自动检查 Node.js、npm 与 Python，安装前后端依赖，创建 `backend\.env`，并分别启动后端和前端。若未填写真实 API Key，脚本会使用 `mock` 大模型与内存知识图谱启动基础演示流程；如需真实 DeepSeek 与讯飞 TTS，请先编辑 `backend\.env` 后再启动。

### 方式一：Windows 本地启动

后端：

```powershell
cd I:\project\rjb\RJBRJB
copy backend\.env.example backend\.env
# 编辑 backend\.env，填入 DeepSeek 和讯飞 TTS 配置；不填也可用部分降级能力
powershell -ExecutionPolicy Bypass -File .\scripts\start_backend.ps1
```

前端：

```powershell
cd I:\project\rjb\RJBRJB
powershell -ExecutionPolicy Bypass -File .\scripts\start_frontend.ps1
```

访问：

```text
http://127.0.0.1:5173/#/portal
```

### 方式二：手动启动

后端：

```powershell
cd I:\project\rjb\RJBRJB\backend
..\.conda\python.exe -m pip install -r requirements.txt
..\.conda\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

前端：

```powershell
cd I:\project\rjb\RJBRJB\frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

### 方式三：Docker Compose

```powershell
cd I:\project\rjb\RJBRJB
copy backend\.env.example backend\.env
docker compose up --build
```

访问：

```text
http://127.0.0.1:5173/#/portal
```

## 主要 API

| 接口 | 说明 |
| --- | --- |
| `GET /health` | 后端基础健康检查 |
| `GET /health/detail` | 服务、数据库、图谱与缓存统计 |
| `POST /api/auth/register` | 用户注册 |
| `POST /api/auth/login` | 用户登录 |
| `POST /api/sessions/` | 创建学习会话 |
| `POST /api/sessions/{id}/chat` | 学习对话 |
| `POST /api/sessions/{id}/events` | 记录学习行为 |
| `POST /api/resources/generate` | 生成学习资源 |
| `GET /api/resources/stream-generate` | 流式生成学习资源 |
| `POST /api/code/execute` | 执行 Python 代码 |
| `POST /api/code/judge` | 练习题判题 |
| `GET /api/graph/` | 获取知识图谱 |
| `GET /api/graph/concept/{concept}` | 获取知识点详情 |
| `GET /api/evaluation/*` | 掌握度与学习评估 |
| `GET /api/learning-plan/*` | 学习计划与学习时长 |
| `GET /api/teacher/*` | 教师课程管理 |
| `GET /api/admin/*` | 管理端课程和用户管理 |
| `GET /api/assistant/*` | 数字人助教 |
| `GET /api/tts/status` | 讯飞 TTS 配置状态 |
| `POST /api/tts/synthesize` | 文本转语音 |

## 验证命令

后端导入检查：

```powershell
cd I:\project\rjb\RJBRJB\backend
..\.conda\python.exe -m py_compile app\main.py
```

后端接口检查：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8001/health/detail"
Invoke-RestMethod -Uri "http://127.0.0.1:8001/api/tts/status"
```

前端构建检查：

```powershell
cd I:\project\rjb\RJBRJB\frontend
npm run build
```

## 项目结构

```text
RJBRJB/
├─ backend/                 FastAPI 后端、多智能体、数据库、TTS、图谱服务
├─ frontend/                React 前端、课程广场、学生端、教师端、管理端
├─ data/                    知识图谱种子数据
├─ docs/                    设计文档、接口说明、测试报告、更新报告
├─ scripts/                 Windows 本地启动脚本
├─ docker-compose.yml       容器化启动配置
├─ environment.yml          Conda 环境配置
├─ SETUP.md                 环境搭建说明
└─ README.md                项目总览
```

## 提交注意事项

可以提交源码、配置模板、依赖清单、文档、脚本、静态展示素材和示例数据。不要提交真实密钥、本机虚拟环境、`node_modules`、构建产物、运行数据库、日志和临时测试音频。

真实密钥只应写入本机 `backend/.env`，仓库中只保留 `backend/.env.example`。
