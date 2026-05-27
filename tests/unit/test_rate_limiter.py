import time
from unittest.mock import patch

from voice_server.notifications.rate_limiter import RateLimiter


def test_allows_first_call():
    rl = RateLimiter(window_seconds=60)
    assert rl.allow("error:VOICE_SERVICE_UNAVAILABLE") is True


def test_blocks_within_window():
    rl = RateLimiter(window_seconds=60)
    rl.allow("error:VOICE_SERVICE_UNAVAILABLE")
    assert rl.allow("error:VOICE_SERVICE_UNAVAILABLE") is False


def test_allows_after_window():
    rl = RateLimiter(window_seconds=1)
    rl.allow("error:TIMEOUT")
    time.sleep(1.1)
    assert rl.allow("error:TIMEOUT") is True


def test_different_keys_independent():
    rl = RateLimiter(window_seconds=60)
    assert rl.allow("error:A") is True
    assert rl.allow("error:B") is True
    assert rl.allow("error:A") is False
    assert rl.allow("error:B") is False


def test_reset_allows_again():
    rl = RateLimiter(window_seconds=60)
    rl.allow("error:X")
    assert rl.allow("error:X") is False
    rl.reset("error:X")
    assert rl.allow("error:X") is True
