# Pickleball Court Reserver

Our park district releases next week's court times at 7am sharp and they're
gone in like 10 seconds. I got tired of trying to click fast enough every
morning so I wrote this to do it for me.

It's a Selenium script that waits until the exact second slots open, logs
in, and works down a priority list of courts/times I set ahead of time. If
someone beats me to my first choice it just tries the next one on the list.

## Setup

```bash
pip install -r requirements.txt
cp config.example.json config.json
```

Fill in `config.json` with the portal URL, your login, and which slots you
want, in priority order. It's gitignored already so don't worry about
committing it by accident.

## Running it

```bash
python main.py --config config.json
```

Add `--dry-run` if you just want to check that login and slot-searching
still work without actually submitting a booking -- handy after the site
changes its layout on you.

## Getting notified

Set `webhook_url` in `config.json` to a Discord webhook URL and a failed run
(or a crash -- login broke, site layout changed) pings that channel instead
of you finding out later that you don't have a court. Set
`notify_on_success` to `true` too if you also want a ping when it actually
books something. Leave `webhook_url` blank and this does nothing, same as
before it existed.

## Stuff I ran into building this

- The "book" button gets disabled with CSS instead of removed from the page
  before release time, so checking if the button exists isn't enough -- had
  to check the `disabled` attribute directly.
- Headless Chrome sometimes renders the calendar before its own JS finishes
  binding the click handlers, so a plain `sleep()` wasn't reliable. Had to
  wait on an actual element instead.

## Heads up

This only works against a booking site with no public API, so it's not
really reusable as-is for anyone else's park district. Only run it against
something you're actually allowed to book on, and don't hammer the server
with it.
