# 【学习工作赛道】AI毕业设计全流程助手 — 从选题到答辩，AI陪你走完全程

## 简介

**AI毕业设计全流程助手** 是一款专为大学生打造的智能毕业设计辅助工具。

每年毕业季，无数学生面临同样的困境：选题迷茫、缺乏思路、数据分析无从下手、答辩紧张到语无伦次。我作为数据科学与大数据技术专业的学生，对此深有体会。

这个项目用AI技术解决这些真实痛点，覆盖毕业设计全流程：智能选题推荐 → 研究思路生成 → CSV数据分析 → 模拟答辩评分。让每位学生都能获得个性化的AI指导，告别毕业设计焦虑。

**目标用户**：面临毕业设计的大三/大四学生
**核心痛点**：选题迷茫、缺乏思路、数据分析困难、答辩紧张

---

## 创作思路

### 为什么做这个项目？

我身边的同学（包括我自己）在毕业设计阶段都经历过这些痛苦：
1. **选题阶段**：导师给的题目要么太难做不出来，要么太简单没技术含量，自己想的题目又担心工作量不够
2. **开题阶段**：确定了题目却不知道从何入手，文献看了很多但思路还是乱的
3. **数据阶段**：好不容易收集到数据，面对Excel表格却不知道如何分析和可视化
4. **答辩阶段**：准备了很久，但评委一问就紧张，回答不到点上

现有的工具大多是单一功能的（比如只有选题推荐或只有答辩题库），没有一个工具能覆盖全流程。而且很多工具的AI只是简单的模板匹配，没有真正的智能。

### 技术方案

**前端**：纯HTML+CSS+JS单文件，零构建工具，部署简单
- AI生命感UI设计：顶部AI状态栏实时显示思考状态，右侧AI思考流展示系统工作过程
- ECharts数据可视化：自动生成直方图、饼图、散点图
- PapaParse CSV解析：前端快速预览数据

**后端**：FastAPI + SQLite + Pandas + 智谱AI GLM-4
- 分层架构：api/service/core/database四层结构
- WorkflowAgent：智能流程控制，自动推荐下一步操作
- LLM统一入口：支持智谱AI/OpenAI多模型切换
- JWT认证 + SQLite持久化

### 创新点

1. **五步闭环设计**：选题→研究→数据→答辩→报告，全流程覆盖
2. **AI生命感UI**：让用户感受到AI在思考、在分析、在帮助自己
3. **真实数据分析**：使用Pandas+NumPy进行真实计算，不是前端模拟
4. **智能流程控制**：WorkflowAgent根据用户当前进度推荐下一步
5. **349个预设选题**：覆盖12个学院100+专业，LLM在此基础上生成个性化选题

---

## 体验地址

**本地体验**：
1. 克隆仓库
2. `cd backend && pip install -r requirements.txt`
3. 复制 `.env.example` 为 `.env`，填入智谱AI API Key
4. `python -m uvicorn main:app --reload --port 8001`
5. 浏览器打开 `rag-grad-assistant-demo.html`

**在线体验**：[https://grad-design-ai.onrender.com/app](https://grad-design-ai.onrender.com/app)

---

## TRAE实践

### 如何用TRAE构建这个项目

**第一阶段：前端原型（2小时）**
- 用TRAE的AI对话功能快速生成HTML框架
- 通过自然语言描述UI需求："我要一个AI生命感的界面，有状态栏、思考流、卡片化布局"
- TRAE自动生成CSS动画和交互逻辑

**第二阶段：后端架构（3小时）**
- 用TRAE的代码补全功能快速搭建FastAPI项目结构
- 通过对话确定分层架构："我要api/service/core/database四层结构"
- TRAE自动生成CRUD代码和路由模板

**第三阶段：AI接入（1小时）**
- 用TRAE的调试功能解决API调用问题
- 通过对话优化Prompt："帮我写一个生成毕业设计选题的system prompt"
- TRAE自动优化JSON解析和错误处理

**第四阶段：测试优化（2小时）**
- 用TRAE的代码检查功能发现安全漏洞（CORS、JWT等）
- 通过对话修复问题："我的JWT_SECRET每次重启会变，怎么解决？"
- TRAE提供多种解决方案并解释优缺点

### TRAE带来的效率提升

- **代码生成**：TRAE生成的代码占项目总代码量的60%以上
- **调试加速**：遇到问题时，TRAE能快速定位并给出修复方案
- **架构设计**：通过对话就能确定技术选型和架构方案
- **文档生成**：TRAE能自动生成README和部署文档

---

## 截图展示

![AI欢迎页](screenshots/01-welcome.png)
*AI欢迎页与专业选择*

![智能选题](screenshots/02-topics.png)
*智能选题推荐*

![研究思路](screenshots/03-research.png)
*研究思路生成*

![数据分析](screenshots/04-analysis.png)
*CSV数据分析与可视化*

![模拟答辩](screenshots/05-defense.png)
*模拟答辩与评分*

---

## 项目亮点

1. **AI生命感UI**：顶部AI状态栏实时显示思考状态，右侧AI思考流展示系统工作过程，欢迎页有登场动画
2. **真实数据分析**：使用Pandas+NumPy进行真实计算，不是前端模拟
3. **分层架构**：api/service/core/database四层结构，代码清晰可维护
4. **WorkflowAgent**：智能流程控制，自动推荐下一步操作
5. **LLM统一入口**：支持智谱AI/OpenAI多模型切换

---

## 技术栈

- 前端：HTML + CSS + JS + ECharts + PapaParse
- 后端：FastAPI + SQLite + Pandas + NumPy
- AI：智谱AI GLM-4（统一LLM入口，支持多模型切换）
- 部署：Render.com 免费实例

---

## 开源地址

GitHub：[zhanggj678-jpg/grad-design-ai](https://github.com/zhanggj678-jpg/grad-design-ai)

---

> 本项目参加 TRAE AI创造力大赛 · 学习工作赛道
> 如果你也是面临毕业设计的学生，欢迎试用并给出反馈！
