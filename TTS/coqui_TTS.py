import random
import os
from typing import Final
from utils import settings
import json
import subprocess

# Pre-defined voices (You can modify this as needed for your voices)
eng_voices: Final[tuple] = (
    "tts_models/en/ljspeech/tacotron2-DDC",        # English voice
)

class LinuxTTS:
    def __init__(self):
        self.max_chars = 5000
        self.voices = eng_voices

    def run(
        self,
        text: str,
        filepath: str,
        random_voice=False
    ):
        if random_voice:
            voice = self.randomvoice()
        else:
            voice = settings.config["settings"]["tts"]["python_voice"]

        self.use_coqui(text, filepath, voice)

    @staticmethod
    def randomvoice() -> str:
        to_return = random.choice(eng_voices)
        print(f"Using voice: {to_return}")
        return to_return

    def use_coqui(self, text, filepath, voice):
        """
        Use 'coqui' to generate a WAV file, then convert it to MP3 using ffmpeg.
        """
        # convert apostrophes to unicode
        text = text.replace("\u2019", "'")
        escaped_text = json.dumps(text)  # This will escape quotes and special characters automatically
        filepath = filepath.replace("./assets", "assets")
        filepath = filepath.replace("assets/temp", "/app/tts-output")
        # Generate speech with espeak
        # coqui_command = f"""curl -X POST http://coqui-api:8000/tts \\
        #         -H "Content-Type: application/json" \\
        #         -d @- <<EOF
        #         {{
        #         "text": "{escaped_text}",
        #         "model_name": "{voice}",
        #         "out_path": "{filepath}"
        #         }}
        #         EOF"""

        data = {
            "text": escaped_text,
            "model_name": voice,
            "out_path": filepath
        }
        json_data = json.dumps(data)

        # Créer la commande curl en utilisant subprocess et un tableau d'arguments
        coqui_command = [
            "curl",
            "-X", "POST",
            "http://coqui-api:8000/tts",
            "-H", "Content-Type: application/json",
            "-d", json_data
        ]

        print("command: ", coqui_command)
        # Use subprocess.run() for executing the command
        result = subprocess.run(coqui_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Handle the result and check for errors
        if result.returncode != 0:
            print(f"Error: 'coqui' command failed with return code {result.returncode}")
            print(f"stderr: {result.stderr.decode()}")
            return

        print("Speech generation successful.")

#   curl -X POST http://localhost:8000/tts -H "Content-Type: application/json" -d @- <<EOF
#   {
#     "text": "I'm older but wiser than ever.",
#     "model_name": "tts_models/en/ljspeech/tacotron2-DDC",
#     "out_path": "tts-output/hello.mp3"
#   }
#   EOF
        


# curl -X POST http://coqui-api:8000/tts 
#     -H "Content-Type: application/json" 
#     -d @- <<EOF
#     {
#     "text": "First Image of Zoe Saldana's Neytiri in Avatar Fire and Ash'",
#     "model_name": "tts_models/en/ljspeech/tacotron2-DDC",
#     "out_path": "/app/tts-output/1kd4m4z/mp3/title.mp3"
#     }
#     EOF