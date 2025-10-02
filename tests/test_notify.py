import json

from reserver import notify


def test_send_does_nothing_without_a_webhook_url(monkeypatch):
    calls = []
    monkeypatch.setattr(notify.urllib.request, "urlopen", lambda *a, **k: calls.append(a))
    notify.send(None, "should not be sent")
    assert calls == []


def test_send_posts_json_content_to_the_webhook(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout=None):
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["headers"] = request.headers

    monkeypatch.setattr(notify.urllib.request, "urlopen", fake_urlopen)
    notify.send("https://discord.com/api/webhooks/abc/def", "Booked: court 2 at 9am Saturday")

    assert captured["url"] == "https://discord.com/api/webhooks/abc/def"
    assert captured["body"] == {"content": "Booked: court 2 at 9am Saturday"}
    assert captured["headers"]["Content-type"] == "application/json"


def test_send_swallows_errors_instead_of_crashing_the_run(monkeypatch):
    def broken_urlopen(*a, **k):
        raise OSError("webhook host unreachable")

    monkeypatch.setattr(notify.urllib.request, "urlopen", broken_urlopen)
    # Should not raise.
    notify.send("https://example.com/webhook", "test")
