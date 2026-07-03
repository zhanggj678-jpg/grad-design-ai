"""
数据库核心模块 - 连接管理和表定义
使用SQLite，支持异步操作
"""
import os
import sqlite3
from typing import Optional
from contextlib import contextmanager
from datetime import datetime

# 数据库文件路径
# Render 等云平台文件系统只读，使用 /tmp 作为可写目录
DB_DIR = os.getenv("DB_DIR", os.path.join(os.sep, "tmp", "grad_design_db"))
DB_PATH = os.path.join(DB_DIR, "grad_design.db")

# 确保 DB_DIR 目录存在
os.makedirs(DB_DIR, exist_ok=True)


def get_db_path() -> str:
    """获取数据库路径"""
    return DB_PATH


@contextmanager
def get_db_connection():
    """
    获取数据库连接（上下文管理器）
    使用示例：
        with get_db_connection() as conn:
            cursor = conn.execute("SELECT * FROM users")
            rows = cursor.fetchall()
    """
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # 让结果可以通过列名访问
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def init_database():
    """初始化数据库 - 创建所有表"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 1. 用户表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                avatar TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. 会话表 - 记录用户每次使用的工作流会话
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                user_id INTEGER,
                current_stage TEXT DEFAULT 'init',
                dept TEXT DEFAULT '',
                major TEXT DEFAULT '',
                direction TEXT DEFAULT '',
                selected_topic TEXT DEFAULT '',  -- JSON
                research_plan TEXT DEFAULT '',   -- JSON
                csv_data TEXT DEFAULT '',        -- JSON
                analysis_result TEXT DEFAULT '', -- JSON
                defense_score TEXT DEFAULT '',   -- JSON
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # 3. 选题记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                difficulty INTEGER DEFAULT 3,
                tags TEXT DEFAULT '',  -- JSON数组
                is_selected INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)

        # 4. 答辩记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS defense_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT DEFAULT '',
                score TEXT DEFAULT '',  -- JSON
                feedback TEXT DEFAULT '',
                level TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)

        # 5. 数据分析记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analysis_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                filename TEXT DEFAULT '',
                row_count INTEGER DEFAULT 0,
                column_count INTEGER DEFAULT 0,
                summary TEXT DEFAULT '',      -- JSON
                charts TEXT DEFAULT '',       -- JSON
                insights TEXT DEFAULT '',     -- JSON
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)

        # 6. 操作日志表 - 用于审计和调试
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS operation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                user_id INTEGER,
                action TEXT NOT NULL,
                details TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 7. 用户行为分析表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                user_id INTEGER,
                action TEXT NOT NULL,
                duration_seconds INTEGER DEFAULT 0,
                step_completed INTEGER DEFAULT 0,
                details TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)

        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON sessions(session_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_topics_session_id ON topics(session_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_defense_session_id ON defense_records(session_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_analysis_session_id ON analysis_records(session_id)
        """)

        conn.commit()
        print(f"[DB] Database initialized at: {DB_PATH}")


def check_database() -> dict:
    """检查数据库状态，返回各表记录数"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        tables = ['users', 'sessions', 'topics', 'defense_records', 'analysis_records', 'operation_logs']
        result = {}
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                result[table] = cursor.fetchone()[0]
            except:
                result[table] = -1
        return result


def reset_database():
    """重置数据库（危险操作，仅开发使用）"""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_database()


# 初始化时自动建表
if __name__ == "__main__":
    init_database()
    print("Tables count:", check_database())
