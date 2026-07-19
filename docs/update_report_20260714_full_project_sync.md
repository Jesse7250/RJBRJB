# 智慧伴学完整同步版更新报告（2026-07-14）

## 一、提交目的

本次提交用于将当前本地可运行的智慧伴学项目完整同步到远程新分支，方便队友直接拉取同一版代码进行联调、测试和后续合并。

本分支包含前端课程广场、课程学习工作台、学习资源三模式、数字人悬浮助手、讯飞 TTS、DeepSeek 接入、Agent 生成链路优化等近期修改内容。

注意：为避免密钥泄漏，`backend/.env` 不会提交。队友拉取代码后需要根据 `backend/.env.example` 创建自己的 `.env` 并填写 API Key。

## 二、主要更新内容

### 1. 环境变量模板整理

- 重写 `backend/.env.example`，补全当前项目实际使用的配置字段。
- 明确区分 DeepSeek、讯飞星火、讯飞 TTS、Neo4j、SQLite、CORS、运行模式等配置。
- 新增 `GRAPH_BACKEND`、`SPARK_TTS_API_URL`、`SPARK_TTS_API_PASSWORD`、`RESOURCE_CACHE_TTL_HOURS` 等字段说明。
- 使用占位符替代真实密钥，确保可以安全提交到 GitHub。
- 更新 `.gitignore`，忽略本地 TTS 测试音频 `backend/tts-test*.mp3`、`backend/tts-check*.mp3`。

### 2. DeepSeek / Agent 链路调整

- DeepSeek 模型配置统一指向 `deepseek-v4-pro`。
- 对 DeepSeek 调用逻辑做了兼容处理，避免 provider 与 endpoint 配置不一致导致回复异常。
- 优化 Agent 编排链路：
  - Navigator：负责学习路径规划。
  - Generator / Builder：负责资源生成。
  - Reviewer / Guardian：负责资源审核与安全检查。
  - Socrates：负责学习问题的苏格拉底式引导。
  - Profiler：负责学习画像更新。
- 对 Agent 超时和降级提示做了调整，提升失败时的可解释性。

### 3. 学习对话优化

- 修复学习对话默认输入语句和发送按钮逻辑。
- 用户未点击输入框时，可直接发送默认学习问题。
- 用户点击输入框但没有输入任何内容时，发送按钮禁用，避免误发空消息。
- 优化苏格拉底式引导显示：
  - 学习问题才进入引导式回答。
  - 普通问候、身份询问等不再强制套用苏格拉底式引导。
  - 提示、继续引导、参考思路等交互样式统一。
- 修复学习画像风格被后端旧数据反复覆盖的问题，前端当前选择的学习风格优先展示。

### 4. 学习资源页优化

- 学习资源包增加前端缓存，避免切换页面后重复请求后端资源。
- 三种资源模式进一步明确：
  - 文字型：展示结构化讲义。
  - 视觉型：展示视频讲解；如果当前节点无视频资源，提示暂无相关视频。
  - 听觉型：基于讲义内容生成老师式讲解稿，再调用 TTS 合成语音。
- 听觉型讲解支持：
  - 进入听觉型页面后自动生成讲解稿和语音。
  - 生成完成后可播放 / 暂停。
  - 支持倍速。
  - 支持进度条拖动。
  - 音频 Blob 缓存，减少重复生成和切换页面后的播放失败。
- 优化讲义、导图、练习题、代码案例、报告、反馈等区域的浅色主题表现。

### 5. 数字人小蜂导学优化

- 课程广场加入数字人展示模块，作为平台视觉入口。
- 课程内加入数字人悬浮助手“小蜂导学”。
- 数字人支持男 / 女形象切换，并与对应音色绑定。
- 悬浮球支持拖动，展开面板跟随悬浮球定位。
- 展开面板本身不再触发拖动，用户可以复制窗口内文本。
- 重新打开数字人对话窗口时自动滚动到最新消息。
- 支持左侧 / 右侧贴边入口，避免遮挡主要学习内容。
- 重写数字人后端 `SYSTEM_PROMPT`：
  - 数字人定位为页面导学助手和学习陪伴助手。
  - 重点解释当前页面功能、按钮作用、学习建议和下一步操作。
  - 不再错误提及项目没有的“动觉型”学习模式。
  - 不伪造实时画像、资源和掌握度数据。
  - 深度 Python 学习问题建议引导到“学习对话”页面。

### 6. 讯飞 TTS 接入

- 增加 WebSocket 版讯飞 TTS 服务文件。
- 后端 TTS 状态接口可检查讯飞配置是否完整。
- 前端语音播放优先使用后端讯飞 TTS，失败时再降级到浏览器语音。
- 增加调试日志，便于判断当前数字人使用的是讯飞音色还是浏览器音色。

### 7. 课程广场与课程内容页优化

- 起始页作为课程广场，用户先登录 / 注册，再选择课程进入学习工作台。
- Python 课程作为当前已开放课程，其他课程保留入口但不展示假数据。
- 顶栏按钮、课程筛选、登录注册交互进行了可用性处理。
- 课程内容页保留知识图谱、学习资源、学习对话、代码沙箱、掌握进度等核心模块。
- 调整多处浅色主题残留问题，减少深色旧样式残留。

