# Telegram Voice-Chat Music Bot

Plays music in a group's voice chat, controlled by you (owner) and anyone you
promote to sudo/admin. Supports spinning up independent clone bots with
separate tokens.

## 1. Get credentials

- `API_ID` / `API_HASH`: https://my.telegram.org → API Development Tools
- `BOT_TOKEN`: message [@BotFather](https://t.me/BotFather) → `/newbot`
- `OWNER_ID`: your numeric Telegram user ID — message [@userinfobot](https://t.me/userinfobot)

## 2. Generate a session string (needed to join voice chats)

Bots can't join voice chats directly — a normal user account has to. This
should be an account **you control** (a secondary account is fine, doesn't
have to be your main one).

```bash
pip install -r requirements.txt
python helpers/generate_session.py
```

Copy the printed string — that's your `SESSION_STRING`.

## 3. Set environment variables

```bash
export API_ID=123456
export API_HASH=abcdef123456
export BOT_TOKEN=123456:ABC-your-bot-token
export SESSION_STRING=your_generated_string
export OWNER_ID=your_telegram_user_id
export SUDO_USERS=111111,222222   # optional, comma-separated extra admins
```

(On Windows, use `set VAR=value` in cmd, or a `.env` file with a tool like
`python-dotenv` if you prefer.)

## 4. Install & run

```bash
pip install -r requirements.txt
python bot.py
```

## 5. Using it

1. Add the bot to your group, make it **admin** (needs permission to manage
   voice chats).
2. In the group, run `/authorize` (as owner/sudo) so members can use it —
   or skip this and only sudo users can control playback.
3. Start a voice chat in the group, then `/play <song name or link>`.
4. `/pause`, `/resume`, `/skip`, `/queue`, `/stop` as needed.

## 6. Admin panel (all via chat commands, no separate website)

| Command | Who | What |
|---|---|---|
| `/authorize` | sudo | let this group use the bot |
| `/unauthorize` | sudo | revoke a group |
| `/addsudo <id>` | owner | grant control to a user |
| `/rmsudo <id>` | owner | revoke control |
| `/sudolist` | sudo | list current admins |
| `/addclone <token> <name>` | owner | launch an independent clone bot |
| `/rmclone <name>` | owner | stop a clone |
| `/clones` | owner | list running clones |

## What I deliberately left out

I did **not** add a "send this link to every group the bot is in" broadcast
feature. That's effectively unsolicited mass messaging — it gets bots banned
by Telegram's spam detection fast, and it messages people in groups who never
opted in. If you want to announce something, do it manually in the specific
groups you actually manage, or ask group admins for permission first.

## Notes

- `pytgcalls`/`pyrogram` APIs change between versions — if `/play` errors
  with an import or method-not-found issue, check your installed
  `py-tgcalls` version's docs; the `MediaStream` call in `plugins/music.py`
  matches py-tgcalls 2.x.
- All data (sudo list, authorized groups, clone registry) is stored in
  `data.json` next to `bot.py` — back it up if you care about it.
- This is a real, working starting point — not a toy. For a i3/4GB machine,
  running the bot itself is fine (it's mostly network I/O), but consider a
  cheap VPS ($3-5/mo tier) for 24/7 uptime instead of your laptop.
