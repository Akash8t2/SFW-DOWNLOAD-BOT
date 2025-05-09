from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from utils.db import add_user, log_usage
from utils.helpers import download_media
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Client(
    name="SFW_DownloadBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# Keyboards
START_MARKUP = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔗 Support Group", url=Config.SUPPORT_GROUP_URL)],
])

# Instagram URL Regex Pattern
INSTA_REGEX = r'(https?://)?(www\.)?instagram\.com/(reel|p|stories|tv)/[a-zA-Z0-9_-]+/?(\?igshid=[a-zA-Z0-9_]+)?'

@app.on_message(filters.command("start") & filters.private)
async def start(client: Client, message: Message):
    await add_user(message.from_user.id)
    text = (
        f"👋 Hello <b>{message.from_user.first_name}</b>!\n"
        f"Welcome to <b>{Config.BOT_USERNAME}</b>.\n\n"
        "🔹 Send me an Instagram, TikTok, YouTube, or Pinterest link.\n"
        "🔹 I'll fetch and send the video without watermark (if supported).\n\n"
        "🚀 Enjoy your premium downloader experience!"
    )
    await message.reply_text(text, reply_markup=START_MARKUP, disable_web_page_preview=True)

# Handle Private Instagram Links
@app.on_message(filters.private & filters.regex(INSTA_REGEX))
async def handle_private_insta(client: Client, message: Message):
    await log_usage(message.from_user.id)
    await download_media(message, platform="instagram", premium=True)

# Handle Group Instagram Links (Auto-detect)
@app.on_message(filters.group & filters.regex(INSTA_REGEX))
async def handle_group_insta(client: Client, message: Message):
    await log_usage(message.from_user.id)
    await download_media(message, platform="instagram", premium=False)

# Handle Other Platforms (YT, TikTok etc.)
@app.on_message(filters.text & (filters.private | filters.group))
async def handle_other_platforms(client: Client, message: Message):
    url = message.text.strip()
    if any(domain in url for domain in ["youtube.com", "youtu.be", "tiktok.com", "pinterest.com"]):
        await log_usage(message.from_user.id)
        await download_media(message, platform="other", premium=message.chat.type == "private")

@app.on_inline_query()
async def inline_query_handler(client, inline_query):
    await inline_query.answer([])

if __name__ == "__main__":
    app.run()
