import asyncio
import os
import re
import uuid
from dataclasses import dataclass
from typing import Optional

import yt_dlp

from pyrogram import filters
from pyrogram.types import Message

from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream

try:
    from pytgcalls.types.stream import StreamAudioEnded
except ImportError:
    StreamAudioEnded = None

from client import bot, calls
from config import (
    DOWNLOAD_DIR,
    MAX_QUEUE,
    YOUTUBE_COOKIES,
)


# ============================================================
# Song
# ============================================================

@dataclass
class Song:
    title: str
    url: str
    duration: int
    requested_by: str
    file: Optional[str] = None


# ============================================================
# Runtime
# ============================================================

queues: dict[int, list[Song]] = {}
current: dict[int, Song] = {}

play_locks: dict[int, asyncio.Lock] = {}


def get_lock(chat_id: int) -> asyncio.Lock:
    if chat_id not in play_locks:
        play_locks[chat_id] = asyncio.Lock()

    return play_locks[chat_id]


# ============================================================
# Helpers
# ============================================================

def format_duration(seconds: int) -> str:
    if not seconds:
        return "Unknown"

    seconds = int(seconds)

    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours:
        return f"{hours}:{minutes:02}:{seconds:02}"

    return f"{minutes}:{seconds:02}"


def is_youtube_url(text: str) -> bool:
    return bool(
        re.match(
            r"^https?://"
            r"(www\.)?"
            r"(youtube\.com|youtu\.be)/",
            text,
            re.IGNORECASE,
        )
    )


# ============================================================
# yt-dlp
# ============================================================

def ytdlp_options() -> dict:
    options = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }

    if YOUTUBE_COOKIES:
        if os.path.isfile(YOUTUBE_COOKIES):
            options["cookiefile"] = YOUTUBE_COOKIES

    return options


# ============================================================
# YouTube search
# ============================================================

def search_youtube(query: str) -> Optional[dict]:
    options = ytdlp_options()

    options.update(
        {
            "extract_flat": True,
            "skip_download": True,
        }
    )

    if is_youtube_url(query):
        target = query
    else:
        target = f"ytsearch1:{query}"

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(
            target,
            download=False,
        )

    if not info:
        return None

    if "entries" in info:
        entries = [
            entry
            for entry in info["entries"]
            if entry
        ]

        if not entries:
            return None

        return entries[0]

    return info


# ============================================================
# Download audio
# ============================================================

def download_audio(url: str) -> str:

    filename = os.path.join(
        DOWNLOAD_DIR,
        f"{uuid.uuid4().hex}.%(ext)s",
    )

    options = ytdlp_options()

    options.update(
        {
            "format": "bestaudio/best",
            "outtmpl": filename,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }
    )

    with yt_dlp.YoutubeDL(options) as ydl:

        info = ydl.extract_info(
            url,
            download=True,
        )

        prepared = ydl.prepare_filename(info)

    base = os.path.splitext(prepared)[0]

    mp3 = base + ".mp3"

    if os.path.exists(mp3):
        return mp3

    if os.path.exists(prepared):
        return prepared

    directory = os.path.dirname(prepared)

    if os.path.isdir(directory):

        prefix = os.path.basename(base)

        for name in os.listdir(directory):

            if name.startswith(prefix):

                path = os.path.join(
                    directory,
                    name,
                )

                if os.path.isfile(path):
                    return path

    raise FileNotFoundError(
        "Downloaded audio file was not found."
    )


# ============================================================
# Create Song
# ============================================================

async def create_song(
    query: str,
    requester: str,
) -> Optional[Song]:

    info = await asyncio.to_thread(
        search_youtube,
        query,
    )

    if not info:
        return None

    url = (
        info.get("webpage_url")
        or info.get("original_url")
    )

    if not url:

        video_id = info.get("id")

        if not video_id:
            return None

        url = (
            "https://www.youtube.com/watch?v="
            + video_id
        )

    return Song(
        title=info.get(
            "title",
            "Unknown",
        ),
        url=url,
        duration=info.get(
            "duration",
            0,
        ) or 0,
        requested_by=requester,
    )


