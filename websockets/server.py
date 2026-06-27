from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse
from fastapi.websockets import WebSocketDisconnect
import numpy as np
import io
import wave
import os
import asyncio
from dotenv import load_dotenv
from sarvamai import SarvamAI

load_dotenv()

app = FastAPI()

stt = SarvamAI(
    api_subscription_key=os.getenv("SARVAM_API_KEY")
)

SAMPLE_RATE = 16000
CHUNK_SIZE = 1024
SILENCE_THRESHOLD = 500
SILENCE_DURATION_MS = 800
MIN_AUDIO_MS = 300

silence_frames_needed = int(SILENCE_DURATION_MS / (CHUNK_SIZE / SAMPLE_RATE * 1000))


def pcm_to_wav_bytes(pcm_bytes: bytes) -> bytes:
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(pcm_bytes)
    wav_buffer.seek(0)
    return wav_buffer.read()


async def transcribe_audio(audio_bytes: bytes):
    if len(audio_bytes) < MIN_AUDIO_MS * SAMPLE_RATE * 2 // 1000:
        return None
    wav_data = pcm_to_wav_bytes(audio_bytes)
    try:
        response = await asyncio.to_thread(
            stt.speech_to_text.transcribe,
            file=("audio.wav", wav_data, "audio/wav"),
            model="saaras:v3",
            mode="transcribe"
        )
        return response.transcript
    except Exception as e:
        print(f"Transcription error: {e}")
        return None


@app.get("/")
async def home():
    return JSONResponse({"status": "Server Running"})


@app.websocket("/audio")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("✅ Client Connected")

    audio_buffer = bytearray()
    speech_detected = False
    silence_frames = 0

    try:
        while True:
            message = await websocket.receive_bytes()

            audio_chunk = np.frombuffer(message, dtype=np.int16)
            energy = float(np.abs(audio_chunk).mean())

            if energy > SILENCE_THRESHOLD:
                audio_buffer.extend(message)
                speech_detected = True
                silence_frames = 0
            else:
                if speech_detected:
                    audio_buffer.extend(message)
                    silence_frames += 1

                    if silence_frames >= silence_frames_needed:
                        transcript = await transcribe_audio(bytes(audio_buffer))
                        if transcript:
                            print(f"📝 User: {transcript}")
                            await websocket.send_text(transcript)

                        audio_buffer.clear()
                        speech_detected = False
                        silence_frames = 0

    except WebSocketDisconnect:
        print("❌ Client Disconnected")
        if speech_detected and len(audio_buffer) > 0:
            transcript = await transcribe_audio(bytes(audio_buffer))
            if transcript:
                print(f"📝 User (final): {transcript}")
                await websocket.send_text(transcript)