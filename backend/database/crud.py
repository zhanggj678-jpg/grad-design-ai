"""
CRUD操作模块 - 数据库增删改查封装
所有数据库操作都通过这里，上层不直接操作SQL
"""
import json
import sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime

from .db import get_db_connection


# ========== 通用工具 ==========

def _now() -> str:
    """当前时间ISO格式"""
    return datetime.now().isoformat()


def _to_json(data: Any) -> str:
    """将数据转为JSON字符串"""
    if data is None:
        return ""
    return json.dumps(data, ensure_ascii=False)


def _from_json(json_str: str) -> Any:
    """将JSON字符串转为数据"""
    if not json_str:
        return None
    try:
        return json.loads(json_str)
    except:
        return None


def _row_to_dict(row: sqlite3.Row) -> Dict:
    """将sqlite3.Row转为字典"""
    return {key: row[key] for key in row.keys()}


# ========== 用户相关 CRUD ==========

class UserCRUD:
    """用户表CRUD"""

    @staticmethod
    def create(username: str, email: str, password_hash: str) -> Optional[int]:
        """创建用户，返回用户ID"""
        try:
            with get_db_connection() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO users (username, email, password_hash, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (username, email, password_hash, _now(), _now())
                )
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None  # 用户名或邮箱已存在

    @staticmethod
    def get_by_id(user_id: int) -> Optional[Dict]:
        """根据ID获取用户"""
        with get_db_connection() as conn:
            cursor = conn.execute(
                "SELECT id, username, email, avatar, created_at FROM users WHERE id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            return _row_to_dict(row) if row else None

    @staticmethod
    def get_by_username(username: str) -> Optional[Dict]:
        """根据用户名获取用户（包含密码hash，用于登录）"""
        with get_db_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,)
            )
            row = cursor.fetchone()
            return _row_to_dict(row) if row else None

    @staticmethod
    def get_by_email(email: str) -> Optional[Dict]:
        """根据邮箱获取用户"""
        with get_db_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM users WHERE email = ?",
                (email,)
            )
            row = cursor.fetchone()
            return _row_to_dict(row) if row else None


# ========== 会话相关 CRUD ==========

