import os

from dotenv import load_dotenv
from sarvamai import AsyncSarvamAI
from sarvamai import AudioOutput, EventResponse

load_dotenv()


class SarvamStreamingTTS:

    def __init__(self, on_audio=None):

        self.client = AsyncSarvamAI(
            api_subscription_key=os.getenv("SARVAM_API_KEY")
        )

        self.connection = None
        self.ws = None

        # Callback
        self.on_audio = on_audio

    async def connect(self):

        if self.ws is not None:
            return

        self.connection = self.client.text_to_speech_streaming.connect(
            model="bulbul:v3",
            send_completion_event=True
        )

        self.ws = await self.connection.__aenter__()

        await self.ws.configure(
            target_language_code="en-IN",
            speaker="kavya",
            speech_sample_rate=8000,
            output_audio_codec="alaw"
        )

        print("✅ Sarvam Streaming TTS Connected")

    async def speak(self, text: str):

        if self.ws is None:
            return

        try:

            await self.ws.convert(text)

            await self.ws.flush()

            while True:

                message = await self.ws.recv()

                #
                # Audio Chunk
                #
                if isinstance(message, AudioOutput):

                    if self.on_audio:

                        await self.on_audio(
                            message.data.audio
                        )

                #
                # Final Event
                #
                elif isinstance(message, EventResponse):

                    if message.data.event_type == "final":

                        break

        except Exception as e:

            print(f"❌ TTS Error : {e}")

    async def disconnect(self):

        try:

            if self.connection:

                await self.connection.__aexit__(
                    None,
                    None,
                    None
                )

        except Exception as e:

            print(f"TTS Disconnect Error : {e}")

        finally:

            self.ws = None
            self.connection = None