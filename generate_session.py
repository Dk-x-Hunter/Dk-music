from pyrogram import Client


print("=" * 50)
print("        DK MUSIC - SESSION GENERATOR")
print("=" * 50)
print()
print("Enter your Telegram API credentials.")
print("You can get them from my.telegram.org")
print()


api_id = input("API ID: ").strip()
api_hash = input("API HASH: ").strip()


if not api_id.isdigit():
    raise ValueError("API ID must contain numbers only.")

if not api_hash:
    raise ValueError("API HASH cannot be empty.")


print()
print("Starting Telegram login...")
print("A Telegram login code will be sent to your account.")
print()


with Client(
    "dk_music_session",
    api_id=int(api_id),
    api_hash=api_hash,
    in_memory=True,
) as app:

    session_string = app.export_session_string()

    print()
    print("=" * 50)
    print("        SESSION GENERATED")
    print("=" * 50)
    print()
    print(session_string)
    print()
    print("=" * 50)
    print("Copy the session string to GitHub Secrets.")
    print("Secret name: ASSISTANT_SESSION")
    print("=" * 50)