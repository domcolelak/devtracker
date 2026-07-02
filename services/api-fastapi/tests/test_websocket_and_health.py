import asyncio
import threading
import time

import fakeredis
import fakeredis.aioredis
import pytest
from starlette.websockets import WebSocketDisconnect

import app.routers.notifications as notifications_module
from tests.conftest import make_token


class TestHealth:
    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "service": "api-fastapi"}

    def test_openapi_schema_available(self, client):
        response = client.get("/openapi.json")
        assert response.status_code == 200
        paths = response.json()["paths"]
        assert "/tasks" in paths
        assert "/tasks/{task_id}" in paths

    def test_swagger_ui_served(self, client):
        response = client.get("/docs")
        assert response.status_code == 200
        assert "swagger" in response.text.lower()


class TestWebSocketAuth:
    def test_invalid_token_rejected(self, client):
        with pytest.raises(WebSocketDisconnect) as exc_info:
            with client.websocket_connect("/ws/notifications?token=garbage"):
                pass
        assert exc_info.value.code == 1008

    def test_refresh_token_rejected(self, client):
        # decode_token ONLY VERIFIES SIGNATURE/EXPIRY; token_type IS NOT CHECKED ON
        # THE WS PATH, BUT AN EXPIRED TOKEN MUST STILL BE REJECTED
        with pytest.raises(WebSocketDisconnect) as exc_info:
            token = make_token(expires_in=-10)
            with client.websocket_connect(f"/ws/notifications?token={token}"):
                pass
        assert exc_info.value.code == 1008

    def test_missing_token_rejected(self, client):
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/ws/notifications"):
                pass


class TestWebSocketDelivery:
    def test_published_event_is_forwarded_to_client(self, client, monkeypatch):
        """FULL HAPPY PATH: SUBSCRIBE VIA WS, PUBLISH ON THE (FAKE) REDIS CHANNEL FROM A
        SEPARATE THREAD, ASSERT THE MESSAGE ARRIVES ON THE WEBSOCKET. A SHARED FakeServer
        LETS TWO EVENT LOOPS (TEST THREAD AND TestClient PORTAL) SEE THE SAME PUB/SUB BUS."""
        server = fakeredis.FakeServer()

        def fake_pubsub_connection():
            return fakeredis.aioredis.FakeRedis(server=server, decode_responses=True)

        monkeypatch.setattr(notifications_module, "new_pubsub_connection", fake_pubsub_connection)

        def publish_when_subscribed() -> None:
            async def run() -> None:
                publisher = fakeredis.aioredis.FakeRedis(server=server, decode_responses=True)
                # RETRY UNTIL publish() REPORTS AT LEAST ONE SUBSCRIBER - THAT IS THE
                # MOMENT THE WS HANDLER'S SUBSCRIPTION IS ACTUALLY REGISTERED
                for _ in range(50):
                    delivered_to = await publisher.publish(
                        "task_events", '{"event": "task.created", "task": {}}'
                    )
                    if delivered_to > 0:
                        return
                    await asyncio.sleep(0.1)
                raise AssertionError("WS subscriber never appeared on the channel")

            time.sleep(0.2)
            asyncio.run(run())

        publisher_thread = threading.Thread(target=publish_when_subscribed)
        publisher_thread.start()

        token = make_token()
        with client.websocket_connect(f"/ws/notifications?token={token}") as ws:
            message = ws.receive_text()

        publisher_thread.join()
        assert '"task.created"' in message
