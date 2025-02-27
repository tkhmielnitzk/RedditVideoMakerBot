import random

from gtts import gTTS

from utils import settings

from pydub import AudioSegment
import os

class GTTS:
    def __init__(self):
        self.max_chars = 5000
        self.voices = []

    def run(self, text, filepath, random_voice: bool = False):
        tts = gTTS(
            text=text,
            lang=settings.config["reddit"]["thread"]["post_lang"] or "en",
            slow=False,
        )
        # tts.save(filepath)
        temp_filepath = filepath.replace(".mp3", "_temp.mp3")
        tts.save(temp_filepath)

        # Load and speed up the audio using pydub
        audio = AudioSegment.from_file(temp_filepath)
        faster_audio = audio.speedup(playback_speed=1.2)  # Slightly faster (adjust as needed)

        # Save the sped-up audio to the final file
        faster_audio.export(filepath, format="mp3")
        # Remove the temporary file
        if os.path.exists(temp_filepath):
            os.remove(temp_filepath)

    def randomvoice(self):
        return random.choice(self.voices)
