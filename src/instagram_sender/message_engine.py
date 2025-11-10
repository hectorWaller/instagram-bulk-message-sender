from __future__ import annotations

import random
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

from utils.logger import append_status_log

class MessageEngine:
    """
    Core engine responsible for orchestrating bulk message sending.

    In this reference implementation, actual network calls to Instagram
    are not performed. Instead, delivery is simulated while preserving
    realistic logging, error handling, and timing behaviour.
    """

    def __init__(
        self,
        logger,
        delay_controller,
        cookies: List[Dict[str, Any]] | None,
        log_file_path: str | Path,
    ) -> None:
        self.logger = logger
        self.delay_controller = delay_controller
        self.cookies = cookies or []
        self.log_file_path = Path(log_file_path)

    def _simulate_send(self, username: str, message_text: str) -> Dict[str, Any]:
        """
        Simulate sending a message to a single Instagram username.

        Success probability is slightly higher when cookies are present,
        mimicking authenticated vs unauthenticated behaviour.
        """
        base_success_probability = 0.93 if self.cookies else 0.80
        is_success = random.random() < base_success_probability

        timestamp = datetime.utcnow().isoformat() + "Z"

        entry: Dict[str, Any] = {
            "username": username,
            "message": message_text,
            "status": "success" if is_success else "failed",
            "timestamp": timestamp,
        }

        if not is_success:
            # In a real implementation, this would reflect actual error details
            entry["error"] = "Simulated delivery failure (network, rate limit, or invalid session)."

        return entry

    def send_bulk_messages(self, usernames: Iterable[str], message_text: str) -> List[Dict[str, Any]]:
        """
        Send a message to all provided usernames, respecting delays between sends.

        Each attempt is logged both to stdout (via the logger) and to a JSON
        log file suitable for downstream analysis.
        """
        usernames_list = list(usernames)
        results: List[Dict[str, Any]] = []

        if not usernames_list:
            self.logger.warning("No usernames to process; aborting.")
            return results

        self.logger.info("Preparing to send messages to %d usernames.", len(usernames_list))

        for index, username in enumerate(usernames_list, start=1):
            self.logger.info("(%d/%d) Sending message to @%s", index, len(usernames_list), username)

            entry = self._simulate_send(username, message_text)
            append_status_log(self.log_file_path, entry)

            if entry["status"] == "success":
                self.logger.info("Message successfully delivered to @%s", username)
            else:
                self.logger.error(
                    "Failed to deliver message to @%s: %s",
                    username,
                    entry.get("error", "Unknown error"),
                )

            results.append(entry)

            # No delay after the last message
            if index < len(usernames_list):
                delay_seconds = self.delay_controller.sleep()
                self.logger.debug("Waited %.2f seconds before next message.", delay_seconds)

        self.logger.info("Bulk messaging session completed.")
        return results