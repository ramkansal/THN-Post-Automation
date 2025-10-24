from datetime import datetime
from pathlib import Path

from flask import Flask, request, redirect, url_for, render_template_string, send_from_directory, abort, flash

from config import APP_TITLE, DEFAULT_FEED, DEFAULT_OUT, FLASK_SECRET, IST
from processor import run_job
from templates import INDEX_TEMPLATE, RESULTS_TEMPLATE, BROWSER_TEMPLATE


app = Flask(__name__)
app.secret_key = FLASK_SECRET

BASE_OUT = Path(DEFAULT_OUT).resolve()
BASE_OUT.mkdir(parents=True, exist_ok=True)


def _safe_path(rel_path: str) -> Path:
    p = (BASE_OUT / rel_path).resolve()
    if not str(p).startswith(str(BASE_OUT)):
        raise ValueError("Path escape blocked")
    return p


@app.route("/", methods=["GET"])
def index():
    today = datetime.now(IST).date().isoformat()
    return render_template_string(
        INDEX_TEMPLATE,
        title=APP_TITLE,
        feed=DEFAULT_FEED,
        out_root=str(BASE_OUT),
        today=today,
    )


@app.route("/run", methods=["POST"])
def run():
    feed = request.form.get("feed", DEFAULT_FEED).strip()
    out_root = request.form.get("out_root", str(BASE_OUT)).strip()
    date_str = request.form.get("date")
    max_items = request.form.get("max_items")
    overwrite = bool(request.form.get("overwrite"))

    if not date_str:
        flash("Date is required.")
        return redirect(url_for("index"))

    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        flash("Invalid date.")
        return redirect(url_for("index"))

    try:
        res = run_job(
            feed=feed,
            out_root=out_root,
            target_date=target_date,
            max_items=int(max_items) if max_items else None,
            overwrite=overwrite,
        )
    except Exception as e:
        flash(f"Run failed: {e}")
        return redirect(url_for("index"))

    return render_template_string(
        RESULTS_TEMPLATE,
        title=APP_TITLE,
        target_date=target_date.isoformat(),
        root=res["dir"],
        items=res["items"],
        count=res["count"],
    )


@app.route("/o/")
def browse_root():
    entries = []
    for p in sorted(BASE_OUT.iterdir()):
        href = url_for("browse_dir", relpath=p.name) if p.is_dir() else url_for("serve_file", relpath=p.name)
        entries.append({"name": p.name, "type": "dir" if p.is_dir() else "file", "href": href})
    return render_template_string(BROWSER_TEMPLATE, title=APP_TITLE, root=str(BASE_OUT), entries=entries)


@app.route("/o/<path:relpath>")
def browse_dir(relpath):
    try:
        p = _safe_path(relpath)
    except Exception:
        abort(404)
    if not p.exists():
        abort(404)

    if p.is_file():
        return redirect(url_for("serve_file", relpath=relpath))
    
    # Detect if this looks like a "day" directory containing article files (txt/md/html/image by slug)
    files = [c for c in p.iterdir() if c.is_file()]
    has_article_texts = any(c.suffix.lower() in (".txt", ".md") for c in files)

    if has_article_texts:
        # Group by slug (stem without extension, ignoring '-1' style duplicates by keeping exact stem)
        by_slug = {}
        for f in files:
            stem = f.stem
            by_slug.setdefault(stem, []).append(f)

        items = []
        for slug, fpaths in sorted(by_slug.items()):
            # Build paths map
            paths = {}
            title = slug
            link = ""

            # Prefer .txt to derive title/link; fallback to .md
            txt_file = next((fp for fp in fpaths if fp.suffix.lower() == ".txt"), None)
            md_file = next((fp for fp in fpaths if fp.suffix.lower() == ".md"), None)
            html_file = next((fp for fp in fpaths if fp.suffix.lower() == ".html"), None)
            img_file = next((fp for fp in fpaths if fp.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")), None)

            def relstr(fp):
                try:
                    return str(fp.relative_to(BASE_OUT))
                except Exception:
                    return str(fp)

            if html_file:
                paths["html"] = relstr(html_file)
            if md_file:
                paths["md"] = relstr(md_file)
            if txt_file:
                paths["txt"] = relstr(txt_file)
            if img_file:
                paths["image"] = relstr(img_file)

            # Parse caption to extract title and link
            src = txt_file or md_file
            if src and src.exists():
                try:
                    content = src.read_text(encoding="utf-8", errors="ignore")
                    # Title: first non-empty line
                    for line in content.splitlines():
                        if line.strip():
                            title = line.strip()
                            break
                    # Link: first line that looks like a URL
                    for line in content.splitlines():
                        ls = line.strip()
                        if ls.startswith("http://") or ls.startswith("https://"):
                            link = ls
                            break
                except Exception:
                    pass

            items.append({
                "title": title,
                "link": link,
                "slug": slug,
                "paths": paths,
                "image_saved": img_file is not None,
                "errors": [],
            })

        # Try to detect target date from path (…/YYYY/MM/DD)
        try:
            relp = p.relative_to(BASE_OUT)
            parts = relp.parts
            target_label = str(p)
            if len(parts) >= 3 and all(part.isdigit() for part in parts[-3:]):
                y, m, d = parts[-3:]
                target_label = f"{y}-{m}-{d}"
        except Exception:
            target_label = str(p.name)

        return render_template_string(
            RESULTS_TEMPLATE,
            title=APP_TITLE,
            target_date=target_label,
            root=str(p),
            items=items,
            count=len(items),
        )

    # Default: show standard browser grid for non-article directories
    entries = []
    for c in sorted(p.iterdir()):
        sub = f"{relpath}/{c.name}"
        href = url_for("browse_dir", relpath=sub) if c.is_dir() else url_for("serve_file", relpath=sub)
        entries.append({"name": c.name, "type": "dir" if c.is_dir() else "file", "href": href})

    return render_template_string(BROWSER_TEMPLATE, title=APP_TITLE, root=str(p), entries=entries)


@app.route("/files/<path:relpath>")
def serve_file(relpath):
    try:
        p = _safe_path(relpath)
    except Exception:
        abort(404)
    if not p.exists() or not p.is_file():
        abort(404)
    return send_from_directory(directory=str(p.parent), path=p.name, as_attachment=False)


@app.context_processor
def inject_urls():
    return {"serve_file": serve_file}
