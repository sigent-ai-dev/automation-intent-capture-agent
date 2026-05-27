import struct

from voice_server.audio.resample import downsample_24k_to_16k


def test_empty_input():
    assert downsample_24k_to_16k(b"") == b""


def test_ratio_3_to_2():
    # 6 input samples at 24kHz -> 4 output samples at 16kHz
    samples_24k = [1000, 2000, 3000, 4000, 5000, 6000]
    pcm_24k = struct.pack(f"<{len(samples_24k)}h", *samples_24k)
    result = downsample_24k_to_16k(pcm_24k)
    num_out = len(result) // 2
    assert num_out == 4


def test_odd_byte_length():
    # 5 bytes = 2 full samples + 1 leftover byte -> only 2 samples processed
    pcm_24k = struct.pack("<2h", 1000, 2000) + b"\x00"
    result = downsample_24k_to_16k(pcm_24k)
    # 2 input samples at 24kHz -> 1 output sample at 16kHz
    num_out = len(result) // 2
    assert num_out == 1


def test_output_within_16bit_range():
    # Max amplitude samples
    samples = [32767, -32768, 32767, -32768, 32767, -32768]
    pcm_24k = struct.pack(f"<{len(samples)}h", *samples)
    result = downsample_24k_to_16k(pcm_24k)
    out_samples = struct.unpack(f"<{len(result) // 2}h", result)
    for s in out_samples:
        assert -32768 <= s <= 32767


def test_larger_input():
    # 300 samples -> 200 output samples
    samples = list(range(300))
    pcm_24k = struct.pack(f"<{len(samples)}h", *samples)
    result = downsample_24k_to_16k(pcm_24k)
    num_out = len(result) // 2
    assert num_out == 200
