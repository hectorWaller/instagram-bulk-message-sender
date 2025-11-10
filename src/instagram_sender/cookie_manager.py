from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.validator import validate_cookies

class CookieManager:
    """
    Manages the retrieval and validation of Instagram cookies.

    Cookies can be provided inline in the configuration or stored in an
    external JSON file. The manager performs basic validation to ensure
    the cookies are well-formed enough to be used by an HTTP client.
    """

    def __init__(
        self,
        config: Dict[str, Any] | None,
        logger=None,
        root_dir: Optional[Path] = None,
    ) -> None:
        self.config = config or {}
        self.logger = logger
        self.root_dir = root_dir or Path.cwd()

    def _load_cookies_from_inline(self) -> Optional[List[Dict[str, Any]]]:
        cookies = self.config.get("cookies")
        if not cookies:
            return None

        try:
            validate_cookies(cookies)
        except ValueError as exc:
            if self.logger:
                self.logger.error("Inline cookies are invalid: %s", exc)
            return None

        if self.logger:
            self.logger.info("Loaded %d cookies from inline configuration.", len(cookies))
        return cookies

    def _load_cookies_from_file(self) -> Optional[List[Dict[str, Any]]]:
        cookies_file = self.config.get("cookies_file")
        if not cookies_file:
            return None

        path = Path(cookies_file)
        if not path.is_absolute():
            path = self.root_dir / cookies_file

        if not path.exists():
            if self.logger:
                self.logger.warning("Cookies file '%s' does not exist; continuing without cookies.", path)
            return None

        try:
            with path.open("r", encoding="utf-8") as f:
                cookies = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            if self.logger:
                self.logger.error("Failed to read cookies file '%s': %s", path, exc)
            return None

        try:
            validate_cookies(cookies)
        except ValueError as exc:
            if self.logger:
                self.logger.error("Cookies in file '%s' are invalid: %s", path, exc)
            return None

        if self.logger:
            self.logger.info("Loaded %d cookies from file '%s'.", len(cookies), path)
        return cookies

    def load_cookies(self) -> List[Dict[str, Any]]:
        """
        Load cookies from configuration or file.

        If no valid cookies are found, an empty list is returned and the
        engine will operate in simulation-only mode.
        """
        cookies = self._load_cookies_from_inline()
        if cookies is None:
            cookies = self._load_cookies_from_file()

        if cookies is None:
            cookies = []
            if self.logger:
                self.logger.warning("No valid cookies available; running in simulation mode only.")

        return cookies