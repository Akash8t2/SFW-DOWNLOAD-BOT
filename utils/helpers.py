import os  
import asyncio  
import logging  
from pyrogram.types import Message  
import yt_dlp  
from config import Config  
  
download_path = Config.DOWNLOAD_PATH if hasattr(Config, 'DOWNLOAD_PATH') else "downloads"  
os.makedirs(download_path, exist_ok=True)  
  
COOKIES_FILE = "youtube_cookies.txt"  
  
def progress_bar(percent):
    blocks = int(percent // 10)
    return "▰" * blocks + "▱" * (10 - blocks)

async def download_media(message: Message, premium: bool):  
    url = message.text.strip()  
    status_msg = await message.reply_text("Downloading...\n▱▱▱▱▱▱▱▱▱▱ 0%", quote=True)  
  
    async def progress_hook(d):  
        if d['status'] == 'downloading':  
            percent = d.get('_percent_str', '0.0%').strip().replace('%', '')  
            try:  
                percent = float(percent)  
                bar = progress_bar(percent)  
                await status_msg.edit_text(f"Downloading...\n{bar} {int(percent)}%")  
            except:  
                pass  
        elif d['status'] == 'finished':  
            await status_msg.edit_text("✅ Download complete!\n📤 Uploading... 0%")  
  
    opts = {  
        "format": "best",  
        "outtmpl": os.path.join(download_path, "%(id)s.%(ext)s"),  
        "noplaylist": True,  
        "quiet": True,  
        "geo_bypass": True,  
        "progress_hooks": [progress_hook],  
    }  
  
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
            await status_msg.edit_text(  
                f"❌ File too large ({size_mb:.2f} MB). Only premium users can download videos over {Config.MAX_VIDEO_SIZE_MB} MB."  
            )  
            os.remove(file_path)  
            return  
  
        caption = f"Downloaded via {Config.BOT_USERNAME}\n{info.get('title')}"  
  
        if size_mb > Config.MAX_VIDEO_SIZE_MB and premium:  
            await status_msg.edit_text(  
                f"⚠️ File size is {size_mb:.2f} MB, sending link instead:"  
            )  
            await message.reply_text(info.get('url'), quote=True)  
        else:  
            async def upload_progress(current, total):  
                percent = int(current * 100 / total)  
                bar = progress_bar(percent)  
                await status_msg.edit_text(f"✅ Download complete!\n📤 Uploading... {percent}% {bar}")  
  
            await message.reply_video(  
                video=file_path,  
                caption=caption,  
                quote=True,  
                progress=upload_progress  
            )  
  
        os.remove(file_path)  
  
    except Exception:  
        logging.exception("Download failed")  
        await status_msg.edit_text("❌ Download failed. Try again later.")