# ============================================================
# Cleanup
# ============================================================

def delete_file(path: Optional[str]):

    if not path:
        return

    try:

        if os.path.exists(path):
            os.remove(path)

    except OSError:
        pass


# ============================================================
# Play next
# ============================================================

async def play_next(chat_id: int):

    lock = get_lock(chat_id)

    async with lock:

        if chat_id in current:
            return

        if not queues.get(chat_id):
            return

        song = queues[chat_id].pop(0)

        current[chat_id] = song

    try:

        await bot.send_message(
            chat_id,
            (
                "🔎 **YouTube result found**\n\n"
                f"🎵 **{song.title}**\n"
                f"⏱ `{format_duration(song.duration)}`\n\n"
                "⬇️ Downloading audio..."
            ),
        )

        song.file = await asyncio.to_thread(
            download_audio,
            song.url,
        )

        await bot.send_message(
            chat_id,
            "🔊 **Starting voice chat playback...**",
        )

        await calls.play(
            chat_id,
            MediaStream(song.file),
        )

        await bot.send_message(
            chat_id,
            (
                "▶️ **Now Playing**\n\n"
                f"🎵 **{song.title}**\n"
                f"⏱ `{format_duration(song.duration)}`\n"
                f"👤 {song.requested_by}"
            ),
        )

    except Exception as exc:

        current.pop(
            chat_id,
            None,
        )

        delete_file(
            song.file
        )

        await bot.send_message(
            chat_id,
            (
                "❌ **Playback failed**\n\n"
                f"`{str(exc)[:1500]}`"
            ),
        )

        if queues.get(chat_id):
            await play_next(chat_id)


# ============================================================
# Stream ended
# ============================================================

@calls.on_stream_end()
async def stream_finished(
    client: PyTgCalls,
    update,
):

    chat_id = update.chat_id

    song = current.pop(
        chat_id,
        None,
    )

    if song:
        delete_file(
            song.file
        )

    if queues.get(chat_id):

        await play_next(
            chat_id
        )

        return

    try:
        await calls.leave_call(
            chat_id
        )
    except Exception:
        pass

    queues.pop(
        chat_id,
        None,
    )


# ============================================================
# /play
# ============================================================

@bot.on_message(
    filters.command("play")
)
async def play_command(
    _,
    message: Message,
):

    if len(message.command) < 2:

        await message.reply_text(
            (
                "🎵 **Usage:**\n\n"
                "`/play song name`\n\n"
                "Example:\n"
                "`/play Shape of You`"
            )
        )

        return

    query = message.text.split(
        None,
        1,
    )[1].strip()

    status = await message.reply_text(
        "🔎 **Searching YouTube...**"
    )

    requester = (
        message.from_user.mention
        if message.from_user
        else "Unknown"
    )

    try:

        song = await create_song(
            query,
            requester,
        )

        if not song:

            await status.edit_text(
                "❌ **No YouTube result found.**"
            )

            return

        chat_id = message.chat.id

        if chat_id not in queues:
            queues[chat_id] = []

        # Nothing playing.
        if chat_id not in current:

            queues[chat_id].append(
                song
            )

            await status.edit_text(
                (
                    "✅ **Found on YouTube**\n\n"
                    f"🎵 **{song.title}**\n"
                    f"⏱ `{format_duration(song.duration)}`\n\n"
                    "▶️ Starting..."
                )
            )

            await play_next(
                chat_id
            )

            return

        # Queue limit.
        if len(queues[chat_id]) >= MAX_QUEUE:

            await status.edit_text(
                (
                    "❌ **Queue is full.**\n\n"
                    f"Maximum: `{MAX_QUEUE}`"
                )
            )

            return

        queues[chat_id].append(
            song
        )

        position = len(
            queues[chat_id]
        )

        await status.edit_text(
            (
                "➕ **Added to queue**\n\n"
                f"🎵 **{song.title}**\n"
                f"📌 Position: `{position}`"
            )
        )

    except Exception as exc:

        await status.edit_text(
            (
                "❌ **YouTube error**\n\n"
                f"`{str(exc)[:1500]}`"
            )
        )


