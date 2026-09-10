🎵 Dk Music Bot

A simple Telegram group voice-chat music bot.

The assistant account joins the voice chat and plays audio from YouTube.

✨ Features

- 🔎 YouTube song search
- ▶️ Play by song name
- 🔗 Play YouTube links
- 🎧 Assistant joins the VC
- 📋 Queue system
- ⏸ Pause
- ▶️ Resume
- ⏭ Skip
- ⏹ Stop
- 🎵 Now Playing
- 🔄 Automatic next song
- 🚫 No clone system
- 🚫 No unnecessary database

🎮 Commands

/play <song name>
/play <YouTube URL>

/queue
/now

/pause
/resume
/skip
/stop

Example

/play Shape of You

The bot will:

🔎 Search YouTube
       ↓
🎵 Find the song
       ↓
👤 Assistant joins VC
       ↓
▶️ Play audio
       ↓
📋 Next songs go to queue
       ↓
🔄 Automatically play next song
       ↓
👋 Leave VC when queue is empty

🔧 Environment Variables

Set these variables:

API_ID=
API_HASH=
BOT_TOKEN=
ASSISTANT_SESSION=
OWNER_ID=

API_ID and API_HASH

Get these from Telegram's API development page.

BOT_TOKEN

Create your bot using BotFather and copy the bot token.

ASSISTANT_SESSION

This is the session string for the Telegram account that will join the voice chat.

Generate it with:

python generate_session.py

Never share or upload the session string.

OWNER_ID

Your Telegram user ID.

📦 Installation

Install Python 3.10+ and FFmpeg.

sudo apt update
sudo apt install ffmpeg -y

Clone the repository:

git clone https://github.com/Dk-x-Hunter/Dk-music
cd Dk-music

Install dependencies:

pip install -r requirements.txt

▶️ Start

Set your environment variables and run:

python bot.py

🎧 Telegram Setup

1. Add the bot to your group.
2. Add the assistant account to the group.
3. Give the assistant appropriate admin permissions.
4. Start a Telegram voice chat.
5. Send:

/play <song name>

The assistant will join the voice chat and play the selected YouTube audio.

🔐 Security

Never upload these files or values:

*.session
*.session-journal
.env
BOT_TOKEN
API_HASH
ASSISTANT_SESSION

Keep your assistant session private.

📄 License

For personal use and learning.