"""
API路由
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.api.models import (
    VideoRequest, APIResponse, ProgressResponse,
    SummaryRequest, SummaryResponse, TranscriptData
)
from app.services.bilibili_api import BilibiliAPI
from app.services.subtitle_processor import SubtitleProcessor
from app.services.video_downloader import VideoDownloader
from app.services.asr_engine import ASREngine
from app.services.deepseek_service import DeepSeekService
import logging
import uuid
from typing import Dict

logger = logging.getLogger(__name__)

router = APIRouter()

# 任务存储（生产环境应使用Redis等持久化存储）
tasks: Dict[str, dict] = {}

bilibili_api = BilibiliAPI()
subtitle_processor = SubtitleProcessor()
video_downloader = VideoDownloader()
asr_engine = ASREngine()
deepseek_service = DeepSeekService()


@router.post("/extract", response_model=APIResponse)
async def extract_transcript(request: VideoRequest, background_tasks: BackgroundTasks):
    """
    提取视频逐字稿主接口
    """
    try:
        logger.info(f"Received request to extract transcript: {request.url}")

        # 步骤1：解析BV号
        bvid = bilibili_api.extract_bvid(request.url)
        if not bvid:
            raise HTTPException(status_code=400, detail="无效的B站视频链接")

        # 步骤2：获取视频信息
        video_info = await bilibili_api.get_video_info(bvid)
        if not video_info:
            raise HTTPException(status_code=404, detail="视频不存在或无法访问")

        cid = video_info.get('cid')
        title = video_info.get('title', '')
        duration = video_info.get('duration', 0)

        logger.info(f"Video info: {title} (BV{bvid}, CID: {cid})")

        # 步骤3：尝试获取CC字幕
        subtitle = await bilibili_api.get_subtitle(bvid, cid)
        if subtitle:
            logger.info("Found CC subtitle")
            utterances = subtitle_processor.parse_bilibili_subtitle(subtitle)
            transcript = subtitle_processor.format_transcript(utterances, request.format)

            return APIResponse(
                code=0,
                message="success",
                data=TranscriptData(
                    bvid=bvid,
                    title=title,
                    duration=duration,
                    method="subtitle",
                    transcript=transcript,
                    utterances=utterances
                )
            )

        # 步骤4：尝试获取AI字幕
        ai_subtitle = await bilibili_api.get_ai_subtitle(bvid, cid)
        if ai_subtitle:
            logger.info("Found AI subtitle")
            utterances = subtitle_processor.parse_bilibili_subtitle(ai_subtitle)
            transcript = subtitle_processor.format_transcript(utterances, request.format)

            return APIResponse(
                code=0,
                message="success",
                data=TranscriptData(
                    bvid=bvid,
                    title=title,
                    duration=duration,
                    method="ai_subtitle",
                    transcript=transcript,
                    utterances=utterances
                )
            )

        # 步骤5：没有字幕，需要下载视频并进行ASR
        logger.info("No subtitle found, will use ASR")

        # 检查 ASR 是否可用
        try:
            # 尝试导入 ASR 引擎检查是否可用
            if not hasattr(asr_engine, '_check_availability'):
                # 添加可用性检查方法
                from app.services.asr_engine import BCUT_AVAILABLE, WHISPER_AVAILABLE
                if not BCUT_AVAILABLE and not WHISPER_AVAILABLE:
                    raise HTTPException(
                        status_code=501,
                        detail="ASR 功能暂不可用。该视频没有字幕，需要语音识别功能，但当前部署环境不支持。建议选择有字幕的视频。"
                    )
        except ImportError:
            raise HTTPException(
                status_code=501,
                detail="ASR 功能暂不可用。该视频没有字幕，需要语音识别功能，但当前部署环境不支持。建议选择有字幕的视频。"
            )

        # 创建异步任务
        task_id = str(uuid.uuid4())
        tasks[task_id] = {
            "status": "pending",
            "progress": 0,
            "message": "任务已创建",
            "bvid": bvid,
            "title": title,
            "duration": duration
        }

        # 添加后台任务
        background_tasks.add_task(
            process_video_with_asr,
            task_id, request.url, bvid, cid, title, duration, request.format
        )

        return APIResponse(
            code=0,
            message="字幕不存在，已创建ASR任务",
            data=TranscriptData(
                bvid=bvid,
                title=title,
                duration=duration,
                method="asr",
                transcript=f"任务ID: {task_id}，请使用 /api/progress/{task_id} 查询进度",
                utterances=[]
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting transcript: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"服务器错误: {str(e)}")


@router.get("/progress/{task_id}", response_model=ProgressResponse)
async def get_progress(task_id: str):
    """
    查询任务进度
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")

    task = tasks[task_id]

    return ProgressResponse(
        task_id=task_id,
        status=task["status"],
        progress=task["progress"],
        message=task["message"],
        result=task.get("result")
    )


@router.post("/summarize", response_model=SummaryResponse)
async def summarize_transcript(request: SummaryRequest):
    """
    使用 DeepSeek 总结视频逐字稿

    将逐字稿整理成结构化笔记，突出重点，去掉口语化内容
    """
    try:
        logger.info(f"Received summarize request, text length: {len(request.transcript)}, style: {request.style}")

        # 检查文本长度
        if len(request.transcript) < 10:
            raise HTTPException(
                status_code=400,
                detail="逐字稿内容过短，无法总结"
            )

        # 调用 DeepSeek 服务
        result = await deepseek_service.summarize_transcript(
            transcript=request.transcript,
            style=request.style
        )

        logger.info(f"Summarization completed successfully")

        return SummaryResponse(
            summary=result["summary"],
            key_points=result["key_points"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Summarization failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"总结失败: {str(e)}"
        )


async def process_video_with_asr(
    task_id: str,
    url: str,
    bvid: str,
    cid: int,
    title: str,
    duration: int,
    output_format: str
):
    """
    后台任务：下载视频并进行ASR识别
    """
    try:
        # 更新进度：开始处理
        tasks[task_id].update({
            "status": "processing",
            "progress": 10,
            "message": "开始下载视频..."
        })

        # 下载音频
        audio_path = await video_downloader.download_audio_only(url)

        # 检查下载是否成功
        if not audio_path:
            raise Exception("视频下载失败，无法进行语音识别")

        tasks[task_id].update({
            "progress": 50,
            "message": "下载完成，开始语音识别..."
        })

        # ASR识别
        utterances = await asr_engine.recognize(audio_path)

        tasks[task_id].update({
            "progress": 90,
            "message": "识别完成，格式化输出..."
        })

        # 格式化输出
        transcript = subtitle_processor.format_transcript(utterances, output_format)

        # 完成
        tasks[task_id].update({
            "status": "completed",
            "progress": 100,
            "message": "处理完成",
            "result": TranscriptData(
                bvid=bvid,
                title=title,
                duration=duration,
                method="asr",
                transcript=transcript,
                utterances=utterances
            )
        })

        logger.info(f"Task {task_id} completed successfully")

    except Exception as e:
        logger.error(f"Task {task_id} failed: {str(e)}", exc_info=True)
        tasks[task_id].update({
            "status": "failed",
            "progress": 0,
            "message": f"处理失败: {str(e)}"
        })
