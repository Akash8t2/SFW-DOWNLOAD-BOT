from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from utils.db import add_user, log_usage
from utils.helpers import download_media
import re
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = Client(
    "SFW_DownloadBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

INSTA_REGEX = r'(https?://)?(www\.)?instagram\.com/(reel|p|tv)/[a-zA-Z0-9_-]+/?(\?.*)?'

# स्टार्ट कमांड
@app.on_message(filters.command("start") & filters.private)
async def start(client: Client, message: Message):
    await add_user(message.from_user.id)
    await message.reply_text(
        "🔹 Instagram लिंक भेजें (Reel/Post)\n"
        "🔹 मैं वीडियो डाउनलोड कर दूंगा!",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Support", url=Config.SUPPORT_GROUP_URL)]])
    )

# प्राइवेट मैसेज हैंडलर
@app.on_message(filters.private & filters.regex(INSTA_REGEX))
async def handle_private(client: Client, message: Message):
    await log_usage(message.from_user.id)
    await download_media(message)

# ग्रुप मैसेज हैंडलर (ऑटो डिटेक्ट)
@app.on_message(filters.group & filters.regex(INSTA_REGEX))
async def handle_group(client: Client, message: Message):
    try:
        await message.reply_chat_action("upload_video")
        await download_media(message, reply_to=True)
        await log_usage(message.from_user.id)
    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    app.run()
