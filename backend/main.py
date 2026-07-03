"""
FastAPI 入口文件
毕业设计全流程助手 - 后端服务
"""
import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 加载环境变量（必须在其他模块导入之前）
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# 初始化数据库
from database.db import init_database
init_database()

# 导入路由 - 使用直接导入避免相对导入问题
from api.auth import router as auth_router
from api.topics import router as topics_router
from api.analysis import router as analysis_router
from api.defense import router as defense_router
from api.workflow import router as workflow_router
from api.export import router as export_router

# 创建FastAPI应用
app = FastAPI(
    title="毕业设计全流程助手 API",
    description="AI驱动的毕业设计选题、研究、分析、答辩一体化平台",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS配置 - 允许前端跨域访问
# 生产环境应限制为具体域名，开发环境使用环境变量或默认值
_cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
if _cors_origins == ["*"]:
    _cors_allow_all = True
else:
    _cors_allow_all = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if _cors_allow_all else _cors_origins,
    allow_credentials=not _cors_allow_all,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router)
app.include_router(topics_router)
app.include_router(analysis_router)
app.include_router(defense_router)
app.include_router(workflow_router)
app.include_router(export_router)


@app.get("/")
async def root():
    """根路径 - API信息"""
    return {
        "name": "毕业设计全流程助手 API",
        "version": "1.0.0",
        "description": "AI驱动的毕业设计选题、研究、分析、答辩一体化平台",
        "docs": "/docs",
        "endpoints": {
            "auth": "/auth",
            "topics": "/topics",
            "analysis": "/analysis",
            "defense": "/defense",
            "workflow": "/workflow"
        }
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    from database.db import check_database
    db_status = check_database()
    
    return {
        "status": "healthy",
        "database": db_status,
        "version": "1.0.0"
    }


# 托管前端页面（部署后访问 / 即可打开前端）
_FRONTEND_HTML = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "rag-grad-assistant-demo.html")

@app.get("/app")
async def serve_frontend():
    """返回前端HTML页面"""
    if os.path.exists(_FRONTEND_HTML):
        return FileResponse(_FRONTEND_HTML, media_type="text/html; charset=utf-8")
    return {"error": "Frontend not found"}


# 启动命令（开发环境）
# uvicorn main:app --reload --host 0.0.0.0 --port 8000

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)
