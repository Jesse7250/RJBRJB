# 智慧伴学 EduMate 环境搭建指南

本文档用于从零配置并运行当前项目。默认前端端口为 `5173`，后端端口为 `8001`。

## 1. 环境要求

| 工具 | 建议版本 | 检查命令 |
| --- | --- | --- |
| Git | 任意可用版本 | `git --version` |
| Node.js | 20 LTS，最低 18 | `node --version` |
| npm | 随 Node.js 安装 | `npm --version` |
| Python | 3.11 | `python --version` |
| Conda | 可选 | `conda --version` |
| Docker Desktop | 可选 | `docker --version` |

## 2. 获取项目

```powershell
cd I:\project\rjb
git clone git@github.com:Jesse7250/RJBRJB.git
cd RJBRJB
git checkout feature/full-project-sync-20260714
```

如果已经 clone 过：

```powershell
cd I:\project\rjb\RJBRJB
git checkout feature/full-project-sync-20260714
git pull --ff-only origin feature/full-project-sync-20260714
```

## 3. 后端配置

### 3.0 双击一键启动

Windows 环境下可在项目根目录直接双击 `Launch_EduMate.bat` 或 `启动项目.bat`。

脚本会自动执行以下步骤：

- 检查 Node.js、npm 和 Python。
- 创建 `backend\.env`。
- 未配置真实 API Key 时，自动使用 `mock` 大模型和内存知识图谱启动基础演示。
- 安装后端和前端依赖。
- 分别启动后端 `8001` 与前端 `5173`。
- 前端就绪后自动打开浏览器进入课程广场。

如需使用真实 DeepSeek 与讯飞 TTS，请先编辑 `backend\.env` 后重新启动。

### 3.1 准备环境变量

```powershell
cd I:\project\rjb\RJBRJB
copy backend\.env.example backend\.env
```

然后编辑 `backend\.env`：

- `DEEPSEEK_API_KEY`：DeepSeek API Key。填写后可使用真实大模型生成。
- `DEEPSEEK_MODEL`：项目建议使用 `deepseek-v4-pro`。
- `SPARK_TTS_APP_ID`、`SPARK_TTS_API_KEY`、`SPARK_TTS_API_SECRET`：讯飞 TTS 语音合成配置。
- `SPARK_TTS_API_URL`：填写你在讯飞控制台开通的 TTS 地址。
- `GRAPH_BACKEND`：本地演示建议用 `memory`；有 Neo4j 时可改为 `neo4j`。

不要把 `backend\.env` 提交到 GitHub。

### 3.2 使用项目已有 Conda 环境运行

如果项目目录下已有 `.conda` 环境：

```powershell
cd I:\project\rjb\RJBRJB\backend
..\.conda\python.exe -m pip install -r requirements.txt
..\.conda\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

如果本机复用旧项目 `RJB_demo` 中的 Conda 环境：

```powershell
cd I:\project\rjb\RJBRJB\backend
I:\project\rjb\RJB_demo\.conda\python.exe -m pip install -r requirements.txt
I:\project\rjb\RJB_demo\.conda\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

### 3.3 使用 Conda 新建环境

```powershell
cd I:\project\rjb\RJBRJB
conda env create -f environment.yml
conda activate edumate-rjb
python -m pip install -r backend\requirements.txt
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

### 3.4 使用启动脚本

```powershell
cd I:\project\rjb\RJBRJB
powershell -ExecutionPolicy Bypass -File .\scripts\start_backend.ps1
```

## 4. 前端配置

打开一个新的 PowerShell 窗口：

```powershell
cd I:\project\rjb\RJBRJB\frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

也可以使用脚本：

```powershell
cd I:\project\rjb\RJBRJB
powershell -ExecutionPolicy Bypass -File .\scripts\start_frontend.ps1
```

浏览器访问：

```text
http://127.0.0.1:5173/#/portal
```

## 5. Docker Compose 运行

Docker Compose 会同时启动 Neo4j、后端和前端。

`Dockerfile` 描述单个服务的构建方式，`docker-compose.yml` 描述前端、后端和 Neo4j 如何一起启动。安装 Docker Desktop 后，可以用这一方式减少手动配置 Python、Node.js 与图数据库环境的步骤。

```powershell
cd I:\project\rjb\RJBRJB
copy backend\.env.example backend\.env
docker compose up --build
```

访问：

```text
http://127.0.0.1:5173/#/portal
```

## 6. 运行检查

后端健康检查：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8001/health/detail"
```

TTS 状态检查：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8001/api/tts/status"
```

前端构建检查：

```powershell
cd I:\project\rjb\RJBRJB\frontend
npm run build
```

## 7. 常见问题

### 前端提示后端连接中断

确认后端是否运行在 `8001`：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8001/health"
```

当前 `frontend/vite.config.ts` 已将 `/api` 和 `/health` 代理到 `http://localhost:8001`。

### `vite` 不是内部或外部命令

说明前端依赖未安装，执行：

```powershell
cd I:\project\rjb\RJBRJB\frontend
npm install
```

### 后端报 `ModuleNotFoundError: No module named 'app'`

启动后端时要进入 `backend` 目录：

```powershell
cd I:\project\rjb\RJBRJB\backend
..\.conda\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

### 讯飞 TTS 状态为可用但页面不播放

先检查接口是否能返回音频：

```powershell
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8001/api/tts/synthesize" -ContentType "application/json" -Body '{"text":"你好，我是智慧伴学的数字人助教。","voice":"x4_xiaoyan"}'
```

如果接口正常但浏览器不播放，检查浏览器控制台是否有音频加载错误或跨域错误。

### 不配置 API Key 能不能运行

可以运行基础流程。未配置 DeepSeek 或讯飞 TTS 时，部分大模型生成、数字人回复和高质量语音会进入降级逻辑；比赛展示建议填写真实 API Key。
