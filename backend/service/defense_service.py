"""
答辩服务 - 模拟答辩、评分、问题生成
"""
from typing import Dict, List, Optional

from core.llm import get_llm_client
from core.agent import get_agent
from database.crud import (
    SessionCRUD, DefenseCRUD, LogCRUD
)


class DefenseService:
    """答辩服务"""

    # 预设问题模板（当LLM不可用时使用）
    DEFAULT_QUESTIONS = [
        "请简要介绍一下你的选题背景和研究意义？",
        "你的研究采用了哪些技术方法？",
        "你的创新点在哪里？",
        "数据来源是什么？如何保证数据的可靠性？",
        "研究过程中遇到的最大困难是什么？如何解决的？",
        "你的研究成果有什么实际应用价值？",
        "如果继续深入研究，你会从哪些方面展开？",
        "你的实验结果是否达到了预期目标？",
        "请解释一下核心算法/模型的原理？",
        "你的研究与现有工作相比有什么优势？"
    ]

    @staticmethod
    async def generate_questions(session_id: str, count: int = 6) -> Dict:
        """
        生成答辩问题

        基于选题和研究计划，调用LLM生成个性化问题
        """
        agent = get_agent()
        session = agent.get_session(session_id)

        if not session or not session.selected_topic:
            return {"success": False, "error": "请先选择选题"}

        topic = session.selected_topic
        major = session.major

        # 尝试用 Multi-Agent（DefenseJudgeAgent）生成个性化问题
        llm = get_llm_client()
        questions = []
        agent_messages = []

        if llm.config.api_key:
            try:
                # 尝试 Multi-Agent 流程
                from core.multi_agent import MultiAgentOrchestrator, DefenseJudgeAgent
                orchestrator = MultiAgentOrchestrator()
                topic_title = topic.get('title', '') if isinstance(topic, dict) else str(topic)
                topic_desc = topic.get('description', '') if isinstance(topic, dict) else ''
                context = {
                    "topic": topic_title,
                    "description": topic_desc,
                    "major": major,
                    "count": count
                }
                result = await orchestrator.run_pipeline([DefenseJudgeAgent()], context)
                if result:
                    exec_result = result.get("results", {}).get("defense_judge", {})
                    if exec_result.get("questions"):
                        questions = exec_result["questions"]
                    # 提取 Agent 思考流消息
                    thinking = result.get("thinking", [])
                    agent_messages = [{"role": m.role.value, "content": m.content, "type": m.message_type} for m in thinking]
            except Exception:
                # Multi-Agent 失败，降级为直接 LLM 调用
                try:
                    system_prompt = """你是一位毕业设计答辩评委。请根据学生的选题，生成具体、有深度的答辩问题。

要求：
1. 问题要针对选题的具体内容
2. 涵盖：背景意义、技术方案、创新点、数据来源、困难解决、应用价值
3. 每个问题要简洁明确
4. 返回JSON数组格式

示例：["请介绍一下选题的背景？", "你采用了什么技术方案？"]"""

                    user_prompt = f"""专业：{major}
选题：{topic.get('title', '')}
描述：{topic.get('description', '')}

请生成{count}个答辩问题。"""

                    response = await llm.chat(
                        messages=[{"role": "user", "content": user_prompt}],
                        system_prompt=system_prompt,
                        temperature=0.8
                    )

                    import json
                    import re
                    try:
                        json_match = re.search(r'\[.*\]', response, re.DOTALL)
                        if json_match:
                            questions = json.loads(json_match.group())
                        else:
                            questions = json.loads(response)
                    except Exception:
                        questions = []
                except Exception:
                    questions = []

        # 如果LLM没有返回问题，使用默认问题
        if not questions or not isinstance(questions, list):
            questions = DefenseService.DEFAULT_QUESTIONS[:count]

        # 确保问题数量
        questions = questions[:count]
        while len(questions) < count:
            questions.append(DefenseService.DEFAULT_QUESTIONS[len(questions) % len(DefenseService.DEFAULT_QUESTIONS)])

        LogCRUD.create(session_id, None, "questions_generated",
                       f"生成了{len(questions)}个答辩问题")

        return {
            "success": True,
            "session_id": session_id,
            "questions": questions,
            "agent_messages": agent_messages
        }

    @staticmethod
    async def evaluate_answer(session_id: str, question: str,
                              answer: str, question_index: int = 0) -> Dict:
        """
        评估答辩回答

        调用LLM对回答进行评分和反馈
        """
        agent = get_agent()
        session = agent.get_session(session_id)

        if not session:
            return {"success": False, "error": "会话不存在"}

        topic_title = session.selected_topic.get("title", "") if session.selected_topic else ""

        # 调用LLM评估
        llm = get_llm_client()
        evaluation = None

        if llm.config.api_key:
            try:
                evaluation = await llm.evaluate_defense(question, answer, topic_title)
            except Exception:
                evaluation = None

        # 如果LLM失败，使用基础评分
        if not evaluation:
            evaluation = DefenseService._basic_evaluation(question, answer)

        # 保存记录
        score = evaluation.get("score", {})
        DefenseCRUD.create(
            session_id=session_id,
            question=question,
            answer=answer,
            score=score,
            feedback=evaluation.get("feedback", ""),
            level=evaluation.get("level", "一般")
        )

        # 更新Agent状态
        agent.add_defense_record(session_id, question, answer, score)

        # 更新数据库中的总分
        defense_records = DefenseCRUD.get_by_session(session_id)
        total_score = {"innovation": 0, "technique": 0, "logic": 0, "presentation": 0}
        for record in defense_records:
            record_score = record.get("score", {})
            for key in total_score:
                total_score[key] += record_score.get(key, 0)

        SessionCRUD.update_defense_score(session_id, total_score)

        LogCRUD.create(session_id, None, "answer_evaluated",
                       f"评估了第{question_index + 1}题回答")

        return {
            "success": True,
            "session_id": session_id,
            "question_index": question_index,
            "evaluation": evaluation
        }

    @staticmethod
    def _basic_evaluation(question: str, answer: str) -> Dict:
        """基础评估（LLM不可用时的降级方案）"""
        answer_length = len(answer)

        # 根据回答长度和关键词简单评分
        score = {
            "innovation": 15,
            "technique": 15,
            "logic": 15,
            "presentation": 15
        }

        # 长度加分
        if answer_length > 100:
            score["presentation"] += 3
        if answer_length > 200:
            score["logic"] += 3

        # 关键词检测
        tech_keywords = ["算法", "模型", "数据", "分析", "系统", "设计", "实现",
                        "优化", "框架", "库", "API", "数据库", "前端", "后端"]
        for kw in tech_keywords:
            if kw in answer:
                score["technique"] += 1

        innovation_keywords = ["创新", "改进", "优化", "新", "独特", "差异", "优势"]
        for kw in innovation_keywords:
            if kw in answer:
                score["innovation"] += 1

        # 封顶
        for key in score:
            score[key] = min(score[key], 30)

        total = sum(score.values())

        if total >= 90:
            level = "优秀"
        elif total >= 75:
            level = "良好"
        elif total >= 60:
            level = "一般"
        else:
            level = "需改进"

        return {
            "score": score,
            "feedback": f"回答长度{answer_length}字，总体表现{level}。",
            "level": level,
            "highlights": ["回答完整" if answer_length > 50 else "回答简洁"],
            "suggestions": ["建议增加更多技术细节" if score["technique"] < 20 else "技术描述较好"]
        }

    @staticmethod
    def get_defense_history(session_id: str) -> List[Dict]:
        """获取答辩历史"""
        return DefenseCRUD.get_by_session(session_id)

    @staticmethod
    def get_defense_stats(session_id: str) -> Dict:
        """获取答辩统计"""
        return DefenseCRUD.get_stats(session_id)

    @staticmethod
    async def generate_report(session_id: str) -> Dict:
        """
        生成答辩综合报告
        """
        stats = DefenseCRUD.get_stats(session_id)
        records = DefenseCRUD.get_by_session(session_id)

        if not records:
            return {"success": False, "error": "暂无答辩记录"}

        total_score = sum([
            stats.get("avg_innovation", 0),
            stats.get("avg_technique", 0),
            stats.get("avg_logic", 0),
            stats.get("avg_presentation", 0)
        ])

        if total_score >= 90:
            overall_level = "优秀"
            advice = "表现非常出色，继续保持！"
        elif total_score >= 75:
            overall_level = "良好"
            advice = "整体表现不错，可以在技术深度上进一步加强。"
        elif total_score >= 60:
            overall_level = "一般"
            advice = "基本达标，建议多练习答辩表达，增加技术细节。"
        else:
            overall_level = "需改进"
            advice = "需要认真准备，建议重新梳理论文内容和技术要点。"

        return {
            "success": True,
            "session_id": session_id,
            "overall_score": round(total_score, 1),
            "overall_level": overall_level,
            "stats": stats,
            "record_count": len(records),
            "advice": advice,
            "records": records
        }
