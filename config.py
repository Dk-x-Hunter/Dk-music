import os


# ============================================================
# Environment helper
# ============================================================

def env(name, default=None, required=False):
    value = os.getenv(name)

    if value is None or value.strip() == "":
        if required:
            raise RuntimeError(
                f"Missing required environment variable: {name}"se
            )
        return default

    return value.strip()


# ============================================================
# Telegram
# ============================================================

API_ID = int(env("API_ID", required=True))

API_HASH = env(
    "API_HASH",
    required=True,
)

BOT_TOKEN = env(
    "BOT_TOKEN",
    required=True,
)


# ============================================================
# Assistant Session
# ============================================================

ASSISTANT_SESSION = env(
    "ASSISTANT_SESSION",
    "",
)

STRING_SESSION = env(
    "STRING_SESSION",
    "",
)

# Support either secret name.
SESSION_STRING = (
    ASSISTANT_SESSION
    or STRING_SESSION
)

if not SESSION_STRING:
    raise RuntimeError(
        "Missing ASSISTANT_SESSION or STRING_SESSION."
    )


# ============================================================
# Owner
# ============================================================

OWNER_ID = int(
    env(
        "OWNER_ID",
        required=True,
    )
)


# ============================================================
# Sudo Users
# ============================================================

SUDO_USERS = {
    OWNER_ID
}

sudo_raw = env(
    "SUDO_USERS",
    "",
)

if sudo_raw:
    for item in sudo_raw.replace(
        ",",
        " ",
    ).split():

        try:
            SUDO_USERS.add(
                int(item)
            )
        except ValueError:
            pass


# ============================================================
# YouTube
# ============================================================

YOUTUBE_COOKIES = env(
    "YOUTUBE_COOKIES",
    "",
)

YOUTUBE_COOKIES_URL = env(
    "YOUTUBE_COOKIES_URL",
    "",
)


# ============================================================
# Music
# ============================================================

DOWNLOAD_DIR = env(
    "DOWNLOAD_DIR",
    "downloads",
)

MAX_QUEUE = int(
    env(
        "MAX_QUEUE",
        "20",
    )
)

os.makedirs(
    DOWNLOAD_DIR,
    exist_ok=True,
)


# ============================================================
# Optional MongoDB
# ============================================================

MONGO_URI = env(
    "MONGO_URI",
    "",
)

MONGO_DB_NAME = env(
    "MONGO_DB_NAME",
    "dkmusic",
)


# ============================================================
# Logger
# ============================================================

LOGGER_ID = int(
    env(
        "LOGGER_ID",
        "0",
    )
)


# ============================================================
# Permission helpers
# ============================================================

def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


def is_sudo(user_id: int) -> bool:
    return user_id in SUDO_USERS


def is_owner_or_sudo(
    user_id: int,
) -> bool:
    return (
        user_id == OWNER_ID
        or user_id in SUDO_USERS
    )

