"""
选题服务 - 选题生成、管理、研究思路
"""
from typing import List, Dict, Optional

from core.llm import get_llm_client
from core.agent import get_agent
from database.crud import (
    SessionCRUD, TopicCRUD, LogCRUD,
    create_user_session
)


class TopicService:
    """选题服务"""

    @staticmethod
    async def generate_topics(session_id: str, dept: str, major: str,
                              direction: str, count: int = 4) -> Dict:
        """
        生成毕业设计选题

        流程：
        1. 更新会话专业信息
        2. 调用LLM生成选题
        3. 保存选题到数据库
        4. 返回结果
        """
        # 更新会话
        agent = get_agent()
        agent.select_major(session_id, dept, major, direction)
        SessionCRUD.update_major(session_id, dept, major, direction)

        # 调用LLM生成选题（优先使用 Multi-Agent）
        llm = get_llm_client()
        topics = []
        agent_messages = []

        if llm.config.api_key:
            try:
                from core.multi_agent import MultiAgentOrchestrator, TopicAnalystAgent
                orchestrator = MultiAgentOrchestrator()
                context = {
                    "major": major,
                    "direction": direction,
                    "count": count
                }
                result = await orchestrator.run_pipeline([TopicAnalystAgent()], context)
                if result:
                    exec_result = result.get("results", {}).get("topic_analyst", {})
                    if exec_result.get("topics"):
                        topics = exec_result["topics"]
                    thinking = result.get("thinking", [])
                    agent_messages = [{"role": m.role.value, "content": m.content, "type": m.message_type} for m in thinking]
            except Exception:
                # Multi-Agent 失败，降级为直接 LLM 调用
                topics = await llm.generate_topics(major, direction, count)
        else:
            topics = await llm.generate_topics(major, direction, count)

        # 保存到数据库
        saved_topics = []
        for topic in topics:
            topic_id = TopicCRUD.create(
                session_id=session_id,
                title=topic.get("title", ""),
                description=topic.get("desc", ""),
                difficulty=topic.get("diff", 3),
                tags=topic.get("tags", [])
            )
            saved_topics.append({
                "id": topic_id,
                **topic
            })

        LogCRUD.create(session_id, None, "topics_generated",
                       f"生成了{len(topics)}个选题: {major}/{direction}")

        return {
            "success": True,
            "session_id": session_id,
            "major": major,
            "direction": direction,
            "topics": saved_topics,
            "agent_messages": agent_messages
        }

    @staticmethod
    def select_topic(session_id: str, topic_id: int) -> Dict:
        """选择选题"""
        # 获取选题信息
        topics = TopicCRUD.get_by_session(session_id)
        selected = None
        for t in topics:
            if t["id"] == topic_id:
                selected = t
                break

        if not selected:
            return {"success": False, "error": "选题不存在"}

        # 更新Agent状态
        agent = get_agent()
        topic_data = {
            "id": selected["id"],
            "title": selected["title"],
            "description": selected["description"],
            "difficulty": selected["difficulty"],
            "tags": selected["tags"]
        }
        agent.select_topic(session_id, topic_data)

        # 更新数据库
        TopicCRUD.mark_selected(topic_id)
        SessionCRUD.update_topic(session_id, topic_data)

        LogCRUD.create(session_id, None, "topic_selected",
                       f"选择了选题: {selected['title']}")

        return {
            "success": True,
            "session_id": session_id,
            "selected_topic": topic_data
        }

    @staticmethod
    async def generate_research_plan(session_id: str) -> Dict:
        """
        生成研究思路/计划

        基于已选选题，调用LLM生成详细的研究方案
        """
        agent = get_agent()
        session = agent.get_session(session_id)

        if not session or not session.selected_topic:
            return {"success": False, "error": "请先选择选题"}

        topic = session.selected_topic
        major = session.major
        direction = session.direction

        # 构建提示词
        system_prompt = """你是一位资深的毕业设计指导老师。请根据学生的选题，生成详细、可执行的研究方案。

要求：
1. 包含研究背景、研究目标、技术路线
2. 分阶段列出具体任务和时间安排
3. 列出需要掌握的技术栈和学习资源
4. 给出可能遇到的难点和解决方案
5. 返回JSON格式

返回格式：
{
  "background": "研究背景",
  "objectives": ["目标1", "目标2"],
  "tech_stack": ["技术1", "技术2"],
  "phases": [
    {"name": "阶段1", "duration": "2周", "tasks": ["任务1", "任务2"]}
  ],
  "difficulties": [{"problem": "难点", "solution": "解决方案"}],
  "resources": ["资源1", "资源2"]
}"""

        user_prompt = f"""专业：{major}
研究方向：{direction}
选题：{topic.get('title', '')}
选题描述：{topic.get('description', '')}

请生成详细的研究方案。"""

        llm = get_llm_client()
        response = await llm.chat(
            messages=[{"role": "user", "content": user_prompt}],
            system_prompt=system_prompt,
            temperature=0.7
        )

        # 解析JSON
        import json
        import re
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                plan = json.loads(json_match.group())
            else:
                plan = json.loads(response)
        except Exception:
            # 解析失败返回默认结构
            plan = {
                "background": f"针对{major}领域的{direction}方向进行深入研究",
                "objectives": ["完成毕业设计", "掌握相关技术"],
                "tech_stack": ["Python", "数据分析"],
                "phases": [
                    {"name": "文献调研", "duration": "1周", "tasks": ["查阅相关文献"]},
                    {"name": "需求分析", "duration": "1周", "tasks": ["明确研究目标"]},
                    {"name": "系统设计", "duration": "2周", "tasks": ["设计系统架构"]},
                    {"name": "编码实现", "duration": "4周", "tasks": ["完成核心功能"]},
                    {"name": "测试优化", "duration": "2周", "tasks": ["测试并优化"]},
                    {"name": "论文撰写", "duration": "2周", "tasks": ["撰写毕业论文"]}
                ],
                "difficulties": [],
                "resources": []
            }

        # 更新状态
        agent.set_research_plan(session_id, plan)
        SessionCRUD.update_research_plan(session_id, plan)

        LogCRUD.create(session_id, None, "research_plan_generated",
                       f"生成了研究方案: {topic.get('title', '')}")

        return {
            "success": True,
            "session_id": session_id,
            "plan": plan
        }

    @staticmethod
    def get_session_topics(session_id: str) -> List[Dict]:
        """获取会话的所有选题"""
        return TopicCRUD.get_by_session(session_id)
