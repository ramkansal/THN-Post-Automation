"""Configuration settings for THN Post Kit."""
import os
from zoneinfo import ZoneInfo

# Feed Configuration
DEFAULT_FEED = "https://feeds.feedburner.com/TheHackersNews?format=xml"

# Timezone
IST = ZoneInfo("Asia/Kolkata")

# User Agent
UA = "thn-post-kit/2.0 (+https://thehackernews.com)"

# Hashtags for captions
HASHTAGS = "#cybersecurity #infosec #TheHackerNews"

# App Configuration
APP_TITLE = "THN Post Kit"
DEFAULT_OUT = os.environ.get("THN_OUT_DIR", "./THN")
FLASK_SECRET = os.environ.get("FLASK_SECRET", "dev-secret")
PORT = int(os.environ.get("PORT", 5000))
