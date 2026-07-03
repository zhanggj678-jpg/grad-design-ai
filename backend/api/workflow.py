"""
工作流路由 - 会话管理、进度查询、智能推荐
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from core.agent import get_agent
from database.crud import (
    create_user_session, get_full_session, SessionCRUD
)

router = APIRouter(prefix="/workflow", tags=["工作流"])


# ========== 请求模型 ==========

class CreateSessionResponse(BaseModel):
    success: bool
    session_id: Optional[str] = None
    error: Optional[str] = None


class RecommendResponse(BaseModel):
    success: bool
    current_stage: Optional[str] = None
    next_stage: Optional[str] = None
    next_action: Optional[str] = None
    reason: Optional[str] = None
    tips: Optional[list] = None
    estimated_time: Optional[str] = None
    progress: Optional[int] = None
    session_id: Optional[str] = None
    completed_steps: Optional[list] = None
    total_steps: Optional[int] = None
    error: Optional[str] = None


class ProgressResponse(BaseModel):
    success: bool
    session_id: str
    current_stage: Optional[str] = None
    progress_percent: Optional[int] = None
    selected_topic: Optional[dict] = None
    defense_score: Optional[dict] = None
    defense_count: Optional[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    error: Optional[str] = None


class FullSessionResponse(BaseModel):
    success: bool
    session_id: str
    session: Optional[dict] = None
    error: Optional[str] = None


# ========== 路由 ==========

@router.post("/session", response_model=CreateSessionResponse)
async def create_session():
    """创建新会话"""
    session_id = create_user_session()
    return CreateSessionResponse(success=True, session_id=session_id)


@router.get("/recommend/{session_id}", response_model=RecommendResponse)
async def recommend_next_step(session_id: str):
    """获取下一步推荐"""
    agent = get_agent()
    
    try:
        result = await agent.recommend_next_step(session_id)
        return RecommendResponse(success=True, **result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/progress/{session_id}", response_model=ProgressResponse)
async def get_progress(session_id: str):
    """获取进度摘要"""
    agent = get_agent()
    
    try:
        result = agent.get_progress_summary(session_id)
        return ProgressResponse(success=True, **result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/session/{session_id}", response_model=FullSessionResponse)
async def get_session(session_id: str):
    """获取完整会话信息"""
    session = get_full_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    return FullSessionResponse(success=True, session_id=session_id, session=session)
