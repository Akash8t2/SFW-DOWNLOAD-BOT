import os
import requests
from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config

# Heroku setup
HEROKU_API_KEY = Config.HEROKU_API_KEY
HEROKU_APP_NAME = Config.HEROKU_APP_NAME

@Client.on_message(filters.command("logs") & filters.user(Config.OWNER_ID))
async def fetch_logs(client: Client, message: Message):
    if not HEROKU_API_KEY or not HEROKU_APP_NAME:
        await message.reply_text("❌ Heroku API Key ya App Name missing hai.")
        return

    headers = {
        "Accept": "application/vnd.heroku+json; version=3",
        "Authorization": f"Bearer {HEROKU_API_KEY}"
    }

    log_url = f"https://api.heroku.com/apps/{HEROKU_APP_NAME}/log-sessions"
    data = {
        "source": "app",
        "dyno": "",
        "lines": 1000,
        "tail": False
    }

    try:
        response = requests.post(log_url, headers=headers, json=data)
        response.raise_for_status()
        log_session_url = response.json()["logplex_url"]

        logs = requests.get(log_session_url).text

        if len(logs) > 4096:
            # Send as file
            with open("heroku_logs.txt", "w", encoding='utf-8') as f:
                f.write(logs)
            await message.reply_document("heroku_logs.txt", caption="📝 Heroku Logs")
            os.remove("heroku_logs.txt")
        else:
            await message.reply_text(f"```\n{logs}\n```", quote=True)

    except Exception as e:
        await message.reply_text(f"❌ Error fetching logs:\n`{e}`")
