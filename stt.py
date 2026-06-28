import os
import asyncio
import base64
import traceback

from dotenv import load_dotenv
from sarvamai import AsyncSarvamAI

load_dotenv()


class SarvamStreamingSTT:

    def __init__(self, on_transcript=None):

        self.client = AsyncSarvamAI(
            api_subscription_key=os.getenv("SARVAM_API_KEY")
        )

        self.connection = None
        self.ws = None
        self.listener_task = None

        self.on_transcript = on_transcript

    async def connect(self):

        if self.ws is not None:
            print("🟢 STT already connected")
            print("WS OBJECT :", self.ws)
            print("WS ID     :", id(self.ws))
            return

        print("\n" + "=" * 70)
        print("🔄 CONNECTING TO SARVAM STT")
        print("=" * 70)

        try:

            self.connection = self.client.speech_to_text_streaming.connect(
                model="saaras:v3",
                mode="transcribe",
                language_code="en-IN",
                sample_rate=8000,
                input_audio_codec="pcm_s16le",
                high_vad_sensitivity=True,
                vad_signals=True
            )

            print("✅ Connection object created")
            print(self.connection)

            self.ws = await self.connection.__aenter__()

            print("\n✅ STT WebSocket Connected")
            print("WS OBJECT :", self.ws)
            print("WS ID     :", id(self.ws))

            self.listener_task = asyncio.create_task(
                self.receive()
            )

            print("🎧 Listener task started")
            print("TASK :", self.listener_task)

        except Exception:

            print("\n❌ CONNECT FAILED")
            traceback.print_exc()

            self.ws = None

    async def send_audio(self, pcm_bytes: bytes):

        print("\n" + "-" * 70)
        print("🎤 send_audio()")
        print("-" * 70)

        print("WS :", self.ws)

        if self.ws is None:
            print("❌ STT websocket is None")
            return

        print("PCM SIZE :", len(pcm_bytes))

        try:

            audio_b64 = base64.b64encode(
                pcm_bytes
            ).decode()

            print("Encoded Size :", len(audio_b64))

            print("➡️ Calling ws.transcribe()...")

            await self.ws.transcribe(
                audio=audio_b64,
                encoding="audio/wav",
                sample_rate=8000
            )

            print("✅ ws.transcribe() Finished")

        except Exception:

            print("\n❌ SEND AUDIO FAILED")
            traceback.print_exc()

            print("Setting ws=None")

            self.ws = None

    async def receive(self):

        print("\n" + "=" * 70)
        print("🎧 RECEIVE LOOP STARTED")
        print("=" * 70)

        try:

            while True:

                print("\nWaiting for STT Event...")
                print("Current WS :", self.ws)

                response = await self.ws.recv()

                print("\n⬇️ RAW RESPONSE")
                print(type(response))
                print(response)

                if not hasattr(response, "type"):
                    print("⚠️ Unknown response object")
                    continue

                print("EVENT :", response.type)

                if response.type != "data":
                    continue

                transcript = response.data.transcript

                print("TRANSCRIPT :", transcript)

                if not transcript:
                    continue

                print(f"\n🎤 USER : {transcript}")

                if self.on_transcript:
                    await self.on_transcript(transcript)

        except asyncio.CancelledError:

            print("\n🛑 RECEIVE TASK CANCELLED")

        except Exception:

            print("\n" + "=" * 70)
            print("❌ RECEIVE LOOP CRASHED")
            print("=" * 70)

            traceback.print_exc()

            print("\nWS BEFORE NONE :", self.ws)

            self.ws = None

            print("WS AFTER NONE :", self.ws)

    async def disconnect(self):

        print("\n" + "=" * 70)
        print("🔌 DISCONNECT STT")
        print("=" * 70)

        try:

            if self.listener_task:

                print("Cancelling Listener...")
                self.listener_task.cancel()

            if self.connection:

                print("Closing Connection...")
                await self.connection.__aexit__(
                    None,
                    None,
                    None
                )

        except Exception:

            traceback.print_exc()

        finally:

            self.ws = None
            self.connection = None
            self.listener_task = None

            print("✅ STT Disconnected")