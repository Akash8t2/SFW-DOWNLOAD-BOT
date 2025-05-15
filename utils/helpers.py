import os
import asyncio
import logging
from pyrogram import Client
from pyrogram.types import Message
import yt_dlp
from config import Config

# Setup download directory
download_path = getattr(Config, 'DOWNLOAD_PATH', 'downloads')
os.makedirs(download_path, exist_ok=True)

COOKIES_FILE = "youtube_cookies.txt"

async def download_media(client: Client, message: Message, premium: bool):
    url = message.text.strip().split('?')[0]
    status_msg = await message.reply_text("📥 Starting download...")
    file_path = None  # Track downloaded file path

    loop = asyncio.get_running_loop()
    progress_data = {"last_percent": 0}

    # Progress Hook with Thread-Safe Updates
    def progress_hook(d):
        if d.get("status") == "downloading":
            percent_str = d.get("_percent_str", "0%").strip()
            try:
                current_percent = float(percent_str.replace('%',''))
                if current_percent - progress_data["last_percent"] >= 2:
                    progress_data["last_percent"] = current_percent
                    asyncio.run_coroutine_threadsafe(
                        status_msg.edit_text(f"📥 Downloading... {percent_str}"),
                        loop
                    )
            except Exception as e:
                logging.error(f"Progress Error: {e}", exc_info=True)

    try:
        # Step 1: Metadata Extraction
        is_instagram = "instagram.com" in url.lower()
        
        opts_info = {
            "format": "best",
            "noplaylist": True,
            "quiet": True,
            "geo_bypass": True,
            "nocheckcertificate": True,
        }
        if os.path.exists(COOKIES_FILE) and not is_instagram:
            opts_info["cookiefile"] = COOKIES_FILE

        with yt_dlp.YoutubeDL(opts_info) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
        
        # Size Validation
        max_size = Config.MAX_VIDEO_SIZE_MB * 1024 * 1024
        filesize = next((
            f['filesize'] for f in reversed(info.get('formats', []))
            if f.get('filesize') and (f['filesize'] <= max_size or premium)
        ), None)

        if not filesize and not premium:
            await status_msg.edit_text(f"❌ File exceeds {Config.MAX_VIDEO_SIZE_MB}MB limit")
            return

        # Step 2: Actual Download
        opts_download = {
            **opts_info,
            "outtmpl": os.path.join(download_path, "%(id)s.%(ext)s"),
            "progress_hooks": [progress_hook],
        }

        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(opts_download).download([url]))
        
        # File Path Handling
        file_path = os.path.join(download_path, f"{info['id']}.{info.get('ext', 'mp4')}")

        # Step 3: Upload with Progress
        await status_msg.edit_text("✅ Uploading...")
        await message.reply_video(
            file_path,
            caption=f"Downloaded via @{Config.BOT_USERNAME}\n{info.get('title', '')}",
            progress=lambda current, total: asyncio.run_coroutine_threadsafe(
                status_msg.edit_text(f"📤 Uploading... {current * 100 / total:.1f}%"),
                loop
            )
        )

    except yt_dlp.utils.DownloadError as e:
        await message.reply_text(f"❌ Download failed: {str(e)}", quote=True)
    except Exception as e:
        logging.error(f"Critical Error: {str(e)}", exc_info=True)
        await message.reply_text("❌ Processing failed due to internal error", quote=True)
    finally:
        # Guaranteed Cleanup
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        await status_msg.delete()
