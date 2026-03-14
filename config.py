import json
from pathlib import Path

ROOT_DIR = Path(__file__).parent
CONFIG_FILE = ROOT_DIR / "config.json"

_config: dict | None = None


def get_config() -> dict:
    global _config
    if _config is None:
        if CONFIG_FILE.is_file():
            _config = json.loads(CONFIG_FILE.read_text())
        else:
            _config = {}
    return _config


def output_dir() -> Path:
    return ROOT_DIR / get_config().get("output_dir", "downloads")


def gemini_model() -> str:
    return get_config().get("gemini_model", "gemini-2.5-flash")
