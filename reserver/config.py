"""Load and validate config.json."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


REQUIRED_KEYS = ("portal_url", "login", "release_time", "preferred_slots")


class ConfigError(ValueError):
    """Raised when config.json is missing keys or malformed."""


@dataclass
class PreferredSlot:
    day_of_week: str
    start_time: str
    duration_minutes: int
    court_priority: list[int] = field(default_factory=list)


@dataclass
class Config:
    portal_url: str
    username: str
    password: str
    release_time: str
    release_timezone: str
    days_ahead: int
    preferred_slots: list[PreferredSlot]
    headless: bool
    max_retries: int
    retry_delay_seconds: float

    @classmethod
    def from_dict(cls, raw: dict) -> "Config":
        missing = [k for k in REQUIRED_KEYS if k not in raw]
        if missing:
            raise ConfigError(f"config.json is missing required keys: {missing}")

        login = raw["login"]
        if "username" not in login or "password" not in login:
            raise ConfigError("config.json 'login' must have 'username' and 'password'")

        slots = [PreferredSlot(**slot) for slot in raw["preferred_slots"]]
        if not slots:
            raise ConfigError("config.json 'preferred_slots' cannot be empty")

        return cls(
            portal_url=raw["portal_url"],
            username=login["username"],
            password=login["password"],
            release_time=raw["release_time"],
            release_timezone=raw.get("release_timezone", "America/Chicago"),
            days_ahead=raw.get("days_ahead", 7),
            preferred_slots=slots,
            headless=raw.get("headless", True),
            max_retries=raw.get("max_retries", 5),
            retry_delay_seconds=raw.get("retry_delay_seconds", 2),
        )

    @classmethod
    def load(cls, path: str | Path) -> "Config":
        path = Path(path)
        if not path.exists():
            raise ConfigError(
                f"{path} not found. Copy config.example.json to config.json and fill it in."
            )
        with path.open() as f:
            raw = json.load(f)
        return cls.from_dict(raw)
