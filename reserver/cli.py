"""argparse entry point."""
from __future__ import annotations

import argparse
import logging

from reserver.booking import BookingFailedError, book_preferred_slot
from reserver.browser import make_driver
from reserver.config import Config, ConfigError
from reserver.logging_config import setup_logging
from reserver.scheduler import wait_until_release
from reserver import auth

log = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Automatically reserve a pickleball court.")
    parser.add_argument("--config", default="config.json", help="Path to config.json")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run the full flow (login, search) without submitting a real booking.",
    )
    parser.add_argument(
        "--skip-wait",
        action="store_true",
        help="Skip waiting for the release time (useful for testing right now).",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    setup_logging()
    args = build_parser().parse_args(argv)

    try:
        config = Config.load(args.config)
    except ConfigError as exc:
        log.error(str(exc))
        return 1

    if not args.skip_wait:
        wait_until_release(config.release_time, config.release_timezone)

    driver = make_driver(headless=config.headless)
    try:
        auth.login(driver, config.portal_url, config.username, config.password)
        result = book_preferred_slot(driver, config, dry_run=args.dry_run)
        log.info("Done: %s", result)
        return 0
    except BookingFailedError as exc:
        log.error(str(exc))
        return 2
    finally:
        driver.quit()


if __name__ == "__main__":
    raise SystemExit(main())
