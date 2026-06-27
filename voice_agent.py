from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage,BaseMessage,SystemMessage
from langgraph.graph import StateGraph, START,END,MessagesState
from langgraph.graph.message import add_messages
from typing import TypedDict,Annotated
from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder
import asyncio,os
from ai_prompts import SYSTEM_PROMPT
from dotenv import load_dotenv
from sarvamai import SarvamAI
from base64_to_audiofile import save_audio
from audio_to_text import audio_to_text
import io
import threading
import numpy as np
import sounddevice as sd
import soundfile as sf
from scipy.io.wavfile import write
load_dotenv()

gemini_model=ChatGoogleGenerativeAI(model="gemini-2.5-flash")
tts=SarvamAI(api_subscription_key=os.getenv("SARVAM_API_KEY"))
stt = SarvamAI(
    api_subscription_key=os.getenv("SARVAM_API_KEY")
)
       
async def build_graph():
    
    async def ChatAssistance(state:MessagesState)->MessagesState:
        prompt=ChatPromptTemplate.from_messages([
            ("system",SYSTEM_PROMPT),
            MessagesPlaceholder("messages")
        ])
        chain=prompt | gemini_model
        response=await chain.ainvoke(state["messages"])
        return {"messages":[response]}

    graph=StateGraph(MessagesState)
    graph.add_node("ChatAssistance",ChatAssistance)
    graph.add_edge(START,"ChatAssistance")
    graph.add_edge("ChatAssistance",END)
    return graph.compile()
    
    
def record_audio_until_stop(filename: str):
    audio_data = []
    recording = True
    sample_rate = 16000

    def record_audio():
        nonlocal audio_data, recording

        with sd.InputStream(
            samplerate=sample_rate,
            channels=1,
            dtype="int16"
        ) as stream:

            print("🎤 Recording... Press Enter to stop.")

            while recording:
                chunk, _ = stream.read(1024)
                audio_data.append(chunk)

    def stop_recording():
        nonlocal recording
        input()
        recording = False

    # Start recording thread
    recording_thread = threading.Thread(target=record_audio)
    recording_thread.start()

    # Start stop listener thread
    stop_thread = threading.Thread(target=stop_recording)
    stop_thread.start()

    stop_thread.join()
    recording_thread.join()

    if not audio_data:
        return ""

    # Combine chunks
    audio_data = np.concatenate(audio_data, axis=0)

    # Overwrite existing file with new recording
    write(filename, sample_rate, audio_data)

    print(f"✅ Audio saved to {filename}")

    # Transcribe using Sarvam
    with open(filename, "rb") as audio_file:
        response = stt.speech_to_text.transcribe(
            file=audio_file,
            model="saaras:v3",
            mode="transcribe"
        )

    print(f"📝 User: {response.transcript}")

    return response.transcript

def play_audio(text: str):
    cleaned_text = text.replace("**", "")
    final_res = tts.text_to_speech.convert(
        model="bulbul:v3",
        text=cleaned_text,
        target_language_code="en-IN",
        speaker="kavya"
    )
    print(cleaned_text)
    # Save audio
    audio_path = save_audio(final_res.audios[0])
    # Auto play audio
    data, samplerate = sf.read(audio_path)
    sd.play(data, samplerate)
    sd.wait()
    
async def main():
    wk = await build_graph()
    while True:
        user_inputt = record_audio_until_stop("input_aud.wav")
        if user_inputt.strip().lower() == "exit":
            break
        if len(user_inputt)!=0:
            inptt = {
                "messages": [HumanMessage(content=user_inputt)]
            }
            resp = await wk.ainvoke(inptt)
            res = resp["messages"][-1].content
            play_audio(res)
            
            
        
        
if __name__=="__main__":
    asyncio.run(main())
