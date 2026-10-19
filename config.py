import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    API_ID = int(os.environ.get("API_ID", 12345678))
    API_HASH = os.environ.get("API_HASH", "your_api_hash_here")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz")
    ADMIN_ID = int(os.environ.get("ADMIN_ID", 123456789))
    
    # API Endpoint
    API_BASE = os.environ.get("API_BASE", "https://samra-youtube-api.krishnalucky193.workers.dev")
    
    # Bot session string or persistent session file
    BOT_SESSION = os.environ.get("BOT_SESSION", "")
    
    # Download temp path
    DOWNLOAD_DIR = os.environ.get("DOWNLOAD_DIR", "./downloads")

cfg = Config()
