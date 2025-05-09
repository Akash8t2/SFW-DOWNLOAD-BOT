from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from utils.db import db
from utils.helpers import Downloader
import re
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = Client(
    "SFW_DownloadBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

downloader = Downloader()
INSTA_REGEX = r'(https?://)?(www\.)?instagram\.com/(reel|p|tv)/[\w-]+/?'

@app.on_message(filters.command("start") & filters.private)
async def start(client: Client, message: Message):
    await db.add_user(message.from_user.id, message.from_user.username)
    await message.reply_text(
        "📥 Instagram Reel/Post का लिंक भेजें\n"
        "🔄 मैं वीडियो डाउनलोड कर दूंगा!",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("सपोर्ट", url=Config.SUPPORT_GROUP_URL)
        ]])
    )

@app.on_message(filters.regex(INSTA_REGEX))
async def handle_message(client: Client, message: Message):
    try:
        # Permission Check for Groups
        if message.chat.type != "private":
            if not message.text.startswith("@" + Config.BOT_USERNAME):
                return
        
        await message.reply_chat_action("upload_video")
        
        # Download Video
        video_path = await downloader.download_instagram(message.text)
        
        # Send Video
        await message.reply_video(
            video=video_path,
            caption=f"📥 Downloaded via @{Config.BOT_USERNAME}",
            reply_to_message_id=message.id if message.chat.type != "private" else None
        )
        
        # Cleanup
        os.remove(video_path)
        await db.log_usage(message.from_user.id)
        
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")
        logging.error(str(e))

if __name__ == "__main__":
    app.run()
