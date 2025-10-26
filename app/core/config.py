"""
应用配置模块
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""

    # 环境配置
    APP_ENV: str = "development"
    DEBUG: bool = True

    # B站API配置
    BILIBILI_COOKIE: Optional[str] = None
    BILIBILI_API_BASE: str = "https://api.bilibili.com"

    # ASR配置
    ASR_PROVIDER: str = "bcut"  # bcut or whisper
    WHISPER_MODEL: str = "base"

    # 文件存储
    UPLOAD_DIR: str = "./data/uploads"
    TEMP_DIR: str = "./data/temp"
    MAX_FILE_SIZE: str = "500MB"

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"

    # DeepSeek API配置（预留）
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_API_URL: str = "https://api.deepseek.com/v1"

    # 任务配置
    MAX_VIDEO_DURATION: int = 7200  # 最大视频时长（秒）
    REQUEST_TIMEOUT: int = 1800  # 请求超时时间（秒）
    MAX_RETRY: int = 3  # 最大重试次数

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# 创建全局配置实例
settings = Settings()
