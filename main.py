import os
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from utils.db import add_user, log_usage, total_users, get_user_stats, users as users_col
from utils.helpers import download_media

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Ensure downloads folder
os.makedirs(Config.DOWNLOAD_PATH if hasattr(Config, 'DOWNLOAD_PATH') else "downloads", exist_ok=True)

app = Client(
    name="SFW_DownloadBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

START_MARKUP = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔗 Support Group", url=Config.SUPPORT_GROUP_URL)],
    [InlineKeyboardButton("📊 My Stats", callback_data="stats")],
    [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")]
])

# Track admins awaiting broadcast messages
pending_broadcast_admins = set()

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

@app.on_message(filters.private & filters.text)
async def private_handler(client: Client, message: Message):
    user_id = message.from_user.id
    await add_user(user_id)

    # Broadcast flow
    if user_id in pending_broadcast_admins:
        pending_broadcast_admins.remove(user_id)
        await message.reply_text("📤 Broadcasting to all users...", quote=True)
        total = await total_users()
        count = 0
        for u in users_col.find({}, {"_id": 1}):
            try:
                await client.send_message(chat_id=u["_id"], text=message.text)
                count += 1
            except Exception:
                continue
        await message.reply_text(f"✅ Broadcast completed. Sent to {count}/{total} users.", quote=True)
        return

    # Download flow
    if not message.text.startswith("http"):
        return

    await log_usage(user_id)
    stats = await get_user_stats(user_id)
    premium = stats.get("premium", False)
    await download_media(message, premium)

@app.on_message(filters.group & filters.text)
async def group_handler(client: Client, message: Message):
    # Only process if message contains a URL
    if not message.text or "http" not in message.text:
        return

    user_id = message.from_user.id
    await add_user(user_id)
    await log_usage(user_id)
    stats = await get_user_stats(user_id)
    premium = stats.get("premium", False)
    await download_media(message, premium)

@app.on_callback_query(filters.regex(r"^
