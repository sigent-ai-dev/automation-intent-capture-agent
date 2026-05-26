from dataclasses import dataclass

SUPPORTED_CODEC = "pcm"
SUPPORTED_SAMPLE_RATE = 16000
SUPPORTED_BIT_DEPTH = 16
SUPPORTED_CHANNELS = 1


@dataclass(frozen=True)
class AudioCodec:
    format: str
    sample_rate: int
    bit_depth: int
    channels: int

    def is_supported(self) -> bool:
        return (
            self.format == SUPPORTED_CODEC
            and self.sample_rate == SUPPORTED_SAMPLE_RATE
            and self.bit_depth == SUPPORTED_BIT_DEPTH
            and self.channels == SUPPORTED_CHANNELS
        )

    @classmethod
    def default(cls) -> "AudioCodec":
        return cls(
            format=SUPPORTED_CODEC,
            sample_rate=SUPPORTED_SAMPLE_RATE,
            bit_depth=SUPPORTED_BIT_DEPTH,
            channels=SUPPORTED_CHANNELS,
        )
