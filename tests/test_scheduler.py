from datetime import datetime, timedelta

from reserver.scheduler import seconds_until


def test_seconds_until_future_time_today(monkeypatch):
    # Freeze "now" and ask for a release time 30 seconds later.
    import reserver.scheduler as scheduler_module
    from dateutil import tz

    zone = tz.gettz("America/Chicago")
    fixed_now = datetime(2025, 6, 1, 6, 59, 30, tzinfo=zone)

    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now

    monkeypatch.setattr(scheduler_module, "datetime", FrozenDatetime)

    remaining = seconds_until("07:00:00", "America/Chicago")
    assert 29 <= remaining <= 30


def test_seconds_until_wraps_to_next_day(monkeypatch):
    import reserver.scheduler as scheduler_module
    from dateutil import tz

    zone = tz.gettz("America/Chicago")
    fixed_now = datetime(2025, 6, 1, 7, 0, 1, tzinfo=zone)

    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now

    monkeypatch.setattr(scheduler_module, "datetime", FrozenDatetime)

    remaining = seconds_until("07:00:00", "America/Chicago")
    # Missed today's 07:00:00 by a second, so it should roll to tomorrow (~24h).
    assert timedelta(hours=23).total_seconds() < remaining < timedelta(hours=24).total_seconds()
