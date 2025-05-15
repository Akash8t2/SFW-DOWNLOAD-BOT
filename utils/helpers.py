import os
import re
import asyncio
import logging
import requests
from pyrogram.types import Message
import yt_dlp
from config import Config

# Setup download path
download_path = getattr(Config, 'DOWNLOAD_PATH', 'downloads')
os.makedirs(download_path, exist_ok=True)

COOKIES_FILE = "youtube_cookies.txt"

# === Terabox Helpers ===
def is_terabox_link(url: str):
    return "terabox.com" in url or "4funbox.com" in url

def get_terabox_direct_link(url: str):
    try:
        api_url = f"https://terabox.cosybrandoool.workers.dev/?url={url}"
        response = requests.get(api_url)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        logging.error(f"Terabox API call failed: {e}")
    return None

# === Main Handler ===
async def download_media(message: Message, premium: bool):
    url = message.text.strip()

    # === Terabox handling ===
    if is_terabox_link(url):
        data = get_terabox_direct_link(url)
        if data:
            caption = (
                f"**{data['file_name']}**\n"
                f"**Size:** `{data['size']}`\n\n"
                f"[Direct Download Link]({data['direct_link']})"
            )
            await message.reply_photo(
                photo=data["thumb"],
                caption=caption,
                parse_mode="markdown",
                quote=True
            )
        else:
            await message.reply_text("❌ Failed to extract Terabox link.", quote=True)
        return

    # === Other sources via yt_dlp ===
    opts = {
        "format": "best",
        "outtmpl": os.path.join(download_path, "%(id)s.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "geo_bypass": True,
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
        await message.reply_text("❌ Download failed. Try again later.", quote=True)
