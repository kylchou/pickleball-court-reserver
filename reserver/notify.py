from __future__ import annotations

import json
import logging
import urllib.request

log = logging.getLogger(__name__)


def send(webhook_url: str | None, message: str) -> None:
    """Never raises, so a broken webhook can't fail a run that booked fine."""
    if not webhook_url:
        return

    body = json.dumps({"content": message}).encode("utf-8")
    request = urllib.request.Request(
        webhook_url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(request, timeout=10)
    except Exception:
        log.exception("Webhook notification failed to send")
