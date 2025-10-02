"""Optional webhook ping (Discord-compatible) so a bad run doesn't just sit
in reserver.log until I happen to check it. No new dependency -- Discord
(and Slack, with a tiny tweak) both take a plain JSON POST, so stdlib
urllib is enough.
"""
from __future__ import annotations

import json
import logging
import urllib.request

log = logging.getLogger(__name__)


def send(webhook_url: str | None, message: str) -> None:
    """No-op if no webhook is configured. Never raises -- a broken webhook
    shouldn't take down a run that otherwise booked the court fine.
    """
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
