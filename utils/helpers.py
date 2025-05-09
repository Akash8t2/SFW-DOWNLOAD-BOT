import os
import asyncio
from yt_dlp import YoutubeDL
from pyrogram.types import Message
from config import Config
import logging

logger = logging.getLogger(__name__)
DOWNLOAD_PATH = "downloads"
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

async def download_media(message: Message, reply_to=False):
    url = message.text.strip()
    ydl_opts = {
        'format': 'best',
        'outtmpl': os.path.join(DOWNLOAD_PATH, '%(id)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
    }

    try:
        loop = asyncio.get_event_loop()
        file_path = await loop.run_in_executor(None, _sync_download, url, ydl_opts)
        
        await _send_video(message, file_path, reply_to)
        
    except Exception as e:
        logger.error(f"Download failed: {str(e)}")
        await message.reply_text("❌ डाउनलोड असफल! लिंक चेक करें")

def _sync_download(url, ydl_opts):
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

async def _send_video(message: Message, file_path: str, reply_to: bool):
    if os.path.exists(file_path):
        await message.reply_video(
            video=file_path,
            caption=f"Downloaded via @{Config.BOT_USERNAME}",
            reply_to_message_id=message.id if reply_to else None
        )
        os.remove(file_path)
    else:
        await message.reply_text("⚠️ वीडियो नहीं मिला")
