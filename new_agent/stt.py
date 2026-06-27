import os
import asyncio
import base64

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
            return

        self.connection = self.client.speech_to_text_streaming.connect(
            model="saaras:v3",
            mode="transcribe",
            language_code="en-IN",
            sample_rate=8000,
            input_audio_codec="pcm_s16le",
            high_vad_sensitivity=True,
            vad_signals=True
        )

        self.ws = await self.connection.__aenter__()

        print("✅ Sarvam Streaming Connected")

        self.listener_task = asyncio.create_task(
            self.receive()
        )

    async def send_audio(self, pcm_bytes: bytes):

        if self.ws is None:
            return

        try:

            audio_b64 = base64.b64encode(
                pcm_bytes
            ).decode()

            await self.ws.transcribe(
                audio=audio_b64,
                encoding="audio/wav",
                sample_rate=8000
            )

        except Exception as e:

            print(f"❌ STT Send Error : {e}")

    async def receive(self):

        try:

            while True:

                response = await self.ws.recv()

                if response.type != "data":
                    continue

                transcript = response.data.transcript

                if not transcript:
                    continue

                print(f"\n🎤 USER : {transcript}")

                if self.on_transcript:
                    await self.on_transcript(transcript)

        except Exception as e:

            print(f"❌ STT Receive Error : {e}")

    async def disconnect(self):

        try:

            if self.listener_task:
                self.listener_task.cancel()

            if self.connection:
                await self.connection.__aexit__(
                    None,
                    None,
                    None
                )

        except Exception as e:

            print(e)

        finally:

            self.ws = None
            self.connection = None
            self.listener_task = None