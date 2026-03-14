import argparse
import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

from apify_client import ApifyClient
from dotenv import load_dotenv

from config import output_dir

load_dotenv()

ACTOR_ID = "clockworks/tiktok-comments-scraper"


def extract_post_id(url: str) -> str:
    """Extract post ID from TikTok video URL."""
    path = urlparse(url).path.rstrip("/")
    return path.split("/")[-1]


def resolve_video_url(target: str) -> str:
    """Resolve target to a TikTok video URL. Accepts a URL, post ID, or JSON path."""
    # URL
    if target.startswith("http"):
        return target

    # JSON file path
    target_path = Path(target)
    if target_path.is_file():
        data = json.loads(target_path.read_text())
        if isinstance(data, list):
            data = data[0]
        url = data.get("webVideoUrl") or data.get("submittedVideoUrl")
        if url:
            return url
        print(f"Error: no video URL found in {target}", file=sys.stderr)
        sys.exit(1)

    # Post ID -> look for downloads/<id>/result.json
    result_path = output_dir() / target / "result.json"
    if result_path.is_file():
        data = json.loads(result_path.read_text())
        url = data.get("webVideoUrl") or data.get("submittedVideoUrl")
        if url:
            return url
        print(f"Error: no video URL found in {result_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Error: '{target}' is not a URL, file, or known post ID", file=sys.stderr)
    sys.exit(1)


def scrape_comments(url: str, count: int = 100, max_replies: int = 0) -> list[dict]:
    token = os.environ.get("APIFY_API_TOKEN")
    if not token:
        print("Error: APIFY_API_TOKEN not set. Copy .env.example to .env and add your token.", file=sys.stderr)
        sys.exit(1)

    client = ApifyClient(token)

    run_input = {
        "postURLs": [url],
        "commentsPerPost": count,
        "maxRepliesPerComment": max_replies,
    }

    run = client.actor(ACTOR_ID).call(run_input=run_input)

    if run is None:
        print("Error: Actor run failed.", file=sys.stderr)
        sys.exit(1)

    items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
    return items


def main():
    parser = argparse.ArgumentParser(description="Scrape TikTok video comments via Apify")
    parser.add_argument("target", help="TikTok video URL, post ID, or path to result JSON")
    parser.add_argument("-n", "--count", type=int, default=100, help="Number of comments to fetch (default: 100)")
    parser.add_argument("--replies", type=int, default=0, help="Max replies per comment (default: 0)")
    args = parser.parse_args()

    url = resolve_video_url(args.target)

    items = scrape_comments(url, count=args.count, max_replies=args.replies)

    post_id = extract_post_id(url)
    # Use videoWebUrl from first result if available (more reliable)
    if items and items[0].get("videoWebUrl"):
        post_id = extract_post_id(items[0]["videoWebUrl"])

    post_dir = output_dir() / post_id
    post_dir.mkdir(parents=True, exist_ok=True)
    dest = post_dir / "comments.json"
    dest.write_text(json.dumps(items, indent=2, ensure_ascii=False))
    print(f"Saved {len(items)} comments to {dest}")


if __name__ == "__main__":
    main()
