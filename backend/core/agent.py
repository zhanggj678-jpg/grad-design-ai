"""
智能流程控制 - 毕业设计工作流管理
管理用户会话状态，协调各步骤数据流转
"""
import json
import uuid
from typing import Dict, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime

from database.crud import SessionCRUD, TopicCRUD


@dataclass
class SessionState:
    """会话状态"""
    session_id: str
    user_id: Optional[int] = None
    current_stage: str = "init"  # init -> topic -> research -> data -> defense -> report
    dept: str = ""
    major: str = ""
    direction: str = ""
    selected_topic: Optional[Dict] = None
    research_plan: Optional[Dict] = None
    csv_data: Optional[Dict] = None
    analysis_result: Optional[Dict] = None
    defense_records: List[Dict] = field(default_factory=list)
    defense_score: Optional[Dict] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "current_stage": self.current_stage,
            "dept": self.dept,
            "major": self.major,
            "direction": self.direction,
            "selected_topic": self.selected_topic,
            "research_plan": self.research_plan,
            "csv_data": self.csv_data,
            "analysis_result": self.analysis_result,
            "defense_records": self.defense_records,
            "defense_score": self.defense_score,
            "created_at": self.created_at
        }


class WorkflowAgent:
    """工作流Agent - 管理毕业设计全流程"""

    def __init__(self):
        self._sessions: Dict[str, SessionState] = {}
        self._load_sessions_from_db()

    def _load_sessions_from_db(self):
        """从数据库加载活跃会话"""
        try:
            # 加载最近24小时的会话
            from database.db import get_db_connection
            with get_db_connection() as conn:
                cursor = conn.execute(
                    """SELECT * FROM sessions 
                       WHERE updated_at > datetime('now', '-1 day')
                       ORDER BY updated_at DESC LIMIT 100"""
                )
                rows = cursor.fetchall()
                for row in rows:
                    session = self._row_to_session(row)
                    self._sessions[session.session_id] = session
        except Exception as e:
            print(f"[Agent] 加载会话失败: {e}")

    def _row_to_session(self, row) -> SessionState:
        """数据库行转SessionState"""
        def parse_json(val):
            if not val:
                return None
            try:
                return json.loads(val)
            except Exception:
                return None

        return SessionState(
            session_id=row["session_id"],
            user_id=row.get("user_id"),
            current_stage=row.get("current_stage", "init"),
            dept=row.get("dept", ""),
            major=row.get("major", ""),
            direction=row.get("direction", ""),
            selected_topic=parse_json(row.get("selected_topic")),
            research_plan=parse_json(row.get("research_plan")),
            csv_data=parse_json(row.get("csv_data")),
            analysis_result=parse_json(row.get("analysis_result")),
            defense_score=parse_json(row.get("defense_score")),
            created_at=row.get("created_at", datetime.now().isoformat())
        )

    def _save_session_to_db(self, session: SessionState):
        """保存会话到数据库"""
        try:
            SessionCRUD.update_fields(
                session_id=session.session_id,
                current_stage=session.current_stage,
                dept=session.dept,
                major=session.major,
                direction=session.direction,
                selected_topic=json.dumps(session.selected_topic, ensure_ascii=False) if session.selected_topic else "",
                research_plan=json.dumps(session.research_plan, ensure_ascii=False) if session.research_plan else "",
                csv_data=json.dumps(session.csv_data, ensure_ascii=False) if session.csv_data else "",
                analysis_result=json.dumps(session.analysis_result, ensure_ascii=False) if session.analysis_result else "",
                defense_score=json.dumps(session.defense_score, ensure_ascii=False) if session.defense_score else ""
            )
        except Exception as e:
            print(f"[Agent] 保存会话失败: {e}")

    def create_session(self, user_id: Optional[int] = None) -> str:
        """创建新会话"""
        session_id = str(uuid.uuid4())
        session = SessionState(session_id=session_id, user_id=user_id)
        self._sessions[session_id] = session

        # 同时保存到数据库
        try:
            SessionCRUD.create(session_id=session_id, user_id=user_id)
        except Exception as e:
            print(f"[Agent] 创建数据库会话失败: {e}")

        return session_id

    def get_session(self, session_id: str) -> Optional[SessionState]:
        """获取会话（优先内存，其次数据库）"""
        if session_id in self._sessions:
            return self._sessions[session_id]

        # 尝试从数据库加载
        try:
            db_session = SessionCRUD.get_by_session_id(session_id)
            if db_session:
                session = self._db_to_session(db_session)
                self._sessions[session_id] = session
                return session
        except Exception as e:
            print(f"[Agent] 从数据库加载会话失败: {e}")

        return None

    def _db_to_session(self, db_data: Dict) -> SessionState:
        """数据库数据转SessionState"""
        def parse_json(val):
            if not val:
                return None
            try:
                return json.loads(val) if isinstance(val, str) else val
            except Exception:
                return None

        return SessionState(
            session_id=db_data.get("session_id", ""),
            user_id=db_data.get("user_id"),
            current_stage=db_data.get("current_stage", "init"),
            dept=db_data.get("dept", ""),
            major=db_data.get("major", ""),
            direction=db_data.get("direction", ""),
            selected_topic=parse_json(db_data.get("selected_topic")),
            research_plan=parse_json(db_data.get("research_plan")),
            csv_data=parse_json(db_data.get("csv_data")),
            analysis_result=parse_json(db_data.get("analysis_result")),
            defense_score=parse_json(db_data.get("defense_score")),
            created_at=db_data.get("created_at", datetime.now().isoformat())
        )

    def select_major(self, session_id: str, dept: str, major: str,
                     direction: str) -> bool:
        """选择专业信息（兼容旧接口）"""
        return self.update_basic_info(session_id, dept, major, direction)

    def update_basic_info(self, session_id: str, dept: str, major: str,
                         direction: str) -> bool:
        """更新基本信息"""
        session = self._get_or_create(session_id)
        session.dept = dept
        session.major = major
        session.direction = direction
        session.current_stage = "topic"
        self._save_session_to_db(session)
        return True

    def select_topic(self, session_id: str, topic: Dict) -> bool:
        """选择选题"""
        session = self._get_or_create(session_id)
        session.selected_topic = topic
        session.current_stage = "research"
        self._save_session_to_db(session)
        return True

    def set_research_plan(self, session_id: str, plan: Dict) -> bool:
        """设置研究计划"""
        session = self._get_or_create(session_id)
        session.research_plan = plan
        session.current_stage = "data"
        self._save_session_to_db(session)
        return True

    def upload_data(self, session_id: str, data: Dict) -> bool:
        """上传数据"""
        session = self._get_or_create(session_id)
        session.csv_data = data
        self._save_session_to_db(session)
        return True

    def set_analysis_result(self, session_id: str, result: Dict) -> bool:
        """设置分析结果"""
        session = self._get_or_create(session_id)
        session.analysis_result = result
        session.current_stage = "defense"
        self._save_session_to_db(session)
        return True

    def add_defense_record(self, session_id: str, question: str,
                          answer: str, score: Dict) -> bool:
        """添加答辩记录"""
        session = self._get_or_create(session_id)
        record = {
            "question": question,
            "answer": answer,
            "score": score,
            "timestamp": datetime.now().isoformat()
        }
        session.defense_records.append(record)

        # 计算平均分
        if session.defense_records:
            avg_score = {}
            for key in ["innovation", "technique", "logic", "presentation"]:
                values = [r["score"].get(key, 0) for r in session.defense_records if key in r.get("score", {})]
                avg_score[key] = round(sum(values) / len(values), 1) if values else 0
            session.defense_score = avg_score

        session.current_stage = "report"
        self._save_session_to_db(session)
        return True

    def get_progress_summary(self, session_id: str) -> Dict:
        """获取进度摘要"""
        session = self.get_session(session_id)
        if not session:
            return {"error": "会话不存在"}

        stages = ["init", "topic", "research", "data", "defense", "report"]
        current_index = stages.index(session.current_stage) if session.current_stage in stages else 0

        return {
            "session_id": session_id,
            "current_stage": session.current_stage,
            "progress": f"{current_index + 1}/{len(stages)}",
            "completed_stages": stages[:current_index + 1],
            "has_topic": session.selected_topic is not None,
            "has_plan": session.research_plan is not None,
            "has_data": session.csv_data is not None,
            "defense_count": len(session.defense_records),
            "defense_score": session.defense_score
        }

    def recommend_next_step(self, session_id: str) -> str:
        """推荐下一步"""
        session = self.get_session(session_id)
        if not session:
            return "请先创建会话"

        recommendations = {
            "init": "请填写基本信息（院系、专业、研究方向）",
            "topic": "请选择一个合适的毕业设计选题",
            "research": "请查看AI生成的研究方案，开始设计实验",
            "data": "请上传数据文件进行分析",
            "defense": "请开始模拟答辩练习",
            "report": "您可以查看答辩报告和评分"
        }

        return recommendations.get(session.current_stage, "继续完善您的毕业设计")

    def _get_or_create(self, session_id: str) -> SessionState:
        """获取或创建会话"""
        session = self.get_session(session_id)
        if not session:
            session = SessionState(session_id=session_id)
            self._sessions[session_id] = session
            try:
                SessionCRUD.create(session_id=session_id)
            except Exception:
                pass
        return session

    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """清理过期会话"""
        cutoff = datetime.now().timestamp() - (max_age_hours * 3600)
        expired = []
        for sid, session in self._sessions.items():
            try:
                created = datetime.fromisoformat(session.created_at).timestamp()
                if created < cutoff:
                    expired.append(sid)
            except Exception:
                pass

        for sid in expired:
            del self._sessions[sid]
            print(f"[Agent] 清理过期会话: {sid}")


# 全局实例
_agent: Optional[WorkflowAgent] = None


def get_agent() -> WorkflowAgent:
    """获取Agent实例（单例）"""
    global _agent
    if _agent is None:
        _agent = WorkflowAgent()
    return _agent
