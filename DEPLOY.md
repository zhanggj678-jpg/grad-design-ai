# 部署指南 - AI毕业设计全流程助手

## 方案一：Render.com（推荐，免费）

### 1. 准备代码
确保代码已推送到 GitHub 仓库。

### 2. 注册 Render
访问 https://render.com 注册账号（可用 GitHub 账号登录）。

### 3. 创建 Web Service
1. 点击 **New** -> **Web Service**
2. 连接你的 GitHub 仓库
3. 配置如下：
   - **Name**: grad-design-assistant
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free

### 4. 设置环境变量
在 Render 控制台 -> Environment 中设置：
- `ZHIPU_API_KEY`: 你的智谱AI API Key（从 https://open.bigmodel.cn/ 获取）
- `JWT_SECRET`: 随机字符串（用于JWT签名，已自动生成）
- `ENV`: production

### 5. 部署
点击 **Create Web Service**，等待部署完成。

部署成功后，你会获得一个类似 `https://grad-design-assistant.onrender.com` 的地址。

---

## 方案二：Vercel（前端）+ Render（后端）

### 前端部署到 Vercel
1. 将 `rag-grad-assistant-demo.html` 重命名为 `index.html`
2. 推送到 GitHub
3. 在 Vercel 导入项目并部署
4. 免费获得 HTTPS 域名

### 后端部署到 Render
按方案一部署后端，然后将前端 API_BASE 改为后端地址。

---

## 方案三：本地运行（开发测试）

### 启动后端
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

### 打开前端
直接用浏览器打开 `rag-grad-assistant-demo.html`

---

## 环境变量说明

| 变量名 | 说明 | 必填 |
|--------|------|------|
| `ZHIPU_API_KEY` | 智谱AI API Key | 是（启用真实AI） |
| `JWT_SECRET` | JWT签名密钥 | 是（生产环境） |
| `ENV` | 运行环境 | 否（默认development） |
| `CORS_ORIGINS` | 允许的跨域域名 | 否（默认*） |
| `LLM_PROVIDER` | LLM提供商：zhipu/openai | 否（默认zhipu） |
| `LLM_MODEL` | 模型名称 | 否（默认glm-4-flash） |
| `LLM_BASE_URL` | LLM API基础URL | 否（默认智谱AI地址） |

---

## 获取智谱AI API Key

1. 访问 https://open.bigmodel.cn/
2. 注册/登录账号
3. 进入「API Keys」页面
4. 创建新的 API Key
5. 复制 Key 到环境变量中

---

## 部署后验证

访问以下地址验证：
- 根路径：`https://你的域名/`
- API文档：`https://你的域名/docs`
- 健康检查：`https://你的域名/health`
