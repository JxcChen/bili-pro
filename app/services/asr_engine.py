"""
ASR语音识别引擎模块
"""
import logging
from pathlib import Path
from typing import Optional, List, Dict
from app.core.config import settings
from app.api.models import Utterance

logger = logging.getLogger(__name__)

# 检查 ASR 引擎是否可用
try:
    from bcut_asr import BcutASR
    BCUT_AVAILABLE = True
except ImportError:
    BCUT_AVAILABLE = False
    logger.warning("bcut-asr not installed. ASR functionality will be limited.")

try:
    from faster_whisper import WhisperModel
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logger.warning("faster-whisper not installed. Whisper fallback not available.")


class ASREngine:
    """ASR识别引擎类"""

    def __init__(self):
        self.provider = settings.ASR_PROVIDER

    async def recognize(self, audio_path: str) -> List[Utterance]:
        """
        语音识别主接口
        根据配置选择必剪ASR或Whisper
        """
        try:
            if self.provider == "bcut":
                return await self.recognize_with_bcut(audio_path)
            elif self.provider == "whisper":
                return await self.recognize_with_whisper(audio_path)
            else:
                logger.warning(f"Unknown ASR provider: {self.provider}, using bcut")
                return await self.recognize_with_bcut(audio_path)

        except Exception as e:
            logger.error(f"ASR recognition failed: {str(e)}", exc_info=True)
            # 尝试备选方案
            if self.provider == "bcut":
                logger.info("Trying fallback to Whisper")
                return await self.recognize_with_whisper(audio_path)
            else:
                return []

    async def recognize_with_bcut(self, audio_path: str) -> List[Utterance]:
        """
        使用必剪ASR识别
        文档: https://github.com/SocialSisterYi/bcut-asr
        """
        if not BCUT_AVAILABLE:
            raise Exception("bcut-asr未安装，请运行: pip install bcut-asr")

        try:
            logger.info(f"Starting bcut ASR recognition: {audio_path}")

            # 导入bcut_asr库
            from bcut_asr import BcutASR

            # 初始化
            asr = BcutASR()

            # 识别
            result = await asr.recognize(audio_path)

            # 解析结果
            utterances = []
            if result and "utterances" in result:
                for item in result["utterances"]:
                    utterance = Utterance(
                        text=item.get("text", "").strip(),
                        start=float(item.get("start_time", 0)),
                        end=float(item.get("end_time", 0))
                    )
                    if utterance.text:
                        utterances.append(utterance)

            logger.info(f"Bcut ASR completed, got {len(utterances)} utterances")
            return utterances

        except ImportError:
            logger.error("bcut-asr library not installed, please run: pip install bcut-asr")
            raise
        except Exception as e:
            logger.error(f"Bcut ASR error: {str(e)}", exc_info=True)
            raise

    async def recognize_with_whisper(self, audio_path: str) -> List[Utterance]:
        """
        使用Faster-Whisper识别（备选方案）
        文档: https://github.com/guillaumekln/faster-whisper
        """
        if not WHISPER_AVAILABLE:
            raise Exception("faster-whisper未安装，请运行: pip install faster-whisper")

        try:
            logger.info(f"Starting Whisper recognition: {audio_path}")

            # 导入faster_whisper库
            from faster_whisper import WhisperModel

            # 初始化模型
            model_size = settings.WHISPER_MODEL
            model = WhisperModel(model_size, device="cpu", compute_type="int8")

            # 识别
            segments, info = model.transcribe(
                audio_path,
                language="zh",  # 中文
                beam_size=5,
                vad_filter=True,  # 使用VAD过滤
            )

            # 解析结果
            utterances = []
            for segment in segments:
                utterance = Utterance(
                    text=segment.text.strip(),
                    start=float(segment.start),
                    end=float(segment.end)
                )
                if utterance.text:
                    utterances.append(utterance)

            logger.info(f"Whisper completed, got {len(utterances)} utterances")
            return utterances

        except ImportError:
            logger.error("faster-whisper library not installed, please run: pip install faster-whisper")
            raise
        except Exception as e:
            logger.error(f"Whisper error: {str(e)}", exc_info=True)
            raise
