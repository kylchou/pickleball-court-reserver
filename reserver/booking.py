"""Search preferred slots and book the first available court, with retries."""
from __future__ import annotations

import logging
import time
from datetime import date, timedelta

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from reserver.config import Config, PreferredSlot

log = logging.getLogger(__name__)


class BookingFailedError(RuntimeError):
    """Raised when every preferred slot/court combination is unavailable."""


def _target_date(days_ahead: int, day_of_week: str) -> date:
    """Find the next date, within the booking window, matching the given weekday name."""
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    today = date.today()
    for offset in range(days_ahead + 1):
        candidate = today + timedelta(days=offset)
        if weekdays[candidate.weekday()] == day_of_week:
            return candidate
    raise ValueError(f"No {day_of_week} found within {days_ahead} days")


def _open_calendar_for(driver, target: date, wait: WebDriverWait) -> None:
    driver.get(f"{driver.current_url.split('?')[0]}?date={target.isoformat()}")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='court-grid']")))


def _try_book_court(driver, wait: WebDriverWait, slot: PreferredSlot, court_number: int) -> bool:
    selector = (
        f"[data-testid='slot-court-{court_number}-{slot.start_time}']"
    )
    try:
        cell = driver.find_element(By.CSS_SELECTOR, selector)
    except NoSuchElementException:
        return False

    if cell.get_attribute("disabled") is not None:
        return False  # already booked, or not released yet

    try:
        cell.click()
        confirm = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-testid='confirm-booking']")))
        confirm.click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='booking-success']")))
        return True
    except (ElementClickInterceptedException, TimeoutException):
        # Someone else grabbed it between us seeing it open and us clicking.
        return False


def book_preferred_slot(driver, config: Config, dry_run: bool = False) -> dict:
    """Try each preferred slot in order, and within a slot each court in priority order.

    Returns a dict describing what was booked. Raises BookingFailedError if nothing
    could be booked after config.max_retries full passes over the preferred list.
    """
    wait = WebDriverWait(driver, 10)

    for attempt in range(1, config.max_retries + 1):
        log.info("Booking attempt %d/%d", attempt, config.max_retries)
        for slot in config.preferred_slots:
            target = _target_date(config.days_ahead, slot.day_of_week)
            _open_calendar_for(driver, target, wait)

            for court in slot.court_priority:
                if dry_run:
                    log.info(
                        "[dry-run] would attempt court %s on %s at %s",
                        court, target, slot.start_time,
                    )
                    continue

                if _try_book_court(driver, wait, slot, court):
                    result = {
                        "date": target.isoformat(),
                        "start_time": slot.start_time,
                        "duration_minutes": slot.duration_minutes,
                        "court": court,
                    }
                    log.info("Booked: %s", result)
                    return result

        if dry_run:
            return {"dry_run": True}

        time.sleep(config.retry_delay_seconds)

    raise BookingFailedError(
        "No preferred slot/court combination was available after "
        f"{config.max_retries} attempts."
    )
