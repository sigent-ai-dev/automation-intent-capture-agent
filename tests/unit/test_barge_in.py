import struct

import pytest

from voice_server.bidi.barge_in import BargeInDetector


@pytest.fixture
def detector():
    return BargeInDetector(energy_threshold=0.15)


def _make_audio(amplitude: int, num_samples: int = 160) -> bytes:
    return struct.pack(f"<{num_samples}h", *([amplitude] * num_samples))


def test_silence_not_detected(detector):
    audio = _make_audio(0)
    assert detector.check(audio) is False


def test_loud_audio_detected(detector):
    # amplitude that exceeds threshold (0.15 * 32767 ≈ 4915)
    audio = _make_audio(6000)
    assert detector.check(audio) is True


def test_below_threshold_not_detected(detector):
    # amplitude below threshold
    audio = _make_audio(1000)
    assert detector.check(audio) is False


def test_reset_clears_state(detector):
    audio = _make_audio(6000)
    detector.check(audio)
    detector.reset()
    assert detector._triggered is False
