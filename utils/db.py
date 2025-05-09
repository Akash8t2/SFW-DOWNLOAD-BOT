from datetime import datetime
from typing import Dict, Optional
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from config import Config
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.client = MongoClient(Config.MONGO_DB_URI)
        self.db = self.client[Config.MONGO_DB_NAME]
        self.users = self.db.users
        self._create_indexes()

    def _create_indexes(self):
        try:
            self.users.create_index("downloads", background=True)
            self.users.create_index("premium", background=True)
        except PyMongoError as e:
            logger.error(f"Index Error: {str(e)}")

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
            logger.error(f"Add User Error: {str(e)}")
            return False

    async def log_usage(self, user_id: int) -> bool:
        try:
            result = self.users.update_one(
                {"_id": user_id},
                {"$inc": {"downloads": 1}}
            )
            return result.modified_count > 0
        except PyMongoError as e:
            logger.error(f"Log Usage Error: {str(e)}")
            return False

# Singleton Instance
db = Database()
