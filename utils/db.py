from datetime import datetime
from typing import Dict, List, Optional
from pymongo import MongoClient, ReturnDocument
from pymongo.errors import PyMongoError
from config import Config

class Database:
    def __init__(self):
        self.client = MongoClient(Config.MONGO_DB_URI)
        self.db = self.client['SFWDownloadBot']
        self.users = self.db['users']
        
        # Create indexes
        self.users.create_index("downloads", background=True)
        self.users.create_index("premium", background=True)

    async def add_user(self, user_id: int) -> bool:
        """Add a new user to the database atomically"""
        try:
            result = self.users.update_one(
                {"_id": user_id},
                {"$setOnInsert": {
                    "joined": datetime.utcnow(),
                    "downloads": 0,
                    "premium": False
                }},
                upsert=True
            )
            return result.upserted_id is not None
        except PyMongoError as e:
            print(f"Database error in add_user: {e}")
            return False

    async def log_usage(self, user_id: int) -> bool:
        """Increment download counter atomically"""
        try:
            result = self.users.update_one(
                {"_id": user_id},
                {"$inc": {"downloads": 1}},
                upsert=True  # Creates user if not exists
            )
            return result.modified_count > 0
        except PyMongoError as e:
            print(f"Database error in log_usage: {e}")
            return False

    async def set_premium(self, user_id: int, status: bool = True) -> bool:
        """Update premium status with atomic operation"""
        try:
            result = self.users.update_one(
                {"_id": user_id},
                {"$set": {"premium": status}},
                upsert=False  # Don't create new users here
            )
            return result.modified_count > 0
        except PyMongoError as e:
            print(f"Database error in set_premium: {e}")
            return False

    async def get_user_stats(self, user_id: int) -> Optional[Dict]:
        """Get user statistics with projection"""
        try:
            return self.users.find_one(
                {"_id": user_id},
                {"_id": 0, "joined": 1, "downloads": 1, "premium": 1}
            )
        except PyMongoError as e:
            print(f"Database error in get_user_stats: {e}")
            return None

    async def total_users(self) -> int:
        """Get total user count efficiently"""
        try:
            return self.users.count_documents({})
        except PyMongoError as e:
            print(f"Database error in total_users: {e}")
            return 0

    async def top_downloaders(self, limit: int = 10) -> List[Dict]:
        """Get top downloaders with optimized query"""
        try:
            return list(self.users.find(
                {},
                {"_id": 1, "downloads": 1}
            ).sort("downloads", -1).limit(limit))
        except PyMongoError as e:
            print(f"Database error in top_downloaders: {e}")
            return []

# Singleton instance
db = Database()
