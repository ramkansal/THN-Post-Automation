"""Web scraping and article extraction utilities."""
import re
import requests
from bs4 import BeautifulSoup


def download_html(url: str, session: requests.Session) -> str:
    """Download HTML content from URL."""
    r = session.get(url, timeout=45)
    r.raise_for_status()
    return r.text


def extract_article_text(html: str, url: str | None = None) -> str:
    """Extract article text from HTML."""
    soup = BeautifulSoup(html, "lxml")

    # Try to find article tag
    art = soup.find("article")
    if art:
        txt = art.get_text(" ", strip=True)
        if len(txt) > 400:
            return txt

    # Try to find post-body div
    cand = soup.find("div", id=re.compile(r"^post-body", re.I))
    if cand:
        txt = cand.get_text(" ", strip=True)
        if len(txt) > 400:
            return txt

    # Try specific class selector
    cand = soup.select_one("div.post-body.entry-content")
    if cand:
        txt = cand.get_text(" ", strip=True)
        if len(txt) > 400:
            return txt

    # Find largest text block
    blocks = sorted(
        (el.get_text(" ", strip=True) for el in soup.find_all(["div", "section", "main", "article", "p"])),
        key=lambda t: len(t or ""),
        reverse=True,
    )
    for t in blocks:
        if len(t) > 600:
            return t

    # Try readability as fallback
    try:
        from readability import Document
        doc = Document(html)
        main_html = doc.summary()
        s2 = BeautifulSoup(main_html, "lxml")
        t2 = s2.get_text(" ", strip=True)
        if len(t2) > 200:
            return t2
    except Exception:
        pass

    # Final fallback: return all text
    return soup.get_text(" ", strip=True)
