import re
import requests
from bs4 import BeautifulSoup

def download_html(url: str, session: requests.Session) -> str:
    r = session.get(url, timeout=45)
    r.raise_for_status()
    return r.text

def extract_article_text(html: str, url: str | None = None) -> str:
    soup = BeautifulSoup(html, "lxml")

    art = soup.find("article")
    if art:
        txt = art.get_text(" ", strip=True)
        if len(txt) > 400:
            return txt

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

    blocks = sorted(
        (el.get_text(" ", strip=True) for el in soup.find_all(["div", "section", "main", "article", "p"])),
        key=lambda t: len(t or ""),
        reverse=True,
    )
    for t in blocks:
        if len(t) > 600:
            return t

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

    return soup.get_text(" ", strip=True)