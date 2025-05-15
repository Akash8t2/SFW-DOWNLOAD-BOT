import os
import asyncio
import logging
from pyrogram.types import Message
import yt_dlp
from config import Config

# Setup download directory
download_path = getattr(Config, 'DOWNLOAD_PATH', 'downloads')
os.makedirs(download_path, exist_ok=True)

COOKIES_FILE = "youtube_cookies.txt"

async def download_media(message: Message, premium: bool):
    url = message.text.strip().split('?')[0]  # Clean URL
    status_msg = await message.reply_text("📥 Starting download...")

    # Progress tracking
    progress_data = {"last_percent": 0}

    def progress_hook(d):
        if d.get("status") == "downloading":
            percent_str = d.get("_percent_str", "").strip()
            try:
                percent_val = int(float(percent_str.strip('%')))
                if percent_val - progress_data["last_percent"] >= 2:
                    progress_data["last_percent"] = percent_val
                    asyncio.run_coroutine_threadsafe(
                        status_msg.edit_text(f"📥 Downloading... {percent_str}"),
                        asyncio.get_event_loop()
                    )
            except Exception:
                pass
        elif d.get("status") == "finished":
            asyncio.run_coroutine_threadsafe(
                status_msg.edit_text("✅ Download finished. Uploading..."),
                asyncio.get_event_loop()
            )

    is_instagram = "instagram.com" in url.lower()

    # yt-dlp options
    opts = {
        "format": "best",
        "outtmpl": os.path.join(download_path, "%(id)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "geo_bypass": True,
        "nocheckcertificate": True,
        "progress_hooks": [progress_hook],
    }

    # Use cookies only for non-Instagram
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

        # Premium size check
        if not premium and size_mb > Config.MAX_VIDEO_SIZE_MB:
            await message.reply_text(
                f"❌ File too large ({size_mb:.2f} MB). Only premium users can download videos over {Config.MAX_VIDEO_SIZE_MB} MB.",
                quote=True
            )
            os.remove(file_path)
            return

        # Send video
        caption = f"Downloaded via @{Config.BOT_USERNAME}\n{info.get('title') or ''}"
        await message.reply_video(file_path, caption=caption, quote=True)

        os.remove(file_path)

    except Exception as e:
        logging.exception("Download failed")
        await message.reply_text(
            f"❌ Download failed.\n<b>Error:</b> {e}", quote=True
        )
