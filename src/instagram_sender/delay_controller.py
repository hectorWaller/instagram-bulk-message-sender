from __future__ import annotations

import random
import time
from typing import Optional

class DelayController:
    """
    Computes and applies delays between message sends.

    A base delay is always applied, with an optional random jitter added
    on top to mimic natural human behaviour and reduce the risk of
    triggering automated spam detection.
    """

    def __init__(self, base_delay: float, max_jitter: float = 0.0, logger: Optional[object] = None) -> None:
        self.base_delay = max(0.0, float(base_delay))
        self.max_jitter = max(0.0, float(max_jitter))
        self.logger = logger

    def next_delay(self) -> float:
        jitter = random.uniform(0, self.max_jitter) if self.max_jitter > 0 else 0.0
        delay = self.base_delay + jitter
        return max(delay, 0.0)

    def sleep(self) -> float:
        delay = self.next_delay()
        if self.logger:
            self.logger.debug("Sleeping for %.2f seconds before sending the next message.", delay)
        time.sleep(delay)
        return delay