import os  
import asyncio  
import logging  
from pyrogram.types import Message  
import yt_dlp  
from config import Config  
  
# Ensure download directory exists  
download_path = Config.DOWNLOAD_PATH if hasattr(Config, 'DOWNLOAD_PATH') else "downloads"  
os.makedirs(download_path, exist_ok=True)  
  
# Path to cookies file  
COOKIES_FILE = "youtube_cookies.txt"  # You already added this in your repo  
  
async def download_media(message: Message, premium: bool):  
    url = message.text.strip()  
  
    opts = {  
        "format": "best",  
        "outtmpl": os.path.join(download_path, "%(id)s.%(ext)s"),  
        "noplaylist": True,  
        "quiet": True,  
        "geo_bypass": True,  
    }  
  
    # Add cookies if file exists  
    if os.path.exists(COOKIES_FILE):  
        opts["cookiefile"] = COOKIES_FILE  
  
    loop = asyncio.get_event_loop()  
  
    def run_download():  
        with yt_dlp.YoutubeDL(opts) as ydl:  
            info = ydl.extract_info(url, download=True)  
            file_path = ydl.prepare_filename(info)  
            return info, file_path  
  
    try:  
        info, file_path = await loop.run_in_executor(None, run_download)  
        size_mb = os.path.getsize(file_path) / (1024 * 1024)  
  
        if not premium and size_mb > Config.MAX_VIDEO_SIZE_MB:  
            await message.reply_text(  
                f"❌ File too large ({size_mb:.2f} MB). Only premium users can download videos over {Config.MAX_VIDEO_SIZE_MB} MB.",  
                quote=True  
            )  
            os.remove(file_path)  
            return  
  
        caption = f"Downloaded via {Config.BOT_USERNAME}\n{info.get('title')}"  
  
        if size_mb > Config.MAX_VIDEO_SIZE_MB and premium:  
            await message.reply_text(  
                f"⚠️ File size is {size_mb:.2f} MB, sending link instead:",  
                disable_web_page_preview=True,  
                quote=True  
            )  
            await message.reply_text(info.get('url'), quote=True)  
        else:  
            await message.reply_video(file_path, caption=caption, quote=True)  
  
        os.remove(file_path)  
  
    except Exception:  
        logging.exception("Download failed")  
        await message.reply_text("❌ Download failed. Try again later.", quote=True)```
