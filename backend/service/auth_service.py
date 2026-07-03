"""
认证服务 - 用户注册、登录、JWT管理
使用 bcrypt 进行密码哈希，PyJWT 进行令牌管理
"""
import os
import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict

# JWT密钥（优先从环境变量获取，开发环境使用固定默认值）
_is_production = os.getenv("ENV", "development") == "production"
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    if _is_production:
        raise ValueError(
            "JWT_SECRET 环境变量未设置！\n"
            "请在 .env 文件中设置 JWT_SECRET=your_secret_key_here\n"
            "或使用命令: export JWT_SECRET=$(openssl rand -hex 32)"
        )
    else:
        # 开发环境使用固定默认值（仅用于本地测试）
        JWT_SECRET = "dev-jwt-secret-do-not-use-in-production-2024"

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24


def hash_password(password: str) -> str:
    """密码哈希（bcrypt）"""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """验证密码"""
    try:
        password_bytes = password.encode('utf-8')
        hashed_bytes = hashed.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


def create_access_token(user_id: int, username: str) -> str:
    """创建访问令牌"""
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {
        "user_id": user_id,
        "username": username,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=ALGORITHM)


def verify_token(token: str) -> Optional[Dict]:
    """验证令牌，返回payload"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


# ========== 业务逻辑 ==========

from database.crud import UserCRUD


class AuthService:
    """认证服务"""

    @staticmethod
    def register(username: str, email: str, password: str) -> Dict:
        """用户注册"""
        # 验证输入
        if len(username) < 3 or len(username) > 20:
            return {"success": False, "error": "用户名长度需在3-20个字符之间"}
        if len(password) < 6:
            return {"success": False, "error": "密码长度至少6位"}
        if "@" not in email or "." not in email.split("@")[-1]:
            return {"success": False, "error": "邮箱格式不正确"}

        # 检查用户名/邮箱是否已存在
        if UserCRUD.get_by_username(username):
            return {"success": False, "error": "用户名已存在"}
        if UserCRUD.get_by_email(email):
            return {"success": False, "error": "邮箱已被注册"}

        # 创建用户
        password_hash = hash_password(password)
        user_id = UserCRUD.create(username, email, password_hash)

        if not user_id:
            return {"success": False, "error": "创建用户失败"}

        # 生成Token
        token = create_access_token(user_id, username)

        return {
            "success": True,
            "user_id": user_id,
            "username": username,
            "token": token
        }

    @staticmethod
    def login(username: str, password: str) -> Dict:
        """用户登录"""
        user = UserCRUD.get_by_username(username)
        if not user:
            return {"success": False, "error": "用户名或密码错误"}

        if not verify_password(password, user["password_hash"]):
            return {"success": False, "error": "用户名或密码错误"}

        # 生成Token
        token = create_access_token(user["id"], user["username"])

        return {
            "success": True,
            "user_id": user["id"],
            "username": user["username"],
            "token": token
        }

    @staticmethod
    def get_current_user(token: str) -> Optional[Dict]:
        """获取当前用户"""
        payload = verify_token(token)
        if not payload:
            return None

        user_id = payload.get("user_id")
        if not user_id:
            return None

        return UserCRUD.get_by_id(user_id)
