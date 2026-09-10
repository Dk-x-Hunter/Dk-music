import os

# ==== Required ====
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
SESSION_STRING = os.getenv("ASSISTANT_SESSION") or os.getenv("STRING_SESSION")

# ==== Ownership / access control ====
MAIN_OWNER = int(os.getenv("OWNER_ID"))
DEPLOYED_OWNER_ID = int(os.getenv("OWNER_ID"))

SUDO_USERS = [
    int(user_id.strip())
    for user_id in os.getenv("SUDO_USERS", "").split(",")
    if user_id.strip()
]

# ==== Storage ====
DB_FILE = os.path.join(os.path.dirname(__file__), "data.json")

# ==== Clone system ====
CLONE_ONLY_OWNER = os.getenv("CLONE_ONLY_OWNER", "true").lower() == "true"