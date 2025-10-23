#!/usr/bin/env python3

from config import PORT
from web import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)
