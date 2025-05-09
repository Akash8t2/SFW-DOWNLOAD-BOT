from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from utils.db import db
from utils.helpers import Downloader
import re
import logging
import traceback

# लॉगिंग कॉन्फ़िगर करें
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Client(
    "SFW_DownloadBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

downloader = Downloader()
INSTA_REGEX = r'(https?://)?(www\.)?instagram\.com/(reel|p|tv)/[a-zA-Z0-9_-]+/?(\?.*)?'

# स्टार्ट कमांड
@app.on_message(filters.command("start") & filters.private)
async def start(client: Client, message: Message):
    try:
        user = message.from_user
        await db.add_user(user.id, user.username or user.first_name)
        await message.reply_text(
            "🎬 **Instagram Video Downloader**\n\n"
            "किसी भी Instagram Reel/Post का लिंक भेजें, मैं उसे डाउनलोड कर दूँगा!\n\n"
            "⚠️ **नोट:** सिर्फ पब्लिक अकाउंट के वीडियो काम करते हैं",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("सपोर्ट ग्रुप", url=Config.SUPPORT_GROUP_URL)
            ]])
        )
    except Exception as e:
        logger.error(f"Start Error: {traceback.format_exc()}")

# ग्रुप और प्राइवेट दोनों के लिए हैंडलर
@app.on_message(filters.text & (filters.group | filters.private))
async def handle_messages(client: Client, message: Message):
    try:
        # सिर्फ Instagram लिंक प्रोसेस करें
        if not re.match(INSTA_REGEX, message.text):
            return

        # ग्रुप में mention/reply चेक करें
        if message.chat.type == enums.ChatType.GROUP:
            if not (message.text.startswith("@" + Config.BOT_USERNAME) and 
                   not (message.reply_to_message and message.reply_to_message.from_user.is_self)):
                return

        await message.reply_chat_action(enums.ChatAction.UPLOAD_VIDEO)
        user = message.from_user

        # डाउनलोड शुरू करें
        video_path = await downloader.download_media(message.text)
        
        # वीडियो भेजें
        await message.reply_video(
            video=video_path,
            caption=f"📥 Downloaded via @{Config.BOT_USERNAME}",
            reply_to_message_id=message.id if message.chat.type != enums.ChatType.PRIVATE else None
        )

        # क्लीनअप और लॉग
        os.remove(video_path)
        await db.log_usage(user.id)

    except Exception as e:
        error_msg = f"❌ Error: {str(e)}\n\n{traceback.format_exc()}"
        logger.error(error_msg)
        await message.reply_text("⚠️ डाउनलोड असफल! कृपया लिंक चेक करें")

if __name__ == "__main__":
    logger.info("Bot Started!")
    app.run()
