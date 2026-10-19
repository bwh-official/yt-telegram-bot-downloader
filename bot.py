import os
import time
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from pyrogram.errors import FloodWait

from config import cfg
from utils import extract_video_id, format_duration, parse_duration_seconds, make_safe_filename, get_channel_tag
from api import fetch_video_info, download_file, download_thumbnail
from keyboards import (
    build_start_markup,
    build_help_markup,
    build_download_options_markup
)
from progress import render_progress_text

# Initialize Pyrogram Bot Client with persistent session
if cfg.BOT_SESSION:
    app = Client(
        name="SamraYTDownloaderBot",
        session_string=cfg.BOT_SESSION,
        api_id=cfg.API_ID,
        api_hash=cfg.API_HASH,
        bot_token=cfg.BOT_TOKEN,
        workdir="./"
    )
else:
    app = Client(
        name="SamraYTDownloaderBot",
        api_id=cfg.API_ID,
        api_hash=cfg.API_HASH,
        bot_token=cfg.BOT_TOKEN,
        workdir="./"
    )

# Start Command Handler
@app.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, m: Message):
    first_name = m.from_user.first_name if m.from_user else "User"
    mention = f"<a href='tg://user?id={m.from_user.id}'>{first_name}</a>"
    
    start_text = (
        f"<b>👋 Welcome {mention} to YouTube Pro Downloader!</b>\n\n"
        f"🚀 <i>I can download high-speed YouTube Videos in all resolutions (144p to 4K) & Ultra High Quality MP3 audio!</i>\n\n"
        f"<b>✨ Features:</b>\n"
        f"• 🎵 High-Fidelity MP3 (320kbps & 128kbps)\n"
        f"• 🎬 All Resolutions: 144p, 360p, 720p, 1080p, 2K, 4K\n"
        f"• ⚡ Instant API link resolving\n"
        f"• 📊 Live visual progress bar\n\n"
        f"👇 <b>Just send me any YouTube video link to get started!</b>"
    )
    await m.reply_text(start_text, reply_markup=build_start_markup(), disable_web_page_preview=True)

# Help Command Handler
@app.on_message(filters.command("help") & filters.private)
async def help_handler(client: Client, m: Message):
    help_text = (
        "<b>📖 How to Download YouTube Media:</b>\n\n"
        "1️⃣ Copy any YouTube link (Video, Shorts, or Music).\n"
        "2️⃣ Send the link here in this chat.\n"
        "3️⃣ Choose your desired video resolution (e.g. 720p, 1080p) or MP3 audio.\n"
        "4️⃣ Sit back and relax while the bot downloads and uploads it directly to your Telegram!\n\n"
        "💡 <i>Shorts, normal videos, and youtu.be links are all supported.</i>"
    )
    await m.reply_text(help_text, reply_markup=build_help_markup(), disable_web_page_preview=True)

# Inline Callbacks: Help and Home Navigation
@app.on_callback_query(filters.regex("^help_guide$"))
async def callback_help_guide(client: Client, cb: CallbackQuery):
    await cb.answer()
    help_text = (
        "<b>📖 How to Download YouTube Media:</b>\n\n"
        "1️⃣ Copy any YouTube link (Video, Shorts, or Music).\n"
        "2️⃣ Send the link here in this chat.\n"
        "3️⃣ Choose your desired video resolution (e.g. 720p, 1080p) or MP3 audio.\n"
        "4️⃣ Sit back and relax while the bot downloads and uploads it directly to your Telegram!\n\n"
        "💡 <i>Shorts, normal videos, and youtu.be links are all supported.</i>"
    )
    await cb.message.edit_text(help_text, reply_markup=build_help_markup(), disable_web_page_preview=True)

@app.on_callback_query(filters.regex("^start_home$"))
async def callback_start_home(client: Client, cb: CallbackQuery):
    await cb.answer()
    first_name = cb.from_user.first_name if cb.from_user else "User"
    mention = f"<a href='tg://user?id={cb.from_user.id}'>{first_name}</a>"
    
    start_text = (
        f"<b>👋 Welcome {mention} to YouTube Pro Downloader!</b>\n\n"
        f"🚀 <i>I can download high-speed YouTube Videos in all resolutions (144p to 4K) & Ultra High Quality MP3 audio!</i>\n\n"
        f"<b>✨ Features:</b>\n"
        f"• 🎵 High-Fidelity MP3 (320kbps & 128kbps)\n"
        f"• 🎬 All Resolutions: 144p, 360p, 720p, 1080p, 2K, 4K\n"
        f"• ⚡ Instant API link resolving\n"
        f"• 📊 Live visual progress bar\n\n"
        f"👇 <b>Just send me any YouTube video link to get started!</b>"
    )
    await cb.message.edit_text(start_text, reply_markup=build_start_markup(), disable_web_page_preview=True)

