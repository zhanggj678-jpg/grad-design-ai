"""
答辩路由 - 问题生成、回答评估、报告生成
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from service.defense_service import DefenseService

router = APIRouter(prefix="/defense", tags=["模拟答辩"])


# ========== 请求模型 ==========

class GenerateQuestionsRequest(BaseModel):
    session_id: str
    count: int = 6


class EvaluateRequest(BaseModel):
    session_id: str
    question: str
    answer: str
    question_index: int = 0


class SessionRequest(BaseModel):
    session_id: str


class QuestionsResponse(BaseModel):
    success: bool
    session_id: str
    questions: List[str] = []
    error: Optional[str] = None


class EvaluateResponse(BaseModel):
    success: bool
    session_id: str
    question_index: int
    evaluation: Optional[dict] = None
    error: Optional[str] = None


class ReportResponse(BaseModel):
    success: bool
    session_id: str
    overall_score: Optional[float] = None
    overall_level: Optional[str] = None
    stats: Optional[dict] = None
    record_count: Optional[int] = None
    advice: Optional[str] = None
    records: Optional[list] = None
    error: Optional[str] = None


# ========== 路由 ==========

@router.post("/questions", response_model=QuestionsResponse)
async def generate_questions(req: GenerateQuestionsRequest):
    """生成答辩问题"""
    result = await DefenseService.generate_questions(req.session_id, req.count)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "生成失败"))
    
    return QuestionsResponse(**result)


@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_answer(req: EvaluateRequest):
    """评估答辩回答"""
    result = await DefenseService.evaluate_answer(
        session_id=req.session_id,
        question=req.question,
        answer=req.answer,
        question_index=req.question_index
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "评估失败"))
    
    return EvaluateResponse(**result)


@router.get("/history/{session_id}")
async def get_defense_history(session_id: str):
    """获取答辩历史"""
    records = DefenseService.get_defense_history(session_id)
    return {
        "success": True,
        "session_id": session_id,
        "records": records
    }


@router.get("/stats/{session_id}")
async def get_defense_stats(session_id: str):
    """获取答辩统计"""
    stats = DefenseService.get_defense_stats(session_id)
    return {
        "success": True,
        "session_id": session_id,
        "stats": stats
    }


@router.post("/report", response_model=ReportResponse)
async def generate_report(req: SessionRequest):
    """生成答辩综合报告"""
    result = await DefenseService.generate_report(req.session_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "生成报告失败"))
    
    return ReportResponse(**result)
