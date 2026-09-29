# pickleball-court-reserver

My park district drops next week's court times at 7am and they're gone in
about 10 seconds. I kept losing, so now a script does the clicking for me.

It waits until the exact second slots open, logs in, and goes down a list of
courts/times I want. If my first pick is taken it moves on to the next one.

## Setup

```bash
pip install -r requirements.txt
cp config.example.json config.json
```

Put the portal URL, your login, and the slots you want (in order) in
`config.json`. It's already in `.gitignore`.

## Running

```bash
python main.py --config config.json
```

Use `--dry-run` to test login and slot searching without actually booking.
Useful when the site changes its layout. `--skip-wait` skips waiting for 7am.

## Discord alerts

Set `webhook_url` in `config.json` to a Discord webhook and you'll get a
message if a run fails or crashes. Set `notify_on_success` to `true` if you
also want one when it books something. No webhook, no messages.

## Things that tripped me up

- Before release time the book button is disabled, not hidden, so I have to
  check the `disabled` attribute instead of just looking for the button.
- Headless Chrome sometimes shows the calendar before the click handlers are
  hooked up, so `sleep()` wasn't reliable. It waits for a real element now.

## Note

This is built for one specific booking site with no API, so it probably
won't work for your park district without changes. Only use it where you're
allowed to book, and don't spam the server.
