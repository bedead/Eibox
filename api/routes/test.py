from fastapi import APIRouter, WebSocket

router = APIRouter()


@router.websocket("/dummy-chatbot/v1/{thread_id}")
async def websocket_endpoint(websocket: WebSocket, thread_id: str):
    await websocket.accept()
    try:
        while True:
            message = await websocket.receive_text()
            await websocket.send_text(f"AI : {message}")

    except Exception as e:
        await websocket.send_text(f"[ERROR] {str(e)}")
    finally:
        await websocket.close()
