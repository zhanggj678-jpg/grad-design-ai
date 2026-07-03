"""
多智能体系统 - Multi-Agent Architecture
4个专业Agent协同工作，模拟真实毕业设计指导团队
"""
from enum import Enum
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
import uuid
import asyncio

class AgentRole(Enum):
    """Agent角色"""
    TOPIC_ANALYST = "topic_analyst"      # 选题分析师
    DATA_SCIENTIST = "data_scientist"    # 数据科学家
    DEFENSE_JUDGE = "defense_judge"       # 答辩评委
    RAG_ADVISOR = "rag_advisor"           # RAG学术顾问

class AgentMessage:
    """Agent消息 - 用于思考流展示"""
    def __init__(self, role: AgentRole, content: str, msg_type: str = "thinking"):
        self.role = role
        self.content = content
        self.msg_type = msg_type  # thinking/analysis/result/warning
        self.timestamp = datetime.now().isoformat()
        self.id = str(uuid.uuid4())[:8]

    def to_dict(self):
        return {
            "id": self.id,
            "role": self.role.value,
            "role_name": self.role.name,
            "content": self.content,
            "msg_type": self.msg_type,
            "timestamp": self.timestamp
        }

class BaseAgent:
    """Agent基类"""
    def __init__(self, role: AgentRole):
        self.role = role
        self.name = {
            AgentRole.TOPIC_ANALYST: "选题分析师",
            AgentRole.DATA_SCIENTIST: "数据科学家",
            AgentRole.DEFENSE_JUDGE: "答辩评委",
            AgentRole.RAG_ADVISOR: "RAG学术顾问"
        }[role]
        self.avatar = {
            AgentRole.TOPIC_ANALYST: "TA",
            AgentRole.DATA_SCIENTIST: "DS",
            AgentRole.DEFENSE_JUDGE: "DJ",
            AgentRole.RAG_ADVISOR: "RA"
        }[role]
        self.color = {
            AgentRole.TOPIC_ANALYST: "#6366f1",
            AgentRole.DATA_SCIENTIST: "#10b981",
            AgentRole.DEFENSE_JUDGE: "#f59e0b",
            AgentRole.RAG_ADVISOR: "#a855f7"
        }[role]

    async def think(self, context: Dict) -> List[AgentMessage]:
        """思考过程，返回消息列表"""
        raise NotImplementedError

    async def execute(self, context: Dict) -> Dict:
        """执行任务，返回结果"""
        raise NotImplementedError

class TopicAnalystAgent(BaseAgent):
    """选题分析师 - 负责选题生成和分析"""
    def __init__(self):
        super().__init__(AgentRole.TOPIC_ANALYST)

    async def think(self, context: Dict) -> List[AgentMessage]:
        messages = []
        major = context.get("major", "")
        direction = context.get("direction", "")

        messages.append(AgentMessage(
            self.role,
            f"正在分析「{major}」专业的「{direction}」方向...",
            "thinking"
        ))
        messages.append(AgentMessage(
            self.role,
            f"检索选题数据库，匹配{major}领域的热门研究方向...",
            "analysis"
        ))
        messages.append(AgentMessage(
            self.role,
            "参考往届优秀毕业设计和最新学术论文趋势...",
            "analysis"
        ))
        return messages

    async def execute(self, context: Dict) -> Dict:
        from core.llm import get_llm_client
        from core.rag_engine import get_rag_engine

        llm = get_llm_client()
        rag = get_rag_engine()

        major = context.get("major", "")
        direction = context.get("direction", "")
        count = context.get("count", 4)

        # 先用RAG检索相关选题作为参考
        rag_results = await rag.search(major, direction, top_k=3)

        # 构建增强的prompt
        reference = ""
        if rag_results:
            reference = "\n\n参考资料（来自学术数据库）：\n"
            for r in rag_results:
                reference += f"- {r.get('title', '')}: {r.get('summary', '')[:100]}\n"

        system_prompt = f"""你是一位资深的毕业设计指导老师，专注于{major}领域。
请根据学生的专业和研究方向，生成具体、有深度的毕业设计选题。
{reference}
要求：
1. 每个选题必须包含：title(标题)、desc(描述)、diff(难度1-5)、tags(技术标签)
2. 选题要贴合实际，有具体的技术栈
3. 难度合理：本科生以2-4为主
4. 返回JSON数组格式"""

        user_prompt = f"专业：{major}，研究方向：{direction}，请生成{count}个毕业设计选题。"

        response = await llm.chat(
            messages=[{"role": "user", "content": user_prompt}],
            system_prompt=system_prompt,
            temperature=0.8
        )

        import re
        try:
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                topics = json.loads(json_match.group())
            else:
                topics = json.loads(response)
        except Exception:
            topics = [{
                "title": f"基于{direction}的{major}领域研究",
                "desc": f"针对{major}领域的{direction}方向进行深度研究。",
                "diff": 3, "tags": [direction, major, "Python"]
            }]

        return {"topics": topics, "rag_references": rag_results}

class DataScientistAgent(BaseAgent):
    """数据科学家 - 负责数据分析和可视化"""
    def __init__(self):
        super().__init__(AgentRole.DATA_SCIENTIST)

    async def think(self, context: Dict) -> List[AgentMessage]:
        messages = []
        filename = context.get("filename", "data.csv")
        row_count = context.get("row_count", 0)

        messages.append(AgentMessage(
            self.role,
            f"开始分析数据文件「{filename}」...",
            "thinking"
        ))
        messages.append(AgentMessage(
            self.role,
            f"数据规模：{row_count}行，正在检查数据质量...",
            "analysis"
        ))
        messages.append(AgentMessage(
            self.role,
            "计算统计指标、相关性分析、分布特征...",
            "analysis"
        ))
        return messages

    async def execute(self, context: Dict) -> Dict:
        # 数据分析由analysis_service处理，这里返回思考流
        return context

