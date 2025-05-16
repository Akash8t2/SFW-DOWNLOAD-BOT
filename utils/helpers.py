import os
import asyncio
import logging
import ssl
import certifi
import yt_dlp
from pyrogram import Client
from pyrogram.types import Message
from config import Config

ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=certifi.where())
download_path = getattr(Config, 'DOWNLOAD_PATH', 'downloads')
os.makedirs(download_path, exist_ok=True)

YOUTUBE_COOKIES = "youtube_cookies.txt"
INSTAGRAM_COOKIES = "instagram_cookies.txt"

async def download_media(client: Client, message: Message, premium: bool):
    url = message.text.strip().split("?")[0]
    status_msg = await message.reply_text("📥 Starting download...")
    file_path = None
    loop = asyncio.get_running_loop()
    progress_data = {"last_percent": 0}

    def progress_hook(d):
        if d.get("status") == "downloading":
            percent_str = d.get("_percent_str", "0%").strip()
            try:
                current = float(percent_str.replace('%', ''))
                if current - progress_data["last_percent"] >= 2:
                    progress_data["last_percent"] = current
                    coro = status_msg.edit_text(f"📥 Downloading... {percent_str}")
                    asyncio.run_coroutine_threadsafe(coro, loop)
            except Exception as e:
                logging.error(f"Progress Error: {e}", exc_info=True)

    try:
        is_instagram = "instagram.com" in url.lower()

        # Set cookiefile only if file exists
        cookiefile = None
        if is_instagram and os.path.exists(INSTAGRAM_COOKIES):
            cookiefile = INSTAGRAM_COOKIES
        elif os.path.exists(YOUTUBE_COOKIES):
            cookiefile = YOUTUBE_COOKIES

        opts = {
            "format": "best",
            "noplaylist": True,
            "quiet": True,
            "geo_bypass": True,
            "nocheckcertificate": not is_instagram,
            "ssl_verify": False if is_instagram else True,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/125.0.0.0 Safari/537.36"
                        if is_instagram else None,
            "verbose": False,
        }
        if cookiefile:
            opts["cookiefile"] = cookiefile

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))

        max_size = Config.MAX_VIDEO_SIZE_MB * 1024 * 1024
        if not premium and (info.get("filesize") or 0) > max_size:
            await status_msg.edit_text(f"❌ File exceeds {Config.MAX_VIDEO_SIZE_MB}MB limit.")
            return

        opts["outtmpl"] = os.path.join(download_path, "%(id)s.%(ext)s")
        opts["progress_hooks"] = [progress_hook]

        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(opts).download([url]))

        file_path = os.path.join(download_path, f"{info['id']}.{info.get('ext', 'mp4')}")

        await status_msg.edit_text("✅ Uploading...")

        # Upload without progress callback (saada upload)
        await message.reply_video(
            file_path,
            caption=f"Downloaded via @{Config.BOT_USERNAME}\n{info.get('title', '')}"
        )

    except yt_dlp.utils.DownloadError as e:
        await message.reply_text(f"❌ Download failed: {str(e).split(';')[0]}")
    except Exception as e:
        logging.error(f"Critical Error: {e}", exc_info=True)
        await message.reply_text("❌ Internal error occurred.")
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        await status_msg.delete()
