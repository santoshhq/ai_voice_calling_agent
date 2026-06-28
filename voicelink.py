import json
import base64

import g711
import numpy as np

from fastapi import WebSocket
from fastapi.websockets import WebSocketDisconnect
from graph import build_graph
from langchain_core.messages import HumanMessage
from stt import SarvamStreamingSTT
from tts import SarvamStreamingTTS
import asyncio
class VoiceLinkHandler:

    def __init__(self):

        self.stream_sid = None
        self.call_sid = None
        self.graph=None
        self.websocket = None
        self.stt = SarvamStreamingSTT(on_transcript=self.on_transcript)
        self.tts = SarvamStreamingTTS( on_audio=self.send_audio)
        self.is_speaking = False
    async def handle(self, websocket: WebSocket):

        await websocket.accept()
        self.websocket = websocket
        print("=" * 60)
        print("✅ VoiceLink Connected")
        print("=" * 60)

        await self.stt.connect()
        await self.tts.connect()
        
        try:

            while True:

                message = await websocket.receive_text()

                print("\n" + "=" * 60)
                print("RAW MESSAGE")
                print("=" * 60)
                print(message)

                data = json.loads(message)

                event = data.get("event")

                print(f"EVENT -> {event}")

                if event == "connected":

                    print("🟢 WebSocket Handshake Completed")

                elif event == "start":

                    start = data.get("start", {})

                    self.stream_sid = start.get("stream_sid")
                    self.call_sid = start.get("call_sid")

                    print(f"\n📞 Call Started")
                    print(f"Stream SID : {self.stream_sid}")
                    print(f"Call SID   : {self.call_sid}")
                    asyncio.create_task(self.auto_hangup())
                elif event == "media":
                    print("📦 MEDIA EVENT RECEIVED")
                    await self.handle_media(data)

                elif event == "mark":

                    mark = data.get("mark", {}).get("name")
                    print(f"📍 Mark Event : {mark}")

                elif event == "stop":

                    print("\n📴 Call Ended")

                    await self.stt.disconnect()
                    await self.tts.disconnect()

                    break

                else:

                    print(f"⚠ Unknown Event : {event}")

        except WebSocketDisconnect:

            print("❌ VoiceLink Disconnected")

        except Exception as e:

            print(f"❌ Error : {e}")

    async def handle_media(self, data):

        media = data.get("media")

        if media is None:
            return

        payload = media.get("payload")

        if not payload:
            return

        try:

            # Base64 -> A-law bytes
            alaw_bytes = base64.b64decode(payload)

            # A-law -> PCM16
            pcm_bytes = self.decode_alaw(alaw_bytes)

            # Send PCM audio to Sarvam Streaming STT
            if not self.is_speaking:
               await self.stt.send_audio(pcm_bytes)

        except Exception as e:

            print(f"❌ Audio Processing Error : {e}")

    def decode_alaw(self, alaw_bytes: bytes) -> bytes:

        """
        VoiceLink
            A-law (8-bit)
                    ↓
        Float32 [-1.0, 1.0]
                    ↓
        PCM16 (Signed 16-bit)
        """

        pcm_float = g711.decode_alaw(alaw_bytes)

        pcm_int16 = (pcm_float * 32767).astype(np.int16)

        return pcm_int16.tobytes()
    
    
    
    async def send_audio(self, audio_chunk):

        if self.websocket is None:
            print("❌ WebSocket is already closed.")
            return

        try:

            await self.websocket.send_json(
                {
                    "event": "media",
                    "stream_sid": self.stream_sid,
                    "media": {
                        "payload": audio_chunk
                    }
                }
            )

            print("🔊 Audio Sent to VoiceLink")

        except Exception as e:

            print(f"❌ Send Audio Error : {e}")
    
    async def on_transcript(self, transcript: str):

        if self.graph is None:
            self.graph = await build_graph()



        result = await self.graph.ainvoke(
            {
                "messages": [
                    HumanMessage(content=transcript)
                ]
            },
    
        )

        reply = result["messages"][-1].content
        print(f"\n🤖 AI : {reply}")
        self.is_speaking = True
        await self.tts.speak(reply)
        self.is_speaking = False
        
    async def auto_hangup(self):

        print("⏳ Auto hangup timer started (60 seconds)")

        await asyncio.sleep(60)

        if self.websocket is None:
            print("⚠️ WebSocket already closed.")
            return

        print("📞 Auto ending call...")

        try:

            await self.stt.disconnect()
            await self.tts.disconnect()

            await self.websocket.close()

        except Exception as e:

            print(f"❌ Hangup Error : {e}")