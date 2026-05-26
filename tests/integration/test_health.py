
import voice_server.main as main_module


async def test_liveness(http_client):
    response = await http_client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"


async def test_readiness_when_ready(http_client):
    response = await http_client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "active_sessions" in data
    assert "uptime_seconds" in data


async def test_readiness_when_draining(http_client):
    original = main_module.accepting_new
    main_module.accepting_new = False
    try:
        response = await http_client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "draining"
    finally:
        main_module.accepting_new = original
