import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

from instagram_sender.message_engine import MessageEngine
from instagram_sender.delay_controller import DelayController
from instagram_sender.cookie_manager import CookieManager
from utils.logger import get_logger
from utils.validator import (
    validate_usernames,
    validate_message,
    validate_delay,
)

def load_config(config_path_arg: str | None, base_dir: Path) -> Dict[str, Any]:
    """
    Load configuration JSON.

    Preference:
    1. Explicit --config path, if provided.
    2. src/config/settings.json if present.
    3. src/config/settings.example.json as a fallback.
    """
    config_dir = base_dir / "config"

    candidate_paths: List[Path] = []
    if config_path_arg:
        candidate_paths.append(Path(config_path_arg))
    candidate_paths.append(config_dir / "settings.json")
    candidate_paths.append(config_dir / "settings.example.json")

    for path in candidate_paths:
        if path.exists():
            try:
                with path.open("r", encoding="utf-8") as f:
                    return json.load(f)
            except (OSError, json.JSONDecodeError) as exc:
                print(f"Failed to load configuration file '{path}': {exc}", file=sys.stderr)
                sys.exit(1)

    print("No configuration file found. Expected at least one settings.json or settings.example.json.", file=sys.stderr)
    sys.exit(1)

def load_usernames(root_dir: Path, source_rel_path: str, logger) -> List[str]:
    usernames_path = (root_dir / source_rel_path).resolve()
    if not usernames_path.exists():
        logger.error("Usernames file '%s' does not exist.", usernames_path)
        sys.exit(1)

    try:
        with usernames_path.open("r", encoding="utf-8") as f:
            raw_usernames = [line.strip() for line in f.readlines()]
    except OSError as exc:
        logger.error("Failed to read usernames file '%s': %s", usernames_path, exc)
        sys.exit(1)

    try:
        return validate_usernames(raw_usernames)
    except ValueError as exc:
        logger.error("Username validation failed: %s", exc)
        sys.exit(1)

def build_delay_controller(config: Dict[str, Any], logger) -> DelayController:
    messaging_cfg = config.get("messaging", {})
    delay_seconds = messaging_cfg.get("delay_seconds", 2)
    max_jitter = messaging_cfg.get("max_random_additional_delay_seconds", 3)

    try:
        base_delay = validate_delay(delay_seconds)
    except ValueError as exc:
        logger.error("Delay validation failed: %s", exc)
        sys.exit(1)

    try:
        jitter = float(max_jitter)
        if jitter < 0:
            logger.warning("max_random_additional_delay_seconds is negative; using 0 instead.")
            jitter = 0.0
    except (TypeError, ValueError):
        logger.warning("max_random_additional_delay_seconds is invalid; using 0.")
        jitter = 0.0

    logger.info("Using base delay %.2fs with up to %.2fs random jitter.", base_delay, jitter)
    return DelayController(base_delay=base_delay, max_jitter=jitter, logger=logger)

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Instagram Bulk Message Sender - simulated bulk DM tool using cookies-based configuration."
    )
    parser.add_argument(
        "--config",
        help="Path to configuration JSON file. Defaults to src/config/settings.json or settings.example.json fallback.",
        default=None,
    )
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parent  # src/
    root_dir = base_dir.parent                  # repository root

    config = load_config(args.config, base_dir)

    logging_cfg = config.get("logging", {})
    log_file_rel = logging_cfg.get("log_file", "data/logs.json")
    log_file_path = (root_dir / log_file_rel).resolve()

    log_level = logging_cfg.get("log_level", "INFO")
    logger = get_logger("instagram_bulk_sender", log_file_path=log_file_path, level=log_level)
    logger.info("Starting Instagram Bulk Message Sender.")

    messaging_cfg = config.get("messaging", {})
    username_source_rel = messaging_cfg.get("username_source_file", "data/usernames.sample.txt")
    message_text = (messaging_cfg.get("default_message") or "").strip()

    try:
        validate_message(message_text)
    except ValueError as exc:
        logger.error("Message validation failed: %s", exc)
        sys.exit(1)

    usernames = load_usernames(root_dir, username_source_rel, logger)
    delay_controller = build_delay_controller(config, logger)

    instagram_cfg = config.get("instagram", {})
    cookie_manager = CookieManager(instagram_cfg, logger=logger, root_dir=root_dir)
    cookies = cookie_manager.load_cookies()

    engine = MessageEngine(
        logger=logger,
        delay_controller=delay_controller,
        cookies=cookies,
        log_file_path=log_file_path,
    )

    try:
        results = engine.send_bulk_messages(usernames=usernames, message_text=message_text)
    except KeyboardInterrupt:
        logger.warning("Interrupted by user; exiting gracefully.")
        sys.exit(1)

    success_count = sum(1 for r in results if r.get("status") == "success")
    failure_count = len(results) - success_count
    logger.info("Finished sending messages. Success: %d, Failed: %d", success_count, failure_count)

if __name__ == "__main__":
    main()