class DefenseJudgeAgent(BaseAgent):
    """答辩评委 - 负责答辩问题生成和评分"""
    def __init__(self):
        super().__init__(AgentRole.DEFENSE_JUDGE)

    async def think(self, context: Dict) -> List[AgentMessage]:
        messages = []
        topic = context.get("topic", "")

        messages.append(AgentMessage(
            self.role,
            f"正在审阅选题「{topic[:30]}...」",
            "thinking"
        ))
        messages.append(AgentMessage(
            self.role,
            "从背景意义、技术方案、创新点、数据来源等维度设计问题...",
            "analysis"
        ))
        messages.append(AgentMessage(
            self.role,
            "问题设计完成，确保覆盖答辩核心考点。",
            "result"
        ))
        return messages

    async def execute(self, context: Dict) -> Dict:
        from core.llm import get_llm_client

        llm = get_llm_client()
        topic = context.get("topic", "")
        major = context.get("major", "")
        count = context.get("count", 6)

        if not llm.config.api_key:
            return {"questions": [
                "请简要介绍一下你的选题背景和研究意义？",
                "你的研究采用了哪些技术方法？",
                "你的创新点在哪里？",
                "数据来源是什么？如何保证数据的可靠性？",
                "研究过程中遇到的最大困难是什么？如何解决的？",
                "你的研究成果有什么实际应用价值？"
            ]}

        system_prompt = """你是一位严格的毕业设计答辩评委。请根据选题生成6个深度答辩问题。
涵盖：背景意义、技术方案、创新点、数据来源、困难解决、应用价值。
返回JSON数组格式。"""

        user_prompt = f"专业：{major}\n选题：{topic}\n请生成{count}个答辩问题。"

        response = await llm.chat(
            messages=[{"role": "user", "content": user_prompt}],
            system_prompt=system_prompt,
            temperature=0.8
        )

        import re
        try:
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            questions = json.loads(json_match.group()) if json_match else json.loads(response)
        except Exception:
            questions = ["请介绍选题背景？", "你用了什么技术方案？", "创新点是什么？",
                         "数据来源？", "最大困难？", "应用价值？"]

        return {"questions": questions[:count]}

class RAGAdvisorAgent(BaseAgent):
    """RAG学术顾问 - 提供学术参考和选题推荐"""
    def __init__(self):
        super().__init__(AgentRole.RAG_ADVISOR)

    async def think(self, context: Dict) -> List[AgentMessage]:
        messages = []
        query = context.get("query", "")

        messages.append(AgentMessage(
            self.role,
            f"正在检索学术数据库，查找「{query[:20]}...」相关文献...",
            "thinking"
        ))
        messages.append(AgentMessage(
            self.role,
            "匹配相关论文、技术方案、开源项目...",
            "analysis"
        ))
        return messages

    async def execute(self, context: Dict) -> Dict:
        from core.rag_engine import get_rag_engine

        rag = get_rag_engine()
        query = context.get("query", "")
        major = context.get("major", "")
        direction = context.get("direction", "")

        results = await rag.search(query or f"{major} {direction}", top_k=5)
        return {"references": results}

class MultiAgentOrchestrator:
    """多智能体协调器 - 统一调度所有Agent"""

    def __init__(self):
        self.agents = {
            AgentRole.TOPIC_ANALYST: TopicAnalystAgent(),
            AgentRole.DATA_SCIENTIST: DataScientistAgent(),
            AgentRole.DEFENSE_JUDGE: DefenseJudgeAgent(),
            AgentRole.RAG_ADVISOR: RAGAdvisorAgent(),
        }
        self._message_history: List[AgentMessage] = []

    def get_message_history(self) -> List[Dict]:
        return [m.to_dict() for m in self._message_history]

    def clear_history(self):
        self._message_history = []

    async def run_agent(self, role: AgentRole, context: Dict,
                        stream_thinking: bool = True) -> Dict:
        """
        运行指定Agent，返回结果和思考流

        Args:
            role: Agent角色
            context: 上下文数据
            stream_thinking: 是否输出思考过程

        Returns:
            {"result": ..., "thinking": [...], "agent": role.value}
        """
        agent = self.agents[role]
        thinking_messages = []

        if stream_thinking:
            think_msgs = await agent.think(context)
            for msg in think_msgs:
                self._message_history.append(msg)
                thinking_messages.append(msg.to_dict())

        result = await agent.execute(context)

        return {
            "result": result,
            "thinking": thinking_messages,
            "agent": role.value,
            "agent_name": agent.name,
            "agent_avatar": agent.avatar,
            "agent_color": agent.color
        }

    async def run_pipeline(self, roles: List[AgentRole], context: Dict) -> Dict:
        """运行多Agent流水线"""
        all_results = {}
        all_thinking = []

        for role in roles:
            result = await self.run_agent(role, context)
            all_results[role.value] = result["result"]
            all_thinking.extend(result["thinking"])
            # 后续Agent可以使用前面Agent的结果
            context.update(result["result"])

        return {
            "results": all_results,
            "thinking": all_thinking
        }

# 全局实例
_multi_agent: Optional[MultiAgentOrchestrator] = None

def get_multi_agent() -> MultiAgentOrchestrator:
    global _multi_agent
    if _multi_agent is None:
        _multi_agent = MultiAgentOrchestrator()
    return _multi_agent
