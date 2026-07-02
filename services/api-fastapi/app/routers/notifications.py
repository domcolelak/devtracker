import jwt
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status

from app.core.redis import TASK_EVENTS_CHANNEL, new_pubsub_connection
from app.core.security import decode_token

router = APIRouter(tags=["notifications"])


@router.websocket("/ws/notifications")
async def notifications_ws(websocket: WebSocket, token: str = Query(...)) -> None:
    """
    REAL-TIME TASK NOTIFICATIONS. CLIENTS CONNECT WITH ?token=<JWT access token>
    (QUERY PARAM RATHER THAN A HEADER, SINCE BROWSER WebSocket CLIENTS CANNOT SET
    CUSTOM HEADERS DURING THE HANDSHAKE). MESSAGES ARE FANNED OUT VIA REDIS PUB/SUB
    SO THIS WORKS ACROSS MULTIPLE api-fastapi REPLICAS, NOT JUST WITHIN ONE PROCESS.
    """
    try:
        decode_token(token)
    except jwt.PyJWTError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()

    pubsub_connection = new_pubsub_connection()
    pubsub = pubsub_connection.pubsub()
    await pubsub.subscribe(TASK_EVENTS_CHANNEL)

    try:
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue
            await websocket.send_text(message["data"])
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe(TASK_EVENTS_CHANNEL)
        await pubsub.aclose()
        await pubsub_connection.aclose()
