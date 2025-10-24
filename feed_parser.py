import os
import feedparser
from urllib.parse import urlparse

from config import DEFAULT_FEED, RATE_LIMIT_FEED_CALLS, RATE_LIMIT_WINDOW_SEC, ALLOW_ONLY_DEFAULT_FEED
from utils import RateLimiter


_limiter = RateLimiter(RATE_LIMIT_FEED_CALLS, RATE_LIMIT_WINDOW_SEC)


def load_feed(feed_source: str):
    if os.path.exists(feed_source):
        with open(feed_source, "rb") as f:
            data = f.read()
        return feedparser.parse(data)

    try:
        parsed = urlparse(feed_source)
        is_url = parsed.scheme in ("http", "https")
    except Exception:
        is_url = False

    if is_url:
        if ALLOW_ONLY_DEFAULT_FEED and feed_source != DEFAULT_FEED:
            raise ValueError("External feeds are not allowed. Use the default RSS feed only.")

        key = DEFAULT_FEED if ALLOW_ONLY_DEFAULT_FEED else feed_source
        if not _limiter.allow(key):
            raise RuntimeError("Rate limit exceeded for RSS fetches. Please try again later.")

    return feedparser.parse(feed_source)


def pick_image(entry) -> str | None:
    if getattr(entry, "enclosures", None):
        for enc in entry.enclosures:
            if "type" in enc and isinstance(enc["type"], str) and enc["type"].startswith("image/"):
                return enc.get("href") or enc.get("url")
    
    if getattr(entry, "media_content", None):
        for m in entry.media_content:
            if "url" in m:
                return m["url"]
    
    if getattr(entry, "links", None):
        for l in entry.links:
            if l.get("rel") == "enclosure" and l.get("type", "").startswith("image/"):
                return l.get("href")
    
    return None
