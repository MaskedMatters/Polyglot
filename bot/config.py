import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
ALLOWED_CHANNEL_NAME = os.getenv("ALLOWED_CHANNEL_NAME", "languages").strip().lower()
ALLOWED_CHANNEL_ID = os.getenv("ALLOWED_CHANNEL_ID")
if ALLOWED_CHANNEL_ID:
    try:
        ALLOWED_CHANNEL_ID = int(ALLOWED_CHANNEL_ID)
    except ValueError:
        ALLOWED_CHANNEL_ID = None

GUILD_ID = os.getenv("GUILD_ID")
if GUILD_ID:
    try:
        GUILD_ID = int(GUILD_ID)
    except ValueError:
        GUILD_ID = None

DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE", "America/New_York")
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/polyglot.db")
BOT_NAME = os.getenv("BOT_NAME", "Polyglot")

try:
    MORNING_REPORT_HOUR = int(os.getenv("MORNING_REPORT_HOUR", "8"))
    MORNING_REPORT_MINUTE = int(os.getenv("MORNING_REPORT_MINUTE", "0"))
except ValueError:
    MORNING_REPORT_HOUR = 8
    MORNING_REPORT_MINUTE = 0