@app.on_callback_query(filters.regex("^close_menu$"))
async def callback_close_menu(client: Client, cb: CallbackQuery):
    try:
        await cb.message.delete()
    except Exception:
        try:
            await cb.message.edit_text("<i>❌ Menu closed.</i>", reply_markup=None)
        except Exception:
            pass
    await cb.answer()

# YouTube Link Detector and Format Fetcher
@app.on_message(filters.private & filters.text & ~filters.command(["start", "help"]))
async def youtube_link_listener(client: Client, m: Message):
    text = m.text.strip()
    video_id = extract_video_id(text)
    
    if not video_id:
        # Prompt only if it looked like a link or invalid request
        if "http://" in text or "https://" in text or "youtu" in text:
            return await m.reply_text("⚠️ <b>Invalid YouTube Link:</b> Please provide a valid YouTube video or shorts URL.")
        return await m.reply_text("👋 Send me a YouTube video link to extract video & audio formats!")

    status_msg = await m.reply_text("⚡ <b>Fetching Video Information & Direct Streams...</b>")
    
    try:
        data = await fetch_video_info(video_id)
        title = data.get("title", "YouTube Video")
        raw_dur = data.get("duration") or data.get("durationLabel")
        duration = format_duration(raw_dur)
        thumbnail_url = data.get("thumbnail") or f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
        
        info_caption = (
            f"🎬 <b>{title}</b>\n\n"
            f"⏱ <b>Duration:</b> <code>{duration}</code>\n"
            f"🆔 <b>Video ID:</b> <code>{video_id}</code>\n"
            f"⚡ <b>Engine:</b> <i>Samra YouTube Cloud API</i>\n\n"
            f"👇 <b>Select your desired resolution or MP3 audio below:</b>"
        )
        
        reply_markup = build_download_options_markup(data)
        
        # Download local thumbnail image for guaranteed Telegram display
        thumb_temp_path = os.path.join(cfg.DOWNLOAD_DIR, f"thumb_preview_{video_id}.jpg")
        local_thumb = await download_thumbnail(video_id, thumbnail_url, thumb_temp_path)
        
        try:
            if local_thumb and os.path.exists(local_thumb):
                await client.send_photo(
                    chat_id=m.chat.id,
                    photo=local_thumb,
                    caption=info_caption,
                    reply_markup=reply_markup
                )
                try:
                    os.remove(local_thumb)
                except Exception:
                    pass
            else:
                await client.send_photo(
                    chat_id=m.chat.id,
                    photo=thumbnail_url,
                    caption=info_caption,
                    reply_markup=reply_markup
                )
            await status_msg.delete()
        except Exception:
            await status_msg.edit_text(info_caption, reply_markup=reply_markup, disable_web_page_preview=False)
            
    except Exception as e:
        await status_msg.edit_text(f"❌ <b>Error resolving video:</b>\n<code>{e}</code>")