class SessionCRUD:
    """会话表CRUD"""

    @staticmethod
    def create(session_id: str, user_id: Optional[int] = None) -> bool:
        """创建会话"""
        try:
            with get_db_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO sessions (session_id, user_id, current_stage, created_at, updated_at)
                    VALUES (?, ?, 'init', ?, ?)
                    """,
                    (session_id, user_id, _now(), _now())
                )
                return True
        except sqlite3.IntegrityError:
            return False

    @staticmethod
    def get(session_id: str) -> Optional[Dict]:
        """获取会话"""
        with get_db_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM sessions WHERE session_id = ?",
                (session_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            data = _row_to_dict(row)
            # 解析JSON字段
            data['selected_topic'] = _from_json(data.get('selected_topic', ''))
            data['research_plan'] = _from_json(data.get('research_plan', ''))
            data['csv_data'] = _from_json(data.get('csv_data', ''))
            data['analysis_result'] = _from_json(data.get('analysis_result', ''))
            data['defense_score'] = _from_json(data.get('defense_score', ''))
            return data

    @staticmethod
    def update_stage(session_id: str, stage: str) -> bool:
        """更新会话阶段"""
        with get_db_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE sessions SET current_stage = ?, updated_at = ? WHERE session_id = ?
                """,
                (stage, _now(), session_id)
            )
            return cursor.rowcount > 0

    @staticmethod
    def update_major(session_id: str, dept: str, major: str, direction: str) -> bool:
        """更新专业信息"""
        with get_db_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE sessions
                SET dept = ?, major = ?, direction = ?, current_stage = 'major_selected', updated_at = ?
                WHERE session_id = ?
                """,
                (dept, major, direction, _now(), session_id)
            )
            return cursor.rowcount > 0

    @staticmethod
    def update_topic(session_id: str, topic: Dict) -> bool:
        """更新选题"""
        with get_db_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE sessions
                SET selected_topic = ?, current_stage = 'topic_selected', updated_at = ?
                WHERE session_id = ?
                """,
                (_to_json(topic), _now(), session_id)
            )
            return cursor.rowcount > 0

    @staticmethod
    def update_research_plan(session_id: str, plan: Dict) -> bool:
        """更新研究计划"""
        with get_db_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE sessions
                SET research_plan = ?, current_stage = 'research_planned', updated_at = ?
                WHERE session_id = ?
                """,
                (_to_json(plan), _now(), session_id)
            )
            return cursor.rowcount > 0

    @staticmethod
    def update_csv_data(session_id: str, data: Dict) -> bool:
        """更新CSV数据"""
        with get_db_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE sessions
                SET csv_data = ?, current_stage = 'data_uploaded', updated_at = ?
                WHERE session_id = ?
                """,
                (_to_json(data), _now(), session_id)
            )
            return cursor.rowcount > 0

    @staticmethod
    def update_analysis_result(session_id: str, result: Dict) -> bool:
        """更新分析结果"""
        with get_db_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE sessions
                SET analysis_result = ?, current_stage = 'analysis_done', updated_at = ?
                WHERE session_id = ?
                """,
                (_to_json(result), _now(), session_id)
            )
            return cursor.rowcount > 0

    @staticmethod
    def update_defense_score(session_id: str, score: Dict) -> bool:
        """更新答辩分数"""
        with get_db_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE sessions
                SET defense_score = ?, current_stage = 'defense_done', updated_at = ?
                WHERE session_id = ?
                """,
                (_to_json(score), _now(), session_id)
            )
            return cursor.rowcount > 0

    @staticmethod
    def list_by_user(user_id: int, limit: int = 20) -> List[Dict]:
        """获取用户的所有会话"""
        with get_db_connection() as conn:
            cursor = conn.execute(
                """
                SELECT session_id, current_stage, dept, major, direction,
                       selected_topic, created_at, updated_at
                FROM sessions WHERE user_id = ? ORDER BY updated_at DESC LIMIT ?
                """,
                (user_id, limit)
            )
            rows = cursor.fetchall()
            result = []
            for row in rows:
                data = _row_to_dict(row)
                data['selected_topic'] = _from_json(data.get('selected_topic', ''))
                result.append(data)
            return result

    @staticmethod
    def update_fields(session_id: str, **kwargs) -> bool:
        """动态更新会话字段"""
        if not kwargs:
            return False

        # 构建SET子句
        allowed_fields = ['current_stage', 'dept', 'major', 'direction',
                         'selected_topic', 'research_plan', 'csv_data',
                         'analysis_result', 'defense_score']

        fields = []
        values = []
        for key, val in kwargs.items():
            if key in allowed_fields:
                fields.append(f"{key} = ?")
                values.append(val)

        if not fields:
            return False

        fields.append("updated_at = ?")
        values.append(_now())
        values.append(session_id)

        with get_db_connection() as conn:
            cursor = conn.execute(
                f"UPDATE sessions SET {', '.join(fields)} WHERE session_id = ?",
                values
            )
            return cursor.rowcount > 0

    @staticmethod
    def get_by_session_id(session_id: str) -> Optional[Dict]:
        """根据session_id获取会话（别名，与get相同但语义更清晰）"""
        return SessionCRUD.get(session_id)

    @staticmethod
    def delete(session_id: str) -> bool:
        """删除会话"""
        with get_db_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM sessions WHERE session_id = ?",
                (session_id,)
            )
            return cursor.rowcount > 0


# ========== 选题相关 CRUD ==========

class TopicCRUD:
    """选题表CRUD"""

    @staticmethod
    def create(session_id: str, title: str, description: str = "",
               difficulty: int = 3, tags: List[str] = None) -> int:
        """创建选题记录"""
        with get_db_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO topics (session_id, title, description, difficulty, tags, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (session_id, title, description, difficulty,
                 _to_json(tags or []), _now())
            )
            return cursor.lastrowid

    @staticmethod
    def get_by_session(session_id: str) -> List[Dict]:
        """获取会话的所有选题"""
        with get_db_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM topics WHERE session_id = ? ORDER BY created_at",
                (session_id,)
            )
            rows = cursor.fetchall()
            result = []
            for row in rows:
                data = _row_to_dict(row)
                data['tags'] = _from_json(data.get('tags', '[]'))
                data['is_selected'] = bool(data.get('is_selected', 0))
                result.append(data)
            return result

    @staticmethod
    def mark_selected(topic_id: int) -> bool:
        """标记选题为已选中"""
        with get_db_connection() as conn:
            cursor = conn.execute(
                "UPDATE topics SET is_selected = 1 WHERE id = ?",
                (topic_id,)
            )
            return cursor.rowcount > 0

    @staticmethod
    def delete_by_session(session_id: str) -> bool:
        """删除会话的所有选题"""
        with get_db_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM topics WHERE session_id = ?",
                (session_id,)
            )
            return cursor.rowcount > 0


# ========== 答辩记录相关 CRUD ==========

