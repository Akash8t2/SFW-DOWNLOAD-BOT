import os
import asyncio
from yt_dlp import YoutubeDL
from pyrogram.types import Message
from config import Config

class Downloader:
    def __init__(self):
        self.download_path = "downloads"
        os.makedirs(self.download_path, exist_ok=True)

    async def download_instagram(self, url: str) -> str:
        ydl_opts = {
            'format': 'best',
            'outtmpl': os.path.join(self.download_path, '%(id)s.%(ext)s'),
            'quiet': True,
            'ignoreerrors': True,
            'extractor_args': {'instagram': {'skip_auth': True}}
        }
        
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._sync_download, url, ydl_opts)
        except Exception as e:
            raise Exception(f"Download Failed: {str(e)}")

    def _sync_download(self, url: str, opts: dict) -> str:
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)
