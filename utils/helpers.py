import os import asyncio import logging from pyrogram.types import Message import yt_dlp from config import Config

Setup download directory

download_path = Config.DOWNLOAD_PATH if hasattr(Config, 'DOWNLOAD_PATH') else "downloads" os.makedirs(download_path, exist_ok=True)

COOKIES_FILE = "youtube_cookies.txt"

async def download_media(message: Message, premium: bool): url = message.text.strip().split('?')[0]  # Clean query strings status_msg = await message.reply_text("📥 Starting download...")

progress_data = {"last_percent": 0}

def progress_hook(d):
    if d["status"] == "downloading":
        percent = d.get("_percent_str", "").strip()
        try:
            percent_value = int(float(percent.strip('%')))
            if percent_value - progress_data["last_percent"] >= 2:
                progress_data["last_percent"] = percent_value
                asyncio.run_coroutine_threadsafe(
                    status_msg.edit_text(f"📥 Downloading... {percent}"),
                    asyncio.get_event_loop()
                )
        except:
            pass
    elif d["status"] == "finished":
        asyncio.run_coroutine_threadsafe(
            status_msg.edit_text("✅ Download finished. Uploading..."),
            asyncio.get_event_loop()
        )

# Determine if URL is Instagram
is_instagram = "instagram.com" in url.lower()

opts = {
    "format": "best",
    "outtmpl": os.path.join(download_path, "%(id)s.%(ext)s"),
    "noplaylist": True,
    "quiet": True,
    "geo_bypass": True,
    "nocheckcertificate": True,
    "progress_hooks": [progress_hook],
}

# Include cookies for non-Instagram (e.g., YouTube age-restricted)
if os.path.exists(COOKIES_FILE) and not is_instagram:
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

    caption = f"Downloaded via {Config.BOT_USERNAME}\n{info.get('title') or ''}"
    await message.reply_video(file_path, caption=caption, quote=True)

    os.remove(file_path)

except Exception as e:
    logging.exception("Download failed")
    await message.reply_text(f"❌ Download failed.\n<b>Error:</b> {str(e)}", quote=True)