# ============================================================
# /queue
# ============================================================

@bot.on_message(
    filters.command("queue")
)
async def queue_command(
    _,
    message: Message,
):

    chat_id = message.chat.id

    lines = []

    song = current.get(
        chat_id
    )

    if song:

        lines.append(
            "▶️ **Now Playing**\n"
            f"🎵 {song.title}\n"
            f"⏱ `{format_duration(song.duration)}`"
        )

    queue = queues.get(
        chat_id,
        [],
    )

    if queue:

        lines.append(
            "\n📋 **Up Next**"
        )

        for index, item in enumerate(
            queue,
            1,
        ):

            lines.append(
                f"`{index}.` {item.title}"
            )

    if not lines:

        lines.append(
            "📭 **Queue is empty.**"
        )

    await message.reply_text(
        "\n".join(lines)
    )


# ============================================================
# /now
# ============================================================

@bot.on_message(
    filters.command("now")
)
async def now_command(
    _,
    message: Message,
):

    song = current.get(
        message.chat.id
    )

    if not song:

        await message.reply_text(
            "📭 **Nothing is playing.**"
        )

        return

    await message.reply_text(
        (
            "🎵 **Now Playing**\n\n"
            f"**{song.title}**\n"
            f"⏱ `{format_duration(song.duration)}`\n"
            f"👤 {song.requested_by}"
        )
    )


# ============================================================
# /pause
# ============================================================

@bot.on_message(
    filters.command("pause")
)
async def pause_command(
    _,
    message: Message,
):

    try:

        await calls.pause(
            message.chat.id
        )

        await message.reply_text(
            "⏸ **Paused.**"
        )

    except Exception as exc:

        await message.reply_text(
            f"❌ `{str(exc)[:700]}`"
        )


# ============================================================
# /resume
# ============================================================

@bot.on_message(
    filters.command("resume")
)
async def resume_command(
    _,
    message: Message,
):

    try:

        await calls.resume(
            message.chat.id
        )

        await message.reply_text(
            "▶️ **Resumed.**"
        )

    except Exception as exc:

        await message.reply_text(
            f"❌ `{str(exc)[:700]}`"
        )


# ============================================================
# /skip
# ============================================================

@bot.on_message(
    filters.command("skip")
)
async def skip_command(
    _,
    message: Message,
):

    chat_id = message.chat.id

    if chat_id not in current:

        await message.reply_text(
            "❌ **Nothing is playing.**"
        )

        return

    old_song = current.pop(
        chat_id,
        None,
    )

    if old_song:
        delete_file(
            old_song.file
        )

    try:

        await calls.stop(
            chat_id
        )

    except Exception:
        pass

    if queues.get(chat_id):

        await message.reply_text(
            "⏭ **Skipped. Playing next...**"
        )

        await play_next(
            chat_id
        )

    else:

        queues.pop(
            chat_id,
            None,
        )

        try:
            await calls.leave_call(
                chat_id
            )
        except Exception:
            pass

        await message.reply_text(
            "⏭ **Skipped. Queue is empty.**"
        )


# ============================================================
# /stop
# ============================================================

@bot.on_message(
    filters.command("stop")
)
async def stop_command(
    _,
    message: Message,
):

    chat_id = message.chat.id

    queues.pop(
        chat_id,
        None,
    )

    song = current.pop(
        chat_id,
        None,
    )

    if song:
        delete_file(
            song.file
        )

    try:

        await calls.stop(
            chat_id
        )

    except Exception:
        pass

    try:

        await calls.leave_call(
            chat_id
        )

    except Exception:
        pass

    await message.reply_text(
        "⏹ **Playback stopped and queue cleared.**"
    )