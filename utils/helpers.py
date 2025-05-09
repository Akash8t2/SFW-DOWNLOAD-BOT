import os
import asyncio
from yt_dlp import YoutubeDL
from config import Config
import logging

logger = logging.getLogger(__name__)

class Downloader:
    def __init__(self):
        self.download_path = "downloads"
        os.makedirs(self.download_path, exist_ok=True)

    async def download_media(self, url: str) -> str:
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
            'quiet': False,
            'ignoreerrors': False,
            'no_warnings': False,
            'extractor_args': {
                'instagram': {
                    'skip_auth': True,
                    'format': 'best',
                }
            },
            'max_filesize': Config.MAX_FILE_SIZE_MB * 10**6,
            'logger': logger
        }

        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._sync_download, url, ydl_opts)
        except Exception as e:
            logger.error(f"Download Error: {traceback.format_exc()}")
            raise Exception(f"Download Failed: {str(e)}")

    def _sync_download(self, url: str, opts: dict) -> str:
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                raise Exception("No video info found")
            return ydl.prepare_filename(info)
