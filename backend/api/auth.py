"""
认证路由 - 注册、登录、用户信息
"""
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from typing import Optional

from service.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["认证"])


# ========== 请求模型 ==========

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    success: bool
    user_id: Optional[int] = None
    username: Optional[str] = None
    token: Optional[str] = None
    error: Optional[str] = None


class UserInfoResponse(BaseModel):
    success: bool
    user: Optional[dict] = None
    error: Optional[str] = None


# ========== 路由 ==========

@router.post("/register", response_model=AuthResponse)
async def register(req: RegisterRequest):
    """用户注册"""
    result = AuthService.register(req.username, req.email, req.password)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return AuthResponse(**result)


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest):
    """用户登录"""
    result = AuthService.login(req.username, req.password)
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["error"])
    return AuthResponse(**result)


@router.get("/me", response_model=UserInfoResponse)
async def get_me(authorization: Optional[str] = Header(None)):
    """获取当前用户信息"""
    if not authorization:
        raise HTTPException(status_code=401, detail="缺少认证信息")

    # 提取token
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization

    user = AuthService.get_current_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Token无效或已过期")

    return UserInfoResponse(success=True, user=user)
