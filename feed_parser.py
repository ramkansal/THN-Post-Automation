"""Feed parsing and image extraction utilities."""
import os
import feedparser


def load_feed(feed_source: str):
    """Load RSS feed from URL or local file."""
    if os.path.exists(feed_source):
        with open(feed_source, "rb") as f:
            data = f.read()
        return feedparser.parse(data)
    return feedparser.parse(feed_source)


def pick_image(entry) -> str | None:
    """Extract image URL from feed entry."""
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
