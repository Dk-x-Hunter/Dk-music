import asyncio
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

import logging

from pyrogram import Client
from pytgcalls import PyTgCalls

import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("musicbot")

if not (config.API_ID and config.API_HASH and config.BOT_TOKEN and config.SESSION_STRING):
    raise SystemExit(
        "Missing config. Set API_ID, API_HASH, BOT_TOKEN, SESSION_STRING "
        "as environment variables (see README.md)."
    )

# The bot users talk to (sends messages, receives commands)
app = Client(
    "musicbot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
    plugins=dict(root="plugins"),
)

# The user account that actually joins the voice chat
user = Client(
    "musicuser",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    session_string=config.SESSION_STRING,
)

call = PyTgCalls(user)

# Per-chat song queue: {chat_id: [ {title, url, requested_by}, ... ]}
QUEUES = {}
