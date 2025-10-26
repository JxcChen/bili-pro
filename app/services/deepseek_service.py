"""
DeepSeek AI 总结服务
"""
import logging
from typing import List, Dict
from openai import OpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)


class DeepSeekService:
    """DeepSeek AI 服务类"""

    def __init__(self):
        """初始化 DeepSeek 客户端"""
        self.client = OpenAI(
            api_key=settings.DEEPSEEK_API_KEY,
            base_url=settings.DEEPSEEK_API_URL
        )
        self.model = "deepseek-chat"  # DeepSeek 模型名称

    async def summarize_transcript(self, transcript: str, style: str = "brief") -> Dict[str, any]:
        """
        总结视频逐字稿

        Args:
            transcript: 逐字稿文本
            style: 总结风格 (brief/detailed/academic)

        Returns:
            包含 summary 和 key_points 的字典
        """
        try:
            logger.info(f"Starting DeepSeek summarization, style: {style}, text length: {len(transcript)}")

            # 构建提示词
            system_prompt = self._build_system_prompt(style)
            user_prompt = f"以下是我视频逐字稿,请你总结成一个笔记形式,md 格式输出,一定要突出重点,去掉一些无意义的口语.:\n\n{transcript}"

            # 调用 DeepSeek API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=4000,
                stream=False
            )

            # 提取响应
            summary_text = response.choices[0].message.content.strip()

            # 解析关键要点（从 markdown 中提取）
            key_points = self._extract_key_points(summary_text)

            logger.info(f"DeepSeek summarization completed, summary length: {len(summary_text)}")

            return {
                "summary": summary_text,
                "key_points": key_points
            }

        except Exception as e:
            logger.error(f"DeepSeek API error: {str(e)}", exc_info=True)
            raise Exception(f"DeepSeek 总结失败: {str(e)}")

    def _build_system_prompt(self, style: str) -> str:
        """
        根据风格构建系统提示词
        """
        base_prompt = """你是一个专业的视频内容总结助手。你的任务是将视频逐字稿整理成结构化的笔记。

要求：
1. 使用 Markdown 格式输出
2. 突出重点内容，使用加粗、列表等格式
3. 去掉无意义的口语、语气词（如"嗯"、"啊"、"那个"等）
4. 保持内容的逻辑性和连贯性
5. 提取核心观点和关键信息"""

        style_additions = {
            "brief": "\n6. 简洁为主，突出核心要点\n7. 每个部分控制在3-5句话",
            "detailed": "\n6. 详细展开每个要点\n7. 保留具体案例和数据\n8. 提供完整的上下文",
            "academic": "\n6. 使用学术化的语言\n7. 结构严谨，逻辑清晰\n8. 提供论点、论据和结论"
        }

        return base_prompt + style_additions.get(style, style_additions["brief"])

    def _extract_key_points(self, markdown_text: str) -> List[str]:
        """
        从 Markdown 文本中提取关键要点
        提取所有二级标题和重要列表项
        """
        key_points = []
        lines = markdown_text.split('\n')

        for line in lines:
            line = line.strip()
            # 提取二级标题
            if line.startswith('## ') and not line.startswith('###'):
                point = line.replace('## ', '').strip()
                if point:
                    key_points.append(point)
            # 提取加粗的列表项
            elif line.startswith('- **') or line.startswith('* **'):
                # 提取加粗内容
                import re
                match = re.search(r'\*\*(.*?)\*\*', line)
                if match:
                    point = match.group(1).strip()
                    if point and point not in key_points:
                        key_points.append(point)

        # 如果没有提取到要点，返回前3个非空行
        if not key_points:
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#') and len(key_points) < 5:
                    if len(line) > 10:  # 过滤太短的行
                        key_points.append(line[:100])  # 限制长度

        return key_points[:10]  # 最多返回10个要点
