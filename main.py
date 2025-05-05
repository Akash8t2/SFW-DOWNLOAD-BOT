from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from utils.db import add_user, log_usage
from utils.helpers import download_media
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Client(
    name="SFW_DownloadBot",  # 'session_name' is invalid in Pyrogram v2+, use 'name'
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# Keyboards
START_MARKUP = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔗 Support Group", url=Config.SUPPORT_GROUP_URL)],
])

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

@app.on_message(filters.text & filters.private)
async def handle_private(client: Client, message: Message):
    await log_usage(message.from_user.id)
    await download_media(message, premium=True)

@app.on_message(filters.text & filters.group)
async def handle_group(client: Client, message: Message):
    if Config.BOT_USERNAME in message.text or (message.reply_to_message and message.reply_to_message.from_user.is_self):
        await log_usage(message.from_user.id)
        await download_media(message, premium=False)

@app.on_inline_query()
async def inline_query_handler(client, inline_query):
    # TODO: Implement inline query feature
    pass

@app.on_callback_query(filters.regex(r"^admin_broadcast$"))
async def admin_broadcast_prompt(client, callback_query):
    user_id = callback_query.from_user.id
    if user_id in Config.ADMINS:
        await callback_query.message.reply_text("Send the broadcast message:")

        @app.on_message(filters.user(user_id) & filters.text)
        async def broadcast(client, message: Message):
            text = message.text
            await message.reply_text("Broadcasting to all users...")
            # TODO: Loop through users in DB and send messages
            await message.reply_text("✅ Broadcast completed.")
    else:
        await callback_query.answer("You are not authorized.", show_alert=True)

if __name__ == "__main__":
    app.run()
