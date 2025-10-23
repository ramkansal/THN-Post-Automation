import os
from zoneinfo import ZoneInfo

DEFAULT_FEED = "https://feeds.feedburner.com/TheHackersNews?format=xml"
IST = ZoneInfo("Asia/Kolkata")
UA = "thn-post-kit/2.0 (+https://thehackernews.com)"
HASHTAGS = "#cybersecurity #infosec #TheHackerNews"
APP_TITLE = "THN Post Kit"
DEFAULT_OUT = os.environ.get("THN_OUT_DIR", "./THN")
FLASK_SECRET = os.environ.get("FLASK_SECRET")
PORT = int(os.environ.get("PORT", 5000))
