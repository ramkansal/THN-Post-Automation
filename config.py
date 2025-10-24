import os
from zoneinfo import ZoneInfo

DEFAULT_FEED = "https://feeds.feedburner.com/TheHackersNews?format=xml"
IST = ZoneInfo("Asia/Kolkata")
UA = "thn-post-kit/2.0 (+https://thehackernews.com)"
HASHTAGS = "#CyberSecurity #InfoSec #Hacking #DataBreach #CyberAttack #ThreatIntel #SecurityNews #CyberThreat #Ransomware"
APP_TITLE = "THN Post Kit"
DEFAULT_OUT = os.environ.get("THN_OUT_DIR", "./THN")
FLASK_SECRET = os.environ.get("FLASK_SECRET")
PORT = int(os.environ.get("PORT", 5000))

RATE_LIMIT_FEED_CALLS = int(os.environ.get("RATE_LIMIT_FEED_CALLS", 10))
RATE_LIMIT_WINDOW_SEC = int(os.environ.get("RATE_LIMIT_WINDOW_SEC", 60))

ALLOW_ONLY_DEFAULT_FEED = os.environ.get("ALLOW_ONLY_DEFAULT_FEED", "1") not in ("0", "false", "False")
