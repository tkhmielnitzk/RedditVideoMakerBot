import os
import subprocess
from pydub import AudioSegment
from TTS.api import TTS

# Cache loaded models
loaded_models = {}

def list_models():
    output = subprocess.check_output(["tts", "--list_models"], text=True)
    return output.strip().splitlines()

def synthesize(text, model_name, out_path):
    if model_name not in loaded_models:
        loaded_models[model_name] = TTS(model_name)

    tts = loaded_models[model_name]
    wav_path = out_path.replace(".mp3", ".wav")
    tts.tts_to_file(text=text, file_path=wav_path)

    if out_path.endswith(".mp3"):
        wav_audio = AudioSegment.from_wav(wav_path)
        wav_audio.export(out_path, format="mp3")
        os.remove(wav_path)

    return out_path
