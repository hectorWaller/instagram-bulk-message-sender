from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

_LOGGERS: dict[str, logging.Logger] = {}

def _normalize_level(level: str | int) -> int:
    if isinstance(level, int):
        return level
    if isinstance(level, str):
        numeric = getattr(logging, level.upper(), None)
        if isinstance(numeric, int):
            return numeric
    return logging.INFO

def get_logger(name: str, log_file_path: str | Path | None = None, level: str | int = "INFO") -> logging.Logger:
    """
    Create or retrieve a configured logger.

    Logs are always written to stdout; if a log_file_path is provided,
    a parallel text log file (with .log extension) is also written.
    """
    if name in _LOGGERS:
        return _LOGGERS[name]

    logger = logging.getLogger(name)
    logger.setLevel(_normalize_level(level))
    logger.propagate = False

    if not logger.handlers:
        formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        if log_file_path:
            try:
                text_log_path = Path(log_file_path).with_suffix(".log")
                text_log_path.parent.mkdir(parents=True, exist_ok=True)
                file_handler = logging.FileHandler(text_log_path, encoding="utf-8")
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            except OSError:
                # If file logging fails, we still keep stdout logging.
                pass

    _LOGGERS[name] = logger
    return logger

def append_status_log(log_file_path: str | Path, entry: Dict[str, Any]) -> None:
    """
    Append a structured status entry to a JSON log file.

    The log file contains a single JSON array of entries. The function
    is resilient to partial or corrupted content: if parsing fails,
    the log is reset with just the current entry.
    """
    path = Path(log_file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if "timestamp" not in entry:
        entry["timestamp"] = datetime.utcnow().isoformat() + "Z"

    data: list[Dict[str, Any]] = []

    if path.exists():
        try:
            with path.open("r", encoding="utf-8") as f:
                raw = f.read().strip()
                if raw:
                    parsed = json.loads(raw)
                    if isinstance(parsed, list):
                        data = parsed
        except (OSError, json.JSONDecodeError):
            # If the log is unreadable, we reset it.
            data = []

    data.append(entry)

    tmp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        tmp_path.replace(path)
    except OSError:
        # Log write failures are non-fatal; they shouldn't crash the app.
        pass