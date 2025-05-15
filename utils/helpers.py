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
    file_path = None  # Track downloaded file path

    loop = asyncio.get_running_loop()
    progress_data = {"last_percent": 0}

    # Improved progress hook with better error handling
    def progress_hook(d):
        if d.get("status") == "downloading":
            percent_str = d.get("_percent_str", "0%").strip()
            try:
                current_percent = float(percent_str.replace('%',''))
                if current_percent - progress_data["last_percent"] >= 2:
                    progress_data["last_percent"] = current_percent
                    coro = status_msg.edit_text(f"📥 Downloading... {percent_str}")
                    asyncio.run_coroutine_threadsafe(coro, loop)
            except Exception as e:
                logging.error(f"Progress hook error: {e}")

    try:
        # Step 1: Extract metadata first for size check
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

        # Extract metadata without downloading
        with yt_dlp.YoutubeDL(opts_info) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))
        
        # Estimate file size from metadata
        filesize = None
        if info.get('filesize'):
            filesize = info['filesize']
        elif info.get('filesize_approx'):
            filesize = info['filesize_approx']
        else:
            # Fallback to best format's filesize
            best_format = next(
                (f for f in reversed(info.get('formats', [])) if f.get('filesize')),
                None
            )
            if best_format:
                filesize = best_format.get('filesize')

        # Pre-check size before download
        if filesize:
            size_mb = filesize / (1024 * 1024)
            if not premium and size_mb > Config.MAX_VIDEO_SIZE_MB:
                await status_msg.edit_text(
                    f"❌ Video too large ({size_mb:.2f} MB). "
                    f"Premium required for >{Config.MAX_VIDEO_SIZE_MB} MB."
                )
                return

        # Step 2: Actual download with progress
        opts_download = {
            **opts_info,
            "outtmpl": os.path.join(download_path, "%(id)s.%(ext)s"),
            "progress_hooks": [progress_hook],
        }

        def run_download():
            with yt_dlp.YoutubeDL(opts_download) as ydl:
                return ydl.download([url])

        await loop.run_in_executor(None, run_download)
        
        # Get actual downloaded file path
        file_ext = info.get('ext') or 'mp4'
        file_path = os.path.join(download_path, f"{info['id']}.{file_ext}")

        # Final size check after actual download
        actual_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if not premium and actual_size_mb > Config.MAX_VIDEO_SIZE_MB:
            await message.reply_text(
                f"❌ File too large ({actual_size_mb:.2f} MB). "
                f"Premium required for >{Config.MAX_VIDEO_SIZE_MB} MB.",
                quote=True
            )
            raise ValueError("File size exceeds limit")

        # Step 3: Upload with cleanup
        await status_msg.edit_text("✅ Uploading...")
        caption = f"Downloaded via @{Config.BOT_USERNAME}\n{info.get('title', '')}"
        await message.reply_video(
            file_path,
            caption=caption,
            quote=True,
            progress=lambda d, u: asyncio.run_coroutine_threadsafe(
                status_msg.edit_text(f"📤 Uploading... {d * 100:.1f}%"), 
                loop
            )
        )

    except Exception as e:
        logging.error(f"Error: {str(e)}", exc_info=True)
        await message.reply_text(f"❌ Error: {str(e)}", quote=True)
    finally:
        # Cleanup in all cases
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        await status_msg.delete()
