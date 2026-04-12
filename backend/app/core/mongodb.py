"""MongoDB connection management using Motor."""

from __future__ import annotations

import logging
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class MongoDB:
    client: AsyncIOMotorClient = None
    db = None

mongodb = MongoDB()

async def connect_to_mongo():
    """Create database connection."""
    logger.info("Connecting to MongoDB...")
    mongodb.client = AsyncIOMotorClient(settings.mongodb_url)
    # Extract database name from URL if present, otherwise default to 'talentra'
    db_name = settings.mongodb_url.split("/")[-1].split("?")[0] or "Talentra"
    mongodb.db = mongodb.client[db_name]
    logger.info(f"Connected to MongoDB database: {db_name}")

async def close_mongo_connection():
    """Close database connection."""
    logger.info("Closing MongoDB connection...")
    if mongodb.client:
        mongodb.client.close()
    logger.info("MongoDB connection closed.")

def get_database():
    """Return the database instance."""
    return mongodb.db
