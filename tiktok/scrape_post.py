import argparse
import json
import os
import sys

from apify_client import ApifyClient
from dotenv import load_dotenv

from config import output_dir

load_dotenv()

ACTOR_ID = "clockworks/tiktok-scraper"


def scrape_tiktok_post(url: str, download_video: bool = False) -> list[dict]:
    token = os.environ.get("APIFY_API_TOKEN")
    if not token:
        print("Error: APIFY_API_TOKEN not set. Copy .env.example to .env and add your token.", file=sys.stderr)
        sys.exit(1)

    client = ApifyClient(token)

    run_input = {
        "postURLs": [url],
        "resultsPerPage": 1,
        # Paid add-on — only enabled via --download-video flag
        "shouldDownloadVideos": download_video,
        # Explicitly disable other charged add-ons
        "shouldDownloadCovers": False,
        "shouldDownloadSlideshowImages": False,
        "shouldDownloadAvatars": False,
        "shouldDownloadMusicCovers": False,
        # Free — provides .vtt subtitle files + CDN video links
        "downloadSubtitlesOptions": "DOWNLOAD_SUBTITLES",
        "commentsPerPost": 0,
        "maxRepliesPerComment": 0,
        "maxFollowersPerProfile": 0,
        "maxFollowingPerProfile": 0,
        "scrapeRelatedVideos": False,
        "proxyCountryCode": "None",
    }

    run = client.actor(ACTOR_ID).call(run_input=run_input)

    if run is None:
        print("Error: Actor run failed.", file=sys.stderr)
        sys.exit(1)

    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    return items


def main():
    parser = argparse.ArgumentParser(description="Scrape TikTok post metadata via Apify")
    parser.add_argument("url", help="TikTok post URL")
    parser.add_argument("--output", "-o", help="Save JSON output to file")
    parser.add_argument(
        "--download-video", action="store_true",
        help="Download video file (paid add-on, charges extra)",
    )
    args = parser.parse_args()

    items = scrape_tiktok_post(args.url, download_video=args.download_video)

    result = items[0] if len(items) == 1 else items
    output = json.dumps(result, indent=2, ensure_ascii=False)

    if args.output:
        out_path = output_dir() / args.output if not os.path.isabs(args.output) else args.output
        out_path = type(out_path)(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output)
        print(f"Saved to {out_path}")
    else:
        # Default: save to downloads/<post_id>/result.json
        posts = items if isinstance(result, list) else [result]
        for post in posts:
            post_id = post.get("id", "unknown")
            post_dir = output_dir() / post_id
            post_dir.mkdir(parents=True, exist_ok=True)
            dest = post_dir / "result.json"
            dest.write_text(json.dumps(post, indent=2, ensure_ascii=False))
            print(f"Saved to {dest}")


if __name__ == "__main__":
    main()