class DefenseCRUD:
    """答辩记录表CRUD"""

    @staticmethod
    def create(session_id: str, question: str, answer: str = "",
               score: Dict = None, feedback: str = "", level: str = "") -> int:
        """创建答辩记录"""
        with get_db_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO defense_records
                (session_id, question, answer, score, feedback, level, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (session_id, question, answer, _to_json(score or {}),
                 feedback, level, _now())
            )
            return cursor.lastrowid

    @staticmethod
    def get_by_session(session_id: str) -> List[Dict]:
        """获取会话的所有答辩记录"""
        with get_db_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM defense_records
                WHERE session_id = ? ORDER BY created_at
                """,
                (session_id,)
            )
            rows = cursor.fetchall()
            result = []
            for row in rows:
                data = _row_to_dict(row)
                data['score'] = _from_json(data.get('score', '{}'))
                result.append(data)
            return result

    @staticmethod
    def get_stats(session_id: str) -> Dict:
        """获取答辩统计"""
        with get_db_connection() as conn:
            cursor = conn.execute(
                """
                SELECT COUNT(*) as count,
                       AVG(CAST(json_extract(score, '$.innovation') AS REAL)) as avg_innovation,
                       AVG(CAST(json_extract(score, '$.technique') AS REAL)) as avg_technique,
                       AVG(CAST(json_extract(score, '$.logic') AS REAL)) as avg_logic,
                       AVG(CAST(json_extract(score, '$.presentation') AS REAL)) as avg_presentation
                FROM defense_records WHERE session_id = ?
                """,
                (session_id,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    "count": row["count"],
                    "avg_innovation": row["avg_innovation"] or 0,
                    "avg_technique": row["avg_technique"] or 0,
                    "avg_logic": row["avg_logic"] or 0,
                    "avg_presentation": row["avg_presentation"] or 0
                }
            return {"count": 0, "avg_innovation": 0, "avg_technique": 0,
                    "avg_logic": 0, "avg_presentation": 0}

    @staticmethod
    def delete_by_session(session_id: str) -> bool:
        """删除会话的所有答辩记录"""
        with get_db_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM defense_records WHERE session_id = ?",
                (session_id,)
            )
            return cursor.rowcount > 0


# ========== 数据分析相关 CRUD ==========

class AnalysisCRUD:
    """数据分析记录表CRUD"""

    @staticmethod
    def create(session_id: str, filename: str = "", row_count: int = 0,
               column_count: int = 0, summary: Dict = None,
               charts: List = None, insights: List = None) -> int:
        """创建分析记录"""
        with get_db_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO analysis_records
                (session_id, filename, row_count, column_count, summary, charts, insights, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (session_id, filename, row_count, column_count,
                 _to_json(summary or {}), _to_json(charts or []),
                 _to_json(insights or []), _now())
            )
            return cursor.lastrowid

    @staticmethod
    def get_by_session(session_id: str) -> Optional[Dict]:
        """获取会话的分析记录"""
        with get_db_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM analysis_records
                WHERE session_id = ? ORDER BY created_at DESC LIMIT 1
                """,
                (session_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            data = _row_to_dict(row)
            data['summary'] = _from_json(data.get('summary', '{}'))
            data['charts'] = _from_json(data.get('charts', '[]'))
            data['insights'] = _from_json(data.get('insights', '[]'))
            return data

    @staticmethod
    def delete_by_session(session_id: str) -> bool:
        """删除会话的分析记录"""
        with get_db_connection() as conn:
            cursor = conn.execute(
                "DELETE FROM analysis_records WHERE session_id = ?",
                (session_id,)
            )
            return cursor.rowcount > 0


# ========== 操作日志相关 CRUD ==========

class LogCRUD:
    """操作日志表CRUD"""

    @staticmethod
    def create(session_id: Optional[str], user_id: Optional[int],
               action: str, details: str = "") -> int:
        """记录操作日志"""
        with get_db_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO operation_logs (session_id, user_id, action, details, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (session_id, user_id, action, details, _now())
            )
            return cursor.lastrowid

    @staticmethod
    def get_by_session(session_id: str, limit: int = 50) -> List[Dict]:
        """获取会话的操作日志"""
        with get_db_connection() as conn:
            cursor = conn.execute(
                """
                SELECT * FROM operation_logs
                WHERE session_id = ? ORDER BY created_at DESC LIMIT ?
                """,
                (session_id, limit)
            )
            rows = cursor.fetchall()
            return [_row_to_dict(row) for row in rows]


# ========== 便捷函数 ==========

def get_full_session(session_id: str) -> Optional[Dict]:
    """
    获取完整会话信息（包含关联数据）
    返回：会话 + 选题列表 + 答辩记录 + 分析记录
    """
    session = SessionCRUD.get(session_id)
    if not session:
        return None

    session['topics'] = TopicCRUD.get_by_session(session_id)
    session['defense_records'] = DefenseCRUD.get_by_session(session_id)
    session['analysis'] = AnalysisCRUD.get_by_session(session_id)
    session['defense_stats'] = DefenseCRUD.get_stats(session_id)

    return session


def create_user_session(user_id: Optional[int] = None) -> str:
    """
    创建新会话并返回session_id
    """
    import uuid
    session_id = str(uuid.uuid4())[:12]
    SessionCRUD.create(session_id, user_id)
    LogCRUD.create(session_id, user_id, "session_created", "新会话创建")
    return session_id
