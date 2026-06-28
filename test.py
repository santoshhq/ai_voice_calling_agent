import asyncio

from tts import SarvamStreamingTTS
from sarvamai import AudioOutput, EventResponse


async def main():

    tts = SarvamStreamingTTS()

    await tts.connect()

    print("Connected\n")

    await tts.ws.convert(
        "Hello Santosh. Welcome to your AI voice assistant."
    )

    await tts.ws.flush()

    while True:

        message = await tts.ws.recv()

        print("=" * 80)
        print(type(message))
        print(message)
        print("=" * 80)

        if isinstance(message, EventResponse):

            if message.data.event_type == "final":
                break

    await tts.disconnect()


asyncio.run(main())