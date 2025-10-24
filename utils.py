import os
import re
import html as ihtml
from pathlib import Path
from urllib.parse import urlsplit, unquote
from collections import deque
from time import time


class RateLimiter:

    def __init__(self, max_calls: int, window_seconds: int):
        self.max_calls = max_calls
        self.window = window_seconds
        self._events: dict[str, deque[float]] = {}

    def allow(self, key: str) -> bool:
        now = time()
        dq = self._events.setdefault(key, deque())
        cutoff = now - self.window
        while dq and dq[0] < cutoff:
            dq.popleft()
        if len(dq) >= self.max_calls:
            return False
        dq.append(now)
        return True


def slugify(s: str, maxlen: int = 80) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s)
    s = re.sub(r"^-+|-+$", "", s)
    return s[:maxlen].rstrip("-")


def strip_html(cdata: str) -> str:
    if not cdata:
        return ""
    text = re.sub(r"<[^>]+>", "", cdata)
    return ihtml.unescape(text).strip()


def ensure_unique_path(p: Path) -> Path:
    if not p.exists():
        return p
    stem, suf = p.stem, p.suffix
    i = 1
    while True:
        cand = p.with_name(f"{stem}-{i}{suf}")
        if not cand.exists():
            return cand
        i += 1


def file_ext_from_url(u: str) -> str:
    path = unquote(urlsplit(u).path)
    _, ext = os.path.splitext(path)
    if ext.lower() in (".jpg", ".jpeg", ".png", ".webp"):
        return ext
    return ".jpg"


def build_caption(title: str, summary: str, link: str, hashtags: str) -> str:
    return f"""{title}

{summary}

{link}

{hashtags}
"""
