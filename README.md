# THN Post Kit

A tool to download and process articles from The Hacker News RSS feed. Downloads HTML, extracts text, saves images, and creates social media captions.

## Project Structure

```
thn-post-automation/
├── app.py              # Main entry point
├── config.py           # Configuration settings
├── web.py              # Flask web application
├── processor.py        # Core processing logic
├── scraper.py          # Web scraping utilities
├── feed_parser.py      # RSS feed parsing
├── utils.py            # Utility functions
├── templates.py        # HTML templates
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## File Descriptions

### `app.py`
Main entry point for the application. Starts the Flask web server.

### `config.py`
Contains all configuration settings:
- Feed URLs
- Timezone settings
- User agent strings
- App title and output directories

### `web.py`
Flask web application with routes:
- `/` - Main form interface
- `/run` - Process articles
- `/o/` - Browse output files
- `/files/<path>` - Serve downloaded files

### `processor.py`
Core processing logic:
- Downloads articles from RSS feed
- Filters by date
- Saves HTML, markdown, images, and captions
- Handles errors gracefully

### `scraper.py`
Web scraping utilities:
- Downloads HTML content
- Extracts article text using multiple strategies
- Falls back to readability library if needed

### `feed_parser.py`
RSS feed parsing:
- Loads feeds from URL or local file
- Extracts image URLs from various feed formats

### `utils.py`
Utility functions:
- URL slugification
- HTML stripping
- Unique file path generation
- Caption building

### `templates.py`
HTML templates for the web interface using Tailwind CSS.

## Usage

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python app.py
   ```

3. Open browser to `http://localhost:5000`

4. Configure settings:
   - Feed URL (default: TheHackerNews)
   - Output directory
   - Target date (IST timezone)
   - Max items (optional)

5. Click "Run" to process articles

## Environment Variables

- `THN_OUT_DIR` - Output directory (default: `./THN`)
- `FLASK_SECRET` - Flask secret key (default: `dev-secret`)
- `PORT` - Server port (default: `5000`)

## Output Structure

```
THN/
└── YYYY/
    └── MM/
        └── DD/
            ├── article-slug.html      # Full HTML
            ├── article-slug.md        # Extracted text
            ├── article-slug.jpg       # Article image
            └── article-slug.txt       # Social media caption
```

## Features

- ✅ RSS feed parsing
- ✅ Date-based filtering (IST timezone)
- ✅ HTML download
- ✅ Article text extraction
- ✅ Image download
- ✅ Social media caption generation
- ✅ Web-based interface
- ✅ File browser
- ✅ Error handling
- ✅ Unique filename generation

## License

MIT
