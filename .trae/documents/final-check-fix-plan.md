# AI毕业设计助手 — 终检修复计划

## 当前状态

终检发现 2 个致命 Bug + 2 个安全问题 + 4 个低优先级问题。

## 修复清单（按优先级排序）

### P0-1：recommend_next_step 返回字符串，端点必定 400 错误

**文件**：`backend/core/agent.py` 第 265 行 + `backend/api/workflow.py` 第 75 行

**问题**：`agent.py` 的 `recommend_next_step()` 返回字符串，但 `workflow.py` 用 `**result` 解包为字典，导致 TypeError。

**修复**：将 `agent.py` 的返回值改为字典格式，包含 `session_id, current_stage, next_stage, next_action, reason, progress` 六个字段，与 `RecommendResponse` 匹配。

### P0-2：后端 phases 格式与前端不匹配，研究方案显示 undefined

**文件**：`rag-grad-assistant-demo.html` 第 992 行

**问题**：后端 prompt 要求 LLM 返回 `{name, duration, tasks}`，但前端渲染时期望 `{title, desc}`。

**修复**：修改前端渲染逻辑，兼容两种格式：`p.title || p.name`，`p.desc || (p.tasks ? p.tasks.join('；') : '')`。

### P1-1：XSS 漏洞 — 聊天消息 innerHTML 渲染用户输入

**文件**：`rag-grad-assistant-demo.html` 的 `addUserMessage` 和 `addAIMessage` 函数

**修复**：添加 `escapeHtml()` 函数，在 innerHTML 中对用户输入转义。

### P1-2：CSV 上传无文件大小限制

**文件**：`backend/api/analysis.py` 第 58 行

**修复**：添加 10MB 文件大小上限检查。

### P2-1：topicPool 缺少韩语/法语预设选题

**文件**：`rag-grad-assistant-demo.html` 的 `topicPool.lang`

**修复**：为 `kr` 和 `fr` 各补充 2 个选题。

### P2-2：README.md 学院数量写成 12（实际 11）

**文件**：`README.md`

**修复**：将 "12个学院" 改为 "11个学院"，"349个预设选题" 改为 "100+个预设选题"。

## 验证步骤

1. 启动后端 → 调用 `/workflow/recommend/{session_id}` 确认返回 200
2. 启动后端 → 完成选题后进入研究方案页，确认 phases 正确显示
3. 在答辩聊天中输入 `<script>alert(1)</script>` 确认不被执行
4. 选择韩语专业 → 确认选题页有内容
5. `git push` 同步到 GitHub
