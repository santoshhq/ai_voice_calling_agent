from fastapi import FastAPI, WebSocket
from fastapi.websockets import WebSocketDisconnect

from voicelink import VoiceLinkHandler

app = FastAPI()

handler = VoiceLinkHandler()


@app.get("/")
async def health():
    return {
        "status": "running",
        "service": "VoiceLink AI Voice Agent"
    }


@app.websocket("/media")
async def media_stream(websocket: WebSocket):
    print("🔥 Incoming WebSocket Request")

    try:
        await handler.handle(websocket)

    except WebSocketDisconnect:
        print("❌ Client Disconnected")

    except Exception as e:
        print(f"❌ Error: {e}")