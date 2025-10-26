"""
B站API封装模块
"""
import aiohttp
import re
import logging
from typing import Optional, Dict, List
from app.core.config import settings

logger = logging.getLogger(__name__)


class BilibiliAPI:
    """B站API调用类"""

    def __init__(self):
        self.base_url = settings.BILIBILI_API_BASE
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://www.bilibili.com"
        }
        if settings.BILIBILI_COOKIE:
            self.headers["Cookie"] = settings.BILIBILI_COOKIE

        # 创建SSL context（禁用验证）
        import ssl
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    def _get_connector(self):
        """获取配置好的连接器"""
        return aiohttp.TCPConnector(ssl=self.ssl_context)

    def extract_bvid(self, url: str) -> Optional[str]:
        """
        从URL中提取BV号
        支持格式:
        - https://www.bilibili.com/video/BV1xx411c7XZ
        - https://b23.tv/xxxxx (短链接)
        - BV1xx411c7XZ (直接输入BV号)
        """
        # 直接匹配BV号
        bv_pattern = r'(BV[a-zA-Z0-9]+)'
        match = re.search(bv_pattern, url)
        if match:
            return match.group(1)

        # 短链接需要先解析
        if 'b23.tv' in url:
            # TODO: 实现短链接解析
            logger.warning("Short URL not fully implemented yet")
            return None

        return None

    async def get_video_info(self, bvid: str) -> Optional[Dict]:
        """
        获取视频基本信息
        API: https://api.bilibili.com/x/web-interface/view?bvid={bvid}
        """
        try:
            url = f"{self.base_url}/x/web-interface/view"
            params = {"bvid": bvid}

            connector = self._get_connector()

            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, params=params, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("code") == 0:
                            video_data = data.get("data", {})
                            return {
                                "bvid": bvid,
                                "title": video_data.get("title"),
                                "duration": video_data.get("duration"),
                                "cid": video_data.get("cid"),
                                "aid": video_data.get("aid"),
                                "owner": video_data.get("owner", {}).get("name"),
                                "desc": video_data.get("desc"),
                            }
                        else:
                            logger.error(f"API error: {data.get('message')}")
                            return None
                    else:
                        logger.error(f"HTTP error: {response.status}")
                        return None

        except Exception as e:
            logger.error(f"Error getting video info: {str(e)}", exc_info=True)
            return None

    async def get_subtitle(self, bvid: str, cid: int) -> Optional[List[Dict]]:
        """
        获取CC字幕
        API: https://api.bilibili.com/x/player/v2?bvid={bvid}&cid={cid}
        """
        try:
            url = f"{self.base_url}/x/player/v2"
            params = {"bvid": bvid, "cid": cid}

            connector = self._get_connector()

            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, params=params, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("code") == 0:
                            subtitle_data = data.get("data", {}).get("subtitle", {})
                            subtitles = subtitle_data.get("subtitles", [])

                            if subtitles:
                                # 获取第一个字幕（通常是中文）
                                subtitle_url = subtitles[0].get("subtitle_url")
                                if subtitle_url:
                                    # 下载字幕JSON
                                    if not subtitle_url.startswith("http"):
                                        subtitle_url = "https:" + subtitle_url

                                    return await self._download_subtitle(subtitle_url)

            return None

        except Exception as e:
            logger.error(f"Error getting subtitle: {str(e)}", exc_info=True)
            return None

    async def get_ai_subtitle(self, bvid: str, cid: int) -> Optional[List[Dict]]:
        """
        获取AI生成的字幕
        需要先检查是否有AI字幕，然后下载
        """
        try:
            # 先尝试从player接口获取AI字幕信息
            url = f"{self.base_url}/x/player/v2"
            params = {"bvid": bvid, "cid": cid}

            connector = self._get_connector()

            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, params=params, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("code") == 0:
                            # 检查是否有AI字幕标记
                            subtitle_data = data.get("data", {}).get("subtitle", {})
                            ai_subtitle = subtitle_data.get("ai_subtitle")

                            if ai_subtitle:
                                subtitle_url = ai_subtitle.get("subtitle_url")
                                if subtitle_url:
                                    if not subtitle_url.startswith("http"):
                                        subtitle_url = "https:" + subtitle_url
                                    return await self._download_subtitle(subtitle_url)

            return None

        except Exception as e:
            logger.error(f"Error getting AI subtitle: {str(e)}", exc_info=True)
            return None

    async def _download_subtitle(self, url: str) -> Optional[List[Dict]]:
        """
        下载字幕JSON文件
        """
        try:
            connector = self._get_connector()

            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(url, headers=self.headers) as response:
                    if response.status == 200:
                        subtitle_data = await response.json()
                        return subtitle_data.get("body", [])

            return None

        except Exception as e:
            logger.error(f"Error downloading subtitle: {str(e)}", exc_info=True)
            return None
