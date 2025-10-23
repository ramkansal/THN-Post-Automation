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
