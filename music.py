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
from pytgcalls.types import StreamEnded

from client import bot, calls, assistant
from config import DOWNLOAD_DIR, MAX_QUEUE


@dataclass
class Song:
    title: str
    url: str
    webpage_url: str
    duration: int
    requested_by: str
    file: Optional[str] = None


queues: dict[int, list[Song]] = {}
current: dict[int, Song] = {}
locks: dict[int, asyncio.Lock] = {}


def get_lock(chat_id: int) -> asyncio.Lock:
    if chat_id not in locks:
        locks[chat_id] = asyncio.Lock()
    return locks[chat_id]


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
            r"^(https?://)?(www\.)?(youtube\.com|youtu\.be)/",
            text,
            re.IGNORECASE,
        )
    )


def search_youtube(query: str) -> Optional[dict]:
    options = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
        "extract_flat": True,
        "default_search": "ytsearch",
    }

    search = query if is_youtube_url(query) else f"ytsearch1:{query}"

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(search, download=False)

        if not info:
            return None

        if "entries" in info:
            entries = [x for x in info["entries"] if x]

            if not entries:
                return None

            info = entries[0]

        return info


def download_song(url: str) -> str:
    filename = os.path.join(
        DOWNLOAD_DIR,
        f"{uuid.uuid4().hex}.%(ext)s",
    )

    options = {
        "format": "bestaudio/best",
        "outtmpl": filename,
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

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=True)
        prepared = ydl.prepare_filename(info)

    base, _ = os.path.splitext(prepared)
    mp3_file = base + ".mp3"

    if os.path.exists(mp3_file):
        return mp3_file

    # Fallback in case the extractor/container is different.
    if os.path.exists(prepared):
        return prepared

    raise FileNotFoundError("Downloaded audio file was not found.")


async def get_song(query: str, requester: str) -> Optional[Song]:
    info = await asyncio.to_thread(search_youtube, query)

    if not info:
        return None

    webpage_url = info.get("webpage_url") or info.get("original_url")

    if not webpage_url:
        video_id = info.get("id")

        if not video_id:
            return None

        webpage_url = f"https://www.youtube.com/watch?v={video_id}"

    return Song(
        title=info.get("title", "Unknown"),
        url=webpage_url,
        webpage_url=webpage_url,
        duration=info.get("duration") or 0,
        requested_by=requester,
    )


async def play_song(chat_id: int):
    async with get_lock(chat_id):
        if chat_id not in queues or not queues[chat_id]:
            current.pop(chat_id, None)
            return

        song = queues[chat_id].pop(0)
        current[chat_id] = song

    try:
        await bot.send_message(
            chat_id,
            (
                "⏳ **Preparing audio...**\n\n"
                f"🎵 **{song.title}**\n"
                f"⏱ `{format_duration(song.duration)}`"
            ),
        )

        # Download outside the event loop.
        song.file = await asyncio.to_thread(
            download_song,
            song.webpage_url,
        )

        # Assistant joins/plays in the group's voice chat.
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
                f"👤 Requested by: {song.requested_by}"
            ),
        )

    except Exception as exc:
        current.pop(chat_id, None)

        await bot.send_message(
            chat_id,
            (
                "❌ **Playback failed.**\n\n"
                f"`{str(exc)[:1000]}`"
            ),
        )

        await play_song(chat_id)


async def cleanup_song(song: Optional[Song]):
    if not song or not song.file:
        return

    try:
        if os.path.exists(song.file):
            os.remove(song.file)
    except OSError:
        pass


@calls.on_stream_end()
async def stream_finished(_: PyTgCalls, update: StreamEnded):
    chat_id = update.chat_id

    old_song = current.pop(chat_id, None)

    await cleanup_song(old_song)

    if queues.get(chat_id):
        await play_song(chat_id)
    else:
        try:
            await calls.leave_call(chat_id)
        except Exception:
            pass

        await bot.send_message(
            chat_id,
            "✅ **Queue finished.** Assistant left the voice chat.",
        )


