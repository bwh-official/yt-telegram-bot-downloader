import re
from urllib.parse import urlparse, parse_qs

def extract_video_id(url_or_text: str) -> str:
    """Extract YouTube video ID from various URL formats or raw video ID."""
    text = url_or_text.strip()
    
    # 1. Plain 11-char ID
    if len(text) == 11 and re.match(r"^[a-zA-Z0-9_-]{11}$", text):
        return text
        
    # 2. Regex for URLs
    patterns = [
        r'(?:https?:\/\/)?(?:www\.)?youtu\.be\/([a-zA-Z0-9_-]{11})',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/(?:watch\?v=|embed\/|v\/|shorts\/|live\/)([a-zA-Z0-9_-]{11})',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/.*[?&]v=([a-zA-Z0-9_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
            
    return None

def parse_duration_seconds(duration_raw) -> int:
    """Safely convert seconds, float, or string durations to int seconds."""
    if not duration_raw:
        return 0
    try:
        if isinstance(duration_raw, (int, float)):
            return int(duration_raw)
        raw_str = str(duration_raw).strip()
        # format: "3.55 min"
        if "min" in raw_str:
            num = float(raw_str.replace("min", "").strip())
            return int(num * 60)
        # format: "03:45" or "01:20:15"
        if ":" in raw_str:
            parts = [int(p) for p in raw_str.split(":")]
            if len(parts) == 3:
                return parts[0] * 3600 + parts[1] * 60 + parts[2]
            elif len(parts) == 2:
                return parts[0] * 60 + parts[1]
        return int(float(raw_str))
    except Exception:
        return 0

def format_duration(seconds) -> str:
    try:
        sec = parse_duration_seconds(seconds)
        if sec <= 0:
            return "N/A"
        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"
    except Exception:
        return "N/A"

def format_size(bytes_num) -> str:
    try:
        bytes_num = float(bytes_num)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_num < 1024.0:
                return f"{bytes_num:.1f} {unit}"
            bytes_num /= 1024.0
        return f"{bytes_num:.1f} TB"
    except Exception:
        return "N/A"

CACHED_SUFFIX = None

def get_channel_tag() -> str:
    """Fetch username suffix dynamically from public telegram link so it's not hardcoded in plain text."""
    global CACHED_SUFFIX
    if CACHED_SUFFIX:
        return CACHED_SUFFIX
        
    try:
        import urllib.request
        req = urllib.request.Request("https://t.me/desibotz/21", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
            # Extract main channel username link
            m = re.search(r'class="tgme_channel_info_header_username"[^>]*>@([a-zA-Z0-9_]+)<', html)
            if not m:
                m = re.search(r'@(desibotz\w*)', html, re.IGNORECASE)
            if m:
                CACHED_SUFFIX = f"@{m.group(1)}"
                return CACHED_SUFFIX
    except Exception:
        pass
        
    # Obfuscated fallback byte representation of '@desibotz'
    # Prevents anyone from finding/replacing plain text '@desibotz' in github search
    CACHED_SUFFIX = bytes([64, 100, 101, 115, 105, 98, 111, 116, 122]).decode('utf-8')
    return CACHED_SUFFIX

def make_safe_filename(title: str, quality: str, ext: str) -> str:
    """
    Format filename:
    Output format: Title @desibotz.mp4
    Dynamic tag resolved from https://t.me/desibotz/21
    """
    # Clean special filesystem characters
    cleaned_title = re.sub(r'[\\/*?:"<>|]', '', title).strip()
    if not cleaned_title:
        cleaned_title = "YouTube_Media"
    cleaned_title = cleaned_title[:65].strip()
    
    tag = get_channel_tag()
    filename = f"{cleaned_title} {tag}.{ext}"
    return filename
