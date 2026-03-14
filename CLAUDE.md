- For running code and dependencies use uv venv
- No new dependencies unless explicitly requested — prefer stdlib
- All output goes to `downloads/<post_id>/` by default (configurable in config.json)

## Project structure

```
config.py                    # shared project config loader (output_dir, gemini_model)
config.json                  # centralized settings
tiktok/                      # Python package
  scrape_post.py             # scrape TikTok post metadata via Apify
  scrape_comments.py         # scrape TikTok comments via Apify
  download_media.py          # download media assets (covers, avatar, music, subtitles, video)
  analyze_video.py           # analyze video using Gemini API
prompts/
  gemini_analyze.txt         # prompt template for Gemini video analysis
docs/
  gemini-pricing.md          # Gemini model pricing reference
```

## Usage

```bash
# Scrape post metadata
uv run scrape-post <tiktok-url> [--download-video]

# Download media assets from result
uv run download-media <result.json or post_id>

# Scrape comments
uv run scrape-comments <tiktok-url or post_id or result.json> [-n 100] [--replies 2]

# Analyze video with Gemini
uv run analyze-video <video.mp4 or post_id> [-p prompts/gemini_analyze.txt]
```

## Notes

- Video download requires paid Apify add-on (`--download-video` flag on scrape-post)
- CDN URLs (covers, music, avatar) expire — download promptly after scraping
- Comments use a separate Apify actor (`clockworks/tiktok-comments-scraper`), ~$0.005 per comment
- Subtitles are free and enabled by default in the scraper
- Gemini analysis requires GEMINI_API_KEY in .env, video must be <20MB
- Model and output directory are configurable in config.json
