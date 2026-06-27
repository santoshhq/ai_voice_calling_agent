import asyncio
import sounddevice as sd
import websockets

CHUNK_SIZE = 1024
SAMPLE_RATE = 16000


async def stream_audio():

    uri = "ws://localhost:4141/audio"

    async with websockets.connect(uri) as websocket:

        print("✅ Connected to FastAPI Server")
        print("🎤 Recording Started... Press Ctrl+C to stop.")

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="int16"
        ) as stream:

            try:
                while True:

                    chunk, overflowed = stream.read(CHUNK_SIZE)

                    if overflowed:
                        print("⚠️ Overflow!")

                    # Convert NumPy array -> bytes
                    audio_bytes = chunk.tobytes()

                    # Send to FastAPI
                    await websocket.send(audio_bytes)

            except KeyboardInterrupt:
                print("\n🛑 Recording Stopped")


if __name__ == "__main__":
    asyncio.run(stream_audio())