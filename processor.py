"""Core processing logic for downloading and saving articles."""
from datetime import date
from pathlib import Path
from email.utils import parsedate_to_datetime
from zoneinfo import ZoneInfo

import requests

from config import IST, UA, HASHTAGS
from utils import slugify, strip_html, ensure_unique_path, file_ext_from_url, build_caption
from feed_parser import load_feed, pick_image
from scraper import download_html, extract_article_text


def run_job(*, feed: str, out_root: str | Path, target_date: date, max_items: int | None,
            overwrite: bool):
    """
    Main processing function to download and save articles from RSS feed.
    
    Args:
        feed: RSS feed URL or local file path
        out_root: Output directory root path
        target_date: Date to filter articles (IST timezone)
        max_items: Maximum number of items to process (optional)
        overwrite: Whether to overwrite existing files
    
    Returns:
        Dictionary with processing results
    """
    out_root = Path(out_root)
    out_root.mkdir(parents=True, exist_ok=True)

    # Load and filter feed entries
    d = load_feed(feed)
    entries = []
    for e in d.entries:
        if getattr(e, "published", None):
            try:
                published = e.published
                if isinstance(published, str):
                    pub = parsedate_to_datetime(published)
                    if pub.tzinfo is None:
                        pub = pub.replace(tzinfo=ZoneInfo("UTC"))
                    pub_ist = pub.astimezone(IST)
                    if pub_ist.date() == target_date:
                        entries.append((pub_ist, e))
            except Exception:
                continue

    entries.sort(key=lambda x: x[0], reverse=True)
    if max_items:
        entries = entries[:max_items]

    # Create output directory structure
    y, m, dday = f"{target_date.year:04d}", f"{target_date.month:02d}", f"{target_date.day:02d}"
    day_dir = out_root / y / m / dday
    day_dir.mkdir(parents=True, exist_ok=True)

    # Setup session
    session = requests.Session()
    session.headers.update({"User-Agent": UA, "Accept": "*/*"})

    results = {
        "dir": str(day_dir.resolve()),
        "items": [],
        "count": 0
    }

    if not entries:
        return results

    # Process each entry
    for pub_ist, e in entries:
        title = e.title.strip()
        link = e.link.strip()
        slug = slugify(title)

        record = {
            "title": title,
            "link": link,
            "slug": slug,
            "paths": {},
            "image_saved": False,
            "errors": []
        }

        # Download HTML
        html_path = day_dir / f"{slug}.html"
        raw_html = ""
        try:
            raw_html = download_html(link, session)
            if html_path.exists() and not overwrite:
                html_path = ensure_unique_path(html_path)
            html_path.write_text(raw_html, encoding="utf-8")
            record["paths"]["html"] = str(html_path.relative_to(out_root))
        except Exception as ex:
            record["errors"].append(f"HTML download failed: {ex}")

        # Extract and save article text
        extracted_text = ""
        if raw_html:
            try:
                extracted_text = extract_article_text(raw_html, url=link)
                md_path = day_dir / f"{slug}.md"
                if md_path.exists() and not overwrite:
                    md_path = ensure_unique_path(md_path)
                md_path.write_text(extracted_text, encoding="utf-8")
                record["paths"]["md"] = str(md_path.relative_to(out_root))
            except Exception as ex:
                record["errors"].append(f"Extraction failed: {ex}")

        # Download image
        img_url = pick_image(e)
        if img_url:
            try:
                ext = file_ext_from_url(img_url)
                img_path = day_dir / f"{slug}{ext}"
                if img_path.exists() and not overwrite:
                    img_path = ensure_unique_path(img_path)
                with session.get(img_url, stream=True, timeout=45) as r:
                    r.raise_for_status()
                    with open(img_path, "wb") as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                record["paths"]["image"] = str(img_path.relative_to(out_root))
                record["image_saved"] = True
            except Exception as ex:
                record["errors"].append(f"Image download failed: {ex}")

        # Create caption with summary
        raw = strip_html(getattr(e, "summary", getattr(e, "description", "")))
        summary_text = (raw[:900] + "…") if len(raw) > 900 else raw

        caption = build_caption(title, summary_text, link, HASHTAGS)
        txt_path = day_dir / f"{slug}.txt"
        if txt_path.exists() and not overwrite:
            txt_path = ensure_unique_path(txt_path)
        txt_path.write_text(caption, encoding="utf-8")
        record["paths"]["txt"] = str(txt_path.relative_to(out_root))

        results["items"].append(record)

    results["count"] = len(results["items"])
    return results
