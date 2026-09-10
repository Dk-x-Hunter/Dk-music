"""
Run this ONCE locally to generate SESSION_STRING.

Voice chats can only be joined by a regular Telegram *user* account
(bots cannot join VCs directly), so pytgcalls needs a logged-in user
session separate from your bot token. This script logs into YOUR
personal account (the one you want acting as the "listener") and
prints a session string you paste into your .env as SESSION_STRING.

Usage:
    python helpers/generate_session.py
"""
import asyncio
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

from pyrogram import Client

api_id = int(input("Enter API_ID: "))
api_hash = input("Enter API_HASH: ")

with Client("session_gen", api_id=api_id, api_hash=api_hash, in_memory=True) as app:
    print("\nYour SESSION_STRING (keep this secret, treat like a password):\n")
    print(app.export_session_string())