### 8. 知识图谱与掌握度相关优化

- 知识图谱保留后端节点数据驱动。
- 路径节点增加动态金色波纹效果。
- 节点详情气泡、概要信息、路径线、学习动作区域进行浅色主题适配。
- 掌握度页面文案由偏技术表达调整为更偏用户可理解表达。
- BKT、猜对概率、失误概率等概念做了前端说明优化。

## 三、运行方式

以下命令默认项目目录为：

```powershell
I:\project\rjb\RJBRJB
```

### 1. 后端运行

如果使用已有的 `RJB_demo` conda 环境：

```powershell
cd I:\project\rjb\RJBRJB\backend
I:\project\rjb\RJB_demo\.conda\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001 --reload
```

后端健康检查：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8001/api/health"
```

TTS 状态检查：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8001/api/tts/status"
```

### 2. 前端运行

首次拉取后需要安装依赖：

```powershell
cd I:\project\rjb\RJBRJB\frontend
npm install
```

启动前端：

```powershell
cd I:\project\rjb\RJBRJB\frontend
npm run dev -- --host 127.0.0.1 --port 5173
```

浏览器访问：

```text
http://127.0.0.1:5173/
```

### 3. 前端生产构建检查

```powershell
cd I:\project\rjb\RJBRJB\frontend
npm run build
```

## 四、需要填写的 API 字段

队友拉取代码后，需要在后端目录复制环境变量模板：

```powershell
cd I:\project\rjb\RJBRJB\backend
Copy-Item .env.example .env
```

然后填写 `backend/.env`。

### 1. DeepSeek 必填字段

```env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-pro
ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
```

说明：

- `DEEPSEEK_API_KEY` 必须换成自己的真实 Key。
- 当前项目统一使用 `deepseek-v4-pro`。
- 如果不想调用真实大模型，可临时设置 `LLM_PROVIDER=mock`，但演示效果会变成模拟数据。

### 2. 讯飞 TTS 必填字段

```env
SPARK_TTS_APP_ID=your_iflytek_tts_app_id
SPARK_TTS_API_KEY=your_iflytek_tts_api_key
SPARK_TTS_API_SECRET=your_iflytek_tts_api_secret
SPARK_TTS_API_URL=wss://tts-api.xfyun.cn/v2/tts
SPARK_TTS_API_PASSWORD=
```

说明：

- `SPARK_TTS_APP_ID`、`SPARK_TTS_API_KEY`、`SPARK_TTS_API_SECRET` 需要填写讯飞控制台的真实信息。
- `SPARK_TTS_API_URL` 需要和讯飞控制台开通的服务地址一致。
- 普通 TTS 一般使用 `wss://tts-api.xfyun.cn/v2/tts`。
- 如果使用讯飞私有 / 高级接口，可能需要填写 `SPARK_TTS_API_PASSWORD`。

### 3. 图谱后端字段

本地开发推荐：

```env
GRAPH_BACKEND=memory
```

如果队友要接 Neo4j：

```env
GRAPH_BACKEND=neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password
```

说明：

- `memory` 模式使用项目内置图谱，最容易跑通。
- `neo4j` 模式需要本地或远程 Neo4j 服务正常启动，并确保密码正确。

### 4. 数据库与应用字段

```env
DATABASE_URL=sqlite:///./eduhive.db
RESOURCE_CACHE_TTL_HOURS=168
SECRET_KEY=change_this_secret_key_before_production
DEBUG=true
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

说明：

- 本地开发默认 SQLite 即可。
- `SECRET_KEY` 本地可用默认值，正式部署必须更换。
- 如果前端端口不是 5173，需要同步修改 `CORS_ORIGINS`。

## 五、不会随 Git 同步的内容

以下内容不会提交到 GitHub：

- `backend/.env`：包含真实 API Key。
- `frontend/node_modules/`：前端依赖，需要队友本地 `npm install`。
- `.conda/`：本地 Python 环境，需要队友自己配置，或复用已有环境。
- `backend/eduhive.db`：本地运行数据库。
- `backend/tts-test*.mp3`、`backend/tts-check*.mp3`：本地 TTS 测试音频。

因此，队友拉取新分支后，代码会一致，但运行环境和密钥需要按本报告重新配置。

## 六、建议队友拉取方式

```powershell
git fetch origin
git checkout feature/full-project-sync-20260714
```

如本地没有依赖：

```powershell
cd frontend
npm install
```

然后根据上方命令分别启动后端和前端。

## 七、仍需关注的问题

- DeepSeek 真实生成会比 mock 慢，复杂资源生成仍可能受模型响应速度和超时设置影响。
- 讯飞 TTS 音色取决于控制台已开通音色，队友环境中未开通对应音色时可能需要更换 voice 参数。
- Neo4j 图谱模式需要后端同学保证图谱数据和 layout 字段稳定。
- 数字人目前主要是导学助手，不应完全替代学习对话页面的 Python 深度辅导。
