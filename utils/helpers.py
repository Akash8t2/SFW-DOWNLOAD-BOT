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
    url = message.text.strip().split('?')[0]
    status_msg = await message.reply_text("📥 Starting download...")
    file_path = None  # Track downloaded file path

    loop = asyncio.get_running_loop()
    progress_data = {"last_percent": 0}

    # Fixed Progress Hook with Async Handling
    def progress_hook(d):
        if d.get("status") == "downloading":
            percent_str = d.get("_percent_str", "0%").strip()
            try:
                current_percent = float(percent_str.replace('%',''))
                if current_percent - progress_data["last_percent"] >= 2:
                    progress_data["last_percent"] = current_percent
                    # Proper Coroutine Scheduling
                    asyncio.run_coroutine_threadsafe(
                        status_msg.edit_text(f"📥 Downloading... {percent_str}"), 
                        loop
                    )
            except Exception as e:
                logging.error(f"Progress Error: {str(e)}", exc_info=True)

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

        # Metadata Extraction
        with yt_dlp.YoutubeDL(opts_info) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
        
        # Size Estimation Logic
        filesize = (
            info.get('filesize') or 
            info.get('filesize_approx') or 
            next(
                (f['filesize'] for f in reversed(info.get('formats', [])) if f.get('filesize')),
                None
            )
        )

        # Pre-Download Size Check
        if filesize and (size_mb := filesize / (1024 ** 2)) > Config.MAX_VIDEO_SIZE_MB and not premium:
            await status_msg.edit_text(
                f"❌ Video too large ({size_mb:.1f}MB). Premium required for >{Config.MAX_VIDEO_SIZE_MB}MB."
            )
            return

        # Step 2: Actual Download
        opts_download = {
            **opts_info,
            "outtmpl": os.path.join(download_path, "%(id)s.%(ext)s"),
            "progress_hooks": [progress_hook],
        }

        def run_download():
            with yt_dlp.YoutubeDL(opts_download) as ydl:
                ydl.download([url])

        await loop.run_in_executor(None, run_download)
        
        # File Path Handling
        file_ext = info.get('ext') or 'mp4'
        file_path = os.path.join(download_path, f"{info['id']}.{file_ext}")

        # Post-Download Size Verification
        if (actual_size := os.path.getsize(file_path) / (1024 ** 2)) > Config.MAX_VIDEO_SIZE_MB and not premium:
            raise ValueError(f"File size {actual_size:.1f}MB exceeds limit")

        # Step 3: Upload with Progress
        await status_msg.edit_text("✅ Uploading...")
        await message.reply_video(
            file_path,
            caption=f"Downloaded via @{Config.BOT_USERNAME}\n{info.get('title', '')}",
            quote=True,
            progress=lambda current, total: loop.create_task(
                status_msg.edit_text(f"📤 Uploading... {current * 100 / total:.1f}%")
            )
        )

    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}", quote=True)
        logging.error(f"Download Failure: {str(e)}", exc_info=True)
    finally:
        # Guaranteed Cleanup
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        await status_msg.delete()
