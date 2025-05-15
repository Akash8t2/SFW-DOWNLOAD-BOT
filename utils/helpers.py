import os
import asyncio
import logging
from pyrogram import Client, enums
from pyrogram.types import Message
import yt_dlp
from config import Config

# Initialize download directory
download_path = getattr(Config, 'DOWNLOAD_PATH', 'downloads')
os.makedirs(download_path, exist_ok=True)

COOKIES_FILE = "youtube_cookies.txt"

async def download_media(client: Client, message: Message, premium: bool):
    url = message.text.strip().split('?')[0]
    status_msg = await message.reply_text("📥 Starting download...", parse_mode=enums.ParseMode.MARKDOWN)
    file_path = None

    loop = asyncio.get_running_loop()
    progress_data = {"last_percent": 0}

    # Enhanced Progress Hook for yt-dlp 2023.11.16
    def progress_hook(d):
        if d.get('status') == 'downloading':
            percent = d.get('_percent_str', '0%').strip()
            try:
                current = float(percent.replace('%', ''))
                if current - progress_data["last_percent"] >= 2:
                    progress_data["last_percent"] = current
                    asyncio.run_coroutine_threadsafe(
                        status_msg.edit_text(f"📥 Downloading... {percent}"),
                        loop
                    )
            except Exception as e:
                logging.error(f"Progress Error: {e}", exc_info=True)

    try:
        # Metadata extraction with yt-dlp 2023.11.16
        ydl_opts = {
            'format': 'best',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'cookiefile': COOKIES_FILE if os.path.exists(COOKIES_FILE) else None,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=False))

        # Size validation (PyMongo 4.5 compatible)
        max_size = Config.MAX_VIDEO_SIZE_MB * 1024 * 1024
        filesize = next((
            f['filesize'] for f in reversed(info['formats']) 
            if f.get('filesize') and (f['filesize'] <= max_size or premium)
        ), None)

        if not filesize and not premium:
            await status_msg.edit_text(f"❌ File exceeds {Config.MAX_VIDEO_SIZE_MB}MB limit")
            return

        # Download process
        ydl_opts.update({
            'outtmpl': os.path.join(download_path, f"%(id)s.%(ext)s"),
            'progress_hooks': [progress_hook],
        })

        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([url]))
        
        # File path resolution
        file_path = os.path.join(download_path, f"{info['id']}.{info['ext']}")

        # Upload with Pyrogram 2.0.106 features
        await status_msg.edit_text("✅ Uploading...")
        await message.reply_video(
            video=file_path,
            caption=f"Downloaded via @{Config.BOT_USERNAME}\n{info.get('title', '')}",
            parse_mode=enums.ParseMode.MARKDOWN,
            progress=client.progress(
                status_msg, 
                "📤 Uploading... {0}%", 
                update_delay=2
            )
        )

    except yt_dlp.utils.DownloadError as e:
        await message.reply_text(f"❌ Download failed: {str(e)}", quote=True)
    except Exception as e:
        logging.error(f"Critical Error: {str(e)}", exc_info=True)
        await message.reply_text("❌ Processing failed due to internal error", quote=True)
    finally:
        # Cleanup with proper async handling
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
        await status_msg.delete()
