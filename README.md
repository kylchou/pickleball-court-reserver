# Pickleball Court Reserver

A Python + Selenium tool that automates reserving pickleball courts on our park
district's booking site. Slots for the following week open at an exact time
every morning and get grabbed within seconds, so this script logs in, waits
until the exact release time, and submits the booking automatically instead of
me refreshing the page and clicking as fast as I can.

## How it works

1. `reserver/scheduler.py` sleeps in short intervals until the configured
   release time (down to the second), so the browser action fires right when
   new slots open.
2. `reserver/browser.py` spins up a Chrome WebDriver (headless by default).
3. `reserver/auth.py` logs into the booking portal.
4. `reserver/booking.py` opens the reservation calendar, scans the preferred
   time windows in priority order, and books the first open court it finds.
5. If the click loses a race condition (another user grabbed the slot first),
   `booking.py` retries the next preferred slot automatically.

## Setup

```bash
pip install -r requirements.txt
cp config.example.json config.json
```

Fill in `config.json` with your own portal URL, login, and preferred time
slots — **`config.json` is gitignored, never commit real credentials.**

## Usage

```bash
python main.py --config config.json
```

Add `--dry-run` to walk through the whole flow (login, search, slot picking)
without actually submitting the booking — useful for testing after the portal
changes its layout.

## Project layout

```
reserver/
  config.py       # loads + validates config.json
  browser.py      # webdriver setup
  auth.py         # login flow
  booking.py      # slot search + booking + retry logic
  scheduler.py    # precise wait-until-release-time logic
  logging_config.py
  cli.py          # argparse entry point
tests/
  test_config.py
  test_scheduler.py
main.py
```

## Notes / lessons learned

- The portal's "book" button is disabled via CSS instead of removed from the
  DOM before release time, so we poll for the `disabled` attribute instead of
  element presence.
- Headless Chrome occasionally renders the calendar widget before its JS
  finishes binding click handlers — added a short explicit wait for a data
  attribute instead of a fixed `sleep()`.

## Disclaimer

Built for personal use against a booking system that doesn't provide an API.
Only use this against a site you're authorized to book on, and be respectful
of rate limits — this is not built to hammer a server.