@bot.on_message(filters.command("play"))
async def play_command(_, message: Message):
    if len(message.command) < 2:
        await message.reply_text(
            "❌ Usage:\n`/play song name or YouTube URL`"
        )
        return

    query = message.text.split(None, 1)[1].strip()

    status = await message.reply_text(
        "🔎 **Searching YouTube...**"
    )

    requester = (
        message.from_user.mention
        if message.from_user
        else "Unknown"
    )

    try:
        song = await get_song(query, requester)

        if not song:
            await status.edit_text(
                "❌ **No YouTube result found.**"
            )
            return

        chat_id = message.chat.id

        if chat_id not in queues:
            queues[chat_id] = []

        # Nothing is currently playing.
        if chat_id not in current:
            queues[chat_id].append(song)

            await status.edit_text(
                (
                    "✅ **Found**\n\n"
                    f"🎵 **{song.title}**\n"
                    f"⏱ `{format_duration(song.duration)}`\n\n"
                    "▶️ Starting playback..."
                )
            )

            await play_song(chat_id)
            return

        # Existing playback -> queue.
        if len(queues[chat_id]) >= MAX_QUEUE:
            await status.edit_text(
                f"❌ Queue limit reached (`{MAX_QUEUE}`)."
            )
            return

        queues[chat_id].append(song)

        position = len(queues[chat_id])

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
            f"❌ Error: `{str(exc)[:1000]}`"
        )


@bot.on_message(filters.command("queue"))
async def queue_command(_, message: Message):
    chat_id = message.chat.id

    lines = []

    now = current.get(chat_id)

    if now:
        lines.append(
            f"▶️ **Now:** {now.title}"
        )

    queue = queues.get(chat_id, [])

    if queue:
        lines.append("")
        lines.append("📋 **Up Next:**")

        for index, song in enumerate(queue, 1):
            lines.append(
                f"`{index}.` {song.title} "
                f"— `{format_duration(song.duration)}`"
            )
    elif not now:
        lines.append("📭 Queue is empty.")

    await message.reply_text("\n".join(lines))


@bot.on_message(filters.command("pause"))
async def pause_command(_, message: Message):
    try:
        await calls.pause(message.chat.id)
        await message.reply_text("⏸ **Paused.**")
    except Exception as exc:
        await message.reply_text(
            f"❌ `{str(exc)[:500]}`"
        )


@bot.on_message(filters.command("resume"))
async def resume_command(_, message: Message):
    try:
        await calls.resume(message.chat.id)
        await message.reply_text("▶️ **Resumed.**")
    except Exception as exc:
        await message.reply_text(
            f"❌ `{str(exc)[:500]}`"
        )


@bot.on_message(filters.command("skip"))
async def skip_command(_, message: Message):
    chat_id = message.chat.id

    try:
        await calls.stop(chat_id)

        # Start next item manually.
        if queues.get(chat_id):
            await play_song(chat_id)
        else:
            current.pop(chat_id, None)

            try:
                await calls.leave_call(chat_id)
            except Exception:
                pass

            await message.reply_text(
                "⏭ **Skipped. Queue is empty.**"
            )
            return

        await message.reply_text("⏭ **Skipped. Playing next song...**")

    except Exception as exc:
        await message.reply_text(
            f"❌ `{str(exc)[:500]}`"
        )


@bot.on_message(filters.command("stop"))
async def stop_command(_, message: Message):
    chat_id = message.chat.id

    queues.pop(chat_id, None)

    old_song = current.pop(chat_id, None)

    await cleanup_song(old_song)

    try:
        await calls.leave_call(chat_id)
    except Exception:
        pass

    await message.reply_text(
        "⏹ **Stopped playback and cleared the queue.**"
    )


@bot.on_message(filters.command("now"))
async def now_command(_, message: Message):
    song = current.get(message.chat.id)

    if not song:
        await message.reply_text(
            "📭 Nothing is playing."
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