import os
import asyncio
from pyrogram.types import Message
import yt_dlp
from config import Config

DOWNLOAD_PATH = "downloads"

async def download_media(message: Message, premium: bool):
    url = message.text.strip()
    opts = {
        "format": "best",
        "outtmpl": os.path.join(DOWNLOAD_PATH, "%(id)s.%(ext)s"),
        "noplaylist": True
    }
    loop = asyncio.get_event_loop()
    def run_download():
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            return info, file_path

    try:
        info, file_path = await loop.run_in_executor(None, run_download)
        size_mb = os.path.getsize(file_path) / (1024 * 1024)
        caption = f"Downloaded via {Config.BOT_USERNAME}\n{info.get('title')}"
        if size_mb > Config.MAX_VIDEO_SIZE_MB:
            await message.reply_text(f"File too large ({size_mb:.2f} MB). Here's the link:", disable_web_page_preview=True)
            await message.reply_text(info.get('url'))
        else:
            await message.reply_video(file_path, caption=caption)
        os.remove(file_path)
    except Exception as e:
        await message.reply_text("❌ Download failed. Try again later.")