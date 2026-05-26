from voice_server.models.codec import AudioCodec


def test_default_codec_is_supported():
    codec = AudioCodec.default()
    assert codec.is_supported()


def test_supported_codec_explicit():
    codec = AudioCodec(format="pcm", sample_rate=16000, bit_depth=16, channels=1)
    assert codec.is_supported()


def test_unsupported_codec_wrong_format():
    codec = AudioCodec(format="opus", sample_rate=16000, bit_depth=16, channels=1)
    assert not codec.is_supported()


def test_unsupported_codec_wrong_sample_rate():
    codec = AudioCodec(format="pcm", sample_rate=44100, bit_depth=16, channels=1)
    assert not codec.is_supported()


def test_unsupported_codec_wrong_bit_depth():
    codec = AudioCodec(format="pcm", sample_rate=16000, bit_depth=24, channels=1)
    assert not codec.is_supported()


def test_unsupported_codec_stereo():
    codec = AudioCodec(format="pcm", sample_rate=16000, bit_depth=16, channels=2)
    assert not codec.is_supported()
