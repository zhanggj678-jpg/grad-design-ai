# AI毕业设计全流程助手

> 【学习工作赛道】AI驱动的毕业设计选题、研究、分析、答辩一体化平台

## 项目简介

**AI毕业设计全流程助手** 是一款专为大学生打造的智能毕业设计辅助工具。从专业选择到模拟答辩，覆盖毕业设计全流程，让每位学生都能获得个性化的AI指导。

**目标用户**：面临毕业设计的大三/大四学生，尤其是计算机、数据科学、人工智能等相关专业

**核心痛点**：
- 选题迷茫：不知道选什么题目，担心题目太难或太简单
- 缺乏思路：确定了题目却不知道从何入手
- 数据分析：面对大量数据不知如何处理和可视化
- 答辩紧张：不知道评委会问什么问题，如何回答

## 核心功能

### 1. 智能选题推荐
- 覆盖 **11个学院、37个专业、100+个预设选题**
- 根据专业和研究方向，AI生成个性化选题
- 每个选题包含难度评级、技术标签、详细描述

### 2. 研究思路生成
- 基于选题自动生成完整研究方案
- 包含研究背景、目标、技术路线、时间安排
- 列出需要掌握的技术栈和学习资源

### 3. CSV数据分析
- 支持上传CSV文件，自动进行数据清洗和分析
- 生成统计摘要、相关性分析、分布洞察
- 自动生成 ECharts 可视化图表（直方图、饼图、散点图）

### 4. 模拟答辩
- AI生成针对性答辩问题
- 四维度评分（创新性/技术深度/逻辑表达/展示能力）
- 关键词检测 + 详细反馈 + 改进建议
- 导出答辩综合报告

### 5. 用户系统
- 注册/登录功能
- JWT认证，安全持久化
- 保存选题历史、答辩记录

## 技术架构

```
前端：纯 HTML + CSS + JS（单文件，零构建）
      ├─ ECharts 数据可视化
      ├─ PapaParse CSV解析
      └─ AI生命感UI（状态栏/思考流/动画）

后端：FastAPI + SQLite + Pandas + 智谱AI GLM-4
      ├─ api/      路由层（5个模块）
      ├─ service/  业务层（auth/topic/analysis/defense）
      ├─ core/     核心层（LLM统一入口 + Agent流程控制）
      └─ database/ 数据层（db.py + crud.py）
```

## 安装步骤

### 本地开发

1. **克隆项目**
```bash
git clone <仓库地址>
cd demo/backend
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，填入你的智谱AI API Key
```

4. **启动后端**
```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

5. **打开前端**
直接用浏览器打开 `rag-grad-assistant-demo.html`

### 生产部署

详见 [DEPLOY.md](DEPLOY.md)

## 环境变量

| 变量名 | 说明 | 必填 |
|--------|------|------|
| `ZHIPU_API_KEY` | 智谱AI API Key | 是 |
| `JWT_SECRET` | JWT签名密钥 | 是 |
| `CORS_ORIGINS` | 允许的跨域域名 | 否（默认*） |
| `LLM_PROVIDER` | LLM提供商 | 否（默认zhipu） |
| `LLM_MODEL` | 模型名称 | 否（默认glm-4-flash） |

## 截图展示

### 1. AI欢迎页与专业选择
![欢迎页](screenshots/01-welcome.png)

### 2. 智能选题推荐
![选题推荐](screenshots/02-topics.png)

### 3. 研究思路生成
![研究思路](screenshots/03-research.png)

### 4. CSV数据分析与可视化
![数据分析](screenshots/04-analysis.png)

### 5. 模拟答辩与评分
![模拟答辩](screenshots/05-defense.png)

## 项目亮点

1. **AI生命感UI**：顶部AI状态栏实时显示思考状态，右侧AI思考流展示系统工作过程，欢迎页有登场动画
2. **真实数据分析**：使用Pandas+NumPy进行真实计算，不是前端模拟
3. **分层架构**：api/service/core/database四层结构，代码清晰可维护
4. **WorkflowAgent**：智能流程控制，自动推荐下一步操作
5. **LLM统一入口**：支持智谱AI/OpenAI多模型切换

## 开源协议

MIT License

## 联系方式

如有问题或建议，欢迎提交 Issue 或联系作者。

---

> 本项目参加 [TRAE AI创造力大赛](https://trae.ai) · 学习工作赛道

欢迎 Star 和 Fork
