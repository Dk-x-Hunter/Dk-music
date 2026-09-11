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
from pytgcalls.types import MediaStream, StreamEnded

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
    webpage_url: str
    duration: int
    requested_by: str
    file: Optional[str] = None


# ============================================================
# Runtime state
# ============================================================

queues: dict[int, list[Song]] = {}
current: dict[int, Song] = {}

# Used to prevent two playback workers starting simultaneously.
play_locks: dict[int, asyncio.Lock] = {}

# Used when /skip is called.
skip_requested: set[int] = set()


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
            r"^(https?://)?(www\.)?"
            r"(youtube\.com|youtu\.be)/",
            text,
            re.IGNORECASE,
        )
    )


# ============================================================
# yt-dlp options
# ============================================================

def base_ytdlp_options() -> dict:
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
    """
    Search YouTube and return the first result.

    /play Shape of You
        ↓
    ytsearch1:Shape of You
        ↓
    First YouTube result
    """

    options = base_ytdlp_options()

    options.update(
        {
            "skip_download": True,
            "extract_flat": True,
            "default_search": "ytsearch",
        }
    )

    if is_youtube_url(query):
        search = query
    else:
        search = f"ytsearch1:{query}"

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(
            search,
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

def download_song(url: str) -> str:
    """
    Download the best available audio from YouTube.
    """

    output_template = os.path.join(
        DOWNLOAD_DIR,
        f"{uuid.uuid4().hex}.%(ext)s",
    )

    options = base_ytdlp_options()

    options.update(
        {
            "format": "bestaudio/best",
            "outtmpl": output_template,
            "noplaylist": True,
            "quiet": True,
            "no_warnings": True,
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

    base, _ = os.path.splitext(prepared)

    mp3_file = base + ".mp3"

    if os.path.exists(mp3_file):
        return mp3_file

    # Fallback if FFmpeg did not create an MP3.
    if os.path.exists(prepared):
        return prepared

    # Last-resort search for the generated file.
    directory = os.path.dirname(prepared)

    if os.path.isdir(directory):
        for filename in os.listdir(directory):
            if filename.startswith(os.path.basename(base)):
                path = os.path.join(directory, filename)

                if os.path.isfile(path):
                    return path

    raise FileNotFoundError(
        "yt-dlp downloaded the media, "
        "but the audio file could not be located."
    )


# ============================================================
# Create Song
# ============================================================

async def get_song(
    query: str,
    requester: str,
) -> Optional[Song]:

    info = await asyncio.to_thread(
        search_youtube,
        query,
    )

    if not info:
        return None

    webpage_url = (
        info.get("webpage_url")
        or info.get("original_url")
    )

    if not webpage_url:
        video_id = info.get("id")

        if not video_id:
            return None

        webpage_url = (
            "https://www.youtube.com/watch?v="
            f"{video_id}"
        )

    return Song(
        title=info.get(
            "title",
            "Unknown YouTube video",
        ),
        webpage_url=webpage_url,
        duration=info.get("duration") or 0,
        requested_by=requester,
    )


# ============================================================
# Cleanup
# ============================================================

async def cleanup_song(
    song: Optional[Song],
):
    if not song or not song.file:
        return

    try:
        if os.path.exists(song.file):
            os.remove(song.file)

    except OSError:
        pass


# ============================================================
# Play next song
# ============================================================

async def play_song(chat_id: int):
    """
    Takes the next song from the queue,
    downloads it and starts PyTgCalls playback.
    """

    lock = get_lock(chat_id)

    # Only one worker may start playback.
    async with lock:

        # Already playing something.
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
                "⏳ **Downloading from YouTube...**\n\n"
                f"🎵 **{song.title}**\n"
                f"⏱ `{format_duration(song.duration)}`"
            ),
        )

        # yt-dlp is blocking, so run it outside
        # the asyncio event loop.
        song.file = await asyncio.to_thread(
            download_song,
            song.webpage_url,
        )

        await bot.send_message(
            chat_id,
            "🔊 **Joining voice chat...**",
        )

        # PyTgCalls will join the active voice chat
        # and play the downloaded media.
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

        current.pop(chat_id, None)

        await cleanup_song(song)

        await bot.send_message(
            chat_id,
            (
                "❌ **Playback failed.**\n\n"
                f"`{str(exc)[:1500]}`"
            ),
        )

        # Try the next queued song.
        if queues.get(chat_id):
            await play_song(chat_id)


# ============================================================
# Stream finished
# ============================================================

@calls.on_stream_end()
async def stream_finished(
    _: PyTgCalls,
    update: StreamEnded,
):
    chat_id = update.chat_id

    old_song = current.pop(
        chat_id,
        None,
    )

    await cleanup_song(old_song)

    # If /skip triggered this event, the skip handler
    # will start the next track.
    if chat_id in skip_requested:
        skip_requested.discard(chat_id)
        return

    # Automatic next song.
    if queues.get(chat_id):
        await play_song(chat_id)
        return

    # Nothing left.
    try:
        await calls.leave_call(chat_id)
    except Exception:
        pass

    queues.pop(chat_id, None)

    await bot.send_message(
        chat_id,
        "✅ **Queue finished.** Assistant left the voice chat.",
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
            "❌ **Usage:**\n"
            "`/play song name`\n\n"
            "or\n\n"
            "`/play YouTube URL`"
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
        song = await get_song(
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

            queues[chat_id].append(song)

            await status.edit_text(
                (
                    "✅ **YouTube result found!**\n\n"
                    f"🎵 **{song.title}**\n"
                    f"⏱ `{format_duration(song.duration)}`\n\n"
                    "▶️ **Starting playback...**"
                )
            )

            await play_song(chat_id)

            return

        # Something is already playing.
        if len(queues[chat_id]) >= MAX_QUEUE:

            await status.edit_text(
                (
                    "❌ **Queue limit reached.**\n\n"
                    f"Maximum: `{MAX_QUEUE}` songs"
                )
            )

            return

        queues[chat_id].append(song)

        position = len(
            queues[chat_id]
        )

        await status.edit_text(
            (
                "➕ **Added to queue**\n\n"
                f"🎵 **{song.title}**\n"
                f"⏱ `{format_duration(song.duration)}`\n"
                f"📌 Position: `{position}`"
            )
        )

    except Exception as exc:

        await status.edit_text(
            (
                "❌ **YouTube search failed.**\n\n"
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

    now = current.get(chat_id)

    if now:
        lines.append(
            "▶️ **Now Playing:**\n"
            f"🎵 {now.title}\n"
            f"⏱ `{format_duration(now.duration)}`"
        )

    queue = queues.get(
        chat_id,
        [],
    )

    if queue:

        lines.append(
            "\n📋 **Up Next:**"
        )

        for index, song in enumerate(
            queue,
            1,
        ):
            lines.append(
                f"`{index}.` {song.title} "
                f"— `{format_duration(song.duration)}`"
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

    skip_requested.add(chat_id)

    try:

        await calls.stop(
            chat_id
        )

        # Remove current state.
        old_song = current.pop(
            chat_id,
            None,
        )

        await cleanup_song(
            old_song
        )

        if queues.get(chat_id):

            await message.reply_text(
                "⏭ **Skipped. Playing next song...**"
            )

            await play_song(
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

    except Exception as exc:

        skip_requested.discard(
            chat_id
        )

        await message.reply_text(
            f"❌ `{str(exc)[:700]}`"
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

    skip_requested.discard(
        chat_id
    )

    old_song = current.pop(
        chat_id,
        None,
    )

    await cleanup_song(
        old_song
    )

    try:
        await calls.leave_call(
            chat_id
        )
    except Exception:
        pass

    await message.reply_text(
        "⏹ **Stopped playback and cleared the queue.**"
    )