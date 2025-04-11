from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from utils import list_models, synthesize

app = FastAPI()

class TTSRequest(BaseModel):
    text: str
    model_name: str = "tts_models/en/vctk/vits"
    out_path: str = "tts-output/output.wav"

@app.get("/")
def root():
    return {"message": "Coqui TTS API Wrapper"}

@app.get("/models")
def get_models():
    return {"models": list_models()}

@app.post("/tts")
def run_tts(req: TTSRequest):
    try:
        out_file = synthesize(req.text, req.model_name, req.out_path)
        return {"message": "Success", "file": out_file}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
