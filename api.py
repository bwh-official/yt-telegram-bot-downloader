import asyncio
import aiohttp
import os
import time
from pyrogram.types import Message
from config import cfg

# Cache for video information: {video_id: {data: dict, timestamp: float}}
VIDEO_CACHE = {}

async def fetch_video_info(video_id_or_url: str) -> dict:
    """Fetch video metadata and direct download streams from the Samra YouTube API."""
    if video_id_or_url in VIDEO_CACHE:
        entry = VIDEO_CACHE[video_id_or_url]
        if time.time() - entry["timestamp"] < 900:  # 15 minutes cache
            return entry["data"]
            
    api_url = f"{cfg.API_BASE}/?url={video_id_or_url}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    timeout = aiohttp.ClientTimeout(total=20)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(api_url, headers=headers) as resp:
            if resp.status != 200:
                raise Exception(f"API returned status {resp.status}")
            data = await resp.json()
            if not data.get("success") and not data.get("status"):
                raise Exception(data.get("error", "Unable to retrieve video formats"))
                
            VIDEO_CACHE[video_id_or_url] = {
                "data": data,
                "timestamp": time.time()
            }
            if data.get("video_id"):
                VIDEO_CACHE[data["video_id"]] = {
                    "data": data,
                    "timestamp": time.time()
                }
            return data

async def download_file(url: str, output_path: str, progress_callback=None):
    """Download stream to local file with async chunks and progress tracking."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://youtube.com/"
    }
    
    timeout = aiohttp.ClientTimeout(total=1800)  # 30 mins max download
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status not in (200, 206):
                raise Exception(f"Failed to stream media: HTTP {resp.status}")
                
            total_size = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            start_time = time.time()
            last_edit = start_time
            
            with open(output_path, "wb") as f:
                async for chunk in resp.content.iter_chunked(1024 * 512): # 512KB chunks
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    now = time.time()
                    if progress_callback and (now - last_edit >= 3 or downloaded >= total_size):
                        last_edit = now
                        await progress_callback(downloaded, total_size, start_time, "📥 Downloading")
                        
    return output_path

async def download_thumbnail(video_id: str, thumb_url: str, output_path: str):
    """Download and prepare high-res JPG thumbnail for Telegram preview and video embeds."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    urls_to_try = [
        thumb_url,
        f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg",
        f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
        f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg"
    ]
    headers = {"User-Agent": "Mozilla/5.0"}
    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        for u in urls_to_try:
            if not u:
                continue
            try:
                async with session.get(u, headers=headers) as resp:
                    if resp.status == 200:
                        content = await resp.read()
                        if len(content) > 1000:
                            # Convert webp or other image formats to baseline RGB JPEG for Telegram
                            try:
                                from PIL import Image
                                import io
                                img = Image.open(io.BytesIO(content))
                                if img.mode != "RGB":
                                    img = img.convert("RGB")
                                img.thumbnail((320, 320))
                                img.save(output_path, "JPEG", quality=90)
                                return output_path
                            except Exception:
                                with open(output_path, "wb") as f:
                                    f.write(content)
                                return output_path
            except Exception:
                continue
    return None
