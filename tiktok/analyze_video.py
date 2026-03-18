import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

from config import ROOT_DIR, gemini_model, output_dir


def _load_prompt_generator():
    """Load generate_auditor_prompt from prompts/gemini_media_analysis.py."""
    spec = importlib.util.spec_from_file_location(
        "gemini_media_analysis", ROOT_DIR / "prompts" / "gemini_media_analysis.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.generate_auditor_prompt

load_dotenv()

DEFAULT_PROMPT_FILE = ROOT_DIR / "prompts" / "gemini_analyze.txt"

MEDIA_MIME = {
    ".mp4": "video/mp4",
    ".mov": "video/quicktime",
    ".avi": "video/x-msvideo",
    ".webm": "video/webm",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


def analyze_media(media_path: Path, prompt: str, model: str) -> tuple[str, dict]:
    """Analyze video or image and return (text, usage_info)."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not set. Add it to .env file.", file=sys.stderr)
        sys.exit(1)

    suffix = media_path.suffix.lower()
    mime_type = MEDIA_MIME.get(suffix)
    if not mime_type:
        print(f"Error: unsupported file type '{suffix}'", file=sys.stderr)
        sys.exit(1)

    media_bytes = media_path.read_bytes()
    size_mb = len(media_bytes) / (1024 * 1024)
    if size_mb > 20:
        print(f"Error: file is {size_mb:.1f}MB, max supported is 20MB for inline upload.", file=sys.stderr)
        sys.exit(1)

    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=model,
        contents=types.Content(
            parts=[
                types.Part(
                    inline_data=types.Blob(data=media_bytes, mime_type=mime_type)
                ),
                types.Part(text=prompt),
            ]
        ),
    )

    usage = {}
    meta = getattr(response, "usage_metadata", None)
    if meta:
        usage = {
            "model": model,
            "prompt_tokens": getattr(meta, "prompt_token_count", None),
            "output_tokens": getattr(meta, "candidates_token_count", None),
            "thinking_tokens": getattr(meta, "thoughts_token_count", None),
            "total_tokens": getattr(meta, "total_token_count", None),
        }

        # Input token breakdown by modality (text vs video)
        prompt_details = getattr(meta, "prompt_tokens_details", None)
        if prompt_details:
            usage["prompt_tokens_by_modality"] = {
                detail.modality.value.lower(): detail.token_count
                for detail in prompt_details
            }

    return response.text, usage


def detect_media_type(path: Path) -> str:
    """Return 'video' or 'image' based on file extension."""
    suffix = path.suffix.lower()
    if suffix in (".mp4", ".mov", ".avi", ".webm"):
        return "video"
    if suffix in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
        return "image"
    return "video"  # default


def resolve_media_path(target: str) -> Path:
    """Resolve target to a media file. Accepts a file path or post ID."""
    target_path = Path(target)
    if target_path.is_file():
        return target_path

    # Try as post ID: downloads/<id>/video.mp4
    by_id = output_dir() / target / "video.mp4"
    if by_id.is_file():
        return by_id

    print(f"Error: '{target}' is not a file and no video found at {by_id}", file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Analyze TikTok video/image using Gemini")
    parser.add_argument("target", help="Path to media file (video/image) or post ID")
    parser.add_argument("-p", "--prompt-file", default=None, help="Path to prompt file (overrides built-in prompt)")
    args = parser.parse_args()

    media_path = resolve_media_path(args.target)
    media_type = detect_media_type(media_path)

    if args.prompt_file:
        prompt_path = Path(args.prompt_file)
        if not prompt_path.is_file():
            print(f"Error: prompt file not found: {prompt_path}", file=sys.stderr)
            sys.exit(1)
        prompt = prompt_path.read_text().strip()
    else:
        generate_auditor_prompt = _load_prompt_generator()
        prompt = generate_auditor_prompt(media_type)

    model = gemini_model()
    print(f"Analyzing ({media_type}): {media_path} (model: {model})")
    text, usage = analyze_media(media_path, prompt, model=model)

    # Save analysis alongside the media
    post_dir = media_path.parent
    dest = post_dir / "analysis.txt"
    dest.write_text(text)
    print(f"Saved to {dest}")

    # Save usage info
    if usage:
        usage_dest = post_dir / "analysis_usage.json"
        usage_dest.write_text(json.dumps(usage, indent=2))
        modality = usage.get("prompt_tokens_by_modality", {})
        modality_str = ", ".join(f"{k}: {v}" for k, v in modality.items()) if modality else ""
        thinking = usage.get("thinking_tokens") or 0
        parts = [f"{usage.get('prompt_tokens', '?')} input"]
        if modality_str:
            parts[0] += f" ({modality_str})"
        parts.append(f"{usage.get('output_tokens', '?')} output")
        if thinking:
            parts.append(f"{thinking} thinking")
        parts.append(f"{usage.get('total_tokens', '?')} total")
        print(f"Usage: {' + '.join(parts)}")
        print(f"Saved usage to {usage_dest}")


if __name__ == "__main__":
    main()
