from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List

_USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9._]{1,30}$")

def validate_usernames(raw_usernames: Iterable[str]) -> List[str]:
    """
    Clean and validate a list of Instagram usernames.

    - Strips whitespace.
    - Removes duplicates (case-insensitive).
    - Ensures usernames match Instagram-style constraints.
    """
    cleaned: List[str] = []
    seen: set[str] = set()

    for raw in raw_usernames:
        username = (raw or "").strip()
        if not username:
            continue

        if not _USERNAME_PATTERN.match(username):
            raise ValueError(f"Invalid Instagram username: {username!r}")

        key = username.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(username)

    if not cleaned:
        raise ValueError("No valid usernames provided.")
    return cleaned

def validate_message(message: str) -> None:
    """
    Validate the outbound message text.
    """
    if not message or not message.strip():
        raise ValueError("Message text cannot be empty.")

    if len(message) > 1_000:
        raise ValueError("Message text is too long (maximum 1000 characters).")

def validate_delay(delay_seconds: float) -> float:
    """
    Validate and normalise the base delay between messages.

    Returns a float representing seconds.
    """
    try:
        delay = float(delay_seconds)
    except (TypeError, ValueError):
        raise ValueError("Delay must be a numeric value.") from None

    if delay < 0:
        raise ValueError("Delay cannot be negative.")

    if delay > 120:
        raise ValueError("Delay is unreasonably high (maximum 120 seconds).")

    return delay

def validate_cookies(cookies: Any) -> None:
    """
    Perform lightweight structural validation of cookies.

    Expects a list of dicts that at least contain `name` and `value`.
    """
    if not isinstance(cookies, list):
        raise ValueError("Cookies must be provided as a list of dictionaries.")

    for index, cookie in enumerate(cookies):
        if not isinstance(cookie, dict):
            raise ValueError(f"Cookie at index {index} is not a dictionary.")
        if "name" not in cookie or "value" not in cookie:
            raise ValueError(f"Cookie at index {index} must contain 'name' and 'value' fields.")