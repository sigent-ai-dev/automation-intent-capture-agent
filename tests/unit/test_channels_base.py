from voice_server.channels.base import (
    get_channels,
    register_channel,
    _channels,
)


class FakeAdapter:
    @property
    def name(self) -> str:
        return "fake"

    async def resolve_identity(self, context):
        return "fake@example.com"

    async def handle_message(self, user_email, intent_id, message):
        return {"response": "ok"}


def setup_function():
    _channels.clear()


def test_register_channel_adds_adapter():
    adapter = FakeAdapter()
    register_channel(adapter)
    assert len(get_channels()) == 1
    assert get_channels()[0].name == "fake"


def test_get_channels_returns_copy():
    adapter = FakeAdapter()
    register_channel(adapter)
    channels = get_channels()
    channels.clear()
    assert len(get_channels()) == 1


def test_multiple_adapters():
    register_channel(FakeAdapter())
    register_channel(FakeAdapter())
    assert len(get_channels()) == 2
