"""
API数据模型
"""
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Literal
from datetime import datetime


class VideoRequest(BaseModel):
    """视频请求模型"""
    url: str = Field(..., description="B站视频URL")
    format: Literal["txt", "srt", "json"] = Field(default="txt", description="输出格式")


class Utterance(BaseModel):
    """单句话模型"""
    text: str = Field(..., description="文本内容")
    start: float = Field(..., description="开始时间（秒）")
    end: float = Field(..., description="结束时间（秒）")


class TranscriptData(BaseModel):
    """逐字稿数据模型"""
    bvid: str = Field(..., description="视频BV号")
    title: str = Field(..., description="视频标题")
    duration: int = Field(..., description="视频时长（秒）")
    method: Literal["subtitle", "ai_subtitle", "asr"] = Field(..., description="提取方法")
    transcript: str = Field(..., description="完整的逐字稿文本")
    utterances: List[Utterance] = Field(..., description="带时间戳的句子列表")


class APIResponse(BaseModel):
    """API响应模型"""
    code: int = Field(..., description="状态码，0表示成功")
    message: str = Field(..., description="响应消息")
    data: Optional[TranscriptData] = Field(None, description="响应数据")


class ProgressResponse(BaseModel):
    """进度响应模型"""
    task_id: str = Field(..., description="任务ID")
    status: Literal["pending", "processing", "completed", "failed"] = Field(..., description="任务状态")
    progress: int = Field(..., description="进度百分比（0-100）")
    message: str = Field(..., description="当前状态描述")
    result: Optional[TranscriptData] = Field(None, description="完成后的结果")


class SummaryRequest(BaseModel):
    """总结请求模型（预留给DeepSeek）"""
    transcript: str = Field(..., description="逐字稿文本")
    style: Literal["brief", "detailed", "academic"] = Field(default="brief", description="总结风格")


class SummaryResponse(BaseModel):
    """总结响应模型（预留给DeepSeek）"""
    summary: str = Field(..., description="总结内容")
    key_points: List[str] = Field(..., description="关键要点")
