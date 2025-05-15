from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from utils.db import add_user, log_usage, set_premium, get_user_stats
import asyncio
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Client(
    name="SFW_DownloadBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

START_MARKUP = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔗 Support Group", url=Config.SUPPORT_GROUP_URL)],
    [InlineKeyboardButton("📊 My Stats", callback_data="my_stats")]
])

@app.on_message(filters.command("start") & filters.private)
async def start(client: Client, message: Message):
    await add_user(message.from_user.id)
    if message.from_user.id == 5397621246:
        await set_premium(5397621246, True)
    text = (
        f"👋 Hello <b>{message.from_user.first_name}</b>!\n"
        f"Welcome to <b>{Config.BOT_USERNAME}</b>.\n\n"
        "🔹 Send me an Instagram, TikTok, YouTube, Pinterest, or Terabox link.\n"
        "🔹 I'll fetch and send the video without watermark (if supported).\n\n"
        "🚀 Enjoy your premium downloader experience!"
    )
    await message.reply_text(text, reply_markup=START_MARKUP, disable_web_page_preview=True)


@app.on_message(filters.command("setpremium") & filters.user(Config.ADMINS))
async def make_premium(client: Client, message: Message):
    parts = message.text.split()
    if len(parts) != 2:
        await message.reply_text("Usage: /setpremium <user_id>")
        return
    try:
        user_id = int(parts[1])
        await set_premium(user_id, True)
        await message.reply_text(f"✅ User {user_id} is now premium.")
    except Exception:
        await message.reply_text("❌ Failed to set premium.")


@app.on_message(filters.command("removepremium") & filters.user(Config.ADMINS))
async def remove_premium(client: Client, message: Message):
    parts = message.text.split()
    if len(parts) != 2:
        await message.reply_text("Usage: /removepremium <user_id>")
        return
    try:
        user_id = int(parts[1])
        await set_premium(user_id, False)
        await message.reply_text(f"✅ User {user_id} is no longer premium.")
    except Exception:
        await message.reply_text("❌ Failed to remove premium.")


@app.on_callback_query(filters.regex("^my_stats$"))
async def stats_handler(client, callback_query):
    stats = await get_user_stats(callback_query.from_user.id)
    if not stats:
        await callback_query.message.reply_text("No stats found.")
        return
    reply = (
        f"📊 <b>Your Stats</b>\n\n"
        f"• Joined: <code>{stats.get('joined')}</code>\n"
        f"• Downloads: <b>{stats.get('downloads')}</b>\n"
        f"• Premium: <b>{'Yes' if stats.get('premium') else 'No'}</b>"
    )
    await callback_query.message.reply_text(reply)


async def download_media_with_progress(message: Message, premium: bool):
    status_msg = await message.reply_text("Starting download...")

    # Simulate condition to check if download is possible
    can_download = True  # Replace with real condition

    if not can_download:
        await status_msg.edit_text("❌ Sorry, no downloadable media found or download cannot be started.")
        return

    # Simulate download progress
    for percent in range(0, 101, 10):
        bars = '▰' * (percent // 10) + '▱' * (10 - (percent // 10))
        await status_msg.edit_text(f"Downloading...\n{bars} {percent}%")
        await asyncio.sleep(1)  # Simulate download chunk delay

    await status_msg.edit_text("✅ Download complete! Sending your file...")

    # Yahan real downloaded file bhejne ka code add karo
    # await message.reply_document(file_path_or_bytes, caption="Here's your file!")

@app.on_message(filters.text & filters.private & filters.regex(r"http"))
async def handle_private(client: Client, message: Message):
    await log_usage(message.from_user.id)
    await download_media_with_progress(message, premium=True)

@app.on_message(filters.text & filters.group & filters.regex(r"http"))
async def handle_group(client: Client, message: Message):
    await log_usage(message.from_user.id)
    await download_media_with_progress(message, premium=False)


if __name__ == "__main__":
    app.run()
