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
    # Clean URL and strip query parameters
    url = message.text.strip().split('?')[0]
    status_msg = await message.reply_text("📥 Starting download...")

    # Capture the running loop once
    loop = asyncio.get_running_loop()
    progress_data = {"last_percent": 0}

    # This hook will run in yt_dlp's thread, but schedule edits in our loop
    def progress_hook(d):
        status = d.get("status")
        if status == "downloading":
            percent_str = d.get("_percent_str", "").strip()
            try:
                val = int(float(percent_str.strip('%')))
            except Exception:
                return
            # Only update every 2% to avoid flooding
            if val - progress_data["last_percent"] >= 2:
                progress_data["last_percent"] = val
                # schedule the coroutine to edit the message
                coro = status_msg.edit_text(f"📥 Downloading... {percent_str}")
                asyncio.run_coroutine_threadsafe(coro, loop)

        elif status == "finished":
            coro = status_msg.edit_text("✅ Download finished. Uploading...")
            asyncio.run_coroutine_threadsafe(coro, loop)

    # Determine if this is an Instagram URL
    is_instagram = "instagram.com" in url.lower()

    # Build yt-dlp options
    opts = {
        "format": "best",
        "outtmpl": os.path.join(download_path, "%(id)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "geo_bypass": True,
        "nocheckcertificate": True,
        "progress_hooks": [progress_hook],
    }

    # Only use cookies for non-Instagram (e.g. YouTube age-restricted)
    if os.path.exists(COOKIES_FILE) and not is_instagram:
        opts["cookiefile"] = COOKIES_FILE

    # Blocking download in thread
    def run_download():
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            return info, file_path

    try:
        info, file_path = await loop.run_in_executor(None, run_download)
        size_mb = os.path.getsize(file_path) / (1024 * 1024)

        # Enforce premium limit
        if not premium and size_mb > Config.MAX_VIDEO_SIZE_MB:
            await message.reply_text(
                f"❌ File too large ({size_mb:.2f} MB). "
                f"Only premium users can download videos over "
                f"{Config.MAX_VIDEO_SIZE_MB} MB.",
                quote=True
            )
            os.remove(file_path)
            return

        # Finally send the video
        caption = f"Downloaded via @{Config.BOT_USERNAME}\n{info.get('title') or ''}"
        await message.reply_video(file_path, caption=caption, quote=True)

        os.remove(file_path)

    except Exception as e:
        logging.exception("Download failed")
        await message.reply_text(
            f"❌ Download failed.\n<b>Error:</b> {e}", quote=True
        )
