#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prepare daily LinkedIn-ready post kits from The Hacker News RSS.
Creates: YYYY/MM/DD/<slug>.{jpg|png} (cover image),
         YYYY/MM/DD/<slug>.html (raw),
         YYYY/MM/DD/<slug>.md (extracted),
         YYYY/MM/DD/<slug>.txt (final caption with 150-200 word summary).

Optional: summarize with DeepSeek (LLM). If disabled, falls back to RSS summary.
Time zone: Asia/Kolkata (IST).
"""
import argparse
import html as ihtml
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, date
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlsplit, unquote
from zoneinfo import ZoneInfo

import requests
import feedparser
from bs4 import BeautifulSoup

# --- Config -------------------------------------------------------------------
DEFAULT_FEED = "https://feeds.feedburner.com/TheHackersNews?format=xml"
IST = ZoneInfo("Asia/Kolkata")
UA = "thn-post-kit/2.0 (+https://thehackernews.com)"

HASHTAGS = "#cybersecurity #infosec #TheHackerNews"  # customize if needed

# --- Helpers ------------------------------------------------------------------
def slugify(s: str, maxlen: int = 80) -> str:
    s = s.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)         # drop punctuation
    s = re.sub(r"[\s_-]+", "-", s)         # collapse
    s = re.sub(r"^-+|-+$", "", s)          # trim hyphens
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

def pick_image(entry) -> str | None:
    # Prefer RSS enclosures with image/*
    if getattr(entry, "enclosures", None):
        for enc in entry.enclosures:
            if "type" in enc and isinstance(enc["type"], str) and enc["type"].startswith("image/"):
                return enc.get("href") or enc.get("url")
    # media_content
    if getattr(entry, "media_content", None):
        for m in entry.media_content:
            if "url" in m:
                return m["url"]
    # Generic enclosure link
    if getattr(entry, "links", None):
        for l in entry.links:
            if l.get("rel") == "enclosure" and l.get("type", "").startswith("image/"):
                return l.get("href")
    return None

# --- Article fetching & extraction --------------------------------------------
def download_html(url: str, session: requests.Session) -> str:
    r = session.get(url, timeout=45)
    r.raise_for_status()
    return r.text

def extract_article_text(html: str, url: str | None = None) -> str:
    """
    Heuristics tuned for The Hacker News (Blogger) + readability fallback:
    - Try <article>, then div[id^=post-body], then div.post-body, then biggest text block
    - If readability-lxml is available, use it as a strong fallback
    """
    soup = BeautifulSoup(html, "lxml")

    # 1) <article>
    art = soup.find("article")
    if art:
        txt = art.get_text(" ", strip=True)
        if len(txt) > 400:
            return txt

    # 2) Blogger-ish containers
    cand = soup.find("div", id=re.compile(r"^post-body", re.I))
    if cand:
        txt = cand.get_text(" ", strip=True)
        if len(txt) > 400:
            return txt

    cand = soup.select_one("div.post-body.entry-content")
    if cand:
        txt = cand.get_text(" ", strip=True)
        if len(txt) > 400:
            return txt

    # 3) Biggest text block heuristic
    blocks = sorted(
        (el.get_text(" ", strip=True) for el in soup.find_all(["div","section","main","article","p"])),
        key=lambda t: len(t or ""),
        reverse=True,
    )
    for t in blocks:
        if len(t) > 600:
            return t

    # 4) readability fallback if installed
    try:
        from readability import Document  # readability-lxml
        doc = Document(html)
        main_html = doc.summary()
        s2 = BeautifulSoup(main_html, "lxml")
        t2 = s2.get_text(" ", strip=True)
        if len(t2) > 200:
            return t2
    except Exception:
        pass

    # 5) Final fallback: whole-page text (last resort)
    return soup.get_text(" ", strip=True)

# --- LLM (DeepSeek) -----------------------------------------------------------
@dataclass
class LLMConfig:
    provider: str = "none"   # "none" or "deepseek"
    model: str = "deepseek-chat"  # or "deepseek-reasoner" etc.
    api_key: str | None = None
    input_mode: str = "text"  # "text" or "html"
    words: int = 180
    temperature: float = 0.2
    max_tokens: int = 600

def summarize_with_deepseek(content: str, cfg: LLMConfig, title: str) -> str:
    if not cfg.api_key:
        raise RuntimeError("DEEPSEEK_API_KEY missing")

    url = "https://api.deepseek.com/chat/completions"
    sys_prompt = (
        "You are a concise cybersecurity news editor. Summarize faithfully with no hype.\n"
        "Rules:\n"
        f"- 150–200 words (target {cfg.words}).\n"
        "- Cover: what happened, who/what is affected, impact/risk, and any concrete mitigation or next steps.\n"
        "- No emojis, no clickbait, no markdown headings. 1–2 short paragraphs max.\n"
        "- Do NOT invent details. If unsure, omit.\n"
    )
    user_prompt = (
        f"Title: {title}\n\n"
        "Summarize the following article under 200 words (minimum 150). "
        "Return plain text only.\n\n"
        "=== BEGIN CONTENT ===\n" + content + "\n=== END CONTENT ==="
    )

    headers = {
        "Authorization": f"Bearer {cfg.api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": cfg.model,
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": cfg.temperature,
        "max_tokens": cfg.max_tokens,
    }

    for attempt in range(3):
        try:
            r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=90)
            if r.status_code in (429, 500, 502, 503, 504) and attempt < 2:
                time.sleep(1.5 * (attempt + 1))
                continue
            r.raise_for_status()
            j = r.json()
            return j["choices"][0]["message"]["content"].strip()
        except Exception as e:
            if attempt == 2:
                raise
            time.sleep(1.5 * (attempt + 1))

# --- CLI ----------------------------------------------------------------------
def parse_args():
    ap = argparse.ArgumentParser(description="Build local post kits from THN with optional LLM summary")
    ap.add_argument("--feed", default=DEFAULT_FEED, help="RSS feed URL or path to a local XML file")
    ap.add_argument("--out", default=".", help="Output root directory")
    ap.add_argument("--date", dest="date_str", default=None, help="Target date in YYYY-MM-DD (IST). Default: today (IST)")
    ap.add_argument("--max", dest="max_items", type=int, default=None, help="Max number of items to export (per day)")
    ap.add_argument("--overwrite", action="store_true", help="Overwrite existing files if they exist")
    # LLM
    ap.add_argument("--llm", choices=["none", "deepseek"], default="none", help="Use an LLM to generate summaries")
    ap.add_argument("--llm-model", default="deepseek-chat", help="DeepSeek model (e.g., deepseek-chat)")
    ap.add_argument("--llm-input", choices=["text", "html"], default="text",
                    help="Send extracted article TEXT or full HTML to the LLM")
    ap.add_argument("--summary-words", type=int, default=180, help="Target words for summary (150–200 recommended)")
    return ap.parse_args()

def load_feed(feed_source: str):
    if os.path.exists(feed_source):
        with open(feed_source, "rb") as f:
            data = f.read()
        return feedparser.parse(data)
    return feedparser.parse(feed_source)

def build_caption(title: str, summary: str, link: str) -> str:
    return f"""{title}

