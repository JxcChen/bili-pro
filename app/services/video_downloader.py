"""
视频下载模块
"""
import logging
import asyncio
from pathlib import Path
from typing import Optional
from app.core.config import settings

# Playwright 是可选依赖
try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    PlaywrightTimeoutError = Exception  # 占位符

logger = logging.getLogger(__name__)


class VideoDownloader:
    """视频下载类"""

    def __init__(self):
        self.download_dir = Path(settings.TEMP_DIR)
        self.download_dir.mkdir(parents=True, exist_ok=True)

    async def download_audio_only(self, video_url: str) -> Optional[str]:
        """
        优先下载音频文件
        使用 yt-dlp 直接下载（更可靠）
        """
        try:
            logger.info(f"Starting audio download for: {video_url}")

            # 优先使用 yt-dlp（更可靠）
            audio_path = await self._download_with_ytdlp(video_url)

            if audio_path:
                logger.info(f"Audio downloaded successfully: {audio_path}")
                return audio_path

            # 备选：使用 Playwright 自动化 snapany
            if PLAYWRIGHT_AVAILABLE:
                logger.info("yt-dlp failed, trying snapany...")
                audio_path = await self._download_with_snapany(video_url)
                if audio_path:
                    logger.info(f"Audio downloaded successfully via snapany: {audio_path}")
                    return audio_path

            logger.error("All download methods failed")
            return None

        except Exception as e:
            logger.error(f"Error downloading audio: {str(e)}", exc_info=True)
            return None

    async def _download_with_ytdlp(self, video_url: str) -> Optional[str]:
        """
        使用 yt-dlp 直接下载音频
        这是最可靠的方法，支持 B站
        """
        try:
            import yt_dlp
            import hashlib

            # 生成唯一文件名
            file_hash = hashlib.md5(video_url.encode()).hexdigest()
            output_path = self.download_dir / f"{file_hash}.m4a"

            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': str(output_path),
                'quiet': True,
                'no_warnings': True,
                'extract_audio': True,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'm4a',
                }],
            }

            logger.info(f"Downloading with yt-dlp: {video_url}")

            # yt-dlp 是同步的，需要在线程池中运行
            import asyncio
            loop = asyncio.get_event_loop()

            def download():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([video_url])

            await loop.run_in_executor(None, download)

            if output_path.exists():
                logger.info(f"yt-dlp download successful: {output_path}")
                return str(output_path)
            else:
                logger.error("yt-dlp download failed: file not found")
                return None

        except ImportError:
            logger.warning("yt-dlp not installed, skipping")
            return None
        except Exception as e:
            logger.error(f"yt-dlp download error: {str(e)}", exc_info=True)
            return None

    async def _download_with_snapany(self, video_url: str) -> Optional[str]:
        """
        使用Playwright自动化snapany网站下载
        网站: https://snapany.com/zh/bilibili
        """
        try:
            async with async_playwright() as p:
                # 启动浏览器（无头模式）
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                # 访问snapany
                await page.goto("https://snapany.com/zh/bilibili", timeout=30000)

                # 等待页面加载
                await page.wait_for_load_state("networkidle")

                # 输入B站链接
                input_selector = 'input[type="text"]'  # 需要根据实际页面调整
                await page.fill(input_selector, video_url)

                # 点击下载按钮
                download_button_selector = 'button:has-text("下载")'  # 需要根据实际页面调整
                await page.click(download_button_selector)

                # 等待处理完成（这里需要根据实际情况调整）
                await page.wait_for_selector('.download-link', timeout=120000)

                # 获取下载链接
                download_link = await page.locator('.download-link').get_attribute('href')

                if download_link:
                    # 下载文件
                    download_path = self.download_dir / f"{hash(video_url)}.mp3"

                    # 使用aiohttp下载
                    import aiohttp
                    async with aiohttp.ClientSession() as session:
                        async with session.get(download_link) as response:
                            if response.status == 200:
                                with open(download_path, 'wb') as f:
                                    f.write(await response.read())

                                await browser.close()
                                return str(download_path)

                await browser.close()
                return None

        except PlaywrightTimeoutError:
            logger.error("Playwright timeout while downloading")
            return None
        except Exception as e:
            logger.error(f"Error in snapany download: {str(e)}", exc_info=True)
            return None

    async def _download_with_bilibili_api(self, video_url: str) -> Optional[str]:
        """
        直接使用B站API下载（备选方案）
        需要处理鉴权和防盗链
        """
        # TODO: 实现B站API直接下载
        logger.warning("Direct Bilibili API download not implemented yet")
        return None

    def cleanup_temp_files(self):
        """
        清理临时文件
        """
        try:
            for file in self.download_dir.glob("*"):
                if file.is_file():
                    file.unlink()
            logger.info("Temp files cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {str(e)}")
