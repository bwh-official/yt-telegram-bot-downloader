from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import cfg

def build_start_markup():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✨ How to Use", callback_data="help_guide"),
            InlineKeyboardButton("⚡ Developer", url="https://t.me/sheffysamra1bot")
        ],
        [
            InlineKeyboardButton("🌐 Fast Web Downloader", url=cfg.API_BASE)
        ]
    ])

def build_help_markup():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔙 Back to Home", callback_data="start_home")
        ]
    ])

def build_download_options_markup(video_data: dict) -> InlineKeyboardMarkup:
    """Build premium categorized buttons for all video resolutions + MP3 options."""
    video_id = video_data.get("video_id", "")
    buttons = []
    
    # 1. MP3 Audio Section (320kbps & 128kbps)
    audio_row = [
        InlineKeyboardButton("🎵 MP3 (320k)", callback_data=f"dl_a_{video_id}_320"),
        InlineKeyboardButton("🎵 MP3 (128k)", callback_data=f"dl_a_{video_id}_128")
    ]
    buttons.append(audio_row)
    
    # 2. Extract and organize Video Resolutions
    available_qualities = video_data.get("availableQuality", [])
    
    # Also check if downloads list has specific qualities
    all_q_set = set()
    for q in available_qualities:
        all_q_set.add(int(q))
        
    for d in video_data.get("downloads", []):
        if d.get("type") == "video" or (d.get("format") == "mp4" and "audio" not in str(d.get("quality", "")).lower()):
            q_clean = str(d.get("quality", "")).replace("p", "")
            if q_clean.isdigit():
                all_q_set.add(int(q_clean))
                
    # Sort qualities in descending order: 2160, 1440, 1080, 720, 480, 360, 240, 144
    sorted_qualities = sorted(list(all_q_set), reverse=True)
    if not sorted_qualities:
        sorted_qualities = [1080, 720, 480, 360]
        
    # Group video buttons into rows of 2 or 3
    video_row = []
    for q in sorted_qualities:
        label = f"🎬 {q}p"
        if q >= 2160:
            label = f"🌟 4K ({q}p)"
        elif q >= 1440:
            label = f"✨ 2K ({q}p)"
        elif q >= 1080:
            label = f"💎 1080p"
        elif q >= 720:
            label = f"HD 720p"
            
        video_row.append(InlineKeyboardButton(label, callback_data=f"dl_v_{video_id}_{q}"))
        if len(video_row) == 2:
            buttons.append(video_row)
            video_row = []
            
    if video_row:
        buttons.append(video_row)
        
    # 3. Direct Streaming / Browser link button
    direct_link = video_data.get("direct_stream_link") or f"{cfg.API_BASE}/?url={video_id}"
    buttons.append([
        InlineKeyboardButton("🌐 Direct Stream / Web Player", url=direct_link)
    ])
    
    # 4. Close button
    buttons.append([
        InlineKeyboardButton("❌ Close Menu", callback_data="close_menu")
    ])
    
    return InlineKeyboardMarkup(buttons)
