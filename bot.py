import logging

from client import app, user, call

logger = logging.getLogger("musicbot")

if __name__ == "__main__":
    logger.info("Starting music bot...")
    user.start()
    call.start()
    app.run()
    logger.info("Bot stopped.")