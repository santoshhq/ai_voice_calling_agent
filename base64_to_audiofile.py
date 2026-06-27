import base64

def save_audio(base64_audio: str, filename="output.wav"):
    audio_bytes = base64.b64decode(base64_audio)

    with open(filename, "wb") as audio_file:
        audio_file.write(audio_bytes)

    print(f"Audio saved as {filename}")

    return filename