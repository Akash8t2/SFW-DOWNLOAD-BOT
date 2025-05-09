import os
from dotenv import load_dotenv
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

class Config:
    API_ID = int(os.getenv("API_ID", "123456"))
    API_HASH = os.getenv("API_HASH", "")
    BOT_TOKEN = os.getenv("BOT_TOKEN", "")
    BOT_USERNAME = os.getenv("BOT_USERNAME", "@SFW_DOWNLOAD_BOT")
    MONGO_DB_URI = os.getenv("MONGO_DB_URI", "")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "SFWDownloadBot")
    ADMINS = [int(x) for x in os.getenv("ADMINS", "").split(",") if x]
    SUPPORT_GROUP_URL = os.getenv("SUPPORT_GROUP_URL", "https://t.me/SFW_Community_Official")
    BROADCAST_BUTTON_LABEL = os.getenv("BROADCAST_BUTTON_LABEL", "📢 Broadcast")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    DOWNLOAD_TIMEOUT = int(os.getenv("DOWNLOAD_TIMEOUT", "60"))
    MAX_VIDEO_SIZE_MB = int(os.getenv("MAX_VIDEO_SIZE_MB", "500"))
