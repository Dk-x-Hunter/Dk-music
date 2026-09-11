import logging

from pyrogram import Client
from pytgcalls import PyTgCalls

from config import (
    API_ID,
    API_HASH,
    BOT_TOKEN,
    ASSISTANT_SESSION,
    STRING_SESSION,
)


# =========================
# Logging
# =========================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

LOGGER = logging.getLogger("DkMusic")


# =========================
# Bot Client
# =========================

bot = Client(
    "dk_music_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)


# =========================
# Assistant Client
# =========================

# Prefer ASSISTANT_SESSION.
# STRING_SESSION is supported as a fallback.

assistant_session = ASSISTANT_SESSION or STRING_SESSION

if not assistant_session:
    raise RuntimeError(
        "ASSISTANT_SESSION or STRING_SESSION is required."
    )


assistant = Client(
    "dk_music_assistant",
    api_id=API_ID,
    api_hash=API_HASH,
    session_string=assistant_session,
)


# =========================
# PyTgCalls
# =========================

calls = PyTgCalls(assistant)


# =========================
# Compatibility aliases
# =========================

# These aliases prevent older modules from breaking if they use
# app/user/call instead of bot/assistant/calls.

app = bot
user = assistant
call = calls


# =========================
# Startup
# =========================

async def start_clients():
    """
    Start Telegram bot, assistant and voice-call client.
    """

    LOGGER.info("Starting Telegram bot...")

    await bot.start()

    LOGGER.info("Starting assistant...")

    await assistant.start()

    LOGGER.info("Starting PyTgCalls...")

    await calls.start()

    LOGGER.info("Dk Music clients started successfully.")


# =========================
# Shutdown
# =========================

async def stop_clients():
    """
    Stop all clients cleanly.
    """

    LOGGER.info("Stopping PyTgCalls...")

    try:
        await calls.stop()
    except Exception as e:
        LOGGER.warning("PyTgCalls stop error: %s", e)

    LOGGER.info("Stopping assistant...")

    try:
        await assistant.stop()
    except Exception as e:
        LOGGER.warning("Assistant stop error: %s", e)

    LOGGER.info("Stopping bot...")

    try:
        await bot.stop()
    except Exception as e:
        LOGGER.warning("Bot stop error: %s", e)

    LOGGER.info("Dk Music stopped.")