{summary}

{link}

{HASHTAGS}
"""

def main():
    args = parse_args()

    target_date: date = (
        datetime.now(tz=IST).date()
        if not args.date_str else datetime.strptime(args.date_str, "%Y-%m-%d").date()
    )
    out_root = Path(args.out)

    d = load_feed(args.feed)
    if d.bozo:
        print(f"[!] RSS parse warning: {getattr(d, 'bozo_exception', 'unknown')}", file=sys.stderr)

    # Collect entries for the target day (IST)
    day_entries = []
    for e in d.entries:
        if getattr(e, "published", None):
            try:
                pub = parsedate_to_datetime(e.published)
                if pub.tzinfo is None:
                    pub = pub.replace(tzinfo=ZoneInfo("UTC"))
                pub_ist = pub.astimezone(IST)
                if pub_ist.date() == target_date:
                    day_entries.append((pub_ist, e))
            except Exception:
                continue

    day_entries.sort(key=lambda x: x[0], reverse=True)
    if args.max_items:
        day_entries = day_entries[:args.max_items]

    y, m, dday = f"{target_date.year:04d}", f"{target_date.month:02d}", f"{target_date.day:02d}"
    day_dir = out_root / y / m / dday
    day_dir.mkdir(parents=True, exist_ok=True)

    if not day_entries:
        print(f"[i] No THN items on {target_date.isoformat()} (IST).")
        return

    # Session
    session = requests.Session()
    session.headers.update({"User-Agent": UA, "Accept": "*/*"})

    # LLM config
    llm_cfg = LLMConfig(
        provider=args.llm,
        model=args.llm_model,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        input_mode=args.llm_input,
        words=args.summary_words,
    )

    created = 0
    for pub_ist, e in day_entries:
        title = e.title.strip()
        link = e.link.strip()
        slug = slugify(title)

        # --- Save RAW HTML -----------------------------------------------------
        html_path = day_dir / f"{slug}.html"
        try:
            raw_html = download_html(link, session)
            if html_path.exists() and not args.overwrite:
                html_path = ensure_unique_path(html_path)
            html_path.write_text(raw_html, encoding="utf-8")
        except Exception as ex:
            print(f"[!] HTML download failed for {link}: {ex}", file=sys.stderr)
            raw_html = ""

        # --- Extract TEXT + save ----------------------------------------------
        extracted_text = ""
        md_path = day_dir / f"{slug}.md"
        if raw_html:
            try:
                extracted_text = extract_article_text(raw_html, url=link)
                if md_path.exists() and not args.overwrite:
                    md_path = ensure_unique_path(md_path)
                md_path.write_text(extracted_text, encoding="utf-8")
            except Exception as ex:
                print(f"[!] Extraction failed for {link}: {ex}", file=sys.stderr)

        # --- Image -------------------------------------------------------------
        img_url = pick_image(e)
        if img_url:
            ext = file_ext_from_url(img_url)
            img_path = day_dir / f"{slug}{ext}"
            if img_path.exists() and not args.overwrite:
                img_path = ensure_unique_path(img_path)
            try:
                with session.get(img_url, stream=True, timeout=45) as r:
                    r.raise_for_status()
                    with open(img_path, "wb") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
            except Exception as ex:
                print(f"[!] Failed image download: {img_url} → {ex}", file=sys.stderr)

        # --- Summary (LLM or fallback) ----------------------------------------
        summary_text = ""
        if llm_cfg.provider == "deepseek":
            try:
                llm_input = raw_html if (llm_cfg.input_mode == "html" and raw_html) else (extracted_text or strip_html(getattr(e, "summary", "")))
                if not llm_input:
                    llm_input = strip_html(getattr(e, "description", "")) or link
                summary_text = summarize_with_deepseek(llm_input, llm_cfg, title=title)
            except Exception as ex:
                print(f"[!] LLM summarize failed, falling back: {ex}", file=sys.stderr)

        if not summary_text:
            # Fallback: RSS summary trimmed
            raw = strip_html(getattr(e, "summary", getattr(e, "description", "")))
            summary_text = (raw[:900] + "…") if len(raw) > 900 else raw

        # --- Final caption -----------------------------------------------------
        caption = build_caption(title, summary_text, link)
        txt_path = day_dir / f"{slug}.txt"
        if txt_path.exists() and not args.overwrite:
            txt_path = ensure_unique_path(txt_path)
        txt_path.write_text(caption, encoding="utf-8")

        created += 1
        print(f"[+] {slug}: html+md+caption" + ("+image" if img_url else ""))

    print(f"[✓] Done. {created} post kit(s) in {day_dir}")

if __name__ == "__main__":
    main()
