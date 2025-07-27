import pytest

from reserver.config import Config, ConfigError


def make_raw(**overrides):
    raw = {
        "portal_url": "https://example.com",
        "login": {"username": "u", "password": "p"},
        "release_time": "07:00:00",
        "preferred_slots": [
            {"day_of_week": "Saturday", "start_time": "09:00", "duration_minutes": 60, "court_priority": [1, 2]}
        ],
    }
    raw.update(overrides)
    return raw


def test_loads_valid_config():
    config = Config.from_dict(make_raw())
    assert config.username == "u"
    assert config.preferred_slots[0].day_of_week == "Saturday"
    assert config.headless is True  # default
    assert config.days_ahead == 7  # default


def test_missing_required_key_raises():
    raw = make_raw()
    del raw["release_time"]
    with pytest.raises(ConfigError):
        Config.from_dict(raw)


def test_missing_login_fields_raises():
    raw = make_raw(login={"username": "u"})
    with pytest.raises(ConfigError):
        Config.from_dict(raw)


def test_empty_preferred_slots_raises():
    raw = make_raw(preferred_slots=[])
    with pytest.raises(ConfigError):
        Config.from_dict(raw)


def test_defaults_can_be_overridden():
    raw = make_raw(headless=False, max_retries=10)
    config = Config.from_dict(raw)
    assert config.headless is False
    assert config.max_retries == 10
