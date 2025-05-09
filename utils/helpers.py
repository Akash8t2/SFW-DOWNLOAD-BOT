import os
import asyncio
import yt_dlp
from pyrogram.types import Message
from instaloader import Instaloader, Post, Profile
from config import Config
import logging
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

DOWNLOAD_PATH = "downloads"
os.makedirs(DOWNLOAD_PATH, exist_ok=True)

class DownloadError(Exception):
    """Custom exception for download failures"""
    pass

class InstagramDownloader:
    def __init__(self):
        self.loader = Instaloader(
            download_pictures=False,
            download_videos=True,
            save_metadata=False,
            download_geotags=False,
            compress_json=False
        )
        # Load Instagram session if available
        if Config.INSTAGRAM_SESSION:
            self.loader.load_session_from_file(Config.INSTAGRAM_USERNAME, Config.INSTAGRAM_SESSION)

    async def _download_post(self, url: str) -> str:
        """Download Instagram post/reel"""
        try:
            shortcode = self._extract_shortcode(url)
            post = Post.from_shortcode(self.loader.context, shortcode)
            self.loader.download_post(post, target=DOWNLOAD_PATH)
            return self._find_downloaded_file(post)
        except Exception as e:
            raise DownloadError(f"Instagram Error: {str(e)}")

    def _extract_shortcode(self, url: str) -> str:
        """Extract shortcode from Instagram URL"""
        pattern = r"(?:reel|p|tv)/([A-Za-z0-9-_]+)"
        match = re.search(pattern, url)
        if not match:
            raise DownloadError("Invalid Instagram URL")
        return match.group(1)

    def _find_downloaded_file(self, post: Post) -> str:
        """Find the downloaded video file"""
        for file in os.listdir(DOWNLOAD_PATH):
            if file.startswith(f"{post.owner_username}_{post.shortcode}"):
                if file.endswith(('.mp4', '.mkv', '.webm')):
                    return os.path.join(DOWNLOAD_PATH, file)
        raise DownloadError("Video file not found after download")

class YTDLPDownloader:
    @staticmethod
    async def download(url: str) -> str:
        """Download using yt-dlp (YouTube, TikTok, etc.)"""
        opts = {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "outtmpl": os.path.join(DOWNLOAD_PATH, "%(id)s.%(ext)s"),
            "noplaylist": True,
            "quiet": True,
            "merge_output_format": "mp4",
            "max_filesize": Config.MAX_VIDEO_SIZE_MB * 1024 * 1024
        }
        
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return ydl.prepare_filename(info)
        except yt_dlp.utils.DownloadError as e:
            if "File is larger than max-filesize" in str(e):
                raise DownloadError(f"File too large (> {Config.MAX_VIDEO_SIZE_MB}MB)")
            raise DownloadError(f"YT-DLP Error: {str(e)}")

async def download_media(message: Message, platform: str, premium: bool):
    """Main download handler for all platforms"""
    url = message.text.strip()
    file_path = None
    
    try:
        # Platform detection
        if "instagram.com" in url:
            downloader = InstagramDownloader()
            file_path = await downloader._download_post(url)
            max_size = Config.MAX_INSTA_SIZE_MB
        else:
            file_path = await YTDLPDownloader.download(url)
            max_size = Config.MAX_VIDEO_SIZE_MB

        # File size validation
        size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if size_mb > max_size:
            raise DownloadError(f"File size {size_mb:.1f}MB exceeds limit ({max_size}MB)")

        # Prepare caption
        caption = Config.CAPTION_TEMPLATE.format(
            username=message.from_user.username or message.from_user.first_name,
            bot_username=Config.BOT_USERNAME,
            premium_status="Premium ✅" if premium else "Free ⚠️"
        )

        # Send media
        await message.reply_video(
            video=file_path,
            caption=caption,
            duration=(await get_video_duration(file_path)),
            reply_to_message_id=message.id if message.chat.type != "private" else None
        )

    except DownloadError as e:
        await message.reply_text(f"❌ {str(e)}", reply_to_message_id=message.id)
    except Exception as e:
        logging.error(f"Critical Error: {str(e)}", exc_info=True)
        await message.reply_text("🔥 Critical error! Contact admin.", reply_to_message_id=message.id)
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

async def get_video_duration(file_path: str) -> int:
    """Get video duration using FFprobe"""
    cmd = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {file_path}"
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await proc.communicate()
    if stderr:
        raise DownloadError("Failed to get video duration")
    return int(float(stdout.decode().strip()))
