#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
THN Post Kit - Main Entry Point

A tool to download and process articles from The Hacker News RSS feed.
Downloads HTML, extracts text, saves images, and creates social media captions.
"""

from config import PORT
from web import app

if __name__ == "__main__":
    # Run development server
    app.run(host="0.0.0.0", port=PORT, debug=True)
