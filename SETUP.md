# 智学蜂巢 EduHive 环境搭建指南

## 前提条件

| 工具 | 最低版本 | 检查命令 |
|------|---------|---------|
| Node.js | 18.0+ | `node --version` |
| Python | 3.11+ | `python --version` |
| Git | 任意 | `git --version` |

## 1. 克隆项目

```bash
git clone git@github.com:Jesse7250/RJBRJB.git
cd RJBRJB
```

## 2. 后端配置

```bash
cd backend

# 复制环境配置（重要！）
cp .env.example .env

# 安装 Python 依赖
pip install -r requirements.txt

# 启动后端（端口 8001）
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

## 3. 前端配置

打开新终端：

```bash
cd frontend

# 安装依赖（首次必须执行）
npm install

# 启动前端（端口 5173）
npm run dev
```

## 4. 打开浏览器

访问 `http://localhost:5173`

## 常见问题

### Q: 前端启动报 `crypto.getRandomValues is not a function`
**A:** Node.js 版本太低，需要 18+。升级 Node.js 或使用 nvm 切换版本。

### Q: 后端启动报 `ModuleNotFoundError`
**A:** 没装 Python 依赖，执行 `pip install -r requirements.txt`

### Q: 页面显示「后端已断开」
**A:** 确认后端在 8001 端口运行，Vite 代理配置指向 8001

### Q: 后端报端口占用
**A:** 换端口：`--port 8002`，同时改 `frontend/vite.config.ts` 中的 proxy target

### Q: 需要 API Key 吗？
**A:** 不需要。LLM 使用 Mock 模式，TTS 自动回退浏览器语音，开箱即用。
