"""
Optional MongoDB database for Dk Music.

MongoDB is NOT required for the bot to play music.

If MONGO_URI is missing or MongoDB is unavailable:
    - the bot continues running
    - runtime data is kept locally in memory
"""

import logging
from typing import Any, Optional

from config import MONGO_URI, MONGO_DB_NAME


LOGGER = logging.getLogger("DkMusic.Database")


# ============================================================
# MongoDB
# ============================================================

mongo_client = None
database = None

mongo_enabled = False


def connect_mongodb() -> bool:
    """
    Try to connect to MongoDB.

    Returns:
        True  -> MongoDB is available
        False -> MongoDB is unavailable/disabled
    """

    global mongo_client
    global database
    global mongo_enabled

    # MongoDB is optional.
    if not MONGO_URI:
        LOGGER.info(
            "MONGO_URI not configured. "
            "Using local runtime storage."
        )

        mongo_enabled = False
        return False

    try:
        from pymongo import MongoClient

        mongo_client = MongoClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
        )

        # Force an actual connection test.
        mongo_client.admin.command("ping")

        database = mongo_client[
            MONGO_DB_NAME
        ]

        mongo_enabled = True

        LOGGER.info(
            "MongoDB connected successfully."
        )

        return True

    except Exception as exc:

        mongo_client = None
        database = None
        mongo_enabled = False

        LOGGER.warning(
            "MongoDB unavailable. "
            "Continuing without MongoDB: %s",
            exc,
        )

        return False


def close_mongodb():
    """
    Close MongoDB connection if one exists.
    """

    global mongo_client
    global database
    global mongo_enabled

    if mongo_client:

        try:
            mongo_client.close()
        except Exception:
            pass

    mongo_client = None
    database = None
    mongo_enabled = False


# ============================================================
# Collection helper
# ============================================================

def get_collection(
    name: str,
):
    """
    Return a MongoDB collection.

    Returns None if MongoDB is disabled.
    """

    if not mongo_enabled:
        return None

    if database is None:
        return None

    return database[name]


# ============================================================
# Generic document operations
# ============================================================

def get_document(
    collection_name: str,
    query: dict,
) -> Optional[dict]:

    collection = get_collection(
        collection_name
    )

    if collection is None:
        return None

    try:
        return collection.find_one(query)

    except Exception as exc:

        LOGGER.warning(
            "MongoDB read failed: %s",
            exc,
        )

        return None


def set_document(
    collection_name: str,
    query: dict,
    data: dict,
) -> bool:

    collection = get_collection(
        collection_name
    )

    if collection is None:
        return False

    try:

        collection.update_one(
            query,
            {
                "$set": data,
            },
            upsert=True,
        )

        return True

    except Exception as exc:

        LOGGER.warning(
            "MongoDB write failed: %s",
            exc,
        )

        return False


def delete_document(
    collection_name: str,
    query: dict,
) -> bool:

    collection = get_collection(
        collection_name
    )

    if collection is None:
        return False

    try:

        collection.delete_one(
            query
        )

        return True

    except Exception as exc:

        LOGGER.warning(
            "MongoDB delete failed: %s",
            exc,
        )

        return False


# ============================================================
# Authorized chats
# ============================================================

def is_chat_authorized(
    chat_id: int,
) -> bool:

    document = get_document(
        "authorized_chats",
        {
            "_id": int(chat_id),
        },
    )

    return document is not None


def authorize_chat(
    chat_id: int,
) -> bool:

    return set_document(
        "authorized_chats",
        {
            "_id": int(chat_id),
        },
        {
            "chat_id": int(chat_id),
        },
    )


def unauthorize_chat(
    chat_id: int,
) -> bool:

    return delete_document(
        "authorized_chats",
        {
            "_id": int(chat_id),
        },
    )


# ============================================================
# Sudo users
# ============================================================

def is_sudo_user(
    user_id: int,
) -> bool:

    document = get_document(
        "sudo_users",
        {
            "_id": int(user_id),
        },
    )

    return document is not None


def add_sudo_user(
    user_id: int,
) -> bool:

    return set_document(
        "sudo_users",
        {
            "_id": int(user_id),
        },
        {
            "user_id": int(user_id),
        },
    )


def remove_sudo_user(
    user_id: int,
) -> bool:

    return delete_document(
        "sudo_users",
        {
            "_id": int(user_id),
        },
    )


# ============================================================
# Simple key/value storage
# ============================================================

def get_value(
    key: str,
    default: Any = None,
) -> Any:

    document = get_document(
        "settings",
        {
            "_id": key,
        },
    )

    if not document:
        return default

    return document.get(
        "value",
        default,
    )


def set_value(
    key: str,
    value: Any,
) -> bool:

    return set_document(
        "settings",
        {
            "_id": key,
        },
        {
            "value": value,
        },
    )


# ============================================================
# Start optional database
# ============================================================

connect_mongodb()