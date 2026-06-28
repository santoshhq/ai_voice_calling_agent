from fastapi import FastAPI, WebSocket
from fastapi.websockets import WebSocketDisconnect

from voicelink import VoiceLinkHandler

app = FastAPI()


@app.get("/")
async def health():
    return {
        "status": "running"
    }


@app.websocket("/media")
async def media_stream(websocket: WebSocket):

    print("🔥 Incoming WebSocket Request")

    # NEW handler for EVERY call
    handler = VoiceLinkHandler()

    try:
        await handler.handle(websocket)

    except WebSocketDisconnect:
        print("❌ Client Disconnected")

    except Exception as e:
        print(e)