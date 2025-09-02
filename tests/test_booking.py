"""Exercise the search/retry/priority logic in booking.py without a real
browser -- fake objects stand in for the Selenium driver, wait, and DOM
elements. This is the part of the codebase that actually matters at 7am on
a Saturday, so it's the part that most needs a regression net.
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    TimeoutException,
)

import reserver.booking as booking_module
from reserver.booking import (
    BookingFailedError,
    _target_date,
    _try_book_court,
    book_preferred_slot,
)
from reserver.config import Config, PreferredSlot


class FakeElement:
    def __init__(self, disabled: bool = False, raise_on_click: Exception | None = None):
        self.disabled = disabled
        self.raise_on_click = raise_on_click
        self.clicked = False

    def get_attribute(self, name: str):
        if name == "disabled":
            return "true" if self.disabled else None
        return None

    def click(self):
        if self.raise_on_click:
            raise self.raise_on_click
        self.clicked = True

    def is_displayed(self) -> bool:
        return True

    def is_enabled(self) -> bool:
        return not self.disabled


class FakeDriver:
    """Just enough of the WebDriver surface for expected_conditions to work
    against: `.find_element` and `.current_url`/`.get`.
    """

    def __init__(self, elements: dict[str, FakeElement] | None = None):
        self.elements = elements or {}
        self.current_url = "https://example.com/reservations"
        self.visited = []

    def get(self, url: str) -> None:
        self.visited.append(url)

    def find_element(self, by, selector):
        try:
            return self.elements[selector]
        except KeyError:
            raise NoSuchElementException(selector)


class FakeWait:
    """Stands in for WebDriverWait. Since tests set the driver up front in
    its final state (nothing actually loads asynchronously here), a single
    evaluation of the condition is enough -- no need to actually poll.
    """

    def __init__(self, driver, timeout=10):
        self.driver = driver

    def until(self, condition):
        result = condition(self.driver)
        if not result:
            raise TimeoutException("condition never became true")
        return result


def make_config(**overrides) -> Config:
    slot = PreferredSlot(
        day_of_week="Saturday", start_time="09:00", duration_minutes=60, court_priority=[1, 2, 3]
    )
    defaults = dict(
        portal_url="https://example.com",
        username="u",
        password="p",
        release_time="07:00:00",
        release_timezone="America/Chicago",
        days_ahead=7,
        preferred_slots=[slot],
        headless=True,
        max_retries=2,
        retry_delay_seconds=0,
    )
    defaults.update(overrides)
    return Config(**defaults)


def test_target_date_finds_next_matching_weekday(monkeypatch):
    # A fixed Monday -- the next Saturday should be 5 days out.
    fixed_today = date(2025, 6, 2)

    class FixedDate(date):
        @classmethod
        def today(cls):
            return fixed_today

    monkeypatch.setattr(booking_module, "date", FixedDate)
    assert _target_date(days_ahead=7, day_of_week="Saturday") == date(2025, 6, 7)


def test_target_date_raises_when_out_of_window(monkeypatch):
    fixed_today = date(2025, 6, 2)

    class FixedDate(date):
        @classmethod
        def today(cls):
            return fixed_today

    monkeypatch.setattr(booking_module, "date", FixedDate)
    with pytest.raises(ValueError):
        _target_date(days_ahead=1, day_of_week="Friday")


def test_try_book_court_missing_element_returns_false():
    driver = FakeDriver(elements={})
    wait = FakeWait(driver)
    slot = PreferredSlot("Saturday", "09:00", 60, [1])
    assert _try_book_court(driver, wait, slot, court_number=1) is False


def test_try_book_court_disabled_cell_returns_false():
    selector = "[data-testid='slot-court-1-09:00']"
    driver = FakeDriver(elements={selector: FakeElement(disabled=True)})
    wait = FakeWait(driver)
    slot = PreferredSlot("Saturday", "09:00", 60, [1])
    assert _try_book_court(driver, wait, slot, court_number=1) is False


def test_try_book_court_success():
    cell_selector = "[data-testid='slot-court-1-09:00']"
    confirm_selector = "[data-testid='confirm-booking']"
    success_selector = "[data-testid='booking-success']"
    driver = FakeDriver(
        elements={
            cell_selector: FakeElement(),
            confirm_selector: FakeElement(),
            success_selector: FakeElement(),
        }
    )
    wait = FakeWait(driver)
    slot = PreferredSlot("Saturday", "09:00", 60, [1])
    assert _try_book_court(driver, wait, slot, court_number=1) is True
    assert driver.elements[cell_selector].clicked
    assert driver.elements[confirm_selector].clicked


def test_try_book_court_lost_the_race_returns_false():
    # Someone else clicked it first -- Selenium raises this mid-click.
    cell_selector = "[data-testid='slot-court-1-09:00']"
    driver = FakeDriver(
        elements={cell_selector: FakeElement(raise_on_click=ElementClickInterceptedException())}
    )
    wait = FakeWait(driver)
    slot = PreferredSlot("Saturday", "09:00", 60, [1])
    assert _try_book_court(driver, wait, slot, court_number=1) is False


def test_book_preferred_slot_falls_through_priority_list(monkeypatch):
    # Court 1 is taken, court 2 is open -- should book court 2, not give up.
    monkeypatch.setattr(booking_module, "_open_calendar_for", lambda *a, **k: None)
    grid = "[data-testid='court-grid']"
    court1 = "[data-testid='slot-court-1-09:00']"
    court2 = "[data-testid='slot-court-2-09:00']"
    confirm = "[data-testid='confirm-booking']"
    success = "[data-testid='booking-success']"
    driver = FakeDriver(
        elements={
            grid: FakeElement(),
            court1: FakeElement(disabled=True),
            court2: FakeElement(),
            confirm: FakeElement(),
            success: FakeElement(),
        }
    )
    monkeypatch.setattr(booking_module, "WebDriverWait", lambda d, t: FakeWait(d))
    config = make_config()
    result = book_preferred_slot(driver, config, dry_run=False)
    assert result["court"] == 2


def test_book_preferred_slot_raises_after_exhausting_retries(monkeypatch):
    monkeypatch.setattr(booking_module, "_open_calendar_for", lambda *a, **k: None)
    monkeypatch.setattr(booking_module, "WebDriverWait", lambda d, t: FakeWait(d))
    driver = FakeDriver(elements={})  # nothing ever available
    config = make_config(max_retries=2, retry_delay_seconds=0)
    with pytest.raises(BookingFailedError):
        book_preferred_slot(driver, config, dry_run=False)


def test_book_preferred_slot_dry_run_never_clicks(monkeypatch):
    monkeypatch.setattr(booking_module, "_open_calendar_for", lambda *a, **k: None)
    grid = "[data-testid='court-grid']"
    court1 = "[data-testid='slot-court-1-09:00']"
    element = FakeElement()
    driver = FakeDriver(elements={grid: FakeElement(), court1: element})
    monkeypatch.setattr(booking_module, "WebDriverWait", lambda d, t: FakeWait(d))
    config = make_config()
    result = book_preferred_slot(driver, config, dry_run=True)
    assert result == {"dry_run": True}
    assert element.clicked is False
