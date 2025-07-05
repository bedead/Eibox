from fastapi import APIRouter, WebSocket
from langgraph.config import RunnableConfig
from langgraph.types import Command
from core import ChatAgent, ChatbotState

router = APIRouter()


def call_graph(user_input, config: RunnableConfig):
    # print(type(user_input))
    events = ChatAgent.stream(
        {"messages": [{"role": "user", "content": user_input}]},
        config,
        stream_mode="values",
    )
    for event in events:
        if event["chatbot"]["messages"]:
            return event["chatbot"]["messages"].content


@router.websocket("/chatbot/v1/{thread_id}")
async def websocket_endpoint(websocket: WebSocket, thread_id: str):
    await websocket.accept()
    try:
        config = RunnableConfig(
            recursion_limit=150, configurable={"thread_id": thread_id}
        )
        while True:
            message = await websocket.receive_text()
            ai_message = call_graph(user_input=message, config=config)
            print(f"AI response: {ai_message}")
            if ai_message:
                await websocket.send_text(f"{ai_message}")
            else:
                await websocket.send_text("[ERROR] No response from AI")

    except Exception as e:
        await websocket.send_text(f"[ERROR] {str(e)}")
    finally:
        await websocket.close()
