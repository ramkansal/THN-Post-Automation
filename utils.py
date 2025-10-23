"""Utility functions for text processing and file handling."""
import os
import re
import html as ihtml
from pathlib import Path
from urllib.parse import urlsplit, unquote


def slugify(s: str, maxlen: int = 80) -> str:
    """Convert a string to a URL-friendly slug."""
    s = s.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)  # drop punctuation
    s = re.sub(r"[\s_-]+", "-", s)  # collapse
    s = re.sub(r"^-+|-+$", "", s)   # trim hyphens
    return s[:maxlen].rstrip("-")


def strip_html(cdata: str) -> str:
    """Strip HTML tags from content."""
    if not cdata:
        return ""
    text = re.sub(r"<[^>]+>", "", cdata)
    return ihtml.unescape(text).strip()


def ensure_unique_path(p: Path) -> Path:
    """Ensure a file path is unique by appending numbers if needed."""
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
    """Extract file extension from URL."""
    path = unquote(urlsplit(u).path)
    _, ext = os.path.splitext(path)
    if ext.lower() in (".jpg", ".jpeg", ".png", ".webp"):
        return ext
    return ".jpg"


def build_caption(title: str, summary: str, link: str, hashtags: str) -> str:
    """Build a caption for social media posts."""
    return f"""{title}

{summary}

{link}

{hashtags}
"""
