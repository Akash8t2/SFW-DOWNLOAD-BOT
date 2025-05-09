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
        self._create_indexes()

    def _create_indexes(self):
        self.users.create_index("downloads", background=True)
        self.users.create_index("premium", background=True)

    async def add_user(self, user_id: int, username: str) -> bool:
        try:
            result = self.users.update_one(
                {"_id": user_id},
                {"$setOnInsert": {
                    "username": username,
                    "joined": datetime.utcnow(),
                    "downloads": 0,
                    "premium": False
                }},
                upsert=True
            )
            return result.upserted_id is not None
        except PyMongoError as e:
            print(f"Database Error: {e}")
            return False

    async def log_usage(self, user_id: int) -> bool:
        try:
            result = self.users.update_one(
                {"_id": user_id},
                {"$inc": {"downloads": 1}}
            )
            return result.modified_count > 0
        except PyMongoError as e:
            print(f"Database Error: {e}")
            return False

    async def get_user(self, user_id: int) -> Optional[Dict]:
        try:
            return self.users.find_one({"_id": user_id})
        except PyMongoError as e:
            print(f"Database Error: {e}")
            return None

# Singleton Instance
db = Database()