# Media Downloader & Telegram Uploader Callback Handler
@app.on_callback_query(filters.regex(r"^dl_(a|v)_([a-zA-Z0-9_-]{11})_(\w+)"))
async def media_download_handler(client: Client, cb: CallbackQuery):
    media_type = cb.matches[0].group(1)   # 'a' for audio, 'v' for video
    video_id = cb.matches[0].group(2)
    quality = cb.matches[0].group(3)
    
    await cb.answer(f"⏳ Processing {quality}...", show_alert=False)
    
    status_msg = await cb.message.reply_text(f"🚀 <b>Connecting to Fast Stream Engine ({quality})...</b>")
    
    try:
        # Retrieve video info from API / Cache
        data = await fetch_video_info(video_id)
        title = data.get("title", "YouTube Media")
        raw_dur = data.get("duration") or data.get("durationLabel")
        duration_seconds = parse_duration_seconds(raw_dur)
        
        # Determine exact download stream URL
        stream_url = None
        if media_type == "a":
            # Audio
            stream_url = f"{cfg.API_BASE}/mp3?url={video_id}&quality={quality}&redirect=1"
            # Check if downloads has direct url
            for d in data.get("downloads", []):
                if d.get("type") == "audio" and str(quality) in str(d.get("quality", "")):
                    if d.get("url"):
                        stream_url = d["url"]
                        break
            ext = "mp3"
        else:
            # Video
            stream_url = f"{cfg.API_BASE}/mp4?url={video_id}&quality={quality}&redirect=1"
            for d in data.get("downloads", []):
                if d.get("type") == "video" and str(quality) in str(d.get("quality", "")).replace("p", ""):
                    if d.get("url"):
                        stream_url = d["url"]
                        break
            ext = "mp4"

        # Formulate permanent suffix filename
        formatted_filename = make_safe_filename(title, quality, ext)
        local_path = os.path.join(cfg.DOWNLOAD_DIR, formatted_filename)
        
        # 1. Download with live visual progress
        async def dl_progress(current, total, start_time, action):
            prog_text = render_progress_text(action, current, total, start_time, title)
            try:
                await status_msg.edit_text(prog_text)
            except FloodWait as fw:
                await asyncio.sleep(fw.value)
            except Exception:
                pass
                
        await status_msg.edit_text(f"📥 <b>Downloading {quality} to server...</b>\n\n<code>{title[:40]}...</code>")
        file_path = await download_file(stream_url, local_path, progress_callback=dl_progress)
        
        # Download video thumbnail for upload preview
        thumb_upload_path = os.path.join(cfg.DOWNLOAD_DIR, f"thumb_up_{video_id}.jpg")
        upload_thumb = await download_thumbnail(video_id, data.get("thumbnail"), thumb_upload_path)

        # 2. Upload to Telegram with live visual progress
        upload_start = time.time()
        last_up_edit = upload_start
        
        async def up_progress(current, total):
            nonlocal last_up_edit
            now = time.time()
            if now - last_up_edit >= 3 or current >= total:
                last_up_edit = now
                prog_text = render_progress_text("📤 Uploading to Telegram", current, total, upload_start, title)
                try:
                    await status_msg.edit_text(prog_text)
                except FloodWait as fw:
                    await asyncio.sleep(fw.value)
                except Exception:
                    pass

        caption = (
            f"🎬 <b>{title}</b>\n\n"
            f"✨ <b>Quality:</b> <code>{quality}{'p' if media_type == 'v' else ' kbps'}</code>\n"
            f"⏱ <b>Duration:</b> <code>{format_duration(duration_seconds)}</code>\n"
            f"⚡ <b>Uploaded by:</b> {get_channel_tag()}\n\n"
            f"<i>Powered by Samra Cloud</i>"
        )
        
        if media_type == "a":
            await client.send_audio(
                chat_id=cb.message.chat.id,
                audio=file_path,
                caption=caption,
                title=title,
                performer="YouTube Pro",
                duration=duration_seconds,
                thumb=upload_thumb if upload_thumb and os.path.exists(upload_thumb) else None,
                progress=up_progress
            )
        else:
            await client.send_video(
                chat_id=cb.message.chat.id,
                video=file_path,
                caption=caption,
                duration=duration_seconds,
                thumb=upload_thumb if upload_thumb and os.path.exists(upload_thumb) else None,
                supports_streaming=True,
                progress=up_progress
            )
            
        await status_msg.delete()
        
        # Cleanup temp media and thumbnail
        if os.path.exists(file_path):
            os.remove(file_path)
        if upload_thumb and os.path.exists(upload_thumb):
            os.remove(upload_thumb)
            
    except Exception as err:
        await status_msg.edit_text(f"❌ <b>Download/Upload Failed:</b>\n<code>{err}</code>")
        if 'local_path' in locals() and os.path.exists(local_path):
            try:
                os.remove(local_path)
            except Exception:
                pass

if __name__ == "__main__":
    print("🚀 Starting Samra YouTube Downloader Bot...", flush=True)
    os.makedirs(cfg.DOWNLOAD_DIR, exist_ok=True)
    app.run()
