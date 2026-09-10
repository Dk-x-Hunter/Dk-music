from pyrogram import Client
from pytgcalls import PyTgCalls

from config import (
    API_ID,
    API_HASH,
    BOT_TOKEN,
    ASSISTANT_SESSION,
)

# Main Telegram bot
bot = Client(
    "dk_music_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

# Assistant/user account
assistant = Client(
    "dk_music_assistant",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=ASSISTANT_SESSION,
)

# Voice-chat engine
calls = PyTgCalls(assistant)