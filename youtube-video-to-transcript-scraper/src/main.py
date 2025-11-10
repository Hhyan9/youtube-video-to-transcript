thonimport argparse
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from extractors.youtube_parser import YouTubeTranscriptExtractor
from outputs.export_manager import ExportManager

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format=LOG_FORMAT)

def load_settings() -> Dict[str, Any]:
    """
    Load configuration from src/config/settings.json if present,
    otherwise fall back to src/config/settings.example.json.
    If neither exists, return sensible defaults.
    """
    base_dir = Path(__file__).resolve().parent
    config_dir = base_dir / "config"
    primary_settings = config_dir / "settings.json"
    example_settings = config_dir / "settings.example.json"

    defaults: Dict[str, Any] = {
        "output_dir": "data",
        "output_format": "json",
        "language_code": None,
        "headers": {},
        "cookies": "",
    }

    path_to_use: Optional[Path] = None
    if primary_settings.exists():
        path_to_use = primary_settings
    elif example_settings.exists():
        path_to_use = example_settings

    if not path_to_use:
        logging.debug("No settings file found; using in-memory defaults.")
        return defaults

    try:
        with path_to_use.open("r", encoding="utf-8") as f:
            file_settings = json.load(f)
        if not isinstance(file_settings, dict):
            raise ValueError("Settings JSON must be an object at the top level.")
        merged = {**defaults, **file_settings}
        logging.debug("Loaded settings from %s", path_to_use)
        return merged
    except Exception as exc:  # noqa: BLE001
        logging.warning("Failed to load settings from %s: %s", path_to_use, exc)
        return defaults

def parse_args(default_settings: Dict[str, Any]) -> argparse.Namespace:
    base_dir = Path(__file__).resolve().parent
    repo_root = base_dir.parent
    default_urls_file = repo_root / "data" / "sample_urls.txt"
    default_output_dir = repo_root / default_settings.get("output_dir", "data")

    parser = argparse.ArgumentParser(
        description="YouTube Video to Transcript scraper - bulk transcript extractor."
    )
    parser.add_argument(
        "--urls-file",
        type=str,
        default=str(default_urls_file),
        help="Path to a text file containing YouTube URLs (one per line).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=str(default_output_dir / "output_sample"),
        help=(
            "Output file path without extension. "
            "The extension is decided by the chosen format."
        ),
    )
    parser.add_argument(
        "--format",
        type=str,
        default=default_settings.get("output_format", "json"),
        choices=["json", "csv", "excel", "html", "xml"],
        help="Output format for the transcripts.",
    )
    parser.add_argument(
        "--language",
        type=str,
        default=default_settings.get("language_code"),
        help="Preferred transcript language code (e.g., en, es). Defaults to auto.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose (debug) logging.",
    )
    return parser.parse_args()

def read_urls_file(path: Path) -> List[str]:
    if not path.exists():
        raise FileNotFoundError(f"URLs file not found: {path}")

    urls: List[str] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            cleaned = line.strip()
            if cleaned and not cleaned.startswith("#"):
                urls.append(cleaned)

    if not urls:
        raise ValueError(f"No valid URLs found in file: {path}")

    return urls

def main() -> None:
    settings = load_settings()
    args = parse_args(settings)
    setup_logging(args.verbose)

    try:
        urls_file = Path(args.urls_file).resolve()
        output_path = Path(args.output).resolve()
        output_format = args.format.lower()
        language = args.language
    except Exception as exc:  # noqa: BLE001
        logging.error("Failed to parse arguments: %s", exc)
        raise SystemExit(1) from exc

    logging.info("Reading URLs from %s", urls_file)
    try:
        urls = read_urls_file(urls_file)
    except Exception as exc:  # noqa: BLE001
        logging.error("Error reading URLs file: %s", exc)
        raise SystemExit(1) from exc

    extractor = YouTubeTranscriptExtractor(language_code=language)
    export_manager = ExportManager()

    logging.info("Fetching transcripts for %d URLs...", len(urls))
    try:
        results = extractor.fetch_transcripts(urls)
    except Exception as exc:  # noqa: BLE001
        logging.error("Failed to fetch transcripts: %s", exc)
        raise SystemExit(1) from exc

    if not results:
        logging.warning("No transcripts were successfully fetched.")
    else:
        logging.info("Successfully fetched %d transcripts.", len(results))

    try:
        export_manager.export(results, output_path, output_format)
    except Exception as exc:  # noqa: BLE001
        logging.error("Failed to export transcripts: %s", exc)
        raise SystemExit(1) from exc

    logging.info(
        "Export complete. Wrote %d transcript record(s) to %s (%s format).",
        len(results),
        output_path,
        output_format,
    )

if __name__ == "__main__":
    main()