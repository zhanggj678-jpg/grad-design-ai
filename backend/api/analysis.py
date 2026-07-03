"""
数据分析路由 - CSV上传、分析、结果获取、论文评审
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional

from service.analysis_service import AnalysisService

router = APIRouter(prefix="/analysis", tags=["数据分析"])


# ========== 请求模型 ==========

class AnalysisResponse(BaseModel):
    success: bool
    session_id: str
    filename: Optional[str] = None
    row_count: Optional[int] = None
    column_count: Optional[int] = None
    summary: Optional[dict] = None
    charts: Optional[list] = None
    insights: Optional[list] = None
    error: Optional[str] = None


class ReportReviewRequest(BaseModel):
    session_id: str
    title: str
    content: str


class ReportReviewResponse(BaseModel):
    success: bool
    session_id: str
    review: Optional[dict] = None
    error: Optional[str] = None


# ========== 路由 ==========

@router.post("/upload", response_model=AnalysisResponse)
async def upload_csv(
    session_id: str = Form(...),
    file: UploadFile = File(...)
):
    """
    上传CSV文件并分析
    
    - **session_id**: 会话ID
    - **file**: CSV文件
    """
    # 检查文件类型
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="只支持CSV文件")
    
    # 读取文件内容
    content = await file.read()
    try:
        csv_text = content.decode('utf-8')
    except UnicodeDecodeError:
        try:
            csv_text = content.decode('gbk')
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="文件编码不支持，请使用UTF-8或GBK编码")
    
    # 分析CSV
    result = AnalysisService.analyze_csv(session_id, file.filename, csv_text)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "分析失败"))
    
    return AnalysisResponse(**result)


@router.get("/result/{session_id}")
async def get_analysis_result(session_id: str):
    """获取分析结果"""
    result = AnalysisService.get_analysis(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="分析结果不存在")
    
    return {
        "success": True,
        "session_id": session_id,
        "analysis": result
    }


@router.post("/report-review", response_model=ReportReviewResponse)
async def report_review(req: ReportReviewRequest):
    """
    AI论文评审
    
    - **session_id**: 会话ID
    - **title**: 论文标题
    - **content**: 论文内容
    """
    result = await AnalysisService.review_report(
        session_id=req.session_id,
        title=req.title,
        content=req.content
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "评审失败"))
    
    return ReportReviewResponse(**result)
