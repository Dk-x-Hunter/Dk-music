import os


def get_env(name: str, default=None, required: bool = False):
    value = os.getenv(name, default)

    if required and not value:
        raise RuntimeError(f"Missing required environment variable: {name}")

    return value


# =========================
# Telegram
# =========================

API_ID = int(get_env("API_ID", required=True))
API_HASH = get_env("API_HASH", required=True)
BOT_TOKEN = get_env("BOT_TOKEN", required=True)

# Pyrogram assistant/user session.
# Generate this separately and put it in GitHub Secrets.
ASSISTANT_SESSION = get_env("ASSISTANT_SESSION", "")

# Optional alternative name.
STRING_SESSION = get_env("STRING_SESSION", "")


# =========================
# Owner / Sudo
# =========================

OWNER_ID = int(get_env("OWNER_ID", required=True))

_sudo_raw = get_env("SUDO_USERS", "")

SUDO_USERS = set()

if _sudo_raw:
    for user_id in _sudo_raw.replace(",", " ").split():
        try:
            SUDO_USERS.add(int(user_id))
        except ValueError:
            pass

# Owner is always sudo.
SUDO_USERS.add(OWNER_ID)


# =========================
# YouTube / yt-dlp
# =========================

# Optional cookies file.
#
# Example:
# YOUTUBE_COOKIES=/home/runner/work/Dk-music/cookies.txt
#
# Leave empty if cookies are not needed.
YOUTUBE_COOKIES = get_env("YOUTUBE_COOKIES", "")

# Optional cookies URL.
#
# If supplied, the application can download the cookies file
# before using yt-dlp.
YOUTUBE_COOKIES_URL = get_env("YOUTUBE_COOKIES_URL", "")


# =========================
# Audio
# =========================

DOWNLOAD_DIR = get_env("DOWNLOAD_DIR", "downloads")

MAX_QUEUE = int(get_env("MAX_QUEUE", "20"))


# =========================
# Optional MongoDB
# =========================

# MongoDB is intentionally optional.
#
# If MONGO_URI is empty or MongoDB fails, the bot should continue
# using local/in-memory state.
MONGO_URI = get_env("MONGO_URI", "")

MONGO_DB_NAME = get_env("MONGO_DB_NAME", "dkmusic")


# =========================
# Logging
# =========================

LOGGER_ID = int(get_env("LOGGER_ID", "0"))


# =========================
# Runtime
# =========================

# Automatically create download directory.
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# =========================
# Helpers
# =========================

def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


def is_sudo(user_id: int) -> bool:
    return user_id in SUDO_USERS