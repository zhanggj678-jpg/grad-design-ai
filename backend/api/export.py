"""
导出路由 - 开题报告导出
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from service.export_service import ExportService

router = APIRouter(prefix="/export", tags=["导出"])


class ExportRequest(BaseModel):
    session_id: str


class ExportResponse(BaseModel):
    success: bool
    html: Optional[str] = None
    filename: Optional[str] = None
    title: Optional[str] = None
    error: Optional[str] = None


@router.post("/opening-report", response_model=ExportResponse)
async def export_opening_report(req: ExportRequest):
    """导出开题报告"""
    from core.agent import get_agent

    agent = get_agent()
    session = agent.get_session(req.session_id)

    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")

    if not session.selected_topic:
        raise HTTPException(status_code=400, detail="请先选择选题")

    session_data = session.to_dict()
    result = ExportService.generate_opening_report(session_data)

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "生成失败"))

    return ExportResponse(**result)
