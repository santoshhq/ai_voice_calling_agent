from sarvamai import SarvamAI
from dotenv import load_dotenv
import os
load_dotenv()
stt = SarvamAI(
    api_subscription_key=os.getenv("SARVAM_API_KEY")
)
def audio_to_text(filename:str):
    response = stt.speech_to_text.transcribe(
        file=open(filename, "rb"),
        model="saaras:v3",
        mode="transcribe",  # or "translate", "verbatim", "translit", "codemix"
    )

    return response.transcript

