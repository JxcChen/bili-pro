"""
字幕处理模块
"""
import logging
from typing import List, Dict
from datetime import timedelta
from app.api.models import Utterance

logger = logging.getLogger(__name__)


class SubtitleProcessor:
    """字幕处理类"""

    def parse_bilibili_subtitle(self, subtitle_data: List[Dict]) -> List[Utterance]:
        """
        解析B站字幕JSON格式
        输入格式: [{"from": 0.0, "to": 3.5, "content": "这是第一句话"}, ...]
        """
        utterances = []

        try:
            for item in subtitle_data:
                utterance = Utterance(
                    text=item.get("content", "").strip(),
                    start=float(item.get("from", 0)),
                    end=float(item.get("to", 0))
                )
                if utterance.text:  # 只添加非空文本
                    utterances.append(utterance)

            logger.info(f"Parsed {len(utterances)} utterances from subtitle")
            return utterances

        except Exception as e:
            logger.error(f"Error parsing subtitle: {str(e)}", exc_info=True)
            return []

    def format_transcript(self, utterances: List[Utterance], format_type: str = "txt") -> str:
        """
        格式化输出
        支持格式: txt, srt, json
        """
        if format_type == "txt":
            return self._to_plain_text(utterances)
        elif format_type == "srt":
            return self._to_srt(utterances)
        elif format_type == "json":
            return self._to_json(utterances)
        else:
            return self._to_plain_text(utterances)

    def _to_plain_text(self, utterances: List[Utterance]) -> str:
        """
        转换为纯文本
        """
        return " ".join([u.text for u in utterances])

    def _to_plain_text_with_timestamps(self, utterances: List[Utterance]) -> str:
        """
        转换为带时间戳的文本
        格式: [00:00:00] 这是第一句话
        """
        lines = []
        for u in utterances:
            timestamp = self._format_timestamp(u.start)
            lines.append(f"[{timestamp}] {u.text}")

        return "\n".join(lines)

    def _to_srt(self, utterances: List[Utterance]) -> str:
        """
        转换为SRT字幕格式
        格式:
        1
        00:00:00,000 --> 00:00:03,500
        这是第一句话
        """
        lines = []

        for i, u in enumerate(utterances, start=1):
            start_time = self._format_srt_timestamp(u.start)
            end_time = self._format_srt_timestamp(u.end)

            lines.append(str(i))
            lines.append(f"{start_time} --> {end_time}")
            lines.append(u.text)
            lines.append("")  # 空行分隔

        return "\n".join(lines)

    def _to_json(self, utterances: List[Utterance]) -> str:
        """
        转换为JSON格式
        """
        import json
        return json.dumps(
            [u.dict() for u in utterances],
            ensure_ascii=False,
            indent=2
        )

    def _format_timestamp(self, seconds: float) -> str:
        """
        格式化时间戳
        输出格式: 00:00:00
        """
        td = timedelta(seconds=seconds)
        hours = int(td.total_seconds() // 3600)
        minutes = int((td.total_seconds() % 3600) // 60)
        secs = int(td.total_seconds() % 60)

        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def _format_srt_timestamp(self, seconds: float) -> str:
        """
        格式化SRT时间戳
        输出格式: 00:00:00,000
        """
        td = timedelta(seconds=seconds)
        hours = int(td.total_seconds() // 3600)
        minutes = int((td.total_seconds() % 3600) // 60)
        secs = int(td.total_seconds() % 60)
        millisecs = int((seconds - int(seconds)) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

    def parse_asr_result(self, asr_data: Dict) -> List[Utterance]:
        """
        解析ASR识别结果
        支持必剪ASR和Whisper格式
        """
        utterances = []

        try:
            # 必剪ASR格式
            if "utterances" in asr_data:
                for item in asr_data["utterances"]:
                    utterance = Utterance(
                        text=item.get("text", "").strip(),
                        start=float(item.get("start_time", 0)),
                        end=float(item.get("end_time", 0))
                    )
                    if utterance.text:
                        utterances.append(utterance)

            # Whisper格式
            elif "segments" in asr_data:
                for segment in asr_data["segments"]:
                    utterance = Utterance(
                        text=segment.get("text", "").strip(),
                        start=float(segment.get("start", 0)),
                        end=float(segment.get("end", 0))
                    )
                    if utterance.text:
                        utterances.append(utterance)

            logger.info(f"Parsed {len(utterances)} utterances from ASR result")
            return utterances

        except Exception as e:
            logger.error(f"Error parsing ASR result: {str(e)}", exc_info=True)
            return []
