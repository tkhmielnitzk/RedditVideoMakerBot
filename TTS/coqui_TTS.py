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

class CoquiTTS:
    def __init__(self):
        self.max_chars = 5000
        self.voices = eng_voices
        self.speed = 1.4

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

        temp_path = os.path.join(
            os.path.dirname(filepath),
            "temp.wav"
        )
        # self.use_coqui(text, filepath, voice)
        self.use_coqui(text, temp_path, voice)
        self.change_speed(temp_path, filepath, self.speed)
        # Remove the temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        else:
            print(f"The file {temp_path} does not exist")

    @staticmethod
    def randomvoice() -> str:
        to_return = random.choice(eng_voices)
        print(f"Using voice: {to_return}")
        return to_return
    

    def normalize_unicode_punctuation(self, text):
        replacements = {
            "\u2019": "'", "\u2018": "'",
            "\u201c": '"', "\u201d": '"',
            "\u2026": "...",
            "\u2013": "-", "\u2014": "-",
            "\u00a0": " ", "\u200b": "",
            "\u2022": "", "\u2122": "",
            "\u00ae": "", "\u00a9": "",
        }
        for uni, char in replacements.items():
            text = text.replace(uni, char)
        return text
    

    def use_coqui(self, text, filepath, voice):
        """
        Use 'coqui' to generate a WAV file, then convert it to MP3 using ffmpeg.
        """
        # convert apostrophes to unicode
        # text = text.replace("\u2019", "'")
        # text = text.replace("\u2026", "...")
        text = self.normalize_unicode_punctuation(text)
        escaped_text = json.dumps(text)  # This will escape quotes and special characters automatically
        filepath = filepath.replace("./assets", "assets")
        filepath = filepath.replace("assets/temp", "/app/tts-output")

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

    def change_speed(self, input_path, output_path, speed):
        """
        Modify the speed of a WAV file using ffmpeg.
        """
        subprocess.run([
            "ffmpeg",
            "-i", input_path,
            "-filter:a", f"atempo={speed}",
            "-y",  # <--- this is the key
            "-vn",  # no video
            output_path
        ])