from pymongo import MongoClient
from datetime import datetime
from config import Config

client = MongoClient(Config.MONGO_DB_URI)
db = client['SFWDownloadBot']
users = db['users']

async def add_user(user_id: int):
    if not users.find_one({"_id": user_id}):
        users.insert_one({
            "_id": user_id,
            "joined": datetime.utcnow(),
            "downloads": 0,
            "premium": False
        })

async def log_usage(user_id: int):
    users.update_one({"_id": user_id}, {"$inc": {"downloads": 1}})

async def set_premium(user_id: int, status: bool = True):
    users.update_one({"_id": user_id}, {"$set": {"premium": status}})

async def get_user_stats(user_id: int) -> dict:
    return users.find_one({"_id": user_id}, {"_id": 0}) or {}

async def total_users() -> int:
    return users.count_documents({})

async def top_downloaders(limit: int = 10) -> list:
    cursor = users.find({}).sort("downloads", -1).limit(limit)
    return list(cursor)
