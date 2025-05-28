from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from gtts import gTTS
import speech_recognition as sr
import uvicorn
from fastapi.responses import FileResponse
import tempfile
import os

app = FastAPI(title="Voice Agent (gTTS)")

@app.get("/")
async def root():
    return {"message": "Voice API Operational (gTTS)"}

@app.get("/favicon.ico")
async def favicon():
    return {}

class TTSRequest(BaseModel):
    text: str
    lang: str = "en"

class STTResponse(BaseModel):
    text: str
    confidence: float
    status: str

class TTSResponse(BaseModel):
    audio_file: str
    status: str

class VoiceProcessor:
    def __init__(self):
        self.recognizer = sr.Recognizer()
    
    def text_to_speech(self, text: str, lang: str = "en") -> str:
        try:
            tts = gTTS(text=text, lang=lang)
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            tts.save(temp_file.name)
            temp_file.close()
            return temp_file.name
        except Exception as e:
            raise Exception(f"TTS Error: {str(e)}")
    
    def speech_to_text(self, audio_data: bytes) -> tuple:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_audio:
                temp_audio.write(audio_data)
                temp_audio.flush()
                with sr.AudioFile(temp_audio.name) as source:
                    audio = self.recognizer.record(source)
                    text = self.recognizer.recognize_google(audio)
                os.unlink(temp_audio.name)
                return text, 0.9
        except sr.UnknownValueError:
            return "Could not understand audio", 0.0
        except sr.RequestError as e:
            return f"Speech recognition error: {str(e)}", 0.0
        except Exception as e:
            return f"Processing error: {str(e)}", 0.0

voice_processor = VoiceProcessor()

@app.post("/text_to_speech", response_model=TTSResponse)
async def text_to_speech(request: TTSRequest):
    try:
        audio_file = voice_processor.text_to_speech(request.text, request.lang)
        return TTSResponse(audio_file=audio_file, status="success")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/speech_to_text", response_model=STTResponse)
async def speech_to_text(file: UploadFile = File(...)):
    try:
        audio_data = await file.read()
        text, confidence = voice_processor.speech_to_text(audio_data)
        return STTResponse(text=text, confidence=confidence, status="success")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download_audio/{filename}")
async def download_audio(filename: str):
    if os.path.exists(filename):
        return FileResponse(filename, media_type="audio/mpeg", filename="response.mp3")
    else:
        raise HTTPException(status_code=404, detail="Audio file not found")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8006)
