import struct


def downsample_24k_to_16k(pcm_24k: bytes) -> bytes:
    """Downsample PCM audio from 24kHz to 16kHz (3:2 ratio).

    Uses linear interpolation for quality. Input/output are 16-bit signed LE mono.
    """
    if not pcm_24k:
        return b""

    num_samples = len(pcm_24k) // 2
    if num_samples == 0:
        return b""

    samples = struct.unpack(f"<{num_samples}h", pcm_24k[: num_samples * 2])

    ratio = 3 / 2
    out_len = int(num_samples / ratio)
    output = []

    for i in range(out_len):
        src_pos = i * ratio
        idx = int(src_pos)
        frac = src_pos - idx

        if idx + 1 < num_samples:
            sample = samples[idx] + frac * (samples[idx + 1] - samples[idx])
        else:
            sample = samples[idx]

        output.append(int(max(-32768, min(32767, sample))))

    return struct.pack(f"<{len(output)}h", *output)
