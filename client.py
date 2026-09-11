import logging

from pyrogram import Client
from pytgcalls import PyTgCalls

from config import (
    API_ID,
    API_HASH,
    BOT_TOKEN,
    SESSION_STRING,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

LOGGER = logging.getLogger("DkMusic")


# =========================
# Telegram Bot
# =========================

bot = Client(
    "dk_music_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)


# =========================
# Telegram Assistant
# =========================

assistant = Client(
    "dk_music_assistant",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=SESSION_STRING,
)


# =========================
# PyTgCalls
# =========================

calls = PyTgCalls(assistant)


# =========================
# Compatibility
# =========================

app = bot
user = assistant
call = calls