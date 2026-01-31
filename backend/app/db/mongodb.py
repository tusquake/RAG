from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional

from app.config import get_settings

settings = get_settings()


class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    db = None


mongodb = MongoDB()


async def connect_to_mongo():
    mongodb.client = AsyncIOMotorClient(settings.MONGODB_URI)
    mongodb.db = mongodb.client[settings.MONGODB_DB_NAME]
    
    await mongodb.db.users.create_index("email", unique=True)
    await mongodb.db.documents.create_index("user_id")
    await mongodb.db.chat_history.create_index([("document_id", 1), ("created_at", -1)])
    
    print(f"Connected to MongoDB: {settings.MONGODB_DB_NAME}")


async def close_mongo_connection():
    if mongodb.client:
        mongodb.client.close()
        print("Closed MongoDB connection")


def get_database():
    return mongodb.db


def get_collection(name: str):
    return mongodb.db[name]
