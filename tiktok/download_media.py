import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from config import output_dir


def is_url_expired(url: str) -> bool:
    params = parse_qs(urlparse(url).query)
    expires = params.get("x-expires")
    if expires:
        try:
            return time.time() > int(expires[0])
        except (ValueError, IndexError):
            return False
    return False


def download_file(url: str, dest: Path, label: str) -> bool:
    if not url:
        return False

    if is_url_expired(url):
        print(f"  Skipped (expired): {label}", file=sys.stderr)
        return False

    dest.parent.mkdir(parents=True, exist_ok=True)

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            with open(dest, "wb") as f:
                while chunk := response.read(8192):
                    f.write(chunk)
        print(f"  Downloaded: {label} -> {dest}")
        return True
    except urllib.error.HTTPError as e:
        print(f"  Failed ({e.code}): {label}", file=sys.stderr)
        return False
    except urllib.error.URLError as e:
        print(f"  Failed (network): {label} - {e.reason}", file=sys.stderr)
        return False
    except OSError as e:
        print(f"  Failed (I/O): {label} - {e}", file=sys.stderr)
        return False


def get_video_url(data: dict) -> str | None:
    video_meta = data.get("videoMeta", {})
    media_urls = data.get("mediaUrls", [])

    # Only available via paid add-on during scrape
    addr = video_meta.get("downloadAddr")
    if addr:
        return addr
    if media_urls:
        return media_urls[0]

    return None


def download_post(data: dict, out_dir: Path) -> dict:
    post_id = data.get("id", "unknown")
    post_dir = out_dir / post_id
    video_meta = data.get("videoMeta", {})
    author_meta = data.get("authorMeta", {})
    music_meta = data.get("musicMeta", {})

    results = {"downloaded": 0, "failed": 0}
    print(f"Post {post_id} -> {post_dir}")

    downloads = []

    # Video
    video_url = get_video_url(data)
    if video_url:
        downloads.append((video_url, post_dir / "video.mp4", "video"))
    else:
        print("  No video URL available (use --download-video during scrape)")

    # Covers
    if video_meta.get("coverUrl"):
        downloads.append((video_meta["coverUrl"], post_dir / "cover.jpg", "cover"))
    if video_meta.get("originalCoverUrl"):
        downloads.append((video_meta["originalCoverUrl"], post_dir / "cover_original.jpg", "cover (original)"))

    # Avatar
    if author_meta.get("avatar"):
        downloads.append((author_meta["avatar"], post_dir / "avatar.jpg", "avatar"))

    # Music
    if music_meta.get("playUrl"):
        downloads.append((music_meta["playUrl"], post_dir / "music.mp3", "music audio"))
    if music_meta.get("coverMediumUrl"):
        downloads.append((music_meta["coverMediumUrl"], post_dir / "music_cover.jpg", "music cover"))

    # Subtitles
    for sub in video_meta.get("subtitleLinks", []):
        link = sub.get("downloadLink")
        lang = sub.get("language", "unknown")
        if link:
            downloads.append((link, post_dir / "subtitles" / f"{lang}.vtt", f"subtitles ({lang})"))

    # Comments — report only
    comment_count = data.get("commentCount", 0)
    if comment_count > 0:
        print(f"  Comments: {comment_count} (use scrape-comments to scrape)")

    for url, dest, label in downloads:
        if download_file(url, dest, label):
            results["downloaded"] += 1
        else:
            results["failed"] += 1

    # Save metadata JSON alongside downloads
    meta_dest = post_dir / "result.json"
    if not meta_dest.exists():
        post_dir.mkdir(parents=True, exist_ok=True)
        meta_dest.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        print(f"  Saved: result.json")

    return results


def resolve_json_path(target: str) -> Path:
    """Resolve target to a JSON file path. Accepts a file path or a post ID."""
    target_path = Path(target)
    if target_path.is_file():
        return target_path

    # Try as post ID: downloads/<id>/result.json
    by_id = output_dir() / target / "result.json"
    if by_id.is_file():
        return by_id

    print(f"Error: '{target}' is not a file and no result found at {by_id}", file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Download TikTok post media assets from a scraped result JSON"
    )
    parser.add_argument("target", help="Path to result JSON file or post ID")
    args = parser.parse_args()

    json_path = resolve_json_path(args.target)

    try:
        with open(json_path) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    out_dir = output_dir()
    posts = data if isinstance(data, list) else [data]

    total = {"downloaded": 0, "failed": 0}
    for post in posts:
        result = download_post(post, out_dir)
        for k in total:
            total[k] += result[k]

    print(f"\nDone: {total['downloaded']} downloaded, {total['failed']} failed/skipped")


if __name__ == "__main__":
    main()
