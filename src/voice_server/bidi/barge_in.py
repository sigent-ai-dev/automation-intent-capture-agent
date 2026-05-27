import struct


class BargeInDetector:
    """Detects user speech during agent output by measuring audio energy."""

    def __init__(self, energy_threshold: float = 0.15) -> None:
        self._threshold = energy_threshold
        self._triggered = False

    def check(self, pcm_bytes: bytes) -> bool:
        num_samples = len(pcm_bytes) // 2
        if num_samples == 0:
            return False

        samples = struct.unpack(f"<{num_samples}h", pcm_bytes[: num_samples * 2])
        rms = (sum(s * s for s in samples) / num_samples) ** 0.5
        normalized = rms / 32767.0

        if normalized >= self._threshold:
            self._triggered = True
            return True
        return False

    def reset(self) -> None:
        self._triggered = False
