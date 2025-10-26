"""
B站视频逐字稿提取系统 - FastAPI Main Application
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, HttpUrl
from typing import Optional, List
import logging
from pathlib import Path

# 导入路由和配置
from app.api import routes
from app.core.config import settings
from app.core.logger import setup_logging

# 初始化日志
setup_logging()
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="Bilibili Transcript Extractor",
    description="B站视频逐字稿提取系统",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(routes.router, prefix="/api")

# 挂载静态文件目录（前端）
frontend_path = Path(__file__).parent / "frontend"
if frontend_path.exists():
    app.mount("/", StaticFiles(directory=str(frontend_path), html=True), name="frontend")


@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    logger.info("Starting Bilibili Transcript Extractor...")

    # 创建必要的目录
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.TEMP_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.LOG_FILE).parent.mkdir(parents=True, exist_ok=True)

    logger.info("Application started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    logger.info("Shutting down Bilibili Transcript Extractor...")


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Bilibili Transcript Extractor API",
        "docs": "/api/docs",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
