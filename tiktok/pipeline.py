import argparse
import json
import sys
from pathlib import Path

from config import ROOT_DIR, output_dir

from tiktok.scrape_post import scrape_tiktok_post
from tiktok.download_media import download_post
from tiktok.scrape_comments import scrape_comments, extract_post_id
from tiktok.analyze_video import analyze_media, _load_prompt_generator, DEFAULT_PROMPT_FILE

from config import gemini_model


def main():
    parser = argparse.ArgumentParser(description="Full TikTok post pipeline: scrape, download, analyze")
    parser.add_argument("url", help="TikTok post URL")
    parser.add_argument("--download-video", action="store_true", help="Download video file (paid add-on)")
    parser.add_argument("--comments", type=int, default=0, help="Number of comments to scrape (default: 0)")
    parser.add_argument("--replies", type=int, default=0, help="Max replies per comment (default: 0)")
    parser.add_argument("-p", "--prompt-file", default=None, help="Prompt file for analysis (overrides built-in prompt)")
    parser.add_argument("--no-analyze", action="store_true", help="Skip video analysis")
    args = parser.parse_args()

    # 1. Scrape post metadata
    print(f"[1/4] Scraping post metadata...")
    items = scrape_tiktok_post(args.url, download_video=args.download_video)
    result = items[0] if len(items) == 1 else items
    data = items[0] if isinstance(result, list) else result

    post_id = data.get("id", "unknown")
    post_dir = output_dir() / post_id
    post_dir.mkdir(parents=True, exist_ok=True)

    dest = post_dir / "result.json"
    dest.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    print(f"  Saved to {dest}")

    # 2. Download media assets
    print(f"\n[2/4] Downloading media assets...")
    download_post(data, output_dir())

    # 3. Scrape comments (optional)
    if args.comments > 0:
        print(f"\n[3/4] Scraping {args.comments} comments...")
        web_url = data.get("webVideoUrl") or data.get("submittedVideoUrl")
        if web_url:
            comment_items = scrape_comments(web_url, count=args.comments, max_replies=args.replies)
            comments_dest = post_dir / "comments.json"
            comments_dest.write_text(json.dumps(comment_items, indent=2, ensure_ascii=False))
            print(f"  Saved {len(comment_items)} comments to {comments_dest}")
        else:
            print("  Skipped: no video URL in result", file=sys.stderr)
    else:
        print(f"\n[3/4] Skipping comments (use --comments N to scrape)")

    # 4. Analyze video
    video_path = post_dir / "video.mp4"
    if args.no_analyze:
        print(f"\n[4/4] Skipping analysis (--no-analyze)")
    elif not video_path.is_file():
        print(f"\n[4/4] Skipping analysis (no video file)")
    else:
        if args.prompt_file:
            prompt_path = Path(args.prompt_file)
            if not prompt_path.is_file():
                print(f"\n[4/4] Skipping analysis (prompt file not found: {prompt_path})", file=sys.stderr)
                prompt = None
            else:
                prompt = prompt_path.read_text().strip()
        else:
            generate_auditor_prompt = _load_prompt_generator()
            prompt = generate_auditor_prompt("video")

        if prompt:
            model = gemini_model()
            print(f"\n[4/4] Analyzing video with {model}...")
            text, usage = analyze_media(video_path, prompt, model=model)
            analysis_dest = post_dir / "analysis.txt"
            analysis_dest.write_text(text)
            print(f"  Saved to {analysis_dest}")
            if usage:
                usage_dest = post_dir / "analysis_usage.json"
                usage_dest.write_text(json.dumps(usage, indent=2))
                thinking = usage.get("thinking_tokens") or 0
                parts = [f"{usage.get('prompt_tokens', '?')} input"]
                parts.append(f"{usage.get('output_tokens', '?')} output")
                if thinking:
                    parts.append(f"{thinking} thinking")
                parts.append(f"{usage.get('total_tokens', '?')} total")
                print(f"  Usage: {' + '.join(parts)}")

    print(f"\nDone! All files in {post_dir}")


if __name__ == "__main__":
    main()
