"""Wait until the exact release time before letting the caller proceed."""
from __future__ import annotations

import logging
import time
from datetime import datetime, timedelta

from dateutil import tz

log = logging.getLogger(__name__)


def seconds_until(release_time: str, timezone_name: str) -> float:
    """Seconds from now until the next occurrence of HH:MM:SS in the given timezone."""
    zone = tz.gettz(timezone_name)
    now = datetime.now(zone)
    hour, minute, second = (int(part) for part in release_time.split(":"))
    target = now.replace(hour=hour, minute=minute, second=second, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return (target - now).total_seconds()


def wait_until_release(release_time: str, timezone_name: str = "America/Chicago") -> None:
    """Sleep in coarse chunks, then fine-grained near the end, so we fire as close
    to the release time as possible without busy-waiting the whole time."""
    remaining = seconds_until(release_time, timezone_name)
    log.info("Waiting %.1f seconds until release time %s (%s)", remaining, release_time, timezone_name)

    while remaining > 5:
        chunk = min(remaining - 5, 30)
        time.sleep(chunk)
        remaining = seconds_until(release_time, timezone_name)

    # Fine-grained final approach so we don't overshoot the release window.
    while remaining > 0:
        time.sleep(min(remaining, 0.1))
        remaining = seconds_until(release_time, timezone_name)

    log.info("Release time reached.")
