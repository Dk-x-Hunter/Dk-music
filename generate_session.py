import asyncio

from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded


async def main():
    print("======================================")
    print("      Dk Music Assistant Session")
    print("======================================")
    print()

    api_id = input("Enter API_ID: ").strip()
    api_hash = input("Enter API_HASH: ").strip()
    phone = input("Enter assistant phone number: ").strip()

    try:
        api_id = int(api_id)
    except ValueError:
        print("❌ API_ID must be a number.")
        return

    app = Client(
        "dk_music_session_generator",
        api_id=api_id,
        api_hash=api_hash,
        in_memory=True,
    )

    try:
        await app.connect()

        sent_code = await app.send_code(phone)

        code = input("Enter Telegram login code: ").strip()

        try:
            await app.sign_in(
                phone_number=phone,
                phone_code_hash=sent_code.phone_code_hash,
                phone_code=code,
            )

        except SessionPasswordNeeded:
            password = input(
                "Enter your Telegram 2FA password: "
            ).strip()

            await app.check_password(password)

        except Exception as exc:
            print(f"\n❌ Login failed: {exc}")
            return

        session_string = await app.export_session_string()

        me = await app.get_me()

        print()
        print("======================================")
        print("✅ SESSION GENERATED")
        print("======================================")
        print(f"Assistant: {me.first_name}")
        print(f"User ID: {me.id}")
        print()
        print("ASSISTANT_SESSION:")
        print(session_string)
        print()
        print("======================================")
        print("⚠️ Keep this session string PRIVATE.")
        print("⚠️ Do NOT upload it to GitHub.")
        print("======================================")

    except Exception as exc:
        print(f"\n❌ Error: {exc}")

    finally:
        try:
            await app.disconnect()
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())