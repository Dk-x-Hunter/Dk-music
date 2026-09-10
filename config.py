import os

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]

BOT_TOKEN = os.environ["BOT_TOKEN"]
ASSISTANT_SESSION = os.environ["ASSISTANT_SESSION"]

OWNER_ID = int(os.environ["OWNER_ID"])

DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "downloads")
MAX_QUEUE = int(os.getenv("MAX_QUEUE", "25"))

os.makedirs(DOWNLOAD_DIR, exist_ok=True)