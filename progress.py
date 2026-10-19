import math
import time
from utils import format_size

def make_progress_bar(current, total, length=12):
    if total <= 0:
        return "▰▰▰▰▰▰▰▰▰▰▰▰"
    percent = current / total
    filled = int(length * percent)
    bar = "▰" * filled + "▱" * (length - filled)
    return bar

def render_progress_text(action: str, current: int, total: int, start_time: float, title: str = "") -> str:
    now = time.time()
    elapsed = max(now - start_time, 0.001)
    speed = current / elapsed
    
    percent_str = f"{(current / total * 100):.1f}%" if total > 0 else "Processing..."
    bar = make_progress_bar(current, total, length=12)
    
    cur_str = format_size(current)
    tot_str = format_size(total) if total > 0 else "Unknown"
    speed_str = f"{format_size(speed)}/s"
    
    eta = int((total - current) / speed) if speed > 0 and total > current else 0
    eta_str = f"{eta}s" if eta < 60 else f"{eta // 60}m {eta % 60}s"
    
    title_snippet = f"<b>Title:</b> <code>{title[:35]}...</code>\n" if title else ""
    
    text = (
        f"<b>⚡ {action} in Progress</b>\n\n"
        f"{title_snippet}"
        f"<code>[{bar}] {percent_str}</code>\n\n"
        f"📊 <b>Processed:</b> <code>{cur_str}</code> / <code>{tot_str}</code>\n"
        f"🚀 <b>Speed:</b> <code>{speed_str}</code>\n"
        f"⏳ <b>ETA:</b> <code>{eta_str}</code>"
    )
    return text
