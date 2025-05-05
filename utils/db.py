from pymongo import MongoClient
from datetime import datetime
from config import Config

# MongoDB setup

client = MongoClient(Config.MONGO_DB_URI) db = client['SFWDownloadBot'] users = db['users']

async def add_user(user_id: int): """ Add a new user to the database with join timestamp and initial download count. """ if not users.find_one({"_id": user_id}): users.insert_one({ "_id": user_id, "joined": datetime.utcnow(),  # UTC timestamp of first interaction "downloads": 0,             # Count of videos downloaded "premium": False            # Premium flag (can be updated later) })

async def log_usage(user_id: int): """ Increment the download counter for a user every time they request a video. """ users.update_one({"_id": user_id}, {"$inc": {"downloads": 1}})

async def set_premium(user_id: int, status: bool = True): """ Update a user's premium status. """ users.update_one({"_id": user_id}, {"$set": {"premium": status}})

async def get_user_stats(user_id: int) -> dict: """ Fetch user statistics (join date, downloads, premium status). """ return users.find_one({"_id": user_id}, {"_id": 0})

async def total_users() -> int: """ Return the total number of users in the bot. """ return users.count_documents({})

async def top_downloaders(limit: int = 10) -> list: """ Return a list of top users by download count. """ cursor = users.find({}).sort("downloads", -1).limit(limit) return list(cursor)

