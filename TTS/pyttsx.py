import random

import pyttsx3
import os

from utils import settings


class pyttsx:
    def __init__(self):
        self.max_chars = 5000
        self.voices = []

    def run(
        self,
        text: str,
        filepath: str,
        random_voice=False
    ):
        voice_id = settings.config["settings"]["tts"]["python_voice"]
        voice_num = settings.config["settings"]["tts"]["py_voice_num"]
        if voice_id == "" or voice_num == "":
            voice_id = 2
            voice_num = 3
            raise ValueError("set pyttsx values to a valid value, switching to defaults")
        else:
            voice_id = int(voice_id)
            voice_num = int(voice_num)
        for i in range(voice_num):
            self.voices.append(i)
            i = +1
        if random_voice:
            voice_id = self.randomvoice()
        
        self.use_pyttsx3(text, filepath, voice_id)

    def randomvoice(self):
        return random.choice(self.voices)

    def use_say(self, text):
        """
        Use the macOS 'say' command for text-to-speech.
        """
        command = f'say "{text}"'
        os.system(command)

    def use_pyttsx3(self, text, filepath, voice_id):
        """
        Use pyttsx3 for text-to-speech and save the file.
        """
        engine = pyttsx3.init(driverName='nsss')
        voices = engine.getProperty("voices")
        try:
            engine.setProperty("voice", voices[voice_id].id)  # Changing voice
        except IndexError:
            print(f"Voice ID {voice_id} is out of range, defaulting to 0.")
            engine.setProperty("voice", voices[0].id)  # Fallback to the first voice
        engine.save_to_file(text, f"{filepath}")
        engine.runAndWait()