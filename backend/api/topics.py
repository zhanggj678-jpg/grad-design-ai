"""
选题路由 - 生成选题、选择选题、研究思路
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from service.topic_service import TopicService
from database.crud import create_user_session

router = APIRouter(prefix="/topics", tags=["选题"])


# ========== 请求模型 ==========

class GenerateTopicsRequest(BaseModel):
    session_id: Optional[str] = None
    dept: str
    major: str
    direction: str
    count: int = 4


class SelectTopicRequest(BaseModel):
    session_id: str
    topic_id: int


class SessionResponse(BaseModel):
    success: bool
    session_id: Optional[str] = None
    error: Optional[str] = None


class TopicsResponse(BaseModel):
    success: bool
    session_id: str
    major: Optional[str] = None
    direction: Optional[str] = None
    topics: List[dict] = []
    error: Optional[str] = None


class PlanResponse(BaseModel):
    success: bool
    session_id: str
    plan: Optional[dict] = None
    error: Optional[str] = None


# ========== 路由 ==========

@router.post("/generate", response_model=TopicsResponse)
async def generate_topics(req: GenerateTopicsRequest):
    """生成毕业设计选题"""
    # 如果没有session_id，创建新会话
    if not req.session_id:
        req.session_id = create_user_session()

    result = await TopicService.generate_topics(
        session_id=req.session_id,
        dept=req.dept,
        major=req.major,
        direction=req.direction,
        count=req.count
    )

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "生成失败"))

    return TopicsResponse(**result)


@router.post("/select", response_model=TopicsResponse)
async def select_topic(req: SelectTopicRequest):
    """选择选题"""
    result = TopicService.select_topic(req.session_id, req.topic_id)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "选择失败"))

    return TopicsResponse(**result)


@router.post("/research-plan", response_model=PlanResponse)
async def generate_research_plan(req: SessionResponse):
    """生成研究思路"""
    if not req.session_id:
        raise HTTPException(status_code=400, detail="缺少session_id")

    result = await TopicService.generate_research_plan(req.session_id)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "生成失败"))

    return PlanResponse(**result)


@router.get("/session/{session_id}")
async def get_session_topics(session_id: str):
    """获取会话的选题列表"""
    topics = TopicService.get_session_topics(session_id)
    return {"success": True, "session_id": session_id, "topics": topics}
