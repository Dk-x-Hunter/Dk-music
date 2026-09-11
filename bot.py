import asyncio
import logging

from client import bot, assistant, calls


# Import music handlers.
# This MUST happen before the clients start so that
# Pyrogram registers all /play, /queue, /pause, etc.
import music  # noqa: F401


LOGGER = logging.getLogger("DkMusic")


async def main():
    """
    Start the Telegram bot, assistant and PyTgCalls.
    """

    LOGGER.info("Starting Dk Music...")

    # Start bot
    await bot.start()
    LOGGER.info("Bot started.")

    # Start assistant
    await assistant.start()
    LOGGER.info("Assistant started.")

    # Start voice-call client
    await calls.start()
    LOGGER.info("PyTgCalls started.")

    me = await bot.get_me()

    LOGGER.info(
        "Dk Music started successfully as @%s",
        me.username,
    )

    print()
    print("=" * 45)
    print("       DK MUSIC BOT STARTED")
    print("=" * 45)
    print(f"Bot: @{me.username}")
    print("YouTube search: ENABLED")
    print("Voice chat: ENABLED")
    print("Queue: ENABLED")
    print("=" * 45)
    print()

    # Keep the application alive.
    try:
        await asyncio.Event().wait()

    finally:
        LOGGER.info("Stopping Dk Music...")

        try:
            await calls.stop()
        except Exception:
            pass

        try:
            await assistant.stop()
        except Exception:
            pass

        try:
            await bot.stop()
        except Exception:
            pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Dk Music stopped.")